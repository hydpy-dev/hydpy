# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class GravitationalAcceleration(parametertools.FixedParameter):
    """Gravitational acceleration [m/s²]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 9.81
