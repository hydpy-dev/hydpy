# pylint: disable=missing-module-docstring

import numpy

from hydpy.core.typingtools import *
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_sequences


class Snowpack(snow_sequences.StateSequence2D):
    """Snow pack [mm]."""

    SPAN = (0.0, None)


class WaterContent(snow_sequences.StateSequence2D):
    """Liquid water content of the snow layer [mm]."""


class SP(snow_sequences.StateSequence2D):
    """Frozen water stored in the snow layer [mm]."""

    CONTROLPARAMETERS = (snow_control.WaterCapacity,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim |SP| following :math:`WC \leq WHC \cdot SP`.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> sclass(2)
        >>> whc(0.1)
        >>> states.sp([[-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...            [-2.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.sp
        sp([[0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
            [0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.wc.values = [[-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0],
        ...                     [-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0]]
        >>> states.sp([[-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...            [-2.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.sp
        sp([[0.0, 0.0, 10.0, 5.0, 5.0, 5.0, 10.0],
            [0.0, 0.0, 10.0, 6.0, 6.0, 6.0, 10.0]])
        >>> whc(0.0)
        >>> states.wc.values = 0.0
        >>> states.sp([[-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...            [-2.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        >>> states.sp
        sp([[0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
            [0.0, 0.0, 0.0, 6.0, 6.0, 6.0, 6.0]])
        """
        whc = self.subseqs.seqs.model.parameters.control.whc
        wc = self.subseqs.wc
        if lower is None:
            wc_values = wc.values.copy()
            wc_values[numpy.isnan(wc_values)] = 0.0
            with numpy.errstate(divide="ignore", invalid="ignore"):
                lower = numpy.clip(wc_values / whc.values, 0.0, numpy.inf)
                lower[:, whc.values == 0.0] = 0.0  # type: ignore[index]
        return super().trim(lower, upper)


class WC(snow_sequences.StateSequence2D):
    """Liquid water content of the snow layer [mm]."""

    SPAN = (0.0, None)

    CONTROLPARAMETERS = (snow_control.WaterCapacity,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        """Trim |WC| following :math:`WC \\leq WHC \\cdot SP`.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> sclass(2)
        >>> whc(0.1)
        >>> states.sp = [[0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0],
        ...              [0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0]]
        >>> states.wc([[-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0],
        ...            [-0.2, 0.0, 0.2, -0.2, 0.0, 0.1, 0.2]])
        >>> states.wc
        wc([[0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2]])
        """
        whc = self.subseqs.seqs.model.parameters.control.whc
        sp = self.subseqs.sp
        if upper is None:
            upper = whc * sp
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
