# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Total(sequencetools.InletSequence):
    """Total input [e.g. m³/s]."""

    NDIM: Final[Literal[1]] = 1
