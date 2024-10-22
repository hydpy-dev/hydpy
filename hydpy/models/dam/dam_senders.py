# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class D(sequencetools.SenderSequence):
    """Water demand [m³/s]."""

    NDIM, NUMERIC = 0, False


class S(sequencetools.SenderSequence):
    """Required water supply [m³/s]."""

    NDIM, NUMERIC = 0, False


class R(sequencetools.SenderSequence):
    """Required water relief [m³/s]."""

    NDIM, NUMERIC = 0, False
