# -*- coding: utf-8 -*-
"""The equations of HydPy-GlobWat model can be differentiated into two
groups. First the vertical water balance an second the horizontal water balance.
The vertical water balance ic calculated per grid cell. The horizontal water
balance is calculated per catchment. This models is primarily developt to
calculate the evaporation.
"""

# imports...
# ...standard library
from __future__ import division, print_function
# ...third party
import numpy
# ...HydPy specific
from hydpy.core import modeltools
# ...model specifc
from hydpy.models.globwat.globwat_constants import *

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
The following calculations are for step 1 'vertical water balance'
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def calc_rainfedevaporation_v1(self):
    """Calculate the rainfed evaporation.

    Required control parameters:
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`
      :class:`~hydpy.models.globwat.globwat_control.KC`
      :class:`~hydpy.models.globwat.globwat_control.VegetationClass`

    Required derived parameters:
      :class:`~hydpy.models.globwat.globwat_derived.SMax`
      :class:`~hydpy.models.globwat.globwat_derived.SEAv`
      :class:`~hydpy.models.globwat.globwat_derived.MOY`
      :class:`~hydpy.models.globwat.globwat_derived.Irrigation`

    Required input sequence:
      :class:`~hydpy.models.globwat.globwat_inputs.E0`

    Required state sequence:
      :class:`~hydpy.models.globwat.globwat_states.S`

    Calculated flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.ERain`

    Additional requirements:
      :attr:`~hydpy.core.modeltools.Model.idx_sim`

    Basic equation:
      :math:`E_{rain} = K_c \\cdot E_0`

    Calculating Erain for the case: S(t-1) <= Smax and S(t-1) >= Seav

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)
        >>> vegetationclass(WATER, DESERT, IRRCPR)
        >>> inputs.e0 = 3.
        >>> derived.seav(1.5, 2., 2.5)
        >>> derived.smax(10., 11., 12.)
        >>> kc.shape = 31, 12
        >>> kc.water[:3] = 1.1
        >>> kc.desert[:3] = .7
        >>> kc.irrcpr[:3] = 1.
        >>> states.fastaccess_old.s = 4., 5., 6.
        >>> derived.moy = [1,2,3]
        >>> derived.irrigation.update()
        >>> model.idx_sim = 0
        >>> model.calc_rainfedevaporation_v1()
        >>> fluxes.erain
        erain(0.0, 2.1, 0.0)

    #Calculating Erain for the case: S(t-1) < Seav

        >>> derived.seav(7., 8., 9.)
        >>> states.fastaccess_old.s = 4., 5., 6.
        >>> model.calc_rainfedevaporation_v1()
        >>> fluxes.erain
        erain(0.0, 1.3125, 0.0)
   """

    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    old = self.sequences.states.fastaccess_old

    for k in range(con.nmbgrids):
        if ((con.vegetationclass[k] == WATER) or (der.irrigation[k] == True)):
            flu.erain[k] = 0.
        elif old.s[k] < der.seav[k]:
            flu.erain[k] = ((con.kc[con.vegetationclass[k]-1, der.moy[self.idx_sim]] * inp.e0[k] * old.s[k]) / der.seav[k])
        else:
            flu.erain[k] = con.kc[con.vegetationclass[k]-1, der.moy[self.idx_sim]] * inp.e0[k]

def calc_groundwaterrecharge_v1(self):
    """Calculate the rate of ground water recharge.

    Required control parameters:
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`
      :class:`~hydpy.models.globwat.globwat_control.Rmax`
      :class:`~hydpy.models.globwat.globwat_control.VegetationClass`

    Required derived parameters:
      :class:`~hydpy.models.globwat.globwat_derived.SMax`
      :class:`~hydpy.models.globwat.globwat_derived.SEAv`

    Required state sequences:
      :class:`~hydpy.models.globwat.globwat_states.S`

    Calculated state sequence:
      :class:`~hydpy.models.globwat.globwat_states.R`

    Basic equation:
      :math:`R = \\frac {R_{max} \\cdot (S(t-1) - S_{eav})}{S_{max} - S_{eav}}`

    Calculating R for the case: S(t-1) <= Smax and S(t-1) > Seav

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)
        >>> vegetationclass(WATER, DESERT, IRRCPR)
        >>> control.rmax = 3., 3., 3.
        >>> derived.seav(1.5, 2., 2.5)
        >>> derived.smax(10., 11., 12.)
        >>> states.fastaccess_old.s = 4., 5., 6.
        >>> model.calc_groundwaterrecharge_v1()
        >>> states.r
        r(0.0, 1.0, 1.105263)

    Calculating R for the case: S(t-1) < Seav

    Examples:
        >>> derived.seav(7., 8., 9.)
        >>> states.fastaccess_old.s = 4., 10., 6.
        >>> model.calc_groundwaterrecharge_v1()
        >>> states.r
        r(0.0, 2.0, 0.0)
    """

    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    old = self.sequences.states.fastaccess_old
    sta = self.sequences.states.fastaccess

    for k in range(con.nmbgrids):
        if (con.vegetationclass[k] == WATER) or (old.s[k] < der.seav[k]):
            sta.r[k] = 0.
        elif (old.s[k] > der.smax[k]) or (der.smax[k] <= der.seav[k]):
            sta.r[k] = con.rmax[k]
        else:
            sta.r[k] = ((con.rmax[k] * (old.s[k] - der.seav[k])) / (der.smax[k] - der.seav[k]))


def calc_changeinstorage_v1(self):
    """Calculate the change of soil storage volume.

    Required control parameters:
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`
      :class:`~hydpy.models.globwat.globwat_control.VegetationClass`
      :class:`~hydpy.models.globwat.globwat_control.ROFactor`

    Required derived parameter:
      :class:`~hydpy.models.globwat.globwat_derived.SMax`

    Required input sequence:
      :class:`~hydpy.models.globwat.globwat_inputs.P`

    Required state sequence:
      :class:`~hydpy.models.globwat.globwat_states.R`

    Required flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.ERain`

    Calculated state sequences:
      :class:`~hydpy.models.globwat.globwat_states.B`
      :class:`~hydpy.models.globwat.globwat_states.S`

    Calculated flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.RO`

    Basic equation:
      :math:`B = S(t-1) - (P(t) - E_{rain}(t) - R(t)) \\cdot \\delta t`

    Calculating for: B < Smax

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)
        >>> vegetationclass(WATER, FOREST, DESERT)
        >>> derived.smax(4.25, 4.25, 4.25)
        >>> states.s.old = 1., 2., 3.
        >>> states.s.new = 5., 6., 7.
        >>> inputs.p = 3.
        >>> fluxes.erain = 2., 2., 2.
        >>> states.r = .5, .5, .5
        >>> model.calc_changeinstorage_v1()
        >>> states.b
        b(0.0, 6.0, 7.0)

    Calculating for: B >= Smax

    Examples:
        >>> states.s.old = 4., 5., 6.
        >>> states.s.new = 5., 6., 7.
        >>> model.calc_changeinstorage_v1()
        >>> states.b
        b(0.0, 4.25, 4.25)
    """

    sta = self.sequences.states.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    new = self.sequences.states.fastaccess_new
    old = self.sequences.states.fastaccess_old

    for k in range(con.nmbgrids):
        if con.vegetationclass[k] != WATER:
            sta.b[k] = old.s[k] + (inp.p[k] * (1 - con.rofactor) - flu.erain[k] - sta.r[k])
            if sta.b[k] < der.smax[k]:
                sta.b[k] = new.s[k]
                flu.ro[k] = 0.

            else:
                flu.ro[k] = (sta.b[k] - der.smax[k])
                sta.b[k] = der.smax[k]
            flu.ro[k] += inp.p[k] * con.rofactor

        else:
            flu.ro[k] = 0.
            sta.b[k] = 0.

def calc_irrigatedcropsevaporation_v1(self):
    """calculate the total evaporation for all crops under irrigation.

    Required control parameters:
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`
      :class:`~hydpy.models.globwat.globwat_control.KC`
      :class:`~hydpy.models.globwat.globwat_control.VegetationClass`
      :class:`~hydpy.models.globwat.globwat_control.Irrigation`

    Required input sequence:
      :class:`~hydpy.models.globwat.globwat_inputs.E0`

    Required derived parameter:
      :class:`~hydpy.models.globwat.globwat_derived.MOY`

    Calculated flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.EC`

    Additional requirements:
      :attr:`~hydpy.core.modeltools.Model.idx_sim`

    Basic equation:
      :math:`E_{c,total} = I_A \\cdot \\sum(C_{ic} \\cdot E_C)`

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)
        >>> vegetationclass(IRRCPR, RADRYTROP, IRRCNPR)
        >>> kc.irrcpr[:3] = 1.
        >>> kc.radrytrop[:3] = .90
        >>> kc.irrcnpr[:3] = 1.
        >>> derived.irrigation.update()
        >>> inputs.e0(3.)
        >>> derived.moy = [1,2,3]
        >>> model.idx_sim = 0
        >>> model.calc_irrigatedcropsevaporation_v1()
        >>> fluxes.ec
        ec(3.0, 0.0, 3.0)
    """

    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess

    for k in range(con.nmbgrids):
        if der.irrigation[k] == True:
            flu.ec[k] = con.kc[con.vegetationclass[k]-1, der.moy[self.idx_sim]] * inp.e0[k]

        else:
            flu.ec[k] = 0.

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
The following calculations are for step 2 'horinzontal water balance'
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def calc_openwaterevaporation_v1(self):
    """calculate the evaporation over open water.

    Required control parameters:
      :class:`~hydpy.models.globwat.globwat_control.KC`
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`
      :class:`~hydpy.models.globwat.globwat_control.VegetationClass`

    Required derived parameter:
      :class:`~hydpy.models.globwat.globwat_derived.MOY`

    Required input sequence:
      :class:`~hydpy.models.globwat.globwat_inputs.E0`

    Calculated flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.EOW`

    Additional requirements:
      :attr:`~hydpy.core.modeltools.Model.idx_sim`

    Basic equation:
      :math:`E_{OW} = K_{OW} \\cdot E_0`

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)

    it is possible to name vegatationclass by number or name e.g. WATER = 11

        >>> vegetationclass(RADRYTROP, WATER, WATER)
        >>> kc(1.1)
        >>> inputs.e0 = 5.
        >>> inputs.p = 10.
        >>> derived.moy = [1,2,3]
        >>> model.idx_sim = 0
        >>> model.calc_openwaterevaporation_v1()
        >>> fluxes.eow
        eow(0.0, 5.5, 5.5)
        >>> fluxes.ro
        ro(0.0, 0.0, 0.0)
    """

    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    inp = self.sequences.inputs.fastaccess
    new = self.sequences.states.fastaccess_new

    for k in range(con.nmbgrids):
        if con.vegetationclass[k] == WATER:
            flu.eow[k] = con.kc[con.vegetationclass[k]-1, der.moy[self.idx_sim]] * inp.e0[k]
            new.s[k] = 0.

        else:
            flu.eow[k] = 0.

def calc_gridevaporation_v1(self):
    """merge different types off evaporation (ERain, EC, EOW) per grid cell to an single timeseries
       Note: only one single type of evaporation per grid cell is possible.

    Required control parameter:
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`

    Required flux sequences:
      :class:`~hydpy.models.globwat.globwat_fluxes.ERain`
      :class:`~hydpy.models.globwat.globwat_fluxes.EC`
      :class:`~hydpy.models.globwat.globwat_fluxes.EOW`

    Calculated flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.EGrid`

    Basic equation:
      :math:`E_{Grid} = E_{Rain} + E_C + E_{OW}`

    >>> from hydpy.models.globwat import *
    >>> parameterstep('1d')
    >>> nmbgrids(3)
    >>> fluxes.erain(1., 2., 3.)
    >>> fluxes.ec(2., 3., 1.)
    >>> fluxes.eow(3., 1., 2.)
    >>> model.calc_gridevaporation_v1()
    >>> fluxes.egrid
    egrid(6.0, 6.0, 6.0)
    """

    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess

    for k in range(con.nmbgrids):
        flu.egrid[k] = flu.erain[k] + flu.ec[k] + flu.eow[k]


def calc_openwaterbalance_v1(self):
    """calculate the water balance over open water on t.

    Required control parameters:
      :class:`~hydpy.models.globwat.globwat_control.KC`
      :class:`~hydpy.models.globwat.globwat_control.NmbGrids`
      :class:`~hydpy.models.globwat.globwat_control.VegetationClass`

    Required input sequence:
      :class:`~hydpy.models.globwat.globwat_inputs.P`

    Required flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.EOW`

    Calculated state sequence:
      :class:`~hydpy.models.globwat.globwat_states.BOW`

    Calculated flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.RO`

    Basic equation:
      :math:`B_{OW} = (P(t) - E_{OW}) \\cdot \\delta t`

    Calculating for: BOW < 0.

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)
        >>> inputs.p = 3.
        >>> fluxes.eow = 5.
        >>> vegetationclass(RADRYTROP, WATER, RAHIGHL)
        >>> model.calc_openwaterbalance_v1()
        >>> fluxes.ro
        ro(0.0, 0.0, 0.0)

    Calculating for: BOW >= 0.

        >>> inputs.p = 5.
        >>> fluxes.eow = 3.
        >>> model.calc_openwaterbalance_v1()
        >>> fluxes.ro
        ro(0.0, 2.0, 0.0)
       """

    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    inp = self.sequences.inputs.fastaccess

    for k in range(con.nmbgrids):
        if con.vegetationclass[k] == WATER:
            sta.bow[k] = inp.p[k] - flu.eow[k]
            if sta.bow[k] < 0.:
                flu.ro[k] = 0.
#                flu.eincrow[k] = (-1 * sta.bow[k])

            else:
                flu.ro[k] = sta.bow[k]
#                flu.erain[k] = flu.eow[k]
#                flu.eincrow[k] = 0.

def calc_subbasinbalance_v1(self):
    """calculate the (sub-)basin water balance on t.

    Required state sequence:
      :class:`~hydpy.models.globwat.globwat_states.Qin`

    Required input sequence:
      :class:`~hydpy.models.globwat.globwat_inputs.P`

    Required flux sequence:
      :class:`~hydpy.models.globwat.globwat_fluxes.EGrid`

    Calculated state sequence:
      :class:`~hydpy.models.globwat.globwat_states.Bsb`

    Basic equation:
      :math:`B_{sb} = Q_{in}(t) + \\sum P(t) - \\sum E(t)`

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(3)
        >>> states.qin(5.)
        >>> inputs.p(1)
        >>> fluxes.egrid(2.)
        >>> model.calc_subbasinbalance_v1()
        >>> states.bsb
        bsb(2.0)
    """

    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    inp = self.sequences.inputs.fastaccess

# hier aufpassen, es können negative Werte entstehen, wenn die Verdunstung hoch
# und Qin sowie Niederschlag gering sind
    sta.bsb = sta.qin + sum(inp.p) - sum(flu.egrid)

def calc_subbasinstorage_v1(self):
    """calculate the (sub-)basin storage on t.

    Required state sequences:
      :class:`~hydpy.models.globwat.globwat_states.Ssb`
      :class:`~hydpy.models.globwat.globwat_states.Bsb`
      :class:`~hydpy.models.globwat.globwat_states.Qout`

    Calculated state sequence:
      :class:`~hydpy.models.globwat.globwat_states.Ssb`

    Basic equation:
      :math:`S_{sb} = S_{sb}(t-1) + (B_{sb}(t) - Q_{out}(t-1)) \\cdot \\delta t`

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> states.ssb.old = 25.
        >>> states.bsb = 1.
        >>> states.qout.old = 6.
        >>> model.calc_subbasinstorage_v1()
        >>> states.ssb
        ssb(20.0)

        check for not negative subbasin storage

        >>> states.qout.old = 36.
        >>> model.calc_subbasinstorage_v1()
        >>> states.ssb
        ssb(0.0)
    """

    sta = self.sequences.states.fastaccess
    old = self.sequences.states.fastaccess_old

# äquivalent dazu kann bei langen Zeitreihen der Speicher des Gebiets irgendwann
# ebenfalls negativ werden --> physikalisch nicht möglich
# Abfrage die den minimalen Speicher auf Null begrenzt!?

    sta.ssb = old.ssb + sta.bsb - old.qout
    if sta.ssb < 0.:
        sta.ssb = 0.


def calc_outflow_v1(self):
    """calculate the (sub-)basin outflow on t.

    Required control parameter:
      :class:`~hydpy.models.globwat.globwat_control.F`

    Required state sequence:
      :class:`~hydpy.models.globwat.globwat_states.Ssb`

    Calculated state sequence:
      :class:`~hydpy.models.globwat.globwat_states.Qout`

    Basic equation:
      :math:`Q_{out}(t) = S_{sb}(t) \\cdot F`

    Examples:
        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> states.ssb(20.)
        >>> model.calc_outflow_v1()
        >>> states.qout
        qout(6.0)
    """

    sta = self.sequences.states.fastaccess
    con = self.parameters.control.fastaccess

    sta.qout = sta.ssb * con.f

def update_inlets_v1(self):
    """Update the inlet link sequence."""
    sta = self.sequences.states.fastaccess
    inl = self.sequences.outlets.fastaccess
    sta.qin = inl.q[0]

def update_outlets_v1(self):
    """Update the outlet link sequence."""
    sta = self.sequences.states.fastaccess
    out = self.sequences.outlets.fastaccess
    out.q[0] += sta.qout

class Model(modeltools.Model):
    """The HydPy-GlobWat model.

     Integration Test:

        The only two simulation steps are in august:

        >>> from hydpy import pub, Timegrid, Timegrids
        >>> pub.timegrids = Timegrids(Timegrid('01.08.2000', '03.08.2000', '1d'))

        Import the model and define the time settings:

        >>> from hydpy.models.globwat import *
        >>> parameterstep('1d')
        >>> nmbgrids(5)

        Do things that are normally done behind the scenes. First, the input
        data shall be available in RAM:

        >>> import numpy
        >>> for (name, seq) in inputs:
        ...     seq.ramflag = True
        ...     seq._setarray(numpy.zeros(2))

        Secondly, the final model output shall be passed to `result`:

        >>> from hydpy.cythons.pointer import Double
        >>> result = Double(0.)
        >>> outlets.q.setpointer(result)

        Define the control parameter values (select only arable land, sealed
        soil and water area as landuse classes, as all other land use classes
        are functionally identical with arable land):

        >>> vegetationclass(IRRCNPR, WATER, IRRCPR, RADRYTROP, WATER)
        >>> area(15., 20., 18., 35., 12.)
        >>> scmax(5., 7., 20., 10., 5.)
        >>> rtd(.6, .6, .6, .6, .6)
        >>> rmax(9. ,5. ,2. ,3. ,10.)
        >>> kc.irrcnpr = 1.
        >>> kc.water = 1.1
        >>> kc.irrcpr = 1.
        >>> kc.radrytrop = .9

        Update the values of all derived parameters:

        >>> model.parameters.update()

        Set the initial values:

        >>> states.fastaccess_old.s = 10., 20., 30., 40., 10.
        >>> states.qin = 50.
        >>> states.fastaccess_old.qout = 15.

        Set the input values for both simulation time steps:

        >>> inputs.p.series = 3.
        >>> inputs.e0.series = 2.

        Check the correctness of the results:

        >>> model.doit(0)
        >>> print(round(result[0], 6))
        0.0
        >>> result[0] = 0.
        >>> model.doit(1)
        >>> print(round(result[0], 6))
        1.44
    """

    _RUNMETHODS = (update_inlets_v1,
                   calc_rainfedevaporation_v1,
                   calc_groundwaterrecharge_v1,
                   calc_changeinstorage_v1,
                   calc_irrigatedcropsevaporation_v1,
                   calc_openwaterevaporation_v1,
                   calc_openwaterbalance_v1,
                   calc_gridevaporation_v1,
                   calc_subbasinbalance_v1,
                   calc_subbasinstorage_v1,
                   calc_outflow_v1,
                   update_outlets_v1)
