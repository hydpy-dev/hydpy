# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils

# ...from grxjland
from hydpy.models.grxjland import grxjland_inputs
from hydpy.models.grxjland import grxjland_fluxes
from hydpy.models.grxjland import grxjland_control
from hydpy.models.grxjland import grxjland_states
from hydpy.models.grxjland import grxjland_outlets
from hydpy.models.grxjland import grxjland_derived
from hydpy.models.grxjland import grxjland_logs


class Calc_Pn_En_AE_V1(modeltools.Method):
    """Calculate net rainfall and net evapotranspiration capacity.

    Basic equations:

        Determination of net rainfall and PE by subtracting E from P to determine
        either a net rainfall Pn or a net evapotranspiration capacity En:

      :math:`Pn = P - E, En = 0 \\ | \\ P \\geq E`

      :math:`Pn = 0,  En = E - P\\ | \\ P < E``

    Examples:

        Evapotranspiration larger than precipitation:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> inputs.p = 20.
        >>> inputs.e = 30.
        >>> model.calc_pn_en_ae_v1()
        >>> fluxes.en
        en(10.0)
        >>> fluxes.pn
        pn(0.0)
        >>> fluxes.ae
        ae(20.0)

        Precipitation larger than evapotranspiration:

        >>> inputs.p = 50.
        >>> inputs.e = 10.
        >>> model.calc_pn_en_ae_v1()
        >>> fluxes.en
        en(0.0)
        >>> fluxes.pn
        pn(40.0)
        >>> fluxes.ae
        ae(10.0)

    """

    REQUIREDSEQUENCES = (
        grxjland_inputs.P,
        grxjland_inputs.E,
    )
    RESULTSEQUENCES = (
        grxjland_fluxes.Pn,
        grxjland_fluxes.En,
        grxjland_fluxes.AE,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        if inp.p >= inp.e:
            flu.pn = inp.p - inp.e
            flu.en = 0.0
        else:
            flu.pn = 0.0
            flu.en = inp.e - inp.p
        flu.ae = inp.e - flu.en


class Calc_PS_V1(modeltools.Method):
    """Calculate part of net rainfall filling the production store.

    Basic equation:

        In case Pn is not zero, a part Ps of Pn fills the production store. It is
        determined as a function of the level S in the store by:

      :math:`Ps = \\frac{X1(1-(\\frac{S}{X1}^{2}tanh(
      \\frac{Pn}{X1}){1+\\frac{S}{X1}tanh(\\frac{Pn}{X1})}`

    Examples:

        Example production store full, no rain fills the production store

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x1(300)
        >>> states.s = 300
        >>> fluxes.pn = 50
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(0.0)

        Example routing store empty, nearly all net rainfall fills the production store:

        >>> states.s = 0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(49.542124)

        Example no net rainfall:

        >>> fluxes.pn = 0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(0.0)
    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Pn,
        grxjland_states.S,
    )
    CONTROLPARAMETERS = (grxjland_control.X1,)

    RESULTSEQUENCES = (grxjland_fluxes.Ps,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess

        flu.ps = (
            con.x1
            * (1.0 - (sta.s / con.x1) ** 2.0)
            * modelutils.tanh(flu.pn / con.x1)
            / (1.0 + sta.s / con.x1 * modelutils.tanh(flu.pn / con.x1))
        )


class Calc_ProductionStore_V1(modeltools.Method):
    """Calculate actual evaporation rate, water content and percolation leakage from
    the production store.

    Basic equations:

        Actual evaporation rate is determined as a function of the level in the
        production store to calculate the quantity.
        Es of water that will evaporate from the store. It is obtained by:

      :math:`Es = \\frac{S(2-\\frac{S}{X1}tanh(\\frac{En}{X1})}{1+(
      1-\\frac{S}{X1})tanh(\\frac{En}{X1})}`

        The water content in the production store is then updated with:

      :math:`S = S - Es + Ps`

        A percolation leakage Perc from the production store is then calculated as a
        power function of the reservoir content:

      :math:`Perc = S{1-[1+(\\frac{4 S}{9 X1})^{4}]^{-1/4}}`

        The reservoir content becomes:

      :math:`S = S- Perc`

        Calculate the total actual evapotranspiration from production storage and net
        rainfall calculation

      :math:`AE = Es + AE`

    Examples:

        Example production store nearly full, no rain:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x1(300.)
        >>> fluxes.ps = 0.
        >>> fluxes.e = 10.
        >>> fluxes.en = 2.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 270.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(1.978652)
        >>> fluxes.ae
        ae(9.978652)
        >>> fluxes.perc
        perc(1.6402)
        >>> states.s
        s(266.381148)

        Check water balance:

        >>> 270. + fluxes.ps - fluxes.perc - fluxes.es - states.s
        0.0

        Example production store nearly full, rain:

        >>> fluxes.ps = 25.
        >>> fluxes.e = 10.
        >>> fluxes.en = 0.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 270.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(0.0)
        >>> fluxes.ae
        ae(10.0)
        >>> fluxes.perc
        perc(2.630796)
        >>> states.s
        s(292.369204)

        Check water balance:

        >>> 270. + fluxes.ps - fluxes.perc - fluxes.es - states.s
        0.0

        Example production store empty, no rain

        >>> fluxes.ps = 0.
        >>> fluxes.e = 10.
        >>> fluxes.en = 2.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 0.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(0.0)
        >>> fluxes.ae
        ae(8.0)
        >>> fluxes.perc
        perc(0.0)
        >>> states.s
        s(0.0)

        Example production store empty, rain

        >>> fluxes.ps = 30.
        >>> fluxes.e = 10.
        >>> fluxes.en = 0.
        >>> fluxes.ae = fluxes.e - fluxes.en
        >>> states.s = 0.
        >>> model.calc_productionstore_v1()
        >>> fluxes.es
        es(0.0)
        >>> fluxes.ae
        ae(10.0)
        >>> fluxes.perc
        perc(0.000029)
        >>> states.s
        s(29.999971)

        Check water balance:

        >>> 0. + fluxes.ps - fluxes.perc - fluxes.es - states.s
        0.0
    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Ps,
        grxjland_fluxes.En,
    )
    CONTROLPARAMETERS = (grxjland_control.X1,)

    UPDATEDSEQUENCES = (
        grxjland_states.S,
        grxjland_fluxes.AE,
    )

    RESULTSEQUENCES = (
        grxjland_fluxes.Es,
        grxjland_fluxes.Perc,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.es = (sta.s * (2.0 - sta.s / con.x1) * modelutils.tanh(flu.en / con.x1)) / (
            1.0 + (1.0 - sta.s / con.x1) * modelutils.tanh(flu.en / con.x1)
        )
        sta.s = sta.s - flu.es + flu.ps
        # flu.perc = sta.s * (1. - (1. + (4. * sta.s / 9. / con.x1) ** 4.) ** (-0.25))
        # probably faster
        flu.perc = sta.s * (
            1.0 - (1.0 + (4. / 9. * sta.s / con.x1) ** 4.0) ** (-0.25)
        )
        sta.s = sta.s - flu.perc
        flu.ae = flu.ae + flu.es


class Calc_Pr_V1(modeltools.Method):
    """Total quantity Pr of water reaching the routing functions.

    Basic equation:

      :math:`Pr = Perc + (Pn - Ps)`

    Examples:

        Example production store nearly full, no rain:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.ps = 3.
        >>> fluxes.perc = 10.
        >>> fluxes.pn = 5.
        >>> model.calc_pr_v1()
        >>>
        >>> fluxes.pr
        pr(12.0)
    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Ps,
        grxjland_fluxes.Pn,
        grxjland_fluxes.Perc,
    )

    RESULTSEQUENCES = (grxjland_fluxes.Pr,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pr = flu.perc + flu.pn - flu.ps


class Calc_UH1_V1(modeltools.Method):
    """Calculate the unit hydrograph UH1 output (convolution).

    Input to the unit hydrograph UH1 is 90% of Pr.

    Examples:

        Prepare a unit hydrograph with only three ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> x4(3)
        >>> derived.uh1.update()
        >>> derived.uh1
        uh1(0.06415, 0.298737, 0.637113)
        >>> logs.quh1 = 1.0, 3.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.pr = 0.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(1.0)
        >>> logs.quh1
        quh1(3.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pr = 4.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(3.23094)
        >>> logs.quh1
        quh1(1.075454, 2.293605, 0.0)

        In the next example we set the memory to zero (no input in the past), and
        apply a single input signal:

        >>> logs.quh1 = 0.0, 0.0, 0.0
        >>> fluxes.pr = 4.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(0.23094)
        >>> fluxes.pr = 0.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(1.075454)
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(2.293605)
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(0.0)

        A unit hydrograph with only one ordinate results in the direct
        routing of the input, remember, only 90% of pr enters UH1:

        >>> x4(0.8)
        >>> derived.uh1.update()
        >>> derived.uh1
        uh1(1.0)
        >>> logs.quh1 = 0
        >>> fluxes.pr = 4.0
        >>> model.calc_uh1_v1()
        >>> fluxes.q9
        q9(3.6)

    """

    DERIVEDPARAMETERS = (grxjland_derived.UH1,)
    REQUIREDSEQUENCES = (grxjland_fluxes.Pr,)
    UPDATEDSEQUENCES = (grxjland_logs.QUH1,)
    RESULTSEQUENCES = (grxjland_fluxes.Q9,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        # 90 % of Pr enters UH1
        flu.q9 = der.uh1[0] * 0.9 * flu.pr + log.quh1[0]
        for jdx in range(1, len(der.uh1)):
            log.quh1[jdx - 1] = der.uh1[jdx] * 0.9 * flu.pr + log.quh1[jdx]


class Calc_UH2_V1(modeltools.Method):
    """Calculate the unit hydrograph UH2 output (convolution).

    Input to the unit hydrograph UH2 is 10% of Pr.

    Examples:

        Prepare a unit hydrograph with six ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> x4(3)
        >>> derived.uh2.update()
        >>> derived.uh2
        uh2(0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075)
        >>> logs.quh2 = 1.0, 3.0, 0.0, 2.0, 1.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.pr = 0.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(1.0)
        >>> logs.quh2
        quh2(3.0, 0.0, 2.0, 1.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pr = 4.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(3.01283)
        >>> logs.quh2
        quh2(0.059747, 2.127423, 1.127423, 0.059747, 0.01283, 0.0)

        In the next example we set the memory to zero (no input in the past), and
        apply a single input signal:

        >>> logs.quh2 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> fluxes.pr = 4.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> fluxes.pr = 0.0
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.059747)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.127423)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.127423)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.059747)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> model.calc_uh2_v1()
        >>> fluxes.q1
        q1(0.0)

    """

    DERIVEDPARAMETERS = (grxjland_derived.UH2,)
    REQUIREDSEQUENCES = (grxjland_fluxes.Pr,)
    UPDATEDSEQUENCES = (grxjland_logs.QUH2,)
    RESULTSEQUENCES = (grxjland_fluxes.Q1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        # 10 % of Pr enters UH2
        flu.q1 = der.uh2[0] * 0.1 * flu.pr + log.quh2[0]
        for jdx in range(1, len(der.uh2)):
            log.quh2[jdx - 1] = der.uh2[jdx] * 0.1 * flu.pr + log.quh2[jdx]


class Calc_UH2_V2(modeltools.Method):
    """Calculate the unit hydrograph UH2 output (convolution).

    This is the version for the GR5J model. The input is 100% of Pr, the output of the
    Unit Hydrograph is splitted in two parts: 90% gets Q9 and 10% gets Q1.

    Examples:

        Prepare a unit hydrograph with only six ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(3)
        >>> derived.uh2.update()
        >>> derived.uh2
        uh2(0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075)
        >>> logs.quh2 = 3.0, 3.0, 0.0, 2.0, 4.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left. The output is splitted in the two parts:

        >>> fluxes.pr = 0.0
        >>> model.calc_uh2_v2()
        >>> fluxes.q1
        q1(0.3)
        >>> fluxes.q9
        q9(2.7)
        >>> logs.quh2
        quh2(3.0, 0.0, 2.0, 4.0, 0.0, 0.0)

    """

    DERIVEDPARAMETERS = (grxjland_derived.UH2,)
    REQUIREDSEQUENCES = (grxjland_fluxes.Pr,)
    UPDATEDSEQUENCES = (grxjland_logs.QUH2,)
    RESULTSEQUENCES = (
        grxjland_fluxes.Q1,
        grxjland_fluxes.Q9,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        d_quh2 = der.uh2[0] * flu.pr + log.quh2[0]
        for jdx in range(1, len(der.uh2)):
            log.quh2[jdx - 1] = der.uh2[jdx] * flu.pr + log.quh2[jdx]
        flu.q1 = 0.1 * d_quh2
        flu.q9 = 0.9 * d_quh2


class Calc_RoutingStore_V1(modeltools.Method):
    """Calculate groundwater exchange term F, level of the non-linear routing store R
    and the outflow Qr of the reservoir.

    Basic equations:

        The ground waterexchange term F that acts on both flow components is
        calculated as:

      :math:`F = X2 \\frac{R}{X3}^{7/2}`


        X2 is the water exchange coefficient. X2 can be either positive in case of
        water imports, negative for water exports or zero when there is no water
        exchange.
        The  higher the level in the routing store, the larger the  exchange.

        The level in the routing store is updated by adding the output Q9 of UH1 and F:

      :math:`R = max(0; R + Q9 + F)`

        The outflow Qr of the reservoir is then calculated as:

      :math:`Qr = R{1-[1+(\\frac{R}{X3})^{4}]^{-1/4}}`

        The level in the reservoir becomes:

      :math:`R = R - Qr`


    Examples:

        Positive groundwater exchange coefficient, routing storage nearly full

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x2(1.02)
        >>> x3(100.)
        >>> fluxes.q9 = 20.
        >>> states.r = 95.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(0.852379)
        >>> states.r
        r(89.548769)
        >>> fluxes.qr
        qr(26.30361)

        Positive groundwater exchange coefficient, routing storage nearly empty:

        >>> states.r = 10.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(0.000323)
        >>> states.r
        r(29.939875)
        >>> fluxes.qr
        qr(0.060448)

        Negative groundwater exchange coefficient, routing storage nearly full

        >>> x2(-1.02)
        >>> states.r = 95.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(-0.852379)
        >>> states.r
        r(89.067124)
        >>> fluxes.qr
        qr(25.080497)

        Negative groundwater exchange coefficient, routing storage nearly empty:

        >>> states.r = 10.
        >>> model.calc_routingstore_v1()
        >>> fluxes.f
        f(-0.000323)
        >>> states.r
        r(29.939236)
        >>> fluxes.qr
        qr(0.060441)


    """

    REQUIREDSEQUENCES = (grxjland_fluxes.Q9,)
    CONTROLPARAMETERS = (
        grxjland_control.X2,
        grxjland_control.X3,
    )

    UPDATEDSEQUENCES = (grxjland_states.R,)

    RESULTSEQUENCES = (
        grxjland_fluxes.F,
        grxjland_fluxes.Qr,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3) ** 3.5
        sta.r = max(0.0, sta.r + flu.q9 + flu.f)
        flu.qr = sta.r * (1 - (1 + (sta.r / con.x3) ** 4) ** (-0.25))
        sta.r = sta.r - flu.qr


class Calc_RoutingStore_V2(modeltools.Method):
    """Calculate groundwater exchange term F, level of the non-linear routing store R
    and the outflow Qr of the reservoir.

    This is the GR5J version of the routing store.

    Basic equations:

        The ground water exchange term F that acts on both flow components is
        calculated as:

      :math:`F = X2 (\\frac{R}{X3} - X5)`


        X2 is the water exchange coefficient. X2 can be either positive in case of
        water imports, negative for water exports or zero when there is no water
        exchange.
        The  higher the level in the routing store, the larger the  exchange. X5 can
        be seen as the external, quasi-stationary potential of the groundwater system
        and F is a ‘‘restoring flux’’ acting like a spring device with constant X2.
        Usually, X2 is negative: the more R/X3 de-parts from X5, the more intense the
        flux is, which tends to restore its value to X5.

        The level in the routing store is updated by adding the output Q9 of UH1 and F:

      :math:`R = max(0; R + Q9 + F)`

        The outflow Qr of the reservoir is then calculated as:

      :math:`Qr = R{1-[1+(\\frac{R}{X3})^{4}]^{-1/4}}`

        The level in the reservoir becomes:

      :math:`R = R - Qr`


    Examples:

        Filled storage

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x2(-0.163)
        >>> x3(100.)
        >>> x5(0.104)
        >>> fluxes.q9 = 20.
        >>> states.r = 95.
        >>> model.calc_routingstore_v2()
        >>> fluxes.f
        f(-0.137898)
        >>> states.r
        r(89.271754)
        >>> fluxes.qr
        qr(25.590348)

        Empty storage:

        >>> states.r = 10.
        >>> model.calc_routingstore_v2()
        >>> fluxes.f
        f(0.000652)
        >>> states.r
        r(29.940201)

    """

    REQUIREDSEQUENCES = (grxjland_fluxes.Q9,)
    CONTROLPARAMETERS = (
        grxjland_control.X2,
        grxjland_control.X3,
        grxjland_control.X5,
    )

    UPDATEDSEQUENCES = (grxjland_states.R,)

    RESULTSEQUENCES = (
        grxjland_fluxes.F,
        grxjland_fluxes.Qr,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3 - con.x5)
        sta.r = max(0, sta.r + flu.q9 + flu.f)
        flu.qr = sta.r * (1 - (1 + (sta.r / con.x3) ** 4) ** (-0.25))
        sta.r = sta.r - flu.qr


class Calc_RoutingStore_V3(modeltools.Method):
    """Calculate groundwater exchange term F, level of the non-linear routing store R
    and the outflow Qr of the reservoir.

    This is the GR6J version of the routing store. 60 % of Q9 enters the routing store.
    # todo: wie Version 2 nur mit 60 % Gleichungen auseinander ziehen?

    Basic equations:

        The ground water exchange term F that acts on both flow components is
        calculated as:

      :math:`F = X2 (\\frac{R}{X3} - X5)`


        X2 is the water exchange coefficient. X2 can be either positive in case of
        water imports, negative for water exports or zero when there is no water
        exchange.
        The  higher the level in the routing store, the larger the  exchange. X5 can
        be seen as the external, quasi-stationary potential of the groundwater system
        and F is a ‘‘restoring flux’’ acting like a spring device with constant X2.
        Usually, X2 is negative: the more R/X3 de-parts from X5, the more intense the
        flux is, which tends to restore its value to X5.

        The level in the routing store is updated by adding the output Q9 of UH1 and F:

      :math:`R = max(0; R + Q9 + F)`

        The outflow Qr of the reservoir is then calculated as:

      :math:`Qr = R{1-[1+(\\frac{R}{X3})^{4}]^{-1/4}}`

        The level in the reservoir becomes:

      :math:`R = R - Qr`


    Examples:

        Filled storage

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x2(-0.163)
        >>> x3(100.)
        >>> x5(0.104)
        >>> fluxes.q9 = 20.
        >>> states.r = 95.
        >>> model.calc_routingstore_v3()
        >>> fluxes.f
        f(-0.137898)
        >>> states.r
        r(86.736252)
        >>> fluxes.qr
        qr(20.12585)

        Empty storage:

        >>> states.r = 10.
        >>> model.calc_routingstore_v3()
        >>> fluxes.f
        f(0.000652)
        >>> states.r
        r(21.987785)

    """

    REQUIREDSEQUENCES = (grxjland_fluxes.Q9,)
    CONTROLPARAMETERS = (
        grxjland_control.X2,
        grxjland_control.X3,
        grxjland_control.X5,
    )

    UPDATEDSEQUENCES = (grxjland_states.R,)

    RESULTSEQUENCES = (
        grxjland_fluxes.F,
        grxjland_fluxes.Qr,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3 - con.x5)
        sta.r = max(0, sta.r + 0.6 * flu.q9 + flu.f)
        flu.qr = sta.r * (1 - (1 + (sta.r / con.x3) ** 4) ** (-0.25))
        sta.r = sta.r - flu.qr


class Calc_ExponentialStore_V3(modeltools.Method):
    """Calculate exponential store.

    This is the exponential store of the GR6J version. 40 % of Q9 enters the routing
    store.

    Basic equations:

    TODO


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x6(4.5)
        >>> fluxes.q9 = 10.
        >>> fluxes.f = -0.5
        >>> states.r2 = 40.
        >>> model.calc_exponentialstore_v3()
        >>> states.r2
        r2(-0.000285)
        >>> fluxes.qr2
        qr2(43.500285)

        Negative storage values possible

        >>> states.r2 = -10.
        >>> fluxes.q9 = 0.1
        >>> model.calc_exponentialstore_v3()
        >>> states.r2
        r2(-10.880042)
        >>> fluxes.qr2
        qr2(0.420042)

        Negative storage values possible

        >>> states.r2 = -50.
        >>> fluxes.q9 = 0.1
        >>> model.calc_exponentialstore_v3()
        >>> states.r2
        r2(-50.460061)
        >>> fluxes.qr2
        qr2(0.000061)

    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q9,
        grxjland_fluxes.F,
    )
    CONTROLPARAMETERS = (grxjland_control.X6,)

    UPDATEDSEQUENCES = (grxjland_states.R2,)

    RESULTSEQUENCES = (grxjland_fluxes.Qr2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        sta.r2 = sta.r2 + 0.4 * flu.q9 + flu.f
        d_ar = max(-33.0, min(33.0, sta.r2 / con.x6))

        if d_ar > 7:
            flu.qr2 = sta.r2 + con.x6 / modelutils.exp(d_ar)
        elif d_ar < -7:
            flu.qr2 = con.x6 * modelutils.exp(d_ar)
        else:
            flu.qr2 = con.x6 * modelutils.log(modelutils.exp(d_ar) + 1.0)

        sta.r2 = sta.r2 - flu.qr2


class Calc_Qd_V1(modeltools.Method):
    """Calculate direct flow component.

    Basic equations:

        Output Q1 of unit hydrograph UH2 is subject to the same water exchange F as
        the routing storage to give the flow component as:

      :math:`Qd = max(0; Q1 + F)`


    Examples:

        Positive groundwater exchange:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.q1 = 20
        >>> fluxes.f = 20
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(40.0)

        Negative groundwater exchange:

        >>> fluxes.f = -10
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(10.0)

        Negative groundwater exchange exceeding outflow of unit hydrograph:
        >>> fluxes.f = -30
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(0.0)

    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Q1,
        grxjland_fluxes.F,
    )

    RESULTSEQUENCES = (grxjland_fluxes.Qd,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qd = max(0, flu.q1 + flu.f)


class Calc_Qt_V1(modeltools.Method):
    """Calculate total flow.

    Basic equations:

        Total streamflow is obtained by

      :math:`Qt = Qr + Qd`


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20
        >>> fluxes.qd = 10
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(30.0)

    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Qr,
        grxjland_fluxes.Qd,
    )

    RESULTSEQUENCES = (grxjland_fluxes.Qt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qt = flu.qr + flu.qd


class Calc_Qt_V3(modeltools.Method):
    """Calculate total flow.

    GR6jX model version

    Basic equations:

        Total streamflow is obtained by

      :math:`Qt = Qr + Qr2 + Qd`


    Examples:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20.
        >>> fluxes.qr2 = 10.
        >>> fluxes.qd = 10.
        >>> model.calc_qt_v3()
        >>> fluxes.qt
        qt(40.0)

    """

    REQUIREDSEQUENCES = (
        grxjland_fluxes.Qr,
        grxjland_fluxes.Qr2,
        grxjland_fluxes.Qd,
    )

    RESULTSEQUENCES = (grxjland_fluxes.Qt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qt = flu.qr + flu.qr2 + flu.qd


class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
      :math:`Q = QFactor \\cdot QT`


    """

    DERIVEDPARAMETERS = (grxjland_derived.QFactor,)
    REQUIREDSEQUENCES = (grxjland_fluxes.Qt,)
    RESULTSEQUENCES = (grxjland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += der.qfactor * flu.qt


class Model(modeltools.AdHocModel):
    """The GRxJ-Land base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_Pn_En_AE_V1,
        Calc_PS_V1,
        Calc_ProductionStore_V1,
        Calc_Pr_V1,
        Calc_UH1_V1,
        Calc_UH2_V1,
        Calc_UH2_V2,
        Calc_RoutingStore_V1,
        Calc_RoutingStore_V2,
        Calc_RoutingStore_V3,
        Calc_ExponentialStore_V3,
        Calc_Qd_V1,
        Calc_Qt_V1,
        Calc_Qt_V3,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
