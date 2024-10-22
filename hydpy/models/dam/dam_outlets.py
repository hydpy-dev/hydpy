# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.OutletSequence):
    """Outflow [m³/s]."""

    NDIM, NUMERIC = 0, False


class S(sequencetools.OutletSequence):
    """Actual water supply [m³/s]."""

    NDIM, NUMERIC = 0, False


class R(sequencetools.OutletSequence):
    """Actual water relief [m³/s]."""

    NDIM, NUMERIC = 0, False
