# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class PossibleSunshineDuration(sequencetools.InputSequence):
    """Possible sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class SunshineDuration(sequencetools.InputSequence):
    """Sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.InputSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.InputSequence):
    """Global radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class Temperature(sequencetools.InputSequence):
    """Temperature [°C]."""

    NDIM, NUMERIC = 0, False


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False
