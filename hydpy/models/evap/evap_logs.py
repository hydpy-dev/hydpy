# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedAirTemperature(sequencetools.LogSequence):
    """Logged air temperature [°C]."""

    NDIM, NUMERIC = 2, False


class LoggedWindSpeed2m(sequencetools.LogSequence):
    """Logged wind speed at 2 m above grass-like vegetation [m/s]."""

    NDIM, NUMERIC = 1, False


class LoggedRelativeHumidity(sequencetools.LogSequence):
    """Logged relative humidity [%]."""

    NDIM, NUMERIC = 1, False


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM, NUMERIC = 1, False


class LoggedPossibleSunshineDuration(sequencetools.LogSequence):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM, NUMERIC = 1, False


class LoggedGlobalRadiation(sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM, NUMERIC = 1, False


class LoggedClearSkySolarRadiation(sequencetools.LogSequence):
    """Logged clear sky radiation [W/m²]."""

    NDIM, NUMERIC = 1, False
