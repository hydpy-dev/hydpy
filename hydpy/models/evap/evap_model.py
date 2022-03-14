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
      :math:`SaturationVapourPressure = 6.108 \cdot
      \exp \left( \frac{17.27 \cdot AirTemperature}{AirTemperature + 237.3} \right)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.airtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> factors.saturationvapourpressure
        saturationvapourpressure(12.279626)
    """

    REQUIREDSEQUENCES = (evap_inputs.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.saturationvapourpressure = 6.108 * modelutils.exp(
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
        >>> factors.saturationvapourpressure = 12.279626
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> factors.saturationvapourpressureslope
        saturationvapourpressureslope(0.822828)
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
        >>> factors.saturationvapourpressure = 30.0
        >>> model.calc_actualvapourpressure_v1()
        >>> factors.actualvapourpressure
        actualvapourpressure(18.0)
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
        >>> inputs.globalradiation = 200.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(154.0)
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
      \sigma \cdot (AirTemperature + 273.16)^4
      \cdot \left( 0.34 - 0.14 \sqrt{ActualVapourPressure / 10} \right) \cdot
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

      :math:`\sigma = 5.6747685185185184 \cdot 10^{-8}`

    Note that when clear sky radiation is zero during night periods, we use the global
    radiation and clear sky radiation sums of the last 24 hours.  The averaging over
    three hours before sunset suggested by  :cite:`ref-Allen1998` could be more precise
    but is a more complicated and error-prone approach.

    Example:

        The following calculation agrees with example 11 of :cite:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(1)
        >>> inputs.airtemperature = 22.1
        >>> inputs.globalradiation = 167.824074
        >>> inputs.clearskysolarradiation = 217.592593
        >>> factors.actualvapourpressure = 21.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(40.87786)

        >>> inputs.clearskysolarradiation = 0.0
        >>> logs.loggedclearskysolarradiation.shape = 1
        >>> logs.loggedclearskysolarradiation = 138.888889
        >>> logs.loggedglobalradiation.shape = 1
        >>> logs.loggedglobalradiation = 115.740741
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(45.832275)
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
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
            5.674768518518519e-08
            * (inp.airtemperature + 273.16) ** 4
            * (0.34 - 0.14 * (fac.actualvapourpressure / 10.0) ** 0.5)
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
        >>> fluxes.netshortwaveradiation  = 111.0
        >>> fluxes.netlongwaveradiation  = 35.0
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(76.0)
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
        >>> derived.days(1/24)
        >>> fluxes.netradiation = 100.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(10.0)
        >>> fluxes.netradiation = -20.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(-10.0)

        For any simulation step size of at least one day, method |Calc_SoilHeatFlux_V1|
        sets the |SoilHeatFlux| to zero, which :cite:`ref-Allen1998` suggests for daily
        simulation steps only:

        >>> derived.days(1)
        >>> fluxes.netradiation = 100.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)
        >>> fluxes.netradiation = -20.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)

        Hence, be aware that function |Calc_SoilHeatFlux_V1| does not give the best
        results for intermediate (e.g. 12 hours) or larger step sizes (e.g. one month).
    """

    DERIVEDPARAMETERS = (evap_derived.Days,)
    REQUIREDSEQUENCES = (evap_fluxes.NetRadiation,)
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if der.days < 1.0:
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
        >>> inputs.atmosphericpressure = 818.0
        >>> model.calc_psychrometricconstant_v1()
        >>> factors.psychrometricconstant
        psychrometricconstant(0.54397)
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
      \frac{37.5 \cdot Hours}{AirTemperature + 273}
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
        >>> derived.days(1)
        >>> derived.hours(24)
        >>> inputs.airtemperature = 16.9
        >>> factors.psychrometricconstant = 0.666
        >>> factors.adjustedwindspeed = 2.078
        >>> factors.actualvapourpressure = 14.09
        >>> factors.saturationvapourpressure = 19.97
        >>> factors.saturationvapourpressureslope = 1.22
        >>> fluxes.netradiation = 153.7037
        >>> fluxes.soilheatflux = 0.0
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.877117)

        The following calculation agrees with example 19 of :cite:`ref-Allen1998`,
        dealing with an hourly simulation step (note that there is a  difference due to
        using 37.5 instead of 37 that is smaller than the precision of the results
        tabulated by :cite:`ref-Allen1998`:

        >>> derived.days(1/24)
        >>> derived.hours(1)
        >>> inputs.airtemperature = 38.0
        >>> factors.psychrometricconstant = 0.673
        >>> factors.adjustedwindspeed = 3.3
        >>> factors.actualvapourpressure = 34.45
        >>> factors.saturationvapourpressure = 66.25
        >>> factors.saturationvapourpressureslope = 3.58
        >>> fluxes.netradiation = 485.8333
        >>> fluxes.soilheatflux = 48.6111
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(0.629106)
    """

    DERIVEDPARAMETERS = (
        evap_derived.Days,
        evap_derived.Hours,
    )
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
            0.0352512
            * der.days
            * fac.saturationvapourpressureslope
            * (flu.netradiation - flu.soilheatflux)
            + (fac.psychrometricconstant * 3.75 * der.hours)
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
