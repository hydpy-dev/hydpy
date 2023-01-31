# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class QA(sequencetools.AideSequence):
    """Seeausfluss (outflow from the lake) [m³/s]."""

    NDIM, NUMERIC = 0, False


class VQ(sequencetools.AideSequence):
    """Hilfsterm (auxiliary term) [m³]."""

    NDIM, NUMERIC = 0, False


class V(sequencetools.AideSequence):
    """Wasservolumen (water volume) [m³]."""

    NDIM, NUMERIC = 0, False
