# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class EarthSunDistance(sequencetools.FactorSequence):
    """The relative inverse distance between the earth and the sun [-]."""

    NDIM, NUMERIC = 0, False


class SolarDeclination(sequencetools.FactorSequence):
    """Solar declination [-]."""

    NDIM, NUMERIC = 0, False


class SunsetHourAngle(sequencetools.FactorSequence):
    """Sunset hour angle [rad]."""

    NDIM, NUMERIC = 0, False


class SolarTimeAngle(sequencetools.FactorSequence):
    """Solar time angle [rad]."""

    NDIM, NUMERIC = 0, False


class TimeOfSunrise(sequencetools.FactorSequence):
    """Time of sunrise [h]."""

    NDIM, NUMERIC = 0, False


class TimeOfSunset(sequencetools.FactorSequence):
    """Time of sunset [h]."""

    NDIM, NUMERIC = 0, False


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class DailyPossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible daily sunshine duration [h/d]."""

    NDIM, NUMERIC = 0, False


class UnadjustedSunshineDuration(sequencetools.FactorSequence):
    """Unadjusted sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class SunshineDuration(sequencetools.FactorSequence):
    """Actual sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class DailySunshineDuration(sequencetools.FactorSequence):
    """Actual daily sunshine duration [h/d]."""

    NDIM, NUMERIC = 0, False


class PortionDailyRadiation(sequencetools.FactorSequence):
    """Portion of the daily radiation sum [%]."""

    NDIM, NUMERIC = 0, False
