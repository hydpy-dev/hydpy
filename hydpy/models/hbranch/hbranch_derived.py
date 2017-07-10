# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class NmbBranches(parametertools.SingleParameter):
    """Number of branches [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        con = self.subpars.pars.control
        self(con.ypoints.shape[0])


class NmbPoints(parametertools.SingleParameter):
    """Number of supporting points for linear interpolation [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (2, None)

    def update(self):
        con = self.subpars.pars.control
        self(con.ypoints.shape[1])


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hbranch, indirectly defined by the user."""
    _PARCLASSES = (NmbBranches, NmbPoints)
