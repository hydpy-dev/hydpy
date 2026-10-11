# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.test import test_control


class Q(sequencetools.FluxSequence):
    """Storage loss [mm/T]"""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
    SPAN = (0.0, None)


class QV(sequencetools.FluxSequence):
    """Storage loss vector [mm/T]"""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True
    SPAN = (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, test_control.N):
            self.__hydpy__change_shape_if_necessary__((p.value,))
