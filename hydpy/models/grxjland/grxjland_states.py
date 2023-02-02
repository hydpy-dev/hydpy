# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.grxjland import grxjland_control


class G(sequencetools.StateSequence):
    """Snow pack [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0, None)


class ETG(sequencetools.StateSequence):
    """Thermal state of Snow pack [°C]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, 0)


class GRatio(sequencetools.StateSequence):
    """Snow covered area [/]."""

    NDIM, NUMERIC, SPAN = 1, False, (0, 1)
    INIT = 0


class GLocalMax(sequencetools.StateSequence):
    """Local melt threshold [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0, None)


class S(sequencetools.StateSequence):
    """Water content production store [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)

    CONTROLPARAMETERS = (grxjland_control.X1,)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`S \\leq X1`.

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> x1(200.0)
        >>> states.s(-100.0)
        >>> states.s
        s(0.0)
        >>> states.s(300.0)
        >>> states.s
        s(200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.x1
        super().trim(lower, upper)


class R(sequencetools.StateSequence):
    """Level of the routing storage [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)

    CONTROLPARAMETERS = (grxjland_control.X3,)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`R \\leq X3`.

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> x3(200.0)
        >>> states.r(-100.0)
        >>> states.r
        r(0.0)
        >>> states.r(300.0)
        >>> states.r
        r(200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.x3
        super().trim(lower, upper)


class R2(sequencetools.StateSequence):
    """Level of the exponential storage [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
