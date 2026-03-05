# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Outputs(sequencetools.OutletSequence):
    """Outputs [?]."""

    NDIM: Final[Literal[1]] = 1
