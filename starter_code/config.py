# -*- coding: utf-8 -*-
"""Nastavitve za Robo ligo FRI 2026 – Gradbišče.

Pred tekmo preverite ROBOT_ID, GAME_ID, SERVER_URL in priklope motorjev.
Datoteka ne uvaža ev3dev2, zato jo lahko uporabljamo tudi pri testiranju na PC.
"""
import os


def _env(name, default):
    value = os.environ.get(name)
    return value if value is not None and value != "" else default


def _env_float(name, default):
    try:
        return float(_env(name, str(default)))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name, default):
    try:
        return int(_env(name, str(default)))
    except (TypeError, ValueError):
        return int(default)


# --- Strežnik in identiteta robota -----------------------------------------
ROBOT_ID = _env("ROBOT_ID", "25")
GAME_ID = _env("GAME_ID", "CHANGE_ME")
# Naslov monitorja/igralnega strežnika iz predstavitve izziva.
SERVER_URL = _env("SERVER_URL", "http://192.168.1.137:8088")
SERVER_TIMEOUT = _env_float("SERVER_TIMEOUT", 1.5)
POLL_INTERVAL = _env_float("POLL_INTERVAL", 0.15)

# "auto" zazna vlogo po začetnem položaju v eni od baz. Lahko nastavite
# eksplicitno "gradbenik" ali "naravovarstvenik", če je to na poligonu potrebno.
ROBOT_ROLE = _env("ROBOT_ROLE", "auto").lower()

# --- EV3 priklopi ------------------------------------------------------------
# ev3dev2 pričakuje vrednosti "outB", "outC" itd.
MOTOR_LEFT_PORT = _env("MOTOR_LEFT_PORT", "outC")
MOTOR_RIGHT_PORT = _env("MOTOR_RIGHT_PORT", "outB")
INVERT_LEFT_MOTOR = _env("INVERT_LEFT_MOTOR", "0") == "1"
INVERT_RIGHT_MOTOR = _env("INVERT_RIGHT_MOTOR", "0") == "1"

# --- Navigacija (vse razdalje so v mm, koti v stopinjah) --------------------
SPEED_MAX = _env_int("SPEED_MAX", 350)
SPEED_DRIVE = _env_int("SPEED_DRIVE", 260)
SPEED_PUSH = _env_int("SPEED_PUSH", 170)
SPEED_TURN_MIN = _env_int("SPEED_TURN_MIN", 65)
DRIVE_KP = _env_float("DRIVE_KP", 0.85)
DRIVE_KI = _env_float("DRIVE_KI", 0.0)
DRIVE_KD = _env_float("DRIVE_KD", 0.0)
TURN_KP = _env_float("TURN_KP", 2.2)
TURN_KI = _env_float("TURN_KI", 0.0)
TURN_KD = _env_float("TURN_KD", 0.0)
PID_INTEGRAL_LIMIT = _env_float("PID_INTEGRAL_LIMIT", 1000.0)
TURN_ONLY_ANGLE = _env_float("TURN_ONLY_ANGLE", 38.0)
DIST_EPS = _env_float("DIST_EPS", 35.0)
DIR_EPS = _env_float("DIR_EPS", 5.0)
WAYPOINT_EPS = _env_float("WAYPOINT_EPS", 55.0)

# Geometrija robota in predmetov. PUSH_STANDOFF_MM je razdalja med središčem
# značke kocke in središčem značke robota, ko se sprednji potiskač dotakne kocke.
# To vrednost je treba umeriti na dejanskem robotu.
ROBOT_CLEARANCE_MM = _env_float("ROBOT_CLEARANCE_MM", 110.0)
OBJECT_RADIUS_MM = _env_float("OBJECT_RADIUS_MM", 70.0)
PUSH_STANDOFF_MM = _env_float("PUSH_STANDOFF_MM", 115.0)
PUSH_APPROACH_TOLERANCE_MM = _env_float("PUSH_APPROACH_TOLERANCE_MM", 45.0)
PUSH_GOAL_TOLERANCE_MM = _env_float("PUSH_GOAL_TOLERANCE_MM", 65.0)
PUSH_STALL_SECONDS = _env_float("PUSH_STALL_SECONDS", 3.0)
MAX_REPLANS_PER_OBJECT = _env_int("MAX_REPLANS_PER_OBJECT", 2)

# Čas, ki ga drevo mora preživeti na istem polju, je po pravilih 5 s.
# Dodamo majhno rezervo zaradi zakasnitve osveževanja podatkov.
PLANT_CONFIRM_SECONDS = _env_float("PLANT_CONFIRM_SECONDS", 5.3)

# --- Vloge, polja in objekti iz konstrukcijske igre -------------------------
# Imena polj so iz konfiguracije igre na strežniku. Parser podpira tudi
# pogostejša alternativna imena, če se testni strežnik razlikuje.
GAME_FIELD_KEYS = ("game_field", "playfield", "arena")
BUILDER_BASE_KEYS = ("construction_site", "builder_base", "red_base", "construction_base")
ENVIRONMENTALIST_BASE_KEYS = ("environmentalists", "environmentalist_base", "green_base", "tree_base")
TREE_FIELD_COLUMNS = _env_int("TREE_FIELD_COLUMNS", 7)
TREE_FIELD_ROWS = _env_int("TREE_FIELD_ROWS", 4)
MAX_PLANT_FIELDS_TO_EVALUATE = _env_int("MAX_PLANT_FIELDS_TO_EVALUATE", 10)

# Skupine objektov, če jih strežnik vrne ločeno.
MATERIAL_GROUP_KEYS = ("construction_material", "construction_materials", "materials", "bricks")
TREE_GROUP_KEYS = ("trees", "tree", "planting_trees")

# Polja, ki lahko vsebujejo tip objekta oziroma ID značke. Če se shema
# strežnika spremeni, dodajte ustrezno ime v te sezname.
OBJECT_TYPE_FIELD_CANDIDATES = (
    "type", "object_type", "kind", "category", "class", "name", "group", "species", "material_type"
)
OBJECT_MARKER_FIELD_CANDIDATES = (
    "marker_id", "aruco_id", "tag_id", "fiducial_id", "marker", "tag", "type_id"
)

# ID-ji značk iz trenutne konfiguracije konstrukcijske igre. Prekrivajoči se
# ID 29 je namenoma obravnavan kot dvoumen in se samodejno ne razvršča.
MATERIAL_MARKER_IDS = ("47", "0", "29", "10", "43", "22")
TREE_MARKER_IDS = ("24", "40", "36", "30", "42", "29")
STEEL_MARKER_IDS = ("47",)
CHERRY_MARKER_IDS = ("24",)

# Točke v predstavitvi izziva: opeka 2, železo 4, smreka 1, češnja 2.
# Aktualna game_config.yaml na uradnem strežniku je ob pripravi projekta
# navajala pine=2 in cherry=4. Vrednosti spodaj sledijo priloženi predstavitvi;
# prilagodite jih dejanskemu točkovanju na tekmovalnem strežniku.
POINTS_BRICK = _env_int("POINTS_BRICK", 2)
POINTS_STEEL = _env_int("POINTS_STEEL", 4)
POINTS_PINE = _env_int("POINTS_PINE", 1)
POINTS_CHERRY = _env_int("POINTS_CHERRY", 2)

# Varnost: ob neznani shemi ne premikamo robota na podlagi ugibanja.
LOG_OBJECT_SCHEMA = _env("LOG_OBJECT_SCHEMA", "1") == "1"
