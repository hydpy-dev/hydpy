# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class S(sequencetools.StateSequence):
    """Storage content [mm]."""
    NDIM, NUMERIC, SPAN = 0, True, (0., None)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the Test model."""
    _SEQCLASSES = (S,)
