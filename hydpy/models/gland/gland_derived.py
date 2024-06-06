# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
import hydpy
from hydpy.core import parametertools

# ...from snow
from hydpy.models.gland import gland_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (gland_control.Area,)

    def update(self):
        """Update |QFactor| based on |Area| and the current simulation
        step size.

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> area(50.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(0.578704)

        change simulationstep to 1 h

        >>> simulationstep('1h')
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(13.888889)

        """
        self(
            self.subpars.pars.control.area
            * 1000.0
            / hydpy.pub.options.simulationstep.seconds
        )
