# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WEvI(sequencetools.LogSequence):
    """Zeitlich gewichtete Interzeptionsverdunstung (temporally weighted interception
    evaporation) [mm/T]."""

    NDIM, NUMERIC = 2, False

    def _get_shape(self):
        """Log sequence |WEvI| is generally initialised with a length of one on the
        first axis:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> logs.wevi.shape = 3
        >>> logs.wevi.shape
        (1, 3)
        """
        return super()._get_shape()

    def _set_shape(self, shape):
        super()._set_shape((1, shape))

    shape = property(fget=_get_shape, fset=_set_shape)


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM, NUMERIC = 1, False


class LoggedPossibleSunshineDuration(sequencetools.LogSequence):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM, NUMERIC = 1, False
