# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.ReceiverSequence):
    """Remote discharge [m³/s]."""

    NDIM = 0
    NUMERIC = False


class D(sequencetools.ReceiverSequence):
    """Water demand [m³/s]."""

    NDIM = 0
    NUMERIC = False


class S(sequencetools.ReceiverSequence):
    """Required water supply [m³/s]."""

    NDIM = 0
    NUMERIC = False


class R(sequencetools.ReceiverSequence):
    """Allowed water relief [m³/s]."""

    NDIM = 0
    NUMERIC = False


class OWL(sequencetools.ReceiverSequence):
    """The water level directly below the dam [m]."""

    NDIM = 0
    NUMERIC = False


class RWL(sequencetools.ReceiverSequence):
    """The water level at a remote location [m]."""

    NDIM = 0
    NUMERIC = False
