# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.FluxSequence):
    """Storage loss [mm/T]"""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class QV(sequencetools.FluxSequence):
    """Storage loss vector [mm/T]"""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)
