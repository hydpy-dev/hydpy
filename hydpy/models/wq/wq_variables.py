# pylint: disable=missing-module-docstring

import abc

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.models.wq import wq_control


class MixinTrapezes(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of the parameter |NmbTrapezes|."""

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, wq_control.NmbTrapezes):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinWidths(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of the parameter |NmbWidths|."""

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, wq_control.NmbWidths):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinSectorsAndWidths(variabletools.Variable, abc.ABC):
    """Mixin class for 2-dimensional parameters and sequences whose shape depends on
    the values of the parameters |NmbSectors| and |NmbWidths|."""

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
    the value of parameter |NmbTrapezes| or parameter |NmbSectors|."""

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, (wq_control.NmbTrapezes, wq_control.NmbSectors)):
            self.__hydpy__change_shape_if_necessary__((p.value,))
