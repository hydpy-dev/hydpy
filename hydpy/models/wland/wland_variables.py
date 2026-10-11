# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.wland import wland_control


class MixinHRUs(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NU|.

    We take the state sequence |IC| as an example:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(3)
    >>> states.ic.shape
    (3,)

    Redefining the same value for parameter |NU| does not delete the already available
    data:

    >>> states.ic = 1.0
    >>> nu(3)
    >>> states.ic
    ic(1.0, 1.0, 1.0)

    Changing the value of parameter |NU| reshapes the sequence and resets its values:

    >>> nu(2)
    >>> states.ic
    ic(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, wland_control.NU):
            self.__hydpy__change_shape_if_necessary__((p.value,))
