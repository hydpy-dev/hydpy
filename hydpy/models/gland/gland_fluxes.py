# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools

# ...from gland


class E(sequencetools.FluxSequence):
    """Potential Evapotranspiration [mm]."""

    NDIM, NUMERIC = 0, False


class EN(sequencetools.FluxSequence):
    """Net evapotranspiration capacity [mm]."""

    NDIM, NUMERIC = 0, False


class PN(sequencetools.FluxSequence):
    """Net rainfall [mm]."""

    NDIM, NUMERIC = 0, False


class PS(sequencetools.FluxSequence):
    """Part of |Pn| filling the production store [mm]."""

    NDIM, NUMERIC = 0, False


class EI(sequencetools.FluxSequence):
    """Evaporation rate from interception store [mm]."""

    NDIM, NUMERIC = 0, False


class ES(sequencetools.FluxSequence):
    """Actual evaporation rate from production store [mm]."""

    NDIM, NUMERIC = 0, False


class AE(sequencetools.FluxSequence):
    """Total actual evaporation rate [mm]."""

    NDIM, NUMERIC = 0, False


class PR(sequencetools.FluxSequence):
    """Total quantity of water reaching unit hydrograph [mm]."""

    NDIM, NUMERIC = 0, False


class PR9(sequencetools.FluxSequence):
    """90% of |PR| [mm]."""

    NDIM, NUMERIC = 0, False


class PR1(sequencetools.FluxSequence):
    """10% of |PR|  [mm]."""

    NDIM, NUMERIC = 0, False


class Q10(sequencetools.FluxSequence):
    """Outlet of runoff concentration [mm]."""

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


class FD(sequencetools.FluxSequence):
    """Groundwater exchange term direct runoff [mm]."""

    NDIM, NUMERIC = 0, False


class FR(sequencetools.FluxSequence):
    """Groundwater exchange term routing store [mm]."""

    NDIM, NUMERIC = 0, False


class FR2(sequencetools.FluxSequence):
    """Groundwater exchange term exponential routing store [mm]."""

    NDIM, NUMERIC = 0, False


class QR(sequencetools.FluxSequence):
    """Outflow of the routing storage [mm]."""

    NDIM, NUMERIC = 0, False


class QR2(sequencetools.FluxSequence):
    """Outflow of the exponential storage [mm]."""

    NDIM, NUMERIC = 0, False


class QD(sequencetools.FluxSequence):
    """Flow component direct flow [mm]."""

    NDIM, NUMERIC = 0, False


class QH(sequencetools.FluxSequence):
    """Total streamflow [mm]."""

    NDIM, NUMERIC = 0, False


class QV(sequencetools.FluxSequence):
    """Total streamflow [m³/s]."""

    NDIM, NUMERIC = 0, False
