# -*- coding: utf-8 -*-

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Total(sequencetools.LinkSequence):
    """Total input [e.g. m³/s]."""
    NDIM, NUMERIC = 0, False


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the hbranch model."""
    CLASSES = (Total,)
