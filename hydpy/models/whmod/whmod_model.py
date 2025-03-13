# pylint: disable=missing-module-docstring

from typing import *

import numpy

from hydpy import config
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.interfaces import aetinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.cythons import modelutils

from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_control
from hydpy.models.whmod import whmod_derived
from hydpy.models.whmod import whmod_inputs
from hydpy.models.whmod import whmod_factors
from hydpy.models.whmod import whmod_fluxes
from hydpy.models.whmod import whmod_states


class Calc_Throughfall_InterceptedWater_V1(modeltools.Method):
    r"""Calculate the interception storage's throughfall and change in water content due
    to precipitation.

    Basic equation:
      .. math::
        T = \begin{cases}
        P &|\ I = C \\
        0 &|\ I \leq C
        \end{cases}
        \\
        I_{new} = I_{old} + P - I
        \\ \\
        T = Throughfall \\
        P = Precipitation \\
        I = InterceptedWater \\
        C = InterceptionCapacity

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> landtype(CORN, CORN, CORN, CORN, WATER)
        >>> interceptioncapacity.corn_jun = 2.0
        >>> interceptioncapacity.corn_jul = 2.5

        >>> from hydpy import pub
        >>> pub.timegrids = "2001-06-29", "2001-07-03", "1d"
        >>> derived.moy.update()

        >>> inputs.precipitation = 1.0
        >>> states.interceptedwater = 0.0, 1.0, 2.0, 3.0, nan
        >>> model.idx_sim = 1
        >>> model.calc_throughfall_interceptedwater_v1()
        >>> states.interceptedwater
        interceptedwater(1.0, 2.0, 2.0, 2.0, 0.0)
        >>> fluxes.throughfall
        throughfall(0.0, 0.0, 1.0, 2.0, 0.0)

        >>> inputs.precipitation = 0.0
        >>> states.interceptedwater = 0.0, 1.0, 2.0, 3.0, nan
        >>> model.idx_sim = 2
        >>> model.calc_throughfall_interceptedwater_v1()
        >>> states.interceptedwater
        interceptedwater(0.0, 1.0, 2.0, 2.5, 0.0)
        >>> fluxes.throughfall
        throughfall(0.0, 0.0, 0.0, 0.5, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.InterceptionCapacity,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY,)
    REQUIREDSEQUENCES = (whmod_inputs.Precipitation,)
    UPDATEDSEQUENCES = (whmod_states.InterceptedWater,)
    RESULTSEQUENCES = (whmod_fluxes.Throughfall,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        month = der.moy[model.idx_sim]
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                sta.interceptedwater[k] = 0.0
                flu.throughfall[k] = 0.0
            else:
                ic: float = con.interceptioncapacity[con.landtype[k] - 1, month]
                flu.throughfall[k] = max(
                    inp.precipitation + sta.interceptedwater[k] - ic, 0.0
                )
                sta.interceptedwater[k] += inp.precipitation - flu.throughfall[k]


class Calc_InterceptionEvaporation_InterceptedWater_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water.

    Basic equations:
      .. math::
        E = get\_interceptionevaporation()
        \\
        I_{new} = I_{old} - E
        \\ \\
        I = InterceptedWater \\
        E = InterceptionEvaporation

    Examples:

        We build an example based on |evap_aet_minhas| for calculating interception
        evaporation, which uses |evap_ret_io| for querying potential
        evapotranspiration:

        >>> from hydpy.models.whmod_rural import *
        >>> parameterstep("1h")
        >>> area(1.0)
        >>> nmbzones(5)
        >>> landtype(GRASS, DECIDUOUS, CORN, SEALED, WATER)
        >>> zonearea(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> interceptioncapacity.jun = 3.0
        >>> derived.moy.shape = 1
        >>> derived.moy(5)
        >>> availablefieldcapacity(0.1)
        >>> rootingdepth(0.1)
        >>> groundwaterdepth(0.1)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     with model.add_petmodel_v1("evap_ret_io"):
        ...         evapotranspirationfactor(0.6, 0.8, 1.0, 1.2, 1.4)
        ...         inputs.referenceevapotranspiration = 1.0

        |Calc_InterceptionEvaporation_InterceptedWater_AETModel_V1| uses the flux
        returned by the submodel to adjust |InterceptedWater|:

        >>> states.interceptedwater = 2.0
        >>> model.calc_interceptionevaporation_interceptedwater_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(0.6, 0.8, 1.0, 1.2, 0.0)
        >>> states.interceptedwater
        interceptedwater(1.4, 1.2, 1.0, 0.8, 0.0)

        |Calc_InterceptionEvaporation_InterceptedWater_AETModel_V1| eventually reduces
        |InterceptionEvaporation| so that |InterceptedWater| does not become negative:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = 5.0
        >>> states.interceptedwater = 2.0
        >>> model.calc_interceptionevaporation_interceptedwater_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(2.0, 2.0, 2.0, 2.0, 0.0)
        >>> states.interceptedwater
        interceptedwater(0.0, 0.0, 0.0, 0.0, 0.0)

        In contrast, |Calc_InterceptionEvaporation_InterceptedWater_AETModel_V1| does
        not reduce negative |InterceptionEvaporation| values (condensation) that cause
        an overshoot of the interception storage capacity:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = -3.0
        >>> states.interceptedwater = 2.0
        >>> model.calc_interceptionevaporation_interceptedwater_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(-1.8, -2.4, -3.0, -3.6, 0.0)
        >>> states.interceptedwater
        interceptedwater(3.8, 4.4, 5.0, 5.6, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    UPDATEDSEQUENCES = (whmod_states.InterceptedWater,)
    RESULTSEQUENCES = (whmod_fluxes.InterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_interceptionevaporation()
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.interceptionevaporation[k] = 0.0
                sta.interceptedwater[k] = 0.0
            else:
                flu.interceptionevaporation[k] = min(
                    submodel.get_interceptionevaporation(k), sta.interceptedwater[k]
                )
                sta.interceptedwater[k] -= flu.interceptionevaporation[k]


class Calc_InterceptionEvaporation_InterceptedWater_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_InterceptionEvaporation_InterceptedWater_AETModel_V1,)
    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    UPDATEDSEQUENCES = (whmod_states.InterceptedWater,)
    RESULTSEQUENCES = (whmod_fluxes.InterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_interceptionevaporation_interceptedwater_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )


class Calc_LakeEvaporation_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    lake evaporation.

    Basic equation:
      .. math::
        LakeEvaporation = get\_waterevaporation()

    Example:

        We build an example based on |evap_aet_minhas| for calculating water
        evaporation, which uses |evap_ret_io| for querying potential
        evapotranspiration:

        >>> from hydpy.models.whmod_rural import *
        >>> parameterstep("1h")
        >>> area(1.0)
        >>> nmbzones(5)
        >>> landtype(GRASS, DECIDUOUS, CORN, SEALED, WATER)
        >>> zonearea(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> interceptioncapacity.jun = 3.0
        >>> derived.moy.shape = 1
        >>> derived.moy(5)
        >>> availablefieldcapacity(0.1)
        >>> rootingdepth(0.1)
        >>> groundwaterdepth(0.1)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     with model.add_petmodel_v1("evap_ret_io"):
        ...         evapotranspirationfactor(0.6, 0.8, 1.0, 1.2, 1.4)
        ...         inputs.referenceevapotranspiration = 1.0

        |Calc_LakeEvaporation_AETModel_V1| stores the flux returned by the submodel
        without any modifications:

        >>> model.aetmodel.determine_interceptionevaporation()
        >>> model.calc_lakeevaporation_v1()
        >>> fluxes.lakeevaporation
        lakeevaporation(0.0, 0.0, 0.0, 0.0, 1.4)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    RESULTSEQUENCES = (whmod_fluxes.LakeEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_waterevaporation()
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.lakeevaporation[k] = submodel.get_waterevaporation(k)
            else:
                flu.lakeevaporation[k] = 0.0


class Calc_LakeEvaporation_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    lake evaporation."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_LakeEvaporation_AETModel_V1,)
    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    RESULTSEQUENCES = (whmod_fluxes.LakeEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_lakeevaporation_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )


class Calc_PotentialSnowmelt_V1(modeltools.Method):
    r"""Calculcate the potential snowmelt with the degree day method.

    Basic equation:
      .. math::
        P = \begin{cases}
        0 &|\ T \leq 0 \\
        D \cdot T &|\ T > 0
        \end{cases}
        \\ \\
        P = PotentialSnowmelt \\
        D = DegreeDayFactor \\
        T = Temperature

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep("1d")
        >>> simulationstep("1d")
        >>> nmbzones(3)
        >>> landtype(GRASS, SEALED, WATER)
        >>> degreedayfactor(grass=3.0, sealed=4.0)

        >>> inputs.temperature = -2.0
        >>> model.calc_potentialsnowmelt_v1()
        >>> fluxes.potentialsnowmelt
        potentialsnowmelt(0.0, 0.0, 0.0)

        >>> inputs.temperature = 0.0
        >>> model.calc_potentialsnowmelt_v1()
        >>> fluxes.potentialsnowmelt
        potentialsnowmelt(0.0, 0.0, 0.0)

        >>> inputs.temperature = 2.0
        >>> model.calc_potentialsnowmelt_v1()
        >>> fluxes.potentialsnowmelt
        potentialsnowmelt(6.0, 8.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.DegreeDayFactor,
    )
    REQUIREDSEQUENCES = (whmod_inputs.Temperature,)
    RESULTSEQUENCES = (whmod_fluxes.PotentialSnowmelt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if (con.landtype[k] == WATER) or (inp.temperature <= 0.0):
                flu.potentialsnowmelt[k] = 0.0
            else:
                flu.potentialsnowmelt[k] = con.degreedayfactor[k] * inp.temperature


class Calc_Snowmelt_Snowpack_V1(modeltools.Method):
    r"""Calculatethe actual snowmelt and update the snow's water content.

    Basic equations:
      .. math::
        M = \begin{cases}
        0 &|\ T \leq 0 \\
        min(P, \, S_{old}) &|\ T > 0
        \end{cases}
        \\
        S_{new} = \begin{cases}
        S_{old} + F &|\ T \leq 0
        \\
        S_{old} - M &|\ T > 0
        \end{cases}
        \\ \\
        M = Snowmelt \\
        P = PotentialSnowmelt \\
        S = SnowPack \\
        T = Temperature \\
        F = Throughfall

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep("1d")
        >>> simulationstep("1d")
        >>> nmbzones(3)
        >>> landtype(GRASS, SEALED, WATER)
        >>> fluxes.throughfall = 1.0

        >>> inputs.temperature = 0.0
        >>> states.snowpack = 0.0, 2.0, 0.0
        >>> model.calc_snowmelt_snowpack_v1()
        >>> fluxes.snowmelt
        snowmelt(0.0, 0.0, 0.0)
        >>> states.snowpack
        snowpack(1.0, 3.0, 0.0)

        >>> inputs.temperature = 1.0
        >>> states.snowpack = 0.0, 3.0, 0.0
        >>> fluxes.potentialsnowmelt = 2.0
        >>> model.calc_snowmelt_snowpack_v1()
        >>> fluxes.snowmelt
        snowmelt(0.0, 2.0, 0.0)
        >>> states.snowpack
        snowpack(0.0, 1.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (
        whmod_inputs.Temperature,
        whmod_fluxes.Throughfall,
        whmod_fluxes.PotentialSnowmelt,
    )
    UPDATEDSEQUENCES = (whmod_states.Snowpack,)
    RESULTSEQUENCES = (whmod_fluxes.Snowmelt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.snowmelt[k] = 0.0
                sta.snowpack[k] = 0.0
            elif inp.temperature <= 0.0:
                flu.snowmelt[k] = 0.0
                sta.snowpack[k] += flu.throughfall[k]
            elif flu.potentialsnowmelt[k] < sta.snowpack[k]:
                flu.snowmelt[k] = flu.potentialsnowmelt[k]
                sta.snowpack[k] -= flu.snowmelt[k]
            else:
                flu.snowmelt[k] = sta.snowpack[k]
                sta.snowpack[k] = 0.0


class Calc_Ponding_V1(modeltools.Method):
    r"""Calculate the (potential) ponding of throughfall and snowmelt of land surfaces.

    Basic equation:
      .. math::
        P = \begin{cases}
        0 &|\ T \leq 0 \\
        F + M &|\ T > 0
        \end{cases}
        \\ \\
        P = Ponding \\
        F = Throughfall \\
        M = Snowmelt \\
        T = Temperature

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(GRASS, SEALED, WATER)

        >>> inputs.temperature = 0.0
        >>> model.calc_ponding_v1()
        >>> fluxes.ponding
        ponding(0.0, 0.0, 0.0)

        >>> inputs.temperature = 1.0
        >>> fluxes.throughfall = 2.0
        >>> fluxes.snowmelt = 3.0
        >>> model.calc_ponding_v1()
        >>> fluxes.ponding
        ponding(5.0, 5.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (
        whmod_inputs.Temperature,
        whmod_fluxes.Throughfall,
        whmod_fluxes.Snowmelt,
    )
    RESULTSEQUENCES = (whmod_fluxes.Ponding,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if (con.landtype[k] == WATER) or (inp.temperature <= 0.0):
                flu.ponding[k] = 0.0
            else:
                flu.ponding[k] = flu.throughfall[k] + flu.snowmelt[k]


class Calc_SurfaceRunoff_V1(modeltools.Method):
    """Calculate the surface runoff from sealed areas.

    Basic equation:
      .. math::
        SurfaceRunoff = Ponding

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(SEALED, WATER, GRASS)
        >>> fluxes.ponding = 3.0
        >>> model.calc_surfacerunoff_v1()
        >>> fluxes.surfacerunoff
        surfacerunoff(3.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (whmod_fluxes.Ponding,)
    RESULTSEQUENCES = (whmod_fluxes.SurfaceRunoff,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.surfacerunoff[k] = flu.ponding[k]
            else:
                flu.surfacerunoff[k] = 0.0


class Calc_RelativeSoilMoisture_V1(modeltools.Method):
    r"""Calculate the relative soil water content.

    Basic equation:
      .. math::
        R = S / M
        \\ \\
        R = RelativeSoilMoisture \\
        S = SoilMoisture \\
        M = MaxSoilWater

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(7)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE)
        >>> derived.maxsoilwater(200.0, 200.0, 200.0, 200.0, 200.0, 0.0, nan)
        >>> states.soilmoisture = 0.0, 50.0, 100.0, 150.0, 200.0, 0.0, nan
        >>> model.calc_relativesoilmoisture_v1()
        >>> factors.relativesoilmoisture
        relativesoilmoisture(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
        """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.SoilType)
    DERIVEDPARAMETERS = (whmod_derived.MaxSoilWater,)
    REQUIREDSEQUENCES = (whmod_states.SoilMoisture,)
    RESULTSEQUENCES = (whmod_factors.RelativeSoilMoisture,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if (con.soiltype[k] == NONE) or (der.maxsoilwater[k] <= 0.0):
                fac.relativesoilmoisture[k] = 0.0
            else:
                fac.relativesoilmoisture[k] = sta.soilmoisture[k] / der.maxsoilwater[k]


class Calc_Percolation_V1(modeltools.Method):
    r"""Calculate the percolation out of the soil storage.

    Basic equation:
      .. math::
        Percolation = P \cdot R ^ {\beta}
        \\ \\
        P = Ponding \\
        R = RelativeSoilMoisture \\
        \beta = BETA

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(7)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE)
        >>> derived.beta(2.0)
        >>> fluxes.ponding(10.0)
        >>> factors.relativesoilmoisture = 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, nan
        >>> model.calc_percolation_v1()
        >>> fluxes.percolation
        percolation(0.0, 0.4, 1.6, 3.6, 6.4, 10.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.SoilType)
    DERIVEDPARAMETERS = (whmod_derived.Beta,)
    REQUIREDSEQUENCES = (whmod_fluxes.Ponding, whmod_factors.RelativeSoilMoisture)
    RESULTSEQUENCES = (whmod_fluxes.Percolation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.soiltype[k] == NONE:
                flu.percolation[k] = 0.0
            else:
                flu.percolation[k] = (
                    flu.ponding[k] * fac.relativesoilmoisture[k] ** der.beta[k]
                )


class Calc_SoilEvapotranspiration_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    soil evapotranspiration.

    Basic equation:
      .. math::
        SoilEvapotranspiration = get\_soilevapotranspiration()

    Example:

        We build an example based on |evap_aet_minhas|:

        >>> from hydpy.models.whmod_rural import *
        >>> parameterstep("1h")
        >>> area(1.0)
        >>> nmbzones(5)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, WATER)
        >>> soiltype(SAND, SAND, SAND, SAND, NONE)
        >>> zonearea(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> availablefieldcapacity(0.1)
        >>> rootingdepth(1.0)
        >>> groundwaterdepth(1.0)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     dissefactor(5.0)

        |Calc_SoilEvapotranspiration_AETModel_V1| stores the flux returned by the
        submodel without any modifications:

        >>> states.soilmoisture = 0.0, 0.0, 50.0, 100.0, 0.0
        >>> model.aetmodel.sequences.fluxes.potentialinterceptionevaporation = 5.0
        >>> model.aetmodel.sequences.fluxes.potentialsoilevapotranspiration = 5.0
        >>> model.aetmodel.sequences.fluxes.interceptionevaporation = 3.0
        >>> model.calc_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 1.717962, 2.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.SoilType)
    RESULTSEQUENCES = (whmod_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_soilevapotranspiration()
        for k in range(con.nmbzones):
            if con.soiltype[k] == NONE:
                flu.soilevapotranspiration[k] = 0.0
            else:
                flu.soilevapotranspiration[k] = submodel.get_soilevapotranspiration(k)


class Calc_SoilEvapotranspiration_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate soil
    evapotranspiration."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_SoilEvapotranspiration_AETModel_V1,)
    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.SoilType)
    RESULTSEQUENCES = (whmod_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_soilevapotranspiration_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )


class Calc_TotalEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the sum of interception evaporation, lake evaporation, and soil
    evapotranspiration.

    Basic equation:
      .. math::
        T = I + S + L
        \\ \\
        T = TotalEvapotranspiration \\
        I = InterceptionEvaporation \\
        S = SoilEvapotranspiration \\
        L = LakeEvaporation

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(GRASS, SEALED, WATER)
        >>> soiltype(SAND, NONE, NONE)
        >>> fluxes.interceptionevaporation = 1.0, 2.0, nan
        >>> fluxes.soilevapotranspiration = 3.0, nan, nan
        >>> fluxes.lakeevaporation = nan, nan, 5.0
        >>> model.calc_totalevapotranspiration_v1()
        >>> fluxes.totalevapotranspiration
        totalevapotranspiration(4.0, 2.0, 5.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.SoilType,
    )
    REQUIREDSEQUENCES = (
        whmod_fluxes.InterceptionEvaporation,
        whmod_fluxes.SoilEvapotranspiration,
        whmod_fluxes.LakeEvaporation,
    )
    RESULTSEQUENCES = (whmod_fluxes.TotalEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.totalevapotranspiration[k] = flu.lakeevaporation[k]
            else:
                flu.totalevapotranspiration[k] = flu.interceptionevaporation[k]
            if con.soiltype[k] != NONE:
                flu.totalevapotranspiration[k] += flu.soilevapotranspiration[k]


class Calc_CapillaryRise_V1(modeltools.Method):
    r"""Calculate the actual capillary rise if requested.

    Basic equation:
      .. math::
        C = P \cdot (1 - R) ^ 3
        \\ \\
        C = CapillaryRise \\
        P = PotentialCapillaryRise \\
        R = RelativeSoilMoisture

    Examples:

        >>> from hydpy.models.whmod import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, SEALED, WATER)
        >>> soiltype(SAND, SAND, SAND, SAND, SAND, NONE, NONE)
        >>> derived.potentialcapillaryrise(2.0)
        >>> factors.relativesoilmoisture = 0.0, 0.25, 0.5, 0.75, 1.0, nan, nan

        >>> withcapillaryrise(True)
        >>> model.calc_capillaryrise_v1()
        >>> fluxes.capillaryrise
        capillaryrise(2.0, 0.84375, 0.25, 0.03125, 0.0, 0.0, 0.0)

        >>> withcapillaryrise(False)
        >>> model.calc_capillaryrise_v1()
        >>> fluxes.capillaryrise
        capillaryrise(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.SoilType,
        whmod_control.WithCapillaryRise,
    )
    DERIVEDPARAMETERS = (whmod_derived.PotentialCapillaryRise,)
    REQUIREDSEQUENCES = (whmod_factors.RelativeSoilMoisture,)
    RESULTSEQUENCES = (whmod_fluxes.CapillaryRise,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.soiltype[k] == NONE:
                flu.capillaryrise[k] = 0.0
            elif con.withcapillaryrise:
                flu.capillaryrise[k] = (
                    der.potentialcapillaryrise[k]
                    * (1.0 - fac.relativesoilmoisture[k]) ** 3
                )
            else:
                flu.capillaryrise[k] = 0.0


class Calc_SoilMoisture_V1(modeltools.Method):
    r"""Update the actual soil storage's water content.

    Basic equation:
      .. math::
        M = I - E - P + C
        \\ \\
        M = SoilMoisture \\
        I = Ponding \\
        E = SoilEvapotranspiration \\
        P = Percolation \\
        C = CapillaryRise

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> soiltype(SAND, SAND, SAND, SAND, NONE)
        >>> derived.maxsoilwater(10.0)

        Cases where the given basic equation does not need further adjustment:

        >>> states.soilmoisture(5.0)
        >>> fluxes.ponding = 2.0
        >>> fluxes.soilevapotranspiration = 2.5, -2.5, 5.0, -5.0, nan
        >>> fluxes.percolation = 5.0
        >>> fluxes.capillaryrise = 3.0
        >>> model.calc_soilmoisture_v1()
        >>> states.soilmoisture
        soilmoisture(2.5, 7.5, 0.0, 10.0, 0.0)
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(2.5, -2.5, 5.0, -5.0, 0.0)
        >>> fluxes.percolation
        percolation(5.0, 5.0, 5.0, 5.0, 0.0)
        >>> fluxes.capillaryrise
        capillaryrise(3.0, 3.0, 3.0, 3.0, 0.0)

        Cases where the soil moisture would become negative (we prevent this by
        reducing percolation and, if positive, evapotranspiration by the same factor):

        >>> states.soilmoisture(2.0)
        >>> fluxes.ponding = 1.0
        >>> fluxes.soilevapotranspiration = 5.0, 0.0, -1.0, 7.0, nan
        >>> fluxes.percolation = 0.0, 5.0, 6.0, 1.0, nan
        >>> fluxes.capillaryrise = 1.0
        >>> model.calc_soilmoisture_v1()
        >>> states.soilmoisture
        soilmoisture(0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(4.0, 0.0, -1.0, 3.5, 0.0)
        >>> fluxes.percolation
        percolation(0.0, 4.0, 5.0, 0.5, 0.0)
        >>> fluxes.capillaryrise
        capillaryrise(1.0, 1.0, 1.0, 1.0, 0.0)

        Cases where the soil moisture would exceed the available storage volume (we
        prevent this by first reducing capillary rise and, if necessary, also
        increasing percolation):

        >>> states.soilmoisture(8.0)
        >>> fluxes.ponding = 1.0
        >>> fluxes.soilevapotranspiration = 1.0, -1.0, -3.0, -4.0, nan
        >>> fluxes.percolation = 1.0
        >>> fluxes.capillaryrise = 5.0, 2.0, 1.0, 0.0, nan
        >>> model.calc_soilmoisture_v1()
        >>> states.soilmoisture
        soilmoisture(10.0, 10.0, 10.0, 10.0, 0.0)
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(1.0, -1.0, -3.0, -4.0, 0.0)
        >>> fluxes.percolation
        percolation(1.0, 1.0, 2.0, 3.0, 0.0)
        >>> fluxes.capillaryrise
        capillaryrise(3.0, 1.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.SoilType)
    DERIVEDPARAMETERS = (whmod_derived.MaxSoilWater,)
    REQUIREDSEQUENCES = (
        whmod_fluxes.Ponding,
        whmod_fluxes.SoilEvapotranspiration,
        whmod_fluxes.Percolation,
        whmod_fluxes.CapillaryRise,
    )
    UPDATEDSEQUENCES = (whmod_states.SoilMoisture,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for k in range(con.nmbzones):
            if con.soiltype[k] == NONE:
                new.soilmoisture[k] = 0.0
                flu.percolation[k] = 0.0
                flu.capillaryrise[k] = 0.0
                flu.soilevapotranspiration[k] = 0.0
            else:
                increase: float = flu.ponding[k] + flu.capillaryrise[k]
                decrease: float = flu.percolation[k]
                if flu.soilevapotranspiration[k] < 0.0:
                    increase -= flu.soilevapotranspiration[k]
                else:
                    decrease += flu.soilevapotranspiration[k]
                new.soilmoisture[k] = old.soilmoisture[k] + increase - decrease
                if new.soilmoisture[k] < 0.0:
                    factor: float = (old.soilmoisture[k] + increase) / decrease
                    flu.percolation[k] *= factor
                    if flu.soilevapotranspiration[k] >= 0.0:
                        flu.soilevapotranspiration[k] *= factor
                    new.soilmoisture[k] = 0.0
                elif new.soilmoisture[k] > der.maxsoilwater[k]:
                    delta: float = new.soilmoisture[k] - der.maxsoilwater[k]
                    if flu.capillaryrise[k] >= delta:
                        flu.capillaryrise[k] -= delta
                        new.soilmoisture[k] = der.maxsoilwater[k]
                    else:
                        new.soilmoisture[k] -= flu.capillaryrise[k]
                        flu.capillaryrise[k] = 0.0
                        flu.percolation[k] += new.soilmoisture[k] - der.maxsoilwater[k]
                        new.soilmoisture[k] = der.maxsoilwater[k]


class Calc_RequiredIrrigation_V1(modeltools.Method):
    r"""Calculate the irrigation demand.

    Basic equation:
      .. math::
        I = \begin{cases}
        (T_1 - R) \cdot M &|\ R < T_0 \\
        0 &|\ R \geq T_0
        \end{cases}
        \\ \\
        I = RequiredIrrigation \\
        T_0 = IrrigationTrigger \\
        T_1 = IrrigationTarget \\
        R = RelativeSoilMoisture \\
        M = MaxSoilWater

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(8)
        >>> landtype(GRASS, GRASS, CORN, CORN, CORN, CORN, CORN, SEALED)
        >>> soiltype(SAND, SAND, SAND, SAND, SAND, SAND, SAND, NONE)
        >>> trigger = irrigationtrigger
        >>> target = irrigationtarget
        >>> trigger.grass, target.grass = 0.0, 0.0
        >>> trigger.corn_jun, target.corn_jun = 0.7, 0.7
        >>> trigger.corn_jul, target.corn_jul = 0.6, 0.8
        >>> derived.maxsoilwater(100.0)
        >>> factors.relativesoilmoisture = 0.0, 0.1, 0.5, 0.6, 0.7, 0.8, 0.9, nan

        >>> from hydpy import pub
        >>> pub.timegrids = "2001-06-29", "2001-07-03", "1d"
        >>> derived.moy.update()

        >>> model.idx_sim = 1
        >>> model.calc_requiredirrigation_v1()
        >>> fluxes.requiredirrigation
        requiredirrigation(0.0, 0.0, 20.0, 10.0, 0.0, 0.0, 0.0, 0.0)

        >>> model.idx_sim = 2
        >>> model.calc_requiredirrigation_v1()
        >>> fluxes.requiredirrigation
        requiredirrigation(0.0, 0.0, 30.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.SoilType,
        whmod_control.IrrigationTrigger,
        whmod_control.IrrigationTarget,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY, whmod_derived.MaxSoilWater)
    REQUIREDSEQUENCES = (whmod_factors.RelativeSoilMoisture,)
    RESULTSEQUENCES = (whmod_fluxes.RequiredIrrigation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        m = der.moy[model.idx_sim]
        for k in range(con.nmbzones):
            l = con.landtype[k] - 1
            sm: float = fac.relativesoilmoisture[k]
            if (con.soiltype[k] == NONE) or (sm >= con.irrigationtrigger[l, m]):
                flu.requiredirrigation[k] = 0.0
            else:
                flu.requiredirrigation[k] = der.maxsoilwater[k] * (
                    con.irrigationtarget[l, m] - sm
                )


class Calc_ExternalIrrigation_SoilMoisture_V1(modeltools.Method):
    r"""Irrigate from external sources, if required and requested.

    Basic equations:
      .. math::
        E = \begin{cases}
        R &|\ W \\
        0 &|\ \overline{W}
        \end{cases}
        \\
        S_{new} = S_{old} + E
        \\ \\
        E = ExternalIrrigation \\
        R = RequiredIrrigation \\
        W = WithExternalIrrigation \\
        S = SoilMoisture

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> landtype(CORN, SEALED)
        >>> soiltype(SAND, NONE)
        >>> fluxes.requiredirrigation(2.0, nan)
        >>> states.soilmoisture = 50.0, nan

        >>> withexternalirrigation(False)
        >>> model.calc_externalirrigation_soilmoisture_v1()
        >>> fluxes.externalirrigation
        externalirrigation(0.0, 0.0)
        >>> states.soilmoisture
        soilmoisture(50.0, 0.0)

        >>> withexternalirrigation(True)
        >>> model.calc_externalirrigation_soilmoisture_v1()
        >>> fluxes.externalirrigation
        externalirrigation(2.0, 0.0)
        >>> states.soilmoisture
        soilmoisture(52.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.SoilType,
        whmod_control.WithExternalIrrigation,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.RequiredIrrigation,)
    RESULTSEQUENCES = (whmod_fluxes.ExternalIrrigation,)
    UPDATEDSEQUENCES = (whmod_states.SoilMoisture,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nmbzones):
            if con.soiltype[k] == NONE:
                sta.soilmoisture[k] = 0.0
                flu.externalirrigation[k] = 0.0
            elif con.withexternalirrigation:
                flu.externalirrigation[k] = flu.requiredirrigation[k]
                sta.soilmoisture[k] += flu.externalirrigation[k]
            else:
                flu.externalirrigation[k] = 0.0


class Calc_PotentialRecharge_V1(modeltools.Method):
    r"""Calculate the potential recharge.

    Basic equation for water areas:
      .. math::
        PotentialRecharge = P - E
        \\ \\
        P = Precipitation \\
        E = LakeEvaporation

    Basic equation for non-sealed land areas:
      .. math::
        PotentialRecharge = P - C
        \\ \\
        P = Percolation \\
        C = CapillaryRise

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(GRASS, SEALED, WATER)
        >>> inputs.precipitation = 7.0
        >>> fluxes.lakeevaporation = 4.0
        >>> fluxes.percolation = 3.0
        >>> fluxes.capillaryrise = 1.0
        >>> model.calc_potentialrecharge_v1()
        >>> fluxes.potentialrecharge
        potentialrecharge(2.0, 0.0, 3.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (
        whmod_inputs.Precipitation,
        whmod_fluxes.LakeEvaporation,
        whmod_fluxes.Percolation,
        whmod_fluxes.CapillaryRise,
    )
    RESULTSEQUENCES = (whmod_fluxes.PotentialRecharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.potentialrecharge[k] = 0.0
            elif con.landtype[k] == WATER:
                flu.potentialrecharge[k] = inp.precipitation - flu.lakeevaporation[k]
            else:
                flu.potentialrecharge[k] = flu.percolation[k] - flu.capillaryrise[k]


class Calc_Baseflow_V1(modeltools.Method):
    r"""Calculate the base flow.

    Basic equation:
      .. math::
        B = (1 - I) \cdot max(P, \, 0)
        \\ \\
        B = Baseflow \\
        I = BaseflowIndex \\
        P = PotentialRecharge

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> baseflowindex(1.0, 0.5, 0.0, 0.0, nan)
        >>> fluxes.potentialrecharge = 2.0, 2.0, 2.0, -2.0, nan
        >>> model.calc_baseflow_v1()
        >>> fluxes.baseflow
        baseflow(0.0, 1.0, 2.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.BaseflowIndex,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.PotentialRecharge,)
    RESULTSEQUENCES = (whmod_fluxes.Baseflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.baseflow[k] = 0.0
            else:
                flu.baseflow[k] = (1.0 - con.baseflowindex[k]) * max(
                    flu.potentialrecharge[k], 0.0
                )


class Calc_ActualRecharge_V1(modeltools.Method):
    r"""Calculate the actual recharge.

    Basic equation:
      .. math::
        A = \sum_{i=1}^N P_i - B_i
        \\ \\
        N = NmbZones \\
        A = ActualRecharge \\
        P = PotentialRecharge \\
        B = Baseflow

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> area(14.0)
        >>> zonearea(1.0, 1.5, 2.5, 2.0, 7.0)
        >>> derived.zoneratio.update()
        >>> fluxes.potentialrecharge = 2.0, 10.0, -2.0, -0.5, nan
        >>> fluxes.baseflow = 0.0, 5.0, 0.0, 0.0, nan
        >>> model.calc_actualrecharge_v1()
        >>> fluxes.actualrecharge
        actualrecharge(0.25)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    DERIVEDPARAMETERS = (whmod_derived.ZoneRatio,)
    REQUIREDSEQUENCES = (whmod_fluxes.PotentialRecharge, whmod_fluxes.Baseflow)
    RESULTSEQUENCES = (whmod_fluxes.ActualRecharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualrecharge = 0.0
        for k in range(con.nmbzones):
            if con.landtype[k] != SEALED:
                flu.actualrecharge += der.zoneratio[k] * (
                    flu.potentialrecharge[k] - flu.baseflow[k]
                )


class Calc_DelayedRecharge_DeepWater_V1(modeltools.Method):
    r"""Calculate the delayed recharge and update the amount of water that is (still)
    percolating through the vadose zone.

    Basic equations:
      .. math::
        W_{new} = (A + W_{old}) \cdot exp(-1 / R)
        \\
        D = A + W_{old} - W_{new}
        \\ \\
        D = DelayedRecharge \\
        A = ActualRecharge \\
        W = DeepWater \\
        R = RechargeDelay

    (The given equations are the analytical solution of the linear storage equation
    under the assumption of a stepwise constant inflow.)

    Examples:

        >>> from hydpy.models.whmod import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> fluxes.actualrecharge = 1.0

        >>> rechargedelay(1.0)
        >>> states.deepwater(2.0)
        >>> model.calc_delayedrecharge_deepwater_v1()
        >>> fluxes.delayedrecharge
        delayedrecharge(1.896362)
        >>> states.deepwater
        deepwater(1.103638)

        >>> rechargedelay(0.0)
        >>> states.deepwater(2.0)
        >>> model.calc_delayedrecharge_deepwater_v1()
        >>> fluxes.delayedrecharge
        delayedrecharge(3.0)
        >>> states.deepwater
        deepwater(0.0)
    """

    CONTROLPARAMETERS = (whmod_control.RechargeDelay,)
    REQUIREDSEQUENCES = (whmod_fluxes.ActualRecharge,)
    UPDATEDSEQUENCES = (whmod_states.DeepWater,)
    RESULTSEQUENCES = (whmod_fluxes.DelayedRecharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        new = model.sequences.states.fastaccess_new
        old = model.sequences.states.fastaccess_old
        if con.rechargedelay > 0.0:
            new.deepwater = (flu.actualrecharge + old.deepwater) * modelutils.exp(
                -1.0 / con.rechargedelay
            )
            flu.delayedrecharge = flu.actualrecharge + old.deepwater - new.deepwater
        else:
            flu.delayedrecharge = old.deepwater + flu.actualrecharge
            new.deepwater = 0.0


class Get_Temperature_V1(modeltools.Method):
    """Get the basin's current air temperature.

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> inputs.temperature = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_temperature_v1(0))
        2.0
        >>> round_(model.get_temperature_v1(1))
        2.0
    """

    REQUIREDSEQUENCES = (whmod_inputs.Temperature,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.temperature


class Get_MeanTemperature_V1(modeltools.Method):
    """Get the basin's current air temperature.

    Example:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> inputs.temperature = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_meantemperature_v1())
        2.0
    """

    REQUIREDSEQUENCES = (whmod_inputs.Temperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.temperature


class Get_Precipitation_V1(modeltools.Method):
    """Get the basin's current precipitation.

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> inputs.precipitation = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_precipitation_v1(0))
        2.0
        >>> round_(model.get_precipitation_v1(1))
        2.0
    """

    REQUIREDSEQUENCES = (whmod_inputs.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.precipitation


class Get_InterceptedWater_V1(modeltools.Method):
    """Get the selected zone's current amount of intercepted water.

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> states.interceptedwater = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_interceptedwater_v1(0))
        2.0
        >>> round_(model.get_interceptedwater_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (whmod_states.InterceptedWater,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        return sta.interceptedwater[k]


class Get_SoilWater_V1(modeltools.Method):
    """Get the selected zone's current soil water content.

    Examples:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> states.soilmoisture = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_soilwater_v1(0))
        2.0
        >>> round_(model.get_soilwater_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (whmod_states.SoilMoisture,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        return sta.soilmoisture[k]


class Get_SnowCover_V1(modeltools.Method):
    """Get the selected zones's current snow cover degree.

    Examples:

        Each response unit with a non-zero amount of snow counts as wholly covered:

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(2)
        >>> states.snowpack = 0.0, 2.0
        >>> model.get_snowcover_v1(0)
        0.0
        >>> model.get_snowcover_v1(1)
        1.0
    """

    REQUIREDSEQUENCES = (whmod_states.Snowpack,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        if sta.snowpack[k] > 0.0:
            return 1.0
        return 0.0


class Model(modeltools.AdHocModel):
    """|whmod.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="WHMod")
    __HYDPY_ROOTMODEL__ = None

    aetmodel = modeltools.SubmodelProperty(aetinterfaces.AETModel_V1)
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        Calc_InterceptionEvaporation_InterceptedWater_AETModel_V1,
        Calc_LakeEvaporation_AETModel_V1,
        Calc_SoilEvapotranspiration_AETModel_V1,
    )
    INTERFACE_METHODS = (
        Get_Temperature_V1,
        Get_MeanTemperature_V1,
        Get_Precipitation_V1,
        Get_InterceptedWater_V1,
        Get_SoilWater_V1,
        Get_SnowCover_V1,
    )
    RUN_METHODS = (
        Calc_Throughfall_InterceptedWater_V1,
        Calc_InterceptionEvaporation_InterceptedWater_V1,
        Calc_LakeEvaporation_V1,
        Calc_PotentialSnowmelt_V1,
        Calc_Snowmelt_Snowpack_V1,
        Calc_Ponding_V1,
        Calc_SurfaceRunoff_V1,
        Calc_RelativeSoilMoisture_V1,
        Calc_Percolation_V1,
        Calc_SoilEvapotranspiration_V1,
        Calc_TotalEvapotranspiration_V1,
        Calc_CapillaryRise_V1,
        Calc_SoilMoisture_V1,
        Calc_RelativeSoilMoisture_V1,
        Calc_RequiredIrrigation_V1,
        Calc_ExternalIrrigation_SoilMoisture_V1,
        Calc_RelativeSoilMoisture_V1,
        Calc_PotentialRecharge_V1,
        Calc_Baseflow_V1,
        Calc_ActualRecharge_V1,
        Calc_DelayedRecharge_DeepWater_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMODELS = ()


class Main_AETModel_V1(modeltools.AdHocModel):
    """Base class for |whmod.DOCNAME.long| models that use submodels that comply with
    the |AETModel_V1| interface."""

    aetmodel: modeltools.SubmodelProperty
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "aetmodel",
        aetinterfaces.AETModel_V1,
        aetinterfaces.AETModel_V1.prepare_nmbzones,
        aetinterfaces.AETModel_V1.prepare_subareas,
        aetinterfaces.AETModel_V1.prepare_zonetypes,
        aetinterfaces.AETModel_V1.prepare_water,
        aetinterfaces.AETModel_V1.prepare_interception,
        aetinterfaces.AETModel_V1.prepare_soil,
        aetinterfaces.AETModel_V1.prepare_plant,
        aetinterfaces.AETModel_V1.prepare_tree,
        aetinterfaces.AETModel_V1.prepare_conifer,
        aetinterfaces.AETModel_V1.prepare_maxsoilwater,
        landtype_constants=whmod_constants.LANDTYPE_CONSTANTS,
        landtype_refindices=whmod_control.LandType,
        soiltype_constants=whmod_constants.SOILTYPE_CONSTANTS,
        soiltype_refindices=whmod_control.SoilType,
        refweights=whmod_control.ZoneArea,
    )
    def add_aetmodel_v1(
        self,
        aetmodel: aetinterfaces.AETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given submodel that follows the |AETModel_V1| interface and
        is responsible for calculating the different kinds of actual
        evapotranspiration.

        >>> from hydpy.models.whmod_rural import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> area(10.0)
        >>> landtype(GRASS, DECIDUOUS, CONIFER, WATER, SEALED)
        >>> zonearea(4.0, 1.0, 1.0, 1.0, 3.0)
        >>> availablefieldcapacity(0.2)
        >>> rootingdepth(1.0)
        >>> groundwaterdepth(1.0)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     nmbhru
        ...     area
        ...     water
        ...     interception
        ...     soil
        ...     dissefactor(grass=1.0, deciduous=2.0, default=3.0)
        ...     for method, arguments in model.preparemethod2arguments.items():
        ...         print(method, arguments[0][0], sep=": ")
        nmbhru(5)
        area(10.0)
        water(conifer=False, deciduous=False, grass=False, sealed=False,
              water=True)
        interception(conifer=True, deciduous=True, grass=True, sealed=True,
                     water=False)
        soil(conifer=True, deciduous=True, grass=True, sealed=False,
             water=False)
        prepare_nmbzones: 5
        prepare_zonetypes: [1 2 4 9 8]
        prepare_subareas: [4. 1. 1. 1. 3.]
        prepare_water: [False False False  True False]
        prepare_interception: [ True  True  True False  True]
        prepare_soil: [ True  True  True False False]
        prepare_plant: [ True  True  True False False]
        prepare_conifer: [False False  True False False]
        prepare_tree: [False  True  True False False]
        prepare_maxsoilwater: [200. 200. 200. 200. 200.]

        >>> df = model.aetmodel.parameters.control.dissefactor
        >>> df
        dissefactor(conifer=3.0, deciduous=2.0, grass=1.0)
        >>> landtype(DECIDUOUS, GRASS, CONIFER, WATER, SEALED)
        >>> df
        dissefactor(conifer=3.0, deciduous=1.0, grass=2.0)
        >>> from hydpy import round_
        >>> round_(df.average_values())
        1.5
        """
        control = self.parameters.control
        derived = self.parameters.derived

        hydrotopes = control.nmbzones.value
        landtype = control.landtype.values

        aetmodel.prepare_nmbzones(hydrotopes)
        aetmodel.prepare_zonetypes(landtype)
        aetmodel.prepare_subareas(control.zonearea.value)
        sel = numpy.full(hydrotopes, False, dtype=config.NP_BOOL)
        sel[landtype == WATER] = True
        aetmodel.prepare_water(sel)
        sel = ~sel
        aetmodel.prepare_interception(sel)
        sel[landtype == SEALED] = False
        aetmodel.prepare_soil(sel)
        aetmodel.prepare_plant(sel)
        sel[:] = False
        sel[landtype == CONIFER] = True
        aetmodel.prepare_conifer(sel)
        sel[landtype == DECIDUOUS] = True
        aetmodel.prepare_tree(sel)

        derived.soildepth.update()
        derived.maxsoilwater.update()
        aetmodel.prepare_maxsoilwater(derived.maxsoilwater.values)


class Sub_TempModel_V1(modeltools.AdHocModel, tempinterfaces.TempModel_V1):
    """Base class for |whmod.DOCNAME.long| models that comply with the |TempModel_V1|
    submodel interface."""


class Sub_PrecipModel_V1(modeltools.AdHocModel, precipinterfaces.PrecipModel_V1):
    """Base class for |whmod.DOCNAME.long| models that comply with the |PrecipModel_V1|
    submodel interface."""


class Sub_IntercModel_V1(modeltools.AdHocModel, stateinterfaces.IntercModel_V1):
    """Base class for |whmod.DOCNAME.long| models that comply with the |IntercModel_V1|
    submodel interface."""


class Sub_SoilWaterModel_V1(modeltools.AdHocModel, stateinterfaces.SoilWaterModel_V1):
    """Base class for |whmod.DOCNAME.long| models that comply with the
    |SoilWaterModel_V1| submodel interface."""


class Sub_SnowCoverModel_V1(modeltools.AdHocModel, stateinterfaces.SnowCoverModel_V1):
    """Base class for |whmod.DOCNAME.long| models that comply with the
    |SnowCoverModel_V1| submodel interface."""
