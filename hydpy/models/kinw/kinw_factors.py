# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
    SPAN = (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
