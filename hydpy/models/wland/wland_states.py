# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

# ...from wland
from hydpy.models.wland import wland_sequences


class IC(wland_sequences.StateSequence1DLand):
    """Interception storage [mm]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True


class SP(wland_sequences.StateSequence1DLand):
    """Snow pack [mm]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True


class DVE(sequencetools.StateSequence):
    """Storage deficit of the vadose zone in the elevated region [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class DV(sequencetools.StateSequence):
    """Storage deficit of the vadose zone in the lowland region [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class HGE(sequencetools.StateSequence):
    """Groundwater level in the elevated region [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class DG(sequencetools.StateSequence):
    """Groundwater depth in the lowland region [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class HQ(sequencetools.StateSequence):
    """Level of the quickflow reservoir [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True


class HS(sequencetools.StateSequence):
    """Surface water level [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
