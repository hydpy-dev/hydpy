# pylint: disable=missing-module-docstring

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.statcorr import statcorr_control


class NmbLogEntries(parametertools.NmbParameter):
    """The number of log entries required for memorising the simulated and observed
    values [-].

    Besides setting the shape of all log sequences (see |MixinLogEntries|),
    |NmbLogEntries| resets all state sequences to their initial values whenever its
    value changes, as the latter depend on the logged data:

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> derived.nmblogentries(2)
    >>> states.residual(2.0)
    >>> derived.nmblogentries(2)
    >>> states.residual
    residual(2.0)
    >>> derived.nmblogentries(3)
    >>> states.residual
    residual(0.0)
    """

    SPAN = (1, None)
    CONTROLPARAMETERS = (
        statcorr_control.EvaluationWindow,
        statcorr_control.StationarityCheck,
        statcorr_control.VariabilityCheck,
        statcorr_control.MaxNaNSkip,
        statcorr_control.AveragingWindow,
    )

    def update(self) -> None:
        """Calculate the number of required log entries and adjust the shape of
        all log sequences.

        The log must be as long as the largest value that uses it.

        |NmbLogEntries.update| raises an error if any relevant control parameter is
        still undefined:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> evaluationwindow(3)
        >>> stationaritycheck(active=True, window=4, ratiominmax=0.5)
        >>> variabilitycheck(active=False)
        >>> maxnanskip(1)
        >>> derived.nmblogentries.update()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: For variable `averagingwindow`, \
no value has been defined so far.

        Here, the window of the stationarity check is the largest value:

        >>> averagingwindow(1)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(4)

        Here, the averaging window of the variability check (plus one) is the
        largest value:

        >>> stationaritycheck(active=False)
        >>> variabilitycheck(active=True, maxrelsumdelta=0.2, averagingwindow=5)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(6)

        Here, |MaxNaNSkip| (plus one) is the largest value:

        >>> variabilitycheck(active=False)
        >>> maxnanskip(6)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(7)

        Here, |EvaluationWindow| is the largest value:

        >>> maxnanskip(0)
        >>> evaluationwindow(5)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(5)

        Here, |AveragingWindow| (plus one) is the largest value:

        >>> evaluationwindow(3)
        >>> averagingwindow(3)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(4)

        Whenever the number of log entries changes, |NmbLogEntries.update| resizes
        all log sequences (filling them with |numpy.nan| values) and resets all
        state sequences to their initial values, as the latter depend on the logged
        data:

        >>> logs
        loggedobservation(nan, nan, nan, nan)
        loggedsimulation(nan, nan, nan, nan)
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

        >>> logs.loggedobservation = 1.0
        >>> states.residual(2.0)
        >>> evaluationwindow(2)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(4)
        >>> logs.loggedobservation
        loggedobservation(1.0, 1.0, 1.0, 1.0)
        >>> states.residual
        residual(2.0)
        """
        control = self.subpars.pars.control
        stationaritycheck = control.stationaritycheck
        variabilitycheck = control.variabilitycheck
        nmb = max(
            control.evaluationwindow.value,
            stationaritycheck.window,
            control.maxnanskip.value + 1,
            control.averagingwindow.value + 1,
            variabilitycheck.averagingwindow + 1,
        )
        self(nmb)

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        if self.value != old:
            for state in self.subpars.pars.model.sequences.states:
                init = state.INIT
                if init is not None:
                    state(init)


class StationarityWindow(parametertools.Parameter):
    """The length of the assessment period of the stationarity check in log entries
    (zero if the check is disabled) [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)
    CONTROLPARAMETERS = (statcorr_control.StationarityCheck,)

    def update(self) -> None:
        """Take the assessment period from parameter |StationarityCheck|.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()

        >>> stationaritycheck(active=True, window=4, ratiominmax=0.5)
        >>> derived.stationaritywindow.update()
        >>> derived.stationaritywindow
        stationaritywindow(4)

        >>> stationaritycheck(active=False)
        >>> derived.stationaritywindow.update()
        >>> derived.stationaritywindow
        stationaritywindow(0)
        """
        stationaritycheck = self.subpars.pars.control.stationaritycheck
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

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()

        >>> stationaritycheck(active=True, window=4, ratiominmax=0.5)
        >>> derived.ratiominmax.update()
        >>> derived.ratiominmax
        ratiominmax(0.5)

        >>> stationaritycheck(active=False)
        >>> derived.ratiominmax.update()
        >>> derived.ratiominmax
        ratiominmax(0.0)
        """
        stationaritycheck = self.subpars.pars.control.stationaritycheck
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

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()

        >>> variabilitycheck(active=True, maxrelsumdelta=0.2, averagingwindow=24)
        >>> derived.maxrelsumdelta.update()
        >>> derived.maxrelsumdelta
        maxrelsumdelta(0.2)

        >>> variabilitycheck(active=False)
        >>> derived.maxrelsumdelta.update()
        >>> derived.maxrelsumdelta
        maxrelsumdelta(0.0)
        """
        variabilitycheck = self.subpars.pars.control.variabilitycheck
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

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()

        >>> variabilitycheck(active=True, maxrelsumdelta=0.2, averagingwindow=24)
        >>> derived.stationaryaveragingwindow.update()
        >>> derived.stationaryaveragingwindow
        stationaryaveragingwindow(24)

        >>> variabilitycheck(active=False)
        >>> derived.stationaryaveragingwindow.update()
        >>> derived.stationaryaveragingwindow
        stationaryaveragingwindow(0)
        """
        variabilitycheck = self.subpars.pars.control.variabilitycheck
        self(variabilitycheck.averagingwindow)
