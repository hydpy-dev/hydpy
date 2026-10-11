# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.dam import dam_control


class MixinLogEntries(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional log sequences whose shape depends on the value of
    parameter |dam_control.NmbLogEntries|.

    We take the log sequence |LoggedTotalRemoteDischarge| as an example:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> nmblogentries(3)
    >>> logs.loggedtotalremotedischarge
    loggedtotalremotedischarge(nan, nan, nan)

    To prevent losing information, updating parameter |dam_control.NmbLogEntries|
    resets the shape only when necessary:

    >>> logs.loggedtotalremotedischarge = 1.0
    >>> nmblogentries(3)
    >>> logs.loggedtotalremotedischarge
    loggedtotalremotedischarge(1.0, 1.0, 1.0)
    >>> nmblogentries(2)
    >>> logs.loggedtotalremotedischarge
    loggedtotalremotedischarge(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, dam_control.NmbLogEntries):
            self.__hydpy__change_shape_if_necessary__((p.value,))
