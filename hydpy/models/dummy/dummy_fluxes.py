# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.FluxSequence):
    """Abfluss [m³/s]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (0.0, None)
