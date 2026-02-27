# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LongQ(sequencetools.OutletSequence):
    """The longitudinal outflow of the last channel segment [m³/s]."""

    NDIM = 1
    NUMERIC = False
