# pylint: disable=missing-module-docstring

import abc

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.models.wq import wq_control


class MixinTrapezes(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of the parameter |NmbTrapezes|.

    We take parameter |BottomWidths| as an example:

    >>> from hydpy.models.wq import *
    >>> parameterstep()
    >>> nmbtrapezes(2)
    >>> bottomwidths.shape
    (2,)

    Redefining the same number of trapezes does not delete the already available
    data, while changing it does:

    >>> bottomwidths(1.0, 2.0)
    >>> nmbtrapezes(2)
    >>> bottomwidths
    bottomwidths(1.0, 2.0)
    >>> nmbtrapezes(3)
    >>> bottomwidths
    bottomwidths(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, wq_control.NmbTrapezes):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinWidths(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of the parameter |NmbWidths|.

    We take parameter |Heights| as an example:

    >>> from hydpy.models.wq import *
    >>> parameterstep()
    >>> nmbwidths(3)
    >>> heights.shape
    (3,)

    Redefining the same number of widths does not delete the already available data,
    while changing it does:

    >>> heights(1.0, 2.0, 3.0)
    >>> nmbwidths(3)
    >>> heights
    heights(1.0, 2.0, 3.0)
    >>> nmbwidths(2)
    >>> heights
    heights(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, wq_control.NmbWidths):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinSectorsAndWidths(variabletools.Variable, abc.ABC):
    """Mixin class for 2-dimensional parameters and sequences whose shape depends on
    the values of the parameters |NmbSectors| and |NmbWidths|.

    We take the derived parameter |SectorFlowPerimetersFromWidths| as an example.
    |NmbSectors| determines the length of its first axis and |NmbWidths| the length of
    its second axis.  Its shape remains undefined as long as either parameter is not
    ready:

    >>> from hydpy.models.wq import *
    >>> parameterstep()
    >>> nmbwidths(3)
    >>> derived.sectorflowperimetersfromwidths
    sectorflowperimetersfromwidths(?)
    >>> nmbsectors(2)
    >>> derived.sectorflowperimetersfromwidths.shape
    (2, 3)

    The order of defining both parameters does not matter:

    >>> from hydpy import reverse_model_wildcard_import
    >>> reverse_model_wildcard_import()
    >>> from hydpy.models.wq import *
    >>> parameterstep()
    >>> nmbsectors(2)
    >>> derived.sectorflowperimetersfromwidths
    sectorflowperimetersfromwidths(?)
    >>> nmbwidths(3)
    >>> derived.sectorflowperimetersfromwidths.shape
    (2, 3)

    Redefining the same values does not delete the already available data, while
    changing one of them does:

    >>> derived.sectorflowperimetersfromwidths.values = 1.0
    >>> nmbsectors(2)
    >>> nmbwidths(3)
    >>> from hydpy import print_matrix
    >>> print_matrix(derived.sectorflowperimetersfromwidths.values)
    | 1.0, 1.0, 1.0 |
    | 1.0, 1.0, 1.0 |
    >>> nmbwidths(4)
    >>> derived.sectorflowperimetersfromwidths
    sectorflowperimetersfromwidths(?)
    """

    NDIM: Final[Literal[2]] = 2

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, wq_control.NmbWidths):
            sectors = exceptiontools.getattr_(p.subpars.nmbsectors, "value", None)
            if sectors is not None:
                self.__hydpy__change_shape_if_necessary__((sectors, p.value))
        elif isinstance(p, wq_control.NmbSectors):
            rows = exceptiontools.getattr_(p.subpars.nmbwidths, "value", None)
            if rows is not None:
                self.__hydpy__change_shape_if_necessary__((p.value, rows))


class MixinTrapezesOrSectors(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NmbTrapezes| or parameter |NmbSectors|.

    We take parameter |StricklerCoefficients| as an example.  Its length agrees with
    the value of the last defined of both parameters:

    >>> from hydpy.models.wq import *
    >>> parameterstep()
    >>> nmbtrapezes(2)
    >>> stricklercoefficients.shape
    (2,)
    >>> nmbsectors(3)
    >>> stricklercoefficients.shape
    (3,)

    Redefining the same number does not delete the already available data, while
    changing it does:

    >>> stricklercoefficients(20.0)
    >>> nmbtrapezes(3)
    >>> stricklercoefficients
    stricklercoefficients(20.0)
    >>> nmbsectors(2)
    >>> stricklercoefficients
    stricklercoefficients(?)
    """

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, (wq_control.NmbTrapezes, wq_control.NmbSectors)):
            self.__hydpy__change_shape_if_necessary__((p.value,))
