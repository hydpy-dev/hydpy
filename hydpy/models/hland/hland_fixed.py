# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class Pi(parametertools.FixedParameter):
    """π [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 3.141592653589793


class FSG(parametertools.FixedParameter):
    """Fraction between the spatial extents of the first-order and the second-order
    slow response groundwater reservoir [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 8.0 / 9.0


class K1L(parametertools.FixedParameter):
    r"""Lowest possible lower boundary value for the parameters |K1|, |K2|, and |K3|
    [-].

    To prevent |SUZ| from taking on negative values, we must ensure that
    :math:`\left( 1 - e^{-1/K0} \right) + \left( 1 - e^{-1/K1} \right) < 1` holds.
    Also, we need to follow the restriction :math:`K0 \leq K1 \leq K2 \leq K3`.
    |K1L| defines the lowest value meeting both constraints:

    >>> from hydpy.models.hland import *
    >>> simulationstep("1h")
    >>> parameterstep("1d")
    >>> from numpy import exp
    >>> from hydpy import round_
    >>> round_(2.0 * (1.0 - exp(-1.0/fixed.k1l)))
    1.0
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.4426950408889632
