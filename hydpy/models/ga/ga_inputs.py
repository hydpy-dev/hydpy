# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Rainfall(sequencetools.InputSequence):
    """Rainfall [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class CapillaryRise(sequencetools.InputSequence):
    """Capillary rise [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.CAPILLARY_RISE


class Evaporation(sequencetools.InputSequence):
    """Evaporation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.EVAPOTRANSPIRATION
