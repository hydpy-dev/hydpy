# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m].

    After each simulation step, the value of |WaterLevel| corresponds to the value
    of the state sequence |WaterVolume| for the end of the simulation step.
    """

    NDIM = 0


class OuterWaterLevel(sequencetools.FactorSequence):
    """The water level directly below the dam [m]."""

    NDIM = 0


class RemoteWaterLevel(sequencetools.FactorSequence):
    """The water level at a remote location [m]."""

    NDIM = 0


class WaterLevelDifference(sequencetools.FactorSequence):
    """Difference between the inner and the outer water level [m].

    The inner water level is above the outer water level for positive values.
    """

    NDIM = 0


class EffectiveWaterLevelDifference(sequencetools.FactorSequence):
    """Effective difference between the inner and the outer water level [m].

    "Effective" could mean, for example, the water level difference above a weir crest
    (where the actual water exchange takes place).
    """

    NDIM = 0
