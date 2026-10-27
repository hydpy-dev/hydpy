# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class ReductionFactor(sequencetools.StateSequence):
    """Factor for linearly reducing the ARIMA correction to zero under instationary
    flow conditions (1.0: apply the correction unabated; 0.0: apply no correction at
    all) [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
    INIT = 1.0


class Stationary(sequencetools.StateSequence):
    """Flag (1.0: yes, 0.0: no) telling whether the measured discharge behaved in a
    stationary way at the last assessment (1.0: apply |ReductionFactor| unabated;
    0.0: reduce |ReductionFactor| linearly) [-].

    |statcorr_arima010| only reassesses stationarity while |Options.simulationmode|
    equals `historical`.  While it equals `forecast`, |Stationary| keeps the value
    determined at the most recent `historical` assessment, so |ReductionFactor|
    keeps ramping towards zero (or stays at ``1.0``) throughout the whole forecast
    horizon instead of jumping back to ``1.0`` once the logged observations run
    out."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
    INIT = 1.0


class EvaluatedDischarge(sequencetools.StateSequence):
    """The mean simulated discharge over the |EvaluationWindow| most recent log
    entries, as determined at the last `historical` assessment [m³/s].

    |Determine_OutputCorrection_V1| compares |EvaluatedDischarge| with |LowerLimit|
    and |UpperLimit| to decide whether the submodel is responsible for correcting
    the discharge.  Like |Stationary|, |statcorr_arima010| only reassesses
    |EvaluatedDischarge| while |Options.simulationmode| equals `historical`.
    While it equals `forecast`, |EvaluatedDischarge| keeps the value determined
    at the most recent `historical` assessment, so the responsible submodel does
    not change throughout the whole forecast horizon, regardless of how the
    forecasted discharge develops."""

    NDIM: Final[Literal[0]] = 0


class RelSumDelta(sequencetools.StateSequence):
    """The sum of the absolute changes of the simulated discharge within the
    |EvaluationWindow| divided by |EvaluatedDischarge|, as determined at the last
    `historical` assessment [-].

    Like |Stationary|, |statcorr_arima010| only reassesses |RelSumDelta| while
    |Options.simulationmode| equals `historical`."""

    NDIM: Final[Literal[0]] = 0


class LowVariability(sequencetools.StateSequence):
    """Flag (1.0: yes, 0.0: no) telling whether the variability check (see
    |VariabilityCheck|) found stationary conditions at the last assessment, so that
    the mean-value-based residual relies on the |StationaryAveragingWindow| instead
    of the |ResidualAveragingWindow| [-].

    Like |Stationary|, |statcorr_arima010| only reassesses |LowVariability| while
    |Options.simulationmode| equals `historical`."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)
    INIT = 0.0


class ForecastStep(sequencetools.StateSequence):
    """The number of elapsed forecast steps since the start of the current
    forecast run (``0.0`` on the first forecast step), reset to ``0.0``
    whenever |Options.simulationmode| equals `historical` [-].

    |Determine_OutputCorrection_V1| uses |ForecastStep| to linearly blend the
    applied residual from the single most recent (pointwise) value towards
    the mean-value-based residual determined via |ResidualAveragingWindow|
    over |ResidualTransitionTime| forecast steps."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)
    INIT = 0.0


class AveragedResidual(sequencetools.StateSequence):
    """The mean-value-based ARIMA residual (mean observed minus mean simulated
    discharge over the |ResidualAveragingWindow| log entries immediately
    preceding the current forecast run) in m³/s, determined once at the first
    forecast step and kept unchanged for the remainder of the forecast
    horizon."""

    NDIM: Final[Literal[0]] = 0
    INIT = 0.0


class Residual(sequencetools.StateSequence):
    """The pointwise ARIMA residual (observed minus simulated discharge, taken
    from the most recently logged entry with a non-|numpy.nan| observation,
    searching back at most |MaxNaNSkip| entries) in m³/s.

    Like |Stationary|, |statcorr_arima010| only
    reassesses |Residual| while |Options.simulationmode| equals `historical`.
    While it equals `forecast`, |Residual| keeps the value determined at the
    most recent `historical` assessment, so the applied correction persists
    throughout the whole forecast horizon (subject only to
    |ReductionFactor|) instead of vanishing as soon as the underlying log
    entry drops out of the logging window."""

    NDIM: Final[Literal[0]] = 0
    INIT = 0.0


class ResidualAnchor(sequencetools.StateSequence):
    """The simulated discharge (in m³/s) at the log position from which
    |Residual| was determined.

    Frozen together with |Residual| while |Options.simulationmode| equals
    `forecast`; see |Residual| for details."""

    NDIM: Final[Literal[0]] = 0
    INIT = 0.0
