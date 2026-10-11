# pylint: disable=missing-module-docstring

import abc

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.kinw import kinw_control


class MixinSubsections(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences whose shape depends on the value of
    parameter |GTS|.

    We take the state sequence |H| as an example:

    >>> from hydpy.models.kinw import *
    >>> parameterstep()
    >>> gts(3)
    >>> states.h
    h(nan, nan, nan)

    |GTS| preserves existing values if the number of subsections does not change:

    >>> states.h = 1.0, 2.0, 3.0
    >>> gts(3)
    >>> states.h
    h(1.0, 2.0, 3.0)

    Changing the number of subsections resets the values:

    >>> gts(2)
    >>> states.h
    h(nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, kinw_control.GTS):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinSegments(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences whose shape depends on the value of
    parameter |kinw_control.NmbSegments|.

    We take the state sequence |WaterVolume| as an example:

    >>> from hydpy.models.kinw import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> states.watervolume.shape
    (2,)

    |NmbSegments| preserves existing values if the number of segments does not change:

    >>> states.watervolume = 1.0, 2.0
    >>> nmbsegments(2)
    >>> states.watervolume
    watervolume(1.0, 2.0)

    Changing the number of segments resets the values:

    >>> nmbsegments(3)
    >>> states.watervolume
    watervolume(nan, nan, nan)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, kinw_control.NmbSegments):
            self.__hydpy__change_shape_if_necessary__((p.value,))
