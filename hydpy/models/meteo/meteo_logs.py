# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.meteo import meteo_variables


class LoggedSunshineDuration(
    meteo_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1


class LoggedGlobalRadiation(meteo_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1


class LoggedUnadjustedSunshineDuration(
    meteo_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged unadjusted sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1


class LoggedUnadjustedGlobalRadiation(
    meteo_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged unadjusted global radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1
