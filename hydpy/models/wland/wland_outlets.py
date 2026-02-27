# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.OutletSequence):
    """Discharge [m³/s]."""

    NDIM = 0
    NUMERIC = False
