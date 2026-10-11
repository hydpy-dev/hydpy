# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.test import test_control


class S(sequencetools.StateSequence):
    """Storage content [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
    SPAN = (0.0, None)


class SV(sequencetools.StateSequence):
    """Storage content vector[mm]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True
    SPAN = (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, test_control.N):
            self.__hydpy__change_shape_if_necessary__((p.value,))
