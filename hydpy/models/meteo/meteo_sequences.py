# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class FactorSequence1D(sequencetools.FactorSequence):
    """Base class for 1-dimensional flux sequences."""

    NDIM: Final[Literal[1]] = 1
    mask = masktools.SubmodelIndexMask()


class FluxSequence1D(sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences."""

    NDIM: Final[Literal[1]] = 1
    mask = masktools.SubmodelIndexMask()
