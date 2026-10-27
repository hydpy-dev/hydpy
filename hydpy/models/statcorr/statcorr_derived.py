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
    """The number of log entries required for memorising the data for the
    logging window [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)
    CONTROLPARAMETERS = (statcorr_control.LoggingWindow,)

    def update(self) -> None:
        """Calculate the number of entries and adjust the shape of all relevant log
        sequences.

        The number of the required log entries depends on the
        parameter |LoggingWindow| and the simulation step size:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> from hydpy.core.timetools import Period
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
        >>> loggingwindow(24)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(24)
        >>> logs  # doctest: +ELLIPSIS
        loggedobserveddischarge(nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                nan, nan, nan, nan, nan, nan)
        loggedsimulateddischarge(nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan, nan, nan)

        To prevent losing information, updating parameter |NmbLogEntries| resets the
        shape of the relevant log sequences only when necessary:

        >>> logs.loggedobserveddischarge = 1.0
        >>> derived.nmblogentries(24)
        >>> logs  # doctest: +ELLIPSIS
        loggedobserveddischarge(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        loggedsimulateddischarge(nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan, nan, nan)

        .. testsetup::

            >>> del pub.timegrids
        """
        control = self.subpars.pars.control

        nmb = control.loggingwindow.value
        self(nmb)
        nmb = int(nmb)
        for seq in self.subpars.pars.model.sequences.logs:
            shape = exceptiontools.getattr_(seq, "shape", (None,))
            if nmb != shape[-1]:
                seq.shape = nmb


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
    """The threshold ratio of the minimum and the maximum measured discharge of the
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
    """The threshold for the sum of the absolute changes of the simulated discharge
    within the |EvaluationWindow| divided by |EvaluatedDischarge| of the variability
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
