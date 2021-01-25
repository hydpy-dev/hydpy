# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.OutletSequence):
    """Runoff [m³/s]."""

    NDIM, NUMERIC = 0, False
