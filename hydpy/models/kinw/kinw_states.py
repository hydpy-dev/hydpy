# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class H(sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""

    NDIM, NUMERIC, SPAN = 1, True, (None, None)


class VG(sequencetools.StateSequence):
    """Wasservolumen (water volume) [million m³]."""

    NDIM, NUMERIC, SPAN = 1, True, (None, None)
