# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring
# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools

# ...from lland
from hydpy.models.wq import wq_control


class BottomDepths(parametertools.Parameter):
    """The cumulated depth of a trapeze and its lower neighbours [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.BottomLevels,)

    def update(self):
        r"""Calculate the depth values based on
        :math:`BottomDepths_i = BottomLevels_i - BottomLevels_0`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 4.0, 6.0)
        >>> derived.bottomdepths.update()
        >>> derived.bottomdepths
        bottomdepths(0.0, 3.0, 5.0)
        """
        bottomlevels = self.subpars.pars.control.bottomlevels.values
        self.values = bottomlevels - bottomlevels[0]


class TrapezeHeights(parametertools.Parameter):
    """The individual height of each trapeze [m].

    The highest trapeze has no upper neighbour and is thus infinitely high.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.BottomLevels,)

    def update(self):
        r"""Calculate the height values based on
        :math:`TrapezeHeights_i = BottomLevels_{i+1} - BottomLevels_i`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 4.0, 6.0)
        >>> derived.trapezeheights.update()
        >>> derived.trapezeheights
        trapezeheights(3.0, 2.0, inf)
        """
        self.values = numpy.inf
        self.values[:-1] = numpy.diff(self.subpars.pars.control.bottomlevels.values)


class SlopeWidths(parametertools.Parameter):
    """The tatal width of both side slopes of each trapeze.

    The highest trapeze has no upper neighbour and is thus infinitely high and
    potentially infinitely wide.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.SideSlopes,)
    DERIVEDPARAMETERS = (TrapezeHeights,)

    def update(self):
        r"""Calculate the slope width values based on
        :math:`SlopeWidths = 2 \cdot SideSlopes \cdot TrapezeHeights`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> derived.trapezeheights(2.0, 3.0, inf)
        >>> derived.slopewidths.update()
        >>> derived.slopewidths
        slopewidths(0.0, 12.0, inf)
        """
        sideslopes = self.subpars.pars.control.sideslopes.values
        trapezeheights = self.subpars.trapezeheights.values
        self.values = numpy.inf
        self.values[:-1] = 2.0 * sideslopes[:-1] * trapezeheights[:-1]


class PerimeterDerivatives(parametertools.Parameter):
    """Change of the perimeter of each trapeze relative to a water level increase
    within the trapeze's range [-].
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.SideSlopes,)

    def update(self):
        r"""Calculate the perimeter derivatives based on
        :math:`2 \cdot \sqrt{1 + SideSlopes^2}`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> sideslopes(0.0, 2.0)
        >>> derived.perimeterderivatives.update()
        >>> derived.perimeterderivatives
        perimeterderivatives(2.0, 4.472136)
        """
        sideslopes = self.subpars.pars.control.sideslopes.value
        self.value = 2.0 * (1.0 + sideslopes**2.0) ** 0.5


class CrestHeightRegularisation(parametertools.Parameter):
    """Regularisation parameter related to the difference between the water depth and
    the crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.CrestHeightTolerance,)

    def update(self):
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following example in
        some detail:

        >>> from hydpy.models.wq import *
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> parameterstep()
        >>> crestheighttolerance(0.0)
        >>> derived.crestheightregularisation.update()
        >>> round_(smooth_logistic2(0.0, derived.crestheightregularisation))
        0.0
        >>> crestheighttolerance(0.0025)
        >>> derived.crestheightregularisation.update()
        >>> round_(smooth_logistic2(0.0025, derived.crestheightregularisation))
        0.00251
        """
        metapar = self.subpars.pars.control.crestheighttolerance.value
        self(smoothtools.calc_smoothpar_logistic2(1000.0 * metapar) / 1000.0)
