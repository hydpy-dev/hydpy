# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m].

    After each simulation step, the value of |WaterLevel| corresponds to the value
    of the state sequence |WaterVolume| for the end of the simulation step.
    """

    NDIM = 0
