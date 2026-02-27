# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Index(sequencetools.AideSequence):
    """Index of the measured height directly below the current height [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (0.0, None)


class Excess(sequencetools.AideSequence):
    """Difference between the current height and the next-lower measured height [m]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (0.0, None)


class Weight(sequencetools.AideSequence):
    """Linear weighting factor that is zero if the current height equals the next-lower
    measured height and one if it equals the next-higher measured height [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (0.0, 1.0)
