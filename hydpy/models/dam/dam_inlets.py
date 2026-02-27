# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.InletSequence):
    """Inflow [m³/s]."""

    NDIM = 1
    NUMERIC = False


class S(sequencetools.InletSequence):
    """Actual water supply [m³/s]."""

    NDIM = 0
    NUMERIC = False


class R(sequencetools.InletSequence):
    """Actual water relief [m³/s]."""

    NDIM = 0
    NUMERIC = False


class E(sequencetools.InletSequence):
    """Bidirectional water exchange [m³/s]."""

    NDIM = 1
    NUMERIC = False
