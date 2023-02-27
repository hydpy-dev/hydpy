# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import variabletools


class FactorSequence1D(sequencetools.FactorSequence):
    """Base class for 1-dimensional factor sequences."""

    NDIM = 1
    mask = masktools.SubmodelIndexMask()


class FluxSequence1D(sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences."""

    NDIM = 1
    mask = masktools.SubmodelIndexMask()
