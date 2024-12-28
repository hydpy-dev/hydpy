# pylint: disable=missing-module-docstring

# import...

# ...from HydPy
from hydpy.core import sequencetools


class GLocalMax(sequencetools.LogSequence):
    """Local melt threshold [mm]."""

    NDIM, NUMERIC = 1, False
