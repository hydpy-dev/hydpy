# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Branched(sequencetools.LinkSequence):
    """Branched outputs [e.g. m³/s]."""
    NDIM, NUMERIC = 1, False


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of the hbranch model."""
    _SEQCLASSES = (Branched,)
