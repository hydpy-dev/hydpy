# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools


class H(sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""

    NDIM, NUMERIC, SPAN = 1, True, (None, None)


class VG(sequencetools.StateSequence):
    """Wasservolumen (water volume) [million m³]."""

    NDIM, NUMERIC, SPAN = 1, True, (None, None)


class WaterVolume(sequencetools.StateSequence):
    """Water volume [million m³]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))
