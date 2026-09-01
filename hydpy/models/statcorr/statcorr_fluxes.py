# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Inflow(sequencetools.FluxSequence):
    """Inflow [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class CorrectedQ(sequencetools.FluxSequence):
    """Corrected Discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
