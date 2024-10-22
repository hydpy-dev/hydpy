"""This module specifies the handling of dates and periods in *HydPy* projects.

.. _`Time Coordinate`: http://cfconventions.org/Data/cf-conventions/\
cf-conventions-1.7/cf-conventions.html#time-coordinate
"""

# import...
# ...from standard library
from __future__ import annotations
import calendar
import collections
import contextlib
import copy
import datetime as datetime_
import time

# ...from third party packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core.typingtools import *

# The import of `_strptime` is not thread save.  The following call of
# `strptime` is supposed to prevent possible problems arising from this bug.
time.strptime("1999", "%Y")

DateConstrArg: TypeAlias = Union[datetime_.datetime, str, "Date"]
PeriodConstrArg: TypeAlias = Union[datetime_.timedelta, str, "Period"]
TypeDate = TypeVar("TypeDate", bound="Date")
TypePeriod = TypeVar("TypePeriod", bound="Period")
TypeTimegrid = TypeVar("TypeTimegrid", bound="Timegrid")
TypeTOY = TypeVar("TypeTOY", bound="TOY")  # pylint: disable=invalid-name
TypeUnit: TypeAlias = Literal["days", "d", "hours", "h", "minutes", "m", "seconds", "s"]


class Date:
    """Handles a single date.

    We built class the |Date| on top of the Python module |datetime|.  It wraps
    |datetime.datetime| objects and specialise this general class on the needs of
    *HydPy* users.

    |Date| objects can be initialised via |datetime.datetime| objects directly:

    >>> import datetime
    >>> date = datetime.datetime(1996, 11, 1, 0, 0, 0)
    >>> from hydpy import Date
    >>> Date(date)
    Date("1996-11-01 00:00:00")

    |Date| objects do not store time zone information.  The |Date| object prepared
    above refers to zero o'clock in the time zone defined by |Options.utcoffset|
    (UTC+01:00 by default).  When the initialisation argument provides other time zone
    information, its date information is adjusted, which we show in the following
    examples, where the prepared |datetime.datetime| objects refer to UTC 00:00 and
    UTC-01:00:

    >>> date = datetime.datetime(1996, 11, 1, 0, 0, 0,
    ...     tzinfo=datetime.timezone(datetime.timedelta(0)))
    >>> Date(date)
    Date("1996-11-01 01:00:00")
    >>> date = datetime.datetime(1996, 11, 1, 0, 0, 0,
    ...     tzinfo=datetime.timezone(datetime.timedelta(hours=-1)))
    >>> Date(date)
    Date("1996-11-01 02:00:00")

    One can change |Options.utcoffset|, but this does not affect already existing
    |Date| objects:

    >>> from hydpy import pub
    >>> pub.options.utcoffset = 0
    >>> temp = Date(date)
    >>> temp
    Date("1996-11-01 01:00:00")
    >>> pub.options.utcoffset = 60
    >>> temp
    Date("1996-11-01 01:00:00")

    Class |Date| accepts |str| objects as alternative constructor arguments.  These are
    often more rapidly defined and allow to set the |Date.style| property by the way
    (see the documentation on method |Date.from_string| for more examples):

    >>> Date("1996-11-01")
    Date("1996-11-01 00:00:00")
    >>> Date("1996.11.01")
    Date("1996.11.01 00:00:00")

    Invalid arguments types result in the following error:

    >>> Date(1)
    Traceback (most recent call last):
    ...
    TypeError: While trying to initialise a `Date` object based on argument `1`, the \
following error occurred: The supplied argument must be either an instance of `Date`, \
`datetime.datetime`, or `str`.  The given arguments type is `int`.

    In contrast to class |datetime.datetime|, class |Date| is mutable:

    >>> date = Date("1996-11-01")
    >>> date.hour = 12
    >>> date
    Date("1996-11-01 12:00:00")

    Unplausible values assigned to property |Date.hour| and its related properties
    result in error messages like the following:

    >>> date.hour = 24
    Traceback (most recent call last):
    ...
    ValueError: While trying to change the hour of the current Date object, the \
following error occurred: hour must be in 0..23

    You can do some math with |Date| objects.  First, you can add |Period| objects to
    shift the date:

    >>> date = Date("2000.01.01")
    >>> date + "1d"
    Date("2000.01.02 00:00:00")
    >>> date += "12h"
    >>> date
    Date("2000.01.01 12:00:00")

    Second, you can subtract both |Period| and other |Date| objects to shift the date
    or determine the time delta, respectively:

    >>> date - "1s"
    Date("2000.01.01 11:59:59")
    >>> date -= "12h"
    >>> date
    Date("2000.01.01 00:00:00")
    >>> date - "2000-01-05"
    Period("-4d")
    >>> "2000.01.01 00:00:30" - date
    Period("30s")

    To try to subtract objects neither interpretable as a |Date| nor |Period| object
    results in the following error:

    >>> date - "1"
    Traceback (most recent call last):
    ...
    TypeError: Object `1` of type `str` cannot be substracted from a `Date` instance.

    The comparison operators work as expected:

    >>> d1, d2 = Date("2000-1-1"), Date("2001-1-1")
    >>> d1 < d2, d1 < "2000-1-1", "2001-1-2" < d1
    (True, False, False)
    >>> d1 <= d2, d1 <= "2000-1-1", "2001-1-2" <= d1
    (True, True, False)
    >>> d1 == d2, d1 == "2000-1-1", "2001-1-2" == d1, d1 == "1d"
    (False, True, False, False)
    >>> d1 != d2, d1 != "2000-1-1", "2001-1-2" != d1, d1 != "1d"
    (True, False, True, True)
    >>> d1 >= d2, d1 >= "2000-1-1", "2001-1-2" >= d1
    (False, True, True)
    >>> d1 > d2, d1 > "2000-1-1", "2001-1-2" > d1
    (False, False, True)
    """

    # These are the so far accepted date format strings.
    formatstrings = {
        "os": "%Y_%m_%d_%H_%M_%S",
        "iso2": "%Y-%m-%d %H:%M:%S",
        "iso1": "%Y-%m-%dT%H:%M:%S",
        "din1": "%d.%m.%Y %H:%M:%S",
        "din2": "%Y.%m.%d %H:%M:%S",
        "raw": "%Y%m%d%H%M%S",
    }
    # The first month of the hydrological year (e.g. November in Germany)
    _firstmonth_wateryear = 11
    _lastformatstring = "os", formatstrings["os"]

    datetime: datetime_.datetime

    def __new__(cls: type[TypeDate], date: DateConstrArg) -> TypeDate:
        try:
            if isinstance(date, Date):
                return cls.from_date(date)
            if isinstance(date, datetime_.datetime):
                return cls.from_datetime(date)
            if isinstance(date, str):
                return cls.from_string(date)
            raise TypeError(
                f"The supplied argument must be either an instance of `Date`, "
                f"`datetime.datetime`, or `str`.  The given arguments type is "
                f"`{type(date).__name__}`."
            )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise a `Date` object based on argument `{date}`"
            )

    @classmethod
    def from_date(cls: type[TypeDate], date: Date) -> TypeDate:
        """Create a new |Date| object based on another |Date| object and return it.

        Initialisation from other |Date| objects preserves their |Date.style|
        information:

        >>> from hydpy import Date
        >>> date1 = Date("2000.01.01")
        >>> date2 = Date(date1)
        >>> date1.style = "iso2"
        >>> date3 = Date.from_date(date1)
        >>> date2
        Date("2000.01.01 00:00:00")
        >>> date3
        Date("2000-01-01 00:00:00")
        """
        self = super().__new__(cls)
        self.datetime = date.datetime
        self.style = date.style
        return self

    @classmethod
    def from_datetime(cls: type[TypeDate], date: datetime_.datetime) -> TypeDate:
        """Create a new |Date| object based on a |datetime.datetime| object and return
        it.

        Initialisation from |datetime.datetime| does not modify the default
        |Date.style| information:

        >>> from hydpy import Date
        >>> from datetime import datetime, timedelta, timezone
        >>> Date.from_datetime(datetime(2000, 1, 1))
        Date("2000-01-01 00:00:00")

        Be aware of the different minimum time resolution of class |datetime.datetime|
        (microseconds) and class |Date| (seconds):

        >>> Date.from_datetime(datetime(2000, 1, 1, microsecond=2))
        Traceback (most recent call last):
        ...
        ValueError: For `Date` instances, the microsecond must be zero, but for the \
given `datetime` object it is `2` instead.

        Due to a different kind of handling time zone information, the time zone
        awareness of |datetime.datetime| objects is removed (see the main documentation
        on class |Date| for further information:

        >>> date = Date.from_datetime(
        ...     datetime(2000, 11, 1, tzinfo=timezone(timedelta(0))))
        >>> date
        Date("2000-11-01 01:00:00")
        >>> date.datetime
        datetime.datetime(2000, 11, 1, 1, 0)
        """
        if date.microsecond != 0:
            raise ValueError(
                f"For `Date` instances, the microsecond must be zero, but for the "
                f"given `datetime` object it is `{date.microsecond:d}` instead."
            )
        self = super().__new__(cls)
        utcoffset = date.utcoffset()
        if utcoffset is not None:
            date = (
                date.replace(tzinfo=None)
                - utcoffset
                + datetime_.timedelta(minutes=hydpy.pub.options.utcoffset)
            )
        self.datetime = date
        return self

    @classmethod
    def from_string(cls: type[TypeDate], date: str) -> TypeDate:
        """Create a new |Date| object based on a |datetime.datetime| object and return
        it.

        The given string needs to match one of the following |Date.style| patterns.

        The `os` style is applied in text files and folder names and does not include
        any empty spaces or colons:

        >>> Date.from_string("1997_11_01_00_00_00").style
        'os'

        The `iso` styles are more legible and come in two flavours.  `iso1` follows
        ISO 8601, and `iso2` (which is the default style) omits the `T` between the
        date and the time:

        >>> Date.from_string("1997-11-01T00:00:00").style
        'iso1'
        >>> Date.from_string("1997-11-01 00:00:00").style
        'iso2'

        The `din` styles rely on points instead of hyphens.  The difference between the
        available flavours lies in the order of the date literals (DIN refers to a
        German norm):

        >>> Date("01.11.1997 00:00:00").style
        'din1'
        >>> Date("1997.11.01 00:00:00").style
        'din2'

        The `raw` style avoids any unnecessary characters:

        >>> Date("19971101000000").style
        'raw'

        You are allowed to abbreviate the input strings:

        >>> for string in ("1996-11-01 00:00:00",
        ...                "1996-11-01 00:00",
        ...                "1996-11-01 00",
        ...                "1996-11-01"):
        ...     print(Date.from_string(string))
        1996-11-01 00:00:00
        1996-11-01 00:00:00
        1996-11-01 00:00:00
        1996-11-01 00:00:00

        You can combine all styles with ISO time zone identifiers:

        >>> Date.from_string("1997-11-01T00:00:00Z")
        Date("1997-11-01T01:00:00")
        >>> Date.from_string("1997-11-01 00:00:00-11:00")
        Date("1997-11-01 12:00:00")
        >>> Date.from_string("1997-11-01 +13")
        Date("1997-10-31 12:00:00")
        >>> Date.from_string("1997-11-01 +1330")
        Date("1997-10-31 11:30:00")
        >>> Date.from_string("01.11.1997 00-500")
        Date("01.11.1997 06:00:00")

        Poorly formatted date strings result in the following or comparable error
        messages:

        >>> Date.from_string("1997/11/01")
        Traceback (most recent call last):
        ...
        ValueError: The given string `1997/11/01` does not agree with any of the \
supported format styles.

        >>> Date.from_string("1997111")
        Traceback (most recent call last):
        ...
        ValueError: The given string `1997111` does not agree with any of the \
supported format styles.

        >>> Date.from_string("1997-11-01 +0000001")
        Traceback (most recent call last):
        ...
        ValueError: While trying to apply the time zone offset defined by string \
`1997-11-01 +0000001`, the following error occurred: wrong number of offset characters

        >>> Date.from_string("1997-11-01 +0X:00")
        Traceback (most recent call last):
        ...
        ValueError: While trying to apply the time zone offset defined by string \
`1997-11-01 +0X:00`, the following error occurred: invalid literal for int() with \
base 10: '0X'
        """
        self = super().__new__(cls)
        substring, offset = self._extract_offset(date)
        vars(self)["style"], date_ = self._extract_date(substring, date)
        self.datetime = self._modify_date(date_, offset, date)
        return self

    @staticmethod
    def _extract_offset(string: str) -> tuple[str, str | None]:
        if "Z" in string:
            return string.split("Z")[0].strip(), "+0000"
        if "+" in string:
            idx = string.find("+")
        elif string.count("-") in (1, 3):
            idx = string.rfind("-")
        else:
            return string, None
        return string[:idx].strip(), string[idx:].strip()

    @classmethod
    def _extract_date(
        cls, substring: str, string: str
    ) -> tuple[str, datetime_.datetime]:
        strptime = datetime_.datetime.strptime
        try:
            style, format_ = cls._lastformatstring
            return style, strptime(substring, format_)
        except ValueError as exc:
            if substring.isdigit():
                format_ = cls.formatstrings["raw"][: len(substring) - 2]
                try:
                    datetime = strptime(substring, format_)
                except ValueError:
                    raise ValueError(
                        f"The given string `{string}` does not agree with any of the "
                        f"supported format styles."
                    ) from exc
                cls._lastformatstring = "raw", format_
                return "raw", datetime
            for style, format_ in cls.formatstrings.items():
                if style != "raw":
                    for _ in range(4):
                        try:
                            datetime = strptime(substring, format_)
                            cls._lastformatstring = style, format_
                            return style, datetime
                        except ValueError:
                            format_ = format_[:-3]
            raise ValueError(
                f"The given string `{string}` does not agree with any of the "
                f"supported format styles."
            ) from exc

    @staticmethod
    def _modify_date(
        date: datetime_.datetime, offset: str | None, string: str
    ) -> datetime_.datetime:
        try:
            if offset is None:
                return date
            factor = 1 if (offset[0] == "+") else -1
            offset = offset[1:].strip().replace(":", "")
            if len(offset) <= 2:
                minutes = int(offset) * 60
            elif len(offset) <= 4:
                minutes = int(offset[:-2]) * 60 + int(offset[-2:])
            else:
                raise ValueError("wrong number of offset characters")
            delta = datetime_.timedelta(
                minutes=factor * minutes - hydpy.pub.options.utcoffset
            )
            new_date = date - delta
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to apply the time zone offset defined by string "
                f"`{string}`"
            )
        return new_date

    @classmethod
    def from_array(cls: type[TypeDate], array: NDArrayFloat) -> TypeDate:
        """Return a |Date| instance based on date information (year, month, day, hour,
        minute, second) stored as the first entries of the successive rows of a
        |numpy.ndarray|.

        >>> from hydpy import Date
        >>> import numpy
        >>> array1d = numpy.array([1992, 10, 8, 15, 15, 42, 999])
        >>> Date.from_array(array1d)
        Date("1992-10-08 15:15:42")

        >>> array3d = numpy.zeros((7, 2, 2))
        >>> array3d[:, 0, 0] = array1d
        >>> Date.from_array(array3d)
        Date("1992-10-08 15:15:42")

        .. note::

           The date defined by the given |numpy.ndarray| cannot include any time zone
           information and corresponds to |Options.utcoffset|, which defaults to
           UTC+01:00.
        """
        for _ in range(1, array.ndim):
            array = array[:, 0]
        return cls.from_datetime(datetime_.datetime(*array.astype(int)[:6]))

    def to_array(self) -> numpy.ndarray:
        """Return a 1-dimensional |numpy| |numpy.ndarray|  with six entries defining
        the actual date (year, month, day, hour, minute, second).

        >>> from hydpy import Date, print_vector
        >>> print_vector(Date("1992-10-8 15:15:42").to_array())
        1992.0, 10.0, 8.0, 15.0, 15.0, 42.0

        .. note::

           The date defined by the returned |numpy.ndarray| does not include any time
           zone information and corresponds to |Options.utcoffset|, which defaults to
           UTC+01:00.
        """
        return numpy.array(
            [self.year, self.month, self.day, self.hour, self.minute, self.second],
            dtype=config.NP_FLOAT,
        )

    @classmethod
    def from_cfunits(cls: type[TypeDate], units: str) -> TypeDate:
        """Return a |Date| object representing the reference date of the given `units`
        string agreeing with the NetCDF-CF conventions.

        We took the following example string from the `Time Coordinate`_ chapter of the
        NetCDF-CF conventions documentation (modified).  Note that method
        |Date.from_cfunits| ignores the first entry (the unit) and assumes UTC+00 for
        strings without time zone identifiers (as opposed to the usual `HydPy`
        convention that dates without time zone identifiers correspond to the local
        time defined by the option |Options.utcoffset|):

        >>> from hydpy import Date
        >>> Date.from_cfunits("seconds since 1992-10-8 15:15:42 -6:00")
        Date("1992-10-08 22:15:42")
        >>> Date.from_cfunits(" day since 1992-10-8 15:15:00")
        Date("1992-10-08 16:15:00")
        >>> Date.from_cfunits("seconds since 1992-10-8 -6:00")
        Date("1992-10-08 07:00:00")
        >>> Date.from_cfunits("m since 1992-10-8")
        Date("1992-10-08 01:00:00")

        One can also pass the unmodified example string from `Time Coordinate`_ as long
        as one omits any decimal fractions of a second different from zero:

        >>> Date.from_cfunits("seconds since 1992-10-8 15:15:42.")
        Date("1992-10-08 16:15:42")
        >>> Date.from_cfunits("seconds since 1992-10-8 15:15:42.00")
        Date("1992-10-08 16:15:42")
        >>> Date.from_cfunits("seconds since 1992-10-8 15:15:42. -6:00")
        Date("1992-10-08 22:15:42")
        >>> Date.from_cfunits("seconds since 1992-10-8 15:15:42.0 -6:00")
        Date("1992-10-08 22:15:42")
        >>> Date.from_cfunits("seconds since 1992-10-8 15:15:42.005 -6:00")
        Traceback (most recent call last):
        ...
        ValueError: While trying to parse the date of the NetCDF-CF "units" string \
`seconds since 1992-10-8 15:15:42.005 -6:00`, the following error occurred: No other \
decimal fraction of a second than "0" allowed.
        """
        try:
            string = units[units.find("since") + 6 :]
            idx = string.find(".")
            if idx != -1:
                jdx = -999
                for jdx, char in enumerate(string[idx + 1 :]):
                    if not char.isnumeric():
                        break
                    if char != "0":
                        raise ValueError(
                            'No other decimal fraction of a second than "0" allowed.'
                        )
                else:
                    if jdx == -999:
                        jdx = idx + 1
                    else:
                        jdx += 1
                string = f"{string[:idx]}{string[idx+jdx+1:]}"
            offset = cls._extract_offset(string)[1]
            if offset is None:
                string = f"{string} +00:00"
            return cls.from_string(string)
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to parse the date of the NetCDF-CF "units" string '
                f"`{units}`"
            )

    def to_cfunits(self, unit: str = "hours", utcoffset: int | None = None) -> str:
        """Return a `units` string agreeing with the NetCDF-CF conventions.

        By default, method |Date.to_cfunits| uses `hours` as the time unit and takes
        the value of |Options.utcoffset| as time zone information:

        >>> from hydpy import Date
        >>> date = Date("1992-10-08 15:15:42")
        >>> date.to_cfunits()
        'hours since 1992-10-08 15:15:42 +01:00'

        You can define arbitrary strings to describe the time unit:

        >>> date.to_cfunits(unit="minutes")
        'minutes since 1992-10-08 15:15:42 +01:00'

        For changing the time zone, pass the corresponding offset in minutes:

        >>> date.to_cfunits(unit="sec", utcoffset=-60)
        'sec since 1992-10-08 13:15:42 -01:00'
        """
        if utcoffset is None:
            utcoffset = hydpy.pub.options.utcoffset
        string = self.to_string("iso2", utcoffset)
        string = " ".join((string[:-6], string[-6:]))
        return f"{unit} since {string}"

    @property
    def style(self) -> str:
        """Date format style to be applied in printing.

        Initially, |Date.style| corresponds to the format style of the string used as
        the initialisation object of a |Date| object:

        >>> from hydpy import Date
        >>> date = Date("01.11.1997 00:00:00")
        >>> date.style
        'din1'
        >>> date
        Date("01.11.1997 00:00:00")

        However, you are allowed to change it:

        >>> date.style = "iso1"
        >>> date
        Date("1997-11-01T00:00:00")

        The default style is `iso2`:

        >>> from datetime import datetime
        >>> date = Date(datetime(2000, 1, 1))
        >>> date
        Date("2000-01-01 00:00:00")
        >>> date.style
        'iso2'

        Trying to set a non-existing style results in the following error message:

        >>> date.style = "iso"
        Traceback (most recent call last):
        ...
        AttributeError: Date format style `iso` is not available.
        """
        return vars(self).get("style", "iso2")

    @style.setter
    def style(self, style: str) -> None:
        if style in self.formatstrings:
            vars(self)["style"] = style
        else:
            vars(self).pop("style", None)
            raise AttributeError(f"Date format style `{style}` is not available.")

    def _set_thing(self, thing: str, value: int) -> None:
        """Convenience method for `year.fset`, `month.fset`..."""
        try:
            kwargs = {}
            for unit in ("year", "month", "day", "hour", "minute", "second"):
                kwargs[unit] = getattr(self, unit)
            kwargs[thing] = int(value)
            self.datetime = datetime_.datetime(**kwargs)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to change the {thing} " f"of the current Date object"
            )

    @property
    def second(self) -> int:
        """The actual second.

        >>> from hydpy import Date
        >>> date = Date("2000-01-01 00:00:00")
        >>> date.second
        0
        >>> date.second = 30
        >>> date.second
        30
        """
        return self.datetime.second

    @second.setter
    def second(self, second: int) -> None:
        self._set_thing("second", second)

    @property
    def minute(self) -> int:
        """The actual minute.

        >>> from hydpy import Date
        >>> date = Date("2000-01-01 00:00:00")
        >>> date.minute
        0
        >>> date.minute = 30
        >>> date.minute
        30
        """
        return self.datetime.minute

    @minute.setter
    def minute(self, minute: int) -> None:
        self._set_thing("minute", minute)

    @property
    def hour(self) -> int:
        """The actual hour.

        >>> from hydpy import Date
        >>> date = Date("2000-01-01 00:00:00")
        >>> date.hour
        0
        >>> date.hour = 12
        >>> date.hour
        12
        """
        return self.datetime.hour

    @hour.setter
    def hour(self, hour: int) -> None:
        self._set_thing("hour", hour)

    @property
    def day(self) -> int:
        """The actual day.

        >>> from hydpy import Date
        >>> date = Date("2000-01-01 00:00:00")
        >>> date.day
        1
        >>> date.day = 15
        >>> date.day
        15
        """
        return self.datetime.day

    @day.setter
    def day(self, day: int) -> None:
        self._set_thing("day", day)

    @property
    def month(self) -> int:
        """The actual month.

        >>> from hydpy import Date
        >>> date = Date("2000-01-01 00:00:00")
        >>> date.month
        1
        >>> date.month = 7
        >>> date.month
        7
        """
        return self.datetime.month

    @month.setter
    def month(self, month: int) -> None:
        self._set_thing("month", month)

    @property
    def year(self) -> int:
        """The actual year.

        >>> from hydpy import Date
        >>> date = Date("2000-01-01 00:00:00")
        >>> date.year
        2000
        >>> date.year = 1   # smallest possible value
        >>> date.year
        1
        >>> date.year = 9999   # highest possible value
        >>> date.year
        9999
        """
        return self.datetime.year

    @year.setter
    def year(self, year: int) -> None:
        self._set_thing("year", year)

    def _get_refmonth(self) -> int:
        """The first month of the hydrological year.

        The default value is 11 (November which is the German reference month):

        >>> from hydpy import Date
        >>> date1 = Date("2000-01-01")
        >>> date1.refmonth
        11

        Setting it, for example, to 10 (October is another typical reference month in
        different countries) affects all |Date| instances, no matter if already
        existing or created afterwards:

        >>> date2 = Date("2010-01-01")
        >>> date1.refmonth = 10
        >>> date1.refmonth
        10
        >>> date2.refmonth
        10
        >>> Date("2010-01-01").refmonth
        10

        Alternatively, you can pass an appropriate string (the first three characters
        count):

        >>> date1.refmonth = "January"
        >>> date1.refmonth
        1
        >>> date1.refmonth = "feb"
        >>> date1.refmonth
        2

        Wrong arguments result in the following error messages:

        >>> date1.refmonth = 0
        Traceback (most recent call last):
        ...
        ValueError: The reference month must be a value between one (January) and \
twelve (December) but `0` is given

        >>> date1.refmonth = "wrong"
        Traceback (most recent call last):
        ...
        ValueError: The given argument `wrong` cannot be interpreted as a month.

        >>> date1.refmonth = 11
        """
        return type(self)._firstmonth_wateryear

    def _set_refmonth(self, value: int | str) -> None:
        try:
            refmonth = int(value)
        except ValueError:
            string = str(value)[:3].lower()
            try:
                months = [
                    "jan",
                    "feb",
                    "mar",
                    "apr",
                    "may",
                    "jun",
                    "jul",
                    "aug",
                    "sew",
                    "oct",
                    "nov",
                    "dec",
                ]
                refmonth = months.index(string) + 1
            except ValueError:
                raise ValueError(
                    f"The given argument `{value}` cannot be "
                    f"interpreted as a month."
                ) from None
        if not 0 < refmonth < 13:
            raise ValueError(
                f"The reference month must be a value between one (January) and "
                f"twelve (December) but `{value}` is given"
            )
        type(self)._firstmonth_wateryear = refmonth

    refmonth = propertytools.Property[int | str, int](
        fget=_get_refmonth, fset=_set_refmonth
    )

    @property
    def wateryear(self) -> int:
        """The actual hydrological year according to the selected reference month.

        Property |Date.refmonth| defaults to November:

        >>> october = Date("1996.10.01")
        >>> november = Date("1996.11.01")
        >>> october.wateryear
        1996
        >>> november.wateryear
        1997

        Note that changing |Date.refmonth| affects all |Date| objects:

        >>> october.refmonth = 10
        >>> october.wateryear
        1997
        >>> november.wateryear
        1997
        >>> october.refmonth = "November"
        >>> october.wateryear
        1996
        >>> november.wateryear
        1997
        """
        if self.month < self._firstmonth_wateryear:
            return self.year
        return self.year + 1

    @property
    def dayofyear(self) -> int:
        """The day of the year as an integer value.

        >>> from hydpy import Date
        >>> Date("2003-03-01").dayofyear
        60
        >>> Date("2004-03-01").dayofyear
        61
        """
        return self.datetime.timetuple().tm_yday

    @property
    def leapyear(self) -> bool:
        """Return whether the actual date falls in a leap year or not.

        >>> from hydpy import Date
        >>> Date("2003-03-01").leapyear
        False
        >>> Date("2004-03-01").leapyear
        True
        >>> Date("2000-03-01").leapyear
        True
        >>> Date("2100-03-01").leapyear
        False
        """
        year = self.year
        return ((year % 4) == 0) and (((year % 100) != 0) or ((year % 400) == 0))

    @property
    def beginning_next_month(self) -> Date:
        """The first possible date of the next month after the month of the current
        |Date| object.

        >>> from hydpy import Date
        >>> Date("2001-01-01 00:00:00").beginning_next_month
        Date("2001-02-01 00:00:00")
        >>> Date("2001-01-31 12:30:30").beginning_next_month
        Date("2001-02-01 00:00:00")
        >>> Date("2001-12-01 00:00:00").beginning_next_month
        Date("2002-01-01 00:00:00")
        >>> Date("2001-12-31 12:30:30").beginning_next_month
        Date("2002-01-01 00:00:00")
        """
        date = Date(self)
        date.day = 1
        date.hour = 0
        date.second = 0
        date.minute = 0
        if date.month == 12:
            date.month = 1
            date.year += 1
        else:
            date.month += 1
        return date

    def __add__(self: TypeDate, other: PeriodConstrArg) -> TypeDate:
        new = self.from_datetime(self.datetime + Period(other).timedelta)
        new.style = self.style
        return new

    def __iadd__(self: TypeDate, other: PeriodConstrArg) -> TypeDate:
        self.datetime += Period(other).timedelta
        return self

    @overload
    def __sub__(self, other: Date | datetime_.datetime) -> Period:
        """Determine the period between two dates."""

    @overload
    def __sub__(self: TypeDate, other: Period | datetime_.timedelta) -> TypeDate:
        """Subtract a period from the actual date."""

    @overload
    def __sub__(self: TypeDate, other: str) -> TypeDate | Period:
        """Result depends on the string."""

    def __sub__(
        self: TypeDate,
        other: Date | datetime_.datetime | datetime_.timedelta | Period | str,
    ) -> TypeDate | Period:
        if isinstance(other, (Date, datetime_.datetime, str)):
            try:
                return Period(self.datetime - type(self)(other).datetime)
            except BaseException:
                pass
        if isinstance(other, (Period, datetime_.timedelta, str)):
            try:
                new = self.from_datetime(self.datetime - Period(other).timedelta)
                new.style = self.style
                return new
            except BaseException:
                pass
        raise TypeError(
            f"Object `{other}` of type `{type(other).__name__}` cannot be substracted "
            f"from a `Date` instance."
        )

    def __rsub__(self, other: DateConstrArg) -> Period:
        return Period(type(self)(other).datetime - self.datetime)

    def __isub__(self: TypeDate, other: PeriodConstrArg) -> TypeDate:  # type: ignore
        # without more flexible ways to relate types to string patterns, there is
        # nothing we can do about it (except providing a less flexible interface, of
        # course)
        self.datetime -= Period(other).timedelta
        return self

    def __lt__(self, other: DateConstrArg) -> bool:
        return self.datetime < type(self)(other).datetime

    def __le__(self, other: DateConstrArg) -> bool:
        return self.datetime <= type(self)(other).datetime

    def __eq__(self, other: Any) -> bool:
        try:
            return self.datetime == type(self)(other).datetime
        except BaseException:
            return False

    def __ne__(self, other: Any) -> bool:
        try:
            return self.datetime != type(self)(other).datetime
        except BaseException:
            return True

    def __gt__(self, other: DateConstrArg) -> bool:
        return self.datetime > type(self)(other).datetime

    def __ge__(self, other: DateConstrArg) -> bool:
        return self.datetime >= type(self)(other).datetime

    def __deepcopy__(self: TypeDate, dict_: dict[str, Any]) -> TypeDate:
        new = type(self).from_date(self)
        new.datetime = copy.deepcopy(self.datetime)
        return new

    def to_string(self, style: str | None = None, utcoffset: int | None = None) -> str:
        """Return a |str| object representing the actual date following the given style
        and the eventually given UTC offset (in minutes).

        Without any input arguments, the actual |Date.style| is used to return a date
        string in your local time zone:

        >>> from hydpy import Date
        >>> date = Date("01.11.1997 00:00:00")
        >>> date.to_string()
        '01.11.1997 00:00:00'

        Passing a style string affects the returned |str| object but not the
        |Date.style| property:

        >>> date.style
        'din1'
        >>> date.to_string(style="iso2")
        '1997-11-01 00:00:00'
        >>> date.style
        'din1'

        When passing the `utcoffset` in minutes, method |Date.to_string| appends the
        offset string:

        >>> date.to_string(style="iso2", utcoffset=60)
        '1997-11-01 00:00:00+01:00'

        If the given offset does not correspond to your local offset defined by
        |Options.utcoffset| (which defaults to UTC+01:00), the date string is adapted:

        >>> date.to_string(style="iso1", utcoffset=0)
        '1997-10-31T23:00:00+00:00'
        """
        if style is None:
            style = self.style
        if utcoffset is None:
            string = ""
            date = self.datetime
        else:
            sign = "+" if utcoffset >= 0 else "-"
            hours = abs(utcoffset // 60)
            minutes = abs(utcoffset % 60)
            string = f"{sign}{hours:02d}:{minutes:02d}"
            offset = utcoffset - hydpy.pub.options.utcoffset
            date = self.datetime + datetime_.timedelta(minutes=offset)
        return date.strftime(self.formatstrings[style]) + string

    def to_repr(self, style: str | None = None, utcoffset: int | None = None) -> str:
        """Similar to method |Date.to_string|, but returns a proper string
        representation instead.

        See method |Date.to_string| for explanations on the following examples:

        >>> from hydpy import Date
        >>> date = Date("01.11.1997 00:00:00")
        >>> date.to_repr()
        'Date("01.11.1997 00:00:00")'
        >>> date.to_repr("iso1", utcoffset=0)
        'Date("1997-10-31T23:00:00+00:00")'
        """
        return f'Date("{self.to_string(style, utcoffset)}")'

    def __str__(self) -> str:
        return self.to_string(self.style)

    def __repr__(self) -> str:
        return self.to_repr()


class Period:
    """Handles a single period.

    We built the class |Period| on top of the Python module |datetime|.  It wraps
    |datetime.timedelta| objects and specialises this general class on the needs of
    *HydPy* users.

    Be aware of the different minimum time resolution of module |datetime|
    (microseconds) and module |timetools| (seconds).

    You can initialise |Period| directly via |datetime.timedelta| objects (see the
    documentation on method |Period.from_timedelta| for more information):

    >>> from hydpy import Period
    >>> from datetime import timedelta
    >>> Period(timedelta(1))
    Period("1d")

    Alternatively, one can initialise from |str| objects.  These must consist of some
    characters defining an integer value followed by a single character defining the
    unit (see the documentation on method |Period.from_timedelta| for more information):

    >>> Period("30s")
    Period("30s")

    In case you need an "empty" period object, pass nothing or |None|:

    >>> Period()
    Period()
    >>> Period(None)
    Period()

    All other types result in the following error:

    >>> Period(1)
    Traceback (most recent call last):
    ...
    TypeError: While trying to initialise a `Period` object based argument `1`, the \
following error occurred: The supplied argument must be either an instance of \
`Period`, `datetime.timedelta`, or `str`, but the given type is `int`.

    Class |Period| supports some mathematical operations.  Depending on the operation,
    the second operand can be either a number or an object interpretable as a date or
    period.

    First, one can add two |Period| objects or add a |Period| object to an object
    representing a date:

    >>> period = Period("1m")
    >>> period + "2m"
    Period("3m")
    >>> "30s" + period
    Period("90s")
    >>> period += "4m"
    >>> period
    Period("5m")
    >>> "2000-01-01" + period
    Date("2000-01-01 00:05:00")
    >>> period + "wrong"
    Traceback (most recent call last):
    ...
    TypeError: Object `wrong` of type `str` cannot be added to a `Period` instance.

    Subtraction works much like addition:

    >>> period = Period("4d")
    >>> period - "1d"
    Period("3d")
    >>> "1d" - period
    Period("-3d")
    >>> period -= "2d"
    >>> period
    Period("2d")
    >>> "2000-01-10" - period
    Date("2000-01-08 00:00:00")
    >>> "wrong" - period
    Traceback (most recent call last):
    ...
    TypeError: A `Period` instance cannot be subtracted from object `wrong` of type \
`str`.

    Use multiplication with a number to change the length of a |Period| object:

    >>> period * 2.0
    Period("4d")
    >>> 0.5 * period
    Period("1d")
    >>> period *= 1.5
    >>> period
    Period("3d")

    Division is possible in combination numbers and objects interpretable as periods:


    >>> period / 3.0
    Period("1d")
    >>> period / "36h"
    2.0
    >>> "6d" / period
    2.0
    >>> period /= 1.5
    >>> period
    Period("2d")

    Floor division and calculation of the remainder are also supported:

    >>> period // "20h"
    2
    >>> period % "20h"
    Period("8h")
    >>> "3d" // period
    1
    >>> timedelta(3) % period
    Period("1d")

    You can change the sign in the following manners:

    >>> period = -period
    >>> period
    Period("-2d")
    >>> +period
    Period("-2d")
    >>> abs(period)
    Period("2d")

    The comparison operators work as expected:

    >>> p1, p3 = Period("1d"), Period("3d")
    >>> p1 < "2d", p1 < "1d", "2d" < p1
    (True, False, False)
    >>> p1 <= p3, p1 <= "1d", "2d" <= p1
    (True, True, False)
    >>> p1 == p3, p1 == "1d", "2d" == p1, p1 == "2000-01-01"
    (False, True, False, False)
    >>> p1 != p3, p1 != "1d", "2d" != p1, p1 != "2000-01-01"
    (True, False, True, True)
    >>> p1 >= p3, p1 >= "1d", "2d" >= p1
    (False, True, True)
    >>> p1 > p3, p1 > "1d", "2d" > p1
    (False, False, True)
    """

    def __new__(
        cls: type[TypePeriod], period: PeriodConstrArg | None = None
    ) -> TypePeriod:
        try:
            if isinstance(period, Period):
                return cls.from_period(period)
            if isinstance(period, datetime_.timedelta):
                return cls.from_timedelta(period)
            if isinstance(period, str):
                return cls.from_string(period)
            if period is None:
                return super().__new__(cls)
            raise TypeError(
                f"The supplied argument must be either an instance of `Period`, "
                f"`datetime.timedelta`, or `str`, but the given type is "
                f"`{type(period).__name__}`."
            )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise a `Period` object based argument "
                f"`{period}`"
            )

    @classmethod
    def from_period(cls: type[TypePeriod], period: Period) -> TypePeriod:
        """Create a new |Period| object based on another |Period| object and return it.

        >>> from hydpy import Period
        >>> p1 = Period("1d")
        >>> p2 = Period.from_period(p1)
        >>> p2
        Period("1d")
        >>> p1 *= 2
        >>> p1
        Period("2d")
        >>> p2
        Period("1d")
        """
        self = super().__new__(cls)
        vars(self)["timedelta"] = vars(period).get("timedelta")
        return self

    @classmethod
    def from_timedelta(
        cls: type[TypePeriod], period: datetime_.timedelta
    ) -> TypePeriod:
        """Create a new |Period| object based on a |datetime.timedelta| object and
        return it.

        |datetime.timedelta| objects defining days or seconds are allowed, but
        |datetime.timedelta| objects defining microseconds are not:

        >>> from hydpy import Period
        >>> from datetime import timedelta
        >>> Period.from_timedelta(timedelta(1, 0))
        Period("1d")
        >>> Period.from_timedelta(timedelta(0, 1))
        Period("1s")
        >>> Period.from_timedelta(timedelta(0, 0, 1))
        Traceback (most recent call last):
        ...
        ValueError: For `Period` instances, microseconds must be zero.  \
However, for the given `timedelta` object it is `1` instead.
        """
        self = super().__new__(cls)
        vars(self)["timedelta"] = self._check_timedelta(period)
        return self

    @staticmethod
    def _check_timedelta(period: datetime_.timedelta) -> datetime_.timedelta:
        if period.microseconds:
            raise ValueError(
                f"For `Period` instances, microseconds must be zero.  However, for "
                f"the given `timedelta` object it is `{period.microseconds}` instead."
            )
        return period

    @classmethod
    def from_string(cls: type[TypePeriod], period: str) -> TypePeriod:
        """Create a new |Period| object based on a |str| object and return it.

        The string must consist of a leading integer number followed by one of the
        lower chase characters `s` (seconds), `m` (minutes), `h` (hours), and `d`
        (days):

        >>> from hydpy import Period
        >>> Period.from_string("30s")
        Period("30s")
        >>> Period.from_string("5m")
        Period("5m")
        >>> Period.from_string("6h")
        Period("6h")
        >>> Period.from_string("1d")
        Period("1d")

        Ill-defined strings result in the following errors:

        >>> Period.from_string("oned")
        Traceback (most recent call last):
        ...
        ValueError: All characters of the given period string, except the last one \
which represents the unit, need to define an integer number.  Instead, these \
characters are `one`.

        >>> Period.from_string("1.5d")
        Traceback (most recent call last):
        ...
        ValueError: All characters of the given period string, except the last one \
which represents the unit, need to define an integer number.  Instead, these \
characters are `1.5`.

        >>> Period.from_string("1D")
        Traceback (most recent call last):
        ...
        ValueError: The last character of the given period string needs to be either \
`d` (days), `h` (hours), `m` (minutes),  or `s` (seconds).  Instead, the last \
character is `D`.
        """
        self = super().__new__(cls)
        vars(self)["timedelta"] = cls._get_timedelta_from_string(period)
        return self

    @staticmethod
    def _get_timedelta_from_string(period: str) -> datetime_.timedelta:
        try:
            number = float(period[:-1])
            if number != int(number):
                raise ValueError
        except ValueError:
            raise ValueError(
                f"All characters of the given period string, except the last one "
                f"which represents the unit, need to define an integer number.  "
                f"Instead, these characters are `{period[:-1]}`."
            ) from None
        unit = period[-1]
        if unit == "d":
            return datetime_.timedelta(number, 0)
        if unit == "h":
            return datetime_.timedelta(0, number * 3600)
        if unit == "m":
            return datetime_.timedelta(0, number * 60)
        if unit == "s":
            return datetime_.timedelta(0, number)
        raise ValueError(
            f"The last character of the given period string needs to be either `d` "
            f"(days), `h` (hours), `m` (minutes),  or `s` (seconds).  Instead, the "
            f"last character is `{unit}`."
        )

    @classmethod
    def from_seconds(cls: type[TypePeriod], seconds: int) -> TypePeriod:
        """Create a new |Period| object based on the given integer number of seconds
        and return it.

        >>> from hydpy import Period
        >>> Period.from_seconds(120)
        Period("2m")
        """
        return cls.from_timedelta(datetime_.timedelta(0, int(seconds)))

    @classmethod
    def from_cfunits(cls: type[TypePeriod], units: TypeUnit) -> TypePeriod:
        """Create a |Period| object representing the time unit of the given `units`
        string agreeing with the NetCDF-CF conventions and return it.

        We took the following example string from the `Time Coordinate`_ chapter of the
        NetCDF-CF conventions.  Note that the character of the first entry (the actual
        time unit) is of relevance:

        >>> from hydpy import Period
        >>> Period.from_cfunits("seconds since 1992-10-8 15:15:42.5 -6:00")
        Period("1s")
        >>> Period.from_cfunits(" day since 1992-10-8 15:15:00")
        Period("1d")
        >>> Period.from_cfunits("m since 1992-10-8")
        Period("1m")
        """
        return cls.from_string(f"1{units.strip()[0]}")

    def _get_timedelta(self) -> datetime_.timedelta:
        """The handled |datetime.timedelta| object.

        You are allowed to change and delete the handled |datetime.timedelta| object:

        >>> from hydpy import Period
        >>> period = Period("1d")
        >>> period.timedelta.days
        1
        >>> del period.timedelta
        >>> period.timedelta
        Traceback (most recent call last):
        ...
        AttributeError: The Period object does not handle a timedelta object at the \
moment.
        >>> from datetime import timedelta
        >>> period.timedelta = timedelta(1)
        >>> hasattr(period, "timedelta")
        True

        Property |Period.timedelta| supports the automatic conversion of given |Period|
        and |str| objects:

        >>> period.timedelta = Period("2d")
        >>> period.timedelta.days
        2

        >>> period.timedelta = "1h"
        >>> period.timedelta.seconds
        3600

        >>> period.timedelta = 1
        Traceback (most recent call last):
        ...
        TypeError: The supplied argument must be either an instance of `Period´, \
`datetime.timedelta` or `str`.  The given argument's type is `int`.
        """
        timedelta = cast(datetime_.timedelta | None, vars(self).get("timedelta"))
        if timedelta is None:
            raise AttributeError(
                "The Period object does not handle a timedelta object at the moment."
            )
        return timedelta

    def _set_timedelta(self, period: PeriodConstrArg | None) -> None:
        if isinstance(period, Period):
            vars(self)["timedelta"] = vars(period).get("timedelta")
        elif isinstance(period, datetime_.timedelta):
            vars(self)["timedelta"] = self._check_timedelta(period)
        elif isinstance(period, str):
            vars(self)["timedelta"] = self._get_timedelta_from_string(period)
        else:
            raise TypeError(
                f"The supplied argument must be either an instance of `Period´, "
                f"`datetime.timedelta` or `str`.  The given argument's type is "
                f"`{type(period).__name__}`."
            )

    def _del_timedelta(self) -> None:
        vars(self)["timedelta"] = None

    timedelta = propertytools.Property[PeriodConstrArg | None, datetime_.timedelta](
        fget=_get_timedelta, fset=_set_timedelta, fdel=_del_timedelta
    )

    @property
    def unit(self) -> str:
        """The (most suitable) unit for the current period.

        |Period.unit| always returns the unit leading to the smallest integer value:

        >>> from hydpy import Period
        >>> period = Period("1d")
        >>> period.unit
        'd'
        >>> period /= 2
        >>> period.unit
        'h'
        >>> Period("120s").unit
        'm'
        >>> Period("90s").unit
        's'
        """
        if not self.days % 1:
            return "d"
        if not self.hours % 1:
            return "h"
        if not self.minutes % 1:
            return "m"
        return "s"

    @property
    def seconds(self) -> float:
        """Period length in seconds.

        >>> from hydpy import Period
        >>> Period("2d").seconds
        172800.0
        """
        return self.timedelta.total_seconds()

    @property
    def minutes(self) -> float:
        """Period length in minutes.

        >>> from hydpy import Period
        >>> Period("2d").minutes
        2880.0
        """
        return self.timedelta.total_seconds() / 60

    @property
    def hours(self) -> float:
        """Period length in hours.

        >>> from hydpy import Period
        >>> Period("2d").hours
        48.0
        """
        return self.timedelta.total_seconds() / 3600

    @property
    def days(self) -> float:
        """Period length in days.

        >>> from hydpy import Period
        >>> Period("2d").days
        2.0
        """
        return self.timedelta.total_seconds() / 86400

    def check(self) -> None:
        """Raise a |RuntimeError| if the step size is undefined at the moment.

        >>> from hydpy import Period
        >>> Period("1d").check()
        >>> Period().check()
        Traceback (most recent call last):
        ...
        RuntimeError: No step size defined at the moment.
        """
        if not self:
            raise RuntimeError("No step size defined at the moment.")

    def __bool__(self) -> bool:
        return bool(getattr(self, "timedelta", None))

    @overload
    def __add__(self: TypePeriod, other: Date | datetime_.datetime) -> Date:
        """Add the |Period| object to a |Date| object."""

    @overload
    def __add__(self: TypePeriod, other: Period | datetime_.timedelta) -> TypePeriod:
        """Add the |Period| object to another |Period| object."""

    @overload
    def __add__(self: TypePeriod, other: str) -> Date | TypePeriod:
        """Result depends on the actual string."""

    def __add__(
        self: TypePeriod,
        other: Date | datetime_.datetime | Period | datetime_.timedelta | str,
    ) -> Date | TypePeriod:
        if isinstance(other, (Date, datetime_.datetime, str)):
            try:
                other = Date(other)
                new = Date(other.datetime + self.timedelta)
                new.style = other.style
                return new
            except BaseException:
                pass
        if isinstance(other, (Period, datetime_.timedelta, str)):
            try:
                timedelta = self.timedelta + type(self)(other).timedelta
                return type(self).from_timedelta(timedelta)
            except BaseException:
                pass
        raise TypeError(
            f"Object `{other}` of type `{type(other).__name__}` "
            f"cannot be added to a `Period` instance."
        )

    @overload
    def __radd__(self, other: Date | datetime_.datetime) -> Date:
        """Add the |Period| object to a |Date| object."""

    @overload
    def __radd__(self: TypePeriod, other: Period | datetime_.timedelta) -> TypePeriod:
        """Add the |Period| object to another |Period| object."""

    @overload
    def __radd__(self: TypePeriod, other: str) -> Date | TypePeriod:
        """Result depends on the string."""

    def __radd__(  # type: ignore
        self: TypePeriod,
        other: Date | datetime_.datetime | Period | datetime_.timedelta | str,
    ) -> Date | TypePeriod:
        # without more flexible ways to relate types to string patterns, there is
        # nothing we can do about it (except providing a less flexible interface, of
        # course)
        return self.__add__(other)

    def __iadd__(  # type: ignore
        self: TypePeriod, other: PeriodConstrArg
    ) -> TypePeriod:
        # without more flexible ways to relate types to string patterns, there is
        # nothing we can do about it (except providing a less flexible interface, of
        # course)
        self.timedelta += type(self)(other).timedelta
        return self

    def __sub__(self: TypePeriod, other: PeriodConstrArg) -> TypePeriod:
        return type(self).from_timedelta(self.timedelta - type(self)(other).timedelta)

    @overload
    def __rsub__(  # type: ignore
        self: TypePeriod, other: Date | datetime_.datetime
    ) -> TypePeriod:
        # without more flexible ways to relate types to string patterns, there is
        # nothing we can do about it (except providing a less flexible interface, of
        # course)
        """Subtract the |Period| object from a |Date| object."""

    @overload
    def __rsub__(self, other: Period | datetime_.timedelta) -> Date:  # type: ignore
        # without more flexible ways to relate types to string patterns, there is
        # nothing we can do about it (except providing a less flexible interface, of
        # course)
        """Subtract the |Period| object from another |Period| object."""

    @overload
    def __rsub__(self: TypePeriod, other: str) -> Date | TypePeriod:
        """Result depends on string."""

    def __rsub__(
        self: TypePeriod,
        other: Date | datetime_.datetime | Period | datetime_.timedelta | str,
    ) -> Date | TypePeriod:
        if isinstance(other, (Date, datetime_.datetime, str)):
            try:
                other = Date(other)
                new = Date(other.datetime - self.timedelta)
                new.style = other.style
                return new
            except BaseException:
                pass
        if isinstance(other, (Period, datetime_.timedelta, str)):
            try:
                timedelta = type(self)(other).timedelta - self.timedelta
                return type(self).from_timedelta(timedelta)
            except BaseException:
                pass
        raise TypeError(
            f"A `Period` instance cannot be subtracted from object `{other}` of type "
            f"`{type(other).__name__}`."
        )

    def __isub__(self: TypePeriod, other: PeriodConstrArg) -> TypePeriod:
        self.timedelta -= type(self)(other).timedelta
        return self

    def __mul__(self: TypePeriod, other: float) -> TypePeriod:
        return type(self).from_timedelta(self.timedelta * other)

    def __rmul__(self: TypePeriod, other: float) -> TypePeriod:
        return self.__mul__(other)

    def __imul__(self: TypePeriod, other: float) -> TypePeriod:
        self.timedelta *= other
        return self

    @overload
    def __truediv__(self, other: PeriodConstrArg) -> float:
        """Divide the |Period| object through another |Period| object."""

    @overload
    def __truediv__(self: TypePeriod, other: float) -> TypePeriod:
        """Divide the |Period| object through a number object."""

    def __truediv__(
        self: TypePeriod, other: PeriodConstrArg | float
    ) -> TypePeriod | float:
        if isinstance(other, (float, int)):
            return type(self).from_timedelta(self.timedelta / other)
        return self.seconds / type(self)(other).seconds

    def __rtruediv__(self, other: PeriodConstrArg) -> float:
        return type(self)(other).seconds / self.seconds

    def __itruediv__(self: TypePeriod, other: float) -> TypePeriod:  # type: ignore
        # without more flexible ways to relate types to string patterns, there is
        # nothing we can do about it (except providing a less flexible interface, of
        # course)
        self.timedelta /= other
        return self

    def __floordiv__(self, other: PeriodConstrArg) -> int:
        return self.timedelta // type(self)(other).timedelta

    def __rfloordiv__(self, other: PeriodConstrArg) -> int:
        return type(self)(other).timedelta // self.timedelta

    def __mod__(self: TypePeriod, other: PeriodConstrArg) -> TypePeriod:
        return type(self).from_timedelta(self.timedelta % type(self)(other).timedelta)

    def __rmod__(self: TypePeriod, other: Period | datetime_.timedelta) -> TypePeriod:
        return type(self).from_timedelta(type(self)(other).timedelta % self.timedelta)

    def __pos__(self: TypePeriod) -> TypePeriod:
        return type(self).from_timedelta(self.timedelta)

    def __neg__(self: TypePeriod) -> TypePeriod:
        return type(self).from_timedelta(-self.timedelta)

    def __abs__(self: TypePeriod) -> TypePeriod:
        return type(self).from_timedelta(abs(self.timedelta))

    def __lt__(self, other: PeriodConstrArg) -> bool:
        return self.timedelta < type(self)(other).timedelta

    def __le__(self, other: PeriodConstrArg) -> bool:
        return self.timedelta <= type(self)(other).timedelta

    def __eq__(self, other: Any) -> bool:
        try:
            return self.timedelta == type(self)(other).timedelta
        except BaseException:
            return False

    def __ne__(self, other: Any) -> bool:
        try:
            return self.timedelta != type(self)(other).timedelta
        except BaseException:
            return True

    def __gt__(self, other: PeriodConstrArg) -> bool:
        return self.timedelta > type(self)(other).timedelta

    def __ge__(self, other: PeriodConstrArg) -> bool:
        return self.timedelta >= type(self)(other).timedelta

    def __str__(self) -> str:
        if self.unit == "d":
            return f"{self.days:.0f}d"
        if self.unit == "h":
            return f"{self.hours:.0f}h"
        if self.unit == "m":
            return f"{self.minutes:.0f}m"
        return f"{self.seconds:.0f}s"

    def __repr__(self) -> str:
        if self:
            return f'Period("{str(self)}")'
        return "Period()"


class Timegrid:
    """Defines an arbitrary number of equidistant dates via the first date, the last
    date, and the step size between subsequent dates.

    In hydrological modelling, input (and output) data are usually only available with
    a certain resolution, which also determines the possible resolution of the actual
    simulation.  Class |Timegrid| reflects this situation by representing equidistant
    dates.

    To initialise a |Timegrid|, pass its first date, its last date and its stepsize as
    |str| objects, |Date| and |Period| objects, or |datetime.datetime| and
    |datetime.timedelta| objects (combinations are allowed):

    >>> from hydpy import Date, Period, Timegrid
    >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
    >>> timegrid
    Timegrid("2000-01-01 00:00:00",
             "2001-01-01 00:00:00",
             "1d")
    >>> timegrid == Timegrid(
    ...     Date("2000-01-01"), Date("2001-01-01"), Period("1d"))
    True
    >>> from datetime import datetime, timedelta
    >>> timegrid == Timegrid(
    ...     datetime(2000, 1, 1), datetime(2001, 1, 1), timedelta(1))
    True

    Passing unsupported argument types results in errors like the following:

    >>> Timegrid("2000-01-01", "2001-01-01", 1)
    Traceback (most recent call last):
    ...
    TypeError: While trying to prepare a Trimegrid object based on the arguments \
`2000-01-01`, `2001-01-01`, and `1`, the following error occurred: While trying to \
initialise a `Period` object based argument `1`, the following error occurred: The \
supplied argument must be either an instance of `Period`, `datetime.timedelta`, or \
`str`, but the given type is `int`.

    You can query indices and the corresponding dates via indexing:

    >>> timegrid[0]
    Date("2000-01-01 00:00:00")
    >>> timegrid[5]
    Date("2000-01-06 00:00:00")
    >>> timegrid[Date("2000-01-01")]
    0
    >>> timegrid["2000-01-06"]
    5

    Indexing beyond the ranges of the actual period is allowed:

    >>> timegrid[-365]
    Date("1999-01-01 00:00:00")
    >>> timegrid["2002-01-01"]
    731

    However, dates that do not precisely match the defined grid result in the following
    error:

    >>> timegrid["2001-01-01 12:00"]
    Traceback (most recent call last):
    ...
    ValueError: The given date `2001-01-01 12:00:00` is not properly alligned on the \
indexed timegrid `Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")`.

    You can determine the length of and iterate over |Timegrid| objects:

    >>> len(timegrid)
    366
    >>> for date in timegrid:
    ...     print(date)  # doctest: +ELLIPSIS
    2000-01-01 00:00:00
    2000-01-02 00:00:00
    ...
    2000-12-30 00:00:00
    2000-12-31 00:00:00

    By default, iteration yields the left-side timestamps (the start points) of the
    respective intervals.  Set the |Options.timestampleft| option to |False| of you
    prefer the right-side timestamps:

    >>> from hydpy import pub
    >>> with pub.options.timestampleft(False):
    ...     for date in timegrid:
    ...         print(date)  # doctest: +ELLIPSIS
    2000-01-02 00:00:00
    2000-01-03 00:00:00
    ...
    2000-12-31 00:00:00
    2001-01-01 00:00:00

    You can check |Timegrid| instances for equality:

    >>> timegrid == Timegrid("2000-01-01", "2001-01-01", "1d")
    True
    >>> timegrid != Timegrid("2000-01-01", "2001-01-01", "1d")
    False
    >>> timegrid == Timegrid("2000-01-02", "2001-01-01", "1d")
    False
    >>> timegrid == Timegrid("2000-01-01", "2001-01-02", "1d")
    False
    >>> timegrid == Timegrid("2000-01-01", "2001-01-01", "2d")
    False
    >>> timegrid == 1
    False

    Also, you can check if a date or even the whole timegrid lies within a span defined
    by a |Timegrid| instance (note unaligned dates and time grids with different step
    sizes are considered unequal):

    >>> Date("2000-01-01") in timegrid
    True
    >>> "2001-01-01" in timegrid
    True
    >>> "2000-07-01" in timegrid
    True
    >>> "1999-12-31" in timegrid
    False
    >>> "2001-01-02" in timegrid
    False
    >>> "2001-01-02 12:00" in timegrid
    False

    >>> timegrid in Timegrid("2000-01-01", "2001-01-01", "1d")
    True
    >>> timegrid in Timegrid("1999-01-01", "2002-01-01", "1d")
    True
    >>> timegrid in Timegrid("2000-01-02", "2001-01-01", "1d")
    False
    >>> timegrid in Timegrid("2000-01-01", "2000-12-31", "1d")
    False
    >>> timegrid in Timegrid("2000-01-01", "2001-01-01", "2d")
    False

    For convenience, you can temporarily modify the attributes of a |Timegrid| object
    by calling it after the `with` statement:

    >>> with timegrid("1999-01-01", "2002-01-01", "1h"):
    ...     print(timegrid)
    Timegrid("1999-01-01 00:00:00", "2002-01-01 00:00:00", "1h")
    >>> print(timegrid)
    Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")

    You are free to select the attributes you want to change (see method
    |Timegrid.modify| for further information) or to change specific attributes later
    within the `with` block:

    >>> with timegrid(lastdate=None) as tg:
    ...     print(timegrid)
    ...     timegrid.firstdate = "1999-01-01"
    ...     tg.lastdate = "2002-01-01"
    ...     tg.stepsize = "1h"
    ...     print(timegrid)
    Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")
    Timegrid("1999-01-01 00:00:00", "2002-01-01 00:00:00", "1h")
    >>> print(timegrid)
    Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")
    """

    _copy: Timegrid

    def __init__(
        self,
        firstdate: DateConstrArg,
        lastdate: DateConstrArg,
        stepsize: PeriodConstrArg,
    ) -> None:
        try:
            self.firstdate = firstdate
            self.lastdate = lastdate
            self.stepsize = stepsize
            self.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to prepare a Trimegrid object based on the arguments "
                f"`{firstdate}`, `{lastdate}`, and `{stepsize}`"
            )

    def _get_firstdate(self) -> Date:
        """The start date of the relevant period.

        You can query and alter the value of property |Timegrid.firstdate| (call method
        |Timegrid.verify| afterwards to make sure the |Timegrid| object did not become
        ill-defined):

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
        >>> timegrid.firstdate
        Date("2000-01-01 00:00:00")
        >>> timegrid.firstdate += "1d"
        >>> timegrid
        Timegrid("2000-01-02 00:00:00",
                 "2001-01-01 00:00:00",
                 "1d")
        """
        return cast(Date, vars(self)["firstdate"])

    def _set_firstdate(self, firstdate: DateConstrArg) -> None:
        vars(self)["firstdate"] = Date(firstdate)

    firstdate = propertytools.Property[DateConstrArg, Date](
        fget=_get_firstdate, fset=_set_firstdate
    )

    def _get_lastdate(self) -> Date:
        """The end date of the relevant period.

        You can query and alter the value of property |Timegrid.lastdate| (call method
        |Timegrid.verify| afterwards to make sure the |Timegrid| object did not become
        ill-defined):

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
        >>> timegrid.lastdate
        Date("2001-01-01 00:00:00")
        >>> timegrid.lastdate += "1d"
        >>> timegrid
        Timegrid("2000-01-01 00:00:00",
                 "2001-01-02 00:00:00",
                 "1d")
        """
        return cast(Date, vars(self)["lastdate"])

    def _set_lastdate(self, lastdate: DateConstrArg) -> None:
        vars(self)["lastdate"] = Date(lastdate)

    lastdate = propertytools.Property[DateConstrArg, Date](
        fget=_get_lastdate, fset=_set_lastdate
    )

    def _get_dates(self) -> tuple[Date, Date]:
        """Shortcut to get or set both property |Timegrid.firstdate| and property
        |Timegrid.lastdate| in one step.

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
        >>> timegrid.dates
        (Date("2000-01-01 00:00:00"), Date("2001-01-01 00:00:00"))
        >>> timegrid.dates = "2002-01-01", "2003-01-01"
        >>> timegrid.firstdate
        Date("2002-01-01 00:00:00")
        >>> timegrid.lastdate
        Date("2003-01-01 00:00:00")
        """
        return self.firstdate, self.lastdate

    def _set_dates(self, dates: tuple[DateConstrArg, DateConstrArg]) -> None:
        self.firstdate = dates[0]
        self.lastdate = dates[1]

    dates = propertytools.Property[
        tuple[DateConstrArg, DateConstrArg], tuple[Date, Date]
    ](fget=_get_dates, fset=_set_dates)

    def _get_stepsize(self) -> Period:
        """The time series data and simulation step size.

        You can query and alter the value of property |Timegrid.stepsize| (call method
        |Timegrid.verify| afterwards to make sure the |Timegrid| object did not become
        ill-defined):

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
        >>> timegrid.stepsize
        Period("1d")
        >>> timegrid.stepsize += "1d"
        >>> timegrid
        Timegrid("2000-01-01 00:00:00",
                 "2001-01-01 00:00:00",
                 "2d")
        """
        return cast(Period, vars(self)["stepsize"])

    def _set_stepsize(self, stepsize: PeriodConstrArg) -> None:
        vars(self)["stepsize"] = Period(stepsize)

    stepsize = propertytools.Property[PeriodConstrArg, Period](
        _get_stepsize, _set_stepsize
    )

    @classmethod
    def from_array(cls: type[TypeTimegrid], array: NDArrayFloat) -> TypeTimegrid:
        """Create a |Timegrid| instance based on information stored in the first 13
        rows of a |numpy.ndarray| object and return it.

        In *HydPy*, external time series files do define the time-related reference of
        their data on their own.  For the |numpy| `npy` binary format, we achieve this
        by reserving the first six entries for the first date of the period, the next
        six entries for the last date of the period, and the last entry for the step
        size (in seconds):

        >>> from numpy import array
        >>> array_ = array([2000, 1, 1, 0, 0, 0,    # first date
        ...                 2000, 1, 1, 7, 0, 0,    # second date
        ...                 3600,                   # step size (in seconds)
        ...                 1, 2, 3, 4, 5, 6, 7])   # data

        Use method |Timegrid.from_array| to extract the time information:

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid.from_array(array_)
        >>> timegrid
        Timegrid("2000-01-01 00:00:00",
                 "2000-01-01 07:00:00",
                 "1h")

        Too little information results in the following error message:

        >>> Timegrid.from_array(array_[:12])
        Traceback (most recent call last):
        ...
        IndexError: To define a Timegrid instance via an array, 13 numbers are \
required, but the given array consist of 12 entries/rows only.

        The inverse method |Timegrid.to_array| creates a new |numpy| |numpy.ndarray|
        based on the current |Timegrid| object:

        >>> from hydpy import round_
        >>> round_(timegrid.to_array())
        2000.0, 1.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 1.0, 1.0, 7.0, 0.0, 0.0, 3600.0
        """
        try:
            return cls(
                Date.from_array(array[:6]),
                Date.from_array(array[6:12]),
                Period.from_seconds(array[12].flat[0]),
            )
        except IndexError:
            raise IndexError(
                f"To define a Timegrid instance via an array, 13 numbers are "
                f"required, but the given array consist of {len(array)} entries/rows "
                f"only."
            ) from None

    def to_array(self) -> NDArrayFloat:
        """Return a 1-dimensional |numpy| |numpy.ndarray| storing the information of
        the actual |Timegrid| object.

        See the documentation on method |Timegrid.from_array| for more information.
        """
        values = numpy.empty(13, dtype=config.NP_FLOAT)
        values[:6] = self.firstdate.to_array()
        values[6:12] = self.lastdate.to_array()
        values[12] = self.stepsize.seconds
        return values

    @classmethod
    def from_timepoints(
        cls: type[TypeTimegrid],
        timepoints: Sequence[float],
        refdate: DateConstrArg,
        unit: TypeUnit = "hours",
    ) -> TypeTimegrid:
        """Return a |Timegrid| object representing the given starting `timepoints`
        related to the given `refdate`.

        At least two given time points must be increasing and equidistant.  By default,
        |Timegrid.from_timepoints| assumes them as hours elapsed since the given
        reference date:

        >>> from hydpy import Timegrid
        >>> Timegrid.from_timepoints([0.0, 6.0, 12.0, 18.0], "01.01.2000")
        Timegrid("01.01.2000 00:00:00",
                 "02.01.2000 00:00:00",
                 "6h")
        >>> Timegrid.from_timepoints([24.0, 30.0, 36.0, 42.0], "1999-12-31")
        Timegrid("2000-01-01 00:00:00",
                 "2000-01-02 00:00:00",
                 "6h")

        You can pass other time units (`days` or `min`) explicitly (only the first
        character counts):

        >>> Timegrid.from_timepoints([0.0, 0.25, 0.5, 0.75], "01.01.2000", unit="d")
        Timegrid("01.01.2000 00:00:00",
                 "02.01.2000 00:00:00",
                 "6h")
        >>> Timegrid.from_timepoints([1.0, 1.25, 1.5, 1.75], "1999-12-31", unit="days")
        Timegrid("2000-01-01 00:00:00",
                 "2000-01-02 00:00:00",
                 "6h")

        When setting the |Options.timestampleft| option to |False|,
        |Timegrid.from_timepoints| assumes each time point to define the right side
        (the end) of a time interval.  Repeating the above examples with this
        modification shifts the |Timegrid.firstdate| and the |Timegrid.lastdate| of the
        returned |Timegrid| objects to the left:

        >>> from hydpy import pub
        >>> with pub.options.timestampleft(False):
        ...     Timegrid.from_timepoints([0.0, 6.0, 12.0, 18.0], "01.01.2000")
        Timegrid("31.12.1999 18:00:00",
                 "01.01.2000 18:00:00",
                 "6h")
        >>> with pub.options.timestampleft(False):
        ...     Timegrid.from_timepoints([24.0, 30.0, 36.0, 42.0], "1999-12-31")
        Timegrid("1999-12-31 18:00:00",
                 "2000-01-01 18:00:00",
                 "6h")
        >>> with pub.options.timestampleft(False):
        ...     Timegrid.from_timepoints([0.0, 0.25, 0.5, 0.75], "01.01.2000", unit="d")
        Timegrid("31.12.1999 18:00:00",
                 "01.01.2000 18:00:00",
                 "6h")
        >>> with pub.options.timestampleft(False):
        ...     Timegrid.from_timepoints([1.0, 1.25, 1.5, 1.75], "1999-12-31", unit="d")
        Timegrid("1999-12-31 18:00:00",
                 "2000-01-01 18:00:00",
                 "6h")
        """
        refdate = Date(refdate)
        period = Period.from_cfunits(unit)
        delta = timepoints[1] - timepoints[0]
        shift = 0.0 if hydpy.pub.options.timestampleft else -delta
        firstdate = refdate + (timepoints[0] + shift) * period
        lastdate = refdate + (timepoints[-1] + delta + shift) * period
        stepsize = (lastdate - firstdate) / len(timepoints)
        return cls(firstdate, lastdate, stepsize)

    def to_timepoints(
        self, unit: TypeUnit = "hours", offset: float | PeriodConstrArg = 0.0
    ) -> numpy.ndarray:
        """Return a |numpy.ndarray| representing the starting time points of the
        |Timegrid| object.

        By default, method |Timegrid.to_timepoints| returns the time elapsed since the
        |Timegrid.firstdate| in hours:

        >>> from hydpy import print_vector, Timegrid
        >>> timegrid = Timegrid("2000-01-01", "2000-01-02", "6h")
        >>> print_vector(timegrid.to_timepoints())
        0.0, 6.0, 12.0, 18.0

        You can define other time units (`days` or `min`) (only the first character
        counts):

        >>> print_vector(timegrid.to_timepoints(unit="d"))
        0.0, 0.25, 0.5, 0.75

        Additionally, one can pass an `offset` that must be of type |int| or a valid
        |Period| initialisation argument:

        >>> print_vector(timegrid.to_timepoints(offset=24))
        24.0, 30.0, 36.0, 42.0
        >>> print_vector(timegrid.to_timepoints(offset="1d"))
        24.0, 30.0, 36.0, 42.0
        >>> print_vector(timegrid.to_timepoints(unit="days", offset="1d"))
        1.0, 1.25, 1.5, 1.75

        When setting the |Options.timestampleft| option to |False|,
        |Timegrid.to_timepoints| assumes each time point to define the right side
        (the end) of a time interval.  Repeating the above examples with this
        modification shifts the time points of the returned |numpy.ndarray| objects to
        the right:

        >>> from hydpy import pub
        >>> with pub.options.timestampleft(False):
        ...     print_vector(timegrid.to_timepoints())
        6.0, 12.0, 18.0, 24.0
        >>> with pub.options.timestampleft(False):
        ...     print_vector(timegrid.to_timepoints(unit="d"))
        0.25, 0.5, 0.75, 1.0
        >>> with pub.options.timestampleft(False):
        ...     print_vector(timegrid.to_timepoints(offset=24))
        30.0, 36.0, 42.0, 48.0
        >>> with pub.options.timestampleft(False):
        ...     print_vector(timegrid.to_timepoints(offset="1d"))
        30.0, 36.0, 42.0, 48.0
        >>> with pub.options.timestampleft(False):
        ...     print_vector(timegrid.to_timepoints(unit="days", offset="1d"))
        1.25, 1.5, 1.75, 2.0
        """
        period = Period.from_cfunits(unit)
        if not isinstance(offset, (float, int)):
            offset = Period(offset) / period
        step = self.stepsize / period
        if not hydpy.pub.options.timestampleft:
            offset += step
        nmb = len(self)
        variable = numpy.linspace(offset, offset + step * (nmb - 1), nmb)
        return variable

    def array2series(self, array: NDArrayFloat) -> NDArrayFloat:
        """Prefix the information of the actual |Timegrid| object to the given array
        and return it.

        The |Timegrid| information is available in the first thirteen values of the
        first axis of the returned series (see the documentation on the method
        |Timegrid.from_array|).

        To show how method |Timegrid.array2series| works, we first apply it on a simple
        list containing numbers:

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("2000-11-01 00:00", "2000-11-01 04:00", "1h")
        >>> series = timegrid.array2series([1, 2, 3.5, "5.0"])

        The first six entries contain the first date of the timegrid (year, month, day,
        hour, minute, second):

        >>> from hydpy import round_
        >>> round_(series[:6])
        2000.0, 11.0, 1.0, 0.0, 0.0, 0.0

        The six subsequent entries contain the last date:

        >>> round_(series[6:12])
        2000.0, 11.0, 1.0, 4.0, 0.0, 0.0

        The thirteens value is the step size in seconds:

        >>> round_(series[12])
        3600.0

        The last four values are the ones of the given vector:

        >>> round_(series[-4:])
        1.0, 2.0, 3.5, 5.0

        The given array can have an arbitrary number of dimensions:

        >>> import numpy
        >>> array = numpy.eye(4)
        >>> series = timegrid.array2series(array)

        Now the timegrid information is stored in the first column:

        >>> round_(series[:13, 0])
        2000.0, 11.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 11.0, 1.0, 4.0, 0.0, 0.0, \
3600.0

        All other columns of the first thirteen rows contain |numpy.nan| values:

        >>> round_(series[12, :])
        3600.0, nan, nan, nan

        The original values are available in the last four rows:

        >>> round_(series[13, :])
        1.0, 0.0, 0.0, 0.0

        Inappropriate array objects result in error messages like the following:

        >>> timegrid.array2series([[1, 2], [3]])
        Traceback (most recent call last):
        ...
        ValueError: While trying to prefix timegrid information to the given array, \
the following error occurred: setting an array element with a sequence. The requested \
array has an inhomogeneous shape after 1 dimensions. The detected shape was (2,) + \
inhomogeneous part.

        The following error occurs when the given array does not fit the defined time
        grid:

        >>> timegrid.array2series([[1, 2], [3, 4]])
        Traceback (most recent call last):
        ...
        ValueError: When converting an array to a sequence, the lengths of the \
timegrid and the given array must be equal, but the length of the timegrid object is \
`4` and the length of the array object is `2`.
        """
        try:
            array = numpy.array(array, dtype=config.NP_FLOAT)
        except BaseException:
            objecttools.augment_excmessage(
                "While trying to prefix timegrid information to the given array"
            )
        if len(array) != len(self):
            raise ValueError(
                f"When converting an array to a sequence, the lengths of the timegrid "
                f"and the given array must be equal, but the length of the timegrid "
                f"object is `{len(self)}` and the length of the array object is "
                f"`{len(array)}`."
            )
        shape = list(array.shape)
        shape[0] += 13
        series = numpy.full(shape, numpy.nan)
        slices = [slice(0, 13)]
        subshape = [13]
        for dummy in range(1, series.ndim):
            slices.append(slice(0, 1))
            subshape.append(1)
        series[tuple(slices)] = self.to_array().reshape(subshape)
        series[13:] = array
        return series

    def verify(self) -> None:
        """Raise a |ValueError| if the dates or the step size of the |Timegrid| object
        are currently inconsistent.

        Method |Timegrid.verify| is called at the end of the initialisation of a new
        |Timegrid| object automatically:

        >>> from hydpy import Timegrid
        >>> Timegrid("2001-01-01", "2000-01-01", "1d")
        Traceback (most recent call last):
        ...
        ValueError: While trying to prepare a Trimegrid object based on the arguments \
`2001-01-01`, `2000-01-01`, and `1d`, the following error occurred: The temporal \
sequence of the first date (`2001-01-01 00:00:00`) and the last date \
(`2000-01-01 00:00:00`) is inconsistent.

        However, the same does not hold when changing property |Timegrid.firstdate|,
        |Timegrid.lastdate|, or |Timegrid.stepsize|:

        >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
        >>> timegrid.stepsize = "4d"

        When in doubt, call method |Timegrid.verify| manually:

        >>> timegrid.verify()
        Traceback (most recent call last):
        ...
        ValueError: The interval between the first date (`2000-01-01 00:00:00`) and \
the last date (`2001-01-01 00:00:00`) is `366d`, which is not an integral multiple of \
the step size `4d`.
        """
        if self.firstdate >= self.lastdate:
            raise ValueError(
                f"The temporal sequence of the first date (`{self.firstdate}`) and "
                f"the last date (`{self.lastdate}`) is inconsistent."
            )
        if (self.lastdate - self.firstdate) % self.stepsize:
            raise ValueError(
                f"The interval between the first date (`{self.firstdate}`) and the "
                f"last date (`{self.lastdate}`) is `{self.lastdate-self.firstdate}`, "
                f"which is not an integral multiple of the step size `{self.stepsize}`."
            )

    def modify(
        self,
        firstdate: DateConstrArg | None = None,
        lastdate: DateConstrArg | None = None,
        stepsize: PeriodConstrArg | None = None,
    ) -> None:
        """Modify one or more |Timegrid| attributes in one step.

        If you want to change all attributes of an existing |Timegrid| object,  it is
        often most convenient to do so in one step via method |Timegrid.modify|:

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("2000-01-01", "2001-01-01", "1d")
        >>> timegrid.modify("1999-01-01", "2002-01-01", "1h")
        >>> timegrid
        Timegrid("1999-01-01 00:00:00",
                 "2002-01-01 00:00:00",
                 "1h")

        Another benefit of method |Timegrid.modify| is that all changes are optional.
        Ignore an argument or set it to |None| explicitly to leave the corresponding
        attribute unchanged:

        >>> timegrid.modify(None, stepsize=None)
        >>> timegrid
        Timegrid("1999-01-01 00:00:00",
                 "2002-01-01 00:00:00",
                 "1h")
        """
        if firstdate is not None:
            self.firstdate = firstdate
        if lastdate is not None:
            self.lastdate = lastdate
        if stepsize is not None:
            self.stepsize = stepsize

    @contextlib.contextmanager
    def __call__(
        self,
        firstdate: DateConstrArg | None = None,
        lastdate: DateConstrArg | None = None,
        stepsize: PeriodConstrArg | None = None,
    ) -> Iterator[Timegrid]:
        firstdate_copy = self.firstdate
        lastdate_copy = self.lastdate
        stepsize_copy = self.stepsize
        try:
            self.modify(firstdate=firstdate, lastdate=lastdate, stepsize=stepsize)
            yield self
        finally:
            self.firstdate = firstdate_copy
            self.lastdate = lastdate_copy
            self.stepsize = stepsize_copy

    def __len__(self) -> int:
        return abs(int((self.lastdate - self.firstdate) / self.stepsize))

    @overload
    def __getitem__(self, key: int) -> Date:
        """Get the date corresponding to the given index value."""

    @overload
    def __getitem__(self, key: DateConstrArg) -> int:
        """Get the index value corresponding to the given date."""

    def __getitem__(self, key: int | DateConstrArg) -> Date | int:
        if isinstance(key, (int, float)):
            return Date(self.firstdate + key * self.stepsize)
        key = Date(key)
        index = (key - self.firstdate) / self.stepsize
        if index % 1.0:
            raise ValueError(
                f"The given date `{key}` is not properly alligned on the indexed "
                f"timegrid `{self}`."
            )
        return int(index)

    def __iter__(self) -> Iterator[Date]:
        dt = copy.deepcopy(self.firstdate).datetime
        last_dt = self.lastdate.datetime
        td = self.stepsize.timedelta
        if not hydpy.pub.options.timestampleft:
            dt += td
            last_dt += td
        from_datetime = Date.from_datetime
        while dt < last_dt:
            yield from_datetime(dt)
            dt = dt + td

    def _containsdate(self, date: Date) -> bool:
        return (self.firstdate <= date <= self.lastdate) and not (
            (date - self.firstdate) % self.stepsize
        )

    def _containstimegrid(self, timegrid: Timegrid) -> bool:
        return (
            self._containsdate(timegrid.firstdate)
            and self._containsdate(timegrid.lastdate)
            and (timegrid.stepsize == self.stepsize)
        )

    def __contains__(self, other: DateConstrArg | Timegrid) -> bool:
        if isinstance(other, Timegrid):
            return self._containstimegrid(other)
        return self._containsdate(Date(other))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Timegrid):
            return (
                (self.firstdate == other.firstdate)
                and (self.lastdate == other.lastdate)
                and (self.stepsize == other.stepsize)
            )
        return False

    def __repr__(self) -> str:
        return self.assignrepr("")

    def __str__(self) -> str:
        return objecttools.flatten_repr(self)

    def assignrepr(
        self, prefix: str, style: str | None = None, utcoffset: int | None = None
    ) -> str:
        """Return a |repr| string with a prefixed assignment.

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid("1996-11-01 00:00:00",
        ...                     "1997-11-01 00:00:00",
        ...                     "1d")
        >>> print(timegrid.assignrepr(prefix="timegrid = "))
        timegrid = Timegrid("1996-11-01 00:00:00",
                            "1997-11-01 00:00:00",
                            "1d")

        >>> print(timegrid.assignrepr(
        ...     prefix="", style="iso1", utcoffset=120))
        Timegrid("1996-11-01T01:00:00+02:00",
                 "1997-11-01T01:00:00+02:00",
                 "1d")
        """
        skip = len(prefix) + 9
        blanks = " " * skip
        return (
            f'{prefix}Timegrid("'
            f'{self.firstdate.to_string(style, utcoffset)}",\n'
            f'{blanks}"{self.lastdate.to_string(style, utcoffset)}",\n'
            f'{blanks}"{str(self.stepsize)}")'
        )


class Timegrids:
    """Handles the "initialisation", the "simulation", and the "evaluation |Timegrid|
    object of a *HydPy* project.

    The HydPy framework distinguishes three "time frames", one associated with the
    initialisation period (|Timegrids.init|), one associated with the actual simulation
    period (|Timegrids.sim|), and one associated with the actual evaluation period
    (|Timegrids.eval_|).  These time frames are represented by three different
    |Timegrid| objects, which are each handled by a single |Timegrid| object.

    There is usually only one |Timegrids| object required within a *HydPy* project
    available as attribute `timegrids` of module |pub|.  You have to create such an
    object at the beginning of your workflow.

    In many cases, one either wants to perform simulations and evaluations covering the
    whole initialisation period or not perform any simulation or evaluation.  In these
    situations, you can pass a single |Timegrid| instance to the constructor of class
    |Timegrids|:

    >>> from hydpy import Timegrid, Timegrids
    >>> timegrids = Timegrids(Timegrid("2000-01-01", "2001-01-01", "1d"))
    >>> print(timegrids)
    Timegrids("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")

    An even shorter approach is to pass the arguments of the |Timegrid| constructor
    directly:

    >>> timegrids == Timegrids("2000-01-01", "2001-01-01", "1d")
    True

    To define a simulation time grid different from the initialisation time grid, pass
    both as two individual |Timegrid| objects:

    >>> timegrids = Timegrids(Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...                       Timegrid("2000-01-01", "2000-07-01", "1d"))

    The evaluation time grid then corresponds to the simulation time grid:

    >>> timegrids
    Timegrids(init=Timegrid("2000-01-01 00:00:00",
                            "2001-01-01 00:00:00",
                            "1d"),
              sim=Timegrid("2000-01-01 00:00:00",
                           "2000-07-01 00:00:00",
                           "1d"),
              eval_=Timegrid("2000-01-01 00:00:00",
                             "2000-07-01 00:00:00",
                             "1d"))

    Of course, you can also define a separate evaluation period:

    >>> timegrids = Timegrids(Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...                       Timegrid("2000-01-01", "2000-07-01", "1d"),
    ...                       Timegrid("2000-06-01", "2000-07-01", "1d"))
    >>> timegrids.init
    Timegrid("2000-01-01 00:00:00",
             "2001-01-01 00:00:00",
             "1d")
    >>> timegrids.sim
    Timegrid("2000-01-01 00:00:00",
             "2000-07-01 00:00:00",
             "1d")
    >>> timegrids.eval_
    Timegrid("2000-06-01 00:00:00",
             "2000-07-01 00:00:00",
             "1d")

    Class |Timegrids| supports keyword arguments:

    >>> Timegrids(firstdate="2000-01-01 00:00:00",
    ...           lastdate="2001-01-01 00:00:00",
    ...           stepsize="1d")
    Timegrids("2000-01-01 00:00:00",
              "2001-01-01 00:00:00",
              "1d")

    >>> Timegrids("2000-01-01 00:00:00",
    ...           "2001-01-01 00:00:00",
    ...           stepsize="1d")
    Timegrids("2000-01-01 00:00:00",
              "2001-01-01 00:00:00",
              "1d")

    >>> Timegrids(init=Timegrid("2000-01-01 00:00:00",
    ...                         "2001-01-01 00:00:00",
    ...                         "1d"),
    ...           sim=Timegrid("2000-01-01 00:00:00",
    ...                        "2000-07-01 00:00:00",
    ...                        "1d"))
    Timegrids(init=Timegrid("2000-01-01 00:00:00",
                            "2001-01-01 00:00:00",
                            "1d"),
              sim=Timegrid("2000-01-01 00:00:00",
                           "2000-07-01 00:00:00",
                           "1d"),
              eval_=Timegrid("2000-01-01 00:00:00",
                             "2000-07-01 00:00:00",
                             "1d"))

    >>> Timegrids(init=Timegrid("2000-01-01 00:00:00",
    ...                         "2001-01-01 00:00:00",
    ...                         "1d"),
    ...           eval_=Timegrid("2000-06-01 00:00:00",
    ...                        "2000-07-01 00:00:00",
    ...                        "1d"))
    Timegrids(init=Timegrid("2000-01-01 00:00:00",
                            "2001-01-01 00:00:00",
                            "1d"),
              sim=Timegrid("2000-01-01 00:00:00",
                           "2001-01-01 00:00:00",
                           "1d"),
              eval_=Timegrid("2000-06-01 00:00:00",
                             "2000-07-01 00:00:00",
                             "1d"))

    Wrong arguments should result in understandable error messages:

    >>> Timegrids(1, 2, 3, 4)
    Traceback (most recent call last):
    ...
    TypeError: While trying to define a new `Timegrids` object based on the arguments \
`1, 2, 3, and 4`, the following error occurred: Initialising `Timegrids` objects \
requires one, two, or three arguments but `4` are given.

    >>> Timegrids("wrong")
    Traceback (most recent call last):
    ...
    ValueError: While trying to define a new `Timegrids` object based on the \
arguments `wrong`, the following error occurred: Initialising a `Timegrids` object \
either requires one, two, or three `Timegrid` objects or two dates objects (of type \
`Date`, `datetime`, or `str`) and one period object (of type `Period`, `timedelta`, \
or `str`), but objects of the types `str, None, and None` are given.

    >>> Timegrids(wrong=Timegrid("2000-01-01", "2001-01-01", "1d"))
    Traceback (most recent call last):
    ...
    TypeError: While trying to define a new `Timegrids` object based on the arguments \
`Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")`, the following error \
occurred: Initialising class `Timegrids` does not support the following given \
keywords: `wrong`.

    >>> Timegrids(
    ...     Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...     init=Timegrid("2000-01-01", "2001-01-01", "1d"))
    Traceback (most recent call last):
    ...
    TypeError: While trying to define a new `Timegrids` object based on the arguments \
`Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d") and \
Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")`, the following error \
occurred: There is a conflict between the given positional and keyword arguments.

    Two |Timegrids| objects are equal if all handled |Timegrid| objects are equal:

    >>> timegrids == Timegrids(
    ...     Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...     Timegrid("2000-01-01", "2000-07-01", "1d"),
    ...     Timegrid("2000-06-01", "2000-07-01", "1d"))
    True
    >>> timegrids == Timegrids(
    ...     Timegrid("1999-01-01", "2001-01-01", "1d"),
    ...     Timegrid("2000-01-01", "2000-07-01", "1d"),
    ...     Timegrid("2000-06-01", "2000-07-01", "1d"))
    False
    >>> timegrids == Timegrids(
    ...     Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...     Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...     Timegrid("2000-06-01", "2000-07-01", "1d"))
    False
    >>> timegrids == Timegrids(
    ...     Timegrid("2000-01-01", "2001-01-01", "1d"),
    ...     Timegrid("2000-01-01", "2000-07-01", "1d"),
    ...     Timegrid("2000-01-01", "2000-07-01", "1d"))
    False
    >>> timegrids == Date("2000-01-01")
    False

    .. role:: raw-html(raw)
       :format: html

    |Timegrids| objects are iterable and yield their |Timegrid| objects in the order
    |Timegrids.init| :raw-html:`&rarr;` |Timegrids.sim| :raw-html:`&rarr;`
    |Timegrids.eval_|:

    >>> for timegrid in timegrids:
    ...     print(timegrid)
    Timegrid("2000-01-01 00:00:00", "2001-01-01 00:00:00", "1d")
    Timegrid("2000-01-01 00:00:00", "2000-07-01 00:00:00", "1d")
    Timegrid("2000-06-01 00:00:00", "2000-07-01 00:00:00", "1d")
    """

    init: Timegrid
    """|Timegrid| object covering the whole initialisation period."""
    sim: Timegrid
    """|Timegrid| object covering the actual simulation period only."""
    eval_: Timegrid
    """|Timegrid| object covering the actual evaluation period only."""

    @overload
    def __init__(
        self, init: Timegrid, sim: Timegrid | None = ..., eval_: Timegrid | None = ...
    ) -> None:
        """from timegrids"""

    @overload
    def __init__(
        self,
        firstdate: DateConstrArg,
        lastdate: DateConstrArg,
        stepsize: PeriodConstrArg,
    ) -> None:
        """from timegrid constructor arguments"""

    def __init__(
        self,
        *args: None | Timegrid | DateConstrArg | PeriodConstrArg,
        **kwargs: None | Timegrid | DateConstrArg | PeriodConstrArg,
    ) -> None:
        values = list(args) + list(kwargs.values())
        try:
            if not 1 <= len(values) <= 3:
                raise TypeError(
                    f"Initialising `Timegrids` objects requires one, two, or three "
                    f"arguments but `{len(values)}` are given."
                )
            arguments: list[None | Timegrid | DateConstrArg | PeriodConstrArg] = [
                None,
                None,
                None,
            ]
            for idx, arg in enumerate(args):
                arguments[idx] = arg
            for idx, name in (
                (0, "init"),
                (1, "sim"),
                (2, "eval_"),
                (0, "firstdate"),
                (1, "lastdate"),
                (2, "stepsize"),
            ):
                value = kwargs.pop(name, None)
                if value is not None:
                    if arguments[idx] is None:
                        arguments[idx] = value
                    else:
                        raise TypeError(
                            "There is a conflict between the given positional and "
                            "keyword arguments."
                        )
            if kwargs:
                raise TypeError(
                    f"Initialising class `Timegrids` does not support the following "
                    f"given keywords: `{objecttools.enumeration(kwargs.keys())}`."
                )
            arg1, arg2, arg3 = arguments
            if (
                isinstance(arg1, Timegrid)
                and ((arg2 is None) or isinstance(arg2, Timegrid))
                and ((arg3 is None) or isinstance(arg3, Timegrid))
            ):
                self.init = copy.deepcopy(arg1)
                if arg2 is None:
                    self.sim = copy.deepcopy(self.init)
                else:
                    self.sim = copy.deepcopy(arg2)
                if arg3 is None:
                    self.eval_ = copy.deepcopy(self.sim)
                else:
                    self.eval_ = copy.deepcopy(arg3)
            elif (
                isinstance(arg1, (Date, datetime_.datetime, str))
                and isinstance(arg2, (Date, datetime_.datetime, str))
                and isinstance(arg3, (Period, datetime_.timedelta, str))
            ):
                self.init = Timegrid(arg1, arg2, arg3)
                self.sim = Timegrid(arg1, arg2, arg3)
                self.eval_ = Timegrid(arg1, arg2, arg3)
            else:
                types_ = objecttools.enumeration(
                    "None" if arg is None else type(arg).__name__ for arg in arguments
                )
                raise ValueError(
                    f"Initialising a `Timegrids` object either requires one, two, or "
                    f"three `Timegrid` objects or two dates objects (of type `Date`, "
                    f"`datetime`, or `str`) and one period object (of type `Period`, "
                    f"`timedelta`, or `str`), but objects of the types `{types_}` are "
                    f"given."
                )
            self.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to define a new `Timegrids` object based on the "
                f"arguments `{objecttools.enumeration(values)}`"
            )

    def _get_stepsize(self) -> Period:
        """Stepsize of all handled |Timegrid| objects.

        You can change the (the identical) |Timegrid.stepsize| of all handled
        |Timegrid| objects at once:

        >>> from hydpy import Timegrids
        >>> timegrids = Timegrids("2000-01-01", "2001-01-01", "1d")
        >>> timegrids.sim.lastdate = "2000-02-01"
        >>> timegrids.eval_.lastdate = "2000-03-01"
        >>> timegrids
        Timegrids(init=Timegrid("2000-01-01 00:00:00",
                                "2001-01-01 00:00:00",
                                "1d"),
                  sim=Timegrid("2000-01-01 00:00:00",
                               "2000-02-01 00:00:00",
                               "1d"),
                  eval_=Timegrid("2000-01-01 00:00:00",
                                 "2000-03-01 00:00:00",
                                 "1d"))

        >>> timegrids.stepsize
        Period("1d")
        >>> timegrids.stepsize = "1h"
        >>> timegrids
        Timegrids(init=Timegrid("2000-01-01 00:00:00",
                                "2001-01-01 00:00:00",
                                "1h"),
                  sim=Timegrid("2000-01-01 00:00:00",
                               "2000-02-01 00:00:00",
                               "1h"),
                  eval_=Timegrid("2000-01-01 00:00:00",
                                 "2000-03-01 00:00:00",
                                 "1h"))
        """
        return self.init.stepsize

    def _set_stepsize(self, stepsize: PeriodConstrArg) -> None:
        self.init.stepsize = Period(stepsize)
        self.sim.stepsize = Period(stepsize)
        self.eval_.stepsize = Period(stepsize)

    stepsize = propertytools.Property[PeriodConstrArg, Period](
        fget=_get_stepsize, fset=_set_stepsize
    )

    def verify(self) -> None:
        """Raise a |ValueError| if the different |Timegrid| objects are inconsistent.

        Method |Timegrids.verify| is called at the end of the initialisation of a new
        |Timegrids| object automatically:

        >>> from hydpy import Timegrid, Timegrids
        >>> Timegrids(init=Timegrid("2001-01-01", "2002-01-01", "1d"),
        ...           sim=Timegrid("2000-01-01", "2002-01-01", "1d"))
        Traceback (most recent call last):
        ...
        ValueError: While trying to define a new `Timegrids` object based on the \
arguments `Timegrid("2001-01-01 00:00:00", "2002-01-01 00:00:00", "1d") and \
Timegrid("2000-01-01 00:00:00", "2002-01-01 00:00:00", "1d")`, the following error \
occurred: The first date of the initialisation period (`2001-01-01 00:00:00`) must \
not be later than the first date of the simulation period (`2000-01-01 00:00:00`).

        However, the same does not hold when one changes a single time grid later:

        >>> timegrids = Timegrids(
        ...     init=Timegrid("2001-01-01", "2002-01-01", "1d"),
        ...     eval_=Timegrid("2001-01-01", "2002-01-01", "1d"))
        >>> timegrids.eval_.lastdate = "2003-01-01"

        When in doubt, call method |Timegrids.verify| manually:

        >>> timegrids.verify()
        Traceback (most recent call last):
        ...
        ValueError: The last date of the initialisation period (`2002-01-01 00:00:00`) \
must not be earlier than the last date of the evaluation period (`2003-01-01 00:00:00`).

        Besides both tests explained by the above error messages, method
        |Timegrids.verify| checks for an equal step size of all |Timegrid| objects and
        their proper alignment:

        >>> timegrids.sim.lastdate = "2002-01-01"
        >>> timegrids.sim.stepsize = "5d"
        >>> timegrids.verify()
        Traceback (most recent call last):
        ...
        ValueError: The initialisation stepsize (`1d`) must be identical with the \
simulation stepsize (`5d`).

        >>> timegrids.sim = Timegrid(
        ...     "2001-01-01 12:00", "2001-12-31 12:00", "1d")
        >>> timegrids.verify()
        Traceback (most recent call last):
        ...
        ValueError: The simulation time grid `Timegrid("2001-01-01 12:00:00", \
"2001-12-31 12:00:00", "1d")` is not properly alligned on the initialisation time \
grid `Timegrid("2001-01-01 00:00:00", "2002-01-01 00:00:00", "1d")`.

        Additionally, the method |Timegrids.verify| calls the verification methods of
        all |Timegrid| objects:

        >>> timegrids.sim.stepsize = "3d"
        >>> timegrids.verify()
        Traceback (most recent call last):
        ...
        ValueError: While trying to verify the simulation time grid \
`Timegrid("2001-01-01 12:00:00", "2001-12-31 12:00:00", "3d")`, the following error \
occurred: The interval between the first date (`2001-01-01 12:00:00`) and the last \
date (`2001-12-31 12:00:00`) is `364d`, which is not an integral multiple of the step \
size `3d`.

        >>> timegrids.sim = timegrids.init
        >>> timegrids.eval_.stepsize = "3d"
        >>> timegrids.verify()
        Traceback (most recent call last):
        ...
        ValueError: While trying to verify the evaluation time grid \
`Timegrid("2001-01-01 00:00:00", "2003-01-01 00:00:00", "3d")`, the following error \
occurred: The interval between the first date (`2001-01-01 00:00:00`) and the last \
date (`2003-01-01 00:00:00`) is `730d`, which is not an integral multiple of the step \
size `3d`.

        >>> timegrids.init.stepsize = "3d"
        >>> timegrids.verify()
        Traceback (most recent call last):
        ...
        ValueError: While trying to verify the initialisation time grid \
`Timegrid("2001-01-01 00:00:00", "2002-01-01 00:00:00", "3d")`, the following error \
occurred: The interval between the first date (`2001-01-01 00:00:00`) and the last \
date (`2002-01-01 00:00:00`) is `365d`, which is not an integral multiple of the step \
size `3d`.
        """
        try:
            self.init.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to verify the initialisation time grid `{self.init}`"
            )
        try:
            self.sim.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to verify the simulation time grid `{self.sim}`"
            )
        try:
            self.eval_.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to verify the evaluation time grid `{self.eval_}`"
            )
        for tg, descr in ((self.sim, "simulation"), (self.eval_, "evaluation")):
            if self.init.firstdate > tg.firstdate:
                raise ValueError(
                    f"The first date of the initialisation period "
                    f"(`{self.init.firstdate}`) must not be later than the first date "
                    f"of the {descr} period (`{tg.firstdate}`)."
                )
            if self.init.lastdate < tg.lastdate:
                raise ValueError(
                    f"The last date of the initialisation period "
                    f"(`{self.init.lastdate}`) must not be earlier than the last date "
                    f"of the {descr} period (`{tg.lastdate}`)."
                )
            if self.init.stepsize != tg.stepsize:
                raise ValueError(
                    f"The initialisation stepsize (`{self.init.stepsize}`) must be "
                    f"identical with the {descr} stepsize (`{tg.stepsize}`)."
                )
            try:
                self.init[tg.firstdate]
            except ValueError as exc:
                raise ValueError(
                    f"The {descr} time grid `{tg}` is not properly alligned on the "
                    f"initialisation time grid `{self.init}`."
                ) from exc

    @property
    def initindices(self) -> tuple[int, int]:
        """A tuple containing the start and end index of the initialisation period.

        >>> from hydpy import Timegrids
        >>> timegrids = Timegrids("2000-01-01", "2001-01-01", "1d")
        >>> timegrids.initindices
        (0, 366)
        """
        return 0, len(self.init)

    @property
    def simindices(self) -> tuple[int, int]:
        """A tuple containing the start and end index of the simulation period
        regarding the initialisation period.

        >>> from hydpy import Timegrids
        >>> timegrids = Timegrids("2000-01-01", "2001-01-01", "1d")
        >>> timegrids.simindices
        (0, 366)
        >>> timegrids.sim.firstdate = "2000-01-11"
        >>> timegrids.sim.lastdate = "2000-02-01"
        >>> timegrids.simindices
        (10, 31)
        """
        return self.init[self.sim.firstdate], self.init[self.sim.lastdate]

    @property
    def evalindices(self) -> tuple[int, int]:
        """A tuple containing the start and end index of the evaluation period
        regarding the initialisation period.

        >>> from hydpy import Timegrids
        >>> timegrids = Timegrids("2000-01-01", "2001-01-01", "1d")
        >>> timegrids.simindices
        (0, 366)
        >>> timegrids.eval_.firstdate = "2000-01-11"
        >>> timegrids.eval_.lastdate = "2000-02-01"
        >>> timegrids.evalindices
        (10, 31)
        """
        return self.init[self.eval_.firstdate], self.init[self.eval_.lastdate]

    def qfactor(self, area: float) -> float:
        """Return the factor for converting `mm/stepsize` to `m³/s` for a reference
        area, given in `km²`.

        >>> from hydpy import Timegrids, round_
        >>> timegrids = Timegrids("2000-01-01", "2001-01-01", "1s")
        >>> timegrids.qfactor(1.0)
        1000.0
        >>> timegrids.stepsize = "2d"
        >>> round_(timegrids.qfactor(2.0))
        0.011574
        """
        return area * 1000.0 / self.stepsize.seconds

    def parfactor(self, stepsize: PeriodConstrArg) -> float:
        """Return the factor for adjusting time-dependent parameter values to the
        actual simulation step size (the given `stepsize` must be related to the
        original parameter values).

        >>> from hydpy import Timegrids
        >>> timegrids = Timegrids("2000-01-01", "2001-01-01", "1d")
        >>> timegrids.parfactor("1d")
        1.0
        >>> timegrids.parfactor("1h")
        24.0
        """
        return self.stepsize / Period(stepsize)

    def __iter__(self) -> Iterator[Timegrid]:
        yield self.init
        yield self.sim
        yield self.eval_

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Timegrids):
            return (
                (self.init == other.init)
                and (self.sim == other.sim)
                and (self.eval_ == other.eval_)
            )
        return False

    def __repr__(self) -> str:
        return self.assignrepr("")

    def assignrepr(self, prefix: str) -> str:
        """Return a |repr| string with a prefixed assignment."""
        caller = "Timegrids("
        if self.init == self.sim == self.eval_:
            repr_tg = (
                self.init.assignrepr(prefix)
                .replace("Timegrid(", caller)
                .replace("\n", "\n ")
            )
            return f"{prefix}{repr_tg}"
        blanks = " " * (len(prefix) + len(caller))
        return (
            f"{self.init.assignrepr(f'{prefix}{caller}init=')},\n"
            f"{self.sim.assignrepr(f'{blanks}sim=')},\n"
            f"{self.eval_.assignrepr(f'{blanks}eval_=')})"
        )

    def __str__(self) -> str:
        return objecttools.flatten_repr(self)


class TOY:
    """Time of year handler.

    |TOY| objects are used to define certain things that are true for a specific time
    point in each year.  The smallest supported time unit is seconds.

    For initialisation, one usually passes a string defining the month, the day, the
    hour, the minute and the second in the mentioned order and separated by single
    underscores:

    >>> from hydpy.core.timetools import Date, TOY
    >>> t = TOY("3_13_23_33_43")
    >>> t.month
    3
    >>> t.day
    13
    >>> t.hour
    23
    >>> t.minute
    33
    >>> t.second
    43

    If a lower precision is required, one can shorten the string, which implicitly sets
    the omitted property to the lowest possible value:

    >>> TOY("3_13_23_33")
    TOY("3_13_23_33_0")

    The most extreme example is to pass no string at all:

    >>> TOY()
    TOY("1_1_0_0_0")

    One can prefix some information to the string, which is useful when the string is
    to be used as a valid variable name somewhere else:

    >>> TOY("something_3_13_23_33_2")
    TOY("3_13_23_33_2")

    As one can see, we lose the prefixed information in the printed string
    representation.  Instead, applying "str" returns a string with a standard prefix:

    >>> str(TOY('something_3_13_23_33_2'))
    'toy_3_13_23_33_2'

    Alternatively, one can use a |Date| object as an initialisation argument, omitting
    the year:

    >>> TOY(Date("2001.02.03 04:05:06"))
    TOY("2_3_4_5_6")

    Ill-defined constructor arguments result in error messages like the following:

    >>> TOY("something")
    Traceback (most recent call last):
    ...
    ValueError: While trying to initialise a TOY object based on argument value \
`something` of type `str`, the following error occurred: When passing a prefixed \
string, you need to define at least the month.


    >>> TOY("2_30_4_5_6")
    Traceback (most recent call last):
    ...
    ValueError: While trying to initialise a TOY object based on argument value \
`2_30_4_5_6` of type `str`, the following error occurred: While trying to retrieve \
the day, the following error occurred: The value of property `day` of the actual TOY \
(time of year) object must lie within the range `(1, 29)`, as the month has already \
been set to `2`, but the given value is `30`.

    It is only allowed to modify the mentioned properties, not to define new ones:

    >>> t.microsecond = 53
    Traceback (most recent call last):
    ...
    AttributeError: TOY (time of year) objects only allow to set the properties \
month, day, hour, minute, and second, but `microsecond` is given.

    You can pass any objects that are convertible to integers:

    >>> t.second = "53"
    >>> t.second
    53

    Unconvertible objects cause the following error:

    >>> t.second = "fiftythree"
    Traceback (most recent call last):
    ...
    ValueError: For TOY (time of year) objects, all properties must be of type `int`, \
but the value `fiftythree` of type `str` given for property `second` cannot be \
converted to `int`.

    Additionally, given values are checked to lie within a suitable range:

    >>> t.second = 60
    Traceback (most recent call last):
    ...
    ValueError: The value of property `second` of TOY (time of year) objects must lie \
within the range `(0, 59)`, but the given value is `60`.

    Note that the allowed values for `month` and `day` depend on each other, which is
    why the order one defines them might be of importance.  So, if January is
    predefined, one can set the day to the 31st:

    >>> t.month = 1
    >>> t.day = 31

    Afterwards, one cannot directly change the month to April:

    >>> t.month = 4
    Traceback (most recent call last):
    ...
    ValueError: The value of property `month` of the actual TOY (time of year) object \
must not be the given value `4`, as the day has already been set to `31`.

    First, set `day` to a smaller value and change `month` afterwards:

    >>> t.day = 30
    >>> t.month = 4

    It is possible to compare two |TOY| instances:

    >>> t1, t2 = TOY("1"), TOY("2")
    >>> t1 < t1, t1 < t2, t2 < t1
    (False, True, False)
    >>> t1 <= t1, t1 <= t2, t2 <= t1
    (True, True, False)
    >>> t1 == t1, t1 == t2, t1 == 1
    (True, False, False)
    >>> t1 != t1, t1 != t2, t1 != 1
    (False, True, True)
    >>> t1 >= t1, t1 >= t2, t2 >= t1
    (True, False, True)
    >>> t1 > t1, t1 > t2, t2 > t1
    (False, False, True)

    Subtracting two |TOY| objects gives their time difference in seconds:

    >>> TOY("1_1_0_3_0") - TOY("1_1_0_1_30")
    90

    Subtraction never results in negative values due to assuming the left operand is
    the posterior (eventually within the subsequent year):

    >>> TOY("1_1_0_1_30") - TOY("12_31_23_58_30")
    180
    """

    _PROPERTIES = collections.OrderedDict(
        (
            ("month", (1, 12)),
            ("day", (1, 31)),
            ("hour", (0, 23)),
            ("minute", (0, 59)),
            ("second", (0, 59)),
        )
    )
    _STARTDATE = Date.from_datetime(datetime_.datetime(2000, 1, 1))
    _ENDDATE = Date.from_datetime(datetime_.datetime(2001, 1, 1))

    month: int
    """The month of the current the actual time of the year."""
    day: int
    """The day of the current the actual time of the year."""
    hour: int
    """The hour of the current the actual time of the year."""
    minute: int
    """The minute of the current the actual time of the year."""
    second: int
    """The second of the current the actual time of the year."""

    def __init__(self, value: str | Date = "") -> None:
        try:
            if isinstance(value, Date):
                datetime = value.datetime
                dict_ = vars(self)
                for name in self._PROPERTIES.keys():
                    dict_[name] = getattr(datetime, name)
            else:
                values = value.split("_")
                if not values[0].isdigit():
                    if values[0] and (len(values) == 1):
                        raise ValueError(
                            "When passing a prefixed string, you need to define at "
                            "least the month."
                        )
                    del values[0]
                for prop in self._PROPERTIES:
                    try:
                        setattr(self, prop, values.pop(0))
                    except IndexError:
                        if prop in ("month", "day"):
                            setattr(self, prop, 1)
                        else:
                            setattr(self, prop, 0)
                    except ValueError:
                        objecttools.augment_excmessage(
                            f"While trying to retrieve the {prop}"
                        )
            vars(self)["seconds_passed"] = None
            vars(self)["seconds_left"] = None
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise a TOY object based on argument "
                f"{objecttools.value_of_type(value)}"
            )

    def __setattr__(self, name: str, value: int) -> None:
        if name not in self._PROPERTIES:
            raise AttributeError(
                f"TOY (time of year) objects only allow to set the properties "
                f"{objecttools.enumeration(self._PROPERTIES.keys())}, but `{name}` is "
                f"given."
            )
        try:
            value = int(value)
        except ValueError:
            raise ValueError(
                f"For TOY (time of year) objects, all properties must be of type "
                f"`int`, but the {objecttools.value_of_type(value)} given for "
                f"property `{name}` cannot be converted to `int`."
            ) from None
        if (name == "day") and hasattr(self, "month"):
            bounds = (1, calendar.monthrange(2000, self.month)[1])
            if not bounds[0] <= value <= bounds[1]:
                raise ValueError(
                    f"The value of property `day` of the actual TOY (time of year) "
                    f"object must lie within the range `{bounds}`, as the month has "
                    f"already been set to `{self.month}`, but the given value is "
                    f"`{value}`."
                )
        elif (name == "month") and hasattr(self, "day"):
            bounds = (1, calendar.monthrange(2000, value)[1])
            if not bounds[0] <= self.day <= bounds[1]:
                raise ValueError(
                    f"The value of property `month` of the actual TOY (time of year) "
                    f"object must not be the given value `{value}`, as the day has "
                    f"already been set to `{self.day}`."
                )
        else:
            bounds = self._PROPERTIES[name]
            if not bounds[0] <= value <= bounds[1]:
                raise ValueError(
                    f"The value of property `{name}` of TOY (time of year) objects "
                    f"must lie within the range `{bounds}`, but the given value is "
                    f"`{value}`."
                )
        super().__setattr__(name, value)
        vars(self)["seconds_passed"] = None
        vars(self)["seconds_left"] = None

    @property
    def seconds_passed(self) -> int:
        """The amount of time passed in seconds since the beginning of the year.

        In the first example, the year is only one minute and thirty seconds old:

        >>> from hydpy.core.timetools import TOY
        >>> toy = TOY("1_1_0_1_30")
        >>> toy.seconds_passed
        90

        Updating the |TOY| object triggers a recalculation of property
        |TOY.seconds_passed|:

        >>> toy.day = 2
        >>> toy.seconds_passed
        86490

        The second example shows the general inclusion of the 29th of February:

        >>> TOY("3").seconds_passed
        5184000
        """
        seconds_passed = cast(int | None, vars(self)["seconds_passed"])
        if seconds_passed is None:
            seconds_passed = int(
                (self._datetime - self._STARTDATE.datetime).total_seconds()
            )
            vars(self)["seconds_passed"] = seconds_passed
        return seconds_passed

    @property
    def seconds_left(self) -> int:
        """The remaining amount of time part of the year (in seconds).

        In the first example, only one minute and thirty seconds of the year remain:

        >>> from hydpy.core.timetools import TOY
        >>> toy = TOY("12_31_23_58_30")
        >>> toy.seconds_left
        90

        Updating the |TOY| object triggers a recalculation of property
        |TOY.seconds_passed|:

        >>> toy.day = 30
        >>> toy.seconds_left
        86490

        The second example shows the general inclusion of the 29th of February:

        >>> TOY("2").seconds_left
        28944000
        """
        seconds_left = cast(int | None, vars(self)["seconds_left"])
        if seconds_left is None:
            seconds_left = int(
                (self._ENDDATE.datetime - self._datetime).total_seconds()
            )
            vars(self)["seconds_left"] = seconds_left
        return seconds_left

    @property
    def _datetime(self) -> datetime_.datetime:
        return datetime_.datetime(
            2000, self.month, self.day, self.hour, self.minute, self.second
        )

    @classmethod
    def centred_timegrid(cls) -> tuple[Timegrid, NDArrayBool]:
        """Return a |Timegrid| object defining the central time points of the year
        2000 and a boolean array describing its intersection with the current
        initialisation period, not taking the year information into account.

        The returned |Timegrid| object does not depend on the defined initialisation
        period:

        >>> from hydpy.core.timetools import TOY
        >>> from hydpy import pub
        >>> pub.timegrids = "2001-10-01", "2010-10-01", "1d"
        >>> TOY.centred_timegrid()[0]
        Timegrid("2000-01-01 12:00:00",
                 "2001-01-01 12:00:00",
                 "1d")

        The same holds for the shape of the returned boolean array:

        >>> len(TOY.centred_timegrid()[1])
        366

        However, the single boolean values depend on whether the respective centred
        date lies at least one time within the initialisation period when ignoring the
        year information.  In our example, all centred dates are "relevant" due to the
        long initialisation period of ten years:

        >>> from hydpy import print_vector, round_
        >>> round_(sum(TOY.centred_timegrid()[1]))
        366

        The boolean array contains only the value |True| for all initialisation periods
        covering at least a full year:

        >>> pub.timegrids = "2000-02-01", "2001-02-01", "1d"
        >>> round_(sum(TOY.centred_timegrid()[1]))
        366
        >>> pub.timegrids = "2001-10-01", "2002-10-01", "1d"
        >>> round_(sum(TOY.centred_timegrid()[1]))
        366

        In all other cases, only the values related to the intersection are |True|:

        >>> pub.timegrids = "2001-01-03", "2001-01-05", "1d"
        >>> print_vector(TOY.centred_timegrid()[1][:5])
        False, False, True, True, False

        >>> pub.timegrids = "2001-12-30", "2002-01-04", "1d"
        >>> print_vector(TOY.centred_timegrid()[1][:5])
        True, True, True, False, False
        >>> print_vector(TOY.centred_timegrid()[1][-5:])
        False, False, False, True, True

        It makes no difference whether initialisation periods not spanning an entire
        year contain the 29th of February:

        >>> pub.timegrids = "2001-02-27", "2001-03-01", "1d"
        >>> print_vector(TOY.centred_timegrid()[1][31+28-3-1:31+28+3-1])
        False, False, True, True, True, False
        >>> pub.timegrids = "2000-02-27", "2000-03-01", "1d"
        >>> print_vector(TOY.centred_timegrid()[1][31+28-3-1:31+28+3-1])
        False, False, True, True, True, False
        """
        init = hydpy.pub.timegrids.init
        shift = init.stepsize / 2.0
        centred = Timegrid(cls._STARTDATE + shift, cls._ENDDATE + shift, init.stepsize)
        if (init.lastdate - init.firstdate) >= "365d":
            return centred, numpy.ones(len(centred), dtype=config.NP_BOOL)
        date0 = copy.deepcopy(init.firstdate)
        date1 = copy.deepcopy(init.lastdate)
        date0.year = 2000
        date1.year = 2000
        relevant = numpy.zeros(len(centred), dtype=config.NP_BOOL)
        if date0 < date1:
            relevant[centred[date0 + shift] : centred[date1 + shift]] = True
        else:
            relevant[centred[date0 + shift] :] = True
            relevant[: centred[date1 + shift]] = True
        return centred, relevant

    def __sub__(self, other: TOY) -> float:
        if self >= other:
            return self.seconds_passed - other.seconds_passed
        return self.seconds_passed + other.seconds_left

    def __lt__(self, other: TOY) -> bool:
        return self.seconds_passed < other.seconds_passed

    def __le__(self, other: TOY) -> bool:
        return self.seconds_passed <= other.seconds_passed

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TOY):
            return self.seconds_passed == other.seconds_passed
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, TOY):
            return self.seconds_passed != other.seconds_passed
        return True

    def __gt__(self, other: TOY) -> bool:
        return self.seconds_passed > other.seconds_passed

    def __ge__(self, other: TOY) -> bool:
        return self.seconds_passed >= other.seconds_passed

    def __str__(self) -> str:
        string = "_".join(str(getattr(self, prop)) for prop in self._PROPERTIES.keys())
        return f"toy_{string}"

    def __repr__(self) -> str:
        content = "_".join(str(getattr(self, prop)) for prop in self._PROPERTIES.keys())
        return f'TOY("{content}")'


TOY0 = TOY("1_1_0_0_0")
"""The very first time of the year."""
