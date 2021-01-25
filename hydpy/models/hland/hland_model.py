# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from standard library
from typing import *

# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils

# ...from hland
from hydpy.models.hland.hland_constants import FIELD, FOREST, GLACIER, ILAKE
from hydpy.models.hland import hland_control
from hydpy.models.hland import hland_derived
from hydpy.models.hland import hland_inputs
from hydpy.models.hland import hland_fluxes
from hydpy.models.hland import hland_states
from hydpy.models.hland import hland_logs
from hydpy.models.hland import hland_outlets


class Calc_TC_V1(modeltools.Method):
    """Adjust the measured air temperature to the altitude of the
    individual zones.

    Basic equation:
      :math:`TC = T - TCAlt \\cdot (ZoneZ-ZRelT)`

    Examples:

        Prepare two zones, the first one lying at the reference
        height and the second one 200 meters above:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(2)
        >>> zrelt(2.0)
        >>> zonez(2.0, 4.0)

        Applying the usual temperature lapse rate of 0.6°C/100m does
        not affect the temperature of the first zone but reduces the
        temperature of the second zone by 1.2°C:

        >>> tcalt(0.6)
        >>> inputs.t = 5.0
        >>> model.calc_tc_v1()
        >>> fluxes.tc
        tc(5.0, 3.8)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.TCAlt,
        hland_control.ZoneZ,
        hland_control.ZRelT,
    )
    REQUIREDSEQUENCES = (hland_inputs.T,)
    RESULTSEQUENCES = (hland_fluxes.TC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.tc[k] = inp.t - con.tcalt[k] * (con.zonez[k] - con.zrelt)


class Calc_TMean_V1(modeltools.Method):
    """Calculate the areal mean temperature of the subbasin.

    Examples:

        Prepare two zones, the first one being twice as large
        as the second one:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(2)
        >>> derived.relzonearea(2.0/3.0, 1.0/3.0)

        With temperature values of 5°C and 8°C  of the respective zones,
        the mean temperature is 6°C:

        >>> fluxes.tc = 5.0, 8.0
        >>> model.calc_tmean_v1()
        >>> fluxes.tmean
        tmean(6.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones,)
    DERIVEDPARAMETERS = (hland_derived.RelZoneArea,)
    REQUIREDSEQUENCES = (hland_fluxes.TC,)
    RESULTSEQUENCES = (hland_fluxes.TMean,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.tmean = 0.0
        for k in range(con.nmbzones):
            flu.tmean += der.relzonearea[k] * flu.tc[k]


class Calc_FracRain_V1(modeltools.Method):
    """Determine the temperature-dependent fraction of (liquid) rainfall
    and (total) precipitation.

    Basic equation:
      :math:`FracRain = \\frac{TC-(TT-\\frac{TTInt}{2})}{TTInt}`

    Restriction:
      :math:`0 \\leq FracRain \\leq 1`

    Examples:

        The threshold temperature of seven zones is 0°C and the corresponding
        temperature interval of mixed precipitation 2°C:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> tt(0.0)
        >>> ttint(2.0)

        The fraction of rainfall is zero below -1°C, is one above 1°C and
        increases linearly in between:

        >>> fluxes.tc = -10.0, -1.0, -0.5, 0.0, 0.5, 1.0, 10.0
        >>> model.calc_fracrain_v1()
        >>> fluxes.fracrain
        fracrain(0.0, 0.0, 0.25, 0.5, 0.75, 1.0, 1.0)

        Note the special case of a zero temperature interval.  With a
        actual temperature being equal to the threshold temperature, the
        rainfall fraction is one:

        >>> ttint(0.0)
        >>> model.calc_fracrain_v1()
        >>> fluxes.fracrain
        fracrain(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.TT,
        hland_control.TTInt,
    )
    REQUIREDSEQUENCES = (hland_fluxes.TC,)
    RESULTSEQUENCES = (hland_fluxes.FracRain,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if flu.tc[k] >= (con.tt[k] + con.ttint[k] / 2.0):
                flu.fracrain[k] = 1.0
            elif flu.tc[k] <= (con.tt[k] - con.ttint[k] / 2.0):
                flu.fracrain[k] = 0.0
            else:
                flu.fracrain[k] = (
                    flu.tc[k] - (con.tt[k] - con.ttint[k] / 2.0)
                ) / con.ttint[k]


class Calc_RFC_SFC_V1(modeltools.Method):
    """Calculate the corrected fractions rainfall/snowfall and total
    precipitation.

    Basic equations:
      :math:`RfC = RfCF \\cdot FracRain` \n
      :math:`SfC = SfCF \\cdot (1 - FracRain)`

    Examples:

        Assume five zones with different temperatures and hence
        different fractions of rainfall and total precipitation:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> fluxes.fracrain = 0.0, 0.25, 0.5, 0.75, 1.0

        With no rainfall and no snowfall correction (implied by the
        respective factors being one), the corrected fraction related
        to rainfall is identical with the original fraction and the
        corrected fraction related to snowfall behaves opposite:

        >>> rfcf(1.0)
        >>> sfcf(1.0)
        >>> model.calc_rfc_sfc_v1()
        >>> fluxes.rfc
        rfc(0.0, 0.25, 0.5, 0.75, 1.0)
        >>> fluxes.sfc
        sfc(1.0, 0.75, 0.5, 0.25, 0.0)

        With a negative rainfall correction of 20% and a positive
        snowfall correction of 20 % the corrected fractions are:

        >>> rfcf(0.8)
        >>> sfcf(1.2)
        >>> model.calc_rfc_sfc_v1()
        >>> fluxes.rfc
        rfc(0.0, 0.2, 0.4, 0.6, 0.8)
        >>> fluxes.sfc
        sfc(1.2, 0.9, 0.6, 0.3, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.RfCF,
        hland_control.SfCF,
    )
    REQUIREDSEQUENCES = (hland_fluxes.FracRain,)
    RESULTSEQUENCES = (
        hland_fluxes.RfC,
        hland_fluxes.SfC,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.rfc[k] = flu.fracrain[k] * con.rfcf[k]
            flu.sfc[k] = (1.0 - flu.fracrain[k]) * con.sfcf[k]


class Calc_PC_V1(modeltools.Method):
    """Apply the precipitation correction factors and adjust precipitation
    to the altitude of the individual zones.

    Basic equation:
      :math:`PC = P \\cdot PCorr
      \\cdot (1+PCAlt \\cdot (ZoneZ-ZRelP))
      \\cdot (RfC + SfC)`

    Examples:

        Five zones are at an elevation of 200 m.  A precipitation value
        of 5 mm has been measured at a gauge at an elevation of 300 m:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zrelp(2.0)
        >>> zonez(3.0)
        >>> inputs.p = 5.0

        The first four zones illustrate the individual precipitation
        corrections due to the general precipitation correction factor
        (|PCorr|, first zone), the altitude correction factor (|PCAlt|,
        second zone), the rainfall related correction (|RfC|, third zone),
        and the snowfall related correction factor (|SfC|, fourth zone).
        The fifth zone illustrates the interaction between all corrections:

        >>> pcorr(1.3, 1.0, 1.0, 1.0, 1.3)
        >>> pcalt(0.0, 0.1, 0.0, 0.0, 0.1)
        >>> fluxes.rfc = 0.5, 0.5, 0.4, 0.5, 0.4
        >>> fluxes.sfc = 0.5, 0.5, 0.5, 0.7, 0.7
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(6.5, 5.5, 4.5, 6.0, 7.865)

        Usually, one would set zero or positive values for parameter |PCAlt|.
        But it is also allowed to set negative values, in order to reflect
        possible negative relationships between precipitation and altitude.
        To prevent from calculating negative precipitation when too large
        negative values are applied, a truncation is performed:

        >>> pcalt(-1.0)
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(0.0, 0.0, 0.0, 0.0, 0.0)

    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.PCAlt,
        hland_control.ZoneZ,
        hland_control.ZRelP,
        hland_control.PCorr,
    )
    REQUIREDSEQUENCES = (
        hland_inputs.P,
        hland_fluxes.RfC,
        hland_fluxes.SfC,
    )
    RESULTSEQUENCES = (hland_fluxes.PC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.pc[k] = inp.p * (1.0 + con.pcalt[k] * (con.zonez[k] - con.zrelp))
            if flu.pc[k] <= 0.0:
                flu.pc[k] = 0.0
            else:
                flu.pc[k] *= con.pcorr[k] * (flu.rfc[k] + flu.sfc[k])


class Calc_EP_V1(modeltools.Method):
    """Adjust potential norm evaporation to the actual temperature.

    Basic equation:
      :math:`EP = EPN \\cdot (1 + ETF \\cdot (TMean - TN))`

    Restriction:
      :math:`0 \\leq EP \\leq 2 \\cdot EPN`

    Examples:

        Assume four zones with different values of the temperature
        related factor for the adjustment of evaporation (the
        negative value of the first zone is not meaningful, but used
        for illustration purporses):

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(4)
        >>> etf(-0.5, 0.0, 0.1, 0.5)
        >>> inputs.tn = 20.0
        >>> inputs.epn = 2.0

        With mean temperature equal to norm temperature, actual
        (uncorrected) evaporation is equal to norm evaporation:

        >>> fluxes.tmean = 20.0
        >>> model.calc_ep_v1()
        >>> fluxes.ep
        ep(2.0, 2.0, 2.0, 2.0)

        With mean temperature 5°C higher than norm temperature, potential
        evaporation is increased by 1 mm for the third zone, which
        possesses a very common adjustment factor.  For the first zone,
        potential evaporation is 0 mm (which is the smallest value
        allowed), and for the fourth zone it is the double value of the
        norm evaporation (which is the largest value allowed):

        >>> fluxes.tmean  = 25.0
        >>> model.calc_ep_v1()
        >>> fluxes.ep
        ep(0.0, 2.0, 3.0, 4.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ETF,
    )
    REQUIREDSEQUENCES = (
        hland_inputs.EPN,
        hland_inputs.TN,
        hland_fluxes.TMean,
    )
    RESULTSEQUENCES = (hland_fluxes.EP,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.ep[k] = inp.epn * (1.0 + con.etf[k] * (flu.tmean - inp.tn))
            flu.ep[k] = min(max(flu.ep[k], 0.0), 2.0 * inp.epn)


class Calc_EPC_V1(modeltools.Method):
    """Apply the evaporation correction factors and adjust evaporation
    to the altitude of the individual zones.

    Calculate the areal mean of (uncorrected) potential evaporation
    for the subbasin, adjust it to the individual zones in accordance
    with their heights and perform some corrections, among which one
    depends on the actual precipitation.

    Basic equation:
      :math:`EPC = EP \\cdot ECorr
      \\cdot (1+ECAlt \\cdot (ZoneZ-ZRelE))
      \\cdot exp(-EPF \\cdot PC)`


    Examples:

        Four zones are at an elevation of 200 m.  A (uncorrected)
        potential evaporation value of 2 mm and a (corrected) precipitation
        value of 5 mm have been determined for each zone beforehand:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbzones(4)
        >>> zrele(2.0)
        >>> zonez(3.0)
        >>> fluxes.ep = 2.0
        >>> fluxes.pc = 5.0

        The first three zones  illustrate the individual evaporation
        corrections due to the general evaporation correction factor
        (|ECorr|, first zone), the altitude correction factor (|ECAlt|,
        second zone), the precipitation related correction factor
        (|EPF|, third zone).  The fourth zone illustrates the interaction
        between all corrections:

        >>> ecorr(1.3, 1.0, 1.0, 1.3)
        >>> ecalt(0.0, 0.1, 0.0, 0.1)
        >>> epf(0.0, 0.0, -numpy.log(0.7)/10.0, -numpy.log(0.7)/10.0)
        >>> model.calc_epc_v1()
        >>> fluxes.epc
        epc(2.6, 1.8, 1.4, 1.638)

        To prevent from calculating negative evaporation values when too
        large values for parameter |ECAlt| are set, a truncation is performed:

        >>> ecalt(2.0)
        >>> model.calc_epc_v1()
        >>> fluxes.epc
        epc(0.0, 0.0, 0.0, 0.0)

    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ECorr,
        hland_control.ECAlt,
        hland_control.ZoneZ,
        hland_control.ZRelE,
        hland_control.EPF,
    )
    REQUIREDSEQUENCES = (
        hland_fluxes.EP,
        hland_fluxes.PC,
    )
    RESULTSEQUENCES = (hland_fluxes.EPC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.epc[k] = (
                flu.ep[k]
                * con.ecorr[k]
                * (1.0 - con.ecalt[k] * (con.zonez[k] - con.zrele))
            )
            if flu.epc[k] <= 0.0:
                flu.epc[k] = 0.0
            else:
                flu.epc[k] *= modelutils.exp(-con.epf[k] * flu.pc[k])


class Calc_TF_Ic_V1(modeltools.Method):
    """Calculate throughfall and update the interception storage
    accordingly.

    Basic equation:
      :math:`TF = \\Bigl \\lbrace
      {
      {PC \\ | \\ Ic = IcMax}
      \\atop
      {0 \\ | \\ Ic < IcMax}
      }`

    Examples:

        Initialize six zones of different types.  Assume a
        generall maximum interception capacity of 2 mm. All zones receive
        a 0.5 mm input of precipitation:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(GLACIER, ILAKE, FIELD, FOREST, FIELD, FIELD)
        >>> icmax(2.0)
        >>> fluxes.pc = 0.5
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_tf_ic_v1()

        For glaciers (first zone) and internal lakes (second zone) the
        interception routine does not apply.  Hence, all precipitation is
        routed as throughfall. For fields and forests, the interception
        routine is identical (usually, only larger capacities for forests
        are assumed, due to their higher leaf area index).  Hence, the
        results of the third and the second zone are equal.  The last
        three zones demonstrate, that all precipitation is stored until
        the interception capacity is reached; afterwards, all precepitation
        is routed as throughfall.  Initial storage reduces the effective
        capacity of the respective simulation step:

        >>> states.ic
        ic(0.0, 0.0, 0.5, 0.5, 1.5, 2.0)
        >>> fluxes.tf
        tf(0.5, 0.5, 0.0, 0.0, 0.0, 0.5)

        A zero precipitation example:

        >>> fluxes.pc = 0.0
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_tf_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
        >>> fluxes.tf
        tf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        A high precipitation example:

        >>> fluxes.pc = 5.0
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_tf_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 2.0, 2.0, 2.0, 2.0)
        >>> fluxes.tf
        tf(5.0, 5.0, 3.0, 3.0, 4.0, 5.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.IcMax,
    )
    REQUIREDSEQUENCES = (hland_fluxes.PC,)
    UPDATEDSEQUENCES = (hland_states.Ic,)
    RESULTSEQUENCES = (hland_fluxes.TF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST):
                flu.tf[k] = max(flu.pc[k] - (con.icmax[k] - sta.ic[k]), 0.0)
                sta.ic[k] += flu.pc[k] - flu.tf[k]
            else:
                flu.tf[k] = flu.pc[k]
                sta.ic[k] = 0.0


class Calc_EI_Ic_V1(modeltools.Method):
    """Calculate interception evaporation and update the interception
    storage accordingly.

    Basic equation:
      :math:`EI = \\Bigl \\lbrace
      {
      {EPC \\ | \\ Ic > 0}
      \\atop
      {0 \\ | \\ Ic = 0}
      }`

    Examples:

        Initialize six zones of different types.  For all zones
        a (corrected) potential evaporation of 0.5 mm is given:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(GLACIER, ILAKE, FIELD, FOREST, FIELD, FIELD)
        >>> fluxes.epc = 0.5
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_ei_ic_v1()

        For glaciers (first zone) and internal lakes (second zone) the
        interception routine does not apply.  Hence, no interception
        evaporation can occur.  For fields and forests, the interception
        routine is identical (usually, only larger capacities for forests
        are assumed, due to their higher leaf area index).  Hence, the
        results of the third and the second zone are equal.  The last
        three zones demonstrate, that all interception evaporation is equal
        to potential evaporation until the interception storage is empty;
        afterwards, interception evaporation is zero:

        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 0.5, 1.5)
        >>> fluxes.ei
        ei(0.0, 0.0, 0.0, 0.0, 0.5, 0.5)

        A zero evaporation example:

        >>> fluxes.epc = 0.0
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_ei_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
        >>> fluxes.ei
        ei(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        A high evaporation example:

        >>> fluxes.epc = 5.0
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_ei_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.ei
        ei(0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
    )
    REQUIREDSEQUENCES = (hland_fluxes.EPC,)
    UPDATEDSEQUENCES = (hland_states.Ic,)
    RESULTSEQUENCES = (hland_fluxes.EI,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST):
                flu.ei[k] = min(flu.epc[k], sta.ic[k])
                sta.ic[k] -= flu.ei[k]
            else:
                flu.ei[k] = 0.0
                sta.ic[k] = 0.0


class Calc_SP_WC_V1(modeltools.Method):
    """Add throughfall to the snow layer.

    Basic equations:
      :math:`\\frac{dSP}{dt} = TF \\cdot \\frac{SfC}{SfC+RfC}` \n
      :math:`\\frac{dWC}{dt} = TF \\cdot \\frac{RfC}{SfC+RfC}`

    Exemples:

        Consider the following setting, in which eight zones of
        different type receive a throughfall of 10mm:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(8)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD, FIELD, FIELD)
        >>> fluxes.tf = 10.0
        >>> fluxes.sfc = 0.5, 0.5, 0.5, 0.5, 0.2, 0.8, 1.0, 4.0
        >>> fluxes.rfc = 0.5, 0.5, 0.5, 0.5, 0.8, 0.2, 4.0, 1.0
        >>> states.sp = 0.0
        >>> states.wc = 0.0
        >>> model.calc_sp_wc_v1()
        >>> states.sp
        sp(0.0, 5.0, 5.0, 5.0, 2.0, 8.0, 2.0, 8.0)
        >>> states.wc
        wc(0.0, 5.0, 5.0, 5.0, 8.0, 2.0, 8.0, 2.0)

        The snow routine does not apply for internal lakes, which is why
        both  the ice storage and the water storage of the first zone
        remain unchanged.  The snow routine is identical for glaciers,
        fields and forests in the current context, which is why the
        results of the second, third, and fourth zone are equal.  The
        last four zones illustrate that the corrected snowfall fraction
        as well as the corrected rainfall fraction are applied in a
        relative manner, as the total amount of water yield has been
        corrected in the interception module already.

        When both factors are zero, the neither the water nor the ice
        content of the snow layer changes:

        >>> fluxes.sfc = 0.0
        >>> fluxes.rfc = 0.0
        >>> states.sp = 2.0
        >>> states.wc = 0.0
        >>> model.calc_sp_wc_v1()
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
    )
    REQUIREDSEQUENCES = (
        hland_fluxes.TF,
        hland_fluxes.RfC,
        hland_fluxes.SfC,
    )
    UPDATEDSEQUENCES = (
        hland_states.WC,
        hland_states.SP,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                if (flu.rfc[k] + flu.sfc[k]) > 0.0:
                    sta.wc[k] += flu.tf[k] * flu.rfc[k] / (flu.rfc[k] + flu.sfc[k])
                    sta.sp[k] += flu.tf[k] * flu.sfc[k] / (flu.rfc[k] + flu.sfc[k])
            else:
                sta.wc[k] = 0.0
                sta.sp[k] = 0.0


class Calc_Melt_SP_WC_V1(modeltools.Method):
    """Calculate melting of the ice content within the snow layer and
    update both the snow layers ice and the water content.

    Basic equations:
      :math:`\\frac{dSP}{dt} = - Melt` \n
      :math:`\\frac{dWC}{dt} = + Melt` \n
      :math:`Melt = min(cfmax \\cdot (TC-TTM), SP)` \n

    Examples:

        Six zones are initialized with the same threshold
        temperature and degree day factor, but  with different zone types
        and initial ice contents:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> cfmax(4.0)
        >>> derived.ttm = 2.0
        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = 2.0

        Note that the assumed length of the simulation step is only a
        half day.  Hence the effective value of the degree day factor
        is not 4 but 2:

        >>> cfmax
        cfmax(4.0)
        >>> cfmax.values
        array([ 2.,  2.,  2.,  2.,  2.,  2.])

        When the actual temperature is equal to the threshold
        temperature for melting and refreezing, no melting  occurs
        and the states remain unchanged:

        >>> fluxes.tc = 2.0
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 10.0, 10.0, 10.0, 5.0, 0.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)

        The same holds true for an actual temperature lower than the
        threshold temperature:

        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = 2.0
        >>> fluxes.tc = -1.0
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 10.0, 10.0, 10.0, 5.0, 0.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)

        With an actual temperature 3°C above the threshold temperature,
        melting can occur. Actual melting is consistent with potential
        melting, except for the first zone, which is an internal lake,
        and the last two zones, for which potential melting exceeds the
        available frozen water content of the snow layer:

        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = 2.0
        >>> fluxes.tc = 5.0
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 6.0, 6.0, 6.0, 5.0, 0.0)
        >>> states.sp
        sp(0.0, 4.0, 4.0, 4.0, 0.0, 0.0)
        >>> states.wc
        wc(0.0, 8.0, 8.0, 8.0, 7.0, 2.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.CFMax,
    )
    DERIVEDPARAMETERS = (hland_derived.TTM,)
    REQUIREDSEQUENCES = (hland_fluxes.TC,)
    UPDATEDSEQUENCES = (
        hland_states.WC,
        hland_states.SP,
    )
    RESULTSEQUENCES = (hland_fluxes.Melt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                if flu.tc[k] > der.ttm[k]:
                    flu.melt[k] = min(
                        con.cfmax[k] * (flu.tc[k] - der.ttm[k]), sta.sp[k]
                    )
                    sta.sp[k] -= flu.melt[k]
                    sta.wc[k] += flu.melt[k]
                else:
                    flu.melt[k] = 0.0
            else:
                flu.melt[k] = 0.0
                sta.wc[k] = 0.0
                sta.sp[k] = 0.0


class Calc_Refr_SP_WC_V1(modeltools.Method):
    """Calculate refreezing of the water content within the snow layer and
    update both the snow layers ice and the water content.

    Basic equations:
      :math:`\\frac{dSP}{dt} =  + Refr` \n
      :math:`\\frac{dWC}{dt} =  - Refr` \n
      :math:`Refr = min(cfr \\cdot cfmax \\cdot (TTM-TC), WC)`

    Examples:

        Six zones are initialized with the same threshold
        temperature, degree day factor and refreezing coefficient, but
        with different zone types and initial states:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> cfmax(4.0)
        >>> cfr(0.1)
        >>> derived.ttm = 2.0
        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 0.5, 0.0

        Note that the assumed length of the simulation step is only
        a half day.  Hence the effective value of the degree day
        factor is not 4 but 2:

        >>> cfmax
        cfmax(4.0)
        >>> cfmax.values
        array([ 2.,  2.,  2.,  2.,  2.,  2.])

        When the actual temperature is equal to the threshold
        temperature for melting and refreezing, neither no refreezing
        occurs and the states remain unchanged:

        >>> fluxes.tc = 2.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        The same holds true for an actual temperature higher than the
        threshold temperature:

        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 0.5, 0.0
        >>> fluxes.tc = 2.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        With an actual temperature 3°C above the threshold temperature,
        only melting can occur. Actual melting is consistent with
        potential melting, except for the first zone, which is an
        internal lake, and the last two zones, for which potential
        melting exceeds the available frozen water content of the
        snow layer:

        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 0.5, 0.0
        >>> fluxes.tc = 5.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        With an actual temperature 3°C below the threshold temperature,
        refreezing can occur. Actual refreezing is consistent with
        potential refreezing, except for the first zone, which is an
        internal lake, and the last two zones, for which potential
        refreezing exceeds the available liquid water content of the
        snow layer:

        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 0.5, 0.0
        >>> fluxes.tc = -1.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.6, 0.6, 0.6, 0.5, 0.0)
        >>> states.sp
        sp(0.0, 2.6, 2.6, 2.6, 2.5, 2.0)
        >>> states.wc
        wc(0.0, 0.4, 0.4, 0.4, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.CFR,
        hland_control.CFMax,
    )
    DERIVEDPARAMETERS = (hland_derived.TTM,)
    REQUIREDSEQUENCES = (hland_fluxes.TC,)
    UPDATEDSEQUENCES = (
        hland_states.WC,
        hland_states.SP,
    )
    RESULTSEQUENCES = (hland_fluxes.Refr,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                if flu.tc[k] < der.ttm[k]:
                    flu.refr[k] = min(
                        con.cfr[k] * con.cfmax[k] * (der.ttm[k] - flu.tc[k]), sta.wc[k]
                    )
                    sta.sp[k] += flu.refr[k]
                    sta.wc[k] -= flu.refr[k]
                else:
                    flu.refr[k] = 0.0
            else:
                flu.refr[k] = 0.0
                sta.wc[k] = 0.0
                sta.sp[k] = 0.0


class Calc_In_WC_V1(modeltools.Method):
    """Calculate the actual water release from the snow layer due to the
    exceedance of the snow layers capacity for (liquid) water.

    Basic equations:
      :math:`\\frac{dWC}{dt} = -In` \n
      :math:`-In = max(WC - WHC \\cdot SP, 0)`

    Examples:

        Initialize six zones of different types and frozen water
        contents of the snow layer and set the relative water holding
        capacity to 20% of the respective frozen water content:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> whc(0.2)
        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 5.0, 0.0

        Also set the actual value of stand precipitation to 5 mm/d:

        >>> fluxes.tf = 5.0

        When there is no (liquid) water content in the snow layer, no water
        can be released:

        >>> states.wc = 0.0
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        When there is a (liquid) water content in the snow layer, the water
        release depends on the frozen water content.  Note the special
        cases of the first zone being an internal lake, for which the snow
        routine does not apply, and of the last zone, which has no ice
        content and thus effectively not really a snow layer:

        >>> states.wc = 5.0
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 3.0, 3.0, 3.0, 4.0, 5.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 1.0, 0.0)

        When the relative water holding capacity is assumed to be zero,
        all liquid water is released:

        >>> whc(0.0)
        >>> states.wc = 5.0
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 5.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        Note that for the single lake zone, stand precipitation is
        directly passed to `in_` in all three examples.
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.WHC,
    )
    REQUIREDSEQUENCES = (
        hland_fluxes.TF,
        hland_states.SP,
    )
    UPDATEDSEQUENCES = (hland_states.WC,)
    RESULTSEQUENCES = (hland_fluxes.In_,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                flu.in_[k] = max(sta.wc[k] - con.whc[k] * sta.sp[k], 0.0)
                sta.wc[k] -= flu.in_[k]
            else:
                flu.in_[k] = flu.tf[k]
                sta.wc[k] = 0.0


class Calc_GlMelt_In_V1(modeltools.Method):
    """Calculate melting from glaciers which are actually not covered by
    a snow layer and add it to the water release of the snow module.

    Basic equation:

      :math:`GlMelt = \\Bigl \\lbrace
      {
      {max(GMelt \\cdot (TC-TTM), 0) \\ | \\ SP = 0}
      \\atop
      {0 \\ | \\ SP > 0}
      }`

    Examples:

        Seven zones are prepared, but glacier melting occurs only
        in the fourth one, as the first three zones are no glaciers, the
        fifth zone is covered by a snow layer and the actual temperature
        of the last two zones is not above the threshold temperature:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbzones(7)
        >>> zonetype(FIELD, FOREST, ILAKE, GLACIER, GLACIER, GLACIER, GLACIER)
        >>> gmelt(4.)
        >>> derived.ttm(2.)
        >>> states.sp = 0., 0., 0., 0., .1, 0., 0.
        >>> fluxes.tc = 3., 3., 3., 3., 3., 2., 1.
        >>> fluxes.in_ = 3.
        >>> model.calc_glmelt_in_v1()
        >>> fluxes.glmelt
        glmelt(0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0)
        >>> fluxes.in_
        in_(3.0, 3.0, 3.0, 5.0, 3.0, 3.0, 3.0)

        Note that the assumed length of the simulation step is only
        a half day. Hence the effective value of the degree day factor
        is not 4 but 2:

        >>> gmelt
        gmelt(4.0)
        >>> gmelt.values
        array([ 2.,  2.,  2.,  2.,  2.,  2.,  2.])
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.GMelt,
    )
    DERIVEDPARAMETERS = (hland_derived.TTM,)
    REQUIREDSEQUENCES = (
        hland_states.SP,
        hland_fluxes.TC,
    )
    UPDATEDSEQUENCES = (hland_fluxes.In_,)
    RESULTSEQUENCES = (hland_fluxes.GlMelt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if (
                (con.zonetype[k] == GLACIER)
                and (sta.sp[k] <= 0.0)
                and (flu.tc[k] > der.ttm[k])
            ):
                flu.glmelt[k] = con.gmelt[k] * (flu.tc[k] - der.ttm[k])
                flu.in_[k] += flu.glmelt[k]
            else:
                flu.glmelt[k] = 0.0


class Calc_R_SM_V1(modeltools.Method):
    """Calculate effective precipitation and update soil moisture.

    Basic equations:
      :math:`\\frac{dSM}{dt} = IN - R` \n
      :math:`R = IN \\cdot \\left(\\frac{SM}{FC}\\right)^{Beta}`


    Examples:

        Initialize six zones of different types.  The field
        capacity of all fields and forests is set to 200mm, the input
        of each zone is 10mm:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> fc(200.0)
        >>> fluxes.in_ = 10.0

        With a common nonlinearity parameter value of 2, a relative
        soil moisture of 50%  (zones three and four) results in a
        discharge coefficient of 25%. For a soil completely dried
        (zone five) or completely saturated (one six) the discharge
        coefficient does not depend on the nonlinearity parameter and
        is 0% and 100% respectively.  Glaciers and internal lakes also
        always route 100% of their input as effective precipitation:

        >>> beta(2.0)
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 2.5, 2.5, 0.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 107.5, 107.5, 10.0, 200.0)

        Through decreasing the nonlinearity parameter, the discharge
        coefficient increases.  A parameter value of zero leads to a
        discharge coefficient of 100% for any soil moisture:

        >>> beta(0.0)
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        With zero field capacity, the discharge coefficient also always
        equates to 100%:

        >>> fc(0.0)
        >>> beta(2.0)
        >>> states.sm = 0.0
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
        hland_control.Beta,
    )
    REQUIREDSEQUENCES = (hland_fluxes.In_,)
    UPDATEDSEQUENCES = (hland_states.SM,)
    RESULTSEQUENCES = (hland_fluxes.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST):
                if con.fc[k] > 0.0:
                    flu.r[k] = flu.in_[k] * (sta.sm[k] / con.fc[k]) ** con.beta[k]
                    flu.r[k] = max(flu.r[k], sta.sm[k] + flu.in_[k] - con.fc[k])
                else:
                    flu.r[k] = flu.in_[k]
                sta.sm[k] += flu.in_[k] - flu.r[k]
            else:
                flu.r[k] = flu.in_[k]
                sta.sm[k] = 0.0


class Calc_CF_SM_V1(modeltools.Method):
    """Calculate capillary flow and update soil moisture.

    Basic equations:
      :math:`\\frac{dSM}{dt} = CF` \n
      :math:`CF = CFLUX \\cdot (1 - \\frac{SM}{FC})`

    Examples:

        Initialize six zones of different types.  The field
        capacity of als fields and forests is set to 200mm, the maximum
        capillary flow rate is 4mm/d:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> fc(200.0)
        >>> cflux(4.0)

        Note that the assumed length of the simulation step is only
        a half day.  Hence the maximum capillary flow per simulation
        step is 2 instead of 4:

        >>> cflux
        cflux(4.0)
        >>> cflux.values
        array([ 2.,  2.,  2.,  2.,  2.,  2.])

        For fields and forests, the actual capillary return flow depends
        on the relative soil moisture deficite, if either the upper zone
        layer provides enough water...

        >>> fluxes.r = 0.0
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 20.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 1.0, 1.0, 2.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 101.0, 101.0, 2.0, 200.0)

        ...our enough effective precipitation is generated, which can be
        rerouted directly:

        >>> cflux(4.0)
        >>> fluxes.r = 10.0
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 0.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 1.0, 1.0, 2.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 101.0, 101.0, 2.0, 200.0)

        If the upper zone layer is empty and no effective precipitation is
        generated, capillary flow is zero:

        >>> cflux(4.0)
        >>> fluxes.r = 0.0
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 0.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        Here an example, where both the upper zone layer and effective
        precipitation provide water for the capillary flow, but less then
        the maximum flow rate times the relative soil moisture:

        >>> cflux(4.0)
        >>> fluxes.r = 0.1
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 0.2
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.3, 0.3, 0.3, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 100.3, 100.3, 0.3, 200.0)

        Even unrealistic high maximum capillary flow rates do not result
        in overfilled soils:

        >>> cflux(1000.0)
        >>> fluxes.r = 200.0
        >>> states.sm = 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 200.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 100.0, 100.0, 200.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 200.0, 200.0, 200.0, 200.0)

        For (unrealistic) soils with zero field capacity, capillary flow
        is always zero:

        >>> fc(0.0)
        >>> states.sm = 0.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
        hland_control.CFlux,
    )
    REQUIREDSEQUENCES = (
        hland_fluxes.R,
        hland_states.UZ,
    )
    UPDATEDSEQUENCES = (hland_states.SM,)
    RESULTSEQUENCES = (hland_fluxes.CF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST):
                if con.fc[k] > 0.0:
                    flu.cf[k] = con.cflux[k] * (1.0 - sta.sm[k] / con.fc[k])
                    flu.cf[k] = min(flu.cf[k], sta.uz + flu.r[k])
                    flu.cf[k] = min(flu.cf[k], con.fc[k] - sta.sm[k])
                else:
                    flu.cf[k] = 0.0
                sta.sm[k] += flu.cf[k]
            else:
                flu.cf[k] = 0.0
                sta.sm[k] = 0.0


class Calc_EA_SM_V1(modeltools.Method):
    """Calculate soil evaporation and update soil moisture.

    Basic equations:
      :math:`\\frac{dSM}{dt} = - EA` \n
      :math:`EA_{temp} = \\biggl \\lbrace
      {
      {EPC \\cdot min\\left(\\frac{SM}{LP \\cdot FC}, 1\\right)
      \\ | \\ SP = 0}
      \\atop
      {0 \\ | \\ SP > 0}
      }` \n
      :math:`EA = EA_{temp} - max(ERED \\cdot (EA_{temp} + EI - EPC), 0)`

    Examples:

        Initialize seven zones of different types.  The field capacity
         of all fields and forests is set to 200mm, potential evaporation
         and interception evaporation are 2mm and 1mm respectively:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD, FIELD)
        >>> fc(200.0)
        >>> lp(0.0, 0.0, 0.5, 0.5, 0.0, 0.8, 1.0)
        >>> ered(0.0)
        >>> fluxes.epc = 2.0
        >>> fluxes.ei = 1.0
        >>> states.sp = 0.0

        Only fields and forests include soils; for glaciers and zones (the
        first two zones) no soil evaporation is performed.  For fields and
        forests, the underlying calculations are the same. In the following
        example, the relative soil moisture is 50% in all field and forest
        zones.  Hence, differences in soil evaporation are related to the
        different soil evaporation parameter values only:

        >>> states.sm = 100.0
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 2.0, 2.0, 2.0, 1.25, 1.0)
        >>> states.sm
        sm(0.0, 0.0, 98.0, 98.0, 98.0, 98.75, 99.0)

        In the last example, evaporation values of 2mm have been calculated
        for some zones despite the fact, that these 2mm added to the actual
        interception evaporation of 1mm exceed potential evaporation.  This
        behaviour can be reduced...

        >>> states.sm = 100.0
        >>> ered(0.5)
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 1.5, 1.5, 1.5, 1.125, 1.0)
        >>> states.sm
        sm(0.0, 0.0, 98.5, 98.5, 98.5, 98.875, 99.0)

        ...or be completely excluded:

        >>> states.sm = 100.0
        >>> ered(1.0)
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> states.sm
        sm(0.0, 0.0, 99.0, 99.0, 99.0, 99.0, 99.0)

        Any occurrence of a snow layer suppresses soil evaporation
        completely:

        >>> states.sp = 0.01
        >>> states.sm = 100.0
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0)

        For (unrealistic) soils with zero field capacity, soil evaporation
        is always zero:

        >>> fc(0.0)
        >>> states.sm = 0.0
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.LP,
        hland_control.FC,
        hland_control.ERed,
    )
    REQUIREDSEQUENCES = (
        hland_states.SP,
        hland_fluxes.EPC,
        hland_fluxes.EI,
    )
    UPDATEDSEQUENCES = (hland_states.SM,)
    RESULTSEQUENCES = (hland_fluxes.EA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST):
                if sta.sp[k] <= 0.0:
                    if (con.lp[k] * con.fc[k]) > 0.0:
                        flu.ea[k] = flu.epc[k] * sta.sm[k] / (con.lp[k] * con.fc[k])
                        flu.ea[k] = min(flu.ea[k], flu.epc[k])
                    else:
                        flu.ea[k] = flu.epc[k]
                    flu.ea[k] -= max(
                        con.ered[k] * (flu.ea[k] + flu.ei[k] - flu.epc[k]), 0.0
                    )
                    flu.ea[k] = min(flu.ea[k], sta.sm[k])
                else:
                    flu.ea[k] = 0.0
                sta.sm[k] -= flu.ea[k]
            else:
                flu.ea[k] = 0.0
                sta.sm[k] = 0.0


class Calc_InUZ_V1(modeltools.Method):
    """Accumulate the total inflow into the upper zone layer.

    Basic equation:
      :math:`InUZ = R - CF`

    Examples:

        Initialize three zones of different relative `land sizes`
        (area related to the total size of the subbasin except lake areas):

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> zonetype(FIELD, ILAKE, GLACIER)
        >>> derived.rellandzonearea = 2.0/3.0, 0.0, 1.0/3.0
        >>> fluxes.r = 6.0, 0.0, 2.0
        >>> fluxes.cf = 2.0, 0.0, 1.0
        >>> model.calc_inuz_v1()
        >>> fluxes.inuz
        inuz(3.0)

        Internal lakes do not contribute to the upper zone layer.  Hence
        for a subbasin consisting only of interal lakes a zero input
        value would be calculated:

        >>> zonetype(ILAKE, ILAKE, ILAKE)
        >>> model.calc_inuz_v1()
        >>> fluxes.inuz
        inuz(0.0)

    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
    )
    DERIVEDPARAMETERS = (hland_derived.RelLandZoneArea,)
    REQUIREDSEQUENCES = (
        hland_fluxes.R,
        hland_fluxes.CF,
    )
    RESULTSEQUENCES = (hland_fluxes.InUZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inuz = 0.0
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                flu.inuz += der.rellandzonearea[k] * (flu.r[k] - flu.cf[k])


class Calc_ContriArea_V1(modeltools.Method):
    """Determine the relative size of the contributing area of the whole
    subbasin.

    Basic equation:
      :math:`ContriArea = \\left( \\frac{SM}{FC} \\right)^{Beta}`

    Examples:

        Four zones are initialized, but only the first two zones
        of type field and forest are taken into account in the calculation
        of the relative contributing area of the catchment (even, if also
        glaciers contribute to the inflow of the upper zone layer):

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(4)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
        >>> beta(2.0)
        >>> fc(200.0)
        >>> resparea(True)
        >>> derived.relsoilarea(0.5)
        >>> derived.relsoilzonearea(1.0/3.0, 2.0/3.0, 0.0, 0.0)

        With a relative soil moisture of 100 % in the whole subbasin, the
        contributing area is also estimated as 100 %,...

        >>> states.sm = 200.0
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ...and relative soil moistures of 0% result in an contributing
        area of 0 %:

        >>> states.sm = 0.0
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(0.0)

        With the given value 2 of the nonlinearity parameter Beta, soil
        moisture of 50 % results in a contributing area estimate of 25%:

        >>> states.sm = 100.0
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(0.25)

        Setting the response area option to False,...

        >>> resparea(False)
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ... setting the soil area (total area of all field and forest
        zones in the subbasin) to zero...,

        >>> resparea(True)
        >>> derived.relsoilarea(0.0)
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ...or setting all field capacities to zero...

        >>> derived.relsoilarea(0.5)
        >>> fc(0.0)
        >>> states.sm = 0.0
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ...leads to contributing area values of 100 %.
    """

    CONTROLPARAMETERS = (
        hland_control.RespArea,
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
        hland_control.Beta,
    )
    DERIVEDPARAMETERS = (
        hland_derived.RelSoilArea,
        hland_derived.RelSoilZoneArea,
    )
    REQUIREDSEQUENCES = (hland_states.SM,)
    RESULTSEQUENCES = (hland_fluxes.ContriArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.contriarea = 1.0
        if con.resparea and (der.relsoilarea > 0.0):
            for k in range(con.nmbzones):
                if con.zonetype[k] in (FIELD, FOREST):
                    if con.fc[k] > 0.0:
                        flu.contriarea *= (
                            sta.sm[k] / con.fc[k]
                        ) ** der.relsoilzonearea[k]
            flu.contriarea **= con.beta[k]


class Calc_Q0_Perc_UZ_V1(modeltools.Method):
    """Perform the upper zone layer routine which determines percolation
    to the lower zone layer and the fast response of the hland model.

    Note that the system behaviour of this method depends strongly on the
    specifications of the options |RespArea| and |RecStep|.

    Basic equations:
      :math:`\\frac{dUZ}{dt} = InUZ - Perc - Q0` \n
      :math:`Perc = PercMax \\cdot ContriArea` \n
      :math:`Q0 = K * \\cdot \\left( \\frac{UZ}{ContriArea} \\right)^{1+Alpha}`

    Examples:

        The upper zone layer routine is an exception compared to
        the other routines of the HydPy-H-Land model, regarding its
        consideration of numerical accuracy.  To increase the accuracy of
        the numerical integration of the underlying ordinary differential
        equation, each simulation step can be divided into substeps, which
        are all solved with first order accuracy.  In the first example,
        this option is omitted through setting the |RecStep| parameter to
        one:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> recstep(2)
        >>> derived.dt = 1/recstep
        >>> percmax(2.0)
        >>> alpha(1.0)
        >>> k(2.0)
        >>> fluxes.contriarea = 1.0
        >>> fluxes.inuz = 0.0
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(1.0)
        >>> fluxes.q0
        q0(0.0)
        >>> states.uz
        uz(0.0)

        Due to the sequential calculation of the upper zone routine, the
        upper zone storage is drained completely through percolation and
        no water is left for fast discharge response.  By dividing the
        simulation step in 100 substeps, the results are quite different:

        >>> recstep(200)
        >>> derived.dt = 1.0/recstep
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.786934)
        >>> fluxes.q0
        q0(0.213066)
        >>> states.uz
        uz(0.0)

        Note that the assumed length of the simulation step is only a
        half day. Hence the effective values of the maximum percolation
        rate and the storage coefficient is not 2 but 1:

        >>> percmax
        percmax(2.0)
        >>> k
        k(2.0)
        >>> percmax.value
        1.0
        >>> k.value
        1.0

        By decreasing the contributing area one decreases percolation but
        increases fast discharge response:

        >>> fluxes.contriarea = 0.5
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.434108)
        >>> fluxes.q0
        q0(0.565892)
        >>> states.uz
        uz(0.0)

        Without any contributing area, the complete amount of water stored in
        the upper zone layer is released as direct discharge immediately:

        >>> fluxes.contriarea = 0.0
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.0)
        >>> fluxes.q0
        q0(1.0)
        >>> states.uz
        uz(0.0)

        Resetting |RecStep| leads to more transparent results.  Note that, due
        to the large value of the storage coefficient and the low accuracy
        of the numerical approximation, direct discharge drains the rest of
        the upper zone storage:

        >>> recstep(2)
        >>> fluxes.contriarea = 0.5
        >>> derived.dt = 1.0/recstep
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.5)
        >>> states.uz
        uz(0.0)

        Applying a more reasonable storage coefficient results in:

        >>> k(0.5)
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.25)
        >>> states.uz
        uz(0.25)

        Adding an input of 0.3 mm results the same percolation value (which,
        in the given example, is determined by the maximum percolation rate
        only), but in an increases value of the direct response (which
        always depends on the actual upper zone storage directly):

        >>> fluxes.inuz = 0.3
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.64)
        >>> states.uz
        uz(0.16)

        Due to the same reasons, another increase in numerical accuracy has
        no impact on percolation but decreases the direct response in the
        given example:

        >>> recstep(200)
        >>> derived.dt = 1.0/recstep
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.421708)
        >>> states.uz
        uz(0.378292)
    """

    CONTROLPARAMETERS = (
        hland_control.RecStep,
        hland_control.PercMax,
        hland_control.K,
        hland_control.Alpha,
    )
    DERIVEDPARAMETERS = (hland_derived.DT,)
    REQUIREDSEQUENCES = (
        hland_fluxes.ContriArea,
        hland_fluxes.InUZ,
    )
    UPDATEDSEQUENCES = (hland_states.UZ,)
    RESULTSEQUENCES = (
        hland_fluxes.Perc,
        hland_fluxes.Q0,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.perc = 0.0
        flu.q0 = 0.0
        for dummy in range(con.recstep):
            sta.uz += der.dt * flu.inuz
            d_perc = min(der.dt * con.percmax * flu.contriarea, sta.uz)
            sta.uz -= d_perc
            flu.perc += d_perc
            if sta.uz > 0.0:
                if flu.contriarea > 0.0:
                    d_q0 = (
                        der.dt * con.k * (sta.uz / flu.contriarea) ** (1.0 + con.alpha)
                    )
                    d_q0 = min(d_q0, sta.uz)
                else:
                    d_q0 = sta.uz
                sta.uz -= d_q0
                flu.q0 += d_q0


class Calc_LZ_V1(modeltools.Method):
    """Update the lower zone layer in accordance with percolation from
    upper groundwater to lower groundwater and/or in accordance with
    lake precipitation.

    Basic equation:
      :math:`\\frac{dLZ}{dt} = Perc + Pc`

    Examples:

        At first, a subbasin with two field zones is assumed (the zones
        could be of type forest or glacier as well).  In such zones,
        precipitation does not fall directly into the lower zone layer,
        hence the given precipitation of 2mm has no impact.  Only
        the actual percolation from the upper zone layer (underneath
        both field zones) is added to the lower zone storage:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(2)
        >>> zonetype(FIELD, FIELD)
        >>> derived.rellandarea = 1.0
        >>> derived.relzonearea = 2.0/3.0, 1.0/3.0
        >>> fluxes.perc = 2.0
        >>> fluxes.pc = 5.0
        >>> states.lz = 10.0
        >>> model.calc_lz_v1()
        >>> states.lz
        lz(12.0)

        If the second zone is an internal lake, its precipitation falls
        on the lower zone layer directly.  Note that only 5/3mm
        precipitation are added, due to the relative size of the
        internal lake within the subbasin. Percolation from the upper
        zone layer increases the lower zone storage only by two thirds
        of its original value, due to the larger spatial extend of
        the lower zone layer:

        >>> zonetype(FIELD, ILAKE)
        >>> derived.rellandarea = 2.0/3.0
        >>> derived.relzonearea = 2.0/3.0, 1.0/3.0
        >>> states.lz = 10.0
        >>> model.calc_lz_v1()
        >>> states.lz
        lz(13.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
    )
    DERIVEDPARAMETERS = (
        hland_derived.RelLandArea,
        hland_derived.RelZoneArea,
    )
    REQUIREDSEQUENCES = (
        hland_fluxes.Perc,
        hland_fluxes.PC,
    )
    UPDATEDSEQUENCES = (hland_states.LZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.lz += der.rellandarea * flu.perc
        for k in range(con.nmbzones):
            if con.zonetype[k] == ILAKE:
                sta.lz += der.relzonearea[k] * flu.pc[k]


class Calc_EL_LZ_V1(modeltools.Method):
    """Calculate lake evaporation.

    Basic equations:
        :math:`\\frac{dLZ}{dt} = -EL` \n
        :math:`EL = \\Bigl \\lbrace
        {
        {EPC \\ | \\ TC > TTIce}
        \\atop
        {0 \\ | \\ TC \\leq TTIce}
        }`

    Examples:

        Six zones of the same size are initialized.  The first three
        zones are no internal lakes, they can not exhibit any lake
        evaporation.  Of the last three zones, which are internal lakes,
        only the last one evaporates water.  For zones five and six,
        evaporation is suppressed due to an assumed ice layer, whenever
        the associated theshold temperature is not exceeded:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, ILAKE)
        >>> ttice(-1.0)
        >>> derived.relzonearea = 1.0/6.0
        >>> fluxes.epc = 0.6
        >>> fluxes.tc = 0.0, 0.0, 0.0, 0.0, -1.0, -2.0
        >>> states.lz = 10.0
        >>> model.calc_el_lz_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.6, 0.0, 0.0)
        >>> states.lz
        lz(9.9)

        Note that internal lakes always contain water.  Hence, the
        HydPy-H-Land model allows for negative values of the lower
        zone storage:

        >>> states.lz = 0.05
        >>> model.calc_el_lz_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.6, 0.0, 0.0)
        >>> states.lz
        lz(-0.05)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.TTIce,
    )
    DERIVEDPARAMETERS = (hland_derived.RelZoneArea,)
    REQUIREDSEQUENCES = (
        hland_fluxes.TC,
        hland_fluxes.EPC,
    )
    UPDATEDSEQUENCES = (hland_states.LZ,)
    RESULTSEQUENCES = (hland_fluxes.EL,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if (con.zonetype[k] == ILAKE) and (flu.tc[k] > con.ttice[k]):
                flu.el[k] = flu.epc[k]
                sta.lz -= der.relzonearea[k] * flu.el[k]
            else:
                flu.el[k] = 0.0


class Calc_Q1_LZ_V1(modeltools.Method):
    """Calculate the slow response of the lower zone layer.

    Basic equations:
        :math:`\\frac{dLZ}{dt} = -Q1` \n
        :math:`Q1 = \\Bigl \\lbrace
        {
        {K4 \\cdot LZ^{1+Gamma} \\ | \\ LZ > 0}
        \\atop
        {0 \\ | \\ LZ\\leq 0}
        }`

    Examples:

        As long as the lower zone storage is negative...

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> k4(0.2)
        >>> gamma(0.0)
        >>> states.lz = -2.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.0)
        >>> states.lz
        lz(-2.0)

        ...or zero, no slow discharge response occurs:

        >>> states.lz = 0.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.0)
        >>> states.lz
        lz(0.0)

        For storage values above zero the linear...

        >>> states.lz = 2.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.2)
        >>> states.lz
        lz(1.8)

        ...or nonlinear storage routing equation applies:

        >>> gamma(1.)
        >>> states.lz = 2.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.4)
        >>> states.lz
        lz(1.6)

        Note that the assumed length of the simulation step is only a
        half day. Hence the effective value of the storage coefficient
        is not 0.2 but 0.1:

        >>> k4
        k4(0.2)
        >>> k4.value
        0.1
    """

    CONTROLPARAMETERS = (
        hland_control.K4,
        hland_control.Gamma,
    )
    UPDATEDSEQUENCES = (hland_states.LZ,)
    RESULTSEQUENCES = (hland_fluxes.Q1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.lz > 0.0:
            flu.q1 = con.k4 * sta.lz ** (1.0 + con.gamma)
        else:
            flu.q1 = 0.0
        sta.lz -= flu.q1


class Calc_InUH_V1(modeltools.Method):
    """Calculate the unit hydrograph input.

    Basic equation:
        :math:`InUH = Q0 + Q1`

    Example:

        The unit hydrographs receives base flow from the whole subbasin
        and direct flow from zones of type field, forest and glacier only.
        In the following example, these occupy only one half of the
        subbasin, which is why the partial input of q0 is halved:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> derived.rellandarea = 0.5
        >>> fluxes.q0 = 4.0
        >>> fluxes.q1 = 1.0
        >>> model.calc_inuh_v1()
        >>> fluxes.inuh
        inuh(3.0)

    """

    DERIVEDPARAMETERS = (hland_derived.RelLandArea,)
    REQUIREDSEQUENCES = (
        hland_fluxes.Q0,
        hland_fluxes.Q1,
    )
    RESULTSEQUENCES = (hland_fluxes.InUH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inuh = der.rellandarea * flu.q0 + flu.q1


class Calc_OutUH_QUH_V1(modeltools.Method):
    """Calculate the unit hydrograph output (convolution).

    Examples:

        Prepare a unit hydrograph with only three ordinates ---
        representing a fast catchment response compared to the selected
        step size:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> derived.uh.shape = 3
        >>> derived.uh = 0.3, 0.5, 0.2
        >>> logs.quh.shape = 3
        >>> logs.quh = 1.0, 3.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.inuh = 0.0
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(1.0)
        >>> logs.quh
        quh(3.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.inuh = 4.0
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(4.2)
        >>> logs.quh
        quh(2.0, 0.8, 0.0)

        The next example demonstates the updating of non empty logging
        sequence:

        >>> fluxes.inuh = 4.0
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(3.2)
        >>> logs.quh
        quh(2.8, 0.8, 0.0)

        A unit hydrograph with only one ordinate results in the direct
        routing of the input:

        >>> derived.uh.shape = 1
        >>> derived.uh = 1.0
        >>> fluxes.inuh = 0.0
        >>> logs.quh.shape = 1
        >>> logs.quh = 0.0
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(0.0)
        >>> logs.quh
        quh(0.0)
        >>> fluxes.inuh = 4.0
        >>> model.calc_outuh_quh()
        >>> fluxes.outuh
        outuh(4.0)
        >>> logs.quh
        quh(0.0)
    """

    DERIVEDPARAMETERS = (hland_derived.UH,)
    REQUIREDSEQUENCES = (hland_fluxes.InUH,)
    UPDATEDSEQUENCES = (hland_logs.QUH,)
    RESULTSEQUENCES = (hland_fluxes.OutUH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.outuh = der.uh[0] * flu.inuh + log.quh[0]
        for jdx in range(1, len(der.uh)):
            log.quh[jdx - 1] = der.uh[jdx] * flu.inuh + log.quh[jdx]


class Calc_QT_V1(modeltools.Method):
    """Calculate the total discharge after possible abstractions.

    Basic equation:
        :math:`QT = max(QFactor \\cdot OutUH - Abstr, 0)`

    Examples:

        Trying to abstract less then available, as much as available and
        less then available results in:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> abstr(1.0)
        >>> derived.qfactor(0.5)
        >>> fluxes.outuh = 4.0
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(1.0)
        >>> fluxes.outuh = 2.0
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(0.0)
        >>> fluxes.outuh = 1.0
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(0.0)

        Note that "negative abstractions" are allowed:

        >>> abstr(-1.0)
        >>> fluxes.outuh = 2.0
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(2.0)
    """

    CONTROLPARAMETERS = (hland_control.Abstr,)
    DERIVEDPARAMETERS = (hland_derived.QFactor,)
    REQUIREDSEQUENCES = (hland_fluxes.OutUH,)
    RESULTSEQUENCES = (hland_fluxes.QT,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qt = max(der.qfactor * flu.outuh - con.abstr, 0.0)


class Pass_Q_v1(modeltools.Method):
    """Update the outlet link sequence."""

    REQUIREDSEQUENCES = (hland_fluxes.QT,)
    RESULTSEQUENCES = (hland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.qt


class Model(modeltools.AdHocModel):
    """The HydPy-H-Land base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_TC_V1,
        Calc_TMean_V1,
        Calc_FracRain_V1,
        Calc_RFC_SFC_V1,
        Calc_PC_V1,
        Calc_EP_V1,
        Calc_EPC_V1,
        Calc_TF_Ic_V1,
        Calc_EI_Ic_V1,
        Calc_SP_WC_V1,
        Calc_Melt_SP_WC_V1,
        Calc_Refr_SP_WC_V1,
        Calc_In_WC_V1,
        Calc_GlMelt_In_V1,
        Calc_R_SM_V1,
        Calc_CF_SM_V1,
        Calc_EA_SM_V1,
        Calc_InUZ_V1,
        Calc_ContriArea_V1,
        Calc_Q0_Perc_UZ_V1,
        Calc_LZ_V1,
        Calc_EL_LZ_V1,
        Calc_Q1_LZ_V1,
        Calc_InUH_V1,
        Calc_OutUH_QUH_V1,
        Calc_QT_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Q_v1,)
    SENDER_METHODS = ()
    SUBMODELS = ()
