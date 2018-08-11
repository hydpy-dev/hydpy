# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class WET0(sequencetools.LogSequence):
    """Zeitlich gewichtete Grasreferenzverdunstung (temporally weighted
    reference evapotranspiration) [mm].

    Log sequence |WET0| is generally initialized with a length of one
    on the first axis:

    >>> from hydpy.models.lland import *
    >>> parameterstep()
    >>> logs.wet0.shape = 3
    >>> logs.wet0.shape
    (1, 3)
    """
    NDIM, NUMERIC = 2, False

    @sequencetools.LogSequence.shape.setter
    def shape(self, shape):
        sequencetools.LogSequence.shape.fset(self, (1, shape))

class LogSequences(sequencetools.LogSequences):
    """Log sequences of the HydPy-L-Land model."""
    CLASSES = (WET0,)
