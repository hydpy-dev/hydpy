# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.ga import ga_variables


class InitialSurfaceWater(ga_variables.MixinSoils, sequencetools.AideSequence):
    """The initial surface water depth at the beginning of a numerical substep [mm]."""

    NDIM: Final[Literal[1]] = 1


class ActualSurfaceWater(ga_variables.MixinSoils, sequencetools.AideSequence):
    """The actual surface water depth [mm]."""

    NDIM: Final[Literal[1]] = 1
