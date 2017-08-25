# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """runoff [m³/s]."""
    NDIM, NUMERIC = 0, False


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of GlobWat."""
    _SEQCLASSES = (Q,)
