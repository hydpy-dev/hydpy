# -*- coding: utf-8 -*-
"""
Version 1 of the L-Land model is designed to aggree with the LARSIM-ME
configuration of the LARSIM model used by the German Federal Institute
of Hydrology, but offers more flexibility in some regards (e.g. in
parameterization).  It can briefly be summarized as follows:

 * Simple routines for adjusting the meteorological input data.
 * Reference evapotranspiration after Turc-Wendling.
 * Landuse and month specific potential evapotranspiration.
 *

Note that, due to the calculation of potential evapotranspiration with
the Turc-Wendling approach, the simulation step size should be on day.


Integration tests:

    The integration tests are performed in January (to allow for realistic
    snow examples), spanning over a period of five days:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '06.08.2000',
    ...                                    '1d'))

    Prepare the model instance and built the connections to element `land`
    and node `outlet`:

    >>> from hydpy.models.lland_v1 import *
    >>> parameterstep('1d')
    >>> from hydpy import Node, Element
    >>> outlet = Node('outlet')
    >>> land = Element('land', outlets=outlet)
    >>> land.connect(model)

    All tests shall be performed using one hydrological response unit only:

    >>> nhru(1)

    Initialize a test function object, which prepares and runs the tests
    and prints their results for the given sequences:

    >>> from hydpy.core.testtools import Test
    >>> test = Test(land,
    ...             (outlet.sequences.sim,))

    nö
    ...             {'inzp': (.5, .5, 0.),
    ...              'wats': (10., 10., 0.),
    ...              'waes': (15., 15., 0.),
    ...              'bowa': (150., 0., 0.),
    ...              'qdgz1': .1,
    ...              'qdgz2': .0,
    ...              'qigz1': .1,
    ...              'qigz2': .1,
    ...              'qbgz': .1,
    ...              'qdga1': .1,
    ...              'qdga2': .0,
    ...              'qiga1': .1,
    ...              'qiga2': .1,
    ...              'qbga': .1})

    Define the control parameter values (select only arable land, sealed
    soil and water area as landuse classes, as all other land use classes
    are functionally identical with arable land):

    >>> ft(100.)
    >>> fhru(1.)
    >>> lnk(ACKER)
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
    >>> relwz(.5)
    >>> relwb(.05)
    >>> beta(.01)
    >>> fbeta(1.)
    >>> dmax(5.)
    >>> dmin(1.)
    >>> bsf(.4)
    >>> a1(0.)
    >>> a2(inf)
    >>> tind(1.)
    >>> eqb(100.)
    >>> eqi1(50.)
    >>> eqi2(10.)
    >>> eqd1(2.)
    >>> eqd2(1.)

    Update the values of all derived parameters:

    >>> #model.parameters.update()

    Set the initial values:

    >>> #states.inzp = .5
    >>> #states.wats = 10.
    >>> #states.waes = 15.
    >>> #states.bowa = 150.
    >>> #states.qdgz1 = .1
    >>> #states.qdgz2 = .0
    >>> #states.qigz1 = .1
    >>> #states.qigz2 = .1
    >>> #states.qbgz = .1
    >>> #states.qdga1 = .1
    >>> #states.qdga2 = .0
    >>> #states.qiga1 = .1
    >>> #states.qiga2 = .1
    >>> #states.qbga = .1

    Set the input values for both simulation time steps:

    >>> inputs.nied.series = 2.
    >>> inputs.teml.series = 10.
    >>> inputs.glob.series = 100.

    Check the correctness of the results:

    >>> #model.doit(0)
    >>> #print(round(result[0], 6))
    2.217163
    >>> #result[0] = 0.
    >>> #model.doit(1)
    >>> #print(round(result[0], 6))
    3.741258

    >>> #test()


"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core.modelimports import *
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from lland
from hydpy.models.lland import lland_model
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_derived
from hydpy.models.lland import lland_inputs
from hydpy.models.lland import lland_fluxes
from hydpy.models.lland import lland_states
from hydpy.models.lland import lland_aides
from hydpy.models.lland import lland_outlets
from hydpy.models.lland.lland_parameters import Parameters
from hydpy.models.lland.lland_constants import *


class Model(modeltools.Model):
    """LARSIM-Land version of HydPy-L-Land (lland_v1)."""
    _RUNMETHODS = (lland_model.calc_nkor_v1,
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
                   lland_model.calc_qdgz1_qdgz2_v1,
                   lland_model.calc_qbga_v1,
                   lland_model.calc_qiga1_v1,
                   lland_model.calc_qiga2_v1,
                   lland_model.calc_qdga1_v1,
                   lland_model.calc_qdga2_v1,
                   lland_model.calc_q_v1,
                   lland_model.update_outlets_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of lland_v1, directly defined by the user."""
    _PARCLASSES = (lland_control.FT,
                   lland_control.NHRU,
                   lland_control.Lnk,
                   lland_control.FHRU,
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
                   lland_control.RelWZ,
                   lland_control.RelWB,
                   lland_control.Beta,
                   lland_control.FBeta,
                   lland_control.DMax,
                   lland_control.DMin,
                   lland_control.BSf,
                   lland_control.A1,
                   lland_control.A2,
                   lland_control.TInd,
                   lland_control.EQB,
                   lland_control.EQI1,
                   lland_control.EQI2,
                   lland_control.EQD1,
                   lland_control.EQD2)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of lland_v1, indirectly defined by the user."""
    _PARCLASSES = (lland_derived.MOY,
                   lland_derived.KInz,
                   lland_derived.WB,
                   lland_derived.WZ,
                   lland_derived.KB,
                   lland_derived.KI1,
                   lland_derived.KI2,
                   lland_derived.KD1,
                   lland_derived.KD2,
                   lland_derived.QFactor)


class InputSequences(sequencetools.InputSequences):
    """Input sequences of lland_v1."""
    _SEQCLASSES = (lland_inputs.Nied,
                   lland_inputs.TemL,
                   lland_inputs.Glob)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of lland_v1."""
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
                   lland_fluxes.QDGZ,
                   lland_fluxes.Q)


class StateSequences(sequencetools.StateSequences):
    """State sequences of lland_v1."""
    _SEQCLASSES = (lland_states.Inzp,
                   lland_states.WATS,
                   lland_states.WAeS,
                   lland_states.BoWa,
                   lland_states.QDGZ1,
                   lland_states.QDGZ2,
                   lland_states.QIGZ1,
                   lland_states.QIGZ2,
                   lland_states.QBGZ,
                   lland_states.QDGA1,
                   lland_states.QDGA2,
                   lland_states.QIGA1,
                   lland_states.QIGA2,
                   lland_states.QBGA)


class AideSequences(sequencetools.AideSequences):
    """Aide sequences of lland_v1."""
    _SEQCLASSES = (lland_aides.Temp,
                   lland_aides.SfA,
                   lland_aides.Exz,
                   lland_aides.BVl,
                   lland_aides.MVl,
                   lland_aides.RVl,
                   lland_aides.EPW)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of lland_v1."""
    _SEQCLASSES = (lland_outlets.Q,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
