# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False


class Temperature(sequencetools.InputSequence):
    """Air temperature [°C]."""

    NDIM, NUMERIC = 0, False
