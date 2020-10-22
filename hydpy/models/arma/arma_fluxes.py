# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class QIn(sequencetools.FluxSequence):
    """Total inflow [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QPIn(sequencetools.FluxSequence):
    """Inflow portions corresponding to the different thresholds [m³/s]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class QMA(sequencetools.FluxSequence):
    """MA result for the different thresholds [m³/s]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class QAR(sequencetools.FluxSequence):
    """AR result for the different thresholds [m³/s]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class QPOut(sequencetools.FluxSequence):
    """Outflow portions corresponding to the different thresholds [m³/s]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class QOut(sequencetools.FluxSequence):
    """Total outflow [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)
