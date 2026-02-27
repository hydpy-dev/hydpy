# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

from hydpy.models.evap import evap_sequences


class Precipitation(evap_sequences.FluxSequence1D):
    """Precipitation [mm/T]."""


class DailyPrecipitation(evap_sequences.FluxSequence1D):
    """The precipitation sum of the last 24 hours [mm/d]."""


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Average global radiation in the last 24 hours [W/m²]."""

    NDIM: Final[Literal[0]] = 0


class NetShortwaveRadiation(evap_sequences.FluxSequence1D):
    """Net shortwave radiation [W/m²]."""


class DailyNetShortwaveRadiation(evap_sequences.FluxSequence1D):
    """Average net shortwave radiation in the last 24 hours [W/m²]."""


class NetLongwaveRadiation(evap_sequences.FluxSequence1D):
    """Net longwave radiation [W/m²]."""


class DailyNetLongwaveRadiation(evap_sequences.FluxSequence1D):
    """Average net longwave radiation in the last 24 hours [W/m²]."""


class NetRadiation(evap_sequences.FluxSequence1D):
    """Total net radiation [W/m²]."""


class DailyNetRadiation(evap_sequences.FluxSequence1D):
    """Average net radiation in the last 24 hours [W/m²]."""


class SoilHeatFlux(evap_sequences.FluxSequence1D):
    """Soil heat flux [W/m²]."""


class ReferenceEvapotranspiration(evap_sequences.FluxSequence1D):
    """Reference (grass) evapotranspiration [mm/T]."""


class PotentialInterceptionEvaporation(evap_sequences.FluxSequence1D):
    """Potential interception evaporation [mm/T]."""


class PotentialSoilEvapotranspiration(evap_sequences.FluxSequence1D):
    """Potential evapotranspiration from soils [mm/T]."""


class PotentialEvapotranspiration(evap_sequences.FluxSequence1D):
    """Potential (land type-specific) evapotranspiration [mm/T]."""


class DailyPotentialSoilEvapotranspiration(evap_sequences.FluxSequence1D):
    """The potential soil evapotranspiration sum of the last 24 hours [mm/d]."""


class MeanReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Mean reference evapotranspiration [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class MeanPotentialEvapotranspiration(sequencetools.FluxSequence):
    """Mean potential evapotranspiration [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class PotentialWaterEvaporation(evap_sequences.FluxSequence1D):
    """Potential evaporation from open water areas [mm/T]."""


class WaterEvaporation(evap_sequences.FluxSequence1D):
    """Actual evaporation from open water areas [mm/T]."""


class DailyWaterEvaporation(evap_sequences.FluxSequence1D):
    """The water evaporation sum of the last 24 hours [mm/d]."""


class InterceptionEvaporation(evap_sequences.FluxSequence1D):
    """Actual interception evaporation [mm/T]."""


class SoilEvapotranspiration(evap_sequences.FluxSequence1D):
    """Actual soil evapotranspiration [mm/T]."""
