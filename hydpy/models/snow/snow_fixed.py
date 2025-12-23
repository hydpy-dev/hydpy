# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class ZThreshold(parametertools.FixedParameter):
    """Altitude threshold for constant precipitation [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 4000.0


class MinMelt(parametertools.FixedParameter):
    """Minimum ratio of actual to potential melt [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.1


class TThreshSnow(parametertools.FixedParameter):
    """Temperature below which all precipitation falls as snow [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = -1.0


class TThreshRain(parametertools.FixedParameter):
    """Temperature above which all precipitation falls as rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 3.0


class MinG(parametertools.FixedParameter):
    """Amount of snow below which actual melt can be equal to potential melt [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 0.0
