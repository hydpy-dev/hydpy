# -*- coding: utf-8 -*-
"""This module implements tools to determine time related indices."""
# import...
# ...from standard library
from __future__ import division, print_function
import copy
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import autodoctools


class Indexer(object):
    """Handles arrays containing indexes.

    One can specify the index arrays manually, but usually they are
    determined automatically based on the |Timegrids| object made
    available through module |pub|.
    """
    def __init__(self):
        self._monthofyear = None
        self._monthofyear_hash = hash(None)
        self._dayofyear = None
        self._dayofyear_hash = hash(None)
        self._timeofyear = None
        self._timeofyear_hash = hash(None)

    def _getmonthofyear(self):
        """Month of the year index (January = 0...)."""
        from hydpy.pub import timegrids
        if ((self._monthofyear is None) or
                (hash(timegrids) != self._monthofyear_hash)):
            def monthofyear(date):
                return date.month-1
            self._monthofyear = self._calcidxs(monthofyear)
            self._monthofyear_hash = hash(timegrids)
        return self._monthofyear

    def _setmonthofyear(self, values):
        from hydpy.pub import timegrids
        self._monthofyear = self._convertandtest(values, 'monthofyear')
        self._monthofyear_hash = hash(timegrids)

    def _delmonthofyear(self):
        self._monthofyear = None

    monthofyear = property(_getmonthofyear, _setmonthofyear, _delmonthofyear)

    def _getdayofyear(self):
        """Day of the year index (the first of January = 0...).

        For reasons of consistency between leap years and non-leap years,
        assuming a daily time step, index 59 is always associated with the
        29th of February.  Hence, it is missing in non-leap years:

        >>> from hydpy import pub
        >>> from hydpy import Timegrids, Timegrid
        >>> from hydpy.core.indextools import Indexer
        >>> pub.timegrids = Timegrids(Timegrid('27.02.2004',
        ...                                    '3.03.2004',
        ...                                    '1d'))
        >>> Indexer().dayofyear
        array([57, 58, 59, 60, 61])
        >>> pub.timegrids = Timegrids(Timegrid('27.02.2005',
        ...                                    '3.03.2005',
        ...                                    '1d'))
        >>> Indexer().dayofyear
        array([57, 58, 60, 61])
        """
        if ((self._dayofyear is None) or
                (hash(pub.timegrids) != self._dayofyear_hash)):
            def dayofyear(date):
                return (date.dayofyear-1 +
                        ((date.month > 2) and (not date.leapyear)))
            self._dayofyear = self._calcidxs(dayofyear)
            self._dayofyear_hash = hash(pub.timegrids)
        return self._dayofyear

    def _setdayofyear(self, values):
        self._dayofyear = self._convertandtest(values, 'dayofyear')
        self._dayofyear_hash = hash(pub.timegrids)

    def _deldayofyear(self):
        self._dayofyear = None

    dayofyear = property(_getdayofyear, _setdayofyear, _deldayofyear)

    def _gettimeofyear(self):
        """Time of the year index (first simulation step of each year = 0...).

        The property |Indexer.timeofyear| is best explained through
        comparing it with property |Indexer.dayofyear|:

        Let us reconsider one of the examples of the documentation on
        property |Indexer.dayofyear|:

        >>> from hydpy import pub
        >>> from hydpy import Timegrids, Timegrid
        >>> from hydpy.core.indextools import Indexer
        >>> pub.timegrids = Timegrids(Timegrid('27.02.2005',
        ...                                    '3.03.2005',
        ...                                    '1d'))

        Due to the simulation stepsize being one day, the index arrays
        calculated by both properties are identical:

        >>> Indexer().dayofyear
        array([57, 58, 60, 61])
        >>> Indexer().timeofyear
        array([57, 58, 60, 61])

        In the next example the step size is halved:

        >>> pub.timegrids = Timegrids(Timegrid('27.02.2005',
        ...                                    '3.03.2005',
        ...                                    '12h'))

        Now the there a generally two subsequent simulation steps associated
        with the same day:

        >>> Indexer().dayofyear
        array([57, 57, 58, 58, 60, 60, 61, 61])

        However, the `timeofyear` array gives the index of the
        respective simulation steps of the actual year:

        >>> Indexer().timeofyear
        array([114, 115, 116, 117, 120, 121, 122, 123])

        Note the gap in the returned index array due to 2005 being not a
        leap year.
        """
        if ((self._timeofyear is None) or
                (hash(pub.timegrids) != self._timeofyear_hash)):
            if pub.timegrids is None:
                refgrid = None
            else:
                refgrid = timetools.Timegrid(timetools.Date('2000.01.01'),
                                             timetools.Date('2001.01.01'),
                                             pub.timegrids.stepsize)

            def timeofyear(date):
                date = copy.deepcopy(date)
                date.year = 2000
                return refgrid[date]

            self._timeofyear = self._calcidxs(timeofyear)
            self._timeofyear_hash = hash(pub.timegrids)
        return self._timeofyear

    def _settimeofyear(self, values):
        self._timeofyear = self._convertandtest(values, 'timeofyear')
        self._timeofyear_hash = hash(pub.timegrids)

    def _deltimeofyear(self):
        self._timeofyear = None

    timeofyear = property(_gettimeofyear, _settimeofyear, _deltimeofyear)

    def _convertandtest(self, values, name):
        """Try to convert the given values to a |numpy| |numpy.ndarray| and
        check if it is plausible.  If so, return the array, other raise
        a |ValueError| or re-raise a |numpy| specific exception.
        """
        try:
            array = numpy.array(values, dtype=int)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to assign a new `%s` '
                'index array to an Indexer object'
                % name)
        if array.ndim != 1:
            raise ValueError(
                'The `%s` index array of an Indexer object must be '
                '1-dimensional.  However, the given value has interpreted '
                'as a %d-dimensional object.'
                % (name, array.ndim))
        if pub.timegrids is not None:
            if len(array) != len(pub.timegrids.init):
                raise ValueError(
                    'The %s` index array of an Indexer object must have a '
                    'number of entries fitting to the initialization time '
                    'period precisely.  However, the given value has been '
                    'interpreted to be of length %d and the length of the '
                    'Timegrid object representing the actual initialization '
                    'time period is %d.'
                    % (name, len(array), len(pub.timegrids.init)))
        return array

    def _calcidxs(self, func):
        """Return the required indexes based on the given lambda function
        and the |Timegrids| object handled by module |pub|.  Raise a
        |RuntimeError| if the latter is not available.
        """
        if pub.timegrids is None:
            raise RuntimeError(
                'An Indexer object has been asked for an %s array.  Such an '
                'array has neither been determined yet nor can it be '
                'determined automatically at the moment.   Either define an '
                '%s array manually and pass it to the Indexer object, or make '
                'a proper Timegrids object available within the pub module.  '
                'In usual HydPy applications, the latter is done '
                'automatically.'
                % (func.__name__, func.__name__))
        idxs = numpy.empty(len(pub.timegrids.init), dtype=int)
        for (jdx, date) in enumerate(pub.timegrids.init):
            idxs[jdx] = func(date)
        return idxs


autodoctools.autodoc_module()
