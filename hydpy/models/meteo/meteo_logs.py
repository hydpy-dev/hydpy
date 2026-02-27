# pylint: disable=missing-module-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedGlobalRadiation(sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedUnadjustedSunshineDuration(sequencetools.LogSequence):
    """Logged unadjusted sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedUnadjustedGlobalRadiation(sequencetools.LogSequence):
    """Logged unadjusted global radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
