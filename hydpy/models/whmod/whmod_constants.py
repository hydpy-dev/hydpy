from hydpy.core import parametertools

GRAS = parametertools.IntConstant(1)
"""WHMod: 0"""
DECIDIOUS = parametertools.IntConstant(2)
"""WHMod: 1"""
CORN = parametertools.IntConstant(3)
"""WHMod: 2"""
CONIFER = parametertools.IntConstant(4)
"""WHMod: 3"""
SPRINGWHEAT = parametertools.IntConstant(5)
"""WHMod: 4"""
WINTERWHEAT = parametertools.IntConstant(6)
"""WHMod: 5"""
SUGARBEETS = parametertools.IntConstant(7)
"""WHMod: 6"""
SEALED = parametertools.IntConstant(8)
"""WHMod: 7"""
WATER = parametertools.IntConstant(9)
"""WHMod: 8"""

SAND = parametertools.IntConstant(10)
SAND_COHESIVE = parametertools.IntConstant(11)
LOAM = parametertools.IntConstant(12)
CLAY = parametertools.IntConstant(13)
SILT = parametertools.IntConstant(14)
PEAT = parametertools.IntConstant(15)


CONSTANTS: parametertools.Constants = parametertools.Constants()
LANDUSE_CONSTANTS: parametertools.Constants = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value <= WATER}
)
SOIL_CONSTANTS: parametertools.Constants = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value >= SAND}
)

# Make only the constants available on wildcard-imports.
__all__ = [
    "GRAS",
    "DECIDIOUS",
    "CORN",
    "CONIFER",
    "SPRINGWHEAT",
    "WINTERWHEAT",
    "SUGARBEETS",
    "SEALED",
    "WATER",
    "SAND",
    "SAND_COHESIVE",
    "LOAM",
    "CLAY",
    "SILT",
    "PEAT",
]
