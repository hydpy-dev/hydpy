# pylint: disable=missing-module-docstring

from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *


class NmbSubmodels(parametertools.Parameter):
    """The number of output correction submodels [-].

    Setting |NmbSubmodels| automatically resizes the
    |Model.outputcorrmodels| submodel slots accordingly:

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> nmbsubmodels(3)
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
    """The length of the time period for evaluating the current conditions."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int


class MaxNaNSkip(parametertools.Parameter):
    """The maximum number of log entries to search back for the most recently
    available residual when the current or recent observed values are
    missing."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class Active(parametertools.Parameter):
    """Flag determining whether the submodel may correct the simulated values at
    all [-].

    Even when |Active| is |True|, the submodel only corrects the simulated values
    while the relevant mean simulated value lies within the range defined by
    |LowerLimit| and |UpperLimit| (see |Determine_OutputCorrection_V1|)."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool


class CorrectionMode(parametertools.Parameter):
    """The simulation mode(s) in which the submodel may correct the simulated
    values [-].

    Pass one of the strings `historical`, `forecast`, or `both`, corresponding to
    the possible values of |Options.simulationmode|.  Internally, |CorrectionMode|
    stores them as the integer values 1, 2, and 3:

    >>> from hydpy.models.statcorr_arima010 import *
    >>> parameterstep()
    >>> correctionmode
    correctionmode(?)
    >>> correctionmode("historical")
    >>> correctionmode
    correctionmode("historical")
    >>> correctionmode.value
    1
    >>> correctionmode("forecast")
    >>> correctionmode
    correctionmode("forecast")
    >>> correctionmode.value
    2
    >>> correctionmode("both")
    >>> correctionmode
    correctionmode("both")
    >>> correctionmode.value
    3

    Other strings are not allowed:

    >>> correctionmode("always")
    Traceback (most recent call last):
    ...
    ValueError: For parameter `correctionmode` of element `?`, the given mode \
`always` is not among the supported modes `historical`, `forecast`, and `both`.

    Passing the integer values directly is also possible:

    >>> correctionmode(1)
    >>> correctionmode
    correctionmode("historical")

    Regardless of |CorrectionMode|, the submodel keeps updating its log and states
    in both simulation modes (see |Determine_OutputCorrection_V1|).
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, 3)

    MODES: Final = {"historical": 1, "forecast": 2, "both": 3}

    def __call__(self, *args, **kwargs) -> None:
        if (len(args) == 1) and not kwargs and isinstance(args[0], str):
            mode = args[0]
            if mode not in self.MODES:
                raise ValueError(
                    f"For parameter {objecttools.elementphrase(self)}, the given "
                    f"mode `{mode}` is not among the supported modes `historical`, "
                    f"`forecast`, and `both`."
                )
            super().__call__(self.MODES[mode])
        else:
            super().__call__(*args, **kwargs)

    def __repr__(self) -> str:
        for mode, value in self.MODES.items():
            if exceptiontools.getattr_(self, "value", None) == value:
                return f'{self.name}("{mode}")'
        return super().__repr__()


class LowerLimit(parametertools.Parameter):
    """Lower (inclusive) limit of the submodel's range of responsibility
    [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class UpperLimit(parametertools.Parameter):
    """Upper (exclusive) limit of the submodel's range of responsibility
    [unit of the corrected variable].

    Set it to |numpy.inf| to define a range without an upper limit."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class StationarityCheck(parametertools.SpecialParameter):
    """Configuration of the check of whether the observed values behave in a
    stationary way [-].

    |StationarityCheck| is a special parameter (see |SpecialParameter|).  Either
    switch the check off by passing |False| or switch it on by passing the length of
    the assessment period (`window`, in log entries) and the threshold for the ratio
    of the minimum and the maximum observed values within this period
    (`ratiominmax`), below which |Determine_OutputCorrection_V1| considers the
    conditions instationary:

    >>> from hydpy.models.statcorr_arima010 import *
    >>> parameterstep()
    >>> stationaritycheck
    stationaritycheck(?)
    >>> stationaritycheck.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: For parameter `stationaritycheck` of element `?`, it is still \
unknown whether the stationarity check is enabled.

    >>> stationaritycheck(False)
    >>> stationaritycheck
    stationaritycheck(False)
    >>> stationaritycheck.verify()

    Passing `window` and `ratiominmax` implicitly enables the check:

    >>> stationaritycheck(window=10, ratiominmax=0.5)
    >>> stationaritycheck
    stationaritycheck(window=10, ratiominmax=0.5)
    >>> stationaritycheck.enabled, stationaritycheck.window
    (True, 10)
    >>> from hydpy import round_
    >>> round_(stationaritycheck.ratiominmax)
    0.5

    Passing |True| explicitly is allowed but optional:

    >>> stationaritycheck(True, window=5, ratiominmax=0.8)
    >>> stationaritycheck
    stationaritycheck(window=5, ratiominmax=0.8)

    An enabled check requires both `window` and `ratiominmax`:

    >>> stationaritycheck(True)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, both `window` and \
`ratiominmax` must be given when enabling the stationarity check.

    >>> stationaritycheck(window=5)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, both `window` and \
`ratiominmax` must be given when enabling the stationarity check.

    A disabled check does not accept `window` or `ratiominmax`:

    >>> stationaritycheck(False, window=5, ratiominmax=0.8)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `window` and \
`ratiominmax` must not be given when disabling the stationarity check.

    >>> stationaritycheck()
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, pass either a \
boolean value or the keyword arguments `window` and `ratiominmax`.

    `window` must be a positive integer, and `ratiominmax` must lie between zero and
    one:

    >>> stationaritycheck(window=0, ratiominmax=0.8)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `window` must be a \
positive integer, but `0` is given.

    >>> stationaritycheck(window=5, ratiominmax=1.5)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `ratiominmax` must \
lie between zero and one, but `1.5` is given.

    Failed calls leave the previous configuration untouched:

    >>> stationaritycheck
    stationaritycheck(window=5, ratiominmax=0.8)
    """

    _config: tuple[bool, int, float] | None

    def __init__(self, subvars: variabletools.SubVariables[Any, Any, Any, Any]) -> None:
        super().__init__(subvars)
        self._config = None

    def __call__(
        self,
        value: bool | None = None,
        *,
        window: int | None = None,
        ratiominmax: float | None = None,
    ) -> None:
        if (value is False) and ((window is not None) or (ratiominmax is not None)):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, `window` and "
                f"`ratiominmax` must not be given when disabling the stationarity "
                f"check."
            )
        if value is False:
            self._config = (False, 0, 0.0)
            return
        if (value is None) and (window is None) and (ratiominmax is None):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, pass either a "
                f"boolean value or the keyword arguments `window` and `ratiominmax`."
            )
        if (window is None) or (ratiominmax is None):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, both `window` and "
                f"`ratiominmax` must be given when enabling the stationarity check."
            )
        if (int(window) != window) or (window < 1):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, `window` must be a "
                f"positive integer, but `{window}` is given."
            )
        if not 0.0 <= ratiominmax <= 1.0:
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, `ratiominmax` must "
                f"lie between zero and one, but `{ratiominmax}` is given."
            )
        self._config = (True, int(window), float(ratiominmax))

    def __repr__(self) -> str:
        if self._config is None:
            return f"{self.name}(?)"
        enabled, window, ratiominmax = self._config
        if not enabled:
            return f"{self.name}(False)"
        return (
            f"{self.name}(window={window}, "
            f"ratiominmax={objecttools.repr_(ratiominmax)})"
        )

    def verify(self) -> None:
        """Raise a |RuntimeError| if the configuration is still unknown."""
        if self._config is None:
            raise RuntimeError(
                f"For parameter {objecttools.elementphrase(self)}, it is still unknown "
                f"whether the stationarity check is enabled."
            )

    @property
    def configured(self) -> bool:
        """Flag indicating whether the stationarity check has already been
        configured.

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> stationaritycheck.configured
        False
        >>> stationaritycheck(False)
        >>> stationaritycheck.configured
        True
        """
        return self._config is not None

    def _get_config(self) -> tuple[bool, int, float]:
        self.verify()
        assert self._config is not None
        return self._config

    @property
    def enabled(self) -> bool:
        """Flag indicating whether the stationarity check is enabled."""
        return self._get_config()[0]

    @property
    def window(self) -> int:
        """The length of the assessment period in log entries (zero if the check is
        disabled)."""
        return self._get_config()[1]

    @property
    def ratiominmax(self) -> float:
        """The threshold ratio of the minimum and the maximum observed values
        (zero if the check is disabled)."""
        return self._get_config()[2]


class VariabilityCheck(parametertools.SpecialParameter):
    """Configuration of the check of whether the simulated values vary little
    enough to base the correction on a long-term mean residual [-].

    |VariabilityCheck| is a special parameter (see |SpecialParameter|).  Either
    switch the check off by passing |False| or switch it on by passing the threshold
    for the sum of the absolute changes of the simulated values within the
    |EvaluationWindow| divided by |EvaluatedValue| (`maxrelsumdelta`) and the
    length of the averaging period (`averagingwindow`, in log entries) for
    determining the mean-value-based residual under stationary conditions (see
    |Determine_OutputCorrection_V1|):

    >>> from hydpy.models.statcorr_arima010 import *
    >>> parameterstep()
    >>> variabilitycheck
    variabilitycheck(?)
    >>> variabilitycheck.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: For parameter `variabilitycheck` of element `?`, it is still \
unknown whether the variability check is enabled.

    >>> variabilitycheck(False)
    >>> variabilitycheck
    variabilitycheck(False)
    >>> variabilitycheck.verify()

    Passing `maxrelsumdelta` and `averagingwindow` implicitly enables the check:

    >>> variabilitycheck(maxrelsumdelta=0.2, averagingwindow=24)
    >>> variabilitycheck
    variabilitycheck(maxrelsumdelta=0.2, averagingwindow=24)
    >>> variabilitycheck.enabled, variabilitycheck.averagingwindow
    (True, 24)
    >>> from hydpy import round_
    >>> round_(variabilitycheck.maxrelsumdelta)
    0.2

    Passing |True| explicitly is allowed but optional:

    >>> variabilitycheck(True, maxrelsumdelta=0.1, averagingwindow=12)
    >>> variabilitycheck
    variabilitycheck(maxrelsumdelta=0.1, averagingwindow=12)

    An enabled check requires both `maxrelsumdelta` and `averagingwindow`:

    >>> variabilitycheck(True)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `variabilitycheck` of element `?`, both \
`maxrelsumdelta` and `averagingwindow` must be given when enabling the variability \
check.

    >>> variabilitycheck(maxrelsumdelta=0.1)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `variabilitycheck` of element `?`, both \
`maxrelsumdelta` and `averagingwindow` must be given when enabling the variability \
check.

    A disabled check does not accept `maxrelsumdelta` or `averagingwindow`:

    >>> variabilitycheck(False, maxrelsumdelta=0.1, averagingwindow=12)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `variabilitycheck` of element `?`, `maxrelsumdelta` \
and `averagingwindow` must not be given when disabling the variability check.

    >>> variabilitycheck()
    Traceback (most recent call last):
    ...
    ValueError: For parameter `variabilitycheck` of element `?`, pass either a \
boolean value or the keyword arguments `maxrelsumdelta` and `averagingwindow`.

    `maxrelsumdelta` must not be negative, and `averagingwindow` must be a positive
    integer:

    >>> variabilitycheck(maxrelsumdelta=-0.1, averagingwindow=12)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `variabilitycheck` of element `?`, `maxrelsumdelta` \
must not be negative, but `-0.1` is given.

    >>> variabilitycheck(maxrelsumdelta=0.1, averagingwindow=0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `variabilitycheck` of element `?`, `averagingwindow` \
must be a positive integer, but `0` is given.

    Failed calls leave the previous configuration untouched:

    >>> variabilitycheck
    variabilitycheck(maxrelsumdelta=0.1, averagingwindow=12)
    """

    _config: tuple[bool, float, int] | None

    def __init__(self, subvars: variabletools.SubVariables[Any, Any, Any, Any]) -> None:
        super().__init__(subvars)
        self._config = None

    def __call__(
        self,
        value: bool | None = None,
        *,
        maxrelsumdelta: float | None = None,
        averagingwindow: int | None = None,
    ) -> None:
        if (value is False) and (
            (maxrelsumdelta is not None) or (averagingwindow is not None)
        ):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, `maxrelsumdelta` "
                f"and `averagingwindow` must not be given when disabling the "
                f"variability check."
            )
        if value is False:
            self._config = (False, 0.0, 0)
            return
        if (value is None) and (maxrelsumdelta is None) and (averagingwindow is None):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, pass either a "
                f"boolean value or the keyword arguments `maxrelsumdelta` and "
                f"`averagingwindow`."
            )
        if (maxrelsumdelta is None) or (averagingwindow is None):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, both "
                f"`maxrelsumdelta` and `averagingwindow` must be given when enabling "
                f"the variability check."
            )
        if maxrelsumdelta < 0.0:
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, `maxrelsumdelta` "
                f"must not be negative, but `{maxrelsumdelta}` is given."
            )
        if (int(averagingwindow) != averagingwindow) or (averagingwindow < 1):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, `averagingwindow` "
                f"must be a positive integer, but `{averagingwindow}` is given."
            )
        self._config = (True, float(maxrelsumdelta), int(averagingwindow))

    def __repr__(self) -> str:
        if self._config is None:
            return f"{self.name}(?)"
        enabled, maxrelsumdelta, averagingwindow = self._config
        if not enabled:
            return f"{self.name}(False)"
        return (
            f"{self.name}(maxrelsumdelta={objecttools.repr_(maxrelsumdelta)}, "
            f"averagingwindow={averagingwindow})"
        )

    def verify(self) -> None:
        """Raise a |RuntimeError| if the configuration is still unknown."""
        if self._config is None:
            raise RuntimeError(
                f"For parameter {objecttools.elementphrase(self)}, it is still unknown "
                f"whether the variability check is enabled."
            )

    @property
    def configured(self) -> bool:
        """Flag indicating whether the variability check has already been
        configured.

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> variabilitycheck.configured
        False
        >>> variabilitycheck(False)
        >>> variabilitycheck.configured
        True
        """
        return self._config is not None

    def _get_config(self) -> tuple[bool, float, int]:
        self.verify()
        assert self._config is not None
        return self._config

    @property
    def enabled(self) -> bool:
        """Flag indicating whether the variability check is enabled."""
        return self._get_config()[0]

    @property
    def maxrelsumdelta(self) -> float:
        """The threshold for the relative sum of the absolute changes of the
        simulated values (zero if the check is disabled)."""
        return self._get_config()[1]

    @property
    def averagingwindow(self) -> int:
        """The length of the averaging period under stationary conditions in log
        entries (zero if the check is disabled)."""
        return self._get_config()[2]


class ReductionSteps(parametertools.Parameter):
    """Number of timesteps for linearly reducing the ARIMA correction to zero once
    the stationarity check (see |StationarityCheck|) detects instationary
    conditions [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class MaxAbsShift(parametertools.Parameter):
    """The maximum absolute shift applied when the current forecast value
    exceeds the simulated value at the point the residual was determined (see
    |Determine_OutputCorrection_V1|) [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class MaxRelShift(parametertools.Parameter):
    """The maximum relative shift (in %) applied when the current forecast value
    is at or below the simulated value at the point the residual was
    determined (see |Determine_OutputCorrection_V1|)."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class AveragingWindow(parametertools.Parameter):
    """The length (in log entries) of the averaging period immediately
    preceding the current forecast run, used to determine the mean-value-based
    ARIMA residual (see |Determine_OutputCorrection_V1|).  Set to zero to
    disable mean-value-based correction and rely on the single most recent
    (pointwise) residual only, as |Determine_OutputCorrection_V1| already did
    before |AveragingWindow| and |TransitionSteps| were
    introduced."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class TransitionSteps(parametertools.Parameter):
    """The number of forecast steps over which the applied residual
    transitions linearly from the single most recent (pointwise) residual to
    the mean-value-based residual determined via |AveragingWindow|,
    avoiding an abrupt jump right at the start of the forecast horizon."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class Propagate(parametertools.Parameter):
    """Flag determining whether the corrected discharge is passed on to the
    downstream network (|True|) or calculated only for local output at the
    current gauge, while the uncorrected inflow is passed on instead
    (|False|)."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
