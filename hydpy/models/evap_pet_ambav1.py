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

Additionally, |evap_pet_ambav1| requires radiation-related data (potential sunshine
duration, actual sunshine duration, and global radiation) that must be supplied by a
"real" submodel that complies with the |RadiationModel_V1| or the |RadiationModel_V4|
interface.

Integration tests
=================

.. how_to_understand_integration_tests::

The design of the following integration tests is similar to the one chosen for
|evap_morsim| to ease the comparison of both models.

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
>>> leafareaindex(5.0)
>>> cropheight(10.0)
>>> leafresistance(40.0)

The following parameters have no direct equivalents in |evap_morsim|:

>>> wetsoilresistance(100.0)
>>> soilresistanceincrease(1.0)
>>> wetnessthreshold(0.5)
>>> cloudtypefactor(0.2)
>>> nightcloudfactor(1.0)

We add submodels of type |meteo_temp_io|, |meteo_precip_io|, |meteo_psun_sun_glob_io|,
and |dummy_snowcover| that supply additional information on the catchment's state
instead of complicating the comparisons by introducing complex main or submodels:

>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     hruarea(1.0)
...     temperatureaddend(0.0)
>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     hruarea(1.0)
...     precipitationfactor(1.0)
>>> with model.add_radiationmodel_v4("meteo_psun_sun_glob_io"):
...     pass
>>> with model.add_snowcovermodel_v1("dummy_snowcover"):
...     pass

Now, we can initialise an |IntegrationTest| object:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

The following meteorological input and snow cover data also agree with the first
|evap_morsim| examples:

>>> inputs.windspeed.series = 2.0
>>> inputs.relativehumidity.series = 80.0
>>> inputs.atmosphericpressure.series = 1000.0
>>> model.tempmodel.sequences.inputs.temperature.series = 15.0
>>> model.radiationmodel.sequences.inputs.sunshineduration.series = 6.0
>>> model.radiationmodel.sequences.inputs.possiblesunshineduration.series = 16.0
>>> model.radiationmodel.sequences.inputs.globalradiation.series = 190.0
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

.. _evap_pet_ambav1_non_tree_vegetation_daily:

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
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | adjustedwindspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             12.381026 |               55.393952 |       0.0 |           0.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         8.211488 |                        3.073332 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          124.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             12.381026 |                57.24078 |       0.0 |          10.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         8.211488 |                        3.010527 |                             3.073332 |              0.0 |                   0.0 |         0.375 |          148.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             12.381026 |               52.869385 |       0.0 |           0.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         8.211488 |                        3.163548 |                             3.010527 |              0.0 |                   0.0 |         0.375 |          100.0 |

.. _evap_pet_ambav1_tree_like_vegetation_daily:

tree-like vegetation
____________________

All effects of enabling the flag for tree-like vegetation (like in the
:ref:`evap_morsim_deciduous_trees` example of |evap_morsim|) are due to a wind speed
reduction that tries to adjust wind speed measurements over short grass to forest
sites:

.. integration-test::

    >>> tree(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | adjustedwindspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  1.2 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |               55.393952 |       0.0 |           0.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                        2.768363 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          124.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  1.2 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |                57.24078 |       0.0 |          10.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                        2.722902 |                             2.768363 |              0.0 |                   0.0 |         0.375 |          148.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  1.2 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |               52.869385 |       0.0 |           0.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                         2.83302 |                             2.722902 |              0.0 |                   0.0 |         0.375 |          100.0 |

.. _evap_pet_ambav1_water_area_daily:

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
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | adjustedwindspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |           0.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  1.0 |         1.890672 |              1.890672 |         0.375 |            nan |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |          10.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         1.890672 |              1.890672 |         0.375 |            nan |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |           0.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         1.890672 |              1.890672 |         0.375 |            nan |

.. _evap_pet_ambav1_snow_daily:

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
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | adjustedwindspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  1.2 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |             20.635044 |               52.869385 |       0.0 |          10.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         5.545339 |                         2.83302 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          100.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  1.2 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.5 |                 0.375 |             20.635044 |               52.869385 |       0.5 |          10.0 |               10.0 |           190.0 |                  95.0 |            71.952081 |    23.047919 |     1.728594 |                         4.467744 |                        2.282495 |                              2.83302 |              0.0 |                   0.0 |         0.375 |          100.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                  1.2 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.8 |                 0.375 |             20.635044 |               52.869385 |       1.0 |          10.0 |               10.0 |           190.0 |                  38.0 |            67.962081 |   -29.962081 |    -2.247156 |                         3.390149 |                         1.73197 |                             2.282495 |              0.0 |                   0.0 |         0.375 |          100.0 |

.. _evap_pet_ambav1_hourly_simulation_land:

hourly simulation, land
_______________________

The following examples deal with an hourly simulation step:

>>> pub.timegrids = "2000-08-03", "2000-08-04", "1h"

We need to restore the values of all time-dependent parameters:

>>> for parameter in model.parameters.fixed:
...     parameter.restore()

As in the :ref:`evap_morsim_hourly_simulation_land` example, we switch to using
|meteo_v003| instead of |meteo_psun_sun_glob_io| to gain the radiation-related data:

>>> with model.add_radiationmodel_v1("meteo_v003"):
...     latitude(54.1)
...     longitude(9.7)
...     angstromconstant(0.25)
...     angstromfactor(0.5)
...     angstromalternative(0.15)
>>> test = IntegrationTest(element)

The following meteorological input data also agree with the
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
>>> model.radiationmodel.sequences.inputs.sunshineduration.series = (
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.5, 0.7, 0.8, 0.5, 0.4, 0.5,
...     0.5, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0)

In contrast to |evap_morsim|, |evap_pet_ambav1| does not require "daily" averages or
sums of meteorological input data but calculates, e.g., hourly water area evaporation
values and aggregates them to daily values later.  But it needs to remember the last
determined cloud coverage degree (which is only estimateable at daytime) and other
factors related to the topmost soil layer's wetness calculations:

>>> test.inits = (
...     (states.soilresistance, 100.0),
...     (states.cloudcoverage, 0.3),
...     (logs.loggedprecipitation, 0.0),
...     (logs.loggedwaterevaporation, 0.0),
...     (logs.loggedpotentialsoilevapotranspiration, 0.0),
...     (model.radiationmodel.sequences.logs.loggedsunshineduration,
...      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.1, 0.2, 0.1, 0.2, 0.2, 0.3, 0.0,
...       0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
...     (model.radiationmodel.sequences.logs.loggedunadjustedglobalradiation,
...      [0.0, 0.0, 0.0, 0.0, 0.0, 27.777778, 55.555556, 138.888889, 222.222222,
...       305.555556, 333.333333, 388.888889, 527.777778, 444.444444, 250.0,
...       222.222222, 166.666667, 111.111111, 55.555556, 27.777778, 0.0, 0.0, 0.0,
...       0.0]))

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
    |                date | relativehumidity | windspeed | atmosphericpressure | airtemperature | adjustedwindspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-03 00:00:00 |             95.1 |       0.8 |              1015.0 |           16.9 |                 0.48 |              0.0 |                      0.0 |                19.254836 |                      1.221127 |            18.311349 |     996.688651 |   1.210743 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.097029 |   -66.097029 |    -8.262129 |                        -0.037693 |                       -0.023944 |                                  0.0 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 01:00:00 |             94.9 |       0.8 |              1015.0 |           16.6 |                 0.48 |              0.0 |                      0.0 |                18.891521 |                      1.200918 |            17.928054 |     997.071946 |   1.212171 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |             66.49025 |    -66.49025 |    -8.311281 |                        -0.037115 |                       -0.023484 |                            -0.023944 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 02:00:00 |             95.9 |       0.8 |              1015.0 |           16.4 |                 0.48 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            17.887902 |     997.112098 |   1.213026 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.746025 |   -66.746025 |    -8.343253 |                        -0.040693 |                       -0.025679 |                            -0.047427 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 03:00:00 |             96.7 |       0.8 |              1015.0 |           16.3 |                 0.48 |              0.0 |                      0.0 |                18.534226 |                      1.180995 |            17.922597 |     997.077403 |   1.213429 |           0.2 |                   0.3 |             51.587609 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.871985 |   -66.871985 |    -8.358998 |                        -0.043513 |                       -0.027423 |                            -0.073107 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 04:00:00 |             97.2 |       0.8 |              1015.0 |           16.0 |                 0.48 |              0.0 |                 0.429734 |                18.182867 |                      1.161352 |            17.673747 |     997.326253 |   1.214802 |           0.2 |                   0.3 |             51.587609 |               61.046495 |       0.0 |           0.0 |                0.0 |        1.943686 |              1.554949 |            67.350953 |   -65.796004 |    -6.103894 |                        -0.046101 |                       -0.032312 |                            -0.100529 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 05:00:00 |             97.5 |       0.6 |              1015.0 |           15.9 |                 0.36 |              0.0 |                      1.0 |                18.067051 |                      1.154867 |            17.615375 |     997.384625 |   1.215249 |           0.2 |                   0.0 |             68.783479 |               44.486064 |       0.0 |           0.0 |                0.0 |       21.932441 |             17.545953 |             74.18377 |   -56.637817 |    -2.831891 |                        -0.043716 |                       -0.035425 |                            -0.132841 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 06:00:00 |             97.7 |       0.9 |              1015.0 |           16.0 |                 0.54 |              0.0 |                      1.0 |                18.182867 |                      1.161352 |            17.764661 |     997.235339 |    1.21476 |           0.2 |                   0.0 |             45.855653 |               44.486064 |       0.0 |           0.0 |                0.0 |       57.256187 |             45.804949 |            76.052657 |   -30.247708 |    -1.512385 |                        -0.017899 |                        -0.01326 |                            -0.168266 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 07:00:00 |             97.4 |       0.9 |              1015.0 |           16.6 |                 0.54 |              0.0 |                      1.0 |                18.891521 |                      1.200918 |            18.400342 |     996.599658 |   1.211956 |           0.2 |                   0.0 |             45.855653 |               44.486064 |       0.0 |           0.0 |                0.0 |      109.332844 |             87.466275 |            78.286958 |     9.179317 |     0.458966 |                         0.018527 |                        0.013802 |                            -0.181526 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 08:00:00 |             96.8 |       0.9 |              1016.0 |           17.4 |                 0.54 |              0.0 |                      1.0 |                19.873972 |                      1.255448 |            19.238005 |     996.761995 |   1.209438 |           0.2 |                   0.0 |             45.855653 |               44.486064 |       0.0 |           0.0 |                0.0 |      170.949152 |            136.759322 |            80.758678 |    56.000644 |     2.800032 |                         0.064012 |                        0.048035 |                            -0.167725 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 09:00:00 |             86.1 |       1.3 |              1016.0 |           19.0 |                 0.78 |              0.2 |                      1.0 |                21.973933 |                      1.370827 |            18.919557 |     997.080443 |   1.202958 |           0.2 |                   0.2 |             31.746221 |               44.486064 |       0.0 |           0.0 |                0.0 |      311.762624 |              249.4101 |            83.807053 |   165.603046 |     8.280152 |                         0.239582 |                        0.164879 |                            -0.119689 |              0.0 |                   0.0 |           0.2 |          100.0 |
    | 2000-08-03 10:00:00 |             76.8 |       1.5 |              1016.0 |           20.3 |                  0.9 |              0.5 |                      1.0 |                23.820593 |                      1.471068 |            18.294216 |     997.705784 |    1.19791 |           0.2 |                   0.5 |             27.513392 |               45.139282 |       0.0 |           0.0 |                0.0 |      501.583299 |            401.266639 |            78.072984 |   323.193655 |    16.159683 |                         0.476874 |                        0.316766 |                              0.04519 |              0.0 |                   0.0 |           0.5 |          124.0 |
    | 2000-08-03 11:00:00 |             71.8 |       1.2 |              1016.0 |           21.4 |                 0.72 |              0.7 |                      1.0 |                25.487706 |                      1.560666 |            18.300173 |     997.699827 |   1.193433 |           0.2 |                   0.7 |              34.39174 |               45.591614 |       0.0 |           0.0 |                0.0 |      615.018727 |            492.014981 |            65.479184 |   426.535797 |     21.32679 |                         0.582679 |                        0.418623 |                             0.361956 |              0.0 |                   0.0 |           0.7 |          148.0 |
    | 2000-08-03 12:00:00 |             67.5 |       1.3 |              1016.0 |           21.3 |                 0.78 |              0.8 |                      1.0 |                 25.33205 |                      1.552334 |            17.099134 |     998.900866 |   1.194376 |           0.2 |                   0.8 |             31.746221 |               45.923379 |       0.0 |           0.0 |                0.0 |      626.544326 |            501.235461 |            55.933117 |   445.302344 |    22.265117 |                         0.641129 |                        0.448576 |                             0.780579 |              0.0 |                   0.0 |           0.8 |          172.0 |
    | 2000-08-03 13:00:00 |             66.1 |       1.5 |              1016.0 |           21.8 |                  0.9 |              0.5 |                      1.0 |                26.118719 |                       1.59437 |            17.264473 |     998.735527 |   1.192277 |           0.2 |                   0.5 |             27.513392 |               46.177112 |       0.0 |           0.0 |                0.0 |      496.133417 |            396.906734 |            74.712412 |   322.194322 |    16.109716 |                         0.567816 |                        0.381411 |                             1.229155 |              0.0 |                   0.0 |           0.5 |          196.0 |
    | 2000-08-03 14:00:00 |             63.4 |       1.9 |              1016.0 |           22.9 |                 1.14 |              0.4 |                      1.0 |                27.924898 |                      1.690242 |            17.704385 |     998.295615 |   1.187651 |           0.2 |                   0.4 |             21.721099 |               46.377447 |       0.0 |           0.0 |                0.0 |      419.520994 |            335.616795 |            74.509683 |   261.107112 |    13.055356 |                         0.611473 |                        0.383052 |                             1.610566 |              0.0 |                   0.0 |           0.4 |          220.0 |
    | 2000-08-03 15:00:00 |             62.4 |       1.9 |              1016.0 |           22.7 |                 1.14 |              0.5 |                      1.0 |                27.588616 |                      1.672458 |            17.215297 |     998.784703 |   1.188672 |           0.2 |                   0.5 |             21.721099 |               46.539635 |       0.0 |           0.0 |                0.0 |      387.887354 |            310.309883 |            66.706608 |   243.603275 |    12.180164 |                         0.601487 |                        0.375231 |                             1.993618 |              0.0 |                   0.0 |           0.5 |          244.0 |
    | 2000-08-03 16:00:00 |             61.1 |       2.3 |              1016.0 |           22.5 |                 1.38 |              0.5 |                      1.0 |                27.255876 |                      1.654832 |             16.65334 |      999.34666 |   1.189726 |           0.2 |                   0.5 |             17.943516 |               46.673625 |       0.0 |           0.0 |                0.0 |      278.496873 |            222.797499 |            61.019556 |   161.777943 |     8.088897 |                         0.608152 |                        0.349994 |                              2.36885 |              0.0 |                   0.0 |           0.5 |          268.0 |
    | 2000-08-03 17:00:00 |             62.1 |       2.4 |              1016.0 |           21.9 |                 1.44 |              0.3 |                      1.0 |                26.278588 |                      1.602891 |            16.319003 |     999.680997 |   1.192295 |           0.2 |                   0.3 |              17.19587 |               46.786182 |       0.0 |           0.0 |                0.0 |      137.138608 |            109.710886 |            65.667044 |    44.043842 |     2.202192 |                           0.4928 |                        0.275418 |                             2.718844 |              0.0 |                   0.0 |           0.3 |          292.0 |
    | 2000-08-03 18:00:00 |             67.0 |       2.5 |              1016.0 |           21.4 |                  1.5 |              0.1 |                      1.0 |                25.487706 |                      1.560666 |            17.076763 |     998.923237 |    1.19398 |           0.2 |                   0.1 |             16.508035 |               46.882068 |       0.0 |           0.0 |                0.0 |       51.080715 |             40.864572 |            67.356303 |   -26.491731 |    -1.324587 |                         0.377498 |                        0.205212 |                             2.994262 |              0.0 |                   0.0 |           0.1 |          316.0 |
    | 2000-08-03 19:00:00 |             74.5 |       2.5 |              1016.0 |           20.7 |                  1.5 |              0.0 |                      1.0 |                24.415439 |                      1.503132 |            18.189502 |     997.810498 |   1.196326 |           0.2 |                   0.0 |             16.508035 |               46.964732 |       0.0 |           0.0 |                0.0 |       13.632816 |             10.906253 |            67.127904 |   -56.221651 |    -2.811083 |                         0.252792 |                        0.135658 |                             3.199474 |              0.0 |                   0.0 |           0.0 |          340.0 |
    | 2000-08-03 20:00:00 |             81.2 |       2.2 |              1016.0 |           19.4 |                 1.32 |              0.0 |                   0.1364 |                 22.52831 |                      1.401035 |            18.292988 |     997.707012 |   1.201595 |           0.2 |                   0.0 |             18.759131 |              146.745137 |       0.0 |           0.0 |                0.0 |        0.185943 |              0.148755 |            68.417789 |   -68.269035 |    -7.835236 |                         0.133664 |                        0.038276 |                             3.335132 |              0.0 |                   0.0 |           0.0 |          364.0 |
    | 2000-08-03 21:00:00 |             86.9 |       1.7 |              1016.0 |           17.8 |                 1.02 |              0.0 |                      0.0 |                20.381763 |                      1.283491 |            17.711752 |     998.288248 |   1.208466 |           0.2 |                   0.0 |             24.276522 |              229.198312 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            70.667062 |   -70.667062 |    -8.833383 |                         0.040887 |                        0.009758 |                             3.373408 |              0.0 |                   0.0 |           0.0 |          388.0 |
    | 2000-08-03 22:00:00 |             90.1 |       1.7 |              1017.0 |           17.0 |                 1.02 |              0.0 |                      0.0 |                19.377294 |                      1.227926 |            17.458941 |     999.541059 |   1.213114 |           0.2 |                   0.0 |             24.276522 |              237.366255 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            71.684719 |   -71.684719 |     -8.96059 |                         0.015001 |                        0.003408 |                             3.383166 |              0.0 |                   0.0 |           0.0 |          412.0 |
    | 2000-08-03 23:00:00 |             90.9 |       2.3 |              1017.0 |           16.4 |                 1.38 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            16.955269 |    1000.044731 |   1.215856 |           0.2 |                   0.0 |             17.943516 |              245.140562 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            72.396674 |   -72.396674 |    -9.049584 |                         0.032023 |                        0.005468 |                             3.386574 |              0.0 |                   0.0 |           0.0 |          436.0 |

.. _evap_pet_ambav1_hourly_simulation_water:

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
    |                date | relativehumidity | windspeed | atmosphericpressure | airtemperature | adjustedwindspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-03 00:00:00 |             95.1 |       0.8 |              1015.0 |           16.9 |                  0.8 |              0.0 |                      0.0 |                19.254836 |                      1.221127 |            18.311349 |     996.688651 |   1.210743 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.097029 |   -66.097029 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061946 |              0.093252 |           0.3 |            nan |
    | 2000-08-03 01:00:00 |             94.9 |       0.8 |              1015.0 |           16.6 |                  0.8 |              0.0 |                      0.0 |                18.891521 |                      1.200918 |            17.928054 |     997.071946 |   1.212171 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |             66.49025 |    -66.49025 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061919 |              0.086506 |           0.3 |            nan |
    | 2000-08-03 02:00:00 |             95.9 |       0.8 |              1015.0 |           16.4 |                  0.8 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            17.887902 |     997.112098 |   1.213026 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.746025 |   -66.746025 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062108 |              0.079751 |           0.3 |            nan |
    | 2000-08-03 03:00:00 |             96.7 |       0.8 |              1015.0 |           16.3 |                  0.8 |              0.0 |                      0.0 |                18.534226 |                      1.180995 |            17.922597 |     997.077403 |   1.213429 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.871985 |   -66.871985 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062257 |               0.07299 |           0.3 |            nan |
    | 2000-08-03 04:00:00 |             97.2 |       0.8 |              1015.0 |           16.0 |                  0.8 |              0.0 |                 0.429734 |                18.182867 |                      1.161352 |            17.673747 |     997.326253 |   1.214802 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |        1.943686 |              1.554949 |            67.350953 |   -65.796004 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.060973 |              0.066283 |           0.3 |            nan |
    | 2000-08-03 05:00:00 |             97.5 |       0.6 |              1015.0 |           15.9 |                  0.6 |              0.0 |                      1.0 |                18.067051 |                      1.154867 |            17.615375 |     997.384625 |   1.215249 |           0.2 |                   0.0 |           1254.958629 |                     0.0 |       0.0 |           0.0 |                0.0 |       21.932441 |             17.545953 |             74.18377 |   -56.637817 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.052482 |               0.05993 |           0.0 |            nan |
    | 2000-08-03 06:00:00 |             97.7 |       0.9 |              1015.0 |           16.0 |                  0.9 |              0.0 |                      1.0 |                18.182867 |                      1.161352 |            17.764661 |     997.235339 |    1.21476 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |       57.256187 |             45.804949 |            76.052657 |   -30.247708 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.027784 |              0.054606 |           0.0 |            nan |
    | 2000-08-03 07:00:00 |             97.4 |       0.9 |              1015.0 |           16.6 |                  0.9 |              0.0 |                      1.0 |                18.891521 |                      1.200918 |            18.400342 |     996.599658 |   1.211956 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |      109.332844 |             87.466275 |            78.286958 |     9.179317 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.009247 |              0.050824 |           0.0 |            nan |
    | 2000-08-03 08:00:00 |             96.8 |       0.9 |              1016.0 |           17.4 |                  0.9 |              0.0 |                      1.0 |                19.873972 |                      1.255448 |            19.238005 |     996.761995 |   1.209438 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |      170.949152 |            136.759322 |            80.758678 |    56.000644 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.054509 |              0.048929 |           0.0 |            nan |
    | 2000-08-03 09:00:00 |             86.1 |       1.3 |              1016.0 |           19.0 |                  1.3 |              0.2 |                      1.0 |                21.973933 |                      1.370827 |            18.919557 |     997.080443 |   1.202958 |           0.2 |                   0.2 |            579.211675 |                     0.0 |       0.0 |           0.0 |                0.0 |      311.762624 |              249.4101 |            83.807053 |   165.603046 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.168431 |               0.05178 |           0.2 |            nan |
    | 2000-08-03 10:00:00 |             76.8 |       1.5 |              1016.0 |           20.3 |                  1.5 |              0.5 |                      1.0 |                23.820593 |                      1.471068 |            18.294216 |     997.705784 |    1.19791 |           0.2 |                   0.5 |            501.983452 |                     0.0 |       0.0 |           0.0 |                0.0 |      501.583299 |            401.266639 |            78.072984 |   323.193655 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.33605 |              0.061615 |           0.5 |            nan |
    | 2000-08-03 11:00:00 |             71.8 |       1.2 |              1016.0 |           21.4 |                  1.2 |              0.7 |                      1.0 |                25.487706 |                      1.560666 |            18.300173 |     997.699827 |   1.193433 |           0.2 |                   0.7 |            627.479315 |                     0.0 |       0.0 |           0.0 |                0.0 |      615.018727 |            492.014981 |            65.479184 |   426.535797 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.448309 |              0.076128 |           0.7 |            nan |
    | 2000-08-03 12:00:00 |             67.5 |       1.3 |              1016.0 |           21.3 |                  1.3 |              0.8 |                      1.0 |                 25.33205 |                      1.552334 |            17.099134 |     998.900866 |   1.194376 |           0.2 |                   0.8 |            579.211675 |                     0.0 |       0.0 |           0.0 |                0.0 |      626.544326 |            501.235461 |            55.933117 |   445.302344 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.469143 |              0.091509 |           0.8 |            nan |
    | 2000-08-03 13:00:00 |             66.1 |       1.5 |              1016.0 |           21.8 |                  1.5 |              0.5 |                      1.0 |                26.118719 |                       1.59437 |            17.264473 |     998.735527 |   1.192277 |           0.2 |                   0.5 |            501.983452 |                     0.0 |       0.0 |           0.0 |                0.0 |      496.133417 |            396.906734 |            74.712412 |   322.194322 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.347617 |              0.101827 |           0.5 |            nan |
    | 2000-08-03 14:00:00 |             63.4 |       1.9 |              1016.0 |           22.9 |                  1.9 |              0.4 |                      1.0 |                27.924898 |                      1.690242 |            17.704385 |     998.295615 |   1.187651 |           0.2 |                   0.4 |            396.302725 |                     0.0 |       0.0 |           0.0 |                0.0 |      419.520994 |            335.616795 |            74.509683 |   261.107112 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.29431 |              0.109923 |           0.4 |            nan |
    | 2000-08-03 15:00:00 |             62.4 |       1.9 |              1016.0 |           22.7 |                  1.9 |              0.5 |                      1.0 |                27.588616 |                      1.672458 |            17.215297 |     998.784703 |   1.188672 |           0.2 |                   0.5 |            396.302725 |                     0.0 |       0.0 |           0.0 |                0.0 |      387.887354 |            310.309883 |            66.706608 |   243.603275 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.27556 |              0.117238 |           0.5 |            nan |
    | 2000-08-03 16:00:00 |             61.1 |       2.3 |              1016.0 |           22.5 |                  2.3 |              0.5 |                      1.0 |                27.255876 |                      1.654832 |             16.65334 |      999.34666 |   1.189726 |           0.2 |                   0.5 |            327.380512 |                     0.0 |       0.0 |           0.0 |                0.0 |      278.496873 |            222.797499 |            61.019556 |   161.777943 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.193958 |              0.121153 |           0.5 |            nan |
    | 2000-08-03 17:00:00 |             62.1 |       2.4 |              1016.0 |           21.9 |                  2.4 |              0.3 |                      1.0 |                26.278588 |                      1.602891 |            16.319003 |     999.680997 |   1.192295 |           0.2 |                   0.3 |            313.739657 |                     0.0 |       0.0 |           0.0 |                0.0 |      137.138608 |            109.710886 |            65.667044 |    44.043842 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.070342 |              0.119917 |           0.3 |            nan |
    | 2000-08-03 18:00:00 |             67.0 |       2.5 |              1016.0 |           21.4 |                  2.5 |              0.1 |                      1.0 |                25.487706 |                      1.560666 |            17.076763 |     998.923237 |    1.19398 |           0.2 |                   0.1 |            301.190071 |                     0.0 |       0.0 |           0.0 |                0.0 |       51.080715 |             40.864572 |            67.356303 |   -26.491731 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         -0.00517 |              0.115535 |           0.1 |            nan |
    | 2000-08-03 19:00:00 |             74.5 |       2.5 |              1016.0 |           20.7 |                  2.5 |              0.0 |                      1.0 |                24.415439 |                      1.503132 |            18.189502 |     997.810498 |   1.196326 |           0.2 |                   0.0 |            301.190071 |                     0.0 |       0.0 |           0.0 |                0.0 |       13.632816 |             10.906253 |            67.127904 |   -56.221651 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.040413 |              0.109684 |           0.0 |            nan |
    | 2000-08-03 20:00:00 |             81.2 |       2.2 |              1016.0 |           19.4 |                  2.2 |              0.0 |                   0.1364 |                 22.52831 |                      1.401035 |            18.292988 |     997.707012 |   1.201595 |           0.2 |                   0.0 |            342.261444 |                     0.0 |       0.0 |           0.0 |                0.0 |        0.185943 |              0.148755 |            68.417789 |   -68.269035 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.057386 |              0.103127 |           0.0 |            nan |
    | 2000-08-03 21:00:00 |             86.9 |       1.7 |              1016.0 |           17.8 |                  1.7 |              0.0 |                      0.0 |                20.381763 |                      1.283491 |            17.711752 |     998.288248 |   1.208466 |           0.2 |                   0.0 |            442.926575 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            70.667062 |   -70.667062 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062884 |               0.09634 |           0.0 |            nan |
    | 2000-08-03 22:00:00 |             90.1 |       1.7 |              1017.0 |           17.0 |                  1.7 |              0.0 |                      0.0 |                19.377294 |                      1.227926 |            17.458941 |     999.541059 |   1.213114 |           0.2 |                   0.0 |            442.926575 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            71.684719 |   -71.684719 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.064246 |              0.089496 |           0.0 |            nan |
    | 2000-08-03 23:00:00 |             90.9 |       2.3 |              1017.0 |           16.4 |                  2.3 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            16.955269 |    1000.044731 |   1.215856 |           0.2 |                   0.0 |            327.380512 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            72.396674 |   -72.396674 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.063192 |              0.082697 |           0.0 |            nan |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import radiationinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2B,
    evap_model.Main_PrecipModel_V1,
    evap_model.Main_PrecipModel_V2B,
    evap_model.Main_RadiationModel_V1,
    evap_model.Main_RadiationModel_V4,
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
        evap_model.Process_RadiationModel_V1,
        evap_model.Calc_PossibleSunshineDuration_V1,
        evap_model.Calc_SunshineDuration_V1,
        evap_model.Calc_GlobalRadiation_V1,
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
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V4,
        stateinterfaces.SnowCoverModel_V1,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )
    radiationmodel = modeltools.SubmodelProperty(
        radiationinterfaces.RadiationModel_V1, radiationinterfaces.RadiationModel_V4
    )
    snowcovermodel = modeltools.SubmodelProperty(stateinterfaces.SnowCoverModel_V1)


tester = Tester()
cythonizer = Cythonizer()
