# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring
"""
.. _`solar time`: https://en.wikipedia.org/wiki/Solar_time
"""
# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.auxs import roottools
from hydpy.cythons import modelutils

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
    """Query the current inflow from all inlet nodes.

    Basic equation:
      :math:`QZ = \\sum Q_{inlets}`
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


class Update_LoggedTemL_V1(modeltools.Method):
    """Log the air temperature values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedteml.shape = 3
        >>> logs.loggedteml = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedteml_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.teml,
        ...                          logs.loggedteml))
        >>> test.nexts.teml = 0.0, 6.0, 3.0, 3.0
        >>> del test.inits.loggedteml
        >>> test()
        | ex. | teml |           loggedteml |
        -------------------------------------
        |   1 |  0.0 | 0.0  0.0         0.0 |
        |   2 |  6.0 | 6.0  0.0         0.0 |
        |   3 |  3.0 | 3.0  6.0         0.0 |
        |   4 |  3.0 | 3.0  3.0         6.0 |
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_inputs.TemL,)
    UPDATEDSEQUENCES = (lland_logs.LoggedTemL,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedteml[idx] = log.loggedteml[idx - 1]
        log.loggedteml[0] = inp.teml


class Calc_TemLTag_V1(modeltools.Method):
    """Calculate the average air temperature of the last 24 hours.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedteml.shape = 3
        >>> logs.loggedteml = 1.0, 5.0, 3.0
        >>> model.calc_temltag_v1()
        >>> fluxes.temltag
        temltag(3.0)
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_logs.LoggedTemL,)
    UPDATEDSEQUENCES = (lland_fluxes.TemLTag,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.temltag = 0.0
        for idx in range(der.nmblogentries):
            flu.temltag += log.loggedteml[idx]
        flu.temltag /= der.nmblogentries


class Update_LoggedRelativeHumidity_V1(modeltools.Method):
    """Log the sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedrelativehumidity.shape = 3
        >>> logs.loggedrelativehumidity = 0.0
        >>> from hydpy import UnitTest
        >>> method = (
        ...     model.update_loggedrelativehumidity_v1)
        >>> test = UnitTest(model,
        ...                method,
        ...                 last_example=4,
        ...                 parseqs=(inputs.relativehumidity,
        ...                          logs.loggedrelativehumidity))
        >>> test.nexts.relativehumidity = 0.0, 6.0, 3.0, 3.0
        >>> del test.inits.loggedrelativehumidity
        >>> test()
        | ex. | relativehumidity |           loggedrelativehumidity |
        -------------------------------------------------------------
        |   1 |              0.0 | 0.0  0.0                     0.0 |
        |   2 |              6.0 | 6.0  0.0                     0.0 |
        |   3 |              3.0 | 3.0  6.0                     0.0 |
        |   4 |              3.0 | 3.0  3.0                     6.0 |

    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_inputs.RelativeHumidity,)
    UPDATEDSEQUENCES = (lland_logs.LoggedRelativeHumidity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedrelativehumidity[idx] = log.loggedrelativehumidity[idx - 1]
        log.loggedrelativehumidity[0] = inp.relativehumidity


class Calc_DailyRelativeHumidity_V1(modeltools.Method):
    """Calculate the average relative humidity of the last 24 hours.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedrelativehumidity.shape = 3
        >>> logs.loggedrelativehumidity = 1.0, 5.0, 3.0
        >>> model.calc_dailyrelativehumidity_v1()
        >>> fluxes.dailyrelativehumidity
        dailyrelativehumidity(3.0)
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_logs.LoggedRelativeHumidity,)
    UPDATEDSEQUENCES = (lland_fluxes.DailyRelativeHumidity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailyrelativehumidity = 0.0
        for idx in range(der.nmblogentries):
            flu.dailyrelativehumidity += log.loggedrelativehumidity[idx]
        flu.dailyrelativehumidity /= der.nmblogentries


class Update_LoggedWindSpeed2m_V1(modeltools.Method):
    """Log the wind speed values 2 meters above ground of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedwindspeed2m.shape = 3
        >>> logs.loggedwindspeed2m = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedwindspeed2m_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.windspeed2m,
        ...                          logs.loggedwindspeed2m))
        >>> test.nexts.windspeed2m = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedwindspeed2m
        >>> test()
        | ex. | windspeed2m |           loggedwindspeed2m |
        ---------------------------------------------------
        |   1 |         1.0 | 1.0  0.0                0.0 |
        |   2 |         3.0 | 3.0  1.0                0.0 |
        |   3 |         2.0 | 2.0  3.0                1.0 |
        |   4 |         4.0 | 4.0  2.0                3.0 |
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_fluxes.WindSpeed2m,)
    UPDATEDSEQUENCES = (lland_logs.LoggedWindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedwindspeed2m[idx] = log.loggedwindspeed2m[idx - 1]
        log.loggedwindspeed2m[0] = flu.windspeed2m


class Calc_DailyWindSpeed2m_V1(modeltools.Method):
    """Calculate the average wind speed 2 meters above ground of the last
    24 hours.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedwindspeed2m.shape = 3
        >>> logs.loggedwindspeed2m = 1.0, 5.0, 3.0
        >>> model.calc_dailywindspeed2m_v1()
        >>> fluxes.dailywindspeed2m
        dailywindspeed2m(3.0)
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_logs.LoggedWindSpeed2m,)
    UPDATEDSEQUENCES = (lland_fluxes.DailyWindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailywindspeed2m = 0.0
        for idx in range(der.nmblogentries):
            flu.dailywindspeed2m += log.loggedwindspeed2m[idx]
        flu.dailywindspeed2m /= der.nmblogentries


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
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailysunshineduration = 0.0
        for idx in range(der.nmblogentries):
            flu.dailysunshineduration += log.loggedsunshineduration[idx]


class Calc_NKor_V1(modeltools.Method):
    """Adjust the given precipitation value :cite:`ref-LARSIM`.

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


class Calc_TKorTag_V1(modeltools.Method):
    """Adjust the given daily air temperature value.

    Basic equation:
      :math:`TKorTag = KT + TemLTag`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> kt(-2.0, 0.0, 2.0)
        >>> fluxes.temltag(1.0)
        >>> model.calc_tkortag_v1()
        >>> fluxes.tkortag
        tkortag(-1.0, 1.0, 3.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KT,
    )
    REQUIREDSEQUENCES = (lland_fluxes.TemLTag,)
    RESULTSEQUENCES = (lland_fluxes.TKorTag,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.tkortag[k] = con.kt[k] + flu.temltag


class Return_AdjustedWindSpeed_V1(modeltools.Method):
    """Adjust and return the measured wind speed to the given defined
    height above the ground :cite:`ref-LARSIM`.

    Basic equation:
      :math:`WindSpeed \\cdot
      \\frac{ln(newheight/Z0)}{ln(MeasuringHeightWindSpeed/Z0)}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> from hydpy import round_
        >>> round_(model.return_adjustedwindspeed_v1(2.0))
        4.007956
        >>> round_(model.return_adjustedwindspeed_v1(0.5))
        3.153456
    """

    CONTROLPARAMETERS = (lland_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (lland_fixed.Z0,)
    REQUIREDSEQUENCES = (lland_inputs.WindSpeed,)

    @staticmethod
    def __call__(
        model: modeltools.Model,
        newheight: float,
    ) -> float:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        return inp.windspeed * (
            modelutils.log(newheight / fix.z0)
            / modelutils.log(con.measuringheightwindspeed / fix.z0)
        )


class Calc_WindSpeed2m_V1(modeltools.Method):
    """Adjust the measured wind speed to a height of 2 meters above the ground.

    Method |Calc_WindSpeed2m_V1| uses method |Return_AdjustedWindSpeed_V1|
    to adjust the wind speed of all hydrological response units.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed2m_v1()
        >>> fluxes.windspeed2m
        windspeed2m(4.007956)
    """

    SUBMETHODS = (Return_AdjustedWindSpeed_V1,)
    CONTROLPARAMETERS = (lland_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (lland_fixed.Z0,)
    REQUIREDSEQUENCES = (lland_inputs.WindSpeed,)
    RESULTSEQUENCES = (lland_fluxes.WindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed2m = model.return_adjustedwindspeed_v1(2.0)


class Calc_ReducedWindSpeed2m_V1(modeltools.Method):
    """Calculate the ref-use-specific wind speed at height of 2 meters
    :cite:`ref-LARSIM` (based on :cite:`ref-LUBW2006a`,
    :cite:`ref-LUBWLUWG2015`).


    Basic equation (for forests):
      :math:`ReducedWindSpeed2m = \
      max(P1Wind - P2Wind \\cdot LAI, 0) \\cdot WindSpeed2m`

    Example:

        The basic equation given above holds for forests (hydrological
        response units of type |LAUBW|, |MISCHW|, and |NADELW| only.
        For all other ref-use types method |Calc_ReducedWindSpeed2m_V1|
        maintains the given wind speed for grass:

        >>> from hydpy import pub
        >>> pub.timegrids = '2019-05-30', '2019-06-03', '1d'
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
        >>> model.idx_sim = pub.timegrids.init['2019-05-31']
        >>> model.calc_reducedwindspeed2m_v1()
        >>> fluxes.reducedwindspeed2m
        reducedwindspeed2m(2.0, 0.6, 0.2, 0.0)

        >>> lai.obstb_jun = 0.0
        >>> lai.laubw_jun = 3.0
        >>> lai.mischw_jun = 6.0
        >>> lai.nadelw_jun = 10.0
        >>> model.idx_sim = pub.timegrids.init['2019-06-01']
        >>> model.calc_reducedwindspeed2m_v1()
        >>> fluxes.reducedwindspeed2m
        reducedwindspeed2m(2.0, 0.4, 0.0, 0.0)
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


class Calc_WindSpeed10m_V1(modeltools.Method):
    """Adjust the measured wind speed to a height of 10 meters above the ground.

    Method |Calc_WindSpeed10m_V1| uses method |Return_AdjustedWindSpeed_V1|
    to adjust the wind speed of all hydrological response units.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(3.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed10m_v1()
        >>> fluxes.windspeed10m
        windspeed10m(5.871465)
    """

    SUBMETHODS = (Return_AdjustedWindSpeed_V1,)
    CONTROLPARAMETERS = (lland_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (lland_fixed.Z0,)
    REQUIREDSEQUENCES = (lland_inputs.WindSpeed,)
    RESULTSEQUENCES = (lland_fluxes.WindSpeed10m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed10m = model.return_adjustedwindspeed_v1(10.0)


class Calc_SolarDeclination_V1(modeltools.Method):
    # noinspection PyUnresolvedReferences
    """Calculate the solar declination (:cite:`ref-LARSIM`).

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`SolarDeclination = 0.41 \\cdot cos \\left(
      \\frac{2 \\cdot Pi \\cdot (DOY - 171)}{365} \\right)`

    Examples:

        We define an initialisation period covering both a leap year (2000)
        and a non-leap year (2001):

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import pub, round_
        >>> pub.timegrids = '2000-01-01', '2002-01-01', '1d'
        >>> derived.doy.update()

        The following convenience function applies method
        |Calc_SolarDeclination_V1| for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_solardeclination_v1()
        ...         print(date, end=': ')
        ...         round_(fluxes.solardeclination.value)

        The results are identical for both years, due to :

        >>> test('2000-01-01', '2000-02-28', '2000-02-29',
        ...      '2000-03-01', '2000-12-31')
        2000-01-01: -0.401992
        2000-02-28: -0.149946
        2000-02-29: -0.143355
        2000-03-01: -0.136722
        2000-12-31: -0.401992

        >>> test('2001-01-01', '2001-02-28',
        ...      '2001-03-01', '2001-12-31')
        2001-01-01: -0.401992
        2001-02-28: -0.149946
        2001-03-01: -0.136722
        2001-12-31: -0.401992

        .. testsetup::

            >>> del pub.timegrids
    """
    DERIVEDPARAMETERS = (lland_derived.DOY,)
    FIXEDPARAMETERS = (lland_fixed.Pi,)
    RESULTSEQUENCES = (lland_fluxes.SolarDeclination,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.solardeclination = 0.41 * modelutils.cos(
            2.0 * fix.pi * (der.doy[model.idx_sim] - 171.0) / 365.0
        )


class Calc_TSA_TSU_V1(modeltools.Method):
    """Calculate time of sunrise and sunset of the current day
    :cite:`ref-LARSIM` (based on :cite:`ref-Thompson1981`).

    Basic equations:
      :math:`TSA^* = \\frac{12}{Pi} \\cdot acos \\left(
      tan(SolarDeclination) \\cdot tan(LatitudeRad) +
      \\frac{0.0145}{cos(SolarDeclination) \\cdot cos(LatitudeRad)} \\right)`

      :math:`\\delta = \\frac{4 \\cdot (UTCLongitude - Longitude)}{60}`

      :math:`TSA = TSA^* + \\delta`

      :math:`TSU = 24 - TSA^* + \\delta`

    Examples:

        We calculate the local time of sunrise and sunset for a latitude of
        approximately 52°N and a longitude of 10°E, which is 5° west of the
        longitude defining the local time zone:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> longitude(10.0)
        >>> derived.utclongitude(15.0)
        >>> derived.latituderad(0.9)

        The sunshine duration varies between seven hours at winter solstice
        and 16 hours at summer solstice:

        >>> fluxes.solardeclination = -0.41
        >>> model.calc_tsa_tsu_v1()
        >>> fluxes.tsa
        tsa(8.432308)
        >>> fluxes.tsu
        tsu(16.234359)
        >>> fluxes.solardeclination = 0.41
        >>> model.calc_tsa_tsu_v1()
        >>> fluxes.tsa
        tsa(4.002041)
        >>> fluxes.tsu
        tsu(20.664625)
    """

    CONTROLPARAMETERS = (lland_control.Longitude,)
    DERIVEDPARAMETERS = (
        lland_derived.LatitudeRad,
        lland_derived.UTCLongitude,
    )
    FIXEDPARAMETERS = (lland_fixed.Pi,)
    REQUIREDSEQUENCES = (lland_fluxes.SolarDeclination,)
    RESULTSEQUENCES = (
        lland_fluxes.TSA,
        lland_fluxes.TSU,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.tsa = (
            12.0
            / fix.pi
            * modelutils.acos(
                modelutils.tan(flu.solardeclination) * modelutils.tan(der.latituderad)
                + 0.0145
                / modelutils.cos(flu.solardeclination)
                / modelutils.cos(der.latituderad)
            )
        )
        flu.tsu = 24.0 - flu.tsa
        d_dt = (der.utclongitude - con.longitude) * 4.0 / 60.0
        flu.tsa += d_dt
        flu.tsu += d_dt


class Calc_EarthSunDistance_V1(modeltools.Method):
    """Calculate the relative inverse distance between the earth and the sun.

    Basic equation (:cite:`ref-Allen1998`, equation 23):

      :math:`EarthSunDistance = 1 + 0.033 \\cdot cos \\bigl(
      2 \\cdot Pi / 366 \\cdot (DOY + 1) \\bigr)`

    Note that this equation differs a little from the one given by Allen
    :cite:`ref-Allen1998`.
    The following examples show that |Calc_EarthSunDistance_V1| calculates
    the same distance value for a specific "day" (e.g. the 1st March) both
    for leap years and non-leap years.  Hence, there is a tiny "jump"
    between the 28th February and the 1st March for non-leap years.

    Examples:

        We define an initialisation period covering both a leap year (2000)
        and a non-leap year (2001):

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import pub, round_
        >>> pub.timegrids = '2000-01-01', '2002-01-01', '1d'
        >>> derived.doy.update()

        The following convenience function applies method
        |Calc_EarthSunDistance_V1| for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_earthsundistance_v1()
        ...         print(date, end=': ')
        ...         round_(fluxes.earthsundistance.value)

        The results are identical for both years:

        >>> test('2000-01-01', '2000-02-28', '2000-02-29',
        ...      '2000-03-01', '2000-07-01', '2000-12-31')
        2000-01-01: 1.032995
        2000-02-28: 1.017471
        2000-02-29: 1.016988
        2000-03-01: 1.0165
        2000-07-01: 0.967
        2000-12-31: 1.033

        >>> test('2001-01-01', '2001-02-28',
        ...      '2001-03-01', '2001-07-01', '2001-12-31')
        2001-01-01: 1.032995
        2001-02-28: 1.017471
        2001-03-01: 1.0165
        2001-07-01: 0.967
        2001-12-31: 1.033

        The following calculation agrees with example 8 of Allen
        :cite:`ref-Allen1998`:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_earthsundistance_v1()
        >>> fluxes.earthsundistance
        earthsundistance(0.984993)
    """

    DERIVEDPARAMETERS = (lland_derived.DOY,)
    FIXEDPARAMETERS = (lland_fixed.Pi,)
    RESULTSEQUENCES = (lland_fluxes.EarthSunDistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.earthsundistance = 1.0 + 0.033 * modelutils.cos(
            2 * fix.pi / 366.0 * (der.doy[model.idx_sim] + 1)
        )


class Calc_ExtraterrestrialRadiation_V1(modeltools.Method):
    """Calculate the amount of extraterrestrial radiation of the current day
    :cite:`ref-LARSIM` (based on :cite:`ref-Thompson1981`).

    Basic equation:
      :math:`ExternalTerrestrialRadiation =
      \\frac{Sol \\cdot EarthSunDistance \\cdot (
      SunsetHourAngle \\cdot sin(LatitudeRad) \\cdot sin(SolarDeclination) +
      cos(LatitudeRad) \\cdot cos(SolarDeclination) \\cdot sin(SunsetHourAngle)
      )}{PI}`

      :math:`SunsetHourAngle = (TSU-TSA) \\cdot \\frac{Pi}{24}`

    Examples:

        First, we calculate the extraterrestrial radiation for a latitude of
        approximately 52°N:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.latituderad(0.9)

        The sunshine duration varies between seven hours at winter solstice
        and 16 hours at summer solstice, which corresponds to a daily sum of
        extraterrestrial radiation of 6.1 and 44.4 MJ/m², respectively:

        >>> fluxes.solardeclination = -0.41
        >>> fluxes.earthsundistance = 0.97
        >>> fluxes.tsa = 8.4
        >>> fluxes.tsu = 15.6
        >>> model.calc_extraterrestrialradiation_v1()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(6.087605)

        >>> fluxes.solardeclination = 0.41
        >>> fluxes.earthsundistance = 1.03
        >>> fluxes.tsa = 4.0
        >>> fluxes.tsu = 20.0
        >>> model.calc_extraterrestrialradiation_v1()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(44.44131)
    """

    DERIVEDPARAMETERS = (lland_derived.LatitudeRad,)
    FIXEDPARAMETERS = (
        lland_fixed.Pi,
        lland_fixed.Sol,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SolarDeclination,
        lland_fluxes.EarthSunDistance,
        lland_fluxes.TSA,
        lland_fluxes.TSU,
    )
    RESULTSEQUENCES = (lland_fluxes.ExtraterrestrialRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_sunsethourangle = (flu.tsu - flu.tsa) * fix.pi / 24.0
        flu.extraterrestrialradiation = (
            fix.sol
            * flu.earthsundistance
            / fix.pi
            * (
                d_sunsethourangle
                * modelutils.sin(flu.solardeclination)
                * modelutils.sin(der.latituderad)
                + modelutils.cos(flu.solardeclination)
                * modelutils.cos(der.latituderad)
                * modelutils.sin(d_sunsethourangle)
            )
        )


class Calc_PossibleSunshineDuration_V1(modeltools.Method):
    """Calculate the possible astronomical sunshine duration
    :cite:`ref-LARSIM`.

    Basic equation:
      :math:`PossibleSunshineDuration = max \\bigl(
      max(SCT-Hours/2, TSA) - min(SCT+Hours/2, TSU), 0 \\bigr)`

    Examples:

        We focus on winter conditions with a relatively short possible
        sunshine duration:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> fluxes.tsa(8.4)
        >>> fluxes.tsu(15.6)

        We start with a daily simulation time step.  The possible sunshine
        duration is, as to be expected, the span between sunrise and sunset:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> model.calc_possiblesunshineduration_v1()
        >>> fluxes.possiblesunshineduration
        possiblesunshineduration(7.2)

        The following example calculates the hourly possible sunshine
        durations of the same day:

        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1h'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> sum_ = 0.0
        >>> for idx in range(24):
        ...     model.idx_sim = idx
        ...     model.calc_possiblesunshineduration_v1()
        ...     print(idx+1, end=': ')   # doctest: +ELLIPSIS
        ...     round_(fluxes.possiblesunshineduration.value)
        ...     sum_ += fluxes.possiblesunshineduration.value
        1: 0.0
        ...
        9: 0.6
        10: 1.0
        ...
        15: 1.0
        16: 0.6
        17: 0.0
        ...
        24: 0.0

        The sum of the hourly possible sunshine durations equals the daily
        possible sunshine, of course:

        >>> round_(sum_)
        7.2

        .. testsetup::

            >>> del pub.timegrids
    """

    DERIVEDPARAMETERS = (
        lland_derived.SCT,
        lland_derived.Hours,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TSA,
        lland_fluxes.TSU,
    )
    RESULTSEQUENCES = (lland_fluxes.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_tc = der.sct[model.idx_sim]
        d_t0 = max((d_tc - der.hours / 2.0), flu.tsa)
        d_t1 = min((d_tc + der.hours / 2.0), flu.tsu)
        flu.possiblesunshineduration = max(d_t1 - d_t0, 0.0)


class Calc_DailyPossibleSunshineDuration_V1(modeltools.Method):
    """Calculate the possible astronomical sunshine duration.

    Basic equation:
      :math:`PossibleSunshineDuration =  TSU - TSA`

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> fluxes.tsa(8.4)
        >>> fluxes.tsu(15.6)
        >>> model.calc_dailypossiblesunshineduration()
        >>> fluxes.dailypossiblesunshineduration
        dailypossiblesunshineduration(7.2)
    """

    REQUIREDSEQUENCES = (
        lland_fluxes.TSA,
        lland_fluxes.TSU,
    )
    RESULTSEQUENCES = (lland_fluxes.DailyPossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.dailypossiblesunshineduration = flu.tsu - flu.tsa


class Calc_SP_V1(modeltools.Method):
    """Calculate the relative sum of radiation :cite:`ref-LARSIM-Hilfe`.

    Additional requirements:
      |Model.idx_sim|

    Basic equations:

      .. math::
        SP = S_P^*(SCT + Hours/2) - S_P^*(SCT - Hours/2)

      .. math::
        S_P^*(t) = \\begin{cases}
        0
        &|\\
        TL_P(t) \\leq 0
        \\\\
        50 - 50 \\cdot cos\\bigl(1.8 \\cdot TL_P(t)\\bigr) -
        3.4 \\cdot sin\\bigl(3.6 \\cdot TL_P(t)\\bigr)^2
        &|\\
        0 < TL_P(t) \\leq 50 \\cdot \\frac{2 \\cdot Pi}{360}
        \\\\
        50 - 50 \\cdot cos\\bigl(1.8 \\cdot TL_P(t)\\bigr) +
        3.4 \\cdot sin\\bigl(3.6 \\cdot TL_P(t)\\bigr)^2
        &|\\
        50 \\cdot \\frac{2 \\cdot Pi}{360} < TL_P(t) <
        100 \\cdot \\frac{2 \\cdot Pi}{360}
        \\\\
        100
        &|\\
        100 \\cdot \\frac{2 \\cdot Pi}{360} \\leq TL_P(t)
        \\end{cases}

      .. math::
        TL_P(t) = 100 \\cdot \\frac{2 \\cdot Pi}{360} \\cdot
        \\frac{t - TSA}{TSU - TSA}

    Examples:

        We focus on winter conditions with a relatively short possible
        sunshine duration:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> fluxes.tsa(8.4)
        >>> fluxes.tsu(15.6)

        We start with an hourly simulation time step.  The relative radiation
        sum is, as to be expected, zero before sunrise and after sunset.
        In between, it reaches its maximum around noon:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1h'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(7, 17):
        ...     model.idx_sim = idx
        ...     model.calc_sp_v1()
        ...     print(idx+1, end=': ')
        ...     round_(fluxes.sp.value)
        8: 0.0
        9: 0.853709
        10: 7.546592
        11: 18.473585
        12: 23.126115
        13: 23.126115
        14: 18.473585
        15: 7.546592
        16: 0.853709
        17: 0.0

        The following examples show how method |Calc_SP_V1| works for
        time step sizes longer than one hour:

        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> model.idx_sim = 0
        >>> model.calc_sp_v1()
        >>> fluxes.sp
        sp(100.0)

        >>> pub.timegrids = '2000-01-01', '2000-01-02', '6h'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(4):
        ...     model.idx_sim = idx
        ...     model.calc_sp_v1()
        ...     print((idx+1)*6, end=': ')
        ...     round_(fluxes.sp.value)
        6: 0.0
        12: 50.0
        18: 50.0
        24: 0.0

        >>> pub.timegrids = '2000-01-01', '2000-01-02', '3h'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(8):
        ...     model.idx_sim = idx
        ...     model.calc_sp_v1()
        ...     print((idx+1)*3, end=': ')
        ...     round_(fluxes.sp.value)
        3: 0.0
        6: 0.0
        9: 0.853709
        12: 49.146291
        15: 49.146291
        18: 0.853709
        21: 0.0
        24: 0.0

        Often, method |Calc_SP_V1| calculates a small but unrealistic
        "bumb" around noon (for example, the relative radiation is slightly
        smaller between 11:30 and 12:00 than it is between 11:00 and 11:30):

        >>> pub.timegrids = '2000-01-01', '2000-01-02', '30m'
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(15, 33):
        ...     model.idx_sim = idx
        ...     model.calc_sp_v1()
        ...     print((idx+1)/2, end=': ')
        ...     round_(fluxes.sp.value)
        8.0: 0.0
        8.5: 0.021762
        9.0: 0.831947
        9.5: 2.514315
        10.0: 5.032276
        10.5: 7.989385
        11.0: 10.4842
        11.5: 11.696873
        12.0: 11.429242
        12.5: 11.429242
        13.0: 11.696873
        13.5: 10.4842
        14.0: 7.989385
        14.5: 5.032276
        15.0: 2.514315
        15.5: 0.831947
        16.0: 0.021762
        16.5: 0.0

        .. testsetup::

            >>> del pub.timegrids
        """

    DERIVEDPARAMETERS = (
        lland_derived.SCT,
        lland_derived.Hours,
    )
    FIXEDPARAMETERS = (lland_fixed.Pi,)
    REQUIREDSEQUENCES = (
        lland_fluxes.TSA,
        lland_fluxes.TSU,
    )
    RESULTSEQUENCES = (lland_fluxes.SP,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_fac = 2.0 * fix.pi / 360.0
        flu.sp = 0.0
        for i in range(2):
            if i:
                d_dt = der.hours / 2.0
            else:
                d_dt = -der.hours / 2.0
            d_tlp = (
                100.0
                * d_fac
                * ((der.sct[model.idx_sim] + d_dt - flu.tsa) / (flu.tsu - flu.tsa))
            )
            if d_tlp <= 0.0:
                d_sp = 0.0
            elif d_tlp < 100.0 * d_fac:
                d_sp = 50.0 - 50.0 * modelutils.cos(1.8 * d_tlp)
                d_temp = 3.4 * modelutils.sin(3.6 * d_tlp) ** 2
                if d_tlp <= 50.0 * d_fac:
                    d_sp -= d_temp
                else:
                    d_sp += d_temp
            else:
                d_sp = 100.0
            if i:
                flu.sp += d_sp
            else:
                flu.sp -= d_sp


class Return_DailyGlobalRadiation_V1(modeltools.Method):
    """Calculate and return the daily global radiation :cite:`ref-LARSIM`.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      .. math::
        ExtraterrestrialRadiation \\cdot \\begin{cases}
        AngstromConstant + AngstromFactor \\cdot
        \\frac{sunshineduration}{possiblesunshineduration}
        &|\\
        sunshineduration > 0 \\;\\; \\lor \\;\\; Days < 1
        \\\\
        AngstromAlternative
        &|\\
        sunshineduration = 0 \\;\\; \\land \\;\\; Days \\geq1
        \\end{cases}

    Example:

        You can define the underlying Angstrom coefficients on a monthly
        basis to reflect the annual variability in the relationship between
        sunshine duration and  global radiation.  First, we demonstrate
        this for a daily time-step basis:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromalternative.jan = 0.2
        >>> angstromconstant.feb = 0.2
        >>> angstromfactor.feb = 0.6
        >>> angstromalternative.feb = 0.3
        >>> fluxes.extraterrestrialradiation = 1.7
        >>> model.idx_sim = 1
        >>> round_(model.return_dailyglobalradiation_v1(0.6, 1.0))
        0.68
        >>> model.idx_sim = 2
        >>> round_(model.return_dailyglobalradiation_v1(0.6, 1.0))
        0.952

        If possible sunshine duration is zero, we generally set global
        radiation to zero (even if the actual sunshine duration is larger
        than zero, which might occur as a result of small inconsistencies
        between measured and calculated input data):

        >>> round_(model.return_dailyglobalradiation_v1(0.6, 0.0))
        0.0

        When actual sunshine is zero, the alternative Angstrom coefficient
        applies:

        >>> model.idx_sim = 1
        >>> round_(model.return_dailyglobalradiation_v1(0.0, 1.0))
        0.34
        >>> model.idx_sim = 2
        >>> round_(model.return_dailyglobalradiation_v1(0.0, 1.0))
        0.51

        All of the examples and explanations above hold for short simulation
        time steps, except that parameter |AngstromAlternative| does never
        replace parameter |AngstromConstant|:

        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1h'
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> model.idx_sim = 1
        >>> round_(model.return_dailyglobalradiation_v1(0.0, 1.0))
        0.17

        .. testsetup::

            >>> del pub.timegrids
        """

    CONTROLPARAMETERS = (
        lland_control.AngstromConstant,
        lland_control.AngstromFactor,
        lland_control.AngstromAlternative,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Days,
    )
    REQUIREDSEQUENCES = (lland_fluxes.ExtraterrestrialRadiation,)

    @staticmethod
    def __call__(
        model: modeltools.Model,
        sunshineduration: float,
        possiblesunshineduration: float,
    ) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if possiblesunshineduration > 0.0:
            idx = der.moy[model.idx_sim]
            if (sunshineduration <= 0.0) and (der.days >= 1.0):
                return flu.extraterrestrialradiation * con.angstromalternative[idx]
            return flu.extraterrestrialradiation * (
                con.angstromconstant[idx]
                + con.angstromfactor[idx] * sunshineduration / possiblesunshineduration
            )
        return 0.0


class Calc_GlobalRadiation_V1(modeltools.Method):
    """Calculate the global radiation :cite:`ref-LARSIM`.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      .. math::
        GlobalRadiation =  \\frac{SP}{100}\\cdot \\begin{cases}
        Return\\_DailyGlobalRadiation\\_V1(
        SunshineDuration, PossibleSunshineDuration)
        &|\\
        PossibleSunshineDuration > 0
        \\\\
        Return\\_DailyGlobalRadiation\\_V1(
        DailySunshineDuration, DailyPossibleSunshineDuration)
        &|\\
        PossibleSunshineDuration = 0
        \\end{cases}

    Examples:

        Method |Calc_GlobalRadiation_V1| uses the actual value of |SP| and
        method |Return_DailyGlobalRadiation_V1|, to calculate the current
        global radiation agreeing with the current values of sequence
        |SunshineDuration| and sequence |PossibleSunshineDuration|:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromalternative.jan = 0.2
        >>> inputs.sunshineduration = 0.6
        >>> fluxes.possiblesunshineduration = 1.0
        >>> fluxes.extraterrestrialradiation = 1.7
        >>> fluxes.sp = 50.0
        >>> model.idx_sim = 1
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.34)

        During nightime periods, the value of |PossibleSunshineDuration| is
        zero.  Then, method |Calc_GlobalRadiation_V1| uses the values of the
        sequences |DailySunshineDuration| and |DailyPossibleSunshineDuration|
        as surrogates:

        >>> fluxes.possiblesunshineduration = 0.0
        >>> fluxes.dailysunshineduration = 4.0
        >>> fluxes.dailypossiblesunshineduration = 10.0

        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.255)

        .. testsetup::

            >>> del pub.timegrids
        """

    SUBMETHODS = (Return_DailyGlobalRadiation_V1,)
    CONTROLPARAMETERS = (
        lland_control.AngstromConstant,
        lland_control.AngstromFactor,
        lland_control.AngstromAlternative,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Days,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.SunshineDuration,
        lland_fluxes.ExtraterrestrialRadiation,
        lland_fluxes.PossibleSunshineDuration,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
        lland_fluxes.SP,
    )
    RESULTSEQUENCES = (lland_fluxes.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if flu.possiblesunshineduration > 0.0:
            d_act = inp.sunshineduration
            d_pos = flu.possiblesunshineduration
        else:
            d_act = flu.dailysunshineduration
            d_pos = flu.dailypossiblesunshineduration
        flu.globalradiation = (
            flu.sp / 100.0 * model.return_dailyglobalradiation_v1(d_act, d_pos)
        )


class Update_LoggedGlobalRadiation_V1(modeltools.Method):
    """Log the global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> simulationstep('8h')
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> logs.loggedglobalradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedglobalradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.globalradiation,
        ...                          logs.loggedglobalradiation))
        >>> test.nexts.globalradiation = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedglobalradiation
        >>> test()
        | ex. | globalradiation |           loggedglobalradiation |
        -----------------------------------------------------------
        |   1 |             1.0 | 1.0  0.0                    0.0 |
        |   2 |             3.0 | 3.0  1.0                    0.0 |
        |   3 |             2.0 | 2.0  3.0                    1.0 |
        |   4 |             4.0 | 4.0  2.0                    3.0 |
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (lland_fluxes.GlobalRadiation,)
    UPDATEDSEQUENCES = (lland_logs.LoggedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedglobalradiation[idx] = log.loggedglobalradiation[idx - 1]
        log.loggedglobalradiation[0] = flu.globalradiation


class Calc_DailyGlobalRadiation_V1(modeltools.Method):
    """Calculate the daily global radiation.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`DailyGlobalRadiation = Return\\_DailyGlobalRadiation\\_(
      DailySunshineDuration, DailyPossibleSunshineDuration)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromconstant.feb = 0.2
        >>> angstromfactor.feb = 0.6

        We define the extraterrestrial radiation to 10 MJ/m² and the
        possible sunshine duration to 12 hours:

        >>> fluxes.extraterrestrialradiation = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0

        We define a daily simulation step size and update the relevant
        derived parameters:

        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> derived.moy.update()
        >>> derived.nmblogentries.update()

        Applying the Angstrom coefficients for January and February on
        the defined extraterrestrial radiation and a sunshine duration
        of 7.2 hours results in a daily global radiation sum of 4.0 MJ/m²
        and 5.6 MJ/m², respectively:

        >>> model.idx_sim = 1
        >>> fluxes.dailysunshineduration = 7.2
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(4.0)

        >>> model.idx_sim = 2
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(5.6)

        Finally, we demonstrate for January that method
        |Calc_DailyGlobalRadiation_V1| calculates the same values for an
        hourly simulation time step, as long as the daily sum of sunshine
        duration remains identical:

        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1h'
        >>> derived.moy.update()
        >>> derived.nmblogentries.update()

        The actual simulation step starts at 11 o'clock and ends at 12 o'clock:

        >>> model.idx_sim = pub.timegrids.init['2000-01-31 11:00']
        >>> fluxes.dailysunshineduration = 7.2
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = (Return_DailyGlobalRadiation_V1,)
    CONTROLPARAMETERS = (
        lland_control.AngstromConstant,
        lland_control.AngstromFactor,
        lland_control.AngstromAlternative,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Days,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.ExtraterrestrialRadiation,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
    )
    UPDATEDSEQUENCES = (lland_fluxes.DailyGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.dailyglobalradiation = model.return_dailyglobalradiation_v1(
            flu.dailysunshineduration, flu.dailypossiblesunshineduration
        )


class Calc_AdjustedGlobalRadiation_V1(modeltools.Method):
    """Adjust the current global radiation to the daily global radiation.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`AdjustedGlobalRadiation = GlobalRadiation \\cdot
      \\frac{DailyGlobalRadiation}{\\sum LoggedGlobalRadiation}`

    Examples:

        The purpose of method |Calc_AdjustedGlobalRadiation_V1| is to
        adjust hourly global radiation values (or those of other short
        simulation time steps) so that their sum over the last 24 hours
        equals the global radiation value directly calculated with the
        relative sunshine duration over the last 24 hours.  We try to
        explain this somewhat contraintuitive approach by building up
        the examples on the examples on the documentation on method
        |Calc_DailyGlobalRadiation_V1|.

        Again, we start with a daily simulation time step:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> derived.nmblogentries.update()

        For such a daily simulation time step, the values of the
        sequences |GlobalRadiation|, |DailyGlobalRadiation|, and
        |LoggedGlobalRadiation| must be identical:

        >>> model.idx_sim = 1
        >>> fluxes.globalradiation = 4.0
        >>> fluxes.dailyglobalradiation = 4.0
        >>> logs.loggedglobalradiation = 4.0

        After calling method |Calc_AdjustedGlobalRadiation_V1|, the
        same holds for the adjusted global radiation sum:

        >>> model.calc_adjustedglobalradiation_v1()
        >>> fluxes.adjustedglobalradiation
        adjustedglobalradiation(4.0)

        Normally, one would not expect method |Calc_AdjustedGlobalRadiation_V1|
        to have an effect when applied on daily simulation time steps at all.
        However, it corrects "wrong" predefined global radiation values:

        >>> fluxes.dailyglobalradiation = 5.6
        >>> model.calc_adjustedglobalradiation_v1()
        >>> fluxes.adjustedglobalradiation
        adjustedglobalradiation(5.6)

        We now demonstrate how method |Calc_AdjustedGlobalRadiation_V1|
        actually works for hourly simulation time steps:

        >>> simulationstep('1h')
        >>> derived.nmblogentries.update()

        The daily global radiation value does not depend on the simulation
        time step.  We reset it to 4 MJ/m²/d:

        >>> fluxes.dailyglobalradiation = 4.0

        The other global radiation values now must be smaller and vary
        throughout the day.  We set them consistently with the values
        of the logged sunshine duration in the documentation on method
        |Calc_DailyGlobalRadiation_V1|:

        >>> fluxes.globalradiation = 0.8
        >>> logs.loggedglobalradiation = (
        ...     0.8, 0.8, 0.2, 0.1, 0.1, 0.0,
        ...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ...     0.0, 0.1, 0.4, 0.6, 0.7, 0.8)

        Compared with the total 24 hours, the simulation time steps around
        noon are relatively sunny, both for the current and the last day
        (see the first and the last entries of the log sequence for sunshine
        duration).  Accordingly, the sum of the hourly global radiation
        values (4.6 W/m²)  is larger than the directly calculated daily sum
        (4.0 W/m²).  Method |Calc_AdjustedGlobalRadiation_V1| uses the
        fraction of both sums to finally calculate the adjusted global
        radiation (:math:`0.8 \\cdot 4.0 / 4.6`):

        >>> model.calc_adjustedglobalradiation_v1()
        >>> fluxes.adjustedglobalradiation
        adjustedglobalradiation(0.695652)
    """

    DERIVEDPARAMETERS = (lland_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        lland_fluxes.GlobalRadiation,
        lland_fluxes.DailyGlobalRadiation,
        lland_logs.LoggedGlobalRadiation,
    )
    UPDATEDSEQUENCES = (lland_fluxes.AdjustedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        d_glob_sum = 0.0
        for idx in range(der.nmblogentries):
            d_glob_sum += log.loggedglobalradiation[idx]
        flu.adjustedglobalradiation = (
            flu.globalradiation * flu.dailyglobalradiation / d_glob_sum
        )


class Calc_ET0_V1(modeltools.Method):
    """Calculate reference evapotranspiration after Turc-Wendling.

    Basic equation:
      :math:`ET0 = KE \\cdot
      \\frac{(8.64 \\cdot Glob+93 \\cdot KF) \\cdot (TKor+22)}
      {165 \\cdot (TKor+123) \\cdot (1 + 0.00019 \\cdot min(HNN, 600))}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> ke(1.1)
        >>> kf(0.6)
        >>> hnn(200.0, 600.0, 1000.0)
        >>> inputs.glob = 200.0
        >>> fluxes.tkor = 15.0
        >>> model.calc_et0_v1()
        >>> fluxes.et0
        et0(3.07171, 2.86215, 2.86215)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KE,
        lland_control.KF,
        lland_control.HNN,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.Glob,
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (lland_fluxes.ET0,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = con.ke[k] * (
                (8.64 * inp.glob + 93.0 * con.kf[k])
                * (flu.tkor[k] + 22.0)
                / (
                    165.0
                    * (flu.tkor[k] + 123.0)
                    * (1.0 + 0.00019 * min(con.hnn[k], 600.0))
                )
            )


class Calc_ET0_WET0_V1(modeltools.Method):
    """Correct the given reference evapotranspiration and update the
    corresponding log sequence.

    Basic equation:
      :math:`ET0_{new} = WfET0 \\cdot KE \\cdot PET +
      (1-WfET0) \\cdot ET0_{old}`

    Example:

        Prepare four hydrological response units with different value
        combinations of parameters |KE| and |WfET0|:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(4)
        >>> ke(0.8, 1.2, 0.8, 1.2)
        >>> wfet0(2.0, 2.0, 0.2, 0.2)

        Note that the actual value of time dependend parameter |WfET0|
        is reduced due the difference between the given parameter and
        simulation time steps:

        >>> from hydpy import round_
        >>> round_(wfet0.values)
        1.0, 1.0, 0.1, 0.1

        For the first two hydrological response units, the given |PET|
        value is modified by -0.4 mm and +0.4 mm, respectively.  For the
        other two response units, which weight the "new" evapotranspiration
        value with 10 %, |ET0| does deviate from the old value of |WET0|
        by -0.04 mm and +0.04 mm only:

        >>> inputs.pet = 2.0
        >>> logs.wet0 = 2.0
        >>> model.calc_et0_wet0_v1()
        >>> fluxes.et0
        et0(1.6, 2.4, 1.96, 2.04)
        >>> logs.wet0
        wet0([[1.6, 2.4, 1.96, 2.04]])
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.WfET0,
        lland_control.KE,
    )
    REQUIREDSEQUENCES = (lland_inputs.PET,)
    UPDATEDSEQUENCES = (lland_logs.WET0,)
    RESULTSEQUENCES = (lland_fluxes.ET0,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = (
                con.wfet0[k] * con.ke[k] * inp.pet
                + (1.0 - con.wfet0[k]) * log.wet0[0, k]
            )
            log.wet0[0, k] = flu.et0[k]


class Calc_EvPo_V1(modeltools.Method):
    """Calculate the potential evapotranspiration for the relevant land
    use and month.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`EvPo = FLn \\cdot ET0`

    Example:

        For clarity, this is more of a kind of an integration example.
        Parameter |FLn| both depends on time (the actual month) and space
        (the actual land use).  Firstly, let us define a initialization
        time period spanning the transition from June to July:

        >>> from hydpy import pub
        >>> pub.timegrids = '30.06.2000', '02.07.2000', '1d'

        Secondly, assume that the considered subbasin is differenciated in
        two HRUs, one of primarily consisting of arable land and the other
        one of deciduous forests:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)

        Thirdly, set the |FLn|
        values, one for the relevant months and land use classes:

        >>> fln.acker_jun = 1.299
        >>> fln.acker_jul = 1.304
        >>> fln.laubw_jun = 1.350
        >>> fln.laubw_jul = 1.365

        Fourthly, the index array connecting the simulation time steps
        defined above and the month indexes (0...11) can be retrieved
        from the |pub| module.  This can be done manually more
        conveniently via its update method:

        >>> derived.moy.update()
        >>> derived.moy
        moy(5, 6)

        Finally, the actual method (with its simple equation) is applied
        as usual:

        >>> fluxes.et0 = 2.0
        >>> model.idx_sim = 0
        >>> model.calc_evpo_v1()
        >>> fluxes.evpo
        evpo(2.598, 2.7)
        >>> model.idx_sim = 1
        >>> model.calc_evpo_v1()
        >>> fluxes.evpo
        evpo(2.608, 2.73)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FLn,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (lland_fluxes.ET0,)
    RESULTSEQUENCES = (lland_fluxes.EvPo,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.evpo[k] = con.fln[con.lnk[k] - 1, der.moy[model.idx_sim]] * flu.et0[k]


class Calc_NBes_Inzp_V1(modeltools.Method):
    """Calculate stand precipitation and update the interception storage
    accordingly.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      .. math::
        NBes = \\begin{cases}
        PKor
        &|\\
        Inzp = KInz
        \\\\
        0
        &|\\
        Inzp < KInz
        \\end{cases}

    Examples:

        Initialise five HRUs with different land usages:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
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
    """Calculate the ratio of frozen to total precipitation :cite:`ref-LARSIM`.

    Basic equation:
      :math:`SNRatio =
      min\\left(max\\left(\\frac{(TGr-TSp/2-TKor)}{TSp}, 0\\right), 1\\right)`

    Examples:

        In the first example, the threshold temperature of seven
        hydrological response units is 0 °C and the temperature interval
        of mixed precipitation 2 °C:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
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


# class Calc_F2SIMax_V1(modeltools.Method):
#     """
#     Factor for calculation of snow interception capacity.
#
#     Basic equation:
#        :math:`F2SIMax = \\Bigl \\lbrace
#        {
#        {2.0 \\ | \\ TKor > -1°C}
#        \\atop
#        {2.5 + 0.5 \\cdot TKor \\ | \\ -3.0 °C \\leq TKor \\leq -1.0 °C}
#        \\atop
#        {1.0 \\ | \\ TKor < -3.0 °C}
#        }`
#
#     Example:
#
#         >>> from hydpy.models.lland import *
#         >>> parameterstep('1d')
#         >>> nhru(5)
#         >>> fluxes.tkor(-5.0, -3.0, -2.0, -1.0,  0.0)
#         >>> model.calc_f2simax()
#         >>> fluxes.f2simax
#         f2simax(1.0, 1.0, 1.5, 2.0, 2.0)
#
#     """
#     CONTROLPARAMETERS = (
#         lland_control.NHRU,
#     )
#     REQUIREDSEQUENCES = (
#         lland_fluxes.TKor,
#     )
#     RESULTSEQUENCES = (
#         lland_fluxes.F2SIMax,
#     )
#
#     @staticmethod
#     def __call__(model: modeltools.Model) -> None:
#         con = model.parameters.control.fastaccess
#         flu = model.sequences.fluxes.fastaccess
#         for k in range(con.nhru):
#             if flu.tkor[k] < -3.:
#                 flu.f2simax[k] = 1.
#             elif (flu.tkor[k] >= -3.) and (flu.tkor[k] <= -1.):
#                 flu.f2simax[k] = 2.5 + 0.5*flu.tkor[k]
#             else:
#                 flu.f2simax[k] = 2.0
#
#
# class Calc_SInzpCap_V1(modeltools.Method):
#     """
#     Snow interception capacity
#
#     Basic equation:
#        :math:`SInzpCap = F1SIMax * F2SIMax`
#
#     Example:
#
#         >>> from hydpy.models.lland import *
#         >>> parameterstep('1d')
#         >>> nhru(3)
#         >>> lnk(ACKER, LAUBW, NADELW)
#         >>> derived.moy = 5
#         >>> derived.f1simax.acker_jun = 9.5
#         >>> derived.f1simax.laubw_jun = 11.0
#         >>> derived.f1simax.nadelw_jun = 12.0
#         >>> fluxes.f2simax(1.5)
#         >>> model.calc_sinzpcap_v1()
#         >>> fluxes.sinzpcap
#         sinzpcap(14.25, 16.5, 18.0)
#         >>> derived.moy = 0
#         >>> derived.f1simax.acker_jan = 6.0
#         >>> derived.f1simax.laubw_jan = 6.5
#         >>> derived.f1simax.nadelw_jan = 10.0
#         >>> model.calc_sinzpcap_v1()
#         >>> fluxes.sinzpcap
#         sinzpcap(9.0, 9.75, 15.0)
#     """
#
#     CONTROLPARAMETERS = (
#         lland_control.NHRU,
#         lland_control.Lnk,
#     )
#     DERIVEDPARAMETERS = (
#         lland_derived.F1SIMax,
#         lland_derived.MOY,
#     )
#     REQUIREDSEQUENCES = (
#         lland_fluxes.F2SIMax,
#     )
#     RESULTSEQUENCES = (
#         lland_fluxes.SInzpCap,
#     )
#
#     @staticmethod
#     def __call__(model: modeltools.Model) -> None:
#         con = model.parameters.control.fastaccess
#         der = model.parameters.derived.fastaccess
#         flu = model.sequences.fluxes.fastaccess
#         for k in range(con.nhru):
#             flu.sinzpcap[k] = (
#                 der.f1simax[con.lnk[k] - 1, der.moy[model.idx_sim]] *
#                 flu.f2simax[k])
#
#
# class Calc_F2SIRate_V1(modeltools.Method):
#     """
#     Factor for calculation of snow interception capacity.
#
#     Basic equation:
#        :math:`F2SIRate =
#
#     Example:
#
#         >>> from hydpy.models.lland import *
#         >>> parameterstep('1d')
#         >>> nhru(5)
#         >>> p3sirate(0.003)
#         >>> states.stinz = 0.0, 0.5, 1.0, 5.0, 10.0
#         >>> model.calc_f2sirate()
#         >>> fluxes.f2sirate
#         f2sirate(0.0, 0.0015, 0.003, 0.015, 0.03)
#     """
#
#     CONTROLPARAMETERS = (
#         lland_control.NHRU,
#         lland_control.P3SIRate,
#     )
#     REQUIREDSEQUENCES = (
#         lland_states.STInz,
#     )
#     RESULTSEQUENCES = (
#         lland_fluxes.F2SIRate,
#     )
#
#     @staticmethod
#     def __call__(model: modeltools.Model) -> None:
#         con = model.parameters.control.fastaccess
#         flu = model.sequences.fluxes.fastaccess
#         sta = model.sequences.states.fastaccess
#         for k in range(con.nhru):
#             flu.f2sirate[k] = sta.stinz[k] * con.p3sirate
#
#
# class Calc_SInzpRate_V1(modeltools.Method):
#     """
#     Snow interception rate
#
#     Basic equation:
#        :math:`SInzpRate = min(F1SIRate + F2SIRate; 1)`
#
#     Example:
#         >>> from hydpy.models.lland import *
#         >>> parameterstep('1d')
#         >>> nhru(3)
#         >>> derived.f1sirate.acker_jan = 0.22
#         >>> derived.f1sirate.laubw_jan = 0.30
#         >>> derived.f1sirate.nadelw_jan = 0.32
#         >>> fluxes.f2sirate = 0.0015, 0.003, 0.015
#     """
#     CONTROLPARAMETERS = (
#         lland_control.NHRU,
#     )
#     DERIVEDPARAMETERS = (
#         lland_derived.F1SIRate,
#     )
#     REQUIREDSEQUENCES = (
#         lland_fluxes.F2SIRate,
#     )
#     RESULTSEQUENCES = (
#         lland_fluxes.SInzpRate,
#     )
#
#     @staticmethod
#     def __call__(model: modeltools.Model) -> None:
#         con = model.parameters.control.fastaccess
#         der = model.parameters.derived.fastaccess
#         flu = model.sequences.fluxes.fastaccess
#         Stimmt 1 min oder max?
#         for k in range(con.nhru):
#             flu.sinzprate[k] = min(
#                 der.f1sirate[con.lnk[k] - 1, der.moy[model.idx_sim]] +
#                 flu.f2sirate[k], 1)
#
#
# class Calc_NBes_SInz_V1(modeltools.Method):
#     """Update interception storage.
#
#     Example:
#
#         >>> from hydpy.models.lland import *
#         >>> parameterstep('1d')
#         >>> nhru(4)
#         >>> lnk(ACKER, NADELW, NADELW, NADELW)
#         >>> # states.sinz()
#         >>> # states.stinz()
#         >>> # fluxes.sinzcap()
#         >>> # fluxes.sinzrate()
#         >>> # fluxes.nkor()
#         >>> # model.calc_nbes_sinz()
#         >>> # fluxes.sbes
#         >>> # fluxes.nbes
#         >>> # states.stinz
#         >>> # states.sinz
#     """
#
#     CONTROLPARAMETERS = (
#         lland_control.NHRU,
#         lland_control.Lnk,
#     )
#     REQUIREDSEQUENCES = (
#         lland_fluxes.SInzpRate,
#         lland_fluxes.NKor,
#         lland_fluxes.SInzpCap,
#         lland_aides.SNRatio,
#     )
#     UPDATEDSEQUENCES = (
#         lland_states.SInz,
#         lland_states.STInz,
#     )
#     RESULTSEQUENCES = (
#         lland_fluxes.NBes,
#         lland_fluxes.SBes,
#     )
#
#     @staticmethod
#     def __call__(model: modeltools.Model) -> None:
#         con = model.parameters.control.fastaccess
#         der = model.parameters.derived.fastaccess
#         flu = model.sequences.fluxes.fastaccess
#         aid = model.sequences.aides.fastaccess
#         sta = model.sequences.states.fastaccess
#         for k in range(con.nhru):
#             if con.lnk[k] in (WASSER, FLUSS, SEE):
#                 sta.sinz[k] = 0.
#             elif con.lnk[k] == NADELW:
#                 if flu.nkor[k] > flu.sinzprate[k]:
#                     d_max = flu.sinzprate[k]
#                     d_besrate = flu.nkor[k] - flu.sinzprate[k]
#                 else:
#                     d_max = flu.nkor[k]
#                     d_besrate = 0
#                 d_cap = flu.sinzpcap[con.lnk[k] - 1, der.moy[model.idx_sim]]
#
#                 flu.nbes[k] = max(d_max + sta.sinz[k] - d_cap, 0.) + d_besrate
#                 flu.sbes[k] = aid.snratio[k] * flu.nbes[k]
#                 d_ninz = flu.nkor[k] - flu.nbes[k]
#                 d_sinz = aid.snratio[k] * d_ninz
#                 sta.sinz[k] += d_ninz
#                 sta.stinz[k] += d_sinz
#                 d_nbes = max(sta.sinz[k] - con.pwmax[k] * sta.stinz[k], 0.)
#                 flu.nbes[k] += d_nbes
#                 sta.sinz[k] -= d_nbes


class Calc_SBes_V1(modeltools.Method):
    """Calculate the frozen part of stand precipitation.

    Basic equation:
      :math:`SBes = SNRatio \\cdot NBes`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
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
        >>> parameterstep('1d')
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


class Calc_WGTF_V1(modeltools.Method):
    """Calculate the heat flux according to the degree-day method
    :cite:`ref-LARSIM`.

    Basic equation:
      :math:`WGTF = GTF \\cdot (TKor - TRefT) \\cdot RSchmelz`

    Examples:

        Initialise six hydrological response units with identical degree-day
        factors and temperature thresholds, but different combinations of
        land use and air temperature:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
        |SEE|) in principally identical for all other ref-use type
        (here, |ACKER| and |LAUBW|).  The results of the last three
        response units show the expectable linear relationship.  However,
        note that that |WGTF| is allowed to be negative:

        >>> model.calc_wgtf_v1()
        >>> fluxes.wgtf
        wgtf(0.0, 0.0, 0.835, 0.835, 0.0, -0.835)
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
    of ingoing precipitation (:cite:`ref-LARSIM`, modified).

    Method |Calc_WNied_V1| assumes that the temperature of precipitation
    equals air temperature minus |TRefN|.

    Basic equation:
      :math:`WNied = (TKor - TRefN) \\cdot
      (CPEis \\cdot SBes + CPWasser \\cdot (NBes - SBes))`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(ACKER, ACKER, ACKER, ACKER, WASSER)
        >>> trefn(-2.0, 2.0, 2.0, 2.0, 2.0)
        >>> fluxes.tkor(1.0)
        >>> fluxes.nbes = 10.0
        >>> fluxes.sbes = 0.0, 0.0, 5.0, 10.0, 10.0
        >>> model.calc_wnied_v1()
        >>> fluxes.wnied
        wnied(0.125604, -0.041868, -0.031384, -0.0209, 0.0)
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
        >>> parameterstep('1d')
        >>> nhru(6)
        >>> lnk(ACKER, ACKER, ACKER, ACKER, ACKER, WASSER)
        >>> trefn(1.0)
        >>> states.esnow = 0.02
        >>> fluxes.tkor = 4.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> fluxes.nbes = 10.0
        >>> fluxes.sbes = 0.0, 0.0, 5.0, 10.0, 5.0, 5.0
        >>> fluxes.wada = 0.0, 0.0, 0.0, 0.0, 5.0, 5.0
        >>> model.calc_wnied_esnow_v1()
        >>> fluxes.wnied
        wnied(0.125604, -0.041868, -0.031384, -0.0209, -0.01045, 0.0)
        >>> states.esnow
        esnow(0.145604, -0.021868, -0.011384, -0.0009, 0.00955, 0.0)
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
    """Calculate and return the saturation vapour pressure over an
    arbitrary surface for the given temperature :cite:`ref-LARSIM`
    (based on :cite:`ref-Weischt1983`).

    Basic equation:
      :math:`0.61078 \\cdot
      2.71828^{\\frac{17.08085 \\cdot temperature}{temperature + 234.175}}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_saturationvapourpressure_v1(10.0))
        1.229385
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        temperature: float,
    ) -> float:
        return 0.61078 * 2.71828 ** (17.08085 * temperature / (temperature + 234.175))


class Return_SaturationVapourPressureSlope_V1(modeltools.Method):
    """Calculate and return the saturation vapour pressure slope over an
    arbitrary surface for the given temperature.

    Basic equation (derivative of |Return_SaturationVapourPressure_V1|:
      :math:`\\frac{2443.06 \\cdot
      exp((17.08085 \\cdot temperature) / (temperature + 234.175)}
      {(temperature+234.175)^2}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_saturationvapourpressureslope_v1(10.0))
        0.082477
        >>> dx = 1e-6
        >>> round_((model.return_saturationvapourpressure_v1(10.0+dx) -
        ...         model.return_saturationvapourpressure_v1(10.0-dx))/2/dx)
        0.082477
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        temperature: float,
    ) -> float:
        return (
            2443.06
            * modelutils.exp(17.08085 * temperature / (temperature + 234.175))
            / (temperature + 234.175) ** 2
        )


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
        saturationvapourpressure(0.285087, 0.61078, 1.229385)
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


class Calc_DailySaturationVapourPressure_V1(modeltools.Method):
    """Calculate the daily saturation vapour pressure over arbitrary surfaces.

    Basic equation:
      :math:`DailySaturationVapourPressure =
      Return\\_SaturationVapourPressure\\_V1(TKorTag)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkortag = -10.0, 0.0, 10.0
        >>> model.calc_dailysaturationvapourpressure_v1()
        >>> fluxes.dailysaturationvapourpressure
        dailysaturationvapourpressure(0.285087, 0.61078, 1.229385)
    """

    SUBMETHODS = (Return_SaturationVapourPressure_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (lland_fluxes.TKorTag,)
    RESULTSEQUENCES = (lland_fluxes.DailySaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dailysaturationvapourpressure[
                k
            ] = model.return_saturationvapourpressure_v1(flu.tkortag[k])


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    """Calculate the daily slope of the saturation vapour pressure curve.

    Basic equation:
      :math:`SaturationVapourPressureSlope =
      Return\\_SaturationVapourPressureSlope\\_V1(TKor)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkor = -10.0, 0.0, 10.0
        >>> fluxes.saturationvapourpressure = 0.285096, 0.6108, 1.229426
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> fluxes.saturationvapourpressureslope
        saturationvapourpressureslope(0.022691, 0.044551, 0.082477)
    """

    SUBMETHODS = (Return_SaturationVapourPressureSlope_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (lland_fluxes.TKor,)
    RESULTSEQUENCES = (lland_fluxes.SaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.saturationvapourpressureslope[
                k
            ] = model.return_saturationvapourpressureslope_v1(flu.tkor[k])


class Calc_DailySaturationVapourPressureSlope_V1(modeltools.Method):
    """Calculate the daily slope of the saturation vapour pressure curve.

    Basic equation:
      :math:`DailySaturationVapourPressureSlope =
      Return\\_SaturationVapourPressureSlope\\_V1(TKorTag)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkortag = 10.0, 0.0, -10.0
        >>> model.calc_dailysaturationvapourpressureslope_v1()
        >>> fluxes.dailysaturationvapourpressureslope
        dailysaturationvapourpressureslope(0.082477, 0.044551, 0.022691)
    """

    SUBMETHODS = (Return_SaturationVapourPressureSlope_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (lland_fluxes.TKorTag,)
    RESULTSEQUENCES = (lland_fluxes.DailySaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dailysaturationvapourpressureslope[
                k
            ] = model.return_saturationvapourpressureslope_v1(flu.tkortag[k])


class Return_ActualVapourPressure_V1(modeltools.Method):
    """Calculate and return the actual vapour pressure for the given
    saturation vapour pressure and relative humidity. :cite:`ref-LARSIM`
    (based on `ref-Weischet1983`)

    Basic equation:
      :math:`saturationvapourpressure \\cdot relativehumidity / 100`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_actualvapourpressure_v1(2.0, 60.0))
        1.2
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        saturationvapourpressure: float,
        relativehumidity: float,
    ) -> float:
        return saturationvapourpressure * relativehumidity / 100.0


class Calc_ActualVapourPressure_V1(modeltools.Method):
    """Calculate the actual vapour pressure.

    Basic equation:
      :math:`ActualVapourPressure = Return\\_ActualVapourPressure\\_V1(
      SaturationVapourPressure, RelativeHumidity)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep()
        >>> nhru(1)
        >>> derived.nmblogentries.update()
        >>> inputs.relativehumidity = 60.0
        >>> fluxes.saturationvapourpressure = 2.0
        >>> model.calc_actualvapourpressure_v1()
        >>> fluxes.actualvapourpressure
        actualvapourpressure(1.2)
    """

    SUBMETHODS = (Return_ActualVapourPressure_V1,)
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
            flu.actualvapourpressure[k] = model.return_actualvapourpressure_v1(
                flu.saturationvapourpressure[k], inp.relativehumidity
            )


class Calc_DailyActualVapourPressure_V1(modeltools.Method):
    """Calculate the daily actual vapour pressure.

    Basic equation:
      :math:`DailyActualVapourPressure = Return\\_ActualVapourPressure\\_V1(
      DailySaturationVapourPressure, DailyRelativeHumidity)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep()
        >>> nhru(1)
        >>> derived.nmblogentries.update()
        >>> fluxes.dailyrelativehumidity = 40.0
        >>> fluxes.dailysaturationvapourpressure = 4.0
        >>> model.calc_dailyactualvapourpressure_v1()
        >>> fluxes.dailyactualvapourpressure
        dailyactualvapourpressure(1.6)
    """

    SUBMETHODS = (Return_ActualVapourPressure_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_fluxes.DailyRelativeHumidity,
        lland_fluxes.DailySaturationVapourPressure,
    )
    RESULTSEQUENCES = (lland_fluxes.DailyActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dailyactualvapourpressure[k] = model.return_actualvapourpressure_v1(
                flu.dailysaturationvapourpressure[k],
                flu.dailyrelativehumidity,
            )


class Calc_DailyNetLongwaveRadiation_V1(modeltools.Method):
    """Calculate the daily net longwave radiation.

    Basic equation above a snow-free surface:
       :math:`DailyNetLongwaveRadiation =
       Sigma \\cdot (TKorTag + 273.15)^4 \\cdot
       \\left(Emissivity - FrAtm \\cdot
       \\left(\\frac{DailyActualVapourPressure \\cdot 10}
       {TKorTag + 273.15}\\right)^{1/7}\\right) \\cdot
       \\left(0.2 + 0.8 \\cdot
       \\frac{DailySunshineDuration}{DailyPossibleSunshineDuration}\\right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> emissivity(0.95)
        >>> fluxes.tkortag = 22.1, 0.0
        >>> fluxes.dailyactualvapourpressure = 1.6, 0.6
        >>> fluxes.dailysunshineduration = 12.0
        >>> fluxes.dailypossiblesunshineduration = 14.0
        >>> model.calc_dailynetlongwaveradiation_v1()
        >>> fluxes.dailynetlongwaveradiation
        dailynetlongwaveradiation(3.495045, 5.027685)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Emissivity,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKorTag,
        lland_fluxes.DailyActualVapourPressure,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
    )
    RESULTSEQUENCES = (lland_fluxes.DailyNetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_relsunshine = flu.dailysunshineduration / flu.dailypossiblesunshineduration
        for k in range(con.nhru):
            d_temp = flu.tkortag[k] + 273.15
            flu.dailynetlongwaveradiation[k] = (
                (0.2 + 0.8 * d_relsunshine)
                * fix.sigma
                * d_temp ** 4
                * (
                    con.emissivity
                    - fix.fratm
                    * (flu.dailyactualvapourpressure[k] * 10.0 / d_temp) ** (1.0 / 7.0)
                )
            )


class Return_NetLongwaveRadiationSnow_V1(modeltools.Method):
    """Calculate and return the net longwave radiation for snow-covered areas.

    Method |Return_NetLongwaveRadiationSnow_V1| relies on two different
    equations, one for forests (|LAUBW|, |MISCHW|, and |NADELW|) and the
    other other one for all other land use classes :cite:`ref-LARSIM` (based
    on :cite:`ref-Thompson1981`).

    Basic equation:

      .. math::
        \\begin{cases}
        Fr \\cdot \\Bigl(0.97 \\cdot Sigma \\cdot \\bigl((TKor + 273.15)^4 -
        R_{Latm}\\bigl)\\Bigl)
        &|\\
        Lnk \\in \\{LAUBW, MISCHW, NADELW\\}
        \\\\
        Sigma \\cdot (TempSSurface + 273.15)^4 - R_{Latm}
        &|\\
        Lnk \\notin \\{LAUBW, MISCHW, NADELW\\}
        \\end{cases}

      :math:`R_{Latm} =
      FrAtm \\cdot Sigma \\cdot  (Tkor+273.15)^4 \\cdot
      \\left(\\frac{ActualVapourPressure \\cdot 10}{TKor+273.15}\\right)^{1/7}
      \\cdot \\left(1 + 0.22 \\cdot \\left(
      1 - \\frac{DailySunshineDuration}{DailyPossibleSunshineDuration}\\right)^2
      \\right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)
        >>> derived.moy(5)
        >>> derived.days(1/24)
        >>> derived.fr(0.5)
        >>> emissivity(0.95)
        >>> fluxes.tempssurface = -5.0
        >>> fluxes.tkor = 0.0
        >>> fluxes.actualvapourpressure = 0.6
        >>> fluxes.dailysunshineduration = 12.0
        >>> fluxes.dailypossiblesunshineduration = 14.0
        >>> from hydpy import print_values
        >>> for hru in range(2):
        ...     print_values(
        ...         [hru, model.return_netlongwaveradiationsnow_v1(hru)])
        0, 0.208605
        1, 0.127729
    """

    CONTROLPARAMETERS = (lland_control.Lnk,)
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Days,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_fluxes.TKor,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
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
        d_relsunshine = flu.dailysunshineduration / flu.dailypossiblesunshineduration
        d_sigma = fix.sigma * der.days
        d_temp = flu.tkor[k] + 273.15
        d_ratm = (
            fix.fratm
            * d_sigma
            * d_temp ** 4
            * (flu.actualvapourpressure[k] * 10.0 / d_temp) ** (1.0 / 7.0)
            * (1.0 + 0.22 * (1.0 - d_relsunshine) ** 2)
        )
        if con.lnk[k] in (LAUBW, MISCHW, NADELW):
            idx = der.moy[model.idx_sim]
            return der.fr[con.lnk[k] - 1, idx] * (
                0.97 * d_sigma * (flu.tkor[k] + 273.15) ** 4 - d_ratm
            )
        return d_sigma * (flu.tempssurface[k] + 273.15) ** 4 - d_ratm


class Update_TauS_V1(modeltools.Method):
    """Calculate the dimensionless age of the snow layer :cite:`ref-LARSIM`
    (based on :cite:`ref-LUBW2006b`).

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
        >>> parameterstep('1d')
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
                d_r2 = min(d_r1 ** 10, 1.0)
                sta.taus[k] *= max(1 - 0.1 * flu.sbes[k], 0.0)
                sta.taus[k] += (d_r1 + d_r2 + 0.03) / 1e6 * der.seconds
            else:
                sta.taus[k] = modelutils.nan


class Calc_ActualAlbedo_V1(modeltools.Method):
    """Calculate the current albedo value :cite:`ref-LARSIM` (based on
    :cite:`ref-LUBW2006b`).

    For snow-free surfaces, method |Calc_ActualAlbedo_V1| takes the
    value of parameter |Albedo| relevant for the given landuse and month.
    For snow conditions, it estimates the albedo based on the snow age,
    as shown by the following equation.

    Basic equation:
      :math:`AlbedoSnow = Albedo0Snow \\cdot
      \\left(1-SnowAgingFactor \\cdot \\frac{TauS}{1 + TauS}\\right)`

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(ACKER, VERS, VERS, VERS, VERS)
        >>> albedo0snow(0.8)
        >>> snowagingfactor(0.35)
        >>> albedo.acker_jan = 0.2
        >>> albedo.vers_jan = 0.3
        >>> albedo.acker_feb = 0.4
        >>> albedo.vers_feb = 0.5
        >>> derived.moy.update()
        >>> states.taus = nan, nan, 0.0, 1.0, 3.0
        >>> states.waes = 0.0, 0.0, 1.0, 1.0, 1.0
        >>> model.idx_sim = 1
        >>> model.calc_actualalbedo_v1()
        >>> fluxes.actualalbedo
        actualalbedo(0.2, 0.3, 0.8, 0.66, 0.59)
        >>> model.idx_sim = 2
        >>> model.calc_actualalbedo_v1()
        >>> fluxes.actualalbedo
        actualalbedo(0.4, 0.5, 0.8, 0.66, 0.59)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.SnowAgingFactor,
        lland_control.Albedo0Snow,
        lland_control.Albedo,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (
        lland_states.TauS,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (lland_fluxes.ActualAlbedo,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.0:
                flu.actualalbedo[k] = con.albedo0snow * (
                    1.0 - con.snowagingfactor * sta.taus[k] / (1.0 + sta.taus[k])
                )
            else:
                flu.actualalbedo[k] = con.albedo[con.lnk[k] - 1, der.moy[model.idx_sim]]


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    """Calculate the net shortwave radiation.

    Basic equation:
      :math:`NetShortwaveRadiation =
      (1.0 - ActualAlbedo) \\cdot AdjustedGlobalRadiation`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> fluxes.actualalbedo = 0.25
        >>> fluxes.adjustedglobalradiation = 1.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(0.75)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_fluxes.ActualAlbedo,
        lland_fluxes.AdjustedGlobalRadiation,
    )
    RESULTSEQUENCES = (lland_fluxes.NetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.netshortwaveradiation[k] = (
                1.0 - flu.actualalbedo[k]
            ) * flu.adjustedglobalradiation


class Calc_NetShortwaveRadiationSnow_V1(modeltools.Method):
    """Calculate the net shortwave radiation for snow-surfaces.

    Basic equation:
      :math:`NetShortwaveRadiationSnow =
      Fr \\cdot (1.0 - ActualAlbedo) \\cdot AdjustedGlobalRadiation`

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)
        >>> derived.fr.acker_jan = 1.0
        >>> derived.fr.acker_feb = 1.0
        >>> derived.fr.laubw_jan = 0.5
        >>> derived.fr.laubw_feb = 0.1
        >>> derived.moy.update()
        >>> fluxes.actualalbedo = 0.5
        >>> fluxes.adjustedglobalradiation = 2.0

        >>> model.idx_sim = pub.timegrids.init['2000-01-31']
        >>> model.calc_netshortwaveradiationsnow_v1()
        >>> fluxes.netshortwaveradiationsnow
        netshortwaveradiationsnow(1.0, 0.5)

        >>> model.idx_sim = pub.timegrids.init['2000-02-01']
        >>> model.calc_netshortwaveradiationsnow_v1()
        >>> fluxes.netshortwaveradiationsnow
        netshortwaveradiationsnow(1.0, 0.1)
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
        lland_fluxes.ActualAlbedo,
        lland_fluxes.AdjustedGlobalRadiation,
    )
    RESULTSEQUENCES = (lland_fluxes.NetShortwaveRadiationSnow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.netshortwaveradiationsnow[k] = (
                der.fr[con.lnk[k] - 1, der.moy[model.idx_sim]]
                * (1.0 - flu.actualalbedo[k])
                * flu.adjustedglobalradiation
            )


class Calc_DailyNetShortwaveRadiation_V1(modeltools.Method):
    """Calculate the daily net shortwave radiation.

    Basic equation:
      :math:`DailyNetShortwaveRadiation =
      (1.0 - ActualAlbedo) \\cdot DailyGlobalRadiation`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep()
        >>> nhru(1)
        >>> fluxes.actualalbedo(0.25)
        >>> fluxes.dailyglobalradiation = 1.0
        >>> model.calc_dailynetshortwaveradiation_v1()
        >>> fluxes.dailynetshortwaveradiation
        dailynetshortwaveradiation(0.75)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_fluxes.DailyGlobalRadiation,
        lland_fluxes.ActualAlbedo,
    )
    RESULTSEQUENCES = (lland_fluxes.DailyNetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dailynetshortwaveradiation[k] = (
                1.0 - flu.actualalbedo[k]
            ) * flu.dailyglobalradiation


class Return_TempS_V1(modeltools.Method):
    """Calculate and return the average temperature of the snow layer
    :cite:`ref-LARSIM`.

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
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> states.wats = 0.0, 0.5, 5.0, 0.5, 0.5
        >>> states.waes = 0.0, 1.0, 10.0, 1.0, 1.0
        >>> states.esnow = 0.0, 0.0, -0.1, -0.8, -1.0
        >>> from hydpy import round_
        >>> round_(model.return_temps_v1(0))
        nan
        >>> round_(model.return_temps_v1(1))
        0.0
        >>> round_(model.return_temps_v1(2))
        -3.186337
        >>> round_(model.return_temps_v1(3))
        -254.906959
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


class Return_ESnow_V1(modeltools.Method):
    """Calculate and return the thermal energy content of the snow layer for
    the given bulk temperature :cite:`ref-LARSIM`.

    Basic equation:
      :math:`temps \\cdot (WATS \\cdot CPEis + (WAeS-WATS)\\cdot CPWasser)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> states.wats = 0.0, 0.5, 5.0
        >>> states.waes = 0.0, 1.0, 10.0
        >>> states.esnow = 0.0, 0.0, -0.1
        >>> from hydpy import round_
        >>> round_(model.return_esnow_v1(0, 1.0))
        0.0
        >>> round_(model.return_esnow_v1(1, 0.0))
        0.0
        >>> round_(model.return_esnow_v1(2, -3.186337))
        -0.1
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
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> pwmax(2.0)
        >>> fluxes.tkor = -1.0
        >>> states.wats = 0.0, 0.5, 5
        >>> states.waes = 0.0, 1.0, 10
        >>> states.esnow = 0.0, 0.0, -0.1
        >>> model.calc_temps_v1()
        >>> aides.temps
        temps(nan, 0.0, -3.186337)
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
    """Calculate the mean temperature in the top-layer of the soil
    :cite:`ref-LARSIM` (based on :cite:`ref-LUBW2006b`).

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
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(WASSER, FLUSS, SEE, WASSER, SEE, FLUSS, WASSER)
        >>> model.calc_tz_v1()
        >>> fluxes.tz
        tz(nan, nan, nan, nan, nan, nan, nan)

        For all other land use types, the above basic equation applies:

        >>> lnk(ACKER)
        >>> derived.heatoffusion(26.72)
        >>> states.ebdn(-10.0, -1.0, 0.0, 13.36, 26.72, 27.72, 36.72)
        >>> model.calc_tz_v1()
        >>> fluxes.tz
        tz(-33.333333, -3.333333, 0.0, 0.0, 0.0, 3.333333, 33.333333)
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


class Calc_G_V1(modeltools.Method):
    """Calculate and return the "MORECS" soil heat flux (modified
    :cite:`ref-LARSIM`, based on :cite:`ref-Thompson1981`).

    Basic equations:
      :math:`G = \\frac{PossibleSunshineDuration}
      {DailyPossibleSunshineDuration} \\cdot G_D
      + \\frac{(Hours - PossibleSunshineDuration)}
      {24-DailyPossibleSunshineDuration} \\cdot G_N`

      :math:`G_N = WG2Z - G_D`

      :math:`G_D = (0.3 - 0.03 \\cdot LAI) \\cdot DailyNetRadiation`

    The above equations are our interpretation on the relevant equations
    and explanations given in the LARSIM user manual.  :math:`G_D` is the
    daytime sum of the soil heat flux, which depends on the daily sum of
    net radiation and the leaf area index.  Curiously, |DailyNetRadiation|
    and :math:`G_D` become inversely related for leaf area index values
    larger than 10.  |WG2Z| defines the daily energy change of the soil
    layer, which is why we use its difference to :math:`G_D` for estimating
    the nighttime sum of the soil heat flux (:math:`G_N`).

    .. note::

       The sudden jumps of the soil heat flux calculated by method |Calc_G_V1|
       sometimes result in strange-looking evapotranspiration time-series.
       Hence, we do not use |Calc_G_V1| in any application model for now
       but leave it for further discussions and use the simplified method
       |Calc_G_V2| instead.

    Examples:

        To start as simple as possible, we perform the first test calculation
        for a daily simulation step size:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-05-30', '2000-06-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()

        We define five hydrological respose units, of which only the first
        four ones need further parameterisation, as method |Calc_G_V1|
        generally sets |G| to zero for all kinds of water areas:

        >>> nhru(6)
        >>> lnk(BODEN, OBSTB, OBSTB, LAUBW, NADELW, WASSER)

        We assign leaf area indices covering the usual range of values:

        >>> lai.boden = 0.0
        >>> lai.obstb = 5.0
        >>> lai.laubw = 10.0
        >>> lai.nadelw = 15.0

        We define a positive |WG2Z| value for May (on average, energy moves
        from the soil body to the soil surface) and a negative one for June
        (enery moves for the surface to the body):

        >>> wg2z.mai = 1.0
        >>> wg2z.jun = -2.0

        The following derived parameters need to be updated:

        >>> derived.moy.update()
        >>> derived.hours.update()

        For a daily simulation step size, the values of
        |PossibleSunshineDuration| (of the current simulation step) and
        |DailyPossibleSunshineDuration| must be identical:

        >>> fluxes.possiblesunshineduration = 14.0
        >>> fluxes.dailypossiblesunshineduration = 14.0

        We set |DailyNetRadiation| to 10 MJ/m² for most response units,
        except one of the |ACKER| ones:

        >>> fluxes.dailynetradiation = 10.0, 10.0, -10.0, 10.0, 10.0, 10.0

        For the given daily simulation step size, method |Calc_G_V1|
        calculates soil surface fluxes identical with the |WG2Z| value
        of the respective month:

        >>> model.idx_sim = pub.timegrids.init['2000-05-31']
        >>> model.calc_g_v1()
        >>> fluxes.g
        g(1.0, 1.0, 1.0, 1.0, 1.0, 0.0)
        >>> model.idx_sim = pub.timegrids.init['2000-06-01']
        >>> model.calc_g_v1()
        >>> fluxes.g
        g(-2.0, -2.0, -2.0, -2.0, -2.0, 0.0)

        Next, we switch to an hourly step size and focus on May:

        >>> pub.timegrids = '2000-05-30 00:00', '2000-06-02 00:00', '1h'
        >>> model.idx_sim = pub.timegrids.init['2000-05-31']
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> derived.days.update()

        During daytime (when the possible sunshine duration is one hour),
        the soil surface flux is negative for net radiation values larger
        one and for leaf area index values smaller than ten (see response
        units one and two).  Negative net radiation (response unit three)
        ar leaf area indices larger then ten (response unit five) result
        in positive soil surface fluxes:

        >>> fluxes.possiblesunshineduration = 1.0
        >>> model.calc_g_v1()
        >>> fluxes.g
        g(-0.214286, -0.107143, 0.107143, 0.0, 0.107143, 0.0)
        >>> day = fluxes.g.values.copy()

        The nighttime soils surface fluxes (which we calculate through
        setting |PossibleSunshineDuration| to zero) somehow compensate the
        daytime ones:

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_g_v1()
        >>> fluxes.g
        g(0.4, 0.25, -0.05, 0.1, -0.05, 0.0)
        >>> night = fluxes.g.values.copy()

        This compensation enforces that the daily sum the surface flux agrees
        with the actual value of |WG2Z|, which we confirm by the following
        test calculation:

        >>> from hydpy import print_values
        >>> print_values(day*fluxes.dailypossiblesunshineduration +
        ...              night*(24-fluxes.dailypossiblesunshineduration))
        1.0, 1.0, 1.0, 1.0, 1.0, 0.0
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.LAI,
        lland_control.WG2Z,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Hours,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.PossibleSunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
        lland_fluxes.DailyNetRadiation,
    )
    RESULTSEQUENCES = (lland_fluxes.G,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (FLUSS, SEE, WASSER):
                flu.g[k] = 0.0
            else:
                idx = der.moy[model.idx_sim]
                d_cr = 0.3 - 0.03 * con.lai[con.lnk[k] - 1, idx]
                d_gd = -d_cr * flu.dailynetradiation[k]
                d_gn = con.wg2z[idx] - d_gd
                d_gd_h = d_gd / flu.dailypossiblesunshineduration
                d_gn_h = d_gn / (24.0 - flu.dailypossiblesunshineduration)
                flu.g[k] = (
                    flu.possiblesunshineduration * d_gd_h
                    + (der.hours - flu.possiblesunshineduration) * d_gn_h
                )


class Calc_G_V2(modeltools.Method):
    """Take the actual daily soil heat flux from parameter |WG2Z|.

    Basic equations:
      :math:`G = WG2Z`

    .. note::

       Method |Calc_G_V2| workaround.  We might remove it, as soon as the
       shortcomings of method |Calc_G_V1| are fixed.

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-05-30 00:00', '2000-06-02 00:00', '1h'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, WASSER, FLUSS, SEE)
        >>> wg2z.mai = 1.2
        >>> wg2z.jun = -2.4
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> model.idx_sim = pub.timegrids.init['2000-05-31 23:00']
        >>> model.calc_g_v2()
        >>> fluxes.g
        g(0.05, 0.0, 0.0, 0.0)
        >>> model.idx_sim = pub.timegrids.init['2000-06-01 00:00']
        >>> model.calc_g_v2()
        >>> fluxes.g
        g(-0.1, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WG2Z,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Days,
    )
    RESULTSEQUENCES = (lland_fluxes.G,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (FLUSS, SEE, WASSER):
                flu.g[k] = 0.0
            else:
                flu.g[k] = der.days * con.wg2z[der.moy[model.idx_sim]]


class Return_WG_V1(modeltools.Method):
    """Calculate and return the "dynamic" soil heat flux :cite:`ref-LARSIM`.

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
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> fixed.lambdag.restore()
        >>> fluxes.tz = 2.0
        >>> fluxes.tkor = 10.0
        >>> states.waes = 0.0, 1.0
        >>> aides.temps = nan, -1.0
        >>> from hydpy import round_
        >>> round_(model.return_wg_v1(0))
        -0.1728
        >>> round_(model.return_wg_v1(1))
        0.0648
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
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(ACKER, VERS, WASSER, FLUSS, SEE)
        >>> fixed.lambdag.restore()
        >>> fluxes.tz = 2.0
        >>> fluxes.tkor = 10.0
        >>> states.waes = 0.0, 1.0, 0.0, 0.0, 0.0
        >>> aides.temps = nan, -1.0, nan, nan, nan
        >>> model.calc_wg_v1()
        >>> fluxes.wg
        wg(-0.1728, 0.0648, 0.0, 0.0, 0.0)
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
    """Update the thermal energy content of the upper soil layer
    :cite:`ref-LARSIM`.

    Basic equation:
      :math:`\\frac{dEBdn}{dt} = WG2Z \\cdot Days - WG`

    Example:

        Water areas do not posses a soil energy content. For all other
        landuse types, the above equation applies:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(WASSER, FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> pub.timegrids = '2019-04-29', '2019-05-03', '1d'
        >>> derived.moy.update()
        >>> derived.seconds.update()
        >>> derived.days.update()
        >>> wg2z.apr = -0.03
        >>> wg2z.mai = -0.04
        >>> states.ebdn = 0.0
        >>> fluxes.wg = 0.0, 0.0, 0.0, 0.5, 1.0, 2.0
        >>> model.idx_sim = 1
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(0.0, 0.0, 0.0, -0.53, -1.03, -2.03)
        >>> model.idx_sim = 2
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(0.0, 0.0, 0.0, -1.07, -2.07, -4.07)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WG2Z,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Days,
    )
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
                sta.ebdn[k] += con.wg2z[der.moy[model.idx_sim]] * der.days - flu.wg[k]


class Return_WSensSnow_V1(modeltools.Method):
    """Calculate and return the sensible heat flux of the snow surface
    :cite:`ref-LARSIM`.

    Basic equation:
      :math:`(Turb0 + Turb1 \\cdot WindSpeed2m) \\cdot (TempSSurface - TKor)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fluxes.tkor = -2.0, -1.0
        >>> fluxes.tempssurface = -5.0, 0.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> from hydpy import round_
        >>> round_(model.return_wsenssnow_v1(0))
        -0.0864
        >>> round_(model.return_wsenssnow_v1(1))
        0.0288
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


class Return_WLatSnow_V1(modeltools.Method):
    """Calculate and return the latent heat flux of the snow surface
    :cite:`ref-LARSIM`.

    Basic equation:
      :math:`(Turb0 + Turb1 \\cdot ReducedWindSpeed2m) \\cdot
      PsiInv \\cdot (SaturationVapourPressureSnow - ActualVapourPressure))`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.saturationvapourpressuresnow = 0.4, 0.8
        >>> fluxes.actualvapourpressure = .6108
        >>> from hydpy import round_
        >>> round_(model.return_wlatsnow_v1(0))
        -0.10685
        >>> round_(model.return_wlatsnow_v1(1))
        0.095902
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
    """Calculate and return the snow surface heat flux :cite:`ref-LARSIM`
    (based on :cite:`ref-LUBW2006b`).

    Basic equation:
      :math:`KTSchnee \\cdot (TempS - TempSSurface)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(1)
        >>> ktschnee(0.432)
        >>> fluxes.tempssurface = -3.0
        >>> aides.temps = -2.0
        >>> from hydpy import round_
        >>> round_(model.return_wsurf_v1(0))
        0.018

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
        >>> round_(model.return_netradiation_v1(3.0, 2.0))
        1.0
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        netshortwaveradiation: float,
        netlongwaveradiation: float,
    ) -> float:
        return netshortwaveradiation - netlongwaveradiation


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation.

    Basic equation:
      :math:`NetRadiation = Return\\_NetRadiation\\_V1(
      NetShortwaveRadiation, DailyNetLongwaveRadiation \\cdot Days)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> derived.days(0.5)
        >>> fluxes.netshortwaveradiation = 3.0
        >>> fluxes.dailynetlongwaveradiation = 2.0
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(2.0)
    """

    SUBMETHODS = (Return_NetRadiation_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    DERIVEDPARAMETERS = (lland_derived.Days,)
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiation,
        lland_fluxes.DailyNetLongwaveRadiation,
    )
    UPDATEDSEQUENCES = (lland_fluxes.NetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.netradiation[k] = model.return_netradiation_v1(
                flu.netshortwaveradiation[k],
                flu.dailynetlongwaveradiation[k] * der.days,
            )


class Calc_DailyNetRadiation_V1(modeltools.Method):
    """Calculate the daily total net radiation for snow-free land surfaces.

    Basic equation:
      :math:`NetRadiation = Return\\_NetRadiation\\_V1(
      DailyDailyNetShortwaveRadiation, DailyNetLongwaveRadiation)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> fluxes.dailynetshortwaveradiation = 3.0
        >>> fluxes.dailynetlongwaveradiation = 2.0
        >>> model.calc_dailynetradiation_v1()
        >>> fluxes.dailynetradiation
        dailynetradiation(1.0)
    """

    SUBMETHODS = (Return_NetRadiation_V1,)
    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_fluxes.DailyNetLongwaveRadiation,
        lland_fluxes.DailyNetShortwaveRadiation,
    )
    RESULTSEQUENCES = (lland_fluxes.DailyNetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dailynetradiation[k] = model.return_netradiation_v1(
                flu.dailynetshortwaveradiation[k],
                flu.dailynetlongwaveradiation[k],
            )


class Return_EnergyGainSnowSurface_V1(modeltools.Method):
    """Calculate and return the net energy gain of the snow surface
    (:cite:`ref-LARSIM` :cite:`ref-LUBW2006b`, modified).

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
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> ktschnee(0.432)
        >>> derived.days.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiationsnow = 2.0
        >>> derived.nmblogentries.update()
        >>> fluxes.dailysunshineduration = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0
        >>> aides.temps = -2.0

        Under the defined conditions and for a snow surface temperature of
        -4 °C, the net energy gain would be negative:

        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_energygainsnowsurface_v1(-4.0))
        -6.565618

        As a side-effect, method |Return_EnergyGainSnowSurface_V1| calculates
        the following flux sequences for the given snow surface temperature:

        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.453913)
        >>> fluxes.netlongwaveradiationsnow
        netlongwaveradiationsnow(8.126801)
        >>> fluxes.netradiationsnow
        netradiationsnow(-6.126801)
        >>> fluxes.wsenssnow
        wsenssnow(-0.6912)
        >>> fluxes.wlatsnow
        wlatsnow(1.994016)
        >>> fluxes.wsurf
        wsurf(0.864)

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
        lland_derived.Days,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.PsyInv,
        lland_fixed.Sigma,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
        lland_aides.TempS,
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
    """Determine and return the snow surface temperature
    (:cite:`ref-LARSIM` based on :cite:`ref-LUBW2006b`, modified).

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
        |Return_EnergyGainSnowSurface_V1|, except that we prepare five
        hydrological response units:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(ACKER)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> ktschnee(0.432)
        >>> derived.nmblogentries.update()
        >>> derived.days.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 0.0, 1.0, 1.0, 1.0, 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiationsnow = 1.0, 1.0, 2.0, 2.0, 2.0
        >>> fluxes.dailysunshineduration = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0
        >>> aides.temps = nan, -2.0, -2.0, -50.0, -200.0

        For the first, snow-free response unit, we cannot define a reasonable
        snow surface temperature, of course.  Comparing response units
        two and three shows that a moderate increase in short wave radiation
        is compensated by a moderate increase in snow surface temperature.
        To demonstrate the robustness of the implemented approach, response
        units three to five show the extreme decrease in surface temperature
        due to an even more extrem decrease in the bulk temperature of the
        snow layer:

        >>> for hru in range(5):
        ...     _ = model.return_tempssurface_v1(hru)
        >>> fluxes.tempssurface
        tempssurface(nan, -8.064938, -7.512933, -19.826442, -66.202324)

        As to be expected, the energy fluxes of the snow surface neutralise
        each other (within the defined numerical accuracy):

        >>> from hydpy import print_values
        >>> print_values(fluxes.netradiationsnow -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, 0.0, 0.0, 0.0, 0.0

        Through setting parameter |KTSchnee| to |numpy.inf|, we disable
        the iterative search for the correct surface temperature.  Instead,
        method |Return_TempSSurface_V1| simply uses the bulk temperature of
        the snow layer as its surface temperature and sets |WSurf| so that
        the energy gain of the snow surface is zero:

        >>> ktschnee(inf)
        >>> for hru in range(5):
        ...     _ = model.return_tempssurface_v1(hru)
        >>> fluxes.tempssurface
        tempssurface(nan, -2.0, -2.0, -50.0, -200.0)
        >>> fluxes.wsurf
        wsurf(0.0, 11.476385, 10.476385, -43.376447, -159.135575)
        >>> print_values(fluxes.netradiationsnow -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, 0.0, 0.0, 0.0, 0.0
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
        lland_derived.Days,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_states.WAeS,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
        lland_aides.TempS,
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
                model.pegasustempssurface.find_x(
                    -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10
                )
        else:
            flu.tempssurface[k] = modelutils.nan
            flu.saturationvapourpressuresnow[k] = 0.0
            flu.wsenssnow[k] = 0.0
            flu.wlatsnow[k] = 0.0
            flu.wsurf[k] = 0.0
        return flu.tempssurface[k]


class Return_BackwardEulerError_V1(modeltools.Method):
    """Calculate and return the "Backward Euler error" regarding the
    update of |ESnow| due to the energy fluxes |WG| and |WSurf|
    (:cite:`ref-LARSIM` based on :cite:`ref-LUBW2006b`, modified).

    Basic equation:
      :math:`ESnow_{old} - esnow_{new} + WG(esnow{new} ) - WSurf(esnow{new})`

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
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> derived.nmblogentries.update()
        >>> derived.days.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 12.0
        >>> states.wats = 10.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiationsnow = 2.0
        >>> states.esnow = -0.1
        >>> fluxes.dailysunshineduration = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0
        >>> fluxes.tz = 0.0

        Under the defined conditions the "correct" next value of |ESnow|,
        when following the Backward Euler approach, is approximately
        -0.195 MJ/m²:

        >>> ktschnee(inf)
        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_backwardeulererror_v1(-0.19536469903172524))
        0.0

        As a side-effect, method |Return_BackwardEulerError_V1| calculates
        the following flux sequences for the given amount of energy:

        >>> aides.temps
        temps(-6.67375)
        >>> fluxes.tempssurface
        tempssurface(-6.67375)
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.370062)
        >>> fluxes.netlongwaveradiationsnow
        netlongwaveradiationsnow(7.12037)
        >>> fluxes.netradiationsnow
        netradiationsnow(-5.12037)
        >>> fluxes.wsenssnow
        wsenssnow(-2.539296)
        >>> fluxes.wlatsnow
        wlatsnow(0.973963)
        >>> fluxes.wsurf
        wsurf(3.555037)
        >>> fluxes.wg
        wg(3.459672)

        Note that the original value of |ESnow| remains unchanged, to allow
        for calling method |Return_BackwardEulerError_V1| multiple times
        during a root search without the need for an external reset:

        >>> states.esnow
        esnow(-0.1)

        In the above example, |KTSchnee| is set to |numpy.inf|, which is
        why |TempSSurface| is identical with |TempS|.  After setting the
        common value of 0.432 MJ/m²/K/d, the surface temperature is
        calculated by another, embeded iteration approach (see method
        |Return_TempSSurface_V1|).  Hence, the values of |TempSSurface|
        and |TempS| differ and the energy amount of -0.195 MJ/m² is
        not correct anymore:

        >>> ktschnee(0.432)
        >>> round_(model.return_backwardeulererror_v1(-0.19536469903172524))
        2.70906
        >>> aides.temps
        temps(-6.67375)
        >>> fluxes.tempssurface
        tempssurface(-8.632029)
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.317671)
        >>> fluxes.netlongwaveradiationsnow
        netlongwaveradiationsnow(6.402218)
        >>> fluxes.netradiationsnow
        netradiationsnow(-4.402218)
        >>> fluxes.wsenssnow
        wsenssnow(-3.892859)
        >>> fluxes.wlatsnow
        wlatsnow(0.336617)
        >>> fluxes.wsurf
        wsurf(0.845976)
        >>> fluxes.wg
        wg(3.459672)
        >>> states.esnow
        esnow(-0.1)

        If there is no snow-cover, it makes little sense to call method
        |Return_BackwardEulerError_V1|.  For savety, we let it then
        return a |numpy.nan| value:

        >>> states.waes = 0.0
        >>> round_(model.return_backwardeulererror_v1(-0.10503956))
        nan
        >>> fluxes.wsurf
        wsurf(0.845976)
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
        lland_derived.Days,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
        lland_fixed.Z,
        lland_fixed.LambdaG,
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_states.WAeS,
        lland_states.WATS,
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.TZ,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
        lland_aides.TempS,
        lland_states.ESnow,
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


class Update_ESnow_V1(modeltools.Method):
    """Update the thermal energy content of the snow layer with regard to the
    energy fluxes from the soil and the atmosphere (except the one related
    to the heat content of precipitation). :cite:`ref-LARSIM` based on
    :cite:`ref-LUBW2006b`, modified.

    Basic equation:
      :math:`\\frac{dESnow}{dt} = WG - WSurf`

    For a thin snow cover, small absolute changes in its energy content
    result in extreme temperature changes, which makes the above calculation
    stiff.  Furthermore, the nonlinearity of the term :math:` WSurf(ESnow(t))`
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
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(8)
        >>> lnk(ACKER)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> ktschnee(inf)
        >>> derived.nmblogentries.update()
        >>> derived.days.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes = 0.0, 120.0, 12.0, 1.2, 0.12, 0.012, 1.2e-6, 1.2e-12
        >>> states.wats = 0.0, 100.0, 12.0, 1.0, 0.10, 0.010, 1.0e-6, 1.0e-12
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiationsnow = 2.0
        >>> states.esnow = -0.1
        >>> fluxes.dailysunshineduration = 10.0
        >>> fluxes.dailypossiblesunshineduration = 12.0
        >>> fluxes.tz = 0.0

        For the first, snow-free response unit, the energy content of the
        snow layer is zero.  For the other response units we see that the
        energy content decreases with decreasing snow thickness (This
        result is intuitively clear, but requires iteration in very different
        orders of magnitudes.  We hope, our implementation works always
        well.  Please tell us, if you encounter any cases where it does not):

        >>> model.update_esnow_v1()
        >>> states.esnow
        esnow(0.0, -1.723064, -0.167737, -0.019803, -0.001983, -0.000198, 0.0,
              0.0)
        >>> aides.temps
        temps(nan, -5.886068, -6.688079, -6.764855, -6.774109, -6.775036,
              -6.775139, -6.775139)
        >>> fluxes.tempssurface
        tempssurface(nan, -5.886068, -6.688079, -6.764855, -6.774109, -6.775036,
                     -6.775139, -6.775139)

        As to be expected, the requirement of the Backward Euler method
        is approximetely fullfilled for each response unit:

        >>> esnow = states.esnow.values.copy()
        >>> states.esnow = -0.1
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

        >>> ktschnee(0.432)
        >>> model.update_esnow_v1()
        >>> states.esnow
        esnow(0.0, -0.806055, -0.090244, -0.010808, -0.001084, -0.000108, 0.0,
              0.0)
        >>> aides.temps
        temps(nan, -2.753522, -3.59826, -3.692022, -3.7035, -3.704652, -3.70478,
              -3.70478)
        >>> fluxes.tempssurface
        tempssurface(nan, -7.692134, -7.893588, -7.915986, -7.918728, -7.919003,
                     -7.919034, -7.919034)

        The resulting energy amounts are, again, the "correct" ones:

        >>> esnow = states.esnow.values.copy()
        >>> states.esnow = -0.1
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
        lland_derived.Days,
        lland_derived.Fr,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
        lland_fixed.Z,
        lland_fixed.LambdaG,
        lland_fixed.Sigma,
        lland_fixed.PsyInv,
        lland_fixed.FrAtm,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiationSnow,
        lland_fluxes.TKor,
        lland_fluxes.ReducedWindSpeed2m,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DailySunshineDuration,
        lland_fluxes.DailyPossibleSunshineDuration,
        lland_fluxes.TZ,
        lland_states.WATS,
        lland_states.WAeS,
        lland_aides.TempS,
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
                    model.return_esnow_v1(k, 100.0),
                    -100.0,
                    100.0,
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
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> fluxes.wgtf = 2.0
        >>> fluxes.wnied = 1.0, 2.0
        >>> model.calc_schmpot_v1()
        >>> fluxes.schmpot
        schmpot(8.982036, 11.976048)
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
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.esnow = nan, 5.0, 2.0, -2.0
        >>> model.calc_schmpot_v2()
        >>> fluxes.schmpot
        schmpot(0.0, 14.97006, 5.988024, 0.0)
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
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.esnow = nan, -5.0, -2.0, 2.0
        >>> model.calc_gefrpot_v1()
        >>> fluxes.gefrpot
        gefrpot(0.0, 14.97006, 5.988024, 0.0)
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
        >>> parameterstep('1d')
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
        >>> parameterstep('1d')
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
        >>> parameterstep('1d')
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
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(WASSER, FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> fluxes.gefr = 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 4.0
        >>> fluxes.schm = 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 4.0
        >>> states.esnow = 1.0, 1.0, 1.0, 1.0, -1.5, 1.336, 0.0
        >>> states.waes = 1.0, 1.0, 1.0, 0.0, 5.0, 5.0, 10.0
        >>> model.update_esnow_v2()
        >>> states.esnow
        esnow(0.0, 0.0, 0.0, 0.0, -0.164, 0.0, 0.0)
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
    """Calculate the ratio between frozen water and total water within
    the top soil layer :cite:`ref-LARSIM`.

    Basic equations:
      :math:`SFF = min\\left(max\\left(
      1 - \\frac{EBdn}{BoWa2Z} \\cdot RSchmelz, 0\\right), 1\\right)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(9)
        >>> lnk(VERS, WASSER, FLUSS, SEE, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> states.ebdn(0.0, 0.0, 0.0, 0.0, 28.0, 27.0, 10.0, 0.0, -1.0)
        >>> model.calc_sff_v1()
        >>> fluxes.sff
        sff(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.625749, 1.0, 1.0)
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
                flu.sff[k] = min(
                    max(
                        1.0 - sta.ebdn[k] / (fix.bowa2z[k] * fix.rschmelz),
                        0.0,
                    ),
                    1.0,
                )


class Calc_FVG_V1(modeltools.Method):
    """Calculate the degree of frost sealing of the soil :cite:`ref-LARSIM`.

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


class Calc_EvB_V1(modeltools.Method):
    """Calculate the actual soil evapotranspiration.

    Basic equations:
      :math:`EvB = (EvPo - EvI) \\cdot
      \\frac{1 - temp}{1 + temp -2 \\cdot exp(-GrasRef_R)}`

      :math:`temp = exp\\left(-GrasRef_R \\cdot \\frac{BoWa}{WMax}\\right)`

    Examples:

        Soil evapotranspiration is calculated neither for water nor for
        sealed areas (see the first three hydrological reponse units of
        type |FLUSS|, |SEE|, and |VERS|).  All other land use classes are
        handled in accordance with a recommendation of the set of codes
        described in DVWK-M 504 :cite:`ref-DVWK`.  In case maximum soil water
        storage (|WMax|) is zero, soil evaporation (|EvB|) is generally set to
        zero (see the fourth hydrological response unit).  The last three
        response units demonstrate the rise in soil evaporation with increasing
        soil moisture, which is lessening in the high soil moisture range:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> grasref_r(5.0)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0)
        >>> fluxes.evpo = 5.0
        >>> fluxes.evi = 3.0
        >>> states.bowa = 50.0, 50.0, 50.0, 0.0, 0.0, 50.0, 100.0
        >>> model.calc_evb_v1()
        >>> fluxes.evb
        evb(0.0, 0.0, 0.0, 0.0, 0.0, 1.717962, 2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.GrasRef_R,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvPo,
        lland_fluxes.EvI,
    )
    RESULTSEQUENCES = (lland_fluxes.EvB,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE) or con.wmax[k] <= 0.0:
                flu.evb[k] = 0.0
            else:
                d_temp = modelutils.exp(-con.grasref_r * sta.bowa[k] / con.wmax[k])
                flu.evb[k] = (
                    (flu.evpo[k] - flu.evi[k])
                    * (1.0 - d_temp)
                    / (1.0 + d_temp - 2.0 * modelutils.exp(-con.grasref_r))
                )


class Calc_DryAirPressure_V1(modeltools.Method):
    """Calculate the pressure of the dry air (based on :cite:`ref-DWD1987`).

    Basic equation:
       :math:`DryAirPressure = AirPressure - ActualVapourPressure`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.actualvapourpressure = 0.9, 1.1, 2.5
        >>> inputs.atmosphericpressure = 120.0
        >>> model.calc_dryairpressure_v1()
        >>> fluxes.dryairpressure
        dryairpressure(119.1, 118.9, 117.5)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    REQUIREDSEQUENCES = (
        lland_fluxes.ActualVapourPressure,
        lland_inputs.AtmosphericPressure,
    )
    RESULTSEQUENCES = (lland_fluxes.DryAirPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dryairpressure[k] = (
                inp.atmosphericpressure - flu.actualvapourpressure[k]
            )


class Calc_DensityAir_V1(modeltools.Method):
    """Calculate the density of the air (based on :cite:`ref-DWD1987`).

    Basic equation:
       :math:`DensityAir = \\frac{DryAirPressure}{RDryAir \\cdot (TKor+273.15)}
       + \\frac{ActualVapourPressure}{RWaterVapour \\cdot (TKor+273.15)}`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.dryairpressure = 119.1, 100.0, 115.0
        >>> fluxes.actualvapourpressure = 0.8, 0.7, 1.0
        >>> fluxes.tkor = 10.0, 12.0, 14.0
        >>> model.calc_densityair_v1()
        >>> fluxes.densityair
        densityair(1.471419, 1.226998, 1.402691)
    """

    CONTROLPARAMETERS = (lland_control.NHRU,)
    FIXEDPARAMETERS = (
        lland_fixed.RDryAir,
        lland_fixed.RWaterVapour,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DryAirPressure,
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (lland_fluxes.DensityAir,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            d_t = flu.tkor[k] + 273.15
            flu.densityair[k] = flu.dryairpressure[k] / (
                fix.rdryair * d_t
            ) + flu.actualvapourpressure[k] / (fix.rwatervapour * d_t)


class Calc_AerodynamicResistance_V1(modeltools.Method):
    """Calculate the aerodynamic resistance :cite:`ref-LARSIM` (based on
    :cite:`ref-Thompson1981`).

    Basic equations (:math:`z_0` after Quast and Boehm, 1997):
      .. math::
        AerodynamicResistance = \\begin{cases}
        \\frac{6.25}{WindSpeed10m} \\cdot ln\\left(\\frac{10}{z_0}\\right)^2
        &|\\
        z_0 < 10
        \\\\
        \\frac{94}{WindSpeed10m}
        &|\\
        z_0 \\geq 10
        \\end{cases}

      :math:`z_0 = 0.021 + 0.163 \\cdot CropHeight`


    Examples:

        Besides wind speed, aerodynamic resistance depends on the crop height,
        which typically varies between different ref-use classes and, for
        vegetated surfaces, months.  In the first example, we set some
        different crop heights for different ref-use types to cover the
        relevant range of values:

        >>> from hydpy import pub
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(WASSER, ACKER, OBSTB, LAUBW, NADELW)
        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> derived.moy.update()
        >>> cropheight.wasser_jan = 0.0
        >>> cropheight.acker_jan = 1.0
        >>> cropheight.obstb_jan = 5.0
        >>> cropheight.laubw_jan = 10.0
        >>> cropheight.nadelw_jan = 15.0
        >>> fluxes.windspeed10m = 3.0
        >>> model.idx_sim = 1
        >>> model.calc_aerodynamicresistance_v1()
        >>> fluxes.aerodynamicresistance
        aerodynamicresistance(79.202731, 33.256788, 12.831028, 31.333333,
                              31.333333)

        The last example shows an decrease in resistance for increasing
        crop height for the first three hydrological response units only.
        When reaching a crop height of 10 m, the calculated resistance
        increases discontinously (see the fourth response unit) and then
        remains constant (see the fifth response unit).  In the next
        example, we set some unrealistic values, to inspect this
        behaviour more closely:

        >>> cropheight.wasser_feb = 8.0
        >>> cropheight.acker_feb = 9.0
        >>> cropheight.obstb_feb = 10.0
        >>> cropheight.laubw_feb = 11.0
        >>> cropheight.nadelw_feb = 12.0
        >>> model.idx_sim = 2
        >>> model.calc_aerodynamicresistance_v1()
        >>> fluxes.aerodynamicresistance
        aerodynamicresistance(8.510706, 7.561677, 31.333333, 31.333333,
                              31.333333)

        To get rid of this jump, one could use a threshold crop height
        of 1.14 m instead of 10 m for the selection of
        the two underlying equations:

        :math:`1.1404411695422059 =
        \\frac{\\frac{10}{\\exp(\\sqrt{94/6.25}}-0.021}{0.163}`

        The last example shows the inverse relationship between resistance
        and wind speed.  For zero wind speed, resistance becomes infinite:

        >>> from hydpy import print_values
        >>> cropheight(2.0)
        >>> for ws in (0.0, 0.1, 1.0, 10.0):
        ...     fluxes.windspeed10m = ws
        ...     model.calc_aerodynamicresistance_v1()
        ...     print_values([ws, fluxes.aerodynamicresistance[0]])
        0.0, inf
        0.1, 706.026613
        1.0, 70.602661
        10.0, 7.060266

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.CropHeight,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (lland_fluxes.WindSpeed10m,)
    RESULTSEQUENCES = (lland_fluxes.AerodynamicResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if flu.windspeed10m > 0.0:
            for k in range(con.nhru):
                d_ch = con.cropheight[con.lnk[k] - 1, der.moy[model.idx_sim]]
                if d_ch < 10.0:
                    d_z0 = 0.021 + 0.163 * d_ch
                    flu.aerodynamicresistance[k] = (
                        6.25 / flu.windspeed10m * modelutils.log(10.0 / d_z0) ** 2
                    )
                else:
                    flu.aerodynamicresistance[k] = 94.0 / flu.windspeed10m
        else:
            for k in range(con.nhru):
                flu.aerodynamicresistance[k] = modelutils.inf


class Calc_SoilSurfaceResistance_V1(modeltools.Method):
    """Calculate the surface resistance of the bare soil surface
    :cite:`ref-LARSIM` (based on :cite:`ref-Thompson1981`).

    Basic equation:
      .. math::
        SoilSurfaceResistance = \\begin{cases}
        100
        &|\\
        NFk > 20
        \\\\
        \\frac{100 \\cdot NFk}{max(BoWa-PWP, 0) + NFk/100}
        &|\\
        NFk \\geq 20
        \\end{cases}

    Examples:

        Water areas and sealed surfaces do not posses a soil, which is why
        we set the soil surface resistance to |numpy.nan|:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(VERS, WASSER, FLUSS, SEE)
        >>> fk(0.0)
        >>> pwp(0.0)
        >>> derived.nfk.update()
        >>> states.bowa = 0.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> fluxes.soilsurfaceresistance
        soilsurfaceresistance(nan, nan, nan, nan)

        For "typical" soils, which posses an available field capacity larger
        than 20 mm, we set the soil surface resistance to 100.0 s/m:

        >>> lnk(ACKER)
        >>> fk(20.1, 30.0, 40.0, 40.0)
        >>> pwp(0.0, 0.0, 10.0, 10.0)
        >>> derived.nfk.update()
        >>> states.bowa = 0.0, 20.0, 5.0, 30.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> fluxes.soilsurfaceresistance
        soilsurfaceresistance(100.0, 100.0, 100.0, 100.0)

        For all soils with smaller actual field capacities, resistance
        is 10'000 s/m as long as the soil water content does not exceed
        the permanent wilting point:

        >>> pwp(0.1, 20.0, 20.0, 30.0)
        >>> derived.nfk.update()
        >>> states.bowa = 0.0, 10.0, 20.0, 30.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> fluxes.soilsurfaceresistance
        soilsurfaceresistance(10000.0, 10000.0, 10000.0, 10000.0)

        With increasing soil water contents, resistance decreases and
        reaches a value of 99 s/m:

        >>> pwp(0.0)
        >>> fk(20.0)
        >>> derived.nfk.update()
        >>> states.bowa = 5.0, 10.0, 15.0, 20.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> fluxes.soilsurfaceresistance
        soilsurfaceresistance(384.615385, 196.078431, 131.578947, 99.009901)

        >>> fk(50.0)
        >>> pwp(40.0)
        >>> derived.nfk.update()
        >>> states.bowa = 42.5, 45.0, 47.5, 50.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> fluxes.soilsurfaceresistance
        soilsurfaceresistance(384.615385, 196.078431, 131.578947, 99.009901)

        For zero field capacity, we set the soil surface resistance to zero:

        >>> pwp(0.0)
        >>> fk(0.0)
        >>> derived.nfk.update()
        >>> states.bowa = 0.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> fluxes.soilsurfaceresistance
        soilsurfaceresistance(inf, inf, inf, inf)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWP,
    )
    DERIVEDPARAMETERS = (lland_derived.NFk,)
    REQUIREDSEQUENCES = (lland_states.BoWa,)
    RESULTSEQUENCES = (lland_fluxes.SoilSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, FLUSS, SEE, WASSER):
                flu.soilsurfaceresistance[k] = modelutils.nan
            elif der.nfk[k] > 20.0:
                flu.soilsurfaceresistance[k] = 100.0
            elif der.nfk[k] > 0.0:
                d_free = min(max(sta.bowa[k] - con.pwp[k], 0.0), der.nfk[k])
                flu.soilsurfaceresistance[k] = (
                    100.0 * der.nfk[k] / (d_free + 0.01 * der.nfk[k])
                )
            else:
                flu.soilsurfaceresistance[k] = modelutils.inf


class Calc_LanduseSurfaceResistance_V1(modeltools.Method):
    """Calculate the surface resistance of vegetation, water and sealed areas.
    :cite:`ref-LARSIM` (based on :cite:`ref-Thompson1981`)

    Basic equations:
       :math:`LanduseSurfaceResistance = SR^* \\cdot \\left(3.5 \\cdot
       \\left(1 - \\frac{min(BoWa, PY)}{PY}\\right) +
       exp\\left(\\frac{0.2 \\cdot PY}{max(BoWa, 0)}\\right)\\right)`

      .. math::
        SR^* = \\begin{cases}
        SurfaceResistance
        &|\\
        Lnk \\neq NADELW
        \\\\
        10\\,000
        &|\\
        Lnk = NADELW \\;\\; \\land \\;\\;
        (TKor \\leq -5 \\;\\; \\lor \\;\\; \\Delta \\geq 2)
        \\\\
        min\\left(\\frac{25 \\cdot SurfaceResistance}{(TKor + 5)
       \\cdot (1 - \\Delta/2)}, 10\\,000\\right)
        &|\\
        Lnk = NADELW \\;\\; \\land \\;\\;
        (-5 < TKor < 20 \\;\\; \\land \\;\\; \\Delta < 2)
        \\\\
        min\\left(\\frac{SurfaceResistance}{(1 - \\Delta/2)}, 10\\,000\\right)
        &|\\
        Lnk = NADELW \\;\\; \\land \\;\\;
        (20 \\leq TKor \\;\\; \\land \\;\\; \\Delta < 2)
        \\end{cases}

      :math:`\\Delta = SaturationVapourPressure - ActualVapourPressure`


    Example:

        Method |Calc_LanduseSurfaceResistance_V1| relies on multiple
        discontinuous relationships, works different for different
        types of ref-use, and uses montly varying base parameters.
        Hence, we try to start simple and introduce further complexities
        step by step.

        For sealed surfaces and water areas the original parameter values
        are in effect without any modification:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-05-30', '2000-06-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(VERS, FLUSS, SEE, WASSER)
        >>> surfaceresistance.fluss_mai = 0.0
        >>> surfaceresistance.see_mai = 0.0
        >>> surfaceresistance.wasser_mai = 0.0
        >>> surfaceresistance.vers_mai = 500.0
        >>> derived.moy.update()
        >>> model.idx_sim = 1
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(500.0, 0.0, 0.0, 0.0)

        For all "soil areas", we sligthly increase the original parameter
        value by a constant factor for wet soils (|BoWa| > |PY|) and
        increase it even more for dry soils (|BoWa| > |PY|).  For
        a completely dry soil, surface resistance becomes infinite:

        >>> lnk(ACKER)
        >>> py(0.0)
        >>> surfaceresistance.acker_jun = 40.0
        >>> states.bowa = 0.0, 10.0, 20.0, 30.0
        >>> model.idx_sim = 2
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(inf, 48.85611, 48.85611, 48.85611)

        >>> py(20.0)
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(inf, 129.672988, 48.85611, 48.85611)

        >>> states.bowa = 17.0, 18.0, 19.0, 20.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(71.611234, 63.953955, 56.373101, 48.85611)

        Only for coniferous trees, we further increase surface resistance
        for low temperatures and high water vapour pressure deficits.
        The highest resistance value results from air temperatures lower
        than -5 °C or vapour deficits higher than 2 kPa:

        >>> lnk(NADELW)
        >>> surfaceresistance.nadelw_jun = 80.0
        >>> states.bowa = 20.0
        >>> fluxes.tkor = 30.0
        >>> fluxes.saturationvapourpressure = 3.0
        >>> fluxes.actualvapourpressure = 0.0, 1.0, 2.0, 3.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 12214.027582, 195.424441,
                                 97.712221)

        >>> fluxes.actualvapourpressure = 1.0, 1.01, 1.1, 1.2
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 12214.027582, 1954.244413,
                                 977.122207)

        >>> fluxes.actualvapourpressure = 2.0
        >>> fluxes.tkor = -10.0, 5.0, 20.0, 35.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 488.561103, 195.424441,
                                 195.424441)

        >>> fluxes.tkor = -6.0, -5.0, -4.0, -3.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 12214.027582, 4885.611033,
                                 2442.805516)

        >>> fluxes.tkor = 18.0, 19.0, 20.0, 21.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(212.417871, 203.567126, 195.424441, 195.424441)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.SurfaceResistance,
        lland_control.PY,
    )
    DERIVEDPARAMETERS = (lland_derived.MOY,)
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (lland_fluxes.LanduseSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            d_res = con.surfaceresistance[con.lnk[k] - 1, der.moy[model.idx_sim]]
            if con.lnk[k] == NADELW:
                d_def = flu.saturationvapourpressure[k] - flu.actualvapourpressure[k]
                if (flu.tkor[k] <= -5.0) or (d_def >= 2.0):
                    flu.landusesurfaceresistance[k] = 10000.0
                elif flu.tkor[k] < 20.0:
                    flu.landusesurfaceresistance[k] = min(
                        (25.0 * d_res) / (flu.tkor[k] + 5.0) / (1.0 - 0.5 * d_def),
                        10000.0,
                    )
                else:
                    flu.landusesurfaceresistance[k] = min(
                        d_res / (1.0 - 0.5 * d_def), 10000.0
                    )
            else:
                flu.landusesurfaceresistance[k] = d_res
            if con.lnk[k] not in (WASSER, FLUSS, SEE, VERS):
                if sta.bowa[k] <= 0.0:
                    flu.landusesurfaceresistance[k] = modelutils.inf
                elif sta.bowa[k] < con.py[k]:
                    flu.landusesurfaceresistance[k] *= 3.5 * (
                        1.0 - sta.bowa[k] / con.py[k]
                    ) + modelutils.exp(0.2 * con.py[k] / sta.bowa[k])
                else:
                    flu.landusesurfaceresistance[k] *= modelutils.exp(0.2)


class Calc_ActualSurfaceResistance_V1(modeltools.Method):
    """Calculate the total surface resistance. :cite:`ref-LARSIM`
    (based on :cite:`ref-Grant1975`)

    Basic equations:
      :math:`ActualSurfaceResistance =
      \\left(w \\cdot \\frac{1}{SRD} +
      (1-w) \\cdot \\frac{1}{SRN}\\right)^{-1}`

      :math:`SRD =
      \\left(\\frac{1-0.7^{LAI}}{LanduseSurfaceResistance} +
      \\frac{0.7^{LAI}}{SoilSurfaceResistance}\\right)^{-1}`

      :math:`SRN =
      \\left(\\frac{LAI}{2500} + \\frac{1}{SoilSurfaceResistance}\\right)^{-1}`

      :math:`w = \\frac{PossibleSunshineDuration}{Hours}`


    Examples:

        For sealed surfaces and water areas, method
        |Calc_ActualSurfaceResistance_V1| just uses the values of sequence
        |LanduseSurfaceResistance| as the effective surface resistance values:

        >>> from hydpy import pub
        >>> pub.timegrids = '2019-05-30', '2019-06-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(VERS, FLUSS, SEE, WASSER)
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> fluxes.soilsurfaceresistance = nan
        >>> fluxes.landusesurfaceresistance = 500.0, 0.0, 0.0, 0.0
        >>> model.idx_sim = 1
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(500.0, 0.0, 0.0, 0.0)

        For all other landuse types, the final soil resistance is a
        combination of |LanduseSurfaceResistance| and |SoilSurfaceResistance|
        that depends on the leaf area index.  We demonstrate this for the
        landuse types |ACKER|, |OBSTB|, |LAUBW|, and |NADELW|, for which we
        define different leaf area indices:

        >>> lnk(ACKER, OBSTB, LAUBW, NADELW)
        >>> lai.acker_mai = 0.0
        >>> lai.obstb_mai = 2.0
        >>> lai.laubw_mai = 5.0
        >>> lai.nadelw_mai = 10.0

        The soil and landuse surface resistance are identical for all
        four hydrological response units:

        >>> fluxes.soilsurfaceresistance = 200.0
        >>> fluxes.landusesurfaceresistance = 100.0

        When we assume that the sun shines the whole day, the final
        resistance is identical with the soil surface resistance for
        zero leaf area indices (see the first response unit) and
        becomes closer to landuse surface resistance for when the
        leaf area index increases:

        >>> fluxes.possiblesunshineduration = 24.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(200.0, 132.450331, 109.174477, 101.43261)

        For a polar night, there is a leaf area index-dependend interpolation
        between soil surface resistance and a fixed resistance value:

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(200.0, 172.413793, 142.857143, 111.111111)

        For all days that are not polar nights or polar days, the values
        of the two examples above are weighted based on the possible
        sunshine duration of that day:

        >>> fluxes.possiblesunshineduration = 12.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(200.0, 149.812734, 123.765057, 106.051498)

        The following examples demonstrate that method
        |Calc_ActualSurfaceResistance_V1| works similar when applied on an
        hourly time basis during the daytime period (first example),
        during the nighttime (second example), and during dawn or
        dusk (third example):

        >>> pub.timegrids = '2019-05-31 22:00', '2019-06-01 03:00', '1h'
        >>> nhru(1)
        >>> lnk(NADELW)
        >>> fluxes.soilsurfaceresistance = 200.0
        >>> fluxes.landusesurfaceresistance = 100.0
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> lai.nadelw_jun = 5.0
        >>> model.idx_sim = 2
        >>> fluxes.possiblesunshineduration = 1.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(109.174477)

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(142.857143)

        >>> fluxes.possiblesunshineduration = 0.5
        >>> model.calc_actualsurfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(123.765057)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.LAI,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Hours,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SoilSurfaceResistance,
        lland_fluxes.LanduseSurfaceResistance,
        lland_fluxes.PossibleSunshineDuration,
    )

    RESULTSEQUENCES = (lland_fluxes.ActualSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, FLUSS, SEE, WASSER):
                flu.actualsurfaceresistance[k] = flu.landusesurfaceresistance[k]
            else:
                d_lai = con.lai[con.lnk[k] - 1, der.moy[model.idx_sim]]
                d_invrestday = (
                    (1.0 - 0.7 ** d_lai) / flu.landusesurfaceresistance[k]
                ) + 0.7 ** d_lai / flu.soilsurfaceresistance[k]
                d_invrestnight = d_lai / 2500.0 + 1.0 / flu.soilsurfaceresistance[k]
                flu.actualsurfaceresistance[k] = 1.0 / (
                    (
                        flu.possiblesunshineduration / der.hours * d_invrestday
                        + (1.0 - flu.possiblesunshineduration / der.hours)
                        * d_invrestnight
                    )
                )


class Return_Penman_V1(modeltools.Method):
    """Calculate and return the evaporation from water surfaces according to
    Penman :cite:`ref-LARSIM` (based on :cite:`ref-DVWK1996`).

    Basic equation:
      :math:`Days \\cdot \\frac{DailySaturationVapourPressureSlope \\cdot
      \\frac{DailyNetRadiation}{LW} +
      Psy \\cdot (1.3 + 0.94 \\cdot DailyWindSpeed2m) \\cdot
      (DailySaturationVapourPressure-DailyActualVapourPressure)}
      {DailySaturationVapourPressureSlope + Psy}`

    Examples:

        We initialise seven hydrological response units.  In reponse units
        one to three, evaporation is due to radiative forcing only.  In
        response units four to six, evaporation is due to aerodynamic forcing
        only.  Response unit seven shows the combined effect of both forces:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> nhru(7)
        >>> derived.days.update()
        >>> fluxes.dailynetradiation = 0.0, 3.5, 7.0, 0.0, 0.0, 0.0, 7.0
        >>> fluxes.dailywindspeed2m = 2.0
        >>> fluxes.dailysaturationvapourpressure = 1.2
        >>> fluxes.dailysaturationvapourpressureslope = 0.08
        >>> fluxes.dailyactualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0
        >>> from hydpy import print_values
        >>> for hru in range(7):
        ...     deficit = (fluxes.dailysaturationvapourpressure[hru] -
        ...                fluxes.dailyactualvapourpressure[hru])
        ...     print_values([fluxes.dailynetradiation[hru],
        ...                   deficit,
        ...                   model.return_penman_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.781513
        7.0, 0.0, 1.563027
        0.0, 0.0, 0.0
        0.0, 0.6, 0.858928
        0.0, 1.2, 1.717856
        7.0, 1.2, 3.280882

        The above results apply for a daily simulation time step.  The
        following example demonstrates that  we get equivalent results
        for hourly time steps:

        >>> simulationstep('1h')
        >>> derived.days.update()
        >>> for hru in range(7):
        ...     deficit = (fluxes.dailysaturationvapourpressure[hru] -
        ...                fluxes.dailyactualvapourpressure[hru])
        ...     print_values([fluxes.dailynetradiation[hru],
        ...                   deficit,
        ...                   24*model.return_penman_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.781513
        7.0, 0.0, 1.563027
        0.0, 0.0, 0.0
        0.0, 0.6, 0.858928
        0.0, 1.2, 1.717856
        7.0, 1.2, 3.280882
    """

    DERIVEDPARAMETERS = (lland_derived.Days,)
    FIXEDPARAMETERS = (
        lland_fixed.LW,
        lland_fixed.Psy,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.DailySaturationVapourPressureSlope,
        lland_fluxes.DailyNetRadiation,
        lland_fluxes.DailyWindSpeed2m,
        lland_fluxes.DailySaturationVapourPressure,
        lland_fluxes.DailyActualVapourPressure,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
    ) -> float:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return (
            der.days
            * (
                flu.dailysaturationvapourpressureslope[k]
                * flu.dailynetradiation[k]
                / fix.lw
                + fix.psy
                * (1.3 + 0.94 * flu.dailywindspeed2m)
                * (
                    flu.dailysaturationvapourpressure[k]
                    - flu.dailyactualvapourpressure[k]
                )
            )
            / (flu.dailysaturationvapourpressureslope[k] + fix.psy)
        )


class Return_PenmanMonteith_V1(modeltools.Method):
    """Calculate and return the evapotranspiration according to Penman-Monteith.
    :cite:`ref-LARSIM` (based on :cite:`ref-Thompson1981`)

    Basic equations:
      :math:`\\frac{SaturationVapourPressureSlope \\cdot (NetRadiation + G) +
      Seconds \\cdot C \\cdot DensitiyAir \\cdot CPLuft \\cdot
      \\frac{SaturationVapourPressure - ActualVapourPressure}
      {AerodynamicResistance^*}}
      {LW \\cdot (SaturationVapourPressureSlope + Psy \\cdot
      C \\cdot (1 + \\frac{actualsurfaceresistance}{AerodynamicResistance^*}))}`

      :math:`C = 1 +
      \\frac{b' \\cdot AerodynamicResistance^*}{DensitiyAir \\cdot CPLuft}`

      :math:`b' = 4 \\cdot Emissivity \\cdot
      \\frac{Sigma}{60 \\cdot 60 \\cdot 24} \\cdot (273.15 + TKor)^3`

      :math:`AerodynamicResistance^* =
      min\\Bigl(max\\bigl(AerodynamicResistance, 10^{-6}\\bigl), 10^6\\Bigl)`

    Correction factor `C` takes the difference between measured temperature
    and actual surface temperature into account.

    Example:

        We build the following example on the first example of the
        documentation on method |Return_Penman_V1|.  The total available
        energy (|NetRadiation| plus |G|) and the vapour saturation pressure
        deficit (|SaturationVapourPressure| minus |ActualVapourPressure|
        are identical.  To make the results roughly comparable, we use
        resistances suitable for water surfaces through setting
        |ActualSurfaceResistance| to zero and |AerodynamicResistance| to
        a reasonable precalculated value of 106 s/m:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> nhru(7)
        >>> emissivity(0.96)
        >>> derived.seconds.update()
        >>> fluxes.netradiation = 1.0, 4.5, 8.0, 1.0, 1.0, 1.0, 8.0
        >>> fluxes.g = -1.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0
        >>> fluxes.densityair = 1.24
        >>> fluxes.actualsurfaceresistance = 0.0
        >>> fluxes.aerodynamicresistance = 106.0
        >>> fluxes.tkor = 10.0

        For the first three hydrological response units with energy forcing
        only, there is a relatively small deviation to the results of method
        |Return_Penman_v1| due to the correction factor `C`, which is only
        implemented by method |Return_PenmanMonteith_v1|.  For response
        units four to six with dynamic forcing only, the results of method
        |Return_PenmanMonteith_v1| are more than twice as large as those
        of method |Return_Penman_v1|:

        >>> from hydpy import print_values
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([fluxes.netradiation[hru]+fluxes.g[hru],
        ...                   deficit,
        ...                   model.return_penmanmonteith_v1(
        ...                       hru, fluxes.actualsurfaceresistance[hru])])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.657142
        7.0, 0.0, 1.314284
        0.0, 0.0, 0.0
        0.0, 0.6, 2.031724
        0.0, 1.2, 4.063447
        7.0, 1.2, 5.377732

        Next, we repeat the above calculations using resistances relevant
        for vegetated surfaces (note that this also changes the results
        of the first three response units due to correction factor `C`
        depending on |AerodynamicResistance|):

        >>> fluxes.actualsurfaceresistance = 80.0
        >>> fluxes.aerodynamicresistance = 40.0
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([fluxes.netradiation[hru]+fluxes.g[hru],
        ...                   deficit,
        ...                   model.return_penmanmonteith_v1(
        ...                       hru, fluxes.actualsurfaceresistance[hru])])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.36958
        7.0, 0.0, 0.739159
        0.0, 0.0, 0.0
        0.0, 0.6, 2.469986
        0.0, 1.2, 4.939972
        7.0, 1.2, 5.679131

        The above results are sensitive to the relation of
        |ActualSurfaceResistance| and |AerodynamicResistance|.  The
        following example demonstrates this sensitivity through varying
        |ActualSurfaceResistance| over a wide range:

        >>> fluxes.netradiation = 8.0
        >>> fluxes.actualvapourpressure = 0.0
        >>> fluxes.actualsurfaceresistance = (
        ...     0.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0)
        >>> for hru in range(7):
        ...     print_values([fluxes.actualsurfaceresistance[hru],
        ...                   model.return_penmanmonteith_v1(
        ...                       hru, fluxes.actualsurfaceresistance[hru])])
        0.0, 11.208588
        20.0, 9.014385
        50.0, 6.968226
        100.0, 5.055617
        200.0, 3.263897
        500.0, 1.581954
        1000.0, 0.851033

        One potential pitfall of the given Penman-Monteith equation is that
        |AerodynamicResistance| becomes infinite for zero windspeed.  We
        protect method |Return_PenmanMonteith_V1| against this problem
        (and the less likely problem of zero aerodynamic resistance) by
        limiting the value of |AerodynamicResistance| to the interval
        :math:`[10^{-6}, 10^6]`:

        >>> fluxes.actualvapourpressure = 0.6
        >>> fluxes.actualsurfaceresistance = 80.0
        >>> fluxes.aerodynamicresistance = (
        ...     0.0, 1e-6, 1e-3, 1.0, 1e3, 1e6, inf)
        >>> for hru in range(7):
        ...     print_values([fluxes.aerodynamicresistance[hru],
        ...                   model.return_penmanmonteith_v1(
        ...                       hru, fluxes.actualsurfaceresistance[hru])])
        0.0, 5.00683
        0.000001, 5.00683
        0.001, 5.006734
        1.0, 4.91391
        1000.0, 0.829364
        1000000.0, 0.001275
        inf, 0.001275

        Now we change the simulation time step from one day to one hour
        to demonstrate that we can reproduce the results of the first
        example, which requires to adjust |NetRadiation| and |WG|:

        >>> simulationstep('1h')
        >>> derived.seconds.update()
        >>> fluxes.netradiation = 1.0, 4.5, 8.0, 1.0, 1.0, 1.0, 8.0
        >>> fluxes.netradiation /= 24
        >>> fluxes.g = -1.0/24
        >>> fluxes.actualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0
        >>> fluxes.actualsurfaceresistance = 0.0
        >>> fluxes.aerodynamicresistance = 106.0
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([24*(fluxes.netradiation[hru]+fluxes.g[hru]),
        ...                   deficit,
        ...                   24*model.return_penmanmonteith_v1(
        ...                       hru, fluxes.actualsurfaceresistance[hru])])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.657142
        7.0, 0.0, 1.314284
        0.0, 0.0, 0.0
        0.0, 0.6, 2.031724
        0.0, 1.2, 4.063447
        7.0, 1.2, 5.377732
    """

    CONTROLPARAMETERS = (lland_control.Emissivity,)
    DERIVEDPARAMETERS = (lland_derived.Seconds,)
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.LW,
        lland_fixed.CPLuft,
        lland_fixed.Psy,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.G,
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DensityAir,
        lland_fluxes.AerodynamicResistance,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model,
        k: int,
        actualsurfaceresistance: float,
    ) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_ar = min(max(flu.aerodynamicresistance[k], 1e-6), 1e6)
        d_b = (
            4.0
            * con.emissivity
            * fix.sigma
            / 60.0
            / 60.0
            / 24.0
            * (273.15 + flu.tkor[k]) ** 3
        )
        d_c = 1.0 + d_b * d_ar / flu.densityair[k] / fix.cpluft
        return (
            (
                flu.saturationvapourpressureslope[k] * (flu.netradiation[k] + flu.g[k])
                + der.seconds
                * d_c
                * flu.densityair[k]
                * fix.cpluft
                * (flu.saturationvapourpressure[k] - flu.actualvapourpressure[k])
                / d_ar
            )
            / (
                flu.saturationvapourpressureslope[k]
                + fix.psy * d_c * (1.0 + actualsurfaceresistance / d_ar)
            )
            / fix.lw
        )


class Calc_EvPo_V2(modeltools.Method):
    """Calculate the potential evaporation according to Penman or
    Penman-Monteith.

    Method |Calc_EvPo_V2| applies method |Return_Penman_V1| on all water
    areas and method |Return_PenmanMonteith_V1| on all other hydrological
    response units.  For Penman-Monteith, we yield potential values by passing
    zero surface resistance values to method |Return_PenmanMonteith_V1|.

    Example:

        We recalculate the results for the seventh hydrological response
        unit of the first example of the documention on the methods
        |Return_Penman_V1| and |Return_PenmanMonteith_V1|.  The calculated
        potential values differ markedly:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(WASSER, ACKER)
        >>> emissivity(0.96)
        >>> derived.nmblogentries.update()
        >>> derived.seconds.update()
        >>> derived.days.update()
        >>> fluxes.netradiation = 8.0
        >>> fluxes.dailynetradiation = 7.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.dailysaturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.dailysaturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 0.0
        >>> fluxes.dailyactualvapourpressure = 0.0
        >>> fluxes.windspeed2m = 2.0
        >>> fluxes.dailywindspeed2m = 2.0
        >>> fluxes.tkor = 10.0
        >>> fluxes.g = -1.0
        >>> fluxes.densityair = 1.24
        >>> fluxes.aerodynamicresistance = 106.0
        >>> model.calc_evpo_v2()
        >>> fluxes.evpo
        evpo(3.280882, 5.377732)
    """

    SUBMETHODS = (
        Return_Penman_V1,
        Return_PenmanMonteith_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Emissivity,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Days,
        lland_derived.Seconds,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.LW,
        lland_fixed.CPLuft,
        lland_fixed.Psy,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.G,
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DensityAir,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.DailySaturationVapourPressureSlope,
        lland_fluxes.DailyNetRadiation,
        lland_fluxes.DailyWindSpeed2m,
        lland_fluxes.DailySaturationVapourPressure,
        lland_fluxes.DailyActualVapourPressure,
    )
    RESULTSEQUENCES = (lland_fluxes.EvPo,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, SEE, FLUSS):
                flu.evpo[k] = model.return_penman_v1(k)
            else:
                flu.evpo[k] = model.return_penmanmonteith_v1(k, 0.0)


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
        >>> parameterstep('1d')
        >>> nhru(8)
        >>> lnk(ACKER, ACKER, ACKER, ACKER, ACKER, ACKER, ACKER, WASSER)
        >>> fluxes.wlatsnow = -1.0, 0.0, 2.0, 4.0, 6.0, 6.0, 6.0, 6.0
        >>> states.waes = 2.0, 2.0, 2.0, 2.0, 2.0, 1.5, 0.0, 2.0
        >>> states.wats = 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 1.0
        >>> model.calc_evs_waes_wats_v1()
        >>> fluxes.evs
        evs(-0.37489, 0.0, 0.74978, 1.49956, 2.0, 1.5, 0.0, 0.0)
        >>> states.waes
        waes(2.37489, 2.0, 1.25022, 0.50044, 0.0, 0.0, 0.0, 0.0)
        >>> states.wats
        wats(1.187445, 1.0, 0.62511, 0.25022, 0.0, 0.0, 0.0, 0.0)
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


class Calc_EvI_Inzp_V1(modeltools.Method):
    """Calculate interception evaporation and update the interception
    storage accordingly.

    Basic equation:
      :math:`\\frac{dInzp}{dt} = -EvI`

      .. math::
        EvI = \\begin{cases}
        EvPo
        &|\\
        Inzp > 0
        \\\\
        0
        &|\\
        Inzp = 0
        \\end{cases}

    Examples:

        For all "land response units" like arable land (|ACKER|), interception
        evaporation (|EvI|) is identical with potential evapotranspiration
        (|EvPo|) as long as it is met by available intercepted water (|Inzp|):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> states.inzp = 0.0, 2.0, 4.0
        >>> fluxes.evpo = 3.0
        >>> model.calc_evi_inzp_v1()
        >>> states.inzp
        inzp(0.0, 0.0, 1.0)
        >>> fluxes.evi
        evi(0.0, 2.0, 3.0)

        For water areas (|WASSER|, |FLUSS| and |SEE|), |EvI| is generally
        equal to |EvPo| (but this might be corrected by a method called
        after |Calc_EvI_Inzp_V1| has been applied) and |Inzp| is set to zero:

        >>> lnk(WASSER, FLUSS, SEE)
        >>> states.inzp = 2.0
        >>> fluxes.evpo = 3.0
        >>> model.calc_evi_inzp_v1()
        >>> states.inzp
        inzp(0.0, 0.0, 0.0)
        >>> fluxes.evi
        evi(3.0, 3.0, 3.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (lland_fluxes.EvPo,)
    UPDATEDSEQUENCES = (lland_states.Inzp,)
    RESULTSEQUENCES = (lland_fluxes.EvI,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.evi[k] = flu.evpo[k]
                sta.inzp[k] = 0.0
            else:
                flu.evi[k] = min(flu.evpo[k], sta.inzp[k])
                sta.inzp[k] -= flu.evi[k]


class Calc_EvB_V2(modeltools.Method):
    """Calculate the actual evapotranspiration from the soil.

    Basic equation:
      :math:`EvB = \\frac{EvPo - EvI}{EvPo} \\cdot
      Return\\_PenmanMonteith\\_V1(ActualSurfaceResistance)`

    Example:

        For sealed surfaces, water areas and snow-covered hydrological
        response units, there is no soil evapotranspiration:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(VERS, WASSER, FLUSS, SEE, NADELW, NADELW)
        >>> states.waes = 0.0, 0.0, 0.0, 0.0, 0.1, 10.0
        >>> model.calc_evb_v2()
        >>> fluxes.evb
        evb(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        For all other cases, method |Calc_EvB_V2| first applies method
        |Return_PenmanMonteith_V1| (of which's documentation we take
        most of the following test configuration) and adjusts the returned
        soil evapotranspiration to the (prioritised) interception evaporation
        in accordance with the base equation defined above:

        >>> lnk(NADELW)
        >>> states.waes = 0.0
        >>> emissivity(0.96)
        >>> derived.seconds.update()
        >>> fluxes.netradiation = 8.0, 8.0, 8.0, 8.0, 8.0, -30.0
        >>> fluxes.g = -1.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 0.0
        >>> fluxes.densityair = 1.24
        >>> fluxes.actualsurfaceresistance = 0.0
        >>> fluxes.aerodynamicresistance = 106.0
        >>> fluxes.tkor = 10.0
        >>> fluxes.evpo = 0.0, 6.0, 6.0, 6.0, 6.0, -6.0
        >>> fluxes.evi = 0.0, 0.0, 2.0, 4.0, 6.0, -3.0
        >>> model.calc_evb_v2()
        >>> fluxes.evb
        evb(0.0, 5.377732, 3.585154, 1.792577, 0.0, -0.878478)
    """

    SUBMETHODS = (Return_PenmanMonteith_V1,)
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Emissivity,
    )
    DERIVEDPARAMETERS = (lland_derived.Seconds,)
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.LW,
        lland_fixed.CPLuft,
        lland_fixed.Psy,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.G,
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DensityAir,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.ActualSurfaceResistance,
        lland_fluxes.EvPo,
        lland_fluxes.EvI,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (lland_fluxes.EvB,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if (
                (con.lnk[k] in (VERS, WASSER, FLUSS, SEE))
                or (sta.waes[k] > 0.0)
                or (flu.evpo[k] == 0.0)
            ):
                flu.evb[k] = 0.0
            else:
                flu.evb[k] = (
                    (flu.evpo[k] - flu.evi[k])
                    / flu.evpo[k]
                    * model.return_penmanmonteith_v1(
                        k,
                        flu.actualsurfaceresistance[k],
                    )
                )


class Calc_QKap_V1(modeltools.Method):
    """ "Calculate the capillary rise.

    Basic equation:
      :math:`QKap = KapMax \\cdot min\\left(max\\left(1 -
      \\frac{BoWa-KapGrenz_1}{KapGrenz_2-KapGrenz_1}, 0 \\right), 1 \\right)`

    Examples:

        We prepare six hydrological response units of landuse type |ACKER|
        with different soil water contents:

        >>> from hydpy.models.lland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
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
        (BoWa \\leq NFk \\;\\; \\land \\;\\; RBeta)
        \\\\
        Beta_{eff}  \\cdot (BoWa - PWP)
        &|\\
        BoWa > NFk \\;\\; \\lor \\;\\;
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
        >>> simulationstep('12h')
        >>> parameterstep('1d')
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
        array([ 0.02,  0.02,  0.02,  0.02,  0.02,  0.02,  0.02,  0.02])

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
        >>> simulationstep('12h')
        >>> parameterstep('1d')
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
        array([ 2.,  2.,  2.,  2.,  2.,  2.,  2.,  2.])

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
        >>> simulationstep('12h')
        >>> parameterstep('1d')
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
        array([ 5.,  5.,  5.,  5.,  5.,  5.,  5.,  5.])

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


class Calc_BoWa_V1(modeltools.Method):
    """Update the soil moisture and, if necessary, correct the ingoing and
    outgoing fluxes.

    Basic equations:
       :math:`\\frac{dBoWa}{dt} = WaDa + Qkap - EvB - QBB - QIB1 - QIB2 - QDB`

       :math:`0 \\leq BoWa \\leq WMax`

    Examples:

        For water areas and sealed surfaces, we simply set soil moisture |BoWa|
        to zero and do not need to perform any flux corrections:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> lnk(FLUSS, SEE, WASSER, VERS)
        >>> states.bowa = 100.0
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 0.0, 0.0)

        We make no principal distinction between the remaining land use
        classes and select arable land (|ACKER|) for the following examples.

        To prevent soil water contents increasing |WMax|, we might need to
        decrease |WaDa| and |QKap|:

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
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(95.0, 100.0, 100.0, 100.0)
        >>> fluxes.wada
        wada(0.0, 5.0, 2.5, 6.0)
        >>> fluxes.qkap
        qkap(10.0, 10.0, 2.5, 4.0)
        >>> fluxes.evb
        evb(5.0, 5.0, 5.0, 5.0)

        Additionally, to prevent storage overlflows we might need to
        decrease |EvB| in case it is negative (meaning, condensation
        increases the soil water storage):

        >>> states.bowa = 90.0
        >>> fluxes.wada = 0.0, 5.0, 10.0, 15.0
        >>> fluxes.qkap = 2.5
        >>> fluxes.evb = -2.5
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(95.0, 100.0, 100.0, 100.0)
        >>> fluxes.wada
        wada(0.0, 5.0, 3.333333, 7.5)
        >>> fluxes.qkap
        qkap(2.5, 2.5, 0.833333, 1.25)
        >>> fluxes.evb
        evb(-2.5, -2.5, -0.833333, -1.25)

        To prevent negative |BoWa| value, we might need to decrease |QBB|,
        |QIB1|, |QIB1|, |QBB|, and |EvB|:

        >>> states.bowa = 10.0
        >>> fluxes.wada = 0.0
        >>> fluxes.qkap = 0.0
        >>> fluxes.evb = 0.0, 5.0, 10.0, 15.0
        >>> fluxes.qbb = 1.25
        >>> fluxes.qib1 = 1.25
        >>> fluxes.qib2 = 1.25
        >>> fluxes.qdb = 1.25
        >>> model.calc_bowa_v1()
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

        We do not to modify negative |EvB| values (condensation) to prevent
        negative |BoWa| values:

        >>> states.bowa = 10.0
        >>> fluxes.evb = -15.0, -10.0, -5.0, 0.0
        >>> fluxes.qbb = 5.0
        >>> fluxes.qib1 = 5.0
        >>> fluxes.qib2 = 5.0
        >>> fluxes.qdb = 5.0
        >>> model.calc_bowa_v1()
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


class Calc_QBGZ_V1(modeltools.Method):
    """Aggregate the amount of base flow released by all "soil type" HRUs
    and the "net precipitation" above water areas of type |SEE|.

    Water areas of type |SEE| are assumed to be directly connected with
    groundwater, but not with the stream network.  This is modelled by
    adding their (positive or negative) "net input" (|NKor|-|EvI|) to the
    "percolation output" of the soil containing HRUs.

    Basic equation:
       :math:`QBGZ = \\Sigma\\bigl(FHRU \\cdot \\bigl(QBB-Qkap\\bigl)\\bigl) +
       \\Sigma\\bigl(FHRU \\cdot \\bigl(NKor_{SEE}-EvI_{SEE}\\bigl)\\bigl)`

    Examples:

        The first example shows that |QBGZ| is the area weighted sum of
        |QBB| from "soil type" HRUs like arable land (|ACKER|) and of
        |NKor|-|EvI| from water areas of type |SEE|.  All other water
        areas (|WASSER| and |FLUSS|) and also sealed surfaces (|VERS|)
        have no impact on |QBGZ|:

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
        >>> states.qbgz
        qbgz(4.5)

        The second example shows that large evaporation values above a
        HRU of type |SEE| can result in negative values of |QBGZ|:

        >>> fluxes.evi[5] = 30
        >>> model.calc_qbgz_v1()
        >>> states.qbgz
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
    RESULTSEQUENCES = (lland_states.QBGZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qbgz = 0.0
        for k in range(con.nhru):
            if con.lnk[k] == SEE:
                sta.qbgz += con.fhru[k] * (flu.nkor[k] - flu.evi[k])
            elif con.lnk[k] not in (WASSER, FLUSS, VERS):
                sta.qbgz += con.fhru[k] * (flu.qbb[k] - flu.qkap[k])


class Calc_QIGZ1_V1(modeltools.Method):
    """Aggregate the amount of the first interflow component released
    by all HRUs.

    Basic equation:
       :math:`QIGZ1 = \\Sigma(FHRU \\cdot QIB1)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fhru(0.75, 0.25)
        >>> fluxes.qib1 = 1.0, 5.0
        >>> model.calc_qigz1_v1()
        >>> states.qigz1
        qigz1(2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (lland_fluxes.QIB1,)
    RESULTSEQUENCES = (lland_states.QIGZ1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qigz1 = 0.0
        for k in range(con.nhru):
            sta.qigz1 += con.fhru[k] * flu.qib1[k]


class Calc_QIGZ2_V1(modeltools.Method):
    """Aggregate the amount of the second interflow component released
    by all HRUs.

    Basic equation:
       :math:`QIGZ2 = \\Sigma(FHRU \\cdot QIB2)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fhru(0.75, 0.25)
        >>> fluxes.qib2 = 1.0, 5.0
        >>> model.calc_qigz2_v1()
        >>> states.qigz2
        qigz2(2.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (lland_fluxes.QIB2,)
    RESULTSEQUENCES = (lland_states.QIGZ2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qigz2 = 0.0
        for k in range(con.nhru):
            sta.qigz2 += con.fhru[k] * flu.qib2[k]


class Calc_QDGZ_V1(modeltools.Method):
    """Aggregate the amount of total direct flow released by all HRUs.

    Basic equation:
       :math:`QDGZ = \\Sigma\\bigl(FHRU \\cdot QDB\\bigl) +
       \\Sigma\\bigl(FHRU \\cdot \\bigl(NKor_{FLUSS}-EvI_{FLUSS}\\bigl)\\bigl)`

    Examples:

        The first example shows that |QDGZ| is the area weighted sum of
        |QDB| from "land type" HRUs like arable land (|ACKER|) and sealed
        surfaces (|VERS|) as well as of |NKor|-|EvI| from water areas of
        type |FLUSS|.  Water areas of type |WASSER| and |SEE| have no
        impact on |QDGZ|:

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

        The second example shows that large evaporation values above a
        HRU of type |FLUSS| can result in negative values of |QDGZ|:

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
    """Separate total direct flow into a slower and a faster component.

    Basic equations:
       :math:`QDGZ2 = \\frac{(QDGZ-A2)^2}{QDGZ+A1-A2}`

       :math:`QDGZ1 = QDGZ - QDGZ2`

    Examples:

        We borrowed the formula for calculating the amount of the faster
        component of direct flow from the well-known curve number approach.
        Parameter |A2| would be the initial loss and parameter |A1| the
        maximum storage, but one should not take this analogy too literally.

        With the value of parameter |A1| set to zero, parameter |A2| defines
        the maximum amount of "slow" direct runoff per time step:

        >>> from hydpy.models.lland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> a1(0.0)

        Let us set the value of |A2| to 4 mm/d, which is 2 mm/12h concerning
        the selected simulation step size:

        >>> a2(4.0)
        >>> a2
        a2(4.0)
        >>> a2.value
        2.0

        Define a test function and let it calculate |QDGZ1| and |QDGZ1| for
        values of |QDGZ| ranging from -10 to 100 mm/12h:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_qdgz1_qdgz2_v1,
        ...                 last_example=6,
        ...                 parseqs=(fluxes.qdgz,
        ...                          states.qdgz1,
        ...                          states.qdgz2))
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

        Setting |A2| to zero and |A1| to 4 mm/d (or 2 mm/12h) results in
        a smoother transition:

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

        Alternatively, one can mix these two configurations by setting
        the values of both parameters to 2 mm/h:

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

        Note the similarity of the results for very high values of total
        direct flow |QDGZ| in all three examples, which converge to the sum
        of the values of parameter |A1| and |A2|, representing the maximum
        value of `slow` direct flow generation per simulation step
    """

    CONTROLPARAMETERS = (
        lland_control.A2,
        lland_control.A1,
    )
    REQUIREDSEQUENCES = (lland_fluxes.QDGZ,)
    RESULTSEQUENCES = (
        lland_states.QDGZ2,
        lland_states.QDGZ1,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if flu.qdgz > con.a2:
            sta.qdgz2 = (flu.qdgz - con.a2) ** 2 / (flu.qdgz + con.a1 - con.a2)
            sta.qdgz1 = flu.qdgz - sta.qdgz2
        else:
            sta.qdgz2 = 0.0
            sta.qdgz1 = flu.qdgz


class Calc_QBGA_V1(modeltools.Method):
    """Perform the runoff concentration calculation for base flow.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QBGA_{neu} = QBGA_{alt} +
       (QBGZ_{alt}-QBGA_{alt}) \\cdot (1-exp(-KB^{-1})) +
       (QBGZ_{neu}-QBGZ_{alt}) \\cdot (1-KB\\cdot(1-exp(-KB^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kb(0.1)
        >>> states.qbgz.old = 2.0
        >>> states.qbgz.new = 4.0
        >>> states.qbga.old = 3.0
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kb(0.0)
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kb(1e500)
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(5.0)
    """

    DERIVEDPARAMETERS = (lland_derived.KB,)
    REQUIREDSEQUENCES = (lland_states.QBGZ,)
    UPDATEDSEQUENCES = (lland_states.QBGA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kb <= 0.0:
            new.qbga = new.qbgz
        elif der.kb > 1e200:
            new.qbga = old.qbga + new.qbgz - old.qbgz
        else:
            d_temp = 1.0 - modelutils.exp(-1.0 / der.kb)
            new.qbga = (
                old.qbga
                + (old.qbgz - old.qbga) * d_temp
                + (new.qbgz - old.qbgz) * (1.0 - der.kb * d_temp)
            )


class Calc_QIGA1_V1(modeltools.Method):
    """Perform the runoff concentration calculation for the first
    interflow component.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QIGA1_{neu} = QIGA1_{alt} +
       (QIGZ1_{alt}-QIGA1_{alt}) \\cdot (1-exp(-KI1^{-1})) +
       (QIGZ1_{neu}-QIGZ1_{alt}) \\cdot (1-KI1\\cdot(1-exp(-KI1^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.ki1(0.1)
        >>> states.qigz1.old = 2.0
        >>> states.qigz1.new = 4.0
        >>> states.qiga1.old = 3.0
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.ki1(0.0)
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.ki1(1e500)
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(5.0)
    """

    DERIVEDPARAMETERS = (lland_derived.KI1,)
    REQUIREDSEQUENCES = (lland_states.QIGZ1,)
    UPDATEDSEQUENCES = (lland_states.QIGA1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.ki1 <= 0.0:
            new.qiga1 = new.qigz1
        elif der.ki1 > 1e200:
            new.qiga1 = old.qiga1 + new.qigz1 - old.qigz1
        else:
            d_temp = 1.0 - modelutils.exp(-1.0 / der.ki1)
            new.qiga1 = (
                old.qiga1
                + (old.qigz1 - old.qiga1) * d_temp
                + (new.qigz1 - old.qigz1) * (1.0 - der.ki1 * d_temp)
            )


class Calc_QIGA2_V1(modeltools.Method):
    """Perform the runoff concentration calculation for the second
    interflow component.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QIGA2_{neu} = QIGA2_{alt} +
       (QIGZ2_{alt}-QIGA2_{alt}) \\cdot (1-exp(-KI2^{-1})) +
       (QIGZ2_{neu}-QIGZ2_{alt}) \\cdot (1-KI2\\cdot(1-exp(-KI2^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.ki2(0.1)
        >>> states.qigz2.old = 2.0
        >>> states.qigz2.new = 4.0
        >>> states.qiga2.old = 3.0
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.ki2(0.0)
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.ki2(1e500)
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(5.0)
    """

    DERIVEDPARAMETERS = (lland_derived.KI2,)
    REQUIREDSEQUENCES = (lland_states.QIGZ2,)
    UPDATEDSEQUENCES = (lland_states.QIGA2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.ki2 <= 0.0:
            new.qiga2 = new.qigz2
        elif der.ki2 > 1e200:
            new.qiga2 = old.qiga2 + new.qigz2 - old.qigz2
        else:
            d_temp = 1.0 - modelutils.exp(-1.0 / der.ki2)
            new.qiga2 = (
                old.qiga2
                + (old.qigz2 - old.qiga2) * d_temp
                + (new.qigz2 - old.qigz2) * (1.0 - der.ki2 * d_temp)
            )


class Calc_QDGA1_V1(modeltools.Method):
    """Perform the runoff concentration calculation for "slow" direct runoff.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QDGA1_{neu} = QDGA1_{alt} +
       (QDGZ1_{alt}-QDGA1_{alt}) \\cdot (1-exp(-KD1^{-1})) +
       (QDGZ1_{neu}-QDGZ1_{alt}) \\cdot (1-KD1\\cdot(1-exp(-KD1^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kd1(0.1)
        >>> states.qdgz1.old = 2.0
        >>> states.qdgz1.new = 4.0
        >>> states.qdga1.old = 3.0
        >>> model.calc_qdga1_v1()
        >>> states.qdga1
        qdga1(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kd1(0.0)
        >>> model.calc_qdga1_v1()
        >>> states.qdga1
        qdga1(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kd1(1e500)
        >>> model.calc_qdga1_v1()
        >>> states.qdga1
        qdga1(5.0)
    """

    DERIVEDPARAMETERS = (lland_derived.KD1,)
    REQUIREDSEQUENCES = (lland_states.QDGZ1,)
    UPDATEDSEQUENCES = (lland_states.QDGA1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kd1 <= 0.0:
            new.qdga1 = new.qdgz1
        elif der.kd1 > 1e200:
            new.qdga1 = old.qdga1 + new.qdgz1 - old.qdgz1
        else:
            d_temp = 1.0 - modelutils.exp(-1.0 / der.kd1)
            new.qdga1 = (
                old.qdga1
                + (old.qdgz1 - old.qdga1) * d_temp
                + (new.qdgz1 - old.qdgz1) * (1.0 - der.kd1 * d_temp)
            )


class Calc_QDGA2_V1(modeltools.Method):
    """Perform the runoff concentration calculation for "fast" direct runoff.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QDGA2_{neu} = QDGA2_{alt} +
       (QDGZ2_{alt}-QDGA2_{alt}) \\cdot (1-exp(-KD2^{-1})) +
       (QDGZ2_{neu}-QDGZ2_{alt}) \\cdot (1-KD2\\cdot(1-exp(-KD2^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kd2(0.1)
        >>> states.qdgz2.old = 2.0
        >>> states.qdgz2.new = 4.0
        >>> states.qdga2.old = 3.0
        >>> model.calc_qdga2_v1()
        >>> states.qdga2
        qdga2(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kd2(0.0)
        >>> model.calc_qdga2_v1()
        >>> states.qdga2
        qdga2(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kd2(1e500)
        >>> model.calc_qdga2_v1()
        >>> states.qdga2
        qdga2(5.0)
    """

    DERIVEDPARAMETERS = (lland_derived.KD2,)
    REQUIREDSEQUENCES = (lland_states.QDGZ2,)
    UPDATEDSEQUENCES = (lland_states.QDGA2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kd2 <= 0.0:
            new.qdga2 = new.qdgz2
        elif der.kd2 > 1e200:
            new.qdga2 = old.qdga2 + new.qdgz2 - old.qdgz2
        else:
            d_temp = 1.0 - modelutils.exp(-1.0 / der.kd2)
            new.qdga2 = (
                old.qdga2
                + (old.qdgz2 - old.qdga2) * d_temp
                + (new.qdgz2 - old.qdgz2) * (1.0 - der.kd2 * d_temp)
            )


class Calc_QAH_V1(modeltools.Method):
    """Calculate the final runoff in mm.

    Basic equation:
       :math:`QAH = QZH + QBGA + QIGA1 + QIGA2 + QDGA1 + QDGA2 +
       NKor_{WASSER} - EvI_{WASSER}`

    In case there are water areas of type |WASSER|, their |NKor| values are
    added and their |EvPo| values are subtracted from the "potential" runoff
    value, if possible.  This can result in problematic modifications of
    simulated runoff series. It seems advisable to use the water types
    |FLUSS| and |SEE| instead.

    Examples:

        When there are no water areas in the respective subbasin (we choose
        arable land |ACKER| arbitrarily), the inflow (|QZH|) and the different
        runoff components (|QBGA|, |QIGA1|, |QIGA2|, |QDGA1|, and |QDGA2|)
        are simply summed up:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER, ACKER, ACKER)
        >>> fhru(0.5, 0.2, 0.3)
        >>> negq(False)
        >>> states.qbga = 0.1
        >>> states.qiga1 = 0.2
        >>> states.qiga2 = 0.3
        >>> states.qdga1 = 0.4
        >>> states.qdga2 = 0.5
        >>> fluxes.qzh = 1.0
        >>> fluxes.nkor = 10.0
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(2.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        The defined values of interception evaporation do not show any
        impact on the result of the given example, the predefined values
        for sequence |EvI| remain unchanged.  But when we define the first
        hydrological as a water area (|WASSER|), |Calc_QAH_V1| adds the
        adjusted precipitaton (|NKor|) to and subtracts the interception
        evaporation (|EvI|) from |lland_fluxes.QAH|:

        >>> control.lnk(WASSER, VERS, NADELW)
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(5.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        Note that only 5 mm are added (instead of the |NKor| value 10 mm)
        and that only 2 mm are substracted (instead of the |EvI| value 4 mm,
        as the first response unit area only accounts for 50 % of the
        total subbasin area.

        Setting also the land use class of the second response unit to water
        type |WASSER| and resetting |NKor| to zero would result in overdrying.
        To avoid this, both actual water evaporation values stored in
        sequence |EvI| are reduced by the same factor:

        >>> control.lnk(WASSER, WASSER, NADELW)
        >>> fluxes.nkor = 0.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(0.0)
        >>> fluxes.evi
        evi(3.333333, 4.166667, 3.0)

        The handling of water areas of type |FLUSS| and |SEE| differs
        from those of type |WASSER|, as these do receive their net input
        before the runoff concentration routines are applied.  This
        should be more realistic in most cases (especially for type |SEE|,
        representing lakes not directly connected to the stream network).
        But it could also, at least for very dry periods, result in negative
        outflow values. We avoid this by setting |lland_fluxes.QAH|
        to zero and adding the truncated negative outflow value to the |EvI|
        value of all response units of type |FLUSS| and |SEE|:

        >>> control.lnk(FLUSS, SEE, NADELW)
        >>> states.qbga = -1.0
        >>> states.qdga2 = -1.9
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_qah_v1()
        >>> fluxes.qah
        qah(0.0)
        >>> fluxes.evi
        evi(2.571429, 3.571429, 3.0)

        This adjustment of |EvI| is only correct regarding the total
        water balance.  Neither spatial nor temporal consistency of the
        resulting |EvI| values are assured.  In the most extreme case,
        even negative |EvI| values might occur.  This seems acceptable,
        as long as the adjustment of |EvI| is rarely triggered.  When in
        doubt about this, check sequences |EvPo| and |EvI| of all |FLUSS|
        and |SEE| units for possible discrepancies.  Also note that
        |lland_fluxes.QAH| might perform unnecessary corrections when you
        combine water type |WASSER| with water type |SEE| or |FLUSS|.

        For some model configurations, negative discharges for dry conditions
        are acceptable or even preferable, which is possible through
        setting parameter |NegQ| to |True|:

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
        lland_states.QBGA,
        lland_states.QIGA1,
        lland_states.QIGA2,
        lland_states.QDGA1,
        lland_states.QDGA2,
        lland_fluxes.NKor,
        lland_fluxes.QZH,
    )
    UPDATEDSEQUENCES = (lland_fluxes.EvI,)
    RESULTSEQUENCES = (lland_fluxes.QAH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.qah = flu.qzh + sta.qbga + sta.qiga1 + sta.qiga2 + sta.qdga1 + sta.qdga2
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
    ADD_METHODS = (
        Return_AdjustedWindSpeed_V1,
        Return_ActualVapourPressure_V1,
        Calc_DailyNetLongwaveRadiation_V1,
        Return_NetLongwaveRadiationSnow_V1,
        Return_DailyGlobalRadiation_V1,
        Return_Penman_V1,
        Return_PenmanMonteith_V1,
        Return_EnergyGainSnowSurface_V1,
        Return_SaturationVapourPressure_V1,
        Return_SaturationVapourPressureSlope_V1,
        Return_NetRadiation_V1,
        Return_WSensSnow_V1,
        Return_WLatSnow_V1,
        Return_WSurf_V1,
        Return_BackwardEulerError_V1,
        Return_TempS_V1,
        Return_WG_V1,
        Return_ESnow_V1,
        Return_TempSSurface_V1,
    )
    RUN_METHODS = (
        Calc_QZH_V1,
        Update_LoggedTemL_V1,
        Calc_TemLTag_V1,
        Update_LoggedRelativeHumidity_V1,
        Calc_DailyRelativeHumidity_V1,
        Update_LoggedSunshineDuration_V1,
        Calc_NKor_V1,
        Calc_TKor_V1,
        Calc_TKorTag_V1,
        Calc_WindSpeed2m_V1,
        Calc_ReducedWindSpeed2m_V1,
        Update_LoggedWindSpeed2m_V1,
        Calc_DailyWindSpeed2m_V1,
        Calc_WindSpeed10m_V1,
        Calc_SolarDeclination_V1,
        Calc_DailySunshineDuration_V1,
        Calc_TSA_TSU_V1,
        Calc_EarthSunDistance_V1,
        Calc_ExtraterrestrialRadiation_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_DailyPossibleSunshineDuration_V1,
        Calc_SP_V1,
        Calc_GlobalRadiation_V1,
        Update_LoggedGlobalRadiation_V1,
        Calc_DailyGlobalRadiation_V1,
        Calc_AdjustedGlobalRadiation_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_DailySaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V1,
        Calc_DailySaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Calc_DailyActualVapourPressure_V1,
        Calc_ET0_V1,
        Calc_ET0_WET0_V1,
        Calc_EvPo_V1,
        Calc_NBes_Inzp_V1,
        Calc_SNRatio_V1,
        # Calc_F2SIMax_V1,
        # Calc_SInzpCap_V1,
        # Calc_F2SIRate_V1,
        # Calc_SInzpRate_V1,
        # Calc_NBes_SInz_V1,
        Calc_SBes_V1,
        Calc_WATS_V1,
        Calc_WaDa_WAeS_V1,
        Calc_WGTF_V1,
        Calc_WNied_V1,
        Calc_WNied_ESnow_V1,
        Calc_TZ_V1,
        Calc_WG_V1,
        Calc_TempS_V1,
        Update_TauS_V1,
        Calc_ActualAlbedo_V1,
        Calc_NetShortwaveRadiation_V1,
        Calc_NetShortwaveRadiationSnow_V1,
        Calc_DailyNetShortwaveRadiation_V1,
        Calc_G_V1,
        Calc_G_V2,
        Calc_EvB_V2,
        Update_EBdn_V1,
        Update_ESnow_V1,
        Calc_NetRadiation_V1,
        Calc_DailyNetRadiation_V1,
        Calc_DryAirPressure_V1,
        Calc_DensityAir_V1,
        Calc_AerodynamicResistance_V1,
        Calc_SoilSurfaceResistance_V1,
        Calc_LanduseSurfaceResistance_V1,
        Calc_ActualSurfaceResistance_V1,
        Calc_EvPo_V2,
        Calc_EvI_Inzp_V1,
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
        Calc_QDGZ1_QDGZ2_V1,
        Calc_QBGA_V1,
        Calc_QIGA1_V1,
        Calc_QIGA2_V1,
        Calc_QDGA1_V1,
        Calc_QDGA2_V1,
        Calc_QAH_V1,
        Calc_QA_V1,
    )
    OUTLET_METHODS = (Pass_QA_V1,)
    SENDER_METHODS = ()
    SUBMODELS = (
        PegasusESnow,
        PegasusTempSSurface,
    )
    idx_hru = modeltools.Idx_HRU()
