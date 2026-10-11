# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.kinw import kinw_control
from hydpy.models.kinw import kinw_variables


class QZ(sequencetools.FluxSequence):
    """Mittlerer Zufluss in Gerinnestrecke (average inflow into the channel)
    [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class QZA(sequencetools.FluxSequence):
    """Aktueller Zufluss in Gerinnestrecke (current inflow into the channel)
    [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
    SPAN = (0.0, None)


class Inflow(sequencetools.FluxSequence):
    """Flow into the first channel segment [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class QG(kinw_variables.MixinSubsections, sequencetools.FluxSequence):
    """Durchfluss gesamt (total discharge) [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True
    SPAN = (0.0, None)


class InternalFlow(sequencetools.FluxSequence):
    """Flow between the channel segments [m³/s].

    The length of |InternalFlow| is one less than |kinw_control.NmbSegments|:

    >>> from hydpy.models.kinw import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> fluxes.internalflow.shape
    (1,)

    For zero segments, its length is also zero:

    >>> nmbsegments(0)
    >>> fluxes.internalflow.shape
    (0,)
    """

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, kinw_control.NmbSegments):
            self.__hydpy__change_shape_if_necessary__((max(p.value - 1, 0),))


class QA(sequencetools.FluxSequence):
    """Abfluss aus Gerinnestrecke (outflow out of the channel) [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
    SPAN = (0.0, None)


class Outflow(sequencetools.FluxSequence):
    """Flow out of the last channel segment [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class DH(kinw_variables.MixinSubsections, sequencetools.FluxSequence):
    """Wasserstandänderung (temporal change of the water stage) [m/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True
    SPAN = (0.0, None)
