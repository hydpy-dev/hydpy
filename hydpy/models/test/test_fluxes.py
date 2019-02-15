# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.FluxSequence):
    """Storage loss [mm/T]"""
    NDIM, NUMERIC, SPAN = 0, True, (0., None)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the Test model."""
    CLASSES = (Q,)
