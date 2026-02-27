# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class GravitationalAcceleration(parametertools.FixedParameter):
    """Gravitational acceleration [m/s²]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 9.81
