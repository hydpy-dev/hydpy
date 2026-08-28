# pylint: disable=missing-module-docstring
from __future__ import annotations

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_masks

if TYPE_CHECKING:
    from hydpy.models.snow import snow_control  # actual import below


class ZipParameterBase(parametertools.ZipParameter):
    """Base class for |ZipParameterComplete| and |ZipPameterLand|."""

    constants = {}

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.snow.snow_control import NumberZones

        if isinstance(p, NumberZones):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class ZipParameterComplete(ZipParameterBase):
    """Base class for 1-dimensional parameters with values for all zone types.

    The following example shows that the shape of parameter |ZoneHeight| is set
    automatically, and that weighted averaging is supported:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
    >>> from hydpy.models.hland_96 import *
    >>> parameterstep("1d")
    >>> area(10.0)
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, ILAKE, GLACIER)
    >>> zonearea(4.0, 3.0, 2.0, 1.0)
    >>> zonez(10.0, 40.0, 30.0, 20.0)
    >>> with model.add_snowmodel_v1("snow_dd") as snowmodel:
    ...     redistributionpaths(n_zones=1)
    >>> from hydpy import round_
    >>> zoneheight = snowmodel.parameters.control.zoneheight
    >>> round_(zoneheight.average_values())
    24.0
    >>> round_(zoneheight.average_values(zoneheight.availablemasks.land))
    22.5
    """

    mask = snow_masks.Complete()


class ZipPameterLand(ZipParameterBase):
    """Base class for 1-dimensional parameters with values only for land zones.

    The following example shows that the shape of parameter |DegreeDayFactor| is set
    automatically, and that weighted averaging is supported:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
    >>> from hydpy.models.hland_96 import *
    >>> parameterstep("1d")
    >>> area(10.0)
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, ILAKE, GLACIER)
    >>> zonearea(4.0, 3.0, 2.0, 1.0)
    >>> zonez(10.0, 40.0, 30.0, 20.0)
    >>> with model.add_snowmodel_v1("snow_dd") as snowmodel:
    ...     redistributionpaths(n_zones=1)
    ...     degreedayfactor(field=5.0, forest=3.0, glacier=4.0)
    >>> from hydpy import round_
    >>> round_(snowmodel.parameters.control.degreedayfactor.average_values())
    4.125
    """

    mask = snow_masks.Land()


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
