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
    >>> nmb_cells(2)
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

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells,)
    REQUIREDSEQUENCES = (whmod_fluxes.NiederschlagRichter,)
    RESULTSEQUENCES = (whmod_fluxes.NiedNachInterz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            flu.niednachinterz[k] = flu.niederschlagrichter


class Calc_Seeniederschlag_V1(modeltools.Method):
    """Berechnung Niederschlag auf Wasserflächen.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(3)
    >>> nutz_nr(GRAS, VERSIEGELT, WASSER)
    >>> fluxes.niederschlagrichter = 2.0
    >>> model.calc_seeniederschlag_v1()
    >>> fluxes.seeniederschlag
    seeniederschlag(0.0, 0.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    REQUIREDSEQUENCES = (whmod_fluxes.NiederschlagRichter,)
    RESULTSEQUENCES = (whmod_fluxes.Seeniederschlag,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] == WASSER:
                flu.seeniederschlag[k] = flu.niederschlagrichter
            else:
                flu.seeniederschlag[k] = 0.0


class Calc_Interzeptionsspeicher_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(6)
    >>> nutz_nr(LAUBWALD)
    >>> maxinterz(gras=[0.4, 0.4, 0.6, 0.8, 1.0, 1.0,
    ...                 1.0, 1.0, 1.0, 0.6, 0.5, 0.4],
    ...           laubwald=[0.1, 0.1, 0.3, 0.8, 1.4, 2.2,
    ...                     2.4, 2.4, 2.2, 1.6, 0.3, 0.1],
    ...           mais=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                 0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           nadelwald=[2.2, 2.2, 2.2, 2.2, 2.2, 2.2,
    ...                      2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
    ...           sommerweizen=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                         0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           winterweizen=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                         0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           zuckerrueben=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
    ...                         0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
    ...           versiegelt=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ...                       2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
    ...           wasser=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
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
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
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
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] == WASSER:
                sta.interzeptionsspeicher[k] = 0.0
                flu.niednachinterz[k] = flu.niederschlagrichter
                flu.interzeptionsverdunstung[k] = 0.0
            else:
                d_maxinterz = con.maxinterz[con.nutz_nr[k] - 1, month]
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
    >>> nmb_cells(3)
    >>> nutz_nr(VERSIEGELT, WASSER, GRAS)
    >>> fluxes.niednachinterz = 3.0
    >>> model.calc_oberflaechenabfluss_v1()
    >>> fluxes.oberflaechenabfluss
    oberflaechenabfluss(3.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    REQUIREDSEQUENCES = (whmod_fluxes.NiedNachInterz,)
    RESULTSEQUENCES = (whmod_fluxes.Oberflaechenabfluss,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] == VERSIEGELT:
                flu.oberflaechenabfluss[k] = flu.niednachinterz[k]
            else:
                flu.oberflaechenabfluss[k] = 0.0


class Calc_ZuflussBoden_V1(modeltools.Method):
    """Berechnung Bestandsniederschlag.

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> simulationstep("1d")
    >>> nmb_cells(2)
    >>> nutz_nr(GRAS, GRAS)
    >>> gradfaktor(4.5)
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

    >>> nutz_nr(VERSIEGELT, WASSER)
    >>> states.schneespeicher = 5.0
    >>> fluxes.niednachinterz = 2.0
    >>> model.calc_zuflussboden_v1()
    >>> states.schneespeicher
    schneespeicher(0.0, 0.0)
    >>> fluxes.zuflussboden
    zuflussboden(0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.Gradfaktor,
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
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
                sta.schneespeicher[k] = 0.0
                flu.zuflussboden[k] = 0.0
            elif inp.temp_tm > 0.0:
                d_maxschneeschmelze = con.gradfaktor[k] * inp.temp_tm
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
    >>> nmb_cells(9)
    >>> nutz_nr(GRAS, LAUBWALD, MAIS, NADELWALD, SOMMERWEIZEN, WINTERWEIZEN,
    ...         ZUCKERRUEBEN, VERSIEGELT, WASSER)
    >>> derived.nfkwe(200.0)
    >>> states.aktbodenwassergehalt(100.0)
    >>> model.calc_relbodenfeuchte_v1()
    >>> factors.relbodenfeuchte
    relbodenfeuchte(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    DERIVEDPARAMETERS = (whmod_derived.nFKwe,)
    REQUIREDSEQUENCES = (whmod_states.AktBodenwassergehalt,)
    RESULTSEQUENCES = (whmod_factors.RelBodenfeuchte,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmb_cells):
            if (con.nutz_nr[k] in (WASSER, VERSIEGELT)) or (der.nfkwe[k] <= 0.0):
                fac.relbodenfeuchte[k] = 0.0
            else:
                fac.relbodenfeuchte[k] = sta.aktbodenwassergehalt[k] / der.nfkwe[k]


class Calc_Sickerwasser_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(9)
    >>> nutz_nr(GRAS, LAUBWALD, MAIS, NADELWALD, SOMMERWEIZEN, WINTERWEIZEN,
    ...         ZUCKERRUEBEN, VERSIEGELT, WASSER)
    >>> derived.beta(2.0)
    >>> fluxes.zuflussboden(10.0)
    >>> factors.relbodenfeuchte(0.5)
    >>> model.calc_sickerwasser_v1()
    >>> fluxes.sickerwasser
    sickerwasser(2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    DERIVEDPARAMETERS = (whmod_derived.Beta,)
    REQUIREDSEQUENCES = (whmod_fluxes.ZuflussBoden, whmod_factors.RelBodenfeuchte)
    RESULTSEQUENCES = (whmod_fluxes.Sickerwasser,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
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
    >>> nmb_cells(5)
    >>> nutz_nr(LAUBWALD, NADELWALD, GRAS, WASSER, VERSIEGELT)
    >>> fln(gras=[0.804, 0.927, 1.014, 1.041, 1.059, 1.056,
    ...           1.038, 0.999, 0.977, 0.965, 0.989, 0.927],
    ...     laubwald=[1.003, 1.003, 1.053, 1.179, 1.114, 1.227,
    ...               1.241, 1.241, 1.241, 1.139, 1.082, 1.003],
    ...     mais=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...           1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     nadelwald=[1.335, 1.335, 1.335, 1.335, 1.307, 1.321,
    ...                1.335, 1.335, 1.335, 1.335, 1.335, 1.335],
    ...     sommerweizen=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...                   1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     winterweizen=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...                   1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     zuckerrueben=[0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
    ...                   1.185, 1.151, 0.974, 0.853, 0.775, 0.733],
    ...     versiegelt=0.0,
    ...     wasser=[1.165, 1.217, 1.256, 1.283, 1.283, 1.296,
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
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
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
        for k in range(con.nmb_cells):
            flu.maxverdunstung[k] = con.fln[con.nutz_nr[k] - 1, month] * inp.et0


class Calc_Bodenverdunstung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(7)
    >>> nutz_nr(GRAS, GRAS, GRAS, GRAS, GRAS, VERSIEGELT, WASSER)
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
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.MinhasR,
    )
    REQUIREDSEQUENCES = (whmod_factors.RelBodenfeuchte, whmod_fluxes.MaxVerdunstung)
    RESULTSEQUENCES = (whmod_fluxes.Bodenverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
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
    >>> nmb_cells(7)
    >>> nutz_nr(GRAS, GRAS, GRAS, GRAS, GRAS, WASSER, VERSIEGELT)
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

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    REQUIREDSEQUENCES = (
        whmod_fluxes.MaxVerdunstung,
        whmod_fluxes.InterzeptionsVerdunstung,
    )
    UPDATEDSEQUENCES = (whmod_fluxes.Bodenverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
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
    >>> nmb_cells(3)
    >>> nutz_nr(GRAS, VERSIEGELT, WASSER)
    >>> fluxes.maxverdunstung = 2.0
    >>> model.calc_seeverdunstung_v1()
    >>> fluxes.seeverdunstung
    seeverdunstung(0.0, 0.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    REQUIREDSEQUENCES = (whmod_fluxes.MaxVerdunstung,)
    RESULTSEQUENCES = (whmod_fluxes.Seeverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] == WASSER:
                flu.seeverdunstung[k] = flu.maxverdunstung[k]
            else:
                flu.seeverdunstung[k] = 0.0


class Calc_AktVerdunstung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(2)
    >>> fluxes.interzeptionsverdunstung = 1.0, 0.0
    >>> fluxes.bodenverdunstung = 2.0, 0.0
    >>> fluxes.seeverdunstung = 0.0, 4.0
    >>> model.calc_aktverdunstung_v1()
    >>> fluxes.aktverdunstung
    aktverdunstung(3.0, 4.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells,)
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
        for k in range(con.nmb_cells):
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
    >>> nmb_cells(6)
    >>> nutz_nr(GRAS)
    >>> mitfunktion_kapillareraufstieg(True)
    >>> bodentyp(SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)
    >>> flurab(0.0)   # ToDo: shouldn't be necessary
    >>> kapilschwellwert(sand=0.8, sand_bindig=1.4, lehm=1.4,
    ...                  ton=1.35, schluff=1.75, torf=0.85)
    >>> kapilgrenzwert(sand=0.4, sand_bindig=0.85, lehm=0.45,
    ...                ton=0.25, schluff=0.75, torf=0.55)
    >>> derived.wurzeltiefe(0.0)

    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_potkapilaufstieg_v1,
    ...     last_example=31,
    ...     parseqs=(control.flurab,
    ...              fluxes.potkapilaufstieg))
    >>> import numpy
    >>> test.nexts.flurab = numpy.arange(0.0, 3.1, 0.1)
    >>> test()
    | ex. |                          flurab |                                           potkapilaufstieg |
    ------------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0     0.0 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   2 | 0.1  0.1  0.1  0.1  0.1     0.1 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   3 | 0.2  0.2  0.2  0.2  0.2     0.2 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   4 | 0.3  0.3  0.3  0.3  0.3     0.3 |  5.0       5.0       5.0  4.772727   5.0               5.0 |
    |   5 | 0.4  0.4  0.4  0.4  0.4     0.4 |  5.0       5.0       5.0  4.318182   5.0               5.0 |
    |   6 | 0.5  0.5  0.5  0.5  0.5     0.5 | 3.75       5.0  4.736842  3.863636   5.0               5.0 |
    |   7 | 0.6  0.6  0.6  0.6  0.6     0.6 |  2.5       5.0  4.210526  3.409091   5.0          4.166667 |
    |   8 | 0.7  0.7  0.7  0.7  0.7     0.7 | 1.25       5.0  3.684211  2.954545   5.0               2.5 |
    |   9 | 0.8  0.8  0.8  0.8  0.8     0.8 |  0.0       5.0  3.157895       2.5  4.75          0.833333 |
    |  10 | 0.9  0.9  0.9  0.9  0.9     0.9 |  0.0  4.545455  2.631579  2.045455  4.25               0.0 |
    |  11 | 1.0  1.0  1.0  1.0  1.0     1.0 |  0.0  3.636364  2.105263  1.590909  3.75               0.0 |
    |  12 | 1.1  1.1  1.1  1.1  1.1     1.1 |  0.0  2.727273  1.578947  1.136364  3.25               0.0 |
    |  13 | 1.2  1.2  1.2  1.2  1.2     1.2 |  0.0  1.818182  1.052632  0.681818  2.75               0.0 |
    |  14 | 1.3  1.3  1.3  1.3  1.3     1.3 |  0.0  0.909091  0.526316  0.227273  2.25               0.0 |
    |  15 | 1.4  1.4  1.4  1.4  1.4     1.4 |  0.0       0.0       0.0       0.0  1.75               0.0 |
    |  16 | 1.5  1.5  1.5  1.5  1.5     1.5 |  0.0       0.0       0.0       0.0  1.25               0.0 |
    |  17 | 1.6  1.6  1.6  1.6  1.6     1.6 |  0.0       0.0       0.0       0.0  0.75               0.0 |
    |  18 | 1.7  1.7  1.7  1.7  1.7     1.7 |  0.0       0.0       0.0       0.0  0.25               0.0 |
    |  19 | 1.8  1.8  1.8  1.8  1.8     1.8 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  20 | 1.9  1.9  1.9  1.9  1.9     1.9 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  21 | 2.0  2.0  2.0  2.0  2.0     2.0 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  22 | 2.1  2.1  2.1  2.1  2.1     2.1 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  23 | 2.2  2.2  2.2  2.2  2.2     2.2 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  24 | 2.3  2.3  2.3  2.3  2.3     2.3 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  25 | 2.4  2.4  2.4  2.4  2.4     2.4 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  26 | 2.5  2.5  2.5  2.5  2.5     2.5 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  27 | 2.6  2.6  2.6  2.6  2.6     2.6 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  28 | 2.7  2.7  2.7  2.7  2.7     2.7 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  29 | 2.8  2.8  2.8  2.8  2.8     2.8 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  30 | 2.9  2.9  2.9  2.9  2.9     2.9 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  31 | 3.0  3.0  3.0  3.0  3.0     3.0 |  0.0       0.0       0.0       0.0   0.0               0.0 |

    >>> derived.wurzeltiefe(1.0)
    >>> test()
    | ex. |                          flurab |                                           potkapilaufstieg |
    ------------------------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0     0.0 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   2 | 0.1  0.1  0.1  0.1  0.1     0.1 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   3 | 0.2  0.2  0.2  0.2  0.2     0.2 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   4 | 0.3  0.3  0.3  0.3  0.3     0.3 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   5 | 0.4  0.4  0.4  0.4  0.4     0.4 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   6 | 0.5  0.5  0.5  0.5  0.5     0.5 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   7 | 0.6  0.6  0.6  0.6  0.6     0.6 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   8 | 0.7  0.7  0.7  0.7  0.7     0.7 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |   9 | 0.8  0.8  0.8  0.8  0.8     0.8 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  10 | 0.9  0.9  0.9  0.9  0.9     0.9 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  11 | 1.0  1.0  1.0  1.0  1.0     1.0 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  12 | 1.1  1.1  1.1  1.1  1.1     1.1 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  13 | 1.2  1.2  1.2  1.2  1.2     1.2 |  5.0       5.0       5.0       5.0   5.0               5.0 |
    |  14 | 1.3  1.3  1.3  1.3  1.3     1.3 |  5.0       5.0       5.0  4.772727   5.0               5.0 |
    |  15 | 1.4  1.4  1.4  1.4  1.4     1.4 |  5.0       5.0       5.0  4.318182   5.0               5.0 |
    |  16 | 1.5  1.5  1.5  1.5  1.5     1.5 | 3.75       5.0  4.736842  3.863636   5.0               5.0 |
    |  17 | 1.6  1.6  1.6  1.6  1.6     1.6 |  2.5       5.0  4.210526  3.409091   5.0          4.166667 |
    |  18 | 1.7  1.7  1.7  1.7  1.7     1.7 | 1.25       5.0  3.684211  2.954545   5.0               2.5 |
    |  19 | 1.8  1.8  1.8  1.8  1.8     1.8 |  0.0       5.0  3.157895       2.5  4.75          0.833333 |
    |  20 | 1.9  1.9  1.9  1.9  1.9     1.9 |  0.0  4.545455  2.631579  2.045455  4.25               0.0 |
    |  21 | 2.0  2.0  2.0  2.0  2.0     2.0 |  0.0  3.636364  2.105263  1.590909  3.75               0.0 |
    |  22 | 2.1  2.1  2.1  2.1  2.1     2.1 |  0.0  2.727273  1.578947  1.136364  3.25               0.0 |
    |  23 | 2.2  2.2  2.2  2.2  2.2     2.2 |  0.0  1.818182  1.052632  0.681818  2.75               0.0 |
    |  24 | 2.3  2.3  2.3  2.3  2.3     2.3 |  0.0  0.909091  0.526316  0.227273  2.25               0.0 |
    |  25 | 2.4  2.4  2.4  2.4  2.4     2.4 |  0.0       0.0       0.0       0.0  1.75               0.0 |
    |  26 | 2.5  2.5  2.5  2.5  2.5     2.5 |  0.0       0.0       0.0       0.0  1.25               0.0 |
    |  27 | 2.6  2.6  2.6  2.6  2.6     2.6 |  0.0       0.0       0.0       0.0  0.75               0.0 |
    |  28 | 2.7  2.7  2.7  2.7  2.7     2.7 |  0.0       0.0       0.0       0.0  0.25               0.0 |
    |  29 | 2.8  2.8  2.8  2.8  2.8     2.8 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  30 | 2.9  2.9  2.9  2.9  2.9     2.9 |  0.0       0.0       0.0       0.0   0.0               0.0 |
    |  31 | 3.0  3.0  3.0  3.0  3.0     3.0 |  0.0       0.0       0.0       0.0   0.0               0.0 |

    >>> nutz_nr(VERSIEGELT)
    >>> test(last_example=1)
    | ex. |                          flurab |                          potkapilaufstieg |
    -------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0     0.0 | 0.0  0.0  0.0  0.0  0.0               0.0 |

    >>> nutz_nr(WASSER)
    >>> test(last_example=1)
    | ex. |                          flurab |                          potkapilaufstieg |
    -------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0     0.0 | 0.0  0.0  0.0  0.0  0.0               0.0 |

    >>> nutz_nr(GRAS)
    >>> mitfunktion_kapillareraufstieg(False)
    >>> test(last_example=1)
    | ex. |                          flurab |                          potkapilaufstieg |
    -------------------------------------------------------------------------------------
    |   1 | 0.0  0.0  0.0  0.0  0.0     0.0 | 0.0  0.0  0.0  0.0  0.0               0.0 |
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.MitFunktion_KapillarerAufstieg,
        whmod_control.KapilSchwellwert,
        whmod_control.KapilGrenzwert,
        whmod_control.Flurab,
    )
    DERIVEDPARAMETERS = (whmod_derived.Wurzeltiefe,)
    RESULTSEQUENCES = (whmod_fluxes.PotKapilAufstieg,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.mitfunktion_kapillareraufstieg and (
                con.nutz_nr[k] not in (VERSIEGELT, WASSER)
            ):
                d_schwell = con.kapilschwellwert[k]
                d_grenz = con.kapilgrenzwert[k]
                if con.flurab[k] > (der.wurzeltiefe[k] + d_schwell):
                    flu.potkapilaufstieg[k] = 0.0
                elif con.flurab[k] < (der.wurzeltiefe[k] + d_grenz):
                    flu.potkapilaufstieg[k] = 5.0
                else:
                    flu.potkapilaufstieg[k] = (
                        5.0
                        * (der.wurzeltiefe[k] + d_schwell - con.flurab[k])
                        / (d_schwell - d_grenz)
                    )
            else:
                flu.potkapilaufstieg[k] = 0.0


class Calc_KapilAufstieg_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(7)
    >>> nutz_nr(GRAS, GRAS, GRAS, GRAS, GRAS, VERSIEGELT, WASSER)
    >>> mitfunktion_kapillareraufstieg(True)
    >>> factors.relbodenfeuchte(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
    >>> fluxes.potkapilaufstieg(2.0)
    >>> model.calc_kapilaufstieg_v1()
    >>> fluxes.kapilaufstieg
    kapilaufstieg(2.0, 0.84375, 0.25, 0.03125, 0.0, 0.0, 0.0)

    >>> mitfunktion_kapillareraufstieg(False)
    >>> model.calc_kapilaufstieg_v1()
    >>> fluxes.kapilaufstieg
    kapilaufstieg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.MitFunktion_KapillarerAufstieg,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.PotKapilAufstieg, whmod_factors.RelBodenfeuchte)
    RESULTSEQUENCES = (whmod_fluxes.KapilAufstieg,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.mitfunktion_kapillareraufstieg and (
                con.nutz_nr[k] not in (VERSIEGELT, WASSER)
            ):
                flu.kapilaufstieg[k] = (
                    flu.potkapilaufstieg[k] * (1.0 - fac.relbodenfeuchte[k]) ** 3
                )
            else:
                flu.kapilaufstieg[k] = 0.0


class Calc_AktBodenwassergehalt_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(5)
    >>> nutz_nr(GRAS)
    >>> derived.nfkwe(100.0)
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

    >>> nutz_nr(WASSER, WASSER, WASSER, VERSIEGELT, VERSIEGELT)
    >>> fluxes.bodenverdunstung(0.0, 5.0, 10.0, 5.0, 5.0)
    >>> model.calc_aktbodenwassergehalt_v1()
    >>> states.aktbodenwassergehalt
    aktbodenwassergehalt(0.0, 0.0, 0.0, 0.0, 0.0)
    >>> fluxes.sickerwasser
    sickerwasser(4.0, 5.0, 5.0, 3.0, 3.0)
    >>> fluxes.kapilaufstieg
    kapilaufstieg(3.0, 3.0, 3.0, 4.0, 2.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
    DERIVEDPARAMETERS = (whmod_derived.nFKwe,)
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
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
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
                elif sta.aktbodenwassergehalt[k] > der.nfkwe[k]:
                    flu.kapilaufstieg[k] += der.nfkwe[k] - sta.aktbodenwassergehalt[k]
                    sta.aktbodenwassergehalt[k] = der.nfkwe[k]


class Calc_PotGrundwasserneubildung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(3)
    >>> nutz_nr(GRAS, VERSIEGELT, WASSER)
    >>> fluxes.sickerwasser(2.0)
    >>> fluxes.kapilaufstieg(1.0)
    >>> fluxes.seeniederschlag(7.0)
    >>> fluxes.seeverdunstung(4.0)
    >>> model.calc_potgrundwasserneubildung_v1()
    >>> fluxes.potgrundwasserneubildung
    potgrundwasserneubildung(1.0, 0.0, 3.0)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells, whmod_control.Nutz_Nr)
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
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] == WASSER:
                flu.potgrundwasserneubildung[k] = (
                    flu.seeniederschlag[k] - flu.seeverdunstung[k]
                )
            elif con.nutz_nr[k] == VERSIEGELT:
                flu.potgrundwasserneubildung[k] = 0.0
            else:
                flu.potgrundwasserneubildung[k] = (
                    flu.sickerwasser[k] - flu.kapilaufstieg[k]
                )


class Calc_Basisabfluss_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(4)
    >>> bfi(1.0, 0.8, 1.0, 0.8)
    >>> fluxes.potgrundwasserneubildung(1.0, 1.0, -1.0, -1.0)
    >>> model.calc_basisabfluss_v1()
    >>> fluxes.basisabfluss
    basisabfluss(0.0, 0.2, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.BFI,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.PotGrundwasserneubildung,)
    RESULTSEQUENCES = (whmod_fluxes.Basisabfluss,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] == VERSIEGELT:
                flu.basisabfluss[k] = 0.0
            else:
                flu.basisabfluss[k] = max(
                    (1.0 - con.bfi[k]) * flu.potgrundwasserneubildung[k], 0.0
                )


class Calc_AktGrundwasserneubildung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(4)
    >>> area(14.0)
    >>> f_area(2.0, 3.0, 5.0, 4.0)
    >>> derived.relarea.update()
    >>> fluxes.potgrundwasserneubildung = 2.0, 10.0, -2.0, -0.5
    >>> fluxes.basisabfluss = 0.0, 5.0, 0.0, 0.0
    >>> model.calc_aktgrundwasserneubildung_v1()
    >>> fluxes.aktgrundwasserneubildung
    aktgrundwasserneubildung(0.5)
    """

    CONTROLPARAMETERS = (whmod_control.Nmb_Cells,)
    DERIVEDPARAMETERS = (whmod_derived.RelArea,)
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
        for k in range(con.nmb_cells):
            flu.aktgrundwasserneubildung += der.relarea[k] * (
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
    ...     schwerpunktlaufzeit.value = k
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

    CONTROLPARAMETERS = (whmod_control.Schwerpunktlaufzeit,)
    REQUIREDSEQUENCES = (whmod_fluxes.AktGrundwasserneubildung,)
    UPDATEDSEQUENCES = (whmod_states.Zwischenspeicher,)
    RESULTSEQUENCES = (whmod_fluxes.VerzGrundwasserneubildung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if con.schwerpunktlaufzeit > 0:
            d_sp = (
                sta.zwischenspeicher + flu.aktgrundwasserneubildung
            ) * modelutils.exp(-1.0 / con.schwerpunktlaufzeit)
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
        landtype_refindices=whmod_control.Nutz_Nr,
        soiltype_constants=whmod_constants.SOIL_CONSTANTS,
        soiltype_refindices=whmod_control.BodenTyp,
        refweights=whmod_control.F_AREA,
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
        >>> nmb_cells(5)
        >>> area(10.0)
        >>> nutz_nr(GRAS, LAUBWALD, NADELWALD, WASSER, VERSIEGELT)
        >>> f_area(4.0, 1.0, 1.0, 1.0, 3.0)
        >>> derived.nfkwe(200.0)
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     nmbhru
        ...     area
        ...     water
        ...     interception
        ...     soil
        ...     dissefactor(gras=1.0, laubwald=2.0, default=3.0)
        ...     for method, arguments in model.preparemethod2arguments.items():
        ...         print(method, arguments[0][0], sep=": ")
        nmbhru(5)
        area(10.0)
        water(gras=False, laubwald=False, nadelwald=False, versiegelt=False,
              wasser=True)
        interception(gras=True, laubwald=True, nadelwald=True,
                     versiegelt=False, wasser=False)
        soil(gras=True, laubwald=True, nadelwald=True, versiegelt=False,
             wasser=False)
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
        dissefactor(gras=1.0, laubwald=2.0, nadelwald=3.0)
        >>> nutz_nr(LAUBWALD, GRAS, NADELWALD, WASSER, VERSIEGELT)
        >>> df
        dissefactor(gras=2.0, laubwald=1.0, nadelwald=3.0)
        >>> from hydpy import round_
        >>> round_(df.average_values())
        1.5
        """
        control = self.parameters.control
        derived = self.parameters.derived

        hydrotopes = control.nmb_cells.value
        landuse = control.nutz_nr.values

        aetmodel.prepare_nmbzones(hydrotopes)
        aetmodel.prepare_zonetypes(landuse)
        aetmodel.prepare_subareas(control.f_area.value)
        sel = numpy.full(hydrotopes, False, dtype=config.NP_BOOL)
        sel[landuse == WASSER] = True
        aetmodel.prepare_water(sel)
        sel = ~sel
        sel[landuse == VERSIEGELT] = False
        aetmodel.prepare_interception(sel)
        aetmodel.prepare_soil(sel)
        aetmodel.prepare_plant(sel)
        sel[:] = False
        sel[landuse == NADELWALD] = True
        aetmodel.prepare_conifer(sel)
        sel[landuse == LAUBWALD] = True
        aetmodel.prepare_tree(sel)

        aetmodel.prepare_maxsoilwater(derived.nfkwe.values)
