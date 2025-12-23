# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SurfaceArea(sequencetools.AideSequence):
    """Surface area [km²]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class AllowedDischarge(sequencetools.AideSequence):
    """Discharge threshold that should not be overcut by the actual discharge
    [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class AllowedWaterLevel(sequencetools.AideSequence):
    """The water level at the end of a simulation step that would follow from applying
    the allowed water level drop [m]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)
