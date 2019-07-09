# -*- coding: utf-8 -*-
"""This module implements tools to determine time related indices."""
# import...
# ...from standard library
import copy
# ...from site-packages
import numpy
# ...from HydPy
import hydpy
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import timetools


class IndexerProperty(propertytools.BaseProperty):
    """Property for handling time related indices.

    Some models (e.g. |lland_v1|) require time related indice values.
    |IndexerProperty| provides some caching functionalities, to avoid
    recalculating the same indices for different model instances over
    and over.  We illustrate this by taking |Indexer.monthofyear| as
    an example.

    For efficiency, repeated querying of |Indexer.monthofyear| returns
    the same |numpy| |numpy.array| object:

    >>> from hydpy import pub
    >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
    >>> monthofyear = pub.indexer.monthofyear
    >>> monthofyear
    array([1, 1, 1, 2, 2])
    >>> pub.indexer.monthofyear
    array([1, 1, 1, 2, 2])
    >>> pub.indexer.monthofyear is monthofyear
    True

    When the |Timegrids| object handled by module |pub| changes,
    |IndexerProperty| calculates and returns a new index array:

    >>> pub.timegrids.init.firstdate += '1d'
    >>> pub.indexer.monthofyear
    array([1, 1, 2, 2])
    >>> pub.indexer.monthofyear is monthofyear
    False

    When in doubt, you can delete can manually delete the cached
    |numpy| |numpy.ndarray| and will receive a freshly calculated
    index array afterwards:

    >>> monthofyear = pub.indexer.monthofyear
    >>> pub.indexer.monthofyear is monthofyear
    True
    >>> del pub.indexer.monthofyear
    >>> pub.indexer.monthofyear
    array([1, 1, 2, 2])
    >>> pub.indexer.monthofyear is monthofyear
    False

    You are allowed to define alternative values manually, which
    seems advisable only during testing:

    >>> pub.indexer.monthofyear = [0, 1, 2, 3]
    >>> pub.indexer.monthofyear
    array([0, 1, 2, 3])
    >>> pub.timegrids.init.firstdate -= '1d'
    >>> pub.indexer.monthofyear
    array([1, 1, 1, 2, 2])
    """

    def __init__(self, fget):
        self.fget = fget
        self.fset = self._fset
        self.fdel = self._fdel
        self.__doc__ = fget.__doc__
        self.values = None
        self.timegrids = None

    def call_fget(self, obj) -> numpy.ndarray:
        timegrids = hydpy.pub.get('timegrids')
        if (self.values is None) or (self.timegrids != timegrids):
            self.values = self._calcidxs(self.fget(obj))
            self.timegrids = copy.deepcopy(timegrids)
        return self.values

    def call_fset(self, obj, value):
        self._fset(value)

    def _fset(self, values):
        self.values = self._convertandtest(values, self.name)
        self.timegrids = copy.deepcopy(hydpy.pub.get('timegrids'))

    def call_fdel(self, obj):
        self.fdel()

    def _fdel(self):
        self.values = None
        self.timegrids = None

    @staticmethod
    def _convertandtest(values, name):
        """Try to convert the given values to a |numpy| |numpy.ndarray| and
        check if it is plausible.  If so, return the array, otherwise raise
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
        timegrids = hydpy.pub.get('timegrids')
        if timegrids is not None:
            if len(array) != len(timegrids.init):
                raise ValueError(
                    'The %s` index array of an Indexer object must have a '
                    'number of entries fitting to the initialization time '
                    'period precisely.  However, the given value has been '
                    'interpreted to be of length %d and the length of the '
                    'Timegrid object representing the actual initialization '
                    'time period is %d.'
                    % (name, len(array), len(timegrids.init)))
        return array

    @staticmethod
    def _calcidxs(func):
        """Return the required indexes based on the given lambda function
        and the |Timegrids| object handled by module |pub|.  Raise a
        |RuntimeError| if the latter is not available.
        """
        timegrids = hydpy.pub.get('timegrids')
        if timegrids is None:
            raise RuntimeError(
                'An Indexer object has been asked for an %s array.  Such an '
                'array has neither been determined yet nor can it be '
                'determined automatically at the moment.   Either define an '
                '%s array manually and pass it to the Indexer object, or make '
                'a proper Timegrids object available within the pub module.  '
                'In usual HydPy applications, the latter is done '
                'automatically.'
                % (func.__name__, func.__name__))
        idxs = numpy.empty(len(timegrids.init), dtype=int)
        for jdx, date in enumerate(hydpy.pub.timegrids.init):
            idxs[jdx] = func(date)
        return idxs


class Indexer:
    """Handles different |IndexerProperty| objects defining time
    related indices.

    One can specify the index arrays manually, but usually they are
    determined automatically based on the |Timegrids| object made
    available through module |pub|.
    """
    def __init__(self):
        self._monthofyear = None
        self._monthofyear_timegrids = hash(None)
        self._dayofyear = None
        self._dayofyear_hash = hash(None)
        self._timeofyear = None
        self._timeofyear_hash = hash(None)

    @IndexerProperty
    def monthofyear(self):
        """Month of the year index.

        The following example shows the month indices of the last days
        February (1) and the first days of March (2) for a leap year:

        >>> from hydpy import pub
        >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
        >>> monthofyear = pub.indexer.monthofyear
        >>> monthofyear
        array([1, 1, 1, 2, 2])
        """
        # pylint: disable=no-self-use
        # pylint does not understand descriptors well enough, so far
        def _monthofyear(date):
            return date.month - 1
        return _monthofyear

    @IndexerProperty
    def dayofyear(self):
        """Day of the year index (the first of January = 0...).

        For reasons of consistency between leap years and non-leap years,
        assuming a daily time step, index 59 is always associated with the
        29th of February.  Hence, it is missing in non-leap years:

        >>> from hydpy import pub
        >>> from hydpy.core.indextools import Indexer
        >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
        >>> Indexer().dayofyear
        array([57, 58, 59, 60, 61])
        >>> pub.timegrids = '27.02.2005', '3.03.2005', '1d'
        >>> Indexer().dayofyear
        array([57, 58, 60, 61])
        """
        # pylint: disable=no-self-use
        # pylint does not understand descriptors well enough, so far
        def _dayofyear(date):
            return (date.dayofyear-1 +
                    ((date.month > 2) and (not date.leapyear)))
        return _dayofyear

    @IndexerProperty
    def timeofyear(self):
        """Time of the year index (first simulation step of each year = 0...).

        The property |Indexer.timeofyear| is best explained through
        comparing it with property |Indexer.dayofyear|:

        Let us reconsider one of the examples of the documentation on
        property |Indexer.dayofyear|:

        >>> from hydpy import pub
        >>> from hydpy import Timegrids, Timegrid
        >>> from hydpy.core.indextools import Indexer
        >>> pub.timegrids = '27.02.2005', '3.03.2005', '1d'

        Due to the simulation stepsize being one day, the index arrays
        calculated by both properties are identical:

        >>> Indexer().dayofyear
        array([57, 58, 60, 61])
        >>> Indexer().timeofyear
        array([57, 58, 60, 61])

        In the next example the step size is halved:

        >>> pub.timegrids = '27.02.2005', '3.03.2005', '12h'

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
        # pylint: disable=no-self-use
        # pylint does not understand descriptors well enough, so far
        refgrid = timetools.Timegrid(
            timetools.Date('2000.01.01'),
            timetools.Date('2001.01.01'),
            hydpy.pub.timegrids.stepsize)

        def _timeofyear(date):
            date = copy.deepcopy(date)
            date.year = 2000
            return refgrid[date]

        return _timeofyear
