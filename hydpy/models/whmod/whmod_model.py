# -*- coding: utf-8 -*-
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
from hydpy.core import logtools
from hydpy.core import modeltools
from hydpy.cythons import modelutils

# ...from hland
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_control
from hydpy.models.whmod import whmod_derived
from hydpy.models.whmod import whmod_inputs
from hydpy.models.whmod import whmod_fluxes
from hydpy.models.whmod import whmod_states

if TYPE_CHECKING:
    from hydpy.core import timetools


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

    I:\\pgm-tgu\\info\\WHMOD_WeitereInfos\\01_Wissen\\29140414_BachalorArbeit_TUHH


    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(2)
    >>> nutz_nr(LAUBWALD, NADELWALD)
    >>> factorc(
    ...     laubwald=[0.0575, 0.1322, 0.1159, 0.1187, 0.9500, 1.1325,
    ...               1.0739, 1.0442, 1.0111, 0.1694, 0.0754, 0.0533],
    ...     nadelwald=[0.0604, 0.1592, 0.3090, 0.4273, 1.0310, 1.0340,
    ...                0.9596, 1.0112, 0.9000, 0.2838, 0.0910, 0.0608])

    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_niednachinterz_v1,
    ...     last_example=11,
    ...     parseqs=(fluxes.niederschlagrichter, fluxes.niednachinterz))

    >>> from hydpy import pub
    >>> pub.timegrids = "2001-09-01", "2001-11-01", "1d"
    >>> derived.moy.update()

    >>> model.idx_sim = pub.timegrids.init["2001-09-30"]
    >>> test.nexts.niederschlagrichter = range(0, 11, 1)
    >>> test()
    | ex. | niederschlagrichter |           niednachinterz |
    --------------------------------------------------------
    |   1 |                 0.0 |      0.0             0.0 |
    |   2 |                 1.0 |  0.31175        0.197321 |
    |   3 |                 2.0 | 0.915365        0.701972 |
    |   4 |                 3.0 | 1.638475        1.332452 |
    |   5 |                 4.0 | 2.427062        2.031877 |
    |   6 |                 5.0 | 3.257064        2.774913 |
    |   7 |                 6.0 | 4.115647        3.548044 |
    |   8 |                 7.0 | 4.995149        4.343203 |
    |   9 |                 8.0 | 5.890628        5.155185 |
    |  10 |                 9.0 |  6.79871        5.980438 |
    |  11 |                10.0 | 7.716989        6.816428 |

    >>> test.nexts.niederschlagrichter = range(0, 101, 10)
    >>> test()
    | ex. | niederschlagrichter |            niednachinterz |
    ---------------------------------------------------------
    |   1 |                 0.0 |       0.0             0.0 |
    |   2 |                10.0 |  7.716989        6.816428 |
    |   3 |                20.0 | 17.210705       15.503737 |
    |   4 |                30.0 | 26.965322       24.465771 |
    |   5 |                40.0 | 36.831417       33.545191 |
    |   6 |                50.0 | 46.759734       42.690131 |
    |   7 |                60.0 | 56.727827       51.876953 |
    |   8 |                70.0 | 66.723558       61.092879 |
    |   9 |                80.0 | 76.739617        70.33021 |
    |  10 |                90.0 | 86.771258       79.583949 |
    |  11 |               100.0 | 96.815225       88.850667 |

    >>> model.idx_sim = pub.timegrids.init["2001-10-01"]
    >>> test.nexts.niederschlagrichter = range(0, 11, 1)
    >>> test()
    | ex. | niederschlagrichter |         niednachinterz |
    ------------------------------------------------------
    |   1 |                 0.0 |    0.0             0.0 |
    |   2 |                 1.0 | 0.8306          0.7162 |
    |   3 |                 2.0 | 1.6612          1.4324 |
    |   4 |                 3.0 | 2.4918          2.1486 |
    |   5 |                 4.0 | 3.3224          2.8648 |
    |   6 |                 5.0 |  4.153           3.581 |
    |   7 |                 6.0 | 4.9836          4.2972 |
    |   8 |                 7.0 | 5.8142          5.0134 |
    |   9 |                 8.0 | 6.6448          5.7296 |
    |  10 |                 9.0 | 7.4754          6.4458 |
    |  11 |                10.0 |  8.306           7.162 |

    >>> test.nexts.niederschlagrichter = range(0, 101, 10)
    >>> test()
    | ex. | niederschlagrichter |         niednachinterz |
    ------------------------------------------------------
    |   1 |                 0.0 |    0.0             0.0 |
    |   2 |                10.0 |  8.306           7.162 |
    |   3 |                20.0 | 16.612          14.324 |
    |   4 |                30.0 | 24.918          21.486 |
    |   5 |                40.0 | 33.224          28.648 |
    |   6 |                50.0 |  41.53           35.81 |
    |   7 |                60.0 | 49.836          42.972 |
    |   8 |                70.0 | 58.142          50.134 |
    |   9 |                80.0 | 66.448          57.296 |
    |  10 |                90.0 | 74.754          64.458 |
    |  11 |               100.0 |  83.06           71.62 |

    >>> nmb_cells(3)
    >>> nutz_nr(GRAS, WASSER, VERSIEGELT)
    >>> model.idx_sim = 0
    >>> model.calc_niednachinterz_v1()
    >>> fluxes.niednachinterz
    niednachinterz(100.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.FactorC,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY,)
    REQUIREDSEQUENCES = (whmod_fluxes.NiederschlagRichter,)
    RESULTSEQUENCES = (whmod_fluxes.NiedNachInterz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        month = der.moy[model.idx_sim]
        summer = 4 <= month <= 8
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
                flu.niednachinterz[k] = 0.0
                continue
            if con.nutz_nr[k] == LAUBWALD:
                if summer:
                    d_loss = con.factorc[0, month] * (
                        1.0034 * modelutils.log(flu.niederschlagrichter + 1.0)
                        - 0.01481 * flu.niederschlagrichter
                    )
                else:
                    d_loss = con.factorc[0, month] * flu.niederschlagrichter
                flu.niednachinterz[k] = flu.niederschlagrichter - d_loss
            elif con.nutz_nr[k] == NADELWALD:
                if summer:
                    d_loss = con.factorc[1, month] * (
                        1.187 * modelutils.log(flu.niederschlagrichter + 1.0)
                        + 0.0691 * flu.niederschlagrichter
                    )
                else:
                    d_loss = con.factorc[1, month] * flu.niederschlagrichter
                flu.niednachinterz[k] = flu.niederschlagrichter - d_loss
            else:
                flu.niednachinterz[k] = flu.niederschlagrichter


class Calc_NiedNachInterz_V2(modeltools.Method):
    """Berechnung Bestandsniederschlag.

    Erst mal keine Interzeptionsverdunstung!!!

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(2)
    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_niednachinterz_v2,
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

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
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


class Calc_InterzeptionsVerdunstung_V1(modeltools.Method):
    """Berechne die Interzeptionsverdunstung (nachträglich).

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(4)
    >>> nutz_nr(GRAS, GRAS, VERSIEGELT, WASSER)
    >>> fluxes.niederschlagrichter = 3.0
    >>> fluxes.niednachinterz = 1.0, 2.0, 2.0, 2.0
    >>> model.calc_interzeptionsverdunstung_v1()
    >>> fluxes.interzeptionsverdunstung
    interzeptionsverdunstung(2.0, 1.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
    REQUIREDSEQUENCES = (
        whmod_fluxes.NiederschlagRichter,
        whmod_fluxes.NiedNachInterz,
    )
    RESULTSEQUENCES = (whmod_fluxes.InterzeptionsVerdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
                flu.interzeptionsverdunstung[k] = 0.0
            else:
                flu.interzeptionsverdunstung[k] = (
                    flu.niederschlagrichter - flu.niednachinterz[k]
                )


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
    REQUIREDSEQUENCES = (
        whmod_fluxes.NiederschlagRichter,
        whmod_fluxes.MaxVerdunstung,
    )
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


class Calc_Interzeptionsspeicher_V2(modeltools.Method):
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
    >>> model.calc_interzeptionsspeicher_v2()
    >>> states.interzeptionsspeicher
    interzeptionsspeicher(1.0, 2.0, 2.2, 2.0, 1.0, 0.0)
    >>> fluxes.niednachinterz
    niednachinterz(0.0, 0.0, 0.8, 0.0, 0.0, 0.0)
    >>> fluxes.interzeptionsverdunstung
    interzeptionsverdunstung(0.0, 0.0, 0.0, 1.0, 2.0, 3.0)

    >>> states.interzeptionsspeicher = 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
    >>> model.idx_sim = 2
    >>> model.calc_interzeptionsspeicher_v2()
    >>> states.interzeptionsspeicher
    interzeptionsspeicher(1.0, 2.0, 2.4, 2.0, 1.0, 0.0)
    >>> fluxes.niednachinterz
    niednachinterz(0.0, 0.0, 0.6, 0.0, 0.0, 0.0)
    >>> fluxes.interzeptionsverdunstung
    interzeptionsverdunstung(0.0, 0.0, 0.0, 1.0, 2.0, 3.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.MaxInterz,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY,)
    REQUIREDSEQUENCES = (
        whmod_fluxes.NiederschlagRichter,
        whmod_fluxes.MaxVerdunstung,
    )
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
                flu.interzeptionsverdunstung[k] = min(
                    sta.interzeptionsspeicher[k], flu.maxverdunstung[k]
                )
                sta.interzeptionsspeicher[k] -= flu.interzeptionsverdunstung[k]
                flu.niednachinterz[k] = max(
                    sta.interzeptionsspeicher[k] - d_maxinterz, 0.0
                )
                sta.interzeptionsspeicher[k] -= flu.niednachinterz[k]


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

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
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
    REQUIREDSEQUENCES = (
        whmod_inputs.Temp_TM,
        whmod_fluxes.NiedNachInterz,
    )
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
    >>> fluxes.relbodenfeuchte
    relbodenfeuchte(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
    DERIVEDPARAMETERS = (whmod_derived.nFKwe,)
    REQUIREDSEQUENCES = (whmod_states.AktBodenwassergehalt,)
    RESULTSEQUENCES = (whmod_fluxes.RelBodenfeuchte,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmb_cells):
            if (con.nutz_nr[k] in (WASSER, VERSIEGELT)) or (der.nfkwe[k] <= 0.0):
                flu.relbodenfeuchte[k] = 0.0
            else:
                flu.relbodenfeuchte[k] = sta.aktbodenwassergehalt[k] / der.nfkwe[k]


class Calc_Sickerwasser_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(9)
    >>> nutz_nr(GRAS, LAUBWALD, MAIS, NADELWALD, SOMMERWEIZEN, WINTERWEIZEN,
    ...         ZUCKERRUEBEN, VERSIEGELT, WASSER)
    >>> derived.beta(2.0)
    >>> fluxes.zuflussboden(10.0)
    >>> fluxes.relbodenfeuchte(0.5)
    >>> model.calc_sickerwasser_v1()
    >>> fluxes.sickerwasser
    sickerwasser(2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
    DERIVEDPARAMETERS = (whmod_derived.Beta,)
    REQUIREDSEQUENCES = (
        whmod_fluxes.ZuflussBoden,
        whmod_fluxes.RelBodenfeuchte,
    )
    RESULTSEQUENCES = (whmod_fluxes.Sickerwasser,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
                flu.sickerwasser[k] = 0.0
            else:
                flu.sickerwasser[k] = (
                    flu.zuflussboden[k] * flu.relbodenfeuchte[k] ** der.beta[k]
                )


class Calc_Saettigungsdampfdruckdefizit_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_saettigungsdampfdruckdefizit_v1,
    ...     last_example=6,
    ...     parseqs=(inputs.temp14,
    ...              inputs.relluftfeuchte,
    ...              fluxes.saettigungsdampfdruckdefizit))
    >>> test.nexts.temp14 = 0.0, 0.0, 0.0, 10.0, 20.0, 30.0
    >>> test.nexts.relluftfeuchte = 1.0, 0.5, 0.0, 0.0, 0.0, 0.0
    >>> test()
    | ex. | temp14 | relluftfeuchte | saettigungsdampfdruckdefizit |
    ----------------------------------------------------------------
    |   1 |    0.0 |            1.0 |                          0.0 |
    |   2 |    0.0 |            0.5 |                       3.0535 |
    |   3 |    0.0 |            0.0 |                        6.107 |
    |   4 |   10.0 |            0.0 |                    12.253137 |
    |   5 |   20.0 |            0.0 |                    23.292884 |
    |   6 |   30.0 |            0.0 |                     42.20658 |
    """

    REQUIREDSEQUENCES = (
        whmod_inputs.RelLuftfeuchte,
        whmod_inputs.Temp14,
    )
    RESULTSEQUENCES = (whmod_fluxes.Saettigungsdampfdruckdefizit,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.saettigungsdampfdruckdefizit = (1.0 - inp.relluftfeuchte) * (
            6.107 * 10.0 ** ((7.5 * inp.temp14) / (238.0 + inp.temp14))
        )


class Calc_MaxVerdunstung_V1(modeltools.Method):
    """Berechnung maximale/potenzielle Verdunstung.

    Haude-Ansatz (mit "Dommermuth-Trumpf"-Koeffizienten).

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(5)
    >>> nutz_nr(LAUBWALD, NADELWALD, GRAS, WASSER, VERSIEGELT)
    >>> faktor(
    ...     gras=[0.2, 0.21, 0.21, 0.29, 0.29, 0.28,
    ...           0.26, 0.25, 0.23, 0.22, 0.2, 0.2],
    ...     laubwald=[0.1, 0.22, 0.23, 0.3, 0.33, 0.35,
    ...               0.33, 0.3, 0.2, 0.1, 0.1, 0.1],
    ...     mais=[0.14, 0.14, 0.14, 0.14, 0.18, 0.26,
    ...           0.26, 0.26, 0.24, 0.21, 0.14, 0.14],
    ...     nadelwald=[0.1, 0.1, 0.1, 0.3, 0.39, 0.33,
    ...                0.31, 0.25, 0.25, 0.22, 0.1, 0.1],
    ...     sommerweizen=[0.14, 0.14, 0.18, 0.3, 0.38, 0.4,
    ...                   0.35, 0.15, 0.15, 0.14, 0.14, 0.14],
    ...     winterweizen=[0.18, 0.18, 0.19, 0.26, 0.34, 0.38,
    ...                   0.34, 0.22, 0.21, 0.2, 0.18, 0.18],
    ...     zuckerrueben=[0.14, 0.14, 0.14, 0.15, 0.23, 0.3,
    ...                   0.36, 0.32, 0.26, 0.19, 0.14, 0.14],
    ...     versiegelt=0.0,
    ...     wasser=[0.26, 0.26, 0.33, 0.39, 0.39, 0.37,
    ...             0.35, 0.33, 0.31, 0.26, 0.26, 0.26])
    >>> faktorwald(
    ...     laubwald=[0.01, 0, 0.04, 0.1, 0.23, 0.28,
    ...               0.32, 0.26, 0.17, 0.1, 0.01, 0],
    ...     nadelwald=[0.08, 0.04, 0.14, 0.35, 0.39, 0.34,
    ...                0.31, 0.25, 0.2, 0.13, 0.07, 0.05])

    >>> from hydpy import pub
    >>> pub.timegrids = "2001-06-29", "2001-07-03", "1d"
    >>> derived.moy.update()

    >>> from hydpy import UnitTest
    >>> test = UnitTest(
    ...     model, model.calc_maxverdunstung_v1,
    ...     last_example=5,
    ...     parseqs=(inputs.temp14,
    ...              fluxes.saettigungsdampfdruckdefizit,
    ...              fluxes.maxverdunstung))
    >>> test.nexts.temp14 = 0.0, 1.0, 10.0, 30.0, 30.0
    >>> test.nexts.saettigungsdampfdruckdefizit = 3.0, 3.0, 12.0, 20.0, 20.0

    >>> model.idx_sim = pub.timegrids.init["2001-06-30"]
    >>> test()
    | ex. | temp14 | saettigungsdampfdruckdefizit |                         maxverdunstung |
    ----------------------------------------------------------------------------------------
    |   1 |    0.0 |                          3.0 |  0.0   0.0   0.0   0.0             0.0 |
    |   2 |    1.0 |                          3.0 | 0.84  1.02  0.84  1.11             0.0 |
    |   3 |   10.0 |                         12.0 | 3.36  4.08  3.36  4.44             0.0 |
    |   4 |   30.0 |                         20.0 |  5.6   6.8   5.6   7.4             0.0 |
    |   5 |   30.0 |                         20.0 |  5.6   6.8   5.6   7.4             0.0 |

    >>> model.idx_sim = pub.timegrids.init["2001-07-01"]
    >>> test()
    | ex. | temp14 | saettigungsdampfdruckdefizit |                         maxverdunstung |
    ----------------------------------------------------------------------------------------
    |   1 |    0.0 |                          3.0 |  0.0   0.0   0.0   0.0             0.0 |
    |   2 |    1.0 |                          3.0 | 0.96  0.93  0.78  1.05             0.0 |
    |   3 |   10.0 |                         12.0 | 3.84  3.72  3.12   4.2             0.0 |
    |   4 |   30.0 |                         20.0 |  6.4   6.2   5.2   7.0             0.0 |
    |   5 |   30.0 |                         20.0 |  6.4   6.2   5.2   7.0             0.0 |
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
        whmod_control.FaktorWald,
        whmod_control.Faktor,
    )
    DERIVEDPARAMETERS = (whmod_derived.MOY,)
    REQUIREDSEQUENCES = (
        whmod_inputs.Temp14,
        whmod_fluxes.Saettigungsdampfdruckdefizit,
    )
    RESULTSEQUENCES = (whmod_fluxes.MaxVerdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if inp.temp14 <= 0.0:
            for k in range(con.nmb_cells):
                flu.maxverdunstung[k] = 0.0
        else:
            month = der.moy[model.idx_sim]
            for k in range(con.nmb_cells):
                nutz = con.nutz_nr[k]
                if nutz == LAUBWALD:
                    d_factor = con.faktorwald[0, month]
                elif nutz == NADELWALD:
                    d_factor = con.faktorwald[1, month]
                else:
                    d_factor = con.faktor[nutz - 1, month]
                flu.maxverdunstung[k] = d_factor * flu.saettigungsdampfdruckdefizit


class Calc_MaxVerdunstung_V2(modeltools.Method):
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
    >>> model.calc_maxverdunstung_v2()
    >>> fluxes.maxverdunstung
    maxverdunstung(6.135, 6.605, 5.28, 6.48, 0.0)

    >>> model.idx_sim = pub.timegrids.init["2001-07-01"]
    >>> model.calc_maxverdunstung_v2()
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
    >>> fluxes.relbodenfeuchte = 0.0, 0.25, 0.5, 0.75, 1.0, 0.5, 0.5
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
    REQUIREDSEQUENCES = (
        whmod_fluxes.RelBodenfeuchte,
        whmod_fluxes.MaxVerdunstung,
    )
    RESULTSEQUENCES = (whmod_fluxes.Bodenverdunstung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if con.nutz_nr[k] in (VERSIEGELT, WASSER):
                flu.bodenverdunstung[k] = 0.0
            else:
                d_temp = modelutils.exp(-con.minhasr[k] * flu.relbodenfeuchte[k])
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
    >>> fluxes.interzeptionsverdunstung[:5] + fluxes.bodenverdunstung[:5]
    array([ 1.  ,  1.25,  1.5 ,  1.75,  2.  ])

    >>> fluxes.interzeptionsverdunstung = 1.0
    >>> fluxes.bodenverdunstung = 0.0, 0.5, 1.0, 1.5, 2.0, 2.0, 2.0
    >>> model.corr_bodenverdunstung_v1()
    >>> fluxes.bodenverdunstung
    bodenverdunstung(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
    >>> fluxes.interzeptionsverdunstung[:5] + fluxes.bodenverdunstung[:5]
    array([ 1.  ,  1.25,  1.5 ,  1.75,  2.  ])
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
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

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
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
            if (con.nutz_nr[k] in (VERSIEGELT, WASSER)) or (
                not con.mitfunktion_kapillareraufstieg[k]
            ):
                flu.potkapilaufstieg[k] = 0.0
            else:
                d_schwell = con.kapilschwellwert[k]
                d_grenz = con.kapilgrenzwert[k]
                if con.flurab > (der.wurzeltiefe[k] + d_schwell):
                    flu.potkapilaufstieg[k] = 0.0
                elif con.flurab < (der.wurzeltiefe[k] + d_grenz):
                    flu.potkapilaufstieg[k] = 5.0
                else:
                    flu.potkapilaufstieg[k] = (
                        5.0
                        * (der.wurzeltiefe[k] + d_schwell - con.flurab)
                        / (d_schwell - d_grenz)
                    )


class Calc_KapilAufstieg_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(7)
    >>> nutz_nr(GRAS, GRAS, GRAS, GRAS, GRAS, VERSIEGELT, WASSER)
    >>> mitfunktion_kapillareraufstieg(True)
    >>> fluxes.relbodenfeuchte(0.0, 0.25, 0.5, 0.75, 1.0, 0.0, 0.0)
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
    REQUIREDSEQUENCES = (
        whmod_fluxes.PotKapilAufstieg,
        whmod_fluxes.RelBodenfeuchte,
    )
    RESULTSEQUENCES = (whmod_fluxes.KapilAufstieg,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmb_cells):
            if (con.nutz_nr[k] in (VERSIEGELT, WASSER)) or (
                not con.mitfunktion_kapillareraufstieg[k]
            ):
                flu.kapilaufstieg[k] = 0.0
            else:
                flu.kapilaufstieg[k] = (
                    flu.potkapilaufstieg[k] * (1.0 - flu.relbodenfeuchte[k]) ** 3
                )


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

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
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

    >>> from hydpy.models.whmod_v3 import *
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

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Nutz_Nr,
    )
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


class Calc_AktGrundwasserneubildung_V1(modeltools.Method):
    """

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(4)
    >>> area(14.0)
    >>> f_area(2.0, 3.0, 5.0, 4.0)
    >>> bfi(1.0, 0.5, 1.0, 0.5)
    >>> fluxes.potgrundwasserneubildung(2.0, 10.0, -2.0, -0.5)
    >>> model.calc_aktgrundwasserneubildung_v1()
    >>> fluxes.aktgrundwasserneubildung
    aktgrundwasserneubildung(0.5)
    """

    CONTROLPARAMETERS = (
        whmod_control.Nmb_Cells,
        whmod_control.Area,
        whmod_control.F_AREA,
        whmod_control.BFI,
    )
    REQUIREDSEQUENCES = (whmod_fluxes.PotGrundwasserneubildung,)
    RESULTSEQUENCES = (whmod_fluxes.AktGrundwasserneubildung,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.aktgrundwasserneubildung = 0.0
        for k in range(con.nmb_cells):
            if flu.potgrundwasserneubildung[k] > 0.0:
                flu.aktgrundwasserneubildung += (
                    con.f_area[k] * con.bfi[k] * flu.potgrundwasserneubildung[k]
                )
            else:
                flu.aktgrundwasserneubildung += (
                    con.f_area[k] * flu.potgrundwasserneubildung[k]
                )
        flu.aktgrundwasserneubildung /= con.area


class Calc_VerzGrundwasserneubildung_Zwischenspeicher_V1(modeltools.Method):
    """

    Nur eine Näherungslösung. Bei kleinen Flurabständen etwas zu geringe
    Verzögerung möglich, dafür immer bilanztreu.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> from numpy import arange
    >>> from hydpy import print_values
    >>> for k in numpy.arange(0., 5.5, .5):
    ...     schwerpunktlaufzeit.value = k
    ...     states.zwischenspeicher = 2.0
    ...     fluxes.aktgrundwasserneubildung = 1.0
    ...     model.calc_verzgrundwasserneubildung_zwischenspeicher_v1()
    ...     print_values(
    ...         [k,
    ...          fluxes.verzgrundwasserneubildung.value,
    ...          states.zwischenspeicher.value])
    0.0, 2.0, 0.0
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
            flu.verzgrundwasserneubildung = sta.zwischenspeicher
            sta.zwischenspeicher = 0.0


class Model(modeltools.AdHocModel):
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_NiederschlagRichter_V1,
        Calc_NiedNachInterz_V1,
        Calc_NiedNachInterz_V2,
        Calc_InterzeptionsVerdunstung_V1,
        Calc_Interzeptionsspeicher_V1,
        Calc_Interzeptionsspeicher_V2,
        Calc_Seeniederschlag_V1,
        Calc_Oberflaechenabfluss_V1,
        Calc_ZuflussBoden_V1,
        Calc_RelBodenfeuchte_V1,
        Calc_Sickerwasser_V1,
        Calc_Saettigungsdampfdruckdefizit_V1,
        Calc_MaxVerdunstung_V1,
        Calc_MaxVerdunstung_V2,
        Calc_Bodenverdunstung_V1,
        Corr_Bodenverdunstung_V1,
        Calc_Seeverdunstung_V1,
        Calc_AktVerdunstung_V1,
        Calc_PotKapilAufstieg_V1,
        Calc_KapilAufstieg_V1,
        Calc_AktBodenwassergehalt_V1,
        Calc_PotGrundwasserneubildung_V1,
        Calc_AktGrundwasserneubildung_V1,
        Calc_VerzGrundwasserneubildung_Zwischenspeicher_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


class Position(NamedTuple):
    """The row and column of a `WHMod` grid cell.

    Counting starts with 1.
    """

    row: int
    col: int

    @classmethod
    def from_sequence(cls, sequence: "Sequence") -> "Position":
        """Extract the grid cell position from the name of the |Element|
        object handling the given sequence."""
        _, row, col = sequence.subseqs.seqs.model.element.name.split("_")
        return cls(row=int(row), col=int(col))


class Positionbounds(NamedTuple):
    """The smallest and heighest row and column values of multiple `WHMod`
    grid cells."""

    rowmin: int
    rowmax: int
    colmin: int
    colmax: int

    @classmethod
    def from_sequences(cls, sequences: Iterable["Sequence"]) -> "Positionbounds":
        """Extract the grid cell position from the names of the |Element|
        objects handling the given sequences."""
        rowmin = numpy.inf
        rowmax = -numpy.inf
        colmin = numpy.inf
        colmax = -numpy.inf
        for sequence in sequences:
            row, col = Position.from_sequence(sequence)
            rowmin = min(rowmin, row)
            rowmax = max(rowmax, row)
            colmin = min(colmin, col)
            colmax = max(colmax, col)
        return Positionbounds(
            rowmin=rowmin,
            rowmax=rowmax,
            colmin=colmin,
            colmax=colmax,
        )


class WHModLoggerMixin:
    def __init__(
        self,
        firstdate: Optional["timetools.DateConstrArg"] = None,
        lastdate: Optional["timetools.DateConstrArg"] = None,
    ) -> None:
        super().__init__(firstdate=firstdate, lastdate=lastdate)
        self._positionbounds = None

    @abc.abstractmethod
    def _determine_positionbounds(self) -> Positionbounds:
        ...

    @property
    def positionbounds(self) -> Positionbounds:
        """The |PositionBounds| relevant for the logged sequences."""
        if self._positionbounds:
            return self._positionbounds
        return self._determine_positionbounds()

    @positionbounds.setter
    def positionbounds(self, positionbounds: Positionbounds) -> None:
        self._positionbounds = positionbounds

    @positionbounds.deleter
    def positionbounds(self) -> None:
        self._positionbounds = None

    def _dict2grid(
        self,
        sequence2value: Dict["Sequence", float],
        defaultvalue: float = 0.0,
    ) -> numpy.ndarray:
        pb = self.positionbounds
        shape = (pb.rowmax - pb.rowmin + 1, pb.colmax - pb.colmin + 1)
        grid = numpy.full(shape, defaultvalue, dtype=float)
        for sequence, value in sequence2value.items():
            position = Position.from_sequence(sequence)
            grid[position.row - pb.rowmin, position.col - pb.colmin] = value
        return grid

    @property
    def factor(self) -> float:
        """Factor for converting mm/stepsize to m/s (or m³/m²/s)."""
        return 1.0 / (1000.0 * hydpy.pub.timegrids.stepsize.seconds)

    def _write_rchfile(
        self,
        rchfile: TextIO,
        layer: int,
        balancefile: int,
        values_per_line: int,
        precision: int,
        exp_digits: int,
        sequence2values: Iterable[Dict["Sequence", float]],
    ) -> None:
        rchfile.write(
            f"{str(layer).rjust(10)}"
            f"{str(balancefile).rjust(10)}"
            f"         1         1\n"
        )
        positionbounds = self.positionbounds
        for sequence2value in sequence2values:
            nchars = precision + exp_digits + 5
            formatstring = f"({values_per_line}e{nchars}.{precision})".ljust(20)
            rchfile.write(
                f"         1         1         0         0\n"
                f"        18     1.000{formatstring}        -1     RECHARGE\n"
            )
            ncols = positionbounds.colmax - positionbounds.colmin + 1
            sections = numpy.arange(values_per_line, ncols, values_per_line)
            nchars = precision + exp_digits + 5
            grid = self.factor * self._dict2grid(sequence2value)
            for row in grid:
                for subarray in numpy.array_split(row, sections):
                    rchfile.write(
                        "".join(
                            numpy.format_float_scientific(
                                value,
                                unique=False,
                                precision=precision,
                                exp_digits=exp_digits,
                            ).rjust(nchars)
                            for value in subarray
                        )
                    )
                    rchfile.write("\n")


class WHModLogger(WHModLoggerMixin, logtools.Logger):
    """Specialisation of class |Logger| for `WHMod`."""

    def _determine_positionbounds(self) -> Positionbounds:
        return Positionbounds.from_sequences(self.sequence2sum.keys())

    def write_rchfile(
        self,
        rchfile: TextIO,
        layer: int = 1,
        balancefile: int = 51,
        values_per_line: int = 20,
        precision: int = 4,
        exp_digits: int = 3,
    ) -> None:
        """Write a recharge file (`.rch`)  for exporting groundwater recharge
        to ModFlow.

        See method |WHModMonthLogger.write_rchfile| of class |WHModMonthLogger|
        for further information
        """
        self._write_rchfile(
            rchfile=rchfile,
            layer=layer,
            balancefile=balancefile,
            values_per_line=values_per_line,
            precision=precision,
            exp_digits=exp_digits,
            sequence2values=[self.sequence2mean],
        )


class WHModMonthLogger(WHModLoggerMixin, logtools.MonthLogger):
    """Specialisation of class |MonthLogger| for `WHMod`."""

    def _determine_positionbounds(self) -> Positionbounds:
        sequence2value = tuple(self.month2sequence2sum.values())[0]
        return Positionbounds.from_sequences(sequence2value.keys())

    def write_rchfile(
        self,
        rchfile: TextIO,
        layer: int = 1,
        balancefile: int = 51,
        values_per_line: int = 20,
        precision: int = 4,
        exp_digits: int = 3,
    ) -> None:
        """Write a recharge file (`.rch`)  for exporting groundwater recharge
        to ModFlow.

        Using this functions only makes sense when logging
        |AktGrundwasserneubildung| sequences only.

        Header: Die 1 steht dafür, dass NB nur in Top layer angesetzt wird und
        die 51 ist eine ID für das Bilanzfile

        Subheader: Info darüber, ob neue Werte folgen oder die aus dem
        Schritt vorher genommen werden, Unit number, Faktor für alle Werte
        im Zeitschritt, Formatangabe…)
        Erste Zeile ist immer gleich, Format: Integer10, Integer 10,
        Integer 10, Integer 10
        Zweite Zeile ist auch immer gleich Format: Integer 10, float10.3
        (10 Stellen, davon 3 Nachkommastellen), A20 (20 charakters), Integer10
        In dieser Zeile bestimmst du mit „(10e12.3)“ das Format des folgenden
        Arrays (s.u.) mit NB-Werten, hier: max. 10 Werte in eine Zeile,
        das „e“ steht für Exponential-Schreibweise, ein Zahlenwert hat immer
        12 characters, 3 Nachkommastellen sind in den 12 Stellen berücksichtigt.
        Du kannst hier auch 20 Werte pro Zeile definieren und
        4 Nachkommastellen; es muss nur in der Kopfzeile definiert sein.
        Vorschlag: 4 Nachkommastellen
        """
        sequence2values = [s2m for (_, s2m) in sorted(self.month2sequence2mean.items())]
        self._write_rchfile(
            rchfile=rchfile,
            layer=layer,
            balancefile=balancefile,
            values_per_line=values_per_line,
            precision=precision,
            exp_digits=exp_digits,
            sequence2values=sequence2values,
        )
