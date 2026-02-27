# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.InletSequence):
    """Runoff [m³/s]."""

    NDIM = 1
    NUMERIC = False
