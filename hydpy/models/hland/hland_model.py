"""
.. _`issue 68`: https://github.com/hydpy-dev/hydpy/issues/68
"""

# imports...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy import config
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.core.typingtools import *
from hydpy.interfaces import aetinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import rconcinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces

# ...from hland
from hydpy.models.hland import hland_constants
from hydpy.models.hland.hland_constants import FIELD, FOREST, GLACIER, ILAKE, SEALED
from hydpy.models.hland import hland_control
from hydpy.models.hland import hland_derived
from hydpy.models.hland import hland_fixed
from hydpy.models.hland import hland_inputs
from hydpy.models.hland import hland_factors
from hydpy.models.hland import hland_fluxes
from hydpy.models.hland import hland_states
from hydpy.models.hland import hland_aides
from hydpy.models.hland import hland_outlets


class Calc_TC_V1(modeltools.Method):
    r"""Adjust the measured air temperature to the altitude of the individual zones.

    Basic equation:
      :math:`TC = T + TCorr - TCAlt \cdot (ZoneZ - Z)`

    Examples:

        Prepare two zones, the first lying at the reference height and the second 200
        meters above:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(2)
        >>> zonez(2.0, 4.0)
        >>> derived.z(2.0)

        Applying the usual temperature lapse rate of 0.6°C/100m does not affect the
        first zone but reduces the temperature of the second zone by 1.2°C:

        >>> tcorr(1.0)
        >>> tcalt(0.6)
        >>> inputs.t = 5.0
        >>> model.calc_tc_v1()
        >>> factors.tc
        tc(6.0, 4.8)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.TCorr,
        hland_control.TCAlt,
        hland_control.ZoneZ,
    )
    DERIVEDPARAMETERS = (hland_derived.Z,)
    REQUIREDSEQUENCES = (hland_inputs.T,)
    RESULTSEQUENCES = (hland_factors.TC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbzones):
            fac.tc[k] = inp.t + con.tcorr[k] - con.tcalt[k] * (con.zonez[k] - der.z)


class Calc_FracRain_V1(modeltools.Method):
    r"""Determine the temperature-dependent fraction of (liquid) rainfall
    and (total) precipitation.

    Basic equation:
      :math:`FracRain = \frac{TC-(TT-\frac{TTInt}{2})}{TTInt}`

    Restriction:
      :math:`0 \leq FracRain \leq 1`

    Examples:

        The threshold temperature of seven zones is 0°C, and the corresponding
        temperature interval of mixed precipitation 2°C:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> tt(0.0)
        >>> ttint(2.0)

        The fraction of rainfall is zero below -1°C, is one above 1°C, and increases
        linearly in between:

        >>> factors.tc = -10.0, -1.0, -0.5, 0.0, 0.5, 1.0, 10.0
        >>> model.calc_fracrain_v1()
        >>> factors.fracrain
        fracrain(0.0, 0.0, 0.25, 0.5, 0.75, 1.0, 1.0)

        Note the particular case of a zero temperature interval.  With an actual
        temperature being equal to the threshold temperature, the rainfall fraction
        is one:

        >>> ttint(0.0)
        >>> model.calc_fracrain_v1()
        >>> factors.fracrain
        fracrain(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.TT, hland_control.TTInt)
    REQUIREDSEQUENCES = (hland_factors.TC,)
    RESULTSEQUENCES = (hland_factors.FracRain,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbzones):
            d_dt = con.ttint[k] / 2.0
            if fac.tc[k] >= (con.tt[k] + d_dt):
                fac.fracrain[k] = 1.0
            elif fac.tc[k] <= (con.tt[k] - d_dt):
                fac.fracrain[k] = 0.0
            else:
                fac.fracrain[k] = (fac.tc[k] - (con.tt[k] - d_dt)) / con.ttint[k]


class Calc_RFC_SFC_V1(modeltools.Method):
    r"""Calculate the corrected fractions of rainfall/snowfall and total precipitation.

    Basic equations:
      :math:`RfC = RfCF \cdot FracRain`

      :math:`SfC = SfCF \cdot (1 - FracRain)`

    Examples:

        Assume five zones with different temperatures and hence different fractions of
        rainfall and total precipitation:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> factors.fracrain = 0.0, 0.25, 0.5, 0.75, 1.0

        With no rainfall and no snowfall correction (due to the respective factors
        being one), the corrected fraction related to rain is identical to the original
        fraction, while the corrected fraction related to snow behaves the opposite:

        >>> rfcf(1.0)
        >>> sfcf(1.0)
        >>> model.calc_rfc_sfc_v1()
        >>> factors.rfc
        rfc(0.0, 0.25, 0.5, 0.75, 1.0)
        >>> factors.sfc
        sfc(1.0, 0.75, 0.5, 0.25, 0.0)

        With a rainfall reduction of 20% and a snowfall increase of 20 %, the corrected
        fractions are as follows:

        >>> rfcf(0.8)
        >>> sfcf(1.2)
        >>> model.calc_rfc_sfc_v1()
        >>> factors.rfc
        rfc(0.0, 0.2, 0.4, 0.6, 0.8)
        >>> factors.sfc
        sfc(1.2, 0.9, 0.6, 0.3, 0.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.RfCF, hland_control.SfCF)
    REQUIREDSEQUENCES = (hland_factors.FracRain,)
    RESULTSEQUENCES = (hland_factors.RfC, hland_factors.SfC)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbzones):
            fac.rfc[k] = fac.fracrain[k] * con.rfcf[k]
            fac.sfc[k] = (1.0 - fac.fracrain[k]) * con.sfcf[k]


class Calc_PC_V1(modeltools.Method):
    r"""Apply the precipitation correction factors and adjust precipitation to the
    altitude of the individual zones.

    Basic equation:
      :math:`PC = P \cdot PCorr \cdot (1 + PCAlt \cdot (ZoneZ - Z)) \cdot (RfC + SfC)`

    Examples:

        Five zones are at an elevation of 200 m.  A precipitation value of 5 mm has
        been measured at a gauge at an elevation of 300 m:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonez(3.0)
        >>> inputs.p = 5.0
        >>> derived.z(2.0)

        The first four zones illustrate the individual precipitation corrections due to
        the general (|PCorr|, first zone), the altitude (|PCAlt|, second zone), the
        rainfall (|RfC|, third zone), and the snowfall adjustment (|SfC|, fourth zone).
        The fifth zone illustrates the interaction between all corrections:

        >>> pcorr(1.3, 1.0, 1.0, 1.0, 1.3)
        >>> pcalt(0.0, 0.1, 0.0, 0.0, 0.1)
        >>> factors.rfc = 0.5, 0.5, 0.4, 0.5, 0.4
        >>> factors.sfc = 0.5, 0.5, 0.5, 0.7, 0.7
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(6.5, 5.5, 4.5, 6.0, 7.865)

        Usually, one would set zero or positive values for parameter |PCAlt|.  But it
        is also allowed to assign negative values to reflect possible negative
        relationships between precipitation and altitude.  Method |Calc_PC_V1| performs
        the required truncations to prevent negative precipitation values:


        >>> pcalt(-1.0)
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.PCAlt,
        hland_control.ZoneZ,
        hland_control.PCorr,
    )
    DERIVEDPARAMETERS = (hland_derived.Z,)
    REQUIREDSEQUENCES = (hland_inputs.P, hland_factors.RfC, hland_factors.SfC)
    RESULTSEQUENCES = (hland_fluxes.PC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.pc[k] = inp.p * (1.0 + con.pcalt[k] * (con.zonez[k] - der.z))
            if flu.pc[k] <= 0.0:
                flu.pc[k] = 0.0
            else:
                flu.pc[k] *= con.pcorr[k] * (fac.rfc[k] + fac.sfc[k])


class Calc_TF_Ic_V1(modeltools.Method):
    r"""Calculate throughfall and update the interception storage accordingly.

    Basic equation:
      .. math::
        TF =
        \begin{cases}
        PC &|\ Ic = IcMax
        \\
        0 &|\ Ic < IcMax
        \end{cases}

    Examples:

        Initialise seven zones of different types.  Assume a general interception
        capacity of 2 mm. All zones receive a precipitation input of 0.5 mm:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> zonetype(GLACIER, ILAKE, FIELD, FOREST, SEALED, SEALED, SEALED)
        >>> icmax(2.0)
        >>> fluxes.pc = 0.5
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_tf_ic_v1()

        The interception routine does not apply to glaciers (first zone) and internal
        lakes (second zone).  Hence, all precipitation becomes throughfall. For fields,
        forests, and sealed areas, the interception routine works identical, so the
        results of zone three to five are equal.  The last three zones demonstrate that
        all precipitation is stored until the intercepted water reaches the available
        capacity; afterwards, all precipitation becomes throughfall.  Initial storage
        reduces the effective capacity of the respective simulation step:

        >>> states.ic
        ic(0.0, 0.0, 0.5, 0.5, 0.5, 1.5, 2.0)
        >>> fluxes.tf
        tf(0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5)

        A zero precipitation example:

        >>> fluxes.pc = 0.0
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_tf_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
        >>> fluxes.tf
        tf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        A high precipitation example:

        >>> fluxes.pc = 5.0
        >>> states.ic = 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0
        >>> model.calc_tf_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> fluxes.tf
        tf(5.0, 5.0, 3.0, 3.0, 3.0, 4.0, 5.0)
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
            if con.zonetype[k] in (FIELD, FOREST, SEALED):
                flu.tf[k] = max(flu.pc[k] - (con.icmax[k] - sta.ic[k]), 0.0)
                sta.ic[k] += flu.pc[k] - flu.tf[k]
            else:
                flu.tf[k] = flu.pc[k]
                sta.ic[k] = 0.0


class Calc_EI_Ic_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water.

    Basic equation:
      :math:`\frac{dIc_i}{dt} = -EI_i`

    Examples:

        We build an example based on |evap_aet_hbv96| for calculating interception
        evaporation, which uses |evap_ret_io| for querying potential
        evapotranspiration:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep("1h")
        >>> nmbzones(5)
        >>> zonetype(GLACIER, SEALED, FIELD, FOREST, ILAKE)
        >>> area(1.0)
        >>> zonearea(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> zonez(5.0)
        >>> icmax(3.0)
        >>> fc(50.0)
        >>> fluxes.tf = 0.5
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     with model.add_petmodel_v1("evap_ret_io"):
        ...         evapotranspirationfactor(0.6, 0.8, 1.0, 1.2, 1.4)
        ...         inputs.referenceevapotranspiration = 1.0

        |Calc_EI_Ic_AETModel_V1| uses the flux returned by the submodel to adjust |Ic|:

        >>> states.ic = 2.0
        >>> model.calc_ei_ic_v1()
        >>> fluxes.ei
        ei(0.0, 0.8, 1.0, 1.2, 0.0)
        >>> states.ic
        ic(0.0, 1.2, 1.0, 0.8, 0.0)
        >>> fluxes.tf
        tf(0.5, 0.5, 0.5, 0.5, 0.5)

        |Calc_EI_Ic_AETModel_V1| eventually reduces |EI| so that |Ic| does not become
        negative:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = 5.0
        >>> states.ic = 2.0
        >>> model.calc_ei_ic_v1()
        >>> fluxes.ei
        ei(0.0, 2.0, 2.0, 2.0, 0.0)
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.tf
        tf(0.5, 0.5, 0.5, 0.5, 0.5)

        In contrast, |Calc_EI_Ic_AETModel_V1| does not reduce negative |EI| values
        (condensation) that cause an overshoot of the interception storage capacity:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = -3.0
        >>> states.ic = 2.0
        >>> model.calc_ei_ic_v1()
        >>> fluxes.ei
        ei(0.0, -2.4, -3.0, -3.6, 0.0)
        >>> states.ic
        ic(0.0, 4.4, 5.0, 5.6, 0.0)
        >>> fluxes.tf
        tf(0.5, 0.5, 0.5, 0.5, 0.5)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    UPDATEDSEQUENCES = (hland_states.Ic,)
    RESULTSEQUENCES = (hland_fluxes.EI,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_interceptionevaporation()
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, SEALED):
                flu.ei[k] = min(submodel.get_interceptionevaporation(k), sta.ic[k])
                sta.ic[k] -= flu.ei[k]
            else:
                flu.ei[k] = 0.0
                sta.ic[k] = 0.0


class Calc_EI_Ic_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_EI_Ic_AETModel_V1,)
    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    UPDATEDSEQUENCES = (hland_states.Ic,)
    RESULTSEQUENCES = (hland_fluxes.EI,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_ei_ic_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_SP_WC_V1(modeltools.Method):
    r"""Add throughfall to the snow layer.

    Basic equations:
      :math:`\frac{dSP}{dt} = SFDist \cdot TF \cdot \frac{SfC}{SfC + RfC}`

      :math:`\frac{dWC}{dt} = SFDist \cdot TF \cdot \frac{RfC}{SfC + RfC}`

    Examples:

        Consider the following setting, in which nine zones of different types receive
        a throughfall of 10 mm:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(9)
        >>> sclass(1)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED, FIELD, FIELD, FIELD, FIELD)
        >>> sfdist(0.2)
        >>> fluxes.tf = 10.0
        >>> factors.sfc = 0.5, 0.5, 0.5, 0.5, 0.5, 0.2, 0.8, 1.0, 4.0
        >>> factors.rfc = 0.5, 0.5, 0.5, 0.5, 0.5, 0.8, 0.2, 4.0, 1.0
        >>> states.sp = 2.0
        >>> states.wc = 1.0
        >>> model.calc_sp_wc_v1()
        >>> states.sp
        sp(0.0, 7.0, 7.0, 7.0, 7.0, 4.0, 10.0, 4.0, 10.0)
        >>> states.wc
        wc(0.0, 6.0, 6.0, 6.0, 6.0, 9.0, 3.0, 9.0, 3.0)

        The snow routine does not apply to internal lakes, which is why both the ice
        storage and the water storage of the first zone remain unchanged.  The snow
        routine is identical for fields, forests, sealed areas, and glaciers (besides
        the additional glacier melt), which is why the results zone three to five are
        equal.  The last four zones illustrate that method |Calc_SP_WC_V1| applies the
        corrected snowfall and rainfall fractions "relatively", considering that the
        throughfall is already corrected.

        When both factors are zero, neither the water nor the ice content of the snow
        layer changes:

        >>> factors.sfc = 0.0
        >>> factors.rfc = 0.0
        >>> states.sp = 2.0
        >>> states.wc = 1.0
        >>> model.calc_sp_wc_v1()
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)

        In the above examples, we did not divide the zones into snow classes. If we do
        so, method |Calc_SP_WC_V1| adds different amounts of snow and rainfall to the
        individual snow classes based on the current values of parameter |SFDist|:

        >>> sclass(2)
        >>> sfdist(0.0, 2.0)
        >>> factors.sfc = 0.5, 0.5, 0.5, 0.5, 0.5, 0.2, 0.8, 1.0, 4.0
        >>> factors.rfc = 0.5, 0.5, 0.5, 0.5, 0.5, 0.8, 0.2, 4.0, 1.0
        >>> states.sp = 2.0
        >>> states.wc = 1.0
        >>> model.calc_sp_wc_v1()
        >>> states.sp
        sp([[0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            [0.0, 12.0, 12.0, 12.0, 12.0, 6.0, 18.0, 6.0, 18.0]])
        >>> states.wc
        wc([[0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [0.0, 11.0, 11.0, 11.0, 11.0, 17.0, 5.0, 17.0, 5.0]])
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
        hland_control.SFDist,
    )
    REQUIREDSEQUENCES = (hland_fluxes.TF, hland_factors.RfC, hland_factors.SfC)
    UPDATEDSEQUENCES = (hland_states.WC, hland_states.SP)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                d_denom = fac.rfc[k] + fac.sfc[k]
                if d_denom > 0.0:
                    d_rain = flu.tf[k] * fac.rfc[k] / d_denom
                    d_snow = flu.tf[k] * fac.sfc[k] / d_denom
                    for c in range(con.sclass):
                        sta.wc[c, k] += con.sfdist[c] * d_rain
                        sta.sp[c, k] += con.sfdist[c] * d_snow
            else:
                for c in range(con.sclass):
                    sta.wc[c, k] = 0.0
                    sta.sp[c, k] = 0.0


class Calc_SPL_WCL_SP_WC_V1(modeltools.Method):
    r"""Calculate the subbasin-internal redistribution losses of the snow layer.

    Basic equations:
      :math:`\frac{dSP}{dt} = -SPL`

      :math:`\frac{dWC}{dt} = -WCL`

      :math:`SPL = SP \cdot RelExcess`

      :math:`WCL = WC \cdot RelExcess`

      :math:`RelExcess = \frac{max(SP + WC - SMax, 0)}{SP + WC}`

    Examples:

        We prepare eight zones.  We use the first five to show the identical behaviour
        of the land-use types |GLACIER|, |FIELD|, |FOREST|, and |SEALED| and the unique
        behaviour of type |ILAKE|.  Zones six to eight serve to demonstrate the effects
        of different initial states:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(8)
        >>> sclass(1)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED, FIELD, FIELD, FIELD)
        >>> smax(500.0)

        Internal lakes do not possess a snow module and cannot redistribute any snow.
        Hence, |Calc_SPL_WCL_SP_WC_V1| sets the loss (|SPL| and |WCL|) and state (|SP|
        and |WC|) sequences to zero.  For all other zones, the total amount of snow
        redistribution depends on how much the total water equivalent exceeds the
        threshold parameter |SMax| (consistently set to 500 m).  The fraction between
        the liquid (|WCL|) and frozen (|SPL|) loss depends on the fraction between
        the actual storage of liquid (|WC|) and frozen (|SP|) water in the snow layer:

        >>> states.sp = 600.0, 600.0, 600.0, 600.0, 600.0, 60.0, 800.0, 0.0
        >>> states.wc = 200.0, 200.0, 200.0, 200.0, 200.0, 20.0, 0.0, 800.0
        >>> model.calc_spl_wcl_sp_wc_v1()
        >>> fluxes.spl
        spl(0.0, 225.0, 225.0, 225.0, 225.0, 0.0, 300.0, 0.0)
        >>> fluxes.wcl
        wcl(0.0, 75.0, 75.0, 75.0, 75.0, 0.0, 0.0, 300.0)
        >>> states.sp
        sp(0.0, 375.0, 375.0, 375.0, 375.0, 60.0, 500.0, 0.0)
        >>> states.wc
        wc(0.0, 125.0, 125.0, 125.0, 125.0, 20.0, 0.0, 500.0)

        The above example deals with a single snow class.  Here, we add a second snow
        class to illustrate that the total snow loss of each zone does not depend on
        its average snow storage but the degree of exceedance of |SMax| within its
        individual snow classes:

        >>> sclass(2)
        >>> states.sp = [[600.0, 600.0, 600.0, 600.0, 600.0, 60.0, 800.0, 0.0],
        ...              [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
        >>> states.wc = [[200.0, 200.0, 200.0, 200.0, 200.0, 20.0, 0.0, 800.0],
        ...              [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
        >>> model.calc_spl_wcl_sp_wc_v1()
        >>> fluxes.spl
        spl(0.0, 112.5, 112.5, 112.5, 112.5, 0.0, 150.0, 0.0)
        >>> fluxes.wcl
        wcl(0.0, 37.5, 37.5, 37.5, 37.5, 0.0, 0.0, 150.0)
        >>> states.sp
        sp([[0.0, 375.0, 375.0, 375.0, 375.0, 60.0, 500.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        >>> states.wc
        wc([[0.0, 125.0, 125.0, 125.0, 125.0, 20.0, 0.0, 500.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
        hland_control.SMax,
    )
    UPDATEDSEQUENCES = (hland_states.WC, hland_states.SP)
    RESULTSEQUENCES = (hland_fluxes.SPL, hland_fluxes.WCL)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            flu.spl[k] = 0.0
            flu.wcl[k] = 0.0
            if con.zonetype[k] == ILAKE:
                for c in range(con.sclass):
                    sta.sp[c, k] = 0.0
                    sta.wc[c, k] = 0.0
            elif not modelutils.isinf(con.smax[k]):
                for c in range(con.sclass):
                    d_snow = sta.sp[c, k] + sta.wc[c, k]
                    d_excess = d_snow - con.smax[k]
                    if d_excess > 0.0:
                        d_excess_sp = d_excess * sta.sp[c, k] / d_snow
                        d_excess_wc = d_excess * sta.wc[c, k] / d_snow
                        flu.spl[k] += d_excess_sp / con.sclass
                        flu.wcl[k] += d_excess_wc / con.sclass
                        sta.sp[c, k] -= d_excess_sp
                        sta.wc[c, k] -= d_excess_wc


class Calc_SPG_WCG_SP_WC_V1(modeltools.Method):
    r"""Calculate the subbasin-internal redistribution gains of the snow layer.

    Basic equations:
      :math:`\frac{dSP}{dt} = -SPG`

      :math:`\frac{dWC}{dt} = -WCG`

    Examples:

        We prepare an example consisting of seven zones, sorted by (non-strictly)
        descending elevation.  For now, there is a single snow class per zone, and the
        zones' areas are identical (1.0 km²).  The last zone is of type |ILAKE| and
        does not participate in snow redistribution. We use the same configuration for
        |SMax| (the maximum snow storage) and |SRed| (defining the redistribution
        paths) throughout all examples:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> area(7.0)
        >>> nmbzones(7)
        >>> sclass(1)
        >>> zonetype(GLACIER, FIELD, FOREST, SEALED, FOREST, FIELD, ILAKE)
        >>> zonez(30.0, 25.0, 20.0, 15.0, 10.0, 10.0, 5.0)
        >>> zonearea(1.0)
        >>> psi(1.0)
        >>> sfdist(1.0)
        >>> smax(500.0)
        >>> sred([[0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
        ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

        For convenience, we prepare a function that updates all relevant derived
        parameters:

        >>> def update():
        ...     derived.rellandarea.update()
        ...     derived.relzoneareas.update()
        ...     derived.rellowerzonearea.update()
        ...     derived.zonearearatios.update()
        ...     derived.indiceszonez.update()
        ...     derived.sredorder.update()
        ...     derived.srednumber.update()
        ...     derived.sredend.update()
        >>> update()

        In the first example, the total snow water equivalent (300 mm) is way below
        |SRed| (500 mm).  Hence, all frozen (|SPL|) and liquid (|WCL|) water released
        deposits completely in the target zones:

        >>> states.sp = 200.0
        >>> states.wc = 100.0
        >>> fluxes.spl = 20.0, 20.0, 20.0, 20.0, 0.0, 0.0, 0.0
        >>> fluxes.wcl = 10.0, 10.0, 10.0, 10.0, 0.0, 0.0, 0.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(0.0, 4.0, 24.0, 24.0, 14.0, 14.0, 0.0)
        >>> fluxes.wcg
        wcg(0.0, 2.0, 12.0, 12.0, 7.0, 7.0, 0.0)
        >>> states.sp
        sp(200.0, 204.0, 224.0, 224.0, 214.0, 214.0, 0.0)
        >>> states.wc
        wc(100.0, 102.0, 112.0, 112.0, 107.0, 107.0, 0.0)

        The following test function checks that method |Calc_SPG_WCG_SP_WC_V1| does not
        introduce any water balance errors:

        >>> from hydpy import repr_
        >>> def check(sp_old, wc_old):
        ...     def check_vector(deltas):
        ...         return numpy.max(numpy.abs(numpy.sum(deltas, axis=0)))
        ...     sp_new = states.sp.average_values()
        ...     sp_delta_l = fluxes.spl.average_values()
        ...     sp_delta_g = fluxes.spg.average_values()
        ...     sp_old_array = numpy.array(6 * [sp_old] + [0.0])
        ...     wc_new = states.wc.average_values()
        ...     wc_delta_l = fluxes.wcl.average_values()
        ...     wc_delta_g = fluxes.wcg.average_values()
        ...     wc_old_array = numpy.array(6 * [wc_old] + [0.0])
        ...     errors = [sp_old + sp_delta_l - sp_new,
        ...               sp_delta_l - sp_delta_g,
        ...               check_vector(sp_old_array + fluxes.spg - states.sp),
        ...               wc_old + wc_delta_l - wc_new,
        ...               wc_delta_l - wc_delta_g,
        ...               check_vector(wc_old_array + fluxes.wcg - states.wc)]
        ...     print(*(repr_(error) for error in errors), sep=", ")

        The possible errors related to different aspects of the frozen and the liquid
        water content of the snow layer are all within the range of the given numerical
        precision:

        >>> check(sp_old=200.0, wc_old=100.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        Next, we increase the size of the first area and decrease the size of the
        second area by the same amount.  The different results for |SPG| and |WCG|
        reflect that the loss terms (|SPL| and |WCL|) relate to the sizes of the
        supplying zones while the gain terms (|SPG| and |WCG|) relate to the sizes of
        the receiving zones:

        >>> zonearea(1.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> update()
        >>> states.sp = 200.0
        >>> states.wc = 100.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(0.0, 12.0, 16.0, 26.0, 16.0, 16.0, 0.0)
        >>> fluxes.wcg
        wcg(0.0, 6.0, 8.0, 13.0, 8.0, 8.0, 0.0)
        >>> states.sp
        sp(200.0, 212.0, 216.0, 226.0, 216.0, 216.0, 0.0)
        >>> states.wc
        wc(100.0, 106.0, 108.0, 113.0, 108.0, 108.0, 0.0)
        >>> check(sp_old=200.0, wc_old=100.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        When modelling high mountain areas, even the lowest zones (the so-called
        "dead-ends") can receive substantial amounts of redistributed snow.  Therefore,
        the simple "from top to bottom" approach described so far can result in
        unrealistic snow towers for these dead-ends, especially if their size is small
        compared to the size of the snow-delivering area.  To prevent such artefacts,
        method |Calc_SPG_WCG_SP_WC_V1| takes the total snow amount of all dead-ends
        exceeding the |Smax| threshold and distributes it gradually to the other zones,
        starting from the lowest in the order defined by parameter |IndicesZoneZ|:

        >>> zonearea(1.0)
        >>> update()
        >>> states.sp = 400.0
        >>> states.wc = 75.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(0.0, 13.333333, 16.666667, 16.666667, 16.666667, 16.666667, 0.0)
        >>> fluxes.wcg
        wcg(0.0, 6.666667, 8.333333, 8.333333, 8.333333, 8.333333, 0.0)
        >>> states.sp
        sp(400.0, 413.333333, 416.666667, 416.666667, 416.666667, 416.666667,
           0.0)
        >>> states.wc
        wc(75.0, 81.666667, 83.333333, 83.333333, 83.333333, 83.333333, 0.0)
        >>> check(sp_old=400.0, wc_old=75.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        If the total snow amount of all zone reaches |SMax|, |Calc_SPG_WCG_SP_WC_V1|
        distributes all remaining excess evenly to all non-lake zones:

        >>> states.sp = 400.0
        >>> states.wc = 90.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(13.333333, 13.333333, 13.333333, 13.333333, 13.333333, 13.333333,
            0.0)
        >>> fluxes.wcg
        wcg(6.666667, 6.666667, 6.666667, 6.666667, 6.666667, 6.666667, 0.0)
        >>> states.sp
        sp(413.333333, 413.333333, 413.333333, 413.333333, 413.333333,
           413.333333, 0.0)
        >>> states.wc
        wc(96.666667, 96.666667, 96.666667, 96.666667, 96.666667, 96.666667, 0.0)
        >>> check(sp_old=400.0, wc_old=90.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        Introducing multiple snow classes within each zone complicates things.  We
        repeat some of the above examples with an increased number of snow classes:

        >>> sclass(2)
        >>> update()

        The "normal" snow redistribution relies similarly on parameter |SFDist| as the
        snowfall accumulation does.  We show this by repeating the first example with
        the most extreme configuration of |SFDist|, where the second snow class
        receives the entire amount of incoming snow:

        >>> sfdist(0.0, 2.0)
        >>> states.sp = 200.0
        >>> states.wc = 100.0
        >>> fluxes.spl = 20.0, 20.0, 20.0, 20.0, 0.0, 0.0, 0.0
        >>> fluxes.wcl = 10.0, 10.0, 10.0, 10.0, 0.0, 0.0, 0.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(0.0, 4.0, 24.0, 24.0, 14.0, 14.0, 0.0)
        >>> fluxes.wcg
        wcg(0.0, 2.0, 12.0, 12.0, 7.0, 7.0, 0.0)
        >>> states.sp
        sp([[200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 0.0],
            [200.0, 208.0, 248.0, 248.0, 228.0, 228.0, 0.0]])
        >>> states.wc
        wc([[100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 0.0],
            [100.0, 104.0, 124.0, 124.0, 114.0, 114.0, 0.0]])

        During the eventual "bottom to top" re-redistribution, on the other hand,
        the fractions between the gains of individual snow classes do not depend on
        |SFDist| but their remaining capacities:

        >>> states.sp = 400.0
        >>> states.wc = 75.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(0.0, 13.333333, 16.666667, 16.666667, 16.666667, 16.666667, 0.0)
        >>> fluxes.wcg
        wcg(0.0, 6.666667, 8.333333, 8.333333, 8.333333, 8.333333, 0.0)
        >>> states.sp
        sp([[400.0, 412.280702, 416.666667, 416.666667, 416.666667, 416.666667,
             0.0],
            [400.0, 414.385965, 416.666667, 416.666667, 416.666667, 416.666667,
             0.0]])
        >>> states.wc
        wc([[75.0, 81.140351, 83.333333, 83.333333, 83.333333, 83.333333, 0.0],
            [75.0, 82.192982, 83.333333, 83.333333, 83.333333, 83.333333, 0.0]])
        >>> check(sp_old=400.0, wc_old=75.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        During a subbasin-wide excess of |SMax|, all snow classes of a specific zone
        handle the same total snow water equivalent:

        >>> states.sp = 400.0
        >>> states.wc = 90.0
        >>> model.calc_spg_wcg_sp_wc_v1()
        >>> fluxes.spg
        spg(13.333333, 13.333333, 13.333333, 13.333333, 13.333333, 13.333333,
            0.0)
        >>> fluxes.wcg
        wcg(6.666667, 6.666667, 6.666667, 6.666667, 6.666667, 6.666667, 0.0)
        >>> states.sp
        sp([[413.333333, 413.333333, 413.333333, 413.333333, 413.333333,
             413.333333, 0.0],
            [413.333333, 413.333333, 413.333333, 413.333333, 413.333333,
             413.333333, 0.0]])
        >>> states.wc
        wc([[96.666667, 96.666667, 96.666667, 96.666667, 96.666667, 96.666667,
             0.0],
            [96.666667, 96.666667, 96.666667, 96.666667, 96.666667, 96.666667,
             0.0]])
        >>> check(sp_old=400.0, wc_old=90.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
        hland_control.SFDist,
        hland_control.SMax,
        hland_control.SRed,
    )
    DERIVEDPARAMETERS = (
        hland_derived.RelLandArea,
        hland_derived.RelZoneAreas,
        hland_derived.ZoneAreaRatios,
        hland_derived.IndicesZoneZ,
        hland_derived.SRedNumber,
        hland_derived.SRedOrder,
        hland_derived.SRedEnd,
    )
    REQUIREDSEQUENCES = (hland_fluxes.SPL, hland_fluxes.WCL)
    UPDATEDSEQUENCES = (hland_states.WC, hland_states.SP)
    RESULTSEQUENCES = (
        hland_aides.SPE,
        hland_aides.WCE,
        hland_fluxes.SPG,
        hland_fluxes.WCG,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess

        # initialise gain and excess:
        for i in range(con.nmbzones):
            flu.spg[i] = 0.0
            flu.wcg[i] = 0.0
            aid.spe[i] = 0.0
            aid.wce[i] = 0.0
            if con.zonetype[i] == ILAKE:
                for c in range(con.sclass):
                    sta.sp[c, i] = 0.0
                    sta.wc[c, i] = 0.0

        # redistribute losses from top to bottom:
        for i in range(der.srednumber):
            # f: from, t: to
            f, t = der.sredorder[i, 0], der.sredorder[i, 1]
            d_f = der.zonearearatios[f, t] * con.sred[f, t]
            d_gain_frozen = d_f * (flu.spl[f] + aid.spe[f])
            d_gain_liquid = d_f * (flu.wcl[f] + aid.wce[f])
            d_gain_total = d_gain_frozen + d_gain_liquid
            for c in range(con.sclass):
                d_gain_pot = con.sfdist[c] * d_gain_total
                if d_gain_pot > 0.0:
                    d_gain_max = con.smax[t] - sta.sp[c, t] - sta.wc[c, t]
                    d_fraction_gain = min(d_gain_max / d_gain_pot, 1.0)
                    d_factor_gain = d_fraction_gain * con.sfdist[c]
                    flu.spg[t] += d_factor_gain * d_gain_frozen / con.sclass
                    flu.wcg[t] += d_factor_gain * d_gain_liquid / con.sclass
                    sta.sp[c, t] += d_factor_gain * d_gain_frozen
                    sta.wc[c, t] += d_factor_gain * d_gain_liquid
                    d_factor_excess = (1.0 - d_fraction_gain) * con.sfdist[c]
                    aid.spe[t] += d_factor_excess * d_gain_frozen / con.sclass
                    aid.wce[t] += d_factor_excess * d_gain_liquid / con.sclass

        # check for remaining excess at the dead ends:
        d_excess_frozen_basin, d_excess_liquid_basin = 0.0, 0.0
        for i in range(con.nmbzones):
            if der.sredend[i]:
                d_excess_frozen_basin += der.relzoneareas[i] * (aid.spe[i] + flu.spl[i])
                d_excess_liquid_basin += der.relzoneareas[i] * (aid.wce[i] + flu.wcl[i])
        if (d_excess_frozen_basin + d_excess_liquid_basin) <= 0.0:
            return

        # redistribute the remaining excess from bottom to top:
        for i in range(con.nmbzones):
            t = der.indiceszonez[i]
            if con.zonetype[t] == ILAKE:
                continue
            d_excess_frozen_zone = d_excess_frozen_basin / der.relzoneareas[t]
            d_excess_liquid_zone = d_excess_liquid_basin / der.relzoneareas[t]
            d_excess_total_zone = d_excess_frozen_zone + d_excess_liquid_zone
            d_gain_max_cum = 0.0
            for c in range(con.sclass):
                d_gain_max_cum += con.smax[t] - sta.sp[c, t] - sta.wc[c, t]
            if d_gain_max_cum <= 0.0:
                continue
            d_fraction_gain_zone = min(
                d_gain_max_cum / con.sclass / d_excess_total_zone, 1.0
            )
            d_excess_frozen_zone_actual = d_fraction_gain_zone * d_excess_frozen_zone
            d_excess_liquid_zone_actual = d_fraction_gain_zone * d_excess_liquid_zone
            for c in range(con.sclass):
                d_fraction_gain_class = (
                    con.smax[t] - sta.sp[c, t] - sta.wc[c, t]
                ) / d_gain_max_cum
                d_delta_sp_zone = d_fraction_gain_class * d_excess_frozen_zone_actual
                d_delta_wc_zone = d_fraction_gain_class * d_excess_liquid_zone_actual
                flu.spg[t] += d_delta_sp_zone
                flu.wcg[t] += d_delta_wc_zone
                sta.sp[c, t] += d_delta_sp_zone * con.sclass
                sta.wc[c, t] += d_delta_wc_zone * con.sclass
            d_excess_frozen_basin -= d_excess_frozen_zone_actual * der.relzoneareas[t]
            d_excess_liquid_basin -= d_excess_liquid_zone_actual * der.relzoneareas[t]
            if (d_excess_frozen_basin + d_excess_liquid_basin) <= 0.0:
                return

        # redistribute the still remaining excess evenly:
        d_excess_frozen_land = d_excess_frozen_basin / der.rellandarea
        d_excess_liquid_land = d_excess_liquid_basin / der.rellandarea
        for t in range(con.nmbzones):
            if con.zonetype[t] != ILAKE:
                flu.spg[t] += d_excess_frozen_land
                flu.wcg[t] += d_excess_liquid_land
                for c in range(con.sclass):
                    sta.sp[c, t] += d_excess_frozen_land
                    sta.wc[c, t] += d_excess_liquid_land
        return


class Calc_CFAct_V1(modeltools.Method):
    r"""Adjust the day degree factor for snow to the current day of the year.

    Basic equations:
      :math:`CFAct = max( CFMax + f \cdot CFVar, 0 )`

      :math:`f = sin(2 \cdot  Pi \cdot (DOY + 1) / 366) / 2`

    Examples:

        We initialise five zones of different types but the same values for |CFMax| and
        |CFVar|.  For internal lakes, |CFAct| is always zero.  In all other cases,
        results are identical and follow a sinusoid curve throughout the year (of which
        we show only selected points as the maximum around June 20 and the minimum
        around December 20):

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED)
        >>> cfmax(4.0)
        >>> cfvar(3.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_cfact_v1,
        ...                 last_example=10,
        ...                 parseqs=(derived.doy, factors.cfact))
        >>> test.nexts.doy = 0, 1, 170, 171, 172, 353, 354, 355, 364, 365
        >>> test()
        | ex. |                     doy |                                       cfact |
        -------------------------------------------------------------------------------
        |   1 |   0    0    0    0    0 | 0.0  1.264648  1.264648  1.264648  1.264648 |
        |   2 |   1    1    1    1    1 | 0.0  1.267289  1.267289  1.267289  1.267289 |
        |   3 | 170  170  170  170  170 | 0.0  2.749762  2.749762  2.749762  2.749762 |
        |   4 | 171  171  171  171  171 | 0.0  2.749976  2.749976  2.749976  2.749976 |
        |   5 | 172  172  172  172  172 | 0.0  2.749969  2.749969  2.749969  2.749969 |
        |   6 | 353  353  353  353  353 | 0.0  1.250238  1.250238  1.250238  1.250238 |
        |   7 | 354  354  354  354  354 | 0.0  1.250024  1.250024  1.250024  1.250024 |
        |   8 | 355  355  355  355  355 | 0.0  1.250031  1.250031  1.250031  1.250031 |
        |   9 | 364  364  364  364  364 | 0.0  1.260018  1.260018  1.260018  1.260018 |
        |  10 | 365  365  365  365  365 | 0.0  1.262224  1.262224  1.262224  1.262224 |

        Now, we convert all zones to type |FIELD| and vary |CFVar|.  If we set |CFVar|
        to zero, |CFAct| always equals |CFMax| (see zone one).  If we change the sign
        of |CFVar|, the sinusoid curve shifts a half year to reflect the southern
        hemisphere's annual cycle of radiation (compare zone two and three).  Finally,
        |Calc_CFAct_V1| prevents negative values of |CFAct| by setting them to zero
        (see zone four and five):

        >>> zonetype(FIELD)
        >>> cfvar(0.0, 3.0, -3.0, 10.0, -10.0)
        >>> test()
        | ex. |                     doy |                                       cfact |
        -------------------------------------------------------------------------------
        |   1 |   0    0    0    0    0 | 2.0  1.264648  2.735352       0.0  4.451173 |
        |   2 |   1    1    1    1    1 | 2.0  1.267289  2.732711       0.0  4.442371 |
        |   3 | 170  170  170  170  170 | 2.0  2.749762  1.250238  4.499206       0.0 |
        |   4 | 171  171  171  171  171 | 2.0  2.749976  1.250024  4.499919       0.0 |
        |   5 | 172  172  172  172  172 | 2.0  2.749969  1.250031  4.499896       0.0 |
        |   6 | 353  353  353  353  353 | 2.0  1.250238  2.749762       0.0  4.499206 |
        |   7 | 354  354  354  354  354 | 2.0  1.250024  2.749976       0.0  4.499919 |
        |   8 | 355  355  355  355  355 | 2.0  1.250031  2.749969       0.0  4.499896 |
        |   9 | 364  364  364  364  364 | 2.0  1.260018  2.739982       0.0  4.466606 |
        |  10 | 365  365  365  365  365 | 2.0  1.262224  2.737776       0.0  4.459252 |
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.CFMax,
        hland_control.CFVar,
    )
    FIXEDPARAMETERS = (hland_fixed.Pi,)
    DERIVEDPARAMETERS = (hland_derived.DOY,)
    RESULTSEQUENCES = (hland_factors.CFAct,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        d_factor = 0.5 * modelutils.sin(
            2 * fix.pi * (der.doy[model.idx_sim] + 1) / 366 - 1.39
        )
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                fac.cfact[k] = max(con.cfmax[k] + d_factor * con.cfvar[k], 0.0)
            else:
                fac.cfact[k] = 0.0


class Calc_Melt_SP_WC_V1(modeltools.Method):
    r"""Calculate the melting of the ice content within the snow layer and update both
    the snow layers' ice and the water content.

    Basic equations:
      :math:`\frac{dSP}{dt} = - Melt`

      :math:`\frac{dWC}{dt} = + Melt`

      :math:`Melt = min(CFAct \cdot (TC - TTM), SP)`

    Examples:

        We initialise seven zones with the same threshold temperature and degree-day
        factor but different zone types and initial ice contents:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> sclass(1)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED, SEALED, SEALED)
        >>> derived.ttm = 2.0
        >>> factors.cfact(2.0)
        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = 2.0

        When the actual temperature equals the threshold temperature for melting and
        refreezing, no melting occurs, and the states remain unchanged:

        >>> factors.tc = 2.0
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)

        The same holds for an actual temperature lower than the threshold temperature:

        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = 2.0
        >>> factors.tc = -1.0
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)

        With an actual temperature of 3°C above the threshold temperature, melting can
        occur. The actual melting is consistent with potential melting, except for the
        first zone, an internal lake, and the last two zones, for which potential
        melting exceeds the available frozen water content of the snow layer:

        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = 2.0
        >>> factors.tc = 5.0
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 6.0, 6.0, 6.0, 6.0, 5.0, 0.0)
        >>> states.sp
        sp(0.0, 4.0, 4.0, 4.0, 4.0, 0.0, 0.0)
        >>> states.wc
        wc(0.0, 8.0, 8.0, 8.0, 8.0, 7.0, 2.0)

        In the above examples, we did not divide the zones into snow classes. If we do
        so, method |Calc_Melt_SP_WC_V1| assumes a uniform distribution of the
        potential melting among the individual classes.  This assumption implies that
        if a single snow class does not provide enough frozen water, the actual melting
        of the total zone must be smaller than its potential melt rate:

        >>> sclass(2)
        >>> states.sp = [[0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 0.0],
        ...              [0.0, 10.0, 10.0, 10.0, 10.0, 10.0, 0.0]]
        >>> states.wc = [[0.0], [2.0]]
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt([[0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 0.0],
              [0.0, 6.0, 6.0, 6.0, 6.0, 6.0, 0.0]])
        >>> states.sp
        sp([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 4.0, 4.0, 4.0, 4.0, 4.0, 0.0]])
        >>> states.wc
        wc([[0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 0.0],
            [0.0, 8.0, 8.0, 8.0, 8.0, 8.0, 2.0]])
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
    )
    DERIVEDPARAMETERS = (hland_derived.TTM,)
    REQUIREDSEQUENCES = (hland_factors.TC, hland_factors.CFAct)
    UPDATEDSEQUENCES = (hland_states.WC, hland_states.SP)
    RESULTSEQUENCES = (hland_fluxes.Melt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                if fac.tc[k] > der.ttm[k]:
                    d_potmelt = fac.cfact[k] * (fac.tc[k] - der.ttm[k])
                    for c in range(con.sclass):
                        flu.melt[c, k] = min(d_potmelt, sta.sp[c, k])
                        sta.sp[c, k] -= flu.melt[c, k]
                        sta.wc[c, k] += flu.melt[c, k]
                else:
                    for c in range(con.sclass):
                        flu.melt[c, k] = 0.0
            else:
                for c in range(con.sclass):
                    flu.melt[c, k] = 0.0
                    sta.wc[c, k] = 0.0
                    sta.sp[c, k] = 0.0


class Calc_Refr_SP_WC_V1(modeltools.Method):
    r"""Calculate refreezing of the water content within the snow layer and
    update both the snow layers' ice and the water content.

    Basic equations:
      :math:`\frac{dSP}{dt} =  + Refr`

      :math:`\frac{dWC}{dt} =  - Refr`

      :math:`Refr = min(cfr \cdot cfmax \cdot (TTM - TC), WC)`

    Examples:

        We initialise seven zones with the same threshold temperature, degree-day factor
        and refreezing coefficient but different zone types and initial states:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> sclass(1)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED, SEALED, SEALED)
        >>> cfmax(4.0)
        >>> cfr(0.1)
        >>> derived.ttm = 2.0
        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0

        Note that the assumed length of the simulation step is half a day.  Hence the
        effective value of the degree-day factor is not 4 but 2:

        >>> cfmax
        cfmax(4.0)
        >>> from hydpy import round_
        >>> round_(cfmax.values[0])
        2.0

        When the actual temperature equals the threshold temperature for melting and
        refreezing, no refreezing occurs, and the states remain unchanged:

        >>> factors.tc = 2.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        The same holds for an actual temperature higher than the threshold temperature:

        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0
        >>> factors.tc = 2.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        With an actual temperature of 3°C above the threshold temperature, there is no
        refreezing:

        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0
        >>> factors.tc = 5.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        With an actual temperature of 3°C below the threshold temperature, refreezing
        can occur. Actual refreezing is consistent with potential refreezing, except
        for the first zone, an internal lake, and the last two zones, for which
        potential refreezing exceeds the available liquid water content of the snow
        layer:

        >>> states.sp = 2.0
        >>> states.wc = 0.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0
        >>> factors.tc = -1.0
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.6, 0.6, 0.6, 0.6, 0.5, 0.0)
        >>> states.sp
        sp(0.0, 2.6, 2.6, 2.6, 2.6, 2.5, 2.0)
        >>> states.wc
        wc(0.0, 0.4, 0.4, 0.4, 0.4, 0.0, 0.0)

        In the above examples, we did not divide the zones into snow classes. If we do
        so, method |Calc_Refr_SP_WC_V1| assumes a uniform distribution of the potential
        refreezing among the individual classes.  This assumption implies that if a
        single snow class does not provide enough liquid water, the actual refreezing
        of the total zone must be smaller than its potential refreezing rate:

        >>> sclass(2)
        >>> states.sp = [[0.0], [2.0]]
        >>> states.wc = [[0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0],
        ...              [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]]
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr([[0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0],
              [0.0, 0.6, 0.6, 0.6, 0.6, 0.6, 0.0]])
        >>> states.sp
        sp([[0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0],
            [0.0, 2.6, 2.6, 2.6, 2.6, 2.6, 2.0]])
        >>> states.wc
        wc([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.4, 0.4, 0.4, 0.4, 0.4, 0.0]])
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
        hland_control.CFR,
        hland_control.CFMax,
    )
    DERIVEDPARAMETERS = (hland_derived.TTM,)
    REQUIREDSEQUENCES = (hland_factors.TC,)
    UPDATEDSEQUENCES = (hland_states.WC, hland_states.SP)
    RESULTSEQUENCES = (hland_fluxes.Refr,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                if fac.tc[k] < der.ttm[k]:
                    d_potrefr = con.cfr[k] * con.cfmax[k] * (der.ttm[k] - fac.tc[k])
                    for c in range(con.sclass):
                        flu.refr[c, k] = min(d_potrefr, sta.wc[c, k])
                        sta.sp[c, k] += flu.refr[c, k]
                        sta.wc[c, k] -= flu.refr[c, k]
                else:
                    for c in range(con.sclass):
                        flu.refr[c, k] = 0.0
            else:
                for c in range(con.sclass):
                    flu.refr[c, k] = 0.0
                    sta.wc[c, k] = 0.0
                    sta.sp[c, k] = 0.0


class Calc_In_WC_V1(modeltools.Method):
    r"""Calculate the actual water release from the snow layer due to the exceedance of
    the snow layers' capacity for (liquid) water.

    Basic equations:
      :math:`\frac{dWC}{dt} = -In`

      :math:`-In = max(WC - WHC \cdot SP, 0)`

    Examples:

        We initialise seven zones of different types with different frozen water
        contents of the snow layer and set the relative water holding capacity to 20 %:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> sclass(1)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED, SEALED, SEALED)
        >>> whc(0.2)
        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0

        Also, we set the actual value of stand precipitation to 5 mm/d:

        >>> fluxes.tf = 5.0

        When there is no (liquid) water content in the snow layer, no water can be
        released:

        >>> states.wc = 0.0
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        When there is a (liquid) water content in the snow layer, the water release
        depends on the frozen water content.  Note the special cases of the first zone
        being an internal lake, for which the snow routine does not apply, and of the
        last zone, which has no ice content and thus effectively is not a snow layer:

        >>> states.wc = 5.0
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 3.0, 3.0, 3.0, 3.0, 4.0, 5.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 2.0, 1.0, 0.0)

        For a relative water holding capacity of zero, the snow layer releases all
        liquid water immediately:

        >>> whc(0.0)
        >>> states.wc = 5.0
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        In the above examples, we did not divide the zones into snow classes. If we do
        so, method |Calc_In_WC_V1| averages the water release of all snow classes of
        each zone:

        >>> sclass(2)
        >>> whc(0.0)
        >>> states.sp = 0.0, 10.0, 10.0, 10.0, 10.0, 5.0, 0.0
        >>> states.wc = [[2.0], [3.0]]
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(5.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5)
        >>> states.wc
        wc([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

        For the single lake zone, method |Calc_In_WC_V1| passed the stand precipitation
        directly to |In_| in all examples.
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
        hland_control.WHC,
    )
    REQUIREDSEQUENCES = (hland_fluxes.TF, hland_states.SP)
    UPDATEDSEQUENCES = (hland_states.WC,)
    RESULTSEQUENCES = (hland_fluxes.In_,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            flu.in_[k] = 0.0
            if con.zonetype[k] != ILAKE:
                for c in range(con.sclass):
                    d_wc_old = sta.wc[c, k]
                    sta.wc[c, k] = min(d_wc_old, con.whc[k] * sta.sp[c, k])
                    flu.in_[k] += (d_wc_old - sta.wc[c, k]) / con.sclass
            else:
                flu.in_[k] = flu.tf[k]
                for c in range(con.sclass):
                    sta.wc[c, k] = 0.0


class Calc_SWE_V1(modeltools.Method):
    r"""Calculate the total snow water equivalent.

    Basic equation:
      :math:`SWE = SP + WC`

    Example:

        We initialise five zones of different types, each one with two snow classes.
        For internal lakes, |Calc_SWE_V1| generally sets the snow water equivalent to
        zero.  For all others, the given basic equation applies:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> sclass(2)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED)
        >>> states.wc = [[0.1, 0.2, 0.3, 0.4, 0.5], [0.6, 0.7, 0.8, 0.9, 1.0]]
        >>> states.sp = [[1.0, 2.0, 3.0, 4.0, 5.0], [6.0, 7.0, 8.0, 9.0, 10.0]]
        >>> model.calc_swe_v1()
        >>> factors.swe
        swe([[0.0, 2.2, 3.3, 4.4, 5.5],
             [0.0, 7.7, 8.8, 9.9, 11.0]])
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
    )
    REQUIREDSEQUENCES = (hland_states.SP, hland_states.WC)
    RESULTSEQUENCES = (hland_factors.SWE,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                for c in range(con.sclass):
                    fac.swe[c, k] = sta.sp[c, k] + sta.wc[c, k]
            else:
                for c in range(con.sclass):
                    fac.swe[c, k] = 0.0


class Calc_SR_V1(modeltools.Method):
    r"""Calculate the sealed surface runoff.

    Basic equations:
      .. math::
        SR =
        \begin{cases}
        In &|\ ZoneType_k = SEALED
        \\
        0 &|\ ZoneType_k \neq SEALED
        \end{cases}

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED)
        >>> fluxes.in_ = 1.0
        >>> fluxes.sr = 2.0
        >>> model.calc_sr_v1()
        >>> fluxes.sr
        sr(0.0, 0.0, 0.0, 0.0, 1.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    REQUIREDSEQUENCES = (hland_fluxes.In_,)
    RESULTSEQUENCES = (hland_fluxes.SR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] == SEALED:
                flu.sr[k] = flu.in_[k]
            else:
                flu.sr[k] = 0.0


class Calc_GAct_V1(modeltools.Method):
    r"""Adjust the day degree factor for glacier ice to the current day of the year.

    Basic equations:
      :math:`GAct = max( GMelt + f \cdot GVar, 0 )`

      :math:`f = sin(2 \cdot  Pi \cdot (DOY + 1) / 366) / 2`

    Examples:

        The following examples agree with the ones |Calc_CFAct_V1|, except that method
        |Calc_GAct_V1| applies the given basic equations only for zones of types
        |GLACIER| and sets |GAct| to zero for all other zone types:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, SEALED)
        >>> gmelt(4.0)
        >>> gvar(3.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_gact_v1,
        ...                 last_example=10,
        ...                 parseqs=(derived.doy, factors.gact))
        >>> test.nexts.doy = 0, 1, 170, 171, 172, 353, 354, 355, 364, 365
        >>> test()
        | ex. |                     doy |                          gact |
        -----------------------------------------------------------------
        |   1 |   0    0    0    0    0 | 0.0  1.264648  0.0  0.0   0.0 |
        |   2 |   1    1    1    1    1 | 0.0  1.267289  0.0  0.0   0.0 |
        |   3 | 170  170  170  170  170 | 0.0  2.749762  0.0  0.0   0.0 |
        |   4 | 171  171  171  171  171 | 0.0  2.749976  0.0  0.0   0.0 |
        |   5 | 172  172  172  172  172 | 0.0  2.749969  0.0  0.0   0.0 |
        |   6 | 353  353  353  353  353 | 0.0  1.250238  0.0  0.0   0.0 |
        |   7 | 354  354  354  354  354 | 0.0  1.250024  0.0  0.0   0.0 |
        |   8 | 355  355  355  355  355 | 0.0  1.250031  0.0  0.0   0.0 |
        |   9 | 364  364  364  364  364 | 0.0  1.260018  0.0  0.0   0.0 |
        |  10 | 365  365  365  365  365 | 0.0  1.262224  0.0  0.0   0.0 |

        >>> zonetype(GLACIER)
        >>> gvar(0.0, 3.0, -3.0, 10.0, -10.0)
        >>> test()
        | ex. |                     doy |                                        gact |
        -------------------------------------------------------------------------------
        |   1 |   0    0    0    0    0 | 2.0  1.264648  2.735352       0.0  4.451173 |
        |   2 |   1    1    1    1    1 | 2.0  1.267289  2.732711       0.0  4.442371 |
        |   3 | 170  170  170  170  170 | 2.0  2.749762  1.250238  4.499206       0.0 |
        |   4 | 171  171  171  171  171 | 2.0  2.749976  1.250024  4.499919       0.0 |
        |   5 | 172  172  172  172  172 | 2.0  2.749969  1.250031  4.499896       0.0 |
        |   6 | 353  353  353  353  353 | 2.0  1.250238  2.749762       0.0  4.499206 |
        |   7 | 354  354  354  354  354 | 2.0  1.250024  2.749976       0.0  4.499919 |
        |   8 | 355  355  355  355  355 | 2.0  1.250031  2.749969       0.0  4.499896 |
        |   9 | 364  364  364  364  364 | 2.0  1.260018  2.739982       0.0  4.466606 |
        |  10 | 365  365  365  365  365 | 2.0  1.262224  2.737776       0.0  4.459252 |
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.GMelt,
        hland_control.GVar,
    )
    FIXEDPARAMETERS = (hland_fixed.Pi,)
    DERIVEDPARAMETERS = (hland_derived.DOY,)
    RESULTSEQUENCES = (hland_factors.GAct,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        d_factor = 0.5 * modelutils.sin(
            2 * fix.pi * (der.doy[model.idx_sim] + 1) / 366 - 1.39
        )
        for k in range(con.nmbzones):
            if con.zonetype[k] == GLACIER:
                fac.gact[k] = max(con.gmelt[k] + d_factor * con.gvar[k], 0.0)
            else:
                fac.gact[k] = 0.0


class Calc_GlMelt_In_V1(modeltools.Method):
    r"""Calculate the melting of non-snow-covered glaciers and add it to the water
    release of the snow module.

    Basic equation:
      .. math::
        GlMelt =
        \begin{cases}
        max(GMelt \cdot (TC - TTM), 0) &|\ SP = 0
        \\
        0 &|\ SP > 0
        \end{cases}

    Examples:

        We prepare eight zones. The first four zones are no glaciers, a snow layer
        covers the sixth zone, and the last two zones actual temperature is not above
        the threshold temperature.  Hence, glacier melting occurs only in the fifth
        zone:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(8)
        >>> sclass(1)
        >>> zonetype(FIELD, FOREST, ILAKE, SEALED, GLACIER, GLACIER, GLACIER, GLACIER)
        >>> derived.ttm(2.0)
        >>> factors.tc = 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 2.0, 1.0
        >>> factors.gact = 2.0
        >>> states.sp = 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0
        >>> fluxes.in_ = 3.0
        >>> model.calc_glmelt_in_v1()
        >>> fluxes.glmelt
        glmelt(0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0)
        >>> fluxes.in_
        in_(3.0, 3.0, 3.0, 3.0, 5.0, 3.0, 3.0, 3.0)

        In the above examples, we did not divide the zones into snow classes. If we do
        so, method |Calc_GlMelt_In_V1| sums the glacier melt of all non-snow-covered
        snow classes of each glacier zone. This assumption implies that if there is a
        single snow-covered snow class, the actual glacier melting of the total zone
        must be smaller than its potential melt rate:

        >>> sclass(2)
        >>> factors.tc = 3.0
        >>> fluxes.in_ = 3.0
        >>> states.sp = [[0.0, 0.0, 0.1, 0.1, 0.0, 0.0, 0.1, 0.1],
        ...              [0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1]]
        >>> model.calc_glmelt_in_v1()
        >>> fluxes.glmelt
        glmelt(0.0, 0.0, 0.0, 0.0, 2.0, 1.0, 1.0, 0.0)
        >>> fluxes.in_
        in_(3.0, 3.0, 3.0, 3.0, 5.0, 4.0, 4.0, 3.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.SClass,
        hland_control.ZoneType,
    )
    DERIVEDPARAMETERS = (hland_derived.TTM,)
    REQUIREDSEQUENCES = (hland_states.SP, hland_factors.TC, hland_factors.GAct)
    UPDATEDSEQUENCES = (hland_fluxes.In_,)
    RESULTSEQUENCES = (hland_fluxes.GlMelt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            flu.glmelt[k] = 0.0
            if (con.zonetype[k] == GLACIER) and (fac.tc[k] > der.ttm[k]):
                d_glmeltpot = fac.gact[k] / con.sclass * (fac.tc[k] - der.ttm[k])
                for c in range(con.sclass):
                    if sta.sp[c, k] <= 0.0:
                        flu.glmelt[k] += d_glmeltpot
                        flu.in_[k] += d_glmeltpot


class Calc_R_SM_V1(modeltools.Method):
    r"""Calculate effective precipitation and update the soil moisture.

    Basic equations:
      :math:`\frac{dSM}{dt} = IN - R`

      :math:`R = IN \cdot \left( \frac{SM}{FC} \right)^{Beta}`


    Examples:

        We initialise seven zones of different types.  The field capacity of all fields
        and forests is 200 mm, the input of each zone is 10 mm:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> zonetype(ILAKE, GLACIER, SEALED, FIELD, FIELD, FOREST, FOREST)
        >>> fc(200.0)
        >>> fluxes.in_ = 10.0

        With the typical nonlinearity parameter value of 2, relative soil moisture of
        50 % (zones five and six) results in a discharge coefficient of 25 %.  For
        a completely dried (zone four) or saturated soil (zone seven), the discharge
        coefficient is generally 0 % and 100 %, respectively.  Glaciers, internal lakes
        and sealed areas always route 100% of their input as effective precipitation:

        >>> beta(2.0)
        >>> states.sm = 0.0, 0.0, 0.0, 0.0, 100.0, 100.0, 200.0
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 0.0, 2.5, 2.5, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 10.0, 107.5, 107.5, 200.0)

        By decreasing the nonlinearity parameter, the discharge coefficient increases.
        A parameter value of zero leads to a discharge coefficient of 100 % for any
        soil moisture:

        >>> beta(0.0)
        >>> states.sm = 0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        Also, with a field capacity of zero, the discharge coefficient always equates
        to 100 %:

        >>> fc(0.0)
        >>> beta(2.0)
        >>> states.sm = 0.0
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
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
    r"""Calculate capillary flow and update the soil moisture.

    Basic equations:
      :math:`\frac{dSM}{dt} = CF`

      :math:`CF = CFLUX \cdot (1 - \frac{SM}{FC})`

    Examples:

        We initialise seven zones of different types.  For all fields and forests, the
        field capacity is 200 mm and the maximum capillary flow rate is 4 mm/d:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> zonetype(ILAKE, GLACIER, SEALED, FIELD, FOREST, FOREST, FOREST)
        >>> fc(200.0)
        >>> cflux(4.0)

        Note that the assumed length of the simulation step is only half a day.  Hence
        the maximum capillary flow per simulation step is 2 instead of 4:

        >>> cflux
        cflux(4.0)
        >>> from hydpy import round_
        >>> round_(cflux.values[0])
        2.0

        For fields and forests, the actual capillary return flow depends only on the
        relative soil moisture deficit, provided that the upper zone layer stores
        enough water or that enough "routable" effective precipitation is available:

        >>> fluxes.r = 0.0
        >>> states.sm = 0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 20.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 1.0, 1.0, 2.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 101.0, 101.0, 2.0, 200.0)

        >>> states.sm = 0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 0.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        If the upper zone layer is empty and no effective precipitation is available,
        capillary flow is zero:

        >>> fluxes.r = 0.0
        >>> states.sm = 0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 0.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        In the following example, both the upper zone layer and effective precipitation
        provide water for the capillary flow but less than the maximum flow rate times
        the relative soil moisture:

        >>> fluxes.r = 0.1
        >>> states.sm = 0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 0.2
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.3, 0.3, 0.3, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 100.3, 100.3, 0.3, 200.0)

        Even unrealistic high maximum capillary flow rates do not result in overfilled
        soils:

        >>> cflux(1000.0)
        >>> fluxes.r = 200.0
        >>> states.sm = 0.0, 0.0, 0.0, 100.0, 100.0, 0.0, 200.0
        >>> states.uz = 200.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 100.0, 100.0, 200.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 200.0, 200.0, 200.0, 200.0)

        For soils with zero field capacity, capillary flow is always zero:

        >>> fc(0.0)
        >>> states.sm = 0.0
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
        hland_control.CFlux,
    )
    REQUIREDSEQUENCES = (hland_fluxes.R, hland_states.UZ)
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


class Calc_EA_SM_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    soil evapotranspiration and adjust the soil water content.

    Basic equation:
      :math:`\frac{dSM_i}{dt} = -EA_i`

    Examples:

        We build an example based on |evap_aet_hbv96| for calculating soil
        evapotranspiration:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep("1h")
        >>> nmbzones(5)
        >>> zonetype(GLACIER, SEALED, FIELD, FOREST, ILAKE)
        >>> area(1.0)
        >>> zonearea(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> zonez(5.0)
        >>> fc(50.0)
        >>> fluxes.r = 0.5
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     soilmoisturelimit(0.0)
        ...     excessreduction(field=0.5, forest=0.0)

        |Calc_EA_SM_AETModel_V1| uses the flux returned by the submodel to adjust |SM|:

        >>> model.aetmodel.sequences.fluxes.potentialinterceptionevaporation = 1.0
        >>> model.aetmodel.sequences.fluxes.potentialsoilevapotranspiration = 1.0
        >>> model.aetmodel.sequences.fluxes.interceptionevaporation = 1.0
        >>> states.sm = 3.0
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 0.5, 1.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 2.5, 2.0, 0.0)
        >>> fluxes.r
        r(0.5, 0.5, 0.5, 0.5, 0.5)

        |Calc_EA_SM_AETModel_V1| eventually reduces |EA| so that |SM| does not become
        negative:

        >>> model.aetmodel.sequences.fluxes.potentialinterceptionevaporation = 5.0
        >>> model.aetmodel.sequences.fluxes.potentialsoilevapotranspiration = 5.0
        >>> model.aetmodel.sequences.fluxes.interceptionevaporation = 5.0
        >>> states.sm = 3.0
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 2.5, 3.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.5, 0.0, 0.0)
        >>> fluxes.r
        r(0.5, 0.5, 0.5, 0.5, 0.5)

        |Calc_EA_SM_AETModel_V1| converts any amounts of condensation (negative |EA|)
        that would cause soil water to exceed field capacity to the effective soil
        response (|R|):

        >>> model.aetmodel.sequences.fluxes.potentialinterceptionevaporation = -5.0
        >>> model.aetmodel.sequences.fluxes.potentialsoilevapotranspiration = -5.0
        >>> model.aetmodel.sequences.fluxes.interceptionevaporation = -5.0
        >>> states.sm = 47.0
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, -2.5, -5.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 49.5, 50.0, 0.0)
        >>> fluxes.r
        r(0.5, 0.5, 0.5, 2.5, 0.5)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
    )
    UPDATEDSEQUENCES = (hland_states.SM, hland_fluxes.R)
    RESULTSEQUENCES = (hland_fluxes.EA,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_soilevapotranspiration()
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST):
                flu.ea[k] = min(submodel.get_soilevapotranspiration(k), sta.sm[k])
                sta.sm[k] -= flu.ea[k]
                if sta.sm[k] > con.fc[k]:
                    flu.r[k] += sta.sm[k] - con.fc[k]
                    sta.sm[k] = con.fc[k]
            else:
                flu.ea[k] = 0.0
                sta.sm[k] = 0.0


class Calc_EA_SM_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate soil
    evapotranspiration and adjust the soil water content."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_EA_SM_AETModel_V1,)
    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
    )
    UPDATEDSEQUENCES = (hland_states.SM, hland_fluxes.R)
    RESULTSEQUENCES = (hland_fluxes.EA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_ea_sm_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_InUZ_V1(modeltools.Method):
    r"""Accumulate the total inflow into the upper zone layer.

    Basic equation:
      .. math::
        InUZ = \sum_{k=1}^{NmbZones} \frac{RelZoneAreas_k}{RelUpperZoneArea} \cdot
        \begin{cases}
        R-CF &|\ ZoneType_k \in \{FIELD, FOREST, GLACIER \}
        \\
        0 &|\ ZoneType_k \notin \{FIELD, FOREST, GLACIER \}
        \end{cases}

    Examples:

        We initialise five zones of different land-use types and sizes.  Method
        |Calc_InUZ_V1| takes only those of type |FIELD|, |FOREST|, and |GLACIER| into
        account:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, ILAKE, GLACIER, SEALED)
        >>> derived.relzoneareas = 0.25, 0.2, 0.4, 0.05, 0.1
        >>> derived.relupperzonearea = 0.5
        >>> fluxes.r = 2.0, 4.0, 1.0, 6.0, 1.0
        >>> fluxes.cf = 1.0, 2.0, 0.5, 3.0, 0.5
        >>> model.calc_inuz_v1()
        >>> fluxes.inuz
        inuz(1.6)

        Internal lakes and sealed areas do not contribute to the upper zone layer.
        Hence, for a subbasin consisting only of such zones, |InUZ| is zero:

        >>> zonetype(ILAKE, ILAKE, ILAKE, SEALED, SEALED)
        >>> model.calc_inuz_v1()
        >>> fluxes.inuz
        inuz(0.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelUpperZoneArea)
    REQUIREDSEQUENCES = (hland_fluxes.R, hland_fluxes.CF)
    RESULTSEQUENCES = (hland_fluxes.InUZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inuz = 0.0
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                flu.inuz += (
                    der.relzoneareas[k] / der.relupperzonearea * (flu.r[k] - flu.cf[k])
                )


class Calc_SUZ_V1(modeltools.Method):
    r"""Add the effective precipitation to the upper storage reservoir.

    Basic equation:
      :math:`\frac{SUZ}{dt} = R`

    Example:

        For internal lakes and sealed areas, method |Calc_SUZ_V1| always sets |SUZ| to
        zero:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep()
        >>> nmbzones(4)
        >>> zonetype(FIELD, ILAKE, GLACIER, SEALED)
        >>> states.suz = 1.0, 0.0, 2.0, 0.0
        >>> fluxes.r = 2.0
        >>> model.calc_suz_v1()
        >>> states.suz
        suz(3.0, 0.0, 4.0, 0.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    REQUIREDSEQUENCES = (hland_fluxes.R,)
    UPDATEDSEQUENCES = (hland_states.SUZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                sta.suz[k] += flu.r[k]
            else:
                sta.suz[k] = 0.0


class Calc_ContriArea_V1(modeltools.Method):
    r"""Determine the relative size of the contributing area of the whole subbasin.

    Basic equation:
      :math:`ContriArea = \left( \frac{SM}{FC} \right)^{Beta}`

    Examples:

        We initialise five zones. Method |Calc_ContriArea_V1| takes only the first two
        zones of type field and forest into account (even though glaciers also
        contribute to the inflow of the upper zone layer):

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> beta(2.0)
        >>> fc(200.0)
        >>> resparea(True)
        >>> derived.relzoneareas(1.0/6.0, 2.0/6.0, 1.0/6.0, 1.0/6.0, 1.0/6.0)
        >>> derived.relsoilarea(0.5)

        With relative soil moisture of 100 % in the whole subbasin, the contributing
        area is also 100 %:

        >>> states.sm = 200.0
        >>> model.calc_contriarea_v1()
        >>> factors.contriarea
        contriarea(1.0)

        Relative soil moistures of 0 % result in a contributing area of 0 %:

        >>> states.sm = 0.0
        >>> model.calc_contriarea_v1()
        >>> factors.contriarea
        contriarea(0.0)

        For the given value 2 of the nonlinearity parameter |Beta|, soil moisture of
        50 % corresponds to contributing area of 25 %:

        >>> states.sm = 100.0
        >>> model.calc_contriarea_v1()
        >>> factors.contriarea
        contriarea(0.25)

        Setting the |RespArea| option to |False|, the soil area (total area of all
        field and forest zones in the subbasin) to zero, or all field capacities to
        zero, results in contributing area values of 100 %:

        >>> resparea(False)
        >>> model.calc_contriarea_v1()
        >>> factors.contriarea
        contriarea(1.0)

        >>> resparea(True)
        >>> derived.relsoilarea(0.0)
        >>> model.calc_contriarea_v1()
        >>> factors.contriarea
        contriarea(1.0)

        >>> derived.relsoilarea(0.5)
        >>> fc(0.0)
        >>> states.sm = 0.0
        >>> model.calc_contriarea_v1()
        >>> factors.contriarea
        contriarea(1.0)
    """

    CONTROLPARAMETERS = (
        hland_control.RespArea,
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.FC,
        hland_control.Beta,
    )
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelSoilArea)
    REQUIREDSEQUENCES = (hland_states.SM,)
    RESULTSEQUENCES = (hland_factors.ContriArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        fac.contriarea = 1.0
        if con.resparea and (der.relsoilarea > 0.0):
            for k in range(con.nmbzones):
                if con.zonetype[k] in (FIELD, FOREST):
                    if con.fc[k] > 0.0:
                        d_weight = der.relzoneareas[k] / der.relsoilarea
                        fac.contriarea *= (sta.sm[k] / con.fc[k]) ** d_weight
            fac.contriarea **= con.beta[k]


class Calc_Q0_Perc_UZ_V1(modeltools.Method):
    r"""Calculate the percolation and direct runoff leaving the upper zone storage
    and update it accordingly.

    Basic equations:
      :math:`\frac{dUZ}{dt} = InUZ - Perc - Q0`

      :math:`Perc = PercMax \cdot ContriArea`

      :math:`Q0 = K \cdot \left( \frac{UZ}{ContriArea} \right)^{1+Alpha}`

    Note that the system behaviour of this method depends strongly on the
    specifications of the options |RespArea| and |RecStep|.

    Examples:

        First, we prepare a small helper function for checking if method
        |Calc_Q0_Perc_UZ_V1| always complies with the water balance equation, assuming
        an initial content of the upper zone storage of 1 mm:

        >>> from hydpy import round_
        >>> def check():
        ...     error = 1.0 + fluxes.inuz - fluxes.perc - fluxes.q0 - states.uz
        ...     assert round(error, 12) == 0

        The upper zone layer routine is an exception compared to the other subroutines
        of |hland| regarding numerical accuracy.  Method |Calc_Q0_Perc_UZ_V1| divides
        each simulation step into substeps and solves each substep with the explicit
        Euler method.  The more substeps involved, the more precise the numerical
        integration of the underlying ordinary differential equations.  In the first
        example, we omit this option by setting the |RecStep| parameter, which defines
        the number of substeps, to one:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> recstep(2)
        >>> derived.dt = 1/recstep
        >>> percmax(2.0)
        >>> alpha(1.0)
        >>> k(2.0)
        >>> factors.contriarea = 1.0
        >>> fluxes.inuz = 0.0
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(1.0)
        >>> fluxes.q0
        q0(0.0)
        >>> states.uz
        uz(0.0)
        >>> check()

        Due to the sequential calculation of the upper zone routine, the upper zone
        storage drains completely through percolation, and no water remains for fast
        discharge response.  By dividing the simulation step into 100 substeps, method
        |Calc_Q0_Perc_UZ_V1| also calculates a considerable amount of direct runoff:

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
        >>> check()

        Note that the assumed length of the simulation step is half a day. Hence the
        effective values of the maximum percolation rate and the storage coefficient
        are not 2 but 1:

        >>> percmax
        percmax(2.0)
        >>> k
        k(2.0)
        >>> percmax.value
        1.0
        >>> k.value
        1.0

        By decreasing the contributing area, one reduces percolation but increases the
        fast discharge response:

        >>> factors.contriarea = 0.5
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.434108)
        >>> fluxes.q0
        q0(0.565892)
        >>> states.uz
        uz(0.0)
        >>> check()

        Without any contributing area, the complete amount of water stored in the upper
        zone layer is released as direct discharge immediately:

        >>> factors.contriarea = 0.0
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.0)
        >>> fluxes.q0
        q0(1.0)
        >>> states.uz
        uz(0.0)
        >>> check()

        Resetting |RecStep| leads to more transparent results.  Note that direct
        discharge drains the rest of the upper zone storage due to the storage
        coefficient's large value and the numerical approximation's low accuracy:

        >>> recstep(2)
        >>> factors.contriarea = 0.5
        >>> derived.dt = 1.0/recstep
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.5)
        >>> states.uz
        uz(0.0)
        >>> check()

        Applying a more reasonable storage coefficient leads to the following results:

        >>> k(0.5)
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.25)
        >>> states.uz
        uz(0.25)
        >>> check()

        Adding an input of 0.3 mm results in the same percolation value (which here is
        determined by the maximum percolation rate only) but increases the direct
        response (which always depends on the actual upper zone storage):

        >>> fluxes.inuz = 0.3
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.64)
        >>> states.uz
        uz(0.16)
        >>> check()

        Due to the same reasons, another increase in numerical accuracy has no impact
        on percolation but decreases the direct response:

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
        >>> check()

        If phases of capillary rise, |InUZ| is negative and constant throughout the
        complete simulation interval.  However, if |UZ| runs dry during the simulation
        interval, it can no contribute to the capillary rise.  To always comply with
        the water balance equation, method |Calc_Q0_Perc_UZ_V1| reduces both |Perc|
        and |Q0| by the same factor in such situations.  Reducing |InUZ| would be more
        reasonable but would also require modifying |CF| and |SM| (and others?), which
        is way too much effort given the minor impact of this manipulation on the
        general simulation results.  The following two examples show how the
        manipulation works if the capillary rise requires all (first example) or half
        (second example) of the available water.

        >>> fluxes.inuz = -1.0
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.0)
        >>> fluxes.q0
        q0(0.0)
        >>> states.uz
        uz(0.0)
        >>> check()

        >>> fluxes.inuz = -0.5
        >>> states.uz = 1.0
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.323912)
        >>> fluxes.q0
        q0(0.176088)
        >>> states.uz
        uz(0.0)
        >>> check()
    """

    CONTROLPARAMETERS = (
        hland_control.RecStep,
        hland_control.PercMax,
        hland_control.K,
        hland_control.Alpha,
    )
    DERIVEDPARAMETERS = (hland_derived.DT,)
    REQUIREDSEQUENCES = (hland_factors.ContriArea, hland_fluxes.InUZ)
    UPDATEDSEQUENCES = (hland_states.UZ,)
    RESULTSEQUENCES = (hland_fluxes.Perc, hland_fluxes.Q0)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        uz_old: float = sta.uz
        flu.perc = 0.0
        flu.q0 = 0.0
        for _ in range(con.recstep):
            sta.uz = max(sta.uz + der.dt * flu.inuz, 0.0)
            perc: float = min(der.dt * con.percmax * fac.contriarea, sta.uz)
            sta.uz -= perc
            flu.perc += perc
            if sta.uz > 0.0:
                if fac.contriarea > 0.0:
                    q0: float = min(
                        der.dt * con.k * (sta.uz / fac.contriarea) ** (1.0 + con.alpha),
                        sta.uz,
                    )
                else:
                    q0 = sta.uz
                sta.uz -= q0
                flu.q0 += q0
        error: float = sta.uz - (uz_old + flu.inuz - flu.perc - flu.q0)
        if error > 0.0:
            factor: float = 1.0 - error / (flu.perc + flu.q0)
            flu.perc *= factor
            flu.q0 *= factor


class Calc_DP_SUZ_V1(modeltools.Method):
    r"""Calculate the deep percolation and remove it from the upper storage reservoir.

    Basic equation:
      :math:`DP = min(PERCMax, SUZ)`

      :math:`\frac{SUZ}{dt} = -DP`

      :math:`\frac{SUZ}{dt} = -RS -RI`

    Example:

        For internal lakes and sealed areas, method |Calc_DP_SUZ_V1| always sets the
        values of |DP| and |SUZ| to zero:

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(9)
        >>> zonetype(FIELD, FIELD, FIELD, FIELD, FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> percmax(4.8)
        >>> states.suz = 0.0, 0.1, 0.2, 0.3, 0.4, 0.4, 0.4, 0.4, 0.4
        >>> model.calc_dp_suz_v1()
        >>> fluxes.dp
        dp(0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0, 0.0)
        >>> states.suz
        suz(0.0, 0.0, 0.0, 0.1, 0.2, 0.2, 0.2, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.PercMax,
    )
    UPDATEDSEQUENCES = (hland_states.SUZ,)
    RESULTSEQUENCES = (hland_fluxes.DP,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                flu.dp[k] = min(sta.suz[k], con.percmax)
                sta.suz[k] -= flu.dp[k]
            else:
                flu.dp[k] = 0.0
                sta.suz[k] = 0.0


class Calc_QAb_QVs_BW_V1(modeltools.Method):
    """Calculate the flow and the percolation from a two-outlet reservoir and update it.

    Method |Calc_QAb_QVs_BW_V1| is an "additional method" used by the "run methods"
    |Calc_QAb1_QVs1_BW1_V1| and |Calc_QAb2_QVs2_BW2_V1| for calculating the flow and
    the percolation from the surface water reservoir and the interflow reservoir,
    respectively.  See the documentation on method |Calc_QAb1_QVs1_BW1_V1| for further
    information.
    """

    # positional arguments required for consistency with the cythonized extension class:
    @staticmethod
    def __call__(  # pylint: disable=too-many-positional-arguments
        model: modeltools.Model,
        k: int,
        h: VectorFloat,
        k1: VectorFloat,
        k2: VectorFloat,
        s0: VectorFloat,
        qz: VectorFloat,
        qa1: VectorFloat,
        qa2: VectorFloat,
        t0: float,
        /,
    ) -> None:
        d_h = h[k]
        d_k1 = k1[k]
        d_k2 = k2[k]
        d_qz = qz[k]
        d_s0 = s0[k]
        if (d_k1 == 0.0) and (d_s0 > d_h):
            qa1[k] += d_s0 - d_h
            s0[k] = d_s0 = d_h
        if (d_k1 == 0.0) and (d_s0 == d_h) and (d_qz > d_h / d_k2):
            d_qa2 = d_h / d_k2
            d_dt = 1.0 - t0
            qa2[k] += d_dt * d_qa2
            qa1[k] += d_dt * (d_qz - d_qa2)
        elif d_k2 == 0.0:
            qa2[k] += d_s0 + d_qz
            s0[k] = 0.0
        elif (d_s0 < d_h) or (d_s0 == d_h and d_qz <= d_h / d_k2):
            if (d_s0 == d_h) or (d_qz <= d_h / d_k2):
                d_t1 = 1.0
            elif modelutils.isinf(d_k2):
                d_t1 = (d_h - d_s0) / d_qz
            else:
                d_t1 = t0 + d_k2 * modelutils.log(
                    (d_qz - d_s0 / d_k2) / (d_qz - d_h / d_k2)
                )
            if 0.0 < d_t1 < 1.0:
                qa2[k] += (d_t1 - t0) * d_qz - (d_h - d_s0)
                s0[k] = d_h
                model.calc_qab_qvs_bw_v1(k, h, k1, k2, s0, qz, qa1, qa2, d_t1)
            elif modelutils.isinf(d_k2):
                s0[k] += (1.0 - t0) * d_qz
            else:
                d_dt = 1.0 - t0
                d_k2qz = d_k2 * d_qz
                s0[k] = d_k2qz - (d_k2qz - d_s0) * modelutils.exp(-d_dt / d_k2)
                qa2[k] += d_s0 - s0[k] + d_dt * d_qz
        else:
            d_v1 = 1.0 / d_k1 + 1.0 / d_k2
            d_v2 = d_qz + d_h / d_k1
            d_nom = d_v2 - d_h * d_v1
            d_denom = d_v2 - d_s0 * d_v1
            if (d_s0 == d_h) or (d_denom == 0.0) or (not 0 < d_nom / d_denom <= 1):
                d_t1 = 1.0
            else:
                d_t1 = t0 - 1.0 / d_v1 * modelutils.log(d_nom / d_denom)
                d_t1 = min(d_t1, 1.0)
            d_dt = d_t1 - t0
            d_v3 = (d_v2 * d_dt) / d_v1
            d_v4 = d_denom / d_v1**2 * (1.0 - modelutils.exp(-d_dt * d_v1))
            d_qa1 = (d_v3 - d_v4 - d_h * d_dt) / d_k1
            d_qa2 = (d_v3 - d_v4) / d_k2
            qa1[k] += d_qa1
            qa2[k] += d_qa2
            if d_t1 == 1.0:
                s0[k] += d_dt * d_qz - d_qa1 - d_qa2
            else:
                s0[k] = d_h
            if d_t1 < 1.0:
                model.calc_qab_qvs_bw_v1(k, h, k1, k2, s0, qz, qa1, qa2, d_t1)


class Calc_QAb1_QVs1_BW1_V1(modeltools.Method):
    r"""Calculate the flow and the percolation from the surface flow reservoir and
    update it.

    Basic equations:
      :math:`\frac{dBW1}{dt} = R - QAb1 - QVs1`

      :math:`QAb1 = \frac{max(BW1 - H1, 0)}{TAb1}`

      :math:`QVs1 = \frac{BW1}{TVs1}`

    We follow the new COSERO implementation described in :cite:t:`ref-Kling2005` and
    :cite:t:`ref-Kling2006` and solve the given ordinary differential equation under the
    assumption of constant inflow (|R|).  Despite the simple appearance of the short
    equation, its solution is quite complicated due to the threshold |H1| used
    (:cite:t:`ref-Kling2005` and :cite:t:`ref-Kling2006` explain the math in some
    detail).
    Additionally, we allow setting either |TAb1| or |TVs1| to |numpy.inf| or zero,
    allowing for disabling certain surface flow reservoir functionalities.
    Consequently, our source code includes many branches, and extensive testing is
    required to get some confidence in its robustness.  We verified each of the
    following tests with numerical integration results.  You can find this independent
    test code in `issue 68`_.  Please tell us if you encounter a plausible combination
    of parameter values not adequately covered by our tests or source code.

    Examples:

        We prepare eight zones with identical values for the control parameters |H1|,
        |TAb1|, and |TVs1|.  We only vary the inflow (|R|) and the initial state
        (|BW1|).  For the first and the second zone, |BW1| changes but remains
        permanently below |H1|.  Hence, all water leaving the storage leaves via
        percolation.  For the third and the fourth zone, |BW1| also changes but is
        permanently above |H1|.  Hence, there is a continuous generation of percolation
        and surface runoff.  For the fifth and sixth zone, |BW1| starts below and ends
        above |H1| and the other way round.  For the seventh and the eighth zone,
        inflow and outflow are balanced:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(8)
        >>> zonetype(FIELD)
        >>> h1(4.0)
        >>> tab1(1.0)
        >>> tvs1(2.0)
        >>> fluxes.r = 0.0, 2.0, 0.0, 2.0, 5.0, 0.1, 0.5, 2.5
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 1.561119, 1.956437, 0.246114, 0.181758, 0.0, 1.0)
        >>> fluxes.qvs1
        qvs1(0.442398, 0.672805, 1.780559, 1.978219, 1.007586, 1.086805, 0.5,
             1.5)
        >>> states.bw1
        bw1(1.557602, 3.327195, 5.658322, 7.065344, 5.7463, 3.831437, 2.0, 6.0)

        In the following examples, we keep the general configuration but set either
        |TAb1| or |TVs1| to |numpy.inf| or zero (you can replace |numpy.inf| with a
        high value and zero with a low value to confirm the correct "direction" of our
        handling of these special cases):

        >>> infinity = inf
        >>> zero = 0.0

        Setting |TAb1| to |numpy.inf| disables the surface runoff:

        >>> tab1(infinity)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.qvs1
        qvs1(0.442398, 0.672805, 1.990793, 2.221199, 1.018414, 1.117516, 0.5,
             1.615203)
        >>> states.bw1
        bw1(1.557602, 3.327195, 7.009207, 8.778801, 5.981586, 3.982484, 2.0,
            6.884797)

        Setting |TAb1| to zero enforces that all water exceeding |H1| becomes surface
        runoff immediately:

        >>> tab1(zero)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 5.0, 6.0, 2.115471, 1.0, 0.0, 3.5)
        >>> fluxes.qvs1
        qvs1(0.442398, 0.672805, 0.884797, 1.0, 0.884529, 0.896317, 0.5, 1.0)
        >>> states.bw1
        bw1(1.557602, 3.327195, 3.115203, 4.0, 4.0, 3.203683, 2.0, 4.0)

        Setting |TVs1| to |numpy.inf| disables the percolation:

        >>> tab1(1.0)
        >>> tvs1(infinity)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 1.967347, 2.393469, 0.408182, 0.414775, 0.0, 1.319592)
        >>> fluxes.qvs1
        qvs1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.bw1
        bw1(2.0, 4.0, 7.032653, 8.606531, 6.591818, 4.685225, 2.5, 7.180408)

        Setting |TAb1| to zero ensures that all availalbe water becomes percolation
        immediately:

        >>> tvs1(zero)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.qvs1
        qvs1(2.0, 4.0, 9.0, 11.0, 7.0, 5.1, 2.5, 8.5)
        >>> states.bw1
        bw1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        The following examples repeat the ones above for the edge case where the
        threshold value |H1| is zero:

        >>> h1(0.0)
        >>> tvs1(2.0)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.703511, 1.09883, 3.165801, 3.561119, 1.691807, 1.778544,
             0.802341, 2.604682)
        >>> fluxes.qvs1
        qvs1(0.351756, 0.549415, 1.5829, 1.780559, 0.845904, 0.889272, 0.40117,
             1.302341)
        >>> states.bw1
        bw1(0.944733, 2.351756, 4.251299, 5.658322, 4.462289, 2.432184,
            1.296489, 4.592977)

        >>> tab1(infinity)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.qvs1
        qvs1(0.442398, 0.672805, 1.990793, 2.221199, 1.018414, 1.117516, 0.5,
             1.615203)
        >>> states.bw1
        bw1(1.557602, 3.327195, 7.009207, 8.778801, 5.981586, 3.982484, 2.0,
            6.884797)

        >>> tab1(zero)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(2.0, 4.0, 9.0, 11.0, 7.0, 5.1, 2.5, 8.5)
        >>> fluxes.qvs1
        qvs1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.bw1
        bw1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        >>> tab1(1.0)
        >>> tvs1(infinity)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.786939, 1.213061, 3.541224, 3.967347, 1.852245, 1.988653,
             0.893469, 2.893469)
        >>> fluxes.qvs1
        qvs1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.bw1
        bw1(1.213061, 2.786939, 5.458776, 7.032653, 5.147755, 3.111347,
            1.606531, 5.606531)

        >>> tvs1(zero)
        >>> states.bw1 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.qvs1
        qvs1(2.0, 4.0, 9.0, 11.0, 7.0, 5.1, 2.5, 8.5)
        >>> states.bw1
        bw1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        |Calc_QAb1_QVs1_BW1_V1| processes forest and glacier zones like field zones but
        sets the values of |QAb1|, |QVs1|, and |BW1| to zero for internal lakes and
        sealed areas:

        >>> zonetype(FOREST, GLACIER, ILAKE, SEALED, FOREST, GLACIER, ILAKE, SEALED)
        >>> h1(4.0)
        >>> tab1(1.0)
        >>> tvs1(2.0)
        >>> fluxes.r = 2.0, 2.0, 2.0, 2.0, 2.5, 2.5, 2.5, 2.5
        >>> states.bw1 = 2.0, 2.0, 2.0, 2.0, 6.0, 6.0, 6.0, 6.0
        >>> model.calc_qab1_qvs1_bw1_v1()
        >>> fluxes.qab1
        qab1(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0)
        >>> fluxes.qvs1
        qvs1(0.672805, 0.672805, 0.0, 0.0, 1.5, 1.5, 0.0, 0.0)
        >>> states.bw1
        bw1(3.327195, 3.327195, 0.0, 0.0, 6.0, 6.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.H1,
        hland_control.TAb1,
        hland_control.TVs1,
    )
    REQUIREDSEQUENCES = (hland_fluxes.R,)
    UPDATEDSEQUENCES = (hland_states.BW1,)
    RESULTSEQUENCES = (hland_fluxes.QAb1, hland_fluxes.QVs1)
    SUBMETHODS = (Calc_QAb_QVs_BW_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            flu.qab1[k] = 0.0
            flu.qvs1[k] = 0.0
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                model.calc_qab_qvs_bw_v1(
                    k,
                    con.h1,
                    con.tab1,
                    con.tvs1,
                    sta.bw1,
                    flu.r,
                    flu.qab1,
                    flu.qvs1,
                    0.0,
                )
            else:
                sta.bw1[k] = 0.0


class Calc_QAb2_QVs2_BW2_V1(modeltools.Method):
    r"""Calculate the flow and the percolation from the interflow reservoir and update
    it.

    Basic equations:
      :math:`\frac{dBW2}{dt} = QVs1 - QAb2 - QVs2`

      :math:`QAb2 = \frac{max(BW2 - H2, 0)}{TAb2}`

      :math:`QVs2 = \frac{BW2}{TVs2}`

    Method |Calc_QAb2_QVs2_BW2_V1| is functionally identical with method
    |Calc_QAb1_QVs1_BW1_V1| and also relies on the "additional method"
    |Calc_QAb_QVs_BW_V1|.  Please see the documentation on method
    |Calc_QAb1_QVs1_BW1_V1|, which provides more information and exhaustive example
    calculations.

    Example:

        We only repeat the first and the last example of the documentation on method
        |Calc_QAb1_QVs1_BW1_V1| to verify that method |Calc_QAb2_QVs2_BW2_V1| calls
        method |Calc_QAb_QVs_BW_V1| correctly:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(8)
        >>> zonetype(FIELD)
        >>> h2(4.0)
        >>> tab2(1.0)
        >>> tvs2(2.0)
        >>> fluxes.qvs1 = 0.0, 2.0, 0.0, 2.0, 5.0, 0.1, 0.5, 2.5
        >>> states.bw2 = 2.0, 2.0, 9.0, 9.0, 2.0, 5.0, 2.0, 6.0
        >>> model.calc_qab2_qvs2_bw2_v1()
        >>> fluxes.qab2
        qab2(0.0, 0.0, 1.561119, 1.956437, 0.246114, 0.181758, 0.0, 1.0)
        >>> fluxes.qvs2
        qvs2(0.442398, 0.672805, 1.780559, 1.978219, 1.007586, 1.086805, 0.5,
             1.5)
        >>> states.bw2
        bw2(1.557602, 3.327195, 5.658322, 7.065344, 5.7463, 3.831437, 2.0, 6.0)

        |Calc_QAb2_QVs2_BW2_V1| processes forest and glacier zones like field zones but
        sets the values of |QAb2|, |QVs2|, and |BW2| to zero for internal lakes and
        sealed areas:

        >>> zonetype(FOREST, GLACIER, ILAKE, SEALED, FOREST, GLACIER, ILAKE, SEALED)
        >>> fluxes.qvs1 = 2.0, 2.0, 2.0, 2.0, 2.5, 2.5, 2.5, 2.5
        >>> states.bw2 = 2.0, 2.0, 2.0, 2.0, 6.0, 6.0, 6.0, 6.0
        >>> model.calc_qab2_qvs2_bw2_v1()
        >>> fluxes.qab2
        qab2(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0)
        >>> fluxes.qvs2
        qvs2(0.672805, 0.672805, 0.0, 0.0, 1.5, 1.5, 0.0, 0.0)
        >>> states.bw2
        bw2(3.327195, 3.327195, 0.0, 0.0, 6.0, 6.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.H2,
        hland_control.TAb2,
        hland_control.TVs2,
    )
    REQUIREDSEQUENCES = (hland_fluxes.QVs1,)
    UPDATEDSEQUENCES = (hland_states.BW2,)
    RESULTSEQUENCES = (hland_fluxes.QAb2, hland_fluxes.QVs2)
    SUBMETHODS = (Calc_QAb_QVs_BW_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            flu.qab2[k] = 0.0
            flu.qvs2[k] = 0.0
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                model.calc_qab_qvs_bw_v1(
                    k,
                    con.h2,
                    con.tab2,
                    con.tvs2,
                    sta.bw2,
                    flu.qvs1,
                    flu.qab2,
                    flu.qvs2,
                    0.0,
                )
            else:
                sta.bw2[k] = 0.0


class Calc_RS_RI_SUZ_V1(modeltools.Method):
    r"""Calculate the surface runoff and the interflow and remove them from the upper
    storage reservoir.

    Basic equation:
      :math:`RS = (SUZ - SGR) \cdot (1 - W0)`

      :math:`RI = SUZ \cdot (1 - W1)`

      :math:`\frac{SUZ}{dt} = -(RS + RI)`

    Examples:

        For internal lakes and sealed areas, method |Calc_RS_RI_SUZ_V1| always sets the
        values of |RS|, |RI|, and |SUZ| to zero:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep()
        >>> nmbzones(9)
        >>> zonetype(FIELD, FIELD, FIELD, FIELD, FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> sgr(10.0)
        >>> derived.w0 = 0.4
        >>> derived.w1 = 0.8
        >>> states.suz = 0.0, 5.0, 10.0, 15.0, 20.0, 20.0, 20.0, 20.0, 20.0
        >>> model.calc_rs_ri_suz_v1()
        >>> fluxes.rs
        rs(0.0, 0.0, 0.0, 3.0, 6.0, 6.0, 6.0, 0.0, 0.0)
        >>> fluxes.ri
        ri(0.0, 1.0, 2.0, 3.0, 4.0, 4.0, 4.0, 0.0, 0.0)
        >>> states.suz
        suz(0.0, 4.0, 8.0, 9.0, 10.0, 10.0, 10.0, 0.0, 0.0)

        Theoretically, the parallel calculation of |RS| and |RI| can result in negative
        values of |SUZ|.  The checks implemented for the parameter classes |K0| and
        |K1| should prevent this problem.  However, to be definitely on the safe side,
        method |Calc_RS_RI_SUZ_V1| also checks if the final state of |SUZ| is negative
        and, when necessary, resets it to zero and reduces |RS| and |RI| accordingly
        (with the same fraction):

        >>> derived.w0 = 0.1
        >>> derived.w1 = 0.2
        >>> states.suz = 0.0, 5.0, 10.0, 15.0, 20.0, 20.0, 20.0, 20.0, 20.0
        >>> model.calc_rs_ri_suz_v1()
        >>> fluxes.rs
        rs(0.0, 0.0, 0.0, 4.909091, 10.8, 10.8, 10.8, 0.0, 0.0)
        >>> fluxes.ri
        ri(0.0, 4.0, 8.0, 13.090909, 19.2, 19.2, 19.2, 0.0, 0.0)
        >>> states.suz
        suz(0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.SGR,
    )
    DERIVEDPARAMETERS = (hland_derived.W0, hland_derived.W1)
    UPDATEDSEQUENCES = (hland_states.SUZ,)
    RESULTSEQUENCES = (hland_fluxes.RS, hland_fluxes.RI)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                if sta.suz[k] > con.sgr[k]:
                    flu.rs[k] = (sta.suz[k] - con.sgr[k]) * (1.0 - der.w0[k])
                else:
                    flu.rs[k] = 0.0
                flu.ri[k] = sta.suz[k] * (1.0 - der.w1[k])
                sta.suz[k] -= flu.rs[k] + flu.ri[k]
                if sta.suz[k] < 0.0:
                    d_f = 1.0 - sta.suz[k] / (flu.rs[k] + flu.ri[k])
                    flu.rs[k] *= d_f
                    flu.ri[k] *= d_f
                    sta.suz[k] = 0.0
            else:
                sta.suz[k] = 0.0
                flu.rs[k] = 0.0
                flu.ri[k] = 0.0


class Calc_LZ_V1(modeltools.Method):
    r"""Add percolation from the upper zone layera and lake precipitation to the lower
    zone storage.

    Basic equation:
      .. math::
        \frac{dLZ}{dt} = \frac{RelUpperZoneArea}{RelLowerZoneArea} \cdot Perc +
        \sum_{k=1}^{NmbZones} \frac{RelZoneAreas_k}{RelLowerZoneArea} \cdot
        \begin{cases}
        Pc_k &|\ ZoneType_k = ILAKE
        \\
        0 &|\ ZoneType_k \neq ILAKE
        \end{cases}

    Examples:

        We define a subbasin with five zones of different land-use types and sizes:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 15.0, 25.0)
        >>> psi(1.0)

        To ensure the consistency of the values of the relevant derived parameters, we
        apply their |Parameter.update| methods:

        >>> derived.relzoneareas.update()
        >>> derived.relupperzonearea.update()
        >>> derived.rellowerzonearea.update()

        First, we set the precipitation intensity (|PC|) to 30 mm and the percolation
        intensity (|PERC|) to zero. Only the internal lake zone passes its value for
        |PC| directly to the lower zone layer.  The fraction between its size (15 km²)
        and the extent of the lower zone layer (75 km²) is 1/5.  Hence, the single
        zone's input of 30 mm increases the lower zone layer's water content by 6 mm:

        >>> fluxes.pc = 30.0
        >>> fluxes.perc = 0.0
        >>> states.lz = 10.0
        >>> model.calc_lz_v1()
        >>> states.lz
        lz(16.0)

        Second, we set |PC| to zero and the percolation intensity to 5 mm.  The
        fraction between the extents of the upper zone layer (60 km²) and the lower
        zone layer (75 km³) is 4/5. Hence, percolation released by the upper zone layer
        increases the content of the lower zone layer by 4 mm:

        >>> fluxes.pc = 0.0
        >>> fluxes.perc = 5.0
        >>> model.calc_lz_v1()
        >>> states.lz
        lz(20.0)

        In case the extent of the lower zone area is zero (which is possible for
        completely sealed subbasins only) method |Calc_LZ_V1| sets |LZ| to zero:

        >>> derived.rellowerzonearea(0.0)
        >>> model.calc_lz_v1()
        >>> states.lz
        lz(0.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (
        hland_derived.RelUpperZoneArea,
        hland_derived.RelLowerZoneArea,
        hland_derived.RelZoneAreas,
    )
    REQUIREDSEQUENCES = (hland_fluxes.Perc, hland_fluxes.PC)
    UPDATEDSEQUENCES = (hland_states.LZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if der.rellowerzonearea > 0.0:
            sta.lz += der.relupperzonearea / der.rellowerzonearea * flu.perc
            for k in range(con.nmbzones):
                if con.zonetype[k] == ILAKE:
                    sta.lz += der.relzoneareas[k] / der.rellowerzonearea * flu.pc[k]
        else:
            sta.lz = 0.0


class Calc_LZ_V2(modeltools.Method):
    r"""Add percolation from the interflow reservoir and lake precipitation to the
    lower zone storage.

    Basic equation:
      .. math::
        \frac{dLZ}{dt} =
        \sum_{k=1}^{NmbZones} \frac{RelZoneAreas_k}{RelLowerZoneArea} \cdot
        \begin{cases}
        QVs2_k &|\ ZoneType_k \in \{ FIELD, FOREST, GLACIER \}
        \\
        Pc_k &|\ ZoneType_k = ILAKE
        \\
        0 &|\ ZoneType_k = SEALED
        \end{cases}

    Example:

        The first three zones of type |FIELD|, |FOREST|, and |GLACIER| contribute via
        deep percolation to the lower zone reservoir.  For the fourth zone of type
        |ILAKE|, precipitation contributes directly to the lower zone storage.  The
        fifth zone of type |SEALED| does not contribute to the lower zone storage at
        all:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas = 0.24, 0.18, 0.12, 0.06, 0.4
        >>> derived.rellowerzonearea = 0.6
        >>> fluxes.qvs2 = 1.0, 2.0, 3.0, nan, nan
        >>> fluxes.pc = nan, nan, nan, 14.0, nan
        >>> states.lz = 5.0
        >>> model.calc_lz_v2()
        >>> states.lz
        lz(8.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    REQUIREDSEQUENCES = (hland_fluxes.QVs2, hland_fluxes.PC)
    UPDATEDSEQUENCES = (hland_states.LZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] == ILAKE:
                sta.lz += der.relzoneareas[k] / der.rellowerzonearea * flu.pc[k]
            elif con.zonetype[k] != SEALED:
                sta.lz += der.relzoneareas[k] / der.rellowerzonearea * flu.qvs2[k]


class Calc_GR1_V1(modeltools.Method):
    r"""Calculate the recharge to the fast response groundwater reservoir.

    Basic equation:
      :math:`GR1 = min \left(DP, \frac{SG1Max - SG1}{K2} \right)`

    Examples:

        For internal lakes and sealed areas, method |Calc_GR1_V1| always sets the values
        of |GR1| and |SG1| to zero:

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(9)
        >>> zonetype(FIELD, FIELD, FIELD, FIELD, FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> sg1max(10.0)
        >>> k2(10.0/24.0)
        >>> from hydpy import round_
        >>> round_(k2.values[0])
        10.0
        >>> fluxes.dp = 0.5
        >>> states.sg1 = 0.0, 5.0, 9.0, 9.9, 10.0, 5.0, 5.0, 5.0, 5.0
        >>> model.calc_gr1_v1()
        >>> fluxes.gr1
        gr1(0.5, 0.5, 0.1, 0.01, 0.0, 0.5, 0.5, 0.0, 0.0)

        For unreasonably low values of parameter |K2|, the sum of |SG1| and |GR1| could
        theoretically become larger than |SG1Max|.  We let method |Calc_GR1_V1| reduce
        |GR1| when necessary to ensure this does not happen:

        >>> k2.values = 0.5
        >>> states.sg1 = 0.0, 5.0, 9.0, 9.9, 10.0, 5.0, 5.0, 5.0, 5.0
        >>> model.calc_gr1_v1()
        >>> fluxes.gr1
        gr1(0.5, 0.5, 0.5, 0.1, 0.0, 0.5, 0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.SG1Max,
        hland_control.K2,
    )
    REQUIREDSEQUENCES = (hland_fluxes.DP,)
    UPDATEDSEQUENCES = (hland_states.SG1,)
    RESULTSEQUENCES = (hland_fluxes.GR1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                flu.gr1[k] = min(flu.dp[k], (con.sg1max[k] - sta.sg1[k]) / con.k2[k])
                flu.gr1[k] -= max(sta.sg1[k] + flu.gr1[k] - con.sg1max[k], 0.0)
            else:
                sta.sg1[k] = 0.0
                flu.gr1[k] = 0.0


class Calc_RG1_SG1_V1(modeltools.Method):
    r"""Calculate the discharge from the fast response groundwater reservoir and
    subtract it.

    Basic equation:
      :math:`SG1_{new} = W2 \cdot SG1_{old} + (1 - W2) \cdot K2 \cdot GR1`

      :math:`RG1 = SG1_{old} + GR1 - SG1_{new}`

    Example:

        For internal lakes and sealed areas, method |Calc_RG1_SG1_V1| always sets the
        values of |GR1| and |SG1| to zero:

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> zonetype(FIELD, FIELD, FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> k2(1.0/24, 10.0/24, 100.0/24, 100.0/24, 100.0/24, 100.0/24, 100.0/24)
        >>> from hydpy import round_
        >>> round_(k2.values)
        1.442695, 10.0, 100.0, 100.0, 100.0, 100.0, 100.0
        >>> derived.w2.update()
        >>> fluxes.gr1 = 2.0
        >>> states.sg1 = 5.0
        >>> model.calc_rg1_sg1_v1()
        >>> fluxes.rg1
        rg1(3.057305, 0.572561, 0.059718, 0.059718, 0.059718, 0.0, 0.0)
        >>> states.sg1
        sg1(3.942695, 6.427439, 6.940282, 6.940282, 6.940282, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        hland_control.NmbZones,
        hland_control.ZoneType,
        hland_control.K2,
    )
    DERIVEDPARAMETERS = (hland_derived.W2,)
    REQUIREDSEQUENCES = (hland_fluxes.GR1,)
    UPDATEDSEQUENCES = (hland_states.SG1,)
    RESULTSEQUENCES = (hland_fluxes.RG1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                d_sg1 = sta.sg1[k]
                sta.sg1[k] = (
                    der.w2[k] * d_sg1 + (1.0 - der.w2[k]) * con.k2[k] * flu.gr1[k]
                )
                flu.rg1[k] = d_sg1 + flu.gr1[k] - sta.sg1[k]
            else:
                sta.sg1[k] = 0.0
                flu.rg1[k] = 0.0


class Calc_GR2_GR3_V1(modeltools.Method):
    r"""Calculate the recharge of the first-order and the second-order slow response
    groundwater reservoir.

    Basic equations:
      .. math::
        GRT =
        \sum_{k=1}^{NmbZones} \frac{RelZoneAreas_k}{RelLowerZoneArea} \cdot
        \begin{cases}
        DP_k - GR1_k &|\ ZoneType_k \in \{ FIELD, FOREST, GLACIER \}
        \\
        Pc_k &|\ ZoneType_k = ILAKE
        \\
        0 &|\ ZoneType_k = SEALED
        \end{cases}

      :math:`GR2 = FSG \cdot GRT`

      :math:`GR3 = (1 - FSG) \cdot GRT`

    Example:

        Method |Calc_GR2_GR3_V1| aggregates the given input (term "GRT" in the given
        basic equations) divides it between |GR2| and |GR3|:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.24, 0.18, 0.12, 0.06, 0.4)
        >>> derived.rellowerzonearea(0.6)
        >>> fluxes.gr1 = 1.0, 2.0, 3.0, nan, nan
        >>> fluxes.dp = 4.0, 6.0, 8.0, nan, nan
        >>> fluxes.pc = nan, nan, nan, 11.0, nan
        >>> model.calc_gr2_gr3_v1()
        >>> fluxes.gr2
        gr2(4.0)
        >>> fluxes.gr3
        gr3(0.5)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    FIXEDPARAMETERS = (hland_fixed.FSG,)
    REQUIREDSEQUENCES = (hland_fluxes.PC, hland_fluxes.DP, hland_fluxes.GR1)
    RESULTSEQUENCES = (hland_fluxes.GR2, hland_fluxes.GR3)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.gr2 = 0.0
        flu.gr3 = 0.0
        for k in range(con.nmbzones):
            if con.zonetype[k] == SEALED:
                continue
            d_weight = der.relzoneareas[k] / der.rellowerzonearea
            if con.zonetype[k] == ILAKE:
                d_total = d_weight * flu.pc[k]
            else:
                d_total = d_weight * (flu.dp[k] - flu.gr1[k])
            flu.gr2 += fix.fsg * d_total
            flu.gr3 += (1.0 - fix.fsg) * d_total


class Calc_EL_SG2_SG3_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    lake evaporation and adjust the slow response groundwater reservoirs.

    Basic equations:
      :math:`\frac{dSG2_i}{dt} =
      -FSG \cdot \frac{RelZoneAreas_i}{RelLowerZoneArea} \cdot EL_i`

      :math:`\frac{dSG3_i}{dt} =
      -(1 - FSG) \cdot \frac{RelZoneAreas_i}{RelLowerZoneArea} \cdot EL_i`

    Examples:

        We build an example based on |evap_aet_hbv96| for calculating lake evaporation:

        >>> from hydpy.models.hland_96p import *
        >>> parameterstep("1h")
        >>> nmbzones(5)
        >>> zonetype(GLACIER, SEALED, FIELD, FOREST, ILAKE)
        >>> area(0.9)
        >>> zonearea(0.2, 0.1, 0.1, 0.1, 0.4)
        >>> psi(1.0)
        >>> zonez(5.0)
        >>> fc(50.0)
        >>> derived.relzoneareas.update()
        >>> derived.rellowerzonearea.update()
        >>> factors.tc = 10.0
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     temperaturethresholdice(0.0)

        |Calc_EL_SG2_SG3_AETModel_V1| uses the flux returned by the submodel to adjust
        |SG2| and |SG3|, considering the total extent of the groundwater-affected
        subarea and the fraction between the spatial extents of the first-order and the
        second-order slow response groundwater reservoir:

        >>> model.aetmodel.sequences.fluxes.potentialwaterevaporation = 2.25
        >>> states.sg2 = 3.0
        >>> states.sg3 = 0.3
        >>> model.calc_el_sg2_sg3_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.0, 2.25)
        >>> states.sg2
        sg2(2.0)
        >>> states.sg3
        sg3(0.175)

        Zones of type |ILAKE| are assumed to have an open water surface, so evaporation
        is always possible.  Therefore, applying |Calc_EL_SG2_SG3_AETModel_V1| can
        result in negative |SG2| and |SG3| values:

        >>> model.aetmodel.sequences.fluxes.potentialwaterevaporation = 4.5
        >>> states.sg2 = 1.0
        >>> states.sg3 = 0.1
        >>> model.calc_el_sg2_sg3_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.0, 4.5)
        >>> states.sg2
        sg2(-1.0)
        >>> states.sg3
        sg3(-0.15)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    FIXEDPARAMETERS = (hland_fixed.FSG,)
    UPDATEDSEQUENCES = (hland_states.SG2, hland_states.SG3)
    RESULTSEQUENCES = (hland_fluxes.EL,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_waterevaporation()
        for k in range(con.nmbzones):
            if con.zonetype[k] == ILAKE:
                flu.el[k] = submodel.get_waterevaporation(k)
                weight: float = der.relzoneareas[k] / der.rellowerzonearea
                sta.sg2 -= fix.fsg * weight * flu.el[k]
                sta.sg3 -= (1.0 - fix.fsg) * weight * flu.el[k]
            else:
                flu.el[k] = 0.0


class Calc_EL_SG2_SG3_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation, soil evapotranspiration, and open water evaporation, and
    adjust the related interception, soil water, and slow response groundwater storages
    accordingly."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_EL_SG2_SG3_AETModel_V1,)
    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    FIXEDPARAMETERS = (hland_fixed.FSG,)
    UPDATEDSEQUENCES = (hland_states.SG2, hland_states.SG3)
    RESULTSEQUENCES = (hland_fluxes.EL,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_el_sg2_sg3_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_RG2_SG2_V1(modeltools.Method):
    r"""Calculate the discharge from the first-order slow response groundwater
    reservoir and subtract it.

    Basic equation:
      :math:`SG2_{new} = W3 \cdot SG2_{old} + (1 - W3) \cdot K3 \cdot GR2`

      :math:`RG2 = SG2_{old} + GR2 - SG2_{new}`

    Examples:

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> k3(2.0/24)
        >>> from hydpy import round_
        >>> round_(k3.values)
        2.0
        >>> derived.w3.update()
        >>> fluxes.gr2 = 2.0

        For non-negative |SG2| values, method |Calc_RG2_SG2_V1| strictly follows the
        given base equation:

        >>> states.sg2 = 5.0
        >>> model.calc_rg2_sg2_v1()
        >>> fluxes.rg2
        rg2(2.393469)
        >>> states.sg2
        sg2(4.606531)

        For negative |SG2| values, it uses |RG2| to fill the groundwater storage
        so that no discharge occurs:

        >>> states.sg2 = -3.0
        >>> model.calc_rg2_sg2_v1()
        >>> fluxes.rg2
        rg2(0.0)
        >>> states.sg2
        sg2(-1.0)

        >>> states.sg2 = -2.0
        >>> model.calc_rg2_sg2_v1()
        >>> fluxes.rg2
        rg2(0.0)
        >>> states.sg2
        sg2(0.0)

        If the sum of |SG2| and |RG2| is positive, recharge first fills the deficit.
        In the remaining time, |Calc_RG2_SG2_V1| handles the remaining recharge as
        implied by the basic equations (with parameters |K3| and |W3| adapted to the
        remaining time interval):

        >>> states.sg2 = -1.0
        >>> model.calc_rg2_sg2_v1()
        >>> fluxes.rg2
        rg2(0.115203)
        >>> states.sg2
        sg2(0.884797)
    """

    CONTROLPARAMETERS = (hland_control.K3,)
    DERIVEDPARAMETERS = (hland_derived.W3,)
    REQUIREDSEQUENCES = (hland_fluxes.GR2,)
    UPDATEDSEQUENCES = (hland_states.SG2,)
    RESULTSEQUENCES = (hland_fluxes.RG2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        d_sg2 = sta.sg2
        d_gr2 = flu.gr2
        d_k3 = con.k3
        d_w3 = der.w3
        if d_sg2 < 0.0 < d_gr2:
            d_add = min(-sta.sg2, d_gr2)
            d_k3 *= d_gr2 / d_add
            d_w3 = modelutils.exp(-1.0 / d_k3)
            d_sg2 += d_add
            d_gr2 -= d_add
        if d_sg2 >= 0.0:
            sta.sg2 = d_w3 * d_sg2 + (1.0 - d_w3) * d_k3 * d_gr2
            flu.rg2 = d_sg2 + d_gr2 - sta.sg2
        else:
            sta.sg2 = d_sg2
            flu.rg2 = 0.0


class Calc_RG3_SG3_V1(modeltools.Method):
    r"""Calculate the discharge from the second-order slow response groundwater
    reservoir and subtract it.

    Basic equation:
      :math:`SG3_{new} = W4 \cdot SG3_{old} + (1 - W4) \cdot K4 \cdot GR3`

      :math:`RG3 = SG3_{old} + GR3 - SG3_{new}`

    Examples:

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> derived.k4(1.0/24)
        >>> from hydpy import round_
        >>> round_(derived.k4.values)
        1.0
        >>> derived.w4.update()
        >>> fluxes.gr3 = 2.0

        For non-negative |SG3| values, method |Calc_RG3_SG3_V1| strictly follows the
        given base equation:

        >>> states.sg3 = 5.0
        >>> model.calc_rg3_sg3_v1()
        >>> fluxes.rg3
        rg3(3.896362)
        >>> states.sg3
        sg3(3.103638)

        For negative |SG3| values, it uses |RG3| to fill the groundwater storage
        so that no discharge occurs:

        >>> states.sg3 = -3.0
        >>> model.calc_rg3_sg3_v1()
        >>> fluxes.rg3
        rg3(0.0)
        >>> states.sg3
        sg3(-1.0)

        >>> states.sg3 = -2.0
        >>> model.calc_rg3_sg3_v1()
        >>> fluxes.rg3
        rg3(0.0)
        >>> states.sg3
        sg3(0.0)

        If the sum of |SG3| and |RG3| is positive, recharge first fills the deficit.
        In the remaining time, |Calc_RG3_SG3_V1| handles the remaining recharge as
        implied by the basic equations (with parameters |hland_derived.K4| and |W4|
        adapted to the remaining time interval):

        >>> states.sg3 = -1.0
        >>> model.calc_rg3_sg3_v1()
        >>> fluxes.rg3
        rg3(0.213061)
        >>> states.sg3
        sg3(0.786939)
    """

    DERIVEDPARAMETERS = (hland_derived.K4, hland_derived.W4)
    REQUIREDSEQUENCES = (hland_fluxes.GR3,)
    UPDATEDSEQUENCES = (hland_states.SG3,)
    RESULTSEQUENCES = (hland_fluxes.RG3,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        d_sg3 = sta.sg3
        d_gr3 = flu.gr3
        d_k4 = der.k4
        d_w4 = der.w4
        if d_sg3 < 0.0 < d_gr3:
            d_add = min(-sta.sg3, d_gr3)
            d_k4 *= d_gr3 / d_add
            d_w4 = modelutils.exp(-1.0 / d_k4)
            d_sg3 += d_add
            d_gr3 -= d_add
        if d_sg3 >= 0.0:
            sta.sg3 = d_w4 * d_sg3 + (1.0 - d_w4) * d_k4 * d_gr3
            flu.rg3 = d_sg3 + d_gr3 - sta.sg3
        else:
            sta.sg3 = d_sg3
            flu.rg3 = 0.0


class Calc_EL_LZ_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    lake evaporation and adjust the lower zone's water content.

    Basic equation:
      :math:`\frac{dLZ_i}{dt} = -\frac{RelZoneAreas_i}{RelLowerZoneArea} \cdot EL_i`

    Examples:

        We build an example based on |evap_aet_hbv96| for calculating lake evaporation:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep("1h")
        >>> nmbzones(5)
        >>> zonetype(GLACIER, SEALED, FIELD, FOREST, ILAKE)
        >>> area(0.9)
        >>> zonearea(0.2, 0.1, 0.1, 0.1, 0.4)
        >>> psi(1.0)
        >>> zonez(5.0)
        >>> fc(50.0)
        >>> derived.relzoneareas.update()
        >>> derived.rellowerzonearea.update()
        >>> factors.tc = 10.0
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     temperaturethresholdice(0.0)

        |Calc_EL_LZ_AETModel_V1| uses the flux returned by the submodel to adjust |LZ|,
        considering the extent of the groundwater-affected subarea:

        >>> model.aetmodel.sequences.fluxes.potentialwaterevaporation = 2.0
        >>> states.lz = 3.0
        >>> model.calc_el_lz_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.0, 2.0)
        >>> states.lz
        lz(2.0)

        Zones of type |ILAKE| are assumed to have an open water surface, so evaporation
        is always possible.  Therefore, applying |Calc_EL_LZ_AETModel_V1| can result in
        negative |LZ| values:

        >>> model.aetmodel.sequences.fluxes.potentialwaterevaporation = 6.0
        >>> states.lz = 1.0
        >>> model.calc_el_lz_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.0, 6.0)
        >>> states.lz
        lz(-2.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    UPDATEDSEQUENCES = (hland_states.LZ,)
    RESULTSEQUENCES = (hland_fluxes.EL,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_waterevaporation()
        for k in range(con.nmbzones):
            if con.zonetype[k] == ILAKE:
                flu.el[k] = submodel.get_waterevaporation(k)
                sta.lz -= der.relzoneareas[k] / der.rellowerzonearea * flu.el[k]
            else:
                flu.el[k] = 0.0


class Calc_EL_LZ_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate lake
    evaporation and adjust the lower zone's water content."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_EL_LZ_AETModel_V1,)
    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    UPDATEDSEQUENCES = (hland_states.LZ,)
    RESULTSEQUENCES = (hland_fluxes.EL,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_el_lz_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_Q1_LZ_V1(modeltools.Method):
    r"""Calculate the slow response of the lower zone layer.

    Basic equations:
      .. math::
        Q1 =
        \begin{cases}
        K4 \cdot LZ^{1 + Gamma} &|\ LZ > 0
        \\
        0 &|\ LZ \leq 0
        \end{cases}

      :math:`\frac{dLZ}{dt} = -Q1`

    Examples:

        As long as the lower zone storage is negative or zero, there is no slow
        discharge response:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> k4(0.2)
        >>> gamma(0.0)
        >>> states.lz = -2.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.0)
        >>> states.lz
        lz(-2.0)

        >>> states.lz = 0.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.0)
        >>> states.lz
        lz(0.0)

        For storage values above zero the linear or nonlinear storage routing equation
        applies:

        >>> states.lz = 2.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.2)
        >>> states.lz
        lz(1.8)

        >>> gamma(1.0)
        >>> states.lz = 2.0
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.4)
        >>> states.lz
        lz(1.6)

        Note that the assumed length of the simulation step is half a day. Hence the
        effective value of the storage coefficient is not 0.2 but 0.1:

        >>> k4
        k4(0.2)
        >>> k4.value
        0.1
    """

    CONTROLPARAMETERS = (hland_control.K4, hland_control.Gamma)
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


class Calc_InRC_V1(modeltools.Method):
    r"""Calculate the input of the runoff concentration submodel.

    Basic equation:
      .. math::
        InRC = A_U \cdot Q0 + A_L \cdot Q1 +
        \sum_{k=1}^{N}  A_Z^k \cdot \begin{cases}
        R &|\ T_Z^k = S
        \\
        0 &|\ T_Z^k \neq S
        \end{cases}
        \\ \\
        N = NmbZones \\
        A_U = RelUpperZoneArea \\
        A_L = RelLowerZoneArea \\
        A_Z = RelZoneAreas  \\
        T_Z = ZoneType \\
        S = SEALED

    Example:

        We define a subbasin with five zones of different land-use types and sizes:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 15.0, 25.0)
        >>> psi(1.0)

        To ensure the consistency of the values of the relevant derived parameters, we
        apply their |Parameter.update| methods:

        >>> derived.relzoneareas.update()
        >>> derived.relupperzonearea.update()
        >>> derived.rellowerzonearea.update()

        The runoff concentration submodel receives freshly generated runoff (|R|)
        directly from the sealed zone (0.5 mm), direct runoff (|Q0|) indirectly from
        the field, forest, and glacier zones (0.6 mm) and base flow (|Q1|) indirectly
        from the field, forest, glacier and internal lake zones (3.0 mm):

        >>> fluxes.r = 2.0
        >>> fluxes.q0 = 1.0
        >>> fluxes.q1 = 4.0
        >>> model.calc_inrc_v1()
        >>> fluxes.inrc
        inrc(4.1)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (
        hland_derived.RelZoneAreas,
        hland_derived.RelUpperZoneArea,
        hland_derived.RelLowerZoneArea,
    )
    REQUIREDSEQUENCES = (hland_fluxes.R, hland_fluxes.Q0, hland_fluxes.Q1)
    RESULTSEQUENCES = (hland_fluxes.InRC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inrc = der.relupperzonearea * flu.q0 + der.rellowerzonearea * flu.q1
        for k in range(con.nmbzones):
            if con.zonetype[k] == SEALED:
                flu.inrc += der.relzoneareas[k] * flu.r[k]


class Calc_InRC_V2(modeltools.Method):
    r"""Calculate the input of the runoff concentration submodel.

    Basic equation:
      .. math::
        InRC = A_L \cdot (RG2 + RG3) +
        \sum_{k=1}^{N}
        \begin{cases}
        RS + RI + RG1 &|\ T_Z^k \in \{FI, FO, G \}
        \\
        R &|\ T_Z^k = S
        \\
        0 &|\ T_Z^k = L
        \end{cases}
        \\ \\
        N = NmbZones \\
        A_L = RelLowerZoneArea \\
        Z_T = ZoneType \\
        FI = FIELD \\
        FO = FOREST \\
        G = GLACIER \\
        S = SEALED \\
        L = ILAKE

    Example:

        Besides adding all components, method |Calc_InRC_V2| needs to aggregate the HRU
        level values of |RS|, |RI|, |RG1|, and |R| to the subbasin level:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.35, 0.25, 0.15, 0.05, 0.2)
        >>> derived.rellowerzonearea(0.8)
        >>> fluxes.rs = 0.1, 0.2, 0.3, nan, nan
        >>> fluxes.ri = 0.4, 0.6, 0.8, nan, nan
        >>> fluxes.rg1 = 1.1, 1.4, 1.7, nan, nan
        >>> fluxes.r = nan, nan, nan, nan, 2.0
        >>> fluxes.rg2 = 3.0
        >>> fluxes.rg3 = 4.0
        >>> model.calc_inrc_v2()
        >>> fluxes.inrc
        inrc(7.53)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLowerZoneArea)
    REQUIREDSEQUENCES = (
        hland_fluxes.R,
        hland_fluxes.RS,
        hland_fluxes.RI,
        hland_fluxes.RG1,
        hland_fluxes.RG2,
        hland_fluxes.RG3,
    )
    RESULTSEQUENCES = (hland_fluxes.InRC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inrc = der.rellowerzonearea * (flu.rg2 + flu.rg3)
        for k in range(con.nmbzones):
            if con.zonetype[k] in (FIELD, FOREST, GLACIER):
                flu.inrc += der.relzoneareas[k] * (flu.rs[k] + flu.ri[k] + flu.rg1[k])
            elif con.zonetype[k] == SEALED:
                flu.inrc += der.relzoneareas[k] * flu.r[k]


class Calc_InRC_V3(modeltools.Method):
    r"""Calculate the input of the runoff concentration submodel.

    Basic equation:
      .. math::
        InRC = \sum_{k=1}^{N} \frac{A_Z^k}{A_L} \cdot
        \begin{cases}
        QAb1 + QAb2 &|\ T_Z^k \in \{FI, FO, G \}
        \\
        R &|\ T_Z^k = S
        \\
        0 &|\ T_Z^k = L
        \end{cases}
        \\ \\
        N = NmbZones \\
        A_Z = RelZoneAreas \\
        A_L = RelLandArea \\
        T_Z = ZoneType \\
        FI = FIELD \\
        FO = FOREST \\
        G = GLACIER \\
        S = SEALED \\
        L = ILAKE

    Example:

        The runoff concentration submodel receives surface flow (|QAb1| and |QAb2|)
        from the first three zones of type |FIELD|, |FOREST|, and |GLACIER|, receives
        directly generated runoff from the fifth zone of type |SEALED|, and receives
        nothing from the fourth zone of type |ILAKE|:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas = 0.35, 0.25, 0.15, 0.2, 0.05
        >>> derived.rellandarea(0.8)
        >>> fluxes.qab1 = 1.0, 2.0, 3.0, nan, nan
        >>> fluxes.qab2 = 3.0, 6.0, 9.0, nan, nan
        >>> fluxes.r = nan, nan, nan, nan, 8.0
        >>> model.calc_inrc_v3()
        >>> fluxes.inrc
        inrc(7.0)
    """

    CONTROLPARAMETERS = (hland_control.NmbZones, hland_control.ZoneType)
    DERIVEDPARAMETERS = (hland_derived.RelZoneAreas, hland_derived.RelLandArea)
    REQUIREDSEQUENCES = (hland_fluxes.R, hland_fluxes.QAb1, hland_fluxes.QAb2)
    RESULTSEQUENCES = (hland_fluxes.InRC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inrc = 0.0
        for k in range(con.nmbzones):
            if con.zonetype[k] == ILAKE:
                continue
            d_weight = der.relzoneareas[k] / der.rellandarea
            if con.zonetype[k] == SEALED:
                flu.inrc += d_weight * flu.r[k]
            else:
                flu.inrc += d_weight * (flu.qab1[k] + flu.qab2[k])


class Calc_OutRC_RConcModel_V1(modeltools.Method):
    """Let a submodel that follows the |RConcModel_V1| submodel interface calculate
    runoff concentration."""

    REQUIREDSEQUENCES = (hland_fluxes.InRC,)
    RESULTSEQUENCES = (hland_fluxes.OutRC,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: rconcinterfaces.RConcModel_V1
    ) -> None:
        flu = model.sequences.fluxes.fastaccess
        submodel.set_inflow(flu.inrc)
        submodel.determine_outflow()
        flu.outrc = submodel.get_outflow()


class Calc_OutRC_V1(modeltools.Method):
    """If the model has a submodel that follows the |RConcModel_V1| submodel interface,
    calculate runoff concentration. If not, set the output equal to the input.

    Examples:

        A model without a submodel for runoff concentration directs the input directly
        to the output:

        >>> from hydpy.models.hland_96 import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> fluxes.inrc = 1.0
        >>> model.calc_outrc_v1()
        >>> fluxes.outrc
        outrc(1.0)

        If a submodel for runoff concentration is added (in this case, a unit
        hydrograph with three ordinates), the output for the first time step
        corresponds to the portion of the input specified by the first ordinate (since
        the initial conditions of the logging sequence |rconc_logs.QUH| were set to
        zero, and thus no additional runoff portions from previous time steps are
        included):

        >>> with model.add_rconcmodel_v1("rconc_uh"):
        ...     uh([0.3,0.4,0.3])
        ...     logs.quh = 0.0, 0.0, 0.0
        >>> model.calc_outrc_v1()
        >>> fluxes.outrc
        outrc(0.3)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_OutRC_RConcModel_V1,)
    REQUIREDSEQUENCES = (hland_fluxes.InRC,)
    RESULTSEQUENCES = (hland_fluxes.OutRC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel is None:
            flu.outrc = flu.inrc
        elif model.rconcmodel_typeid == 1:
            model.calc_outrc_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel)
            )


class Calc_RT_V1(modeltools.Method):
    r"""Calculate the total discharge in mm.

    Basic equation:
        :math:`RT = OutRC`

    Examples:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> fluxes.outrc = 3.0
        >>> model.calc_rt_v1()
        >>> fluxes.rt
        rt(3.0)
    """

    REQUIREDSEQUENCES = (hland_fluxes.OutRC,)
    RESULTSEQUENCES = (hland_fluxes.RT,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.rt = flu.outrc


class Calc_RT_V2(modeltools.Method):
    r"""Calculate the total discharge in mm.

    Basic equation:
        :math:`RT = RelUpperZoneArea \cdot OutRC + RelLowerZoneArea \cdot Q1`

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> derived.rellandarea(0.8)
        >>> derived.rellowerzonearea(0.6)
        >>> fluxes.outrc = 2.5
        >>> fluxes.q1 = 1.0
        >>> model.calc_rt_v2()
        >>> fluxes.rt
        rt(2.6)
    """

    DERIVEDPARAMETERS = (hland_derived.RelLandArea, hland_derived.RelLowerZoneArea)
    REQUIREDSEQUENCES = (hland_fluxes.OutRC, hland_fluxes.Q1)
    RESULTSEQUENCES = (hland_fluxes.RT,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.rt = der.rellandarea * flu.outrc + der.rellowerzonearea * flu.q1


class Calc_QT_V1(modeltools.Method):
    r"""Calculate the total discharge in m³/s.

    Basic equation:
        :math:`QT = QFactor \cdot RT`

    Example:

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> derived.qfactor(0.5)
        >>> fluxes.rt = 2.0
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(1.0)
    """

    DERIVEDPARAMETERS = (hland_derived.QFactor,)
    REQUIREDSEQUENCES = (hland_fluxes.RT,)
    RESULTSEQUENCES = (hland_fluxes.QT,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qt = der.qfactor * flu.rt


class Pass_Q_V1(modeltools.Method):
    r"""Update the outlet link sequence."""

    REQUIREDSEQUENCES = (hland_fluxes.QT,)
    RESULTSEQUENCES = (hland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.qt


class Get_Temperature_V1(modeltools.Method):
    """Get the selected zone's current temperature.

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> factors.tc = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_temperature_v1(0))
        2.0
        >>> round_(model.get_temperature_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (hland_factors.TC,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.tc[s]


class Get_MeanTemperature_V1(modeltools.Method):
    """Get the basin's current mean temperature.

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> inputs.t = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_meantemperature_v1())
        2.0
    """

    REQUIREDSEQUENCES = (hland_inputs.T,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.t


class Get_Precipitation_V1(modeltools.Method):
    """Get the current precipitation from the selected zone.

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> fluxes.pc = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_precipitation_v1(0))
        2.0
        >>> round_(model.get_precipitation_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (hland_fluxes.PC,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.pc[s]


class Get_InterceptedWater_V1(modeltools.Method):
    """Get the selected zone's current amount of intercepted water.

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> states.ic = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_interceptedwater_v1(0))
        2.0
        >>> round_(model.get_interceptedwater_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (hland_states.Ic,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        return sta.ic[k]


class Get_SoilWater_V1(modeltools.Method):
    """Get the selected zone's current soil water content.

    Example:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> states.sm = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_soilwater_v1(0))
        2.0
        >>> round_(model.get_soilwater_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (hland_states.SM,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        return sta.sm[k]


class Get_SnowCover_V1(modeltools.Method):
    """Get the selected zone's current snow cover degree.

    Example:

        Each snow class with a non-zero amount of snow counts as completely covered:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> sclass(2)
        >>> states.sp = [[0.0, 0.0, 1.0], [0.0, 1.0, 1.0]]
        >>> from hydpy import round_
        >>> round_(model.get_snowcover_v1(0))
        0.0
        >>> round_(model.get_snowcover_v1(1))
        0.5
        >>> round_(model.get_snowcover_v1(2))
        1.0
    """

    CONTROLPARAMETERS = (hland_control.SClass,)
    REQUIREDSEQUENCES = (hland_states.SP,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        snowcovered: float = 0.0
        for c in range(con.sclass):
            snowcovered += sta.sp[c, k] > 0.0
        return snowcovered / con.sclass


class Model(modeltools.AdHocModel):
    """|hland.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="H")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_TC_V1,
        Calc_FracRain_V1,
        Calc_RFC_SFC_V1,
        Calc_PC_V1,
        Calc_TF_Ic_V1,
        Calc_EI_Ic_V1,
        Calc_SP_WC_V1,
        Calc_SPL_WCL_SP_WC_V1,
        Calc_SPG_WCG_SP_WC_V1,
        Calc_CFAct_V1,
        Calc_Melt_SP_WC_V1,
        Calc_Refr_SP_WC_V1,
        Calc_In_WC_V1,
        Calc_SWE_V1,
        Calc_SR_V1,
        Calc_GAct_V1,
        Calc_GlMelt_In_V1,
        Calc_R_SM_V1,
        Calc_CF_SM_V1,
        Calc_EA_SM_V1,
        Calc_InUZ_V1,
        Calc_SUZ_V1,
        Calc_ContriArea_V1,
        Calc_Q0_Perc_UZ_V1,
        Calc_DP_SUZ_V1,
        Calc_QAb1_QVs1_BW1_V1,
        Calc_QAb2_QVs2_BW2_V1,
        Calc_RS_RI_SUZ_V1,
        Calc_LZ_V1,
        Calc_LZ_V2,
        Calc_GR1_V1,
        Calc_RG1_SG1_V1,
        Calc_GR2_GR3_V1,
        Calc_RG2_SG2_V1,
        Calc_RG3_SG3_V1,
        Calc_EL_SG2_SG3_V1,
        Calc_EL_LZ_V1,
        Calc_Q1_LZ_V1,
        Calc_InRC_V1,
        Calc_InRC_V3,
        Calc_OutRC_V1,
        Calc_InRC_V2,
        Calc_RT_V1,
        Calc_RT_V2,
        Calc_QT_V1,
    )
    INTERFACE_METHODS = (
        Get_Temperature_V1,
        Get_MeanTemperature_V1,
        Get_Precipitation_V1,
        Get_InterceptedWater_V1,
        Get_SoilWater_V1,
        Get_SnowCover_V1,
    )
    ADD_METHODS = (
        Calc_EI_Ic_AETModel_V1,
        Calc_EA_SM_AETModel_V1,
        Calc_EL_LZ_AETModel_V1,
        Calc_EL_SG2_SG3_AETModel_V1,
        Calc_QAb_QVs_BW_V1,
        Calc_OutRC_RConcModel_V1,
    )
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1, rconcinterfaces.RConcModel_V1)
    SUBMODELS = ()

    aetmodel = modeltools.SubmodelProperty(aetinterfaces.AETModel_V1)
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    rconcmodel = modeltools.SubmodelProperty(rconcinterfaces.RConcModel_V1)
    rconcmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_typeid = modeltools.SubmodelTypeIDProperty()


class Main_AETModel_V1(modeltools.AdHocModel):
    """Base class for |hland.DOCNAME.long| models that use submodels that comply with
    the |AETModel_V1| interface."""

    aetmodel: modeltools.SubmodelProperty
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "aetmodel",
        aetinterfaces.AETModel_V1,
        aetinterfaces.AETModel_V1.prepare_nmbzones,
        aetinterfaces.AETModel_V1.prepare_subareas,
        aetinterfaces.AETModel_V1.prepare_elevations,
        aetinterfaces.AETModel_V1.prepare_maxsoilwater,
        aetinterfaces.AETModel_V1.prepare_water,
        aetinterfaces.AETModel_V1.prepare_interception,
        aetinterfaces.AETModel_V1.prepare_soil,
        aetinterfaces.AETModel_V1.prepare_plant,
        landtype_constants=hland_constants.CONSTANTS,
        landtype_refindices=hland_control.ZoneType,
        refweights=hland_control.ZoneArea,
    )
    def add_aetmodel_v1(
        self,
        aetmodel: aetinterfaces.AETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given submodel that follows the |AETModel_V1| interface and
        is responsible for calculating the different kinds of actual
        evapotranspiration.

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> area(10.0)
        >>> zonetype(FIELD, FOREST, ILAKE, GLACIER, SEALED)
        >>> zonearea(2.0)
        >>> zonez(3.0)
        >>> fc(200.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     nmbhru
        ...     water
        ...     interception
        ...     soil
        ...     excessreduction(field=1.0, forest=0.5, default=nan)
        ...     for method, arguments in model.preparemethod2arguments.items():
        ...         print(method, arguments[0][0], sep=": ")
        nmbhru(5)
        water(field=False, forest=False, glacier=False, ilake=True,
              sealed=False)
        interception(field=True, forest=True, glacier=False, ilake=False,
                     sealed=True)
        soil(field=True, forest=True, glacier=False, ilake=False, sealed=False)
        prepare_nmbzones: 5
        prepare_zonetypes: [1 2 4 3 5]
        prepare_subareas: [2. 2. 2. 2. 2.]
        prepare_elevations: [300. 300. 300. 300. 300.]
        prepare_maxsoilwater: [200. 200. 200. 200. 200.]
        prepare_water: [False False  True False False]
        prepare_interception: [ True  True False False  True]
        prepare_plant: [ True  True False False False]
        prepare_soil: [ True  True False False False]

        >>> ered = model.aetmodel.parameters.control.excessreduction
        >>> ered
        excessreduction(field=1.0, forest=0.5)
        >>> zonetype(FOREST, FIELD, ILAKE, GLACIER, SEALED)
        >>> ered
        excessreduction(field=0.5, forest=1.0)
        >>> from hydpy import round_
        >>> round_(ered.average_values())
        0.75
        """
        control = self.parameters.control
        nmbzones = control.nmbzones.value
        zonetype = control.zonetype.values

        aetmodel.prepare_nmbzones(nmbzones)
        aetmodel.prepare_zonetypes(zonetype)
        aetmodel.prepare_subareas(control.zonearea.value)
        aetmodel.prepare_elevations(100.0 * control.zonez.values)
        aetmodel.prepare_maxsoilwater(control.fc.values)
        sel = numpy.full(nmbzones, False, dtype=config.NP_BOOL)
        sel[zonetype == ILAKE] = True
        aetmodel.prepare_water(sel)
        sel = ~sel
        sel[zonetype == GLACIER] = False
        aetmodel.prepare_interception(sel)
        sel[zonetype == SEALED] = False
        aetmodel.prepare_plant(sel)
        aetmodel.prepare_soil(sel)


class Main_RConcModel_V1(modeltools.AdHocModel):
    """Base class for |hland.DOCNAME.long| models that use submodels that comply with
    the |RConcModel_V1| interface."""

    rconcmodel: modeltools.SubmodelProperty
    rconcmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel("rconcmodel", rconcinterfaces.RConcModel_V1)
    def add_rconcmodel_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating the runoff concentration.

        >>> from hydpy.models.hland_96 import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_v1("rconc_uh"):
        ...     uh([0.3, 0.5, 0.2])
        ...     logs.quh.shape = 3
        ...     logs.quh = 1.0, 3.0, 0.0
        >>> model.sequences.fluxes.inrc = 0.0
        >>> model.calc_outrc_v1()
        >>> fluxes.outrc
        outrc(1.0)
        """

    def _get_rconcmodel_waterbalance(
        self, initial_conditions: ConditionsModel
    ) -> float:
        r"""Get the water balance of the rconc submodel if used."""
        if self.rconcmodel:
            rconcmodel_conditions = initial_conditions["model.rconcmodel"]
            return self.rconcmodel.get_waterbalance(rconcmodel_conditions)
        return 0.0


class Sub_TempModel_V1(modeltools.AdHocModel, tempinterfaces.TempModel_V1):
    """Base class for |hland.DOCNAME.long| models that comply with the |TempModel_V1|
    submodel interface."""


class Sub_PrecipModel_V1(modeltools.AdHocModel, precipinterfaces.PrecipModel_V1):
    """Base class for |hland.DOCNAME.long| models that comply with the |PrecipModel_V1|
    submodel interface."""


class Sub_IntercModel_V1(modeltools.AdHocModel, stateinterfaces.IntercModel_V1):
    """Base class for |hland.DOCNAME.long| models that comply with the |IntercModel_V1|
    submodel interface."""


class Sub_SoilWaterModel_V1(modeltools.AdHocModel, stateinterfaces.SoilWaterModel_V1):
    """Base class for |hland.DOCNAME.long| models that comply with the
    |SoilWaterModel_V1| submodel interface."""


class Sub_SnowCoverModel_V1(modeltools.AdHocModel, stateinterfaces.SnowCoverModel_V1):
    """Base class for |hland.DOCNAME.long| models that comply with the
    |SnowCoverModel_V1| submodel interface."""
