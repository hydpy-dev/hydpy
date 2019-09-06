# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class V(sequencetools.StateSequence):
    """Wasservolumen (water volume) [m³]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class W(sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-L-Lake."""
    CLASSES = (V,
               W)
