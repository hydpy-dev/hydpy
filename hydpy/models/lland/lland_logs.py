# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WEvPo(sequencetools.LogSequence):
    """Zeitlich gewichtete potenzielle Verdunstung (temporally weighted potential
    evapotranspiration) [mm/T]."""

    NDIM, NUMERIC = 2, False

    def _get_shape(self):
        """Log sequence |WEvPo| is generally initialized with a length of one on the
        first axis:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> logs.wevpo.shape = 3
        >>> logs.wevpo.shape
        (1, 3)
        """
        return super()._get_shape()

    def _set_shape(self, shape):
        super()._set_shape((1, shape))

    shape = property(fget=_get_shape, fset=_set_shape)


class LoggedTemL(sequencetools.LogSequence):
    """Logged air temperature [°C]."""

    NDIM, NUMERIC = 1, False


class LoggedRelativeHumidity(sequencetools.LogSequence):
    """Logged relative humidity [%]."""

    NDIM, NUMERIC = 1, False


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM, NUMERIC = 1, False


class LoggedPossibleSunshineDuration(sequencetools.LogSequence):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM, NUMERIC = 1, False


class LoggedGlobalRadiation(sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM, NUMERIC = 1, False


class LoggedWindSpeed2m(sequencetools.LogSequence):
    """Logged wind speed [m/s]."""

    NDIM, NUMERIC = 1, False
