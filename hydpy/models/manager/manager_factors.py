# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Alertness(sequencetools.FactorSequence):
    """The current need for low water control [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
