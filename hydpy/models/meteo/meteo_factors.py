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


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Possible astronomical sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class SunshineDuration(sequencetools.FactorSequence):
    """Sunshine duration [h]."""

    NDIM, NUMERIC = 0, False
