# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class H(sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""
    NDIM, NUMERIC, SPAN = 1, True, (0., None)
