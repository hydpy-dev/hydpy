# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LogIn(sequencetools.LogSequence):
    """The recent and the past inflow portions for the application of the
    different MA processes [m³/s]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False
    SPAN = (None, None)


class LogOut(sequencetools.LogSequence):
    """The past outflow portions for the application of the
    different AR processes [m³/s]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False
    SPAN = (None, None)
