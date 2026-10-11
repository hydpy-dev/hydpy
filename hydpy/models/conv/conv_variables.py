# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.conv import conv_derived


class MixinInputs(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences whose shape depends on the value of
    parameter |NmbInputs|.

    We take the flux sequence |conv_fluxes.Inputs| as an example:

    >>> from hydpy.models.conv import *
    >>> parameterstep()
    >>> derived.nmbinputs(2)
    >>> fluxes.inputs.shape
    (2,)

    Redefining the same number does not delete the already available data, while
    changing it does:

    >>> fluxes.inputs = 1.0, 2.0
    >>> derived.nmbinputs(2)
    >>> fluxes.inputs
    inputs(1.0, 2.0)
    >>> derived.nmbinputs(3)
    >>> fluxes.inputs
    inputs(nan, nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, conv_derived.NmbInputs):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinOutputs(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences whose shape depends on the value of
    parameter |NmbOutputs|.

    We take the flux sequence |conv_fluxes.Outputs| as an example:

    >>> from hydpy.models.conv import *
    >>> parameterstep()
    >>> derived.nmboutputs(2)
    >>> fluxes.outputs.shape
    (2,)

    Redefining the same number does not delete the already available data, while
    changing it does:

    >>> fluxes.outputs = 1.0, 2.0
    >>> derived.nmboutputs(2)
    >>> fluxes.outputs
    outputs(1.0, 2.0)
    >>> derived.nmboutputs(3)
    >>> fluxes.outputs
    outputs(nan, nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, conv_derived.NmbOutputs):
            self.__hydpy__change_shape_if_necessary__((p.value,))
