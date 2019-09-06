# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class S(sequencetools.StateSequence):
    """Storage content [mm]."""
    NDIM, NUMERIC, SPAN = 0, True, (0., None)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the Test model."""
    CLASSES = (S,)
