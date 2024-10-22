# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.InletSequence):
    """Abfluss (runoff) [m³/s]."""

    NDIM, NUMERIC = 1, False
