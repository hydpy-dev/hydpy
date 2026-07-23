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


class SRedOrder(parametertools.Parameter):
    """Processing order for the snow redistribution routine [-]."""

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (snow_control.RedistributionPaths,)

    def update(self) -> None:
        """Update the processing order based on the weighting factors defined by
        parameter |SRed|.

        An example for well-sorted data:

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(FIELD)
        >>> sred([[0.0, 0.2, 0.2, 0.2, 0.2, 0.2],
        ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        >>> derived.sredorder.update()
        >>> derived.sredorder
        sredorder([[0, 1],
                   [0, 2],
                   [0, 3],
                   [0, 4],
                   [0, 5],
                   [1, 2],
                   [2, 3],
                   [3, 4],
                   [3, 5]])

        An erroneous example, including a cycle:

        >>> sred([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
        >>> derived.sredorder.update()
        Traceback (most recent call last):
        ...
        RuntimeError: The weighting factors of parameter `sred` of element `?` define \
at least one cycle: (1, 4), (4, 5), and (5, 1).

        A "no redistribution" example:

        >>> sred(0.0)
        >>> derived.sredorder.update()
        >>> derived.sredorder
        sredorder([[]])

        An example or unsorted data:

        >>> nmbzones(5)
        >>> zonetype(FIELD)
        >>> sred([[0.0, 0.5, 0.0, 0.5, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 1.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [1.0, 0.0, 0.0, 0.0, 0.0]])
        >>> derived.sredorder.update()
        >>> derived.sredorder
        sredorder([[2, 4],
                   [4, 0],
                   [0, 1],
                   [0, 3]])
        """
        sred = self.subpars.pars.control.sred
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


class SRedEnd(parametertools.Parameter):
    """Flags that indicate the "dead ends" of snow redistribution within a subbasin."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = bool
    SPAN = (False, True)

    CONTROLPARAMETERS = (snow_control.NumberZones,)
    DERIVEDPARAMETERS = (SRedOrder,)

    def update(self) -> None:
        """Update the dead-end flags based on parameter |SRedOrder|.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> derived.sredorder.shape = 9, 2
        >>> derived.sredorder([[0, 1],
        ...                    [0, 2],
        ...                    [1, 2],
        ...                    [0, 3],
        ...                    [2, 3],
        ...                    [0, 4],
        ...                    [3, 4],
        ...                    [0, 5],
        ...                    [3, 5]])
        >>> derived.sredend.update()
        >>> derived.sredend
        sredend(False, False, False, False, True, True)
        """
        nmbzones = self.subpars.pars.control.nmbzones.value
        sredorder = self.subpars.sredorder.values
        self.values = ~numpy.isin(numpy.arange(nmbzones), sredorder[:, 0])


class SRedNumber(parametertools.Parameter):
    """The total number of snow redistribution paths [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (snow_control.RedistributionPaths,)
    # DERIVEDPARAMETERS = (ZoneAreaRatios,)

    def update(self) -> None:
        """Update the number of redistribution paths based on the parameter |SRedOrder|.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> derived.sredorder.shape = 8, 3
        >>> derived.srednumber.update()
        >>> derived.srednumber
        srednumber(8)
        """
        self.value = self.subpars.sredorder.shape[0]


class RelZoneAreas(snow_parameters.ZipParameterFloat1D):
    """Relative area of all zones [-]."""

    SPAN = (0.0, 1.0)
    strict_valuehandling: bool = False

    CONTROLPARAMETERS = (
        snow_control.ZoneArea,
        snow_control.ZoneType,
        # snow_control.Psi,
    )

    def update(self) -> None:
        """Update the relative area based on the parameters |ZoneArea|, |ZoneType|,
        and |Psi|.

        In the simplest case, |RelZoneAreas| provides the fractions of the zone areas
        available via the control parameter |ZoneArea|:

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> area(100.0)
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> zonearea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> psi(1.0)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(field=0.1, forest=0.4, glacier=0.2, ilake=0.25,
                     sealed=0.05)

        |snow| assumes complete sealing for zones classified as land-use type
        |SEALED|.  Hence, besides interception losses, their runoff coefficient is
        always one.  When deriving zone types from available land-use classifications,
        we are likely to identify zones as |SEALED| that actually have lower runoff
        coefficients due to incomplete sealing, infiltration of sealed surface runoff
        on adjacent unsealed areas, retention of surface runoff in sewage treatment
        plants, and many other issues.  Parameter |Psi| allows decreasing the effective
        relative area of zones of type |SEALED|. Method |RelZoneAreas.update| divides
        the remaining "uneffective" sealed area to all zones of different land-use
        types (proportionally to their sizes), except those of type |GLACIER|:

        >>> psi(0.6)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(field=0.102667, forest=0.410667, glacier=0.2,
                     ilake=0.256667, sealed=0.03)

        For subbasins without |SEALED| zones, the value of |Psi| is irrelevant:

        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.1, 0.4, 0.2, 0.25, 0.05)

        The same holds for subbasins consisting only of |SEALED| and |GLACIER| zones:

        >>> zonetype(SEALED)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.1, 0.4, 0.2, 0.25, 0.05)
        >>> zonetype(GLACIER, GLACIER, SEALED, SEALED, SEALED)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.1, 0.4, 0.2, 0.25, 0.05)

        The last example demonstrates that the underlying algorithm also works when
        multiple |SEALED| or |GLACIER| zones are involved:

        >>> zonetype(FIELD, GLACIER, GLACIER, SEALED, SEALED)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.22, 0.4, 0.2, 0.15, 0.03)
        """
        control = self.subpars.pars.control
        zonearea = control.zonearea.values
        zonetype = control.zonetype.values
        psi = control.psi.value
        # idxs_source = zonetype == SEALED
        # idxs_sink = ~idxs_source * (zonetype != GLACIER)
        # if (psi < 1.0) and numpy.any(idxs_source) and numpy.any(idxs_sink):
        #     adjusted_area = zonearea.copy()
        #     adjusted_area[idxs_source] *= psi
        #     delta = numpy.sum(zonearea) - numpy.sum(adjusted_area)
        #     weights = adjusted_area[idxs_sink] / numpy.sum(adjusted_area[idxs_sink])
        #     adjusted_area[idxs_sink] += weights * delta
        #     self.values = adjusted_area / numpy.sum(adjusted_area)
        # else:
        #     self.values = zonearea / numpy.sum(zonearea)


class RelLandArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, |GLACIER|, and |SEALED| zones [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)

    CONTROLPARAMETERS = (snow_control.Land,)
    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self) -> None:
        """Update |RelLandArea| based on |RelZoneAreas| and |ZoneType|.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.1, 0.2, 0.3, 0.15, 0.25)
        >>> derived.rellandarea.update()
        >>> derived.rellandarea
        rellandarea(0.85)
        """
        temp = self.subpars.relzoneareas.values.copy()
        temp[self.subpars.pars.control.Land.values] = 0.0
        self(numpy.sum(temp))


class ZoneAreaRatios(parametertools.Parameter):
    """Ratios of all zone combinations [-]."""

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float
    SPAN = (0.0, None)

    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self) -> None:
        """Update the zone area ratios based on the parameter |ZoneArea|.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> derived.relzoneareas(0.0625, 0.3125, 0.625)
        >>> derived.zonearearatios.update()
        >>> derived.zonearearatios
        zonearearatios([[1.0, 0.2, 0.1],
                        [5.0, 1.0, 0.5],
                        [10.0, 2.0, 1.0]])
        """
        relzoneareas = self.subpars.relzoneareas.values
        self.values = relzoneareas[:, numpy.newaxis] / relzoneareas


class IndicesZoneZ(parametertools.Parameter):
    """Indices of the zones sorted by altitude [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (snow_control.ZoneHeight,)

    def update(self) -> None:
        """Update the indices based on the order of the values of parameter |ZoneZ|.

        >>> from hydpy.models.snow import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonez(3.0, 4.0, 2.0, 5.0, 3.0)
        >>> derived.indiceszonez.update()
        >>> derived.indiceszonez
        indiceszonez(2, 0, 4, 1, 3)
        """
        self.values = numpy.argsort(self.subpars.pars.control.zonez.values)
