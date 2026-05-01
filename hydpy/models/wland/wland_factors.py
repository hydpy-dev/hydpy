# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class DHS(sequencetools.FactorSequence):
    """External change of the surface water depth [mm/T]."""

    NDIM: Final[Literal[0]] = 0
