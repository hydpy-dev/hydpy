# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class InitialSurfaceWater(sequencetools.AideSequence):
    """The initial surface water depth at the beginning of a numerical substep [mm]."""

    NDIM = 1
    NUMERIC = False


class ActualSurfaceWater(sequencetools.AideSequence):
    """The actual surface water depth [mm]."""

    NDIM = 1
    NUMERIC = False
