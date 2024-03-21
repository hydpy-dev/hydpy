# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomisch mögliche Sonnenscheindauer (astronomically possible sunshine
    duration) [h]."""

    NDIM, NUMERIC = 0, False


class SunshineDuration(sequencetools.FactorSequence):
    """Sonnenscheindauer (sunshine duration) [h]."""

    NDIM, NUMERIC = 0, False
