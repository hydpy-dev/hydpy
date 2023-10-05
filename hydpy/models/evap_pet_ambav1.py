# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""A submodel that implements the AMBAV 1.0 equations :cite:p:`ref-Löpmeier2014` for
calculating potential evapotranspiration.

.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN
.. _`German Meteorological Service (DWD)`: https://www.dwd.de/EN/specialusers/agriculture/agriculture_node.html
.. _`MORSIM/AMBAV issue`: https://github.com/hydpy-dev/hydpy/issues/118

|evap_pet_ambav1| is a submodel that supplies its main model with estimates of
potential evapotranspiration from soils and potential evaporation from interception
storages and water areas.  It closely follows version 1.0 of the AMBAV model, as
described by :cite:t:`ref-Löpmeier2014`, which was developed and used by the German
Meteorological Service (DWD) to calculate soil evapotranspiration and interception
evaporation for different crops based on the Penman-Monteith equation.  We added a
routine for calculating evaporation from water areas based on the pure Penman equation.
The `MORSIM/AMBAV issue`_ on GitHub discusses this and other decisions in detail.  We
implemented |evap_pet_ambav1| on behalf of the `German Federal Institute of Hydrology
(BfG)`_ for modelling large river basins in central Europe.

|evap_pet_ambav1| requires additional data about the catchment's current state, which
it usually queries from its main model, if possible:

 * The current air temperature.
 * The current precipitation.
 * The snow cover degree.

Integration tests
=================

.. how_to_understand_integration_tests::

The design of the following integration tests is similar to the one chosen for
|evap_morsim|  allow comparing both models as well as possible.

We prepare a simulation period of three days for the first examples:

>>> from hydpy import pub
>>> pub.timegrids = "2000-08-01", "2000-08-04", "1d"

According to the intended usage as a submodel, |evap_pet_ambav1| requires no
connections to any nodes.  Hence, assigning a model instance to a blank |Element|
instance is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_pet_ambav1 import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

The following parameter settings are comparable to the ones selected for |evap_morsim|:

>>> nmbhru(1)
>>> hrutype(0)
>>> measuringheightwindspeed(10.0)
>>> leafalbedo(0.2)
>>> leafalbedosnow(0.8)
>>> groundalbedo(0.2)
>>> groundalbedosnow(0.8)
>>> leafalbedo(0.2)
>>> leafalbedosnow(0.8)
>>> leafareaindex(5.0)
>>> cropheight(10.0)
>>> leafresistance(40.0)

The following parameters have no direct equivalents in |evap_morsim|:

>>> wetsoilresistance(100.0)
>>> soilresistanceincrease(1.0)
>>> wetnessthreshold(0.5)
>>> cloudtypefactor(0.2)
>>> nightcloudfactor(1.0)

We add submodels of type |meteo_temp_io|, |meteo_precip_io|, and |dummy_snowcover| that
supply additional information on the catchment's state instead of complicating the
comparisons by introducing a complex main model:

>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     hruarea(1.0)
...     temperatureaddend(0.0)
>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     hruarea(1.0)
...     precipitationfactor(1.0)
>>> with model.add_snowcovermodel_v1("dummy_snowcover"):
...     pass

Now, we can initialise an |IntegrationTest| object:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

The following meteorological input and snow cover data agrees also with the first
|evap_morsim| examples:

>>> inputs.windspeed.series = 2.0
>>> inputs.relativehumidity.series = 80.0
>>> inputs.atmosphericpressure.series = 1000.0
>>> inputs.sunshineduration.series = 6.0
>>> inputs.possiblesunshineduration.series = 16.0
>>> inputs.globalradiation.series = 190.0
>>> model.tempmodel.sequences.inputs.temperature.series = 15.0
>>> model.snowcovermodel.sequences.inputs.snowcover.series = 0.0

Only |evap_pet_ambav1| requires precipitation data to simulate the wetness of the
topmost soil layer for adjusting the soil surface's albedo and resistance.  We define
precipitation to occur on the second day:

>>> model.precipmodel.sequences.inputs.precipitation.series = 0.0, 10.0, 0.0

In contrast to |evap_morsim|, |evap_pet_ambav1| even requires logged values when
applied on daily timesteps to keep track of the temporal persistency of the topmost
soil layer's wetness:

>>> test.inits = ((states.soilresistance, 100.0),
...               (logs.loggedprecipitation, [0.0]),
...               (logs.loggedpotentialsoilevapotranspiration, [1.0]))

non-tree vegetation
___________________

The following configuration corresponds to the :ref:`evap_morsim_non_tree_vegetation`
example of |evap_morsim|:

>>> interception(True)
>>> soil(True)
>>> plant(True)
>>> tree(False)
>>> water(False)

In the |evap_morsim| example, the resulting soil evapotranspiration values differ due
to different amounts of intercepted water.  In contrast, |evap_pet_ambav1| calculates
only potential values and thus does not consider storage contents.  The differences
between the individual days stem from the changing topmost soil layer's wetness.  In
this context, note that the precipitation event of the second day only affects the
results of the third day and later.  Also, note that the potential interception and
soil evapotranspiration estimates of |evap_pet_ambav1| are much larger than for
|evap_morsim| (we discuss this difference in the `MORSIM/AMBAV issue`_):

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | adjustedwindspeed10m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  2.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             12.381026 |               55.393952 |       0.0 |           0.0 |                0.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         8.211488 |                        3.073332 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          124.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  2.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             12.381026 |                57.24078 |       0.0 |          10.0 |                0.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         8.211488 |                        3.010527 |                             3.073332 |              0.0 |                   0.0 |         0.375 |          148.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  2.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             12.381026 |               52.869385 |       0.0 |           0.0 |               10.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         8.211488 |                        3.163548 |                             3.010527 |              0.0 |                   0.0 |         0.375 |          100.0 |

tree-like vegetation
____________________

All effects of enabling the flag for tree-like vegetation (like in the
:ref:`evap_morsim_deciduous_trees` example of |evap_morsim|) are due to a wind speed
reduction that tries to adjust wind speed measurements over short grass to forest
sites:

.. integration-test::

    >>> tree(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | adjustedwindspeed10m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  1.2 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |               55.393952 |       0.0 |           0.0 |                0.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                        2.768363 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          124.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  1.2 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |                57.24078 |       0.0 |          10.0 |                0.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                        2.722902 |                             2.768363 |              0.0 |                   0.0 |         0.375 |          148.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  1.2 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |               52.869385 |       0.0 |           0.0 |               10.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                         2.83302 |                             2.722902 |              0.0 |                   0.0 |         0.375 |          100.0 |

water area
__________

Switching from vegetated soil to an open water area requires setting the crop height to
zero:

>>> interception(False)
>>> soil(False)
>>> plant(False)
>>> tree(False)
>>> water(True)
>>> cropheight(0.0)

While |evap_morsim| estimates an evaporation rate of 3.2 mm/day in the
:ref:`evap_water_area` example, |evap_pet_ambav1| estimates only 1.9 mm/day:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | adjustedwindspeed10m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  2.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |           0.0 |                0.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  1.0 |         1.890672 |              1.890672 |         0.375 |            nan |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  2.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |          10.0 |                0.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         1.890672 |              1.890672 |         0.375 |            nan |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  2.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |           0.0 |               10.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         1.890672 |              1.890672 |         0.375 |            nan |

snow
____

Now, we demonstrate the effect of snow on potential evapotranspiration from land areas
by setting different snow cover degrees:

>>> interception(True)
>>> soil(True)
>>> plant(True)
>>> tree(True)
>>> water(False)
>>> cropheight(10.0)
>>> model.snowcovermodel.sequences.inputs.snowcover.series = [0.0], [0.5], [1.0]

We set all precipitation values to 10 mm to focus only on the influence of the snow
cover:

>>> model.precipmodel.sequences.inputs.precipitation.series = 10.0
>>> test.inits.loggedprecipitation = 10.0

In contrast to |evap_morsim|, as discussed in the
:ref:`evap_morsim_snow_on_non_tree_vegetation` example, |evap_pet_ambav1| never
suppresses evapotranspiration completely but adjusts the current albedo to the given
snow-specific values, which are usually larger than those of the leaf and soil surfaces
and so usually reduces evapotranspiration:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | adjustedwindspeed10m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  1.2 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |               52.869385 |       0.0 |          10.0 |               10.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                         2.83302 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          100.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  1.2 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.5 |                 0.375 |             20.635044 |               52.869385 |       0.5 |          10.0 |               10.0 |                  95.0 |            71.952081 |    23.047919 |     1.728594 |                         4.467744 |                        2.282495 |                              2.83302 |              0.0 |                   0.0 |         0.375 |          100.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                  1.2 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.8 |                 0.375 |             20.635044 |               52.869385 |       1.0 |          10.0 |               10.0 |                  38.0 |            67.962081 |   -29.962081 |    -2.247156 |                         3.390149 |                         1.73197 |                             2.282495 |              0.0 |                   0.0 |         0.375 |          100.0 |

hourly simulation, land
_______________________

The following examples deal with an hourly simulation step:

>>> pub.timegrids = "2000-08-01", "2000-08-02", "1h"

We need to restore the values of all time-dependent parameters:

>>> for parameter in model.parameters.fixed:
...     parameter.restore()
>>> test = IntegrationTest(element)

The following meteorological input data agrees with the
:ref:`evap_morsim_hourly_simulation_land` example of |evap_morsim|:

>>> inputs.atmosphericpressure.series = (
...     1015.0, 1015.0, 1015.0, 1015.0, 1015.0, 1015.0, 1015.0, 1015.0, 1016.0, 1016.0,
...     1016.0, 1016.0, 1016.0, 1016.0, 1016.0, 1016.0, 1016.0, 1016.0, 1016.0, 1016.0,
...     1016.0, 1016.0, 1017.0, 1017.0)
>>> inputs.windspeed.series = (
...     0.8, 0.8, 0.8, 0.8, 0.8, 0.6, 0.9, 0.9, 0.9, 1.3, 1.5, 1.2, 1.3, 1.5, 1.9, 1.9,
...     2.3, 2.4, 2.5, 2.5, 2.2, 1.7, 1.7, 2.3)
>>> inputs.relativehumidity.series = (
...     95.1, 94.9, 95.9, 96.7, 97.2, 97.5, 97.7, 97.4, 96.8, 86.1, 76.8, 71.8, 67.5,
...     66.1, 63.4, 62.4, 61.1, 62.1, 67.0, 74.5, 81.2, 86.9, 90.1, 90.9)
>>> inputs.sunshineduration.series = (
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.5, 0.7, 0.8, 0.5, 0.4, 0.5,
...     0.5, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0)
>>> inputs.possiblesunshineduration.series = (
...     0.0, 0.0, 0.0, 0.0, 0.4, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
...     1.0, 1.0, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0)
>>> inputs.globalradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 1.9, 21.9, 57.3, 109.3, 170.9, 311.8, 501.6, 615.0, 626.5,
...     496.1, 419.5, 387.9, 278.5, 137.1, 51.1, 13.6, 0.2, 0.0, 0.0, 0.0)

In contrast to |evap_morsim|, |evap_pet_ambav1| does not require "daily" averages or
sums of meteorological input data but calculates, e.g., hourly water area evaporation
values and aggregates them to daily values later.  But it needs to remember the last
determined cloud coverage degree (which is only estimateable at daytime) and other
factors related to the topmost soil layer's wetness calculations:

>>> test.inits = ((states.soilresistance, 100.0),
...               (states.cloudcoverage, 0.3),
...               (logs.loggedprecipitation, 0.0),
...               (logs.loggedwaterevaporation, 0.0),
...               (logs.loggedpotentialsoilevapotranspiration, 0.0))

The contrived day is warm, free of snow and rain:

>>> model.tempmodel.sequences.inputs.temperature.series = (
...     16.9, 16.6, 16.4, 16.3, 16.0, 15.9, 16.0, 16.6, 17.4, 19.0, 20.3, 21.4, 21.3,
...     21.8, 22.9, 22.7, 22.5, 21.9, 21.4, 20.7, 19.4, 17.8, 17.0, 16.4)
>>> model.snowcovermodel.sequences.inputs.snowcover.series = 0.0
>>> model.precipmodel.sequences.inputs.precipitation.series = 0.0

Considering the :ref:`evap_morsim_hourly_simulation_land` example, |evap_pet_ambav1|
estimates higher potential interception evaporation rates and potential soil
evapotranspiration rates that are (as to be expected) higher but roughly comparable to
the actual soil evapotranspiration rates of |evap_morsim|:

.. integration-test::

    >>> test("evap_pet_ambav1_hourly_simulation_land",
    ...      axis1=(fluxes.potentialinterceptionevaporation,
    ...             fluxes.potentialsoilevapotranspiration))
    |                date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | adjustedwindspeed10m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-01 00:00:00 |             95.1 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.9 |                 0.48 |                19.254836 |                      1.221127 |            18.311349 |     996.688651 |   1.210743 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |                   0.0 |            66.097029 |   -66.097029 |    -8.262129 |                        -0.037693 |                       -0.023944 |                                  0.0 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-01 01:00:00 |             94.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.6 |                 0.48 |                18.891521 |                      1.200918 |            17.928054 |     997.071946 |   1.212171 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |                   0.0 |             66.49025 |    -66.49025 |    -8.311281 |                        -0.037115 |                       -0.023484 |                            -0.023944 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-01 02:00:00 |             95.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.4 |                 0.48 |                18.652661 |                      1.187604 |            17.887902 |     997.112098 |   1.213026 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |                   0.0 |            66.746025 |   -66.746025 |    -8.343253 |                        -0.040693 |                       -0.025679 |                            -0.047427 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-01 03:00:00 |             96.7 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.3 |                 0.48 |                18.534226 |                      1.180995 |            17.922597 |     997.077403 |   1.213429 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |                   0.0 |            66.871985 |   -66.871985 |    -8.358998 |                        -0.043513 |                       -0.027423 |                            -0.073107 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-01 04:00:00 |             97.2 |       0.8 |              1015.0 |              0.0 |                      0.4 |             1.9 |           16.0 |                 0.48 |                18.182867 |                      1.161352 |            17.673747 |     997.326253 |   1.214802 |           0.2 |                   0.3 |             51.587609 |               62.254838 |       0.0 |           0.0 |                0.0 |                  1.52 |            67.348507 |   -65.828507 |    -6.253708 |                        -0.045991 |                       -0.032045 |                            -0.100529 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-01 05:00:00 |             97.5 |       0.6 |              1015.0 |              0.0 |                      1.0 |            21.9 |           15.9 |                 0.36 |                18.067051 |                      1.154867 |            17.615375 |     997.384625 |   1.215249 |           0.2 |                   0.0 |             68.783479 |               44.486064 |       0.0 |           0.0 |                0.0 |                 17.52 |            74.181953 |   -56.661953 |    -2.833098 |                        -0.043738 |                       -0.035442 |                            -0.132575 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-01 06:00:00 |             97.7 |       0.9 |              1015.0 |              0.0 |                      1.0 |            57.3 |           16.0 |                 0.54 |                18.182867 |                      1.161352 |            17.764661 |     997.235339 |    1.21476 |           0.2 |                   0.0 |             45.855653 |               44.486064 |       0.0 |           0.0 |                0.0 |                 45.84 |            76.055111 |   -30.215111 |    -1.510756 |                         -0.01787 |                       -0.013239 |                            -0.168017 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-01 07:00:00 |             97.4 |       0.9 |              1015.0 |              0.0 |                      1.0 |           109.3 |           16.6 |                 0.54 |                18.891521 |                      1.200918 |            18.400342 |     996.599658 |   1.211956 |           0.2 |                   0.0 |             45.855653 |               44.486064 |       0.0 |           0.0 |                0.0 |                 87.44 |            78.285119 |     9.154881 |     0.457744 |                         0.018505 |                        0.013785 |                            -0.181255 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-01 08:00:00 |             96.8 |       0.9 |              1016.0 |              0.0 |                      1.0 |           170.9 |           17.4 |                 0.54 |                19.873972 |                      1.255448 |            19.238005 |     996.761995 |   1.209438 |           0.2 |                   0.0 |             45.855653 |               44.486064 |       0.0 |           0.0 |                0.0 |                136.72 |            80.755926 |    55.964074 |     2.798204 |                         0.063979 |                         0.04801 |                             -0.16747 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-01 09:00:00 |             86.1 |       1.3 |              1016.0 |              0.2 |                      1.0 |           311.8 |           19.0 |                 0.78 |                21.973933 |                      1.370827 |            18.919557 |     997.080443 |   1.202958 |           0.2 |                   0.2 |             31.746221 |               44.486064 |       0.0 |           0.0 |                0.0 |                249.44 |            83.809146 |   165.630854 |     8.281543 |                         0.239608 |                        0.164897 |                             -0.11946 |              0.0 |                   0.0 |           0.2 |          100.0 |
    | 2000-08-01 10:00:00 |             76.8 |       1.5 |              1016.0 |              0.5 |                      1.0 |           501.6 |           20.3 |                  0.9 |                23.820593 |                      1.471068 |            18.294216 |     997.705784 |    1.19791 |           0.2 |                   0.5 |             27.513392 |               45.139282 |       0.0 |           0.0 |                0.0 |                401.28 |            78.073919 |   323.206081 |    16.160304 |                         0.476886 |                        0.316774 |                             0.045437 |              0.0 |                   0.0 |           0.5 |          124.0 |
    | 2000-08-01 11:00:00 |             71.8 |       1.2 |              1016.0 |              0.7 |                      1.0 |           615.0 |           21.4 |                 0.72 |                25.487706 |                      1.560666 |            18.300173 |     997.699827 |   1.193433 |           0.2 |                   0.7 |              34.39174 |               45.591614 |       0.0 |           0.0 |                0.0 |                 492.0 |            65.478136 |   426.521864 |    21.326093 |                         0.582665 |                        0.418613 |                             0.362211 |              0.0 |                   0.0 |           0.7 |          148.0 |
    | 2000-08-01 12:00:00 |             67.5 |       1.3 |              1016.0 |              0.8 |                      1.0 |           626.5 |           21.3 |                 0.78 |                 25.33205 |                      1.552334 |            17.099134 |     998.900866 |   1.194376 |           0.2 |                   0.8 |             31.746221 |               45.923379 |       0.0 |           0.0 |                0.0 |                 501.2 |            55.930635 |   445.269365 |    22.263468 |                         0.641097 |                        0.448553 |                             0.780824 |              0.0 |                   0.0 |           0.8 |          172.0 |
    | 2000-08-01 13:00:00 |             66.1 |       1.5 |              1016.0 |              0.5 |                      1.0 |           496.1 |           21.8 |                  0.9 |                26.118719 |                       1.59437 |            17.264473 |     998.735527 |   1.192277 |           0.2 |                   0.5 |             27.513392 |               46.177112 |       0.0 |           0.0 |                0.0 |                396.88 |             74.71054 |    322.16946 |    16.108473 |                         0.567792 |                        0.381395 |                             1.229378 |              0.0 |                   0.0 |           0.5 |          196.0 |
    | 2000-08-01 14:00:00 |             63.4 |       1.9 |              1016.0 |              0.4 |                      1.0 |           419.5 |           22.9 |                 1.14 |                27.924898 |                      1.690242 |            17.704385 |     998.295615 |   1.187651 |           0.2 |                   0.4 |             21.721099 |               46.377447 |       0.0 |           0.0 |                0.0 |                 335.6 |            74.508507 |   261.091493 |    13.054575 |                         0.611457 |                        0.383042 |                             1.610773 |              0.0 |                   0.0 |           0.4 |          220.0 |
    | 2000-08-01 15:00:00 |             62.4 |       1.9 |              1016.0 |              0.5 |                      1.0 |           387.9 |           22.7 |                 1.14 |                27.588616 |                      1.672458 |            17.215297 |     998.784703 |   1.188672 |           0.2 |                   0.5 |             21.721099 |               46.539635 |       0.0 |           0.0 |                0.0 |                310.32 |            66.707316 |   243.612684 |    12.180634 |                         0.601497 |                        0.375237 |                             1.993815 |              0.0 |                   0.0 |           0.5 |          244.0 |
    | 2000-08-01 16:00:00 |             61.1 |       2.3 |              1016.0 |              0.5 |                      1.0 |           278.5 |           22.5 |                 1.38 |                27.255876 |                      1.654832 |             16.65334 |      999.34666 |   1.189726 |           0.2 |                   0.5 |             17.943516 |               46.673625 |       0.0 |           0.0 |                0.0 |                 222.8 |            61.019731 |   161.780269 |     8.089013 |                         0.608154 |                        0.349995 |                             2.369052 |              0.0 |                   0.0 |           0.5 |          268.0 |
    | 2000-08-01 17:00:00 |             62.1 |       2.4 |              1016.0 |              0.3 |                      1.0 |           137.1 |           21.9 |                 1.44 |                26.278588 |                      1.602891 |            16.319003 |     999.680997 |   1.192295 |           0.2 |                   0.3 |              17.19587 |               46.786182 |       0.0 |           0.0 |                0.0 |                109.68 |            65.664882 |    44.015118 |     2.200756 |                         0.492772 |                        0.275402 |                             2.719048 |              0.0 |                   0.0 |           0.3 |          292.0 |
    | 2000-08-01 18:00:00 |             67.0 |       2.5 |              1016.0 |              0.1 |                      1.0 |            51.1 |           21.4 |                  1.5 |                25.487706 |                      1.560666 |            17.076763 |     998.923237 |    1.19398 |           0.2 |                   0.1 |             16.508035 |               46.882068 |       0.0 |           0.0 |                0.0 |                 40.88 |            67.357383 |   -26.477383 |    -1.323869 |                         0.377512 |                        0.205219 |                              2.99445 |              0.0 |                   0.0 |           0.1 |          316.0 |
    | 2000-08-01 19:00:00 |             74.5 |       2.5 |              1016.0 |              0.0 |                      1.0 |            13.6 |           20.7 |                  1.5 |                24.415439 |                      1.503132 |            18.189502 |     997.810498 |   1.196326 |           0.2 |                   0.0 |             16.508035 |               46.964732 |       0.0 |           0.0 |                0.0 |                 10.88 |            67.126066 |   -56.246066 |    -2.812303 |                         0.252768 |                        0.135645 |                             3.199669 |              0.0 |                   0.0 |           0.0 |          340.0 |
    | 2000-08-01 20:00:00 |             81.2 |       2.2 |              1016.0 |              0.0 |                      0.2 |             0.2 |           19.4 |                 1.32 |                 22.52831 |                      1.401035 |            18.292988 |     997.707012 |   1.201595 |           0.2 |                   0.0 |             18.759131 |              126.929813 |       0.0 |           0.0 |                0.0 |                  0.16 |            68.418576 |   -68.258576 |    -7.508443 |                         0.133349 |                        0.042258 |                             3.335314 |              0.0 |                   0.0 |           0.0 |          364.0 |
    | 2000-08-01 21:00:00 |             86.9 |       1.7 |              1016.0 |              0.0 |                      0.0 |             0.0 |           17.8 |                 1.02 |                20.381763 |                      1.283491 |            17.711752 |     998.288248 |   1.208466 |           0.2 |                   0.0 |             24.276522 |              229.198312 |       0.0 |           0.0 |                0.0 |                   0.0 |            70.667062 |   -70.667062 |    -8.833383 |                         0.040887 |                        0.009758 |                             3.377573 |              0.0 |                   0.0 |           0.0 |          388.0 |
    | 2000-08-01 22:00:00 |             90.1 |       1.7 |              1017.0 |              0.0 |                      0.0 |             0.0 |           17.0 |                 1.02 |                19.377294 |                      1.227926 |            17.458941 |     999.541059 |   1.213114 |           0.2 |                   0.0 |             24.276522 |              237.366255 |       0.0 |           0.0 |                0.0 |                   0.0 |            71.684719 |   -71.684719 |     -8.96059 |                         0.015001 |                        0.003408 |                             3.387331 |              0.0 |                   0.0 |           0.0 |          412.0 |
    | 2000-08-01 23:00:00 |             90.9 |       2.3 |              1017.0 |              0.0 |                      0.0 |             0.0 |           16.4 |                 1.38 |                18.652661 |                      1.187604 |            16.955269 |    1000.044731 |   1.215856 |           0.2 |                   0.0 |             17.943516 |              245.140562 |       0.0 |           0.0 |                0.0 |                   0.0 |            72.396674 |   -72.396674 |    -9.049584 |                         0.032023 |                        0.005468 |                             3.390739 |              0.0 |                   0.0 |           0.0 |          436.0 |

hourly simulation, water
________________________

|evap_pet_ambav1| also calculates hourly water evaporation values, which show a clear
diurnal pattern not apparent in the generally aggregated water evaporation values of
|evap_morsim| in example :ref:`evap_morsim_hourly_simulation_water`:

.. integration-test::

    >>> test.inits.loggedwaterevaporation = 0.1
    >>> interception(False)
    >>> soil(False)
    >>> plant(False)
    >>> tree(False)
    >>> water(True)
    >>> cropheight(0.0)
    >>> test("evap_pet_ambav1_hourly_simulation_water",
    ...      axis1=(fluxes.waterevaporation, fluxes.dailywaterevaporation))
    |                date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | adjustedwindspeed10m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-01 00:00:00 |             95.1 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.9 |                  0.8 |                19.254836 |                      1.221127 |            18.311349 |     996.688651 |   1.210743 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |            66.097029 |   -66.097029 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061946 |              0.093252 |           0.3 |            nan |
    | 2000-08-01 01:00:00 |             94.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.6 |                  0.8 |                18.891521 |                      1.200918 |            17.928054 |     997.071946 |   1.212171 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |             66.49025 |    -66.49025 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061919 |              0.086506 |           0.3 |            nan |
    | 2000-08-01 02:00:00 |             95.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.4 |                  0.8 |                18.652661 |                      1.187604 |            17.887902 |     997.112098 |   1.213026 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |            66.746025 |   -66.746025 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062108 |              0.079751 |           0.3 |            nan |
    | 2000-08-01 03:00:00 |             96.7 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.3 |                  0.8 |                18.534226 |                      1.180995 |            17.922597 |     997.077403 |   1.213429 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |            66.871985 |   -66.871985 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062257 |               0.07299 |           0.3 |            nan |
    | 2000-08-01 04:00:00 |             97.2 |       0.8 |              1015.0 |              0.0 |                      0.4 |             1.9 |           16.0 |                  0.8 |                18.182867 |                      1.161352 |            17.673747 |     997.326253 |   1.214802 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |                  1.52 |            67.348507 |   -65.828507 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061003 |              0.066282 |           0.3 |            nan |
    | 2000-08-01 05:00:00 |             97.5 |       0.6 |              1015.0 |              0.0 |                      1.0 |            21.9 |           15.9 |                  0.6 |                18.067051 |                      1.154867 |            17.615375 |     997.384625 |   1.215249 |           0.2 |                   0.0 |           1254.958629 |                     0.0 |       0.0 |           0.0 |                0.0 |                 17.52 |            74.181953 |   -56.661953 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.052504 |              0.059928 |           0.0 |            nan |
    | 2000-08-01 06:00:00 |             97.7 |       0.9 |              1015.0 |              0.0 |                      1.0 |            57.3 |           16.0 |                  0.9 |                18.182867 |                      1.161352 |            17.764661 |     997.235339 |    1.21476 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |                 45.84 |            76.055111 |   -30.215111 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.027753 |              0.054605 |           0.0 |            nan |
    | 2000-08-01 07:00:00 |             97.4 |       0.9 |              1015.0 |              0.0 |                      1.0 |           109.3 |           16.6 |                  0.9 |                18.891521 |                      1.200918 |            18.400342 |     996.599658 |   1.211956 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |                 87.44 |            78.285119 |     9.154881 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.009224 |              0.050822 |           0.0 |            nan |
    | 2000-08-01 08:00:00 |             96.8 |       0.9 |              1016.0 |              0.0 |                      1.0 |           170.9 |           17.4 |                  0.9 |                19.873972 |                      1.255448 |            19.238005 |     996.761995 |   1.209438 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |                136.72 |            80.755926 |    55.964074 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.054474 |              0.048925 |           0.0 |            nan |
    | 2000-08-01 09:00:00 |             86.1 |       1.3 |              1016.0 |              0.2 |                      1.0 |           311.8 |           19.0 |                  1.3 |                21.973933 |                      1.370827 |            18.919557 |     997.080443 |   1.202958 |           0.2 |                   0.2 |            579.211675 |                     0.0 |       0.0 |           0.0 |                0.0 |                249.44 |            83.809146 |   165.630854 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.168458 |              0.051778 |           0.2 |            nan |
    | 2000-08-01 10:00:00 |             76.8 |       1.5 |              1016.0 |              0.5 |                      1.0 |           501.6 |           20.3 |                  1.5 |                23.820593 |                      1.471068 |            18.294216 |     997.705784 |    1.19791 |           0.2 |                   0.5 |            501.983452 |                     0.0 |       0.0 |           0.0 |                0.0 |                401.28 |            78.073919 |   323.206081 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.336062 |              0.061614 |           0.5 |            nan |
    | 2000-08-01 11:00:00 |             71.8 |       1.2 |              1016.0 |              0.7 |                      1.0 |           615.0 |           21.4 |                  1.2 |                25.487706 |                      1.560666 |            18.300173 |     997.699827 |   1.193433 |           0.2 |                   0.7 |            627.479315 |                     0.0 |       0.0 |           0.0 |                0.0 |                 492.0 |            65.478136 |   426.521864 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.448294 |              0.076126 |           0.7 |            nan |
    | 2000-08-01 12:00:00 |             67.5 |       1.3 |              1016.0 |              0.8 |                      1.0 |           626.5 |           21.3 |                  1.3 |                 25.33205 |                      1.552334 |            17.099134 |     998.900866 |   1.194376 |           0.2 |                   0.8 |            579.211675 |                     0.0 |       0.0 |           0.0 |                0.0 |                 501.2 |            55.930635 |   445.269365 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.469109 |              0.091506 |           0.8 |            nan |
    | 2000-08-01 13:00:00 |             66.1 |       1.5 |              1016.0 |              0.5 |                      1.0 |           496.1 |           21.8 |                  1.5 |                26.118719 |                       1.59437 |            17.264473 |     998.735527 |   1.192277 |           0.2 |                   0.5 |            501.983452 |                     0.0 |       0.0 |           0.0 |                0.0 |                396.88 |             74.71054 |    322.16946 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.347591 |              0.101822 |           0.5 |            nan |
    | 2000-08-01 14:00:00 |             63.4 |       1.9 |              1016.0 |              0.4 |                      1.0 |           419.5 |           22.9 |                  1.9 |                27.924898 |                      1.690242 |            17.704385 |     998.295615 |   1.187651 |           0.2 |                   0.4 |            396.302725 |                     0.0 |       0.0 |           0.0 |                0.0 |                 335.6 |            74.508507 |   261.091493 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.294294 |              0.109917 |           0.4 |            nan |
    | 2000-08-01 15:00:00 |             62.4 |       1.9 |              1016.0 |              0.5 |                      1.0 |           387.9 |           22.7 |                  1.9 |                27.588616 |                      1.672458 |            17.215297 |     998.784703 |   1.188672 |           0.2 |                   0.5 |            396.302725 |                     0.0 |       0.0 |           0.0 |                0.0 |                310.32 |            66.707316 |   243.612684 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.275569 |              0.117233 |           0.5 |            nan |
    | 2000-08-01 16:00:00 |             61.1 |       2.3 |              1016.0 |              0.5 |                      1.0 |           278.5 |           22.5 |                  2.3 |                27.255876 |                      1.654832 |             16.65334 |      999.34666 |   1.189726 |           0.2 |                   0.5 |            327.380512 |                     0.0 |       0.0 |           0.0 |                0.0 |                 222.8 |            61.019731 |   161.780269 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.19396 |              0.121148 |           0.5 |            nan |
    | 2000-08-01 17:00:00 |             62.1 |       2.4 |              1016.0 |              0.3 |                      1.0 |           137.1 |           21.9 |                  2.4 |                26.278588 |                      1.602891 |            16.319003 |     999.680997 |   1.192295 |           0.2 |                   0.3 |            313.739657 |                     0.0 |       0.0 |           0.0 |                0.0 |                109.68 |            65.664882 |    44.015118 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.070312 |              0.119911 |           0.3 |            nan |
    | 2000-08-01 18:00:00 |             67.0 |       2.5 |              1016.0 |              0.1 |                      1.0 |            51.1 |           21.4 |                  2.5 |                25.487706 |                      1.560666 |            17.076763 |     998.923237 |    1.19398 |           0.2 |                   0.1 |            301.190071 |                     0.0 |       0.0 |           0.0 |                0.0 |                 40.88 |            67.357383 |   -26.477383 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.005155 |              0.115529 |           0.1 |            nan |
    | 2000-08-01 19:00:00 |             74.5 |       2.5 |              1016.0 |              0.0 |                      1.0 |            13.6 |           20.7 |                  2.5 |                24.415439 |                      1.503132 |            18.189502 |     997.810498 |   1.196326 |           0.2 |                   0.0 |            301.190071 |                     0.0 |       0.0 |           0.0 |                0.0 |                 10.88 |            67.126066 |   -56.246066 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.040437 |              0.109678 |           0.0 |            nan |
    | 2000-08-01 20:00:00 |             81.2 |       2.2 |              1016.0 |              0.0 |                      0.2 |             0.2 |           19.4 |                  2.2 |                 22.52831 |                      1.401035 |            18.292988 |     997.707012 |   1.201595 |           0.2 |                   0.0 |            342.261444 |                     0.0 |       0.0 |           0.0 |                0.0 |                  0.16 |            68.418576 |   -68.258576 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.057376 |               0.10312 |           0.0 |            nan |
    | 2000-08-01 21:00:00 |             86.9 |       1.7 |              1016.0 |              0.0 |                      0.0 |             0.0 |           17.8 |                  1.7 |                20.381763 |                      1.283491 |            17.711752 |     998.288248 |   1.208466 |           0.2 |                   0.0 |            442.926575 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |            70.667062 |   -70.667062 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062884 |              0.096334 |           0.0 |            nan |
    | 2000-08-01 22:00:00 |             90.1 |       1.7 |              1017.0 |              0.0 |                      0.0 |             0.0 |           17.0 |                  1.7 |                19.377294 |                      1.227926 |            17.458941 |     999.541059 |   1.213114 |           0.2 |                   0.0 |            442.926575 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |            71.684719 |   -71.684719 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.064246 |               0.08949 |           0.0 |            nan |
    | 2000-08-01 23:00:00 |             90.9 |       2.3 |              1017.0 |              0.0 |                      0.0 |             0.0 |           16.4 |                  2.3 |                18.652661 |                      1.187604 |            16.955269 |    1000.044731 |   1.215856 |           0.2 |                   0.0 |            327.380512 |                     0.0 |       0.0 |           0.0 |                0.0 |                   0.0 |            72.396674 |   -72.396674 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.063192 |               0.08269 |           0.0 |            nan |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2B,
    evap_model.Main_PrecipModel_V1,
    evap_model.Main_PrecipModel_V2B,
    evap_model.Main_SnowCoverModel_V1,
    evap_model.Sub_ETModel,
    petinterfaces.PETModel_V2,
):
    """An AMBAV 1.0 version of HydPy-Evap for calculating potential
    evapotranspiration."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Determine_PotentialInterceptionEvaporation_V1,
        evap_model.Determine_PotentialSoilEvapotranspiration_V1,
        evap_model.Determine_PotentialWaterEvaporation_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialInterceptionEvaporation_V1,
        evap_model.Determine_PotentialSoilEvapotranspiration_V1,
        evap_model.Determine_PotentialWaterEvaporation_V1,
        evap_model.Get_PotentialWaterEvaporation_V1,
        evap_model.Get_PotentialInterceptionEvaporation_V1,
        evap_model.Get_PotentialSoilEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_AirTemperature_V1,
        evap_model.Return_AdjustedWindSpeed_V1,
        evap_model.Calc_AdjustedWindSpeed10m_V1,
        evap_model.Calc_SaturationVapourPressure_V1,
        evap_model.Calc_SaturationVapourPressureSlope_V1,
        evap_model.Calc_ActualVapourPressure_V1,
        evap_model.Calc_DryAirPressure_V1,
        evap_model.Calc_AirDensity_V1,
        evap_model.Calc_CurrentAlbedo_V2,
        evap_model.Calc_NetShortwaveRadiation_V2,
        evap_model.Update_CloudCoverage_V1,
        evap_model.Calc_AdjustedCloudCoverage_V1,
        evap_model.Calc_NetLongwaveRadiation_V2,
        evap_model.Calc_NetRadiation_V1,
        evap_model.Calc_AerodynamicResistance_V2,
        evap_model.Calc_DailyPrecipitation_V1,
        evap_model.Calc_DailyPotentialSoilEvapotranspiration_V1,
        evap_model.Update_SoilResistance_V1,
        evap_model.Calc_ActualSurfaceResistance_V2,
        evap_model.Calc_PotentialSoilEvapotranspiration_V1,
        evap_model.Return_Evaporation_PenmanMonteith_V2,
        evap_model.Calc_SnowCover_V1,
        evap_model.Calc_SoilHeatFlux_V4,
        evap_model.Calc_WaterEvaporation_V4,
        evap_model.Calc_AirTemperature_TempModel_V1,
        evap_model.Calc_AirTemperature_TempModel_V2,
        evap_model.Calc_SnowCover_SnowCoverModel_V1,
        evap_model.Calc_PotentialInterceptionEvaporation_V2,
        evap_model.Calc_Precipitation_PrecipModel_V1,
        evap_model.Calc_Precipitation_PrecipModel_V2,
        evap_model.Calc_Precipitation_V1,
        evap_model.Update_LoggedPrecipitation_V1,
        evap_model.Update_LoggedPotentialSoilEvapotranspiration_V1,
        evap_model.Update_LoggedWaterEvaporation_V1,
        evap_model.Calc_DailyWaterEvaporation_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
        stateinterfaces.SnowCoverModel_V1,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )
    snowcovermodel = modeltools.SubmodelProperty(stateinterfaces.SnowCoverModel_V1)


tester = Tester()
cythonizer = Cythonizer()
