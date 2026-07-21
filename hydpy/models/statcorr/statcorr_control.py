# pylint: disable=missing-module-docstring

from hydpy.core import exceptiontools
from hydpy.core import parametertools, timetools
from hydpy.core.typingtools import *


class LoggingWindow(parametertools.Parameter):
    """The length of the time period to be logged."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int


class NmbOutputCorrModels(parametertools.Parameter):
    """The number of output correction submodels [-].

    Setting |NmbOutputCorrModels| automatically resizes the
    |Model.outputcorrmodels| submodel slots accordingly:

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> nmboutputcorrmodels(3)
    >>> model.outputcorrmodels.number
    3
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.outputcorrmodels.number = self.value


class EvaluationWindow(parametertools.Parameter):
    """The length of the time period for evaluation of flow conditions."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int


class MaxResidualLookback(parametertools.Parameter):
    """The maximum number of log entries to search back for the most recently
    available residual when the current or recent observed discharge values are
    missing."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class CorrNQ(parametertools.Parameter):
    """Determines whether output correction is applied to the low flow range (NQ)"""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool


class CorrMQ(parametertools.Parameter):
    """Determines whether output correction is applied to the mean flow range (MQ)"""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool


class CorrHQ(parametertools.Parameter):
    """Determines whether output correction is applied to the high flow range (HQ)"""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool


class QminQmax(parametertools.Parameter):
    """Threshold value [%] for the quotient of the minimum and the maximum measured
    flow within the |NqmStationarityWindow| assessment period, below which flow
    conditions are considered instationary."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 100.0)


class NqmStationarityWindow(parametertools.Parameter):
    """Assessment period (timesteps) for determining stationarity
    of low and mean flow conditions"""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int


class LinearReductionTime(parametertools.Parameter):
    """Number of timesteps for linearly reducing the ARIMA correction to zero once
    instationary flow conditions are detected, separately for the NQ range (index 0)
    and the MQ range (index 1).

    >>> from hydpy.models.statcorr_arima010 import *
    >>> parameterstep()
    >>> control.linearreductiontime(12, 6)
    >>> control.linearreductiontime
    linearreductiontime(12, 6)
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = int
    SPAN = (0, None)

    def __call__(self, *args, **kwargs) -> None:
        self.shape = 2
        super().__call__(*args, **kwargs)


class LimitNQM(parametertools.Parameter):
    """
    Discharge threshold for the transition from NQ to MQ range in m³/s.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float


class LimitMQH(parametertools.Parameter):
    """
    Discharge threshold for the transition from MQ to HQ range in m³/s.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float


class MaxAbsoluteShift(parametertools.Parameter):
    """The maximum absolute shift (in m³/s) applied when the current forecast
    discharge exceeds the simulated discharge at the point the residual was
    determined (see |Determine_OutputCorrection_V1|)."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class MaxRelativeShift(parametertools.Parameter):
    """The maximum relative shift (in %) applied when the current forecast
    discharge is at or below the simulated discharge at the point the residual
    was determined (see |Determine_OutputCorrection_V1|)."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class ResidualAveragingWindow(parametertools.Parameter):
    """The length (in log entries) of the averaging period immediately
    preceding the current forecast run, used to determine the mean-value-based
    ARIMA residual (see |Determine_OutputCorrection_V1|).  Set to zero to
    disable mean-value-based correction and rely on the single most recent
    (pointwise) residual only, as |Determine_OutputCorrection_V1| already did
    before |ResidualAveragingWindow| and |ResidualTransitionTime| were
    introduced."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class ResidualTransitionTime(parametertools.Parameter):
    """The number of forecast steps over which the applied residual
    transitions linearly from the single most recent (pointwise) residual to
    the mean-value-based residual determined via |ResidualAveragingWindow|,
    avoiding an abrupt jump right at the start of the forecast horizon."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class PropagateCorrection(parametertools.Parameter):
    """Flag determining whether the corrected discharge is passed on to the
    downstream network (|True|) or calculated only for local output at the
    current gauge, while the uncorrected inflow is passed on instead
    (|False|)."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
