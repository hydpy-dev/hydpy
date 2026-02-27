# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class T(sequencetools.InputSequence):
    """Air temperature [°C]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class FXG(sequencetools.InputSequence):
    """Seepage/extraction (normalised to |AT|) [mm/T]."""

    NDIM = 0
    NUMERIC = True
    STANDARD_NAME = sequencetools.StandardInputNames.ARTIFICIAL_GROUNDWATER_RECHARGE


class FXS(sequencetools.InputSequence):
    """Surface water supply/extraction (normalised to |AT|) [mm/T]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.ARTIFICIAL_SURFACE_WATER_SUPPLY
