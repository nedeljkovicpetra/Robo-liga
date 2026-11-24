# -*- coding: utf-8 -*-
"""Glavna avtonomna zanka za Robo ligo FRI 2026 – Gradbišče."""
import argparse
import json
import sys
import time

from starter_code import config
from starter_code.connection import Connection
from robot.data import GameSnapshot
from robot.hardware import MotorPair
from robot.navigation import Navigator
from robot.gradbenik import choose_task as choose_builder_task
from robot.naravovarstvenik import choose_task as choose_environmentalist_task


def _print_schema_warning(snapshot):
    if not snapshot.unclassified_objects:
        return
    print("OPOZORILO: {} objektov nima prepoznavne vrste. Robot bo ostal ustavljen.".format(
        len(snapshot.unclassified_objects)
    ))
    if config.LOG_OBJECT_SCHEMA:
        for item in snapshot.unclassified_objects[:3]:
            print("  objekt key={!r}, id={!r}, marker_id={!r}, keys={}".format(
                item.get("key"), item.get("id"), item.get("marker_id"), item.get("keys")
            ))
        print("Preverite OBJECT_TYPE_FIELD_CANDIDATES / OBJECT_MARKER_FIELD_CANDIDATES "
              "v starter_code/config.py glede na dejanski JSON s testnega strežnika.")


def inspect_snapshot(raw):
    """Tiskalni način za preverjanje JSON sheme brez premikanja motorjev."""
    snapshot = GameSnapshot(raw)
    robot_pos = snapshot.robot_position(config.ROBOT_ID)
    role = snapshot.role_from_position(robot_pos)
    print("Stanje igre: game_on={}, paused={}, time_left={:.1f}s".format(
        snapshot.game_on, snapshot.game_paused, snapshot.time_left
    ))
    print("Povzetek: {}".format(snapshot.debug_summary()))
    print("Robot {}: position={}, direction={}, detected_role={}".format(
        config.ROBOT_ID, robot_pos, snapshot.robot_direction(config.ROBOT_ID), role
    ))
    print("Polja: {}".format(sorted(snapshot.fields.keys())))
    _print_schema_warning(snapshot)
    return snapshot


def _make_stop_button():
    try:
        from ev3dev2.button import Button
        return Button()
    except Exception:
        return None


def _stop_requested(button):
    if button is None:
        return False
    try:
        return bool(button.down)
    except Exception:
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Avtonomni robot za Robo ligo FRI 2026 – Gradbišče"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="ne krmili fizičnih motorjev; še vedno bere igralni strežnik")
    parser.add_argument("--inspect-json", metavar="PATH",
                        help="preveri lokalni JSON in konča brez povezave/motorjev")
    parser.add_argument("--max-iterations", type=int, default=0,
                        help="omeji število ciklov (0 = brez omejitve)")
    args = parser.parse_args(argv)

    if args.inspect_json:
        try:
            with open(args.inspect_json, "r") as source:
                raw = json.load(source)
            inspect_snapshot(raw)
            return 0
        except Exception as err:
            print("Napaka pri branju JSON: {}".format(err))
            return 2

    if not config.GAME_ID or config.GAME_ID == "CHANGE_ME":
        print("NAPAKA: nastavite GAME_ID v starter_code/config.py ali okoljski spremenljivki.")
        return 2

    motors = None
    connection = None
    try:
        motors = MotorPair(dry_run=args.dry_run)
        navigator = Navigator(motors)
        connection = Connection(config.SERVER_URL, config.GAME_ID,
                                timeout=config.SERVER_TIMEOUT)
        button = _make_stop_button()
        print("Robo liga FRI 2026 – Gradbišče")
        print("GET {}".format(connection.url))
        print("ROBOT_ID={}, ROBOT_ROLE={}".format(config.ROBOT_ID, config.ROBOT_ROLE))
        if args.dry_run:
            print("DRY-RUN: fizični motorji niso priključeni.")

        role = None
        mission = None
        completed_ids = set()
        failed_ids = set()
        last_warning = 0.0
        last_summary = 0.0
        was_game_on = False
        iterations = 0

        while not _stop_requested(button):
            if args.max_iterations and iterations >= args.max_iterations:
                break
            iterations += 1

            raw = connection.request(debug=False)
            if raw is None:
                navigator.stop()
                now = time.time()
                if now - last_warning > 3.0:
                    print("Strežnik trenutno ni dosegljiv: {}".format(connection.last_error))
                    last_warning = now
                time.sleep(config.POLL_INTERVAL)
                continue

            snapshot = GameSnapshot(raw)
            robot_position = snapshot.robot_position(config.ROBOT_ID)
            robot_direction = snapshot.robot_direction(config.ROBOT_ID)

            # Prvič vlogo preberemo takoj, ko je robot v eni od baz, tudi če
            # program zaženemo tik po začetku. Menjavo vloge zaznavamo med odmori.
            if robot_position is not None and (role is None or not snapshot.game_on):
                detected_role = snapshot.role_from_position(robot_position)
                if detected_role and detected_role != role:
                    role = detected_role
                    mission = None
                    completed_ids = set()
                    failed_ids = set()
                    print("Zaznana vloga robota: {}".format(role))

            # Pravilo tekme: motorji smejo delovati samo med aktivno in nezaustavljeno igro.
            if (not snapshot.game_on or snapshot.game_paused or snapshot.time_left <= 0.0):
                navigator.stop()
                if was_game_on and not snapshot.game_on:
                    mission = None
                    completed_ids = set()
                    failed_ids = set()
                was_game_on = snapshot.game_on
                time.sleep(config.POLL_INTERVAL)
                continue
            was_game_on = True

            if robot_position is None or robot_direction is None:
                navigator.stop()
                now = time.time()
                if now - last_warning > 2.0:
                    print("Sledilnik ne vidi značke robota {} – motorji ustavljeni.".format(
                        config.ROBOT_ID
                    ))
                    last_warning = now
                time.sleep(config.POLL_INTERVAL)
                continue

            if snapshot.game_field is None:
                navigator.stop()
                now = time.time()
                if now - last_warning > 2.0:
                    print("Manjka poligon game_field; brez meja polja se robot ne bo premikal.")
                    last_warning = now
                time.sleep(config.POLL_INTERVAL)
                continue

            if snapshot.unclassified_objects:
                navigator.stop()
                now = time.time()
                if now - last_warning > 2.0:
                    _print_schema_warning(snapshot)
                    last_warning = now
                time.sleep(config.POLL_INTERVAL)
                continue

            if role == "gradbenik" and snapshot.builder_base is None:
                navigator.stop()
                time.sleep(config.POLL_INTERVAL)
                continue
            if role == "naravovarstvenik" and (
                    snapshot.environmentalist_base is None or not snapshot.planting_fields):
                navigator.stop()
                time.sleep(config.POLL_INTERVAL)
                continue

            if role not in ("gradbenik", "naravovarstvenik"):
                navigator.stop()
                now = time.time()
                if now - last_warning > 2.0:
                    print("Vloge ni mogoče določiti. Preverite polji construction_site in environmentalists.")
                    last_warning = now
                time.sleep(config.POLL_INTERVAL)
                continue

            if mission is None:
                if role == "gradbenik":
                    mission = choose_builder_task(snapshot, robot_position,
                                                  config.ROBOT_ID, completed_ids | failed_ids)
                else:
                    mission = choose_environmentalist_task(
                        snapshot, robot_position, config.ROBOT_ID,
                        completed_ids | failed_ids
                    )
                if mission is None:
                    navigator.stop()
                    now = time.time()
                    if now - last_summary > 3.0:
                        print("Ni dosegljivega cilja. {}".format(snapshot.debug_summary()))
                        _print_schema_warning(snapshot)
                        last_summary = now
                    time.sleep(config.POLL_INTERVAL)
                    continue
                print("Nov cilj: object_id={}, type={}, role={}, destination={}".format(
                    mission.object_id, mission.object_kind, role, mission.destination
                ))

            result = mission.step(snapshot, robot_position, robot_direction, navigator)
            if result == "DONE":
                navigator.stop()
                completed_ids.add(mission.object_id)
                print("Cilj {} zaključen.".format(mission.object_id))
                mission = None
            elif result == "FAILED":
                navigator.stop()
                failed_ids.add(mission.object_id)
                print("Cilj {} ni izvedljiv; preskakujem ga.".format(mission.object_id))
                mission = None

            time.sleep(config.POLL_INTERVAL)

        print("Ustavljam robota.")
        return 0
    except KeyboardInterrupt:
        print("Prekinjeno s tipkovnico.")
        return 0
    except Exception as err:
        print("KRITIČNA NAPAKA: {}".format(err))
        return 1
    finally:
        if motors is not None:
            motors.stop()
            motors.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    sys.exit(main())
