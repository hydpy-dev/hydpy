# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.ReceiverSequence):
    """The water level at a single remote location [m]."""

    NDIM = 0
    NUMERIC = False


class WaterLevels(sequencetools.ReceiverSequence):
    """The water level at multiple remote locations [m]."""

    NDIM = 1
    NUMERIC = False
