# pylint: disable=missing-module-docstring

from hydpy.core import masktools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.meteo import meteo_variables


class FactorSequence1D(meteo_variables.MixinHRUs, sequencetools.FactorSequence):
    """Base class for 1-dimensional flux sequences."""

    NDIM: Final[Literal[1]] = 1
    mask = masktools.SubmodelIndexMask()


class FluxSequence1D(meteo_variables.MixinHRUs, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences."""

    NDIM: Final[Literal[1]] = 1
    mask = masktools.SubmodelIndexMask()
