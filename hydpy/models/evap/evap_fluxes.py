# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class AdjustedWindSpeed(sequencetools.FluxSequence):
    """Adjusted wind speed [m/s]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(sequencetools.FluxSequence):
    """Saturation vapour pressure [kPa]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressureSlope(sequencetools.FluxSequence):
    """The slope of the saturation vapour pressure curve [kPa/°C]."""

    NDIM, NUMERIC = 0, False


class ActualVapourPressure(sequencetools.FluxSequence):
    """Actual vapour pressure [kPa]."""

    NDIM, NUMERIC = 0, False


class EarthSunDistance(sequencetools.FluxSequence):
    """The relative inverse distance between the earth and the sun [-]."""

    NDIM, NUMERIC = 0, False


class SolarDeclination(sequencetools.FluxSequence):
    """Solar declination [-]."""

    NDIM, NUMERIC = 0, False


class SunsetHourAngle(sequencetools.FluxSequence):
    """Sunset hour angle [rad]."""

    NDIM, NUMERIC = 0, False


class SolarTimeAngle(sequencetools.FluxSequence):
    """Solar time angle [rad]."""

    NDIM, NUMERIC = 0, False


class ExtraterrestrialRadiation(sequencetools.FluxSequence):
    """Extraterrestial radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class PossibleSunshineDuration(sequencetools.FluxSequence):
    """Possible astronomical sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class ClearSkySolarRadiation(sequencetools.FluxSequence):
    """Clear sky solar radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.FluxSequence):
    """Global radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class NetShortwaveRadiation(sequencetools.FluxSequence):
    """Net shortwave radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class NetLongwaveRadiation(sequencetools.FluxSequence):
    """Net longwave radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class NetRadiation(sequencetools.FluxSequence):
    """Total net radiation [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class SoilHeatFlux(sequencetools.FluxSequence):
    """Soil heat flux [MJ/m²/T]."""

    NDIM, NUMERIC = 0, False


class PsychrometricConstant(sequencetools.FluxSequence):
    """Psychrometric constant [kPa/°C]."""

    NDIM, NUMERIC = 0, False


class ReferenceEvapotranspiration(sequencetools.FluxSequence):
    """Reference evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False
