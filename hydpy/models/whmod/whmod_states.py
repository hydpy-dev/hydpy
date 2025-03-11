# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences
from hydpy.models.whmod import whmod_derived


class InterceptedWater(whmod_sequences.State1DNonWaterSequence):
    """Interception storage water content [mm]."""

    SPAN = (0.0, None)


class Snowpack(whmod_sequences.State1DNonWaterSequence):
    """Snow layer's total water content [mm]."""

    SPAN = (0.0, None)


class SoilMoisture(whmod_sequences.State1DSoilSequence):
    """Crop-available soil water content [mm]."""

    SPAN = (0.0, None)
    DERIVEDPARAMETERS = (whmod_derived.MaxSoilWater,)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |SoilMoisture| following :math:`0 \leq SoilMoisture \leq MaxSoilWater`.

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> derived.maxsoilwater(200.0)
        >>> states.soilmoisture(-100.0, 0.0, 100.0, 200.0, 300.0)
        >>> states.soilmoisture
        soilmoisture(0.0, 0.0, 100.0, 200.0, 200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.derived.maxsoilwater
        return super().trim(lower, upper)


class DeepWater(sequencetools.StateSequence):
    """Amount of water that is (still) percolating through the vadose zone [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
