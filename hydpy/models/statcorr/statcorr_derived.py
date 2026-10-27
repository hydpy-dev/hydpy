# pylint: disable=missing-module-docstring

import hydpy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.statcorr import statcorr_control


class IsForecastMode(parametertools.Parameter):
    """Flag telling whether |Options.simulationmode| currently is `forecast` [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool

    def update(self) -> None:
        """Take the current value of |Options.simulationmode| from module |pub|.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> derived.isforecastmode.update()
        >>> derived.isforecastmode
        isforecastmode(False)

        >>> pub.options.simulationmode = "forecast"
        >>> derived.isforecastmode.update()
        >>> derived.isforecastmode
        isforecastmode(True)

        >>> del pub.options.simulationmode
        """
        self(hydpy.pub.options.simulationmode == "forecast")


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for memorising the simulated and observed
    values [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)
    CONTROLPARAMETERS = (
        statcorr_control.EvaluationWindow,
        statcorr_control.StationarityCheck,
        statcorr_control.VariabilityCheck,
        statcorr_control.MaxNaNSkip,
        statcorr_control.AveragingWindow,
    )

    def update(self) -> None:
        """Calculate the number of required log entries from the submodel's other
        parameters and adjust the shape of all log sequences.

        The log must cover the |EvaluationWindow|, the assessment period of the
        stationarity check (see |StationarityCheck|), and the |MaxNaNSkip| most
        recent entries.  The mean-value-based residual (see
        |Calc_AveragedResidual_V1|) relies on the |AveragingWindow| (or the averaging
        period of the variability check, see |VariabilityCheck|) entries preceding
        the current one, which requires one additional entry.

        As long as not all relevant control parameters are defined,
        |NmbLogEntries.update| leaves the current value untouched:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> evaluationwindow(3)
        >>> stationaritycheck(window=4, ratiominmax=0.5)
        >>> variabilitycheck(False)
        >>> maxnanskip(2)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(?)

        >>> averagingwindow(1)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(4)

        >>> stationaritycheck(False)
        >>> variabilitycheck(maxrelsumdelta=0.2, averagingwindow=5)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(6)

        >>> variabilitycheck(False)
        >>> maxnanskip(7)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(7)

        >>> maxnanskip(0)
        >>> averagingwindow(3)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(4)

        Whenever the number of log entries changes, |NmbLogEntries.update| resizes
        all log sequences (filling them with |numpy.nan| values) and resets all
        state sequences to their initial values, as the latter depend on the logged
        data:

        >>> logs
        loggedobservedvalue(nan, nan, nan, nan)
        loggedsimulatedvalue(nan, nan, nan, nan)
        >>> states
        reductionfactor(1.0)
        stationary(1.0)
        evaluatedvalue(nan)
        relsumdelta(nan)
        lowvariability(0.0)
        forecaststep(0.0)
        averagedresidual(0.0)
        residual(0.0)
        residualanchor(0.0)

        To prevent losing information, it leaves the log and state sequences
        untouched as long as the number of log entries does not change:

        >>> logs.loggedobservedvalue = 1.0
        >>> states.residual(2.0)
        >>> evaluationwindow(2)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(4)
        >>> logs.loggedobservedvalue
        loggedobservedvalue(1.0, 1.0, 1.0, 1.0)
        >>> states.residual
        residual(2.0)
        """
        control = self.subpars.pars.control
        stationaritycheck = cast(
            statcorr_control.StationarityCheck, control.stationaritycheck
        )
        variabilitycheck = cast(
            statcorr_control.VariabilityCheck, control.variabilitycheck
        )
        if not (
            stationaritycheck.configured
            and variabilitycheck.configured
            and exceptiontools.attrready(control.evaluationwindow, "value")
            and exceptiontools.attrready(control.maxnanskip, "value")
            and exceptiontools.attrready(control.averagingwindow, "value")
        ):
            return
        nmb = max(
            control.evaluationwindow.value,
            stationaritycheck.window,
            control.maxnanskip.value,
            control.averagingwindow.value + 1,
            variabilitycheck.averagingwindow + 1,
        )
        self(nmb)
        nmb = int(self.value)
        sequences = self.subpars.pars.model.sequences
        resized = False
        for seq in sequences.logs:
            shape = exceptiontools.getattr_(seq, "shape", (None,))
            if nmb != shape[-1]:
                seq.shape = nmb
                resized = True
        if resized:
            for state in sequences.states:
                state(state.INIT)


class StationarityWindow(parametertools.Parameter):
    """The length of the assessment period of the stationarity check in log entries
    (zero if the check is disabled) [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)
    CONTROLPARAMETERS = (statcorr_control.StationarityCheck,)

    def update(self) -> None:
        """Take the assessment period from parameter |StationarityCheck|.

        As long as |StationarityCheck| is not configured,
        |StationarityWindow.update| leaves the current value untouched:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.stationaritywindow.update()
        >>> derived.stationaritywindow
        stationaritywindow(?)

        >>> stationaritycheck(window=4, ratiominmax=0.5)
        >>> derived.stationaritywindow.update()
        >>> derived.stationaritywindow
        stationaritywindow(4)

        >>> stationaritycheck(False)
        >>> derived.stationaritywindow.update()
        >>> derived.stationaritywindow
        stationaritywindow(0)
        """
        stationaritycheck = cast(
            statcorr_control.StationarityCheck,
            self.subpars.pars.control.stationaritycheck,
        )
        if stationaritycheck.configured:
            self(stationaritycheck.window)


class RatioMinMax(parametertools.Parameter):
    """The threshold ratio of the minimum and the maximum observed values of the
    stationarity check (zero if the check is disabled) [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)
    CONTROLPARAMETERS = (statcorr_control.StationarityCheck,)

    def update(self) -> None:
        """Take the threshold ratio from parameter |StationarityCheck|.

        As long as |StationarityCheck| is not configured, |RatioMinMax.update| leaves
        the current value untouched:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.ratiominmax.update()
        >>> derived.ratiominmax
        ratiominmax(?)

        >>> stationaritycheck(window=4, ratiominmax=0.5)
        >>> derived.ratiominmax.update()
        >>> derived.ratiominmax
        ratiominmax(0.5)

        >>> stationaritycheck(False)
        >>> derived.ratiominmax.update()
        >>> derived.ratiominmax
        ratiominmax(0.0)
        """
        stationaritycheck = cast(
            statcorr_control.StationarityCheck,
            self.subpars.pars.control.stationaritycheck,
        )
        if stationaritycheck.configured:
            self(stationaritycheck.ratiominmax)


class MaxRelSumDelta(parametertools.Parameter):
    """The threshold for the sum of the absolute changes of the simulated values
    within the |EvaluationWindow| divided by |EvaluatedValue| of the variability
    check (zero if the check is disabled) [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    CONTROLPARAMETERS = (statcorr_control.VariabilityCheck,)

    def update(self) -> None:
        """Take the threshold from parameter |VariabilityCheck|.

        As long as |VariabilityCheck| is not configured, |MaxRelSumDelta.update|
        leaves the current value untouched:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.maxrelsumdelta.update()
        >>> derived.maxrelsumdelta
        maxrelsumdelta(?)

        >>> variabilitycheck(maxrelsumdelta=0.2, averagingwindow=24)
        >>> derived.maxrelsumdelta.update()
        >>> derived.maxrelsumdelta
        maxrelsumdelta(0.2)

        >>> variabilitycheck(False)
        >>> derived.maxrelsumdelta.update()
        >>> derived.maxrelsumdelta
        maxrelsumdelta(0.0)
        """
        variabilitycheck = cast(
            statcorr_control.VariabilityCheck,
            self.subpars.pars.control.variabilitycheck,
        )
        if variabilitycheck.configured:
            self(variabilitycheck.maxrelsumdelta)


class StationaryAveragingWindow(parametertools.Parameter):
    """The length of the averaging period for determining the mean-value-based
    residual under stationary conditions in log entries (zero if the variability
    check is disabled) [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)
    CONTROLPARAMETERS = (statcorr_control.VariabilityCheck,)

    def update(self) -> None:
        """Take the averaging period from parameter |VariabilityCheck|.

        As long as |VariabilityCheck| is not configured,
        |StationaryAveragingWindow.update| leaves the current value untouched:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.stationaryaveragingwindow.update()
        >>> derived.stationaryaveragingwindow
        stationaryaveragingwindow(?)

        >>> variabilitycheck(maxrelsumdelta=0.2, averagingwindow=24)
        >>> derived.stationaryaveragingwindow.update()
        >>> derived.stationaryaveragingwindow
        stationaryaveragingwindow(24)

        >>> variabilitycheck(False)
        >>> derived.stationaryaveragingwindow.update()
        >>> derived.stationaryaveragingwindow
        stationaryaveragingwindow(0)
        """
        variabilitycheck = cast(
            statcorr_control.VariabilityCheck,
            self.subpars.pars.control.variabilitycheck,
        )
        if variabilitycheck.configured:
            self(variabilitycheck.averagingwindow)
