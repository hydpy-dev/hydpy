# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.exch import exch_control


class TOY(parametertools.TOYParameter):
    """References the |Indexer.timeofyear| index array provided by the
    instance of class |Indexer| available in module |pub| [-]."""


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class NmbBranches(parametertools.Parameter):
    """The number of branches [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)

    # ToDo CONTROLPARAMETERS = (exch_control.YPoints,)

    def update(self) -> None:
        """Determine the number of branches."""
        con = self.subpars.pars.control
        try:
            self(con.ypoints.shape[0])
        except:
            self(len(self.subpars.pars.model.nodenames))
            con.pars.model.sequences.fluxes.outputs.shape = self.value
            # con.pars.model.sequences.outlets.branched.shape = self.value


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
