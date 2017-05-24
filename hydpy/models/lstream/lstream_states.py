# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools

class QZ(sequencetools.StateSequence):
    """Zufluss in Gerinnestrecke (inflow into the channel) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QA(sequencetools.StateSequence):
    """Abfluss aus Gerinnestrecke (outflow out of the channel) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-L-Stream."""
    _SEQCLASSES = (QZ, QA)

