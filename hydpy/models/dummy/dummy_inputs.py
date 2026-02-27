# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class InterceptedWater(sequencetools.InputSequence):
    """Intercepted water [mm]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)
    STANDARD_NAME = sequencetools.StandardInputNames.INTERCEPTED_WATER_HRU


class SoilWater(sequencetools.InputSequence):
    """Soil water content [mm]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)
    STANDARD_NAME = sequencetools.StandardInputNames.SOIL_WATER_HRU


class SnowCover(sequencetools.InputSequence):
    """Snow cover degree [-]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)
    STANDARD_NAME = sequencetools.StandardInputNames.SNOW_COVER_DEGREE_HRU


class SnowyCanopy(sequencetools.InputSequence):
    """Snow cover degree in the canopies of tree-like vegetation (is |numpy.nan| for
    non-tree-like vegetation) [-]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)
    STANDARD_NAME = sequencetools.StandardInputNames.SNOW_COVER_DEGREE_CANOPY_HRU


class SnowAlbedo(sequencetools.InputSequence):
    """Snow albedo [-]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, 1.0)
    STANDARD_NAME = sequencetools.StandardInputNames.ALBEDO_HRU
