# -*- coding: utf-8 -*-
import json
import os
import unittest

from starter_code.classes import Point, Polygon
from robot.data import GameSnapshot
from robot.navigation import PathPlanner, path_length
from robot.hardware import MotorPair
from robot.navigation import Navigator
from robot.gradbenik import choose_task as choose_builder_task, _builder_obstacles
from robot.naravovarstvenik import choose_task as choose_tree_task


BASE = os.path.dirname(__file__)


def sample():
    with open(os.path.join(BASE, "sample_construction_game.json"), "r") as handle:
        return json.load(handle)


class GeometryTests(unittest.TestCase):
    def test_polygon_contains_and_center(self):
        polygon = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        self.assertTrue(polygon.contains(Point(50, 50)))
        self.assertFalse(polygon.contains(Point(150, 50)))
        self.assertEqual(polygon.center, Point(50, 50))

    def test_path_planner_goes_around_obstacle_and_respects_board_edge(self):
        board = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        obstacle = {"position": {"x": 500, "y": 500}, "radius": 80}
        planner = PathPlanner(board, clearance=100)
        route = planner.find_path(Point(100, 500), Point(900, 500), [obstacle])
        self.assertGreaterEqual(len(route), 3)
        self.assertGreater(path_length(route), 800)
        for index in range(len(route) - 1):
            self.assertTrue(planner.segment_clear(route[index], route[index + 1], [obstacle]))
        self.assertFalse(planner.segment_clear(Point(50, 200), Point(250, 200), []))


class DataTests(unittest.TestCase):
    def test_parser_reads_objects_fields_and_role(self):
        snapshot = GameSnapshot(sample())
        self.assertEqual(len(snapshot.materials), 2)
        self.assertEqual(len(snapshot.trees), 2)
        self.assertIsNotNone(snapshot.builder_base)
        self.assertIsNotNone(snapshot.environmentalist_base)
        self.assertEqual(snapshot.role_from_position(Point(300, 1000)), "gradbenik")
        self.assertEqual(snapshot.role_from_position(Point(2600, 1000)), "naravovarstvenik")
        self.assertGreater(len(snapshot.planting_fields), 0)
        self.assertEqual(len(snapshot.tile_fields), 28)

    def test_unknown_objects_are_not_guessed(self):
        data = sample()
        data["objects"] = {"random": {"id": "random-uuid", "position": {"x": 500, "y": 500}}}
        snapshot = GameSnapshot(data)
        self.assertEqual(len(snapshot.unclassified_objects), 1)
        self.assertEqual(len(snapshot.materials), 0)
        self.assertEqual(len(snapshot.trees), 0)

    def test_builder_obstacles_cover_tree_field(self):
        data = sample()
        data["objects"]["trees"]["t1"]["position"] = {"x": 3250, "y": 1000}
        snapshot = GameSnapshot(data)
        # T1 je v zeleni bazi: ni ga mogoče posaditi, vendar je še vedno
        # polje s kocko, ki se mu mora gradbenik izogniti.
        planted = next(field for field in snapshot.tile_fields
                       if field.contains(snapshot.trees[0].position))
        obstacles = _builder_obstacles(snapshot, None, "25")
        field_obstacle = next(item for item in obstacles
                              if getattr(item, "kind", None) == "tree_field")
        self.assertGreaterEqual(
            field_obstacle.radius,
            max(planted.center.distance_to(vertex) for vertex in planted.points) - 1e-6
        )
        planner = PathPlanner(snapshot.game_field)
        self.assertFalse(planner.segment_clear(
            Point(2500, 1000), Point(3500, 1000), obstacles
        ))

    def test_marker_ids_choose_subtypes_inside_groups(self):
        data = sample()
        data["objects"]["construction_material"] = {
            "mat-steel": {"id": "mat-steel", "marker_id": 47,
                          "position": {"x": 1200, "y": 500}},
            "mat-brick": {"id": "mat-brick", "marker_id": 10,
                          "position": {"x": 1800, "y": 1500}}
        }
        data["objects"]["trees"] = {
            "tree-cherry": {"id": "tree-cherry", "marker_id": 24,
                            "position": {"x": 3000, "y": 900}},
            "tree-pine": {"id": "tree-pine", "marker_id": 40,
                          "position": {"x": 3400, "y": 1100}}
        }
        snapshot = GameSnapshot(data)
        self.assertEqual({obj.kind for obj in snapshot.materials}, {"steel", "brick"})
        self.assertEqual({obj.kind for obj in snapshot.trees}, {"cherry", "pine"})

    def test_strategy_selects_tasks(self):
        snapshot = GameSnapshot(sample())
        builder = choose_builder_task(snapshot, Point(300, 1000), "25")
        self.assertIsNotNone(builder)
        self.assertEqual(builder.role, "gradbenik")
        # Robota z zelenega izhodišča obravnavamo kot naravovarstvenika.
        env_task = choose_tree_task(snapshot, Point(2600, 1000), "12")
        self.assertIsNotNone(env_task)
        self.assertEqual(env_task.role, "naravovarstvenik")
        # Izračun pristopne poti ne sme spreminjati polmera objektov v stanju.
        for obj in snapshot.objects.values():
            self.assertEqual(obj.radius, 70.0)


class HardwareTests(unittest.TestCase):
    def test_fake_motor_pair_and_navigation(self):
        motors = MotorPair(dry_run=True)
        navigator = Navigator(motors)
        arrived = navigator.move_to(Point(100, 100), 0, Point(500, 100))
        self.assertFalse(arrived)
        self.assertNotEqual(motors.left.speed, 0)
        navigator.stop()
        self.assertEqual(motors.left.speed, 0)
        self.assertEqual(motors.right.speed, 0)


if __name__ == "__main__":
    unittest.main()
