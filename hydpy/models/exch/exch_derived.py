# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.exch import exch_control


class TOY(parametertools.TOYParameter):
    """References the |Indexer.timeofyear| index array provided by the instance of
    class |Indexer| available in module |pub| [-]."""


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


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
