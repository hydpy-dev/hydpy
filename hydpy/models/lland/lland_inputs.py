# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

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
    """Sonnenscheindauer (sunshine duration) [h]."""

    NDIM, NUMERIC = 0, False


class PossibleSunshineDuration(sequencetools.InputSequence):
    """Astronomisch mögliche Sonnenscheindauer (astronomically possible sunshine
    duration) [h]."""

    NDIM, NUMERIC = 0, False


class Glob(sequencetools.InputSequence):
    """Globalstrahlung (global radiation) [W/m²]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.InputSequence):
    """Globalstrahlung (global radiation) [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM, NUMERIC = 0, False


class WindSpeed(sequencetools.InputSequence):
    """Windgeschwindigkeit (wind speed) [m/s]."""

    NDIM, NUMERIC = 0, False


class PET(sequencetools.InputSequence):
    """Potenzielle Verdunstung (potential evapotranspiration) [mm]."""

    NDIM, NUMERIC = 0, False


class AtmosphericPressure(sequencetools.InputSequence):
    """Luftdruck (atmospheric pressure) [kPa]."""

    NDIM, NUMERIC = 0, False
