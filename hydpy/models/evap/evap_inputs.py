# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class ReferenceEvapotranspiration(sequencetools.InputSequence):
    """Reference evapotranspiration [mm/T]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.POTENTIAL_EVAPOTRANSPIRATION


class RelativeHumidity(sequencetools.InputSequence):
    """Relative humidity [%]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.RELATIVE_HUMIDITY


class WindSpeed(sequencetools.InputSequence):
    """Wind speed [m/s]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.WIND_SPEED


class AtmosphericPressure(sequencetools.InputSequence):
    """Atmospheric pressure [hPa]."""

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.ATMOSPHERIC_PRESSURE


class NormalAirTemperature(sequencetools.InputSequence):
    """Normal air temperature [°C].


    In the terminology of HBV96: TN.
    """

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.NORMAL_AIR_TEMPERATURE


class NormalEvapotranspiration(sequencetools.InputSequence):
    """Normal evapotranspiration [mm/T].

    In the terminology of HBV96: EPN.
    """

    NDIM = 0
    NUMERIC = False
    STANDARD_NAME = sequencetools.StandardInputNames.NORMAL_EVAPOTRANSPIRATION
