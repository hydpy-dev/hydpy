# pylint: disable=missing-module-docstring

from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *


class NmbSubmodels(parametertools.NmbParameter):
    """The number of output correction submodels [-].

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> nmbsubmodels(3)
    >>> model.outputcorrmodels.number
    3
    """

    SPAN = (0, None)

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.outputcorrmodels.number = self.value


class EvaluationWindow(parametertools.Parameter):
    """The number of time steps the submodels use for evaluating parameters
    based on logged values [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)


class MaxNaNSkip(parametertools.Parameter):
    """The maximum number of log entries with NaN values to skip
    when evaluating logged parameters [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class Active(parametertools.Parameter):
    """Flag determining whether the submodel may correct the simulated values at
    all [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool


class CorrectionMode(parametertools.Parameter):
    """The simulation mode(s) in which the submodel may correct the simulated
    values [-].

    Pass one of the options `historical`, `forecast`, or `both` (corresponding to
    the possible values of |Options.simulationmode|) via the keyword argument
    `option`.  Internally, |CorrectionMode| stores them as the integer values 1, 2,
    and 3:

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> correctionmode
    correctionmode(?)
    >>> correctionmode(option="historical")
    >>> correctionmode
    correctionmode(option="historical")
    >>> correctionmode.value
    1
    >>> correctionmode(option="forecast")
    >>> correctionmode.value
    2
    >>> correctionmode(option="both")
    >>> correctionmode.value
    3

    Other options are not allowed:

    >>> correctionmode(option="always")
    Traceback (most recent call last):
    ...
    ValueError: Parameter `correctionmode` of element `?` supports the options \
`historical`, `forecast`, and `both`, but `always` is given.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, 3)

    def _set_option(self, *, option: str) -> dict[str, str]:
        if option == "historical":
            self.values = 1
        elif option == "forecast":
            self.values = 2
        elif option == "both":
            self.values = 3
        else:
            raise ValueError(
                f"Parameter {objecttools.elementphrase(self)} supports the options "
                f"`historical`, `forecast`, and `both`, but `{option}` is given."
            )
        return {"option": option}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("option", type_=str), setter=_set_option
        )
    )


class LowerLimit(parametertools.Parameter):
    """Lower (inclusive) limit of the submodel's range of responsibility
    [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (None, None)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim upper values in accordance with :math:`LowerLimit \leq UpperLimit`.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> lowerlimit(3.0)
        >>> lowerlimit
        lowerlimit(3.0)
        >>> upperlimit.value = 2.0
        >>> lowerlimit(1.0)
        >>> lowerlimit
        lowerlimit(1.0)
        >>> lowerlimit(3.0)
        >>> lowerlimit
        lowerlimit(2.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.upperlimit, "value", None)
        return super().trim(lower, upper)


class UpperLimit(parametertools.Parameter):
    """Upper (exclusive) limit of the submodel's range of responsibility
    [unit of the corrected variable].

    Set it to |numpy.inf| to define a range without an upper limit."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (None, None)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim lower values in accordance with :math:`LowerLimit \leq UpperLimit`.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> upperlimit(1.0)
        >>> upperlimit
        upperlimit(1.0)
        >>> upperlimit(3.0)
        >>> lowerlimit.value = 2.0
        >>> upperlimit
        upperlimit(3.0)
        >>> upperlimit(1.0)
        >>> upperlimit
        upperlimit(2.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.lowerlimit, "value", None)
        return super().trim(lower, upper)


class StationarityCheck(parametertools.SpecialParameter):
    """Configuration of the check of whether the observed values behave in a
    stationary way, optionally combined with the check of whether the simulated
    values vary little enough to base the correction on a long-term mean residual
    [-].

    Either switch the check off by passing `active=False` or switch it on by passing
    `active=True` together with the length of the assessment period (`window`, in log
    entries) and the threshold for the ratio of the minimum and the maximum observed
    values within this period (`ratiominmax`):

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> stationaritycheck
    stationaritycheck(?)
    >>> stationaritycheck.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: For parameter `stationaritycheck` of element `?`, no configuration \
has been defined so far.  Please pass either `active=False` or `active=True` \
together with the required keyword arguments.

    >>> stationaritycheck(active=False)
    >>> stationaritycheck
    stationaritycheck(active=False)
    >>> stationaritycheck.verify()
    >>> stationaritycheck(active=True, window=10, ratiominmax=0.5)
    >>> stationaritycheck
    stationaritycheck(active=True, window=10, ratiominmax=0.5)
    >>> stationaritycheck.enabled, stationaritycheck.window
    (True, 10)
    >>> from hydpy import round_
    >>> round_(stationaritycheck.ratiominmax)
    0.5

    Optionally, a variability check may switched on by additionally passing the
    threshold for the relative sum of the absolute changes of the simulated values
    (`maxrelsumdelta`) and the length of the averaging period (`averagingwindow`, in
    log entries):

    >>> stationaritycheck.variabilitycheck
    False
    >>> stationaritycheck(
    ...     active=True, window=10, ratiominmax=0.5, maxrelsumdelta=0.2,
    ...     averagingwindow=24
    ... )
    >>> stationaritycheck
    stationaritycheck(active=True, window=10, ratiominmax=0.5, maxrelsumdelta=0.2, \
averagingwindow=24)
    >>> stationaritycheck.variabilitycheck, stationaritycheck.averagingwindow
    (True, 24)
    >>> round_(stationaritycheck.maxrelsumdelta)
    0.2

    `active` is always required:

    >>> stationaritycheck(window=5, ratiominmax=0.8)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, the keyword \
argument `active` must be given.

    An enabled check requires both `window` and `ratiominmax`:

    >>> stationaritycheck(active=True, window=5)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, both `window` and \
`ratiominmax` must be given when enabling the stationarity check.

    The variability check requires both `maxrelsumdelta` and `averagingwindow`:

    >>> stationaritycheck(active=True, window=5, ratiominmax=0.8, maxrelsumdelta=0.1)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, either both or \
none of `maxrelsumdelta` and `averagingwindow` must be given.

    A disabled check does not accept any further keyword arguments:

    >>> stationaritycheck(active=False, window=5, ratiominmax=0.8)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, no further \
keyword arguments must be given when disabling the stationarity check.

    >>> stationaritycheck(active=False, maxrelsumdelta=0.1, averagingwindow=12)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, no further \
keyword arguments must be given when disabling the stationarity check.

    `window` and `averagingwindow` must be positive integers, `ratiominmax` must lie
    between zero and one, and `maxrelsumdelta` must not be negative:

    >>> stationaritycheck(active=True, window=0, ratiominmax=0.8)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `window` must be a \
positive integer, but `0` is given.

    >>> stationaritycheck(active=True, window=5, ratiominmax=1.5)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `ratiominmax` must \
lie between zero and one, but `1.5` is given.

    >>> stationaritycheck(
    ...     active=True, window=5, ratiominmax=0.8, maxrelsumdelta=-0.1,
    ...     averagingwindow=12
    ... )
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `maxrelsumdelta` \
must not be negative, but `-0.1` is given.

    >>> stationaritycheck(
    ...     active=True, window=5, ratiominmax=0.8, maxrelsumdelta=0.1,
    ...     averagingwindow=0
    ... )
    Traceback (most recent call last):
    ...
    ValueError: For parameter `stationaritycheck` of element `?`, `averagingwindow` \
must be a positive integer, but `0` is given.

    Failed calls leave the previous configuration untouched:

    >>> stationaritycheck
    stationaritycheck(active=True, window=10, ratiominmax=0.5, maxrelsumdelta=0.2, \
averagingwindow=24)
    """

    _config: tuple[bool, int, float, float, int] | None

    def __init__(self, subvars: variabletools.SubVariables[Any, Any, Any, Any]) -> None:
        super().__init__(subvars)
        self._config = None

    @overload
    def __call__(self, *, active: Literal[False]) -> None: ...

    @overload
    def __call__(
        self, *, active: Literal[True], window: int, ratiominmax: float
    ) -> None: ...

    @overload
    def __call__(
        self,
        *,
        active: Literal[True],
        window: int,
        ratiominmax: float,
        maxrelsumdelta: float,
        averagingwindow: int,
    ) -> None: ...

    def __call__(
        self,
        *,
        active: bool | None = None,
        window: int | None = None,
        ratiominmax: float | None = None,
        maxrelsumdelta: float | None = None,
        averagingwindow: int | None = None,
    ) -> None:
        if active is None:
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, the keyword "
                f"argument `active` must be given."
            )
        others = (window, ratiominmax, maxrelsumdelta, averagingwindow)
        if not active:
            if any(other is not None for other in others):
                raise ValueError(
                    f"For parameter {objecttools.elementphrase(self)}, no further "
                    f"keyword arguments must be given when disabling the "
                    f"stationarity check."
                )
            self._config = (False, 0, 0.0, 0.0, 0)
            return
        if (window is None) or (ratiominmax is None):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, both `window` and "
                f"`ratiominmax` must be given when enabling the stationarity check."
            )
        if (maxrelsumdelta is None) != (averagingwindow is None):
            raise ValueError(
                f"For parameter {objecttools.elementphrase(self)}, either both or "
                f"none of `maxrelsumdelta` and `averagingwindow` must be given."
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
        if (maxrelsumdelta is None) or (averagingwindow is None):
            self._config = (True, int(window), float(ratiominmax), 0.0, 0)
            return
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
        self._config = (
            True,
            int(window),
            float(ratiominmax),
            float(maxrelsumdelta),
            int(averagingwindow),
        )

    def __repr__(self) -> str:
        if self._config is None:
            return f"{self.name}(?)"
        enabled, window, ratiominmax, maxrelsumdelta, averagingwindow = self._config
        if not enabled:
            return f"{self.name}(active=False)"
        string = (
            f"{self.name}(active=True, window={window}, "
            f"ratiominmax={objecttools.repr_(ratiominmax)}"
        )
        if averagingwindow > 0:
            string = (
                f"{string}, maxrelsumdelta={objecttools.repr_(maxrelsumdelta)}, "
                f"averagingwindow={averagingwindow}"
            )
        return f"{string})"

    def verify(self) -> None:
        """Raise a |RuntimeError| if no configuration has been defined so far."""
        if self._config is None:
            raise RuntimeError(
                f"For parameter {objecttools.elementphrase(self)}, no configuration "
                f"has been defined so far.  Please pass either `active=False` or "
                f"`active=True` together with the required keyword arguments."
            )

    @property
    def configured(self) -> bool:
        """Flag indicating whether the stationarity check has already been
        configured.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> stationaritycheck.configured
        False
        >>> stationaritycheck(active=False)
        >>> stationaritycheck.configured
        True
        """
        return self._config is not None

    def _get_config(self) -> tuple[bool, int, float, float, int]:
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

    @property
    def variabilitycheck(self) -> bool:
        """Flag indicating whether the variability check is enabled."""
        return self._get_config()[4] > 0

    @property
    def maxrelsumdelta(self) -> float:
        """The threshold for the sum of the absolute changes of the simulated values
        per time step divided by their mean."""
        return self._get_config()[3]

    @property
    def averagingwindow(self) -> int:
        """The length of the averaging period (number of log entries) for
        determining the mean-value-based residual under low variability conditions
        (zero if the variability check is disabled)."""
        return self._get_config()[4]


class ReductionSteps(parametertools.Parameter):
    """Number of forecast steps for linearly reducing the correction to zero [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class MaxAbsShift(parametertools.Parameter):
    """The maximum absolute shift applied [unit of the corrected variable]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class MaxRelShift(parametertools.Parameter):
    """The maximum relative shift applied [-].

    |MaxRelShift| is a fraction, not a percentage as in LARSIM (compare
    https://larsim.info/larsimhilfe/html/LARSIM-Einzelparameter/LARSIM_Einzelparameter_065_MAX-ARIMA-NQ_[proz].htm)
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class AveragingWindow(parametertools.Parameter):
    """The length (in log entries) of the averaging period immediately
    preceding the current time step, used to determine the mean-value-based
    residual [-].

    Set to zero to disable mean-value-based correction and rely on the single most
    recent (pointwise) residual only.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class TransitionSteps(parametertools.Parameter):
    """The number of forecast steps over which the applied residual transitions
    linearly from the single most recent (pointwise) residual to the mean-value-based
    residual [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class Propagate(parametertools.Parameter):
    """Flag determining whether the corrected value is passed on to the
    downstream network (|True|) or calculated only for local output at the
    current gauge, while the original value is passed on instead
    (|False|) [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
