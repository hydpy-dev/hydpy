# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class NmbRuns(parametertools.SolverParameter):
    """The number of (repeated) runs of the |RunModel.RUN_METHODS| per simulation step
    [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = int
    TIME = None
    INIT = 1


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.000001


class RelErrorMax(parametertools.SolverParameter):
    """Relative numerical error tolerance [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.001


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.0


class RelDTMax(parametertools.SolverParameter):
    """Largest relative integration time step size allowed [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 1.0


class WaterVolumeTolerance(parametertools.SolverParameter):
    """Targeted accuracy in terms of the relative water volume for the Pegasus search
    of the final water depth [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 1e-10


class WaterDepthTolerance(parametertools.SolverParameter):
    """Targeted accuracy in terms of the absolute water depth for the Pegasus search of
    the final water depth [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 1e-10
