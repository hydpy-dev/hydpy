"""
.. _`solar time`: https://en.wikipedia.org/wiki/Solar_time
"""

# imports...
# ...from standard library
import contextlib

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.models.meteo import meteo_parameters
from hydpy.models.meteo import meteo_fixed
from hydpy.models.meteo import meteo_control
from hydpy.models.meteo import meteo_derived
from hydpy.models.meteo import meteo_sequences
from hydpy.models.meteo import meteo_inputs
from hydpy.models.meteo import meteo_factors
from hydpy.models.meteo import meteo_fluxes
from hydpy.models.meteo import meteo_logs


class Calc_EarthSunDistance_V1(modeltools.Method):
    r"""Calculate the relative inverse distance between the Earth and the sun
    according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 23):
      :math:`EarthSunDistance = 1 + 0.033 \cdot cos(2 \cdot Pi / 366 \cdot (DOY + 1)`

    Note that this equation differs slightly from the one given by
    :cite:t:`ref-Allen1998`.  The following examples show that
    |Calc_EarthSunDistance_V1| calculates the same distance value for a specific
    "day" (e.g. the 1st March) both for leap years and non-leap years.  Hence,
    there is a tiny "jump" between 28th February and 1st March for non-leap years.

    Examples:

        We define an initialisation period covering a leap year (2000) and a non-leap
        year (2001):

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> derived.doy.update()

        The following convenience function applies method |Calc_EarthSunDistance_V1|
        for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_earthsundistance_v1()
        ...         print(date, end=": ")
        ...         round_(factors.earthsundistance.value)

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

        The following calculation agrees with example 8 of :cite:t:`ref-Allen1998`:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_earthsundistance_v1()
        >>> factors.earthsundistance
        earthsundistance(0.984993)

        .. testsetup::

            >>> del pub.timegrids
    """

    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    DERIVEDPARAMETERS = (meteo_derived.DOY,)
    RESULTSEQUENCES = (meteo_factors.EarthSunDistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fix = model.parameters.fixed.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.earthsundistance = 1.0 + 0.033 * modelutils.cos(
            2 * fix.pi / 366.0 * (der.doy[model.idx_sim] + 1)
        )


class Calc_SolarDeclination_V1(modeltools.Method):
    r"""Calculate the solar declination according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 24):
      :math:`SolarDeclination =
      0.409 \cdot sin(2 \cdot Pi / 366 \cdot (DOY + 1) - 1.39)`

    Note that this equation differs slightly from the one given by
    :cite:t:`ref-Allen1998` due to reasons explained in the documentation on method
    |Calc_EarthSunDistance_V1|.

    Examples:

        We define an initialisation period covering both a leap year (2000) and a
        non-leap year (2001):

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> derived.doy.update()

        The following convenience function applies method |Calc_SolarDeclination_V1|
        for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_solardeclination_v1()
        ...         print(date, end=": ")
        ...         round_(factors.solardeclination.value)

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

        The following calculation agrees with example 8 of :cite:t:`ref-Allen1998`:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_solardeclination_v1()
        >>> factors.solardeclination
        solardeclination(0.117464)

        .. testsetup::

            >>> del pub.timegrids
    """

    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    DERIVEDPARAMETERS = (meteo_derived.DOY,)
    RESULTSEQUENCES = (meteo_factors.SolarDeclination,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fix = model.parameters.fixed.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.solardeclination = 0.409 * modelutils.sin(
            2 * fix.pi / 366 * (der.doy[model.idx_sim] + 1) - 1.39
        )


class Calc_SolarDeclination_V2(modeltools.Method):
    r"""Calculate the solar declination according to :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`SolarDeclination = 0.41 \cdot cos \left(
      \frac{2 \cdot Pi \cdot (DOY - 171)}{365} \right)`

    Examples:

        We define an initialisation period covering both a leap year (2000) and a
        non-leap year (2001):

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2002-01-01", "1d"
        >>> derived.doy.update()

        The following convenience function applies method |Calc_SolarDeclination_V2|
        for the given dates and prints the results:

        >>> def test(*dates):
        ...     for date in dates:
        ...         model.idx_sim = pub.timegrids.init[date]
        ...         model.calc_solardeclination_v2()
        ...         print(date, end=": ")
        ...         round_(factors.solardeclination.value)

        The results are identical for both years:

        >>> test("2000-01-01", "2000-02-28", "2000-02-29",
        ...      "2000-03-01", "2000-12-31")
        2000-01-01: -0.401992
        2000-02-28: -0.149946
        2000-02-29: -0.143355
        2000-03-01: -0.136722
        2000-12-31: -0.401992

        >>> test("2001-01-01", "2001-02-28",
        ...      "2001-03-01", "2001-12-31")
        2001-01-01: -0.401992
        2001-02-28: -0.149946
        2001-03-01: -0.136722
        2001-12-31: -0.401992

        .. testsetup::

            >>> del pub.timegrids
    """

    DERIVEDPARAMETERS = (meteo_derived.DOY,)
    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    RESULTSEQUENCES = (meteo_factors.SolarDeclination,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.solardeclination = 0.41 * modelutils.cos(
            2.0 * fix.pi * (der.doy[model.idx_sim] - 171.0) / 365.0
        )


class Calc_SunsetHourAngle_V1(modeltools.Method):
    r"""Calculate the sunset hour angle according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 25):
      :math:`SunsetHourAngle = arccos(-tan(LatitudeRad) \cdot tan(SolarDeclination))`

    Example:

        The following calculation agrees with example 8 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.doy.shape = 1
        >>> derived.doy(246)
        >>> derived.latituderad(-.35)
        >>> factors.solardeclination = 0.12
        >>> model.calc_sunsethourangle_v1()
        >>> factors.sunsethourangle
        sunsethourangle(1.526767)
    """

    DERIVEDPARAMETERS = (meteo_derived.LatitudeRad,)
    REQUIREDSEQUENCES = (meteo_factors.SolarDeclination,)
    RESULTSEQUENCES = (meteo_factors.SunsetHourAngle,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.sunsethourangle = modelutils.acos(
            -modelutils.tan(der.latituderad) * modelutils.tan(fac.solardeclination)
        )


class Calc_SolarTimeAngle_V1(modeltools.Method):
    r"""Calculate the solar time angle at the midpoint of the current period according
    to :cite:t:`ref-Allen1998`.

    Basic equations (:cite:t:`ref-Allen1998`, equations 31 to 33):
      :math:`SolarTimeAngle =
      Pi / 12 \cdot ((SCT + (Longitude - UTCLongitude) / 15 + S_c) - 12)`

      :math:`S_c = 0.1645 \cdot sin(2 \cdot b) -
      0.1255 \cdot cos(b) - 0.025 \cdot sin(b)`

      :math:`b = (2 \cdot Pi \cdot (DOY - 80)) / 365`

    Note there are two slight deviations from the equations given by
    :cite:t:`ref-Allen1998`.  The first one is that positive numbers correspond to
    longitudes east of Greenwich and negative numbers to longitudes west of Greenwich.
    The second one is due to the definition of parameter |DOY|, as explained in the
    documentation on method |Calc_EarthSunDistance_V1|.

    Examples:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-09-03", "2000-09-04", "1h"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> longitude(15)
        >>> derived.doy.update()
        >>> derived.sct.update()
        >>> derived.utclongitude.update()
        >>> for hour in range(24):
        ...     model.idx_sim = hour
        ...     model.calc_solartimeangle_v1()
        ...     print(hour, end=": ")
        ...     round_(factors.solartimeangle.value)  # doctest: +ELLIPSIS
        0: -3.004157
        1: -2.742358
        ...
        11: -0.124364
        12: 0.137435
        ...
        22: 2.755429
        23: 3.017229

        .. testsetup::

            >>> del pub.timegrids
    """

    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    CONTROLPARAMETERS = (meteo_control.Longitude,)
    DERIVEDPARAMETERS = (
        meteo_derived.DOY,
        meteo_derived.SCT,
        meteo_derived.UTCLongitude,
    )
    RESULTSEQUENCES = (meteo_factors.SolarTimeAngle,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fix = model.parameters.fixed.fastaccess
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        d_b = 2.0 * fix.pi * (der.doy[model.idx_sim] - 80.0) / 365.0
        d_sc = (
            0.1645 * modelutils.sin(2.0 * d_b)
            - 0.1255 * modelutils.cos(d_b)
            - 0.025 * modelutils.sin(d_b)
        )
        d_time = (
            der.sct[model.idx_sim] + (con.longitude - der.utclongitude) / 15.0 + d_sc
        )
        fac.solartimeangle = fix.pi / 12.0 * (d_time - 12.0)


class Calc_TimeOfSunrise_TimeOfSunset_V1(modeltools.Method):
    r"""Calculate the time of sunrise and sunset of the current day according to
    :cite:t:`ref-LARSIM`, based on :cite:t:`ref-Thompson1981`.

    Basic equations:
      :math:`TimeOfSunset^* = \frac{12}{Pi} \cdot acos \left(
      tan(SolarDeclination) \cdot tan(LatitudeRad) +
      \frac{0.0145}{cos(SolarDeclination) \cdot cos(LatitudeRad)} \right)`

      :math:`\delta = \frac{4 \cdot (UTCLongitude - Longitude)}{60}`

      :math:`TimeOfSunset = TimeOfSunset^* + \delta`

      :math:`TimeOfSunset = 24 - TimeOfSunset^* + \delta`

    Examples:

        We calculate the local time of sunrise and sunset for a latitude of
        approximately 52°N and a longitude of 10°E, 5° west of the longitude that
        defines the local time zone:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> longitude(10.0)
        >>> derived.utclongitude(15.0)
        >>> derived.latituderad(0.9)


        The sunshine duration varies between seven hours at the winter solstice and 16
        hours at the summer solstice:

        >>> factors.solardeclination = -0.41
        >>> model.calc_timeofsunrise_timeofsunset_v1()
        >>> factors.timeofsunrise
        timeofsunrise(8.432308)
        >>> factors.timeofsunset
        timeofsunset(16.234359)
        >>> factors.solardeclination = 0.41
        >>> model.calc_timeofsunrise_timeofsunset_v1()
        >>> factors.timeofsunrise
        timeofsunrise(4.002041)
        >>> factors.timeofsunset
        timeofsunset(20.664625)
    """

    CONTROLPARAMETERS = (meteo_control.Longitude,)
    DERIVEDPARAMETERS = (meteo_derived.LatitudeRad, meteo_derived.UTCLongitude)
    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    REQUIREDSEQUENCES = (meteo_factors.SolarDeclination,)
    RESULTSEQUENCES = (meteo_factors.TimeOfSunrise, meteo_factors.TimeOfSunset)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.timeofsunrise = (12.0 / fix.pi) * modelutils.acos(
            modelutils.tan(fac.solardeclination) * modelutils.tan(der.latituderad)
            + 0.0145
            / modelutils.cos(fac.solardeclination)
            / modelutils.cos(der.latituderad)
        )
        fac.timeofsunset = 24.0 - fac.timeofsunrise
        d_dt = (der.utclongitude - con.longitude) * 4.0 / 60.0
        fac.timeofsunrise += d_dt
        fac.timeofsunset += d_dt


class Calc_ExtraterrestrialRadiation_V1(modeltools.Method):
    r"""Calculate the extraterrestrial radiation according to :cite:t:`ref-Allen1998`.

    Basic equation for daily simulation steps (:cite:t:`ref-Allen1998`, equation 21):
      :math:`ExternalTerrestrialRadiation =
      \frac{SolarConstant}{Pi} \cdot EarthSunDistance \cdot (
      SunsetHourAngle \cdot sin(LatitudeRad) \cdot sin(SolarDeclination) +
      cos(LatitudeRad) \cdot cos(SolarDeclination) \cdot sin(SunsetHourAngle))`

    Basic equation for (sub)hourly steps (:cite:t:`ref-Allen1998`, eq. 28 to 30):
      :math:`ExternalTerrestrialRadiation =
      \frac{12 \cdot SolarConstant}{Pi} \cdot EarthSunDistance \cdot \Big(
      (\omega_2 - \omega_1) \cdot sin(LatitudeRad) \cdot sin(SolarDeclination) +
      cos(LatitudeRad) \cdot cos(SolarDeclination) \cdot (sin(\omega_2) -
      sin(\omega_1)) \Big)`

      :math:`\omega_1 = SolarTimeAngle - Pi \cdot Days`

      :math:`\omega_2 = SolarTimeAngle + Pi \cdot Days`

    Examples:

        The following calculation agrees with example 8 of :cite:t:`ref-Allen1998` for
        daily time steps:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.days(1)
        >>> derived.latituderad(-0.35)
        >>> factors.earthsundistance = 0.985
        >>> factors.solardeclination = 0.12
        >>> factors.sunsethourangle = 1.527
        >>> model.calc_extraterrestrialradiation_v1()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(372.473355)

        The following calculation repeats the above example for an hourly simulation
        time step, still covering the whole day:

        >>> import numpy
        >>> longitude(-20)
        >>> derived.utclongitude(-20)
        >>> derived.days(1/24)
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
        6: 116.280258
        7: 431.467206
        8: 713.483659
        9: 943.11066
        10: 1104.699509
        11: 1187.238194
        12: 1185.101838
        13: 1098.436032
        14: 933.146907
        15: 700.498642
        16: 416.345834
        17: 100.053027
        18: 0.0
        19: 0.0
        20: 0.0
        21: 0.0
        22: 0.0
        23: 0.0

        Note that, even with identical values of the local longitude (|Longitude|) and
        the one of the time zone (|UTCLongitude|), the calculated radiation values are
        not symmetrical due to the eccentricity of the Earth"s orbit (see `solar
        time`_).

        There is a slight deviation between the directly calculated daily value and the
        mean of the hourly values:

        >>> round_(sum_/24)
        372.077574

        For sub-daily simulation time steps, results are most accurate for the shortest
        step size.  On the other hand, they can be (extremely) inaccurate for timesteps
        between one hour and one day.  We demonstrate this by comparing the mean
        sub-daily values of different step sizes with the directly calculated daily
        value (note the apparent total fail of method
        |Calc_ExtraterrestrialRadiation_V1| for a step size of 720 minutes):

        >>> for minutes in [1, 5, 15, 30, 60, 90, 120, 144, 160,
        ...                 180, 240, 288, 360, 480, 720, 1440]:
        ...     derived.days(minutes/60/24)
        ...     nmb = int(1440/minutes)
        ...     derived.doy.shape = nmb
        ...     derived.doy(246)
        ...     derived.sct.shape = nmb
        ...     derived.sct = numpy.linspace(minutes/60/2, 24-minutes/60/2, nmb)
        ...     sum_ = 0.0
        ...     for idx in range(nmb):
        ...         model.idx_sim = idx
        ...         model.calc_solartimeangle_v1()
        ...         model.calc_extraterrestrialradiation_v1()
        ...         sum_ += fluxes.extraterrestrialradiation
        ...     print(minutes, end=": ")
        ...     round_(sum_/24 - 372.473355)
        1: -0.000626
        5: -0.008549
        15: -0.100092
        30: -0.395781
        60: -0.395781
        90: -0.395781
        120: -0.395781
        144: -14.43193
        160: -9.539017
        180: -0.395781
        240: -44.735212
        288: -25.486399
        360: -0.395781
        480: -44.735212
        720: -372.473355
        1440: -356.953632
    """

    FIXEDPARAMETERS = (meteo_fixed.Pi, meteo_fixed.SolarConstant)
    DERIVEDPARAMETERS = (meteo_derived.Days, meteo_derived.LatitudeRad)
    REQUIREDSEQUENCES = (
        meteo_factors.SolarTimeAngle,
        meteo_factors.EarthSunDistance,
        meteo_factors.SolarDeclination,
        meteo_factors.SunsetHourAngle,
    )
    RESULTSEQUENCES = (meteo_fluxes.ExtraterrestrialRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fix = model.parameters.fixed.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if der.days < 1.0:
            d_delta = fix.pi * der.days
            d_omega1 = fac.solartimeangle - d_delta
            d_omega2 = fac.solartimeangle + d_delta
            flu.extraterrestrialradiation = max(
                (12.0 * fix.solarconstant / fix.pi * fac.earthsundistance)
                * (
                    (
                        (d_omega2 - d_omega1)
                        * modelutils.sin(der.latituderad)
                        * modelutils.sin(fac.solardeclination)
                    )
                    + (
                        modelutils.cos(der.latituderad)
                        * modelutils.cos(fac.solardeclination)
                        * (modelutils.sin(d_omega2) - modelutils.sin(d_omega1))
                    )
                ),
                0.0,
            )
        else:
            flu.extraterrestrialradiation = (
                fix.solarconstant / fix.pi * fac.earthsundistance
            ) * (
                (
                    fac.sunsethourangle
                    * modelutils.sin(der.latituderad)
                    * modelutils.sin(fac.solardeclination)
                )
                + (
                    modelutils.cos(der.latituderad)
                    * modelutils.cos(fac.solardeclination)
                    * modelutils.sin(fac.sunsethourangle)
                )
            )


class Calc_ExtraterrestrialRadiation_V2(modeltools.Method):
    r"""Calculate the amount of extraterrestrial radiation according to
    :cite:t:`ref-LARSIM`, based on :cite:t:`ref-Thompson1981`.

    Basic equation:
      :math:`ExternalTerrestrialRadiation =
      \frac{SolarConstant \cdot EarthSunDistance \cdot (
      SunsetHourAngle \cdot sin(LatitudeRad) \cdot sin(SolarDeclination) +
      cos(LatitudeRad) \cdot cos(SolarDeclination) \cdot sin(SunsetHourAngle)
      )}{PI}`

      :math:`SunsetHourAngle = (TimeOfSunset - TimeOfSunset) \cdot Pi / 24`

    Examples:

        First, we calculate the extraterrestrial radiation for a latitude of
        approximately 52°N:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.latituderad(0.9)

        The sunshine duration varies between seven hours at the winter solstice and 16
        hours at summer solstice, corresponding to mean daily radiations of 70 and
        514 W/m².

        >>> factors.solardeclination = -0.41
        >>> factors.earthsundistance = 0.97
        >>> factors.timeofsunrise = 8.4
        >>> factors.timeofsunset = 15.6
        >>> model.calc_extraterrestrialradiation_v2()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(70.458396)

        >>> factors.solardeclination = 0.41
        >>> factors.earthsundistance = 1.03
        >>> factors.timeofsunrise = 4.0
        >>> factors.timeofsunset = 20.0
        >>> model.calc_extraterrestrialradiation_v2()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(514.367012)
    """

    DERIVEDPARAMETERS = (meteo_derived.LatitudeRad,)
    FIXEDPARAMETERS = (meteo_fixed.Pi, meteo_fixed.SolarConstant)
    REQUIREDSEQUENCES = (
        meteo_factors.SolarDeclination,
        meteo_factors.EarthSunDistance,
        meteo_factors.TimeOfSunrise,
        meteo_factors.TimeOfSunset,
    )
    RESULTSEQUENCES = (meteo_fluxes.ExtraterrestrialRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_sunsethourangle = (fac.timeofsunset - fac.timeofsunrise) * fix.pi / 24.0
        flu.extraterrestrialradiation = (
            fix.solarconstant * fac.earthsundistance / fix.pi
        ) * (
            d_sunsethourangle
            * modelutils.sin(fac.solardeclination)
            * modelutils.sin(der.latituderad)
            + modelutils.cos(fac.solardeclination)
            * modelutils.cos(der.latituderad)
            * modelutils.sin(d_sunsethourangle)
        )


class Calc_PossibleSunshineDuration_V1(modeltools.Method):
    r"""Calculate the astronomically possible sunshine duration according to
    :cite:t:`ref-Allen1998`.

    Basic equation for daily timesteps :cite:t:`ref-Allen1998` (equation 34):
      :math:`PossibleSunshineDuration = 24 / Pi \cdot SunsetHourAngle`

    Basic equation for (sub)hourly timesteps:
      :math:`PossibleSunshineDuration =
      min(max(12 / Pi \cdot (SunsetHourAngle - \tau), 0), Hours)`

      .. math::
        \tau =
        \begin{cases}
        -SolarTimeAngle - Pi \cdot Days &|\ SolarTimeAngle \leq 0
        \\
        SolarTimeAngle - Pi \cdot Days &|\  SolarTimeAngle > 0
        \end{cases}

    Examples:

        The following calculation agrees with example 9 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.days(1)
        >>> derived.hours(24)
        >>> factors.sunsethourangle(1.527)
        >>> model.calc_possiblesunshineduration_v1()
        >>> factors.possiblesunshineduration
        possiblesunshineduration(11.665421)

        The following calculation repeats the above example for an hourly simulation
        time step, still covering the whole day. Therefore the ratio is only calculated
        during sunrise and sunset and set to 1 at daytime and 0 at nighttime:

        >>> from hydpy import round_
        >>> import numpy
        >>> derived.days(1/24)
        >>> derived.hours(1)
        >>> solartimeangles = numpy.linspace(-3.004157, 3.017229, 24)
        >>> sum_ = 0.
        >>> for hour, solartimeangle in enumerate(solartimeangles):
        ...     factors.solartimeangle = solartimeangle
        ...     model.calc_possiblesunshineduration_v1()
        ...     print(hour, end=": ")  # doctest: +ELLIPSIS
        ...     round_(factors.possiblesunshineduration.value)
        ...     sum_ += factors.possiblesunshineduration.value
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

        The sum of the hourly sunshine durations equals the one-step calculation result:

        >>> round_(sum_)
        11.665421
    """

    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    DERIVEDPARAMETERS = (meteo_derived.Days, meteo_derived.Hours)
    REQUIREDSEQUENCES = (meteo_factors.SolarTimeAngle, meteo_factors.SunsetHourAngle)
    RESULTSEQUENCES = (meteo_factors.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fix = model.parameters.fixed.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        if der.hours < 24.0:
            if fac.solartimeangle <= 0.0:
                d_thresh = -fac.solartimeangle - fix.pi * der.days
            else:
                d_thresh = fac.solartimeangle - fix.pi * der.days
            fac.possiblesunshineduration = min(
                max(12.0 / fix.pi * (fac.sunsethourangle - d_thresh), 0.0), der.hours
            )
        else:
            fac.possiblesunshineduration = 24.0 / fix.pi * fac.sunsethourangle


class Calc_PossibleSunshineDuration_V2(modeltools.Method):
    r"""Calculate the astronomically possible sunshine duration according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`PossibleSunshineDuration = max \bigl(
      max(SCT-Hours/2, TimeOfSunrise) - min(SCT + Hours / 2, TimeOfSunset), 0 \bigr)`

    Examples:

        We focus on winter conditions with a relatively short possible sunshine
        duration:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> factors.timeofsunrise(8.4)
        >>> factors.timeofsunset(15.6)

        We start with a daily simulation time step.  The possible sunshine duration is,
        as expected, the span between sunrise and sunset:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> model.calc_possiblesunshineduration_v2()
        >>> factors.possiblesunshineduration
        possiblesunshineduration(7.2)

        The following example calculates the possible hourly sunshine durations of the
        same day:

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> sum_ = 0.0
        >>> for idx in range(24):
        ...     model.idx_sim = idx
        ...     model.calc_possiblesunshineduration_v2()
        ...     print(idx+1, end=": ")   # doctest: +ELLIPSIS
        ...     round_(factors.possiblesunshineduration.value)
        ...     sum_ += factors.possiblesunshineduration.value
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

        The sum of the possible hourly sunshine durations equals the daily possible
        sunshine, of course:

        >>> round_(sum_)
        7.2

        .. testsetup::

            >>> del pub.timegrids
    """

    DERIVEDPARAMETERS = (meteo_derived.SCT, meteo_derived.Hours)
    REQUIREDSEQUENCES = (meteo_factors.TimeOfSunrise, meteo_factors.TimeOfSunset)
    RESULTSEQUENCES = (meteo_factors.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        d_stc = der.sct[model.idx_sim]
        d_t0 = max((d_stc - der.hours / 2.0), fac.timeofsunrise)
        d_t1 = min((d_stc + der.hours / 2.0), fac.timeofsunset)
        fac.possiblesunshineduration = max(d_t1 - d_t0, 0.0)


class Calc_DailyPossibleSunshineDuration_V1(modeltools.Method):
    """Calculate the astronomically possible daily sunshine duration.

    Basic equation:
      :math:`DailyPossibleSunshineDuration =  TimeOfSunset - TimeOfSunrise`

    Examples:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> factors.timeofsunrise(8.4)
        >>> factors.timeofsunset(15.6)
        >>> model.calc_dailypossiblesunshineduration()
        >>> factors.dailypossiblesunshineduration
        dailypossiblesunshineduration(7.2)
    """

    REQUIREDSEQUENCES = (meteo_factors.TimeOfSunrise, meteo_factors.TimeOfSunset)
    RESULTSEQUENCES = (meteo_factors.DailyPossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.dailypossiblesunshineduration = fac.timeofsunset - fac.timeofsunrise


class Update_LoggedSunshineDuration_V1(modeltools.Method):
    """Log the sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.meteo import *
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

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_inputs.SunshineDuration,)
    UPDATEDSEQUENCES = (meteo_logs.LoggedSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedsunshineduration[idx] = log.loggedsunshineduration[idx - 1]
        log.loggedsunshineduration[0] = inp.sunshineduration


class Update_LoggedGlobalRadiation_V1(modeltools.Method):
    """Log the global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedglobalradiation.shape = 3
        >>> logs.loggedglobalradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedglobalradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.globalradiation,
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

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_inputs.GlobalRadiation,)
    UPDATEDSEQUENCES = (meteo_logs.LoggedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedglobalradiation[idx] = log.loggedglobalradiation[idx - 1]
        log.loggedglobalradiation[0] = inp.globalradiation


class Calc_DailySunshineDuration_V1(modeltools.Method):
    """Calculate the sunshine duration sum of the last 24 hours.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsunshineduration.shape = 3
        >>> logs.loggedsunshineduration = 1.0, 5.0, 3.0
        >>> model.calc_dailysunshineduration_v1()
        >>> factors.dailysunshineduration
        dailysunshineduration(9.0)
    """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_logs.LoggedSunshineDuration,)
    UPDATEDSEQUENCES = (meteo_factors.DailySunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.dailysunshineduration = 0.0
        for idx in range(der.nmblogentries):
            fac.dailysunshineduration += log.loggedsunshineduration[idx]


class Calc_DailyGlobalRadiation_V2(modeltools.Method):
    """Calculate the global radiation sum of the last 24 hours.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedglobalradiation.shape = 3
        >>> logs.loggedglobalradiation = 100.0, 800.0, 600.0
        >>> model.calc_dailyglobalradiation_v2()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(500.0)
    """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_logs.LoggedGlobalRadiation,)
    UPDATEDSEQUENCES = (meteo_fluxes.DailyGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailyglobalradiation = 0.0
        for idx in range(der.nmblogentries):
            flu.dailyglobalradiation += log.loggedglobalradiation[idx]
        flu.dailyglobalradiation /= der.nmblogentries


class Calc_PortionDailyRadiation_V1(modeltools.Method):
    r"""Calculate the relative sum of radiation according to :cite:t:`ref-LARSIM-Hilfe`.

    Basic equations:

      .. math::
        SP = S_P^*(SCT + Hours/2) - S_P^*(SCT - Hours/2)

      .. math::
        S_P^*(t) = \begin{cases}
        0
        &|\
        TL_P(t) \leq 0
        \\
        50 - 50 \cdot cos\bigl(1.8 \cdot TL_P(t)\bigr) -
        3.4 \cdot sin\bigl(3.6 \cdot TL_P(t)\bigr)^2
        &|\
        0 < TL_P(t) \leq 50 \cdot \frac{2 \cdot Pi}{360}
        \\
        50 - 50 \cdot cos\bigl(1.8 \cdot TL_P(t)\bigr) +
        3.4 \cdot sin\bigl(3.6 \cdot TL_P(t)\bigr)^2
        &|\
        50 \cdot \frac{2 \cdot Pi}{360} < TL_P(t) <
        100 \cdot \frac{2 \cdot Pi}{360}
        \\
        100
        &|\
        100 \cdot \frac{2 \cdot Pi}{360} \leq TL_P(t)
        \end{cases}

      .. math::
        TL_P(t) = 100 \cdot \frac{2 \cdot Pi}{360} \cdot
        \frac{t - TimeOfSunrise}{TimeOfSunset - TimeOfSunrise}

    Examples:

        We focus on winter conditions with a relatively short possible
        sunshine duration:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> factors.timeofsunrise(8.4)
        >>> factors.timeofsunset(15.6)

        We start with an hourly simulation time step.  The relative radiation sum is,
        as expected, zero before sunrise and after sunset.  In between, it reaches its
        maximum around noon:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(7, 17):
        ...     model.idx_sim = idx
        ...     model.calc_portiondailyradiation_v1()
        ...     print(idx+1, end=": ")
        ...     round_(factors.portiondailyradiation.value)
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

        The following examples show how method |Calc_PortionDailyRadiation_V1| works
        for time step sizes longer than one hour:

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> model.idx_sim = 0
        >>> model.calc_portiondailyradiation_v1()
        >>> factors.portiondailyradiation
        portiondailyradiation(100.0)

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "6h"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(4):
        ...     model.idx_sim = idx
        ...     model.calc_portiondailyradiation_v1()
        ...     print((idx+1)*6, end=": ")
        ...     round_(factors.portiondailyradiation.value)
        6: 0.0
        12: 50.0
        18: 50.0
        24: 0.0

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "3h"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(8):
        ...     model.idx_sim = idx
        ...     model.calc_portiondailyradiation_v1()
        ...     print((idx+1)*3, end=": ")
        ...     round_(factors.portiondailyradiation.value)
        3: 0.0
        6: 0.0
        9: 0.853709
        12: 49.146291
        15: 49.146291
        18: 0.853709
        21: 0.0
        24: 0.0

        Often, method |Calc_PortionDailyRadiation_V1| calculates a small but
        unrealistic "bump" around noon (for example, the relative radiation is slightly
        smaller between 11:30 and 12:00 than it is between 11:00 and 11:30):

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "30m"
        >>> derived.sct.update()
        >>> derived.hours.update()
        >>> for idx in range(15, 33):
        ...     model.idx_sim = idx
        ...     model.calc_portiondailyradiation_v1()
        ...     print((idx+1)/2, end=": ")
        ...     round_(factors.portiondailyradiation.value)
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

    DERIVEDPARAMETERS = (meteo_derived.SCT, meteo_derived.Hours)
    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    REQUIREDSEQUENCES = (meteo_factors.TimeOfSunrise, meteo_factors.TimeOfSunset)
    RESULTSEQUENCES = (meteo_factors.PortionDailyRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        d_fac = 2.0 * fix.pi / 360.0
        fac.portiondailyradiation = 0.0
        for i in range(2):
            if i:
                d_dt = der.hours / 2.0
            else:
                d_dt = -der.hours / 2.0
            d_tlp = (100.0 * d_fac) * (
                (der.sct[model.idx_sim] + d_dt - fac.timeofsunrise)
                / (fac.timeofsunset - fac.timeofsunrise)
            )
            if d_tlp <= 0.0:
                d_p = 0.0
            elif d_tlp < 100.0 * d_fac:
                d_p = 50.0 - 50.0 * modelutils.cos(1.8 * d_tlp)
                d_temp = 3.4 * modelutils.sin(3.6 * d_tlp) ** 2
                if d_tlp <= 50.0 * d_fac:
                    d_p -= d_temp
                else:
                    d_p += d_temp
            else:
                d_p = 100.0
            if i:
                fac.portiondailyradiation += d_p
            else:
                fac.portiondailyradiation -= d_p


class Return_DailyGlobalRadiation_V1(modeltools.Method):
    r"""Calculate and return the daily global radiation according to
    :cite:t:`ref-LARSIM`.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      .. math::
        ExtraterrestrialRadiation \cdot \begin{cases}
        AngstromConstant + AngstromFactor \cdot
        \frac{sunshineduration}{possiblesunshineduration}
        &|\
        sunshineduration > 0 \;\; \lor \;\; Days < 1
        \\
        AngstromAlternative
        &|\
        sunshineduration = 0 \;\; \land \;\; Days \geq 1
        \end{cases}

    Example:

        You can define month-specific Angstrom coefficients to reflect the annual
        variability in the relationship between sunshine duration and global radiation.
        First, we demonstrate this on a daily timestep basis:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromalternative.jan = 0.2
        >>> angstromconstant.feb = 0.2
        >>> angstromfactor.feb = 0.6
        >>> angstromalternative.feb = 0.3
        >>> fluxes.extraterrestrialradiation = 340.0
        >>> model.idx_sim = 1
        >>> round_(model.return_dailyglobalradiation_v1(0.6, 1.0))
        136.0
        >>> model.idx_sim = 2
        >>> round_(model.return_dailyglobalradiation_v1(0.6, 1.0))
        190.4

        If the possible sunshine duration is zero, we generally set global radiation to
        zero (even if the actual sunshine duration is larger than zero, which might
        occur as a result of inconsistencies between measured and calculated input
        data):

        >>> round_(model.return_dailyglobalradiation_v1(0.6, 0.0))
        0.0

        When actual sunshine is zero, the alternative Ångström coefficient applies:

        >>> model.idx_sim = 1
        >>> round_(model.return_dailyglobalradiation_v1(0.0, 1.0))
        68.0
        >>> model.idx_sim = 2
        >>> round_(model.return_dailyglobalradiation_v1(0.0, 1.0))
        102.0

        All of the examples and explanations above hold for short simulation timesteps,
        except that |AngstromAlternative| never replaces |AngstromConstant|:

        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1h"
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> model.idx_sim = 1
        >>> round_(model.return_dailyglobalradiation_v1(0.0, 1.0))
        34.0

        .. testsetup::

            >>> del pub.timegrids
        """

    CONTROLPARAMETERS = (
        meteo_control.AngstromConstant,
        meteo_control.AngstromFactor,
        meteo_control.AngstromAlternative,
    )
    DERIVEDPARAMETERS = (meteo_derived.MOY, meteo_derived.Days)
    REQUIREDSEQUENCES = (meteo_fluxes.ExtraterrestrialRadiation,)

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


class Calc_ClearSkySolarRadiation_V1(modeltools.Method):
    r"""Calculate the clear sky solar radiation according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t`ref-Allen1998`, eq. 35):
      :math:`ClearSkySolarRadiation =
      ExtraterrestrialRadiation \cdot (AngstromConstant + AngstromFactor)`

    Example:

        We use the Ångström coefficients (a=0.19, b=0.55) recommended for Germany by
        DVWK-M 504 :cite:t:`ref-DVWK` for January and the default values (a=0.25, b=0.5)
        for February:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> angstromconstant.jan = 0.19
        >>> angstromfactor.jan = 0.55
        >>> angstromconstant.feb = 0.25
        >>> angstromfactor.feb = 0.5
        >>> derived.moy.update()
        >>> fluxes.extraterrestrialradiation = 200.0
        >>> model.idx_sim = 1
        >>> model.calc_clearskysolarradiation_v1()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(148.0)
        >>> model.idx_sim = 2
        >>> model.calc_clearskysolarradiation_v1()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(150.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (meteo_control.AngstromConstant, meteo_control.AngstromFactor)
    DERIVEDPARAMETERS = (meteo_derived.MOY,)
    REQUIREDSEQUENCES = (meteo_fluxes.ExtraterrestrialRadiation,)
    RESULTSEQUENCES = (meteo_fluxes.ClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        idx = der.moy[model.idx_sim]
        flu.clearskysolarradiation = flu.extraterrestrialradiation * (
            con.angstromconstant[idx] + con.angstromfactor[idx]
        )


class Calc_GlobalRadiation_V1(modeltools.Method):
    r"""Calculate the global radiation according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 35):
      :math:`GlobalRadiation = ExtraterrestrialRadiation \cdot (AngstromConstant +
      AngstromFactor \cdot SunshineDuration / PossibleSunshineDuration)`

    Example:

        We use the Ångström coefficients (a=0.19, b=0.55) recommended for Germany by
        DVWK-M 504 :cite:t:`ref-DVWK` for January and the default values (a=0.25, b=0.5)
        for February:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> angstromconstant.jan = 0.19
        >>> angstromfactor.jan = 0.55
        >>> angstromconstant.feb = 0.25
        >>> angstromfactor.feb = 0.5
        >>> derived.moy.update()
        >>> inputs.sunshineduration = 12.0
        >>> factors.possiblesunshineduration = 14.0
        >>> fluxes.extraterrestrialradiation = 200.0
        >>> model.idx_sim = 1
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(132.285714)
        >>> model.idx_sim = 2
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(135.714286)

        For zero possible sunshine durations, |Calc_GlobalRadiation_V1| sets
        |meteo_fluxes.GlobalRadiation| to zero:

        >>> factors.possiblesunshineduration = 0.0
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (meteo_control.AngstromConstant, meteo_control.AngstromFactor)
    DERIVEDPARAMETERS = (meteo_derived.MOY,)
    REQUIREDSEQUENCES = (
        meteo_inputs.SunshineDuration,
        meteo_factors.PossibleSunshineDuration,
        meteo_fluxes.ExtraterrestrialRadiation,
    )
    RESULTSEQUENCES = (meteo_fluxes.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        fac = model.sequences.factors.fastaccess
        if fac.possiblesunshineduration > 0.0:
            idx = der.moy[model.idx_sim]
            flu.globalradiation = flu.extraterrestrialradiation * (
                con.angstromconstant[idx]
                + con.angstromfactor[idx]
                * inp.sunshineduration
                / fac.possiblesunshineduration
            )
        else:
            flu.globalradiation = 0.0


class Calc_UnadjustedGlobalRadiation_V1(modeltools.Method):
    r"""Calculate the unadjusted global radiation according to :cite:t:`ref-LARSIM`.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      .. math::
        UnadjustedGlobalRadiation =
        NmbLogEntries \cdot \frac{SP}{100} \cdot \begin{cases}
        Return\_DailyGlobalRadiation\_V1(
        SunshineDuration, PossibleSunshineDuration)
        &|\
        PossibleSunshineDuration > 0
        \\
        Return\_DailyGlobalRadiation\_V1(
        DailySunshineDuration, DailyPossibleSunshineDuration)
        &|\
        PossibleSunshineDuration = 0
        \end{cases}

    Examples:

        Method |Calc_UnadjustedGlobalRadiation_V1| uses the actual value of
        |PortionDailyRadiation| and method |Return_DailyGlobalRadiation_V1| to
        calculate global radiation according to the current values of
        |meteo_inputs.SunshineDuration| and |meteo_factors.PossibleSunshineDuration|:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-31", "2000-02-02", "6h"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromalternative.jan = 0.2
        >>> inputs.sunshineduration = 0.6
        >>> factors.possiblesunshineduration = 1.0
        >>> fluxes.extraterrestrialradiation = 340.0
        >>> factors.portiondailyradiation = 50.0
        >>> model.idx_sim = 3
        >>> model.calc_unadjustedglobalradiation_v1()
        >>> fluxes.unadjustedglobalradiation
        unadjustedglobalradiation(272.0)

        During nighttime periods, the value of |meteo_factors.PossibleSunshineDuration|
        is zero.  Then, |Calc_GlobalRadiation_V1| uses the values of
        |DailySunshineDuration| and |DailyPossibleSunshineDuration| as surrogates:

        >>> factors.possiblesunshineduration = 0.0
        >>> factors.dailysunshineduration = 4.0
        >>> factors.dailypossiblesunshineduration = 10.0
        >>> model.calc_unadjustedglobalradiation_v1()
        >>> fluxes.unadjustedglobalradiation
        unadjustedglobalradiation(204.0)

        .. testsetup::

            >>> del pub.timegrids
        """

    SUBMETHODS = (Return_DailyGlobalRadiation_V1,)
    CONTROLPARAMETERS = (
        meteo_control.AngstromConstant,
        meteo_control.AngstromFactor,
        meteo_control.AngstromAlternative,
    )
    DERIVEDPARAMETERS = (
        meteo_derived.NmbLogEntries,
        meteo_derived.MOY,
        meteo_derived.Days,
    )
    REQUIREDSEQUENCES = (
        meteo_inputs.SunshineDuration,
        meteo_factors.PossibleSunshineDuration,
        meteo_factors.DailySunshineDuration,
        meteo_factors.DailyPossibleSunshineDuration,
        meteo_factors.PortionDailyRadiation,
        meteo_fluxes.ExtraterrestrialRadiation,
    )
    RESULTSEQUENCES = (meteo_fluxes.UnadjustedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if fac.possiblesunshineduration > 0.0:
            d_act = inp.sunshineduration
            d_pos = fac.possiblesunshineduration
        else:
            d_act = fac.dailysunshineduration
            d_pos = fac.dailypossiblesunshineduration
        flu.unadjustedglobalradiation = (
            der.nmblogentries * fac.portiondailyradiation / 100.0
        ) * model.return_dailyglobalradiation_v1(d_act, d_pos)


class Adjust_ClearSkySolarRadiation_V1(modeltools.Method):
    r"""Use the portion of the daily radiation sum to adjust the clear sky solar
    radiation's daily average to the current simulation step.

    Basic equation:
      .. math::
        C_{new} = N \cdot P / 100 \cdot C_{old}
        \\ \\
        C = ClearSkySolarRadiation \\
        N = NmbLogEntries \\
        P = PortionDailyRadiation

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.nmblogentries(4)
        >>> factors.portiondailyradiation = 10.0
        >>> fluxes.clearskysolarradiation = 200.0
        >>> model.adjust_clearskysolarradiation_v1()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(80.0)
        """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_factors.PortionDailyRadiation,)
    UPDATEDSEQUENCES = (meteo_fluxes.ClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.clearskysolarradiation *= (
            der.nmblogentries * fac.portiondailyradiation / 100.0
        )


class Update_LoggedUnadjustedGlobalRadiation_V1(modeltools.Method):
    """Log the unadjusted global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.meteo import *
        >>> simulationstep("8h")
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> logs.loggedunadjustedglobalradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedunadjustedglobalradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.unadjustedglobalradiation,
        ...                          logs.loggedunadjustedglobalradiation))
        >>> test.nexts.unadjustedglobalradiation = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedunadjustedglobalradiation
        >>> test()
        | ex. | unadjustedglobalradiation |           loggedunadjustedglobalradiation |
        -------------------------------------------------------------------------------
        |   1 |                       1.0 | 1.0  0.0                              0.0 |
        |   2 |                       3.0 | 3.0  1.0                              0.0 |
        |   3 |                       2.0 | 2.0  3.0                              1.0 |
        |   4 |                       4.0 | 4.0  2.0                              3.0 |
    """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_fluxes.UnadjustedGlobalRadiation,)
    UPDATEDSEQUENCES = (meteo_logs.LoggedUnadjustedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedunadjustedglobalradiation[idx] = (
                log.loggedunadjustedglobalradiation[idx - 1]
            )
        log.loggedunadjustedglobalradiation[0] = flu.unadjustedglobalradiation


class Calc_DailyGlobalRadiation_V1(modeltools.Method):
    r"""Calculate the daily global radiation.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`DailyGlobalRadiation = Return\_DailyGlobalRadiation\_V1(
      DailySunshineDuration, DailyPossibleSunshineDuration)`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromconstant.feb = 0.2
        >>> angstromfactor.feb = 0.6

        We set the extraterrestrial radiation to 200 W/m² and the possible sunshine
        duration to 12 hours:

        >>> fluxes.extraterrestrialradiation = 200.0
        >>> factors.dailypossiblesunshineduration = 12.0

        We define a daily simulation step size and update the relevant derived
        parameters:

        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> derived.moy.update()

        Applying the Ångström coefficients for January and February on the defined
        extraterrestrial radiation and a sunshine duration of 7.2 hours results in a
        daily global radiation average of 80 and 112 W/m², respectively:

        >>> model.idx_sim = 1
        >>> factors.dailysunshineduration = 7.2
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(80.0)

        >>> model.idx_sim = 2
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(112.0)

        Finally, we demonstrate for January that method |Calc_DailyGlobalRadiation_V1|
        calculates the same values for an hourly simulation time step, as long as the
        daily sum of sunshine duration remains identical:

        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1h"
        >>> derived.moy.update()

        The actual simulation step starts at 11 o'clock and ends at 12 o'clock:

        >>> model.idx_sim = pub.timegrids.init["2000-01-31 11:00"]
        >>> factors.dailysunshineduration = 7.2
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(80.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = (Return_DailyGlobalRadiation_V1,)
    CONTROLPARAMETERS = (
        meteo_control.AngstromConstant,
        meteo_control.AngstromFactor,
        meteo_control.AngstromAlternative,
    )
    DERIVEDPARAMETERS = (meteo_derived.MOY, meteo_derived.Days)
    REQUIREDSEQUENCES = (
        meteo_factors.DailySunshineDuration,
        meteo_factors.DailyPossibleSunshineDuration,
        meteo_fluxes.ExtraterrestrialRadiation,
    )
    UPDATEDSEQUENCES = (meteo_fluxes.DailyGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailyglobalradiation = model.return_dailyglobalradiation_v1(
            fac.dailysunshineduration, fac.dailypossiblesunshineduration
        )


class Return_SunshineDuration_V1(modeltools.Method):
    r"""Calculate the sunshine duration reversely to |Return_DailyGlobalRadiation_V1|
    and return it.

    Basic equation:
      :math:`\frac{possiblesunshineduration}{AngstromFactor} \cdot \left(
      \frac{globalradiation}{extraterrestrialradiation} - AngstromConstant \right)`

    Example:

        Essentially, |Return_SunshineDuration_V1| tries to invert
        |Return_DailyGlobalRadiation_V1| and thus also relies on the Ångström formula.
        Instead of estimating global radiation from sunshine duration, it estimates
        sunshine duration from global radiation.  We demonstrate this by repeating the
        first examples of |Calc_GlobalRadiation_V1| "backwards":

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.moy.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromalternative.jan = 0.2
        >>> angstromconstant.feb = 0.2
        >>> angstromfactor.feb = 0.6
        >>> angstromalternative.feb = 0.3
        >>> model.idx_sim = 1
        >>> round_(model.return_sunshineduration_v1(136.0, 340.0, 1.0))
        0.6
        >>> model.idx_sim = 2
        >>> round_(model.return_sunshineduration_v1(190.4, 340.0, 1.0))
        0.6

        In contrast to |Return_DailyGlobalRadiation_V1|, |Return_SunshineDuration_V1|
        never applies |AngstromAlternative| instead of |AngstromConstant|.  Hence, as
        in the following repeated examples, |Return_SunshineDuration_V1| might invert
        |Return_DailyGlobalRadiation_V1| only roughly during periods with little
        sunshine:

        >>> model.idx_sim = 1
        >>> round_(model.return_sunshineduration_v1(68.0, 340.0, 1.0))
        0.2
        >>> model.idx_sim = 2
        >>> round_(model.return_sunshineduration_v1(102.0, 340.0, 1.0))
        0.166667

        We must consider additional corner cases.  The first one deals with a potential
        zero division during nighttime.  If extraterrestrial radiation is zero,
        |Return_SunshineDuration_V1| takes the astronomically possible sunshine
        duration (which should ideally also be zero) as the actual sunshine duration:

        >>> model.idx_sim = 1
        >>> round_(model.return_sunshineduration_v1(136.0, 0.0, 0.00001))
        0.00001

        Measured global radiation smaller than estimated diffusive radiation would
        result in negative sunshine durations when following the Ångström formula
        strictly.  Additionally, measured global radiation larger than estimated
        clear-sky radiation would result in sunshine durations larger than the
        astronomically possible sunshine duration.  The following example shows that
        method |Return_SunshineDuration_V1| prevents such inconsistencies by trimming
        the estimated sunshine duration when necessary:

        >>> for globrad in (0.0, 34.0, 35.0, 136.0, 203.0, 204.0, 340.0):
        ...     sundur = model.return_sunshineduration_v1(globrad, 340.0, 1.0)
        ...     round_((globrad, sundur))
        0.0, 0.0
        34.0, 0.0
        35.0, 0.005882
        136.0, 0.6
        203.0, 0.994118
        204.0, 1.0
        340.0, 1.0

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = ()
    CONTROLPARAMETERS = (meteo_control.AngstromConstant, meteo_control.AngstromFactor)
    DERIVEDPARAMETERS = (meteo_derived.MOY,)

    @staticmethod
    def __call__(
        model: modeltools.Model,
        globalradiation: float,
        extraterrestrialradiation: float,
        possiblesunshineduration: float,
    ) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        if extraterrestrialradiation <= 0.0:
            return possiblesunshineduration
        idx = der.moy[model.idx_sim]
        d_sd = (possiblesunshineduration / con.angstromfactor[idx]) * (
            globalradiation / extraterrestrialradiation - con.angstromconstant[idx]
        )
        return min(max(d_sd, 0.0), possiblesunshineduration)


class Calc_UnadjustedSunshineDuration_V1(modeltools.Method):
    r"""Calculate the unadjusted sunshine duration reversely to
    |Calc_UnadjustedGlobalRadiation_V1|.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`UnadjustedSunshineDuration = Return\_SunshineDuration
      \left( GlobalRadiation, NmbLogEntries \cdot \frac{PortionDailyRadiation}{100}
      \cdot ExtraterrestrialRadiation, PossibleSunshineDuration \right)`

    Example:

        Method |Calc_UnadjustedSunshineDuration_V1| relies on
        |Return_SunshineDuration_V1| and thus has the same limitation regarding periods
        with little sunshine.  See its documentation for further information.  Here, we
        only demonstrate the proper passing of |meteo_inputs.GlobalRadiation|,
        |ExtraterrestrialRadiation| (eventually reduced by |PortionDailyRadiation|) and
        |meteo_factors.PossibleSunshineDuration|:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-31", "2000-02-02", "6h"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> derived.moy.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> inputs.globalradiation = 272.0
        >>> factors.possiblesunshineduration = 1.0
        >>> factors.portiondailyradiation = 50.0
        >>> fluxes.extraterrestrialradiation = 340.0
        >>> model.idx_sim = 3
        >>> model.calc_unadjustedsunshineduration_v1()
        >>> factors.unadjustedsunshineduration
        unadjustedsunshineduration(0.6)

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = (Return_SunshineDuration_V1,)
    CONTROLPARAMETERS = (meteo_control.AngstromConstant, meteo_control.AngstromFactor)
    DERIVEDPARAMETERS = (meteo_derived.MOY, meteo_derived.NmbLogEntries)
    REQUIREDSEQUENCES = (
        meteo_inputs.GlobalRadiation,
        meteo_factors.PossibleSunshineDuration,
        meteo_factors.PortionDailyRadiation,
        meteo_fluxes.ExtraterrestrialRadiation,
    )
    RESULTSEQUENCES = (meteo_factors.UnadjustedSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        fac.unadjustedsunshineduration = model.return_sunshineduration_v1(
            inp.globalradiation,
            flu.extraterrestrialradiation
            * der.nmblogentries
            * fac.portiondailyradiation
            / 100.0,
            fac.possiblesunshineduration,
        )


class Calc_GlobalRadiation_V2(modeltools.Method):
    r"""Adjust the current global radiation to the daily global radiation according to
     :cite:t:`ref-LARSIM`.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`GlobalRadiation = UnadjustedGlobalRadiation \cdot
      \frac{DailyGlobalRadiation}{\sum LoggedUnadjustedGlobalRadiation / NmbLogEntries}`

    Examples:

        The purpose of method |Calc_GlobalRadiation_V2| is to adjust hourly global
        radiation values (or those of other short simulation time steps) so that their
        mean over the last 24 hours equals the global radiation value directly
        calculated with the relative sunshine duration over the last 24 hours.  We try
        to explain this somewhat counterintuitive approach by extending the
        documentation examples on method |Calc_DailyGlobalRadiation_V1|.

        Again, we start with a daily simulation time step:

        >>> from hydpy.models.meteo import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> derived.nmblogentries.update()

        For such a daily simulation time step, the values of the sequences
        |UnadjustedGlobalRadiation|, |DailyGlobalRadiation|, and
        |LoggedUnadjustedGlobalRadiation| must be identical:

        >>> model.idx_sim = 1
        >>> fluxes.unadjustedglobalradiation = 200.0
        >>> fluxes.dailyglobalradiation = 200.0
        >>> logs.loggedunadjustedglobalradiation = 200.0

        After calling |Calc_GlobalRadiation_V2|, the same holds for the adjusted global
        radiation sum:

        >>> model.calc_globalradiation_v2()
        >>> fluxes.globalradiation
        globalradiation(200.0)

        Intuitively, one would not expect method |Calc_GlobalRadiation_V2| to have any
        effect when applied on daily simulation time steps at all.  However, it
        corrects "wrong" predefined global radiation values:

        >>> fluxes.dailyglobalradiation = 280.0
        >>> model.calc_globalradiation_v2()
        >>> fluxes.globalradiation
        globalradiation(280.0)

        We now demonstrate how method |Calc_GlobalRadiation_V2| works for hourly
        simulation time steps:

        >>> simulationstep("1h")
        >>> derived.nmblogentries.update()

        The daily global radiation value does not depend on the simulation timestep.
        We reset it to 200 W/m²:

        >>> fluxes.dailyglobalradiation = 200.0

        The other global radiation values must be smaller and vary throughout the day.
        We set them in agreement with the logged sunshine duration specified in the
        documentation on method |Calc_DailyGlobalRadiation_V1|:

        >>> fluxes.unadjustedglobalradiation = 960.0
        >>> logs.loggedunadjustedglobalradiation = (
        ...     960.0, 960.0, 240.0, 120.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 120.0, 480.0, 720.0, 840.0, 960.0)

        Compared with the total 24 hours, the simulation time steps around noon are
        relatively sunny, both for the current and the last day (see the first and the
        last entry of the log sequence for the sunshine duration).  Accordingly, the
        hourly global radiation values' mean (230 W/m²) is larger than the directly
        calculated daily mean (200 W/m²).  Method |Calc_GlobalRadiation_V2| uses the
        fraction of both sums to calculate the adjusted global radiation
        (:math:`960 \cdot 200 / 230`):

        >>> model.calc_globalradiation_v2()
        >>> fluxes.globalradiation
        globalradiation(834.782609)
    """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        meteo_fluxes.UnadjustedGlobalRadiation,
        meteo_fluxes.DailyGlobalRadiation,
        meteo_logs.LoggedUnadjustedGlobalRadiation,
    )
    RESULTSEQUENCES = (meteo_fluxes.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        d_glob_sum = 0.0
        for idx in range(der.nmblogentries):
            d_glob_sum += log.loggedunadjustedglobalradiation[idx]
        d_glob_mean = d_glob_sum / der.nmblogentries
        flu.globalradiation = (
            flu.unadjustedglobalradiation * flu.dailyglobalradiation / d_glob_mean
        )


class Calc_SunshineDuration_V1(modeltools.Method):
    r"""Calculate the sunshine duration according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 35, rearranged):
      :math:`SunshineDuration =
      \left(\frac{GlobalRadiation}{ExtraterrestrialRadiation}-AngstromConstant \right)
      \cdot \frac{PossibleSunshineDuration}{AngstromFactor}`

    Example:

        Essentially, |Calc_SunshineDuration_V1| inverts |Calc_GlobalRadiation_V1| and
        thus also relies on the Ångström formula.  Instead of estimating global
        radiation from sunshine duration, it estimates global radiation from sunshine
        duration.  We demonstrate this by repeating the examples of
        |Calc_GlobalRadiation_V1| "backwards":

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> angstromconstant.jan = 0.19
        >>> angstromfactor.jan = 0.55
        >>> angstromconstant.feb = 0.25
        >>> angstromfactor.feb = 0.5
        >>> derived.moy.update()
        >>> factors.possiblesunshineduration = 14.0
        >>> fluxes.extraterrestrialradiation = 200.0
        >>> model.idx_sim = 1
        >>> inputs.globalradiation = 132.285714
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(12.0)
        >>> model.idx_sim = 2
        >>> inputs.globalradiation = 135.714286
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(12.0)

        |Calc_SunshineDuration_V1| sets |meteo_factors.SunshineDuration| to zero for
        zero extraterrestrial radiation:

        >>> fluxes.extraterrestrialradiation = 0.0
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(0.0)

        Inconsistencies between global radiation measurements and the Ångström formula
        (and the selected coefficients) can result in unrealistic sunshine duration
        estimates.  Method |Calc_SunshineDuration_V1| reduces this problem by lowering
        too high values to the possible sunshine duration and increasing too low values
        to zero:

        >>> fluxes.extraterrestrialradiation = 200.0
        >>> inputs.globalradiation = 210.0
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(14.0)

        >>> inputs.globalradiation = 0.0
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (meteo_control.AngstromConstant, meteo_control.AngstromFactor)
    DERIVEDPARAMETERS = (meteo_derived.MOY,)
    REQUIREDSEQUENCES = (
        meteo_inputs.GlobalRadiation,
        meteo_factors.PossibleSunshineDuration,
        meteo_fluxes.ExtraterrestrialRadiation,
    )
    RESULTSEQUENCES = (meteo_factors.SunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        fac = model.sequences.factors.fastaccess
        if flu.extraterrestrialradiation > 0.0:
            idx = der.moy[model.idx_sim]
            d_sd = (
                (inp.globalradiation / flu.extraterrestrialradiation)
                - con.angstromconstant[idx]
            ) * (fac.possiblesunshineduration / con.angstromfactor[idx])
            fac.sunshineduration = min(max(d_sd, 0.0), fac.possiblesunshineduration)
        else:
            fac.sunshineduration = 0.0


class Update_LoggedUnadjustedSunshineDuration_V1(modeltools.Method):
    """Log the unadjusted sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.meteo import *
        >>> simulationstep("8h")
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> logs.loggedunadjustedsunshineduration = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedunadjustedsunshineduration_v1,
        ...                 last_example=4,
        ...                 parseqs=(factors.unadjustedsunshineduration,
        ...                          logs.loggedunadjustedsunshineduration))
        >>> test.nexts.unadjustedsunshineduration = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedunadjustedsunshineduration
        >>> test()  # doctest: +ELLIPSIS
        | ex. | unadjustedsunshineduration | ... loggedunadjustedsunshineduration |
        -------------------------------------...-----------------------------------
        |   1 |                        1.0 | 1.0  0.0           ...           0.0 |
        |   2 |                        3.0 | 3.0  1.0           ...           0.0 |
        |   3 |                        2.0 | 2.0  3.0           ...           1.0 |
        |   4 |                        4.0 | 4.0  2.0           ...           3.0 |
    """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (meteo_factors.UnadjustedSunshineDuration,)
    UPDATEDSEQUENCES = (meteo_logs.LoggedUnadjustedSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedunadjustedsunshineduration[idx] = (
                log.loggedunadjustedsunshineduration[idx - 1]
            )
        log.loggedunadjustedsunshineduration[0] = fac.unadjustedsunshineduration


class Calc_DailySunshineDuration_V2(modeltools.Method):
    r"""Calculate the daily sunshine duration reversely to
    |Calc_DailyGlobalRadiation_V1|.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`DailySunshineDuration = Return\_SunshineDuration \left(
      DailyGlobalRadiation, ExtraterrestrialRadiation, DailyPossibleSunshineDuration
      \right)`

    Example:

        Method |Calc_UnadjustedSunshineDuration_V1| relies on
        |Return_SunshineDuration_V1| and thus comes with the same limitation regarding
        periods with little sunshine.  See its documentation for further information.
        Here, we only demonstrate the proper passing of |DailyGlobalRadiation|,
        |ExtraterrestrialRadiation|, and |DailyPossibleSunshineDuration|:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.moy.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> factors.dailypossiblesunshineduration = 12.0
        >>> fluxes.dailyglobalradiation = 80.0
        >>> fluxes.extraterrestrialradiation = 200.0
        >>> model.idx_sim = 1
        >>> model.calc_dailysunshineduration_v2()
        >>> factors.dailysunshineduration
        dailysunshineduration(7.2)

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMETHODS = (Return_SunshineDuration_V1,)
    CONTROLPARAMETERS = (meteo_control.AngstromConstant, meteo_control.AngstromFactor)
    DERIVEDPARAMETERS = (meteo_derived.MOY,)
    REQUIREDSEQUENCES = (
        meteo_factors.DailyPossibleSunshineDuration,
        meteo_fluxes.DailyGlobalRadiation,
        meteo_fluxes.ExtraterrestrialRadiation,
    )
    RESULTSEQUENCES = (meteo_factors.DailySunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        fac.dailysunshineduration = model.return_sunshineduration_v1(
            flu.dailyglobalradiation,
            flu.extraterrestrialradiation,
            fac.dailypossiblesunshineduration,
        )


class Calc_SunshineDuration_V2(modeltools.Method):
    r"""Adjust the current sunshine duration to the daily sunshine duration like
    |Calc_GlobalRadiation_V2| adjusts the current global radiation to the daily global
    radiation.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`SunshineDuration = UnadjustedSunshineDuration \cdot
      \frac{DailySunshineDuration}{\sum LoggedUnadjustedSunshineDuration}`

    Examples:

        |Calc_SunshineDuration_V2| implements a standardisation approach following the
        reasons and strategy explained in the documentation on method
        |Calc_GlobalRadiation_V2|.  Hence, we first adopt its examples without repeated
        explanations:

        >>> from hydpy.models.meteo import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> derived.nmblogentries.update()
        >>> model.idx_sim = 1
        >>> factors.unadjustedsunshineduration = 4.0
        >>> factors.dailysunshineduration = 4.0
        >>> logs.loggedunadjustedsunshineduration = 4.0
        >>> model.calc_sunshineduration_v2()
        >>> factors.sunshineduration
        sunshineduration(4.0)
        >>> factors.dailysunshineduration = 5.6
        >>> model.calc_sunshineduration_v2()
        >>> factors.sunshineduration
        sunshineduration(5.6)

        >>> simulationstep("1h")
        >>> derived.nmblogentries.update()
        >>> factors.dailysunshineduration = 4.0
        >>> factors.unadjustedsunshineduration = 0.8
        >>> logs.loggedunadjustedsunshineduration = (
        ...     0.8, 0.8, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.4, 0.6, 0.7, 0.8)
        >>> model.calc_sunshineduration_v2()
        >>> factors.sunshineduration
        sunshineduration(0.695652)

        The global radiation of a day cannot be zero due to diffusive radiations, but
        the sunshine duration can.  Hence, |Calc_SunshineDuration_V2| requires a
        safeguard against zero-divisions not relevant for |Calc_GlobalRadiation_V2|.
        We decided to generally set the adjusted sunshine duration to zero if the
        directly calculated daily sunshine duration or the current unadjusted sunshine
        duration is zero. (Note the sum of the logged unadjusted sunshine duration can
        only be zero if the present unadjusted sunshine duration is zero):

        >>> factors.unadjustedsunshineduration = 0.0
        >>> logs.loggedunadjustedsunshineduration = 0.0
        >>> model.calc_sunshineduration_v2()
        >>> factors.sunshineduration
        sunshineduration(0.0)
    """

    DERIVEDPARAMETERS = (meteo_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        meteo_factors.UnadjustedSunshineDuration,
        meteo_factors.DailySunshineDuration,
        meteo_factors.PossibleSunshineDuration,
        meteo_logs.LoggedUnadjustedSunshineDuration,
    )
    RESULTSEQUENCES = (meteo_factors.SunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        d_nom = fac.unadjustedsunshineduration * fac.dailysunshineduration
        if d_nom == 0.0:
            fac.sunshineduration = 0.0
        else:
            d_denom = 0.0
            for idx in range(der.nmblogentries):
                d_denom += log.loggedunadjustedsunshineduration[idx]
            fac.sunshineduration = min(d_nom / d_denom, fac.possiblesunshineduration)


class Calc_Temperature_V1(modeltools.Method):
    r"""Take the input temperature for each hydrological response unit.

    Basic equation:
      :math:`Temperature_{factors} = Temperature_{inputs}`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> inputs.temperature = 2.0
        >>> model.calc_temperature_v1()
        >>> factors.temperature
        temperature(2.0, 2.0)
    """

    CONTROLPARAMETERS = (meteo_control.NmbHRU,)
    REQUIREDSEQUENCES = (meteo_inputs.Temperature,)
    RESULTSEQUENCES = (meteo_factors.Temperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.temperature[k] = inp.temperature


class Adjust_Temperature_V1(modeltools.Method):
    r"""Adjust the previously determined temperature values.

    Basic equation:
      :math:`Temperature_{new} = TemperatureAddend + Temperature_{old}`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> temperatureaddend(-0.6, -1.2)
        >>> factors.temperature = 2.0
        >>> model.adjust_temperature_v1()
        >>> factors.temperature
        temperature(1.4, 0.8)
    """

    CONTROLPARAMETERS = (meteo_control.NmbHRU, meteo_control.TemperatureAddend)
    UPDATEDSEQUENCES = (meteo_factors.Temperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.temperature[k] += con.temperatureaddend[k]


class Calc_MeanTemperature_V1(modeltools.Method):
    r"""Calculate the average temperature.

    Basic equation:
      :math:`MeanTemperature =
      \sum_{i=1}^{NmbHRU} HRUAreaFraction_i \cdot Temperature_i`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.hruareafraction(0.8, 0.2)
        >>> factors.temperature = 1.0, 2.0
        >>> model.calc_meantemperature_v1()
        >>> factors.meantemperature
        meantemperature(1.2)
    """

    CONTROLPARAMETERS = (meteo_control.NmbHRU,)
    DERIVEDPARAMETERS = (meteo_derived.HRUAreaFraction,)
    REQUIREDSEQUENCES = (meteo_factors.Temperature,)
    RESULTSEQUENCES = (meteo_factors.MeanTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.meantemperature = 0.0
        for s in range(con.nmbhru):
            fac.meantemperature += der.hruareafraction[s] * fac.temperature[s]


class Calc_Precipitation_V1(modeltools.Method):
    r"""Take the input precipitation for each hydrological response unit.

    Basic equation:
      :math:`Precipitation_{fluxes} = Precipitation_{inputs}`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> inputs.precipitation = 2.0
        >>> model.calc_precipitation_v1()
        >>> fluxes.precipitation
        precipitation(2.0, 2.0)
    """

    CONTROLPARAMETERS = (meteo_control.NmbHRU,)
    REQUIREDSEQUENCES = (meteo_inputs.Precipitation,)
    RESULTSEQUENCES = (meteo_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.precipitation[k] = inp.precipitation


class Adjust_Precipitation_V1(modeltools.Method):
    r"""Adjust the previously determined precipitation values.

    Basic equation:
      :math:`Precipitation_{new} = PrecipitationFactor \cdot Precipitation_{old}`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> precipitationfactor(0.5, 2.0)
        >>> fluxes.precipitation = 2.0
        >>> model.adjust_precipitation_v1()
        >>> fluxes.precipitation
        precipitation(1.0, 4.0)
    """

    CONTROLPARAMETERS = (meteo_control.NmbHRU, meteo_control.PrecipitationFactor)
    UPDATEDSEQUENCES = (meteo_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.precipitation[k] *= con.precipitationfactor[k]


class Calc_MeanPrecipitation_V1(modeltools.Method):
    r"""Calculate the average precipitation.

    Basic equation:
      :math:`MeanPrecipitation =
      \sum_{i=1}^{NmbHRU} HRUAreaFraction_i \cdot Precipitation_i`

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.hruareafraction(0.8, 0.2)
        >>> fluxes.precipitation = 1.0, 2.0
        >>> model.calc_meanprecipitation_v1()
        >>> fluxes.meanprecipitation
        meanprecipitation(1.2)
    """

    CONTROLPARAMETERS = (meteo_control.NmbHRU,)
    DERIVEDPARAMETERS = (meteo_derived.HRUAreaFraction,)
    REQUIREDSEQUENCES = (meteo_fluxes.Precipitation,)
    RESULTSEQUENCES = (meteo_fluxes.MeanPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.meanprecipitation = 0.0
        for s in range(con.nmbhru):
            flu.meanprecipitation += der.hruareafraction[s] * flu.precipitation[s]


class Determine_Temperature_V1(modeltools.Method):
    r"""Interface method that applies the complete application model by executing all
    "run methods"."""

    @staticmethod
    def __call__(model: modeltools.AdHocModel) -> None:
        model.run()


class Get_Temperature_V1(modeltools.Method):
    """Get the current temperature from the selected hydrological response unit.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> factors.temperature = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_temperature_v1(0))
        2.0
        >>> round_(model.get_temperature_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (meteo_factors.Temperature,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.temperature[s]


class Get_MeanTemperature_V1(modeltools.Method):
    """Get the mean temperature.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> factors.meantemperature = 3.0
        >>> model.get_meantemperature_v1()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_factors.MeanTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.meantemperature


class Determine_Precipitation_V1(modeltools.Method):
    r"""Interface method that applies the complete application model by executing all
    "run methods"."""

    @staticmethod
    def __call__(model: modeltools.AdHocModel) -> None:
        model.run()


class Get_Precipitation_V1(modeltools.Method):
    """Get the current precipitation from the selected hydrological response unit.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.precipitation = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_precipitation_v1(0))
        2.0
        >>> round_(model.get_precipitation_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (meteo_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.precipitation[s]


class Get_MeanPrecipitation_V1(modeltools.Method):
    """Get the mean precipitation.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.meanprecipitation = 3.0
        >>> model.get_meanprecipitation_v1()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_fluxes.MeanPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.meanprecipitation


class Process_Radiation_V1(modeltools.ReusableMethod):
    """Interface method for radiation-related submodels that executes all "run
    methods"."""

    @staticmethod
    def __call__(model: modeltools.AdHocModel) -> None:
        model.run()


class Get_PossibleSunshineDuration_V1(modeltools.Method):
    """Get the potential sunshine duration in h.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> factors.possiblesunshineduration = 3.0
        >>> model.get_possiblesunshineduration_v1()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_factors.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.possiblesunshineduration


class Get_PossibleSunshineDuration_V2(modeltools.Method):
    """Get the potential sunshine duration in h.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> inputs.possiblesunshineduration = 3.0
        >>> model.get_possiblesunshineduration_v2()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_inputs.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.possiblesunshineduration


class Get_SunshineDuration_V1(modeltools.Method):
    """Get the actual sunshine duration in h.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> factors.sunshineduration = 3.0
        >>> model.get_sunshineduration_v1()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_factors.SunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.sunshineduration


class Get_SunshineDuration_V2(modeltools.Method):
    """Get the actual sunshine duration in h.

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> inputs.sunshineduration = 3.0
        >>> model.get_sunshineduration_v2()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_inputs.SunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.sunshineduration


class Get_ClearSkySolarRadiation_V1(modeltools.Method):
    """Get the clear sky solar radiation in W/m².

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> fluxes.clearskysolarradiation = 3.0
        >>> model.get_clearskysolarradiation_v1()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_fluxes.ClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.clearskysolarradiation


class Get_ClearSkySolarRadiation_V2(modeltools.Method):
    """Get the clear sky solar radiation in W/m².

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> inputs.clearskysolarradiation = 3.0
        >>> model.get_clearskysolarradiation_v2()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_inputs.ClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.clearskysolarradiation


class Get_GlobalRadiation_V1(modeltools.Method):
    """Get the global radiation in W/m².

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> fluxes.globalradiation = 3.0
        >>> model.get_globalradiation_v1()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_fluxes.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.globalradiation


class Get_GlobalRadiation_V2(modeltools.Method):
    """Get the global radiation in W/m².

    Example:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> inputs.globalradiation = 3.0
        >>> model.get_globalradiation_v2()
        3.0
    """

    REQUIREDSEQUENCES = (meteo_inputs.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.globalradiation


class Model(modeltools.AdHocModel):
    """|meteo.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Meteo")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_EarthSunDistance_V1,
        Calc_SolarDeclination_V1,
        Calc_SolarDeclination_V2,
        Calc_SunsetHourAngle_V1,
        Calc_SolarTimeAngle_V1,
        Calc_TimeOfSunrise_TimeOfSunset_V1,
        Calc_DailyPossibleSunshineDuration_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_PossibleSunshineDuration_V2,
        Update_LoggedSunshineDuration_V1,
        Calc_DailySunshineDuration_V1,
        Update_LoggedGlobalRadiation_V1,
        Calc_DailyGlobalRadiation_V2,
        Calc_ExtraterrestrialRadiation_V1,
        Calc_ExtraterrestrialRadiation_V2,
        Calc_DailySunshineDuration_V2,
        Calc_SunshineDuration_V1,
        Calc_PortionDailyRadiation_V1,
        Calc_ClearSkySolarRadiation_V1,
        Adjust_ClearSkySolarRadiation_V1,
        Calc_GlobalRadiation_V1,
        Calc_UnadjustedGlobalRadiation_V1,
        Calc_UnadjustedSunshineDuration_V1,
        Update_LoggedUnadjustedGlobalRadiation_V1,
        Update_LoggedUnadjustedSunshineDuration_V1,
        Calc_DailyGlobalRadiation_V1,
        Calc_GlobalRadiation_V2,
        Calc_SunshineDuration_V2,
        Calc_Temperature_V1,
        Adjust_Temperature_V1,
        Calc_MeanTemperature_V1,
        Calc_Precipitation_V1,
        Adjust_Precipitation_V1,
        Calc_MeanPrecipitation_V1,
    )
    INTERFACE_METHODS = (
        Determine_Temperature_V1,
        Get_Temperature_V1,
        Get_MeanTemperature_V1,
        Determine_Precipitation_V1,
        Get_Precipitation_V1,
        Get_MeanPrecipitation_V1,
        Process_Radiation_V1,
        Get_PossibleSunshineDuration_V1,
        Get_PossibleSunshineDuration_V2,
        Get_SunshineDuration_V1,
        Get_SunshineDuration_V2,
        Get_ClearSkySolarRadiation_V1,
        Get_ClearSkySolarRadiation_V2,
        Get_GlobalRadiation_V1,
        Get_GlobalRadiation_V2,
    )
    ADD_METHODS = (Return_DailyGlobalRadiation_V1, Return_SunshineDuration_V1)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class Sub_BaseModel(modeltools.AdHocModel):
    """Base class for |meteo.DOCNAME.long| submodels."""

    @staticmethod
    @contextlib.contextmanager
    def share_configuration(
        sharable_configuration: SharableConfiguration,
    ) -> Generator[None, None, None]:
        """Take the `landtype_constants` data to adjust all parameters inherited from
        |meteo_parameters.ZipParameter1D| and the `refweights` parameter instance to
        adjust the index references of all parameters inherited from
        |meteo_parameters.ZipParameter1D| and all sequences inherited from
        |meteo_sequences.FluxSequence1D|:

        >>> from hydpy.core.parametertools import Constants, NameParameter, Parameter
        >>> consts = Constants(GRASS=1, TREES=3, WATER=2)
        >>> class LandType(NameParameter):
        ...     __name__ = "temp.py"
        ...     constants = consts
        >>> class Subarea(Parameter):
        ...     ...
        >>> from hydpy.models.meteo.meteo_model import Sub_BaseModel
        >>> with Sub_BaseModel.share_configuration(
        ...         {"landtype_refindices": LandType,
        ...          "refweights": Subarea}):
        ...     from hydpy.models.meteo.meteo_parameters import ZipParameter1D
        ...     ZipParameter1D.constants
        ...     ZipParameter1D.refindices.__name__
        ...     ZipParameter1D._refweights.__name__
        ...     from hydpy.models.meteo.meteo_sequences import FluxSequence1D
        ...     FluxSequence1D._refweights.__name__
        {'GRASS': 1, 'TREES': 3, 'WATER': 2}
        'LandType'
        'Subarea'
        'Subarea'
        >>> ZipParameter1D.constants
        {}
        >>> ZipParameter1D.refindices
        >>> ZipParameter1D._refweights
        >>> FluxSequence1D._refweights
        """
        with meteo_parameters.ZipParameter1D.modify_refindices(
            sharable_configuration["landtype_refindices"]
        ), meteo_parameters.ZipParameter1D.modify_refweights(
            sharable_configuration["refweights"]
        ), meteo_parameters.ZipParameter1D.modify_refweights(
            sharable_configuration["refweights"]
        ), meteo_sequences.FluxSequence1D.modify_refweights(
            sharable_configuration["refweights"]
        ):
            yield

    @importtools.define_targetparameter(meteo_control.NmbHRU)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of hydrological response units.

        >>> from hydpy.models.meteo_precip_io import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> nmbhru
        nmbhru(2)
        """
        self.parameters.control.nmbhru(nmbzones)

    @importtools.define_targetparameter(meteo_control.HRUArea)
    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the area of all hydrological response units in km².

        >>> from hydpy.models.meteo_precip_io import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_subareas([1.0, 3.0])
        >>> hruarea
        hruarea(1.0, 3.0)
        """
        self.parameters.control.hruarea(subareas)
