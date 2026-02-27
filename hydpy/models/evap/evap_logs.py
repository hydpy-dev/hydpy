# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LoggedAirTemperature(sequencetools.LogSequence):
    """Logged air temperature [°C]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False


class LoggedPrecipitation(sequencetools.LogSequence):
    """Logged precipitation [mm/T]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False


class LoggedWindSpeed2m(sequencetools.LogSequence):
    """Logged wind speed at 2 m above grass-like vegetation [m/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedRelativeHumidity(sequencetools.LogSequence):
    """Logged relative humidity [%]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedPossibleSunshineDuration(sequencetools.LogSequence):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedGlobalRadiation(sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedClearSkySolarRadiation(sequencetools.LogSequence):
    """Logged clear sky radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class LoggedPotentialEvapotranspiration(sequencetools.LogSequence):
    """Logged (damped) potential evapotranspiration [mm/T]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False

    @property
    def shape(self):
        """A tuple containing the lengths of all dimensions.

        |LoggedPotentialEvapotranspiration| is generally initialised with a length of
        one on the first axis:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> logs.loggedpotentialevapotranspiration.shape = 3
        >>> logs.loggedpotentialevapotranspiration.shape
        (1, 3)
        """
        return super().shape

    @shape.setter
    def shape(self, shape):
        super(__class__, type(self)).shape.fset(self, (1, shape))


class LoggedWaterEvaporation(sequencetools.LogSequence):
    """Logged evaporation from water areas [mm/T]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False


class LoggedPotentialSoilEvapotranspiration(sequencetools.LogSequence):
    """Logged potential soil evapotranspiration [mm/T]."""

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False
