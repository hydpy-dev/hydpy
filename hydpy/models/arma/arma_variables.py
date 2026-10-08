# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.arma import arma_derived


class MixinNmb(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences that handle one value per response
    function.

    We take the flux sequence |QPIn| as an example.  Its length always agrees with the
    number of response functions:

    >>> from hydpy.models.arma import *
    >>> parameterstep("1d")
    >>> responses(((1.0, 2.0), (1.0,)), th_3=((1.0,), (1.0, 2.0, 3.0)))
    >>> derived.nmb.update()
    >>> fluxes.qpin
    qpin(nan, nan)

    Updating parameter |Nmb| again does not reset the available values as long as the
    number of response functions stays the same:

    >>> fluxes.qpin = 1.0, 2.0
    >>> derived.nmb.update()
    >>> fluxes.qpin
    qpin(1.0, 2.0)

    Otherwise, it does:

    >>> responses(((1.0, 2.0), (1.0,)))
    >>> derived.nmb.update()
    >>> fluxes.qpin
    qpin(nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, arma_derived.Nmb):
            self.__hydpy__change_shape_if_necessary__((p.value,))
