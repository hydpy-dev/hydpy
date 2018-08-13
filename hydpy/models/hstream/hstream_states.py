# -*- coding: utf-8 -*-

# import...
# ...from standard library
import sys
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import sequencetools


class QJoints(sequencetools.StateSequence):
    """Runoff at the segment junctions [m³/s]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def __call__(self, *args):
        try:
            sequencetools.StateSequence.__call__(self, *args)
        except BaseException:
            message = sys.exc_info()[1]
            sequencetools.StateSequence.__call__(self, numpy.mean(args))
            warnings.warn('Note that, due to the following problem, the'
                          'affected HydPy-H-Stream model could be initialised '
                          'with an averaged value only: %s' % message)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the hstream model."""
    CLASSES = (QJoints,)
