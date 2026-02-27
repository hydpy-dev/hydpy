# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class A(sequencetools.ObserverSequence):
    """Externally requested additional water release [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
