# pylint: disable=missing-module-docstring

import itertools

import math

import numpy

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.auxs import smoothtools
from hydpy.models.wq import wq_control
from hydpy.models.wq import wq_variables


class BottomDepths(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The cumulated depth of a trapezium and its lower neighbours [m]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.BottomLevels,)

    def update(self) -> None:
        r"""Calculate the depth values based on
        :math:`BottomDepths_i = BottomLevels_i - BottomLevels_0`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 4.0, 6.0)
        >>> derived.bottomdepths.update()
        >>> derived.bottomdepths
        bottomdepths(0.0, 3.0, 5.0)
        """
        bottomlevels = self.subpars.pars.control.bottomlevels.values
        self.values = bottomlevels - bottomlevels[0]


class TrapezeHeights(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The individual height of each trapezium [m].

    The highest trapezium has no upper neighbour and is thus infinitely high.
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.BottomLevels,)

    def update(self) -> None:
        r"""Calculate the height values based on
        :math:`TrapezeHeights_i = BottomLevels_{i+1} - BottomLevels_i`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 4.0, 6.0)
        >>> derived.trapezeheights.update()
        >>> derived.trapezeheights
        trapezeheights(3.0, 2.0, inf)
        """
        self.values = numpy.inf
        self.values[:-1] = numpy.diff(self.subpars.pars.control.bottomlevels.values)


class SlopeWidths(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The total width of both side slopes of each trapezium.

    The highest trapezium has no upper neighbour and is thus infinitely high and
    potentially infinitely wide.
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.SideSlopes,)
    DERIVEDPARAMETERS = (TrapezeHeights,)

    def update(self) -> None:
        r"""Calculate the slope width values based on
        :math:`SlopeWidths = 2 \cdot SideSlopes \cdot TrapezeHeights`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> derived.trapezeheights(2.0, 3.0, inf)
        >>> derived.slopewidths.update()
        >>> derived.slopewidths
        slopewidths(0.0, 12.0, inf)
        """
        sideslopes = self.subpars.pars.control.sideslopes.values
        trapezeheights = self.subpars.trapezeheights.values
        self.values = numpy.inf
        self.values[:-1] = 2.0 * sideslopes[:-1] * trapezeheights[:-1]


class TrapezeAreas(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The individual area of each trapezium [m].

    The highest trapezium has no upper neighbour and is thus infinitely large.
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.BottomWidths,)
    DERIVEDPARAMETERS = (TrapezeHeights, SlopeWidths)

    def update(self) -> None:
        r"""Calculate the perimeter derivatives based on
        :math:`(BottomWidths + SlopeWidths / 2) \cdot TrapezeHeights`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(4)
        >>> bottomlevels(1.0, 3.0, 4.0, 5.0)
        >>> bottomwidths(2.0, 0.0, 2.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0, 2.0)
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> derived.trapezeareas.update()
        >>> derived.trapezeareas
        trapezeareas(4.0, 4.0, 10.0, inf)
        """
        wb = self.subpars.pars.control.bottomwidths.values
        ht = self.subpars.trapezeheights.values
        ws = self.subpars.slopewidths.values
        self.values = (wb + ws / 2.0) * ht
        w = numpy.cumsum(wb + ws)
        self.values[1:] += w[:-1] * ht[1:]


class PerimeterDerivatives(wq_variables.MixinTrapezes, parametertools.Parameter):
    """Change of the perimeter of each trapezium relative to a water level increase
    within the trapezoidal's range [-].
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.SideSlopes,)

    def update(self) -> None:
        r"""Calculate the perimeter derivatives based on
        :math:`2 \cdot \sqrt{1 + SideSlopes^2}`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> sideslopes(0.0, 2.0)
        >>> derived.perimeterderivatives.update()
        >>> derived.perimeterderivatives
        perimeterderivatives(2.0, 4.472136)
        """
        sideslopes = self.subpars.pars.control.sideslopes.value
        self.values = 2.0 * (1.0 + sideslopes**2.0) ** 0.5


class _SectorWidths(wq_variables.MixinSectorsAndWidths, parametertools.Parameter):
    TYPE: Final = float
    SPAN = (0.0, None)

    def _update(self, widths: wq_control.FlowWidths | wq_control.TotalWidths) -> None:
        control = self.subpars.pars.control
        n = control.nmbsectors.value
        t = control.transitions.values
        w = widths.values
        self.values = 0.0
        s = self.values
        for i in range(n):
            w0 = 0.0 if i == 0 else w[t[i - 1]]
            w1 = w[-1] if i + 1 == n else w[t[i]]
            s[i, :] = numpy.clip(w - w0, 0.0, w1 - w0)


class SectorFlowWidths(_SectorWidths):
    """The sector-specific widths of those subareas of the cross section involved in
    water routing [m]."""

    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.FlowWidths,
    )

    def update(self) -> None:
        """Allocate the |wq_control.FlowWidths| parts to the respective cross-section
        sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowwidths
        sectorflowwidths([[2.0, 4.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0],
                          [0.0, 0.0, 0.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0],
                          [0.0, 0.0, 0.0, 0.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 10.0, 12.0]])
        """
        flowwidths = self.subpars.pars.control.flowwidths
        self._update(flowwidths)


class SectorTotalWidths(_SectorWidths):
    """The sector-specific widths of the total cross section [m]."""

    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.TotalWidths,
    )

    def update(self) -> None:
        """Allocate the |wq_control.TotalWidths| parts to the respective cross-section
        sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> totalwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectortotalwidths.update()
        >>> derived.sectortotalwidths
        sectortotalwidths([[2.0, 4.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0],
                           [0.0, 0.0, 0.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0],
                           [0.0, 0.0, 0.0, 0.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                           [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 10.0, 12.0]])
        """
        totalwidths = self.subpars.pars.control.totalwidths
        self._update(totalwidths)


class _SectorAreasFromWidths(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):

    def _update(self, widths: SectorFlowWidths | SectorTotalWidths) -> None:
        h = self.subpars.pars.control.heights.values
        w = widths.values
        h_diff = numpy.diff(h)
        w_mean = (w[:, :-1] + w[:, 1:]) / 2.0
        self.values = 0.0
        self.values[:, 1:] = numpy.cumsum(h_diff * w_mean, axis=1)


class SectorFlowAreasFromWidths(_SectorAreasFromWidths):
    """The sector-specific wetted areas of those subareas of the cross section
    involved in water routing [m²]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorFlowWidths,)

    def update(self) -> None:
        """Calculate the cumulative sum of the individual trapezoidal areas defined by
        the height-width pairs of the individual sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowareasfromwidths.update()
        >>> derived.sectorflowareasfromwidths
        sectorflowareasfromwidths([[0.0, 6.0, 11.0, 11.0, 11.0, 17.0, 23.0,
                                    29.0, 35.0],
                                   [0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 16.0, 24.0,
                                    32.0],
                                   [0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 8.0, 12.0,
                                    16.0],
                                   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 11.0,
                                    22.0]])
        """
        sectorflowwidths = self.subpars.sectorflowwidths
        self._update(sectorflowwidths)


class SectorTotalAreasFromWidths(_SectorAreasFromWidths):
    """The sector-specific wetted areas of the total cross section [m²]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorTotalWidths,)

    def update(self) -> None:
        """Calculate the cumulative sum of the individual trapezoidal areas defined by
        the height-width pairs of the individual sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> totalwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectortotalwidths.update()
        >>> derived.sectortotalareasfromwidths.update()
        >>> derived.sectortotalareasfromwidths
        sectortotalareasfromwidths([[0.0, 6.0, 11.0, 11.0, 11.0, 17.0, 23.0,
                                     29.0, 35.0],
                                    [0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 16.0, 24.0,
                                     32.0],
                                    [0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 8.0, 12.0,
                                     16.0],
                                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 11.0,
                                     22.0]])
        """
        sectortotalwidths = self.subpars.sectortotalwidths
        self._update(sectortotalwidths)


class _SectorAreasFromTable(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):

    def _update(self, *, widths: VectorFloat, areas: VectorFloat) -> None:

        control = self.subpars.pars.control
        nw = control.nmbwidths.value
        ns = control.nmbsectors.value
        ts = control.transitions.values
        hs = control.heights.values

        self.values = 0.0
        vs = self.values
        for i in range(ns):
            t = (nw - 1) if (i == ns - 1) else ts[i]
            vs[i, : t + 1] = areas[: t + 1]
            vs[i, t + 1 :] = areas[t] + numpy.cumsum(widths[t] * numpy.diff(hs[t:]))
            if i > 0:
                vs[i, :] -= numpy.sum(vs[:i, :], axis=0)


class SectorFlowAreasFromTable(_SectorAreasFromTable):
    """The sector-specific wetted areas of those subareas of the cross section involved
    in water routing [m²]."""

    TYPE: Final = float

    CONTROLPARAMETERS = (
        wq_control.NmbWidths,
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.FlowWidths,
        wq_control.FlowAreas,
    )

    def update(self) -> None:
        """Divide the routing-relevant wetted areas of the complete cross section into
        the individual sections.

        We perform the following test calculation using geometric input data, assuming
        a pattern of stacked trapezoids for simplicity:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> transitions(2, 3, 5)
        >>> heights(1.0, 3.0, 4.0, 6.0, 6.0, 9.0, 10.0)
        >>> flowwidths(2.0, 4.0, 4.0, 6.0, 8.0, 8.0, 12.0)
        >>> flowareas.approximate()
        >>> flowareas
        flowareas(0.0, 6.0, 10.0, 20.0, 20.0, 44.0, 54.0)
        >>> derived.sectorflowareasfromtable.update()
        >>> derived.sectorflowareasfromtable
        sectorflowareasfromtable([[0.0, 6.0, 10.0, 18.0, 18.0, 30.0, 34.0],
                                  [0.0, 0.0, 0.0, 2.0, 2.0, 8.0, 10.0],
                                  [0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 8.0],
                                  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]])
        >>> assert numpy.array_equal(
        ...     numpy.sum(derived.sectorflowareasfromtable.values, axis=0),
        ...     flowareas.values,
        ... )
        """

        control = self.subpars.pars.control
        self._update(widths=control.flowwidths.values, areas=control.flowareas.values)


class SectorTotalAreasFromTable(_SectorAreasFromTable):
    """The sector-specific wetted areas of the total cross section [m²]."""

    TYPE: Final = float

    CONTROLPARAMETERS = (
        wq_control.NmbWidths,
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.TotalWidths,
        wq_control.TotalAreas,
    )

    def update(self) -> None:
        """Divide the total wetted areas of the complete cross section into the
        individual sections.

        We perform the following test calculation using geometric input data, assuming
        a pattern of stacked trapezoids for simplicity:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> transitions(2, 3, 5)
        >>> heights(1.0, 3.0, 4.0, 6.0, 6.0, 9.0, 10.0)
        >>> totalwidths(2.0, 4.0, 4.0, 6.0, 8.0, 8.0, 12.0)
        >>> totalareas.approximate()
        >>> totalareas
        totalareas(0.0, 6.0, 10.0, 20.0, 20.0, 44.0, 54.0)
        >>> derived.sectortotalareasfromtable.update()
        >>> derived.sectortotalareasfromtable
        sectortotalareasfromtable([[0.0, 6.0, 10.0, 18.0, 18.0, 30.0, 34.0],
                                   [0.0, 0.0, 0.0, 2.0, 2.0, 8.0, 10.0],
                                   [0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 8.0],
                                   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]])
        >>> assert numpy.array_equal(
        ...     numpy.sum(derived.sectortotalareasfromtable.values, axis=0),
        ...     totalareas.values,
        ... )
        """

        control = self.subpars.pars.control
        self._update(widths=control.totalwidths.values, areas=control.totalareas.values)


class _AreaAdjustments(wq_variables.MixinSectorsAndWidths, parametertools.Parameter):

    def _update(self, *, widths: MatrixFloat, areas: MatrixFloat) -> None:

        control = self.subpars.pars.control
        nw = control.nmbwidths.value
        ns = control.nmbsectors.value
        ts = control.transitions.values
        hs = control.heights.values

        self.values = 1.0
        vs = self.values
        for i in range(ns):
            t1 = nw - 1 if i == ns - 1 else ts[i]
            t0 = 0 if i == 0 else ts[i - 1]
            dhs = numpy.diff(hs[t0 : t1 + 1])
            das_trapezoid = dhs * (widths[i, t0:t1] + widths[i, t0 + 1 : t1 + 1]) / 2.0
            das_data = numpy.diff(areas[i, t0 : t1 + 1])
            sel = dhs > 0.0
            vs[i, t0:t1][sel] = das_data[sel] / das_trapezoid[sel]
        self.trim()


class FlowAreaAdjustments(_AreaAdjustments):
    """Factors for adjusting flow areas calculated by assuming trapezoidal geometries
    to externally defined flow areas [-]."""

    TYPE: Final = float
    SPAN = (0.0, 2.0)

    CONTROLPARAMETERS = (
        wq_control.NmbWidths,
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
    )
    DERIVEDPARAMETERS = (SectorFlowWidths, SectorFlowAreasFromTable)

    def update(self) -> None:
        """Divide externally defined flow areas by flow areas calculated assuming
        trapezoidal geometries.

        For the first test calculation, we calculate the "externally defined" areas
        based on trapezoidal geometries.  Hence, all adjustment factors are one:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> transitions(2, 3, 5)
        >>> heights(1.0, 3.0, 4.0, 6.0, 6.0, 9.0, 10.0)
        >>> flowwidths(2.0, 4.0, 4.0, 6.0, 8.0, 8.0, 12.0)
        >>> flowareas.approximate()
        >>> flowareas
        flowareas(0.0, 6.0, 10.0, 20.0, 20.0, 44.0, 54.0)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowareasfromtable.update()
        >>> derived.flowareaadjustments.update()
        >>> derived.flowareaadjustments
        flowareaadjustments(1.0)

        After setting "non-trapezoidal" areas, the individual adjustment factors should
        usually lie between zero and two (in the extrapolation range, all factors are
        one):

        >>> flowareas(0.0, 8.0, 10.0, 22.0, 22.0, 42.0, 53.0)
        >>> derived.sectorflowareasfromtable.update()
        >>> derived.flowareaadjustments.update()
        >>> derived.flowareaadjustments
        flowareaadjustments([[1.333333, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0],
                             [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0],
                             [1.0, 1.0, 1.0, 1.0, 0.333333, 1.0, 1.0],
                             [1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 1.0]])

        Unplausible adjustment factors are trimmed to the acceptable interval:

        >>> flowareas(0.0, 8.0, 10.0, 22.0, 22.0, 39.0, 53.0)
        >>> derived.sectorflowareasfromtable.update()
        >>> derived.flowareaadjustments.update()
        >>> derived.flowareaadjustments
        flowareaadjustments([[1.333333, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0],
                             [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0],
                             [1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],
                             [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0]])
        """
        derived = self.subpars
        self._update(
            widths=derived.sectorflowwidths.values,
            areas=derived.sectorflowareasfromtable.values,
        )


class TotalAreaAdjustments(_AreaAdjustments):
    """Factors for adjusting total wetted areas calculated by assuming trapezoidal
    geometries to externally defined total wetted areas [-]."""

    TYPE: Final = float
    SPAN = (0.0, 2.0)

    CONTROLPARAMETERS = (
        wq_control.NmbWidths,
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
    )
    DERIVEDPARAMETERS = (SectorTotalWidths, SectorTotalAreasFromTable)

    def update(self) -> None:
        """Divide externally defined flow areas by flow areas calculated assuming
        trapezoidal geometries.

        For the first test calculation, we calculate the "externally defined" areas
        based on trapezoidal geometries.  Hence, all adjustment factors are one:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> transitions(2, 3, 5)
        >>> heights(1.0, 3.0, 4.0, 6.0, 6.0, 9.0, 10.0)
        >>> totalwidths(2.0, 4.0, 4.0, 6.0, 8.0, 8.0, 12.0)
        >>> totalareas.approximate()
        >>> totalareas
        totalareas(0.0, 6.0, 10.0, 20.0, 20.0, 44.0, 54.0)
        >>> derived.sectortotalwidths.update()
        >>> derived.sectortotalareasfromtable.update()
        >>> derived.totalareaadjustments.update()
        >>> derived.totalareaadjustments
        totalareaadjustments(1.0)

        After setting "non-trapezoidal" areas, the individual adjustment factors should
        usually lie between zero and two (in the extrapolation range, all factors are
        one):

        >>> totalareas(0.0, 8.0, 10.0, 22.0, 22.0, 42.0, 53.0)
        >>> derived.sectortotalareasfromtable.update()
        >>> derived.totalareaadjustments.update()
        >>> derived.totalareaadjustments
        totalareaadjustments([[1.333333, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0],
                              [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0],
                              [1.0, 1.0, 1.0, 1.0, 0.333333, 1.0, 1.0],
                              [1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 1.0]])

        Unplausible adjustment factors are trimmed to the acceptable interval:

        >>> totalareas(0.0, 8.0, 10.0, 22.0, 22.0, 39.0, 53.0)
        >>> derived.sectortotalareasfromtable.update()
        >>> derived.totalareaadjustments.update()
        >>> derived.totalareaadjustments
        totalareaadjustments([[1.333333, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0],
                              [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0],
                              [1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],
                              [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0]])
        """
        derived = self.subpars
        self._update(
            widths=derived.sectortotalwidths.values,
            areas=derived.sectortotalareasfromtable.values,
        )


class SectorFlowPerimetersFromWidths(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):
    """The sector-specific wetted perimeters of those subareas of the cross section
    involved in water routing [m]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorFlowWidths,)

    def update(self) -> None:
        """Calculate the total wetted perimeters of the individual sections.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowperimetersfromwidths.update()
        >>> derived.sectorflowperimetersfromwidths
        sectorflowperimetersfromwidths([[2.0, 6.472136, 9.300563, 9.300563,
                                         9.300563, 11.300563, 13.300563,
                                         15.300563, 17.300563],
                                        [0.0, 0.0, 0.0, 8.0, 8.0, 10.0, 12.0,
                                         14.0, 16.0],
                                        [0.0, 0.0, 0.0, 0.0, 4.0, 6.0, 8.0,
                                         10.0, 12.0],
                                        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.324555,
                                         10.796691, 13.625118]])
        """

        control = self.subpars.pars.control
        h = control.heights.values
        w = self.subpars.sectorflowwidths.values
        dh = numpy.diff(h)
        dw = numpy.diff(w)
        p = numpy.sqrt(numpy.square(2.0 * dh) + numpy.square(dw))
        self.values = 0.0
        for i, t in enumerate(
            itertools.chain([numpy.int64(0)], control.transitions.values)
        ):
            self.values[i, t:] = w[i, t]
            self.values[i, t + 1 :] += numpy.cumsum(p[i, t:])


class SectorFlowPerimetersFromTable(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):
    """The sector-specific wetted perimeters of those subareas of the cross section
    involved in water routing [m]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (
        wq_control.NmbWidths,
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.FlowWidths,
        wq_control.FlowPerimeters,
    )

    def update(self) -> None:
        """Divide the total wetted perimeters of the complete cross section into the
        individual sections.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> transitions(2, 3, 5)
        >>> heights(1.0, 3.0, 4.0, 6.0, 6.0, 9.0, 10.0)
        >>> flowwidths(2.0, 4.0, 4.0, 6.0, 8.0, 8.0, 12.0)
        >>> flowperimeters.approximate()
        >>> flowperimeters
        flowperimeters(2.0, 6.472136, 8.472136, 12.944272, 14.944272, 20.944272,
                       25.416408)
        >>> derived.sectorflowperimetersfromtable.update()
        >>> derived.sectorflowperimetersfromtable
        sectorflowperimetersfromtable([[2.0, 6.472136, 8.472136, 12.472136,
                                        12.472136, 18.472136, 20.472136],
                                       [0.0, 0.0, 0.0, 4.472136, 4.472136,
                                        10.472136, 12.472136],
                                       [0.0, 0.0, 0.0, 0.0, 2.0, 8.0, 10.0],
                                       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.472136]])
        """

        control = self.subpars.pars.control
        nw = control.nmbwidths.value
        ns = control.nmbsectors.value
        ts = control.transitions.values
        hs = control.heights.values
        ps = control.flowperimeters.values

        self.values = 0.0
        vs = self.values
        for i in range(ns):
            t1 = (nw - 1) if (i == ns - 1) else ts[i]
            if i == 0:
                vs[i, : t1 + 1] = ps[: t1 + 1]
            else:
                t0 = ts[i - 1]
                vs[i, t0 + 1 : t1 + 1] = ps[t0 + 1 : t1 + 1] - ps[t0]
            vs[i, t1 + 1 :] = vs[i, t1] + numpy.cumsum(2.0 * numpy.diff(hs[t1:]))


class SectorFlowPerimeterDerivativesFromWidths(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):
    """Sector-specific changes in the wetted perimeters of the subareas of the cross
    section involved in water routing with respect to water-level increases [m]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorFlowWidths,)

    def update(self) -> None:
        r"""Calculate the flow perimeter derivatives based on
        :math:`2 \cdot \sqrt{1 + (dw / dh / 2)^2}`.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowperimeterderivativesfromwidths.update()
        >>> derived.sectorflowperimeterderivativesfromwidths
        sectorflowperimeterderivativesfromwidths([[2.236068, 2.828427, 2.0, 2.0,
                                                   2.0, 2.0, 2.0, 2.0, 2.0],
                                                  [nan, nan, 2.0, 2.0, 2.0, 2.0,
                                                   2.0, 2.0, 2.0],
                                                  [nan, nan, nan, 2.0, 2.0, 2.0,
                                                   2.0, 2.0, 2.0],
                                                  [nan, nan, nan, nan, nan,
                                                   6.324555, 4.472136, 2.828427,
                                                   2.0]])
        """
        control = self.subpars.pars.control
        n = control.nmbwidths.value
        dh = numpy.diff(control.heights.values)
        dw = numpy.diff(self.subpars.sectorflowwidths.values)
        self.values = numpy.nan
        v = self.values
        v[:, -1] = 2.0
        for i, t in enumerate(
            itertools.chain([numpy.int64(0)], control.transitions.values)
        ):
            d = 2.0
            for j in range(n - 2, t - 1, -1):
                if dh[j] > 0.0:
                    d = 2.0 * math.sqrt(1.0 + math.pow(dw[i, j] / dh[j] / 2.0, 2.0))
                v[i, j] = d


class SectorFlowPerimeterDerivativesFromTable(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):
    """Sector-specific changes in the wetted perimeters of the subareas of the cross
    section involved in water routing with respect to water-level increases [m]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
    )
    DERIVEDPARAMETERS = (SectorFlowPerimetersFromTable,)

    def update(self) -> None:
        r"""Approximate the derivatives of the sector-specific flow perimeter based on
        simple difference quotients between subsequent measurement heights.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 6.0, 6.0, 9.0, 10.0)
        >>> flowwidths(2.0, 4.0, 4.0, 6.0, 8.0, 8.0, 12.0)
        >>> flowperimeters.approximate()
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowperimetersfromtable.update()
        >>> derived.sectorflowperimeterderivativesfromtable.update()
        >>> derived.sectorflowperimeterderivativesfromtable
        sectorflowperimeterderivativesfromtable([[2.236068, 2.0, 2.0, 2.0, 2.0,
                                                  2.0, 2.0],
                                                 [nan, nan, 2.236068, 2.0, 2.0,
                                                  2.0, 2.0],
                                                 [nan, nan, nan, 2.0, 2.0, 2.0,
                                                  2.0],
                                                 [nan, nan, nan, nan, nan,
                                                  4.472136, 2.0]])
        """

        derived = self.subpars
        control = derived.pars.control

        ns = control.nmbsectors.value
        ts = control.transitions.values
        dh = numpy.diff(control.heights.values)
        dp = numpy.diff(derived.sectorflowperimetersfromtable.values, axis=1)

        self.values = numpy.nan
        vs = self.values
        for i in range(ns):
            t = 0 if i == 0 else ts[i - 1]
            sel = dh[t:] > 0.0
            vs[i, t:-1][sel] = dp[i, t:][sel] / dh[t:][sel]
            vs[i, t:-1][~sel] = 2.0
        self.values[:, -1] = 2.0


class CrestHeightRegularisation(parametertools.Parameter):
    """Regularisation parameter related to the difference between the water depth and
    the crest height [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (wq_control.CrestHeightTolerance,)

    def update(self) -> None:
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following example in
        some detail:

        >>> from hydpy.models.wq import *
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> parameterstep()
        >>> crestheighttolerance(0.0)
        >>> derived.crestheightregularisation.update()
        >>> round_(smooth_logistic2(0.0, derived.crestheightregularisation))
        0.0
        >>> crestheighttolerance(0.0025)
        >>> derived.crestheightregularisation.update()
        >>> round_(smooth_logistic2(0.0025, derived.crestheightregularisation))
        0.00251
        """
        metapar = self.subpars.pars.control.crestheighttolerance.value
        self(smoothtools.calc_smoothpar_logistic2(1000.0 * metapar) / 1000.0)
