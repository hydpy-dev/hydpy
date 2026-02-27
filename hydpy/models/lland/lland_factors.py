# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomisch mögliche Sonnenscheindauer (astronomically possible sunshine
    duration) [h]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class SunshineDuration(sequencetools.FactorSequence):
    """Sonnenscheindauer (sunshine duration) [h]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
