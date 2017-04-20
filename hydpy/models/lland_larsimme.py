
# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...model specifc
from hydpy.models.lland import lland_model
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_derived
from hydpy.models.lland import lland_inputs
from hydpy.models.lland import lland_fluxes
from hydpy.models.lland import lland_states
from hydpy.models.lland import lland_aides
from hydpy.models.lland import lland_links
from hydpy.models.lland.lland_parameters import Parameters
from hydpy.models.lland.lland_sequences import Sequences
from hydpy.models.lland.lland_constants import *
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

class Model(modeltools.Model):
    """LARSIM-ME version of the HydPy-L-Land model.

    Integration test:

        The only simulation step is in January:

        >>> from hydpy import pub
        >>> pub.indexer.monthofyear = [0]

        Import the model and primary the required time settings:

        >>> from hydpy.models.lland_larsimme import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> model.idx_sim = 0

        Define the control parameter values (select only arable land, sealed
        soil and water area as landuse classes, as all other land use classes
        are functionally identical with arable land):

        >>> ft(100.)
        >>> nhru(3)
        >>> fhru(1./3.)
        >>> lnk(ACKER, VERS, WASSER)
        >>> hnn(100.)
        >>> kg(1.2)
        >>> kt(-1.)
        >>> ke(0.9)
        >>> kf(.6)
        >>> fln.acker_jan = 1.
        >>> fln.vers_jan = .8
        >>> fln.wasser_jan = 1.3
        >>> hinz(.2)
        >>> lai.acker_jan = 1.0
        >>> treft(0.)
        >>> trefn(0.)
        >>> tgr(0.)
        >>> gtf(5.)
        >>> pwmax(1.4)
        >>> grasref_r(5.)
        >>> nfk(200.)
        >>> relwb(.05)
        >>> relwz(.5)
        >>> beta(.01)
        >>> dmin(1.)
        >>> dmax(5.)
        >>> bsf(.4)
        >>> tind(1.)
        >>> eqb(100.)
        >>> eqi1(50.)
        >>> eqi2(10.)
        >>> eqd(2.)

        Update the values of all derived parameters:

        >>> model.parameters.update()

        Set the initial values:



        >>> model.run()
    """
    _METHODS = (lland_model.calc_nkor_v1,
                lland_model.calc_tkor_v1,
                lland_model.calc_et0_v1,
                lland_model.calc_evpo_v1,
                lland_model.calc_nbes_inzp_v1,
                lland_model.calc_evi_inzp_v1,
                lland_model.calc_wgtf_v1,
                lland_model.calc_schm_wats_v1,
                lland_model.calc_wada_waes_v1,
                lland_model.calc_evb_v1,
                lland_model.calc_qbb_v1,
                lland_model.calc_qib1_v1,
                lland_model.calc_qib2_v1,
                lland_model.calc_qdb_v1,
                lland_model.calc_bowa_v1,
                lland_model.calc_qbgz_v1,
                lland_model.calc_qigz1_v1,
                lland_model.calc_qigz2_v1,
                lland_model.calc_qdgz_v1,
                lland_model.calc_qbga_v1,
                lland_model.calc_qiga1_v1,
                lland_model.calc_qiga2_v1,
                lland_model.calc_qdga_v1,
                lland_model.calc_q_v1,
                lland_model.update_outlets_v1)

class ControlParameters(parametertools.SubParameters):
    """Control parameters of LARSIM-ME, directly defined by the user."""
    _PARCLASSES = (lland_control.FT,
                   lland_control.NHRU,
                   lland_control.FHRU,
                   lland_control.Lnk,
                   lland_control.HNN,
                   lland_control.KG,
                   lland_control.KT,
                   lland_control.KE,
                   lland_control.KF,
                   lland_control.FLn,
                   lland_control.HInz,
                   lland_control.LAI,
                   lland_control.TRefT,
                   lland_control.TRefN,
                   lland_control.TGr,
                   lland_control.GTF,
                   lland_control.RSchmelz,
                   lland_control.CPWasser,
                   lland_control.PWMax,
                   lland_control.GrasRef_R,
                   lland_control.NFk,
                   lland_control.RelWB,
                   lland_control.RelWZ,
                   lland_control.Beta,
                   lland_control.DMin,
                   lland_control.DMax,
                   lland_control.BSf,
                   lland_control.TInd,
                   lland_control.EQB,
                   lland_control.EQI1,
                   lland_control.EQI2,
                   lland_control.EQD)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of LARSIM-ME, indirectly defined by the user."""
    _PARCLASSES = (lland_derived.MOY,
                   lland_derived.KInz,
                   lland_derived.WB,
                   lland_derived.WZ,
                   lland_derived.KB,
                   lland_derived.KI1,
                   lland_derived.KI2,
                   lland_derived.KD,
                   lland_derived.QFactor)

class InputSequences(sequencetools.InputSequences):
    """Input sequences of LARSIM-ME."""
    _SEQCLASSES = (lland_inputs.Nied,
                   lland_inputs.TemL,
                   lland_inputs.Glob)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of LARSIM-ME."""
    _SEQCLASSES = (lland_fluxes.NKor,
                   lland_fluxes.TKor,
                   lland_fluxes.ET0,
                   lland_fluxes.EvPo,
                   lland_fluxes.NBes,
                   lland_fluxes.EvI,
                   lland_fluxes.EvB,
                   lland_fluxes.WGTF,
                   lland_fluxes.Schm,
                   lland_fluxes.WaDa,
                   lland_fluxes.QDB,
                   lland_fluxes.QIB1,
                   lland_fluxes.QIB2,
                   lland_fluxes.QBB,
                   lland_fluxes.Q)

class StateSequences(sequencetools.StateSequences):
    """State sequences of LARSIM-ME."""
    _SEQCLASSES = (lland_states.Inzp,
                   lland_states.WATS,
                   lland_states.WAeS,
                   lland_states.BoWa,
                   lland_states.QDGZ,
                   lland_states.QIGZ1,
                   lland_states.QIGZ2,
                   lland_states.QBGZ,
                   lland_states.QDGA,
                   lland_states.QIGA1,
                   lland_states.QIGA2,
                   lland_states.QBGA)

class AideSequences(sequencetools.AideSequences):
    """Aide sequences of LARSIM-ME."""
    _SEQCLASSES = (lland_aides.Temp,
                   lland_aides.SfA,
                   lland_aides.Exz,
                   lland_aides.BVl,
                   lland_aides.MVl,
                   lland_aides.RVl,
                   lland_aides.EPW)

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of LARSIM-ME."""
    _SEQCLASSES = (lland_links.Q,)

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()