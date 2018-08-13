# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 0, False


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of the hland model."""
    CLASSES = (Q,)
