# pylint: disable=missing-module-docstring

import networkx
import numpy

from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_parameters
from hydpy.models.snow import snow_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class ZoneAreaFraction(snow_parameters.ZipParameterComplete):
    """Relative area of each zone [-]."""

    TYPE: Final = float
    SPAN = (0.0, 1.0)
    strict_valuehandling: bool = False

    CONTROLPARAMETERS = (snow_control.ZoneArea,)

    def update(self) -> None:
        """Update |ZoneAreaFraction| based on parameter |ZoneArea|.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(5)
        >>> zonearea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> derived.zoneareafraction.update()
        >>> derived.zoneareafraction
        zoneareafraction(0.1, 0.4, 0.2, 0.25, 0.05)
        """
        zonearea = self.subpars.pars.control.zonearea.values
        self(zonearea / numpy.sum(zonearea))


class LandAreaFraction(parametertools.Parameter):
    """Relative area of all zones representing land areas [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)

    CONTROLPARAMETERS = (snow_control.Land,)
    DERIVEDPARAMETERS = (ZoneAreaFraction,)

    def update(self) -> None:
        """Update |LandAreaFraction| based on parameters |ZoneAreaFraction| and
        |snow_control.Land|.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(5)
        >>> land(True, True, True, False, True)
        >>> derived.zoneareafraction(0.1, 0.2, 0.3, 0.15, 0.25)
        >>> derived.landareafraction.update()
        >>> derived.landareafraction
        landareafraction(0.85)
        """
        temp = self.subpars.zoneareafraction.values.copy()
        temp[~self.subpars.pars.control.land.values] = 0.0
        self(numpy.sum(temp))


class ZoneAreaRatio(parametertools.Parameter):
    """Area ratios of all zone pairs [-]."""

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float
    SPAN = (0.0, None)

    DERIVEDPARAMETERS = (ZoneAreaFraction,)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:

        if isinstance(p, snow_control.NumberZones):
            self.__hydpy__change_shape_if_necessary__((p.value, p.value))

    def update(self) -> None:
        """Update |ZoneAreaRatio| based on parameter |ZoneAreaFraction|.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> derived.zoneareafraction(0.0625, 0.3125, 0.625)
        >>> derived.zonearearatio.update()
        >>> derived.zonearearatio
        zonearearatio([[1.0, 0.2, 0.1],
                       [5.0, 1.0, 0.5],
                       [10.0, 2.0, 1.0]])
        """
        zoneareafraction = self.subpars.zoneareafraction.values
        self.values = zoneareafraction[:, numpy.newaxis] / zoneareafraction


class AverageHeight(parametertools.Parameter):
    """Average subbasin elevation [100m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float

    CONTROLPARAMETERS = (snow_control.ZoneArea, snow_control.ZoneHeight)

    def update(self) -> None:
        """Update |AverageHeight| based on parameters |ZoneArea| and |ZoneHeight|.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zoneheight(1.0, 3.0, 8.0)
        >>> derived.averageheight.update()
        >>> derived.averageheight
        averageheight(3.0)
        """
        control = self.subpars.pars.control
        areas = control.zonearea.values
        self.value = numpy.dot(areas, control.zoneheight.values) / numpy.sum(areas)


class ZoneHeightOrder(snow_parameters.ZipParameterComplete):
    """Indices of the zones sorted by elevation [-]."""

    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (snow_control.ZoneHeight,)

    def update(self) -> None:
        """Update |ZoneHeightOrder| based on parameter |ZoneHeight|.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(5)
        >>> zoneheight(3.0, 4.0, 2.0, 5.0, 3.0)
        >>> derived.zoneheightorder.update()
        >>> derived.zoneheightorder
        zoneheightorder(2, 0, 4, 1, 3)
        """
        self.values = numpy.argsort(self.subpars.pars.control.zoneheight.values)


class RedistributionOrder(parametertools.Parameter):
    """Processing order for the snow redistribution routine [-]."""

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (snow_control.RedistributionPaths,)

    def update(self) -> None:
        """Update |RedistributionOrder| based on parameter |RedistributionPaths|.

        An example for well-sorted data:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(6)
        >>> land(True)
        >>> redistributionpaths([[0.0, 0.2, 0.2, 0.2, 0.2, 0.2],
        ...                      [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        >>> derived.redistributionorder.update()
        >>> derived.redistributionorder
        redistributionorder([[0, 1],
                             [0, 2],
                             [0, 3],
                             [0, 4],
                             [0, 5],
                             [1, 2],
                             [2, 3],
                             [3, 4],
                             [3, 5]])

        An erroneous example, including a cycle:

        >>> redistributionpaths([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ...                      [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
        >>> derived.redistributionorder.update()
        Traceback (most recent call last):
        ...
        RuntimeError: The weighting factors of parameter `redistributionpaths` of \
element `?` define at least one cycle: (1, 4), (4, 5), and (5, 1).

        A "no redistribution" example:

        >>> redistributionpaths(0.0)
        >>> derived.redistributionorder.update()
        >>> derived.redistributionorder
        redistributionorder([[]])

        An example for unsorted data:

        >>> numberzones(5)
        >>> land(True)
        >>> redistributionpaths([[0.0, 0.5, 0.0, 0.5, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 1.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [1.0, 0.0, 0.0, 0.0, 0.0]])
        >>> derived.redistributionorder.update()
        >>> derived.redistributionorder
        redistributionorder([[2, 4],
                             [4, 0],
                             [0, 1],
                             [0, 3]])
        """
        sred = self.subpars.pars.control.redistributionpaths
        idxs, jdxs = numpy.nonzero(sred.values)
        self.shape = len(idxs), 2
        if len(idxs):
            dg = networkx.DiGraph(zip(idxs, jdxs))
            try:
                repr_tuple = objecttools.repr_tuple
                first_cycle = (repr_tuple(c) for c in networkx.find_cycle(dg))
                raise RuntimeError(
                    f"The weighting factors of parameter "
                    f"{objecttools.elementphrase(sred)} define at least one cycle: "
                    f"{objecttools.enumeration(first_cycle)}."
                )
            except networkx.NetworkXNoCycle:
                self.values = tuple(networkx.topological_sort(networkx.line_graph(dg)))
        else:
            self.values = 0


class RedistributionEnd(snow_parameters.ZipParameterComplete):
    """Flags that indicate the "dead ends" of snow redistribution within a subbasin."""

    TYPE: Final = bool
    SPAN = (False, True)
    CONTROLPARAMETERS = (snow_control.NumberZones,)
    DERIVEDPARAMETERS = (RedistributionOrder,)

    def update(self) -> None:
        """Update |RedistributionEnd| based on parameter |RedistributionOrder|.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> numberzones(6)
        >>> derived.redistributionorder.shape = 9, 2
        >>> derived.redistributionorder([[0, 1],
        ...                              [0, 2],
        ...                              [1, 2],
        ...                              [0, 3],
        ...                              [2, 3],
        ...                              [0, 4],
        ...                              [3, 4],
        ...                              [0, 5],
        ...                              [3, 5]])
        >>> derived.redistributionend.update()
        >>> derived.redistributionend
        redistributionend(False, False, False, False, True, True)
        """
        numberzones = self.subpars.pars.control.numberzones.value
        redistributionorder = self.subpars.redistributionorder.values
        self.values = ~numpy.isin(numpy.arange(numberzones), redistributionorder[:, 0])


class RedistributionNumber(parametertools.Parameter):
    """The total number of snow redistribution paths [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)

    DERIVEDPARAMETERS = (RedistributionOrder,)

    def update(self) -> None:
        """Update |RedistributionNumber| based on parameter |RedistributionOrder|.

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> derived.redistributionorder.shape = 8, 3
        >>> derived.redistributionnumber.update()
        >>> derived.redistributionnumber
        redistributionnumber(8)
        """
        self.value = self.subpars.redistributionorder.shape[0]


class GThresh(snow_parameters.Parameter1DLayers):
    """Accumulation threshold [mm]."""

    SPAN = (0.0, None)

    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.MeanAnSolidPrecip,
        snow_control.CN4,
    )

    def update(self) -> None:
        """Update |GThresh| based on :math:`GThresh = MeanAnSolidPrecip / CN4` [-].

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> meanansolidprecip(700.0, 750.0, 730.0, 630.0, 700.0)
        >>> cn4(0.6)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(420.0, 450.0, 438.0, 378.0, 420.0)
        """
        control = self.subpars.pars.control
        self.values = control.meanansolidprecip * control.cn4


class ZMean(parametertools.Parameter):
    """Mean elevation of all layer [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float

    CONTROLPARAMETERS = (snow_control.ZLayers,)

    def update(self) -> None:
        """Update |ZMean| by averaging |ZLayers| (weighted with |LayerArea|).

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> zlayers(700.0, 750.0, 730.0, 630.0, 700.0)
        >>> layerarea(0.1, 0.3, 0.2, 0.2, 0.2)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(707.0)
        """
        self.value = self.subpars.pars.control.zlayers.average_values()
