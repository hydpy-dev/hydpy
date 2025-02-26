# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from standard library
import abc
from typing import *
from typing import TextIO

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.interfaces import aetinterfaces
from hydpy.cythons import modelutils

# ...from whmod
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_control
from hydpy.models.whmod import whmod_derived
from hydpy.models.whmod import whmod_inputs
from hydpy.models.whmod import whmod_factors
from hydpy.models.whmod import whmod_fluxes
from hydpy.models.whmod import whmod_states


class Calc_Throughfall_InterceptedWater_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(4)
    >>> landtype(DECIDIOUS)
    >>> interceptioncapacity.decidious_jun = 2.2
    >>> interceptioncapacity.decidious_jul = 2.4

    >>> from hydpy import pub
    >>> pub.timegrids = "2001-06-29", "2001-07-03", "1d"
    >>> derived.moy.update()

    >>> inputs.precipitation = 1.0
    >>> states.interceptedwater = 0.0, 1.0, 2.0, 2.2
    >>> model.idx_sim = 1
    >>> model.calc_throughfall_interceptedwater_v1()
    >>> states.interceptedwater
    interceptedwater(1.0, 2.0, 2.2, 2.2)
    >>> fluxes.throughfall
    throughfall(0.0, 0.0, 0.8, 1.0)

    >>> states.interceptedwater = 0.0, 1.0, 2.0, 2.4
    >>> model.idx_sim = 2
    >>> model.calc_throughfall_interceptedwater_v1()
    >>> states.interceptedwater
    interceptedwater(1.0, 2.0, 2.4, 2.4)
    >>> fluxes.throughfall
    throughfall(0.0, 0.0, 0.6, 1.0)
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
            if con.landtype[k] in (SEALED, WATER):
                sta.interceptedwater[k] = 0.0
                flu.throughfall[k] = inp.precipitation  # ToDo
            else:
                ic: float = con.interceptioncapacity[con.landtype[k] - 1, month]
                flu.throughfall[k] = max(
                    inp.precipitation + sta.interceptedwater[k] - ic, 0.0
                )
                sta.interceptedwater[k] += inp.precipitation - flu.throughfall[k]


class Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_AETModel_V1(
    modeltools.Method
):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water.

    Basic equation:
      :math:`\frac{dIc_i}{dt} = -EI_i`  ToDo

    Examples:

        We build an example based on |evap_aet_minhas| for calculating interception
        evaporation, which uses |evap_ret_io| for querying potential
        evapotranspiration:

        >>> from hydpy.models.whmod_pet import *
        >>> parameterstep("1h")
        >>> area(1.0)
        >>> nmbzones(5)
        >>> landtype(GRAS, DECIDIOUS, CORN, SEALED, WATER)
        >>> zonearea(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> interceptioncapacity.jun = 3.0
        >>> availablefieldcapacity(50.0)
        >>> derived.moy.shape = 1
        >>> derived.moy(5)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     with model.add_petmodel_v1("evap_ret_io"):
        ...         evapotranspirationfactor(0.6, 0.8, 1.0, 1.2, 1.4)
        ...         inputs.referenceevapotranspiration = 1.0


        |Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_AETModel_V1|
        uses the flux returned by the submodel to adjust |InterceptedWater|:

        >>> states.interceptedwater = 2.0
        >>> model.calc_interceptionevaporation_interceptedwater_lakeevaporation_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(0.6, 0.8, 1.0, 0.0, 0.0)
        >>> states.interceptedwater
        interceptedwater(1.4, 1.2, 1.0, 0.0, 0.0)
        >>> fluxes.lakeevaporation
        lakeevaporation(0.0, 0.0, 0.0, 0.0, 1.4)

        |Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_AETModel_V1|
        eventually reduces |InterceptionEvaporation| so that |InterceptedWater| does
        not become negative:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = 5.0
        >>> states.interceptedwater = 2.0
        >>> model.calc_interceptionevaporation_interceptedwater_lakeevaporation_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(2.0, 2.0, 2.0, 0.0, 0.0)
        >>> states.interceptedwater
        interceptedwater(0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.lakeevaporation
        lakeevaporation(0.0, 0.0, 0.0, 0.0, 7.0)

        In contrast,
        |Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_AETModel_V1|
        does not reduce negative |InterceptionEvaporation| values (condensation) that
        cause an overshoot of the interception storage capacity:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = -3.0
        >>> states.interceptedwater = 2.0
        >>> model.calc_interceptionevaporation_interceptedwater_lakeevaporation_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(-1.8, -2.4, -3.0, 0.0, 0.0)
        >>> states.interceptedwater
        interceptedwater(3.8, 4.4, 5.0, 0.0, 0.0)
        >>> fluxes.lakeevaporation
        lakeevaporation(0.0, 0.0, 0.0, 0.0, -4.2)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    UPDATEDSEQUENCES = (whmod_states.InterceptedWater,)
    RESULTSEQUENCES = (
        whmod_fluxes.InterceptionEvaporation,
        whmod_fluxes.LakeEvaporation,
    )

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_interceptionevaporation()
        submodel.determine_waterevaporation()
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.interceptionevaporation[k] = 0.0
                sta.interceptedwater[k] = 0.0
                flu.lakeevaporation[k] = 0.0
            elif con.landtype[k] == WATER:
                flu.interceptionevaporation[k] = 0.0
                sta.interceptedwater[k] = 0.0
                flu.lakeevaporation[k] = submodel.get_waterevaporation(k)
            else:
                flu.interceptionevaporation[k] = min(
                    submodel.get_interceptionevaporation(k), sta.interceptedwater[k]
                )
                sta.interceptedwater[k] -= flu.interceptionevaporation[k]
                flu.lakeevaporation[k] = 0.0


class Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_V1(
    modeltools.Method
):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (
        Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_AETModel_V1,
    )
    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    UPDATEDSEQUENCES = (whmod_states.InterceptedWater,)
    RESULTSEQUENCES = (
        whmod_fluxes.InterceptionEvaporation,
        whmod_fluxes.LakeEvaporation,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_interceptionevaporation_interceptedwater_lakeevaporation_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )


class Calc_SurfaceRunoff_V1(modeltools.Method):
    """Berechnung SurfaceRunoff.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(SEALED, WATER, GRAS)
    >>> fluxes.throughfall = 3.0
    >>> model.calc_surfacerunoff_v1()
    >>> fluxes.surfacerunoff
    surfacerunoff(3.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (whmod_fluxes.Throughfall,)
    RESULTSEQUENCES = (whmod_fluxes.SurfaceRunoff,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.surfacerunoff[k] = flu.throughfall[k]
            else:
                flu.surfacerunoff[k] = 0.0


class Calc_Ponding_V1(modeltools.Method):
    """Berechnung Bestandsniederschlag.

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> simulationstep("1d")
    >>> nmbzones(2)
    >>> landtype(GRAS, GRAS)
    >>> degreedayfactor(4.5)
    >>> fluxes.throughfall = 3.0

    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_ponding_v1,
    ...     last_example=6,
    ...     parseqs=(inputs.temperature,
    ...              states.snowpack,
    ...              fluxes.ponding))
    >>> test.nexts.temperature = range(-1, 6)
    >>> test.inits.snowpack = (0.0, 10.0)
    >>> test()
    | ex. | temperature |      snowpack |      ponding |
    ----------------------------------------------------
    |   1 |        -1.0 | 3.0      13.0 | 0.0      0.0 |
    |   2 |         0.0 | 3.0      13.0 | 0.0      0.0 |
    |   3 |         1.0 | 0.0       5.5 | 3.0      7.5 |
    |   4 |         2.0 | 0.0       1.0 | 3.0     12.0 |
    |   5 |         3.0 | 0.0       0.0 | 3.0     13.0 |
    |   6 |         4.0 | 0.0       0.0 | 3.0     13.0 |

    >>> landtype(SEALED, WATER)
    >>> states.snowpack = 5.0
    >>> fluxes.throughfall = 2.0
    >>> model.calc_ponding_v1()
    >>> states.snowpack
    snowpack(0.0, 0.0)
    >>> fluxes.ponding
    ponding(0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.DegreeDayFactor,
    )
    REQUIREDSEQUENCES = (whmod_inputs.Temperature, whmod_fluxes.Throughfall)
    UPDATEDSEQUENCES = (whmod_states.Snowpack,)
    RESULTSEQUENCES = (whmod_fluxes.Ponding,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                sta.snowpack[k] = 0.0
                flu.ponding[k] = 0.0
            elif inp.temperature > 0.0:
                maxschneeschmelze: float = con.degreedayfactor[k] * inp.temperature
                schneeschmelze: float = min(sta.snowpack[k], maxschneeschmelze)
                sta.snowpack[k] -= schneeschmelze
                flu.ponding[k] = flu.throughfall[k] + schneeschmelze
            else:
                sta.snowpack[k] += flu.throughfall[k]
                flu.ponding[k] = 0.0


class Calc_RelativeSoilMoisture_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRAS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT,
    ...         SUGARBEETS, SEALED, WATER)
    >>> derived.maxsoilwater(200.0)
    >>> states.soilmoisture(100.0)
    >>> model.calc_relativesoilmoisture_v1()
    >>> factors.relativesoilmoisture
    relativesoilmoisture(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    DERIVEDPARAMETERS = (whmod_derived.MaxSoilWater,)
    REQUIREDSEQUENCES = (whmod_states.SoilMoisture,)
    RESULTSEQUENCES = (whmod_factors.RelativeSoilMoisture,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if (con.landtype[k] in (WATER, SEALED)) or (der.maxsoilwater[k] <= 0.0):
                fac.relativesoilmoisture[k] = 0.0
            else:
                fac.relativesoilmoisture[k] = sta.soilmoisture[k] / der.maxsoilwater[k]


class Calc_Percolation_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRAS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT,
    ...         SUGARBEETS, SEALED, WATER)
    >>> derived.beta(2.0)
    >>> fluxes.ponding(10.0)
    >>> factors.relativesoilmoisture(0.5)
    >>> model.calc_percolation_v1()
    >>> fluxes.percolation
    percolation(2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
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
            if con.landtype[k] in (SEALED, WATER):
                flu.percolation[k] = 0.0
            else:
                flu.percolation[k] = (
                    flu.ponding[k] * fac.relativesoilmoisture[k] ** der.beta[k]
                )


class Calc_MaxVerdunstung_V1(modeltools.Method):
    """Berechnung maximale/potenzielle Verdunstung.

    Modifikation einer extern vorgegebenen potenziellen Verdunstung
    (FAO Grasreferenzverdunstung).

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> landtype(DECIDIOUS, CONIFER, GRAS, WATER, SEALED)
    >>> fln(gras=[0.804, 0.927, 1.014, 1.041, 1.059, 1.056,
    ...           1.038, 0.999, 0.977, 0.965, 0.989, 0.927],
    ...     decidious=[1.003, 1.003, 1.053, 1.179, 1.114, 1.227,
    ...               1.241, 1.241, 1.241, 1.139, 1.082, 1.003],
    ...     corn=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...           1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     conifer=[1.335, 1.335, 1.335, 1.335, 1.307, 1.321,
    ...                1.335, 1.335, 1.335, 1.335, 1.335, 1.335],
    ...     springwheat=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...                   1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     winterwheat=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...                   1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     sugarbeets=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...                   1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     sealed=0.0,
    ...     water=[1.165, 1.217, 1.256, 1.283, 1.283, 1.296,
    ...             1.283, 1.283, 1.270, 1.230, 1.165, 1.139])

    >>> from hydpy import pub
    >>> pub.timegrids = "2001-06-29", "2001-07-03", "1d"
    >>> derived.moy.update()

    >>> inputs.et0 = 5.0

    >>> model.idx_sim = pub.timegrids.init["2001-06-30"]
    >>> model.calc_maxverdunstung_v1()
    >>> fluxes.maxverdunstung
    maxverdunstung(6.135, 6.605, 5.28, 6.48, 0.0)

    >>> model.idx_sim = pub.timegrids.init["2001-07-01"]
    >>> model.calc_maxverdunstung_v1()
    >>> fluxes.maxverdunstung
    maxverdunstung(6.205, 6.675, 5.19, 6.415, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.FLN,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY,)
    REQUIREDSEQUENCES = (whmod_inputs.ET0,)
    RESULTSEQUENCES = (whmod_fluxes.MaxVerdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        month = der.moy[model.idx_sim]
        for k in range(con.nmbzones):
            flu.maxverdunstung[k] = con.fln[con.landtype[k] - 1, month] * inp.et0


class Calc_SoilEvapotranspiration_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, SEALED, WATER)
    >>> minhasr(3.0)
    >>> fluxes.maxverdunstung = 2.0
    >>> factors.relativesoilmoisture = 0.0, 0.25, 0.5, 0.75, 1.0, 0.5, 0.5
    >>> model.calc_soilevapotranspiration_v1()
    >>> fluxes.soilevapotranspiration
    soilevapotranspiration(0.0, 0.768701, 1.382877, 1.77884, 2.0, 0.0, 0.0)

    >>> minhasr(6.0)
    >>> model.calc_soilevapotranspiration_v1()
    >>> fluxes.soilevapotranspiration
    soilevapotranspiration(0.0, 1.275468, 1.818886, 1.96569, 2.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.MinhasR,
    )
    REQUIREDSEQUENCES = (
        whmod_factors.RelativeSoilMoisture,
        whmod_fluxes.MaxVerdunstung,
    )
    RESULTSEQUENCES = (whmod_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                flu.soilevapotranspiration[k] = 0.0
            else:
                temp: float = modelutils.exp(
                    -con.minhasr[k] * fac.relativesoilmoisture[k]
                )
                flu.soilevapotranspiration[k] = (
                    flu.maxverdunstung[k]
                    * (1.0 - temp)
                    / (1.0 - 2.0 * modelutils.exp(-con.minhasr[k]) + temp)
                )


class Corr_SoilEvapotranspiration_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, WATER, SEALED)
    >>> fluxes.maxverdunstung = 2.0
    >>> fluxes.interceptionevaporation = 0.0, 0.5, 1.0, 1.5, 2.0, 2.0, 2.0
    >>> fluxes.soilevapotranspiration = 1.0
    >>> model.corr_soilevapotranspiration_v1()
    >>> fluxes.soilevapotranspiration
    soilevapotranspiration(1.0, 0.75, 0.5, 0.25, 0.0, 0.0, 0.0)
    >>> from hydpy import print_vector
    >>> print_vector(fluxes.interceptionevaporation[:5] + fluxes.soilevapotranspiration[:5])
    1.0, 1.25, 1.5, 1.75, 2.0

    >>> fluxes.interceptionevaporation = 1.0
    >>> fluxes.soilevapotranspiration = 0.0, 0.5, 1.0, 1.5, 2.0, 2.0, 2.0
    >>> model.corr_soilevapotranspiration_v1()
    >>> fluxes.soilevapotranspiration
    soilevapotranspiration(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
    >>> print_vector(fluxes.interceptionevaporation[:5] + fluxes.soilevapotranspiration[:5])
    1.0, 1.25, 1.5, 1.75, 2.0
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (
        whmod_fluxes.MaxVerdunstung,
        whmod_fluxes.InterceptionEvaporation,
    )
    UPDATEDSEQUENCES = (whmod_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                flu.soilevapotranspiration[k] = 0.0
            elif flu.maxverdunstung[k] <= flu.interceptionevaporation[k]:
                flu.soilevapotranspiration[k] = 0.0
            else:
                flu.soilevapotranspiration[k] *= (
                    flu.maxverdunstung[k] - flu.interceptionevaporation[k]
                ) / flu.maxverdunstung[k]


class Calc_LakeEvaporation_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(GRAS, SEALED, WATER)
    >>> fluxes.maxverdunstung = 2.0
    >>> model.calc_lakeevaporation_v1()
    >>> fluxes.lakeevaporation
    lakeevaporation(0.0, 0.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (whmod_fluxes.MaxVerdunstung,)
    RESULTSEQUENCES = (whmod_fluxes.LakeEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.lakeevaporation[k] = flu.maxverdunstung[k]
            else:
                flu.lakeevaporation[k] = 0.0


class Calc_TotalEvapotranspiration_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(2)
    >>> fluxes.interceptionevaporation = 1.0, 0.0
    >>> fluxes.soilevapotranspiration = 2.0, 0.0
    >>> fluxes.lakeevaporation = 0.0, 4.0
    >>> model.calc_totalevapotranspiration_v1()
    >>> fluxes.totalevapotranspiration
    totalevapotranspiration(3.0, 4.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones,)
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
            flu.totalevapotranspiration[k] = (
                flu.interceptionevaporation[k]
                + flu.soilevapotranspiration[k]
                + flu.lakeevaporation[k]
            )


class Calc_PotentialCapillaryRise_V1(modeltools.Method):
    # pylint: disable=line-too-long
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(6)
    >>> landtype(GRAS)
    >>> capillaryrise(True)
    >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT)
    >>> groundwaterdepth(0.0)   # ToDo: shouldn't be necessary
    >>> capillarythreshold(sand=0.8, sand_cohesive=1.4, loam=1.4,
    ...                  clay=1.35, silt=1.75, peat=0.85)
    >>> capillarylimit(sand=0.4, sand_cohesive=0.85, loam=0.45,
    ...                clay=0.25, silt=0.75, peat=0.55)
    >>> derived.soildepth(0.0)

    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_potentialcapillaryrise_v1,
    ...     last_example=31,
    ...     parseqs=(control.groundwaterdepth,
    ...              fluxes.potentialcapillaryrise))
    >>> import numpy
    >>> test.nexts.groundwaterdepth = numpy.arange(0.0, 3.1, 0.1)
    >>> test()
    | ex. |                          groundwaterdepth |                                           potentialcapillaryrise |
    ----------------------------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   2 | 0.1  0.1  0.1  0.1  0.1               0.1 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   3 | 0.2  0.2  0.2  0.2  0.2               0.2 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   4 | 0.3  0.3  0.3  0.3  0.3               0.3 |  5.0       5.0       5.0  4.772727   5.0                     5.0 |
    |   5 | 0.4  0.4  0.4  0.4  0.4               0.4 |  5.0       5.0       5.0  4.318182   5.0                     5.0 |
    |   6 | 0.5  0.5  0.5  0.5  0.5               0.5 | 3.75       5.0  4.736842  3.863636   5.0                     5.0 |
    |   7 | 0.6  0.6  0.6  0.6  0.6               0.6 |  2.5       5.0  4.210526  3.409091   5.0                4.166667 |
    |   8 | 0.7  0.7  0.7  0.7  0.7               0.7 | 1.25       5.0  3.684211  2.954545   5.0                     2.5 |
    |   9 | 0.8  0.8  0.8  0.8  0.8               0.8 |  0.0       5.0  3.157895       2.5  4.75                0.833333 |
    |  10 | 0.9  0.9  0.9  0.9  0.9               0.9 |  0.0  4.545455  2.631579  2.045455  4.25                     0.0 |
    |  11 | 1.0  1.0  1.0  1.0  1.0               1.0 |  0.0  3.636364  2.105263  1.590909  3.75                     0.0 |
    |  12 | 1.1  1.1  1.1  1.1  1.1               1.1 |  0.0  2.727273  1.578947  1.136364  3.25                     0.0 |
    |  13 | 1.2  1.2  1.2  1.2  1.2               1.2 |  0.0  1.818182  1.052632  0.681818  2.75                     0.0 |
    |  14 | 1.3  1.3  1.3  1.3  1.3               1.3 |  0.0  0.909091  0.526316  0.227273  2.25                     0.0 |
    |  15 | 1.4  1.4  1.4  1.4  1.4               1.4 |  0.0       0.0       0.0       0.0  1.75                     0.0 |
    |  16 | 1.5  1.5  1.5  1.5  1.5               1.5 |  0.0       0.0       0.0       0.0  1.25                     0.0 |
    |  17 | 1.6  1.6  1.6  1.6  1.6               1.6 |  0.0       0.0       0.0       0.0  0.75                     0.0 |
    |  18 | 1.7  1.7  1.7  1.7  1.7               1.7 |  0.0       0.0       0.0       0.0  0.25                     0.0 |
    |  19 | 1.8  1.8  1.8  1.8  1.8               1.8 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  20 | 1.9  1.9  1.9  1.9  1.9               1.9 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  21 | 2.0  2.0  2.0  2.0  2.0               2.0 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  22 | 2.1  2.1  2.1  2.1  2.1               2.1 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  23 | 2.2  2.2  2.2  2.2  2.2               2.2 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  24 | 2.3  2.3  2.3  2.3  2.3               2.3 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  25 | 2.4  2.4  2.4  2.4  2.4               2.4 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  26 | 2.5  2.5  2.5  2.5  2.5               2.5 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  27 | 2.6  2.6  2.6  2.6  2.6               2.6 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  28 | 2.7  2.7  2.7  2.7  2.7               2.7 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  29 | 2.8  2.8  2.8  2.8  2.8               2.8 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  30 | 2.9  2.9  2.9  2.9  2.9               2.9 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  31 | 3.0  3.0  3.0  3.0  3.0               3.0 |  0.0       0.0       0.0       0.0   0.0                     0.0 |

    >>> derived.soildepth(1.0)
    >>> test()
    | ex. |                          groundwaterdepth |                                           potentialcapillaryrise |
    ----------------------------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   2 | 0.1  0.1  0.1  0.1  0.1               0.1 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   3 | 0.2  0.2  0.2  0.2  0.2               0.2 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   4 | 0.3  0.3  0.3  0.3  0.3               0.3 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   5 | 0.4  0.4  0.4  0.4  0.4               0.4 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   6 | 0.5  0.5  0.5  0.5  0.5               0.5 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   7 | 0.6  0.6  0.6  0.6  0.6               0.6 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   8 | 0.7  0.7  0.7  0.7  0.7               0.7 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |   9 | 0.8  0.8  0.8  0.8  0.8               0.8 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |  10 | 0.9  0.9  0.9  0.9  0.9               0.9 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |  11 | 1.0  1.0  1.0  1.0  1.0               1.0 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |  12 | 1.1  1.1  1.1  1.1  1.1               1.1 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |  13 | 1.2  1.2  1.2  1.2  1.2               1.2 |  5.0       5.0       5.0       5.0   5.0                     5.0 |
    |  14 | 1.3  1.3  1.3  1.3  1.3               1.3 |  5.0       5.0       5.0  4.772727   5.0                     5.0 |
    |  15 | 1.4  1.4  1.4  1.4  1.4               1.4 |  5.0       5.0       5.0  4.318182   5.0                     5.0 |
    |  16 | 1.5  1.5  1.5  1.5  1.5               1.5 | 3.75       5.0  4.736842  3.863636   5.0                     5.0 |
    |  17 | 1.6  1.6  1.6  1.6  1.6               1.6 |  2.5       5.0  4.210526  3.409091   5.0                4.166667 |
    |  18 | 1.7  1.7  1.7  1.7  1.7               1.7 | 1.25       5.0  3.684211  2.954545   5.0                     2.5 |
    |  19 | 1.8  1.8  1.8  1.8  1.8               1.8 |  0.0       5.0  3.157895       2.5  4.75                0.833333 |
    |  20 | 1.9  1.9  1.9  1.9  1.9               1.9 |  0.0  4.545455  2.631579  2.045455  4.25                     0.0 |
    |  21 | 2.0  2.0  2.0  2.0  2.0               2.0 |  0.0  3.636364  2.105263  1.590909  3.75                     0.0 |
    |  22 | 2.1  2.1  2.1  2.1  2.1               2.1 |  0.0  2.727273  1.578947  1.136364  3.25                     0.0 |
    |  23 | 2.2  2.2  2.2  2.2  2.2               2.2 |  0.0  1.818182  1.052632  0.681818  2.75                     0.0 |
    |  24 | 2.3  2.3  2.3  2.3  2.3               2.3 |  0.0  0.909091  0.526316  0.227273  2.25                     0.0 |
    |  25 | 2.4  2.4  2.4  2.4  2.4               2.4 |  0.0       0.0       0.0       0.0  1.75                     0.0 |
    |  26 | 2.5  2.5  2.5  2.5  2.5               2.5 |  0.0       0.0       0.0       0.0  1.25                     0.0 |
    |  27 | 2.6  2.6  2.6  2.6  2.6               2.6 |  0.0       0.0       0.0       0.0  0.75                     0.0 |
    |  28 | 2.7  2.7  2.7  2.7  2.7               2.7 |  0.0       0.0       0.0       0.0  0.25                     0.0 |
    |  29 | 2.8  2.8  2.8  2.8  2.8               2.8 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  30 | 2.9  2.9  2.9  2.9  2.9               2.9 |  0.0       0.0       0.0       0.0   0.0                     0.0 |
    |  31 | 3.0  3.0  3.0  3.0  3.0               3.0 |  0.0       0.0       0.0       0.0   0.0                     0.0 |

    >>> landtype(SEALED)
    >>> test(last_example=1)
    | ex. |                          groundwaterdepth |                          potentialcapillaryrise |
    -----------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 | 0.0  0.0  0.0  0.0  0.0                     0.0 |

    >>> landtype(WATER)
    >>> test(last_example=1)
    | ex. |                          groundwaterdepth |                          potentialcapillaryrise |
    -----------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 | 0.0  0.0  0.0  0.0  0.0                     0.0 |

    >>> landtype(GRAS)
    >>> capillaryrise(False)
    >>> test(last_example=1)
    | ex. |                          groundwaterdepth |                          potentialcapillaryrise |
    -----------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 | 0.0  0.0  0.0  0.0  0.0                     0.0 |
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.CapillaryRise,
        whmod_control.CapillaryThreshold,
        whmod_control.CapillaryLimit,
        whmod_control.GroundwaterDepth,
    )
    DERIVEDPARAMETERS = (whmod_derived.SoilDepth,)
    RESULTSEQUENCES = (whmod_fluxes.PotentialCapillaryRise,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.capillaryrise and (con.landtype[k] not in (SEALED, WATER)):
                schwell: float = con.capillarythreshold[k]
                grenz: float = con.capillarylimit[k]
                if con.groundwaterdepth[k] > (der.soildepth[k] + schwell):
                    flu.potentialcapillaryrise[k] = 0.0
                elif con.groundwaterdepth[k] < (der.soildepth[k] + grenz):
                    flu.potentialcapillaryrise[k] = 5.0
                else:
                    flu.potentialcapillaryrise[k] = (
                        5.0
                        * (der.soildepth[k] + schwell - con.groundwaterdepth[k])
                        / (schwell - grenz)
                    )
            else:
                flu.potentialcapillaryrise[k] = 0.0


class Calc_CapillaryRise_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, SEALED, WATER)
    >>> capillaryrise(True)
    >>> factors.relativesoilmoisture(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
    >>> fluxes.potentialcapillaryrise(2.0)
    >>> model.calc_capillaryrise_v1()
    >>> fluxes.capillaryrise
    capillaryrise(2.0, 0.84375, 0.25, 0.03125, 0.0, 0.0, 0.0)

    >>> capillaryrise(False)
    >>> model.calc_capillaryrise_v1()
    >>> fluxes.capillaryrise
    capillaryrise(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.CapillaryRise,
    )
    REQUIREDSEQUENCES = (
        whmod_fluxes.PotentialCapillaryRise,
        whmod_factors.RelativeSoilMoisture,
    )
    RESULTSEQUENCES = (whmod_fluxes.CapillaryRise,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.capillaryrise and (con.landtype[k] not in (SEALED, WATER)):
                flu.capillaryrise[k] = (
                    flu.potentialcapillaryrise[k]
                    * (1.0 - fac.relativesoilmoisture[k]) ** 3
                )
            else:
                flu.capillaryrise[k] = 0.0


class Calc_SoilMoisture_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> landtype(GRAS)
    >>> derived.maxsoilwater(100.0)
    >>> fluxes.ponding(2.0)
    >>> fluxes.soilevapotranspiration(1.0)
    >>> states.soilmoisture(0.0, 1.0, 50.0, 98.0, 100.0)
    >>> fluxes.capillaryrise(3.0, 3.0, 3.0, 5.0, 5.0)
    >>> fluxes.percolation(5.0, 5.0, 5.0, 3.0, 3.0)
    >>> model.calc_soilmoisture_v1()
    >>> states.soilmoisture
    soilmoisture(0.0, 0.0, 49.0, 100.0, 100.0)
    >>> fluxes.percolation
    percolation(4.0, 5.0, 5.0, 3.0, 3.0)
    >>> fluxes.capillaryrise
    capillaryrise(3.0, 3.0, 3.0, 4.0, 2.0)

    >>> landtype(WATER, WATER, WATER, SEALED, SEALED)
    >>> fluxes.soilevapotranspiration(0.0, 5.0, 10.0, 5.0, 5.0)
    >>> model.calc_soilmoisture_v1()
    >>> states.soilmoisture
    soilmoisture(0.0, 0.0, 0.0, 0.0, 0.0)
    >>> fluxes.percolation
    percolation(4.0, 5.0, 5.0, 3.0, 3.0)
    >>> fluxes.capillaryrise
    capillaryrise(3.0, 3.0, 3.0, 4.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
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
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                sta.soilmoisture[k] = 0.0
            else:
                sta.soilmoisture[k] += (
                    flu.ponding[k]
                    - flu.soilevapotranspiration[k]
                    - flu.percolation[k]
                    + flu.capillaryrise[k]
                )
                if sta.soilmoisture[k] < 0.0:
                    flu.percolation[k] += sta.soilmoisture[k]
                    sta.soilmoisture[k] = 0.0
                elif sta.soilmoisture[k] > der.maxsoilwater[k]:
                    flu.capillaryrise[k] += der.maxsoilwater[k] - sta.soilmoisture[k]
                    sta.soilmoisture[k] = der.maxsoilwater[k]


class Calc_PotentialRecharge_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(GRAS, SEALED, WATER)
    >>> inputs.precipitation(7.0)
    >>> fluxes.percolation(2.0)
    >>> fluxes.capillaryrise(1.0)
    >>> fluxes.lakeevaporation(4.0)
    >>> model.calc_potentialrecharge_v1()
    >>> fluxes.potentialrecharge
    potentialrecharge(1.0, 0.0, 3.0)
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
            if con.landtype[k] == WATER:
                flu.potentialrecharge[k] = inp.precipitation - flu.lakeevaporation[k]
            elif con.landtype[k] == SEALED:
                flu.potentialrecharge[k] = 0.0
            else:
                flu.potentialrecharge[k] = flu.percolation[k] - flu.capillaryrise[k]


class Calc_Baseflow_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(4)
    >>> baseflowindex(1.0, 0.8, 1.0, 0.8)
    >>> fluxes.potentialrecharge(1.0, 1.0, -1.0, -1.0)
    >>> model.calc_baseflow_v1()
    >>> fluxes.baseflow
    baseflow(0.0, 0.2, 0.0, 0.0)
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
                flu.baseflow[k] = max(
                    (1.0 - con.baseflowindex[k]) * flu.potentialrecharge[k], 0.0
                )


class Calc_ActualRecharge_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(4)
    >>> area(14.0)
    >>> zonearea(2.0, 3.0, 5.0, 4.0)
    >>> derived.zoneratio.update()
    >>> fluxes.potentialrecharge = 2.0, 10.0, -2.0, -0.5
    >>> fluxes.baseflow = 0.0, 5.0, 0.0, 0.0
    >>> model.calc_actualrecharge_v1()
    >>> fluxes.actualrecharge
    actualrecharge(0.5)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones,)
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
            flu.actualrecharge += der.zoneratio[k] * (
                flu.potentialrecharge[k] - flu.baseflow[k]
            )


class Calc_DelayedRecharge_DeepWater_V1(modeltools.Method):
    """

    Nur eine Näherungslösung. Bei kleinen Flurabständen etwas zu geringe
    Verzögerung möglich, dafür immer bilanztreu.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> from numpy import arange
    >>> from hydpy import print_vector
    >>> for k in numpy.arange(0., 5.5, .5):
    ...     rechargedelay.value = k
    ...     states.deepwater = 2.0
    ...     fluxes.actualrecharge = 1.0
    ...     model.calc_delayedrecharge_deepwater_v1()
    ...     print_vector(
    ...         [k,
    ...          fluxes.delayedrecharge.value,
    ...          states.deepwater.value])
    0.0, 3.0, 0.0
    0.5, 2.593994, 0.406006
    1.0, 1.896362, 1.103638
    1.5, 1.459749, 1.540251
    2.0, 1.180408, 1.819592
    2.5, 0.98904, 2.01096
    3.0, 0.850406, 2.149594
    3.5, 0.745568, 2.254432
    4.0, 0.663598, 2.336402
    4.5, 0.597788, 2.402212
    5.0, 0.543808, 2.456192
    """

    CONTROLPARAMETERS = (whmod_control.RechargeDelay,)
    REQUIREDSEQUENCES = (whmod_fluxes.ActualRecharge,)
    UPDATEDSEQUENCES = (whmod_states.DeepWater,)
    RESULTSEQUENCES = (whmod_fluxes.DelayedRecharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if con.rechargedelay > 0:
            sp: float = (sta.deepwater + flu.actualrecharge) * modelutils.exp(
                -1.0 / con.rechargedelay
            )
            flu.delayedrecharge = flu.actualrecharge + sta.deepwater - sp
            sta.deepwater = sp
        else:
            flu.delayedrecharge = sta.deepwater + flu.actualrecharge
            sta.deepwater = 0.0


class Model(modeltools.AdHocModel):
    """|whmod.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="WHMod")
    __HYDPY_ROOTMODEL__ = None

    aetmodel = modeltools.SubmodelProperty(aetinterfaces.AETModel_V1)
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_MaxVerdunstung_V1,
        Calc_Throughfall_InterceptedWater_V1,
        Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_V1,
        Calc_SurfaceRunoff_V1,
        Calc_Ponding_V1,
        Calc_RelativeSoilMoisture_V1,
        Calc_Percolation_V1,
        Calc_SoilEvapotranspiration_V1,
        Corr_SoilEvapotranspiration_V1,
        Calc_LakeEvaporation_V1,
        Calc_TotalEvapotranspiration_V1,
        Calc_PotentialCapillaryRise_V1,
        Calc_CapillaryRise_V1,
        Calc_SoilMoisture_V1,
        Calc_PotentialRecharge_V1,
        Calc_Baseflow_V1,
        Calc_ActualRecharge_V1,
        Calc_DelayedRecharge_DeepWater_V1,
    )
    ADD_METHODS = (
        Calc_InterceptionEvaporation_InterceptedWater_LakeEvaporation_AETModel_V1,
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
        landtype_constants=whmod_constants.LANDUSE_CONSTANTS,
        landtype_refindices=whmod_control.LandType,
        soiltype_constants=whmod_constants.SOIL_CONSTANTS,
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

        >>> from hydpy.models.whmod_pet import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> area(10.0)
        >>> landtype(GRAS, DECIDIOUS, CONIFER, WATER, SEALED)
        >>> zonearea(4.0, 1.0, 1.0, 1.0, 3.0)
        >>> derived.availablefieldcapacity○(200.0)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     nmbhru
        ...     area
        ...     water
        ...     interception
        ...     soil
        ...     dissefactor(gras=1.0, decidious=2.0, default=3.0)
        ...     for method, arguments in model.preparemethod2arguments.items():
        ...         print(method, arguments[0][0], sep=": ")
        nmbhru(5)
        area(10.0)
        water(conifer=False, decidious=False, gras=False, sealed=False,
              water=True)
        interception(conifer=True, decidious=True, gras=True, sealed=False,
                     water=False)
        soil(conifer=True, decidious=True, gras=True, sealed=False,
             water=False)
        prepare_nmbzones: 5
        prepare_zonetypes: [1 2 4 9 8]
        prepare_subareas: [4. 1. 1. 1. 3.]
        prepare_water: [False False False  True False]
        prepare_interception: [ True  True  True False False]
        prepare_soil: [ True  True  True False False]
        prepare_plant: [ True  True  True False False]
        prepare_conifer: [False False  True False False]
        prepare_tree: [False  True  True False False]
        prepare_maxsoilwater: [200. 200. 200. 200. 200.]

        >>> df = model.aetmodel.parameters.control.dissefactor
        >>> df
        dissefactor(conifer=3.0, decidious=2.0, gras=1.0)
        >>> landtype(DECIDIOUS, GRAS, CONIFER, WATER, SEALED)
        >>> df
        dissefactor(conifer=3.0, decidious=1.0, gras=2.0)
        >>> from hydpy import round_
        >>> round_(df.average_values())
        1.5
        """
        control = self.parameters.control

        hydrotopes = control.nmbzones.value
        landtype = control.landtype.values

        aetmodel.prepare_nmbzones(hydrotopes)
        aetmodel.prepare_zonetypes(landtype)
        aetmodel.prepare_subareas(control.zonearea.value)
        sel = numpy.full(hydrotopes, False, dtype=config.NP_BOOL)
        sel[landtype == WATER] = True
        aetmodel.prepare_water(sel)
        sel = ~sel
        sel[landtype == SEALED] = False
        aetmodel.prepare_interception(sel)
        aetmodel.prepare_soil(sel)
        aetmodel.prepare_plant(sel)
        sel[:] = False
        sel[landtype == CONIFER] = True
        aetmodel.prepare_conifer(sel)
        sel[landtype == DECIDIOUS] = True
        aetmodel.prepare_tree(sel)

        aetmodel.prepare_maxsoilwater(control.availablefieldcapacity.values)
