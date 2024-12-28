# pylint: disable=missing-module-docstring

# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.gland import gland_control


class I(sequencetools.StateSequence):
    """Water content interception store [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)

    CONTROLPARAMETERS = (gland_control.IMax,)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`S \\leq X1`.

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> imax(20.0)
        >>> states.i(-10.0)
        >>> states.i
        i(0.0)
        >>> states.i(30.0)
        >>> states.i
        i(20.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.imax.value
        super().trim(lower, upper)


class S(sequencetools.StateSequence):
    """Water content production store [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)

    CONTROLPARAMETERS = (gland_control.X1,)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`S \\leq X1`.

        >>> from hydpy.models.gland import *
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
            upper = self.subseqs.seqs.model.parameters.control.x1.value
        super().trim(lower, upper)


class R(sequencetools.StateSequence):
    """Water content routing storage [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)

    CONTROLPARAMETERS = (gland_control.X3,)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`R \\leq X3`.

        >>> from hydpy.models.gland import *
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
            upper = self.subseqs.seqs.model.parameters.control.x3.value
        super().trim(lower, upper)


class R2(sequencetools.StateSequence):
    """Level of the exponential storage [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
