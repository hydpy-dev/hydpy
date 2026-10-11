# pylint: disable=missing-module-docstring

import abc

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.evap import evap_control

# from hydpy.models.evap import evap_derived  actual import below


class MixinHRUs(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |evap_control.NmbHRU|.

    We take parameter |HRUArea| as an example:

    >>> from hydpy.models.evap import *
    >>> parameterstep()
    >>> nmbhru(2)
    >>> hruarea.shape
    (2,)

    Redefining the same value does not delete the already available data, while
    changing it does:

    >>> hruarea(1.0, 2.0)
    >>> nmbhru(2)
    >>> hruarea
    hruarea(1.0, 2.0)
    >>> nmbhru(3)
    >>> hruarea
    hruarea(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, evap_control.NmbHRU):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinLogEntries(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional log sequences whose shape depends on the value of
    parameter |evap_derived.NmbLogEntries|.

    We take the log sequence |LoggedGlobalRadiation| as an example:

    >>> from hydpy.models.evap import *
    >>> parameterstep()
    >>> derived.nmblogentries(3)
    >>> logs.loggedglobalradiation
    loggedglobalradiation(nan, nan, nan)

    Redefining the same number of log entries does not delete the already available
    data, while changing it does:

    >>> logs.loggedglobalradiation = 1.0
    >>> derived.nmblogentries(3)
    >>> logs.loggedglobalradiation
    loggedglobalradiation(1.0, 1.0, 1.0)
    >>> derived.nmblogentries(2)
    >>> logs.loggedglobalradiation
    loggedglobalradiation(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.evap import evap_derived

        if isinstance(p, evap_derived.NmbLogEntries):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinLogEntriesHRUs(variabletools.Variable, abc.ABC):
    """Mixin class for 2-dimensional log sequences whose shape depends on the values of
    the parameters |evap_derived.NmbLogEntries| and |evap_control.NmbHRU|.

    We take the log sequence |LoggedAirTemperature| as an example.
    |evap_derived.NmbLogEntries| determines the length of its first axis and
    |evap_control.NmbHRU| the length of its second axis.  Its shape remains undefined as
    long as either parameter is not ready:

    >>> from hydpy.models.evap import *
    >>> parameterstep()
    >>> derived.nmblogentries(2)
    >>> logs.loggedairtemperature.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable \
`loggedairtemperature` can only be retrieved after it has been defined.
    >>> nmbhru(3)
    >>> logs.loggedairtemperature.shape
    (2, 3)

    The order of defining both parameters does not matter:

    >>> from hydpy import reverse_model_wildcard_import
    >>> reverse_model_wildcard_import()
    >>> from hydpy.models.evap import *
    >>> parameterstep()
    >>> nmbhru(3)
    >>> logs.loggedairtemperature.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable \
`loggedairtemperature` can only be retrieved after it has been defined.
    >>> derived.nmblogentries(2)
    >>> logs.loggedairtemperature.shape
    (2, 3)

    Redefining the same values does not delete the already available data, while
    changing one of them does:

    >>> logs.loggedairtemperature = 2.0
    >>> nmbhru(3)
    >>> derived.nmblogentries(2)
    >>> logs.loggedairtemperature
    loggedairtemperature([[2.0, 2.0, 2.0],
                          [2.0, 2.0, 2.0]])
    >>> nmbhru(2)
    >>> logs.loggedairtemperature
    loggedairtemperature([[nan, nan],
                          [nan, nan]])
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.evap import evap_derived

        if isinstance(p, evap_derived.NmbLogEntries):
            control = p.subpars.pars.control
            nmbhru = exceptiontools.getattr_(control.nmbhru, "value", None)
            if nmbhru is not None:
                self.__hydpy__change_shape_if_necessary__((p.value, nmbhru))
        elif isinstance(p, evap_control.NmbHRU):
            par = getattr(p.subpars.pars.derived, "nmblogentries", None)
            nmblogentries = exceptiontools.getattr_(par, "value", None)
            if nmblogentries is not None:
                self.__hydpy__change_shape_if_necessary__((nmblogentries, p.value))
