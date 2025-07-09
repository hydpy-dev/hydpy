# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools

# ...from wq
from hydpy.models.wq import wq_control


class MixinTrapezes(variabletools.Variable):
    """Mixin class for 1-dimensional parameters and sequence whose shape depends on the
    value of parameter |NmbTrapezes|."""

    NDIM = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
