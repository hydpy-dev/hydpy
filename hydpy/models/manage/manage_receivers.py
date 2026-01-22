# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.ReceiverSequence):
    """ToDo"""

    NDIM, NUMERIC = 0, False


class WaterVolume(sequencetools.ReceiverSequence):
    """The current water volume of the potential water suppliers [million m³]."""

    NDIM, NUMERIC = 1, False
