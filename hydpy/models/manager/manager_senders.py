# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Request(sequencetools.SenderSequence):
    """The actual additional water release requested from the individual sources
    [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
