# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterVolume(sequencetools.StateSequence):
    """Water volume [million m³]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)
