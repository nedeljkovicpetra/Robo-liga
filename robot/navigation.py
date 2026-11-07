#OVO IM JE ZAJEDNICKO, ZNACI U SUSTINI KRETANJE I TAKO TE GLUPOSTI

def getDistance (p1, p2):
    #udaljenost dve poy
    pass

def getAngel (p1, robotDir, p2):
    #ugao izmedju pravca robota i cilja
    pass

#KRETANJE
def turnToTarget (target):
    #self explanatory
    pass

def driveToTarget (motor_left, motor_right, distance, angle, pidForward, pidTurn):
    uBase = pidForward.update(measurement=distance)
    uTurn = pidTurn.update(measurement=angle)

    uBase = min(max(uBase, -SPEED_BASE_MAX), SPEED_BASE_MAX)  #config.py 24

    speedRight = -uBase + uTurn  #pid.py 104
    speedLeft = -uBase - uTurn

    speedRight = round(min(max(speedRight, -SPEED_MAX), SPEED_MAX))  #config.py 21
    speedLeft = round(min(max(speedLeft, -SPEED_MAX), SPEED_MAX))

    motor_right.run_forever(speed_sp=speedRight)
    motor_left.run_forever(speed_sp=speedLeft)

def stopRobot (motor_left, motor_right):
    motor_left.stop(stop_action='brake')
    motor_right.stop(stop_action='brake')

#NAVIGACIJA
def targetReached (robotPos, target):
    #take a wild guess
    pass

def pathClear (start, target, obstacles):
    #i wonder what this one does
    pass

def findPath (start, target, obstacles):
    #od pocetne do final destination
    pass