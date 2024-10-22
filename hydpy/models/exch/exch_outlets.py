# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Exchange(sequencetools.OutletSequence):
    """Bidirectional water exchange [m³/s]."""

    NDIM, NUMERIC = 1, False


class Branched(sequencetools.OutletSequence):
    """Branched outputs [e.g. m³/s]."""

    NDIM, NUMERIC = 1, False
