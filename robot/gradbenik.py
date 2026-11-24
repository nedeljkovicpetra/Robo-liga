# -*- coding: utf-8 -*-
"""Strategija gradbenika: opeke in železo dostavlja v rdečo bazo."""
import copy
import math

from starter_code import config
from starter_code.classes import Point, GameObject
from robot.navigation import PathPlanner, path_length
from robot.tasks import PushMission



def _builder_obstacles(snapshot, exclude_object_id=None, robot_id=None):
    """Ovire gradbenika, vključno s celimi polji, na katerih stojijo drevesa.

    Kazen se po pravilih sproži, ko je središče značke robota znotraj polja z
    drevesom. Zato ne zadošča obvoz same kocke: polje modeliramo z omejevalnim
    krogom, ki v celoti pokrije kvadratno polje.
    """
    obstacles = snapshot.obstacles(exclude_object_id, robot_id)
    for tree in snapshot.trees:
        for field in snapshot.tile_fields:
            if not field.contains(tree.position):
                continue
            radius = max(field.center.distance_to(vertex) for vertex in field.points)
            # PathPlanner prišteje še varnostni odmik robota, zato je
            # prepovedano območje večje od samega polja.
            field_obstacle = GameObject(
                "tree-field-{}".format(tree.id), field.center, "tree_field"
            )
            field_obstacle.radius = radius
            obstacles.append(field_obstacle)
            break
    return obstacles


def findMaterial(gameState):
    """Združljivost s prvotnim projektom; pričakuje normaliziran GameSnapshot."""
    return list(getattr(gameState, "materials", []) or [])


def selectMaterial(robotPos, materials):
    robotPos = Point(robotPos)
    if not materials:
        return None
    return min(materials, key=lambda item: robotPos.distance_to(item.position))


def getPushPosition(material, base, offset=None):
    """Točka za robota za kocko, v smeri proti bazi."""
    material = Point(material.position if hasattr(material, "position") else material)
    base_center = Point(base.center if hasattr(base, "center") else base)
    dx = base_center.x - material.x
    dy = base_center.y - material.y
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    stand_off = config.PUSH_STANDOFF_MM if offset is None else float(offset)
    return Point(material.x - dx / length * stand_off,
                 material.y - dy / length * stand_off)


def izracunaj_vrednost_materiala(material):
    kind = getattr(material, "kind", "brick")
    return config.POINTS_STEEL if kind == "steel" else config.POINTS_BRICK


def choose_task(snapshot, robot_position, robot_id, exclude_ids=None):
    exclude_ids = set(str(value) for value in (exclude_ids or []))
    if snapshot.builder_base is None:
        return None
    robot_position = Point(robot_position)
    candidates = []
    for material in snapshot.materials:
        if material.id in exclude_ids:
            continue
        if snapshot.builder_base.contains(material.position):
            continue
        obstacles = _builder_obstacles(snapshot, material.id, robot_id)
        planner = PathPlanner(snapshot.game_field)
        object_route = planner.find_path(material.position,
                                         snapshot.builder_base.center, obstacles)
        if not object_route or len(object_route) < 2:
            continue
        push_position = getPushPosition(material, snapshot.builder_base)
        approach_obstacles = _builder_obstacles(snapshot, None, robot_id)
        for index, obstacle in enumerate(approach_obstacles):
            if getattr(obstacle, "id", None) == material.id:
                approach_obstacles[index] = copy.copy(obstacle)
                approach_obstacles[index].radius = 0.0
        robot_route = planner.find_path(robot_position, push_position, approach_obstacles)
        if not robot_route:
            continue
        cost = path_length(robot_route) + path_length(object_route)
        value = float(izracunaj_vrednost_materiala(material))
        # Razmerje točk / ocenjena pot daje prednost dragocenemu in dosegljivemu železu.
        score = value / max(150.0, cost)
        candidates.append((score, material, object_route))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, material, route = candidates[0]
    return PushMission(material, snapshot.builder_base.center,
                       snapshot.builder_base, route, "gradbenik", robot_id)


def runGradbenik(gameState, robotPos, robotDir=None, base=None,
                 obstacles=None, safeDistance=None, offset=None):
    """Stara javna funkcija; vrne izbran PushMission za normalizirano stanje."""
    robot_id = str(config.ROBOT_ID)
    return choose_task(gameState, robotPos, robot_id)
