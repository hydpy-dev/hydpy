# pylint: disable=missing-module-docstring

# imports...
# ...from site-packages
from matplotlib import pyplot

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.cythons import smoothutils
from hydpy.interfaces import dischargeinterfaces

# ...from wq
from hydpy.models.wq import wq_control
from hydpy.models.wq import wq_derived
from hydpy.models.wq import wq_factors
from hydpy.models.wq import wq_fluxes
from hydpy.models.wq import wq_aides


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


class Calc_WaterDepth_V1(modeltools.Method):
    r"""Calculate the water depth based on the current water level.

    Basic equation:
      .. math::
        WaterDepth = max(WaterLevel - BottomLevels_{\,0}, \ 0)

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(2.0, 3.0)
        >>> factors.waterlevel(6.0)
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(4.0)

        >>> factors.waterlevel(1.0)
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(0.0)
    """

    CONTROLPARAMETERS = (wq_control.BottomLevels,)
    REQUIREDSEQUENCES = (wq_factors.WaterLevel,)
    RESULTSEQUENCES = (wq_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.waterdepth = max(fac.waterlevel - con.bottomlevels[0], 0.0)


class Calc_WaterDepth_V2(modeltools.Method):
    r"""Calculate the water depth based on the current wetted area.

    Basic equation:
      .. math::
        WaterDepth = \begin{cases}
        a / w &|\ s = 0 \\
        \left( \sqrt{4 \cdot s \cdot a + w^2} - w \right) / (2 \cdot s) &|\ s > 0 \\
        \end{cases}
        \\
        a = WettedArea \\
        w = BottomWidth \\
        s = SideSlope

    Examples:

        One can understand |Calc_WaterDepth_V2| as an inverse method of
        |Calc_WettedAreas_V1| (and |Calc_WettedArea_V1|).  Hence, the following
        convenience function allows the creation of examples that are directly
        comparable to those on method |Calc_WettedAreas_V1|:

        >>> from hydpy import print_vector, round_
        >>> def test(*wettedareas):
        ...     derived.trapezeheights.update()
        ...     derived.slopewidths.update()
        ...     derived.trapezeareas.update()
        ...     for a in wettedareas:
        ...         factors.wettedarea = a
        ...         model.calc_waterdepth_v2()
        ...         print_vector([a, factors.waterdepth.value])

        The first example deals with identical rectangular trapezes.  We pass different
        wetted areas to the test function.  These are the sums of the wetted areas of
        the different trapeze ranges calculated in the first example on method
        |Calc_WettedAreas_V1|.  As expected, method |Calc_WaterDepth_V2| finds the
        water depths used as input data for this example.  However, note that negative
        wetted areas result in zero water depths:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(0.0)
        >>> factors.wettedarea = 0.0
        >>> test(-0.5, 0.0, 1.0, 2.0, 4.0, 6.0, 9.0, 12.0, 15.0, 18.0)
        -0.5, 0.0
        0.0, 0.0
        1.0, 0.5
        2.0, 1.0
        4.0, 1.5
        6.0, 2.0
        9.0, 2.5
        12.0, 3.0
        15.0, 3.5
        18.0, 4.0

        The second example deals with identical triangular trapezes and corresponds to
        the second example on method |Calc_WettedAreas_V1|:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(0.0)
        >>> sideslopes(2.0)
        >>> test(-0.5, 0.0, 0.5, 2.0, 4.5, 8.0, 12.5, 18.0, 24.5, 32.0)
        -0.5, 0.0
        0.0, 0.0
        0.5, 0.5
        2.0, 1.0
        4.5, 1.5
        8.0, 2.0
        12.5, 2.5
        18.0, 3.0
        24.5, 3.5
        32.0, 4.0

        The third example deals with identical "complete" trapezes and corresponds to
        the third example on method |Calc_WettedAreas_V1|:

        >>> bottomlevels(1.0, 2.0, 3.0)
        >>> bottomwidths(2.0)
        >>> sideslopes(2.0)
        >>> test(-0.5, 0.0, 1.5, 4.0, 8.5, 14.0, 21.5, 30.0, 39.5, 50.0)
        -0.5, 0.0
        0.0, 0.0
        1.5, 0.5
        4.0, 1.0
        8.5, 1.5
        14.0, 2.0
        21.5, 2.5
        30.0, 3.0
        39.5, 3.5
        50.0, 4.0

        The fourth example mixes three different geometries and corresponds to the
        fourth example on method |Calc_WettedAreas_V1|:

        >>> bottomlevels(1.0, 3.0, 4.0)
        >>> bottomwidths(2.0, 0.0, 2.0)
        >>> sideslopes(0.0, 2.0, 2.0)
        >>> test(-0.5, 0.0, 1.0, 2.0, 3.0, 4.0, 5.5, 8.0, 12.5, 18.0)
        -0.5, 0.0
        0.0, 0.0
        1.0, 0.5
        2.0, 1.0
        3.0, 1.5
        4.0, 2.0
        5.5, 2.5
        8.0, 3.0
        12.5, 3.5
        18.0, 4.0
    """

    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
        wq_derived.TrapezeAreas,
    )
    REQUIREDSEQUENCES = (wq_factors.WettedArea,)
    RESULTSEQUENCES = (wq_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        a: float = fac.wettedarea
        d: float = 0.0
        w: float = 0.0
        for i in range(con.nmbtrapezes):
            if a > der.trapezeareas[i]:
                a -= der.trapezeareas[i]
                d += der.trapezeheights[i]
                w += con.bottomwidths[i] + der.slopewidths[i]
            else:
                if a > 0.0:
                    w += con.bottomwidths[i]
                    ss: float = con.sideslopes[i]
                    if ss > 1e-10:
                        d += ((4.0 * ss * a + w**2.0) ** 0.5 - w) / (2.0 * ss)
                    else:
                        d += a / w
                fac.waterdepth = d
                break


class Calc_WaterDepth_V3(modeltools.Method):
    r"""Calculate the water depth based on the current water level.

    Basic equation:
      .. math::m
        WaterDepth = max(WaterLevel - Heights_0, \ 0)

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(2)
        >>> heights(2.0, 3.0)
        >>> factors.waterlevel(6.0)
        >>> model.calc_waterdepth_v3()
        >>> factors.waterdepth
        waterdepth(4.0)

        >>> factors.waterlevel(1.0)
        >>> model.calc_waterdepth_v3()
        >>> factors.waterdepth
        waterdepth(0.0)
    """

    CONTROLPARAMETERS = (wq_control.Heights,)
    REQUIREDSEQUENCES = (wq_factors.WaterLevel,)
    RESULTSEQUENCES = (wq_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.waterdepth = max(fac.waterlevel - con.heights[0], 0.0)


class Calc_WaterLevel_V1(modeltools.Method):
    r"""Calculate the water level based on the current water depth.

    Basic equation:
      .. math::
        WaterLevel = WaterDepth + BottomLevels_{\,0}

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(2.0, 3.0)
        >>> factors.waterdepth(4.0)
        >>> model.calc_waterlevel_v1()
        >>> factors.waterlevel
        waterlevel(6.0)
    """

    CONTROLPARAMETERS = (wq_control.BottomLevels,)
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (wq_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.waterlevel = fac.waterdepth + con.bottomlevels[0]


class Calc_WaterLevel_V2(modeltools.Method):
    """Calculate the water level based on the current water depth.

    Basic equation:
      .. math::
        WaterLevel = WaterDepth + Heights_0

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(2)
        >>> heights(2.0, 3.0)
        >>> factors.waterdepth(4.0)
        >>> model.calc_waterlevel_v2()
        >>> factors.waterlevel
        waterlevel(6.0)
    """

    CONTROLPARAMETERS = (wq_control.Heights,)
    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)
    RESULTSEQUENCES = (wq_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.waterlevel = fac.waterdepth + con.heights[0]


class Calc_Index_Excess_Weight_V1(modeltools.Method):
    r"""Calculate some aide sequences that help to ease other calculations.

    Basic equations:
      .. math::
        E = L - H_i \\
        w = E / (H_{i+1} - H_i)
        \\ \\
        L = WaterLevel \\
        H = Heights \\
        i = Index \\
        E = Excess \\
        w = Weight

    Example:

        |Index| corresponds to the measured height directly equal to or below the
        current height (and is zero if the current height is smaller than the lowest
        measured height).  |Excess| corresponds to the difference between the actual
        and the indexed height. |Weight| serves as a linear weighting factor and grows
        from zero to one when increasing the current height from the next-lower to the
        next-upper height (and is |numpy.nan| in case there is no next-upper height):

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(3)
        >>> heights(1.0, 5.0, 7.0)
        >>> from hydpy import print_vector
        >>> for waterlevel in range(10):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     print_vector([waterlevel, aides.index.value, aides.excess.value,
        ...                   aides.weight.value])
        0, 0.0, 0.0, 0.0
        1, 0.0, 0.0, 0.0
        2, 0.0, 1.0, 0.25
        3, 0.0, 2.0, 0.5
        4, 0.0, 3.0, 0.75
        5, 1.0, 0.0, 0.0
        6, 1.0, 1.0, 0.5
        7, 2.0, 0.0, nan
        8, 2.0, 1.0, nan
        9, 2.0, 2.0, nan
    """

    CONTROLPARAMETERS = (wq_control.NmbWidths, wq_control.Heights)
    REQUIREDSEQUENCES = (wq_factors.WaterLevel,)
    RESULTSEQUENCES = (wq_aides.Index, wq_aides.Weight, wq_aides.Excess)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        if fac.waterlevel <= con.heights[0]:
            aid.index = 0.0
            aid.weight = 0.0
            aid.excess = 0.0
        else:
            for i in range(con.nmbwidths - 1):
                if fac.waterlevel < con.heights[i + 1]:
                    aid.index = i
                    aid.excess = fac.waterlevel - con.heights[i]
                    aid.weight = aid.excess / (con.heights[i + 1] - con.heights[i])
                    break
            else:
                aid.index = con.nmbwidths - 1
                aid.excess = fac.waterlevel - con.heights[con.nmbwidths - 1]
                aid.weight = modelutils.nan


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

        >>> from hydpy import print_vector, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     derived.slopewidths.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_wettedareas_v1()
        ...         round_(d, end=": ")
        ...         print_vector(factors.wettedareas.values)

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


class Calc_FlowAreas_V1(modeltools.Method):
    r"""Calculate the sector-specific wetted areas of those subareas of the cross
    section involved in water routing.

    Basic equation:
      .. math::
        A = AS_i + E \cdot (SW_i + W) / 2
        \\ \\
        i = Index \\
        E = Excess \\
        A = FlowAreas \\
        W = FlowWidths \\
        AS = SectorFlowAreas \\
        WS = SectorFlowWidths

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowareas.update()
        >>> from hydpy import print_vector
        >>> for waterlevel in range(11):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     model.calc_flowwidths_v1()
        ...     model.calc_flowareas_v1()
        ...     print_vector([waterlevel, *factors.flowareas.values])
        0, 0.0, 0.0, 0.0, 0.0
        1, 0.0, 0.0, 0.0, 0.0
        2, 2.5, 0.0, 0.0, 0.0
        3, 6.0, 0.0, 0.0, 0.0
        4, 11.0, 0.0, 0.0, 0.0
        5, 17.0, 8.0, 4.0, 0.0
        6, 23.0, 16.0, 8.0, 3.0
        7, 29.0, 24.0, 12.0, 11.0
        8, 35.0, 32.0, 16.0, 22.0
        9, 41.0, 40.0, 20.0, 34.0
        10, 47.0, 48.0, 24.0, 46.0
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    DERIVEDPARAMETERS = (wq_derived.SectorFlowAreas, wq_derived.SectorFlowWidths)
    REQUIREDSEQUENCES = (wq_aides.Index, wq_aides.Excess, wq_factors.FlowWidths)
    RESULTSEQUENCES = (wq_factors.FlowAreas,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        j = int(aid.index)
        for i in range(con.nmbsectors):
            fac.flowareas[i] = der.sectorflowareas[i, j] + (
                aid.excess * (der.sectorflowwidths[i, j] + fac.flowwidths[i]) / 2.0
            )


class Calc_TotalAreas_V1(modeltools.Method):
    r"""Calculate the sector-specific wetted areas of the total cross section.

    Basic equation:
      .. math::
        A = AS_i + E \cdot (SW_i + W) / 2
        \\ \\
        i = Index \\
        E = Excess \\
        A = TotalAreas \\
        W = TotalWidths \\
        AS = SectorTotalAreas \\
        WS = SectorTotalWidths

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> totalwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectortotalwidths.update()
        >>> derived.sectortotalareas.update()
        >>> from hydpy import print_vector
        >>> for waterlevel in range(11):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     model.calc_totalwidths_v1()
        ...     model.calc_totalareas_v1()
        ...     print_vector([waterlevel, *factors.totalareas.values])
        0, 0.0, 0.0, 0.0, 0.0
        1, 0.0, 0.0, 0.0, 0.0
        2, 2.5, 0.0, 0.0, 0.0
        3, 6.0, 0.0, 0.0, 0.0
        4, 11.0, 0.0, 0.0, 0.0
        5, 17.0, 8.0, 4.0, 0.0
        6, 23.0, 16.0, 8.0, 3.0
        7, 29.0, 24.0, 12.0, 11.0
        8, 35.0, 32.0, 16.0, 22.0
        9, 41.0, 40.0, 20.0, 34.0
        10, 47.0, 48.0, 24.0, 46.0
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    DERIVEDPARAMETERS = (wq_derived.SectorTotalAreas, wq_derived.SectorTotalWidths)
    REQUIREDSEQUENCES = (wq_aides.Index, wq_aides.Excess, wq_factors.TotalWidths)
    RESULTSEQUENCES = (wq_factors.TotalAreas,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        j = int(aid.index)
        for i in range(con.nmbsectors):
            fac.totalareas[i] = der.sectortotalareas[i, j] + (
                aid.excess * (der.sectortotalwidths[i, j] + fac.totalwidths[i]) / 2.0
            )


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


class Calc_FlowArea_V1(modeltools.Method):
    r"""Sum up the individual cross-section sectors' flow areas.

    Basic equation:
      :math:`FlowArea = \sum_{i=1}^{NmbSectors} FlowAreas_i`

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(3)
        >>> factors.flowareas(2.0, 3.0, 1.0)
        >>> model.calc_flowarea_v1()
        >>> factors.flowarea
        flowarea(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    REQUIREDSEQUENCES = (wq_factors.FlowAreas,)
    RESULTSEQUENCES = (wq_factors.FlowArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.flowarea = 0.0
        for i in range(con.nmbsectors):
            fac.flowarea += fac.flowareas[i]


class Calc_TotalArea_V1(modeltools.Method):
    r"""Sum up the individual cross-section sectors' total wetted areas.

    Basic equation:
      :math:`TotalArea = \sum_{i=1}^{NmbSectors} TotalAreas_i`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(3)
        >>> factors.totalareas(2.0, 3.0, 1.0)
        >>> model.calc_totalarea_v1()
        >>> factors.totalarea
        totalarea(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    REQUIREDSEQUENCES = (wq_factors.TotalAreas,)
    RESULTSEQUENCES = (wq_factors.TotalArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.totalarea = 0.0
        for i in range(con.nmbsectors):
            fac.totalarea += fac.totalareas[i]


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

        >>> from hydpy import print_vector, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_wettedperimeters_v1()
        ...         round_(d, end=": ")
        ...         print_vector(factors.wettedperimeters.values)

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


class Calc_FlowPerimeters_V1(modeltools.Method):
    r"""Interpolate the sector-specific wetted perimeters of those subareas of the cross
    section involved in water routing.

    Basic equations:
      .. math::
        P = \begin{cases}
        (1 - w) \cdot PS_i + w \cdot PS_{i+1} &|\ w \neq nan \\
        PS_i + 2 \cdot E &|\ w = nan
        \end{cases}
        \\ \\
        i = Index \\
        w = Weight \\
        E = Excess \\
        P = FlowPerimeters \\
        PS = SectorFlowPerimeters

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowperimeters.update()
        >>> from hydpy import print_vector
        >>> for waterlevel in range(11):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     model.calc_flowwidths_v1()
        ...     model.calc_flowperimeters_v1()
        ...     print_vector([waterlevel, *factors.flowperimeters.values])
        0, 2.0, 0.0, 0.0, 0.0
        1, 2.0, 0.0, 0.0, 0.0
        2, 4.236068, 0.0, 0.0, 0.0
        3, 6.472136, 0.0, 0.0, 0.0
        4, 9.300563, 8.0, 4.0, 0.0
        5, 11.300563, 10.0, 6.0, 0.0
        6, 13.300563, 12.0, 8.0, 6.324555
        7, 15.300563, 14.0, 10.0, 10.796691
        8, 17.300563, 16.0, 12.0, 13.625118
        9, 19.300563, 18.0, 14.0, 15.625118
        10, 21.300563, 20.0, 16.0, 17.625118
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    DERIVEDPARAMETERS = (wq_derived.SectorFlowPerimeters,)
    REQUIREDSEQUENCES = (wq_aides.Index, wq_aides.Weight, wq_aides.Excess)
    RESULTSEQUENCES = (wq_factors.FlowPerimeters,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        j = int(aid.index)
        if modelutils.isnan(aid.weight):
            for i in range(con.nmbsectors):
                fac.flowperimeters[i] = (
                    der.sectorflowperimeters[i, j] + 2.0 * aid.excess
                )
        else:
            for i in range(con.nmbsectors):
                w: float = aid.weight
                fac.flowperimeters[i] = (1.0 - w) * der.sectorflowperimeters[
                    i, j
                ] + w * der.sectorflowperimeters[i, j + 1]


class Calc_WettedPerimeter_V1(modeltools.Method):
    r"""Sum up the individual trapeze ranges' wetted perimeters.

    Basic equation:
      :math:`WettedPerimeter = \sum_{i=1}^{NmbTrapezes} WettedPerimeters_i`

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(3)
        >>> factors.wettedperimeters(2.0, 3.0, 1.0)
        >>> model.calc_wettedperimeter_v1()
        >>> factors.wettedperimeter
        wettedperimeter(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbTrapezes,)
    REQUIREDSEQUENCES = (wq_factors.WettedPerimeters,)
    RESULTSEQUENCES = (wq_factors.WettedPerimeter,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.wettedperimeter = 0.0
        for i in range(con.nmbtrapezes):
            fac.wettedperimeter += fac.wettedperimeters[i]


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

        >>> from hydpy import print_vector, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     derived.perimeterderivatives.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_wettedperimeterderivatives_v1()
        ...         round_(d, end=": ")
        ...         print_vector(factors.wettedperimeterderivatives.values)

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


class Calc_FlowPerimeterDerivatives_V1(modeltools.Method):
    """Take the sector-specific wetted perimeter derivatives of those subareas of the
    cross section involved in water routing.

    Basic equations:
      .. math::
        P = DS_i
        \\ \\
        i = Index \\
        D = FlowPerimeterDerivatives \\
        DS = SectorFlowPerimeterDerivatives

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowperimeterderivatives.update()
        >>> from hydpy import print_vector
        >>> for waterlevel in range(11):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     model.calc_flowperimeterderivatives_v1()
        ...     print_vector([waterlevel, *factors.flowperimeterderivatives.values])
        0, 2.236068, nan, nan, nan
        1, 2.236068, nan, nan, nan
        2, 2.236068, nan, nan, nan
        3, 2.828427, nan, nan, nan
        4, 2.0, 2.0, 2.0, nan
        5, 2.0, 2.0, 2.0, 6.324555
        6, 2.0, 2.0, 2.0, 4.472136
        7, 2.0, 2.0, 2.0, 2.828427
        8, 2.0, 2.0, 2.0, 2.0
        9, 2.0, 2.0, 2.0, 2.0
        10, 2.0, 2.0, 2.0, 2.0
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    DERIVEDPARAMETERS = (wq_derived.SectorFlowPerimeterDerivatives,)
    REQUIREDSEQUENCES = (wq_aides.Index,)
    RESULTSEQUENCES = (wq_factors.FlowPerimeterDerivatives,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        j = int(aid.index)
        for i in range(con.nmbsectors):
            fac.flowperimeterderivatives[i] = der.sectorflowperimeterderivatives[i, j]


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

        >>> from hydpy import print_vector, round_
        >>> def test():
        ...     derived.bottomdepths.update()
        ...     derived.trapezeheights.update()
        ...     derived.slopewidths.update()
        ...     for d in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        ...         factors.waterdepth = d
        ...         model.calc_surfacewidths_v1()
        ...         round_(d, end=": ")
        ...         print_vector(factors.surfacewidths.values)

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


class Calc_FlowWidths_V1(modeltools.Method):
    r"""Interpolate the sector-specific widths of those subareas of the cross section
    involved in water routing.

    Basic equation:
      .. math::
        W_i = \begin{cases}
        (1 - w) \cdot WS_i + w \cdot WS_{i+1} &|\ w \neq nan \\
        WS_i &|\ w = nan
        \end{cases}
        \\ \\
        i = Index \\
        w = Weight \\
        W = FlowWidths \\
        WS = SectorFlowWidths

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> flowwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectorflowwidths.update()
        >>> from hydpy import print_vector
        >>> for waterlevel in range(11):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     model.calc_flowwidths_v1()
        ...     print_vector([waterlevel, *factors.flowwidths.values])
        0, 2.0, 0.0, 0.0, 0.0
        1, 2.0, 0.0, 0.0, 0.0
        2, 3.0, 0.0, 0.0, 0.0
        3, 4.0, 0.0, 0.0, 0.0
        4, 6.0, 8.0, 4.0, 0.0
        5, 6.0, 8.0, 4.0, 0.0
        6, 6.0, 8.0, 4.0, 6.0
        7, 6.0, 8.0, 4.0, 10.0
        8, 6.0, 8.0, 4.0, 12.0
        9, 6.0, 8.0, 4.0, 12.0
        10, 6.0, 8.0, 4.0, 12.0
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    DERIVEDPARAMETERS = (wq_derived.SectorFlowWidths,)
    REQUIREDSEQUENCES = (wq_aides.Index, wq_aides.Weight)
    RESULTSEQUENCES = (wq_factors.FlowWidths,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        j = int(aid.index)
        if modelutils.isnan(aid.weight):
            for i in range(con.nmbsectors):
                fac.flowwidths[i] = der.sectorflowwidths[i, j]
        else:
            for i in range(con.nmbsectors):
                fac.flowwidths[i] = (1.0 - aid.weight) * der.sectorflowwidths[
                    i, j
                ] + aid.weight * der.sectorflowwidths[i, j + 1]


class Calc_TotalWidths_V1(modeltools.Method):
    r"""Interpolate the sector-specific widths of the total cross section.

    Basic equation:
      .. math::
        W_i = \begin{cases}
        (1 - w) \cdot WS_i + w \cdot WS_{i+1} &|\ w \neq nan \\
        WS_i &|\ w = nan
        \end{cases}
        \\ \\
        i = Index \\
        w = Weight \\
        W = TotalWidths \\
        WS = SectorTotalWidths

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(9)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 4.0, 5.0, 6.0, 7.0, 8.0)
        >>> totalwidths(2.0, 4.0, 6.0, 14.0, 18.0, 18.0, 24.0, 28.0, 30.0)
        >>> transitions(2, 3, 5)
        >>> derived.sectortotalwidths.update()
        >>> from hydpy import print_vector
        >>> for waterlevel in range(11):
        ...     factors.waterlevel = waterlevel
        ...     model.calc_index_excess_weight_v1()
        ...     model.calc_totalwidths_v1()
        ...     print_vector([waterlevel, *factors.totalwidths.values])
        0, 2.0, 0.0, 0.0, 0.0
        1, 2.0, 0.0, 0.0, 0.0
        2, 3.0, 0.0, 0.0, 0.0
        3, 4.0, 0.0, 0.0, 0.0
        4, 6.0, 8.0, 4.0, 0.0
        5, 6.0, 8.0, 4.0, 0.0
        6, 6.0, 8.0, 4.0, 6.0
        7, 6.0, 8.0, 4.0, 10.0
        8, 6.0, 8.0, 4.0, 12.0
        9, 6.0, 8.0, 4.0, 12.0
        10, 6.0, 8.0, 4.0, 12.0
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    DERIVEDPARAMETERS = (wq_derived.SectorTotalWidths,)
    REQUIREDSEQUENCES = (wq_aides.Index, wq_aides.Weight)
    RESULTSEQUENCES = (wq_factors.TotalWidths,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        aid = model.sequences.aides.fastaccess

        j = int(aid.index)
        if modelutils.isnan(aid.weight):
            for i in range(con.nmbsectors):
                fac.totalwidths[i] = der.sectortotalwidths[i, j]
        else:
            for i in range(con.nmbsectors):
                fac.totalwidths[i] = (1.0 - aid.weight) * der.sectortotalwidths[
                    i, j
                ] + aid.weight * der.sectortotalwidths[i, j + 1]


class Calc_TotalWidth_V1(modeltools.Method):
    r"""Sum the individual cross-section sectors' water surface widths.

    Basic equation:
      :math:`TotalWidth = \sum_{i=1}^{NmbSectors} TotalWidths_i`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(3)
        >>> factors.totalwidths(2.0, 3.0, 1.0)
        >>> model.calc_totalwidth_v1()
        >>> factors.totalwidth
        totalwidth(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    REQUIREDSEQUENCES = (wq_factors.TotalWidths,)
    RESULTSEQUENCES = (wq_factors.TotalWidth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.totalwidth = 0.0
        for i in range(con.nmbsectors):
            fac.totalwidth += fac.totalwidths[i]


class Calc_Discharges_V1(modeltools.Method):
    r"""Calculate the discharge for each trapeze range.

    Basic equation:
      .. math::
        Discharges_i = \begin{cases}
        0 &|\ d < 0 \\
        F \cdot C \cdot A^{5/3} \cdot P^{-2/3} \cdot \sqrt{S_B} &|\ 0 \leq d
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        F = CalibrationFactors_i \\
        C = StricklerCoefficients_i \\
        A = WettedAreas_i \\
        P = WettedPerimeters_i \\
        S_B = BottomSlope

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(4)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0, 20.0, 20.0)
        >>> calibrationfactors(1.0, 1.0, 3.0, 1.0)
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
        wq_control.CalibrationFactors,
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
                    con.calibrationfactors[i]
                    * con.stricklercoefficients[i]
                    * con.bottomslope**0.5
                    * fac.wettedareas[i] ** (5.0 / 3.0)
                    / fac.wettedperimeters[i] ** (2.0 / 3.0)
                )
            else:
                flu.discharges[i] = 0.0


class Calc_Discharges_V2(modeltools.Method):
    r"""Calculate the discharge for each cross-section sector.

    Basic equation:
      .. math::
        Q = \begin{cases}
        0 &|\ A < 0 \\
        F \cdot C \cdot A^{5/3} \cdot P^{-2/3} \cdot \sqrt{S} &|\ 0 \leq A
        \end{cases}
        \\ \\
        Q = Discharges \\
        F = CalibrationFactors \\
        C = StricklerCoefficients \\
        A = FlowAreas \\
        P = FlowPerimeters \\
        S = BottomSlope

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(4)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0, 20.0, 80.0)
        >>> calibrationfactors(1.0, 1.0, 3.0, 1.0)
        >>> factors.flowareas = 1.0, 4.0, 8.0, 0.0
        >>> factors.flowperimeters = 2.0, 4.0, 6.0, 8.0
        >>> model.calc_discharges_v2()
        >>> fluxes.discharges
        discharges(1.259921, 16.0, 58.147859, 0.0)
    """

    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.BottomSlope,
        wq_control.StricklerCoefficients,
        wq_control.CalibrationFactors,
    )
    REQUIREDSEQUENCES = (wq_factors.FlowAreas, wq_factors.FlowPerimeters)
    RESULTSEQUENCES = (wq_fluxes.Discharges,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for i in range(con.nmbsectors):
            if fac.flowareas[i] > 0.0:
                flu.discharges[i] = (
                    con.calibrationfactors[i]
                    * con.stricklercoefficients[i]
                    * con.bottomslope**0.5
                    * fac.flowareas[i] ** (5.0 / 3.0)
                    / fac.flowperimeters[i] ** (2.0 / 3.0)
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


class Calc_Discharge_V3(modeltools.Method):
    r"""Sum up the individual cross-section sectors' discharges.

    Basic equation:
      :math:`Discharge = \sum_{i=1}^{NmbSector} Discharges_i`

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(3)
        >>> fluxes.discharges(2.0, 3.0, 1.0)
        >>> model.calc_discharge_v3()
        >>> fluxes.discharge
        discharge(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    REQUIREDSEQUENCES = (wq_fluxes.Discharges,)
    RESULTSEQUENCES = (wq_fluxes.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.discharge = 0.0
        for i in range(con.nmbsectors):
            flu.discharge += flu.discharges[i]


class Calc_DischargeDerivatives_V1(modeltools.Method):
    r"""Calculate the discharge change for each trapeze range with respect to a water
    level increase.

    Basic equation:
     .. math::
        DischargeDerivatives_i = \begin{cases}
        0 &|\ d < 0 \\
        F \cdot C \cdot
        (A / P)^{5/3} \cdot \frac{5 \cdot P \cdot A' - 2 \cdot A \cdot P'}{3 \cdot P}
        \cdot \sqrt{S_B} &|\ 0 \leq d
        \end{cases}
        \\ \\
        d = WaterDepth - BottomDepth_i \\
        F = CalibrationFactors_i \\
        C = StricklerCoefficients_i \\
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
        >>> stricklercoefficients(20.0, 40.0, 20.0, 60.0)
        >>> calibrationfactors(1.0, 1.0, 3.0, 1.0)
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
        wq_control.CalibrationFactors,
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
                    con.calibrationfactors[i]
                    * con.stricklercoefficients[i]
                    * con.bottomslope**0.5
                    * (a / p) ** (2.0 / 3.0)
                    * (5.0 * p * da - 2.0 * a * dp)
                    / (3.0 * p)
                )
            else:
                fac.dischargederivatives[i] = 0.0


class Calc_DischargeDerivatives_V2(modeltools.Method):
    r"""Calculate the discharge change for each cross section-sector with respect to a
    water level increase.

    Basic equation:
     .. math::
        Q' = \begin{cases}
        0 &|\ L \leq H \\
        C \cdot
        (A / P)^{5/3} \cdot \frac{5 \cdot P \cdot A' - 2 \cdot A \cdot P'}{3 \cdot P}
        \cdot \sqrt{S} &|\ L > H
        \end{cases}
        \\ \\
        Q' = DischargeDerivatives \\
        L = WaterLevel \\
        H = Heights \\
        F = CalibrationFactors \\
        C = StricklerCoefficients \\
        A = FlowAreas \\
        A' = FlowWidth \\
        P = FlowPerimeters \\
        P' = FlowPerimeterDerivatives \\
        S = BottomSlope

    Example:

        The following example reuses the same cross-section configuration as the
        example on method |Calc_DischargeDerivatives_V1| and so results in the same
        derivative estimates:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbwidths(7)
        >>> nmbsectors(4)
        >>> heights(1.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0)
        >>> flowwidths(2.0, 2.0, 6.0, 8.0, 12.0, 14.0, 16.0)
        >>> transitions(1, 2, 4)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0, 20.0, 60.0)
        >>> calibrationfactors(1.0, 1.0, 3.0, 1.0)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectorflowareas.update()
        >>> derived.sectorflowperimeterderivatives.update()
        >>> derived.sectorflowperimeters.update()
        >>> factors.waterlevel = 4.5
        >>> model.calc_index_excess_weight_v1()
        >>> model.calc_flowwidths_v1()
        >>> model.calc_flowareas_v1()
        >>> model.calc_flowperimeters_v1()
        >>> model.calc_flowperimeterderivatives_v1()
        >>> model.calc_dischargederivatives_v2()
        >>> factors.dischargederivatives
        dischargederivatives(3.884141, 18.475494, 16.850223, 0.0)
    """

    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.BottomSlope,
        wq_control.StricklerCoefficients,
        wq_control.CalibrationFactors,
    )
    REQUIREDSEQUENCES = (
        wq_factors.WaterLevel,
        wq_factors.FlowAreas,
        wq_factors.FlowWidths,
        wq_factors.FlowPerimeters,
        wq_factors.FlowPerimeterDerivatives,
    )
    RESULTSEQUENCES = (wq_factors.DischargeDerivatives,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        for i in range(con.nmbsectors):
            t = 0 if i == 0 else int(con.transitions[i - 1])
            if fac.waterlevel > con.heights[t]:
                a: float = fac.flowareas[i]
                da: float = fac.flowwidths[i]
                p: float = fac.flowperimeters[i]
                dp: float = fac.flowperimeterderivatives[i]
                fac.dischargederivatives[i] = (
                    con.calibrationfactors[i]
                    * con.stricklercoefficients[i]
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


class Calc_DischargeDerivative_V2(modeltools.Method):
    r"""Sum the individual cross-section sectors' discharge derivatives.

    Basic equation:
      :math:`DischargeDerivative = \sum_{i=1}^{NmbSectors} DischargeDerivatives_i`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(3)
        >>> bottomslope(0.01)
        >>> factors.dischargederivatives(2.0, 3.0, 1.0)
        >>> model.calc_dischargederivative_v2()
        >>> factors.dischargederivative
        dischargederivative(6.0)
    """

    CONTROLPARAMETERS = (wq_control.NmbSectors,)
    REQUIREDSEQUENCES = (wq_factors.DischargeDerivatives,)
    RESULTSEQUENCES = (wq_factors.DischargeDerivative,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.dischargederivative = 0.0
        for i in range(con.nmbsectors):
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

        >>> factors.surfacewidth = 0.0
        >>> model.calc_celerity_v1()
        >>> factors.celerity
        celerity(nan)
    """

    REQUIREDSEQUENCES = (wq_factors.DischargeDerivative, wq_factors.SurfaceWidth)
    RESULTSEQUENCES = (wq_factors.Celerity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        if fac.surfacewidth > 0.0:
            fac.celerity = fac.dischargederivative / fac.surfacewidth
        else:
            fac.celerity = modelutils.nan


class Calc_Celerity_V2(modeltools.Method):
    r"""Calculate the kinematic wave celerity.

    Basic equation:
      :math:`Celerity = \frac{DischargeDerivative}{TotalWidth}`

    Examples:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.dischargederivative = 6.0
        >>> factors.totalwidth = 2.0
        >>> model.calc_celerity_v2()
        >>> factors.celerity
        celerity(3.0)

        >>> factors.totalwidth = 0.0
        >>> model.calc_celerity_v2()
        >>> factors.celerity
        celerity(nan)
    """

    REQUIREDSEQUENCES = (wq_factors.DischargeDerivative, wq_factors.TotalWidth)
    RESULTSEQUENCES = (wq_factors.Celerity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        if fac.totalwidth > 0.0:
            fac.celerity = fac.dischargederivative / fac.totalwidth
        else:
            fac.celerity = modelutils.nan


class Set_WaterDepth_V1(modeltools.Method):
    """Set the water depth in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> model.set_waterdepth_v1(2.0)
        >>> factors.waterdepth
        waterdepth(2.0)
    """

    RESULTSEQUENCES = (wq_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.Model, waterdepth: float) -> None:
        fac = model.sequences.factors.fastaccess

        fac.waterdepth = waterdepth


class Set_WaterLevel_V1(modeltools.Method):
    """Set the water level in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> model.set_waterlevel_v1(2.0)
        >>> factors.waterlevel
        waterlevel(2.0)
    """

    RESULTSEQUENCES = (wq_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model, waterlevel: float) -> None:
        fac = model.sequences.factors.fastaccess

        fac.waterlevel = waterlevel


class Set_WettedArea_V1(modeltools.Method):
    """Set the wetted area in m².

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> model.set_wettedarea_v1(2.0)
        >>> factors.wettedarea
        wettedarea(2.0)
    """

    RESULTSEQUENCES = (wq_factors.WettedArea,)

    @staticmethod
    def __call__(model: modeltools.Model, wettedarea: float) -> None:
        fac = model.sequences.factors.fastaccess

        fac.wettedarea = wettedarea


class Use_WaterDepth_V1(modeltools.SetAutoMethod):
    """Set the water depth in m and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> bottomwidths(2.0, 2.0)
        >>> sideslopes(0.0, 0.0)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0)
        >>> calibrationfactors(1.0)
        >>> derived.bottomdepths.update()
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> derived.perimeterderivatives.update()
        >>> model.use_waterdepth_v1(3.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.wettedarea
        wettedarea(8.0)
        >>> fluxes.discharge
        discharge(14.945466)
        >>> factors.celerity
        celerity(2.642957)
    """

    SUBMETHODS = (
        Set_WaterDepth_V1,
        Calc_WaterLevel_V1,
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
        wq_control.BottomLevels,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
        wq_control.StricklerCoefficients,
        wq_control.CalibrationFactors,
        wq_control.BottomSlope,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
        wq_derived.PerimeterDerivatives,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WaterLevel,
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


class Use_WaterDepth_V2(modeltools.SetAutoMethod):
    """Set the water depth in m and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> bottomwidths(2.0, 2.0)
        >>> sideslopes(0.0, 0.0)
        >>> derived.bottomdepths.update()
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> model.use_waterdepth_v2(3.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.wettedarea
        wettedarea(8.0)
        >>> factors.wettedperimeter
        wettedperimeter(12.0)
    """

    SUBMETHODS = (
        Set_WaterDepth_V1,
        Calc_WaterLevel_V1,
        Calc_WettedAreas_V1,
        Calc_WettedArea_V1,
        Calc_WettedPerimeters_V1,
        Calc_WettedPerimeter_V1,
    )
    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomLevels,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WaterLevel,
        wq_factors.WettedAreas,
        wq_factors.WettedArea,
        wq_factors.WettedPerimeters,
        wq_factors.WettedPerimeter,
    )


class Use_WaterDepth_V3(modeltools.SetAutoMethod):
    """Set the water depth in m and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(2)
        >>> nmbwidths(3)
        >>> heights(1.0, 3.0, 3.0)
        >>> flowwidths(2.0, 2.0, 4.0)
        >>> totalwidths(2.0, 2.0, 4.0)
        >>> transitions(1)
        >>> stricklercoefficients(20.0, 40.0)
        >>> calibrationfactors(1.0)
        >>> bottomslope(0.01)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectortotalwidths.update()
        >>> derived.sectorflowareas.update()
        >>> derived.sectortotalareas.update()
        >>> derived.sectorflowperimeters.update()
        >>> derived.sectorflowperimeterderivatives.update()
        >>> model.use_waterdepth_v3(3.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.flowarea
        flowarea(8.0)
        >>> factors.totalarea
        totalarea(8.0)
        >>> fluxes.discharge
        discharge(14.945466)
        >>> factors.celerity
        celerity(2.642957)
    """

    SUBMETHODS = (
        Set_WaterDepth_V1,
        Calc_WaterLevel_V2,
        Calc_Index_Excess_Weight_V1,
        Calc_FlowWidths_V1,
        Calc_TotalWidths_V1,
        Calc_TotalWidth_V1,
        Calc_FlowAreas_V1,
        Calc_TotalAreas_V1,
        Calc_FlowPerimeters_V1,
        Calc_FlowPerimeterDerivatives_V1,
        Calc_FlowArea_V1,
        Calc_TotalArea_V1,
        Calc_Discharges_V2,
        Calc_Discharge_V3,
        Calc_DischargeDerivatives_V2,
        Calc_DischargeDerivative_V2,
        Calc_Celerity_V2,
    )
    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.NmbWidths,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.StricklerCoefficients,
        wq_control.CalibrationFactors,
        wq_control.BottomSlope,
    )
    DERIVEDPARAMETERS = (
        wq_derived.SectorFlowWidths,
        wq_derived.SectorTotalWidths,
        wq_derived.SectorFlowAreas,
        wq_derived.SectorTotalAreas,
        wq_derived.SectorFlowPerimeters,
        wq_derived.SectorFlowPerimeterDerivatives,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WaterLevel,
        wq_aides.Index,
        wq_aides.Excess,
        wq_aides.Weight,
        wq_factors.FlowAreas,
        wq_factors.FlowArea,
        wq_factors.TotalAreas,
        wq_factors.TotalArea,
        wq_factors.FlowPerimeters,
        wq_factors.FlowPerimeterDerivatives,
        wq_factors.FlowWidths,
        wq_factors.TotalWidths,
        wq_factors.TotalWidth,
        wq_factors.DischargeDerivatives,
        wq_factors.DischargeDerivative,
        wq_fluxes.Discharges,
        wq_fluxes.Discharge,
        wq_factors.Celerity,
    )


class Use_WaterLevel_V1(modeltools.SetAutoMethod):
    """Set the water level in m and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> bottomwidths(2.0, 2.0)
        >>> sideslopes(0.0, 0.0)
        >>> bottomslope(0.01)
        >>> stricklercoefficients(20.0, 40.0)
        >>> calibrationfactors(1.0)
        >>> derived.bottomdepths.update()
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> derived.perimeterderivatives.update()
        >>> model.use_waterlevel_v1(4.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.wettedarea
        wettedarea(8.0)
        >>> fluxes.discharge
        discharge(14.945466)
        >>> factors.celerity
        celerity(2.642957)
    """

    SUBMETHODS = (
        Set_WaterLevel_V1,
        Calc_WaterDepth_V1,
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
        wq_control.BottomLevels,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
        wq_control.StricklerCoefficients,
        wq_control.CalibrationFactors,
        wq_control.BottomSlope,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
        wq_derived.PerimeterDerivatives,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterLevel,
        wq_factors.WaterDepth,
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


class Use_WaterLevel_V2(modeltools.SetAutoMethod):
    """Set the water level in m and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> bottomwidths(2.0, 2.0)
        >>> sideslopes(0.0, 0.0)
        >>> derived.bottomdepths.update()
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> model.use_waterlevel_v2(4.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.wettedarea
        wettedarea(8.0)
        >>> factors.wettedperimeter
        wettedperimeter(12.0)
    """

    SUBMETHODS = (
        Set_WaterLevel_V1,
        Calc_WaterDepth_V1,
        Calc_WettedAreas_V1,
        Calc_WettedArea_V1,
        Calc_WettedPerimeters_V1,
        Calc_WettedPerimeter_V1,
    )
    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomLevels,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WaterLevel,
        wq_factors.WettedAreas,
        wq_factors.WettedArea,
        wq_factors.WettedPerimeters,
        wq_factors.WettedPerimeter,
    )


class Use_WaterLevel_V3(modeltools.SetAutoMethod):
    """Set the water level in m and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbsectors(2)
        >>> nmbwidths(3)
        >>> heights(1.0, 3.0, 3.0)
        >>> flowwidths(2.0, 2.0, 4.0)
        >>> totalwidths(2.0, 2.0, 4.0)
        >>> transitions(1)
        >>> stricklercoefficients(20.0, 40.0)
        >>> calibrationfactors(1.0)
        >>> bottomslope(0.01)
        >>> derived.sectorflowwidths.update()
        >>> derived.sectortotalwidths.update()
        >>> derived.sectorflowareas.update()
        >>> derived.sectortotalareas.update()
        >>> derived.sectorflowperimeters.update()
        >>> derived.sectorflowperimeterderivatives.update()
        >>> model.use_waterlevel_v3(4.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.flowarea
        flowarea(8.0)
        >>> factors.totalarea
        totalarea(8.0)
        >>> fluxes.discharge
        discharge(14.945466)
        >>> factors.celerity
        celerity(2.642957)
    """

    SUBMETHODS = (
        Set_WaterLevel_V1,
        Calc_WaterDepth_V3,
        Calc_Index_Excess_Weight_V1,
        Calc_FlowWidths_V1,
        Calc_TotalWidths_V1,
        Calc_TotalWidth_V1,
        Calc_FlowAreas_V1,
        Calc_TotalAreas_V1,
        Calc_FlowPerimeters_V1,
        Calc_FlowPerimeterDerivatives_V1,
        Calc_FlowArea_V1,
        Calc_TotalArea_V1,
        Calc_Discharges_V2,
        Calc_Discharge_V3,
        Calc_DischargeDerivatives_V2,
        Calc_DischargeDerivative_V2,
        Calc_Celerity_V2,
    )
    CONTROLPARAMETERS = (
        wq_control.NmbSectors,
        wq_control.NmbWidths,
        wq_control.Transitions,
        wq_control.Heights,
        wq_control.StricklerCoefficients,
        wq_control.CalibrationFactors,
        wq_control.BottomSlope,
    )
    DERIVEDPARAMETERS = (
        wq_derived.SectorFlowWidths,
        wq_derived.SectorTotalWidths,
        wq_derived.SectorFlowAreas,
        wq_derived.SectorTotalAreas,
        wq_derived.SectorFlowPerimeters,
        wq_derived.SectorFlowPerimeterDerivatives,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WaterLevel,
        wq_aides.Index,
        wq_aides.Excess,
        wq_aides.Weight,
        wq_factors.FlowAreas,
        wq_factors.FlowArea,
        wq_factors.TotalAreas,
        wq_factors.TotalArea,
        wq_factors.FlowPerimeters,
        wq_factors.FlowPerimeterDerivatives,
        wq_factors.FlowWidths,
        wq_factors.TotalWidths,
        wq_factors.TotalWidth,
        wq_factors.DischargeDerivatives,
        wq_factors.DischargeDerivative,
        wq_fluxes.Discharges,
        wq_fluxes.Discharge,
        wq_factors.Celerity,
    )


class Use_WettedArea_V1(modeltools.SetAutoMethod):
    """Set the wetted area in m² and use it to calculate all other properties.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> nmbtrapezes(2)
        >>> bottomlevels(1.0, 3.0)
        >>> bottomwidths(2.0, 2.0)
        >>> sideslopes(0.0, 0.0)
        >>> derived.bottomdepths.update()
        >>> derived.trapezeheights.update()
        >>> derived.slopewidths.update()
        >>> derived.trapezeareas.update()
        >>> model.use_wettedarea_v1(8.0)
        >>> factors.waterdepth
        waterdepth(3.0)
        >>> factors.waterlevel
        waterlevel(4.0)
        >>> factors.wettedarea
        wettedarea(8.0)
        >>> factors.wettedperimeter
        wettedperimeter(12.0)
    """

    SUBMETHODS = (
        Set_WettedArea_V1,
        Calc_WaterDepth_V2,
        Calc_WaterLevel_V1,
        Calc_WettedAreas_V1,
        Calc_WettedArea_V1,
        Calc_WettedPerimeters_V1,
        Calc_WettedPerimeter_V1,
    )
    CONTROLPARAMETERS = (
        wq_control.NmbTrapezes,
        wq_control.BottomLevels,
        wq_control.BottomWidths,
        wq_control.SideSlopes,
    )
    DERIVEDPARAMETERS = (
        wq_derived.BottomDepths,
        wq_derived.TrapezeHeights,
        wq_derived.SlopeWidths,
        wq_derived.TrapezeAreas,
    )
    RESULTSEQUENCES = (
        wq_factors.WaterDepth,
        wq_factors.WaterLevel,
        wq_factors.WettedAreas,
        wq_factors.WettedArea,
        wq_factors.WettedPerimeters,
        wq_factors.WettedPerimeter,
    )


class Get_WaterDepth_V1(modeltools.Method):
    """Get the water depth in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.waterdepth = 2.0
        >>> model.get_waterdepth_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.waterdepth


class Get_WaterLevel_V1(modeltools.Method):
    """Get the water level in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.waterlevel = 2.0
        >>> model.get_waterlevel_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.waterlevel


class Get_WettedArea_V1(modeltools.Method):
    """Get the wetted area in m².

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.wettedarea = 2.0
        >>> model.get_wettedarea_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.WettedArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.wettedarea


class Get_WettedArea_V2(modeltools.Method):
    """Get the wetted area in m².

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.totalarea = 2.0
        >>> model.get_wettedarea_v2()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.TotalArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.totalarea


class Get_WettedPerimeter_V1(modeltools.Method):
    """Get the wetted perimeter in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.wettedperimeter = 2.0
        >>> model.get_wettedperimeter_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.WettedPerimeter,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.wettedperimeter


class Get_SurfaceWidth_V1(modeltools.Method):
    """Get the surface width in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.surfacewidth = 2.0
        >>> model.get_surfacewidth_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.SurfaceWidth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.surfacewidth


class Get_SurfaceWidth_V2(modeltools.Method):
    """Get the surface width in m.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> factors.totalwidth = 2.0
        >>> model.get_surfacewidth_v2()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.TotalWidth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.totalwidth


class Get_Discharge_V1(modeltools.Method):
    """Get the discharge in m³/s.

    Example:

        >>> from hydpy.models.wq import *
        >>> parameterstep()
        >>> fluxes.discharge = 2.0
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
        >>> factors.celerity = 2.0
        >>> model.get_celerity_v1()
        2.0
    """

    REQUIREDSEQUENCES = (wq_factors.Celerity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.celerity


class Model(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """|wq.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="WQ")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        Calculate_Discharge_V1,
        Set_WaterDepth_V1,
        Set_WaterLevel_V1,
        Set_WettedArea_V1,
        Use_WaterDepth_V1,
        Use_WaterDepth_V2,
        Use_WaterDepth_V3,
        Use_WaterLevel_V1,
        Use_WaterLevel_V2,
        Use_WaterLevel_V3,
        Use_WettedArea_V1,
        Get_WaterDepth_V1,
        Get_WaterLevel_V1,
        Get_WettedArea_V1,
        Get_WettedArea_V2,
        Get_WettedPerimeter_V1,
        Get_SurfaceWidth_V1,
        Get_SurfaceWidth_V2,
        Get_Discharge_V1,
        Get_Celerity_V1,
    )
    ADD_METHODS = (
        Calc_WaterDepth_V1,
        Calc_WaterDepth_V2,
        Calc_WaterDepth_V3,
        Calc_WaterLevel_V1,
        Calc_WaterLevel_V2,
        Calc_Index_Excess_Weight_V1,
        Calc_WettedAreas_V1,
        Calc_FlowAreas_V1,
        Calc_TotalAreas_V1,
        Calc_WettedArea_V1,
        Calc_FlowArea_V1,
        Calc_TotalArea_V1,
        Calc_WettedPerimeters_V1,
        Calc_FlowPerimeters_V1,
        Calc_WettedPerimeter_V1,
        Calc_WettedPerimeterDerivatives_V1,
        Calc_FlowPerimeterDerivatives_V1,
        Calc_SurfaceWidths_V1,
        Calc_SurfaceWidth_V1,
        Calc_FlowWidths_V1,
        Calc_TotalWidths_V1,
        Calc_TotalWidth_V1,
        Calc_Discharges_V1,
        Calc_Discharges_V2,
        Calc_Discharge_V2,
        Calc_Discharge_V3,
        Calc_DischargeDerivatives_V1,
        Calc_DischargeDerivatives_V2,
        Calc_DischargeDerivative_V1,
        Calc_DischargeDerivative_V2,
        Calc_Celerity_V1,
        Calc_Celerity_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class TrapezeModel(modeltools.AdHocModel):
    """Base class for |wq.DOCNAME.long| models that rely on trapezoidal geometries."""

    def plot(
        self,
        *,
        ymax: float | None = None,
        color: str | None = None,
        label: bool | str = False
    ) -> pyplot.Figure:
        """Plot the channel profile.

        See the main documentation of the application model |wq_trapeze| for more
        information.
        """
        con = self.parameters.control
        der = self.parameters.derived
        n = con.nmbtrapezes.value
        bl = con.bottomlevels.values
        bw = con.bottomwidths.values
        ss = con.sideslopes.values
        sw = der.slopewidths.values
        th = der.trapezeheights.values

        xs = [0.0]
        ys = [bl[0]]

        def _add(dx: float, dy: float) -> None:
            xs.append(xs[-1] + dx)
            ys.append(ys[-1] + dy)
            xs.insert(0, -xs[-1])
            ys.insert(0, ys[-1])

        for i in range(n):
            _add(dx=bw[i] / 2.0, dy=0.0)
            if i < n - 1:
                _add(dx=sw[i] / 2.0, dy=th[i])

        if (ymax is None) or (ymax <= ys[-1]):
            if n == 1:
                ymax = bl[0] + (bw[0] / 2.0 if bw[0] > 0.0 else 1.0)
            else:
                ymax = bl[0] + (bl[-1] - bl[0]) / n * (n + 1)

        dy_ = ymax - bl[-1]
        dx_ = dy_ * ss[-1]
        _add(dx=dx_, dy=dy_)

        pyplot.xlabel("distance from centre [m]")
        pyplot.ylabel("elevation [m]")
        if isinstance(label, bool) and label:
            label = objecttools.devicename(self)
        if isinstance(label, str):
            pyplot.plot(xs, ys, color=color, label=label)
            pyplot.legend()
        else:
            pyplot.plot(xs, ys, color=color)

        return pyplot.gcf()

    def get_depths_of_discontinuity(self) -> tuple[float, ...]:
        """Get the depths of all trapeze bottoms (except zero).

        >>> from hydpy.models.wq_trapeze_strickler import *
        >>> parameterstep()

        >>> nmbtrapezes(1)
        >>> bottomlevels(1.0)
        >>> model.get_depths_of_discontinuity()
        ()

        >>> nmbtrapezes(3)
        >>> bottomlevels(1.0, 3.0, 4.0)
        >>> from hydpy import print_vector
        >>> print_vector(model.get_depths_of_discontinuity())
        2.0, 3.0
        """
        bottomlevels = self.parameters.control.bottomlevels.values
        return tuple(bottomlevels[1:] - bottomlevels[0])


class WidthsModel(modeltools.AdHocModel):
    """Base class for |wq.DOCNAME.long| models that rely on width measurements."""

    def plot(
        self,
        *,
        ymax: float | None = None,
        color: str | None = None,
        label: bool | str = False
    ) -> pyplot.Figure:
        """Plot the channel profile.

        The following tests closely resemble those of |wq_trapeze| for comparison and
        serve the same purpose: to clarify how individual parameter values translate
        into actual geometries.  Like for the |wq_trapeze| examples, we first create a
        test function that simplifies inserting generated figures into the online
        documentation:

        >>> from hydpy.core.testtools import save_autofig
        >>> def plot(example, label=False):
        ...     figure = model.plot(label=label)
        ...     save_autofig(f"wq_widths_{example}.png", figure=figure)

        Basically, "width models" as |wq_widths_strickler| rely on cross-section widths
        measured (or otherwise estimated) at different heights.  In the case of a
        simple rectangular profile, defining a single measurement suffices:

        >>> from hydpy.models.wq_widths_strickler import *
        >>> parameterstep()
        >>> nmbwidths(1)

        Principally, one can define multiple subsectors within a cross-section, for
        example, to perform separate discharge estimations with different friction
        coefficients.  Each transition from one sector to its neighbour must lie at a
        height/width pair.  However, when defining only a single height/width pair, as
        in this example, we can only specify a single sector:

        >>> nmbsectors(1)

        |wq_widths_strickler| uses the neutral term "height" because submodels should
        be able to handle water levels as well as water depths.  Here, we set the
        single height to 1 m:

        >>> heights(1.0)

        In contrast to "trapeze models", "width models" allow for differentiation
        between active and passive areas within a cross-section profile.  We set the
        rectangle's "flow width", which is actively involved in water routing, to 2 m:

        >>> flowwidths(2.0)

        We set the "total widths" to 3 m, so that a rest of 1 m, which contributes to
        storing but not to routing water, remains (this can be useful to approximately
        consider, for example, the effects of groynes):

        >>> totalwidths(3.0)

        The plot routine adds the cross-section's active part in dashed lines:

        >>> plot("rectangle")

        .. image:: wq_widths_rectangle.png
           :width: 400

        Defining a triangular cross-section requires (at least) two height/width pairs.
        Above the highest height/value pair, the profile's outlines are, somewhat in
        contrast to |wq_trapeze|, vertically oriented:

        >>> nmbwidths(2)
        >>> heights(1.0, 2.0)
        >>> flowwidths(0.0, 4.0)
        >>> totalwidths(0.0, 6.0)
        >>> plot("triangle")

        .. image:: wq_widths_triangle.png
           :width: 400

        For a simple trapeze, two height/width pairs are also sufficient:

        >>> flowwidths(2.0, 6.0)
        >>> totalwidths(2.0, 8.0)
        >>> plot("one_trapeze")

        .. image:: wq_widths_one_trapeze.png
           :width: 400

        Next, we define a three-trapeze profile identical to one in the documentation
        of |wq_trapeze| (except for the vertically oriented outlines above the highest
        height/width pair).  Therefore, we need to define five height/width pairs:

        >>> nmbwidths(5)

        It is allowed to define multiple widths for the same height.  Here, we make use
        of this to model the upper trapeze's bottom:

        >>> heights(1.0, 3.0, 4.0, 4.0, 5.0)
        >>> flowwidths(2.0, 2.0, 6.0, 8.0, 12.0)
        >>> totalwidths(2.0, 2.0, 6.0, 10.0, 14.0)

        Increasing the value of parameter |NmbSectors| to three and setting the
        suitable transition indices via the index parameter |Transitions| results in a
        definition of separate sectors analogous to the definition of separate trapeze
        ranges in the |wq_trapeze| example:

        >>> nmbsectors(3)
        >>> transitions(1, 2)

        All transitions are marked via circles:

        >>> from hydpy import Element
        >>> e = Element("three_trapezes_1")
        >>> e.model = model
        >>> plot("three_trapezes_1", label=True)

        .. image:: wq_widths_three_trapezes_1.png
           :width: 400

        In the last example, most of the outline and all transition points of the total
        cross-section overlay the corresponding properties of the subarea that
        contributes actively to water routing.  The following example shows that those
        properties are depicted by solid lines and filled circles and by dashed lines
        and empty circles, respectively:

        >>> transitions(1, 3)
        >>> plot("three_trapezes_2", label="three_trapezes_2")

        .. image:: wq_widths_three_trapezes_2.png
           :width: 400
        """

        con = self.parameters.control
        nw = con.nmbwidths.value
        hs = con.heights.value
        fws = con.flowwidths.values
        tws = con.totalwidths.values
        ts = con.transitions.values

        fxs = [0.0]
        txs = [0.0]
        ys = [hs[0]]

        def _add_to_lines(fx: float, tx: float, y: float) -> None:
            fxs.append(fx / 2.0)
            fxs.insert(0, -fx / 2.0)
            txs.append(tx / 2.0)
            txs.insert(0, -tx / 2.0)
            ys.append(y)
            ys.insert(0, y)

        for h, fw, tw in zip(hs, fws, tws):
            _add_to_lines(fx=fw, tx=tw, y=h)
        if (ymax is None) or (ymax <= ys[-1]):
            ymax = hs[0] + 1.0 if nw == 1 else hs[0] + (hs[-1] - hs[0]) / nw * (nw + 1)
        _add_to_lines(fx=fws[-1], tx=tws[-1], y=ymax)

        pfxs = []
        ptxs = []
        pys = []

        def _add_to_points(fx: float, tx: float, y: float) -> None:
            pfxs.append(fx / 2.0)
            pfxs.insert(0, -fx / 2.0)
            ptxs.append(tx / 2.0)
            ptxs.insert(0, -tx / 2.0)
            pys.append(y)
            pys.insert(0, y)

        for t in ts:
            t = int(t)
            _add_to_points(fx=fws[t], tx=tws[t], y=hs[t])

        pyplot.xlabel("distance from centre [m]")
        pyplot.ylabel("height [m]")
        line = pyplot.plot(fxs, ys, color=color, linestyle=":")[0]
        colour = line.get_color()
        if isinstance(label, bool) and label:
            label = objecttools.devicename(self)
        if isinstance(label, str):
            pyplot.plot(txs, ys, color=colour, label=label)
            pyplot.legend()
        else:
            pyplot.plot(txs, ys, color=colour)
        pyplot.plot(
            pfxs,
            pys,
            markeredgecolor=colour,
            markerfacecolor="white",
            linestyle="",
            marker="o",
        )
        pyplot.plot(ptxs, pys, color=colour, linestyle="", marker="o")

        return pyplot.gcf()

    def get_depths_of_discontinuity(self) -> tuple[float, ...]:
        """Get all measurement heights (except the first one).

        >>> from hydpy.models.wq_widths_strickler import *
        >>> parameterstep()

        >>> nmbwidths(1)
        >>> heights(1.0)
        >>> model.get_depths_of_discontinuity()
        ()

        >>> nmbwidths(3)
        >>> heights(1.0, 3.0, 4.0)
        >>> from hydpy import print_vector
        >>> print_vector(model.get_depths_of_discontinuity())
        2.0, 3.0
        """
        heights = self.parameters.control.heights.values
        return tuple(heights[1:] - heights[0])


class Base_DischargeModel_V2(dischargeinterfaces.DischargeModel_V2):
    """Base class for |wq.DOCNAME.long| models that comply with the |DischargeModel_V2|
    submodel interface."""

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
