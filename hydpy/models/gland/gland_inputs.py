# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION
