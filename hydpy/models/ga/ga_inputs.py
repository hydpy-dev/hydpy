# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Rainfall(sequencetools.InputSequence):
    """Rainfall [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class CapillaryRise(sequencetools.InputSequence):
    """Capillary rise [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.CAPILLARY_RISE


class Evaporation(sequencetools.InputSequence):
    """Evaporation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.EVAPOTRANSPIRATION
