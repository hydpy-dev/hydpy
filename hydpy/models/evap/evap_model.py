# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_derived
from hydpy.models.evap import evap_inputs
from hydpy.models.evap import evap_factors
from hydpy.models.evap import evap_fluxes
from hydpy.models.evap import evap_logs


class Calc_AdjustedWindSpeed_V1(modeltools.Method):
    r"""Adjust the measured wind speed to a height of two meters above the ground.

    Basic equation (:cite:`ref-Allen1998` equation 47, modified for higher precision):
      :math:`AdjustedWindSpeed = WindSpeed \cdot
      \frac{ln((2-d)/z_0)}{ln((MeasuringHeightWindSpeed-d)/z_0)}`

      :math:`d = 2 / 3 \cdot 0.12`

      :math:`z_0 = 0.123 \cdot 0.12`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_adjustedwindspeed_v1()
        >>> factors.adjustedwindspeed
        adjustedwindspeed(3.738763)
    """

    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)
    RESULTSEQUENCES = (evap_factors.AdjustedWindSpeed,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        d_d = 2.0 / 3.0 * 0.12
        d_z0 = 0.123 * 0.12
        fac.adjustedwindspeed = inp.windspeed * (
            modelutils.log((2.0 - d_d) / d_z0)
            / modelutils.log((con.measuringheightwindspeed - d_d) / d_z0)
        )


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    r"""Calculate the saturation vapour pressure.

    Basic equation (:cite:`ref-Allen1998`, equation 11):
      :math:`SaturationVapourPressure = 0.6108 \cdot
      \exp \left( \frac{17.27 \cdot AirTemperature}{AirTemperature + 237.3} \right)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.airtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> factors.saturationvapourpressure
        saturationvapourpressure(1.227963)
    """

    REQUIREDSEQUENCES = (evap_inputs.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.saturationvapourpressure = 0.6108 * modelutils.exp(
            17.27 * inp.airtemperature / (inp.airtemperature + 237.3)
        )


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    r"""Calculate the slope of the saturation vapour pressure curve.

    Basic equation (:cite:`ref-Allen1998`, equation 13):
      :math:`SaturationVapourPressureSlope = 4098 \cdot
      \frac{SaturationVapourPressure}{(AirTemperature + 237.3)^2}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.airtemperature = 10.0
        >>> factors.saturationvapourpressure = 1.227963
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> factors.saturationvapourpressureslope
        saturationvapourpressureslope(0.082283)
    """

    REQUIREDSEQUENCES = (
        evap_inputs.AirTemperature,
        evap_factors.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.saturationvapourpressureslope = (
            4098.0 * fac.saturationvapourpressure / (inp.airtemperature + 237.3) ** 2
        )


class Calc_ActualVapourPressure_V1(modeltools.Method):
    r"""Calculate the actual vapour pressure.

    Basic equation (:cite:`ref-Allen1998`, equation 19, modified):
      :math:`ActualVapourPressure = SaturationVapourPressure \cdot
      RelativeHumidity / 100`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.relativehumidity = 60.0
        >>> factors.saturationvapourpressure = 3.0
        >>> model.calc_actualvapourpressure_v1()
        >>> factors.actualvapourpressure
        actualvapourpressure(1.8)
    """

    REQUIREDSEQUENCES = (
        evap_inputs.RelativeHumidity,
        evap_factors.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.ActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.actualvapourpressure = (
            fac.saturationvapourpressure * inp.relativehumidity / 100.0
        )


class Update_LoggedClearSkySolarRadiation_V1(modeltools.Method):
    """Log the clear sky solar radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorized values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedclearskysolarradiation.shape = 3
        >>> logs.loggedclearskysolarradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedclearskysolarradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.clearskysolarradiation,
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
    REQUIREDSEQUENCES = (evap_inputs.ClearSkySolarRadiation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedclearskysolarradiation[idx] = log.loggedclearskysolarradiation[
                idx - 1
            ]
        log.loggedclearskysolarradiation[0] = inp.clearskysolarradiation


class Update_LoggedGlobalRadiation_V1(modeltools.Method):
    """Log the global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorized values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.evap import *
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

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_inputs.GlobalRadiation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedglobalradiation[idx] = log.loggedglobalradiation[idx - 1]
        log.loggedglobalradiation[0] = inp.globalradiation


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net shortwave radiation for the hypothetical grass reference crop.

    Basic equation (:cite:`ref-Allen1998`, equation 38):
      :math:`NetShortwaveRadiation = (1.0 - 0.23) \cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.globalradiation = 20.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(15.4)
    """

    REQUIREDSEQUENCES = (evap_inputs.GlobalRadiation,)
    RESULTSEQUENCES = (evap_fluxes.NetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.netshortwaveradiation = (1.0 - 0.23) * inp.globalradiation


class Calc_NetLongwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net longwave radiation.

    Basic equations (:cite:`ref-Allen1998`, equation 39, modified):
      :math:`NetLongwaveRadiation =
      \sigma \cdot Seconds \cdot (AirTemperature+273.16)^4
      \cdot (0.34 - 0.14 \sqrt{ActualVapourPressure}) \cdot
      (1.35 \cdot GR / CSSR - 0.35)`

      .. math::
        GR =
        \begin{cases}
        GlobalRadiation &|\ ClearSkySolarRadiation > 0
        \\
        \sum{LoggedGlobalRadiation} &|\ ClearSkySolarRadiation = 0
        \end{cases}

      .. math::
        CSSR =
        \begin{cases}
        ClearSkySolarRadiation &|\ ClearSkySolarRadiation > 0
        \\
        \sum{LoggedClearSkySolarRadiation} &|\ ClearSkySolarRadiation = 0
        \end{cases}

      :math:`\sigma = 5.6747685185185184 \cdot 10^{-14}`

    Note that when clear sky radiation is zero during night periods, we use the global
    radiation and clear sky radiation sums of the last 24 hours.  The averaging over
    three hours before sunset suggested by  :cite:`ref-Allen1998` could be more precise
    but is a more complicated and error-prone approach.

    Example:

        The following calculation agrees with example 11 of :cite:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(60*60*24)
        >>> derived.nmblogentries(1)
        >>> inputs.airtemperature = 22.1
        >>> inputs.globalradiation = 14.5
        >>> inputs.clearskysolarradiation = 18.8
        >>> factors.actualvapourpressure = 2.1
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(3.531847)

        >>> inputs.clearskysolarradiation = 0.0
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
        evap_inputs.ClearSkySolarRadiation,
        evap_inputs.GlobalRadiation,
        evap_factors.ActualVapourPressure,
        evap_logs.LoggedGlobalRadiation,
        evap_logs.LoggedClearSkySolarRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        if inp.clearskysolarradiation > 0.0:
            d_globalradiation = inp.globalradiation
            d_clearskysolarradiation = inp.clearskysolarradiation
        else:
            d_globalradiation = 0.0
            d_clearskysolarradiation = 0.0
            for idx in range(der.nmblogentries):
                d_clearskysolarradiation += log.loggedclearskysolarradiation[idx]
                d_globalradiation += log.loggedglobalradiation[idx]
        flu.netlongwaveradiation = (
            (4.903e-9 / 24.0 / 60.0 / 60.0 * der.seconds)
            * (inp.airtemperature + 273.16) ** 4
            * (0.34 - 0.14 * fac.actualvapourpressure**0.5)
            * (1.35 * d_globalradiation / d_clearskysolarradiation - 0.35)
        )


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation.

    Basic equation (:cite:`ref-Allen1998`, equation 40):
      :math:`NetRadiation = NetShortwaveRadiation - NetLongwaveRadiation`

    Example:

        The following calculation agrees with example 12 of :cite:`ref-Allen1998`:

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
    r"""Calculate the soil heat flux.

    Basic equation for daily timesteps (:cite:`ref-Allen1998`, equation 42):
      :math:`SoilHeatFlux = 0` \n

    Basic equation for (sub)hourly timesteps (:cite:`ref-Allen1998`, eq. 45 and 46 ):
      :math:`SoilHeatFlux = \Bigl \lbrace
      {
      {0.1 \cdot SoilHeatFlux \ | \ NetRadiation \geq 0}
      \atop
      {0.5 \cdot SoilHeatFlux \ | \ NetRadiation < 0}
      }`

    Examples:

        For simulation time steps shorter one day, we define all steps with positive
        |NetRadiation| as part of the daylight period and all steps with negative
        |NetRadiation| as part of the nighttime period.  If the summed |NetRadiation|
        during daytime is five times as high as the absolute summed |NetRadiation|
        during nighttime, the total |SoilHeatFlux| is zero:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(60 * 60)
        >>> fluxes.netradiation = 10.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(1.0)
        >>> fluxes.netradiation = -2.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(-1.0)

        For any simulation step size of at least one day, method |Calc_SoilHeatFlux_V1|
        sets the |SoilHeatFlux| to zero, which :cite:`ref-Allen1998` suggests for daily
        simulation steps only:

        >>> derived.seconds(60 * 60 * 24)
        >>> fluxes.netradiation = 10.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)
        >>> fluxes.netradiation = -2.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)

        Hence, be aware that function |Calc_SoilHeatFlux_V1| does not give the best
        results for intermediate (e.g. 12 hours) or larger step sizes (e.g. one month).
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
    r"""Calculate the psychrometric constant.

    Basic equation (:cite:`ref-Allen1998`, equation 8):
      :math:`PsychrometricConstant = 6.65 \cdot 10^{-4} \cdot AtmosphericPressure`

    Example:

        The following calculation agrees with example 2 of :cite:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.atmosphericpressure = 81.8
        >>> model.calc_psychrometricconstant_v1()
        >>> factors.psychrometricconstant
        psychrometricconstant(0.054397)
    """

    REQUIREDSEQUENCES = (evap_inputs.AtmosphericPressure,)
    RESULTSEQUENCES = (evap_factors.PsychrometricConstant,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.psychrometricconstant = 6.65e-4 * inp.atmosphericpressure


class Calc_ReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the reference evapotranspiration constant.

    Basic equation (:cite:`ref-Allen1998`, equation 6):
      :math:`ReferenceEvapotranspiration =
      \frac{
      0.408 \cdot SaturationVapourPressureSlope \cdot (NetRadiation - SoilHeatFlux) +
      PsychrometricConstant \cdot
      \frac{37.5 \cdot Seconds}{60 \cdot 60 \cdot (AirTemperature + 273)}
      \cdot AdjustedWindSpeed \cdot (SaturationVapourPressure - ActualVapourPressure)
      }
      {
      SaturationVapourPressureSlope +
      PsychrometricConstant \cdot (1 + 0.34 \cdot AdjustedWindSpeed)
      }`

    Note that :cite:`ref-Allen1998` recommends the coefficient 37 for hourly
    simulations and 900 for daily simulations.  |Calc_ReferenceEvapotranspiration_V1|
    generally uses 37.5, which gives 900 when multiplied by 24.

    Example:

        The following calculation agrees with example 18 of :cite:`ref-Allen1998`,
        dealing with a daily simulation step:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.seconds(24*60*60)
        >>> inputs.airtemperature = 16.9
        >>> factors.psychrometricconstant = 0.0666
        >>> factors.adjustedwindspeed = 2.078
        >>> factors.actualvapourpressure = 1.409
        >>> factors.saturationvapourpressure = 1.997
        >>> factors.saturationvapourpressureslope = 0.122
        >>> fluxes.netradiation = 13.28
        >>> fluxes.soilheatflux = 0.0
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.877117)

        The following calculation agrees with example 19 of :cite:`ref-Allen1998`,
        dealing with an hourly simulation step (note that there is a  difference due to
        using 37.5 instead of 37 that is smaller than the precision of the results
        tabulated by :cite:`ref-Allen1998`:

        >>> derived.seconds(60*60)
        >>> inputs.airtemperature = 38.0
        >>> factors.psychrometricconstant = 0.0673
        >>> factors.adjustedwindspeed = 3.3
        >>> factors.actualvapourpressure = 3.445
        >>> factors.saturationvapourpressure = 6.625
        >>> factors.saturationvapourpressureslope = 0.358
        >>> fluxes.netradiation = 1.749
        >>> fluxes.soilheatflux = 0.175
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(0.629106)
    """

    DERIVEDPARAMETERS = (evap_derived.Seconds,)
    REQUIREDSEQUENCES = (
        evap_inputs.AirTemperature,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.PsychrometricConstant,
        evap_factors.AdjustedWindSpeed,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.referenceevapotranspiration = (
            0.408
            * fac.saturationvapourpressureslope
            * (flu.netradiation - flu.soilheatflux)
            + fac.psychrometricconstant
            * (37.5 / 60.0 / 60.0 * der.seconds)
            / (inp.airtemperature + 273.0)
            * fac.adjustedwindspeed
            * (fac.saturationvapourpressure - fac.actualvapourpressure)
        ) / (
            fac.saturationvapourpressureslope
            + fac.psychrometricconstant * (1.0 + 0.34 * fac.adjustedwindspeed)
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
        Update_LoggedClearSkySolarRadiation_V1,
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
