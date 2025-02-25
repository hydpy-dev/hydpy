# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences


class InterceptedWater(whmod_sequences.State1DSequence):
    """[mm]"""


class Snowpack(whmod_sequences.State1DSequence):
    """[mm]"""


class SoilMoisture(whmod_sequences.State1DSequence):
    """[mm]"""


class DeepWater(sequencetools.StateSequence):
    """[mm]"""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
