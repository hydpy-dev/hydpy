# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class SPE(sequencetools.AideSequence):
    """Subbasin-internal redistribution excess of the snow's ice content [mm/T]."""

    NDIM: Final[Literal[1]] = 1


class WCE(sequencetools.AideSequence):
    """Subbasin-internal redistribution excess of the snow's water content [mm/T]."""

    NDIM: Final[Literal[1]] = 1
