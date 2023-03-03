# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.meteo import meteo_sequences


class ExtraterrestrialRadiation(sequencetools.FluxSequence):
    """Extraterrestial radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class UnadjustedGlobalRadiation(sequencetools.FluxSequence):
    """Unadjusted global radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Daily sum of global radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class Precipitation(meteo_sequences.FluxSequence1D):
    """Precipitation [mm/T]."""


class MeanPrecipitation(sequencetools.FluxSequence):
    """Mean precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False
