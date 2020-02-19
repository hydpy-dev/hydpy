# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.AideSequence):
    """Water level [m]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class SurfaceArea(sequencetools.AideSequence):
    """Surface area [million m²]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class AllowedDischarge(sequencetools.AideSequence):
    """Discharge threshold that should not be overcut by the actual discharge
    [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)
