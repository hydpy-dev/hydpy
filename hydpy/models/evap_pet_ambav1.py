# pylint: disable=line-too-long, unused-wildcard-import
"""
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
|evap_aet_morsim| to ease the comparison of both models.

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

The following parameter settings are comparable to the ones selected for
|evap_aet_morsim|:

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

The following parameters have no direct equivalents in |evap_aet_morsim|:

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
|evap_aet_morsim| examples:

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

In contrast to |evap_aet_morsim|, |evap_pet_ambav1| even requires logged values when
applied on daily timesteps to keep track of the temporal persistency of the topmost
soil layer's wetness:

>>> test.inits = ((states.soilresistance, 100.0),
...               (logs.loggedprecipitation, [0.0]),
...               (logs.loggedpotentialsoilevapotranspiration, [1.0]))

.. _evap_pet_ambav1_vegetation_daily:

vegetation
__________

The following configuration corresponds to the
:ref:`evap_aet_morsim_non_tree_vegetation`, :ref:`evap_aet_morsim_deciduous_trees`,
and :ref:`evap_aet_morsim_conifers` examples of |evap_aet_morsim| because
|evap_pet_ambav1| does not handle different kinds of vegetation distinctly:

>>> interception(True)
>>> soil(True)
>>> plant(True)
>>> water(False)

In the |evap_aet_morsim| examples, the resulting soil evapotranspiration values differ
due to different amounts of intercepted water.  In contrast, |evap_pet_ambav1|
calculates only potential values and thus does not consider storage contents.  The
differences between the individual days stem from the changing topmost soil layer's
wetness.  In this context, note that the precipitation event of the second day only
affects the results of the third day and later:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |                  47.0 |               55.393952 |       0.0 |           0.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         3.301949 |                        2.292368 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          124.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |                  47.0 |                57.24078 |       0.0 |          10.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         3.301949 |                        2.269236 |                             2.292368 |              0.0 |                   0.0 |         0.375 |          148.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |                  47.0 |               52.869385 |       0.0 |           0.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         3.301949 |                        2.324763 |                             2.269236 |              0.0 |                   0.0 |         0.375 |          100.0 |

.. _evap_pet_ambav1_water_area_daily:

water area
__________

Switching from vegetated soil to an open water area requires setting the crop height to
zero:

>>> interception(False)
>>> soil(False)
>>> plant(False)
>>> water(True)
>>> cropheight(0.0)

While |evap_aet_morsim| estimates an evaporation rate of 3.2 mm/day in the
:ref:`evap_water_area` example, |evap_pet_ambav1| estimates only 1.9 mm/day:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |           0.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  1.0 |         1.890672 |              1.890672 |         0.375 |            nan |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |          10.0 |                0.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         1.890672 |              1.890672 |         0.375 |            nan |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |            376.487589 |                     0.0 |       0.0 |           0.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         1.890672 |              1.890672 |         0.375 |            nan |

.. _evap_pet_ambav1_snow_daily:

snow
____

Now, we demonstrate the effect of snow on potential evapotranspiration from land areas
by setting different snow cover degrees:

>>> interception(True)
>>> soil(True)
>>> plant(True)
>>> water(False)
>>> cropheight(10.0)
>>> model.snowcovermodel.sequences.inputs.snowcover.series = [0.0], [0.5], [1.0]

We set all precipitation values to 10 mm to focus only on the influence of the snow
cover:

>>> model.precipmodel.sequences.inputs.precipitation.series = 10.0
>>> test.inits.loggedprecipitation = 10.0

In contrast to |evap_aet_morsim|, as discussed in the
:ref:`evap_aet_morsim_snow_on_non_tree_vegetation` example, |evap_pet_ambav1| never
suppresses evapotranspiration completely but adjusts the current albedo to the given
snow-specific values, which are usually larger than those of the leaf and soil surfaces
and so usually reduces evapotranspiration:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.2 |                 0.375 |                  47.0 |               52.869385 |       0.0 |          10.0 |               10.0 |           190.0 |                 152.0 |            75.942081 |    76.057919 |     5.704344 |                         3.301949 |                        2.324763 |                                  1.0 |              0.0 |                   0.0 |         0.375 |          100.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.5 |                 0.375 |                  47.0 |               52.869385 |       0.5 |          10.0 |               10.0 |           190.0 |                  95.0 |            71.952081 |    23.047919 |     1.728594 |                         2.224354 |                        1.566074 |                             2.324763 |              0.0 |                   0.0 |         0.375 |          100.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |          2.0 |              6.0 |                     16.0 |                17.053462 |                      1.097868 |             13.64277 |      986.35723 |   1.202725 |           0.8 |                 0.375 |                  47.0 |               52.869385 |       1.0 |          10.0 |               10.0 |           190.0 |                  38.0 |            67.962081 |   -29.962081 |    -2.247156 |                         1.146759 |                        0.807385 |                             1.566074 |              0.0 |                   0.0 |         0.375 |          100.0 |

.. _evap_pet_ambav1_hourly_simulation_land:

hourly simulation, land
_______________________

The following examples deal with an hourly simulation step:

>>> pub.timegrids = "2000-08-03", "2000-08-04", "1h"

We need to restore the values of all time-dependent parameters:

>>> for parameter in model.parameters.fixed:
...     parameter.restore()

As in the :ref:`evap_aet_morsim_hourly_simulation_land` example, we switch to using
|meteo_glob_morsim| instead of |meteo_psun_sun_glob_io| to gain the radiation-related
data:

>>> with model.add_radiationmodel_v1("meteo_glob_morsim"):
...     latitude(54.1)
...     longitude(9.7)
...     angstromconstant(0.25)
...     angstromfactor(0.5)
...     angstromalternative(0.15)
>>> test = IntegrationTest(element)

The following meteorological input data also agree with the
:ref:`evap_aet_morsim_hourly_simulation_land` example of |evap_aet_morsim|:

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

In contrast to |evap_aet_morsim|, |evap_pet_ambav1| does not require "daily" averages
or sums of meteorological input data but calculates, e.g., hourly water area
evaporation values and aggregates them to daily values later.  But it needs to remember
the last determined cloud coverage degree (which is only estimateable at daytime) and
other factors related to the topmost soil layer's wetness calculations:

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

Considering the :ref:`evap_aet_morsim_hourly_simulation_land` example,
|evap_pet_ambav1| estimates higher potential interception evaporation rates and
potential soil evapotranspiration rates that are (as to be expected) higher but roughly
comparable to the actual soil evapotranspiration rates of |evap_aet_morsim|:

.. integration-test::

    >>> test("evap_pet_ambav1_hourly_simulation_land",
    ...      axis1=(fluxes.potentialinterceptionevaporation,
    ...             fluxes.potentialsoilevapotranspiration))
    |                date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-03 00:00:00 |             95.1 |       0.8 |              1015.0 |           16.9 |          0.8 |              0.0 |                      0.0 |                19.254836 |                      1.221127 |            18.311349 |     996.688651 |   1.210743 |           0.2 |                   0.3 |                 117.5 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.097029 |   -66.097029 |    -8.262129 |                         -0.04742 |                       -0.037873 |                                  0.0 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 01:00:00 |             94.9 |       0.8 |              1015.0 |           16.6 |          0.8 |              0.0 |                      0.0 |                18.891521 |                      1.200918 |            17.928054 |     997.071946 |   1.212171 |           0.2 |                   0.3 |                 117.5 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |             66.49025 |    -66.49025 |    -8.311281 |                        -0.047169 |                        -0.03759 |                            -0.037873 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 02:00:00 |             95.9 |       0.8 |              1015.0 |           16.4 |          0.8 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            17.887902 |     997.112098 |   1.213026 |           0.2 |                   0.3 |                 117.5 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.746025 |   -66.746025 |    -8.343253 |                        -0.048737 |                       -0.038782 |                            -0.075462 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 03:00:00 |             96.7 |       0.8 |              1015.0 |           16.3 |          0.8 |              0.0 |                      0.0 |                18.534226 |                      1.180995 |            17.922597 |     997.077403 |   1.213429 |           0.2 |                   0.3 |                 117.5 |               84.848485 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.871985 |   -66.871985 |    -8.358998 |                        -0.049972 |                       -0.039735 |                            -0.114244 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 04:00:00 |             97.2 |       0.8 |              1015.0 |           16.0 |          0.8 |              0.0 |                 0.429734 |                18.182867 |                      1.161352 |            17.673747 |     997.326253 |   1.214802 |           0.2 |                   0.3 |                 117.5 |               61.046495 |       0.0 |           0.0 |                0.0 |        1.943686 |              1.554949 |            67.350953 |   -65.796004 |    -6.103894 |                        -0.051541 |                       -0.043408 |                            -0.153979 |              0.0 |                   0.0 |           0.3 |          100.0 |
    | 2000-08-03 05:00:00 |             97.5 |       0.6 |              1015.0 |           15.9 |          0.6 |              0.0 |                      1.0 |                18.067051 |                      1.154867 |            17.615375 |     997.384625 |   1.215249 |           0.2 |                   0.0 |            156.666667 |               44.486064 |       0.0 |           0.0 |                0.0 |       21.932441 |             17.545953 |             74.18377 |   -56.637817 |    -2.831891 |                        -0.047351 |                       -0.042938 |                            -0.197387 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 06:00:00 |             97.7 |       0.9 |              1015.0 |           16.0 |          0.9 |              0.0 |                      1.0 |                18.182867 |                      1.161352 |            17.764661 |     997.235339 |    1.21476 |           0.2 |                   0.0 |            104.444444 |               44.486064 |       0.0 |           0.0 |                0.0 |       57.256187 |             45.804949 |            76.052657 |   -30.247708 |    -1.512385 |                        -0.022926 |                       -0.019874 |                            -0.240325 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 07:00:00 |             97.4 |       0.9 |              1015.0 |           16.6 |          0.9 |              0.0 |                      1.0 |                18.891521 |                      1.200918 |            18.400342 |     996.599658 |   1.211956 |           0.2 |                   0.0 |            104.444444 |               44.486064 |       0.0 |           0.0 |                0.0 |      109.332844 |             87.466275 |            78.286958 |     9.179317 |     0.458966 |                         0.012762 |                        0.011094 |                            -0.260199 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 08:00:00 |             96.8 |       0.9 |              1016.0 |           17.4 |          0.9 |              0.0 |                      1.0 |                19.873972 |                      1.255448 |            19.238005 |     996.761995 |   1.209438 |           0.2 |                   0.0 |            104.444444 |               44.486064 |       0.0 |           0.0 |                0.0 |      170.949152 |            136.759322 |            80.758678 |    56.000644 |     2.800032 |                         0.056776 |                        0.049541 |                            -0.249105 |              0.0 |                   0.0 |           0.0 |          100.0 |
    | 2000-08-03 09:00:00 |             86.1 |       1.3 |              1016.0 |           19.0 |          1.3 |              0.2 |                      1.0 |                21.973933 |                      1.370827 |            18.919557 |     997.080443 |   1.202958 |           0.2 |                   0.2 |             72.307692 |               44.486064 |       0.0 |           0.0 |                0.0 |      311.762624 |              249.4101 |            83.807053 |   165.603046 |     8.280152 |                         0.192493 |                        0.160555 |                            -0.199564 |              0.0 |                   0.0 |           0.2 |          100.0 |
    | 2000-08-03 10:00:00 |             76.8 |       1.5 |              1016.0 |           20.3 |          1.5 |              0.5 |                      1.0 |                23.820593 |                      1.471068 |            18.294216 |     997.705784 |    1.19791 |           0.2 |                   0.5 |             62.666667 |               44.486064 |       0.0 |           0.0 |                0.0 |      501.583299 |            401.266639 |            78.072984 |   323.193655 |    16.159683 |                         0.383595 |                        0.314757 |                            -0.039008 |              0.0 |                   0.0 |           0.5 |          100.0 |
    | 2000-08-03 11:00:00 |             71.8 |       1.2 |              1016.0 |           21.4 |          1.2 |              0.7 |                      1.0 |                25.487706 |                      1.560666 |            18.300173 |     997.699827 |   1.193433 |           0.2 |                   0.7 |             78.333333 |               45.139282 |       0.0 |           0.0 |                0.0 |      615.018727 |            492.014981 |            65.479184 |   426.535797 |     21.32679 |                         0.489898 |                         0.41859 |                             0.275749 |              0.0 |                   0.0 |           0.7 |          124.0 |
    | 2000-08-03 12:00:00 |             67.5 |       1.3 |              1016.0 |           21.3 |          1.3 |              0.8 |                      1.0 |                 25.33205 |                      1.552334 |            17.099134 |     998.900866 |   1.194376 |           0.2 |                   0.8 |             72.307692 |               45.591614 |       0.0 |           0.0 |                0.0 |      626.544326 |            501.235461 |            55.933117 |   445.302344 |    22.265117 |                         0.525472 |                        0.442652 |                              0.69434 |              0.0 |                   0.0 |           0.8 |          148.0 |
    | 2000-08-03 13:00:00 |             66.1 |       1.5 |              1016.0 |           21.8 |          1.5 |              0.5 |                      1.0 |                26.118719 |                       1.59437 |            17.264473 |     998.735527 |   1.192277 |           0.2 |                   0.5 |             62.666667 |               45.923379 |       0.0 |           0.0 |                0.0 |      496.133417 |            396.906734 |            74.712412 |   322.194322 |    16.109716 |                         0.427223 |                         0.35209 |                             1.136991 |              0.0 |                   0.0 |           0.5 |          172.0 |
    | 2000-08-03 14:00:00 |             63.4 |       1.9 |              1016.0 |           22.9 |          1.9 |              0.4 |                      1.0 |                27.924898 |                      1.690242 |            17.704385 |     998.295615 |   1.187651 |           0.2 |                   0.4 |             49.473684 |               46.177112 |       0.0 |           0.0 |                0.0 |      419.520994 |            335.616795 |            74.509683 |   261.107112 |    13.055356 |                         0.415078 |                        0.329249 |                             1.489082 |              0.0 |                   0.0 |           0.4 |          196.0 |
    | 2000-08-03 15:00:00 |             62.4 |       1.9 |              1016.0 |           22.7 |          1.9 |              0.5 |                      1.0 |                27.588616 |                      1.672458 |            17.215297 |     998.784703 |   1.188672 |           0.2 |                   0.5 |             49.473684 |               46.377447 |       0.0 |           0.0 |                0.0 |      387.887354 |            310.309883 |            66.706608 |   243.603275 |    12.180164 |                          0.40046 |                        0.316867 |                             1.818331 |              0.0 |                   0.0 |           0.5 |          220.0 |
    | 2000-08-03 16:00:00 |             61.1 |       2.3 |              1016.0 |           22.5 |          2.3 |              0.5 |                      1.0 |                27.255876 |                      1.654832 |             16.65334 |      999.34666 |   1.189726 |           0.2 |                   0.5 |             40.869565 |               46.539635 |       0.0 |           0.0 |                0.0 |      278.496873 |            222.797499 |            61.019556 |   161.777943 |     8.088897 |                         0.357306 |                         0.27009 |                             2.135198 |              0.0 |                   0.0 |           0.5 |          244.0 |
    | 2000-08-03 17:00:00 |             62.1 |       2.4 |              1016.0 |           21.9 |          2.4 |              0.3 |                      1.0 |                26.278588 |                      1.602891 |            16.319003 |     999.680997 |   1.192295 |           0.2 |                   0.3 |             39.166667 |               46.673625 |       0.0 |           0.0 |                0.0 |      137.138608 |            109.710886 |            65.667044 |    44.043842 |     2.202192 |                         0.240721 |                        0.178882 |                             2.405288 |              0.0 |                   0.0 |           0.3 |          268.0 |
    | 2000-08-03 18:00:00 |             67.0 |       2.5 |              1016.0 |           21.4 |          2.5 |              0.1 |                      1.0 |                25.487706 |                      1.560666 |            17.076763 |     998.923237 |    1.19398 |           0.2 |                   0.1 |                  37.6 |               46.786182 |       0.0 |           0.0 |                0.0 |       51.080715 |             40.864572 |            67.356303 |   -26.491731 |    -1.324587 |                           0.1512 |                        0.110539 |                             2.584171 |              0.0 |                   0.0 |           0.1 |          292.0 |
    | 2000-08-03 19:00:00 |             74.5 |       2.5 |              1016.0 |           20.7 |          2.5 |              0.0 |                      1.0 |                24.415439 |                      1.503132 |            18.189502 |     997.810498 |   1.196326 |           0.2 |                   0.0 |                  37.6 |               46.882068 |       0.0 |           0.0 |                0.0 |       13.632816 |             10.906253 |            67.127904 |   -56.221651 |    -2.811083 |                         0.080478 |                        0.058384 |                             2.694709 |              0.0 |                   0.0 |           0.0 |          316.0 |
    | 2000-08-03 20:00:00 |             81.2 |       2.2 |              1016.0 |           19.4 |          2.2 |              0.0 |                   0.1364 |                 22.52831 |                      1.401035 |            18.292988 |     997.707012 |   1.201595 |           0.2 |                   0.0 |             42.727273 |              143.134128 |       0.0 |           0.0 |                0.0 |        0.185943 |              0.148755 |            68.417789 |   -68.269035 |    -7.835236 |                         0.024911 |                        0.012051 |                             2.753093 |              0.0 |                   0.0 |           0.0 |          340.0 |
    | 2000-08-03 21:00:00 |             86.9 |       1.7 |              1016.0 |           17.8 |          1.7 |              0.0 |                      0.0 |                20.381763 |                      1.283491 |            17.711752 |     998.288248 |   1.208466 |           0.2 |                   0.0 |             55.294118 |              220.606061 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            70.667062 |   -70.667062 |    -8.833383 |                        -0.015625 |                       -0.006654 |                             2.765144 |              0.0 |                   0.0 |           0.0 |          364.0 |
    | 2000-08-03 22:00:00 |             90.1 |       1.7 |              1017.0 |           17.0 |          1.7 |              0.0 |                      0.0 |                19.377294 |                      1.227926 |            17.458941 |     999.541059 |   1.213114 |           0.2 |                   0.0 |             55.294118 |              229.198312 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            71.684719 |   -71.684719 |     -8.96059 |                         -0.02696 |                       -0.011041 |                              2.75849 |              0.0 |                   0.0 |           0.0 |          388.0 |
    | 2000-08-03 23:00:00 |             90.9 |       2.3 |              1017.0 |           16.4 |          2.3 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            16.955269 |    1000.044731 |   1.215856 |           0.2 |                   0.0 |             40.869565 |              237.366255 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            72.396674 |   -72.396674 |    -9.049584 |                        -0.019425 |                       -0.006339 |                             2.747449 |              0.0 |                   0.0 |           0.0 |          412.0 |

.. _evap_pet_ambav1_hourly_simulation_water:

hourly simulation, water
________________________

|evap_pet_ambav1| also calculates hourly water evaporation values, which show a clear
diurnal pattern not apparent in the generally aggregated water evaporation values of
|evap_aet_morsim| in example :ref:`evap_aet_morsim_hourly_simulation_water`:

.. integration-test::

    >>> test.inits.loggedwaterevaporation = 0.1
    >>> interception(False)
    >>> soil(False)
    >>> plant(False)
    >>> water(True)
    >>> cropheight(0.0)
    >>> test("evap_pet_ambav1_hourly_simulation_water",
    ...      axis1=(fluxes.waterevaporation, fluxes.dailywaterevaporation))
    |                date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed10m | sunshineduration | possiblesunshineduration | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | dryairpressure | airdensity | currentalbedo | adjustedcloudcoverage | aerodynamicresistance | actualsurfaceresistance | snowcover | precipitation | dailyprecipitation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | potentialinterceptionevaporation | potentialsoilevapotranspiration | dailypotentialsoilevapotranspiration | waterevaporation | dailywaterevaporation | cloudcoverage | soilresistance |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-03 00:00:00 |             95.1 |       0.8 |              1015.0 |           16.9 |          0.8 |              0.0 |                      0.0 |                19.254836 |                      1.221127 |            18.311349 |     996.688651 |   1.210743 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.097029 |   -66.097029 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061946 |              2.238054 |           0.3 |            nan |
    | 2000-08-03 01:00:00 |             94.9 |       0.8 |              1015.0 |           16.6 |          0.8 |              0.0 |                      0.0 |                18.891521 |                      1.200918 |            17.928054 |     997.071946 |   1.212171 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |             66.49025 |    -66.49025 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.061919 |              2.076136 |           0.3 |            nan |
    | 2000-08-03 02:00:00 |             95.9 |       0.8 |              1015.0 |           16.4 |          0.8 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            17.887902 |     997.112098 |   1.213026 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.746025 |   -66.746025 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062108 |              1.914028 |           0.3 |            nan |
    | 2000-08-03 03:00:00 |             96.7 |       0.8 |              1015.0 |           16.3 |          0.8 |              0.0 |                      0.0 |                18.534226 |                      1.180995 |            17.922597 |     997.077403 |   1.213429 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            66.871985 |   -66.871985 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062257 |              1.751771 |           0.3 |            nan |
    | 2000-08-03 04:00:00 |             97.2 |       0.8 |              1015.0 |           16.0 |          0.8 |              0.0 |                 0.429734 |                18.182867 |                      1.161352 |            17.673747 |     997.326253 |   1.214802 |           0.2 |                   0.3 |            941.218972 |                     0.0 |       0.0 |           0.0 |                0.0 |        1.943686 |              1.554949 |            67.350953 |   -65.796004 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.060973 |              1.590798 |           0.3 |            nan |
    | 2000-08-03 05:00:00 |             97.5 |       0.6 |              1015.0 |           15.9 |          0.6 |              0.0 |                      1.0 |                18.067051 |                      1.154867 |            17.615375 |     997.384625 |   1.215249 |           0.2 |                   0.0 |           1254.958629 |                     0.0 |       0.0 |           0.0 |                0.0 |       21.932441 |             17.545953 |             74.18377 |   -56.637817 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.052482 |              1.438317 |           0.0 |            nan |
    | 2000-08-03 06:00:00 |             97.7 |       0.9 |              1015.0 |           16.0 |          0.9 |              0.0 |                      1.0 |                18.182867 |                      1.161352 |            17.764661 |     997.235339 |    1.21476 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |       57.256187 |             45.804949 |            76.052657 |   -30.247708 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.027784 |              1.310533 |           0.0 |            nan |
    | 2000-08-03 07:00:00 |             97.4 |       0.9 |              1015.0 |           16.6 |          0.9 |              0.0 |                      1.0 |                18.891521 |                      1.200918 |            18.400342 |     996.599658 |   1.211956 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |      109.332844 |             87.466275 |            78.286958 |     9.179317 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.009247 |               1.21978 |           0.0 |            nan |
    | 2000-08-03 08:00:00 |             96.8 |       0.9 |              1016.0 |           17.4 |          0.9 |              0.0 |                      1.0 |                19.873972 |                      1.255448 |            19.238005 |     996.761995 |   1.209438 |           0.2 |                   0.0 |            836.639086 |                     0.0 |       0.0 |           0.0 |                0.0 |      170.949152 |            136.759322 |            80.758678 |    56.000644 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.054509 |              1.174289 |           0.0 |            nan |
    | 2000-08-03 09:00:00 |             86.1 |       1.3 |              1016.0 |           19.0 |          1.3 |              0.2 |                      1.0 |                21.973933 |                      1.370827 |            18.919557 |     997.080443 |   1.202958 |           0.2 |                   0.2 |            579.211675 |                     0.0 |       0.0 |           0.0 |                0.0 |      311.762624 |              249.4101 |            83.807053 |   165.603046 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.168431 |               1.24272 |           0.2 |            nan |
    | 2000-08-03 10:00:00 |             76.8 |       1.5 |              1016.0 |           20.3 |          1.5 |              0.5 |                      1.0 |                23.820593 |                      1.471068 |            18.294216 |     997.705784 |    1.19791 |           0.2 |                   0.5 |            501.983452 |                     0.0 |       0.0 |           0.0 |                0.0 |      501.583299 |            401.266639 |            78.072984 |   323.193655 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.33605 |               1.47877 |           0.5 |            nan |
    | 2000-08-03 11:00:00 |             71.8 |       1.2 |              1016.0 |           21.4 |          1.2 |              0.7 |                      1.0 |                25.487706 |                      1.560666 |            18.300173 |     997.699827 |   1.193433 |           0.2 |                   0.7 |            627.479315 |                     0.0 |       0.0 |           0.0 |                0.0 |      615.018727 |            492.014981 |            65.479184 |   426.535797 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.448309 |              1.827078 |           0.7 |            nan |
    | 2000-08-03 12:00:00 |             67.5 |       1.3 |              1016.0 |           21.3 |          1.3 |              0.8 |                      1.0 |                 25.33205 |                      1.552334 |            17.099134 |     998.900866 |   1.194376 |           0.2 |                   0.8 |            579.211675 |                     0.0 |       0.0 |           0.0 |                0.0 |      626.544326 |            501.235461 |            55.933117 |   445.302344 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.469143 |              2.196221 |           0.8 |            nan |
    | 2000-08-03 13:00:00 |             66.1 |       1.5 |              1016.0 |           21.8 |          1.5 |              0.5 |                      1.0 |                26.118719 |                       1.59437 |            17.264473 |     998.735527 |   1.192277 |           0.2 |                   0.5 |            501.983452 |                     0.0 |       0.0 |           0.0 |                0.0 |      496.133417 |            396.906734 |            74.712412 |   322.194322 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.347617 |              2.443838 |           0.5 |            nan |
    | 2000-08-03 14:00:00 |             63.4 |       1.9 |              1016.0 |           22.9 |          1.9 |              0.4 |                      1.0 |                27.924898 |                      1.690242 |            17.704385 |     998.295615 |   1.187651 |           0.2 |                   0.4 |            396.302725 |                     0.0 |       0.0 |           0.0 |                0.0 |      419.520994 |            335.616795 |            74.509683 |   261.107112 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.29431 |              2.638148 |           0.4 |            nan |
    | 2000-08-03 15:00:00 |             62.4 |       1.9 |              1016.0 |           22.7 |          1.9 |              0.5 |                      1.0 |                27.588616 |                      1.672458 |            17.215297 |     998.784703 |   1.188672 |           0.2 |                   0.5 |            396.302725 |                     0.0 |       0.0 |           0.0 |                0.0 |      387.887354 |            310.309883 |            66.706608 |   243.603275 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |          0.27556 |              2.813707 |           0.5 |            nan |
    | 2000-08-03 16:00:00 |             61.1 |       2.3 |              1016.0 |           22.5 |          2.3 |              0.5 |                      1.0 |                27.255876 |                      1.654832 |             16.65334 |      999.34666 |   1.189726 |           0.2 |                   0.5 |            327.380512 |                     0.0 |       0.0 |           0.0 |                0.0 |      278.496873 |            222.797499 |            61.019556 |   161.777943 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.193958 |              2.907665 |           0.5 |            nan |
    | 2000-08-03 17:00:00 |             62.1 |       2.4 |              1016.0 |           21.9 |          2.4 |              0.3 |                      1.0 |                26.278588 |                      1.602891 |            16.319003 |     999.680997 |   1.192295 |           0.2 |                   0.3 |            313.739657 |                     0.0 |       0.0 |           0.0 |                0.0 |      137.138608 |            109.710886 |            65.667044 |    44.043842 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         0.070342 |              2.878007 |           0.3 |            nan |
    | 2000-08-03 18:00:00 |             67.0 |       2.5 |              1016.0 |           21.4 |          2.5 |              0.1 |                      1.0 |                25.487706 |                      1.560666 |            17.076763 |     998.923237 |    1.19398 |           0.2 |                   0.1 |            301.190071 |                     0.0 |       0.0 |           0.0 |                0.0 |       51.080715 |             40.864572 |            67.356303 |   -26.491731 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |         -0.00517 |              2.772837 |           0.1 |            nan |
    | 2000-08-03 19:00:00 |             74.5 |       2.5 |              1016.0 |           20.7 |          2.5 |              0.0 |                      1.0 |                24.415439 |                      1.503132 |            18.189502 |     997.810498 |   1.196326 |           0.2 |                   0.0 |            301.190071 |                     0.0 |       0.0 |           0.0 |                0.0 |       13.632816 |             10.906253 |            67.127904 |   -56.221651 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.040413 |              2.632424 |           0.0 |            nan |
    | 2000-08-03 20:00:00 |             81.2 |       2.2 |              1016.0 |           19.4 |          2.2 |              0.0 |                   0.1364 |                 22.52831 |                      1.401035 |            18.292988 |     997.707012 |   1.201595 |           0.2 |                   0.0 |            342.261444 |                     0.0 |       0.0 |           0.0 |                0.0 |        0.185943 |              0.148755 |            68.417789 |   -68.269035 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.057386 |              2.475038 |           0.0 |            nan |
    | 2000-08-03 21:00:00 |             86.9 |       1.7 |              1016.0 |           17.8 |          1.7 |              0.0 |                      0.0 |                20.381763 |                      1.283491 |            17.711752 |     998.288248 |   1.208466 |           0.2 |                   0.0 |            442.926575 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            70.667062 |   -70.667062 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.062884 |              2.312154 |           0.0 |            nan |
    | 2000-08-03 22:00:00 |             90.1 |       1.7 |              1017.0 |           17.0 |          1.7 |              0.0 |                      0.0 |                19.377294 |                      1.227926 |            17.458941 |     999.541059 |   1.213114 |           0.2 |                   0.0 |            442.926575 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            71.684719 |   -71.684719 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.064246 |              2.147909 |           0.0 |            nan |
    | 2000-08-03 23:00:00 |             90.9 |       2.3 |              1017.0 |           16.4 |          2.3 |              0.0 |                      0.0 |                18.652661 |                      1.187604 |            16.955269 |    1000.044731 |   1.215856 |           0.2 |                   0.0 |            327.380512 |                     0.0 |       0.0 |           0.0 |                0.0 |             0.0 |                   0.0 |            72.396674 |   -72.396674 |          0.0 |                              0.0 |                             0.0 |                                  0.0 |        -0.063192 |              1.984717 |           0.0 |            nan |
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
    """|evap_pet_ambav1.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-PET-AMBAV-1.0",
        description="potential evapotranspiration based on AMBAV 1.0",
    )
    __HYDPY_ROOTMODEL__ = False

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
        evap_model.Calc_WindSpeed10m_V1,
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
