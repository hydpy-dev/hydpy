# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.whmod import whmod_control


class MixinZones(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NmbZones|.

    We take parameter |AvailableFieldCapacity| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> availablefieldcapacity.shape
    (3,)

    Redefining the same value does not delete the already available data:

    >>> availablefieldcapacity(2.0)
    >>> nmbzones(3)
    >>> availablefieldcapacity
    availablefieldcapacity(2.0)

    Changing |NmbZones| reshapes the parameter and requires resetting its values:

    >>> nmbzones(2)
    >>> availablefieldcapacity
    availablefieldcapacity(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, whmod_control.NmbZones):
            self.__hydpy__change_shape_if_necessary__((p.value,))
