# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class ZThreshold(parametertools.FixedParameter):
    """Altitude threshold for constant precipitation [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    INIT = 4000.0


class MinMelt(parametertools.FixedParameter):
    """Minimum ratio of actual to potential melt [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, 1.0)
    INIT = 0.1


class TThreshSnow(parametertools.FixedParameter):
    """Temperature below which all precipitation falls as snow [°C]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    INIT = -1.0


class TThreshRain(parametertools.FixedParameter):
    """Temperature above which all precipitation falls as rain [°C]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    INIT = 3.0


class MinG(parametertools.FixedParameter):
    """Amount of snow below which actual melt can be equal to potential melt [mm]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    INIT = 0.0
