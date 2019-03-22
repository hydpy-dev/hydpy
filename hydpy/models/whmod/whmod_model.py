# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring
"""

>>> from hydpy import pub
>>> pub.options.reprdigits = 6
>>> pub.options.usecython = True

"""
# imports...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
# ...from hland
from hydpy.models.whmod.whmod_constants import *


def calc_niederschlagrichter_v1(self):
    """Niederschlagskorrektur nach Richter.

    Required control parameter:
      |KorrNiedNachRichter|

    Required input sequence:
      |Niederschlag|

    Calculated flux sequences:
      |NiederschlagRichter|

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> korrniednachrichter(False)
    >>> inputs.niederschlag = 5.0
    >>> model.calc_niederschlagrichter_v1()
    >>> fluxes.niederschlagrichter
    niederschlagrichter(5.0)

    >>> korrniednachrichter(True)
    Traceback (most recent call last):
    ...
    NotImplementedError: Richterkorrektur fehlt noch
    """
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.niederschlagrichter = inp.niederschlag


def calc_niednachinterz_v1(self):
    """Berechnung Bestandsniederschlag.

    I:\\pgm-tgu\\info\\WHMOD_WeitereInfos\\01_Wissen\\29140414_BachalorArbeit_TUHH

    Required control parameters:
      |InterzeptionNach_Dommermuth_Trampf|
      |Nmb_Cells|
      |Nutz_Nr|
      |FactorC|

    Required derived parameter:
       |MOY|

    Required flux sequence:
      |NiederschlagRichter|

    Calculated flux sequences:
      |NiedNachInterz|


    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> interzeptionnach_dommermuth_trampf(True)
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
    >>> pub.timegrids = '2001-09-01', '2001-11-01', '1d'
    >>> derived.moy.update()

    >>> model.idx_sim = pub.timegrids.init['2001-09-30']
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

    >>> model.idx_sim = pub.timegrids.init['2001-10-01']
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
    
    >>> interzeptionnach_dommermuth_trampf(False)
    Traceback (most recent call last):
    ...
    NotImplementedError: Bislang nur Dommermuth-Trampf möglich
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    month = der.moy[self.idx_sim]
    summer = 4 <= month <= 8
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] in (VERSIEGELT, WASSER):
            flu.niednachinterz[k] = 0.
            continue
        if con.nutz_nr[k] == LAUBWALD:
            if summer:
                d_loss = con.factorc[0, month] * (
                        1.0034 * modelutils.log(flu.niederschlagrichter + 1.0) -
                        0.01481 * flu.niederschlagrichter)
            else:
                d_loss = con.factorc[0, month] * flu.niederschlagrichter
            flu.niednachinterz[k] = flu.niederschlagrichter - d_loss
        elif con.nutz_nr[k] == NADELWALD:
            if summer:
                d_loss = con.factorc[1, month] * (
                        1.187 * modelutils.log(flu.niederschlagrichter + 1.0) +
                        0.0691 * flu.niederschlagrichter)
            else:
                d_loss = con.factorc[1, month] * flu.niederschlagrichter
            flu.niednachinterz[k] = flu.niederschlagrichter - d_loss
        else:
            flu.niednachinterz[k] = flu.niederschlagrichter


def calc_seeniederschlag_v1(self):
    """Berechnung Niederschlag auf Wasserflächen.

    Required control parameters:
      |Nutz_Nr|

    Required flux sequence:
      |NiederschlagRichter|

    Calculated flux sequences:
      |Seeniederschlag|


    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(3)
    >>> nutz_nr(GRAS, VERSIEGELT, WASSER)
    >>> fluxes.niederschlagrichter = 2.0
    >>> model.calc_seeniederschlag_v1()
    >>> fluxes.seeniederschlag
    seeniederschlag(0.0, 0.0, 2.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] == WASSER:
            flu.seeniederschlag[k] = flu.niederschlagrichter
        else:
            flu.seeniederschlag[k] = 0.


def calc_interzeptionsverdunstung_v1(self):
    """Berechne die Interzeptionsverdunstung (nachträglich).

    Required control parameters:
      |Nmb_Cells|

    Required flux sequences:
      |NiederschlagRichter|
      |NiedNachInterz|

    Calculated flux sequences:
      |InterzeptionsVerdunstung|

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> interzeptionnach_dommermuth_trampf(True)
    >>> nmb_cells(4)
    >>> nutz_nr(GRAS, GRAS, VERSIEGELT, WASSER)
    >>> fluxes.niederschlagrichter = 3.0
    >>> fluxes.niednachinterz = 1.0, 2.0, 2.0, 2.0
    >>> model.calc_interzeptionsverdunstung_v1()
    >>> fluxes.interzeptionsverdunstung
    interzeptionsverdunstung(2.0, 1.0, 0.0, 0.0)

    >>> interzeptionnach_dommermuth_trampf(False)
    Traceback (most recent call last):
    ...
    NotImplementedError: Bislang nur Dommermuth-Trampf möglich
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] in (VERSIEGELT, WASSER):
            flu.interzeptionsverdunstung[k] = 0.
        else:
            flu.interzeptionsverdunstung[k] = (
                    flu.niederschlagrichter - flu.niednachinterz[k])


def calc_oberflaechenabfluss_v1(self):
    """Berechnung Oberflaechenabfluss.

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(3)
    >>> nutz_nr(VERSIEGELT, WASSER, GRAS)
    >>> fluxes.niederschlagrichter = 3.0
    >>> model.calc_oberflaechenabfluss_v1()
    >>> fluxes.oberflaechenabfluss
    oberflaechenabfluss(3.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] == VERSIEGELT:
            flu.oberflaechenabfluss[k] = flu.niederschlagrichter
        else:
            flu.oberflaechenabfluss[k] = 0.


def calc_zuflussboden_v1(self):
    """Berechnung Bestandsniederschlag.

    Required control parameter:
      |Nmb_Cells|
      |Nutz_Nr|
      |Gradfaktor|

    Required input sequence:
      |Temp_TM|

    Required flux sequence:
      |NiedNachInterz|

    Updated state sequence:
      |Schneespeicher|

    Calculated flux sequences:
      |ZuflussBoden|

    >>> from hydpy.models.whmod import *
    >>> parameterstep('1d')
    >>> simulationstep('1d')
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
    con = self.parameters.control.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] in (VERSIEGELT, WASSER):
            sta.schneespeicher[k] = 0.0
            flu.zuflussboden[k] = 0.0
        elif inp.temp_tm > 0.:
            d_maxschneeschmelze = con.gradfaktor[k] * inp.temp_tm
            d_schneeschmelze = min(sta.schneespeicher[k], d_maxschneeschmelze)
            sta.schneespeicher[k] -= d_schneeschmelze
            flu.zuflussboden[k] = flu.niednachinterz[k] + d_schneeschmelze
        else:
            sta.schneespeicher[k] += flu.niednachinterz[k]
            flu.zuflussboden[k] = 0.


def calc_relbodenfeuchte_v1(self):
    """

    Required control parameters:
      |Nmb_Cells|
      |Nutz_Nr|

    Required state sequence:
      |AktBodenwassergehalt|

    Calculated flux sequences:
      |RelBodenfeuchte|

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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmb_cells):
        if ((con.nutz_nr[k] in (WASSER, VERSIEGELT)) or
                (der.nfkwe[k] <= 0.)):
            flu.relbodenfeuchte[k] = 0.
        else:
            flu.relbodenfeuchte[k] = sta.aktbodenwassergehalt[k]/der.nfkwe[k]


def calc_sickerwasser_v1(self):
    """

    Required control parameters:
      |Nmb_Cells|
      |Nutz_Nr|

    Required derived parameter:
      |Beta|

    Required flux sequence:
      |ZuflussBoden|
      |RelBodenfeuchte|

    Calculated flux sequences:
      |Sickerwasser|

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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] in (VERSIEGELT, WASSER):
            flu.sickerwasser[k] = 0.
        else:
            flu.sickerwasser[k] = \
                flu.zuflussboden[k] * flu.relbodenfeuchte[k]**der.beta[k]


def calc_saettigungsdampfdruckdefizit_v1(self):
    """

    Required input sequence:
      |Temp14|
      |RelLuftfeuchte|

    Calculated flux sequences:
      |Saettigungsdampfdruckdefizit|

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
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.saettigungsdampfdruckdefizit = (
        (1.-inp.relluftfeuchte) *
        (6.107*10.0**((7.5*inp.temp14)/(238.+inp.temp14))))


def calc_maxverdunstung_v1(self):
    """Berechnung maximale/potenzielle Verdunstung.

    Required control parameters:
      |InterzeptionNach_Dommermuth_Trampf|
      |Nmb_Cells|
      |Nutz_Nr|
      |FaktorWald|

    Required derived parameter:
       |MOY|

    Required input sequence:
      |Temp14|

    Required flux sequence:
      |Saettigungsdampfdruckdefizit|

    Calculated flux sequences:
      |MaxVerdunstung|


    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> interzeptionnach_dommermuth_trampf(True)
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
    >>> pub.timegrids = '2001-06-29', '2001-07-03', '1d'
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

    >>> model.idx_sim = pub.timegrids.init['2001-06-30']
    >>> test()
    | ex. | temp14 | saettigungsdampfdruckdefizit |                         maxverdunstung |
    ----------------------------------------------------------------------------------------
    |   1 |    0.0 |                          3.0 |  0.0   0.0   0.0   0.0             0.0 |
    |   2 |    1.0 |                          3.0 | 0.84  1.02  0.84  1.11             0.0 |
    |   3 |   10.0 |                         12.0 | 3.36  4.08  3.36  4.44             0.0 |
    |   4 |   30.0 |                         20.0 |  5.6   6.8   5.6   7.4             0.0 |
    |   5 |   30.0 |                         20.0 |  5.6   6.8   5.6   7.4             0.0 |

    >>> model.idx_sim = pub.timegrids.init['2001-07-01']
    >>> test()
    | ex. | temp14 | saettigungsdampfdruckdefizit |                         maxverdunstung |
    ----------------------------------------------------------------------------------------
    |   1 |    0.0 |                          3.0 |  0.0   0.0   0.0   0.0             0.0 |
    |   2 |    1.0 |                          3.0 | 0.96  0.93  0.78  1.05             0.0 |
    |   3 |   10.0 |                         12.0 | 3.84  3.72  3.12   4.2             0.0 |
    |   4 |   30.0 |                         20.0 |  6.4   6.2   5.2   7.0             0.0 |
    |   5 |   30.0 |                         20.0 |  6.4   6.2   5.2   7.0             0.0 |

    >>> interzeptionnach_dommermuth_trampf(False)
    Traceback (most recent call last):
    ...
    NotImplementedError: Bislang nur Dommermuth-Trampf möglich
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    inp = self.sequences.inputs.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if inp.temp14 <= 0.:
        for k in range(con.nmb_cells):
            flu.maxverdunstung[k] = 0.
    else:
        month = der.moy[self.idx_sim]
        for k in range(con.nmb_cells):
            nutz = con.nutz_nr[k]
            if nutz == LAUBWALD:
                d_factor = con.faktorwald[0, month]
            elif nutz == NADELWALD:
                d_factor = con.faktorwald[1, month]
            else:
                d_factor = con.faktor[nutz-1, month]
            flu.maxverdunstung[k] = d_factor * flu.saettigungsdampfdruckdefizit


def calc_bodenverdunstung_v1(self):
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
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] in (VERSIEGELT, WASSER):
            flu.bodenverdunstung[k] = 0.
        else:
            d_temp = modelutils.exp(-con.minhasr[k]*flu.relbodenfeuchte[k])
            flu.bodenverdunstung[k] = (
                flu.maxverdunstung[k] *
                (1.0-d_temp)/(1.-2.*modelutils.exp(-con.minhasr[k])+d_temp))


def calc_seeverdunstung_v1(self):
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
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] == WASSER:
            flu.seeverdunstung[k] = flu.maxverdunstung[k]
        else:
            flu.seeverdunstung[k] = 0.


def calc_aktverdunstung_v1(self):
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
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        flu.aktverdunstung[k] = (flu.interzeptionsverdunstung[k] +
                                 flu.bodenverdunstung[k] +
                                 flu.seeverdunstung[k])


def calc_potkapilaufstieg_v1(self):
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if ((con.nutz_nr[k] in (VERSIEGELT, WASSER)) or
                (not con.mitfunktion_kapillareraufstieg[k])):
            flu.potkapilaufstieg[k] = 0.
        else:
            d_schwell = con.kapilschwellwert[k]
            d_grenz = con.kapilgrenzwert[k]
            if con.flurab[k] > (der.wurzeltiefe[k] + d_schwell):
                flu.potkapilaufstieg[k] = 0.
            elif con.flurab[k] < (der.wurzeltiefe[k] + d_grenz):
                flu.potkapilaufstieg[k] = 5.
            else:
                flu.potkapilaufstieg[k] = (
                    5.*(der.wurzeltiefe[k]+d_schwell-con.flurab[k]) /
                    (d_schwell-d_grenz))


def calc_kapilaufstieg_v1(self):
    """
    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(5)
    >>> mitfunktion_kapillareraufstieg(True)
    >>> fluxes.relbodenfeuchte(0.0, 0.25, 0.5, 0.75, 1.0)
    >>> fluxes.potkapilaufstieg(2.0)
    >>> model.calc_kapilaufstieg_v1()
    >>> fluxes.kapilaufstieg
    kapilaufstieg(2.0, 0.84375, 0.25, 0.03125, 0.0)

    >>> mitfunktion_kapillareraufstieg(False)
    >>> model.calc_kapilaufstieg_v1()
    >>> fluxes.kapilaufstieg
    kapilaufstieg(0.0, 0.0, 0.0, 0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.mitfunktion_kapillareraufstieg[k]:
            flu.kapilaufstieg[k] = \
                flu.potkapilaufstieg[k]*(1.-flu.relbodenfeuchte[k])**3
        else:
            flu.kapilaufstieg[k] = 0.


def calc_aktbodenwassergehalt_v1(self):
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    sta = self.sequences.states.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] in (VERSIEGELT, WASSER):
            sta.aktbodenwassergehalt[k] = 0.
        else:
            sta.aktbodenwassergehalt[k] += (
                flu.zuflussboden[k] - flu.aktverdunstung[k] -
                flu.sickerwasser[k] + flu.kapilaufstieg[k])
            if sta.aktbodenwassergehalt[k] < 0.:
                # ToDo
                # flu.sickerwasser[k] += sta.aktbodenwassergehalt[k]
                sta.aktbodenwassergehalt[k] = 0.
            elif sta.aktbodenwassergehalt[k] > der.nfkwe[k]:
                # ToDo:
                # flu.kapilaufstieg[k] -= \
                #     der.nfkwe[k] - sta.aktbodenwassergehalt[k]
                sta.aktbodenwassergehalt[k] = der.nfkwe[k]


def calc_aktgrundwasserneubildung_v1(self):
    """
    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmb_cells(3)
    >>> nutz_nr(GRAS, VERSIEGELT, WASSER)
    >>> fluxes.sickerwasser(2.0)
    >>> fluxes.kapilaufstieg(1.0)
    >>> fluxes.seeniederschlag(7.0)
    >>> fluxes.seeverdunstung(4.0)
    >>> model.calc_aktgrundwasserneubildung_v1()
    >>> fluxes.aktgrundwasserneubildung
    aktgrundwasserneubildung(1.0, 0.0, 3.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for k in range(con.nmb_cells):
        if con.nutz_nr[k] == WASSER:
            flu.aktgrundwasserneubildung[k] = (
                flu.seeniederschlag[k] - flu.seeverdunstung[k])
        elif con.nutz_nr[k] == VERSIEGELT:
            flu.aktgrundwasserneubildung[k] = 0.
        else:
            flu.aktgrundwasserneubildung[k] = (
                flu.sickerwasser[k] - flu.kapilaufstieg[k])


class Model(modeltools.Model):
    RUN_METHODS = (calc_niederschlagrichter_v1,
                   calc_niednachinterz_v1,
                   calc_interzeptionsverdunstung_v1,
                   calc_seeniederschlag_v1,
                   calc_oberflaechenabfluss_v1,
                   calc_zuflussboden_v1,
                   calc_relbodenfeuchte_v1,
                   calc_sickerwasser_v1,
                   calc_saettigungsdampfdruckdefizit_v1,
                   calc_maxverdunstung_v1,
                   calc_bodenverdunstung_v1,
                   calc_seeverdunstung_v1,
                   calc_aktverdunstung_v1,
                   calc_potkapilaufstieg_v1,
                   calc_kapilaufstieg_v1,
                   calc_aktbodenwassergehalt_v1,
                   calc_aktgrundwasserneubildung_v1)
    OUTLET_METHODS = ()
