# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

from hydpy.core import sequencetools



class En(sequencetools.FluxSequence):
    """Net evapotranspiration capacity [mm]."""
    NDIM, NUMERIC = 0, False


class PLayer(sequencetools.FluxSequence):
    """Precipitation of each snow layer[mm]."""
    NDIM, NUMERIC = 1, False

class PSnowLayer(sequencetools.FluxSequence):
    """Snowfall of each snow layer[mm]."""
    NDIM, NUMERIC = 1, False

class PRainLayer(sequencetools.FluxSequence):
    """Rainfall of each snow layer[mm]."""
    NDIM, NUMERIC = 1, False


class TLayer(sequencetools.FluxSequence):
    """Daily mean air temperature of each snow layer [°C]."""
    NDIM, NUMERIC = 1, False


class TMinLayer(sequencetools.FluxSequence):
    """Daily minimum air temperature of each snow layer [°C]."""
    NDIM, NUMERIC = 1, False


class TMaxLayer(sequencetools.FluxSequence):
    """Daily maximum air temperature of each snow layer [°C]."""
    NDIM, NUMERIC = 1, False

class SolidFraction(sequencetools.FluxSequence):
    """Solid Fraction of precipitation [/]."""
    NDIM, NUMERIC, SPAN = 1, False, (0, 1)


class PotMelt(sequencetools.FluxSequence):
    """Potential snow melt [mm]."""
    NDIM, NUMERIC = 1, False

class Melt(sequencetools.FluxSequence):
    """Snow melt [mm]."""
    NDIM, NUMERIC = 1, False

class Pn(sequencetools.FluxSequence):
    """Net rainfall [mm]."""
    NDIM, NUMERIC = 0, False


class Ps(sequencetools.FluxSequence):
    """Part of Pn filling the production store [mm]."""
    NDIM, NUMERIC = 0, False


class Es(sequencetools.FluxSequence):
    """Actual evaporation rate from production storage [mm]."""
    NDIM, NUMERIC = 0, False

class AE(sequencetools.FluxSequence):
    """Total actual evaporation rate [mm]."""
    NDIM, NUMERIC = 0, False


class Pr(sequencetools.FluxSequence):
    """Total quantity of water reaching routing functions [mm]."""
    NDIM, NUMERIC = 0, False


class Perc(sequencetools.FluxSequence):
    """Percolation leakage [mm]."""
    NDIM, NUMERIC = 0, False


class Q9(sequencetools.FluxSequence):
    """Output of unit hydrograph UH1 [mm]."""
    NDIM, NUMERIC = 0, False


class Q1(sequencetools.FluxSequence):
    """Output of unit hydrograph UH2 [mm]."""
    NDIM, NUMERIC = 0, False


class F(sequencetools.FluxSequence):
    """Groundwater exchange term [mm]."""
    NDIM, NUMERIC = 0, False


class Qr(sequencetools.FluxSequence):
    """Outflow of the routing storage [mm]."""
    NDIM, NUMERIC = 0, False


class Qr2(sequencetools.FluxSequence):
    """Outflow of the exponential storage [mm]."""
    NDIM, NUMERIC = 0, False


class Qd(sequencetools.FluxSequence):
    """Flow component direct flow [mm]."""
    NDIM, NUMERIC = 0, False


class Qt(sequencetools.FluxSequence):
    """Total streamflow [mm]."""
    NDIM, NUMERIC = 0, False

