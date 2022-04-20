# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core.typingtools import *
from hydpy.models.musk import musk_sequences


class CourantNumber(musk_sequences.StateSequence1D):
    """Courant number [-]."""

    SPAN = (None, None)


class ReynoldsNumber(musk_sequences.StateSequence1D):
    """Cell Reynolds number [-]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)


class Discharge(musk_sequences.StateSequence1D):
    """Current discharge at the segment endpoints [m³/s]."""

    SPAN = (0.0, None)

    @property
    def refweights(self) -> NDArrayFloat:
        """Modified relative length of all channel segments.

        Opposed to other 1-dimensional |musk| sequences, |Discharge| handles values
        that apply to the start and endpoint of each channel segment.
        |Discharge.refweights| adjusts the returned relative lengths of all segments so
        that functions like |Variable.average_values| calculate the weighted average of
        the mean values of all segments, each one gained by averaging the discharge
        value at the start and the endpoint:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> length(4.0, 1.0, 3.0)
        >>> states.discharge.refweights
        array([0.25  , 0.3125, 0.25  , 0.1875])

        >>> states.discharge = 1.0, 2.0, 3.0, 4.0
        >>> states.discharge.average_values()
        2.375

        For a (non-existing) channel with zero segments, |Discharge.refweights| a
        single weight with the value one:

        >>> nmbsegments(0)
        >>> states.discharge.refweights
        array([1.])
        """
        control = self.subseqs.seqs.model.parameters.control
        nmbsegments = control.nmbsegments.value
        if nmbsegments == 0:
            return numpy.array([1.0], dtype=float)
        if hasattr(control, "length"):
            length = control.length.values
        else:
            length = numpy.ones((self.shape[0] - 1,), dtype=float)
        weights = numpy.zeros(self.shape, dtype=float)
        weights[:-1] = length
        weights[1:] += length

        return weights / numpy.sum(weights)
