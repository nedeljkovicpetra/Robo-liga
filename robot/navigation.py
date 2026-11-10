#OVO IM JE ZAJEDNICKO, ZNACI U SUSTINI KRETANJE I TAKO TE GLUPOSTI
import math
from starter_code.config import SPEED_BASE_MAX, SPEED_MAX, DIST_EPS

def getDistance (p1, p2):
    distance = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
    return distance

def getAngle (p1, robotDir, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y

    angle = math.degrees(math.atan2(dy, dx))
    relativeAngle = angle - robotDir

    if abs(relativeAngle) > 180:
        if relativeAngle > 0:
            relativeAngle -= 360
        else:
            relativeAngle += 360
    return relativeAngle

#KRETANJE
def turnToTarget (motor_left, motor_right, angle, pidTurn):
    uTurn = pidTurn.update(measurement=angle)

    speedRight = uTurn
    speedLeft = -uTurn

    speedRight = round(min(max(speedRight, -SPEED_MAX), SPEED_MAX))  #config.py 21
    speedLeft = round(min(max(speedLeft, -SPEED_MAX), SPEED_MAX))

    motor_right.run_forever(speed_sp=speedRight)
    motor_left.run_forever(speed_sp=speedLeft)

def driveToTarget (motor_left, motor_right, distance, angle, pidForward, pidTurn):
    uBase = pidForward.update(measurement=distance)
    uTurn = pidTurn.update(measurement=angle)

    uBase = min(max(uBase, -SPEED_BASE_MAX), SPEED_BASE_MAX)  #config.py 24

    speedRight = -uBase + uTurn  #pid.py 104
    speedLeft = -uBase - uTurn

def stopRobot (motor_left, motor_right):
    motor_left.stop(stop_action='brake')
    motor_right.stop(stop_action='brake')

#NAVIGACIJA
def targetReached (robotPos, target):
    distance = getDistance(robotPos, target)

    if distance <= DIST_EPS:   #config.py 40
        return 1
    return 0

def pathClear (start, target, obstacles, safeDistance):
    dx = target.x - start.x
    dy = target.y - start.y

    lengthSquared = dx**2 + dy**2

    for obstacle in obstacles:
        if lengthSquared == 0:
            distance = getDistance(start, obstacle)
        else:
            t = ((obstacle.x - start.x) * dx + (obstacle.y - start.y) * dy) / lengthSquared
            t = max(0, min(1, t))

            closestX = start.x + t * dx
            closestY = start.y + t * dy
            distance = math.sqrt((obstacle.x - closestX)**2 + (obstacle.y - closestY)**2)

            if distance <= safeDistance:
                return 0
            return 1

def findPath (start, target, obstacles):
    if pathClear(start, target, obstacles):
        return [target]
    return []