# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.OutletSequence):
    """Discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
