# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class NmbZones(parametertools.NmbParameter):
    """The number of separately modelled zones [-]."""

    SPAN = (0, None)


class ComputesSnowEvaporation(parametertools.Parameter):
    """Flag that indicates whether the relevant snow model computes snow evaporation
    [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
    SPAN = (False, True)
