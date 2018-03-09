# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):   # pylint: disable=invalid-name
    """Discharge [m³/s]."""
    NDIM, NUMERIC = 0, False


class S(sequencetools.LinkSequence):   # pylint: disable=invalid-name
    """Water supply [m³/s]."""
    NDIM, NUMERIC = 0, False


class R(sequencetools.LinkSequence):   # pylint: disable=invalid-name
    """Water relief [m³/s]."""
    NDIM, NUMERIC = 0, False


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the dam model."""
    _SEQCLASSES = (Q,
                   S,
                   R)
