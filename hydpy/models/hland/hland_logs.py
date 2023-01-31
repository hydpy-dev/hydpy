# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
import warnings

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class QUH(sequencetools.LogSequence):
    """All temporary outflow values of the unit hydrograph [mm].

    The last value is always set to zero to avoid biased results:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1h")
    >>> simulationstep("1h")
    >>> maxbaz(3.0)
    >>> derived.uh.update()
    >>> logs.quh(1.0, 2.0, 1.0)
    >>> logs.quh
    quh(1.0, 2.0, 0.0)

    For a wrong number of input values, |QUH| distributes their sum equally and emits
    the following warning:

    >>> logs.quh(1.0, 2.0, 3.0, 0.0)   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    UserWarning: Due to the following problem, log sequence `quh` of element `?` \
handling model `hland` could be initialised with a averaged value only: While trying \
to set the value(s) of variable `quh`, the following error occurred: While trying to \
convert the value(s) `(1.0, 2.0, 3.0, 0.0)` to a numpy ndarray with shape `(3...)` and \
type `float`, the following error occurred: could not broadcast input array from shape \
(4...) into shape (3...)

    >>> logs.quh
    quh(3.0, 3.0, 0.0)
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    def __call__(self, *args):
        try:
            super().__call__(*args)
            self.values[-1] = 0.0
        except BaseException as exc:
            super().__call__(numpy.sum(args) / (self.shape[0] - 1))
            self.values[-1] = 0.0
            warnings.warn(
                f"Due to the following problem, log sequence "
                f"{objecttools.elementphrase(self)} handling model "
                f"`{self.subseqs.seqs.model}` could be initialised "
                f"with a averaged value only: {exc}"
            )

    @property
    def refweights(self) -> Vector[float]:
        """A vector with identical values (so that averaging the values of |QUH|
        results in the arithmetic mean value).

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> logs.quh.shape = 3
        >>> logs.quh.refweights
        array([1., 1., 1.])
        """
        return numpy.ones(self.shape, dtype=float)
