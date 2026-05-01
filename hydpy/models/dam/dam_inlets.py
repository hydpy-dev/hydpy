# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.InletSequence):
    """Inflow [m³/s]."""

    NDIM: Final[Literal[1]] = 1


class S(sequencetools.InletSequence):
    """Actual water supply [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class R(sequencetools.InletSequence):
    """Actual water relief [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class E(sequencetools.InletSequence):
    """Bidirectional water exchange [m³/s]."""

    NDIM: Final[Literal[1]] = 1
