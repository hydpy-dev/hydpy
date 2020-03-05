# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Nied(sequencetools.InputSequence):
    """Niederschlag (precipitation) [mm]."""
    NDIM, NUMERIC = 0, False


class TemL(sequencetools.InputSequence):
    """Lufttemperatur (air temperature) [°C]."""
    NDIM, NUMERIC = 0, False


class SunshineDuration(sequencetools.InputSequence):
    """Sonnenscheindauer [h]."""
    NDIM, NUMERIC = 0, False


class Glob(sequencetools.InputSequence):
    """Globalstrahlung (global radiation) [W/m²]."""
    NDIM, NUMERIC = 0, False


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""
    NDIM, NUMERIC = 0, False


class WindSpeed(sequencetools.InputSequence):
    """Wind speed [m/s]."""
    NDIM, NUMERIC = 0, False


class PET(sequencetools.InputSequence):
    """Potenzielle Verdunstung (potential evapotranspiration) [mm]."""
    NDIM, NUMERIC = 0, False


class AtmosphericPressure(sequencetools.InputSequence):
    """Luftdruck (atmospheric pressure) [hPa]."""
    NDIM, NUMERIC = 0, False
