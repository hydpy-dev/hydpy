# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class K(parametertools.Parameter):
    """Storage coefficient [1/T].

    For educational purposes, the actual value of parameter |K| does
    not depend on the difference between the actual simulation time step and
    the actual parameter time step.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class N(parametertools.NmbParameter):
    """Number of storages [-]."""

    SPAN = (1, None)
