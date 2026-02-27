# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m].

    After each simulation step, the value of |WaterLevel| corresponds to the value
    of the state sequence |WaterVolume| for the end of the simulation step.
    """

    NDIM: Final[Literal[0]] = 0


class OuterWaterLevel(sequencetools.FactorSequence):
    """The water level directly below the dam [m]."""

    NDIM: Final[Literal[0]] = 0


class RemoteWaterLevel(sequencetools.FactorSequence):
    """The water level at a remote location [m]."""

    NDIM: Final[Literal[0]] = 0


class WaterLevelDifference(sequencetools.FactorSequence):
    """Difference between the inner and the outer water level [m].

    The inner water level is above the outer water level for positive values.
    """

    NDIM: Final[Literal[0]] = 0


class EffectiveWaterLevelDifference(sequencetools.FactorSequence):
    """Effective difference between the inner and the outer water level [m].

    "Effective" could mean, for example, the water level difference above a weir crest
    (where the actual water exchange takes place).
    """

    NDIM: Final[Literal[0]] = 0
