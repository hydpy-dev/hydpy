# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class ReferenceEvapotranspiration(sequencetools.InputSequence):
    """Reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM, NUMERIC = 0, False


class WindSpeed(sequencetools.InputSequence):
    """Wind speed [m/s]."""

    NDIM, NUMERIC = 0, False


class AtmosphericPressure(sequencetools.InputSequence):
    """Atmospheric pressure [hPa]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.InputSequence):
    """Global radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.InputSequence):
    """Clear sky solar radiation [W/m²]."""

    NDIM, NUMERIC = 0, False


class NormalAirTemperature(sequencetools.InputSequence):
    """Normal air temperature [°C].


    In the terminology of HBV96: TN.
    """

    NDIM, NUMERIC = 0, False


class NormalEvapotranspiration(sequencetools.InputSequence):
    """Normal evapotranspiration [mm/T].

    In the terminology of HBV96: EPN.
    """

    NDIM, NUMERIC = 0, False
