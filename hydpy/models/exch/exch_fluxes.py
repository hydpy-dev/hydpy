# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class PotentialExchange(sequencetools.FluxSequence):
    """The potential bidirectional water exchange [m³/s]."""

    NDIM, NUMERIC = 0, False


class ActualExchange(sequencetools.FluxSequence):
    """The actual bidirectional water exchange [m³/s]."""

    NDIM, NUMERIC = 0, False
