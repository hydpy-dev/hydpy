# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.wq import wq_variables


class Discharges(wq_variables.MixinWidthsOrShapes, sequencetools.FluxSequence):
    """The discharge of each trapezoidal range [m³/s]."""


class Discharge(sequencetools.FluxSequence):
    """Total discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
