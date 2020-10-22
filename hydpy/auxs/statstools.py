# -*- coding: utf-8 -*-
"""This module implements statistical functionalities frequently used in
hydrological modelling."""
# import...
# ...from standard library
from typing import *
from typing_extensions import Literal

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.auxs import validtools

pandas: "pandas" = exceptiontools.OptionalImport("pandas", ["pandas"], locals())
optimize: "optimize" = exceptiontools.OptionalImport(
    "optimize", ["scipy.optimize"], locals()
)
special: "special" = exceptiontools.OptionalImport(
    "special", ["scipy.special"], locals()
)
if TYPE_CHECKING:
    import pandas
    from scipy import optimize
    from scipy import special


class SimObs(NamedTuple):
    """A named tuple containing one array of simulated and one array of
    observed values."""

    sim: numpy.ndarray
    obs: numpy.ndarray


@overload
def aggregate_series(
    sim: Sequence[float],
    obs: Sequence[float],
    stepsize: Literal["daily", "d"],
    aggregator: Callable,
    basetime: str = ...,
) -> SimObs:
    """sim and obs as arguments, daily aggregation"""


@overload
def aggregate_series(
    sim: Sequence[float],
    obs: Sequence[float],
    stepsize: Literal["monthly", "m"],
    aggregator: Callable,
) -> SimObs:
    """sim and obs as arguments, monthly aggregation"""


@overload
def aggregate_series(
    node: devicetools.Node,
    stepsize: Literal["daily", "d"],
    aggregator: Callable,
    basetime: str = ...,
) -> SimObs:
    """node as an argument, daily aggregation"""


@overload
def aggregate_series(
    node: devicetools.Node,
    stepsize: Literal["monthly", "m"],
    aggregator: Callable,
) -> SimObs:
    """node as an argument, monthly aggregation"""


@objecttools.excmessage_decorator("aggregate the given series")
def aggregate_series(
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    stepsize: Literal["daily", "d", "monthly", "m"] = "monthly",
    function: Union[str, Callable] = "mean",
    basetime: str = "00:00",
) -> SimObs:
    """Aggregate the time series on a monthly or daily basis.

    Often, we need some kind of aggregation before analysing deviations
    between simulation results and observations.  Function |aggregate_series|
    performs such aggregation on a monthly or daily basis.  You are
    free to specify arbitrary aggregation functions.

    We first show the default behaviour of function |aggregate_series|,
    which is to calculate monthly averages.  Therefore, we first say the
    hydrological summer half-year 2001 to be our simulation period and
    define a daily simulation step size:

    >>> from hydpy import aggregate_series, pub, Node
    >>> pub.timegrids = '01.11.2000', '01.05.2001', '1d'

    Next, we prepare a |Node| object and assign some constantly increasing
    and decreasing values to its `simulation` and the `observation` series,
    respectively:

    >>> import numpy
    >>> node = Node('test')
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(1, 181+1)
    >>> node.sequences.obs.series = numpy.arange(181, 0, -1)

    |aggregate_series| returns the data within index-sorted |pandas.Series|
    objects (note that the index addresses the left boundary of each time step:

    >>> sim, obs = aggregate_series(node=node)
    >>> sim
    2000-11-01     15.5
    2000-12-01     46.0
    2001-01-01     77.0
    2001-02-01    106.5
    2001-03-01    136.0
    2001-04-01    166.5
    Freq: MS, Name: sim, dtype: float64
    >>> obs
    2000-11-01    166.5
    2000-12-01    136.0
    2001-01-01    105.0
    2001-02-01     75.5
    2001-03-01     46.0
    2001-04-01     15.5
    Freq: MS, Name: obs, dtype: float64

    You can pass another aggregation function:

    >>> aggregate_series(node=node, function=numpy.sum).sim
    2000-11-01     465.0
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    2001-04-01    4995.0
    Freq: MS, Name: sim, dtype: float64

    Functions |aggregate_series| raises errors like the following for
    unsuitable functions:

    >>> def wrong():
    ...     return None
    >>> aggregate_series(node=node, function=wrong)
    Traceback (most recent call last):
    ...
    TypeError: While trying to aggregate the given series, the following \
error occurred: While trying to perform the aggregation based on method \
`wrong`, the following error occurred: wrong() takes 0 positional arguments \
but 1 was given

    When passing a string, |aggregate_series| queries it from |numpy|:

    >>> aggregate_series(node=node, function='sum').sim
    2000-11-01     465.0
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    2001-04-01    4995.0
    Freq: MS, Name: sim, dtype: float64

    |aggregate_series| raises the following error when the requested function
    does not exist:

    >>> aggregate_series(node=node, function='Sum')
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Module `numpy` does not provide a function named `Sum`.

    To prevent from conclusions, |aggregate_series| generally ignores all
    data of incomplete intervals:

    >>> pub.timegrids = '30.11.2000', '2.04.2001', '1d'
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(30, 152+1)
    >>> node.sequences.obs.series = numpy.arange(152, 29, -1)
    >>> aggregate_series(node=node, function='sum').sim
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    Freq: MS, Name: sim, dtype: float64

    The following example shows that even with only one missing value at
    the respective ends of the simulation period, |aggregate_series| does
    not return any result for the first (November 2000) and the last
    aggregation interval (April 2001):

    >>> pub.timegrids = '02.11.2000', '30.04.2001', '1d'
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(2, 180+1)
    >>> node.sequences.obs.series = numpy.arange(180, 1, -1)
    >>> aggregate_series(node=node, function='sum').sim
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    Freq: MS, Name: sim, dtype: float64

    Now we prepare a time-grid with an hourly simulation step size, to
    show some examples on daily aggregation:

    >>> pub.timegrids = '01.01.2000 22:00', '05.01.2000 22:00', '1h'
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(1, 1+4*24)
    >>> node.sequences.obs.series = numpy.arange(4*24, 0, -1)

    By default, function |aggregate_series| aggregates daily from 0 o'clock
    to 0 o'clock, which here results in a loss of the first two and the last
    22 values of the entire period:

    >>> sim, obs = aggregate_series(node=node, stepsize='daily')
    >>> sim
    2000-01-02    14.5
    2000-01-03    38.5
    2000-01-04    62.5
    Freq: 86400S, Name: sim, dtype: float64
    >>> obs
    2000-01-02    82.5
    2000-01-03    58.5
    2000-01-04    34.5
    Freq: 86400S, Name: obs, dtype: float64

    If you want the aggregation to start at a different time of the day,
    use the `basetime` argument.  In our example, starting at 22 o'clock
    fits the defined initialisation time grid and ensures the usage of
    all available data:

    >>> aggregate_series(node=node, stepsize='daily', basetime='22:00').sim
    2000-01-01 22:00:00    12.5
    2000-01-02 22:00:00    36.5
    2000-01-03 22:00:00    60.5
    2000-01-04 22:00:00    84.5
    Freq: 86400S, Name: sim, dtype: float64

    So far, the `basetime` argument works for daily aggregation only:

    >>> aggregate_series(node=node, stepsize='monthly', basetime='22:00')
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Use the `basetime` argument in combination with a `daily` \
aggregation step size only.

    Note that you are also free to either pass the `sim` and `obs` series
    directly instead of a `node` (see function |prepare_arrays| for further
    information):

    >>> xs = sim=node.sequences.sim.series
    >>> ys = obs=node.sequences.obs.series
    >>> aggregate_series(sim=xs, obs=ys, stepsize='daily').sim
    2000-01-02    14.5
    2000-01-03    38.5
    2000-01-04    62.5
    Freq: 86400S, Name: sim, dtype: float64

    |aggregate_series| does not support aggregation for simulation step
    sizes larger one day:

    >>> pub.timegrids = '01.01.2000 22:00', '05.01.2000 22:00', '1d'
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(1, 1+4)
    >>> node.sequences.obs.series = numpy.arange(4, 0, -1)
    >>> aggregate_series(node=node, stepsize='daily').sim
    2000-01-01    1.0
    2000-01-02    2.0
    2000-01-03    3.0
    2000-01-04    4.0
    Freq: 86400S, Name: sim, dtype: float64

    >>> pub.timegrids = '01.01.2000 22:00', '05.01.2000 22:00', '2d'
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(1, 1+2)
    >>> node.sequences.obs.series = numpy.arange(2, 0, -1)
    >>> aggregate_series(node=node, stepsize='daily')
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Data aggregation is not supported for simulation step sizes \
greater one day.

    We are looking forward supporting other useful aggregation step sizes later:

    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Argument `stepsize` received value `yearly`, but only the \
following ones are supported: `monthly` (default) and `daily`.

    >>> pub.timegrids = '01.01.2000 22:00', '05.01.2000 22:00', '1d'
    >>> aggregate_series(node=node, stepsize='yearly')
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Argument `stepsize` received value `yearly`, but only the \
following ones are supported: `monthly` (default) and `daily`.
    """
    if isinstance(function, str):
        try:
            function = getattr(numpy, function)
        except AttributeError:
            raise ValueError(
                f"Module `numpy` does not provide a function named " f"`{function}`."
            ) from None
    tg = hydpy.pub.timegrids.init
    if tg.stepsize > "1d":
        raise ValueError(
            "Data aggregation is not supported for simulation "
            "step sizes greater one day."
        )
    if stepsize == "daily":
        rule = "86400s"
        offset = (
            timetools.Date(f"2000-01-01 {basetime}") - timetools.Date("2000-01-01")
        ).seconds
        firstdate_expanded = tg.firstdate - "1d"
        lastdate_expanded = tg.lastdate + "1d"
    elif basetime != "00:00":
        raise ValueError(
            "Use the `basetime` argument in combination with "
            "a `daily` aggregation step size only."
        )
    elif stepsize == "monthly":
        rule = "MS"
        offset = 0
        firstdate_expanded = tg.firstdate - "31d"
        lastdate_expanded = tg.lastdate + "31d"
    else:
        raise ValueError(
            f"Argument `stepsize` received value `{stepsize}`, but only the "
            f"following ones are supported: `monthly` (default) and `daily`."
        )
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=False,
    )
    dataframe_orig = pandas.DataFrame()
    dataframe_orig["sim"] = sim
    dataframe_orig["obs"] = obs
    dataframe_orig.index = pandas.date_range(
        start=tg.firstdate.datetime,
        end=(tg.lastdate - tg.stepsize).datetime,
        freq=tg.stepsize.timedelta,
    )
    dataframe_expanded = dataframe_orig.reindex(
        pandas.date_range(
            start=firstdate_expanded.datetime,
            end=lastdate_expanded.datetime,
            freq=tg.stepsize.timedelta,
        ),
        fill_value=numpy.nan,
    )
    resampler = dataframe_expanded.resample(
        rule=rule,
        offset=f"{offset}s",
    )
    try:
        df_resampled_expanded = resampler.apply(lambda x: function(x.values))
    except BaseException:
        objecttools.augment_excmessage(
            f"While trying to perform the aggregation based "
            f"on method `{function.__name__}`"
        )
    # noinspection PyUnboundLocalVariable
    idx0 = df_resampled_expanded.first_valid_index()
    idx1 = df_resampled_expanded.last_valid_index()
    df_resampled_stripped = df_resampled_expanded.loc[idx0:idx1]
    return SimObs(
        sim=df_resampled_stripped["sim"],
        obs=df_resampled_stripped["obs"],
    )


@overload
def filter_series(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    date_ranges: Optional[
        Iterable[Tuple[timetools.DateConstrArg, timetools.DateConstrArg]]
    ],
) -> SimObs:
    """sim and obs and date_ranges as arguments"""


@overload
def filter_series(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    months: Optional[Iterable[int]],
) -> SimObs:
    """sim and obs and month as arguments"""


@overload
def filter_series(
    *,
    node: devicetools.Node,
    date_ranges: Optional[
        Iterable[Tuple[timetools.DateConstrArg, timetools.DateConstrArg]]
    ],
) -> SimObs:
    """node and date_ranges as arguments"""


@overload
def filter_series(
    *,
    node: devicetools.Node,
    months: Optional[Iterable[int]],
) -> SimObs:
    """node and month as arguments"""


@objecttools.excmessage_decorator("filter the given series")
def filter_series(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
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
    >>> pub.timegrids = '2001-11-01', '2003-11-01', '1d'

    Next, we prepare a |Node| object and assign some constantly increasing
    and decreasing values to its `simulation` and the `observation` series,
    respectively:

    >>> import numpy
    >>> node = Node('test')
    >>> node.prepare_allseries()
    >>> node.sequences.sim.series = numpy.arange(1, 2*365+1)
    >>> node.sequences.obs.series = numpy.arange(2*365, 0, -1)

    First, we select data of arbitrary sub-periods via the `data_ranges`
    argument.  Each data range consists of the start-point and the end-point
    of a sub-period. Here, we choose all values that belong to 31 October
    or 1 November (note that unsorted data ranges are acceptable):

    >>> date_ranges = [('2001-11-01', '2001-11-02'),
    ...                ('2002-10-31', '2002-11-02'),
    ...                ('2003-10-31', '2003-11-01')]
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

    >>> date_ranges = [('2001-10-31', '2003-11-01')]
    >>> filter_series(node=node, date_ranges=date_ranges)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: The given date (2001-10-31 00:00:00) is before the first date of \
the initialisation period (2001-11-01 00:00:00).

    >>> date_ranges = [('2001-11-01', '2003-11-02')]
    >>> filter_series(node=node, date_ranges=date_ranges)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: The given date (2003-11-02 00:00:00) is behind the last date of \
the initialisation period (2003-11-01 00:00:00).

    >>> date_ranges = [('2001-11-02', '2001-11-02')]
    >>> filter_series(node=node, date_ranges=date_ranges)
    Traceback (most recent call last):
    ...
    ValueError: While trying to filter the given series, the following error \
occurred: The given first date `2001-11-02 00:00:00` is not before than the \
given last date `2001-11-02 00:00:00`.

    Note that function |filter_series| does not remove any duplicates:

    >>> date_ranges = [('2001-11-01', '2001-11-05'),
    ...                ('2001-11-01', '2001-11-02'),
    ...                ('2001-11-04', '2001-11-06')]
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=False,
    )
    dataframe["sim"] = sim
    dataframe["obs"] = obs
    tg = hydpy.pub.timegrids.init
    dataframe.index = pandas.date_range(
        start=tg.firstdate.datetime,
        end=tg.lastdate.datetime - tg.stepsize.timedelta,
        freq=tg.stepsize.timedelta,
    )
    dataframe_selected = pandas.DataFrame()
    if (date_ranges is None) and (months is None):
        raise ValueError(
            "You need to define either the `date_ranges` or `months` "
            "argument, but none of them is given."
        )
    if (date_ranges is not None) and (months is not None):
        raise ValueError(
            "You need to define either the `date_ranges` or `months` "
            "argument, but both of them are given."
        )
    if date_ranges is not None:
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
            selected_dates = dataframe.loc[idx0:idx1]
            dataframe_selected = pandas.concat(
                [selected_dates, dataframe_selected],
            )
    else:
        for month in months:
            selected_dates = dataframe.loc[dataframe.index.month == int(month)]
            dataframe_selected = pandas.concat(
                [selected_dates, dataframe_selected],
            )
    dataframe_selected = dataframe_selected.sort_index()
    return SimObs(
        sim=dataframe_selected["sim"],
        obs=dataframe_selected["obs"],
    )


def prepare_arrays(
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
) -> SimObs:
    """Prepare and return two |numpy| arrays based on the given arguments.

    Note that many functions provided by module |statstools| apply function
    |prepare_arrays| internally (e.g. |nse|).  But you can also use it
    manually, as shown in the following examples.

    Function |prepare_arrays| can extract time-series data from |Node|
    objects.  To set up an example for this, we define an initialisation
    period and prepare a |Node| object:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

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
    if node:
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
    sim = numpy.asarray(sim)
    obs = numpy.asarray(obs)
    if skip_nan:
        idxs = ~numpy.isnan(sim) * ~numpy.isnan(obs)
        sim = sim[idxs]
        obs = obs[idxs]
    return SimObs(
        sim=sim,
        obs=obs,
    )


@overload
def rmse(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> numpy.ndarray:
    """node as argument"""


@overload
def rmse(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the root-mean-square error")
def rmse(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return numpy.sqrt(numpy.mean((sim - obs) ** 2))


@overload
def nse(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> numpy.ndarray:
    """node as argument"""


@overload
def nse(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the Nash-Sutcliffe efficiency")
def nse(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return 1.0 - numpy.sum((sim - obs) ** 2) / numpy.sum((obs - numpy.mean(obs)) ** 2)


@overload
def nse_log(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def nse_log(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the log-Nash-Sutcliffe efficiency")
def nse_log(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return 1.0 - numpy.sum((numpy.log(sim) - numpy.log(obs)) ** 2) / numpy.sum(
        (numpy.log(obs) - numpy.mean(numpy.log(obs))) ** 2
    )


@overload
def corr2(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def corr2(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the R²-Error")
def corr2(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    if (numpy.std(sim) == 0.0) or (numpy.std(obs) == 0.0):
        return numpy.nan
    return numpy.corrcoef(sim, obs)[0, 1] ** 2


@overload
def kge(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def kge(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the Kling-Gupta-Efficiency")
def kge(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return 1 - numpy.sum(
        (numpy.corrcoef(sim, obs)[0, 1] - 1) ** 2
        + (numpy.std(sim) / numpy.std(obs) - 1) ** 2
        + (numpy.mean(sim) / numpy.mean(obs) - 1) ** 2
    )


@overload
def bias_abs(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def bias_abs(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the absolute bias")
def bias_abs(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    # noinspection PyTypeChecker
    return numpy.mean(sim - obs)


@overload
def bias_rel(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def bias_rel(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the relative bias")
def bias_rel(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return numpy.mean(sim) / numpy.mean(obs) - 1.0


@overload
def std_ratio(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def std_ratio(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the standard deviation ratio")
def std_ratio(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return numpy.std(sim) / numpy.std(obs) - 1.0


@overload
def corr(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> float:
    """node as argument"""


@overload
def corr(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> float:
    """sim and obs as arguments"""


@objecttools.excmessage_decorator("calculate the Pearson correlation coefficient")
def corr(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    if (numpy.std(sim) == 0.0) or (numpy.std(obs) == 0.0):
        return numpy.nan
    return numpy.corrcoef(sim, obs)[0, 1]


def _pars_sepd(xi, beta):
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


def _pars_h(sigma1, sigma2, sim):
    return sigma1 * numpy.mean(sim) + sigma2 * sim


@overload
def hsepd_pdf(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
) -> numpy.ndarray:
    """node as argument"""


@overload
def hsepd_pdf(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    node: devicetools.Node,
    skip_nan: bool = ...,
) -> numpy.ndarray:
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
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
) -> numpy.ndarray:
    # noinspection PyUnresolvedReferences
    """Calculate the probability densities based on the
    heteroskedastic skewed exponential power distribution.

    For convenience, we store the required parameters of the probability
    density function as well as the simulated and observed values in a
    dictionary:

    >>> import numpy
    >>> from hydpy import hsepd_pdf, round_
    >>> general = {'sigma1': 0.2,
    ...            'sigma2': 0.0,
    ...            'xi': 1.0,
    ...            'beta': 0.0,
    ...            'sim': numpy.arange(10.0, 41.0),
    ...            'obs': numpy.full(31, 25.0)}

    The following test function allows for varying one parameter and prints
    some and plots all the probability density values corresponding to
    different simulated values:

    >>> def test(**kwargs):
    ...     from matplotlib import pyplot
    ...     special = general.copy()
    ...     name, values = list(kwargs.items())[0]
    ...     results = numpy.zeros((len(general['sim']), len(values)+1))
    ...     results[:, 0] = general['sim']
    ...     for jdx, value in enumerate(values):
    ...         special[name] = value
    ...         results[:, jdx+1] = hsepd_pdf(**special)
    ...         pyplot.plot(results[:, 0], results[:, jdx+1],
    ...                     label='%s=%.1f' % (name, value))
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    sigmas = _pars_h(sigma1, sigma2, sim)
    mu_xi, sigma_xi, w_beta, c_beta = _pars_sepd(xi, beta)
    x, mu = obs, sim
    a = (x - mu) / sigmas
    a_xi = numpy.empty(a.shape)
    idxs = mu_xi + sigma_xi * a < 0.0
    a_xi[idxs] = numpy.absolute(xi * (mu_xi + sigma_xi * a[idxs]))
    a_xi[~idxs] = numpy.absolute(1.0 / xi * (mu_xi + sigma_xi * a[~idxs]))
    ps = (
        2.0
        * sigma_xi
        / (xi + 1.0 / xi)
        * w_beta
        * numpy.exp(-c_beta * a_xi ** (2.0 / (1.0 + beta)))
    ) / sigmas
    return ps


def _hsepd_manual(sigma1, sigma2, xi, beta, sim, obs) -> float:
    ps = hsepd_pdf(
        sigma1=sigma1,
        sigma2=sigma2,
        xi=xi,
        beta=beta,
        sim=sim,
        obs=obs,
    )
    ps[ps < 1e-200] = 1e-200
    # noinspection PyTypeChecker
    return numpy.mean(numpy.log(ps))


@overload
def hsepd_manual(
    *,
    sigma1: float,
    sigma2: float,
    xi: float,
    beta: float,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
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
    skip_nan: bool = ...,
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
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
) -> float:
    """Calculate the mean of the logarithmic probability densities of the
    heteroskedastic skewed exponential power distribution.

    The following examples stem from the documentation of function
    |hsepd_pdf|, which is used by function |hsepd_manual|.  The first
    one deals with a heteroscedastic normal distribution:

    >>> from hydpy import round_
    >>> from hydpy import hsepd_manual
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
    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    return _hsepd_manual(sigma1, sigma2, xi, beta, sim, obs)


@overload
def hsepd(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
    inits: Optional[Iterable[float]],
    return_pars: Literal[False],
    silent: bool,
) -> float:
    """sim and obs as argument, do not return parameters"""


@overload
def hsepd(
    *,
    sim: Sequence[float],
    obs: Sequence[float],
    skip_nan: bool = ...,
    inits: Optional[Iterable[float]],
    return_pars: Literal[True],
    silent: bool,
) -> Tuple[float, Tuple[float, float, float, float]]:
    """sim and obs as arguments, do return parameters"""


@overload
def hsepd(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
    inits: Optional[Iterable[float]],
    return_pars: Literal[False],
    silent: bool,
) -> float:
    """node as an arguments, do not return parameters"""


@overload
def hsepd(
    *,
    node: devicetools.Node,
    skip_nan: bool = ...,
    inits: Optional[Iterable[float]],
    return_pars: Literal[True],
    silent: bool,
) -> Tuple[float, Tuple[float, float, float, float]]:
    """node as an argument, do return parameters"""


@objecttools.excmessage_decorator(
    "calculate an objective value based on method `hsepd`"
)
def hsepd(
    *,
    sim: Optional[Sequence[float]] = None,
    obs: Optional[Sequence[float]] = None,
    node: Optional[devicetools.Node] = None,
    skip_nan: bool = False,
    inits: Optional[Iterable[float]] = None,
    return_pars: bool = False,
    silent: bool = True,
) -> float:
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

    >>> from hydpy import round_
    >>> from hydpy import hsepd, hsepd_manual
    >>> round_(hsepd_manual(sigma1=0.2, sigma2=0.0,
    ...                     xi=1.0, beta=0.0,
    ...                     sim=sim, obs=obs))
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

    def transform(pars):
        """Transform the actual optimisation problem into a function to
        be minimised and apply parameter constraints."""
        sigma1, sigma2, xi, beta = constrain(*pars)
        return -_hsepd_manual(sigma1, sigma2, xi, beta, sim, obs)

    def constrain(sigma1, sigma2, xi, beta):
        """Apply constraints on the given parameter values."""
        sigma1 = numpy.clip(sigma1, 0.0, None)
        sigma2 = numpy.clip(sigma2, 0.0, None)
        xi = numpy.clip(xi, 0.1, 10.0)
        beta = numpy.clip(beta, -0.99, 5.0)
        return sigma1, sigma2, xi, beta

    sim, obs = prepare_arrays(
        sim=sim,
        obs=obs,
        node=node,
        skip_nan=skip_nan,
    )
    if inits is None:
        inits = [0.1, 0.2, 3.0, 1.0]
    values = optimize.fmin(transform, inits, ftol=1e-12, xtol=1e-12, disp=not silent)
    values = constrain(*values)
    result = _hsepd_manual(*values, sim=sim, obs=obs)
    if return_pars:
        # noinspection PyTypeChecker
        return result, values
    return result


@objecttools.excmessage_decorator("calculate the weighted mean time")
def calc_mean_time(
    timepoints: Sequence[float],
    weights: Sequence[float],
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
    timepoints = numpy.array(timepoints)
    weights = numpy.array(weights)
    validtools.test_equal_shape(timepoints=timepoints, weights=weights)
    validtools.test_non_negative(weights=weights)
    return numpy.dot(timepoints, weights) / numpy.sum(weights)


@objecttools.excmessage_decorator(
    "calculate the weighted time deviation from mean time"
)
def calc_mean_time_deviation(
    timepoints: Sequence[float],
    weights: Sequence[float],
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
    timepoints = numpy.array(timepoints)
    weights = numpy.array(weights)
    validtools.test_equal_shape(timepoints=timepoints, weights=weights)
    validtools.test_non_negative(weights=weights)
    if mean_time is None:
        mean_time = calc_mean_time(timepoints, weights)
    return numpy.sqrt(
        numpy.dot(weights, (timepoints - mean_time) ** 2) / numpy.sum(weights)
    )


@objecttools.excmessage_decorator(
    "evaluate the simulation results of some node objects"
)
def evaluationtable(
    nodes: Sequence[devicetools.Node],
    criteria: Sequence[Callable],
    nodenames: Optional[Sequence[str]] = None,
    critnames: Optional[Sequence[str]] = None,
    skip_nan: bool = False,
):
    """Return a table containing the results of the given evaluation
    criteria for the given |Node| objects.

    First, we define two nodes with different simulation and observation
    data (see function |prepare_arrays| for some explanations):

    >>> from hydpy import pub, Node, nan
    >>> pub.timegrids = '01.01.2000', '04.01.2000', '1d'
    >>> nodes = Node('test1'), Node('test2')
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
    function |evaluationtable| returns the following table (which is
    a |pandas| |pandas.DataFrame|):

    >>> from hydpy import evaluationtable, corr, bias_abs
    >>> evaluationtable(nodes, (corr, bias_abs))
           corr  bias_abs
    test1   1.0      -3.0
    test2   NaN       NaN

    One can pass alternative names for both the node objects and the
    criteria functions.  Also, `nan` values can be skipped:

    >>> evaluationtable(nodes, (corr, bias_abs),
    ...                 nodenames=('first node', 'second node'),
    ...                 critnames=('corrcoef', 'bias'),
    ...                 skip_nan=True)
                 corrcoef  bias
    first node        1.0  -3.0
    second node      -1.0   0.0

    The number of assigned node objects and criteria functions must
    match the number of given alternative names:

    >>> evaluationtable(nodes, (corr, bias_abs),
    ...                 nodenames=('first node',))
    Traceback (most recent call last):
    ...
    ValueError: While trying to evaluate the simulation results of some \
node objects, the following error occurred: 2 node objects are given \
which does not match with number of given alternative names being 1.

    >>> evaluationtable(nodes, (corr, bias_abs),
    ...                 critnames=('corrcoef',))
    Traceback (most recent call last):
    ...
    ValueError: While trying to evaluate the simulation results of some \
node objects, the following error occurred: 2 criteria functions are given \
which does not match with number of given alternative names being 1.
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
    data = numpy.empty((len(nodes), len(criteria)), dtype=float)
    for idx, node in enumerate(nodes):
        sim, obs = prepare_arrays(
            sim=None,
            obs=None,
            node=node,
            skip_nan=skip_nan,
        )
        for jdx, criterion in enumerate(criteria):
            data[idx, jdx] = criterion(
                sim=sim,
                obs=obs,
            )
    table = pandas.DataFrame(data=data, index=nodenames, columns=critnames)
    return table
