# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.lland import lland_variables


class LoggedSunshineDuration(
    lland_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1


class LoggedPossibleSunshineDuration(
    lland_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
