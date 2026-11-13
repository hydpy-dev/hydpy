# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Discharge(sequencetools.InputSequence):
    """Discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)
    STANDARD_NAME = sequencetools.StandardInputNames.DISCHARGE
