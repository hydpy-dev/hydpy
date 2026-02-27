# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class SurfaceWaterSupply(sequencetools.FluxSequence):
    """Water supply to the soil's surface [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class SoilWaterSupply(sequencetools.FluxSequence):
    """Water supply to the soil's body (e.g., capillary rise) [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class Demand(sequencetools.FluxSequence):
    """(Potential) water withdrawal from the soil's surface and body [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class Infiltration(sequencetools.FluxSequence):
    """Infiltration through the soil's surface [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class Percolation(sequencetools.FluxSequence):
    """Percolation through the soil's bottom [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class SoilWaterAddition(sequencetools.FluxSequence):
    """Actual addition of soil water due to processes like capillary rise [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class Withdrawal(sequencetools.FluxSequence):
    """Withdrawal from the soil's surface or body (e.g. due to evaporation) [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class SurfaceRunoff(sequencetools.FluxSequence):
    """Surface runoff [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class TotalInfiltration(sequencetools.FluxSequence):
    """Average infiltration of the whole subbasin [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class TotalPercolation(sequencetools.FluxSequence):
    """Average percolation of the whole subbasin [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class TotalSoilWaterAddition(sequencetools.FluxSequence):
    """Average soil water addition to the whole subbasin [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class TotalWithdrawal(sequencetools.FluxSequence):
    """Average withdrawal of the whole subbasin [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False


class TotalSurfaceRunoff(sequencetools.FluxSequence):
    """Average surface runoff of the whole subbasin [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
