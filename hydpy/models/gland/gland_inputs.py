# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION
