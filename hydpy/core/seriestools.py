"""This module provides features for working with time series."""

# import...
# ...from standard library
from __future__ import annotations

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    import pandas
else:
    pandas = exceptiontools.OptionalImport("pandas", ["pandas"], locals())


@overload
def aggregate_series(
    *,
    series: NDArrayFloat,
    stepsize: Literal["daily", "d"],
    aggregator: Union[str, Callable[[NDArrayFloat], float]] = "mean",
    subperiod: bool = True,
    basetime: str = "00:00",
) -> pandas.DataFrame:
    """sim and obs as arguments, daily aggregation"""


@overload
def aggregate_series(
    *,
    series: NDArrayFloat,
    stepsize: Literal["monthly", "m"],
    aggregator: Union[str, Callable[[NDArrayFloat], float]] = "mean",
    subperiod: bool = True,
) -> pandas.DataFrame:
    """sim and obs as arguments, monthly aggregation"""


@objecttools.excmessage_decorator("aggregate the given series")
def aggregate_series(
    series: NDArrayFloat,
    stepsize: StepSize = "monthly",
    aggregator: Union[str, Callable[[NDArrayFloat], float]] = "mean",
    subperiod: bool = True,
    basetime: str = "00:00",
) -> pandas.DataFrame:
    """Aggregate the time series on a monthly or daily basis.

    Often, we need some aggregation before analysing deviations between simulation
    results and observations.  Function |aggregate_series| performs such aggregation on
    a monthly or daily basis.  You are free to specify arbitrary aggregation functions.

    We first show the default behaviour of function |aggregate_series|, which is to
    calculate monthly averages.  Therefore, we first say the hydrological summer
    half-year 2001 to be our simulation period and define a daily simulation step size:

    >>> from hydpy import aggregate_series, pub, Node
    >>> pub.timegrids = "01.11.2000", "01.05.2001", "1d"

    Next, we prepare a |Node| object and assign some constantly increasing values to
    its `simulation` series:

    >>> import numpy
    >>> node = Node("test")
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(1, 181+1)

    |aggregate_series| returns the data within index-sorted |pandas.Series| objects
    (note that the index addresses the left boundary of each time step:

    >>> aggregate_series(series=sim.series)
                series
    2000-11-01    15.5
    2000-12-01    46.0
    2001-01-01    77.0
    2001-02-01   106.5
    2001-03-01   136.0
    2001-04-01   166.5

    The following example shows how to restrict the considered period via the
    |Timegrids.eval_| |Timegrid| of the |Timegrids| object available in the |pub|
    module and pass a different aggregation function:

    >>> pub.timegrids.eval_.dates = "2001-01-01", "2001-03-01"
    >>> aggregate_series(series=sim.series, aggregator=numpy.sum)
                series
    2001-01-01  2387.0
    2001-02-01  2982.0

    Even for short evaluation periods, the passed data must still cover the correspond
    to the complete initialisation period:

    >>> pub.timegrids.eval_.dates = "2001-01-01", "2001-03-01"
    >>> aggregate_series(series=sim.evalseries, aggregator=numpy.sum)
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following error \
occurred: The length of the passed vector (59) differs from the length of the \
initialisation time grid (181).

    Functions |aggregate_series| raises errors like the following for unsuitable
    functions:

    >>> def wrong(values):
    ...     assert False, "wrong function"
    >>> aggregate_series(series=sim.series, aggregator=wrong)
    Traceback (most recent call last):
    ...
    AssertionError: While trying to aggregate the given series, the following error \
occurred: While trying to perform the aggregation based on method `wrong`, the \
following error occurred: wrong function

    When passing a string, |aggregate_series| queries it from |numpy|:

    >>> pub.timegrids.eval_.dates = "2001-01-01", "2001-02-01"
    >>> aggregate_series(series=sim.series, aggregator="sum")
                series
    2001-01-01  2387.0

    |aggregate_series| raises the following error when the requested function does not
    exist:

    >>> aggregate_series(series=sim.series, aggregator="Sum")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following error \
occurred: Module `numpy` does not provide a function named `Sum`.

    To prevent from wrong conclusions, |aggregate_series| generally ignores all data of
    incomplete intervals:

    >>> pub.timegrids = "2000-11-30", "2001-04-02", "1d"
    >>> node.prepare_simseries()
    >>> sim.series = numpy.arange(30, 152+1)
    >>> sim = node.sequences.sim
    >>> aggregate_series(series=sim.series, aggregator="sum")
                series
    2000-12-01  1426.0
    2001-01-01  2387.0
    2001-02-01  2982.0
    2001-03-01  4216.0

    >>> pub.timegrids.eval_.dates = "2001-01-02", "2001-02-28"
    >>> aggregate_series(series=sim.series)
    Empty DataFrame
    Columns: [series]
    Index: []

    If you want to analyse the data of the complete initialisation period independently
    of the state of |Timegrids.eval_|, set argument `subperiod` to |False|:

    >>> aggregate_series(series=sim.series, aggregator="sum", subperiod=False)
                series
    2000-12-01  1426.0
    2001-01-01  2387.0
    2001-02-01  2982.0
    2001-03-01  4216.0

    The following example shows that even with only one missing value at the respective
    ends of the simulation period, |aggregate_series| does not return any result for
    the first (November 2000) and the last aggregation interval (April 2001):

    >>> pub.timegrids = "02.11.2000", "30.04.2001", "1d"
    >>> node.prepare_simseries()
    >>> sim.series = numpy.arange(2, 180+1)
    >>> aggregate_series(series=node.sequences.sim.series)
                series
    2000-12-01    46.0
    2001-01-01    77.0
    2001-02-01   106.5
    2001-03-01   136.0

    Now we prepare a time grid with an hourly simulation step size to show some
    examples of daily aggregation:

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "1h"
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(1, 1+4*24)

    By default, function |aggregate_series| aggregates daily from 0 o'clock to
    0 o'clock, resulting in a loss of the first two and the last 22 values of the
    entire period:

    >>> aggregate_series(series=sim.series, stepsize="daily")
                series
    2000-01-02    14.5
    2000-01-03    38.5
    2000-01-04    62.5

    If you want the aggregation to start at a different time of the day, use the
    `basetime` argument.  In our example, starting at 22 o'clock fits the defined
    initialisation time grid and ensures the usage of all available data:

    >>> aggregate_series(series=sim.series, stepsize="daily", basetime="22:00")
                         series
    2000-01-01 22:00:00    12.5
    2000-01-02 22:00:00    36.5
    2000-01-03 22:00:00    60.5
    2000-01-04 22:00:00    84.5

    So far, the `basetime` argument works for daily aggregation only:

    >>> aggregate_series(series=sim.series, stepsize="monthly", basetime="22:00")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following error \
occurred: Use the `basetime` argument in combination with a `daily` aggregation step \
size only.

    |aggregate_series| does not support aggregation for simulation step sizes larger
    one day:

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "1d"
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.arange(1, 1+4)
    >>> aggregate_series(series=sim.series, stepsize="daily")
                series
    2000-01-02     2.0
    2000-01-03     3.0
    2000-01-04     4.0

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "2d"
    >>> node.prepare_simseries()
    >>> aggregate_series(series=node.sequences.sim.series, stepsize="daily")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following error \
occurred: Data aggregation is not supported for simulation step sizes greater one day.

    We are looking forward supporting other useful aggregation step sizes later:

    >>> pub.timegrids = "01.01.2000 22:00", "05.01.2000 22:00", "1d"
    >>> node.prepare_simseries()
    >>> aggregate_series(series=node.sequences.sim.series, stepsize="yearly")
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate the given series, the following error \
occurred: Argument `stepsize` received value `yearly`, but only the following ones \
are supported: `monthly` (default) and `daily`.
    """
    timegrids: timetools.Timegrids = hydpy.pub.timegrids
    if isinstance(aggregator, str):
        try:
            realaggregator = getattr(numpy, aggregator)
        except AttributeError:
            raise ValueError(
                f"Module `numpy` does not provide a function named " f"`{aggregator}`."
            ) from None
    else:
        realaggregator = aggregator
    tg = timegrids.eval_ if subperiod else timegrids.init
    if tg.stepsize > "1d":
        raise ValueError(
            "Data aggregation is not supported for simulation step sizes greater one "
            "day."
        )
    if stepsize in ("d", "daily"):
        rule = "86400s"
        dt = timetools.Date(f"2000-01-01 {basetime}") - timetools.Date("2000-01-01")
        offset = dt.seconds
    elif basetime != "00:00":
        raise ValueError(
            "Use the `basetime` argument in combination with a `daily` aggregation "
            "step size only."
        )
    elif stepsize in ("m", "monthly"):
        rule = "MS"
        offset = 0
    else:
        raise ValueError(
            f"Argument `stepsize` received value `{stepsize}`, but only the following "
            f"ones are supported: `monthly` (default) and `daily`."
        )
    if len(series) != len(timegrids.init):
        raise ValueError(
            f"The length of the passed vector ({len(series)}) differs from the length "
            f"of the initialisation time grid ({len(timegrids.init)})."
        )
    dataframe_orig = pandas.DataFrame()
    idx0, idx1 = timegrids.evalindices if subperiod else timegrids.initindices
    dataframe_orig["series"] = numpy.asarray(series)[idx0:idx1]
    dataframe_orig.index = pandas.date_range(
        start=tg.firstdate.datetime,
        end=(tg.lastdate - tg.stepsize).datetime,
        freq=tg.stepsize.timedelta,
    )
    resampler = dataframe_orig.resample(rule=rule, offset=f"{offset}s")
    try:
        dataframe_resampled = resampler.apply(lambda x: realaggregator(x.values))
    except BaseException:
        objecttools.augment_excmessage(
            f"While trying to perform the aggregation based on method "
            f"`{realaggregator.__name__}`"
        )
    for jdx0, date0 in enumerate(dataframe_resampled.index):
        if date0 >= tg.firstdate:
            break
    for jdx1, date1 in enumerate(reversed(dataframe_resampled.index)):
        date = timetools.Date(date1)
        if stepsize in ("daily", "d"):
            date += "1d"
        else:
            date = date.beginning_next_month
        if date <= tg.lastdate:
            jdx1 = len(dataframe_resampled) - jdx1
            break
    # pylint: disable=undefined-loop-variable
    # the dataframe index above cannot be empty
    return dataframe_resampled[jdx0:jdx1]
