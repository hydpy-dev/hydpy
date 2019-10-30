# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.OutletSequence):
    """Abfluss (runoff) [m³/s]."""
    NDIM, NUMERIC = 0, False


class OutletSequences(sequencetools.OutletSequences):
    """Downstream link sequences of HydPy-L-Stream."""
    CLASSES = (Q,)
