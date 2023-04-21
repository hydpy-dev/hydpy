# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools

# ...from grxjland


class En(sequencetools.FluxSequence):
    """Net evapotranspiration capacity [mm]."""

    NDIM, NUMERIC = 0, False


class Pn(sequencetools.FluxSequence):
    """Net rainfall [mm]."""

    NDIM, NUMERIC = 0, False


class Ps(sequencetools.FluxSequence):
    """Part of `Pn` filling the production store [mm]."""

    NDIM, NUMERIC = 0, False


class Es(sequencetools.FluxSequence):
    """Actual evaporation rate from production store [mm]."""

    NDIM, NUMERIC = 0, False


class AE(sequencetools.FluxSequence):
    """Total actual evaporation rate [mm]."""

    NDIM, NUMERIC = 0, False


class Pr(sequencetools.FluxSequence):
    """Total quantity of water reaching unit hydrograph [mm]."""

    NDIM, NUMERIC = 0, False


class PrUH1(sequencetools.FluxSequence):
    """Total quantity of water reaching unit hydrograph 1 [mm]."""

    NDIM, NUMERIC = 0, False


class PrUH2(sequencetools.FluxSequence):
    """Total quantity of water reaching unit hydrograph 2 [mm]."""

    NDIM, NUMERIC = 0, False


class QOutUH2(sequencetools.FluxSequence):
    """Outlet of unit hydrograph 2 [mm]."""

    NDIM, NUMERIC = 0, False


class Perc(sequencetools.FluxSequence):
    """Percolation [mm]."""

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
