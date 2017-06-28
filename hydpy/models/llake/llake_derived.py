# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
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


class NmbSubsteps(parametertools.SingleParameter):
    """Number of the internal simulation steps [-].

    Examples:

        Initialize a llake model and assume a simulation step size of 12 hours:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')

        If the maximum internal step size is also set to 12 hours, there is
        only one internal calculation step per outer simulation step:

        >>> maxdt('12h')
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(1)

        Assigning smaller values to `maxdt` increases `nmbstepsize`:

        >>> maxdt('1h')
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(12)

        In case the simulationstep is not a whole multiple of `dwmax`,
        the value of `nmbsubsteps` is rounded up:

        >>> maxdt('59m')
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(13)

        Even for `maxdt` values exceeding the simulationstep, the value
        of `numbsubsteps` does not become smaller than one:

        >>> maxdt('2d')
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(1)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        maxdt = self.subpars.pars.control.maxdt
        seconds = self.simulationstep.seconds
        self.value = numpy.ceil(seconds/maxdt)


class VQ(parametertools.SeasonalParameter):
    """Hilfsterm (auxiliary term): math:VdtQ = 2 \\cdot + dt \\cdot Q` [m³].

    >>> from hydpy.models.llake import *
    >>> parameterstep('1d')
    >>> simulationstep('12h')
    >>> n(3)
    >>> v(0., 1e5, 1e6)
    >>> q(_1=[0., 1., 2.], _7=[0., 2., 5.])
    >>> maxdt('12h')
    >>> derived.seconds.update()
    >>> derived.nmbsubsteps.update()
    >>> derived.vq.update()
    >>> derived.vq
    vq(toy_1_1_0_0_0=[0.0, 243200.0, 2086400.0],
       toy_7_1_0_0_0=[0.0, 286400.0, 2216000.0])
    """
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        der = self.subpars
        for (toy, qs) in con.q:
            setattr(self, str(toy), 2.*con.v+der.seconds/der.nmbsubsteps*qs)
        self.refresh()


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-L-Lake, indirectly defined by the user."""
    _PARCLASSES = (TOY, Seconds, NmbSubsteps, VQ)
