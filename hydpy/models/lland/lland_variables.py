# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.lland import lland_control

# from hydpy.models.lland import lland_derived  actual import below


class MixinHRUs(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NHRU|.

    We take parameter |KG| as an example:

    >>> from hydpy.models.lland import *
    >>> parameterstep()
    >>> nhru(3)
    >>> kg.shape
    (3,)

    Redefining the same number of hydrological response units does not delete the
    already available data:

    >>> kg(2.0)
    >>> nhru(3)
    >>> kg
    kg(2.0)

    Changing the number of hydrological response units reshapes the parameter and
    requires resetting its values:

    >>> nhru(2)
    >>> kg
    kg(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, lland_control.NHRU):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinLogEntries(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional log sequences whose shape depends on the value of
    parameter |lland_derived.NmbLogEntries|.

    We take the log sequence |LoggedSunshineDuration| as an example:

    >>> from hydpy.models.lland import *
    >>> parameterstep()
    >>> derived.nmblogentries(3)
    >>> logs.loggedsunshineduration
    loggedsunshineduration(nan, nan, nan)

    Redefining the same number of log entries does not delete the already available
    data, while changing it does:

    >>> logs.loggedsunshineduration = 2.0
    >>> derived.nmblogentries(3)
    >>> logs.loggedsunshineduration
    loggedsunshineduration(2.0, 2.0, 2.0)
    >>> derived.nmblogentries(2)
    >>> logs.loggedsunshineduration
    loggedsunshineduration(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.lland import lland_derived

        if isinstance(p, lland_derived.NmbLogEntries):
            self.__hydpy__change_shape_if_necessary__((p.value,))
