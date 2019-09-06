# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Discharge [m³/s]."""
    NDIM, NUMERIC = 0, False


class S(sequencetools.LinkSequence):
    """Water supply [m³/s]."""
    NDIM, NUMERIC = 0, False


class R(sequencetools.LinkSequence):
    """Water relief [m³/s]."""
    NDIM, NUMERIC = 0, False


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the dam model."""
    CLASSES = (Q,
               S,
               R)
