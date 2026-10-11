# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.dummy import dummy_control


class MixinZones(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |dummy_control.NmbZones|.

    We take the input sequence |dummy_inputs.SoilWater| as an example:

    >>> from hydpy.models.dummy_soilwater import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> inputs.soilwater.shape
    (3,)

    Redefining the same value does not delete the already available data:

    >>> inputs.soilwater = 1.0, 2.0, 3.0
    >>> nmbzones(3)
    >>> inputs.soilwater
    soilwater(1.0, 2.0, 3.0)

    Changing the value reshapes the sequence and resets its values:

    >>> nmbzones(2)
    >>> inputs.soilwater
    soilwater(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, dummy_control.NmbZones):
            self.__hydpy__change_shape_if_necessary__((p.value,))
