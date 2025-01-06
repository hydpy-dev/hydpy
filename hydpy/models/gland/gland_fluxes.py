# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class E(sequencetools.FluxSequence):
    """Potential evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class EN(sequencetools.FluxSequence):
    """Net evapotranspiration capacity [mm/T]."""

    NDIM, NUMERIC = 0, False


class PN(sequencetools.FluxSequence):
    """Net precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False


class PS(sequencetools.FluxSequence):
    """Part of |PN| filling the production store [mm/T]."""

    NDIM, NUMERIC = 0, False


class EI(sequencetools.FluxSequence):
    """Actual evaporation from the interception store [mm/T]."""

    NDIM, NUMERIC = 0, False


class ES(sequencetools.FluxSequence):
    """Actual evapotranspiration from the production store [mm/T]."""

    NDIM, NUMERIC = 0, False


class AE(sequencetools.FluxSequence):
    """Total actual evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class PR(sequencetools.FluxSequence):
    """Total inflow into the runoff concentration module [mm/T]."""

    NDIM, NUMERIC = 0, False


class PR9(sequencetools.FluxSequence):
    """90% of |PR| [mm/T]."""

    NDIM, NUMERIC = 0, False


class PR1(sequencetools.FluxSequence):
    """10% of |PR| [mm/T]."""

    NDIM, NUMERIC = 0, False


class Q10(sequencetools.FluxSequence):
    """Total outflow of runoff concentration module [mm/T]."""

    NDIM, NUMERIC = 0, False


class Perc(sequencetools.FluxSequence):
    """Percolation [mm/T]."""

    NDIM, NUMERIC = 0, False


class Q9(sequencetools.FluxSequence):
    """Outflow of runoff concentration submodel receiving |PR9| [mm/T]."""

    NDIM, NUMERIC = 0, False


class Q1(sequencetools.FluxSequence):
    """Outflow of runoff concentration submodel receiving |PR1| [mm/T]."""

    NDIM, NUMERIC = 0, False


class FD(sequencetools.FluxSequence):
    """Groundwater exchange affecting the direct runoff [mm/T]."""

    NDIM, NUMERIC = 0, False


class FR(sequencetools.FluxSequence):
    """Groundwater exchange affecting the routing store [mm/T]."""

    NDIM, NUMERIC = 0, False


class FR2(sequencetools.FluxSequence):
    """Groundwater exchange affecting the exponential routing store [mm/T]."""

    NDIM, NUMERIC = 0, False


class QR(sequencetools.FluxSequence):
    """Outflow of the routing store [mm/T]."""

    NDIM, NUMERIC = 0, False


class QR2(sequencetools.FluxSequence):
    """Outflow of the exponential store [mm/T]."""

    NDIM, NUMERIC = 0, False


class QD(sequencetools.FluxSequence):
    """Direct runoff [mm/T]."""

    NDIM, NUMERIC = 0, False


class QH(sequencetools.FluxSequence):
    """Total runoff [mm/T]."""

    NDIM, NUMERIC = 0, False


class QV(sequencetools.FluxSequence):
    """Total discharge [m³/s]."""

    NDIM, NUMERIC = 0, False
