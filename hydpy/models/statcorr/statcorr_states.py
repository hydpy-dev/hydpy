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


class FlowCondition(sequencetools.StateSequence):
    """The most recently determined flow condition (0.0: NQ, 1.0: MQ, 2.0: HQ) [-].

    Like |Stationary|, |statcorr_arima010| only reassesses |FlowCondition| while
    |Options.simulationmode| equals `historical`.  While it equals `forecast`,
    |FlowCondition| keeps the value determined at the most recent `historical`
    assessment, so |Determine_OutputCorrection_V1| always relies on the flow
    condition observed right before the forecast horizon started rather than on
    the (still continuously simulated) current discharge, which could otherwise
    let |ReductionFactor| jump back to ``1.0`` whenever the forecasted discharge
    happens to pass through the HQ range."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 2.0)
    INIT = 2.0


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
