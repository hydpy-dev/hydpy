# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class WaterLevel(sequencetools.AideSequence):
    """Water level [m]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class AideSequences(sequencetools.AideSequences):
    """State sequences of the dam model."""
    CLASSES = (WaterLevel,)
