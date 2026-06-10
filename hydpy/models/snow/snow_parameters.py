# pylint: disable=missing-module-docstring

from hydpy.core import masktools
from hydpy.core import parametertools
from hydpy.core.typingtools import *

# from hydpy.models.snow import snow_control  # actual import below


class ZipParameter1DNmbHRU(parametertools.ZipParameter):
    """Base class for parameters with different values for individual hydrological
    response units.

    The following example shows that the shape of parameter || is set ToDo
    automatically, and that weighted averaging is possible:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nmbhru(4)
    >>> hruarea(0.1, 0.2, 0.3, 0.4)
    >>> from hydpy import round_
    >>> round_(hruarea.average_values())  # ToDo: better example
    0.3
    """

    TYPE: Final = float

    constants = {}
    mask = masktools.SubmodelIndexMask()

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        from hydpy.models.snow.snow_control import NmbHRU

        if isinstance(p, NmbHRU):
            self.__hydpy__change_shape_if_necessary__((p.value,))

    @property
    def refweights(self) -> parametertools.Parameter:
        """Alias for the associated instance of |NmbHRU| for calculating aggregated
        values for layer-specific parameters."""
        return self.subpars.pars.control.hruarea


class LandParameter1DNmbHRU(ZipParameter1DNmbHRU):
    """Base class for water area-related 1-dimensional parameters.

    >>> from hydpy.models.hland_96 import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> area(6.0)
    >>> zonearea(2.0, 1.0, 1.0, 1.0, 1.0)
    >>> zonetype(ILAKE, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonez(2.0)
    >>> fc(200.0)
    >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
    ...     temperaturethresholdice(ilake=1.0)
    >>> model.aetmodel.parameters.control.temperaturethresholdice
    temperaturethresholdice(1.0)
    >>> model.aetmodel.parameters.control.temperaturethresholdice.average_values()
    1.0
    """

    # mask = snow_masks.Land() # ToDo


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
