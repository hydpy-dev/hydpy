# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Rainfall(sequencetools.InputSequence):
    """Rainfall [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class CapillaryRise(sequencetools.InputSequence):
    """Capillary rise [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.CAPILLARY_RISE


class Evaporation(sequencetools.InputSequence):
    """Evaporation [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.EVAPOTRANSPIRATION
