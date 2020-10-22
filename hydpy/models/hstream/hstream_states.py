# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

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
    >>> parameterstep("1h")
    >>> simulationstep("1h")
    >>> lag(2.0)
    >>> derived.nmbsegments.update()
    >>> states.qjoints(1.0, 2.0)
    Traceback (most recent call last):
    ...
    UserWarning: Due to the following problem, state sequence `qjoints` of \
element `?` handling model `hstream` could be  initialised with an averaged \
value only: While trying to set the value(s) of variable `qjoints`, the \
following error occurred: While trying to convert the value(s) `(1.0, 2.0)` \
to a numpy ndarray with shape `(3,)` and type `float`, the following error \
occurred: could not broadcast input array from shape (2) into shape (3)

    >>> states.qjoints
    qjoints(1.5, 1.5, 1.5)

    >>> states.qjoints(1.0, 2.0, 3.0)
    >>> states.qjoints
    qjoints(1.0, 2.0, 3.0)
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    def __call__(self, *args):
        try:
            super().__call__(*args)
        except BaseException as exc:
            super().__call__(numpy.mean(args))
            warnings.warn(
                f"Due to the following problem, state sequence "
                f"{objecttools.elementphrase(self)} handling model "
                f"`{self.subseqs.seqs.model}` could be  initialised "
                f"with an averaged value only: {exc}"
            )

    @property
    def refweights(self):
        """A |numpy| |numpy.ndarray| with equal weights for all segment
        junctions..

        >>> from hydpy.models.hstream import *
        >>> parameterstep("1d")
        >>> states.qjoints.shape = 5
        >>> states.qjoints.refweights
        array([ 0.2,  0.2,  0.2,  0.2,  0.2])
        """
        # pylint: disable=unsubscriptable-object
        # due to a pylint bug (see https://github.com/PyCQA/pylint/issues/870)
        return numpy.full(self.shape, 1.0 / self.shape[0], dtype=float)
