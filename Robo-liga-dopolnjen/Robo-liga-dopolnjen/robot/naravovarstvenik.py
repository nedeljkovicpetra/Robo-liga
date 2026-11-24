# -*- coding: utf-8 -*-
"""Strategija naravovarstvenika: drevesa posadi na prosta polja poligona."""
import math
import copy

from starter_code import config
from starter_code.classes import Point
from robot.navigation import PathPlanner, path_length
from robot.tasks import PushMission


def findTrees(gameState):
    return list(getattr(gameState, "trees", []) or [])


def selectTrees(robotPos, trees):
    if not trees:
        return None
    robotPos = Point(robotPos)
    return min(trees, key=lambda item: robotPos.distance_to(item.position))


def findPlantingFields(gameState):
    return list(getattr(gameState, "planting_fields", []) or [])


def selectPlantingFields(tree, fields):
    if not fields:
        return None
    tree_pos = Point(tree.position if hasattr(tree, "position") else tree)
    return min(fields, key=lambda field: tree_pos.distance_to(field.center))


def getPushPosition(tree, plantingField, offset=None):
    tree = Point(tree.position if hasattr(tree, "position") else tree)
    target = Point(plantingField.center if hasattr(plantingField, "center") else plantingField)
    dx = target.x - tree.x
    dy = target.y - tree.y
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    stand_off = config.PUSH_STANDOFF_MM if offset is None else float(offset)
    return Point(tree.x - dx / length * stand_off,
                 tree.y - dy / length * stand_off)


def _tree_points(tree):
    if tree.kind == "cherry":
        return config.POINTS_CHERRY
    return config.POINTS_PINE


def choose_task(snapshot, robot_position, robot_id, exclude_ids=None):
    exclude_ids = set(str(value) for value in (exclude_ids or []))
    if not snapshot.trees or not snapshot.planting_fields:
        return None
    robot_position = Point(robot_position)

    # Polje, na katerem že stoji drugo drevo, ni prosto.
    occupied = set()
    for field_index, field in enumerate(snapshot.planting_fields):
        for tree in snapshot.trees:
            if field.contains(tree.position):
                occupied.add(field_index)
                break

    candidates = []
    for tree in snapshot.trees:
        if tree.id in exclude_ids:
            continue
        if any(field.contains(tree.position) for field in snapshot.planting_fields):
            # Že posajeno drevo pustimo pri miru; presajanje ne prinese dodatnih točk.
            continue
        obstacles = snapshot.obstacles(tree.id, robot_id)
        planner = PathPlanner(snapshot.game_field)
        best_field = None
        best_route = None
        best_efficiency = -1.0
        available_fields = [
            (tree.position.distance_to(field.center), index, field)
            for index, field in enumerate(snapshot.planting_fields)
            if index not in occupied
        ]
        available_fields.sort(key=lambda item: item[0])
        limit = max(1, int(config.MAX_PLANT_FIELDS_TO_EVALUATE))
        fields_to_check = available_fields[:limit]
        for pass_index, field_batch in enumerate((fields_to_check, available_fields[limit:])):
            if pass_index == 1 and best_field is not None:
                break
            for _, index, field in field_batch:
                route = planner.find_path(tree.position, field.center, obstacles)
                if not route or len(route) < 2:
                    continue
                approach = getPushPosition(tree, field)
                approach_obstacles = snapshot.obstacles(None, robot_id)
                for obstacle_index, obstacle in enumerate(approach_obstacles):
                    if getattr(obstacle, "id", None) == tree.id:
                        approach_obstacles[obstacle_index] = copy.copy(obstacle)
                        approach_obstacles[obstacle_index].radius = 0.0
                robot_route = planner.find_path(robot_position, approach, approach_obstacles)
                if not robot_route:
                    continue
                cost = path_length(robot_route) + path_length(route)
                score = float(_tree_points(tree)) / max(150.0, cost)
                if score > best_efficiency:
                    best_efficiency = score
                    best_field = field
                    best_route = route
        if best_field is not None:
            candidates.append((best_efficiency, tree, best_field, best_route))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, tree, field, route = candidates[0]
    return PushMission(tree, field.center, field, route,
                       "naravovarstvenik", robot_id)


def runNavarovarstvenik(gameState, robotPos, robotDir=None,
                        obstacles=None, safeDistance=None, offset=None):
    """Stara javna funkcija; vrne izbran PushMission za normalizirano stanje."""
    return choose_task(gameState, robotPos, str(config.ROBOT_ID))


# Slovenski zapis imena za novejšo kodo.
runNaravovarstvenik = runNavarovarstvenik
