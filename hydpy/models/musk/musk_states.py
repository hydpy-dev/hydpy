# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy import config
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

        >>> from hydpy import round_
        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> round_(states.discharge.refweights)
        0.166667, 0.333333, 0.333333, 0.166667

        >>> states.discharge = 1.0, 2.0, 3.0, 4.0
        >>> round_(states.discharge.average_values())
        2.5

        For a (non-existing) channel with zero segments, |Discharge.refweights| a
        single weight with the value one:

        >>> nmbsegments(0)
        >>> round_(states.discharge.refweights)
        1.0
        """
        nmbsegments = self.subseqs.seqs.model.parameters.control.nmbsegments.value
        if nmbsegments == 0:
            return numpy.array([1.0], dtype=config.NP_FLOAT)
        weights = numpy.ones(nmbsegments + 1, dtype=config.NP_FLOAT)
        weights[1:-1] += 1.0
        return weights / numpy.sum(weights)
