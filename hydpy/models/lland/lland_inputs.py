# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Nied(sequencetools.InputSequence):
    """Niederschlag (precipitation) [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class TemL(sequencetools.InputSequence):
    """Lufttemperatur (air temperature) [°C]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.RELATIVE_HUMIDITY


class WindSpeed(sequencetools.InputSequence):
    """Windgeschwindigkeit (wind speed) [m/s]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.WIND_SPEED
