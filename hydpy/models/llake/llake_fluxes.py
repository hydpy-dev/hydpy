# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class QZ(sequencetools.FluxSequence):
    """Seezufluss (inflow into the lake) [m³/s]."""
    NDIM, NUMERIC = 0, False


class QA(sequencetools.FluxSequence):
    """Seeausfluss (outflow from the lake) [m³/s]."""
    NDIM, NUMERIC = 0, False


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-L-Lake."""
    CLASSES = (QZ,
               QA)
