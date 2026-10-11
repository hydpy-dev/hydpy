# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class NmbZones(parametertools.NmbParameter):
    """The number of separately modelled zones [-]."""

    SPAN = (0, None)
