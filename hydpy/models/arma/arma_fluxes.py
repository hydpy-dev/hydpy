# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class QIn(sequencetools.FluxSequence):
    """Total inflow [m³/s]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (0.0, None)


class QPIn(sequencetools.FluxSequence):
    """Inflow portions corresponding to the different thresholds [m³/s]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)


class QMA(sequencetools.FluxSequence):
    """MA result for the different thresholds [m³/s]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)


class QAR(sequencetools.FluxSequence):
    """AR result for the different thresholds [m³/s]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)


class QPOut(sequencetools.FluxSequence):
    """Outflow portions corresponding to the different thresholds [m³/s]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)


class QOut(sequencetools.FluxSequence):
    """Total outflow [m³/s]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (0.0, None)
