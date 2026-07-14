# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
