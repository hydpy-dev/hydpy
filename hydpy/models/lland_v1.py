# -*- coding: utf-8 -*-
"""
Version 1 of the L-Land model is designed to aggree with the LARSIM-ME
configuration of the LARSIM model used by the German Federal Institute
of Hydrology (BfG), but offers more flexibility in some regards (e.g. in
parameterization).  It can briefly be summarized as follows:

 * Simple routines for adjusting the meteorological input data.
 * Reference evapotranspiration after Turc-Wendling.
 * An enhanced degree-day-method for calculating snow melt.
 * A simple snow retention routine.
 * Landuse and month specific potential evapotranspiration.
 * Acual soil evapotranspiration after ATV-DVWK- 504 (2002).
 * Soil routine based on the Xinanjiang model.
 * One base flow, two interflow and two direct flow components.
 * Seperate linear storages for modelling runoff concentration.
 * Additional evaporation from water areas.

The following picture shows the general structure of L-Land Version 1.  Note
that, besides water areas and sealed surface areas, all land use types rely
on the same process equations:

.. image:: HydPy-L-Land_Version-1.png

As all models implemented in HydPy, base model L-Land can principally be
applied on arbitrary simulation step sizes.  But for the L-Land version 1
application model one has to be aware, that the Turc-Wendling equation
for calculating reference evaporation is designed for daily values only.


Integration tests:

    The integration tests are performed in January (to allow for realistic
    snow examples), spanning over a period of five days:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '06.01.2000',
    ...                                    '1d'))

    Prepare the model instance and built the connections to element `land`
    and node `outlet`:

    >>> from hydpy.models.lland_v1 import *
    >>> parameterstep('1d')
    >>> from hydpy import Node, Element
    >>> outlet = Node('outlet')
    >>> land = Element('land', outlets=outlet)
    >>> land.connect(model)

    All tests shall be performed using single hydrological response unit with
    a size of one square kilometre an a altitude of 100 meter:

    >>> nhru(1)
    >>> ft(1.)
    >>> fhru(1.)
    >>> hnn(100.)

    Initialize a test function object, which prepares and runs the tests
    and prints their results for the given sequences:

    >>> from hydpy.core.testtools import Test
    >>> test = Test(land)
    >>> test.dateformat = '%d.%m.'

    Set the input values for the complete simulation period:

    >>> inputs.nied.series = 0., 5., 5., 5., 0.
    >>> inputs.teml.series = -2., -1., 0., 1., 2.
    >>> inputs.glob.series = 100.

    Define the control parameter values (select only arable land, sealed
    soil and water area as landuse classes, as all other land use classes
    are functionally identical with arable land):

    >>> lnk(ACKER)
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
    >>> tsp(0.)
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

    Check the correctness of the results:

    >>> test()
    |   date | nied | teml |  glob | nkor | tkor |      et0 |     evpo | nbes | sbes | evi |      evb |     wgtf |     schm |     wada |      qdb | qib1 | qib2 | qbb |     qdgz |        q | inzp |     wats |     waes |     bowa |    qdgz1 | qdgz2 | qigz1 | qigz2 | qbgz |    qdga1 | qdga2 | qiga1 | qiga2 | qbga |   outlet |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | -2.0 | 100.0 |  0.0 | -3.0 | 0.779561 | 0.779561 |  0.0 |  0.0 | 0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |  0.0 |  0.0 | 0.0 |      0.0 |      0.0 |  0.0 |      0.0 |      0.0 |      0.0 |      0.0 |   0.0 |   0.0 |   0.0 |  0.0 |      0.0 |   0.0 |   0.0 |   0.0 |  0.0 |      0.0 |
    | 02.01. |  5.0 | -1.0 | 100.0 |  6.0 | -2.0 | 0.813809 | 0.813809 |  5.8 |  5.8 | 0.2 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |  0.0 |  0.0 | 0.0 |      0.0 |      0.0 |  0.0 |      5.8 |      5.8 |      0.0 |      0.0 |   0.0 |   0.0 |   0.0 |  0.0 |      0.0 |   0.0 |   0.0 |   0.0 |  0.0 |      0.0 |
    | 03.01. |  5.0 |  0.0 | 100.0 |  6.0 | -1.0 | 0.847495 | 0.847495 |  5.8 |  5.8 | 0.2 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |  0.0 |  0.0 | 0.0 |      0.0 |      0.0 |  0.0 |     11.6 |     11.6 |      0.0 |      0.0 |   0.0 |   0.0 |   0.0 |  0.0 |      0.0 |   0.0 |   0.0 |   0.0 |  0.0 |      0.0 |
    | 04.01. |  5.0 |  1.0 | 100.0 |  6.0 |  0.0 | 0.880634 | 0.880634 |  5.8 |  0.0 | 0.2 |      0.0 |      0.0 |      0.0 |     1.16 | 0.000962 |  0.0 |  0.0 | 0.0 | 0.000962 | 0.000205 |  0.0 |     11.6 |    16.24 | 1.159038 | 0.000962 |   0.0 |   0.0 |   0.0 |  0.0 | 0.000205 |   0.0 |   0.0 |   0.0 |  0.0 | 0.000002 |
    | 05.01. |  0.0 |  2.0 | 100.0 |  0.0 |  1.0 | 0.913238 | 0.913238 |  0.0 |  0.0 | 0.0 | 0.013321 | 5.012535 | 5.012535 | 7.017549 | 0.047086 |  0.0 |  0.0 | 0.0 | 0.047086 |  0.01033 |  0.0 | 6.587465 | 9.222451 |  8.11618 | 0.047086 |   0.0 |   0.0 |   0.0 |  0.0 |  0.01033 |   0.0 |   0.0 |   0.0 |  0.0 |  0.00012 |
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
                   lland_model.calc_sbes_v1,
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
                   lland_control.TSp,
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
                   lland_fluxes.SBes,
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
