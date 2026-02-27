# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Nied(sequencetools.InputSequence):
    """Niederschlag (precipitation) [mm/T]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class TemL(sequencetools.InputSequence):
    """Lufttemperatur (air temperature) [°C]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.RELATIVE_HUMIDITY


class WindSpeed(sequencetools.InputSequence):
    """Windgeschwindigkeit (wind speed) [m/s]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.WIND_SPEED
