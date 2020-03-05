# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring
"""
.. _`Allen`: http://www.fao.org/3/x0490e/x0490e00.htm
"""
# ToDo: search for varrho
# imports...
# ...from standard library
import typing
# ...from HydPy
from hydpy.core import modeltools
from hydpy.auxs import roottools
from hydpy.core.typingtools import Vector
from hydpy.cythons import modelutils
# ...from lland
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_derived
from hydpy.models.lland import lland_inputs
from hydpy.models.lland import lland_fluxes
from hydpy.models.lland import lland_states
from hydpy.models.lland import lland_logs
from hydpy.models.lland import lland_aides
from hydpy.models.lland import lland_outlets
from hydpy.models.lland.lland_constants import WASSER, FLUSS, SEE, VERS, NADELW


class Calc_NKor_V1(modeltools.Method):
    """Adjust the given precipitation value.

    Basic equation:
      :math:`NKor = KG \\cdot Nied`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
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
    REQUIREDSEQUENCES = (
        lland_inputs.Nied,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NKor,
    )
    
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
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> kt(-2.0, 0.0, 2.0)
        >>> inputs.teml(1.)
        >>> model.calc_tkor_v1()
        >>> fluxes.tkor
        tkor(-1.0, 1.0, 3.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KT,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.TemL,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TKor,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.tkor[k] = con.kt[k] + inp.teml


class Calc_PsychrometricConstant_V1(modeltools.Method):
    """Calculate the psychrometric constant.

    Basic equation (`Allen`_, equation 8):
      :math:`PsychrometricConstant =
      6.65 \\cdot 10^{-4} \\cdot AtmosphericPressure`

    Example:

        The following calculation agrees with example 2 of `Allen`_:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> inputs.atmosphericpressure(81.8)
        >>> model.calc_psychrometricconstant_v1()
        >>> fluxes.psychrometricconstant
        psychrometricconstant(0.054397)
    """

    REQUIREDSEQUENCES = (
        lland_inputs.AtmosphericPressure,
    )
    RESULTSEQUENCES = (
        lland_fluxes.PsychrometricConstant,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.psychrometricconstant = 6.65e-4 * inp.atmosphericpressure

    # ToDo: Wird in Larsim nicht berechnet sondern konstant angenommen
    # (evtl. in lland_v3 anpassen)


class Calc_WindSpeed2m_V1(modeltools.Method):
    """Adjust the measured wind speed to a height of 2 meters
    above the ground.

    For further documentation see method |Adjust_WindSpeed_V1|.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed2m_v1()
        >>> fluxes.windspeed2m
        windspeed2m(3.738763)
    """
    CONTROLPARAMETERS = (
        lland_control.MeasuringHeightWindSpeed,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.WindSpeed,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WindSpeed2m,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed2m = model.adjust_windspeed_v1(2.)


class Calc_WindSpeed10m_V1(modeltools.Method):
    """Adjust the measured wind speed to a height of 10 meters
    above the ground.

    For further documentation see method |Adjust_WindSpeed_V1|.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(3.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed10m_v1()
        >>> fluxes.windspeed10m
        windspeed10m(6.15649)
    """
    CONTROLPARAMETERS = (
        lland_control.MeasuringHeightWindSpeed,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.WindSpeed,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WindSpeed10m,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed10m = model.adjust_windspeed_v1(10.,)


class Adjust_WindSpeed_V1(modeltools.Method):
    """Adjust the measured wind speed to the defined height above the ground.

    Basic equation (`Allen`_ equation 47, modified for higher precision):
      :math:`AdjustedWindSpeed2m = WindSpeed \\cdot
      \\frac{ln((newheight-d)/z_0)}
      {ln((MeasuringHeightWindSpeed-d)/z_0)}` \n

      :math:`d = 2 / 3 \\cdot 0.12` \n

      :math:`z_0 = 0.123 \\cdot 0.12`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> from hydpy import round_
        >>> round_(model.adjust_windspeed_v1(2.0))
        3.738763
        >>> round_(model.adjust_windspeed_v1(0.5))
        2.571532
        """
    CONTROLPARAMETERS = (
        lland_control.MeasuringHeightWindSpeed,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.WindSpeed,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, newheight: float) -> float:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        d_d = 2. / 3. * .12
        d_z0 = .123 * .12
        return (inp.windspeed *
                (modelutils.log((newheight-d_d)/d_z0) /
                 modelutils.log((con.measuringheightwindspeed-d_d)/d_z0)))


class Calc_EarthSunDistance_V1(modeltools.Method):
    # noinspection PyUnresolvedReferences
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

        >>> from hydpy.models.lland import *
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

        The following calculation agrees with example 8 of `Allen`_:

        >>> derived.doy(246)
        >>> model.idx_sim = 0
        >>> model.calc_earthsundistance_v1()
        >>> fluxes.earthsundistance
        earthsundistance(0.984993)

        .. testsetup::

            >>> del pub.timegrids
        """
    DERIVEDPARAMETERS = (
        lland_derived.DOY,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EarthSunDistance,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.earthsundistance = 1. + 0.033 * modelutils.cos(
            2 * 3.141592653589793 / 366. * (der.doy[model.idx_sim] + 1)
        )


class Calc_SolarDeclination_V1(modeltools.Method):
    # noinspection PyUnresolvedReferences
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

        The results are identical for both years:

        >>> test('2000-01-01', '2000-02-28', '2000-02-29',
        ...      '2000-03-01', '2000-12-31')
        2000-01-01: -0.401012
        2000-02-28: -0.150618
        2000-02-29: -0.144069
        2000-03-01: -0.137476
        2000-12-31: -0.402334

        >>> test('2001-01-01', '2001-02-28',
        ...      '2001-03-01', '2001-12-31')
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

        .. testsetup::

            >>> del pub.timegrids
        """
    DERIVEDPARAMETERS = (
        lland_derived.DOY,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SolarDeclination,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.solardeclination = .409 * modelutils.sin(
            2 * 3.141592653589793 / 366 * (der.doy[model.idx_sim] + 1) - 1.39
        )


class Calc_SunsetHourAngle_V1(modeltools.Method):
    """Calculate the sunset hour angle.

    Basic equation (`Allen`_, equation 25):
      :math:`SunsetHourAngle =
      arccos(-tan(LatitudeRad) \\cdot tan(SolarDeclination))`

    Example:

        The following calculation agrees with example 8 of `Allen`_:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.doy.shape = 1
        >>> derived.doy(246)
        >>> derived.latituderad(-0.35)
        >>> fluxes.solardeclination = 0.12
        >>> model.calc_sunsethourangle_v1()
        >>> fluxes.sunsethourangle
        sunsethourangle(1.526767)
    """
    DERIVEDPARAMETERS = (
        lland_derived.LatitudeRad,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SolarDeclination,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SunsetHourAngle,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.sunsethourangle = modelutils.acos(
            -modelutils.tan(der.latituderad) *
            modelutils.tan(flu.solardeclination)
        )


class Calc_SolarTimeAngle_V1(modeltools.Method):
    """Calculate the solar time angle at the midpoint of the current period.

    Basic equations (`Allen`_, equations 31 to 33):
      :math:`SolarTimeAngle =
      \\pi / 12 \\cdot
      ((SCT \\cdot 60 \\cdot 60 + (Longitude - UTCLongitude) / 15 + S_c)
      - 12)` \n

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

        >>> from hydpy import pub, round_, UnitTest
        >>> pub.timegrids = '2000-09-03', '2000-09-04', '1h'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> longitude(15)
        >>> derived.doy.update()
        >>> derived.sct.update()
        >>> derived.utclongitude.update()
        >>> for hour in range(24):
        ...     model.idx_sim = hour
        ...     model.calc_solartimeangle_v1()
        ...     print(hour, end=': ')
        ...     round_(fluxes.solartimeangle.value)   # doctest: +ELLIPSIS
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
    CONTROLPARAMETERS = (
        lland_control.Longitude,
    )
    DERIVEDPARAMETERS = (
        lland_derived.DOY,
        lland_derived.SCT,
        lland_derived.UTCLongitude,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SolarTimeAngle,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_pi = 3.141592653589793
        d_b = 2. * d_pi * (der.doy[model.idx_sim] - 80.) / 365.
        d_sc = (
            .1645 * modelutils.sin(2. * d_b) -
            .1255 * modelutils.cos(d_b) -
            .025 * modelutils.sin(d_b))
        flu.solartimeangle = d_pi / 12. * (
            (der.sct[model.idx_sim] / 60. / 60. +
             (con.longitude - der.utclongitude) / 15. + d_sc) - 12.)


class Calc_ExtraterrestrialRadiation_V1(modeltools.Method):
    """Calculate the extraterrestrial radiation.

    Basic equation for daily simulation steps (`Allen`_, equation 21):
      :math:`ExternalTerrestrialRadiation =
      \\frac{Seconds}{\\pi} \\cdot
      \\frac{4.92}{60 \\cdot 60} \\cdot
      EarthSunDistance \\cdot (
      SunsetHourAngle \\cdot sin(LatitudeRad) \\cdot sin(SolarDeclination) +
      cos(LatitudeRad) \\cdot cos(SolarDeclination) \\cdot sin(SunsetHourAngle)
      )`

    Basic equation for hourly simulation steps (`Allen`_, eq. 28 to 30):
      :math:`ExternalTerrestrialRadiation =
      \\frac{12 \\cdot Seconds}{\\pi \\cdot 60 \\cdot 60} \\cdot 4.92 \\cdot
      EarthSunDistance \\cdot (
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

        >>> from hydpy.models.lland import *
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
        >>> derived.sct = numpy.linspace(1800.0, 84600.0, 24)
        >>> sum_ = 0.0
        >>> from hydpy import round_
        >>> for hour in range(24):
        ...     model.idx_sim = hour
        ...     model.calc_solartimeangle_v1()
        ...     model.calc_extraterrestrialradiation_v1()
        ...     print(hour, end=': ')
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
        day due to the eccentricity of the Earth's orbit (see `solar time`_).

        There is a small deviation between the directly calculated daily
        value and the sum of the hourly values:

        >>> round_(sum_)
        32.139663
    """
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
        lland_derived.LatitudeRad,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SolarTimeAngle,
        lland_fluxes.EarthSunDistance,
        lland_fluxes.SolarDeclination,
        lland_fluxes.SunsetHourAngle,
    )
    RESULTSEQUENCES = (
        lland_fluxes.ExtraterrestrialRadiation,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_pi = 3.141592653589793
        d_g = 0.0820 / 60
        if der.seconds <= 60. * 60.:
            d_delta = d_pi * der.seconds / 60. / 60. / 24.
            d_omega1 = flu.solartimeangle - d_delta
            d_omega2 = flu.solartimeangle + d_delta
            flu.extraterrestrialradiation = max(
                12. * der.seconds / d_pi * d_g * flu.earthsundistance * (
                    ((d_omega2 - d_omega1) *
                     modelutils.sin(der.latituderad) *
                     modelutils.sin(flu.solardeclination)) +
                    (modelutils.cos(der.latituderad) *
                     modelutils.cos(flu.solardeclination) *
                     (modelutils.sin(d_omega2) - modelutils.sin(d_omega1))
                     )), 0.)
        else:
            flu.extraterrestrialradiation = (
                der.seconds/d_pi*d_g*flu.earthsundistance *
                ((flu.sunsethourangle*modelutils.sin(der.latituderad) *
                  modelutils.sin(flu.solardeclination)) +
                 (modelutils.cos(der.latituderad) *
                  modelutils.cos(flu.solardeclination) *
                  modelutils.sin(flu.sunsethourangle))))


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

        >>> from hydpy.models.lland import *
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
        ...     print(hour, end=': ')   # doctest: +ELLIPSIS
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
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SolarTimeAngle,
        lland_fluxes.SunsetHourAngle,
    )
    RESULTSEQUENCES = (
        lland_fluxes.PossibleSunshineDuration,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_pi = 3.141592653589793
        d_hours = der.seconds / 60. / 60.
        d_days = d_hours / 24.
        if d_hours <= 1.:
            if flu.solartimeangle <= 0.:
                d_thresh = -flu.solartimeangle - d_pi * d_days
            else:
                d_thresh = flu.solartimeangle - d_pi * d_days
            flu.possiblesunshineduration = \
                min(max(12./d_pi*(flu.sunsethourangle-d_thresh), 0.), d_hours)
        else:
            flu.possiblesunshineduration = 24. / d_pi * flu.sunsethourangle


class Update_LoggedPossibleSunshineDuration_V1(modeltools.Method):
    """Log the possible sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorised values to the right and stores the
        respective new value on the most left position:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedpossiblesunshineduration.shape = 3
        >>> logs.loggedpossiblesunshineduration = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedpossiblesunshineduration_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.possiblesunshineduration,
        ...                          logs.loggedpossiblesunshineduration))
        >>> test.nexts.possiblesunshineduration = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedpossiblesunshineduration
        >>> test()
        | ex. | possiblesunshineduration |\
           loggedpossiblesunshineduration |
        ----------------------------------\
-------------------------------------------
        |   1 |                      1.0 |\
 1.0  0.0                             0.0 |
        |   2 |                      3.0 |\
 3.0  1.0                             0.0 |
        |   3 |                      2.0 |\
 2.0  3.0                             1.0 |
        |   4 |                      4.0 |\
 4.0  2.0                             3.0 |
    """
    DERIVEDPARAMETERS = (
        lland_derived.NmbLogEntries,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.PossibleSunshineDuration,
    )
    UPDATEDSEQUENCES = (
        lland_logs.LoggedPossibleSunshineDuration,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedpossiblesunshineduration[idx] = \
                log.loggedpossiblesunshineduration[idx - 1]
        log.loggedpossiblesunshineduration[0] = flu.possiblesunshineduration


class Calc_GlobalRadiation_V1(modeltools.Method):
    """Calculate the global radiation.

    Basic equations:
      :math:`GlobalRadiation =
            Extraterrestrialradiation *
                (AngstromConstant + AngstromFactor *
                 SunshineDuration/PossibleSunshineDuration))

    Example:

        Calculate the |GlobalRadiation| from |SunshineDuration| in January

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1h'
        >>> derived.moy.update()
        >>> angstromconstant.jan = 0.172
        >>> angstromfactor.jan = 0.573
        >>> inputs.sunshineduration(0.6)
        >>> fluxes.possiblesunshineduration = 1.0
        >>> fluxes.extraterrestrialradiation = 1.7
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.87686)

        The same |SunshineDuration| leads in June to a lower |GlobalRadiation|
        than in january

        >>> pub.timegrids = '2000-06-01', '2000-06-02', '1h'
        >>> derived.moy.update()
        >>> angstromconstant.jun = 0.160
        >>> angstromfactor.jun = 0.629
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.91358)

        If sunshineduration is 0 also the global radiation is set
        to 0.

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.0)

        To prevent inconsistencies the globalradiation is also set to zero if
        the |ExtraterrestrialRadiation| is zero

        >>> fluxes.possiblesunshineduration = 0.05
        >>> fluxes.extraterrestrialradiation = 0.0
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.0)

        .. testsetup::

            >>> del pub.timegrids
        """
    CONTROLPARAMETERS = (
        lland_control.AngstromConstant,
        lland_control.AngstromFactor,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.ExtraterrestrialRadiation,
        lland_fluxes.PossibleSunshineDuration,
        lland_inputs.SunshineDuration,
    )
    RESULTSEQUENCES = (
        lland_fluxes.GlobalRadiation,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        if ((flu.possiblesunshineduration <= 0.0) or
                (flu.extraterrestrialradiation <= 0.0)):
            # ToDo: Inkonsistenz:
            #  possiblesunshineduration/extraterrestrialradiation
            flu.globalradiation = 0.0
        else:
            idx = der.moy[model.idx_sim]
            flu.globalradiation = (
                flu.extraterrestrialradiation *
                (con.angstromconstant[idx] + con.angstromfactor[idx] *
                 inp.sunshineduration/flu.possiblesunshineduration))
        # TODO: Korrektur aus SOSD in GLob übernehmen?
        # TODO: Diskrepanzen possiblesunshineduration/extraterrestrialradiation
        # TODO: Sunshineduration > Possiblesunshineduration


class Update_LoggedSunshineDuration_V1(modeltools.Method):
    """Log the sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively
        moves the three memorized values to the right and stores the
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
    DERIVEDPARAMETERS = (
        lland_derived.NmbLogEntries,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.SunshineDuration,
    )
    UPDATEDSEQUENCES = (
        lland_logs.LoggedSunshineDuration,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries-1, 0, -1):
            log.loggedsunshineduration[idx] = \
                log.loggedsunshineduration[idx - 1]
        log.loggedsunshineduration[0] = inp.sunshineduration


class Calc_ET0_V1(modeltools.Method):
    """Calculate reference evapotranspiration after Turc-Wendling.

    Basic equation:
      :math:`ET0 = KE \\cdot
      \\frac{(8.64 \\cdot Glob+93 \\cdot KF) \\cdot (TKor+22)}
      {165 \\cdot (TKor+123) \\cdot (1 + 0.00019 \\cdot min(HNN, 600))}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
    RESULTSEQUENCES = (
        lland_fluxes.ET0,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = (
                con.ke[k] * (
                    ((8.64 * inp.glob + 93. * con.kf[k]) *
                     (flu.tkor[k] + 22.)) /
                    (165. * (flu.tkor[k] + 123.) *
                     (1. + 0.00019 * min(con.hnn[k], 600.)))
                )
            )


class Calc_ET0_WET0_V1(modeltools.Method):
    """Correct the given reference evapotranspiration and update the
    corresponding log sequence.

    Basic equation:
      :math:`ET0_{new} = WfET0 \\cdot KE \\cdot PET +
      (1-WfET0) \\cdot ET0_{alt}`

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
    REQUIREDSEQUENCES = (
        lland_inputs.PET,
    )
    UPDATEDSEQUENCES = (
        lland_logs.WET0,
    )
    RESULTSEQUENCES = (
        lland_fluxes.ET0,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = (con.wfet0[k] * con.ke[k] * inp.pet +
                          (1. - con.wfet0[k]) * log.wet0[0, k])
            log.wet0[0, k] = flu.et0[k]


class Calc_EvPo_V1(modeltools.Method):
    """Calculate land use and month specific values of potential
    evapotranspiration.

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
        >>> fluxes.evpowater
        evpowater(2.608, 2.73)

        .. testsetup::

            >>> del pub.timegrids
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FLn,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.ET0,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvPo,
        lland_fluxes.EvPoWater,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.evpo[k] = \
                con.fln[con.lnk[k] - 1, der.moy[model.idx_sim]] * flu.et0[k]
            flu.evpowater[k] = flu.evpo[k]


class Calc_NBes_Inzp_V1(modeltools.Method):
    """Calculate stand precipitation and update the interception storage
    accordingly.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`NBes = \\Bigl \\lbrace
      {
      {PKor \\ | \\ Inzp = KInz}
      \\atop
      {0 \\ | \\ Inzp < KInz}
      }`

    Examples:

        Initialize five HRUs with different land usages:

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
    REQUIREDSEQUENCES = (
        lland_fluxes.NKor,
    )
    UPDATEDSEQUENCES = (
        lland_states.Inzp,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NBes,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.nbes[k] = 0.
                sta.inzp[k] = 0.
            else:
                flu.nbes[k] = (
                    max(flu.nkor[k] + sta.inzp[k] -
                        der.kinz[con.lnk[k] - 1, der.moy[model.idx_sim]], 0.)
                )
                sta.inzp[k] += flu.nkor[k] - flu.nbes[k]


class Calc_SN_Ratio_V1(modeltools.Method):
    """Calculate the ratio of frozen to total precipitation.

    Examples:

        In the first example, the threshold temperature of seven hydrological
        response units is 0 °C and the corresponding temperature interval of
        mixed precipitation 2 °C:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> tgr(1.0)
        >>> tsp(2.0)

        The value of |SN_Ratio| is zero above 1 °C and 1 below -1 °C.  Between
        these temperature values, |SN_Ratio| decreases linearly:

        >>> fluxes.nkor = 4.0
        >>> fluxes.tkor = -9.0, 0.0, 0.5, 1.0, 1.5, 2.0, 11.0
        >>> model.calc_sn_ratio_v1()
        >>> aides.sn_ratio
        sn_ratio(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)

        Note the special case of a zero temperature interval.  With the
        actual temperature being equal to the threshold temperature, the
        the value of `sbes` is zero:

        >>> tsp(0.0)
        >>> model.calc_sn_ratio_v1()
        >>> aides.sn_ratio
        sn_ratio(1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.TGr,
        lland_control.TSp,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_aides.SN_Ratio,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if flu.tkor[k] >= (con.tgr[k]+con.tsp[k]/2.):
                aid.sn_ratio[k] = 0.
            elif flu.tkor[k] <= (con.tgr[k]-con.tsp[k]/2.):
                aid.sn_ratio[k] = 1.
            else:
                aid.sn_ratio[k] = (
                    ((con.tgr[k]+con.tsp[k]/2.)-flu.tkor[k])/con.tsp[k])


class Calc_SKor_V1(modeltools.Method):
    """Calculate the frozen part of precipitation.

    Basic equation:
      :math:`SKor = SN_Ratio \\cdot NKor`

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> aides.sn_ratio = 0.0, 0.5, 1.0
        >>> fluxes.nkor = 4.0
        >>> model.calc_skor_v1()
        >>> fluxes.skor
        skor(0.0, 2.0, 4.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_aides.SN_Ratio,
        lland_fluxes.NKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SKor,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            flu.skor[k] = aid.sn_ratio[k]*flu.nkor[k]


class Calc_F2SIMax_V1(modeltools.Method):
    """
    Factor for calculation of snow interception capacity.

    Basic equation:
       :math:`F2SIMax = \\Bigl \\lbrace
       {
       {2.0 \\ | \\ TKor > -1°C}
       \\atop
       {2.5 + 0.5 \\cdot TKor \\ | \\ -3.0 °C \\leq TKor \\leq -1.0 °C}
       \\atop
       {1.0 \\ | \\ TKor < -3.0 °C}
       }`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> fluxes.tkor(-5.0, -3.0, -2.0, -1.0,  0.0)
        >>> model.calc_f2simax()
        >>> fluxes.f2simax
        f2simax(1.0, 1.0, 1.5, 2.0, 2.0)

    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.F2SIMax,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if flu.tkor[k] < -3.:
                flu.f2simax[k] = 1.
            elif (flu.tkor[k] >= -3.) and (flu.tkor[k] <= -1.):
                flu.f2simax[k] = 2.5 + 0.5*flu.tkor[k]
            else:
                flu.f2simax[k] = 2.0


class Calc_SInzpCap_V1(modeltools.Method):
    """
    Snow interception capacity

    Basic equation:
       :math:`SInzpCap = F1SIMax * F2SIMax`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> lnk(ACKER, LAUBW, NADELW)
        >>> derived.moy = 5
        >>> derived.f1simax.acker_jun = 9.5
        >>> derived.f1simax.laubw_jun = 11.0
        >>> derived.f1simax.nadelw_jun = 12.0
        >>> fluxes.f2simax(1.5)
        >>> model.calc_sinzpcap_v1()
        >>> fluxes.sinzpcap
        sinzpcap(14.25, 16.5, 18.0)
        >>> derived.moy = 0
        >>> derived.f1simax.acker_jan = 6.0
        >>> derived.f1simax.laubw_jan = 6.5
        >>> derived.f1simax.nadelw_jan = 10.0
        >>> model.calc_sinzpcap_v1()
        >>> fluxes.sinzpcap
        sinzpcap(9.0, 9.75, 15.0)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.F1SIMax,
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.F2SIMax,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SInzpCap,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.sinzpcap[k] = (
                der.f1simax[con.lnk[k] - 1, der.moy[model.idx_sim]] *
                flu.f2simax[k])


class Calc_F2SIRate_V1(modeltools.Method):
    """
    Factor for calculation of snow interception capacity.

    Basic equation:
       :math:`F2SIRate =

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> p3sirate(0.003)
        >>> states.stinz = 0.0, 0.5, 1.0, 5.0, 10.0
        >>> model.calc_f2sirate()
        >>> fluxes.f2sirate
        f2sirate(0.0, 0.0015, 0.003, 0.015, 0.03)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.P3SIRate,
    )
    REQUIREDSEQUENCES = (
        lland_states.STInz,
    )
    RESULTSEQUENCES = (
        lland_fluxes.F2SIRate,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            flu.f2sirate[k] = sta.stinz[k] * con.p3sirate


class Calc_SInzpRate_V1(modeltools.Method):
    """
    Snow interception rate

    Basic equation:
       :math:`SInzpRate = min(F1SIRate + F2SIRate; 1)`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> derived.f1sirate.acker_jan = 0.22
        >>> derived.f1sirate.laubw_jan = 0.30
        >>> derived.f1sirate.nadelw_jan = 0.32
        >>> fluxes.f2sirate = 0.0015, 0.003, 0.015
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.F1SIRate,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.F2SIRate,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SInzpRate,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        # ToDo: Stimmt 1 min oder max?
        for k in range(con.nhru):
            flu.sinzprate[k] = min(
                der.f1sirate[con.lnk[k] - 1, der.moy[model.idx_sim]] +
                flu.f2sirate[k], 1)


class Calc_NBes_SInz_V1(modeltools.Method):
    """Update interception storage.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> lnk(ACKER, NADELW, NADELW, NADELW)
        >>> # states.sinz()
        >>> # states.stinz()
        >>> # fluxes.sinzcap()
        >>> # fluxes.sinzrate()
        >>> # fluxes.nkor()
        >>> # model.calc_nbes_sinz()
        >>> # fluxes.sbes
        >>> # fluxes.nbes
        >>> # states.stinz
        >>> # states.sinz
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SInzpRate,
        lland_fluxes.NKor,
        lland_fluxes.SInzpCap,
        lland_aides.SN_Ratio,
    )
    UPDATEDSEQUENCES = (
        lland_states.SInz,
        lland_states.STInz,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NBes,
        lland_fluxes.SBes,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        sta = model.sequences.states.fastaccess
        # ToDo
        c_temp = 1
        # for k in range(con.nhru):
        #     if con.lnk[k] in (WASSER, FLUSS, SEE):
        #         sta.sinz[k] = 0.
        #     elif con.lnk[k] == NADELW:
        #         if flu.nkor[k] > flu.sinzprate[k]:
        #             d_max = flu.sinzprate[k]
        #             d_besrate = flu.nkor[k] - flu.sinzprate[k]
        #         else:
        #             d_max = flu.nkor[k]
        #             d_besrate = 0
        #         d_cap = flu.sinzpcap[con.lnk[k] - 1, der.moy[model.idx_sim]]
        #
        #         flu.nbes[k] = max(d_max + sta.sinz[k] - d_cap, 0.) + d_besrate
        #         flu.sbes[k] = aid.sn_ratio[k] * flu.nbes[k]
        #         d_ninz = flu.nkor[k] - flu.nbes[k]
        #         d_sinz = aid.sn_ratio[k] * d_ninz
        #         sta.sinz[k] += d_ninz
        #         sta.stinz[k] += d_sinz
        #         d_nbes = max(sta.sinz[k] - con.pwmax[k] * sta.stinz[k], 0.)
        #         flu.nbes[k] += d_nbes
        #         sta.sinz[k] -= d_nbes


class Calc_SBes_V1(modeltools.Method):
    """Calculate the frozen part of stand precipitation.

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(1)
        >>> fluxes.nbes(10.0)
        >>> aides.sn_ratio(0.8)
        >>> model.calc_sbes_v1()
        >>> fluxes.sbes
        sbes(8.0)
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_aides.SN_Ratio,
        lland_fluxes.NBes,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SBes,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            flu.sbes[k] = aid.sn_ratio[k] * flu.nbes[k]


class Calc_WATS_V1(modeltools.Method):
    """Add the snow fall to the frozen water equivalent of the snow cover.

    Basic equation:
      :math:`WATS = WATS + SBes`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(FLUSS, ACKER)
        >>> fluxes.sbes(2.0)
        >>> states.wats = 5.5
        >>> model.calc_wats_v1()
        >>> states.wats
        wats(0.0, 7.5)
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
    )
    UPDATEDSEQUENCES = (
        lland_states.WATS,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.wats[k] = 0.
            else:
                sta.wats[k] += flu.sbes[k]


class Calc_WaDa_WAeS_V1(modeltools.Method):
    """Add as much precipitation to the snow cover as it is able to hold.

    Basic equations:
      :math:`\\frac{dWAeS}{dt} = NBes - WaDa`

      :math:`WAeS \\leq PWMax \\cdot WATS`

    Examples:

        For simplicity, the threshold parameter |PWMax| is set to a value
        of two for each of the six initialized HRUs.  Thus, snow cover can
        hold as much liquid water as it contains frozen water.  Stand
        precipitation is also always set to the same value, but we vary the
        initial conditions of the snow cover:

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

        Note the special cases of the first two HRUs of type |FLUSS| and
        |SEE|.  For water areas, stand precipitaton |NBes| is generally
        passed to |WaDa| and |WAeS| is set to zero.  For all other land
        use classes (of which only |ACKER| is selected), only the amount
        of |NBes| exceeding the actual snow holding capacity is passed
        to |WaDa|.
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
    UPDATEDSEQUENCES = (
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WaDa,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.waes[k] = 0.
                flu.wada[k] = flu.nbes[k]
            else:
                sta.waes[k] += flu.nbes[k]
                flu.wada[k] = max(sta.waes[k]-con.pwmax[k]*sta.wats[k], 0.)
                sta.waes[k] -= flu.wada[k]


class Calc_WGTF_V1(modeltools.Method):
    """Calculate the heat flux according to the degree-day method.

    Basic equation:
      :math:`WGTF = GTF \\cdot (TKor - TRefT) \\cdot RSchmelz`

    Examples:

        Initialize seven HRUs with identical degree-day factors and
        temperature thresholds, but different combinations of land use
        and air temperature:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(7)
        >>> lnk(ACKER, LAUBW, FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> gtf(5.0)
        >>> treft(0.0)
        >>> trefn(1.0)
        >>> fluxes.tkor = 2.0, 2.0, 2.0, 2.0, -1.0, 0.0, 1.0

        Compared to most other LARSIM parameters, the specific heat capacity
        and melt heat capacity of water can be seen as fixed properties
        (0.334 MJ/kg):

        >>> rschmelz(0.334)

        Note that the values of the degree-day factor are only half
        as much as the given value, due to the simulation step size
        being only half as long as the parameter step size:

        >>> gtf
        gtf(5.0)
        >>> gtf.values
        array([ 2.5,  2.5,  2.5,  2.5,  2.5,  2.5,  2.5])

        After performing the calculation, one can see that the potential
        melting rate is identical for the first two HRUs (|ACKER| and
        |LAUBW|).  The land use class results in no difference, except for
        water areas (third and forth HRU, |FLUSS| and |SEE|), where no
        potential melt needs to be calculated.  The last three HRUs (again
        |ACKER|) show the usual behaviour of the degree day method, when the
        actual temperature is below (fourth HRU), equal to (fifth HRU) or
        above (sixths zone) the threshold temperature.  Additionally, the
        first two zones show the influence of the additional energy intake
        due to "warm" precipitation.  Obviously, this additional term is
        quite negligible for common parameterizations, even if lower
        values for the separate threshold temperature |TRefT| would be
        taken into account:

        >>> model.calc_wgtf_v1()
        >>> fluxes.wgtf
        wgtf(1.67, 1.67, 1.67, 1.67, -0.835, 0.0, 0.835)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.GTF,
        lland_control.TRefT,
        lland_control.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WGTF,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.wgtf[k] = con.gtf[k]*(flu.tkor[k]-con.treft[k])*con.rschmelz


class Calc_WNied_V1(modeltools.Method):
    """Calculate the heat flux caused by liquid precipitation on snow.

    We assume that the temperature of precipitation equals air temperature
    and |TRefN| equals the reference temperature to define whether the energy
    input is positive or negative (normally 0°C).

    # ToDo: TREfN entspricht surface temperature des Schnees?

    Basic equation:
      :math:`WNied = cp_{w} \\cdot (TKor - TRefN) \\cdot NKor \\cdot
      \\varrho_{W}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> cpwasser(0.0041868)
        >>> fluxes.tkor(1.0)
        >>> trefn(0.0, 0.5)
        >>> fluxes.nbes(10.0)
        >>> model.calc_wnied_v1()
        >>> fluxes.wnied
        wnied(0.041868, 0.020934)
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.TRefN,
        lland_control.CPWasser,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.NBes,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WNied,
    )

    # todo: Unterscheidung fester/flüssiger Niederschlag

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.wnied[k] = (
                    con.cpwasser *
                    (flu.tkor[k] - con.trefn[k]) *
                    flu.nbes[k])


class Calc_WNied_V2(modeltools.Method):
    """Calculate the heat flux due to precipitation falling on a snow layer.

    We assume that the temperature of precipitation equals air temperature.
    The same holds for the temperature of the fraction of precipitation not
    hold by the snow layer (in other words: no temperature mixing occurs).
    In contrast to method |Calc_WNied_V1|, method |Calc_WNied_V1| does
    not use parameter |TRefN|. Hence, the "energy input threshold" is
    effectively always 0 °C.

    Basic equation:
      :math:`WNied = TKor \\cdot
      (CPEis \\cdot SBes + CPWasser \\cdot (NBes - SBes - WaDa))`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> cpwasser(0.0041868)
        >>> cpeis(0.00206)
        >>> fluxes.tkor = 3.0, -1.0, -1.0, -1.0, -1.0
        >>> fluxes.nbes = 10.0
        >>> fluxes.sbes = 0.0, 0.0, 5.0, 10.0, 5.0
        >>> fluxes.wada = 0.0, 0.0, 0.0, 0.0, 5.0
        >>> model.calc_wnied_v2()
        >>> fluxes.wnied
        wnied(0.125604, -0.041868, -0.031234, -0.0206, -0.0103)
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.CPWasser,
        lland_control.CPEis,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.NBes,
        lland_fluxes.SBes,
        lland_fluxes.WaDa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WNied,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.wnied[k] = (
                flu.tkor[k] *
                (con.cpeis*flu.sbes[k] +
                 con.cpwasser*(flu.nbes[k]-flu.sbes[k]-flu.wada[k]))
            )


class Update_ESnow_V1(modeltools.Method):
    """Update the heat content of the snow layer regarding the thermal
    energy of precipitation.

    Basic equation:
      :math:`\\frac{ESnow}{dt} = WNied`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> states.waes =  1.0, 1.0, 0.0
        >>> states.esnow = 0.0, 1.0, 2.0
        >>> fluxes.wnied = -1.0, 1.0, 1.0
        >>> model.update_esnow_v1()
        >>> states.esnow
        esnow(-1.0, 2.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_states.WAeS,
        lland_fluxes.WNied,
    )
    UPDATEDSEQUENCES = (
        lland_states.ESnow,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                sta.esnow[k] += flu.wnied[k]
            else:
                sta.esnow[k] = 0.
            # ToDo: esnow = nan?
            # if modelutils.isnan(sta.esnow[k]):
            #     sta.esnow[k] = 0.
            # else:
            #     sta.esnow[k] += flu.wnied[k]


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    """Calculate the saturation vapour pressure.

    For further documentation see |Calc_SaturationVapourPressure_Single_V1|.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkor(-10.0, 0.0, 10.0)
        >>> model.calc_saturationvapourpressure_v1()
        >>> fluxes.saturationvapourpressure
        saturationvapourpressure(0.285096, 0.6108, 1.229426)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SaturationVapourPressure,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        con = model.parameters.control.fastaccess
        for k in range(con.nhru):
            flu.saturationvapourpressure[k] = \
                model.calc_saturationvapourpressure_single_v1(flu.tkor[k])
            

class Calc_SaturationVapourPressure_Single_V1(modeltools.Method):
    """Calculate the saturation vapour pressure for a given temperature.
    The used formula is considered for the calculation of saturation vapour
    pressure over water surfaces.

    Basic equation (`Allen`_):
      :math:`SaturationVapourPressure = 0.6108 \\cdot
      \\exp(\\frac{17.08085 \\cdot TKor}{TKor + 234.175})`

    # ToDo: fester Begriff für "Single"

    |Calc_SaturationVapourPressure_Single_V1| is a 'Single' method which means
    that this method cannot be directly used by an application model. It needs
    to be called by an other method which hands the actual |NHRU|.

    Additionally this method needs a temperature as parameter and returns the
    saturation vapour pressure for the given temperature for the current |NHRU|.

    The following example shows how this method is used in the method
    |Calc_SaturationVapourPressure_V1| which uses the air temperature as
    parameter.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkor(-10.0, 0.0, 10.0)
        >>> model.calc_saturationvapourpressure_v1()
        >>> fluxes.saturationvapourpressure
        saturationvapourpressure(0.285096, 0.6108, 1.229426)
    """
    
    @staticmethod
    def __call__(model: modeltools.Model, t: float) -> float:
        return .6108*modelutils.exp(17.08085 * t / (t + 234.175))


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    """Calculate the slope of the saturation vapour pressure curve.

    Basic equation (`Allen`_, equation 13):
      :math:`SaturationVapourPressureSlope = 4098 \\cdot
      \\frac{SaturationVapourPressure}{(TKor+237.3)^2}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkor(-10.0, 0.0, 10.0)
        >>> fluxes.saturationvapourpressure(0.285096, 0.6108, 1.229426)
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> fluxes.saturationvapourpressureslope
        saturationvapourpressureslope(0.022613, 0.04445, 0.082381)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SaturationVapourPressureSlope,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.saturationvapourpressureslope[k] = \
                4098.*flu.saturationvapourpressure[k]/(flu.tkor[k]+237.3)**2


class Calc_ActualVapourPressure_V1(modeltools.Method):
    """Calculate the actual vapour pressure.

    For further documentation see |Calc_ActualVapourPressure_Single_V1|

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> inputs.relativehumidity = 60.0
        >>> fluxes.saturationvapourpressure = 2.0, 1.8, 1.5
        >>> model.calc_actualvapourpressure_v1()
        >>> fluxes.actualvapourpressure
        actualvapourpressure(1.2, 1.08, 0.9)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
        lland_fluxes.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (
        lland_fluxes.ActualVapourPressure,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.actualvapourpressure[k] = (
                model.calc_actualvapourpressure_single_v1(
                    flu.saturationvapourpressure[k]))


class Calc_ActualVapourPressure_Single_V1(modeltools.Method):
    """Calculate the actual vapour pressure for a single |NHRU| for a given
    saturation vapour pressure.

    Basic equation (`Allen`_, equation 19, modified):
      :math:`ActualVapourPressure = SaturationVapourPressure \\cdot
      RelativeHumidity / 100`

    Calc_ActualVapourPressure_Single_V1 is a 'Single' method which means
    that this method cannot be directly used by an application model.

    This method needs a saturation vapour pressure as parameter and returns the
    actual vapour pressure for the given temperature.

    The following example shows how this method is used in the method
    |Calc_ActualVapourPressure| which uses the |SaturationVapourPressure| as
    parameter.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> inputs.relativehumidity = 60.0
        >>> fluxes.saturationvapourpressure = 2.0, 1.8, 1.5
        >>> model.calc_actualvapourpressure_v1()
        >>> fluxes.actualvapourpressure
        actualvapourpressure(1.2, 1.08, 0.9)
    """

    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model,
                 saturationvapourpressure: float) -> float:
        inp = model.sequences.inputs.fastaccess
        return saturationvapourpressure * inp.relativehumidity/100.


class Calc_NetLongwaveRadiation_V1(modeltools.Method):
    """Calculate the net longwave radiation for snow free surfaces.

    For further documentation see |Calc_NetLongwaveRadiation_Single_V1|.

    Example:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nhru(3)
        >>> derived.seconds(60*60*24)
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> derived.nmblogentries.update()
        >>> fluxes.tkor = 22.1, 0.0, 0.0
        >>> fluxes.actualvapourpressure = 1.6, 0.6, 0.6
        >>> fluxes.possiblesunshineduration = 14.0
        >>> inputs.sunshineduration = 12.0
        >>> logs.loggedpossiblesunshineduration = 14.0
        >>> logs.loggedsunshineduration = 12.0
        >>> emissivity(0.95)
        >>> fratm(1.28)
        >>> states.waes = 0.0, 0.0, 1.0
        >>> fluxes.tempssurface = nan, nan, 0.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.495045, 5.027685, 6.949137)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Emissivity,
        lland_control.FrAtm,
    )
    DERIVEDPARAMETERS = (
        lland_derived.NmbLogEntries,
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_states.WAeS,
        lland_fluxes.ActualVapourPressure,
        lland_logs.LoggedPossibleSunshineDuration,
        lland_logs.LoggedSunshineDuration,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        for k in range(con.nhru):
            model.calc_netlongwaveradiation_single_v1(k)


class Calc_NetLongwaveRadiation_Single_V1(modeltools.Method):
    """Calculates the net longwave radiation.

    Basic Equation (above a snow layer):
       :math:`NetLongwaveRadiation= -(5.67e-14 \\cdot Seconds \\cdot (TKor +
       273.15)^4 \\cdot (FrAtm \\cdot (ActualVapourPressure \\cdot \\frac{10}
       {TKor + 273.15})^{\\frac{1}{7}}-Emissivity) \\cdot (0.2+0.8 \\cdot
       (\frac{SunshineDuration}{PossibleSunshineDuration})))`

    Basic Equation (above snow-free surfaces):
       :math:`NetLongwaveRadiation = (5.67e-14 \\cdot Seconds \\cdot
       (TempSSurface+273.15)^4 - 5.67e-14 \\cdot Seconds \\cdot
       (Tkor + 273.15)^4 \\cdot FrAtm \\cdot (ActualVapourPressure \\cdot
       \\frac{10}{TKor[k] + 273.15})^{\\frac{1}{7}} \\cdot (1 + 0.22
       \\cdot (1-\frac{SunshineDuration}{PossibleSunshineDuration})^2))`

    |Netlongwaveradiation| uses two different formulas. One if the surface is
    snow covered (and the snow surface temperature is calculated) and the
    other one if there is no snow (and thus no snow surface temperature is
    calculated).

    Example:

        ToDo: update doc

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> emissivity(0.95)
        >>> fratm(1.28)
        >>> derived.seconds.update()
        >>> derived.nmblogentries.update()
        >>> inputs.sunshineduration = 12.0
        >>> states.waes = 0.0, 0.0, 1.0, 1.0
        >>> fluxes.tkor = 22.1, 0.0, 0.0, 0.0
        >>> fluxes.actualvapourpressure = 1.6, 0.6, 0.6, 0.6
        >>> fluxes.possiblesunshineduration = 14.0
        >>> fluxes.tempssurface = nan, nan, 0.0, -5.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.495045, 5.027685, 6.949137, 5.006517)

        If we set the current sunshineduration to 0 we get the same value as
        above since we logged the sunshine duration:

        >>> inputs.possiblesunshineduration = 0.0
        >>> logs.loggedsunshineduration = 12.0
        >>> logs.loggedpossiblesunshineduration = 14.0

        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.495045, 5.027685, 6.949137, 5.006517)

        .. testsetup::

            >>> del pub.timegrids
    """
    # todo Wert für langwellige Strahlung ohne Schnee weicht stark ab!
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Emissivity,
        lland_control.FrAtm,
    )
    DERIVEDPARAMETERS = (
        lland_derived.NmbLogEntries,
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_states.WAeS,
        lland_fluxes.ActualVapourPressure,
        lland_inputs.SunshineDuration,
        lland_logs.LoggedPossibleSunshineDuration,
        lland_logs.LoggedSunshineDuration,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NetLongwaveRadiation,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess

        if flu.possiblesunshineduration > 0:
            d_sunshineduration = inp.sunshineduration
            d_possiblesunshineduration = flu.possiblesunshineduration
            # todo: Hier sollte es eine Warnung geben, wenn Sonnenscheindauer >
            #  possiblesunshineduration
        else:
            d_sunshineduration = 0.
            d_possiblesunshineduration = 0.
            for idx in range(der.nmblogentries):
                d_possiblesunshineduration += \
                    log.loggedpossiblesunshineduration[idx]
                d_sunshineduration += log.loggedsunshineduration[idx]

        d_relsunshine = d_sunshineduration/d_possiblesunshineduration

        d_temp1 = 5.67e-14 * der.seconds * (flu.tkor[k] + 273.15) ** 4
        d_temp2 = (flu.actualvapourpressure[k] * 10. /
                   (flu.tkor[k] + 273.15)) ** (1. / 7.)
        if sta.waes[k] == 0.0:
            flu.netlongwaveradiation[k] = -(
                d_temp1*(con.fratm*d_temp2-con.emissivity) *
                (.2+.8*d_relsunshine))
        else:
            flu.netlongwaveradiation[k] = (
                5.67e-14*der.seconds*(flu.tempssurface[k]+273.15)**4 -
                d_temp1*con.fratm*d_temp2*(1.+.22*(1.-d_relsunshine)**2))
        # todo: 1.28 als möglicher Kalibrierparameter (FRatm) Nicht in
        #  Tape35 enthalten?
        # todo: Konstanten: Stefan Boltzmann-Konstante:
        #  5.67 * 10^(-14) MW/m²/K^4
        # todo: Vorsicht bei anderen Schneeoptionen


class Update_TauS_V1(modeltools.Method):
    """Calculate the dimensionless age of the snow layer.

    Basic equations:
      :math:`TauS* = TauS \\cdot max(1 - 0.1 \\cdot SBes), 0)`

      :math:`TauS = TauS* + \\frac{r_1+r_2+r_3}{10^6} \\cdot Seconds`

      :math:`r_1 = exp(5000 \\cdot
      (\\frac{1}{273.15} - \\frac{1}{273.15+TempS}))`

      :math:`r_2 = min(r_1^{10}, 1)`

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
        lland_fluxes.TKor,
        lland_states.WAeS,
        lland_aides.TempS,
    )
    RESULTSEQUENCES = (
        lland_states.TauS,
    )
    
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
                    sta.taus[k] = 0
                d_r1 = modelutils.exp(5000*(1/273.15-1/(273.15+aid.temps[k])))
                d_r2 = min(d_r1**10, 1)
                sta.taus[k] *= max(1-0.1*flu.sbes[k], 0)
                sta.taus[k] += (d_r1+d_r2+0.03)/1e6*der.seconds
            else:
                sta.taus[k] = modelutils.nan


class Calc_AlbedoCorr_V1(modeltools.Method):
    """Calculate the current albedo value.

    For snow-free surfaces, method |Calc_AlbedoCorr_V1| uses takes the
    value of parameter |Albedo| relevant for the given landuse and month.
    For snow surfaces, it estimates the albedo based on the snow age, as
    shown by the following equation:

    Basic equations:
      :math:`AlbedoSnow = Albedo0Snow \\cdot
      (1-SnowAgingFactor \\cdot \\frac{TauS}{1 + TauS})`

    Example:

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
        >>> model.calc_albedocorr_v1()
        >>> fluxes.albedocorr
        albedocorr(0.2, 0.3, 0.8, 0.66, 0.59)
        >>> model.idx_sim = 2
        >>> model.calc_albedocorr_v1()
        >>> fluxes.albedocorr
        albedocorr(0.4, 0.5, 0.8, 0.66, 0.59)

        .. testsetup::

            >>> del pub.timegrids
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.SnowAgingFactor,
        lland_control.Albedo0Snow,
        lland_control.Albedo,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_states.TauS,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.AlbedoCorr,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] <= 0.:
                flu.albedocorr[k] = \
                    con.albedo[con.lnk[k]-1, der.moy[model.idx_sim]]
            else:
                flu.albedocorr[k] = (
                    con.albedo0snow *
                    (1.-con.snowagingfactor*sta.taus[k]/(1.+sta.taus[k])))


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    """Calculate the net shortwave radiation.

    Basic equation (`Allen`_, equation 38):
      :math:`NetShortwaveRadiation = (1.0 - Albedo) \\cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.albedocorr(0.23, 0.5)
        >>> fluxes.globalradiation = 20.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(15.4, 10.0)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.GlobalRadiation,
        lland_fluxes.AlbedoCorr,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NetShortwaveRadiation,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.netshortwaveradiation[k] = \
                (1. - flu.albedocorr[k]) * flu.globalradiation


class Calc_TempS_V1(modeltools.Method):
    """Calculate the average temperature of the snow layer.

    ToDo: states.fastaccess_old.waes statt fastaccess.esnow?

    Basic equation:
      :math:`TempS = \\frac{E_{snow}}{WATS \\cdot
      \\varrho_{w} \\cdot cp_{eis} + (WAeS-WATS)\\cdot cp_{wasser}}`

    If there is no snow (|WAeS| = 0), |TempS| is set to NaN..

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> pwmax(2.0)
        >>> cpwasser(0.0041868)
        >>> cpeis(0.00209)
        >>> fluxes.tkor(-1.0)
        >>> states.wats(0.0, 0.5, 5)
        >>> states.waes(0.0, 1.0, 10)
        >>> states.esnow(nan, 0.0, -0.1)
        >>> model.calc_temps_v1()
        >>> aides.temps
        temps(nan, 0.0, -3.186337)
    """

    CONTROLPARAMETERS = (
        lland_control.CPWasser,
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_states.WATS,
        lland_states.WAeS,
        lland_states.ESnow,
        lland_fluxes.SBes,
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_aides.TempS,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                aid.temps[k] = (
                    sta.esnow[k] /
                    (sta.wats[k]*con.cpeis +
                     (sta.waes[k]-sta.wats[k])*con.cpwasser))
            else:
                aid.temps[k] = modelutils.nan


class Calc_TZ_V1(modeltools.Method):
    """Calculate mean soil temperature accounting for the thawing of soil water.

    Basic equations:

    Energy to melt the complete soil water:
      :math:`d_melt = BoWa2Z \\cdot RSchmelz \\cdot \\varrho_{W}`

    Completely frozen soil (EBdn < 0):
      :math:`TZ = \\frac{EBdn}{2 \\cdot z \\cdot \\varrho_{W} \\cdot c_G}`

    Partly frozen soil (0 < EBdn < Melt)
      :math:`TZ = 0`

    Unfrozen soil (EBdn < 0)
      :math:`TZ = \\frac{EBdn - d_melt}{2 \\cdot z \\cdot
      \\varrho_{W} \\cdot c_G}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> cg(1.5)
        >>> z(0.1)
        >>> derived.heatoffusion(26.72)
        >>> states.ebdn(-10.0, -1.0, 0.0, 13.36, 26.72, 27.72, 36.72)
        >>> model.calc_tz_v1()
        >>> fluxes.tz
        tz(-33.333333, -3.333333, 0.0, 0.0, 0.0, 3.333333, 33.333333)
        """
    CONTROLPARAMETERS = (
        lland_control.CG,
        lland_control.Z,
    )
    DERIVEDPARAMETERS = (
        lland_derived.HeatOfFusion,
    )
    REQUIREDSEQUENCES = (
        lland_states.EBdn,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TZ,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.ebdn[k] >= der.heatoffusion[k]:
                flu.tz[k] = \
                    (sta.ebdn[k]-der.heatoffusion[k])/(2*con.z*con.cg[k])
            elif sta.ebdn[k] <= 0:
                flu.tz[k] = sta.ebdn[k]/(2*con.z*con.cg[k])
            else:
                flu.tz[k] = 0.


class Calc_WG_V1(modeltools.Method):
    """Calculate the soil heat flux.

    The soil heat flux depends on the temperature gradient between depth z
    and the surface.  We set the soil surface temperature to the air
    temperature for snow-free conditions and otherwise to the average
    temperature of the snow layer.

    Basic equations:
      :math:`WG = \\lambda_{G} \\cdot \\frac{T-T_z}{z} \\cdot Seconds`

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> z(0.1)
        >>> derived.seconds(24*60*60)
        >>> fluxes.tz = 2.0
        >>> fluxes.tkor = 10.0
        >>> states.waes = 0.0, 1.0
        >>> aides.temps = nan, -1.0
        >>> model.calc_wg_v1()
        >>> fluxes.wg
        wg(-4.1472, 1.5552)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Z,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TZ,
        lland_fluxes.TKor,
        lland_states.WAeS,
        lland_aides.TempS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WG,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                d_t0 = aid.temps[k]  # ToDo
                # d_t0 = flu.tkor[k]  # ToDo
            else:
                d_t0 = flu.tkor[k]
            flu.wg[k] = 6.e-7*(flu.tz[k]-d_t0)/con.z*der.seconds
        # todo: Konstante: 0.6e-6 MW/m °C (Wärmeleitfähigkeit des Bodens)


class Update_EBdn_V1(modeltools.Method):
    """Aktualisiere den Energieinhalt der oberen Bodensäule bis zu einer Tiefe
    von 2z

    Basic equation:
      :math:`EBdn = EBdn_{t-1} + W_G - W_{G2Z}`

    # ToDo: überall model.idx_sim explizit setzen

    Example:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nhru(3)
        >>> pub.timegrids = '2019-04-29', '2019-05-03', '1d'
        >>> derived.moy.update()
        >>> derived.seconds.update()
        >>> wg2z.apr = -0.03
        >>> wg2z.mai = -0.04
        >>> fluxes.wg(0.5, 1.0, 2.0)
        >>> states.ebdn(0.0)
        >>> model.idx_sim = 2
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(-0.54, -1.04, -2.04)
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(-1.08, -2.08, -4.08)

        >>> model.idx_sim = 1
        >>> states.ebdn(0.0)
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(-0.53, -1.03, -2.03)

        .. testsetup::

            >>> del pub.timegrids
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.WG2Z,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WG,
    )
    UPDATEDSEQUENCES = (
        lland_states.EBdn,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            sta.ebdn[k] += con.wg2z[der.moy[model.idx_sim]]-flu.wg[k]


class Calc_WSensSnow_Single_V1(modeltools.Method):
    """Calculate the sensible heat flux of the snow surface.

    Basic equations:
      :math:`WSensSnow  = (turb0 + turb1 \\cdot WindSpeed10m) \\cdot
      (TKor - TempsSurface)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> derived.seconds(24*60*60)
        >>> nhru(2)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fluxes.tkor = -2.0, -1.0
        >>> fluxes.tempssurface = -5.0, 0.0
        >>> fluxes.windspeed10m = 3.0
        >>> model.calc_wsenssnow_single_v1(0)
        >>> model.calc_wsenssnow_single_v1(1)
        >>> fluxes.wsenssnow
        wsenssnow(-2.0736, 0.6912)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Turb0,
        lland_control.Turb1,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.TempSSurface,
        lland_fluxes.WindSpeed10m,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WSensSnow,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.wsenssnow[k] = (
            (con.turb0+con.turb1*flu.windspeed10m) *
            (flu.tempssurface[k]-flu.tkor[k]) *
            der.seconds*1e-6)


class Calc_WLatSnow_Single_V1(modeltools.Method):
    """Calculate the latent heat flux of the snow surface.

    Basic equations:
      :math:`WLatSnow  = (turb0 + turb1 \\cdot WindSpeed10m) \\cdot
      (\\frac{1}{17.6\\,°C \\cdot kpa^-1}
      \\cdot(SaturationPressure - SaturationPressureSnow))`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> derived.seconds(24*60*60)
        >>> nhru(2)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fluxes.windspeed10m(3.0)
        >>> fluxes.actualvapourpressuresnow(0.4, 0.8)
        >>> for k in range(2):
        ...     model.calc_wlatsnow_single_v1(k)
        >>> fluxes.wlatsnow
        wlatsnow(-2.564407, 2.301641)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Turb0,
        lland_control.Turb1
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WindSpeed10m,  # todo: wirklich 10m?
        lland_fluxes.ActualVapourPressureSnow,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WLatSnow,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.wlatsnow[k] = (
            der.seconds*1e-6*(con.turb0+con.turb1*flu.windspeed10m) *
            (17.6*(flu.actualvapourpressuresnow[k]-.6108)))
        # todo: Psychrometerkonstante über Schnee berechnen??


class Calc_WSurf_Single_V1(modeltools.Method):
    """Calculate the snow surface heat flux.

    Basic equation:
      :math:`WSurf = (TempSSurface - TempS) \\cdot KT_{Schnee}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> derived.seconds(24*60*60)
        >>> fluxes.tempssurface = -3.0
        >>> aides.temps = -2.0
        >>> model.calc_wsurf_single_v1(0)
        >>> fluxes.wsurf
        wsurf(0.432)
    """
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_aides.TempS,
        lland_fluxes.TempSSurface,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WSurf,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.wsurf[k] = (aid.temps[k]-flu.tempssurface[k])*5.0e-6*der.seconds

        # todo: Konstante: Effektive Wärmeleitfähigkeit des Schnees: 5 W/m²/K
        #  Vorsicht! abhängig von Schneetiefe oberste Schneeschicht (KTSchnee)


class Calc_EnergyBalanceSurface_V1(modeltools.Method):
    """Calculate and return the net energy gain of the snow surface.

    As surface cannot store any energy, method |Calc_EnergyBalanceSurface_V1|
    returns zero if one supplies it with the correct temperature of
    the snow surface.  Hence, this methods provides a means to find this
    "correct" temperature via root finding algorithms.

    0 = Surf + Short - Long - Sens - Lat
    Basic equations:
      :math:`EnergyBalanceSurface = WSurf(TempSSurface) +
      NetshortwaveRadiation - NetlongwaveRadiation(TempSSurface) -
      WSensSnow(TempSSurface) - WLatSnow(TempSSurface)`

    See also the documentation of the following methods, used to calculate
    the individual energy terms:

     * |Calc_SaturationVapourPressure_Single_V1|
     * |Calc_ActualVapourPressure_Single_V1|
     * |Calc_NetLongwaveRadiation_Single_V1|
     * |Calc_WSensSnow_Single_V1|
     * |Calc_WLatSnow_Single_V1|
     * |Calc_WSurf_Single_V1|

    Example:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> derived.nmblogentries.update()
        >>> nhru(1)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fratm(1.28)
        >>> derived.seconds(24*60*60)
        >>> inputs.relativehumidity = 60.0
        >>> inputs.sunshineduration(10.0)
        >>> states.waes.values = 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiation = 2.0
        >>> fluxes.possiblesunshineduration = 12.0
        >>> logs.loggedsunshineduration = 10.0
        >>> logs.loggedpossiblesunshineduration = 12.0
        >>> aides.temps = -2.0
        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.calc_energybalancesurface_v1(-4.0))
        -0.454395
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.453927)
        >>> fluxes.actualvapourpressuresnow
        actualvapourpressuresnow(0.272356)
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(8.126801)
        >>> fluxes.wsenssnow
        wsenssnow(-0.6912)
        >>> fluxes.wlatsnow
        wlatsnow(-4.117207)
        >>> fluxes.wsurf
        wsurf(0.864)

        .. testsetup::

            >>> del pub.timegrids
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.FrAtm,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
        lland_states.WAeS,
        lland_fluxes.NetShortwaveRadiation,
        lland_fluxes.TKor,
        lland_fluxes.WindSpeed10m,
        lland_inputs.SunshineDuration,
        lland_fluxes.PossibleSunshineDuration,
        lland_logs.LoggedPossibleSunshineDuration,
        lland_logs.LoggedSunshineDuration,
        lland_aides.TempS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.ActualVapourPressureSnow,
        lland_fluxes.WSensSnow,
        lland_fluxes.WLatSnow,
        lland_fluxes.NetLongwaveRadiation,
        lland_fluxes.WSurf,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, tempssurface: float) -> float:
        flu = model.sequences.fluxes.fastaccess

        k = model.idx_hru

        flu.tempssurface[k] = tempssurface

        flu.saturationvapourpressuresnow[k] = \
            model.calc_saturationvapourpressure_single_v1(
                flu.tempssurface[k])
        flu.actualvapourpressuresnow[k] = \
            model.calc_actualvapourpressure_single_v1(
                flu.saturationvapourpressuresnow[k])
        model.calc_wlatsnow_single_v1(k)
        model.calc_wsenssnow_single_v1(k)
        model.calc_netlongwaveradiation_single_v1(k)
        model.calc_wsurf_single_v1(k)

        return (
            flu.wsurf[k] +
            flu.netshortwaveradiation[k] -
            flu.netlongwaveradiation[k] -
            flu.wsenssnow[k] -
            flu.wlatsnow[k]
        )


class Calc_TempSSurface_V1(modeltools.Method):
    """Determine the snow surface temperature.

    |Calc_TempsSurface_V1| needs to determine the snow surface temperature
    via iteration.  Therefore, it uses the class |PegasusTempSSurface|
    which searche the root of the net energy gain of the snow surface
    define by method |Calc_EnergyBalanceSurface_V1|.

    For snow-free conditions, method |Calc_TempsSurface_V1| sets the value
    of |TempSSurface| to |numpy.nan| and the values of |WSensSnow|,
    |WLatSnow|, and |WSurf| to zero.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(5)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fratm(1.28)
        >>> derived.seconds(24*60*60)
        >>> inputs.sunshineduration = 10.0
        >>> inputs.relativehumidity = 60.0
        >>> states.waes.values = 0.0, 1.0, 1.0, 1.0, 1.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiation = 1.0, 1.0, 2.0, 2.0, 2.0
        >>> fluxes.possiblesunshineduration = 12.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> aides.temps = nan, -2.0, -2.0, -50.0, -200.0

        >>> control.tempssurfaceflag(True)
        >>> model.calc_tempssurface_v1()
        >>> fluxes.tempssurface
        tempssurface(nan, -4.832608, -4.259254, -16.889144, -63.201335)

        >>> from hydpy import print_values
        >>> print_values(fluxes.netshortwaveradiation -
        ...              fluxes.netlongwaveradiation -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, 0.0, 0.0, 0.0, 0.0

        >>> control.tempssurfaceflag(False)
        >>> model.calc_tempssurface_v1()
        >>> fluxes.tempssurface
        tempssurface(nan, -2.0, -2.0, -50.0, -200.0)

        >>> from hydpy import print_values
        >>> print_values(fluxes.netshortwaveradiation -
        ...              fluxes.netlongwaveradiation -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, -5.008511, -4.008511, 47.307802, 163.038145
        >>> fluxes.wsurf
        wsurf(0.0, 0.0, 0.0, 0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.FrAtm,
        lland_control.TempSSurfaceFlag,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
        lland_inputs.SunshineDuration,
        lland_fluxes.NetShortwaveRadiation,
        lland_fluxes.WNied,
        lland_fluxes.TKor,
        lland_fluxes.WindSpeed10m,
        lland_fluxes.PossibleSunshineDuration,
        lland_states.WAeS,
        lland_aides.TempS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SaturationVapourPressureSnow,
        lland_fluxes.ActualVapourPressureSnow,
        lland_fluxes.TempSSurface,
        lland_fluxes.WSensSnow,
        lland_fluxes.WLatSnow,
        lland_fluxes.NetLongwaveRadiation,
        lland_fluxes.WSurf,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        aid = model.sequences.aides.fastaccess
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                if con.tempssurfaceflag:
                    model.idx_hru = k
                    model.pegasustempssurface.find_x(
                        -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10)
                else:
                    model.idx_hru = k
                    model.calc_energybalancesurface_v1(aid.temps[k])
                    flu.wsurf[k] = 0
            else:
                flu.tempssurface[k] = modelutils.nan
                flu.saturationvapourpressuresnow[k] = 0.
                flu.actualvapourpressuresnow[k] = 0.
                flu.wsenssnow[k] = 0.
                flu.wlatsnow[k] = 0.
                flu.wsurf[k] = 0.


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation.

    Basic equation (`Allen`_):
      :math:`NetRadiation = NetShortwaveRadiation-NetLongwaveRadiation`

    Example:

        The following calculation agrees with example 12 of `Allen`_:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> fluxes.netshortwaveradiation  = 11.1
        >>> fluxes.netlongwaveradiation  = 3.5
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(7.6)

    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetShortwaveRadiation,
        lland_fluxes.NetLongwaveRadiation,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NetRadiation,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.netradiation[k] = \
                flu.netshortwaveradiation[k] - flu.netlongwaveradiation[k]


class Calc_SchmPot_V1(modeltools.Method):
    """Calculate the potential snow melt according to the day degree method.
    This energy is available for melting of the snow layer

    Basic equation:
      :math:`W_{Melt) = (W_{GTF} + W_{Nied})/RSchmelz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> rschmelz(0.334)
        >>> fluxes.wgtf(2.0)
        >>> fluxes.wnied = 1.0, 2.0
        >>> model.calc_schmpot_v1()
        >>> fluxes.schmpot
        schmpot(8.982036, 11.976048)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WGTF,
        lland_fluxes.WNied,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SchmPot,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.schmpot[k] = max((flu.wgtf[k]+flu.wnied[k])/con.rschmelz, 0)


class Calc_WSnow_V1(modeltools.Method):
    """Calculate the energy balance of the snow layer according to the complete
    energy balance (Knauf, 2006).

    Basic equations:
      :math:`W_{snow} = - W_G + W_{nied} + NetShortwaveRadiation -
      NetLongwaveRadiation - W_{sens} - W_{Lat}`

      Example:

          >>> from hydpy.models.lland import *
          >>> parameterstep('1d')
          >>> nhru(2)
          >>> fluxes.wg(4.0)
          >>> fluxes.wsurf(3.0)
          >>> states.waes = (0.0, 1.0)
          >>> model.calc_wsnow_v1()
          >>> fluxes.wsnow
          wsnow(0.0, 1.0)
          """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WSurf,
        lland_fluxes.WG,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WSnow,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                flu.wsnow[k] = flu.wg[k]-flu.wsurf[k]
            else:
                flu.wsnow[k] = 0.


class Update_ESnow_V2(modeltools.Method):
    """Calculate the heat content of the snow layer.

    Basic equation:
       :math`ESnow = ESnow_{t-1} + WSnow`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> states.waes = 0.0, 1.0, 10.0
        >>> states.esnow = 0.0, 0.0, 2.0
        >>> fluxes.wsnow = -1.0, -1.0, 1.0
        >>> model.update_esnow_v2()
        >>> states.esnow
        esnow(0.0, -1.0, 3.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WSnow,
        lland_states.WAeS,
    )
    UPDATEDSEQUENCES = (
        lland_states.ESnow,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                sta.esnow[k] += flu.wsnow[k]
            else:
                sta.esnow[k] = 0.


class Calc_SchmPot_V2(modeltools.Method):
    """Calculate the potential snow melt from the heat content of the snow layer.

    Basic equations:
      :math:`SchmPot = ESnow/RSchmelz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> rschmelz(0.334)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.esnow = nan, 5.0, 2.0, -2.0
        >>> model.calc_schmpot_v2()
        >>> fluxes.schmpot
        schmpot(0.0, 14.97006, 5.988024, 0.0)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_states.ESnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SchmPot,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                flu.schmpot[k] = max(sta.esnow[k]/con.rschmelz, 0)
            else:
                flu.schmpot[k] = 0.
            # ToDo: Eingabe Knauf-Parameter
            # ToDo: Schmelzrate durch Bodenwärme


class Calc_GefrPot_V1(modeltools.Method):
    """Calculate the potential refreezing from the energy balance.

    Basic equations:
      :math:`GefrPot = -WMelt/RSchmelz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> rschmelz(0.334)
        >>> states.waes = 0.0, 1.0, 1.0, 1.0
        >>> states.esnow = nan, -5.0, -2.0, 2.0
        >>> model.calc_gefrpot_v1()
        >>> fluxes.gefrpot
        gefrpot(0.0, 14.97006, 5.988024, 0.0)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_states.ESnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.GefrPot,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k]>0:
                flu.gefrpot[k] = max(-sta.esnow[k]/con.rschmelz, 0)
            else:
                flu.gefrpot[k] = 0.


class Calc_Schm_WATS_V1(modeltools.Method):
    """Calculate the actual amount of water melting within the snow layer.

    Basic equations:
      :math:`Schm = \\Bigl \\lbrace
      {
      {SchmPot \\ | \\ WATS > 0}
      \\atop
      {0 \\ | \\ WATS = 0}
      }`

    Examples:

        Initialise two water (|FLUSS| and |SEE|) and four arable land
        (|ACKER|) HRUs.  Assume the same values for the initial amount
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
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
        lland_fluxes.SchmPot,
        lland_states.WATS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.Schm,
    )
    UPDATEDSEQUENCES = (
        lland_states.WATS,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            flu.schm[k] = min(flu.schmpot[k], sta.wats[k])
            sta.wats[k] -= flu.schm[k]


class Calc_Gefr_WATS_V1(modeltools.Method):
    """Calculate the actual amount of water melting within the snow layer.

    Basic equations:
      :math:`Gefr = \\Bigl \\lbrace
      {
      {GefrPot \\ | \\ WAeS - WATS > 0}
      \\atop
      {0 \\ | \\ WATS = 0}
      }`

    Examples:

        Initialise two water (|FLUSS| and |SEE|) and four arable land
        (|ACKER|) HRUs.  Assume the same values for the initial amount
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
        lland_fluxes.SBes,
        lland_fluxes.GefrPot,
        lland_states.WAeS,
        lland_states.WATS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.Gefr,
    )
    UPDATEDSEQUENCES = (
        lland_states.WATS,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.refreezeflag:
                flu.gefr[k] = min(flu.gefrpot[k], (sta.waes[k]-sta.wats[k]))
                sta.wats[k] += flu.gefr[k]
            else:
                flu.gefr[k] = 0.


class Update_WaDa_WAeS_V1(modeltools.Method):
    """Update the actual water release from the snow cover, after melting
    of snow.

    Basic equations:
      :math:`WaDaCorr = Max(WAeS-PWMax \\cdot WATS, 0)'

      :math:`WaDa += WaDaCorr`

      :math:`WAeS -= WaDaCorr`

    Examples:

        For simplicity, the threshold parameter |PWMax| is set to a value
        of two for each of the six initialized HRUs.  Thus, snow cover can
        hold as much liquid water as it contains frozen water, but the initial
        conditions of the snow cover are varied:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> pwmax(2.0)
        >>> states.wats = 0.0, 0.0, 0.0, 1.0, 1.0, 1.0
        >>> states.waes = 1.0, 1.0, 0.0, 1.0, 2.0, 3.0
        >>> fluxes.wada(1.0)
        >>> model.update_wada_waes_v1()
        >>> states.waes
        waes(1.0, 1.0, 0.0, 1.0, 2.0, 2.0)
        >>> fluxes.wada
        wada(1.0, 1.0, 1.0, 1.0, 1.0, 2.0)

        Note the special cases of the first two HRUs of type |FLUSS| and
        |SEE|.  For water areas, there is no snow cover and therefore
        no additional |WAeS| is generated.  For all other land
        use classes (of which only |ACKER| is selected), only the amount
        of |WAeS| exceeding the actual snow holding capacity is passed
        to |WaDa|.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (
        lland_states.WATS,
    )
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
                d_wada_corr = max(sta.waes[k]-con.pwmax[k]*sta.wats[k], 0.)
                flu.wada[k] += d_wada_corr
                sta.waes[k] -= d_wada_corr


class Update_ESnow_V3(modeltools.Method):
    """Update the energy content of the snow layer.

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
        >>> rschmelz(0.334)
        >>> fluxes.gefr = 0.0, 4.0, 0.0, 4.0
        >>> fluxes.schm = 0.0, 0.0, 4.0, 4.0
        >>> states.esnow = 1.0, -1.5, 1.336, 0.0
        >>> states.wats = 0.0, 5.0, 5.0, 10.0
        >>> model.update_esnow_v3()
        >>> states.esnow
        esnow(0.0, -0.164, 0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.Gefr,
        lland_fluxes.Schm,
        lland_states.WATS,
    )
    UPDATEDSEQUENCES = (
        lland_states.ESnow,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if sta.wats[k] > 0.:
                sta.esnow[k] -= flu.schm[k]*con.rschmelz
                sta.esnow[k] += flu.gefr[k]*con.rschmelz
            else:
                sta.esnow[k] = 0.


class Calc_SFF_V1(modeltools.Method):
    """Calculate proportion of frozen water relative to total water (soil layer
    2z)

    Basic equations:
      :math:`SFF = Max(1 - \\frac{EBdn}{BoWa} \\cdot R_{Schmelz}
      \\cdot \\varrho_W, 0)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> rschmelz(0.322)
        >>> bowa2z(80.0)
        >>> states.ebdn(30.0, -1.0, 5.0)
        >>> model.calc_sff_v1()
        >>> fluxes.sff
        sff(0.0, 1.0, 0.805901)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.RSchmelz,
        lland_control.BoWa2Z,
    )
    REQUIREDSEQUENCES = (
        lland_states.EBdn,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SFF,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.ebdn[k] < 0:
                flu.sff[k] = 1
            else:
                flu.sff[k] = max(1-sta.ebdn[k]/(con.bowa2z[k]*con.rschmelz), 0)


class Calc_FVG_V1(modeltools.Method):
    """Calculate the degree of frost sealing.

    Basic equation:
      :math:`FVG = Min(1.0, fvf \\cdot SFF^{b_{sff}})`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fvf(0.8)
        >>> bsff(2.0)
        >>> fluxes.sff(0.5, 0.8, 1.0)
        >>> model.calc_fvg_v1()
        >>> fluxes.fvg
        fvg(0.2, 0.512, 0.8)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.BSFF,
        lland_control.FVF,
    )
    RESULTSEQUENCES = (
        lland_fluxes.FVG,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.fvg[k] = con.fvf*flu.sff[k]**con.bsff


class Calc_EvB_V1(modeltools.Method):
    """Calculate the actual soil lland evaporation.

    Basic equations:
      :math:`temp = exp(-GrasRef_R \\cdot \\frac{BoWa}{WMax})`

      :math:`EvB = (EvPo - EvI) \\cdot
      \\frac{1 - temp}{1 + temp -2 \\cdot exp(-GrasRef_R)}`

    Examples:

        Soil llandevaporation is calculated neither for water nor for sealed
        areas (see the first three HRUs of type |FLUSS|, |SEE|, and |VERS|).
        Instead it is set to the evaporation over water surfaces.
        All other land use classes are handled in accordance with a
        recommendation of the set of codes described in ATV-DVWK-M 504
        (arable land |ACKER| has been selected for the last four HRUs
        arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> grasref_r(5.0)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0)
        >>> fluxes.evpo = 5.0
        >>> fluxes.evpowater = 5.0
        >>> fluxes.evi = 3.0
        >>> states.bowa = 50.0, 50.0, 50.0, 0.0, 0.0, 50.0, 100.0
        >>> model.calc_evb_v1()
        >>> fluxes.evb
        evb(5.0, 5.0, 5.0, 0.0, 0.0, 1.717962, 2.0)

        In case maximum soil water storage (|WMax|) is zero, soil evaporation
        (|EvB|) is generally set to zero (see the forth HRU).  The last
        three HRUs demonstrate the rise in soil evaporation with increasing
        soil moisture, which is lessening in the high soil moisture range.
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
    RESULTSEQUENCES = (
        lland_fluxes.EvB,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.evb[k] = flu.evpo[k]
            elif con.wmax[k] <= 0.:
                flu.evb[k] = 0.
            else:
                d_temp = modelutils.exp(-con.grasref_r *
                                        sta.bowa[k] / con.wmax[k])
                flu.evb[k] = (
                    (flu.evpo[k] - flu.evi[k]) * (1. - d_temp) /
                    (1. + d_temp - 2. * modelutils.exp(-con.grasref_r))
                )


class Calc_DryAirPressure_V1(modeltools.Method):
    """Calculate pressure of dry air.

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

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )

    REQUIREDSEQUENCES = (
        lland_fluxes.ActualVapourPressure,
        lland_inputs.AtmosphericPressure,
    )

    RESULTSEQUENCES = (
        lland_fluxes.DryAirPressure,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dryairpressure[k] = \
                inp.atmosphericpressure - flu.actualvapourpressure[k]


class Calc_DensityAir_V1(modeltools.Method):
    """Calculate the density of the air.

    Basic equation:
       :math:`DensityAir = \\frac{pd}{Rd \\cdot T}
       + \\frac{ActualVapourPressure}{Rv \\cdot T}`

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )

    REQUIREDSEQUENCES = (
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.DryAirPressure,
        lland_fluxes.TKor,
    )

    RESULTSEQUENCES = (
        lland_fluxes.DensityAir,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.densityair[k] = (
                (flu.dryairpressure[k]/(0.287058*(flu.tkor[k]+273.15))) +
                (flu.actualvapourpressure[k]/(0.461495*(flu.tkor[k]+273.15))))
        # TODO Konstanten: specific gas constant for water vapour and for
        #  dry air


class Calc_AerodynamicResistance_V1(modeltools.Method):
    """Calculate aerodynamic resistance. It describes the resistance created
    by wind.

    Basic equations:
        z0 nach Quast und Boehm, 1997
       :math:`z0 = 0.021 + 0.163 \\cdot cropheight`
       :math:`AerodynamicResistance = \\biggl \\lbrace
       {
       \\frac{6,25}{u_{m,10}}(ln(\\frac{10}{z_{0}}))^{2} z_{0}<1\\,m
       \\atop
       \\frac{94}{u_{m,10}} z_{0}\\geqq1\\,m
       }`

    Example:

        Vegetation reduces the wind velocity ander therefore the
        aerodynamic resistance decreases with crop height.

        >>> from hydpy import pub
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, WASSER, LAUBW, NADELW)
        >>> pub.timegrids = '2019-06-16', '2019-06-17', '1d'
        >>> derived.moy.update()
        >>> cropheight.wasser_jun = 0.05
        >>> cropheight.acker_jun = 0.6
        >>> cropheight.laubw_jun = 9.0
        >>> cropheight.nadelw_jun = 11.0
        >>> cropheight.wasser_jan = 0.05
        >>> cropheight.acker_jan = 0.05
        >>> cropheight.laubw_jan = 2.0
        >>> cropheight.nadelw_jan = 11.0
        >>> fluxes.windspeed10m = 3.0
        >>> model.calc_aerodynamicresistance_v1()
        >>> fluxes.aerodynamicresistance
        aerodynamicresistance(40.938736, 71.001889, 7.561677, 31.333333)

        Cropheight changes within the season, this has an influence on
        aerodynamic resistance:

        >>> pub.timegrids = '2019-01-16', '2019-01-17', '1d'
        >>> derived.moy.update()
        >>> model.calc_aerodynamicresistance_v1()
        >>> fluxes.aerodynamicresistance
        aerodynamicresistance(71.001889, 71.001889, 23.53422, 31.333333)

        With increasing wind speed the aerodynamic resistance decreases.
        For effective cropheights < 10m cropheight has no influence:

        >>> fluxes.windspeed10m = 12.0
        >>> model.calc_aerodynamicresistance_v1()
        >>> fluxes.aerodynamicresistance
        aerodynamicresistance(17.750472, 17.750472, 5.883555, 7.833333)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        lland_control.CropHeight,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )

    REQUIREDSEQUENCES = (
        lland_fluxes.WindSpeed10m,
    )

    RESULTSEQUENCES = (
        lland_fluxes.AerodynamicResistance,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nhru):
            d_z0 = \
	            0.021+0.163*con.cropheight[con.lnk[k]-1, der.moy[model.idx_sim]]
            if con.cropheight[con.lnk[k]-1, der.moy[model.idx_sim]]< 10:
                flu.aerodynamicresistance[k] = \
                    6.25/flu.windspeed10m*(modelutils.log(10/d_z0))**2
            else:
                flu.aerodynamicresistance[k] = 94/flu.windspeed10m
            # ToDo: unstetige Funktion.
            # -> unrealistisch


class Calc_SurfaceResistanceBare_V1(modeltools.Method):
    """Calculate surface resistance of bare soil.

    Basic equation:
       :math:`SurfaceResistanceBare = \\biggl \\lbrace
       {
       100 \\|\\ NFk > 20
       \\atop
       100 \\cdot \\frac{WMax - PWP}{(BoWa - PWP) + 0.01 \\cdot (Wmax - PWP)}
       \\|\\ NFk \\geq 20
       }`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER)
        >>> fk(10.0, 20.0, 30.0, 30.0, 40.0, 40.0)
        >>> pwp(10.0)
        >>> derived.nfk.update()
        >>> derived.nfk
        nfk(0.0, 10.0, 20.0, 20.0, 30.0, 30.0)
        >>> states.bowa = 5.0, 10.0, 20.0, 30.0, 40.0, 50.0
        >>> model.calc_surfaceresistancebare_v1()
        >>> fluxes.surfaceresistancebare
        surfaceresistancebare(10000.0, 10000.0, 196.078431, 99.009901, 100.0,
                              100.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.PWP,
        lland_control.FK,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.NFk,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SurfaceResistanceBare,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if der.nfk[k] > 20.:
                flu.surfaceresistancebare[k] = 100.
            elif der.nfk[k] == 0.:
                flu.surfaceresistancebare[k] = 10000.
            else:
                d_free = max(min((sta.bowa[k]-con.pwp[k]), con.fk[k]), 0.)
                flu.surfaceresistancebare[k] = (
                        100.*der.nfk[k]/(d_free+.01*der.nfk[k]))


class Calc_SurfaceResistanceLandUse_V1(modeltools.Method):
    """Calculate land use specific surface resistance.

    Example:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER, WASSER, NADELW, NADELW, NADELW, VERS)
        >>> surfaceresistance.acker_mai = 40.0
        >>> surfaceresistance.nadelw_mai = 80.0
        >>> surfaceresistance.wasser_mai = 0.0
        >>> fluxes.tkor(10.0, 10.0, -3.0, 25.0, -10.0, 5.0)
        >>> fluxes.saturationvapourpressure(1.227963, 1.227963, 1.227963,
        ... 1.227963, 2.5, 1.227963)
        >>> fluxes.actualvapourpressure(0.736778, 0.736778, 0.736778, 0.736778,
        ... 0.4,  0.736778)
        >>> fluxes.surfaceresistancebare(100.0)
        >>> pub.timegrids = '2019-05-16', '2019-05-17', '1d'
        >>> derived.moy.update()
        >>> model.calc_surfaceresistancelanduse_v1()
        >>> fluxes.surfaceresistancelanduse
        surfaceresistancelanduse(40.0, 0.0, 1159.850611, 106.043484, 10000.0,
                                 100.0)

        >>> pub.timegrids = '2019-01-16', '2019-01-17', '1d'
        >>> derived.moy.update()
        >>> surfaceresistance.acker_jan = 10.0
        >>> surfaceresistance.nadelw_jan = 60.0
        >>> surfaceresistance.wasser_jan = 0.0
        >>> model.calc_surfaceresistancelanduse_v1()
        >>> fluxes.surfaceresistancelanduse
        surfaceresistancelanduse(10.0, 0.0, 1159.850611, 79.532613, 10000.0,
                                 100.0)

        .. testsetup::

            >>> del pub.timegrids
    """
    CONTROLPARAMETERS = (
        lland_control.Lnk,
        lland_control.SurfaceResistance,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.SurfaceResistanceBare,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SurfaceResistanceLandUse,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] == NADELW:
                # calculate surface resistance correction for air temperature
                if flu.tkor[k] < -5:
                    d_surfaceresistancecorrt = 10000.
                elif -5. < flu.tkor[k] < 20.:
                    d_surfaceresistancecorrt = (25 * 70) / (flu.tkor[k] + 5)
                else:
                    d_surfaceresistancecorrt = \
                        con.surfaceresistance[con.lnk[k] - 1, der.moy[
                            model.idx_sim]]
                # calculate surface resistance correction for saturation deficit
                if (flu.saturationvapourpressure[k] -
                        flu.actualvapourpressure[k] < 2):
                    d_de = (flu.saturationvapourpressure[k] -
                            flu.actualvapourpressure[k])
                    flu.surfaceresistancelanduse[k] = \
                        d_surfaceresistancecorrt / (1 - 0.5 * d_de)
                else:
                    flu.surfaceresistancelanduse[k] = 10000.
            elif con.lnk[k] == VERS:
                flu.surfaceresistancelanduse[k] = flu.surfaceresistancebare[k]
            else:
                flu.surfaceresistancelanduse[k] = \
                    con.surfaceresistance[con.lnk[k] - 1, der.moy[
                        model.idx_sim]]


class Calc_SurfaceResistanceMoist_V1(modeltools.Method):
    """Calculate soil moisture dependent surface resistance.

    Basic equation:
       :math:`SurfaceresistanceMoist = \\biggl \\lbrace
       {
       SurfaceResistanceLanduse \\cdot (3.5 + exp(0.2)) \\|\\ BoWa > PWP
       \\atop
       SurfaceResistanceLanduse \\cdot (3.5 \\cdot (1 - BoWa / PWP) +
       exp(0.2 \\cdot \\frac{PWP}{BoWa})) \\|\\ BoWa \\leq PWP
       }`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(7)
        >>> pwp(30.0)
        >>> lnk(WASSER, WASSER, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> states.bowa = 0.0, 20.0, 0.0, 15.0, 30.0, 45.0, 150.0
        >>> fluxes.surfaceresistancelanduse = (0.0, 0.0, 40.0, 40.0, 40.0, 40.0,
        ...     40.0)
        >>> model.calc_surfaceresistancemoist_v1()
        >>> fluxes.surfaceresistancemoist
        surfaceresistancemoist(0.0, 0.0, inf, 129.672988, 48.85611, 48.85611,
                               48.85611)
        >>> control.pwp(0.0)
        >>> model.calc_surfaceresistancemoist_v1()
        >>> fluxes.surfaceresistancemoist
        surfaceresistancemoist(0.0, 0.0, inf, 48.85611, 48.85611, 48.85611,
                               48.85611)
    """
    CONTROLPARAMETERS = (
        lland_control.PWP,
        lland_control.NHRU,
        lland_control.Lnk,
    )

    REQUIREDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.SurfaceResistanceLandUse,
    )

    RESULTSEQUENCES = (
        lland_fluxes.SurfaceResistanceMoist,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                # todo: Nan-Werte für Wasserflächen sinnvoller?
                flu.surfaceresistancemoist[k] = flu.surfaceresistancelanduse[k]
            elif (sta.bowa[k] == 0.) and (flu.surfaceresistancelanduse[k] != 0):
                flu.surfaceresistancemoist[k] = modelutils.inf
            elif sta.bowa[k] > con.pwp[k]:
                flu.surfaceresistancemoist[k] = \
                    flu.surfaceresistancelanduse[k]*(modelutils.exp(.2))
            else:
                flu.surfaceresistancemoist[k] = (
                    flu.surfaceresistancelanduse[k] *
                    (3.5*(1.-sta.bowa[k]/con.pwp[k]) +
                     modelutils.exp(.2*con.pwp[k]/sta.bowa[k]))
                )

        # TODO: frei verfügbares Bodenwasser entspricht WMax - PWP?
        # TODO: entspricht Schwellenwert pflanzengebundenes Wasser Py - PWP?
        # TODO: PWP bei erweiterten Bodenparametern eigentlich nicht vorhanden


class Calc_SurfaceResistanceCorr_V1(modeltools.Method):
    """Calculate corrected surface resistance.

    Basic equations:
      ResDay:
      :math:`\\frac {1}{\\frac{1-0.7^{LAI}}{flu.surfaceresistancemoist[k]} +
      \\frac{0.7^{LAI}}{SurfaceResistanceBare}}`

      ResNight:
      :math:`\\frac{1}{\\frac{LAI}{2500} + \\frac{1}{SurfacResistanceMoist}}`

      :math:`SurfaceresistanceCorr = \\frac{1}{\\frac{PossibleSunshineDuration}
      {hours} \\cdot \frac{1}{ResDay + (1-\\frac{PossibleSunshineDuration}
      {hours} \\cdot \\frac{1}{ResNight})}`

    Example:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(ACKER, WASSER, NADELW, NADELW, NADELW)
        >>> lai.nadelw = 5.0
        >>> lai.wasser = 0.0
        >>> lai.acker = 1.0
        >>> fluxes.surfaceresistancebare(100.0)
        >>> fluxes.surfaceresistancemoist(188.85611, 0.0, 5476.121874,
        ... 500.673998, 47214.027582)
        >>> pub.timegrids = '2019-05-16', '2019-05-17', '1d'
        >>> derived.moy.update()
        >>> derived.seconds.update()
        >>> fluxes.possiblesunshineduration(11.02503)
        >>> model.calc_surfaceresistancecorr_v1()
        >>> fluxes.surfaceresistancecorr
        surfaceresistancecorr(142.36436, 0.0, 494.600634, 270.531886, \
533.941016)

        .. testsetup::

            >>> del pub.timegrids
    """
    CONTROLPARAMETERS = (
        lland_control.LAI,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SurfaceResistanceBare,
        lland_fluxes.SurfaceResistanceMoist,
        lland_fluxes.PossibleSunshineDuration,
    )

    RESULTSEQUENCES = (
        lland_fluxes.SurfaceResistanceCorr,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_hours = der.seconds / 60. / 60.
        for k in range(con.nhru):
            if flu.surfaceresistancemoist[k] == 0.:
                flu.surfaceresistancecorr[k] = 0.
            else:
                d_surfaceresistanceday = (
                    1 /
                    (((1-0.7**con.lai[con.lnk[k]-1,
                                      der.moy[model.idx_sim]]) /
                      flu.surfaceresistancemoist[k]) +
                     0.7**con.lai[con.lnk[k]-1, der.moy[model.idx_sim]] /
                     flu.surfaceresistancebare[k])
                )
                d_surfaceresistancenight = (
                    1 /
                    (con.lai[con.lnk[k]-1, der.moy[model.idx_sim]]/2500 +
                     1/flu.surfaceresistancemoist[k]))

                flu.surfaceresistancecorr[k] = (
                    1 /
                    ((flu.possiblesunshineduration/d_hours) *
                     1/d_surfaceresistanceday +
                     (1-flu.possiblesunshineduration/d_hours) *
                     1/d_surfaceresistancenight))


class Calc_PM_Single_V1(modeltools.Method):
    """Calculate llandevapootranspiration according to Penman-Monteith

    Basic equations:
    :math:`EvPo = \\frac
    {\\Delta \\cdot (NetRadiation + WG) + \\varrho c_{p}
    (SaturationVapourPressure - ActualVapourPressure) / AerodynamicResistance
    \\cdot C}{\\Delta + \\gamma (1 + SurfaceResistnaceCorr /
    AerodynamicResistance) \\cdot C} \\cdot \frac{1}{\\varrho_{w} \\cdot
    \\lambda}`

    :math:`C = 1 + 4 \\cdot Emissivity \\cdot Sigma \\cdot (273.15 + TKor)^3`

    Example:

    The following example shows how the function |Calc_PM_Single_V1| is used
    by the function |Calc_EvB_V1|. In this case |Calc_PM_Single_V1| is used
    to calculate the evapotranspiration according to Penman-Monteith over
    land surfaces without snow.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER, ACKER, ACKER, LAUBW, LAUBW, LAUBW)
        >>> fluxes.tkor(0.0, 1.0, 10.0, 0.0, 1.0, 10.0)
        >>> states.waes = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> emissivity(0.95)
        >>> derived.seconds = 24*60*60

        .. testsetup::

            >>> inputs.relativehumidity(75.0)
            >>> inputs.atmosphericpressure(101.3)
            >>> derived.moy = 0
            >>> cropheight.wasser_jan = 0.05
            >>> cropheight.acker_jan = 0.05
            >>> cropheight.laubw_jan = 2.0
            >>> fluxes.windspeed10m(3.0)
            >>> control.pwp(30.0)
            >>> control.wmax(210.0)
            >>> states.bowa(150.0)
            >>> surfaceresistance.acker_jan = 40.0
            >>> surfaceresistance.wasser_jan = 0.0
            >>> surfaceresistance.laubw_jan = 80.0

        >>> fluxes.saturationvapourpressure(0.6, 0.7, 1.2, 0.6, 0.7, 1.2)
        >>> fluxes.saturationvapourpressureslope(
        ...     0.04, 0.05, 0.08, 0.04, 0.05, 0.08)
        >>> fluxes.actualvapourpressure(
        ...     0.46, 0.49, 0.92, 0.46, 0.49, 0.92)
        >>> fluxes.psychrometricconstant(0.07)
        >>> fluxes.densityair(
        ...     1.29, 1.29, 1.24, 1.29, 1.29, 1.24)
        >>> fluxes.aerodynamicresistance(
        ...     120.4, 120.4, 120.4, 31.9, 31.9, 31.9)
        >>> fluxes.surfaceresistancecorr(
        ...     64.9, 64.9, 64.9, 109.4, 109.4, 109.4)
        >>> fluxes.densityair(
        ...     1.29, 1.28, 1.24, 1.29, 1.28, 1.24)

        >>> fluxes.wg(0.04, 0.02, 0.01, 0.04, 0.02, 0.01)
        >>> fluxes.netradiation(1.0, 2.0, 3.0, 1.0, 2.0, 3.0)
        >>> fluxes.evi(0.25, 0.46, 0.5, 0.25, 0.46, 0.5)
        >>> fluxes.evpo(0.45, 0.76, 1.10, 0.45, 0.76, 1.10)

        >>> model.calc_evb_v2()
        >>> fluxes.evb
        evb(0.211625, 0.296876, 0.565181, 0.275607, 0.370984, 0.672898)

        hourly timestep:

        >>> derived.seconds = 60*60
        >>> fluxes.wg(0.0017, 0.0008, 0.0004, 0.0017, 0.0008, 0.0004)
        >>> fluxes.netradiation(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
        >>> fluxes.evi(0.025, 0.046, 0.05, 0.025, 0.046, 0.05)
        >>> fluxes.evpo(0.045, 0.076, 0.11, 0.045, 0.076, 0.110)

        >>> model.calc_evb_v2()
        >>> fluxes.evb
        evb(0.011014, 0.016982, 0.036529, 0.018222, 0.02392, 0.047643)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Emissivity,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.DensityAir,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.SurfaceResistanceCorr,
        lland_fluxes.WG,
        lland_fluxes.NetRadiation,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, k: int, surfaceresistance: float) \
            -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        # TODO Konstante: Stefan-Boltzmann-Konstante
        # TODO Konstante: spezifische Wärmekonstante Luft(0.001005MJ/kg),
        #  Latente Verdunstungswärme (2.465 MJ/kg)
        # C: Korrekturfaktor für Abweichungen von gemessener Temperatur und
        # Oberflächentemperatur
        d_c = (
            1.+((4.*con.emissivity*5.67e-8*(273.15 + flu.tkor[k])**3) *
                flu.aerodynamicresistance[k])/(flu.densityair[k]*1005.))
        return (
            (flu.saturationvapourpressureslope[k] *
             (flu.netradiation[k]+flu.wg[k])+flu.densityair[k] *
             0.001005 *
             (flu.saturationvapourpressure[k] -
              flu.actualvapourpressure[k]) *
             d_c*der.seconds/(flu.aerodynamicresistance[k])) /
            (flu.saturationvapourpressureslope[k] +
             flu.psychrometricconstant *
             (1.+surfaceresistance /
              flu.aerodynamicresistance[k])*d_c)/2.465000)


class Calc_Penman_V1(modeltools.Method):
    """Calculates the evapotranspiration from water surfaces according to
    Penman

    Basic equations:
      :math:`f(v) = 0.13 + 0.94 \\cdot WindSpeed2m`

      :math:`EvPoWater = \\frac{\\Delta \\frac{NetRadiation}{L}+\\gamma
      \\cdot f(v) \\cdot (SaturationVapourPressure-ActualVapourPressure)}
      {\\Delta + \\gamma}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        
        Test in Tagesschrittweite:
        
        >>> derived.seconds = 24*60*60
        >>> fluxes.saturationvapourpressure(1.227963)
        >>> fluxes.saturationvapourpressureslope(0.082283)
        >>> fluxes.actualvapourpressure(0.736778)
        >>> fluxes.netradiation(7.296675, 10.0)
        >>> fluxes.psychrometricconstant(0.067364)
        >>> fluxes.windspeed2m(2.243258)
        >>> model.calc_evpo_v3()
        >>> fluxes.evpo
        evpo(2.383011, 2.986657)
        
        Test in Stundenschrittweite:
        >>> derived.seconds = 60*60
        >>> fluxes.netradiation(0.2, 0.4)
        >>> model.calc_evpo_v3()
        >>> fluxes.evpo
        evpo(0.076063, 0.120722)
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.NetRadiation,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.WindSpeed2m,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model, evpo: Vector) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            evpo[k] = (
                (flu.saturationvapourpressureslope[k] *
                 flu.netradiation[k]*1e6/der.seconds/28.5 +
                 flu.psychrometricconstant *
                 (0.13+0.094*flu.windspeed2m) *
                 10 *
                 (flu.saturationvapourpressure[k] -
                  flu.actualvapourpressure[k])) /
                (flu.saturationvapourpressureslope[k] +
                 flu.psychrometricconstant)) / (24*60*60)*der.seconds
        # ToDo: f(v) in extra Methode?


class Calc_EvPo_V2(modeltools.Method):
    # todo: Für Wasserflächen wurde die Formel in LARSIM angepasst. Aber wie?
    """Calculate evpotranspiration according to Penman-Monteith

    For further documentation see |Calc_PM_Single_V1|

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(9)
        >>> lnk(ACKER, ACKER, ACKER, LAUBW, LAUBW, LAUBW, WASSER, WASSER,
        ... WASSER)
        >>> fluxes.tkor(0.0, 1.0, 10.0, 0.0, 1.0, 10.0, 0.0, 1.0, 10.0)
        >>> emissivity(0.95)
        >>> derived.seconds = 24*60*60

        >>> fluxes.saturationvapourpressure(
        ...     0.6, 0.7, 1.2, 0.6, 0.7, 1.2, 0.6, 0.7, 1.2)
        >>> fluxes.saturationvapourpressureslope(
        ...     0.04, 0.05, 0.08, 0.04, 0.05, 0.08, 0.04, 0.05, 0.08)
        >>> fluxes.actualvapourpressure(
        ...     0.46, 0.49, 0.92, 0.46, 0.49, 0.92, 0.46, 0.49, 0.92)
        >>> fluxes.psychrometricconstant(0.07)
        >>> fluxes.densityair(
        ...     1.29, 1.29, 1.24, 1.29, 1.29, 1.24, 1.29, 1.29, 1.24)
        >>> fluxes.aerodynamicresistance(
        ...     120.4, 120.4, 120.4, 31.9, 31.9, 31.9, 120.4, 120.4, 120.4)
        >>> fluxes.surfaceresistancecorr(
        ...     64.9, 64.9, 64.9, 109.4, 109.4, 109.4, 0.0, 0.0, 0.0)
        >>> fluxes.densityair(
        ...     1.29, 1.28, 1.24, 1.29, 1.28, 1.24, 1.29, 1.28, 1.24)

        >>> fluxes.wg(0.04, 0.02, 0.01, 0.04, 0.02, 0.01, 0.04, 0.02, 0.01)
        >>> fluxes.netradiation(1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0)
        >>> model.calc_evpo_v2()
        >>> fluxes.evpo
        evpo(0.658719, 1.021527, 1.350634, 2.023197, 2.901006, 3.332555,
             0.658719, 1.021527, 1.350634)
    """
    CONTROLPARAMETERS = (
        lland_control.Emissivity,
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.WG,
        lland_fluxes.DensityAir,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.TKor,
        lland_fluxes.PsychrometricConstant,
    )
    # todo: Muss angepasst werden (cropheight=0)??
    RESULTSEQUENCES = (
        lland_fluxes.EvPo,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.evpo[k] = model.calc_pm_single_v1(k, 0.)


class Calc_EvPo_V3(modeltools.Method):
    """Calculate evpotranspiration according to Penman.

    For further documentation see |Calc_Penman_V1|.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> derived.seconds = 24*60*60
        >>> fluxes.saturationvapourpressure(1.227963)
        >>> fluxes.saturationvapourpressureslope(0.082283)
        >>> fluxes.actualvapourpressure(0.736778)
        >>> fluxes.netradiation(7.296675, 10.0)
        >>> fluxes.psychrometricconstant(0.067364)
        >>> fluxes.windspeed2m(2.243258)
        >>> model.calc_evpo_v3()
        >>> fluxes.evpo
        evpo(2.383011, 2.986657)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.NetRadiation,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.WindSpeed2m,
        lland_fluxes.ActualVapourPressure,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvPo,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        model.calc_penman_v1(flu.evpo)


class Calc_EvPoWater_V1(modeltools.Method):
    """Calculates the evapotranspiration from water surfaces according to
    Penman

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> derived.seconds = 24*60*60
        >>> fluxes.saturationvapourpressure(1.227963)
        >>> fluxes.saturationvapourpressureslope(0.082283)
        >>> fluxes.actualvapourpressure(0.736778)
        >>> fluxes.netradiation(7.296675)
        >>> fluxes.psychrometricconstant(0.067364)
        >>> fluxes.windspeed2m(2.243258)
        >>> model.calc_evpowater_v1()
        >>> fluxes.evpowater
        evpowater(2.383011, 2.383011)
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.NetRadiation,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.WindSpeed2m,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvPoWater,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        model.calc_penman_v1(flu.evpowater)


class Calc_EvPoSnow_WAeS_WATS_V1(modeltools.Method):
    """Calculate evpotranspiration over snow covered surfaces according to
    latent heat calculated in snow module and update WAeS und WATS,
    due to evapotranspiration from the snow layer.

    Basic equations:
      :math:`EvPoSnow = - WLatSnow/WLatVap`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> fluxes.wlatsnow = 0.0, -2.0, 1.0, 4.0, 6.0
        >>> states.waes = 0.0, 5.0, 5.0, 5.0, 5.0
        >>> states.wats = 0.0, 4.0, 4.0, 4.0, 4.0
        >>> model.calc_evposnow_waes_wats_v1()
        >>> fluxes.evposnow
        evposnow(0.0, -0.8, 0.4, 1.6, 2.4)
        >>> states.waes
        waes(0.0, 5.8, 4.6, 3.4, 2.6)
        >>> states.wats
        wats(0.0, 4.0, 4.0, 3.4, 2.6)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WLatSnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvPoSnow,
    )
    UPDATEDSEQUENCES = (
        lland_states.WAeS,
        lland_states.WATS,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        for k in range(con.nhru):
            if sta.waes[k] > 0:
                flu.evposnow[k] = flu.wlatsnow[k] / 2.5
                sta.waes[k] -= flu.evposnow[k]
                sta.waes[k] = max(sta.waes[k], 0)
                sta.wats[k] = min(sta.waes[k], sta.wats[k])
            else:
                flu.evposnow[k] = 0.
        # todo: Konstante latent heat of vaporization 2.5


class Calc_EvI_Inzp_V1(modeltools.Method):
    """Calculate interception lland evaporation and update the interception
    storage accordingly.

    Basic equation:
      :math:`EvI = \\Bigl \\lbrace
      {
      {EvPo \\ | \\ Inzp > 0}
      \\atop
      {0 \\ | \\ Inzp = 0}
      }`

    Examples:

        Initialize five HRUs with different combinations of land usage
        and initial interception storage and apply a value of potential
        evaporation of 3 mm on each one:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> states.inzp = 2.0, 2.0, 0.0, 2.0, 4.0
        >>> fluxes.evpowater = 3.0
        >>> model.calc_evi_inzp_v1()
        >>> states.inzp
        inzp(0.0, 0.0, 0.0, 0.0, 1.0)
        >>> fluxes.evi
        evi(0.0, 0.0, 0.0, 2.0, 3.0)

        For arable land (|ACKER|) and most other land types, interception
        evaporation (|EvI|) is identical with potential evapotranspiration
        (|EvPo|), as long as it is met by available intercepted water
        ([Inzp|).  Only water areas (|FLUSS| and |SEE|),  |EvI| is
        generally equal to |EvPo| (but this might be corrected by a method
        called after |Calc_EvI_Inzp_V1| has been applied) and [Inzp| is
        set to zero.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.EvPoWater,
    )
    UPDATEDSEQUENCES = (
        lland_states.Inzp,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvI,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.evi[k] = 0.
                sta.inzp[k] = 0.
            else:
                flu.evi[k] = min(flu.evpowater[k], sta.inzp[k])
                sta.inzp[k] -= flu.evi[k]
        # todo: Verdunstung aus Interzeptionsspeicher bei Schnee?


class Calc_EvB_V2(modeltools.Method):  # todo für Interzeptionsspeicher
    """
    Calculate the actual evapotranspiration from soil.

    For further documentation see |Calc_PM_single_V1|

    Example:

       >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(9)
        >>> lnk(ACKER, ACKER, ACKER, LAUBW, LAUBW, LAUBW, WASSER, WASSER,
        ... WASSER)
        >>> fluxes.tkor(0.0, 1.0, 10.0, 0.0, 1.0, 10.0, 0.0, 1.0, 10.0)
        >>> states.waes = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
        >>> emissivity(0.95)
        >>> derived.seconds = 24*60*60

        >>> fluxes.saturationvapourpressure(
        ...     0.6, 0.7, 1.2, 0.6, 0.7, 1.2, 0.6, 0.7, 1.2)
        >>> fluxes.saturationvapourpressureslope(
        ...     0.04, 0.05, 0.08, 0.04, 0.05, 0.08, 0.04, 0.05, 0.08)
        >>> fluxes.actualvapourpressure(
        ...     0.46, 0.49, 0.92, 0.46, 0.49, 0.92, 0.46, 0.49, 0.92)
        >>> fluxes.psychrometricconstant(0.07)
        >>> fluxes.densityair(
        ...     1.29, 1.29, 1.24, 1.29, 1.29, 1.24, 1.29, 1.29, 1.24)
        >>> fluxes.aerodynamicresistance(
        ...     120.4, 120.4, 120.4, 31.9, 31.9, 31.9, 120.4, 120.4, 120.4)
        >>> fluxes.surfaceresistancecorr(
        ...     64.9, 64.9, 64.9, 109.4, 109.4, 109.4, 0.0, 0.0, 0.0)
        >>> fluxes.densityair(
        ...     1.29, 1.28, 1.24, 1.29, 1.28, 1.24, 1.29, 1.28, 1.24)

        >>> fluxes.wg(0.04, 0.02, 0.01, 0.04, 0.02, 0.01, 0.04, 0.02, 0.01)
        >>> fluxes.netradiation(1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0)
        >>> fluxes.evi(0.25, 0.46, 0.5, 0.25, 0.46, 0.5, 0.0, 0.0, 0.0)
        >>> fluxes.evpo(0.45, 0.76, 1.10, 0.45, 0.76, 1.10, 0.45, 0.76, 1.10)
        >>> fluxes.evpowater(
        ...     0.45, 0.76, 1.10, 0.45, 0.76, 1.10, 0.45, 0.76,1.10)

        >>> model.calc_evb_v2()
        >>> fluxes.evb
        evb(0.0, 0.296876, 0.565181, 0.0, 0.370984, 0.672898, 0.45, 0.76, 1.1)
    """
    CONTROLPARAMETERS = (
        lland_control.Emissivity,
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.WG,
        lland_fluxes.DensityAir,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.SurfaceResistanceCorr,
        lland_fluxes.TKor,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.EvPoWater,
        lland_fluxes.EvPo,
        lland_fluxes.EvPoWater,
        lland_fluxes.EvI,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvB,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.evb[k] = flu.evpowater[k]
            elif sta.waes[k] > 0.:
                flu.evb[k] = 0
            else:
                d_ev_boden = model.calc_pm_single_v1(
                    k, flu.surfaceresistancecorr[k])
                flu.evb[k] = (flu.evpo[k]-flu.evi[k])/flu.evpo[k]*d_ev_boden


class Calc_QKap_V1(modeltools.Method):
    """"Calculate the amount of capillary rise.

    Basic equation:
      :math:`Q_{kap} = \\Bigl \\lbrace
      {
      QMAX_{kap} \\|\\ BoWa<KapGrenz1
      \\atop
      QMAX_{kap}-\\frac{QMAX_{kap}(BoWa-KapGrenz1)}{KapGrenz2-KapGrenz1}
      \\|\\ KapGrenz1 \\leq BoWa<KapGrenz2
      \\atop
      0 \\|\\ KapGrenz2 \\leq BoWa
      }`

    Examples:

        To calculate the capillary rise |QKap|, we need to define the maximum
        capillary rise rate |KapMax| and threshold values |KapGrenz| for
        capillary rise or at least an option (e.g. option='KapAquantec') how
        |KapGrenz| should be parametrized.

        >>> from hydpy.models.lland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> wmax(160.)
        >>> states.bowa(5.,80.,140.)
        >>> kapmax(1.5)

        |FK| is needed to calculate |KapGrenz| for the options 'KapAquantec'
        and 'kapillarerAufstieg'

        >>> fk(80)

        with the option 'KapAquantec'

        >>> kapgrenz(option='KapAquantec')
        >>> kapgrenz
        kapgrenz([[40.0, 80.0],
                  [40.0, 80.0],
                  [40.0, 80.0]])
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(0.75, 0.0, 0.0)

        with the option 'BodenGrundwasser'

        >>> kapgrenz(option='BodenGrundwasser')
        >>> kapgrenz
        kapgrenz([[0.0, 16.0],
                  [0.0, 16.0],
                  [0.0, 16.0]])
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(0.515625, 0.0, 0.0)

        with the option 'kapillarerAufstieg'

        >>> kapgrenz(option='kapillarerAufstieg')
        >>> kapgrenz
        kapgrenz(80.0)
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(0.75, 0.75, 0.0)

        with predefined |KapGrenz| values
        >>> kapgrenz(20, 180)
        >>> kapgrenz
        kapgrenz([[20.0, 180.0],
                  [20.0, 180.0],
                  [20.0, 180.0]])
        >>> model.calc_qkap_v1()
        >>> fluxes.qkap
        qkap(0.75, 0.46875, 0.1875)


    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KapMax,
        lland_control.KapGrenz,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QKap,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE))
                    or (con.wmax[k] <= 0.)):
                flu.qkap[k] = 0.
            elif sta.bowa[k] <= con.kapgrenz[k, 0]:
                flu.qkap[k] = con.kapmax[k]
            elif ((sta.bowa[k] > con.kapgrenz[k, 0]) and
                  (sta.bowa[k] <= con.kapgrenz[k, 1])):
                flu.qkap[k] = (
                    con.kapmax[k] -
                    (sta.bowa[k] - con.kapgrenz[k, 0]) *
                    ((con.kapmax[k]) / (
                        con.kapgrenz[k, 1] - con.kapgrenz[k, 0])))
            elif sta.bowa[k] > con.kapgrenz[k, 1]:
                flu.qkap[k] = 0


class Calc_QBB_V1(modeltools.Method):
    """Calculate the amount of base flow released from the soil.

    Basic equations:
      :math:`Beta_{eff} = \\Bigl \\lbrace
      {
      {Beta \\ | \\ BoWa \\leq FK}
      \\atop
      {Beta \\cdot (1+(FBeta-1)\\cdot\\frac{BoWa-FK}{WMax-FK}) \\|\\ BoWa > FK}
      }`

      :math:`QBB = \\Bigl \\lbrace
      {
      {0 \\ | \\ BoWa \\leq PWP}
      \\atop
      {Beta_{eff}  \\cdot (BoWa - PWP) \\|\\ BoWa > PWP}
      }`

    Examples:

        For water and sealed areas, no base flow is calculated (see the
        first three HRUs of type |VERS|, |FLUSS|, and |SEE|).  No principal
        distinction is made between the remaining land use classes (arable
        land |ACKER| has been selected for the last five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> beta(0.04)
        >>> fbeta(2.0)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0, 200.0)
        >>> pwp(10.0)
        >>> fk(70.0)

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

        Note that for the last two HRUs the same amount of base flow
        generation is determined, in spite of the fact that both exhibit
        different relative soil moistures.

        In the second example, the actual soil water content |BoWa| is set
        to high values.  For values below threshold |FK|, the discussion above
        remains valid.  For values above |FK|, percolation shows a nonlinear
        behaviour when factor |FBeta| is set to values larger than one:

        >>> wmax(0.0, 0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 200.0)
        >>> states.bowa = 0.0, 0.0, 0.0, 60.0, 70.0, 80.0, 100.0, 200.0
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 1.0, 1.2, 1.866667, 3.6, 7.6)

        If we do not want to have capillary rise and  percolation at the same
        time we activate the flag |CorrQBBFlag|.
        >>> corrqbbflag(1)
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
        lland_control.KapGrenz,
        lland_control.PWP,
        lland_control.FK,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.QKap,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QBB,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.bowa[k] <= con.pwp[k]) or (con.wmax[k] <= 0.)):
                flu.qbb[k] = 0.
            elif sta.bowa[k] <= con.fk[k]:
                if con.corrqbbflag[k] == 1:
                    flu.qbb[k] = 0.
                else:
                    flu.qbb[k] = con.beta[k] * (sta.bowa[k] - con.pwp[k])
            else:
                flu.qbb[k] = (
                    (con.beta[k] * (sta.bowa[k] - con.pwp[k]) *
                     (1. + (con.fbeta[k] - 1.) *
                      ((sta.bowa[k] - con.fk[k]) / (con.wmax[k] - con.fk[k]))))
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
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QIB1,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.bowa[k] <= con.pwp[k])):
                flu.qib1[k] = 0.
            else:
                flu.qib1[k] = con.dmin[k] * (sta.bowa[k] / con.wmax[k])


class Calc_QIB2_V1(modeltools.Method):
    """Calculate the first inflow component released from the soil.

    Basic equation:
      :math:`QIB2 = (DMax-DMin) \\cdot
      (\\frac{BoWa-FK}{WMax-FK})^\\frac{3}{2}`

    Examples:

        For water and sealed areas, no interflow is calculated (the first
        three HRUs are of type |FLUSS|, |SEE|, and |VERS|, respectively).
        No principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last
        five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QIB1,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.bowa[k] <= con.fk[k]) or (con.wmax[k] <= con.fk[k])):
                flu.qib2[k] = 0.
            else:
                flu.qib2[k] = ((con.dmax[k] - con.dmin[k]) *
                               ((sta.bowa[k] - con.fk[k]) /
                                (con.wmax[k] - con.fk[k])) ** 1.5)


class Calc_QDB_V1(modeltools.Method):
    """Calculate direct runoff released from the soil.

    Basic equations:
      :math:`QDB = \\Bigl \\lbrace
      {
      {max(Exz, 0) \\ | \\ SfA \\leq 0}
      \\atop
      {max(Exz + WMax \\cdot SfA^{BSf+1}, 0) \\ | \\ SfA > 0}
      }`

      :math:`SFA = (1 - \\frac{BoWa}{WMax})^\\frac{1}{BSf+1} -
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
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
    RESULTSEQUENCES = (
        lland_fluxes.QDB,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.qdb[k] = 0.
            elif ((con.lnk[k] in (VERS, FLUSS, SEE)) or
                  (con.wmax[k] <= 0.)):
                flu.qdb[k] = flu.wada[k]
            else:
                if sta.bowa[k] < con.wmax[k]:
                    d_sfa = (
                        (1.-sta.bowa[k]/con.wmax[k])**(1./(con.bsf[k]+1.)) -
                        (flu.wada[k]/((con.bsf[k]+1.)*con.wmax[k])))
                else:
                    d_sfa = 0.
                d_exz = sta.bowa[k] + flu.wada[k] - con.wmax[k]
                flu.qdb[k] = d_exz
                if d_sfa > 0.:
                    flu.qdb[k] += d_sfa ** (con.bsf[k] + 1.) * con.wmax[k]
                flu.qdb[k] = max(flu.qdb[k], 0.)


class Update_QDB_V1(modeltools.Method):
    """Aktualisiert den Direktabfluss anhand des Frostversiegelungsgrades
    (adjusts the direct runoff according to the degree of frost sealing)

    Basic equation:
      :math:`Max(FVG \\cdot WaDa - QDB), 0)`

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WaDa,
        lland_fluxes.FVG,
    )
    UPDATEDSEQUENCES = (
        lland_fluxes.QDB,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.qdb[k] += flu.fvg[k] * (flu.wada[k] - flu.qdb[k])


class Calc_BoWa_V1(modeltools.Method):
    """Update soil moisture and correct fluxes if necessary.

    Basic equations:
       :math:`\\frac{dBoWa}{dt} = WaDa + Qkap - EvB - QBB - QIB1 - QIB2 - QDB`

       :math:`BoWa \\geq 0`

    Examples:

        For water areas (|FLUSS| and |SEE|) and sealed areas (|VERS|),
        soil moisture |BoWa| is simply set to zero and no flux correction
        are performed (see the first three HRUs).  No principal distinction
        is made between the remaining land use classes (arable land |ACKER|
        has been selected for the last four HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> fk(1.0)
        >>> corrqbbflag(0)
        >>> states.bowa = 2.0
        >>> fluxes.wada = 1.0
        >>> fluxes.evb = 1.0, 1.0, 1.0, 0.0, 0.1, 0.2, 0.3
        >>> fluxes.qbb = 1.0, 1.0, 1.0, 0.0, 0.2, 0.4, 0.6
        >>> fluxes.qkap = 0.5, 0.5, 0.5, 0.0, 0.1, 0.2, 0.3
        >>> fluxes.qib1 = 1.0, 1.0, 1.0, 0.0, 0.3, 0.6, 0.9
        >>> fluxes.qib2 = 1.0, 1.0, 1.0, 0.0, 0.4, 0.8, 1.2
        >>> fluxes.qdb = 1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 1.5
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 0.0, 3.0, 1.5, 0.2, 0.0)
        >>> fluxes.evb
        evb(1.0, 1.0, 1.0, 0.0, 0.1, 0.2, 0.22)
        >>> fluxes.qbb
        qbb(1.0, 1.0, 1.0, 0.0, 0.2, 0.4, 0.44)
        >>> fluxes.qkap
        qkap(0.5, 0.5, 0.5, 0.0, 0.0, 0.2, 0.3)
        >>> fluxes.qib1
        qib1(1.0, 1.0, 1.0, 0.0, 0.3, 0.6, 0.66)
        >>> fluxes.qib2
        qib2(1.0, 1.0, 1.0, 0.0, 0.4, 0.8, 0.88)
        >>> fluxes.qdb
        qdb(1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 1.1)

        The capillary rise is reduced for all cases where |BoWa| is bigger
        than |FK|

        >>> fluxes.qkap
        qkap(0.5, 0.5, 0.5, 0.0, 0.0, 0.2, 0.3)

        For the seventh HRU, the original total loss terms would result in a
        negative soil moisture value.  Hence it is reduced to the total loss
        term of the sixt HRU, which results exactly in a complete emptying
        of the soil storage.

        If we set the correction flag true:

        >>> fk(2.5)
        >>> corrqbbflag(1)
        >>> states.bowa = 2.0
        >>> fluxes.wada = 1.0
        >>> fluxes.evb = 1.0, 1.0, 1.0, 0.0, 0.1, 0.2, 0.3
        >>> fluxes.qbb = 1.0, 1.0, 1.0, 0.0, 0.2, 0.4, 0.6
        >>> fluxes.qkap = 0.5, 0.5, 0.5, 0.0, 0.1, 0.2, 0.3
        >>> fluxes.qib1 = 1.0, 1.0, 1.0, 0.0, 0.3, 0.6, 0.9
        >>> fluxes.qib2 = 1.0, 1.0, 1.0, 0.0, 0.4, 0.8, 1.2
        >>> fluxes.qdb = 1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 1.5
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 0.0, 3.0, 1.8, 0.6, 0.0)
        >>> fluxes.evb
        evb(1.0, 1.0, 1.0, 0.0, 0.1, 0.2, 0.253846)
        >>> fluxes.qbb
        qbb(1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.qkap
        qkap(0.5, 0.5, 0.5, 0.0, 0.1, 0.2, 0.3)
        >>> fluxes.qib1
        qib1(1.0, 1.0, 1.0, 0.0, 0.3, 0.6, 0.761538)
        >>> fluxes.qib2
        qib2(1.0, 1.0, 1.0, 0.0, 0.4, 0.8, 1.015385)
        >>> fluxes.qdb
        qdb(1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 1.269231)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.CorrQBBFlag,
        lland_control.FK,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WaDa,
    )
    UPDATEDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvB,
        lland_fluxes.QBB,
        lland_fluxes.QIB1,
        lland_fluxes.QIB2,
        lland_fluxes.QDB,
        lland_fluxes.QKap,
    )
    RESULTSEQUENCES = (

    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                sta.bowa[k] = 0.
            else:
                # TODO: Mit der neuen Variante ist Kondensation möglich
                if flu.evb[k] > 0.:
                    d_evap = flu.evb[k]
                    d_cond = 0.
                else:
                    d_evap = 0.
                    d_cond = flu.evb[k]
                d_bvl = (
                    d_evap + flu.qbb[k] + flu.qib1[k] + flu.qib2[k] +
                    flu.qdb[k])
                d_mvl = sta.bowa[k] + flu.wada[k] + flu.qkap[k] + d_cond
                if d_bvl > d_mvl:
                    if con.corrqbbflag[k] and flu.qbb[k] > 0.:
                        d_delta = min(d_bvl - d_mvl, flu.qbb[k])
                        flu.qbb[k] -= d_delta
                        d_bvl = (
                            d_evap + flu.qbb[k] + flu.qib1[k] +
                            flu.qib2[k] + flu.qdb[k])
                        d_mvl = sta.bowa[k] + flu.wada[k] + flu.qkap[k] + d_cond
                        if d_bvl > d_mvl:
                            sta.bowa[k] = d_mvl - d_bvl
                    d_rvl = d_mvl / d_bvl
                    if flu.evb[k] > 0:
                        flu.evb[k] *= d_rvl
                    flu.qbb[k] *= d_rvl
                    flu.qib1[k] *= d_rvl
                    flu.qib2[k] *= d_rvl
                    flu.qdb[k] *= d_rvl
                    sta.bowa[k] = 0.
                else:
                    sta.bowa[k] = d_mvl - d_bvl
                    if con.corrqbbflag[k] and (sta.bowa[k] < con.fk[k]):
                        if flu.qbb[k] > 0.:
                            d_delta = min(con.fk[k] - sta.bowa[k], flu.qbb[k])
                            flu.qbb[k] -= d_delta
                            sta.bowa[k] += d_delta
                    elif sta.bowa[k] > con.fk[k]:
                        if flu.qkap[k] > 0.:
                            d_delta = min(sta.bowa[k] - con.fk[k], flu.qkap[k])
                            flu.qkap[k] -= d_delta
                            sta.bowa[k] -= d_delta


class Calc_QBGZ_V1(modeltools.Method):
    """Aggregate the amount of base flow released by all "soil type" HRUs
    and the "net precipitation" above water areas of type |SEE|.

    Water areas of type |SEE| are assumed to be directly connected with
    groundwater, but not with the stream network.  This is modelled by
    adding their (positive or negative) "net input" (|NKor|-|EvI|) to the
    "percolation output" of the soil containing HRUs.

    Basic equation:
       :math:`QBGZ = \\Sigma(FHRU \\cdot (QBB-Qkap)) +
       \\Sigma(FHRU \\cdot (NKor_{SEE}-EvI_{SEE}))`

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
    RESULTSEQUENCES = (
        lland_states.QBGZ,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qbgz = 0.
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
    REQUIREDSEQUENCES = (
        lland_fluxes.QIB1,
    )
    RESULTSEQUENCES = (
        lland_states.QIGZ1,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qigz1 = 0.
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
    REQUIREDSEQUENCES = (
        lland_fluxes.QIB2,
    )
    RESULTSEQUENCES = (
        lland_states.QIGZ2,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qigz2 = 0.
        for k in range(con.nhru):
            sta.qigz2 += con.fhru[k] * flu.qib2[k]


class Calc_QDGZ_V1(modeltools.Method):
    """Aggregate the amount of total direct flow released by all HRUs.

    Basic equation:
       :math:`QDGZ = \\Sigma(FHRU \\cdot QDB) +
       \\Sigma(FHRU \\cdot (NKor_{FLUSS}-EvI_{FLUSS}))`

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
    RESULTSEQUENCES = (
        lland_fluxes.QDGZ,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qdgz = 0.
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
        >>> parameterstep('1d')
        >>> simulationstep('12h')
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
    REQUIREDSEQUENCES = (
        lland_fluxes.QDGZ,
    )
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
            sta.qdgz2 = 0.
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
    DERIVEDPARAMETERS = (
        lland_derived.KB,
    )
    REQUIREDSEQUENCES = (
        lland_states.QBGZ,
        lland_states.QBGA,
    )
    RESULTSEQUENCES = (
        lland_states.QBGA,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kb <= 0.:
            new.qbga = new.qbgz
        elif der.kb > 1e200:
            new.qbga = old.qbga + new.qbgz - old.qbgz
        else:
            d_temp = (1. - modelutils.exp(-1. / der.kb))
            new.qbga = (old.qbga +
                        (old.qbgz - old.qbga) * d_temp +
                        (new.qbgz - old.qbgz) * (1. - der.kb * d_temp))


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
    DERIVEDPARAMETERS = (
        lland_derived.KI1,
    )
    REQUIREDSEQUENCES = (
        lland_states.QIGZ1,
        lland_states.QIGA1,
    )
    RESULTSEQUENCES = (
        lland_states.QIGA1,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.ki1 <= 0.:
            new.qiga1 = new.qigz1
        elif der.ki1 > 1e200:
            new.qiga1 = old.qiga1 + new.qigz1 - old.qigz1
        else:
            d_temp = (1. - modelutils.exp(-1. / der.ki1))
            new.qiga1 = (old.qiga1 +
                         (old.qigz1 - old.qiga1) * d_temp +
                         (new.qigz1 - old.qigz1) * (1. - der.ki1 * d_temp))


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
    DERIVEDPARAMETERS = (
        lland_derived.KI2,
    )
    REQUIREDSEQUENCES = (
        lland_states.QIGZ2,
        lland_states.QIGA2,
    )
    RESULTSEQUENCES = (
        lland_states.QIGA2,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.ki2 <= 0.:
            new.qiga2 = new.qigz2
        elif der.ki2 > 1e200:
            new.qiga2 = old.qiga2 + new.qigz2 - old.qigz2
        else:
            d_temp = (1. - modelutils.exp(-1. / der.ki2))
            new.qiga2 = (old.qiga2 +
                         (old.qigz2 - old.qiga2) * d_temp +
                         (new.qigz2 - old.qigz2) * (1. - der.ki2 * d_temp))


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
    DERIVEDPARAMETERS = (
        lland_derived.KD1,
    )
    REQUIREDSEQUENCES = (
        lland_states.QDGZ1,
        lland_states.QDGA1,
    )
    RESULTSEQUENCES = (
        lland_states.QDGA1,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kd1 <= 0.:
            new.qdga1 = new.qdgz1
        elif der.kd1 > 1e200:
            new.qdga1 = old.qdga1 + new.qdgz1 - old.qdgz1
        else:
            d_temp = (1. - modelutils.exp(-1. / der.kd1))
            new.qdga1 = (old.qdga1 +
                         (old.qdgz1 - old.qdga1) * d_temp +
                         (new.qdgz1 - old.qdgz1) * (1. - der.kd1 * d_temp))


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
    DERIVEDPARAMETERS = (
        lland_derived.KD2,
    )
    REQUIREDSEQUENCES = (
        lland_states.QDGZ2,
        lland_states.QDGA2,
    )
    RESULTSEQUENCES = (
        lland_states.QDGA2,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kd2 <= 0.:
            new.qdga2 = new.qdgz2
        elif der.kd2 > 1e200:
            new.qdga2 = old.qdga2 + new.qdgz2 - old.qdgz2
        else:
            d_temp = (1. - modelutils.exp(-1. / der.kd2))
            new.qdga2 = (old.qdga2 +
                         (old.qdgz2 - old.qdga2) * d_temp +
                         (new.qdgz2 - old.qdgz2) * (1. - der.kd2 * d_temp))


class Calc_Q_V1(modeltools.Method):
    """Calculate the final runoff.

    Note that, in case there are water areas, their |NKor| values are
    added and their |EvPo| values are subtracted from the "potential"
    runoff value, if possible.  This hold true for |WASSER| only and is
    due to compatibility with the original LARSIM implementation. Using land
    type |WASSER| can result  in problematic modifications of simulated
    runoff series. It seems advisable to use land type |FLUSS| and/or
    land type |SEE| instead.

    Basic equations:
       :math:`Q = QBGA + QIGA1 + QIGA2 + QDGA1 + QDGA2 +
       NKor_{WASSER} - EvI_{WASSER}`

       :math:`Q \\geq 0`

    Examples:

        When there are no water areas in the respective subbasin (we
        choose arable land |ACKER| arbitrarily), the different runoff
        components are simply summed up:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER, ACKER, ACKER)
        >>> fhru(0.5, 0.2, 0.3)
        >>> negq(False)
        >>> states.qbga = 0.1
        >>> states.qiga1 = 0.3
        >>> states.qiga2 = 0.5
        >>> states.qdga1 = 0.7
        >>> states.qdga2 = 0.9
        >>> fluxes.nkor = 10.0
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(2.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        The defined values of interception evaporation do not show any
        impact on the result of the given example, the predefined values
        for sequence |EvI| remain unchanged.  But when the first HRU is
        assumed to be a water area (|WASSER|), its adjusted precipitaton
        |NKor| value and its interception  evaporation |EvI| value are added
        to and subtracted from |lland_fluxes.Q| respectively:

        >>> control.lnk(WASSER, VERS, NADELW)
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(5.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        Note that only 5 mm are added (instead of the |NKor| value 10 mm)
        and that only 2 mm are substracted (instead of the |EvI| value 4 mm,
        as the first HRU`s area only accounts for 50 % of the subbasin area.

        Setting also the land use class of the second HRU to land type
        |WASSER| and resetting |NKor| to zero would result in overdrying.
        To avoid this, both actual water evaporation values stored in
        sequence |EvI| are reduced by the same factor:

        >>> control.lnk(WASSER, WASSER, NADELW)
        >>> fluxes.nkor = 0.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(0.0)
        >>> fluxes.evi
        evi(3.333333, 4.166667, 3.0)

        The handling from water areas of type |FLUSS| and |SEE| differs
        from those of type |WASSER|, as these do receive their net input
        before the runoff concentration routines are applied.  This
        should be more realistic in most cases (especially for type |SEE|
        representing lakes not direct connected to the stream network).
        But it could sometimes result in negative outflow values. This
        is avoided by simply setting |lland_fluxes.Q| to zero and adding
        the truncated negative outflow value to the |EvI| value of all
        HRUs of type |FLUSS| and |SEE|:

        >>> control.lnk(FLUSS, SEE, NADELW)
        >>> states.qbga = -1.0
        >>> states.qdga2 = -1.5
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(0.0)
        >>> fluxes.evi
        evi(2.571429, 3.571429, 3.0)

        This adjustment of |EvI| is only correct regarding the total
        water balance.  Neither spatial nor temporal consistency of the
        resulting |EvI| values are assured.  In the most extreme case,
        even negative |EvI| values might occur.  This seems acceptable,
        as long as the adjustment of |EvI| is rarely triggered.  When in
        doubt about this, check sequences |EvPo| and |EvI| of HRUs of
        types |FLUSS| and |SEE| for possible discrepancies.  Also note
        that there might occur unnecessary corrections of |lland_fluxes.Q|
        in case landtype |WASSER| is combined with either landtype
        |SEE| or |FLUSS|.

        Eventually you might want to avoid correcting |lland_fluxes.Q|.
        This can be achieved by setting parameter |NegQ| to `True`:

        >>> negq(True)
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(-1.0)
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
        lland_fluxes.EvI,
    )
    UPDATEDSEQUENCES = (
        lland_fluxes.EvI,
    )
    RESULTSEQUENCES = (
        lland_fluxes.Q,
        lland_aides.EPW,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.q = sta.qbga + sta.qiga1 + sta.qiga2 + sta.qdga1 + sta.qdga2
        if (not con.negq) and (flu.q < 0.):
            d_area = 0.
            for k in range(con.nhru):
                if con.lnk[k] in (FLUSS, SEE):
                    d_area += con.fhru[k]
            if d_area > 0.:
                for k in range(con.nhru):
                    if con.lnk[k] in (FLUSS, SEE):
                        flu.evi[k] += flu.q / d_area
            flu.q = 0.
        aid.epw = 0.
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.q += con.fhru[k] * flu.nkor[k]
                aid.epw += con.fhru[k] * flu.evi[k]
        if (flu.q > aid.epw) or con.negq:
            flu.q -= aid.epw
        elif aid.epw > 0.:
            for k in range(con.nhru):
                if con.lnk[k] == WASSER:
                    flu.evi[k] *= flu.q / aid.epw
            flu.q = 0.


class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
       :math:`Q_{outlets} = QFactor \\cdot Q_{fluxes}`
    """
    DERIVEDPARAMETERS = (
        lland_derived.QFactor,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.Q,
    )
    RESULTSEQUENCES = (
        lland_outlets.Q,
    )
    
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += der.qfactor * flu.q


class PegasusTempSSurface(roottools.Pegasus):
    """Objective function of PegasesTempSSurface iteration."""   # ToDo
    METHODS = (
        Calc_EnergyBalanceSurface_V1,
    )


class Model(modeltools.AdHocModel):
    """Base model for HydPy-L-Land."""
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        Adjust_WindSpeed_V1,
        Calc_PM_Single_V1,
        Calc_Penman_V1,
        Calc_EnergyBalanceSurface_V1,
        Calc_WSensSnow_Single_V1,
        Calc_SaturationVapourPressure_Single_V1,
        Calc_ActualVapourPressure_Single_V1,
        Calc_WLatSnow_Single_V1,
        Calc_WSurf_Single_V1,
        Calc_NetLongwaveRadiation_Single_V1,
    )
    RUN_METHODS = (
        Calc_NKor_V1,
        Calc_TKor_V1,
        Calc_PsychrometricConstant_V1,
        Calc_WindSpeed2m_V1,
        Calc_WindSpeed10m_V1,
        Calc_EarthSunDistance_V1,
        Calc_SolarDeclination_V1,
        Calc_SunsetHourAngle_V1,
        Calc_SolarTimeAngle_V1,
        Calc_ExtraterrestrialRadiation_V1,
        Calc_PossibleSunshineDuration_V1,
        Update_LoggedPossibleSunshineDuration_V1,
        Calc_GlobalRadiation_V1,
        Update_LoggedSunshineDuration_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Calc_ET0_V1,
        Calc_ET0_WET0_V1,
        Calc_EvPo_V1,
        Calc_NBes_Inzp_V1,
        Calc_SN_Ratio_V1,
        Calc_SKor_V1,
        Calc_F2SIMax_V1,
        Calc_SInzpCap_V1,
        Calc_F2SIRate_V1,
        Calc_SInzpRate_V1,
        Calc_NBes_SInz_V1,
        Calc_SBes_V1,
        Calc_WATS_V1,
        Calc_WaDa_WAeS_V1,
        Calc_WGTF_V1,
        Calc_WNied_V1,
        Calc_WNied_V2,
        Update_ESnow_V1,
        Calc_TZ_V1,
        Calc_WG_V1,
        Calc_TempS_V1,
        Update_TauS_V1,
        Calc_AlbedoCorr_V1,
        Calc_NetLongwaveRadiation_V1,
        Calc_NetShortwaveRadiation_V1,
        Calc_NetRadiation_V1,
        Calc_DryAirPressure_V1,
        Calc_DensityAir_V1,
        Calc_AerodynamicResistance_V1,
        Calc_SurfaceResistanceBare_V1,
        Calc_SurfaceResistanceLandUse_V1,
        Calc_SurfaceResistanceMoist_V1,
        Calc_SurfaceResistanceCorr_V1,
        Calc_EvPo_V2,
        Calc_EvPo_V3,
        Calc_EvPoWater_V1,
        Calc_EvI_Inzp_V1,
        Calc_EvB_V1,
        Calc_EvB_V2,
        Update_EBdn_V1,
        Calc_TempSSurface_V1,
        Calc_SchmPot_V1,
        Calc_WSnow_V1,
        Update_ESnow_V2,
        Calc_SchmPot_V2,
        Calc_GefrPot_V1,
        Calc_Schm_WATS_V1,
        Calc_Gefr_WATS_V1,
        Calc_EvPoSnow_WAeS_WATS_V1,
        Update_WaDa_WAeS_V1,
        Update_ESnow_V3,
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
        Calc_Q_V1,
    )
    OUTLET_METHODS = (
        Pass_Q_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = (
        PegasusTempSSurface,
    )
    INDICES = (
        'idx_sim',
        'idx_hru',
    )
