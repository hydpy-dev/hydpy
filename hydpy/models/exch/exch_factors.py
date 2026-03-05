# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *


class WaterLevels(variabletools.MixinFixedShape, sequencetools.FactorSequence):
    """The water level at two locations [m].

    After each simulation step, the value of |exch_factors.WaterLevels| corresponds to
    the value of the |LoggedWaterLevels| of the previous simulation step.
    """

    NDIM: Final[Literal[1]] = 1
    SHAPE = (2,)


class DeltaWaterLevel(sequencetools.FactorSequence):
    """Effective difference of the two water levels [m].

    After each simulation step, the value of |DeltaWaterLevel| corresponds to the value
    of the |LoggedWaterLevels| of the previous simulation step.
    """

    NDIM: Final[Literal[0]] = 0


class X(sequencetools.FactorSequence):
    """Arbitrary kind of input data [?]."""

    NDIM: Final[Literal[0]] = 0


class Y(sequencetools.FactorSequence):
    """Arbitrary kind of result data [?]."""

    NDIM: Final[Literal[0]] = 0
