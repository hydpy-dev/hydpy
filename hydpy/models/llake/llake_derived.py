# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy import pub
from hydpy.core import parametertools


class TOY(parametertools.IndexParameter):
    """References the "global" time of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, None)

    def update(self):
        self.setreference(pub.indexer.timeofyear)


class Seconds(parametertools.SingleParameter):
    """Length of the actual simulation step size in seconds [s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        self.value = self.simulationstep.seconds


class VQ(parametertools.SeasonalParameter):
    """Hilfsterm (auxiliary term): math:VdtQ = 2 \\cdot + dt \\cdot Q` [m³].

    >>> from hydpy.models.llake import *
    >>> parameterstep('1d')
    >>> simulationstep('12h')
    >>> n(3)
    >>> v(0., 1e5, 1e6)
    >>> q(_1=[0., 1., 2.], _7=[0., 2., 5.])
    >>> derived.vq.update()
    >>> derived.vq
    vq(toy_1_1_0_0_0=[0.0, 243200.0, 2086400.0],
       toy_7_1_0_0_0=[0.0, 286400.0, 2216000.0])
    """
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        for (toy, qs) in con.q:
            setattr(self, str(toy), 2.*con.v+self.simulationstep.seconds*qs)
        self.refresh()


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-L-Lake, indirectly defined by the user."""
    _PARCLASSES = (TOY, Seconds, VQ)
