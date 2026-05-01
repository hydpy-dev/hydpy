# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.FluxSequence):
    """Storage loss [mm/T]"""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
    SPAN = (0.0, None)


class QV(sequencetools.FluxSequence):
    """Storage loss vector [mm/T]"""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True
    SPAN = (0.0, None)
