# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class OriginalQ(sequencetools.FluxSequence):
    """Original (uncorrected) discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class CorrectedQ(sequencetools.FluxSequence):
    """Corrected Discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class CorrectedValue(sequencetools.FluxSequence):
    """Corrected value [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0


class IsActive(sequencetools.FluxSequence):
    """Flag (1.0: yes, 0.0: no) telling whether the submodel corrected the simulated
    value in the current simulation step [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
