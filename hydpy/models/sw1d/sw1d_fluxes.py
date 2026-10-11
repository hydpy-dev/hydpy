# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.sw1d import sw1d_control


class Inflow(sequencetools.FluxSequence):
    """Longitudinal flow into the first channel segment [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class Outflow(sequencetools.FluxSequence):
    """Longitudinal flow out of the last channel segment [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class LateralFlow(sequencetools.FluxSequence):
    """Lateral flow into the first channel segment [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class NetInflow(sequencetools.FluxSequence):
    """The net inflow into a channel segment [m³/T]."""

    NDIM: Final[Literal[0]] = 0


class DischargeUpstream(sequencetools.FluxSequence):
    """The summed (partial) of all upstream routing models [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class DischargeDownstream(sequencetools.FluxSequence):
    """The summed (partial) of all downstream routing models [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class DischargeVolume(sequencetools.FluxSequence):
    """The total amount of discharge of a simulation step [m³/T]."""

    NDIM: Final[Literal[0]] = 0


class Discharges(sequencetools.FluxSequence):
    """The discharges between all channel segments, including the flow into the first
    and out of the last one [m³/s].

    The length of |Discharges| exceeds the value of parameter |NmbSegments| by one:

    >>> from hydpy.models.sw1d_channel import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> fluxes.discharges.shape
    (3,)
    """

    NDIM: Final[Literal[1]] = 1
    PLUS = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, sw1d_control.NmbSegments):
            self.__hydpy__change_shape_if_necessary__((p.value + 1,))
