# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class Parameter0D(parametertools.Parameter):
    """Base class for scalar control parameters that handle float values."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
