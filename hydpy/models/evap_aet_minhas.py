# pylint: disable=line-too-long, unused-wildcard-import
"""|evap_aet_minhas| serves as a submodel that supplies its main model with estimates
of evapotranspiration from soils and evaporation from interception storages and water
areas.  Therefore, it requires potential evapotranspiration data calculated by a
sub-submodel.  See, for example, the documentation of application model |lland_dd|,
where |evap_ret_tw2002| calculates grass reference evapotranspiration values after
Turc-Wendling :cite:p:`ref-DVWK`, which |evap_pet_mlc| converts to month- and land
type-specific potential evapotranspiration values.

Integration tests
=================

.. how_to_understand_integration_tests::

According to the intended usage as a submodel, |evap_aet_minhas| requires no
connections to any nodes.  Hence, assigning a model instance to a blank |Element|
instance is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_aet_minhas import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

We perform the integration test for three simulation days:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

Besides the number of hydrological response units, which |evap_aet_minhas| usually
receives from its main model in real applications, we only need to define values for
the control parameters |MaxSoilWater| and |DisseFactor|:

>>> nmbhru(1)
>>> maxsoilwater(200.0)
>>> dissefactor(5.0)

We add submodels of type |evap_ret_io|, |dummy_interceptedwater|, and |dummy_soilwater|
for providing pre-defined values of potential evapotranspiration (identical values for
potential interception evaporation and soil evapotranspiration), intercepted water, and
soil water:

>>> with model.add_petmodel_v1("evap_ret_io"):
...     hruarea(1.0)
...     evapotranspirationfactor(1.0)
>>> with model.add_intercmodel_v1("dummy_interceptedwater"):
...     pass
>>> with model.add_soilwatermodel_v1("dummy_soilwater"):
...     pass

Now, we can initialise an |IntegrationTest| object:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

All of the following tests share the same input time series.  Reference
evapotranspiration (used as potential evapotranspiration) and the initial soil water
content are identical for all three days, while the initial amount of intercepted water
varies from 0 to 2 mm, of which the last value equals reference evaporation:

>>> model.petmodel.sequences.inputs.referenceevapotranspiration.series = 2.0
>>> model.intercmodel.sequences.inputs.interceptedwater.series = [[0.0], [1.0], [2.0]]
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 100.0

.. _evap_aet_minhas_vegetated_soil:

vegetated soil
______________

For "vegetated soils", interception evaporation and soil evapotranspiration are
relevant:

>>> interception(True)
>>> soil(True)
>>> water(False)

The results for the second day show that the sum of interception evaporation and soil
water evapotranspiration never exceeds the given potential evapotranspiration:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     0.0 |               1.717962 |
    | 02/01 |              1.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     1.0 |               0.858981 |
    | 03/01 |              2.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     2.0 |                    0.0 |

.. _evap_aet_minhas_bare_soil:

bare soil
_________

Next, we assume a "bare soil" where interception processes are irrelevant:

>>> interception(False)
>>> soil(True)
>>> water(False)

Due to ignoring possible interception evaporation, soil water evapotranspiration is
identical for all three days:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     0.0 |               1.717962 |
    | 02/01 |              1.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     0.0 |               1.717962 |
    | 03/01 |              2.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     0.0 |               1.717962 |

.. _evap_aet_minhas_sealed_soil:

sealed soil
___________

The following "sealed soil" can evaporate water from its surface but not from its body:

>>> interception(True)
>>> soil(False)
>>> water(False)

All results are as to be expected:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     0.0 |                    0.0 |
    | 02/01 |              1.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     1.0 |                    0.0 |
    | 03/01 |              2.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              0.0 |                     2.0 |                    0.0 |

.. _evap_aet_minhas_water_area:

water area
__________

A "water area" comes neither with a solid surface nor a soil body:

>>> interception(False)
>>> soil(False)
>>> water(True)

There is never any difference between potential and actual evaporation for water areas:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              2.0 |                     0.0 |                    0.0 |
    | 02/01 |              1.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              2.0 |                     0.0 |                    0.0 |
    | 03/01 |              2.0 |     100.0 |                              2.0 |                             2.0 |                       2.0 |              2.0 |                     0.0 |                    0.0 |

.. _evap_aet_minhas_unequal_potential_values_soil:

unequal potential values, soil
______________________________

The previous examples relied on the |evap_ret_io| submodel, which complies with the
|PETModel_V1| interface that provides only a single potential evapotranspiration value
per time step.  |evap_aet_minhas| is also compatible with submodels that follow
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
>>> model.petmodel.tempmodel.sequences.inputs.temperature.series = 15.0
>>> model.petmodel.precipmodel.sequences.inputs.precipitation.series = 0.0
>>> model.petmodel.radiationmodel.sequences.inputs.sunshineduration.series = 6.0
>>> model.petmodel.radiationmodel.sequences.inputs.possiblesunshineduration.series = 16.0
>>> model.petmodel.radiationmodel.sequences.inputs.globalradiation.series = 190.0
>>> model.petmodel.snowcovermodel.sequences.inputs.snowcover.series = 0.0

>>> test.inits = (
...     (model.petmodel.sequences.states.soilresistance, 100.0),
...     (model.petmodel.sequences.logs.loggedprecipitation, [0.0]),
...     (model.petmodel.sequences.logs.loggedpotentialsoilevapotranspiration, [1.0])
... )

The time series of intercepted and soil water agree with the previous examples:

>>> model.intercmodel.sequences.inputs.interceptedwater.series = [[0.0], [1.0], [2.0]]
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 100.0

The following results are comparable to the :ref:`evap_aet_minhas_vegetated_soil`
example.  As long as (positive) potential interception evaporation is larger than
(positive) potential soil evapotranspiration, the sum of actual interception
evaporation and actual soil evapotranspiration should never exceed potential
interception evaporation:

.. integration-test::

    >>> interception(True)
    >>> soil(True)
    >>> water(False)
    >>> test()
    |  date | interceptedwater | soilwater | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                         3.017202 |                        2.203966 |                       0.0 |              0.0 |                     0.0 |               1.893165 |
    | 02/01 |              1.0 |     100.0 |                         3.017202 |                        2.184337 |                       0.0 |              0.0 |                     1.0 |               1.254435 |
    | 03/01 |              2.0 |     100.0 |                         3.017202 |                        2.169588 |                       0.0 |              0.0 |                     2.0 |               0.628295 |

unequal potential values, water
_______________________________

For water areas, |evap_aet_minhas| takes the potential water evaporation calculated by
|evap_pet_ambav1| as actual water evaporation:

.. integration-test::

    >>> interception(False)
    >>> soil(False)
    >>> water(True)
    >>> test()
    |  date | interceptedwater | soilwater | potentialinterceptionevaporation | potentialsoilevapotranspiration | potentialwaterevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                              0.0 |                             0.0 |                  3.142563 |         3.142563 |                     0.0 |                    0.0 |
    | 02/01 |              1.0 |     100.0 |                              0.0 |                             0.0 |                  3.142563 |         3.142563 |                     0.0 |                    0.0 |
    | 03/01 |              2.0 |     100.0 |                              0.0 |                             0.0 |                  3.142563 |         3.142563 |                     0.0 |                    0.0 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import aetinterfaces
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_PET_PETModel_V1,
    evap_model.Main_PET_PETModel_V2,
    evap_model.Main_IntercModel_V1,
    evap_model.Main_SoilWaterModel_V1,
    evap_model.Sub_ETModel,
    aetinterfaces.AETModel_V1,
):
    """|evap_aet_minhas.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-AET-Minhas",
        description="actual evapotranspiration based on the Minhas equation",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V1,
        evap_model.Determine_SoilEvapotranspiration_V2,
        evap_model.Determine_WaterEvaporation_V2,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V1,
        evap_model.Determine_SoilEvapotranspiration_V2,
        evap_model.Determine_WaterEvaporation_V2,
        evap_model.Get_WaterEvaporation_V1,
        evap_model.Get_InterceptionEvaporation_V1,
        evap_model.Get_SoilEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_PotentialInterceptionEvaporation_PETModel_V1,
        evap_model.Calc_PotentialInterceptionEvaporation_PETModel_V2,
        evap_model.Calc_PotentialInterceptionEvaporation_V3,
        evap_model.Calc_PotentialWaterEvaporation_PETModel_V1,
        evap_model.Calc_PotentialWaterEvaporation_PETModel_V2,
        evap_model.Calc_PotentialWaterEvaporation_V1,
        evap_model.Calc_WaterEvaporation_V2,
        evap_model.Calc_InterceptedWater_V1,
        evap_model.Calc_InterceptionEvaporation_V1,
        evap_model.Calc_SoilWater_V1,
        evap_model.Calc_PotentialSoilEvapotranspiration_PETModel_V1,
        evap_model.Calc_PotentialSoilEvapotranspiration_PETModel_V2,
        evap_model.Calc_PotentialSoilEvapotranspiration_V2,
        evap_model.Calc_SoilEvapotranspiration_V2,
        evap_model.Update_SoilEvapotranspiration_V3,
        evap_model.Calc_InterceptedWater_IntercModel_V1,
        evap_model.Calc_SoilWater_SoilWaterModel_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMODELS = ()

    petmodel = modeltools.SubmodelProperty(
        petinterfaces.PETModel_V1, petinterfaces.PETModel_V2
    )
    intercmodel = modeltools.SubmodelProperty(stateinterfaces.IntercModel_V1)
    soilwatermodel = modeltools.SubmodelProperty(stateinterfaces.SoilWaterModel_V1)


tester = Tester()
cythonizer = Cythonizer()
