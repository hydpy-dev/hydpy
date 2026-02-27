# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class NmbZones(parametertools.Parameter):
    """The number of separately modelled zones [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    TIME = None
    SPAN = (0, None)

    def __call__(self, *args, **kwargs) -> None:
        nmbhru_old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        nmbhru_new = self.value
        if nmbhru_new != nmbhru_old:
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = nmbhru_new
