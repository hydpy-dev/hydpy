# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
import warnings

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.StateSequence):
    """Current runoff at the segment endpoints [m³/s].

    When a wrong number of input values is given, |musk_states.Q| uses their
    average and emits the following warning:

    >>> from hydpy.models.musk import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     states.q(1.0, 2.0)
    UserWarning: Due to the following problem, state sequence `q` of element `?` \
handling model `musk` could be  initialised with an averaged value only: While trying \
to set the value(s) of variable `q`, the following error occurred: While trying to \
convert the value(s) `(1.0, 2.0)` to a numpy ndarray with shape `(3,)` and type \
`float`, the following error occurred: could not broadcast input array from shape \
(2,) into shape (3,)

    >>> states.q
    q(1.5, 1.5, 1.5)

    >>> states.q(1.0, 2.0, 3.0)
    >>> states.q
    q(1.0, 2.0, 3.0)
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    def __call__(self, *args) -> None:
        try:
            super().__call__(*args)
        except BaseException as exc:
            super().__call__(numpy.mean(args))
            warnings.warn(
                f"Due to the following problem, state sequence "
                f"{objecttools.elementphrase(self)} handling model "
                f"`{self.subseqs.seqs.model}` could be  initialised with an averaged "
                f"value only: {exc}"
            )

    @property
    def refweights(self) -> NDArrayFloat:
        """A |numpy| |numpy.ndarray| with equal weights for all segment junctions.

        >>> from hydpy.models.musk import *
        >>> parameterstep("1d")
        >>> states.q.shape = 5
        >>> states.q.refweights
        array([0.2, 0.2, 0.2, 0.2, 0.2])
        """
        return numpy.full(self.shape, 1.0 / self.shape[0], dtype=float)
