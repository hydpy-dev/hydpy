# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class R(sequencetools.ObserverSequence):
    """Externally requested water release [m³/s]."""

    NDIM, NUMERIC = 1, False
