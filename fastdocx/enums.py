from enum import Enum, IntEnum

from fastdocx.units import Color


class HeadingLevel(IntEnum):
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


class Alignment(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2
    JUSTIFY = 3


class ColorName(Enum):
    BLACK = Color(0, 0, 0)
    WHITE = Color(255, 255, 255)
    DARK_RED = Color(139, 0, 0)
    RED = Color(255, 0, 0)
    ORANGE = Color(255, 165, 0)
    YELLOW = Color(255, 255, 0)
    LIGHT_GREEN = Color(144, 238, 144)
    GREEN = Color(0, 255, 0)
    LIGHT_BLUE = Color(173, 216, 230)
    BLUE = Color(0, 0, 255)
    DARK_BLUE = Color(0, 0, 139)
    PURPLE = Color(128, 0, 128)

    @property
    def color(self) -> Color:
        return self.value
