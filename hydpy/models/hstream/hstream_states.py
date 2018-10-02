# -*- coding: utf-8 -*-

# import...
# ...from standard library
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import sequencetools


class QJoints(sequencetools.StateSequence):
    """Runoff at the segment junctions [m³/s].

    When a wrong number of input values is given, |QJoints| uses their
    average and emits the following warning:

    >>> from hydpy.models.hstream import *
    >>> parameterstep('1h')
    >>> simulationstep('1h')
    >>> lag(2.0)
    >>> derived.nmbsegments.update()
    >>> states.qjoints(1.0, 2.0)
    Traceback (most recent call last):
    ...
    UserWarning: Due to the following problem, state sequence `qjoints` of \
element `?` handling model `hstream` could be  initialised with an averaged \
value only: For sequence `qjoints` setting new values failed.  The values \
`(1.0, 2.0)` cannot be converted to a numpy ndarray with shape (3,) \
containing entries of type float.
    >>> states.qjoints
    qjoints(1.5, 1.5, 1.5)

    >>> states.qjoints(1.0, 2.0, 3.0)
    >>> states.qjoints
    qjoints(1.0, 2.0, 3.0)
    """
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def __call__(self, *args):
        try:
            sequencetools.StateSequence.__call__(self, *args)
        except BaseException as exc:
            sequencetools.StateSequence.__call__(self, numpy.mean(args))
            warnings.warn(
                f'Due to the following problem, state sequence '
                f'{objecttools.elementphrase(self)} handling model '
                f'`{self.subseqs.seqs.model}` could be  initialised '
                f'with an averaged value only: {exc}')

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
