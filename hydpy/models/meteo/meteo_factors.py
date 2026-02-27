# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

from hydpy.models.meteo import meteo_sequences


class EarthSunDistance(sequencetools.FactorSequence):
    """The relative inverse distance between the Earth and the sun [-]."""

    NDIM: Final[Literal[0]] = 0


class SolarDeclination(sequencetools.FactorSequence):
    """Solar declination [-]."""

    NDIM: Final[Literal[0]] = 0


class SunsetHourAngle(sequencetools.FactorSequence):
    """Sunset hour angle [rad]."""

    NDIM: Final[Literal[0]] = 0


class SolarTimeAngle(sequencetools.FactorSequence):
    """Solar time angle [rad]."""

    NDIM: Final[Literal[0]] = 0


class TimeOfSunrise(sequencetools.FactorSequence):
    """Time of sunrise [h]."""

    NDIM: Final[Literal[0]] = 0


class TimeOfSunset(sequencetools.FactorSequence):
    """Time of sunset [h]."""

    NDIM: Final[Literal[0]] = 0


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0


class DailyPossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible daily sunshine duration [h/d]."""

    NDIM: Final[Literal[0]] = 0


class UnadjustedSunshineDuration(sequencetools.FactorSequence):
    """Unadjusted sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0


class SunshineDuration(sequencetools.FactorSequence):
    """Actual sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0


class DailySunshineDuration(sequencetools.FactorSequence):
    """Actual daily sunshine duration [h/d]."""

    NDIM: Final[Literal[0]] = 0


class PortionDailyRadiation(sequencetools.FactorSequence):
    """Portion of the daily radiation sum [%]."""

    NDIM: Final[Literal[0]] = 0


class Temperature(meteo_sequences.FactorSequence1D):
    """Temperature [°C]."""


class MeanTemperature(sequencetools.FactorSequence):
    """Mean temperature [°C]."""

    NDIM: Final[Literal[0]] = 0
