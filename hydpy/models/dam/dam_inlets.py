# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.InletSequence):
    """Inflow [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class S(sequencetools.InletSequence):
    """Actual water supply [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class R(sequencetools.InletSequence):
    """Actual water relief [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class E(sequencetools.InletSequence):
    """Bidirectional water exchange [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
