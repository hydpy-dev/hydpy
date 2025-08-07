# pylint: disable=missing-module-docstring
# import...
# ...from standard library
import itertools

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools

# ...from wq
from hydpy.models.wq import wq_control
from hydpy.models.wq import wq_variables


class BottomDepths(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The cumulated depth of a trapeze and its lower neighbours [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

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
    """The individual height of each trapeze [m].

    The highest trapeze has no upper neighbour and is thus infinitely high.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)

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
    """The total width of both side slopes of each trapeze.

    The highest trapeze has no upper neighbour and is thus infinitely high and
    potentially infinitely wide.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)

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
    """The individual area of each trapeze [m].

    The highest trapeze has no upper neighbour and is thus infinitely large.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)

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
    """Change of the perimeter of each trapeze relative to a water level increase
    within the trapeze's range [-].
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)

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
    TYPE, TIME, SPAN = float, None, (0.0, None)

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
        """Allocate the |FlowWidths| parts to the respective cross-section sectors.

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
        assert isinstance(flowwidths, wq_control.FlowWidths)
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
        """Allocate the |TotalWidths| parts to the respective cross-section sectors.

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
        assert isinstance(totalwidths, wq_control.TotalWidths)
        self._update(totalwidths)


class _SectorAreas(wq_variables.MixinSectorsAndWidths, parametertools.Parameter):
    TYPE, TIME, SPAN = float, None, (0.0, None)

    def _update(self, widths: SectorFlowWidths | SectorTotalWidths) -> None:
        h = self.subpars.pars.control.heights.values
        w = widths.values
        h_diff = numpy.diff(h)
        w_mean = (w[:, :-1] + w[:, 1:]) / 2.0
        self.values = 0.0
        self.values[:, 1:] = numpy.cumsum(h_diff * w_mean, axis=1)


class SectorFlowAreas(_SectorAreas):
    """The sector-specific wetted areas of those subareas of the cross section
    involved in water routing [m²]."""

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorFlowWidths,)

    def update(self) -> None:
        """Calculate the cumulative sum of the individual trapeze areas defined by the
        height-width pairs of the individual sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowareas.update()
        >>> derived.sectorflowareas
        sectorflowareas([[0.0, 6.0, 11.0, 11.0, 11.0, 17.0, 23.0, 29.0, 35.0],
                         [0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 16.0, 24.0, 32.0],
                         [0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 8.0, 12.0, 16.0],
                         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 11.0, 22.0]])
        """
        sectorflowwidths = self.subpars.sectorflowwidths
        assert isinstance(sectorflowwidths, SectorFlowWidths)
        self._update(sectorflowwidths)


class SectorTotalAreas(_SectorAreas):
    """The sector-specific wetted areas of the total cross section [m²]."""

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorTotalWidths,)

    def update(self) -> None:
        """Calculate the cumulative sum of the individual trapeze areas defined by the
        height-width pairs of the individual sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> totalwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectortotalwidths.update()
        >>> derived.sectortotalareas.update()
        >>> derived.sectortotalareas
        sectortotalareas([[0.0, 6.0, 11.0, 11.0, 11.0, 17.0, 23.0, 29.0, 35.0],
                          [0.0, 0.0, 0.0, 0.0, 0.0, 8.0, 16.0, 24.0, 32.0],
                          [0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 8.0, 12.0, 16.0],
                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 11.0, 22.0]])
        """
        sectortotalwidths = self.subpars.sectortotalwidths
        assert isinstance(sectortotalwidths, SectorTotalWidths)
        self._update(sectortotalwidths)


class SectorFlowPerimeters(
    wq_variables.MixinSectorsAndWidths, parametertools.Parameter
):
    """The sector-specific wetted perimeters of those subareas of the cross section
    involved in water routing [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (wq_control.Heights,)
    DERIVEDPARAMETERS = (SectorFlowWidths,)

    def update(self) -> None:
        """Calculate the cumulative sum of the individual trapeze perimeters defined by
        the height-width pairs of the individual sectors.

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowperimeters.update()
        >>> derived.sectorflowperimeters
        sectorflowperimeters([[2.0, 6.472136, 9.300563, 9.300563, 9.300563,
                               11.300563, 13.300563, 15.300563, 17.300563],
                              [0.0, 0.0, 0.0, 8.0, 8.0, 10.0, 12.0, 14.0, 16.0],
                              [0.0, 0.0, 0.0, 0.0, 4.0, 6.0, 8.0, 10.0, 12.0],
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
        for i, t in enumerate(itertools.chain([0], control.transitions.values)):
            self.values[i, t:] = w[i, t]
            self.values[i, t + 1 :] += numpy.cumsum(p[i, t:])


class CrestHeightRegularisation(parametertools.Parameter):
    """Regularisation parameter related to the difference between the water depth and
    the crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

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
