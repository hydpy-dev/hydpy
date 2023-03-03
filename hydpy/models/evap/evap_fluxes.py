# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.evap import evap_sequences


class Precipitation(evap_sequences.FluxSequence1D):
    """Precipitation [mm/T]."""

    NUMERIC = False


class NetShortwaveRadiation(sequencetools.FluxSequence):
    """Net shortwave radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class NetLongwaveRadiation(evap_sequences.FluxSequence1D):
    """Net longwave radiation [W/m²]."""

    NUMERIC = False


class NetRadiation(evap_sequences.FluxSequence1D):
    """Total net radiation [W/m²]."""

    NUMERIC = False


class SoilHeatFlux(evap_sequences.FluxSequence1D):
    """Soil heat flux [W/m²]."""

    NUMERIC = False


class ReferenceEvapotranspiration(evap_sequences.FluxSequence1D):
    """Reference (grass) evapotranspiration [mm/T]."""

    NUMERIC = False


class PotentialEvapotranspiration(evap_sequences.FluxSequence1D):
    """Potential (land use-specific) evapotranspiration [mm/T]."""

    NUMERIC = False


class MeanReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Mean reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class MeanPotentialEvapotranspiration(sequencetools.FluxSequence):
    """Mean potential evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False
