# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


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

    NDIM, TYPE = 1, float

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))

    @property
    def refweights(self) -> parametertools.Parameter:
        """Alias for the associated instance of |LayerArea| for calculating aggregated
        values for layer-specific parameters."""
        return self.subpars.pars.control.layerarea


class Parameter1D366(parametertools.Parameter):
    """Base class for parameters with 366 values (days of the year)."""

    def __call__(self, *args, **kwargs):
        self.__hydpy__change_shape_if_necessary__((366,))
        super().__call__(*args, **kwargs)
