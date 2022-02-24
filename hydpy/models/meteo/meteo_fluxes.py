# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class ExtraterrestrialRadiation(sequencetools.FluxSequence):
    """Extraterrestial radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class UnadjustedGlobalRadiation(sequencetools.FluxSequence):
    """Unadjusted global radiation [MJ/m²]."""

    NDIM, NUMERIC = 0, False


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Daily sum of global radiation [MJ/m²/d]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False
