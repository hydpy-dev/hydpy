# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class A(sequencetools.ObserverSequence):
    """Externally requested additional water release [m³/s]."""

    NDIM = 1
    NUMERIC = False
