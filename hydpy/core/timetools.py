# -*- coding: utf-8 -*-
"""This module specifies how  dates and periods are handled in HydPy.

.. _`Time Coordinate`: http://cfconventions.org/Data/cf-conventions/\
cf-conventions-1.7/cf-conventions.html#time-coordinate
"""
# import...
# ...from standard library
import calendar
import collections
import copy
import datetime
import numbers
import time
from typing import *
# ...from third party packages
import numpy
# ...from HydPy
import hydpy
from hydpy.core.abctools import *
from hydpy.core import objecttools


# The import of `_strptime` is not thread save.  The following call of
# `strptime` is supposed to prevent possible problems arising from this bug.
time.strptime('1999', '%Y')


class Date(DateABC):
    """Handles a single date.

    Classes |Date| is build on top of the Python module |datetime|.
    In essence, it wraps the |datetime| class |datetime.datetime|,
    and is supposed to specialise this general class on the needs
    of HydPy users.

    Be aware of the different minimum time resolution of module |datetime|
    (microseconds) and module |timetools| (seconds).

    |Date| objects can be initialized via |datetime.datetime| objects
    directly:

    >>> import datetime
    >>> date = datetime.datetime(1996, 11, 1, 0, 0, 0)
    >>> from hydpy import Date
    >>> Date(date)
    Date('1996-11-01 00:00:00')

    |Date| objects do not store time zone information.  The |Date| object
    prepared above refers to zero o'clock in the time zone defined by
    |Options.utcoffset| (UTC+01:00 by default).  When the initialization
    argument provides its own time zone information, its date information
    is adjusted.  This is shown in the following example, where the
    prepared |datetime.datetime| object refers to UTC-01:00 (Python 2.7
    does not implement a concrete |datetime.timezone| class, which is
    why define a lazy one first):

    >>> class UTC_1(datetime.tzinfo):
    ...     def utcoffset(self, dt):
    ...         return datetime.timedelta(hours=-1)
    >>> date = datetime.datetime(1996, 11, 1, 0, 0, 0, tzinfo=UTC_1())
    >>> Date(date)
    Date('1996-11-01 02:00:00')

    One can change |Options.utcoffset|, but this does not change the
    |Date| objects already existing:

    >>> from hydpy import pub
    >>> pub.options.utcoffset = 0
    >>> temp = Date(date)
    >>> temp
    Date('1996-11-01 01:00:00')
    >>> pub.options.utcoffset = 60
    >>> temp
    Date('1996-11-01 01:00:00')

    Usually, one uss |str| objects as initialization arguments, which
    need to match one of the following format styles.  The `os` style is
    applied in text files and folder names, and does not include any
    empty spaces or colons:

    >>> Date('1997_11_01_00_00_00').style
    'os'

    The `iso` styles are more legible and and comes in two flavours.
    `iso1` is in accordance with ISO 8601, and `iso2` (which is the
    default style) omits the `T` between date and time:

    >>> Date('1997-11-01T00:00:00').style
    'iso1'
    >>> Date('1997-11-01 00:00:00').style
    'iso2'

    The `din` styles rely on points instead of hyphens.  The difference
    between the available flavours lies in the order of the date literals
    (DIN refers to a german norm):

    >>> Date('01.11.1997 00:00:00').style
    'din1'
    >>> Date('1997.11.01 00:00:00').style
    'din2'

    It is allowed to abbreviate the input strings:

    >>> for string in ('1996-11-01 00:00:00',
    ...                '1996-11-01 00:00',
    ...                '1996-11-01 00',
    ...                '1996-11-01'):
    ...     print(Date(string))
    1996-11-01 00:00:00
    1996-11-01 00:00:00
    1996-11-01 00:00:00
    1996-11-01 00:00:00

    All styles described above can be combined with ISO time zone
    identifiers.  Some examples:

    >>> Date('1997-11-01T00:00:00Z')
    Date('1997-11-01T01:00:00')
    >>> Date('1997-11-01 00:00:00-11:00')
    Date('1997-11-01 12:00:00')
    >>> Date('1997-11-01 +1300')
    Date('1997-10-31 12:00:00')
    >>> Date('01.11.1997 00-500')
    Date('01.11.1997 06:00:00')

    Poorly formatted date strings result in the following or comparable
    error messages:

    >>> Date('1997/11/01')
    Traceback (most recent call last):
    ...
    ValueError: Date could not be identified out of the given string \
1997/11/01.  The available formats are OrderedDict([\
('os', '%Y_%m_%d_%H_%M_%S'), ('iso2', '%Y-%m-%d %H:%M:%S'), \
('iso1', '%Y-%m-%dT%H:%M:%S'), ('din1', '%d.%m.%Y %H:%M:%S'), \
('din2', '%Y.%m.%d %H:%M:%S')]).

    >>> Date('1997-11-01 +0000001')
    Traceback (most recent call last):
    ...
    ValueError: While trying to apply the time zone offset from string \
`1997-11-01 +0000001`, the following error occurred: wrong number of \
offset characters

    >>> Date('1997-11-01 +0X:00')
    Traceback (most recent call last):
    ...
    ValueError: While trying to apply the time zone offset from string \
`1997-11-01 +0X:00`, the following error occurred: invalid \
literal for int() with base 10: '0X'
    """

    # These are the so far accepted date format strings.
    _formatstrings = collections.OrderedDict([
        ('os', '%Y_%m_%d_%H_%M_%S'),
        ('iso2', '%Y-%m-%d %H:%M:%S'),
        ('iso1', '%Y-%m-%dT%H:%M:%S'),
        ('din1', '%d.%m.%Y %H:%M:%S'),
        ('din2', '%Y.%m.%d %H:%M:%S')])
    # The first month of the hydrological year (e.g. November in Germany)
    _firstmonth_wateryear = 11

    def __init__(self, date):
        self.datetime = None
        self._style = None
        datetime_ = getattr(date, 'datetime', None)
        if datetime_ is not None:
            self.datetime = datetime_
            self.style = getattr(date, 'style', None)
            return
        microsecond = getattr(date, 'microsecond', None)
        if microsecond is not None:
            if microsecond != 0:
                raise ValueError(
                    f'For `Date` instances, the microsecond must be `0`.  '
                    f'For the given `datetime` object, it is '
                    f'`{microsecond:d}` instead.')
            date = date.isoformat().replace('T', ' ')
        try:
            self.datetime = datetime.datetime(
                2000, date.month, date.day,
                date.hour, date.minute, date.second)
            return
        except AttributeError:
            pass
        try:
            self._init_from_string(date)
            return
        except BaseException as exc:
            if isinstance(date, str):
                raise exc
            raise TypeError(
                f'The supplied argument must be either an instance of '
                f'`Date`, `datetime.datetime`, `TOY` or `str`.  The given '
                f'arguments type is {objecttools.classname(date)}.')

    def _init_from_string(self, string):
        substring, offset = self._extract_offset(string)
        style, date = self._extract_date(substring, string)
        self.datetime = self._modify_date(date, offset, string)
        self._style = style
        return

    @staticmethod
    def _extract_offset(string):
        if 'Z' in string:
            return string.split('Z')[0].strip(), '+0000'
        if '+' in string:
            idx = string.find('+')
        elif string.count('-') in (1, 3):
            idx = string.rfind('-')
        else:
            return string, None
        return string[:idx].strip(), string[idx:].strip()

    @classmethod
    def _extract_date(cls, substring, string):
        for (style, format_) in cls._formatstrings.items():
            for dummy in range(4):
                try:
                    date = datetime.datetime.strptime(substring, format_)
                    return style, date
                except ValueError:
                    format_ = format_[:-3]
        raise ValueError(
            f'Date could not be identified out of the given string '
            f'{string}.  The available formats are {cls._formatstrings}.')

    @staticmethod
    def _modify_date(date, offset, string):
        try:
            if offset is None:
                return date
            else:
                factor = 1 if (offset[0] == '+') else -1
                offset = offset[1:].strip().replace(':', '')
                if len(offset) <= 2:
                    minutes = int(offset)*60
                elif len(offset) <= 4:
                    minutes = int(offset[:-2])*60 + int(offset[-2:])
                else:
                    raise ValueError(
                        'wrong number of offset characters')
                delta = datetime.timedelta(
                    minutes=factor*minutes-hydpy.pub.options.utcoffset)
                return date - delta
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to apply the time zone offset '
                f'from string `{string}`')

    @classmethod
    def from_array(cls, array):
        """Return a |Date| instance based on date information (year,
        month, day, hour, minute, second) stored as the first entries of
        the successive rows of a |numpy.ndarray|.

        >>> from hydpy import Date
        >>> import numpy
        >>> array1d = numpy.array([1992, 10, 8, 15, 15, 42, 999])
        >>> Date.from_array(array1d)
        Date('1992-10-08 15:15:42')

        >>> array3d = numpy.zeros((7, 2, 2))
        >>> array3d[:, 0, 0] = array1d
        >>> Date.from_array(array3d)
        Date('1992-10-08 15:15:42')

        .. note::

           The date defined by the given |numpy.ndarray| cannot
           include any time zone information and corresponds to
           |Options.utcoffset|, which defaults to UTC+01:00.
        """
        intarray = numpy.array(array, dtype=int)
        for dummy in range(1, array.ndim):
            intarray = intarray[:, 0]
        return cls(datetime.datetime(*intarray[:6]))

    def to_array(self):
        """Return a 1-dimensional |numpy| |numpy.ndarray|  with six entries
        defining the actual date (year, month, day, hour, minute, second).

        >>> from hydpy import Date
        >>> Date('1992-10-8 15:15:42').to_array()
        array([ 1992.,    10.,     8.,    15.,    15.,    42.])

        .. note::

           The date defined by the returned |numpy.ndarray| does not
           include any time zone information and corresponds to
           |Options.utcoffset|, which defaults to UTC+01:00.
        """
        return numpy.array([self.year, self.month, self.day, self.hour,
                            self.minute, self.second], dtype=float)

    @classmethod
    def from_cfunits(cls, units) -> 'Date':
        """Return a |Date| object representing the reference date of the
        given `units` string aggreeing with the NetCDF-CF conventions.

        The following example string is taken from the `Time Coordinate`_
        chapter of the NetCDF-CF conventions documentation (modified).
        Note that the first entry (the unit) is ignored:

        >>> from hydpy import Date
        >>> Date.from_cfunits('seconds since 1992-10-8 15:15:42 -6:00')
        Date('1992-10-08 22:15:42')
        >>> Date.from_cfunits(' day since 1992-10-8 15:15:00')
        Date('1992-10-08 15:15:00')
        >>> Date.from_cfunits('seconds since 1992-10-8 -6:00')
        Date('1992-10-08 07:00:00')
        >>> Date.from_cfunits('m since 1992-10-8')
        Date('1992-10-08 00:00:00')

        Without modification, when "0" is included as the decimal fractions
        of a second, the example string from `Time Coordinate`_ can also
        be passed.  However, fractions different from "0" result in
        an error:

        >>> Date.from_cfunits('seconds since 1992-10-8 15:15:42.')
        Date('1992-10-08 15:15:42')
        >>> Date.from_cfunits('seconds since 1992-10-8 15:15:42.00')
        Date('1992-10-08 15:15:42')
        >>> Date.from_cfunits('seconds since 1992-10-8 15:15:42. -6:00')
        Date('1992-10-08 22:15:42')
        >>> Date.from_cfunits('seconds since 1992-10-8 15:15:42.0 -6:00')
        Date('1992-10-08 22:15:42')
        >>> Date.from_cfunits('seconds since 1992-10-8 15:15:42.005 -6:00')
        Traceback (most recent call last):
        ...
        ValueError: While trying to parse the date of the NetCDF-CF "units" \
string `seconds since 1992-10-8 15:15:42.005 -6:00`, the following error \
occurred: No other decimal fraction of a second than "0" allowed.
        """
        try:
            string = units[units.find('since')+6:]
            idx = string.find('.')
            if idx != -1:
                jdx = None
                for jdx, char in enumerate(string[idx+1:]):
                    if not char.isnumeric():
                        break
                    if char != '0':
                        raise ValueError(
                            'No other decimal fraction of a second '
                            'than "0" allowed.')
                else:
                    if jdx is None:
                        jdx = idx+1
                    else:
                        jdx += 1
                string = f'{string[:idx]}{string[idx+jdx+1:]}'
            return cls(string)
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to parse the date of the NetCDF-CF "units" '
                f'string `{units}`')

    def to_cfunits(self, unit='hours', utcoffset=None):
        """Return a `units` string aggreeing with the NetCDF-CF conventions.

        By default, |Date.to_cfunits| takes `hours` as time unit, and the
        the actual value of |Options.utcoffset| as time zone information:

        >>> from hydpy import Date
        >>> date = Date('1992-10-08 15:15:42')
        >>> date.to_cfunits()
        'hours since 1992-10-08 15:15:42 +01:00'

        Other time units are allowed (no checks are performed, so select
        something useful):

        >>> date.to_cfunits(unit='minutes')
        'minutes since 1992-10-08 15:15:42 +01:00'

        For changing the time zone, pass the corresponding offset in minutes:

        >>> date.to_cfunits(unit='sec', utcoffset=-60)
        'sec since 1992-10-08 13:15:42 -01:00'
        """
        if utcoffset is None:
            utcoffset = hydpy.pub.options.utcoffset
        string = self.to_string('iso2', utcoffset)
        string = ' '.join((string[:-6], string[-6:]))
        return f'{unit} since {string}'

    def _get_refmonth(self):
        """First month of the hydrological year. The default value is 11
        (November which is the german reference month). Setting it e.g. to 10
        (October is another common reference month many different countries)
        affects all |Date| instances."""
        return type(self)._firstmonth_wateryear

    def _set_refmonth(self, value):
        try:
            type(self)._firstmonth_wateryear = int(value)
        except ValueError:
            string = str(value)[:3].lower()
            try:
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                          'jul', 'aug', 'sew', 'oct', 'nov', 'dec']
                type(self)._firstmonth_wateryear = months.index(string) + 1
            except ValueError:
                raise ValueError(
                    f'The given value `{value}` cannot be interpreted '
                    f'as a month. Supply e.g. a number between 1 '
                    f'and 12 or a month name instead.')

    refmonth = property(_get_refmonth, _set_refmonth)

    def _get_style(self):
        """Date format style to be applied in printing.

        Initially, |Date.style| corresponds to the format style of the
        string used as the initialization object of a |Date| object:

        >>> from hydpy import Date
        >>> date = Date('01.11.1997 00:00:00')
        >>> date.style
        'din1'
        >>> date
        Date('01.11.1997 00:00:00')

        However, you are allowed to change it:

        >>> date.style = 'iso2'
        >>> date
        Date('1997-11-01 00:00:00')

        Trying to set a non-existing style results in:

        >>> date.style = 'iso'
        Traceback (most recent call last):
        ...
        KeyError: 'Date format style `iso` is not available.'
        """
        if self._style is None:
            return 'iso2'
        return self._style

    def _set_style(self, style):
        if style in self._formatstrings:
            self._style = style
        else:
            self._style = None
            raise KeyError(
                f'Date format style `{style}` is not available.')

    style = property(_get_style, _set_style)

    def _set_thing(self, thing, value):
        """Convenience method for `_set_year`, `_set_month`..."""
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise TypeError(
                f'Changing the {thing} of a `Date` instance is only '
                f'allowed via numbers, but the given value `{value}` '
                f'is of type `{type(value)}` instead.')
        kwargs = {}
        for unit in ('year', 'month', 'day', 'hour', 'minute', 'second'):
            kwargs[unit] = getattr(self, unit)
        kwargs[thing] = value
        self.datetime = datetime.datetime(**kwargs)

    def _get_second(self):
        """The actual second.

        >>> from hydpy import Date
        >>> date = Date('2000-01-01 00:00:00')
        >>> date.second
        0
        >>> date.second = 30
        >>> date.second
        30
        """
        return self.datetime.second

    def _set_second(self, second):
        self._set_thing('second', second)

    second = property(_get_second, _set_second)

    def _get_minute(self):
        """The actual minute.

        >>> from hydpy import Date
        >>> date = Date('2000-01-01 00:00:00')
        >>> date.minute
        0
        >>> date.minute = 30
        >>> date.minute
        30
        """
        return self.datetime.minute

    def _set_minute(self, minute):
        self._set_thing('minute', minute)

    minute = property(_get_minute, _set_minute)

    def _get_hour(self):
        """The actual hour.

        >>> from hydpy import Date
        >>> date = Date('2000-01-01 00:00:00')
        >>> date.hour
        0
        >>> date.hour = 12
        >>> date.hour
        12
        """
        return self.datetime.hour

    def _set_hour(self, hour):
        self._set_thing('hour', hour)

    hour = property(_get_hour, _set_hour)

    def _get_day(self):
        """The actual day.

        >>> from hydpy import Date
        >>> date = Date('2000-01-01 00:00:00')
        >>> date.day
        1
        >>> date.day = 15
        >>> date.day
        15
        """
        return self.datetime.day

    def _set_day(self, day):
        self._set_thing('day', day)

    day = property(_get_day, _set_day)

    def _get_month(self):
        """The actual month.

        >>> from hydpy import Date
        >>> date = Date('2000-01-01 00:00:00')
        >>> date.month
        1
        >>> date.month = 7
        >>> date.month
        7
        """
        return self.datetime.month

    def _set_month(self, month):
        self._set_thing('month', month)

    month = property(_get_month, _set_month)

    def _get_year(self):
        """The actual year.

        >>> from hydpy import Date
        >>> date = Date('2000-01-01 00:00:00')
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

    def _set_year(self, year):
        self._set_thing('year', year)

    year = property(_get_year, _set_year)

    @property
    def wateryear(self):
        """The actual hydrological year according to the selected
        reference month.

        The reference mont reference |Date.refmonth| defaults to November:

        >>> october = Date('1996.10.01')
        >>> november = Date('1996.11.01')
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
        >>> october.refmonth = 'November'
        >>> october.wateryear
        1996
        >>> november.wateryear
        1997
        """
        if self.month < self._firstmonth_wateryear:
            return self.year
        return self.year + 1

    @property
    def dayofyear(self):
        """Day of year as an integer value.

        >>> from hydpy import Date
        >>> Date('2003-03-01').dayofyear
        60
        >>> Date('2004-03-01').dayofyear
        61
        """
        return self.datetime.timetuple().tm_yday

    @property
    def leapyear(self):
        """Return whether the actual date falls in a leap year or not.

        >>> from hydpy import Date
        >>> Date('2003-03-01').leapyear
        False
        >>> Date('2004-03-01').leapyear
        True
        >>> Date('2000-03-01').leapyear
        True
        >>> Date('2100-03-01').leapyear
        False
        """
        year = self.year
        return (((year % 4) == 0) and
                (((year % 100) != 0) or ((year % 400) == 0)))

    def __add__(self, other):
        new = Date(self.datetime + Period(other).timedelta)
        new.style = self.style
        return new

    def __iadd__(self, other):
        self.datetime += Period(other).timedelta
        return self

    def __sub__(self, other):
        try:
            return Period(self.datetime-Date(other).datetime)
        except (TypeError, ValueError):
            try:
                new = Date(self.datetime-Period(other).timedelta)
                new.style = self.style
                return new
            except (TypeError, ValueError):
                raise Exception(
                    f'Object `{str(other)}` of type `{type(other)}` '
                    f'cannot be substracted from a `Date` instance.')

    def __isub__(self, other):
        self.datetime -= Period(other).timedelta
        return self

    def __lt__(self, other):
        return self.datetime < Date(other).datetime

    def __le__(self, other):
        return self.datetime <= Date(other).datetime

    def __eq__(self, other):
        return self.datetime == Date(other).datetime

    def __ne__(self, other):
        return self.datetime != Date(other).datetime

    def __gt__(self, other):
        return self.datetime > Date(other).datetime

    def __ge__(self, other):
        return self.datetime >= Date(other).datetime

    def to_string(self, style=None, utcoffset=None):
        """Return a |str| object representing the actual date in
        accordance with the given style and the eventually given
        UTC offset (in minutes).

        Without any input arguments, the actual |Date.style| is used
        to return a date string in your local time zone:

        >>> from hydpy import Date
        >>> date = Date('01.11.1997 00:00:00')
        >>> date.to_string()
        '01.11.1997 00:00:00'

        Passing a style string affects the returned |str| object, but
        not the |Date.style| property:

        >>> date.style
        'din1'
        >>> date.to_string(style='iso2')
        '1997-11-01 00:00:00'
        >>> date.style
        'din1'

        When passing the `utcoffset` in minutes, the offset string is
        appended:

        >>> date.to_string(style='iso2', utcoffset=60)
        '1997-11-01 00:00:00+01:00'

        If the given offset does not correspond to your local offset
        defined by |Options.utcoffset| (which defaults to UTC+01:00),
        the date string is adapted:

        >>> date.to_string(style='iso1', utcoffset=0)
        '1997-10-31T23:00:00+00:00'
        """
        if not style:
            style = self.style
        if utcoffset is None:
            string = ''
            date = self.datetime
        else:
            sign = '+' if utcoffset >= 0 else '-'
            hours = abs(utcoffset // 60)
            minutes = abs(utcoffset % 60)
            string = f'{sign}{hours:02d}:{minutes:02d}'
            offset = utcoffset-hydpy.pub.options.utcoffset
            date = self.datetime + datetime.timedelta(minutes=offset)
        return date.strftime(self._formatstrings[style]) + string

    def to_repr(self, style=None, utcoffset=None):
        """Similar as method |Date.to_string|, but returns a proper
        string representation instead.

        See method |Date.to_string| for explanations on the following
        examples:

        >>> from hydpy import Date
        >>> date = Date('01.11.1997 00:00:00')
        >>> date.to_repr()
        "Date('01.11.1997 00:00:00')"
        >>> date.to_repr('iso1', utcoffset=0)
        "Date('1997-10-31T23:00:00+00:00')"
        """
        return f"Date('{self.to_string(style, utcoffset)}')"

    def __str__(self):
        return self.to_string(self.style)

    def __repr__(self):
        return self.to_repr()

    def __dir__(self):
        return objecttools.dir_(self)


class Period(PeriodABC):
    """Handles the length of a single time period.

    Class |Period| is build on top of the Python module |datetime|.
    In essence, it wraps the |datetime| class |datetime.timedelta| and
    is supposed to specialise this general classes on the needs of HydPy
    users.

    Be aware of the different minimum time resolution of module |datetime|
    (microseconds) and module |timetools| (seconds).

    |Period| objects can be directly initialized via |datetime.timedelta|
    objects, e.g.:

    >>> from datetime import timedelta
    >>> from hydpy import Period
    >>> # Initialize a `timedelta` object...
    >>> timedelta_object = timedelta(1, 0)
    >>> # ...and use it to initialise a `Period` object
    >>> period = Period(timedelta_object)

    Alternatively, one can initialize from |str| objects.  These must
    consist of some characters defining an integer value directly followed
    by a single character defining the unit:

    >>> # 30 seconds:
    >>> Period('30s')
    Period('30s')
    >>> # 5 minutes:
    >>> Period('5m')
    Period('5m')
    >>> # 6 hours:
    >>> Period('6h')
    Period('6h')
    >>> # 1 day:
    >>> Period('1d')
    Period('1d')

    In case you need an "empty" period object, just pass nothing or |None|:

    >>> Period()
    Period()
    >>> Period(None)
    Period()

    |Period| always determines the unit leading to the most legigible
    expression:

    >>> # Print using the unit leading to the smallest integer value:
    >>> period = Period('1d')
    >>> print(period)
    1d
    >>> # Alternatively, the values of all time units are directly
    >>> # available as `float` objects:
    >>> period.days
    1.0
    >>> period.hours
    24.0
    >>> period.minutes
    1440.0
    >>> period.seconds
    86400.0

    If considered useful, logic and arithmetic operations are supported.
    Some examples:

    >>> # Determine the period length between two dates.
    >>> from hydpy import Date
    >>> date1, date2 = Date('1997-11-01'), Date('1996-11-01')
    >>> wholeperiod = date1 - date2
    >>> print(wholeperiod)
    365d
    >>> # Determine, how often one period fits into the other.
    >>> wholeperiod / period
    365.0
    >>> # Get one sixths of period:
    >>> period / 6
    Period('4h')
    >>> # But when trying to get one seventh of period, the following
    >>> # error is raised:
    >>> period / 7
    Traceback (most recent call last):
    ...
    ValueError: For `Period` instances, microseconds must be zero.  \
However, for the given `timedelta` object, it is`857142` instead.

    >>> # Double a period duration.
    >>> period *= 2
    >>> period
    Period('2d')
    >>> # Shift a date.
    >>> date1 - period
    Date('1997-10-30 00:00:00')
    >>> # Note that the modulo operator returns a boolean value, indicating
    >>> # whether division results in a remainder or not:
    >>> Period('1d') % Period('12h')
    False
    >>> Period('1d') % Period('13h')
    True
    >>> # Following the same line of thinking, floor division leads to the
    >>> # opposite results:
    >>> Period('1d') // Period('12h')
    True
    >>> Period('1d') // Period('13h')
    False
    >>> # Compare dates or periods.
    >>> date1 < date2
    False
    >>> min(date1, date2)
    Date('1996-11-01 00:00:00')
    >>> period == wholeperiod
    False
    >>> # Operations on initialisation arguments are supported.
    >>> date1 + '5m'
    Date('1997-11-01 00:05:00')
    >>> period != '12h'
    True
    """

    ConstrArg = Union['Period', datetime.timedelta, str, None]

    def __init__(self, period=None):
        self._timedelta = None
        self.timedelta = period
        self._unit = None

    @property
    def timedelta(self):
        if self._timedelta is None:
            raise AttributeError(
                'The Period object does not contain a timedelta object '
                '(eventually, it has been initialized without an argument).')
        else:
            return self._timedelta

    @timedelta.setter
    def timedelta(self, period):
        if period is None:
            self._timedelta = None
        elif isinstance(period, PeriodABC):
            self._timedelta = getattr(period, 'timedelta', None)
        elif isinstance(period, datetime.timedelta):
            if period.microseconds:
                raise ValueError(
                    f'For `Period` instances, microseconds must be zero.  '
                    f'However, for the given `timedelta` object, it is'
                    f'`{period.microseconds}` instead.')
            self._timedelta = period
        elif isinstance(period, str):
            self._init_from_string(period)
        else:
            raise TypeError(
                f'The supplied argument must be either an instance '
                f' of `datetime.timedelta` or `str`.  The given '
                f'arguments type is {objecttools.classname(period)}.')

    @timedelta.deleter
    def timedelta(self):
        self._timedelta = None

    def _init_from_string(self, period):
        try:
            number = int(period[:-1])
        except ValueError:
            raise ValueError(
                f'All characters of the given period string, '
                f'except the last one which represents the unit, '
                f'need to define a whole decimal number.  Instead,'
                f' these characters are `{period[:-1]}`.')
        self._unit = period[-1]
        if self._unit not in ('d', 'h', 'm', 's'):
            raise ValueError(
                f'The last character of the given period string needs '
                f'to be either `d` (days), `h` (hours) or `m` (minutes).  '
                f'Instead, the last character is `{self._unit}`.')
        if self._unit == 'd':
            self._timedelta = datetime.timedelta(number, 0)
        elif self._unit == 'h':
            self._timedelta = datetime.timedelta(0, number*3600)
        elif self._unit == 'm':
            self._timedelta = datetime.timedelta(0, number*60)
        elif self._unit == 's':
            self._timedelta = datetime.timedelta(0, number)

    @classmethod
    def fromseconds(cls, seconds):
        """Return a |Period| instance based on a given number of seconds."""
        try:
            seconds = int(seconds)
        except TypeError:
            seconds = int(seconds.flatten()[0])
        return cls(datetime.timedelta(0, int(seconds)))

    @classmethod
    def from_cfunits(cls, units):
        """Return a |Period| object representing the time unit of the
        given `units` string aggreeing with the NetCDF-CF conventions.

        The following example string is taken from the `Time Coordinate`_
        chapter of the NetCDF-CF conventions.  Note that the character
        of the first entry (the actual time unit) is of relevance:

        >>> from hydpy import Period
        >>> Period.from_cfunits('seconds since 1992-10-8 15:15:42.5 -6:00')
        Period('1s')
        >>> Period.from_cfunits(' day since 1992-10-8 15:15:00')
        Period('1d')
        >>> Period.from_cfunits('m since 1992-10-8')
        Period('1m')
        """
        return cls(f'1{units.strip()[0]}')

    def _guessunit(self):
        """Guess the unit of the period as the largest one, which results in
        an integer duration.
        """
        if not self.days % 1:
            return 'd'
        elif not self.hours % 1:
            return 'h'
        elif not self.minutes % 1:
            return 'm'
        elif not self.seconds % 1:
            return 's'
        else:
            raise ValueError(
                'The stepsize is not a multiple of one '
                'second, which is not allowed.')

    unit = property(_guessunit)

    def _get_seconds(self):
        """Period length in seconds."""
        return self.timedelta.total_seconds()

    seconds = property(_get_seconds)

    def _get_minutes(self):
        """Period length in minutes."""
        return self.seconds / 60

    minutes = property(_get_minutes)

    def _get_hours(self):
        """Period length in hours."""
        return self.minutes / 60

    hours = property(_get_hours)

    def _get_days(self):
        """Period length in days."""
        return self.hours / 24

    days = property(_get_days)

    def __bool__(self):
        return self._timedelta is not None

    def __nonzero__(self):
        return self.__bool__()

    def __add__(self, other):
        try:
            new = Date(Date(other).datetime + self.timedelta)
            new.style = other.style
            return new
        except (TypeError, ValueError):
            try:
                return Period(self.timedelta + Period(other).timedelta)
            except (TypeError, ValueError):
                raise Exception(
                    f'Object `{str(other)}` of type `{type(other)}` '
                    f'cannot be added to a `Period` instance.')

    def __iadd__(self, other):
        self.timedelta += Period(other).timedelta
        return self

    def __sub__(self, other):
        return Period(self.timedelta - Period(other).timedelta)

    def __isub__(self, other):
        self.timedelta -= Period(other).timedelta
        return self

    def __mul__(self, value):
        return Period(self.timedelta * value)

    def __rmul__(self, value):
        return self * value

    def __imul__(self, value):
        self.timedelta *= value
        return self

    def __truediv__(self, other):
        if isinstance(other, numbers.Integral):
            return Period(self.timedelta // other)
        return self.seconds / Period(other).seconds

    def __itruediv__(self, value):
        return self / value

    def __mod__(self, other):
        return (self.seconds % Period(other).seconds) != 0.

    def __floordiv__(self, other):
        return (self.seconds % Period(other).seconds) == 0.

    def __lt__(self, other):
        return self.timedelta < Period(other).timedelta

    def __le__(self, other):
        return self.timedelta <= Period(other).timedelta

    def __eq__(self, other):
        return self.timedelta == Period(other).timedelta

    def __ne__(self, other):
        return self.timedelta != Period(other).timedelta

    def __gt__(self, other):
        return self.timedelta > Period(other).timedelta

    def __ge__(self, other):
        return self.timedelta >= Period(other).timedelta

    def __str__(self):
        if not self:
            return '?'
        if self.unit == 'd':
            return f'{self.days:.0f}d'
        if self.unit == 'h':
            return f'{self.hours:.0f}h'
        if self.unit == 'm':
            return f'{self.minutes:.0f}m'
        return f'{self.seconds:.0f}s'

    def __repr__(self):
        if self:
            return f"Period('{str(self)}')"
        return 'Period()'

    def __dir__(self):
        return objecttools.dir_(self)


class Timegrid(TimegridABC):
    """Handle a time period defined by to dates and a step size in between.

    In hydrological modelling, input (and output) data are usually only
    available with a certain resolution, which also determines the possible
    resolution of the actual simulation.  This is reflected by the class
    |Timegrid|, which represents the first and the last date of e.g.
    a simulation period as well as the intermediate dates. A |Timegrid|
    object is initialized by defining its first date, its last date and its
    stepsize:

    >>> from hydpy import Date, Period, Timegrid
    >>> # Either pass the proper attributes directly...
    >>> firstdate = Date('1996-11-01')
    >>> lastdate = Date('1997-11-01')
    >>> stepsize = Period('1d')
    >>> timegrid_sim = Timegrid(firstdate, lastdate, stepsize)
    >>> timegrid_sim
    Timegrid('1996-11-01 00:00:00',
             '1997-11-01 00:00:00',
             '1d')
    >>> # ...or pass their initialization arguments...
    >>> timegrid_sim = Timegrid('1996-11-01', '1997-11-01', '1d')
    >>> timegrid_sim
    Timegrid('1996-11-01 00:00:00',
             '1997-11-01 00:00:00',
             '1d')
    >>> # or predefined timegrid object:
    >>> Timegrid(timegrid_sim)
    Timegrid('1996-11-01 00:00:00',
             '1997-11-01 00:00:00',
             '1d')

    For wrong arguments errors like the following are raised:

    >>> Timegrid(firstdate, lastdate)
    Traceback (most recent call last):
    ...
    ValueError: While trying to prepare a Trimegrid object based on the \
arguments `1996-11-01 00:00:00 and 1997-11-01 00:00:00 , the following \
error occurred: Wrong number of arguments. Either pass one preprepared \
Timegrid object or three objects interpretable as dates and periods.

    |Timegrid| provides functionalities to ease and secure the handling
    of dates in HydPy. Here some examples:

    >>> # Retrieve a date via indexing, e.g. the second one:
    >>> date = timegrid_sim[1]
    >>> date
    Date('1996-11-02 00:00:00')
    >>> # Or the other way round, retrieve the index belonging to a date:
    >>> timegrid_sim[date]
    1
    >>> # Indexing beyond the ranges of the actual time period is allowed:
    >>> timegrid_sim[-366]
    Date('1995-11-01 00:00:00')
    >>> timegrid_sim[timegrid_sim[date+'365d']]
    Date('1997-11-02 00:00:00')
    >>> # Iterate through all time grid points (e.g. to print the first
    >>> # day of each month):
    >>> for date in timegrid_sim:
    ...     if date.day == 1:
    ...         print(date)
    1996-11-01 00:00:00
    1996-12-01 00:00:00
    ...
    1997-09-01 00:00:00
    1997-10-01 00:00:00

    After doing some changes one should call the |Timegrid.verify|
    method:

    >>> # `verify` keeps silent if everything seems to be alright...
    >>> timegrid_sim.verify()
    >>> # ...but raises an suitable exception otherwise:
    >>> timegrid_sim.firstdate.minute = 30
    >>> timegrid_sim.verify()
    Traceback (most recent call last):
    ...
    ValueError: Unplausible timegrid. The period span between the given \
dates 1996-11-01 00:30:00 and 1997-11-01 00:00:00 is not a multiple of the \
given step size 1d.

    One can check two |Timegrid| instances for equality:

    >>> # Make a deep copy of the timegrid already existing.
    >>> import copy
    >>> timegrid_test = copy.deepcopy(timegrid_sim)
    >>> # Test for equality and non-equality.
    >>> timegrid_sim == timegrid_test
    True
    >>> timegrid_sim != timegrid_test
    False
    >>> # Modify one date of the new timegrid.
    >>> timegrid_test.firstdate += '1d'
    >>> # Again, test for equality and non-equality.
    >>> timegrid_sim == timegrid_test
    False
    >>> timegrid_sim != timegrid_test
    True

    Also, one can check if a date or even the whole timegrid lies within a
    span defined by a |Timegrid| instance:

    >>> # Define a long timegrid:
    >>> timegrid_long = Timegrid('1996.11.01', '2006.11.01', '1d')
    >>> # Check different dates for lying in the defined time period:
    >>> '1996-10-31' in timegrid_long
    False
    >>> '1996-11-01' in timegrid_long
    True
    >>> '1996-11-02' in timegrid_long
    True
    >>> # For dates not alligned on the grid `False` is returned:
    >>> '1996-11-01 12:00' in timegrid_long
    False

    >>> # Now define a timegrid containing only the first year of the
    >>> # long one:
    >>> timegrid_short = Timegrid('1996-11-01', '1997-11-01', '1d')
    >>> # Check which timegrid is contained by the other:
    >>> timegrid_short in timegrid_long
    True
    >>> timegrid_long in timegrid_short
    False
    >>> # For timegrids with different stepsizes `False` is returned:
    >>> timegrid_short.stepsize = Period('1h')
    >>> timegrid_short in timegrid_long
    False
    """
    _firstdate = None
    _lastdate = None
    _stepsize = None

    def __init__(self, *args):
        try:
            if len(args) == 1:
                self.firstdate = args[0].firstdate
                self.lastdate = args[0].lastdate
                self.stepsize = args[0].stepsize
            elif len(args) == 3:
                self.firstdate, self.lastdate, self.stepsize = args
            else:
                raise ValueError(
                    'Wrong number of arguments.')
            self.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to prepare a Trimegrid object based '
                f'on the arguments `{objecttools.enumeration(args)} ',
                f'Either pass one preprepared Timegrid object or three '
                f'objects interpretable as dates and periods.')

    @property
    def firstdate(self):
        return self._firstdate

    @firstdate.setter
    def firstdate(self, firstdate):
        self._firstdate = Date(firstdate)

    @property
    def lastdate(self):
        return self._lastdate

    @lastdate.setter
    def lastdate(self, lastdate):
        self._lastdate = Date(lastdate)

    @property
    def stepsize(self):
        return self._stepsize

    @stepsize.setter
    def stepsize(self, stepsize):
        self._stepsize = Period(stepsize)

    @classmethod
    def from_array(cls, array):
        """Returns a |Timegrid| instance based on two date and one period
        information stored in the first 13 rows of a |numpy.ndarray| object.
        """
        try:
            return cls(Date.from_array(array[:6]),
                       Date.from_array(array[6:12]),
                       Period.fromseconds(array[12]))
        except IndexError:
            raise IndexError(
                f'To define a Timegrid instance via an array, 13 '
                f'numbers are required.  However, the given array '
                f'consist of {len(array)} entries/rows only.')

    def to_array(self):
        """Returns a 1-dimensional |numpy| |numpy.ndarray| with thirteen
        entries first defining the start date, secondly defining the end
        date and thirdly the step size in seconds.
        """
        values = numpy.empty(13, dtype=float)
        values[:6] = self.firstdate.to_array()
        values[6:12] = self.lastdate.to_array()
        values[12] = self.stepsize.seconds
        return values

    @classmethod
    def from_timepoints(cls, timepoints, refdate, unit='hours'):
        """Return a |Timegrid| object representing the given starting
        `timepoints` in relation to the given `refdate`.

        The following examples identical with the ones of
        |Timegrid.to_timepoints| but reversed.

        At least two given time points must be increasing and
        equidistant.  By default, they are assumed in hours since
        the given reference date:

        >>> from hydpy import Timegrid
        >>> Timegrid.from_timepoints(
        ...     [0.0, 6.0, 12.0, 18.0], '01.01.2000')
        Timegrid('01.01.2000 00:00:00',
                 '02.01.2000 00:00:00',
                 '6h')
        >>> Timegrid.from_timepoints(
        ...     [24.0, 30.0, 36.0, 42.0], '1999-12-31')
        Timegrid('2000-01-01 00:00:00',
                 '2000-01-02 00:00:00',
                 '6h')

        Other time units (`days` or `min`) must be passed explicitely
        (only the first character counts):

        >>> Timegrid.from_timepoints(
        ...     [0.0, 0.25, 0.5, 0.75], '01.01.2000', unit='d')
        Timegrid('01.01.2000 00:00:00',
                 '02.01.2000 00:00:00',
                 '6h')
        >>> Timegrid.from_timepoints(
        ...     [1.0, 1.25, 1.5, 1.75], '1999-12-31', unit='day')
        Timegrid('2000-01-01 00:00:00',
                 '2000-01-02 00:00:00',
                 '6h')
        """
        refdate = Date(refdate)
        unit = Period.from_cfunits(unit)
        delta = timepoints[1]-timepoints[0]
        firstdate = refdate+timepoints[0]*unit
        lastdate = refdate+(timepoints[-1]+delta)*unit
        stepsize = (lastdate-firstdate)/len(timepoints)
        return cls(firstdate, lastdate, stepsize)

    def to_timepoints(self, unit='hours', offset=None):
        """Return an |numpy.ndarray| representing the starting time points
        of the |Timegrid| object.

        The following examples identical with the ones of
        |Timegrid.from_timepoints| but reversed.

        By default, the time points are given in hours:

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid('2000-01-01', '2000-01-02', '6h')
        >>> timegrid.to_timepoints()
        array([  0.,   6.,  12.,  18.])

        Other time units (`days` or `min`) can be defined (only the first
        character counts):

        >>> timegrid.to_timepoints(unit='d')
        array([ 0.  ,  0.25,  0.5 ,  0.75])

        Additionally, one can pass an `offset` that must be of type |int|
        or an valid |Period| initialization argument:

        >>> timegrid.to_timepoints(offset=24)
        array([ 24.,  30.,  36.,  42.])
        >>> timegrid.to_timepoints(offset='1d')
        array([ 24.,  30.,  36.,  42.])
        >>> timegrid.to_timepoints(unit='day', offset='1d')
        array([ 1.  ,  1.25,  1.5 ,  1.75])
        """
        unit = Period.from_cfunits(unit)
        if offset is None:
            offset = 0.
        else:
            try:
                offset = Period(offset)/unit
            except TypeError:
                offset = offset
        step = self.stepsize/unit
        nmb = len(self)
        variable = numpy.linspace(offset, offset+step*(nmb-1), nmb)
        return variable

    def array2series(self, array):
        """Prefix the information of the actual Timegrid object to the given
        array and return it.

        The Timegrid information is stored in the first thirteen values of
        the first axis of the returned series.  Initialize a Timegrid object
        and apply its `array2series` method on a simple list containing
        numbers:

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid('2000-11-01 00:00', '2000-11-01 04:00', '1h')
        >>> series = timegrid.array2series([1, 2, 3.5, '5.0'])

        The first six entries contain the first date of the timegrid (year,
        month, day, hour, minute, second):

        >>> from hydpy import round_
        >>> round_(series[:6])
        2000.0, 11.0, 1.0, 0.0, 0.0, 0.0

        The six subsequent entries contain the last date:

        >>> round_(series[6:12])
        2000.0, 11.0, 1.0, 4.0, 0.0, 0.0

        The thirteens value is the step size in seconds:

        >>> round_(series[12])
        3600.0

        The last four value are the ones of the given vector:

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

        All other columns of the first thirteen rows contain nan values, e.g.:

        >>> round_(series[12, :])
        3600.0, nan, nan, nan

        The original values are stored in the last four rows, e.g.:

        >>> round_(series[13, :])
        1.0, 0.0, 0.0, 0.0

        Inappropriate array objects result in error messages like:

        >>> timegrid.array2series([[1, 2], [3]])
        Traceback (most recent call last):
        ...
        ValueError: While trying to prefix timegrid information to the given \
array, the following error occurred: setting an array element with a sequence.

        If the given array does not fit to the defined timegrid, a special
        error message is returned:

        >>> timegrid.array2series([[1, 2], [3, 4]])
        Traceback (most recent call last):
        ...
        ValueError: When converting an array to a sequence, the lengths of \
the timegrid and the given array must be equal, but the length of the \
timegrid object is `4` and the length of the array object is `2`.
        """
        try:
            array = numpy.array(array, dtype=float)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to prefix timegrid information to the '
                'given array')
        if len(array) != len(self):
            raise ValueError(
                f'When converting an array to a sequence, the lengths of the '
                f'timegrid and the given array must be equal, but the length '
                f'of the timegrid object is `{len(self)}` and the length of '
                f'the array object is `{len(array)}`.')
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

    def verify(self):
        """Raise an |ValueError| if the dates or the step size of the time
        frame are inconsistent.
        """
        if self.firstdate >= self.lastdate:
            raise ValueError(
                f'Unplausible timegrid. The first given date '
                f'{self.firstdate}, the second given date is {self.lastdate}.')
        if (self.lastdate-self.firstdate) % self.stepsize:
            raise ValueError(
                f'Unplausible timegrid. The period span between the given '
                f'dates {self.firstdate} and {self.lastdate} is not '
                f'a multiple of the given step size {self.stepsize}.')

    def __len__(self):
        return abs(int((self.lastdate-self.firstdate) / self.stepsize))

    def __getitem__(self, key):
        if isinstance(key, numbers.Integral):
            return Date(self.firstdate + key*self.stepsize)
        else:
            key = Date(key)
            index = (key-self.firstdate) / self.stepsize
            if index % 1.:
                raise ValueError(
                    f'The given date `{key}` is not properly alligned on '
                    f'the indexed timegrid.')
            else:
                return int(index)

    def __iter__(self):
        date = copy.deepcopy(self.firstdate)
        while date < self.lastdate:
            yield date
            date = date + self.stepsize

    def _containsdate(self, date):
        date = Date(date)
        return ((self.firstdate <= date <= self.lastdate) and
                ((date-self.firstdate) // self.stepsize))

    def _containstimegrid(self, timegrid):
        return (self._containsdate(timegrid.firstdate) and
                self._containsdate(timegrid.lastdate) and
                (timegrid.stepsize == self.stepsize))

    def __contains__(self, other):
        if isinstance(other, TimegridABC):
            return self._containstimegrid(other)
        return self._containsdate(other)

    def __eq__(self, other):
        return ((self.firstdate == other.firstdate) and
                (self.lastdate == other.lastdate) and
                (self.stepsize == other.stepsize))

    def __ne__(self, other):
        return ((self.firstdate != other.firstdate) or
                (self.lastdate != other.lastdate) or
                (self.stepsize != other.stepsize))

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix, style=None, utcoffset=None):
        """Return a |repr| string with an prefixed assignement.

        Without option arguments given, printing the returned string
        looks like:

        >>> from hydpy import Timegrid
        >>> timegrid = Timegrid('1996-11-01 00:00:00',
        ...                     '1997-11-01 00:00:00',
        ...                     '1d')
        >>> print(timegrid.assignrepr(prefix='timegrid = '))
        timegrid = Timegrid('1996-11-01 00:00:00',
                            '1997-11-01 00:00:00',
                            '1d')

        The optional arguments are passed to method |Date.to_repr|
        without any modifications:

        >>> print(timegrid.assignrepr(
        ...     prefix='', style='iso1', utcoffset=120))
        Timegrid('1996-11-01T01:00:00+02:00',
                 '1997-11-01T01:00:00+02:00',
                 '1d')
        """
        skip = len(prefix) + 9
        blanks = ' ' * skip
        return (f"{prefix}Timegrid('"
                f"{self.firstdate.to_string(style, utcoffset)}',\n"
                f"{blanks}'{self.lastdate.to_string(style, utcoffset)}',\n"
                f"{blanks}'{str(self.stepsize)}')")

    def __dir__(self):
        return objecttools.dir_(self)


class Timegrids(TimegridsABC):
    """Handles all |Timegrid| instances of a HydPy project.

    The HydPy framework distinguishes two `time frames`, one associated
    with the input date available on disk (`data`), one associated with the
    initialisation period (`init`), and one associated with the actual
    simulation period (`sim`).  The last two latter time frames are
    represented by two different |Timegrid| objects, which are both
    handled by a single |Timegrids| object.  (The `data` time frames
    are also defined via |Timegrid| objects, but for each input data
    file separately. See module |sequencetools| for further information.)

    There is usually only one |Timegrids| object required within each
    HydPy project.  Usually it is instantiated in the project's main file
    or at the top of script defining a HydPy workflow and assigned to the
    |pub| module, which provides access to "global" project settings:

    >>> from hydpy import Timegrid, Timegrids

    In many cases, one want to perform the simulation over the whole
    initialization period.  Then only one Timegrid instance must be
    defined:

    >>> Timegrids(Timegrid('2000-11-11',
    ...                    '2003-11-11',
    ...                    '1d'))
    Timegrids(Timegrid('2000-11-11 00:00:00',
                       '2003-11-11 00:00:00',
                       '1d'))

    For convenience, one can pass the required strings directly to the
    constructor, and also an already existing |Timegrids| object:

    >>> timegrid = Timegrids('2000-11-11', '2003-11-11', '1d')
    >>> timegrid
    Timegrids(Timegrid('2000-11-11 00:00:00',
                       '2003-11-11 00:00:00',
                       '1d'))
    >>> Timegrids(timegrid)
    Timegrids(Timegrid('2000-11-11 00:00:00',
                       '2003-11-11 00:00:00',
                       '1d'))

    Wrong arguments should result in understandable error messages:

    >>> Timegrids()
    Traceback (most recent call last):
    ...
    ValueError: While trying to define a new Timegrids object based on \
arguments ``, the following error occurred: Wrong number of arguments. \
Either pass one `Timegrids` object, one or two `Timegrid` objects, \
or three strings.

    For simulations covering only a part of the initialisation period,
    two Timegrid instances must be given:

    >>> timegrids = Timegrids(Timegrid('2000-11-11',
    ...                                '2003-11-11',
    ...                                '1h'),
    ...                       Timegrid('2001-11-11',
    ...                                '2002-11-11',
    ...                                '1h'))
    >>> timegrids
    Timegrids(Timegrid('2000-11-11 00:00:00',
                       '2003-11-11 00:00:00',
                       '1h'),
              Timegrid('2001-11-11 00:00:00',
                       '2002-11-11 00:00:00',
                       '1h'))

    Some examples on the usage of this |Timegrids| instance:

    >>> # Get the general data and simulation step size:
    >>> timegrids.stepsize
    Period('1h')
    >>> # Get the factor to convert `mm/stepsize` to m^3/s for an area
    >>> # of 36 km^2:
    >>> timegrids.qfactor(36.)
    10.0
    >>> # Get the index of the first values of the `initialization frame`
    >>> # which belong to the `simulation frame`.
    >>> timegrids.init[timegrids.sim.firstdate]
    8760

    You can check two |Timegrids| objects for equality:

    >>> import copy
    >>> test = copy.deepcopy(timegrids)
    >>> timegrids == test
    True
    >>> test.init.firstdate += '1d'
    >>> timegrids == test
    False
    >>> timegrids != test
    True

    When comparing with a "wrong" object (which does not provide both
    an `init` and a `sim` |Timegrid| member), |False| is returned:

    >>> timegrids == 'test'
    False
    >>> timegrids != 'test'
    True

    Each manual change should be followed by calling the
    |Timegrids.verify| method, which calls the |Timegrid.verify|
    method of the single |Timegrid| instances and performs some
    additional tests:

    >>> # To postpone the end of the `simulation time frame` exactly
    >>> # one year is fine:
    >>> timegrids.sim.lastdate += '365d'
    >>> timegrids.verify()
    >>> # But any additional day shifts it outside the `initialisation
    >>> # time frame`, so verification raises a value error:
    >>> timegrids.sim.lastdate += '1d'
    >>> timegrids.verify()
    Traceback (most recent call last):
    ...
    ValueError: The last date of the initialisation period \
(2003-11-11 00:00:00) must not be earlier than the last date of the \
simulation period (2003-11-12 00:00:00).
    >>> timegrids.sim.lastdate -= '1d'

    >>> # The other boundary is also checked:
    >>> timegrids.sim.firstdate -= '366d'
    >>> timegrids.verify()
    Traceback (most recent call last):
    ...
    ValueError: The first date of the initialisation period \
(2000-11-11 00:00:00) must not be later than the first date of the \
simulation period (2000-11-10 00:00:00).

    >>> # Both timegrids are checked to have the same step size:
    >>> timegrids.sim = Timegrid('2001-11-11',
    ...                          '2002-11-11',
    ...                          '1d')
    >>> timegrids.verify()
    Traceback (most recent call last):
    ...
    ValueError: The initialization stepsize (1h) must be identical \
with the simulation stepsize (1d).

    >>> # Also, they are checked to be properly aligned:
    >>> timegrids.sim = Timegrid('2001-11-11 00:30',
    ...                              '2002-11-11 00:30',
    ...                              '1h')
    >>> timegrids.verify()
    Traceback (most recent call last):
    ...
    ValueError: The simulation time grid is not properly alligned \
on the initialization time grid.
    """

    def __init__(self, *args):
        try:
            if (len(args) == 0) or (len(args) > 3):
                raise ValueError(
                    'Wrong number of arguments.')
            if (len(args) == 1) and isinstance(args[0], type(self)):
                self.init = args[0].init
                self.sim = args[0].sim
            else:
                if len(args) == 3:
                    args = [Timegrid(*args)]
                self.init = Timegrid(args[0])
                try:
                    self.sim = Timegrid(args[1])
                except IndexError:
                    self.sim = copy.deepcopy(self.init)
            self.verify()
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to define a new Timegrids object based on '
                f'arguments `{objecttools.enumeration(args)}`',
                f'Either pass one `Timegrids` object, one or two `Timegrid` '
                f'objects, or three strings.')

    def _get_stepsize(self):
        """Stepsize of all handled |Timegrid| objects."""
        return self.init.stepsize

    def _set_stepsize(self, stepsize):
        stepsize = Period(stepsize)
        for (dummy, timegrid) in self:
            timegrid.stepsize = stepsize

    stepsize = property(_get_stepsize, _set_stepsize)

    def verify(self):
        """Raise an |ValueError| it the different time grids are
        inconsistent."""
        self.init.verify()
        self.sim.verify()
        if self.init.firstdate > self.sim.firstdate:
            raise ValueError(
                f'The first date of the initialisation period '
                f'({self.init.firstdate}) must not be later '
                f'than the first date of the simulation period '
                f'({self.sim.firstdate}).')
        elif self.init.lastdate < self.sim.lastdate:
            raise ValueError(
                f'The last date of the initialisation period '
                f'({self.init.lastdate}) must not be earlier '
                f'than the last date of the simulation period '
                f'({self.sim.lastdate}).')
        elif self.init.stepsize != self.sim.stepsize:
            raise ValueError(
                f'The initialization stepsize ({self.init.stepsize}) '
                f'must be identical with the simulation stepsize '
                f'({self.sim.stepsize}).')
        else:
            try:
                self.init[self.sim.firstdate]
            except ValueError:
                raise ValueError(
                    'The simulation time grid is not properly '
                    'alligned on the initialization time grid.')

    def qfactor(self, area):
        """Return the factor for converting `mm/stepsize` to `m^3/s`.

        Argument:
            * area (|float|): Reference area, which must be given in
              the unit `km^2`.
        """
        return area * 1000. / self.stepsize.seconds

    def parfactor(self, stepsize):
        """Return the factor for converting parameter to simulation step size.

        Argument:
            * stepsize (|Period| or an suitable initialization argument
              thereof): Time interval, to which the parameter values refer.
        """
        return self.stepsize / Period(stepsize)

    def __eq__(self, other):
        try:
            return ((self.init == other.init) and
                    (self.sim == other.sim))
        except AttributeError:
            return False

    def __str__(self):
        return 'All timegrids of the actual HydPy project.'

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        """Return a |repr| string with a prefixed assignment."""
        caller = 'Timegrids('
        blanks = ' ' * (len(prefix) + len(caller))
        prefix = f'{prefix}{caller}'
        lines = [f'{self.init.assignrepr(prefix)},']
        if self.sim != self.init:
            lines.append(f'{self.sim.assignrepr(blanks)},')
        lines[-1] = lines[-1][:-1] + ')'
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class TOY:
    """Time of year handler.

    |TOY| objects are used to define certain things that are true for a
    certain time point in each year.  The smallest supported time unit is
    seconds.

    Normally, for initialization a string is passed, defining the month, the
    day, the hour, the minute and the second in the order they are mentioned,
    separated by a single underscore:

    >>> from hydpy.core.timetools import TOY
    >>> t = TOY('3_13_23_33_43')
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

    If a lower precision is required, one can shorten the string, which
    implicitely sets the omitted property to the lowest possible value:

    >>> TOY('3_13_23_33')
    TOY('3_13_23_33_0')

    The most extreme example would be, to pass not string at all:

    >>> TOY()
    TOY('1_1_0_0_0')

    One can prefix some information to the string, which is usefull when the
    string is to be used as a valid variable name somewhere else:

    >>> TOY('something_3_13_23_33_2')
    TOY('3_13_23_33_2')

    As one can see, the prefixed information is lost in the printed string
    representation.  But a string with a standard prefix is returned through
    applying |str| on |TOY| instances:

    >>> str(TOY('something_3_13_23_33_2'))
    'toy_3_13_23_33_2'

    Alternatively, one can use a |Date| object as a initialization argument,
    ommitting the year:

    >>> TOY(Date('2001.02.03 04:05:06'))
    TOY('2_3_4_5_6')

    It is only allowed to modify the mentioned properties, not to define new
    ones:

    >>> t.microsecond = 53
    Traceback (most recent call last):
    ...
    AttributeError: TOY (time of year) objects only allow to set the \
properties month, day, hour, minute, and second, but `microsecond` is given.

    It is allowed to pass objects that can be converted to integers:

    >>> t.second = '53'
    >>> t.second
    53

    If the passed object cannot be converted properly, an exception is raised:

    >>> t.second = 'fiftythree'
    Traceback (most recent call last):
    ...
    ValueError: For TOY (time of year) objects, all properties must be of \
type `int`, but the value `fiftythree` of type `str` given for property \
`second` cannot be converted to `int`.

    Additionally, given values are checked to lie within a suitable range:

    >>> t.second = 60
    Traceback (most recent call last):
    ...
    ValueError: The value of property `second` of TOY (time of year) \
objects must lie within the range `(0, 59)`, but the given value is `60`.

    Note that the allowed values for `month` and `day` depend on each other,
    which is why the order one defines them might be of importance.  So, if
    January is predefined, one can set day to the 31th:

    >>> t.month = 1
    >>> t.day = 31

    But afterwards one cannot directly change the month to February:

    >>> t.month = 2
    Traceback (most recent call last):
    ...
    ValueError: The value of property `month` of the actual TOY \
(time of year) object must not be the given value `2`, as the day \
has already been set to `31`.

    Hence first set `day` to a smaller value and then change `month`:

    >>> t.day = 28
    >>> t.month = 2

    For February it is important to note, that the 29th is generally
    disallowed:

    >>> t.day = 29
    Traceback (most recent call last):
    ...
    ValueError: The value of property `day` of the actual TOY (time of year) \
object must lie within the range `(1, 28)`, as the month has already been \
set to `2`, but the given value is `29`.

    It is possible to compare two |TOY| instances:

    >>> t1, t2 = TOY('1'), TOY('2')
    >>> (t1 < t1, t1 < t2, t2 < t1)
    (False, True, False)
    >>> (t1 <= t1, t1 <= t2, t2 <= t1)
    (True, True, False)
    >>> (t1 == t1, t1 == t2)
    (True, False)
    >>> (t1 != t1, t1 != t2)
    (False, True)
    >>> (t1 >= t1, t1 >= t2, t2 >= t1)
    (True, False, True)
    >>> (t1 > t1, t1 > t2, t2 > t1)
    (False, False, True)

    Subtracting two |TOY| object gives their time difference in seconds:

    >>> TOY('1_1_0_3_0') - TOY('1_1_0_1_30')
    90

    Instead of negative values, it is always assumed that the first |TOY|
    object lies within the future (eventually within the subsequent year):

    >>> TOY('1_1_0_1_30') - TOY('12_31_23_58_30')
    180
    """
    _PROPERTIES = collections.OrderedDict((('month', (1, 12)),
                                           ('day', (1, 31)),
                                           ('hour', (0, 23)),
                                           ('minute', (0, 59)),
                                           ('second', (0, 59))))
    _STARTDATE = Date('2000-01-01')
    _ENDDATE = Date('2001-01-01')

    def __init__(self, value=''):
        with objecttools.ResetAttrFuncs(self):
            self.month = None
            self.day = None
            self.hour = None
            self.minute = None
            self.second = None
        if isinstance(value, DateABC):
            for name in self._PROPERTIES.keys():
                self.__dict__[name] = getattr(value, name)
        else:
            values = value.split('_')
            if not values[0].isdigit():
                del values[0]
            for prop in self._PROPERTIES:
                try:
                    setattr(self, prop, values.pop(0))
                except IndexError:
                    if prop in ('month', 'day'):
                        setattr(self, prop, 1)
                    else:
                        setattr(self, prop, 0)
                except ValueError:
                    objecttools.augment_excmessage(
                        f'While trying to retrieve the {prop} for TOY (time '
                        f'of year) object based on the string `{value}`')

    def __setattr__(self, name, value):
        if name not in self._PROPERTIES:
            raise AttributeError(
                f'TOY (time of year) objects only allow to set the '
                f'properties {objecttools.enumeration(self._PROPERTIES.keys())}'
                f', but `{name}` is given.')
        try:
            value = int(value)
        except ValueError:
            raise ValueError(
                f'For TOY (time of year) objects, all properties must be of '
                f'type `int`, but the {objecttools.value_of_type(value)} '
                f'given for property `{name}` cannot be converted to `int`.')
        if (name == 'day') and (self.month is not None):
            bounds = (1, calendar.monthrange(1999, self.month)[1])
            if not bounds[0] <= value <= bounds[1]:
                raise ValueError(
                    f'The value of property `day` of the actual TOY '
                    f'(time of year) object must lie within the range '
                    f'`{bounds}`, as the month has already been set to '
                    f'`{self.month}`, but the given value is `{value}`.')
        elif (name == 'month') and (self.day is not None):
            bounds = (1, calendar.monthrange(2000, value)[1])
            if not bounds[0] <= self.day <= bounds[1]:
                raise ValueError(
                    f'The value of property `month` of the actual TOY '
                    f'(time of year) object must not be the given value '
                    f'`{value}`, as the day has already been set to '
                    f'`{self.day}`.')
        else:
            bounds = self._PROPERTIES[name]
            if not bounds[0] <= value <= bounds[1]:
                raise ValueError(
                    f'The value of property `{name}` of TOY (time of '
                    f'year) objects must lie within the range `{bounds}`, '
                    f'but the given value is `{value}`.')
        object.__setattr__(self, name, value)

    @property
    def seconds_passed(self):
        """Amount of time passed in seconds since the beginning of the year.

        In the first example, the year is only one minute and thirty seconds
        old:

        >>> from hydpy.core.timetools import TOY
        >>> TOY('1_1_0_1_30').seconds_passed
        90

        The second example shows that the 29th February is generally included:

        >>> TOY('3').seconds_passed
        5184000
        """
        return int((Date(self).datetime -
                    self._STARTDATE.datetime).total_seconds())

    @property
    def seconds_left(self):
        """Remaining part of the year in seconds.

        In the first example, only one minute and thirty seconds of the year
        remain:

        >>> from hydpy.core.timetools import TOY
        >>> TOY('12_31_23_58_30').seconds_left
        90

        The second example shows that the 29th February is generally included:

        >>> TOY('2').seconds_left
        28944000
        """
        return int((self._ENDDATE.datetime -
                    Date(self).datetime).total_seconds())

    @classmethod
    def centred_timegrid(cls, simulationstep):
        """Return a |Timegrid| object defining the central time points
        of the year 2000 for the given simulation step.

        >>> from hydpy.core.timetools import TOY
        >>> TOY.centred_timegrid('1d')
        Timegrid('2000-01-01 12:00:00',
                 '2001-01-01 12:00:00',
                 '1d')
        """
        simulationstep = Period(simulationstep)
        return Timegrid(
            cls._STARTDATE+simulationstep/2,
            cls._ENDDATE+simulationstep/2,
            simulationstep)

    def __lt__(self, other):
        return self.seconds_passed < other.seconds_passed

    def __le__(self, other):
        return self.seconds_passed <= other.seconds_passed

    def __eq__(self, other):
        return self.seconds_passed == other.seconds_passed

    def __ne__(self, other):
        return self.seconds_passed != other.seconds_passed

    def __gt__(self, other):
        return self.seconds_passed > other.seconds_passed

    def __ge__(self, other):
        return self.seconds_passed >= other.seconds_passed

    def __sub__(self, other):
        if self >= other:
            return self.seconds_passed - other.seconds_passed
        return self.seconds_passed + other.seconds_left

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        string = '_'.join(str(getattr(self, prop)) for prop
                          in self._PROPERTIES.keys())
        return f"toy_{string}"

    def __repr__(self):
        return "TOY('%s')" % '_'.join(str(getattr(self, prop)) for prop
                                      in self._PROPERTIES.keys())

    __dir__ = objecttools.dir_
