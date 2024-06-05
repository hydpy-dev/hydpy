# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.cythons import smoothutils
from hydpy.interfaces import dischargeinterfaces

# ...from wq
from hydpy.models.wq import wq_control
from hydpy.models.wq import wq_derived
from hydpy.models.wq import wq_factors
from hydpy.models.wq import wq_fluxes


class Calculate_Discharge_V1(modeltools.Method):
    r"""Calculate the discharge based on the water depth given in m according to
    :cite:t:`ref-Brauer2014` and return it in mm/T.

    Basic equation (discontinuous):
      .. math::
        q = q_{max} \cdot \left( \frac{max(h-h_{max}, \ 0)}{h_{max}-h_{min}} \right)^x
        \\ \\
        q = Discharge \\
        q_{max} = BankfullDischarge \\
        h = waterdepth \\
        h_{max} = ChannelDepth \\
        h_{min} = CrestHeight \\
        x = DischargeExponent

    Examples:

        >>> from hydpy.models.wq_walrus import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> channeldepth(5.0)
        >>> crestheight(2.0)
        >>> bankfulldischarge(2.0)
        >>> dischargeexponent(2.0)
        >>> from hydpy import round_
        >>> hs = 1.0, 1.9, 2.0, 2.1, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0

        Without smoothing:

        >>> crestheighttolerance(0.0)
        >>> derived.crestheightregularisation.update()
        >>> for h in hs:
        ...     round_([h, model.calculate_discharge_v1(h)])
        1.0, 0.0
        1.9, 0.0
        2.0, 0.0
        2.1, 0.001111
        3.0, 0.111111
        4.0, 0.444444
        5.0, 1.0
        6.0, 1.777778
        7.0, 2.777778
        8.0, 4.0

        Without smooting:

        >>> crestheighttolerance(0.1)
        >>> derived.crestheightregularisation.update()
        >>> for h in hs:
        ...     round_([h, model.calculate_discharge_v1(h)])
        1.0, 0.0
        1.9, 0.0
        2.0, 0.00001
        2.1, 0.001111
        3.0, 0.111111
        4.0, 0.444444
        5.0, 1.0
        6.0, 1.777778
        7.0, 2.777778
        8.0, 4.0
    """

    CONTROLPARAMETERS = (
        wq_control.ChannelDepth,
        wq_control.CrestHeight,
        wq_control.BankfullDischarge,
        wq_control.DischargeExponent,
    )
    DERIVEDPARAMETERS = (wq_derived.CrestHeightRegularisation,)

    @staticmethod
    def __call__(model: modeltools.Model, waterdepth: float) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess

        h: float = smoothutils.smooth_logistic2(
            waterdepth - con.crestheight, der.crestheightregularisation
        )
        f: float = (h / (con.channeldepth - con.crestheight)) ** con.dischargeexponent
        return con.bankfulldischarge * f


class Calc_WettedAreas_V1(modeltools.Method):
    r"""Calculate the wetted area for each trapeze range.

    Basic equation:
      .. math::
        WettedAreas_i = \begin{cases}
        0 &|\ d < 0 \\
        (W_B + S_S\cdot d) \cdot d &|\ 0 \leq d < H_T \\
        (W_B + W_S / 2) \cdot H_T + (W_B + W_S) \cdot (d - H_T) &|\ H_T \leq d \\
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        H_T = TrapezeHeights_i \\
        W_B = BottomWidths_i \\
        S_S = SideSlopes_i \\
        W_S = SlopeWidths_i

    Examples:

        The following convenience function executes |Calc_WettedAreas_V1| for different
        water depths and prints the resulting wetted areas:

        >>> from hydpy import print_values, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     derived.slopewidths.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_wettedareas_v1()
        ...         round_(d, end=": ")
        ...         print_values(factors.wettedareas.values)

        The first example deals with identical rectangular trapezes.  There are no
        differences except those due to the different bottom levels:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(0.0)
        >>> test()
        0.0: 0.0, 0.0, 0.0
        0.5: 1.0, 0.0, 0.0
        1.0: 2.0, 0.0, 0.0
        1.5: 3.0, 1.0, 0.0
        2.0: 4.0, 2.0, 0.0
        2.5: 5.0, 3.0, 1.0
        3.0: 6.0, 4.0, 2.0
        3.5: 7.0, 5.0, 3.0
        4.0: 8.0, 6.0, 4.0

        The second example deals with identical triangular trapezes.  Here, the heights
        of the individual trapezes also matter because they mark where the triangular
        shape switches to a rectangular shape:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(0.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 0.0, 0.0, 0.0
        0.5: 0.5, 0.0, 0.0
        1.0: 2.0, 0.0, 0.0
        1.5: 4.0, 0.5, 0.0
        2.0: 6.0, 2.0, 0.0
        2.5: 8.0, 4.0, 0.5
        3.0: 10.0, 6.0, 2.0
        3.5: 12.0, 8.0, 4.5
        4.0: 14.0, 10.0, 8.0

        The third example deals with identical "complete" trapezes by combining the
        first two geometries:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 0.0, 0.0, 0.0
        0.5: 1.5, 0.0, 0.0
        1.0: 4.0, 0.0, 0.0
        1.5: 7.0, 1.5, 0.0
        2.0: 10.0, 4.0, 0.0
        2.5: 13.0, 7.0, 1.5
        3.0: 16.0, 10.0, 4.0
        3.5: 19.0, 13.0, 7.5
        4.0: 22.0, 16.0, 12.0

        The fourth example mixes three different geometries:

        >>> bottomlevels(1.0, 3.0, 4.0)
        >>> bottomwidths(2.0, 0.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> test()
        0.0: 0.0, 0.0, 0.0
        0.5: 1.0, 0.0, 0.0
        1.0: 2.0, 0.0, 0.0
        1.5: 3.0, 0.0, 0.0
        2.0: 4.0, 0.0, 0.0
        2.5: 5.0, 0.5, 0.0
        3.0: 6.0, 2.0, 0.0
        3.5: 7.0, 4.0, 1.5
        4.0: 8.0, 6.0, 4.0
    """

    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
    )
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (wq_factors.WettedAreas,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        for i in range(con.nmbtrapezes):
            d: float = fac.waterdepth - der.bottomdepths[i]
            if d < 0.0:
                fac.wettedareas[i] = 0.0
            else:
                ht: float = der.trapezeheights[i]
                wb: float = con.bottomwidths[i]
                if d < ht:
                    ss: float = con.sideslopes[i]
                    fac.wettedareas[i] = (wb + ss * d) * d
                else:
                    ws: float = der.slopewidths[i]
                    fac.wettedareas[i] = (wb + ws / 2.0) * ht + (wb + ws) * (d - ht)


class Calc_WettedArea_V1(modeltools.Method):
    r"""Sum up the individual trapeze ranges' wetted areas.

    Basic equation:
      :math:`WettedArea = \sum_{i=1}^{NmbTrapezes} WettedAreas_i`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> factors.wettedareas(2.0, 3.0, 1.0)
        >>> model.calc_wettedarea_v1()
        >>> factors.wettedarea
        wettedarea(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbTrapezes,)
    REQUIREDSEQUENCES = (wq_factors.WettedAreas,)
    RESULTSEQUENCES = (wq_factors.WettedArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.wettedarea = 0.0
        for i in range(con.nmbtrapezes):
            fac.wettedarea += fac.wettedareas[i]


class Calc_WettedPerimeters_V1(modeltools.Method):
    r"""Calculate the wetted perimeter for each trapeze range.

    Basic equation:
      .. math::
        WettedPerimeters_i = \begin{cases}
        0 &|\ d < 0 \\
        W_B + 2 \cdot d \cdot \sqrt{S_S^2 + 1} &|\ 0 \leq d < H_T \\
        W_B + 2 \cdot H_T \cdot \sqrt{S_S^2 + 1} + 2 \cdot (d - H_T) &|\ H_T \leq d \\
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        H_T = TrapezeHeights_i \\
        W_B = BottomWidths_i \\
        S_S = SideSlopes_i

    Examples:

        The following convenience function executes |Calc_WettedPerimeters_V1| for
        different water depths and prints the resulting wetted perimeters:

        >>> from hydpy import print_values, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_wettedperimeters_v1()
        ...         round_(d, end=": ")
        ...         print_values(factors.wettedperimeters.values)

        The first example deals with identical rectangular trapezes.  Note that method
        |Calc_WettedPerimeters_V1| adds the contact surface between two adjacent trapeze
        ranges only to the wetted perimeter of the inner one:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(0.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 3.0, 0.0, 0.0
        1.0: 4.0, 2.0, 0.0
        1.5: 5.0, 3.0, 0.0
        2.0: 6.0, 4.0, 2.0
        2.5: 7.0, 5.0, 3.0
        3.0: 8.0, 6.0, 4.0
        3.5: 9.0, 7.0, 5.0
        4.0: 10.0, 8.0, 6.0

        The second example deals with identical triangular trapezes.  Here, the heights
        of the individual trapezes also matter because they mark where the triangular
        shape switches to a rectangular shape:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(0.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 0.0, 0.0, 0.0
        0.5: 2.236068, 0.0, 0.0
        1.0: 4.472136, 0.0, 0.0
        1.5: 5.472136, 2.236068, 0.0
        2.0: 6.472136, 4.472136, 0.0
        2.5: 7.472136, 5.472136, 2.236068
        3.0: 8.472136, 6.472136, 4.472136
        3.5: 9.472136, 7.472136, 6.708204
        4.0: 10.472136, 8.472136, 8.944272

        The third example deals with identical "complete" trapezes by combining the
        first two geometries:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 4.236068, 0.0, 0.0
        1.0: 6.472136, 2.0, 0.0
        1.5: 7.472136, 4.236068, 0.0
        2.0: 8.472136, 6.472136, 2.0
        2.5: 9.472136, 7.472136, 4.236068
        3.0: 10.472136, 8.472136, 6.472136
        3.5: 11.472136, 9.472136, 8.708204
        4.0: 12.472136, 10.472136, 10.944272

        The fourth example mixes three different geometries:

        >>> bottomlevels(1.0, 3.0, 4.0)
        >>> bottomwidths(2.0, 0.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 3.0, 0.0, 0.0
        1.0: 4.0, 0.0, 0.0
        1.5: 5.0, 0.0, 0.0
        2.0: 6.0, 0.0, 0.0
        2.5: 7.0, 2.236068, 0.0
        3.0: 8.0, 4.472136, 2.0
        3.5: 9.0, 5.472136, 4.236068
        4.0: 10.0, 6.472136, 6.472136
    """

    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (wq_derived.BottomDepths, wq_derived.TrapezeHeights)
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (wq_factors.WettedPerimeters,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        for i in range(con.nmbtrapezes):
            d: float = fac.waterdepth - der.bottomdepths[i]
            if d < 0.0:
                fac.wettedperimeters[i] = 0.0
            else:
                ht: float = der.trapezeheights[i]
                wb: float = con.bottomwidths[i]
                ss: float = con.sideslopes[i]
                if d < ht:
                    fac.wettedperimeters[i] = wb + 2.0 * d * (ss**2.0 + 1.0) ** 0.5
                else:
                    fac.wettedperimeters[i] = (
                        wb + 2.0 * ht * (ss**2.0 + 1.0) ** 0.5 + 2.0 * (d - ht)
                    )


class Calc_WettedPerimeterDerivatives_V1(modeltools.Method):
    r"""Calculate the change in the wetted perimeter of each trapeze range with respect
    to the water level increase.

    Basic equation:
      .. math::
        WettedPerimeterDerivatives_i = \begin{cases}
        0 &|\ d < 0 \\
        P' &|\ 0 \leq d < H_T \\
        2 &|\ H_T \leq d \\
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        H_T = TrapezeHeights_i \\
        P' = PerimeterDerivatives_i

    Examples:

        The following convenience function executes |Calc_WettedPerimeterDerivatives_V1|
        for different water depths and prints the resulting wetted perimeters:

        >>> from hydpy import print_values, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     derived.perimeterderivatives.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_wettedperimeterderivatives_v1()
        ...         round_(d, end=": ")
        ...         print_values(factors.wettedperimeterderivatives.values)

        The first example deals with identical rectangular trapezes.  Note that method
        |Calc_WettedPerimeterDerivatives_V1| adds the contact surface increase between
        two adjacent trapeze ranges only to the wetted perimeter derivative of the inner
        one:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(0.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 2.0, 0.0, 0.0
        1.0: 2.0, 2.0, 0.0
        1.5: 2.0, 2.0, 0.0
        2.0: 2.0, 2.0, 2.0
        2.5: 2.0, 2.0, 2.0
        3.0: 2.0, 2.0, 2.0
        3.5: 2.0, 2.0, 2.0
        4.0: 2.0, 2.0, 2.0

        The second example deals with identical triangular trapezes.  Here, the heights
        of the individual trapezes also matter because they mark where the triangular
        shape switches to a rectangular shape:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(0.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 4.472136, 0.0, 0.0
        0.5: 4.472136, 0.0, 0.0
        1.0: 2.0, 4.472136, 0.0
        1.5: 2.0, 4.472136, 0.0
        2.0: 2.0, 2.0, 4.472136
        2.5: 2.0, 2.0, 4.472136
        3.0: 2.0, 2.0, 4.472136
        3.5: 2.0, 2.0, 4.472136
        4.0: 2.0, 2.0, 4.472136

        The third example deals with identical "complete" trapezes by combining the
        first two geometries:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 4.472136, 0.0, 0.0
        0.5: 4.472136, 0.0, 0.0
        1.0: 2.0, 4.472136, 0.0
        1.5: 2.0, 4.472136, 0.0
        2.0: 2.0, 2.0, 4.472136
        2.5: 2.0, 2.0, 4.472136
        3.0: 2.0, 2.0, 4.472136
        3.5: 2.0, 2.0, 4.472136
        4.0: 2.0, 2.0, 4.472136

        The fourth example mixes three different geometries:

        >>> bottomlevels(1.0, 3.0, 4.0)
        >>> bottomwidths(2.0, 0.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 2.0, 0.0, 0.0
        1.0: 2.0, 0.0, 0.0
        1.5: 2.0, 0.0, 0.0
        2.0: 2.0, 4.472136, 0.0
        2.5: 2.0, 4.472136, 0.0
        3.0: 2.0, 2.0, 4.472136
        3.5: 2.0, 2.0, 4.472136
        4.0: 2.0, 2.0, 4.472136
    """

    CONTROLPARAMETERS = (wq_control.NmbTrapezes,)
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.PerimeterDerivatives,
    )
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (wq_factors.WettedPerimeterDerivatives,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        for i in range(con.nmbtrapezes):
            d: float = fac.waterdepth - der.bottomdepths[i]
            if d < 0.0:
                fac.wettedperimeterderivatives[i] = 0.0
            elif d < der.trapezeheights[i]:
                fac.wettedperimeterderivatives[i] = der.perimeterderivatives[i]
            else:
                fac.wettedperimeterderivatives[i] = 2.0


class Calc_SurfaceWidths_V1(modeltools.Method):
    r"""Calculate the surface width for each trapeze range.

    Basic equation:
      .. math::
        SurfaceWidths_i = \begin{cases}
        0 &|\ d < 0 \\
        W_B + 2 \cdot S_S \cdot d &|\ 0 \leq d < H_T \\
        W_B + W_S &|\ H_T \leq d \\
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        H_T = TrapezeHeights_i \\
        W_B = BottomWidths_i \\
        S_S = SideSlopes_i \\
        W_S = SlopeWidth_i

    Example:

        The following convenience function executes |Calc_SurfaceWidths_V1| for
        different water depths and prints the surface widths:

        >>> from hydpy import print_values, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     derived.slopewidths.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_surfacewidths_v1()
        ...         round_(d, end=": ")
        ...         print_values(factors.surfacewidths.values)

        The first example deals with identical rectangular trapezes.  There are no
        differences except those due to the different bottom levels:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(0.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 2.0, 0.0, 0.0
        1.0: 2.0, 2.0, 0.0
        1.5: 2.0, 2.0, 0.0
        2.0: 2.0, 2.0, 2.0
        2.5: 2.0, 2.0, 2.0
        3.0: 2.0, 2.0, 2.0
        3.5: 2.0, 2.0, 2.0
        4.0: 2.0, 2.0, 2.0

        The second example deals with identical triangular trapezes.  Here, the heights
        of the individual trapezes also matter because they mark where the triangular
        shape switches to a rectangular shape:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(0.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 0.0, 0.0, 0.0
        0.5: 2.0, 0.0, 0.0
        1.0: 4.0, 0.0, 0.0
        1.5: 4.0, 2.0, 0.0
        2.0: 4.0, 4.0, 0.0
        2.5: 4.0, 4.0, 2.0
        3.0: 4.0, 4.0, 4.0
        3.5: 4.0, 4.0, 6.0
        4.0: 4.0, 4.0, 8.0

        The third example deals with identical "complete" trapezes by combining the
        first two geometries:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(2.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 4.0, 0.0, 0.0
        1.0: 6.0, 2.0, 0.0
        1.5: 6.0, 4.0, 0.0
        2.0: 6.0, 6.0, 2.0
        2.5: 6.0, 6.0, 4.0
        3.0: 6.0, 6.0, 6.0
        3.5: 6.0, 6.0, 8.0
        4.0: 6.0, 6.0, 10.0

        The fourth example mixes three different geometries:

        >>> bottomlevels(1.0, 3.0, 4.0)
        >>> bottomwidths(2.0, 0.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> test()
        0.0: 2.0, 0.0, 0.0
        0.5: 2.0, 0.0, 0.0
        1.0: 2.0, 0.0, 0.0
        1.5: 2.0, 0.0, 0.0
        2.0: 2.0, 0.0, 0.0
        2.5: 2.0, 2.0, 0.0
        3.0: 2.0, 4.0, 2.0
        3.5: 2.0, 4.0, 4.0
        4.0: 2.0, 4.0, 6.0
    """

    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
    )
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (wq_factors.SurfaceWidths,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        for i in range(con.nmbtrapezes):
            d: float = fac.waterdepth - der.bottomdepths[i]
            if d < 0.0:
                fac.surfacewidths[i] = 0.0
            elif d < der.trapezeheights[i]:
                fac.surfacewidths[i] = con.bottomwidths[i] + 2.0 * con.sideslopes[i] * d
            else:
                fac.surfacewidths[i] = con.bottomwidths[i] + der.slopewidths[i]


class Calc_SurfaceWidth_V1(modeltools.Method):
    r"""Sum the individual trapeze ranges' surface widths.

    Basic equation:
      :math:`SurfaceWidth = \sum_{i=1}^{NmbTrapezes} SurfaceWidths_i`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomslope(0.01)
        >>> factors.surfacewidths(2.0, 3.0, 1.0)
        >>> model.calc_surfacewidth_v1()
        >>> factors.surfacewidth
        surfacewidth(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbTrapezes,)
    REQUIREDSEQUENCES = (wq_factors.SurfaceWidths,)
    RESULTSEQUENCES = (wq_factors.SurfaceWidth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.surfacewidth = 0.0
        for i in range(con.nmbtrapezes):
            fac.surfacewidth += fac.surfacewidths[i]


class Calc_Discharges_V1(modeltools.Method):
    r"""Calculate the discharge for each trapeze range.

    Basic equation:
      .. math::
        Discharges_i = \begin{cases}
        0 &|\ d < 0 \\
        C \cdot A^{5/3} \cdot P^{-2/3} \cdot \sqrt{S_B} &|\ 0 \leq d
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        C = StricklerCoefficient_i \\
        A = WettedAreas_i \\
        P = WettedPerimeters_i \\
        S_B = BottomSlope

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(4)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0, 60.0, 80.0)
        >>> derived.bottomdepths = 1.0, 2.0, 3.0, 4.0
        >>> factors.wettedareas = 1.0, 4.0, 8.0, 16.0
        >>> factors.wettedperimeters = 2.0, 4.0, 6.0, 8.0
        >>> factors.waterdepth = 4.0
        >>> model.calc_discharges_v1()
        >>> fluxes.discharges
        discharges(1.259921, 16.0, 58.147859, 0.0)
    """

    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomSlope,
        wq_control.StricklerCoefficients,
    )
    DERIVEDPARAMETERS = (wq_derived.BottomDepths,)
    REQUIREDSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WettedAreas,
        wq_factors.WettedPerimeters,
    )
    RESULTSEQUENCES = (wq_fluxes.Discharges,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for i in range(con.nmbtrapezes):
            if fac.waterdepth > der.bottomdepths[i]:
                flu.discharges[i] = (
                    con.stricklercoefficients[i]
                    * con.bottomslope**0.5
                    * fac.wettedareas[i] ** (5.0 / 3.0)
                    / fac.wettedperimeters[i] ** (2.0 / 3.0)
                )
            else:
                flu.discharges[i] = 0.0


class Calc_Discharge_V2(modeltools.Method):
    r"""Sum the individual trapeze ranges' discharges.

    Basic equation:
      :math:`Discharge = \sum_{i=1}^{NmbTrapezes} Discharges_i`

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomslope(0.01)
        >>> fluxes.discharges(2.0, 3.0, 1.0)
        >>> model.calc_discharge_v2()
        >>> fluxes.discharge
        discharge(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbTrapezes,)
    REQUIREDSEQUENCES = (wq_fluxes.Discharges,)
    RESULTSEQUENCES = (wq_fluxes.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.discharge = 0.0
        for i in range(con.nmbtrapezes):
            flu.discharge += flu.discharges[i]


class Calc_DischargeDerivatives_V1(modeltools.Method):
    r"""Calculate the discharge change for each trapeze range with respect to a water
    level increase.

    Basic equation:
     .. math::
        DischargeDerivatives_i = \begin{cases}
        0 &|\ d < 0 \\
        C \cdot
        (A / P)^{5/3} \cdot \frac{5 \cdot P \cdot A' - 2 \cdot A \cdot P'}{3 \cdot P}
        \cdot \sqrt{S_B} &|\ 0 \leq d
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        C = StricklerCoefficient_i \\
        A = WettedAreas_i \\
        A' = SurfaceWidth_i \\
        P = WettedPerimeters_i \\
        P' = WettedPerimeterDerivatives_i \\
        S_B = BottomSlope

    Example:

        The given basic equation assumes that the wetted area, the wetted perimeter,
        and their derivatives are calculated via methods |Calc_WettedAreas_V1|,
        |Calc_SurfaceWidths_V1|, |Calc_WettedPerimeters_V1|, and
        |Calc_WettedPerimeterDerivatives_V1|.  Hence, we apply these methods and check
        that, after also executing |Calc_DischargeDerivatives_V1|, the results are
        sufficiently similar to the numerical approximations gained when applying
        |NumericalDifferentiator| to the mentioned methods and method
        |Calc_Discharges_V1|:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(4)
        >>> bottomlevels(1.0, 3.0, 4.0, 5.0)
        >>> bottomwidths(2.0, 0.0, 2.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0, 2.0)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0, 60.0, 60.0)
        >>> factors.waterdepth = 3.5
        >>> derived.bottomdepths.update()
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> derived.perimeterderivatives.update()
        >>> model.calc_wettedareas_v1()
        >>> model.calc_surfacewidths_v1()
        >>> model.calc_wettedperimeters_v1()
        >>> model.calc_wettedperimeterderivatives_v1()
        >>> model.calc_dischargederivatives_v1()
        >>> factors.dischargederivatives
        dischargederivatives(3.884141, 18.475494, 16.850223, 0.0)

        >>> from hydpy import NumericalDifferentiator, pub
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=factors.waterdepth,
        ...     ysequences=[fluxes.discharges],
        ...     methods=[model.calc_wettedareas_v1,
        ...              model.calc_surfacewidths_v1,
        ...              model.calc_wettedperimeters_v1,
        ...              model.calc_wettedperimeterderivatives_v1,
        ...              model.calc_discharges_v1],
        ...     dx=1e-8)
        >>> with pub.options.reprdigits(5):
        ...     numdiff()
        d_discharges/d_waterdepth: 3.88414, 18.47549, 16.85022, 0.0
    """

    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomSlope,
        wq_control.StricklerCoefficients,
    )
    DERIVEDPARAMETERS = (wq_derived.BottomDepths,)
    REQUIREDSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WettedAreas,
        wq_factors.WettedPerimeters,
        wq_factors.WettedPerimeterDerivatives,
        wq_factors.SurfaceWidths,
    )
    RESULTSEQUENCES = (wq_factors.DischargeDerivatives,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        for i in range(con.nmbtrapezes):
            if fac.waterdepth > der.bottomdepths[i]:
                a: float = fac.wettedareas[i]
                da: float = fac.surfacewidths[i]
                p: float = fac.wettedperimeters[i]
                dp: float = fac.wettedperimeterderivatives[i]
                fac.dischargederivatives[i] = (
                    con.stricklercoefficients[i]
                    * con.bottomslope**0.5
                    * (a / p) ** (2.0 / 3.0)
                    * (5.0 * p * da - 2.0 * a * dp)
                    / (3.0 * p)
                )
            else:
                fac.dischargederivatives[i] = 0.0


class Calc_DischargeDerivative_V1(modeltools.Method):
    r"""Sum the individual trapeze ranges' discharge derivatives.

    Basic equation:
      :math:`DischargeDerivative = \sum_{i=1}^{NmbTrapezes} DischargeDerivatives_i`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomslope(0.01)
        >>> factors.dischargederivatives(2.0, 3.0, 1.0)
        >>> model.calc_dischargederivative_v1()
        >>> factors.dischargederivative
        dischargederivative(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbTrapezes,)
    REQUIREDSEQUENCES = (wq_factors.DischargeDerivatives,)
    RESULTSEQUENCES = (wq_factors.DischargeDerivative,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.dischargederivative = 0.0
        for i in range(con.nmbtrapezes):
            fac.dischargederivative += fac.dischargederivatives[i]


class Calc_Celerity_V1(modeltools.Method):
    r"""Calculate the kinematic wave celerity.

    Basic equation:
      :math:`Celerity = \frac{DischargeDerivative}{SurfaceWidth}`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.dischargederivative = 6.0
        >>> factors.surfacewidth = 2.0
        >>> model.calc_celerity_v1()
        >>> factors.celerity
        celerity(3.0)
    """

    REQUIREDSEQUENCES = (wq_factors.DischargeDerivative, wq_factors.SurfaceWidth)
    RESULTSEQUENCES = (wq_factors.Celerity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        fac.celerity = fac.dischargederivative / fac.surfacewidth


class Process_V1(modeltools.AutoMethod):
    """Process all possible output data according to the current water depth/water
    level."""

    SUBMETHODS = (
        Calc_WettedAreas_V1,
        Calc_WettedArea_V1,
        Calc_WettedPerimeters_V1,
        Calc_WettedPerimeterDerivatives_V1,
        Calc_SurfaceWidths_V1,
        Calc_SurfaceWidth_V1,
        Calc_Discharges_V1,
        Calc_Discharge_V2,
        Calc_DischargeDerivatives_V1,
        Calc_DischargeDerivative_V1,
        Calc_Celerity_V1,
    )
    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
        wq_control.StricklerCoefficients,
        wq_control.BottomSlope,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
        wq_derived.PerimeterDerivatives,
    )
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (
        wq_factors.WettedAreas,
        wq_factors.WettedArea,
        wq_factors.WettedPerimeters,
        wq_factors.WettedPerimeterDerivatives,
        wq_factors.SurfaceWidths,
        wq_factors.SurfaceWidth,
        wq_factors.DischargeDerivatives,
        wq_factors.DischargeDerivative,
        wq_factors.Celerity,
        wq_fluxes.Discharges,
        wq_fluxes.Discharge,
    )


class Set_WaterDepth_V1(modeltools.Method):
    """Set the water depth in m and adjust the current water level.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> model.set_waterdepth_v1(2.0)
        >>> factors.waterdepth
        waterdepth(2.0)
        >>> factors.waterlevel
        waterlevel(3.0)
    """

    CONTROLPARAMETERS = (wq_control.BottomLevels,)
    RESULTSEQUENCES = (wq_factors.WaterDepth, wq_factors.WaterLevel)

    @staticmethod
    def __call__(model: modeltools.Model, waterdepth: float) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.waterdepth = waterdepth
        fac.waterlevel = waterdepth + con.bottomlevels[0]


class Set_WaterLevel_V1(modeltools.Method):
    """Set the water level in m and adjust the current water depth.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> model.set_waterlevel_v1(3.0)
        >>> factors.waterdepth
        waterdepth(2.0)
        >>> factors.waterlevel
        waterlevel(3.0)
    """

    CONTROLPARAMETERS = (wq_control.BottomLevels,)
    RESULTSEQUENCES = (wq_factors.WaterDepth, wq_factors.WaterLevel)

    @staticmethod
    def __call__(model: modeltools.Model, waterlevel: float) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.waterlevel = waterlevel
        fac.waterdepth = waterlevel - con.bottomlevels[0]


class Get_WettedArea_V1(modeltools.Method):
    """Get the wetted area in m².

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.wettedarea(2.0)
        >>> model.get_wettedarea_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.WettedArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.wettedarea


class Get_SurfaceWidth_V1(modeltools.Method):
    """Get the surface width in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.surfacewidth(2.0)
        >>> model.get_surfacewidth_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.SurfaceWidth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.surfacewidth


class Get_Discharge_V1(modeltools.Method):
    """Get the discharge in m³/s.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> fluxes.discharge(2.0)
        >>> model.get_discharge_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_fluxes.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.discharge


class Get_Celerity_V1(modeltools.Method):
    """Get the wave celerity in m/s.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.celerity(2.0)
        >>> model.get_celerity_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.Celerity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.celerity


class Model(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """The HydPy-WQ base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        Calculate_Discharge_V1,
        Set_WaterDepth_V1,
        Set_WaterLevel_V1,
        Process_V1,
        Get_WettedArea_V1,
        Get_SurfaceWidth_V1,
        Get_Discharge_V1,
        Get_Celerity_V1,
    )
    ADD_METHODS = (
        Calc_WettedAreas_V1,
        Calc_WettedArea_V1,
        Calc_WettedPerimeters_V1,
        Calc_WettedPerimeterDerivatives_V1,
        Calc_SurfaceWidths_V1,
        Calc_SurfaceWidth_V1,
        Calc_Discharges_V1,
        Calc_Discharge_V2,
        Calc_DischargeDerivatives_V1,
        Calc_DischargeDerivative_V1,
        Calc_Celerity_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class Base_DischargeModel_V2(dischargeinterfaces.DischargeModel_V2):
    """Base class for HydPy-WQ models that comply with the |DischargeModel_V2| submodel
    interface."""

    @importtools.define_targetparameter(wq_control.ChannelDepth)
    def prepare_channeldepth(self, channeldepth: float) -> None:
        """Set the channel depth in m.

        >>> from hydpy.models.wq_walrus import *
        >>> parameterstep()
        >>> model.prepare_channeldepth(2.0)
        >>> channeldepth
        channeldepth(2.0)
        """
        self.parameters.control.channeldepth(channeldepth)

    @importtools.define_targetparameter(wq_control.CrestHeightTolerance)
    def prepare_tolerance(self, tolerance: float) -> None:
        """Set the depth-related smoothing parameter in m.

        >>> from hydpy.models.wq_walrus import *
        >>> parameterstep()
        >>> model.prepare_tolerance(2.0)
        >>> crestheighttolerance
        crestheighttolerance(2.0)
        """
        self.parameters.control.crestheighttolerance(tolerance)
