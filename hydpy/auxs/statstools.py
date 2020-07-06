# -*- coding: utf-8 -*-
"""This module implements statistical functionalities frequently used in
hydrological modelling.
"""
# import...
# ...from standard library
import datetime as datetime_
import warnings
from typing import *
# ...from site-packages
import numpy
import pandas
# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import typingtools
from hydpy.auxs import validtools
pandas = exceptiontools.OptionalImport(
    'pandas', ['pandas'], locals())
optimize = exceptiontools.OptionalImport(
    'optimize', ['scipy.optimize'], locals())
special = exceptiontools.OptionalImport(
    'special', ['scipy.special'], locals())


@overload
def aggregate_series(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        aggregation_step: Union['Period', datetime_.timedelta, str],
        aggregation_type: Union[numpy.mean, numpy.std],
        base: Optional[int] = None,
) -> numpy.ndarray:
    """node as argument"""


@overload
def aggregate_series(
        node: devicetools.Node,
        aggregation_step: Union['Period', datetime_.timedelta, str],
        aggregation_type: Union[numpy.mean, numpy.std],
        base: Optional[int] = None,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'aggregate_series')
def aggregate_series(
        sim=None, obs=None, node=None, aggregation_step=None,
        aggregation_type=None, base=None,
) -> Tuple[pandas.Series, pandas.Series]:
    """Aggregates simulated and observed runoff.

    In order to aggregate data a timegrid corresponding to the runoff data has
    to be defined:

    >>> from hydpy import pub, Node, nan
    >>> pub.timegrids = '01.01.2000 22:00:00', '03.01.2000 22:00:00', '1h'
    >>> node = Node('test')

    Next, we assign values to the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0)
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = (2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0)

    >>> import numpy
    >>> from hydpy import aggregate_series

    Now we can pass the node to object to function |aggregate_series| function.
    As aggregation type any numpy function can be chosen. The aggregation step
    defines the rule for data resampling.

    By default the day begins at 0 o'clock. Incomplete days will be dropped:

    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='24h',
    ...     aggregation_type=numpy.mean,
    ...     )
    >>> obs
    2000-01-02    1.0
    Freq: 24H, Name: obs, dtype: float64
    >>> sim
    2000-01-02    1.083333
    Freq: 24H, Name: sim, dtype: float64

    If the aggregation should start at a different hour of the day it can be
    defined in the 'base' argument:

    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='24h',
    ...     aggregation_type=numpy.mean,
    ...     base=22,
    ...     )
    >>> obs
    2000-01-01    1.083333
    2000-01-02    1.916667
    Freq: 24H, Name: obs, dtype: float64
    >>> sim
    2000-01-01    1.0
    2000-01-02    2.0
    Freq: 24H, Name: sim, dtype: float64

    Instead of nodes also series can be passed:
    >>> obs, sim = aggregate_series(
    ...     sim=node.sequences.sim.series,
    ...     obs=node.sequences.obs.series,
    ...     aggregation_step='24h',
    ...     aggregation_type=numpy.mean,
    ...     base=22,
    ...     )
    >>> obs
    2000-01-01    1.083333
    2000-01-02    1.916667
    Freq: 24H, Name: obs, dtype: float64
    >>> sim
    2000-01-01    1.0
    2000-01-02    2.0
    Freq: 24H, Name: sim, dtype: float64


    >>> pub.timegrids = '01.01.2000', '01.03.2000', '1d'

    Next, we assign values to the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0)
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = (2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0)
    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='M',
    ...     aggregation_type=numpy.mean,
    ...     )
    >>> obs
    2000-01-31    2.0
    2000-02-29    1.0
    Freq: M, Name: obs, dtype: float64
    >>> sim
    2000-01-31    1.0
    2000-02-29    2.0
    Freq: M, Name: sim, dtype: float64

    The 'base' argument is only valid for hourly aggregation step sizes:
    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='M',
    ...     aggregation_type=numpy.mean,
    ...     base = 22
    ...     )
    Traceback (most recent call last):
    ...
    Exception: While trying to aggregate_series, the following error \
occurred: Argument 'base' can only be defined if timestep is smaller than daily

    If we define the aggregation step size bigger than the timestep we get an
    error:
    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='H',
    ...     aggregation_type=numpy.mean,
    ...     )
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate_series, the following error \
occurred: Aggregation step 'H' is bigger than timestep '1d'

    If we define an invalid aggregation step size we also get an error:
    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='2.5h',
    ...     aggregation_type=numpy.mean,
    ...     )
    Traceback (most recent call last):
    ...
    ValueError: While trying to aggregate_series, the following error \
occurred: Invalid aggregation frequency `2.5h`

    If we define an aggregation type as string instead of passing a function
    we also get an error:
    >>> obs, sim = aggregate_series(
    ...     node=node,
    ...     aggregation_step='24h',
    ...     aggregation_type='mean',
    ...     )
    Traceback (most recent call last):
    ...
    TypeError: While trying to aggregate_series, the following error \
occurred: `mean` is not a valid function for aggregation
    """

    if not base:
        base = 0
    elif hydpy.pub.timegrids.stepsize.seconds < 24*60*60:
        base /= hydpy.pub.timegrids.stepsize.timedelta.seconds/(60*60)
    else:
        raise Exception("Argument 'base' can only be defined if timestep is "
                        "smaller than daily")
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=False)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=False)
    dataframe = pandas.DataFrame()
    dataframe['obs'] = obs
    dataframe['sim'] = sim
    timedelta = hydpy.pub.timegrids.stepsize.timedelta
    firstdate = hydpy.pub.timegrids.sim.firstdate.datetime
    lastdate = hydpy.pub.timegrids.sim.lastdate.datetime - timedelta
    index = pandas.date_range(start=firstdate, end=lastdate, freq=timedelta)
    dataframe.index = index
    firstdate_fill = f'{firstdate.year}-{firstdate.month}-01 00:00:00'
    lastdate_fill = (lastdate -
                     pandas.tseries.offsets.Day() +
                     pandas.tseries.offsets.MonthEnd())
    lastdate_fill = f'{lastdate_fill.year}-' \
                    f'{lastdate_fill.month}-' \
                    f'{lastdate_fill.day} ' \
                    f'23:00:00'

    new_index = pandas.date_range(firstdate_fill, lastdate_fill, freq=timedelta)
    dataframe_infilled = dataframe.reindex(new_index, fill_value=numpy.nan)

    if hydpy.pub.timegrids.stepsize.seconds < 24 * 60 * 60:
        dataframe_infilled.index = \
            [ind - base * timedelta for ind in dataframe_infilled.index]

    warnings.filterwarnings("error")
    try:
        df_resample = dataframe_infilled.resample(
            aggregation_step,
        ).apply(lambda x: aggregation_type(x.values))
    except RuntimeWarning:
        warnings.resetwarnings()
        raise ValueError(f"Aggregation step '{aggregation_step}' "
                         f"is bigger than timestep "
                         f"'{hydpy.pub.timegrids.stepsize}'")
    except ValueError:
        warnings.resetwarnings()
        raise ValueError(f'Invalid aggregation frequency `{aggregation_step}`')
    except TypeError:
        warnings.resetwarnings()
        raise TypeError(f'`{aggregation_type}` is not a valid function '
                        f'for aggregation')
    warnings.resetwarnings()
    first_idx = df_resample.first_valid_index()
    last_idx = df_resample.last_valid_index()
    df_mean_valid = df_resample.loc[first_idx:last_idx]

    return df_mean_valid['obs'], df_mean_valid['sim']


@overload
def filter_series_by_date(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        date_ranges: Optional[List[List[str]]],
        months: Optional[List[str]] = None
) -> numpy.ndarray:
    """node as argument"""


@overload
def filter_series_by_date(
        node: devicetools.Node,
        date_ranges: Optional[List[List[str]]],
        months: Optional[List[str]] = None
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'filter series by date')
def filter_series_by_date(
        sim=None, obs=None, node=None, date_ranges=None, months=None
) -> Tuple[pandas.Series, pandas.Series]:
    """Filter time series by dates

    >>> from hydpy import pub, Node, nan
    >>> pub.timegrids = '31.12.1999 22:00:00', '02.01.2000 22:00:00', '1h'
    >>> node = Node('test')

    Next, we assign values to the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0)
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = (2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...     2.0, 2.0)

    To select time periods, a list of lists with start and end dates of the
    periods to extract have to be handed to the date_range argument:

    >>> date_ranges = [['1999-12-31 22:30:00', '2000-01-01 00:00:00'],
    ...                ['2000-01-02 03:00:00', '2000-01-02 05:00:00']]
    >>> obs, sim = filter_series_by_date(node=node, date_ranges=date_ranges)

    The returned series also have a time index which addresses to the right
    boundary of the simulationstep. The value for '2000-01-02 03:00:00' will
    not be returned because it is the value for the timespan between 2 and 3
    o'clack and therefore not within the date range:

    >>> obs
    2000-01-02 04:00:00    2.0
    2000-01-02 05:00:00    2.0
    2000-01-01 00:00:00    2.0
    Name: obs, dtype: float64
    >>> sim
    2000-01-02 04:00:00    2.0
    2000-01-02 05:00:00    2.0
    2000-01-01 00:00:00    1.0
    Name: sim, dtype: float64

    Instead of date ranges also specific months can be defined. Note that even
    if we select december, also the '2000-01-01 00:00:00' value is returned
    because it describes the timestep fron 23 to 24 o'clock of 31st december:

    >>> obs, sim = filter_series_by_date(node=node, months=['12'])
    >>> obs
    1999-12-31 23:00:00    2.0
    2000-01-01 00:00:00    2.0
    Name: obs, dtype: float64
    >>> sim
    1999-12-31 23:00:00    1.0
    2000-01-01 00:00:00    1.0
    Name: sim, dtype: float64

    Alternatively series and a predefined timegrid can be used:

    >>> sim = node.sequences.sim.series
    >>> obs = node.sequences.obs.series

    >>> obs, sim = filter_series_by_date(sim=sim, obs=obs, months=['12'])
    >>> obs
    1999-12-31 23:00:00    2.0
    2000-01-01 00:00:00    2.0
    Name: obs, dtype: float64
    >>> sim
    1999-12-31 23:00:00    1.0
    2000-01-01 00:00:00    1.0
    Name: sim, dtype: float64
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=False)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=False)
    dataframe = pandas.DataFrame()
    dataframe['obs'] = obs
    dataframe['sim'] = sim
    timedelta = hydpy.pub.timegrids.stepsize.timedelta
    dataframe_selected = pandas.DataFrame()
    if date_ranges:
        dates = date_ranges
    elif months:
        dates = months
    for date in dates:
        if date_ranges:
            firstdate = hydpy.pub.timegrids.sim.firstdate.datetime + timedelta
            lastdate = hydpy.pub.timegrids.sim.lastdate.datetime
            index = pandas.date_range(start=firstdate, end=lastdate,
                                      freq=timedelta)
            dataframe.index = index
            selected_date = dataframe.loc[date[0]:date[1]][1:]
        elif months:
            firstdate = hydpy.pub.timegrids.sim.firstdate.datetime
            lastdate = hydpy.pub.timegrids.sim.lastdate.datetime - timedelta
            index = pandas.date_range(start=firstdate, end=lastdate,
                                      freq=timedelta)
            dataframe.index = index
            selected_date = dataframe.loc[dataframe.index.month == int(date)]
            selected_date.index = \
                [ind + timedelta for ind in selected_date.index]
        dataframe_selected = pandas.concat([selected_date, dataframe_selected])
    return dataframe_selected['obs'], dataframe_selected['sim']


@overload
def prepare_arrays(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def prepare_arrays(
        sim: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def prepare_arrays(
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def prepare_arrays(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


def prepare_arrays(sim=None, obs=None, node=None, skip_nan=False):
    """Prepare and return two |numpy| arrays based on the given arguments.

    Note that many functions provided by module |statstools| apply function
    |prepare_arrays| internally (e.g. |nse|).  But you can also apply it
    manually, as shown in the following examples.

    Function |prepare_arrays| can extract time series data from |Node|
    objects.  To set up an example for this, we define a initialization
    time period and prepare a |Node| object:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, nan, nan, nan, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 4.0, 5.0, nan, nan, nan, 6.0

    Now we can pass the node object to function |prepare_arrays| and
    get the (unmodified) time series data:

    >>> from hydpy import prepare_arrays
    >>> arrays = prepare_arrays(node=node)
    >>> round_(arrays[0])
    1.0, nan, nan, nan, 2.0, 3.0
    >>> round_(arrays[1])
    4.0, 5.0, nan, nan, nan, 6.0

    Alternatively, we can pass directly any iterables (e.g. |list| and
    |tuple| objects) containing the `simulated` and `observed` data:

    >>> arrays = prepare_arrays(sim=list(node.sequences.sim.series),
    ...                         obs=tuple(node.sequences.obs.series))
    >>> round_(arrays[0])
    1.0, nan, nan, nan, 2.0, 3.0
    >>> round_(arrays[1])
    4.0, 5.0, nan, nan, nan, 6.0

    The optional `skip_nan` flag allows to skip all values, which are
    no numbers.  Note that only those pairs of `simulated` and `observed`
    values are returned which do not contain any `nan`:

    >>> arrays = prepare_arrays(node=node, skip_nan=True)
    >>> round_(arrays[0])
    1.0, 3.0
    >>> round_(arrays[1])
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
                'Values are passed to both arguments `sim` and `node`, '
                'which is not allowed.')
        if obs is not None:
            raise ValueError(
                'Values are passed to both arguments `obs` and `node`, '
                'which is not allowed.')
        sim = node.sequences.sim.series
        obs = node.sequences.obs.series
    elif (sim is not None) and (obs is None):
        raise ValueError(
            'A value is passed to argument `sim` '
            'but no value is passed to argument `obs`.')
    elif (obs is not None) and (sim is None):
        raise ValueError(
            'A value is passed to argument `obs` '
            'but no value is passed to argument `sim`.')
    elif (sim is None) and (obs is None):
        raise ValueError(
            'Neither a `Node` object is passed to argument `node` nor '
            'are arrays passed to arguments `sim` and `obs`.')
    sim = numpy.asarray(sim)
    obs = numpy.asarray(obs)
    if skip_nan:
        idxs = ~numpy.isnan(sim) * ~numpy.isnan(obs)
        sim = sim[idxs]
        obs = obs[idxs]
    return sim, obs


@overload
def nse(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def nse(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the Nash-Sutcliffe efficiency')
def nse(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the efficiency criteria after Nash & Sutcliffe.

    If the simulated values predict the observed values as well
    as the average observed value (regarding the the mean square
    error), the NSE value is zero:

    >>> from hydpy import nse
    >>> nse(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0])
    0.0
    >>> nse(sim=[0.0, 2.0, 4.0], obs=[1.0, 2.0, 3.0])
    0.0

    For worse and better simulated values the NSE is negative
    or positive, respectively:

    >>> nse(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0])
    -3.0
    >>> nse(sim=[1.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0])
    0.5

    The highest possible value is one:

    >>> nse(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(nse(node=node))
    0.090909

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |nse|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    return 1.-numpy.sum((sim-obs)**2)/numpy.sum((obs-numpy.mean(obs))**2)


@overload
def nse_log(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def nse_log(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the log-Nash-Sutcliffe efficiency')
def nse_log(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the efficiency criteria after Nash & Sutcliffe for
    logarithmic values.

    For worse and better simulated values the NSE is negative
    or positive, respectively:

    >>> from hydpy import nse_log
    >>> from hydpy import round_
    >>> round_(nse_log(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -2.910616
    >>> round_(nse_log(sim=[1.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.733662

    The highest possible value is one:

    >>> nse_log(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(nse_log(node=node))
    0.104811

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |nse_log|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)

    return (1.-numpy.sum((numpy.log(sim)-numpy.log(obs))**2) /
            numpy.sum((numpy.log(obs)-numpy.mean(numpy.log(obs)))**2))


@overload
def r_squared(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def r_squared(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the R²-Error')
def r_squared(sim=None, obs=None, node=None, skip_nan=False):
    """The coefficient of determination r² is defined as the squared
    value of the coefficient of correlation according to Bravais-Pearson.

    >>> from hydpy import r_squared
    >>> from hydpy import round_
    >>> r_squared(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0
    >>> r_squared(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0])
    1.0
    >>> round_(r_squared(sim=[2.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    0.75

    Take care if there is no variation in one of the data series the
    correlation coefficient and therefore also R² will return nan-values.
    >>> r_squared(sim=[2.0, 2.0, 2.0], obs=[2.0, 2.0, 3.0])
    nan

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(r_squared(node=node))
    0.409091

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |r_squared|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)

    return numpy.corrcoef(sim, obs)[0, 1]**2


@overload
def kge(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def kge(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the Kling-Gupta-Efficiency')
def kge(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the Kling-Gupta efficiency :cite:`ref-Kling2012`.

    >>> from hydpy import  kge
    >>> from hydpy import round_
    >>> kge(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0])
    1.0
    >>> kge(sim=[3.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0])
    -3.0
    >>> round_(kge(sim=[2.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -2.688461

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(kge(node=node))
    0.808446

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |kge|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)

    return (1 - numpy.sum(
        (numpy.corrcoef(sim, obs)[0, 1] - 1)**2 +
        (numpy.std(sim)/numpy.std(obs) - 1)**2 +
        (numpy.mean(sim)/numpy.mean(obs) - 1)**2))


@overload
def bias_abs(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def bias_abs(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the absolute bias')
def bias_abs(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the absolute difference between the means of the simulated
    and the observed values.

    >>> from hydpy import round_
    >>> from hydpy import bias_abs
    >>> round_(bias_abs(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.0
    >>> round_(bias_abs(sim=[5.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    1.0
    >>> round_(bias_abs(sim=[1.0, 1.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -1.0

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(bias_abs(node=node))
    -0.5

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |bias_abs|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    return numpy.mean(sim-obs)


@overload
def bias_rel(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def bias_rel(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the relative bias')
def bias_rel(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the relative difference between the means of the simulated
    and the observed values.

    >>> from hydpy import round_
    >>> from hydpy import bias_rel
    >>> round_(bias_rel(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.0
    >>> round_(bias_rel(sim=[5.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    0.5
    >>> round_(bias_rel(sim=[1.0, 1.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -0.5

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(bias_rel(node=node))
    -0.2

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |bias_rel|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    return numpy.mean(sim)/numpy.mean(obs)-1.


@overload
def std_ratio(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def std_ratio(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the standard deviation ratio')
def std_ratio(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the ratio between the standard deviation of the simulated
    and the observed values.

    >>> from hydpy import round_
    >>> from hydpy import std_ratio
    >>> round_(std_ratio(sim=[1.0, 2.0, 3.0], obs=[1.0, 2.0, 3.0]))
    0.0
    >>> round_(std_ratio(sim=[1.0, 1.0, 1.0], obs=[1.0, 2.0, 3.0]))
    -1.0
    >>> round_(std_ratio(sim=[0.0, 3.0, 6.0], obs=[1.0, 2.0, 3.0]))
    2.0

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(std_ratio(node=node))
    -0.147197

    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |std_ratio|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    return numpy.std(sim)/numpy.std(obs)-1.


@overload
def corr(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def corr(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the Pearson correlation coefficient')
def corr(sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the product-moment correlation coefficient after Pearson.

    >>> from hydpy import round_
    >>> from hydpy import corr
    >>> round_(corr(sim=[0.5, 1.0, 1.5], obs=[1.0, 2.0, 3.0]))
    1.0
    >>> round_(corr(sim=[4.0, 2.0, 0.0], obs=[1.0, 2.0, 3.0]))
    -1.0
    >>> round_(corr(sim=[1.0, 2.0, 1.0], obs=[1.0, 2.0, 3.0]))
    0.0

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(corr(node=node))
    0.639602

    Take care if there is no variation in one of the data series the
    correlation coefficient will return nan-values.
    >>> round_(corr(sim=[2.0, 2.0, 2.0], obs=[1.0, 2.0, 3.0]))
    nan


    See the documentation on function |prepare_arrays| for some
    additional instructions for use of function |corr|.
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    return numpy.corrcoef(sim, obs)[0, 1]


def _pars_sepd(xi, beta):
    gamma1 = special.gamma(3.*(1.+beta)/2.)
    gamma2 = special.gamma((1.+beta)/2.)
    w_beta = gamma1**.5 / (1.+beta) / gamma2**1.5
    c_beta = (gamma1/gamma2)**(1./(1.+beta))
    m_1 = special.gamma(1.+beta) / gamma1**.5 / gamma2**.5
    m_2 = 1.
    mu_xi = m_1*(xi-1./xi)
    sigma_xi = numpy.sqrt((m_2-m_1**2)*(xi**2+1./xi**2)+2*m_1**2-m_2)
    return mu_xi, sigma_xi, w_beta, c_beta


def _pars_h(sigma1, sigma2, sim):
    return sigma1*numpy.mean(sim) + sigma2*sim


@overload
def hsepd_pdf(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def hsepd_pdf(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the probability densities with the '
    'heteroskedastic skewed exponential power distribution')
def hsepd_pdf(sigma1, sigma2, xi, beta,
              sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the probability densities based on the
    heteroskedastic skewed exponential power distribution.

    For convenience, the required parameters of the probability density
    function as well as the simulated and observed values are stored
    in a dictonary:

    >>> import numpy
    >>> from hydpy import round_
    >>> from hydpy import hsepd_pdf
    >>> general = {'sigma1': 0.2,
    ...            'sigma2': 0.0,
    ...            'xi': 1.0,
    ...            'beta': 0.0,
    ...            'sim': numpy.arange(10.0, 41.0),
    ...            'obs': numpy.full(31, 25.0)}

    The following test function allows the variation of one parameter
    and prints some and plots all of probability density values
    corresponding to different simulated values:

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

    When varying parameter `beta`, the resulting probabilities correspond
    to the Laplace distribution (1.0), normal distribution (0.0), and the
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

    When varying parameter `xi`, the resulting density is negatively
    skewed (0.2), symmetric (1.0), and positively skewed (5.0),
    respectively:

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

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(hsepd_pdf(sigma1=general['sigma1'], sigma2=general['sigma2'],
    ...     xi=general['xi'], beta=general['beta'], node=node, skip_nan=False))
    0.997356, 0.043821, 0.043821, 0.043821, 0.043821, 0.043821
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    sigmas = _pars_h(sigma1, sigma2, sim)
    mu_xi, sigma_xi, w_beta, c_beta = _pars_sepd(xi, beta)
    x, mu = obs, sim
    a = (x-mu)/sigmas
    a_xi = numpy.empty(a.shape)
    idxs = mu_xi+sigma_xi*a < 0.
    a_xi[idxs] = numpy.absolute(xi*(mu_xi+sigma_xi*a[idxs]))
    a_xi[~idxs] = numpy.absolute(1./xi*(mu_xi+sigma_xi*a[~idxs]))
    ps = (2.*sigma_xi/(xi+1./xi)*w_beta *
          numpy.exp(-c_beta*a_xi**(2./(1.+beta))))/sigmas
    return ps


def _hsepd_manual(sigma1, sigma2, xi, beta, sim, obs):
    ps = hsepd_pdf(sigma1, sigma2, xi, beta, sim, obs)
    ps[ps < 1e-200] = 1e-200
    return numpy.mean(numpy.log(ps))


@overload
def hsepd_manual(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def hsepd_manual(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate an objective value based on method `hsepd_manual`')
def hsepd_manual(sigma1, sigma2, xi, beta,
                 sim=None, obs=None, node=None, skip_nan=False):
    """Calculate the mean of the logarithmised probability densities of the
    'heteroskedastic skewed exponential power distribution.

    The following examples are taken from the documentation of function
    |hsepd_pdf|, which is used by function |hsepd_manual|.  The first
    one deals with a heteroscedastic normal distribution:

    >>> from hydpy import round_
    >>> from hydpy import hsepd_manual
    >>> round_(hsepd_manual(sigma1=0.2, sigma2=0.2,
    ...                     xi=1.0, beta=0.0,
    ...                     sim=numpy.arange(10.0, 41.0),
    ...                     obs=numpy.full(31, 25.0)))
    -3.682842

    The second one is supposed to show to small zero probability density
    values are set to 1e-200 before calculating their logarithm (which
    means that the lowest possible value returned by function
    |hsepd_manual| is approximately -460):

    >>> round_(hsepd_manual(sigma1=0.2, sigma2=0.0,
    ...                     xi=1.0, beta=-0.99,
    ...                     sim=numpy.arange(10.0, 41.0),
    ...                     obs=numpy.full(31, 25.0)))
    -209.539335

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> round_(hsepd_manual(sigma1=0.2, sigma2=0.0,
    ...                     xi=1.0, beta=-0.99,
    ...                     node=node))
    -383.818532
    """
    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    return _hsepd_manual(sigma1, sigma2, xi, beta, sim, obs)


@overload
def hsepd(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def hsepd(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate an objective value based on method `hsepd`')
def hsepd(sim=None, obs=None, node=None, skip_nan=False,
          inits=None, return_pars=False, silent=True):
    """Calculate the mean of the logarithmised probability densities of the
    'heteroskedastic skewed exponential power distribution.

    Function |hsepd| serves the same purpose as function |hsepd_manual|,
    but tries to estimate the parameters of the heteroscedastic skewed
    exponential distribution via an optimization algorithm.  This
    is shown by generating a random sample.  1000 simulated values
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
    `sigma1` (0.2), , `sigma2` (0.0), `xi` (1.0), and `beta` (0.0).
    The estimated values are returned in the mentioned order through
    enabling the `return_pars` option:

    >>> value, pars = hsepd(sim=sim, obs=obs, return_pars=True)
    >>> round_(pars, decimals=5)
    0.19966, 0.0, 0.96836, 0.0188

    There is no guarantee that the optimization numerical optimization
    algorithm underlying function |hsepd| will always find the parameters
    resulting in the largest value returned by function |hsepd_manual|.
    You can increase its robustness (and decrease computation time) by
    supplying good initial parameter values:

    >>> value, pars = hsepd(sim=sim, obs=obs, return_pars=True,
    ...                     inits=(0.2, 0.0, 1.0, 0.0))
    >>> round_(pars, decimals=5)
    0.19966, 0.0, 0.96836, 0.0188

    However, the following example shows a case when this strategie
    results in worse results:

    >>> value, pars = hsepd(sim=sim, obs=obs, return_pars=True,
    ...                     inits=(0.0, 0.2, 1.0, 0.0))
    >>> round_(value)
    -2.174492
    >>> round_(pars)
    0.0, 0.213179, 1.705485, 0.505112

    Alternatively a node can be used as input:

    >>> from hydpy import pub, Node, round_, nan
    >>> pub.timegrids = '01.01.2000', '07.01.2000', '1d'
    >>> node = Node('test')

    Next, we assign values the `simulation` and the `observation` sequences
    (to do so for the `observation` sequence requires a little trick, as
    its values are normally supposed to be read from a file):

    >>> node.prepare_simseries()
    >>> with pub.options.checkseries(False):
    ...     node.sequences.sim.series = 1.0, 2.0, 1.0, 3.0, 2.0, 3.0
    ...     node.sequences.obs.activate_ram()
    ...     node.sequences.obs.series = 1.0, 3.0, 2.0, 2.0, 3.0, 4.0

    >>> value, pars = hsepd(node=node, return_pars=True,
    ...                     inits=(0.0, 0.2, 1.0, 0.0))
    >>> round_(value)
    -1.121904
    >>> round_(pars)
    0.0, 0.904799, 0.387431, 3.231805
    """

    def transform(pars):
        """Transform the actual optimization problem into a function to
        be minimized and apply parameter constraints."""
        sigma1, sigma2, xi, beta = constrain(*pars)
        return -_hsepd_manual(sigma1, sigma2, xi, beta, sim, obs)

    def constrain(sigma1, sigma2, xi, beta):
        """Apply constrains on the given parameter values."""
        sigma1 = numpy.clip(sigma1, 0.0, None)
        sigma2 = numpy.clip(sigma2, 0.0, None)
        xi = numpy.clip(xi, 0.1, 10.0)
        beta = numpy.clip(beta, -0.99, 5.0)
        return sigma1, sigma2, xi, beta

    if not node:
        sim, obs = prepare_arrays(sim=sim, obs=obs, skip_nan=skip_nan)
    else:
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
    if not inits:
        inits = [0.1, 0.2, 3.0, 1.0]
    values = optimize.fmin(transform, inits,
                           ftol=1e-12, xtol=1e-12,
                           disp=not silent)
    values = constrain(*values)
    result = _hsepd_manual(*values, sim=sim, obs=obs)
    if return_pars:
        return result, values
    return result


@overload
def calc_mean_time(
        sim: typingtools.Vector,
        obs: typingtools.Vector,
        skip_nan: bool,
) -> numpy.ndarray:
    """node as argument"""


@overload
def calc_mean_time(
        node: devicetools.Node,
        skip_nan: bool,
) -> numpy.ndarray:
    """sim and obs as argument"""


@objecttools.excmessage_decorator(
    'calculate the weighted mean time')
def calc_mean_time(timepoints, weights):
    """Return the weighted mean of the given timepoints.

    With equal given weights, the result is simply the mean of the given
    time points:

    >>> from hydpy import calc_mean_time
    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[2., 2.])
    5.0

    With different weights, the resulting mean time is shifted to the larger
    ones:

    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[1., 3.])
    6.0

    Or, in the most extreme case:

    >>> calc_mean_time(timepoints=[3., 7.],
    ...                weights=[0., 4.])
    7.0

    There will be some checks for input plausibility perfomed, e.g.:

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
    return numpy.dot(timepoints, weights)/numpy.sum(weights)


@objecttools.excmessage_decorator(
    'calculate the weighted time deviation from mean time')
def calc_mean_time_deviation(timepoints, weights, mean_time=None):
    """Return the weighted deviation of the given timepoints from their mean
    time.

    With equal given weights, the is simply the standard deviation of the
    given time points:

    >>> from hydpy import calc_mean_time_deviation
    >>> calc_mean_time_deviation(timepoints=[3., 7.],
    ...                          weights=[2., 2.])
    2.0

    One can pass a precalculated or alternate mean time:

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

    There will be some checks for input plausibility perfomed, e.g.:

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
    return (numpy.sqrt(numpy.dot(weights, (timepoints-mean_time)**2) /
                       numpy.sum(weights)))


@objecttools.excmessage_decorator(
    'evaluate the simulation results of some node objects')
def evaluationtable(nodes, criteria, nodenames=None,
                    critnames=None, skip_nan=False):
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
    actually a pandas data frame):

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
    match the number of givern alternative names:

    >>> evaluationtable(nodes, (corr, bias_abs),
    ...                 nodenames=('first node',))
    Traceback (most recent call last):
    ...
    ValueError: While trying to evaluate the simulation results of some \
node objects, the following error occurred: 2 node objects are given \
which does not match with number of given alternative names beeing 1.

    >>> evaluationtable(nodes, (corr, bias_abs),
    ...                 critnames=('corrcoef',))
    Traceback (most recent call last):
    ...
    ValueError: While trying to evaluate the simulation results of some \
node objects, the following error occurred: 2 criteria functions are given \
which does not match with number of given alternative names beeing 1.
    """
    if nodenames:
        if len(nodes) != len(nodenames):
            raise ValueError(
                '%d node objects are given which does not match with '
                'number of given alternative names beeing %s.'
                % (len(nodes), len(nodenames)))
    else:
        nodenames = [node.name for node in nodes]
    if critnames:
        if len(criteria) != len(critnames):
            raise ValueError(
                '%d criteria functions are given which does not match '
                'with number of given alternative names beeing %s.'
                % (len(criteria), len(critnames)))
    else:
        critnames = [crit.__name__ for crit in criteria]
    data = numpy.empty((len(nodes), len(criteria)), dtype=float)
    for idx, node in enumerate(nodes):
        sim, obs = prepare_arrays(node=node, skip_nan=skip_nan)
        for jdx, criterion in enumerate(criteria):
            data[idx, jdx] = criterion(sim, obs)
    table = pandas.DataFrame(
        data=data, index=nodenames, columns=critnames)
    return table
