# -*- coding: utf-8 -*-
"""
Version 1 of the L-Land model is designed to agree with the LARSIM-ME
configuration of the LARSIM model used by the German Federal Institute
of Hydrology (BfG), but offers more flexibility in some regards (e.g. in
parameterization).  It can briefly be summarized as follows:

 * Simple routines for adjusting the meteorological input data.
 * Reference evapotranspiration after Turc-Wendling.
 * An enhanced degree-day-method for calculating snow melt.
 * A simple snow retention routine.
 * Landuse and month specific potential evapotranspiration.
 * Acual soil evapotranspiration after ATV-DVWK- 504 (2002).
 * A Soil routine based on the Xinanjiang model.
 * One base flow, two interflow and two direct flow components.
 * Seperate linear storages for modelling runoff concentration.
 * Additional evaporation from water areas.

The following figure shows the general structure of L-Land Version 1.  Note
that, besides water areas and sealed surface areas, all land use types rely
on the same set of process equations:

.. image:: HydPy-L-Land_Version-1.png

As all models implemented in HydPy, base model L-Land can principally be
applied on arbitrary simulation step sizes.  But for the L-Land version 1
application model one has to be aware, that the Turc-Wendling equation
for calculating reference evaporation is designed for daily time steps only.


Integration tests:

    All integration tests are performed in January (to allow for realistic
    snow examples), spanning over a period of five days:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '06.01.2000',
    ...                                    '1d'))

    Prepare the model instance and build the connections to element `land`
    and node `outlet`:

    >>> from hydpy.models.lland_v1 import *
    >>> parameterstep('1d')
    >>> from hydpy import Node, Element
    >>> outlet = Node('outlet')
    >>> land = Element('land', outlets=outlet)
    >>> land.connect(model)

    All tests shall be performed using a single hydrological response unit
    with a size of one square kilometre at an altitude of 100 meter:

    >>> nhru(1)
    >>> ft(1.)
    >>> fhru(1.)
    >>> hnn(100.)

    Initialize a test function object, which prepares and runs the tests
    and prints their results for the given sequences:

    >>> from hydpy.core.testtools import Test
    >>> test = Test(land)

    Define a format for the dates to be printed:

    >>> test.dateformat = '%d.%m.'

    In the first example, coniferous forest is selected as the only
    land use class:

    >>> lnk(NADELW)

    All control parameters are set in manner, that lets their corresponding
    methods show an impact on the results:

    >>> kg(1.2)
    >>> kt(1.)
    >>> ke(0.9)
    >>> kf(.6)
    >>> fln(.5)
    >>> hinz(.2)
    >>> lai(4.)
    >>> treft(0.)
    >>> trefn(0.)
    >>> tgr(1.)
    >>> tsp(2.)
    >>> gtf(5.)
    >>> rschmelz(334.)
    >>> cpwasser(4.1868)
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
    >>> a1(1.)
    >>> a2(1.)
    >>> tind(1.)
    >>> eqb(100.)
    >>> eqi1(50.)
    >>> eqi2(10.)
    >>> eqd1(2.)
    >>> eqd2(1.)

    Initially, relative soil moisture is 75%, but all other storages are
    empty and there is base flow only:

    >>> test.inits={'inzp': 0.,
    ...             'wats': 0.,
    ...             'waes': 0.,
    ...             'bowa': 150.,
    ...             'qdgz1': 0.,
    ...             'qdgz2': 0.,
    ...             'qigz1': 0.,
    ...             'qigz2': 0.,
    ...             'qbgz': 1.,
    ...             'qdga1': 0.,
    ...             'qdga2': 0.,
    ...             'qiga1': 0.,
    ...             'qiga2': 0.,
    ...             'qbga': 1.}

    For the input data, a strong increase in temperature from -5°C to +10°C
    is defined, to activate both the snow and the evapotranspiration routines:

    >>> inputs.nied.series = 0., 5., 5., 5., 0.
    >>> inputs.teml.series = -5., -5., 0., 5., 10.
    >>> inputs.glob.series = 100.

    The following results show that all relevant model components are at least
    activated once during the simulation period:

    >>> test()
    |   date | nied | teml |  glob | nkor | tkor |      et0 |     evpo |     nbes |     sbes |      evi |      evb |      wgtf |     schm |     wada |      qdb |     qib1 |     qib2 |      qbb |     qdgz |        q |     inzp |    wats |     waes |       bowa |    qdgz1 |    qdgz2 |    qigz1 |    qigz2 |     qbgz |    qdga1 |    qdga2 |    qiga1 |    qiga2 |     qbga |   outlet |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | -5.0 | 100.0 |  0.0 | -4.0 | 0.744738 | 0.372369 |      0.0 |      0.0 |      0.0 | 0.359997 |       0.0 |      0.0 |      0.0 |      0.0 |     0.75 | 1.414214 |      1.4 |      0.0 | 1.077855 |      0.0 |     0.0 |      0.0 |  146.07579 |      0.0 |      0.0 |     0.75 | 1.414214 |      1.4 |      0.0 |      0.0 |  0.00745 | 0.068411 | 1.001993 | 0.012475 |
    | 02.01. |  5.0 | -5.0 | 100.0 |  6.0 | -4.0 | 0.744738 | 0.372369 |      5.2 |      5.2 | 0.372369 |      0.0 |       0.0 |      0.0 |      0.0 |      0.0 | 0.730379 | 1.251034 | 1.360758 |      0.0 | 1.216305 | 0.427631 |     5.2 |      5.2 | 142.733619 |      0.0 |      0.0 | 0.730379 | 1.251034 | 1.360758 |      0.0 |      0.0 | 0.021959 | 0.188588 | 1.005758 | 0.014078 |
    | 03.01. |  5.0 |  0.0 | 100.0 |  6.0 |  1.0 | 0.913238 | 0.456619 | 5.627631 | 2.813816 | 0.456619 |      0.0 |  5.012535 | 5.012535 | 6.625839 |  2.04495 | 0.713668 | 1.117415 | 1.327336 |  2.04495 |  1.84654 | 0.343381 | 3.00128 | 4.201792 | 144.156088 | 1.510991 |  0.53396 | 0.713668 | 1.117415 | 1.327336 | 0.321934 | 0.196433 |  0.03582 | 0.283229 | 1.009124 | 0.021372 |
    | 04.01. |  5.0 |  5.0 | 100.0 |  6.0 |  6.0 | 1.068676 | 0.534338 | 5.543381 |      0.0 | 0.534338 |      0.0 | 30.075212 |  3.00128 | 9.745173 | 3.096033 |  0.72078 |  1.17367 | 1.341561 | 3.096033 | 2.987559 | 0.265662 |     0.0 |      0.0 | 147.569218 | 1.677006 | 1.419027 |  0.72078 |  1.17367 | 1.341561 | 0.825163 | 0.735388 | 0.049313 | 0.365334 | 1.012361 | 0.034578 |
    | 05.01. |  0.0 | 10.0 | 100.0 |  0.0 | 11.0 | 1.212514 | 0.606257 |      0.0 |      0.0 | 0.265662 | 0.328303 | 55.137889 |      0.0 |      0.0 |      0.0 | 0.737846 | 1.312348 | 1.375692 |      0.0 | 2.976082 |      0.0 |     0.0 |      0.0 | 143.815029 |      0.0 |      0.0 | 0.737846 | 1.312348 | 1.375692 | 0.803032 | 0.645499 | 0.062779 | 0.448966 | 1.015807 | 0.034445 |

    The second example deals with a sealed surface:

    >>> lnk(VERS)

    For sealed surfaces, the soil routine is skippend an no base flow is
    calculated.  Thus the corresponding initial values are set to zero:

    >>> test.inits['bowa'] = 0.
    >>> test.inits['qbgz'] = 0.
    >>> test.inits['qbga'] = 0.

    As retention processes below the surface are assumed to be negligible,
    all water reaching the sealed surface becomes direct discharge
    immediately:

    >>> test()
    |   date | nied | teml |  glob | nkor | tkor |      et0 |     evpo |     nbes |     sbes |      evi | evb |      wgtf |     schm |     wada |      qdb | qib1 | qib2 | qbb |     qdgz |        q |     inzp |    wats |     waes | bowa |    qdgz1 |    qdgz2 | qigz1 | qigz2 | qbgz |    qdga1 |    qdga2 | qiga1 | qiga2 | qbga |   outlet |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | -5.0 | 100.0 |  0.0 | -4.0 | 0.744738 | 0.372369 |      0.0 |      0.0 |      0.0 | 0.0 |       0.0 |      0.0 |      0.0 |      0.0 |  0.0 |  0.0 | 0.0 |      0.0 |      0.0 |      0.0 |     0.0 |      0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 |      0.0 |
    | 02.01. |  5.0 | -5.0 | 100.0 |  6.0 | -4.0 | 0.744738 | 0.372369 |      5.2 |      5.2 | 0.372369 | 0.0 |       0.0 |      0.0 |      0.0 |      0.0 |  0.0 |  0.0 | 0.0 |      0.0 |      0.0 | 0.427631 |     5.2 |      5.2 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 |      0.0 |
    | 03.01. |  5.0 |  0.0 | 100.0 |  6.0 |  1.0 | 0.913238 | 0.456619 | 5.627631 | 2.813816 | 0.456619 | 0.0 |  5.012535 | 5.012535 | 6.625839 | 6.625839 |  0.0 |  0.0 | 0.0 | 6.625839 | 2.151239 | 0.343381 | 3.00128 | 4.201792 |  0.0 | 1.849076 | 4.776763 |   0.0 |   0.0 |  0.0 | 0.393967 | 1.757273 |   0.0 |   0.0 |  0.0 | 0.024899 |
    | 04.01. |  5.0 |  5.0 | 100.0 |  6.0 |  6.0 | 1.068676 | 0.534338 | 5.543381 |      0.0 | 0.534338 | 0.0 | 30.075212 |  3.00128 | 9.745173 | 9.745173 |  0.0 |  0.0 | 0.0 | 9.745173 | 5.772522 | 0.265662 |     0.0 |      0.0 |  0.0 | 1.897385 | 7.847788 |   0.0 |   0.0 |  0.0 |   0.9768 | 4.795722 |   0.0 |   0.0 |  0.0 | 0.066812 |
    | 05.01. |  0.0 | 10.0 | 100.0 |  0.0 | 11.0 | 1.212514 | 0.606257 |      0.0 |      0.0 | 0.265662 | 0.0 | 55.137889 |      0.0 |      0.0 |      0.0 |  0.0 |  0.0 | 0.0 |      0.0 | 4.772719 |      0.0 |     0.0 |      0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 | 0.934763 | 3.837956 |   0.0 |   0.0 |  0.0 |  0.05524 |


    For water areas, even the interception and the snow module are skipped:

    >>> lnk(WASSER)
    >>> test()
    |   date | nied | teml |  glob | nkor | tkor |      et0 |     evpo | nbes | sbes |      evi | evb | wgtf | schm | wada | qdb | qib1 | qib2 | qbb | qdgz |        q | inzp | wats | waes | bowa |    qdgz1 |    qdgz2 | qigz1 | qigz2 | qbgz |    qdga1 |    qdga2 | qiga1 | qiga2 | qbga |   outlet |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | -5.0 | 100.0 |  0.0 | -4.0 | 0.744738 | 0.372369 |  0.0 |  0.0 |      0.0 | 0.0 |  0.0 |  0.0 |  0.0 | 0.0 |  0.0 |  0.0 | 0.0 |  0.0 |      0.0 |  0.0 |  0.0 |  0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 |      0.0 |
    | 02.01. |  5.0 | -5.0 | 100.0 |  6.0 | -4.0 | 0.744738 | 0.372369 |  6.0 |  6.0 | 0.372369 | 0.0 |  0.0 |  0.0 |  6.0 | 6.0 |  0.0 |  0.0 | 0.0 |  6.0 | 1.551075 |  0.0 |  0.0 |  0.0 |  0.0 | 1.833333 | 4.166667 |   0.0 |   0.0 |  0.0 | 0.390612 | 1.532831 |   0.0 |   0.0 |  0.0 | 0.017952 |
    | 03.01. |  5.0 |  0.0 | 100.0 |  6.0 |  1.0 | 0.913238 | 0.456619 |  6.0 |  3.0 | 0.456619 | 0.0 |  0.0 |  0.0 |  6.0 | 6.0 |  0.0 |  0.0 | 0.0 |  6.0 | 3.699393 |  0.0 |  0.0 |  0.0 |  0.0 | 1.833333 | 4.166667 |   0.0 |   0.0 |  0.0 | 0.958279 | 3.197733 |   0.0 |   0.0 |  0.0 | 0.042817 |
    | 04.01. |  5.0 |  5.0 | 100.0 |  6.0 |  6.0 | 1.068676 | 0.534338 |  6.0 |  0.0 | 0.534338 | 0.0 |  0.0 |  0.0 |  6.0 | 6.0 |  0.0 |  0.0 | 0.0 |  6.0 | 4.578464 |  0.0 |  0.0 |  0.0 |  0.0 | 1.833333 | 4.166667 |   0.0 |   0.0 |  0.0 | 1.302586 | 3.810216 |   0.0 |   0.0 |  0.0 | 0.052991 |
    | 05.01. |  0.0 | 10.0 | 100.0 |  0.0 | 11.0 | 1.212514 | 0.606257 |  0.0 |  0.0 | 0.606257 | 0.0 |  0.0 |  0.0 |  0.0 | 0.0 |  0.0 |  0.0 | 0.0 |  0.0 | 3.017254 |  0.0 |  0.0 |  0.0 |  0.0 |      0.0 |      0.0 |   0.0 |   0.0 |  0.0 | 1.120806 | 2.502705 |   0.0 |   0.0 |  0.0 | 0.034922 |

    Note that for water areas, interception evaporation is actually
    evaporation from the water surface.  Also note, that the water land use
    class is the only one, for which evaporation is abstracted after the runoff
    concentration routines have been applied.  Thus water areas can evaporate
    the water supply of previous time steps and, more import, the water supply
    of other areas within the same subbasin.
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
