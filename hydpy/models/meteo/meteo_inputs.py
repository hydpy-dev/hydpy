# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class PossibleSunshineDuration(sequencetools.InputSequence):
    """Possible sunshine duration [h]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.POSSIBLE_SUNSHINE_DURATION


class SunshineDuration(sequencetools.InputSequence):
    """Sunshine duration [h]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.SUNSHINE_DURATION


class ClearSkySolarRadiation(sequencetools.InputSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.CLEAR_SKY_SOLAR_RADIATION


class GlobalRadiation(sequencetools.InputSequence):
    """Global radiation [W/m²]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.GLOBAL_RADIATION


class Temperature(sequencetools.InputSequence):
    """Temperature [°C]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION
