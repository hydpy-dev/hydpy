# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools

# ...from llake
from hydpy.models.llake import llake_control


class TOY(parametertools.TOYParameter):
    """References the |Indexer.timeofyear| index array provided by the
    instance of class |Indexer| available in module |pub|. [-]."""


class Seconds(parametertools.SecondsParameter):
    """Length of the actual simulation step size in seconds [s]."""


class NmbSubsteps(parametertools.Parameter):
    """Number of the internal simulation steps [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    CONTROLPARAMETERS = (llake_control.MaxDT,)
    DERIVEDPARAMETERS = (Seconds,)

    def update(self):
        """Determine the number of substeps.

        Initialize a llake model and assume a simulation step size of 12 hours:

        >>> from hydpy.models.llake import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> derived.seconds.update()

        If the maximum internal step size is also set to 12 hours, there is
        only one internal calculation step per outer simulation step:

        >>> maxdt("12h")
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(1)

        Assigning smaller values to `maxdt` increases `nmbstepsize`:

        >>> maxdt("1h")
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(12)

        In case the simulationstep is not a whole multiple of `dwmax`,
        the value of `nmbsubsteps` is rounded up:

        >>> maxdt("59m")
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(13)

        Even for `maxdt` values exceeding the simulationstep, the value
        of `numbsubsteps` does not become smaller than one:

        >>> maxdt("2d")
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(1)
        """
        maxdt = self.subpars.pars.control.maxdt
        seconds = self.subpars.seconds
        self.value = numpy.ceil(seconds / maxdt)


class VQ(parametertools.SeasonalParameter):
    """Hilfsterm (auxiliary term): math:VdtQ = 2 \\cdot + dt \\cdot Q` [m³]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        llake_control.Q,
        llake_control.V,
    )
    DERIVEDPARAMETERS = (
        Seconds,
        NmbSubsteps,
    )

    def update(self):
        """Calulate the auxilary term.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "12h"
        >>> from hydpy.models.llake import *
        >>> parameterstep("1d")
        >>> n(3)
        >>> v(0., 1e5, 1e6)
        >>> q(_1=[0., 1., 2.], _7=[0., 2., 5.])
        >>> maxdt("12h")
        >>> derived.seconds.update()
        >>> derived.nmbsubsteps.update()
        >>> derived.vq.update()
        >>> derived.vq
        vq(toy_1_1_0_0_0=[0.0, 243200.0, 2086400.0],
           toy_7_1_0_0_0=[0.0, 286400.0, 2216000.0])
        """
        con = self.subpars.pars.control
        der = self.subpars
        for toy, qs in con.q:
            setattr(self, str(toy), 2.0 * con.v + der.seconds / der.nmbsubsteps * qs)
        self.refresh()
