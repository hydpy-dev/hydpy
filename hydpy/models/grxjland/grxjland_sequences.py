# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import sequencetools


class Flux1DSequence(sequencetools.FluxSequence):
    """Base class for 1-dimensional factor subclasses that support aggregation.

    The following example shows how the subclass |Player| works:

    >>> from hydpy.models.grxjland import *
    >>> parameterstep("1d")
    >>> nsnowlayers(4)
    >>> fluxes.player(5.0, 2.0, 4.0, 1.0)
    >>> from hydpy import round_
    >>> round_(fluxes.player.average_values())
    3.0
    """

    NDIM = 1
    NUMERIC = False

    @property
    def refweights(self):
        """Weights for calculating mean."""
        return (
            numpy.ones(self.subseqs.seqs.model.parameters.control.nsnowlayers)
            / self.subseqs.seqs.model.parameters.control.nsnowlayers
        )
