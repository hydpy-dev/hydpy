# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences


class InterceptedWater(whmod_sequences.State1DNonWaterSequence):
    """Interception storage water content [mm]."""


class Snowpack(whmod_sequences.State1DNonWaterSequence):
    """Snow layer's total water content [mm]."""


class SoilMoisture(whmod_sequences.State1DSoilSequence):
    """Crop-available soil water content [mm]."""


class DeepWater(sequencetools.StateSequence):
    """Amount of water that is (still) percolating through the vadose zone [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
