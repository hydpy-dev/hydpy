# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.models.manager import manager_variables


class LoggedDischarge(manager_variables.MixinMemory, sequencetools.LogSequence):
    """Logged discharge values of the target location [m³/s]."""


class LoggedRequest(manager_variables.MixinMemory, sequencetools.LogSequence):
    """Logged sums of the additional release requests of all sources directly
    neighbouring the target location [m³/s]."""


class LoggedWaterVolume(
    manager_variables.MixinSourceSequence, sequencetools.LogSequence
):
    """Logged water volumes of the individual sources [million m³]."""
