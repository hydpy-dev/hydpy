# -*- coding: utf-8 -*-
"""This module provides features for working with time series."""
# import...
# ...from standard library
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import typingtools

if TYPE_CHECKING:
    import pandas
else:
    pandas = exceptiontools.OptionalImport("pandas", ["pandas"], locals())


@overload
def aggregate_series(
    series: typingtools.VectorInput[float],
    stepsize: Literal["daily", "d"],
    aggregator: Callable,
    basetime: str = ...,
) -> pandas.DataFrame:
    """sim and obs as arguments, daily aggregation"""


@overload
def aggregate_series(
    series: typingtools.VectorInput[float],
    stepsize: Literal["monthly", "m"],
    aggregator: Callable,
) -> pandas.DataFrame:
    """sim and obs as arguments, monthly aggregation"""


@objecttools.excmessage_decorator("aggregate the given series")
def aggregate_series(
    series: typingtools.VectorInput[float],
    stepsize: Literal["daily", "d", "monthly", "m"] = "monthly",
    aggregator: Union[str, Callable] = "mean",
    basetime: str = "00:00",
) -> pandas.DataFrame:
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
    >>> pub.timegrids = "01.11.2000", "01.05.2001", "1d"

    Next, we prepare a |Node| object and assign some constantly increasing
    values to its `simulation` series:

    >>> import numpy
    >>> node = Node("test")
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(1, 181+1)

    |aggregate_series| returns the data within index-sorted |pandas.Series|
    objects (note that the index addresses the left boundary of each time step:

    >>> aggregate_series(series=sim.series)
    2000-11-01     15.5
    2000-12-01     46.0
    2001-01-01     77.0
    2001-02-01    106.5
    2001-03-01    136.0
    2001-04-01    166.5
    Freq: MS, Name: series, dtype: float64

    You can pass another aggregation function:

    >>> aggregate_series(series=sim.series, aggregator=numpy.sum)
    2000-11-01     465.0
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    2001-04-01    4995.0
    Freq: MS, Name: series, dtype: float64

    Functions |aggregate_series| raises errors like the following for
    unsuitable functions:

    >>> def wrong():
    ...     return None
    >>> aggregate_series(series=sim.series, aggregator=wrong)
    Traceback (most recent call last):
    ...
    TypeError: While trying to aggregate the given series, the following \
error occurred: While trying to perform the aggregation based on method \
`wrong`, the following error occurred: wrong() takes 0 positional arguments \
but 1 was given

    When passing a string, |aggregate_series| queries it from |numpy|:

    >>> aggregate_series(series=sim.series, aggregator="sum")
    2000-11-01     465.0
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    2001-04-01    4995.0
    Freq: MS, Name: series, dtype: float64

    |aggregate_series| raises the following error when the requested function
    does not exist:

    >>> aggregate_series(series=sim.series, aggregator="Sum")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Module `numpy` does not provide a function named `Sum`.

    To prevent from wrong conclusions, |aggregate_series| generally ignores all
    data of incomplete intervals:

    >>> pub.timegrids = "30.11.2000", "2.04.2001", "1d"
    >>> node.prepare_simseries()
    >>> sim.series = node.sequences.sim
    >>> sim.series = numpy.arange(30, 152+1)
    >>> aggregate_series(series=sim.series, aggregator="sum")
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    Freq: MS, Name: series, dtype: float64

    The following example shows that even with only one missing value at
    the respective ends of the simulation period, |aggregate_series| does
    not return any result for the first (November 2000) and the last
    aggregation interval (April 2001):

    >>> pub.timegrids = "02.11.2000", "30.04.2001", "1d"
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(2, 180+1)
    >>> aggregate_series(series=sim.series, aggregator="sum")
    2000-12-01    1426.0
    2001-01-01    2387.0
    2001-02-01    2982.0
    2001-03-01    4216.0
    Freq: MS, Name: series, dtype: float64

    Now we prepare a time-grid with an hourly simulation step size, to
    show some examples on daily aggregation:

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "1h"
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(1, 1+4*24)

    By default, function |aggregate_series| aggregates daily from 0 o'clock
    to 0 o'clock, which here results in a loss of the first two and the last
    22 values of the entire period:

    >>> aggregate_series(series=sim.series, stepsize="daily")
    2000-01-02    14.5
    2000-01-03    38.5
    2000-01-04    62.5
    Freq: 86400S, Name: series, dtype: float64

    If you want the aggregation to start at a different time of the day,
    use the `basetime` argument.  In our example, starting at 22 o'clock
    fits the defined initialisation time grid and ensures the usage of
    all available data:

    >>> aggregate_series(series=sim.series, stepsize="daily", basetime="22:00")
    2000-01-01 22:00:00    12.5
    2000-01-02 22:00:00    36.5
    2000-01-03 22:00:00    60.5
    2000-01-04 22:00:00    84.5
    Freq: 86400S, Name: series, dtype: float64

    So far, the `basetime` argument works for daily aggregation only:

    >>> aggregate_series(series=sim.series, stepsize="monthly", basetime="22:00")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Use the `basetime` argument in combination with a `daily` \
aggregation step size only.

    |aggregate_series| does not support aggregation for simulation step
    sizes larger one day:

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "1d"
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(1, 1+4)
    >>> aggregate_series(series=sim.series, stepsize="daily")
    2000-01-01    1.0
    2000-01-02    2.0
    2000-01-03    3.0
    2000-01-04    4.0
    Freq: 86400S, Name: series, dtype: float64

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "2d"
    >>> node.prepare_simseries()
    >>> aggregate_series(series=node.sequences.sim.series, stepsize="daily")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Data aggregation is not supported for simulation step sizes \
greater one day.

    We are looking forward supporting other useful aggregation step sizes later:

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "1d"
    >>> node.prepare_simseries()
    >>> aggregate_series(series=node.sequences.sim.series, stepsize="yearly")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following \
error occurred: Argument `stepsize` received value `yearly`, but only the \
following ones are supported: `monthly` (default) and `daily`.
    """
    if isinstance(aggregator, str):
        try:
            realaggregator = getattr(numpy, aggregator)
        except AttributeError:
            raise ValueError(
                f"Module `numpy` does not provide a function named " f"`{aggregator}`."
            ) from None
    else:
        realaggregator = aggregator
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
    dataframe_orig = pandas.DataFrame()
    dataframe_orig["series"] = numpy.asarray(series)
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
        df_resampled_expanded = resampler.apply(lambda x: realaggregator(x.values))
    except BaseException:
        objecttools.augment_excmessage(
            f"While trying to perform the aggregation based "
            f"on method `{realaggregator.__name__}`"
        )
    # noinspection PyUnboundLocalVariable
    idx0 = df_resampled_expanded.first_valid_index()
    idx1 = df_resampled_expanded.last_valid_index()
    df_resampled_stripped = df_resampled_expanded.loc[idx0:idx1]
    return df_resampled_stripped["series"]
