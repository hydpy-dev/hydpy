# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
import sys
import warnings
# ...from site-packages
import numpy
# ...HydPy specific
from hydpy.core import sequencetools


class QUH(sequencetools.LogSequence):
    """Whole outflow delayed by means of the unit hydrograph [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def __call__(self, *args):
        try:
            sequencetools.LogSequence.__call__(self, *args)
        except BaseException:
            message = sys.exc_info()[1]
            sequencetools.LogSequence.__call__(self, numpy.sum(args))
            warnings.warn('Note that, due to the following problem, the '
                          'unit-hydrograph of the affected HydPy-H-Land '
                          'model could be initialised with an summed '
                          'value only: %s' % message)
        # The last value must be zero, otherwise all results were biased:
        self.values[-1] = 0.


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the hland model."""
    _SEQCLASSES = (QUH,)
