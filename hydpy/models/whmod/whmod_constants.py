"""|whmod.DOCNAME.long| provides two types of constants: those associated with the land
type and those associated with the soil type of the individual zones of a
sub-catchment.  They are all available via wildcard-imports:

>>> from hydpy.models.whmod import *
>>> (GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS, SEALED,
...  WATER)
(1, 2, 3, 4, 5, 6, 7, 8, 9)
>>> (SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE)
(10, 11, 12, 13, 14, 15, 16)
"""

from hydpy.core import parametertools

GRASS = parametertools.IntConstant(1)
"""Land type constant for grassland."""
DECIDUOUS = parametertools.IntConstant(2)
"""Land type constant for deciduous forests."""
CORN = parametertools.IntConstant(3)
"""Land type constant for corn fields."""
CONIFER = parametertools.IntConstant(4)
"""Land type constant for coniferous forests."""
SPRINGWHEAT = parametertools.IntConstant(5)
"""Land type constant for spring wheat fields."""
WINTERWHEAT = parametertools.IntConstant(6)
"""Land type constant for winter wheat fields."""
SUGARBEETS = parametertools.IntConstant(7)
"""Land type constant for sugar beet fields."""
SEALED = parametertools.IntConstant(8)
"""Land type constant for sealed areas."""
WATER = parametertools.IntConstant(9)
"""Land type constant for water areas."""

SAND = parametertools.IntConstant(10)
"""Soil type constant for sand."""
SAND_COHESIVE = parametertools.IntConstant(11)
"""Soil type constant for cohesive sand."""
LOAM = parametertools.IntConstant(12)
"""Soil type constant for loam."""
CLAY = parametertools.IntConstant(13)
"""Soil type constant for clay."""
SILT = parametertools.IntConstant(14)
"""Soil type constant for silt."""
PEAT = parametertools.IntConstant(15)
"""Soil type constant for peat."""
NONE = parametertools.IntConstant(16)
"""Soil type constant for areas without soils."""


CONSTANTS: parametertools.Constants = parametertools.Constants()
LANDTYPE_CONSTANTS: parametertools.Constants = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value <= WATER}
)
SOILTYPE_CONSTANTS: parametertools.Constants = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value >= SAND}
)

# Make only the constants available on wildcard-imports.
__all__ = [
    "GRASS",
    "DECIDUOUS",
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
    "NONE",
]
