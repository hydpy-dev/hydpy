# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import inflect
import numpy

# ...from HydPy
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils

# ...from snow
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_derived
from hydpy.models.snow import snow_fixed
from hydpy.models.snow import snow_inputs
from hydpy.models.snow import snow_factors
from hydpy.models.snow import snow_fluxes
from hydpy.models.snow import snow_states
from hydpy.models.snow import snow_logs


class Calc_PLayer_V1(modeltools.Method):
    r"""Adjust the precipitation to the altitude for the snow layers according to
    :cite:t:`ref-Valery`.

    Basic equations:

      .. math::
        L_i^* = P \cdot \begin{cases}
        e^{G\cdot \big(Z_i - \overline{Z}\big)} &|\ Z_i \leq T \\
        e^{G\cdot max\big(T- \overline{Z}, \,0\big)} &|\ Z_i > T
        \end{cases}
        \\
        L_i = L_i^* \cdot \frac{P}{\sum_{i=1}^{N} A_i \cdot L_i^*}
        \\ \\
        L = PLayer \\
        G = GradP \\
        Z = ZLayers \\
        \overline{Z} = ZMean \\
        T = ZThreshold  \\
        N = NLayers \\
        A = LayerArea

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> layerarea(0.2)
        >>> gradp(0.00041)
        >>> inputs.p = 10.0

        The threshold parameter |ZThreshold| is usually fixed to 4000 m:

        >>> fixed.zthreshold
        zthreshold(4000.0)

        If all layers lie below the threshold, their precipitation values become
        adjusted by the same equation:

        >>> zlayers(2199.0, 2599.0, 2999.0, 3399.0, 3799.0)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(2999.0)
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(7.013551, 8.263467, 9.736135, 11.471253, 13.515595)

        The total precipitation volume stays intact:

        >>> from hydpy import round_
        >>> round_(fluxes.player.average_values())
        10.0

        Layers above the threshold altitude are only adjusted with respect to the
        threshold:

        >>> zlayers(3199.0, 3599.0, 3999.0, 4399.0, 4799.0)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(3999.0)
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(7.881562, 9.28617, 10.941098, 10.945585, 10.945585)
        >>> round_(fluxes.player.average_values())
        10.0

        If the average layer altitude exceeds the threshold, the precipitation values
        of the upper layers are not directly adjusted.  Still, |Calc_PLayer_V1|
        indirectly increases them by decreasing the lower layers' precipitation and
        subsequently adjusting all layers' precipitation sum back to the original
        volume:

        >>> zlayers(3201.0, 3601.0, 4001.0, 4401.0, 4801.0)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(4001.0)
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(7.882977, 9.287837, 10.943062, 10.943062, 10.943062)
        >>> round_(fluxes.player.average_values())
        10.0

        If all layers lie above the threshold, all get the same (original)
        precipitation value:

        >>> zlayers(4201.0, 4601.0, 5001.0, 5401.0, 5801.0)
        >>> derived.zmean.update()
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(10.0, 10.0, 10.0, 10.0, 10.0)

        The last example demonstrates that the water balance remains intact for layers
        with different sizes:

        >>> zlayers(3201.0, 3601.0, 4001.0, 4401.0, 4801.0)
        >>> control.layerarea(0.3, 0.2, 0.2, 0.2, 0.1)
        >>> derived.zmean.update()
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(8.1337, 9.583241, 11.286484, 11.286484, 11.286484)
        >>> round_(fluxes.player.average_values())
        10.0
    """

    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.LayerArea,
        snow_control.GradP,
    )
    DERIVEDPARAMETERS = (snow_derived.ZMean,)
    FIXEDPARAMETERS = (snow_fixed.ZThreshold,)
    REQUIREDSEQUENCES = (snow_inputs.P,)
    RESULTSEQUENCES = (snow_fluxes.PLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        p: float = 0.0
        for k in range(con.nlayers):
            if con.zlayers[k] <= fix.zthreshold:
                delta: float = con.zlayers[k] - der.zmean
            else:
                delta = max(fix.zthreshold - der.zmean, 0.0)
            flu.player[k] = inp.p * modelutils.exp(con.gradp * delta)
            p += flu.player[k] * con.layerarea[k]

        if p > 0.0:
            for k in range(con.nlayers):
                flu.player[k] = flu.player[k] / p * inp.p


class Return_T_V1(modeltools.Method):
    r"""Return the altitude-adjusted temperature.

    Basic equation:
      :math:`f(t, \, k, \, g) = t + (ZMean - ZLayer_k) \cdot g / 100`

    Examples:

        The adjustment depends on the selected layer's altitude relative to the average
        altitude and the current-day temperature gradient:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmean(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()

        >>> model.idx_sim = pub.timegrids.init["2000-01-01"]
        >>> round_(model.return_t_v1(5.0, 0, gradtmean.values))
        6.0
        >>> round_(model.return_t_v1(5.0, 1, gradtmean.values))
        4.0

        >>> model.idx_sim = pub.timegrids.init["2000-12-31"]
        >>> round_(model.return_t_v1(5.0, 0, gradtmean.values))
        7.0
        >>> round_(model.return_t_v1(5.0, 1, gradtmean.values))
        3.0
    """

    CONTROLPARAMETERS = (snow_control.ZLayers,)
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)

    @staticmethod
    def __call__(model: modeltools.Model, t: float, k: int, g: MatrixFloat) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess

        return t + (der.zmean - con.zlayers[k]) * g[der.doy[model.idx_sim]] / 100.0


class Calc_TLayer_V1(modeltools.Method):
    r"""Calculate the mean temperature for each snow layer based on method
    |Return_T_V1|.

    Basic equation:
      :math:`TLayer_k = f_{Return\_T\_V1}(T, \, k, \, GradTMean)`

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmean(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()
        >>> inputs.t = 5.0

        >>> model.idx_sim = 0
        >>> model.calc_tlayer_v1()
        >>> factors.tlayer
        tlayer(6.0, 4.0)

        >>> model.idx_sim = 365
        >>> model.calc_tlayer_v1()
        >>> factors.tlayer
        tlayer(7.0, 3.0)
    """

    SUBMETHODS = (Return_T_V1,)
    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.GradTMean,
    )
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)
    REQUIREDSEQUENCES = (snow_inputs.T,)
    RESULTSEQUENCES = (snow_factors.TLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            fac.tlayer[k] = model.return_t_v1(inp.t, k, con.gradtmean)


class Calc_TMinLayer_V1(modeltools.Method):
    r"""Calculate the minimum temperature for each snow layer based on method
    |Return_T_V1|.

    Basic equation:
      :math:`TMinLayer_k = f_{Return\_T\_V1}(TMin, \, k, \, GradTMin)`

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmin(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()
        >>> inputs.tmin = 5.0

        >>> model.idx_sim = 0
        >>> model.calc_tminlayer_v1()
        >>> factors.tminlayer
        tminlayer(6.0, 4.0)

        >>> model.idx_sim = 365
        >>> model.calc_tminlayer_v1()
        >>> factors.tminlayer
        tminlayer(7.0, 3.0)
    """

    SUBMETHODS = (Return_T_V1,)
    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.GradTMin,
    )
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)
    REQUIREDSEQUENCES = (snow_inputs.TMin,)
    RESULTSEQUENCES = (snow_factors.TMinLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            fac.tminlayer[k] = model.return_t_v1(inp.tmin, k, con.gradtmin)


class Calc_TMaxLayer_V1(modeltools.Method):
    r"""Calculate the maximum temperature for each snow layer based on method
    |Return_T_V1|.

    Basic equation:
      :math:`TMaxLayer_k = f_{Return\_T\_V1}(TMax, \, k, \, GradTMax)`

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmax(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()
        >>> inputs.tmax = 5.0

        >>> model.idx_sim = 0
        >>> model.calc_tmaxlayer_v1()
        >>> factors.tmaxlayer
        tmaxlayer(6.0, 4.0)

        >>> model.idx_sim = 365
        >>> model.calc_tmaxlayer_v1()
        >>> factors.tmaxlayer
        tmaxlayer(7.0, 3.0)
    """

    SUBMETHODS = (Return_T_V1,)
    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.GradTMax,
    )
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)
    REQUIREDSEQUENCES = (snow_inputs.TMax,)
    RESULTSEQUENCES = (snow_factors.TMaxLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            fac.tmaxlayer[k] = model.return_t_v1(inp.tmax, k, con.gradtmax)


class Calc_SolidFractionPrecipitation_V1(modeltools.Method):
    r"""Calculate the solid precipitation fraction for each snow layer according to
    :cite:t:`ref-USACE1956`.

    Basic equation:
      .. math::
        F = min \left( max \left( \frac{R - T}{R - S}, \, 0 \right), \, 1 \right)
        \\ \\
        F = SolidFractionPrecipitation \\
        T = TLayer \\
        R = TThreshRain \\
        S = TThreshSnow

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(7)
        >>> factors.tlayer = -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0
        >>> model.calc_solidfractionprecipitation_v1()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    FIXEDPARAMETERS = (snow_fixed.TThreshSnow, snow_fixed.TThreshRain)
    REQUIREDSEQUENCES = (snow_factors.TLayer,)
    RESULTSEQUENCES = (snow_factors.SolidFractionPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            r: float = fix.tthreshrain
            s: float = fix.tthreshsnow
            t: float = fac.tlayer[k]
            fac.solidfractionprecipitation[k] = min(max((r - t) / (r - s), 0.0), 1.0)


class Calc_SolidFractionPrecipitation_V2(modeltools.Method):
    r"""Calculate the solid precipitation fraction for each snow layer according to
    :cite:t:`ref-Turcotte2007` and :cite:t:`ref-USACE1956`.

    Basic equation:
      .. math::
        F = \begin{cases}
        min \left( max \left( 1 - \frac{X}{X - N}, \, 0 \right), \, 1 \right)
        &|\ Z < 1500 \\
        min \left( max \left( \frac{R - T}{R - S}, \, 0 \right), \, 1 \right)
        &|\ Z \geq 1500 \end{cases}
        \\ \\
        F = SolidFractionPrecipitation \\
        Z = ZMean \\
        X = TMaxLayer \\
        N = TMinLayer \\
        T = TLayer \\
        R = TThreshRain \\
        S = TThreshSnow

    Examples:

        For catchments with an average elevation below 1500 m, the (daily) solid
        precipitation fraction is determined by the time with an air temperature below
        0°C, which is estimated based on |TMaxLayer| and |TMinLayer|:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(7)
        >>> derived.zmean(1499.0)
        >>> factors.tminlayer = -2.0, -2.0, -2.0, -2.0, -1.0, 0.0, 1.0
        >>> factors.tmaxlayer = -1.0, 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.666667, 0.5, 0.333333, 0.0, 0.0)


        Swapping the minimum and maximum values (which might occur in applications due
        to input data errors or problematic altitude adjustments) yields the same
        results:

        >>> factors.tminlayer = -1.0, 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
        >>> factors.tmaxlayer = -2.0, -2.0, -2.0, -2.0, -1.0, 0.0, 1.0
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.666667, 0.5, 0.333333, 0.0, 0.0)

        Identical minimum and maximum temperatures also pose no problem:

        >>> factors.tminlayer = -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0
        >>> factors.tmaxlayer = -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0)

        For higher catchments, the usual linear interpolation approach between a
        minimum (|TThreshSnow|) and a maximum (|TThreshRain|) temperature threshold
        applies (as when using |Calc_SolidFractionPrecipitation_V1|):

        >>> factors.tlayer = -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0
        >>> derived.zmean(1500.0)
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    DERIVEDPARAMETERS = (snow_derived.ZMean,)
    FIXEDPARAMETERS = (snow_fixed.TThreshSnow, snow_fixed.TThreshRain)
    REQUIREDSEQUENCES = (
        snow_factors.TLayer,
        snow_factors.TMinLayer,
        snow_factors.TMaxLayer,
    )
    RESULTSEQUENCES = (snow_factors.SolidFractionPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            if der.zmean < 1500.0:
                x: float = fac.tmaxlayer[k]
                n: float = fac.tminlayer[k]
                if n < x:
                    w: float = n / (n - x)
                elif n > x:
                    w = x / (x - n)
                elif x < 0.0:
                    w = 1.0
                elif x == 0.0:
                    w = 0.5
                else:
                    w = 0.0
            else:
                r: float = fix.tthreshrain
                s: float = fix.tthreshsnow
                t: float = fac.tlayer[k]
                w = (r - t) / (r - s)
            fac.solidfractionprecipitation[k] = min(max(w, 0.0), 1.0)


class Calc_PRainLayer_V1(modeltools.Method):
    r"""Calculate the liquid part of precipitation :cite:p:`ref-USACE1956`.

    Basic equation:
      :math:`PRainLayer = (1 - SolidFractionPrecipitation) \cdot PLayer`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> fluxes.player = 0.0, 4.0
        >>> factors.solidfractionprecipitation = 0.25
        >>> model.calc_prainlayer()
        >>> fluxes.prainlayer
        prainlayer(0.0, 3.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_factors.SolidFractionPrecipitation, snow_fluxes.PLayer)
    RESULTSEQUENCES = (snow_fluxes.PRainLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            f: float = fac.solidfractionprecipitation[k]
            flu.prainlayer[k] = (1.0 - f) * flu.player[k]


class Calc_PSnowLayer_V1(modeltools.Method):
    r"""Calculate the frozen part of precipitation.

    Basic equation:
      :math:`PSnowLayer = SolidFractionPrecipitation \cdot PLayer`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> fluxes.player = 0.0, 4.0
        >>> factors.solidfractionprecipitation = 0.25
        >>> model.calc_psnowlayer()
        >>> fluxes.psnowlayer
        psnowlayer(0.0, 1.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_factors.SolidFractionPrecipitation, snow_fluxes.PLayer)
    RESULTSEQUENCES = (snow_fluxes.PSnowLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            flu.psnowlayer[k] = fac.solidfractionprecipitation[k] * flu.player[k]


class Update_G_V1(modeltools.Method):
    """Add the snowfall to each layer's snow pack.

    Basic equation:
      :math:`G_{new} = G_{old} + PSnowLayer`

    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nlayers(3)
        >>> fluxes.psnowlayer = 0.0, 1.0, 1.0
        >>> states.g = 1.0, 1.0, 0.0
        >>> model.update_g_v1()
        >>> states.g
        g(1.0, 2.0, 1.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_fluxes.PSnowLayer,)
    UPDATEDSEQUENCES = (snow_states.G,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.g[k] += flu.psnowlayer[k]


class Calc_ETG_V1(modeltools.Method):
    r"""Update the thermal state of each snow layer.

    Basic equation:
      .. math::
        E_{new} = min(C \cdot E_{old} + (1 - C) \cdot T, \, 0)
        \\ \\
        E = ETG \\
        C = CN1 \\
        T = TLayer

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(3)
        >>> cn1(0.75)
        >>> factors.tlayer = 1.0, 0.0, -1.0
        >>> states.etg = -1.0, 0.0, 1.0
        >>> model.calc_etg_v1()
        >>> states.etg
        etg(-0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.CN1)
    REQUIREDSEQUENCES = (snow_factors.TLayer,)
    UPDATEDSEQUENCES = (snow_states.ETG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.etg[k] = min(
                con.cn1 * sta.etg[k] + (1.0 - con.cn1) * fac.tlayer[k], 0.0
            )


class Calc_PotMelt_V1(modeltools.Method):
    r"""Calculate the potential melt for each snow layer.

    Basic equation:
      .. math::
        P = \begin{cases}
        min \big(G, \, C \cdot max(T, \, 0) \big) &|\ E = 0
        \\
        0 &|\ E < 0
        \end{cases}
        \\ \\
        P = PotMelt \\
        E = ETG \\
        C = CN2 \\
        T = TLayer

    Example:

        |Calc_PotMelt_V1| extends the classical day degree with a restriction that
        prevents any melting as long as the snowpack's thermal state is below 0°C:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> simulationstep("1d")
        >>> parameterstep("12h")
        >>> nlayers(5)
        >>> cn2(1.0)
        >>> factors.tlayer = 1.0, -1.0, 1.0, 1.0, 1.0
        >>> states.g = 1.0, 1.0, 1.0, 2.0, 3.0
        >>> states.etg = -1.0, 0.0, 0.0, 0.0, 0.0
        >>> model.calc_potmelt_v1()
        >>> fluxes.potmelt
        potmelt(0.0, 0.0, 1.0, 2.0, 2.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.CN2)
    REQUIREDSEQUENCES = (snow_factors.TLayer, snow_states.ETG, snow_states.G)
    RESULTSEQUENCES = (snow_fluxes.PotMelt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            if sta.etg[k] < 0.0:
                flu.potmelt[k] = 0.0
            else:
                flu.potmelt[k] = min(sta.g[k], max(con.cn2 * fac.tlayer[k], 0.0))


class Calc_GRatio_V1(modeltools.Method):
    r"""Calculate the fraction of the snow-covered area for each snow layer.

    Basic equation:
      :math:`GRatio = min(G / GThresh, \, 1)`

    Example:

        We set |CN4|, used to derive |GThresh|, to 0.9, which corresponds to the
        configuration of the original CemaNeige model:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(4)
        >>> cn4(0.9)
        >>> meanansolidprecip(100.0, 100.0, 100.0, 200.0)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(90.0, 90.0, 90.0, 180.0)
        >>> states.g = 67.5, 90.0, 90.1, 90.0
        >>> model.calc_gratio_v1()
        >>> states.gratio
        gratio(0.75, 1.0, 1.0, 0.5)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    DERIVEDPARAMETERS = (snow_derived.GThresh,)
    REQUIREDSEQUENCES = (snow_states.G,)
    UPDATEDSEQUENCES = (snow_states.GRatio,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.gratio[k] = min(sta.g[k] / der.gthresh[k], 1.0)


class Update_GRatio_GLocalMax_V1(modeltools.Method):
    r"""Calculate the fraction of the snow-covered area for each snow layer and update
    |GLocalMax| before calculating the snowmelt.

    Basic equations:
      .. math::
        L_{new} = min(G, \, L_{old}) \\
        R = min(G / L_{new}, \, 1.0)
        \\ \\
        L = GLocalMax \\
        R = GRatio

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> meanansolidprecip(80.0)
        >>> cn4(0.9)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(72.0)
        >>> states.g = 30.0, 20.0, 12.0, 80.0, 50.0
        >>> states.gratio = 0.0, 0.2, 1.0, 1.0, 1.0
        >>> fluxes.potmelt = 10.0, 10.0, 10.0, 0.0, 0.0
        >>> logs.glocalmax = 40.0, 30.0, 20.0, 10.0, 0.0
        >>> hysteresis(True)
        >>> model.update_gratio_glocalmax_v1()
        >>> states.gratio
        gratio(0.75, 0.666667, 1.0, 1.0, 1.0)
        >>> logs.glocalmax
        glocalmax(40.0, 30.0, 12.0, 10.0, 72.0)

        If we switch off hysteresis, |GRatio| will dependent solely on |GThresh| and
        |GLocalMax| is always set to zero:

        >>> hysteresis(False)
        >>> model.update_gratio_glocalmax_v1()
        >>> states.gratio
        gratio(0.416667, 0.277778, 0.166667, 1.0, 0.694444)
        >>> logs.glocalmax
        glocalmax(0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.Hysteresis)
    DERIVEDPARAMETERS = (snow_derived.GThresh,)
    REQUIREDSEQUENCES = (snow_states.G, snow_fluxes.PotMelt)
    UPDATEDSEQUENCES = (snow_states.GRatio, snow_logs.GLocalMax)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            if con.hysteresis:
                if log.glocalmax[k] == 0.0:
                    log.glocalmax[k] = der.gthresh[k]
                if flu.potmelt[k] > 0.0:
                    if sta.gratio[k] == 1.0:
                        log.glocalmax[k] = min(sta.g[k], log.glocalmax[k])
                    sta.gratio[k] = min(sta.g[k] / log.glocalmax[k], 1.0)
            else:
                sta.gratio[k] = min(sta.g[k] / der.gthresh[k], 1.0)
                log.glocalmax[k] = 0.0


class Calc_Melt_V1(modeltools.Method):
    r"""Calculate the actual snow melt for each layer.

    Basic equation:
      .. math::
        M = P \cdot ((1 - N) \cdot R + N)
        \\ \\
        M = Melt \\
        P = PotMelt \\
        N = MinMelt \\
        R = GRatio

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> fluxes.potmelt = 0.0, 0.5, 1.0, 1.5, 2.0
        >>> states.gratio = 0.0, 0.25, 0.5, 0.75, 1.0
        >>> states.g = 0.0, 0.5, 1.0, 1.5, 2.0
        >>> model.calc_melt_v1()
        >>> fluxes.melt
        melt(0.0, 0.1625, 0.55, 1.1625, 2.0)

        In the original formulation of the CemaNeige model, the basic equation
        typically results in an exponential decrease in snow cover because |PotMelt|
        never exceeds |G| and |GRatio| converges to zero during snow cover depletion.
        To provide an opportunity to avoid infinitely thin snow layers in summer, we
        introduced the fixed parameter |MinG|, which defines the amount of snow below
        which |Melt| equals |PotMelt|:

        >>> fixed.ming(1.0)
        >>> model.calc_melt_v1()
        >>> fluxes.melt
        melt(0.0, 0.5, 0.55, 1.1625, 2.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    FIXEDPARAMETERS = (snow_fixed.MinMelt, snow_fixed.MinG)
    REQUIREDSEQUENCES = (snow_fluxes.PotMelt, snow_states.GRatio, snow_states.G)
    RESULTSEQUENCES = (snow_fluxes.Melt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            flu.melt[k] = flu.potmelt[k]
            if sta.g[k] >= fix.ming:
                flu.melt[k] *= (1.0 - fix.minmelt) * sta.gratio[k] + fix.minmelt


class Update_G_V2(modeltools.Method):
    """Remove the snowmelt from the snowpack.

    Basic equation:
      :math:`G_{new} = G_{old} - Melt`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(4)
        >>> fluxes.melt = 0.0, 0.2, 0.2, 0.2
        >>> states.g = 0.0, 0.2, 0.4, 0.6
        >>> model.update_g_v2()
        >>> states.g
        g(0.0, 0.0, 0.2, 0.4)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_fluxes.Melt,)
    UPDATEDSEQUENCES = (snow_states.G,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.g[k] -= flu.melt[k]


class Update_GRatio_GLocalMax_V2(modeltools.Method):
    r"""Calculate the fraction of the snow-covered area for each snow layer and update
    |GLocalMax| after calculating the snowmelt.

    Basic equation:

      .. math::
        R_{new}= \begin{cases}
        min \left( R_{old} + \Delta / C, \, 1 \right) &|\ \Delta > 0 \\
        min \left( G / L, \, 1 \right) &|\ \Delta < 0
        \end{cases}
        \\ \\
        R = GRatio \\
        \Delta = PSnowLayer - Melt \\
        C = CN3 \\
        L = GLocalMax

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> cn3(3.0)
        >>> cn4(0.2)
        >>> meanansolidprecip(100.0)
        >>> derived.gthresh.update()
        >>> fluxes.psnowlayer = 0.0, 1.0, 2.0, 3.0, 4.0
        >>> fluxes.melt = 0.0, 0.0, 3.0, 2.0, 2.0
        >>> states.g = 10.0, 20.0, 30.0, 40.0, 50.0
        >>> states.gratio = 0.1, 0.5, 0.8, 0.2, 0.4
        >>> logs.glocalmax = 10.0

        If |Hysteresis| is deactivated, |Update_GRatio_GLocalMax_V2| has no effect:

        >>> hysteresis(False)
        >>> model.update_gratio_glocalmax_v2()
        >>> states.gratio
        gratio(0.1, 0.5, 0.8, 0.2, 0.4)
        >>> logs.glocalmax
        glocalmax(10.0, 10.0, 10.0, 10.0, 10.0)

        After activating |Hysteresis|, |Update_GRatio_GLocalMax_V2| updates |GRatio|
        and |GLocalMax| differently depending on whether the snowpack is increasing or
        decreasing:

        >>> hysteresis(True)
        >>> model.update_gratio_glocalmax_v2()
        >>> states.gratio
        gratio(0.1, 0.833333, 1.0, 0.533333, 1.0)
        >>> logs.glocalmax
        glocalmax(10.0, 10.0, 10.0, 10.0, 20.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.Hysteresis,
        snow_control.CN3,
    )
    DERIVEDPARAMETERS = (snow_derived.GThresh,)
    REQUIREDSEQUENCES = (snow_fluxes.Melt, snow_fluxes.PSnowLayer, snow_states.G)
    UPDATEDSEQUENCES = (snow_states.GRatio, snow_logs.GLocalMax)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess

        if con.hysteresis:
            for k in range(con.nlayers):
                dg: float = flu.psnowlayer[k] - flu.melt[k]
                if dg > 0.0:
                    sta.gratio[k] = min(sta.gratio[k] + dg / con.cn3, 1.0)
                    if sta.gratio[k] == 1.0:
                        log.glocalmax[k] = der.gthresh[k]
                elif dg < 0.0:
                    sta.gratio[k] = min(sta.g[k] / log.glocalmax[k], 1.0)


class Calc_PNetLayer_V1(modeltools.Method):
    """Sum the rainfall and the actual snow melt for each layer.

    Basic equation:
      :math:`PNetLayer = PRainLayer + Melt`

    Example:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(2)
    >>> fluxes.prainlayer = 1.0, 2.0
    >>> fluxes.melt = 3.0, 4.0
    >>> model.calc_pnetlayer_v1()
    >>> fluxes.pnetlayer
    pnetlayer(4.0, 6.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_fluxes.PRainLayer, snow_fluxes.Melt)
    RESULTSEQUENCES = (snow_fluxes.PNetLayer,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            flu.pnetlayer[k] = flu.prainlayer[k] + flu.melt[k]


class Calc_PNet_V1(modeltools.Method):
    r"""Calculate the catchment's average net rainfall.

    Basic equation:
      :math:`PNet = \sum_{i=1}^{NLayers} LayerArea_i \cdot PRainLayer_i`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> layerarea(0.2, 0.8)
        >>> fluxes.pnetlayer = 2.0, 1.0
        >>> model.calc_pnet_v1()
        >>> fluxes.pnet
        pnet(1.2)
        >>> from hydpy import round_
        >>> round_(fluxes.pnetlayer.average_values())
        1.2
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.LayerArea)
    REQUIREDSEQUENCES = (snow_fluxes.PNetLayer,)
    RESULTSEQUENCES = (snow_fluxes.PNet,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.pnet = 0.0
        for k in range(con.nlayers):
            flu.pnet += flu.pnetlayer[k] * con.layerarea[k]


class Model(modeltools.AdHocModel):
    """|snow.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Snow")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (Return_T_V1,)
    RUN_METHODS = (
        Calc_PLayer_V1,
        Calc_TLayer_V1,
        Calc_TMinLayer_V1,
        Calc_TMaxLayer_V1,
        Calc_SolidFractionPrecipitation_V1,
        Calc_SolidFractionPrecipitation_V2,
        Calc_PRainLayer_V1,
        Calc_PSnowLayer_V1,
        Update_G_V1,
        Calc_ETG_V1,
        Calc_PotMelt_V1,
        Calc_GRatio_V1,
        Update_GRatio_GLocalMax_V1,
        Calc_Melt_V1,
        Update_G_V2,
        Update_GRatio_GLocalMax_V2,
        Calc_PNetLayer_V1,
        Calc_PNet_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class BaseModel(modeltools.AdHocModel):
    """Base model for CemaNeige-like layered models."""

    def prepare_layers(self, *, hypsodata: VectorInputFloat) -> None:
        """Set the control parameters |LayerArea| and |ZLayers| based on hypsometric
        data.

        Method |BaseModel.prepare_layers| requires the percentiles of the catchment's
        elevation distribution in meters, prefixed by the minimum and suffixed by the
        maximum elevation, which makes exactly 101 data points:

        >>> from hydpy.models.snow_cn import *
        >>> parameterstep()
        >>> model.prepare_layers(hypsodata=[0.0])
        Traceback (most recent call last):
        ...
        ValueError: Method `prepare_layers` requires a vector of 101 hypsometric data \
points but 1 value is given.

        If 100 is a multiple of the number of layers, |BaseModel.prepare_layers| can
        select the correct data directly:

        >>> nlayers(5)
        >>> hypsodata = [
        ...     286.0, 309.0, 320.0, 327.0, 333.0, 338.0, 342.0, 347.0, 351.0, 356.0,
        ...     360.0, 365.0, 369.0, 373.0, 378.0, 382.0, 387.0, 393.0, 399.0, 405.0,
        ...     411.0, 417.0, 423.0, 428.0, 434.0, 439.0, 443.0, 448.0, 453.0, 458.0,
        ...     463.0, 469.0, 474.0, 480.0, 485.0, 491.0, 496.0, 501.0, 507.0, 513.0,
        ...     519.0, 524.0, 530.0, 536.0, 542.0, 548.0, 554.0, 560.0, 566.0, 571.0,
        ...     577.0, 583.0, 590.0, 596.0, 603.0, 609.0, 615.0, 622.0, 629.0, 636.0,
        ...     642.0, 649.0, 656.0, 663.0, 669.0, 677.0, 684.0, 691.0, 698.0, 706.0,
        ...     714.0, 722.0, 730.0, 738.0, 746.0, 754.0, 762.0, 770.0, 777.0, 786.0,
        ...     797.0, 808.0, 819.0, 829.0, 841.0, 852.0, 863.0, 875.0, 887.0, 901.0,
        ...     916.0, 934.0, 952.0, 972.0, 994.0, 1012.0, 1029.0, 10540.0, 10800.0,
        ...     11250.0, 12780.0
        ... ]
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.2)
        >>> zlayers
        zlayers(360.0, 463.0, 577.0, 714.0, 916.0)

        Otherwise, it still selects some of the given values and thereby needs to
        trick a little, which results in some deviations from the original elevation
        distribution:

        >>> nlayers(7)
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.142857)
        >>> zlayers
        zlayers(347.0, 423.0, 501.0, 583.0, 677.0, 786.0, 972.0)


        >>> nlayers(70)
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.014286)
        >>> zlayers
        zlayers(286.0, 320.0, 333.0, 342.0, 351.0, 360.0, 369.0, 378.0, 387.0,
                399.0, 411.0, 423.0, 434.0, 443.0, 453.0, 463.0, 474.0, 485.0,
                496.0, 507.0, 519.0, 530.0, 542.0, 554.0, 566.0, 577.0, 590.0,
                603.0, 615.0, 629.0, 642.0, 649.0, 656.0, 663.0, 669.0, 677.0,
                684.0, 691.0, 698.0, 706.0, 714.0, 722.0, 730.0, 738.0, 746.0,
                754.0, 762.0, 770.0, 777.0, 786.0, 797.0, 808.0, 819.0, 829.0,
                841.0, 852.0, 863.0, 875.0, 887.0, 901.0, 916.0, 934.0, 952.0,
                972.0, 994.0, 1012.0, 1029.0, 10540.0, 10800.0, 11250.0)

        Due to this selection mechanism (without interpolation), the highest number of
        supported layers is 100:

        >>> nlayers(100)
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.01)
        >>> assert zlayers == hypsodata[:-1]

        >>> nlayers(101)
        >>> model.prepare_layers(hypsodata=hypsodata)
        Traceback (most recent call last):
        ...
        ValueError: Method `prepare_layers` works for at most 100 layers, but the \
value of parameter `nlayers` of element `?` is set to 101.
        """

        if len(hypsodata) != 101:
            p = inflect.engine()
            n = len(hypsodata)
            raise ValueError(
                f"Method `prepare_layers` requires a vector of 101 hypsometric data "
                f"points but {len(hypsodata)} {p.plural_noun('value', n)} "
                f"{p.plural_verb('is', n)} given."
            )

        control = self.parameters.control

        if control.nlayers > 100:
            raise ValueError(
                f"Method `prepare_layers` works for at most 100 layers, but the value "
                f"of parameter {objecttools.elementphrase(control.nlayers)} is set to "
                f"{control.nlayers.value}."
            )

        control.layerarea(1.0 / control.nlayers)
        width = 100 // control.nlayers
        rest = 100 % control.nlayers
        i0 = 0
        control.zlayers(numpy.nan)
        for i1 in range(control.nlayers.value):
            if rest == 0:
                adjusted_width = width
            else:
                adjusted_width = width + 1
                rest -= 1
            if adjusted_width <= 2:
                control.zlayers.values[i1] = hypsodata[i0]
            else:
                control.zlayers.values[i1] = hypsodata[int(i0 + adjusted_width / 2.0)]
            i0 = i0 + adjusted_width
