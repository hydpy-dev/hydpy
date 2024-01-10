# -*- coding: utf-8 -*-
"""
.. _`Pegasus method`: https://link.springer.com/article/10.1007/BF01932959
"""

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.auxs import quadtools
from hydpy.auxs import roottools
from hydpy.cythons import modelutils
from hydpy.cythons import smoothutils
from hydpy.interfaces import dischargeinterfaces
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.interfaces import tempinterfaces

# ...from wland
from hydpy.models.wland import wland_control
from hydpy.models.wland import wland_derived
from hydpy.models.wland import wland_fixed
from hydpy.models.wland import wland_solver
from hydpy.models.wland import wland_inputs
from hydpy.models.wland import wland_factors
from hydpy.models.wland import wland_fluxes
from hydpy.models.wland import wland_states
from hydpy.models.wland import wland_aides
from hydpy.models.wland import wland_outlets
from hydpy.models.wland import wland_constants
from hydpy.models.wland.wland_constants import CONIFER, DECIDIOUS, SEALED, SOIL, MIXED


class Pick_HS_V1(modeltools.Method):
    """Take the surface water level from a submodel that complies with the
    |WaterLevelModel_V1| interface, if available.

    Examples:

        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep()

        Without an available submodel, |Pick_HS_V1| does not change the current value
        of sequence |HS| and sets |DHS| (the change of |HS|) accordingly to zero:

        >>> states.hs(3000.0)
        >>> model.pick_hs_v1()
        >>> states.hs
        hs(3000.0)
        >>> factors.dhs
        dhs(0.0)

        We take |exch_waterlevel| as an example to demonstrate that |Pick_HS_V1|
        correctly uses submodels that follow the |WaterLevelModel_V1| interface for
        updating |HS| and logs such changes via sequence |DHS|:

        >>> with model.add_waterlevelmodel_v1("exch_waterlevel"):
        ...     pass
        >>> from hydpy import Element, Node
        >>> wl = Node("wl", variable="WaterLevel")
        >>> wl.sequences.sim = 2.0
        >>> e = Element("e", receivers=wl, outlets="q")
        >>> e.model = model
        >>> model.pick_hs_v1()
        >>> states.hs
        hs(2000.0)

        >>> factors.dhs
        dhs(-1000.0)
    """

    UPDATEDSEQUENCES = (wland_states.HS,)
    RESULTSEQUENCES = (wland_factors.DHS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if model.waterlevelmodel is None:
            fac.dhs = 0.0
        elif model.waterlevelmodel_typeid == 1:
            hs: float = 1000.0 * (
                cast(
                    stateinterfaces.WaterLevelModel_V1, model.waterlevelmodel
                ).get_waterlevel()
            )
            fac.dhs = hs - new.hs
            old.hs = new.hs = hs


class Calc_FXS_V1(modeltools.Method):
    r"""Query the current surface water supply/extraction.

    Basic equation:
      .. math::
        FXS_{fluxes} = \begin{cases}
        0 &|\ FXS_{inputs} = 0
        \\
        \frac{FXS_{inputs}}{ASR} &|\ FXS_{inputs} \neq 0 \land NU > 1
        \\
        inf &|\ FXS_{inputs} \neq 0 \land NU = 1
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.asr(0.5)
        >>> inputs.fxs = 2.0
        >>> model.calc_fxs_v1()
        >>> fluxes.fxs
        fxs(4.0)
        >>> nu(1)
        >>> derived.asr(0.0)
        >>> model.calc_fxs_v1()
        >>> fluxes.fxs
        fxs(inf)
        >>> inputs.fxs = 0.0
        >>> model.calc_fxs_v1()
        >>> fluxes.fxs
        fxs(0.0)
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    DERIVEDPARAMETERS = (wland_derived.ASR,)
    REQUIREDSEQUENCES = (wland_inputs.FXS,)
    RESULTSEQUENCES = (wland_fluxes.FXS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if inp.fxs == 0.0:
            flu.fxs = 0.0
        elif con.nu == 1:
            flu.fxs = modelutils.inf
        else:
            flu.fxs = inp.fxs / der.asr


class Calc_FXG_V1(modeltools.Method):
    r"""Query the current seepage/extraction.

    Basic equation:
      .. math::
        FXG_{fluxes} = \begin{cases}
        0 &|\ FXG_{inputs} = 0
        \\
        \frac{FXG_{inputs}}{AGR} &|\ FXG_{inputs} \neq 0 \land AGR > 0
        \\
        inf &|\ FXG_{inputs} \neq 0 \land AGR = 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.agr(0.4)
        >>> inputs.fxg = 2.0
        >>> model.calc_fxg_v1()
        >>> fluxes.fxg
        fxg(5.0)
        >>> derived.agr(0.0)
        >>> model.calc_fxg_v1()
        >>> fluxes.fxg
        fxg(inf)
        >>> inputs.fxg = 0.0
        >>> model.calc_fxg_v1()
        >>> fluxes.fxg
        fxg(0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.AGR,)
    REQUIREDSEQUENCES = (wland_inputs.FXG,)
    RESULTSEQUENCES = (wland_fluxes.FXG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if inp.fxg == 0.0:
            flu.fxg = 0.0
        else:
            ra: float = der.agr
            if ra > 0.0:
                flu.fxg = inp.fxg / ra
            else:
                flu.fxg = modelutils.inf


class Calc_PC_V1(modeltools.Method):
    r"""Calculate the corrected precipitation.

    Basic equation:
      :math:`PC = CP \cdot P`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> cp(1.2)
        >>> inputs.p = 2.0
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(2.4)
    """

    CONTROLPARAMETERS = (wland_control.CP,)
    REQUIREDSEQUENCES = (wland_inputs.P,)
    RESULTSEQUENCES = (wland_fluxes.PC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.pc = con.cp * inp.p


class Calc_PE_PET_PETModel_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    potential evapotranspiration of the land areas and the potential evaporation of the
    surface water storage.

    Example:

        We use |evap_tw2002| as an example:

        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep()
        >>> nu(4)
        >>> at(1.0)
        >>> aur(0.25, 0.15, 0.1, 0.5)
        >>> lt(FIELD, FIELD, FIELD, WATER)
        >>> derived.nul.update()
        >>> from hydpy import prepare_model
        >>> with model.add_petmodel_v1("evap_tw2002"):
        ...     hrualtitude(200.0, 600.0, 1000.0, 100.0)
        ...     coastfactor(0.6)
        ...     evapotranspirationfactor(1.1)
        ...     inputs.globalradiation = 200.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         temperatureaddend(1.0)
        ...         inputs.temperature = 14.0
        >>> model.calc_pe_pet_v1()
        >>> fluxes.pe
        pe(3.07171, 2.86215, 2.86215, 3.128984)
        >>> fluxes.pet
        pet(3.07171, 2.86215, 2.86215, 0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.NUL,)
    RESULTSEQUENCES = (wland_fluxes.PE, wland_fluxes.PET)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialevapotranspiration()
        for k in range(der.nul):
            flu.pe[k] = flu.pet[k] = submodel.get_potentialevapotranspiration(k)
        flu.pe[der.nul] = submodel.get_potentialevapotranspiration(der.nul)
        flu.pet[der.nul] = 0.0


class Calc_PE_PET_PETModel_V2(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V2| interface calculate the
    potential interception evaporation and potential vadose zone evapotranspiration of
    the land areas and the potential evaporation of the surface water storage.

    Examples:

        We use |evap_pet_ambav1| as an example.  All data stems from the integration
        tests :ref:`evap_pet_ambav1_non_tree_vegetation_daily`,
        :ref:`evap_pet_ambav1_tree_like_vegetation_daily`,
        :ref:`evap_pet_ambav1_snow_daily`, and :ref:`evap_pet_ambav1_water_area_daily`:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-08-01", "2000-08-02", "1d"
        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep("1h")
        >>> nu(4)
        >>> at(1.0)
        >>> aur(0.25, 0.15, 0.1, 0.5)
        >>> lt(FIELD, DECIDIOUS, DECIDIOUS, WATER)
        >>> derived.nul.update()
        >>> inputs.t = 15.0
        >>> inputs.p = 0.0
        >>> states.sp = 0.0, 0.0, 1.0, 0.0
        >>> from hydpy import prepare_model
        >>> with model.add_petmodel_v2("evap_pet_ambav1") as ambav:
        ...     measuringheightwindspeed(10.0)
        ...     leafalbedo(0.2)
        ...     leafalbedosnow(0.8)
        ...     groundalbedo(0.2)
        ...     groundalbedosnow(0.8)
        ...     leafareaindex(5.0)
        ...     cropheight.field = 10.0
        ...     cropheight.decidious = 10.0
        ...     cropheight.water = 0.0
        ...     leafresistance(40.0)
        ...     wetsoilresistance(100.0)
        ...     soilresistanceincrease(1.0)
        ...     wetnessthreshold(0.5)
        ...     cloudtypefactor(0.2)
        ...     nightcloudfactor(1.0)
        ...     inputs.windspeed = 2.0
        ...     inputs.relativehumidity = 80.0
        ...     inputs.atmosphericpressure = 1000.0
        ...     inputs.sunshineduration = 6.0
        ...     inputs.possiblesunshineduration = 16.0
        ...     inputs.globalradiation = 190.0
        ...     states.soilresistance = 100.0

        The first example reproduces the results for the first simulated day of the
        integration tests :ref:`evap_pet_ambav1_non_tree_vegetation_daily` (first
        response unit), :ref:`evap_pet_ambav1_tree_like_vegetation_daily` (second
        response unit), and :ref:`evap_pet_ambav1_water_area_daily` (fourth response
        unit):

        >>> ambav.sequences.logs.loggedprecipitation = [0.0]
        >>> ambav.sequences.logs.loggedpotentialsoilevapotranspiration = [1.0]
        >>> model.calc_pe_pet_v1()
        >>> fluxes.pe
        pe(8.211488, 5.545339, 3.390149, 1.890672)
        >>> fluxes.pet
        pet(3.073332, 2.768363, 1.692442, 0.0)

        The second example reproduces the results for the third simulated day of the
        :ref:`evap_pet_ambav1_snow_daily` integration test (third response unit):

        >>> ambav.sequences.logs.loggedprecipitation = [10.0]
        >>> ambav.sequences.logs.loggedpotentialsoilevapotranspiration = [2.282495]
        >>> model.calc_pe_pet_v1()
        >>> fluxes.pe
        pe(8.211488, 5.545339, 3.390149, 1.890672)
        >>> fluxes.pet
        pet(3.163548, 2.83302, 1.73197, 0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    DERIVEDPARAMETERS = (wland_derived.NUL,)
    RESULTSEQUENCES = (wland_fluxes.PE, wland_fluxes.PET)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V2) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialinterceptionevaporation()
        submodel.determine_potentialsoilevapotranspiration()
        submodel.determine_potentialwaterevaporation()
        for k in range(der.nul):
            flu.pe[k] = submodel.get_potentialinterceptionevaporation(k)
            flu.pet[k] = submodel.get_potentialsoilevapotranspiration(k)
        flu.pe[der.nul] = submodel.get_potentialwaterevaporation(der.nul)
        flu.pet[der.nul] = 0.0


class Calc_PE_PET_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| or |PETModel_V2| interface
    calculate the potential evapotranspiration of the land areas and the potential
    evaporation of the surface water storage."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1, petinterfaces.PETModel_V2)
    SUBMETHODS = (Calc_PE_PET_PETModel_V1, Calc_PE_PET_PETModel_V2)
    DERIVEDPARAMETERS = (wland_derived.NUL,)
    RESULTSEQUENCES = (wland_fluxes.PE, wland_fluxes.PET)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.petmodel_typeid == 1:
            model.calc_pe_pet_petmodel_v1(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )
        elif model.petmodel_typeid == 2:
            model.calc_pe_pet_petmodel_v2(
                cast(petinterfaces.PETModel_V2, model.petmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_TF_V1(modeltools.Method):
    r"""Calculate the total amount of throughfall of the land areas.

    Basic equation (discontinuous):
      .. math::
        TF = \begin{cases}
        P &|\ IC > IT
        \\
        0 &|\ IC < IT
        \end{cases}

    Examples:

        >>> from hydpy import pub, UnitTest
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> lt(FIELD, WATER)
        >>> ih(0.2)
        >>> lai.field_mar = 5.0
        >>> lai.field_apr = 10.0
        >>> derived.moy.update()
        >>> derived.nul.update()
        >>> fluxes.pc = 5.0
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_tf_v1,
        ...     last_example=6,
        ...     parseqs=(states.ic, fluxes.tf),
        ... )
        >>> test.nexts.ic = -4.0, 0.0, 1.0, 2.0, 3.0, 7.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> test()
        | ex. |         ic |       tf |
        -------------------------------
        |   1 | -4.0  -4.0 | 0.0  0.0 |
        |   2 |  0.0   0.0 | 0.0  0.0 |
        |   3 |  1.0   1.0 | 2.5  0.0 |
        |   4 |  2.0   2.0 | 5.0  0.0 |
        |   5 |  3.0   3.0 | 5.0  0.0 |
        |   6 |  7.0   7.0 | 5.0  0.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> test()
        | ex. |         ic |           tf |
        -----------------------------------
        |   1 | -4.0  -4.0 |     0.0  0.0 |
        |   2 |  0.0   0.0 | 0.00051  0.0 |
        |   3 |  1.0   1.0 |    0.05  0.0 |
        |   4 |  2.0   2.0 |     2.5  0.0 |
        |   5 |  3.0   3.0 |    4.95  0.0 |
        |   6 |  7.0   7.0 |     5.0  0.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (wland_control.LT, wland_control.LAI, wland_control.IH)
    DERIVEDPARAMETERS = (wland_derived.MOY, wland_derived.NUL, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_fluxes.PC, wland_states.IC)
    RESULTSEQUENCES = (wland_fluxes.TF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(der.nul):
            lai: float = con.lai[con.lt[k] - SEALED, der.moy[model.idx_sim]]
            flu.tf[k] = flu.pc * smoothutils.smooth_logistic1(
                sta.ic[k] - con.ih * lai, der.rh1
            )
        flu.tf[der.nul] = 0.0


class Calc_EI_V1(modeltools.Method):
    r"""Calculate the interception evaporation of the land areas.

    Basic equation (discontinuous):
      .. math::
        EI = \begin{cases}
        PE &|\ IC > 0
        \\
        0 &|\ IC < 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.pe = 5.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_ei_v1,
        ...     last_example=9,
        ...     parseqs=(states.ic, fluxes.ei)
        ... )
        >>> test.nexts.ic = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |         ic |       ei |
        -------------------------------
        |   1 | -4.0  -4.0 | 0.0  0.0 |
        |   2 | -3.0  -3.0 | 0.0  0.0 |
        |   3 | -2.0  -2.0 | 0.0  0.0 |
        |   4 | -1.0  -1.0 | 0.0  0.0 |
        |   5 |  0.0   0.0 | 2.5  0.0 |
        |   6 |  1.0   1.0 | 5.0  0.0 |
        |   7 |  2.0   2.0 | 5.0  0.0 |
        |   8 |  3.0   3.0 | 5.0  0.0 |
        |   9 |  4.0   4.0 | 5.0  0.0 |


        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |         ic |            ei |
        ------------------------------------
        |   1 | -4.0  -4.0 |      0.0  0.0 |
        |   2 | -3.0  -3.0 | 0.000005  0.0 |
        |   3 | -2.0  -2.0 |  0.00051  0.0 |
        |   4 | -1.0  -1.0 |     0.05  0.0 |
        |   5 |  0.0   0.0 |      2.5  0.0 |
        |   6 |  1.0   1.0 |     4.95  0.0 |
        |   7 |  2.0   2.0 |  4.99949  0.0 |
        |   8 |  3.0   3.0 | 4.999995  0.0 |
        |   9 |  4.0   4.0 |      5.0  0.0 |

    """

    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_fluxes.PE, wland_states.IC)
    RESULTSEQUENCES = (wland_fluxes.EI,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(der.nul):
            flu.ei[k] = flu.pe[k] * (smoothutils.smooth_logistic1(sta.ic[k], der.rh1))
        flu.ei[der.nul] = 0.0


class Calc_FR_V1(modeltools.Method):
    r"""Determine the fraction between rainfall and total precipitation.

    Basic equation:
      :math:`FR = \frac{T- \left( TT - TI / 2 \right)}{TI}`

    Restriction:
      :math:`0 \leq FR \leq 1`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> tt(1.0)
        >>> ti(4.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_fr_v1,
        ...     last_example=9,
        ...     parseqs=(inputs.t, aides.fr)
        ... )
        >>> test.nexts.t = -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0
        >>> test()
        | ex. |    t |   fr |
        ---------------------
        |   1 | -3.0 |  0.0 |
        |   2 | -2.0 |  0.0 |
        |   3 | -1.0 |  0.0 |
        |   4 |  0.0 | 0.25 |
        |   5 |  1.0 |  0.5 |
        |   6 |  2.0 | 0.75 |
        |   7 |  3.0 |  1.0 |
        |   8 |  4.0 |  1.0 |
        |   9 |  5.0 |  1.0 |
    """

    CONTROLPARAMETERS = (wland_control.TT, wland_control.TI)
    REQUIREDSEQUENCES = (wland_inputs.T,)
    RESULTSEQUENCES = (wland_aides.FR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        aid = model.sequences.aides.fastaccess
        if inp.t >= (con.tt + con.ti / 2.0):
            aid.fr = 1.0
        elif inp.t <= (con.tt - con.ti / 2.0):
            aid.fr = 0.0
        else:
            aid.fr = (inp.t - (con.tt - con.ti / 2.0)) / con.ti


class Calc_RF_V1(modeltools.Method):
    r"""Calculate the liquid amount of throughfall (rainfall) of the land areas.

    Basic equation:
      :math:`RF = FR \cdot TF`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.tf = 2.0
        >>> aides.fr = 0.8
        >>> model.calc_rf_v1()
        >>> fluxes.rf
        rf(1.6, 0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.NUL,)
    REQUIREDSEQUENCES = (wland_fluxes.TF, wland_aides.FR)
    RESULTSEQUENCES = (wland_fluxes.RF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(der.nul):
            flu.rf[k] = aid.fr * flu.tf[k]
        flu.rf[der.nul] = 0.0


class Calc_SF_V1(modeltools.Method):
    r"""Calculate the frozen amount of throughfall (snowfall) of the land areas.

    Basic equation:
      :math:`SF = (1-FR) \cdot TF`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.tf = 2.0
        >>> aides.fr = 0.8
        >>> model.calc_sf_v1()
        >>> fluxes.sf
        sf(0.4, 0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.NUL,)
    REQUIREDSEQUENCES = (wland_fluxes.TF, wland_aides.FR)
    RESULTSEQUENCES = (wland_fluxes.SF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(der.nul):
            flu.sf[k] = (1.0 - aid.fr) * flu.tf[k]
        flu.sf[der.nul] = 0.0


class Calc_PM_V1(modeltools.Method):
    r"""Calculate the potential snowmelt of the land areas.

    Basic equation (discontinous):
      :math:`PM = max \left( DDF \cdot (T - DDT), 0 \right)`

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nu(2)
        >>> derived.nul.update()
        >>> ddf(4.0)
        >>> ddt(1.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_pm_v1,
        ...     last_example=11,
        ...     parseqs=(inputs.t, fluxes.pm)
        ... )
        >>> test.nexts.t = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0

        Without smoothing:

        >>> st(0.0)
        >>> derived.rt2.update()
        >>> test()
        | ex. |    t |        pm |
        --------------------------
        |   1 | -4.0 |  0.0  0.0 |
        |   2 | -3.0 |  0.0  0.0 |
        |   3 | -2.0 |  0.0  0.0 |
        |   4 | -1.0 |  0.0  0.0 |
        |   5 |  0.0 |  0.0  0.0 |
        |   6 |  1.0 |  0.0  0.0 |
        |   7 |  2.0 |  2.0  0.0 |
        |   8 |  3.0 |  4.0  0.0 |
        |   9 |  4.0 |  6.0  0.0 |
        |  10 |  5.0 |  8.0  0.0 |
        |  11 |  6.0 | 10.0  0.0 |

        With smoothing:

        >>> st(1.0)
        >>> derived.rt2.update()
        >>> test()
        | ex. |    t |            pm |
        ------------------------------
        |   1 | -4.0 |      0.0  0.0 |
        |   2 | -3.0 | 0.000001  0.0 |
        |   3 | -2.0 | 0.000024  0.0 |
        |   4 | -1.0 | 0.000697  0.0 |
        |   5 |  0.0 |     0.02  0.0 |
        |   6 |  1.0 | 0.411048  0.0 |
        |   7 |  2.0 |     2.02  0.0 |
        |   8 |  3.0 | 4.000697  0.0 |
        |   9 |  4.0 | 6.000024  0.0 |
        |  10 |  5.0 | 8.000001  0.0 |
        |  11 |  6.0 |     10.0  0.0 |
    """

    CONTROLPARAMETERS = (wland_control.DDF, wland_control.DDT)
    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.RT2)
    REQUIREDSEQUENCES = (wland_inputs.T,)
    RESULTSEQUENCES = (wland_fluxes.PM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(der.nul):
            flu.pm[k] = con.ddf[k] * smoothutils.smooth_logistic2(
                inp.t - con.ddt, der.rt2
            )
        flu.pm[der.nul] = 0.0


class Calc_AM_V1(modeltools.Method):
    r"""Calculate the actual snowmelt of the land areas.

    Basic equation (discontinous):
      .. math::
        AM = \begin{cases}
        PM &|\ SP > 0
        \\
        0 &|\ SP < 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.pm = 2.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_am_v1,
        ...     last_example=9,
        ...     parseqs=(states.sp, fluxes.am)
        ... )
        >>> test.nexts.sp = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |         sp |       am |
        -------------------------------
        |   1 | -4.0  -4.0 | 0.0  0.0 |
        |   2 | -3.0  -3.0 | 0.0  0.0 |
        |   3 | -2.0  -2.0 | 0.0  0.0 |
        |   4 | -1.0  -1.0 | 0.0  0.0 |
        |   5 |  0.0   0.0 | 1.0  0.0 |
        |   6 |  1.0   1.0 | 2.0  0.0 |
        |   7 |  2.0   2.0 | 2.0  0.0 |
        |   8 |  3.0   3.0 | 2.0  0.0 |
        |   9 |  4.0   4.0 | 2.0  0.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |         sp |            am |
        ------------------------------------
        |   1 | -4.0  -4.0 |      0.0  0.0 |
        |   2 | -3.0  -3.0 | 0.000002  0.0 |
        |   3 | -2.0  -2.0 | 0.000204  0.0 |
        |   4 | -1.0  -1.0 |     0.02  0.0 |
        |   5 |  0.0   0.0 |      1.0  0.0 |
        |   6 |  1.0   1.0 |     1.98  0.0 |
        |   7 |  2.0   2.0 | 1.999796  0.0 |
        |   8 |  3.0   3.0 | 1.999998  0.0 |
        |   9 |  4.0   4.0 |      2.0  0.0 |

    """

    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_fluxes.PM, wland_states.SP)
    RESULTSEQUENCES = (wland_fluxes.AM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(der.nul):
            flu.am[k] = flu.pm[k] * smoothutils.smooth_logistic1(sta.sp[k], der.rh1)
        flu.am[der.nul] = 0.0


class Calc_PS_V1(modeltools.Method):
    r"""Calculate the precipitation entering the surface water reservoir.

    Basic equation:
      :math:`PS = PC`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> fluxes.pc = 3.0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(3.0)
    """

    REQUIREDSEQUENCES = (wland_fluxes.PC,)
    RESULTSEQUENCES = (wland_fluxes.PS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.ps = flu.pc


class Calc_W_V1(modeltools.Method):
    r"""Calculate the wetness index.

    Basic equation:
      :math:`W = cos \left(
      \frac{max(min(DV, CW), 0) \cdot Pi}{CW} \right) \cdot \frac{1}{2} + \frac{1}{2}`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> cw(200.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_w_v1,
        ...     last_example=11,
        ...     parseqs=(states.dv, aides.w)
        ... )
        >>> test.nexts.dv = (
        ...     -50.0, -5.0, 0.0, 5.0, 50.0, 100.0, 150.0, 195.0, 200.0, 205.0, 250.0)
        >>> test()
        | ex. |    dv |        w |
        --------------------------
        |   1 | -50.0 |      1.0 |
        |   2 |  -5.0 |      1.0 |
        |   3 |   0.0 |      1.0 |
        |   4 |   5.0 | 0.998459 |
        |   5 |  50.0 | 0.853553 |
        |   6 | 100.0 |      0.5 |
        |   7 | 150.0 | 0.146447 |
        |   8 | 195.0 | 0.001541 |
        |   9 | 200.0 |      0.0 |
        |  10 | 205.0 |      0.0 |
        |  11 | 250.0 |      0.0 |
    """

    CONTROLPARAMETERS = (wland_control.CW,)
    FIXEDPARAMETERS = (wland_fixed.Pi,)
    REQUIREDSEQUENCES = (wland_states.DV,)
    RESULTSEQUENCES = (wland_aides.W,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.w = 0.5 + 0.5 * modelutils.cos(
            max(min(sta.dv, con.cw), 0.0) * fix.pi / con.cw
        )


class Calc_PV_V1(modeltools.Method):
    r"""Calculate the rainfall (and snowmelt) entering the vadose zone.

    Basic equation:
      .. math::
        PV = \sum_{i=1}^{NUL} \left ( \frac{AUR_i}{AGR} \cdot (RF_i + AM_i) \cdot
        \begin{cases}
        0 &|\ LT_i = SEALED
        \\
        1-W &|\ LT_i \neq SEALED
        \end{cases}  \right )

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(4)
        >>> derived.nul.update()
        >>> lt(FIELD, SOIL, SEALED, WATER)
        >>> aur(0.35, 0.1, 0.05, 0.5)
        >>> derived.agr.update()
        >>> fluxes.rf = 3.0, 2.0, 1.0, 0.0
        >>> fluxes.am = 1.0, 2.0, 3.0, 0.0
        >>> aides.w = 0.75
        >>> model.calc_pv_v1()
        >>> fluxes.pv
        pv(1.0)
    """

    CONTROLPARAMETERS = (wland_control.LT, wland_control.AUR)
    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.AGR)
    REQUIREDSEQUENCES = (wland_fluxes.RF, wland_fluxes.AM, wland_aides.W)
    RESULTSEQUENCES = (wland_fluxes.PV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.pv = 0.0
        for k in range(der.nul):
            if con.lt[k] != SEALED:
                flu.pv += (1.0 - aid.w) * con.aur[k] / der.agr * (flu.rf[k] + flu.am[k])


class Calc_PQ_V1(modeltools.Method):
    r"""Calculate the rainfall (and snowmelt) entering the quickflow reservoir.

    Basic equation:
      .. math::
        PQ = \sum_{i=1}^{NUL}\left( \frac{AUR_i}{ALR} \cdot (RF_i + AM_i) \cdot
        \begin{cases}
        1 &|\ LT_i = SEALED
        \\
        W &|\ LT_i \neq SEALED
        \end{cases} \right)

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(4)
        >>> lt(FIELD, SOIL, SEALED, WATER)
        >>> aur(0.3, 0.15, 0.05, 0.5)
        >>> derived.nul.update()
        >>> derived.alr.update()
        >>> fluxes.rf = 3.0, 2.0, 1.0, 0.0
        >>> fluxes.am = 1.0, 2.0, 2.0, 0.0
        >>> aides.w = 0.75
        >>> model.calc_pq_v1()
        >>> fluxes.pq
        pq(3.0)
    """

    CONTROLPARAMETERS = (wland_control.LT, wland_control.AUR)
    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.ALR)
    REQUIREDSEQUENCES = (wland_fluxes.RF, wland_fluxes.AM, wland_aides.W)
    RESULTSEQUENCES = (wland_fluxes.PQ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.pq = 0.0
        for k in range(der.nul):
            pq: float = con.aur[k] / der.alr * (flu.rf[k] + flu.am[k])
            if con.lt[k] != SEALED:
                pq *= aid.w
            flu.pq += pq


class Calc_Beta_V1(modeltools.Method):
    r"""Calculate the evapotranspiration reduction factor.

    Basic equations:
      :math:`Beta = \frac{1 - x}{1 + x} \cdot \frac{1}{2} + \frac{1}{2}`

      :math:`x = exp \left( Zeta1 \cdot (DV - Zeta2) \right)`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> zeta1(0.02)
        >>> zeta2(400.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_beta_v1,
        ...     last_example=12,
        ...     parseqs=(states.dv, aides.beta)
        ... )
        >>> test.nexts.dv = (
        ...     -100.0, 0.0, 100.0, 200.0, 300.0, 400.0,
        ...     500.0, 600.0, 700.0, 800.0, 900.0, 100000.0
        ... )
        >>> test()
        | ex. |       dv |     beta |
        -----------------------------
        |   1 |   -100.0 | 0.999955 |
        |   2 |      0.0 | 0.999665 |
        |   3 |    100.0 | 0.997527 |
        |   4 |    200.0 | 0.982014 |
        |   5 |    300.0 | 0.880797 |
        |   6 |    400.0 |      0.5 |
        |   7 |    500.0 | 0.119203 |
        |   8 |    600.0 | 0.017986 |
        |   9 |    700.0 | 0.002473 |
        |  10 |    800.0 | 0.000335 |
        |  11 |    900.0 | 0.000045 |
        |  12 | 100000.0 |      0.0 |
    """

    CONTROLPARAMETERS = (wland_control.Zeta1, wland_control.Zeta2)
    REQUIREDSEQUENCES = (wland_states.DV,)
    RESULTSEQUENCES = (wland_aides.Beta,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        temp: float = con.zeta1 * (sta.dv - con.zeta2)
        if temp > 700.0:
            aid.beta = 0.0
        else:
            temp = modelutils.exp(temp)
            aid.beta = 0.5 + 0.5 * (1.0 - temp) / (1.0 + temp)


class Calc_ETV_V1(modeltools.Method):
    r"""Calculate the actual evapotranspiration from the vadose zone.

    The following equation uses the :cite:t:`ref-Wigmosta1994` approach to extend the
    original WALRUS equation to cope with different potential values for |PE| and |PET|.
    (See the documentation on method |evap_model.Update_SoilEvapotranspiration_V3|,
    which covers the corner cases of this approach in more detail.)

    Basic equation:
      .. math::
        ETV = \sum_{i=1}^{NUL} \left( \frac{AUR_i}{AGR} \cdot
        \frac{PE_i - EI_i}{PE_i} \cdot PET_i \cdot
        \begin{cases}
        0 &|\ LT_i = SEALED
        \\
        Beta  &|\ LT_i \neq SEALED
        \end{cases}  \right)

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(4)
        >>> lt(FIELD, SOIL, SEALED, WATER)
        >>> aur(0.2, 0.2, 0.1, 0.5)
        >>> derived.nul.update()
        >>> derived.agr.update()
        >>> fluxes.pe = 5.0
        >>> fluxes.pet = 4.0
        >>> fluxes.ei = 1.0, 3.0, 2.0, 0.0
        >>> aides.beta = 0.75
        >>> model.calc_etv_v1()
        >>> fluxes.etv
        etv(1.8)
    """

    CONTROLPARAMETERS = (wland_control.LT, wland_control.AUR)
    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.AGR)
    REQUIREDSEQUENCES = (
        wland_fluxes.PE,
        wland_fluxes.PET,
        wland_fluxes.EI,
        wland_aides.Beta,
    )
    RESULTSEQUENCES = (wland_fluxes.ETV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.etv = 0.0
        for k in range(der.nul):
            if con.lt[k] != SEALED:
                if flu.pe[k] > 0.0:
                    pet: float = (flu.pe[k] - flu.ei[k]) / flu.pe[k] * flu.pet[k]
                    flu.etv += con.aur[k] / der.agr * pet * aid.beta


class Calc_ES_V1(modeltools.Method):
    r"""Calculate the actual evaporation from the surface water reservoir.

    Basic equation (discontinous):
      .. math::
        ES = \begin{cases}
        PE &|\ HS > 0
        \\
        0 &|\ HS \leq 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.pe = 3.0, 5.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_es_v1,
        ...     last_example=9,
        ...     parseqs=(states.hs, fluxes.es)
        ... )
        >>> test.nexts.hs = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   hs |  es |
        --------------------
        |   1 | -4.0 | 0.0 |
        |   2 | -3.0 | 0.0 |
        |   3 | -2.0 | 0.0 |
        |   4 | -1.0 | 0.0 |
        |   5 |  0.0 | 2.5 |
        |   6 |  1.0 | 5.0 |
        |   7 |  2.0 | 5.0 |
        |   8 |  3.0 | 5.0 |
        |   9 |  4.0 | 5.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   hs |       es |
        -------------------------
        |   1 | -4.0 |      0.0 |
        |   2 | -3.0 | 0.000005 |
        |   3 | -2.0 |  0.00051 |
        |   4 | -1.0 |     0.05 |
        |   5 |  0.0 |      2.5 |
        |   6 |  1.0 |     4.95 |
        |   7 |  2.0 |  4.99949 |
        |   8 |  3.0 | 4.999995 |
        |   9 |  4.0 |      5.0 |
    """
    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_fluxes.PE, wland_states.HS)
    RESULTSEQUENCES = (wland_fluxes.ES,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.es = flu.pe[der.nul] * smoothutils.smooth_logistic1(sta.hs, der.rh1)


class Calc_ET_V1(modeltools.Method):
    r"""Calculate the total actual evapotranspiration.

    Basic equation:
      :math:`ET =  ASR \cdot ES + AGR \cdot ETV + \sum_{i=1}^{NUL} AUR_i \cdot EI_i`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(3)
        >>> lt(FIELD, SEALED, WATER)
        >>> aur(0.5, 0.3, 0.2)
        >>> derived.nul.update()
        >>> derived.asr.update()
        >>> derived.agr.update()
        >>> fluxes.ei = 1.0, 2.0, 0.0
        >>> fluxes.etv = 3.0
        >>> fluxes.es = 4.0
        >>> model.calc_et_v1()
        >>> fluxes.et
        et(3.4)
    """

    CONTROLPARAMETERS = (wland_control.AUR,)
    DERIVEDPARAMETERS = (wland_derived.NUL, wland_derived.ASR, wland_derived.AGR)
    REQUIREDSEQUENCES = (wland_fluxes.EI, wland_fluxes.ETV, wland_fluxes.ES)
    RESULTSEQUENCES = (wland_fluxes.ET,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        ei: float = 0.0
        for k in range(der.nul):
            ei += con.aur[k] * flu.ei[k]
        flu.et = ei + der.agr * flu.etv + der.asr * flu.es


class Calc_DVEq_V1(modeltools.Method):
    r"""Calculate the equilibrium storage deficit of the vadose zone.

    Basic equation (discontinuous):
      .. math::
        DVEq = \begin{cases}
          0 &|\ DG \leq PsiAE
          \\
          ThetaS \cdot \left( DG - \frac{DG^{1-1/b}}{(1-1/b) \cdot PsiAE^{-1/B}} -
          \frac{PsiAE}{1-B} \right) &|\ PsiAE < DG
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_dveq_v1,
        ...     last_example=6,
        ...     parseqs=(states.dg, aides.dveq)
        ... )
        >>> test.nexts.dg = 200.0, 300.0, 400.0, 800.0, 1600.0, 3200.0

        Without smoothing:

        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  200.0 |        0.0 |
        |   2 |  300.0 |        0.0 |
        |   3 |  400.0 |   1.182498 |
        |   4 |  800.0 |  21.249634 |
        |   5 | 1600.0 |  97.612368 |
        |   6 | 3200.0 | 313.415248 |
    """

    CONTROLPARAMETERS = (wland_control.ThetaS, wland_control.PsiAE, wland_control.B)
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (wland_states.DG,)
    RESULTSEQUENCES = (wland_aides.DVEq,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            if sta.dg < con.psiae:
                aid.dveq = 0.0
            else:
                aid.dveq = con.thetas * (
                    sta.dg
                    - sta.dg ** (1.0 - 1.0 / con.b)
                    / (1.0 - 1.0 / con.b)
                    / con.psiae ** (-1.0 / con.b)
                    - con.psiae / (1.0 - con.b)
                )
        else:
            aid.dveq = modelutils.nan


class Return_DVH_V1(modeltools.Method):
    r"""Return the storage deficit of the vadose zone at a specific height above
    the groundwater table.

    Basic equation (discontinous):
      .. math::
        DVH = \begin{cases}
          0 &|\ DG \leq PsiAE
          \\
          ThetaS \cdot \left(1 - \left( \frac{h}{PsiAE} \right)^{-1/b} \right)
          &|\ PsiAE < DG
        \end{cases}

    This power law is the differential of the equation underlying method
    |Calc_DVEq_V1| with respect to height.  :cite:t:`ref-Brauer2014` also cites it
    (equation 6) but does not use it directly.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> psiae(300.0)
        >>> b(5.0)

        With smoothing:

        >>> from hydpy import repr_
        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> for h in [200.0, 299.0, 300.0, 301.0, 400.0, 500.0, 600.0]:
        ...     print(repr_(h), repr_(model.return_dvh_v1(h)))
        200.0 0.0
        299.0 0.0
        300.0 0.0
        301.0 0.000266
        400.0 0.022365
        500.0 0.038848
        600.0 0.05178

        Without smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> for h in [200.0, 299.0, 300.0, 301.0, 400.0, 500.0, 600.0]:
        ...     print(repr_(h), repr_(model.return_dvh_v1(h)))
        200.0 0.0
        299.0 0.000001
        300.0 0.00004
        301.0 0.000267
        400.0 0.022365
        500.0 0.038848
        600.0 0.05178
    """

    CONTROLPARAMETERS = (wland_control.ThetaS, wland_control.PsiAE, wland_control.B)
    DERIVEDPARAMETERS = (wland_derived.RH1,)

    @staticmethod
    def __call__(model: modeltools.Model, h: float) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        h = smoothutils.smooth_max1(h, con.psiae, der.rh1)
        return con.thetas * (1.0 - (h / con.psiae) ** (-1.0 / con.b))


class Calc_DVEq_V2(modeltools.Method):
    r"""Calculate the equilibrium storage deficit of the vadose zone.

    Basic equation:
      :math:`DHEq = \int_{0}^{DG} Return\_DVH\_V1(h) \ \ dh`

    Method |Calc_DVEq_V2| integrates |Return_DVH_V1| numerically, based on the
    Lobatto-Gauß quadrature.  Hence, it should give nearly identical results as
    method |Calc_DVEq_V1|, which provides the analytical solution to the underlying
    power law. The benefit of method |Calc_DVEq_V2| is that it supports the
    regularisation of |Return_DVH_V1|, which |Calc_DVEq_V1| does not.  In our
    experience, this benefit does not justify the additional numerical cost.
    However, we keep it for educational purposes, mainly as a starting point to
    implement alternative relationships between the soil water deficit and the
    groundwater table that we cannot solve analytically.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.nug(0)
        >>> model.calc_dveq_v2()
        >>> aides.dveq
        dveq(nan)

        >>> derived.nug(1)
        >>> thetas(0.4)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_dveq_v2,
        ...     last_example=8,
        ...     parseqs=(states.dg, aides.dveq)
        ... )
        >>> test.nexts.dg = 200.0, 299.0, 300.0, 301.0, 400.0, 800.0, 1600.0, 3200.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  200.0 |        0.0 |
        |   2 |  299.0 |        0.0 |
        |   3 |  300.0 |        0.0 |
        |   4 |  301.0 |   0.000133 |
        |   5 |  400.0 |   1.182498 |
        |   6 |  800.0 |  21.249634 |
        |   7 | 1600.0 |  97.612368 |
        |   8 | 3200.0 | 313.415248 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  200.0 |        0.0 |
        |   2 |  299.0 |        0.0 |
        |   3 |  300.0 |   0.000033 |
        |   4 |  301.0 |   0.000176 |
        |   5 |  400.0 |   1.182542 |
        |   6 |  800.0 |   21.24972 |
        |   7 | 1600.0 |  97.612538 |
        |   8 | 3200.0 | 313.415588 |
    """

    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.PsiAE,
        wland_control.B,
        wland_control.SH,
    )
    DERIVEDPARAMETERS = (wland_derived.NUG, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_states.DG,)
    RESULTSEQUENCES = (wland_aides.DVEq,)
    SUBMETHODS = (Return_DVH_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            x0: float = -10.0 * con.sh
            if sta.dg > con.psiae:
                t1: float = model.quaddveq_v1.integrate(x0, con.psiae, 2, 20, 1e-8)
                t2: float = model.quaddveq_v1.integrate(con.psiae, sta.dg, 2, 20, 1e-8)
                aid.dveq = t1 + t2
            else:
                aid.dveq = model.quaddveq_v1.integrate(x0, sta.dg, 2, 20, 1e-8)
        else:
            aid.dveq = modelutils.nan


class Calc_DVEq_V3(modeltools.Method):
    r"""Calculate the equilibrium storage deficit of the vadose zone.

    Basic equation (discontinuous):
      .. math::
        DHEq = ThetaR \cdot DG + \begin{cases}
          0 &|\ DG \leq PsiAE
          \\
          ThetaS \cdot \left( DG - \frac{DG^{1-1/b}}{(1-1/b) \cdot PsiAE^{-1/B}} -
          \frac{PsiAE}{1-B} \right) &|\ PsiAE < DG
        \end{cases}

    Method |Calc_DVEq_V3| extends the original `WALRUS`_ relationship between the
    groundwater depth and the equilibrium water deficit of the vadose zone defined
    by equation 5 of :cite:t:`ref-Brauer2014` and implemented into application model
    |wland| by method |Calc_DVEq_V1|.  Parameter |ThetaR| introduces a (small)
    amount of water to fill the tension-saturated area directly above the groundwater
    table.  This "residual saturation" allows the direct injection of water into
    groundwater without risking infinitely fast groundwater depth changes.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> thetar(0.01)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_dveq_v3,
        ...     last_example=8,
        ...     parseqs=(states.dg, aides.dveq)
        ... )
        >>> test.nexts.dg = 200.0, 299.0, 300.0, 301.0, 400.0, 800.0, 1600.0, 3200.0

        Without smoothing:

        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  200.0 |        2.0 |
        |   2 |  299.0 |       2.99 |
        |   3 |  300.0 |        3.0 |
        |   4 |  301.0 |    3.01013 |
        |   5 |  400.0 |   5.152935 |
        |   6 |  800.0 |  28.718393 |
        |   7 | 1600.0 | 111.172058 |
        |   8 | 3200.0 | 337.579867 |
    """

    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.ThetaR,
        wland_control.PsiAE,
        wland_control.B,
    )
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (wland_states.DG,)
    RESULTSEQUENCES = (wland_aides.DVEq,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            if sta.dg < con.psiae:
                aid.dveq = con.thetar * sta.dg
            else:
                aid.dveq = (con.thetas - con.thetar) * (
                    sta.dg
                    - sta.dg ** (1.0 - 1.0 / con.b)
                    / (1.0 - 1.0 / con.b)
                    / con.psiae ** (-1.0 / con.b)
                    - con.psiae / (1.0 - con.b)
                ) + con.thetar * sta.dg
        else:
            aid.dveq = modelutils.nan


class Return_DVH_V2(modeltools.Method):
    r"""Return the storage deficit of the vadose zone at a specific height above
    the groundwater table.

    Basic equation (discontinous):
      .. math::
        DVH = ThetaR + \begin{cases}
          0 &|\ DG \leq PsiAE
          \\
          (ThetaS-ThetaR) \cdot \left(1 - \left( \frac{h}{PsiAE} \right)^{-1/b} \right)
          &|\ PsiAE < DG
        \end{cases}

    The given equation is the differential of the equation underlying method
    |Calc_DVEq_V3| with respect to height.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> thetar(0.01)
        >>> psiae(300.0)
        >>> b(5.0)

        With smoothing:

        >>> from hydpy import repr_
        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> for h in [200.0, 299.0, 300.0, 301.0, 400.0, 500.0, 600.0]:
        ...     print(repr_(h), repr_(model.return_dvh_v2(h)))
        200.0 0.01
        299.0 0.01
        300.0 0.01
        301.0 0.010259
        400.0 0.031806
        500.0 0.047877
        600.0 0.060485

        Without smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> for h in [200.0, 299.0, 300.0, 301.0, 400.0, 500.0, 600.0]:
        ...     print(repr_(h), repr_(model.return_dvh_v2(h)))
        200.0 0.01
        299.0 0.010001
        300.0 0.010039
        301.0 0.01026
        400.0 0.031806
        500.0 0.047877
        600.0 0.060485
    """

    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.ThetaR,
        wland_control.PsiAE,
        wland_control.B,
    )
    DERIVEDPARAMETERS = (wland_derived.RH1,)

    @staticmethod
    def __call__(model: modeltools.Model, h: float) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        h = smoothutils.smooth_max1(h, con.psiae, der.rh1)
        return con.thetar + (
            (con.thetas - con.thetar) * (1.0 - (h / con.psiae) ** (-1.0 / con.b))
        )


class Calc_DVEq_V4(modeltools.Method):
    r"""Calculate the equilibrium storage deficit of the vadose zone.

    Basic equation:
      :math:`DHEq = \int_{0}^{DG} Return\_DVH\_V2(h) \ \ dh`

    Method |Calc_DVEq_V4| integrates |Return_DVH_V2| numerically based on the
    Lobatto-Gauß quadrature.  The short discussion in the documentation on
    |Calc_DVEq_V2| (which integrates |Return_DVH_V1|) also applies to |Calc_DVEq_V4|.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.nug(0)
        >>> model.calc_dveq_v4()
        >>> aides.dveq
        dveq(nan)

        >>> derived.nug(1)
        >>> thetas(0.4)
        >>> thetar(0.01)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_dveq_v4,
        ...     last_example=8,
        ...     parseqs=(states.dg, aides.dveq)
        ... )
        >>> test.nexts.dg = 200.0, 299.0, 300.0, 301.0, 400.0, 800.0, 1600.0, 3200.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  200.0 |        2.0 |
        |   2 |  299.0 |       2.99 |
        |   3 |  300.0 |        3.0 |
        |   4 |  301.0 |    3.01013 |
        |   5 |  400.0 |   5.152935 |
        |   6 |  800.0 |  28.718393 |
        |   7 | 1600.0 | 111.172058 |
        |   8 | 3200.0 | 337.579867 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  200.0 |        2.1 |
        |   2 |  299.0 |       3.09 |
        |   3 |  300.0 |   3.100032 |
        |   4 |  301.0 |   3.110172 |
        |   5 |  400.0 |   5.252979 |
        |   6 |  800.0 |  28.818477 |
        |   7 | 1600.0 | 111.272224 |
        |   8 | 3200.0 | 337.680198 |
    """

    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.ThetaR,
        wland_control.PsiAE,
        wland_control.B,
        wland_control.SH,
    )
    DERIVEDPARAMETERS = (wland_derived.NUG, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_states.DG,)
    RESULTSEQUENCES = (wland_aides.DVEq,)
    SUBMETHODS = (Return_DVH_V2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            x0: float = -10.0 * con.sh
            if sta.dg > con.psiae:
                t1: float = model.quaddveq_v2.integrate(x0, con.psiae, 2, 20, 1e-8)
                t2: float = model.quaddveq_v2.integrate(con.psiae, sta.dg, 2, 20, 1e-8)
                aid.dveq = t1 + t2
            else:
                aid.dveq = model.quaddveq_v2.integrate(x0, sta.dg, 2, 20, 1e-8)
        else:
            aid.dveq = modelutils.nan


class Return_ErrorDV_V1(modeltools.Method):
    r"""Calculate the difference between the equilibrium and the actual storage
    deficit of the vadose zone.

    Basic equation:
      :math:`DVEq_{Calc\_DVEq\_V3} - DV`

    Method |Return_ErrorDV_V1| uses |Calc_DVEq_V3| to calculate the equilibrium
    deficit corresponding to the current groundwater depth.  The following example
    shows that it resets the values |DG| and |DVEq|,  which it needs to change
    temporarily, to their original states.

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> thetar(0.01)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> states.dg = -9.0
        >>> aides.dveq = -99.0
        >>> states.dv = 3.152935
        >>> from hydpy import round_
        >>> round_(model.return_errordv_v1(400.0))
        2.0
        >>> states.dg
        dg(-9.0)
        >>> aides.dveq
        dveq(-99.0)

    Technical checks:

        As mentioned above, method |Return_ErrorDV_V1| changes the values of the
        sequences |DG| and |DVEq|, but only temporarily.  Hence, we do not include
        them in the method specifications, even if the following check considers this
        to be erroneous:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.wland.wland_model import Return_ErrorDV_V1
        >>> print(check_selectedvariables(Return_ErrorDV_V1))
        Definitely missing: dg and dveq
        Possibly missing (REQUIREDSEQUENCES):
            Calc_DVEq_V3: DG
        Possibly missing (RESULTSEQUENCES):
            Calc_DVEq_V3: DVEq
    """

    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.ThetaR,
        wland_control.PsiAE,
        wland_control.B,
    )
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (wland_states.DV,)
    SUBMETHODS = (Calc_DVEq_V3,)

    @staticmethod
    def __call__(model: modeltools.Model, dg: float) -> float:
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        dveq_old: float = aid.dveq
        dg_old: float = sta.dg
        sta.dg = dg
        model.calc_dveq_v3()
        d_delta: float = aid.dveq - sta.dv
        aid.dveq = dveq_old
        sta.dg = dg_old
        return d_delta


class Calc_DGEq_V1(modeltools.Method):
    r"""Calculate the equilibrium groundwater depth.

    Method |Calc_DGEq_V1| calculates the equilibrium groundwater depth for the
    current water deficit of the vadose zone, following methods |Return_DVH_V2|
    and |Calc_DVEq_V3|.  As we are not aware of an analytical solution, we solve
    it numerically via class |PegasusDGEq|, which performs an iterative root-search
    based on the `Pegasus method`_.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> thetar(0.01)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_dgeq_v1,
        ...     last_example=13,
        ...     parseqs=(states.dv, aides.dgeq)
        ... )
        >>> test.nexts.dv = (
        ...     -1.0, -0.01, 0.0, 0.01, 1.0, 2.0, 2.99, 3.0,
        ...     3.01012983, 5.1529353, 28.71839324, 111.1720584, 337.5798671)
        >>> test()
        | ex. |         dv |   dgeq |
        -----------------------------
        |   1 |       -1.0 |    0.0 |
        |   2 |      -0.01 |    0.0 |
        |   3 |        0.0 |    0.0 |
        |   4 |       0.01 |    1.0 |
        |   5 |        1.0 |  100.0 |
        |   6 |        2.0 |  200.0 |
        |   7 |       2.99 |  299.0 |
        |   8 |        3.0 |  300.0 |
        |   9 |    3.01013 |  301.0 |
        |  10 |   5.152935 |  400.0 |
        |  11 |  28.718393 |  800.0 |
        |  12 | 111.172058 | 1600.0 |
        |  13 | 337.579867 | 3200.0 |
    """
    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.ThetaR,
        wland_control.PsiAE,
        wland_control.B,
    )
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (wland_states.DV,)
    RESULTSEQUENCES = (wland_aides.DGEq,)
    SUBMETHODS = (Return_ErrorDV_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.psiae.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if sta.dv > 0.0:
            error: float = model.return_errordv_v1(con.psiae)
            if error <= 0.0:
                aid.dgeq = model.pegasusdgeq.find_x(
                    con.psiae, 10000.0, con.psiae, 1000000.0, 0.0, 1e-8, 20
                )
            else:
                aid.dgeq = model.pegasusdgeq.find_x(
                    0.0, con.psiae, 0.0, con.psiae, 0.0, 1e-8, 20
                )
        else:
            aid.dgeq = 0.0


class Calc_GF_V1(modeltools.Method):
    r"""Calculate the gain factor for changes in groundwater depth.

    Basic equation (discontinuous):
     .. math::
        GF = \begin{cases}
          0 &|\ DG \leq 0
          \\
          Return\_DVH\_V2(DGEq - DG)^{-1} &|\ 0 < DG
        \end{cases}

    The original `WALRUS`_ model attributes a passive role to groundwater dynamics.
    All water entering or leaving the underground is added to or subtracted from the
    vadose zone, and the groundwater table only reacts to such changes until it is in
    equilibrium with the updated water deficit in the vadose zone.  Hence, the movement
    of the groundwater table is generally slow.  However, in catchments with
    near-surface water tables, we often observe fast responses of groundwater to input
    forcings, maybe due to rapid infiltration along macropores or the re-infiltration
    of channel water.  In such situations, where the input water somehow bypasses the
    vadose zone, the speed of the rise of the groundwater table depends not only on
    the effective pore size of the soil material but also on the soil's degree of
    saturation directly above the groundwater table.  The smaller the remaining pore
    size, the larger the fraction between the water table's rise and the actual
    groundwater recharge.  We call this fraction the "gain factor" (|GF|).

    The `WALRUS`_ model does not explicitly account for the soil moisture in different
    depths above the groundwater table.  To keep the vertically lumped approach, we
    use the difference between the actual (|DG|) and the equilibrium groundwater depth
    (|DGEq|) as an indicator for the wetness above the groundwater table.  When |DG|
    is identical to |DGEq|, soil moisture and groundwater are in equilibrium.  Then,
    the tension-saturated area is fully developed, and the groundwater table moves
    quickly (depending on |ThetaR|).  The opposite case is when |DG| is much smaller
    than |DGEq|.  Such a situation occurs after a fast rise of the groundwater table
    when the soil water still needs much redistribution before it can be in equilibrium
    with groundwater.  In the most extreme case, the gain factor is just as large as
    indicated by the effective pore size alone (depending on |ThetaS|).

    The above discussion only applies as long as the groundwater table is below the
    soil surface.  For large-scale ponding (see :cite:t:`ref-Brauer2014`, section 5.11),
    we set |GF| to zero.  See the documentation on the methods |Calc_CDG_V1| and
    |Calc_FGS_V1| for related discussions.

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> thetar(0.01)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> sh(0.0)
        >>> aides.dgeq = 5000.0
        >>> derived.rh1.update()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_gf_v1,
        ...     last_example=16,
        ...     parseqs=(states.dg, aides.gf)
        ... )
        >>> test.nexts.dg = (
        ...     -10.0, -1.0, 0.0, 1.0, 10.0,
        ...     1000.0, 2000.0, 3000.0, 4000.0, 4500.0, 4600.0,
        ...     4690.0, 4699.0, 4700.0, 4701.0, 4710.0)
        >>> test()
        | ex. |     dg |        gf |
        ----------------------------
        |   1 |  -10.0 |       0.0 |
        |   2 |   -1.0 |       0.0 |
        |   3 |    0.0 |   2.81175 |
        |   4 |    1.0 |  5.623782 |
        |   5 |   10.0 |  5.626316 |
        |   6 | 1000.0 |  5.963555 |
        |   7 | 2000.0 |  6.496601 |
        |   8 | 3000.0 |  7.510869 |
        |   9 | 4000.0 | 10.699902 |
        |  10 | 4500.0 |  20.88702 |
        |  11 | 4600.0 | 31.440737 |
        |  12 | 4690.0 | 79.686112 |
        |  13 | 4699.0 | 97.470815 |
        |  14 | 4700.0 |     100.0 |
        |  15 | 4701.0 |     100.0 |
        |  16 | 4710.0 |     100.0 |

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |        gf |
        ----------------------------
        |   1 |  -10.0 |       0.0 |
        |   2 |   -1.0 |  0.056232 |
        |   3 |    0.0 |   2.81175 |
        |   4 |    1.0 |  5.567544 |
        |   5 |   10.0 |  5.626316 |
        |   6 | 1000.0 |  5.963555 |
        |   7 | 2000.0 |  6.496601 |
        |   8 | 3000.0 |  7.510869 |
        |   9 | 4000.0 | 10.699902 |
        |  10 | 4500.0 |  20.88702 |
        |  11 | 4600.0 | 31.440737 |
        |  12 | 4690.0 | 79.686112 |
        |  13 | 4699.0 | 97.465434 |
        |  14 | 4700.0 | 99.609455 |
        |  15 | 4701.0 | 99.994314 |
        |  16 | 4710.0 |     100.0 |
    """
    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.ThetaR,
        wland_control.PsiAE,
        wland_control.B,
    )
    DERIVEDPARAMETERS = (wland_derived.RH1,)
    REQUIREDSEQUENCES = (wland_states.DG, wland_aides.DGEq)
    RESULTSEQUENCES = (wland_aides.GF,)
    SUBMETHODS = (Return_DVH_V2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.gf = smoothutils.smooth_logistic1(sta.dg, der.rh1) / model.return_dvh_v2(
            aid.dgeq - sta.dg
        )


class Calc_CDG_V1(modeltools.Method):
    r"""Calculate the change in the groundwater depth due to percolation and
    capillary rise.

    Basic equation (discontinuous):
      :math:`CDG = \frac{DV-min(DVEq, DG)}{CV}`

    Note that this equation slightly differs from equation 6 of
    :cite:t:`ref-Brauer2014`.  In the case of large-scale ponding, |DVEq| always stays
    at zero, and we let |DG| take control of the speed of the water table movement.
    See the documentation on method |Calc_FGS_V1| for additional information on the
    differences between |wland| and `WALRUS`_ for this rare situation.

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> cv(10.0)
        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> states.dv = 100.0
        >>> states.dg = 1000.0
        >>> aides.dveq = 80.0
        >>> model.calc_cdg_v1()
        >>> fluxes.cdg
        cdg(1.0)

        Without large-scale ponding:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_cdg_v1,
        ...     last_example=5,
        ...     parseqs=(states.dg, fluxes.cdg)
        ... )

        With large-scale ponding and without smoothing:

        >>> states.dv = -10.0
        >>> aides.dveq = 0.0
        >>> test.nexts.dg = 10.0, 1.0, 0.0, -1.0, -10.0
        >>> test()
        | ex. |    dg |   cdg |
        -----------------------
        |   1 |  10.0 |  -0.5 |
        |   2 |   1.0 |  -0.5 |
        |   3 |   0.0 |  -0.5 |
        |   4 |  -1.0 | -0.45 |
        |   5 | -10.0 |   0.0 |

        With large-scale ponding and with smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |    dg |       cdg |
        ---------------------------
        |   1 |  10.0 |      -0.5 |
        |   2 |   1.0 | -0.499891 |
        |   3 |   0.0 | -0.492458 |
        |   4 |  -1.0 | -0.449891 |
        |   5 | -10.0 |       0.0 |
    """

    CONTROLPARAMETERS = (wland_control.CV,)
    DERIVEDPARAMETERS = (wland_derived.NUG, wland_derived.RH1)
    REQUIREDSEQUENCES = (wland_states.DG, wland_states.DV, wland_aides.DVEq)
    RESULTSEQUENCES = (wland_fluxes.CDG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            target: float = smoothutils.smooth_min1(aid.dveq, sta.dg, der.rh1)
            flu.cdg = (sta.dv - target) / con.cv
        else:
            flu.cdg = 0.0


class Calc_CDG_V2(modeltools.Method):
    r"""Calculate the vadose zone's storage deficit change due to percolation,
    capillary rise, macropore infiltration, seepage, groundwater drainage, and channel
    water infiltration.

    Basic equation:
      :math:`CDG = \frac{DV-min(DVEq, DG)}{CV} + GF \cdot \big( FGS - PV - FXG \big)`

    Method |Calc_CDG_V2| extends |Calc_CDG_V1|, which implements the (nearly) original
    `WALRUS`_ relationship defined by equation 6 of :cite:t:`ref-Brauer2014`).  See the
    documentation on method |Calc_GF_V1| for a comprehensive explanation of the reason
    for this extension.

    Examples:

        Without large-scale ponding:

        >>> from hydpy.models.wland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> cv(10.0)
        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> states.dv = 100.0
        >>> states.dg = 1000.0
        >>> fluxes.pv = 1.0
        >>> fluxes.fxg = 2.0
        >>> fluxes.fgs = 4.0
        >>> aides.dveq = 80.0
        >>> aides.gf = 2.0
        >>> model.calc_cdg_v2()
        >>> fluxes.cdg
        cdg(3.0)

        With large-scale ponding and without smoothing:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_cdg_v2,
        ...     last_example=5,
        ...     parseqs=(states.dg, fluxes.cdg)
        ... )
        >>> aides.gf = 0.0
        >>> states.dv = -10.0
        >>> aides.dveq = 0.0
        >>> test.nexts.dg = 10.0, 1.0, 0.0, -1.0, -10.0
        >>> test()
        | ex. |    dg |   cdg |
        -----------------------
        |   1 |  10.0 |  -0.5 |
        |   2 |   1.0 |  -0.5 |
        |   3 |   0.0 |  -0.5 |
        |   4 |  -1.0 | -0.45 |
        |   5 | -10.0 |   0.0 |

        With large-scale ponding and with smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |    dg |       cdg |
        ---------------------------
        |   1 |  10.0 |      -0.5 |
        |   2 |   1.0 | -0.499891 |
        |   3 |   0.0 | -0.492458 |
        |   4 |  -1.0 | -0.449891 |
        |   5 | -10.0 |       0.0 |
    """

    CONTROLPARAMETERS = (wland_control.CV,)
    DERIVEDPARAMETERS = (wland_derived.NUG, wland_derived.RH1)
    REQUIREDSEQUENCES = (
        wland_fluxes.PV,
        wland_fluxes.FGS,
        wland_fluxes.FXG,
        wland_states.DG,
        wland_states.DV,
        wland_aides.DVEq,
        wland_aides.GF,
    )
    RESULTSEQUENCES = (wland_fluxes.CDG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            target: float = smoothutils.smooth_min1(aid.dveq, sta.dg, der.rh1)
            cdg_slow: float = (sta.dv - target) / con.cv
            cdg_fast: float = aid.gf * (flu.fgs - flu.pv - flu.fxg)
            flu.cdg = cdg_slow + cdg_fast
        else:
            flu.cdg = 0.0


class Calc_FGS_V1(modeltools.Method):
    r"""Calculate the groundwater drainage or surface water infiltration.

    For large-scale ponding, |wland| and `WALRUS`_ calculate |FGS| differently
    (even for discontinuous parameterisations).  The `WALRUS`_  model redistributes
    water instantaneously in such cases (see :cite:t:`ref-Brauer2014`, section 5.11),
    which relates to infinitely high flow velocities and cannot be handled by the
    numerical integration algorithm underlying |wland|.  Hence, we instead introduce
    the parameter |CGF|.  Setting it to a value larger than zero increases the flow
    velocity with increasing large-scale ponding.  The larger the value of |CGF|,
    the stronger the functional similarity of both approaches.  But note that very
    high values can result in increased computation times.

    Basic equations (discontinous):
      :math:`Gradient = CD - DG - HS`

      :math:`ContactSurface = max \left( CD - DG, HS \right)`

      :math:`Excess = max \left( -DG, HS - CD, 0 \right)`

      :math:`Conductivity = \frac{1 + CGF \cdot Excess}{CG}`

      :math:`FGS = Gradient \cdot ContactSurface \cdot Conductivity`

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> cg(10000.0)
        >>> derived.cd(600.0)
        >>> states.hs = 300.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_fgs_v1,
        ...                 last_example=15,
        ...                 parseqs=(states.dg, states.hs, fluxes.fgs))
        >>> test.nexts.dg = (
        ...     -100.0, -1.0, 0.0, 1.0, 100.0, 200.0, 290.0, 299.0,
        ...     300.0, 301.0, 310.0, 400.0, 500.0, 600.0, 700.0)

        Without smoothing and without increased conductivity for large-scale ponding:

        >>> cgf(0.0)
        >>> sh(0.0)
        >>> derived.rh2.update()
        >>> test()
        | ex. |     dg |    hs |     fgs |
        ----------------------------------
        |   1 | -100.0 | 300.0 |    14.0 |
        |   2 |   -1.0 | 300.0 | 9.04505 |
        |   3 |    0.0 | 300.0 |     9.0 |
        |   4 |    1.0 | 300.0 | 8.95505 |
        |   5 |  100.0 | 300.0 |     5.0 |
        |   6 |  200.0 | 300.0 |     2.0 |
        |   7 |  290.0 | 300.0 |   0.155 |
        |   8 |  299.0 | 300.0 | 0.01505 |
        |   9 |  300.0 | 300.0 |     0.0 |
        |  10 |  301.0 | 300.0 |  -0.015 |
        |  11 |  310.0 | 300.0 |   -0.15 |
        |  12 |  400.0 | 300.0 |    -1.5 |
        |  13 |  500.0 | 300.0 |    -3.0 |
        |  14 |  600.0 | 300.0 |    -4.5 |
        |  15 |  700.0 | 300.0 |    -6.0 |

        Without smoothing but with increased conductivity for large-scale ponding:

        >>> cgf(0.1)
        >>> test()
        | ex. |     dg |    hs |      fgs |
        -----------------------------------
        |   1 | -100.0 | 300.0 |    294.0 |
        |   2 |   -1.0 | 300.0 | 10.85406 |
        |   3 |    0.0 | 300.0 |      9.0 |
        |   4 |    1.0 | 300.0 |  8.95505 |
        |   5 |  100.0 | 300.0 |      5.0 |
        |   6 |  200.0 | 300.0 |      2.0 |
        |   7 |  290.0 | 300.0 |    0.155 |
        |   8 |  299.0 | 300.0 |  0.01505 |
        |   9 |  300.0 | 300.0 |      0.0 |
        |  10 |  301.0 | 300.0 |   -0.015 |
        |  11 |  310.0 | 300.0 |    -0.15 |
        |  12 |  400.0 | 300.0 |     -1.5 |
        |  13 |  500.0 | 300.0 |     -3.0 |
        |  14 |  600.0 | 300.0 |     -4.5 |
        |  15 |  700.0 | 300.0 |     -6.0 |

        With smoothing and with increased conductivity for large-scale ponding:

        >>> sh(1.0)
        >>> derived.rh2.update()
        >>> test()
        | ex. |     dg |    hs |      fgs |
        -----------------------------------
        |   1 | -100.0 | 300.0 |    294.0 |
        |   2 |   -1.0 | 300.0 | 10.87215 |
        |   3 |    0.0 | 300.0 | 9.369944 |
        |   4 |    1.0 | 300.0 |  8.97296 |
        |   5 |  100.0 | 300.0 |      5.0 |
        |   6 |  200.0 | 300.0 |      2.0 |
        |   7 |  290.0 | 300.0 |    0.155 |
        |   8 |  299.0 | 300.0 |  0.01505 |
        |   9 |  300.0 | 300.0 |      0.0 |
        |  10 |  301.0 | 300.0 |   -0.015 |
        |  11 |  310.0 | 300.0 |    -0.15 |
        |  12 |  400.0 | 300.0 |     -1.5 |
        |  13 |  500.0 | 300.0 |     -3.0 |
        |  14 |  600.0 | 300.0 |     -4.5 |
        |  15 |  700.0 | 300.0 |     -6.0 |
    """

    CONTROLPARAMETERS = (wland_control.CG, wland_control.CGF)
    DERIVEDPARAMETERS = (wland_derived.CD, wland_derived.NUG, wland_derived.RH2)
    REQUIREDSEQUENCES = (wland_states.DG, wland_states.HS)
    RESULTSEQUENCES = (wland_fluxes.FGS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if der.nug:
            gradient: float = der.cd - sta.dg - sta.hs
            contactsurface: float = der.cd - sta.dg
            contactsurface = smoothutils.smooth_max1(contactsurface, sta.hs, der.rh2)
            excess: float = sta.hs - der.cd
            excess = smoothutils.smooth_max2(-sta.dg, excess, 0.0, der.rh2)
            conductivity: float = (1.0 + con.cgf * excess) / con.cg
            flu.fgs = gradient * contactsurface * conductivity
        else:
            flu.fgs = 0.0


class Calc_FQS_V1(modeltools.Method):
    r"""Calculate the quickflow.

    Basic equation:
      :math:`FQS = \frac{HQ}{CQ}`

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nu(2)
        >>> cq(10.0)
        >>> states.hq = 100.0
        >>> model.calc_fqs_v1()
        >>> fluxes.fqs
        fqs(5.0)

        Without land areas, quickflow is zero:

        >>> nu(1)
        >>> model.calc_fqs_v1()
        >>> fluxes.fqs
        fqs(0.0)
    """

    CONTROLPARAMETERS = (wland_control.NU, wland_control.CQ)
    REQUIREDSEQUENCES = (wland_states.HQ,)
    RESULTSEQUENCES = (wland_fluxes.FQS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if con.nu > 1:
            flu.fqs = sta.hq / con.cq
        else:
            flu.fqs = 0.0


class Calc_RH_V1(modeltools.Method):
    r"""Let a submodel that complies with the |DischargeModel_V2| interface calculate
    the runoff height or, if no such submodel is available, equate it with all other
    flows in and out of the surface water storage.

    Basic equation (without submodel):
      :math:`RH = ASR \cdot (PS - ES + FXS) + ALR \cdot FQS + AGR \cdot FGS`

    Examples:

        >>> from hydpy.models.wland_v001 import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")

        Without an available submodel, |Calc_RH_V1| applies the given basic equation:

        >>> derived.asr(0.2)
        >>> derived.alr(0.8)
        >>> derived.agr(0.6)
        >>> fluxes.ps = 3.0
        >>> fluxes.fxs = 1.0
        >>> fluxes.es = 2.0
        >>> fluxes.fqs(0.5)
        >>> fluxes.fgs(0.2)
        >>> model.calc_rh_v1()
        >>> fluxes.rh
        rh(0.92)

        We use |q_walrus|, which implements WALRUS' standard approach for calculating
        |RH|, to demonstrate that |Calc_RH_V1| correctly uses submodels that follow the
        |DischargeModel_V2| interface:

        >>> sh(0.1)
        >>> states.hs(3000.0)
        >>> derived.cd(5000.0)
        >>> with model.add_dischargemodel_v2("q_walrus"):
        ...     crestheight(2.0)
        ...     bankfulldischarge(2.0)
        ...     dischargeexponent(2.0)
        >>> model.calc_rh_v1()
        >>> fluxes.rh
        rh(0.111111)
    """

    DERIVEDPARAMETERS = (wland_derived.ASR, wland_derived.ALR, wland_derived.AGR)
    REQUIREDSEQUENCES = (
        wland_fluxes.PS,
        wland_fluxes.ES,
        wland_fluxes.FXS,
        wland_fluxes.FQS,
        wland_fluxes.FGS,
        wland_states.HS,
    )
    RESULTSEQUENCES = (wland_fluxes.RH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if model.dischargemodel is None:
            flu.rh = (
                der.asr * (flu.fxs + flu.ps - flu.es)
                + der.alr * flu.fqs
                + der.agr * flu.fgs
            )
        elif model.dischargemodel_typeid == 2:
            flu.rh = cast(
                dischargeinterfaces.DischargeModel_V2, model.dischargemodel
            ).calculate_discharge(sta.hs / 1000.0)


class Update_IC_V1(modeltools.Method):
    r"""Update the interception storage.

    Basic equation:
      :math:`\frac{dIC}{dt} = PC - TF - EI`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.pc = 2.0
        >>> fluxes.tf = 1.0
        >>> fluxes.ei = 3.0
        >>> states.ic.old = 4.0
        >>> model.update_ic_v1()
        >>> states.ic
        ic(2.0, 0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.NUL,)
    REQUIREDSEQUENCES = (wland_fluxes.PC, wland_fluxes.TF, wland_fluxes.EI)
    UPDATEDSEQUENCES = (wland_states.IC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for k in range(der.nul):
            new.ic[k] = old.ic[k] + (flu.pc - flu.tf[k] - flu.ei[k])
        new.ic[der.nul] = 0


class Update_SP_V1(modeltools.Method):
    r"""Update the storage deficit.

    Basic equation:
      :math:`\frac{dSP}{dt} = SF - AM`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> derived.nul.update()
        >>> fluxes.sf = 1.0
        >>> fluxes.am = 2.0
        >>> states.sp.old = 3.0
        >>> model.update_sp_v1()
        >>> states.sp
        sp(2.0, 0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.NUL,)
    REQUIREDSEQUENCES = (wland_fluxes.SF, wland_fluxes.AM)
    UPDATEDSEQUENCES = (wland_states.SP,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for k in range(der.nul):
            new.sp[k] = old.sp[k] + (flu.sf[k] - flu.am[k])
        new.sp[der.nul] = 0


class Update_DV_V1(modeltools.Method):
    r"""Update the storage deficit of the vadose zone.

    Basic equation:
      :math:`\frac{dDV}{dt} = -(FXG + PV - ETV - FGS)`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> fluxes.fxg = 1.0
        >>> fluxes.pv = 2.0
        >>> fluxes.etv = 3.0
        >>> fluxes.fgs = 4.0
        >>> states.dv.old = 5.0
        >>> model.update_dv_v1()
        >>> states.dv
        dv(9.0)
    """
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (
        wland_fluxes.FXG,
        wland_fluxes.PV,
        wland_fluxes.ETV,
        wland_fluxes.FGS,
    )
    UPDATEDSEQUENCES = (wland_states.DV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.nug:
            new.dv = old.dv - (flu.fxg + flu.pv - flu.etv - flu.fgs)
        else:
            new.dv = modelutils.nan


class Update_DG_V1(modeltools.Method):
    r"""Update the groundwater depth.

    Basic equation:
      :math:`\frac{dDG}{dt} = CDG`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> states.dg.old = 2.0
        >>> fluxes.cdg = 3.0
        >>> model.update_dg_v1()
        >>> states.dg
        dg(5.0)
    """
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (wland_fluxes.CDG,)
    UPDATEDSEQUENCES = (wland_states.DG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.nug:
            new.dg = old.dg + flu.cdg
        else:
            new.dg = modelutils.nan


class Update_HQ_V1(modeltools.Method):
    r"""Update the level of the quickflow reservoir.

    Basic equation:
      :math:`\frac{dHQ}{dt} = PQ - FQS`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> states.hq.old = 2.0
        >>> fluxes.pq = 3.0
        >>> fluxes.fqs = 4.0
        >>> model.update_hq_v1()
        >>> states.hq
        hq(1.0)
    """

    REQUIREDSEQUENCES = (wland_fluxes.PQ, wland_fluxes.FQS)
    UPDATEDSEQUENCES = (wland_states.HQ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.hq = old.hq + (flu.pq - flu.fqs)


class Update_HS_V1(modeltools.Method):
    r"""Update the surface water level.

    Basic equation:
      :math:`\frac{dHS}{dt} =
      PS - ES + FXS + \frac{ALR \cdot FQS + AGR \cdot FGS - RH}{ASR}`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.alr(0.8)
        >>> derived.asr(0.2)
        >>> derived.agr(0.8)
        >>> states.hs.old = 2.0
        >>> fluxes.fxs = 3.0
        >>> fluxes.ps = 4.0
        >>> fluxes.es = 5.0
        >>> fluxes.fgs = 6.0
        >>> fluxes.fqs = 7.0
        >>> fluxes.rh = 8.0
        >>> model.update_hs_v1()
        >>> states.hs
        hs(16.0)
    """

    DERIVEDPARAMETERS = (wland_derived.ALR, wland_derived.ASR, wland_derived.AGR)
    REQUIREDSEQUENCES = (
        wland_fluxes.FXS,
        wland_fluxes.PS,
        wland_fluxes.ES,
        wland_fluxes.FGS,
        wland_fluxes.FQS,
        wland_fluxes.RH,
    )
    UPDATEDSEQUENCES = (wland_states.HS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.hs = (
            old.hs
            + (flu.fxs + flu.ps - flu.es)
            + (der.alr * flu.fqs + der.agr * flu.fgs - flu.rh) / der.asr
        )


class Calc_R_V1(modeltools.Method):
    r"""Calculate the runoff in m³/s.

    Basic equation:
       :math:`R = QF \cdot RH`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.qf(2.0)
        >>> fluxes.rh = 3.0
        >>> model.calc_r_v1()
        >>> fluxes.r
        r(6.0)
    """

    DERIVEDPARAMETERS = (wland_derived.QF,)
    REQUIREDSEQUENCES = (wland_fluxes.RH,)
    RESULTSEQUENCES = (wland_fluxes.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.r = der.qf * flu.rh


class Pass_R_V1(modeltools.Method):
    r"""Update the outlet link sequence.

    Basic equation:
       :math:`Q = R`
    """

    REQUIREDSEQUENCES = (wland_fluxes.R,)
    RESULTSEQUENCES = (wland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.r


class Get_Temperature_V1(modeltools.Method):
    """Get the current subbasin-wide air temperature value (that applies to all
    hydrological response units so that the given index does not matter).

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> inputs.t = 2.0
        >>> model.get_temperature_v1(0)
        2.0
        >>> model.get_temperature_v1(1)
        2.0
    """

    REQUIREDSEQUENCES = (wland_inputs.T,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.t


class Get_MeanTemperature_V1(modeltools.Method):
    """Get the current subbasin-wide air temperature value.

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> inputs.t = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_meantemperature_v1())
        2.0
    """

    REQUIREDSEQUENCES = (wland_inputs.T,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.t


class Get_Precipitation_V1(modeltools.Method):
    """Get the current subbasin-wide precipitation value (that applies to all
    hydrological response units so that the given index does not matter).

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> fluxes.pc = 2.0
        >>> model.get_precipitation_v1(0)
        2.0
        >>> model.get_precipitation_v1(1)
        2.0
    """

    REQUIREDSEQUENCES = (wland_fluxes.PC,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.pc


class Get_SnowCover_V1(modeltools.Method):
    """Get the selected response unit's current snow cover degree.

    Example:

        Each response unit with a non-zero amount of snow counts as completely covered:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> states.sp = 0.0, 2.0
        >>> model.get_snowcover_v1(0)
        0.0
        >>> model.get_snowcover_v1(1)
        1.0
    """

    REQUIREDSEQUENCES = (wland_states.SP,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        if sta.sp[k] > 0.0:
            return 1.0
        return 0.0


class PegasusDGEq(roottools.Pegasus):
    """Pegasus iterator for finding the equilibrium groundwater depth."""

    METHODS = (Return_ErrorDV_V1,)


class QuadDVEq_V1(quadtools.Quad):
    """Adaptive quadrature method for integrating the equilibrium storage deficit
    of the vadose zone."""

    METHODS = (Return_DVH_V1,)


class QuadDVEq_V2(quadtools.Quad):
    """Adaptive quadrature method for integrating the equilibrium storage deficit
    of the vadose zone."""

    METHODS = (Return_DVH_V2,)


class Model(modeltools.ELSModel):
    """The *HydPy-W-Land* model."""

    SOLVERPARAMETERS = (
        wland_solver.AbsErrorMax,
        wland_solver.RelErrorMax,
        wland_solver.RelDTMin,
        wland_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (Calc_PE_PET_V1, Calc_FR_V1, Calc_PM_V1)
    RECEIVER_METHODS = (Pick_HS_V1,)
    INTERFACE_METHODS = (
        Get_Temperature_V1,
        Get_MeanTemperature_V1,
        Get_Precipitation_V1,
        Get_SnowCover_V1,
    )
    ADD_METHODS = (
        Calc_PE_PET_PETModel_V1,
        Calc_PE_PET_PETModel_V2,
        Return_ErrorDV_V1,
        Return_DVH_V1,
        Return_DVH_V2,
    )
    PART_ODE_METHODS = (
        Calc_FXS_V1,
        Calc_FXG_V1,
        Calc_PC_V1,
        Calc_TF_V1,
        Calc_EI_V1,
        Calc_SF_V1,
        Calc_RF_V1,
        Calc_AM_V1,
        Calc_PS_V1,
        Calc_W_V1,
        Calc_PV_V1,
        Calc_PQ_V1,
        Calc_Beta_V1,
        Calc_ETV_V1,
        Calc_ES_V1,
        Calc_FQS_V1,
        Calc_FGS_V1,
        Calc_RH_V1,
        Calc_DVEq_V1,
        Calc_DVEq_V2,
        Calc_DVEq_V3,
        Calc_DVEq_V4,
        Calc_DGEq_V1,
        Calc_GF_V1,
        Calc_CDG_V1,
        Calc_CDG_V2,
    )
    FULL_ODE_METHODS = (
        Update_IC_V1,
        Update_SP_V1,
        Update_DV_V1,
        Update_DG_V1,
        Update_HQ_V1,
        Update_HS_V1,
    )
    OUTLET_METHODS = (Calc_ET_V1, Calc_R_V1, Pass_R_V1)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMODELS = (PegasusDGEq, QuadDVEq_V1, QuadDVEq_V2)

    petmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    pemodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    pemodel_typeid = modeltools.SubmodelTypeIDProperty()

    dischargemodel = modeltools.SubmodelProperty(dischargeinterfaces.DischargeModel_V2)
    dischargemodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    dischargemodel_typeid = modeltools.SubmodelTypeIDProperty()

    waterlevelmodel = modeltools.SubmodelProperty(stateinterfaces.WaterLevelModel_V1)
    waterlevelmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    waterlevelmodel_typeid = modeltools.SubmodelTypeIDProperty()


class BaseModel(modeltools.ELSModel):
    """Base model for |wland_v001| and |wland_v002|."""

    def check_waterbalance(self, initial_conditions: ConditionsModel) -> float:
        r"""Determine the water balance error of the previous simulation run in mm.

        Method |BaseModel.check_waterbalance| calculates the balance error as follows:

          .. math::
            Error = \Sigma In - \Sigma Out + \Sigma \Delta H -
            \Delta Vol_{basin} - \Delta Vol_{hru}
            \\ \\
            \Sigma In = \sum_{t=t_0}^{t_1} PC_t + FXG_t + FXS_t
            \\
            \Sigma Out = \sum_{t=t_0}^{t_1} ET_t + RH_t
            \\
            \Sigma \Delta H= ASR \cdot \sum_{t=t_0}^{t_1} DHS_t
            \\
            \Delta Vol_{basin} =
            ALR \cdot \big( HQ_{t1} - HQ_{t0} \big) +
            AGR \cdot \big( DV_{t1} - DV_{t0} \big) +
            ASR \cdot \big( HS_{t1} - HS_{t0} \big)
            \\
            \Delta Vol_{hru} = \sum_{k=1}^{NUL} AUR^k \cdot \Big(
            \big( IC_{t1}^k - IC_{t0}^k \big) + \big( SP_{t1}^k - SP_{t0}^k \big)
            \Big)

        The returned error should always be in scale with numerical precision so that
        it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation via
        property |Sequences.conditions|.  See the integration tests of the application
        model |wland_v001| for some examples.
        """
        control = self.parameters.control
        derived = self.parameters.derived
        inputs = self.sequences.inputs
        factors = self.sequences.factors
        fluxes = self.sequences.fluxes
        last = self.sequences.states
        first = initial_conditions["model"]["states"]
        ddv = (last.dv - first["dv"]) * derived.agr
        if numpy.isnan(ddv):
            ddv = 0.0
        return (
            sum(fluxes.pc.series)
            + sum(inputs.fxg.series)
            + sum(inputs.fxs.series)
            - sum(fluxes.et.series)
            - sum(fluxes.rh.series)
            + sum(factors.dhs.series) * derived.asr
            - sum((last.ic - first["ic"])[:-1] * control.aur[:-1])
            - sum((last.sp - first["sp"])[:-1] * control.aur[:-1])
            - (last.hq - first["hq"]) * derived.alr
            - (last.hs - first["hs"]) * derived.asr
            + ddv
        )


class Main_PETModel_V1(modeltools.ELSModel):
    """Base class for HydPy-W models that use submodels that comply with the
    |PETModel_V1| interface."""

    petmodel: modeltools.SubmodelProperty
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "petmodel",
        petinterfaces.PETModel_V1,
        petinterfaces.PETModel_V1.prepare_nmbzones,
        petinterfaces.PETModel_V1.prepare_subareas,
        petinterfaces.PETModel_V1.prepare_zonetypes,
        landtype_constants=wland_constants.LANDUSE_CONSTANTS,
        landtype_refindices=wland_control.LT,
        refweights=wland_control.AUR,
    )
    def add_petmodel_v1(
        self,
        petmodel: petinterfaces.PETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `petmodel` that follows the |PETModel_V1| interface.

        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep()
        >>> nu(3)
        >>> at(10.0)
        >>> aur(0.5, 0.3, 0.2)
        >>> lt(FIELD, TREES, WATER)
        >>> with model.add_petmodel_v1("evap_tw2002"):
        ...     nmbhru
        ...     hruarea
        ...     evapotranspirationfactor(field=1.0, trees=2.0, water=1.5)
        nmbhru(3)
        hruarea(5.0, 3.0, 2.0)

        >>> etf = model.petmodel.parameters.control.evapotranspirationfactor
        >>> etf
        evapotranspirationfactor(field=1.0, trees=2.0, water=1.5)
        >>> lt(TREES, FIELD, WATER)
        >>> etf
        evapotranspirationfactor(field=2.0, trees=1.0, water=1.5)
        >>> from hydpy import round_
        >>> round_(etf.average_values())
        1.4
        """
        control = self.parameters.control
        petmodel.prepare_nmbzones(control.nu.value)
        petmodel.prepare_zonetypes(control.lt.values)
        petmodel.prepare_subareas(control.at.value * control.aur.values)


class Main_PETModel_V2(modeltools.ELSModel):
    """Base class for HydPy-W models that use submodels that comply with the
    |PETModel_V2| interface."""

    petmodel: modeltools.SubmodelProperty
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "petmodel",
        petinterfaces.PETModel_V2,
        petinterfaces.PETModel_V2.prepare_nmbzones,
        petinterfaces.PETModel_V2.prepare_subareas,
        petinterfaces.PETModel_V2.prepare_zonetypes,
        petinterfaces.PETModel_V2.prepare_water,
        petinterfaces.PETModel_V2.prepare_interception,
        petinterfaces.PETModel_V2.prepare_soil,
        petinterfaces.PETModel_V2.prepare_plant,
        petinterfaces.PETModel_V2.prepare_tree,
        landtype_constants=wland_constants.LANDUSE_CONSTANTS,
        landtype_refindices=wland_control.LT,
        refweights=wland_control.AUR,
    )
    def add_petmodel_v2(
        self,
        petmodel: petinterfaces.PETModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `petmodel` that follows the |PETModel_V2| interface.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep()
        >>> nu(12)
        >>> at(10.0)
        >>> aur(0.006, 0.02, 0.034, 0.048, 0.062, 0.076,
        ...     0.09, 0.104, 0.118, 0.132, 0.146, 0.164)
        >>> lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE,
        ...    WETLAND, TREES, CONIFER, DECIDIOUS, MIXED, WATER)
        >>> with model.add_petmodel_v2("evap_pet_ambav1") as petmodel:
        ...     nmbhru
        ...     hrutype
        ...     water
        ...     interception
        ...     soil
        ...     plant
        ...     tree
        ...     petmodel.preparemethod2arguments["prepare_nmbzones"]
        ...     petmodel.preparemethod2arguments["prepare_subareas"]
        ...     groundalbedo(conifer=0.05, decidious=0.1, field=0.15, mixed=0.2,
        ...                  orchard=0.25, pasture=0.3, sealed=0.35, soil=0.4,
        ...                  trees=0.45, water=0.5, wetland=0.55, wine=0.6)
        nmbhru(12)
        hrutype(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE, WETLAND, TREES,
                CONIFER, DECIDIOUS, MIXED, WATER)
        water(conifer=False, decidious=False, field=False, mixed=False,
              orchard=False, pasture=False, sealed=False, soil=False,
              trees=False, water=True, wetland=False, wine=False)
        interception(conifer=True, decidious=True, field=True, mixed=True,
                     orchard=True, pasture=True, sealed=True, soil=True,
                     trees=True, water=False, wetland=True, wine=True)
        soil(conifer=True, decidious=True, field=True, mixed=True,
             orchard=True, pasture=True, sealed=False, soil=True, trees=True,
             water=False, wetland=True, wine=True)
        plant(conifer=True, decidious=True, field=True, mixed=True,
              orchard=True, pasture=True, sealed=False, soil=False,
              trees=True, water=False, wetland=True, wine=True)
        tree(conifer=True, decidious=True, field=False, mixed=True,
             orchard=False, pasture=False, sealed=False, soil=False,
             trees=False, water=False, wetland=False, wine=False)
        ((12,), {})
        ((array([0.06, 0.2 , 0.34, 0.48, 0.62, 0.76, 0.9 , 1.04, 1.18, 1.32, 1.46,
               1.64]),), {})

        >>> assert model is model.petmodel.tempmodel
        >>> assert model is model.petmodel.precipmodel
        >>> assert model is model.petmodel.snowcovermodel

        >>> ga = model.petmodel.parameters.control.groundalbedo
        >>> ga
        groundalbedo(conifer=0.05, decidious=0.1, field=0.15, mixed=0.2,
                     orchard=0.25, pasture=0.3, sealed=0.35, soil=0.4,
                     trees=0.45, water=0.5, wetland=0.55, wine=0.6)
        >>> lt(FIELD, SEALED, WINE, ORCHARD, SOIL, PASTURE,
        ...    WETLAND, TREES, CONIFER, DECIDIOUS, MIXED, WATER)
        >>> ga
        groundalbedo(conifer=0.05, decidious=0.1, field=0.35, mixed=0.2,
                     orchard=0.25, pasture=0.3, sealed=0.15, soil=0.4,
                     trees=0.45, water=0.5, wetland=0.55, wine=0.6)
        >>> from hydpy import round_
        >>> round_(ga.average_values())
        0.3117
        """
        control = self.parameters.control
        nu = control.nu.value
        lt = control.lt.values

        petmodel.prepare_nmbzones(nu)
        petmodel.prepare_zonetypes(lt)
        petmodel.prepare_subareas(control.at.value * control.aur.values)
        sel = numpy.full(nu, False, dtype=bool)
        sel[-1] = True
        petmodel.prepare_water(sel)
        sel = ~sel
        petmodel.prepare_interception(sel)
        sel[lt == SEALED] = False
        petmodel.prepare_soil(sel)
        sel[lt == SOIL] = False
        petmodel.prepare_plant(sel)
        sel = numpy.full(nu, False, dtype=bool)
        sel[lt == CONIFER] = True
        sel[lt == DECIDIOUS] = True
        sel[lt == MIXED] = True
        petmodel.prepare_tree(sel)


class Main_DischargeModel_V2(modeltools.ELSModel):
    """Base class for HydPy-W models that use submodels that comply with the
    |DischargeModel_V2| interface."""

    dischargemodel: modeltools.SubmodelProperty
    dischargemodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    dischargemodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "dischargemodel",
        dischargeinterfaces.DischargeModel_V2,
        dischargeinterfaces.DischargeModel_V2.prepare_channeldepth,
        dischargeinterfaces.DischargeModel_V2.prepare_tolerance,
    )
    def add_dischargemodel_v2(
        self,
        dischargemodel: dischargeinterfaces.DischargeModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `dischargemodel` that follows the |DischargeModel_V2|
        interface.

        Note the dependency on the derived parameter |CD|:

        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep()
        >>> sh(10.0)
        >>> with model.add_dischargemodel_v2("q_walrus", update=False):
        ...     pass
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to add a submodel \
to the main model `wland_v001`, the following error occurred: While trying to \
determine the missing value of the derived parameter `cd` of element `?`, the \
following error occurred: While trying to subtract variable `gl` and `BL` instance \
`bl(?)`, the following error occurred: For variable `bl`, no value has been defined \
so far.

        You can define its value manually for testing:

        >>> derived.cd(2000.0)
        >>> with model.add_dischargemodel_v2("q_walrus", update=False):
        ...     channeldepth
        ...     crestheighttolerance
        channeldepth(2.0)
        crestheighttolerance(0.01)

        >>> model.dischargemodel.parameters.control.channeldepth
        channeldepth(2.0)
        >>> model.dischargemodel.parameters.control.crestheighttolerance
        crestheighttolerance(0.01)

        However, |Main_DischargeModel_V2.add_dischargemodel_v2| updates the channel
        depth whenever possible to make the added submodel consistent with the main
        model's current control parameter values:

        >>> gl(4.0)
        >>> bl(3.0)
        >>> with model.add_dischargemodel_v2("q_walrus", update=False):
        ...     channeldepth
        ...     crestheighttolerance
        channeldepth(1.0)
        crestheighttolerance(0.01)

        >>> derived.cd
        cd(1000.0)
        >>> model.dischargemodel.parameters.control.channeldepth
        channeldepth(1.0)
        >>> model.dischargemodel.parameters.control.crestheighttolerance
        crestheighttolerance(0.01)
        """
        cd = self.parameters.derived.cd
        try:
            cd.update()
        except exceptiontools.AttributeNotReady:
            if not exceptiontools.attrready(cd, "value"):
                objecttools.augment_excmessage(
                    f"While trying to determine the missing value of the derived "
                    f"parameter {objecttools.elementphrase(cd)}"
                )
        dischargemodel.prepare_channeldepth(cd.value / 1000.0)
        dischargemodel.prepare_tolerance(self.parameters.control.sh.value / 1000.0)


class Main_WaterLevelModel_V1(modeltools.ELSModel):
    """Base class for HydPy-W models that use submodels that comply with the
    |WaterLevelModel_V1| interface."""

    waterlevelmodel: modeltools.SubmodelProperty
    waterlevelmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    waterlevelmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel("waterlevelmodel", stateinterfaces.WaterLevelModel_V1)
    def add_waterlevelmodel_v1(
        self,
        waterlevelmodel: stateinterfaces.WaterLevelModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `waterlevelmodel` that follows the |WaterLevelModel_V1|
        interface.

        >>> from hydpy.models.wland_v001 import *
        >>> parameterstep()
        >>> from hydpy.models import exch_waterlevel
        >>> with model.add_waterlevelmodel_v1(exch_waterlevel):
        ...     pass
        >>> assert isinstance(model.waterlevelmodel, exch_waterlevel.Model)
        """


class Sub_TempModel_V1(modeltools.ELSModel, tempinterfaces.TempModel_V1):
    """Base class for HydPy-W models that comply with the |TempModel_V1| submodel
    interface."""


class Sub_PrecipModel_V1(modeltools.ELSModel, precipinterfaces.PrecipModel_V1):
    """Base class for HydPy-W models that comply with the |PrecipModel_V1| submodel
    interface."""


class Sub_SnowCoverModel_V1(modeltools.ELSModel, stateinterfaces.SnowCoverModel_V1):
    """Base class for HydPy-W models that comply with the |SnowCoverModel_V1| submodel
    interface."""
