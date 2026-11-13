# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools

# from hydpy.models.statcorr import statcorr_derived  actual import below


class MixinLogEntries(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional log sequences whose shape depends on the value of
    parameter |NmbLogEntries|.

    We take the log sequence |LoggedObservation| as an example:

    >>> from hydpy.models.statcorr import *
    >>> parameterstep()
    >>> derived.nmblogentries(3)
    >>> logs.loggedobservation
    loggedobservation(nan, nan, nan)

    To prevent losing information, updating parameter |NmbLogEntries| resets the
    shape only when necessary:

    >>> logs.loggedobservation = 1.0
    >>> derived.nmblogentries(3)
    >>> logs.loggedobservation
    loggedobservation(1.0, 1.0, 1.0)
    >>> derived.nmblogentries(2)
    >>> logs.loggedobservation
    loggedobservation(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.statcorr import statcorr_derived

        if isinstance(p, statcorr_derived.NmbLogEntries):
            self.__hydpy__change_shape_if_necessary__((p.value,))
