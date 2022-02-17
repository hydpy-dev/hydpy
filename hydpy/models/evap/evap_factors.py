# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class AdjustedWindSpeed(sequencetools.FactorSequence):
    """Adjusted wind speed [m/s]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(sequencetools.FactorSequence):
    """Saturation vapour pressure [kPa]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressureSlope(sequencetools.FactorSequence):
    """The slope of the saturation vapour pressure curve [kPa/°C]."""

    NDIM, NUMERIC = 0, False


class ActualVapourPressure(sequencetools.FactorSequence):
    """Actual vapour pressure [kPa]."""

    NDIM, NUMERIC = 0, False


class PsychrometricConstant(sequencetools.FactorSequence):
    """Psychrometric constant [kPa/°C]."""

    NDIM, NUMERIC = 0, False
