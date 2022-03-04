# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class AirTemperature(sequencetools.InputSequence):
    """Air temperature [°C]."""

    NDIM, NUMERIC = 0, False


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM, NUMERIC = 0, False


class WindSpeed(sequencetools.InputSequence):
    """Wind speed [m/s]."""

    NDIM, NUMERIC = 0, False


class AtmosphericPressure(sequencetools.InputSequence):
    """Atmospheric pressure [kPA]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.InputSequence):
    """Global radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.InputSequence):
    """Clear sky solar radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False
