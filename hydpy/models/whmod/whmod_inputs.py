# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM = 0
    NUMERIC = False


class Temperature(sequencetools.InputSequence):
    """Air temperature [°C]."""

    NDIM = 0
    NUMERIC = False
