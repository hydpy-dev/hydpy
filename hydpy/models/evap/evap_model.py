# -*- coding: utf-8 -*-
"""
.. _`Allen`: http://www.fao.org/3/x0490e/x0490e00.htm
.. _`solar time`: https://en.wikipedia.org/wiki/Solar_time
.. _`DWA-M 504`: `https://de.dwa.de/de/regelwerksankuendigungen-volltext/verdunstung-von-land-und-wasserfl%C3%A4chen.html` # pylint: disable=line-too-long
.. Link does not work after line break (reason not found yet)

"""
# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_derived
from hydpy.models.evap import evap_inputs
from hydpy.models.evap import evap_fluxes
from hydpy.models.evap import evap_logs


class Calc_AdjustedWindSpeed_V1(modeltools.Method):
    """Adjust the measured wind speed to a height of two meters above
    the ground.

    Basic equation (`Allen`_ equation 47, modified for higher precision):
      :math:`AdjustedWindSpeed = WindSpeed \\cdot
      \\frac{ln((2-d)/z_0)}
      {ln((MeasuringHeightWindSpeed-d)/z_0)}` \n

      :math:`d = 2 / 3 \\cdot 0.12` \n

      :math:`z_0 = 0.123 \\cdot 0.12`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_adjustedwindspeed_v1()
        >>> fluxes.adjustedwindspeed
        adjustedwindspeed(3.738763)
    """

    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)
    RESULTSEQUENCES = (evap_fluxes.AdjustedWindSpeed,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_d = 2.0 / 3.0 * 0.12
        d_z0 = 0.123 * 0.12
        flu.adjustedwindspeed = inp.windspeed * (
            modelutils.log((2.0 - d_d) / d_z0)
            / modelutils.log((con.measuringheightwindspeed - d_d) / d_z0)
        )


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    """Calculate the saturation vapour pressure.

    Basic equation (`Allen`_, equation 11):
      :math:`SaturationVapourPressure = 0.6108 \\cdot
      \\exp(\\frac{17.27 \\cdot AirTemperature}{AirTemperature + 237.3})`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.airtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> fluxes.saturationvapourpressure
        saturationvapourpressure(1.227963)
    """

    REQUIREDSEQUENCES = (evap_inputs.AirTemperature,)
    RESULTSEQUENCES = (evap_fluxes.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.saturationvapourpressure = 0.6108 * modelutils.exp(
            17.27 * inp.airtemperature / (inp.airtemperature + 237.3)
        )


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    """Calculate the slope of the saturation vapour pressure curve.

    Basic equation (`Allen`_, equation 13):
      :math:`SaturationVapourPressureSlope = 4098 \\cdot
      \\frac{SaturationVapourPressure}{(AirTemperature+237.3)^2}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.airtemperature = 10.0
        >>> fluxes.saturationvapourpressure(1.227963)
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> fluxes.saturationvapourpressureslope
        saturationvapourpressureslope(0.082283)
    """

    REQUIREDSEQUENCES = (
        evap_inputs.AirTemperature,
        evap_fluxes.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_fluxes.SaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.saturationvapourpressureslope = (
            4098.0 * flu.saturationvapourpressure / (inp.airtemperature + 237.3) ** 2
        )


class Calc_ActualVapourPressure_V1(modeltools.Method):
    """Calculate the actual vapour pressure.

    Basic equation (`Allen`_, equation 19, modified):
      :math:`ActualVapourPressure = SaturationVapourPressure \\cdot
      RelativeHumidity / 100`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.relativehumidity = 60.0
        >>> fluxes.saturationvapourpressure = 3.0
        >>> model.calc_actualvapourpressure_v1()
        >>> fluxes.actualvapourpressure
        actualvapourpressure(1.8)
    """

    REQUIREDSEQUENCES = (
        evap_inputs.RelativeHumidity,
        evap_fluxes.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_fluxes.ActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualvapourpressure = (
            flu.saturationvapourpressure * inp.relativehumidity / 100.0
        )


class Calc_EarthSunDistance_V1(modeltools.Method):
    """Calculate the relative inverse distance between the earth and the sun.

    Basic equation (`Allen`_, equation 23):
      :math:`EarthSunDistance = 1 + 0.033 \\cdot cos(
      2 \\cdot \\pi / 366 \\cdot (DOY + 1)`

    Note that this equation differs a little from the one given by `Allen`_.
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
        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> derived.doy.update()

        The following convenience function applies method
        |Calc_EarthSunDistance_V1| for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_earthsundistance_v1()
        ...         print(date, end=": ")
        ...         round_(fluxes.earthsundistance.value)

        The results are identical for both years:

        >>> test("2000-01-01", "2000-02-28", "2000-02-29",
        ...      "2000-03-01", "2000-07-01", "2000-12-31")
        2000-01-01: 1.032995
        2000-02-28: 1.017471
        2000-02-29: 1.016988
        2000-03-01: 1.0165
        2000-07-01: 0.967
        2000-12-31: 1.033

        >>> test("2001-01-01", "2001-02-28",
        ...      "2001-03-01", "2001-07-01", "2001-12-31")
        2001-01-01: 1.032995
        2001-02-28: 1.017471
        2001-03-01: 1.0165
        2001-07-01: 0.967
        2001-12-31: 1.033

        The following calculation agrees with example 8 of `Allen`_:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_earthsundistance_v1()
        >>> fluxes.earthsundistance
        earthsundistance(0.984993)
    """

    DERIVEDPARAMETERS = (evap_derived.DOY,)
    RESULTSEQUENCES = (evap_fluxes.EarthSunDistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.earthsundistance = 1.0 + 0.033 * modelutils.cos(
            2 * 3.141592653589793 / 366.0 * (der.doy[model.idx_sim] + 1)
        )


class Calc_SolarDeclination_V1(modeltools.Method):
    """Calculate the solar declination.

    Basic equation (`Allen`_, equation 24):
      :math:`SolarDeclination = 0.409 \\cdot sin(
      2 \\cdot \\pi / 366 \\cdot (DOY + 1) - 1.39)`

    Note that this equation actually differs from the one given by
    `Allen`_ a little, due to reasons explained in the documentation
    on method |Calc_EarthSunDistance_V1|.

    Examples:

        We define an initialisation period covering both a leap year (2000)
        and a non-leap year (2001):

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> derived.doy.update()

        The following convenience function applies method
        |Calc_SolarDeclination_V1| for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_solardeclination_v1()
        ...         print(date, end=": ")
        ...         round_(fluxes.solardeclination.value)

        The results are identical for both years:

        >>> test("2000-01-01", "2000-02-28", "2000-02-29",
        ...      "2000-03-01", "2000-12-31")
        2000-01-01: -0.401012
        2000-02-28: -0.150618
        2000-02-29: -0.144069
        2000-03-01: -0.137476
        2000-12-31: -0.402334

        >>> test("2001-01-01", "2001-02-28",
        ...      "2001-03-01", "2001-12-31")
        2001-01-01: -0.401012
        2001-02-28: -0.150618
        2001-03-01: -0.137476
        2001-12-31: -0.402334

        The following calculation agrees with example 8 of `Allen`_:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_solardeclination_v1()
        >>> fluxes.solardeclination
        solardeclination(0.117464)
    """

    DERIVEDPARAMETERS = (evap_derived.DOY,)
    RESULTSEQUENCES = (evap_fluxes.SolarDeclination,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.solardeclination = 0.409 * modelutils.sin(
            2 * 3.141592653589793 / 366 * (der.doy[model.idx_sim] + 1) - 1.39
        )


class Calc_SunsetHourAngle_V1(modeltools.Method):
    """Calculate the sunset hour angle.

    Basic equation (`Allen`_, equation 25):
      :math:`SunsetHourAngle =
      arccos(-tan(LatitudeRad) \\cdot tan(SolarDeclination))`

    Example:

        The following calculation agrees with example 8 of `Allen`_:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.doy.shape = 1
        >>> derived.doy(246)
        >>> derived.latituderad(-.35)
        >>> fluxes.solardeclination = 0.12
        >>> model.calc_sunsethourangle_v1()
        >>> fluxes.sunsethourangle
        sunsethourangle(1.526767)
    """

    DERIVEDPARAMETERS = (evap_derived.LatitudeRad,)
    REQUIREDSEQUENCES = (evap_fluxes.SolarDeclination,)
    RESULTSEQUENCES = (evap_fluxes.SunsetHourAngle,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.sunsethourangle = modelutils.acos(
            -modelutils.tan(der.latituderad) * modelutils.tan(flu.solardeclination)
        )


class Calc_SolarTimeAngle_V1(modeltools.Method):
    """Calculate the solar time angle at the midpoint of the current period.

    Basic equations (`Allen`_, equations 31 to 33):
      :math:`SolarTimeAngle =
      \\pi / 12 \\cdot ((SCT + (Longitude - UTCLongitude) / 15 + S_c) - 12)` \n

      :math:`S_c = 0.1645 \\cdot sin(2 \\cdot b) -
      0.1255 \\cdot cos(b) - 0.025 \\cdot sin(b)` \n

      :math:`b = (2 \\cdot \\pi (DOY - 80)) / 365`

    Note there are two small deviations from the equations given by
    `Allen`_.  The first one is to describe longitudes east of
    Greenwich with positive numbers and longitudes west of Greenwich
    with negative numbers.  The second one is due to the definition of
    parameter |DOY|, as explained in the documentation on method
    |Calc_EarthSunDistance_V1|.

    Examples:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-09-03", "2000-09-04", "1h"
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> longitude(15)
        >>> derived.doy.update()
        >>> derived.sct.update()
        >>> derived.utclongitude.update()
        >>> for hour in range(24):
        ...     model.idx_sim = hour
        ...     model.calc_solartimeangle_v1()
        ...     print(hour, end=": ")
        ...     round_(fluxes.solartimeangle.value)   # doctest: +ELLIPSIS
        0: -3.004157
        1: -2.742358
        ...
        11: -0.124364
        12: 0.137435
        ...
        22: 2.755429
        23: 3.017229
    """

    CONTROLPARAMETERS = (evap_control.Longitude,)
    DERIVEDPARAMETERS = (
        evap_derived.DOY,
        evap_derived.SCT,
        evap_derived.UTCLongitude,
    )
    RESULTSEQUENCES = (evap_fluxes.SolarTimeAngle,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_pi = 3.141592653589793
        d_b = 2.0 * d_pi * (der.doy[model.idx_sim] - 80.0) / 365.0
        d_sc = (
            0.1645 * modelutils.sin(2.0 * d_b)
            - 0.1255 * modelutils.cos(d_b)
            - 0.025 * modelutils.sin(d_b)
        )
        flu.solartimeangle = (
            d_pi
            / 12.0
            * (
                (
                    der.sct[model.idx_sim]
                    + (con.longitude - der.utclongitude) / 15.0
                    + d_sc
                )
                - 12.0
            )
        )


class Calc_ExtraterrestrialRadiation_V1(modeltools.Method):
    """Calculate the extraterrestrial radiation.

    Basic equation for daily simulation steps (`Allen`_, equation 21):
      :math:`ExternalTerrestrialRadiation =
      \\frac{Seconds \\ 4.92}{\\pi \\ 60 \\cdot 60} \\cdot
      EarthSunDistance \\cdot (
      SunsetHourAngle \\cdot sin(LatitudeRad) \\cdot sin(SolarDeclination) +
      cos(LatitudeRad) \\cdot cos(SolarDeclination) \\cdot sin(SunsetHourAngle)
      )`

    Basic equation for (sub)hourly simulation steps (`Allen`_, eq. 28 to 30):
      :math:`ExternalTerrestrialRadiation =
      \\frac{12 \\cdot 4.92}{\\pi} \\cdot EarthSunDistance \\cdot (
      (\\omega_2 - \\omega_1) \\cdot sin(LatitudeRad) \\cdot
      sin(SolarDeclination) +
      cos(LatitudeRad) \\cdot cos(SolarDeclination) \\cdot
      (sin(\\omega_2) - sin(\\omega_1))
      )` \n

      :math:`omega_1 = SolarTimeAngle -
      \\frac{\\pi \\cdot Seconds}{60 \\cdot 60 \\cdot 24}` \n

      :math:`omega_2 = SolarTimeAngle +
      \\frac{\\pi \\cdot Seconds}{60 \\cdot 60 \\cdot 24}`

    Examples:

        The following calculation agrees with example 8 of `Allen`_
        for daily time steps:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(60*60*24)
        >>> derived.latituderad(-0.35)
        >>> fluxes.earthsundistance = 0.985
        >>> fluxes.solardeclination = 0.12
        >>> fluxes.sunsethourangle = 1.527
        >>> model.calc_extraterrestrialradiation_v1()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(32.173851)

        The following calculation repeats the above example for an hourly
        simulation time step, still covering the whole day:

        >>> import numpy
        >>> longitude(-20)
        >>> derived.utclongitude(-20)
        >>> derived.seconds(60*60)
        >>> derived.doy.shape = 24
        >>> derived.doy(246)
        >>> derived.sct.shape = 24
        >>> derived.sct = numpy.linspace(0.5, 23.5, 24)
        >>> sum_ = 0.0
        >>> from hydpy import round_
        >>> for hour in range(24):
        ...     model.idx_sim = hour
        ...     model.calc_solartimeangle_v1()
        ...     model.calc_extraterrestrialradiation_v1()
        ...     print(hour, end=": ")
        ...     round_(fluxes.extraterrestrialradiation.value)
        ...     sum_ += fluxes.extraterrestrialradiation
        0: 0.0
        1: 0.0
        2: 0.0
        3: 0.0
        4: 0.0
        5: 0.0
        6: 0.418507
        7: 1.552903
        8: 2.567915
        9: 3.39437
        10: 3.975948
        11: 4.273015
        12: 4.265326
        13: 3.953405
        14: 3.35851
        15: 2.52118
        16: 1.49848
        17: 0.360103
        18: 0.0
        19: 0.0
        20: 0.0
        21: 0.0
        22: 0.0
        23: 0.0

        Note that, even with identical values of the local longitude
        (|Longitude|) and the one of the time zone (|UTCLongitude|), the
        calculated radiation values are not symmetrically shaped during the
        day due to the eccentricity of the Earth"s orbit (see `solar time`_).

        There is a small deviation between the directly calculated daily
        value and the sum of the hourly values:

        >>> round_(sum_)
        32.139663

        For sub-daily simulation time steps, the results of method
        |Calc_ExtraterrestrialRadiation_V1| are most accurate for the shortest
        time steps.  On the other hand, they can be (extremely) inaccurate
        for timesteps between one hour and one day.  We demonstrate this by
        comparing the sum of the sub-daily values of different step sizes with
        the directly calculated daily value (note the apparent total fail of
        method |Calc_ExtraterrestrialRadiation_V1| for a step size of 720
        minutes):

        >>> for minutes in [1, 5, 15, 30, 60, 90, 120, 144, 160,
        ...                 180, 240, 288, 360, 480, 720, 1440]:
        ...     derived.seconds(minutes*60)
        ...     nmb = int(1440/minutes)
        ...     derived.doy.shape = nmb
        ...     derived.doy(246)
        ...     derived.sct.shape = nmb
        ...     derived.sct = numpy.linspace(
        ...         minutes/60/2, 24-minutes/60/2, nmb)
        ...     sum_ = 0.0
        ...     for idx in range(nmb):
        ...         model.idx_sim = idx
        ...         model.calc_solartimeangle_v1()
        ...         model.calc_extraterrestrialradiation_v1()
        ...         sum_ += fluxes.extraterrestrialradiation
        ...     print(minutes, end=": ")
        ...     round_(sum_-32.173851)
        1: -0.000054
        5: -0.000739
        15: -0.008646
        30: -0.034188
        60: -0.034188
        90: -0.034188
        120: -0.034188
        144: -1.246615
        160: -0.823971
        180: -0.034188
        240: -3.86418
        288: -2.201488
        360: -0.034188
        480: -3.86418
        720: -32.173851
        1440: 0.0
    """

    DERIVEDPARAMETERS = (
        evap_derived.Seconds,
        evap_derived.LatitudeRad,
    )
    REQUIREDSEQUENCES = (
        evap_fluxes.SolarTimeAngle,
        evap_fluxes.EarthSunDistance,
        evap_fluxes.SolarDeclination,
        evap_fluxes.SunsetHourAngle,
    )
    RESULTSEQUENCES = (evap_fluxes.ExtraterrestrialRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_pi = 3.141592653589793
        if der.seconds < 60.0 * 60.0 * 24.0:
            d_delta = d_pi * der.seconds / 60.0 / 60.0 / 24.0
            d_omega1 = flu.solartimeangle - d_delta
            d_omega2 = flu.solartimeangle + d_delta
            flu.extraterrestrialradiation = max(
                12.0
                * 4.92
                / d_pi
                * flu.earthsundistance
                * (
                    (
                        (d_omega2 - d_omega1)
                        * modelutils.sin(der.latituderad)
                        * modelutils.sin(flu.solardeclination)
                    )
                    + (
                        modelutils.cos(der.latituderad)
                        * modelutils.cos(flu.solardeclination)
                        * (modelutils.sin(d_omega2) - modelutils.sin(d_omega1))
                    )
                ),
                0.0,
            )
        else:
            flu.extraterrestrialradiation = (
                der.seconds
                * 0.0820
                / 60.0
                / d_pi
                * flu.earthsundistance
                * (
                    (
                        flu.sunsethourangle
                        * modelutils.sin(der.latituderad)
                        * modelutils.sin(flu.solardeclination)
                    )
                    + (
                        modelutils.cos(der.latituderad)
                        * modelutils.cos(flu.solardeclination)
                        * modelutils.sin(flu.sunsethourangle)
                    )
                )
            )


class Calc_PossibleSunshineDuration_V1(modeltools.Method):
    """Calculate the possible astronomical sunshine duration.

    Basic equation for daily timesteps (`Allen`_, equation 34):
      :math:`PossibleSunshineDuration = 24 / \\pi \\cdot SunsetHourAngle`

    Basic equation for (sub)hourly timesteps:
      :math:`PossibleSunshineDuration =
      min(max(12 / \\pi \\cdot (SunsetHourAngle - \\tau), 0),
      \\frac{Seconds}{60 \\cdot 60})` \n

      :math:`\\tau = \\Bigl \\lbrace
      {
      {-SolarTimeAngle - \\pi \\cdot Days \\ | \\ SolarTimeAngle \\leq 0}
      \\atop
      {SolarTimeAngle - \\pi \\cdot Days \\ | \\ SolarTimeAngle > 0}
      }`

    Examples:

        The following calculation agrees with example 9 of `Allen`_:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(60*60*24)
        >>> fluxes.sunsethourangle(1.527)
        >>> model.calc_possiblesunshineduration_v1()
        >>> fluxes.possiblesunshineduration
        possiblesunshineduration(11.665421)

        The following calculation repeats the above example for an hourly
        simulation time step, still covering the whole day. Therefore the ratio
        is only calculated for the hours of sunrise and sunset. In between the
        ratio is set to 1 (day) or 0 (night):

        >>> from hydpy import round_
        >>> import numpy
        >>> derived.seconds(60*60)
        >>> solartimeangles = numpy.linspace(-3.004157, 3.017229, 24)
        >>> sum_ = 0.
        >>> for hour, solartimeangle in enumerate(solartimeangles):
        ...     fluxes.solartimeangle = solartimeangle
        ...     model.calc_possiblesunshineduration_v1()
        ...     print(hour, end=": ")   # doctest: +ELLIPSIS
        ...     round_(fluxes.possiblesunshineduration.value)
        ...     sum_ += fluxes.possiblesunshineduration.value
        0: 0.0
        ...
        5: 0.0
        6: 0.857676
        7: 1.0
        ...
        16: 1.0
        17: 0.807745
        18: 0.0
        ...
        23: 0.0

        The sum of the hourly sunshine durations equals the one-step
        calculation result:

        >>> round_(sum_)
        11.665421
    """

    DERIVEDPARAMETERS = (evap_derived.Seconds,)
    REQUIREDSEQUENCES = (
        evap_fluxes.SolarTimeAngle,
        evap_fluxes.SunsetHourAngle,
    )
    RESULTSEQUENCES = (evap_fluxes.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_pi = 3.141592653589793
        d_hours = der.seconds / 60.0 / 60.0
        d_days = d_hours / 24.0
        if d_hours < 24.0:
            if flu.solartimeangle <= 0.0:
                d_thresh = -flu.solartimeangle - d_pi * d_days
            else:
                d_thresh = flu.solartimeangle - d_pi * d_days
            flu.possiblesunshineduration = min(
                max(12.0 / d_pi * (flu.sunsethourangle - d_thresh), 0.0), d_hours
            )
        else:
            flu.possiblesunshineduration = 24.0 / d_pi * flu.sunsethourangle


class Calc_ClearSkySolarRadiation_V1(modeltools.Method):
    """Calculate the clear sky solar radiation.

    Basic equation (adjusted to |Calc_GlobalRadiation_V1|, `Allen`_ eq. 35):
      :math:`ClearSkySolarRadiation =
      ExtraterrestrialRadiation \\cdot (AngstromConstant + AngstromFactor)`

    Example:

        We use the Ångström coefficients (a=0.19, b=0.55) recommended
        for Germany by `DWA-M 504`_ for January and the default values
        (a=0.25, b=0.5) for February:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> angstromconstant.jan = 0.19
        >>> angstromfactor.jan = 0.55
        >>> angstromconstant.feb = 0.25
        >>> angstromfactor.feb = 0.5
        >>> derived.moy.update()
        >>> fluxes.extraterrestrialradiation = 40.0
        >>> model.idx_sim = 1
        >>> model.calc_clearskysolarradiation_v1()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(29.6)
        >>> model.idx_sim = 2
        >>> model.calc_clearskysolarradiation_v1()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(30.0)
    """

    CONTROLPARAMETERS = (
        evap_control.AngstromConstant,
        evap_control.AngstromFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (evap_fluxes.ExtraterrestrialRadiation,)
    RESULTSEQUENCES = (evap_fluxes.ClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        idx = der.moy[model.idx_sim]
        flu.clearskysolarradiation = flu.extraterrestrialradiation * (
            con.angstromconstant[idx] + con.angstromfactor[idx]
        )


class Update_LoggedClearSkySolarRadiation_V1(modeltools.Method):
    """Log the clear sky solar radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorized values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedclearskysolarradiation.shape = 3
        >>> logs.loggedclearskysolarradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedclearskysolarradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.clearskysolarradiation,
        ...                          logs.loggedclearskysolarradiation))
        >>> test.nexts.clearskysolarradiation = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedclearskysolarradiation
        >>> test()
        | ex. | clearskysolarradiation |           loggedclearskysolarradiation\
 |
        -----------------------------------------------------------------------\
--
        |   1 |                    1.0 | 1.0  0.0                           0.0\
 |
        |   2 |                    3.0 | 3.0  1.0                           0.0\
 |
        |   3 |                    2.0 | 2.0  3.0                           1.0\
 |
        |   4 |                    4.0 | 4.0  2.0                           3.0\
 |
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_fluxes.ClearSkySolarRadiation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedclearskysolarradiation[idx] = log.loggedclearskysolarradiation[
                idx - 1
            ]
        log.loggedclearskysolarradiation[0] = flu.clearskysolarradiation


class Calc_GlobalRadiation_V1(modeltools.Method):
    """Calculate the extraterrestrial radiation.

    Basic equation (`Allen`_, equation 35):
      :math:`GlobalRadiation = ExtraterrestrialRadiation \\cdot (
      AngstromConstant + AngstromFactor \\cdot
      SunshineDuration / PossibleSunshineDuration
      )`

    Example:

        We use the Ångström coefficients (a=0.19, b=0.55) recommended
        for Germany by `DWA-M 504`_ for January and the default values
        (a=0.25, b=0.5) for February:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> angstromconstant.jan = 0.19
        >>> angstromfactor.jan = 0.55
        >>> angstromconstant.feb = 0.25
        >>> angstromfactor.feb = 0.5
        >>> derived.moy.update()
        >>> inputs.sunshineduration = 12.0
        >>> fluxes.possiblesunshineduration = 14.0
        >>> fluxes.extraterrestrialradiation = 40.0
        >>> model.idx_sim = 1
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(26.457143)
        >>> model.idx_sim = 2
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(27.142857)

        For zero possible sunshine durations, |Calc_GlobalRadiation_V1|
        sets |GlobalRadiation| to zero:

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.AngstromConstant,
        evap_control.AngstromFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (
        evap_fluxes.ExtraterrestrialRadiation,
        evap_inputs.SunshineDuration,
        evap_fluxes.PossibleSunshineDuration,
    )
    RESULTSEQUENCES = (evap_fluxes.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if flu.possiblesunshineduration > 0.0:
            idx = der.moy[model.idx_sim]
            flu.globalradiation = flu.extraterrestrialradiation * (
                con.angstromconstant[idx]
                + con.angstromfactor[idx]
                * inp.sunshineduration
                / flu.possiblesunshineduration
            )
        else:
            flu.globalradiation = 0.0


class Update_LoggedGlobalRadiation_V1(modeltools.Method):
    """Log the global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorized values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedglobalradiation.shape = 3
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

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_fluxes.GlobalRadiation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedglobalradiation[idx] = log.loggedglobalradiation[idx - 1]
        log.loggedglobalradiation[0] = flu.globalradiation


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    """Calculate the net shortwave radiation for the hypothetical grass
    reference crop.

    Basic equation (`Allen`_, equation 38):
      :math:`NetShortwaveRadiation = (1.0 - 0.23) \\cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> fluxes.globalradiation = 20.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(15.4)
    """

    REQUIREDSEQUENCES = (evap_fluxes.GlobalRadiation,)
    RESULTSEQUENCES = (evap_fluxes.NetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.netshortwaveradiation = (1.0 - 0.23) * flu.globalradiation


class Calc_NetLongwaveRadiation_V1(modeltools.Method):
    """Calculate the net longwave radiation.

    Basic equation (`Allen`_, equation 39, modified):
      :math:`NetLongwaveRadiation =
      \\sigma \\cdot Seconds \\cdot (AirTemperature+273.16)^4
      \\cdot (0.34 - 0.14 \\sqrt{ActualVapourPressure}) \\cdot
      (1.35 \\cdot GR / CSSR - 0.35)` \n

      :math:`GR = \\Bigl \\lbrace
      {
      {GlobalRadiation \\ | \\ ClearSkySolarRadiation > 0}
      \\atop
      {\\sum{LoggedGlobalRadiation} \\ | \\ ClearSkySolarRadiation = 0}
      }` \n

      :math:`CSSR = \\Bigl \\lbrace
      {
      {ClearSkySolarRadiation \\ | \\ ClearSkySolarRadiation > 0}
      \\atop
      {\\sum{LoggedClearSkySolarRadiation} \\ | \\ ClearSkySolarRadiation = 0}
      }` \n

      :math:`\\sigma = 5.6747685185185184 \\cdot 10^{-14}`

    Note that during night periods, when clear sky radiation is zero, we use
    the global radiation and clear sky radiation sums of the last 24 hours.
    Averaging over the last three hours before sunset, as suggested by
    `Allen`_, could be a more precise but also more complicated and
    error-prone approach.

    Example:

        The following calculation agrees with example 11 of `Allen`_:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(60*60*24)
        >>> derived.nmblogentries(1)
        >>> inputs.airtemperature = 22.1
        >>> fluxes.actualvapourpressure = 2.1
        >>> fluxes.clearskysolarradiation = 18.8
        >>> fluxes.globalradiation = 14.5
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.531847)

        >>> fluxes.clearskysolarradiation = 0.0
        >>> logs.loggedclearskysolarradiation.shape = 1
        >>> logs.loggedclearskysolarradiation = 12.0
        >>> logs.loggedglobalradiation.shape = 1
        >>> logs.loggedglobalradiation = 10.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.959909)
    """

    DERIVEDPARAMETERS = (
        evap_derived.NmbLogEntries,
        evap_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        evap_inputs.AirTemperature,
        evap_fluxes.ClearSkySolarRadiation,
        evap_fluxes.GlobalRadiation,
        evap_fluxes.ActualVapourPressure,
        evap_logs.LoggedGlobalRadiation,
        evap_logs.LoggedClearSkySolarRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        if flu.clearskysolarradiation > 0.0:
            d_globalradiation = flu.globalradiation
            d_clearskysolarradiation = flu.clearskysolarradiation
        else:
            d_globalradiation = 0.0
            d_clearskysolarradiation = 0.0
            for idx in range(der.nmblogentries):
                d_clearskysolarradiation += log.loggedclearskysolarradiation[idx]
                d_globalradiation += log.loggedglobalradiation[idx]
        flu.netlongwaveradiation = (
            4.903e-9
            / 24.0
            / 60.0
            / 60.0
            * der.seconds
            * (inp.airtemperature + 273.16) ** 4
            * (0.34 - 0.14 * flu.actualvapourpressure ** 0.5)
            * (1.35 * d_globalradiation / d_clearskysolarradiation - 0.35)
        )


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation.

    Basic equation (`Allen`_, equation 40):
      :math:`NetRadiation = NetShortwaveRadiation-NetLongwaveRadiation`

    Example:

        The following calculation agrees with example 12 of `Allen`_:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> fluxes.netshortwaveradiation  = 11.1
        >>> fluxes.netlongwaveradiation  = 3.5
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(7.6)
    """

    REQUIREDSEQUENCES = (
        evap_fluxes.NetShortwaveRadiation,
        evap_fluxes.NetLongwaveRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.netradiation = flu.netshortwaveradiation - flu.netlongwaveradiation


class Calc_SoilHeatFlux_V1(modeltools.Method):
    """Calculate the soil heat flux.

    Basic equation for daily timesteps (`Allen`_, equation 42):
      :math:`SoilHeatFlux = 0` \n

    Basic equation for (sub)hourly timesteps (`Allen`_, eq. 45 and 46 ):
      :math:`SoilHeatFlux = \\Bigl \\lbrace
      {
      {0.1 \\cdot SoilHeatFlux \\ | \\ NetRadiation \\geq 0}
      \\atop
      {0.5 \\cdot SoilHeatFlux \\ | \\ NetRadiation < 0}
      }`

    Examples:

        For simulation time steps shorter one day, we define all steps with
        a positive |NetRadiation| to be part of the daylight period and all
        steps with a negative |NetRadiation| to be part of the nighttime
        period.  In case the summed |NetRadiation| of all daylight steps is
        five times as high as the absolute summed |NetRadiation| of all
        nighttime steps, the total |SoilHeatFlux| is zero:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(60*60)
        >>> fluxes.netradiation = 10.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(1.0)
        >>> fluxes.netradiation = -2.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(-1.0)

        For any simulation step size of least one day, method
        |Calc_SoilHeatFlux_V1| sets the |SoilHeatFlux| to zero, which
        is suggested by `Allen`_ for daily simulation steps only:


        >>> derived.seconds(60*60*24)
        >>> fluxes.netradiation = 10.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)
        >>> fluxes.netradiation = -2.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)

        Hence, be aware that function |Calc_SoilHeatFlux_V1| does not give
        the best results for intermediate (e.g. 12 hours) or larger
        step sizes (e.g. one month).
    """

    DERIVEDPARAMETERS = (evap_derived.Seconds,)
    REQUIREDSEQUENCES = (evap_fluxes.NetRadiation,)
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if der.seconds < 60.0 * 60.0 * 24.0:
            if flu.netradiation >= 0.0:
                flu.soilheatflux = 0.1 * flu.netradiation
            else:
                flu.soilheatflux = 0.5 * flu.netradiation
        else:
            flu.soilheatflux = 0.0


class Calc_PsychrometricConstant_V1(modeltools.Method):
    """Calculate the psychrometric constant.

    Basic equation (`Allen`_, equation 8):
      :math:`PsychrometricConstant =
      6.65 \\cdot 10^{-4} \\cdot AtmosphericPressure`

    Example:

        The following calculation agrees with example 2 of `Allen`_:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.atmosphericpressure = 81.8
        >>> model.calc_psychrometricconstant_v1()
        >>> fluxes.psychrometricconstant
        psychrometricconstant(0.054397)
    """

    REQUIREDSEQUENCES = (evap_inputs.AtmosphericPressure,)
    RESULTSEQUENCES = (evap_fluxes.PsychrometricConstant,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.psychrometricconstant = 6.65e-4 * inp.atmosphericpressure


class Calc_ReferenceEvapotranspiration_V1(modeltools.Method):
    """Calculate the reference evapotranspiration constant.

    Basic equation (`Allen`_, equation 6):
      :math:`ReferenceEvapotranspiration =
      \\frac{
      0.408 \\cdot SaturationVapourPressureSlope \\cdot
      (NetRadiation - SoilHeatFlux) +
      PsychrometricConstant \\cdot
      \\frac{37.5 \\cdot Seconds}{60 \\cdot 60 \\cdot (AirTemperature + 273)}
      \\cdot AdjustedWindSpeed \\cdot
      (SaturationVapourPressure - ActualVapourPressure)
      }
      {
      SaturationVapourPressureSlope +
      PsychrometricConstant \\cdot (1 + 0.34 \\cdot AdjustedWindSpeed)
      }`

    Note that `Allen`_ recommends the coefficient 37 for
    hourly simulations and the coefficient 900 for daily simulations.
    Function |Calc_ReferenceEvapotranspiration_V1| generally uses 37.5,
    which gives 900 when multiplied with 24.

    Example:

        The following calculation agrees with example 18 of `Allen`_,
        dealing with a daily simulation step:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(24*60*60)
        >>> inputs.airtemperature = 16.9
        >>> fluxes.netradiation = 13.28
        >>> fluxes.soilheatflux = 0.0
        >>> fluxes.psychrometricconstant = 0.0666
        >>> fluxes.adjustedwindspeed = 2.078
        >>> fluxes.actualvapourpressure = 1.409
        >>> fluxes.saturationvapourpressure = 1.997
        >>> fluxes.saturationvapourpressureslope = 0.122
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.877117)

        The following calculation agrees with example 19 of `Allen`_,
        dealing with an hourly simulation step (note that there is a
        difference due to using 37.5 instead of 37 that is smaller
        than the precision of the results tabulated by `Allen`_:

        >>> derived.seconds(60*60)
        >>> inputs.airtemperature = 38.0
        >>> fluxes.netradiation = 1.749
        >>> fluxes.soilheatflux = 0.175
        >>> fluxes.psychrometricconstant = 0.0673
        >>> fluxes.adjustedwindspeed = 3.3
        >>> fluxes.actualvapourpressure = 3.445
        >>> fluxes.saturationvapourpressure = 6.625
        >>> fluxes.saturationvapourpressureslope = 0.358
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(0.629106)
    """

    DERIVEDPARAMETERS = (evap_derived.Seconds,)
    REQUIREDSEQUENCES = (
        evap_inputs.AirTemperature,
        evap_fluxes.SaturationVapourPressureSlope,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
        evap_fluxes.PsychrometricConstant,
        evap_fluxes.AdjustedWindSpeed,
        evap_fluxes.SaturationVapourPressure,
        evap_fluxes.ActualVapourPressure,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.referenceevapotranspiration = (
            0.408
            * flu.saturationvapourpressureslope
            * (flu.netradiation - flu.soilheatflux)
            + flu.psychrometricconstant
            * (37.5 / 60.0 / 60.0 * der.seconds)
            / (inp.airtemperature + 273.0)
            * flu.adjustedwindspeed
            * (flu.saturationvapourpressure - flu.actualvapourpressure)
        ) / (
            flu.saturationvapourpressureslope
            + flu.psychrometricconstant * (1.0 + 0.34 * flu.adjustedwindspeed)
        )


class Model(modeltools.AdHocModel):
    """The Evap base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_AdjustedWindSpeed_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Calc_EarthSunDistance_V1,
        Calc_SolarDeclination_V1,
        Calc_SunsetHourAngle_V1,
        Calc_SolarTimeAngle_V1,
        Calc_ExtraterrestrialRadiation_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_ClearSkySolarRadiation_V1,
        Update_LoggedClearSkySolarRadiation_V1,
        Calc_GlobalRadiation_V1,
        Update_LoggedGlobalRadiation_V1,
        Calc_NetShortwaveRadiation_V1,
        Calc_NetLongwaveRadiation_V1,
        Calc_NetRadiation_V1,
        Calc_SoilHeatFlux_V1,
        Calc_PsychrometricConstant_V1,
        Calc_ReferenceEvapotranspiration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()
