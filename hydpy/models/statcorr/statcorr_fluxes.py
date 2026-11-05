# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Inflow(sequencetools.FluxSequence):
    """Inflow [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class CorrectedQ(sequencetools.FluxSequence):
    """Corrected Discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class CorrectedValue(sequencetools.FluxSequence):
    """Corrected value [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0


class ForecastMode(sequencetools.FluxSequence):
    """Flag (1.0: `forecast`, 0.0: `historical`) telling the simulation mode the main
    model passed to |Determine_OutputCorrection_V1| in the current simulation step
    [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)


class IsActive(sequencetools.FluxSequence):
    """Flag (1.0: yes, 0.0: no) telling whether the submodel corrected the simulated
    value in the current simulation step (see |Calc_IsActive_V1|) [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
