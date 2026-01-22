# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools


class LoggedDischarge(sequencetools.LogSequence):
    """ToDo"""

    NDIM, NUMERIC = 0, False


class LoggedWaterVolume(sequencetools.LogSequence):
    """ToDo"""

    NDIM, NUMERIC = 1, False

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
