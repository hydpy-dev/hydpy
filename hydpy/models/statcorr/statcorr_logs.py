# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.statcorr import statcorr_variables


class LoggedObservation(statcorr_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged observed values [unit of the corrected variable]."""

    NDIM: Final[Literal[1]] = 1


class LoggedSimulation(statcorr_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged simulated values [unit of the corrected variable]."""

    NDIM: Final[Literal[1]] = 1
