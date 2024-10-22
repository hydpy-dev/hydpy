# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.ReceiverSequence):
    """Water level [m]."""

    NDIM, NUMERIC = 0, False
