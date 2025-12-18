# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools


class Demand(sequencetools.FluxSequence):
    """ToDo"""

    NDIM, NUMERIC = 0, False


class Request(sequencetools.FluxSequence):
    """ToDo"""

    NDIM, NUMERIC = 1, False

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
