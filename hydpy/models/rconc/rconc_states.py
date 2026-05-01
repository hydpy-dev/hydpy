# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class SC(sequencetools.StateSequence):
    """Storage cascade for runoff concentration [mm]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)
