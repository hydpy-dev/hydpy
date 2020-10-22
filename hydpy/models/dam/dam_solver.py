# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.dam import dam_control


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [m3/s]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.01

    CONTROLPARAMETERS = (dam_control.CatchmentArea,)

    def modify_init(self):
        """ ""Adjust and return the value of class constant `INIT`.

        Note that the default initial value 0.01 refers to mm and the
        actual simulation step size.  Hence the actual default initial
        value in m³/s is:

        :math:`AbsErrorMax = 0.01 \\cdot CatchmentArea \\cdot 1000 / Seconds`

        >>> from hydpy.models.dam import *
        >>> parameterstep('1d')
        >>> simulationstep('1h')
        >>> solver.abserrormax.INIT
        0.01
        >>> catchmentarea(2.0)
        >>> derived.seconds.update()
        >>> from hydpy import round_
        >>> round_(solver.abserrormax.modify_init())
        0.005556
        """
        pars = self.subpars.pars
        catchmentarea = pars.control.catchmentarea
        seconds = pars.derived.seconds
        return self.INIT * catchmentarea * 1000.0 / seconds


class RelErrorMax(parametertools.SolverParameter):
    """Relative numerical error tolerance [1/T]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = numpy.nan


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 0.001


class RelDTMax(parametertools.SolverParameter):
    """Largest relative integration time step size allowed [-]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 1.0
