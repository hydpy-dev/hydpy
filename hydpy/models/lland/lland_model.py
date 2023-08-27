# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.auxs import roottools
from hydpy.cythons import modelutils
from hydpy.interfaces import aetinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import soilinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.interfaces import tempinterfaces

# ...from lland
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_derived
from hydpy.models.lland import lland_fixed
from hydpy.models.lland import lland_inlets
from hydpy.models.lland import lland_inputs
from hydpy.models.lland import lland_fluxes
from hydpy.models.lland import lland_states
from hydpy.models.lland import lland_logs
from hydpy.models.lland import lland_aides
from hydpy.models.lland import lland_outlets
from hydpy.models.lland import lland_constants
from hydpy.models.lland.lland_constants import (
    WASSER,
    FLUSS,
    SEE,
    VERS,
    LAUBW,
    MISCHW,
    NADELW,
)


class Pick_QZ_V1(modeltools.Method):
    r"""Query the current inflow from all inlet nodes.

    Basic equation:
      :math:`QZ = \sum Q_{inlets}`
    """

    REQUIREDSEQUENCES = (lland_inlets.Q,)
    RESULTSEQUENCES = (lland_fluxes.QZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.qz = 0.0
        for idx in range(inl.len_q):
            flu.qz += inl.q[idx][0]


class Calc_QZH_V1(modeltools.Method):
    """Calculate the inflow in mm.

    Basic equation:
       :math:`QZH = QZ / QFactor`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.qfactor(2.0)
        >>> fluxes.qz = 6.0
        >>> model.calc_qzh_v1()
        >>> fluxes.qzh
        qzh(3.0)
    """

    DERIVEDPARAMETERS = (lland_derived.QFactor,)
    REQUIREDSEQUENCES = (lland_fluxes.QZ,)
    RESULTSEQUENCES = (lland_fluxes.QZH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qzh = flu.qz / der.qfactor


class Update_LoggedSunshineDuration_V1(modeltools.Method):
    """Log the sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsunshineduration.shape = 3
        >>> logs.loggedsunshineduration = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedsunshineduration_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.sunshineduration,
        ...                          logs.loggedsunshineduration))
        >>> test.nexts.sunshineduration = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedsunshineduration
        >>> test()
        | ex. | sunshineduration |           loggedsunshineduration |
        -------------------------------------------------------------
        |   1 |              1.0 | 1.0  0.0                     0.0 |
        |   2 |              3.0 | 3.0  1.0                     0.0 |
        |   3 |              2.0 | 2.0  3.0                     1.0 |
        |   4 |              4.0 | 4.0  2.0                     3.0 |

    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_inputs.SunshineDuration,)
    UPDATEDSEQUENCES = (lland_logs.LoggedSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedsunshineduration[idx] = log.loggedsunshineduration[idx - 1]
        log.loggedsunshineduration[0] = inp.sunshineduration


class Calc_DailySunshineDuration_V1(modeltools.Method):
    """Calculate the sunshine duration sum of the last 24 hours.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsunshineduration.shape = 3
        >>> logs.loggedsunshineduration = 1.0, 5.0, 3.0
        >>> model.calc_dailysunshineduration_v1()
        >>> fluxes.dailysunshineduration
        dailysunshineduration(9.0)
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_logs.LoggedSunshineDuration,)
    UPDATEDSEQUENCES = (lland_fluxes.DailySunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.dailysunshineduration = 0.0
        for idx in range(der.nmblogentries):
            flu.dailysunshineduration += log.loggedsunshineduration[idx]


class Update_LoggedPossibleSunshineDuration_V1(modeltools.Method):
    """Log the sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedpossiblesunshineduration.shape = 3
        >>> logs.loggedpossiblesunshineduration = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedpossiblesunshineduration_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.possiblesunshineduration,
        ...                          logs.loggedpossiblesunshineduration))
        >>> test.nexts.possiblesunshineduration = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedpossiblesunshineduration
        >>> test()
        | ex. | possiblesunshineduration |           loggedpossiblesunshineduration |
        -----------------------------------------------------------------------------
        |   1 |                      1.0 | 1.0  0.0                             0.0 |
        |   2 |                      3.0 | 3.0  1.0                             0.0 |
        |   3 |                      2.0 | 2.0  3.0                             1.0 |
        |   4 |                      4.0 | 4.0  2.0                             3.0 |

    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_inputs.PossibleSunshineDuration,)
    UPDATEDSEQUENCES = (lland_logs.LoggedPossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedpossiblesunshineduration[
                idx
            ] = log.loggedpossiblesunshineduration[idx - 1]
        log.loggedpossiblesunshineduration[0] = inp.possiblesunshineduration


class Calc_DailyPossibleSunshineDuration_V1(modeltools.Method):
    """Calculate the sunshine duration sum of the last 24 hours.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedpossiblesunshineduration.shape = 3
        >>> logs.loggedpossiblesunshineduration = 1.0, 5.0, 3.0
        >>> model.calc_dailypossiblesunshineduration_v1()
        >>> fluxes.dailypossiblesunshineduration
        dailypossiblesunshineduration(9.0)
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_logs.LoggedPossibleSunshineDuration,)
    UPDATEDSEQUENCES = (lland_fluxes.DailyPossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailypossiblesunshineduration = 0.0
        for idx in range(der.nmblogentries):
            flu.dailypossiblesunshineduration += log.loggedpossiblesunshineduration[idx]


class Calc_NKor_V1(modeltools.Method):
    """Adjust the given precipitation value according to :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`NKor = KG \\cdot Nied`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> kg(0.8, 1.0, 1.2)
        >>> inputs.nied = 10.0
        >>> model.calc_nkor_v1()
        >>> fluxes.nkor
        nkor(8.0, 10.0, 12.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KG,
    )
    REQUIREDSEQUENCES = (lland_inputs.Nied,)
    RESULTSEQUENCES = (lland_fluxes.NKor,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.nkor[k] = con.kg[k] * inp.nied


class Calc_TKor_V1(modeltools.Method):
    """Adjust the given air temperature value.

    Basic equation:
      :math:`TKor = KT + TemL`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> kt(-2.0, 0.0, 2.0)
        >>> inputs.teml(1.0)
        >>> model.calc_tkor_v1()
        >>> fluxes.tkor
        tkor(-1.0, 1.0, 3.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KT,
    )
    REQUIREDSEQUENCES = (lland_inputs.TemL,)
    RESULTSEQUENCES = (lland_fluxes.TKor,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.tkor[k] = con.kt[k] + inp.teml


class Calc_WindSpeed2m_V1(modeltools.Method):
    r"""Adjust the measured wind speed to a height of 2 meters above the ground
    according to :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`WindSpeed2m = WindSpeed \cdot
      \frac{ln(newheight / Z0)}{ln(MeasuringHeightWindSpeed / Z0)}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed2m_v1()
        >>> fluxes.windspeed2m
        windspeed2m(4.007956)
    """

    CONTROLPARAMETERS = (lland_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (lland_fixed.Z0,)
    REQUIREDSEQUENCES = (lland_inputs.WindSpeed,)
    RESULTSEQUENCES = (lland_fluxes.WindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed2m = inp.windspeed * (
            modelutils.log(2.0 / fix.z0)
            / modelutils.log(con.measuringheightwindspeed / fix.z0)
        )


class Calc_ReducedWindSpeed2m_V1(modeltools.Method):
    """Calculate the landuse-use-specific wind speed at height of 2 meters
    according to :cite:t:`ref-LARSIM` (based on :cite:t:`ref-LUBW2006a`,
    :cite:t:`ref-LUBWLUWG2015`).


    Basic equation (for forests):
      :math:`ReducedWindSpeed2m = \
      max(P1Wind - P2Wind \\cdot LAI, 0) \\cdot WindSpeed2m`

    Example:

        The basic equation given above holds for forests (hydrological
        response units of type |LAUBW|, |MISCHW|, and |NADELW| only.
        For all other landuse-use types method |Calc_ReducedWindSpeed2m_V1|
        maintains the given wind speed for grass:

        >>> from hydpy import pub
        >>> pub.timegrids = "2019-05-30", "2019-06-03", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(OBSTB, LAUBW, MISCHW, NADELW)
        >>> lai.obstb_mai = 0.0
        >>> lai.laubw_mai = 2.0
        >>> lai.mischw_mai = 4.0
        >>> lai.nadelw_mai = 7.0
        >>> p1wind(0.5)
        >>> p2wind(0.1)
        >>> derived.moy.update()
        >>> fluxes.windspeed2m = 2.0
        >>> model.idx_sim = pub.timegrids.init["2019-05-31"]
        >>> model.calc_reducedwindspeed2m_v1()
        >>> fluxes.reducedwindspeed2m
        reducedwindspeed2m(2.0, 0.6, 0.2, 0.0)

        >>> lai.obstb_jun = 0.0
        >>> lai.laubw_jun = 3.0
        >>> lai.mischw_jun = 6.0
        >>> lai.nadelw_jun = 10.0
        >>> model.idx_sim = pub.timegrids.init["2019-06-01"]
        >>> model.calc_reducedwindspeed2m_v1()
        >>> fluxes.reducedwindspeed2m
        reducedwindspeed2m(2.0, 0.4, 0.0, 0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.LAI,
        lland_control.P1Wind,
        lland_control.P2Wind,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (lland_fluxes.WindSpeed2m,)
    RESULTSEQUENCES = (lland_fluxes.ReducedWindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                d_lai = con.lai[con.lnk[k] - 1, der.moy[model.idx_sim]]
                flu.reducedwindspeed2m[k] = (
                    max(con.p1wind - con.p2wind * d_lai, 0.0) * flu.windspeed2m
                )
            else:
                flu.reducedwindspeed2m[k] = flu.windspeed2m


class Update_EvI_WEvI_V1(modeltools.Method):
    r"""Delay the given interception evaporation and update the corresponding log
    sequence.

    Basic equation:
      :math:`EvI_{new} = WfEvI \cdot EvI_{old} + (1 - WfEvI) \cdot WEvI`

    Example:

        Prepare four hydrological response units with different combinations of delay
        factors and "old" interception evaporation values:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nhru(4)
        >>> wfevi(2.0, 2.0, 0.2, 0.2)
        >>> fluxes.evi = 1.6, 2.4, 1.6, 2.4

        Note that the actual value of the time-dependent parameter |WfEvI| is reduced
        due to the difference between the given parameter and simulation time steps:

        >>> from hydpy import round_
        >>> round_(wfevi.values)
        1.0, 1.0, 0.1, 0.1

        The evaporation value of the last simulation step is 2.0 mm:

        >>> logs.wevi = 2.0

        For the first two hydrological response units, the "old" |EvI| value is
        modified by -0.4 mm and +0.4 mm, respectively.  For the other two response
        units, which weigh the "new" evaporation value with 10 %, the new value of
        |EvI| deviates from |WEvI| by -0.04 mm and +0.04 mm only:

        >>> model.update_evi_wevi_v1()
        >>> fluxes.evi
        evi(1.6, 2.4, 1.96, 2.04)
        >>> logs.wevi
        wevi(1.6, 2.4, 1.96, 2.04)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.WfEvI,
    )
    UPDATEDSEQUENCES = (
        lland_fluxes.EvI,
        lland_logs.WEvI,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for k in range(con.nhru):
            flu.evi[k] = (
                con.wfevi[k] * flu.evi[k] + (1.0 - con.wfevi[k]) * log.wevi[0, k]
            )
            log.wevi[0, k] = flu.evi[k]


class Calc_NBes_Inzp_V1(modeltools.Method):
    r"""Calculate stand precipitation and update the interception storage accordingly.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      .. math::
        NBes = \begin{cases}
        PKor
        &|\
        Inzp = KInz
        \\
        0
        &|\
        Inzp < KInz
        \end{cases}

    Examples:

        Initialise five HRUs with different land usages:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> lnk(SIED_D, FEUCHT, GLETS, FLUSS, SEE)

        Define |KInz| values for July the selected land usages directly:

        >>> derived.kinz.sied_d_jul = 2.0
        >>> derived.kinz.feucht_jul = 1.0
        >>> derived.kinz.glets_jul = 0.0
        >>> derived.kinz.fluss_jul = 1.0
        >>> derived.kinz.see_jul = 1.0

        Now we prepare a |MOY| object, that assumes that the first, second,
        and third simulation time steps are in June, July, and August
        respectively (we make use of the value defined above for July, but
        setting the values of parameter |MOY| this way allows for a more
        rigorous testing of proper indexing):

        >>> derived.moy.shape = 3
        >>> derived.moy = 5, 6, 7
        >>> model.idx_sim = 1

        The dense settlement (|SIED_D|), the wetland area (|FEUCHT|), and
        both water areas (|FLUSS| and |SEE|) start with a initial interception
        storage of 1/2 mm, the glacier (|GLETS|) and water areas (|FLUSS| and
        |SEE|) start with 0 mm.  In the first example, actual precipition
        is 1 mm:

        >>> states.inzp = 0.5, 0.5, 0.0, 1.0, 1.0
        >>> fluxes.nkor = 1.0
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(1.5, 1.0, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.5, 1.0, 0.0, 0.0)

        Only for the settled area, interception capacity is not exceeded,
        meaning no stand precipitation occurs.  Note that it is common in
        define zero interception capacities for glacier areas, but not
        mandatory.  Also note that the |KInz|, |Inzp| and |NKor| values
        given for both water areas are ignored completely, and |Inzp|
        and |NBes| are simply set to zero.

        If there is no precipitation, there is of course also no stand
        precipitation and interception storage remains unchanged:

        >>> states.inzp = 0.5, 0.5, 0.0, 0.0, 0.0
        >>> fluxes.nkor = 0.
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(0.5, 0.5, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.0, 0.0, 0.0, 0.0)

        Interception capacities change discontinuously between consecutive
        months.  This can result in little stand precipitation events in
        periods without precipitation:

        >>> states.inzp = 1.0, 0.0, 0.0, 0.0, 0.0
        >>> derived.kinz.sied_d_jul = 0.6
        >>> fluxes.nkor = 0.0
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(0.6, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.4, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.KInz,
    )
    REQUIREDSEQUENCES = (lland_fluxes.NKor,)
    UPDATEDSEQUENCES = (lland_states.Inzp,)
    RESULTSEQUENCES = (lland_fluxes.NBes,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.nbes[k] = 0.0
                sta.inzp[k] = 0.0
            else:
                flu.nbes[k] = max(
                    flu.nkor[k]
                    + sta.inzp[k]
                    - der.kinz[con.lnk[k] - 1, der.moy[model.idx_sim]],
                    0.0,
                )
                sta.inzp[k] += flu.nkor[k] - flu.nbes[k]


class Calc_SNRatio_V1(modeltools.Method):
    """Calculate the ratio of frozen to total precipitation according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`SNRatio =
      min\\left(max\\left(\\frac{(TGr-TSp/2-TKor)}{TSp}, 0\\right), 1\\right)`

    Examples:

        In the first example, the threshold temperature of seven
        hydrological response units is 0 °C and the temperature interval
        of mixed precipitation 2 °C:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> tgr(1.0)
        >>> tsp(2.0)

        The value of |SNRatio| is zero above 0 °C and 1 below 2 °C.  Between
        these temperature values |SNRatio| decreases linearly:

        >>> fluxes.nkor = 4.0
        >>> fluxes.tkor = -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0
        >>> model.calc_snratio_v1()
        >>> aides.snratio
        snratio(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)

        Note the special case of a zero temperature interval.  With the
        actual temperature being equal to the threshold temperature, the
        the value of |SNRatio| is zero:

        >>> tsp(0.0)
        >>> model.calc_snratio_v1()
        >>> aides.snratio
        snratio(1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.TGr,
        lland_control.TSp,
    )
    REQUIREDSEQUENCES = (lland_fluxes.TKor,)
    RESULTSEQUENCES = (lland_aides.SNRatio,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if flu.tkor[k] >= (con.tgr[k] + con.tsp[k] / 2.0):
                aid.snratio[k] = 0.0
            elif flu.tkor[k] <= (con.tgr[k] - con.tsp[k] / 2.0):
                aid.snratio[k] = 1.0
            else:
                aid.snratio[k] = (
                    (con.tgr[k] + con.tsp[k] / 2.0) - flu.tkor[k]
                ) / con.tsp[k]


class Calc_SBes_V1(modeltools.Method):
    """Calculate the frozen part of stand precipitation.

    Basic equation:
      :math:`SBes = SNRatio \\cdot NBes`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(2)
        >>> fluxes.nbes = 10.0
        >>> aides.snratio = 0.2, 0.8
        >>> model.calc_sbes_v1()
        >>> fluxes.sbes
        sbes(2.0, 8.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_aides.SNRatio,
        lland_fluxes.NBes,
    )
    RESULTSEQUENCES = (lland_fluxes.SBes,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            flu.sbes[k] = aid.snratio[k] * flu.nbes[k]


class Calc_SnowIntMax_V1(modeltools.Method):
    r"""Calculate the current capacity of the snow interception storage according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      .. math::
        SnowIntMax = \bigg( P1SIMax +  P2SIMax \cdot LAI \bigg) \cdot \begin{cases}
        1 &|\ TKor  \leq -3
        \\
        (5 + TKor ) / 2 &|\ -3 < TKor < -1
        \\
        2 &|\ -1 \leq TKor
        \end{cases}

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-04-29", "2000-05-03", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(8)
        >>> lnk(ACKER, LAUBW, LAUBW, LAUBW, LAUBW, LAUBW, MISCHW, NADELW)
        >>> lai.laubw_apr = 4.0
        >>> lai.laubw_mai = 7.0
        >>> lai.mischw_apr = 6.0
        >>> lai.mischw_mai = 8.0
        >>> lai.nadelw = 11.0
        >>> p1simax(8.0)
        >>> p2simax(1.5)
        >>> derived.moy.update()
        >>> fluxes.tkor = 0.0, 0.0, -1.0, -2.0, -3.0, -4.0, -4.0, -4.0

        >>> model.idx_sim = pub.timegrids.init["2000-04-30"]
        >>> model.calc_snowintmax_v1()
        >>> fluxes.snowintmax
        snowintmax(0.0, 28.0, 28.0, 21.0, 14.0, 14.0, 17.0, 24.5)

        >>> model.idx_sim = pub.timegrids.init["2000-05-01"]
        >>> model.calc_snowintmax_v1()
        >>> fluxes.snowintmax
        snowintmax(0.0, 37.0, 37.0, 27.75, 18.5, 18.5, 20.0, 24.5)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.LAI,
        lland_control.P1SIMax,
        lland_control.P2SIMax,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (lland_fluxes.TKor,)
    RESULTSEQUENCES = (lland_fluxes.SnowIntMax,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        idx = der.moy[model.idx_sim]
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                d_lai = con.lai[con.lnk[k] - 1, idx]
                flu.snowintmax[k] = con.p1simax + con.p2simax * d_lai
                if flu.tkor[k] >= -1.0:
                    flu.snowintmax[k] *= 2
                elif flu.tkor[k] > -3.0:
                    flu.snowintmax[k] *= 2.5 + 0.5 * flu.tkor[k]
            else:
                flu.snowintmax[k] = 0.0


class Calc_SnowIntRate_V1(modeltools.Method):
    r"""Calculate the ratio between the snow interception rate and precipitation
    intensity according to :cite:t:`ref-LARSIM`.

    Basic equation:
       :math:`SnowIntRate = min\big(  P1SIRate +  P2SIRate \cdot LAI
       + P3SIRate \cdot SInz, 1 \big))`

    Example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-04-29", "2000-05-03", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(7)
        >>> lnk(ACKER, LAUBW, LAUBW, LAUBW, LAUBW, MISCHW, NADELW)
        >>> lai.laubw_apr = 4.0
        >>> lai.laubw_mai = 7.0
        >>> lai.mischw_apr = 6.0
        >>> lai.mischw_mai = 8.0
        >>> lai.nadelw = 11.0
        >>> p1sirate(0.2)
        >>> p2sirate(0.02)
        >>> p3sirate(0.003)
        >>> derived.moy.update()
        >>> states.sinz = 500.0, 500.0, 50.0, 5.0, 0.0, 0.0, 0.0

        >>> model.idx_sim = pub.timegrids.init["2000-04-30"]
        >>> model.calc_snowintrate_v1()
        >>> fluxes.snowintrate
        snowintrate(0.0, 1.0, 0.43, 0.295, 0.28, 0.32, 0.42)

        >>> model.idx_sim = pub.timegrids.init["2000-05-01"]
        >>> model.calc_snowintrate_v1()
        >>> fluxes.snowintrate
        snowintrate(0.0, 1.0, 0.49, 0.355, 0.34, 0.36, 0.42)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.LAI,
        lland_control.P1SIRate,
        lland_control.P2SIRate,
        lland_control.P3SIRate,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (lland_states.SInz,)
    RESULTSEQUENCES = (lland_fluxes.SnowIntRate,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        idx = der.moy[model.idx_sim]
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                d_lai = con.lai[con.lnk[k] - 1, idx]
                flu.snowintrate[k] = min(
                    con.p1sirate + con.p2sirate * d_lai + con.p3sirate * sta.sinz[k],
                    1.0,
                )
            else:
                flu.snowintrate[k] = 0.0


class Calc_NBesInz_V1(modeltools.Method):
    r"""Calculate the total amount of stand precipitation reaching the snow
    interception storage.

    Basic equation  (does this comply with `LARSIM`_?):
      :math:`NBesInz =
      min \big( SnowIntRate \cdot NBes, max (SnowIntMax - SInz, 0) \big)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER, LAUBW, MISCHW, NADELW, NADELW, NADELW)
        >>> states.sinz = 0.0, 0.0, 5.0, 10.0, 15.0, 20.0
        >>> fluxes.nbes = 20.0
        >>> fluxes.snowintmax = 15.0
        >>> fluxes.snowintrate = 0.5
        >>> model.calc_nbesinz_v1()
        >>> fluxes.nbesinz
        nbesinz(0.0, 10.0, 10.0, 5.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBes,
        lland_fluxes.SnowIntMax,
        lland_fluxes.SnowIntRate,
        lland_states.SInz,
    )
    RESULTSEQUENCES = (lland_fluxes.NBesInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                flu.nbesinz[k] = min(
                    flu.snowintrate[k] * flu.nbes[k],
                    max(flu.snowintmax[k] - sta.sinz[k], 0.0),
                )
            else:
                flu.nbesinz[k] = 0.0


class Calc_SBesInz_V1(modeltools.Method):
    r"""Calculate the frozen amount of stand precipitation reaching the snow
    interception storage.

    Basic equations (does this comply with `LARSIM`_?):
      :math:`SBesInz = SNRatio \cdot NBesInz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, MISCHW, NADELW)
        >>> fluxes.nbesinz = 10.0, 10.0, 5.0, 2.5
        >>> aides.snratio = 0.8
        >>> model.calc_sbesinz_v1()
        >>> fluxes.sbesinz
        sbesinz(0.0, 8.0, 4.0, 2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBesInz,
        lland_aides.SNRatio,
    )
    RESULTSEQUENCES = (lland_fluxes.SBesInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                flu.sbesinz[k] = aid.snratio[k] * flu.nbesinz[k]
            else:
                flu.sbesinz[k] = 0.0


class Calc_STInz_V1(modeltools.Method):
    r"""Add the relevant fraction of the frozen amount of stand precipitation
    to the frozen water equivalent of the interception snow storage.

    Basic equation:
      :math:`\frac{STInz}{dt} = SBesInz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, MISCHW, NADELW)
        >>> states.stinz = 0.0, 1.0, 2.0, 3.0
        >>> fluxes.sbesinz = 1.0
        >>> model.calc_stinz_v1()
        >>> states.stinz
        stinz(0.0, 2.0, 3.0, 4.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (lland_fluxes.SBesInz,)
    UPDATEDSEQUENCES = (lland_states.STInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                sta.stinz[k] += flu.sbesinz[k]
            else:
                sta.stinz[k] = 0.0


class Calc_WaDaInz_SInz_V1(modeltools.Method):
    r"""Add as much liquid precipitation to the snow interception storage as it is
    able to hold.

    Basic equations:
      :math:`\frac{dSInz}{dt} = NBesInz - WaDaInz`

      :math:`SInz \leq PWMax \cdot STInz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> lnk(ACKER, LAUBW, MISCHW, NADELW, NADELW)
        >>> pwmax(2.0)
        >>> fluxes.nbesinz = 1.0
        >>> states.stinz = 0.0, 0.0, 1.0, 1.0, 1.0
        >>> states.sinz = 1.0, 0.0, 1.0, 1.5, 2.0
        >>> model.calc_wadainz_sinz_v1()
        >>> states.sinz
        sinz(0.0, 0.0, 2.0, 2.0, 2.0)
        >>> fluxes.wadainz
        wadainz(0.0, 1.0, 0.0, 0.5, 1.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBesInz,
        lland_states.STInz,
    )
    UPDATEDSEQUENCES = (lland_states.SInz,)
    RESULTSEQUENCES = (lland_fluxes.WaDaInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                sta.sinz[k] += flu.nbesinz[k]
                flu.wadainz[k] = max(sta.sinz[k] - con.pwmax[k] * sta.stinz[k], 0.0)
                sta.sinz[k] -= flu.wadainz[k]
            else:
                flu.wadainz[k] = 0.0
                sta.sinz[k] = 0.0


class Calc_WNiedInz_ESnowInz_V1(modeltools.Method):
    r"""Calculate the heat flux into the snow interception storage due to the amount
    of precipitation actually hold by the snow layer.

    Basic equation:
      :math:`\frac{dESnowInz}{dt} = W\!NiedInz`

      :math:`W\!NiedInz = (TKor-TRefN) \cdot
      (CPEis \cdot SBesInz + CPWasser \cdot (NBesInz - SBesInz - WaDaInz))`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(LAUBW, MISCHW, NADELW, NADELW, NADELW, ACKER)
        >>> trefn(1.0)
        >>> states.esnowinz = 0.5
        >>> fluxes.tkor = 4.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> fluxes.nbesinz = 10.0
        >>> fluxes.sbesinz = 0.0, 0.0, 5.0, 10.0, 5.0, 5.0
        >>> fluxes.wadainz = 0.0, 0.0, 0.0, 0.0, 5.0, 5.0
        >>> model.calc_wniedinz_esnowinz_v1()
        >>> fluxes.wniedinz
        wniedinz(2.9075, -0.969167, -0.726481, -0.483796, -0.241898, 0.0)
        >>> states.esnowinz
        esnowinz(3.4075, -0.469167, -0.226481, 0.016204, 0.258102, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.TRefN,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.NBesInz,
        lland_fluxes.SBesInz,
        lland_fluxes.WaDaInz,
    )
    UPDATEDSEQUENCES = (lland_states.ESnowInz,)
    RESULTSEQUENCES = (lland_fluxes.WNiedInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                d_ice = fix.cpeis * flu.sbesinz[k]
                d_water = fix.cpwasser * (
                    flu.nbesinz[k] - flu.sbesinz[k] - flu.wadainz[k]
                )
                flu.wniedinz[k] = (flu.tkor[k] - con.trefn[k]) * (d_ice + d_water)
                sta.esnowinz[k] += flu.wniedinz[k]
            else:
                flu.wniedinz[k] = 0.0
                sta.esnowinz[k] = 0.0


class Return_TempSInz_V1(modeltools.Method):
    r"""Calculate and return the average temperature of the intercepted snow.

    Basic equation:
      :math:`max \left( \frac{ESnowInz}{STInz \cdot CPEis + (SInz - STInz)
      \cdot CPWasser}, -273 \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> states.stinz = 0.0, 0.5, 5.0, 0.5, 0.5
        >>> states.sinz = 0.0, 1.0, 10.0, 1.0, 1.0
        >>> states.esnowinz = 0.0, 0.0, -1.0, -10.0, -100.0
        >>> from hydpy import round_
        >>> round_(model.return_tempsinz_v1(0))
        nan
        >>> round_(model.return_tempsinz_v1(1))
        0.0
        >>> round_(model.return_tempsinz_v1(2))
        -1.376498
        >>> round_(model.return_tempsinz_v1(3))
        -137.649758
        >>> round_(model.return_tempsinz_v1(4))
        -273.0
    """

    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_states.STInz,
        lland_states.SInz,
        lland_states.ESnowInz,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.sinz[k] > 0.0:
            d_ice = fix.cpeis * sta.stinz[k]
            d_water = fix.cpwasser * (sta.sinz[k] - sta.stinz[k])
            return max(sta.esnowinz[k] / (d_ice + d_water), -273.0)
        return modelutils.nan


class Calc_TempSInz_V1(modeltools.Method):
    """Calculate the average temperature of the intercepted snow.

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER, LAUBW, MISCHW, NADELW, NADELW, NADELW)
        >>> pwmax(2.0)
        >>> fluxes.tkor = -1.0
        >>> states.stinz = 0.0, 0.5, 5.0, 5.0, 5.0, 5.0
        >>> states.sinz = 0.0, 1.0, 10.0, 10.0, 10.0, 10.0
        >>> states.esnowinz = 0.0, 0.0, -2.0, -2.0, -2.0, -2.0
        >>> model.calc_tempsinz_v1()
        >>> aides.tempsinz
        tempsinz(nan, 0.0, -2.752995, -2.752995, -2.752995, -2.752995)
    """

    SUBMETHODS = (Return_TempSInz_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_states.STInz,
        lland_states.SInz,
        lland_states.ESnowInz,
    )
    RESULTSEQUENCES = (lland_aides.TempSInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            aid.tempsinz[k] = model.return_tempsinz_v1(k)


class Update_ASInz_V1(modeltools.Method):
    r"""Calculate the dimensionless age of the intercepted snow.

    Basic equations:
      :math:`TauSInz_{new} = TauSInz_{old} \cdot max(1 - 0.1 \cdot SBesInz), 0) +
      \frac{r_1+r_2+r_3}{10^6} \cdot Seconds`

      :math:`r_1 = exp \left( 5000 \cdot
      \left( \frac{1}{273.15} - \frac{1}{273.15 + TempSInz} \right) \right)`

      :math:`r_2 = min \left(r_1^{10}, 1 \right)`

      :math:`r_3 = 0.03`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(10)
        >>> derived.seconds(24*60*60)
        >>> fluxes.sbesinz = 0.0, 1.0, 5.0, 9.0, 10.0, 11.0, 11.0, 11.0, 11.0, 11.0
        >>> states.sinz = 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        >>> states.asinz = 1.0, nan, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        >>> aides.tempsinz = 0.0, 0.0, -10.0, -10.0, -10.0, -10.0, -1.0, 0.0, 1.0, 10.0
        >>> model.update_asinz_v1()
        >>> states.asinz
        asinz(nan, 0.175392, 0.545768, 0.145768, 0.045768, 0.045768, 0.127468,
              0.175392, 0.181358, 0.253912)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    DERIVEDPARAMETERS = (lland_derived.Seconds,)
    REQUIREDSEQUENCES = (
        lland_fluxes.SBesInz,
        lland_states.SInz,
        lland_aides.TempSInz,
    )
    RESULTSEQUENCES = (lland_states.ASInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if sta.sinz[k] > 0:
                if modelutils.isnan(sta.asinz[k]):
                    sta.asinz[k] = 0.0
                d_r1 = modelutils.exp(
                    5000.0 * (1 / 273.15 - 1.0 / (273.15 + aid.tempsinz[k]))
                )
                d_r2 = min(d_r1**10, 1.0)
                sta.asinz[k] *= max(1 - 0.1 * flu.sbesinz[k], 0.0)
                sta.asinz[k] += (d_r1 + d_r2 + 0.03) / 1e6 * der.seconds
            else:
                sta.asinz[k] = modelutils.nan


class Calc_ActualAlbedoInz_V1(modeltools.Method):
    r"""Calculate the current albedo of the intercepted snow.

    Basic equation:
      :math:`AlbedoSnowInz = Albedo0Snow \cdot
      \left( 1 - SnowAgingFactor \cdot \frac{ASInz}{1 + ASInz} \right)`

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(5)
        >>> albedo0snow(0.8)
        >>> snowagingfactor(0.35)
        >>> states.asinz = nan, nan, 0.0, 1.0, 3.0
        >>> states.sinz = 0.0, 0.0, 1.0, 1.0, 1.0
        >>> model.calc_actualalbedoinz_v1()
        >>> fluxes.actualalbedoinz
        actualalbedoinz(nan, nan, 0.8, 0.66, 0.59)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.SnowAgingFactor,
        lland_control.Albedo0Snow,
    )
    REQUIREDSEQUENCES = (
        lland_states.ASInz,
        lland_states.SInz,
    )
    RESULTSEQUENCES = (lland_fluxes.ActualAlbedoInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.sinz[k] > 0.0:
                flu.actualalbedoinz[k] = con.albedo0snow * (
                    1.0 - con.snowagingfactor * sta.asinz[k] / (1.0 + sta.asinz[k])
                )
            else:
                flu.actualalbedoinz[k] = modelutils.nan


class Calc_NetShortwaveRadiationInz_V1(modeltools.Method):
    r"""Calculate the net shortwave radiation for the intercepted snow.

    Basic equation:
      :math:`NetShortwaveRadiationInz =
      (1 - Fr) \cdot (1.0 - ActualAlbedoInz) \cdot AdjustedGlobalRadiation`

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)
        >>> derived.fr.acker_jan = 1.0
        >>> derived.fr.acker_feb = 1.0
        >>> derived.fr.laubw_jan = 0.5
        >>> derived.fr.laubw_feb = 0.1
        >>> derived.moy.update()
        >>> inputs.globalradiation = 40.0
        >>> fluxes.actualalbedoinz = 0.5

        >>> model.idx_sim = pub.timegrids.init["2000-01-31"]
        >>> model.calc_netshortwaveradiationinz_v1()
        >>> fluxes.netshortwaveradiationinz
        netshortwaveradiationinz(0.0, 10.0)

        >>> model.idx_sim = pub.timegrids.init["2000-02-01"]
        >>> model.calc_netshortwaveradiationinz_v1()
        >>> fluxes.netshortwaveradiationinz
        netshortwaveradiationinz(0.0, 18.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Fr,
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.GlobalRadiation,
        lland_fluxes.ActualAlbedoInz,
    )
    RESULTSEQUENCES = (lland_fluxes.NetShortwaveRadiationInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                flu.netshortwaveradiationinz[k] = (
                    (1.0 - der.fr[con.lnk[k] - 1, der.moy[model.idx_sim]])
                    * (1.0 - flu.actualalbedoinz[k])
                    * inp.globalradiation
                )
            else:
                flu.netshortwaveradiationinz[k] = 0.0


class Calc_SchmPotInz_V1(modeltools.Method):
    r"""Calculate the potential melt of the intercepted snow according to its heat
    content.

    Basic equation:
      :math:`SchmPotInz = max \left( \frac{ESnowInz}{RSchmelz}, 0 \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(4)
        >>> states.sinz = 0.0, 1.0, 1.0, 1.0
        >>> states.esnowinz = nan, 10.0, 5.0, -5.0
        >>> model.calc_schmpotinz_v1()
        >>> fluxes.schmpotinz
        schmpotinz(0.0, 1.293413, 0.646707, 0.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_states.ESnowInz,
        lland_states.SInz,
    )
    RESULTSEQUENCES = (lland_fluxes.SchmPotInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.sinz[k] > 0.0:
                flu.schmpotinz[k] = max(sta.esnowinz[k] / fix.rschmelz, 0.0)
            else:
                flu.schmpotinz[k] = 0.0


class Calc_SchmInz_STInz_V1(modeltools.Method):
    r"""Calculate the actual amount of snow melting within the snow interception
    storage.

    Basic equations:

      :math:`\frac{dSTInz}{dt} = -SchmInz`

      .. math::
        SchmInz = \begin{cases}
        SchmPotInz &|\ STInz> 0
        \\
        0 &|\ STInz = 0
        \end{cases}

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(ACKER, LAUBW, MISCHW, NADELW, NADELW, NADELW)
        >>> states.stinz = 0.0, 0.0, 2.0, 2.0, 2.0, 2.0
        >>> fluxes.schmpotinz = 1.0, 1.0, 0.0, 1.0, 3.0, 5.0
        >>> model.calc_schminz_stinz_v1()
        >>> states.stinz
        stinz(0.0, 0.0, 2.0, 1.0, 0.0, 0.0)
        >>> fluxes.schminz
        schminz(0.0, 0.0, 0.0, 1.0, 2.0, 2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (lland_fluxes.SchmPotInz,)
    RESULTSEQUENCES = (lland_fluxes.SchmInz,)
    UPDATEDSEQUENCES = (lland_states.STInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                flu.schminz[k] = min(flu.schmpotinz[k], sta.stinz[k])
                sta.stinz[k] -= flu.schminz[k]
            else:
                flu.schminz[k] = 0.0


class Calc_GefrPotInz_V1(modeltools.Method):
    r"""Calculate the potential refreezing within the snow interception storage
    according to its thermal energy.

    Basic equation:
      :math:`GefrPotInz = max \left( -\frac{ESnowInz}{RSchmelz}, 0 \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(4)
        >>> states.sinz = 0.0, 1.0, 1.0, 1.0
        >>> states.esnowinz = nan, -10.0, -5.0, 5.0
        >>> model.calc_gefrpotinz_v1()
        >>> fluxes.gefrpotinz
        gefrpotinz(0.0, 1.293413, 0.646707, 0.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_states.ESnowInz,
        lland_states.SInz,
    )
    RESULTSEQUENCES = (lland_fluxes.GefrPotInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.sinz[k] > 0:
                flu.gefrpotinz[k] = max(-sta.esnowinz[k] / fix.rschmelz, 0)
            else:
                flu.gefrpotinz[k] = 0.0


class Calc_GefrInz_STInz_V1(modeltools.Method):
    r"""Calculate the actual amount of snow melting within the snow interception
    storage.

    Basic equations:
      :math:`\frac{dGefrInz}{dt} = -GefrInz`

      .. math::
        GefrInz = \begin{cases}
        GefrPotInz &|\ SInz - STInz > 0
        \\
        0 &|\ SInz - STInz = 0
        \end{cases}

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(ACKER, LAUBW, LAUBW, LAUBW, MISCHW, NADELW)
        >>> refreezeflag(True)
        >>> states.stinz = 0.0, 0.0, 2.0, 2.0, 2.0, 2.0
        >>> states.sinz = 0.0, 0.0, 4.0, 4.0, 4.0, 4.0
        >>> fluxes.gefrpotinz = 1.0, 1.0, 0.0, 1.0, 3.0, 5.0
        >>> model.calc_gefrinz_stinz_v1()
        >>> states.stinz
        stinz(0.0, 0.0, 2.0, 3.0, 4.0, 4.0)
        >>> fluxes.gefrinz
        gefrinz(0.0, 0.0, 0.0, 1.0, 2.0, 2.0)

        >>> refreezeflag(False)
        >>> model.calc_gefrinz_stinz_v1()
        >>> states.stinz
        stinz(0.0, 0.0, 2.0, 3.0, 4.0, 4.0)
        >>> fluxes.gefrinz
        gefrinz(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.RefreezeFlag,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.GefrPotInz,
        lland_states.SInz,
    )
    RESULTSEQUENCES = (lland_fluxes.GefrInz,)
    UPDATEDSEQUENCES = (lland_states.STInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW) and con.refreezeflag:
                flu.gefrinz[k] = min(flu.gefrpotinz[k], (sta.sinz[k] - sta.stinz[k]))
                sta.stinz[k] += flu.gefrinz[k]
            else:
                flu.gefrinz[k] = 0.0


class Calc_EvSInz_SInz_STInz_V1(modeltools.Method):
    r"""Calculate the evaporation from the snow interception storage, if any exists,
    and its content accordingly.

    Basic equations:
      :math:`SInz_{new} = f \cdot SInz_{old}`

      :math:`STInz_{new} = f \cdot STInz_{old}`

      :math:`f = \frac{SInz - EvSInz}{SInz}`

      :math:`EvSInz = max \left( \frac{WLatInz}{LWE}, SInz \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(LAUBW, MISCHW, NADELW, NADELW, NADELW, NADELW, NADELW, ACKER)
        >>> fluxes.wlatinz = -20.0, 0.0, 50.0, 100.0, 150.0, 150.0, 150.0, 150.0
        >>> states.sinz = 2.0, 2.0, 2.0, 2.0, 2.0, 1.5, 0.0, 2.0
        >>> states.stinz = 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 1.0
        >>> model.calc_evsinz_sinz_stinz_v1()
        >>> fluxes.evsinz
        evsinz(-0.323905, 0.0, 0.809762, 1.619524, 2.0, 1.5, 0.0, 0.0)
        >>> states.sinz
        sinz(2.323905, 2.0, 1.190238, 0.380476, 0.0, 0.0, 0.0, 0.0)
        >>> states.stinz
        stinz(1.161952, 1.0, 0.595119, 0.190238, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    FIXEDPARAMETERS = (lland_fixed.LWE,)
    REQUIREDSEQUENCES = (lland_fluxes.WLatInz,)
    RESULTSEQUENCES = (lland_fluxes.EvSInz,)
    UPDATEDSEQUENCES = (
        lland_states.SInz,
        lland_states.STInz,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW) and (sta.sinz[k] > 0.0):
                flu.evsinz[k] = min(flu.wlatinz[k] / fix.lwe, sta.sinz[k])
                d_frac = (sta.sinz[k] - flu.evsinz[k]) / sta.sinz[k]
                sta.sinz[k] *= d_frac
                sta.stinz[k] *= d_frac
            else:
                flu.evsinz[k] = 0.0
                sta.sinz[k] = 0.0
                sta.stinz[k] = 0.0


class Update_WaDaInz_SInz_V1(modeltools.Method):
    r"""Update the actual water release from and the liquid water content of
    the snow interception storage due to melting.

    Basic equations:
      :math:`WaDaInz_{new} = WaDaInz_{old} + \Delta`

      :math:`SInz_{new} = SInz_{old} - \Delta`

      :math:`\Delta = max(SInz - PWMax \cdot STInz, 0)`

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> lnk(ACKER, LAUBW, LAUBW, MISCHW, NADELW)
        >>> pwmax(2.0)
        >>> states.stinz = 0.0, 0.0, 1.0, 1.0, 1.0
        >>> states.sinz = 1.0, 0.0, 1.0, 2.0, 3.0
        >>> fluxes.wadainz = 1.0
        >>> model.update_wadainz_sinz_v1()
        >>> states.sinz
        sinz(1.0, 0.0, 1.0, 2.0, 2.0)
        >>> fluxes.wadainz
        wadainz(1.0, 1.0, 1.0, 1.0, 2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (lland_states.STInz,)
    UPDATEDSEQUENCES = (
        lland_states.SInz,
        lland_fluxes.WaDaInz,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                d_wadainz_corr = max(sta.sinz[k] - con.pwmax[k] * sta.stinz[k], 0.0)
                flu.wadainz[k] += d_wadainz_corr
                sta.sinz[k] -= d_wadainz_corr


class Update_ESnowInz_V2(modeltools.Method):
    r"""Update the thermal energy content of the intercepted snow regarding snow
    melt and refreezing.

    Basic equation:
      :math:`\frac{dESnowInz}{dt} = RSchmelz \cdot (GefrInz - SchmInz)`

    Examples:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> lnk(ACKER, NADELW, NADELW, NADELW, NADELW)
        >>> fluxes.gefrinz = 0.0, 0.0, 4.0, 0.0, 4.0
        >>> fluxes.schminz = 0.0, 0.0, 0.0, 4.0, 4.0
        >>> states.esnowinz = 20.0, 20.0, -40.0, 30.925926, 0.0
        >>> states.sinz = 1.0, 0.0, 5.0, 5.0, 10.0
        >>> model.update_esnowinz_v2()
        >>> states.esnowinz
        esnowinz(0.0, 0.0, -9.074074, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_fluxes.GefrInz,
        lland_fluxes.SchmInz,
        lland_states.SInz,
    )
    UPDATEDSEQUENCES = (lland_states.ESnowInz,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (LAUBW, MISCHW, NADELW) and sta.sinz[k] > 0.0:
                sta.esnowinz[k] += fix.rschmelz * (flu.gefrinz[k] - flu.schminz[k])
            else:
                sta.esnowinz[k] = 0.0


class Calc_WATS_V1(modeltools.Method):
    """Add the snow fall to the frozen water equivalent of the snow cover.

    Basic equation:
      :math:`\\frac{dW\\!ATS}{dt} = SBes`

    Example:

        On water surfaces, method |Calc_WATS_V1| never builds up a snow layer:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(WASSER, FLUSS, SEE, ACKER)
        >>> fluxes.sbes = 2.0
        >>> states.wats = 5.5
        >>> model.calc_wats_v1()
        >>> states.wats
        wats(0.0, 0.0, 0.0, 7.5)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (lland_fluxes.SBes,)
    UPDATEDSEQUENCES = (lland_states.WATS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.wats[k] = 0.0
            else:
                sta.wats[k] += flu.sbes[k]


class Calc_WATS_V2(modeltools.Method):
    r"""Add the not intercepted snow fall to the frozen water equivalent of the
    snow cover.

    Basic equation:
      :math:`\frac{dW\!\!ATS}{dt} = SBes - SBesInz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(WASSER, ACKER, LAUBW)
        >>> states.wats = 0.0, 1.0, 2.0
        >>> fluxes.sbes = 2.0
        >>> fluxes.sbesinz = 1.0
        >>> model.calc_wats_v2()
        >>> states.wats
        wats(0.0, 3.0, 3.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
        lland_fluxes.SBesInz,
    )
    UPDATEDSEQUENCES = (lland_states.WATS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.wats[k] = 0.0
            elif con.lnk[k] in (LAUBW, MISCHW, NADELW):
                sta.wats[k] += flu.sbes[k] - flu.sbesinz[k]
            else:
                sta.wats[k] += flu.sbes[k]


class Calc_WaDa_WAeS_V1(modeltools.Method):
    """Add as much liquid precipitation to the snow cover as it is able to hold.

    Basic equations:
      :math:`\\frac{dW\\!AeS}{dt} = NBes - WaDa`

      :math:`W\\!AeS \\leq PWMax \\cdot W\\!ATS`

    Example:

        For simplicity, we set the threshold parameter |PWMax| to a value
        of two for each of the six initialised hydrological response units.
        Thus, the snow layer can hold as much liquid water as it contains
        frozen water.  Stand precipitation is also always set to the same
        value, but we vary the initial conditions of the snow cover:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> pwmax(2.0)
        >>> fluxes.nbes = 1.0
        >>> states.wats = 0.0, 0.0, 0.0, 1.0, 1.0, 1.0
        >>> states.waes = 1.0, 1.0, 0.0, 1.0, 1.5, 2.0
        >>> model.calc_wada_waes_v1()
        >>> states.waes
        waes(0.0, 0.0, 0.0, 2.0, 2.0, 2.0)
        >>> fluxes.wada
        wada(1.0, 1.0, 1.0, 0.0, 0.5, 1.0)

        Note the special cases of the first two response units of type |FLUSS|
        and |SEE|.  For water areas, stand precipitaton |NBes| is generally
        passed to |WaDa| and |WAeS| is set to zero.  For all other land
        use classes (of which only |ACKER| is selected), method
        |Calc_WaDa_WAeS_V1| only passes the part of |NBes| exceeding the
        actual snow holding capacity to |WaDa|.
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBes,
        lland_states.WATS,
    )
    UPDATEDSEQUENCES = (lland_states.WAeS,)
    RESULTSEQUENCES = (lland_fluxes.WaDa,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.waes[k] = 0.0
                flu.wada[k] = flu.nbes[k]
            else:
                sta.waes[k] += flu.nbes[k]
                flu.wada[k] = max(sta.waes[k] - con.pwmax[k] * sta.wats[k], 0.0)
                sta.waes[k] -= flu.wada[k]


class Calc_WaDa_WAeS_V2(modeltools.Method):
    r"""Add as much liquid precipitation and interception melt to the snow cover
    as it is able to hold.

    Basic equations:
      :math:`\frac{dW\!\!AeS}{dt} = NBes - NBesInz + WaDaInz - WaDa`

      :math:`W\!\!AeS \leq PWMax \cdot W\!\!AT\!S`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(10)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER, LAUBW, LAUBW, LAUBW, LAUBW)
        >>> pwmax(2.0)
        >>> fluxes.nbes = 1.5
        >>> fluxes.nbesinz = 1.0
        >>> fluxes.wadainz = 0.5
        >>> states.wats = 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0
        >>> states.waes = 1.0, 1.0, 0.0, 1.0, 1.5, 2.0, 0.0, 1.0, 1.5, 2.0
        >>> model.calc_wada_waes_v2()
        >>> states.waes
        waes(0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 0.0, 2.0, 2.0, 2.0)
        >>> fluxes.wada
        wada(1.5, 1.5, 1.5, 0.5, 1.0, 1.5, 1.0, 0.0, 0.5, 1.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBes,
        lland_fluxes.NBesInz,
        lland_fluxes.WaDaInz,
        lland_states.WATS,
    )
    UPDATEDSEQUENCES = (lland_states.WAeS,)
    RESULTSEQUENCES = (lland_fluxes.WaDa,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.waes[k] = 0.0
                flu.wada[k] = flu.nbes[k]
            if con.lnk[k] in (LAUBW, MISCHW, NADELW):
                sta.waes[k] += flu.nbes[k] - flu.nbesinz[k] + flu.wadainz[k]
                flu.wada[k] = max(sta.waes[k] - con.pwmax[k] * sta.wats[k], 0.0)
                sta.waes[k] -= flu.wada[k]
            else:
                sta.waes[k] += flu.nbes[k]
                flu.wada[k] = max(sta.waes[k] - con.pwmax[k] * sta.wats[k], 0.0)
                sta.waes[k] -= flu.wada[k]


class Calc_WGTF_V1(modeltools.Method):
    """Calculate the heat flux according to the degree-day method according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`WGTF = GTF \\cdot (TKor - TRefT) \\cdot RSchmelz`

    Examples:

        Initialise six hydrological response units with identical degree-day
        factors and temperature thresholds, but different combinations of
        land use and air temperature:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, LAUBW, ACKER, ACKER, LAUBW)
        >>> gtf(5.0)
        >>> treft(0.0)
        >>> trefn(1.0)
        >>> fluxes.tkor = 1.0, 1.0, 1.0, 1.0, 0.0, -1.0

        Note that the values of the degree-day factor are only half
        as much as the given value, due to the simulation step size
        being only half as long as the parameter step size:

        >>> gtf
        gtf(5.0)
        >>> from hydpy import print_values
        >>> print_values(gtf.values)
        2.5, 2.5, 2.5, 2.5, 2.5, 2.5

        The results of the first four hydrological response units show
        that |WGTF| is generally zero for water areas (here, |FLUSS| and
        |SEE|) in principally identical for all other landuse-use type
        (here, |ACKER| and |LAUBW|).  The results of the last three
        response units show the expectable linear relationship.  However,
        note that that |WGTF| is allowed to be negative:

        >>> model.calc_wgtf_v1()
        >>> fluxes.wgtf
        wgtf(0.0, 0.0, 19.328704, 19.328704, 0.0, -19.328704)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.GTF,
        lland_control.TRefT,
    )
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (lland_fluxes.TKor,)
    RESULTSEQUENCES = (lland_fluxes.WGTF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wgtf[k] = 0.0
            else:
                flu.wgtf[k] = con.gtf[k] * (flu.tkor[k] - con.treft[k]) * fix.rschmelz


class Calc_WNied_V1(modeltools.Method):
    """Calculate the heat flux into the snow layer due to the total amount
    of ingoing precipitation (:cite:t:`ref-LARSIM`, modified).

    Method |Calc_WNied_V1| assumes that the temperature of precipitation
    equals air temperature minus |TRefN|.

    Basic equation:
      :math:`WNied = (TKor - TRefN) \\cdot
      (CPEis \\cdot SBes + CPWasser \\cdot (NBes - SBes))`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> lnk(ACKER, ACKER, ACKER, ACKER, WASSER)
        >>> trefn(-2.0, 2.0, 2.0, 2.0, 2.0)
        >>> fluxes.tkor(1.0)
        >>> fluxes.nbes = 10.0
        >>> fluxes.sbes = 0.0, 0.0, 5.0, 10.0, 10.0
        >>> model.calc_wnied_v1()
        >>> fluxes.wnied
        wnied(2.9075, -0.969167, -0.726481, -0.483796, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.TRefN,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.NBes,
        lland_fluxes.SBes,
    )
    RESULTSEQUENCES = (lland_fluxes.WNied,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wnied[k] = 0.0
            else:
                d_ice = fix.cpeis * flu.sbes[k]
                d_water = fix.cpwasser * (flu.nbes[k] - flu.sbes[k])
                flu.wnied[k] = (flu.tkor[k] - con.trefn[k]) * (d_ice + d_water)


class Calc_WNied_ESnow_V1(modeltools.Method):
    """Calculate the heat flux into the snow layer due to the amount
    of precipitation actually hold by the snow layer.

    Method |Calc_WNied_V1| assumes that the temperature of precipitation
    equals air temperature minus |TRefN|.  The same holds for the
    temperature of the fraction of precipitation not hold by the snow
    layer (in other words: no temperature mixing occurs).

    Basic equation:
      :math:`\\frac{dESnow}{dt} = WNied`

      :math:`WNied = (TKor-TRefN) \\cdot
      (CPEis \\cdot SBes + CPWasser \\cdot (NBes - SBes - WaDa))`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(ACKER, ACKER, ACKER, ACKER, ACKER, WASSER)
        >>> trefn(1.0)
        >>> states.esnow = 0.5
        >>> fluxes.tkor = 4.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> fluxes.nbes = 10.0
        >>> fluxes.sbes = 0.0, 0.0, 5.0, 10.0, 5.0, 5.0
        >>> fluxes.wada = 0.0, 0.0, 0.0, 0.0, 5.0, 5.0
        >>> model.calc_wnied_esnow_v1()
        >>> fluxes.wnied
        wnied(2.9075, -0.969167, -0.726481, -0.483796, -0.241898, 0.0)
        >>> states.esnow
        esnow(3.4075, -0.469167, -0.226481, 0.016204, 0.258102, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.TRefN,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.NBes,
        lland_fluxes.SBes,
        lland_fluxes.WaDa,
    )
    UPDATEDSEQUENCES = (lland_states.ESnow,)
    RESULTSEQUENCES = (lland_fluxes.WNied,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wnied[k] = 0.0
                sta.esnow[k] = 0.0
            else:
                d_ice = fix.cpeis * flu.sbes[k]
                d_water = fix.cpwasser * (flu.nbes[k] - flu.sbes[k] - flu.wada[k])
                flu.wnied[k] = (flu.tkor[k] - con.trefn[k]) * (d_ice + d_water)
                sta.esnow[k] += flu.wnied[k]


class Return_SaturationVapourPressure_V1(modeltools.Method):
    r"""Calculate and return the saturation vapour pressure over an
    arbitrary surface for the given temperature according to :cite:t:`ref-LARSIM`
    (based on :cite:t:`ref-Weischet1983`).

    Basic equation:
      :math:`6.1078 \cdot
      2.71828^{\frac{17.08085 \cdot temperature}{temperature + 234.175}}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_saturationvapourpressure_v1(10.0))
        12.293852
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        temperature: float,
    ) -> float:
        return 6.1078 * 2.71828 ** (17.08085 * temperature / (temperature + 234.175))


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    """Calculate the saturation vapour pressure over arbitrary surfaces.

    Basic equation:
      :math:`SaturationVapourPressure =
      Return\\_SaturationVapourPressure\\_V1(TKor)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkor = -10.0, 0.0, 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> fluxes.saturationvapourpressure
        saturationvapourpressure(2.850871, 6.1078, 12.293852)
    """

    SUBMETHODS = (Return_SaturationVapourPressure_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (lland_fluxes.TKor,)
    RESULTSEQUENCES = (lland_fluxes.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.saturationvapourpressure[k] = model.return_saturationvapourpressure_v1(
                flu.tkor[k]
            )


class Calc_ActualVapourPressure_V1(modeltools.Method):
    r"""Calculate the actual vapour pressure.

    Basic equation:
      :math:`ActualVapourPressure =
      SaturationVapourPressure \cdot RelativeHumidity / 100`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep()
        >>> nhru(1)
        >>> derived.nmblogentries.update()
        >>> inputs.relativehumidity = 60.0
        >>> fluxes.saturationvapourpressure = 20.0
        >>> model.calc_actualvapourpressure_v1()
        >>> fluxes.actualvapourpressure
        actualvapourpressure(12.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
        lland_fluxes.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (lland_fluxes.ActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.actualvapourpressure[k] = (
                flu.saturationvapourpressure[k] * inp.relativehumidity / 100.0
            )


class Calc_RLAtm_V1(modeltools.Method):
    r"""Calculate the longwave radiation emitted from the atmosphere according to
    :cite:t:`ref-LARSIM` (based on :cite:t:`ref-Thompson1981`).

    Basic equation:

      :math:`RLAtm =
      FrAtm \cdot Sigma \cdot  (Tkor + 273.15)^4 \cdot
      \left( \frac{ActualVapourPressure}{TKor + 273.15} \right) ^{1/7}
      \cdot \left(1 + 0.22 \cdot \left(
      1 - \frac{DailySunshineDuration}{DailyPossibleSunshineDuration} \right)^2
      \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.tkor = 0.0, 10.0
        >>> fluxes.actualvapourpressure = 6.0
        >>> fluxes.dailysunshineduration = 12.0
        >>> fluxes.dailypossiblesunshineduration = 14.0
        >>> model.calc_rlatm_v1()
        >>> aides.rlatm
        rlatm(235.207154, 270.197425)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
    )
    RESULTSEQUENCES = (lland_aides.RLAtm,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        d_rs = flu.dailysunshineduration / flu.dailypossiblesunshineduration
        d_common = fix.fratm * fix.sigma * (1.0 + 0.22 * (1.0 - d_rs) ** 2)
        for k in range(con.nhru):
            d_t = flu.tkor[k] + 273.15
            aid.rlatm[k] = d_common * (
                d_t**4 * (flu.actualvapourpressure[k] / d_t) ** (1.0 / 7.0)
            )


class Return_NetLongwaveRadiationInz_V1(modeltools.Method):
    r"""Calculate and return the net longwave radiation for intercepted snow.

    The following equation is not part of the official `LARSIM`_ documentation.
    We think, it fits to the geometric assumtions underlying method
    |Return_NetLongwaveRadiationSnow_V1| but so far have not thoroughly checked
    if it results in realistic net longwave radiations.

    Basic equation:

      :math:`\big( 1 - Fr \big) \cdot \big( 0.97 \cdot Sigma \cdot (TempS + 273.15)^4
      - RLAtm \big)`

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(LAUBW, NADELW)
        >>> derived.moy.update()
        >>> derived.fr.laubw_jan = 0.4
        >>> derived.fr.laubw_feb = 0.5
        >>> derived.fr.nadelw_jan = 0.6
        >>> derived.fr.nadelw_feb = 0.7
        >>> aides.tempsinz = -1.0
        >>> aides.rlatm = 100.0

        >>> model.idx_sim = pub.timegrids.init["2000-01-31"]
        >>> from hydpy import print_values
        >>> for hru in range(2):
        ...     print_values([hru, model.return_netlongwaveradiationinz_v1(hru)])
        0, 126.624073
        1, 84.416049

        >>> model.idx_sim = pub.timegrids.init["2000-02-01"]
        >>> from hydpy import print_values
        >>> for hru in range(2):
        ...     print_values([hru, model.return_netlongwaveradiationinz_v1(hru)])
        0, 105.520061
        1, 63.312037

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (lland_control.Lnk,)
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (lland_fixed.Sigma,)
    REQUIREDSEQUENCES = (
        lland_aides.TempSInz,
        lland_aides.RLAtm,
    )

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        aid = model.sequences.aides.fastaccess
        d_fr = der.fr[con.lnk[k] - 1, der.moy[model.idx_sim]]
        d_rlsnow = fix.sigma * (aid.tempsinz[k] + 273.15) ** 4
        return (1.0 - d_fr) * (d_rlsnow - aid.rlatm[k])


class Return_NetLongwaveRadiationSnow_V1(modeltools.Method):
    r"""Calculate and return the net longwave radiation for snow-covered areas.

    Method |Return_NetLongwaveRadiationSnow_V1| differentiates between forests
    (|LAUBW|, |MISCHW|, and |NADELW|) and open areas.  The outgoing longwave radiation
    always depends on the snow surface temperature.  For open areas, the ingoing counter
    radiation stems from the atmosphere only.  This atmospheric radiation is partly
    replaced by the longwave radiation emitted by the tree canopies for forests.  The
    lower the value of parameter |Fr|, the higher this shading effect of the canopies.
    See :cite:t:`ref-LARSIM` and :cite:t:`ref-Thompson1981` for further information.

    Basic equation:

      .. math::
        Sigma \cdot (TempSSurface + 273.15)^4 - \begin{cases}
        Fr \cdot RLAtm + \big( 1 - Fr  \big) \cdot
        \big( 0.97 \cdot Sigma \cdot (TKor + 273.15)^4 \big)
        &|\
        Lnk \in \{LAUBW, MISCHW, NADELW\}
        \\
        RLAtm
        &|\
        Lnk \notin \{LAUBW, MISCHW, NADELW\}
        \end{cases}

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)
        >>> derived.moy.shape = 1
        >>> derived.moy(5)
        >>> derived.fr(0.3)
        >>> fluxes.tempssurface = -5.0
        >>> fluxes.tkor = 0.0
        >>> aides.rlatm = 235.207154
        >>> from hydpy import print_values
        >>> for hru in range(2):
        ...     print_values([hru, model.return_netlongwaveradiationsnow_v1(hru)])
        0, 57.945793
        1, 8.273292
    """

    CONTROLPARAMETERS = (lland_control.Lnk,)
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (lland_fixed.Sigma,)
    REQUIREDSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_fluxes.TKor,
        lland_aides.RLAtm,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        d_temp = flu.tkor[k] + 273.15
        d_counter = aid.rlatm[k]
        if con.lnk[k] in (LAUBW, MISCHW, NADELW):
            d_fr = der.fr[con.lnk[k] - 1, der.moy[model.idx_sim]]
            d_counter = d_fr * d_counter + (1.0 - d_fr) * 0.97 * fix.sigma * d_temp**4
        return fix.sigma * (flu.tempssurface[k] + 273.15) ** 4 - d_counter


class Update_TauS_V1(modeltools.Method):
    """Calculate the dimensionless age of the snow layer according to
    :cite:t:`ref-LARSIM` (based on :cite:t:`ref-LUBW2006b`).

    Basic equations:
      :math:`TauS_{new} = TauS_{old} \\cdot max(1 - 0.1 \\cdot SBes), 0) +
      \\frac{r_1+r_2+r_3}{10^6} \\cdot Seconds`

      :math:`r_1 = exp\\left(5000 \\cdot
      \\left(\\frac{1}{273.15} - \\frac{1}{273.15+TempS}\\right)\\right)`

      :math:`r_2 = min\\left(r_1^{10}, 1\\right)`

      :math:`r_3 = 0.03`

    Example:

        For snow-free surfaces, |TauS| is not defined; snowfall rejuvenates
        an existing snow layer; high temperatures increase the speed of aging:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(10)
        >>> derived.seconds(24*60*60)
        >>> fluxes.sbes = 0.0, 1.0, 5.0, 9.0, 10.0, 11.0, 11.0, 11.0, 11.0, 11.0
        >>> states.waes = 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        >>> states.taus = 1.0, nan, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        >>> aides.temps = (
        ...     0.0, 0.0, -10.0, -10.0, -10.0, -10.0, -1.0, 0.0, 1.0, 10.0)
        >>> model.update_taus()
        >>> states.taus
        taus(nan, 0.175392, 0.545768, 0.145768, 0.045768, 0.045768, 0.127468,
             0.175392, 0.181358, 0.253912)

        Note that an initial |numpy.nan| value serves as an indication that
        there has been no snow-layer in the last simulation step, meaning
        the snow is fresh and starts with an age of zero (see the first
        two hydrological response units).
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    DERIVEDPARAMETERS = (lland_derived.Seconds,)
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
        lland_states.WAeS,
        lland_aides.TempS,
    )
    RESULTSEQUENCES = (lland_states.TauS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0:
                if modelutils.isnan(sta.taus[k]):
                    sta.taus[k] = 0.0
                d_r1 = modelutils.exp(
                    5000.0 * (1 / 273.15 - 1.0 / (273.15 + aid.temps[k]))
                )
                d_r2 = min(d_r1**10, 1.0)
                sta.taus[k] *= max(1 - 0.1 * flu.sbes[k], 0.0)
                sta.taus[k] += (d_r1 + d_r2 + 0.03) / 1e6 * der.seconds
            else:
                sta.taus[k] = modelutils.nan


class Calc_ActualAlbedo_V1(modeltools.Method):
    r"""Calculate the current snow albedo according to :cite:t:`ref-LARSIM`, based on
    :cite:t:`ref-LUBW2006b`.

    For snow-free surfaces, method |Calc_ActualAlbedo_V1| sets |ActualAlbedo| to
    |numpy.nan|.  For snow conditions, it estimates the albedo based on the snow age,
    as shown by the following equation.

    Basic equation:
      :math:`ActualAlbedo = Albedo0Snow \cdot
      \left( 1 - SnowAgingFactor \cdot \frac{TauS}{1 + TauS} \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> albedo0snow(0.8)
        >>> snowagingfactor(0.35)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.taus = nan, 0.0, 1.0, 3.0
        >>> model.calc_actualalbedo_v1()
        >>> fluxes.actualalbedo
        actualalbedo(nan, 0.8, 0.66, 0.59)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.SnowAgingFactor,
        lland_control.Albedo0Snow,
    )
    REQUIREDSEQUENCES = (
        lland_states.TauS,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (lland_fluxes.ActualAlbedo,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.0:
                flu.actualalbedo[k] = con.albedo0snow * (
                    1.0 - con.snowagingfactor * sta.taus[k] / (1.0 + sta.taus[k])
                )
            else:
                flu.actualalbedo[k] = modelutils.nan


class Calc_NetShortwaveRadiationSnow_V1(modeltools.Method):
    r"""Calculate the net shortwave radiation for snow-surfaces.

    Basic equation:
      :math:`NetShortwaveRadiationSnow =
      Fr \cdot (1.0 - ActualAlbedo) \cdot AdjustedGlobalRadiation`

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)
        >>> derived.fr.acker_jan = 1.0
        >>> derived.fr.acker_feb = 1.0
        >>> derived.fr.laubw_jan = 0.5
        >>> derived.fr.laubw_feb = 0.1
        >>> derived.moy.update()
        >>> inputs.globalradiation = 40.0
        >>> fluxes.actualalbedo = 0.5

        >>> model.idx_sim = pub.timegrids.init["2000-01-31"]
        >>> model.calc_netshortwaveradiationsnow_v1()
        >>> fluxes.netshortwaveradiationsnow
        netshortwaveradiationsnow(20.0, 10.0)

        >>> model.idx_sim = pub.timegrids.init["2000-02-01"]
        >>> model.calc_netshortwaveradiationsnow_v1()
        >>> fluxes.netshortwaveradiationsnow
        netshortwaveradiationsnow(20.0, 2.0)

        >>> fluxes.actualalbedo = nan
        >>> model.calc_netshortwaveradiationsnow_v1()
        >>> fluxes.netshortwaveradiationsnow
        netshortwaveradiationsnow(0.0, 0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.GlobalRadiation,
        lland_fluxes.ActualAlbedo,
    )
    RESULTSEQUENCES = (lland_fluxes.NetShortwaveRadiationSnow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if modelutils.isnan(flu.actualalbedo[k]):
                flu.netshortwaveradiationsnow[k] = 0.0
            else:
                flu.netshortwaveradiationsnow[k] = (
                    der.fr[con.lnk[k] - 1, der.moy[model.idx_sim]]
                    * (1.0 - flu.actualalbedo[k])
                    * inp.globalradiation
                )


class Return_TempS_V1(modeltools.Method):
    """Calculate and return the average temperature of the snow layer according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`max\\left(
      \\frac{ESnow}{WATS \\cdot CPEis + (WAeS-WATS) \\cdot CPWasser},
      -273\\right)`

    Example:

        Note that we use |numpy.nan| values for snow-free surfaces
        (see the result of the first hydrological response unit) and
        that method |Return_TempS_V1| never returns temperature values
        lower than -273 °C (see the result of the fifth response unit):

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> states.wats = 0.0, 0.5, 5.0, 0.5, 0.5
        >>> states.waes = 0.0, 1.0, 10.0, 1.0, 1.0
        >>> states.esnow = 0.0, 0.0, -1.0, -10.0, -100.0
        >>> from hydpy import round_
        >>> round_(model.return_temps_v1(0))
        nan
        >>> round_(model.return_temps_v1(1))
        0.0
        >>> round_(model.return_temps_v1(2))
        -1.376498
        >>> round_(model.return_temps_v1(3))
        -137.649758
        >>> round_(model.return_temps_v1(4))
        -273.0
    """

    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_states.WATS,
        lland_states.WAeS,
        lland_states.ESnow,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.waes[k] > 0.0:
            d_ice = fix.cpeis * sta.wats[k]
            d_water = fix.cpwasser * (sta.waes[k] - sta.wats[k])
            return max(sta.esnow[k] / (d_ice + d_water), -273.0)
        return modelutils.nan


class Return_ESnowInz_V1(modeltools.Method):
    r"""Calculate and return the thermal energy content of the intercepted snow
    for its given bulk temperature.

    Basic equation:
      :math:`temps \cdot \big( STInz \cdot CPEis + (SInz - STInz) \cdot CPWasser \big)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(3)
        >>> states.stinz = 0.0, 0.5, 5.0
        >>> states.sinz = 0.0, 1.0, 10.0
        >>> states.esnowinz = 0.0, 0.0, -2.0
        >>> from hydpy import round_
        >>> round_(model.return_esnowinz_v1(0, 1.0))
        0.0
        >>> round_(model.return_esnowinz_v1(1, 0.0))
        0.0
        >>> round_(model.return_esnowinz_v1(2, -2.752995))
        -2.0
    """

    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_states.STInz,
        lland_states.SInz,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
        temps: float,
    ) -> float:
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        d_ice = fix.cpeis * sta.stinz[k]
        d_water = fix.cpwasser * (sta.sinz[k] - sta.stinz[k])
        return temps * (d_ice + d_water)


class Return_ESnow_V1(modeltools.Method):
    """Calculate and return the thermal energy content of the snow layer for
    the given bulk temperature according to :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`temps \\cdot (WATS \\cdot CPEis + (WAeS-WATS)\\cdot CPWasser)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(3)
        >>> states.wats = 0.0, 0.5, 5.0
        >>> states.waes = 0.0, 1.0, 10.0
        >>> states.esnow = 0.0, 0.0, -2.0
        >>> from hydpy import round_
        >>> round_(model.return_esnow_v1(0, 1.0))
        0.0
        >>> round_(model.return_esnow_v1(1, 0.0))
        0.0
        >>> round_(model.return_esnow_v1(2, -2.752995))
        -2.0
    """

    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_states.WATS,
        lland_states.WAeS,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
        temps: float,
    ) -> float:
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        d_ice = fix.cpeis * sta.wats[k]
        d_water = fix.cpwasser * (sta.waes[k] - sta.wats[k])
        return temps * (d_ice + d_water)


class Calc_TempS_V1(modeltools.Method):
    """Calculate the average temperature of the snow layer.

    Method |Calc_TempS_V1| uses method |Return_TempS_V1| to calculate
    the snow temperature of all hydrological response units.

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(3)
        >>> pwmax(2.0)
        >>> fluxes.tkor = -1.0
        >>> states.wats = 0.0, 0.5, 5
        >>> states.waes = 0.0, 1.0, 10
        >>> states.esnow = 0.0, 0.0, -2.0
        >>> model.calc_temps_v1()
        >>> aides.temps
        temps(nan, 0.0, -2.752995)
    """

    SUBMETHODS = (Return_TempS_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_states.WATS,
        lland_states.WAeS,
        lland_states.ESnow,
    )
    RESULTSEQUENCES = (lland_aides.TempS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            aid.temps[k] = model.return_temps_v1(k)


class Calc_TZ_V1(modeltools.Method):
    """Calculate the mean temperature in the top-layer of the soil according to
    :cite:t:`ref-LARSIM` (based on :cite:t:`ref-LUBW2006b`).

    Basic equation:
      .. math::
        TZ = \\begin{cases}
        \\frac{EBdn}{2 \\cdot z \\cdot CG}
        &|\\
        EBdn \\leq 0
        \\\\
        0
        &|\\
        0 < EBdn \\leq HeatOfFusion
        \\\\
        \\frac{EBdn - HeatOfFusion}{2 \\cdot z \\cdot CG}
        &|\\
        HeatOfFusion < EBdn
        \\end{cases}

    Examples:

        We set |TZ| to |numpy.nan| for all types of water areas:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> lnk(WASSER, FLUSS, SEE, WASSER, SEE, FLUSS, WASSER)
        >>> model.calc_tz_v1()
        >>> fluxes.tz
        tz(nan, nan, nan, nan, nan, nan, nan)

        For all other land use types, the above basic equation applies:

        >>> lnk(ACKER)
        >>> derived.heatoffusion(310.0)
        >>> states.ebdn(-20.0, -10.0, 0.0, 310.0, 620.0, 630, 640.0)
        >>> model.calc_tz_v1()
        >>> fluxes.tz
        tz(-2.88, -1.44, 0.0, 0.0, 0.0, 1.44, 2.88)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (lland_derived.HeatOfFusion,)
    FIXEDPARAMETERS = (
        lland_fixed.Z,
        lland_fixed.CG,
    )
    REQUIREDSEQUENCES = (lland_states.EBdn,)
    RESULTSEQUENCES = (lland_fluxes.TZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.tz[k] = modelutils.nan
            elif sta.ebdn[k] < 0.0:
                flu.tz[k] = sta.ebdn[k] / (2.0 * fix.z * fix.cg)
            elif sta.ebdn[k] < der.heatoffusion[k]:
                flu.tz[k] = 0.0
            else:
                flu.tz[k] = (sta.ebdn[k] - der.heatoffusion[k]) / (2.0 * fix.z * fix.cg)


class Return_WG_V1(modeltools.Method):
    """Calculate and return the "dynamic" soil heat flux according to
    :cite:t:`ref-LARSIM`.

    The soil heat flux |WG| depends on the temperature gradient between
    depth z and the surface.  We set the soil surface temperature to the air
    temperature for snow-free conditions and otherwise to the average
    temperature of the snow layer.

    Basic equations:
      .. math::
        \\begin{cases}
        LambdaG \\cdot \\frac{TZ-TempS}{Z}
        &|\\
        WAeS > 0
        \\\\
        LambdaG \\cdot \\frac{TZ-TKor}{Z}
        &|\\
        WAeS = 0
        \\end{cases}

    Examples:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nhru(2)
        >>> fixed.lambdag.restore()
        >>> fluxes.tz = 2.0
        >>> fluxes.tkor = 10.0
        >>> states.waes = 0.0, 1.0
        >>> aides.temps = nan, -1.0
        >>> from hydpy import round_
        >>> round_(model.return_wg_v1(0))
        -48.0
        >>> round_(model.return_wg_v1(1))
        18.0
    """

    FIXEDPARAMETERS = (
        lland_fixed.Z,
        lland_fixed.LambdaG,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TZ,
        lland_fluxes.TKor,
        lland_states.WAeS,
        lland_aides.TempS,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if sta.waes[k] > 0.0:
            d_temp = aid.temps[k]
        else:
            d_temp = flu.tkor[k]
        return fix.lambdag * (flu.tz[k] - d_temp) / fix.z


class Calc_WG_V1(modeltools.Method):
    """Calculate the soil heat flux.

    Method |Calc_WG_V1| uses method |Return_WG_V1| to calculate the
    "dynamic" soil heat flux for all hydrological response units that
    do not represent water areas.

    Examples:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> lnk(ACKER, VERS, WASSER, FLUSS, SEE)
        >>> fixed.lambdag.restore()
        >>> fluxes.tz = 2.0
        >>> fluxes.tkor = 10.0
        >>> states.waes = 0.0, 1.0, 0.0, 0.0, 0.0
        >>> aides.temps = nan, -1.0, nan, nan, nan
        >>> model.calc_wg_v1()
        >>> fluxes.wg
        wg(-48.0, 18.0, 0.0, 0.0, 0.0)
    """

    SUBMETHODS = (Return_WG_V1,)
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Z,
        lland_fixed.LambdaG,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TZ,
        lland_fluxes.TKor,
        lland_states.WAeS,
        lland_aides.TempS,
    )
    RESULTSEQUENCES = (lland_fluxes.WG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (FLUSS, SEE, WASSER):
                flu.wg[k] = 0.0
            else:
                flu.wg[k] = model.return_wg_v1(k)


class Update_EBdn_V1(modeltools.Method):
    """Update the thermal energy content of the upper soil layer according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`\\frac{dEBdn}{dt} = WG2Z - WG`

    Example:

        Water areas do not posses a soil energy content. For all other
        landuse types, the above equation applies:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(WASSER, FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> pub.timegrids = "2019-04-29", "2019-05-03", "1d"
        >>> derived.moy.update()
        >>> wg2z.apr = -0.347222
        >>> wg2z.may = -0.462963
        >>> states.ebdn = 0.0
        >>> fluxes.wg = 0.0, 0.0, 0.0, 5.787037, 11.574074, 23.148148
        >>> model.idx_sim = 1
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(0.0, 0.0, 0.0, -6.134259, -11.921296, -23.49537)
        >>> model.idx_sim = 2
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(0.0, 0.0, 0.0, -12.384259, -23.958333, -47.106481)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WG2Z,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (lland_fluxes.WG,)
    UPDATEDSEQUENCES = (lland_states.EBdn,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.ebdn[k] = 0.0
            else:
                sta.ebdn[k] += con.wg2z[der.moy[model.idx_sim]] - flu.wg[k]


class Return_WSensInz_V1(modeltools.Method):
    r"""Calculate and return the sensible heat flux between the intercepted snow and
    the atmosphere.

    Basic equation:
      :math:`(Turb0 + Turb1 \cdot WindSpeed2m) \cdot (TempSInz - TKor)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fluxes.tkor = -2.0, -1.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> aides.tempsinz = -5.0, 0.0
        >>> from hydpy import round_
        >>> round_(model.return_wsensinz_v1(0))
        -24.0
        >>> round_(model.return_wsensinz_v1(1))
        8.0
    """

    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_aides.TempSInz,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        return (con.turb0 + con.turb1 * flu.reducedwindspeed2m[k]) * (
            aid.tempsinz[k] - flu.tkor[k]
        )


class Return_WSensSnow_V1(modeltools.Method):
    """Calculate and return the sensible heat flux of the snow surface according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`(Turb0 + Turb1 \\cdot WindSpeed2m) \\cdot (TempSSurface - TKor)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fluxes.tkor = -2.0, -1.0
        >>> fluxes.tempssurface = -5.0, 0.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> from hydpy import round_
        >>> round_(model.return_wsenssnow_v1(0))
        -24.0
        >>> round_(model.return_wsenssnow_v1(1))
        8.0
    """

    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.TempSSurface,
        lland_fluxes.ReducedWindSpeed2m,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return (con.turb0 + con.turb1 * flu.reducedwindspeed2m[k]) * (
            flu.tempssurface[k] - flu.tkor[k]
        )


class Return_WLatInz_V1(modeltools.Method):
    r"""Calculate and return the latent heat flux between the surface of the
    intercepted snow and the atmosphere.

    Basic equation:
      :math:`(Turb0 + Turb1 \cdot ReducedWindSpeed2m) \cdot
      PsiInv \cdot (SaturationVapourPressureInz - ActualVapourPressure))`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.saturationvapourpressureinz = 4.0, 8.0
        >>> fluxes.actualvapourpressure = 6.108
        >>> from hydpy import round_
        >>> round_(model.return_wlatinz_v1(0))
        -29.68064
        >>> round_(model.return_wlatinz_v1(1))
        26.63936
    """

    CONTROLPARAMETERS = (lland_control.Turb0, lland_control.Turb1)
    FIXEDPARAMETERS = (lland_fixed.PsyInv,)
    REQUIREDSEQUENCES = (
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.SaturationVapourPressureInz,
        lland_fluxes.ActualVapourPressure,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return (
            (con.turb0 + con.turb1 * flu.reducedwindspeed2m[k])
            * fix.psyinv
            * (flu.saturationvapourpressureinz[k] - flu.actualvapourpressure[k])
        )


class Return_WLatSnow_V1(modeltools.Method):
    """Calculate and return the latent heat flux of the snow surface according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`(Turb0 + Turb1 \\cdot ReducedWindSpeed2m) \\cdot
      PsiInv \\cdot (SaturationVapourPressureSnow - ActualVapourPressure))`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.saturationvapourpressuresnow = 4.0, 8.0
        >>> fluxes.actualvapourpressure = 6.108
        >>> from hydpy import round_
        >>> round_(model.return_wlatsnow_v1(0))
        -29.68064
        >>> round_(model.return_wlatsnow_v1(1))
        26.63936
    """

    CONTROLPARAMETERS = (lland_control.Turb0, lland_control.Turb1)
    FIXEDPARAMETERS = (lland_fixed.PsyInv,)
    REQUIREDSEQUENCES = (
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.ActualVapourPressure,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return (
            (con.turb0 + con.turb1 * flu.reducedwindspeed2m[k])
            * fix.psyinv
            * (flu.saturationvapourpressuresnow[k] - flu.actualvapourpressure[k])
        )


class Return_WSurf_V1(modeltools.Method):
    """Calculate and return the snow surface heat flux according to :cite:t:`ref-LARSIM`
    (based on :cite:t:`ref-LUBW2006b`).

    Basic equation:
      :math:`KTSchnee \\cdot (TempS - TempSSurface)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nhru(1)
        >>> ktschnee(5.0)
        >>> fluxes.tempssurface = -4.0
        >>> aides.temps = -2.0
        >>> from hydpy import round_
        >>> round_(model.return_wsurf_v1(0))
        10.0

        Method |Return_WSurf_V1| explicitely supports infinite
        |KTSchnee| values:

        >>> ktschnee(inf)
        >>> round_(model.return_wsurf_v1(0))
        inf
    """

    CONTROLPARAMETERS = (lland_control.KTSchnee,)
    REQUIREDSEQUENCES = (
        lland_aides.TempS,
        lland_fluxes.TempSSurface,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        if modelutils.isinf(con.ktschnee):
            return modelutils.inf
        return con.ktschnee * (aid.temps[k] - flu.tempssurface[k])


class Return_NetRadiation_V1(modeltools.Method):
    """Calculate and return the total net radiation.

    Basic equation:
      :math:`netshortwaveradiation - netlongwaveradiation`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_netradiation_v1(300.0, 200.0))
        100.0
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        netshortwaveradiation: float,
        netlongwaveradiation: float,
    ) -> float:
        return netshortwaveradiation - netlongwaveradiation


class Return_EnergyGainSnowSurface_V1(modeltools.Method):
    """Calculate and return the net energy gain of the snow surface
    (:cite:t`ref-LARSIM` based on :cite:t:`ref-LUBW2006b`, modified).

    As surface cannot store any energy, method |Return_EnergyGainSnowSurface_V1|
    returns zero if one supplies it with the correct temperature of the
    snow surface.  Hence, this methods provides a means to find this
    "correct" temperature via root finding algorithms.

    Basic equation:
      :math:`WSurf(tempssurface) +
      NetshortwaveRadiation - NetlongwaveRadiation(tempssurface) -
      WSensSnow(tempssurface) - WLatSnow(tempssurface)`

    Example:

        Method |Return_EnergyGainSnowSurface_V1| relies on multiple
        submethods with different requirements.  Hence, we first need to
        specify a lot of input data (see the documentation on the
        different submethods for further information):

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> ktschnee(5.0)
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationsnow = 20.0
        >>> derived.nmblogentries.update()
        >>> aides.temps = -2.0
        >>> aides.rlatm = 200.0

        Under the defined conditions and for a snow surface temperature of
        -4 °C, the net energy gain would be negative:

        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_energygainsnowsurface_v1(-4.0))
        -82.62933

        As a side-effect, method |Return_EnergyGainSnowSurface_V1| calculates
        the following flux sequences for the given snow surface temperature:

        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(4.539126)
        >>> fluxes.netlongwaveradiationsnow
        netlongwaveradiationsnow(97.550439)
        >>> fluxes.netradiationsnow
        netradiationsnow(-77.550439)
        >>> fluxes.wsenssnow
        wsenssnow(-8.0)
        >>> fluxes.wlatsnow
        wlatsnow(23.078891)
        >>> fluxes.wsurf
        wsurf(10.0)

    Technical checks:

        Note that method |Return_EnergyGainSnowSurface_V1| calculates the
        value of sequence |SaturationVapourPressureSnow| before its submethod
        |Return_WLatSnow_V1| uses it and that it assigns the given value to
        sequence |TempSSurface| before its submethods |Return_WSensSnow_V1|,
        |Return_NetLongwaveRadiationSnow_V1|, and |Return_WSurf_V1| use it:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.lland.lland_model import (
        ...     Return_EnergyGainSnowSurface_V1)
        >>> print(check_selectedvariables(Return_EnergyGainSnowSurface_V1))
        Possibly missing (REQUIREDSEQUENCES):
            Return_WLatSnow_V1: SaturationVapourPressureSnow
            Return_WSensSnow_V1: TempSSurface
            Return_NetLongwaveRadiationSnow_V1: TempSSurface
            Return_WSurf_V1: TempSSurface
    """

    SUBMETHODS = (
        Return_SaturationVapourPressure_V1,
        Return_WLatSnow_V1,
        Return_WSensSnow_V1,
        Return_NetLongwaveRadiationSnow_V1,
        Return_NetRadiation_V1,
        Return_WSurf_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.Lnk,
        lland_control.KTSchnee,
        lland_control.Turb0,
        lland_control.Turb1,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.PsyInv,
        lland_fixed.Sigma,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_aides.TempS,
        lland_aides.RLAtm,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.WSensSnow,
        lland_fluxes.WLatSnow,
        lland_fluxes.NetLongwaveRadiationSnow,
        lland_fluxes.NetRadiationSnow,
        lland_fluxes.WSurf,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        tempssurface: float,
    ) -> float:
        flu = model.sequences.fluxes.fastaccess

        k = model.idx_hru

        flu.tempssurface[k] = tempssurface

        flu.saturationvapourpressuresnow[k] = model.return_saturationvapourpressure_v1(
            flu.tempssurface[k]
        )
        flu.wlatsnow[k] = model.return_wlatsnow_v1(k)
        flu.wsenssnow[k] = model.return_wsenssnow_v1(k)
        flu.netlongwaveradiationsnow[k] = model.return_netlongwaveradiationsnow_v1(k)
        flu.netradiationsnow[k] = model.return_netradiation_v1(
            flu.netshortwaveradiationsnow[k],
            flu.netlongwaveradiationsnow[k],
        )
        flu.wsurf[k] = model.return_wsurf_v1(k)

        return (
            flu.wsurf[k] + flu.netradiationsnow[k] - flu.wsenssnow[k] - flu.wlatsnow[k]
        )


class Return_TempSSurface_V1(modeltools.Method):
    """Determine and return the snow surface temperature (:cite:t:`ref-LARSIM`
    based on :cite:t:`ref-LUBW2006b`, modified).

    |Return_TempSSurface_V1| needs to determine the snow surface temperature
    via iteration.  Therefore, it uses the class |PegasusTempSSurface|
    which searches the root of the net energy gain of the snow surface
    defined by method |Return_EnergyGainSnowSurface_V1|.

    For snow-free conditions, method |Return_TempSSurface_V1| sets the value
    of |TempSSurface| to |numpy.nan| and the values of |WSensSnow|,
    |WLatSnow|, and |WSurf| to zero.  For snow conditions, the side-effects
    discussed in the documentation on method |Return_EnergyGainSnowSurface_V1|
    apply.

    Example:

        We reuse the configuration of the documentation on method
        |Return_EnergyGainSnowSurface_V1|, except that we prepare six
        hydrological response units and calculate their snow surface temperature:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(ACKER)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> ktschnee(5.0)
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 0.0, 1.0, 1.0, 1.0, 1.0, 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationsnow = 10.0, 10.0, 20.0, 20.0, 20.0, 200.0
        >>> aides.temps = nan, -2.0, -2.0, -50.0, -200.0, -2.0
        >>> aides.rlatm = 200.0
        >>> for hru in range(6):
        ...     _ = model.return_tempssurface_v1(hru)

        For the first, snow-free response unit, we cannot define a reasonable
        snow surface temperature, of course:

        >>> fluxes.tempssurface[0]
        nan

        Comparing response units two and three shows that a moderate increase
        in short wave radiation is compensated by a moderate increase in snow
        surface temperature:

        >>> from hydpy import print_values
        >>> print_values(fluxes.tempssurface[1:3])
        -8.307868, -7.828995

        To demonstrate the robustness of the implemented approach, response
        units three to five show the extreme decrease in surface temperature
        due to an even more extrem decrease in the bulk temperature of the
        snow layer:

        >>> print_values(fluxes.tempssurface[2:5])
        -7.828995, -20.191197, -66.644357

        The sixths response unit comes with a very high net radiation
        to clarify that the allowed maximum value of the snow surface temperature
        is 0°C.  Hence, the snow temperature gradient might actually be too
        small for conducting all available energy deeper into the snow layer.
        In reality, only the topmost snow layer would melt in such a situation.
        Here, we do not differentiate between melting processes in different
        layers and thus add the potential energy excess at the snow surface to
        |WSurf|:

        >>> print_values(fluxes.tempssurface[5:])
        0.0

        As to be expected, the energy fluxes of the snow surface neutralise
        each other (within the defined numerical accuracy):

        >>> print_values(fluxes.netradiationsnow -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, 0.0, 0.0, 0.0, 0.0, 0.0

        Through setting parameter |KTSchnee| to |numpy.inf|, we disable
        the iterative search for the correct surface temperature.  Instead,
        method |Return_TempSSurface_V1| simply uses the bulk temperature of
        the snow layer as its surface temperature and sets |WSurf| so that
        the energy gain of the snow surface is zero:

        >>> ktschnee(inf)
        >>> for hru in range(6):
        ...     _ = model.return_tempssurface_v1(hru)
        >>> fluxes.tempssurface
        tempssurface(nan, -2.0, -2.0, -50.0, -200.0, -2.0)
        >>> fluxes.wsurf
        wsurf(0.0, 137.892846, 127.892846, -495.403823, -1835.208545, -52.107154)
        >>> print_values(fluxes.netradiationsnow -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, 0.0, 0.0, 0.0, 0.0, 0.0
    """

    SUBMETHODS = (Return_EnergyGainSnowSurface_V1,)
    CONTROLPARAMETERS = (
        lland_control.Lnk,
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.KTSchnee,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_states.WAeS,
        lland_aides.TempS,
        lland_aides.RLAtm,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.WSensSnow,
        lland_fluxes.WLatSnow,
        lland_fluxes.NetLongwaveRadiationSnow,
        lland_fluxes.NetRadiationSnow,
        lland_fluxes.WSurf,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if sta.waes[k] > 0.0:
            if modelutils.isinf(con.ktschnee):
                model.idx_hru = k
                model.return_energygainsnowsurface_v1(aid.temps[k])
                flu.wsurf[k] = (
                    flu.wsenssnow[k] + flu.wlatsnow[k] - flu.netradiationsnow[k]
                )
            else:
                model.idx_hru = k
                model.pegasustempssurface.find_x(-50.0, 0.0, -100.0, 0.0, 0.0, 1e-8, 10)
                flu.wsurf[k] -= model.return_energygainsnowsurface_v1(
                    flu.tempssurface[k]
                )
        else:
            flu.tempssurface[k] = modelutils.nan
            flu.saturationvapourpressuresnow[k] = 0.0
            flu.wsenssnow[k] = 0.0
            flu.wlatsnow[k] = 0.0
            flu.wsurf[k] = 0.0
        return flu.tempssurface[k]


class Return_WSurfInz_V1(modeltools.Method):
    r"""Calculate and return the intercepted snow heat flux |WSurfInz|.

    Basic equation:
      :math:`WSurfInz = WSensInz + WLatInz - NetRadiationInz`

    Note that method |Return_WSurfInz_V1| calls a number of submethods and uses
    their results to update the corresponding sequences.  When calculating
    |SaturationVapourPressureInz| calls method |Return_SaturationVapourPressure_V1|,
    as follows:

      :math:`SaturationVapourPressureInz = Return_SaturationVapourPressure_V1(
      max(TempSInz, TKor)`

    The reason for using the maximum of the intercepted snow temperature (|TempSInz|)
    and the air temperature (|TKor|) is to increase the evaporation of intercepted
    snow (|EvSInz|). See :cite:t:`ref-LARSIM`.

    Example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(1)
        >>> lnk(LAUBW)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> derived.fr(0.5)
        >>> derived.nmblogentries.update()
        >>> derived.moy.update()
        >>> inputs.relativehumidity = 60.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationinz = 20.0
        >>> fluxes.dailysunshineduration = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0
        >>> aides.tempsinz = -6.675053
        >>> aides.rlatm = 200.0

        >>> from hydpy import round_
        >>> round_(model.return_wsurfinz_v1(0))
        21.616068

        >>> fluxes.saturationvapourpressureinz
        saturationvapourpressureinz(4.893489)
        >>> fluxes.netlongwaveradiationinz
        netlongwaveradiationinz(42.94817)
        >>> fluxes.netradiationinz
        netradiationinz(-22.94817)
        >>> fluxes.wsensinz
        wsensinz(-29.400424)
        >>> fluxes.wlatinz
        wlatinz(28.068322)
        >>> fluxes.wsurfinz
        wsurfinz(21.616068)

    Technical checks:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.lland.lland_model import Return_WSurfInz_V1
        >>> print(check_selectedvariables(Return_WSurfInz_V1))
        Possibly missing (REQUIREDSEQUENCES):
            Return_WLatInz_V1: SaturationVapourPressureInz

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = (
        Return_SaturationVapourPressure_V1,
        Return_WLatInz_V1,
        Return_WSensInz_V1,
        Return_NetLongwaveRadiationInz_V1,
        Return_NetRadiation_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationInz,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_aides.TempSInz,
        lland_aides.RLAtm,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SaturationVapourPressureInz,
        lland_fluxes.WSensInz,
        lland_fluxes.WLatInz,
        lland_fluxes.NetLongwaveRadiationInz,
        lland_fluxes.NetRadiationInz,
        lland_fluxes.WSurfInz,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.saturationvapourpressureinz[k] = model.return_saturationvapourpressure_v1(
            max(aid.tempsinz[k], flu.tkor[k])
        )
        flu.wlatinz[k] = model.return_wlatinz_v1(k)
        flu.wsensinz[k] = model.return_wsensinz_v1(k)
        flu.netlongwaveradiationinz[k] = model.return_netlongwaveradiationinz_v1(k)
        flu.netradiationinz[k] = model.return_netradiation_v1(
            flu.netshortwaveradiationinz[k], flu.netlongwaveradiationinz[k]
        )
        flu.wsurfinz[k] = flu.wsensinz[k] + flu.wlatinz[k] - flu.netradiationinz[k]
        return flu.wsurfinz[k]


class Return_BackwardEulerErrorInz_V1(modeltools.Method):
    r"""Calculate and return the "Backward Euler error" regarding the update of
    |ESnowInz| due to the energy flux |WSurfInz|.

    Basic equation:
      :math:`ESnowInz_{old} - esnowinz_{new} - WSurfInz(esnowinz{new})`

    Example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(1)
        >>> lnk(LAUBW)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> derived.fr(0.5)
        >>> derived.nmblogentries.update()
        >>> derived.moy.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.sinz = 120.0
        >>> states.stinz = 100.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationinz = 20.0
        >>> states.esnowinz = -1.0
        >>> fluxes.dailysunshineduration = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0
        >>> aides.rlatm = 200.0

        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_backwardeulererrorinz_v1(-22.6160684))
        0.0

        >>> aides.tempsinz
        tempsinz(-6.675053)
        >>> fluxes.saturationvapourpressureinz
        saturationvapourpressureinz(4.893489)
        >>> fluxes.netlongwaveradiationinz
        netlongwaveradiationinz(42.94817)
        >>> fluxes.netradiationinz
        netradiationinz(-22.94817)
        >>> fluxes.wsensinz
        wsensinz(-29.400424)
        >>> fluxes.wlatinz
        wlatinz(28.068322)
        >>> fluxes.wsurfinz
        wsurfinz(21.616068)

        >>> states.esnowinz
        esnowinz(-1.0)


        >>> states.sinz = 0.0
        >>> round_(model.return_backwardeulererrorinz_v1(-1.8516245536573426))
        nan
        >>> fluxes.wsurfinz
        wsurfinz(21.616068)

    Technical checks:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.lland.lland_model import Return_BackwardEulerErrorInz_V1
        >>> print(check_selectedvariables(Return_BackwardEulerErrorInz_V1))
        Possibly missing (REQUIREDSEQUENCES):
            Return_WLatInz_V1: SaturationVapourPressureInz
            Return_WSensInz_V1: TempSInz
            Return_NetLongwaveRadiationInz_V1: TempSInz
            Return_WSurfInz_V1: TempSInz

    .. testsetup::

        >>> del pub.timegrids
    """

    SUBMETHODS = (
        Return_TempSInz_V1,
        Return_SaturationVapourPressure_V1,
        Return_WLatInz_V1,
        Return_WSensInz_V1,
        Return_NetLongwaveRadiationInz_V1,
        Return_NetRadiation_V1,
        Return_WSurfInz_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
    )
    REQUIREDSEQUENCES = (
        lland_states.SInz,
        lland_states.STInz,
        lland_fluxes.NetShortwaveRadiationInz,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_states.ESnowInz,
        lland_aides.RLAtm,
    )
    RESULTSEQUENCES = (
        lland_aides.TempSInz,
        lland_fluxes.SaturationVapourPressureInz,
        lland_fluxes.WSensInz,
        lland_fluxes.WLatInz,
        lland_fluxes.NetLongwaveRadiationInz,
        lland_fluxes.NetRadiationInz,
        lland_fluxes.WSurfInz,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        esnowinz: float,
    ) -> float:
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        k = model.idx_hru
        if sta.sinz[k] > 0.0:
            d_esnowinz_old = sta.esnowinz[k]
            sta.esnowinz[k] = esnowinz
            aid.tempsinz[k] = model.return_tempsinz_v1(k)
            sta.esnowinz[k] = d_esnowinz_old
            return d_esnowinz_old - esnowinz - model.return_wsurfinz_v1(k)
        return modelutils.nan


class Return_BackwardEulerError_V1(modeltools.Method):
    """Calculate and return the "Backward Euler error" regarding the
    update of |ESnow| due to the energy fluxes |WG| and |WSurf|
    (:cite:t:`ref-LARSIM` based on :cite:t:`ref-LUBW2006b`, modified).

    Basic equation:
      :math:`ESnow_{old} - esnow_{new} + WG(esnow{new}) - WSurf(esnow{new})`

    Method |Return_BackwardEulerError_V1| does not calculate any hydrologically
    meaningfull property.  It is just a technical means to update the energy
    content of the snow layer with running into instability issues.  See the
    documentation on method |Update_ESnow_V1| for further information.

    Example:

        Method |Return_BackwardEulerError_V1| relies on multiple submethods
        with different requirements.  Hence, we first need to specify a lot
        of input data (see the documentation on the different submethods for
        further information):

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> derived.nmblogentries.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 12.0
        >>> states.wats = 10.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationsnow = 20.0
        >>> states.esnow = -1.0
        >>> fluxes.tz = 0.0
        >>> aides.rlatm = 200.0

        Under the defined conditions the "correct" next value of |ESnow|,
        when following the Backward Euler approach, is approximately
        -2.36 Wd/m²:

        >>> ktschnee(inf)
        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_backwardeulererror_v1(-2.3582799))
        0.0

        As a side-effect, method |Return_BackwardEulerError_V1| calculates
        the following flux sequences for the given amount of energy:

        >>> aides.temps
        temps(-6.96038)
        >>> fluxes.tempssurface
        tempssurface(-6.96038)
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(3.619445)
        >>> fluxes.netlongwaveradiationsnow
        netlongwaveradiationsnow(84.673816)
        >>> fluxes.netradiationsnow
        netradiationsnow(-64.673816)
        >>> fluxes.wsenssnow
        wsenssnow(-31.683041)
        >>> fluxes.wlatsnow
        wlatsnow(10.129785)
        >>> fluxes.wsurf
        wsurf(43.120561)
        >>> fluxes.wg
        wg(41.762281)

        Note that the original value of |ESnow| remains unchanged, to allow
        for calling method |Return_BackwardEulerError_V1| multiple times
        during a root search without the need for an external reset:

        >>> states.esnow
        esnow(-1.0)

        In the above example, |KTSchnee| is set to |numpy.inf|, which is
        why |TempSSurface| is identical with |TempS|.  After setting the
        common value of 5 W/m²/K, the surface temperature is
        calculated by another, embeded iteration approach (see method
        |Return_TempSSurface_V1|).  Hence, the values of |TempSSurface|
        and |TempS| differ and the energy amount of -2.36 Wd/m² is
        not correct anymore:

        >>> ktschnee(5.0)
        >>> round_(model.return_backwardeulererror_v1(-2.3582799))
        32.808687
        >>> aides.temps
        temps(-6.96038)
        >>> fluxes.tempssurface
        tempssurface(-9.022755)
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(3.080429)
        >>> fluxes.netlongwaveradiationsnow
        netlongwaveradiationsnow(75.953474)
        >>> fluxes.netradiationsnow
        netradiationsnow(-55.953474)
        >>> fluxes.wsenssnow
        wsenssnow(-48.182039)
        >>> fluxes.wlatsnow
        wlatsnow(2.540439)
        >>> fluxes.wsurf
        wsurf(10.311874)
        >>> fluxes.wg
        wg(41.762281)
        >>> states.esnow
        esnow(-1.0)

        If there is no snow-cover, it makes little sense to call method
        |Return_BackwardEulerError_V1|.  For savety, we let it then
        return a |numpy.nan| value:

        >>> states.waes = 0.0
        >>> round_(model.return_backwardeulererror_v1(-2.3582799))
        nan
        >>> fluxes.wsurf
        wsurf(10.311874)
    """

    SUBMETHODS = (
        Return_TempS_V1,
        Return_WG_V1,
        Return_TempSSurface_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.Lnk,
        lland_control.KTSchnee,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
        lland_fixed.Z,
        lland_fixed.LambdaG,
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
    )
    REQUIREDSEQUENCES = (
        lland_states.WAeS,
        lland_states.WATS,
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.TZ,
        lland_fluxes.ActualVapourPressure,
        lland_states.ESnow,
        lland_aides.TempS,
        lland_aides.RLAtm,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.WSensSnow,
        lland_fluxes.WLatSnow,
        lland_fluxes.NetLongwaveRadiationSnow,
        lland_fluxes.NetRadiationSnow,
        lland_fluxes.WSurf,
        lland_fluxes.WG,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        esnow: float,
    ) -> float:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        k = model.idx_hru
        if sta.waes[k] > 0.0:
            d_esnow_old = sta.esnow[k]
            sta.esnow[k] = esnow
            aid.temps[k] = model.return_temps_v1(k)
            sta.esnow[k] = d_esnow_old
            model.return_tempssurface_v1(k)
            flu.wg[k] = model.return_wg_v1(k)
            return d_esnow_old - esnow + flu.wg[k] - flu.wsurf[k]
        return modelutils.nan


class Update_ESnowInz_V1(modeltools.Method):
    """Update the thermal energy content of the intercepted snow with regard to the
    energy fluxes from the atmosphere (except the one related to the heat content of
    precipitation).

    Basic equation:
      :math:`\\frac{dESnow}{dt} = - WSurf`

    Example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(LAUBW)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> derived.fr(0.5)
        >>> derived.nmblogentries.update()
        >>> derived.moy.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.sinz = 0.0, 120.0, 12.0, 1.2, 0.12, 0.012, 1.2e-6, 1.2e-12
        >>> states.stinz = 0.0, 100.0, 12.0, 1.0, 0.10, 0.010, 1.0e-6, 1.0e-12
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationinz = 20.0
        >>> states.esnowinz = -1.0
        >>> aides.rlatm = 200.0

        >>> model.update_esnowinz_v1()
        >>> states.esnowinz
        esnowinz(0.0, -22.616068, -2.514108, -0.300877, -0.030179, -0.003019,
                 0.0, 0.0)
        >>> aides.tempsinz
        tempsinz(nan, -6.675053, -8.661041, -8.880269, -8.907091, -8.909782,
                 -8.910081, -8.910081)

        >>> esnowinz = states.esnowinz.values.copy()
        >>> states.esnowinz = -1.0
        >>> errors = []
        >>> for hru in range(8):
        ...     model.idx_hru = hru
        ...     errors.append(model.return_backwardeulererrorinz_v1(esnowinz[hru]))
        >>> from hydpy import print_values
        >>> print_values(errors)
        nan, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    Technical checks:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.lland.lland_model import Update_ESnowInz_V1
        >>> print(check_selectedvariables(Update_ESnowInz_V1))
        Possibly missing (REQUIREDSEQUENCES):
            Return_WSurfInz_V1: TempSInz

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = (
        Return_ESnowInz_V1,
        Return_BackwardEulerErrorInz_V1,
        Return_WSurfInz_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Turb0,
        lland_control.Turb1,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationInz,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_states.STInz,
        lland_states.SInz,
        lland_aides.RLAtm,
    )
    UPDATEDSEQUENCES = (lland_states.ESnowInz,)
    RESULTSEQUENCES = (
        lland_aides.TempSInz,
        lland_fluxes.SaturationVapourPressureInz,
        lland_fluxes.WSensInz,
        lland_fluxes.WLatInz,
        lland_fluxes.NetLongwaveRadiationInz,
        lland_fluxes.NetRadiationInz,
        lland_fluxes.WSurfInz,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if sta.sinz[k] > 0.0:
                model.idx_hru = k
                d_esnowinz = sta.esnowinz[k]
                sta.esnowinz[k] = model.pegasusesnowinz.find_x(
                    model.return_esnowinz_v1(k, -30.0),
                    model.return_esnowinz_v1(k, 30.0),
                    model.return_esnowinz_v1(k, -100.0),
                    model.return_esnowinz_v1(k, 100.0),
                    0.0,
                    1e-8,
                    10,
                )
                if sta.esnowinz[k] > 0.0:
                    aid.tempsinz[k] = 0.0
                    sta.esnowinz[k] = d_esnowinz - model.return_wsurfinz_v1(k)
            else:
                sta.esnowinz[k] = 0.0
                aid.tempsinz[k] = modelutils.nan
                flu.netlongwaveradiationinz[k] = 0.0
                flu.netradiationinz[k] = 0.0
                flu.saturationvapourpressureinz[k] = 0.0
                flu.wsensinz[k] = 0.0
                flu.wlatinz[k] = 0.0
                flu.wsurfinz[k] = 0.0


class Update_ESnow_V1(modeltools.Method):
    """Update the thermal energy content of the snow layer with regard to the
    energy fluxes from the soil and the atmosphere (except the one related
    to the heat content of precipitation). :cite:t:`ref-LARSIM` based on
    :cite:t:`ref-LUBW2006b`, modified.

    Basic equation:
      :math:`\\frac{dESnow}{dt} = WG - WSurf`

    For a thin snow cover, small absolute changes in its energy content
    result in extreme temperature changes, which makes the above calculation
    stiff.  Furthermore, the nonlinearity of the term :math:`WSurf(ESnow(t))`
    prevents from finding an analytical solution of the problem.  This is why
    we apply the A-stable Backward Euler method.  Through our simplified
    approach of taking only one variable (|ESnow|) into account, we can solve
    the underlying root finding problem without any need to calculate or
    approximate derivatives.  Speaking plainly, we use the Pegasus iterator
    |PegasusESnow| to find the root of method |Return_BackwardEulerError_V1|
    whenever the surface is snow-covered.

    Example:

        We reuse the configuration of the documentation on method
        |Return_BackwardEulerError_V1|, except that we prepare five
        hydrological response units:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(ACKER)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> ktschnee(inf)
        >>> derived.nmblogentries.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 0.0, 120.0, 12.0, 1.2, 0.12, 0.012, 1.2e-6, 1.2e-12
        >>> states.wats = 0.0, 100.0, 12.0, 1.0, 0.10, 0.010, 1.0e-6, 1.0e-12
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationsnow = 20.0
        >>> states.esnow = -1.0
        >>> fluxes.tz = 0.0
        >>> aides.rlatm = 200.0

        For the first, snow-free response unit, the energy content of the
        snow layer is zero.  For the other response units we see that the
        energy content decreases with decreasing snow thickness (This
        result is intuitively clear, but requires iteration in very different
        orders of magnitudes.  We hope, our implementation works always
        well.  Please tell us, if you encounter any cases where it does not):

        >>> model.update_esnow_v1()
        >>> states.esnow
        esnow(0.0, -20.789871, -2.024799, -0.239061, -0.023939, -0.002394, 0.0,
              0.0)
        >>> aides.temps
        temps(nan, -6.136057, -6.975386, -7.055793, -7.065486, -7.066457,
              -7.066565, -7.066565)
        >>> fluxes.tempssurface
        tempssurface(nan, -6.136057, -6.975386, -7.055793, -7.065486, -7.066457,
                     -7.066565, -7.066565)

        As to be expected, the requirement of the Backward Euler method
        is approximetely fullfilled for each response unit:

        >>> esnow = states.esnow.values.copy()
        >>> states.esnow = -1.0
        >>> errors = []
        >>> for hru in range(8):
        ...     model.idx_hru = hru
        ...     errors.append(model.return_backwardeulererror_v1(esnow[hru]))
        >>> from hydpy import print_values
        >>> print_values(errors)
        nan, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        The following example repeats the above one, but enables the
        iterative adjustment of the snow surface temperature, which
        is embeded into the iterative adjustment of the energy content
        of the snow layer:

        >>> ktschnee(5.0)
        >>> model.update_esnow_v1()
        >>> states.esnow
        esnow(0.0, -9.695862, -1.085682, -0.130026, -0.013043, -0.001305, 0.0,
              0.0)
        >>> aides.temps
        temps(nan, -2.861699, -3.740149, -3.837669, -3.849607, -3.850805,
              -3.850938, -3.850938)
        >>> fluxes.tempssurface
        tempssurface(nan, -8.034911, -8.245463, -8.268877, -8.271743, -8.272031,
                     -8.272063, -8.272063)

        The resulting energy amounts are, again, the "correct" ones:

        >>> esnow = states.esnow.values.copy()
        >>> states.esnow = -1.0
        >>> errors = []
        >>> for hru in range(8):
        ...     model.idx_hru = hru
        ...     errors.append(model.return_backwardeulererror_v1(esnow[hru]))
        >>> print_values(errors)
        nan, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    """

    SUBMETHODS = (
        Return_ESnow_V1,
        Return_TempSSurface_V1,
        Return_WG_V1,
        Return_BackwardEulerError_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.KTSchnee,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
        lland_fixed.Z,
        lland_fixed.LambdaG,
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.TZ,
        lland_states.WATS,
        lland_states.WAeS,
        lland_aides.TempS,
        lland_aides.RLAtm,
    )
    UPDATEDSEQUENCES = (lland_states.ESnow,)
    RESULTSEQUENCES = (
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.TempSSurface,
        lland_fluxes.WSensSnow,
        lland_fluxes.WLatSnow,
        lland_fluxes.NetLongwaveRadiationSnow,
        lland_fluxes.NetRadiationSnow,
        lland_fluxes.WSurf,
        lland_fluxes.WG,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.0:
                model.idx_hru = k
                d_esnow = sta.esnow[k]
                sta.esnow[k] = model.pegasusesnow.find_x(
                    model.return_esnow_v1(k, -30.0),
                    model.return_esnow_v1(k, 30.0),
                    model.return_esnow_v1(k, -100.0),
                    model.return_esnow_v1(k, 100.0),
                    0.0,
                    1e-8,
                    10,
                )
                if sta.esnow[k] > 0.0:
                    aid.temps[k] = 0.0
                    flu.tempssurface[k] = model.return_tempssurface(k)
                    flu.wg[k] = model.return_wg_v1(k)
                    sta.esnow[k] = d_esnow + flu.wg[k] - flu.wsurf[k]
            else:
                sta.esnow[k] = 0.0
                aid.temps[k] = modelutils.nan
                flu.tempssurface[k] = modelutils.nan
                flu.netlongwaveradiationsnow[k] = 0.0
                flu.netradiationsnow[k] = 0.0
                flu.saturationvapourpressuresnow[k] = 0.0
                flu.wsenssnow[k] = 0.0
                flu.wlatsnow[k] = 0.0
                flu.wsurf[k] = 0.0


class Calc_SchmPot_V1(modeltools.Method):
    """Calculate the potential snow melt according to the day degree method.

    Basic equation:
      :math:`SchmPot = max\\left(\\frac{WGTF + WNied}{RSchmelz}, 0\\right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(2)
        >>> fluxes.wgtf = 20.0
        >>> fluxes.wnied = 10.0, 20.0
        >>> model.calc_schmpot_v1()
        >>> fluxes.schmpot
        schmpot(3.88024, 5.173653)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_fluxes.WGTF,
        lland_fluxes.WNied,
    )
    RESULTSEQUENCES = (lland_fluxes.SchmPot,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.schmpot[k] = max((flu.wgtf[k] + flu.wnied[k]) / fix.rschmelz, 0.0)


class Calc_SchmPot_V2(modeltools.Method):
    """Calculate the potential snow melt according to the heat content of the
    snow layer.

    Basic equation:
      :math:`SchmPot = max\\left(\\frac{ESnow}{RSchmelz}, 0\\right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(4)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.esnow = nan, 100.0, 50.0, -50.0
        >>> model.calc_schmpot_v2()
        >>> fluxes.schmpot
        schmpot(0.0, 12.934132, 6.467066, 0.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_states.ESnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (lland_fluxes.SchmPot,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.0:
                flu.schmpot[k] = max(sta.esnow[k] / fix.rschmelz, 0.0)
            else:
                flu.schmpot[k] = 0.0


class Calc_GefrPot_V1(modeltools.Method):
    """Calculate the potential refreezing within the snow layer according
    to the thermal energy content of the snow layer.

    Basic equation:
      :math:`GefrPot = max\\left(-\\frac{ESnow}{RSchmelz}, 0\\right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(4)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.esnow = nan, -100.0, -50.0, 50.0
        >>> model.calc_gefrpot_v1()
        >>> fluxes.gefrpot
        gefrpot(0.0, 12.934132, 6.467066, 0.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_states.ESnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (lland_fluxes.GefrPot,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0:
                flu.gefrpot[k] = max(-sta.esnow[k] / fix.rschmelz, 0)
            else:
                flu.gefrpot[k] = 0.0


class Calc_Schm_WATS_V1(modeltools.Method):
    """Calculate the actual amount of water melting within the snow layer.

    Basic equations:

      :math:`\\frac{dW\\!ATS}{dt} = -Schm`

      .. math::
        Schm = \\begin{cases}
        SchmPot
        &|\\
        WATS > 0
        \\\\
        0
        &|\\
        WATS = 0
        \\end{cases}


    Examples:

        We initialise two water (|FLUSS| and |SEE|) and four arable land
        (|ACKER|) HRUs.  We assume the same values for the initial amount
        of frozen water (|WATS|) and the frozen part of stand precipitation
        (|SBes|), but different values for potential snowmelt (|SchmPot|):

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> states.wats = 0.0, 0.0, 2.0, 2.0, 2.0, 2.0
        >>> fluxes.schmpot = 1.0, 1.0, 0.0, 1.0, 3.0, 5.0
        >>> model.calc_schm_wats_v1()
        >>> states.wats
        wats(0.0, 0.0, 2.0, 1.0, 0.0, 0.0)
        >>> fluxes.schm
        schm(0.0, 0.0, 0.0, 1.0, 2.0, 2.0)

        Actual melt is either limited by potential melt or the available frozen
        water, which is the sum of initial frozen water and the frozen part
        of stand precipitation.
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (lland_fluxes.SchmPot,)
    RESULTSEQUENCES = (lland_fluxes.Schm,)
    UPDATEDSEQUENCES = (lland_states.WATS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.schm[k] = 0.0
            else:
                flu.schm[k] = min(flu.schmpot[k], sta.wats[k])
                sta.wats[k] -= flu.schm[k]


class Calc_Gefr_WATS_V1(modeltools.Method):
    """Calculate the actual amount of water melting within the snow layer.

    Basic equations:
      :math:`\\frac{dGefr}{dt} = -Gefr`

      .. math::
        Gefr = \\begin{cases}
        GefrPot
        &|\\
        WAeS - WATS > 0
        \\\\
        0
        &|\\
        WAeS - WATS = 0
        \\end{cases}

    Examples:

        We initialise two water (|FLUSS| and |SEE|) and four arable land
        (|ACKER|) HRUs.  We assume the same values for the initial amount
        of frozen water (|WATS|) and the frozen part of stand precipitation
        (|SBes|), but different values for potential snowmelt (|SchmPot|):

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> refreezeflag(True)
        >>> states.wats = 0.0, 0.0, 2.0, 2.0, 2.0, 2.0
        >>> states.waes = 0.0, 0.0, 4.0, 4.0, 4.0, 4.0
        >>> fluxes.gefrpot = 1.0, 1.0, 0.0, 1.0, 3.0, 5.0
        >>> model.calc_gefr_wats_v1()
        >>> states.wats
        wats(0.0, 0.0, 2.0, 3.0, 4.0, 4.0)
        >>> fluxes.gefr
        gefr(0.0, 0.0, 0.0, 1.0, 2.0, 2.0)

        If we deactivate the refreezing flag, liquid water in the snow layer
        does not refreeze. |Gefr| is set to 0 and |WATS| does not change:

        >>> refreezeflag(False)
        >>> model.calc_gefr_wats_v1()
        >>> states.wats
        wats(0.0, 0.0, 2.0, 3.0, 4.0, 4.0)
        >>> fluxes.gefr
        gefr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        Actual refreezing is either limited by potential refreezing or the
        available water.
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.RefreezeFlag,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.GefrPot,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (lland_fluxes.Gefr,)
    UPDATEDSEQUENCES = (lland_states.WATS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE) or not con.refreezeflag:
                flu.gefr[k] = 0.0
            else:
                flu.gefr[k] = min(flu.gefrpot[k], (sta.waes[k] - sta.wats[k]))
                sta.wats[k] += flu.gefr[k]


class Update_WaDa_WAeS_V1(modeltools.Method):
    """Update the actual water release from and the liquid water content of
    the snow layer due to melting.

    Basic equations:
      :math:`WaDa_{new} = WaDa_{old} + \\Delta`

      :math:`WAeS_{new} = WAeS_{old} - \\Delta`

      :math:`\\Delta = max(WAeS-PWMax \\cdot WATS, 0)`

    Examples:

        We set the threshold parameter |PWMax| for each of the seven
        initialised hydrological response units to two.  Thus, the snow
        cover can hold as much liquid water as it contains frozen water.
        For the first three response units, which represent water
        surfaces, snow-related processes are ignored and the original
        values of |WaDa| and |WAeS| remain unchanged. For all other land
        use classes (of which we select |ACKER| arbitrarily), method
        |Update_WaDa_WAeS_V1| passes only the amount of |WAeS| exceeding
        the actual snow holding capacity to |WaDa|:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> lnk(WASSER, FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> pwmax(2.0)
        >>> states.wats = 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0
        >>> states.waes = 1.0, 1.0, 1.0, 0.0, 1.0, 2.0, 3.0
        >>> fluxes.wada = 1.0
        >>> model.update_wada_waes_v1()
        >>> states.waes
        waes(1.0, 1.0, 1.0, 0.0, 1.0, 2.0, 2.0)
        >>> fluxes.wada
        wada(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (lland_states.WATS,)
    UPDATEDSEQUENCES = (
        lland_states.WAeS,
        lland_fluxes.WaDa,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] not in (WASSER, FLUSS, SEE):
                d_wada_corr = max(sta.waes[k] - con.pwmax[k] * sta.wats[k], 0.0)
                flu.wada[k] += d_wada_corr
                sta.waes[k] -= d_wada_corr


class Update_ESnow_V2(modeltools.Method):
    """Update the thermal energy content of the snow layer regarding snow
    melt and refreezing.

    Basic equation:
      :math:`\\frac{dESNOW}{dt} = RSchmelz \\cdot (Gefr - Schm)`

    Examples:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> lnk(WASSER, FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> fluxes.gefr = 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 4.0
        >>> fluxes.schm = 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 4.0
        >>> states.esnow = 20.0, 20.0, 20.0, 20.0, -40.0, 30.925926, 0.0
        >>> states.waes = 1.0, 1.0, 1.0, 0.0, 5.0, 5.0, 10.0
        >>> model.update_esnow_v2()
        >>> states.esnow
        esnow(0.0, 0.0, 0.0, 0.0, -9.074074, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    FIXEDPARAMETERS = (lland_fixed.RSchmelz,)
    REQUIREDSEQUENCES = (
        lland_fluxes.Gefr,
        lland_fluxes.Schm,
        lland_states.WAeS,
    )
    UPDATEDSEQUENCES = (lland_states.ESnow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if (con.lnk[k] in (WASSER, FLUSS, SEE)) or (sta.waes[k] <= 0.0):
                sta.esnow[k] = 0.0
            else:
                sta.esnow[k] += fix.rschmelz * (flu.gefr[k] - flu.schm[k])


class Calc_SFF_V1(modeltools.Method):
    r"""Calculate the ratio between frozen water and total water within
    the top soil layer according to :cite:t:`ref-LARSIM`.

    Basic equations:
      :math:`SFF = min \left( max \left(
      1 - \frac{EBdn}{BoWa2Z \cdot RSchmelz}, 0 \right), 1 \right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(9)
        >>> lnk(VERS, WASSER, FLUSS, SEE, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> states.ebdn(0.0, 0.0, 0.0, 0.0, 620.0, 618.519, 309.259, 0.0, -1.0)
        >>> model.calc_sff_v1()
        >>> fluxes.sff
        sff(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    FIXEDPARAMETERS = (
        lland_fixed.BoWa2Z,
        lland_fixed.RSchmelz,
    )
    REQUIREDSEQUENCES = (lland_states.EBdn,)
    RESULTSEQUENCES = (lland_fluxes.SFF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.sff[k] = 0.0
            else:
                d_sff = 1.0 - sta.ebdn[k] / (fix.bowa2z[k] * fix.rschmelz)
                flu.sff[k] = min(max(d_sff, 0.0), 1.0)


class Calc_FVG_V1(modeltools.Method):
    """Calculate the degree of frost sealing of the soil according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`FVG = min\\bigl(FVF \\cdot SFF^{BSFF}, 1\\bigl)`

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(7)
        >>> lnk(VERS, WASSER, FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> fvf(0.8)
        >>> bsff(2.0)
        >>> fluxes.sff(1.0, 1.0, 1.0, 1.0, 0.0, 0.5, 1.0)
        >>> model.calc_fvg_v1()
        >>> fluxes.fvg
        fvg(0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.8)

        The calculated degree of frost sealing does never exceed one,
        even when defining |FVF| values larger one:

        >>> fvf(1.6)
        >>> model.calc_fvg_v1()
        >>> fluxes.fvg
        fvg(0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 1.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.BSFF,
        lland_control.FVF,
    )
    REQUIREDSEQUENCES = (lland_fluxes.SFF,)
    RESULTSEQUENCES = (lland_fluxes.FVG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.fvg[k] = 0.0
            else:
                flu.fvg[k] = min(con.fvf * flu.sff[k] ** con.bsff, 1.0)


class Calc_EvB_AETModel_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    soil evapotranspiration.

    Examples:

        We build an example based on |evap_minhas|:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep("1h")
        >>> nhru(5)
        >>> lnk(VERS, ACKER, ACKER, MISCHW, WASSER)
        >>> ft(1.0)
        >>> fhru(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> wmax(100.0)
        >>> with model.add_aetmodel_v1("evap_minhas"):
        ...     dissefactor(5.0)

        |Calc_EvB_AETModel_V1| stores the flux returned by the submodel without any
        modifications:

        >>> states.bowa = 0.0, 0.0, 50.0, 100.0, 0.0
        >>> model.aetmodel.sequences.fluxes.potentialevapotranspiration = 5.0
        >>> model.aetmodel.sequences.fluxes.interceptionevaporation = 3.0
        >>> model.calc_evb_v1()
        >>> fluxes.evb
        evb(0.0, 0.0, 1.717962, 2.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    RESULTSEQUENCES = (lland_fluxes.EvB,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_soilevapotranspiration()
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.evb[k] = 0.0
            else:
                flu.evb[k] = submodel.get_soilevapotranspiration(k)


class Calc_EvB_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate soil
    evapotranspiration."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_EvB_AETModel_V1,)
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    RESULTSEQUENCES = (lland_fluxes.EvB,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_evb_aetmodel_v1(cast(aetinterfaces.AETModel_V1, model.aetmodel))
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_EvS_WAeS_WATS_V1(modeltools.Method):
    """Calculate the evaporation from the snow layer, if any exists, and
    update the snow cover accordingly.

    Basic equations:
      :math:`WAeS_{new} = f \\cdot WAeS_{old}`

      :math:`WATS_{new} = f \\cdot WATS_{old}`

      :math:`f = \\frac{WAeS-EvS}{WAeS}`

      :math:`EvS = max\\left(\\frac{WLatSnow}{L}, WAeS\\right)`

    Example:

        The first hydrological response unit shows that method
        |Calc_EvS_WAeS_WATS_V1| does calculate condensation and deposition
        if a negative flux of latent heat suggests so.  We define the
        relative amounts of condensation and deposition so that the fraction
        between the frozen and the total water content of the snow layer
        does not change.  The same holds for vaporisation and sublimation,
        as shown by response units to to seven.  Note that method
        |Calc_EvS_WAeS_WATS_V1| prevents negative water contents but does
        not prevent to high liquid water contents, which eventually needs
        to be corrected by another method called subsequentially.  The last
        response unit shows that method |Calc_EvS_WAeS_WATS_V1| sets |EvS|,
        |WATS| and |WAeS| to zero for water areas:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(ACKER, ACKER, ACKER, ACKER, ACKER, ACKER, ACKER, WASSER)
        >>> fluxes.wlatsnow = -25.0, 0.0, 50.0, 90.0, 150.0, 150.0, 150.0, 150.0
        >>> states.waes = 2.0, 2.0, 2.0, 2.0, 2.0, 1.5, 0.0, 2.0
        >>> states.wats = 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 1.0
        >>> model.calc_evs_waes_wats_v1()
        >>> fluxes.evs
        evs(-0.404881, 0.0, 0.809762, 1.457572, 2.0, 1.5, 0.0, 0.0)
        >>> states.waes
        waes(2.404881, 2.0, 1.190238, 0.542428, 0.0, 0.0, 0.0, 0.0)
        >>> states.wats
        wats(1.202441, 1.0, 0.595119, 0.271214, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    FIXEDPARAMETERS = (lland_fixed.LWE,)
    REQUIREDSEQUENCES = (lland_fluxes.WLatSnow,)
    RESULTSEQUENCES = (lland_fluxes.EvS,)
    UPDATEDSEQUENCES = (
        lland_states.WAeS,
        lland_states.WATS,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, SEE, FLUSS) or (sta.waes[k] <= 0.0):
                flu.evs[k] = 0.0
                sta.waes[k] = 0.0
                sta.wats[k] = 0.0
            else:
                flu.evs[k] = min(flu.wlatsnow[k] / fix.lwe, sta.waes[k])
                d_frac = (sta.waes[k] - flu.evs[k]) / sta.waes[k]
                sta.waes[k] *= d_frac
                sta.wats[k] *= d_frac


class Calc_EvI_Inzp_AETModel_V1(modeltools.Method):
    r"""Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water.

    Basic equation:
      :math:`\frac{dInzp_i}{dt} = -EvI_i`

    Examples:

        We build an example based on |evap_minhas| for calculating interception
        evaporation, which uses |evap_io| for querying potential evapotranspiration:

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep("1h")
        >>> nhru(5)
        >>> lnk(VERS, ACKER, ACKER, MISCHW, WASSER)
        >>> ft(1.0)
        >>> fhru(0.05, 0.1, 0.2, 0.3, 0.35)
        >>> derived.kinz.jun = 3.0
        >>> wmax(50.0)
        >>> derived.moy.shape = 1
        >>> derived.moy(5)
        >>> fluxes.nbes = 0.5
        >>> with model.add_aetmodel_v1("evap_minhas"):
        ...     with model.add_petmodel_v1("evap_io"):
        ...         evapotranspirationfactor(0.6, 0.8, 1.0, 1.2, 1.4)
        ...         inputs.referenceevapotranspiration = 1.0

        For non-water areas, |Calc_EvI_Inzp_AETModel_V1| uses the flux returned by the
        submodel to adjust |Inzp|:

        >>> states.inzp = 2.0
        >>> model.calc_evi_inzp_v1()
        >>> fluxes.evi
        evi(0.6, 0.8, 1.0, 1.2, 1.4)
        >>> states.inzp
        inzp(1.4, 1.2, 1.0, 0.8, 0.0)
        >>> fluxes.nbes
        nbes(0.5, 0.5, 0.5, 0.5, 0.5)

        |Calc_EvI_Inzp_AETModel_V1| eventually reduces |EvI| so that |Inzp| does not
        become negative:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = 5.0
        >>> states.inzp = 2.0
        >>> model.calc_evi_inzp_v1()
        >>> fluxes.evi
        evi(2.0, 2.0, 2.0, 2.0, 7.0)
        >>> states.inzp
        inzp(0.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.5, 0.5, 0.5, 0.5, 0.5)

        In contrast, |Calc_EvI_Inzp_AETModel_V1| does not reduce negative |EvI| values
        (condensation) that cause an overshoot of the interception storage capacity:

        >>> model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration = -3.0
        >>> states.inzp = 2.0
        >>> model.calc_evi_inzp_v1()
        >>> fluxes.evi
        evi(-1.8, -2.4, -3.0, -3.6, -4.2)
        >>> states.inzp
        inzp(3.8, 4.4, 5.0, 5.6, 0.0)
        >>> fluxes.nbes
        nbes(0.5, 0.5, 0.5, 0.5, 0.5)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    UPDATEDSEQUENCES = (lland_states.Inzp,)
    RESULTSEQUENCES = (lland_fluxes.EvI,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: aetinterfaces.AETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        submodel.determine_interceptionevaporation()
        submodel.determine_waterevaporation()
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.evi[k] = submodel.get_waterevaporation(k)
                sta.inzp[k] = 0.0
            else:
                flu.evi[k] = min(submodel.get_interceptionevaporation(k), sta.inzp[k])
                sta.inzp[k] -= flu.evi[k]


class Calc_EvI_Inzp_V1(modeltools.Method):
    """Let a submodel that follows the |AETModel_V1| submodel interface calculate
    interception evaporation and adjust the amount of intercepted water."""

    SUBMODELINTERFACES = (aetinterfaces.AETModel_V1,)
    SUBMETHODS = (Calc_EvI_Inzp_AETModel_V1,)
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    UPDATEDSEQUENCES = (lland_states.Inzp,)
    RESULTSEQUENCES = (lland_fluxes.EvI,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.aetmodel_typeid == 1:
            model.calc_evi_inzp_aetmodel_v1(
                cast(aetinterfaces.AETModel_V1, model.aetmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_QKap_V1(modeltools.Method):
    """Calculate the capillary rise.

    Basic equation:
      :math:`QKap = KapMax \\cdot min\\left(max\\left(1 -
      \\frac{BoWa-KapGrenz_1}{KapGrenz_2-KapGrenz_1}, 0 \\right), 1 \\right)`

    Examples:

        We prepare six hydrological response units of landuse type |ACKER|
        with different soil water contents:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(6)
        >>> lnk(ACKER)
        >>> wmax(100.0)
        >>> states.bowa(0.0, 20.0, 40.0, 60.0, 80.0, 100.0)

        The maximum capillary rise is 3 mm/d (which is 1.5 mm for the
        actual simulation time step of 12 hours):

        >>> kapmax(3.0)

        Please read the documentation on parameter |KapGrenz|, which gives
        some examples on how to configure the capillary rise thresholds.
        The following examples show the calculation results for with and
        without a range of linear transition:

        >>> kapgrenz(20.0, 80.0)
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(1.5, 1.5, 1.0, 0.5, 0.0, 0.0)

        >>> kapgrenz(40.0, 40.0)
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(1.5, 1.5, 1.5, 0.0, 0.0, 0.0)

        You are allowed to set the lower threshold to values lower than
        zero and the larger one to values larger than |WMax|:

        >>> kapgrenz(-50.0, 150.0)
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(1.125, 0.975, 0.825, 0.675, 0.525, 0.375)

        For water areas and sealed surfaces, capillary rise is always zero:

        >>> lnk(WASSER, FLUSS, SEE, VERS, VERS, VERS)
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.KapMax,
        lland_control.KapGrenz,
        lland_control.WMax,
    )
    REQUIREDSEQUENCES = (lland_states.BoWa,)
    RESULTSEQUENCES = (lland_fluxes.QKap,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if (con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or (con.wmax[k] <= 0.0):
                flu.qkap[k] = 0.0
            elif sta.bowa[k] <= con.kapgrenz[k, 0]:
                flu.qkap[k] = con.kapmax[k]
            elif sta.bowa[k] <= con.kapgrenz[k, 1]:
                flu.qkap[k] = con.kapmax[k] * (
                    1.0
                    - (sta.bowa[k] - con.kapgrenz[k, 0])
                    / (con.kapgrenz[k, 1] - con.kapgrenz[k, 0])
                )
            else:
                flu.qkap[k] = 0


class Calc_QBB_V1(modeltools.Method):
    """Calculate the amount of base flow released from the soil.

    Basic equations:
      .. math::
        QBB = \\begin{cases}
        0
        &|\\
        BoWa \\leq PWP \\;\\; \\lor \\;\\;
        (BoWa \\leq FK \\;\\; \\land \\;\\; RBeta)
        \\\\
        Beta_{eff}  \\cdot (BoWa - PWP)
        &|\\
        BoWa > FK \\;\\; \\lor \\;\\;
        (BoWa > PWP \\;\\; \\land \\;\\; \\overline{RBeta})
        \\end{cases}

      .. math::
        Beta_{eff} = \\begin{cases}
        Beta
        &|\\
        BoWa \\leq FK
        \\\\
        Beta \\cdot \\left(1+(FBeta-1)\\cdot\\frac{BoWa-FK}{WMax-FK}\\right)
        &|\\
        BoWa > FK
        \\end{cases}

    Examples:

        For water and sealed areas, no base flow is calculated (see the
        first three hydrological response units of type |VERS|, |FLUSS|, and
        |SEE|).  No principal distinction is made between the remaining land
        use classes (arable land |ACKER| has been selected for the last five
        HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> beta(0.04)
        >>> fbeta(2.0)
        >>> wmax(0.0, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, 200.0)
        >>> fk(70.0)
        >>> pwp(10.0)
        >>> rbeta(False)

        Note the time dependence of parameter |Beta|:

        >>> beta
        beta(0.04)
        >>> beta.values
        array([0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02])

        In the first example, the actual soil water content |BoWa| is set
        to low values.  For values below the threshold |PWP|, no percolation
        occurs.  Above |PWP| (but below |FK|), |QBB| increases linearly by
        an amount defined by parameter |Beta|:

        >>> states.bowa = 20.0, 20.0, 20.0, 0.0, 0.0, 10.0, 20.0, 20.0
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2)

        Note that for the last two response units the same amount of base
        flow generation is determined, in spite of the fact that both exhibit
        different relative soil moistures.

        If we set the reduction option |RBeta| to |False|, |QBB| is
        reduced to zero as long as |BoWa| does not exceed |FK|:

        >>> rbeta(True)
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        In the second example, we set the actual soil water content |BoWa|
        to high values.  For values below threshold |FK|, the discussion above
        remains valid.  For values above |FK|, percolation shows a nonlinear
        behaviour when factor |FBeta| is set to values larger than one:

        >>> rbeta(False)
        >>> wmax(0.0, 0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 200.0)
        >>> fk(70.0)
        >>> pwp(10.0)
        >>> states.bowa = 0.0, 0.0, 0.0, 60.0, 70.0, 80.0, 100.0, 200.0
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 1.0, 1.2, 1.866667, 3.6, 7.6)

        >>> rbeta(True)
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 0.0, 0.0, 1.866667, 3.6, 7.6)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.Beta,
        lland_control.FBeta,
        lland_control.RBeta,
        lland_control.PWP,
        lland_control.FK,
    )
    REQUIREDSEQUENCES = (lland_states.BoWa,)
    RESULTSEQUENCES = (lland_fluxes.QBB,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if (
                (con.lnk[k] in (VERS, WASSER, FLUSS, SEE))
                or (sta.bowa[k] <= con.pwp[k])
                or (con.wmax[k] <= 0.0)
            ):
                flu.qbb[k] = 0.0
            elif sta.bowa[k] <= con.fk[k]:
                if con.rbeta:
                    flu.qbb[k] = 0.0
                else:
                    flu.qbb[k] = con.beta[k] * (sta.bowa[k] - con.pwp[k])
            else:
                flu.qbb[k] = (
                    con.beta[k]
                    * (sta.bowa[k] - con.pwp[k])
                    * (
                        1.0
                        + (con.fbeta[k] - 1.0)
                        * (sta.bowa[k] - con.fk[k])
                        / (con.wmax[k] - con.fk[k])
                    )
                )


class Calc_QIB1_V1(modeltools.Method):
    """Calculate the first inflow component released from the soil.

    Basic equation:
      :math:`QIB1 = DMin \\cdot \\frac{BoWa}{WMax}`

    Examples:

        For water and sealed areas, no interflow is calculated (the first
        three HRUs are of type |FLUSS|, |SEE|, and |VERS|, respectively).
        No principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last five
        HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> dmax(10.0)
        >>> dmin(4.0)
        >>> wmax(101.0, 101.0, 101.0, 0.0, 101.0, 101.0, 101.0, 202.0)
        >>> pwp(10.0)
        >>> states.bowa = 10.1, 10.1, 10.1, 0.0, 0.0, 10.0, 10.1, 10.1

        Note the time dependence of parameter |DMin|:

        >>> dmin
        dmin(4.0)
        >>> dmin.values
        array([2., 2., 2., 2., 2., 2., 2., 2.])

        Compared to the calculation of |QBB|, the following results show
        some relevant differences:

        >>> model.calc_qib1_v1()
        >>> fluxes.qib1
        qib1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.1)

        Firstly, as demonstrated with the help of the seventh and the
        eight HRU, the generation of the first interflow component |QIB1|
        depends on relative soil moisture.  Secondly, as demonstrated with
        the help the sixth and seventh HRU, it starts abruptly whenever
        the slightest exceedance of the threshold  parameter |PWP| occurs.
        Such sharp discontinuouties are a potential source of trouble.
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.DMin,
        lland_control.WMax,
        lland_control.PWP,
    )
    REQUIREDSEQUENCES = (lland_states.BoWa,)
    RESULTSEQUENCES = (lland_fluxes.QIB1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if (con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or (
                sta.bowa[k] <= con.pwp[k]
            ):
                flu.qib1[k] = 0.0
            else:
                flu.qib1[k] = con.dmin[k] * (sta.bowa[k] / con.wmax[k])


class Calc_QIB2_V1(modeltools.Method):
    """Calculate the second inflow component released from the soil.

    Basic equation:
      :math:`QIB2 = (DMax-DMin) \\cdot
      \\left(\\frac{BoWa-FK}{WMax-FK}\\right)^\\frac{3}{2}`

    Examples:

        For water and sealed areas, no interflow is calculated (the first
        three HRUs are of type |FLUSS|, |SEE|, and |VERS|, respectively).
        No principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last
        five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> dmax(10.0)
        >>> dmin(4.0)
        >>> wmax(100.0, 100.0, 100.0, 50.0, 100.0, 100.0, 100.0, 200.0)
        >>> fk(50.0)
        >>> states.bowa = 100.0, 100.0, 100.0, 50.1, 50.0, 75.0, 100.0, 100.0

        Note the time dependence of parameters |DMin| (see the example above)
        and |DMax|:

        >>> dmax
        dmax(10.0)
        >>> dmax.values
        array([5., 5., 5., 5., 5., 5., 5., 5.])

        The following results show that he calculation of |QIB2| both
        resembles those of |QBB| and |QIB1| in some regards:

        >>> model.calc_qib2_v1()
        >>> fluxes.qib2
        qib2(0.0, 0.0, 0.0, 0.0, 0.0, 1.06066, 3.0, 0.57735)

        In the given example, the maximum rate of total interflow
        generation is 5 mm/12h (parameter |DMax|).  For the seventh zone,
        which contains a saturated soil, the value calculated for the
        second interflow component (|QIB2|) is 3 mm/h.  The "missing"
        value of 2 mm/12h is be calculated by method |Calc_QIB1_V1|.

        (The fourth zone, which is slightly oversaturated, is only intended
        to demonstrate that zero division due to |WMax| = |FK| is circumvented.)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.DMax,
        lland_control.DMin,
        lland_control.FK,
    )
    REQUIREDSEQUENCES = (lland_states.BoWa,)
    RESULTSEQUENCES = (lland_fluxes.QIB2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if (
                (con.lnk[k] in (VERS, WASSER, FLUSS, SEE))
                or (sta.bowa[k] <= con.fk[k])
                or (con.wmax[k] <= con.fk[k])
            ):
                flu.qib2[k] = 0.0
            else:
                flu.qib2[k] = (con.dmax[k] - con.dmin[k]) * (
                    (sta.bowa[k] - con.fk[k]) / (con.wmax[k] - con.fk[k])
                ) ** 1.5


class Calc_QDB_V1(modeltools.Method):
    """Calculate direct runoff released from the soil.

    Basic equations:
      .. math::
        QDB = \\begin{cases}
        max\\bigl(Exz, 0\\bigl)
        &|\\
        SfA \\leq 0
        \\\\
        max\\bigl(Exz + WMax \\cdot SfA^{BSf+1}, 0\\bigl)
        &|\\
        SfA > 0
        \\end{cases}

      :math:`SFA = \\left(1 - \\frac{BoWa}{WMax}\\right)^\\frac{1}{BSf+1} -
      \\frac{WaDa}{(BSf+1) \\cdot WMax}`

      :math:`Exz = (BoWa + WaDa) - WMax`

    Examples:

        For water areas (|FLUSS| and |SEE|), sealed areas (|VERS|), and
        areas without any soil storage capacity, all water is completely
        routed as direct runoff |QDB| (see the first four HRUs).  No
        principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last five
        HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(9)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> bsf(0.4)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0)
        >>> fluxes.wada = 10.0
        >>> states.bowa = (
        ...     100.0, 100.0, 100.0, 0.0, -0.1, 0.0, 50.0, 100.0, 100.1)
        >>> model.calc_qdb_v1()
        >>> fluxes.qdb
        qdb(10.0, 10.0, 10.0, 10.0, 0.142039, 0.144959, 1.993649, 10.0, 10.1)

        With the common |BSf| value of 0.4, the discharge coefficient
        increases more or less exponentially with soil moisture.
        For soil moisture values slightly below zero or above usable
        field capacity, plausible amounts of generated direct runoff
        are ensured.
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.BSf,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WaDa,
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (lland_fluxes.QDB,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.qdb[k] = 0.0
            elif (con.lnk[k] in (VERS, FLUSS, SEE)) or (con.wmax[k] <= 0.0):
                flu.qdb[k] = flu.wada[k]
            else:
                if sta.bowa[k] < con.wmax[k]:
                    d_sfa = (1.0 - sta.bowa[k] / con.wmax[k]) ** (
                        1.0 / (con.bsf[k] + 1.0)
                    ) - (flu.wada[k] / ((con.bsf[k] + 1.0) * con.wmax[k]))
                else:
                    d_sfa = 0.0
                d_exz = sta.bowa[k] + flu.wada[k] - con.wmax[k]
                flu.qdb[k] = d_exz
                if d_sfa > 0.0:
                    flu.qdb[k] += d_sfa ** (con.bsf[k] + 1.0) * con.wmax[k]
                flu.qdb[k] = max(flu.qdb[k], 0.0)


class Update_QDB_V1(modeltools.Method):
    """Update the direct runoff according to the degree of frost sealing.

    Basic equation:
      :math:`QDB_{updated} = QDB + FVG \\cdot (WaDa - QDB)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.qdb(5.0)
        >>> fluxes.wada(10.0)
        >>> fluxes.fvg(0.2)
        >>> model.update_qdb_v1()
        >>> fluxes.qdb
        qdb(6.0, 6.0, 6.0)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_fluxes.WaDa,
        lland_fluxes.FVG,
    )
    UPDATEDSEQUENCES = (lland_fluxes.QDB,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.qdb[k] += flu.fvg[k] * (flu.wada[k] - flu.qdb[k])


class Calc_BoWa_Default_V1(modeltools.Method):
    r"""Update the soil moisture and (if necessary) correct the fluxes to be added or
    subtracted.

    Basic equations:
       :math:`\frac{dBoWa}{dt} = WaDa + Qkap - EvB - QBB - QIB1 - QIB2 - QDB`

       :math:`0 \leq BoWa \leq WMax`

    Examples:

        For water areas and sealed surfaces, we can set soil moisture (|BoWa|) to zero
        and do not need to perform any flux corrections:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(4)
        >>> lnk(FLUSS, SEE, WASSER, VERS)
        >>> states.bowa = 100.0
        >>> model.calc_bowa_default_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 0.0, 0.0)

        We make no principal distinction between the remaining land use classes and
        select arable land (|ACKER|) for the following examples.

        To prevent soil water contents from exceeding |WMax|, we might need to decrease
        |WaDa| and |QKap|:

        >>> lnk(ACKER)
        >>> wmax(100.0)
        >>> states.bowa = 90.0
        >>> fluxes.wada = 0.0, 5.0, 10.0, 15.0
        >>> fluxes.qkap = 10.0
        >>> fluxes.evb = 5.0
        >>> fluxes.qbb = 0.0
        >>> fluxes.qib1 = 0.0
        >>> fluxes.qib2 = 0.0
        >>> fluxes.qdb = 0.0
        >>> model.calc_bowa_default_v1()
        >>> states.bowa
        bowa(95.0, 100.0, 100.0, 100.0)
        >>> fluxes.wada
        wada(0.0, 5.0, 2.5, 6.0)
        >>> fluxes.qkap
        qkap(10.0, 10.0, 2.5, 4.0)
        >>> fluxes.evb
        evb(5.0, 5.0, 5.0, 5.0)

        Additionally, to prevent storage overflows, we might need to decrease |EvB| if
        it is negative (when condensation increases the soil water storage):

        >>> states.bowa = 90.0
        >>> fluxes.wada = 0.0, 5.0, 10.0, 15.0
        >>> fluxes.qkap = 2.5
        >>> fluxes.evb = -2.5
        >>> model.calc_bowa_default_v1()
        >>> states.bowa
        bowa(95.0, 100.0, 100.0, 100.0)
        >>> fluxes.wada
        wada(0.0, 5.0, 3.333333, 7.5)
        >>> fluxes.qkap
        qkap(2.5, 2.5, 0.833333, 1.25)
        >>> fluxes.evb
        evb(-2.5, -2.5, -0.833333, -1.25)

        To prevent negative |BoWa| values, we might need to decrease |QBB|, |QIB2|,
        |QIB1|, |QBB|, and |EvB|:

        >>> states.bowa = 10.0
        >>> fluxes.wada = 0.0
        >>> fluxes.qkap = 0.0
        >>> fluxes.evb = 0.0, 5.0, 10.0, 15.0
        >>> fluxes.qbb = 1.25
        >>> fluxes.qib1 = 1.25
        >>> fluxes.qib2 = 1.25
        >>> fluxes.qdb = 1.25
        >>> model.calc_bowa_default_v1()
        >>> states.bowa
        bowa(5.0, 0.0, 0.0, 0.0)
        >>> fluxes.evb
        evb(0.0, 5.0, 6.666667, 7.5)
        >>> fluxes.qbb
        qbb(1.25, 1.25, 0.833333, 0.625)
        >>> fluxes.qib1
        qib1(1.25, 1.25, 0.833333, 0.625)
        >>> fluxes.qib2
        qib2(1.25, 1.25, 0.833333, 0.625)
        >>> fluxes.qdb
        qdb(1.25, 1.25, 0.833333, 0.625)

        We do not modify negative |EvB| values (condensation) when preventing negative
        |BoWa| values:

        >>> states.bowa = 10.0
        >>> fluxes.evb = -15.0, -10.0, -5.0, 0.0
        >>> fluxes.qbb = 5.0
        >>> fluxes.qib1 = 5.0
        >>> fluxes.qib2 = 5.0
        >>> fluxes.qdb = 5.0
        >>> model.calc_bowa_default_v1()
        >>> states.bowa
        bowa(5.0, 0.0, 0.0, 0.0)
        >>> fluxes.evb
        evb(-15.0, -10.0, -5.0, 0.0)
        >>> fluxes.qbb
        qbb(5.0, 5.0, 3.75, 2.5)
        >>> fluxes.qib1
        qib1(5.0, 5.0, 3.75, 2.5)
        >>> fluxes.qib2
        qib2(5.0, 5.0, 3.75, 2.5)
        >>> fluxes.qdb
        qdb(5.0, 5.0, 3.75, 2.5)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
    )
    REQUIREDSEQUENCES = (lland_fluxes.WaDa,)
    UPDATEDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvB,
        lland_fluxes.QBB,
        lland_fluxes.QIB1,
        lland_fluxes.QIB2,
        lland_fluxes.QDB,
        lland_fluxes.QKap,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                sta.bowa[k] = 0.0
            else:
                d_decr = flu.qbb[k] + flu.qib1[k] + flu.qib2[k] + flu.qdb[k]
                d_incr = flu.wada[k] + flu.qkap[k]
                if flu.evb[k] > 0.0:
                    d_decr += flu.evb[k]
                else:
                    d_incr -= flu.evb[k]
                if d_decr > sta.bowa[k] + d_incr:
                    d_rvl = (sta.bowa[k] + d_incr) / d_decr
                    if flu.evb[k] > 0.0:
                        flu.evb[k] *= d_rvl
                    flu.qbb[k] *= d_rvl
                    flu.qib1[k] *= d_rvl
                    flu.qib2[k] *= d_rvl
                    flu.qdb[k] *= d_rvl
                    sta.bowa[k] = 0.0
                else:
                    sta.bowa[k] = (sta.bowa[k] + d_incr) - d_decr
                    if sta.bowa[k] > con.wmax[k]:
                        d_factor = (sta.bowa[k] - con.wmax[k]) / d_incr
                        if flu.evb[k] < 0.0:
                            flu.evb[k] *= d_factor
                        flu.wada[k] *= d_factor
                        flu.qkap[k] *= d_factor
                        sta.bowa[k] = con.wmax[k]


class Calc_BoWa_SoilModel_V1(modeltools.Method):
    r"""Apply a submodel following the |SoilModel_V1| interface to include additional
    direct runoff and groundwater recharge components into the soil moisture update.

    Examples:

        We prepare a |lland| model instance consisting of four hydrological response
        units, which will serve as the main model:

        >>> from hydpy.models.lland_v1 import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nhru(4)

        As an example, we select |ga_garto_submodel1| as the submodel.  We define its
        parameter values like in the initial examples of the documentation on
        |ga_garto_submodel1| and its stand-alone counterpart |ga_garto| (soil type
        loam) but prepare - analogue to the main model's setting - four soil
        compartments.  The two first compartments have a soil depth of 1.0 m ("deep
        soils") and the two last of 0.1 m ("flat soils"):

        >>> from hydpy import prepare_model, pub
        >>> with model.add_soilmodel_v1("ga_garto_submodel1"):
        ...     nmbsoils(4)
        ...     nmbbins(3)
        ...     with pub.options.parameterstep("1s"):
        ...         dt(1.0)
        ...     sealed(False)
        ...     soildepth(1000.0, 1000.0, 100.0, 100.0)
        ...     residualmoisture(0.027)
        ...     saturationmoisture(0.434)
        ...     saturatedconductivity(13.2)
        ...     poresizedistribution(0.252)
        ...     airentrypotential(111.5)

        For water areas and sealed surfaces, |lland| does not apply its submodel and
        just sets |BoWa| to zero:

        >>> lnk(FLUSS, SEE, WASSER, VERS)
        >>> states.bowa = 100.0
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 0.0, 0.0)

        |Calc_BoWa_SoilModel_V1| works the same for all other land use types.  We
        randomly select |ACKER| (arable land):

        >>> lnk(ACKER)

        The water reaching the soil routine (|WaDa|) is 40 mm/h for each response unit
        in all examples:

        >>> fluxes.wada = 40.0

        We define a function that will help us to execute the following test runs.  It
        sets the values of the main model's flux sequences for direct runoff (|QDB|),
        both interflow components (|QIB2| and |QIB1|), base flow (|QBB|),
        evapotranspiration (|EvB|), and capillary rise (|QKap|).  Direct runoff is
        predefined to 40 mm/h for the first (deep) and third (flat) response unit and
        0 mm/h for the second (deep) and fourth (flat) response unit.  The other flux
        sequences' values are customisable (default value 0 mm/h).  The initial
        relative soil moisture (|ga_states.Moisture|) is 10 %, which makes an absolute
        soil water content (|BoWa|) of 100 mm for the first two and 10 mm for the last
        two response units.  After applying method |Calc_BoWa_SoilModel_V1|, our test
        function checks for possible water balance violations and (if it does not find
        any) prints the updated soil moisture content and the eventually adjusted flux
        sequences's values:

        >>> garto = model.soilmodel
        >>> from numpy import array, round
        >>> from hydpy.core.objecttools import repr_values
        >>> def check(qib2=0, qib1=0, qbb=0, evb=0, qkap=0):
        ...     fluxes.qdb = 40.0, 0.0, 40, 0.0
        ...     fluxes.qib2 = qib2
        ...     fluxes.qib1 = qib1
        ...     fluxes.qbb = qbb
        ...     fluxes.evb = evb
        ...     fluxes.qkap = qkap
        ...     garto.sequences.states.moisture = 0.1
        ...     garto.sequences.states.frontdepth = 0.0
        ...     garto.sequences.states.moisturechange = 0.0
        ...     old_bowa = array([garto.get_soilwatercontent(k) for k in range(4)])
        ...     model.calc_bowa_v1()
        ...     new_bowa = states.bowa.values.copy()
        ...     delta = (fluxes.wada + fluxes.qkap - fluxes.qdb - fluxes.qib2
        ...              - fluxes.qib1 - fluxes.qbb - fluxes.evb)
        ...     assert all(round(new_bowa, 11) == round(old_bowa + delta, 11))
        ...     print("bowa:", repr_values(states.bowa))
        ...     print("qdb:", repr_values(fluxes.qdb))
        ...     print("qib2:", repr_values(fluxes.qib2))
        ...     print("qib1:", repr_values(fluxes.qib1))
        ...     print("qbb:", repr_values(fluxes.qbb))
        ...     print("evb:", repr_values(fluxes.evb))
        ...     print("qkap:", repr_values(fluxes.qkap))

        If |WaDa| (the potential direct runoff amount) and |QDB| (the already
        calculated direct runoff amount) are equal, like for the hydrological response
        units one and three, there is no water left that could infiltrate into the
        soil.  For zero previously calculated direct runoff, |WaDa| could infiltrate
        completely.  Here, about 38.9 mm enter the deep soil, and the remainder
        (1.1 mm) becomes direct runoff (compare with example
        :ref:`ga_garto_5h_1000mm`).  The flat soil becomes completely saturated so that
        there is a larger amount of direct runoff (4.5 mm) and also a considerable
        amount of groundwater recharge (2.1 mm) (see example :ref:`ga_garto_5h_100mm`):

        >>> check()
        bowa: 100.0, 138.896943, 10.0, 43.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 0.0, 0.0, 0.0, 0.0
        qib1: 0.0, 0.0, 0.0, 0.0
        qbb: 0.0, 0.0, 0.0, 2.097333
        evb: 0.0, 0.0, 0.0, 0.0
        qkap: 0.0, 0.0, 0.0, 0.0

        |Calc_BoWa_SoilModel_V1| adds externally defined capillary rise after
        performing the infiltration and percolation routine.  Hence, passing a
        capillary rise value of 1.0 mm does not result in direct runoff or groundwater
        recharge differences compared to the previous example  Note that the fourths
        soil compartment cannot receive capillary rise due to its saturation.  Hence,
        |Calc_BoWa_SoilModel_V1| corrects |QKap| to zero:

        >>> check(qkap=1.0)
        bowa: 101.0, 139.896943, 11.0, 43.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 0.0, 0.0, 0.0, 0.0
        qib1: 0.0, 0.0, 0.0, 0.0
        qbb: 0.0, 0.0, 0.0, 2.097333
        evb: 0.0, 0.0, 0.0, 0.0
        qkap: 1.0, 1.0, 1.0, 0.0

        Passing an (extremely unrealistic) capillary rise of 40.0 mm requires also a
        reduction for the third soil compartment:

        >>> check(qkap=40.0)
        bowa: 140.0, 178.896943, 43.4, 43.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 0.0, 0.0, 0.0, 0.0
        qib1: 0.0, 0.0, 0.0, 0.0
        qbb: 0.0, 0.0, 0.0, 2.097333
        evb: 0.0, 0.0, 0.0, 0.0
        qkap: 40.0, 40.0, 33.4, 0.0

        |Calc_BoWa_SoilModel_V1| allows for negative evapotranspiration values and
        handles them like capillary rise.  If their sum exceeds the available soil
        water storage, |Calc_BoWa_SoilModel_V1| reduces both by the same factor:

        >>> check(qkap=30.0, evb=-10.0)
        bowa: 140.0, 178.896943, 43.4, 43.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 0.0, 0.0, 0.0, 0.0
        qib1: 0.0, 0.0, 0.0, 0.0
        qbb: 0.0, 0.0, 0.0, 2.097333
        evb: -10.0, -10.0, -8.35, 0.0
        qkap: 30.0, 30.0, 25.05, 0.0

        The last process triggered by |Calc_BoWa_SoilModel_V1| is removing of a
        defined water demand.  This demand is the sum of both interflow components,
        base flow, and evapotranspiration:

        >>> check(qib2=6.0, qib1=3.0, qbb=2.0, evb=1.0)
        bowa: 88.0, 126.896943, 2.7, 31.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 6.0, 6.0, 3.65, 6.0
        qib1: 3.0, 3.0, 1.825, 3.0
        qbb: 2.0, 2.0, 1.216667, 4.097333
        evb: 1.0, 1.0, 0.608333, 1.0
        qkap: 0.0, 0.0, 0.0, 0.0

        For soils that do not contain enough water to satisfy the whole demand,
        |Calc_BoWa_SoilModel_V1| reduces all mentioned components by the same factor:

        >>> check(qib2=12.0, qib1=6.0, qbb=4.0, evb=2.0)
        bowa: 76.0, 114.896943, 2.7, 19.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 12.0, 12.0, 3.65, 12.0
        qib1: 6.0, 6.0, 1.825, 6.0
        qbb: 4.0, 4.0, 1.216667, 6.097333
        evb: 2.0, 2.0, 0.608333, 2.0
        qkap: 0.0, 0.0, 0.0, 0.0

        Negative evapotranspiration values cannot contribute to soil overdrying.
        Hence, |Calc_BoWa_SoilModel_V1| does not modify negative evapotranspiration
        values when reducing the "real" loss terms:

        >>> check(qib2=6.0, qib1=3.0, qbb=2.0, evb=-1.0, qkap=1.0)
        bowa: 91.0, 129.896943, 2.7, 32.4
        qdb: 40.0, 1.103057, 40.0, 4.502667
        qib2: 6.0, 6.0, 5.072727, 6.0
        qib1: 3.0, 3.0, 2.536364, 3.0
        qbb: 2.0, 2.0, 1.690909, 4.097333
        evb: -1.0, -1.0, -1.0, 0.0
        qkap: 1.0, 1.0, 1.0, 0.0
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (lland_fluxes.WaDa,)
    UPDATEDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvB,
        lland_fluxes.QBB,
        lland_fluxes.QIB1,
        lland_fluxes.QIB2,
        lland_fluxes.QDB,
        lland_fluxes.QKap,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: soilinterfaces.SoilModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                sta.bowa[k] = 0.0
            else:
                # infiltration and percolation
                submodel.set_initialsurfacewater(k, flu.wada[k])
                submodel.set_actualsurfacewater(k, flu.wada[k] - flu.qdb[k])
                submodel.set_soilwatersupply(k, 0.0)
                submodel.set_soilwaterdemand(k, 0.0)
                submodel.execute_infiltration(k)
                infiltration: float = submodel.get_infiltration(k)
                flu.qdb[k] += (flu.wada[k] - flu.qdb[k]) - infiltration
                qbb_soilmodel: float = submodel.get_percolation(k)
                # capillary rise and negative evapotranspiration
                supply: float = flu.qkap[k]
                if flu.evb[k] < 0.0:
                    supply -= flu.evb[k]
                submodel.set_soilwatersupply(k, supply)
                submodel.add_soilwater(k)
                addition: float = submodel.get_soilwateraddition(k)
                if addition < supply:
                    factor: float = addition / supply
                    flu.qkap[k] *= factor
                    if flu.evb[k] < 0.0:
                        flu.evb[k] *= factor
                # LARSIM-type baseflow, interflow, and positive evaporation
                demand: float = flu.qbb[k] + flu.qib1[k] + flu.qib2[k]
                if flu.evb[k] > 0.0:
                    demand += flu.evb[k]
                submodel.set_soilwaterdemand(k, demand)
                submodel.remove_soilwater(k)
                removal: float = submodel.get_soilwaterremoval(k)
                if removal < demand:
                    factor = removal / demand
                    flu.qbb[k] *= factor
                    flu.qib1[k] *= factor
                    flu.qib2[k] *= factor
                    if flu.evb[k] > 0.0:
                        flu.evb[k] *= factor
                # sync soil moisture
                sta.bowa[k] = submodel.get_soilwatercontent(k)
                flu.qbb[k] += qbb_soilmodel


class Calc_BoWa_V1(modeltools.Method):
    """Update the soil moisture.

    |Calc_BoWa_V1| serves as a switch method.  Its behaviour depends on whether the
    user activates a soil submodel following the |SoilModel_V1| interface or not.  If
    not, |Calc_BoWa_V1| applies |Calc_BoWa_Default_V1| to perform a "simple" soil
    moisture update.  If so, |Calc_BoWa_V1| uses |Calc_BoWa_SoilModel_V1| to include
    additional direct runoff and groundwater recharge components into the soil moisture
    update.  See the documentation of the mentioned submethods for more information.
    """

    SUBMODELINTERFACES = (soilinterfaces.SoilModel_V1,)
    SUBMETHODS = (
        Calc_BoWa_Default_V1,
        Calc_BoWa_SoilModel_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
    )
    REQUIREDSEQUENCES = (lland_fluxes.WaDa,)
    UPDATEDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvB,
        lland_fluxes.QBB,
        lland_fluxes.QIB1,
        lland_fluxes.QIB2,
        lland_fluxes.QDB,
        lland_fluxes.QKap,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.soilmodel is None:
            model.calc_bowa_default_v1()
        elif model.soilmodel_typeid == 1:
            model.calc_bowa_soilmodel_v1(
                cast(soilinterfaces.SoilModel_V1, model.soilmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.soilmodel)


class Calc_QBGZ_V1(modeltools.Method):
    r"""Aggregate the amount of base flow released by all "soil type" HRUs and the
    "net precipitation" above water areas of type |SEE|.

    Water areas of type |SEE| are assumed to be directly connected with groundwater,
    but not with the stream network.  This is modelled by adding their (positive or
    negative) "net input" (|NKor|-|EvI|) to the "percolation output" of the soil
    containing HRUs.

    Basic equation:
       :math:`QBGZ = \Sigma \bigl( FHRU \cdot \bigl( QBB - Qkap \bigl) \bigl) +
       \Sigma \bigl (FHRU \cdot \bigl( NKor_{SEE} - EvI_{SEE} \bigl) \bigl)`

    Examples:

        The first example shows that |QBGZ| is the area weighted sum of |QBB| from
        "soil type" HRUs like arable land (|ACKER|) and of |NKor|-|EvI| from water
        areas of type |SEE|.  All other water areas (|WASSER| and |FLUSS|) and also
        sealed surfaces (|VERS|) have no impact on |QBGZ|:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER, ACKER, VERS, WASSER, FLUSS, SEE)
        >>> fhru(0.1, 0.2, 0.1, 0.1, 0.1, 0.4)
        >>> fluxes.qbb = 2., 4.0, 300.0, 300.0, 300.0, 300.0
        >>> fluxes.qkap = 1., 2.0, 150.0, 150.0, 150.0, 150.0
        >>> fluxes.nkor = 200.0, 200.0, 200.0, 200.0, 200.0, 20.0
        >>> fluxes.evi = 100.0, 100.0, 100.0, 100.0, 100.0, 10.0
        >>> model.calc_qbgz_v1()
        >>> fluxes.qbgz
        qbgz(4.5)

        The second example shows that large evaporation values above a HRU of type
        |SEE| can result in negative values of |QBGZ|:

        >>> fluxes.evi[5] = 30
        >>> model.calc_qbgz_v1()
        >>> fluxes.qbgz
        qbgz(-3.5)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NKor,
        lland_fluxes.EvI,
        lland_fluxes.QBB,
        lland_fluxes.QKap,
    )
    RESULTSEQUENCES = (lland_fluxes.QBGZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qbgz = 0.0
        for k in range(con.nhru):
            if con.lnk[k] == SEE:
                flu.qbgz += con.fhru[k] * (flu.nkor[k] - flu.evi[k])
            elif con.lnk[k] not in (WASSER, FLUSS, VERS):
                flu.qbgz += con.fhru[k] * (flu.qbb[k] - flu.qkap[k])


class Calc_QIGZ1_V1(modeltools.Method):
    r"""Aggregate the amount of the first interflow component released by all HRUs.

    Basic equation:
       :math:`QIGZ1 = \Sigma(FHRU \cdot QIB1)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fhru(0.75, 0.25)
        >>> fluxes.qib1 = 1.0, 5.0
        >>> model.calc_qigz1_v1()
        >>> fluxes.qigz1
        qigz1(2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (lland_fluxes.QIB1,)
    RESULTSEQUENCES = (lland_fluxes.QIGZ1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qigz1 = 0.0
        for k in range(con.nhru):
            flu.qigz1 += con.fhru[k] * flu.qib1[k]


class Calc_QIGZ2_V1(modeltools.Method):
    r"""Aggregate the amount of the second interflow component released by all HRUs.

    Basic equation:
       :math:`QIGZ2 = \Sigma(FHRU \cdot QIB2)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fhru(0.75, 0.25)
        >>> fluxes.qib2 = 1.0, 5.0
        >>> model.calc_qigz2_v1()
        >>> fluxes.qigz2
        qigz2(2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (lland_fluxes.QIB2,)
    RESULTSEQUENCES = (lland_fluxes.QIGZ2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qigz2 = 0.0
        for k in range(con.nhru):
            flu.qigz2 += con.fhru[k] * flu.qib2[k]


class Calc_QDGZ_V1(modeltools.Method):
    r"""Aggregate the amount of total direct flow released by all HRUs.

    Basic equation:
       :math:`QDGZ = \Sigma \bigl( FHRU \cdot QDB \bigl) +
       \Sigma \bigl (FHRU \cdot \bigl( NKor_{FLUSS} - EvI_{FLUSS} \bigl) \bigl)`

    Examples:

        The first example shows that |QDGZ| is the area weighted sum of |QDB| from
        "land type" HRUs like arable land (|ACKER|) and sealed surfaces (|VERS|) as
        well as of |NKor|-|EvI| from water areas of type |FLUSS|.  Water areas of type
        |WASSER| and |SEE| have no impact on |QDGZ|:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(ACKER, VERS, WASSER, SEE, FLUSS)
        >>> fhru(0.1, 0.2, 0.1, 0.2, 0.4)
        >>> fluxes.qdb = 2., 4.0, 300.0, 300.0, 300.0
        >>> fluxes.nkor = 200.0, 200.0, 200.0, 200.0, 20.0
        >>> fluxes.evi = 100.0, 100.0, 100.0, 100.0, 10.0
        >>> model.calc_qdgz_v1()
        >>> fluxes.qdgz
        qdgz(5.0)

        The second example shows that large evaporation values above a HRU of type
        |FLUSS| can result in negative values of |QDGZ|:

        >>> fluxes.evi[4] = 30
        >>> model.calc_qdgz_v1()
        >>> fluxes.qdgz
        qdgz(-3.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NKor,
        lland_fluxes.EvI,
        lland_fluxes.QDB,
    )
    RESULTSEQUENCES = (lland_fluxes.QDGZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qdgz = 0.0
        for k in range(con.nhru):
            if con.lnk[k] == FLUSS:
                flu.qdgz += con.fhru[k] * (flu.nkor[k] - flu.evi[k])
            elif con.lnk[k] not in (WASSER, SEE):
                flu.qdgz += con.fhru[k] * flu.qdb[k]


class Calc_QDGZ1_QDGZ2_V1(modeltools.Method):
    r"""Separate total direct flow into a slower and a faster component.

    Basic equations:
       :math:`QDGZ2 = \frac{(QDGZ - A2)^2}{QDGZ + A1 - A2}`

       :math:`QDGZ1 = QDGZ - QDGZ2`

    Examples:

        We borrowed the formula for calculating the amount of the faster component of
        direct flow from the well-known curve number approach.  Parameter |A2| would be
        the initial loss and parameter |A1| the maximum storage, but one should not
        take this analogy too literally.

        With the value of parameter |A1| set to zero, parameter |A2| defines the
        maximum amount of "slow" direct runoff per time step:

        >>> from hydpy.models.lland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> a1(0.0)

        Let us set the value of |A2| to 4 mm/d, which is 2 mm/12h concerning the
        selected simulation step size:

        >>> a2(4.0)
        >>> a2
        a2(4.0)
        >>> a2.value
        2.0

        Define a test function and let it calculate |QDGZ1| and |QDGZ1| for values of
        |QDGZ| ranging from -10 to 100 mm/12h:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_qdgz1_qdgz2_v1,
        ...                 last_example=6,
        ...                 parseqs=(fluxes.qdgz, fluxes.qdgz1, fluxes.qdgz2))
        >>> test.nexts.qdgz = -10.0, 0.0, 1.0, 2.0, 3.0, 100.0
        >>> test()
        | ex. |  qdgz | qdgz1 | qdgz2 |
        -------------------------------
        |   1 | -10.0 | -10.0 |   0.0 |
        |   2 |   0.0 |   0.0 |   0.0 |
        |   3 |   1.0 |   1.0 |   0.0 |
        |   4 |   2.0 |   2.0 |   0.0 |
        |   5 |   3.0 |   2.0 |   1.0 |
        |   6 | 100.0 |   2.0 |  98.0 |

        Setting |A2| to zero and |A1| to 4 mm/d (or 2 mm/12h) results in a smoother
        transition:

        >>> a2(0.0)
        >>> a1(4.0)
        >>> test()
        | ex. |  qdgz |    qdgz1 |     qdgz2 |
        --------------------------------------
        |   1 | -10.0 |    -10.0 |       0.0 |
        |   2 |   0.0 |      0.0 |       0.0 |
        |   3 |   1.0 | 0.666667 |  0.333333 |
        |   4 |   2.0 |      1.0 |       1.0 |
        |   5 |   3.0 |      1.2 |       1.8 |
        |   6 | 100.0 | 1.960784 | 98.039216 |

        Alternatively, one can mix these two configurations by setting the values of
        both parameters to 2 mm/h:

        >>> a2(2.0)
        >>> a1(2.0)
        >>> test()
        | ex. |  qdgz |    qdgz1 |    qdgz2 |
        -------------------------------------
        |   1 | -10.0 |    -10.0 |      0.0 |
        |   2 |   0.0 |      0.0 |      0.0 |
        |   3 |   1.0 |      1.0 |      0.0 |
        |   4 |   2.0 |      1.5 |      0.5 |
        |   5 |   3.0 | 1.666667 | 1.333333 |
        |   6 | 100.0 |     1.99 |    98.01 |

        Note the similarity of the results for very high values of total direct flow
        |QDGZ| in all three examples, which converge to the sum of the values of
        parameter |A1| and |A2|, representing the maximum value of `slow` direct flow
        generation per simulation step
    """

    CONTROLPARAMETERS = (
        lland_control.A2,
        lland_control.A1,
    )
    REQUIREDSEQUENCES = (lland_fluxes.QDGZ,)
    RESULTSEQUENCES = (
        lland_fluxes.QDGZ2,
        lland_fluxes.QDGZ1,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if flu.qdgz > con.a2:
            flu.qdgz2 = (flu.qdgz - con.a2) ** 2 / (flu.qdgz + con.a1 - con.a2)
            flu.qdgz1 = flu.qdgz - flu.qdgz2
        else:
            flu.qdgz2 = 0.0
            flu.qdgz1 = flu.qdgz


class Return_SG_V1(modeltools.Method):
    r"""Return the new storage value after applying the analytical solution for the
    linear storage differential equation under the assumption of constant inflow.

    Basic equation:
       :math:`k \cdot qz - (k \cdot qz - s) \cdot exp(-1 / k)`

    Examples:

        The first "normal" test relies on the given basic equation:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_sg_v1(3.0, 1.0, 2.0, 1.0))
        2.417343

        Zero concentration time does not result in zero division errors:

        >>> round_(model.return_sg_v1(0.0, 1.0, 2.0, 1.0))
        0.0

        Also, it is safe to apply infinite concentration time:

        >>> round_(model.return_sg_v1(inf, 1.0, 2.0, 1.0))
        3.0
    """

    @staticmethod
    def __call__(
        model: modeltools.Model, k: float, s: float, qz: float, dt: float
    ) -> float:
        if k <= 0.0:
            return 0.0
        if modelutils.isinf(k):
            return s + qz
        return k * qz - (k * qz - s) * modelutils.exp(-dt / k)


class Calc_QBGA_SBG_V1(modeltools.Method):
    r"""Update the base flow storage and calculate its outflow.

    Basic equations:
       :math:`SBG = Return\_SG\_V1(KB, SBG, QBGZ)`

       :math:`QBGA = SBG_{old} - SBG_{new} + QBGZ`

    Example:

        Method |Calc_QBGA_SBG_V1| relies on the analytical solution of the linear
        storage equation implemented by method |Return_SG_V1|, from which we take the
        following test configuration:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> derived.kb(3.0)
        >>> states.sbg.old = 1.0
        >>> fluxes.qbgz = 2.0
        >>> model.calc_qbga_sbg_v1()
        >>> states.sbg
        sbg(2.417343)
        >>> fluxes.qbga
        qbga(0.582657)
    """

    SUBMETHODS = (Return_SG_V1,)
    DERIVEDPARAMETERS = (lland_derived.KB,)
    REQUIREDSEQUENCES = (lland_fluxes.QBGZ,)
    UPDATEDSEQUENCES = (lland_states.SBG,)
    RESULTSEQUENCES = (lland_fluxes.QBGA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.sbg = model.return_sg_v1(der.kb, old.sbg, flu.qbgz, 1.0)
        flu.qbga = old.sbg - new.sbg + flu.qbgz


class Calc_QBGA_SBG_QBGZ_QDGZ_V1(modeltools.Method):
    r"""Update the base flow storage and calculate its outflow, taking possible
    "groundwater restrictions" into account.

    .. _`issue 87`: https://github.com/hydpy-dev/hydpy/issues/87

    Without active restrictions, method |Calc_QBGA_SBG_QBGZ_QDGZ_V1| works like
    |Calc_QBGA_SBG_V1|.  There are two restrictions, one being volume- and the other
    one rise-related.

    In the "volume-related" case, |Calc_QBGA_SBG_QBGZ_QDGZ_V1| redirects groundwater
    recharge to the direct flow components as soon as the groundwater amount reaches
    its limit (the available aquifer volume), defined by the parameters |VolBMax| and
    |GSBMax|.

    The "rise-related" restriction redirects water in the same direction but reacts to
    a too fast rise of the groundwater table instead of a too high groundwater amount.
    It is a linear interpolation approach, with parameter |GSBGrad1| representing the
    highest possible rise without any reduction of the groundwater inflow and
    |GSBGrad2| representing the rise where groundwater recharge would become zero.

    Conceptually, both restrictions follow :cite:t:`ref-LARSIM` but their
    implementations differ in a way that may lead to relevant differences in the
    results.

    The implementation of |Calc_QBGA_SBG_QBGZ_QDGZ_V1| is quite complex due to a huge
    of edge cases requiring special handling.  See issue `issue 87`_ for a detailed
    discussion of its development and the underlying math (there, you can also report
    edge cases we might not handle well so far).  Here, we give only the basic
    ordinary differential equation solved by |Calc_QBGA_SBG_QBGZ_QDGZ_V1|.

    Basic equation:
      .. math::
        SBG'(t) = \begin{cases}
            0
            &|\
            SBG(t) = GSBMax \cdot VolBMax \ \land \  SBG'(t) > 0
        \\[5pt]
            QBGZ - \frac{SBG(t)}{KB}
            &|\
            (SBG(t) < GSBMax \cdot VolBMax \ \lor \ SBG'(t) \leq 0)
            \ \land \ SBG'(t) \leq GSBGrad1
        \\[5pt]
            \frac{GSBGrad2-SBG'(t)}{GSBGrad2-GSBGrad1} \cdot QBGZ - \frac{SBG(t)}{KB}
            &|\
            (SBG(t) < GSBMax \cdot VolBMax \ \lor \ SBG'(t) \leq 0)
            \ \land\  SBG'(t) > GSBGrad1
        \end{cases}

        Examples:

            To give some context, we start our explanations based on method
            |Calc_QBGA_SBG_V1|:

            >>> from hydpy.models.lland import *
            >>> simulationstep("1d")
            >>> parameterstep("1d")
            >>> derived.kb(10.0)
            >>> states.sbg.old = 5.0
            >>> fluxes.qbgz = 2.0
            >>> model.calc_qbga_sbg_v1()
            >>> states.sbg
            sbg(6.427439)
            >>> fluxes.qbga
            qbga(0.572561)

            The content of the storage for base flow (groundwater amount) increases
            from 5 mm to about 6.43 mm.

            At the beginning of the interval, the increase of the content of the base
            flow storage (groundwater rise) is 1.5 mm/d:

            >>> from hydpy import round_
            >>> round_(fluxes.qbgz - states.sbg.old / derived.kb)
            1.5

            With increasing groundwater amount during the interval, base flow also
            increases, dampening the groundwater rise.  Hence, it is only about 1.36 at
            the end of the interval:

            >>> round_(fluxes.qbgz - states.sbg.new / derived.kb)
            1.357256

            Capturing all branches of |Calc_QBGA_SBG_QBGZ_QDGZ_V1| requires extensive
            testing.  Therefore, we define function `check`, which compares the given
            analytical solution with a numerical approximation of the original ODE and
            performs some balance-related tests (`sm` stands for the maximum
            groundwater amount and `g1` and `g2` for |GSBGrad1| and |GSBGrad2|):

            >>> from numpy import exp
            >>> from scipy.integrate import ode
            >>> def check(sm, g1, g2):
            ...     # update the parameters:
            ...     volbmax(sm)
            ...     gsbgrad1.value = g1
            ...     gsbgrad2.value = g2
            ...     # reset the fluxes (eventually changed by previous calls):
            ...     fluxes.qbgz = 2.0
            ...     fluxes.qdgz = 1.0
            ...     # apply a numerical solver:
            ...     integrator = ode(f_ode)
            ...     _ = integrator.set_integrator("zvode", method="bdf", rtol=1e-10)
            ...     _ = integrator.set_initial_value([min(states.sbg.old, sm), 0.0])
            ...     sbg_est, qbga_est = integrator.integrate(1.0).real
            ...     qbga_est += max(states.sbg.old - sm, 0.0)
            ...     # calculate the analytical solution:
            ...     model.calc_qbga_sbg_qbgz_qdgz_v1()
            ...     # compare the analytical with the numerical solution:
            ...     assert round(states.sbg.new, 6) == round(sbg_est, 6)
            ...     assert round(fluxes.qbga, 6) == round(qbga_est, 6)
            ...     # check water balances:
            ...     assert states.sbg.new == states.sbg.old + fluxes.qbgz - fluxes.qbga
            ...     assert 2.0 + 1.0 == fluxes.qbgz + fluxes.qdgz
            ...     # print the resulting values of all modified sequences:
            ...     print(states.sbg, fluxes.qbga, fluxes.qbgz, fluxes.qdgz, sep=", ")

            Function `check` requires a function that implements the given ODE.  We
            define function `f_ode` for this purpose, which needs lot of special
            casing.  It returns the current groundwater change (inflow minus outflow)
            and the outflow itself. Note that handling :math:`k = \infty` is highly ad
            hoc and only thought to work for the following tests:

            >>> def f_ode(t, x):
            ...     k = derived.kb.value
            ...     z = fluxes.qbgz.value
            ...     sm = control.gsbmax.value * control.volbmax.value
            ...     g1 = control.gsbgrad1.value
            ...     g2 = control.gsbgrad2.value
            ...     s = x[0]
            ...     if s <= 0.0:
            ...         ds = 0.0
            ...     elif s >= sm:
            ...         ds = 0.0
            ...     elif k == 0.0:
            ...         ds = -5e3
            ...     elif z - s / k <= g1:
            ...         ds = z - s / k
            ...     elif g1 == g2:
            ...         ds = g1
            ...     elif numpy.isinf(k):
            ...         ds = g2 / ((g2 - g1) / z + 1.0)
            ...     else:
            ...         ds = (g2 * (s - k * z) - g1 * s) / (k * (g1 - g2 - z))
            ...     if s <= 0.0:
            ...         return [[ds, 0.0]]
            ...     elif k == 0.0:
            ...         return [[ds, 7e3]]
            ...     return [[ds, s / k]]

            We start by demonstrating pure volume-related restrictions.  Therefore, we
            set |GSBMax| to one so that values for `sm` correspond to the highest
            possible groundwater amount:

            >>> gsbmax(1.0)

            If `sm` is higher than the final groundwater amount, applying
            |Calc_QBGA_SBG_QBGZ_QDGZ_V1| leads to the same results as
            |Calc_QBGA_SBG_V1|:

            >>> check(sm=10.0, g1=1.5, g2=2.0)
            sbg(6.427439), qbga(0.572561), qbgz(2.0), qdgz(1.0)

            An active volume-related restriction decreases the groundwater inflow
            (which reduces base flow) and increases the amount of direct runoff:

            >>> check(sm=6.0, g1=1.5, g2=2.0)
            sbg(6.0), qbga(0.5659), qbgz(1.5659), qdgz(1.4341)

            Starting with an already activated volume-related restriction works as
            expected:

            >>> check(sm=5.0, g1=1.5, g2=2.0)
            sbg(5.0), qbga(0.5), qbgz(0.5), qdgz(2.5)

            |Calc_QBGA_SBG_QBGZ_QDGZ_V1| handles possible initial violations of
            volume-related restrictions by adding the excess to base flow:

            >>> check(sm=4.0, g1=1.5, g2=2.0)
            sbg(4.0), qbga(1.4), qbgz(0.4), qdgz(2.6)

            Setting |KB| to |numpy.inf| works (in case someone will ever need it):

            >>> derived.kb(inf)
            >>> check(sm=10.0, g1=inf, g2=inf)
            sbg(7.0), qbga(0.0), qbgz(2.0), qdgz(1.0)
            >>> check(sm=6.0, g1=inf, g2=inf)
            sbg(6.0), qbga(0.0), qbgz(1.0), qdgz(2.0)
            >>> check(sm=5.0, g1=inf, g2=inf)
            sbg(5.0), qbga(0.0), qbgz(0.0), qdgz(3.0)
            >>> check(sm=4.0, g1=inf, g2=inf)
            sbg(4.0), qbga(1.0), qbgz(0.0), qdgz(3.0)

            Next, we demonstrate pure rise-related restrictions.

            If |GSBGrad1| (and subsequently |GSBGrad2|) is not smaller than the initial
            groundwater rise, |Calc_QBGA_SBG_QBGZ_QDGZ_V1| calculates the same results
            as |Calc_QBGA_SBG_V1|:

            >>> derived.kb(10.0)
            >>> check(sm=10.0, g1=1.5, g2=2.0)
            sbg(6.427439), qbga(0.572561), qbgz(2.0), qdgz(1.0)
            >>> check(sm=inf, g1=1.5, g2=2.0)
            sbg(6.427439), qbga(0.572561), qbgz(2.0), qdgz(1.0)

            The following examples deal with a situation where (only) |GSBGrad1| is
            smaller than the groundwater rise at the interval's start and end time:

            >>> check(sm=10.0, g1=1.0, g2=2.0)
            sbg(6.147436), qbga(0.557691), qbgz(1.705127), qdgz(1.294873)
            >>> check(sm=inf, g1=1.0, g2=2.0)
            sbg(6.147436), qbga(0.557691), qbgz(1.705127), qdgz(1.294873)
            >>> check(sm=5.0, g1=1.0, g2=2.0)
            sbg(5.0), qbga(0.5), qbgz(0.5), qdgz(2.5)
            >>> check(sm=4.0, g1=1.0, g2=2.0)
            sbg(4.0), qbga(1.4), qbgz(0.4), qdgz(2.6)

            Now, both |GSBGrad1| and |GSBGrad2| are smaller than the groundwater rise
            at the interval's start and end time:

            >>> check(sm=10.0, g1=0.5, g2=1.0)
            sbg(5.693046), qbga(0.534768), qbgz(1.227814), qdgz(1.772186)
            >>> check(sm=inf, g1=0.5, g2=1.0)
            sbg(5.693046), qbga(0.534768), qbgz(1.227814), qdgz(1.772186)
            >>> check(sm=5.0, g1=0.5, g2=1.0)
            sbg(5.0), qbga(0.5), qbgz(0.5), qdgz(2.5)
            >>> check(sm=4.0, g1=0.5, g2=1.0)
            sbg(4.0), qbga(1.4), qbgz(0.4), qdgz(2.6)

            It is acceptable to set |GSBGrad1| to zero:

            >>> check(sm=10.0, g1=0.0, g2=1.0)
            sbg(5.491758), qbga(0.524725), qbgz(1.016483), qdgz(1.983517)
            >>> derived.kb(0.0)
            >>> check(sm=10.0, g1=0.0, g2=0.0)
            sbg(0.0), qbga(7.0), qbgz(2.0), qdgz(1.0)

            The same holds for setting both |GSBGrad1| and |GSBGrad2| to zero:

            >>> derived.kb(10.0)
            >>> check(sm=10.0, g1=0.0, g2=0.0)
            sbg(5.0), qbga(0.5), qbgz(0.5), qdgz(2.5)

            Also, it is okay to set |GSBGrad1| and |GSBGrad2| to the same non-zero
            value:

            >>> check(sm=10.0, g1=1.0, g2=1.0)
            sbg(6.0), qbga(0.55), qbgz(1.55), qdgz(1.45)
            >>> check(sm=10.0, g1=1.4, g2=1.4)
            sbg(6.39434), qbga(0.569946), qbgz(1.964286), qdgz(1.035714)

            As for the volume-related case, one can apply rise-related restrictions
            when the value of |KB| is |numpy.inf|:

            >>> derived.kb(inf)
            >>> check(sm=10.0, g1=0.0, g2=0.0)
            sbg(5.0), qbga(0.0), qbgz(0.0), qdgz(3.0)
            >>> check(sm=10.0, g1=1.0, g2=1.0)
            sbg(6.0), qbga(0.0), qbgz(1.0), qdgz(2.0)
            >>> check(sm=10.0, g1=0.0, g2=2.0)
            sbg(6.0), qbga(0.0), qbgz(1.0), qdgz(2.0)
            >>> check(sm=10.0, g1=1.0, g2=2.0)
            sbg(6.333333), qbga(0.0), qbgz(1.333333), qdgz(1.666667)

            Finally, we demonstrate combinations of volume- and rise-related
            restrictions.

            In the first combinational example, the rise-related restriction is active
            right from the start.  After a while, the groundwater amount reaches its
            highest possible value (5.8 mm).  From then on, the groundwater table is
            not allowed to rise anymore, which deactivates the rise-related
            restriction:

            >>> derived.kb(10.0)
            >>> check(sm=5.8, g1=1.4, g2=1.4)
            sbg(5.8), qbga(0.557143), qbgz(1.357143), qdgz(1.642857)

            The second combinational example is even more complex.  The groundwater
            rise slows down until it does not exceed `g1` anymore.  Then, no
            restriction is active anymore, and the evolution of |SGD| follows the
            simple linear storage model.  However, this happens only for a short while
            due to |SGD| reaching `sm` soon afterwards:

            >>> check(sm=6.2, g1=1.4, g2=1.4)
            sbg(6.2), qbga(0.568565), qbgz(1.768565), qdgz(1.231435)
    """
    CONTROLPARAMETERS = (
        lland_control.VolBMax,
        lland_control.GSBMax,
        lland_control.GSBGrad1,
        lland_control.GSBGrad2,
    )
    DERIVEDPARAMETERS = (lland_derived.KB,)
    UPDATEDSEQUENCES = (
        lland_states.SBG,
        lland_fluxes.QDGZ,
        lland_fluxes.QBGZ,
    )
    RESULTSEQUENCES = (lland_fluxes.QBGA,)
    SUBMETHODS = (Calc_QBGA_SBG_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        # pylint: disable=too-many-branches
        # (I know this method is much too complex but I do not see a good way to
        # refactor it)
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        k: float = der.kb
        sm: float = con.gsbmax * con.volbmax
        g1: float = con.gsbgrad1
        g2: float = con.gsbgrad2
        s0: float = old.sbg
        z: float = flu.qbgz
        if s0 > sm:
            excess: float = s0 - sm
            s0 = sm
        else:
            excess = 0.0
        if k == 0.0:
            new.sbg = 0.0
            flu.qbga = s0 + flu.qbgz
        elif z - s0 / k <= g1:
            if modelutils.isinf(k):
                new.sbg = min(s0 + z, sm)
                flu.qbga = 0.0
            else:
                if modelutils.isinf(sm):
                    t: float = 1.0
                else:
                    fraction: float = (k * z - sm) / (k * z - s0)
                    if fraction > 0.0:
                        t = -k * modelutils.log(fraction)
                    else:
                        t = 1.0
                if t < 1.0:
                    new.sbg = sm
                    flu.qbga = s0 - sm + t * flu.qbgz
                    flu.qbga += (1.0 - t) * sm / k
                else:
                    new.sbg = model.return_sg_v1(k, s0, z, 1.0)
                    flu.qbga = s0 - new.sbg + flu.qbgz
        elif g2 == 0.0:
            flu.qbga = s0 / k
            new.sbg = s0
        else:
            if modelutils.isinf(k) and (g2 > g1):
                flu.qbga = 0.0
                new.sbg = s0 + g2 / ((g2 - g1) / z + 1.0)
            else:
                st: float = min(k * (z - g1), sm)
                if g1 == g2:
                    t = min((st - s0) / g1, 1.0)
                    flu.qbga = t * (g1 * t + 2.0 * s0) / (2.0 * k)
                else:
                    c1: float = (g2 - g1) / (g1 - g2 - z)
                    c2: float = (g2 * k * z) / (g1 - g2)
                    t = min(k / c1 * modelutils.log((st + c2) / (s0 + c2)), 1.0)
                    flu.qbga = (s0 + c2) * (
                        modelutils.exp(c1 * t / k) - 1.0
                    ) / c1 - c2 * t / k
                if t < 1.0:
                    if st == sm:
                        new.sbg = sm
                        flu.qbga += (1.0 - t) * sm / k
                    else:
                        fraction = (k * z - sm) / (k * z - st)
                        if fraction > 0.0:
                            tt: float = -k * modelutils.log(fraction)
                        else:
                            tt = 1.0
                        if t + tt < 1.0:
                            new.sbg = sm
                            flu.qbga += st - sm + tt * flu.qbgz
                            flu.qbga += (1.0 - t - tt) * sm / k
                        else:
                            new.sbg = model.return_sg_v1(k, st, z, 1.0 - t)
                            flu.qbga += st - new.sbg + (1.0 - t) * flu.qbgz
                elif g1 == g2:
                    new.sbg = s0 + g1
                else:
                    new.sbg = (s0 + c2) * modelutils.exp(1.0 / k * c1) - c2
        qbgz: float = flu.qbgz
        flu.qbgz = new.sbg - s0 + flu.qbga
        flu.qdgz += qbgz - flu.qbgz
        flu.qbga += excess


class Calc_QIGA1_SIG1_V1(modeltools.Method):
    r"""Update the storage of the first interflow component and calculate its outflow.

    Basic equations:
       :math:`SIG1 = Return\_SG\_V1(KI1, SIG1, QIGZ1)`

       :math:`QIGA1 = SIG1_{old} - SIG1_{new} + QIGZ1`

    Example:

        Method |Calc_QIGA1_SIG1_V1| relies on the analytical solution of the linear
        storage equation implemented by method |Return_SG_V1|, from which we take the
        following test configuration:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> derived.ki1(3.0)
        >>> states.sig1.old = 1.0
        >>> fluxes.qigz1 = 2.0
        >>> model.calc_qiga1_sig1_v1()
        >>> states.sig1
        sig1(2.417343)
        >>> fluxes.qiga1
        qiga1(0.582657)
    """

    DERIVEDPARAMETERS = (lland_derived.KI1,)
    REQUIREDSEQUENCES = (lland_fluxes.QIGZ1,)
    UPDATEDSEQUENCES = (lland_states.SIG1,)
    RESULTSEQUENCES = (lland_fluxes.QIGA1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.sig1 = model.return_sg_v1(der.ki1, old.sig1, flu.qigz1, 1.0)
        flu.qiga1 = old.sig1 - new.sig1 + flu.qigz1


class Calc_QIGA2_SIG2_V1(modeltools.Method):
    r"""Update the storage of the second interflow component and calculate its outflow.

    Basic equations:
       :math:`SIG2 = Return\_SG\_V2(KI2, SIG2, QIGZ2)`

       :math:`QIGA2 = SIG2_{old} - SIG2_{new} + QIGZ2`

    Example:

        Method |Calc_QIGA2_SIG2_V1| relies on the analytical solution of the linear
        storage equation implemented by method |Return_SG_V1|, from which we take the
        following test configuration:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> derived.ki2(3.0)
        >>> states.sig2.old = 1.0
        >>> fluxes.qigz2 = 2.0
        >>> model.calc_qiga2_sig2_v1()
        >>> states.sig2
        sig2(2.417343)
        >>> fluxes.qiga2
        qiga2(0.582657)
    """

    DERIVEDPARAMETERS = (lland_derived.KI2,)
    REQUIREDSEQUENCES = (lland_fluxes.QIGZ2,)
    UPDATEDSEQUENCES = (lland_states.SIG2,)
    RESULTSEQUENCES = (lland_fluxes.QIGA2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.sig2 = model.return_sg_v1(der.ki2, old.sig2, flu.qigz2, 1.0)
        flu.qiga2 = old.sig2 - new.sig2 + flu.qigz2


class Calc_QDGA1_SDG1_V1(modeltools.Method):
    r"""Update the storage of the slow direct runoff component and calculate its
    outflow.

    Basic equations:
       :math:`QBDA1 = Return\_SG\_V1(KD1, SDG1, QDGZ1)`

       :math:`QDGA1 = SDG1_{old} - SDG1_{new} + QDGZ1`

    Example:

        Method |Calc_QDGA1_SDG1_V1| relies on the analytical solution of the linear
        storage equation implemented by method |Return_SG_V1|, from which we take the
        following test configuration:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> derived.kd1(3.0)
        >>> states.sdg1.old = 1.0
        >>> fluxes.qdgz1 = 2.0
        >>> model.calc_qdga1_sdg1_v1()
        >>> states.sdg1
        sdg1(2.417343)
        >>> fluxes.qdga1
        qdga1(0.582657)
    """

    DERIVEDPARAMETERS = (lland_derived.KD1,)
    REQUIREDSEQUENCES = (lland_fluxes.QDGZ1,)
    UPDATEDSEQUENCES = (lland_states.SDG1,)
    RESULTSEQUENCES = (lland_fluxes.QDGA1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.sdg1 = model.return_sg_v1(der.kd1, old.sdg1, flu.qdgz1, 1.0)
        flu.qdga1 = old.sdg1 - new.sdg1 + flu.qdgz1


class Calc_QDGA2_SDG2_V1(modeltools.Method):
    r"""Update the storage of the fast direct runoff component and calculate its
    outflow.

    Basic equations:
       :math:`QBDA2 = Return\_SG\_V1(KD2, SDG2, QDGZ2)`

       :math:`QDGA2 = SDG2_{old} - SDG2_{new} + QDGZ2`

    Example:

        Method |Calc_QDGA2_SDG2_V1| relies on the analytical solution of the linear
        storage equation implemented by method |Return_SG_V1|, from which we take the
        following test configuration:

        >>> from hydpy.models.lland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> derived.kd2(3.0)
        >>> states.sdg2.old = 1.0
        >>> fluxes.qdgz2 = 2.0
        >>> model.calc_qdga2_sdg2_v1()
        >>> states.sdg2
        sdg2(2.417343)
        >>> fluxes.qdga2
        qdga2(0.582657)
    """

    DERIVEDPARAMETERS = (lland_derived.KD2,)
    REQUIREDSEQUENCES = (lland_fluxes.QDGZ2,)
    UPDATEDSEQUENCES = (lland_states.SDG2,)
    RESULTSEQUENCES = (lland_fluxes.QDGA2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.sdg2 = model.return_sg_v1(der.kd2, old.sdg2, flu.qdgz2, 1.0)
        flu.qdga2 = old.sdg2 - new.sdg2 + flu.qdgz2


class Calc_QAH_V1(modeltools.Method):
    """Calculate the final runoff in mm.

    Basic equation:
       :math:`QAH = QZH + QBGA + QIGA1 + QIGA2 + QDGA1 + QDGA2 +
       NKor_{WASSER} - EvI_{WASSER}`

    In case there are water areas of type |WASSER|, their |NKor| values are added and
    their |EvI| values are subtracted from the "potential" runoff value, if possible.
    This can result in problematic modifications of simulated runoff series. It seems
    advisable to use the water types |FLUSS| and |SEE| instead.

    Examples:

        When there are no water areas in the respective subbasin (we choose arable land
        |ACKER| arbitrarily), the inflow (|QZH|) and the different runoff components
        (|QBGA|, |QIGA1|, |QIGA2|, |QDGA1|, and |QDGA2|) are simply summed up:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER, ACKER, ACKER)
        >>> fhru(0.5, 0.2, 0.3)
        >>> negq(False)
        >>> fluxes.qbga = 0.1
        >>> fluxes.qiga1 = 0.2
        >>> fluxes.qiga2 = 0.3
        >>> fluxes.qdga1 = 0.4
        >>> fluxes.qdga2 = 0.5
        >>> fluxes.qzh = 1.0
        >>> fluxes.nkor = 10.0
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(2.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        The defined values of interception evaporation do not show any impact on the
        result of the given example, the predefined values for sequence |EvI| remain
        unchanged.  But when we define the first hydrological as a water area
        (|WASSER|), |Calc_QAH_V1| adds the adjusted precipitaton (|NKor|) to and
        subtracts the interception evaporation (|EvI|) from |lland_fluxes.QAH|:

        >>> control.lnk(WASSER, VERS, NADELW)
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(5.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        Note that only 5 mm are added (instead of the |NKor| value 10 mm) and that only
        2 mm are substracted (instead of the |EvI| value 4 mm, as the first response
        unit area only accounts for 50 % of the total subbasin area.

        Setting also the land use class of the second response unit to water type
        |WASSER| and resetting |NKor| to zero would result in overdrying.  To avoid
        this, both actual water evaporation values stored in sequence |EvI| are reduced
        by the same factor:

        >>> control.lnk(WASSER, WASSER, NADELW)
        >>> fluxes.nkor = 0.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(0.0)
        >>> fluxes.evi
        evi(3.333333, 4.166667, 3.0)

        The handling of water areas of type |FLUSS| and |SEE| differs from those of
        type |WASSER|, as these do receive their net input before the runoff
        concentration routines are applied.  This should be more realistic in most
        cases (especially for type |SEE|, representing lakes not directly connected to
        the stream network).  But it could also, at least for very dry periods, result
        in negative outflow values. We avoid this by setting |lland_fluxes.QAH| to zero
        and adding the truncated negative outflow value to the |EvI| value of all
        response units of type |FLUSS| and |SEE|:

        >>> control.lnk(FLUSS, SEE, NADELW)
        >>> fluxes.qbga = -1.0
        >>> fluxes.qdga2 = -1.9
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(0.0)
        >>> fluxes.evi
        evi(2.571429, 3.571429, 3.0)

        This adjustment of |EvI| is only correct regarding the total water balance.
        Neither spatial nor temporal consistency of the resulting |EvI| values are
        assured.  In the most extreme case, even negative |EvI| values might occur.
        This seems acceptable, as long as the adjustment of |EvI| is rarely triggered.
        When in doubt about this, check sequence |EvI| for all |FLUSS| and |SEE| units
        for possible discrepancies.  Also note that |lland_fluxes.QAH| might perform
        unnecessary corrections when you combine water type |WASSER| with water type
        |SEE| or |FLUSS|.

        For some model configurations, negative discharges for dry conditions are
        acceptable or even preferable, which is possible through setting parameter
        |NegQ| to |True|:

        >>> negq(True)
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(-1.0)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NegQ,
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.QBGA,
        lland_fluxes.QIGA1,
        lland_fluxes.QIGA2,
        lland_fluxes.QDGA1,
        lland_fluxes.QDGA2,
        lland_fluxes.NKor,
        lland_fluxes.QZH,
    )
    UPDATEDSEQUENCES = (lland_fluxes.EvI,)
    RESULTSEQUENCES = (lland_fluxes.QAH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qah = flu.qzh + flu.qbga + flu.qiga1 + flu.qiga2 + flu.qdga1 + flu.qdga2
        if (not con.negq) and (flu.qah < 0.0):
            d_area = 0.0
            for k in range(con.nhru):
                if con.lnk[k] in (FLUSS, SEE):
                    d_area += con.fhru[k]
            if d_area > 0.0:
                for k in range(con.nhru):
                    if con.lnk[k] in (FLUSS, SEE):
                        flu.evi[k] += flu.qah / d_area
            flu.qah = 0.0
        d_epw = 0.0
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.qah += con.fhru[k] * flu.nkor[k]
                d_epw += con.fhru[k] * flu.evi[k]
        if (flu.qah > d_epw) or con.negq:
            flu.qah -= d_epw
        elif d_epw > 0.0:
            for k in range(con.nhru):
                if con.lnk[k] == WASSER:
                    flu.evi[k] *= flu.qah / d_epw
            flu.qah = 0.0


class Calc_QA_V1(modeltools.Method):
    """Calculate the final runoff in m³/s.

    Basic equation:
       :math:`QA = QFactor \\cdot QAH`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.qfactor(2.0)
        >>> fluxes.qah = 3.0
        >>> model.calc_qa_v1()
        >>> fluxes.qa
        qa(6.0)
    """

    DERIVEDPARAMETERS = (lland_derived.QFactor,)
    REQUIREDSEQUENCES = (lland_fluxes.QAH,)
    RESULTSEQUENCES = (lland_fluxes.QA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qa = der.qfactor * flu.qah


class Pass_QA_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
       :math:`Q_{outlets} = QA`
    """

    REQUIREDSEQUENCES = (lland_fluxes.QA,)
    RESULTSEQUENCES = (lland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.qa


class Get_Temperature_V1(modeltools.Method):
    """Get the selected zone's current temperature.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.tkor = 2.0, 4.0
        >>> model.get_temperature_v1(0)
        2.0
        >>> model.get_temperature_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (lland_fluxes.TKor,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.tkor[s]


class Get_MeanTemperature_V1(modeltools.Method):
    """Get the basin's current mean temperature.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> inputs.teml = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_meantemperature_v1())
        2.0
    """

    REQUIREDSEQUENCES = (lland_inputs.TemL,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.teml


class Get_Precipitation_V1(modeltools.Method):
    """Get the current precipitation from the selected hydrological response unit.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.nkor = 2.0, 4.0
        >>> model.get_precipitation_v1(0)
        2.0
        >>> model.get_precipitation_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (lland_fluxes.NKor,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.nkor[s]


class Get_InterceptedWater_V1(modeltools.Method):
    """Get the selected response unit's current amount of intercepted water.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> states.inzp = 2.0, 4.0
        >>> model.get_interceptedwater_v1(0)
        2.0
        >>> model.get_interceptedwater_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (lland_states.Inzp,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        return sta.inzp[k]


class Get_SoilWater_V1(modeltools.Method):
    """Get the selected response unit's current soil water content.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> states.bowa = 2.0, 4.0
        >>> model.get_soilwater_v1(0)
        2.0
        >>> model.get_soilwater_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (lland_states.BoWa,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        return sta.bowa[k]


class Get_SnowCover_V1(modeltools.Method):
    """Get the selected response unit's current snow cover degree.

    Example:

        Each response unit with a non-zero amount of snow counts as completely covered:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> states.wats = 0.0, 2.0
        >>> model.get_snowcover_v1(0)
        0.0
        >>> model.get_snowcover_v1(1)
        1.0
    """

    REQUIREDSEQUENCES = (lland_states.WATS,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        sta = model.sequences.states.fastaccess

        if sta.wats[k] > 0.0:
            return 1.0
        return 0.0


class Get_SnowyCanopy_V1(modeltools.Method):
    """Get the selected response unit's current snow cover degree in the canopies of
    tree-like vegetation (or |numpy.nan| if the zone's vegetation is not tree-like).

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(LAUBW, MISCHW, NADELW, ACKER)
        >>> states.stinz = 0.0
        >>> from hydpy import print_values
        >>> print_values(model.get_snowycanopy_v1(i) for i in range(4))
        0.0, 0.0, 0.0, nan
        >>> states.stinz = 0.1
        >>> print_values(model.get_snowycanopy_v1(i) for i in range(4))
        1.0, 1.0, 1.0, nan
    """

    CONTROLPARAMETERS = (lland_control.Lnk,)
    REQUIREDSEQUENCES = (lland_states.STInz,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        if con.lnk[k] in (LAUBW, MISCHW, NADELW):
            return float(sta.stinz[k] > 0.0)
        return modelutils.nan


class Get_SnowAlbedo_V1(modeltools.Method):
    """Get the selected response unit's current albedo as a fraction.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.actualalbedo = 2.0, 4.0
        >>> model.get_snowalbedo_v1(0)
        2.0
        >>> model.get_snowalbedo_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (lland_fluxes.ActualAlbedo,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.actualalbedo[k]


class PegasusESnowInz(roottools.Pegasus):
    """Pegasus iterator for finding the correct energy content of the intercepted
    snow."""

    METHODS = (Return_BackwardEulerErrorInz_V1,)


class PegasusESnow(roottools.Pegasus):
    """Pegasus iterator for finding the correct snow energy content."""

    METHODS = (Return_BackwardEulerError_V1,)


class PegasusTempSSurface(roottools.Pegasus):
    """Pegasus iterator for finding the correct snow surface temperature."""

    METHODS = (Return_EnergyGainSnowSurface_V1,)


class Model(modeltools.AdHocModel):
    """Base model for HydPy-L-Land."""

    INLET_METHODS = (Pick_QZ_V1,)
    RECEIVER_METHODS = ()
    INTERFACE_METHODS = (
        Get_Temperature_V1,
        Get_MeanTemperature_V1,
        Get_Precipitation_V1,
        Get_InterceptedWater_V1,
        Get_SoilWater_V1,
        Get_SnowCover_V1,
        Get_SnowyCanopy_V1,
        Get_SnowAlbedo_V1,
    )
    ADD_METHODS = (
        Calc_EvI_Inzp_AETModel_V1,
        Calc_EvB_AETModel_V1,
        Return_NetLongwaveRadiationInz_V1,
        Return_NetLongwaveRadiationSnow_V1,
        Return_EnergyGainSnowSurface_V1,
        Return_SaturationVapourPressure_V1,
        Return_NetRadiation_V1,
        Return_WSensInz_V1,
        Return_WSensSnow_V1,
        Return_WLatInz_V1,
        Return_WLatSnow_V1,
        Return_WSurfInz_V1,
        Return_WSurf_V1,
        Return_BackwardEulerErrorInz_V1,
        Return_BackwardEulerError_V1,
        Return_TempSInz_V1,
        Return_TempS_V1,
        Return_WG_V1,
        Return_ESnowInz_V1,
        Return_ESnow_V1,
        Return_TempSSurface_V1,
        Return_SG_V1,
        Calc_BoWa_Default_V1,
        Calc_BoWa_SoilModel_V1,
    )
    RUN_METHODS = (
        Calc_QZH_V1,
        Update_LoggedSunshineDuration_V1,
        Calc_DailySunshineDuration_V1,
        Update_LoggedPossibleSunshineDuration_V1,
        Calc_DailyPossibleSunshineDuration_V1,
        Calc_NKor_V1,
        Calc_TKor_V1,
        Calc_WindSpeed2m_V1,
        Calc_ReducedWindSpeed2m_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_ActualVapourPressure_V1,
        Calc_NBes_Inzp_V1,
        Calc_SNRatio_V1,
        Calc_SBes_V1,
        Calc_SnowIntMax_V1,
        Calc_SnowIntRate_V1,
        Calc_NBesInz_V1,
        Calc_SBesInz_V1,
        Calc_STInz_V1,
        Calc_WaDaInz_SInz_V1,
        Calc_WNiedInz_ESnowInz_V1,
        Calc_TempSInz_V1,
        Update_ASInz_V1,
        Calc_NetShortwaveRadiationInz_V1,
        Calc_ActualAlbedoInz_V1,
        Update_ESnowInz_V1,
        Calc_SchmPotInz_V1,
        Calc_SchmInz_STInz_V1,
        Calc_GefrPotInz_V1,
        Calc_GefrInz_STInz_V1,
        Calc_EvSInz_SInz_STInz_V1,
        Update_WaDaInz_SInz_V1,
        Update_ESnowInz_V2,
        Calc_WATS_V1,
        Calc_WATS_V2,
        Calc_WaDa_WAeS_V1,
        Calc_WaDa_WAeS_V2,
        Calc_WGTF_V1,
        Calc_WNied_V1,
        Calc_WNied_ESnow_V1,
        Calc_TZ_V1,
        Calc_WG_V1,
        Calc_TempS_V1,
        Update_TauS_V1,
        Calc_ActualAlbedo_V1,
        Calc_NetShortwaveRadiationSnow_V1,
        Calc_RLAtm_V1,
        Update_EBdn_V1,
        Update_ESnow_V1,
        Calc_EvI_Inzp_V1,
        Update_EvI_WEvI_V1,
        Calc_EvB_V1,
        Calc_SchmPot_V1,
        Calc_SchmPot_V2,
        Calc_GefrPot_V1,
        Calc_Schm_WATS_V1,
        Calc_Gefr_WATS_V1,
        Calc_EvS_WAeS_WATS_V1,
        Update_WaDa_WAeS_V1,
        Update_ESnow_V2,
        Calc_SFF_V1,
        Calc_FVG_V1,
        Calc_QKap_V1,
        Calc_QBB_V1,
        Calc_QIB1_V1,
        Calc_QIB2_V1,
        Calc_QDB_V1,
        Update_QDB_V1,
        Calc_BoWa_V1,
        Calc_QBGZ_V1,
        Calc_QIGZ1_V1,
        Calc_QIGZ2_V1,
        Calc_QDGZ_V1,
        Calc_QBGA_SBG_V1,
        Calc_QBGA_SBG_QBGZ_QDGZ_V1,
        Calc_QIGA1_SIG1_V1,
        Calc_QIGA2_SIG2_V1,
        Calc_QDGZ1_QDGZ2_V1,
        Calc_QDGA1_SDG1_V1,
        Calc_QDGA2_SDG2_V1,
        Calc_QAH_V1,
        Calc_QA_V1,
    )
    OUTLET_METHODS = (Pass_QA_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        aetinterfaces.AETModel_V1,
        soilinterfaces.SoilModel_V1,
    )
    SUBMODELS = (
        PegasusESnowInz,
        PegasusESnow,
        PegasusTempSSurface,
    )

    idx_hru = modeltools.Idx_HRU()

    aetmodel = modeltools.SubmodelProperty(aetinterfaces.AETModel_V1)
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    soilmodel = modeltools.SubmodelProperty(soilinterfaces.SoilModel_V1, optional=True)
    soilmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    soilmodel_typeid = modeltools.SubmodelTypeIDProperty()


class Main_AETModel_V1(modeltools.AdHocModel):
    """Base class for HydPy-L models that support submodels that comply with the
    |AETModel_V1| interface."""

    aetmodel: modeltools.SubmodelProperty
    aetmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    aetmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "aetmodel",
        aetinterfaces.AETModel_V1,
        aetinterfaces.AETModel_V1.prepare_nmbzones,
        aetinterfaces.AETModel_V1.prepare_zonetypes,
        aetinterfaces.AETModel_V1.prepare_subareas,
        aetinterfaces.AETModel_V1.prepare_maxsoilwater,
        aetinterfaces.AETModel_V1.prepare_water,
        aetinterfaces.AETModel_V1.prepare_interception,
        aetinterfaces.AETModel_V1.prepare_soil,
        aetinterfaces.AETModel_V1.prepare_tree,
        aetinterfaces.AETModel_V1.prepare_conifer,
        landtype_constants=lland_constants.CONSTANTS,
        landtype_refindices=lland_control.Lnk,
        refweights=lland_control.FHRU,
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

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.lland_v3 import *
        >>> parameterstep()
        >>> nhru(7)
        >>> ft(10.0)
        >>> fhru(0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1)
        >>> lnk(ACKER, LAUBW, NADELW, VERS, WASSER, FLUSS, SEE)
        >>> wmax(200.0)
        >>> with model.add_aetmodel_v1("evap_morsim"):
        ...     nmbhru
        ...     hrutype
        ...     water
        ...     interception
        ...     soil
        ...     tree
        ...     conifer
        ...     fieldcapacity(200.0)
        ...     wiltingpoint(acker=50.0, laubw=150.0, nadelw=250.0)
        ...     leafareaindex.acker_aug = 3.5
        ...     for method, argument in model.predefinedmethod2argument.items():
        ...         print(method, argument, sep=": ")
        nmbhru(7)
        hrutype(ACKER, LAUBW, NADELW, VERS, WASSER, FLUSS, SEE)
        water(acker=False, fluss=True, laubw=False, nadelw=False, see=True,
              vers=False, wasser=True)
        interception(acker=True, fluss=False, laubw=True, nadelw=True,
                     see=False, vers=True, wasser=False)
        soil(acker=True, fluss=False, laubw=True, nadelw=True, see=False,
             vers=False, wasser=False)
        tree(acker=False, fluss=False, laubw=True, nadelw=True, see=False,
             vers=False, wasser=False)
        conifer(acker=False, fluss=False, laubw=False, nadelw=True, see=False,
                vers=False, wasser=False)
        prepare_subareas: [1. 2. 1. 2. 1. 2. 1.]

        >>> from hydpy import round_
        >>> round_(model.aetmodel.parameters.control.leafareaindex.acker_aug)
        3.5

        >>> wp = model.aetmodel.parameters.control.wiltingpoint
        >>> wp
        wiltingpoint(acker=50.0, laubw=150.0, nadelw=200.0)
        >>> lnk(NADELW, LAUBW, ACKER, VERS, WASSER, FLUSS, SEE)
        >>> wp
        wiltingpoint(acker=200.0, laubw=150.0, nadelw=50.0)
        >>> round_(wp.average_values())
        137.5
        """
        control = self.parameters.control
        nhru = control.nhru.value
        lnk = control.lnk.values

        aetmodel.prepare_nmbzones(nhru)
        aetmodel.prepare_zonetypes(lnk)
        aetmodel.prepare_subareas(control.fhru.values * control.ft.value)
        aetmodel.prepare_maxsoilwater(control.wmax.values)
        sel = numpy.full(nhru, False, dtype=bool)
        sel[lnk == WASSER] = True
        sel[lnk == FLUSS] = True
        sel[lnk == SEE] = True
        aetmodel.prepare_water(sel)
        aetmodel.prepare_interception(~sel)
        sel[lnk == VERS] = True
        aetmodel.prepare_soil(~sel)
        sel = numpy.full(nhru, False, dtype=bool)
        sel[lnk == NADELW] = True
        aetmodel.prepare_conifer(sel)
        sel[lnk == LAUBW] = True
        sel[lnk == MISCHW] = True
        aetmodel.prepare_tree(sel)


class Main_SoilModel_V1(modeltools.AdHocModel):
    """Base class for HydPy-L models that support submodels that comply with the
    |SoilModel_V1| interface."""

    soilmodel: modeltools.SubmodelProperty
    soilmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    soilmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "soilmodel",
        soilinterfaces.SoilModel_V1,
        soilinterfaces.SoilModel_V1.prepare_nmbzones,
    )
    def add_soilmodel_v1(
        self,
        soilmodel: soilinterfaces.SoilModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given soil model that follows the |SoilModel_V1| interface.

        >>> from hydpy.models.lland_v1 import *
        >>> parameterstep()
        >>> nhru(2)
        >>> ft(10.0)
        >>> fhru(0.2, 0.8)
        >>> with model.add_soilmodel_v1("ga_garto_submodel1", update=False):
        ...     nmbsoils
        nmbsoils(2)
        >>> model.soilmodel.parameters.control.nmbsoils
        nmbsoils(2)
        """
        control = self.parameters.control
        soilmodel.prepare_nmbzones(control.nhru.value)


class Sub_TempModel_V1(modeltools.AdHocModel, tempinterfaces.TempModel_V1):
    """Base class for HydPy-L models that comply with the |TempModel_V1| submodel
    interface."""


class Sub_PrecipModel_V1(modeltools.AdHocModel, precipinterfaces.PrecipModel_V1):
    """Base class for HydPy-L models that comply with the |PrecipModel_V1| submodel
    interface."""


class Sub_IntercModel_V1(modeltools.AdHocModel, stateinterfaces.IntercModel_V1):
    """Base class for HydPy-L models that comply with the |IntercModel_V1| submodel
    interface."""


class Sub_SoilWaterModel_V1(modeltools.AdHocModel, stateinterfaces.SoilWaterModel_V1):
    """Base class for HydPy-L models that comply with the |SoilWaterModel_V1| submodel
    interface."""


class Sub_SnowCoverModel_V1(modeltools.AdHocModel, stateinterfaces.SnowCoverModel_V1):
    """Base class for HydPy-L models that comply with the |SnowCoverModel_V1| submodel
    interface."""


class Sub_SnowyCanopyModel_V1(
    modeltools.AdHocModel, stateinterfaces.SnowyCanopyModel_V1
):
    """Base class for HydPy-L models that comply with the |SnowyCanopyModel_V1|
    submodel interface."""


class Sub_SnowAlbedoModel_V1(modeltools.AdHocModel, stateinterfaces.SnowAlbedoModel_V1):
    """Base class for HydPy-L models that comply with the |SnowAlbedoModel_V1| submodel
    interface."""
