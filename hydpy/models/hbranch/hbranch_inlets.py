# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Total(sequencetools.InletSequence):
    """Total input [e.g. m³/s]."""
    NDIM, NUMERIC = 1, False


class InletSequences(sequencetools.InletSequences):
    """Upstream link sequences of the hbranch model."""
    CLASSES = (Total,)
