# -*- coding: utf-8 -*-
"""This module implements statistical functionalities frequently used in
hydrological modelling."""
# import...
# ...from standard library
import warnings
from typing import *
from typing import TextIO
from typing_extensions import Literal  # type: ignore[misc]
from typing_extensions import Protocol  # type: ignore[misc]

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.auxs import validtools
from hydpy.core import seriestools
from hydpy.core import timetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    import pandas
    from scipy import optimize
    from scipy import special
else:
    pandas = exceptiontools.OptionalImport("pandas", ["pandas"], locals())
    optimize = exceptiontools.OptionalImport("optimize", ["scipy.optimize"], locals())
    special = exceptiontools.OptionalImport("special", ["scipy.special"], locals())


class SimObs(NamedTuple):
    """A named tuple containing one array of simulated and one array of
    observed values."""

    sim: Vector[float]
    obs: Vector[float]


@overload
def filter_series(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    date_ranges: Iterable[Tuple[timetools.DateConstrArg, timetools.DateConstrArg]],
) -> SimObs:
    """sim and obs and date_ranges as arguments"""


@overload
def filter_series(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    months: Iterable[int],
) -> SimObs:
    """sim and obs and month as arguments"""


@overload
def filter_series(
    *,
    node: devicetools.Node,
    date_ranges: Iterable[Tuple[timetools.DateConstrArg, timetools.DateConstrArg]],
) -> SimObs:
    """node and date_ranges as arguments"""


@overload
def filter_series(
    *,
    node: devicetools.Node,
    months: Iterable[int],
) -> SimObs:
    """node and month as arguments"""


@objecttools.excmessage_decorator("filter the given series")
def filter_series(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    date_ranges: Optional[
        Iterable[Tuple[timetools.DateConstrArg, timetools.DateConstrArg]]
    ] = None,
    months: Optional[Iterable[int]] = None,
) -> SimObs:
    """Filter time series for the given date ranges or months.

    Often, we want to apply objective functions like |nse| on a subset
    of the available simulated and observed values.  The function
    |filter_series| helps to extract the relevant data either by data ranges
    or by months.  Common examples are to pass a single date range to ignore
    the first non-optimal values of a warm-up period, to pass a set of
    date ranges to focus on certain events or to pass a set of months
    to perform a seasonal analysis.

    To show how |filter_series| works, we prepare a daily initialisation
    time grid spanning two hydrological years:

    >>> from hydpy import filter_series, pub, Node
    >>> pub.timegrids = "2001-11-01", "2003-11-01", "1d"

    Next, we prepare a |Node| object and assign some constantly increasing
    and decreasing values to its `simulation` and the `observation` series,
    respectively:

    >>> import numpy
    >>> node = Node("test")
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(1, 2*365+1)
    >>> node.sequences.obs.series = numpy.arange(2*365, 0, -1)

    First, we select data of arbitrary sub-periods via the `data_ranges`
    argument.  Each data range consists of the start-point and the end-point
    of a sub-period. Here, we choose all values that belong to 31 October
    or 1 November (note that unsorted data ranges are acceptable):

    >>> date_ranges = [("2001-11-01", "2001-11-02"),
    ...                ("2002-10-31", "2002-11-02"),
    ...                ("2003-10-31", "2003-11-01")]
    >>> results = filter_series(node=node, date_ranges=date_ranges)

    |filter_series| returns the data within index-sorted |pandas.Series|
    objects (note that the index addresses the left boundary of each
    time step):

    >>> results.sim   # doctest: +ELLIPSIS
    2001-11-01      1.0
    2002-10-31    365.0
    2002-11-01    366.0
    2003-10-31    730.0
    Name: sim...
    >>> results.obs   # doctest: +ELLIPSIS
    2001-11-01    730.0
    2002-10-31    366.0
    2002-11-01    365.0
    2003-10-31      1.0
    Name: obs...

    To help avoiding possible hard-to-find errors, |filter_series| performs
    the following checks:

    >>> date_ranges = [("2001-10-31", "2003-11-01")]
    >>> filter_series(node=node, date_ranges=date_ranges)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: The given date (2001-10-31 00:00:00) is before the first date of \
the initialisation period (2001-11-01 00:00:00).

    >>> date_ranges = [("2001-11-01", "2003-11-02")]
    >>> filter_series(node=node, date_ranges=date_ranges)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: The given date (2003-11-02 00:00:00) is behind the last date of \
the initialisation period (2003-11-01 00:00:00).

    >>> date_ranges = [("2001-11-02", "2001-11-02")]
    >>> filter_series(node=node, date_ranges=date_ranges)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: The given first date `2001-11-02 00:00:00` is not before than the \
given last date `2001-11-02 00:00:00`.

    Note that function |filter_series| does not remove any duplicates:

    >>> date_ranges = [("2001-11-01", "2001-11-05"),
    ...                ("2001-11-01", "2001-11-02"),
    ...                ("2001-11-04", "2001-11-06")]
    >>> sim = filter_series(node=node, date_ranges=date_ranges).sim
    >>> sim   # doctest: +ELLIPSIS
    2001-11-01    1.0
    2001-11-01    1.0
    2001-11-02    2.0
    2001-11-03    3.0
    2001-11-04    4.0
    2001-11-04    4.0
    2001-11-05    5.0
    Name: sim...

    Instead of date ranges, one can specify months via integer numbers.
    We begin with selecting October (10) and November (11) individually:

    >>> sim = filter_series(node=node, months=[11]).sim
    >>> len(sim)
    60
    >>> sim   # doctest: +ELLIPSIS
    2001-11-01      1.0
    2001-11-02      2.0
    ...
    2002-11-29    394.0
    2002-11-30    395.0
    Name: sim...

    >>> sim = filter_series(node=node, months=[10]).sim
    >>> len(sim)
    62
    >>> sim   # doctest: +ELLIPSIS
    2002-10-01    335.0
    2002-10-02    336.0
    ...
    2003-10-30    729.0
    2003-10-31    730.0
    Name: sim...

    One can select multiple months, which neither need to be sorted nor
    consecutive:

    >>> sim = filter_series(node=node, months=[4, 1]).sim
    >>> len(sim)
    122
    >>> sim   # doctest: +ELLIPSIS
    2002-01-01     62.0
    2002-01-02     63.0
    ...
    2003-04-29    545.0
    2003-04-30    546.0
    Name: sim...

    Note that you are also free to either pass the `sim` and `obs` series
    directly instead of a `node` (see function |prepare_arrays| for further
    information):

    >>> xs = node.sequences.sim.series
    >>> ys = node.sequences.obs.series
    >>> filter_series(sim=xs, obs=ys, months=[4, 1]).sim   # doctest: +ELLIPSIS
    2002-01-01     62.0
    2002-01-02     63.0
    ...
    2003-04-29    545.0
    2003-04-30    546.0
    Name: sim...

    Missing or double information for arguments `date_ranges` and `months`
    results in the following error messages:

    >>> filter_series(node=node)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: You need to define either the `date_ranges` or `months` argument, \
but none of them is given.

    >>> filter_series(node=node, date_ranges=[], months=[])
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: You need to define either the `date_ranges` or `months` argument, \
but both of them are given.
    """
    dataframe = pandas.DataFrame()
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=False,
        subperiod=False,
    )
    del sim, obs
    dataframe["sim"] = sim_
    dataframe["obs"] = obs_
    tg = hydpy.pub.timegrids.init
    dataframe.index = pandas.date_range(
        start=tg.firstdate.datetime,
        end=tg.lastdate.datetime - tg.stepsize.timedelta,
        freq=tg.stepsize.timedelta,
    )
    dataframe_selected = pandas.DataFrame()
    if (date_ranges is not None) and (months is None):
        for date_range in date_ranges:
            date0 = tg[tg[date_range[0]]]
            date1 = tg[tg[date_range[1]]]
            if date0 < tg.firstdate:
                raise ValueError(
                    f"The given date ({date0}) is before the first date "
                    f"of the initialisation period ({tg.firstdate})."
                )
            if date1 > tg.lastdate:
                raise ValueError(
                    f"The given date ({date1}) is behind the last date "
                    f"of the initialisation period ({tg.lastdate})."
                )
            if date0 >= date1:
                raise ValueError(
                    f"The given first date `{date0}` is not before than "
                    f"the given last date `{date1}`."
                )
            idx0 = date0.to_string(style="iso1")
            idx1 = (date1 - tg.stepsize).to_string(style="iso1")
            selected_dates = dataframe.loc[idx0:idx1]  # type: ignore[misc]
            dataframe_selected = pandas.concat(
                [selected_dates, dataframe_selected],
            )
    elif (date_ranges is None) and (months is not None):
        for month in months:
            selected_dates = dataframe.loc[dataframe.index.month == int(month)]
            dataframe_selected = pandas.concat(
                [selected_dates, dataframe_selected],
            )
    elif (date_ranges is None) and (months is None):
        raise ValueError(
            "You need to define either the `date_ranges` or `months` "
            "argument, but none of them is given."
        )
    else:
        raise ValueError(
            "You need to define either the `date_ranges` or `months` "
            "argument, but both of them are given."
        )
    dataframe_selected = dataframe_selected.sort_index()
    return SimObs(
        sim=dataframe_selected["sim"],
        obs=dataframe_selected["obs"],
    )


def prepare_arrays(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> SimObs:
    """Prepare and return two |numpy| arrays based on the given arguments.

    Note that many functions provided by module |statstools| apply function
    |prepare_arrays| internally (e.g. |nse|).  But you can also use it
    manually, as shown in the following examples.

    Function |prepare_arrays| can extract time-series data from |Node|
    objects.  To set up an example for this, we define an initialisation
    period and prepare a |Node| object:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = "01.01.2000", "07.01.2000", "1d"
    >>> node = Node("test")

    Next, we assign some values to the `simulation` and the `observation`
    sequences of the node:

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, nan, nan, nan, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 4.0, 5.0, nan, nan, nan, 6.0

    Now we can pass the node object to function |prepare_arrays| and
    get the (unmodified) time-series data:

    >>> from hydpy import prepare_arrays
    >>> arrays = prepare_arrays(node=node)
    >>> round_(arrays.sim)
    1.0, nan, nan, nan, 2.0, 3.0
    >>> round_(arrays.obs)
    4.0, 5.0, nan, nan, nan, 6.0

    Alternatively, we can pass directly any iterable (e.g. |list| and
    |tuple| objects) containing the `simulated` and `observed` data:

    >>> arrays = prepare_arrays(sim=list(node.sequences.sim.series),
    ...                         obs=tuple(node.sequences.obs.series))
    >>> round_(arrays.sim)
    1.0, nan, nan, nan, 2.0, 3.0
    >>> round_(arrays.obs)
    4.0, 5.0, nan, nan, nan, 6.0

    The optional `skip_nan` flag allows skipping all values, which are
    no numbers.  Note that |prepare_arrays| returns only those pairs of
    `simulated` and `observed` values which do not contain any `nan` value:

    >>> arrays = prepare_arrays(node=node, skip_nan=True)
    >>> round_(arrays.sim)
    1.0, 3.0
    >>> round_(arrays.obs)
    4.0, 6.0

    If you are interested in analysing a sub-period, adapt the global
    |Timegrids.eval_| |Timegrid| beforehand.  When passing a |Node|
    object, function |prepare_arrays| then returns the data of the
    current evaluation sub-period only:

    >>> pub.timegrids.eval_.dates = "02.01.2000", "06.01.2000"
    >>> arrays = prepare_arrays(node=node)
    >>> round_(arrays.sim)
    nan, nan, nan, 2.0
    >>> round_(arrays.obs)
    5.0, nan, nan, nan

    Suppose one instead passes the simulation and observation time-series
    directly (which possibly fit the evaluation period already).  In that
    case, function |prepare_arrays| ignores the current |Timegrids.eval_|
    |Timegrid| by default:

    >>> arrays = prepare_arrays(sim=arrays.sim, obs=arrays.obs)
    >>> round_(arrays.sim)
    nan, nan, nan, 2.0
    >>> round_(arrays.obs)
    5.0, nan, nan, nan

    Use the `subperiod` argument to deviate from the default behaviour:

    >>> arrays = prepare_arrays(node=node, subperiod=False)
    >>> round_(arrays.sim)
    1.0, nan, nan, nan, 2.0, 3.0
    >>> round_(arrays.obs)
    4.0, 5.0, nan, nan, nan, 6.0

    >>> arrays = prepare_arrays(sim=arrays.sim, obs=arrays.obs, subperiod=True)
    >>> round_(arrays.sim)
    nan, nan, nan, 2.0
    >>> round_(arrays.obs)
    5.0, nan, nan, nan

    The final examples show the error messages returned in case of
    invalid combinations of input arguments:

    >>> prepare_arrays()
    Traceback (most recent call last):
    ...
    ValueError: Neither a `Node` object is passed to argument `node` nor \
are arrays passed to arguments `sim` and `obs`.

    >>> prepare_arrays(sim=node.sequences.sim.series, node=node)
    Traceback (most recent call last):
    ...
    ValueError: Values are passed to both arguments `sim` and `node`, \
which is not allowed.

    >>> prepare_arrays(obs=node.sequences.obs.series, node=node)
    Traceback (most recent call last):
    ...
    ValueError: Values are passed to both arguments `obs` and `node`, \
which is not allowed.

    >>> prepare_arrays(sim=node.sequences.sim.series)
    Traceback (most recent call last):
    ...
    ValueError: A value is passed to argument `sim` but \
no value is passed to argument `obs`.

    >>> prepare_arrays(obs=node.sequences.obs.series)
    Traceback (most recent call last):
    ...
    ValueError: A value is passed to argument `obs` but \
no value is passed to argument `sim`.
    """
    if node is not None:
        if sim is not None:
            raise ValueError(
                "Values are passed to both arguments `sim` and `node`, "
                "which is not allowed."
            )
        if obs is not None:
            raise ValueError(
                "Values are passed to both arguments `obs` and `node`, "
                "which is not allowed."
            )
        sim = node.sequences.sim.series
        obs = node.sequences.obs.series
    elif (sim is not None) and (obs is None):
        raise ValueError(
            "A value is passed to argument `sim` "
            "but no value is passed to argument `obs`."
        )
    elif (obs is not None) and (sim is None):
        raise ValueError(
            "A value is passed to argument `obs` "
            "but no value is passed to argument `sim`."
        )
    elif (sim is None) and (obs is None):
        raise ValueError(
            "Neither a `Node` object is passed to argument `node` nor "
            "are arrays passed to arguments `sim` and `obs`."
        )
    sim_ = numpy.asarray(sim)
    obs_ = numpy.asarray(obs)
    if subperiod or ((subperiod is None) and (node is not None)):
        idx0, idx1 = hydpy.pub.timegrids.evalindices
        sim_ = sim_[idx0:idx1]
        obs_ = obs_[idx0:idx1]
    if skip_nan:
        idxs = ~numpy.isnan(sim_) * ~numpy.isnan(obs_)
        sim_ = sim_[idxs]
        obs_ = obs_[idxs]
    return SimObs(
        sim=sim_,
        obs=obs_,
    )


class Criterion(Protocol):
    """Callback protocol for efficiency criteria like |nse|."""

    __name__: str

    @overload
    def __call__(
        self,
        *,
        sim: VectorInput[float],
        obs: VectorInput[float],
        skip_nan: bool = False,
        subperiod: bool = False,
    ) -> float:
        ...

    @overload
    def __call__(
        self,
        *,
        node: devicetools.Node,
        skip_nan: bool = False,
        subperiod: bool = True,
    ) -> float:
        ...


@overload
def rmse(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def rmse(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the root-mean-square error")
def rmse(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the root-mean-square error.

    >>> from hydpy import rmse, round_
    >>> rmse(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    0.0
    >>> round_(rmse(sim=[1.0, 2.0, 3.0], obs=[0.5, 2.0, 4.5]))
    0.912871

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |rmse|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return cast(float, numpy.sqrt(numpy.mean((sim_ - obs_) ** 2)))


@overload
def nse(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def nse(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the Nash-Sutcliffe efficiency")
def nse(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the efficiency criteria after Nash & Sutcliffe.

    If the simulated values predict the observed values as well as the
    average observed value (regarding the mean square error), the NSE
    value is zero:

    >>> from hydpy import nse
    >>> nse(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0])
    0.0
    >>> nse(sim=[0.0, 2.0, 4.0], obs=[1.0, 2.0, 3.0])
    0.0

    For worse and better agreement, the NSE is negative or positive,
    respectively:

    >>> nse(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0])
    -3.0
    >>> nse(sim=[1.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0])
    0.5

    The highest possible value is one:

    >>> nse(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |nse|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return cast(
        float,
        1.0 - numpy.sum((sim_ - obs_) ** 2) / numpy.sum((obs_ - numpy.mean(obs_)) ** 2),
    )


@overload
def nse_log(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def nse_log(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the log-Nash-Sutcliffe efficiency")
def nse_log(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the efficiency criteria after Nash & Sutcliffe for
    logarithmic values.

    The following calculations repeat the ones of the documentation
    on function |nse| but with exponentiated values.  Hence, the
    results are similar or, as in the first and the last example,
    even identical:

    >>> from hydpy import nse_log, round_
    >>> from numpy import exp
    >>> nse_log(sim=exp([2.0, 2.0, 2.0]), obs=exp([1.0, 2.0, 3.0]))
    0.0
    >>> nse_log(sim=exp([0.0, 2.0, 4.0]), obs=exp([1.0, 2.0, 3.0]))
    0.0

    >>> round_(nse(sim=exp([3.0, 2.0, 1.0]), obs=exp([1.0, 2.0, 3.0])))
    -2.734185
    >>> round_(nse(sim=exp([1.0, 2.0, 2.0]), obs=exp([1.0, 2.0, 3.0])))
    0.002139

    >>> nse(sim=exp([1.0, 2.0, 3.0]), obs=exp([1.0, 2.0, 3.0]))
    1.0

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |nse_log|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return cast(
        float,
        1.0
        - numpy.sum((numpy.log(sim_) - numpy.log(obs_)) ** 2)
        / numpy.sum((numpy.log(obs_) - numpy.mean(numpy.log(obs_))) ** 2),
    )


@overload
def corr2(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def corr2(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the R²-Error")
def corr2(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the coefficient of determination via the square of the
    coefficient of correlation according to Bravais-Pearson.

    For perfect positive or negative correlation, |corr2| returns 1:

    >>> from hydpy import corr2, round_
    >>> corr2(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0
    >>> corr2(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0])
    1.0

    If there is no correlation at all, |corr2| returns 0:

    >>> corr2(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 1.0])
    0.0

    An intermediate example:

    >>> round_(corr2(sim=[2.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    0.75

    Take care if there is no variation in one of the data series.  Then the
    correlation coefficient is not defined, and |corr2| returns |numpy.nan|:

    >>> corr2(sim=[2.0, 2.0, 2.0], obs=[2.0, 2.0, 3.0])
    nan

    See the documentation on function |prepare_arrays| for some additional
    instructions for using |corr2|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    if (numpy.std(sim_) == 0.0) or (numpy.std(obs_) == 0.0):
        return cast(float, numpy.nan)
    return cast(float, numpy.corrcoef(sim_, obs_)[0, 1] ** 2)


@overload
def kge(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def kge(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the Kling-Gupta-Efficiency")
def kge(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the Kling-Gupta efficiency :cite:`ref-Kling2012`.

    >>> from hydpy import  kge, round_
    >>> kge(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0
    >>> kge(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0])
    -3.0
    >>> round_(kge(sim=[2.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -2.688461

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |kge|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return cast(
        float,
        1.0
        - numpy.sum(
            (numpy.corrcoef(sim_, obs_)[0, 1] - 1) ** 2
            + (numpy.std(sim_) / numpy.std(obs_) - 1) ** 2
            + (numpy.mean(sim_) / numpy.mean(obs_) - 1) ** 2
        ),
    )


@overload
def bias_abs(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def bias_abs(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the absolute bias")
def bias_abs(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the absolute difference between the means of the simulated
    and the observed values.

    >>> from hydpy import bias_abs, round_
    >>> round_(bias_abs(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.0
    >>> round_(bias_abs(sim=[5.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    1.0
    >>> round_(bias_abs(sim=[1.0, 1.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -1.0

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |bias_abs|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    # noinspection PyTypeChecker
    return cast(float, numpy.mean(sim_ - obs_))


@overload
def bias_rel(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def bias_rel(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the relative bias")
def bias_rel(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the relative difference between the means of the simulated
    and the observed values.

    >>> from hydpy import bias_rel, round_
    >>> round_(bias_rel(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.0
    >>> round_(bias_rel(sim=[5.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.5
    >>> round_(bias_rel(sim=[1.0, 1.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -0.5

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |bias_rel|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return cast(float, numpy.mean(sim_) / numpy.mean(obs_) - 1.0)


@overload
def std_ratio(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def std_ratio(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the standard deviation ratio")
def std_ratio(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the ratio between the standard deviation of the simulated
    and the observed values.

    >>> from hydpy import round_, std_ratio
    >>> round_(std_ratio(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0]))
    0.0
    >>> round_(std_ratio(sim=[1.0, 1.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -1.0
    >>> round_(std_ratio(sim=[0.0, 3.0, 6.0], obs=[1.0, 2.0, 3.0]))
    2.0

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |std_ratio|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return cast(float, numpy.std(sim_) / numpy.std(obs_) - 1.0)


@overload
def corr(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def corr(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the Pearson correlation coefficient")
def corr(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the product-moment correlation coefficient after Pearson.

    >>> from hydpy import corr, round_
    >>> round_(corr(sim=[0.5, 1.0, 1.5], obs=[1.0, 2.0, 3.0]))
    1.0
    >>> round_(corr(sim=[4.0, 2.0, 0.0], obs=[1.0, 2.0, 3.0]))
    -1.0
    >>> round_(corr(sim=[1.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    0.0

    Take care if there is no variation in one of the data series.  Then
    the correlation coefficient is not defined, and |corr| returns |numpy.nan|:

    >>> round_(corr(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    nan

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |corr|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    if (numpy.std(sim_) == 0.0) or (numpy.std(obs_) == 0.0):
        return cast(float, numpy.nan)
    return cast(float, numpy.corrcoef(sim_, obs_)[0, 1])


def _pars_sepd(xi: float, beta: float) -> Tuple[float, float, float, float]:
    gamma1 = special.gamma(3.0 * (1.0 + beta) / 2.0)
    gamma2 = special.gamma((1.0 + beta) / 2.0)
    w_beta = gamma1 ** 0.5 / (1.0 + beta) / gamma2 ** 1.5
    c_beta = (gamma1 / gamma2) ** (1.0 / (1.0 + beta))
    m_1 = special.gamma(1.0 + beta) / gamma1 ** 0.5 / gamma2 ** 0.5
    m_2 = 1.0
    mu_xi = m_1 * (xi - 1.0 / xi)
    sigma_xi = numpy.sqrt(
        (m_2 - m_1 ** 2) * (xi ** 2 + 1.0 / xi ** 2) + 2 * m_1 ** 2 - m_2
    )
    return mu_xi, sigma_xi, w_beta, c_beta


def _pars_h(
    sigma1: float,
    sigma2: float,
    sim: Vector[float],
) -> Vector[float]:
    return sigma1 * cast(float, numpy.mean(sim)) + sigma2 * sim


@overload
def hsepd_pdf(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> Vector[float]:
    """node as argument"""


@overload
def hsepd_pdf(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> Vector[float]:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator(
    "calculate the probability densities with the "
    "heteroskedastic skewed exponential power distribution"
)
def hsepd_pdf(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> Vector[float]:
    # noinspection PyUnresolvedReferences
    """Calculate the probability densities based on the heteroskedastic
    skewed exponential power distribution.

    For convenience, we store the required parameters of the probability
    density function as well as the simulated and observed values in a
    dictionary:

    >>> import numpy
    >>> from hydpy import hsepd_pdf, round_
    >>> general = {"sigma1": 0.2,
    ...            "sigma2": 0.0,
    ...            "xi": 1.0,
    ...            "beta": 0.0,
    ...            "sim": numpy.arange(10.0, 41.0),
    ...            "obs": numpy.full(31, 25.0)}

    The following test function allows for varying one parameter and prints
    some and plots all the probability density values corresponding to
    different simulated values:

    >>> def test(**kwargs):
    ...     from matplotlib import pyplot
    ...     special = general.copy()
    ...     name, values = list(kwargs.items())[0]
    ...     results = numpy.zeros((len(general["sim"]), len(values)+1))
    ...     results[:, 0] = general["sim"]
    ...     for jdx, value in enumerate(values):
    ...         special[name] = value
    ...         results[:, jdx+1] = hsepd_pdf(**special)
    ...         pyplot.plot(results[:, 0], results[:, jdx+1],
    ...                     label="%s=%.1f" % (name, value))
    ...     pyplot.legend()
    ...     for idx, result in enumerate(results):
    ...         if not (idx % 5):
    ...             round_(result)

    When varying `beta`, the resulting probabilities correspond to the
    Laplace distribution (1.0), normal distribution (0.0), and the
    uniform distribution (-1.0), respectively.  Note that we use -0.99
    instead of -1.0 for approximating the uniform distribution to prevent
    from running into numerical problems, which are not solved yet:

    >>> test(beta=[1.0, 0.0, -0.99])
    10.0, 0.002032, 0.000886, 0.0
    15.0, 0.008359, 0.010798, 0.0
    20.0, 0.034382, 0.048394, 0.057739
    25.0, 0.141421, 0.079788, 0.057739
    30.0, 0.034382, 0.048394, 0.057739
    35.0, 0.008359, 0.010798, 0.0
    40.0, 0.002032, 0.000886, 0.0

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    When varying `xi`, the resulting density is negatively skewed (0.2),
    symmetric (1.0), and positively skewed (5.0), respectively:

    >>> test(xi=[0.2, 1.0, 5.0])
    10.0, 0.0, 0.000886, 0.003175
    15.0, 0.0, 0.010798, 0.012957
    20.0, 0.092845, 0.048394, 0.036341
    25.0, 0.070063, 0.079788, 0.070063
    30.0, 0.036341, 0.048394, 0.092845
    35.0, 0.012957, 0.010798, 0.0
    40.0, 0.003175, 0.000886, 0.0

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    In the above examples, the actual `sigma` (5.0) is calculated by
    multiplying `sigma1` (0.2) with the mean simulated value (25.0),
    internally.  This can be done for modelling homoscedastic errors.
    Instead, `sigma2` is multiplied with the individual simulated values
    to account for heteroscedastic errors.  With increasing values of
    `sigma2`, the resulting densities are modified as follows:

    >>> test(sigma2=[0.0, 0.1, 0.2])
    10.0, 0.000886, 0.002921, 0.005737
    15.0, 0.010798, 0.018795, 0.022831
    20.0, 0.048394, 0.044159, 0.037988
    25.0, 0.079788, 0.053192, 0.039894
    30.0, 0.048394, 0.04102, 0.032708
    35.0, 0.010798, 0.023493, 0.023493
    40.0, 0.000886, 0.011053, 0.015771

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |hsepd_pdf|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    sigmas = _pars_h(sigma1, sigma2, sim_)
    mu_xi, sigma_xi, w_beta, c_beta = _pars_sepd(xi, beta)
    x, mu = obs_, sim_
    a = (x - mu) / sigmas
    a_xi = cast(Vector[float], numpy.empty(a.shape))
    idxs = mu_xi + sigma_xi * a < 0.0
    a_xi[idxs] = numpy.absolute(xi * (mu_xi + sigma_xi * a[idxs]))
    a_xi[~idxs] = numpy.absolute(1.0 / xi * (mu_xi + sigma_xi * a[~idxs]))
    ps = (
        (2.0 * sigma_xi / (xi + 1.0 / xi) * w_beta)
        * cast(
            Vector[float],
            numpy.exp(-c_beta * a_xi ** (2.0 / (1.0 + beta))),
        )
    ) / sigmas
    return ps


def _hsepd_manual(
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    ps = hsepd_pdf(
        sigma1=sigma1,
        sigma2=sigma2,
        xi=xi,
        beta=beta,
        sim=sim,
        obs=obs,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    ps[ps < 1e-200] = 1e-200
    # noinspection PyTypeChecker
    return cast(float, numpy.mean(numpy.log(ps)))


@overload
def hsepd_manual(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
) -> float:
    """node as argument"""


@overload
def hsepd_manual(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator(
    "calculate an objective value based on method `hsepd_manual`"
)
def hsepd_manual(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
) -> float:
    """Calculate the mean of the logarithmic probability densities of the
    heteroskedastic skewed exponential power distribution.

    The following examples stem from the documentation of function
    |hsepd_pdf|, which is used by function |hsepd_manual|.  The first
    one deals with a heteroscedastic normal distribution:

    >>> from hydpy import hsepd_manual, round_
    >>> round_(hsepd_manual(sigma1=0.2, sigma2=0.2,
    ...                     xi=1.0, beta=0.0,
    ...                     sim=numpy.arange(10.0, 41.0),
    ...                     obs=numpy.full(31, 25.0)))
    -3.682842

    Too small probability density values are set to 1e-200 before calculating
    their logarithm (which means that the lowest possible value returned by
    function |hsepd_manual| is approximately -460):

    >>> round_(hsepd_manual(sigma1=0.2, sigma2=0.0,
    ...                     xi=1.0, beta=-0.99,
    ...                     sim=numpy.arange(10.0, 41.0),
    ...                     obs=numpy.full(31, 25.0)))
    -209.539335

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |hsepd_manual|.
    """
    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    del sim, obs
    return _hsepd_manual(
        sigma1=sigma1,
        sigma2=sigma2,
        xi=xi,
        beta=beta,
        sim=sim_,
        obs=obs_,
        skip_nan=False,
        subperiod=False,
    )


@overload
def hsepd(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
    inits: Optional[Iterable[float]] = None,
    return_pars: Literal[False] = False,
    silent: bool = True,
) -> float:
    """sim and obs as argument, do not return parameters"""


@overload
def hsepd(
    *,
    sim: VectorInput[float],
    obs: VectorInput[float],
    skip_nan: bool = False,
    subperiod: bool = False,
    inits: Optional[Iterable[float]] = None,
    return_pars: Literal[True] = True,
    silent: bool = True,
) -> Tuple[float, Tuple[float, float, float, float]]:
    """sim and obs as arguments, do return parameters"""


@overload
def hsepd(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
    inits: Optional[Iterable[float]] = None,
    return_pars: Literal[False] = False,
    silent: bool = True,
) -> float:
    """node as an arguments, do not return parameters"""


@overload
def hsepd(
    *,
    node: devicetools.Node,
    skip_nan: bool = False,
    subperiod: bool = True,
    inits: Optional[Iterable[float]] = None,
    return_pars: Literal[True] = True,
    silent: bool = True,
) -> Tuple[float, Tuple[float, float, float, float]]:
    """node as an argument, do return parameters"""


@objecttools.excmessage_decorator(
    "calculate an objective value based on method `hsepd`"
)
def hsepd(
    *,
    sim: Optional[VectorInput[float]] = None,
    obs: Optional[VectorInput[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    subperiod: Optional[bool] = None,
    inits: Optional[Iterable[float]] = None,
    return_pars: bool = False,
    silent: bool = True,
) -> Union[float, Tuple[float, Tuple[float, float, float, float]]]:
    """Calculate the mean of the logarithmic probability densities of the
    heteroskedastic skewed exponential power distribution.

    Function |hsepd| serves the same purpose as function |hsepd_manual|
    but tries to estimate the parameters of the heteroscedastic skewed
    exponential distribution via an optimisation algorithm.  This is
    shown by generating a random sample.  One thousant simulated values
    are scattered around the observed (true) value of 10.0 with a
    standard deviation of 2.0:

    >>> import numpy
    >>> numpy.random.seed(0)
    >>> sim = numpy.random.normal(10.0, 2.0, 1000)
    >>> obs = numpy.full(1000, 10.0)

    First, as a reference, we calculate the "true" value based on
    function |hsepd_manual| and the correct distribution parameters:

    >>> from hydpy import Period, hsepd, hsepd_manual, pub, round_
    >>> round_(hsepd_manual(
    ...     sigma1=0.2, sigma2=0.0, xi=1.0, beta=0.0, sim=sim, obs=obs))
    -2.100093

    When using function |hsepd|, the returned value is even a little
    "better":

    >>> round_(hsepd(sim=sim, obs=obs))
    -2.09983

    This is due to the deviation from the random sample to its
    theoretical distribution.  This is reflected by small differences
    between the estimated values and the theoretical values of
    `sigma1` (0.2), `sigma2` (0.0), `xi` (1.0), and `beta` (0.0).
    The estimated values are returned in the mentioned order through
    enabling the `return_pars` option:

    >>> value, pars = hsepd(sim=sim, obs=obs, return_pars=True)
    >>> round_(pars, decimals=5)
    0.19966, 0.0, 0.96836, 0.0188

    There is no guarantee that the optimisation numerical optimisation
    algorithm underlying function |hsepd| will always find the parameters
    resulting in the largest value returned by function |hsepd_manual|.
    You can increase its robustness (and decrease computation time) by
    supplying close initial parameter values:

    >>> value, pars = hsepd(sim=sim, obs=obs, return_pars=True,
    ...                     inits=(0.2, 0.0, 1.0, 0.0))
    >>> round_(pars, decimals=5)
    0.19966, 0.0, 0.96836, 0.0188

    However, the following example shows a case when this strategy
    results in worse results:

    >>> value, pars = hsepd(sim=sim, obs=obs, return_pars=True,
    ...                     inits=(0.0, 0.2, 1.0, 0.0))
    >>> round_(value)
    -2.174492
    >>> round_(pars)
    0.0, 0.213179, 1.705485, 0.505112

    See the documentation on function |prepare_arrays| for some
    additional instructions for using |hsepd|.
    """

    def transform(pars: Tuple[float, float, float, float]) -> float:
        """Transform the actual optimisation problem into a function to
        be minimised and apply parameter constraints."""
        sigma1, sigma2, xi, beta = constrain(*pars)
        return -_hsepd_manual(
            sigma1=sigma1,
            sigma2=sigma2,
            xi=xi,
            beta=beta,
            sim=sim_,
            obs=obs_,
            skip_nan=False,
            subperiod=False,
        )

    def constrain(
        sigma1: float, sigma2: float, xi: float, beta: float
    ) -> Tuple[float, float, float, float]:
        """Apply constraints on the given parameter values."""
        sigma1 = numpy.clip(sigma1, 0.0, None)
        sigma2 = numpy.clip(sigma2, 0.0, None)
        xi = numpy.clip(xi, 0.1, 10.0)
        beta = numpy.clip(beta, -0.99, 5.0)
        return sigma1, sigma2, xi, beta

    sim_, obs_ = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
        subperiod=subperiod,
    )
    if inits is None:
        inits = [0.1, 0.2, 3.0, 1.0]
    original_values = optimize.fmin(
        transform, inits, ftol=1e-12, xtol=1e-12, disp=not silent
    )
    constrained_values = constrain(*original_values)
    result = _hsepd_manual(
        *constrained_values,
        sim=sim_,
        obs=obs_,
        skip_nan=False,
        subperiod=False,
    )
    if return_pars:
        # noinspection PyTypeChecker
        return result, constrained_values
    return result


@objecttools.excmessage_decorator("calculate the weighted mean time")
def calc_mean_time(
    timepoints: VectorInput[float],
    weights: VectorInput[float],
) -> float:
    """Return the weighted mean of the given time points.

    With equal given weights, the result is simply the mean of the given
    time points:

    >>> from hydpy import calc_mean_time
    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[2., 2.])
    5.0

    With different weights, the resulting time is shifted to the larger ones:

    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[1., 3.])
    6.0

    Or, in the most extreme case:

    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[0., 4.])
    7.0

    There are some checks for input plausibility, e.g.:

    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[-2., 2.])
    Traceback (most recent call last):
    ...
    ValueError: While trying to calculate the weighted mean time, \
the following error occurred: For the following objects, at least \
one value is negative: weights.
    """
    timepoints = numpy.asarray(timepoints)
    weights = numpy.asarray(weights)
    validtools.test_equal_shape(timepoints=timepoints, weights=weights)
    validtools.test_non_negative(weights=weights)
    return cast(
        float,
        numpy.dot(timepoints, weights) / numpy.sum(weights),
    )


@objecttools.excmessage_decorator(
    "calculate the weighted time deviation from mean time"
)
def calc_mean_time_deviation(
    timepoints: VectorInput[float],
    weights: VectorInput[float],
    mean_time: Optional[float] = None,
) -> float:
    """Return the weighted deviation of the given timepoints from their mean
    time.

    With equal given weights, the is simply the standard deviation of the
    given time points:

    >>> from hydpy import calc_mean_time_deviation
    >>> calc_mean_time_deviation(timepoints=[3., 7.],
    ...                          weights=[2., 2.])
    2.0

    One can pass a precalculated mean time:

    >>> from hydpy import round_
    >>> round_(calc_mean_time_deviation(timepoints=[3., 7.],
    ...                                 weights=[2., 2.],
    ...                                 mean_time=4.))
    2.236068

    >>> round_(calc_mean_time_deviation(timepoints=[3., 7.],
    ...                                 weights=[1., 3.]))
    1.732051

    Or, in the most extreme case:

    >>> calc_mean_time_deviation(timepoints=[3., 7.],
    ...                          weights=[0., 4.])
    0.0

    There are some checks for input plausibility, e.g.:

    >>> calc_mean_time_deviation(timepoints=[3., 7.],
    ...                          weights=[-2., 2.])
    Traceback (most recent call last):
    ...
    ValueError: While trying to calculate the weighted time deviation \
from mean time, the following error occurred: For the following objects, \
at least one value is negative: weights.
    """
    timepoints_ = numpy.asarray(timepoints)
    weights_ = numpy.asarray(weights)
    del timepoints, weights
    validtools.test_equal_shape(timepoints=timepoints_, weights=weights_)
    validtools.test_non_negative(weights=weights_)
    if mean_time is None:
        mean_time = calc_mean_time(timepoints_, weights_)
    return cast(
        float,
        numpy.sqrt(
            numpy.dot(weights_, (timepoints_ - mean_time) ** 2) / numpy.sum(weights_)
        ),
    )


@overload
def print_evaluationtable(
    *,
    nodes: Sequence[devicetools.Node],
    criteria: Sequence[Criterion],
    nodenames: Optional[Sequence[str]] = None,
    critnames: Optional[Sequence[str]] = None,
    critfactors: Sequence1[float] = 1.0,
    critdigits: Sequence1[int] = 2,
    subperiod: bool = True,
    average: bool = True,
    averagename: str = "mean",
    filter_: float = 1.0,
    missingvalue: str = "-",
    decimalseperator: str = ".",
    file_: Optional[Union[str, TextIO]] = None,
) -> None:
    ...


@overload
def print_evaluationtable(
    *,
    nodes: Sequence[devicetools.Node],
    criteria: Sequence[Criterion],
    nodenames: Optional[Sequence[str]] = None,
    critnames: Optional[Sequence[str]] = None,
    critfactors: Sequence1[float] = 1.0,
    critdigits: Sequence1[int] = 2,
    subperiod: bool = True,
    average: bool = True,
    averagename: str = "mean",
    filter_: float = 1.0,
    stepsize: Literal["daily", "d", "monthly", "m"] = "daily",
    aggregator: Union[str, Callable[[VectorInput[float]], float]] = "mean",
    missingvalue: str = "-",
    decimalseperator: str = ".",
    file_: Optional[Union[str, TextIO]] = None,
) -> None:
    ...


@objecttools.excmessage_decorator(
    "evaluate the simulation results of some node objects"
)
def print_evaluationtable(
    *,
    nodes: Sequence[devicetools.Node],
    criteria: Sequence[Criterion],
    nodenames: Optional[Sequence[str]] = None,
    critnames: Optional[Sequence[str]] = None,
    critfactors: Sequence1[float] = 1.0,
    critdigits: Sequence1[int] = 2,
    subperiod: bool = True,
    average: bool = True,
    averagename: str = "mean",
    filter_: float = 1.0,
    stepsize: Optional[Literal["daily", "d", "monthly", "m"]] = None,
    aggregator: Union[str, Callable[[VectorInput[float]], float]] = "mean",
    missingvalue: str = "-",
    decimalseperator: str = ".",
    file_: Optional[Union[str, TextIO]] = None,
) -> None:
    """Print a table containing the results of the given evaluation criteria
    for the given |Node| objects.

    First, we define two nodes with different simulation and observation
    data (see function |prepare_arrays| for some explanations):

    >>> from hydpy import pub, Node, nan
    >>> pub.timegrids = "01.01.2000", "04.01.2000", "1d"
    >>> nodes = Node("test1"), Node("test2")
    >>> for node in nodes:
    ...     node.prepare_simseries()
    ...     node.sequences.sim.series = 1.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 4.0, 5.0, 6.0
    >>> nodes[0].sequences.sim.series = 1.0, 2.0, 3.0
    >>> nodes[0].sequences.obs.series = 4.0, 5.0, 6.0
    >>> nodes[1].sequences.sim.series = 1.0, 2.0, 3.0
    >>> with pub.options.checkseries(False):
    ...     nodes[1].sequences.obs.series = 3.0, nan, 1.0

    Selecting functions |corr| and |bias_abs| as evaluation criteria,
    function |print_evaluationtable| prints the following table:

    >>> from hydpy import bias_abs, corr, print_evaluationtable
    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs))
           corr  bias_abs
    test1  1.00     -3.00
    test2     -         -
    mean   1.00     -3.00

    One can pass alternative names for the node objects, the criteria functions,
    and the row containing the average values.  Also, one can use the `filter_`
    argument to force printing statistics in case of incomplete observation data.
    In the following example, we accept a maximum fraction of missing data of 50 %:

    >>> print_evaluationtable(nodes=nodes,
    ...                       criteria=(corr, bias_abs),
    ...                       nodenames=("first node", "second node"),
    ...                       critnames=("corrcoef", "bias"),
    ...                       critdigits=1,
    ...                       averagename="average",
    ...                       filter_=0.5)   # doctest: +NORMALIZE_WHITESPACE
                 corrcoef  bias
    first node        1.0  -3.0
    second node      -1.0   0.0
    average           0.0  -1.5

    The number of assigned node objects and criteria functions must
    match the number of given alternative names:

    >>> print_evaluationtable(nodes=nodes,
    ...                       criteria=(corr, bias_abs),
    ...                       nodenames=("first node",))
    Traceback (most recent call last):
    ...
    ValueError: While trying to evaluate the simulation results of some \
node objects, the following error occurred: 2 node objects are given \
which does not match with number of given alternative names being 1.

    >>> print_evaluationtable(nodes=nodes,
    ...                       criteria=(corr, bias_abs),
    ...                       critnames=("corrcoef",))
    Traceback (most recent call last):
    ...
    ValueError: While trying to evaluate the simulation results of some \
node objects, the following error occurred: 2 criteria functions are given \
which does not match with number of given alternative names being 1.

    Set the `average` argument to |False| to omit the row containing the
    average values:

    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs),
    ...                       average=False)
           corr  bias_abs
    test1  1.00     -3.00
    test2     -         -

    You can use the arguments `critfactors` and `critdigits` by passing either
    a single number or a sequence of criteria-specific numbers to modify the
    printed values:

    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs),
    ...                       critfactors=(10.0, 0.1),
    ...                       critdigits=1)
           corr  bias_abs
    test1  10.0      -0.3
    test2     -         -
    mean   10.0      -0.3

    By default, function |print_evaluationtable| prints the statics relevant
    for the actual evaluation period only:

    >>> pub.timegrids.eval_.dates = "01.01.2000", "02.01.2000"
    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs))
           corr  bias_abs
    test1     -     -3.00
    test2     -     -2.00
    mean      -     -2.50

    You can deviate from this default behaviour by setting the `subperiod`
    argument to |False|:

    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs),
    ...                       subperiod=False)
           corr  bias_abs
    test1  1.00     -3.00
    test2     -         -
    mean   1.00     -3.00

    Use the `stepsize` argument (eventually in combination with argument
    `aggregator`) to print the statistics of previously aggregated time
    series.  See function |aggregate_series| for further information.

    Here, the daily aggregation step size results in identical results as
    the original step size is also one day:

    >>> pub.timegrids.eval_ = pub.timegrids.init
    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs),
    ...                       stepsize="daily",
    ...                       aggregator="mean")
           corr  bias_abs
    test1  1.00     -3.00
    test2     -         -
    mean   1.00     -3.00

    For the monthly step size, the result table is empty, due to the too short
    initialisation period covering less than a month:

    >>> pub.timegrids.eval_.dates = pub.timegrids.init.dates
    >>> print_evaluationtable(nodes=nodes,  # doctest: +NORMALIZE_WHITESPACE
    ...                       criteria=(corr, bias_abs),
    ...                       stepsize="monthly",
    ...                       aggregator="mean")
           corr  bias_abs
    test1     -         -
    test2     -         -
    mean      -         -
    """
    if nodenames:
        if len(nodes) != len(nodenames):
            raise ValueError(
                f"{len(nodes)} node objects are given which does not "
                f"match with number of given alternative names being "
                f"{len(nodenames)}."
            )
    else:
        nodenames = [node.name for node in nodes]
    if critnames:
        if len(criteria) != len(critnames):
            raise ValueError(
                f"{len(criteria)} criteria functions are given which does "
                f"not match with number of given alternative names being "
                f"{len(critnames)}."
            )
    else:
        critnames = [crit.__name__ for crit in criteria]
    if isinstance(critfactors, float):
        critfactors = len(criteria) * (critfactors,)
    if isinstance(critdigits, int):
        critdigits = len(criteria) * (critdigits,)
    formats = tuple(f"%.{d}f" for d in critdigits)
    data = numpy.empty((len(nodes), len(criteria)), dtype=float)
    for idx, node in enumerate(nodes):
        if stepsize is not None:
            sim = seriestools.aggregate_series(
                series=node.sequences.sim.series,
                stepsize=stepsize,
                aggregator=aggregator,
                subperiod=subperiod,
            ).values
            obs = seriestools.aggregate_series(
                series=node.sequences.obs.series,
                stepsize=stepsize,
                aggregator=aggregator,
                subperiod=subperiod,
            ).values
        else:
            sim, obs = prepare_arrays(
                node=node,
                skip_nan=False,
                subperiod=subperiod,
            )
        if len(obs) > 0:
            availability = 1.0 - sum(numpy.isnan(obs)) / len(obs)
        else:
            availability = 0.0
        if availability < filter_:
            data[idx, :] = numpy.nan
        else:
            for jdx, (criterion, critfactor) in enumerate(zip(criteria, critfactors)):
                data[idx, jdx] = critfactor * criterion(sim=sim, obs=obs, skip_nan=True)

    def _write(x: str, ys: Iterable[str], printtarget_: TextIO) -> None:
        printtarget_.write(f"{x}\t")
        printtarget_.write("\t".join(ys).replace(".", decimalseperator))
        printtarget_.write("\n")

    def _nmbs2strs(numbers: Iterable[float]) -> Generator[str, None, None]:
        return (
            (f % n).replace(".", decimalseperator).replace("nan", missingvalue)
            for n, f in zip(numbers, formats)
        )

    with objecttools.get_printtarget(file_) as printtarget:
        _write("", critnames, printtarget)
        for nodename, row in zip(nodenames, data):
            _write(nodename, _nmbs2strs(row), printtarget)
        if average:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", "Mean of empty slice")
                mean = _nmbs2strs(numpy.nanmean(data, axis=0))
            _write(averagename, mean, printtarget)
