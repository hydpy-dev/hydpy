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


class Calc_NiederschlagRichter_V1(modeltools.Method):
    """Niederschlagskorrektur nach Richter.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> inputs.niederschlag = 5.0
    >>> model.calc_niederschlagrichter_v1()
    >>> fluxes.niederschlagrichter
    niederschlagrichter(5.0)
    """

    REQUIREDSEQUENCES = (whmod_inputs.Niederschlag,)
    RESULTSEQUENCES = (whmod_fluxes.NiederschlagRichter,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.niederschlagrichter = inp.niederschlag


class Calc_NiedNachInterz_V1(modeltools.Method):
    """Berechnung Bestandsniederschlag.

    Erst mal keine Interzeptionsverdunstung!!!

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(2)
    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_niednachinterz_v1,
    ...     last_example=11,
    ...     parseqs=(fluxes.niederschlagrichter, fluxes.niednachinterz))
    >>> test.nexts.niederschlagrichter = range(0, 11, 1)
    >>> test()
    | ex. | niederschlagrichter |       niednachinterz |
    ----------------------------------------------------
    |   1 |                 0.0 |  0.0             0.0 |
    |   2 |                 1.0 |  1.0             1.0 |
    |   3 |                 2.0 |  2.0             2.0 |
    |   4 |                 3.0 |  3.0             3.0 |
    |   5 |                 4.0 |  4.0             4.0 |
    |   6 |                 5.0 |  5.0             5.0 |
    |   7 |                 6.0 |  6.0             6.0 |
    |   8 |                 7.0 |  7.0             7.0 |
    |   9 |                 8.0 |  8.0             8.0 |
    |  10 |                 9.0 |  9.0             9.0 |
    |  11 |                10.0 | 10.0            10.0 |
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones,)
    REQUIREDSEQUENCES = (whmod_fluxes.NiederschlagRichter,)
    RESULTSEQUENCES = (whmod_fluxes.NiedNachInterz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.niednachinterz[k] = flu.niederschlagrichter


class Calc_Seeniederschlag_V1(modeltools.Method):
    """Berechnung Niederschlag auf Wasserflächen.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(GRAS, SEALED, WATER)
    >>> fluxes.niederschlagrichter = 2.0
    >>> model.calc_seeniederschlag_v1()
    >>> fluxes.seeniederschlag
    seeniederschlag(0.0, 0.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (whmod_fluxes.NiederschlagRichter,)
    RESULTSEQUENCES = (whmod_fluxes.Seeniederschlag,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.seeniederschlag[k] = flu.niederschlagrichter
            else:
                flu.seeniederschlag[k] = 0.0


class Calc_Interzeptionsspeicher_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(6)
    >>> landtype(DECIDIOUS)
    >>> maxinterz(gras=[0.4, 0.4, 0.6, 0.8, 1.0, 1.0,
    ...                 1.0, 1.0, 1.0, 0.6, 0.5, 0.4],
    ...           decidious=[0.1, 0.1, 0.3, 0.8, 1.4, 2.2,
    ...                     2.4, 2.4, 2.2, 1.6, 0.3, 0.1],
    ...           corn=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                 0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           conifer=[2.2, 2.2, 2.2, 2.2, 2.2, 2.2,
    ...                      2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
    ...           springwheat=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                         0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           winterwheat=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                         0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           sugarbeets=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                         0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           sealed=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...                       2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
    ...           water=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    ...                   0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    >>> from hydpy import pub
    >>> pub.timegrids = "2001-06-29", "2001-07-03", "1d"
    >>> derived.moy.update()

    >>> fluxes.niederschlagrichter = 1.0
    >>> fluxes.maxverdunstung = 0.0, 0.0, 0.0, 1.0, 2.0, 3.0
    >>> states.interzeptionsspeicher = 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
    >>> model.idx_sim = 1
    >>> model.calc_interzeptionsspeicher_v1()
    >>> states.interzeptionsspeicher
    interzeptionsspeicher(1.0, 2.0, 2.2, 1.2, 0.2, 0.0)
    >>> fluxes.niednachinterz
    niednachinterz(0.0, 0.0, 0.8, 0.8, 0.8, 0.8)
    >>> fluxes.interzeptionsverdunstung
    interzeptionsverdunstung(0.0, 0.0, 0.0, 1.0, 2.0, 2.2)

    >>> states.interzeptionsspeicher = 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
    >>> model.idx_sim = 2
    >>> model.calc_interzeptionsspeicher_v1()
    >>> states.interzeptionsspeicher
    interzeptionsspeicher(1.0, 2.0, 2.4, 1.4, 0.4, 0.0)
    >>> fluxes.niednachinterz
    niednachinterz(0.0, 0.0, 0.6, 0.6, 0.6, 0.6)
    >>> fluxes.interzeptionsverdunstung
    interzeptionsverdunstung(0.0, 0.0, 0.0, 1.0, 2.0, 2.4)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.MaxInterz,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY,)
    REQUIREDSEQUENCES = (whmod_fluxes.NiederschlagRichter, whmod_fluxes.MaxVerdunstung)
    UPDATEDSEQUENCES = (whmod_states.Interzeptionsspeicher,)
    RESULTSEQUENCES = (
        whmod_fluxes.NiedNachInterz,
        whmod_fluxes.InterzeptionsVerdunstung,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        month = der.moy[model.idx_sim]
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                sta.interzeptionsspeicher[k] = 0.0
                flu.niednachinterz[k] = flu.niederschlagrichter
                flu.interzeptionsverdunstung[k] = 0.0
            else:
                d_maxinterz = con.maxinterz[con.landtype[k] - 1, month]
                sta.interzeptionsspeicher[k] += flu.niederschlagrichter
                flu.niednachinterz[k] = max(
                    sta.interzeptionsspeicher[k] - d_maxinterz, 0.0
                )
                sta.interzeptionsspeicher[k] -= flu.niednachinterz[k]
                flu.interzeptionsverdunstung[k] = min(
                    sta.interzeptionsspeicher[k], flu.maxverdunstung[k]
                )
                sta.interzeptionsspeicher[k] -= flu.interzeptionsverdunstung[k]


class Calc_Oberflaechenabfluss_V1(modeltools.Method):
    """Berechnung Oberflaechenabfluss.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(SEALED, WATER, GRAS)
    >>> fluxes.niednachinterz = 3.0
    >>> model.calc_oberflaechenabfluss_v1()
    >>> fluxes.oberflaechenabfluss
    oberflaechenabfluss(3.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (whmod_fluxes.NiedNachInterz,)
    RESULTSEQUENCES = (whmod_fluxes.Oberflaechenabfluss,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.oberflaechenabfluss[k] = flu.niednachinterz[k]
            else:
                flu.oberflaechenabfluss[k] = 0.0


class Calc_ZuflussBoden_V1(modeltools.Method):
    """Berechnung Bestandsniederschlag.

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> simulationstep("1d")
    >>> nmbzones(2)
    >>> landtype(GRAS, GRAS)
    >>> degreedayfactor(4.5)
    >>> fluxes.niednachinterz = 3.0

    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_zuflussboden_v1,
    ...     last_example=6,
    ...     parseqs=(inputs.temp_tm,
    ...              states.schneespeicher,
    ...              fluxes.zuflussboden))
    >>> test.nexts.temp_tm = range(-1, 6)
    >>> test.inits.schneespeicher = (0.0, 10.0)
    >>> test()
    | ex. | temp_tm |      schneespeicher |      zuflussboden |
    -----------------------------------------------------------
    |   1 |    -1.0 | 3.0            13.0 | 0.0           0.0 |
    |   2 |     0.0 | 3.0            13.0 | 0.0           0.0 |
    |   3 |     1.0 | 0.0             5.5 | 3.0           7.5 |
    |   4 |     2.0 | 0.0             1.0 | 3.0          12.0 |
    |   5 |     3.0 | 0.0             0.0 | 3.0          13.0 |
    |   6 |     4.0 | 0.0             0.0 | 3.0          13.0 |

    >>> landtype(SEALED, WATER)
    >>> states.schneespeicher = 5.0
    >>> fluxes.niednachinterz = 2.0
    >>> model.calc_zuflussboden_v1()
    >>> states.schneespeicher
    schneespeicher(0.0, 0.0)
    >>> fluxes.zuflussboden
    zuflussboden(0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.DegreeDayFactor,
    )
    REQUIREDSEQUENCES = (whmod_inputs.Temp_TM, whmod_fluxes.NiedNachInterz)
    UPDATEDSEQUENCES = (whmod_states.Schneespeicher,)
    RESULTSEQUENCES = (whmod_fluxes.ZuflussBoden,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                sta.schneespeicher[k] = 0.0
                flu.zuflussboden[k] = 0.0
            elif inp.temp_tm > 0.0:
                d_maxschneeschmelze = con.degreedayfactor[k] * inp.temp_tm
                d_schneeschmelze = min(sta.schneespeicher[k], d_maxschneeschmelze)
                sta.schneespeicher[k] -= d_schneeschmelze
                flu.zuflussboden[k] = flu.niednachinterz[k] + d_schneeschmelze
            else:
                sta.schneespeicher[k] += flu.niednachinterz[k]
                flu.zuflussboden[k] = 0.0


class Calc_RelBodenfeuchte_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRAS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT,
    ...         SUGARBEETS, SEALED, WATER)
    >>> derived.maxsoilwater(200.0)
    >>> states.aktbodenwassergehalt(100.0)
    >>> model.calc_relbodenfeuchte_v1()
    >>> factors.relbodenfeuchte
    relbodenfeuchte(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    DERIVEDPARAMETERS = (whmod_derived.MaxSoilWater,)
    REQUIREDSEQUENCES = (whmod_states.AktBodenwassergehalt,)
    RESULTSEQUENCES = (whmod_factors.RelBodenfeuchte,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if (con.landtype[k] in (WATER, SEALED)) or (der.maxsoilwater[k] <= 0.0):
                fac.relbodenfeuchte[k] = 0.0
            else:
                fac.relbodenfeuchte[k] = (
                    sta.aktbodenwassergehalt[k] / der.maxsoilwater[k]
                )


class Calc_Sickerwasser_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRAS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT,
    ...         SUGARBEETS, SEALED, WATER)
    >>> derived.beta(2.0)
    >>> fluxes.zuflussboden(10.0)
    >>> factors.relbodenfeuchte(0.5)
    >>> model.calc_sickerwasser_v1()
    >>> fluxes.sickerwasser
    sickerwasser(2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    DERIVEDPARAMETERS = (whmod_derived.Beta,)
    REQUIREDSEQUENCES = (whmod_fluxes.ZuflussBoden, whmod_factors.RelBodenfeuchte)
    RESULTSEQUENCES = (whmod_fluxes.Sickerwasser,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                flu.sickerwasser[k] = 0.0
            else:
                flu.sickerwasser[k] = (
                    flu.zuflussboden[k] * fac.relbodenfeuchte[k] ** der.beta[k]
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


class Calc_Bodenverdunstung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, SEALED, WATER)
    >>> minhasr(3.0)
    >>> fluxes.maxverdunstung = 2.0
    >>> factors.relbodenfeuchte = 0.0, 0.25, 0.5, 0.75, 1.0, 0.5, 0.5
    >>> model.calc_bodenverdunstung_v1()
    >>> fluxes.bodenverdunstung
    bodenverdunstung(0.0, 0.768701, 1.382877, 1.77884, 2.0, 0.0, 0.0)

    >>> minhasr(6.0)
    >>> model.calc_bodenverdunstung_v1()
    >>> fluxes.bodenverdunstung
    bodenverdunstung(0.0, 1.275468, 1.818886, 1.96569, 2.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.MinhasR,
    )
    REQUIREDSEQUENCES = (whmod_factors.RelBodenfeuchte, whmod_fluxes.MaxVerdunstung)
    RESULTSEQUENCES = (whmod_fluxes.Bodenverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                flu.bodenverdunstung[k] = 0.0
            else:
                d_temp = modelutils.exp(-con.minhasr[k] * fac.relbodenfeuchte[k])
                flu.bodenverdunstung[k] = (
                    flu.maxverdunstung[k]
                    * (1.0 - d_temp)
                    / (1.0 - 2.0 * modelutils.exp(-con.minhasr[k]) + d_temp)
                )


class Corr_Bodenverdunstung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, WATER, SEALED)
    >>> fluxes.maxverdunstung = 2.0
    >>> fluxes.interzeptionsverdunstung = 0.0, 0.5, 1.0, 1.5, 2.0, 2.0, 2.0
    >>> fluxes.bodenverdunstung = 1.0
    >>> model.corr_bodenverdunstung_v1()
    >>> fluxes.bodenverdunstung
    bodenverdunstung(1.0, 0.75, 0.5, 0.25, 0.0, 0.0, 0.0)
    >>> from hydpy import print_vector
    >>> print_vector(fluxes.interzeptionsverdunstung[:5] + fluxes.bodenverdunstung[:5])
    1.0, 1.25, 1.5, 1.75, 2.0

    >>> fluxes.interzeptionsverdunstung = 1.0
    >>> fluxes.bodenverdunstung = 0.0, 0.5, 1.0, 1.5, 2.0, 2.0, 2.0
    >>> model.corr_bodenverdunstung_v1()
    >>> fluxes.bodenverdunstung
    bodenverdunstung(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
    >>> print_vector(fluxes.interzeptionsverdunstung[:5] + fluxes.bodenverdunstung[:5])
    1.0, 1.25, 1.5, 1.75, 2.0
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (
        whmod_fluxes.MaxVerdunstung,
        whmod_fluxes.InterzeptionsVerdunstung,
    )
    UPDATEDSEQUENCES = (whmod_fluxes.Bodenverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                flu.bodenverdunstung[k] = 0.0
            elif flu.maxverdunstung[k] <= flu.interzeptionsverdunstung[k]:
                flu.bodenverdunstung[k] = 0.0
            else:
                flu.bodenverdunstung[k] *= (
                    flu.maxverdunstung[k] - flu.interzeptionsverdunstung[k]
                ) / flu.maxverdunstung[k]


class Calc_Seeverdunstung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(GRAS, SEALED, WATER)
    >>> fluxes.maxverdunstung = 2.0
    >>> model.calc_seeverdunstung_v1()
    >>> fluxes.seeverdunstung
    seeverdunstung(0.0, 0.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (whmod_fluxes.MaxVerdunstung,)
    RESULTSEQUENCES = (whmod_fluxes.Seeverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.seeverdunstung[k] = flu.maxverdunstung[k]
            else:
                flu.seeverdunstung[k] = 0.0


class Calc_AktVerdunstung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(2)
    >>> fluxes.interzeptionsverdunstung = 1.0, 0.0
    >>> fluxes.bodenverdunstung = 2.0, 0.0
    >>> fluxes.seeverdunstung = 0.0, 4.0
    >>> model.calc_aktverdunstung_v1()
    >>> fluxes.aktverdunstung
    aktverdunstung(3.0, 4.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones,)
    REQUIREDSEQUENCES = (
        whmod_fluxes.InterzeptionsVerdunstung,
        whmod_fluxes.Bodenverdunstung,
        whmod_fluxes.Seeverdunstung,
    )
    RESULTSEQUENCES = (whmod_fluxes.AktVerdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            flu.aktverdunstung[k] = (
                flu.interzeptionsverdunstung[k]
                + flu.bodenverdunstung[k]
                + flu.seeverdunstung[k]
            )


class Calc_PotKapilAufstieg_V1(modeltools.Method):
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
    ...     model, model.calc_potkapilaufstieg_v1,
    ...     last_example=31,
    ...     parseqs=(control.groundwaterdepth,
    ...              fluxes.potkapilaufstieg))
    >>> import numpy
    >>> test.nexts.groundwaterdepth = numpy.arange(0.0, 3.1, 0.1)
    >>> test()
    | ex. |                          groundwaterdepth |                                           potkapilaufstieg |
    ----------------------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   2 | 0.1  0.1  0.1  0.1  0.1               0.1 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   3 | 0.2  0.2  0.2  0.2  0.2               0.2 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   4 | 0.3  0.3  0.3  0.3  0.3               0.3 |  5.0       5.0       5.0  4.772727   5.0               5.0 |
    |   5 | 0.4  0.4  0.4  0.4  0.4               0.4 |  5.0       5.0       5.0  4.318182   5.0               5.0 |
    |   6 | 0.5  0.5  0.5  0.5  0.5               0.5 | 3.75       5.0  4.736842  3.863636   5.0               5.0 |
    |   7 | 0.6  0.6  0.6  0.6  0.6               0.6 |  2.5       5.0  4.210526  3.409091   5.0          4.166667 |
    |   8 | 0.7  0.7  0.7  0.7  0.7               0.7 | 1.25       5.0  3.684211  2.954545   5.0               2.5 |
    |   9 | 0.8  0.8  0.8  0.8  0.8               0.8 |  0.0       5.0  3.157895       2.5  4.75          0.833333 |
    |  10 | 0.9  0.9  0.9  0.9  0.9               0.9 |  0.0  4.545455  2.631579  2.045455  4.25               0.0 |
    |  11 | 1.0  1.0  1.0  1.0  1.0               1.0 |  0.0  3.636364  2.105263  1.590909  3.75               0.0 |
    |  12 | 1.1  1.1  1.1  1.1  1.1               1.1 |  0.0  2.727273  1.578947  1.136364  3.25               0.0 |
    |  13 | 1.2  1.2  1.2  1.2  1.2               1.2 |  0.0  1.818182  1.052632  0.681818  2.75               0.0 |
    |  14 | 1.3  1.3  1.3  1.3  1.3               1.3 |  0.0  0.909091  0.526316  0.227273  2.25               0.0 |
    |  15 | 1.4  1.4  1.4  1.4  1.4               1.4 |  0.0       0.0       0.0       0.0  1.75               0.0 |
    |  16 | 1.5  1.5  1.5  1.5  1.5               1.5 |  0.0       0.0       0.0       0.0  1.25               0.0 |
    |  17 | 1.6  1.6  1.6  1.6  1.6               1.6 |  0.0       0.0       0.0       0.0  0.75               0.0 |
    |  18 | 1.7  1.7  1.7  1.7  1.7               1.7 |  0.0       0.0       0.0       0.0  0.25               0.0 |
    |  19 | 1.8  1.8  1.8  1.8  1.8               1.8 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  20 | 1.9  1.9  1.9  1.9  1.9               1.9 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  21 | 2.0  2.0  2.0  2.0  2.0               2.0 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  22 | 2.1  2.1  2.1  2.1  2.1               2.1 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  23 | 2.2  2.2  2.2  2.2  2.2               2.2 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  24 | 2.3  2.3  2.3  2.3  2.3               2.3 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  25 | 2.4  2.4  2.4  2.4  2.4               2.4 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  26 | 2.5  2.5  2.5  2.5  2.5               2.5 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  27 | 2.6  2.6  2.6  2.6  2.6               2.6 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  28 | 2.7  2.7  2.7  2.7  2.7               2.7 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  29 | 2.8  2.8  2.8  2.8  2.8               2.8 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  30 | 2.9  2.9  2.9  2.9  2.9               2.9 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  31 | 3.0  3.0  3.0  3.0  3.0               3.0 |  0.0       0.0       0.0       0.0   0.0               0.0 |

    >>> derived.soildepth(1.0)
    >>> test()
    | ex. |                          groundwaterdepth |                                           potkapilaufstieg |
    ----------------------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   2 | 0.1  0.1  0.1  0.1  0.1               0.1 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   3 | 0.2  0.2  0.2  0.2  0.2               0.2 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   4 | 0.3  0.3  0.3  0.3  0.3               0.3 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   5 | 0.4  0.4  0.4  0.4  0.4               0.4 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   6 | 0.5  0.5  0.5  0.5  0.5               0.5 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   7 | 0.6  0.6  0.6  0.6  0.6               0.6 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   8 | 0.7  0.7  0.7  0.7  0.7               0.7 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   9 | 0.8  0.8  0.8  0.8  0.8               0.8 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  10 | 0.9  0.9  0.9  0.9  0.9               0.9 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  11 | 1.0  1.0  1.0  1.0  1.0               1.0 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  12 | 1.1  1.1  1.1  1.1  1.1               1.1 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  13 | 1.2  1.2  1.2  1.2  1.2               1.2 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  14 | 1.3  1.3  1.3  1.3  1.3               1.3 |  5.0       5.0       5.0  4.772727   5.0               5.0 |
    |  15 | 1.4  1.4  1.4  1.4  1.4               1.4 |  5.0       5.0       5.0  4.318182   5.0               5.0 |
    |  16 | 1.5  1.5  1.5  1.5  1.5               1.5 | 3.75       5.0  4.736842  3.863636   5.0               5.0 |
    |  17 | 1.6  1.6  1.6  1.6  1.6               1.6 |  2.5       5.0  4.210526  3.409091   5.0          4.166667 |
    |  18 | 1.7  1.7  1.7  1.7  1.7               1.7 | 1.25       5.0  3.684211  2.954545   5.0               2.5 |
    |  19 | 1.8  1.8  1.8  1.8  1.8               1.8 |  0.0       5.0  3.157895       2.5  4.75          0.833333 |
    |  20 | 1.9  1.9  1.9  1.9  1.9               1.9 |  0.0  4.545455  2.631579  2.045455  4.25               0.0 |
    |  21 | 2.0  2.0  2.0  2.0  2.0               2.0 |  0.0  3.636364  2.105263  1.590909  3.75               0.0 |
    |  22 | 2.1  2.1  2.1  2.1  2.1               2.1 |  0.0  2.727273  1.578947  1.136364  3.25               0.0 |
    |  23 | 2.2  2.2  2.2  2.2  2.2               2.2 |  0.0  1.818182  1.052632  0.681818  2.75               0.0 |
    |  24 | 2.3  2.3  2.3  2.3  2.3               2.3 |  0.0  0.909091  0.526316  0.227273  2.25               0.0 |
    |  25 | 2.4  2.4  2.4  2.4  2.4               2.4 |  0.0       0.0       0.0       0.0  1.75               0.0 |
    |  26 | 2.5  2.5  2.5  2.5  2.5               2.5 |  0.0       0.0       0.0       0.0  1.25               0.0 |
    |  27 | 2.6  2.6  2.6  2.6  2.6               2.6 |  0.0       0.0       0.0       0.0  0.75               0.0 |
    |  28 | 2.7  2.7  2.7  2.7  2.7               2.7 |  0.0       0.0       0.0       0.0  0.25               0.0 |
    |  29 | 2.8  2.8  2.8  2.8  2.8               2.8 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  30 | 2.9  2.9  2.9  2.9  2.9               2.9 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  31 | 3.0  3.0  3.0  3.0  3.0               3.0 |  0.0       0.0       0.0       0.0   0.0               0.0 |

    >>> landtype(SEALED)
    >>> test(last_example=1)
    | ex. |                          groundwaterdepth |                          potkapilaufstieg |
    -----------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 | 0.0  0.0  0.0  0.0  0.0               0.0 |

    >>> landtype(WATER)
    >>> test(last_example=1)
    | ex. |                          groundwaterdepth |                          potkapilaufstieg |
    -----------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 | 0.0  0.0  0.0  0.0  0.0               0.0 |

    >>> landtype(GRAS)
    >>> capillaryrise(False)
    >>> test(last_example=1)
    | ex. |                          groundwaterdepth |                          potkapilaufstieg |
    -----------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0               0.0 | 0.0  0.0  0.0  0.0  0.0               0.0 |
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
    RESULTSEQUENCES = (whmod_fluxes.PotKapilAufstieg,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.capillaryrise and (con.landtype[k] not in (SEALED, WATER)):
                d_schwell = con.capillarythreshold[k]
                d_grenz = con.capillarylimit[k]
                if con.groundwaterdepth[k] > (der.soildepth[k] + d_schwell):
                    flu.potkapilaufstieg[k] = 0.0
                elif con.groundwaterdepth[k] < (der.soildepth[k] + d_grenz):
                    flu.potkapilaufstieg[k] = 5.0
                else:
                    flu.potkapilaufstieg[k] = (
                        5.0
                        * (der.soildepth[k] + d_schwell - con.groundwaterdepth[k])
                        / (d_schwell - d_grenz)
                    )
            else:
                flu.potkapilaufstieg[k] = 0.0


class Calc_KapilAufstieg_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, SEALED, WATER)
    >>> capillaryrise(True)
    >>> factors.relbodenfeuchte(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
    >>> fluxes.potkapilaufstieg(2.0)
    >>> model.calc_kapilaufstieg_v1()
    >>> fluxes.kapilaufstieg
    kapilaufstieg(2.0, 0.84375, 0.25, 0.03125, 0.0, 0.0, 0.0)

    >>> capillaryrise(False)
    >>> model.calc_kapilaufstieg_v1()
    >>> fluxes.kapilaufstieg
    kapilaufstieg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.CapillaryRise,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.PotKapilAufstieg, whmod_factors.RelBodenfeuchte)
    RESULTSEQUENCES = (whmod_fluxes.KapilAufstieg,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.capillaryrise and (con.landtype[k] not in (SEALED, WATER)):
                flu.kapilaufstieg[k] = (
                    flu.potkapilaufstieg[k] * (1.0 - fac.relbodenfeuchte[k]) ** 3
                )
            else:
                flu.kapilaufstieg[k] = 0.0


class Calc_AktBodenwassergehalt_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> landtype(GRAS)
    >>> derived.maxsoilwater(100.0)
    >>> fluxes.zuflussboden(2.0)
    >>> fluxes.bodenverdunstung(1.0)
    >>> states.aktbodenwassergehalt(0.0, 1.0, 50.0, 98.0, 100.0)
    >>> fluxes.kapilaufstieg(3.0, 3.0, 3.0, 5.0, 5.0)
    >>> fluxes.sickerwasser(5.0, 5.0, 5.0, 3.0, 3.0)
    >>> model.calc_aktbodenwassergehalt_v1()
    >>> states.aktbodenwassergehalt
    aktbodenwassergehalt(0.0, 0.0, 49.0, 100.0, 100.0)
    >>> fluxes.sickerwasser
    sickerwasser(4.0, 5.0, 5.0, 3.0, 3.0)
    >>> fluxes.kapilaufstieg
    kapilaufstieg(3.0, 3.0, 3.0, 4.0, 2.0)

    >>> landtype(WATER, WATER, WATER, SEALED, SEALED)
    >>> fluxes.bodenverdunstung(0.0, 5.0, 10.0, 5.0, 5.0)
    >>> model.calc_aktbodenwassergehalt_v1()
    >>> states.aktbodenwassergehalt
    aktbodenwassergehalt(0.0, 0.0, 0.0, 0.0, 0.0)
    >>> fluxes.sickerwasser
    sickerwasser(4.0, 5.0, 5.0, 3.0, 3.0)
    >>> fluxes.kapilaufstieg
    kapilaufstieg(3.0, 3.0, 3.0, 4.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    DERIVEDPARAMETERS = (whmod_derived.MaxSoilWater,)
    REQUIREDSEQUENCES = (
        whmod_fluxes.ZuflussBoden,
        whmod_fluxes.Bodenverdunstung,
        whmod_fluxes.Sickerwasser,
        whmod_fluxes.KapilAufstieg,
    )
    UPDATEDSEQUENCES = (whmod_states.AktBodenwassergehalt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] in (SEALED, WATER):
                sta.aktbodenwassergehalt[k] = 0.0
            else:
                sta.aktbodenwassergehalt[k] += (
                    flu.zuflussboden[k]
                    - flu.bodenverdunstung[k]
                    - flu.sickerwasser[k]
                    + flu.kapilaufstieg[k]
                )
                if sta.aktbodenwassergehalt[k] < 0.0:
                    flu.sickerwasser[k] += sta.aktbodenwassergehalt[k]
                    sta.aktbodenwassergehalt[k] = 0.0
                elif sta.aktbodenwassergehalt[k] > der.maxsoilwater[k]:
                    flu.kapilaufstieg[k] += (
                        der.maxsoilwater[k] - sta.aktbodenwassergehalt[k]
                    )
                    sta.aktbodenwassergehalt[k] = der.maxsoilwater[k]


class Calc_PotGrundwasserneubildung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> landtype(GRAS, SEALED, WATER)
    >>> fluxes.sickerwasser(2.0)
    >>> fluxes.kapilaufstieg(1.0)
    >>> fluxes.seeniederschlag(7.0)
    >>> fluxes.seeverdunstung(4.0)
    >>> model.calc_potgrundwasserneubildung_v1()
    >>> fluxes.potgrundwasserneubildung
    potgrundwasserneubildung(1.0, 0.0, 3.0)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones, whmod_control.LandType)
    REQUIREDSEQUENCES = (
        whmod_fluxes.Seeniederschlag,
        whmod_fluxes.Seeverdunstung,
        whmod_fluxes.Sickerwasser,
        whmod_fluxes.KapilAufstieg,
    )
    RESULTSEQUENCES = (whmod_fluxes.PotGrundwasserneubildung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == WATER:
                flu.potgrundwasserneubildung[k] = (
                    flu.seeniederschlag[k] - flu.seeverdunstung[k]
                )
            elif con.landtype[k] == SEALED:
                flu.potgrundwasserneubildung[k] = 0.0
            else:
                flu.potgrundwasserneubildung[k] = (
                    flu.sickerwasser[k] - flu.kapilaufstieg[k]
                )


class Calc_Basisabfluss_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(4)
    >>> baseflowindex(1.0, 0.8, 1.0, 0.8)
    >>> fluxes.potgrundwasserneubildung(1.0, 1.0, -1.0, -1.0)
    >>> model.calc_basisabfluss_v1()
    >>> fluxes.basisabfluss
    basisabfluss(0.0, 0.2, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.NmbZones,
        whmod_control.LandType,
        whmod_control.BaseflowIndex,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.PotGrundwasserneubildung,)
    RESULTSEQUENCES = (whmod_fluxes.Basisabfluss,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbzones):
            if con.landtype[k] == SEALED:
                flu.basisabfluss[k] = 0.0
            else:
                flu.basisabfluss[k] = max(
                    (1.0 - con.baseflowindex[k]) * flu.potgrundwasserneubildung[k], 0.0
                )


class Calc_AktGrundwasserneubildung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(4)
    >>> area(14.0)
    >>> zonearea(2.0, 3.0, 5.0, 4.0)
    >>> derived.zoneratio.update()
    >>> fluxes.potgrundwasserneubildung = 2.0, 10.0, -2.0, -0.5
    >>> fluxes.basisabfluss = 0.0, 5.0, 0.0, 0.0
    >>> model.calc_aktgrundwasserneubildung_v1()
    >>> fluxes.aktgrundwasserneubildung
    aktgrundwasserneubildung(0.5)
    """

    CONTROLPARAMETERS = (whmod_control.NmbZones,)
    DERIVEDPARAMETERS = (whmod_derived.ZoneRatio,)
    REQUIREDSEQUENCES = (
        whmod_fluxes.PotGrundwasserneubildung,
        whmod_fluxes.Basisabfluss,
    )
    RESULTSEQUENCES = (whmod_fluxes.AktGrundwasserneubildung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.aktgrundwasserneubildung = 0.0
        for k in range(con.nmbzones):
            flu.aktgrundwasserneubildung += der.zoneratio[k] * (
                flu.potgrundwasserneubildung[k] - flu.basisabfluss[k]
            )


class Calc_VerzGrundwasserneubildung_Zwischenspeicher_V1(modeltools.Method):
    """

    Nur eine Näherungslösung. Bei kleinen Flurabständen etwas zu geringe
    Verzögerung möglich, dafür immer bilanztreu.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> from numpy import arange
    >>> from hydpy import print_vector
    >>> for k in numpy.arange(0., 5.5, .5):
    ...     rechargedelay.value = k
    ...     states.zwischenspeicher = 2.0
    ...     fluxes.aktgrundwasserneubildung = 1.0
    ...     model.calc_verzgrundwasserneubildung_zwischenspeicher_v1()
    ...     print_vector(
    ...         [k,
    ...          fluxes.verzgrundwasserneubildung.value,
    ...          states.zwischenspeicher.value])
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
    REQUIREDSEQUENCES = (whmod_fluxes.AktGrundwasserneubildung,)
    UPDATEDSEQUENCES = (whmod_states.Zwischenspeicher,)
    RESULTSEQUENCES = (whmod_fluxes.VerzGrundwasserneubildung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if con.rechargedelay > 0:
            d_sp = (
                sta.zwischenspeicher + flu.aktgrundwasserneubildung
            ) * modelutils.exp(-1.0 / con.rechargedelay)
            flu.verzgrundwasserneubildung = (
                flu.aktgrundwasserneubildung + sta.zwischenspeicher - d_sp
            )
            sta.zwischenspeicher = d_sp
        else:
            flu.verzgrundwasserneubildung = (
                sta.zwischenspeicher + flu.aktgrundwasserneubildung
            )
            sta.zwischenspeicher = 0.0


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
        Calc_NiederschlagRichter_V1,
        Calc_MaxVerdunstung_V1,
        Calc_NiedNachInterz_V1,
        Calc_Interzeptionsspeicher_V1,
        Calc_Seeniederschlag_V1,
        Calc_Oberflaechenabfluss_V1,
        Calc_ZuflussBoden_V1,
        Calc_RelBodenfeuchte_V1,
        Calc_Sickerwasser_V1,
        Calc_Bodenverdunstung_V1,
        Corr_Bodenverdunstung_V1,
        Calc_Seeverdunstung_V1,
        Calc_AktVerdunstung_V1,
        Calc_PotKapilAufstieg_V1,
        Calc_KapilAufstieg_V1,
        Calc_AktBodenwassergehalt_V1,
        Calc_PotGrundwasserneubildung_V1,
        Calc_Basisabfluss_V1,
        Calc_AktGrundwasserneubildung_V1,
        Calc_VerzGrundwasserneubildung_Zwischenspeicher_V1,
    )
    ADD_METHODS = ()
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
        >>> derived.maxsoilwater(200.0)
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
        sel[landtype == SEALED] = False
        aetmodel.prepare_interception(sel)
        aetmodel.prepare_soil(sel)
        aetmodel.prepare_plant(sel)
        sel[:] = False
        sel[landtype == CONIFER] = True
        aetmodel.prepare_conifer(sel)
        sel[landtype == DECIDIOUS] = True
        aetmodel.prepare_tree(sel)

        aetmodel.prepare_maxsoilwater(derived.maxsoilwater.values)
