# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from manager
from hydpy.models.manager import manager_sequences


class DemandTarget(sequencetools.FluxSequence):
    """The demand for additional water release at the target location [m³/s]."""

    NDIM, NUMERIC = 0, False


class FreeDischarge(sequencetools.FluxSequence):
    """The discharge at the target location that would have occurred without requesting
    additional water releases [m³/s]."""

    NDIM, NUMERIC = 0, False


class DemandSources(manager_sequences.MixinSource, sequencetools.FluxSequence):
    """The demand for additional water release at the individual sources [m³/s]."""


class PossibleRelease(manager_sequences.MixinSource, sequencetools.FluxSequence):
    """The possible additional water releases of the individual sources [m³/s]."""


class Request(manager_sequences.MixinSource, sequencetools.FluxSequence):
    """The actual additional water release requested from the individual sources
    [m³/s]."""
