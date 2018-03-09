# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [mm/T]."""
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0., None)
    INIT = 0.01


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 0.001


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of the Test model."""
    _PARCLASSES = (AbsErrorMax, RelDTMin)
