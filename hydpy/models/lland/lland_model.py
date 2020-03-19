# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring
"""
.. _`Allen`: http://www.fao.org/3/x0490e/x0490e00.htm
.. _`ATV-DVWK-M 504`: \
https://webshop.dwa.de/de/merkblatt-atv-dvwk-m-504-september-2002.html
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.nkor[k] = con.kg[k]*inp.nied


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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.tkor[k] = con.kt[k]+inp.teml


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
    def __call__(model: 'lland.Model') -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.psychrometricconstant = 6.65e-4*inp.atmosphericpressure


class Return_AdjustedWindSpeed_V1(modeltools.Method):
    """Adjust and return the measured wind speed to the given defined
    height above the ground.

    Basic equation (`Allen`_ equation 47, modified for higher precision):
      :math:`WindSpeed \\cdot
      \\frac{ln((newheight-d)/z_0)}{ln((MeasuringHeightWindSpeed-d)/z_0)}` \n

      :math:`d = 2 / 3 \\cdot 0.12` \n

      :math:`z_0 = 0.123 \\cdot 0.12`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> from hydpy import round_
        >>> round_(model.return_adjustedwindspeed_v1(2.0))
        3.738763
        >>> round_(model.return_adjustedwindspeed_v1(0.5))
        2.571532
        """
    CONTROLPARAMETERS = (
        lland_control.MeasuringHeightWindSpeed,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.WindSpeed,
    )

    @staticmethod
    def __call__(model: 'lland.Model', newheight: float) -> float:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        d_d = 2./3.*.12
        d_z0 = .123*.12
        return (inp.windspeed *
                (modelutils.log((newheight-d_d)/d_z0) /
                 modelutils.log((con.measuringheightwindspeed-d_d)/d_z0)))


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
        windspeed2m(3.738763)
    """
    SUBMETHODS = (
        Return_AdjustedWindSpeed_V1,
    )
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
    def __call__(model: 'lland.Model') -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed2m = model.return_adjustedwindspeed_v1(2.)


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
        windspeed10m(6.15649)
    """
    SUBMETHODS = (
        Return_AdjustedWindSpeed_V1,
    )
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
    def __call__(model: 'lland.Model') -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.windspeed10m = model.return_adjustedwindspeed_v1(10.)


class Calc_EarthSunDistance_V1(modeltools.Method):
    # noinspection PyUnresolvedReferences
    """Calculate the relative inverse distance between the earth and the sun.

    Additional requirements:
      |Model.idx_sim|

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
    FIXEDPARAMETERS = (
        lland_fixed.Pi,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EarthSunDistance,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.earthsundistance = 1.+0.033*modelutils.cos(
            2.*fix.pi/366.*(der.doy[model.idx_sim]+1.))


class Calc_SolarDeclination_V1(modeltools.Method):
    # noinspection PyUnresolvedReferences
    """Calculate the solar declination.

    Additional requirements:
      |Model.idx_sim|

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
    FIXEDPARAMETERS = (
        lland_fixed.Pi,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SolarDeclination,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.solardeclination = .409*modelutils.sin(
            2.*fix.pi/366.*(der.doy[model.idx_sim]+1.)-1.39)


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
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.sunsethourangle = modelutils.acos(
            -modelutils.tan(der.latituderad) *
            modelutils.tan(flu.solardeclination))


class Calc_SolarTimeAngle_V1(modeltools.Method):
    """Calculate the solar time angle at the midpoint of the current period.

    Additional requirements:
      |Model.idx_sim|

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
    FIXEDPARAMETERS = (
        lland_fixed.Pi,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SolarTimeAngle,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_b = 2.*fix.pi*(der.doy[model.idx_sim]-80.)/365.
        d_sc = (
            .1645*modelutils.sin(2.*d_b) -
            .1255*modelutils.cos(d_b) -
            .025*modelutils.sin(d_b))
        flu.solartimeangle = fix.pi/12. * (
            (der.sct[model.idx_sim]/60./60. +
             (con.longitude-der.utclongitude)/15.+d_sc)-12.)


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
    FIXEDPARAMETERS = (
        lland_fixed.Pi,
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
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_g = 0.0820/60.
        if der.seconds <= 60.*60.:
            d_delta = fix.pi*der.seconds/60./60./24.
            d_omega1 = flu.solartimeangle - d_delta
            d_omega2 = flu.solartimeangle + d_delta
            flu.extraterrestrialradiation = max(
                12.*der.seconds/fix.pi*d_g*flu.earthsundistance * (
                    (d_omega2-d_omega1) *
                    modelutils.sin(der.latituderad) *
                    modelutils.sin(flu.solardeclination) +
                    modelutils.cos(der.latituderad) *
                    modelutils.cos(flu.solardeclination) *
                    (modelutils.sin(d_omega2)-modelutils.sin(d_omega1))), 0.)
        else:
            flu.extraterrestrialradiation = (
                der.seconds/fix.pi*d_g*flu.earthsundistance * (
                    flu.sunsethourangle*modelutils.sin(der.latituderad) *
                    modelutils.sin(flu.solardeclination) +
                    modelutils.cos(der.latituderad) *
                    modelutils.cos(flu.solardeclination) *
                    modelutils.sin(flu.sunsethourangle)))


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
    FIXEDPARAMETERS = (
        lland_fixed.Pi,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SolarTimeAngle,
        lland_fluxes.SunsetHourAngle,
    )
    RESULTSEQUENCES = (
        lland_fluxes.PossibleSunshineDuration,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_hours = der.seconds/60./60.
        d_days = d_hours/24.
        if d_hours <= 1.:
            if flu.solartimeangle <= 0.:
                d_thresh = -flu.solartimeangle-fix.pi*d_days
            else:
                d_thresh = flu.solartimeangle-fix.pi*d_days
            flu.possiblesunshineduration = \
                min(max(12./fix.pi*(flu.sunsethourangle-d_thresh), 0.), d_hours)
        else:
            flu.possiblesunshineduration = 24./fix.pi*flu.sunsethourangle


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
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedpossiblesunshineduration[idx] = \
                log.loggedpossiblesunshineduration[idx - 1]
        log.loggedpossiblesunshineduration[0] = flu.possiblesunshineduration


class Calc_GlobalRadiation_V1(modeltools.Method):
    """Calculate the global radiation.

    Additional requirements:
      |Model.idx_sim|

    Basic equations:
      :math:`GlobalRadiation = Extraterrestrialradiation * (AngstromConstant +
      AngstromFactor * SunshineDuration / PossibleSunshineDuration))`

    Example:

        You can define the underlying Angstrom coefficients on a monthly
        basis to the annual variability in the relationship between sunshine
        duration and  global radiation:

        >>> from hydpy.models.lland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> pub.timegrids = '2000-01-30', '2000-02-03', '1d'
        >>> derived.moy.update()
        >>> angstromconstant.jan = 0.1
        >>> angstromfactor.jan = 0.5
        >>> angstromconstant.feb = 0.2
        >>> angstromfactor.feb = 0.6
        >>> inputs.sunshineduration(0.6)
        >>> fluxes.possiblesunshineduration = 1.0
        >>> fluxes.extraterrestrialradiation = 1.7
        >>> model.idx_sim = 1
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.68)
        >>> model.idx_sim = 2
        >>> model.calc_globalradiation_v1()
        >>> fluxes.globalradiation
        globalradiation(0.952)

        If possible sunshine duration is zero, we generally set global
        radiation to zero (even if the actual sunshine duration is larger
        than zero, which might occur as a result of small inconsistencies
        between measured and calculated input data):

        >>> fluxes.possiblesunshineduration = 0.0
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        if flu.possiblesunshineduration > 0.:
            idx = der.moy[model.idx_sim]
            flu.globalradiation = flu.extraterrestrialradiation * (
                con.angstromconstant[idx]+con.angstromfactor[idx] *
                inp.sunshineduration/flu.possiblesunshineduration)
        else:
            flu.globalradiation = 0.


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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = con.ke[k]*(
                ((8.64*inp.glob+93.*con.kf[k])*(flu.tkor[k]+22.)) /
                (165.*(flu.tkor[k]+123.) * (1.+0.00019*min(con.hnn[k], 600.))))


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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = (con.wfet0[k]*con.ke[k]*inp.pet +
                          (1.-con.wfet0[k])*log.wet0[0, k])
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
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.ET0,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvPo,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.evpo[k] = \
                con.fln[con.lnk[k]-1, der.moy[model.idx_sim]]*flu.et0[k]


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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.nbes[k] = 0.
                sta.inzp[k] = 0.
            else:
                flu.nbes[k] = max(
                    flu.nkor[k]+sta.inzp[k] -
                    der.kinz[con.lnk[k]-1, der.moy[model.idx_sim]], 0.)
                sta.inzp[k] += flu.nkor[k]-flu.nbes[k]


class Calc_SN_Ratio_V1(modeltools.Method):
    """Calculate the ratio of frozen to total precipitation.

    Examples:

        In the first example, the threshold temperature of seven
        hydrological response units is 0 °C and the temperature interval
        of mixed precipitation 2 °C:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> tgr(1.0)
        >>> tsp(2.0)

        The value of |SN_Ratio| is zero above 1 °C and 1 below -1 °C.  Between
        these temperature values |SN_Ratio| decreases linearly:

        >>> fluxes.nkor = 4.0
        >>> fluxes.tkor = -9.0, 0.0, 0.5, 1.0, 1.5, 2.0, 11.0
        >>> model.calc_sn_ratio_v1()
        >>> aides.sn_ratio
        sn_ratio(1.0, 1.0, 0.75, 0.5, 0.25, 0.0, 0.0)

        Note the special case of a zero temperature interval.  With the
        actual temperature being equal to the threshold temperature, the
        the value of |SN_Ratio| is zero:

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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if flu.tkor[k] >= (con.tgr[k]+con.tsp[k]/2.):
                aid.sn_ratio[k] = 0.
            elif flu.tkor[k] <= (con.tgr[k]-con.tsp[k]/2.):
                aid.sn_ratio[k] = 1.
            else:
                aid.sn_ratio[k] = \
                    ((con.tgr[k]+con.tsp[k]/2.)-flu.tkor[k])/con.tsp[k]


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
#     def __call__(model: 'lland.Model') -> None:
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
#     def __call__(model: 'lland.Model') -> None:
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
#     def __call__(model: 'lland.Model') -> None:
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
#     def __call__(model: 'lland.Model') -> None:
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
#         lland_aides.SN_Ratio,
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
#     def __call__(model: 'lland.Model') -> None:
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
#                 flu.sbes[k] = aid.sn_ratio[k] * flu.nbes[k]
#                 d_ninz = flu.nkor[k] - flu.nbes[k]
#                 d_sinz = aid.sn_ratio[k] * d_ninz
#                 sta.sinz[k] += d_ninz
#                 sta.stinz[k] += d_sinz
#                 d_nbes = max(sta.sinz[k] - con.pwmax[k] * sta.stinz[k], 0.)
#                 flu.nbes[k] += d_nbes
#                 sta.sinz[k] -= d_nbes


class Calc_SBes_V1(modeltools.Method):
    """Calculate the frozen part of stand precipitation.

    Basic equation:
      :math:`SBes = SN_Ratio \\cdot NBes`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> fluxes.nbes = 10.0
        >>> aides.sn_ratio = 0.2, 0.8
        >>> model.calc_sbes_v1()
        >>> fluxes.sbes
        sbes(2.0, 8.0)
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            flu.sbes[k] = aid.sn_ratio[k]*flu.nbes[k]


class Calc_WATS_V1(modeltools.Method):
    """Add the snow fall to the frozen water equivalent of the snow cover.

    Basic equation:
      :math:`WATS = WATS + SBes`

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
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
    )
    UPDATEDSEQUENCES = (
        lland_states.WATS,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.wats[k] = 0.
            else:
                sta.wats[k] += flu.sbes[k]


class Calc_WaDa_WAeS_V1(modeltools.Method):
    """Add as much liquid precipitation to the snow cover as it is able to hold.

    Basic equations:
      :math:`\\frac{dWAeS}{dt} = NBes - WaDa`

      :math:`WAeS \\leq PWMax \\cdot WATS`

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
        |Calc_WaDa_WAeS_V1|only the amount only passes the part of |NBes|
        exceeding the actual snow holding capacity to |WaDa|.
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
    def __call__(model: 'lland.Model') -> None:
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
        |SEE|) in principally identical for all other land-use type
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
    FIXEDPARAMETERS = (
        lland_fixed.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WGTF,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wgtf[k] = 0.
            else:
                flu.wgtf[k] = con.gtf[k]*(flu.tkor[k]-con.treft[k])*fix.rschmelz


class Calc_WNied_V1(modeltools.Method):
    """Calculate the heat flux into the snow layer due to the total amount
    of ingoing precipitation.

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
    )
    RESULTSEQUENCES = (
        lland_fluxes.WNied,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wnied[k] = 0.
            else:
                d_ice = fix.cpeis*flu.sbes[k]
                d_water = fix.cpwasser*(flu.nbes[k]-flu.sbes[k])
                flu.wnied[k] = (flu.tkor[k]-con.trefn[k])*(d_ice+d_water)


class Calc_WNied_ESnow_V1(modeltools.Method):
    """Calculate the heat flux into the snow layer due to the amount
    of precipitation actually hold by the snow layer.

    Method |Calc_WNied_V1| assumes that the temperature of precipitation
    equals air temperature minus |TRefN|.  The same holds for the
    temperature of the fraction of precipitation not hold by the snow
    layer (in other words: no temperature mixing occurs).

    Basic equation:
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
    UPDATEDSEQUENCES = (
        lland_states.ESnow,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WNied,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wnied[k] = 0.
                sta.esnow[k] = 0.
            else:
                d_ice = fix.cpeis*flu.sbes[k]
                d_water = fix.cpwasser*(flu.nbes[k]-flu.sbes[k]-flu.wada[k])
                flu.wnied[k] = (flu.tkor[k]-con.trefn[k])*(d_ice+d_water)
                sta.esnow[k] += flu.wnied[k]


class Return_SaturationVapourPressure_V1(modeltools.Method):
    """Calculate and return the saturation vapour pressure over an
    arbitrary surface for the given temperature.

    Basic equation (Allen, equation 11, modified):
      :math:`0.6108 \\cdot
      \\exp(\\frac{17.08085 \\cdot Temperature}{Temperature + 234.175})`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_saturationvapourpressure_v1(10.0))
        1.229426
    """

    @staticmethod
    def __call__(model: 'lland.Model', temperature: float) -> float:
        return .6108*modelutils.exp(17.08085*temperature/(temperature+234.175))


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    """Calculate the saturation vapour pressure over arbitrary surfaces.

    Method |Calc_SaturationVapourPressure_V1| uses method
    |Return_SaturationVapourPressure_V1| to calculate the saturation
    vapour pressure of all hydrological response units.

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> fluxes.tkor(-10.0, 0.0, 10.0)
        >>> model.calc_saturationvapourpressure_v1()
        >>> fluxes.saturationvapourpressure
        saturationvapourpressure(0.285096, 0.6108, 1.229426)
    """
    SUBMETHODS = (
        Return_SaturationVapourPressure_V1,
    )
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
    def __call__(model: 'lland.Model') -> None:
        flu = model.sequences.fluxes.fastaccess
        con = model.parameters.control.fastaccess
        for k in range(con.nhru):
            flu.saturationvapourpressure[k] = \
                model.return_saturationvapourpressure_v1(flu.tkor[k])


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    """Calculate the slope of the saturation vapour pressure curve.

    Basic equation (`Allen`_, equation 13, modified):
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.saturationvapourpressureslope[k] = \
                4098.*flu.saturationvapourpressure[k]/(flu.tkor[k]+237.3)**2


class Return_ActualVapourPressure_V1(modeltools.Method):
    """Calculate and return the actual vapour pressure for the given
    saturation vapour pressure.

    Basic equation (`Allen`_, equation 19, modified):
      :math:`SaturationVapourPressure \\cdot RelativeHumidity / 100`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> inputs.relativehumidity = 60.0
        >>> from hydpy import round_
        >>> round_(model.return_actualvapourpressure_v1(2.0))
        1.2
    """
    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
    )

    @staticmethod
    def __call__(model: 'lland.Model', saturationvapourpressure: float) \
            -> float:
        inp = model.sequences.inputs.fastaccess
        return saturationvapourpressure * inp.relativehumidity / 100.


class Calc_ActualVapourPressure_V1(modeltools.Method):
    """Calculate the actual vapour pressure.

    Method |Calc_ActualVapourPressure_V1| uses method
    |Return_ActualVapourPressure_V1| to calculate the actual
    vapour pressure of all hydrological response units.

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
    SUBMETHODS = (
        Return_ActualVapourPressure_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.RelativeHumidity,
        lland_fluxes.SaturationVapourPressure,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.actualvapourpressure[k] = \
                model.return_actualvapourpressure_v1(
                    flu.saturationvapourpressure[k])


class Return_NetLongwaveRadiation_V1(modeltools.Method):
    """Calculate and return the net longwave radiation.

    Method |Return_NetLongwaveRadiation_V1| relies on two different
    equations for snow-covered and snow-free surfaces.

    Basic equation (above a snow layer):
       :math:`-(Sigma \\cdot (TKor + 273.15)^4 \\cdot
       (FrAtm \\cdot (ActualVapourPressure \\cdot \\frac{10}
       {TKor + 273.15})^{\\frac{1}{7}}-Emissivity) \\cdot (0.2+0.8 \\cdot
       (\frac{SunshineDuration}{PossibleSunshineDuration})))`

    Basic equation (above a snow-free surface):
       :math:`(Sigma \\cdot (TempSSurface+273.15)^4 - Sigma \\cdot
       (Tkor + 273.15)^4 \\cdot FrAtm \\cdot (ActualVapourPressure \\cdot
       \\frac{10}{TKor[k] + 273.15})^{\\frac{1}{7}} \\cdot (1 + 0.22
       \\cdot (1-\frac{SunshineDuration}{PossibleSunshineDuration})^2))`

    Examples:

        The first two hydrological response units deal with a snow-free
        situation (where no temperature of a snow surface can be defined),
        wheres the last to units deal with a snow layer.  Note the
        considerable difference between the results of the second (snow-free)
        and the third (snow-covered) response unit:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> emissivity(0.95)
        >>> fratm(1.28)
        >>> derived.nmblogentries.update()
        >>> inputs.sunshineduration = 12.0
        >>> states.waes = 0.0, 0.0, 1.0, 1.0
        >>> fluxes.tkor = 22.1, 0.0, 0.0, 0.0
        >>> fluxes.actualvapourpressure = 1.6, 0.6, 0.6, 0.6
        >>> fluxes.possiblesunshineduration = 14.0
        >>> fluxes.tempssurface = nan, nan, 0.0, -5.0
        >>> from hydpy import print_values
        >>> for hru in range(4):
        ...     print_values([hru, model.return_netlongwaveradiation_v1(hru)])
        0, 3.495045
        1, 5.027685
        2, 6.949137
        3, 5.006517

        If we set the current sunshine duration to zero but log the original
        sunshine duration, we get the same results as above:

        >>> inputs.possiblesunshineduration = 0.0
        >>> logs.loggedsunshineduration = 12.0
        >>> logs.loggedpossiblesunshineduration = 14.0
        >>> for hru in range(4):
        ...     print_values([hru, model.return_netlongwaveradiation_v1(hru)])
        0, 3.495045
        1, 5.027685
        2, 6.949137
        3, 5.006517

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
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TempSSurface,
        lland_states.WAeS,
        lland_fluxes.ActualVapourPressure,
        lland_inputs.SunshineDuration,
        lland_logs.LoggedPossibleSunshineDuration,
        lland_logs.LoggedSunshineDuration,
    )

    @staticmethod
    def __call__(model: 'lland.Model', k: int) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess

        if flu.possiblesunshineduration > 0:
            d_sunshineduration = inp.sunshineduration
            d_possiblesunshineduration = flu.possiblesunshineduration
        else:
            d_sunshineduration = 0.
            d_possiblesunshineduration = 0.
            for idx in range(der.nmblogentries):
                d_possiblesunshineduration += \
                    log.loggedpossiblesunshineduration[idx]
                d_sunshineduration += log.loggedsunshineduration[idx]

        d_relsunshine = d_sunshineduration/d_possiblesunshineduration

        d_temp1 = fix.sigma*(flu.tkor[k]+273.15)**4
        d_temp2 = (flu.actualvapourpressure[k]*10. /
                   (flu.tkor[k]+273.15))**(1./7.)
        if sta.waes[k] > 0.:
            return (fix.sigma*(flu.tempssurface[k]+273.15)**4 -
                    d_temp1*con.fratm*d_temp2*(1.+.22*(1.-d_relsunshine)**2))
        return -(d_temp1*(con.fratm*d_temp2-con.emissivity) *
                 (.2+.8*d_relsunshine))


class Calc_NetLongwaveRadiation_V1(modeltools.Method):
    """Calculate the net longwave radiation for snow-free land surfaces.

    Example:

        Basically, method |Calc_NetLongwaveRadiation_V1| just uses method
        |Return_NetLongwaveRadiation_V1| to calculate the long wave
        radiation of each non-water response unit and keeps the eventually
        predefined values of the other ones:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> lnk(ACKER)
        >>> derived.nmblogentries.update()
        >>> fluxes.tkor = 22.1
        >>> fluxes.actualvapourpressure = 1.6
        >>> fluxes.possiblesunshineduration = 14.0
        >>> inputs.sunshineduration = 12.0
        >>> emissivity(0.95)
        >>> fratm(1.28)
        >>> states.waes = 0.0, 1.0
        >>> fluxes.tempssurface = nan
        >>> fluxes.netlongwaveradiation = 1.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.495045, 1.0)

        .. testsetup::

            >>> del pub.timegrids
    """
    SUBMETHODS = (
        Return_NetLongwaveRadiation_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Emissivity,
        lland_control.FrAtm,
    )
    DERIVEDPARAMETERS = (
        lland_derived.NmbLogEntries,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_states.WAeS,
        lland_fluxes.ActualVapourPressure,
        lland_logs.LoggedPossibleSunshineDuration,
        lland_logs.LoggedSunshineDuration,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NetLongwaveRadiation,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] <= 0.:
                flu.netlongwaveradiation[k] = \
                    model.return_netlongwaveradiation_v1(k)


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
    def __call__(model: 'lland.Model') -> None:
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


class Calc_ActualAlbedo_V1(modeltools.Method):
    """Calculate the current albedo value.

    For snow-free surfaces, method |Calc_AlbedoCorr_V1| takes the
    value of parameter |Albedo| relevant for the given landuse and month.
    For snow conditions, it estimates the albedo based on the snow age,
    as shown by the following equation.

    Basic equations:
      :math:`AlbedoSnow = Albedo0Snow \\cdot
      (1-SnowAgingFactor \\cdot \\frac{TauS}{1 + TauS})`

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
        lland_fluxes.ActualAlbedo,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                flu.actualalbedo[k] = (
                    con.albedo0snow *
                    (1.-con.snowagingfactor*sta.taus[k]/(1.+sta.taus[k])))
            else:
                flu.actualalbedo[k] = \
                    con.albedo[con.lnk[k]-1, der.moy[model.idx_sim]]


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    """Calculate the net shortwave radiation.

    Basic equation (`Allen`_, equation 38):
      :math:`NetShortwaveRadiation = (1.0 - Albedo) \\cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.actualalbedo(0.23, 0.5)
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
        lland_fluxes.ActualAlbedo,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NetShortwaveRadiation,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.netshortwaveradiation[k] = \
                (1.-flu.actualalbedo[k])*flu.globalradiation


class Return_TempS_V1(modeltools.Method):
    """Calculate and return the average temperature of the snow layer.

    Basic equation:
      :math:`\\frac{ESnow}{WATS \\cdot CPEis + (WAeS-WATS) \\cdot CPWasser}`

    Example:

        Note that we use |numpy.nan| values for snow-free surfaces
        (see the result of the first hydrological response unit):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> states.wats = 0.0, 0.5, 5.0
        >>> states.waes = 0.0, 1.0, 10.0
        >>> states.esnow = 0.0, 0.0, -0.1
        >>> from hydpy import round_
        >>> round_(model.return_temps_v1(0))
        nan
        >>> round_(model.return_temps_v1(1))
        0.0
        >>> round_(model.return_temps_v1(2))
        -3.186337
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
    def __call__(model: 'lland.Model', k: int) -> float:
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.waes[k] > 0.:
            d_ice = fix.cpeis*sta.wats[k]
            d_water = fix.cpwasser*(sta.waes[k]-sta.wats[k])
            return sta.esnow[k]/(d_ice+d_water)
        return modelutils.nan


class Return_ESnow_V1(modeltools.Method):
    """Calculate and return the energy content of the snow layer for
    the given bulk temperature.

    Basic equation:
      :math:`TempS \\cdot (WATS \\cdot CPEis + (WAeS-WATS)\\cdot CPWasser)`

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
    def __call__(model: 'lland.Model', k: int, temps: float) -> float:
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        d_ice = fix.cpeis*sta.wats[k]
        d_water = fix.cpwasser*(sta.waes[k]-sta.wats[k])
        return temps*(d_ice+d_water)


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
    SUBMETHODS = (
        Return_TempS_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    FIXEDPARAMETERS = (
        lland_fixed.CPWasser,
        lland_fixed.CPEis,
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            aid.temps[k] = model.return_temps_v1(k)


class Calc_TZ_V1(modeltools.Method):
    """Calculate the mean temperature in the top-layer of the soil.

    Basic equation for a completely frozen soil:
      :math:`TZ = \\frac{EBdn}{2 \\cdot z \\cdot c_G}`

    Basic equation for a partly frozen soil:
      :math:`TZ = 0`

    Basic equation for a completely unfrozen soil:
      :math:`TZ = \\frac{EBdn - BoWa2Z \\cdot RSchmelz}{2 \\cdot z \\cdot c_G}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> cg(1.5)
        >>> derived.heatoffusion(26.72)
        >>> states.ebdn(-10.0, -1.0, 0.0, 13.36, 26.72, 27.72, 36.72)
        >>> model.calc_tz_v1()
        >>> fluxes.tz
        tz(-33.333333, -3.333333, 0.0, 0.0, 0.0, 3.333333, 33.333333)
        """
    CONTROLPARAMETERS = (
        lland_control.CG,
    )
    DERIVEDPARAMETERS = (
        lland_derived.HeatOfFusion,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Z,
    )
    REQUIREDSEQUENCES = (
        lland_states.EBdn,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TZ,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.ebdn[k] < 0.:
                flu.tz[k] = sta.ebdn[k]/(2.*fix.z*con.cg[k])
            elif sta.ebdn[k] < der.heatoffusion[k]:
                flu.tz[k] = 0.
            else:
                flu.tz[k] = \
                    (sta.ebdn[k]-der.heatoffusion[k])/(2.*fix.z*con.cg[k])


class Return_WG_V1(modeltools.Method):
    """Calculate and return the soil heat flux.

    The soil heat flux depends on the temperature gradient between depth z
    and the surface.  We set the soil surface temperature to the air
    temperature for snow-free conditions and otherwise to the average
    temperature of the snow layer.

    Basic equations:
      :math:`\\lambdaG \\cdot \\frac{Tz-T_{surface}}{Z}`

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
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
    RESULTSEQUENCES = (
        lland_fluxes.WG,
    )

    @staticmethod
    def __call__(model: 'lland.Model', k: int) -> float:
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if sta.waes[k] > 0.:
            d_temp = aid.temps[k]
        else:
            d_temp = flu.tkor[k]
        return fix.lambdag*(flu.tz[k]-d_temp)/fix.z


class Calc_WG_V1(modeltools.Method):
    """Calculate the soil heat flux.

    Method |Calc_WG_V1| uses method |Return_WG_V1| to calculate the
    soil heat flux for all hydrological response units.

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
        >>> model.calc_wg_v1()
        >>> fluxes.wg
        wg(-0.1728, 0.0648)
    """
    SUBMETHODS = (
        Return_WG_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
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
    RESULTSEQUENCES = (
        lland_fluxes.WG,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.wg[k] = model.return_wg_v1(k)


class Update_EBdn_V1(modeltools.Method):
    """Update the energy content of the upper soil layer.

    Basic equation:
      :math:`\\frac{dEBdn}{dt} = WG2Z - WG`

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
        >>> states.ebdn = 0.0
        >>> fluxes.wg = 0.5, 1.0, 2.0
        >>> model.idx_sim = 1
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(-0.53, -1.03, -2.03)
        >>> model.idx_sim = 2
        >>> model.update_ebdn_v1()
        >>> states.ebdn
        ebdn(-1.07, -2.07, -4.07)

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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            sta.ebdn[k] += con.wg2z[der.moy[model.idx_sim]]-flu.wg[k]


class Return_WSensSnow_V1(modeltools.Method):
    """Calculate and return the sensible heat flux of the snow surface.

    Basic equations:
      :math:`(Turb0 + Turb1 \\cdot WindSpeed10m) \\cdot (TKor - TempSSurface)`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fluxes.tkor = -2.0, -1.0
        >>> fluxes.tempssurface = -5.0, 0.0
        >>> fluxes.windspeed10m = 3.0
        >>> from hydpy import round_
        >>> round_(model.return_wsenssnow_v1(0))
        -0.0864
        >>> round_(model.return_wsenssnow_v1(1))
        0.0288
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Turb0,
        lland_control.Turb1,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
        lland_fluxes.TempSSurface,
        lland_fluxes.WindSpeed10m,
    )

    @staticmethod
    def __call__(model: 'lland.Model', k: int) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return ((con.turb0+con.turb1*flu.windspeed10m) *
                (flu.tempssurface[k]-flu.tkor[k]))


class Return_WLatSnow_V1(modeltools.Method):
    """Calculate and return the latent heat flux of the snow surface.

    Basic equations:
      :math:`(Turb0 + Turb1 \\cdot WindSpeed10m) \\cdot
      \\beta \\cdot(ActualVapourPressureSnow - SaturationVapourPressureSnow))`

      :math:`\\beta = 17.6 °C/kpa`
      :math:`SaturationVapourPressureSnow = 0.6108 kPa`

    Example:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1h')
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fluxes.windspeed10m = 3.0
        >>> fluxes.actualvapourpressuresnow = 0.4, 0.8
        >>> from hydpy import round_
        >>> round_(model.return_wlatsnow_v1(0))
        -0.10685
        >>> round_(model.return_wlatsnow_v1(1))
        0.095902
        """
    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WindSpeed10m,
        lland_fluxes.ActualVapourPressureSnow,
    )

    @staticmethod
    def __call__(model: 'lland.Model', k: int) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return ((con.turb0+con.turb1*flu.windspeed10m) *
                17.6*(flu.actualvapourpressuresnow[k]-.6108))


class Return_WSurf_V1(modeltools.Method):
    """Calculate and return the snow surface heat flux.

    Basic equation:
      :math:`KTSchnee \\cdot (TempSSurface - TempS)`

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
    REQUIREDSEQUENCES = (
        lland_aides.TempS,
        lland_fluxes.TempSSurface,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WSurf,
    )

    @staticmethod
    def __call__(model: 'lland.Model', k: int) -> float:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        if modelutils.isinf(con.ktschnee):
            return modelutils.inf
        return con.ktschnee*(aid.temps[k]-flu.tempssurface[k])


class Return_EnergyGainSnowSurface_V1(modeltools.Method):
    """Calculate and return the net energy gain of the snow surface.

    As surface cannot store any energy, method |Return_EnergyGainSnowSurface_V1|
    returns zero if one supplies it with the correct temperature of the
    snow surface.  Hence, this methods provides a means to find this
    "correct" temperature via root finding algorithms.

    Basic equations:
      :math:`WSurf(TempSSurface) + NetRadiation(TempSSurface) -
      WSensSnow(TempSSurface) - WLatSnow(TempSSurface)`

      :math:`NetRadiation(TempSSurface) =
      NetshortwaveRadiation - NetlongwaveRadiation(TempSSurface)`

    Example:

        Method |Return_EnergyGainSnowSurface_V1| relies on multiple
        submethods with different requirements.  Hence, we first need to
        specify a lot of input data (see the documentation on the
        different submethods for further information):

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(1)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fratm(1.28)
        >>> ktschnee(0.432)
        >>> derived.seconds.update()
        >>> inputs.relativehumidity = 60.0
        >>> inputs.sunshineduration = 10.0
        >>> states.waes = 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiation = 2.0
        >>> fluxes.possiblesunshineduration = 12.0
        >>> aides.temps = -2.0

        Under the defined conditions and for a snow surface temperature of
        -4 °C, the net energy gain would be negative:

        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_energygainsnowsurface_v1(-4.0))
        -0.454395

        As a side-effect, method |Return_EnergyGainSnowSurface_V1| calculates
        the following flux sequences for the given snow surface temperature:

        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.453927)
        >>> fluxes.actualvapourpressuresnow
        actualvapourpressuresnow(0.272356)
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(8.126801)
        >>> fluxes.netradiation
        netradiation(-6.126801)
        >>> fluxes.wsenssnow
        wsenssnow(-0.6912)
        >>> fluxes.wlatsnow
        wlatsnow(-4.117207)
        >>> fluxes.wsurf
        wsurf(0.864)
    """
    SUBMETHODS = (
        Return_SaturationVapourPressure_V1,
        Return_ActualVapourPressure_V1,
        Return_WSensSnow_V1,
        Return_WLatSnow_V1,
        Return_WSurf_V1,
        Return_NetLongwaveRadiation_V1,
    )
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
    def __call__(model: 'lland.Model', tempssurface: float) -> float:
        flu = model.sequences.fluxes.fastaccess

        k = model.idx_hru
        flu.tempssurface[k] = tempssurface

        flu.saturationvapourpressuresnow[k] = \
            model.return_saturationvapourpressure_v1(flu.tempssurface[k])
        flu.actualvapourpressuresnow[k] = \
            model.return_actualvapourpressure_v1(
                flu.saturationvapourpressuresnow[k])
        flu.wlatsnow[k] = model.return_wlatsnow_v1(k)
        flu.wsenssnow[k] = model.return_wsenssnow_v1(k)
        flu.netlongwaveradiation[k] = model.return_netlongwaveradiation_v1(k)
        flu.netradiation[k] = \
            flu.netshortwaveradiation[k]-flu.netlongwaveradiation[k]
        flu.wsurf[k] = model.return_wsurf_v1(k)

        return flu.wsurf[k]+flu.netradiation[k]-flu.wsenssnow[k]-flu.wlatsnow[k]


class Return_TempSSurface_V1(modeltools.Method):
    """Determine and return the snow surface temperature.

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
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fratm(1.28)
        >>> ktschnee(0.432)
        >>> derived.seconds(24*60*60)
        >>> inputs.relativehumidity = 60.0
        >>> inputs.sunshineduration = 10.0
        >>> states.waes = 0.0, 1.0, 1.0, 1.0, 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.possiblesunshineduration = 12.0
        >>> fluxes.netshortwaveradiation = 1.0, 1.0, 2.0, 2.0, 2.0
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
        tempssurface(nan, -4.832608, -4.259254, -16.889144, -63.201335)

        As to be expected, the energy fluxes of the snow surface neutralise
        each other (within the defined numerical accuracy):

        >>> from hydpy import print_values
        >>> print_values(fluxes.netradiation -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, 0.0, 0.0, 0.0, 0.0

        Through setting parameter |KTSchnee| to |numpy.inf|, we disable
        the iterative search for the correct surface temperature.  Instead,
        method |Return_TempSSurface_V1| simply uses the bulk temperature of
        the snow layer as its surface temperature and sets |WSurf| so that
        the energy gain of the snow surface is zero::

        >>> ktschnee(inf)
        >>> for hru in range(5):
        ...     _ = model.return_tempssurface_v1(hru)
        >>> fluxes.tempssurface
        tempssurface(nan, -2.0, -2.0, -50.0, -200.0)
        >>> fluxes.wsurf
        wsurf(0.0, 5.008511, 4.008511, -47.307802, -163.038145)
        >>> print_values(fluxes.netradiation -
        ...              fluxes.wsenssnow -
        ...              fluxes.wlatsnow +
        ...              fluxes.wsurf)
        nan, -0.0, -0.0, 0.0, 0.0
    """
    CONTROLPARAMETERS = (
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.FrAtm,
        lland_control.KTSchnee,
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
    def __call__(model: 'lland.Model', k: int) -> float:
        aid = model.sequences.aides.fastaccess
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.waes[k] > 0.:
            if modelutils.isinf(con.ktschnee):
                model.idx_hru = k
                model.return_energygainsnowsurface_v1(aid.temps[k])
                flu.wsurf[k] = \
                    flu.wsenssnow[k]+flu.wlatsnow[k]-flu.netradiation[k]
            else:
                model.idx_hru = k
                model.pegasustempssurface.find_x(
                    -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10)
        else:
            flu.tempssurface[k] = modelutils.nan
            flu.saturationvapourpressuresnow[k] = 0.
            flu.actualvapourpressuresnow[k] = 0.
            flu.wsenssnow[k] = 0.
            flu.wlatsnow[k] = 0.
            flu.wsurf[k] = 0.
        return flu.tempssurface[k]


class Return_BackwardEulerError_V1(modeltools.Method):
    """Calculate and return the "Backward Euler error" regarding the
    update of |ESnow| due to the energy fluxes |WG| and |WSurf|.

    Basic equation:
      :math:`ESnow_{old} - ESnow_{new} + WG(ESnow_{new} ) - WSurf(ESnow_{new})`

    Method |Return_BackwardEulerError_V1| does not calculate any
    hydrologically meaningfull.  It is just a technical means to update
    the energy content of the snow layer with running into instability
    issues.  See the documentation on method |Update_ESnow_V2| for
    further information.

    Example:

        Method |Return_BackwardEulerError_V1| relies on multiple
        submethods with different requirements.  Hence, we first need to
        specify a lot of input data (see the documentation on the
        different submethods for further information):

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(1)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fratm(1.28)
        >>> derived.seconds.update()
        >>> inputs.relativehumidity = 60.0
        >>> inputs.sunshineduration = 10.0
        >>> states.waes = 12.0
        >>> states.wats = 10.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiation = 2.0
        >>> fluxes.possiblesunshineduration = 12.0
        >>> states.esnow = -0.1
        >>> fluxes.tz = 0.0

        Under the defined conditions the "correct" next value of |ESnow|,
        when following the Backward Euler Approach, is approximately
        -0.105 MJ/m²:

        >>> ktschnee(inf)
        >>> from hydpy import round_
        >>> model.idx_hru = 0
        >>> round_(model.return_backwardeulererror_v1(-0.10503956))
        -0.0

        As a side-effect, method |Return_BackwardEulerError_V1| calculates
        the following flux sequences for the given amount of energy:

        >>> aides.temps
        temps(-3.588201)
        >>> fluxes.tempssurface
        tempssurface(-3.588201)
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.468236)
        >>> fluxes.actualvapourpressuresnow
        actualvapourpressuresnow(0.280941)
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(8.284498)
        >>> fluxes.netradiation
        netradiation(-6.284498)
        >>> fluxes.wsenssnow
        wsenssnow(-0.406565)
        >>> fluxes.wlatsnow
        wlatsnow(-4.01277)
        >>> fluxes.wsurf
        wsurf(1.865163)
        >>> fluxes.wg
        wg(1.860123)

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
        and |TempS| differ and the energy amount of -0.105 MJ/m² is
        not correct anymore:

        >>> ktschnee(0.432)
        >>> round_(model.return_backwardeulererror_v1(-0.10503956))
        1.405507
        >>> aides.temps
        temps(-3.588201)
        >>> fluxes.tempssurface
        tempssurface(-4.652219)
        >>> fluxes.saturationvapourpressuresnow
        saturationvapourpressuresnow(0.432056)
        >>> fluxes.actualvapourpressuresnow
        actualvapourpressuresnow(0.259234)
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(7.878514)
        >>> fluxes.netradiation
        netradiation(-5.878514)
        >>> fluxes.wsenssnow
        wsenssnow(-1.142014)
        >>> fluxes.wlatsnow
        wlatsnow(-4.276844)
        >>> fluxes.wsurf
        wsurf(0.459656)
        >>> fluxes.wg
        wg(1.860123)
        >>> states.esnow
        esnow(-0.1)

        If there is no snow-cover, it makes little sense to call method
        |Return_BackwardEulerError_V1|.  For savety, we let it then
        return a |numpy.nan| value:

        >>> states.waes = 0.0
        >>> round_(model.return_backwardeulererror_v1(-0.10503956))
        nan
        >>> fluxes.wsurf
        wsurf(0.459656)
    """
    SUBMETHODS = (
        Return_TempS_V1,
        Return_WG_V1,
        Return_TempSSurface_V1,
    )
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
        lland_states.WATS,
        lland_fluxes.NetShortwaveRadiation,
        lland_fluxes.TKor,
        lland_fluxes.WindSpeed10m,
        lland_inputs.SunshineDuration,
        lland_fluxes.PossibleSunshineDuration,
        lland_logs.LoggedPossibleSunshineDuration,
        lland_logs.LoggedSunshineDuration,
        lland_fluxes.TZ,
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
    def __call__(model: 'lland.Model', esnow: float) -> float:
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        sta = model.sequences.states.fastaccess
        k = model.idx_hru
        if sta.waes[k] > 0.:
            d_esnow_old = sta.esnow[k]
            sta.esnow[k] = esnow
            aid.temps[k] = model.return_temps_v1(k)
            sta.esnow[k] = d_esnow_old
            model.return_tempssurface_v1(k)
            flu.wg[k] = model.return_wg_v1(k)
            return d_esnow_old-esnow+flu.wg[k]-flu.wsurf[k]
        return modelutils.nan


class Update_ESnow_V2(modeltools.Method):
    """Update the energy content of the snow layer with regard to the
    energy fluxes from the soil and the atmosphere (except the one related
    to the heat content of precipitation).

    Basic equation:
      :math:`\\frac{dESnow}{dt} = WG(ESnow(t)) - WSurf(ESnow(t))`

    For a thin snow cover, small absolute changes in its energy content
    result in extreme temperature changes, which makes the above calculation
    stiff.  Furthermore, the nonlinearity of the term :math:` WSurf(ESnow(t))`
    prevents from finding an analytical solution of the problem.  This
    is why we apply the A-stable Backward Euler method.  Through our
    simplified approach of taking only one variable (|ESnow|) into account,
    we can solve the underlying root finding problem without any need to
    calculate or approximate derivatives.  Speaking plainly, we use the
    Pegasus iterator |PegasusESnow| to find the root of method
    Method |Return_BackwardEulerError_V1| whenever the surface is snow-covered.

    Example:

        We reuse the configuration of the documentation on method
        |Return_BackwardEulerError_V1|, except that we prepare five
        hydrological response units:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> nhru(8)
        >>> turb0(0.1728)
        >>> turb1(0.1728)
        >>> fratm(1.28)
        >>> ktschnee(inf)
        >>> derived.seconds.update()
        >>> inputs.relativehumidity = 60.0
        >>> inputs.sunshineduration = 10.0
        >>> states.waes = 0.0, 120.0, 12.0, 1.2, 0.12, 0.012, 1.2e-6, 1.2e-12
        >>> states.wats = 0.0, 100.0, 12.0, 1.0, 0.10, 0.010, 1.0e-6, 1.0e-12
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.possiblesunshineduration = 12.0
        >>> fluxes.netshortwaveradiation = 2.0
        >>> states.esnow = -0.1
        >>> fluxes.tz = 0.0

        For the first, snow-free response unit, the energy content of the
        snow layer is zero.  For the other response units we see that the
        energy content decreases with decreasing snow thickness (This
        result is intuitively clear, but requires iteration in very different
        orders of magnitudes.  We hope, our implementation works always
        well.  Please tell us, if you encounter any cases where it does not):


        >>> model.update_esnow_v2()
        >>> states.esnow
        esnow(0.0, -0.92156, -0.090193, -0.010653, -0.001067, -0.000107, -0.0,
              -0.0)
        >>> aides.temps
        temps(nan, -3.148092, -3.596224, -3.639221, -3.644405, -3.644924,
              -3.644982, -3.644982)
        >>> fluxes.tempssurface
        tempssurface(nan, -3.148092, -3.596224, -3.639221, -3.644405, -3.644924,
                     -3.644982, -3.644982)

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
        >>> model.update_esnow_v2()
        >>> states.esnow
        esnow(0.0, -0.444773, -0.049844, -0.00597, -0.000599, -0.00006, -0.0,
              -0.0)
        >>> aides.temps
        temps(nan, -1.519365, -1.987383, -2.039381, -2.045747, -2.046385,
              -2.046456, -2.046456)
        >>> fluxes.tempssurface
        tempssurface(nan, -4.140689, -4.256139, -4.268976, -4.270547, -4.270705,
                     -4.270722, -4.270722)

        The resulting energy amounts are, again, the "correct" ones:

        >>> esnow = states.esnow.values.copy()
        >>> states.esnow = -0.1
        >>> errors = []
        >>> for hru in range(8):
        ...     model.idx_hru = hru
        ...     errors.append(model.return_backwardeulererror_v1(esnow[hru]))
        >>> print_values(errors)
        nan, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0
    """
    SUBMETHODS = (
        Return_ESnow_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Turb0,
        lland_control.Turb1,
        lland_control.FrAtm,
        lland_control.KTSchnee,
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
    def __call__(model: 'lland.Model') -> None:
        aid = model.sequences.aides.fastaccess
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                model.idx_hru = k
                sta.esnow[k] = model.pegasusesnow.find_x(
                    model.return_esnow_v1(k, -30.0),
                    model.return_esnow_v1(k, 100.0),
                    -100.0, 100.0, 0.0, 1e-8, 10)
            else:
                sta.esnow[k] = 0.
                aid.temps[k] = modelutils.nan
                flu.tempssurface[k] = modelutils.nan
                flu.saturationvapourpressuresnow[k] = 0.
                flu.actualvapourpressuresnow[k] = 0.
                flu.wsenssnow[k] = 0.
                flu.wlatsnow[k] = 0.
                flu.wsurf[k] = 0.


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation for snow-free land surfaces.

    Basic equation (`Allen`_, equation 40):
      :math:`NetRadiation = NetShortwaveRadiation - NetLongwaveRadiation`

    Example:

        For the first, snow-free hydrological response unit, the result agrees
        with example 12 of `Allen`_; for the second, snow-covered response
        unit, the original |NetRadiation| value remains unchanged:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fluxes.netshortwaveradiation = 11.1
        >>> fluxes.netlongwaveradiation = 3.5
        >>> fluxes.netradiation = 2.0
        >>> states.waes = 0.0, 1.0
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(7.6, 2.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    REQUIREDSEQUENCES = (
        lland_states.WAeS,
        lland_fluxes.NetShortwaveRadiation,
        lland_fluxes.NetLongwaveRadiation,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NetRadiation,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] <= 0.:
                flu.netradiation[k] = \
                    flu.netshortwaveradiation[k]-flu.netlongwaveradiation[k]


class Calc_SchmPot_V1(modeltools.Method):
    """Calculate the potential snow melt according to the day degree method.

    Basic equation:
      :math:`WMelt = max((WGTF + WNied, 0)/RSchmelz`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> fluxes.wgtf(2.0)
        >>> fluxes.wnied = 1.0, 2.0
        >>> model.calc_schmpot_v1()
        >>> fluxes.schmpot
        schmpot(8.982036, 11.976048)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    FIXEDPARAMETERS = (
        lland_fixed.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WGTF,
        lland_fluxes.WNied,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SchmPot,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.schmpot[k] = max((flu.wgtf[k]+flu.wnied[k])/fix.rschmelz, 0)


class Calc_SchmPot_V2(modeltools.Method):
    """Calculate the potential snow melt according to the heat content of the
    snow layer.

    Basic equations:
      :math:`SchmPot = max(ESnow/RSchmelz, 0)`

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    FIXEDPARAMETERS = (
        lland_fixed.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_states.ESnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SchmPot,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0.:
                flu.schmpot[k] = max(sta.esnow[k]/fix.rschmelz, 0)
            else:
                flu.schmpot[k] = 0.


class Calc_GefrPot_V1(modeltools.Method):
    """Calculate the potential refreezing within the snow layer according
    to the energy content of the snow layer.

    Basic equations:
      :math:`GefrPot = max(-ESnow/RSchmelz, 0)`

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    FIXEDPARAMETERS = (
        lland_fixed.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_states.ESnow,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.GefrPot,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0:
                flu.gefrpot[k] = max(-sta.esnow[k]/fix.rschmelz, 0)
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    """Update the actual water release from and the liquid water content of
    the snow layer due to melting.

    Basic equations:
      :math:`\\delta = Max(WAeS-PWMax \\cdot WATS, 0)'

      :math:`WaDa_{new} = WaDa_{old} + \\delta`

      :math:`WAeS_{new} = WAeS_{old} - \\delta`

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
    REQUIREDSEQUENCES = (
        lland_states.WATS,
    )
    UPDATEDSEQUENCES = (
        lland_states.WAeS,
        lland_fluxes.WaDa,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] not in (WASSER, FLUSS, SEE):
                d_wada_corr = max(sta.waes[k]-con.pwmax[k]*sta.wats[k], 0.)
                flu.wada[k] += d_wada_corr
                sta.waes[k] -= d_wada_corr


class Update_ESnow_V3(modeltools.Method):
    """Update the energy content of the snow layer regarding snow melt
    and refreezing.

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(4)
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
    )
    FIXEDPARAMETERS = (
        lland_fixed.RSchmelz,
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if sta.wats[k] > 0.:
                sta.esnow[k] -= flu.schm[k]*fix.rschmelz
                sta.esnow[k] += flu.gefr[k]*fix.rschmelz
            else:
                sta.esnow[k] = 0.


class Calc_SFF_V1(modeltools.Method):
    """Calculate the ratio between frozen water and total water within
    the top soil layer.

    Basic equations:
      :math:`SFF = Min(Max(1 - \\frac{EBdn}{BoWa2Z} \\cdot RSchmelz, 0), 1)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(9)
        >>> lnk(VERS, WASSER, FLUSS, SEE, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> bowa2z(80.0)
        >>> states.ebdn(0.0, 0.0, 0.0, 0.0, 28.0, 27.0, 10.0, 0.0, -1.0)
        >>> model.calc_sff_v1()
        >>> fluxes.sff
        sff(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.625749, 1.0, 1.0)
        """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.BoWa2Z,
    )
    FIXEDPARAMETERS = (
        lland_fixed.RSchmelz,
    )
    REQUIREDSEQUENCES = (
        lland_states.EBdn,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SFF,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.sff[k] = 0.
            elif sta.ebdn[k] < 0.:
                flu.sff[k] = 1.
            else:
                flu.sff[k] = \
                    max(1.-sta.ebdn[k]/(con.bowa2z[k]*fix.rschmelz), 0.)


class Calc_FVG_V1(modeltools.Method):
    """Calculate the degree of frost sealing of the soil.

    Basic equation:
      :math:`FVG = FVF \\cdot SFF^{BSFF})`

    Example:

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
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.BSFF,
        lland_control.FVF,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SFF,
    )
    RESULTSEQUENCES = (
        lland_fluxes.FVG,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                flu.fvg[k] = 0.
            else:
                flu.fvg[k] = con.fvf*flu.sff[k]**con.bsff


class Calc_EvB_V1(modeltools.Method):
    """Calculate the actual soil evapotranspiration.

    Basic equations:
      :math:`temp = exp(-GrasRef_R \\cdot \\frac{BoWa}{WMax})`

      :math:`EvB = (EvPo - EvI) \\cdot
      \\frac{1 - temp}{1 + temp -2 \\cdot exp(-GrasRef_R)}`

    Examples:

        Soil evapotranspiration is calculated neither for water nor for
        sealed areas (see the first three hydrological reponse units of
        type |FLUSS|, |SEE|, and |VERS|).  All other land use classes are
        handled in accordance with a recommendation of the set of codes
        described in `ATV-DVWK-M 504`_.  In case maximum soil water storage
        (|WMax|) is zero, soil evaporation (|EvB|) is generally set to zero
        (see the fourth hydrological response unit).  The last three response
        units demonstrate the rise in soil evaporation with increasing
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
    RESULTSEQUENCES = (
        lland_fluxes.EvB,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE) or con.wmax[k] <= 0.:
                flu.evb[k] = 0.
            else:
                d_temp = modelutils.exp(-con.grasref_r*sta.bowa[k]/con.wmax[k])
                flu.evb[k] = ((flu.evpo[k]-flu.evi[k])*(1.-d_temp) /
                              (1.+d_temp-2.*modelutils.exp(-con.grasref_r)))


class Calc_DryAirPressure_V1(modeltools.Method):
    """Calculate the pressure of the dry air.

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
    def __call__(model: 'lland.Model') -> None:
        inp = model.sequences.inputs.fastaccess
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.dryairpressure[k] = \
                inp.atmosphericpressure-flu.actualvapourpressure[k]


class Calc_DensityAir_V1(modeltools.Method):   # ToDo: WASSER Abfragen nicht vergessen
    """Calculate the density of the air.

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
    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    FIXEDPARAMETERS = (
        lland_fixed.RDryAir,
        lland_fixed.RWaterVapour,
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            d_t = flu.tkor[k]+273.15
            flu.densityair[k] = (
                flu.dryairpressure[k]/(fix.rdryair*d_t) +
                flu.actualvapourpressure[k]/(fix.rwatervapour*d_t))


class Calc_AerodynamicResistance_V1(modeltools.Method):
    """Calculate the aerodynamic resistance.

    Basic equations (z0 nach Quast und Boehm, 1997):

       :math:`z_0 = 0.021 + 0.163 \\cdot CropHeight`

       :math:`AerodynamicResistance = \\biggl \\lbrace
       {
       \\frac{6.25}{WindSpeed10m} \\cdot ln(\\frac{10}{z_0})^2 \\|\\ z_0 < 10
       \\atop
       \\frac{94}{WindSpeed10m} z_{0} \\|\\ z_0 \\geq 10
       }`

    Examples:

        Besides wind speed, aerodynamic resistance depends on the crop height,
        which typically varies between different land-use classes and, for
        vegetated surfaces, months.  In the first example, we set some
        different crop heights for different land-use types to cover the
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

        :math:`1.1404411695422059 = (10/\\exp(\\sqrt(94/6.25))-0.021)/0.163`

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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if flu.windspeed10m > 0.:
            for k in range(con.nhru):
                d_ch = con.cropheight[con.lnk[k]-1, der.moy[model.idx_sim]]
                if d_ch < 10.:
                    d_z0 = .021+.163*d_ch
                    flu.aerodynamicresistance[k] = \
                        6.25/flu.windspeed10m*modelutils.log(10./d_z0)**2
                else:
                    flu.aerodynamicresistance[k] = 94./flu.windspeed10m
        else:
            for k in range(con.nhru):
                flu.aerodynamicresistance[k] = modelutils.inf


class Calc_SoilSurfaceResistance_V1(modeltools.Method):
    """Calculate the surface resistance of the soil surface.

    Basic equation:
       :math:`SoilSurfaceResistance = \\biggl \\lbrace
       {
       100 \\|\\ NFk > 20
       \\atop
       100 \\cdot \\frac{NFk}{max(BoWa-PWP, 0) + NFk/100}
       \\|\\ NFk \\geq 20
       }`

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
    DERIVEDPARAMETERS = (
        lland_derived.NFk,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SoilSurfaceResistance,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, FLUSS, SEE, WASSER):
                flu.soilsurfaceresistance[k] = modelutils.nan
            elif der.nfk[k] > 20.:
                flu.soilsurfaceresistance[k] = 100.
            elif der.nfk[k] > 0.:
                d_free = min(max(sta.bowa[k]-con.pwp[k], 0.), der.nfk[k])
                flu.soilsurfaceresistance[k] = \
                    100.*der.nfk[k]/(d_free+.01*der.nfk[k])
            else:
                flu.soilsurfaceresistance[k] = modelutils.inf


class Calc_LanduseSurfaceResistance_V1(modeltools.Method):
    """Calculate the surface resistance of vegetation, water and sealed areas.

    Basic equation:

       :math:`LanduseSurfaceResistance = SurfaceResistance* \\cdot
       (3.5 \\cdot (1 - \\frac{min(BoWa, PWP)}{PWP}) +
       exp(\\frac{0.2 \\cdot PWP}{min(BoWa, 0)}))`

    Modification for coniferous trees:

       :math:`Deficit = SaturationVapourPressure - ActualVapourPressure`

       :math:`SurfaceResistance* = \\biggl \\lbrace
       {
       10'000 \\|\\ TKor \\leq PWP or Deficit \\geq 2
       \\atop
       min(\\frac{25 \\cdot SurfaceResistance}{(min(TKor, 20) + 5)
       \\cdot (1 - Deficit/2)}, 10'000) \\|\\ PWP < TKor < 20
       }`

    Example:

        Method |Calc_LanduseSurfaceResistance_V1| relies on multiple
        discontinuous relationships, works different for different
        types of land-use, and uses montly varying base parameters.
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
        value by a constant factor for wet soils (|BoWa| > |PWP) and
        increase it even more for dry soils (|BoWa| > |PWP).  For
        a completely dry soil, surface resistance becomes infinite:

        >>> lnk(ACKER)
        >>> pwp(0.0)
        >>> surfaceresistance.acker_jun = 40.0
        >>> states.bowa = 0.0, 10.0, 20.0, 30.0
        >>> model.idx_sim = 2
        >>> model.calc_landusesurfaceresistance_v1()
        >>> fluxes.landusesurfaceresistance
        landusesurfaceresistance(inf, 48.85611, 48.85611, 48.85611)

        >>> pwp(20.0)
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
        lland_fluxes.SoilSurfaceResistance,
    )
    RESULTSEQUENCES = (
        lland_fluxes.LanduseSurfaceResistance,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            d_res = con.surfaceresistance[con.lnk[k]-1, der.moy[model.idx_sim]]
            if con.lnk[k] == NADELW:
                d_def = \
                    flu.saturationvapourpressure[k]-flu.actualvapourpressure[k]
                if (flu.tkor[k] <= -5.) or (d_def >= 2.):
                    flu.landusesurfaceresistance[k] = 10000.
                elif flu.tkor[k] < 20.:
                    flu.landusesurfaceresistance[k] = min(
                        (25.*d_res)/(flu.tkor[k]+5.)/(1.-.5*d_def), 10000.)
                else:
                    flu.landusesurfaceresistance[k] = min(
                        d_res/(1.-.5*d_def), 10000.)
            else:
                flu.landusesurfaceresistance[k] = d_res
            if con.lnk[k] not in (WASSER, FLUSS, SEE, VERS):
                if sta.bowa[k] <= 0.:
                    flu.landusesurfaceresistance[k] = modelutils.inf
                elif sta.bowa[k] < con.pwp[k]:
                    flu.landusesurfaceresistance[k] *= (
                        3.5*(1.-sta.bowa[k]/con.pwp[k]) +
                        modelutils.exp(.2*con.pwp[k]/sta.bowa[k]))
                else:
                    flu.landusesurfaceresistance[k] *= modelutils.exp(.2)


class Calc_SurfaceResistance_V1(modeltools.Method):
    """Calculate the total surface resistance.

    Basic equations:
      :math:`SurfaceRestance_{day} = \\frac{1}
      {\\frac{1-0.7^{LAI}}{LanduseSurfaceResistance} +
      \\frac{0.7^{LAI}}{SoilSurfaceResistance}}`

      :math:`SurfaceRestance_{night} = \\frac{1}
      {\\frac{LAI}{2500} + \\frac{1}{LanduseSurfaceResistance}}`

      :math:`w = \\frac{PossibleSunshineDuration}{Seconds / 60 / 60}`

      :math:`Surfaceresistance = \\frac{1}
      {x \\cdot \\frac{1}{SurfaceRestance_{day}} +
      (1-x) \\cdot \\frac{1}{SurfaceRestance_{night}}}`

    Examples:

        For sealed surfaces and water areas, method |Calc_SurfaceResistance_V1|
        just the values of sequence |LanduseSurfaceResistance| as the
        effective surface resistance values:

        >>> from hydpy import pub
        >>> pub.timegrids = '2019-05-30', '2019-06-03', '1d'
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(VERS, FLUSS, SEE, WASSER)
        >>> derived.moy.update()
        >>> derived.seconds.update()
        >>> fluxes.soilsurfaceresistance = nan
        >>> fluxes.landusesurfaceresistance = 500.0, 0.0, 0.0, 0.0
        >>> model.idx_sim = 1
        >>> model.calc_surfaceresistance_v1()
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
        >>> model.calc_surfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(200.0, 132.450331, 109.174477, 101.43261)

        For a polar night, there is a leaf area index-dependend interpolation
        between soil surface resistance and a fixed resistance value:

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_surfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(200.0, 172.413793, 142.857143, 111.111111)

        For all days that are not polar nights or polar days, the values
        of the two examples above are weighted based on the possible
        sunshine duration of that day:

        >>> fluxes.possiblesunshineduration = 12.0
        >>> model.calc_surfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(200.0, 149.812734, 123.765057, 106.051498)

        The following examples demonstrate that method
        |Calc_SurfaceResistance_V1| works similar when applied on an
        hourly time basis during the daytime period (first example),
        during the nighttime (second example), and during dawn or
        dusk (third example):

        >>> pub.timegrids = '2019-05-31 22:00', '2019-06-01 03:00', '1h'
        >>> nhru(1)
        >>> lnk(NADELW)
        >>> fluxes.soilsurfaceresistance = 200.0
        >>> fluxes.landusesurfaceresistance = 100.0
        >>> derived.moy.update()
        >>> derived.seconds.update()
        >>> lai.nadelw_jun = 5.0
        >>> model.idx_sim = 2
        >>> fluxes.possiblesunshineduration = 1.0
        >>> model.calc_surfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(109.174477)

        >>> fluxes.possiblesunshineduration = 0.0
        >>> model.calc_surfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(142.857143)

        >>> fluxes.possiblesunshineduration = 0.5
        >>> model.calc_surfaceresistance_v1()
        >>> fluxes.actualsurfaceresistance
        actualsurfaceresistance(123.765057)

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
        lland_fluxes.SoilSurfaceResistance,
        lland_fluxes.LanduseSurfaceResistance,
        lland_fluxes.PossibleSunshineDuration,
    )

    RESULTSEQUENCES = (
        lland_fluxes.ActualSurfaceResistance,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_hours = der.seconds/60./60.
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, FLUSS, SEE, WASSER):
                flu.actualsurfaceresistance[k] = flu.landusesurfaceresistance[k]
            else:
                d_lai = con.lai[con.lnk[k]-1, der.moy[model.idx_sim]]
                d_invrestday = (
                    ((1.-.7**d_lai)/flu.landusesurfaceresistance[k]) +
                    .7**d_lai/flu.soilsurfaceresistance[k])
                d_invrestnight = \
                    d_lai/2500.+1./flu.soilsurfaceresistance[k]
                flu.actualsurfaceresistance[k] = (
                    1. /
                    (flu.possiblesunshineduration/d_hours*d_invrestday +
                     (1.-flu.possiblesunshineduration/d_hours)*d_invrestnight))


class Return_PenmanMonteith_V1(modeltools.Method):
    """Calculate and return the evapotranspiration according to Penman-Monteith.

    Basic equations:

    :math:`\\frac
    {SaturationVapourPressureSlope \\cdot (NetRadiation + WG) +
    Seconds \\cdot C \\cdot DensitiyAir \\cdot CPLuft \\cdot
    (SaturationVapourPressure - ActualVapourPressure) / AerodynamicResistance}
    {L \\cdot (SaturationVapourPressureSlope +
    PsychrometricConstant \\cdot
    C \\cdot (1 + SurfaceResistance/AerodynamicResistance))}`

    :math:`b' = 1 + 4 \\cdot Emissivity \\cdot Sigma \\cdot (273.15 + TKor)^3`

    :math:`C = 1 +
    \\frac{b' \\cdot AerodynamicResistance}{DensitiyAir \\cdot CPLuft}`

    Correction factor `C` takes the difference between measured temperature
    and actual surface temperature into account.

    Example:

        We build the following example on the first example of the
        documentation on method |Return_Penman_V1|.  The total available
        energy (|NetRadiation| plus |WG|) and the vapour saturation pressure
        deficit (|SaturationVapourPressure| minus |ActualVapourPressure|
        are identical.  To make the results roughly comparable, we use
        resistances suitable for water surfaces through setting
        |AerodynamicResistance| to zero and |ActualSurfaceResistance| to
        a reasonalbe precalculated value of 106 s/m:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> nhru(7)
        >>> emissivity(0.96)
        >>> derived.seconds.update()
        >>> fluxes.netradiation = 1.0, 4.5, 8.0, 1.0, 1.0, 1.0, 8.0
        >>> fluxes.wg = -1.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0
        >>> fluxes.densityair = 1.24
        >>> fluxes.psychrometricconstant = 0.07
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
        ...     print_values([fluxes.netradiation[hru]+fluxes.wg[hru],
        ...                   deficit,
        ...                   model.return_penmanmonteith_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.633733
        7.0, 0.0, 1.267465
        0.0, 0.0, 0.0
        0.0, 0.6, 1.959347
        0.0, 1.2, 3.918693
        7.0, 1.2, 5.186158

        Next, we repeat the above calculations using resistances relevant
        for vegetated surfaces (note that this also changes the results
        of the first three response units due to correction factor `C`
        depending on |AerodynamicResistance|):

        >>> fluxes.actualsurfaceresistance = 80.0
        >>> fluxes.aerodynamicresistance = 40.0
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([fluxes.netradiation[hru]+fluxes.wg[hru],
        ...                   deficit,
        ...                   model.return_penmanmonteith_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.3517
        7.0, 0.0, 0.703399
        0.0, 0.0, 0.0
        0.0, 0.6, 2.35049
        0.0, 1.2, 4.70098
        7.0, 1.2, 5.404379

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
        ...                   model.return_penmanmonteith_v1(hru)])
        0.0, 10.84584
        20.0, 8.664782
        50.0, 6.656796
        100.0, 4.802069
        200.0, 3.083698
        500.0, 1.487181
        1000.0, 0.798324

        Now we change the simulation time step from one day to one hour
        to demonstrate that we can reproduce the results of the first
        example, which only required to adjust |NetRadiation| and |WG|:

        >>> simulationstep('1h')
        >>> derived.seconds.update()
        >>> fixed.sigma.restore()
        >>> fluxes.netradiation = 1.0, 4.5, 8.0, 1.0, 1.0, 1.0, 8.0
        >>> fluxes.netradiation /= 24
        >>> fluxes.wg = -1.0/24
        >>> fluxes.actualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0
        >>> fluxes.actualsurfaceresistance = 0.0
        >>> fluxes.aerodynamicresistance = 106.0
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([24*(fluxes.netradiation[hru]+fluxes.wg[hru]),
        ...                   deficit,
        ...                   24*model.return_penmanmonteith_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.633733
        7.0, 0.0, 1.267465
        0.0, 0.0, 0.0
        0.0, 0.6, 1.959347
        0.0, 1.2, 3.918693
        7.0, 1.2, 5.186158
        """
    CONTROLPARAMETERS = (
        lland_control.Emissivity,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    FIXEDPARAMETERS = (
        lland_fixed.Sigma,
        lland_fixed.L,
        lland_fixed.CPLuft,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.WG,
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.DensityAir,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.ActualSurfaceResistance,
    )

    @staticmethod
    def __call__(model: 'lland.Model', k: int) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_b = 4.*con.emissivity*fix.sigma/der.seconds*(273.15+flu.tkor[k])**3
        d_c = 1.+d_b*flu.aerodynamicresistance[k]/flu.densityair[k]/fix.cpluft
        return (
            (flu.saturationvapourpressureslope[k] *
             (flu.netradiation[k]+flu.wg[k]) +
             der.seconds*flu.densityair[k]*fix.cpluft *
             (flu.saturationvapourpressure[k]-flu.actualvapourpressure[k]) *
             d_c/flu.aerodynamicresistance[k]) /
            (flu.saturationvapourpressureslope[k] +
             flu.psychrometricconstant*d_c *
             (1.+flu.actualsurfaceresistance[k]/flu.aerodynamicresistance[k])) /
            fix.l)


class Return_Penman_V1(modeltools.Method):
    """Calculate and return the evaporation from water surfaces according to
    Penman.

    Basic equation:
      :math:`\\frac{SaturationVapourPressureSlope \\cdot \\frac{NetRadiation}{L}
      + \\PsychrometricConstant \\cdot (1.3 + 0.94 \\cdot WindSpeed2m) \\cdot
      (SaturationVapourPressure-ActualVapourPressure)}
      {SaturationVapourPressureSlope + PsychrometricConstant}`

    Examples:

        We initialise seven hydrological response units.  In reponse units
        one to three, evaporation is due to radiative forcing only.  In
        response units four to six, evaporation is due to aerodynamic forcing
        only.  Response unit seven shows the combined effect of both forces:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(7)
        >>> derived.seconds(24*60*60)
        >>> fluxes.netradiation = 0.0, 3.5, 7.0, 0.0, 0.0, 0.0, 7.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0
        >>> fluxes.psychrometricconstant = 0.07
        >>> fluxes.windspeed2m = 2.0
        >>> from hydpy import print_values
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([fluxes.netradiation[hru],
        ...                   deficit,
        ...                   model.return_penman_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.758068
        7.0, 0.0, 1.516136
        0.0, 0.0, 0.0
        0.0, 0.6, 0.8904
        0.0, 1.2, 1.7808
        7.0, 1.2, 3.296936
        
        The above results apply for a daily simulation time step.  The
        following example demonstrates that, after adjusting the total
        amount of energy available via sequence |NetRadiation|, we get
        equivalent results for hourly time steps:

        >>> derived.seconds(60*60)
        >>> fluxes.netradiation /= 24
        >>> for hru in range(7):
        ...     deficit = (fluxes.saturationvapourpressure[hru] -
        ...                fluxes.actualvapourpressure[hru])
        ...     print_values([24*fluxes.netradiation[hru],
        ...                   deficit,
        ...                   24*model.return_penman_v1(hru)])
        0.0, 0.0, 0.0
        3.5, 0.0, 0.758068
        7.0, 0.0, 1.516136
        0.0, 0.0, 0.0
        0.0, 0.6, 0.8904
        0.0, 1.2, 1.7808
        7.0, 1.2, 3.296936
        """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    DERIVEDPARAMETERS = (
        lland_derived.Seconds,
    )
    FIXEDPARAMETERS = (
        lland_fixed.L,
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
    def __call__(model: 'lland.Model', k: int) -> float:
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        return (
            (flu.saturationvapourpressureslope[k]*flu.netradiation[k]/fix.l +
             flu.psychrometricconstant*(1.3+.94*flu.windspeed2m) *
             (flu.saturationvapourpressure[k]-flu.actualvapourpressure[k]) /
             (24*60*60)*der.seconds) /
            (flu.saturationvapourpressureslope[k]+flu.psychrometricconstant))


class Calc_EvPo_V3(modeltools.Method):
    """Calculate the potential evaporation according to Penman.

    At the moment, method |Calc_EvPo_V3| just applies method
    |Return_Penman_V1| on all hydrological response units, irregardless
    if they represent water areas or not.  This might change in the future.

    Example:

        For the first seven hydrological response units, the following
        results agree with the results discussed in the documentation
        on method |Return_Penman_V1|.  The eights response unit demonstrates
        that method |Calc_EvPo_V3| trims negative evaporation to zero and
        thus generally prevents condensation:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(8)
        >>> derived.seconds(24*60*60)
        >>> fluxes.netradiation = 0.0, 3.5, 7.0, 0.0, 0.0, 0.0, 7.0, -1.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 1.2, 1.2, 1.2, 1.2, 0.6, 0.0, 0.0, 1.2
        >>> fluxes.psychrometricconstant = 0.07
        >>> fluxes.windspeed2m = 2.0
        >>> model.calc_evpo_v3()
        >>> fluxes.evpo
        evpo(0.0, 0.758068, 1.516136, 0.0, 0.8904, 1.7808, 3.296936, 0.0)
    """
    SUBMETHODS = (
        Return_Penman_V1,
    )
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.evpo[k] = max(model.return_penman_v1(k), 0.)


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
        evposnow(0.0, -0.812216, 0.406108, 1.624431, 2.436647)
        >>> states.waes
        waes(0.0, 5.812216, 4.593892, 3.375569, 2.563353)
        >>> states.wats
        wats(0.0, 4.0, 4.0, 3.375569, 2.563353)
    """

    CONTROLPARAMETERS = (
        lland_control.NHRU,
    )
    FIXEDPARAMETERS = (
        lland_fixed.L,
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if sta.waes[k] > 0:
                flu.evposnow[k] = flu.wlatsnow[k]/fix.l
                sta.waes[k] -= flu.evposnow[k]
                sta.waes[k] = max(sta.waes[k], 0)
                sta.wats[k] = min(sta.waes[k], sta.wats[k])
            else:
                flu.evposnow[k] = 0.


class Calc_EvI_Inzp_V1(modeltools.Method):
    """Calculate interception evaporation and update the interception
    storage accordingly.

    Basic equation:
      :math:`EvI = \\Bigl \\lbrace
      {
      {EvPo \\ | \\ Inzp > 0}
      \\atop
      {0 \\ | \\ Inzp = 0}
      }`

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
    REQUIREDSEQUENCES = (
        lland_fluxes.EvPo,
    )
    UPDATEDSEQUENCES = (
        lland_states.Inzp,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvI,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.evi[k] = flu.evpo[k]
                sta.inzp[k] = 0.
            else:
                flu.evi[k] = min(flu.evpo[k], sta.inzp[k])
                sta.inzp[k] -= flu.evi[k]


class Calc_EvI_Inzp_V2(modeltools.Method):
    """Calculate interception evaporation and update the interception
    storage accordingly for snow-free surfaces.

    Method |Calc_EvI_Inzp_V2| works exactly like method |Calc_EvI_Inzp_V1|,
    except that it sets |EvI| to zero for all snow-covered surfaces.

    Examples:

        For snow-free land surfaces (see the first two hydrological
        response units), there is no difference to the results discussed
        in the documentation on method |Calc_EvI_Inzp_V1|.  For snow-covered
        surfaces, there is no interception evaporation and thus no change
        in interception storage (see the third response unit):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> states.inzp = 2.0, 4.0, 4.0
        >>> fluxes.evpo = 3.0
        >>> states.waes = 0.0, 0.0, 1.0
        >>> model.calc_evi_inzp_v2()
        >>> states.inzp
        inzp(0.0, 1.0, 4.0)
        >>> fluxes.evi
        evi(2.0, 3.0, 0.0)

        For water areas, where we do not model any snow processes, there
        is no difference to the results of method |Calc_EvI_Inzp_V1|:

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
    REQUIREDSEQUENCES = (
        lland_states.WAeS,
        lland_fluxes.EvPo,
    )
    UPDATEDSEQUENCES = (
        lland_states.Inzp,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvI,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.evi[k] = flu.evpo[k]
                sta.inzp[k] = 0.
            elif sta.waes[k] > 0.:
                flu.evi[k] = 0.
            else:
                flu.evi[k] = min(flu.evpo[k], sta.inzp[k])
                sta.inzp[k] -= flu.evi[k]


class Calc_EvB_V2(modeltools.Method):
    """Calculate the actual evapotranspiration from the soil.

    :math:`EvB = \\frac{EvPo - EvI}{EvPo}  \\cdot EvB_{Penman-Monteith}`

    Example:

        For sealed surfaces, water areas and snow-covered hydrological
        response units, there is no soil evaporation:

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
        soil evaporation to the (prioritised) interception evaporation
        in accordance with the base equation defined above.  Additionally,
        the first and the last response unit show that method |Calc_EvPo_V3|
        sets |EvB| to zero when |EvPo| is zero or when the original soil
        evapotranspiration value calculated by |Return_PenmanMonteith_V1|
        is negative:

        >>> lnk(NADELW)
        >>> states.waes = 0.0
        >>> emissivity(0.96)
        >>> derived.seconds.update()
        >>> fluxes.netradiation = 8.0, 8.0, 8.0, 8.0, 8.0, -30.0
        >>> fluxes.wg = -1.0
        >>> fluxes.saturationvapourpressure = 1.2
        >>> fluxes.saturationvapourpressureslope = 0.08
        >>> fluxes.actualvapourpressure = 0.0
        >>> fluxes.densityair = 1.24
        >>> fluxes.psychrometricconstant = 0.07
        >>> fluxes.actualsurfaceresistance = 0.0
        >>> fluxes.aerodynamicresistance = 106.0
        >>> fluxes.tkor = 10.0
        >>> fluxes.evpo = 0.0, 6.0, 6.0, 6.0, 6.0, 6.0
        >>> fluxes.evi = 0.0, 0.0, 2.0, 4.0, 6.0, 3.0
        >>> model.calc_evb_v2()
        >>> fluxes.evb
        evb(0.0, 5.186158, 3.457439, 1.728719, 0.0, 0.0)
    """
    SUBMETHODS = (
        Return_PenmanMonteith_V1,
    )
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.Emissivity,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NetRadiation,
        lland_fluxes.WG,
        lland_fluxes.TKor,
        lland_fluxes.SaturationVapourPressureSlope,
        lland_fluxes.SaturationVapourPressure,
        lland_fluxes.ActualVapourPressure,
        lland_fluxes.PsychrometricConstant,
        lland_fluxes.DensityAir,
        lland_fluxes.AerodynamicResistance,
        lland_fluxes.ActualSurfaceResistance,
        lland_fluxes.EvPo,
        lland_fluxes.EvI,
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvB,
    )

    @staticmethod
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.waes[k] > 0.) or (flu.evpo[k] <= 0.)):
                flu.evb[k] = 0.
            else:
                d_evb = model.return_penmanmonteith_v1(k)
                if d_evb < 0.:
                    flu.evb[k] = 0.
                else:
                    flu.evb[k] = (flu.evpo[k]-flu.evi[k])/flu.evpo[k]*d_evb


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
    def __call__(model: 'lland.Model') -> None:
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
        time we activate the flag |CorrQBBFlag|:

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
    def __call__(model: 'lland.Model') -> None:
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
                    flu.qbb[k] = con.beta[k]*(sta.bowa[k]-con.pwp[k])
            else:
                flu.qbb[k] = (
                    (con.beta[k]*(sta.bowa[k]-con.pwp[k]) *
                     (1.+(con.fbeta[k]-1.) *
                      ((sta.bowa[k]-con.fk[k])/(con.wmax[k]-con.fk[k]))))
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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

        >>> fluxes.qkap   # ToDo
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                sta.bowa[k] = 0.
            else:
                d_bvl = \
                    flu.evb[k]+flu.qbb[k]+flu.qib1[k]+flu.qib2[k]+flu.qdb[k]
                d_mvl = sta.bowa[k]+flu.wada[k]+flu.qkap[k]
                if d_bvl > d_mvl:
                    if con.corrqbbflag[k] and flu.qbb[k] > 0.:
                        d_delta = min(d_bvl-d_mvl, flu.qbb[k])
                        flu.qbb[k] -= d_delta
                        d_bvl = (flu.evb[k]+flu.qbb[k]+flu.qib1[k] +
                                 flu.qib2[k]+flu.qdb[k])
                        d_mvl = sta.bowa[k]+flu.wada[k]+flu.qkap[k]
                        if d_bvl > d_mvl:
                            sta.bowa[k] = d_mvl-d_bvl
                    d_rvl = d_mvl/d_bvl
                    if flu.evb[k] > 0:
                        flu.evb[k] *= d_rvl
                    flu.qbb[k] *= d_rvl
                    flu.qib1[k] *= d_rvl
                    flu.qib2[k] *= d_rvl
                    flu.qdb[k] *= d_rvl
                    sta.bowa[k] = 0.
                else:
                    sta.bowa[k] = d_mvl-d_bvl
                    if con.corrqbbflag[k] and (sta.bowa[k] < con.fk[k]):
                        if flu.qbb[k] > 0.:
                            d_delta = min(con.fk[k]-sta.bowa[k], flu.qbb[k])
                            flu.qbb[k] -= d_delta
                            sta.bowa[k] += d_delta
                    elif sta.bowa[k] > con.fk[k]:
                        if flu.qkap[k] > 0.:
                            d_delta = min(sta.bowa[k]-con.fk[k], flu.qkap[k])
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
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
    def __call__(model: 'lland.Model') -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.q = sta.qbga + sta.qiga1+sta.qiga2+sta.qdga1+sta.qdga2
        if (not con.negq) and (flu.q < 0.):
            d_area = 0.
            for k in range(con.nhru):
                if con.lnk[k] in (FLUSS, SEE):
                    d_area += con.fhru[k]
            if d_area > 0.:
                for k in range(con.nhru):
                    if con.lnk[k] in (FLUSS, SEE):
                        flu.evi[k] += flu.q/d_area
            flu.q = 0.
        aid.epw = 0.
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.q += con.fhru[k]*flu.nkor[k]
                aid.epw += con.fhru[k]*flu.evi[k]
        if (flu.q > aid.epw) or con.negq:
            flu.q -= aid.epw
        elif aid.epw > 0.:
            for k in range(con.nhru):
                if con.lnk[k] == WASSER:
                    flu.evi[k] *= flu.q/aid.epw
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
    def __call__(model: 'lland.Model') -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += der.qfactor * flu.q


class PegasusESnow(roottools.Pegasus):
    """Pegasus iterator for finding the correct snow energy content."""
    METHODS = (
        Return_BackwardEulerError_V1,
    )


class PegasusTempSSurface(roottools.Pegasus):
    """Pegasus iterator for finding the correct snow surface temperature."""
    METHODS = (
        Return_EnergyGainSnowSurface_V1,
    )


class Model(modeltools.AdHocModel):
    """Base model for HydPy-L-Land."""
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        Return_AdjustedWindSpeed_V1,
        Return_ActualVapourPressure_V1,
        Return_NetLongwaveRadiation_V1,
        Return_Penman_V1,
        Return_PenmanMonteith_V1,
        Return_EnergyGainSnowSurface_V1,
        Return_SaturationVapourPressure_V1,
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
        Calc_NetLongwaveRadiation_V1,
        Calc_NetShortwaveRadiation_V1,
        Calc_NetRadiation_V1,
        Calc_DryAirPressure_V1,
        Calc_DensityAir_V1,
        Calc_AerodynamicResistance_V1,
        Calc_SoilSurfaceResistance_V1,
        Calc_LanduseSurfaceResistance_V1,
        Calc_SurfaceResistance_V1,
        Calc_EvPo_V3,
        Calc_EvI_Inzp_V1,
        Calc_EvI_Inzp_V2,
        Calc_EvB_V1,
        Calc_EvB_V2,
        Update_EBdn_V1,
        Update_ESnow_V2,
        Calc_SchmPot_V1,
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
        PegasusESnow,
        PegasusTempSSurface,
    )
    INDICES = (
        'idx_sim',
        'idx_hru',
    )
