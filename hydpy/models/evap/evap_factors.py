# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class AdjustedAirTemperature(sequencetools.FactorSequence):
    """Adjusted air temperature [°C]."""

    NDIM, NUMERIC = 1, False


class AdjustedWindSpeed(sequencetools.FactorSequence):
    """Adjusted wind speed [m/s]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(sequencetools.FactorSequence):
    """Saturation vapour pressure [hPa]."""

    NDIM, NUMERIC = 1, False


class SaturationVapourPressureSlope(sequencetools.FactorSequence):
    """The slope of the saturation vapour pressure curve [hPa/K]."""

    NDIM, NUMERIC = 1, False


class ActualVapourPressure(sequencetools.FactorSequence):
    """Actual vapour pressure [hPa]."""

    NDIM, NUMERIC = 1, False


class PsychrometricConstant(sequencetools.FactorSequence):
    """Psychrometric constant [hPa/K]."""

    NDIM, NUMERIC = 0, False
