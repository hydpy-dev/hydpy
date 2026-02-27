# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

from hydpy.models.meteo import meteo_sequences


class ExtraterrestrialRadiation(sequencetools.FluxSequence):
    """Extraterrestial radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class UnadjustedGlobalRadiation(sequencetools.FluxSequence):
    """Unadjusted global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Daily sum of global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class Precipitation(meteo_sequences.FluxSequence1D):
    """Precipitation [mm/T]."""


class MeanPrecipitation(sequencetools.FluxSequence):
    """Mean precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
