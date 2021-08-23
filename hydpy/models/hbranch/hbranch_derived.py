# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.hbranch import hbranch_control


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class NmbBranches(parametertools.Parameter):
    """The number of branches [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    CONTROLPARAMETERS = (hbranch_control.YPoints,)

    def update(self):
        """Determine the number of branches."""
        con = self.subpars.pars.control
        self(con.ypoints.shape[0])


class NmbPoints(parametertools.Parameter):
    """The number of supporting points for linear interpolation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (2, None)

    CONTROLPARAMETERS = (hbranch_control.YPoints,)

    def update(self):
        """Determine the number of points."""
        con = self.subpars.pars.control
        self(con.ypoints.shape[1])
