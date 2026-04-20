# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class InputSequence0D(sequencetools.InputSequence):
    """Base class for scalar input sequences."""

    NDIM: Final[Literal[0]] = 0


class FluxSequence0D(sequencetools.FluxSequence):
    """Base class for scalar flux sequences."""

    NDIM: Final[Literal[0]] = 0


class StateSequence0D(sequencetools.StateSequence):
    """Base class for scalar state sequences."""

    NDIM: Final[Literal[0]] = 0


class OutletSequence0D(sequencetools.OutletSequence):
    """Base class for scalar state sequences."""

    NDIM: Final[Literal[0]] = 0
