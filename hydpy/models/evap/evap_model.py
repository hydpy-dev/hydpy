# -*- coding: utf-8 -*-
"""
.. _`issue 118`: https://github.com/hydpy-dev/hydpy/issues/118
"""
# imports...
# ...from standard library
import contextlib

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import radiationinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_parameters
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_derived
from hydpy.models.evap import evap_fixed
from hydpy.models.evap import evap_sequences
from hydpy.models.evap import evap_inputs
from hydpy.models.evap import evap_factors
from hydpy.models.evap import evap_fluxes
from hydpy.models.evap import evap_logs
from hydpy.models.evap import evap_states


class Calc_AirTemperature_TempModel_V1(modeltools.Method):
    """Query hydrological response units' air temperature from a main model referenced
    as a sub-submodel and follows the |TempModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |evap_ret_tw2002| as an example:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> fc(100.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     pass
        >>> factors.tc = 2.0, 0.0, 5.0
        >>> model.aetmodel.calc_airtemperature_v1()
        >>> model.aetmodel.sequences.factors.airtemperature
        airtemperature(2.0, 0.0, 5.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.AirTemperature,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: tempinterfaces.TempModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.airtemperature[k] = submodel.get_temperature(k)


class Calc_AirTemperature_TempModel_V2(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V2| interface determine the air
    temperature of the hydrological response units.

    Example:

        We use the combination of |evap_ret_tw2002| and |meteo_temp_io| as an example:

        >>> from hydpy.models.evap_ret_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     temperatureaddend(1.0, 2.0, 4.0)
        ...     inputs.temperature = 2.0
        >>> model.calc_airtemperature_v1()
        >>> factors.airtemperature
        airtemperature(3.0, 4.0, 6.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.AirTemperature,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: tempinterfaces.TempModel_V2
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        submodel.determine_temperature()
        for k in range(con.nmbhru):
            fac.airtemperature[k] = submodel.get_temperature(k)


class Calc_AirTemperature_V1(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V1| or |TempModel_V2| interface
    determine the air temperature of the individual hydrological response units."""

    SUBMODELINTERFACES = (tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2)
    SUBMETHODS = (Calc_AirTemperature_TempModel_V1, Calc_AirTemperature_TempModel_V2)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.AirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.tempmodel_typeid == 1:
            model.calc_airtemperature_tempmodel_v1(
                cast(tempinterfaces.TempModel_V1, model.tempmodel)
            )
        elif model.tempmodel_typeid == 2:
            model.calc_airtemperature_tempmodel_v2(
                cast(tempinterfaces.TempModel_V2, model.tempmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Update_LoggedAirTemperature_V1(modeltools.Method):
    """Log the air temperature values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        six memorised values to the right and stores the two respective new values on
        the leftmost position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedairtemperature.shape = 3, 2
        >>> logs.loggedairtemperature = 0.0, 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedairtemperature_v1,
        ...                 last_example=4,
        ...                 parseqs=(factors.airtemperature,
        ...                          logs.loggedairtemperature))
        >>> test.nexts.airtemperature = [1.0, 2.0], [3.0, 6.0], [2.0, 4.0], [4.0, 8.0]
        >>> del test.inits.loggedairtemperature
        >>> test()
        | ex. |      airtemperature |                          loggedairtemperature |
        -----------------------------------------------------------------------------
        |   1 | 1.0             2.0 | 1.0  2.0  0.0  0.0  0.0                   0.0 |
        |   2 | 3.0             6.0 | 3.0  6.0  1.0  2.0  0.0                   0.0 |
        |   3 | 2.0             4.0 | 2.0  4.0  3.0  6.0  1.0                   2.0 |
        |   4 | 4.0             8.0 | 4.0  8.0  2.0  4.0  3.0                   6.0 |
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_factors.AirTemperature,)
    UPDATEDSEQUENCES = (evap_logs.LoggedAirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            for k in range(con.nmbhru):
                log.loggedairtemperature[idx, k] = log.loggedairtemperature[idx - 1, k]
        for k in range(con.nmbhru):
            log.loggedairtemperature[0, k] = fac.airtemperature[k]


class Calc_DailyAirTemperature_V1(modeltools.Method):
    """Calculate the average air temperature of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedairtemperature.shape = 3, 2
        >>> logs.loggedairtemperature = [[1.0, 2.0], [5.0, 6.0], [3.0, 4.0]]
        >>> model.calc_dailyairtemperature_v1()
        >>> factors.dailyairtemperature
        dailyairtemperature(3.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedAirTemperature,)
    RESULTSEQUENCES = (evap_factors.DailyAirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.dailyairtemperature[k] = 0.0
        for idx in range(der.nmblogentries):
            for k in range(con.nmbhru):
                fac.dailyairtemperature[k] += log.loggedairtemperature[idx, k]
        for k in range(con.nmbhru):
            fac.dailyairtemperature[k] /= der.nmblogentries


class Calc_MeanAirTemperature_TempModel_V1(modeltools.Method):
    """Query mean air temperature from a main model referenced as a sub-submodel and
    follows the |TempModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |evap_pet_hbv96| as an example:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> fc(200.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     with model.add_petmodel_v1("evap_pet_hbv96"):
        ...         pass
        >>> inputs.t = 2.0
        >>> model.aetmodel.petmodel.calc_meanairtemperature_v1()
        >>> model.aetmodel.petmodel.sequences.factors.meanairtemperature
        meanairtemperature(2.0)
    """

    RESULTSEQUENCES = (evap_factors.MeanAirTemperature,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: tempinterfaces.TempModel_V1
    ) -> None:
        fac = model.sequences.factors.fastaccess
        fac.meanairtemperature = submodel.get_meantemperature()


class Calc_MeanAirTemperature_TempModel_V2(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V2| interface determine the
    mean air temperature.

    Example:

        We use the combination of |evap_pet_hbv96| and |meteo_temp_io| as an example:

        >>> from hydpy.models.evap_pet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     temperatureaddend(1.0, 2.0, 4.0)
        ...     inputs.temperature = 2.0
        >>> model.calc_meanairtemperature_v1()
        >>> factors.meanairtemperature
        meanairtemperature(3.9)
    """

    RESULTSEQUENCES = (evap_factors.MeanAirTemperature,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: tempinterfaces.TempModel_V2
    ) -> None:
        fac = model.sequences.factors.fastaccess
        submodel.determine_temperature()
        fac.meanairtemperature = submodel.get_meantemperature()


class Calc_MeanAirTemperature_V1(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V1| or |TempModel_V2| interface
    determine the air temperature."""

    SUBMODELINTERFACES = (tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2)
    SUBMETHODS = (
        Calc_MeanAirTemperature_TempModel_V1,
        Calc_MeanAirTemperature_TempModel_V2,
    )
    RESULTSEQUENCES = (evap_factors.MeanAirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.tempmodel_typeid == 1:
            model.calc_meanairtemperature_tempmodel_v1(
                cast(tempinterfaces.TempModel_V1, model.tempmodel)
            )
        elif model.tempmodel_typeid == 2:
            model.calc_meanairtemperature_tempmodel_v2(
                cast(tempinterfaces.TempModel_V2, model.tempmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_WindSpeed2m_V1(modeltools.Method):
    r"""Adjust the measured wind speed to a height of two meters above the ground
    following :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 47, modified for higher
    precision):

      .. math::
        WindSpeed2m = WindSpeed \cdot
        \frac{ln((2 - d) / z_0)}{ln((MeasuringHeightWindSpeed - d) / z_0)}
        \\ \\
        d = 2 / 3 \cdot 0.12 \\
        z_0 = 0.123 \cdot 0.12

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed2m_v1()
        >>> factors.windspeed2m
        windspeed2m(3.738763)
    """

    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)
    RESULTSEQUENCES = (evap_factors.WindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        d: float = 2.0 / 3.0 * 0.12
        z0: float = 0.123 * 0.12
        fac.windspeed2m = inp.windspeed * (
            modelutils.log((2.0 - d) / z0)
            / modelutils.log((con.measuringheightwindspeed - d) / z0)
        )


class Return_AdjustedWindSpeed_V1(modeltools.Method):
    r"""Adjust and return the measured wind speed to the defined height above the
    ground using the logarithmic wind profile.

    Basic equation:
      .. math::
        v_1 = v_0 \cdot \frac{ln(h_1 / z_0)}{ln(h_0 / z_0)}
        \\ \\
        v_1 = wind \ speed \ at \ h_1 \\
        h_1 = given \ height \\
        z_0 = RoughnessLengthGrass \\
        v_0 = WindSpeed \ (at \ h_0) \\
        h_0 = MeasuringHeightWindSpeed

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> from hydpy import round_
        >>> round_(model.return_adjustedwindspeed_v1(2.0))
        4.007956
        >>> round_(model.return_adjustedwindspeed_v1(0.5))
        3.153456
    """

    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (evap_fixed.RoughnessLengthGrass,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)

    @staticmethod
    def __call__(model: modeltools.Model, h: float) -> float:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        inp = model.sequences.inputs.fastaccess
        if h == con.measuringheightwindspeed:
            return inp.windspeed
        return inp.windspeed * (
            modelutils.log(h / fix.roughnesslengthgrass)
            / modelutils.log(con.measuringheightwindspeed / fix.roughnesslengthgrass)
        )


class Calc_WindSpeed2m_V2(modeltools.Method):
    """Adjust the measured wind speed to a height of 2 meters above the ground
    following :cite:t:`ref-LARSIM`.

    Method |Calc_WindSpeed2m_V2| relies on method |Return_AdjustedWindSpeed_V1|.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed2m_v2()
        >>> factors.windspeed2m
        windspeed2m(4.007956)
    """

    SUBMETHODS = (Return_AdjustedWindSpeed_V1,)
    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (evap_fixed.RoughnessLengthGrass,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)
    RESULTSEQUENCES = (evap_factors.WindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.windspeed2m = model.return_adjustedwindspeed_v1(2.0)


class Update_LoggedWindSpeed2m_V1(modeltools.Method):
    """Log the wind speed values 2 meters above the ground of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        leftmost position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedwindspeed2m.shape = 3
        >>> logs.loggedwindspeed2m = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedwindspeed2m_v1,
        ...                 last_example=4,
        ...                 parseqs=(factors.windspeed2m,
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

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_factors.WindSpeed2m,)
    UPDATEDSEQUENCES = (evap_logs.LoggedWindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedwindspeed2m[idx] = log.loggedwindspeed2m[idx - 1]
        log.loggedwindspeed2m[0] = fac.windspeed2m


class Calc_DailyWindSpeed2m_V1(modeltools.Method):
    """Calculate the average wind speed 2 meters above ground of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedwindspeed2m.shape = 3
        >>> logs.loggedwindspeed2m = 1.0, 5.0, 3.0
        >>> model.calc_dailywindspeed2m_v1()
        >>> factors.dailywindspeed2m
        dailywindspeed2m(3.0)
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedWindSpeed2m,)
    RESULTSEQUENCES = (evap_factors.DailyWindSpeed2m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.dailywindspeed2m = 0.0
        for idx in range(der.nmblogentries):
            fac.dailywindspeed2m += log.loggedwindspeed2m[idx]
        fac.dailywindspeed2m /= der.nmblogentries


class Calc_WindSpeed10m_V1(modeltools.Method):
    """Adjust the measured wind speed to a height of 10 meters above the ground
    following :cite:t:`ref-LARSIM`.

    Method |Calc_WindSpeed2m_V2| relies on method |Return_AdjustedWindSpeed_V1|.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> measuringheightwindspeed(3.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_windspeed10m_v1()
        >>> factors.windspeed10m
        windspeed10m(5.871465)
    """

    SUBMETHODS = (Return_AdjustedWindSpeed_V1,)
    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    FIXEDPARAMETERS = (evap_fixed.RoughnessLengthGrass,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)
    RESULTSEQUENCES = (evap_factors.WindSpeed10m,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.windspeed10m = model.return_adjustedwindspeed_v1(10.0)


class Update_LoggedRelativeHumidity_V1(modeltools.Method):
    """Log the relative humidity values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the new value on the leftmost
        position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedrelativehumidity.shape = 3
        >>> logs.loggedrelativehumidity = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedrelativehumidity_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.relativehumidity,
        ...                          logs.loggedrelativehumidity))
        >>> test.nexts.relativehumidity = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedrelativehumidity
        >>> test()
        | ex. | relativehumidity |           loggedrelativehumidity |
        -------------------------------------------------------------
        |   1 |              1.0 | 1.0  0.0                     0.0 |
        |   2 |              3.0 | 3.0  1.0                     0.0 |
        |   3 |              2.0 | 2.0  3.0                     1.0 |
        |   4 |              4.0 | 4.0  2.0                     3.0 |
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_inputs.RelativeHumidity,)
    UPDATEDSEQUENCES = (evap_logs.LoggedRelativeHumidity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedrelativehumidity[idx] = log.loggedrelativehumidity[idx - 1]
        log.loggedrelativehumidity[0] = inp.relativehumidity


class Calc_DailyRelativeHumidity_V1(modeltools.Method):
    """Calculate the average of the relative humidity of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedrelativehumidity.shape = 3
        >>> logs.loggedrelativehumidity = 1.0, 5.0, 3.0
        >>> model.calc_dailyrelativehumidity_v1()
        >>> factors.dailyrelativehumidity
        dailyrelativehumidity(3.0)
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedRelativeHumidity,)
    RESULTSEQUENCES = (evap_factors.DailyRelativeHumidity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        fac.dailyrelativehumidity = 0.0
        for idx in range(der.nmblogentries):
            fac.dailyrelativehumidity += log.loggedrelativehumidity[idx]
        fac.dailyrelativehumidity /= der.nmblogentries


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    r"""Calculate the saturation vapour pressure according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 11):
      :math:`SaturationVapourPressure = 6.108 \cdot
      \exp \left( \frac{17.27 \cdot AirTemperature}{AirTemperature + 237.3} \right)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.airtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> factors.saturationvapourpressure
        saturationvapourpressure(12.279626)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressure[k] = 6.108 * modelutils.exp(
                17.27 * fac.airtemperature[k] / (fac.airtemperature[k] + 237.3)
            )


class Return_SaturationVapourPressure_V1(modeltools.Method):
    r"""Calculate and return the saturation vapour pressure according to
    :cite:t:`ref-Weischet1983`.

    Basic equation:
      :math:`f(T) = 6.1078 \cdot 2.71828^{\frac{17.08085 \cdot T}{T + 234.175}}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_saturationvapourpressure_v1(10.0))
        12.293852
    """

    @staticmethod
    def __call__(model: modeltools.Model, airtemperature: float) -> float:
        return 6.1078 * 2.71828 ** (
            17.08085 * airtemperature / (airtemperature + 234.175)
        )


class Calc_SaturationVapourPressure_V2(modeltools.Method):
    r"""Calculate the saturation vapour pressure according to
    :cite:t:`ref-Weischet1983`.

    Basic equation:
      :math:`SaturationVapourPressure =
      Return\_SaturationVapourPressure\_V1(AirTemperature)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.airtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v2()
        >>> factors.saturationvapourpressure
        saturationvapourpressure(12.293852)
    """

    SUBMETHODS = (Return_SaturationVapourPressure_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressure[k] = model.return_saturationvapourpressure_v1(
                fac.airtemperature[k]
            )


class Calc_DailySaturationVapourPressure_V1(modeltools.Method):
    r"""Calculate the average of the saturation vapour pressure of the last 24 hours
    according to :cite:t:`ref-Weischet1983`.

    Basic equation:
      :math:`DailySaturationVapourPressure =
      Return\_SaturationVapourPressure\_V1(DailyAirTemperature)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.dailyairtemperature = 10.0
        >>> model.calc_dailysaturationvapourpressure_v1()
        >>> factors.dailysaturationvapourpressure
        dailysaturationvapourpressure(12.293852)
    """

    SUBMETHODS = (Return_SaturationVapourPressure_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.DailyAirTemperature,)
    RESULTSEQUENCES = (evap_factors.DailySaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.dailysaturationvapourpressure[k] = (
                model.return_saturationvapourpressure_v1(fac.dailyairtemperature[k])
            )


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    r"""Calculate the slope of the saturation vapour pressure curve according to
    :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 13):
      :math:`SaturationVapourPressureSlope = 4098 \cdot
      \frac{SaturationVapourPressure}{(AirTemperature + 237.3)^2}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.airtemperature = 10.0
        >>> factors.saturationvapourpressure = 12.279626
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> factors.saturationvapourpressureslope
        saturationvapourpressureslope(0.822828)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
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
                / (fac.airtemperature[k] + 237.3) ** 2
            )


class Return_SaturationVapourPressureSlope_V1(modeltools.Method):
    r"""Calculate and return the saturation vapour pressure slope according to
    :cite:t:`ref-Weischet1983`.

    Basic equation (derivative of |Return_SaturationVapourPressure_V1|:
      :math:`f(T) =
      \frac{24430.6 \cdot exp((17.08085 \cdot T) / (T + 234.175)}{(T + 234.175)^2}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(model.return_saturationvapourpressureslope_v1(10.0))
        0.824774

        >>> dx = 1e-6
        >>> round_((model.return_saturationvapourpressure_v1(10.0 + dx) -
        ...         model.return_saturationvapourpressure_v1(10.0 - dx)) / 2 / dx)
        0.824775
    """

    @staticmethod
    def __call__(model: modeltools.Model, t: float) -> float:
        return (
            24430.6 * modelutils.exp(17.08085 * t / (t + 234.175)) / (t + 234.175) ** 2
        )


class Calc_SaturationVapourPressureSlope_V2(modeltools.Method):
    r"""Calculate the slope of the saturation vapour pressure curve according to
    :cite:t:`ref-Weischet1983`.

    Basic equation:
      :math:`SaturationVapourPressureSlope =
      Return\_SaturationVapourPressureSlope\_V1(AirTemperature)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> factors.airtemperature = 10.0, 0.0, -10.0
        >>> model.calc_saturationvapourpressureslope_v2()
        >>> factors.saturationvapourpressureslope
        saturationvapourpressureslope(0.824774, 0.445506, 0.226909)
    """

    SUBMETHODS = (Return_SaturationVapourPressureSlope_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressureslope[k] = (
                model.return_saturationvapourpressureslope_v1(fac.airtemperature[k])
            )


class Calc_DailySaturationVapourPressureSlope_V1(modeltools.Method):
    r"""Average the slope of the saturation vapour pressure curve according to
    :cite:t:`ref-Weischet1983` of the last 24 hours.

    Basic equation:
      :math:`DailySaturationVapourPressureSlope =
      Return\_SaturationVapourPressureSlope\_V1(DailyAirTemperature)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> factors.dailyairtemperature = 10.0, 0.0, -10.0
        >>> model.calc_dailysaturationvapourpressureslope_v1()
        >>> factors.dailysaturationvapourpressureslope
        dailysaturationvapourpressureslope(0.824774, 0.445506, 0.226909)
    """

    SUBMETHODS = (Return_SaturationVapourPressureSlope_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.DailyAirTemperature,)
    RESULTSEQUENCES = (evap_factors.DailySaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.dailysaturationvapourpressureslope[k] = (
                model.return_saturationvapourpressureslope_v1(
                    fac.dailyairtemperature[k]
                )
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


class Calc_DailyActualVapourPressure_V1(modeltools.Method):
    r"""Calculate the average of the actual vapour pressure of the last 24 hours.

    Basic equation:
      :math:`DailyActualVapourPressure = DailySaturationVapourPressure \cdot
      DailyRelativeHumidity / 100`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.dailyrelativehumidity = 60.0
        >>> factors.dailysaturationvapourpressure = 30.0
        >>> model.calc_dailyactualvapourpressure_v1()
        >>> factors.dailyactualvapourpressure
        dailyactualvapourpressure(18.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_factors.DailyRelativeHumidity,
        evap_factors.DailySaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.DailyActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.dailyactualvapourpressure[k] = (
                fac.dailysaturationvapourpressure[k] * fac.dailyrelativehumidity / 100.0
            )


class Calc_DryAirPressure_V1(modeltools.Method):
    """Calculate the dry air pressure :cite:p:`ref-DWD1987`.

    Basic equation:
       :math:`DryAirPressure = AirPressure - ActualVapourPressure`

    Example:
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> factors.actualvapourpressure = 9.0, 11.0, 25.0
        >>> inputs.atmosphericpressure = 1200.0
        >>> model.calc_dryairpressure_v1()
        >>> factors.dryairpressure
        dryairpressure(1191.0, 1189.0, 1175.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_factors.ActualVapourPressure,
        evap_inputs.AtmosphericPressure,
    )
    RESULTSEQUENCES = (evap_factors.DryAirPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.dryairpressure[k] = (
                inp.atmosphericpressure - fac.actualvapourpressure[k]
            )


class Calc_AirDensity_V1(modeltools.Method):
    r"""Calculate the air density :cite:p:`ref-DWD1987`.

    Basic equation:
       :math:`AirDensity = \frac{100}{AirTemperature + 273.15} \cdot
       \left( \frac{DryAirPressure}{GasConstantDryAir}
       + \frac{ActualVapourPressure}{GasConstantWaterVapour} \right)`

    Example:
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> factors.dryairpressure = 1191.0, 1000.0, 1150.0
        >>> factors.actualvapourpressure = 8.0, 7.0, 10.0
        >>> factors.airtemperature = 10.0, 12.0, 14.0
        >>> model.calc_airdensity_v1()
        >>> factors.airdensity
        airdensity(1.471419, 1.226998, 1.402691)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    FIXEDPARAMETERS = (evap_fixed.GasConstantDryAir, evap_fixed.GasConstantWaterVapour)
    REQUIREDSEQUENCES = (
        evap_factors.ActualVapourPressure,
        evap_factors.DryAirPressure,
        evap_factors.AirTemperature,
    )
    RESULTSEQUENCES = (evap_factors.AirDensity,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.airdensity[k] = (100.0 / (fac.airtemperature[k] + 273.15)) * (
                fac.dryairpressure[k] / fix.gasconstantdryair
                + fac.actualvapourpressure[k] / fix.gasconstantwatervapour
            )


class Process_RadiationModel_V1(modeltools.Method):
    """Let a submodel that complies with the |RadiationModel_V1| interface preprocess
    all eventually required data.

    Example:

        We use the combination of |evap_ret_fao56| and |meteo_glob_fao56| as an
        example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
        >>> from hydpy.models.evap_ret_fao56 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56"):
        ...     latitude(50.8)
        ...     angstromconstant(0.25)
        ...     angstromfactor(0.5)
        ...     inputs.sunshineduration = 9.25
        >>> model.process_radiationmodel_v1()
        >>> model.radiationmodel.sequences.fluxes.globalradiation
        globalradiation(255.367464)

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMODELINTERFACES = (radiationinterfaces.RadiationModel_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.radiationmodel_typeid == 1:
            cast(
                radiationinterfaces.RadiationModel_V1, model.radiationmodel
            ).process_radiation()
        # ToDo:
        #     elif ...
        #     else:
        #         assert_never(model.radiationmodel)


class Calc_PossibleSunshineDuration_V1(modeltools.Method):
    """Query the possible sunshine duration from a submodel that complies with the
    |RadiationModel_V1| or |RadiationModel_V4| interface.

    Examples:

        We combine |evap_pet_ambav1| with submodels that comply with different
        interfaces.  First, with |meteo_glob_fao56|, which complies with
        |RadiationModel_V1|:

        >>> from hydpy.models.evap_pet_ambav1 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56", update=False):
        ...     factors.possiblesunshineduration = 10.0
        >>> model.calc_possiblesunshineduration()
        >>> factors.possiblesunshineduration
        possiblesunshineduration(10.0)

        Second, with |meteo_psun_sun_glob_io|, which complies with |RadiationModel_V4|:

        >>> with model.add_radiationmodel_v4("meteo_psun_sun_glob_io", update=False):
        ...     inputs.possiblesunshineduration = 14.0
        >>> model.calc_possiblesunshineduration()
        >>> factors.possiblesunshineduration
        possiblesunshineduration(14.0)
    """

    SUBMODELINTERFACES = (
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V4,
    )
    RESULTSEQUENCES = (evap_factors.PossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        if model.radiationmodel_typeid == 1:
            fac.possiblesunshineduration = cast(
                radiationinterfaces.RadiationModel_V3, model.radiationmodel
            ).get_possiblesunshineduration()
        elif model.radiationmodel_typeid == 4:
            fac.possiblesunshineduration = cast(
                radiationinterfaces.RadiationModel_V4, model.radiationmodel
            ).get_possiblesunshineduration()
        # ToDo:
        #     elif ...
        #     else:
        #         assert_never(model.radiationmodel)


class Calc_SunshineDuration_V1(modeltools.Method):
    """Query the actual sunshine duration from a submodel that complies with the
    |RadiationModel_V1| or |RadiationModel_V4| interface.

    Examples:

        We combine |evap_pet_ambav1| with submodels that comply with different
        interfaces.  First, with |meteo_glob_fao56|, which complies with
        |RadiationModel_V1|:

        >>> from hydpy.models.evap_pet_ambav1 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56", update=False):
        ...     inputs.sunshineduration = 10.0
        >>> model.calc_sunshineduration()
        >>> factors.sunshineduration
        sunshineduration(10.0)

        Second, with |meteo_psun_sun_glob_io|, which complies with |RadiationModel_V4|:

        >>> with model.add_radiationmodel_v4("meteo_psun_sun_glob_io", update=False):
        ...     inputs.sunshineduration = 14.0
        >>> model.calc_sunshineduration()
        >>> factors.sunshineduration
        sunshineduration(14.0)
    """

    SUBMODELINTERFACES = (
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V4,
    )
    RESULTSEQUENCES = (evap_factors.SunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        if model.radiationmodel_typeid == 1:
            fac.sunshineduration = cast(
                radiationinterfaces.RadiationModel_V3, model.radiationmodel
            ).get_sunshineduration()
        elif model.radiationmodel_typeid == 4:
            fac.sunshineduration = cast(
                radiationinterfaces.RadiationModel_V4, model.radiationmodel
            ).get_sunshineduration()
        # ToDo:
        #     elif ...
        #     else:
        #         assert_never(model.radiationmodel)


class Calc_ClearSkySolarRadiation_V1(modeltools.Method):
    """Query the global radiation from a submodel that complies with the
    |RadiationModel_V1| or |RadiationModel_V3| interface.

    Examples:

        We combine |evap_ret_fao56| with submodels that comply with different
        interfaces.  First, with |meteo_glob_fao56|, which complies with
        |RadiationModel_V1|:

        >>> from hydpy.models.evap_ret_fao56 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56", update=False):
        ...     fluxes.clearskysolarradiation = 100.0
        >>> model.calc_clearskysolarradiation()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(100.0)

        Second, with |meteo_clear_glob_io|, which complies with |RadiationModel_V3|:

        >>> with model.add_radiationmodel_v3("meteo_clear_glob_io", update=False):
        ...     inputs.clearskysolarradiation = 300.0
        >>> model.calc_clearskysolarradiation()
        >>> fluxes.clearskysolarradiation
        clearskysolarradiation(300.0)
    """

    SUBMODELINTERFACES = (
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V3,
    )
    RESULTSEQUENCES = (evap_fluxes.ClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess

        if model.radiationmodel_typeid == 1:
            flu.clearskysolarradiation = cast(
                radiationinterfaces.RadiationModel_V1, model.radiationmodel
            ).get_clearskysolarradiation()
        elif model.radiationmodel_typeid == 3:
            flu.clearskysolarradiation = cast(
                radiationinterfaces.RadiationModel_V3, model.radiationmodel
            ).get_clearskysolarradiation()
        # ToDo:
        #     elif ...
        #     else:
        #         assert_never(model.radiationmodel)


class Calc_GlobalRadiation_V1(modeltools.Method):
    """Query the global radiation from a submodel that complies with the
    |RadiationModel_V1|, |RadiationModel_V2|, |RadiationModel_V3|, or
    |RadiationModel_V4| interface.

    Examples:

        We combine three main models with submodels that comply with the four
        radiation-related interfaces.  First, |evap_ret_fao56| with |meteo_glob_fao56|,
        which complies with |RadiationModel_V1|:

        >>> from hydpy.models.evap_ret_fao56 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56", update=False):
        ...     fluxes.globalradiation = 100.0
        >>> model.calc_globalradiation()
        >>> fluxes.globalradiation
        globalradiation(100.0)

        Second, |evap_ret_tw2002| with |meteo_glob_io|, which complies with
        |RadiationModel_V2|:

        >>> from hydpy.core.importtools import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.evap_ret_tw2002 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v2("meteo_glob_io", update=False):
        ...     inputs.globalradiation = 200.0
        >>> model.calc_globalradiation()
        >>> fluxes.globalradiation
        globalradiation(200.0)

        Third, |evap_ret_fao56| with |meteo_clear_glob_io|, which complies with
        |RadiationModel_V3|:

        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.evap_ret_fao56 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v3("meteo_clear_glob_io", update=False):
        ...     inputs.globalradiation = 300.0
        >>> model.calc_globalradiation()
        >>> fluxes.globalradiation
        globalradiation(300.0)

        Fourth, |evap_pet_ambav1| with |meteo_psun_sun_glob_io|, which complies with
        |RadiationModel_V4|:

        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.evap_pet_ambav1 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v4("meteo_psun_sun_glob_io", update=False):
        ...     inputs.globalradiation = 400.0
        >>> model.calc_globalradiation()
        >>> fluxes.globalradiation
        globalradiation(400.0)
    """

    SUBMODELINTERFACES = (
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V2,
        radiationinterfaces.RadiationModel_V3,
        radiationinterfaces.RadiationModel_V4,
    )
    RESULTSEQUENCES = (evap_fluxes.GlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess

        if model.radiationmodel_typeid == 1:
            flu.globalradiation = cast(
                radiationinterfaces.RadiationModel_V1, model.radiationmodel
            ).get_globalradiation()
        elif model.radiationmodel_typeid == 2:
            flu.globalradiation = cast(
                radiationinterfaces.RadiationModel_V2, model.radiationmodel
            ).get_globalradiation()
        elif model.radiationmodel_typeid == 3:
            flu.globalradiation = cast(
                radiationinterfaces.RadiationModel_V3, model.radiationmodel
            ).get_globalradiation()
        elif model.radiationmodel_typeid == 4:
            flu.globalradiation = cast(
                radiationinterfaces.RadiationModel_V4, model.radiationmodel
            ).get_globalradiation()
        # ToDo:
        #     else:
        #         assert_never(model.radiationmodel)


class Update_LoggedSunshineDuration_V1(modeltools.Method):
    """Log the sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the new value on the leftmost
        position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsunshineduration.shape = 3
        >>> logs.loggedsunshineduration = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedsunshineduration_v1,
        ...                 last_example=4,
        ...                 parseqs=(factors.sunshineduration,
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

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_factors.SunshineDuration,)
    UPDATEDSEQUENCES = (evap_logs.LoggedSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedsunshineduration[idx] = log.loggedsunshineduration[idx - 1]
        log.loggedsunshineduration[0] = fac.sunshineduration


class Calc_DailySunshineDuration_V1(modeltools.Method):
    """Calculate the sunshine duration sum of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsunshineduration.shape = 3
        >>> logs.loggedsunshineduration = 1.0, 5.0, 3.0
        >>> model.calc_dailysunshineduration_v1()
        >>> factors.dailysunshineduration
        dailysunshineduration(9.0)
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedSunshineDuration,)
    RESULTSEQUENCES = (evap_factors.DailySunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        fac.dailysunshineduration = 0.0
        for idx in range(der.nmblogentries):
            fac.dailysunshineduration += log.loggedsunshineduration[idx]


class Update_LoggedPossibleSunshineDuration_V1(modeltools.Method):
    """Log the astronomically possible sunshine duration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the new value on the leftmost
        position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedpossiblesunshineduration.shape = 3
        >>> logs.loggedpossiblesunshineduration = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedpossiblesunshineduration_v1,
        ...                 last_example=4,
        ...                 parseqs=(factors.possiblesunshineduration,
        ...                          logs.loggedpossiblesunshineduration))
        >>> test.nexts.possiblesunshineduration = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedpossiblesunshineduration
        >>> test()
        | ex. | possiblesunshineduration |           loggedpossiblesunshineduration |
        -----------------------------------------------------------------------------
        |   1 |                      1.0 | 1.0  0.0                             0.0 |
        |   2 |                      3.0 | 3.0  1.0                             0.0 |
        |   3 |                      2.0 | 2.0  3.0                             1.0 |
        |   4 |                      4.0 | 4.0  2.0                             3.0 |
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_factors.PossibleSunshineDuration,)
    UPDATEDSEQUENCES = (evap_logs.LoggedPossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedpossiblesunshineduration[idx] = (
                log.loggedpossiblesunshineduration[idx - 1]
            )
        log.loggedpossiblesunshineduration[0] = fac.possiblesunshineduration


class Calc_DailyPossibleSunshineDuration_V1(modeltools.Method):
    """Calculate the sunshine duration sum of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedpossiblesunshineduration.shape = 3
        >>> logs.loggedpossiblesunshineduration = 1.0, 5.0, 3.0
        >>> model.calc_dailypossiblesunshineduration_v1()
        >>> factors.dailypossiblesunshineduration
        dailypossiblesunshineduration(9.0)
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedPossibleSunshineDuration,)
    RESULTSEQUENCES = (evap_factors.DailyPossibleSunshineDuration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        fac.dailypossiblesunshineduration = 0.0
        for idx in range(der.nmblogentries):
            fac.dailypossiblesunshineduration += log.loggedpossiblesunshineduration[idx]


class Update_LoggedClearSkySolarRadiation_V1(modeltools.Method):
    """Log the clear sky solar radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the new value on the leftmost
        position:

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


class Update_LoggedGlobalRadiation_V1(modeltools.Method):
    """Log the global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the new value on the leftmost
        position:

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


class Calc_DailyGlobalRadiation_V1(modeltools.Method):
    """Average the global radiation of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedglobalradiation.shape = 3
        >>> logs.loggedglobalradiation = 100.0, 800.0, 600.0
        >>> model.calc_dailyglobalradiation_v1()
        >>> fluxes.dailyglobalradiation
        dailyglobalradiation(500.0)
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedGlobalRadiation,)
    RESULTSEQUENCES = (evap_fluxes.DailyGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dailyglobalradiation = 0.0
        for idx in range(der.nmblogentries):
            flu.dailyglobalradiation += log.loggedglobalradiation[idx]
        flu.dailyglobalradiation /= der.nmblogentries


class Calc_CurrentAlbedo_SnowAlbedoModel_V1(modeltools.Method):
    """Query the current Earth surface albedo from a main model referenced as a
    sub-submodel and follows the |SnowAlbedoModel_V1| interface."""

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.CurrentAlbedo,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: stateinterfaces.SnowAlbedoModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.currentalbedo[k] = submodel.get_snowalbedo(k)


class Calc_CurrentAlbedo_V1(modeltools.Method):
    """Take the land type- and month-specific albedo from parameter |Albedo| or a
    submodel that complies with the |SnowAlbedoModel_V1| interface.

    Examples:

        We use the combination of |lland_knauf| and |evap_aet_morsim| as an example and
        set different albedo values for the land types |lland_constants.ACKER| and
        |lland_constants.VERS| for January and February:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.models.lland_knauf import *
        >>> parameterstep()
        >>> ft(10.0)
        >>> nhru(3)
        >>> fhru(5.0, 3.0, 2.0)
        >>> lnk(ACKER, VERS, VERS)
        >>> measuringheightwindspeed(10.0)
        >>> lai(3.0)
        >>> wmax(100.0)
        >>> with model.add_aetmodel_v1("evap_aet_morsim"):
        ...     albedo.acker_jan = 0.2
        ...     albedo.vers_jan = 0.3
        ...     albedo.acker_feb = 0.4
        ...     albedo.vers_feb = 0.5

        |SnowAlbedoModel_V1| submodels return |numpy.nan| values for snow-free
        conditions.  In such cases (see the first and second hydrological response
        unit), |Calc_CurrentAlbedo_V1| takes the relevant value from parameter
        |Albedo|.  If there is a snow cover (see the third response unit), the
        |SnowAlbedoModel_V1| submodel provides an albedo value and
        |Calc_CurrentAlbedo_V1| takes it without modification:

        >>> model.aetmodel.idx_sim = 1
        >>> fluxes.actualalbedo = nan, nan, 1.0
        >>> model.aetmodel.calc_currentalbedo_v1()
        >>> model.aetmodel.sequences.factors.currentalbedo
        currentalbedo(0.2, 0.3, 1.0)

        |Calc_CurrentAlbedo_V1| always falls back on using the land type- and
        month-specific values of parameter |Albedo| if no |SnowAlbedoModel_V1| submodel
        is available:

        >>> del model.aetmodel.snowalbedomodel
        >>> model.aetmodel.idx_sim = 2
        >>> model.aetmodel.calc_currentalbedo_v1()
        >>> model.aetmodel.sequences.factors.currentalbedo
        currentalbedo(0.4, 0.5, 0.5)
    """

    SUBMODELINTERFACES = (stateinterfaces.SnowAlbedoModel_V1,)
    SUBMETHODS = (Calc_CurrentAlbedo_SnowAlbedoModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.HRUType, evap_control.Albedo)
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    RESULTSEQUENCES = (evap_factors.CurrentAlbedo,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        if model.snowalbedomodel is None:
            for k in range(con.nmbhru):
                fac.currentalbedo[k] = con.albedo[
                    con.hrutype[k] - con._albedo_rowmin,
                    der.moy[model.idx_sim] - con._albedo_columnmin,
                ]
        elif model.snowalbedomodel_typeid == 1:
            model.calc_currentalbedo_snowalbedomodel_v1(
                cast(stateinterfaces.SnowAlbedoModel_V1, model.snowalbedomodel)
            )
            for k in range(con.nmbhru):
                if modelutils.isnan(fac.currentalbedo[k]):
                    fac.currentalbedo[k] = con.albedo[
                        con.hrutype[k] - con._albedo_rowmin,
                        der.moy[model.idx_sim] - con._albedo_columnmin,
                    ]


class Calc_CurrentAlbedo_V2(modeltools.Method):
    r"""Calculate the earth's surface albedo based on the current leaf area index and
    snow conditions following :cite:t:`ref-Löpmeier2014`.

    Basic equations:
      .. math::
        CurrentAlbedo = \alpha_g + (\alpha_l - \alpha_g) \cdot min(lai/4, \ 1)
        \\ \\
        \alpha_g = \omega \cdot GroundAlbedoSnow + (1 - \omega) \cdot \alpha_g^* \\
        \alpha_g^*  = GroundAlbedo \cdot \begin{cases}
        1 &|\ \overline{Soil} \ \lor \ p / e < \tau \\
        0.5 &|\ Soil \ \land \ p / e \geq \tau \end{cases} \\
        \tau = WetnessThreshold \\
        p = DailyPrecipitation \\
        e = DailyPotentialSoilEvapotranspiration \\
        \alpha_l = \omega \cdot LeafAlbedoSnow + (1 - \omega) \cdot LeafAlbedo \\
        \omega = SnowCover \\
        lai = LeafAreaIndex

    Examples:

        We use |lland_knauf| and |evap_aet_minhas| as main models to prepare an
        applicable |evap| instance (more precisely, an |evap_pet_ambav1| instance):

        >>> from hydpy.models.lland_knauf import *
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(WASSER, BODEN, ACKER, BAUMB, LAUBW)
        >>> ft(10.0)
        >>> fhru(0.2)
        >>> wmax(200.0)
        >>> measuringheightwindspeed(10.0)
        >>> lai.acker = 2.0
        >>> lai.baumb = 3.0
        >>> lai.may_laubw = 4.0
        >>> lai.jun_laubw = 5.0
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-05-30", "2000-06-03", "1d"
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     with model.add_petmodel_v2("evap_pet_ambav1") as ambav:
        ...         groundalbedo(wasser=0.1, boden=0.2, acker=0.2, baumb=0.2, laubw=0.2)
        ...         groundalbedosnow(0.8)
        ...         leafalbedo(acker=0.3, baumb=0.3, laubw=0.3)
        ...         leafalbedosnow(0.6)
        ...         wetnessthreshold(0.5)
        ...         factors.snowcover = 0.0
        ...         fluxes.dailyprecipitation = 1.0
        ...         fluxes.dailypotentialsoilevapotranspiration = 4.0
        >>> factors = ambav.sequences.factors
        >>> fluxes = ambav.sequences.fluxes

        The first example focuses on the general weighting of the ground's and the
        leaves' albedo based on the current leaf area index.  For vegetation-free
        hydrological response units, |Calc_CurrentAlbedo_V2| only considers the
        ground's albedo:

        >>> ambav.idx_sim = pub.timegrids.init["2000-05-31"]
        >>> ambav.calc_currentalbedo_v2()
        >>> factors.currentalbedo
        currentalbedo(0.1, 0.2, 0.25, 0.275, 0.3)

        For a leaf area index of four, |Calc_CurrentAlbedo_V2| only considers the
        leaves' albedo.  Hence, setting higher indexes than four does not change the
        results:

        >>> ambav.idx_sim = pub.timegrids.init["2000-06-01"]
        >>> ambav.calc_currentalbedo_v2()
        >>> factors.currentalbedo
        currentalbedo(0.1, 0.2, 0.25, 0.275, 0.3)

        For wet conditions, where the ratio of precipitation and potential soil
        evapotranspiration exceeds the defined wetness threshold,
        |Calc_CurrentAlbedo_V2| halves the ground's albedo of all response units with
        non-sealed soils:

        >>> fluxes.dailyprecipitation = 2.0
        >>> ambav.calc_currentalbedo_v2()
        >>> factors.currentalbedo
        currentalbedo(0.1, 0.1, 0.2, 0.25, 0.3)

        For complete snow covers, |Calc_CurrentAlbedo_V2| relies on |GroundAlbedoSnow|
        and |LeafAlbedoSnow| instead of |GroundAlbedo| and |LeafAlbedo|:

        >>> fluxes.dailyprecipitation = 1.0
        >>> factors.snowcover = 1.0
        >>> ambav.calc_currentalbedo_v2()
        >>> factors.currentalbedo
        currentalbedo(0.8, 0.8, 0.7, 0.65, 0.6)

        For incomplete snow covers, |Calc_CurrentAlbedo_V2| weights the respective
        parameter pairs accordingly:

        >>> factors.snowcover = 0.5
        >>> ambav.calc_currentalbedo_v2()
        >>> factors.currentalbedo
        currentalbedo(0.45, 0.5, 0.475, 0.4625, 0.45)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Soil,
        evap_control.Plant,
        evap_control.GroundAlbedo,
        evap_control.GroundAlbedoSnow,
        evap_control.LeafAlbedo,
        evap_control.LeafAlbedoSnow,
        evap_control.LeafAreaIndex,
        evap_control.WetnessThreshold,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (
        evap_factors.SnowCover,
        evap_fluxes.DailyPrecipitation,
        evap_fluxes.DailyPotentialSoilEvapotranspiration,
    )
    RESULTSEQUENCES = (evap_factors.CurrentAlbedo,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nmbhru):
            w: float = fac.snowcover[k]
            a_s: float = con.groundalbedo[k]
            if con.soil[k]:
                wetness: float = flu.dailyprecipitation[k] / con.wetnessthreshold[k]
                if wetness >= flu.dailypotentialsoilevapotranspiration[k]:
                    a_s /= 2.0
            a_g: float = w * con.groundalbedosnow[k] + (1.0 - w) * a_s
            a_l: float = w * con.leafalbedosnow[k] + (1.0 - w) * con.leafalbedo[k]
            if con.plant[k]:
                lai: float = con.leafareaindex[
                    con.hrutype[k] - con._leafareaindex_rowmin,
                    der.moy[model.idx_sim] - con._leafareaindex_columnmin,
                ]
                if lai < 4.0:
                    fac.currentalbedo[k] = a_g + 0.25 * (a_l - a_g) * lai
                else:
                    fac.currentalbedo[k] = a_l
            else:
                fac.currentalbedo[k] = a_g


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net shortwave radiation for the hypothetical grass reference
    crop according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 38):
      :math:`NetShortwaveRadiation = (1.0 - 0.23) \cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> fluxes.globalradiation = 200.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(154.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_fluxes.GlobalRadiation,)
    RESULTSEQUENCES = (evap_fluxes.NetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        netshortwaveradiation: float = (1.0 - 0.23) * flu.globalradiation
        for k in range(con.nmbhru):
            flu.netshortwaveradiation[k] = netshortwaveradiation


class Calc_NetShortwaveRadiation_V2(modeltools.Method):
    r"""Calculate the net shortwave radiation for a time-variable albedo.

    Basic equation:
      :math:`NetShortwaveRadiation = (1.0 - CurrentAlbedo) \cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> fluxes.globalradiation = 100.0
        >>> factors.currentalbedo = 0.25
        >>> model.calc_netshortwaveradiation_v2()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(75.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.CurrentAlbedo, evap_fluxes.GlobalRadiation)
    RESULTSEQUENCES = (evap_fluxes.NetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.netshortwaveradiation[k] = flu.globalradiation * (
                1.0 - fac.currentalbedo[k]
            )


class Calc_DailyNetShortwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net shortwave radiation average for the last 24 hours.

    Basic equation:
      :math:`DailyNetShortwaveRadiation = (1-CurrentAlbedo) \cdot DailyGlobalRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.currentalbedo(0.25)
        >>> fluxes.dailyglobalradiation = 100.0
        >>> model.calc_dailynetshortwaveradiation_v1()
        >>> fluxes.dailynetshortwaveradiation
        dailynetshortwaveradiation(75.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_fluxes.DailyGlobalRadiation, evap_factors.CurrentAlbedo)
    RESULTSEQUENCES = (evap_fluxes.DailyNetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.dailynetshortwaveradiation[k] = (
                1.0 - fac.currentalbedo[k]
            ) * flu.dailyglobalradiation


class Update_CloudCoverage_V1(modeltools.Method):
    r"""Update the degree of cloud coverage.

    Basic equation:
      .. math::
        c_{new} =
        \begin{cases}
        s / s_0 &|\ s_0 = h \\
        c_{old} &|\ s_0 < h \\
        \end{cases}
        \\ \\
        c = CloudCoverage \\
        s = SunshineDuration \\
        s_0 = PossibleSunshineDuration \\
        h = Hours

    Examples:

        For a daily simulation step size, |Update_CloudCoverage_V1| always uses the
        ratio of the actual and the astronomically possible sunshine duration to
        estimate the cloud coverage degree:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.days(1.0)
        >>> factors.sunshineduration = 8.0
        >>> factors.possiblesunshineduration = 10.0
        >>> model.update_cloudcoverage_v1()
        >>> states.cloudcoverage
        cloudcoverage(0.8)

        The finally calculated cloud coverage degree never exceeds one:

        >>> factors.sunshineduration = 11.0
        >>> model.update_cloudcoverage_v1()
        >>> states.cloudcoverage
        cloudcoverage(1.0)

        Now, we switch to an hourly simulation step size:

        >>> derived.days(1.0 / 24.0)
        >>> derived.hours(1.0)

        During the daytime, |Update_CloudCoverage_V1| always updates the cloud coverage
        degree as described above:

        >>> factors.sunshineduration = 0.4
        >>> factors.possiblesunshineduration = 1.0
        >>> model.update_cloudcoverage_v1()
        >>> states.cloudcoverage
        cloudcoverage(0.4)

        From dusk until dawn, when the astronomically possible sunshine duration is
        shorter than the simulation step size, |Update_CloudCoverage_V1| leaves the
        previously calculated value untouched:

        >>> factors.possiblesunshineduration = 0.8
        >>> model.update_cloudcoverage_v1()
        >>> states.cloudcoverage
        cloudcoverage(0.4)
        """

    DERIVEDPARAMETERS = (evap_derived.Hours, evap_derived.Days)
    REQUIREDSEQUENCES = (
        evap_factors.SunshineDuration,
        evap_factors.PossibleSunshineDuration,
    )
    UPDATEDSEQUENCES = (evap_states.CloudCoverage,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess

        p0: float = fac.possiblesunshineduration
        if (der.days >= 1.0) or (p0 >= der.hours):
            sta.cloudcoverage = min(fac.sunshineduration / p0, 1.0)


class Calc_AdjustedCloudCoverage_V1(modeltools.Method):
    r"""Calculate the adjusted cloud coverage degree.

    Basic equation:
      .. math::
        AdjustedCloudCoverage = \omega \cdot c + (1 - \omega) \cdot n \cdot c
        \\ \\
        \omega = PossibleSunshineDuration / Hours \\
        c = CloudCoverage\\
        n = NightCloudFactor

    Examples:

        The above equation generally holds for night cloud factors not exceeding one:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nightcloudfactor(0.5)
        >>> derived.hours(24.0)
        >>> factors.possiblesunshineduration = 18.0
        >>> states.cloudcoverage = 0.8
        >>> model.calc_adjustedcloudcoverage_v1()
        >>> factors.adjustedcloudcoverage
        adjustedcloudcoverage(0.7)

        For night cloud factors above one, |Calc_AdjustedCloudCoverage_V1| ensures the
        estimated nighttime cloud cover degree never exceeds one:

        >>> nightcloudfactor(2.0)
        >>> model.calc_adjustedcloudcoverage_v1()
        >>> factors.adjustedcloudcoverage
        adjustedcloudcoverage(0.85)
        """

    CONTROLPARAMETERS = (evap_control.NightCloudFactor,)
    DERIVEDPARAMETERS = (evap_derived.Hours,)
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_states.CloudCoverage,
    )
    RESULTSEQUENCES = (evap_factors.AdjustedCloudCoverage,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        w: float = fac.possiblesunshineduration / der.hours
        c: float = sta.cloudcoverage
        n: float = con.nightcloudfactor
        fac.adjustedcloudcoverage = w * c + (1.0 - w) * min(n * c, 1.0)


class Calc_NetLongwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net longwave radiation according to :cite:t:`ref-Allen1998`.

    Basic equations (:cite:t:`ref-Allen1998`, equation 39, modified):
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

    Note that when clear sky radiation is zero at night, we use the global radiation
    and clear sky radiation sums of the last 24 hours.  Averaging over three hours
    before sunset, as :cite:t:`ref-Allen1998` suggests, could be more precise but is a
    more complicated and error-prone approach.

    Example:

        The following calculation agrees with example 11 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> derived.nmblogentries(1)
        >>> fluxes.globalradiation = 167.824074
        >>> fluxes.clearskysolarradiation = 217.592593
        >>> factors.airtemperature = 22.1
        >>> factors.actualvapourpressure = 21.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(40.87786)

        >>> fluxes.clearskysolarradiation = 0.0
        >>> logs.loggedclearskysolarradiation.shape = 1
        >>> logs.loggedclearskysolarradiation = 138.888889
        >>> logs.loggedglobalradiation.shape = 1
        >>> logs.loggedglobalradiation = 115.740741
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(45.832275)

        When necessary, |Calc_NetLongwaveRadiation_V1| trims the fraction of global
        radiation and clear sky solar radiation to one to prevent calculating
        unrealistically high net longwave radiations:

        >>> logs.loggedclearskysolarradiation = 1.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(59.13842)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
        evap_factors.ActualVapourPressure,
        evap_fluxes.ClearSkySolarRadiation,
        evap_fluxes.GlobalRadiation,
        evap_logs.LoggedGlobalRadiation,
        evap_logs.LoggedClearSkySolarRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        if flu.clearskysolarradiation > 0.0:
            globalradiation: float = flu.globalradiation
            clearskysolarradiation: float = flu.clearskysolarradiation
        else:
            globalradiation = 0.0
            clearskysolarradiation = 0.0
            for idx in range(der.nmblogentries):
                clearskysolarradiation += log.loggedclearskysolarradiation[idx]
                globalradiation += log.loggedglobalradiation[idx]
        for k in range(con.nmbhru):
            flu.netlongwaveradiation[k] = (
                5.674768518518519e-08
                * (fac.airtemperature[k] + 273.16) ** 4
                * (0.34 - 0.14 * (fac.actualvapourpressure[k] / 10.0) ** 0.5)
                * (1.35 * min(globalradiation / clearskysolarradiation, 1.0) - 0.35)
            )


class Calc_NetLongwaveRadiation_V2(modeltools.Method):
    r"""Calculate the net longwave radiation according to :cite:t:`ref-Löpmeier2014`,
    based on :cite:t:`ref-Holtslag1981`, :cite:t:`ref-Idso1969`, and
    :cite:t:`ref-Sellers1960`.

    Basic equations:
      .. math::
        NetLongwaveRadiation = RL_s - RL_a
        \\ \\
        RL_{s} = 0.97 \cdot \sigma \cdot (T + 273.1)^4 + 0.07 \cdot (1 - \alpha) \cdot G
        \\ \\
        RL_{a} = \left( 1 + C \cdot N^2 \right) \cdot \left(
        1 - 0.261 \cdot e^{-0.000777 \cdot T^2} \right) \cdot \sigma \cdot (T + 273.1)^4
        \\ \\
        \sigma = StefanBoltzmannConstant \\
        T = AirTemperature \\
        \alpha = CurrentAlbedo \\
        G = GlobalRadiation \\
        C = CloudTypeFactor \\
        N = AdjustedCloudCoverage

    Example:

        The following example is roughly comparable to the first example of
        |Calc_NetLongwaveRadiation_V1| taken from :cite:t:`ref-Allen1998` but results
        in a more than thrice as large net longwave radiation estimate:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> cloudtypefactor(0.2)
        >>> derived.nmblogentries(1)
        >>> fluxes.globalradiation = 167.824074
        >>> factors.adjustedcloudcoverage = 167.824074 / 217.592593
        >>> factors.airtemperature = 22.1
        >>> factors.currentalbedo = 0.23
        >>> model.calc_netlongwaveradiation_v2()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(30.940701)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.CloudTypeFactor)
    FIXEDPARAMETERS = (evap_fixed.StefanBoltzmannConstant,)
    REQUIREDSEQUENCES = (
        evap_factors.CurrentAlbedo,
        evap_factors.AdjustedCloudCoverage,
        evap_factors.AirTemperature,
        evap_fluxes.GlobalRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        s: float = fix.stefanboltzmannconstant
        g: float = flu.globalradiation
        f: float = 1.0 + con.cloudtypefactor * fac.adjustedcloudcoverage**2.0
        for k in range(con.nmbhru):
            t: float = fac.airtemperature[k]
            a: float = fac.currentalbedo[k]
            rs: float = 0.97 * s * (t + 273.1) ** 4.0 + 0.07 * (1.0 - a) * g
            ra: float = f * (
                (1.0 - 0.261 * modelutils.exp(-0.000777 * t**2.0))
                * (s * (t + 273.1) ** 4.0)
            )
            flu.netlongwaveradiation[k] = rs - ra


class Calc_DailyNetLongwaveRadiation_V1(modeltools.Method):
    r"""Calculate the average net longwave radiation of the last 24 hours according to
    :cite:t:`ref-LARSIM`.

    Basic equation:
      .. math::
       DailyNetLongwaveRadiation = \sigma\cdot T^4 \cdot
       \left( \epsilon - c \cdot \left(\frac{P} {T}\right)^{1/7} \right) \cdot
       \left (0.2 + 0.8 \cdot\frac{S}{S_p} \right)\\
       \\
       \sigma = StefanBoltzmannConstant \\
       T = DailyAirTemperature + 273.15 \\
       \epsilon = Emissivity \\
       c = FactorCounterRadiation \\
       P = DailyActualVapourPressure \\
       S = DailySunshineDuration\\
       S_p = DailyPossibleSunshineDuration

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> emissivity(0.95)
        >>> factors.dailyairtemperature = 22.1, 0.0
        >>> factors.dailyactualvapourpressure = 16.0, 6.0
        >>> factors.dailysunshineduration = 12.0
        >>> factors.dailypossiblesunshineduration = 14.0
        >>> model.calc_dailynetlongwaveradiation_v1()
        >>> fluxes.dailynetlongwaveradiation
        dailynetlongwaveradiation(40.451915, 58.190798)

        When necessary, |Calc_DailyNetLongwaveRadiation_V1| trims the fraction of
        actual and possible sunshine duration to one to prevent calculating
        unrealistically high net longwave radiations:

        >>> factors.dailysunshineduration = 24.0
        >>> model.calc_dailynetlongwaveradiation_v1()
        >>> fluxes.dailynetlongwaveradiation
        dailynetlongwaveradiation(45.671517, 65.699288)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Emissivity)
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.FactorCounterRadiation,
    )
    REQUIREDSEQUENCES = (
        evap_factors.DailyAirTemperature,
        evap_factors.DailyActualVapourPressure,
        evap_factors.DailySunshineDuration,
        evap_factors.DailyPossibleSunshineDuration,
    )
    RESULTSEQUENCES = (evap_fluxes.DailyNetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        rel_sunshine: float = min(
            fac.dailysunshineduration / fac.dailypossiblesunshineduration, 1.0
        )
        for k in range(con.nmbhru):
            t: float = fac.dailyairtemperature[k] + 273.15
            flu.dailynetlongwaveradiation[k] = (
                (0.2 + 0.8 * rel_sunshine)
                * (fix.stefanboltzmannconstant * t**4)
                * (
                    con.emissivity
                    - fix.factorcounterradiation
                    * (fac.dailyactualvapourpressure[k] / t) ** (1.0 / 7.0)
                )
            )


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation according to :cite:t:`ref-Allen1998` and
    according to :cite:t:`ref-Löpmeier2014`.

    Basic equation:
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
                flu.netshortwaveradiation[k] - flu.netlongwaveradiation[k]
            )


class Calc_NetRadiation_V2(modeltools.Method):
    """Calculate the total net radiation according to :cite:t:`ref-LARSIM`.

    Basic equation:
      :math:`NetRadiation = NetShortwaveRadiation - DailyNetLongwaveRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> fluxes.netshortwaveradiation = 300.0
        >>> fluxes.dailynetlongwaveradiation = 200.0
        >>> model.calc_netradiation_v2()
        >>> fluxes.netradiation
        netradiation(100.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_fluxes.NetShortwaveRadiation,
        evap_fluxes.DailyNetLongwaveRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.netradiation[k] = (
                flu.netshortwaveradiation[k] - flu.dailynetlongwaveradiation[k]
            )


class Calc_DailyNetRadiation_V1(modeltools.Method):
    """Calculate the average of the net radiation of the last 24 hours.

    Basic equation:
      :math:`DailyNetRadiation = DailyNetShortwaveRadiation - DailyNetLongwaveRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> fluxes.dailynetshortwaveradiation = 300.0
        >>> fluxes.dailynetlongwaveradiation = 200.0
        >>> model.calc_dailynetradiation_v1()
        >>> fluxes.dailynetradiation
        dailynetradiation(100.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_fluxes.DailyNetLongwaveRadiation,
        evap_fluxes.DailyNetShortwaveRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.DailyNetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.dailynetradiation[k] = (
                flu.dailynetshortwaveradiation[k] - flu.dailynetlongwaveradiation[k]
            )


class Calc_SoilHeatFlux_V1(modeltools.Method):
    r"""Calculate the soil heat flux according to :cite:t:`ref-Allen1998`.

    Basic equation for daily timesteps (:cite:t:`ref-Allen1998`, equation 42):
      :math:`SoilHeatFlux = 0`

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


class Calc_SoilHeatFlux_V2(modeltools.Method):
    r"""Calculate the MORECS-like soil heat flux roughly based on :cite:t:`ref-LARSIM`
    and :cite:t:`ref-Thompson1981`.

    Basic equations:
      :math:`SoilHeatFlux = \frac{PossibleSunshineDuration}
      {DailyPossibleSunshineDuration} \cdot G_D
      + \frac{(Hours - PossibleSunshineDuration)}
      {24-DailyPossibleSunshineDuration} \cdot G_N`

      :math:`G_N = AverageSoilHeatFlux - SoilHeatFlux_D`

      :math:`G_D = (0.3 - 0.03 \cdot LAI) \cdot DailyNetRadiation`

    The above equations are our interpretation of the relevant equations and
    explanations in the LARSIM user manual.  :math:`G_D` is the daytime sum of the soil
    heat flux, which depends on the daily sum of net radiation and the leaf area index.
    Curiously, |DailyNetRadiation| and :math:`G_D` become inversely related for leaf
    area index values higher than 10.  |AverageSoilHeatFlux| defines the daily energy
    change of the soil layer, which is why we use its difference to :math:`G_D` for
    estimating the nighttime sum of the soil heat flux (:math:`G_N`).

    .. note::

       The sudden jumps of the soil heat flux calculated by method
       |Calc_SoilHeatFlux_V2| sometimes result in strange-looking evapotranspiration
       time series.  Hence, we do not use |Calc_SoilHeatFlux_V2| in any application
       model for now but leave it for further discussion and use the simplified method
       |Calc_SoilHeatFlux_V3| instead.

    .. warning::

       We implemented this method when |lland| handled energy fluxes in MJ/m²/T.
       Before using it in an application model, one probably needs to adjust it to the
       new energy flux unit W/m².

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types `wood`, `trees`, `soil`, `acre`, and `water` to apply |evap| as a
        stand-alone model:

        >>> from hydpy import pub
        >>> pub.timegrids = "2019-05-30", "2019-06-03", "1d"
        >>> from hydpy.core.parametertools import Constants
        >>> WOOD, TREES, BUSH, SOIL, WATER = 1, 2, 3, 4, 5
        >>> constants = Constants(
        ...     WOOD=WOOD, TREES=TREES, BUSH=BUSH, SOIL=SOIL, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType, LeafAreaIndex
        >>> with HRUType.modify_constants(constants), \
        ...         LeafAreaIndex.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(4)

        We perform the first test calculation for a daily simulation step size to start
        as simple as possible:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-05-30", "2000-06-03", "1d"
        >>> from hydpy.models.evap import *
        >>> parameterstep()

        We define six hydrological response units, of which only the first five need
        further parameterisation, as method |Calc_SoilHeatFlux_V2| generally sets
        |SoilHeatFlux| to zero for water areas:

        >>> nmbhru(6)
        >>> hrutype(SOIL, BUSH, BUSH, TREES, WOOD, WATER)
        >>> water(False, False, False, False, False, True)

        We assign leaf area indices covering the usual range of values:

        >>> leafareaindex.soil = 0.0
        >>> leafareaindex.bush = 5.0
        >>> leafareaindex.trees = 10.0
        >>> leafareaindex.wood = 15.0

        We define a negative |AverageSoilHeatFlux| value for May (on average, energy
        moves from the soil body to the soil surface) and a positive one for June
        (energy moves from the surface to the body):

        >>> averagesoilheatflux.may = -10.0
        >>> averagesoilheatflux.jun = 20.0

        The following derived parameters need to be updated:

        >>> derived.moy.update()
        >>> derived.hours.update()

        For a daily simulation step size, the values of |PossibleSunshineDuration| (of
        the current simulation step) and |DailyPossibleSunshineDuration| must be
        identical:

        >>> factors.possiblesunshineduration = 14.0
        >>> factors.dailypossiblesunshineduration = 14.0

        We set |DailyNetRadiation| to 100 W/m² for most response units, except for the
        second bush unit:

        >>> fluxes.dailynetradiation = 100.0, 100.0, -100.0, 100.0, 100.0, 100.0

        For the given daily simulation step size, method |Calc_SoilHeatFlux_V2|
        calculates soil surface fluxes identical to the |AverageSoilHeatFlux| value
        of the respective month:

        >>> model.idx_sim = pub.timegrids.init["2000-05-31"]
        >>> model.calc_soilheatflux_v2()
        >>> fluxes.soilheatflux
        soilheatflux(-10.0, -10.0, -10.0, -10.0, -10.0, 0.0)
        >>> model.idx_sim = pub.timegrids.init["2000-06-01"]
        >>> model.calc_soilheatflux_v2()
        >>> fluxes.soilheatflux
        soilheatflux(20.0, 20.0, 20.0, 20.0, 20.0, 0.0)

        Next, we switch to an hourly step size and focus on May:

        >>> pub.timegrids = "2000-05-30 00:00", "2000-06-02 00:00", "1h"
        >>> model.idx_sim = pub.timegrids.init["2000-05-31"]
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> derived.days.update()

        During daytime (when the possible sunshine duration is one hour), the soil
        surface flux is positive for positive net radiation values and for leaf area
        index values below ten (see response units one and two).  Negative net
        radiation (response unit three) and leaf area indices above ten (response unit
        five) result in negative soil surface fluxes:

        >>> factors.possiblesunshineduration = 1.0
        >>> model.calc_soilheatflux_v2()
        >>> fluxes.soilheatflux
        soilheatflux(-2.142857, -1.071429, 1.071429, 0.0, 1.071429, 0.0)
        >>> day = fluxes.soilheatflux.values.copy()

        The nighttime soil surface fluxes (which we calculate by setting
        |PossibleSunshineDuration| to zero) somehow compensate for the daytime ones:

        >>> factors.possiblesunshineduration = 0.0
        >>> model.calc_soilheatflux_v2()
        >>> fluxes.soilheatflux
        soilheatflux(2.0, 0.5, -2.5, -1.0, -2.5, 0.0)
        >>> night = fluxes.soilheatflux.values.copy()

        This compensation enforces that the daily sum of the surface flux agrees
        with the actual value of |AverageSoilHeatFlux|, which we confirm by the
        following test calculation:

        >>> from hydpy import print_vector
        >>> print_vector(day * factors.dailypossiblesunshineduration +
        ...              night * (24.0 - factors.dailypossiblesunshineduration))
        -10.0, -10.0, -10.0, -10.0, -10.0, 0.0

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Water,
        evap_control.LeafAreaIndex,
        evap_control.AverageSoilHeatFlux,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY, evap_derived.Hours)
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_factors.DailyPossibleSunshineDuration,
        evap_fluxes.DailyNetRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.water[k]:
                flu.soilheatflux[k] = 0.0
            else:
                lai: float = con.leafareaindex[
                    con.hrutype[k] - con._leafareaindex_rowmin,
                    der.moy[model.idx_sim] - con._leafareaindex_columnmin,
                ]
                cr: float = 0.3 - 0.03 * lai
                gd: float = -cr * flu.dailynetradiation[k]
                gn: float = con.averagesoilheatflux[der.moy[model.idx_sim]] - gd
                gd_h: float = gd / fac.dailypossiblesunshineduration
                gn_h: float = gn / (24.0 - fac.dailypossiblesunshineduration)
                ps: float = fac.possiblesunshineduration
                flu.soilheatflux[k] = ps * gd_h + (der.hours - ps) * gn_h


class Calc_SoilHeatFlux_V3(modeltools.Method):
    """Take the monthly average soil heat flux as the current soil heat flux.

    Basic equations:
      :math:`SoilHeatFlux = AverageSoilHeatFlux`

    .. note::

       Method |Calc_SoilHeatFlux_V3| is a workaround.  We might remove it as soon as
       the shortcomings of method |Calc_SoilHeatFlux_V2| are fixed.

    Examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-05-30 00:00", "2000-06-02 00:00", "1h"
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> water(False, True)
        >>> averagesoilheatflux.may = 12.0
        >>> averagesoilheatflux.jun = -24.0
        >>> derived.moy.update()
        >>> derived.days.update()
        >>> model.idx_sim = pub.timegrids.init["2000-05-31 23:00"]
        >>> model.calc_soilheatflux_v3()
        >>> fluxes.soilheatflux
        soilheatflux(12.0, 0.0)
        >>> model.idx_sim = pub.timegrids.init["2000-06-01 00:00"]
        >>> model.calc_soilheatflux_v3()
        >>> fluxes.soilheatflux
        soilheatflux(-24.0, 0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Water,
        evap_control.AverageSoilHeatFlux,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.water[k]:
                flu.soilheatflux[k] = 0.0
            else:
                flu.soilheatflux[k] = con.averagesoilheatflux[der.moy[model.idx_sim]]


class Calc_SoilHeatFlux_V4(modeltools.Method):
    r"""Calculate the AMBAV-like soil heat flux based on :cite:t:`ref-Löpmeier2014`.

    Basic equations:
      .. math::
        G = max(a - b \cdot LAI, \ 0) \cdot R_n \\
        a = \omega \cdot 0.2 + (1 - \omega) \cdot 0.5 \\
        b = a \cdot 0.03 / 0.2
        \\ \\
        G = SoilHeatFlux \\
        LAI = LeafAreaIndex \\
        R_n = NetRadiation \\
        \omega = PossibleSunshineDuration / Hours

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types `wood`, `trees`, `bush`, and `acre` to apply |evap| as a stand-alone
        model consisting of four hydrological response units:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-05-30", "2000-06-03", "1d"
        >>> from hydpy.core.parametertools import Constants
        >>> WOOD, TREES, BUSH, ACRE, WATER = 1, 2, 3, 4, 5
        >>> constants = Constants(WOOD=WOOD, TREES=TREES, BUSH=BUSH, ACRE=ACRE)
        >>> from hydpy.models.evap.evap_control import HRUType, LeafAreaIndex
        >>> with HRUType.modify_constants(constants), \
        ...         LeafAreaIndex.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(4)

        For water areas, the soil heat flux is generally zero:

        >>> water(True)
        >>> model.calc_soilheatflux_v4()
        >>> fluxes.soilheatflux
        soilheatflux(0.0, 0.0, 0.0, 0.0)

        We focus on non-water areas using all the different defined land cover types in
        the following examples:

        >>> hrutype(ACRE, BUSH, TREES, WOOD)
        >>> water(False)

        The next calculation addressed the complete 31st of May, for which we set land
        cover-specific leaf area indices:

        >>> model.idx_sim = pub.timegrids.init["2000-05-31"]
        >>> derived.hours.update()
        >>> derived.moy.update()
        >>> leafareaindex.acre_may = 0.0
        >>> leafareaindex.bush_may = 2.0
        >>> leafareaindex.trees_may = 5.0
        >>> leafareaindex.wood_may = 10.0

        We say the astronomically possible sunshine duration and the net radiation of
        that day to be 18 h and 200 W/m²:

        >>> factors.possiblesunshineduration = 18.0
        >>> fluxes.netradiation = 200.0

        The larger the leaf area index, the smaller the soil heat flux.  The dense
        canopies of trees can suppress them entirely:

        >>> model.calc_soilheatflux_v4()
        >>> fluxes.soilheatflux
        soilheatflux(55.0, 38.5, 13.75, 0.0)

        Now, we switch to an hourly step size and to the time of sunrise on the 1st of
        June:

        >>> pub.timegrids = "2000-06-01 04:00", "2000-06-01 08:00", "1h"
        >>> model.idx_sim = pub.timegrids.init["2000-06-01 05:00"]
        >>> derived.hours.update()
        >>> derived.moy.update()

        We set slightly larger leaf area indices:

        >>> leafareaindex.acre_jun = 0.0
        >>> leafareaindex.bush_jun = 3.0
        >>> leafareaindex.trees_jun = 6.0
        >>> leafareaindex.wood_jun = 12.0

        We assume sunrise at 5:15 and a negative net radiation value:

        >>> factors.possiblesunshineduration = 0.25
        >>> fluxes.netradiation = -20.0

        Again, dense vegetation reduces the soil heat flux without changing its sign,
        and very dense vegetation suppresses it completely:

        >>> model.calc_soilheatflux_v4()
        >>> model.calc_soilheatflux_v4()
        >>> fluxes.soilheatflux
        soilheatflux(-8.5, -4.675, -0.85, 0.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Water,
        evap_control.LeafAreaIndex,
    )
    DERIVEDPARAMETERS = (evap_derived.Hours, evap_derived.MOY)
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_fluxes.NetRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        w: float = fac.possiblesunshineduration / der.hours
        a: float = w * 0.2 + (1.0 - w) * 0.5
        b: float = a * 0.03 / 0.2
        for k in range(con.nmbhru):
            if con.water[k]:
                flu.soilheatflux[k] = 0.0
            else:
                lai: float = con.leafareaindex[
                    con.hrutype[k] - con._leafareaindex_rowmin,
                    der.moy[model.idx_sim] - con._leafareaindex_columnmin,
                ]
                flu.soilheatflux[k] = max(a - b * lai, 0.0) * flu.netradiation[k]


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


class Calc_AerodynamicResistance_V1(modeltools.Method):
    r"""Calculate the aerodynamic resistance according to :cite:t:`ref-LARSIM` and
    based on :cite:t:`ref-Thompson1981`.

    Basic equations (:math:`z_0` after :cite:t:`ref-Quast1997`):
      .. math::
        AerodynamicResistance = \begin{cases}
        \frac{6.25}{WindSpeed10m} \cdot ln\left(\frac{10}{z_0}\right)^2
        &|\
        CropHeight < 10
        \\
        \frac{94}{WindSpeed10m}
        &|\
        CropHeight \geq 10
        \end{cases}

      :math:`z_0 = 0.021 + 0.163 \cdot CropHeight`

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types of wood, trees, bush, acre, and water to apply |evap| as a stand-alone
        model:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.core.parametertools import Constants
        >>> WOOD, TREES, BUSH, ACRE, WATER = 1, 2, 3, 4, 5
        >>> constants = Constants(
        ...     WOOD=WOOD, TREES=TREES, BUSH=BUSH, ACRE=ACRE, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType, CropHeight
        >>> with HRUType.modify_constants(constants), CropHeight.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(5)
        >>> hrutype(WATER, ACRE, BUSH, TREES, WOOD)
        >>> derived.moy.update()

        Besides wind speed, aerodynamic resistance depends on the crop height, which
        typically differs between land types and, for vegetated surfaces, months.  In
        the first example, we set different crop heights for different land types to
        cover the relevant range of values:

        >>> cropheight.water_jan = 0.0
        >>> cropheight.acre_jan = 1.0
        >>> cropheight.bush_jan = 5.0
        >>> cropheight.trees_jan = 10.0
        >>> cropheight.wood_jan = 30.0
        >>> factors.windspeed10m = 3.0
        >>> model.idx_sim = 1
        >>> model.calc_aerodynamicresistance_v1()
        >>> factors.aerodynamicresistance
        aerodynamicresistance(79.202731, 33.256788, 12.831028, 31.333333,
                              31.333333)

        The last example shows a decrease in resistance with increasing crop height for
        the first three hydrological response units only.  However, when  reaching a
        crop height of 10 m, the calculated resistance increases discontinuously (see
        the fourth response unit) and remains constant above (see the fifth response
        unit).  In the following example, we set unrealistic values to inspect this
        behaviour more closely:

        >>> cropheight.water_feb = 8.0
        >>> cropheight.acre_feb = 9.0
        >>> cropheight.bush_feb = 10.0
        >>> cropheight.trees_feb = 11.0
        >>> cropheight.wood_feb = 12.0
        >>> model.idx_sim = 2
        >>> model.calc_aerodynamicresistance_v1()
        >>> factors.aerodynamicresistance
        aerodynamicresistance(8.510706, 7.561677, 31.333333, 31.333333,
                              31.333333)

        One could use a threshold crop height of 1.14 m instead of 10 m to remove this
        discontinuity:

        :math:`1.1404411695422059 = \frac{\frac{10}{\exp\sqrt{94/6.25}}-0.021}{0.163}`

        The last example shows the inverse relationship between resistance and wind
        speed.  For zero wind speed, resistance becomes infinite:

        >>> from hydpy import print_vector
        >>> cropheight(2.0)
        >>> for ws in (0.0, 0.1, 1.0, 10.0):
        ...     factors.windspeed10m = ws
        ...     model.calc_aerodynamicresistance_v1()
        ...     print_vector([ws, factors.aerodynamicresistance[0]])
        0.0, inf
        0.1, 706.026613
        1.0, 70.602661
        10.0, 7.060266

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.CropHeight,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (evap_factors.WindSpeed10m,)
    RESULTSEQUENCES = (evap_factors.AerodynamicResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        if fac.windspeed10m > 0.0:
            for k in range(con.nmbhru):
                ch: float = con.cropheight[
                    con.hrutype[k] - con._cropheight_rowmin,
                    der.moy[model.idx_sim] - con._cropheight_columnmin,
                ]
                if ch < 10.0:
                    z0: float = 0.021 + 0.163 * ch
                    fac.aerodynamicresistance[k] = (
                        6.25 / fac.windspeed10m * modelutils.log(10.0 / z0) ** 2
                    )
                else:
                    fac.aerodynamicresistance[k] = 94.0 / fac.windspeed10m
        else:
            for k in range(con.nmbhru):
                fac.aerodynamicresistance[k] = modelutils.inf


class Calc_AerodynamicResistance_V2(modeltools.Method):
    r"""Calculate the aerodynamic resistance according to :cite:t:`ref-Löpmeier2014`.

    Basic equation:
      .. math::
        AerodynamicResistance = AerodynamicResistanceFactor / WindSpeed10m

    Examples:

        We reuse the same example setting of method |Calc_AerodynamicResistance_V1| to
        allow for comparisons:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-03", "1d"
        >>> from hydpy.core.parametertools import Constants
        >>> WOOD, TREES, BUSH, ACRE, WATER = 1, 2, 3, 4, 5
        >>> constants = Constants(
        ...     WOOD=WOOD, TREES=TREES, BUSH=BUSH, ACRE=ACRE, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType, CropHeight
        >>> from hydpy.models.evap.evap_derived import AerodynamicResistanceFactor, RoughnessLength  # pylint: disable=line-too-long
        >>> with HRUType.modify_constants(constants), CropHeight.modify_rows(constants), AerodynamicResistanceFactor.modify_rows(constants), RoughnessLength.modify_rows(constants) :  # pylint: disable=line-too-long
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(5)
        >>> hrutype(WATER, ACRE, BUSH, TREES, WOOD)
        >>> derived.moy.update()

        |Calc_AerodynamicResistance_V2| calculates larger resistances for crops smaller
        than 10 meters and equal resistances for crops larger than 10 meters:

        >>> cropheight.water_jan = 0.0
        >>> cropheight.acre_jan = 1.0
        >>> cropheight.bush_jan = 5.0
        >>> cropheight.trees_jan = 10.0
        >>> cropheight.wood_jan = 30.0
        >>> derived.roughnesslength.update()
        >>> derived.aerodynamicresistancefactor.update()
        >>> factors.windspeed10m = 3.0
        >>> model.idx_sim = 1
        >>> model.calc_aerodynamicresistance_v2()
        >>> factors.aerodynamicresistance
        aerodynamicresistance(250.991726, 37.398301, 31.333333, 31.333333,
                              31.333333)

        For zero wind speed, resistance becomes infinite:

        >>> from hydpy import print_vector
        >>> factors.windspeed10m = 0.0
        >>> model.calc_aerodynamicresistance_v2()
        >>> factors.aerodynamicresistance
        aerodynamicresistance(inf, inf, inf, inf, inf)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.HRUType)
    DERIVEDPARAMETERS = (evap_derived.MOY, evap_derived.AerodynamicResistanceFactor)
    REQUIREDSEQUENCES = (evap_factors.WindSpeed10m,)
    RESULTSEQUENCES = (evap_factors.AerodynamicResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess

        if fac.windspeed10m > 0.0:
            for k in range(con.nmbhru):
                f: float = der.aerodynamicresistancefactor[
                    con.hrutype[k] - der._aerodynamicresistancefactor_rowmin,
                    der.moy[model.idx_sim] - der._aerodynamicresistancefactor_columnmin,
                ]
                fac.aerodynamicresistance[k] = f / fac.windspeed10m
        else:
            for k in range(con.nmbhru):
                fac.aerodynamicresistance[k] = modelutils.inf


class Calc_SoilSurfaceResistance_V1(modeltools.Method):
    r"""Calculate the resistance of the bare soil surface according to
    :cite:t:`ref-LARSIM` and based on :cite:t:`ref-Thompson1981`.

    Basic equations:
      .. math::
        SoilSurfaceResistance = \begin{cases}
        100 &|\ W_m> 20
        \\
        \frac{100 \cdot W_m}{W_a + W_m/100} &|\ W_m\leq 20
        \end{cases}
        \\ \\
        W_a = SoilWater \\
        W_m = MaxSoilWater

    Examples:

        For areas without relevant soils (for example, water areas and sealed
        surfaces), |Calc_SoilSurfaceResistance_V1| sets the soil surface resistance to
        |numpy.nan|.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(5)
        >>> soil(False)
        >>> maxsoilwater(0.0)
        >>> soilmoisturelimit(0.0)
        >>> factors.soilwater = 0.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> factors.soilsurfaceresistance
        soilsurfaceresistance(nan, nan, nan, nan, nan)

        For soils with a maximum water content larger than 20 mm, the soil
        surface resistance is generally 100.0 s/m:

        >>> soil(True)
        >>> maxsoilwater(20.1)
        >>> factors.soilwater = 0.0, 5.0, 10.0, 15.0, 20.1
        >>> model.calc_soilsurfaceresistance_v1()
        >>> factors.soilsurfaceresistance
        soilsurfaceresistance(100.0, 100.0, 100.0, 100.0, 100.0)

        For "real" soils, resistance decreases with increasing soil water contents
        until it reaches a minimum of 99 s/m:

        >>> maxsoilwater(20.0)
        >>> factors.soilwater = 0.0, 5.0, 10.0, 15.0, 20.0
        >>> model.calc_soilsurfaceresistance_v1()
        >>> factors.soilsurfaceresistance
        soilsurfaceresistance(10000.0, 384.615385, 196.078431, 131.578947,
                              99.009901)

        For zero maximum water contents, soil surface resistance is zero:

        >>> maxsoilwater(0.0)
        >>> model.calc_soilsurfaceresistance_v1()
        >>> factors.soilsurfaceresistance
        soilsurfaceresistance(inf, inf, inf, inf, inf)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.MaxSoilWater,
    )
    REQUIREDSEQUENCES = (evap_factors.SoilWater,)
    RESULTSEQUENCES = (evap_factors.SoilSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            sw_max: float = con.maxsoilwater[k]
            if not con.soil[k]:
                fac.soilsurfaceresistance[k] = modelutils.nan
            elif sw_max > 20.0:
                fac.soilsurfaceresistance[k] = 100.0
            elif sw_max > 0.0:
                sw_act: float = min(max(fac.soilwater[k], 0.0), sw_max)
                fac.soilsurfaceresistance[k] = 100.0 * sw_max / (sw_act + 0.01 * sw_max)
            else:
                fac.soilsurfaceresistance[k] = modelutils.inf


class Update_LoggedPrecipitation_V1(modeltools.Method):
    """Log the precipitation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        six memorised values to the right and stores the respective two new values on
        the most left position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedprecipitation.shape = 3, 2
        >>> logs.loggedprecipitation = 0.0, 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedprecipitation_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.precipitation,
        ...                          logs.loggedprecipitation))
        >>> test.nexts.precipitation = [1.0, 2.0], [3.0, 6.0], [2.0, 4.0], [4.0, 8.0]
        >>> del test.inits.loggedprecipitation
        >>> test()
        | ex. |      precipitation |                          loggedprecipitation |
        ---------------------------------------------------------------------------
        |   1 | 1.0            2.0 | 1.0  2.0  0.0  0.0  0.0                  0.0 |
        |   2 | 3.0            6.0 | 3.0  6.0  1.0  2.0  0.0                  0.0 |
        |   3 | 2.0            4.0 | 2.0  4.0  3.0  6.0  1.0                  2.0 |
        |   4 | 4.0            8.0 | 4.0  8.0  2.0  4.0  3.0                  6.0 |
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_fluxes.Precipitation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            for k in range(con.nmbhru):
                log.loggedprecipitation[idx, k] = log.loggedprecipitation[idx - 1, k]
        for k in range(con.nmbhru):
            log.loggedprecipitation[0, k] = flu.precipitation[k]


class Calc_DailyPrecipitation_V1(modeltools.Method):
    """Calculate the precipitation sum of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedprecipitation.shape = 3, 2
        >>> logs.loggedprecipitation = [1.0, 2.0], [5.0, 6.0], [3.0, 4.0]
        >>> model.calc_dailyprecipitation_v1()
        >>> fluxes.dailyprecipitation
        dailyprecipitation(9.0, 12.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedPrecipitation,)
    RESULTSEQUENCES = (evap_fluxes.DailyPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.dailyprecipitation[k] = 0.0
        for idx in range(der.nmblogentries):
            for k in range(con.nmbhru):
                flu.dailyprecipitation[k] += log.loggedprecipitation[idx, k]


class Update_LoggedPotentialSoilEvapotranspiration_V1(modeltools.Method):
    # pylint: disable=line-too-long
    """Log the potential soil evapotranspiration values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        six memorised values to the right and stores the two new values on the leftmost
        position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedpotentialsoilevapotranspiration.shape = 3, 2
        >>> logs.loggedpotentialsoilevapotranspiration = 0.0, 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedpotentialsoilevapotranspiration_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.potentialsoilevapotranspiration,
        ...                          logs.loggedpotentialsoilevapotranspiration))
        >>> test.nexts.potentialsoilevapotranspiration = [1.0, 2.0], [3.0, 6.0], [2.0, 4.0], [4.0, 8.0]
        >>> del test.inits.loggedpotentialsoilevapotranspiration
        >>> test()
        | ex. |      potentialsoilevapotranspiration |                          loggedpotentialsoilevapotranspiration |
        ---------------------------------------------------------------------------------------------------------------
        |   1 | 1.0                              2.0 | 1.0  2.0  0.0  0.0  0.0                                    0.0 |
        |   2 | 3.0                              6.0 | 3.0  6.0  1.0  2.0  0.0                                    0.0 |
        |   3 | 2.0                              4.0 | 2.0  4.0  3.0  6.0  1.0                                    2.0 |
        |   4 | 4.0                              8.0 | 4.0  8.0  2.0  4.0  3.0                                    6.0 |
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_fluxes.PotentialSoilEvapotranspiration,)
    UPDATEDSEQUENCES = (evap_logs.LoggedPotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            for k in range(con.nmbhru):
                log.loggedpotentialsoilevapotranspiration[idx, k] = (
                    log.loggedpotentialsoilevapotranspiration[idx - 1, k]
                )
        for k in range(con.nmbhru):
            log.loggedpotentialsoilevapotranspiration[0, k] = (
                flu.potentialsoilevapotranspiration[k]
            )


class Calc_DailyPotentialSoilEvapotranspiration_V1(modeltools.Method):
    """Calculate the potential soil evapotranspiration sum of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedpotentialsoilevapotranspiration.shape = 3, 2
        >>> logs.loggedpotentialsoilevapotranspiration = (
        ...     [1.0, 2.0], [5.0, 6.0], [3.0, 4.0])
        >>> model.calc_dailypotentialsoilevapotranspiration_v1()
        >>> fluxes.dailypotentialsoilevapotranspiration
        dailypotentialsoilevapotranspiration(9.0, 12.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedPotentialSoilEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.DailyPotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.dailypotentialsoilevapotranspiration[k] = 0.0
        for idx in range(der.nmblogentries):
            for k in range(con.nmbhru):
                flu.dailypotentialsoilevapotranspiration[
                    k
                ] += log.loggedpotentialsoilevapotranspiration[idx, k]


class Update_SoilResistance_V1(modeltools.Method):
    r"""Update the soil surface resistance following :cite:t:`ref-Löpmeier2014`.

    Basic equations:
      .. math::
        r_{new} = \begin{cases}
        r_{old} + \Delta &|\ p / e < \tau \\
        w &|\ p / e \geq \tau
        \end{cases} \\
        \\ \\
        r = SoilResistance \\
        w = WetSoilResistance \\
        \Delta = SoilResistanceIncrease \\
        \tau = WetnessThreshold \\
        p = DailyPrecipitation \\
        e = DailyPotentialSoilEvapotranspiration

    Example:

        |Update_SoilResistance_V1| generally sets the soil surface resistance to |nan|
        for all areas without relevant soils (see the first hydrological response
        unit).  For all other areas, it increases the resistance constantly as long as
        the precipitation sum over the last 24 hours is less than the potential
        evapotranspiration sum over the last 24 hours (second response unit) or
        otherwise sets it to the "initial value" for wet soil surfaces (third and
        fourth response unit):

        >>> from hydpy.models.evap import *
        >>> parameterstep("1d")
        >>> simulationstep("1h")
        >>> nmbhru(4)
        >>> soil(False, True, True, True)
        >>> wetsoilresistance(50.0)
        >>> wetnessthreshold(0.5)
        >>> soilresistanceincrease(24.0)
        >>> states.soilresistance = 60.0
        >>> fluxes.dailyprecipitation = 3.0, 4.0, 5.0, 6.0
        >>> fluxes.dailypotentialsoilevapotranspiration = 10.0
        >>> model.update_soilresistance_v1()
        >>> states.soilresistance
        soilresistance(nan, 61.0, 50.0, 50.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.WetSoilResistance,
        evap_control.SoilResistanceIncrease,
        evap_control.WetnessThreshold,
    )
    REQUIREDSEQUENCES = (
        evap_fluxes.DailyPrecipitation,
        evap_fluxes.DailyPotentialSoilEvapotranspiration,
    )
    UPDATEDSEQUENCES = (evap_states.SoilResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                wetness: float = flu.dailyprecipitation[k] / con.wetnessthreshold[k]
                if wetness < flu.dailypotentialsoilevapotranspiration[k]:
                    sta.soilresistance[k] += con.soilresistanceincrease[k]
                else:
                    sta.soilresistance[k] = con.wetsoilresistance[k]
            else:
                sta.soilresistance[k] = modelutils.nan


class Calc_LanduseSurfaceResistance_V1(modeltools.Method):
    r"""Calculate the resistance of vegetation surfaces, water surfaces and sealed
    surfaces according to :cite:t:`ref-LARSIM` and based on :cite:t:`ref-Thompson1981`.

    Basic equations:
      .. math::
        LanduseSurfaceResistance = r^* \cdot \begin{cases}
        3.5 \cdot (1 - W / \tau) + exp(0.2 \cdot \tau / W)&|\ W \leq \tau
        \\
        exp(0.2) &|\ W > \tau
        \end{cases}
        \\ \\ \\
        r^*= \begin{cases}
        r&|\ \overline{C}
        \\
        10\,000 &|\ C \;\; \land \;\; (T \leq -5 \;\; \lor \;\; \Delta \geq 20)
        \\
        min\left(\frac{25 \cdot r}{(T + 5)
        \cdot (1 - \Delta / 20)}, \ 10\,000\right)
        &|\ C \;\; \land \;\; (-5 < T < 20 \;\; \land \;\; \Delta < 20)
        \\
        min\left(\frac{r}{1 - \Delta / 20}, \ 10\,000\right)
        &|\ C \;\; \land \;\; (20 \leq T \;\; \land \;\; \Delta < 20)
        \end{cases}
        \\ \\ \\
        W = SoilWater \\
        C = Conifer \\
        \tau = SoilMoistureLimit \cdot MaxSoilWater \\
        r = SurfaceResistance \\
        \Delta = SaturationVapourPressure - ActualVapourPressure \\
        T = AirTemperature

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types `water`, `sealed`, `acre`, and `conifer` to apply |evap| as a stand-alone
        model:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-05-30", "2000-06-03", "1d"
        >>> from hydpy.core.parametertools import Constants
        >>> WATER, SEALED, ACRE, CONIFER,  = 1, 2, 3, 4
        >>> constants = Constants(
        ...     WATER=WATER, SEALED=SEALED, ACRE=ACRE, CONIFER=CONIFER)
        >>> from hydpy.models.evap.evap_control import HRUType, SurfaceResistance
        >>> with HRUType.modify_constants(constants), \
        ...         SurfaceResistance.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(4)

        Method |Calc_LanduseSurfaceResistance_V1| relies on multiple discontinuous
        relationships, works differently for different land types, and uses monthly
        varying parameters.  Hence, we start simple and introduce further complexities
        step by step.

        For response units without relevant soils (like those with sealed surfaces or
        surface water bodies), the original parameter values are in effect without any
        modification:

        >>> hrutype(SEALED, SEALED, WATER, WATER)
        >>> soil(False)
        >>> conifer(False)
        >>> surfaceresistance.water_may = 0.0
        >>> surfaceresistance.sealed_may = 500.0
        >>> derived.moy.update()
        >>> model.idx_sim = 1
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(500.0, 500.0, 0.0, 0.0)

        For all "soil areas", |Calc_LanduseSurfaceResistance_V1| slightly increases the
        original parameter value by a constant factor for wet soils (|SoilWater| >
        |SoilMoistureLimit|) and increases it even more for dry soils (|SoilWater| >
        |SoilMoistureLimit|).  For a completely dried-up soils, surface resistance
        becomes infinite:

        >>> hrutype(ACRE)
        >>> soil(True)
        >>> soilmoisturelimit(0.0)
        >>> surfaceresistance.acre_jun = 40.0
        >>> factors.soilwater = 0.0, 10.0, 20.0, 30.0
        >>> model.idx_sim = 2
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(inf, 48.85611, 48.85611, 48.85611)

        >>> maxsoilwater(40.0)
        >>> soilmoisturelimit(0.5)
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(inf, 129.672988, 48.85611, 48.85611)

        >>> factors.soilwater = 17.0, 18.0, 19.0, 20.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(71.611234, 63.953955, 56.373101, 48.85611)

        |Calc_LanduseSurfaceResistance_V1| treats coniferous trees special by
        increasing surface resistance further for low temperatures and high water
        vapour pressure deficits.  The highest resistance value occurs for air
        temperatures lower than -5 °C or vapour pressure deficits higher than 20 hPa:

        >>> hrutype(CONIFER)
        >>> conifer(True)
        >>> surfaceresistance.conifer_jun = 80.0
        >>> factors.soilwater = 20.0
        >>> factors.airtemperature = 30.0
        >>> factors.saturationvapourpressure = 30.0
        >>> factors.actualvapourpressure = 0.0, 10.0, 20.0, 30.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 12214.027582, 195.424441,
                                 97.712221)

        >>> factors.actualvapourpressure = 10.0, 10.1, 11.0, 12.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 12214.027582, 1954.244413,
                                 977.122207)

        >>> factors.actualvapourpressure = 20.0
        >>> factors.airtemperature = -10.0, 5.0, 20.0, 35.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 488.561103, 195.424441,
                                 195.424441)

        >>> factors.airtemperature = -6.0, -5.0, -4.0, -3.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(12214.027582, 12214.027582, 4885.611033,
                                 2442.805516)

        >>> factors.airtemperature = 18.0, 19.0, 20.0, 21.0
        >>> model.calc_landusesurfaceresistance_v1()
        >>> factors.landusesurfaceresistance
        landusesurfaceresistance(212.417871, 203.567126, 195.424441, 195.424441)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Soil,
        evap_control.Conifer,
        evap_control.SurfaceResistance,
        evap_control.MaxSoilWater,
        evap_control.SoilMoistureLimit,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.SoilWater,
    )
    RESULTSEQUENCES = (evap_factors.LanduseSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            r: float = con.surfaceresistance[
                con.hrutype[k] - con._surfaceresistance_rowmin,
                der.moy[model.idx_sim] - con._surfaceresistance_columnmin,
            ]
            if con.conifer[k]:
                d: float = fac.saturationvapourpressure[k] - fac.actualvapourpressure[k]
                if (fac.airtemperature[k] <= -5.0) or (d >= 20.0):
                    fac.landusesurfaceresistance[k] = 10000.0
                elif fac.airtemperature[k] < 20.0:
                    fac.landusesurfaceresistance[k] = min(
                        (25.0 * r) / (fac.airtemperature[k] + 5.0) / (1.0 - 0.05 * d),
                        10000.0,
                    )
                else:
                    fac.landusesurfaceresistance[k] = min(r / (1.0 - 0.05 * d), 10000.0)
            else:
                fac.landusesurfaceresistance[k] = r
            if con.soil[k]:
                sw: float = fac.soilwater[k]
                if sw <= 0.0:
                    fac.landusesurfaceresistance[k] = modelutils.inf
                else:
                    thresh: float = con.soilmoisturelimit[k] * con.maxsoilwater[k]
                    if sw < thresh:
                        fac.landusesurfaceresistance[k] *= 3.5 * (
                            1.0 - sw / thresh
                        ) + modelutils.exp(0.2 * thresh / sw)
                    else:
                        fac.landusesurfaceresistance[k] *= modelutils.exp(0.2)


class Calc_ActualSurfaceResistance_V1(modeltools.Method):
    r"""Calculate the actual surface resistance according to :cite:t:`ref-LARSIM`,
    based on :cite:t:`ref-Grant1975`.

    Basic equations:
      :math:`ActualSurfaceResistance =
      \left(\frac{w}{SR_{day}} + \frac{1 - w}{SR_{night}}\right)^{-1}`

      :math:`SR_{day} =
      \left(\frac{1-0.7^{LeafAreaIndex}}{LanduseSurfaceResistance} +
      \frac{0.7^{LeafAreaIndex}}{SoilSurfaceResistance}\right)^{-1}`

      :math:`SR_{night} =
      \left(\frac{LeafAreaIndex}{2500} + \frac{1}{SoilSurfaceResistance}\right)^{-1}`

      :math:`w = \frac{PossibleSunshineDuration}{Hours}`

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types `wood`, `trees`, `bush`, `acre`, and `water` to apply |evap| as a
        stand-alone model:

        >>> from hydpy import pub
        >>> pub.timegrids = "2019-05-30", "2019-06-03", "1d"
        >>> from hydpy.core.parametertools import Constants
        >>> WOOD, TREES, BUSH, ACRE, WATER = 1, 2, 3, 4, 5
        >>> constants = Constants(
        ...     WOOD=WOOD, TREES=TREES, BUSH=BUSH, ACRE=ACRE, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType, LeafAreaIndex
        >>> with HRUType.modify_constants(constants), \
        ...         LeafAreaIndex.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(4)

        For response units without relevant soils (like those with sealed surfaces or
        surface water bodies), method |Calc_ActualSurfaceResistance_V1| just uses the
        values of sequence |LanduseSurfaceResistance| as the effective surface
        resistance values:

        >>> hrutype(WATER)
        >>> soil(False)
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> factors.soilsurfaceresistance = nan
        >>> factors.landusesurfaceresistance = 500.0, 0.0, 0.0, 0.0
        >>> model.idx_sim = 1
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(500.0, 0.0, 0.0, 0.0)

        For all "soil areas", the final soil resistance is a combination of
        |LanduseSurfaceResistance| and |SoilSurfaceResistance| that depends on the leaf
        area index:

        >>> hrutype(ACRE, BUSH, TREES, WOOD)
        >>> soil(True)
        >>> leafareaindex.acre_may = 0.0
        >>> leafareaindex.bush_may = 2.0
        >>> leafareaindex.trees_may = 5.0
        >>> leafareaindex.wood_may = 10.0

        All four hydrological response units have identical soil- and land-use-related
        surface resistance values:

        >>> factors.soilsurfaceresistance = 200.0
        >>> factors.landusesurfaceresistance = 100.0

        For a polar day, the actual resistance equals the soil surface resistance for
        zero leaf area indices (see the first response unit).  With an increasing leaf
        area index, actual resistance tends towards land-use-related resistance:

        >>> factors.possiblesunshineduration = 24.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(200.0, 132.450331, 109.174477, 101.43261)

        For a polar night, |Calc_ActualSurfaceResistance_V1| performs a leaf area
        index-dependent interpolation between soil surface resistance and a fixed
        resistance value:

        >>> factors.possiblesunshineduration = 0.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(200.0, 172.413793, 142.857143, 111.111111)

        For all days that are neither polar nights nor polar days, the values of the
        two examples above are weighted based on the possible sunshine duration of that
        day:

        >>> factors.possiblesunshineduration = 12.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(200.0, 149.812734, 123.765057, 106.051498)

        The following examples demonstrate that method
        |Calc_ActualSurfaceResistance_V1| works the same way when applied on an hourly
        time basis during the daytime period (first example), during the nighttime
        (second example), and during dawn or dusk (third example):

        >>> pub.timegrids = "2019-05-31 22:00", "2019-06-01 03:00", "1h"
        >>> nmbhru(1)
        >>> hrutype(WOOD)
        >>> soil(True)
        >>> factors.soilsurfaceresistance = 200.0
        >>> factors.landusesurfaceresistance = 100.0
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> leafareaindex.wood_jun = 5.0
        >>> model.idx_sim = 2
        >>> factors.possiblesunshineduration = 1.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(109.174477)

        >>> factors.possiblesunshineduration = 0.0
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(142.857143)

        >>> factors.possiblesunshineduration = 0.5
        >>> model.calc_actualsurfaceresistance_v1()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(123.765057)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Soil,
        evap_control.LeafAreaIndex,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY, evap_derived.Hours)
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_factors.SoilSurfaceResistance,
        evap_factors.LanduseSurfaceResistance,
    )

    RESULTSEQUENCES = (evap_factors.ActualSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                lai: float = con.leafareaindex[
                    con.hrutype[k] - con._leafareaindex_rowmin,
                    der.moy[model.idx_sim] - con._leafareaindex_columnmin,
                ]
                invsrday: float = (
                    (1.0 - 0.7**lai) / fac.landusesurfaceresistance[k]
                ) + 0.7**lai / fac.soilsurfaceresistance[k]
                invsrnight: float = lai / 2500.0 + 1.0 / fac.soilsurfaceresistance[k]
                w: float = fac.possiblesunshineduration / der.hours
                fac.actualsurfaceresistance[k] = 1.0 / (
                    (w * invsrday + (1.0 - w) * invsrnight)
                )
            else:
                fac.actualsurfaceresistance[k] = fac.landusesurfaceresistance[k]


class Calc_ActualSurfaceResistance_V2(modeltools.Method):
    r"""Calculate the actual surface resistance according to :cite:t:`ref-Löpmeier2014`
    and based on :cite:t:`ref-Thompson1981`.

    Basic equations:
      .. math::
        ActualSurfaceResistance = \left(\frac{\omega_{day}}{r_{day}} +
        \frac{1 - \omega_{day}}{r_{night}}\right)^{-1} \\
        \\ \\
        r_{day} = \left(\frac{1 - \omega_{soil}}{r_l} +
        \frac{\omega_{soil}}{r_s}\right)^{-1} \\ \\
        r_{night} = \left(\frac{lai}{2800} + \frac{1}{r_s}\right)^{-1} \\
        \\ \\
        \omega_{day} = PossibleSunshineDuration / Hours \\
        \omega_{soil} = \begin{cases} 0.8^{lai} &|\ lai < 1 \\
        0.7^{lai} &|\ lai \geq 1 \end{cases} \\
        \\ \\
        lai = LeafAreaIndex \\
        r_s = SoilSurfaceResistance \\
        r_l = LeafResistance

    Examples:

        |Calc_ActualSurfaceResistance_V2| works similarly to method
        |Calc_ActualSurfaceResistance_V1|.  We build up a comparable setting but use
        |lland_dd| and |evap_aet_minhas| as main models to prepare an applicable |evap|
        instance (more precisely, an |evap_pet_ambav1| instance) more easily:

        >>> from hydpy.models.lland_dd import *
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(WASSER, FLUSS, SEE, BODEN, BODEN)
        >>> ft(10.0)
        >>> fhru(0.2)
        >>> wmax(200.0)
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-05-30", "2000-06-03", "1d"
        >>> with model.add_aetmodel_v1("evap_aet_minhas"):
        ...     with model.add_petmodel_v2("evap_pet_ambav1") as ambav:
        ...         pass
        >>> control = ambav.parameters.control
        >>> derived = ambav.parameters.derived
        >>> inputs = ambav.sequences.inputs
        >>> factors = ambav.sequences.factors
        >>> states = ambav.sequences.states

        For response units without relevant soils (like those with sealed surfaces) or
        with unvegetated soils, method |Calc_ActualSurfaceResistance_V2| generally
        performs no calculation but sets the effective surface resistance to zero or
        takes the defined soil resistance value:

        >>> control.hrutype
        hrutype(WASSER, FLUSS, SEE, BODEN, BODEN)
        >>> control.soil
        soil(boden=True, fluss=False, see=False, wasser=False)
        >>> states.soilresistance = 300.0
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(0.0, 0.0, 0.0, 300.0, 300.0)

        For all "soil areas", the final soil resistance is a combination of
        |LeafResistance| and |SoilResistance| that depends on the leaf area index,
        which is generally zero for non-vegetated land cover types:

        >>> lnk(BODEN, ACKER, GRUE_E, GRUE_I, NADELW)
        >>> model.update_parameters(ignore_errors=True)
        >>> control.hrutype
        hrutype(BODEN, ACKER, GRUE_E, GRUE_I, NADELW)
        >>> control.soil
        soil(True)
        >>> control.plant
        plant(acker=True, boden=False, grue_e=True, grue_i=True, nadelw=True)
        >>> control.leafareaindex.acker_may = 0.0
        >>> control.leafareaindex.grue_e_may = 0.9999
        >>> control.leafareaindex.grue_i_may = 1.0
        >>> control.leafareaindex.baumb_may = 5.0
        >>> control.leafareaindex.nadelw_may = 10.0
        >>> model.idx_sim = 1
        >>> derived.moy.update()
        >>> derived.hours.update()

        All five hydrological response units have identical soil and leaf resistance
        values:

        >>> control.leafresistance(100.0)
        >>> states.soilresistance = 200.0

        For a polar day, the results are identical to those of method
        |Calc_ActualSurfaceResistance_V1|, except that
        |Calc_ActualSurfaceResistance_V2| calculates larger values for leaf area
        indices smaller than one (which goes along with a sudden resistance decrease
        when reaching a leaf area index of one):

        >>> factors.possiblesunshineduration = 24.0
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(200.0, 200.0, 166.669146, 153.846154, 101.43261)

        For a polar night, |Calc_ActualSurfaceResistance_V2| calculates slightly higher
        values due to assuming a surface resistance of 2,800 s/m instead of 2,500 s/m
        for leaves with completely closed stomata:

        >>> factors.possiblesunshineduration = 0.0
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(200.0, 200.0, 186.667911, 186.666667, 116.666667)

        Accordingly, |Calc_ActualSurfaceResistance_V2| always determines slightly
        higher surface resistances in mixed cases:

        >>> factors.possiblesunshineduration = 12.0
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(200.0, 200.0, 176.102567, 168.674699, 108.517595)

        The following examples demonstrate that method
        |Calc_ActualSurfaceResistance_V2| works the same way when applied on an hourly
        time basis during the daytime period (first example), during the nighttime
        (second example), and during dawn or dusk (third example):

        >>> pub.timegrids = "2019-05-31 22:00", "2019-06-01 03:00", "1h"
        >>> nhru(1)
        >>> lnk(NADELW)
        >>> fhru(1.0)
        >>> wmax(200.0)
        >>> model.update_parameters(ignore_errors=True)
        >>> control.hrutype
        hrutype(NADELW)
        >>> control.soil
        soil(True)
        >>> control.plant
        plant(True)
        >>> control.leafresistance(100.0)
        >>> states.soilresistance = 200.0
        >>> control.leafareaindex.nadelw_jun = 5.0
        >>> derived.moy.update()
        >>> derived.hours.update()
        >>> factors.possiblesunshineduration = 1.0
        >>> ambav.idx_sim = 2
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(109.174477)

        >>> factors.possiblesunshineduration = 0.0
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(147.368421)

        >>> factors.possiblesunshineduration = 0.5
        >>> ambav.calc_actualsurfaceresistance_v2()
        >>> factors.actualsurfaceresistance
        actualsurfaceresistance(125.428304)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Soil,
        evap_control.Plant,
        evap_control.LeafAreaIndex,
        evap_control.LeafResistance,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY, evap_derived.Hours)
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_states.SoilResistance,
    )

    RESULTSEQUENCES = (evap_factors.ActualSurfaceResistance,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nmbhru):
            if con.plant[k]:
                lai: float = con.leafareaindex[
                    con.hrutype[k] - con._leafareaindex_rowmin,
                    der.moy[model.idx_sim] - con._leafareaindex_columnmin,
                ]
                w_soil: float = (0.8 if lai < 1.0 else 0.7) ** lai
                r_soil: float = sta.soilresistance[k]
                r_leaf_day: float = con.leafresistance[k]
                r_day_inv: float = w_soil / r_soil + (1.0 - w_soil) / r_leaf_day
                r_leaf_night: float = 2800.0
                r_night_inv: float = 1.0 / r_soil + lai / r_leaf_night
                w_day: float = fac.possiblesunshineduration / der.hours
                fac.actualsurfaceresistance[k] = 1.0 / (
                    (w_day * r_day_inv + (1.0 - w_day) * r_night_inv)
                )
            elif con.soil[k]:
                fac.actualsurfaceresistance[k] = sta.soilresistance[k]
            else:
                fac.actualsurfaceresistance[k] = 0.0


class Calc_Precipitation_PrecipModel_V1(modeltools.Method):
    """Query precipitation from a main model that is referenced as a sub-submodel and
    follows the |PrecipModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |evap_pet_hbv96| as an example:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> fc(200.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     with model.add_petmodel_v1("evap_pet_hbv96"):
        ...         pass
        >>> fluxes.pc(1.0, 3.0, 2.0)
        >>> model.aetmodel.petmodel.calc_precipitation_v1()
        >>> model.aetmodel.petmodel.sequences.fluxes.precipitation
        precipitation(1.0, 3.0, 2.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.Precipitation,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: precipinterfaces.PrecipModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.precipitation[k] = submodel.get_precipitation(k)


class Calc_Precipitation_PrecipModel_V2(modeltools.Method):
    """Let a submodel that complies with the |PrecipModel_V2| interface determine the
    precipitation.

    Example:

        We use the combination of |evap_pet_hbv96| and |meteo_precip_io| as an example:

        >>> from hydpy.models.evap_pet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     precipitationfactor(0.5, 1.0, 2.0)
        ...     inputs.precipitation = 2.0
        >>> model.calc_precipitation_v1()
        >>> fluxes.precipitation
        precipitation(1.0, 2.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.Precipitation,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: precipinterfaces.PrecipModel_V2
    ) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_precipitation()
        for k in range(con.nmbhru):
            flu.precipitation[k] = submodel.get_precipitation(k)


class Calc_Precipitation_V1(modeltools.Method):
    """Let a submodel that complies with the |PrecipModel_V1| or |PrecipModel_V2|
    interface determine precipitation."""

    SUBMODELINTERFACES = (
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
    )
    SUBMETHODS = (Calc_Precipitation_PrecipModel_V1, Calc_Precipitation_PrecipModel_V2)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.precipmodel_typeid == 1:
            model.calc_precipitation_precipmodel_v1(
                cast(precipinterfaces.PrecipModel_V1, model.precipmodel)
            )
        elif model.precipmodel_typeid == 2:
            model.calc_precipitation_precipmodel_v2(
                cast(precipinterfaces.PrecipModel_V2, model.precipmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_InterceptedWater_IntercModel_V1(modeltools.Method):
    """Query the current amount of intercepted water from a submodel that follows the
    |IntercModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |evap_aet_hbv96| as an example:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> fc(100.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     pass
        >>> states.ic = 1.0, 3.0, 2.0
        >>> model.aetmodel.calc_interceptedwater_v1()
        >>> model.aetmodel.sequences.factors.interceptedwater
        interceptedwater(1.0, 3.0, 2.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.InterceptedWater,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: stateinterfaces.IntercModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.interceptedwater[k] = submodel.get_interceptedwater(k)


class Calc_InterceptedWater_V1(modeltools.Method):
    """Let a submodel that complies with the |IntercModel_V1| interface determine the
    current amount of intercepted water."""

    SUBMODELINTERFACES = (stateinterfaces.IntercModel_V1,)
    SUBMETHODS = (Calc_InterceptedWater_IntercModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.InterceptedWater,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.intercmodel_typeid == 1:
            model.calc_interceptedwater_intercmodel_v1(
                cast(stateinterfaces.IntercModel_V1, model.intercmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_SnowyCanopy_SnowyCanopyModel_V1(modeltools.Method):
    """Query the current snow cover degree in the canopies of tree-like
    vegetation from a submodel that follows the |SnowyCanopyModel_V1| interface."""

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.SnowyCanopy,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: stateinterfaces.SnowyCanopyModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.snowycanopy[k] = submodel.get_snowycanopy(k)


class Calc_SnowyCanopy_V1(modeltools.Method):
    """Query the current snow cover degree in the canopies of tree-like
    vegetation from a submodel that follows the |SnowyCanopyModel_V1| interface, if
    available.

    Examples:

        We use the combination of |lland_knauf_ic| and |evap_aet_morsim| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.lland_knauf_ic import *
        >>> parameterstep()
        >>> ft(10.0)
        >>> nhru(3)
        >>> fhru(5.0, 3.0, 2.0)
        >>> lnk(LAUBW, LAUBW, ACKER)
        >>> measuringheightwindspeed(10.0)
        >>> lai(3.0)
        >>> wmax(100.0)
        >>> states.stinz = 0.0, 0.1, 0.1
        >>> with model.add_aetmodel_v1("evap_aet_morsim"):
        ...     pass
        >>> model.aetmodel.calc_snowycanopy_v1()
        >>> model.aetmodel.sequences.factors.snowycanopy
        snowycanopy(0.0, 1.0, nan)

        Without a suitable submodel, |Calc_SnowyCanopy_V1| generally sets |SnowyCanopy|
        to |numpy.nan|:

        >>> del model.aetmodel.snowycanopymodel
        >>> model.aetmodel.calc_snowycanopy_v1()
        >>> model.aetmodel.sequences.factors.snowycanopy
        snowycanopy(nan, nan, nan)

        .. testsetup::

            >>> del pub.timegrids
    """

    SUBMODELINTERFACES = (stateinterfaces.SnowyCanopyModel_V1,)
    SUBMETHODS = (Calc_SnowyCanopy_SnowyCanopyModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.SnowyCanopy,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        if model.snowycanopymodel is None:
            for k in range(con.nmbhru):
                fac.snowycanopy[k] = modelutils.nan
        elif model.snowycanopymodel_typeid == 1:
            model.calc_snowycanopy_snowycanopymodel_v1(
                cast(stateinterfaces.SnowyCanopyModel_V1, model.snowycanopymodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.snowycanopymodel)


class Calc_SoilWater_SoilWaterModel_V1(modeltools.Method):
    """Query the current soil water amount from as submodel that follows the
    |SoilWaterModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |evap_aet_hbv96| as an example:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> fc(100.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     pass
        >>> states.sm = 10.0, 30.0, 20.0
        >>> model.aetmodel.calc_soilwater_v1()
        >>> model.aetmodel.sequences.factors.soilwater
        soilwater(10.0, 30.0, 20.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.SoilWater,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: stateinterfaces.SoilWaterModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.soilwater[k] = submodel.get_soilwater(k)


class Calc_SoilWater_V1(modeltools.Method):
    """Let a submodel that complies with the |SoilWaterModel_V1| interface determine
    the current soil water amount."""

    SUBMODELINTERFACES = (stateinterfaces.SoilWaterModel_V1,)
    SUBMETHODS = (Calc_SoilWater_SoilWaterModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.SoilWater,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.soilwatermodel_typeid == 1:
            model.calc_soilwater_soilwatermodel_v1(
                cast(stateinterfaces.SoilWaterModel_V1, model.soilwatermodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_SnowCover_SnowCoverModel_V1(modeltools.Method):
    """Query the current snow cover degree from a submodel that follows the
    |SnowCoverModel_V1| interface.

    Example:

        We use the combination of |hland_96| and |evap_aet_hbv96| as an example:

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> sclass(2)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> fc(100.0)
        >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
        ...     pass
        >>> states.sp = [[0.0, 0.0, 1.0], [0.0, 1.0, 1.0]]
        >>> model.aetmodel.calc_snowcover_v1()
        >>> model.aetmodel.sequences.factors.snowcover
        snowcover(0.0, 0.5, 1.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.SnowCover,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: stateinterfaces.SnowCoverModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.snowcover[k] = submodel.get_snowcover(k)


class Calc_SnowCover_V1(modeltools.Method):
    """Let a submodel that complies with the |SnowCoverModel_V1| interface determine
    the current snow cover degree."""

    SUBMODELINTERFACES = (stateinterfaces.SnowCoverModel_V1,)
    SUBMETHODS = (Calc_SnowCover_SnowCoverModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.SnowCover,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.snowcovermodel_typeid == 1:
            model.calc_snowcover_snowcovermodel_v1(
                cast(stateinterfaces.SnowCoverModel_V1, model.snowcovermodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Return_Evaporation_PenmanMonteith_V1(modeltools.Method):
    r"""Calculate the actual evapotranspiration with the Penman-Monteith equation
    according to :cite:t:`ref-LARSIM`, based on :cite:t:`ref-Thompson1981`.

    Basic equations:

    .. math::
      f_{PM}(r_s) =
      \frac{P'_s \cdot (R_n - G) + C \cdot \rho \cdot c_p \cdot (P_s - P_a) / r_a}
      {H \cdot (P'_s + \gamma \cdot C \cdot (1 + r_s / r_a))} \\
      \\
      C = 1 + \frac{b' \cdot r_a}{\rho \cdot c_p} \\
      \\
      b' = 4 \cdot \varepsilon \cdot \sigma \cdot (273.15 + T)^3 \\
      \\
      r_s = actualsurfaceresistance \\
      P'_s = SaturationVapourPressureSlope  \\
      R_n = NetRadiation \\
      G = SoilHeatFlux \\
      \rho = AirDensitiy  \\
      c_p = HeatCapacityAir \\
      P_s = SaturationVapourPressure \\
      P_a = ActualVapourPressure \\
      r_a = AerodynamicResistance \\
      H = HeatOfCondensation \\
      \gamma = PsychrometricConstant \\
      \varepsilon = Emissivity \\
      T = AirTemperature \\
      \sigma = StefanBoltzmannConstant

    Hint: Correction factor `C` takes the difference between measured air temperature
    and actual surface temperature into account.

    Example:

        We build the following example on the first example of the documentation on
        method |Calc_WaterEvaporation_V3|, which relies on the Penman equation.  The
        total available energy (|NetRadiation| minus |SoilHeatFlux|) and the vapour
        saturation pressure deficit (|SaturationVapourPressure| minus
        |ActualVapourPressure| are identical.  To make the results roughly comparable,
        we use resistances suitable for water surfaces by setting
        |ActualSurfaceResistance| to zero and |AerodynamicResistance| to a reasonable
        precalculated value of 106 s/m:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(7)
        >>> emissivity(0.96)
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> fluxes.soilheatflux = 10.0
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.airdensity = 1.24
        >>> factors.actualsurfaceresistance = 0.0
        >>> factors.aerodynamicresistance = 106.0
        >>> factors.airtemperature = 10.0

        For the first three hydrological response units with energy forcing only, there
        is a relatively small deviation to the results of method
        |Calc_WaterEvaporation_V3| due to the correction factor `C`, which is only
        implemented by method |Return_Evaporation_PenmanMonteith_V1|.  For response
        units four to six with dynamic forcing only, the results of method
        |Return_Evaporation_PenmanMonteith_V1| are more than twice as large as those
        of method |Calc_WaterEvaporation_V3|:

        >>> from hydpy import print_vector
        >>> for hru in range(7):
        ...     deficit = (factors.saturationvapourpressure[hru] -
        ...                factors.actualvapourpressure[hru])
        ...     evap = model.return_evaporation_penmanmonteith_v1(
        ...         hru, factors.actualsurfaceresistance[hru])
        ...     energygain = fluxes.netradiation[hru] - fluxes.soilheatflux[hru]
        ...     print_vector([energygain, deficit, evap])
        0.0, 0.0, 0.0
        40.0, 0.0, 0.648881
        90.0, 0.0, 1.459982
        0.0, 0.0, 0.0
        0.0, 6.0, 2.031724
        0.0, 12.0, 4.063447
        90.0, 12.0, 5.523429

        Next, we repeat the above calculations using resistances suitable for vegetated
        surfaces (note that this also changes the results of the first three response
        units due to correction factor `C` depending on |AerodynamicResistance|):

        >>> factors.actualsurfaceresistance = 80.0
        >>> factors.aerodynamicresistance = 40.0
        >>> for hru in range(7):
        ...     deficit = (factors.saturationvapourpressure[hru] -
        ...                factors.actualvapourpressure[hru])
        ...     evap = model.return_evaporation_penmanmonteith_v1(
        ...         hru, factors.actualsurfaceresistance[hru])
        ...     energygain = fluxes.netradiation[hru] - fluxes.soilheatflux[hru]
        ...     print_vector([energygain, deficit, evap])
        0.0, 0.0, 0.0
        40.0, 0.0, 0.364933
        90.0, 0.0, 0.8211
        0.0, 0.0, 0.0
        0.0, 6.0, 2.469986
        0.0, 12.0, 4.939972
        90.0, 12.0, 5.761072

        The above results are sensitive to the ratio between |ActualSurfaceResistance|
        and |AerodynamicResistance|.  The following example demonstrates this
        sensitivity through varying |ActualSurfaceResistance| over a wide range:

        >>> fluxes.netradiation = 100.0
        >>> factors.actualvapourpressure = 0.0
        >>> factors.actualsurfaceresistance = (
        ...     0.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0)
        >>> for hru in range(7):
        ...     print_vector([factors.actualsurfaceresistance[hru],
        ...                   model.return_evaporation_penmanmonteith_v1(
        ...                       hru, factors.actualsurfaceresistance[hru])])
        0.0, 11.370311
        20.0, 9.144449
        50.0, 7.068767
        100.0, 5.128562
        200.0, 3.31099
        500.0, 1.604779
        1000.0, 0.863312

        One potential pitfall of the given Penman-Monteith equation is that
        |AerodynamicResistance| becomes infinite for zero wind speed.  We protect
        method |Return_Evaporation_PenmanMonteith_V1| against this problem (and the
        less likely problem of zero aerodynamic resistance) by limiting the value of
        |AerodynamicResistance| to the interval :math:`[10^{-6}, 10^6]`:

        >>> factors.actualvapourpressure = 6.0
        >>> factors.actualsurfaceresistance = 80.0
        >>> factors.aerodynamicresistance = (0.0, 1e-6, 1e-3, 1.0, 1e3, 1e6, inf)
        >>> for hru in range(7):
        ...     print_vector([factors.aerodynamicresistance[hru],
        ...                   model.return_evaporation_penmanmonteith_v1(
        ...                       hru, factors.actualsurfaceresistance[hru])])
        0.0, 5.00683
        0.000001, 5.00683
        0.001, 5.006739
        1.0, 4.918573
        1000.0, 0.887816
        1000000.0, 0.001372
        inf, 0.001372

        Now, we change the simulation time step from one day to one hour to demonstrate
        that we can reproduce the first example's results:

        >>> simulationstep("1h")
        >>> fixed.heatofcondensation.restore()
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.actualsurfaceresistance = 0.0
        >>> factors.aerodynamicresistance = 106.0
        >>> for hru in range(7):
        ...     deficit = (factors.saturationvapourpressure[hru] -
        ...                factors.actualvapourpressure[hru])
        ...     evap = 24.0 * model.return_evaporation_penmanmonteith_v1(
        ...         hru, factors.actualsurfaceresistance[hru])
        ...     energygain = fluxes.netradiation[hru] - fluxes.soilheatflux[hru]
        ...     print_vector([energygain, deficit, evap])
        0.0, 0.0, 0.0
        40.0, 0.0, 0.648881
        90.0, 0.0, 1.459982
        0.0, 0.0, 0.0
        0.0, 6.0, 2.031724
        0.0, 12.0, 4.063447
        90.0, 12.0, 5.523429
    """

    CONTROLPARAMETERS = (evap_control.Emissivity,)
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model, k: int, actualsurfaceresistance: float
    ) -> float:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        ar: float = min(max(fac.aerodynamicresistance[k], 1e-6), 1e6)
        t: float = 273.15 + fac.airtemperature[k]
        b: float = (4.0 * con.emissivity * fix.stefanboltzmannconstant) * t**3
        c: float = 1.0 + b * ar / fac.airdensity[k] / fix.heatcapacityair
        return (
            (
                fac.saturationvapourpressureslope[k]
                * (flu.netradiation[k] - flu.soilheatflux[k])
                + (c * fac.airdensity[k] * fix.heatcapacityair)
                * (fac.saturationvapourpressure[k] - fac.actualvapourpressure[k])
                / ar
            )
            / (
                fac.saturationvapourpressureslope[k]
                + fix.psychrometricconstant * c * (1.0 + actualsurfaceresistance / ar)
            )
            / fix.heatofcondensation
        )


class Return_Evaporation_PenmanMonteith_V2(modeltools.Method):
    r"""Calculate the actual evapotranspiration with the Penman-Monteith equation
    according to :cite:t:`ref-Löpmeier2014`.

    Basic equation:

    .. math::
      f_{PM}(r_s) =
      \frac{P'_s \cdot (R_n - G) + \rho \cdot c_p \cdot (P_s - P_a) / r_a}
      {H \cdot (P'_s + \gamma \cdot (1 + r_s / r_a))} \\
      \\
      r_s = actualsurfaceresistance \\
      P'_s = SaturationVapourPressureSlope  \\
      R_n = NetRadiation \\
      G = SoilHeatFlux \\
      \rho = AirDensitiy  \\
      c_p = HeatCapacityAir \\
      P_s = SaturationVapourPressure \\
      P_a = ActualVapourPressure \\
      r_a = AerodynamicResistance \\
      H = HeatOfCondensation \\
      \gamma = PsychrometricConstant

    Example:

        Method |Return_Evaporation_PenmanMonteith_V2| equals method
        |Return_Evaporation_PenmanMonteith_V1| except in neglecting the correction
        term `C`.  We repeat the examples of |Return_Evaporation_PenmanMonteith_V1| to
        demonstrate the effects of this difference:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(7)
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> fluxes.soilheatflux = 10.0
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.airdensity = 1.24
        >>> factors.actualsurfaceresistance = 0.0
        >>> factors.aerodynamicresistance = 106.0

        The estimated evapotranspiration values of method
        |Return_Evaporation_PenmanMonteith_V2| are slightly larger for the first three
        hydrological response units with pure energy forcing and smaller for response
        units four to six with pure dynamic forcing:

        >>> from hydpy import print_vector
        >>> for hru in range(7):
        ...     energygain = fluxes.netradiation[hru] - fluxes.soilheatflux[hru]
        ...     vapourdeficit = (factors.saturationvapourpressure[hru] -
        ...                      factors.actualvapourpressure[hru])
        ...     evap = model.return_evaporation_penmanmonteith_v2(
        ...         hru, factors.actualsurfaceresistance[hru])
        ...     print_vector([energygain, vapourdeficit, evap])
        0.0, 0.0, 0.0
        40.0, 0.0, 0.771689
        90.0, 0.0, 1.7363
        0.0, 0.0, 0.0
        0.0, 6.0, 1.701082
        0.0, 12.0, 3.402164
        90.0, 12.0, 5.138464

        This pattern stays the same using resistances suitable for vegetated surfaces:

        >>> factors.actualsurfaceresistance = 80.0
        >>> factors.aerodynamicresistance = 40.0
        >>> for hru in range(7):
        ...     energygain = fluxes.netradiation[hru] - fluxes.soilheatflux[hru]
        ...     vapourdeficit = (factors.saturationvapourpressure[hru] -
        ...                      factors.actualvapourpressure[hru])
        ...     evap = model.return_evaporation_penmanmonteith_v2(
        ...         hru, factors.actualsurfaceresistance[hru])
        ...     print_vector([energygain, vapourdeficit, evap])
        0.0, 0.0, 0.0
        40.0, 0.0, 0.406078
        90.0, 0.0, 0.913677
        0.0, 0.0, 0.0
        0.0, 6.0, 2.372133
        0.0, 12.0, 4.744266
        90.0, 12.0, 5.657942

        The following example shows that |Return_Evaporation_PenmanMonteith_V2| also
        restricts the aerodynamic resistance to the interval :math:`[10^{-6}, 10^6]` and
        that the missing `C` term prevents the estimated evapotranspiration from
        converging to zero with rising aerodynamic resistance:

        >>> fluxes.netradiation = 100.0
        >>> factors.actualvapourpressure = 6.0
        >>> factors.actualsurfaceresistance = 80.0
        >>> factors.aerodynamicresistance = (0.0, 1e-6, 1e-3, 1.0, 1e3, 1e6, inf)
        >>> for hru in range(7):
        ...     print_vector([factors.aerodynamicresistance[hru],
        ...                   model.return_evaporation_penmanmonteith_v2(
        ...                       hru, factors.actualsurfaceresistance[hru])])
        0.0, 5.00683
        0.000001, 5.00683
        0.001, 5.006739
        1.0, 4.91847
        1000.0, 1.849989
        1000000.0, 1.736417
        inf, 1.736417

        Now, we change the simulation time step from one day to one hour to demonstrate
        that we can reproduce the first example's results:

        >>> simulationstep("1h")
        >>> fixed.heatofcondensation.restore()
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.actualsurfaceresistance = 0.0
        >>> factors.aerodynamicresistance = 106.0
        >>> for hru in range(7):
        ...     energygain = fluxes.netradiation[hru] - fluxes.soilheatflux[hru]
        ...     vapourdeficit = (factors.saturationvapourpressure[hru] -
        ...                      factors.actualvapourpressure[hru])
        ...     evap = 24.0 * model.return_evaporation_penmanmonteith_v2(
        ...         hru, factors.actualsurfaceresistance[hru])
        ...     print_vector([energygain, vapourdeficit, evap])
        0.0, 0.0, 0.0
        40.0, 0.0, 0.771689
        90.0, 0.0, 1.7363
        0.0, 0.0, 0.0
        0.0, 6.0, 1.701082
        0.0, 12.0, 3.402164
        90.0, 12.0, 5.138464
    """

    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )

    @staticmethod
    def __call__(
        model: modeltools.Model, k: int, actualsurfaceresistance: float
    ) -> float:
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        ar: float = min(max(fac.aerodynamicresistance[k], 1e-6), 1e6)
        return (
            (
                fac.saturationvapourpressureslope[k]
                * (flu.netradiation[k] - flu.soilheatflux[k])
                + (fac.airdensity[k] * fix.heatcapacityair)
                * (fac.saturationvapourpressure[k] - fac.actualvapourpressure[k])
                / ar
            )
            / (
                fac.saturationvapourpressureslope[k]
                + fix.psychrometricconstant * (1.0 + actualsurfaceresistance / ar)
            )
        ) / fix.heatofcondensation


class Calc_ReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the reference evapotranspiration constant according to
    :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 6):
      :math:`ReferenceEvapotranspiration =
      \frac{
      0.408 \cdot SaturationVapourPressureSlope \cdot (NetRadiation - SoilHeatFlux) +
      PsychrometricConstant \cdot
      \frac{37.5 \cdot Hours}{AirTemperature + 273}
      \cdot WindSpeed2m \cdot (SaturationVapourPressure - ActualVapourPressure)
      }
      {
      SaturationVapourPressureSlope +
      PsychrometricConstant \cdot (1 + 0.34 \cdot WindSpeed2m)
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
        >>> factors.airtemperature = 16.9
        >>> factors.windspeed2m = 2.078
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
        >>> factors.airtemperature = 38.0
        >>> factors.windspeed2m = 3.3
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
    DERIVEDPARAMETERS = (evap_derived.Days, evap_derived.Hours)
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.PsychrometricConstant,
        evap_factors.AirTemperature,
        evap_factors.WindSpeed2m,
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
                / (fac.airtemperature[k] + 273.0)
                * fac.windspeed2m
                * (fac.saturationvapourpressure[k] - fac.actualvapourpressure[k])
            ) / (
                fac.saturationvapourpressureslope[k]
                + fac.psychrometricconstant * (1.0 + 0.34 * fac.windspeed2m)
            )


class Calc_ReferenceEvapotranspiration_V2(modeltools.Method):
    r"""Calculate reference evapotranspiration after Turc-Wendling.

    Basic equation:
      :math:`ReferenceEvapotranspiration =
      \frac{(8.64 \cdot GlobalRadiation + 93 \cdot CoastFactor) \cdot
      (AirTemperature + 22)}
      {165 \cdot (AirTemperature + 123) \cdot
      (1 + 0.00019 \cdot min(Altitude, 600))}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> coastfactor(0.6)
        >>> hrualtitude(200.0, 600.0, 1000.0)
        >>> factors.airtemperature = 15.0
        >>> fluxes.globalradiation = 200.0
        >>> model.calc_referenceevapotranspiration_v2()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.792463, 2.601954, 2.601954)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUAltitude,
        evap_control.CoastFactor,
    )
    REQUIREDSEQUENCES = (evap_factors.AirTemperature, evap_fluxes.GlobalRadiation)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = (
                (8.64 * flu.globalradiation + 93.0 * con.coastfactor[k])
                * (fac.airtemperature[k] + 22.0)
            ) / (
                165.0
                * (fac.airtemperature[k] + 123.0)
                * (1.0 + 0.00019 * min(con.hrualtitude[k], 600.0))
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


class Calc_ReferenceEvapotranspiration_PETModel_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    reference evapotranspiration.

    Example:

        We use |evap_ret_tw2002| as an example:

        >>> from hydpy.models.evap_pet_mlc import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_retmodel_v1("evap_ret_tw2002"):
        ...     hrualtitude(200.0, 600.0, 1000.0)
        ...     coastfactor(0.6)
        ...     evapotranspirationfactor(1.1)
        ...     fluxes.globalradiation = 200.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         temperatureaddend(1.0)
        ...         inputs.temperature = 14.0
        >>> model.calc_referenceevapotranspiration_v4()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.07171, 2.86215, 2.86215)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialevapotranspiration()
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = (
                submodel.get_potentialevapotranspiration(k)
            )


class Calc_ReferenceEvapotranspiration_V4(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    reference evapotranspiration."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMETHODS = (Calc_ReferenceEvapotranspiration_PETModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.retmodel_typeid == 1:
            model.calc_referenceevapotranspiration_petmodel_v1(
                cast(petinterfaces.PETModel_V1, model.retmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_ReferenceEvapotranspiration_V5(modeltools.Method):
    r"""Adjust the normal evapotranspiration to the difference between actual air
    temperature and normal air temperature :cite:p:`ref-Lindstrom1997HBV96`.

    Basic equation:
      :math:`ReferenceEvapotranspiration = NormalEvapotranspiration \cdot
      (1 + AirTemperatureFactor \cdot (MeanAirTemperature - NormalAirTemperature))`

    Restriction:
      :math:`0 \leq ReferenceEvapotranspiration \leq 2 \cdot NormalEvapotranspiration`

    Examples:

        We prepare four hydrological response units with different values for the
        |AirTemperatureFactor| (the negative value of the first unit is not meaningful
        but applied for illustration):

        >>> from hydpy.models.evap import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbhru(4)
        >>> airtemperaturefactor(-0.5, 0.0, 0.1, 0.5)
        >>> inputs.normalairtemperature = 20.0
        >>> inputs.normalevapotranspiration = 2.0

        With actual temperature equal to normal temperature, actual (uncorrected)
        evapotranspiration equals normal evapotranspiration:

        >>> factors.meanairtemperature = 20.0
        >>> model.calc_referenceevapotranspiration_v5()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.0, 2.0, 2.0, 2.0)

        For an actual temperature of 5 °C higher than normal, reference
        evapotranspiration is increased by 1 mm for the third unit.  For the first
        unit, reference evapotranspiration is 0 mm (the smallest value allowed), and
        for the fourth unit, it is the doubled normal value (the largest value
        allowed):

        >>> factors.meanairtemperature  = 25.0
        >>> model.calc_referenceevapotranspiration_v5()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(0.0, 2.0, 3.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.AirTemperatureFactor)
    REQUIREDSEQUENCES = (
        evap_inputs.NormalEvapotranspiration,
        evap_inputs.NormalAirTemperature,
        evap_factors.MeanAirTemperature,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = inp.normalevapotranspiration * (
                1.0
                + con.airtemperaturefactor[k]
                * (fac.meanairtemperature - inp.normalairtemperature)
            )
            flu.referenceevapotranspiration[k] = min(
                max(flu.referenceevapotranspiration[k], 0.0),
                2.0 * inp.normalevapotranspiration,
            )


class Calc_PotentialEvapotranspiration_V1(modeltools.Method):
    r"""Calculate month-specific potential evaporation based on reference
    evapotranspiration.

    Basic equation:
      :math:`PotentialEvapotranspiration = MonthFactor \cdot
      ReferenceEvapotranspiration`

    Examples:

        >>> from hydpy import pub, UnitTest
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> monthfactor.mar = 0.5
        >>> monthfactor.apr = 2.0
        >>> derived.moy.update()
        >>> fluxes.referenceevapotranspiration = 1.0, 2.0
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> model.calc_potentialevapotranspiration_v1()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(0.5, 1.0)
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> model.calc_potentialevapotranspiration_v1()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(2.0, 4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.MonthFactor)
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            factor: float = con.monthfactor[
                der.moy[model.idx_sim] - con._monthfactor_entrymin
            ]
            flu.potentialevapotranspiration[k] = (
                factor * flu.referenceevapotranspiration[k]
            )


class Calc_PotentialEvapotranspiration_V2(modeltools.Method):
    r"""Calculate month- and land cover-specific potential evaporation based on
    reference evapotranspiration.

    Basic equation:
      :math:`PotentialEvapotranspiration = LandMonthFactor \cdot
      ReferenceEvapotranspiration`

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types of grass, trees, and water to apply |evap| as a stand-alone model:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.core.parametertools import Constants
        >>> GRASS, TREES, WATER = 1, 2, 3
        >>> constants = Constants(GRASS=GRASS, TREES=TREES, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType, LandMonthFactor
        >>> with HRUType.modify_constants(constants), \
        ...         LandMonthFactor.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(2)
        >>> hrutype(TREES, WATER)
        >>> landmonthfactor.trees_mar = 1.0
        >>> landmonthfactor.trees_apr = 2.0
        >>> landmonthfactor.water_mar = 0.5
        >>> landmonthfactor.water_apr = 2.0
        >>> derived.moy.update()
        >>> fluxes.referenceevapotranspiration = 1.0, 2.0
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> model.calc_potentialevapotranspiration_v2()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(1.0, 1.0)
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> model.calc_potentialevapotranspiration_v2()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(2.0, 4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.LandMonthFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            factor: float = con.landmonthfactor[
                con.hrutype[k] - con._landmonthfactor_rowmin,
                der.moy[model.idx_sim] - con._landmonthfactor_columnmin,
            ]
            flu.potentialevapotranspiration[k] = (
                factor * flu.referenceevapotranspiration[k]
            )


class Calc_PotentialEvapotranspiration_V3(modeltools.Method):
    r"""Apply the altitude- and precipitation-related adjustment factors on reference
    evapotranspiration to determine potential evapotranspiration
    :cite:p:`ref-Lindstrom1997HBV96`.

    Basic equation:
      .. math::
        PotentialEvapotranspiration = ReferenceEvapotranspiration \cdot
        \left(1 + AltitudeFactor \cdot \frac{HRUAltitude - Altitude}{100} \right) \cdot
        exp(-PrecipitationFactor \cdot Precipitation)

    Examples:

        Three hydrological response units are at an altitude of 300 m (but the entire
        basin's mean altitude is 200 m, for illustration purposes).  A reference
        evapotranspiration value of 2 mm and a precipitation value of 5 mm are
        available at each unit:

        >>> from hydpy.models.evap import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbhru(3)
        >>> hrualtitude(300.0)
        >>> fluxes.referenceevapotranspiration = 2.0
        >>> fluxes.precipitation = 5.0
        >>> derived.altitude(200.0)

        The first two units illustrate the individual altitude-related
        (|AltitudeFactor|, first unit) and the precipitation-related adjustments
        (|PrecipitationFactor|, second unit).  The third zone illustrates the
        interaction between both adjustments:

        >>> import math
        >>> altitudefactor(0.1, 0.0, 0.1)
        >>> precipitationfactor(0.0, -math.log(0.7)/10.0, -math.log(0.7)/10.0)
        >>> model.calc_potentialevapotranspiration_v3()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(1.8, 1.4, 1.26)

        Method |Calc_PotentialEvapotranspiration_V3| performs truncations required to
        prevent negative potential evapotranspiration:

        >>> altitudefactor(2.0)
        >>> model.calc_potentialevapotranspiration_v3()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.AltitudeFactor,
        evap_control.HRUAltitude,
        evap_control.PrecipitationFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.Altitude,)
    REQUIREDSEQUENCES = (
        evap_fluxes.ReferenceEvapotranspiration,
        evap_fluxes.Precipitation,
    )
    RESULTSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.potentialevapotranspiration[k] = flu.referenceevapotranspiration[k] * (
                1.0
                - con.altitudefactor[k] / 100.0 * (con.hrualtitude[k] - der.altitude)
            )
            if flu.potentialevapotranspiration[k] <= 0.0:
                flu.potentialevapotranspiration[k] = 0.0
            else:
                flu.potentialevapotranspiration[k] *= modelutils.exp(
                    -con.precipitationfactor[k] * flu.precipitation[k]
                )


class Update_PotentialEvapotranspiration_V1(modeltools.Method):
    r"""Damp the given potential evapotranspiration and update the corresponding log
    sequence.

    Basic equation:
      .. math::
        E_{mod, new} = \omega \cdot E_{orig, new} + (1 - \omega) \cdot E_{mod, old}
        \\ \\
        \omega = DampingFactor \\
        E = PotentialEvapotranspiration

    Example:

        We prepare four hydrological response units with different combinations of
        damping factors and "old" potential evapotranspiration values:

        >>> from hydpy.models.evap import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbhru(4)
        >>> dampingfactor(2.0, 2.0, 0.2, 0.2)
        >>> fluxes.potentialevapotranspiration = 1.6, 2.4, 1.6, 2.4

        Note that the time-dependent parameter value is reduced due to the difference
        between the given parameter and the simulation step:

        >>> from hydpy import round_
        >>> round_(dampingfactor.values)
        1.0, 1.0, 0.1, 0.1

        The evaporation value of the last simulation step is 2.0 mm:

        >>> logs.loggedpotentialevapotranspiration = 2.0

        For the first two hydrological response units, the "old" potential
        evapotranspiration is modified by -0.4 mm and +0.4 mm, respectively.  For the
        other two response units, which weigh the "new" value with 10 %, the new value
        deviates from its logged counterpart only by -0.04 mm and +0.04 mm:

        >>> model.update_potentialevapotranspiration_v1()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(1.6, 2.4, 1.96, 2.04)
        >>> logs.loggedpotentialevapotranspiration
        loggedpotentialevapotranspiration(1.6, 2.4, 1.96, 2.04)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.DampingFactor)
    UPDATEDSEQUENCES = (
        evap_fluxes.PotentialEvapotranspiration,
        evap_logs.LoggedPotentialEvapotranspiration,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for k in range(con.nmbhru):
            flu.potentialevapotranspiration[k] = (
                con.dampingfactor[k] * flu.potentialevapotranspiration[k]
                + (1.0 - con.dampingfactor[k])
                * log.loggedpotentialevapotranspiration[0, k]
            )
            log.loggedpotentialevapotranspiration[0, k] = (
                flu.potentialevapotranspiration[k]
            )


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

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.EvapotranspirationFactor)
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


class Calc_MeanPotentialEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the average potential evapotranspiration.

    Basic equation:
      :math:`MeanPotentialEvapotranspiration =
      \sum_{i=1}^{NmbHRU} HRUAreaFraction_i \cdot PotentialEvapotranspiration_i`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.hruareafraction(0.8, 0.2)
        >>> fluxes.potentialevapotranspiration = 1.0, 2.0
        >>> model.calc_meanpotentialevapotranspiration_v1()
        >>> fluxes.meanpotentialevapotranspiration
        meanpotentialevapotranspiration(1.2)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.HRUAreaFraction,)
    REQUIREDSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.MeanPotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.meanpotentialevapotranspiration = 0.0
        for s in range(con.nmbhru):
            flu.meanpotentialevapotranspiration += (
                der.hruareafraction[s] * flu.potentialevapotranspiration[s]
            )


class Calc_PotentialWaterEvaporation_PETModel_V1(modeltools.Method):
    """Query the already calculated potential evapotranspiration from a submodel that
    complies with the |PETModel_V1| interface and assume it to be water evaporation.

    Example:

        We use |evap_aet_minhas| and |evap_ret_io| as an example:

        >>> from hydpy.models.evap_aet_minhas import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> with model.add_petmodel_v1("evap_ret_io"):
        ...     hruarea(1.0, 3.0, 2.0)
        ...     fluxes.referenceevapotranspiration = 1.0, 2.0, 4.0
        >>> model.calc_potentialwaterevaporation_v1()
        >>> fluxes.potentialwaterevaporation
        potentialwaterevaporation(1.0, 2.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialWaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.potentialwaterevaporation[k] = submodel.get_potentialevapotranspiration(
                k
            )


class Calc_PotentialWaterEvaporation_PETModel_V2(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V2| interface calculate
    potential water evaporation and query it.

    Example:

        We use |evap_aet_minhas| and |evap_pet_ambav1| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_aet_minhas import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> interception(False, False, True)
        >>> soil(False, False, True)
        >>> water(True, True, False)
        >>> with model.add_petmodel_v2("evap_pet_ambav1"):
        ...     hrutype(0)
        ...     plant(False)
        ...     measuringheightwindspeed(10.0)
        ...     groundalbedo(0.2)
        ...     groundalbedosnow(0.8)
        ...     leafalbedo(0.2)
        ...     leafalbedosnow(0.8)
        ...     leafareaindex(5.0)
        ...     cropheight(0.0)
        ...     cloudtypefactor(0.2)
        ...     nightcloudfactor(1.0)
        ...     inputs.relativehumidity = 80.0
        ...     inputs.windspeed = 2.0
        ...     inputs.atmosphericpressure = 1000.0
        ...     factors.sunshineduration = 6.0
        ...     factors.possiblesunshineduration = 16.0
        ...     fluxes.globalradiation = 190.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         hruarea(1.0)
        ...         temperatureaddend(0.0, 15.0, 0.0)
        ...         inputs.temperature = 15.0
        ...     with model.add_precipmodel_v2("meteo_precip_io"):
        ...         hruarea(1.0)
        ...         precipitationfactor(1.0)
        ...         inputs.precipitation = 0.0
        ...     with model.add_snowcovermodel_v1("dummy_snowcover"):
        ...         inputs.snowcover = 0.0

        >>> model.petmodel.determine_potentialinterceptionevaporation()
        >>> model.calc_potentialwaterevaporation_v1()
        >>> fluxes.potentialwaterevaporation
        potentialwaterevaporation(1.890672, 3.204855, 0.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialWaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V2) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialwaterevaporation()
        for k in range(con.nmbhru):
            flu.potentialwaterevaporation[k] = submodel.get_potentialwaterevaporation(k)


class Calc_PotentialWaterEvaporation_V1(modeltools.Method):
    """Use a submodel that complies with the |PETModel_V1| or |PETModel_V2| interface
    to determine potential soil evapotranspiration."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1, petinterfaces.PETModel_V2)
    SUBMETHODS = (
        Calc_PotentialWaterEvaporation_PETModel_V1,
        Calc_PotentialWaterEvaporation_PETModel_V2,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialWaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.petmodel_typeid == 1:
            model.calc_potentialwaterevaporation_petmodel_v1(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )
        elif model.petmodel_typeid == 2:
            model.calc_potentialwaterevaporation_petmodel_v2(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )


class Calc_WaterEvaporation_V1(modeltools.Method):
    r"""Calculate the actual evaporation from water areas according to
    :cite:t:`ref-Lindstrom1997HBV96`.

    Basic equation:
      .. math::
        WaterEvaporation =
        \begin{cases}
        PotentialWaterEvaporation &|\ AirTemperature > TemperatureThresholdIce
        \\
        0 &|\ AirTemperature \leq TemperatureThresholdIce
        \end{cases}

    Example:

        The occurrence of an ice layer on the water's surface prohibits evaporation
        completely:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> water(True)
        >>> temperaturethresholdice(1.0)
        >>> factors.airtemperature = 0.0, 1.0, 2.0
        >>> fluxes.potentialwaterevaporation = 3.0
        >>> model.calc_waterevaporation_v1()
        >>> fluxes.waterevaporation
        waterevaporation(0.0, 0.0, 3.0)

        For non-water areas, water area evaporation is generally zero:

        >>> water(False)
        >>> model.calc_waterevaporation_v1()
        >>> fluxes.waterevaporation
        waterevaporation(0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Water,
        evap_control.TemperatureThresholdIce,
    )
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
        evap_fluxes.PotentialWaterEvaporation,
    )
    RESULTSEQUENCES = (evap_fluxes.WaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.water[k] and fac.airtemperature[k] > con.temperaturethresholdice[k]:
                flu.waterevaporation[k] = flu.potentialwaterevaporation[k]
            else:
                flu.waterevaporation[k] = 0.0


class Calc_WaterEvaporation_V2(modeltools.Method):
    """Accept potential evaporation from water areas as the actual one.

    Basic equation:
      :math:`WaterEvaporation = PotentialWaterEvaporation`

    Example:

        For non-water areas, water area evaporation is generally zero:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> water(True, False)
        >>> fluxes.potentialwaterevaporation = 3.0
        >>> model.calc_waterevaporation_v2()
        >>> fluxes.waterevaporation
        waterevaporation(3.0, 0.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Water)
    REQUIREDSEQUENCES = (evap_fluxes.PotentialWaterEvaporation,)
    RESULTSEQUENCES = (evap_fluxes.WaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.water[k]:
                flu.waterevaporation[k] = flu.potentialwaterevaporation[k]
            else:
                flu.waterevaporation[k] = 0.0


class Calc_WaterEvaporation_V3(modeltools.Method):
    r"""Calculate the actual evaporation from water areas with the Penman equation
    according to :cite:t:`ref-LARSIM`, based on :cite:t:`ref-DVWK1996`.

    Basic equation:
      .. math::
        WaterEvaporation = \frac{P'_s\cdot R_n / H +
        Days \cdot \gamma\cdot (0.13 + 0.094 \cdot v) \cdot (P_s- P_a)}
        {P'_s+ \gamma} \\
        \\
        P'_s = DailySaturationVapourPressureSlope \\
        R_n = DailyNetRadiation \\
        H = HeatOfCondensation \\
        \gamma  = PsychrometricConstant \\
        v = DailyWindSpeed2m \\
        P_s = DailySaturationVapourPressure \\
        P_a = DailyActualVapourPressure

    Examples:

        We initialise seven hydrological response units.  In response units one to
        three, evaporation is due to radiative forcing only.  In response units four to
        six, evaporation is due to aerodynamic forcing only.  Response unit seven shows
        the combined effect of both forces:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(7)
        >>> water(True)
        >>> derived.days.update()
        >>> fluxes.dailynetradiation = 0.0, 50.0, 100.0, 0.0, 0.0, 0.0, 100.0
        >>> factors.dailywindspeed2m = 2.0
        >>> factors.dailysaturationvapourpressure = 12.0
        >>> factors.dailysaturationvapourpressureslope = 0.8
        >>> factors.dailyactualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> model.calc_waterevaporation_v3()
        >>> fluxes.waterevaporation
        waterevaporation(0.0, 0.964611, 1.929222, 0.0, 0.858928, 1.717856,
                         3.647077)

        The above results apply to a daily simulation time step.  The following example
        demonstrates that |Calc_WaterEvaporation_V3| calculates equivalent results for
        hourly time steps:

        >>> simulationstep("1h")
        >>> derived.days.update()
        >>> fixed.heatofcondensation.restore()
        >>> model.calc_waterevaporation_v3()
        >>> fluxes.waterevaporation *= 24.0
        >>> fluxes.waterevaporation
        waterevaporation(0.0, 0.964611, 1.929222, 0.0, 0.858928, 1.717856,
                         3.647077)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Water)
    DERIVEDPARAMETERS = (evap_derived.Days,)
    FIXEDPARAMETERS = (evap_fixed.HeatOfCondensation, evap_fixed.PsychrometricConstant)
    REQUIREDSEQUENCES = (
        evap_factors.DailySaturationVapourPressure,
        evap_factors.DailySaturationVapourPressureSlope,
        evap_factors.DailyActualVapourPressure,
        evap_factors.DailyWindSpeed2m,
        evap_fluxes.DailyNetRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.WaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.water[k]:
                flu.waterevaporation[k] = (
                    fac.dailysaturationvapourpressureslope[k]
                    * flu.dailynetradiation[k]
                    / fix.heatofcondensation
                    + fix.psychrometricconstant
                    * der.days
                    * (0.13 + 0.094 * fac.dailywindspeed2m)
                    * (
                        fac.dailysaturationvapourpressure[k]
                        - fac.dailyactualvapourpressure[k]
                    )
                ) / (
                    fac.dailysaturationvapourpressureslope[k]
                    + fix.psychrometricconstant
                )
            else:
                flu.waterevaporation[k] = 0.0


class Calc_WaterEvaporation_V4(modeltools.Method):
    r"""Calculate the evaporation from water areas by applying the Penman-Monteith
    equation with zero surface resistance.

    Basic equation:
      .. math::
        WaterEvaporation = \begin{cases}
        f_{PM}(0.0)  &|\ Water
        \\
        0 &|\ \overline{Water}
        \end{cases}

    Examples:

        Usually, one would not consider soil heat fluxes when calculating evaporation
        from water areas.  However, |Calc_WaterEvaporation_V4| takes |SoilHeatFlux|
        into account, so it should usually be set to zero beforehand. Due to
        considering it, the following results agree with the first example on method
        |Calc_PotentialInterceptionEvaporation_V2|:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(7)
        >>> water(True)
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.airdensity = 1.24
        >>> factors.aerodynamicresistance = 106.0
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> fluxes.soilheatflux = 10.0
        >>> model.calc_waterevaporation_v4()
        >>> fluxes.waterevaporation
        waterevaporation(0.0, 0.771689, 1.7363, 0.0, 1.701082, 3.402164,
                         5.138464)

        Water evaporation is always zero for hydrological response units dealing with
        non-water areas:

        >>> water(False)
        >>> model.calc_waterevaporation_v4()
        >>> fluxes.waterevaporation
        waterevaporation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    SUBMETHODS = (Return_Evaporation_PenmanMonteith_V2,)
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Water)
    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.WaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for k in range(con.nmbhru):
            if con.water[k]:
                evap: float = model.return_evaporation_penmanmonteith_v2(k, 0.0)
                flu.waterevaporation[k] = evap
            else:
                flu.waterevaporation[k] = 0.0


class Update_LoggedWaterEvaporation_V1(modeltools.Method):
    # pylint: disable=line-too-long
    """Log the water evaporation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        six memorised values to the right and stores the respective two new values on
        the leftmost position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedwaterevaporation.shape = 3, 2
        >>> logs.loggedwaterevaporation = 0.0, 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedwaterevaporation_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.waterevaporation,
        ...                          logs.loggedwaterevaporation))
        >>> test.nexts.waterevaporation = [1.0, 2.0], [3.0, 6.0], [2.0, 4.0], [4.0, 8.0]
        >>> del test.inits.loggedwaterevaporation
        >>> test()
        | ex. |      waterevaporation |                          loggedwaterevaporation |
        ---------------------------------------------------------------------------------
        |   1 | 1.0               2.0 | 1.0  2.0  0.0  0.0  0.0                     0.0 |
        |   2 | 3.0               6.0 | 3.0  6.0  1.0  2.0  0.0                     0.0 |
        |   3 | 2.0               4.0 | 2.0  4.0  3.0  6.0  1.0                     2.0 |
        |   4 | 4.0               8.0 | 4.0  8.0  2.0  4.0  3.0                     6.0 |
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_fluxes.WaterEvaporation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedWaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            for k in range(con.nmbhru):
                log.loggedwaterevaporation[idx, k] = log.loggedwaterevaporation[
                    idx - 1, k
                ]
        for k in range(con.nmbhru):
            log.loggedwaterevaporation[0, k] = flu.waterevaporation[k]


class Calc_DailyWaterEvaporation_V1(modeltools.Method):
    """Calculate the water evaporation sum of the last 24 hours.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedwaterevaporation.shape = 3, 2
        >>> logs.loggedwaterevaporation = [[1.0, 2.0], [5.0, 6.0], [3.0, 4.0]]
        >>> model.calc_dailywaterevaporation_v1()
        >>> fluxes.dailywaterevaporation
        dailywaterevaporation(9.0, 12.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_logs.LoggedWaterEvaporation,)
    RESULTSEQUENCES = (evap_fluxes.DailyWaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.dailywaterevaporation[k] = 0.0
        for idx in range(der.nmblogentries):
            for k in range(con.nmbhru):
                flu.dailywaterevaporation[k] += log.loggedwaterevaporation[idx, k]


class Calc_InterceptionEvaporation_V1(modeltools.Method):
    r"""Calculate the actual interception evaporation by setting it equal to potential
    evapotranspiration.

    Basic equation:
      .. math::
        InterceptionEvaporation =
        \begin{cases}
        PotentialInterceptionEvaporation &|\ InterceptedWater > 0
        \\
        0 &|\ InterceptedWater = 0
        \end{cases}

    Examples:

        The availability of intercepted water may restrict the possible interception
        evaporation:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(4)
        >>> interception(True)
        >>> fluxes.potentialinterceptionevaporation(1.0)
        >>> factors.interceptedwater(1.5, 1.0, 0.5, 0.0)
        >>> model.calc_interceptionevaporation_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(1.0, 1.0, 0.5, 0.0)

        Interception evaporation is always zero for hydrological response units not
        considering interception:

        >>> interception(False)
        >>> model.calc_interceptionevaporation_v1()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Interception)
    REQUIREDSEQUENCES = (
        evap_factors.InterceptedWater,
        evap_fluxes.PotentialInterceptionEvaporation,
    )
    RESULTSEQUENCES = (evap_fluxes.InterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.interception[k]:
                flu.interceptionevaporation[k] = min(
                    flu.potentialinterceptionevaporation[k], fac.interceptedwater[k]
                )
            else:
                flu.interceptionevaporation[k] = 0.0


class Calc_PotentialInterceptionEvaporation_V1(modeltools.Method):
    r"""Calculate the potential interception evaporation using an extended
    Penman-Monteith equation with zero surface resistance.

    Basic equation:
      .. math::
        PotentialInterceptionEvaporation = \begin{cases}
        f_{PM}(0.0)  &|\ Interception
        \\
        0 &|\ \overline{Interception}
        \end{cases}

    Examples:

        The following settings agree with the first example on method
        |Return_Evaporation_PenmanMonteith_V1|:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(7)
        >>> interception(True)
        >>> emissivity(0.96)
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.airdensity = 1.24
        >>> factors.aerodynamicresistance = 106.0
        >>> factors.airtemperature = 10.0
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> fluxes.soilheatflux = 10.0
        >>> model.calc_potentialinterceptionevaporation_v1()
        >>> fluxes.potentialinterceptionevaporation
        potentialinterceptionevaporation(0.0, 0.648881, 1.459982, 0.0, 2.031724,
                                         4.063447, 5.523429)

        Interception evaporation is always zero for hydrological response units not
        considering interception:

        >>> interception(False)
        >>> model.calc_potentialinterceptionevaporation_v1()
        >>> fluxes.potentialinterceptionevaporation
        potentialinterceptionevaporation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    SUBMETHODS = (Return_Evaporation_PenmanMonteith_V1,)
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Interception,
        evap_control.Emissivity,
    )
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.PotentialInterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.interception[k]:
                flu.potentialinterceptionevaporation[k] = (
                    model.return_evaporation_penmanmonteith_v1(k, 0.0)
                )
            else:
                flu.potentialinterceptionevaporation[k] = 0.0


class Calc_PotentialInterceptionEvaporation_V2(modeltools.Method):
    r"""Calculate the potential interception evaporation by applying the Penman-Monteith
    equation with zero surface resistance.

    Basic equation:
      .. math::
        PotentialInterceptionEvaporation = \begin{cases}
        f_{PM}(0.0)  &|\ Interception
        \\
        0 &|\ \overline{Interception}
        \end{cases}

    Examples:

        The following settings agree with the first example on method
        |Return_Evaporation_PenmanMonteith_V2|:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(7)
        >>> interception(True)
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 12.0, 12.0, 12.0, 12.0, 6.0, 0.0, 0.0
        >>> factors.airdensity = 1.24
        >>> factors.aerodynamicresistance = 106.0
        >>> fluxes.netradiation = 10.0, 50.0, 100.0, 10.0, 10.0, 10.0, 100.0
        >>> fluxes.soilheatflux = 10.0
        >>> model.calc_potentialinterceptionevaporation_v2()
        >>> fluxes.potentialinterceptionevaporation
        potentialinterceptionevaporation(0.0, 0.771689, 1.7363, 0.0, 1.701082,
                                         3.402164, 5.138464)

        Interception evaporation is always zero for hydrological response units not
        considering interception:

        >>> interception(False)
        >>> model.calc_potentialinterceptionevaporation_v1()
        >>> fluxes.potentialinterceptionevaporation
        potentialinterceptionevaporation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    SUBMETHODS = (Return_Evaporation_PenmanMonteith_V2,)
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Interception)
    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.PotentialInterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.interception[k]:
                evap: float = model.return_evaporation_penmanmonteith_v2(k, 0.0)
                flu.potentialinterceptionevaporation[k] = evap
            else:
                flu.potentialinterceptionevaporation[k] = 0.0


class Calc_PotentialInterceptionEvaporation_PETModel_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate
    potential evapotranspiration and assume it as potential interception evaporation.

    Example:

        We use |evap_aet_minhas| and |evap_ret_io| as an example:

        >>> from hydpy.models.evap_aet_minhas import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> with model.add_petmodel_v1("evap_ret_io"):
        ...     hruarea(1.0, 3.0, 2.0)
        ...     evapotranspirationfactor(0.5, 1.0, 2.0)
        ...     inputs.referenceevapotranspiration = 2.0
        >>> model.calc_potentialinterceptionevaporation_v3()
        >>> fluxes.potentialinterceptionevaporation
        potentialinterceptionevaporation(1.0, 2.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialInterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialevapotranspiration()
        for k in range(con.nmbhru):
            flu.potentialinterceptionevaporation[k] = (
                submodel.get_potentialevapotranspiration(k)
            )


class Calc_PotentialInterceptionEvaporation_PETModel_V2(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V2| interface calculate
    potential interception evaporation and query it.

    Example:

        We use |evap_aet_minhas| and |evap_pet_ambav1| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_aet_minhas import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> interception(False, True, True)
        >>> soil(False, True, True)
        >>> water(True, False, False)
        >>> with model.add_petmodel_v2("evap_pet_ambav1"):
        ...     hrutype(0)
        ...     plant(True)
        ...     measuringheightwindspeed(10.0)
        ...     groundalbedo(0.2)
        ...     groundalbedosnow(0.8)
        ...     leafalbedo(0.2)
        ...     leafalbedosnow(0.8)
        ...     leafareaindex(5.0)
        ...     cropheight(10.0)
        ...     cloudtypefactor(0.2)
        ...     nightcloudfactor(1.0)
        ...     inputs.relativehumidity = 80.0
        ...     inputs.windspeed = 2.0
        ...     inputs.atmosphericpressure = 1000.0
        ...     factors.sunshineduration = 6.0
        ...     factors.possiblesunshineduration = 16.0
        ...     fluxes.globalradiation = 190.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         hruarea(1.0)
        ...         temperatureaddend(0.0)
        ...         inputs.temperature = 15.0
        ...     with model.add_precipmodel_v2("meteo_precip_io"):
        ...         hruarea(1.0)
        ...         precipitationfactor(1.0)
        ...         inputs.precipitation = 0.0
        ...     with model.add_snowcovermodel_v1("dummy_snowcover"):
        ...         inputs.snowcover = 0.0, 0.0, 1.0
        >>> model.calc_potentialinterceptionevaporation_v3()
        >>> fluxes.potentialinterceptionevaporation
        potentialinterceptionevaporation(0.0, 3.301949, 1.146759)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialInterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V2) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialinterceptionevaporation()
        for k in range(con.nmbhru):
            flu.potentialinterceptionevaporation[k] = (
                submodel.get_potentialinterceptionevaporation(k)
            )


class Calc_PotentialInterceptionEvaporation_V3(modeltools.Method):
    """Use a submodel that complies with the |PETModel_V1| or |PETModel_V2| interface
    to determine evaporation from water areas."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1, petinterfaces.PETModel_V2)
    SUBMETHODS = (
        Calc_PotentialInterceptionEvaporation_PETModel_V1,
        Calc_PotentialInterceptionEvaporation_PETModel_V2,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialInterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.petmodel_typeid == 1:
            model.calc_potentialinterceptionevaporation_petmodel_v1(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )
        elif model.petmodel_typeid == 2:
            model.calc_potentialinterceptionevaporation_petmodel_v2(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )


class Calc_InterceptionEvaporation_V2(modeltools.Method):
    r"""Calculate the actual interception evaporation by setting it equal to potential
    interception evaporation.

    Basic equation:
      .. math::
        InterceptionEvaporation =
        \begin{cases}
        min(PotentialInterceptionEvaporation, \ InterceptedWater) &|\
        Interception \land ( Tree \lor SnowCover = 0 )
        \\
        0 &|\ \overline{Interception} \lor ( \overline{Tree} \land SnowCover > 0 )
        \end{cases}

    Examples:

        We prepare two hydrological response units.  The first one is tree-like, while
        the second one is not:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(2)
        >>> interception(True)
        >>> tree(True, False)
        >>> factors.interceptedwater = 1.0
        >>> fluxes.potentialinterceptionevaporation = 1.0

        Without any snow cover, the vegetation type does not make a difference:

        >>> factors.snowcover = 0.0
        >>> factors.snowycanopy = 0.0, nan
        >>> model.calc_interceptionevaporation_v2()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(1.0, 1.0)

        For tree-like vegetation, a snow layer (on the ground) does not affect
        interception evaporation.  For other vegetation types, even incomplete covering
        suppresses interception evaporation completely:

        >>> factors.snowcover = 0.1
        >>> model.calc_interceptionevaporation_v2()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(1.0, 0.0)

        For tree-like vegetation, snow interception (in the canopy) suppresses
        interception evaporation completely:

        >>> factors.snowcover = 0.0
        >>> factors.snowycanopy = 1.0
        >>> model.calc_interceptionevaporation_v2()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(0.0, 1.0)

        The availability of intercepted water may restrict the possible interception
        evaporation:

        >>> factors.snowycanopy = 0.0
        >>> factors.interceptedwater = 0.5, 0.0
        >>> model.calc_interceptionevaporation_v2()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(0.5, 0.0)

        Interception evaporation is always zero for hydrological response units not
        considering interception:

        >>> interception(False)
        >>> model.calc_interceptionevaporation_v2()
        >>> fluxes.interceptionevaporation
        interceptionevaporation(0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Interception,
        evap_control.Tree,
    )
    REQUIREDSEQUENCES = (
        evap_factors.InterceptedWater,
        evap_factors.SnowCover,
        evap_factors.SnowyCanopy,
        evap_fluxes.PotentialInterceptionEvaporation,
    )
    RESULTSEQUENCES = (evap_fluxes.InterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if (
                con.interception[k]
                and (con.tree[k] or (fac.snowcover[k] == 0.0))
                and not (con.tree[k] and (fac.snowycanopy[k] > 0.0))
            ):
                flu.interceptionevaporation[k] = min(
                    flu.potentialinterceptionevaporation[k], fac.interceptedwater[k]
                )
            else:
                flu.interceptionevaporation[k] = 0.0


class Calc_PotentialSoilEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the potential evapotranspiration from the soil by applying the
    Penman-Monteith equation with an actual surface resistance that does not consider
    the current soil moisture.

    Basic equation:
      .. math::
        PotentialSoilEvapotranspiration = \begin{cases}
        f_{PM}(ActualSurfaceResistance)  &|\ Soil
        \\
        0 &|\ \overline{Soil}
        \end{cases}

    Examples:

        We prepare two hydrological response units, of which only the first one's soil
        is accessible for evapotranspiration losses.  The other settings agree with the
        last response unit in the second example on method
        |Return_Evaporation_PenmanMonteith_V2|:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(2)
        >>> soil(True, False)
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 0.0
        >>> factors.airdensity = 1.24
        >>> factors.aerodynamicresistance = 40.0
        >>> factors.actualsurfaceresistance = 80.0
        >>> fluxes.netradiation = 100.0
        >>> fluxes.soilheatflux = 10.0

        The determined potential evapotranspiration value for the first response unit
        agrees with the corresponding |Return_Evaporation_PenmanMonteith_V2| example.
        For the soil-free unit, it is zero:

        >>> model.calc_potentialsoilevapotranspiration_v1()
        >>> fluxes.potentialsoilevapotranspiration
        potentialsoilevapotranspiration(5.657942, 0.0)
    """

    SUBMETHODS = (Return_Evaporation_PenmanMonteith_V2,)
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Soil)
    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_factors.ActualSurfaceResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.PotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                r: float = fac.actualsurfaceresistance[k]
                pet: float = model.return_evaporation_penmanmonteith_v2(k, r)
                flu.potentialsoilevapotranspiration[k] = pet
            else:
                flu.potentialsoilevapotranspiration[k] = 0.0


class Calc_PotentialSoilEvapotranspiration_PETModel_V1(modeltools.Method):
    """Query the already calculated potential evapotranspiration from a submodel that
    complies with the |PETModel_V1| interface and assume it as potential soil
    evapotranspiration.

    Example:

        We use |evap_aet_minhas| and |evap_ret_io| as an example:

        >>> from hydpy.models.evap_aet_minhas import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> with model.add_petmodel_v1("evap_ret_io"):
        ...     hruarea(1.0, 3.0, 2.0)
        ...     fluxes.referenceevapotranspiration = 1.0, 2.0, 4.0
        >>> model.calc_potentialsoilevapotranspiration_v2()
        >>> fluxes.potentialsoilevapotranspiration
        potentialsoilevapotranspiration(1.0, 2.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.potentialsoilevapotranspiration[k] = (
                submodel.get_potentialevapotranspiration(k)
            )


class Calc_PotentialSoilEvapotranspiration_PETModel_V2(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V2| interface calculate
    potential soil evapotranspiration and query it.

    Example:

        We use |evap_aet_minhas| and |evap_pet_ambav1| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_aet_minhas import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> interception(False, True, True)
        >>> soil(False, True, True)
        >>> water(True, False, False)
        >>> with model.add_petmodel_v2("evap_pet_ambav1"):
        ...     hrutype(0)
        ...     plant(True)
        ...     measuringheightwindspeed(10.0)
        ...     leafalbedo(0.2)
        ...     leafalbedosnow(0.8)
        ...     groundalbedo(0.2)
        ...     groundalbedosnow(0.8)
        ...     leafareaindex(5.0)
        ...     cropheight(10.0)
        ...     leafresistance(40.0)
        ...     wetsoilresistance(100.0)
        ...     soilresistanceincrease(1.0)
        ...     wetnessthreshold(0.5)
        ...     cloudtypefactor(0.2)
        ...     nightcloudfactor(1.0)
        ...     inputs.relativehumidity = 80.0
        ...     inputs.windspeed = 2.0
        ...     inputs.atmosphericpressure = 1000.0
        ...     factors.sunshineduration = 6.0
        ...     factors.possiblesunshineduration = 16.0
        ...     fluxes.globalradiation = 190.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         hruarea(1.0)
        ...         temperatureaddend(0.0)
        ...         inputs.temperature = 15.0
        ...     with model.add_precipmodel_v2("meteo_precip_io"):
        ...         hruarea(1.0)
        ...         precipitationfactor(1.0)
        ...         inputs.precipitation = 0.0
        ...     with model.add_snowcovermodel_v1("dummy_snowcover"):
        ...         inputs.snowcover = 0.0, 0.0, 1.0
        >>> model.petmodel.determine_potentialinterceptionevaporation()
        >>> model.calc_potentialsoilevapotranspiration_v2()
        >>> fluxes.potentialsoilevapotranspiration
        potentialsoilevapotranspiration(0.0, 2.324763, 0.807385)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V2) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialsoilevapotranspiration()
        for k in range(con.nmbhru):
            flu.potentialsoilevapotranspiration[k] = (
                submodel.get_potentialsoilevapotranspiration(k)
            )


class Calc_PotentialSoilEvapotranspiration_V2(modeltools.Method):
    """Use a submodel that complies with the |PETModel_V1| or |PETModel_V2| interface
    to determine potential soil evapotranspiration."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1, petinterfaces.PETModel_V2)
    SUBMETHODS = (
        Calc_PotentialSoilEvapotranspiration_PETModel_V1,
        Calc_PotentialSoilEvapotranspiration_PETModel_V2,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.PotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.petmodel_typeid == 1:
            model.calc_potentialsoilevapotranspiration_petmodel_v1(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )
        elif model.petmodel_typeid == 2:
            model.calc_potentialsoilevapotranspiration_petmodel_v2(
                cast(petinterfaces.PETModel_V1, model.petmodel)
            )


class Calc_SoilEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the actual soil evapotranspiration according to
    :cite:t:`ref-Lindstrom1997HBV96`.

    Basic equation:
      .. math::
        et_s = pet_s \cdot \frac{s}{l \cdot m}
        \\ \\
        et_s = SoilEvapotranspiration \\
        pet_s = PotentialSoilEvapotranspiration \\
        s = SoilWater \\
        l = SoilMoistureLimit \\
        m = MaxSoilWater

    Examples:

        We initialise seven hydrological response units with different soil water
        contents, including two that fall below and above the lowest and highest
        possible soil moisture, respectively, to show that
        |Calc_SoilEvapotranspiration_V1| works stably in case of eventual numerical
        errors:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(7)
        >>> soil(True)
        >>> maxsoilwater(200.0)
        >>> soilmoisturelimit(0.5)
        >>> fluxes.potentialsoilevapotranspiration = 2.0
        >>> factors.soilwater = -1.0, 0.0, 50.0, 100.0, 150.0, 200.0, 201.0
        >>> model.calc_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 1.0, 2.0, 2.0, 2.0, 2.0)

        When setting |SoilMoistureLimit| to zero, |Calc_SoilEvapotranspiration_V1| sets
        actual soil evapotranspiration equal to possible soil evapotranspiration,
        except for negative soil moisture:

        >>> soilmoisturelimit(0.0)
        >>> model.calc_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)

        Setting |SoilMoistureLimit| to one does not result in any explanatory
        behaviour:

        >>> soilmoisturelimit(1.0)
        >>> model.calc_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.0)

        Condensation does not depend on actual soil moisture.  Hence,
        |Calc_SoilEvapotranspiration_V1| generally sets actual soil evapotranspiration
        equal to potential soil evapotranspiration if negative:

        >>> soilmoisturelimit(0.5)
        >>> fluxes.potentialsoilevapotranspiration = -1.0
        >>> model.calc_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0)

        For non-soil units, soil evapotranspiration is generally zero:

        >>> soil(False)
        >>> fluxes.potentialevapotranspiration = 2.0
        >>> model.calc_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.MaxSoilWater,
        evap_control.SoilMoistureLimit,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SoilWater,
        evap_fluxes.PotentialSoilEvapotranspiration,
    )
    RESULTSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                flu.soilevapotranspiration[k] = flu.potentialsoilevapotranspiration[k]
                if flu.soilevapotranspiration[k] > 0.0:
                    if fac.soilwater[k] < 0.0:
                        flu.soilevapotranspiration[k] = 0.0
                    else:
                        thresh: float = con.soilmoisturelimit[k] * con.maxsoilwater[k]
                        if fac.soilwater[k] < thresh:
                            flu.soilevapotranspiration[k] *= fac.soilwater[k] / thresh
            else:
                flu.soilevapotranspiration[k] = 0.0


class Calc_SoilEvapotranspiration_V2(modeltools.Method):
    r"""Calculate the actual soil evapotranspiration according to
    :cite:t:`ref-Minhas1974`.

    The applied equation deviates from the original by using the formulation of
    :cite:t:`ref-Disse1995`, which is mathematically identical but simpler to
    parameterise and does not explicitly account for the permanent wilting point.

    Basic equation:
      .. math::
       et_s = pet_s \cdot \frac
       {1 - exp\left(-f\cdot \frac{w}{m } \right)}
       {1 + exp\left(-f\cdot \frac{w}{m } \right) - 2 \cdot exp(-f)}
        \\ \\
        et_s = SoilEvapotranspiration \\
        pet_s = PotentialSoilEvapotranspiration \\
        f = DisseFactor \\
        w = SoilWater \\
        m = MaxSoilWater

    Examples:

        We initialise five hydrological response units with different soil water
        contents, including two that fall below and above the lowest and highest
        possible soil moisture, respectively, to show that
        |Calc_SoilEvapotranspiration_V2| works stably in case of eventual numerical
        errors:

        >>> from hydpy.models.evap import *
        >>> parameterstep("1d")
        >>> nmbhru(5)
        >>> soil(True)
        >>> dissefactor(5.0)
        >>> maxsoilwater(100.0)
        >>> fluxes.potentialsoilevapotranspiration = 2.0
        >>> factors.soilwater = -1.0, 0.0, 50.0, 100.0, 101.0
        >>> model.calc_soilevapotranspiration_v2()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 1.717962, 2.0, 2.0)

        Condensation does not depend on actual soil moisture.  Hence,
        |Calc_SoilEvapotranspiration_V2| generally sets actual soil evapotranspiration
        equal to potential soil evapotranspiration if negative:

        >>> fluxes.potentialsoilevapotranspiration = -2.0
        >>> model.calc_soilevapotranspiration_v2()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-2.0, -2.0, -2.0, -2.0, -2.0)

        For non-soil units, soil evapotranspiration is always zero:

        >>> soil(False)
        >>> model.calc_soilevapotranspiration_v2()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.MaxSoilWater,
        evap_control.DisseFactor,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SoilWater,
        evap_fluxes.PotentialSoilEvapotranspiration,
    )
    RESULTSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                flu.soilevapotranspiration[k] = flu.potentialsoilevapotranspiration[k]
                if flu.soilevapotranspiration[k] > 0.0:
                    moisture: float = fac.soilwater[k] / con.maxsoilwater[k]
                    if moisture <= 0.0:
                        flu.soilevapotranspiration[k] = 0.0
                    elif moisture <= 1.0:
                        temp: float = modelutils.exp(-con.dissefactor[k] * moisture)
                        flu.soilevapotranspiration[k] *= (1.0 - temp) / (
                            1.0 + temp - 2.0 * modelutils.exp(-con.dissefactor[k])
                        )
            else:
                flu.soilevapotranspiration[k] = 0.0


class Calc_SoilEvapotranspiration_V3(modeltools.Method):
    r"""Calculate the evapotranspiration from the soil by applying the Penman-Monteith
    equation with an actual surface resistance considering the current soil moisture.

    Basic equation:
      .. math::
        SoilEvapotranspiration = \begin{cases}
        f_{PM}(ActualSurfaceResistance)  &|\ Soil \land (Tree \lor SnowCover = 0 )
        \\
        0 &|\ \overline{Soil } \lor ( \overline{Tree} \land SnowCover > 0 )
        \end{cases}

    Examples:

        We prepare two hydrological response units.  The first one is tree-like, while
        the second one is not.  The other settings agree with the last response unit in
        the second example on method |Return_Evaporation_PenmanMonteith_V1|:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> nmbhru(2)
        >>> soil(True)
        >>> tree(True, False)
        >>> emissivity(0.96)
        >>> factors.saturationvapourpressure = 12.0
        >>> factors.saturationvapourpressureslope = 0.8
        >>> factors.actualvapourpressure = 0.0
        >>> factors.airdensity = 1.24
        >>> factors.aerodynamicresistance = 40.0
        >>> factors.actualsurfaceresistance = 80.0
        >>> factors.airtemperature = 10.0
        >>> fluxes.netradiation = 100.0
        >>> fluxes.soilheatflux = 10.0

        Without any snow cover, the vegetation type does not make a difference:

        >>> factors.snowcover(0.0)
        >>> model.calc_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(5.761072, 5.761072)

        For tree-like vegetation, a snow layer (on the ground) does not affect soil
        evapotranspiration.  For other vegetation types, even incomplete covering
        suppresses interception evaporation completely:

        >>> factors.snowcover(0.1)
        >>> model.calc_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(5.761072, 0.0)

        Soil evapotranspiration is always zero for soil-less hydrological response
        units:

        >>> soil(False)
        >>> model.calc_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0)
    """

    SUBMETHODS = (Return_Evaporation_PenmanMonteith_V1,)
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.Tree,
        evap_control.Emissivity,
    )
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SnowCover,
        evap_factors.AirTemperature,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_factors.ActualSurfaceResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k] and (con.tree[k] or fac.snowcover[k] == 0.0):
                flu.soilevapotranspiration[k] = (
                    model.return_evaporation_penmanmonteith_v1(
                        k, fac.actualsurfaceresistance[k]
                    )
                )

            else:
                flu.soilevapotranspiration[k] = 0.0


class Update_SoilEvapotranspiration_V1(modeltools.Method):
    r"""Reduce actual soil evapotranspiration if the sum of interception evaporation
    and soil evapotranspiration exceeds potential evapotranspiration, according to
    :cite:t:`ref-Lindstrom1997HBV96`.

    :cite:t:`ref-Lindstrom1997HBV96` does not distinguish between potential
    interception evaporation and potential soil evapotranspiration.  Hence, the
    following equation is generalised to deal with situations where both terms are
    unequal.  See `issue 118`_ for further information.

    Basic equation:
      .. math::
        et_s^{new} = et_s^{old} - r \cdot \Big(
        et_s^{old} + e_i - \big(r \cdot pe_i + (1 - r) \cdot (pet_s + pe_i) / 2 \big)
        \Big)
        \\ \\
        et_s = SoilEvapotranspiration \\
        r = ExcessReduction \\
        e_i = InterceptionEvaporation \\
        pet = PotentialEvapotranspiration

    Examples:

        We initialise six hydrological response units with different unmodified soil
        evapotranspiration values, including a negative one (condensation).  When
        setting |ExcessReduction| to one, |Update_SoilEvapotranspiration_V1| does not
        allow the sum of interception evaporation and soil evapotranspiration to exceed
        potential interception evaporation:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(6)
        >>> soil(True)
        >>> excessreduction(1.0)
        >>> fluxes.potentialinterceptionevaporation = 2.0
        >>> fluxes.potentialsoilevapotranspiration = 1.5
        >>> fluxes.interceptionevaporation = 1.0
        >>> fluxes.soilevapotranspiration = -0.5, 0.0, 0.5, 1.0, 1.5, 2.0
        >>> model.update_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-0.5, 0.0, 0.5, 1.0, 1.0, 1.0)

        When setting |ExcessReduction| to one, |Update_SoilEvapotranspiration_V1| does
        not reduce any exceedances:

        >>> excessreduction(0.0)
        >>> fluxes.soilevapotranspiration = -0.5, 0.0, 0.5, 1.0, 1.5, 2.0
        >>> model.update_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-0.5, 0.0, 0.5, 1.0, 1.5, 2.0)

        When setting |ExcessReduction| to 0.5, |Update_SoilEvapotranspiration_V1| takes
        the average of potential interception evaporation and the average of potential
        interception evaporation and soil evapotranspiration as the threshold and
        halves each exceedance above this threshold:

        >>> fluxes.potentialinterceptionevaporation = 2.5
        >>> fluxes.potentialsoilevapotranspiration = 0.5
        >>> excessreduction(0.5)
        >>> fluxes.soilevapotranspiration = -0.5, 0.0, 0.5, 1.0, 1.5, 2.0
        >>> model.update_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-0.5, 0.0, 0.5, 1.0, 1.25, 1.5)

        In the unfortunate case of interception evaporation exceeding potential
        evapotranspiration, previously positive soil evapotranspiration values can
        become negative:

        >>> fluxes.interceptionevaporation = 3.0
        >>> fluxes.soilevapotranspiration = -0.5, 0.0, 0.5, 1.0, 1.5, 2.0
        >>> model.update_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-0.75, -0.5, -0.25, 0.0, 0.25, 0.5)

        For negative potential evapotranspiration (condensation),
        |Update_SoilEvapotranspiration_V1| reverses its behaviour to prevent the sum of
        interception and soil condensation from exceeding potential condensation (too
        much):

        >>> fluxes.potentialinterceptionevaporation = -2.5
        >>> fluxes.potentialsoilevapotranspiration = -0.5
        >>> fluxes.interceptionevaporation = -1.0
        >>> fluxes.soilevapotranspiration = 0.5, -0.0, -0.5, -1.0, -1.5, -2.0
        >>> model.update_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.5, 0.0, -0.5, -1.0, -1.25, -1.5)

        For non-soil units, soil evapotranspiration is generally zero:

        >>> soil(False)
        >>> model.update_soilevapotranspiration_v1()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.ExcessReduction,
    )
    REQUIREDSEQUENCES = (
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_fluxes.PotentialSoilEvapotranspiration,
        evap_fluxes.InterceptionEvaporation,
    )
    UPDATEDSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                r: float = con.excessreduction[k]
                pei: float = flu.potentialinterceptionevaporation[k]
                pets: float = flu.potentialsoilevapotranspiration[k]
                pet: float = r * pei + (1.0 - r) * (pei + pets) / 2.0
                ets: float = flu.soilevapotranspiration[k]
                ei: float = flu.interceptionevaporation[k]
                excess: float = ets + ei - pet
                if (pet >= 0.0) and (excess > 0.0):
                    flu.soilevapotranspiration[k] -= r * excess
                elif (pet < 0.0) and (excess < 0.0):
                    flu.soilevapotranspiration[k] -= r * excess
            else:
                flu.soilevapotranspiration[k] = 0.0


class Update_SoilEvapotranspiration_V2(modeltools.Method):
    r"""Reduce actual soil evapotranspiration due to snow covering.

    Basic equations:
      .. math::
        et_s^{new} = (1 - c) \cdot et_s^{old}
        \\ \\
        et_s = SoilEvapotranspiration \\
        c = SnowCover

    Examples:

        We initialise five hydrological response units with different snow cover
        degrees:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(5)
        >>> soil(True)
        >>> factors.snowcover = 0.0, 0.25, 0.5, 0.75, 1.0
        >>> fluxes.soilevapotranspiration = 2.0
        >>> model.update_soilevapotranspiration_v2()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(2.0, 1.5, 1.0, 0.5, 0.0)

        For non-soil units, soil evapotranspiration is generally zero:

        >>> soil(False)
        >>> model.update_soilevapotranspiration_v2()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Soil)
    REQUIREDSEQUENCES = (evap_factors.SnowCover,)
    RESULTSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k] and (fac.snowcover[k] < 1.0):
                flu.soilevapotranspiration[k] *= 1.0 - fac.snowcover[k]
            else:
                flu.soilevapotranspiration[k] = 0.0


class Update_SoilEvapotranspiration_V3(modeltools.Method):
    r"""Reduce actual soil evapotranspiration if interception evaporation occurs
    simultaneously following :cite:t:`ref-Wigmosta1994`.

    Basic equation:
      :math:`SoilEvapotranspiration_{new} =
      \frac{PotentialInterceptionEvaporation - InterceptionEvaporation}
      {PotentialInterceptionEvaporation} \cdot SoilEvapotranspiration_{old}`

    Example:

        For response units with relevant interception and soil storage, method
        |Update_SoilEvapotranspiration_V3| applies the given base equation:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(4)
        >>> interception(True)
        >>> soil(True)
        >>> fluxes.potentialinterceptionevaporation = 3.0
        >>> fluxes.interceptionevaporation = 0.0, 1.0, 2.0, 3.0
        >>> fluxes.soilevapotranspiration = 2.0
        >>> model.update_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(2.0, 1.333333, 0.666667, 0.0)

        The same holds for negative values (condensation) and mixtures of positive and
        negative values (possibly due to different energy balances when only soil
        evapotranspiration takes the soil heat flux into account):

        >>> fluxes.potentialinterceptionevaporation = -3.0
        >>> fluxes.interceptionevaporation = 0.0, -1.0, -2.0, -3.0
        >>> fluxes.soilevapotranspiration = -2.0
        >>> model.update_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-2.0, -1.333333, -0.666667, 0.0)

        >>> fluxes.potentialinterceptionevaporation = 3.0
        >>> fluxes.interceptionevaporation = 0.0, 1.0, 2.0, 3.0
        >>> fluxes.soilevapotranspiration = -2.0
        >>> model.update_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(-2.0, -1.333333, -0.666667, 0.0)

        |Update_SoilEvapotranspiration_V3| sets the soil evapotranspiration to zero if
        potential interception evaporation is also zero:

        >>> fluxes.potentialinterceptionevaporation = 0.0
        >>> fluxes.interceptionevaporation = 0.0
        >>> fluxes.soilevapotranspiration = 2.0
        >>> model.update_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.0, 0.0)

        For response units that do not consider interception,
        |Update_SoilEvapotranspiration_V3| never modifies soil evapotranspiration:

        >>> interception(False)
        >>> fluxes.potentialinterceptionevaporation = 3.0
        >>> fluxes.soilevapotranspiration = 2.0
        >>> model.update_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(2.0, 2.0, 2.0, 2.0)

        For response units without relevant soil storage,
        |Update_SoilEvapotranspiration_V3| generally sets soil evapotranspiration to
        zero:

        >>> soil(False)
        >>> model.update_soilevapotranspiration_v3()
        >>> fluxes.soilevapotranspiration
        soilevapotranspiration(0.0, 0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Interception,
        evap_control.Soil,
    )
    REQUIREDSEQUENCES = (
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_fluxes.InterceptionEvaporation,
    )
    UPDATEDSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            if con.soil[k]:
                if con.interception[k]:
                    if flu.potentialinterceptionevaporation[k] == 0.0:
                        flu.soilevapotranspiration[k] = 0.0
                    else:
                        flu.soilevapotranspiration[k] *= (
                            flu.potentialinterceptionevaporation[k]
                            - flu.interceptionevaporation[k]
                        ) / flu.potentialinterceptionevaporation[k]
            else:
                flu.soilevapotranspiration[k] = 0.0


class Determine_PotentialEvapotranspiration_V1(modeltools.Method):
    """Interface method that applies the complete application model by executing all
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
        >>> from hydpy import round_
        >>> round_(model.get_potentialevapotranspiration_v1(0))
        2.0
        >>> round_(model.get_potentialevapotranspiration_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.referenceevapotranspiration[k]


class Get_PotentialEvapotranspiration_V2(modeltools.Method):
    """Get the current potential evapotranspiration from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.potentialevapotranspiration = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_potentialevapotranspiration_v2(0))
        2.0
        >>> round_(model.get_potentialevapotranspiration_v2(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.potentialevapotranspiration[k]


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


class Get_MeanPotentialEvapotranspiration_V2(modeltools.Method):
    """Get the averaged potential evapotranspiration.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.meanpotentialevapotranspiration = 3.0
        >>> model.get_meanpotentialevapotranspiration_v2()
        3.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.MeanPotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.meanpotentialevapotranspiration


class Determine_PotentialInterceptionEvaporation_V1(modeltools.AutoMethod):
    """Determine the potential interception evaporation according to AMBAV 1.0
    :cite:p:`ref-Löpmeier2014`."""

    SUBMETHODS = (
        Process_RadiationModel_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_SunshineDuration_V1,
        Calc_GlobalRadiation_V1,
        Calc_AirTemperature_V1,
        Calc_WindSpeed10m_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Calc_DryAirPressure_V1,
        Calc_AirDensity_V1,
        Calc_AerodynamicResistance_V2,
        Calc_SnowCover_V1,
        Calc_DailyPrecipitation_V1,
        Calc_DailyPotentialSoilEvapotranspiration_V1,
        Calc_CurrentAlbedo_V2,
        Calc_NetShortwaveRadiation_V2,
        Update_CloudCoverage_V1,
        Calc_AdjustedCloudCoverage_V1,
        Calc_NetLongwaveRadiation_V2,
        Calc_NetRadiation_V1,
        Calc_SoilHeatFlux_V4,
        Calc_PotentialInterceptionEvaporation_V2,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Interception,
        evap_control.Soil,
        evap_control.Plant,
        evap_control.Water,
        evap_control.MeasuringHeightWindSpeed,
        evap_control.GroundAlbedo,
        evap_control.GroundAlbedoSnow,
        evap_control.LeafAlbedo,
        evap_control.LeafAlbedoSnow,
        evap_control.LeafAreaIndex,
        evap_control.WetnessThreshold,
        evap_control.CloudTypeFactor,
        evap_control.NightCloudFactor,
    )
    DERIVEDPARAMETERS = (
        evap_derived.Hours,
        evap_derived.Days,
        evap_derived.MOY,
        evap_derived.NmbLogEntries,
        evap_derived.AerodynamicResistanceFactor,
    )
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.GasConstantDryAir,
        evap_fixed.GasConstantWaterVapour,
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.RoughnessLengthGrass,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_inputs.WindSpeed,
        evap_inputs.AtmosphericPressure,
        evap_inputs.RelativeHumidity,
        evap_logs.LoggedPrecipitation,
        evap_logs.LoggedPotentialSoilEvapotranspiration,
    )
    UPDATEDSEQUENCES = (evap_states.CloudCoverage,)
    RESULTSEQUENCES = (
        evap_factors.SunshineDuration,
        evap_factors.PossibleSunshineDuration,
        evap_fluxes.GlobalRadiation,
        evap_factors.AirTemperature,
        evap_factors.WindSpeed10m,
        evap_factors.SaturationVapourPressure,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.ActualVapourPressure,
        evap_factors.DryAirPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_factors.SnowCover,
        evap_factors.CurrentAlbedo,
        evap_factors.AdjustedCloudCoverage,
        evap_fluxes.DailyPrecipitation,
        evap_fluxes.DailyPotentialSoilEvapotranspiration,
        evap_fluxes.NetShortwaveRadiation,
        evap_fluxes.NetLongwaveRadiation,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
        evap_fluxes.PotentialInterceptionEvaporation,
    )


class Determine_InterceptionEvaporation_V1(modeltools.AutoMethod):
    """Determine the actual interception evaporation according to
    :cite:t:`ref-Lindstrom1997HBV96`."""

    SUBMETHODS = (
        Calc_PotentialInterceptionEvaporation_V3,
        Calc_InterceptedWater_V1,
        Calc_InterceptionEvaporation_V1,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Interception)
    RESULTSEQUENCES = (
        evap_factors.InterceptedWater,
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_fluxes.InterceptionEvaporation,
    )


class Determine_InterceptionEvaporation_V2(modeltools.AutoMethod):
    """Determine the actual interception evaporation according to
    :cite:t:`ref-Thompson1981` and :cite:t:`ref-LARSIM`."""

    SUBMETHODS = (
        Process_RadiationModel_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_SunshineDuration_V1,
        Calc_GlobalRadiation_V1,
        Calc_AirTemperature_V1,
        Update_LoggedAirTemperature_V1,
        Calc_DailyAirTemperature_V1,
        Calc_WindSpeed10m_V1,
        Update_LoggedRelativeHumidity_V1,
        Calc_DailyRelativeHumidity_V1,
        Calc_SaturationVapourPressure_V2,
        Calc_DailySaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V2,
        Calc_DailySaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Calc_DailyActualVapourPressure_V1,
        Calc_DryAirPressure_V1,
        Calc_AirDensity_V1,
        Calc_AerodynamicResistance_V1,
        Calc_SnowCover_V1,
        Calc_SnowyCanopy_V1,
        Update_LoggedSunshineDuration_V1,
        Calc_DailySunshineDuration_V1,
        Update_LoggedPossibleSunshineDuration_V1,
        Calc_DailyPossibleSunshineDuration_V1,
        Calc_CurrentAlbedo_V1,
        Calc_NetShortwaveRadiation_V2,
        Calc_DailyNetLongwaveRadiation_V1,
        Calc_NetRadiation_V2,
        Calc_SoilHeatFlux_V3,
        Calc_PotentialInterceptionEvaporation_V1,
        Calc_InterceptedWater_V1,
        Calc_InterceptionEvaporation_V2,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Interception,
        evap_control.Tree,
        evap_control.Water,
        evap_control.MeasuringHeightWindSpeed,
        evap_control.Albedo,
        evap_control.CropHeight,
        evap_control.Emissivity,
        evap_control.AverageSoilHeatFlux,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY, evap_derived.NmbLogEntries)
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.FactorCounterRadiation,
        evap_fixed.GasConstantDryAir,
        evap_fixed.GasConstantWaterVapour,
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.RoughnessLengthGrass,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_inputs.WindSpeed,
        evap_inputs.AtmosphericPressure,
        evap_inputs.RelativeHumidity,
    )
    UPDATEDSEQUENCES = (
        evap_logs.LoggedAirTemperature,
        evap_logs.LoggedRelativeHumidity,
        evap_logs.LoggedSunshineDuration,
        evap_logs.LoggedPossibleSunshineDuration,
    )
    RESULTSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_factors.SunshineDuration,
        evap_fluxes.GlobalRadiation,
        evap_factors.AirTemperature,
        evap_factors.DailyAirTemperature,
        evap_factors.WindSpeed10m,
        evap_factors.DailyRelativeHumidity,
        evap_factors.SaturationVapourPressure,
        evap_factors.DailySaturationVapourPressure,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.DailySaturationVapourPressureSlope,
        evap_factors.ActualVapourPressure,
        evap_factors.DailyActualVapourPressure,
        evap_factors.DryAirPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_factors.SnowCover,
        evap_factors.SnowyCanopy,
        evap_factors.DailySunshineDuration,
        evap_factors.DailyPossibleSunshineDuration,
        evap_factors.CurrentAlbedo,
        evap_fluxes.NetShortwaveRadiation,
        evap_fluxes.DailyNetLongwaveRadiation,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_factors.InterceptedWater,
        evap_fluxes.InterceptionEvaporation,
    )


class Determine_PotentialSoilEvapotranspiration_V1(modeltools.AutoMethod):
    """Determine the actual evapotranspiration from the soil according to AMBAV 1.0
    :cite:p:`ref-Löpmeier2014`."""

    SUBMETHODS = (
        Update_SoilResistance_V1,
        Calc_ActualSurfaceResistance_V2,
        Calc_PotentialSoilEvapotranspiration_V1,
        Update_LoggedPotentialSoilEvapotranspiration_V1,
        Calc_Precipitation_V1,
        Update_LoggedPrecipitation_V1,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Soil,
        evap_control.Plant,
        evap_control.LeafAreaIndex,
        evap_control.WetSoilResistance,
        evap_control.SoilResistanceIncrease,
        evap_control.WetnessThreshold,
        evap_control.LeafResistance,
    )
    DERIVEDPARAMETERS = (
        evap_derived.NmbLogEntries,
        evap_derived.Hours,
        evap_derived.MOY,
    )
    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.DailyPrecipitation,
        evap_fluxes.DailyPotentialSoilEvapotranspiration,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    UPDATEDSEQUENCES = (
        evap_states.SoilResistance,
        evap_logs.LoggedPrecipitation,
        evap_logs.LoggedPotentialSoilEvapotranspiration,
    )
    RESULTSEQUENCES = (
        evap_factors.ActualSurfaceResistance,
        evap_fluxes.PotentialSoilEvapotranspiration,
        evap_fluxes.Precipitation,
    )


class Determine_SoilEvapotranspiration_V1(modeltools.AutoMethod):
    """Determine the actual evapotranspiration from the soil according to
    :cite:t:`ref-Lindstrom1997HBV96`."""

    SUBMETHODS = (
        Calc_SoilWater_V1,
        Calc_SnowCover_V1,
        Calc_PotentialSoilEvapotranspiration_V2,
        Calc_SoilEvapotranspiration_V1,
        Update_SoilEvapotranspiration_V1,
        Update_SoilEvapotranspiration_V2,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Soil,
        evap_control.MaxSoilWater,
        evap_control.SoilMoistureLimit,
        evap_control.ExcessReduction,
    )
    REQUIREDSEQUENCES = (
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_fluxes.InterceptionEvaporation,
    )
    RESULTSEQUENCES = (
        evap_factors.SoilWater,
        evap_factors.SnowCover,
        evap_fluxes.PotentialSoilEvapotranspiration,
        evap_fluxes.SoilEvapotranspiration,
    )


class Determine_SoilEvapotranspiration_V2(modeltools.AutoMethod):
    """Determine the actual evapotranspiration from the soil according to
    :cite:t:`ref-Minhas1974`."""

    SUBMETHODS = (
        Calc_SoilWater_V1,
        Calc_PotentialSoilEvapotranspiration_V2,
        Calc_SoilEvapotranspiration_V2,
        Update_SoilEvapotranspiration_V3,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Interception,
        evap_control.Soil,
        evap_control.MaxSoilWater,
        evap_control.DisseFactor,
    )
    REQUIREDSEQUENCES = (
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_fluxes.InterceptionEvaporation,
    )
    RESULTSEQUENCES = (
        evap_factors.SoilWater,
        evap_fluxes.PotentialSoilEvapotranspiration,
        evap_fluxes.SoilEvapotranspiration,
    )


class Determine_SoilEvapotranspiration_V3(modeltools.AutoMethod):
    """Determine the actual evapotranspiration from the soil according to
    :cite:t:`ref-Thompson1981` and :cite:t:`ref-LARSIM`."""

    SUBMETHODS = (
        Calc_SoilWater_V1,
        Calc_SnowCover_V1,
        Calc_SoilSurfaceResistance_V1,
        Calc_LanduseSurfaceResistance_V1,
        Calc_ActualSurfaceResistance_V1,
        Calc_SoilEvapotranspiration_V3,
        Update_SoilEvapotranspiration_V3,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.Interception,
        evap_control.Soil,
        evap_control.Tree,
        evap_control.Conifer,
        evap_control.LeafAreaIndex,
        evap_control.SurfaceResistance,
        evap_control.Emissivity,
        evap_control.MaxSoilWater,
        evap_control.SoilMoistureLimit,
    )
    DERIVEDPARAMETERS = (evap_derived.Hours, evap_derived.MOY)
    FIXEDPARAMETERS = (
        evap_fixed.StefanBoltzmannConstant,
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.PossibleSunshineDuration,
        evap_factors.AirTemperature,
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
        evap_fluxes.PotentialInterceptionEvaporation,
        evap_fluxes.InterceptionEvaporation,
    )
    RESULTSEQUENCES = (
        evap_factors.SoilWater,
        evap_factors.SnowCover,
        evap_factors.SoilSurfaceResistance,
        evap_factors.LanduseSurfaceResistance,
        evap_factors.ActualSurfaceResistance,
        evap_fluxes.SoilEvapotranspiration,
    )


class Determine_PotentialWaterEvaporation_V1(modeltools.AutoMethod):
    """Determine the potential evaporation from open water areas according to AMBAV 1.0
    :cite:p:`ref-Löpmeier2014`."""

    SUBMETHODS = (
        Calc_WaterEvaporation_V4,
        Update_LoggedWaterEvaporation_V1,
        Calc_DailyWaterEvaporation_V1,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Water)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.HeatCapacityAir,
        evap_fixed.PsychrometricConstant,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_factors.AirDensity,
        evap_factors.AerodynamicResistance,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    UPDATEDSEQUENCES = (evap_logs.LoggedWaterEvaporation,)
    RESULTSEQUENCES = (evap_fluxes.WaterEvaporation, evap_fluxes.DailyWaterEvaporation)


class Determine_WaterEvaporation_V1(modeltools.AutoMethod):
    """Determine the actual evapotranspiration from open water areas according to
    :cite:t:`ref-Lindstrom1997HBV96`."""

    SUBMETHODS = (
        Calc_AirTemperature_V1,
        Calc_PotentialWaterEvaporation_V1,
        Calc_WaterEvaporation_V1,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Water,
        evap_control.TemperatureThresholdIce,
    )
    RESULTSEQUENCES = (
        evap_factors.AirTemperature,
        evap_fluxes.PotentialWaterEvaporation,
        evap_fluxes.WaterEvaporation,
    )


class Determine_WaterEvaporation_V2(modeltools.AutoMethod):
    """Accept potential evapotranspiration as the actual evaporation from water
    areas."""

    SUBMETHODS = (Calc_PotentialWaterEvaporation_V1, Calc_WaterEvaporation_V2)
    CONTROLPARAMETERS = (evap_control.NmbHRU, evap_control.Water)
    RESULTSEQUENCES = (
        evap_fluxes.PotentialWaterEvaporation,
        evap_fluxes.WaterEvaporation,
    )


class Determine_WaterEvaporation_V3(modeltools.AutoMethod):
    """Determine the actual evapotranspiration from open water areas according to
    :cite:t:`ref-LARSIM`, based on :cite:t:`ref-DVWK1996`."""

    SUBMETHODS = (
        Calc_WindSpeed2m_V2,
        Update_LoggedWindSpeed2m_V1,
        Calc_DailyWindSpeed2m_V1,
        Update_LoggedGlobalRadiation_V1,
        Calc_DailyGlobalRadiation_V1,
        Calc_DailyNetShortwaveRadiation_V1,
        Calc_DailyNetRadiation_V1,
        Calc_WaterEvaporation_V3,
    )
    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.Water,
        evap_control.MeasuringHeightWindSpeed,
    )
    DERIVEDPARAMETERS = (evap_derived.Days, evap_derived.NmbLogEntries)
    FIXEDPARAMETERS = (
        evap_fixed.HeatOfCondensation,
        evap_fixed.PsychrometricConstant,
        evap_fixed.RoughnessLengthGrass,
    )
    UPDATEDSEQUENCES = (evap_logs.LoggedWindSpeed2m, evap_logs.LoggedGlobalRadiation)
    REQUIREDSEQUENCES = (
        evap_inputs.WindSpeed,
        evap_factors.CurrentAlbedo,
        evap_factors.DailySaturationVapourPressure,
        evap_factors.DailySaturationVapourPressureSlope,
        evap_factors.DailyActualVapourPressure,
        evap_fluxes.GlobalRadiation,
        evap_fluxes.DailyNetLongwaveRadiation,
    )
    RESULTSEQUENCES = (
        evap_factors.WindSpeed2m,
        evap_fluxes.DailyGlobalRadiation,
        evap_fluxes.DailyNetShortwaveRadiation,
        evap_fluxes.DailyNetRadiation,
        evap_factors.DailyWindSpeed2m,
        evap_fluxes.WaterEvaporation,
    )


class Get_WaterEvaporation_V1(modeltools.Method):
    """Get the current water area evaporation from the selected hydrological response
    unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.waterevaporation = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_waterevaporation_v1(0))
        2.0
        >>> round_(model.get_waterevaporation_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.WaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.waterevaporation[k]


class Get_PotentialWaterEvaporation_V1(modeltools.Method):
    """Get the water area evaporation sum of the last 24 hours from the selected
    hydrological response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> simulationstep("12h")
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.days.update()
        >>> fluxes.dailywaterevaporation = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_potentialwaterevaporation_v1(0))
        1.0
        >>> round_(model.get_potentialwaterevaporation_v1(1))
        2.0
    """

    DERIVEDPARAMETERS = (evap_derived.Days,)
    REQUIREDSEQUENCES = (evap_fluxes.DailyWaterEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        return der.days * flu.dailywaterevaporation[k]


class Get_PotentialInterceptionEvaporation_V1(modeltools.Method):
    """Get the current potential interception evaporation from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.potentialinterceptionevaporation = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_potentialinterceptionevaporation_v1(0))
        2.0
        >>> round_(model.get_potentialinterceptionevaporation_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.PotentialInterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.potentialinterceptionevaporation[k]


class Get_InterceptionEvaporation_V1(modeltools.Method):
    """Get the current actual interception evaporation from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.interceptionevaporation = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_interceptionevaporation_v1(0))
        2.0
        >>> round_(model.get_interceptionevaporation_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.InterceptionEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.interceptionevaporation[k]


class Get_PotentialSoilEvapotranspiration_V1(modeltools.Method):
    """Get the current potential soil evapotranspiration from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.potentialsoilevapotranspiration = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_potentialsoilevapotranspiration_v1(0))
        2.0
        >>> round_(model.get_potentialsoilevapotranspiration_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.PotentialSoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.potentialsoilevapotranspiration[k]


class Get_SoilEvapotranspiration_V1(modeltools.Method):
    """Get the current soil evapotranspiration from the selected hydrological response
    unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.soilevapotranspiration = 2.0, 4.0
        >>> from hydpy import round_
        >>> round_(model.get_soilevapotranspiration_v1(0))
        2.0
        >>> round_(model.get_soilevapotranspiration_v1(1))
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.SoilEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.soilevapotranspiration[k]


class Model(modeltools.AdHocModel):
    """|evap.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Evap")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_AirTemperature_V1,
        Update_LoggedAirTemperature_V1,
        Calc_DailyAirTemperature_V1,
        Calc_WindSpeed2m_V1,
        Calc_WindSpeed2m_V2,
        Update_LoggedWindSpeed2m_V1,
        Calc_DailyWindSpeed2m_V1,
        Calc_WindSpeed10m_V1,
        Update_LoggedRelativeHumidity_V1,
        Calc_DailyRelativeHumidity_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_SaturationVapourPressure_V2,
        Calc_DailySaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V1,
        Calc_SaturationVapourPressureSlope_V2,
        Calc_DailySaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Calc_DailyActualVapourPressure_V1,
        Calc_DryAirPressure_V1,
        Calc_AirDensity_V1,
        Process_RadiationModel_V1,
        Calc_PossibleSunshineDuration_V1,
        Calc_SunshineDuration_V1,
        Calc_ClearSkySolarRadiation_V1,
        Calc_GlobalRadiation_V1,
        Update_LoggedSunshineDuration_V1,
        Calc_DailySunshineDuration_V1,
        Update_LoggedPossibleSunshineDuration_V1,
        Calc_DailyPossibleSunshineDuration_V1,
        Update_LoggedClearSkySolarRadiation_V1,
        Update_LoggedGlobalRadiation_V1,
        Calc_CurrentAlbedo_V1,
        Calc_CurrentAlbedo_V2,
        Calc_DailyGlobalRadiation_V1,
        Calc_NetShortwaveRadiation_V1,
        Calc_NetShortwaveRadiation_V2,
        Calc_DailyNetShortwaveRadiation_V1,
        Update_CloudCoverage_V1,
        Calc_AdjustedCloudCoverage_V1,
        Calc_NetLongwaveRadiation_V1,
        Calc_NetLongwaveRadiation_V2,
        Calc_DailyNetLongwaveRadiation_V1,
        Calc_NetRadiation_V1,
        Calc_NetRadiation_V2,
        Calc_DailyNetRadiation_V1,
        Calc_SoilHeatFlux_V1,
        Calc_SoilHeatFlux_V2,
        Calc_SoilHeatFlux_V3,
        Calc_SoilHeatFlux_V4,
        Calc_PsychrometricConstant_V1,
        Calc_AerodynamicResistance_V1,
        Calc_AerodynamicResistance_V2,
        Calc_SoilSurfaceResistance_V1,
        Calc_DailyPrecipitation_V1,
        Calc_DailyPotentialSoilEvapotranspiration_V1,
        Update_SoilResistance_V1,
        Calc_LanduseSurfaceResistance_V1,
        Calc_ActualSurfaceResistance_V1,
        Calc_ActualSurfaceResistance_V2,
        Calc_ReferenceEvapotranspiration_V1,
        Calc_ReferenceEvapotranspiration_V2,
        Calc_ReferenceEvapotranspiration_V3,
        Calc_ReferenceEvapotranspiration_V4,
        Calc_ReferenceEvapotranspiration_V5,
        Adjust_ReferenceEvapotranspiration_V1,
        Calc_PotentialEvapotranspiration_V1,
        Calc_PotentialEvapotranspiration_V2,
        Calc_PotentialEvapotranspiration_V3,
        Update_PotentialEvapotranspiration_V1,
        Calc_MeanReferenceEvapotranspiration_V1,
        Calc_MeanPotentialEvapotranspiration_V1,
        Calc_InterceptedWater_V1,
        Calc_SoilWater_V1,
        Calc_SnowCover_V1,
        Calc_SnowyCanopy_V1,
        Calc_PotentialWaterEvaporation_V1,
        Calc_WaterEvaporation_V1,
        Calc_WaterEvaporation_V2,
        Calc_WaterEvaporation_V3,
        Calc_WaterEvaporation_V4,
        Update_LoggedWaterEvaporation_V1,
        Calc_DailyWaterEvaporation_V1,
        Calc_InterceptionEvaporation_V1,
        Calc_PotentialInterceptionEvaporation_V1,
        Calc_PotentialInterceptionEvaporation_V2,
        Calc_PotentialInterceptionEvaporation_V3,
        Calc_InterceptionEvaporation_V2,
        Calc_PotentialSoilEvapotranspiration_V1,
        Calc_PotentialSoilEvapotranspiration_V2,
        Calc_SoilEvapotranspiration_V1,
        Calc_SoilEvapotranspiration_V2,
        Calc_SoilEvapotranspiration_V3,
        Update_SoilEvapotranspiration_V1,
        Update_SoilEvapotranspiration_V2,
        Update_SoilEvapotranspiration_V3,
        Update_LoggedPrecipitation_V1,
        Update_LoggedPotentialSoilEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        Determine_PotentialEvapotranspiration_V1,
        Get_PotentialEvapotranspiration_V1,
        Get_PotentialEvapotranspiration_V2,
        Get_MeanPotentialEvapotranspiration_V1,
        Get_MeanPotentialEvapotranspiration_V2,
        Determine_InterceptionEvaporation_V1,
        Determine_InterceptionEvaporation_V2,
        Determine_PotentialInterceptionEvaporation_V1,
        Determine_SoilEvapotranspiration_V1,
        Determine_SoilEvapotranspiration_V2,
        Determine_SoilEvapotranspiration_V3,
        Determine_WaterEvaporation_V1,
        Determine_WaterEvaporation_V2,
        Determine_WaterEvaporation_V3,
        Get_WaterEvaporation_V1,
        Get_PotentialWaterEvaporation_V1,
        Get_PotentialInterceptionEvaporation_V1,
        Get_InterceptionEvaporation_V1,
        Get_PotentialSoilEvapotranspiration_V1,
        Get_SoilEvapotranspiration_V1,
    )
    ADD_METHODS = (
        Return_AdjustedWindSpeed_V1,
        Return_SaturationVapourPressure_V1,
        Return_SaturationVapourPressureSlope_V1,
        Return_Evaporation_PenmanMonteith_V1,
        Return_Evaporation_PenmanMonteith_V2,
        Calc_ReferenceEvapotranspiration_PETModel_V1,
        Calc_AirTemperature_TempModel_V1,
        Calc_AirTemperature_TempModel_V2,
        Calc_Precipitation_PrecipModel_V1,
        Calc_Precipitation_PrecipModel_V2,
        Calc_InterceptedWater_IntercModel_V1,
        Calc_SoilWater_SoilWaterModel_V1,
        Calc_SnowCover_SnowCoverModel_V1,
        Calc_SnowyCanopy_SnowyCanopyModel_V1,
        Calc_PotentialInterceptionEvaporation_PETModel_V1,
        Calc_PotentialInterceptionEvaporation_PETModel_V2,
        Calc_PotentialSoilEvapotranspiration_PETModel_V1,
        Calc_PotentialSoilEvapotranspiration_PETModel_V2,
        Calc_PotentialWaterEvaporation_PETModel_V1,
        Calc_PotentialWaterEvaporation_PETModel_V2,
        Calc_CurrentAlbedo_SnowAlbedoModel_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        petinterfaces.PETModel_V1,
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
    )
    SUBMODELS = ()

    retmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    retmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    retmodel_typeid = modeltools.SubmodelTypeIDProperty()

    petmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    radiationmodel = modeltools.SubmodelProperty(
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V2,
        radiationinterfaces.RadiationModel_V3,
        radiationinterfaces.RadiationModel_V4,
    )
    radiationmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    radiationmodel_typeid = modeltools.SubmodelTypeIDProperty()

    intercmodel = modeltools.SubmodelProperty(stateinterfaces.IntercModel_V1)
    intercmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    intercmodel_typeid = modeltools.SubmodelTypeIDProperty()

    soilwatermodel = modeltools.SubmodelProperty(stateinterfaces.SoilWaterModel_V1)
    soilwatermodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    soilwatermodel_typeid = modeltools.SubmodelTypeIDProperty()

    snowcovermodel = modeltools.SubmodelProperty(stateinterfaces.SnowCoverModel_V1)
    snowcovermodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    snowcovermodel_typeid = modeltools.SubmodelTypeIDProperty()

    snowycanopymodel = modeltools.SubmodelProperty(
        stateinterfaces.SnowyCanopyModel_V1, optional=True
    )
    snowycanopymodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    snowycanopymodel_typeid = modeltools.SubmodelTypeIDProperty()

    snowalbedomodel = modeltools.SubmodelProperty(
        stateinterfaces.SnowAlbedoModel_V1, optional=True
    )
    snowalbedomodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    snowalbedomodel_typeid = modeltools.SubmodelTypeIDProperty()


class Sub_ETModel(modeltools.AdHocModel):
    """Base class for submodels that comply with the submodel interfaces defined in
    modules |petinterfaces| and |aetinterfaces|."""

    @staticmethod
    @contextlib.contextmanager
    def share_configuration(
        sharable_configuration: SharableConfiguration,
    ) -> Generator[None, None, None]:
        """Take the `landtype_constants` data to adjust the parameters
        |evap_control.HRUType| and |evap_control.LandMonthFactor|, the
        `landtype_refindices` parameter instance to adjust the index references of all
        parameters inherited from |evap_parameters.ZipParameter1D| and the `refweights`
        parameter instance to adjust the weight references of all sequences inherited
        from |evap_sequences.FactorSequence1D| or |evap_sequences.FluxSequence1D|,
        temporarily:

        >>> from hydpy.core.parametertools import Constants, NameParameter, Parameter
        >>> consts = Constants(GRASS=1, TREES=3, WATER=2)
        >>> class LandType(NameParameter):
        ...     __name__ = "temp.py"
        ...     constants = consts
        >>> class Subarea(Parameter):
        ...     ...
        >>> from hydpy.models.evap.evap_model import Sub_ETModel
        >>> with Sub_ETModel.share_configuration(
        ...         {"landtype_constants": consts,
        ...          "landtype_refindices": LandType,
        ...          "refweights": Subarea}):
        ...     from hydpy.models.evap.evap_control import HRUType, LandMonthFactor
        ...     HRUType.constants
        ...     LandMonthFactor.rowmin, LandMonthFactor.rownames
        ...     from hydpy.models.evap.evap_parameters import ZipParameter1D
        ...     ZipParameter1D.refindices.__name__
        ...     ZipParameter1D._refweights.__name__
        ...     from hydpy.models.evap.evap_sequences import FactorSequence1D, \
FluxSequence1D
        ...     FactorSequence1D._refweights.__name__
        ...     FluxSequence1D._refweights.__name__
        {'GRASS': 1, 'TREES': 3, 'WATER': 2}
        (1, ('grass', 'water', 'trees'))
        'LandType'
        'Subarea'
        'Subarea'
        'Subarea'
        >>> HRUType.constants
        {'ANY': 0}
        >>> LandMonthFactor.rowmin, LandMonthFactor.rownames
        (0, ('ANY',))
        >>> ZipParameter1D.refindices
        >>> ZipParameter1D._refweights
        >>> FactorSequence1D._refweights
        >>> FluxSequence1D._refweights
        """
        with evap_control.HRUType.modify_constants(
            sharable_configuration["landtype_constants"]
        ), evap_parameters.LandMonthParameter.modify_rows(
            sharable_configuration["landtype_constants"]
        ), evap_parameters.ZipParameter1D.modify_refindices(
            sharable_configuration["landtype_refindices"]
        ), evap_parameters.ZipParameter1D.modify_refweights(
            sharable_configuration["refweights"]
        ), evap_parameters.ZipParameter1D.modify_refweights(
            sharable_configuration["refweights"]
        ), evap_sequences.FactorSequence1D.modify_refweights(
            sharable_configuration["refweights"]
        ), evap_sequences.FluxSequence1D.modify_refweights(
            sharable_configuration["refweights"]
        ):
            yield

    @importtools.define_targetparameter(evap_control.NmbHRU)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of hydrological response units.

        >>> from hydpy.models.evap_ret_tw2002 import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> nmbhru
        nmbhru(2)
        """
        self.parameters.control.nmbhru(nmbzones)

    @importtools.define_targetparameter(evap_control.HRUArea)
    def prepare_subareas(self, subareas: VectorInputFloat) -> None:
        """Set the area of all hydrological response units in km².

        >>> from hydpy.models.evap_ret_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_subareas([1.0, 3.0])
        >>> hruarea
        hruarea(1.0, 3.0)
        """
        self.parameters.control.hruarea(subareas)

    @importtools.define_targetparameter(evap_control.HRUAltitude)
    def prepare_elevations(self, elevations: VectorInputFloat) -> None:
        """If such a parameter exists, set the altitude of all hydrological response
        units in m.

        >>> from hydpy import prepare_model
        >>> petmodel = prepare_model("evap_pet_hbv96")
        >>> petmodel.parameters.control.nmbhru(2)
        >>> petmodel.prepare_elevations([1.0, 3.0])
        >>> petmodel.parameters.control.hrualtitude
        hrualtitude(1.0, 3.0)
        """
        self.parameters.control.hrualtitude(elevations)

    @importtools.define_targetparameter(evap_control.HRUType)
    def prepare_zonetypes(self, zonetypes: VectorInputInt) -> None:
        """If such a parameter exists, set the hydrological response unit types.

        >>> GRASS, TREES, WATER = 1, 3, 2
        >>> from hydpy.core.parametertools import Constants
        >>> constants = Constants(GRASS=GRASS, TREES=TREES, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType
        >>> with HRUType.modify_constants(constants):
        ...     from hydpy.models.evap_pet_mlc import *
        ...     parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_zonetypes([TREES, WATER])
        >>> hrutype
        hrutype(TREES, WATER)
        """
        self.parameters.control.hrutype(zonetypes)

    @importtools.define_targetparameter(evap_control.Water)
    def prepare_water(self, water: VectorInputBool) -> None:
        """Set the flag indicating whether or not the respective hydrological response
        units are water areas.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_water([True, False])
        >>> water
        water(True, False)
        """
        self.parameters.control.water(water)

    @importtools.define_targetparameter(evap_control.Interception)
    def prepare_interception(self, interception: VectorInputBool) -> None:
        """Set the flag indicating whether or not the respective hydrological response
        units consider interception evaporation.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_interception([True, False])
        >>> interception
        interception(True, False)
        """
        self.parameters.control.interception(interception)

    @importtools.define_targetparameter(evap_control.Soil)
    def prepare_soil(self, soil: VectorInputBool) -> None:
        """Set the flag indicating whether or not the respective hydrological response
        units consider evapotranspiration from the soil.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_soil([True, False])
        >>> soil
        soil(True, False)
        """
        self.parameters.control.soil(soil)

    @importtools.define_targetparameter(evap_control.Plant)
    def prepare_plant(self, plant: VectorInputBool) -> None:
        """Set the flag indicating whether or not the respective hydrological response
        units contain vegetation.

        >>> from hydpy import prepare_model
        >>> ambav = prepare_model("evap_pet_ambav1")
        >>> ambav.parameters.control.nmbhru(2)
        >>> ambav.prepare_plant([True, False])
        >>> ambav.parameters.control.plant
        plant(True, False)
        """
        self.parameters.control.plant(plant)

    @importtools.define_targetparameter(evap_control.Tree)
    def prepare_tree(self, tree: VectorInputBool) -> None:
        """Set the flag indicating whether or not the respective hydrological response
        units contain tree-like vegetation.

        >>> from hydpy.models.evap_aet_morsim import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_tree([True, False])
        >>> tree
        tree(True, False)
        """
        self.parameters.control.tree(tree)

    @importtools.define_targetparameter(evap_control.Conifer)
    def prepare_conifer(self, conifer: VectorInputBool) -> None:
        """Set the flag indicating whether or not the respective hydrological response
        units contain conifer-like vegetation.

        >>> from hydpy.models.evap_aet_morsim import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_conifer([True, False])
        >>> conifer
        conifer(True, False)
        """
        self.parameters.control.conifer(conifer)

    @importtools.define_targetparameter(evap_control.LeafAreaIndex)
    def prepare_leafareaindex(self, leafareaindex: MatrixInputFloat) -> None:
        """Set the leaf area index in m²/m².

        >>> from hydpy.models.evap_aet_morsim import *
        >>> parameterstep()
        >>> model.prepare_leafareaindex(10.0)
        >>> leafareaindex
        leafareaindex(ANY=[10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0])
        """
        self.parameters.control.leafareaindex(leafareaindex)

    @importtools.define_targetparameter(evap_control.MeasuringHeightWindSpeed)
    def prepare_measuringheightwindspeed(self, measuringheightwindspeed: float) -> None:
        """Set the height above the ground of the wind speed measurements in m.

        >>> from hydpy.models.evap_aet_morsim import *
        >>> parameterstep()
        >>> model.prepare_measuringheightwindspeed(10.0)
        >>> measuringheightwindspeed
        measuringheightwindspeed(10.0)
        """
        self.parameters.control.measuringheightwindspeed(measuringheightwindspeed)

    @importtools.define_targetparameter(evap_control.MaxSoilWater)
    def prepare_maxsoilwater(self, maxsoilwater: VectorInputFloat) -> None:
        """Set the maximum soil water content in mm.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_maxsoilwater([100.0, 200.0])
        >>> maxsoilwater
        maxsoilwater(100.0, 200.0)
        """
        self.parameters.control.maxsoilwater(maxsoilwater)


class Main_RET_PETModel_V1(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that use submodels named `retmodel`
    and comply with the |PETModel_V1| interface."""

    retmodel: modeltools.SubmodelProperty
    retmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    retmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "retmodel",
        petinterfaces.PETModel_V1,
        petinterfaces.PETModel_V1.prepare_nmbzones,
        petinterfaces.PETModel_V1.prepare_subareas,
    )
    def add_retmodel_v1(
        self,
        retmodel: petinterfaces.PETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `retmodel` that follows the |PETModel_V1| interface and
        is responsible for calculating the reference evapotranspiration.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.evap_pet_m import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> hruarea(2.0, 8.0)
        >>> with model.add_retmodel_v1("evap_ret_io"):
        ...     nmbhru
        nmbhru(2)
        >>> model.retmodel.parameters.control.hruarea
        hruarea(2.0, 8.0)
        """
        control = self.parameters.control
        retmodel.prepare_nmbzones(control.nmbhru.value)
        retmodel.prepare_subareas(control.hruarea.values)


class Main_PET_PETModel_V1(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that use submodels named `petmodel`
    and comply with the |PETModel_V1| interface."""

    petmodel: modeltools.SubmodelProperty
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "petmodel",
        petinterfaces.PETModel_V1,
        petinterfaces.PETModel_V1.prepare_nmbzones,
    )
    def add_petmodel_v1(
        self,
        petmodel: petinterfaces.PETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `petmodel` that follows the |PETModel_V1| interface and
        is responsible for calculating potential evapotranspiration.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_petmodel_v1("evap_ret_io"):
        ...     hruarea(8.0, 2.0)
        ...     nmbhru
        nmbhru(2)
        """
        control = self.parameters.control
        petmodel.prepare_nmbzones(control.nmbhru.value)


class Main_PET_PETModel_V2(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that use submodels named `petmodel`
    and comply with the |PETModel_V2| interface."""

    petmodel: modeltools.SubmodelProperty
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "petmodel",
        petinterfaces.PETModel_V2,
        petinterfaces.PETModel_V2.prepare_nmbzones,
        petinterfaces.PETModel_V2.prepare_interception,
        petinterfaces.PETModel_V2.prepare_soil,
        petinterfaces.PETModel_V2.prepare_water,
    )
    def add_petmodel_v2(
        self,
        petmodel: petinterfaces.PETModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `petmodel` that follows the |PETModel_V2| interface and
        is responsible for calculating potential evapotranspiration.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> interception(True)
        >>> soil(True)
        >>> water(False)
        >>> with model.add_petmodel_v2("evap_pet_ambav1"):
        ...     nmbhru
        ...     interception
        ...     soil
        ...     water
        nmbhru(2)
        interception(True)
        soil(True)
        water(False)
        """
        control = self.parameters.control
        petmodel.prepare_nmbzones(control.nmbhru.value)
        petmodel.prepare_interception(control.interception.value)
        petmodel.prepare_soil(control.soil.value)
        petmodel.prepare_water(control.water.value)


class Main_TempModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |TempModel_V1| interface."""

    tempmodel: modeltools.SubmodelProperty
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |TempModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_pet_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.tempmodel
        >>> evap.tempmodel_is_mainmodel
        False
        >>> evap.tempmodel_typeid
        0

        >>> hland = prepare_model("hland_96")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.tempmodel is hland
        True
        >>> evap.tempmodel_is_mainmodel
        True
        >>> evap.tempmodel_typeid
        1
        """
        if isinstance(mainmodel, tempinterfaces.TempModel_V1):
            self.tempmodel = mainmodel
            self.tempmodel_is_mainmodel = True
            self.tempmodel_typeid = tempinterfaces.TempModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)


class Main_TempModel_V2A(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |TempModel_V2| interface and provide subarea size information."""

    tempmodel: modeltools.SubmodelProperty
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "tempmodel",
        tempinterfaces.TempModel_V2,
        tempinterfaces.TempModel_V2.prepare_nmbzones,
        tempinterfaces.TempModel_V2.prepare_subareas,
    )
    def add_tempmodel_v2(
        self,
        tempmodel: tempinterfaces.TempModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given precipitation model that follows the |TempModel_V2|
        interface and set the number and the subareas of its zones.

        >>> from hydpy.models.evap_pet_hbv96 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbhru(2)
        >>> hruarea(2.0, 8.0)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     nmbhru
        ...     hruarea
        ...     temperatureaddend(1.0, 2.0)
        nmbhru(2)
        hruarea(2.0, 8.0)
        >>> model.tempmodel.parameters.control.temperatureaddend
        temperatureaddend(1.0, 2.0)
        """
        control = self.parameters.control
        tempmodel.prepare_nmbzones(control.nmbhru.value)
        tempmodel.prepare_subareas(control.hruarea.value)


class Main_TempModel_V2B(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |TempModel_V2| interface and do not provide subarea size information."""

    tempmodel: modeltools.SubmodelProperty
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "tempmodel",
        tempinterfaces.TempModel_V2,
        tempinterfaces.TempModel_V2.prepare_nmbzones,
    )
    def add_tempmodel_v2(
        self,
        tempmodel: tempinterfaces.TempModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given precipitation model that follows the |TempModel_V2|
        interface and set the number of its zones.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbhru(2)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     nmbhru
        ...     hruarea(0.8, 0.2)
        ...     temperatureaddend(1.0, 2.0)
        nmbhru(2)
        >>> model.tempmodel.parameters.control.hruarea
        hruarea(0.8, 0.2)
        >>> model.tempmodel.parameters.control.temperatureaddend
        temperatureaddend(1.0, 2.0)
        """
        control = self.parameters.control
        tempmodel.prepare_nmbzones(control.nmbhru.value)


class Main_PrecipModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |PrecipModel_V1| interface."""

    precipmodel: modeltools.SubmodelProperty
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |PrecipModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_pet_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.precipmodel
        >>> evap.precipmodel_is_mainmodel
        False
        >>> evap.precipmodel_typeid
        0

        >>> hland = prepare_model("hland_96")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.precipmodel is hland
        True
        >>> evap.precipmodel_is_mainmodel
        True
        >>> evap.precipmodel_typeid
        1
        """
        if isinstance(mainmodel, precipinterfaces.PrecipModel_V1):
            self.precipmodel = mainmodel
            self.precipmodel_is_mainmodel = True
            self.precipmodel_typeid = precipinterfaces.PrecipModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)


class Main_PrecipModel_V2A(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |PrecipModel_V2| interface."""

    precipmodel: modeltools.SubmodelProperty
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "precipmodel",
        precipinterfaces.PrecipModel_V2,
        precipinterfaces.PrecipModel_V2.prepare_nmbzones,
        precipinterfaces.PrecipModel_V2.prepare_subareas,
    )
    def add_precipmodel_v2(
        self,
        precipmodel: precipinterfaces.PrecipModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given precipitation model that follows the |PrecipModel_V2|
        interface and set the number and the subareas of its zones.

        >>> from hydpy.models.evap_pet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> hruarea(2.0, 8.0)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     nmbhru
        ...     hruarea
        ...     precipitationfactor(1.0, 2.0)
        nmbhru(2)
        hruarea(2.0, 8.0)
        >>> model.precipmodel.parameters.control.precipitationfactor
        precipitationfactor(1.0, 2.0)
        """
        control = self.parameters.control
        precipmodel.prepare_nmbzones(control.nmbhru.value)
        precipmodel.prepare_subareas(control.hruarea.value)


class Main_PrecipModel_V2B(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |PrecipModel_V2| interface."""

    precipmodel: modeltools.SubmodelProperty
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "precipmodel",
        precipinterfaces.PrecipModel_V2,
        precipinterfaces.PrecipModel_V2.prepare_nmbzones,
    )
    def add_precipmodel_v2(
        self,
        precipmodel: precipinterfaces.PrecipModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given precipitation model that follows the |PrecipModel_V2|
        interface and set the number of its zones.

        >>> from hydpy.models.evap_pet_ambav1 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     nmbhru
        ...     hruarea(0.8, 0.2)
        ...     precipitationfactor(1.0, 2.0)
        nmbhru(2)
        >>> model.precipmodel.parameters.control.hruarea
        hruarea(0.8, 0.2)
        >>> model.precipmodel.parameters.control.precipitationfactor
        precipitationfactor(1.0, 2.0)
        """
        control = self.parameters.control
        precipmodel.prepare_nmbzones(control.nmbhru.value)


class Main_RadiationModel_V1(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |RadiationModel_V1| interface."""

    radiationmodel: modeltools.SubmodelProperty
    radiationmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    radiationmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "radiationmodel", radiationinterfaces.RadiationModel_V1
    )
    def add_radiationmodel_v1(
        self,
        radiationmodel: radiationinterfaces.RadiationModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given radiation model that follows the |RadiationModel_V1|
        interface.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_ret_tw2002 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56"):
        ...     latitude(50.0)
        ...     longitude(5.0)
        >>> model.radiationmodel.parameters.control.latitude
        latitude(50.0)
        """


class Main_RadiationModel_V2(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |RadiationModel_V2| interface."""

    radiationmodel: modeltools.SubmodelProperty
    radiationmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    radiationmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "radiationmodel", radiationinterfaces.RadiationModel_V2
    )
    def add_radiationmodel_v2(
        self,
        radiationmodel: radiationinterfaces.RadiationModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given radiation model that follows the |RadiationModel_V2|
        interface.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_ret_tw2002 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v2("meteo_glob_io"):
        ...     inputs.globalradiation = 100.0
        >>> model.radiationmodel.sequences.inputs.globalradiation
        globalradiation(100.0)
        """


class Main_RadiationModel_V3(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |RadiationModel_V3| interface."""

    radiationmodel: modeltools.SubmodelProperty
    radiationmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    radiationmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "radiationmodel", radiationinterfaces.RadiationModel_V3
    )
    def add_radiationmodel_v3(
        self,
        radiationmodel: radiationinterfaces.RadiationModel_V3,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given radiation model that follows the |RadiationModel_V3|
        interface.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_ret_fao56 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v3("meteo_clear_glob_io"):
        ...     inputs.clearskysolarradiation = 200.0
        ...     inputs.globalradiation = 100.0
        >>> model.radiationmodel.sequences.inputs.clearskysolarradiation
        clearskysolarradiation(200.0)
        >>> model.radiationmodel.sequences.inputs.globalradiation
        globalradiation(100.0)
        """


class Main_RadiationModel_V4(modeltools.AdHocModel):
    """Base class for |evap.DOCNAME.long| models that support submodels that comply
    with the |RadiationModel_V4| interface."""

    radiationmodel: modeltools.SubmodelProperty
    radiationmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    radiationmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "radiationmodel", radiationinterfaces.RadiationModel_V4
    )
    def add_radiationmodel_v4(
        self,
        radiationmodel: radiationinterfaces.RadiationModel_V4,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given radiation model that follows the |RadiationModel_V4|
        interface.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.evap_pet_ambav1 import *
        >>> parameterstep()
        >>> with model.add_radiationmodel_v4("meteo_psun_sun_glob_io"):
        ...     inputs.possiblesunshineduration = 12.0
        ...     inputs.sunshineduration = 6.0
        ...     inputs.globalradiation = 100.0
        >>> model.radiationmodel.sequences.inputs.possiblesunshineduration
        possiblesunshineduration(12.0)
        >>> model.radiationmodel.sequences.inputs.sunshineduration
        sunshineduration(6.0)
        >>> model.radiationmodel.sequences.inputs.globalradiation
        globalradiation(100.0)
        """


class Main_IntercModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |IntercModel_V1| interface."""

    intercmodel: modeltools.SubmodelProperty
    intercmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    intercmodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |IntercModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_aet_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.intercmodel
        >>> evap.intercmodel_is_mainmodel
        False
        >>> evap.intercmodel_typeid
        0

        >>> hland = prepare_model("hland_96")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.intercmodel is hland
        True
        >>> evap.intercmodel_is_mainmodel
        True
        >>> evap.intercmodel_typeid
        1
        """
        if isinstance(mainmodel, stateinterfaces.IntercModel_V1):
            self.intercmodel = mainmodel
            self.intercmodel_is_mainmodel = True
            self.intercmodel_typeid = stateinterfaces.IntercModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)

    @importtools.prepare_submodel(
        "intercmodel",
        stateinterfaces.IntercModel_V1,
        stateinterfaces.IntercModel_V1.prepare_nmbzones,
    )
    def add_intercmodel_v1(
        self,
        intercmodel: stateinterfaces.IntercModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given interception model that follows the |IntercModel_V1|
        interface and set the number of its zones.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_intercmodel_v1("dummy_interceptedwater"):
        ...     nmbhru
        nmbhru(2)
        """
        control = self.parameters.control
        intercmodel.prepare_nmbzones(control.nmbhru.value)


class Main_SoilWaterModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |SoilWaterModel_V1| interface."""

    soilwatermodel: modeltools.SubmodelProperty
    soilwatermodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    soilwatermodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |SoilWaterModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_aet_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.soilwatermodel
        >>> evap.soilwatermodel_is_mainmodel
        False
        >>> evap.soilwatermodel_typeid
        0

        >>> hland = prepare_model("hland_96")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.soilwatermodel is hland
        True
        >>> evap.soilwatermodel_is_mainmodel
        True
        >>> evap.soilwatermodel_typeid
        1
        """
        if isinstance(mainmodel, stateinterfaces.SoilWaterModel_V1):
            self.soilwatermodel = mainmodel
            self.soilwatermodel_is_mainmodel = True
            self.soilwatermodel_typeid = stateinterfaces.SoilWaterModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)

    @importtools.prepare_submodel(
        "soilwatermodel",
        stateinterfaces.SoilWaterModel_V1,
        stateinterfaces.SoilWaterModel_V1.prepare_nmbzones,
    )
    def add_soilwatermodel_v1(
        self,
        soilwatermodel: stateinterfaces.SoilWaterModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given soil water model that follows the |SoilWaterModel_V1|
        interface and set the number of its zones.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_soilwatermodel_v1("dummy_soilwater"):
        ...     nmbhru
        nmbhru(2)
        """
        control = self.parameters.control
        soilwatermodel.prepare_nmbzones(control.nmbhru.value)


class Main_SnowCoverModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |SnowCoverModel_V1| interface."""

    snowcovermodel: modeltools.SubmodelProperty
    snowcovermodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    snowcovermodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |SnowCoverModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_aet_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.snowcovermodel
        >>> evap.snowcovermodel_is_mainmodel
        False
        >>> evap.snowcovermodel_typeid
        0

        >>> hland = prepare_model("hland_96")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.snowcovermodel is hland
        True
        >>> evap.snowcovermodel_is_mainmodel
        True
        >>> evap.snowcovermodel_typeid
        1
        """
        if isinstance(mainmodel, stateinterfaces.SnowCoverModel_V1):
            self.snowcovermodel = mainmodel
            self.snowcovermodel_is_mainmodel = True
            self.snowcovermodel_typeid = stateinterfaces.SnowCoverModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)

    @importtools.prepare_submodel(
        "snowcovermodel",
        stateinterfaces.SnowCoverModel_V1,
        stateinterfaces.SnowCoverModel_V1.prepare_nmbzones,
    )
    def add_snowcovermodel_v1(
        self,
        snowcovermodel: stateinterfaces.SnowCoverModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given snow cover model that follows the
        |SnowCoverModel_V1| interface and set the number of its zones.

        >>> from hydpy.models.evap_aet_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_snowcovermodel_v1("dummy_snowcover"):
        ...     nmbhru
        nmbhru(2)
        """
        control = self.parameters.control
        snowcovermodel.prepare_nmbzones(control.nmbhru.value)


class Main_SnowyCanopyModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |SnowyCanopyModel_V1| interface."""

    snowycanopymodel: modeltools.SubmodelProperty
    snowycanopymodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    snowycanopymodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |SnowyCanopyModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_aet_morsim")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.snowycanopymodel
        >>> evap.snowycanopymodel_is_mainmodel
        False
        >>> evap.snowycanopymodel_typeid
        0

        >>> lland = prepare_model("lland_knauf_ic")
        >>> evap.add_mainmodel_as_subsubmodel(lland)
        True
        >>> evap.snowycanopymodel is lland
        True
        >>> evap.snowycanopymodel_is_mainmodel
        True
        >>> evap.snowycanopymodel_typeid
        1
        """
        if isinstance(mainmodel, stateinterfaces.SnowyCanopyModel_V1):
            self.snowycanopymodel = mainmodel
            self.snowycanopymodel_is_mainmodel = True
            self.snowycanopymodel_typeid = stateinterfaces.SnowyCanopyModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)

    @importtools.prepare_submodel(
        "snowycanopymodel",
        stateinterfaces.SnowyCanopyModel_V1,
        stateinterfaces.SnowyCanopyModel_V1.prepare_nmbzones,
    )
    def add_snowycanopymodel_v1(
        self,
        snowycanopymodel: stateinterfaces.SnowyCanopyModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given snow cover model that follows the
        |SnowyCanopyModel_V1| interface and set the number of its zones.

        >>> from hydpy.models.evap_aet_morsim import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_snowycanopymodel_v1("dummy_snowycanopy"):
        ...     nmbhru
        nmbhru(2)
        """
        control = self.parameters.control
        snowycanopymodel.prepare_nmbzones(control.nmbhru.value)


class Main_SnowAlbedoModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for |evap.DOCNAME.long| models that can use main models as their
    sub-submodels if they comply with the |SnowAlbedoModel_V1| interface."""

    snowalbedomodel: modeltools.SubmodelProperty
    snowalbedomodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    snowalbedomodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |SnowAlbedoModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_aet_morsim")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_ret_io"))
        False
        >>> evap.snowalbedomodel
        >>> evap.snowalbedomodel_is_mainmodel
        False
        >>> evap.snowalbedomodel_typeid
        0

        >>> lland = prepare_model("lland_knauf")
        >>> evap.add_mainmodel_as_subsubmodel(lland)
        True
        >>> evap.snowalbedomodel is lland
        True
        >>> evap.snowalbedomodel_is_mainmodel
        True
        >>> evap.snowalbedomodel_typeid
        1
        """
        if isinstance(mainmodel, stateinterfaces.SnowAlbedoModel_V1):
            self.snowalbedomodel = mainmodel
            self.snowalbedomodel_is_mainmodel = True
            self.snowalbedomodel_typeid = stateinterfaces.SnowAlbedoModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)

    @importtools.prepare_submodel(
        "snowalbedomodel",
        stateinterfaces.SnowAlbedoModel_V1,
        stateinterfaces.SnowAlbedoModel_V1.prepare_nmbzones,
    )
    def add_snowalbedomodel_v1(
        self,
        snowalbedomodel: stateinterfaces.SnowAlbedoModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given albedo model that follows the |SnowAlbedoModel_V1|
        interface and set the number of its zones.

        >>> from hydpy.models.evap_aet_morsim import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> with model.add_snowalbedomodel_v1("dummy_snowalbedo"):
        ...     nmbhru
        nmbhru(2)
        """
        control = self.parameters.control
        snowalbedomodel.prepare_nmbzones(control.nmbhru.value)
