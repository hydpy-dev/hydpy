# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core.typingtools import *
from hydpy.core import parametertools


class Parameter1D(parametertools.Parameter):
    """Base class for the 1-dimensional parameters."""

    NDIM = 1

    @property
    def refweights(self) -> NDArrayFloat:
        """The relative length of all channel segments.

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> length(4.0, 1.0, 3.0)
        >>> bottomwidth.refweights
        array([0.5  , 0.125, 0.375])
        """
        length = self.subpars.length.values
        return length / numpy.sum(length)
