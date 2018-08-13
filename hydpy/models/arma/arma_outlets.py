# -*- coding: utf-8 -*-

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 0, False


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of the ARMA model."""
    CLASSES = (Q,)
