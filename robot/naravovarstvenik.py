import math
from starter_code.classes import Point
#from robot.gradbenik import getPushPosition, goToPushPosition, allignWithplantingField
from robot.navigation import findPath, getAngle, driveToTarget, getDistance

#PRONALAZENJE DRVECA
def findTrees(gameState):
    trees = gameState.get("trees", [])
    return trees

def selectTrees(robotPos, trees):
    if not trees:
        return None
    
    closestTree = None
    minDistance = float("inf")
    
    for tree in trees:
        distance = getDistance(robotPos, trees)
        if distance < minDistance:
            minDistance = distance
            closestTree = tree
    return closestTree

#SADNJA
def findPlantingFields(gameState):
    fields = gameState.get("plantingFields", [])
    return fields

def selectPlantingFields(tree, fields):
    if not fields:
        return None

    closestField = None
    minDistance = float("inf")

    for field in fields:
        distance = getDistance(tree, field)
        if distance < minDistance:
            minDistance = distance
            closestField = field
    return closestField

#POZICIONIRANJE ROBOTA
def getPushPosition(tree, plantingField, offset):
    dx = plantingField.x - tree.x
    dy = plantingField.y - tree.y

    distance = math.sqrt(dx**2 + dy**2)

    if distance == 0:
        return None

    pushX = tree.x - (dx / distance) * offset
    pushY = tree.y - (dy / distance) * offset
    return Point({"x": pushX, "y": pushY})

def goToPushPosition(robotPos, pushPos, obstacles, safeDistance):
    path = findPath(robotPos, pushPos, obstacles, safeDistance)
    return path

def allignWithfield(robotPos, robotDir, plantingField):
    angle = getAngle(robotPos, robotDir, plantingField)
    return angle

#GURANJE
def pushTree(motor_left, motor_right, distance, angle, pidForward, pidTurn):
    driveToTarget(motor_left, motor_right, distance, angle, pidForward, pidTurn)

#POSADJENO 1 ILI 0
def treePlanted(treePos, plantingField):
    if (plantingField["minX"] <= treePos.x <= plantingField["maxX"] and plantingField["minY"] <= treePos.y <= base["maxY"]):
        return 1
    return 0

#####
def runNavarovarstvenik(gameState, robotPos, robotDir, obstacles, safeDistance, offset):
    trees = findTrees(gameState)
    if not trees:
        return None

    tree = selectPlantingFields(robotPos, trees)
    if not tree:
        return None

    fields = findPlantingFields(gameState)
    if not fields:
        return None

    plantingField = selectPlantingFields(tree, fields)
    if not plantingField:
        return None

    pushPosition = getPushPosition(tree, plantingField, offset)
    if pushPosition is None:
        return None

    path = goToPushPosition(robotPos, pushPosition, obstacles, safeDistance)
    if not path:
        return None

    return {"tree": tree, "plantingField": plantingField, "pushPosition": pushPosition, "path": path}