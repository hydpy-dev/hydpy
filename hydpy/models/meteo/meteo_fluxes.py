# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.meteo import meteo_sequences


class ExtraterrestrialRadiation(sequencetools.FluxSequence):
    """Extraterrestial radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class UnadjustedGlobalRadiation(sequencetools.FluxSequence):
    """Unadjusted global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Daily sum of global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class Precipitation(meteo_sequences.FluxSequence1D):
    """Precipitation [mm/T]."""


class MeanPrecipitation(sequencetools.FluxSequence):
    """Mean precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
