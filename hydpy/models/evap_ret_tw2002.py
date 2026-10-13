# pylint: disable=line-too-long, unused-wildcard-import
"""The primary purpose of |evap_ret_tw2002| is to serve as a submodel that provides
estimates of potential grass reference evapotranspiration following :cite:t:`ref-DVWK`,
as demonstrated for |lland_dd|.  However, you can also use it as a stand-alone model,
as it does not require interaction with a main model.  The following examples make use
of this stand-alone functionality.

|evap_ret_tw2002| requires two submodels.  One must follow the |RadiationModel_V1| or
the |RadiationModel_V2| interface and provide global radiation data; the other must
follow the |TempModel_V1| or the |TempModel_V2| interface and provide temperature data.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_ret_tw2002| requires no input from an external model and does
not supply any data to an outlet sequence.  Hence, assigning a model instance to a
blank |Element| instance is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_ret_tw2002 import *
>>> parameterstep()
>>> element = Element("element")
>>> element.model = model

The Turc-Wendling equation is designed for daily data.  Hence, we start with a daily
simulation step:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"

We set the parameter and input values in agreement with the
:ref:`evap_ret_fao56_hourly_simulation` example of |evap_ret_fao56|, which allows for
comparison with the results of the FAO reference evapotranspiration model applied to
data of station Uccle (Brussels, Belgium), as reported in example 18 of
:cite:t:`ref-Allen1998`:

>>> nmbhru(1)
>>> hruarea(1.0)
>>> evapotranspirationfactor(1.0)
>>> hrualtitude(100.0)

|evap_ret_fao56| has no counterpart for the |CoastFactor| parameter.  We set its value from
our gut feeling to 0.9, as Brussels is not directly adjacent to the coastline (0.6) but
also not that far away from it (1.0):

>>> coastfactor(0.9)

A |meteo_glob_io| and a |meteo_temp_io| submodel provide the required global radiation
and temperature data:

>>> with model.add_radiationmodel_v2("meteo_glob_io"):
...     pass
>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     temperatureaddend(1.0)

Now, we can initialise an |IntegrationTest| object and set the required meteorological
input:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> model.tempmodel.sequences.inputs.temperature.series = 15.9
>>> model.radiationmodel.sequences.inputs.globalradiation.series = 255.367464

For the example at hand, there is an excellent agreement with the result calculated by
|evap_ret_fao56| and given by :cite:t:`ref-Allen1998`, which is 3.75 mm/d:

.. integration-test::

    >>> test()
    |       date | airtemperature | dailyairtemperature | globalradiation | dailyglobalradiation | referenceevapotranspiration | meanreferenceevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |                16.9 |      255.367464 |           255.367464 |                    3.787245 |                        3.787245 |

Instead of IO submodels, one could use the main model of |evap_ret_tw2002| for
providing the temperature data or a "real" submodel that calculates the global
radiation data.  The first option is not feasible here due to not using
|evap_ret_tw2002| as a submodel but as a stand-alone model.  But we can demonstrate the
latter option by using, for example, |meteo_glob_fao56|, which we also configure in
agreement with the :ref:`evap_ret_fao56_hourly_simulation` example.  Hence,
|meteo_glob_fao56| reproduces the global radiation above so that |evap_ret_tw2002|
calculates the same potential evapotranspiration value:

>>> with model.add_radiationmodel_v1("meteo_glob_fao56"):
...     latitude(50.8)
...     angstromconstant(0.25)
...     angstromfactor(0.5)

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> model.tempmodel.sequences.inputs.temperature.series = 15.9
>>> model.radiationmodel.sequences.inputs.sunshineduration.series = 9.25

.. integration-test::

    >>> test()
    |       date | airtemperature | dailyairtemperature | globalradiation | dailyglobalradiation | referenceevapotranspiration | meanreferenceevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |                16.9 |      255.367464 |           255.367464 |                    3.787245 |                        3.787245 |

|evap_ret_tw2002| is also applicable to sub-daily simulation step sizes.  Then, it
still evaluates the Turc-Wendling equation for daily data, namely the averages of the
air temperature and the global radiation of the last 24 hours, and converts the
resulting daily evapotranspiration to the actual simulation step size.  To demonstrate
this, we prepare a simulation period of 24 hours:

>>> pub.timegrids = "2000-08-03", "2000-08-04", "1h"

We switch back to IO submodels and take the hourly air temperature and global radiation
data from the :ref:`evap_aet_morsim_hourly_simulation_land` example of
|evap_aet_morsim|:

>>> with model.add_radiationmodel_v2("meteo_glob_io"):
...     pass
>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     temperatureaddend(0.0)

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m %H:00"

>>> model.tempmodel.sequences.inputs.temperature.series = (
...     16.9, 16.6, 16.4, 16.3, 16.0, 15.9, 16.0, 16.6, 17.4, 19.0, 20.3, 21.4, 21.3,
...     21.8, 22.9, 22.7, 22.5, 21.9, 21.4, 20.7, 19.4, 17.8, 17.0, 16.4)
>>> model.radiationmodel.sequences.inputs.globalradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 1.943686, 21.932441, 57.256187, 109.332844, 170.949152,
...     311.762624, 501.583299, 615.018727, 626.544326, 496.133417, 419.520994,
...     387.887354, 278.496873, 137.138608, 51.080715, 13.632816, 0.185943, 0.0, 0.0,
...     0.0)

Due to averaging over the last 24 hours, we must provide the corresponding logged data
for the 24 hours preceding the simulation period.  We take them from the
:ref:`evap_aet_morsim_hourly_simulation_land` example, too:

>>> test.inits = (
...     (logs.loggedglobalradiation,
...      [0.0, 0.0, 0.0, 0.0, 0.0, 27.8, 55.6, 138.9, 222.2, 305.6, 333.3, 388.9,
...       527.8, 444.4, 250.0, 222.2, 166.7, 111.1, 55.6, 27.8, 0.0, 0.0, 0.0, 0.0]),
...     (logs.loggedairtemperature,
...      [[13.2], [13.2], [13.1], [12.6], [12.7], [13.0], [13.5], [14.8], [16.2],
...       [17.7], [18.8], [19.4], [20.4], [21.0], [21.5], [21.2], [20.4], [20.7],
...       [20.2], [19.7], [19.0], [18.0], [17.5], [17.1]]))

The calculated reference evapotranspiration does not follow the diurnal pattern of the
meteorological input.  Instead, it changes only gradually with the moving averages of
air temperature and global radiation, so that, for example, the values of the last
night hours even exceed those around noon:

.. integration-test::

    >>> test()
    |             date | airtemperature | dailyairtemperature | globalradiation | dailyglobalradiation | referenceevapotranspiration | meanreferenceevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-03-08 00:00 |           16.9 |           17.279167 |             0.0 |           136.579167 |                    0.087692 |                        0.087692 |
    | 2000-03-08 01:00 |           16.6 |           17.241667 |             0.0 |           136.579167 |                    0.087631 |                        0.087631 |
    | 2000-03-08 02:00 |           16.4 |              17.175 |             0.0 |           136.579167 |                    0.087524 |                        0.087524 |
    | 2000-03-08 03:00 |           16.3 |             17.0625 |             0.0 |           136.579167 |                    0.087343 |                        0.087343 |
    | 2000-03-08 04:00 |           16.0 |           16.908333 |        1.943686 |            135.50182 |                    0.086453 |                        0.086453 |
    | 2000-03-08 05:00 |           15.9 |           16.729167 |       21.932441 |           134.099005 |                    0.085332 |                        0.085332 |
    | 2000-03-08 06:00 |           16.0 |           16.533333 |       57.256187 |           131.855513 |                    0.083693 |                        0.083693 |
    | 2000-03-08 07:00 |           16.6 |              16.375 |      109.332844 |           129.465215 |                    0.082035 |                        0.082035 |
    | 2000-03-08 08:00 |           17.4 |           16.216667 |      170.949152 |           127.329763 |                    0.080534 |                        0.080534 |
    | 2000-03-08 09:00 |           19.0 |             16.1125 |      311.762624 |           129.903206 |                    0.081885 |                        0.081885 |
    | 2000-03-08 10:00 |           20.3 |           16.083333 |      501.583299 |           132.285843 |                    0.083236 |                        0.083236 |
    | 2000-03-08 11:00 |           21.4 |              16.125 |      615.018727 |           135.919957 |                    0.085434 |                        0.085434 |
    | 2000-03-08 12:00 |           21.3 |           16.204167 |      626.544326 |           145.821804 |                    0.091382 |                        0.091382 |
    | 2000-03-08 13:00 |           21.8 |           16.329167 |      496.133417 |           152.606529 |                    0.095595 |                        0.095595 |
    | 2000-03-08 14:00 |           22.9 |           16.545833 |      419.520994 |           157.353237 |                    0.098793 |                        0.098793 |
    | 2000-03-08 15:00 |           22.7 |           16.816667 |      387.887354 |           164.256877 |                    0.103398 |                        0.103398 |
    | 2000-03-08 16:00 |           22.5 |             17.1375 |      278.496873 |           170.073414 |                    0.107493 |                        0.107493 |
    | 2000-03-08 17:00 |           21.9 |             17.4875 |      137.138608 |           173.470855 |                    0.110228 |                        0.110228 |
    | 2000-03-08 18:00 |           21.4 |             17.8375 |       51.080715 |           174.440885 |                    0.111516 |                        0.111516 |
    | 2000-03-08 19:00 |           20.7 |           18.170833 |       13.632816 |           175.008919 |                     0.11253 |                         0.11253 |
    | 2000-03-08 20:00 |           19.4 |           18.454167 |        0.185943 |           175.016667 |                    0.113102 |                        0.113102 |
    | 2000-03-08 21:00 |           17.8 |               18.65 |             0.0 |           175.016667 |                    0.113492 |                        0.113492 |
    | 2000-03-08 22:00 |           17.0 |           18.808333 |             0.0 |           175.016667 |                    0.113807 |                        0.113807 |
    | 2000-03-08 23:00 |           16.4 |           18.941667 |             0.0 |           175.016667 |                    0.114071 |                        0.114071 |

After 24 hours, the moving averages cover exactly the simulated day.  Hence,
multiplying the last hourly value by 24 gives the reference evapotranspiration one
would calculate for this day in a simulation with a daily step size:

>>> from hydpy import round_
>>> round_(24.0 * fluxes.referenceevapotranspiration.series[-1, 0])
2.737713

"""

from hydpy.core import masktools
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import radiationinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_masks
from hydpy.models.evap import evap_model

ADDITIONAL_CONTROLPARAMETERS = (
    evap_control.Soil,
    evap_control.Plant,
    evap_control.Water,
)


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2A,
    evap_model.Main_RadiationModel_V1,
    evap_model.Main_RadiationModel_V2,
    evap_model.Sub_ETModel,
    petinterfaces.PETModel_V1,
):
    """|evap_ret_tw2002.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-RET-TW2002",
        description="Turc-Wendling reference evapotranspiration, 2002",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Process_RadiationModel_V1,
        evap_model.Calc_GlobalRadiation_V1,
        evap_model.Calc_AirTemperature_V1,
        evap_model.Update_LoggedAirTemperature_V1,
        evap_model.Calc_DailyAirTemperature_V1,
        evap_model.Update_LoggedGlobalRadiation_V1,
        evap_model.Calc_DailyGlobalRadiation_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V2,
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_MeanReferenceEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V1,
        evap_model.Get_MeanPotentialEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_AirTemperature_TempModel_V1,
        evap_model.Calc_AirTemperature_TempModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        radiationinterfaces.RadiationModel_V1,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty[
        tempinterfaces.TempModel_V1 | tempinterfaces.TempModel_V2
    ](tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2)
    radiationmodel = modeltools.SubmodelProperty[
        radiationinterfaces.RadiationModel_V1 | radiationinterfaces.RadiationModel_V2
    ](radiationinterfaces.RadiationModel_V1, radiationinterfaces.RadiationModel_V2)


class Masks(masktools.Masks):
    """Masks applicable to |evap_ret_tw2002|."""

    CLASSES = evap_masks.Masks.CLASSES


tester = Tester()
cythonizer = Cythonizer()
