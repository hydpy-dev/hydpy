# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""
|evap_aet_morsim| is a submodel that supplies its main model with estimates of
evapotranspiration from soils and evaporation from interception storages and water
areas.  It  implements the MORECS equations :cite:p:`ref-Thompson1981` for calculating
actual evapotranspiration with some modifications following the LARSIM model
:cite:p:`ref-LARSIM`.

The following list summarises its main components:

 * Evaporation from water surfaces after Penman :cite:p:`ref-Penman1948`.
 * Interception evaporation after Penman-Monteith, assuming zero surface resistance
   :cite:p:`ref-Thompson1981`.
 * Surface roughness after Quast and Böhm :cite:p:`ref-Quast1997`
 * "Potential" evapotranspiration from soils after Penman-Monteith
   :cite:p:`ref-Thompson1981`.
 * "Actual" evapotranspiration from soils after Wigmosta :cite:p:`ref-Wigmosta1994`.

|evap_aet_morsim| requires additional data about the catchment's current state, which it
usually queries from its main model, if possible:

 * The current air temperature (required).
 * The amount of intercepted water (required).
 * The soil water content (required).
 * The snow cover degree (required).
 * The current snow albedo (optional).
 * The snow cover degree within the canopy of tree-like vegetation (optional).

The last two data types are optional.  Hence, |evap_aet_morsim| works in combination
with models as |hland_v1|, which cannot estimate the current snow albedo and snow
interception.  Then, |evap_aet_morsim| relies on land type-specific albedo values (for
snow-free conditions) and assumes zero snow interception.

The above data is usually supplied by the respective main model but can be supplied by
sub-submodels, too, of which we make use in the following examples to simplify the
necessary configuration.  However, |evap_aet_morsim| also requires radiation-related
data from another model (potential sunshine duration, actual sunshine duration, and
global radiation), for which it generally requires a "real" submodel that complies with
the |RadiationModel_V1| or the |RadiationModel_V4| interface.

Integration tests
=================

.. how_to_understand_integration_tests::

We prepare a simulation period of three days for the first examples:

>>> from hydpy import pub, Timegrid
>>> pub.timegrids = "2000-08-01", "2000-08-04", "1d"

According to the intended usage as a submodel, |evap_aet_morsim| requires no
connections to any nodes.  Hence, assigning a model instance to a blank |Element|
instance is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_aet_morsim import *
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
>>> maxsoilwater(200.0)
>>> soilmoisturelimit(100.0)
>>> soilmoisturelimit(0.5)

We add submodels of type |meteo_temp_io|, |meteo_psun_sun_glob_io|,
|dummy_interceptedwater|, |dummy_soilwater|, |dummy_snowcover|, |dummy_snowalbedo|, and
|dummy_snowycanopy| that supply additional information on the catchment's state instead
of complicating the comparisons by introducing complex main or submodels:

>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     hruarea(1.0)
...     temperatureaddend(0.0)
>>> with model.add_radiationmodel_v4("meteo_psun_sun_glob_io"):
...     pass
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

Now, we can initialise an |IntegrationTest| object:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

The following time-constant meteorological input data will also apply to all
integration tests except those with an hourly simulation step:

>>> inputs.windspeed.series = 2.0
>>> inputs.relativehumidity.series = 80.0
>>> inputs.atmosphericpressure.series = 1000.0
>>> model.tempmodel.sequences.inputs.temperature.series = 15.0
>>> model.radiationmodel.sequences.inputs.sunshineduration.series = 6.0
>>> model.radiationmodel.sequences.inputs.possiblesunshineduration.series = 16.0
>>> model.radiationmodel.sequences.inputs.globalradiation.series = 190.0

The data supplied by the "water content submodels" varies only for the amount of
intercepted water:

>>> model.intercmodel.sequences.inputs.interceptedwater.series = [0.0], [3.0], [6.0]
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 50.0

We set the snow-related data so that |evap_aet_morsim| assumes snow-free conditions for
now:

>>> model.snowcovermodel.sequences.inputs.snowcover.series = 0.0
>>> model.snowycanopymodel.sequences.inputs.snowycanopy.series = 0.0
>>> model.snowalbedomodel.sequences.inputs.snowalbedo.series[:] = nan

.. _evap_aet_morsim_non_tree_vegetation:

non-tree vegetation
___________________

Both interception evaporation and soil evapotranspiration are relevant for hydrological
response units with vegetation:

>>> interception(True)
>>> soil(True)
>>> tree(False)
>>> conifer(False)

The following test results demonstrate the general functioning of |evap_aet_morsim|.
Due to the simulation step of one day, the "daily" averages or sums (e.g.
|DailyAirTemperature|) are equal to their original counterparts (|AirTemperature|).
The last two columns show how the :cite:t:`ref-Wigmosta1994` approach reduces soil
evapotranspiration to prevent too high total evaporation estimates:

.. integration-test::

    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |               2.326858 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |               0.783365 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

.. _evap_aet_morsim_deciduous_trees:

deciduous trees
_______________

|evap_aet_morsim| does not distinguish between non-tree vegetation and deciduous trees
for snow-free conditions.  Hence, without adjusting other model parameters, activating
the |evap_control.Tree| flag while keeping the |evap_control.Conifer| flag disabled
does not change simulation results:

.. integration-test::

    >>> tree(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |               2.326858 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |               0.783365 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

.. _evap_aet_morsim_conifers:

conifers
________

However, |evap_aet_morsim| applies additional equations for coniferous trees as
explained in the documentation on method |Calc_LanduseSurfaceResistance_V1|.  Hence,
also enabling the |evap_control.Conifer| flag causes some differences from the previous
results:

.. integration-test::

    >>> conifer(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               195.475111 |              125.663522 |              0.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |                2.13897 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               195.475111 |              125.663522 |              3.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |               0.720111 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               195.475111 |              125.663522 |              6.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

.. _evap_aet_morsim_bare_soil:

bare soil
_________

If we simulate bare soil by disabling interception evaporation, soil water
evapotranspiration becomes identical for all three days:

.. integration-test::

    >>> interception(False)
    >>> tree(False)
    >>> conifer(False)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                              0.0 |              0.0 |                     0.0 |               2.326858 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                              0.0 |              0.0 |                     0.0 |               2.326858 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                              0.0 |              0.0 |                     0.0 |               2.326858 |

.. _evap_aet_morsim_sealed_surface:

sealed surface
______________

For simulating sealed surfaces, one can disable the |evap_control.Soil| flag:

.. integration-test::

    >>> interception(True)
    >>> soil(False)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              0.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     0.0 |                    0.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              3.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                     3.0 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              6.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          3.0 |                         4.522584 |              0.0 |                4.522584 |                    0.0 |

.. _evap_water_area:

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
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              0.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          0.0 |                              0.0 |          3.17665 |                     0.0 |                    0.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              3.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          0.0 |                              0.0 |          3.17665 |                     0.0 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.2 |                  47.0 |                   nan |                     40.0 |                    40.0 |              6.0 |      50.0 |       0.0 |         0.0 |           190.0 |                190.0 |                 152.0 |                      152.0 |                 23.835187 |   128.164813 |        128.164813 |          0.0 |                              0.0 |          3.17665 |                     0.0 |                    0.0 |

.. _evap_aet_morsim_snow_on_non_tree_vegetation:

snow on non-tree vegetation
___________________________

Next, we show how |evap_aet_morsim| uses external information on the occurrence of snow
to modify its outputs.  Therefore, we set the degree of the snow cover (on the ground)
to one and the snow albedo to 0.8:

>>> water(False)
>>> interception(True)
>>> soil(True)
>>> model.snowcovermodel.sequences.inputs.snowcover.series = 1.0
>>> model.snowalbedomodel.sequences.inputs.snowalbedo.series = 0.8

Now |evap_aet_morsim| uses the given snow albedo instead of the land type-specific
albedo value for snow-free conditions for calculating the net shortwave radiation.
However, this difference is irrelevant for non-tree vegetation, as any appearance of
snow (on the ground) suppresses interception evaporation and soil evapotranspiration
completely:

.. integration-test::

    >>> tree(False)
    >>> conifer(False)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       1.0 |         0.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |                    0.0 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       1.0 |         0.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       1.0 |         0.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |                    0.0 |

.. _evap_aet_morsim_snow_under_tree_canopies:

snow under tree canopies
________________________

In contrast, snow on the ground does not suppress interception evaporation and soil
evapotranspiration for tree-like vegetation:

.. integration-test::

    >>> tree(True)
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       1.0 |         0.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       1.0 |         0.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                2.189754 |                    0.0 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       1.0 |         0.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                2.189754 |                    0.0 |

.. _evap_aet_morsim_snow_in_tree_canopies:

snow in tree canopies
______________________

However, snow interception in the canopy suppresses interception evaporation but not
soil evapotranspiration:

.. integration-test::

    >>> model.snowycanopymodel.sequences.inputs.snowycanopy.series = 1.0
    >>> test()
    |  date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              0.0 |      50.0 |       1.0 |         1.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |
    | 02/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              3.0 |      50.0 |       1.0 |         1.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |
    | 03/08 |             80.0 |       2.0 |              1000.0 |           15.0 |                15.0 |    1.603182 |         1.603182 |          2.0 |                  80.0 |              6.0 |                     16.0 |                   6.0 |                          16.0 |                17.078326 |                     17.078326 |                      1.100236 |                           1.100236 |            13.662661 |                 13.662661 |     986.337339 |   1.202716 |           0.8 |                  47.0 |                 100.0 |               129.672988 |              106.410903 |              6.0 |      50.0 |       1.0 |         1.0 |           190.0 |                190.0 |                  38.0 |                       38.0 |                 23.835187 |    14.164813 |         14.164813 |          3.0 |                         2.189754 |              0.0 |                     0.0 |               1.126623 |

.. _evap_aet_morsim_hourly_simulation_land:

hourly simulation, land
_______________________

For sub-daily step sizes, the averaging and summing mechanisms of |evap_aet_morsim|
come into play.  To demonstrate this, we prepare a simulation period of 24 hours:

>>> pub.timegrids = "2000-08-03", "2000-08-04", "1h"

We need to restore the values of all time-dependent parameters:

>>> for parameter in model.parameters.fixed:
...     parameter.restore()

This time, we prefer to let |meteo_glob_morsim| calculate the possible sunshine
duration, the actual sunshine duration, and the global radiation on the fly instead of
inserting pre-calculated values via |meteo_psun_sun_glob_io|.  The following
configuration agrees with the :ref:`lland_v3_acker_summer_hourly` example of
|lland_v3|:

>>> with model.add_radiationmodel_v1("meteo_glob_morsim"):
...     latitude(54.1)
...     longitude(9.7)
...     angstromconstant(0.25)
...     angstromfactor(0.5)
...     angstromalternative(0.15)

>>> test = IntegrationTest(element)

The following meteorological input data also stems from the
:ref:`lland_v3_acker_summer_hourly` example of |lland_v3|, too:

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

|evap_aet_morsim| calculates "daily" averages and sums based on the last 24 hours.
Hence, we must provide the corresponding logged data for the 24 hours preceding the
simulation period.  We take them from the :ref:`lland_v3_acker_summer_hourly` example,
too:

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
...       2.5, 2.1, 2.2, 1.7, 1.7, 1.3, 1.3, 0.7, 0.8]),
...     (model.radiationmodel.sequences.logs.loggedunadjustedglobalradiation,
...      [0.0, 0.0, 0.0, 0.0, 0.0, 27.777778, 55.555556, 138.888889, 222.222222,
...       305.555556, 333.333333, 388.888889, 527.777778, 444.444444, 250.0,
...       222.222222, 166.666667, 111.111111, 55.555556, 27.777778, 0.0, 0.0, 0.0,
...       0.0]))

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

    >>> test("evap_aet_morsim_hourly_simulation_land",
    ...      axis1=(fluxes.potentialinterceptionevaporation,
    ...             fluxes.interceptionevaporation, fluxes.soilevapotranspiration))
    |                date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-03 00:00:00 |             95.1 |       0.8 |              1015.0 |           16.9 |           17.279167 |    0.641273 |         1.605886 |          0.8 |             85.883333 |              0.0 |                      0.0 |                   1.3 |                          15.7 |                19.284227 |                     19.753091 |                      1.223615 |                           1.249589 |              18.3393 |                 16.964613 |       996.6607 |    1.21073 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.408237 |   -10.408237 |         98.855096 |          3.0 |                        -0.001093 |              0.0 |               -0.001093 |                    0.0 |
    | 2000-08-03 01:00:00 |             94.9 |       0.8 |              1015.0 |           16.6 |           17.241667 |    0.641273 |         1.603439 |          0.8 |             85.991667 |              0.0 |                      0.0 |                   1.3 |                          15.7 |                18.920184 |                      19.70628 |                       1.20339 |                           1.246999 |            17.955254 |                 16.945759 |     997.044746 |   1.212158 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                  10.41572 |    -10.41572 |         98.847613 |          3.0 |                        -0.000723 |              0.0 |               -0.000723 |                    0.0 |
    | 2000-08-03 02:00:00 |             95.9 |       0.8 |              1015.0 |           16.4 |              17.175 |    0.641273 |         1.575992 |          0.8 |             86.233333 |              0.0 |                      0.0 |                   1.3 |                          15.7 |                 18.68084 |                       19.6233 |                      1.190065 |                           1.242407 |            17.914926 |                 16.921826 |     997.085074 |   1.213014 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.421627 |   -10.421627 |         98.841706 |          3.0 |                        -0.002702 |              0.0 |               -0.002702 |                    0.0 |
    | 2000-08-03 03:00:00 |             96.7 |       0.8 |              1015.0 |           16.3 |             17.0625 |    0.641273 |         1.548545 |          0.8 |             86.708333 |              0.0 |                      0.0 |                   1.3 |                          15.5 |                18.562165 |                     19.483964 |                      1.183449 |                            1.23469 |            17.949613 |                  16.89422 |     997.050387 |   1.213417 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.455184 |   -10.455184 |          98.80815 |          3.0 |                        -0.004292 |              0.0 |               -0.004292 |                    0.0 |
    | 2000-08-03 04:00:00 |             97.2 |       0.8 |              1015.0 |           16.0 |           16.908333 |    0.641273 |         1.504432 |          0.8 |             87.366667 |              0.0 |                 0.429734 |                   1.3 |                     14.929734 |                18.210086 |                     19.294427 |                      1.163788 |                           1.224181 |            17.700204 |                 16.856897 |     997.299796 |    1.21479 |           0.2 |                 117.5 |                 100.0 |                 48.85611 |                67.19064 |              0.1 |       nan |       0.0 |         0.0 |        1.943686 |            135.50182 |              1.554949 |                 108.401456 |                 10.555242 |    -9.000293 |         97.846214 |          3.0 |                        -0.004094 |              0.0 |               -0.004094 |                    0.0 |
    | 2000-08-03 05:00:00 |             97.5 |       0.6 |              1015.0 |           15.9 |           16.729167 |    0.480955 |         1.453638 |          0.6 |             88.204167 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                18.094032 |                     19.076181 |                      1.157296 |                           1.212063 |            17.641681 |                 16.825987 |     997.358319 |   1.215237 |           0.2 |            156.666667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |       21.932441 |           134.099005 |             17.545953 |                 107.279204 |                 10.545193 |     7.000759 |         96.734011 |          3.0 |                         0.006831 |              0.0 |                0.006831 |                    0.0 |
    | 2000-08-03 06:00:00 |             97.7 |       0.9 |              1015.0 |           16.0 |           16.533333 |    0.721432 |         1.392031 |          0.9 |             89.191667 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                18.210086 |                     18.840106 |                      1.163788 |                           1.198935 |            17.791254 |                 16.803805 |     997.208746 |   1.214748 |           0.2 |            104.444444 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |       57.256187 |           131.855513 |             45.804949 |                  105.48441 |                  10.52516 |    35.279789 |          94.95925 |          3.0 |                         0.030923 |              0.0 |                0.030923 |                    0.0 |
    | 2000-08-03 07:00:00 |             97.4 |       0.9 |              1015.0 |           16.6 |              16.375 |    0.721432 |         1.334591 |          0.9 |                90.125 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                18.920184 |                     18.651109 |                       1.20339 |                           1.188408 |            18.428259 |                 16.809312 |     996.571741 |   1.211943 |           0.2 |            104.444444 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      109.332844 |           129.465215 |             87.466275 |                 103.572172 |                  10.49073 |    76.975545 |         93.081442 |          3.0 |                         0.066103 |              0.0 |                0.066103 |                    0.0 |
    | 2000-08-03 08:00:00 |             96.8 |       0.9 |              1016.0 |           17.4 |           16.216667 |    0.721432 |         1.260484 |          0.9 |                91.275 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                19.904589 |                     18.463773 |                      1.257963 |                           1.177959 |            19.267642 |                 16.852809 |     996.732358 |   1.209425 |           0.2 |            104.444444 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      170.949152 |           127.329763 |            136.759322 |                  101.86381 |                 10.426918 |   126.332404 |         91.436893 |          3.0 |                         0.109745 |              0.0 |                     0.1 |               0.007985 |
    | 2000-08-03 09:00:00 |             86.1 |       1.3 |              1016.0 |           19.0 |             16.1125 |    1.042069 |         1.203904 |          1.3 |             91.991667 |              0.2 |                      1.0 |                   1.5 |                     14.929734 |                22.008543 |                     18.341425 |                      1.373407 |                           1.171128 |            18.949356 |                 16.872582 |     997.050644 |   1.202945 |           0.2 |             72.307692 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      311.762624 |           129.903206 |              249.4101 |                 103.922564 |                 10.804921 |   238.605178 |         93.117643 |          3.0 |                         0.255431 |              0.0 |                     0.1 |               0.120887 |
    | 2000-08-03 10:00:00 |             76.8 |       1.5 |              1016.0 |           20.3 |           16.083333 |    1.202387 |         1.149836 |          1.5 |             92.241667 |              0.5 |                      1.0 |                   1.7 |                     14.929734 |                23.858503 |                     18.307295 |                      1.473678 |                           1.169221 |             18.32333 |                 16.886954 |      997.67667 |   1.197896 |           0.2 |             62.666667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      501.583299 |           132.285843 |            401.266639 |                 105.828674 |                 11.199993 |   390.066647 |         94.628682 |          3.0 |                          0.44655 |              0.0 |                     0.1 |                0.26458 |
    | 2000-08-03 11:00:00 |             71.8 |       1.2 |              1016.0 |           21.4 |              16.125 |    0.961909 |         1.089916 |          1.2 |             92.104167 |              0.7 |                      1.0 |                   2.2 |                     14.929734 |                25.528421 |                     18.356069 |                      1.563281 |                           1.171946 |            18.329406 |                 16.906704 |     997.670594 |    1.19342 |           0.2 |             78.333333 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      615.018727 |           135.919957 |            492.014981 |                 108.735965 |                 12.222123 |   479.792858 |         96.513842 |          3.0 |                         0.533375 |              0.0 |                     0.1 |               0.347357 |
    | 2000-08-03 12:00:00 |             67.5 |       1.3 |              1016.0 |           21.3 |           16.204167 |    1.042069 |         1.037502 |          1.3 |             91.729167 |              0.8 |                      1.0 |                   2.8 |                     14.929734 |                 25.37251 |                     18.449053 |                       1.55495 |                           1.177138 |            17.126444 |                 16.923163 |     998.873556 |   1.194363 |           0.2 |             72.307692 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      626.544326 |           145.821804 |            501.235461 |                 116.657443 |                 13.461134 |   487.774327 |        103.196309 |          3.0 |                         0.563864 |              0.0 |                     0.1 |               0.366516 |
    | 2000-08-03 13:00:00 |             66.1 |       1.5 |              1016.0 |           21.8 |           16.329167 |    1.202387 |         1.012602 |          1.5 |             91.104167 |              0.5 |                      1.0 |                   3.2 |                     14.929734 |                26.160453 |                      18.59671 |                      1.596982 |                           1.185375 |             17.29206 |                 16.942378 |      998.70794 |   1.192265 |           0.2 |             62.666667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      496.133417 |           152.606529 |            396.906734 |                 122.085223 |                 14.297428 |   382.609306 |        107.787796 |          3.0 |                          0.49394 |              0.0 |                     0.1 |                 0.3042 |
    | 2000-08-03 14:00:00 |             63.4 |       1.9 |              1016.0 |           22.9 |           16.545833 |    1.523023 |         0.984394 |          1.9 |             90.058333 |              0.4 |                      1.0 |                   3.4 |                     14.929734 |                27.969419 |                     18.855098 |                      1.692831 |                           1.199769 |            17.732611 |                 16.980587 |     998.267389 |   1.187639 |           0.2 |             49.473684 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      419.520994 |           157.353237 |            335.616795 |                  125.88259 |                 14.726001 |   320.890794 |        111.156589 |          3.0 |                         0.492669 |              0.0 |                     0.1 |               0.291144 |
    | 2000-08-03 15:00:00 |             62.4 |       1.9 |              1016.0 |           22.7 |           16.816667 |    1.523023 |         0.968687 |          1.9 |             88.816667 |              0.5 |                      1.0 |                   3.8 |                     14.929734 |                27.632633 |                     19.182495 |                      1.675052 |                           1.217969 |            17.242763 |                 17.037252 |     998.757237 |    1.18866 |           0.2 |             49.473684 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      387.887354 |           164.256877 |            310.309883 |                 131.405502 |                 15.562805 |   294.747078 |        115.842696 |          3.0 |                         0.469892 |              0.0 |                     0.1 |               0.273775 |
    | 2000-08-03 16:00:00 |             61.1 |       2.3 |              1016.0 |           22.5 |             17.1375 |     1.84366 |         0.991339 |          2.3 |             87.333333 |              0.5 |                      1.0 |                   4.1 |                     14.929734 |                27.299387 |                     19.576758 |                      1.657431 |                            1.23983 |            16.679926 |                 17.097035 |     999.320074 |   1.189715 |           0.2 |             40.869565 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      278.496873 |           170.073414 |            222.797499 |                 136.058731 |                 16.204965 |   206.592533 |        119.853765 |          3.0 |                         0.424272 |              0.0 |                     0.1 |               0.228619 |
    | 2000-08-03 17:00:00 |             62.1 |       2.4 |              1016.0 |           21.9 |             17.4875 |    1.923819 |         1.017332 |          2.4 |                85.875 |              0.3 |                      1.0 |                   4.4 |                     14.929734 |                26.320577 |                     20.014927 |                      1.605502 |                           1.264057 |            16.345078 |                 17.187818 |     999.654922 |   1.192283 |           0.2 |             39.166667 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |      137.138608 |           173.470856 |            109.710886 |                 138.776684 |                 16.818923 |    92.891964 |        121.957762 |          3.0 |                         0.310168 |              0.0 |                     0.1 |               0.145575 |
    | 2000-08-03 18:00:00 |             67.0 |       2.5 |              1016.0 |           21.4 |             17.8375 |    2.003978 |         1.054998 |          2.5 |             84.620833 |              0.1 |                      1.0 |                   4.5 |                     14.929734 |                25.528421 |                     20.461645 |                      1.563281 |                           1.288683 |            17.104042 |                 17.314814 |     998.895958 |   1.193968 |           0.2 |                  37.6 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |       51.080715 |           174.440885 |             40.864572 |                 139.552708 |                 16.973018 |    23.891554 |         122.57969 |          3.0 |                          0.21817 |              0.0 |                     0.1 |                0.08048 |
    | 2000-08-03 19:00:00 |             74.5 |       2.5 |              1016.0 |           20.7 |           18.170833 |    2.003978 |         1.100997 |          2.5 |                  83.7 |              0.0 |                      1.0 |                   4.5 |                     15.429734 |                24.454368 |                     20.895167 |                      1.505746 |                           1.312512 |            18.218504 |                 17.489255 |     997.781496 |   1.196313 |           0.2 |                  37.6 |                 100.0 |                 48.85611 |               53.450591 |              0.1 |       nan |       0.0 |         0.0 |       13.632816 |           175.008919 |             10.906253 |                 140.007135 |                 16.556776 |    -5.650523 |         123.45036 |          3.0 |                         0.141818 |              0.0 |                     0.1 |                0.02826 |
    | 2000-08-03 20:00:00 |             81.2 |       2.2 |              1016.0 |           19.4 |           18.454167 |    1.763501 |         1.120309 |          2.2 |             83.066667 |              0.0 |                   0.1364 |                   4.5 |                     15.566134 |                22.563931 |                      21.26995 |                      1.403627 |                           1.333058 |            18.321912 |                 17.668238 |     997.678088 |   1.201582 |           0.2 |             42.727273 |                 100.0 |                 48.85611 |                 77.4288 |              0.1 |       nan |       0.0 |         0.0 |        0.185943 |           175.016667 |              0.148755 |                 140.013334 |                 16.343497 |   -16.194743 |        123.669836 |          3.0 |                         0.077552 |              0.0 |                0.077552 |                    0.0 |
    | 2000-08-03 21:00:00 |             86.9 |       1.7 |              1016.0 |           17.8 |               18.65 |    1.362705 |         1.127089 |          1.7 |               82.7375 |              0.0 |                      0.0 |                   4.5 |                     15.566134 |                20.413369 |                     21.532411 |                      1.286025 |                           1.347418 |            17.739217 |                 17.815378 |     998.260783 |   1.208454 |           0.2 |             55.294118 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           175.016667 |                   0.0 |                 140.013334 |                 16.221809 |   -16.221809 |        123.791525 |          3.0 |                         0.033573 |              0.0 |                0.033573 |                    0.0 |
    | 2000-08-03 22:00:00 |             90.1 |       1.7 |              1017.0 |           17.0 |           18.808333 |    1.362705 |         1.142201 |          1.7 |             82.554167 |              0.0 |                      0.0 |                   4.5 |                     15.566134 |                19.406929 |                     21.746678 |                      1.230421 |                           1.359123 |            17.485643 |                 17.952788 |     999.514357 |   1.213101 |           0.2 |             55.294118 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           175.016667 |                   0.0 |                 140.013334 |                 16.101364 |   -16.101364 |        123.911969 |          3.0 |                         0.020744 |              0.0 |                0.020744 |                    0.0 |
    | 2000-08-03 23:00:00 |             90.9 |       2.3 |              1017.0 |           16.4 |           18.941667 |     1.84366 |         1.185687 |          2.3 |             82.379167 |              0.0 |                      0.0 |                   4.5 |                     15.566134 |                 18.68084 |                     21.928555 |                      1.190065 |                           1.369047 |            16.980884 |                 18.064561 |    1000.019116 |   1.215845 |           0.2 |             40.869565 |                 100.0 |                 48.85611 |               83.333333 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           175.016667 |                   0.0 |                 140.013334 |                 16.005095 |   -16.005095 |        124.008238 |          3.0 |                         0.027678 |              0.0 |                0.027678 |                    0.0 |

.. _evap_aet_morsim_hourly_simulation_water:

hourly simulation, water
________________________

In contrast, the Penman equation applied for water areas uses only aggregated input, so
its evaporation estimates show a more pronounced delay and no diurnal pattern:

.. integration-test::

    >>> interception(False)
    >>> soil(False)
    >>> water(True)
    >>> test("evap_aet_morsim_hourly_simulation_water", axis1=fluxes.waterevaporation)
    |                date | relativehumidity | windspeed | atmosphericpressure | airtemperature | dailyairtemperature | windspeed2m | dailywindspeed2m | windspeed10m | dailyrelativehumidity | sunshineduration | possiblesunshineduration | dailysunshineduration | dailypossiblesunshineduration | saturationvapourpressure | dailysaturationvapourpressure | saturationvapourpressureslope | dailysaturationvapourpressureslope | actualvapourpressure | dailyactualvapourpressure | dryairpressure | airdensity | currentalbedo | aerodynamicresistance | soilsurfaceresistance | landusesurfaceresistance | actualsurfaceresistance | interceptedwater | soilwater | snowcover | snowycanopy | globalradiation | dailyglobalradiation | netshortwaveradiation | dailynetshortwaveradiation | dailynetlongwaveradiation | netradiation | dailynetradiation | soilheatflux | potentialinterceptionevaporation | waterevaporation | interceptionevaporation | soilevapotranspiration |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-08-03 00:00:00 |             95.1 |       0.8 |              1015.0 |           16.9 |           17.279167 |    0.641273 |         1.605886 |          0.8 |             85.883333 |              0.0 |                      0.0 |                   1.3 |                          15.7 |                19.284227 |                     19.753091 |                      1.223615 |                           1.249589 |              18.3393 |                 16.964613 |       996.6607 |    1.21073 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.408237 |   -10.408237 |         98.855096 |          0.0 |                              0.0 |         0.106048 |                     0.0 |                    0.0 |
    | 2000-08-03 01:00:00 |             94.9 |       0.8 |              1015.0 |           16.6 |           17.241667 |    0.641273 |         1.603439 |          0.8 |             85.991667 |              0.0 |                      0.0 |                   1.3 |                          15.7 |                18.920184 |                      19.70628 |                       1.20339 |                           1.246999 |            17.955254 |                 16.945759 |     997.044746 |   1.212158 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                  10.41572 |    -10.41572 |         98.847613 |          0.0 |                              0.0 |         0.105867 |                     0.0 |                    0.0 |
    | 2000-08-03 02:00:00 |             95.9 |       0.8 |              1015.0 |           16.4 |              17.175 |    0.641273 |         1.575992 |          0.8 |             86.233333 |              0.0 |                      0.0 |                   1.3 |                          15.7 |                 18.68084 |                       19.6233 |                      1.190065 |                           1.242407 |            17.914926 |                 16.921826 |     997.085074 |   1.213014 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.421627 |   -10.421627 |         98.841706 |          0.0 |                              0.0 |         0.105429 |                     0.0 |                    0.0 |
    | 2000-08-03 03:00:00 |             96.7 |       0.8 |              1015.0 |           16.3 |             17.0625 |    0.641273 |         1.548545 |          0.8 |             86.708333 |              0.0 |                      0.0 |                   1.3 |                          15.5 |                18.562165 |                     19.483964 |                      1.183449 |                            1.23469 |            17.949613 |                  16.89422 |     997.050387 |   1.213417 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           136.579167 |                   0.0 |                 109.263333 |                 10.455184 |   -10.455184 |          98.80815 |          0.0 |                              0.0 |         0.104692 |                     0.0 |                    0.0 |
    | 2000-08-03 04:00:00 |             97.2 |       0.8 |              1015.0 |           16.0 |           16.908333 |    0.641273 |         1.504432 |          0.8 |             87.366667 |              0.0 |                 0.429734 |                   1.3 |                     14.929734 |                18.210086 |                     19.294427 |                      1.163788 |                           1.224181 |            17.700204 |                 16.856897 |     997.299796 |    1.21479 |           0.2 |                 117.5 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |        1.943686 |            135.50182 |              1.554949 |                 108.401456 |                 10.555242 |    -9.000293 |         97.846214 |          0.0 |                              0.0 |         0.102797 |                     0.0 |                    0.0 |
    | 2000-08-03 05:00:00 |             97.5 |       0.6 |              1015.0 |           15.9 |           16.729167 |    0.480955 |         1.453638 |          0.6 |             88.204167 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                18.094032 |                     19.076181 |                      1.157296 |                           1.212063 |            17.641681 |                 16.825987 |     997.358319 |   1.215237 |           0.2 |            156.666667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |       21.932441 |           134.099005 |             17.545953 |                 107.279204 |                 10.545193 |     7.000759 |         96.734011 |          0.0 |                              0.0 |          0.10058 |                     0.0 |                    0.0 |
    | 2000-08-03 06:00:00 |             97.7 |       0.9 |              1015.0 |           16.0 |           16.533333 |    0.721432 |         1.392031 |          0.9 |             89.191667 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                18.210086 |                     18.840106 |                      1.163788 |                           1.198935 |            17.791254 |                 16.803805 |     997.208746 |   1.214748 |           0.2 |            104.444444 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |       57.256187 |           131.855513 |             45.804949 |                  105.48441 |                  10.52516 |    35.279789 |          94.95925 |          0.0 |                              0.0 |           0.0976 |                     0.0 |                    0.0 |
    | 2000-08-03 07:00:00 |             97.4 |       0.9 |              1015.0 |           16.6 |              16.375 |    0.721432 |         1.334591 |          0.9 |                90.125 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                18.920184 |                     18.651109 |                       1.20339 |                           1.188408 |            18.428259 |                 16.809312 |     996.571741 |   1.211943 |           0.2 |            104.444444 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      109.332844 |           129.465215 |             87.466275 |                 103.572172 |                  10.49073 |    76.975545 |         93.081442 |          0.0 |                              0.0 |         0.094696 |                     0.0 |                    0.0 |
    | 2000-08-03 08:00:00 |             96.8 |       0.9 |              1016.0 |           17.4 |           16.216667 |    0.721432 |         1.260484 |          0.9 |                91.275 |              0.0 |                      1.0 |                   1.3 |                     14.929734 |                19.904589 |                     18.463773 |                      1.257963 |                           1.177959 |            19.267642 |                 16.852809 |     996.732358 |   1.209425 |           0.2 |            104.444444 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      170.949152 |           127.329763 |            136.759322 |                  101.86381 |                 10.426918 |   126.332404 |         91.436893 |          0.0 |                              0.0 |          0.09187 |                     0.0 |                    0.0 |
    | 2000-08-03 09:00:00 |             86.1 |       1.3 |              1016.0 |           19.0 |             16.1125 |    1.042069 |         1.203904 |          1.3 |             91.991667 |              0.2 |                      1.0 |                   1.5 |                     14.929734 |                22.008543 |                     18.341425 |                      1.373407 |                           1.171128 |            18.949356 |                 16.872582 |     997.050644 |   1.202945 |           0.2 |             72.307692 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      311.762624 |           129.903206 |              249.4101 |                 103.922564 |                 10.804921 |   238.605178 |         93.117643 |          0.0 |                              0.0 |         0.092645 |                     0.0 |                    0.0 |
    | 2000-08-03 10:00:00 |             76.8 |       1.5 |              1016.0 |           20.3 |           16.083333 |    1.202387 |         1.149836 |          1.5 |             92.241667 |              0.5 |                      1.0 |                   1.7 |                     14.929734 |                23.858503 |                     18.307295 |                      1.473678 |                           1.169221 |             18.32333 |                 16.886954 |      997.67667 |   1.197896 |           0.2 |             62.666667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      501.583299 |           132.285843 |            401.266639 |                 105.828674 |                 11.199993 |   390.066647 |         94.628682 |          0.0 |                              0.0 |         0.093731 |                     0.0 |                    0.0 |
    | 2000-08-03 11:00:00 |             71.8 |       1.2 |              1016.0 |           21.4 |              16.125 |    0.961909 |         1.089916 |          1.2 |             92.104167 |              0.7 |                      1.0 |                   2.2 |                     14.929734 |                25.528421 |                     18.356069 |                      1.563281 |                           1.171946 |            18.329406 |                 16.906704 |     997.670594 |    1.19342 |           0.2 |             78.333333 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      615.018727 |           135.919957 |            492.014981 |                 108.735965 |                 12.222123 |   479.792858 |         96.513842 |          0.0 |                              0.0 |         0.095547 |                     0.0 |                    0.0 |
    | 2000-08-03 12:00:00 |             67.5 |       1.3 |              1016.0 |           21.3 |           16.204167 |    1.042069 |         1.037502 |          1.3 |             91.729167 |              0.8 |                      1.0 |                   2.8 |                     14.929734 |                 25.37251 |                     18.449053 |                       1.55495 |                           1.177138 |            17.126444 |                 16.923163 |     998.873556 |   1.194363 |           0.2 |             72.307692 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      626.544326 |           145.821804 |            501.235461 |                 116.657443 |                 13.461134 |   487.774327 |        103.196309 |          0.0 |                              0.0 |         0.102106 |                     0.0 |                    0.0 |
    | 2000-08-03 13:00:00 |             66.1 |       1.5 |              1016.0 |           21.8 |           16.329167 |    1.202387 |         1.012602 |          1.5 |             91.104167 |              0.5 |                      1.0 |                   3.2 |                     14.929734 |                26.160453 |                      18.59671 |                      1.596982 |                           1.185375 |             17.29206 |                 16.942378 |      998.70794 |   1.192265 |           0.2 |             62.666667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      496.133417 |           152.606529 |            396.906734 |                 122.085223 |                 14.297428 |   382.609306 |        107.787796 |          0.0 |                              0.0 |         0.107024 |                     0.0 |                    0.0 |
    | 2000-08-03 14:00:00 |             63.4 |       1.9 |              1016.0 |           22.9 |           16.545833 |    1.523023 |         0.984394 |          1.9 |             90.058333 |              0.4 |                      1.0 |                   3.4 |                     14.929734 |                27.969419 |                     18.855098 |                      1.692831 |                           1.199769 |            17.732611 |                 16.980587 |     998.267389 |   1.187639 |           0.2 |             49.473684 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      419.520994 |           157.353237 |            335.616795 |                  125.88259 |                 14.726001 |   320.890794 |        111.156589 |          0.0 |                              0.0 |         0.111258 |                     0.0 |                    0.0 |
    | 2000-08-03 15:00:00 |             62.4 |       1.9 |              1016.0 |           22.7 |           16.816667 |    1.523023 |         0.968687 |          1.9 |             88.816667 |              0.5 |                      1.0 |                   3.8 |                     14.929734 |                27.632633 |                     19.182495 |                      1.675052 |                           1.217969 |            17.242763 |                 17.037252 |     998.757237 |    1.18866 |           0.2 |             49.473684 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      387.887354 |           164.256877 |            310.309883 |                 131.405502 |                 15.562805 |   294.747078 |        115.842696 |          0.0 |                              0.0 |         0.117043 |                     0.0 |                    0.0 |
    | 2000-08-03 16:00:00 |             61.1 |       2.3 |              1016.0 |           22.5 |             17.1375 |     1.84366 |         0.991339 |          2.3 |             87.333333 |              0.5 |                      1.0 |                   4.1 |                     14.929734 |                27.299387 |                     19.576758 |                      1.657431 |                            1.23983 |            16.679926 |                 17.097035 |     999.320074 |   1.189715 |           0.2 |             40.869565 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      278.496873 |           170.073414 |            222.797499 |                 136.058731 |                 16.204965 |   206.592533 |        119.853765 |          0.0 |                              0.0 |         0.122625 |                     0.0 |                    0.0 |
    | 2000-08-03 17:00:00 |             62.1 |       2.4 |              1016.0 |           21.9 |             17.4875 |    1.923819 |         1.017332 |          2.4 |                85.875 |              0.3 |                      1.0 |                   4.4 |                     14.929734 |                26.320577 |                     20.014927 |                      1.605502 |                           1.264057 |            16.345078 |                 17.187818 |     999.654922 |   1.192283 |           0.2 |             39.166667 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |      137.138608 |           173.470856 |            109.710886 |                 138.776684 |                 16.818923 |    92.891964 |        121.957762 |          0.0 |                              0.0 |         0.126516 |                     0.0 |                    0.0 |
    | 2000-08-03 18:00:00 |             67.0 |       2.5 |              1016.0 |           21.4 |             17.8375 |    2.003978 |         1.054998 |          2.5 |             84.620833 |              0.1 |                      1.0 |                   4.5 |                     14.929734 |                25.528421 |                     20.461645 |                      1.563281 |                           1.288683 |            17.104042 |                 17.314814 |     998.895958 |   1.193968 |           0.2 |                  37.6 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |       51.080715 |           174.440885 |             40.864572 |                 139.552708 |                 16.973018 |    23.891554 |         122.57969 |          0.0 |                              0.0 |         0.128944 |                     0.0 |                    0.0 |
    | 2000-08-03 19:00:00 |             74.5 |       2.5 |              1016.0 |           20.7 |           18.170833 |    2.003978 |         1.100997 |          2.5 |                  83.7 |              0.0 |                      1.0 |                   4.5 |                     15.429734 |                24.454368 |                     20.895167 |                      1.505746 |                           1.312512 |            18.218504 |                 17.489255 |     997.781496 |   1.196313 |           0.2 |                  37.6 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |       13.632816 |           175.008919 |             10.906253 |                 140.007135 |                 16.556776 |    -5.650523 |         123.45036 |          0.0 |                              0.0 |          0.13143 |                     0.0 |                    0.0 |
    | 2000-08-03 20:00:00 |             81.2 |       2.2 |              1016.0 |           19.4 |           18.454167 |    1.763501 |         1.120309 |          2.2 |             83.066667 |              0.0 |                   0.1364 |                   4.5 |                     15.566134 |                22.563931 |                      21.26995 |                      1.403627 |                           1.333058 |            18.321912 |                 17.668238 |     997.678088 |   1.201582 |           0.2 |             42.727273 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |        0.185943 |           175.016667 |              0.148755 |                 140.013334 |                 16.343497 |   -16.194743 |        123.669836 |          0.0 |                              0.0 |         0.132869 |                     0.0 |                    0.0 |
    | 2000-08-03 21:00:00 |             86.9 |       1.7 |              1016.0 |           17.8 |               18.65 |    1.362705 |         1.127089 |          1.7 |               82.7375 |              0.0 |                      0.0 |                   4.5 |                     15.566134 |                20.413369 |                     21.532411 |                      1.286025 |                           1.347418 |            17.739217 |                 17.815378 |     998.260783 |   1.208454 |           0.2 |             55.294118 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           175.016667 |                   0.0 |                 140.013334 |                 16.221809 |   -16.221809 |        123.791525 |          0.0 |                              0.0 |         0.133735 |                     0.0 |                    0.0 |
    | 2000-08-03 22:00:00 |             90.1 |       1.7 |              1017.0 |           17.0 |           18.808333 |    1.362705 |         1.142201 |          1.7 |             82.554167 |              0.0 |                      0.0 |                   4.5 |                     15.566134 |                19.406929 |                     21.746678 |                      1.230421 |                           1.359123 |            17.485643 |                 17.952788 |     999.514357 |   1.213101 |           0.2 |             55.294118 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           175.016667 |                   0.0 |                 140.013334 |                 16.101364 |   -16.101364 |        123.911969 |          0.0 |                              0.0 |         0.134447 |                     0.0 |                    0.0 |
    | 2000-08-03 23:00:00 |             90.9 |       2.3 |              1017.0 |           16.4 |           18.941667 |     1.84366 |         1.185687 |          2.3 |             82.379167 |              0.0 |                      0.0 |                   4.5 |                     15.566134 |                 18.68084 |                     21.928555 |                      1.190065 |                           1.369047 |            16.980884 |                 18.064561 |    1000.019116 |   1.215845 |           0.2 |             40.869565 |                   nan |                     40.0 |                    40.0 |              0.1 |       nan |       0.0 |         0.0 |             0.0 |           175.016667 |                   0.0 |                 140.013334 |                 16.005095 |   -16.005095 |        124.008238 |          0.0 |                              0.0 |         0.135209 |                     0.0 |                    0.0 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import aetinterfaces
from hydpy.interfaces import radiationinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2B,
    evap_model.Main_RadiationModel_V1,
    evap_model.Main_RadiationModel_V4,
    evap_model.Main_IntercModel_V1,
    evap_model.Main_SoilWaterModel_V1,
    evap_model.Main_SnowCoverModel_V1,
    evap_model.Main_SnowyCanopyModel_V1,
    evap_model.Main_SnowAlbedoModel_V1,
    evap_model.Sub_ETModel,
    aetinterfaces.AETModel_V1,
):
    """|evap_aet_morsim.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-AET-MORSIM ",
        description="actual evapotranspiration based on MORECS/LARSIM",
    )

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
        evap_model.Process_RadiationModel_V1,
        evap_model.Calc_PossibleSunshineDuration_V1,
        evap_model.Calc_SunshineDuration_V1,
        evap_model.Calc_GlobalRadiation_V1,
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
        radiationinterfaces.RadiationModel_V1,
        radiationinterfaces.RadiationModel_V4,
        stateinterfaces.SoilWaterModel_V1,
        stateinterfaces.SnowCoverModel_V1,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    radiationmodel = modeltools.SubmodelProperty(
        radiationinterfaces.RadiationModel_V1, radiationinterfaces.RadiationModel_V4
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
