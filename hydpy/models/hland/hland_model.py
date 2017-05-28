# -*- coding: utf-8 -*-

# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.cythons import modelutils
# ...model specifc
from hydpy.models.hland.hland_constants import FIELD, FOREST, GLACIER, ILAKE

def calc_tc_v1(self):
    """Adjust the measured air temperature to the altitude of the
    individual zones.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.TCAlt`
      :class:`~hydpy.models.hland.hland_control.ZoneZ`
      :class:`~hydpy.models.hland.hland_control.ZRelT`

    Required input sequence:
      :class:`~hydpy.models.hland.hland_inputs.T`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.TC`

    Basic equation:
      :math:`TC = T - TCAlt \\cdot (ZoneZ-ZRelT)`

    Examples:
        Prepare two zones, the first one lying at the reference
        height and the second one 200 meters above:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> _ = nmbzones(2), zrelt(2.), zonez(2., 4.)

        Applying the usual temperature lapse rate of 0.6°C/100m does
        not affect the temperature of the first zone but reduces the
        temperature of the second zone by 1.2°C:

        >>> tcalt(.6)
        >>> inputs.t = 5.
        >>> model.calc_tc_v1()
        >>> fluxes.tc
        tc(5.0, 3.8)
    """
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmbzones):
        flu.tc[k] = inp.t-con.tcalt[k]*(con.zonez[k]-con.zrelt)

def calc_tmean_v1(self):
    """Calculate the areal mean temperature of the subbasin.

    Required derived parameter:
      :class:`~hydpy.models.hland.hland_derived.RelZoneArea`

    Required flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.TC`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.TMean`

    Examples:
        Prepare sized zones, the first one beeing twice as large
        as the second one:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(2)
        >>> derived.relzonearea(2./3., 1./3.)

        With temperature values of 5°C and 8°C  of the respective zones,
        the mean temperature is 6°C:

        >>> fluxes.tc = 5., 8.
        >>> model.calc_tmean_v1()
        >>> fluxes.tmean
        tmean(6.0)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.tmean = 0.
    for k in range(con.nmbzones):
        flu.tmean += der.relzonearea[k]*flu.tc[k]


def calc_fracrain_v1(self):
    """Determine the temperature dependend fraction of (liquid) rainfall
    and (total) precipitation.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.TT`,
      :class:`~hydpy.models.hland.hland_control.TTInt`

    Required flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.TC`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.FracRain`

    Basic equation:
      :math:`FracRain = \\frac{TC-(TT-\\frac{TTInt}{2})}{TTInt}`

    Restriction:
      :math:`0 \\leq FracRain \\leq 1`


    Examles:  The threshold temperature of five
    zones is 0°C and the corresponding temperature intervall of mixed
    precipitation 2°C:

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(7)
    >>> tt(0.)
    >>> ttint(2.)

    The fraction of rainfall is zero below -1°C, is one above 1°C and
    increases linearly in between:

    >>> fluxes.tc = -10., -1., -.5, 0., .5, 1., 10.
    >>> model.calc_fracrain_v1()
    >>> fluxes.fracrain
    fracrain(0.0, 0.0, 0.25, 0.5, 0.75, 1.0, 1.0)

    Note the special case of a zero temperature intervall.  With a
    actual temperature beeing equal to the threshold temperature, the
    rainfall fraction is one:

    >>> ttint(0.)
    >>> model.calc_fracrain_v1()
    >>> fluxes.fracrain
    fracrain(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmbzones):
        if flu.tc[k] >= (con.tt[k]+con.ttint[k]/2.):
            flu.fracrain[k] = 1.
        elif flu.tc[k] <= (con.tt[k]-con.ttint[k]/2.):
            flu.fracrain[k] = 0.
        else:
            flu.fracrain[k] = ((flu.tc[k]-(con.tt[k]-con.ttint[k]/2.)) /
                               con.ttint[k])

def calc_rfc_sfc_v1(self):
    """Calculate the corrected fractions rainfall/snowfall and total
    precipitation.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.RfCF`
      :class:`~hydpy.models.hland.hland_control.SfCF`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.RfC`
      :class:`~hydpy.models.hland.hland_fluxes.SfC`

    Basic equations:
      :math:`RfC = RfCF \\cdot FracRain` \n
      :math:`SfC = SfCF \\cdot (1 - FracRain)`

    Examples:
        Assume five zones with different temperatures and hence
        different fractions of rainfall and total precipitation:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(5)
        >>> fluxes.fracrain = 0., .25, .5, .75, 1.

        With no rainfall and no snowfall correction (implied by the
        respective factors beeing one), the corrected fraction related
        to rainfall is identical with the original fraction and the
        corrected fraction related to snowfall behaves opposite:

        >>> rfcf(1.)
        >>> sfcf(1.)
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
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmbzones):
        flu.rfc[k] = flu.fracrain[k]*con.rfcf[k]
        flu.sfc[k] = (1.-flu.fracrain[k])*con.sfcf[k]

def calc_pc_v1(self):
    """Apply the precipitation correction factors and adjust precipitation
    to the altitude of the individual zones.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.PCorr`
      :class:`~hydpy.models.hland.hland_control.PCAlt`
      :class:`~hydpy.models.hland.hland_control.ZoneZ`
      :class:`~hydpy.models.hland.hland_control.ZRelP`

    Required input sequence:
      :class:`~hydpy.models.hland.hland_inputs.P`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.RfC`
      :class:`~hydpy.models.hland.hland_fluxes.SfC`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.PC`

    Examples:
        Five zones are at an elevation of 200 m.  A precipitation value
        of 5 mm has been measured at a gauge at an elevation of 300 m:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(5)
        >>> zrelp(2.)
        >>> zonez(3.)
        >>> inputs.p = 5.

        Basic equation:
          :math:`PC = P \\cdot PCorr
          \\cdot (1+PCAlt \\cdot (ZoneZ-ZRelP))
          \\cdot (RfC + SfC)`

        The first four zones illustrate the individual precipitation
        corrections due to the general precipitation correction factor
        (first zone), the altitude correction (second zone), the rainfall
        related correction factor (third zone), and the snowfall related
        correction factor (fourth zone):

        >>> pcorr(1.3, 1.0, 1.0, 1.0, 1.3)
        >>> pcalt(0.0, 0.1, 0.0, 0.0, 0.1)
        >>> fluxes.rfc = 0.5, 0.5, 0.4, 0.5, 0.4
        >>> fluxes.sfc = 0.5, 0.5, 0.5, 0.7, 0.7
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(6.5, 5.5, 4.5, 6.0, 7.865)

        The fifth zone illustrates the interaction between all corrections
        --- note that each correction (except the first one) is based the
        corrected precipitation value determined beforehand.
    """
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmbzones):
        flu.pc[k] = inp.p*con.pcorr[k]
        flu.pc[k] *= 1.+con.pcalt[k]*(con.zonez[k]-con.zrelp)
        flu.pc[k] *= flu.rfc[k]+flu.sfc[k]

def calc_ep_v1(self):
    """Adjust potential norm evaporation to the actual temperature.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ETF`

    Required input sequence:
      :class:`~hydpy.models.hland.hland_inputs.EPN`
      :class:`~hydpy.models.hland.hland_inputs.TN`

    Required flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.TMean`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.EP`

    Basic equation:
      :math:`EP = EPN \\cdot (1 + ETF \\cdot (TMean - TN))`

    Restriction:
      :math:`0 \leq EP \leq 2 \\cdot EPN`


    Examples:
        Assume four zones with different values of the temperature
        related factor for the adjustment of evaporation (the
        negative value of the first zone is not meaningful, but used
        for illustration purporses):

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(4)
        >>> etf(-0.5, 0.0, 0.1, 0.5)
        >>> inputs.tn = 20.
        >>> inputs.epn = 2.

        With mean temperature equal to norm temperature, actual
        (uncorrected) evaporation is equal to norm evaporation:

        >>> fluxes.tmean = 20.
        >>> model.calc_ep_v1()
        >>> fluxes.ep
        ep(2.0, 2.0, 2.0, 2.0)

        With mean temperature 5°C higher than norm temperature, potential
        evaporation is increased by 1 mm for the third zone, which
        possesses a very common adjustment factor.  For the first zone,
        potential evaporation is 0 mm (which is the smallest value
        allowed), and for the fourth zone it is the double value of the
        norm evaporation (which is the largest value allowed):

        >>> fluxes.tmean  = 25.
        >>> model.calc_ep_v1()
        >>> fluxes.ep
        ep(0.0, 2.0, 3.0, 4.0)
    """
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmbzones):
        flu.ep[k] = inp.epn*(1.+con.etf[k]*(flu.tmean-inp.tn))
        flu.ep[k] = min(max(flu.ep[k], 0.), 2.*inp.epn)

def calc_epc_v1(self):
    """Apply the evaporation correction factors and adjust evaporation
    to the altitude of the individual zones.

    Calculate the areal mean of (uncorrected) potential evaporation
    for the subbasin, adjust it to the individual zones in accordance
    with their heights and perform some corrections, among which one
    depends on the actual precipitation.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ECorr`
      :class:`~hydpy.models.hland.hland_control.ECAlt`
      :class:`~hydpy.models.hland.hland_control.ZoneZ`
      :class:`~hydpy.models.hland.hland_control.ZRelE`
      :class:`~hydpy.models.hland.hland_control.EPF`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.EP`
      :class:`~hydpy.models.hland.hland_fluxes.PC`

    Calculated flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.EPC`

    Basic equation:
      :math:`EPC = EP \\cdot ECorr
      \\cdot (1+ECAlt \\cdot (ZoneZ-ZRelE))
      \\cdot exp(-EPF \\cdot PC)`


    Examples:
        Four zones are at an elevation of 200 m.  A (uncorrected)
        potential evaporation value of 2 mm and a (corrected) precipitation
        value of 5 mm have been determined for each zone beforehand:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(4)
        >>> zrele(2.)
        >>> zonez(3.)
        >>> fluxes.ep = 2.
        >>> fluxes.pc = 5.

        The first three zones  illustrate the individual evaporation
        corrections due to the general evaporation correction factor
        (first zone), the altitude correction (second zone), the
        precipitation related correction (third zone):

        >>> ecorr(1.3, 1.0, 1.0, 1.3)
        >>> ecalt(0.0, 0.1, 0.0, 0.1)
        >>> epf(0.0, 0.0, -numpy.log(.7)/10., -numpy.log(.7)/10.)
        >>> model.calc_epc_v1()
        >>> fluxes.epc
        epc(2.6, 1.8, 1.4, 1.638)

        The fourth zone illustrates the interaction between all corrections
        --- note that each correction (except the first one) is based the
        corrected evaporation value determined beforehand.
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmbzones):
        flu.epc[k] = (flu.ep[k]*con.ecorr[k] *
                      (1. - con.ecalt[k]*(con.zonez[k]-con.zrele)))
        flu.epc[k] *= modelutils.exp(-con.epf[k]*flu.pc[k])

def calc_tf_ic_v1(self):
    """Calculate throughfall and update the interception storage
    accordingly.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.IcMax`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.PC`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.TF`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.Ic`

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
        >>> parameterstep('1d')
        >>> nmbzones(6)
        >>> zonetype(GLACIER, ILAKE, FIELD, FOREST, FIELD, FIELD)
        >>> icmax(2.)
        >>> fluxes.pc = .5
        >>> states.ic = 0., 0., 0., 0., 1., 2.
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

        >>> fluxes.pc = 0.
        >>> states.ic = 0., 0., 0., 0., 1., 2.
        >>> model.calc_tf_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
        >>> fluxes.tf
        tf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        A high precipitation example:

        >>> fluxes.pc = 5.
        >>> states.ic = 0., 0., 0., 0., 1., 2.
        >>> model.calc_tf_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 2.0, 2.0, 2.0, 2.0)
        >>> fluxes.tf
        tf(5.0, 5.0, 3.0, 3.0, 4.0, 5.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
            flu.tf[k] = max(flu.pc[k]-(con.icmax[k]-sta.ic[k]), 0.)
            sta.ic[k] += flu.pc[k]-flu.tf[k]
        else:
            flu.tf[k] = flu.pc[k]
            sta.ic[k] = 0.

def calc_ei_ic_v1(self):
    """Calculate interception evaporation and update the interception
    storage accordingly.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.EPC`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.EI`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.Ic`

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
        >>> parameterstep('1d')
        >>> nmbzones(6)
        >>> zonetype(GLACIER, ILAKE, FIELD, FOREST, FIELD, FIELD)
        >>> fluxes.epc = .5
        >>> states.ic = 0., 0., 0., 0., 1., 2.
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

        >>> fluxes.epc = 0.
        >>> states.ic = 0., 0., 0., 0., 1., 2.
        >>> model.calc_ei_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
        >>> fluxes.ei
        ei(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        A high evaporation example:

        >>> fluxes.epc = 5.
        >>> states.ic = 0., 0., 0., 0., 1., 2.
        >>> model.calc_ei_ic_v1()
        >>> states.ic
        ic(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.ei
        ei(0.0, 0.0, 0.0, 0.0, 1.0, 2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
            flu.ei[k] = min(flu.epc[k], sta.ic[k])
            sta.ic[k] -= flu.ei[k]
        else:
            flu.ei[k] = 0.
            sta.ic[k] = 0.


def calc_sp_wc_v1(self):
    """Add throughfall to the snow layer.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.TF`
      :class:`~hydpy.models.hland.hland_fluxes.RfC`
      :class:`~hydpy.models.hland.hland_fluxes.SfC`

    Updated state sequences:
      :class:`~hydpy.models.hland.hland_states.WC`
      :class:`~hydpy.models.hland.hland_states.SP`

    Basic equations:
      :math:`\\frac{dSP}{dt} = TF \\cdot \\frac{SfC}{SfC+RfC}` \n
      :math:`\\frac{dWC}{dt} = TF \\cdot \\frac{RfC}{SfC+RfC}`

    Exemples:
        Consider the following setting, in which eight zones of
        different type receive a throughfall of 10mm:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(8)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD, FIELD, FIELD)
        >>> fluxes.tf = 10.
        >>> fluxes.sfc = .5, .5, .5, .5, .2, .8, 1., 4.
        >>> fluxes.rfc = .5, .5, .5, .5, .8, .2, 4., 1.
        >>> states.sp = 0.
        >>> states.wc = 0.
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

        >>> fluxes.sfc = 0.
        >>> fluxes.rfc = 0.
        >>> states.sp = 2.
        >>> states.wc = 0.
        >>> model.calc_sp_wc_v1()
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if con.zonetype[k] != ILAKE:
            if (flu.rfc[k]+flu.sfc[k]) > 0.:
                sta.wc[k] += flu.tf[k]*flu.rfc[k]/(flu.rfc[k]+flu.sfc[k])
                sta.sp[k] += flu.tf[k]*flu.sfc[k]/(flu.rfc[k]+flu.sfc[k])
        else:
            sta.wc[k] = 0.
            sta.sp[k] = 0.

def calc_melt_sp_wc_v1(self):
    """Calculate melting of the ice content within the snow layer and
    update both the snow layers ice and the water content.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.CFMax`

    Required derived parameter:
      :class:`~hydpy.models.hland.hland_derived.TTM`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.TC`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.Melt`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.SP`

    Updatet state sequence:
        :class:`~hydpy.models.hland.hland_states.WC`

    Basic equations:
      :math:`\\frac{dSP}{dt} = - Melt` \n
      :math:`\\frac{dWC}{dt} = + Melt` \n
      :math:`Melt = min(cfmax \\cdot (TC-TTM), SP)` \n

    Examples:
        Six zones are initialized with the same threshold
        temperature and degree day factor, but  with different zone types
        and initial ice contents:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> cfmax(4.)
        >>> derived.ttm = 2.
        >>> states.sp = 0., 10., 10., 10., 5., 0.
        >>> states.wc = 2.

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

        >>> fluxes.tc = 2.
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 10.0, 10.0, 10.0, 5.0, 0.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)

        The same holds true for an actual temperature lower than the
        threshold temperature:

        >>> states.sp = 0., 10., 10., 10., 5., 0.
        >>> states.wc = 2.
        >>> fluxes.tc = -1.
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

        >>> states.sp = 0., 10., 10., 10., 5., 0.
        >>> states.wc = 2.
        >>> fluxes.tc = 5.
        >>> model.calc_melt_sp_wc_v1()
        >>> fluxes.melt
        melt(0.0, 6.0, 6.0, 6.0, 5.0, 0.0)
        >>> states.sp
        sp(0.0, 4.0, 4.0, 4.0, 0.0, 0.0)
        >>> states.wc
        wc(0.0, 8.0, 8.0, 8.0, 7.0, 2.0)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if con.zonetype[k] != ILAKE:
            if flu.tc[k] > der.ttm[k]:
                flu.melt[k] = min(con.cfmax[k] *
                                  (flu.tc[k]-der.ttm[k]), sta.sp[k])
                sta.sp[k] -= flu.melt[k]
                sta.wc[k] += flu.melt[k]
            else:
                flu.melt[k] = 0.
        else:
            flu.melt[k] = 0.
            sta.wc[k] = 0.
            sta.sp[k] = 0.

def calc_refr_sp_wc_v1(self):
    """Calculate refreezing of the water content within the snow layer and
    update both the snow layers ice and the water content.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.CFMax`
      :class:`~hydpy.models.hland.hland_control.CFR`

    Required derived parameter:
      :class:`~hydpy.models.hland.hland_derived.TTM`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.TC`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.Refr`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.WC`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.SP`

    Basic equations:
      :math:`\\frac{dSP}{dt} =  + Refr` \n
      :math:`\\frac{dWC}{dt} =  - Refr` \n
      :math:`Refr = min(cfr \\cdot cfmax \\cdot (TTM-TC), WC)`

    Examples:
        Six zones are initialized with the same threshold
        temperature, degree day factor and refreezing coefficient, but
        with different zone types and initial states:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> cfmax(4.)
        >>> cfr(.1)
        >>> derived.ttm = 2.
        >>> states.sp = 2.
        >>> states.wc = 0., 1., 1., 1., .5, 0.

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

        >>> fluxes.tc = 2.
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sp
        sp(0.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.wc
        wc(0.0, 1.0, 1.0, 1.0, 0.5, 0.0)

        The same holds true for an actual temperature higher than the
        threshold temperature:

        >>> states.sp = 2.
        >>> states.wc = 0., 1., 1., 1., .5, 0.
        >>> fluxes.tc = 2.
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

        >>> states.sp = 2.
        >>> states.wc = 0., 1., 1., 1., .5, 0.
        >>> fluxes.tc = 5.
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

        >>> states.sp = 2.
        >>> states.wc = 0., 1., 1., 1., .5, 0.
        >>> fluxes.tc = -1.
        >>> model.calc_refr_sp_wc_v1()
        >>> fluxes.refr
        refr(0.0, 0.6, 0.6, 0.6, 0.5, 0.0)
        >>> states.sp
        sp(0.0, 2.6, 2.6, 2.6, 2.5, 2.0)
        >>> states.wc
        wc(0.0, 0.4, 0.4, 0.4, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if con.zonetype[k] != ILAKE:
            if flu.tc[k] < der.ttm[k]:
                flu.refr[k] = min(con.cfr[k]*con.cfmax[k] *
                                  (der.ttm[k]-flu.tc[k]), sta.wc[k])
                sta.sp[k] += flu.refr[k]
                sta.wc[k] -= flu.refr[k]
            else:
                flu.refr[k] = 0.

        else:
            flu.refr[k] = 0.
            sta.wc[k] = 0.
            sta.sp[k] = 0.

def calc_in_wc_v1(self):
    """Calculate the actual water release from the snow layer due to the
    exceedance of the snow layers capacity for (liquid) water.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.WHC`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.SP`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.In_`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.WC`

    Basic equations:
      :math:`\\frac{dWC}{dt} = -In` \n
      :math:`-In = max(WC - WHC \\cdot SP, 0)`

    Examples:
        Initialize six zones of different types and frozen water
        contents of the snow layer and set the relative water holding
        capacity to 20% of the respective frozen water content:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> whc(.2)
        >>> states.sp = 0., 10., 10., 10., 5., 0.

        When there is no (liquid) water content in the snow layer, no water
        can be released:

        >>> states.wc = 0.
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        When there is a (liquid) water content in the snow layer, the water
        release depends on the frozen water content.  Note the special
        cases of the first zone beeing an internal lake, for which the snow
        routine does not apply, and of the last zone, which has no ice
        content and thus effectively not really a snow layer:

        >>> states.wc = 5.
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(0.0, 3.0, 3.0, 3.0, 4.0, 5.0)
        >>> states.wc
        wc(0.0, 2.0, 2.0, 2.0, 1.0, 0.0)

        When the relative water holding capacity is assumed to be zero,
        all liquid water is released:

        >>> whc(0.)
        >>> states.wc = 5.
        >>> model.calc_in_wc_v1()
        >>> fluxes.in_
        in_(0.0, 5.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if con.zonetype[k] != ILAKE:
            flu.in_[k] = max(sta.wc[k]-con.whc[k]*sta.sp[k], 0.)
            sta.wc[k] -= flu.in_[k]
        else:
            flu.in_[k] = flu.tf[k]
            sta.wc[k] = 0.

def calc_glmelt_in_v1(self):
    """Calculate melting from glaciers which are actually not covered by
    a snow layer and add it to the water release of the snow module.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.GMelt`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.SP`

    Required flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.TC`

    Calculated fluxes sequence:
      :class:`~hydpy.models.hland.hland_fluxes.GlMelt`

    Updated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.In_`

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
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if con.zonetype[k] == GLACIER:
            if (sta.sp[k] <= 0.) and (flu.tc[k] > der.ttm[k]):
                flu.glmelt[k] = con.gmelt[k]*(flu.tc[k]-der.ttm[k])
                flu.in_[k] += flu.glmelt[k]
            else:
                flu.glmelt[k] = 0.

def calc_r_sm_v1(self):
    """Calculate effective precipitation and update soil moisture.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.FC`
      :class:`~hydpy.models.hland.hland_control.Beta`

    Required fluxes sequence:
      :class:`~hydpy.models.hland.hland_fluxes.In_`

    Calculated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.R`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.SM`

    Basic equations:
      :math:`\\frac{dSM}{dt} = IN - R` \n
      :math:`R = IN \\cdot \\left(\\frac{SM}{FC}\\right)^{Beta}`


    Examples:
        Initialize six zones of different types.  The field
        capacity of all fields and forests is set to 200mm, the input
        of each zone is 10mm:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> fc(200.)
        >>> fluxes.in_ = 10.

        With a common nonlinearity parameter value of 2, a relative
        soil moisture of 50%  (zones three and four) results in a
        discharge coefficient of 25%. For a soil completely dried
        (zone five) or completely saturated (one six) the discharge
        coefficient does not depend on the nonlinearity parameter and
        is 0% and 100% respectively.  Glaciers and internal lakes also
        always route 100% of their input as effective precipitation:

        >>> beta(2.)
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 2.5, 2.5, 0.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 107.5, 107.5, 10.0, 200.0)

        Through decreasing the nonlinearity parameter, the discharge
        coefficient increases.  A parameter value of zero leads to a
        discharge coefficient of 100% for any soil moisture:

        >>> beta(0.)
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        With zero field capacity, the discharge coefficient also always
        equates to 100%:

        >>> fc(0.)
        >>> beta(2.)
        >>> states.sm = 0.
        >>> model.calc_r_sm_v1()
        >>> fluxes.r
        r(10.0, 10.0, 10.0, 10.0, 10.0, 10.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
            if con.fc[k] > 0.:
                flu.r[k] = flu.in_[k]*(sta.sm[k]/con.fc[k])**con.beta[k]
                flu.r[k] = max(flu.r[k], sta.sm[k]+flu.in_[k]-con.fc[k])
            else:
                flu.r[k] = flu.in_[k]
            sta.sm[k] += flu.in_[k]-flu.r[k]
        else:
            flu.r[k] = flu.in_[k]
            sta.sm[k] = 0.

def calc_cf_sm_v1(self):
    """Calculate capillary flow and update soil moisture.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.FC`
      :class:`~hydpy.models.hland.hland_control.CFlux`

    Required fluxes sequence:
      :class:`~hydpy.models.hland.hland_fluxes.R`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.UZ`

    Calculated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.CF`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.SM`

    Basic equations:
      :math:`\\frac{dSM}{dt} = CF` \n
      :math:`CF = CFLUX \\cdot (1 - \\frac{SM}{FC})`

    Examples:
        Initialize six zones of different types.  The field
        capacity of als fields and forests is set to 200mm, the maximum
        capillary flow rate is 4mm/d:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nmbzones(6)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD)
        >>> fc(200.)
        >>> cflux(4.)

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

        >>> fluxes.r = 0.
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> states.uz = 20.
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 1.0, 1.0, 2.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 101.0, 101.0, 2.0, 200.0)

        ...our enough effective precipitation is generated, which can be
        rerouted directly:

        >>> cflux(4.)
        >>> fluxes.r = 10.
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> states.uz = 0.
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 1.0, 1.0, 2.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 101.0, 101.0, 2.0, 200.0)

        If the upper zone layer is empty and no effective precipitation is
        generated, capillary flow is zero:

        >>> cflux(4.)
        >>> fluxes.r = 0.
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> states.uz = 0.
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 100.0, 0.0, 200.0)

        Here an example, where both the upper zone layer and effective
        precipitation provide water for the capillary flow, but less then
        the maximum flow rate times the relative soil moisture:

        >>> cflux(4.)
        >>> fluxes.r = 0.1
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> states.uz = 0.2
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.3, 0.3, 0.3, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 100.3, 100.3, 0.3, 200.0)

        Even unrealistic high maximum capillary flow rates do not result
        in overfilled soils:

        >>> cflux(1000.)
        >>> fluxes.r = 200.
        >>> states.sm = 0., 0., 100., 100., 0., 200.
        >>> states.uz = 200.
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 100.0, 100.0, 200.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 200.0, 200.0, 200.0, 200.0)

        For (unrealistic) soils with zero field capacity, capillary flow
        is always zero:

        >>> fc(0.)
        >>> states.sm = 0.
        >>> model.calc_cf_sm_v1()
        >>> fluxes.cf
        cf(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
            if con.fc[k] > 0.:
                flu.cf[k] = con.cflux[k]*(1.-sta.sm[k]/con.fc[k])
                flu.cf[k] = min(flu.cf[k], sta.uz+flu.r[k])
                flu.cf[k] = min(flu.cf[k], con.fc[k]-sta.sm[k])
            else:
                flu.cf[k] = 0.
            sta.sm[k] += flu.cf[k]
        else:
            flu.cf[k] = 0.
            sta.sm[k] = 0.

def calc_ea_sm_v1(self):
    """Calculate soil evaporation and update soil moisture.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.FC`
      :class:`~hydpy.models.hland.hland_control.LP`
      :class:`~hydpy.models.hland.hland_control.ERed`

    Required fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.EPC`
      :class:`~hydpy.models.hland.hland_fluxes.EI`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.SP`

    Calculated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.EA`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.SM`

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
        >>> parameterstep('1d')
        >>> nmbzones(7)
        >>> zonetype(ILAKE, GLACIER, FIELD, FOREST, FIELD, FIELD, FIELD)
        >>> fc(200.)
        >>> lp(.0, .0, .5, .5, .0, .8, 1.)
        >>> ered(0.)
        >>> fluxes.epc = 2.
        >>> fluxes.ei = 1.
        >>> states.sp = 0.

        Only fields and forests include soils; for glaciers and zones (the
        first two zones) no soil evaporation is performed.  For fields and
        forests, the underlying calculations are the same. In the following
        example, the relative soil moisture is 50% in all field and forest
        zones.  Hence, differences in soil evaporation are related to the
        different soil evaporation parameter values only:

        >>> states.sm = 100.
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 2.0, 2.0, 2.0, 1.25, 1.0)
        >>> states.sm
        sm(0.0, 0.0, 98.0, 98.0, 98.0, 98.75, 99.0)

        In the last example, evaporation values of 2mm have been calculated
        for some zones despite the fact, that these 2mm added to the actual
        interception evaporation of 1mm exceed potential evaporation.  This
        behaviour can be reduced...

        >>> states.sm = 100.
        >>> ered(.5)
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 1.5, 1.5, 1.5, 1.125, 1.0)
        >>> states.sm
        sm(0.0, 0.0, 98.5, 98.5, 98.5, 98.875, 99.0)

        ...or be completely excluded:

        >>> states.sm = 100.
        >>> ered(1.)
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> states.sm
        sm(0.0, 0.0, 99.0, 99.0, 99.0, 99.0, 99.0)

        Any occurence of a snow layer suppresses soil evaporation
        completely:

        >>> states.sp = 0.01
        >>> states.sm = 100.
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0)

        For (unrealistic) soils with zero field capacity, soil evaporation
        is always zero:

        >>> fc(0.)
        >>> states.sm = 0.
        >>> model.calc_ea_sm_v1()
        >>> fluxes.ea
        ea(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
            if sta.sp[k] <= 0.:
                if (con.lp[k]*con.fc[k]) > 0.:
                    flu.ea[k] = flu.epc[k]*sta.sm[k]/(con.lp[k]*con.fc[k])
                    flu.ea[k] = min(flu.ea[k], flu.epc[k])
                else:
                    flu.ea[k] = flu.epc[k]
                flu.ea[k] -= max(con.ered[k] *
                                 (flu.ea[k]+flu.ei[k]-flu.epc[k]), 0.)
                flu.ea[k] = min(flu.ea[k], sta.sm[k])
            else:
                flu.ea[k] = 0.
            sta.sm[k] -= flu.ea[k]
        else:
            flu.ea[k] = 0.
            sta.sm[k] = 0.



def calc_inuz_v1(self):
    """Accumulate the total inflow into the upper zone layer.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`

    Required derived parameters:
      :class:`~hydpy.models.hland.hland_derived.RelLandZoneArea`

    Required fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.R`
      :class:`~hydpy.models.hland.hland_fluxes.CF`

    Calculated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.InUZ`

    Basic equation:
      :math:`InUZ = R - CF`

    Examples:
        Initialize three zones of different relative `land sizes`
        (area related to the total size of the subbasin except lake areas):

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(3)
        >>> zonetype(FIELD, ILAKE, GLACIER)
        >>> derived.rellandzonearea = 2./3., 0., 1./3.
        >>> fluxes.r = 6., 0., 2.
        >>> fluxes.cf = 2., 0., 1.
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.inuz = 0.
    for k in range(con.nmbzones):
        if con.zonetype[k] != ILAKE:
            flu.inuz += der.rellandzonearea[k]*(flu.r[k]-flu.cf[k])

def calc_contriarea_v1(self):
    """Determine the relative size of the contributing area of the whole
    subbasin.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`
      :class:`~hydpy.models.hland.hland_control.RespArea`
      :class:`~hydpy.models.hland.hland_control.FC`
      :class:`~hydpy.models.hland.hland_control.Beta`

    Required derived parameter:
    :class:`~hydpy.models.hland.hland_derived.RelSoilArea`

    Required state sequence:
      :class:`~hydpy.models.hland.hland_states.SM`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.ContriArea`

    Basic equation:
      :math:`ContriArea = \\left( \\frac{SM}{FC} \\right)^{Beta}`

    Examples:
        Four zones are initialized, but only the first two zones
        of type field and forest are taken into account in the calculation
        of the relative contributing area of the catchment (even, if also
        glaciers contribute to the inflow of the upper zone layer):

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(4)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
        >>> beta(2.)
        >>> fc(200.)
        >>> resparea(True)
        >>> derived.relsoilarea(.5)
        >>> derived.relsoilzonearea(1./3., 2./3., 0., 0.)

        With a relative soil moisture of 100% in the whole subbasin, the
        contributing area is also estimated as 100%,...

        >>> states.sm = 200.
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ...and relative soil moistures of 0% result in an contributing
        area of 0%:

        >>> states.sm = 0.
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(0.0)

        With the given value 2 of the nonlinearity parameter Beta, soil
        moisture of 50% results in a contributing area estimate of 25%:

        >>> states.sm = 100.
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
        >>> derived.relsoilarea(0.)
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ...or setting all field capacities to zero...

        >>> derived.relsoilarea(.5)
        >>> fc(0.)
        >>> states.sm = 0.
        >>> model.calc_contriarea_v1()
        >>> fluxes.contriarea
        contriarea(1.0)

        ...leads to contributing area values of 100%.
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    if con.resparea and (der.relsoilarea > 0.):
        flu.contriarea = 0.
        for k in range(con.nmbzones):
            if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
                if con.fc[k] > 0.:
                    flu.contriarea += (der.relsoilzonearea[k]*
                                       (sta.sm[k]/con.fc[k])**con.beta[k])
                else:
                    flu.contriarea += der.relsoilzonearea[k]
    else:
        flu.contriarea = 1.

def calc_q0_perc_uz_v1(self):
    """Perform the upper zone layer routine which determines percolation
    to the lower zone layer and the fast response of the hland model.
    Note that the system behaviour of this method depends strongly on the
    specifications of the options :class:`RespArea` and :class:`RecStep`.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.RecStep`
      :class:`~hydpy.models.hland.hland_control.PercMax`
      :class:`~hydpy.models.hland.hland_control.K`
      :class:`~hydpy.models.hland.hland_control.Alpha`

    Required derived parameters:
      :class:`~hydpy.models.hland.hland_control.DT`

    Required fluxes sequence:
      :class:`~hydpy.models.hland.hland_fluxes.InUZ`

    Used Aide sequences:
      :class:`~hydpy.models.hland.hland_aides.Perc`
      :class:`~hydpy.models.hland.hland_aides.Q0`

    Calculated fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.Perc`
      :class:`~hydpy.models.hland.hland_fluxes.Q0`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.UZ`

    Basic equations:
      :math:`\\frac{dUZ}{dt} = InUZ - Perc - Q0` \n
      :math:`Perc = PercMax \\cdot ContriArea` \n
      :math:`Q0 = \\left( \\frac{UZ}{ContriArea} \\right)^{1+Alpha}`

    Examples:
        The upper zone layer routine is an exception compared to
        the other routines of the HydPy-H-Land model, regarding its
        consideration of numerical accuracy.  To increase the accuracy of
        the numerical integration of the underlying ordinary differential
        equation, each simulation step can be devided into substeps, which
        are all solved with first order accuracy.  In the first example,
        this option is omitted through setting the RecStep parameter to one:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> recstep(2)
        >>> derived.dt = 1./recstep
        >>> percmax(2.)
        >>> alpha(1.)
        >>> k(2.)
        >>> fluxes.contriarea = 1.
        >>> fluxes.inuz = 0.
        >>> states.uz = 1.
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
        >>> derived.dt = 1./recstep
        >>> states.uz = 1.
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

        >>> fluxes.contriarea = .5
        >>> states.uz = 1.
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.434108)
        >>> fluxes.q0
        q0(0.565892)
        >>> states.uz
        uz(0.0)

        Resetting RecStep leads to more transparent results.  Note that, due
        to the large value of the storage coefficient and the low accuracy
        of the numerical approximation, direct discharge drains the rest of
        the upper zone storage:

        >>> recstep(2)
        >>> derived.dt = 1./recstep
        >>> states.uz = 1.
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.5)
        >>> states.uz
        uz(0.0)

        Applying a more reasonable storage coefficient results in:

        >>> k(.5)
        >>> states.uz = 1.
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

        >>> fluxes.inuz = .3
        >>> states.uz = 1.
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
        >>> derived.dt = 1./recstep
        >>> states.uz = 1.
        >>> model.calc_q0_perc_uz_v1()
        >>> fluxes.perc
        perc(0.5)
        >>> fluxes.q0
        q0(0.421708)
        >>> states.uz
        uz(0.378292)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    aid = self.sequences.aides.fastaccess
    flu.perc = 0.
    flu.q0 = 0.
    for jdx in range(con.recstep):
        # First state update related to the upper zone input.
        sta.uz += der.dt*flu.inuz
        # Second state update related to percolation.
        aid.perc = min(der.dt*con.percmax*flu.contriarea, sta.uz)
        sta.uz -= aid.perc
        flu.perc += aid.perc
        # Third state update related to fast runoff response.
        if sta.uz > 0.:
            if flu.contriarea > 0.:
                aid.q0 = (der.dt*con.k *
                          (sta.uz/flu.contriarea)**(1.+con.alpha))
                aid.q0 = min(aid.q0, sta.uz)
            else:
                aid.q0 = sta.uz
            sta.uz -= aid.q0
            flu.q0 += aid.q0
        else:
            aid.q0 = 0.

def calc_lz_v1(self):
    """Update the lower zone layer in accordance with percolation from
    upper groundwater to lower groundwater and/or in accordance with
    lake precipitation.

    Required control parameters:
      :class:`~hydpy.models.hland.hland_control.NmbZones`
      :class:`~hydpy.models.hland.hland_control.ZoneType`

    Required derived parameters:
      :class:`~hydpy.models.hland.hland_control.RelLandArea`
      :class:`~hydpy.models.hland.hland_control.RelZoneArea`

    Required fluxes sequences:
      :class:`~hydpy.models.hland.hland_fluxes.PC`
      :class:`~hydpy.models.hland.hland_fluxes.Perc`

    Updated state sequence:
      :class:`~hydpy.models.hland.hland_states.LZ`

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
        >>> parameterstep('1d')
        >>> nmbzones(2)
        >>> zonetype(FIELD, FIELD)
        >>> derived.rellandarea = 1.
        >>> derived.relzonearea = 2./3., 1./3.
        >>> fluxes.perc = 2.
        >>> fluxes.pc = 5.
        >>> states.lz = 10.
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
        >>> derived.rellandarea = 2./3.
        >>> derived.relzonearea = 2./3., 1./3.
        >>> states.lz = 10.
        >>> model.calc_lz_v1()
        >>> states.lz
        lz(13.0)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    sta.lz += der.rellandarea*flu.perc
    for k in range(con.nmbzones):
        if con.zonetype[k] == ILAKE:
            sta.lz += der.relzonearea[k]*flu.pc[k]

def calc_el_lz_v1(self):
    """Calculate lake evaporation.

    Required control parameters:
        :class:`~hydpy.models.hland.hland_control.NmbZones`
        :class:`~hydpy.models.hland.hland_control.ZoneType`
        :class:`~hydpy.models.hland.hland_control.TTIce`

    Required derived parameters:
        :class:`~hydpy.models.hland.hland_control.RelZoneArea`

    Required fluxes sequences:
        :class:`~hydpy.models.hland.hland_fluxes.TC`
        :class:`~hydpy.models.hland.hland_fluxes.EPC`

    Updated state sequence:
        :class:`~hydpy.models.hland.hland_states.LZ`

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
        >>> parameterstep('1d')
        >>> nmbzones(6)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, ILAKE)
        >>> ttice(-1.)
        >>> derived.relzonearea = 1./6.
        >>> fluxes.epc = .6
        >>> fluxes.tc = 0., 0., 0., 0., -1., -2.
        >>> states.lz = 10.
        >>> model.calc_el_lz_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.6, 0.0, 0.0)
        >>> states.lz
        lz(9.9)

        Note that internal lakes always contain water.  Hence, the
        HydPy-H-Land model allows for negative values of the lower
        zone storage:

        >>> states.lz = .05
        >>> model.calc_el_lz_v1()
        >>> fluxes.el
        el(0.0, 0.0, 0.0, 0.6, 0.0, 0.0)
        >>> states.lz
        lz(-0.05)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmbzones):
        if (con.zonetype[k] == ILAKE) and (flu.tc[k] > con.ttice[k]):
            flu.el[k] = flu.epc[k]
            sta.lz -= der.relzonearea[k]*flu.el[k]
        else:
            flu.el[k] = 0.

def calc_q1_lz_v1(self):
    """Calculate the slow response of the lower zone layer.

    Required control parameters:
        :class:`~hydpy.models.hland.hland_control.K4`
        :class:`~hydpy.models.hland.hland_control.Gamma`

    Calculated fluxes sequence:
        :class:`~hydpy.models.hland.hland_fluxes.Q1`

    Updated state sequence:
        :class:`~hydpy.models.hland.hland_states.LZ`

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
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> k4(.2)
        >>> gamma(0.)
        >>> states.lz = -2.
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.0)
        >>> states.lz
        lz(-2.0)

        ...or zero, no slow discharge response occurs:

        >>> states.lz = 0.
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.0)
        >>> states.lz
        lz(0.0)

        For storage values above zero the linear...

        >>> states.lz = 2.
        >>> model.calc_q1_lz_v1()
        >>> fluxes.q1
        q1(0.2)
        >>> states.lz
        lz(1.8)

        ...or nonlinear storage routing equation applies:

        >>> gamma(1.)
        >>> states.lz = 2.
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
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    if sta.lz > 0.:
        flu.q1 = con.k4*sta.lz**(1.+con.gamma)
    else:
        flu.q1 = 0.
    sta.lz -= flu.q1


def calc_inuh_v1(self):
    """Calculate the unit hydrograph input.

    Required derived parameters:
      :class:`~hydpy.models.hland.hland_derived.RelLandArea`

    Required flux sequences:
      :class:`~hydpy.models.hland.hland_fluxes.Q0`
      :class:`~hydpy.models.hland.hland_fluxes.Q1`

    Calculated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.InUH`

    Basic equation:
        :math:`InUH = Q0 + Q1`

    Example:
        The unit hydrographs receives base flow from the whole subbasin
        and direct flow from zones of type field, forest and glacier only.
        In the following example, these occupy only one half of the
        subbasin, which is why the partial input of q0 is halved:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> derived.rellandarea = 0.5
        >>> fluxes.q0 = 4.
        >>> fluxes.q1 = 1.
        >>> model.calc_inuh_v1()
        >>> fluxes.inuh
        inuh(3.0)

    """
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.inuh = der.rellandarea*flu.q0+flu.q1

def calc_outuh_quh_v1(self):
    """Calculate the unit hydrograph output (convolution).

    Required derived parameters:
        :class:`~hydpy.models.hland.hland_derived.UH`
        :class:`~hydpy.models.hland.hland_derived.NmbUH`

    Required flux sequences:
        :class:`~hydpy.models.hland.hland_fluxes.Q0`
        :class:`~hydpy.models.hland.hland_fluxes.Q1`
        :class:`~hydpy.models.hland.hland_fluxes.InUH`

    Updated log sequence:
        :class:`~hydpy.models.hland.hland_logs.QUH`

    Calculated flux sequence:
        :class:`~hydpy.models.hland.hland_fluxes.OutUH`

    Examples:
        Prepare a unit hydrograph with only three ordinates ---
        representing a fast catchment response compared to the selected
        step size:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> derived.nmbuh = 3
        >>> derived.uh.shape = derived.nmbuh
        >>> derived.uh = 0.3, 0.5, 0.2
        >>> logs.quh.shape = 3
        >>> logs.quh = 1., 3., 0.

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.inuh = 0.
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

        >>> fluxes.inuh = 4.
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(4.2)
        >>> logs.quh
        quh(2.0, 0.8, 0.0)

        The next example demonstates the updating of non empty logging
        sequence:

        >>> fluxes.inuh = 4.
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(3.2)
        >>> logs.quh
        quh(2.8, 0.8, 0.0)

        A unit hydrograph with only one ordinate results in the direct
        routing of the input:

        >>> derived.nmbuh = 1
        >>> derived.uh.shape = derived.nmbuh
        >>> derived.uh = 1.
        >>> fluxes.inuh = 0.
        >>> logs.quh.shape = 1
        >>> logs.quh = 0.
        >>> model.calc_outuh_quh_v1()
        >>> fluxes.outuh
        outuh(0.0)
        >>> logs.quh
        quh(0.0)
        >>> fluxes.inuh = 4.
        >>> model.calc_outuh_quh()
        >>> fluxes.outuh
        outuh(4.0)
        >>> logs.quh
        quh(0.0)
    """
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    log = self.sequences.logs.fastaccess
    flu.outuh = der.uh[0]*flu.inuh+log.quh[0]
    for jdx in range(1, der.nmbuh):
        log.quh[jdx-1] = der.uh[jdx]*flu.inuh+log.quh[jdx]


def calc_qt_v1(self):
    """Calcutate the total discharge after possible abstractions.

    Required control parameter:
      :class:`~hydpy.models.hland.hland_control.Abstr`

    Required flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.OutUH`

    Calculated flux sequence:
      :class:`~hydpy.models.hland.hland_fluxes.QT`

    Basic equation:
        :math:`QT = max(OutUH - Abstr, 0)`

    Examples:
        Trying to abstract less then available, as much as available and
        less then available results in:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> abstr(2.)
        >>> fluxes.outuh = 2.
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(1.0)
        >>> fluxes.outuh = 1.
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(0.0)
        >>> fluxes.outuh = .5
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(0.0)

        Note that "negative abstractions" are allowed:
        >>> abstr(-2.)
        >>> fluxes.outuh = 1.
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.qt = max(flu.outuh-con.abstr, 0.)

def update_outlets_v1(self):
    """Update the outlet link sequence."""
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    out = self.sequences.outlets.fastaccess
    out.q[0] += der.qfactor*flu.qt


class Model(modeltools.Model):
    """The HydPy-H-Land model.

    The equations of HydPy-H-Land model can be differentiated into three
    groups.  First, input data is prepared:

      * :func:`~Model.calc_tc`
      * :func:`~Model.calc_tmean`
      * :func:`~Model.calc_fracrain`
      * :func:`~Model.calc_rfc_sfc`
      * :func:`~Model.calc_pc`
      * :func:`~Model.calc_ep`
      * :func:`~Model.calc_epc`

    Secondly, the differential equations are solved in an ad hoc manner:
      * :func:`~Model.calc_tf_ic`
      * :func:`~Model.calc_ei_ic`
      * :func:`~Model.calc_sp_wc`
      * :func:`~Model.calc_melt_sp_wc`
      * :func:`~Model.calc_refr_sp_wc`
      * :func:`~Model.calc_in_wc`
      * :func:`~Model.calc_r_sm`
      * :func:`~Model.calc_cf_sm`
      * :func:`~Model.calc_ea_sm`
      * :func:`~Model.calc_inuz`
      * :func:`~Model.calc_contriarea`
      * :func:`~Model.calc_q0_perc_uz`
      * :func:`~Model.calc_lz`
      * :func:`~Model.calc_el_lz`
      * :func:`~Model.calc_q1_lz`

    Thirdly, the simulated output runoff is modified:
      * :func:`~Model.calc_inuh`
      * :func:`~Model.calc_outuh_quh`
      * :func:`~Model.calc_qt`

    Note that all methods are performed sequentially in the :func:`~Model.run`
    method, including the state updates --- order matters!  Let us take the
    interception routine as an example.  First, precipitation is added to the
    interception storage and precipitation exceeding the interception capacity
    is routed as throughfall in method :func:`Model.calc_tf_ic`.  Then, based
    on the already updated interception storage, interception evaporation is
    calculated in method :func:`Model.calc_ei_ic`.  It is, as if evaporation
    would always only occur after precipitation, but never beforehand or
    afterwards.
    """
    _RUNMETHODS = (calc_tc_v1,
                   calc_tmean_v1,
                   calc_fracrain_v1,
                   calc_rfc_sfc_v1,
                   calc_pc_v1,
                   calc_ep_v1,
                   calc_epc_v1,
                   calc_tf_ic_v1,
                   calc_ei_ic_v1,
                   calc_sp_wc_v1,
                   calc_melt_sp_wc_v1,
                   calc_refr_sp_wc_v1,
                   calc_glmelt_in_v1,
                   calc_in_wc_v1,
                   calc_r_sm_v1,
                   calc_cf_sm_v1,
                   calc_ea_sm_v1,
                   calc_inuz_v1,
                   calc_contriarea_v1,
                   calc_q0_perc_uz_v1,
                   calc_lz_v1,
                   calc_el_lz_v1,
                   calc_q1_lz_v1,
                   calc_inuh_v1,
                   calc_outuh_quh_v1,
                   calc_qt_v1,
                   update_outlets_v1)
