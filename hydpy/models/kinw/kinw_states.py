# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.kinw import kinw_variables


class H(kinw_variables.MixinSubsections, sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True


class VG(kinw_variables.MixinSubsections, sequencetools.StateSequence):
    """Wasservolumen (water volume) [million m³]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True


class WaterVolume(kinw_variables.MixinSegments, sequencetools.StateSequence):
    """Water volume [million m³]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)
