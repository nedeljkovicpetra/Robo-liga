# -*- coding: utf-8 -*-
"""Izvedba potiskanja objekta po segmentih z nadzorom prek kamere/strežnika."""
import math
import copy
import time

from starter_code.classes import Point
from starter_code import config
from robot.navigation import PathPlanner, getDistance


class PushMission(object):
    def __init__(self, game_object, destination, destination_polygon, route,
                 role, robot_id):
        self.object_id = str(game_object.id)
        self.object_kind = game_object.kind
        self.destination = Point(destination)
        self.destination_polygon = destination_polygon
        self.route = [Point(point) for point in route]
        self.route_index = 1
        self.role = role
        self.robot_id = str(robot_id)
        self.mode = "APPROACH"
        self.robot_path = None
        self.approach_point = None
        self.approach_object_position = None
        self.desired_heading = None
        self.last_object_position = Point(game_object.position)
        self.last_progress_time = time.time()
        self.plant_since = None
        self.replans = 0
        self.last_status_time = 0.0

    def _inside_destination(self, obj):
        return (self.destination_polygon is not None and
                self.destination_polygon.contains(obj.position))

    def _object_route_is_finished(self, obj):
        return self.route_index >= len(self.route)

    def _obstacles(self, snapshot):
        return snapshot.obstacles(self.object_id, self.robot_id)

    def _approach_obstacles(self, snapshot):
        # Ciljna kocka ostane ovira, da robot do nje ne pripelje skozi njo.
        # Njeno središče obravnavamo kot točko; razdaljo do stika določa
        # PUSH_STANDOFF_MM, druge ovire pa ohranijo polmer cele kocke.
        obstacles = snapshot.obstacles(None, self.robot_id)
        for index, obstacle in enumerate(obstacles):
            if getattr(obstacle, "id", None) == self.object_id:
                obstacles[index] = copy.copy(obstacle)
                obstacles[index].radius = 0.0
        return obstacles

    def _replan_object_route(self, snapshot, obj):
        if self.replans >= config.MAX_REPLANS_PER_OBJECT:
            return False
        planner = PathPlanner(snapshot.game_field)
        route = planner.find_path(obj.position, self.destination, self._obstacles(snapshot))
        if not route or len(route) < 2:
            return False
        self.route = route
        self.route_index = 1
        self.mode = "APPROACH"
        self.robot_path = None
        self.approach_point = None
        self.approach_object_position = None
        self.replans += 1
        self.last_object_position = Point(obj.position)
        self.last_progress_time = time.time()
        return True

    def _update_progress(self, obj, now):
        moved = getDistance(obj.position, self.last_object_position)
        if moved >= 7.0:
            self.last_object_position = Point(obj.position)
            self.last_progress_time = now
        return moved

    def step(self, snapshot, robot_position, robot_direction, navigator):
        """Izvede en krmilni cikel. Vrne RUNNING, DONE ali FAILED."""
        now = time.time()
        robot_position = Point(robot_position)
        obj = snapshot.objects.get(self.object_id)
        if obj is None:
            navigator.stop()
            return "FAILED"

        self._update_progress(obj, now)

        # Pri gradbeniku se točke štejejo takoj, ko je značka znotraj baze.
        if self.role == "gradbenik" and self._inside_destination(obj):
            navigator.stop()
            return "DONE"

        # Pri drevesu mora središče značke ostati na istem polju najmanj 5 s.
        if self.role == "naravovarstvenik" and self._inside_destination(obj):
            navigator.stop()
            if self.plant_since is None:
                self.plant_since = now
            if now - self.plant_since >= config.PLANT_CONFIRM_SECONDS:
                return "DONE"
            return "RUNNING"
        elif self.role == "naravovarstvenik":
            self.plant_since = None

        # Ob vsakem izgubljenem napredku najprej varno ustavimo, nato računamo novo pot.
        if self.mode == "PUSH" and now - self.last_progress_time > config.PUSH_STALL_SECONDS:
            navigator.stop()
            if not self._replan_object_route(snapshot, obj):
                return "FAILED"
            return "RUNNING"

        if self.route_index >= len(self.route):
            if not self._replan_object_route(snapshot, obj):
                return "FAILED"
            return "RUNNING"

        segment_goal = Point(self.route[self.route_index])
        dx = segment_goal.x - obj.position.x
        dy = segment_goal.y - obj.position.y
        segment_distance = math.hypot(dx, dy)

        if segment_distance <= config.PUSH_GOAL_TOLERANCE_MM:
            self.route_index += 1
            self.mode = "APPROACH"
            self.robot_path = None
            self.approach_point = None
            self.approach_object_position = None
            navigator.stop()
            return "RUNNING"

        unit_x = dx / segment_distance
        unit_y = dy / segment_distance
        desired_heading = math.degrees(math.atan2(unit_y, unit_x))
        approach_point = Point(
            obj.position.x - unit_x * config.PUSH_STANDOFF_MM,
            obj.position.y - unit_y * config.PUSH_STANDOFF_MM
        )

        # Faza 1: robot se postavi za kocko. Ciljna točka se osveži, če se
        # kocka med približevanjem opazno premakne.
        if self.mode == "APPROACH":
            if (self.approach_point is None or self.approach_object_position is None or
                    getDistance(obj.position, self.approach_object_position) > 35.0):
                self.approach_point = approach_point
                self.approach_object_position = Point(obj.position)
                self.robot_path = None
            if self.robot_path is None:
                robot_planner = PathPlanner(snapshot.game_field)
                self.robot_path = robot_planner.find_path(
                    robot_position, self.approach_point, self._approach_obstacles(snapshot)
                )
                if not self.robot_path:
                    navigator.stop()
                    return "FAILED"
            arrived = navigator.follow_path(
                robot_position, robot_direction, self.robot_path,
                max_speed=config.SPEED_DRIVE
            )
            if arrived or getDistance(robot_position, self.approach_point) <= config.PUSH_APPROACH_TOLERANCE_MM:
                navigator.stop()
                self.mode = "ALIGN"
                self.desired_heading = desired_heading
                self.approach_point = None
                self.approach_object_position = None
                self.robot_path = None
            return "RUNNING"

        # Faza 2: poravnava pred stikom s kocko.
        if self.mode == "ALIGN":
            if navigator.turn_to_heading(robot_direction, desired_heading):
                self.mode = "PUSH"
                self.last_progress_time = now
                self.last_object_position = Point(obj.position)
                navigator.stop()
            return "RUNNING"

        # Faza 3: robot pelje do točke za kocko in jo s tem potiska naprej.
        # Segment je že preverjen s plannerjem, zato tu ne izvajamo obvoza,
        # ki bi robota odmaknil od predmeta.
        robot_goal = Point(
            segment_goal.x - unit_x * config.PUSH_STANDOFF_MM,
            segment_goal.y - unit_y * config.PUSH_STANDOFF_MM
        )
        arrived = navigator.move_to(
            robot_position, robot_direction, robot_goal,
            max_speed=config.SPEED_PUSH
        )
        if arrived and getDistance(obj.position, segment_goal) > config.PUSH_GOAL_TOLERANCE_MM:
            # Verjetno je bil standoff napačno umerjen ali je kocka zdrsnila.
            # Ponovimo postavitev za trenutno lokacijo; omejeno število poskusov.
            navigator.stop()
            if self.replans < config.MAX_REPLANS_PER_OBJECT:
                self.replans += 1
                self.mode = "APPROACH"
                self.approach_point = None
                self.approach_object_position = None
                self.robot_path = None
                self.last_progress_time = now
                return "RUNNING"
            return "FAILED"
        return "RUNNING"
