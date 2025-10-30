"""This module implements tools to determine time-related indices."""

# import...
# ...from standard library
from __future__ import annotations
import copy

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import timetools
from hydpy.core.typingtools import *


Date2Float: TypeAlias = Callable[[timetools.Date], float]


def _get_timegrids(func: Date2Float) -> timetools.Timegrids:
    timegrids = exceptiontools.getattr_(hydpy.pub, "timegrids", None)
    if timegrids is None:
        name = func.__name__[1:]
        raise exceptiontools.AttributeNotReady(
            f"An Indexer object has been asked for an `{name}` array.  Such an array "
            f"has neither been determined yet nor can it be determined automatically "
            f"at the moment.  Either define an `{name}` array manually and pass it to "
            f"the Indexer object, or make a proper Timegrids object available within "
            f"the pub module."
        )
    return timegrids


class IndexerProperty(propertytools.BaseProperty):
    """A property for handling time-related indices.

    Some models (e.g. |lland_dd|) require time related index values. |IndexerProperty|
    provides some caching functionalities to avoid recalculating the same indices for
    different model instances over and over again.  We illustrate this by taking
    property |Indexer.monthofyear| as an example.

    Generally, |Indexer| needs to know the relevant initialisation period before being
    able to calculate any time-related index values.  If you forget to define one first,
    you get the following error message:

    >>> from hydpy import print_vector, pub
    >>> pub.indexer.monthofyear
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: An Indexer object has been asked for \
an `monthofyear` array.  Such an array has neither been determined yet nor can it be \
determined automatically at the moment.  Either define an `monthofyear` array manually \
and pass it to the Indexer object, or make a proper Timegrids object available within \
the pub module.

    For efficiency, repeated querying of |Indexer.monthofyear| returns the same |numpy|
    |numpy.array| object:

    >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
    >>> monthofyear = pub.indexer.monthofyear
    >>> print_vector(monthofyear)
    1, 1, 1, 2, 2
    >>> print_vector(pub.indexer.monthofyear)
    1, 1, 1, 2, 2
    >>> pub.indexer.monthofyear is monthofyear
    True

    When the |Timegrids| object handled by module |pub| changes, |IndexerProperty|
    calculates and returns a new index array:

    >>> pub.timegrids.init.firstdate += "1d"
    >>> print_vector(pub.indexer.monthofyear)
    1, 1, 2, 2
    >>> pub.indexer.monthofyear is monthofyear
    False

    When in doubt, you can manually delete the cached |numpy| |numpy.ndarray| and
    receive a freshly calculated index array afterwards:

    >>> monthofyear = pub.indexer.monthofyear
    >>> pub.indexer.monthofyear is monthofyear
    True
    >>> del pub.indexer.monthofyear
    >>> print_vector(pub.indexer.monthofyear)
    1, 1, 2, 2
    >>> pub.indexer.monthofyear is monthofyear
    False

    You are allowed to define alternative values manually, which seems advisable only
    for testing purposes:

    >>> pub.indexer.monthofyear = 0, 1, 2, 3
    >>> print_vector(pub.indexer.monthofyear)
    0, 1, 2, 3
    >>> pub.timegrids.init.firstdate -= "1d"
    >>> print_vector(pub.indexer.monthofyear)
    1, 1, 1, 2, 2

    When assigning inadequate data, you get errors like the following:

    >>> pub.indexer.monthofyear = 1
    Traceback (most recent call last):
    ...
    TypeError: While trying to assign a new `monthofyear` index array to an Indexer \
object, the following error occurred: 'int' object is not subscriptable

    >>> pub.indexer.monthofyear = [[0, 1, 2, 3], [4, 5, 6, 7]]
    Traceback (most recent call last):
    ...
    ValueError: The `monthofyear` index array of an Indexer object must be \
1-dimensional.  However, the given value has interpreted as a 2-dimensional object.

    >>> pub.indexer.monthofyear = 0, 1, 2, 3
    Traceback (most recent call last):
    ...
    ValueError: The `monthofyear` index array of an Indexer object must have a number \
of entries fitting to the initialization time period precisely.  However, the given \
value has been interpreted to be of length `4` and the length of the Timegrid object \
representing the actual initialisation period is `5`.
    """

    timegrids: timetools.Timegrids | None
    values: VectorFloat | None

    def __init__(self, fget: Callable[[Indexer], Date2Float]) -> None:
        super().__init__()
        self.fget = fget
        self.fset = self._fset
        self.fdel = self._fdel
        self.__doc__ = fget.__doc__
        self.values = None
        self.timegrids = None

    def call_fget(self, obj: Indexer) -> NDArrayFloat:
        timegrids = exceptiontools.getattr_(hydpy.pub, "timegrids", None)
        if (self.values is None) or (self.timegrids != timegrids):
            self.values = self._calcidxs(self.fget(obj))
            self.timegrids = copy.deepcopy(timegrids)
        return self.values

    def call_fset(self, obj: Indexer, value: VectorInputFloat) -> None:
        self._fset(obj, value)

    def _fset(  # pylint: disable=unused-argument
        self, obj: Indexer, values: VectorInputFloat
    ) -> None:
        self.values = self._convertandtest(values, self.name)
        self.timegrids = copy.deepcopy(exceptiontools.getattr_(hydpy.pub, "timegrids"))

    def call_fdel(self, obj: Indexer) -> None:
        self.fdel(obj)

    def _fdel(self, obj: Indexer) -> None:  # pylint: disable=unused-argument
        self.values = None
        self.timegrids = None

    @staticmethod
    def _convertandtest(values: VectorInputFloat, name: str) -> VectorFloat:
        try:
            type_ = type(values[0])
            array: NDArrayFloat = numpy.asarray(
                values, dtype=config.TYPES_PY2NP.get(type_, type_)
            )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to assign a new `{name}` index array to an Indexer "
                f"object"
            )
        if array.ndim != 1:
            raise ValueError(
                f"The `{name}` index array of an Indexer object must be "
                f"1-dimensional.  However, the given value has interpreted as a "
                f"{array.ndim}-dimensional object."
            )
        timegrids = exceptiontools.getattr_(hydpy.pub, "timegrids")
        if timegrids is not None:
            if len(array) != len(timegrids.init):
                raise ValueError(
                    f"The `{name}` index array of an Indexer object must have a number "
                    f"of entries fitting to the initialization time period precisely.  "
                    f"However, the given value has been interpreted to be of length "
                    f"`{len(array)}` and the length of the Timegrid object "
                    f"representing the actual initialisation period is "
                    f"`{len(timegrids.init)}`."
                )
        return array

    @staticmethod
    def _calcidxs(func: Date2Float) -> VectorFloat:
        timegrids = _get_timegrids(func)
        type_ = type(func(timegrids.init[0]))
        idxs: VectorFloat = numpy.empty(
            len(timegrids.init), dtype=config.TYPES_PY2NP.get(type_, type_)
        )
        with hydpy.pub.options.timestampleft(True):
            for jdx, date in enumerate(hydpy.pub.timegrids.init):
                idxs[jdx] = func(date)
        return idxs


class Indexer:
    """Handles different |IndexerProperty| objects defining time-related indices.

    One can specify the index arrays manually, but they are usually determined
    automatically based on the |Timegrids| object made available through module |pub|.
    """

    def __init__(self) -> None:
        self._monthofyear = None
        self._monthofyear_timegrids = hash(None)
        self._dayofyear = None
        self._dayofyear_hash = hash(None)
        self._timeofyear = None
        self._timeofyear_hash = hash(None)

    @IndexerProperty
    def monthofyear(self) -> Date2Float:
        """Index values, representing the month of the year.

        The following example shows the month indices of the last days of February and
        the first days of March for a leap year:

        >>> from hydpy import print_vector, pub
        >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
        >>> monthofyear = pub.indexer.monthofyear
        >>> print_vector(monthofyear)
        1, 1, 1, 2, 2
        """

        def _monthofyear(date: timetools.Date) -> int:
            return date.month - 1

        return _monthofyear

    @IndexerProperty
    def dayofyear(self) -> Date2Float:
        """Index values, representing the month of the year.

        For reasons of consistency between leap years and non-leap years, assuming a
        daily time step, index 59 is always associated with the 29th of February.
        Hence, it is missing in non-leap years:

        >>> from hydpy import print_vector, pub
        >>> from hydpy.core.indextools import Indexer
        >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
        >>> print_vector(Indexer().dayofyear)
        57, 58, 59, 60, 61
        >>> pub.timegrids = "27.02.2005", "3.03.2005", "1d"
        >>> print_vector(Indexer().dayofyear)
        57, 58, 60, 61
        """

        def _dayofyear(date: timetools.Date) -> int:
            return date.dayofyear - 1 + ((date.month > 2) and (not date.leapyear))

        return _dayofyear

    @IndexerProperty
    def timeofyear(self) -> Date2Float:
        """Index values, representing the time of the year.

        Let us reconsider one of the examples of the documentation on property
        |Indexer.dayofyear|:

        >>> from hydpy import print_vector, pub, Timegrids, Timegrid
        >>> from hydpy.core.indextools import Indexer
        >>> pub.timegrids = "27.02.2005", "3.03.2005", "1d"

        Due to the simulation step size of one day, the index arrays calculated by
        properties |Indexer.dayofyear| and |Indexer.timeofyear| are identical:

        >>> print_vector(Indexer().dayofyear)
        57, 58, 60, 61
        >>> print_vector(Indexer().timeofyear)
        57, 58, 60, 61

        In the next example, we halve the step size:

        >>> pub.timegrids = "27.02.2005", "3.03.2005", "12h"

        Now two subsequent simulation steps associated are with the same day:

        >>> print_vector(Indexer().dayofyear)
        57, 57, 58, 58, 60, 60, 61, 61

        However, the `timeofyear` array gives the index of the respective simulation
        steps of the actual year:

        >>> print_vector(Indexer().timeofyear)
        114, 115, 116, 117, 120, 121, 122, 123

        Note the gap in the returned index array due to 2005 being not a leap year.
        """

        def _timeofyear(date: timetools.Date) -> float:
            date = copy.deepcopy(date)
            date.year = 2000
            return refgrid[date]

        refgrid = timetools.Timegrid(
            timetools.Date("2000.01.01"),
            timetools.Date("2001.01.01"),
            _get_timegrids(_timeofyear).stepsize,
        )
        return _timeofyear

    @IndexerProperty
    def standardclocktime(self) -> Date2Float:
        """Standard clock time at the midpoints of the initialisation time steps in
        hours.

        Note that the standard clock time is not usable as an index.  Hence, we might
        later move property |Indexer.standardclocktime| somewhere else or give class
        |Indexer| a more general purpose (and name) later.

        The following examples demonstrate the calculation of the standard clock time
        for simulation step sizes of one day, one hour, one minute, and one second,
        respectively:

        >>> from hydpy import pub, print_vector
        >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
        >>> print_vector(pub.indexer.standardclocktime)
        12.0, 12.0, 12.0, 12.0, 12.0

        >>> pub.timegrids = "27.02.2004 21:00", "28.02.2004 03:00", "1h"
        >>> print_vector(pub.indexer.standardclocktime)
        21.5, 22.5, 23.5, 0.5, 1.5, 2.5

        >>> pub.timegrids = "27.02.2004 23:57:0", "28.02.2004 00:03:00", "1m"
        >>> print_vector(pub.indexer.standardclocktime)
        23.958333, 23.975, 23.991667, 0.008333, 0.025, 0.041667

        >>> pub.timegrids = "27.02.2004 23:59:57", "28.02.2004 00:00:03", "1s"
        >>> print_vector(pub.indexer.standardclocktime)
        23.999306, 23.999583, 23.999861, 0.000139, 0.000417, 0.000694
        """

        def _standardclocktime(date: timetools.Date) -> float:
            t0 = date.hour + (date.minute + date.second / 60.0) / 60.0
            return t0 + hydpy.pub.timegrids.stepsize.hours / 2.0

        return _standardclocktime
