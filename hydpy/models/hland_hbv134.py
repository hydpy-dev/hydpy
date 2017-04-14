
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
    _OMITVERSION = True
    _METHODS = (hland_model.calc_tc_v1,
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
                hland_model.calc_qt_v1)

class ControlParameters(parametertools.SubParameters):
    """Control parameters of LARSIM-ME, directly defined by the user."""
    _PARCLASSES = (hland_control.FT,
                   hland_control.NHRU,
                   hland_control.FHRU,
                   hland_control.Lnk,
                   hland_control.HNN,
                   hland_control.KG,
                   hland_control.KT,
                   hland_control.KE,
                   hland_control.KF,
                   hland_control.FLn,
                   hland_control.HInz,
                   hland_control.LAI,
                   hland_control.TRefT,
                   hland_control.TRefN,
                   hland_control.TGr,
                   hland_control.GTF,
                   hland_control.RSchmelz,
                   hland_control.CPWasser,
                   hland_control.PWMax,
                   hland_control.GrasRef_R,
                   hland_control.NFk,
                   hland_control.RelWB,
                   hland_control.RelWZ,
                   hland_control.Beta,
                   hland_control.DMin,
                   hland_control.DMax,
                   hland_control.BSf,
                   hland_control.TInd,
                   hland_control.EQB,
                   hland_control.EQI1,
                   hland_control.EQI2,
                   hland_control.EQD)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of LARSIM-ME, indirectly defined by the user."""
    _PARCLASSES = (hland_derived.MOY,
                   hland_derived.KInz,
                   hland_derived.WB,
                   hland_derived.WZ,
                   hland_derived.KB,
                   hland_derived.KI1,
                   hland_derived.KI2,
                   hland_derived.KD,
                   hland_derived.QFactor)

class InputSequences(sequencetools.InputSequences):
    """Input sequences of LARSIM-ME."""
    _SEQCLASSES = (hland_inputs.Nied,
                   hland_inputs.TemL,
                   hland_inputs.Glob)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of LARSIM-ME."""
    _SEQCLASSES = (hland_fluxes.NKor,
                   hland_fluxes.TKor,
                   hland_fluxes.ET0,
                   hland_fluxes.EvPo,
                   hland_fluxes.NBes,
                   hland_fluxes.EvI,
                   hland_fluxes.EvB,
                   hland_fluxes.WGTF,
                   hland_fluxes.Schm,
                   hland_fluxes.WaDa,
                   hland_fluxes.QDB,
                   hland_fluxes.QIB1,
                   hland_fluxes.QIB2,
                   hland_fluxes.QBB,
                   hland_fluxes.Q)

class StateSequences(sequencetools.StateSequences):
    """State sequences of LARSIM-ME."""
    _SEQCLASSES = (hland_states.Inzp,
                   hland_states.WATS,
                   hland_states.WAeS,
                   hland_states.BoWa,
                   hland_states.WRel,
                   hland_states.QDGZ,
                   hland_states.QIGZ1,
                   hland_states.QIGZ2,
                   hland_states.QBGZ,
                   hland_states.QDGA,
                   hland_states.QIGA1,
                   hland_states.QIGA2,
                   hland_states.QBGA)

class AideSequences(sequencetools.AideSequences):
    """Aide sequences of LARSIM-ME."""
    _SEQCLASSES = (hland_aides.Temp,
                   hland_aides.SfA,
                   hland_aides.Exz,
                   hland_aides.BVl,
                   hland_aides.MVl,
                   hland_aides.RVl,
                   hland_aides.EPW)

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of LARSIM-ME."""
    _SEQCLASSES = (hland_links.Q,)

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()