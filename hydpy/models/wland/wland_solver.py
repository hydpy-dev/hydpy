# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.01


class RelErrorMax(parametertools.SolverParameter):
    """Relative numerical error tolerance [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.01


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 0.0


class RelDTMax(parametertools.SolverParameter):
    """Largest relative integration time step size allowed [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 1.0
