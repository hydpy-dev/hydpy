# pylint: disable=missing-module-docstring

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_variables


class LoggedAirTemperature(
    evap_variables.MixinLogEntriesHRUs, sequencetools.LogSequence
):
    """Logged air temperature [°C]."""

    NDIM: Final[Literal[2]] = 2


class LoggedPrecipitation(
    evap_variables.MixinLogEntriesHRUs, sequencetools.LogSequence
):
    """Logged precipitation [mm/T]."""

    NDIM: Final[Literal[2]] = 2


class LoggedWindSpeed2m(evap_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged wind speed at 2 m above grass-like vegetation [m/s]."""

    NDIM: Final[Literal[1]] = 1


class LoggedRelativeHumidity(evap_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged relative humidity [%]."""

    NDIM: Final[Literal[1]] = 1


class LoggedSunshineDuration(evap_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1


class LoggedPossibleSunshineDuration(
    evap_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged astronomically possible sunshine duration [h]."""

    NDIM: Final[Literal[1]] = 1


class LoggedGlobalRadiation(evap_variables.MixinLogEntries, sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1


class LoggedClearSkySolarRadiation(
    evap_variables.MixinLogEntries, sequencetools.LogSequence
):
    """Logged clear sky radiation [W/m²]."""

    NDIM: Final[Literal[1]] = 1


class LoggedPotentialEvapotranspiration(sequencetools.LogSequence):
    """Logged (damped) potential evapotranspiration [mm/T].

    |LoggedPotentialEvapotranspiration| handles one value per hydrological response
    unit.  Thus, parameter |evap_control.NmbHRU| determines the length of its second
    axis, while the first axis is always one:

    >>> from hydpy.models.evap import *
    >>> parameterstep()
    >>> nmbhru(2)
    >>> logs.loggedpotentialevapotranspiration.shape
    (1, 2)

    Redefining the same number of hydrological response units does not delete the
    existing data, but changing it does:

    >>> logs.loggedpotentialevapotranspiration = 1.0, 2.0
    >>> nmbhru(2)
    >>> logs.loggedpotentialevapotranspiration
    loggedpotentialevapotranspiration(1.0, 2.0)
    >>> nmbhru(3)
    >>> logs.loggedpotentialevapotranspiration
    loggedpotentialevapotranspiration(nan, nan, nan)
    """

    NDIM: Final[Literal[2]] = 2

    @property
    def shape(self) -> ShapeHookGet:
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
    def shape(self, shape: ShapeHookSet) -> None:
        prop = super(__class__, type(self)).shape  # type: ignore[name-defined]
        prop.fset(self, (1, shape))  # type: ignore[attr-defined]

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, evap_control.NmbHRU):
            if exceptiontools.getattr_(self, "shape", None) != (1, p.value):
                self.shape = p.value  # type: ignore[assignment]


class LoggedWaterEvaporation(
    evap_variables.MixinLogEntriesHRUs, sequencetools.LogSequence
):
    """Logged evaporation from water areas [mm/T]."""

    NDIM: Final[Literal[2]] = 2


class LoggedPotentialSoilEvapotranspiration(
    evap_variables.MixinLogEntriesHRUs, sequencetools.LogSequence
):
    """Logged potential soil evapotranspiration [mm/T]."""

    NDIM: Final[Literal[2]] = 2
