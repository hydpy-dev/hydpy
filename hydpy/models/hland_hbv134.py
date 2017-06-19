
# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...model specifc
from hydpy.models.hland import hland_model
from hydpy.models.hland import hland_control
from hydpy.models.hland import hland_derived
from hydpy.models.hland import hland_inputs
from hydpy.models.hland import hland_fluxes
from hydpy.models.hland import hland_states
from hydpy.models.hland import hland_aides
from hydpy.models.hland import hland_logs
from hydpy.models.hland import hland_links
from hydpy.models.hland.hland_parameters import Parameters
from hydpy.models.hland.hland_sequences import Sequences
from hydpy.models.hland.hland_constants import *
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

class Model(modeltools.Model):
    """HBV134 version of the HydPy-H-Land model.

    Integration test:
    """
    _RUNMETHODS = (hland_model.calc_tc_v1,
                   hland_model.calc_tmean_v1,
                   hland_model.calc_fracrain_v1,
                   hland_model.calc_rfc_sfc_v1,
                   hland_model.calc_pc_v1,
                   hland_model.calc_ep_v1,
                   hland_model.calc_epc_v1,
                   hland_model.calc_tf_ic_v1,
                   hland_model.calc_ei_ic_v1,
                   hland_model.calc_sp_wc_v1,
                   hland_model.calc_melt_sp_wc_v1,
                   hland_model.calc_refr_sp_wc_v1,
                   hland_model.calc_glmelt_in_v1,
                   hland_model.calc_in_wc_v1,
                   hland_model.calc_r_sm_v1,
                   hland_model.calc_cf_sm_v1,
                   hland_model.calc_ea_sm_v1,
                   hland_model.calc_inuz_v1,
                   hland_model.calc_contriarea_v1,
                   hland_model.calc_q0_perc_uz_v1,
                   hland_model.calc_lz_v1,
                   hland_model.calc_el_lz_v1,
                   hland_model.calc_q1_lz_v1,
                   hland_model.calc_inuh_v1,
                   hland_model.calc_outuh_quh_v1,
                   hland_model.calc_qt_v1,
                   hland_model.update_outlets_v1)

class ControlParameters(parametertools.SubParameters):
    """Control parameters of HBV134, directly defined by the user."""
    _PARCLASSES = (hland_control.Area,
                   hland_control.NmbZones,
                   hland_control.ZoneType,
                   hland_control.ZoneArea,
                   hland_control.ZoneZ,
                   hland_control.ZRelP,
                   hland_control.ZRelT,
                   hland_control.ZRelE,
                   hland_control.PCorr,
                   hland_control.PCAlt,
                   hland_control.RfCF,
                   hland_control.SfCF,
                   hland_control.TCAlt,
                   hland_control.ECorr,
                   hland_control.ECAlt,
                   hland_control.EPF,
                   hland_control.ETF,
                   hland_control.ERed,
                   hland_control.TTIce,
                   hland_control.IcMax,
                   hland_control.TT,
                   hland_control.TTInt,
                   hland_control.DTTM,
                   hland_control.CFMax,
                   hland_control.GMelt,
                   hland_control.CFR,
                   hland_control.WHC,
                   hland_control.FC,
                   hland_control.LP,
                   hland_control.Beta,
                   hland_control.PercMax,
                   hland_control.CFlux,
                   hland_control.RespArea,
                   hland_control.RecStep,
                   hland_control.Alpha,
                   hland_control.K,
                   hland_control.K4,
                   hland_control.Gamma,
                   hland_control.MaxBaz,
                   hland_control.Abstr)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HBV134, indirectly defined by the user."""
    _PARCLASSES = (hland_derived.RelZoneArea,
                   hland_derived.RelSoilArea,
                   hland_derived.RelSoilZoneArea,
                   hland_derived.RelLandZoneArea,
                   hland_derived.RelLandArea,
                   hland_derived.TTM,
                   hland_derived.DT,
                   hland_derived.NmbUH,
                   hland_derived.UH,
                   hland_derived.QFactor)

class InputSequences(sequencetools.InputSequences):
    """Input sequences of HBV134."""
    _SEQCLASSES = (hland_inputs.P,
                   hland_inputs.T,
                   hland_inputs.TN,
                   hland_inputs.EPN)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HBV134."""
    _SEQCLASSES = (hland_fluxes.TMean,
                   hland_fluxes.TC,
                   hland_fluxes.FracRain,
                   hland_fluxes.RfC,
                   hland_fluxes.SfC,
                   hland_fluxes.PC,
                   hland_fluxes.EP,
                   hland_fluxes.EPC,
                   hland_fluxes.EI,
                   hland_fluxes.TF,
                   hland_fluxes.TFWat,
                   hland_fluxes.TFIce,
                   hland_fluxes.GlMelt,
                   hland_fluxes.MeltPot,
                   hland_fluxes.Melt,
                   hland_fluxes.RefrPot,
                   hland_fluxes.Refr,
                   hland_fluxes.In_,
                   hland_fluxes.R,
                   hland_fluxes.EA,
                   hland_fluxes.CFPot,
                   hland_fluxes.CF,
                   hland_fluxes.Perc,
                   hland_fluxes.ContriArea,
                   hland_fluxes.InUZ,
                   hland_fluxes.Q0,
                   hland_fluxes.EL,
                   hland_fluxes.Q1,
                   hland_fluxes.InUH,
                   hland_fluxes.OutUH,
                   hland_fluxes.QT)

class StateSequences(sequencetools.StateSequences):
    """State sequences of HBV134."""
    _SEQCLASSES = (hland_states.Ic,
                   hland_states.SP,
                   hland_states.WC,
                   hland_states.SM,
                   hland_states.UZ,
                   hland_states.LZ)

class LogSequences(sequencetools.AideSequences):
    """Aide sequences of HBV134."""
    _SEQCLASSES = (hland_logs.QUH,)

class AideSequences(sequencetools.AideSequences):
    """Aide sequences of HBV134."""
    _SEQCLASSES = (hland_aides.Perc,
                   hland_aides.Q0)

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HBV134."""
    _SEQCLASSES = (hland_links.Q,)

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()