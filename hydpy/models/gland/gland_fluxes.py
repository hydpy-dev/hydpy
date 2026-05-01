# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class E(sequencetools.FluxSequence):
    """Potential evapotranspiration [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class EN(sequencetools.FluxSequence):
    """Net evapotranspiration capacity [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class PN(sequencetools.FluxSequence):
    """Net precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class PS(sequencetools.FluxSequence):
    """Part of |PN| filling the production store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class EI(sequencetools.FluxSequence):
    """Actual evaporation from the interception store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class ES(sequencetools.FluxSequence):
    """Actual evapotranspiration from the production store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class AE(sequencetools.FluxSequence):
    """Total actual evapotranspiration [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class PR(sequencetools.FluxSequence):
    """Total inflow into the runoff concentration module [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class PR9(sequencetools.FluxSequence):
    """90% of |PR| [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class PR1(sequencetools.FluxSequence):
    """10% of |PR| [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class Q10(sequencetools.FluxSequence):
    """Total outflow of runoff concentration module [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class Perc(sequencetools.FluxSequence):
    """Percolation [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class Q9(sequencetools.FluxSequence):
    """Outflow of runoff concentration submodel receiving |PR9| [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class Q1(sequencetools.FluxSequence):
    """Outflow of runoff concentration submodel receiving |PR1| [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class FD(sequencetools.FluxSequence):
    """Groundwater exchange affecting the direct runoff [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class FR(sequencetools.FluxSequence):
    """Groundwater exchange affecting the routing store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class FR2(sequencetools.FluxSequence):
    """Groundwater exchange affecting the exponential routing store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class QR(sequencetools.FluxSequence):
    """Outflow of the routing store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class QR2(sequencetools.FluxSequence):
    """Outflow of the exponential store [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class QD(sequencetools.FluxSequence):
    """Direct runoff [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class QH(sequencetools.FluxSequence):
    """Total runoff [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class QV(sequencetools.FluxSequence):
    """Total discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
