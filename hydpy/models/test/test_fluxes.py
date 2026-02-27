# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.FluxSequence):
    """Storage loss [mm/T]"""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class QV(sequencetools.FluxSequence):
    """Storage loss vector [mm/T]"""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)
