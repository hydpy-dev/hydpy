# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class K(parametertools.Parameter):
    """Storage coefficient [1/T].

    For educational purposes, the actual value of parameter |K| does
    not depend on the difference between the actual simulation time step and
    the actual parameter time step.
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class N(parametertools.Parameter):
    """Number of storages [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        seqs = self.subpars.pars.model.sequences
        seqs.states.sv.shape = self.value
        seqs.fluxes.qv.shape = self.value
