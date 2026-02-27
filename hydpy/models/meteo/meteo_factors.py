# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.meteo import meteo_sequences


class EarthSunDistance(sequencetools.FactorSequence):
    """The relative inverse distance between the Earth and the sun [-]."""

    NDIM = 0
    NUMERIC = False


class SolarDeclination(sequencetools.FactorSequence):
    """Solar declination [-]."""

    NDIM = 0
    NUMERIC = False


class SunsetHourAngle(sequencetools.FactorSequence):
    """Sunset hour angle [rad]."""

    NDIM = 0
    NUMERIC = False


class SolarTimeAngle(sequencetools.FactorSequence):
    """Solar time angle [rad]."""

    NDIM = 0
    NUMERIC = False


class TimeOfSunrise(sequencetools.FactorSequence):
    """Time of sunrise [h]."""

    NDIM = 0
    NUMERIC = False


class TimeOfSunset(sequencetools.FactorSequence):
    """Time of sunset [h]."""

    NDIM = 0
    NUMERIC = False


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible sunshine duration [h]."""

    NDIM = 0
    NUMERIC = False


class DailyPossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible daily sunshine duration [h/d]."""

    NDIM = 0
    NUMERIC = False


class UnadjustedSunshineDuration(sequencetools.FactorSequence):
    """Unadjusted sunshine duration [h]."""

    NDIM = 0
    NUMERIC = False


class SunshineDuration(sequencetools.FactorSequence):
    """Actual sunshine duration [h]."""

    NDIM = 0
    NUMERIC = False


class DailySunshineDuration(sequencetools.FactorSequence):
    """Actual daily sunshine duration [h/d]."""

    NDIM = 0
    NUMERIC = False


class PortionDailyRadiation(sequencetools.FactorSequence):
    """Portion of the daily radiation sum [%]."""

    NDIM = 0
    NUMERIC = False


class Temperature(meteo_sequences.FactorSequence1D):
    """Temperature [°C]."""


class MeanTemperature(sequencetools.FactorSequence):
    """Mean temperature [°C]."""

    NDIM = 0
    NUMERIC = False
