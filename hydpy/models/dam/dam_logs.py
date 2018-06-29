# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...HydPy specific
from hydpy.core import objecttools
from hydpy.core import sequencetools


class LoggedTotalRemoteDischarge(sequencetools.LogSequence):
    """Logged discharge values from somewhere else [m3/s]."""
    NDIM, NUMERIC = 1, False


class LoggedOutflow(sequencetools.LogSequence):
    """Logged discharge values from the dam itself [m3/s]."""
    NDIM, NUMERIC = 1, False


class ShapeOne(sequencetools.LogSequence):
    """Base class for log sequences with a shape of one.

    Parameter derived from |ShapeOne| are generally initialized
    with a shape of one.  Taking parameter |LoggedRequiredRemoteRelease|
    as an example:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> logs.loggedrequiredremoterelease.shape
    (1,)

    Trying to set a new shape results in the following exceptions:

    >>> logs.loggedrequiredremoterelease.shape = 2
    Traceback (most recent call last):
    ...
    AttributeError: The shape of parameter `loggedrequiredremoterelease` \
cannot be changed, but this was attempted for element `?`.

    ."""

    def _initvalues(self):
        setattr(self.fastaccess, self.name,
                numpy.full(1, numpy.nan, dtype=float))

    def _setshape(self, shape):
        raise AttributeError(
            'The shape of parameter `%s` cannot be '
            'changed, but this was attempted for element `%s`.'
            % (self.name, objecttools.devicename(self)))

    shape = property(sequencetools.LogSequence._getshape, _setshape)


class LoggedRequiredRemoteRelease(ShapeOne):
    """Logged required discharge values computed by another model [m3/s]."""
    NDIM, NUMERIC = 1, False


class LoggedAllowedRemoteRelieve(ShapeOne):
    """Logged allowed discharge values computed by another model [m3/s]."""
    NDIM, NUMERIC = 1, False


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the dam model."""
    CLASSES = (LoggedTotalRemoteDischarge,
               LoggedOutflow,
               LoggedRequiredRemoteRelease,
               LoggedAllowedRemoteRelieve)
