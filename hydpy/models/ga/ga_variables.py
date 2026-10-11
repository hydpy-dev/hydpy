# pylint: disable=missing-module-docstring

import abc

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.ga import ga_control


class MixinSoils(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NmbSoils|.

    We take parameter |SoilArea| as an example:

    >>> from hydpy.models.ga import *
    >>> parameterstep()
    >>> nmbsoils(2)
    >>> soilarea.shape
    (2,)

    Redefining the same value does not delete the already available data, while
    changing it does:

    >>> soilarea(1.0)
    >>> nmbsoils(2)
    >>> soilarea
    soilarea(1.0)
    >>> nmbsoils(1)
    >>> soilarea
    soilarea(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, ga_control.NmbSoils):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinBinsSoils(variabletools.Variable, abc.ABC):
    """Mixin class for 2-dimensional sequences whose shape depends on the values of
    the parameters |NmbBins| and |NmbSoils|.

    We take the state sequence |Moisture| as an example.  |NmbBins| determines the
    length of its first axis and |NmbSoils| the length of its second axis.  Its shape
    remains undefined as long as either parameter is not set:

    >>> from hydpy.models.ga import *
    >>> parameterstep()
    >>> nmbsoils(2)
    >>> states.moisture.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable \
`moisture` can only be retrieved after it has been defined.
    >>> nmbbins(3)
    >>> states.moisture.shape
    (3, 2)

    The order of defining both parameters does not matter:

    >>> from hydpy import reverse_model_wildcard_import
    >>> reverse_model_wildcard_import()
    >>> from hydpy.models.ga import *
    >>> parameterstep()
    >>> nmbbins(3)
    >>> states.moisture.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable \
`moisture` can only be retrieved after it has been defined.
    >>> nmbsoils(2)
    >>> states.moisture.shape
    (3, 2)

    Redefining the same values does not delete the already available data, while
    changing one of them does:

    >>> states.moisture = 0.5
    >>> nmbsoils(2)
    >>> nmbbins(3)
    >>> states.moisture
    moisture([[0.5, 0.5],
              [0.5, 0.5],
              [0.5, 0.5]])
    >>> nmbbins(2)
    >>> states.moisture
    moisture([[nan, nan],
              [nan, nan]])
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, ga_control.NmbSoils):
            nmbbins = exceptiontools.getattr_(p.subpars.nmbbins, "value", None)
            if nmbbins is not None:
                self.__hydpy__change_shape_if_necessary__((nmbbins, p.value))
        elif isinstance(p, ga_control.NmbBins):
            nmbsoils = exceptiontools.getattr_(p.subpars.nmbsoils, "value", None)
            if nmbsoils is not None:
                self.__hydpy__change_shape_if_necessary__((p.value, nmbsoils))
