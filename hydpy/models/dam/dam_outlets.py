# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.OutletSequence):
    """Outflow [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class S(sequencetools.OutletSequence):
    """Actual water supply [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class R(sequencetools.OutletSequence):
    """Actual water relief [m³/s]."""

    NDIM: Final[Literal[0]] = 0
