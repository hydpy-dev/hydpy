# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Inflow(sequencetools.FluxSequence):
    """Inflow [mm/T]."""

    NDIM: Final[Literal[0]] = 0


class Outflow(sequencetools.FluxSequence):
    """Outflow [mm/T]."""

    NDIM: Final[Literal[0]] = 0
