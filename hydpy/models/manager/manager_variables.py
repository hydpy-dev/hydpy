# pylint: disable=missing-module-docstring

import abc

from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.models.manager import manager_model
from hydpy.models.manager import manager_control

# from hydpy.models.manager import manager_derived  actual import below


class MixinSources(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences that handle one value per
    source element.

    We take parameter |Active| as an example:

    >>> from hydpy.models.manager import *
    >>> parameterstep()
    >>> sources("a", "b")
    >>> active.shape
    (2,)

    Redefining the same number of sources does not delete the already available data,
    while changing it does:

    >>> active(a=True, b=False)
    >>> sources("a", "b")
    >>> active
    active(a=True, b=False)
    >>> sources("a", "b", "c")
    >>> active
    active(?)
    """

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, manager_control.Sources):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinSourceSequence(MixinSources, abc.ABC):
    """Extends |MixinSources| by a string representation that includes the source names.

    We take the flux sequence |manager_fluxes.Request| as an example:

    >>> from hydpy.models.manager import *
    >>> parameterstep()
    >>> sources("a", "b")
    >>> fluxes.request = 1.0, 2.0
    >>> fluxes.request
    request(a=1.0, b=2.0)
    """

    def __repr__(self) -> str:
        model = cast(manager_model.Model, self.subvars.vars.model)
        sourcenames = model.parameters.control.sources.sourcenames
        repr_ = objecttools.repr_
        n2v = tuple(f"{n}={repr_(v)}" for n, v in zip(sourcenames, self.values))
        return objecttools.assignrepr_values(n2v, f"{self.name}(", width=70) + ")"


class MixinMemory(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional sequences that handle one value per memorised
    simulation step.

    We take the log sequence |LoggedDischarge| as an example:

    >>> from hydpy.models.manager import *
    >>> parameterstep()
    >>> derived.memorylength(3)
    >>> logs.loggeddischarge
    loggeddischarge(nan, nan, nan)

    Redefining the same memory length does not delete the already available data,
    while changing it does:

    >>> logs.loggeddischarge = 1.0
    >>> derived.memorylength(3)
    >>> logs.loggeddischarge
    loggeddischarge(1.0, 1.0, 1.0)
    >>> derived.memorylength(2)
    >>> logs.loggeddischarge
    loggeddischarge(nan, nan)
    """

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.manager import manager_derived

        if isinstance(p, manager_derived.MemoryLength):
            self.__hydpy__change_shape_if_necessary__((p.value,))
