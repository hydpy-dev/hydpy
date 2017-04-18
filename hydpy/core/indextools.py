# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import objecttools
#from hydpy.pub import ... (actual import commands moved to
# different functions below to avoid circular dependencies)

class Indexer(object):
    """Handles arrays containing indexes.  One can specify these array indexes
    manually, but usually they are determined automatically based on the
    :class:`~hydpy.core.timetools.Timegrids` object made available through
    module :mod:`~hydpy.pub`.
    """
    def __init__(self):
        self._monthofyear = None
        self._monthofyear_hash = hash(None)
        self._dayofyear = None
        self._dayofyear_hash = hash(None)

    def _getmonthofyear(self):
        """Month of the year index (January = 0...)."""
        from hydpy.pub import timegrids
        if ((self._monthofyear is None) or
            (hash(timegrids) != self._monthofyear_hash)):
            self._monthofyear = self._calcidxs(lambda date: date.month-1,
                                               'monthofyear')
            self._monthofyear_hash =  hash(timegrids)
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
        >>> from hydpy.core.timetools import Timegrids, Timegrid
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
        from hydpy.pub import timegrids
        if ((self._dayofyear is None) or
            (hash(timegrids) != self._dayofyear_hash)):
            func = lambda date: (date.dayofyear - 1 +
                                 ((date.month > 2) and (not date.leapyear)))
            self._dayofyear = self._calcidxs(func, 'dayofyear')
            self._dayofyear_hash =  hash(timegrids)
        return self._dayofyear
    def _setdayofyear(self, values):
        from hydpy.pub import timegrids
        self._dayofyear = self._convertandtest(values, 'dayofyear')
        self._dayofyear_hash = hash(timegrids)
    def _deldayofyear(self):
        self._dayofyear = None
    dayofyear = property(_getdayofyear, _setdayofyear, _deldayofyear)

    def _convertandtest(self, values, name):
        """Try to convert the given values to a :mod:`numpy`
        :class:`~numpy.ndarrray` and check if it is plausible.  If so, return
        the array, other raise a :class:`~exceptions.ValueError` or re-raise a
        :mod:`numpy` specific exception.
        """
        from hydpy.pub import timegrids
        try:
            array = numpy.array(values, dtype=int)
        except BaseException:
            objecttools.augmentexcmessage('While trying to assign a new `%s` '
                                          'index array to an Indexer object'
                                          % name)
        if array.ndim != 1:
            raise ValueError('The `%s` index array of an Indexer object must '
                             'be 1-dimensional.  However, the given value has '
                             'interpreted as a %d-dimensional object.'
                             % (name, array.ndim))
        if timegrids is not None:
            if len(array) != len(timegrids.init):
                raise ValueError('The %s` index array of an Indexer object '
                                 'must have a number of entries fitting to '
                                 'the initialization time period precisely.  '
                                 'However, the given value has been '
                                 'interpreted to be of length %d and the '
                                 'length of the Timegrid object representing '
                                 'the actual initialization time period is %d.'
                                 % (name, len(array), len(timegrids.init)))
        return array

    def _calcidxs(self, func, name):
        """Return the required indexes based on the given lambda function and
        the :class:`~hydpy.core.timetools.Timegrids` object handled by module
        :mod:`~hydpy.pub`.  Raise a :class:`~exceptions.RuntimeError` if the
        latter is not available.
        """
        from hydpy.pub import timegrids
        if timegrids is None:
            raise RuntimeError('An Indexer object has been asked for an '
                               '%s array.  Such an array has neither been '
                               'determined yet nor can it be determined '
                               'automatically at the moment.   Either '
                               'define an %s array manually and pass it to '
                               'the Indexer object, or make a proper '
                               'Timegrids object available within the pub '
                               'module.  In usual HydPy applications, the '
                               'latter is done automatically.'
                               % (name, name))
        idxs = numpy.empty(len(timegrids.init), dtype=int)
        for (jdx, date) in enumerate(timegrids.init):
            idxs[jdx] = func(date)
        return idxs




