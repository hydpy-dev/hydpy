# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SurfaceArea(sequencetools.AideSequence):
    """Surface area [km²]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class AllowedDischarge(sequencetools.AideSequence):
    """Discharge threshold that should not be overcut by the actual discharge
    [m³/s]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class AllowedWaterLevel(sequencetools.AideSequence):
    """The water level at the end of a simulation step that would follow from applying
    the allowed water level drop [m]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)
