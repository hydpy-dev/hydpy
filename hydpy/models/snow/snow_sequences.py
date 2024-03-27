# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages

# ...from HydPy
from hydpy.core import sequencetools


class Flux1DSequence(sequencetools.FluxSequence):
    """Base class for 1-dimensional factor subclasses that support aggregation.

    The following example shows how the subclass |PLayer| works:

    >>> from hydpy.models.snow import *
    >>> parameterstep("1d")
    >>> nsnowlayers(4)
    >>> layerarea(0.25, 0.25, 0.25, 0.25)
    >>> fluxes.player(5.0, 2.0, 4.0, 1.0)
    >>> from hydpy import round_
    >>> round_(fluxes.player.average_values())
    3.0

    >>> layerarea(0.6, 0.2, 0.1, 0.1)
    >>> round_(fluxes.player.average_values())
    3.9
    """

    NDIM = 1
    NUMERIC = False

    @property
    def refweights(self):
        """Weights for calculating mean."""
        return self.subseqs.seqs.model.parameters.control.layerarea
