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

def driveToTarget (motor_left, motor_right, distance, angle, forward, turn):

    pass

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