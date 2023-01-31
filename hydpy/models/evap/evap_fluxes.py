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

    NDIM, NUMERIC = 0, False


class NetRadiation(sequencetools.FluxSequence):
    """Total net radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class SoilHeatFlux(sequencetools.FluxSequence):
    """Soil heat flux [W/m²]."""

    NDIM, NUMERIC = 0, False


class ReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False
