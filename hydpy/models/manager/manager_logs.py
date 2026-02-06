# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from manager
from hydpy.models.manager import manager_sequences


class LoggedDischarge(manager_sequences.MixinMemory, sequencetools.LogSequence):
    """Logged discharge values of the target location [m³/s]."""


class LoggedRequest(manager_sequences.MixinMemory, sequencetools.LogSequence):
    """Logged sums of the additional release requests of all sources directly
    neighbouring the target location [m³/s]."""


class LoggedWaterVolume(manager_sequences.MixinSource, sequencetools.LogSequence):
    """Logged water volumes of the individual sources [million m³]."""
