# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.snow import snow_control


class MixinLayers(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NLayers|.

    We take parameter |LayerArea| as an example:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(2)
    >>> layerarea.shape
    (2,)

    Redefining the same number of layers does not delete the already available data,
    while changing it does:

    >>> layerarea(0.5)
    >>> nlayers(2)
    >>> layerarea
    layerarea(0.5)
    >>> nlayers(3)
    >>> layerarea
    layerarea(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, snow_control.NLayers):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class Mixin366(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters that handle one value for each day of
    the year.

    Their shape does not depend on parameter |NLayers|, but |NLayers| triggers
    preparation.  We take parameter |GradTMean| as an example.

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(2)
    >>> gradtmean.shape
    (366,)

    Changing the number of layers does not affect the already available data:

    >>> gradtmean(1.0)
    >>> nlayers(3)
    >>> gradtmean
    gradtmean(1.0)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, snow_control.NLayers):
            self.__hydpy__change_shape_if_necessary__((366,))
