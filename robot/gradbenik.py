import math
from starter_code.classes import Point
from robot.navigation import findPath, getAngle, driveToTarget, getDistance

#PRONALAZENJE MATERIJALA
def findMaterial(gameState):
    materials = gameState.get("materials", [])
    return materials

def selectMaterial(robotPos, materials):
    if not materials:
        return None

    closestMaterial = None
    minDistance = float("inf")

    for material in materials:
        distance = getDistance(robotPos, material)
        if distance < minDistance:
            minDistance = distance
            closestMaterial = material

    return closestMaterial

#POZICIONIRANJE ROBOTA
def getPushPosition(material, base, offset):
    dx = base.x - material.x
    dy = base.y - material.y

    distance = math.sqrt(dx**2 + dy**2)

    if distance == 0:
        return None

    pushX = material.x - (dx / distance) * offset
    pushY = material.y - (dy / distance) * offset

    return Point({"x": pushX, "y": pushY})

def goToPushPosition(robotPos, pushPos, obstacles, safeDistance):
    path = findPath(robotPos, pushPos, obstacles, safeDistance)

    return path

def allignWithBase(robotPos, robotDir, base):
    angle = getAngle(robotPos, robotDir, base)

    return angle

#GURANJE MATERIJALA
def pushMaterial(motor_left, motor_right, distance, angle, pidForward, pidTurn):
    driveToTarget(motor_left, motor_right, distance, angle, pidForward, pidTurn)

#DOSTAVA 1 ILI 0
def materialDelievered(materialPos, base):
    if (base["minX"] <= materialPos.x <= base["maxX"] and base["minY"] <= materialPos.y <= base["maxY"]):
        return 1
    return 0

def runGradbenik(gameState, robotPos, robotDir, base, obstacles, safeDistance, offset):
    materials = findMaterial(gameState)
    if not materials:
        return None

    material = selectMaterial(robotPos, materials)
    if material is None:
        return None

    pushPosition = getPushPosition(material, base, offset)
    if pushPosition is None:
        return None

    path = goToPushPosition(robotPos, pushPosition, obstacles, safeDistance)
    if not path:
        return None

    return {
        "material": material,
        "pushPosition": pushPosition,
        "path": path,
        "base": base
    }