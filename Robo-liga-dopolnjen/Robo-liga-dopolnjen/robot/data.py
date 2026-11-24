# -*- coding: utf-8 -*-
"""Pretvorba JSON stanja tekme v varne, normalizirane objekte in poligone.

Strežnik v osnovi pošilja robots, objects in fields. Ker PDF ne določa vseh
podključev v objects za Gradbišče, parser podpira več običajnih zapisov in
ob neznani shemi ne ugiba vrste objekta.
"""
import re

from starter_code.classes import Point, Polygon, GameObject
from starter_code import config


class GameSnapshot(object):
    def __init__(self, raw):
        self.raw = raw or {}
        self.game_on = bool(self.raw.get("game_on", False))
        self.game_paused = bool(self.raw.get("game_paused", False))
        try:
            self.time_left = float(self.raw.get("time_left", 0.0))
        except (TypeError, ValueError):
            self.time_left = 0.0
        self.robots = self.raw.get("robots", {}) or {}
        self.teams = self.raw.get("teams", {}) or {}
        self.objects = {}
        self.materials = []
        self.trees = []
        self.unclassified_objects = []
        self.fields = {}
        self.tile_fields = []
        self.planting_fields = []
        self.game_field = None
        self.builder_base = None
        self.environmentalist_base = None
        self._parse_fields()
        self._parse_objects()

    def robot_data(self, robot_id):
        return self.robots.get(str(robot_id))

    def robot_position(self, robot_id):
        data = self.robot_data(robot_id)
        if not isinstance(data, dict) or not isinstance(data.get("position"), dict):
            return None
        try:
            return Point(data["position"])
        except (KeyError, TypeError, ValueError):
            return None

    def robot_direction(self, robot_id):
        data = self.robot_data(robot_id)
        if not isinstance(data, dict):
            return None
        try:
            return float(data.get("dir", data.get("direction")))
        except (TypeError, ValueError):
            return None

    def team_data(self, robot_id):
        return self.teams.get(str(robot_id), {}) or {}

    def role_from_position(self, position):
        fixed = getattr(config, "ROBOT_ROLE", "auto")
        if fixed in ("gradbenik", "naravovarstvenik"):
            return fixed
        if position is None:
            return None
        if self.builder_base is not None and self.builder_base.contains(position):
            return "gradbenik"
        if (self.environmentalist_base is not None and
                self.environmentalist_base.contains(position)):
            return "naravovarstvenik"
        return None

    def obstacles(self, exclude_object_id=None, robot_id=None):
        result = []
        for obj in self.objects.values():
            if exclude_object_id is not None and obj.id == str(exclude_object_id):
                continue
            result.append(obj)
        for other_id, robot in self.robots.items():
            if robot_id is not None and str(other_id) == str(robot_id):
                continue
            if not isinstance(robot, dict):
                continue
            try:
                result.append(GameObject("robot-" + str(other_id), robot["position"],
                                         "robot", raw=robot))
            except (KeyError, TypeError, ValueError):
                pass
        return result

    def _parse_fields(self):
        raw_fields = self.raw.get("fields", {}) or {}
        if not isinstance(raw_fields, dict):
            return

        # Najprej obdelamo vsa direktna polja.
        for name, value in raw_fields.items():
            polygon = _parse_polygon(value, name)
            if polygon is not None:
                self.fields[str(name)] = polygon

        # Nekatere strežniške različice lahko tree_fields zapakirajo v seznam
        # ali slovar znotraj fields.
        nested = raw_fields.get("tree_fields")
        if isinstance(nested, dict):
            for name, value in nested.items():
                polygon = _parse_polygon(value, "tree_" + str(name))
                if polygon is not None:
                    self.fields[polygon.name] = polygon
        elif isinstance(nested, list):
            for index, value in enumerate(nested):
                polygon = _parse_polygon(value, "tree_{}".format(index))
                if polygon is not None:
                    self.fields[polygon.name] = polygon

        self.game_field = _find_field(self.fields, config.GAME_FIELD_KEYS)
        self.builder_base = _find_field(self.fields, config.BUILDER_BASE_KEYS)
        self.environmentalist_base = _find_field(
            self.fields, config.ENVIRONMENTALIST_BASE_KEYS
        )

        reserved = set([str(k).lower() for k in config.GAME_FIELD_KEYS +
                        config.BUILDER_BASE_KEYS + config.ENVIRONMENTALIST_BASE_KEYS])
        for name, polygon in self.fields.items():
            low = name.lower()
            if low in reserved or low == "tree_fields":
                continue
            # Posamezna polja so uporabna tako za sajenje kot za pravilo kazni.
            # Za sajenje izločimo bazna polja, za izogibanje gradbenika pa
            # ohranimo tudi njihove celice.
            self.tile_fields.append(polygon)

        # V konfiguraciji Gradbišča je mreža drevesnih polj določena kot 7 x 4.
        # Če strežnik pošlje le game_field in obe bazi, polja izpeljemo iz
        # štirih oglišč game_field. Posamezni poligoni imajo prednost, če so na voljo.
        if not self.tile_fields and self.game_field is not None:
            self.tile_fields = _generate_grid_fields(
                self.game_field, config.TREE_FIELD_COLUMNS, config.TREE_FIELD_ROWS
            )

        self.planting_fields = []
        for index, polygon in enumerate(self.tile_fields):
            if self.builder_base is not None and self.builder_base.contains(polygon.center):
                continue
            if (self.environmentalist_base is not None and
                    self.environmentalist_base.contains(polygon.center)):
                continue
            if not polygon.name:
                polygon.name = "planting_field_{}".format(index)
            self.planting_fields.append(polygon)

    def _parse_objects(self):
        raw_objects = self.raw.get("objects", {}) or {}
        candidates = []

        # Dovolimo, da strežnik vrne skupine neposredno na vrhu JSON.
        for key in config.MATERIAL_GROUP_KEYS:
            if key in self.raw:
                candidates.extend(_flatten_group(self.raw.get(key), "material", key))
        for key in config.TREE_GROUP_KEYS:
            if key in self.raw:
                candidates.extend(_flatten_group(self.raw.get(key), "tree", key))

        # Standardni format je objects={random_id: {id, position, dir, ...}}.
        if isinstance(raw_objects, dict):
            grouped = False
            for key, value in raw_objects.items():
                normalized = _group_kind(key)
                if normalized:
                    grouped = True
                    candidates.extend(_flatten_group(value, normalized, key))
            if not grouped:
                candidates.extend(_flatten_group(raw_objects, None, None))
        elif isinstance(raw_objects, list):
            candidates.extend(_flatten_group(raw_objects, None, None))

        seen = set()
        for key, item, group_kind in candidates:
            if not isinstance(item, dict):
                continue
            pos_data = item.get("position", item)
            try:
                position = Point(pos_data)
            except (TypeError, ValueError, KeyError):
                continue

            object_id = item.get("id", key)
            if object_id is None:
                object_id = key
            object_id = str(object_id)
            if object_id in seen:
                continue
            seen.add(object_id)

            marker_id = _marker_id(item)
            kind, subtype = _classify_object(item, key, group_kind, marker_id)
            if kind is None:
                self.unclassified_objects.append({
                    "key": key, "id": object_id, "keys": list(item.keys()),
                    "marker_id": marker_id, "raw": item
                })
                continue

            obj = GameObject(object_id, position, subtype or kind,
                             marker_id=marker_id, raw=item)
            obj.group_kind = kind
            self.objects[obj.id] = obj
            if kind == "material":
                self.materials.append(obj)
            elif kind == "tree":
                self.trees.append(obj)

    def debug_summary(self):
        return ("robots={}, materials={}, trees={}, tile_fields={}, planting_fields={}, "
                "unknown_objects={}, builder_base={}, environmentalist_base={}").format(
                    len(self.robots), len(self.materials), len(self.trees),
                    len(self.tile_fields), len(self.planting_fields), len(self.unclassified_objects),
                    self.builder_base is not None,
                    self.environmentalist_base is not None
                )



def _generate_grid_fields(board, columns, rows):
    """Izračuna mrežo enakomernih kvadratnih polj z bilinearno interpolacijo."""
    if columns <= 0 or rows <= 0 or len(board.points) != 4:
        return []
    # Red oglišč v parserju je TL, TR, BR, BL.
    tl, tr, br, bl = board.points

    def interpolate(u, v):
        top_x = tl.x + (tr.x - tl.x) * u
        top_y = tl.y + (tr.y - tl.y) * u
        bottom_x = bl.x + (br.x - bl.x) * u
        bottom_y = bl.y + (br.y - bl.y) * u
        return Point(top_x + (bottom_x - top_x) * v,
                     top_y + (bottom_y - top_y) * v)

    result = []
    for row in range(rows):
        for col in range(columns):
            u0 = col / float(columns)
            u1 = (col + 1) / float(columns)
            v0 = row / float(rows)
            v1 = (row + 1) / float(rows)
            result.append(Polygon([
                interpolate(u0, v0), interpolate(u1, v0),
                interpolate(u1, v1), interpolate(u0, v1)
            ], "planting_field_{}_{}".format(row, col)))
    return result

def _parse_polygon(value, name):
    if isinstance(value, Polygon):
        return value
    if not isinstance(value, (dict, list, tuple)):
        return None

    # Pogosti oblici zapisa: {top_left: {x,y}, ...}, vertices:[...],
    # points:[...] ali minX/minY/maxX/maxY.
    if isinstance(value, dict):
        for collection_key in ("vertices", "points", "corners", "polygon"):
            if collection_key in value:
                polygon = _parse_polygon(value[collection_key], name)
                if polygon is not None:
                    return polygon
        if all(key in value for key in ("minX", "minY", "maxX", "maxY")):
            return Polygon([
                (value["minX"], value["minY"]),
                (value["maxX"], value["minY"]),
                (value["maxX"], value["maxY"]),
                (value["minX"], value["maxY"])
            ], name)
        corner_order = ("top_left", "top_right", "bottom_right", "bottom_left")
        if all(key in value for key in corner_order):
            try:
                return Polygon([value[key] for key in corner_order], name)
            except (TypeError, ValueError, KeyError):
                return None
        # Če so vse vrednosti videti kot točke, uporabimo njihov vrstni red.
        values = list(value.values())
    else:
        values = list(value)

    try:
        points = [Point(v) for v in values if _looks_like_point(v)]
        if len(points) >= 3:
            return Polygon(points, name)
    except (TypeError, ValueError, KeyError):
        return None
    return None


def _looks_like_point(value):
    if isinstance(value, Point):
        return True
    if isinstance(value, (list, tuple)):
        return len(value) >= 2 and isinstance(value[0], (int, float))
    if isinstance(value, dict):
        if "position" in value and isinstance(value["position"], dict):
            value = value["position"]
        return "x" in value and "y" in value
    return False


def _find_field(fields, aliases):
    for alias in aliases:
        for name, polygon in fields.items():
            if str(name).lower() == str(alias).lower():
                return polygon
    return None


def _flatten_group(group, group_kind, group_key):
    result = []
    if group is None:
        return result
    if isinstance(group, list):
        for index, item in enumerate(group):
            result.append((item.get("id", index) if isinstance(item, dict) else index,
                           item, group_kind))
    elif isinstance(group, dict):
        if "position" in group or ("x" in group and "y" in group):
            result.append((group.get("id", group_key), group, group_kind))
        else:
            for key, item in group.items():
                result.append((key, item, group_kind))
    return result


def _group_kind(name):
    low = str(name).lower()
    if low in [v.lower() for v in config.MATERIAL_GROUP_KEYS]:
        return "material"
    if low in [v.lower() for v in config.TREE_GROUP_KEYS]:
        return "tree"
    return None


def _marker_id(item):
    for key in config.OBJECT_MARKER_FIELD_CANDIDATES:
        if key in item:
            value = item[key]
            if isinstance(value, dict):
                for nested in ("id", "marker_id", "tag_id", "value"):
                    if nested in value:
                        return str(value[nested])
            if value is not None:
                return str(value)
    return None


def _classify_object(item, collection_key, group_kind, marker_id):
    """Vrsto določi iz skupine/opisa, podvrsto pa po polju ali znački.

    ID objekta ni nujno ArUco ID. Kot nadomestek ga uporabimo samo, če se
    njegova vrednost ujema z enim od znanih ID-jev značk.
    """
    text_parts = []
    if group_kind:
        text_parts.append(group_kind)
    if collection_key is not None:
        text_parts.append(str(collection_key))
    for key in config.OBJECT_TYPE_FIELD_CANDIDATES:
        if key in item and item[key] is not None:
            value = item[key]
            if isinstance(value, (str, int, float)):
                text_parts.append(str(value))
    text = " ".join(text_parts).lower()
    compact = re.sub(r"[^a-z0-9]+", "_", text)

    materials = set(str(v) for v in config.MATERIAL_MARKER_IDS)
    trees = set(str(v) for v in config.TREE_MARKER_IDS)
    common = materials.intersection(trees)
    marker = str(marker_id) if marker_id is not None else None
    if marker is None:
        raw_id = item.get("id")
        if raw_id is not None and str(raw_id) in materials.union(trees):
            marker = str(raw_id)
        elif collection_key is not None and str(collection_key) in materials.union(trees):
            marker = str(collection_key)

    is_tree = any(token in compact for token in
                  ("tree", "pine", "spruce", "cherry", "smreka", "cesnja"))
    is_material = any(token in compact for token in
                      ("material", "brick", "steel", "iron", "opeka", "zelezo"))

    # Izrecna podvrsta v JSON-u ima prednost pred privzeto skupino.
    if "cherry" in compact or "cesnja" in compact or "japonska" in compact:
        return "tree", "cherry"
    if "pine" in compact or "spruce" in compact or "smreka" in compact:
        return "tree", "pine"
    if "steel" in compact or "iron" in compact or "zelezo" in compact:
        return "material", "steel"
    if "brick" in compact or "opeka" in compact:
        return "material", "brick"

    # Splošna skupina pove, kaj objekt je; značka pove, katere vrste je.
    if is_tree or (marker in trees and marker not in common):
        subtype = "cherry" if marker in config.CHERRY_MARKER_IDS else "pine"
        return "tree", subtype
    if is_material or (marker in materials and marker not in common):
        subtype = "steel" if marker in config.STEEL_MARKER_IDS else "brick"
        return "material", subtype

    # ID 29 je po trenutno objavljeni konfiguraciji v obeh skupinah in je brez
    # dodatnega podatka dvoumen, zato ga namenoma ne razvrstimo.
    return None, None
