# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.meteo import meteo_control

# from hydpy.models.meteo import meteo_derived  actual import below


class MixinHRUs(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |meteo_control.NmbHRU|.

    We take parameter |PrecipitationFactor| as an example:

    >>> from hydpy.models.meteo import *
    >>> parameterstep()
    >>> nmbhru(3)
    >>> precipitationfactor.shape
    (3,)

    Redefining the same value does not delete the already available data:

    >>> precipitationfactor(2.0)
    >>> nmbhru(3)
    >>> precipitationfactor
    precipitationfactor(2.0)

    Changing the value of |NmbHRU| reshapes the parameter and makes resetting its
    values necessary:

    >>> nmbhru(2)
    >>> precipitationfactor
    precipitationfactor(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, meteo_control.NmbHRU):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinLogEntries(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional log sequences whose shape depends on the value of
    parameter |meteo_derived.NmbLogEntries|.

    We take the log sequence |LoggedSunshineDuration| as an example:

    >>> from hydpy.models.meteo import *
    >>> parameterstep()
    >>> derived.nmblogentries(3)
    >>> logs.loggedsunshineduration
    loggedsunshineduration(nan, nan, nan)

    Redefining the same number of log entries does not delete the already available
    data, while changing it does:

    >>> logs.loggedsunshineduration = 1.0
    >>> derived.nmblogentries(3)
    >>> logs.loggedsunshineduration
    loggedsunshineduration(1.0, 1.0, 1.0)
    >>> derived.nmblogentries(2)
    >>> logs.loggedsunshineduration
    loggedsunshineduration(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.meteo import meteo_derived

        if isinstance(p, meteo_derived.NmbLogEntries):
            self.__hydpy__change_shape_if_necessary__((p.value,))
