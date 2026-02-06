# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.ReceiverSequence):
    """Discharge at the target location [m³/s]."""

    NDIM, NUMERIC = 0, False


class WaterVolume(sequencetools.ReceiverSequence):
    """The current water volume of the individual sources [million m³]."""

    NDIM, NUMERIC = 1, False
