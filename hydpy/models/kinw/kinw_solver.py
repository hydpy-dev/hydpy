# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [m³/s]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.000001


class RelErrorMax(parametertools.SolverParameter):
    """Relative numerical error tolerance [-]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.001


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.0


class RelDTMax(parametertools.SolverParameter):
    """Largest relative integration time step size allowed [-]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 1.0
