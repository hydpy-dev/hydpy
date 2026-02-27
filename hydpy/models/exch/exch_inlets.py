# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Total(sequencetools.InletSequence):
    """Total input [e.g. m³/s]."""

    NDIM = 1
    NUMERIC = False
