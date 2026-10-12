# pylint: disable=missing-module-docstring

from hydpy.auxs import smoothtools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.exch import exch_control


class TOY(parametertools.TOYParameter):
    """References the |Indexer.timeofyear| index array provided by the instance of class
    |Indexer| available in module |pub| [-]."""


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class NmbObserverNodes(parametertools.NmbParameter):
    """The number of observer nodes [-].

    Calling the control parameter |ObserverNodes| sets |NmbObserverNodes| immediately.
    Method |NmbObserverNodes.update| determines the same value:

    >>> from hydpy.models.exch_interp import *
    >>> parameterstep()
    >>> observernodes("node_1", "node_2", "node_3")
    >>> derived.nmbobservernodes(1)
    >>> derived.nmbobservernodes.update()
    >>> derived.nmbobservernodes
    nmbobservernodes(3)
    """

    SPAN = (0, None)

    CONTROLPARAMETERS = (exch_control.ObserverNodes,)

    def update(self) -> None:
        """Determine the number of observer nodes."""
        x = self.subpars.pars.model.sequences.observers.x
        self(len(x.observernodes))


class NmbBranches(parametertools.Parameter):
    """The number of branches [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)

    def update(self) -> None:
        """Determine the number of branches."""
        self(len(self.subpars.pars.model.nodenames))


class NmbPoints(parametertools.Parameter):
    """The number of supporting points for linear interpolation [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (2, None)

    CONTROLPARAMETERS = (exch_control.YPoints,)

    def update(self) -> None:
        """Determine the number of points."""
        con = self.subpars.pars.control
        self(con.ypoints.shape[1])


class StreamIndex(parametertools.Parameter):
    """The index of the stream node's output among the outputs of parameter
    |FlowTransferRules| [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, 1)

    CONTROLPARAMETERS = (exch_control.Targets,)

    def update(self) -> None:
        """Determine the index of the stream node's output.

        |PPolys| sorts its outputs alphabetically by the target nodes' names.  Hence,
        the stream node's output comes first if its name is "smaller" than the name of
        the transfer node:

        >>> from hydpy.models.exch_branch_io import *
        >>> parameterstep()
        >>> targets(stream="channel", transfer="diversion")
        >>> derived.streamindex.update()
        >>> derived.streamindex
        streamindex(0)

        Otherwise, it comes second:

        >>> targets(stream="river", transfer="diversion")
        >>> derived.streamindex.update()
        >>> derived.streamindex
        streamindex(1)
        """
        stream, transfer = self.subpars.pars.model.targetnames
        self(int(stream > transfer))


class VolSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |VolTol| for smoothing kernel
    |smooth_logistic1| [million m³]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (exch_control.VolTol,)

    def update(self) -> None:
        """Calculate the smoothing parameter values.

        The documentation on module |smoothtools| explains the following example in
        some detail:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
        >>> from hydpy.models.exch_water_transfer_io import *
        >>> parameterstep()
        >>> voltol(0.0)
        >>> voltol.values[1] = 2.5
        >>> derived.volsmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(0.1, derived.volsmoothpar[0]))
        1.0
        >>> round_(smooth_logistic1(2.5, derived.volsmoothpar[1]))
        0.99

        .. testsetup::

            >>> del pub.timegrids
        """
        metapar = self.subpars.pars.control.voltol
        self.shape = metapar.shape
        self(smoothtools.calc_smoothpar_logistic1(metapar.values))


class QSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |QTol| for smoothing kernels
    |smooth_min1| and |smooth_max1| [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (exch_control.QTol,)

    def update(self) -> None:
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following example in
        some detail:

        >>> from hydpy.models.exch_water_transfer_io import *
        >>> parameterstep()
        >>> qtol(0.0)
        >>> derived.qsmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_min1
        >>> from hydpy import round_
        >>> round_(smooth_min1(4.0, 1.5, derived.qsmoothpar))
        1.5
        >>> qtol(2.5)
        >>> derived.qsmoothpar.update()
        >>> round_(smooth_min1(4.0, 1.5, derived.qsmoothpar))
        1.49
        """
        metapar = self.subpars.pars.control.qtol
        self(smoothtools.calc_smoothpar_min1(metapar.value))
