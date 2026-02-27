# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class T(sequencetools.InputSequence):
    """Mean air temperature [°C]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class TMin(sequencetools.InputSequence):
    """Minimum air temperature [°C]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.MINIMUM_AIR_TEMPERATURE


class TMax(sequencetools.InputSequence):
    """Maximum air temperature [°C]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.MAXIMUM_AIR_TEMPERATURE
