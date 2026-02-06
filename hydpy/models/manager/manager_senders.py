# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Request(sequencetools.SenderSequence):
    """The actual additional water release requested from the individual sources
    [m³/s]."""

    NDIM, NUMERIC = 1, False
