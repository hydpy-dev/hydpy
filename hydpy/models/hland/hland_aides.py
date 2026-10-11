# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.hland import hland_variables


class SPE(hland_variables.MixinZones, sequencetools.AideSequence):
    """Subbasin-internal redistribution excess of the snow's ice content [mm/T]."""

    NDIM: Final[Literal[1]] = 1


class WCE(hland_variables.MixinZones, sequencetools.AideSequence):
    """Subbasin-internal redistribution excess of the snow's water content [mm/T]."""

    NDIM: Final[Literal[1]] = 1
