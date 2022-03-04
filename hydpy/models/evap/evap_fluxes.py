# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class NetShortwaveRadiation(sequencetools.FluxSequence):
    """Net shortwave radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class NetLongwaveRadiation(sequencetools.FluxSequence):
    """Net longwave radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class NetRadiation(sequencetools.FluxSequence):
    """Total net radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class SoilHeatFlux(sequencetools.FluxSequence):
    """Soil heat flux [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class ReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False
