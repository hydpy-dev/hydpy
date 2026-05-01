# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Inputs(sequencetools.InletSequence):
    """Inputs [?]."""

    NDIM: Final[Literal[1]] = 1
