# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class S(sequencetools.StateSequence):
    """Storage content [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class SV(sequencetools.StateSequence):
    """Storage content vector[mm]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)
