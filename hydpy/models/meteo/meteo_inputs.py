# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class PossibleSunshineDuration(sequencetools.InputSequence):
    """Possible sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.POSSIBLE_SUNSHINE_DURATION


class SunshineDuration(sequencetools.InputSequence):
    """Sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.SUNSHINE_DURATION


class ClearSkySolarRadiation(sequencetools.InputSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.CLEAR_SKY_SOLAR_RADIATION


class GlobalRadiation(sequencetools.InputSequence):
    """Global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.GLOBAL_RADIATION


class Temperature(sequencetools.InputSequence):
    """Temperature [°C]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION
