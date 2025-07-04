# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    __HYDPY__DELTA_SEGMENTS__ = 0
