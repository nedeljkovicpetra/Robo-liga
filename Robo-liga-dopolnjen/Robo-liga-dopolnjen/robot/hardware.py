# -*- coding: utf-8 -*-
"""Dostop do para EV3 motorjev; FakeMotors omogoča lokalno testiranje."""
from starter_code import config


class FakeMotor(object):
    def __init__(self, name):
        self.name = name
        self.speed = 0

    def run_forever(self, speed_sp=0):
        self.speed = int(speed_sp)

    def stop(self, stop_action="brake"):
        self.speed = 0


class MotorPair(object):
    def __init__(self, dry_run=False):
        self.dry_run = bool(dry_run)
        if self.dry_run:
            self.left = FakeMotor("left")
            self.right = FakeMotor("right")
        else:
            try:
                from ev3dev2.motor import LargeMotor
            except ImportError:
                raise RuntimeError(
                    "ev3dev2 ni nameščen. Za testiranje na računalniku uporabite --dry-run."
                )
            self.left = LargeMotor(config.MOTOR_LEFT_PORT)
            self.right = LargeMotor(config.MOTOR_RIGHT_PORT)
            if not getattr(self.left, "address", None):
                raise RuntimeError("Levi motor ni zaznan na {}".format(config.MOTOR_LEFT_PORT))
            if not getattr(self.right, "address", None):
                raise RuntimeError("Desni motor ni zaznan na {}".format(config.MOTOR_RIGHT_PORT))

    def run(self, left_speed, right_speed):
        left_speed = int(left_speed)
        right_speed = int(right_speed)
        if config.INVERT_LEFT_MOTOR:
            left_speed = -left_speed
        if config.INVERT_RIGHT_MOTOR:
            right_speed = -right_speed
        self.left.run_forever(speed_sp=left_speed)
        self.right.run_forever(speed_sp=right_speed)

    def stop(self):
        try:
            self.left.stop(stop_action="brake")
        finally:
            self.right.stop(stop_action="brake")

    def close(self):
        self.stop()
