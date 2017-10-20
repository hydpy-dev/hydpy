# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class WaterLevel(sequencetools.FluxSequence):
    """Water level [m]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class AideSequences(sequencetools.AideSequences):
    """State sequences of the dam model."""
    _SEQCLASSES = (WaterLevel,)
