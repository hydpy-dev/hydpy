# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import propertytools
from hydpy.core import sequencetools


class LoggedAirTemperature(sequencetools.LogSequence):
    """Logged air temperature [°C]."""

    NDIM, NUMERIC = 2, False


class LoggedPrecipitation(sequencetools.LogSequence):
    """Logged precipitation [mm/T]."""

    NDIM, NUMERIC = 2, False


class LoggedWindSpeed2m(sequencetools.LogSequence):
    """Logged wind speed at 2 m above grass-like vegetation [m/s]."""

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


class LoggedClearSkySolarRadiation(sequencetools.LogSequence):
    """Logged clear sky radiation [W/m²]."""

    NDIM, NUMERIC = 1, False


class LoggedPotentialEvapotranspiration(sequencetools.LogSequence):
    """Logged (damped) potential evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 2, False

    def _get_shape(self):
        """A tuple containing the lengths of all dimensions.

        |LoggedPotentialEvapotranspiration| is generally initialised with a length of
        one on the first axis:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> logs.loggedpotentialevapotranspiration.shape = 3
        >>> logs.loggedpotentialevapotranspiration.shape
        (1, 3)
        """
        return super()._get_shape()

    def _set_shape(self, shape):
        super()._set_shape((1, shape))

    shape = propertytools.Property(fget=_get_shape, fset=_set_shape)


class LoggedWaterEvaporation(sequencetools.LogSequence):
    """Logged evaporation from water areas [mm/T]."""

    NDIM, NUMERIC = 2, False


class LoggedPotentialSoilEvapotranspiration(sequencetools.LogSequence):
    """Logged potential soil evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 2, False
