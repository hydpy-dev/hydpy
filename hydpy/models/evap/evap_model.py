# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import petinterfaces
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_derived
from hydpy.models.evap import evap_inputs
from hydpy.models.evap import evap_factors
from hydpy.models.evap import evap_fluxes
from hydpy.models.evap import evap_logs


class Calc_AdjustedAirTemperature_V1(modeltools.Method):
    """Adjust the average air temperature to the (heights) of the individual
    hydrological response units.

    Basic equation:
      :math:`AdjustedAirTemperature = AirTemperatureAddend + AirTemperature`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> airtemperatureaddend(-2.0, 0.0, 2.0)
        >>> inputs.airtemperature(1.0)
        >>> model.calc_adjustedairtemperature_v1()
        >>> factors.adjustedairtemperature
        adjustedairtemperature(-1.0, 1.0, 3.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.AirTemperatureAddend,
    )
    REQUIREDSEQUENCES = (evap_inputs.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.AdjustedAirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.adjustedairtemperature[k] = (
                con.airtemperatureaddend[k] + inp.airtemperature
            )


class Calc_AdjustedWindSpeed_V1(modeltools.Method):
    r"""Adjust the measured wind speed to a height of two meters above the ground
    according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 47, modified for higher
    precision):

      .. math::
        AdjustedWindSpeed = WindSpeed \cdot
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
    r"""Calculate the saturation vapour pressure according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 11):
      :math:`SaturationVapourPressure = 6.108 \cdot \exp \left(
      \frac{17.27 \cdot AdjustedAirTemperature}{AdjustedAirTemperature + 237.3}\right)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.adjustedairtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> factors.saturationvapourpressure
        saturationvapourpressure(12.279626)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.AdjustedAirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressure[k] = 6.108 * modelutils.exp(
                17.27
                * fac.adjustedairtemperature[k]
                / (fac.adjustedairtemperature[k] + 237.3)
            )


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    r"""Calculate the slope of the saturation vapour pressure curve according to
    :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 13):
      :math:`SaturationVapourPressureSlope = 4098 \cdot
      \frac{SaturationVapourPressure}{(AdjustedAirTemperature + 237.3)^2}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.adjustedairtemperature = 10.0
        >>> factors.saturationvapourpressure = 12.279626
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> factors.saturationvapourpressureslope
        saturationvapourpressureslope(0.822828)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_factors.AdjustedAirTemperature,
        evap_factors.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressureslope[k] = (
                4098.0
                * fac.saturationvapourpressure[k]
                / (fac.adjustedairtemperature[k] + 237.3) ** 2
            )


class Calc_ActualVapourPressure_V1(modeltools.Method):
    r"""Calculate the actual vapour pressure according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 19, modified):
      :math:`ActualVapourPressure = SaturationVapourPressure \cdot
      RelativeHumidity / 100`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> inputs.relativehumidity = 60.0
        >>> factors.saturationvapourpressure = 30.0
        >>> model.calc_actualvapourpressure_v1()
        >>> factors.actualvapourpressure
        actualvapourpressure(18.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_inputs.RelativeHumidity,
        evap_factors.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.ActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.actualvapourpressure[k] = (
                fac.saturationvapourpressure[k] * inp.relativehumidity / 100.0
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
    r"""Calculate the net shortwave radiation for the hypothetical grass reference
    crop according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 38):
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
    r"""Calculate the net longwave radiation according to :cite:t:`ref-Allen1998`.

    Basic equations (:cite:t:`ref-Allen1998`, equation 39, modified):
      :math:`NetLongwaveRadiation =
      \sigma \cdot (AdjustedAirTemperature + 273.16)^4
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
    radiation and clear sky radiation sums of the last 24 hours.  Averaging over three
    hours before sunset, as :cite:t:`ref-Allen1998` suggests, could be more precise but
    is a more complicated and error-prone approach.

    Example:

        The following calculation agrees with example 11 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> derived.nmblogentries(1)
        >>> inputs.globalradiation = 167.824074
        >>> inputs.clearskysolarradiation = 217.592593
        >>> factors.adjustedairtemperature = 22.1
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

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        evap_inputs.ClearSkySolarRadiation,
        evap_inputs.GlobalRadiation,
        evap_factors.AdjustedAirTemperature,
        evap_factors.ActualVapourPressure,
        evap_logs.LoggedGlobalRadiation,
        evap_logs.LoggedClearSkySolarRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
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
        for k in range(con.nmbhru):
            flu.netlongwaveradiation[k] = (
                5.674768518518519e-08
                * (fac.adjustedairtemperature[k] + 273.16) ** 4
                * (0.34 - 0.14 * (fac.actualvapourpressure[k] / 10.0) ** 0.5)
                * (1.35 * d_globalradiation / d_clearskysolarradiation - 0.35)
            )


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 40):
      :math:`NetRadiation = NetShortwaveRadiation - NetLongwaveRadiation`

    Example:

        The following calculation agrees with example 12 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> fluxes.netshortwaveradiation  = 111.0
        >>> fluxes.netlongwaveradiation  = 35.0
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(76.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_fluxes.NetShortwaveRadiation,
        evap_fluxes.NetLongwaveRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.netradiation[k] = (
                flu.netshortwaveradiation - flu.netlongwaveradiation[k]
            )


class Calc_SoilHeatFlux_V1(modeltools.Method):
    r"""Calculate the soil heat flux according to :cite:t:`ref-Allen1998`.

    Basic equation for daily timesteps (:cite:t:`ref-Allen1998`, equation 42):
      :math:`SoilHeatFlux = 0` \n

    Basic equation for (sub)hourly timesteps (:cite:t:`ref-Allen1998`, eq. 45 and 46 ):
      :math:`SoilHeatFlux = \Bigl \lbrace
      {
      {0.1 \cdot SoilHeatFlux \ | \ NetRadiation \geq 0}
      \atop
      {0.5 \cdot SoilHeatFlux \ | \ NetRadiation < 0}
      }`

    Examples:

        For simulation time steps shorter than one day, we define all steps with
        positive |NetRadiation| as part of the daylight period and all with negative
        |NetRadiation| as part of the nighttime period.  The total |SoilHeatFlux| is
        zero if the summed |NetRadiation| during daytime is five times as high as the
        absolute summed |NetRadiation| during nighttime:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
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
        sets the |SoilHeatFlux| to zero, which :cite:t:`ref-Allen1998` suggests for
        daily simulation steps only:

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

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.Days,)
    REQUIREDSEQUENCES = (evap_fluxes.NetRadiation,)
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if der.days < 1.0:
            for k in range(con.nmbhru):
                if flu.netradiation[k] >= 0.0:
                    flu.soilheatflux[k] = 0.1 * flu.netradiation[k]
                else:
                    flu.soilheatflux[k] = 0.5 * flu.netradiation[k]
        else:
            for k in range(con.nmbhru):
                flu.soilheatflux[k] = 0.0


class Calc_PsychrometricConstant_V1(modeltools.Method):
    r"""Calculate the psychrometric constant according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 8):
      :math:`PsychrometricConstant = 6.65 \cdot 10^{-4} \cdot AtmosphericPressure`

    Example:

        The following calculation agrees with example 2 of :cite:t:`ref-Allen1998`:

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
    r"""Calculate the reference evapotranspiration constant according to
    :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 6):
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

    Note that :cite:t:`ref-Allen1998` recommends the coefficient 37 for hourly
    simulations and 900 for daily simulations.  |Calc_ReferenceEvapotranspiration_V1|
    generally uses 37.5, which gives 900 when multiplied by 24.

    Example:

        The following calculation agrees with example 18 of :cite:t:`ref-Allen1998`,
        dealing with a daily simulation step:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> derived.days(1)
        >>> derived.hours(24)
        >>> factors.psychrometricconstant = 0.666
        >>> factors.adjustedairtemperature = 16.9
        >>> factors.adjustedwindspeed = 2.078
        >>> factors.actualvapourpressure = 14.09
        >>> factors.saturationvapourpressure = 19.97
        >>> factors.saturationvapourpressureslope = 1.22
        >>> fluxes.netradiation = 153.7037
        >>> fluxes.soilheatflux = 0.0
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.877117)

        The following calculation agrees with example 19 of :cite:t:`ref-Allen1998`,
        dealing with an hourly simulation step (note that there is a  difference due to
        using 37.5 instead of 37, which is smaller than the precision of the results
        tabulated by :cite:t:`ref-Allen1998`:

        >>> derived.days(1/24)
        >>> derived.hours(1)
        >>> factors.psychrometricconstant = 0.673
        >>> factors.adjustedairtemperature = 38.0
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

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (
        evap_derived.Days,
        evap_derived.Hours,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.PsychrometricConstant,
        evap_factors.AdjustedAirTemperature,
        evap_factors.AdjustedWindSpeed,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = (
                0.0352512
                * der.days
                * fac.saturationvapourpressureslope[k]
                * (flu.netradiation[k] - flu.soilheatflux[k])
                + (fac.psychrometricconstant * 3.75 * der.hours)
                / (fac.adjustedairtemperature[k] + 273.0)
                * fac.adjustedwindspeed
                * (fac.saturationvapourpressure[k] - fac.actualvapourpressure[k])
            ) / (
                fac.saturationvapourpressureslope[k]
                + fac.psychrometricconstant * (1.0 + 0.34 * fac.adjustedwindspeed)
            )


class Calc_ReferenceEvapotranspiration_V2(modeltools.Method):
    r"""Calculate reference evapotranspiration after Turc-Wendling.

    Basic equation:
      :math:`ReferenceEvapotranspiration =
      \frac{(8.64 \cdot GlobalRadiation + 93 \cdot CoastFactor) \cdot
      (AdjustedAirTemperature + 22)}
      {165 \cdot (AdjustedAirTemperature + 123) \cdot
      (1 + 0.00019 \cdot min(Altitude, 600))}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> coastfactor(0.6)
        >>> altitude(200.0, 600.0, 1000.0)
        >>> inputs.globalradiation = 200.0
        >>> factors.adjustedairtemperature = 15.0
        >>> model.calc_referenceevapotranspiration_v2()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.792463, 2.601954, 2.601954)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Altitude,
        evap_control.CoastFactor,
    )
    REQUIREDSEQUENCES = (
        evap_inputs.GlobalRadiation,
        evap_factors.AdjustedAirTemperature,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = (
                (8.64 * inp.globalradiation + 93.0 * con.coastfactor[k])
                * (fac.adjustedairtemperature[k] + 22.0)
            ) / (
                165.0
                * (fac.adjustedairtemperature[k] + 123.0)
                * (1.0 + 0.00019 * min(con.altitude[k], 600.0))
            )


class Calc_ReferenceEvapotranspiration_V3(modeltools.Method):
    r"""Take the input reference evapotranspiration for each hydrological response
    unit.

    Basic equation:
      :math:`ReferenceEvapotranspiration_{fluxes} =
      ReferenceEvapotranspiration_{inputs}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> inputs.referenceevapotranspiration = 2.0
        >>> model.calc_referenceevapotranspiration_v3()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.0, 2.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_inputs.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = inp.referenceevapotranspiration


class Adjust_ReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Adjust the previously calculated reference evapotranspiration.

    Basic equation:
      :math:`ReferenceEvapotranspiration_{new} = EvapotranspirationFactor \cdot
      ReferenceEvapotranspiration_{old}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> evapotranspirationfactor(0.5, 2.0)
        >>> fluxes.referenceevapotranspiration = 2.0
        >>> model.adjust_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(1.0, 4.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.EvapotranspirationFactor,
    )
    UPDATEDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] *= con.evapotranspirationfactor[k]


class Calc_MeanReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the average reference evapotranspiration.

    Basic equation:
      :math:`MeanReferenceEvapotranspiration =
      \sum_{i=1}^{NmbHRU} HRUAreaFraction_i \cdot ReferenceEvapotranspiration_i`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.hruareafraction(0.8, 0.2)
        >>> fluxes.referenceevapotranspiration = 1.0, 2.0
        >>> model.calc_meanreferenceevapotranspiration_v1()
        >>> fluxes.meanreferenceevapotranspiration
        meanreferenceevapotranspiration(1.2)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.HRUAreaFraction,)
    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.MeanReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.meanreferenceevapotranspiration = 0.0
        for s in range(con.nmbhru):
            flu.meanreferenceevapotranspiration += (
                der.hruareafraction[s] * flu.referenceevapotranspiration[s]
            )


class Determine_PotentialEvapotranspiration_V1(modeltools.Method):
    r"""Interface method that applies the complete application model by executing all
    "run methods"."""

    @staticmethod
    def __call__(model: modeltools.AdHocModel) -> None:
        model.run()


class Get_PotentialEvapotranspiration_V1(modeltools.Method):
    """Get the current reference evapotranspiration from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.referenceevapotranspiration = 2.0, 4.0
        >>> model.get_potentialevapotranspiration_v1(0)
        2.0
        >>> model.get_potentialevapotranspiration_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.referenceevapotranspiration[s]


class Get_MeanPotentialEvapotranspiration_V1(modeltools.Method):
    """Get the averaged reference evapotranspiration.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.meanreferenceevapotranspiration = 3.0
        >>> model.get_meanpotentialevapotranspiration_v1()
        3.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.MeanReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.meanreferenceevapotranspiration


class Model(
    modeltools.AdHocModel,
):
    """The HydPy-Evap base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_AdjustedAirTemperature_V1,
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
        Calc_ReferenceEvapotranspiration_V2,
        Calc_ReferenceEvapotranspiration_V3,
        Adjust_ReferenceEvapotranspiration_V1,
        Calc_MeanReferenceEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        Determine_PotentialEvapotranspiration_V1,
        Get_PotentialEvapotranspiration_V1,
        Get_MeanPotentialEvapotranspiration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class Base_PETModel_V1(modeltools.AdHocModel, petinterfaces.PETModel_V1):
    """Base class for HydPy-Evap models that comply with the |PETModel_V1| submodel
    interface."""

    @importtools.define_targetparameter(evap_control.NmbHRU)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of hydrological response units.

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> nmbhru
        nmbhru(2)
        """
        self.parameters.control.nmbhru(nmbzones)

    @importtools.define_targetparameter(evap_control.HRUArea)
    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the area of all hydrological response units in km².

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_subareas([1.0, 3.0])
        >>> hruarea
        hruarea(1.0, 3.0)
        """
        self.parameters.control.hruarea(subareas)

    @importtools.define_targetparameter(evap_control.Altitude)
    def prepare_elevations(self, elevations: Sequence[float]) -> None:
        """Set the altitude of all hydrological response units in m.

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_elevations([1.0, 3.0])
        >>> altitude
        altitude(1.0, 3.0)
        """
        self.parameters.control.altitude(elevations)
