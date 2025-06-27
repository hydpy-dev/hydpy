# pylint: disable=missing-module-docstring
# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core import variabletools


class WaterLevels(variabletools.MixinFixedShape, sequencetools.FactorSequence):
    """The water level at two locations [m].

    After each simulation step, the value of |exch_factors.WaterLevels| corresponds to
    the value of the |LoggedWaterLevels| of the previous simulation step.
    """

    NDIM = 1
    SHAPE = (2,)


class DeltaWaterLevel(sequencetools.FactorSequence):
    """Effective difference of the two water levels [m].

    After each simulation step, the value of |DeltaWaterLevel| corresponds to the value
    of the |LoggedWaterLevels| of the previous simulation step.
    """

    NDIM = 0


class X(sequencetools.FactorSequence):
    """Arbitrary kind of input data [?]."""

    NDIM = 0


class Y(sequencetools.FactorSequence):
    """Arbitrary kind of result data [?]."""

    NDIM = 0
