# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class SurfaceArea(sequencetools.AideSequence):
    """Surface area [km²]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class AllowedDischarge(sequencetools.AideSequence):
    """Discharge threshold that should not be overcut by the actual discharge
    [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class AllowedWaterLevel(sequencetools.AideSequence):
    """The water level at the end of a simulation step that would follow from applying
    the allowed water level drop [m]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
