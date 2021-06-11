# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core import variabletools


class WaterLevel(variabletools.MixinFixedShape, sequencetools.FactorSequence):
    """Water level [m].

    After each simulation step, the value of |WaterLevel| corresponds to the value
    of the |LoggedWaterLevel| of the previous simulation step.
    """

    NDIM = 1
    SHAPE = (2,)


class DeltaWaterLevel(sequencetools.FactorSequence):
    """Effective difference of the two water levels [m].

    After each simulation step, the value of |DeltaWaterLevel| corresponds to the value
    of the |LoggedWaterLevel| of the previous simulation step.
    """

    NDIM = 0
