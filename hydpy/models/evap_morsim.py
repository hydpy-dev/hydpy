# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the MORECS equations :cite:p:`ref-Thompson1981` for calculating
actual evapotranspiration with some modifications following the LARSIM model
:cite:p:`ref-LARSIM`.

|evap_morsim| is a submodel that supplies its main model with estimates of
evapotranspiration from soils and evaporation from interception storages and water
areas.  The following list summarises its main components:

 * Evaporation from water surfaces after Penman :cite:p:`ref-Penman1948`.
 * Interception evaporation after Penman-Monteith, assuming zero surface resistance
   :cite:p:`ref-Thompson1981`.
 * Surface roughness after Quast and Böhm :cite:p:`ref-Quast1997`
 * "Potential" evapotranspiration from soils after Penman-Monteith
   :cite:p:`ref-Thompson1981`.
 * "Actual" evapotranspiration from soils after Wigmosta :cite:p:`ref-Wigmosta1994`.

|evap_morsim| requires additional data about the catchment's current state, which it
usually queries from its main model, if possible:

 * The current air temperature (required).
 * The amount of intercepted water (required).
 * The soil water content (required).
 * The snow cover degree (required).
 * The current snow albedo (optional).
 * The snow cover degree within the canopy of tree-like vegetation (optional).

The last two data types are optional.  Hence, |evap_morsim| works in combination with
models as |hland_v1|, which cannot estimate the current snow albedo and snow
interception.  Then, |evap_morsim| relies on land type-specific albedo values (for
snow-free conditions) and assumes zero snow interception.

Integration tests
=================

.. how_to_understand_integration_tests::

We prepare a simulation period of three days for the first examples:

>>> from hydpy import pub, Timegrid
>>> pub.timegrids = "2000-08-01", "2000-08-04", "1d"

According to the intended usage as a submodel, |evap_morsim| requires no connections to
any nodes.  Hence, assigning a model instance to a blank |Element| instance is
sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_morsim import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

We will apply the following parameter set on all integration tests, which makes a few
of them a little unrealistic but simplifies comparisons:

>>> nmbhru(1)
>>> hrutype(0)
>>> measuringheightwindspeed(10.0)
>>> albedo(0.2)
>>> leafareaindex(5.0)
>>> cropheight(10.0)
>>> surfaceresistance(40.0)
>>> emissivity(0.95)
>>> averagesoilheatflux(3.0)
>>> fieldcapacity(200.0)
>>> wiltingpoint(100.0)

We add submodels of type |meteo_temp_io|, |dummy_interceptedwater|, |dummy_soilwater|,
|dummy_snowcover|, |dummy_snowalbedo|, and |dummy_snowycanopy| that supply additional
information on the catchment's state instead of complicating the comparisons by
introducing a complex main model:

>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     hruarea(1.0)
...     temperatureaddend(0.0)
>>> with model.add_intercmodel_v1("dummy_interceptedwater"):
...     pass
>>> with model.add_soilwatermodel_v1("dummy_soilwater"):
...     pass
>>> with model.add_snowcovermodel_v1("dummy_snowcover"):
...     pass
>>> with model.add_snowalbedomodel_v1("dummy_snowalbedo"):
...     pass
>>> with model.add_snowycanopymodel_v1("dummy_snowycanopy"):
...     pass

Now we can initialise an |IntegrationTest| object:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

The following time-constant meteorological input data will also apply to all
integration tests except those with an hourly simulation step:

>>> inputs.windspeed.series = 2.0
>>> inputs.relativehumidity.series = 80.0
>>> inputs.atmosphericpressure.series = 1000.0
>>> inputs.sunshineduration.series = 6.0
>>> inputs.possiblesunshineduration.series = 16.0
>>> inputs.globalradiation.series = 190.0

The data supplied by the submodels varies only for the amount of intercepted water:

>>> model.tempmodel.sequences.inputs.temperature.series = 15.0
>>> model.intercmodel.sequences.inputs.interceptedwater.series = [0.0], [3.0], [6.0]
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 50.0

We set the snow-related data so that |evap_morsim| assumes snow-free conditions for
now:

>>> model.snowcovermodel.sequences.inputs.snowcover.series = 0.0
>>> model.snowycanopymodel.sequences.inputs.snowycanopy.series = 0.0
>>> model.snowalbedomodel.sequences.inputs.snowalbedo.series[:] = nan

non-tree vegetation
___________________

Both interception evaporation and soil evapotranspiration are relevant for hydrological
response units with vegetation:

>>> interception(True)
>>> soil(True)
>>> tree(False)
>>> conifer(False)

The following test results demonstrate the general functioning of |evap_morsim|.  Due
to the simulation step of one day, the "daily" averages or sums (e.g.
|DailyAirTemperature|) are equal to their original counterparts (|AirTemperature|).
The last two columns show how the :cite:t:`ref-Wigmosta1994` approach reduces soil
evapotranspiration to prevent too high total evaporation estimates:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |               2.326858 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |               0.783365 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

deciduous trees
_______________

|evap_morsim| does not distinguish between non-tree vegetation and deciduous trees for
snow-free conditions.  Hence, without adjusting other model parameters, activating the
|evap_control.Tree| flag while keeping the |evap_control.Conifer| flag disabled does
not change simulation results:

.. integration-test::

    >>> tree(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |               2.326858 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |               0.783365 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

conifers
________

However, |evap_morsim| applies additional equations for coniferous trees as explained
in the documentation on method |Calc_LanduseSurfaceResistance_V1|.  Hence, also
enabling the |evap_control.Conifer| flag causes some differences from the previous
results:

.. integration-test::

    >>> conifer(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               195.475111 |              125.663522 |              0.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |                2.13897 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               195.475111 |              125.663522 |              3.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |               0.720111 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               195.475111 |              125.663522 |              6.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |


bare soil
_________

If we simulate bare soil by disabling interception evaporation, soil water
evapotranspiration becomes identical for all three days:

.. integration-test::

    >>> interception(False)
    >>> tree(False)
    >>> conifer(False)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                              0.0 |              0.0 |                     0.0 |               2.326858 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                              0.0 |              0.0 |                     0.0 |               2.326858 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                              0.0 |              0.0 |                     0.0 |               2.326858 |

sealed surface
______________

For simulating sealed surfaces, one can disable the |evap_control.Soil| flag:

.. integration-test::

    >>> interception(True)
    >>> soil(False)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              0.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |                    0.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              3.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              6.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

water area
__________

Set the |evap_control.Interception| and the |evap_control.Soil| flag to |False| and
the |evap_control.Water| flag to |True| to disable the Penman-Monteith-based
interception evaporation and soil evapotranspiration estimation and enable the
Penman-based open water evaporation estimation:

.. integration-test::

    >>> interception(False)
    >>> water(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              0.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          0.0 |                              0.0 |          3.17665 |                     0.0 |                    0.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              3.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          0.0 |                              0.0 |          3.17665 |                     0.0 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              6.0 |      50.0 |       0.0 |         0.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          0.0 |                              0.0 |          3.17665 |                     0.0 |                    0.0 |

snow on non-tree vegetation
___________________________

Next, we show how |evap_morsim| uses external information on the occurrence of snow to
modify its outputs.  Therefore, we set the degree of the snow cover (on the ground) to
one and the snow albedo to 0.8:

>>> water(False)
>>> interception(True)
>>> soil(True)
>>> model.snowcovermodel.sequences.inputs.snowcover.series = 1.0
>>> model.snowalbedomodel.sequences.inputs.snowalbedo.series = 0.8

Now |evap_morsim| uses the given snow albedo instead of the land type-specific albedo
value for snow-free conditions for calculating the net shortwave radiation.  However,
this difference is irrelevant for non-tree vegetation, as any appearance of snow (on
the ground) suppresses interception evaporation and soil evapotranspiration completely:

.. integration-test::

    >>> tree(False)
    >>> conifer(False)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       1.0 |         0.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |                    0.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       1.0 |         0.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       1.0 |         0.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |                    0.0 |

snow under tree canopies
________________________

In contrast, snow on the ground does not suppress interception evaporation and soil
evapotranspiration for tree-like vegetation:

.. integration-test::

    >>> tree(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       1.0 |         0.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       1.0 |         0.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                2.189754 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       1.0 |         0.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                2.189754 |                    0.0 |

snow in tree canopies
______________________

However, snow interception in the canopy suppresses interception evaporation (but not
soil evapotranspiration - should we change this?):

.. integration-test::

    >>> model.snowycanopymodel.sequences.inputs.snowycanopy.series = 1.0
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       1.0 |         1.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       1.0 |         1.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |              6.0 |                     16.0 |           190.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       1.0 |         1.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |

hourly simulation, land
_______________________

For sub-daily step sizes, the averaging and summing mechanisms of |evap_morsim| come
into play.  To demonstrate this, we prepare a simulation period of 24 hours:

>>> pub.timegrids = "2000-08-01", "2000-08-02", "1h"

We need to restore the values of all time-dependent parameters:

>>> for parameter in model.parameters.fixed:
...     parameter.restore()
>>> test = IntegrationTest(element)

The following meteorological input data stems from the
:ref:`lland_v3_acker_summer_hourly` example of |lland_v3|:

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

|evap_morsim| calculates "daily" averages and sums based on the last 24 hours.  Hence,
we must provide the corresponding logged data for the 24 hours preceding the simulation
period.  We take them from the :ref:`lland_v3_acker_summer_hourly` example, too:

>>> test.inits = (
...     (logs.loggedsunshineduration,
...      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.1, 0.2, 0.1, 0.2, 0.2, 0.3, 0.0,
...       0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
...     (logs.loggedpossiblesunshineduration,
...      [0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
...       1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.0, 0.0, 0.0]),
...     (logs.loggedglobalradiation,
...      [0.0, 0.0, 0.0, 0.0, 0.0, 27.8, 55.6, 138.9, 222.2, 305.6, 333.3, 388.9,
...       527.8, 444.4, 250.0, 222.2, 166.7, 111.1, 55.6, 27.8, 0.0, 0.0, 0.0, 0.0]),
...     (logs.loggedairtemperature,
...      [[13.2], [13.2], [13.1], [12.6], [12.7], [13.0], [13.5], [14.8], [16.2],
...       [17.7], [18.8], [19.4], [20.4], [21.0], [21.5], [21.2], [20.4], [20.7],
...       [20.2], [19.7], [19.0], [18.0], [17.5], [17.1]]),
...     (logs.loggedrelativehumidity,
...      [95.1, 94.5, 94.8, 96.4, 96.6, 97.1, 97.1, 96.7, 92.2, 88.5, 81.1, 76.5, 75.1,
...       70.8, 68.9, 69.2, 75.0, 74.0, 77.4, 81.4, 85.3, 90.1, 92.3, 93.8]),
...     (logs.loggedwindspeed2m,
...      [0.8, 1.0, 1.2, 1.3, 0.9, 1.1, 1.3, 1.3, 1.9, 2.2, 1.8, 2.3, 2.4, 2.5, 2.4,
...       2.5, 2.1, 2.2, 1.7, 1.7, 1.3, 1.3, 0.7, 0.8]))

The considered day is warm and snow-free:

>>> model.tempmodel.sequences.inputs.temperature.series = (
...     16.9, 16.6, 16.4, 16.3, 16.0, 15.9, 16.0, 16.6, 17.4, 19.0, 20.3, 21.4, 21.3,
...     21.8, 22.9, 22.7, 22.5, 21.9, 21.4, 20.7, 19.4, 17.8, 17.0, 16.4)
>>> model.snowcovermodel.sequences.inputs.snowcover.series = 0.0
>>> model.intercmodel.sequences.inputs.interceptedwater.series = 0.1
>>> model.snowycanopymodel.sequences.inputs.snowycanopy.series = 0.0
>>> model.snowalbedomodel.sequences.inputs.snowalbedo.series[:] = nan

For land areas, there is a clear diurnal evaporation pattern with a maximum around noon
and a minimum with possible condensation at night because the Penman-Monteith
equation uses only a few "daily" input values (see
|Return_Evaporation_PenmanMonteith_V1|):

.. integration-test::

    >>> test()
    |                date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-01 00:00:00 |             95.1 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.9 |           17.279167 |    0.641273 |         1.605886 |          0.8 |             85.883333 |                   1.3 |                          15.7 |                19.284227 |                     19.753091 |                      1.223615 |                           1.249589 |              18.3393 |                 16.964613 |       996.6607 |    1.21073 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.408237 |   -10.408237 |         98.855096 |          3.0 |                        -0.001093 |              0.0 |               -0.001093 |                    0.0 |
    | 2000-08-01 01:00:00 |             94.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.6 |           17.241667 |    0.641273 |         1.603439 |          0.8 |             85.991667 |                   1.3 |                          15.7 |                18.920184 |                      19.70628 |                       1.20339 |                           1.246999 |            17.955254 |                 16.945759 |     997.044746 |   1.212158 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                  10.41572 |    -10.41572 |         98.847613 |          3.0 |                        -0.000723 |              0.0 |               -0.000723 |                    0.0 |
    | 2000-08-01 02:00:00 |             95.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.4 |              17.175 |    0.641273 |         1.575992 |          0.8 |             86.233333 |                   1.3 |                          15.7 |                 18.68084 |                       19.6233 |                      1.190065 |                           1.242407 |            17.914926 |                 16.921826 |     997.085074 |   1.213014 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.421627 |   -10.421627 |         98.841706 |          3.0 |                        -0.002702 |              0.0 |               -0.002702 |                    0.0 |
    | 2000-08-01 03:00:00 |             96.7 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.3 |             17.0625 |    0.641273 |         1.548545 |          0.8 |             86.708333 |                   1.3 |                          15.5 |                18.562165 |                     19.483964 |                      1.183449 |                            1.23469 |            17.949613 |                  16.89422 |     997.050387 |   1.213417 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.455184 |   -10.455184 |          98.80815 |          3.0 |                        -0.004292 |              0.0 |               -0.004292 |                    0.0 |
    | 2000-08-01 04:00:00 |             97.2 |       0.8 |              1015.0 |              0.0 |                      0.4 |             1.9 |           16.0 |           16.908333 |    0.641273 |         1.504432 |          0.8 |             87.366667 |                   1.3 |                          14.9 |                18.210086 |                     19.294427 |                      1.163788 |                           1.224181 |            17.700204 |                 16.856897 |     997.299796 |    1.21479 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               68.103437 |              0.1 |       nan |       0.0 |         0.0 |                135.5 |                  1.52 |                      108.4 |                 10.560684 |    -9.040684 |         97.839316 |          3.0 |                        -0.004126 |              0.0 |               -0.004126 |                    0.0 |
    | 2000-08-01 05:00:00 |             97.5 |       0.6 |              1015.0 |              0.0 |                      1.0 |            21.9 |           15.9 |           16.729167 |    0.480955 |         1.453638 |          0.6 |             88.204167 |                   1.3 |                          14.9 |                18.094032 |                     19.076181 |                      1.157296 |                           1.212063 |            17.641681 |                 16.825987 |     997.358319 |   1.215237 |           0.2 |            156.666667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           134.095833 |                 17.52 |                 107.276667 |                 10.550629 |     6.969371 |         96.726038 |          3.0 |                         0.006807 |              0.0 |                0.006807 |                    0.0 |
    | 2000-08-01 06:00:00 |             97.7 |       0.9 |              1015.0 |              0.0 |                      1.0 |            57.3 |           16.0 |           16.533333 |    0.721432 |         1.392031 |          0.9 |             89.191667 |                   1.3 |                          14.9 |                18.210086 |                     18.840106 |                      1.163788 |                           1.198935 |            17.791254 |                 16.803805 |     997.208746 |   1.214748 |           0.2 |            104.444444 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           131.854167 |                 45.84 |                 105.483333 |                 10.530586 |    35.309414 |         94.952747 |          3.0 |                         0.030947 |              0.0 |                0.030947 |                    0.0 |
    | 2000-08-01 07:00:00 |             97.4 |       0.9 |              1015.0 |              0.0 |                      1.0 |           109.3 |           16.6 |              16.375 |    0.721432 |         1.334591 |          0.9 |                90.125 |                   1.3 |                          14.9 |                18.920184 |                     18.651109 |                       1.20339 |                           1.188408 |            18.428259 |                 16.809312 |     996.571741 |   1.211943 |           0.2 |            104.444444 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |             129.4625 |                 87.44 |                     103.57 |                 10.496138 |    76.943862 |         93.073862 |          3.0 |                         0.066077 |              0.0 |                0.066077 |                    0.0 |
    | 2000-08-01 08:00:00 |             96.8 |       0.9 |              1016.0 |              0.0 |                      1.0 |           170.9 |           17.4 |           16.216667 |    0.721432 |         1.260484 |          0.9 |                91.275 |                   1.3 |                          14.9 |                19.904589 |                     18.463773 |                      1.257963 |                           1.177959 |            19.267642 |                 16.852809 |     996.732358 |   1.209425 |           0.2 |            104.444444 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |              127.325 |                136.72 |                     101.86 |                 10.432293 |   126.287707 |         91.427707 |          3.0 |                         0.109708 |              0.0 |                     0.1 |               0.007954 |
    | 2000-08-01 09:00:00 |             86.1 |       1.3 |              1016.0 |              0.2 |                      1.0 |           311.8 |           19.0 |             16.1125 |    1.042069 |         1.203904 |          1.3 |             91.991667 |                   1.5 |                          14.9 |                22.008543 |                     18.341425 |                      1.373407 |                           1.171128 |            18.949356 |                 16.872582 |     997.050644 |   1.202945 |           0.2 |             72.307692 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |                129.9 |                249.44 |                     103.92 |                 10.811102 |   238.628898 |         93.108898 |          3.0 |                         0.255453 |              0.0 |                     0.1 |               0.120904 |
    | 2000-08-01 10:00:00 |             76.8 |       1.5 |              1016.0 |              0.5 |                      1.0 |           501.6 |           20.3 |           16.083333 |    1.202387 |         1.149836 |          1.5 |             92.241667 |                   1.7 |                          14.9 |                23.858503 |                     18.307295 |                      1.473678 |                           1.169221 |             18.32333 |                 16.886954 |      997.67667 |   1.197896 |           0.2 |             62.666667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           132.283333 |                401.28 |                 105.826667 |                 11.206987 |   390.073013 |          94.61968 |          3.0 |                         0.446556 |              0.0 |                     0.1 |               0.264584 |
    | 2000-08-01 11:00:00 |             71.8 |       1.2 |              1016.0 |              0.7 |                      1.0 |           615.0 |           21.4 |              16.125 |    0.961909 |         1.089916 |          1.2 |             92.104167 |                   2.2 |                          14.9 |                25.528421 |                     18.356069 |                      1.563281 |                           1.171946 |            18.329406 |                 16.906704 |     997.670594 |    1.19342 |           0.2 |             78.333333 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           135.916667 |                 492.0 |                 108.733333 |                 12.231168 |   479.768832 |         96.502165 |          3.0 |                         0.533353 |              0.0 |                     0.1 |               0.347339 |
    | 2000-08-01 12:00:00 |             67.5 |       1.3 |              1016.0 |              0.8 |                      1.0 |           626.5 |           21.3 |           16.204167 |    1.042069 |         1.037502 |          1.3 |             91.729167 |                   2.8 |                          14.9 |                 25.37251 |                     18.449053 |                       1.55495 |                           1.177138 |            17.126444 |                 16.923163 |     998.873556 |   1.194363 |           0.2 |             72.307692 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           145.816667 |                 501.2 |                 116.653333 |                 13.472648 |   487.727352 |        103.180685 |          3.0 |                          0.56382 |              0.0 |                     0.1 |               0.366481 |
    | 2000-08-01 13:00:00 |             66.1 |       1.5 |              1016.0 |              0.5 |                      1.0 |           496.1 |           21.8 |           16.329167 |    1.202387 |         1.012602 |          1.5 |             91.104167 |                   3.2 |                          14.9 |                26.160453 |                      18.59671 |                      1.596982 |                           1.185375 |             17.29206 |                 16.942378 |      998.70794 |   1.192265 |           0.2 |             62.666667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |                152.6 |                396.88 |                     122.08 |                 14.310598 |   382.569402 |        107.769402 |          3.0 |                         0.493901 |              0.0 |                     0.1 |               0.304171 |
    | 2000-08-01 14:00:00 |             63.4 |       1.9 |              1016.0 |              0.4 |                      1.0 |           419.5 |           22.9 |           16.545833 |    1.523023 |         0.984394 |          1.9 |             90.058333 |                   3.4 |                          14.9 |                27.969419 |                     18.855098 |                      1.692831 |                           1.199769 |            17.732611 |                 16.980587 |     998.267389 |   1.187639 |           0.2 |             49.473684 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           157.345833 |                 335.6 |                 125.876667 |                 14.740009 |   320.859991 |        111.136658 |          3.0 |                         0.492638 |              0.0 |                     0.1 |               0.291122 |
    | 2000-08-01 15:00:00 |             62.4 |       1.9 |              1016.0 |              0.5 |                      1.0 |           387.9 |           22.7 |           16.816667 |    1.523023 |         0.968687 |          1.9 |             88.816667 |                   3.8 |                          14.9 |                27.632633 |                     19.182495 |                      1.675052 |                           1.217969 |            17.242763 |                 17.037252 |     998.757237 |    1.18866 |           0.2 |             49.473684 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |               164.25 |                310.32 |                      131.4 |                 15.578473 |   294.741527 |        115.821527 |          3.0 |                         0.469886 |              0.0 |                     0.1 |               0.273771 |
    | 2000-08-01 16:00:00 |             61.1 |       2.3 |              1016.0 |              0.5 |                      1.0 |           278.5 |           22.5 |             17.1375 |     1.84366 |         0.991339 |          2.3 |             87.333333 |                   4.1 |                          14.9 |                27.299387 |                     19.576758 |                      1.657431 |                            1.23983 |            16.679926 |                 17.097035 |     999.320074 |   1.189715 |           0.2 |             40.869565 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           170.066667 |                 222.8 |                 136.053333 |                 16.221893 |   206.578107 |         119.83144 |          3.0 |                         0.424257 |              0.0 |                     0.1 |               0.228608 |
    | 2000-08-01 17:00:00 |             62.1 |       2.4 |              1016.0 |              0.3 |                      1.0 |           137.1 |           21.9 |             17.4875 |    1.923819 |         1.017332 |          2.4 |                85.875 |                   4.4 |                          14.9 |                26.320577 |                     20.014927 |                      1.605502 |                           1.264057 |            16.345078 |                 17.187818 |     999.654922 |   1.192283 |           0.2 |             39.166667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |             173.4625 |                109.68 |                     138.77 |                 16.837082 |    92.842918 |        121.932918 |          3.0 |                         0.310119 |              0.0 |                     0.1 |               0.145541 |
    | 2000-08-01 18:00:00 |             67.0 |       2.5 |              1016.0 |              0.1 |                      1.0 |            51.1 |           21.4 |             17.8375 |    2.003978 |         1.054998 |          2.5 |             84.620833 |                   4.5 |                          14.9 |                25.528421 |                     20.461645 |                      1.563281 |                           1.288683 |            17.104042 |                 17.314814 |     998.895958 |   1.193968 |           0.2 |                  37.6 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |           174.433333 |                 40.88 |                 139.546667 |                 16.991532 |    23.888468 |        122.555135 |          3.0 |                         0.218167 |              0.0 |                     0.1 |               0.080478 |
    | 2000-08-01 19:00:00 |             74.5 |       2.5 |              1016.0 |              0.0 |                      1.0 |            13.6 |           20.7 |           18.170833 |    2.003978 |         1.100997 |          2.5 |                  83.7 |                   4.5 |                          15.4 |                24.454368 |                     20.895167 |                      1.505746 |                           1.312512 |            18.218504 |                 17.489255 |     997.781496 |   1.196313 |           0.2 |                  37.6 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |                175.0 |                 10.88 |                      140.0 |                 16.573988 |    -5.693988 |        123.426012 |          3.0 |                         0.141776 |              0.0 |                     0.1 |               0.028232 |
    | 2000-08-01 20:00:00 |             81.2 |       2.2 |              1016.0 |              0.0 |                      0.2 |             0.2 |           19.4 |           18.454167 |    1.763501 |         1.120309 |          2.2 |             83.066667 |                   4.5 |                          15.6 |                22.563931 |                      21.26995 |                      1.403627 |                           1.333058 |            18.321912 |                 17.668238 |     997.678088 |   1.201582 |           0.2 |             42.727273 |                 100.0 |                 48.85611 |               74.952555 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                  0.16 |                 140.006667 |                 16.324471 |   -16.164471 |        123.682196 |          3.0 |                         0.077581 |              0.0 |                0.077581 |                    0.0 |
    | 2000-08-01 21:00:00 |             86.9 |       1.7 |              1016.0 |              0.0 |                      0.0 |             0.0 |           17.8 |               18.65 |    1.362705 |         1.127089 |          1.7 |               82.7375 |                   4.5 |                          15.6 |                20.413369 |                     21.532411 |                      1.286025 |                           1.347418 |            17.739217 |                 17.815378 |     998.260783 |   1.208454 |           0.2 |             55.294118 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                   0.0 |                 140.006667 |                 16.202924 |   -16.202924 |        123.803743 |          3.0 |                         0.033589 |              0.0 |                0.033589 |                    0.0 |
    | 2000-08-01 22:00:00 |             90.1 |       1.7 |              1017.0 |              0.0 |                      0.0 |             0.0 |           17.0 |           18.808333 |    1.362705 |         1.142201 |          1.7 |             82.554167 |                   4.5 |                          15.6 |                19.406929 |                     21.746678 |                      1.230421 |                           1.359123 |            17.485643 |                 17.952788 |     999.514357 |   1.213101 |           0.2 |             55.294118 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                   0.0 |                 140.006667 |                  16.08262 |    -16.08262 |        123.924047 |          3.0 |                         0.020761 |              0.0 |                0.020761 |                    0.0 |
    | 2000-08-01 23:00:00 |             90.9 |       2.3 |              1017.0 |              0.0 |                      0.0 |             0.0 |           16.4 |           18.941667 |     1.84366 |         1.185687 |          2.3 |             82.379167 |                   4.5 |                          15.6 |                 18.68084 |                     21.928555 |                      1.190065 |                           1.369047 |            16.980884 |                 18.064561 |    1000.019116 |   1.215845 |           0.2 |             40.869565 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                   0.0 |                 140.006667 |                 15.986463 |   -15.986463 |        124.020204 |          3.0 |                         0.027695 |              0.0 |                0.027695 |                    0.0 |

hourly simulation, water
________________________

In contrast, the Penman equation applied for water areas uses only aggregated input, so
its evaporation estimates show a more pronounced delay and no diurnal pattern:

.. integration-test::

    >>> interception(False)
    >>> soil(False)
    >>> water(True)
    >>> test()
    |                date | relativehumidity | windspeed | atmosphericpressure | sunshineduration | possiblesunshineduration | globalradiation | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-01 00:00:00 |             95.1 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.9 |           17.279167 |    0.641273 |         1.605886 |          0.8 |             85.883333 |                   1.3 |                          15.7 |                19.284227 |                     19.753091 |                      1.223615 |                           1.249589 |              18.3393 |                 16.964613 |       996.6607 |    1.21073 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.408237 |   -10.408237 |         98.855096 |          0.0 |                              0.0 |         0.106048 |                     0.0 |                    0.0 |
    | 2000-08-01 01:00:00 |             94.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.6 |           17.241667 |    0.641273 |         1.603439 |          0.8 |             85.991667 |                   1.3 |                          15.7 |                18.920184 |                      19.70628 |                       1.20339 |                           1.246999 |            17.955254 |                 16.945759 |     997.044746 |   1.212158 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                  10.41572 |    -10.41572 |         98.847613 |          0.0 |                              0.0 |         0.105867 |                     0.0 |                    0.0 |
    | 2000-08-01 02:00:00 |             95.9 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.4 |              17.175 |    0.641273 |         1.575992 |          0.8 |             86.233333 |                   1.3 |                          15.7 |                 18.68084 |                       19.6233 |                      1.190065 |                           1.242407 |            17.914926 |                 16.921826 |     997.085074 |   1.213014 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.421627 |   -10.421627 |         98.841706 |          0.0 |                              0.0 |         0.105429 |                     0.0 |                    0.0 |
    | 2000-08-01 03:00:00 |             96.7 |       0.8 |              1015.0 |              0.0 |                      0.0 |             0.0 |           16.3 |             17.0625 |    0.641273 |         1.548545 |          0.8 |             86.708333 |                   1.3 |                          15.5 |                18.562165 |                     19.483964 |                      1.183449 |                            1.23469 |            17.949613 |                  16.89422 |     997.050387 |   1.213417 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.455184 |   -10.455184 |          98.80815 |          0.0 |                              0.0 |         0.104692 |                     0.0 |                    0.0 |
    | 2000-08-01 04:00:00 |             97.2 |       0.8 |              1015.0 |              0.0 |                      0.4 |             1.9 |           16.0 |           16.908333 |    0.641273 |         1.504432 |          0.8 |             87.366667 |                   1.3 |                          14.9 |                18.210086 |                     19.294427 |                      1.163788 |                           1.224181 |            17.700204 |                 16.856897 |     997.299796 |    1.21479 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |                135.5 |                  1.52 |                      108.4 |                 10.560684 |    -9.040684 |         97.839316 |          0.0 |                              0.0 |         0.102791 |                     0.0 |                    0.0 |
    | 2000-08-01 05:00:00 |             97.5 |       0.6 |              1015.0 |              0.0 |                      1.0 |            21.9 |           15.9 |           16.729167 |    0.480955 |         1.453638 |          0.6 |             88.204167 |                   1.3 |                          14.9 |                18.094032 |                     19.076181 |                      1.157296 |                           1.212063 |            17.641681 |                 16.825987 |     997.358319 |   1.215237 |           0.2 |            156.666667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           134.095833 |                 17.52 |                 107.276667 |                 10.550629 |     6.969371 |         96.726038 |          0.0 |                              0.0 |         0.100573 |                     0.0 |                    0.0 |
    | 2000-08-01 06:00:00 |             97.7 |       0.9 |              1015.0 |              0.0 |                      1.0 |            57.3 |           16.0 |           16.533333 |    0.721432 |         1.392031 |          0.9 |             89.191667 |                   1.3 |                          14.9 |                18.210086 |                     18.840106 |                      1.163788 |                           1.198935 |            17.791254 |                 16.803805 |     997.208746 |   1.214748 |           0.2 |            104.444444 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           131.854167 |                 45.84 |                 105.483333 |                 10.530586 |    35.309414 |         94.952747 |          0.0 |                              0.0 |         0.097594 |                     0.0 |                    0.0 |
    | 2000-08-01 07:00:00 |             97.4 |       0.9 |              1015.0 |              0.0 |                      1.0 |           109.3 |           16.6 |              16.375 |    0.721432 |         1.334591 |          0.9 |                90.125 |                   1.3 |                          14.9 |                18.920184 |                     18.651109 |                       1.20339 |                           1.188408 |            18.428259 |                 16.809312 |     996.571741 |   1.211943 |           0.2 |            104.444444 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             129.4625 |                 87.44 |                     103.57 |                 10.496138 |    76.943862 |         93.073862 |          0.0 |                              0.0 |         0.094689 |                     0.0 |                    0.0 |
    | 2000-08-01 08:00:00 |             96.8 |       0.9 |              1016.0 |              0.0 |                      1.0 |           170.9 |           17.4 |           16.216667 |    0.721432 |         1.260484 |          0.9 |                91.275 |                   1.3 |                          14.9 |                19.904589 |                     18.463773 |                      1.257963 |                           1.177959 |            19.267642 |                 16.852809 |     996.732358 |   1.209425 |           0.2 |            104.444444 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |              127.325 |                136.72 |                     101.86 |                 10.432293 |   126.287707 |         91.427707 |          0.0 |                              0.0 |         0.091861 |                     0.0 |                    0.0 |
    | 2000-08-01 09:00:00 |             86.1 |       1.3 |              1016.0 |              0.2 |                      1.0 |           311.8 |           19.0 |             16.1125 |    1.042069 |         1.203904 |          1.3 |             91.991667 |                   1.5 |                          14.9 |                22.008543 |                     18.341425 |                      1.373407 |                           1.171128 |            18.949356 |                 16.872582 |     997.050644 |   1.202945 |           0.2 |             72.307692 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |                129.9 |                249.44 |                     103.92 |                 10.811102 |   238.628898 |         93.108898 |          0.0 |                              0.0 |         0.092637 |                     0.0 |                    0.0 |
    | 2000-08-01 10:00:00 |             76.8 |       1.5 |              1016.0 |              0.5 |                      1.0 |           501.6 |           20.3 |           16.083333 |    1.202387 |         1.149836 |          1.5 |             92.241667 |                   1.7 |                          14.9 |                23.858503 |                     18.307295 |                      1.473678 |                           1.169221 |             18.32333 |                 16.886954 |      997.67667 |   1.197896 |           0.2 |             62.666667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           132.283333 |                401.28 |                 105.826667 |                 11.206987 |   390.073013 |          94.61968 |          0.0 |                              0.0 |         0.093723 |                     0.0 |                    0.0 |
    | 2000-08-01 11:00:00 |             71.8 |       1.2 |              1016.0 |              0.7 |                      1.0 |           615.0 |           21.4 |              16.125 |    0.961909 |         1.089916 |          1.2 |             92.104167 |                   2.2 |                          14.9 |                25.528421 |                     18.356069 |                      1.563281 |                           1.171946 |            18.329406 |                 16.906704 |     997.670594 |    1.19342 |           0.2 |             78.333333 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           135.916667 |                 492.0 |                 108.733333 |                 12.231168 |   479.768832 |         96.502165 |          0.0 |                              0.0 |         0.095536 |                     0.0 |                    0.0 |
    | 2000-08-01 12:00:00 |             67.5 |       1.3 |              1016.0 |              0.8 |                      1.0 |           626.5 |           21.3 |           16.204167 |    1.042069 |         1.037502 |          1.3 |             91.729167 |                   2.8 |                          14.9 |                 25.37251 |                     18.449053 |                       1.55495 |                           1.177138 |            17.126444 |                 16.923163 |     998.873556 |   1.194363 |           0.2 |             72.307692 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           145.816667 |                 501.2 |                 116.653333 |                 13.472648 |   487.727352 |        103.180685 |          0.0 |                              0.0 |         0.102091 |                     0.0 |                    0.0 |
    | 2000-08-01 13:00:00 |             66.1 |       1.5 |              1016.0 |              0.5 |                      1.0 |           496.1 |           21.8 |           16.329167 |    1.202387 |         1.012602 |          1.5 |             91.104167 |                   3.2 |                          14.9 |                26.160453 |                      18.59671 |                      1.596982 |                           1.185375 |             17.29206 |                 16.942378 |      998.70794 |   1.192265 |           0.2 |             62.666667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |                152.6 |                396.88 |                     122.08 |                 14.310598 |   382.569402 |        107.769402 |          0.0 |                              0.0 |         0.107006 |                     0.0 |                    0.0 |
    | 2000-08-01 14:00:00 |             63.4 |       1.9 |              1016.0 |              0.4 |                      1.0 |           419.5 |           22.9 |           16.545833 |    1.523023 |         0.984394 |          1.9 |             90.058333 |                   3.4 |                          14.9 |                27.969419 |                     18.855098 |                      1.692831 |                           1.199769 |            17.732611 |                 16.980587 |     998.267389 |   1.187639 |           0.2 |             49.473684 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           157.345833 |                 335.6 |                 125.876667 |                 14.740009 |   320.859991 |        111.136658 |          0.0 |                              0.0 |         0.111239 |                     0.0 |                    0.0 |
    | 2000-08-01 15:00:00 |             62.4 |       1.9 |              1016.0 |              0.5 |                      1.0 |           387.9 |           22.7 |           16.816667 |    1.523023 |         0.968687 |          1.9 |             88.816667 |                   3.8 |                          14.9 |                27.632633 |                     19.182495 |                      1.675052 |                           1.217969 |            17.242763 |                 17.037252 |     998.757237 |    1.18866 |           0.2 |             49.473684 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |               164.25 |                310.32 |                      131.4 |                 15.578473 |   294.741527 |        115.821527 |          0.0 |                              0.0 |         0.117023 |                     0.0 |                    0.0 |
    | 2000-08-01 16:00:00 |             61.1 |       2.3 |              1016.0 |              0.5 |                      1.0 |           278.5 |           22.5 |             17.1375 |     1.84366 |         0.991339 |          2.3 |             87.333333 |                   4.1 |                          14.9 |                27.299387 |                     19.576758 |                      1.657431 |                            1.23983 |            16.679926 |                 17.097035 |     999.320074 |   1.189715 |           0.2 |             40.869565 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           170.066667 |                 222.8 |                 136.053333 |                 16.221893 |   206.578107 |         119.83144 |          0.0 |                              0.0 |         0.122604 |                     0.0 |                    0.0 |
    | 2000-08-01 17:00:00 |             62.1 |       2.4 |              1016.0 |              0.3 |                      1.0 |           137.1 |           21.9 |             17.4875 |    1.923819 |         1.017332 |          2.4 |                85.875 |                   4.4 |                          14.9 |                26.320577 |                     20.014927 |                      1.605502 |                           1.264057 |            16.345078 |                 17.187818 |     999.654922 |   1.192283 |           0.2 |             39.166667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             173.4625 |                109.68 |                     138.77 |                 16.837082 |    92.842918 |        121.932918 |          0.0 |                              0.0 |         0.126492 |                     0.0 |                    0.0 |
    | 2000-08-01 18:00:00 |             67.0 |       2.5 |              1016.0 |              0.1 |                      1.0 |            51.1 |           21.4 |             17.8375 |    2.003978 |         1.054998 |          2.5 |             84.620833 |                   4.5 |                          14.9 |                25.528421 |                     20.461645 |                      1.563281 |                           1.288683 |            17.104042 |                 17.314814 |     998.895958 |   1.193968 |           0.2 |                  37.6 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           174.433333 |                 40.88 |                 139.546667 |                 16.991532 |    23.888468 |        122.555135 |          0.0 |                              0.0 |          0.12892 |                     0.0 |                    0.0 |
    | 2000-08-01 19:00:00 |             74.5 |       2.5 |              1016.0 |              0.0 |                      1.0 |            13.6 |           20.7 |           18.170833 |    2.003978 |         1.100997 |          2.5 |                  83.7 |                   4.5 |                          15.4 |                24.454368 |                     20.895167 |                      1.505746 |                           1.312512 |            18.218504 |                 17.489255 |     997.781496 |   1.196313 |           0.2 |                  37.6 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |                175.0 |                 10.88 |                      140.0 |                 16.573988 |    -5.693988 |        123.426012 |          0.0 |                              0.0 |         0.131406 |                     0.0 |                    0.0 |
    | 2000-08-01 20:00:00 |             81.2 |       2.2 |              1016.0 |              0.0 |                      0.2 |             0.2 |           19.4 |           18.454167 |    1.763501 |         1.120309 |          2.2 |             83.066667 |                   4.5 |                          15.6 |                22.563931 |                      21.26995 |                      1.403627 |                           1.333058 |            18.321912 |                 17.668238 |     997.678088 |   1.201582 |           0.2 |             42.727273 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                  0.16 |                 140.006667 |                 16.324471 |   -16.164471 |        123.682196 |          0.0 |                              0.0 |         0.132882 |                     0.0 |                    0.0 |
    | 2000-08-01 21:00:00 |             86.9 |       1.7 |              1016.0 |              0.0 |                      0.0 |             0.0 |           17.8 |               18.65 |    1.362705 |         1.127089 |          1.7 |               82.7375 |                   4.5 |                          15.6 |                20.413369 |                     21.532411 |                      1.286025 |                           1.347418 |            17.739217 |                 17.815378 |     998.260783 |   1.208454 |           0.2 |             55.294118 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                   0.0 |                 140.006667 |                 16.202924 |   -16.202924 |        123.803743 |          0.0 |                              0.0 |         0.133747 |                     0.0 |                    0.0 |
    | 2000-08-01 22:00:00 |             90.1 |       1.7 |              1017.0 |              0.0 |                      0.0 |             0.0 |           17.0 |           18.808333 |    1.362705 |         1.142201 |          1.7 |             82.554167 |                   4.5 |                          15.6 |                19.406929 |                     21.746678 |                      1.230421 |                           1.359123 |            17.485643 |                 17.952788 |     999.514357 |   1.213101 |           0.2 |             55.294118 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                   0.0 |                 140.006667 |                  16.08262 |    -16.08262 |        123.924047 |          0.0 |                              0.0 |         0.134459 |                     0.0 |                    0.0 |
    | 2000-08-01 23:00:00 |             90.9 |       2.3 |              1017.0 |              0.0 |                      0.0 |             0.0 |           16.4 |           18.941667 |     1.84366 |         1.185687 |          2.3 |             82.379167 |                   4.5 |                          15.6 |                 18.68084 |                     21.928555 |                      1.190065 |                           1.369047 |            16.980884 |                 18.064561 |    1000.019116 |   1.215845 |           0.2 |             40.869565 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |           175.008333 |                   0.0 |                 140.006667 |                 15.986463 |   -15.986463 |        124.020204 |          0.0 |                              0.0 |         0.135221 |                     0.0 |                    0.0 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2B,
    evap_model.Main_IntercModel_V1,
    evap_model.Main_SoilWaterModel_V1,
    evap_model.Main_SnowCoverModel_V1,
    evap_model.Main_SnowyCanopyModel_V1,
    evap_model.Main_SnowAlbedoModel_V1,
    evap_model.Sub_AETModel_V1,
):
    """A MORECS version of HydPy-Evap with some modifications according to LARSIM."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V2,
        evap_model.Determine_SoilEvapotranspiration_V3,
        evap_model.Determine_WaterEvaporation_V3,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V2,
        evap_model.Determine_SoilEvapotranspiration_V3,
        evap_model.Determine_WaterEvaporation_V3,
        evap_model.Get_WaterEvaporation_V1,
        evap_model.Get_InterceptionEvaporation_V1,
        evap_model.Get_SoilEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_AirTemperature_V1,
        evap_model.Update_LoggedAirTemperature_V1,
        evap_model.Calc_DailyAirTemperature_V1,
        evap_model.Return_AdjustedWindSpeed_V1,
        evap_model.Calc_WindSpeed2m_V2,
        evap_model.Update_LoggedWindSpeed2m_V1,
        evap_model.Calc_DailyWindSpeed2m_V1,
        evap_model.Calc_WindSpeed10m_V1,
        evap_model.Update_LoggedRelativeHumidity_V1,
        evap_model.Calc_DailyRelativeHumidity_V1,
        evap_model.Return_SaturationVapourPressure_V1,
        evap_model.Calc_SaturationVapourPressure_V2,
        evap_model.Calc_DailySaturationVapourPressure_V1,
        evap_model.Return_SaturationVapourPressureSlope_V1,
        evap_model.Calc_SaturationVapourPressureSlope_V2,
        evap_model.Calc_DailySaturationVapourPressureSlope_V1,
        evap_model.Calc_ActualVapourPressure_V1,
        evap_model.Calc_DryAirPressure_V1,
        evap_model.Calc_AirDensity_V1,
        evap_model.Calc_DailyActualVapourPressure_V1,
        evap_model.Update_LoggedSunshineDuration_V1,
        evap_model.Calc_DailySunshineDuration_V1,
        evap_model.Update_LoggedPossibleSunshineDuration_V1,
        evap_model.Calc_DailyPossibleSunshineDuration_V1,
        evap_model.Update_LoggedGlobalRadiation_V1,
        evap_model.Calc_DailyGlobalRadiation_V1,
        evap_model.Calc_CurrentAlbedo_V1,
        evap_model.Calc_NetShortwaveRadiation_V2,
        evap_model.Calc_DailyNetShortwaveRadiation_V1,
        evap_model.Calc_DailyNetLongwaveRadiation_V1,
        evap_model.Calc_NetRadiation_V2,
        evap_model.Calc_DailyNetRadiation_V1,
        evap_model.Calc_AerodynamicResistance_V1,
        evap_model.Calc_SoilSurfaceResistance_V1,
        evap_model.Calc_LanduseSurfaceResistance_V1,
        evap_model.Calc_ActualSurfaceResistance_V1,
        evap_model.Calc_InterceptedWater_V1,
        evap_model.Calc_SnowyCanopy_V1,
        evap_model.Return_Evaporation_PenmanMonteith_V1,
        evap_model.Calc_InterceptionEvaporation_V2,
        evap_model.Calc_SoilWater_V1,
        evap_model.Calc_SnowCover_V1,
        evap_model.Calc_SoilHeatFlux_V3,
        evap_model.Calc_SoilEvapotranspiration_V3,
        evap_model.Update_SoilEvapotranspiration_V3,
        evap_model.Calc_WaterEvaporation_V3,
        evap_model.Calc_AirTemperature_TempModel_V1,
        evap_model.Calc_AirTemperature_TempModel_V2,
        evap_model.Calc_InterceptedWater_IntercModel_V1,
        evap_model.Calc_SoilWater_SoilWaterModel_V1,
        evap_model.Calc_SnowCover_SnowCoverModel_V1,
        evap_model.Calc_SnowyCanopy_SnowyCanopyModel_V1,
        evap_model.Calc_CurrentAlbedo_SnowAlbedoModel_V1,
        evap_model.Calc_PotentialInterceptionEvaporation_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        stateinterfaces.IntercModel_V1,
        stateinterfaces.SoilWaterModel_V1,
        stateinterfaces.SnowCoverModel_V1,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    intercmodel = modeltools.SubmodelProperty(stateinterfaces.IntercModel_V1)
    soilwatermodel = modeltools.SubmodelProperty(stateinterfaces.SoilWaterModel_V1)
    snowcovermodel = modeltools.SubmodelProperty(stateinterfaces.SnowCoverModel_V1)
    snowycanopymodel = modeltools.SubmodelProperty(
        stateinterfaces.SnowyCanopyModel_V1, optional=True
    )
    snowalbedomodel = modeltools.SubmodelProperty(
        stateinterfaces.SnowAlbedoModel_V1, optional=True
    )


tester = Tester()
cythonizer = Cythonizer()
