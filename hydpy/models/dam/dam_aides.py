# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SurfaceArea(sequencetools.AideSequence):
    """Surface area [km²]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class AllowedDischarge(sequencetools.AideSequence):
    """Discharge threshold not to be overcut by the actual discharge [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)
