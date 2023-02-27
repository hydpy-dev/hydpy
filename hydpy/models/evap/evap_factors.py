# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.evap import evap_sequences


class AdjustedAirTemperature(evap_sequences.FactorSequence1D):
    """Adjusted air temperature [°C]."""

    NUMERIC = False


class AdjustedWindSpeed(sequencetools.FactorSequence):
    """Adjusted wind speed [m/s]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(evap_sequences.FactorSequence1D):
    """Saturation vapour pressure [hPa]."""

    NUMERIC = False


class SaturationVapourPressureSlope(evap_sequences.FactorSequence1D):
    """The slope of the saturation vapour pressure curve [hPa/K]."""

    NUMERIC = False


class ActualVapourPressure(evap_sequences.FactorSequence1D):
    """Actual vapour pressure [hPa]."""

    NUMERIC = False


class PsychrometricConstant(sequencetools.FactorSequence):
    """Psychrometric constant [hPa/K]."""

    NDIM, NUMERIC = 0, False
