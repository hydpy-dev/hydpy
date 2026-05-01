# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Y(sequencetools.SenderSequence):
    """Arbitrary kind of result data [?]."""

    NDIM: Final[Literal[1]] = 1
