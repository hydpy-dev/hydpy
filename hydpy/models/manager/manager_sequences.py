# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

# ...from manager
from hydpy.models.manager import manager_model
from hydpy.models.manager import manager_control
from hydpy.models.manager import manager_derived


class MixinSource(sequencetools.ModelSequence):
    """Mixin class for 1-dimensional sequences that handle one value per source
    element."""

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, manager_control.Sources):
            self.__hydpy__change_shape_if_necessary__((p.value,))

    def __repr__(self) -> str:
        model = cast(manager_model.Model, self.subseqs.seqs.model)
        sourcenames = model.parameters.control.sources.sourcenames
        repr_ = objecttools.repr_
        n2v = tuple(f"{n}={repr_(v)}" for n, v in zip(sourcenames, self.values))
        return objecttools.assignrepr_values(n2v, f"{self.name}(", width=70) + ")"


class MixinMemory(sequencetools.LogSequence):
    """Mixin class for 1-dimensional sequences that handle one value per memorised
    simulation step."""

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, manager_derived.MemoryLength):
            self.__hydpy__change_shape_if_necessary__((p.value,))
