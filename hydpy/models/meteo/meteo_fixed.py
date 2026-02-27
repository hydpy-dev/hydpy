# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class Pi(parametertools.FixedParameter):
    """π [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 3.141592653589793


class SolarConstant(parametertools.FixedParameter):
    """Solar constant [W/m²]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1367.0
