# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedPossibleSunshineDuration(sequencetools.LogSequence):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
