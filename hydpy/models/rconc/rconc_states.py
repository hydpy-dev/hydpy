# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SC(sequencetools.StateSequence):
    """Storage cascade for runoff concentration [mm]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)
