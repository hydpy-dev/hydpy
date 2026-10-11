# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.musk import musk_control


class MixinSegments(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences whose shape depends on the value of
    parameter |musk_control.NmbSegments|.

    We take the flux sequence |ReferenceDischarge| as an example:

    >>> from hydpy.models.musk import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> fluxes.referencedischarge.shape
    (2,)

    |NmbSegments| preserves existing values if the number of segments does not change:

    >>> fluxes.referencedischarge = 1.0, 2.0
    >>> nmbsegments(2)
    >>> fluxes.referencedischarge
    referencedischarge(1.0, 2.0)

    Changing the number of segments resets the values:

    >>> nmbsegments(3)
    >>> fluxes.referencedischarge
    referencedischarge(nan, nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, musk_control.NmbSegments):
            self.__hydpy__change_shape_if_necessary__((p.value,))
