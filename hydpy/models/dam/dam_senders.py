# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.SenderSequence):
    """Discharge [m³/s]."""
    NDIM, NUMERIC = 0, False


class D(sequencetools.SenderSequence):
    """Water demand [m³/s]."""
    NDIM, NUMERIC = 0, False


class S(sequencetools.SenderSequence):
    """Water supply [m³/s]."""
    NDIM, NUMERIC = 0, False


class R(sequencetools.SenderSequence):
    """Water relief [m³/s]."""
    NDIM, NUMERIC = 0, False


class SenderSequences(sequencetools.SenderSequences):
    """Information link sequences of the dam model."""
    CLASSES = (Q,
               D,
               S,
               R)
