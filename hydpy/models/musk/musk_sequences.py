# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
import warnings

# ...from site-packages
import numpy

# ...from HydPy
from hydpy import config
from hydpy.core.typingtools import *
from hydpy.core import objecttools
from hydpy.core import sequencetools


class MixinSequence1D:
    """Mixin class for the 1-dimensional sequences."""

    NDIM, NUMERIC = 1, False

    subseqs: sequencetools.ModelIOSequences

    @property
    def refweights(self) -> VectorFloat:
        """The relative length of all channel segments.

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(4)
        >>> fluxes.referencedischarge.refweights
        array([0.25, 0.25, 0.25, 0.25])
        """
        nmbsegments = self.subseqs.seqs.model.parameters.control.nmbsegments.values
        return numpy.full(nmbsegments, 1.0 / nmbsegments, dtype=config.NP_FLOAT)


class StateSequence1D(  # type: ignore[misc]
    MixinSequence1D, sequencetools.StateSequence
):
    """Base class for the 1-dimensional state sequences.

    For a wrong number of input values, subclasses like |Discharge| use their average
    and emit the following warning:

    >>> from hydpy.models.musk import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     states.discharge(1.0, 2.0)
    UserWarning: Due to the following problem, state sequence `discharge` of element \
`?` handling model `musk` could be initialised with an averaged value only: While \
trying to set the value(s) of variable `discharge`, the following error occurred: \
While trying to convert the value(s) `(1.0, 2.0)` to a numpy ndarray with shape \
`(3,)` and type `float`, the following error occurred: could not broadcast input \
array from shape (2,) into shape (3,)

    >>> states.discharge
    discharge(1.5, 1.5, 1.5)

    >>> states.discharge(1.0, 2.0, 3.0)
    >>> states.discharge
    discharge(1.0, 2.0, 3.0)
    """

    def __call__(self, *args) -> None:
        try:
            super().__call__(*args)
        except BaseException as exc:
            super().__call__(numpy.mean(args))
            warnings.warn(
                f"Due to the following problem, state sequence "
                f"{objecttools.elementphrase(self)} handling model "
                f"`{self.subseqs.seqs.model}` could be initialised with an averaged "
                f"value only: {exc}"
            )


class FactorSequence1D(  # type: ignore[misc]
    MixinSequence1D, sequencetools.FactorSequence
):
    """Base class for the 1-dimensional factor sequences."""


class FluxSequence1D(MixinSequence1D, sequencetools.FluxSequence):  # type: ignore[misc]
    """Base class for the 1-dimensional flux sequences."""
