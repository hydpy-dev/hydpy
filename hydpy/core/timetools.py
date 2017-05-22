
"""This module specifies how  dates and periods are handled in HydPy.

The following classes are implemented:
    * :class:`Date`: Defines a single time point.
    * :class:`Period`: Defines a single time duration.
    * :class:`Timegrid`: Defines an equidistant sequence of time points.
    * :class:`Timegrids`: Handles all :class:`Timegrid` instances of a
      HydPy project.


Date and Period
===============

Both classes :class:`Date` and :class:`Period` are build on top of the Python
module :mod:`datetime`. In essence, they wrap the :mod:`datetime` classes
:class:`~datetime.datetime` and :class:`~datetime.timedelta`, and are supposed
to specialise these general classes on the needs of HydPy users.

Be aware of the different minimum time resolution of module :mod:`datetime`
(microseconds) and module :mod:`~hydpy.core.timetools` (seconds).

:class:`Date` objects can be initialized via :class:`~datetime.datetime`
objects directly, e.g.::

    from datetime import datetime
    from hydpy.core.timetools import Date

    # Initialize a `datetime` object...
    datetime_object = datetime(1996, 11, 1, 0, 0, 0)
    # ...and use it to initialise a `Date` object.
    date1 = Date(datetime_object)

Alternatively, one can use :class:`str` objects as initialization arguments,
which need to match one of the following format styles::

    # The `os` style without empty space and colon, which is applied in
    # text files and folder names:
    date2 = Date('1997_11_01_00_00_00')
    # The `iso` style, which is more legible and in accordance with the
    # international ISO norm:
    date2 = Date('1997.11.01 00:00:00')
    # The `din` style, which is more legible for users in countries where the
    # position of day and year are interchanged (DIN refers to a german norm):
    date2 = Date('01.11.1997 00:00:00')

:class:`Date` keeps the chosen style in mind and uses it for printing.  But
the user is also allowed to change it::

    # Print in accordance with the `iso` style...
    print(date2.string('iso'))
    # ...without changing the memorized `din` style:
    print(date2.style)
    # Alternatively, the style property can be set permanentely:
    date2.style = 'iso'
    print(date2)

It is allowed to abbreviate the input strings. Using the `iso` style as an
example::

    # The following three input arguments...
    test1 = Date('1996.11.01 00:00:00')
    test2 = Date('1996.11.01 00:00')
    test3 = Date('1996.11.01 00')
    test4 = Date('1996.11.01')
    # ...all lead to identical `Date` instances.
    print(test1, test2, test3, test4)

If :class:`Date` has not been initialized via a :class:`str` object and the
style property has not been set manually, the default style `iso` is selected.

One can change the year, month... of a :class:`Date` object via numbers::

    # Assign an integer...
    test4.year = 1997
    # ...or something that can be converted to an integer.
    test4.month = '10'
    print(test4)

One can ask for the actual water year, which depends on the selected
reference month::

    oct = Date('1996.10.01')
    nov = Date('1996.11.01')
    # Under the standard settings, the water year is assumed to start November.
    print(oct.wateryear, nov.wateryear)
    # Changing the reference month via one `Date` object affects all objects.
    test4.refmonth = 10
    print(oct.wateryear, nov.wateryear)
    test4.refmonth = 'November'
    print(oct.wateryear, nov.wateryear)


:class:`Period` objects can be directly initialized via
:class:`~datetime.timedelta` objects, e.g.::

    from datetime import timedelta
    from hydpy.core.timetools import Period

    # Initialize a `timedelta` object...
    timedelta_object = timedelta(1, 0)
    # ...and use it to initialise a `Period` object
    period = Period(timedelta_object)

Alternatively, one can initialize from :class:`str` objects.  These must
consist of some characters defining an integer value directly followed by
a single character defining the unit::

    # 30 seconds:
    period = Period('30s')
    # 5 minutes:
    period = Period('5m')
    # 6 hours:
    period = Period('6h')
    # 1 day:
    period = Period('1d')

:class:`Period` always determines the unit leading to the most legigible
print out::

    # Print using the unit leading to the smallest integer value:
    print(period)
    # Alternatively, the values of all time units are directly available as
    # `float` objects:
    print(period.days)
    print(period.hours)
    print(period.minutes)
    print(period.seconds)

If considered useful, logic and arithmetic operations are supported.
Some examples::

    # Determine the period length between two dates.
    wholeperiod = date2 - date1
    print(wholeperiod)
    # Determine, how often one period fits into the other.
    print(wholeperiod / period)
    # Get one sixths of period:
    print(period / 6)
    # But when trying to get one seventh of period:
    print(period / 7)
    # Double a period duration.
    period *= 2
    print(period)
    # Shift a date.
    date1 -= period
    # Note that the modulo operator returns a boolean value, indicating
    # whether the remainder is zero or not:
    # print(Period('1d') % Period('12h'))
    # print(Period('1d') % Period('13h'))
    # Following the same line of thinking, floor division leads to the
    # opposite results:
    # print(Period('1d') // Period('12h'))
    # print(Period('1d') // Period('13h'))
    # Compare dates or periods.
    print(date1 < date2)
    print(min(date1, date2))
    print(period == wholeperiod)
    # Operations on initialisation arguments are supported.
    print(date1 + '5m')
    print(period != '12h')

Note that :class:`Date` and :class:`Period` objects are mutable.  Use their
`copy` methods whenever this might lead to unintentional results::

    # A date example:
    date1 = Date('1996.11.01 00:00')
    date2 = date1
    date3 = date1.copy()
    date1.year = 1997
    print(date1, date2, date3)
    # A period example:
    period1 = Period('1h')
    period2 = period1
    period3 = period1.copy()
    period1 -= '2h'
    print(period1, period2, period3)



Timegrid and Timegrids
======================

In hydrological modelling, input (and output) data are usually only available
with a certain resolution, which also determines the possible resolution
of the actual simulation.  This is reflected by the class :class:`Timegrid`,
which represents the first and the last date of e.g. a simulation period as
well as the intermediate dates. A :class:`Timegrid` object is initialized
by defining its first date, its last date and its stepsize::

    from hydpy.core.timetools import Date, Period, Timegrid

    # Either pass the proper attributes directly...
    firstdate = Date('1996.11.01')
    lastdate = Date('1997.11.01')
    stepsize = Period('1d')
    timegrid_sim = Timegrid(firstdate, lastdate, stepsize)
    # ...or pass their initialization arguments:
    timegrid_sim = Timegrid('1996.11.01', '1997.11.01', '1d')

:class:`Timegrid` provides functionalities to ease and secure the handling
of dates in HydPy. Here some examples::

    # Retrieve a date via indexing, e.g. the second one:
    date = timegrid_sim[1]
    print(date)
    # Or the other way round, retrieve the index belonging to a date:
    print(timegrid_sim[date])
    # Indexing beyond the ranges of the actual time period is allowed:
    print(timegrid_sim[-366])
    print(timegrid_sim[timegrid_sim[date+'365d']])
    # Iterate through all time grid points (e.g. to print the first day of
    # each month):
    for date in timegrid_sim:
        if date.day == 1:
            print date

After doing some changes one should call the :func:`~Timegrid.verify` method::

    # `verify` keeps silent if everything seems to be alright...
    timegrid_sim.verify()
    # ...but raises an suitable exception otherwise:
    timegrid_sim.firstdate.minute = 30
    timegrid_sim.verify()

One can check two :class:`Timegrid` instances for equality::

    # Make a deep copy of the timegrid already existing.
    timegrid_test = timegrid_sim.copy()
    # Test for equality and non-equality.
    print(timegrid_sim == timegrid_test)
    print(timegrid_sim != timegrid_test)
    # Modify one date of the new timegrid.
    timegrid_test.firstdate += '1d'
    # Again, test for equality and non-equality.
    print(timegrid_sim == timegrid_test)
    print(timegrid_sim != timegrid_test)

Also, one can check if a date or even whole timegrid lies within a span
defined by a :class:`Timegrid` instance::

    # Define a long timegrid...
    timegrid_long = Timegrid('1996.11.01', '2006.11.01', '1d')
    # ...and check different dates for lying in the defined time period:
    print('1996.10.31' in timegrid_long)
    print('1996.11.01' in timegrid_long)
    print('1996.11.02' in timegrid_long)
    # For dates not alligned on the grid `False` is returned:
    print('1996.11.01 12:00' in timegrid_long)

    # Now define a timegrid containing only the first year of the long one:
    timegrid_short = Timegrid('1996.11.01', '1997.11.01', '1d')
    # Check which timegrid is contained by the other:
    print(timegrid_short in timegrid_long)
    print(timegrid_long in timegrid_short)
    # For timegrids with different stepsizes `False` is returned:
    timegrid_short.stepsize = Period('1h')
    print(timegrid_short in timegrid_long)


The HydPy framework distinguishes three `time frames`, one associated with the
input date available on disk (`data`), one associated, with the initialisation
period (`init`) and and one associated with the actual simulation period
(`sim`).  Each time frame is represented by a single :class:`Timegrid` object
and all together are handled by one class :class:`Timegrids` object.

There is usually only one :class:`Timegrids` object required within each
HydPy project.  It is automatically added to the module
:mod:`~hydpy.core.pub` during the initialization of a
:class:`~hydpy.core.hydpy.HydPy` object::

    from hydpy import HydPy
    from hydpy.core import pub

    hydpy = HydPy('tutorial_1')
    print(pub.timegrids)

Some examples on the usage of this :class:`Timegrids` instance::

    # Get the factor to convert `mm/stepsize` to m^3/s for an area of 36 km^2:
    print(pub.timegrids.qfactor(36.))
    # Get the index of the first values of the `data time frame` which belong
    # to the `initialisation time frame`.
    print(pub.timegrids.data[pub.timegrids.init.firstdate])
    # Or, as a similar example, get the index of the first values of the
    # `initialisation time frame` which belong to the `simulation time frame`.
    print(pub.timegrids.init[pub.timegrids.sim.firstdate])

Notice, that the latter index is zero.  This is due to the simulation time
frame beeing identical with the initialisation time frame, if not specified
otherwise in the main control file or by manually changing the simulation time
frame.

Each manual change should be followed by calling the
:func:`~Timegrids.verify` method, which calls the :func:`~Timegrid.verify`
method of the single :class:`Timegrid` instances and performs some additional
tests::

    # Postponing the `simulation time frame` one stepsize is fine...
    pub.timegrids.sim.firstdate += pub.timegrids.stepsize
    pub.timegrids.verify()
    # ...but shifting it outside the `initialisation time frame` or setting
    # it in  between the time grid points results in an error:
    pub.timegrids.sim.firstdate -= 2*pub.timegrids.stepsize
    pub.timegrids.verify()
    pub.timegrids.sim.firstdate += pub.timegrids.stepsize
    pub.timegrids.sim.firstdate.minute = 1
    pub.timegrids.verify()


To facilitate printing to configuration files, both classes :class:`Timegrid`
and :class:`Timegrids` allow for a extended canonical string representations
of their objects::

    # The string representation is generally formated with indentation.
    print(repr(pub.timegrids.data))
    print(repr(pub.timegrids))
    # The class specific `assignrepr` methods allow for inserting assignements.
    print(pub.timegrids.data.assignrepr('timegrid_data = '))
    print(pub.timegrids.assignrepr('timegrids_all = '))


Details
=======
"""

# import...
# ...from standard library
from __future__ import division, print_function
import datetime
import copy
import time
import calendar
import collections
# ...from third party packages
import numpy
# ...from HydPy
from hydpy.core import objecttools

# The import of `_strptime` is not thread save.  The following call of
# `strptime` is supposed to prevent possible problems arising from this bug.
time.strptime('1999', '%Y')


class Date(object):
    """Handles a single date.

    Argument:
        * date (:class:`~datetime.datetime` or :class:`str`): Initialization
          date.

    Attribute:
        * datetime (:class:`~datetime.datetime`): The core of :class:`Date`.
    """

    # These are the so far accepted date format strings.
    _formatstrings = {'os': '%Y_%m_%d_%H_%M_%S',
                      'iso': '%Y.%m.%d %H:%M:%S',
                      'din': '%d.%m.%Y %H:%M:%S'}
    # The first month of the hydrological year (e.g. November in Germany)
    _firstmonth_wateryear = 11

    def __init__(self, date):
        self.datetime = None
        self._style = None
        if isinstance(date, Date):
            self.datetime = date.datetime
        elif isinstance(date, datetime.datetime):
            if date.microsecond:
                raise ValueError('For `Date` instances, the microsecond must '
                                 'be `0`.  For the given `datetime` object, '
                                 'it is `%d` instead.' % date.microsecond)
            self.datetime = date
        elif isinstance(date, str):
            self._initfromstr(date)
        elif isinstance(date, TOY):
            self.datetime = datetime.datetime(2000,
                                              date.month, date.day, date.hour,
                                              date.minute, date.second)
        else:
            raise TypeError('The supplied argument must be either an '
                            'instance of `datetime.datetime` or of `str`.  '
                            'The given arguments type is %s.' % type(date))

    def _initfromstr(self, date):
        """Try to initialize `datetime` from the given :class:`str` instance.

        Arguments:
            * date (:class:`str`): Initialization date.
        """
        for (style, string) in self._formatstrings.items():
            for idx in range(4):
                try:
                    self.datetime = datetime.datetime.strptime(date, string)
                    self._style = style
                except ValueError:
                    string = string[:-3]
        if self.datetime is None:
            raise ValueError('Date could not be identified out of the given '
                             'string %s.  The available formats are %s.'
                             % (date, self._formatstrings))

    @classmethod
    def fromarray(cls, array):
        """Returns a :class:`Date` instance based on date information (year,
        month, day, hour, minute, second) stored as the first entries of the
        successive rows of a :class:`~numpy.ndarray` object."""
        intarray = numpy.array(array, dtype=int)
        for idx in range(1, array.ndim):
            intarray = intarray[:, 0]
        return cls(datetime.datetime(*intarray))

    def toarray(self):
        """Returns a 1-dimensional :mod:`numpy` :class:`~numpy.ndarray` with
        six entries defining the actual date (year, month, day, hour, minute,
        second)."""
        return numpy.array([self.year, self.month, self.day, self.hour,
                            self.minute, self.second], dtype=float)

    def _getrefmonth(self):
        """First month of the hydrological year. The default value is 11
        (November which is the german reference month). Setting it e.g. to 10
        (October is another common reference month many different countries)
        affects all :class:`Date` instances."""
        return Date._firstmonth_wateryear
    def _setrefmonth(self, value):
        try:
            Date._firstmonth_wateryear = int(value)
        except ValueError:
            string = str(value)[:3].lower()
            try:
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                          'jul', 'aug', 'sew', 'oct', 'nov', 'dec']
                Date._firstmonth_wateryear = months.index(string) + 1
            except ValueError:
                raise ValueError('The given value `%s` cannot be interpreted '
                                 'as a month. Supply e.g. a number between 1 '
                                 'and 12 or a month name instead.' % value)
    refmonth = property(_getrefmonth, _setrefmonth)

    def _getstyle(self):
        """Date format style to be applied in printing."""
        if self._style is None:
            return 'iso'
        else:
            return self._style
    def _setstyle(self, style):
        if style in self._formatstrings:
            self._style = style
        else:
            self._style = None
            raise KeyError('Date format style `%s` is not available.' % style)
    style = property(_getstyle, _setstyle)

    def _setthing(self, thing, value):
        """Convenience method for `_setyear`, `_setmonth`..."""
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError('Changing the %s of a `Date` instance is only '
                             'allowed via numbers, but the given value `%s` '
                             'is of type `%s` instead.'
                             % (thing, value, type(value)))
        kwargs = {}
        for unit in ('year', 'month', 'day', 'hour', 'minute', 'second'):
            kwargs[unit] = getattr(self, unit)
        kwargs[thing] = value
        self.datetime = datetime.datetime(**kwargs)

    def _getsecond(self):
        """The actual second."""
        return self.datetime.second
    def _setsecond(self, second):
        self._setthing('second', second)
    second = property(_getsecond, _setsecond)

    def _getminute(self):
        """The actual minute."""
        return self.datetime.minute
    def _setminute(self, minute):
        self._setthing('minute', minute)
    minute = property(_getminute, _setminute)

    def _gethour(self):
        """The actual hour."""
        return self.datetime.hour
    def _sethour(self, hour):
        self._setthing('hour', hour)
    hour = property(_gethour, _sethour)

    def _getday(self):
        """The actual day."""
        return self.datetime.day
    def _setday(self, day):
        self._setthing('day', day)
    day = property(_getday, _setday)

    def _getmonth(self):
        """The actual month."""
        return self.datetime.month
    def _setmonth(self, month):
        self._setthing('month', month)
    month = property(_getmonth, _setmonth)

    def _getyear(self):
        """The actual year."""
        return self.datetime.year
    def _setyear(self, year):
        self._setthing('year', year)
    year = property(_getyear, _setyear)

    def _getwateryear(self):
        """The actual hydrological year according selected reference month."""
        if self.month < self._firstmonth_wateryear:
            return self.year
        else:
            return self.year + 1
    wateryear = property(_getwateryear)

    @property
    def dayofyear(self):
        """Day of year as an integer value."""
        return self.datetime.timetuple().tm_yday

    @property
    def leapyear(self):
        """Return whether the actual date falls in a leap year or not."""
        year = self.year
        return (((year % 4) == 0) and
                (((year % 100) != 0) or ((year % 400) == 0)))

    def copy(self):
        """Returns a deep copy of the :class:`Date` instance."""
        return copy.deepcopy(self)

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
                raise Exception('Object `%s` of type `%s` can not be '
                                'substracted from a `Date` instance.'
                                % (str(other), type(other)))

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

    def string(self, style):
        """Returns a :class:`str` object representing the actual date in
        accordance with the given style.
        """
        retain = self.style
        try:
            self.style = style
            return str(self)
        finally:
            self.style = retain

    def __str__(self):
        return self.datetime.strftime(self._formatstrings[self.style])

    def __repr__(self):
        return 'Date("%s")' % str(self)

    def __dir__(self):
        return objecttools.dir_(self)


class Period(object):
    """Handles the length of a single time period.

    Argument:
        * period (:class:`~datetime.timedelta` or :class:`str`): Period length.

    Attribute:
        * datetime (:class:`~datetime.timedelta`): The core of :class:`Period`.

    """

    def __init__(self, period):
        self.timedelta = None
        self._unit = None
        if isinstance(period, Period):
            self.timedelta = period.timedelta
        elif isinstance(period, datetime.timedelta):
            if period.microseconds:
                raise ValueError('For `Period` instances, microseconds must '
                                 '`0`.  For the given `timedelta` object, it '
                                 'is `%d` instead.' % period.microseconds)
            self.timedelta = period
        elif isinstance(period, str):
            self._initfromstr(period)
        else:
            raise ValueError('The supplied argument must be either an '
                             'instance of `datetime.timedelta` or `str`.  '
                             'The given arguments type is %s.'
                             % objecttools.classname(period))

    def _initfromstr(self, period):
        """Try to initialize `timedelta` from the given :class:`str` instance.

        Arguments:
            * period (:class:`str`): Period length.
         """
        try:
            number = int(period[:-1])
        except ValueError:
            raise ValueError('All characters of the given period string, '
                             'except the last one which represents the unit, '
                             'need to define a whole decimal number.  Instead,'
                             ' these characters are `%s`.' % period[:-1])
        self._unit = period[-1]
        if self._unit not in ('d', 'h', 'm', 's'):
            raise ValueError('The last character of the given period string '
                             'needs to be either `d` (days), `h` (hours) or '
                             '`m` (minutes).  Instead, the last character is '
                             '`%s`.' % self._unit)
        if self._unit == 'd':
            self.timedelta = datetime.timedelta(number, 0)
        elif self._unit == 'h':
            self.timedelta = datetime.timedelta(0, number*3600)
        elif self._unit == 'm':
            self.timedelta = datetime.timedelta(0, number*60)
        elif self._unit == 's':
            self.timedelta = datetime.timedelta(0, number)

    @classmethod
    def fromseconds(cls, seconds):
        """Returns a :class:`Period` instance based on a given number of
        seconds.
        """
        try:
            seconds = int(seconds)
        except TypeError:
            seconds = int(seconds.flatten()[0])
        return cls(datetime.timedelta(0, int(seconds)))

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
            raise ValueError('The stepsize is not a multiple of one '
                             'second, which is not allowed.')
    unit = property(_guessunit)

    def _getseconds(self):
        """Period length in seconds."""
        return self.timedelta.total_seconds()
    seconds = property(_getseconds)

    def _getminutes(self):
        """Period length in minutes."""
        return self.seconds / 60
    minutes = property(_getminutes)

    def _gethours(self):
        """Period length in hours."""
        return self.minutes / 60
    hours = property(_gethours)

    def _getdays(self):
        """Period length in days."""
        return self.hours / 24
    days = property(_getdays)

    def copy(self):
        """Returns a deep copy of the :class:`Period` instance."""
        return copy.deepcopy(self)

    def __add__(self, other):
        try:
            new = Date(Date(other).datetime + self.timedelta)
            new.style = other.style
            return new
        except (TypeError, ValueError):
            try:
                return Period(self.timedelta + Period(other).timedelta)
            except (TypeError, ValueError):
                raise Exception('Object `%s` of type `%s` can not be '
                                'added to a `Period` instance.'
                                % (str(other), type(other)))

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
        if isinstance(other, int):
            return Period(self.timedelta // other)
        else:
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
        if self.unit == 'd':
            return '%dd' % self.days
        elif self.unit == 'h':
            return '%dh' % self.hours
        elif self.unit == 'm':
            return '%dm' % self.minutes
        elif self.unit == 's':
            return '%ds' % self.seconds

    def __repr__(self):
        return 'Period("%s")' % str(self)

    def __dir__(self):
        return objecttools.dir_(self)


class Timegrid(object):
    """Handle a time period defined by to dates and a step size in between."""

    def __init__(self, firstdate, lastdate, stepsize):
        self._firstdate = None
        self._lastdate = None
        self._stepsize = None
        self.firstdate = firstdate
        self.lastdate = lastdate
        self.stepsize = stepsize
        self.verify()

    def _getfirstdate(self):
        return self._firstdate
    def _setfirstdate(self, firstdate):
        self._firstdate = Date(firstdate)
    firstdate = property(_getfirstdate, _setfirstdate)

    def _getlastdate(self):
        return self._lastdate
    def _setlastdate(self, lastdate):
        self._lastdate = Date(lastdate)
    lastdate = property(_getlastdate, _setlastdate)

    def _getstepsize(self):
        return self._stepsize
    def _setstepsize(self, stepsize):
        self._stepsize = Period(stepsize)
    stepsize = property(_getstepsize, _setstepsize)

    @classmethod
    def fromarray(cls, array):
        """Returns a :class:`Timegrid` instance based on two date and one
        period information stored in the first 13 rows of a
        :class:`~numpy.ndarray` object.
        """
        try:
            return cls(firstdate=Date.fromarray(array[:6]),
                       lastdate=Date.fromarray(array[6:12]),
                       stepsize=Period.fromseconds(array[12]))
        except IndexError:
            raise IndexError('To define a Timegrid instance via an array, 13 '
                             'numbers are required.  However, the given array '
                             'consist of %d entries/rows only.' % len(array))

    def toarray(self):
        """Returns a 1-dimensional :mod:`numpy` :class:`~numpy.ndarray` with
        thirteen entries first defining the start date, secondly defining the
        end date and thirdly the step size."""
        values = numpy.empty(13, dtype=float)
        values[:6] = self.firstdate.toarray()
        values[6:12] = self.lastdate.toarray()
        values[12] = self.stepsize.seconds
        return values

    def verify(self):
        """Raise an :class:`~exceptions.ValueError` if the dates or the
        step size of the time frame are inconsistent.
        """
        if self.firstdate >= self.lastdate:
            raise ValueError('Unplausible timegrid. The first given '
                             'date %s, the second given date is %s. '
                             % (self.firstdate, self.lastdate))
        if (self.lastdate-self.firstdate) % self.stepsize:
            raise ValueError('Unplausible timegrid. The period span '
                             'between the given dates %s and %s is not '
                             'a multiple of the given step size %s.' %
                             (self.firstdate, self.lastdate, self.stepsize))

    def copy(self):
        """Returns a deep copy of the :class:`Timegrid` instance."""
        return copy.deepcopy(self)

    def __len__(self):
        return int((self.lastdate-self.firstdate) / self.stepsize)

    def __getitem__(self, key):
        if isinstance(key, int):
            return Date(self.firstdate + key*self.stepsize)
        else:
            key = Date(key)
            index = (key-self.firstdate) / self.stepsize
            if index % 1.:
                raise ValueError('The given date `%s` is not properly '
                                 'alligned on the indexed timegrid.' % key)
            else:
                return int(index)

    def __iter__(self):
        date = self.firstdate.copy()
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
        if isinstance(other, Timegrid):
            return self._containstimegrid(other)
        else:
            return self._containsdate(other)

    def __eq__(self, other):
        return ((self.firstdate == other.firstdate) and
                (self.lastdate == other.lastdate) and
                (self.stepsize == other.stepsize))

    def __ne__(self, other):
        return ((self.firstdate != other.firstdate) or
                (self.lastdate != other.lastdate) or
                (self.stepsize != other.stepsize))

    def __str__(self):
        return ('from %s to %s in %s steps'
                % (self.firstdate, self.lastdate, self.stepsize))

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        """Return a :func:`repr` string with an prefixed assignement.

        Argument:
            * prefix(:class:`str`): Usually something like 'x = '.
        """
        skip = len(prefix) + 9
        blanks = ' ' * skip
        lines = ['%sTimegrid("%s",' % (prefix, str(self.firstdate)),
                 '%s"%s",' % (blanks, str(self.lastdate)),
                 '%s"%s")' % (blanks, str(self.stepsize))]
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class _Timegrids(object):
    """Handle all :class:`Timegrid` instances of a HydPy application.

    Arguments:
        * info (:class:`dict`): Dictionary containing initialisation
          information, usually defined within the main project file.

    Attributes:
        * data (:class:`Timegrid`): For the available data stored on disk.
        * init (:class:`Timegrid`): For the initialisation period.
        * sim (:class:`Timegrid`): For the simulation period.
    """

    def __init__(self, info):
        args = []
        for key in ('date_startdata', 'date_enddata', 'timestep'):
            try:
                args.append(info[key])
            except KeyError:
                raise KeyError('The information `%s` is missing. Usually, '
                               'it is defined within the main project file.'
                               % key)
        self.data = Timegrid(*args)
        self.init = Timegrid(info.get('date_startinit',
                                      self.data.firstdate.copy()),
                             info.get('date_endinit',
                                      self.data.lastdate.copy()),
                             self.data.stepsize)
        self.sim = Timegrid(info.get('date_startsim',
                                     self.init.firstdate.copy()),
                            info.get('date_endsim',
                                     self.init.lastdate.copy()),
                            self.init.stepsize)
        self.verify()

    def _getstepsize(self):
        """Stepsize of all handled :class:`Timegrid` objects."""
        return self.data.stepsize
    def _setstepsize(self, stepsize):
        stepsize = Period(stepsize)
        for (name, timegrid) in self:
            timegrid.stepsize = stepsize
    stepsize = property(_getstepsize, _setstepsize)

    def verify(self):
        """Raise an :class:`~exceptions.RuntimeError` it the different
        time grids are inconsistent.
        """
        if self.data.firstdate > self.init.firstdate:
            raise RuntimeError('The first date of the data period (%s) must '
                               'not be later than the first date of the '
                               'initialisation period  (%s).'
                               % (self.data.firstdate, self.init.firstdate))
        if self.data.lastdate < self.init.lastdate:
            raise RuntimeError('The last date of the data period (%s) must '
                               'not be earlier than the last date of the '
                               'initialisation period  (%s).'
                               % (self.data.lastdate, self.init.lastdate))
        if self.init.firstdate > self.sim.firstdate:
            raise RuntimeError('The first date of the initialisation period '
                               '(%s) must not be later than the first date '
                               'of the simulation period  (%s).'
                               % (self.init.firstdate, self.sim.firstdate))
        if self.init.lastdate < self.sim.lastdate:
            raise RuntimeError('The last date of the initialisation period '
                               '(%s) must not be earlier than the last date '
                               'of the simulation period  (%s).'
                               % (self.init.lastdate, self.sim.lastdate))
        if self.data.stepsize != self.init.stepsize:
            raise RuntimeError('The data stepsize (%s) must be identical with '
                               'the initialisation stepsize (%s).'
                               % (self.data.stepsize, self.init.stepsize))
        if self.init.stepsize != self.sim.stepsize:
            raise RuntimeError('The initialization stepsize (%s) must be '
                               'identical with the simulation stepsize (%s).'
                               % (self.init.stepsize, self.sim.stepsize))
        if self.data[self.init.firstdate] % 1:
            raise RuntimeError('The initialization time grid is not properly '
                               'alligned on the data time grid.')
        if self.init[self.sim.firstdate] % 1:
            raise RuntimeError('The simulation time grid is not properly '
                               'alligned on the initialization time grid.')

    def qfactor(self, area):
        """Return the factor for converting `mm/stepsize` to `m^3/s`.

        Argument:
            * area (:class:`float`): Reference area, which must be given in
              the unit `km^2`.
        """
        return area * 1000. / self.stepsize.seconds

    def parfactor(self, stepsize):
        """Return the factor for converting parameter to simulation step size.

        Argument:
            * stepsize (:class:`Period` or an suitable initialization argument
              thereof): Time interval, to which the parameter values refer.
        """
        return self.stepsize / Period(stepsize)

    def copy(self):
        """Returns a deep copy of the :class:`Timegrids` instance."""
        return copy.deepcopy(self)

    def __iter__(self):
        for (name, timegrid) in dict(self).items():
            yield (name, timegrid)

    def __str__(self):
        return 'All timegrids of the current project.'

    def __repr__(self):
        dic = {'timestep': self.sim.stepsize,
               'date_startdata': self.data.firstdate,
               'date_enddata': self.data.lastdate,
               'date_startinit': self.init.firstdate,
               'date_endinit': self.init.lastdate,
               'date_startsim': self.sim.firstdate,
               'date_endsim': self.sim.lastdate}
        return 'Timegrids(%s)' % dic.__repr__()

    def __dir__(self):
        return objecttools.dir_(self)


class Timegrids(object):
    """Handle all :class:`Timegrid` instances of a HydPy application.

    Arguments and Attributes:
        * data (:class:`Timegrid`): For the available data stored on disk.
        * init (:class:`Timegrid`, optional): For the initialisation
          period.  If not supplied, the specifications of the `data`
          :class:`Timegrid` are applied.
        * sim (:class:`Timegrid`, optional): For the simulation period.
          If not supplied, the specifications of the `init` :class:`Timegrid`
          are applied.
    """

    def __init__(self, data, init=None, sim=None):
        self.data = data
        if init is None:
            self.init = self.data.copy()
        else:
            self.init = init
        if sim is None:
            self.sim = self.init.copy()
        else:
            self.sim = sim
        self.verify()

    def _getstepsize(self):
        """Stepsize of all handled :class:`Timegrid` objects."""
        return self.data.stepsize
    def _setstepsize(self, stepsize):
        stepsize = Period(stepsize)
        for (name, timegrid) in self:
            timegrid.stepsize = stepsize
    stepsize = property(_getstepsize, _setstepsize)

    def verify(self):
        """Raise an :class:`~exceptions.RuntimeError` it the different
        time grids are inconsistent.
        """
        if self.data.firstdate > self.init.firstdate:
            raise RuntimeError('The first date of the data period (%s) must '
                               'not be later than the first date of the '
                               'initialisation period  (%s).'
                               % (self.data.firstdate,
                                  self.init.firstdate))
        if self.data.lastdate < self.init.lastdate:
            raise RuntimeError('The last date of the data period (%s) must '
                               'not be earlier than the last date of the '
                               'initialisation period  (%s).'
                               % (self.data.lastdate,
                                  self.init.lastdate))
        if self.init.firstdate > self.sim.firstdate:
            raise RuntimeError('The first date of the initialisation period '
                               '(%s) must not be later than the first date '
                               'of the simulation period  (%s).'
                               % (self.init.firstdate,
                                  self.sim.firstdate))
        if self.init.lastdate < self.sim.lastdate:
            raise RuntimeError('The last date of the initialisation period '
                               '(%s) must not be earlier than the last date '
                               'of the simulation period  (%s).'
                               % (self.init.lastdate,
                                  self.sim.lastdate))
        if self.data.stepsize != self.init.stepsize:
            raise RuntimeError('The data stepsize (%s) must be identical with '
                               'the initialisation stepsize (%s).'
                               % (self.data.stepsize,
                                  self.init.stepsize))
        if self.init.stepsize != self.sim.stepsize:
            raise RuntimeError('The initialization stepsize (%s) must be '
                               'identical with the simulation stepsize (%s).'
                               % (self.init.stepsize,
                                  self.sim.stepsize))
        if self.data[self.init.firstdate] % 1:
            raise RuntimeError('The initialization time grid is not properly '
                               'alligned on the data time grid.')
        if self.init[self.sim.firstdate] % 1:
            raise RuntimeError('The simulation time grid is not properly '
                               'alligned on the initialization time grid.')

    def qfactor(self, area):
        """Return the factor for converting `mm/stepsize` to `m^3/s`.

        Argument:
            * area (:class:`float`): Reference area, which must be given in
              the unit `km^2`.
        """
        return area * 1000. / self.stepsize.seconds

    def parfactor(self, stepsize):
        """Return the factor for converting parameter to simulation step size.

        Argument:
            * stepsize (:class:`Period` or an suitable initialization argument
              thereof): Time interval, to which the parameter values refer.
        """
        return self.stepsize / Period(stepsize)

    def copy(self):
        """Returns a deep copy of the :class:`Timegrids` instance."""
        return copy.deepcopy(self)

    def __iter__(self):
        for (name, timegrid) in dict(self).items():
            yield (name, timegrid)

    def __str__(self):
        return 'All timegrids of the actual HydPy project.'

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        """Return a :func:`repr` string with an prefixed assignement.

        Argument:
            * prefix(:class:`str`): Usually something like 'x = '.
        """
        caller = 'NewTimegrids('
        blanks = ' ' * (len(prefix) + len(caller))
        prefix = '%s%sdata=' % (prefix, caller)
        lines = ['%s,' % self.data.assignrepr(prefix)]
        if self.init != self.data:
            prefix = '%sinit=' % blanks
            lines.append('%s,' % self.init.assignrepr(prefix))
        if self.sim != self.init:
            prefix = '%ssim=' % blanks
            lines.append('%s,' % self.init.assignrepr(prefix))
        lines[-1] = lines[-1][:-1] + ')'
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class TOY(object):
    """Time of year handler.

    :class:`TOY` objects are used to define certain things that are true for
    a certain time point in each year.  The smallest supported time unit is
    seconds.

    Normally, for initialization a string is passed, defining the month, the
    day, the hour, the minute and the second in the order they are mentioned,
    seperated by a single underscore:

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
    applying :class:`str` on :class:`TOY` instances:

    >>> str(TOY('something_3_13_23_33_2'))
    'toy_3_13_23_33_2'

    Alternatively, one can use a :class:`Date` object as a initialization
    argument, ommitting the year:

    >>> TOY(Date('2001.02.03 04:05:06'))
    TOY('2_3_4_5_6')

    It is only allowed to modify the mentioned properties, not to define new
    ones:

    >>> t.microsecond = 53
    Traceback (most recent call last):
    ...
    AttributeError: TOY (time of year) objects only allow to set the properties month, day, hour, minute or second, but `microsecond` is given.

    It is allowed to pass objects that can be converted to integers:

    >>> t.second = '53'
    >>> t.second
    53

    If the passed object cannot be converted properly, an exception is raised:

    >>> t.second = 'fiftythree'
    Traceback (most recent call last):
    ...
    ValueError: For TOY (time of year) objects, all properties must be of type `int`, but the value `fiftythree` of type `str` given for property `second` cannot be converted to `int`.

    Additionally, given values are checked to lie within a suitable range:

    >>> t.second = 60
    Traceback (most recent call last):
    ...
    ValueError: The value of property `second` of TOY (time of year) objects must lie within the range `(0, 59)`, but the given value is `60`.

    Note that the allowed values for `month` and `day` depend on each other,
    which is why the order one defines them might be of importance.  So, if
    January is predefined, one can set day to the 31th:

    >>> t.month = 1
    >>> t.day = 31

    But afterwards one cannot directly change the month to February:

    >>> t.month = 2
    Traceback (most recent call last):
    ...
    ValueError: The value of property `month` of the actual TOY (time of year) object must not be the given value `2`, as the day has already been set to `31`.

    Hence first set `day` to a smaller value and then change `month`:

    >>> t.day = 28
    >>> t.month = 2

    For February it is important to note, that the 29th is generally
    disallowed:

    >>> t.day = 29
    Traceback (most recent call last):
    ...
    ValueError: The value of property `day` of the actual TOY (time of year) object must lie within the range `(1, 28)`, as the month has already been set to `2`, but the given value is `29`.

    It is possible to compare two :class:`TOY` instances:

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

    Subtracting two :class:`TOY` object gives their time difference in seconds:

    >>> TOY('1_1_0_3_0') - TOY('1_1_0_1_30')
    90

    Instead of negative values, it is always assumed that the first
    :class:`TOY` object lies within the future (eventually within the
    subsequent year):

    >>> TOY('1_1_0_1_30') - TOY('12_31_23_58_30')
    180
    """
    _PROPERTIES = collections.OrderedDict((('month', (1, 12)),
                                           ('day', (1, 31)),
                                           ('hour', (0, 23)),
                                           ('minute', (0, 59)),
                                           ('second', (0, 59))))
    _STARTDATE = Date('01.01.2000')
    _ENDDATE = Date('01.01.2001')

    def __init__(self, value=''):
        if isinstance(value, Date):
            for name in self._PROPERTIES.keys():
                self.__dict__[name] = getattr(value, name)
        else:
            for name in self._PROPERTIES.keys():
                self.__dict__[name] = None
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
                    objecttools.augmentexcmessage(
                        'While trying to retrieve the %s for TOY (time of '
                        'year) object based on the string `%s`'
                        % (prop, value))

    def __setattr__(self, name, value):
        if name not in self._PROPERTIES:
            keys = list(self._PROPERTIES.keys())
            props = ' or '.join((', '.join(keys[:-1]), keys[-1]))
            raise AttributeError('TOY (time of year) objects only allow to '
                                 'set the properties %s, but `%s` is given.'
                                 % (props, name))
        try:
            value = int(value)
        except ValueError:
            raise ValueError('For TOY (time of year) objects, all properties '
                             'must be of type `int`, but the value `%s` of '
                             'type `%s` given for property `%s` cannot be '
                             'converted to `int`.'
                             % (value, objecttools.classname(value), name))
        if (name == 'day') and (self.month is not None):
            bounds = (1, calendar.monthrange(1999, self.month)[1])
            if not (bounds[0] <= value <= bounds[1]):
                raise ValueError('The value of property `day` of the actual '
                                 'TOY (time of year) object must lie within '
                                 'the range `%s`, as the month has already '
                                 'been set to `%s`, but the given value is '
                                 '`%s`.' % (bounds, self.month, value))
        elif (name == 'month') and (self.day is not None):
            bounds = (1, calendar.monthrange(2000, value)[1])
            if not (bounds[0] <= self.day <= bounds[1]):
                raise ValueError('The value of property `month` of the actual '
                                 'TOY (time of year) object must not be the '
                                 'given value `%s`, as the day has already '
                                 'been set to `%s`.' % (value, self.day))
        else:
            bounds = self._PROPERTIES[name]
            if not (bounds[0] <= value <= bounds[1]):
                raise ValueError('The value of property `%s` of TOY (time of '
                                 'year) objects must lie within the range '
                                 '`%s`, but the given value is `%s`.'
                                 % (name, bounds, value))
        object.__setattr__(self, name, value)

    @property
    def passed_seconds(self):
        """Amount of time passed in seconds since the beginning of the year.

        In the first example, the year is only one minute and thirty seconds
        old:

        >>> from hydpy.core.timetools import TOY
        >>> TOY('1_1_0_1_30').passed_seconds
        90

        The second example shows that the 29th February is generally included:

        >>> TOY('3').passed_seconds
        5184000
        """
        return int((Date(self).datetime -
                    self._STARTDATE.datetime).total_seconds())

    @property
    def left_seconds(self):
        """Remaining part of the year in seconds.

        In the first example, only one minute and thirty seconds of the year
        remain:

        >>> from hydpy.core.timetools import TOY
        >>> TOY('12_31_23_58_30').left_seconds
        90

        The second example shows that the 29th February is generally included:

        >>> TOY('2').left_seconds
        28944000
        """
        return int((self._ENDDATE.datetime -
                    Date(self).datetime).total_seconds())

    def __lt__(self, other):
        return self.passed_seconds < other.passed_seconds

    def __le__(self, other):
        return self.passed_seconds <= other.passed_seconds

    def __eq__(self, other):
        return self.passed_seconds == other.passed_seconds

    def __ne__(self, other):
        return self.passed_seconds != other.passed_seconds

    def __gt__(self, other):
        return self.passed_seconds > other.passed_seconds

    def __ge__(self, other):
        return self.passed_seconds >= other.passed_seconds

    def __sub__(self, other):
        if self >= other:
            return self.passed_seconds - other.passed_seconds
        else:
            return self.passed_seconds + other.left_seconds

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return "toy_%s" % '_'.join(str(getattr(self, prop)) for prop
                                   in self._PROPERTIES.keys())

    def __repr__(self):
        return "TOY('%s')" % '_'.join(str(getattr(self, prop)) for prop
                                      in self._PROPERTIES.keys())

    __dir__ = objecttools.dir_
