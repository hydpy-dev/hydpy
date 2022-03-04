# -*- coding: utf-8 -*-
"""
.. _`solar time`: https://en.wikipedia.org/wiki/Solar_time
"""
# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.models.meteo import meteo_fixed
from hydpy.models.meteo import meteo_control
from hydpy.models.meteo import meteo_derived
from hydpy.models.meteo import meteo_inputs
from hydpy.models.meteo import meteo_factors
from hydpy.models.meteo import meteo_fluxes


class Calc_EarthSunDistance_V1(modeltools.Method):
    r"""Calculate the relative inverse distance between the earth and the sun.

    Basic equation (:cite:`ref-Allen1998`, equation 23):
      :math:`EarthSunDistance = 1 + 0.033 \cdot cos(2 \cdot Pi / 366 \cdot (DOY + 1)`

    Note that this equation differs slightly from the one given by
    :cite:`ref-Allen1998`.  The following examples show that |Calc_EarthSunDistance_V1|
    calculates the same distance value for a specific "day" (e.g. the 1st March) both
    for leap years and non-leap years.  Hence, there is a tiny "jump" between 28th
    February and 1st March for non-leap years.

    Examples:

        We define an initialisation period covering both a leap year (2000) and a
        non-leap year (2001):

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

        The following calculation agrees with example 8 of :cite:`ref-Allen1998`:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_earthsundistance_v1()
        >>> factors.earthsundistance
        earthsundistance(0.984993)
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
    r"""Calculate the solar declination.

    Basic equation (:cite:`ref-Allen1998`, equation 24):
      :math:`SolarDeclination =
      0.409 \cdot sin(2 \cdot Pi / 366 \cdot (DOY + 1) - 1.39)`

    Note that this equation differs slightly from the one given by
    :cite:`ref-Allen1998` due to reasons explained in the documentation on method
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

        The following calculation agrees with example 8 of :cite:`ref-Allen1998`:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_solardeclination_v1()
        >>> factors.solardeclination
        solardeclination(0.117464)
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


class Calc_SunsetHourAngle_V1(modeltools.Method):
    r"""Calculate the sunset hour angle.

    Basic equation (:cite:`ref-Allen1998`, equation 25):
      :math:`SunsetHourAngle = arccos(-tan(LatitudeRad) \cdot tan(SolarDeclination))`

    Example:

        The following calculation agrees with example 8 of :cite:`ref-Allen1998`:

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
    r"""Calculate the solar time angle at the midpoint of the current period.

    Basic equations (:cite:`ref-Allen1998`, equations 31 to 33):
      :math:`SolarTimeAngle =
      Pi / 12 \cdot ((SCT + (Longitude - UTCLongitude) / 15 + S_c) - 12)`

      :math:`S_c = 0.1645 \cdot sin(2 \cdot b) -
      0.1255 \cdot cos(b) - 0.025 \cdot sin(b)`

      :math:`b = (2 \cdot Pi \cdot (DOY - 80)) / 365`

    Note there are two slight deviations from the equations given by
    :cite:`ref-Allen1998`.  The first one is that positive numbers correspond to
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


class Calc_ExtraterrestrialRadiation_V1(modeltools.Method):
    r"""Calculate the extraterrestrial radiation.

    Basic equation for daily simulation steps (:cite:`ref-Allen1998`, equation 21):
      :math:`ExternalTerrestrialRadiation =
      \frac{Seconds \ 4.92}{Pi \ 60 \cdot 60} \cdot EarthSunDistance \cdot (
      SunsetHourAngle \cdot sin(LatitudeRad) \cdot sin(SolarDeclination) +
      cos(LatitudeRad) \cdot cos(SolarDeclination) \cdot sin(SunsetHourAngle))`

    Basic equation for (sub)hourly steps (:cite:`ref-Allen1998`, eq. 28 to 30):
      :math:`ExternalTerrestrialRadiation =
      \frac{12 \cdot 4.92}{Pi} \cdot EarthSunDistance \cdot (
      (\omega_2 - \omega_1) \cdot sin(LatitudeRad) \cdot sin(SolarDeclination) +
      cos(LatitudeRad) \cdot cos(SolarDeclination) \cdot (sin(\omega_2) -
      sin(\omega_1)))`

      :math:`\omega_1 = SolarTimeAngle - \frac{Pi \cdot Seconds}{60 \cdot 60 \cdot 24}`

      :math:`\omega_2 = SolarTimeAngle + \frac{Pi \cdot Seconds}{60 \cdot 60 \cdot 24}`

    Examples:

        The following calculation agrees with example 8 of :cite:`ref-Allen1998` for
        daily time steps:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.seconds(60*60*24)
        >>> derived.latituderad(-0.35)
        >>> factors.earthsundistance = 0.985
        >>> factors.solardeclination = 0.12
        >>> factors.sunsethourangle = 1.527
        >>> model.calc_extraterrestrialradiation_v1()
        >>> fluxes.extraterrestrialradiation
        extraterrestrialradiation(32.173851)

        The following calculation repeats the above example for an hourly simulation
        time step, still covering the whole day:

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

        Note that, even with identical values of the local longitude (|Longitude|) and
        the one of the time zone (|UTCLongitude|), the calculated radiation values are
        not symmetrical due to the eccentricity of the Earth"s orbit (see `solar
        time`_).

        There is a slight deviation between the directly calculated daily value and the
        sum of the hourly values:

        >>> round_(sum_)
        32.139663

        For sub-daily simulation time steps, results are most accurate for the shortest
        step size.  On the other hand, they can be (extremely) inaccurate for timesteps
        between one hour and one day.  We demonstrate this by comparing the sum of the
        sub-daily values of different step sizes with the directly calculated daily
        value (note the apparent total fail of method
        |Calc_ExtraterrestrialRadiation_V1| for a step size of 720 minutes):

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

    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    DERIVEDPARAMETERS = (
        meteo_derived.Seconds,
        meteo_derived.LatitudeRad,
    )
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
        if der.seconds < 60.0 * 60.0 * 24.0:
            d_delta = fix.pi * der.seconds / 60.0 / 60.0 / 24.0
            d_omega1 = fac.solartimeangle - d_delta
            d_omega2 = fac.solartimeangle + d_delta
            flu.extraterrestrialradiation = max(
                (12.0 * 4.92 / fix.pi * fac.earthsundistance)
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
                der.seconds * 0.0820 / 60.0 / fix.pi * fac.earthsundistance
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


class Calc_PossibleSunshineDuration_V1(modeltools.Method):
    r"""Calculate the possible astronomical sunshine duration.

    Basic equation for daily timesteps (:cite:`ref-Allen1998`, equation 34):
      :math:`PossibleSunshineDuration = 24 / Pi \cdot SunsetHourAngle`

    Basic equation for (sub)hourly timesteps:
      :math:`PossibleSunshineDuration =
      min(max(12 / Pi \cdot (SunsetHourAngle - \tau), 0), \frac{Seconds}{60 \cdot 60})`

      .. math::
        \tau =
        \begin{cases}
        -SolarTimeAngle - Pi \cdot Days &|\ SolarTimeAngle \leq 0
        \\
        SolarTimeAngle - Pi \cdot Days &|\  SolarTimeAngle > 0
        \end{cases}

    Examples:

        The following calculation agrees with example 9 of :cite:`ref-Allen1998`:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> derived.seconds(60*60*24)
        >>> factors.sunsethourangle(1.527)
        >>> model.calc_possiblesunshineduration_v1()
        >>> factors.possiblesunshineduration
        possiblesunshineduration(11.665421)

        The following calculation repeats the above example for an hourly simulation
        time step, still covering the whole day. Therefore the ratio is only calculated
        during sunrise and sunset and set to 1 at daytime and 0 at nighttime:

        >>> from hydpy import round_
        >>> import numpy
        >>> derived.seconds(60*60)
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
    DERIVEDPARAMETERS = (meteo_derived.Seconds,)
    REQUIREDSEQUENCES = (
        meteo_factors.SolarTimeAngle,
        meteo_factors.SunsetHourAngle,
    )
    RESULTSEQUENCES = (meteo_factors.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fix = model.parameters.fixed.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        d_hours = der.seconds / 60.0 / 60.0
        d_days = d_hours / 24.0
        if d_hours < 24.0:
            if fac.solartimeangle <= 0.0:
                d_thresh = -fac.solartimeangle - fix.pi * d_days
            else:
                d_thresh = fac.solartimeangle - fix.pi * d_days
            fac.possiblesunshineduration = min(
                max(12.0 / fix.pi * (fac.sunsethourangle - d_thresh), 0.0), d_hours
            )
        else:
            fac.possiblesunshineduration = 24.0 / fix.pi * fac.sunsethourangle


class Calc_ClearSkySolarRadiation_V1(modeltools.Method):
    r"""Calculate the clear sky solar radiation.

    Basic equation (:cite:`ref-Allen1998` eq. 35):
      :math:`ClearSkySolarRadiation =
      ExtraterrestrialRadiation \cdot (AngstromConstant + AngstromFactor)`

    Example:

        We use the Ångström coefficients (a=0.19, b=0.55) recommended for Germany by
        DVWK-M 504 :cite:`ref-DVWK` for January and the default values (a=0.25, b=0.5)
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
        meteo_control.AngstromConstant,
        meteo_control.AngstromFactor,
    )
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
    r"""Calculate the global radiation.

    Basic equation (:cite:`ref-Allen1998`, equation 35):
      :math:`GlobalRadiation = ExtraterrestrialRadiation \cdot (AngstromConstant +
      AngstromFactor \cdot SunshineDuration / PossibleSunshineDuration)`

    Example:

        We use the Ångström coefficients (a=0.19, b=0.55) recommended for Germany by
        DVWK-M 504 :cite:`ref-DVWK` for January and the default values (a=0.25, b=0.5)
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
        >>> fluxes.extraterrestrialradiation = 40.0
        >>> model.idx_sim = 1
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(26.457143)
        >>> model.idx_sim = 2
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(27.142857)

        For zero possible sunshine durations, |Calc_GlobalRadiation_V1| sets
        |meteo_fluxes.GlobalRadiation| to zero:

        >>> factors.possiblesunshineduration = 0.0
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.0)
    """

    CONTROLPARAMETERS = (
        meteo_control.AngstromConstant,
        meteo_control.AngstromFactor,
    )
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


class Calc_SunshineDuration_V1(modeltools.Method):
    r"""Calculate the sunshine duration.

    Basic equation (:cite:`ref-Allen1998`, equation 35, rearranged):
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
        >>> fluxes.extraterrestrialradiation = 40.0
        >>> model.idx_sim = 1
        >>> inputs.globalradiation = 26.457143
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(12.0)
        >>> model.idx_sim = 2
        >>> inputs.globalradiation = 27.142857
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

        >>> fluxes.extraterrestrialradiation = 40.0
        >>> inputs.globalradiation = 50.0
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(14.0)

        >>> inputs.globalradiation = 0.0
        >>> model.calc_sunshineduration_v1()
        >>> factors.sunshineduration
        sunshineduration(0.0)
    """

    CONTROLPARAMETERS = (
        meteo_control.AngstromConstant,
        meteo_control.AngstromFactor,
    )
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


class Model(modeltools.AdHocModel):
    """The Meteo base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_EarthSunDistance_V1,
        Calc_SolarDeclination_V1,
        Calc_SunsetHourAngle_V1,
        Calc_SolarTimeAngle_V1,
        Calc_ExtraterrestrialRadiation_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_ClearSkySolarRadiation_V1,
        Calc_GlobalRadiation_V1,
        Calc_SunshineDuration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()
