# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
