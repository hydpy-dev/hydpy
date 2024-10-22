# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class S(sequencetools.StateSequence):
    """Storage content [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class SV(sequencetools.StateSequence):
    """Storage content vector[mm]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)
