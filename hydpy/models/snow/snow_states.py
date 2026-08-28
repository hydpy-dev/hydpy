# pylint: disable=missing-module-docstring

import numpy

from hydpy.core.typingtools import *
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_sequences


class IceContent(snow_sequences.StateSequence2D):
    """Frozen water content of the snow layer [mm]."""

    SPAN = (0.0, None)

    CONTROLPARAMETERS = (snow_control.WaterCapacity,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim |IceContent| following
        :math:`WaterContent \leq WaterCapacity \cdot IceContent`.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(7)
        >>> numberdivisions(2)
        >>> watercapacity(0.1)
        >>> states.icecontent([[-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...                    [-2.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.icecontent
        icecontent([[0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
                    [0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])

        >>> states.watercontent = [[-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0],
        ...                        [-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0]]
        >>> states.icecontent([[-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...                    [-2.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.icecontent
        icecontent([[0.0, 0.0, 10.0, 5.0, 5.0, 5.0, 10.0],
                    [0.0, 0.0, 10.0, 6.0, 6.0, 6.0, 10.0]])

        >>> watercapacity(0.0)
        >>> states.watercontent = 0.0
        >>> states.icecontent([[-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...                    [-2.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.icecontent
        icecontent([[0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
                    [0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        """
        if lower is None:
            capacity = self.subseqs.seqs.model.parameters.control.watercapacity.values
            water = self.subseqs.watercontent.values.copy()
            water[numpy.isnan(water)] = 0.0
            with numpy.errstate(divide="ignore", invalid="ignore"):
                lower = numpy.clip(water / capacity, 0.0, numpy.inf)
                lower[:, capacity == 0.0] = 0.0
        return super().trim(lower, upper)


class WaterContent(snow_sequences.StateSequence2D):
    """Liquid water content of the snow layer [mm]."""

    SPAN = (0.0, None)

    CONTROLPARAMETERS = (snow_control.WaterCapacity,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim |WaterContent| following
        :math:`WaterContent \leq WaterCapacity \cdot IceContent`.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(7)
        >>> numberdivisions(2)
        >>> watercapacity(0.1)
        >>> states.watercontent([[-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0],
        ...                      [-0.2, 0.0, 0.2, -0.2, 0.0, 0.1, 0.2]])
        >>> states.watercontent
        watercontent([[0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 1.0],
                      [0.0, 0.0, 0.2, 0.0, 0.0, 0.1, 0.2]])

        >>> states.icecontent = [[0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...                      [0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0]]
        >>> states.watercontent([[-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0],
        ...                      [-0.2, 0.0, 0.2, -0.2, 0.0, 0.1, 0.2]])
        >>> states.watercontent
        watercontent([[0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2]])
        """
        if upper is None:
            capacity = self.subseqs.seqs.model.parameters.control.watercapacity.values
            ice = self.subseqs.icecontent.values
            upper = capacity * ice
        return super().trim(lower, upper)


class G(snow_sequences.State1DNLayers):
    """Snow pack [mm]."""

    SPAN = (0.0, None)


class ETG(snow_sequences.State1DNLayers):
    """Thermal state of the snow pack [°C]."""

    SPAN = (None, 0.0)


class GRatio(snow_sequences.State1DNLayers):
    """Ratio of the snow-covered area [-]."""

    SPAN = (0.0, 1.0)
