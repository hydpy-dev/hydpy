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


class LoggedRequiredRemoteRelease(sequencetools.LogSequence):
    """Logged required discharge values computed by another model [m3/s].

    Parameter :class:`LoggedRequiredRemoteRelease` is generally initialized
    with a shape of two:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> logs.loggedrequiredremoterelease.shape
    (2,)

    Trying to set a new shape results in the following exceptions:

    >>> logs.loggedrequiredremoterelease.shape = 2
    Traceback (most recent call last):
    ...
    AttributeError: The shape of parameter LoggedRequiredRemoteRelease \
cannot be changed, but this was attempted for element `?`.
    """
    NDIM, NUMERIC = 1, False

    def _initvalues(self):
        setattr(self.fastaccess, self.name,
                numpy.full(2, numpy.nan, dtype=float))

    def _setshape(self, shape):
        raise AttributeError(
            'The shape of parameter LoggedRequiredRemoteRelease cannot be '
            'changed, but this was attempted for element `%s`.'
            % objecttools.devicename(self))

    shape = property(sequencetools.LogSequence._getshape, _setshape)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the dam model."""
    _SEQCLASSES = (LoggedTotalRemoteDischarge,
                   LoggedOutflow,
                   LoggedRequiredRemoteRelease)
