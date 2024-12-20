# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.evap import evap_sequences


class Precipitation(evap_sequences.FluxSequence1D):
    """Precipitation [mm/T]."""

    NUMERIC = False


class DailyPrecipitation(evap_sequences.FluxSequence1D):
    """The precipitation sum of the last 24 hours [mm/d]."""

    NUMERIC = False


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Average global radiation in the last 24 hours [W/m²]."""

    NDIM, NUMERIC = 0, False


class NetShortwaveRadiation(evap_sequences.FluxSequence1D):
    """Net shortwave radiation [W/m²]."""

    NUMERIC = False


class DailyNetShortwaveRadiation(evap_sequences.FluxSequence1D):
    """Average net shortwave radiation in the last 24 hours [W/m²]."""

    NUMERIC = False


class NetLongwaveRadiation(evap_sequences.FluxSequence1D):
    """Net longwave radiation [W/m²]."""

    NUMERIC = False


class DailyNetLongwaveRadiation(evap_sequences.FluxSequence1D):
    """Average net longwave radiation in the last 24 hours [W/m²]."""

    NUMERIC = False


class NetRadiation(evap_sequences.FluxSequence1D):
    """Total net radiation [W/m²]."""

    NUMERIC = False


class DailyNetRadiation(evap_sequences.FluxSequence1D):
    """Average net radiation in the last 24 hours [W/m²]."""

    NUMERIC = False


class SoilHeatFlux(evap_sequences.FluxSequence1D):
    """Soil heat flux [W/m²]."""

    NUMERIC = False


class ReferenceEvapotranspiration(evap_sequences.FluxSequence1D):
    """Reference (grass) evapotranspiration [mm/T]."""

    NUMERIC = False


class PotentialInterceptionEvaporation(evap_sequences.FluxSequence1D):
    """Potential interception evaporation [mm/T]."""

    NUMERIC = False


class PotentialSoilEvapotranspiration(evap_sequences.FluxSequence1D):
    """Potential evapotranspiration from soils [mm/T]."""

    NUMERIC = False


class PotentialEvapotranspiration(evap_sequences.FluxSequence1D):
    """Potential (land type-specific) evapotranspiration [mm/T]."""

    NUMERIC = False


class DailyPotentialSoilEvapotranspiration(evap_sequences.FluxSequence1D):
    """The potential soil evapotranspiration sum of the last 24 hours [mm/d]."""

    NUMERIC = False


class MeanReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Mean reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class MeanPotentialEvapotranspiration(sequencetools.FluxSequence):
    """Mean potential evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class PotentialWaterEvaporation(evap_sequences.FluxSequence1D):
    """Potential evaporation from open water areas [mm/T]."""

    NUMERIC = False


class WaterEvaporation(evap_sequences.FluxSequence1D):
    """Actual evaporation from open water areas [mm/T]."""

    NUMERIC = False


class DailyWaterEvaporation(evap_sequences.FluxSequence1D):
    """The water evaporation sum of the last 24 hours [mm/d]."""

    NUMERIC = False


class InterceptionEvaporation(evap_sequences.FluxSequence1D):
    """Actual interception evaporation [mm/T]."""

    NUMERIC = False


class SoilEvapotranspiration(evap_sequences.FluxSequence1D):
    """Actual soil evapotranspiration [mm/T]."""

    NUMERIC = False
