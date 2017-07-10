# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Total(sequencetools.LinkSequence):
    """Total input [e.g. m³/s]."""
    NDIM, NUMERIC = 0, False


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the hbranch model."""
    _SEQCLASSES = (Total,)
