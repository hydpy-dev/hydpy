# pylint: disable=missing-module-docstring

import numpy

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class AbsErrorMax(parametertools.SolverParameter):
    """Absolute numerical error tolerance [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.01


class RelErrorMax(parametertools.SolverParameter):
    """Relative numerical error tolerance [1/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = numpy.nan


class RelDTMin(parametertools.SolverParameter):
    """Smallest relative integration time step size allowed [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)
    INIT = 0.001


class RelDTMax(parametertools.SolverParameter):
    """Largest relative integration time step size allowed [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)
    INIT = 1.0
