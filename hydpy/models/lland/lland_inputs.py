# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Nied(sequencetools.InputSequence):
    """Niederschlag (precipitation) [mm/T]."""

    NDIM, NUMERIC = 0, False


class TemL(sequencetools.InputSequence):
    """Lufttemperatur (air temperature) [°C]."""

    NDIM, NUMERIC = 0, False


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM, NUMERIC = 0, False


class WindSpeed(sequencetools.InputSequence):
    """Windgeschwindigkeit (wind speed) [m/s]."""

    NDIM, NUMERIC = 0, False
