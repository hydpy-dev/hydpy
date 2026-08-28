# pylint: disable=missing-module-docstring

import contextlib

import inflect
import numpy

from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import throughfallinterfaces
from hydpy.models.snow import snow_parameters
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_derived
from hydpy.models.snow import snow_fixed
from hydpy.models.snow import snow_sequences
from hydpy.models.snow import snow_inputs
from hydpy.models.snow import snow_factors
from hydpy.models.snow import snow_fluxes
from hydpy.models.snow import snow_states
from hydpy.models.snow import snow_logs
from hydpy.models.snow import snow_aides


class Calc_Throughfall_ThroughfallModel_V1(modeltools.Method):
    """Query the throughfall from a main model referenced as a sub-submodel and
    follows the |ThroughfallModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |snow_dd| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(3.0)
        >>> nmbzones(3)
        >>> zonetype(FIELD)
        >>> zonearea(1.0)
        >>> zonez(10.0)
        >>> with model.add_snowmodel_v1("snow_dd") as snowmodel:
        ...     redistributionpaths(n_zones=1)
        >>> fluxes.tf = 2.0, 0.0, 5.0
        >>> snowmodel.calc_throughfall_v1()
        >>> snowmodel.sequences.fluxes.throughfall
        throughfall(2.0, 0.0, 5.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (snow_control.NumberZones,)
    RESULTSEQUENCES = (snow_fluxes.Throughfall,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: throughfallinterfaces.ThroughfallModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.numberzones):
            flu.throughfall[k] = submodel.get_throughfall(k)


class Calc_Throughfall_ThroughfallModel_V2(modeltools.Method):
    """Let a submodel that complies with the |ThroughfallModel_V2| interface provide the
    throughfall.

    Example:

        We use the combination of |snow_dd| and |meteo_throughfall_io| as an example:

        >>> from hydpy.models.snow_dd import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> with model.add_throughfallmodel_v2("meteo_throughfall_io"):
        ...     inputs.throughfall = 3.0, 4.0, 6.0
        >>> model.calc_throughfall_v1()
        >>> fluxes.throughfall
        throughfall(3.0, 4.0, 6.0)
    """

    CONTROLPARAMETERS = (snow_control.NumberZones,)
    RESULTSEQUENCES = (snow_fluxes.Throughfall,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: throughfallinterfaces.ThroughfallModel_V2
    ) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.numberzones):
            flu.throughfall[k] = submodel.get_throughfall(k)


class Calc_Throughfall_V1(modeltools.Method):
    """Let a submodel that complies with the |ThroughfallModel_V1| or the
    |ThroughfallModel_V2| interface provide the throughfall."""

    SUBMODELINTERFACES = (
        throughfallinterfaces.ThroughfallModel_V1,
        throughfallinterfaces.ThroughfallModel_V2,
    )
    SUBMETHODS = (
        Calc_Throughfall_ThroughfallModel_V1,
        Calc_Throughfall_ThroughfallModel_V2,
    )
    CONTROLPARAMETERS = (snow_control.NumberZones,)
    RESULTSEQUENCES = (snow_fluxes.Throughfall,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        if model.throughfallmodel_typeid == 1:
            model.calc_throughfall_throughfallmodel_v1(
                cast(throughfallinterfaces.ThroughfallModel_V1, model.throughfallmodel)
            )
        elif model.throughfallmodel_typeid == 2:
            model.calc_throughfall_throughfallmodel_v2(
                cast(throughfallinterfaces.ThroughfallModel_V2, model.throughfallmodel)
            )


class Calc_AdjustedTemperature_V1(modeltools.Method):
    r"""Correct the subbasin-wide, measured air temperature and adjust it to the
    altitude of the individual zones.

    Basic equation:
      .. math::
        T_{adj} = T + A - L \cdot (Z - Z_{mean})
        \\ \\
        T_{adj} = AdjustedTemperature \\
        T = AirTemperature \\
        A = TemperatureAddend \\
        L = LapseRate \\
        Z = ZoneHeight \\
        Z_{mean} = AverageHeight

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> zoneheight(2.0, 4.0, 6.0)
        >>> temperatureaddend(1.0)
        >>> lapserate(0.6)
        >>> derived.averageheight(4.0)
        >>> inputs.airtemperature = 5.0
        >>> model.calc_adjustedtemperature_v1()
        >>> factors.adjustedtemperature
        adjustedtemperature(7.2, 6.0, 4.8)
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.TemperatureAddend,
        snow_control.LapseRate,
        snow_control.ZoneHeight,
    )
    DERIVEDPARAMETERS = (snow_derived.AverageHeight,)
    REQUIREDSEQUENCES = (snow_inputs.AirTemperature,)
    RESULTSEQUENCES = (snow_factors.AdjustedTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.numberzones):
            fac.adjustedtemperature[k] = (
                inp.airtemperature
                + con.temperatureaddend[k]
                - con.lapserate[k] * (con.zoneheight[k] - der.averageheight)
            )


class Calc_RainSnowFraction_V1(modeltools.Method):
    r"""Determine the ratio of rain to total precipitation

    Basic equation:
      .. math::
        F = min \left( max \left(
        \frac{T - (\tau - \delta / 2)}{\delta}, \, 0 \right), \, 1 \right)
        \\ \\
        F = RainSnowFraction \\
        T = AdjustedAirTemperature \\
        \tau = RainSnowThreshold \\
        \delta = RainSnowInterval

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(7)
        >>> rainsnowthreshold(1.0)
        >>> rainsnowinterval(2.0)
        >>> factors.adjustedtemperature = -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0
        >>> model.calc_rainsnowfraction_v1()
        >>> factors.rainsnowfraction
        rainsnowfraction(0.0, 0.0, 0.25, 0.5, 0.75, 1.0, 1.0)

        For the special case of |RainSnowInterval| being one and |RainSnowThreshold| and
        |AdjustedTemperature| being the same, |RainSnowFraction| is 1:

        >>> rainsnowinterval(0.0)
        >>> model.calc_rainsnowfraction_v1()
        >>> factors.rainsnowfraction
        rainsnowfraction(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.RainSnowThreshold,
        snow_control.RainSnowInterval,
    )
    REQUIREDSEQUENCES = (snow_factors.AdjustedTemperature,)
    RESULTSEQUENCES = (snow_factors.RainSnowFraction,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.numberzones):
            dt: float = con.rainsnowinterval[k] / 2.0
            if fac.adjustedtemperature[k] < (con.rainsnowthreshold[k] - dt):
                fac.rainsnowfraction[k] = 0.0
            elif fac.adjustedtemperature[k] >= (con.rainsnowthreshold[k] + dt):
                fac.rainsnowfraction[k] = 1.0
            else:
                fac.rainsnowfraction[k] = (
                    fac.adjustedtemperature[k] - (con.rainsnowthreshold[k] - dt)
                ) / con.rainsnowinterval[k]


class Calc_IceContent_WaterContent_V1(modeltools.Method):
    r"""Add the throughfall to the snow layer.

    Basic equations:
      .. math::
        I_{new} = I_{old} + D \cdot (1 - F) \cdot T
        \\
        I_{new} = I_{old} + D \cdot F \cdot T
        \\ \\
        I = IceContent \\
        W = WaterContent \\
        D = ThroughfallDistribution\\
        F = RainSnowFraction \\
        T = Throughfall

    Example:

        The basic equation applies to all zones except those that represent water areas,
        for which |IceContent| and |WaterContent| are set to zero:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(6)
        >>> numberdivisions(2)
        >>> land(False, True, True, True, True, True)
        >>> throughfalldistribution(0.5, 1.5)
        >>> fluxes.throughfall = 4.0
        >>> factors.rainsnowfraction(0.5, 0.0, 0.25, 0.5, 0.75, 1.0)
        >>> states.icecontent = 2.0
        >>> states.watercontent = 1.0
        >>> model.calc_icecontent_watercontent_v1()
        >>> states.icecontent
        icecontent([[0.0, 4.0, 3.5, 3.0, 2.5, 2.0],
                    [0.0, 8.0, 6.5, 5.0, 3.5, 2.0]])
        >>> states.watercontent
        watercontent([[0.0, 1.0, 1.5, 2.0, 2.5, 3.0],
                      [0.0, 1.0, 2.5, 4.0, 5.5, 7.0]])
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
        snow_control.ThroughfallDistribution,
    )
    REQUIREDSEQUENCES = (snow_fluxes.Throughfall, snow_factors.RainSnowFraction)
    UPDATEDSEQUENCES = (snow_states.IceContent, snow_states.WaterContent)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.numberzones):
            if con.land[k]:
                rain: float = flu.throughfall[k] * fac.rainsnowfraction[k]
                snow: float = flu.throughfall[k] * (1.0 - fac.rainsnowfraction[k])
                for c in range(con.numberdivisions):
                    sta.watercontent[c, k] += con.throughfalldistribution[c] * rain
                    sta.icecontent[c, k] += con.throughfalldistribution[c] * snow
            else:
                for c in range(con.numberdivisions):
                    sta.watercontent[c, k] = 0.0
                    sta.icecontent[c, k] = 0.0


class Calc_IceLoss_WaterLoss_IceContent_WaterContent_V1(modeltools.Method):
    r"""Calculate the subbasin-internal redistribution losses of the snow layer.

    Basic equations:
      .. math::
        I_{new} = I_{old} - I_L \\
        W_{new} = W_{old} - W_L \\
        I_L = I_{old} \cdot f \\
        W_L = W_{old} \cdot f \\
        f = max \left( \frac{I + W - S}{I + W}, \, 0 \right)
        \\ \\
        I = IceContent \\
        W = WaterContent \\
        I_L = IceLoss \\
        W_L = WaterLoss \\
        S = SnowpackLimit

    Examples:

        The basic equation applies to all zones except those that represent water areas,
        for which |IceContent|, |WaterContent|, |IceLoss|, and |WaterLoss| are set to
        zero.  The relation between |IceLoss| and |WaterLoss| loss depends on the
        relation between |IceContent| and |WaterContent|.  For multiple divisions of a
        zone ("snow classes"), the total loss does not depend on the average storage but
        on the degree of exceedance of |SnowpackLimit| within the individual
        subdivisions:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(5)
        >>> numberdivisions(2)
        >>> land(False, True, True, True, True)
        >>> snowpacklimit(500.0)
        >>> states.icecontent = [[600.0, 600.0, 60.0, 800.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0]]
        >>> states.watercontent = [[200.0, 200.0, 20.0, 0.0, 800.0],
        ...                        [0.0, 0.0, 0.0, 0.0, 0.0]]
        >>> model.calc_iceloss_waterloss_icecontent_watercontent_v1()
        >>> fluxes.iceloss
        iceloss(0.0, 112.5, 0.0, 150.0, 0.0)
        >>> fluxes.waterloss
        waterloss(0.0, 37.5, 0.0, 0.0, 150.0)
        >>> states.icecontent
        icecontent([[0.0, 375.0, 60.0, 500.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0]])
        >>> states.watercontent
        watercontent([[0.0, 125.0, 20.0, 0.0, 500.0],
                      [0.0, 0.0, 0.0, 0.0, 0.0]])
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
        snow_control.SnowpackLimit,
    )
    UPDATEDSEQUENCES = (snow_states.IceContent, snow_states.WaterContent)
    RESULTSEQUENCES = (snow_fluxes.IceLoss, snow_fluxes.WaterLoss)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.numberzones):
            flu.iceloss[k] = 0.0
            flu.waterloss[k] = 0.0
            if not con.land[k]:
                for c in range(con.numberdivisions):
                    sta.icecontent[c, k] = 0.0
                    sta.watercontent[c, k] = 0.0
            elif not modelutils.isinf(con.snowpacklimit[k]):
                for c in range(con.numberdivisions):
                    snow: float = sta.icecontent[c, k] + sta.watercontent[c, k]
                    excess: float = snow - con.snowpacklimit[k]
                    if excess > 0.0:
                        excess_ice: float = excess * sta.icecontent[c, k] / snow
                        excess_water: float = excess * sta.watercontent[c, k] / snow
                        flu.iceloss[k] += excess_ice / con.numberdivisions
                        flu.waterloss[k] += excess_water / con.numberdivisions
                        sta.icecontent[c, k] -= excess_ice
                        sta.watercontent[c, k] -= excess_water


class Calc_IceGain_WaterGain_IceContent_WaterContent_V1(modeltools.Method):
    r"""Calculate the subbasin-internal redistribution gains of the snow layer.

    Basic equations:
      .. math::
        I_{new} = I_{old} + I_G \\
        W_{new} = W_{old} + W_G
        \\ \\
        I = IceContent \\
        W = WaterContent \\
        I_G = IceGain \\
        W_G = WaterGain

    Examples:

        We prepare an example consisting of seven zones, sorted by (non-strictly)
        descending elevation.  For now, there is a single snow class per zone, and the
        zones' areas are identical (1.0 km²).  The last zone is a water area and does
        not participate in snow redistribution. We use the same configuration for
        |SnowpackLimit| (the maximum snow water equivalent) and |RedistributionPaths|
        (defining the redistribution paths) throughout all examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(7)
        >>> numberdivisions(1)
        >>> land(True, True, True, True, True, True, False)
        >>> zoneheight(30.0, 25.0, 20.0, 15.0, 10.0, 10.0, 5.0)
        >>> zonearea(1.0)
        >>> throughfalldistribution(1.0)
        >>> snowpacklimit(500.0)
        >>> redistributionpaths([[0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
        ...                      [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

        For convenience, we prepare a function that updates all relevant derived
        parameters:

        >>> def update():
        ...     derived.landareafraction.update()
        ...     derived.zoneareafraction.update()
        ...     derived.zonearearatio.update()
        ...     derived.zoneheightorder.update()
        ...     derived.redistributionorder.update()
        ...     derived.redistributionnumber.update()
        ...     derived.redistributionend.update()
        >>> update()

        In the first example, the total snow water equivalent (300 mm) is way below
        |SnowpackLimit| (500 mm).  Hence, all frozen (|IceLoss|) and liquid
        (|WaterLoss|) losses deposit completely in the target zones:

        >>> states.icecontent = 200.0
        >>> states.watercontent = 100.0
        >>> fluxes.iceloss = 20.0, 20.0, 20.0, 20.0, 0.0, 0.0, 0.0
        >>> fluxes.waterloss = 10.0, 10.0, 10.0, 10.0, 0.0, 0.0, 0.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(0.0, 4.0, 24.0, 24.0, 14.0, 14.0, 0.0)
        >>> fluxes.watergain
        watergain(0.0, 2.0, 12.0, 12.0, 7.0, 7.0, 0.0)
        >>> states.icecontent
        icecontent(200.0, 204.0, 224.0, 224.0, 214.0, 214.0, 0.0)
        >>> states.watercontent
        watercontent(100.0, 102.0, 112.0, 112.0, 107.0, 107.0, 0.0)

        The following test function checks that method
        |Calc_IceGain_WaterGain_IceContent_WaterContent_V1| does not introduce any
        water balance errors:

        >>> from hydpy import repr_
        >>> def check(ic_old, wc_old):
        ...     def check_vector(deltas):
        ...         return numpy.max(numpy.abs(numpy.sum(deltas, axis=0)))
        ...     ic_new = states.icecontent.average_values("land")
        ...     ic_loss = fluxes.iceloss.average_values("land")
        ...     ic_gain = fluxes.icegain.average_values("land")
        ...     ic_old_array = numpy.asarray(6 * [ic_old] + [0.0])
        ...     wc_new = states.watercontent.average_values("land")
        ...     wc_loss = fluxes.waterloss.average_values("land")
        ...     wc_gain = fluxes.watergain.average_values("land")
        ...     wc_old_array = numpy.asarray(6 * [wc_old] + [0.0])
        ...     errors = [
        ...         ic_old + ic_loss - ic_new,
        ...         ic_loss - ic_gain,
        ...         check_vector(ic_old_array + fluxes.icegain - states.icecontent),
        ...         wc_old + wc_loss - wc_new,
        ...         wc_loss - wc_gain,
        ...         check_vector(wc_old_array + fluxes.watergain - states.watercontent)
        ...     ]
        ...     print(*(repr_(error) for error in errors), sep=", ")

        The possible errors related to different aspects of the frozen and the liquid
        water content of the snow layer are all within the range of the given numerical
        precision:

        >>> check(ic_old=200.0, wc_old=100.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        Next, we increase the size of the first area and decrease the size of the second
        area by the same amount.  The different results for |IceGain| and |WaterGain|
        reflect that the loss terms (|IceLoss| and |WaterLoss|) relate to the sizes of
        the supplying zones while the gain terms (|IceGain| and |WaterGain|) relate to
        the sizes of the receiving zones:

        >>> zonearea(1.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> update()
        >>> states.icecontent = 200.0
        >>> states.watercontent = 100.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(0.0, 12.0, 16.0, 26.0, 16.0, 16.0, 0.0)
        >>> fluxes.watergain
        watergain(0.0, 6.0, 8.0, 13.0, 8.0, 8.0, 0.0)
        >>> states.icecontent
        icecontent(200.0, 212.0, 216.0, 226.0, 216.0, 216.0, 0.0)
        >>> states.watercontent
        watercontent(100.0, 106.0, 108.0, 113.0, 108.0, 108.0, 0.0)
        >>> check(ic_old=200.0, wc_old=100.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        When modelling high mountain areas, even the lowest zones (the so-called
        "dead-ends") can receive substantial amounts of redistributed snow.  Therefore,
        the simple "from top to bottom" approach described so far can result in
        unrealistic snow towers for these dead-ends, especially if their size is small
        compared to the size of the snow-delivering area.  To prevent such artefacts,
        method |Calc_IceGain_WaterGain_IceContent_WaterContent_V1| takes the total snow
        amount of all dead-ends exceeding the |SnowpackLimit| threshold and distributes
        it gradually to the other zones, starting from the lowest in the order defined
        by parameter |ZoneHeightOrder|:

        >>> zonearea(1.0)
        >>> update()
        >>> states.icecontent = 400.0
        >>> states.watercontent = 75.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(0.0, 13.333333, 16.666667, 16.666667, 16.666667, 16.666667, 0.0)
        >>> fluxes.watergain
        watergain(0.0, 6.666667, 8.333333, 8.333333, 8.333333, 8.333333, 0.0)
        >>> states.icecontent
        icecontent(400.0, 413.333333, 416.666667, 416.666667, 416.666667,
                   416.666667, 0.0)
        >>> states.watercontent
        watercontent(75.0, 81.666667, 83.333333, 83.333333, 83.333333,
                     83.333333, 0.0)
        >>> check(ic_old=400.0, wc_old=75.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        If the total snow amount of all zone reaches |SnowpackLimit|,
        |Calc_IceGain_WaterGain_IceContent_WaterContent_V1| distributes all remaining
        excess evenly to all non-water zones:

        >>> states.icecontent = 400.0
        >>> states.watercontent = 90.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(13.333333, 13.333333, 13.333333, 13.333333, 13.333333,
                13.333333, 0.0)
        >>> fluxes.watergain
        watergain(6.666667, 6.666667, 6.666667, 6.666667, 6.666667, 6.666667,
                  0.0)
        >>> states.icecontent
        icecontent(413.333333, 413.333333, 413.333333, 413.333333, 413.333333,
                   413.333333, 0.0)
        >>> states.watercontent
        watercontent(96.666667, 96.666667, 96.666667, 96.666667, 96.666667,
                     96.666667, 0.0)
        >>> check(ic_old=400.0, wc_old=90.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        Introducing multiple subdivisions ("snow classes") within each zone complicates
        things.  We repeat some of the above examples with |NumberDivisions| set to two:

        >>> numberdivisions(2)
        >>> update()

        The "normal" snow redistribution relies similarly on parameter
        |RedistributionPaths| as the snowfall accumulation does.  We show this by
        repeating the first example with the most extreme configuration of
        |RedistributionPaths|, where the second snow class receives the entire amount of
        incoming snow:

        >>> throughfalldistribution(0.0, 2.0)
        >>> states.icecontent = 200.0
        >>> states.watercontent = 100.0
        >>> fluxes.iceloss = 20.0, 20.0, 20.0, 20.0, 0.0, 0.0, 0.0
        >>> fluxes.waterloss = 10.0, 10.0, 10.0, 10.0, 0.0, 0.0, 0.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(0.0, 4.0, 24.0, 24.0, 14.0, 14.0, 0.0)
        >>> fluxes.watergain
        watergain(0.0, 2.0, 12.0, 12.0, 7.0, 7.0, 0.0)
        >>> states.icecontent
        icecontent([[200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 0.0],
                    [200.0, 208.0, 248.0, 248.0, 228.0, 228.0, 0.0]])
        >>> states.watercontent
        watercontent([[100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 0.0],
                      [100.0, 104.0, 124.0, 124.0, 114.0, 114.0, 0.0]])

        During the eventual "bottom to top" re-redistribution, on the other hand,
        the fractions between the gains of individual snow classes do not depend on
        |RedistributionPaths| but on their remaining capacities:

        >>> states.icecontent = 400.0
        >>> states.watercontent = 75.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(0.0, 13.333333, 16.666667, 16.666667, 16.666667, 16.666667, 0.0)
        >>> fluxes.watergain
        watergain(0.0, 6.666667, 8.333333, 8.333333, 8.333333, 8.333333, 0.0)
        >>> states.icecontent
        icecontent([[400.0, 412.280702, 416.666667, 416.666667, 416.666667,
                     416.666667, 0.0],
                    [400.0, 414.385965, 416.666667, 416.666667, 416.666667,
                     416.666667, 0.0]])
        >>> states.watercontent
        watercontent([[75.0, 81.140351, 83.333333, 83.333333, 83.333333,
                       83.333333, 0.0],
                      [75.0, 82.192982, 83.333333, 83.333333, 83.333333,
                       83.333333, 0.0]])
        >>> check(ic_old=400.0, wc_old=75.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        During a subbasin-wide excess of |SnowpackLimit|, all snow classes of a specific
        zone handle the same total snow water equivalent:

        >>> states.icecontent = 400.0
        >>> states.watercontent = 90.0
        >>> model.calc_icegain_watergain_icecontent_watercontent_v1()
        >>> fluxes.icegain
        icegain(13.333333, 13.333333, 13.333333, 13.333333, 13.333333,
                13.333333, 0.0)
        >>> fluxes.watergain
        watergain(6.666667, 6.666667, 6.666667, 6.666667, 6.666667, 6.666667,
                  0.0)
        >>> states.icecontent
        icecontent([[413.333333, 413.333333, 413.333333, 413.333333, 413.333333,
                     413.333333, 0.0],
                    [413.333333, 413.333333, 413.333333, 413.333333, 413.333333,
                     413.333333, 0.0]])
        >>> states.watercontent
        watercontent([[96.666667, 96.666667, 96.666667, 96.666667, 96.666667,
                       96.666667, 0.0],
                      [96.666667, 96.666667, 96.666667, 96.666667, 96.666667,
                       96.666667, 0.0]])
        >>> check(ic_old=400.0, wc_old=90.0)
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
        snow_control.ThroughfallDistribution,
        snow_control.SnowpackLimit,
        snow_control.RedistributionPaths,
    )
    DERIVEDPARAMETERS = (
        snow_derived.LandAreaFraction,
        snow_derived.ZoneAreaFraction,
        snow_derived.ZoneAreaRatio,
        snow_derived.ZoneHeightOrder,
        snow_derived.RedistributionNumber,
        snow_derived.RedistributionOrder,
        snow_derived.RedistributionEnd,
    )
    REQUIREDSEQUENCES = (snow_fluxes.IceLoss, snow_fluxes.WaterLoss)
    UPDATEDSEQUENCES = (snow_states.IceContent, snow_states.WaterContent)
    RESULTSEQUENCES = (
        snow_aides.IceContentExcess,
        snow_aides.WaterContentExcess,
        snow_fluxes.IceGain,
        snow_fluxes.WaterGain,
    )

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess

        # initialise gain and excess:
        for i in range(con.numberzones):
            flu.icegain[i] = 0.0
            flu.watergain[i] = 0.0
            aid.icecontentexcess[i] = 0.0
            aid.watercontentexcess[i] = 0.0
            if not con.land[i]:
                for c in range(con.numberdivisions):
                    sta.icecontent[c, i] = 0.0
                    sta.watercontent[c, i] = 0.0

        # redistribute losses from top to bottom:
        for i in range(der.redistributionnumber):
            # f: from, t: to
            f, t = der.redistributionorder[i, 0], der.redistributionorder[i, 1]
            adjust: float = der.zonearearatio[f, t] * con.redistributionpaths[f, t]
            gain_ice: float = adjust * (flu.iceloss[f] + aid.icecontentexcess[f])
            gain_water: float = adjust * (flu.waterloss[f] + aid.watercontentexcess[f])
            gain_total: float = gain_ice + gain_water
            for c in range(con.numberdivisions):
                gain_pot: float = con.throughfalldistribution[c] * gain_total
                if gain_pot > 0.0:
                    gain_max: float = (
                        con.snowpacklimit[t]
                        - sta.icecontent[c, t]
                        - sta.watercontent[c, t]
                    )
                    fraction_gain: float = min(gain_max / gain_pot, 1.0)
                    factor_gain: float = fraction_gain * con.throughfalldistribution[c]
                    flu.icegain[t] += factor_gain * gain_ice / con.numberdivisions
                    flu.watergain[t] += factor_gain * gain_water / con.numberdivisions
                    sta.icecontent[c, t] += factor_gain * gain_ice
                    sta.watercontent[c, t] += factor_gain * gain_water
                    factor_excess: float = (
                        1.0 - fraction_gain
                    ) * con.throughfalldistribution[c]
                    aid.icecontentexcess[t] += (
                        factor_excess * gain_ice / con.numberdivisions
                    )
                    aid.watercontentexcess[t] += (
                        factor_excess * gain_water / con.numberdivisions
                    )

        # check for remaining excess at the dead ends:
        excess_ice_basin: float = 0.0
        excess_water_basin: float = 0.0
        for i in range(con.numberzones):
            if der.redistributionend[i]:
                excess_ice_basin += der.zoneareafraction[i] * (
                    aid.icecontentexcess[i] + flu.iceloss[i]
                )
                excess_water_basin += der.zoneareafraction[i] * (
                    aid.watercontentexcess[i] + flu.waterloss[i]
                )
        if (excess_ice_basin + excess_water_basin) <= 0.0:
            return

        # redistribute the remaining excess from bottom to top:
        for i in range(con.numberzones):
            t = der.zoneheightorder[i]
            if not con.land[t]:
                continue
            excess_ice_zone: float = excess_ice_basin / der.zoneareafraction[t]
            excess_water_zone: float = excess_water_basin / der.zoneareafraction[t]
            excess_total_zone: float = excess_ice_zone + excess_water_zone
            gain_max_cum: float = 0.0
            for c in range(con.numberdivisions):
                gain_max_cum += (
                    con.snowpacklimit[t] - sta.icecontent[c, t] - sta.watercontent[c, t]
                )
            if gain_max_cum <= 0.0:
                continue
            fraction_gain_zone: float = min(
                gain_max_cum / con.numberdivisions / excess_total_zone, 1.0
            )
            excess_ice_zone_actual: float = fraction_gain_zone * excess_ice_zone
            excess_water_zone_actual: float = fraction_gain_zone * excess_water_zone
            for c in range(con.numberdivisions):
                fraction_gain_class: float = (
                    con.snowpacklimit[t] - sta.icecontent[c, t] - sta.watercontent[c, t]
                ) / gain_max_cum
                delta_icecontent_zone: float = (
                    fraction_gain_class * excess_ice_zone_actual
                )
                delta_watercontent_zone: float = (
                    fraction_gain_class * excess_water_zone_actual
                )
                flu.icegain[t] += delta_icecontent_zone
                flu.watergain[t] += delta_watercontent_zone
                sta.icecontent[c, t] += delta_icecontent_zone * con.numberdivisions
                sta.watercontent[c, t] += delta_watercontent_zone * con.numberdivisions
            excess_ice_basin -= excess_ice_zone_actual * der.zoneareafraction[t]
            excess_water_basin -= excess_water_zone_actual * der.zoneareafraction[t]
            if (excess_ice_basin + excess_water_basin) <= 0.0:
                return

        # redistribute the still remaining excess evenly:
        excess_ice_land: float = excess_ice_basin / der.landareafraction
        excess_water_land: float = excess_water_basin / der.landareafraction
        for t in range(con.numberzones):
            if con.land[t]:
                flu.icegain[t] += excess_ice_land
                flu.watergain[t] += excess_water_land
                for c in range(con.numberdivisions):
                    sta.icecontent[c, t] += excess_ice_land
                    sta.watercontent[c, t] += excess_water_land
        return


class Calc_MeltingFactor_V1(modeltools.Method):
    r"""Adjust the day degree snowmelt factor to the current day of the year.

    Basic equations:
      .. math::
        M = max(F + f \cdot V, \, 0) \\
        f = sin \big(2 \cdot  \pi \cdot (d + 1) / 366 \big) / 2
        \\ \\
        M = MeltingFactor \\
        F = DegreeDayFactor \\
        V = DegreeDayVariability \\
        \pi = Pi \\
        d = DOY

    Examples:

        We initialise six zones, of which the first represents a water area and the
        others represent land areas.  The average degree day factors (|DegreeDayFactor|)
        is identical for all zones, but its annual variability (|DegreeDayVariability|)
        differs.  For water areas, the resulting melting factor is always zero (first
        zone).  For the land areas, it follows a sinusoidal curve throughout the year,
        of which we show only selected points at the extremes around June 20 and
        December 20.  For zero |DegreeDayVariability|, |MeltingFactor| is always
        identical to |DegreeDayFactor| (second zone).  Positive and negative
        |DegreeDayVariability| values result in sinusoid curves that reflect the
        northern and southern hemisphere's annual cycle of radiation, respectively
        (zones three and four).  Note that |Calc_MeltingFactor_V1| prevents negative
        |MeltingFactor| values by setting them to zero (zones five and six):

        >>> from hydpy.models.snow import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> numberzones(6)
        >>> land(False, True, True, True, True, True)
        >>> degreedayfactor(4.0)
        >>> degreedayvariability(0.0, 0.0, 3.0, -3.0, 10.0, -10.0)
        >>> derived.doy.shape = 1
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_meltingfactor_v1,
        ...                 last_example=10,
        ...                 parseqs=(derived.doy, factors.meltingfactor))
        >>> test.nexts.doy = 0, 1, 170, 171, 172, 353, 354, 355, 364, 365
        >>> test()
        | ex. | doy |                                         meltingfactor |
        ---------------------------------------------------------------------
        |   1 |   0 | 0.0  2.0  1.264648  2.735352       0.0       4.451173 |
        |   2 |   1 | 0.0  2.0  1.267289  2.732711       0.0       4.442371 |
        |   3 | 170 | 0.0  2.0  2.749762  1.250238  4.499206            0.0 |
        |   4 | 171 | 0.0  2.0  2.749976  1.250024  4.499919            0.0 |
        |   5 | 172 | 0.0  2.0  2.749969  1.250031  4.499896            0.0 |
        |   6 | 353 | 0.0  2.0  1.250238  2.749762       0.0       4.499206 |
        |   7 | 354 | 0.0  2.0  1.250024  2.749976       0.0       4.499919 |
        |   8 | 355 | 0.0  2.0  1.250031  2.749969       0.0       4.499896 |
        |   9 | 364 | 0.0  2.0  1.260018  2.739982       0.0       4.466606 |
        |  10 | 365 | 0.0  2.0  1.262224  2.737776       0.0       4.459252 |
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.Land,
        snow_control.DegreeDayFactor,
        snow_control.DegreeDayVariability,
    )
    FIXEDPARAMETERS = (snow_fixed.Pi,)
    DERIVEDPARAMETERS = (snow_derived.DOY,)
    RESULTSEQUENCES = (snow_factors.MeltingFactor,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess

        c: float = 0.5 * modelutils.sin(
            2 * fix.pi * (der.doy[model.idx_sim] + 1) / 366 - 1.39
        )
        for k in range(con.numberzones):
            if con.land[k]:
                fac.meltingfactor[k] = max(
                    con.degreedayfactor[k] + c * con.degreedayvariability[k], 0.0
                )
            else:
                fac.meltingfactor[k] = 0.0


class Calc_PotentialMelt_V1(modeltools.Method):
    r"""Calculate the potential snowmelt according to the degree day method.

    Basic equation:
      .. math::
        P = \begin{cases}
        0 &|\ \overline{L} \ \lor \ T \leq \tau \\
        F \cdot (T - \tau) &|\ \overline{L} \ \land \ T > \tau
        \end{cases}
        \\ \\
        L = Land \\
        P = PotentialMelt \\
        T = AdjustedTemperature \\
        F = MeltingFactor \\
        \tau = DegreeDayThreshold

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(5)
        >>> land(True, True, True, True, False)
        >>> degreedaythreshold(2.0, 1.0, 0.0, -1.0, -1.0)
        >>> factors.adjustedtemperature = 1.0
        >>> factors.meltingfactor = 3.0
        >>> model.calc_potentialmelt_v1()
        >>> fluxes.potentialmelt
        potentialmelt(0.0, 0.0, 3.0, 6.0, 0.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.Land,
        snow_control.DegreeDayThreshold,
    )
    REQUIREDSEQUENCES = (snow_factors.AdjustedTemperature, snow_factors.MeltingFactor)
    RESULTSEQUENCES = (snow_fluxes.PotentialMelt,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.numberzones):
            if con.land[k] and (fac.adjustedtemperature[k] > con.degreedaythreshold[k]):
                flu.potentialmelt[k] = fac.meltingfactor[k] * (
                    fac.adjustedtemperature[k] - con.degreedaythreshold[k]
                )
            else:
                flu.potentialmelt[k] = 0.0


class Calc_PotentialFreeze_V1(modeltools.Method):
    r"""Calculate the potential (re)freezing of snow water according to the degree day
    method.

    Basic equation:
      .. math::
        P = \begin{cases}
        F \cdot D \cdot (\tau - T) &|\ \overline{L} \ \lor \ T \leq \tau \\
        0 &|\ \overline{L} \ \land \ T > \tau
        \end{cases}
        \\ \\
        P = PotentialFreeze \\
        F = FreezingFactor \\
        D = DegreeDayFactor \\
        \tau = DegreeDayThreshold \\
        T = AdjustedTemperature \\
        L = Land

    Example:

        >>> from hydpy.models.snow import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> numberzones(5)
        >>> land(True, True, True, True, False)
        >>> degreedaythreshold(0.0, 1.0, 2.0, 3.0, 3.0)
        >>> degreedayfactor(6.0)
        >>> freezingfactor(0.1)
        >>> factors.adjustedtemperature = 1.0
        >>> model.calc_potentialfreeze_v1()
        >>> fluxes.potentialfreeze
        potentialfreeze(0.0, 0.0, 0.3, 0.6, 0.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.Land,
        snow_control.DegreeDayThreshold,
        snow_control.DegreeDayFactor,
        snow_control.FreezingFactor,
    )
    REQUIREDSEQUENCES = (snow_factors.AdjustedTemperature,)
    RESULTSEQUENCES = (snow_fluxes.PotentialFreeze,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.numberzones):
            if con.land[k] and (fac.adjustedtemperature[k] < con.degreedaythreshold[k]):
                flu.potentialfreeze[k] = (
                    con.freezingfactor[k]
                    * con.degreedayfactor[k]
                    * (con.degreedaythreshold[k] - fac.adjustedtemperature[k])
                )
            else:
                flu.potentialfreeze[k] = 0.0


class Calc_ActualMelt_IceContent_WaterContent_V1(modeltools.Method):
    r"""Calculate the melting of the ice content within the snow layer and update both
    the snow layers' ice and the water content.

    Basic equations:
      .. math::
        I_{new} = I_{old} - A \\
        W_{new} = W_{old} + A \\
        A = min \big( P, \, I_{old} \big)
        \\ \\
        I = IceContent \\
        W = WaterContent \\
        A = ActualMelt \\
        P = PotentialMelt

    Example:

        The basic equation applies to all zones except those that represent water areas,
        for which |IceContent|, |WaterContent|, and |ActualMelt| are set to zero:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(7)
        >>> numberdivisions(2)
        >>> land(False, True, True, True, True, True, True)
        >>> control.degreedaythreshold = 2.0
        >>> fluxes.potentialmelt = 6.0
        >>> states.icecontent = [[0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 0.0],
        ...                     [0.0, 10.0, 10.0, 10.0, 10.0, 10.0, 0.0]]
        >>> states.watercontent = [[0.0], [2.0]]
        >>> model.calc_actualmelt_icecontent_watercontent_v1()
        >>> fluxes.actualmelt
        actualmelt([[0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 0.0],
                    [0.0, 6.0, 6.0, 6.0, 6.0, 6.0, 0.0]])
        >>> states.icecontent
        icecontent([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 4.0, 4.0, 4.0, 4.0, 4.0, 0.0]])
        >>> states.watercontent
        watercontent([[0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 0.0],
                      [0.0, 8.0, 8.0, 8.0, 8.0, 8.0, 2.0]])
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
    )
    REQUIREDSEQUENCES = (snow_fluxes.PotentialMelt,)
    UPDATEDSEQUENCES = (snow_states.WaterContent, snow_states.IceContent)
    RESULTSEQUENCES = (snow_fluxes.ActualMelt,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.numberzones):
            if con.land[k]:
                for c in range(con.numberdivisions):
                    flu.actualmelt[c, k] = min(
                        flu.potentialmelt[k], sta.icecontent[c, k]
                    )
                    sta.icecontent[c, k] -= flu.actualmelt[c, k]
                    sta.watercontent[c, k] += flu.actualmelt[c, k]
            else:
                for c in range(con.numberdivisions):
                    flu.actualmelt[c, k] = 0.0
                    sta.watercontent[c, k] = 0.0
                    sta.icecontent[c, k] = 0.0


class Calc_ActualFreeze_IceContent_WaterContent_V1(modeltools.Method):
    r"""Calculate refreezing of the water content within the snow layer and update both
    the snow layers' ice and the water content.

    Basic equations:
      .. math::
        I_{new} = I_{old} + A \\
        W_{new} = W_{old} - A \\
        A = min \big( P, \, W_{old} \big)
        \\ \\
        I = IceContent \\
        W = WaterContent \\
        A = ActualFreeze \\
        P = PotentialFreeze

    Example:

        The basic equation applies to all zones except those that represent water areas,
        for which |IceContent|, |WaterContent|, and |ActualFreeze| are set to zero:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(7)
        >>> numberdivisions(2)
        >>> land(False, True, True, True, True, True, True)
        >>> fluxes.potentialfreeze = 0.6
        >>> states.icecontent = [[0.0], [2.0]]
        >>> states.watercontent = [[0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0],
        ...                        [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]]
        >>> model.calc_actualfreeze_icecontent_watercontent_v1()
        >>> fluxes.actualfreeze
        actualfreeze([[0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0],
                      [0.0, 0.6, 0.6, 0.6, 0.6, 0.6, 0.0]])
        >>> states.icecontent
        icecontent([[0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0],
                    [0.0, 2.6, 2.6, 2.6, 2.6, 2.6, 2.0]])
        >>> states.watercontent
        watercontent([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                      [0.0, 0.4, 0.4, 0.4, 0.4, 0.4, 0.0]])
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
    )
    REQUIREDSEQUENCES = (snow_fluxes.PotentialFreeze,)
    UPDATEDSEQUENCES = (snow_states.WaterContent, snow_states.IceContent)
    RESULTSEQUENCES = (snow_fluxes.ActualFreeze,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.numberzones):
            if con.land[k]:
                for c in range(con.numberdivisions):
                    flu.actualfreeze[c, k] = min(
                        flu.potentialfreeze[k], sta.watercontent[c, k]
                    )
                    sta.icecontent[c, k] += flu.actualfreeze[c, k]
                    sta.watercontent[c, k] -= flu.actualfreeze[c, k]
            else:
                for c in range(con.numberdivisions):
                    flu.actualfreeze[c, k] = 0.0
                    sta.watercontent[c, k] = 0.0
                    sta.icecontent[c, k] = 0.0


class Calc_Release_WaterContent_V1(modeltools.Method):
    r"""Calculate the actual water release from the snow layer due to the exceedance of
    the snow layer's capacity for (liquid) water.

    Basic equations:
      .. math::
        W_{new} = W_{old} - R \\
        R = max(W - C \cdot I, \, 0)
        \\ \\
        W = WaterContent \\
        I = IceContent \\
        R = Release \\
        C = WaterCapacity

    Examples:


        We initialise one water and three land zones with an identical relative
        water-holding capacity of 20 %, different frozen water contents, and a uniform
        throughfall of 5 mm:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(4)
        >>> numberdivisions(1)
        >>> land(False, True, True, True)
        >>> watercapacity(0.2)
        >>> states.icecontent = 0.0, 10.0, 5.0, 0.0
        >>> fluxes.throughfall = 5.0

        When there is no (liquid) water content in the snow layer, no water can be
        released:

        >>> states.watercontent = 0.0
        >>> model.calc_release_watercontent_v1()
        >>> fluxes.release
        release(5.0, 0.0, 0.0, 0.0)
        >>> states.watercontent
        watercontent(0.0, 0.0, 0.0, 0.0)

        When there is a (liquid) water content in the snow layer, its release depends on
        the frozen water content.  Note that for water areas (first zone), for which the
        snow routine does not apply, throughfall is considered as release without any
        modifications:

        >>> states.watercontent = 5.0
        >>> model.calc_release_watercontent_v1()
        >>> fluxes.release
        release(5.0, 3.0, 4.0, 5.0)
        >>> states.watercontent
        watercontent(0.0, 2.0, 1.0, 0.0)

        For a relative water holding capacity of zero, the snow layer releases all
        liquid water immediately:

        >>> watercapacity(0.0)
        >>> states.watercontent = 5.0
        >>> model.calc_release_watercontent_v1()
        >>> fluxes.release
        release(5.0, 5.0, 5.0, 5.0)
        >>> states.watercontent
        watercontent(0.0, 0.0, 0.0, 0.0)

        In the above examples, we did not divide the zones into snow classes. If we do
        so, method |Calc_Release_WaterContent_V1| averages the water release of all
        snow classes of each zone:

        >>> numberdivisions(2)
        >>> watercapacity(0.0)
        >>> states.icecontent = 0.0, 10.0, 5.0, 0.0
        >>> states.watercontent = [[2.0], [3.0]]
        >>> model.calc_release_watercontent_v1()
        >>> fluxes.release
        release(5.0, 2.5, 2.5, 2.5)
        >>> states.watercontent
        watercontent([[0.0, 0.0, 0.0, 0.0],
                      [0.0, 0.0, 0.0, 0.0]])
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
        snow_control.WaterCapacity,
    )
    REQUIREDSEQUENCES = (snow_fluxes.Throughfall, snow_states.IceContent)
    UPDATEDSEQUENCES = (snow_states.WaterContent,)
    RESULTSEQUENCES = (snow_fluxes.Release,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.numberzones):
            flu.release[k] = 0.0
            if con.land[k]:
                for c in range(con.numberdivisions):
                    wc_old: float = sta.watercontent[c, k]
                    sta.watercontent[c, k] = min(
                        wc_old, con.watercapacity[k] * sta.icecontent[c, k]
                    )
                    flu.release[k] += (
                        wc_old - sta.watercontent[c, k]
                    ) / con.numberdivisions
            else:
                flu.release[k] = flu.throughfall[k]
                for c in range(con.numberdivisions):
                    sta.watercontent[c, k] = 0.0


class Calc_Snowpack_V1(modeltools.Method):
    r"""Calculate the total snow water equivalent.

    Basic equation:
      .. math::
        Snowpack = IceContent + WaterContent

    Example:

        The basic equation applies to all zones except those that represent water areas,
        for which |Snowpack| is set to zero:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> numberdivisions(2)
        >>> land(False, True, True)
        >>> states.watercontent = [[0.1, 0.2, 0.3], [0.6, 0.7, 0.8]]
        >>> states.icecontent = [[1.0, 2.0, 3.0], [6.0, 7.0, 8.0]]
        >>> model.calc_snowpack_v1()
        >>> factors.snowpack
        snowpack([[0.0, 2.2, 3.3],
                  [0.0, 7.7, 8.8]])
    """

    CONTROLPARAMETERS = (
        snow_control.NumberZones,
        snow_control.NumberDivisions,
        snow_control.Land,
    )
    REQUIREDSEQUENCES = (snow_states.IceContent, snow_states.WaterContent)
    RESULTSEQUENCES = (snow_factors.Snowpack,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.numberzones):
            if con.land[k]:
                for c in range(con.numberdivisions):
                    fac.snowpack[c, k] = sta.icecontent[c, k] + sta.watercontent[c, k]
            else:
                for c in range(con.numberdivisions):
                    fac.snowpack[c, k] = 0.0


class Process_SnowRoutine_V1(modeltools.Method):
    """Interface method that applies the complete application model by executing all
    "run methods"."""

    @staticmethod
    def __call__(model: modeltools.AdHocModel, /) -> None:
        model.run()


class Get_Release_V1(modeltools.Method):
    """Get the selected zone's meltwater or throughfall release.

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(2)
        >>> fluxes.release = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_release_v1(0))
        2.0
        >>> round_(model.get_release_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (snow_fluxes.Release,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int, /) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.release[k]


class Get_SnowCover_V1(modeltools.Method):
    """Get the selected zone's current snow cover degree.

    Examples:

        Each snow class with a non-zero amount of snow counts as wholly covered:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> numberdivisions(4)
        >>> states.icecontent = [[0.0, 0.0, 1.0],
        ...                      [0.0, 1.0, 1.0],
        ...                      [0.0, 1.0, 1.0],
        ...                      [0.0, 1.0, 1.0]]
        >>> model.get_snowcover_v1(0)
        0.0
        >>> model.get_snowcover_v1(1)
        0.75
        >>> model.get_snowcover_v1(2)
        1.0
    """

    CONTROLPARAMETERS = (snow_control.NumberDivisions,)
    REQUIREDSEQUENCES = (snow_states.IceContent,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int, /) -> float:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        snowcover: float = 0.0
        for d in range(con.numberdivisions):
            if sta.icecontent[d, k] > 0.0:
                snowcover += 1.0
        return snowcover / con.numberdivisions


class Computes_SnowEvaporation_V1(modeltools.Method):
    """Report that the snow routine does not calculate snow evaporation.

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> assert not model.computes_snowevaporation_v1()
    """

    @staticmethod
    def __call__(model: modeltools.Model) -> bool:
        return False


class Calc_PLayer_V1(modeltools.Method):
    r"""Adjust the precipitation to the altitude for the snow layers according to
    :cite:t:`ref-Valery`.

    Basic equations:

      .. math::
        L_i^* = P \cdot \begin{cases}
        e^{G\cdot \big(Z_i - \overline{Z}\big)} &|\ Z_i \leq T \\
        e^{G\cdot max\big(T- \overline{Z}, \,0\big)} &|\ Z_i > T
        \end{cases}
        \\
        L_i = L_i^* \cdot \frac{P}{\sum_{i=1}^{N} A_i \cdot L_i^*}
        \\ \\
        L = PLayer \\
        G = GradP \\
        Z = ZLayers \\
        \overline{Z} = ZMean \\
        T = ZThreshold  \\
        N = NLayers \\
        A = LayerArea

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> layerarea(0.2)
        >>> gradp(0.00041)
        >>> inputs.p = 10.0

        The threshold parameter |ZThreshold| is usually fixed to 4000 m:

        >>> fixed.zthreshold
        zthreshold(4000.0)

        If all layers lie below the threshold, their precipitation values become
        adjusted by the same equation:

        >>> zlayers(2199.0, 2599.0, 2999.0, 3399.0, 3799.0)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(2999.0)
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(7.013551, 8.263467, 9.736135, 11.471253, 13.515595)

        The total precipitation volume stays intact:

        >>> from hydpy import round_
        >>> round_(fluxes.player.average_values())
        10.0

        Layers above the threshold altitude are only adjusted with respect to the
        threshold:

        >>> zlayers(3199.0, 3599.0, 3999.0, 4399.0, 4799.0)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(3999.0)
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(7.881562, 9.28617, 10.941098, 10.945585, 10.945585)
        >>> round_(fluxes.player.average_values())
        10.0

        If the average layer altitude exceeds the threshold, the precipitation values
        of the upper layers are not directly adjusted.  Still, |Calc_PLayer_V1|
        indirectly increases them by decreasing the lower layers' precipitation and
        subsequently adjusting all layers' precipitation sum back to the original
        volume:

        >>> zlayers(3201.0, 3601.0, 4001.0, 4401.0, 4801.0)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(4001.0)
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(7.882977, 9.287837, 10.943062, 10.943062, 10.943062)
        >>> round_(fluxes.player.average_values())
        10.0

        If all layers lie above the threshold, all get the same (original)
        precipitation value:

        >>> zlayers(4201.0, 4601.0, 5001.0, 5401.0, 5801.0)
        >>> derived.zmean.update()
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(10.0, 10.0, 10.0, 10.0, 10.0)

        The last example demonstrates that the water balance remains intact for layers
        with different sizes:

        >>> zlayers(3201.0, 3601.0, 4001.0, 4401.0, 4801.0)
        >>> control.layerarea(0.3, 0.2, 0.2, 0.2, 0.1)
        >>> derived.zmean.update()
        >>> model.calc_player_v1()
        >>> fluxes.player
        player(8.1337, 9.583241, 11.286484, 11.286484, 11.286484)
        >>> round_(fluxes.player.average_values())
        10.0
    """

    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.LayerArea,
        snow_control.GradP,
    )
    DERIVEDPARAMETERS = (snow_derived.ZMean,)
    FIXEDPARAMETERS = (snow_fixed.ZThreshold,)
    REQUIREDSEQUENCES = (snow_inputs.P,)
    RESULTSEQUENCES = (snow_fluxes.PLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        p: float = 0.0
        for k in range(con.nlayers):
            if con.zlayers[k] <= fix.zthreshold:
                delta: float = con.zlayers[k] - der.zmean
            else:
                delta = max(fix.zthreshold - der.zmean, 0.0)
            flu.player[k] = inp.p * modelutils.exp(con.gradp * delta)
            p += flu.player[k] * con.layerarea[k]

        if p > 0.0:
            for k in range(con.nlayers):
                flu.player[k] = flu.player[k] / p * inp.p


class Return_T_V1(modeltools.Method):
    r"""Return the altitude-adjusted temperature.

    Basic equation:
      :math:`f(t, \, k, \, g) = t + (ZMean - ZLayer_k) \cdot g / 100`

    Examples:

        The adjustment depends on the selected layer's altitude relative to the average
        altitude and the current-day temperature gradient:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmean(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()

        >>> model.idx_sim = pub.timegrids.init["2000-01-01"]
        >>> round_(model.return_t_v1(5.0, 0, gradtmean.values))
        6.0
        >>> round_(model.return_t_v1(5.0, 1, gradtmean.values))
        4.0

        >>> model.idx_sim = pub.timegrids.init["2000-12-31"]
        >>> round_(model.return_t_v1(5.0, 0, gradtmean.values))
        7.0
        >>> round_(model.return_t_v1(5.0, 1, gradtmean.values))
        3.0
    """

    CONTROLPARAMETERS = (snow_control.ZLayers,)
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)

    @staticmethod
    def __call__(model: modeltools.Model, t: float, k: int, g: VectorFloat, /) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess

        return t + (der.zmean - con.zlayers[k]) * g[der.doy[model.idx_sim]] / 100.0


class Calc_TLayer_V1(modeltools.Method):
    r"""Calculate the mean temperature for each snow layer based on method
    |Return_T_V1|.

    Basic equation:
      :math:`TLayer_k = f_{Return\_T\_V1}(T, \, k, \, GradTMean)`

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmean(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()
        >>> inputs.t = 5.0

        >>> model.idx_sim = 0
        >>> model.calc_tlayer_v1()
        >>> factors.tlayer
        tlayer(6.0, 4.0)

        >>> model.idx_sim = 365
        >>> model.calc_tlayer_v1()
        >>> factors.tlayer
        tlayer(7.0, 3.0)
    """

    SUBMETHODS = (Return_T_V1,)
    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.GradTMean,
    )
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)
    REQUIREDSEQUENCES = (snow_inputs.T,)
    RESULTSEQUENCES = (snow_factors.TLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            fac.tlayer[k] = model.return_t_v1(inp.t, k, con.gradtmean)


class Calc_TMinLayer_V1(modeltools.Method):
    r"""Calculate the minimum temperature for each snow layer based on method
    |Return_T_V1|.

    Basic equation:
      :math:`TMinLayer_k = f_{Return\_T\_V1}(TMin, \, k, \, GradTMin)`

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmin(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()
        >>> inputs.tmin = 5.0

        >>> model.idx_sim = 0
        >>> model.calc_tminlayer_v1()
        >>> factors.tminlayer
        tminlayer(6.0, 4.0)

        >>> model.idx_sim = 365
        >>> model.calc_tminlayer_v1()
        >>> factors.tminlayer
        tminlayer(7.0, 3.0)
    """

    SUBMETHODS = (Return_T_V1,)
    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.GradTMin,
    )
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)
    REQUIREDSEQUENCES = (snow_inputs.TMin,)
    RESULTSEQUENCES = (snow_factors.TMinLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            fac.tminlayer[k] = model.return_t_v1(inp.tmin, k, con.gradtmin)


class Calc_TMaxLayer_V1(modeltools.Method):
    r"""Calculate the maximum temperature for each snow layer based on method
    |Return_T_V1|.

    Basic equation:
      :math:`TMaxLayer_k = f_{Return\_T\_V1}(TMax, \, k, \, GradTMax)`

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> zlayers(100.0, 500.0)
        >>> import numpy
        >>> gradtmax(numpy.linspace(0.5, 1.0, 366))
        >>> derived.zmean(300.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> derived.doy.update()
        >>> inputs.tmax = 5.0

        >>> model.idx_sim = 0
        >>> model.calc_tmaxlayer_v1()
        >>> factors.tmaxlayer
        tmaxlayer(6.0, 4.0)

        >>> model.idx_sim = 365
        >>> model.calc_tmaxlayer_v1()
        >>> factors.tmaxlayer
        tmaxlayer(7.0, 3.0)
    """

    SUBMETHODS = (Return_T_V1,)
    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.ZLayers,
        snow_control.GradTMax,
    )
    DERIVEDPARAMETERS = (snow_derived.DOY, snow_derived.ZMean)
    REQUIREDSEQUENCES = (snow_inputs.TMax,)
    RESULTSEQUENCES = (snow_factors.TMaxLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            fac.tmaxlayer[k] = model.return_t_v1(inp.tmax, k, con.gradtmax)


class Calc_SolidFractionPrecipitation_V1(modeltools.Method):
    r"""Calculate the solid precipitation fraction for each snow layer according to
    :cite:t:`ref-USACE1956`.

    Basic equation:
      .. math::
        F = min \left( max \left( \frac{R - T}{R - S}, \, 0 \right), \, 1 \right)
        \\ \\
        F = SolidFractionPrecipitation \\
        T = TLayer \\
        R = TThreshRain \\
        S = TThreshSnow

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(7)
        >>> factors.tlayer = -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0
        >>> model.calc_solidfractionprecipitation_v1()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    FIXEDPARAMETERS = (snow_fixed.TThreshSnow, snow_fixed.TThreshRain)
    REQUIREDSEQUENCES = (snow_factors.TLayer,)
    RESULTSEQUENCES = (snow_factors.SolidFractionPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            r: float = fix.tthreshrain
            s: float = fix.tthreshsnow
            t: float = fac.tlayer[k]
            fac.solidfractionprecipitation[k] = min(max((r - t) / (r - s), 0.0), 1.0)


class Calc_SolidFractionPrecipitation_V2(modeltools.Method):
    r"""Calculate the solid precipitation fraction for each snow layer according to
    :cite:t:`ref-Turcotte2007` and :cite:t:`ref-USACE1956`.

    Basic equation:
      .. math::
        F = \begin{cases}
        min \left( max \left( 1 - \frac{X}{X - N}, \, 0 \right), \, 1 \right)
        &|\ Z < 1500 \\
        min \left( max \left( \frac{R - T}{R - S}, \, 0 \right), \, 1 \right)
        &|\ Z \geq 1500 \end{cases}
        \\ \\
        F = SolidFractionPrecipitation \\
        Z = ZMean \\
        X = TMaxLayer \\
        N = TMinLayer \\
        T = TLayer \\
        R = TThreshRain \\
        S = TThreshSnow

    Examples:

        For catchments with an average elevation below 1500 m, the (daily) solid
        precipitation fraction is determined by the time with an air temperature below
        0°C, which is estimated based on |TMaxLayer| and |TMinLayer|:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(7)
        >>> derived.zmean(1499.0)
        >>> factors.tminlayer = -2.0, -2.0, -2.0, -2.0, -1.0, 0.0, 1.0
        >>> factors.tmaxlayer = -1.0, 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.666667, 0.5, 0.333333, 0.0, 0.0)


        Swapping the minimum and maximum values (which might occur in applications due
        to input data errors or problematic altitude adjustments) yields the same
        results:

        >>> factors.tminlayer = -1.0, 0.0, 1.0, 2.0, 2.0, 2.0, 2.0
        >>> factors.tmaxlayer = -2.0, -2.0, -2.0, -2.0, -1.0, 0.0, 1.0
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.666667, 0.5, 0.333333, 0.0, 0.0)

        Identical minimum and maximum temperatures also pose no problem:

        >>> factors.tminlayer = -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0
        >>> factors.tmaxlayer = -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0)

        For higher catchments, the usual linear interpolation approach between a
        minimum (|TThreshSnow|) and a maximum (|TThreshRain|) temperature threshold
        applies (as when using |Calc_SolidFractionPrecipitation_V1|):

        >>> factors.tlayer = -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0
        >>> derived.zmean(1500.0)
        >>> model.calc_solidfractionprecipitation_v2()
        >>> factors.solidfractionprecipitation
        solidfractionprecipitation(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    DERIVEDPARAMETERS = (snow_derived.ZMean,)
    FIXEDPARAMETERS = (snow_fixed.TThreshSnow, snow_fixed.TThreshRain)
    REQUIREDSEQUENCES = (
        snow_factors.TLayer,
        snow_factors.TMinLayer,
        snow_factors.TMaxLayer,
    )
    RESULTSEQUENCES = (snow_factors.SolidFractionPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess

        for k in range(con.nlayers):
            if der.zmean < 1500.0:
                x: float = fac.tmaxlayer[k]
                n: float = fac.tminlayer[k]
                if n < x:
                    w: float = n / (n - x)
                elif n > x:
                    w = x / (x - n)
                elif x < 0.0:
                    w = 1.0
                elif x == 0.0:
                    w = 0.5
                else:
                    w = 0.0
            else:
                r: float = fix.tthreshrain
                s: float = fix.tthreshsnow
                t: float = fac.tlayer[k]
                w = (r - t) / (r - s)
            fac.solidfractionprecipitation[k] = min(max(w, 0.0), 1.0)


class Calc_PRainLayer_V1(modeltools.Method):
    r"""Calculate the liquid part of precipitation :cite:p:`ref-USACE1956`.

    Basic equation:
      :math:`PRainLayer = (1 - SolidFractionPrecipitation) \cdot PLayer`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> fluxes.player = 0.0, 4.0
        >>> factors.solidfractionprecipitation = 0.25
        >>> model.calc_prainlayer()
        >>> fluxes.prainlayer
        prainlayer(0.0, 3.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_factors.SolidFractionPrecipitation, snow_fluxes.PLayer)
    RESULTSEQUENCES = (snow_fluxes.PRainLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            f: float = fac.solidfractionprecipitation[k]
            flu.prainlayer[k] = (1.0 - f) * flu.player[k]


class Calc_PSnowLayer_V1(modeltools.Method):
    r"""Calculate the frozen part of precipitation.

    Basic equation:
      :math:`PSnowLayer = SolidFractionPrecipitation \cdot PLayer`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> fluxes.player = 0.0, 4.0
        >>> factors.solidfractionprecipitation = 0.25
        >>> model.calc_psnowlayer()
        >>> fluxes.psnowlayer
        psnowlayer(0.0, 1.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_factors.SolidFractionPrecipitation, snow_fluxes.PLayer)
    RESULTSEQUENCES = (snow_fluxes.PSnowLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            flu.psnowlayer[k] = fac.solidfractionprecipitation[k] * flu.player[k]


class Update_G_V1(modeltools.Method):
    """Add the snowfall to each layer's snow pack.

    Basic equation:
      :math:`G_{new} = G_{old} + PSnowLayer`

    Examples:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nlayers(3)
        >>> fluxes.psnowlayer = 0.0, 1.0, 1.0
        >>> states.g = 1.0, 1.0, 0.0
        >>> model.update_g_v1()
        >>> states.g
        g(1.0, 2.0, 1.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_fluxes.PSnowLayer,)
    UPDATEDSEQUENCES = (snow_states.G,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.g[k] += flu.psnowlayer[k]


class Calc_ETG_V1(modeltools.Method):
    r"""Update the thermal state of each snow layer.

    Basic equation:
      .. math::
        E_{new} = min(C \cdot E_{old} + (1 - C) \cdot T, \, 0)
        \\ \\
        E = ETG \\
        C = CN1 \\
        T = TLayer

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(3)
        >>> cn1(0.75)
        >>> factors.tlayer = 1.0, 0.0, -1.0
        >>> states.etg = -1.0, 0.0, 1.0
        >>> model.calc_etg_v1()
        >>> states.etg
        etg(-0.5, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.CN1)
    REQUIREDSEQUENCES = (snow_factors.TLayer,)
    UPDATEDSEQUENCES = (snow_states.ETG,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.etg[k] = min(
                con.cn1 * sta.etg[k] + (1.0 - con.cn1) * fac.tlayer[k], 0.0
            )


class Calc_PotMelt_V1(modeltools.Method):
    r"""Calculate the potential melt for each snow layer.

    Basic equation:
      .. math::
        P = \begin{cases}
        min \big(G, \, C \cdot max(T, \, 0) \big) &|\ E = 0
        \\
        0 &|\ E < 0
        \end{cases}
        \\ \\
        P = PotMelt \\
        E = ETG \\
        C = CN2 \\
        T = TLayer

    Example:

        |Calc_PotMelt_V1| extends the classical day degree with a restriction that
        prevents any melting as long as the snowpack's thermal state is below 0°C:

        >>> from hydpy.models.snow import *
        >>> from hydpy import pub
        >>> simulationstep("1d")
        >>> parameterstep("12h")
        >>> nlayers(5)
        >>> cn2(1.0)
        >>> factors.tlayer = 1.0, -1.0, 1.0, 1.0, 1.0
        >>> states.g = 1.0, 1.0, 1.0, 2.0, 3.0
        >>> states.etg = -1.0, 0.0, 0.0, 0.0, 0.0
        >>> model.calc_potmelt_v1()
        >>> fluxes.potmelt
        potmelt(0.0, 0.0, 1.0, 2.0, 2.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.CN2)
    REQUIREDSEQUENCES = (snow_factors.TLayer, snow_states.ETG, snow_states.G)
    RESULTSEQUENCES = (snow_fluxes.PotMelt,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            if sta.etg[k] < 0.0:
                flu.potmelt[k] = 0.0
            else:
                flu.potmelt[k] = min(sta.g[k], max(con.cn2 * fac.tlayer[k], 0.0))


class Calc_GRatio_V1(modeltools.Method):
    r"""Calculate the fraction of the snow-covered area for each snow layer.

    Basic equation:
      :math:`GRatio = min(G / GThresh, \, 1)`

    Example:

        We set |CN4|, used to derive |GThresh|, to 0.9, which corresponds to the
        configuration of the original CemaNeige model:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(4)
        >>> cn4(0.9)
        >>> meanansolidprecip(100.0, 100.0, 100.0, 200.0)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(90.0, 90.0, 90.0, 180.0)
        >>> states.g = 67.5, 90.0, 90.1, 90.0
        >>> model.calc_gratio_v1()
        >>> states.gratio
        gratio(0.75, 1.0, 1.0, 0.5)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    DERIVEDPARAMETERS = (snow_derived.GThresh,)
    REQUIREDSEQUENCES = (snow_states.G,)
    UPDATEDSEQUENCES = (snow_states.GRatio,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.gratio[k] = min(sta.g[k] / der.gthresh[k], 1.0)


class Update_GRatio_GLocalMax_V1(modeltools.Method):
    r"""Calculate the fraction of the snow-covered area for each snow layer and update
    |GLocalMax| before calculating the snowmelt.

    Basic equations:
      .. math::
        L_{new} = min(G, \, L_{old}) \\
        R = min(G / L_{new}, \, 1.0)
        \\ \\
        L = GLocalMax \\
        R = GRatio

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> meanansolidprecip(80.0)
        >>> cn4(0.9)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(72.0)
        >>> states.g = 30.0, 20.0, 12.0, 80.0, 50.0
        >>> states.gratio = 0.0, 0.2, 1.0, 1.0, 1.0
        >>> fluxes.potmelt = 10.0, 10.0, 10.0, 0.0, 0.0
        >>> logs.glocalmax = 40.0, 30.0, 20.0, 10.0, 0.0
        >>> hysteresis(True)
        >>> model.update_gratio_glocalmax_v1()
        >>> states.gratio
        gratio(0.75, 0.666667, 1.0, 1.0, 1.0)
        >>> logs.glocalmax
        glocalmax(40.0, 30.0, 12.0, 10.0, 72.0)

        If we switch off hysteresis, |GRatio| will dependent solely on |GThresh| and
        |GLocalMax| is always set to zero:

        >>> hysteresis(False)
        >>> model.update_gratio_glocalmax_v1()
        >>> states.gratio
        gratio(0.416667, 0.277778, 0.166667, 1.0, 0.694444)
        >>> logs.glocalmax
        glocalmax(0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.Hysteresis)
    DERIVEDPARAMETERS = (snow_derived.GThresh,)
    REQUIREDSEQUENCES = (snow_states.G, snow_fluxes.PotMelt)
    UPDATEDSEQUENCES = (snow_states.GRatio, snow_logs.GLocalMax)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            if con.hysteresis:
                if log.glocalmax[k] == 0.0:
                    log.glocalmax[k] = der.gthresh[k]
                if flu.potmelt[k] > 0.0:
                    if sta.gratio[k] == 1.0:
                        log.glocalmax[k] = min(sta.g[k], log.glocalmax[k])
                    sta.gratio[k] = min(sta.g[k] / log.glocalmax[k], 1.0)
            else:
                sta.gratio[k] = min(sta.g[k] / der.gthresh[k], 1.0)
                log.glocalmax[k] = 0.0


class Calc_Melt_V1(modeltools.Method):
    r"""Calculate the actual snow melt for each layer.

    Basic equation:
      .. math::
        M = P \cdot ((1 - N) \cdot R + N)
        \\ \\
        M = Melt \\
        P = PotMelt \\
        N = MinMelt \\
        R = GRatio

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> fluxes.potmelt = 0.0, 0.5, 1.0, 1.5, 2.0
        >>> states.gratio = 0.0, 0.25, 0.5, 0.75, 1.0
        >>> states.g = 0.0, 0.5, 1.0, 1.5, 2.0
        >>> model.calc_melt_v1()
        >>> fluxes.melt
        melt(0.0, 0.1625, 0.55, 1.1625, 2.0)

        In the original formulation of the CemaNeige model, the basic equation
        typically results in an exponential decrease in snow cover because |PotMelt|
        never exceeds |G| and |GRatio| converges to zero during snow cover depletion.
        To provide an opportunity to avoid infinitely thin snow layers in summer, we
        introduced the fixed parameter |MinG|, which defines the amount of snow below
        which |Melt| equals |PotMelt|:

        >>> fixed.ming(1.0)
        >>> model.calc_melt_v1()
        >>> fluxes.melt
        melt(0.0, 0.5, 0.55, 1.1625, 2.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    FIXEDPARAMETERS = (snow_fixed.MinMelt, snow_fixed.MinG)
    REQUIREDSEQUENCES = (snow_fluxes.PotMelt, snow_states.GRatio, snow_states.G)
    RESULTSEQUENCES = (snow_fluxes.Melt,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            flu.melt[k] = flu.potmelt[k]
            if sta.g[k] >= fix.ming:
                flu.melt[k] *= (1.0 - fix.minmelt) * sta.gratio[k] + fix.minmelt


class Update_G_V2(modeltools.Method):
    """Remove the snowmelt from the snowpack.

    Basic equation:
      :math:`G_{new} = G_{old} - Melt`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(4)
        >>> fluxes.melt = 0.0, 0.2, 0.2, 0.2
        >>> states.g = 0.0, 0.2, 0.4, 0.6
        >>> model.update_g_v2()
        >>> states.g
        g(0.0, 0.0, 0.2, 0.4)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_fluxes.Melt,)
    UPDATEDSEQUENCES = (snow_states.G,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nlayers):
            sta.g[k] -= flu.melt[k]


class Update_GRatio_GLocalMax_V2(modeltools.Method):
    r"""Calculate the fraction of the snow-covered area for each snow layer and update
    |GLocalMax| after calculating the snowmelt.

    Basic equation:

      .. math::
        R_{new}= \begin{cases}
        min \left( R_{old} + \Delta / C, \, 1 \right) &|\ \Delta > 0 \\
        min \left( G / L, \, 1 \right) &|\ \Delta < 0
        \end{cases}
        \\ \\
        R = GRatio \\
        \Delta = PSnowLayer - Melt \\
        C = CN3 \\
        L = GLocalMax

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> cn3(3.0)
        >>> cn4(0.2)
        >>> meanansolidprecip(100.0)
        >>> derived.gthresh.update()
        >>> fluxes.psnowlayer = 0.0, 1.0, 2.0, 3.0, 4.0
        >>> fluxes.melt = 0.0, 0.0, 3.0, 2.0, 2.0
        >>> states.g = 10.0, 20.0, 30.0, 40.0, 50.0
        >>> states.gratio = 0.1, 0.5, 0.8, 0.2, 0.4
        >>> logs.glocalmax = 10.0

        If |Hysteresis| is deactivated, |Update_GRatio_GLocalMax_V2| has no effect:

        >>> hysteresis(False)
        >>> model.update_gratio_glocalmax_v2()
        >>> states.gratio
        gratio(0.1, 0.5, 0.8, 0.2, 0.4)
        >>> logs.glocalmax
        glocalmax(10.0, 10.0, 10.0, 10.0, 10.0)

        After activating |Hysteresis|, |Update_GRatio_GLocalMax_V2| updates |GRatio|
        and |GLocalMax| differently depending on whether the snowpack is increasing or
        decreasing:

        >>> hysteresis(True)
        >>> model.update_gratio_glocalmax_v2()
        >>> states.gratio
        gratio(0.1, 0.833333, 1.0, 0.533333, 1.0)
        >>> logs.glocalmax
        glocalmax(10.0, 10.0, 10.0, 10.0, 20.0)
    """

    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.Hysteresis,
        snow_control.CN3,
    )
    DERIVEDPARAMETERS = (snow_derived.GThresh,)
    REQUIREDSEQUENCES = (snow_fluxes.Melt, snow_fluxes.PSnowLayer, snow_states.G)
    UPDATEDSEQUENCES = (snow_states.GRatio, snow_logs.GLocalMax)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess

        if con.hysteresis:
            for k in range(con.nlayers):
                dg: float = flu.psnowlayer[k] - flu.melt[k]
                if dg > 0.0:
                    sta.gratio[k] = min(sta.gratio[k] + dg / con.cn3, 1.0)
                    if sta.gratio[k] == 1.0:
                        log.glocalmax[k] = der.gthresh[k]
                elif dg < 0.0:
                    sta.gratio[k] = min(sta.g[k] / log.glocalmax[k], 1.0)


class Calc_PNetLayer_V1(modeltools.Method):
    """Sum the rainfall and the actual snow melt for each layer.

    Basic equation:
      :math:`PNetLayer = PRainLayer + Melt`

    Example:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(2)
    >>> fluxes.prainlayer = 1.0, 2.0
    >>> fluxes.melt = 3.0, 4.0
    >>> model.calc_pnetlayer_v1()
    >>> fluxes.pnetlayer
    pnetlayer(4.0, 6.0)
    """

    CONTROLPARAMETERS = (snow_control.NLayers,)
    REQUIREDSEQUENCES = (snow_fluxes.PRainLayer, snow_fluxes.Melt)
    RESULTSEQUENCES = (snow_fluxes.PNetLayer,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nlayers):
            flu.pnetlayer[k] = flu.prainlayer[k] + flu.melt[k]


class Calc_PNet_V1(modeltools.Method):
    r"""Calculate the catchment's average net rainfall.

    Basic equation:
      :math:`PNet = \sum_{i=1}^{NLayers} LayerArea_i \cdot PRainLayer_i`

    Example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(2)
        >>> layerarea(0.2, 0.8)
        >>> fluxes.pnetlayer = 2.0, 1.0
        >>> model.calc_pnet_v1()
        >>> fluxes.pnet
        pnet(1.2)
        >>> from hydpy import round_
        >>> round_(fluxes.pnetlayer.average_values())
        1.2
    """

    CONTROLPARAMETERS = (snow_control.NLayers, snow_control.LayerArea)
    REQUIREDSEQUENCES = (snow_fluxes.PNetLayer,)
    RESULTSEQUENCES = (snow_fluxes.PNet,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.pnet = 0.0
        for k in range(con.nlayers):
            flu.pnet += flu.pnetlayer[k] * con.layerarea[k]


class Model(modeltools.AdHocModel):
    """|snow.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Snow")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        Calc_Throughfall_ThroughfallModel_V1,
        Calc_Throughfall_ThroughfallModel_V2,
        Return_T_V1,
    )
    RUN_METHODS = (
        Calc_Throughfall_V1,
        Calc_AdjustedTemperature_V1,
        Calc_RainSnowFraction_V1,
        Calc_IceContent_WaterContent_V1,
        Calc_IceLoss_WaterLoss_IceContent_WaterContent_V1,
        Calc_IceGain_WaterGain_IceContent_WaterContent_V1,
        Calc_MeltingFactor_V1,
        Calc_PotentialMelt_V1,
        Calc_PotentialFreeze_V1,
        Calc_ActualMelt_IceContent_WaterContent_V1,
        Calc_ActualFreeze_IceContent_WaterContent_V1,
        Calc_Release_WaterContent_V1,
        Calc_Snowpack_V1,
        Calc_PLayer_V1,
        Calc_TLayer_V1,
        Calc_TMinLayer_V1,
        Calc_TMaxLayer_V1,
        Calc_SolidFractionPrecipitation_V1,
        Calc_SolidFractionPrecipitation_V2,
        Calc_PRainLayer_V1,
        Calc_PSnowLayer_V1,
        Update_G_V1,
        Calc_ETG_V1,
        Calc_PotMelt_V1,
        Calc_GRatio_V1,
        Update_GRatio_GLocalMax_V1,
        Calc_Melt_V1,
        Update_G_V2,
        Update_GRatio_GLocalMax_V2,
        Calc_PNetLayer_V1,
        Calc_PNet_V1,
    )
    INTERFACE_METHODS = (
        Process_SnowRoutine_V1,
        Get_Release_V1,
        Get_SnowCover_V1,
        Computes_SnowEvaporation_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    throughfallmodel = modeltools.SubmodelProperty(
        throughfallinterfaces.ThroughfallModel_V1,
        throughfallinterfaces.ThroughfallModel_V2,
    )
    throughfallmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    throughfallmodel_typeid = modeltools.SubmodelTypeIDProperty()


class BaseModel(modeltools.AdHocModel):
    """Base model for CemaNeige-like layered models."""

    def prepare_layers(self, *, hypsodata: VectorInputFloat) -> None:
        """Set the control parameters |LayerArea| and |ZLayers| based on hypsometric
        data.

        Method |BaseModel.prepare_layers| requires the percentiles of the catchment's
        elevation distribution in meters, prefixed by the minimum and suffixed by the
        maximum elevation, which makes exactly 101 data points:

        >>> from hydpy.models.snow_cn import *
        >>> parameterstep()
        >>> model.prepare_layers(hypsodata=[0.0])
        Traceback (most recent call last):
        ...
        ValueError: Method `prepare_layers` requires a vector of 101 hypsometric data \
points but 1 value is given.

        If 100 is a multiple of the number of layers, |BaseModel.prepare_layers| can
        select the correct data directly:

        >>> nlayers(5)
        >>> hypsodata = [
        ...     286.0, 309.0, 320.0, 327.0, 333.0, 338.0, 342.0, 347.0, 351.0, 356.0,
        ...     360.0, 365.0, 369.0, 373.0, 378.0, 382.0, 387.0, 393.0, 399.0, 405.0,
        ...     411.0, 417.0, 423.0, 428.0, 434.0, 439.0, 443.0, 448.0, 453.0, 458.0,
        ...     463.0, 469.0, 474.0, 480.0, 485.0, 491.0, 496.0, 501.0, 507.0, 513.0,
        ...     519.0, 524.0, 530.0, 536.0, 542.0, 548.0, 554.0, 560.0, 566.0, 571.0,
        ...     577.0, 583.0, 590.0, 596.0, 603.0, 609.0, 615.0, 622.0, 629.0, 636.0,
        ...     642.0, 649.0, 656.0, 663.0, 669.0, 677.0, 684.0, 691.0, 698.0, 706.0,
        ...     714.0, 722.0, 730.0, 738.0, 746.0, 754.0, 762.0, 770.0, 777.0, 786.0,
        ...     797.0, 808.0, 819.0, 829.0, 841.0, 852.0, 863.0, 875.0, 887.0, 901.0,
        ...     916.0, 934.0, 952.0, 972.0, 994.0, 1012.0, 1029.0, 10540.0, 10800.0,
        ...     11250.0, 12780.0
        ... ]
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.2)
        >>> zlayers
        zlayers(360.0, 463.0, 577.0, 714.0, 916.0)

        Otherwise, it still selects some of the given values and thereby needs to
        trick a little, which results in some deviations from the original elevation
        distribution:

        >>> nlayers(7)
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.142857)
        >>> zlayers
        zlayers(347.0, 423.0, 501.0, 583.0, 677.0, 786.0, 972.0)


        >>> nlayers(70)
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.014286)
        >>> zlayers
        zlayers(286.0, 320.0, 333.0, 342.0, 351.0, 360.0, 369.0, 378.0, 387.0,
                399.0, 411.0, 423.0, 434.0, 443.0, 453.0, 463.0, 474.0, 485.0,
                496.0, 507.0, 519.0, 530.0, 542.0, 554.0, 566.0, 577.0, 590.0,
                603.0, 615.0, 629.0, 642.0, 649.0, 656.0, 663.0, 669.0, 677.0,
                684.0, 691.0, 698.0, 706.0, 714.0, 722.0, 730.0, 738.0, 746.0,
                754.0, 762.0, 770.0, 777.0, 786.0, 797.0, 808.0, 819.0, 829.0,
                841.0, 852.0, 863.0, 875.0, 887.0, 901.0, 916.0, 934.0, 952.0,
                972.0, 994.0, 1012.0, 1029.0, 10540.0, 10800.0, 11250.0)

        Due to this selection mechanism (without interpolation), the highest number of
        supported layers is 100:

        >>> nlayers(100)
        >>> model.prepare_layers(hypsodata=hypsodata)
        >>> layerarea
        layerarea(0.01)
        >>> assert zlayers == hypsodata[:-1]

        >>> nlayers(101)
        >>> model.prepare_layers(hypsodata=hypsodata)
        Traceback (most recent call last):
        ...
        ValueError: Method `prepare_layers` works for at most 100 layers, but the \
value of parameter `nlayers` of element `?` is set to 101.
        """

        if len(hypsodata) != 101:
            p = inflect.engine()
            n = len(hypsodata)
            raise ValueError(
                f"Method `prepare_layers` requires a vector of 101 hypsometric data "
                f"points but {len(hypsodata)} {p.plural_noun('value', n)} "
                f"{p.plural_verb('is', n)} given."
            )

        control = self.parameters.control

        if control.nlayers > 100:
            raise ValueError(
                f"Method `prepare_layers` works for at most 100 layers, but the value "
                f"of parameter {objecttools.elementphrase(control.nlayers)} is set to "
                f"{control.nlayers.value}."
            )

        control.layerarea(1.0 / control.nlayers)
        width = 100 // control.nlayers
        rest = 100 % control.nlayers
        i0 = 0
        control.zlayers(numpy.nan)
        for i1 in range(control.nlayers.value):
            if rest == 0:
                adjusted_width = width
            else:
                adjusted_width = width + 1
                rest -= 1
            if adjusted_width <= 2:
                control.zlayers.values[i1] = hypsodata[i0]
            else:
                control.zlayers.values[i1] = hypsodata[int(i0 + adjusted_width / 2.0)]
            i0 = i0 + adjusted_width


class Sub_SnowModel(modeltools.AdHocModel):
    """Base class for submodels that comply with the submodel interface
    |SnowModel_V1|."""

    @staticmethod
    @contextlib.contextmanager
    def share_configuration(
        sharable_configuration: SharableConfiguration,
    ) -> Generator[None, None, None]:
        """Share class-level configurations between a main model and its snow submodel
        temporarily.

        >>> from hydpy.core.parametertools import Constants, NameParameter, Parameter
        >>> consts = Constants(GRASS=1, TREES=3, WATER=2)
        >>> class LandType(NameParameter):
        ...     __name__ = "temp.py"
        ...     constants = consts
        >>> class Subarea(Parameter):
        ...     ...
        >>> from hydpy.models.snow.snow_model import Sub_SnowModel
        >>> with Sub_SnowModel.share_configuration(
        ...         {"landtype_constants": consts,
        ...          "landtype_refindices": LandType,
        ...          "refweights": Subarea}):
        ...     from hydpy.models.snow.snow_control import ZoneType
        ...     ZoneType.constants
        ...     from hydpy.models.snow.snow_parameters import ZipParameterBase
        ...     ZipParameterBase.refindices.__name__
        ...     ZipParameterBase._refweights.__name__
        ...     from hydpy.models.snow.snow_sequences import BaseSequence
        ...     BaseSequence._refweights.__name__
        {'GRASS': 1, 'TREES': 3, 'WATER': 2}
        'LandType'
        'Subarea'
        'Subarea'
        >>> ZoneType.constants
        {'ANY': 0}
        >>> ZipParameterBase._refweights
        >>> BaseSequence._refweights
        """
        with snow_control.ZoneType.modify_constants(
            sharable_configuration["landtype_constants"]
        ), snow_parameters.ZipParameterBase.modify_refindices(
            sharable_configuration["landtype_refindices"]
        ), snow_parameters.ZipParameterBase.modify_refweights(
            sharable_configuration["refweights"]
        ), snow_sequences.BaseSequence.modify_refweights(
            sharable_configuration["refweights"]
        ):
            yield

    @importtools.define_targetparameter(snow_control.NumberZones)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones.

        >>> from hydpy.models.snow_dd import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> numberzones
        numberzones(2)
        """
        self.parameters.control.numberzones(nmbzones)

    @importtools.define_targetparameter(snow_control.ZoneArea)
    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km².

        >>> from hydpy.models.snow_dd import *
        >>> parameterstep()
        >>> numberzones(2)
        >>> model.prepare_subareas([1.0, 3.0])
        >>> zonearea
        zonearea(1.0, 3.0)
        """
        self.parameters.control.zonearea(subareas)

    @importtools.define_targetparameter(snow_control.ZoneHeight)
    def prepare_elevations(self, zoneheights: Sequence[float]) -> None:
        """Set the elevations of the individual zones in m.

        >>> from hydpy.models.snow_dd import *
        >>> parameterstep()
        >>> numberzones(2)
        >>> model.prepare_elevations([1.0, 3.0])
        >>> zoneheight
        zoneheight(1.0, 3.0)
        """
        self.parameters.control.zoneheight(zoneheights)

    @importtools.define_targetparameter(snow_control.Land)
    def prepare_land(self, land: VectorInputBool) -> None:
        """Set the flags for whether the individual zones are land areas or not.

        >>> from hydpy.models.snow_dd import *
        >>> parameterstep()
        >>> numberzones(2)
        >>> model.prepare_land([True, False])
        >>> land
        land(True, False)
        """
        self.parameters.control.land(land)


class Main_ThroughfallModel(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |snow.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |ThroughfallModel_V1| interface and can use
    normal submodels that follow the |ThroughfallModel_V2| alternatively."""

    throughfallmodel: modeltools.SubmodelProperty[
        throughfallinterfaces.ThroughfallModel_V1
        | throughfallinterfaces.ThroughfallModel_V2
    ]
    throughfallmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    throughfallmodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |ThroughfallModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> snow = prepare_model("snow_dd")
        >>> snow.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> snow.throughfallmodel
        >>> snow.throughfallmodel_is_mainmodel
        False
        >>> snow.throughfallmodel_typeid
        0

        >>> land = prepare_model("hland_96")
        >>> snow.add_mainmodel_as_subsubmodel(land)
        True
        >>> snow.throughfallmodel is land
        True
        >>> snow.throughfallmodel_is_mainmodel
        True
        >>> snow.throughfallmodel_typeid
        1
        """
        if isinstance(mainmodel, throughfallinterfaces.ThroughfallModel_V1):
            self.throughfallmodel = mainmodel
            self.throughfallmodel_is_mainmodel = True
            self.throughfallmodel_typeid = (
                throughfallinterfaces.ThroughfallModel_V1.typeid
            )
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)

    @importtools.prepare_submodel(
        "throughfallmodel",
        throughfallinterfaces.ThroughfallModel_V2,
        throughfallinterfaces.ThroughfallModel_V2.prepare_nmbzones,
    )
    def add_throughfallmodel_v2(
        self,
        throughfallmodel: throughfallinterfaces.ThroughfallModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given throughfall model that follows the |ThroughfallModel_V2|
        interface and set the number and the subareas of its zones.

        >>> from hydpy.models.snow_dd import *
        >>> parameterstep()
        >>> numberzones(2)
        >>> zonearea(2.0, 8.0)
        >>> with model.add_throughfallmodel_v2("meteo_throughfall_io"):
        ...     numberzones
        ...     zonearea
        numberzones(2)
        zonearea(2.0, 8.0)
        """
        control = self.parameters.control
        throughfallmodel.prepare_nmbzones(control.numberzones.value)
