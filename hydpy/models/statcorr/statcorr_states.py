# pylint: disable=missing-module-docstring

import numpy

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class ReductionFactor(sequencetools.StateSequence):
    """Factor for linearly reducing the ARIMA correction to zero during forecast runs
    under instationary conditions (1.0: apply the correction unabated; 0.0: apply no
    correction at all) [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
    INIT = 1.0


class Stationary(sequencetools.StateSequence):
    """Flag (1.0: yes, 0.0: no) telling whether the observed values behaved in a
    stationary way at the last assessment (1.0: apply |ReductionFactor| unabated;
    0.0: reduce |ReductionFactor| linearly) [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
    INIT = 1.0


class EvaluatedValue(sequencetools.StateSequence):
    """The mean of the available observed values over the |EvaluationWindow| most
    recent log entries, as determined at the last `historical` assessment [unit of
    the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    INIT = numpy.nan


class RelSumDelta(sequencetools.StateSequence):
    """The sum of the absolute changes of the simulated values within the
    |EvaluationWindow| divided by their mean, as determined at the last `historical`
    assessment [-]."""

    NDIM: Final[Literal[0]] = 0
    INIT = numpy.nan


class LowVariability(sequencetools.StateSequence):
    """Flag (1.0: yes, 0.0: no) telling whether the variability check found
    low variability conditions at the last assessment [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
    INIT = 0.0


class ForecastStep(sequencetools.StateSequence):
    """The number of elapsed forecast steps since the start of the current
    forecast run [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)
    INIT = 0.0


class AveragedResidual(sequencetools.StateSequence):
    """The mean-value-based residual (mean observed minus mean simulated value)
    [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    INIT = 0.0


class Residual(sequencetools.StateSequence):
    """The pointwise residual (observed minus simulated value) [unit of the
    corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    INIT = 0.0


class ResidualAnchor(sequencetools.StateSequence):
    """The simulated value at the log position from which
    |Residual| was determined [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    INIT = 0.0
