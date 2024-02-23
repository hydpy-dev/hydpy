# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the actual evapotranspiration routines of HBV96
:cite:p:`ref-Lindstrom1997HBV96`.

|evap_aet_hbv96| serves as a submodel that supplies its main model with estimates of
actual evapotranspiration from soils and actual evaporation from interception storages
and water areas.  Therefore, it requires potential evapotranspiration data calculated
by a sub-submodel.  If you long to emulate HBV96 as closely as possible, select
|evap_pet_hbv96|.

Additionally, |evap_aet_hbv96| requires information about the current air temperature,
the initial water contents of the interception and soil storages, and the current
degree of snow coverage.  By default, |evap_aet_hbv96| queries all these properties
from its main model and, at least for the last three properties, this should be the
desired behaviour in most cases as it fully synchronises the related states.  However,
the following tests use |evap_aet_hbv96| as a stand-alone model.  Hence, we need to
connect additional submodels to it that provide pre-defined temperature, water content,
and snow cover data.

Integration tests
=================

.. how_to_understand_integration_tests::

According to the intended usage as a submodel, |evap_aet_hbv96| requires no connections
to any nodes.  Hence, assigning a model instance to a blank |Element| instance is
sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_aet_hbv96 import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

We perform the integration test for two simulation steps.  We will configure the first
step identical to the first hour of the second day of the simulation period selected
for the integration tests of |hland_v1|:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"

We set all parameter values identical to the ones defined in the :ref:`hland_v1_field`
example of |hland_v1|:

>>> nmbhru(1)
>>> maxsoilwater(200.0)
>>> soilmoisturelimit(0.8)
>>> excessreduction(0.5)
>>> temperaturethresholdice(0.0)

We add submodels of type |evap_io|, |meteo_temp_io|, |dummy_interceptedwater|,
|dummy_soilwater|, and |dummy_snowcover| for providing pre-defined values of potential
evapotranspiration (identical values for potential interception evaporation and soil
evapotranspiration), air temperature, intercepted water, soil water, and snow cover:

>>> with model.add_petmodel_v1("evap_io"):
...     hruarea(1.0)
...     evapotranspirationfactor(1.0)
>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     hruarea(1.0)
...     temperatureaddend(0.0)
>>> with model.add_intercmodel_v1("dummy_interceptedwater"):
...     pass
>>> with model.add_soilwatermodel_v1("dummy_soilwater"):
...     pass
>>> with model.add_snowcovermodel_v1("dummy_snowcover"):
...     pass

Now, we can initialise an |IntegrationTest| object:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

The first temperature input also stems from the input data of the :ref:`hland_v1_field`
example, while the second represents winter conditions:

>>> model.tempmodel.sequences.inputs.temperature.series = 19.2, 0.0

The (constant) potential evapotranspiration value stems from the output of the
integration test of |evap_pet_hbv96|, which is also consistent with the
:ref:`hland_v1_field` example:

>>> model.petmodel.sequences.inputs.referenceevapotranspiration.series = 0.06896

The following interception and soil water contents are intermediate values of the
:ref:`hland_v1_field` example that occur after adding precipitation but before removing
evapotranspiration:

>>> model.intercmodel.sequences.inputs.interceptedwater.series = 2.0
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 99.622389

The first snow cover value represents summer conditions (like in the
:ref:`hland_v1_field` example), while the second represents winter conditions:

>>> model.snowcovermodel.sequences.inputs.snowcover.series = [[0.0], [1.0]]

.. _evap_aet_hbv96_vegetated_soil:

vegetated soil
______________

For "vegetated soils", interception evaporation and soil evapotranspiration are
relevant:

>>> interception(True)
>>> soil(True)
>>> water(False)

For the first hour, interception evaporation equals potential evapotranspiration, while
soil evaporation is smaller due to restricted soil water availability and the priority
of interception evaporation.  In the second hour, the snow cover suppresses soil
evapotranspiration but does not affect interception evaporation:

.. integration-test::

    >>> test()
    |  date | airtemperature | interceptedwater | soilwater | snowcover | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |           19.2 |              2.0 | 99.622389 |       0.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                 0.06896 |               0.021469 |
    | 02/01 |            0.0 |              2.0 | 99.622389 |       1.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                 0.06896 |                    0.0 |

.. _evap_aet_hbv96_bare_soil:

bare soil
_________

Next, we assume a "bare soil" where interception processes are irrelevant:

>>> interception(False)
>>> soil(True)
>>> water(False)

Unlike the :ref:`evap_aet_hbv96_vegetated_soil`, soil evapotranspiration is stronger in
the first hour since interception evaporation does not "consume" any potential
evapotranspiration:

.. integration-test::

    >>> test()
    |  date | airtemperature | interceptedwater | soilwater | snowcover | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |           19.2 |              2.0 | 99.622389 |       0.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                     0.0 |               0.042937 |
    | 02/01 |            0.0 |              2.0 | 99.622389 |       1.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                     0.0 |                    0.0 |

.. _evap_aet_hbv96_sealed_soil:

sealed soil
___________

The following "sealed soil" can evaporate water from its surface but not from its body:

>>> interception(True)
>>> soil(False)
>>> water(False)

The results are consistent with those of the previous examples:

.. integration-test::

    >>> test()
    |  date | airtemperature | interceptedwater | soilwater | snowcover | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |           19.2 |              2.0 | 99.622389 |       0.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                 0.06896 |                    0.0 |
    | 02/01 |            0.0 |              2.0 | 99.622389 |       1.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                 0.06896 |                    0.0 |

.. _evap_aet_hbv96_water_area:

water area
__________

A "water area" comes neither with a solid surface nor a soil body:

>>> interception(False)
>>> soil(False)
>>> water(True)

In the first hour, the actual evaporation from the water area is identical to potential
evapotranspiration.  In the second hour, an assumed ice surface suppresses any
evaporation:

.. integration-test::

    >>> test()
    |  date | airtemperature | interceptedwater | soilwater | snowcover | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |           19.2 |              2.0 | 99.622389 |       0.0 |                          0.06896 |                         0.06896 |                   0.06896 |          0.06896 |                     0.0 |                    0.0 |
    | 02/01 |            0.0 |              2.0 | 99.622389 |       1.0 |                          0.06896 |                         0.06896 |                   0.06896 |              0.0 |                     0.0 |                    0.0 |

unequal potential values, soil
______________________________

The previous examples relied on the |evap_io| submodel, which complies with the
|PETModel_V1| interface that provides only a single potential evapotranspiration value
per time step.  |evap_aet_hbv96| is also compatible with submodels that follow
|PETModel_V2|, which offers separate potential values for interception evaporation,
soil evapotranspiration, and evaporation from water areas.  We use |evap_pet_ambav1| to
demonstrate this functionality:

>>> with model.add_petmodel_v2("evap_pet_ambav1"):
...     hrutype(0)
...     plant(True)
...     measuringheightwindspeed(10.0)
...     leafalbedo(0.2)
...     leafalbedosnow(0.8)
...     groundalbedo(0.2)
...     groundalbedosnow(0.8)
...     leafareaindex(5.0)
...     cropheight(1.0)
...     leafresistance(40.0)
...     wetsoilresistance(100.0)
...     soilresistanceincrease(1.0)
...     wetnessthreshold(0.5)
...     cloudtypefactor(0.2)
...     nightcloudfactor(1.0)
...     with model.add_tempmodel_v2("meteo_temp_io"):
...         hruarea(1.0)
...         temperatureaddend(0.0)
...     with model.add_precipmodel_v2("meteo_precip_io"):
...         hruarea(1.0)
...         precipitationfactor(1.0)
...     with model.add_radiationmodel_v4("meteo_psun_sun_glob_io"):
...         pass
...     with model.add_snowcovermodel_v1("dummy_snowcover"):
...         pass

After recreating the |IntegrationTest| object, we can define the time series and
initial conditions required by |evap_pet_ambav1|:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

>>> model.petmodel.sequences.inputs.windspeed.series = 2.0
>>> model.petmodel.sequences.inputs.relativehumidity.series = 80.0
>>> model.petmodel.sequences.inputs.atmosphericpressure.series = 1000.0
>>> model.petmodel.tempmodel.sequences.inputs.temperature.series = 19.2, 0.0
>>> model.petmodel.precipmodel.sequences.inputs.precipitation.series = 0.0
>>> model.petmodel.radiationmodel.sequences.inputs.sunshineduration.series = 6.0
>>> model.petmodel.radiationmodel.sequences.inputs.possiblesunshineduration.series = 16.0
>>> model.petmodel.radiationmodel.sequences.inputs.globalradiation.series = 190.0
>>> model.petmodel.snowcovermodel.sequences.inputs.snowcover.series = [[0.0], [1.0]]

>>> test.inits = (
...     (model.petmodel.sequences.states.soilresistance, 100.0),
...     (model.petmodel.sequences.logs.loggedprecipitation, [0.0]),
...     (model.petmodel.sequences.logs.loggedpotentialsoilevapotranspiration, [1.0])
... )

The time series of air temperature, intercepted water, soil water, and the snow cover
degree correspond to the previous examples:

>>> model.tempmodel.sequences.inputs.temperature.series = 19.2, 0.0
>>> model.intercmodel.sequences.inputs.interceptedwater.series = 2.0
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 99.622389
>>> model.snowcovermodel.sequences.inputs.snowcover.series = [[0.0], [1.0]]

The following results are comparable to the :ref:`evap_aet_hbv96_vegetated_soil`
example:

.. integration-test::

    >>> interception(True)
    >>> soil(True)
    >>> water(False)
    >>> test()
    |  date | airtemperature | interceptedwater | soilwater | snowcover | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |           19.2 |              2.0 | 99.622389 |       0.0 |                          3.42978 |                        2.604398 |                       0.0 |              0.0 |                     2.0 |               1.422518 |
    | 02/01 |            0.0 |              2.0 | 99.622389 |       1.0 |                         0.482794 |                         0.30027 |                       0.0 |              0.0 |                0.482794 |                    0.0 |

unequal potential values, water
_______________________________

For water areas, |evap_aet_hbv96| takes the potential water evaporation calculated by
|evap_pet_ambav1| as actual water evaporation, as long as the occurrence of an ice
surface does not suppress evaporation:

.. integration-test::

    >>> interception(False)
    >>> soil(False)
    >>> water(True)
    >>> test()
    |  date | airtemperature | interceptedwater | soilwater | snowcover | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |           19.2 |              2.0 | 99.622389 |       0.0 |                              0.0 |                             0.0 |                  3.576338 |         3.576338 |                     0.0 |                    0.0 |
    | 02/01 |            0.0 |              2.0 | 99.622389 |       1.0 |                              0.0 |                             0.0 |                  0.449853 |              0.0 |                     0.0 |                    0.0 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import aetinterfaces
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2B,
    evap_model.Main_PET_PETModel_V1,
    evap_model.Main_PET_PETModel_V2,
    evap_model.Main_IntercModel_V1,
    evap_model.Main_SoilWaterModel_V1,
    evap_model.Main_SnowCoverModel_V1,
    evap_model.Sub_ETModel,
    aetinterfaces.AETModel_V1,
):
    """The HBV96 version of HydPy-Evap for calculating actual evapotranspiration."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V1,
        evap_model.Determine_SoilEvapotranspiration_V1,
        evap_model.Determine_WaterEvaporation_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V1,
        evap_model.Determine_SoilEvapotranspiration_V1,
        evap_model.Determine_WaterEvaporation_V1,
        evap_model.Get_WaterEvaporation_V1,
        evap_model.Get_InterceptionEvaporation_V1,
        evap_model.Get_SoilEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_AirTemperature_V1,
        evap_model.Calc_PotentialInterceptionEvaporation_PETModel_V1,
        evap_model.Calc_PotentialInterceptionEvaporation_PETModel_V2,
        evap_model.Calc_PotentialInterceptionEvaporation_V3,
        evap_model.Calc_PotentialWaterEvaporation_PETModel_V1,
        evap_model.Calc_PotentialWaterEvaporation_PETModel_V2,
        evap_model.Calc_PotentialWaterEvaporation_V1,
        evap_model.Calc_WaterEvaporation_V1,
        evap_model.Calc_InterceptedWater_V1,
        evap_model.Calc_InterceptionEvaporation_V1,
        evap_model.Calc_SoilWater_V1,
        evap_model.Calc_SnowCover_V1,
        evap_model.Calc_PotentialSoilEvapotranspiration_PETModel_V1,
        evap_model.Calc_PotentialSoilEvapotranspiration_PETModel_V2,
        evap_model.Calc_PotentialSoilEvapotranspiration_V2,
        evap_model.Calc_SoilEvapotranspiration_V1,
        evap_model.Update_SoilEvapotranspiration_V1,
        evap_model.Update_SoilEvapotranspiration_V2,
        evap_model.Calc_AirTemperature_TempModel_V1,
        evap_model.Calc_AirTemperature_TempModel_V2,
        evap_model.Calc_InterceptedWater_IntercModel_V1,
        evap_model.Calc_SoilWater_SoilWaterModel_V1,
        evap_model.Calc_SnowCover_SnowCoverModel_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    petmodel = modeltools.SubmodelProperty(
        petinterfaces.PETModel_V1, petinterfaces.PETModel_V2
    )
    intercmodel = modeltools.SubmodelProperty(stateinterfaces.IntercModel_V1)
    soilwatermodel = modeltools.SubmodelProperty(stateinterfaces.SoilWaterModel_V1)
    snowcovermodel = modeltools.SubmodelProperty(stateinterfaces.SnowCoverModel_V1)


tester = Tester()
cythonizer = Cythonizer()
