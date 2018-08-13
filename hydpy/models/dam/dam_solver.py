# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [m3/s].

    Note that the default initial value 0.01 refers to mm and the actual
    simulation step size. Hence the actual default initial value in m³/s is:

    :math:`AbsErrorMax = 0.01 \\cdot CatchmentArea \\cdot 1000 / Seconds`
    """
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0., None)
    INIT = 0.01

    def modify_init(self):
        pars = self.subpars.pars
        catchmentarea = pars.control.catchmentarea
        seconds = pars.derived.seconds
        return self.INIT*catchmentarea*1000./seconds


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 0.001


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of the Test model."""
    CLASSES = (AbsErrorMax, RelDTMin)
