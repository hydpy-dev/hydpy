# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.rconc import rconc_control


class SC(sequencetools.StateSequence):
    """Storage cascade for runoff concentration [mm].

    Parameter |NmbStorages| determines the length of |SC|:

    >>> from hydpy.models.rconc import *
    >>> parameterstep()
    >>> nmbstorages(3)
    >>> states.sc.shape
    (3,)

    |NmbStorages| preserves existing values if the number of storages does not change:

    >>> states.sc = 1.0, 2.0, 3.0
    >>> nmbstorages(3)
    >>> states.sc
    sc(1.0, 2.0, 3.0)

    Changing the number of storages resets the values:

    >>> nmbstorages(2)
    >>> states.sc
    sc(nan, nan)
    """

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, rconc_control.NmbStorages):
            self.__hydpy__change_shape_if_necessary__((p.value,))
