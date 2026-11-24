# -*- coding: utf-8 -*-
"""Preprost PID regulator z zaščito pred deljenjem z nič in wind-upom."""
import time


class PID(object):
    def __init__(self, setpoint=0.0, Kp=1.0, Ki=0.0, Kd=0.0,
                 integral_limit=None, output_limit=None):
        self.setpoint = float(setpoint)
        self.Kp = float(Kp)
        self.Ki = float(Ki or 0.0)
        self.Kd = float(Kd or 0.0)
        self.integral_limit = integral_limit
        self.output_limit = output_limit
        self.reset()

    def reset(self, setpoint=None):
        if setpoint is not None:
            self.setpoint = float(setpoint)
        self._integral = 0.0
        self._last_error = None
        self._last_time = None

    def update(self, measurement, now=None):
        now = time.time() if now is None else float(now)
        error = self.setpoint - float(measurement)
        if self._last_time is None:
            dt = 0.0
            derivative = 0.0
        else:
            dt = max(0.0, now - self._last_time)
            derivative = ((error - self._last_error) / dt
                          if dt > 1e-6 else 0.0)
        if dt > 0.0:
            self._integral += error * dt
            if self.integral_limit is not None:
                limit = abs(float(self.integral_limit))
                self._integral = max(-limit, min(limit, self._integral))
        output = self.Kp * error + self.Ki * self._integral + self.Kd * derivative
        if self.output_limit is not None:
            limit = abs(float(self.output_limit))
            output = max(-limit, min(limit, output))
        self._last_error = error
        self._last_time = now
        return output
