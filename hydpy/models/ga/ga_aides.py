# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class InitialSurfaceWater(sequencetools.AideSequence):
    """The initial surface water depth at the beginning of a numerical substep [mm]."""

    NDIM: Final[Literal[1]] = 1


class ActualSurfaceWater(sequencetools.AideSequence):
    """The actual surface water depth [mm]."""

    NDIM: Final[Literal[1]] = 1
