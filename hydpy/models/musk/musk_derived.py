# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.musk import musk_control
from hydpy.models.musk import musk_parameters


class Seconds(parametertools.SecondsParameter):
    """Length of the actual simulation step size [s]."""


class PerimeterIncrease(musk_parameters.Parameter1D):
    """Increase of the (wetted) perimeter of a trapozoidal profile relative to a water
    level increase [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (musk_control.SideSlope,)

    def update(self):
        r"""Update |PerimeterIncrease| based on |SideSlope| following
        :math:`2 \cdot \sqrt{1 + SideSlope^2}`.

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> sideslope(0.0, 2.0)
        >>> derived.perimeterincrease.update()
        >>> derived.perimeterincrease
        perimeterincrease(2.0, 4.472136)
        """
        sideslope = self.subpars.pars.control.sideslope.value
        self.value = 2.0 * (1.0 + sideslope**2.0) ** 0.5
