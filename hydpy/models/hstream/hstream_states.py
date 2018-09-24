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
            warnings.warn(
                f'Note that, due to the following problem, the '
                f'affected HydPy-H-Stream model could be initialised '
                f'with an averaged value only: {message}')

    @property
    def refweights(self):
        """A |numpy| |numpy.ndarray| with equal weights for all segment
        junctions..

        >>> from hydpy.models.hstream import *
        >>> parameterstep('1d')
        >>> states.qjoints.shape = 5
        >>> states.qjoints.refweights
        array([ 0.2,  0.2,  0.2,  0.2,  0.2])
        """
        return numpy.full(self.shape, 1./self.shape[0], dtype=float)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the hstream model."""
    CLASSES = (QJoints,)
