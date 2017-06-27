# -*- coding: utf-8 -*-

# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.cythons import modelutils
# ...model specifc
from hydpy.models.lland.lland_constants import WASSER, VERS


def calc_nkor_v1(self):
    """Adjust the given precipitation values.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.KG`

    Required input sequence:
      :class:`~hydpy.models.lland.lland_inputs.Nied`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.NKor`

    Basic equation:
      :math:`NKor = KG \\cdot Nied`

    Example:

    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> nhru(3)
    >>> kg(.8, 1., 1.2)
    >>> inputs.nied = 10.
    >>> model.calc_nkor_v1()
    >>> fluxes.nkor
    nkor(8.0, 10.0, 12.0)
    """
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nhru):
        flu.nkor[k] = con.kg[k] * inp.nied


def calc_tkor_v1(self):
    """Adjust the given air temperature values.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.KT`

    Required input sequence:
      :class:`~hydpy.models.lland.lland_inputs.TemL`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.TKor`

    Basic equation:
      :math:`TKor = KT + TemL`

    Example:

    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> nhru(3)
    >>> kt(-2., 0., 2.)
    >>> inputs.teml(1.)
    >>> model.calc_tkor_v1()
    >>> fluxes.tkor
    tkor(-1.0, 1.0, 3.0)
    """
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nhru):
        flu.tkor[k] = con.kt[k] + inp.teml


def calc_et0_v1(self):
    """Calculate reference evapotranspiration after Turc-Wendling.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.KE`
      :class:`~hydpy.models.lland.lland_control.KF`

    Required input sequence:
      :class:`~hydpy.models.lland.lland_inputs.Glob`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.TKor`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.ET0`

    Basic equation:
      :math:`ET0 = KE \\cdot
      \\frac{(8.64 \\cdot Glob+93 \\cdot KF) \\cdot (TKor+22)}
      {165 \\cdot (TKor+123) \\cdot (1 + 0.00019 \\cdot min(HNN, 600))}`

    Example:

    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> simulationstep('12h')
    >>> nhru(3)
    >>> ke(1.1)
    >>> kf(.6)
    >>> hnn(200., 600., 1000.)
    >>> inputs.glob = 200.
    >>> fluxes.tkor = 15.
    >>> model.calc_et0_v1()
    >>> fluxes.et0
    et0(1.535855, 1.431075, 1.431075)
    """
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nhru):
        flu.et0[k] = (con.ke[k]*(((8.64*inp.glob+93.*con.kf[k]) *
                                  (flu.tkor[k]+22.)) /
                                 (165.*(flu.tkor[k]+123.) *
                                  (1.+0.00019*min(con.hnn[k], 600.)))))


def calc_evpo_v1(self):
    """Calculate land use and month specific values of potential
    evapotranspiration.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.FLn`

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_control.MOY`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.ET0`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.EvPo`

    Additional requirements:
      :attr:`~hydpy.core.modeltools.Model.idx_sim`

    Basic equation:
      :math:`EvPo = FLn \\cdot ET0`

    Example:

        For clarity, this is more of a kind of an integration example.
        Parameter :class:`~hydpy.models.lland.lland_control.FLn` both
        depends on time (the actual month) and space (the actual land use).
        Firstly, let us define a initialization time period spanning the
        transition from June to July:

        >>> from hydpy import pub, Timegrid, Timegrids
        >>> pub.timegrids = Timegrids(Timegrid('30.06.2000',
        ...                                    '02.07.2000',
        ...                                    '1d'))

        Secondly, assume that the considered subbasin is differenciated in
        two HRUs, one of primarily consisting of arable land and the other
        one of deciduous forests:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)

        Thirdly, set the :class:`~hydpy.models.lland.lland_control.FLn`
        values, one for the relevant months and land use classes:

        >>> fln.acker_jun = 1.299
        >>> fln.acker_jul = 1.304
        >>> fln.laubw_jun = 1.350
        >>> fln.laubw_jul = 1.365

        Fourthly, the index array connecting the simulation time steps
        defined above and the month indexes (0...11) can be retrieved
        from the :mod:`~hydpy.pub` module.  This can be done manually
        more conveniently via its update method:

        >>> derived.moy.update()
        >>> derived.moy
        moy(5, 6)

        Finally, the actual method (with its simple equation) is applied
        as usual:

        >>> fluxes.et0 = 2.
        >>> model.idx_sim = 0
        >>> model.calc_evpo_v1()
        >>> fluxes.evpo
        evpo(2.598, 2.7)
        >>> model.idx_sim = 1
        >>> model.calc_evpo_v1()
        >>> fluxes.evpo
        evpo(2.608, 2.73)

        Reset module :mod:`~hydpy.pub` to not interfere the following
        examples:

        >>> pub.timegrids = None
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nhru):
        flu.evpo[k] = con.fln[con.lnk[k]-1, der.moy[self.idx_sim]] * flu.et0[k]


def calc_nbes_inzp_v1(self):
    """Calculate throughfall and update the interception storage
    accordingly.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.KInz`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.NKor`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.NBes`

    Updated state sequence:
      :class:`~hydpy.models.lland.lland_states.Inzp`

    Additional requirements:
      :attr:`~hydpy.core.modeltools.Model.idx_sim`

    Basic equation:
      :math:`NBes = \\Bigl \\lbrace
      {
      {PKor \\ | \\ Inzp = KInz}
      \\atop
      {0 \\ | \\ Inzp < KInz}
      }`

    Examples:

        Initialize six HRUs with different land usages:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> lnk(SIED_D, FEUCHT, GLETS, WASSER)

        Define values for the maximum interception storage directly:

        >>> derived.kinz.sied_d_jul = 2.
        >>> derived.kinz.feucht_jul = 1.
        >>> derived.kinz.glets_jul = 0.
        >>> derived.kinz.wasser_jul = 0.

        Assume that the three consecutive initialization time steps
        lie in three different months (does not make sense for the
        selected time step of one day, but allows for a more rigorous
        testing of proper indexing):

        >>> derived.moy.shape = 3
        >>> derived.moy = numpy.array([5, 6, 7])
        >>> model.idx_sim = 1

        The dense settlement and the wetland area start with a initial
        interception storage of 1/2 mm, the glacier and water area (must)
        start with 0 mm.  In the first example, actual precipition is 2 mm:

        >>> states.inzp(0.5, 0.5, 0., 0.)
        >>> fluxes.nkor = 1.
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(1.5, 1.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.5, 1.0, 1.0)

        Only for the settled area, interception capacity is not exceeded,
        meaning not through fall occurs.

        If there is no precipitation, there is of course also no through
        fall and interception storage remains unchanged:

        >>> states.inzp(0.5, 0.5, 0., 0.)
        >>> fluxes.nkor = 0.
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(0.5, 0.5, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.0, 0.0, 0.0)

        Note the following to peculiarities:  Firstly, the behaviour of
        the glacier area is due to its zero interception capacity.  On the
        contrary, the behaviour of the water area hard coded.  Hence,
        increasing the interception capacity shows no effect:

        >>> derived.kinz.glets_jul = 1.
        >>> derived.kinz.wasser_jul = 1.
        >>> states.inzp(0.5, 0.5, 0., 0.)
        >>> fluxes.nkor = 1.
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(1.5, 1.0, 1.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.5, 0.0, 1.0)

        Secondly, due to discontinuous changes of the interception capacity
        between two months, through fall can occur after the corresponding
        precipitation event has occured.  In the last example, this results
        from the given decrease of the glaciers interception capacity:

        >>> derived.kinz.glets_jul = .6
        >>> fluxes.nkor = 0.
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(1.5, 1.0, 0.6, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.0, 0.4, 0.0)

    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if con.lnk[k] != WASSER:
            flu.nbes[k] = \
                max(flu.nkor[k]+sta.inzp[k] -
                    der.kinz[con.lnk[k]-1, der.moy[self.idx_sim]], 0.)
            sta.inzp[k] += flu.nkor[k]-flu.nbes[k]
        else:
            flu.nbes[k] = flu.nkor[k]
            sta.inzp[k] = 0.


def calc_evi_inzp_v1(self):
    """Calculate interception evaporation and update the interception
    storage accordingly.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.TRefT`
      :class:`~hydpy.models.lland.lland_control.TRefN`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.EvPo`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.EvI`

    Updated state sequence:
      :class:`~hydpy.models.lland.lland_states.Inzp`

    Basic equation:
      :math:`EvI = \\Bigl \\lbrace
      {
      {EvPo \\ | \\ Inzp > 0}
      \\atop
      {0 \\ | \\ Inzp = 0}
      }`

    Examples:
        Initialize four HRUs with different combinations of land usage
        and initial interception storage and apply a value of potential
        evaporation of 3 mm on each one:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> lnk(ACKER, ACKER, ACKER, WASSER)
        >>> states.inzp = 0., 2., 4., 0.
        >>> fluxes.evpo = 3.
        >>> model.calc_evi_inzp_v1()
        >>> states.inzp
        inzp(0.0, 0.0, 1.0, 0.0)
        >>> fluxes.evi
        evi(0.0, 2.0, 3.0, 3.0)

        For the first three HRUs of land use class
        :const:`~hydpy.models.lland.lland_constants.ACKER`,
        interception evaporation is identical with potential
        evapotranspiration as long as it is met by the available
        intercepted water.  For water areas, interception evaporation is
        generally set to potential evaporation.
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if con.lnk[k] != WASSER:
            flu.evi[k] = min(flu.evpo[k], sta.inzp[k])
            sta.inzp[k] -= flu.evi[k]
        else:
            flu.evi[k] = flu.evpo[k]


def calc_wgtf_v1(self):
    """Calculate the potential snow melt.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.GTF`
      :class:`~hydpy.models.lland.lland_control.TRefT`
      :class:`~hydpy.models.lland.lland_control.TRefN`
      :class:`~hydpy.models.lland.lland_control.RSchmelz`
      :class:`~hydpy.models.lland.lland_control.CPWasser`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.TKor`

    Calculated fluxes sequence:
      :class:`~hydpy.models.lland.lland_fluxes.WGTF`

    Basic equation:
      :math:`WGTF = max(GTF \\cdot (TKor - TRefT), 0) +
      max(\\frac{CPWasser}{RSchmelz} \\cdot (TKor - TRefN), 0)`

    Examples:
        Initialize six HRUs with identical degree-day factors and
        temperature thresholds, but different combinations of land use
        and air temperature:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(6)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER, ACKER, ACKER)
        >>> gtf(5.)
        >>> treft(0.)
        >>> trefn(1.)
        >>> fluxes.tkor = 2., 2., 2., -1., 0., 1.

        First, note that the values of the degree-day factor are only half
        as much as the given value, due to the small simulation step size
        beeing only half as long as the parameter step size:

        >>> gtf
        gtf(5.0)
        >>> gtf.values
        array([ 2.5,  2.5,  2.5,  2.5,  2.5,  2.5])

        Secondly, note that the specific heat capacity and melt heat
        capacity of water are (compared to most parameters in in
        hydrological models) really fixed properties.  This is why these
        parameters provide initial default values:

        >>> cpwasser
        cpwasser(4.1868)
        >>> rschmelz
        rschmelz(334.0)

        (These values are not hard coded, to allow for changing the
        sensitivity of the snow routine for precipitation driven snow
        melt events.)

        When performing the calculations, one sees that the potential
        melting rate is identical for the first two HRUs.  The land use
        class results in no difference, except for water areas (third HRU),
        where no potential melt needs to be calculated.  The last three
        HRUs show the usual behaviour of the degree day method, when the
        actual temperature is below (fourth HRU), equal to (fifth HRU) or
        above (sixths zone) the threshold temperature.  Additionally, the
        first two zones show the influence of the additional energy intake
        due to "warm" precipitation.  Obviously, this additional term is
        quite negligible for common parameterizations, even if lower
        values for the seperate threshold temperature would be taken into
        account:

        >>> model.calc_wgtf_v1()
        >>> fluxes.wgtf
        wgtf(5.012535, 5.012535, 0.0, 0.0, 0.0, 2.5)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nhru):
        if con.lnk[k] != WASSER:
            flu.wgtf[k] = (
              max(con.gtf[k]*(flu.tkor[k]-con.treft[k]), 0) +
              max(con.cpwasser/con.rschmelz*(flu.tkor[k]-con.trefn[k]), 0.)
              )
        else:
            flu.wgtf[k] = 0.


def calc_schm_wats_v1(self):
    """Calculate the actual amount of water melting within the snow cover.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.TGr`

    Required flux sequences:
      :class:`~hydpy.models.lland.lland_fluxes.TKor`
      :class:`~hydpy.models.lland.lland_fluxes.NBes`
      :class:`~hydpy.models.lland.lland_fluxes.WGTF`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.Schm`

    Updated state sequence:
      :class:`~hydpy.models.lland.lland_states.WATS`

    Basic equations:
      :math:`\\frac{dWATS}{dt}  = \\Bigl \\lbrace
      {
      {NBes - Schm \\ | \\ NKor < TGr}
      \\atop
      {Schm \\ | \\ NKor \\geq TGr}
      }`
      :math:`Schm = \\Bigl \\lbrace
      {
      {WGTF \\ | \\ WATS > 0}
      \\atop
      {0 \\ | \\ WATS = 0}
      }`

    Examples:
        Initialize one water and six arable land HRUs.  Assume the same
        values for the threshold temperature, the initial amount of frozen
        water and stand precipitation, but different values for the
        actual air temperature and potential snow melt:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(WASSER, ACKER, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> tgr(1.)
        >>> states.wats = 2.
        >>> fluxes.nbes = 1.
        >>> fluxes.tkor = 0., 0., 1., 2., 2., 2., 0.
        >>> fluxes.wgtf = 0., 0., 0., 0., 1., 3., 3.
        >>> model.calc_schm_wats_v1()
        >>> states.wats
        wats(0.0, 3.0, 2.0, 2.0, 1.0, 0.0, 0.0)
        >>> fluxes.schm
        schm(0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0)

        For water areas, both the frozen amount of water and actual melt
        are set to zero.  For all other land use classes, the following
        discussion for the arable land HRUs applies. As demonstated with
        the help of the second, third, and forth HRU, stand precipitation
        is added to the frozen amount of the snow layer whenever the
        air temperature is below the associated threshold temperature.
        The last three HRUs show that the actual melting is limited either
        by :class:`~hydpy.models.lland.lland_fluxes.WGTF` (reflecting the
        available energy) or the initial value of
        :class:`~hydpy.models.lland.lland_states.WATS` (reflecting the
        available frozen water).
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if con.lnk[k] != WASSER:
            if flu.tkor[k] < con.tgr[k]:
                sta.wats[k] += flu.nbes[k]
            flu.schm[k] = min(flu.wgtf[k], sta.wats[k])
            sta.wats[k] -= flu.schm[k]
        else:
            sta.wats[k] = 0.
            flu.schm[k] = 0.


def calc_wada_waes_v1(self):
    """Calculate the actual water release from the snow cover.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.PWMax`

    Required flux sequences:
      :class:`~hydpy.models.lland.lland_fluxes.NBes`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.WaDa`

    Required state sequences
      :class:`~hydpy.models.lland.lland_states.WAeS`

    Updated state sequence:
      :class:`~hydpy.models.lland.lland_states.WAeS`

    Basic equations:
      :math:`\\frac{dWAeS}{dt} = NBes - WaDa`
      :math:`WAeS \\leq PWMax \\cdot WATS`

    Examples:
        For simplicity, :class:`~hydpy.models.lland.lland_control.PWMax`
        is set to a value of two for each of the five initialized HRUs.
        Thus, the snow cover can hold as much liquid water as it contains
        frozen water.  Stand precipitation is also always set to the same
        value, but the initial conditions of the snow cover are varied:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(WASSER, ACKER, ACKER, ACKER, ACKER)
        >>> pwmax(2.)
        >>> fluxes.nbes = 1.
        >>> states.wats = 0., 0., 1., 1.0, 1.
        >>> states.waes = 0., 0., 1., 1.5, 2.
        >>> model.calc_wada_waes_v1()
        >>> states.waes
        waes(0.0, 0.0, 2.0, 2.0, 2.0)
        >>> fluxes.wada
        wada(1.0, 1.0, 0.0, 0.5, 1.0)

        Note the special cases of the first HRU (the snow routine is not
        applied for water areas) and the second HRU (for all other land
        use classes the snow routine is also applied on "empty" snow
        covers with zero initial values).
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if con.lnk[k] != WASSER:
            sta.waes[k] += flu.nbes[k]
            flu.wada[k] = max(sta.waes[k]-con.pwmax[k]*sta.wats[k], 0.)
            sta.waes[k] -= flu.wada[k]
        else:
            sta.waes[k] = 0.
            flu.wada[k] = flu.nbes[k]


def calc_evb_v1(self):
    """Calculate the actual water release from the snow cover.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.NFk`
      :class:`~hydpy.models.lland.lland_control.GrasRef_R`

    Required state sequence:
      :class:`~hydpy.models.lland.lland_states.BoWa`

    Required flux sequences:
      :class:`~hydpy.models.lland.lland_fluxes.EvPo`
      :class:`~hydpy.models.lland.lland_fluxes.EvI`

    Used aide sequence:
      :class:`~hydpy.models.lland.lland_aides.Temp`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.EvB`

    Basic equations:
      :math:`temp = exp(-GrasRef_R \\cdot \\frac{BoWa}{NFk})`
      :math:`EvB = (EvPo - EvI) \\cdot
      \\frac{1 - temp}{1 + temp -2 \\cdot exp(-GrasRef_R)}`

    Examples:
        Soil evaporation is calculated neither for water nor for sealed
        areas (see HRUs one and two).  All other land use classes are
        handled in accordance with a recommendation of the set of codes
        described in ATV-DVWK-M 504 (arable land has been selected for
        HRUs three to six arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(6)
        >>> lnk(WASSER, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> grasref_r(5.)
        >>> nfk(0., 0., 0., 100., 100., 100.)
        >>> fluxes.evpo = 5.
        >>> fluxes.evi = 3.
        >>> states.bowa = 0., 0., 0., 0., 50., 100.
        >>> model.calc_evb_v1()
        >>> fluxes.evb
        evb(0.0, 0.0, 0.0, 0.0, 1.717962, 2.0)
calc
        In case usable field capacity is zero, soil evaporation is
        generally set to zero (see the third HRU).  The last three
        HRUs demonstrate the rise in soil evaporation with increasing
        soil moisture, lessening in the high soil moisture range.
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    aid = self.sequences.aides.fastaccess
    for k in range(con.nhru):
        if ((con.lnk[k] != WASSER) and (con.lnk[k] != VERS) and
                (con.nfk[k] > 0.)):
            aid.temp = modelutils.exp(-con.grasref_r *
                                      sta.bowa[k]/con.nfk[k])
            flu.evb[k] = ((flu.evpo[k]-flu.evi[k]) * (1.-aid.temp) /
                          (1.+aid.temp-2.*modelutils.exp(-con.grasref_r)))
        else:
            flu.evb[k] = 0.


def calc_qbb_v1(self):
    """Calculate the amount of base flow released from the soil.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.Beta`
      :class:`~hydpy.models.lland.lland_control.FBeta`

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_derived.WB`
      :class:`~hydpy.models.lland.lland_derived.WZ`

    Required state sequence:
      :class:`~hydpy.models.lland.lland_states.BoWa`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QBB`

    Basic equations:
      :math:`Beta_{eff} = \\Bigl \\lbrace
      {
      {Beta \\ | \\ BoWa \\leq WZ}
      \\atop
      {Beta \\cdot (1+(FBeta-1)\\cdot\\frac{BoWa-WZ}{NFk-WZ}) \\|\\ BoWa > WZ}
      }`

      :math:`QBB = \\Bigl \\lbrace
      {
      {0 \\ | \\ BoWa \\leq WB}
      \\atop
      {Beta_{eff}  \\cdot (BoWa - WB) \\|\\ BoWa > WB}
      }`

    Examples:
        For water and sealed areas, no base is flow calculated (see the
        first two HRUs).  No principal distinction is made between the
        remaining land use classes (arable land has been selected for
        the other five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(7)
        >>> lnk(WASSER, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> beta(.04)
        >>> fbeta(2.)
        >>> nfk(0., 0., 0., 100., 100., 100., 200.)
        >>> derived.wb(10.)
        >>> derived.wz(70.)

        Note the time dependence of parameter
        :class:`~hydpy.models.lland.lland_control.Beta`:

        >>> beta
        beta(0.04)
        >>> beta.values
        array([ 0.02,  0.02,  0.02,  0.02,  0.02,  0.02,  0.02])

        In the first example, the actual soil water content is set to low
        values. For values below the threshold `wb`, not percolation occurs.
        Above `wb` (but below `wz`), calculated percolation shows a linear
        behaviour which is only related to parameter `beta`:

        >>> states.bowa = 0., 0., 0., 0., 10., 20., 20.
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2)

        Note that for the last two HRUs the same amount of
        base flow generation is determined, in spite of the fact
        that both exhibit different relative soil moistures.  It is
        common to modify this "pure absolute dependency" to a "mixed
        absolute/relative dependency" through defining the values of
        parameter :class:`~hydpy.models.lland.lland_derived.WB` indirectly
        via parameter :class:`~hydpy.models.lland.lland_control.RelWB`.

        In the second example, the actual soil water content is set to high
        values.  For values below the threshold `wz`, the disussion above
        remains valid.  For values above `wz`, percolation shows a nonlinear
        behaviour in case factor `fbeta` is set to value larger than one:

        >>> nfk(0., 0., 100., 100., 100, 100., 200.)
        >>> states.bowa = 0., 0., 60., 70., 80., 100., 200.
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 1.0, 1.2, 1.866667, 3.6, 7.6)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if ((con.lnk[k] == WASSER) or (con.lnk[k] == VERS) or
                (sta.bowa[k] <= der.wb[k]) or (con.nfk[k] <= 0.)):
            flu.qbb[k] = 0.
        elif sta.bowa[k] <= der.wz[k]:
            flu.qbb[k] = con.beta[k]*(sta.bowa[k]-der.wb[k])
        else:
            flu.qbb[k] = (con.beta[k]*(sta.bowa[k]-der.wb[k]) *
                          (1.+(con.fbeta[k]-1.)*((sta.bowa[k]-der.wz[k]) /
                                                 (con.nfk[k]-der.wz[k]))))


def calc_qib1_v1(self):
    """Calculate the first inflow component released from the soil.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.NFk`
      :class:`~hydpy.models.lland.lland_control.DMin`

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_derived.WB`

    Required state sequence:
      :class:`~hydpy.models.lland.lland_states.BoWa`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIB1`

    Basic equation:
      :math:`QIB1 = DMin \\cdot \\frac{BoWa}{NFk}`

    Examples:
        For water and sealed areas, no interflow is calculated (see the
        first two HRUs).  No principal distinction is made between the
        remaining land use classes (arable land has been selected for
        the other five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(7)
        >>> lnk(WASSER, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> dmax(10.)
        >>> dmin(4.)
        >>> nfk(0., 0., 0., 101., 101., 101., 202.)
        >>> derived.wb(10.)
        >>> states.bowa = 0., 0., 0., 0., 10., 10.1, 10.1

        Note the time dependence of parameter
        :class:`~hydpy.models.lland.lland_control.DMin`:

        >>> dmin
        dmin(4.0)
        >>> dmin.values
        array([ 2.,  2.,  2.,  2.,  2.,  2.,  2.])

        Compared to the calculation of
        :class:`~hydpy.models.lland.lland_fluxes.QBB`, the following
        results show some relevant differences:

        >>> model.calc_qib1_v1()
        >>> fluxes.qib1
        qib1(0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.1)

        Firstly, as demonstrated with the help of the sixths and the
        sevenths HRU the generation of first interflow component depends
        on the relative soil moisture.  Secondly, as demonstratd with the
        help the fifths and the sixths HRU, it starts abruptly whenever
        there is the slightest exceedance of the threshold  parameter
        :class:`~hydpy.models.lland.lland_derived.WB` occurs.  Such step
        functions are a potential source of trouble.
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if ((con.lnk[k] != WASSER) and (con.lnk[k] != VERS) and
                (sta.bowa[k] > der.wb[k])):
            flu.qib1[k] = con.dmin[k]*(sta.bowa[k]/con.nfk[k])
        else:
            flu.qib1[k] = 0.


def calc_qib2_v1(self):
    """Calculate the first inflow component released from the soil.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.NFk`
      :class:`~hydpy.models.lland.lland_control.DMin`
      :class:`~hydpy.models.lland.lland_control.DMax`

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_derived.WZ`

    Required state sequence:
      :class:`~hydpy.models.lland.lland_states.BoWa`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIB2`

    Basic equation:
      :math:`QIB2 = (DMax-DMin) \\cdot
      (\\frac{BoWa-WZ}{NFk-WZ})^\\frac{3}{2}`

    Examples:
        For water and sealed areas, no interflow is calculated (see the
        first two HRUs).  No principal distinction is made between the
        remaining land use classes (arable land has been selected for
        the other five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(7)
        >>> lnk(WASSER, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> dmax(10.)
        >>> dmin(4.)
        >>> nfk(0., 0., 50., 100., 100., 100., 200.)
        >>> derived.wz(50.)
        >>> states.bowa = 0., 0., 50.1, 50., 75., 100., 100.

        Note the time dependence of parameters
        :class:`~hydpy.models.lland.lland_control.DMin` (see the example
        above) and :class:`~hydpy.models.lland.lland_control.DMax`:

        >>> dmax
        dmax(10.0)
        >>> dmax.values
        array([ 5.,  5.,  5.,  5.,  5.,  5.,  5.])

        The following results show that he calculation of
        :class:`~hydpy.models.lland.lland_fluxes.QIB2` both resembles
        those of :class:`~hydpy.models.lland.lland_fluxes.QBB` and
        :class:`~hydpy.models.lland.lland_fluxes.QIB1` in some regards:

        >>> model.calc_qib2_v1()
        >>> fluxes.qib2
        qib2(0.0, 0.0, 0.0, 0.0, 1.06066, 3.0, 0.57735)

        In the given example, the maximum rate of total interflow
        generation is 5mm/12h.  For the sixths zone, which contains
        a saturated soil, a value of 3mm/h is calculated.  The "missing"
        2mm/12h would be added to the inflow concentration routine via
        :class:`~hydpy.models.lland.lland_fluxes.QIB1`.

        (The third zone, which is slightly oversaturated, is only intended
        to demonstrate that zero division due to nfk=wz is circumvented.)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nhru):
        if ((con.lnk[k] != WASSER) and (con.lnk[k] != VERS) and
                (sta.bowa[k] > der.wz[k]) and (con.nfk[k] > der.wz[k])):
            flu.qib2[k] = ((con.dmax[k]-con.dmin[k]) *
                           ((sta.bowa[k]-der.wz[k]) /
                            (con.nfk[k]-der.wz[k]))**1.5)
        else:
            flu.qib2[k] = 0.


def calc_qdb_v1(self):
    """Calculate direct runoff released from the soil.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`
      :class:`~hydpy.models.lland.lland_control.NFk`
      :class:`~hydpy.models.lland.lland_control.BSF`

    Required state sequence:
      :class:`~hydpy.models.lland.lland_states.BoWa`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.WaDa`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QDB`

    Basic equations:
      :math:`QDB = \\Bigl \\lbrace
      {
      {max(Exz, 0) \\ | \\ SfA \\leq 0}
      \\atop
      {max(Exz + NFk \\cdot SfA^{BSf+1}, 0) \\ | \\ SfA > 0}
      }`
      :math:`SFA = (1 - \\frac{BoWa}{NFk})^\\frac{1}{BSf+1} -
      \\frac{WaDa}{(BSf+1) \\cdot NFk}`
      :math:`Exz = (BoWa + WaDa) - NFk`


    Examples:
        For water areas, sealed areas, and areas without any soil storage
        capacity, all water is completely routed as direct runoff (see the
        first three HRUs).  No principal distinction is made between the
        remaining land use classes (arable land has been selected for
        the other five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(8)
        >>> lnk(WASSER, VERS, ACKER, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> bsf(0.4)
        >>> nfk(0., 0., 0., 100., 100., 100., 100., 100.)
        >>> fluxes.wada = 10.
        >>> states.bowa = 0., 0., 0., -.1, 0., 50., 100., 100.1
        >>> model.calc_qdb_v1()
        >>> fluxes.qdb
        qdb(10.0, 10.0, 10.0, 0.142039, 0.144959, 1.993649, 10.0, 10.1)

        With the common bsf value of 0.4, the discharge coefficient
        increases more or less exponentially with soil moisture.
        For soil moisture values slightly below zero or above usable
        field capacity, plausible amounts of generated direct runoff
        are ensured.
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    aid = self.sequences.aides.fastaccess
    for k in range(con.nhru):
        if ((con.lnk[k] != WASSER) and (con.lnk[k] != VERS) and
                (con.nfk[k] > 0.)):
            if sta.bowa[k] < con.nfk[k]:
                aid.sfa[k] = (
                    (1.-sta.bowa[k]/con.nfk[k])**(1./(con.bsf[k]+1.)) -
                    (flu.wada[k]/((con.bsf[k]+1.)*con.nfk[k])))
            else:
                aid.sfa[k] = 0.
            aid.exz[k] = sta.bowa[k]+flu.wada[k]-con.nfk[k]
            flu.qdb[k] = aid.exz[k]
            if aid.sfa[k] > 0.:
                flu.qdb[k] += aid.sfa[k]**(con.bsf[k]+1.)*con.nfk[k]
            flu.qdb[k] = max(flu.qdb[k], 0.)
        else:
            flu.qdb[k] = flu.wada[k]


def calc_bowa_v1(self):
    """Update soil moisture and correct fluxes if necessary.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.WaDa`

    Updated state sequence:
      :class:`~hydpy.models.lland.lland_states.BoWa`

    Required (and eventually corrected) flux sequences:
      :class:`~hydpy.models.lland.lland_fluxes.EvB`
      :class:`~hydpy.models.lland.lland_fluxes.QBB`
      :class:`~hydpy.models.lland.lland_fluxes.QIB1`
      :class:`~hydpy.models.lland.lland_fluxes.QIB2`
      :class:`~hydpy.models.lland.lland_fluxes.QDB`

    Basic equations:
       :math:`\\frac{dBoWa}{dt} = WaDa - EvB - QBB - QIB1 - QIB2 - QDB`
       :math:`BoWa \\geq 0`

    Examples:
        For water areas and sealed areas, soil moisture is simply set to
        zero and no flux corrections need not be performed.  No principal
        distinction is made between the remaining land use classes (arable
        land has been selected for the other four HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(6)
        >>> lnk(WASSER, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> states.bowa = 2.
        >>> fluxes.wada = 1.
        >>> fluxes.evb(0., 0., 0., .1, .2, .3)
        >>> fluxes.qbb(0., 0., 0., .2, .4, .6)
        >>> fluxes.qib1(0., 0., 0., .3, .6, .9)
        >>> fluxes.qib2(0., 0., 0., .4, .8, 1.2)
        >>> fluxes.qdb(0., 0., 0., .5, 1., 1.5)
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 3.0, 1.5, 0.0, 0.0)
        >>> fluxes.evb
        evb(0.0, 0.0, 0.0, 0.1, 0.2, 0.2)
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 0.2, 0.4, 0.4)
        >>> fluxes.qib1
        qib1(0.0, 0.0, 0.0, 0.3, 0.6, 0.6)
        >>> fluxes.qib2
        qib2(0.0, 0.0, 0.0, 0.4, 0.8, 0.8)
        >>> fluxes.qdb
        qdb(0.0, 0.0, 0.0, 0.5, 1.0, 1.0)

        For the sixths HRU, the original loss terms would result in
        negative soil moisture values.  They are corrected to the same
        loss terms of the fifths HRU, which result in a complete
        emptying of the soil storage exactly.
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    aid = self.sequences.aides.fastaccess
    for k in range(con.nhru):
        if (con.lnk[k] != WASSER) and (con.lnk[k] != VERS):
            aid.bvl[k] = (flu.evb[k] +
                          flu.qbb[k]+flu.qib1[k]+flu.qib2[k]+flu.qdb[k])
            aid.mvl[k] = sta.bowa[k]+flu.wada[k]
            if aid.bvl[k] > aid.mvl[k]:
                aid.rvl[k] = aid.mvl[k]/aid.bvl[k]
                flu.evb[k] *= aid.rvl[k]
                flu.qbb[k] *= aid.rvl[k]
                flu.qib1[k] *= aid.rvl[k]
                flu.qib2[k] *= aid.rvl[k]
                flu.qdb[k] *= aid.rvl[k]
                sta.bowa[k] = 0.
            else:
                sta.bowa[k] = aid.mvl[k]-aid.bvl[k]
        else:
            sta.bowa[k] = 0.


def calc_qbgz_v1(self):
    """Aggregate the amount of base flow released by all HRUs.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.FHRU`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QBB`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QBGZ`

    Basic equation:
       :math:`QBGZ = \\Sigma(FHRU \\cdot QBB)`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, ACKER)
        >>> fhru(.75, .25)
        >>> fluxes.qbb = 1., 5.
        >>> model.calc_qbgz_v1()
        >>> states.qbgz
        qbgz(2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    sta.qbgz = 0.
    for k in range(con.nhru):
        sta.qbgz += con.fhru[k]*flu.qbb[k]


def calc_qigz1_v1(self):
    """Aggregate the amount of the first interflow component released
    by all HRUs.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.FHRU`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIB1`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIGZ1`

    Basic equation:
       :math:`QIGZ1 = \\Sigma(FHRU \\cdot QIB1)`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, ACKER)
        >>> fhru(.75, .25)
        >>> fluxes.qib1 = 1., 5.
        >>> model.calc_qigz1_v1()
        >>> states.qigz1
        qigz1(2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    sta.qigz1 = 0.
    for k in range(con.nhru):
        sta.qigz1 += con.fhru[k]*flu.qib1[k]


def calc_qigz2_v1(self):
    """Aggregate the amount of the second interflow component released
    by all HRUs.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.FHRU`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIB2`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIGZ2`

    Basic equation:
       :math:`QIGZ2 = \\Sigma(FHRU \\cdot QIB2)`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, ACKER)
        >>> fhru(.75, .25)
        >>> fluxes.qib2 = 1., 5.
        >>> model.calc_qigz2_v1()
        >>> states.qigz2
        qigz2(2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    sta.qigz2 = 0.
    for k in range(con.nhru):
        sta.qigz2 += con.fhru[k]*flu.qib2[k]


def calc_qdgz_v1(self):
    """Aggregate the amount of direct flow released by all HRUs.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.FHRU`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QDB`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QDGZ`

    Basic equation:
       :math:`QDGZ = \\Sigma(FHRU \\cdot QDB)`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, ACKER)
        >>> fhru(.75, .25)
        >>> fluxes.qdb = 1., 5.
        >>> model.calc_qdgz_v1()
        >>> states.qdgz
        qdgz(2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    sta.qdgz = 0.
    for k in range(con.nhru):
        sta.qdgz += con.fhru[k]*flu.qdb[k]


def calc_qbga_v1(self):
    """Perform the runoff concentration calculation for base flow.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_control.KB`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QBGZ`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QBGA`

    Basic equation:
       :math:`QBGA_{neu} = QBGA_{alt} +
       (QBGZ_{alt}-QBGA_{alt}) \\cdot (1-exp(-KB^{-1})) +
       (QBGZ_{neu}-QBGZ_{alt}) \\cdot (1-KB\\cdot(1-exp(-KB^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kb(0.1)
        >>> states.qbgz.old = 2.
        >>> states.qbgz.new = 4.
        >>> states.qbga.old = 3.
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kb(0.)
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kb(1e200)
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(5.0)
    """
    der = self.parameters.derived.fastaccess
    old = self.sequences.states.fastaccess_old
    new = self.sequences.states.fastaccess_new
    aid = self.sequences.aides.fastaccess
    if der.kb <= 0.:
        new.qbga = new.qbgz
    elif der.kb > 1e200:
        new.qbga = old.qbga+new.qbgz-old.qbgz
    else:
        aid.temp = (1.-modelutils.exp(-1./der.kb))
        new.qbga = (old.qbga +
                    (old.qbgz-old.qbga)*aid.temp +
                    (new.qbgz-old.qbgz)*(1.-der.kb*aid.temp))


def calc_qiga1_v1(self):
    """Perform the runoff concentration calculation for the first
    interflow component.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_control.KI1`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIGZ1`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIGA1`

    Basic equation:
       :math:`QIGA1_{neu} = QIGA1_{alt} +
       (QIGZ1_{alt}-QIGA1_{alt}) \\cdot (1-exp(-KI1^{-1})) +
       (QIGZ1_{neu}-QIGZ1_{alt}) \\cdot (1-KI1\\cdot(1-exp(-KI1^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.ki1(0.1)
        >>> states.qigz1.old = 2.
        >>> states.qigz1.new = 4.
        >>> states.qiga1.old = 3.
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.ki1(0.)
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.ki1(1e200)
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(5.0)
    """
    der = self.parameters.derived.fastaccess
    old = self.sequences.states.fastaccess_old
    new = self.sequences.states.fastaccess_new
    aid = self.sequences.aides.fastaccess
    if der.ki1 <= 0.:
        new.qiga1 = new.qigz1
    elif der.ki1 > 1e200:
        new.qiga1 = old.qiga1+new.qigz1-old.qigz1
    else:
        aid.temp = (1.-modelutils.exp(-1./der.ki1))
        new.qiga1 = (old.qiga1 +
                     (old.qigz1-old.qiga1)*aid.temp +
                     (new.qigz1-old.qigz1)*(1.-der.ki1*aid.temp))


def calc_qiga2_v1(self):
    """Perform the runoff concentration calculation for the second
    interflow component.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_control.KI2`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIGZ2`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QIGA2`

    Basic equation:
       :math:`QIGA2_{neu} = QIGA2_{alt} +
       (QIGZ2_{alt}-QIGA2_{alt}) \\cdot (1-exp(-KI2^{-1})) +
       (QIGZ2_{neu}-QIGZ2_{alt}) \\cdot (1-KI2\\cdot(1-exp(-KI2^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.ki2(0.1)
        >>> states.qigz2.old = 2.
        >>> states.qigz2.new = 4.
        >>> states.qiga2.old = 3.
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.ki2(0.)
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.ki2(1e200)
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(5.0)
    """
    der = self.parameters.derived.fastaccess
    old = self.sequences.states.fastaccess_old
    new = self.sequences.states.fastaccess_new
    aid = self.sequences.aides.fastaccess
    if der.ki2 <= 0.:
        new.qiga2 = new.qigz2
    elif der.ki2 > 1e200:
        new.qiga2 = old.qiga2+new.qigz2-old.qigz2
    else:
        aid.temp = (1.-modelutils.exp(-1./der.ki2))
        new.qiga2 = (old.qiga2 +
                     (old.qigz2-old.qiga2)*aid.temp +
                     (new.qigz2-old.qigz2)*(1.-der.ki2*aid.temp))


def calc_qdga_v1(self):
    """Perform the runoff concentration calculation for direct runoff.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_derived.KD`

    Required flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QDGZ`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.QDGA`

    Basic equation:
       :math:`QDGA_{neu} = QDGA_{alt} +
       (QDGZ_{alt}-QDGA_{alt}) \\cdot (1-exp(-KD^{-1})) +
       (QDGZ_{neu}-QDGZ_{alt}) \\cdot (1-KD\\cdot(1-exp(-KD^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kd(0.1)
        >>> states.qdgz.old = 2.
        >>> states.qdgz.new = 4.
        >>> states.qdga.old = 3.
        >>> model.calc_qdga_v1()
        >>> states.qdga
        qdga(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kd(0.)
        >>> model.calc_qdga_v1()
        >>> states.qdga
        qdga(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kd(1e200)
        >>> model.calc_qdga_v1()
        >>> states.qdga
        qdga(5.0)
    """
    der = self.parameters.derived.fastaccess
    old = self.sequences.states.fastaccess_old
    new = self.sequences.states.fastaccess_new
    aid = self.sequences.aides.fastaccess
    if der.kd <= 0.:
        new.qdga = new.qdgz
    elif der.kd > 1e200:
        new.qdga = old.qdga+new.qdgz-old.qdgz
    else:
        aid.temp = (1.-modelutils.exp(-1./der.kd))
        new.qdga = (old.qdga +
                    (old.qdgz-old.qdga)*aid.temp +
                    (new.qdgz-old.qdgz)*(1.-der.kd*aid.temp))


def calc_q_v1(self):
    """Calculate the final runoff.

    Note that, in case there are water areas, their (interception)
    evaporation values are subtracted from the "potential" runoff value.

    Required control parameters:
      :class:`~hydpy.models.lland.lland_control.NHRU`
      :class:`~hydpy.models.lland.lland_control.FHRU`
      :class:`~hydpy.models.lland.lland_control.Lnk`

    Required flux sequences:
      :class:`~hydpy.models.lland.lland_fluxes.QBGA`
      :class:`~hydpy.models.lland.lland_fluxes.QIGA1`
      :class:`~hydpy.models.lland.lland_fluxes.QIGA2`
      :class:`~hydpy.models.lland.lland_fluxes.QDGA`
      :class:`~hydpy.models.lland.lland_fluxes.EvI`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_fluxes.Q`

    Basic equations:
       :math:`Q = QBGA + QIGA1 + QIGA2 + QDGA - EvI_{WASSER}`
       :math:`Q \\geq 0`

    Examples:

        When there are no water areas in the respective subbasin, the
        different runoff components are simply summed up:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER, VERS, NADELW)
        >>> fhru(0.5, 0.2, 0.3)
        >>> states.qbga = 1./4.
        >>> states.qiga1 = 2./4.
        >>> states.qiga2 = 3./4.
        >>> states.qdga = 4./4.
        >>> fluxes.evi = 4., 5., 3.
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(2.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        The defined values of interception evaporation do not show any
        impact on the result of the given example.  But when the first
        HRU is assumed to be a water area, its interception evaporation
        is subtracted:

        >>> control.lnk(WASSER, VERS, NADELW)
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(0.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        Note that only 2mm instead of 4mm are subtracted, as the first
        HRU`s area is only 50% of the subbasin area.

        Setting also the land use class of the second HRU to water would
        result in overtrying.  To avoid this, both water evaporation
        values are reduced by the same factor:


        >>> control.lnk(WASSER, WASSER, NADELW)
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(0.0)
        >>> fluxes.evi
        evi(3.333333, 4.166667, 3.0)

    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    aid = self.sequences.aides.fastaccess
    flu.q = sta.qbga+sta.qiga1+sta.qiga2+sta.qdga
    aid.epw = 0.
    for k in range(con.nhru):
        if con.lnk[k] == WASSER:
            aid.epw += con.fhru[k]*flu.evi[k]
    if flu.q > aid.epw:
        flu.q -= aid.epw
    else:
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.evi[k] *= flu.q/aid.epw
        flu.q = 0.


def update_outlets_v1(self):
    """Update the outlet link sequence.

    Required derived parameter:
      :class:`~hydpy.models.lland.lland_control.QFactor`

    Required flux sequences:
      :class:`~hydpy.models.lland.lland_fluxes.Q`

    Calculated flux sequence:
      :class:`~hydpy.models.lland.lland_links.Q`
    """
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    out = self.sequences.outlets.fastaccess
    out.q[0] += der.qfactor*flu.q


class Model(modeltools.Model):
    """Base model for HydPy-L-Land."""

    _RUNMETHODS = (calc_nkor_v1,
                   calc_tkor_v1,
                   calc_et0_v1,
                   calc_evpo_v1,
                   calc_nbes_inzp_v1,
                   calc_evi_inzp_v1,
                   calc_wgtf_v1,
                   calc_schm_wats_v1,
                   calc_wada_waes_v1,
                   calc_evb_v1,
                   calc_qbb_v1,
                   calc_qib1_v1,
                   calc_qib2_v1,
                   calc_qdb_v1,
                   calc_bowa_v1,
                   calc_qbgz_v1,
                   calc_qigz1_v1,
                   calc_qigz2_v1,
                   calc_qdgz_v1,
                   calc_qbga_v1,
                   calc_qiga1_v1,
                   calc_qiga2_v1,
                   calc_qdga_v1,
                   calc_q_v1,
                   update_outlets_v1)
