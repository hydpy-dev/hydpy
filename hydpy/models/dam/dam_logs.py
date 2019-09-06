# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import sequencetools


class LoggedTotalRemoteDischarge(sequencetools.LogSequence):
    """Logged discharge values from somewhere else [m3/s]."""
    NDIM, NUMERIC = 1, False


class LoggedOutflow(sequencetools.LogSequence):
    """Logged discharge values from the dam itself [m3/s]."""
    NDIM, NUMERIC = 1, False


class ShapeOne(sequencetools.LogSequence):
    """Base class for log sequences with a shape of one."""

    def _finalise_connections(self):
        self.shape = (1,)

    def __hydpy__get_shape__(self):
        """Parameter derived from |ShapeOne| are generally initialised
        with a shape of one.

        We take parameter |LoggedRequiredRemoteRelease|
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

        See the documentation on property |Variable.shape| of class
        |Variable| for further information.
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape):
        if hasattr(self, 'shape'):
            raise AttributeError(
                f'The shape of parameter `{self.name}` cannot be '
                f'changed, but this was attempted for element '
                f'`{objecttools.devicename(self)}`.')
        super().__hydpy__set_shape__(shape)

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)


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
