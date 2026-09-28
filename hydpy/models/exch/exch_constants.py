"""ToDo"""

from hydpy.core import parametertools

ADJUST_NOTHING = parametertools.IntConstant(0)
ADJUST_BRANCH = parametertools.IntConstant(1)
ADJUST_RIVER = parametertools.IntConstant(2)

CONSTANTS = parametertools.Constants()

__all__ = [
"ADJUST_NOTHING",
"ADJUST_BRANCH",
"ADJUST_RIVER",
]
