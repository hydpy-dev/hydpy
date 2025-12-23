# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Nied(sequencetools.InputSequence):
    """Niederschlag (precipitation) [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class TemL(sequencetools.InputSequence):
    """Lufttemperatur (air temperature) [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.RELATIVE_HUMIDITY


class WindSpeed(sequencetools.InputSequence):
    """Windgeschwindigkeit (wind speed) [m/s]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.WIND_SPEED
