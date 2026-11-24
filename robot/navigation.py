# -*- coding: utf-8 -*-
"""Geometrija, načrtovanje poti in krmiljenje diferencialnega pogona EV3."""
import heapq
import math

from starter_code.classes import Point
from starter_code import config
from starter_code.pid import PID


def getDistance(p1, p2):
    return Point(p1).distance_to(Point(p2))


def normalize_angle(angle):
    angle = (float(angle) + 180.0) % 360.0 - 180.0
    return angle


def getAngle(p1, robot_dir, p2):
    p1 = Point(p1)
    p2 = Point(p2)
    absolute = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
    return normalize_angle(absolute - float(robot_dir))


def absolute_angle(p1, p2):
    p1 = Point(p1)
    p2 = Point(p2)
    return math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))


def _obstacle_parts(obstacle):
    if hasattr(obstacle, "position"):
        point = Point(obstacle.position)
        radius = getattr(obstacle, "radius", config.OBJECT_RADIUS_MM)
        return point, float(radius)
    if isinstance(obstacle, dict):
        point = Point(obstacle.get("position", obstacle))
        return point, float(obstacle.get("radius", config.OBJECT_RADIUS_MM))
    return Point(obstacle), float(config.OBJECT_RADIUS_MM)


def _distance_point_segment(point, start, end):
    point = Point(point)
    start = Point(start)
    end = Point(end)
    dx = end.x - start.x
    dy = end.y - start.y
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return point.distance_to(start)
    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    closest = Point(start.x + t * dx, start.y + t * dy)
    return point.distance_to(closest)


class PathPlanner(object):
    """Načrtovalnik vidnostnega grafa okoli krožnih ovir.

    Predmeti se obravnavajo kot krogi. To je konservativna aproksimacija za
    10 x 10 cm kocke in omogoča obvoz brez prečkanja dreves.
    """
    def __init__(self, board=None, clearance=None):
        self.board = board
        self.clearance = (config.ROBOT_CLEARANCE_MM if clearance is None
                          else float(clearance))

    def segment_clear(self, start, end, obstacles):
        start = Point(start)
        end = Point(end)
        if self.board is not None:
            length = start.distance_to(end)
            steps = max(2, int(length / 60.0))
            for i in range(steps + 1):
                t = i / float(steps)
                sample = Point(start.x + (end.x - start.x) * t,
                               start.y + (end.y - start.y) * t)
                if not self.board.contains(sample, margin=self.clearance):
                    return False
        for obstacle in obstacles:
            center, radius = _obstacle_parts(obstacle)
            required = radius + self.clearance
            if _distance_point_segment(center, start, end) < required:
                return False
        return True

    def find_path(self, start, target, obstacles):
        start = Point(start)
        target = Point(target)
        obstacles = list(obstacles or [])
        if start.distance_to(target) < 1.0:
            return [start, target]
        if self.segment_clear(start, target, obstacles):
            return [start, target]

        # Vidnostni graf: dodamo točke okoli vsake krožne ovire.
        nodes = [start, target]
        for obstacle in obstacles:
            center, radius = _obstacle_parts(obstacle)
            offset = radius + self.clearance + 35.0
            for step in range(8):
                angle = math.radians(step * 45.0)
                point = Point(center.x + math.cos(angle) * offset,
                              center.y + math.sin(angle) * offset)
                if self.board is None or self.board.contains(point, margin=self.clearance):
                    # Točka mora biti zunaj vseh drugih ovir.
                    clear = True
                    for other in obstacles:
                        other_center, other_radius = _obstacle_parts(other)
                        if point.distance_to(other_center) < other_radius + self.clearance + 5.0:
                            clear = False
                            break
                    if clear:
                        nodes.append(point)

        graph = [[] for _ in nodes]
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if self.segment_clear(nodes[i], nodes[j], obstacles):
                    weight = nodes[i].distance_to(nodes[j])
                    graph[i].append((j, weight))
                    graph[j].append((i, weight))

        distances = [float("inf")] * len(nodes)
        previous = [None] * len(nodes)
        distances[0] = 0.0
        queue = [(0.0, 0)]
        while queue:
            current_distance, current = heapq.heappop(queue)
            if current_distance > distances[current]:
                continue
            if current == 1:
                break
            for neighbour, cost in graph[current]:
                candidate = current_distance + cost
                if candidate < distances[neighbour]:
                    distances[neighbour] = candidate
                    previous[neighbour] = current
                    heapq.heappush(queue, (candidate, neighbour))

        if distances[1] == float("inf"):
            return []
        indices = []
        current = 1
        while current is not None:
            indices.append(current)
            current = previous[current]
        indices.reverse()
        return [nodes[index] for index in indices]


def path_length(path):
    if not path or len(path) < 2:
        return 0.0
    return sum(Point(path[i]).distance_to(path[i + 1]) for i in range(len(path) - 1))


class Navigator(object):
    """PID-krmiljenje diferencialnega pogona na podlagi sledenja ArUco."""
    def __init__(self, motors):
        self.motors = motors
        self.turn_pid = PID(
            setpoint=0.0, Kp=config.TURN_KP, Ki=config.TURN_KI, Kd=config.TURN_KD,
            integral_limit=config.PID_INTEGRAL_LIMIT, output_limit=config.SPEED_MAX
        )
        self.distance_pid = PID(
            setpoint=0.0, Kp=config.DRIVE_KP, Ki=config.DRIVE_KI, Kd=config.DRIVE_KD,
            integral_limit=config.PID_INTEGRAL_LIMIT, output_limit=config.SPEED_MAX
        )
        self._controller_target = None

    def _select_target(self, target_key):
        if target_key != self._controller_target:
            self.turn_pid.reset()
            self.distance_pid.reset()
            self._controller_target = target_key

    def stop(self):
        self.motors.stop()

    def move_to(self, robot_position, robot_direction, target, max_speed=None):
        robot_position = Point(robot_position)
        target = Point(target)
        self._select_target(("point", round(target.x, 1), round(target.y, 1)))
        distance = robot_position.distance_to(target)
        if distance <= config.DIST_EPS:
            self.stop()
            return True

        angle_error = getAngle(robot_position, robot_direction, target)
        speed_limit = int(max_speed or config.SPEED_DRIVE)
        speed_limit = max(1, min(speed_limit, config.SPEED_MAX))

        if abs(angle_error) > config.TURN_ONLY_ANGLE:
            self.distance_pid.reset()
            # PID pri setpoint=0 vrne negativno vrednost za pozitiven kot;
            # po dogovoru uradne predloge se zato levo kolo vrti nasprotno.
            turn = max(-speed_limit, min(speed_limit, self.turn_pid.update(angle_error)))
            if abs(turn) < config.SPEED_TURN_MIN:
                turn = math.copysign(config.SPEED_TURN_MIN, turn)
            left_speed = -turn
            right_speed = turn
        else:
            base = -self.distance_pid.update(distance)
            base = max(55.0, min(float(speed_limit), base))
            turn = max(-speed_limit * 0.65,
                       min(speed_limit * 0.65, self.turn_pid.update(angle_error)))
            right_speed = base + turn
            left_speed = base - turn

        left_speed = int(round(max(-config.SPEED_MAX, min(config.SPEED_MAX, left_speed))))
        right_speed = int(round(max(-config.SPEED_MAX, min(config.SPEED_MAX, right_speed))))
        self.motors.run(left_speed, right_speed)
        return False

    def follow_path(self, robot_position, robot_direction, path, max_speed=None):
        if not path:
            self.stop()
            return True
        robot_position = Point(robot_position)
        # Pot vsebuje začetno točko in ciljne vmesne točke.
        next_index = 1 if len(path) > 1 else 0
        while next_index < len(path) - 1 and robot_position.distance_to(path[next_index]) <= config.WAYPOINT_EPS:
            next_index += 1
        target = path[next_index]
        arrived = self.move_to(robot_position, robot_direction, target, max_speed)
        if next_index == len(path) - 1 and arrived:
            return True
        return False

    def turn_to_heading(self, robot_direction, desired_heading):
        desired_heading = float(desired_heading)
        self._select_target(("heading", round(normalize_angle(desired_heading), 1)))
        error = normalize_angle(desired_heading - float(robot_direction))
        if abs(error) <= config.DIR_EPS:
            self.stop()
            return True
        limit = min(config.SPEED_DRIVE, config.SPEED_MAX)
        turn = max(-limit, min(limit, self.turn_pid.update(error)))
        if abs(turn) < config.SPEED_TURN_MIN:
            turn = math.copysign(config.SPEED_TURN_MIN, turn)
        self.motors.run(-int(turn), int(turn))
        return False


def targetReached(robotPos, target):
    return getDistance(robotPos, target) <= config.DIST_EPS


def pathClear(start, target, obstacles, safeDistance=None):
    planner = PathPlanner(clearance=(config.ROBOT_CLEARANCE_MM if safeDistance is None
                                     else safeDistance))
    return planner.segment_clear(start, target, obstacles)


def findPath(start, target, obstacles, safeDistance=None):
    planner = PathPlanner(clearance=(config.ROBOT_CLEARANCE_MM if safeDistance is None
                                     else safeDistance))
    return planner.find_path(start, target, obstacles)


def turnToTarget(motor_left, motor_right, angle, pidTurn=None):
    turn = -config.TURN_KP * float(angle)
    turn = max(-config.SPEED_MAX, min(config.SPEED_MAX, turn))
    motor_left.run_forever(speed_sp=int(-turn))
    motor_right.run_forever(speed_sp=int(turn))


def driveToTarget(motor_left, motor_right, distance, angle,
                  pidForward=None, pidTurn=None):
    base = min(config.SPEED_DRIVE, max(55.0, config.DRIVE_KP * float(distance)))
    turn = max(-config.SPEED_DRIVE * 0.65,
               min(config.SPEED_DRIVE * 0.65, -config.TURN_KP * float(angle)))
    motor_right.run_forever(speed_sp=int(base + turn))
    motor_left.run_forever(speed_sp=int(base - turn))


def stopRobot(motor_left, motor_right):
    motor_left.stop(stop_action="brake")
    motor_right.stop(stop_action="brake")

