# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *


class Parameter1DLayers(parametertools.Parameter):
    """Base class for parameters with different values for individual layers.

    The following example shows that the shape of parameter |MeanAnSolidPrecip| is set
    automatically, and that weighted averaging is possible:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(4)
    >>> layerarea(0.1, 0.2, 0.3, 0.4)
    >>> meanansolidprecip(3.0, 1.0, 4.0, 2.0)
    >>> from hydpy import round_
    >>> round_(meanansolidprecip.average_values())
    2.5
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))

    @property
    def refweights(self) -> parametertools.Parameter:
        """Alias for the associated instance of |LayerArea| for calculating aggregated
        values for layer-specific parameters."""
        return self.subpars.pars.control.layerarea


class Parameter1D366(parametertools.Parameter):
    """Base class for parameters with 366 values (days of the year)."""

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((366,))
