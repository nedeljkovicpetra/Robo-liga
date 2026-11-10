from enum import Enum
from robot.gradbenik import runGradbenik


class GradbenikState(Enum):
    SELECT_MATERIAL = 0
    GO_TO_PUSH_POSITION = 1
    ALIGN_WITH_BASE = 2
    PUSH_MATERIAL = 3
    CHECK_DELIVERY = 4


def main():
    #inicijalizacija robota i povezivanje sa serverom
    pass


if __name__ == "__main__":
    main()