# -*- coding: utf-8 -*-
"""The equations of HydPy-GlobWat model can be differentiated into two
groups. First the vertical water balance an second the horizontal water balance.
The vertical water balance ic calculated per grid cell. The horizontal water 
balance is calculated per catchment.

:func:`~Model.precipitation`, and :func:`~Model.potentialevaporation`). 
Secondly, the differential equations are solved in an ad hoc manner (see 
methods :func:`~Model.precipitation`, :func:`~Model.interception`,
:func:`~Model.snow`, :func:`~Model.glacier`, :func:`~Model.soil`, 
:func:`~Model.upperzonelayer`, and :func:`~Model.lowerzonelayer`).
Thirdly, the simulated output runoff is modified (see methods
:func:`~Model.convolution` and :func:`~Model.abstraction`).
"""

# imports...
# ...standard library
from __future__ import division, print_function
# ...third party
import numpy
# ...HydPy specific
from hydpy.core import modeltools
# ...model specifc
from .globwat_constants import *

class Model(modeltools.Model):
    """The HydPy-GlobWat model."""

    def run(self, idx):
        """Apply all globwat simulation equations for the given time step.
        
        Note that all methods are performed sequentially --- order matters. 
        """
        # Prepare input data.
        self.temperature()
        self.precipitation()
        self.potentialevaporation()
        # Solve process equations.
        self.calc_rainfedevaporation()
        self.calc_groundwaterrecharge()
        self.calc_changeinstorage()
        self.calc_ec()        
        
        self.interception()
        self.snow()
        self.glacier()
        self.soil()
        self.upperzonelayer()
        self.lowerzonelayer()
        # Modify output data.
        self.convolution()
        self.abstraction()

    def calc_rainfedevaporation(self):    
        
        con = self.parameters.control.fastaccess
        der = self.parameters.control.fastaccess
        inp = self.sequences.inputs.fastaccess
        flu = self.sequences.fluxes.fastaccess
        sta = self.sequences.fluxes.fastaccess
        old = self.sequences.states.fastaccess_old
        #new = self.sequences.states.fastaccess_new
        
        for k in range(con.nmbgrids):
            if (sta.s.old <= der.smax and sta.s.old >= der.seav):         
                flu.erain[k] = con.kc * inp.e0[k]
            
            else:
                sta.s.old  < der.seav
                flu.erain[k] = ((con.kc * inp.e0[k] * old.s) / der.seav)
            
    def calc_groundwaterrecharge(self):
        
        con = self.parameters.control.fastaccess
        der = self.parameters.control.fastaccess
        sta = self.sequences.fluxes.fastaccess
        
        for k in range(con.nmbgrids):
            if (sta.s.old <= der.smax and sta.s.old > der.seav):
                sta.r[k] = (con.rmax * (sta.s.old - der.seav)) / (der.smax - der.seav)

            else:
                sta.s.old < der.seav
                sta.r[k] = 0.
    
    def calc_changeinstorage(self):
        
        sta = self.sequences.fluxes.fastaccess
        inp = self.sequences.inputs.fastaccess
        flu = self.sequences.fluxes.fastaccess
        con = self.parameters.control.fastaccess
        der = self.parameters.control.fastaccess
        
        for k in range(con.nmbgrids):        
            sta.b[k] = sta.s.old - (inp.p[k] - flu.erain[k] - flu.r0[k]) * timestep
            if sta.b[k] < der.smax:
                sta.b[k] = sta.s.new
                flu.r0[k] = 0.
                
            else:
                sta.b[k] >= der.smax
                sta.b[k] = der.smax
                flu.r0[k] = (sta.b[k] - der.smax) / timestep
    
    def calc_ec(self):
        
        flu = self.sequences.fluxes.fastaccess        
        inp = self.sequences.inputs.fastaccess        
        
        for k in range(con.nmbgrids):
            flu.ec[k] = con.kc * inp.e0[k]
        
    def calc_ectotal(self):
        
        for k in range(con.nmbgrids):
            
        
    
    
    def calc_incrirrevaporation(self):
        
        flu = self.sequences.fluxes.fastaccess        
        
        for k in range(con.nmbgrids):
            flu.eincrirr[k] = 
        
    def temperature(self):
        """Adjust the given the air temperature to the individual zones in
        accordance with their heights and calculate the areal mean temperature
        of the subbasin.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.TCAlt`
          :class:`~hydpy.models.hland.hland_control.ZoneZ`
          :class:`~hydpy.models.hland.hland_control.ZRelT`

        Required derived parameter:
          :class:`~hydpy.models.hland.hland_derived.RelZoneArea`

        Required input sequence:
          :class:`~hydpy.models.hland.hland_inputs.T`

        Calculated flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.TC`
          :class:`~hydpy.models.hland.hland_fluxes.TMean`
          
        
        Consider the following example.  Prepare two equally sized zones, the 
        first on lying at the reference height and the second one 200 meters 
        above:  
        
        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> _ = nmbzones(2), zrelt(2.), zonez(2., 4.)
        >>> model.parameters.derived.relzonearea(.5)

        Applying the usual temperature lapse rate of 0.6°C/100m does not 
        affect the temperature of the first zone but reduces the temperature 
        of the second zone by 1.2°C: 

        >>> tcalt(.6)
        >>> model.sequences.inputs.t.value = 5.
        >>> model.temperature()
        >>> print(model.sequences.fluxes.tc.values[0])
        5.0
        >>> print(model.sequences.fluxes.tc.values[1])
        3.8
        
        The areal mean temperature of the subbasin is decreased by 0.6°C 
        accordingly:
        
        >>> print(model.sequences.fluxes.tmean.value)
        4.4
        
        """
        con = self.parameters.control.fastaccess
        der = self.parameters.derived.fastaccess
        inp = self.sequences.inputs.fastaccess
        flu = self.sequences.fluxes.fastaccess
        flu.tmean = 0.
        for k in range(con.nmbzones):
            flu.tc[k] = inp.t-con.tcalt[k]*(con.zonez[k]-con.zrelt)
            flu.tmean += der.relzonearea[k]*flu.tc[k]

    def precipitation(self):
        """Adjust the given precipitation to the individual zones in
        accordance with their heights and perform some corrections, among
        which one depends on the precipitation type (rain/snow).

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.TT`,
          :class:`~hydpy.models.hland.hland_control.TTInt`
          :class:`~hydpy.models.hland.hland_control.PCorr`
          :class:`~hydpy.models.hland.hland_control.PCAlt`
          :class:`~hydpy.models.hland.hland_control.ZoneZ`
          :class:`~hydpy.models.hland.hland_control.ZRelP`
          :class:`~hydpy.models.hland.hland_control.RfCF`
          :class:`~hydpy.models.hland.hland_control.SfCF`

        Required input sequence:
          :class:`~hydpy.models.hland.hland_inputs.P`

        Required flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.TC`

        Calculated flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.FracRain`
          :class:`~hydpy.models.hland.hland_fluxes.RfC`
          :class:`~hydpy.models.hland.hland_fluxes.SfC`
          :class:`~hydpy.models.hland.hland_fluxes.PC`
         
        Consider the following example.  The calculations for each zone take 
        place independently and the zone type has no direct impact.  Here 
        five zones are initialized to allow for the demonstration of the
        different correction factors (and their combination):
        
        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(1)
        >>> _ = tt(0.), ttint(2.), zrelp(2.), zonez(3.)
        >>> model.sequences.inputs.p.value = 10.
        >>> pcorr(1.0, 1.2, 1.0, 1.0, 1.2)
        >>> pcalt(0.0, 0.1, 0.0, 0.0, 0.1)
        >>> rfcf (1.0, 1.0, 1.1, 1.0, 1.1)
        >>> sfcf (1.0, 1.0, 1.0, 1.3, 1.3)
              
        """
        con = self.parameters.control.fastaccess
        inp = self.sequences.inputs.fastaccess
        flu = self.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.fracrain[k] = ((flu.tc[k]-(con.tt[k]-con.ttint[k]/2.)) /
                               con.ttint[k])
            flu.fracrain[k] = min(max(flu.fracrain[k], 0.), 1.)
            flu.rfc[k] = flu.fracrain[k]*con.rfcf[k]
            flu.sfc[k] = (1.-flu.fracrain[k])*con.sfcf[k]
            flu.pc[k] = inp.p*con.pcorr[k]
            flu.pc[k] *= 1.+con.pcalt[k]*(con.zonez[k]-con.zrelp)
            flu.pc[k] *= flu.rfc[k]+flu.sfc[k]

    def potentialevaporation(self):
        """Calculate the areal mean of (uncorrected) potential evaporation
        for the subbasin, adjust it to the individual zones in accordance
        with their heights and perform some corrections, among which one
        depends on the actual precipitation.


        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ECorr`
          :class:`~hydpy.models.hland.hland_control.ETF`
          :class:`~hydpy.models.hland.hland_control.ECAlt`
          :class:`~hydpy.models.hland.hland_control.ZoneZ`
          :class:`~hydpy.models.hland.hland_control.ZRelE`
          :class:`~hydpy.models.hland.hland_control.EPF`

        Required input sequence:
          :class:`~hydpy.models.hland.hland_inputs.EPN`
          :class:`~hydpy.models.hland.hland_inputs.TN`

        Required flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.TMean`
          :class:`~hydpy.models.hland.hland_fluxes.PC`

        Calculated flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.EP`
          :class:`~hydpy.models.hland.hland_fluxes.EPC`
        """
        con = self.parameters.control.fastaccess
        inp = self.sequences.inputs.fastaccess
        flu = self.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.ep[k] = (con.ecorr[k]*inp.epn *
                         (1.+con.etf[k]*(flu.tmean-inp.tn)))
            flu.ep[k] = min(max(flu.ep[k], 0.), 2.*con.ecorr[k]*inp.epn)
            flu.epc[k] = (flu.ep[k] *
                          (1. - con.ecalt[k]*(con.zonez[k]-con.zrele)))
            #flu.epc[k] *= modeltools.exp(-con.epf[k]*flu.pc[k])
            flu.epc[k] *= numpy.exp(-con.epf[k]*flu.pc[k])

    def interception(self):
        """Perform the interception routine for for zones of type `field` and
        `forest`.  For zones of type `ilake` or `glacier` throughfall is
        identical with precipitation.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ZoneType`
          :class:`~hydpy.models.hland.hland_control.IcMax`

        Required flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.PC`
          :class:`~hydpy.models.hland.hland_fluxes.EPC`

        Calculated fluxes sequences:
          :class:`~hydpy.models.hland.hland_fluxes.TF`
          :class:`~hydpy.models.hland.hland_fluxes.EI`

        Updated state sequence:
          :class:`~hydpy.models.hland.hland_states.Ic`
        """
        con = self.parameters.control.fastaccess
        flu = self.sequences.fluxes.fastaccess
        old = self.sequences.states.fastaccess_old
        new = self.sequences.states.fastaccess_new
        for k in range(con.nmbzones):
            if ((con.zonetype[k] == FIELD) or
                    (con.zonetype[k] == FOREST)):
                # First state update related to precipitation.
                flu.tf[k] = max(flu.pc[k]-(con.icmax[k]-old.ic[k]), 0.)
                new.ic[k] = old.ic[k]+flu.pc[k]-flu.tf[k]
                # Second state update related to evaporation.
                flu.ei[k] = min(flu.epc[k], new.ic[k])
                new.ic[k] -= flu.ei[k]
            else:
                flu.tf[k] = flu.pc[k]

    def snow(self):
        """Perform the snow routine for zones of type `field`, `forest` and
        `glacier`.  For zones of type `ilake` water release is identical with
        throughfall.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ZoneType`
          :class:`~hydpy.models.hland.hland_control.CFMax`
          :class:`~hydpy.models.hland.hland_control.CFR`
          :class:`~hydpy.models.hland.hland_control.WHC`

        Required derived parameter:
          :class:`~hydpy.models.hland.hland_derived.TTM`

        Required flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.TF`
          :class:`~hydpy.models.hland.hland_fluxes.RfC`
          :class:`~hydpy.models.hland.hland_fluxes.SfC`
          :class:`~hydpy.models.hland.hland_fluxes.TC`

        Calculated fluxes sequences:
          :class:`~hydpy.models.hland.hland_fluxes.Melt`
          :class:`~hydpy.models.hland.hland_fluxes.Refr`
          :class:`~hydpy.models.hland.hland_fluxes.In_`

        Updated state sequences:
          :class:`~hydpy.models.hland.hland_states.WC`
          :class:`~hydpy.models.hland.hland_states.SP`
        """
        con = self.parameters.control.fastaccess
        der = self.parameters.derived.fastaccess
        flu = self.sequences.fluxes.fastaccess
        old = self.sequences.states.fastaccess_old
        new = self.sequences.states.fastaccess_new
        for k in range(con.nmbzones):
            if con.zonetype[k] != ILAKE:
                # First state update related to liquid/frozen throughfall.
                new.wc[k] = (old.wc[k] +
                             flu.tf[k]*flu.rfc[k]/(flu.rfc[k]+flu.sfc[k]))
                new.sp[k] = (old.sp[k] +
                             flu.tf[k]*flu.sfc[k]/(flu.rfc[k]+flu.sfc[k]))
                # Second state update related to melting/refreezing.
                if flu.tc[k] > der.ttm[k]:
                    flu.melt[k] = min(con.cfmax[k] *
                                      (flu.tc[k]-der.ttm[k]), new.sp[k])
                    flu.refr[k] = 0.
                else:
                    flu.melt[k] = 0.
                    flu.refr[k] = min(con.cfr[k]*con.cfmax[k] *
                                      (der.ttm[k]-flu.tc[k]), new.wc[k])
                new.wc[k] += flu.melt[k]-flu.refr[k]
                new.sp[k] += flu.refr[k]-flu.melt[k]
                # Third state update related to water release.
                flu.in_[k] = max(new.wc[k]-con.whc[k]*new.sp[k], 0.)
                new.wc[k] -= flu.in_[k]
            else:
                flu.in_ = flu.tf

    def glacier(self):
        """Perform the glacier routine for zones of type `glacier`, which
        releases water when the glacier is not covered by a snow  layer.
        For zones of type `field`, `forest` or `ilake` the water release of
        the (potential) snow layer remains unchanged.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ZoneType`
          :class:`~hydpy.models.hland.hland_control.GMelt`

        Required state sequence:
          :class:`~hydpy.models.hland.hland_states.SP`

        Calculated fluxes sequence:
          :class:`~hydpy.models.hland.hland_fluxes.GlMelt`

        Updated flux sequence:
          :class:`~hydpy.models.hland.hland_fluxes.In_`
        """
        con = self.parameters.control.fastaccess
        der = self.parameters.derived.fastaccess
        flu = self.sequences.fluxes.fastaccess
        new = self.sequences.states.fastaccess_new
        for k in range(con.nmbzones):
            if con.zonetype[k] == GLACIER:
                if (new.sp[k] == 0.) and (flu.tc[k] > der.ttm[k]):
                    flu.glmelt[k] = con.gmelt[k]*(flu.tc[k]-der.ttm[k])
                    flu.in_[k] += flu.glmelt[k]
                else:
                    flu.glmelt[k] = 0.

    def soil(self):
        """Perform the soil routine for zones of type `field` and `forest`.
        For zones of type `glacier` or `ilake` the effective response is
        identical with the water release of the snow layer and capillary flow
        as well as evaporation are zero.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ZoneType`
          :class:`~hydpy.models.hland.hland_control.FC`
          :class:`~hydpy.models.hland.hland_control.Beta`
          :class:`~hydpy.models.hland.hland_control.CFlux`
          :class:`~hydpy.models.hland.hland_control.LP`
          :class:`~hydpy.models.hland.hland_control.ERed`

        Required derived parameters:
          :class:`~hydpy.models.hland.hland_derived.RelLandZoneArea`

        Required fluxes sequence:
          :class:`~hydpy.models.hland.hland_fluxes.In_`
          :class:`~hydpy.models.hland.hland_fluxes.EPC`
          :class:`~hydpy.models.hland.hland_fluxes.EI`

        Required state sequence:
          :class:`~hydpy.models.hland.hland_states.SP`
          :class:`~hydpy.models.hland.hland_states.UZ`

        Calculated flux sequence:
          :class:`~hydpy.models.hland.hland_fluxes.R`
          :class:`~hydpy.models.hland.hland_fluxes.CF`
          :class:`~hydpy.models.hland.hland_fluxes.EA`
          :class:`~hydpy.models.hland.hland_fluxes.InUZ`

        Updated state sequence:
          :class:`~hydpy.models.hland.hland_states.SM`
        """
        con = self.parameters.control.fastaccess
        der = self.parameters.derived.fastaccess
        flu = self.sequences.fluxes.fastaccess
        old = self.sequences.states.fastaccess_old
        new = self.sequences.states.fastaccess_new
        flu.inuz = 0.
        for k in range(con.nmbzones):
            if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
                # First state update related to input and response.
                flu.r[k] = max(flu.in_[k]*(old.sm[k]/con.fc[k])**con.beta[k],
                               old.sm[k]+flu.in_[k]-con.fc[k])
                new.sm[k] = old.sm[k]+flu.in_[k]-flu.r[k]
                # Second state update related to capillary flow.
                flu.cf[k] = min(con.cflux[k]*(1.-new.sm[k]/con.fc[k]),
                                old.uz+flu.r[k])
                new.sm[k] += flu.cf[k]
                # Third state update related to actual evaporation.
                if new.sp[k] > 0.:
                    flu.ea[k] = 0.
                else:
                    flu.ea[k] = flu.epc[k]*min(new.sm[k]/(con.lp[k]*con.fc[k]),
                                               1.)
                    flu.ea[k] = min(flu.ea[k], new.sm[k])
                    # Reduce soil evaporation when the sum of interception and
                    # soil evaporation exceeds potential evaporation.
                    flu.ea[k] -= max(con.ered[k] *
                                     (flu.ea[k]+flu.ei[k]-flu.epc[k]), 0.)
                # subtract evaporation from soil moisture
                new.sm[k] -= flu.ea[k]
            else:
                # equate runoff with infiltration
                flu.r[k] = flu.in_[k]
            flu.inuz += der.rellandzonearea[k]*(flu.r[k]-flu.cf[k])

    def upperzonelayer(self):
        """Perform the upper zone layer routine which determines percolation
        to the lower zone layer and the fast response of the hland model.
        Note that the system behaviour of this method depends strongly on the
        specifications of the options :class:`RespArea` and :class:`RecStep`.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.RespArea`
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ZoneType`
          :class:`~hydpy.models.hland.hland_control.FC`
          :class:`~hydpy.models.hland.hland_control.Beta`
          :class:`~hydpy.models.hland.hland_control.RecStep`
          :class:`~hydpy.models.hland.hland_control.PercMax`
          :class:`~hydpy.models.hland.hland_control.K`
          :class:`~hydpy.models.hland.hland_control.Alpha`

        Required fluxes sequence:
          :class:`~hydpy.models.hland.hland_fluxes.InUZ`

        Required state sequence:
          :class:`~hydpy.models.hland.hland_states.SM`

        Used Aide sequences:
          :class:`~hydpy.models.hland.hland_aides.Perc`
          :class:`~hydpy.models.hland.hland_aides.Q0`

        Calculated fluxes sequences:
          :class:`~hydpy.models.hland.hland_fluxes.Perc`
          :class:`~hydpy.models.hland.hland_fluxes.Q0`

        Updated state sequence:
          :class:`~hydpy.models.hland.hland_states.UZ`
        """
        con = self.parameters.control.fastaccess
        der = self.parameters.derived.fastaccess
        flu = self.sequences.fluxes.fastaccess
        old = self.sequences.states.fastaccess_old
        new = self.sequences.states.fastaccess_new
        aid = self.sequences.aides.fastaccess
        # Calculate the `contributing area`, if necessary.
        if con.resparea and (der.nmbsoilzones > 0):
            flu.contriarea = .01
            for k in range(con.nmbzones):
                if (con.zonetype[k] == FIELD) or (con.zonetype[k] == FOREST):
                    flu.contriarea += (.99*der.relsoilzonearea[k]*
                                       (new.sm[k]/con.fc[k])**con.beta[k])
        else:
            flu.contriarea = 1.
        # The following upper zone layer calculations can be performed with a
        # smaller time step width to increase numerical accuracy.
        flu.perc = 0.
        flu.q0 = 0.
        new.uz = old.uz
        for jdx in range(con.recstep):
            # First state update related to the upper zone input.
            new.uz += der.dt*flu.inuz
            # Second state update related to percolation.
            aid.perc = min(der.dt*con.percmax*flu.contriarea, new.uz)
            new.uz -= aid.perc
            flu.perc += aid.perc
            # Third state update related to fast runoff response.
            aid.q0 = min(der.dt*con.k*(new.uz/flu.contriarea)**(1.+con.alpha),
                         new.uz)
            new.uz -= aid.q0
            flu.q0 += aid.q0

    def lowerzonelayer(self):
        """Perform the upper zone layer routine which determines the slow
        response of the hland model and, for zones of type `ilake`, lake
        evaporation.

        Required control parameters:
          :class:`~hydpy.models.hland.hland_control.NmbZones`
          :class:`~hydpy.models.hland.hland_control.ZoneType`
          :class:`~hydpy.models.hland.hland_control.TTIce`
          :class:`~hydpy.models.hland.hland_control.K4`
          :class:`~hydpy.models.hland.hland_control.Gamma`

        Required fluxes sequences:
          :class:`~hydpy.models.hland.hland_fluxes.Perc`
          :class:`~hydpy.models.hland.hland_fluxes.PC`
          :class:`~hydpy.models.hland.hland_fluxes.TC`
          :class:`~hydpy.models.hland.hland_fluxes.EPC`
          :class:`~hydpy.models.hland.hland_fluxes.Perc`

        Calculated fluxes sequences:
          :class:`~hydpy.models.hland.hland_fluxes.EA`
          :class:`~hydpy.models.hland.hland_fluxes.Q1`

        Updated state sequence:
          :class:`~hydpy.models.hland.hland_states.LZ`
        """
        con = self.parameters.control.fastaccess
        der = self.parameters.derived.fastaccess
        flu = self.sequences.fluxes.fastaccess
        old = self.sequences.states.fastaccess_old
        new = self.sequences.states.fastaccess_new
        # First state update related to percolation.
        new.lz = old.lz+der.rellandarea*flu.perc
        # Second and third state update related to lake...
        for k in range(con.nmbzones):
            if con.zonetype[k] == ILAKE:
                # ...precipitation.
                new.lz += der.relzonearea[k]*flu.pc[k]
                # ...evaporation.
                if flu.tc[k] > con.ttice[k]:
                    flu.ea[k] = flu.epc[k]
                else:
                    flu.ea[k] = 0.
                new.lz -= der.relzonearea[k]*flu.ea[k]
        # Fourth state update related to the slow runoff response.
        if new.lz > 0.:
            flu.q1 = con.k4*new.lz**(1.+con.gamma)
        else:
            flu.q1 = 0.
        new.lz -= flu.q1

    def convolution(self):
        """Apply HBV`s triangle unit hydrograph.

        Required derived parameters:
          :class:`~hydpy.models.hland.hland_derived.RelLandArea`
          :class:`~hydpy.models.hland.hland_derived.UH`
          :class:`~hydpy.models.hland.hland_derived.NmbUH`

        Required flux sequences:
          :class:`~hydpy.models.hland.hland_fluxes.Q0`
          :class:`~hydpy.models.hland.hland_fluxes.Q1`
          :class:`~hydpy.models.hland.hland_fluxes.InUH`

        Required and updated log sequence:
          :class:`~hydpy.models.hland.hland_logs.QUH`

        Calculated flux sequence:
          :class:`~hydpy.models.hland.hland_fluxes.OutUH`
        """
        der = self.parameters.derived.fastaccess
        flu = self.sequences.fluxes.fastaccess
        log = self.sequences.logs.fastaccess
        flu.inuh = der.rellandarea*flu.q0+flu.q1
        flu.outuh = der.uh[0]*flu.inuh+log.quh[0]
        for jdx in range(1, der.nmbuh):
            log.quh[jdx-1] = der.uh[jdx]*flu.inuh+log.quh[jdx]

    def abstraction(self):
        """Abstract water from model outflow.

        Required control parameter:
          :class:`~hydpy.models.hland.hland_control.Abstr`

        Required flux sequence:
          :class:`~hydpy.models.hland.hland_fluxes.OutUH`

        Calculated flux sequence:
          :class:`~hydpy.models.hland.hland_fluxes.QT`
        """
        con = self.parameters.control.fastaccess
        flu = self.sequences.fluxes.fastaccess
        flu.qt = max(flu.outuh-con.abstr, 0.)
