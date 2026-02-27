# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class H(sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True


class VG(sequencetools.StateSequence):
    """Wasservolumen (water volume) [million m³]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True


class WaterVolume(sequencetools.StateSequence):
    """Water volume [million m³]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
