# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.FluxSequence):
    """Abfluss [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)
