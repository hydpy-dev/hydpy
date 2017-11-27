# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class WaterVolume(sequencetools.StateSequence):
    """Water volume [million m³]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the dam model."""
    _SEQCLASSES = (WaterVolume,)
