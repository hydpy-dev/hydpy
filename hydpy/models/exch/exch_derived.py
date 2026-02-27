# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *

from hydpy.models.exch import exch_control


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class NmbBranches(parametertools.Parameter):
    """The number of branches [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = int
    TIME = None
    SPAN = (1, None)

    CONTROLPARAMETERS = (exch_control.YPoints,)

    def update(self):
        """Determine the number of branches."""
        con = self.subpars.pars.control
        self(con.ypoints.shape[0])


class NmbPoints(parametertools.Parameter):
    """The number of supporting points for linear interpolation [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = int
    TIME = None
    SPAN = (2, None)

    CONTROLPARAMETERS = (exch_control.YPoints,)

    def update(self):
        """Determine the number of points."""
        con = self.subpars.pars.control
        self(con.ypoints.shape[1])
