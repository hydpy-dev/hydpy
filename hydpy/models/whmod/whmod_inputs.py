# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Precipitation(sequencetools.InputSequence):
    """[mm/T]"""

    NDIM, NUMERIC = 0, False


class Temperature(sequencetools.InputSequence):
    """[°C]"""

    NDIM, NUMERIC = 0, False
