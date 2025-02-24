"""|wland.DOCNAME.long| provides two types of constants: those associated with the
average soil character of a sub-catchment and those associated with the land-use type
of the different hydrological response units of a sub-catchment.  They are all
available via wildcard-imports:

>>> from hydpy.models.wland import *
>>> (SAND, LOAMY_SAND, SANDY_LOAM, SILT_LOAM, LOAM, SANDY_CLAY_LOAM,
... SILT_CLAY_LOAM, CLAY_LOAM, SANDY_CLAY, SILTY_CLAY, CLAY)
(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
>>> (SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE, WETLAND, TREES,
...  CONIFER, DECIDIOUS, MIXED)
(12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22)
"""

# import...
# ...from HydPy
from hydpy.core import parametertools

SAND = parametertools.IntConstant(1)
"""Soil character constant for sand."""
LOAMY_SAND = parametertools.IntConstant(2)
"""Soil character constant for loamy sand."""
SANDY_LOAM = parametertools.IntConstant(3)
"""Soil character constant for sandy loam."""
SILT_LOAM = parametertools.IntConstant(4)
"""Soil character constant for silt loam."""
LOAM = parametertools.IntConstant(5)
"""Soil character constant for loam."""
SANDY_CLAY_LOAM = parametertools.IntConstant(6)
"""Soil character constant for sandy clay loam."""
SILT_CLAY_LOAM = parametertools.IntConstant(7)
"""Soil character constant for silt clay loam."""
CLAY_LOAM = parametertools.IntConstant(8)
"""Soil character constant for clay loam."""
SANDY_CLAY = parametertools.IntConstant(9)
"""Soil character constant for sandy clay."""
SILTY_CLAY = parametertools.IntConstant(10)
"""Soil character constant for silty clay."""
CLAY = parametertools.IntConstant(11)
"""Soil character constant for clay."""

SEALED = parametertools.IntConstant(12)
"""Land type constant for sealed surface."""
FIELD = parametertools.IntConstant(13)
"""Land type constant for fields."""
WINE = parametertools.IntConstant(14)
"""Land type constant for viticulture."""
ORCHARD = parametertools.IntConstant(15)
"""Land type constant for orchards."""
SOIL = parametertools.IntConstant(16)
"""Land type constant for bare, unsealed soils."""
PASTURE = parametertools.IntConstant(17)
"""Land type constant for pasture."""
WETLAND = parametertools.IntConstant(18)
"""Land type constant for wetlands."""
TREES = parametertools.IntConstant(19)
"""Land type constant for loose tree populations."""
CONIFER = parametertools.IntConstant(20)
"""Land type constant for coniferous forests."""
DECIDIOUS = parametertools.IntConstant(21)
"""Land type constant for decidious forests."""
MIXED = parametertools.IntConstant(22)
"""Land type constant for mixed forests."""
WATER = parametertools.IntConstant(23)
"""Land type constant for the surface water storage."""


CONSTANTS = parametertools.Constants()
"""All constants defined by |wland.DOCNAME.long|."""
SOIL_CONSTANTS = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value <= CLAY}
)
"""All soil character constants of |wland.DOCNAME.long|."""
LANDUSE_CONSTANTS = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value >= SEALED}
)
"""All landuse type constants of |wland.DOCNAME.long|."""

__all__ = [
    "SAND",
    "LOAMY_SAND",
    "SANDY_LOAM",
    "SILT_LOAM",
    "LOAM",
    "SANDY_CLAY_LOAM",
    "SILT_CLAY_LOAM",
    "CLAY_LOAM",
    "SANDY_CLAY",
    "SILTY_CLAY",
    "CLAY",
    "SEALED",
    "FIELD",
    "WINE",
    "ORCHARD",
    "SOIL",
    "PASTURE",
    "WETLAND",
    "TREES",
    "CONIFER",
    "DECIDIOUS",
    "MIXED",
    "WATER",
]
