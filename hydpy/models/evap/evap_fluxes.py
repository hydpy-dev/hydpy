# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class NetShortwaveRadiation(sequencetools.FluxSequence):
    """Net shortwave radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class NetLongwaveRadiation(sequencetools.FluxSequence):
    """Net longwave radiation [W/m²]."""

    NDIM, NUMERIC = 1, False


class NetRadiation(sequencetools.FluxSequence):
    """Total net radiation [W/m²]."""

    NDIM, NUMERIC = 1, False


class SoilHeatFlux(sequencetools.FluxSequence):
    """Soil heat flux [W/m²]."""

    NDIM, NUMERIC = 1, False


class ReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Reference (grass) evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 1, False


class PotentialEvapotranspiration(sequencetools.FluxSequence):
    """Potential (land use-specific) evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 1, False


class MeanReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Mean reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class MeanPotentialEvapotranspiration(sequencetools.FluxSequence):
    """Mean potential evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False
