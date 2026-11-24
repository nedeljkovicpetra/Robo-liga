# -*- coding: utf-8 -*-
"""Majhni podatkovni razredi brez zunanjih odvisnosti (združljivo z EV3 Python)."""
import math


class Point(object):
    def __init__(self, position, y=None):
        if isinstance(position, Point):
            self.x, self.y = float(position.x), float(position.y)
        elif y is not None:
            self.x, self.y = float(position), float(y)
        elif isinstance(position, (list, tuple)) and len(position) >= 2:
            self.x, self.y = float(position[0]), float(position[1])
        elif isinstance(position, dict):
            if "position" in position and isinstance(position["position"], dict):
                position = position["position"]
            self.x = float(position["x"])
            self.y = float(position["y"])
        else:
            raise ValueError("Točke ni mogoče pretvoriti iz: {!r}".format(position))

    def __add__(self, other):
        other = Point(other)
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        other = Point(other)
        return Point(self.x - other.x, self.y - other.y)

    def __eq__(self, other):
        try:
            other = Point(other)
            return abs(self.x - other.x) < 1e-6 and abs(self.y - other.y) < 1e-6
        except Exception:
            return False

    def __repr__(self):
        return "Point({:.1f}, {:.1f})".format(self.x, self.y)

    def distance_to(self, other):
        other = Point(other)
        return math.hypot(other.x - self.x, other.y - self.y)

    def as_dict(self):
        return {"x": self.x, "y": self.y}


class Polygon(object):
    """Poligon, sestavljen iz oglišč v koordinatah strežnika (mm)."""
    def __init__(self, points, name=""):
        self.points = [Point(p) for p in points]
        self.name = name
        if len(self.points) < 3:
            raise ValueError("Poligon potrebuje vsaj tri oglišča")

    @property
    def center(self):
        # Središče iz povprečja oglišč je dovolj dobro za pravokotna polja.
        return Point(
            sum(p.x for p in self.points) / float(len(self.points)),
            sum(p.y for p in self.points) / float(len(self.points))
        )

    @property
    def bounds(self):
        return (min(p.x for p in self.points), min(p.y for p in self.points),
                max(p.x for p in self.points), max(p.y for p in self.points))

    def contains(self, point, margin=0.0):
        point = Point(point)
        if margin > 0:
            min_x, min_y, max_x, max_y = self.bounds
            if (point.x < min_x + margin or point.x > max_x - margin or
                    point.y < min_y + margin or point.y > max_y - margin):
                return False
        inside = False
        n = len(self.points)
        j = n - 1
        for i in range(n):
            a = self.points[i]
            b = self.points[j]
            # Točka na robu se šteje kot znotraj.
            cross = ((point.x - a.x) * (b.y - a.y) -
                     (point.y - a.y) * (b.x - a.x))
            if abs(cross) < 1e-6:
                if (min(a.x, b.x) - 1e-6 <= point.x <= max(a.x, b.x) + 1e-6 and
                        min(a.y, b.y) - 1e-6 <= point.y <= max(a.y, b.y) + 1e-6):
                    return True
            intersects = ((a.y > point.y) != (b.y > point.y))
            if intersects:
                x_at_y = (b.x - a.x) * (point.y - a.y) / (b.y - a.y) + a.x
                if point.x < x_at_y:
                    inside = not inside
            j = i
        return inside


class GameObject(object):
    def __init__(self, object_id, position, kind, marker_id=None, raw=None):
        self.id = str(object_id)
        self.position = Point(position)
        self.kind = kind
        self.marker_id = str(marker_id) if marker_id is not None else None
        self.raw = raw or {}
        self.radius = 70.0

    def __repr__(self):
        return "GameObject(id={!r}, kind={!r}, position={!r})".format(
            self.id, self.kind, self.position
        )


class State(object):
    IDLE = 0
    TURN = 1
    DRIVE_STRAIGHT = 2
    LOAD_NEXT_TARGET = 3

    def __init__(self, value=0):
        self.value = value

    def __str__(self):
        return str(self.value)
