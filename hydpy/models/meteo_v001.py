# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Model for calculating radiation terms based on sunshine duration following the FAO
reference evapotranspiration model.

Version 1 of `HydPy-Meteo` follows the guide-line provided by :cite:`ref-Allen1998`.
There are a few differences, but, at least for the following example calculations, they
seem to be of minor importance.  See the documentation on the individual methods for
more detailed information.

|meteo_v001| is tested for daily and hourly simulation time steps.  We are confident 
that it also works fine for steps shorter than one hour.  Applying it on step sizes 
longer one day or between one hour and one day is not advisable (your contributions to 
extend its applicability are welcome, of course).  There is also a geographic 
restriction due to the calculation of the longwave radiation, which fails during polar 
nights (again, contributions are welcome).

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |meteo_v001| calculates multiple meteorological factors hydrological 
models could require.  Many require |GlobalRadiation| for calculating net shortwave 
radiation.  Some also require |PossibleSunshineDuration| or |ClearSkySolarRadiation| to
guess cloudiness for calculating net longwave radiation.  Here, we select
|GlobalRadiation| and |ClearSkySolarRadiation| by importing their globally available
aliases, which we hand over to the |Node| instances `node1` and `node2`:

>>> from hydpy import Element, Node
>>> from hydpy.outputs import meteo_GlobalRadiation, meteo_ClearSkySolarRadiation
>>> node1 = Node("node1", variable=meteo_GlobalRadiation)
>>> node2 = Node("node2", variable=meteo_ClearSkySolarRadiation)

Now we can prepare an instance of |meteo_v001| and assign it to an element connected to 
the prepared nodes:

>>> from hydpy.models.meteo_v001 import *
>>> parameterstep()
>>> element = Element("element", outputs=(node1, node2))
>>> element.model = model

.. _meteo_v001_daily_simulation:

daily simulation
________________

The first example deals with a daily simulation time step.  We calculate the radiation 
terms on 6 July in Uccle (Brussels, Belgium) and take all input data from example 18 of 
:cite:`ref-Allen1998`:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> latitude(50.8)
>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.sunshineduration.series = 9.25

Both for |GlobalRadiation| and |ClearSkySolarRadiation|, the differences to the results
given by :cite:`ref-Allen1998` are less than 1 %:

.. integration-test::

    >>> test(update_parameters=False)
    |       date | sunshineduration | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | extraterrestrialradiation | clearskysolarradiation | globalradiation |     node1 |     node2 |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |             9.25 |         0.967121 |         0.394547 |        2.106601 |            nan |                16.093247 |                 41.047408 |              30.785556 |       22.058369 | 22.058369 | 30.785556 |

.. _meteo_v001_hourly_simulation:

hourly simulation
_________________

The second example deals with an hourly simulation over multiple time steps.  We 
calculate the different radiation terms from 30 September to 1 October in N'Diaye 
(Senegal) and take (or try to derive as good as possible) all parameter and input 
values from example 19 of :cite:`ref-Allen1998`.

Example 19 of :cite:`ref-Allen1998` gives results for the intervals between 2 and 3
o'clock and between 14 and 15 o'clock only.  We assume these clock times refer to
UTC-1:

>>> pub.options.utcoffset = -60
>>> pub.options.utclongitude = -15
>>> pub.timegrids = "2001-09-30 02:00", "2001-10-01 15:00", "1h"
>>> latitude(16.0 + 0.13 / 60 * 100)
>>> longitude(-16.25)

We reuse the Ångström coefficients from the first example:

>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m %H:00"

We set the sunshine duration constantly to 80 % during the first daytime period and
let it linearly increase from 82 % to 88 % in the (incomplete) second daytime period.
The exceedance of the potential sunshine duration during both sunsets does not affect
the results negatively.  At the end of the simulation period, the given sunshine 
duration of 88 % corresponds to a ratio of global radiation and clear sky radiation of 
approximately 0.92, which is an intermediate result of :cite:`ref-Allen1998`:

>>> import numpy
>>> inputs.sunshineduration.series = 0.0
>>> inputs.sunshineduration.series[3:16] = 0.8
>>> inputs.sunshineduration.series[27:] = numpy.linspace(0.82, 0.88, 10)

Again, the calculated |GlobalRadiation| and |ClearSkySolarRadiation| differs 
significantly less than 1 % from the results given by :cite:`ref-Allen1998`:

.. integration-test::

    >>> test("evap_v001_hourly", update_parameters=False,
    ...      axis1=(fluxes.globalradiation, fluxes.clearskysolarradiation))
    |             date | sunshineduration | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | extraterrestrialradiation | clearskysolarradiation | globalradiation |    node1 |    node2 |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.460182 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 03:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.198383 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 04:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |      -1.936583 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 05:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -1.674784 |                   0.0248 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 06:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -1.412985 |                      1.0 |                   0.64211 |               0.481583 |        0.417372 | 0.417372 | 0.481583 |
    | 2001-30-09 07:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -1.151185 |                      1.0 |                  1.817742 |               1.363306 |        1.181532 | 1.181532 | 1.363306 |
    | 2001-30-09 08:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.889386 |                      1.0 |                  2.862942 |               2.147206 |        1.860912 | 1.860912 | 2.147206 |
    | 2001-30-09 09:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.627587 |                      1.0 |                  3.706481 |               2.779861 |        2.409213 | 2.409213 | 2.779861 |
    | 2001-30-09 10:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.365787 |                      1.0 |                  4.290875 |               3.218156 |        2.789069 | 2.789069 | 3.218156 |
    | 2001-30-09 11:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.103988 |                      1.0 |                  4.576297 |               3.432223 |        2.974593 | 2.974593 | 3.432223 |
    | 2001-30-09 12:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       0.157812 |                      1.0 |                  4.543297 |               3.407472 |        2.953143 | 2.953143 | 3.407472 |
    | 2001-30-09 13:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       0.419611 |                      1.0 |                  4.194122 |               3.145592 |         2.72618 |  2.72618 | 3.145592 |
    | 2001-30-09 14:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |        0.68141 |                      1.0 |                   3.55257 |               2.664428 |        2.309171 | 2.309171 | 2.664428 |
    | 2001-30-09 15:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |        0.94321 |                      1.0 |                  2.662361 |                1.99677 |        1.730534 | 1.730534 |  1.99677 |
    | 2001-30-09 16:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       1.205009 |                      1.0 |                   1.58416 |                1.18812 |        1.029704 | 1.029704 |  1.18812 |
    | 2001-30-09 17:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       1.466809 |                 0.819208 |                  0.391446 |               0.293585 |        0.288995 | 0.288995 | 0.293585 |
    | 2001-30-09 18:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       1.728608 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 19:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       1.990407 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 20:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.252207 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 21:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.514006 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 22:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.775806 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-30-09 23:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       3.037605 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 00:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |      -2.982399 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 01:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |        -2.7206 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 02:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |        -2.4588 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 03:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |      -2.197001 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 04:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |      -1.935202 |                      0.0 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 05:00 |             0.82 |         1.000283 |        -0.076994 |        1.548357 |      -1.673402 |                 0.022362 |                       0.0 |                    0.0 |             0.0 |      0.0 |      0.0 |
    | 2001-01-10 06:00 |         0.826667 |         1.000283 |        -0.076994 |        1.548357 |      -1.411603 |                      1.0 |                  0.639042 |               0.479281 |        0.423898 | 0.423898 | 0.479281 |
    | 2001-01-10 07:00 |         0.833333 |         1.000283 |        -0.076994 |        1.548357 |      -1.149804 |                      1.0 |                  1.814257 |               1.360693 |        1.209505 | 1.209505 | 1.360693 |
    | 2001-01-10 08:00 |             0.84 |         1.000283 |        -0.076994 |        1.548357 |      -0.888004 |                      1.0 |                   2.85863 |               2.143972 |        1.915282 | 1.915282 | 2.143972 |
    | 2001-01-10 09:00 |         0.846667 |         1.000283 |        -0.076994 |        1.548357 |      -0.626205 |                      1.0 |                  3.700987 |               2.775741 |        2.491998 | 2.491998 | 2.775741 |
    | 2001-01-10 10:00 |         0.853333 |         1.000283 |        -0.076994 |        1.548357 |      -0.364405 |                      1.0 |                  4.283924 |               3.212943 |        2.898789 | 2.898789 | 3.212943 |
    | 2001-01-10 11:00 |             0.86 |         1.000283 |        -0.076994 |        1.548357 |      -0.102606 |                      1.0 |                  4.567714 |               3.425786 |        3.106046 | 3.106046 | 3.425786 |
    | 2001-01-10 12:00 |         0.866667 |         1.000283 |        -0.076994 |        1.548357 |       0.159193 |                      1.0 |                  4.533018 |               3.399763 |        3.097562 | 3.097562 | 3.399763 |
    | 2001-01-10 13:00 |         0.873333 |         1.000283 |        -0.076994 |        1.548357 |       0.420993 |                      1.0 |                  4.182199 |               3.136649 |        2.871777 | 2.871777 | 3.136649 |
    | 2001-01-10 14:00 |             0.88 |         1.000283 |        -0.076994 |        1.548357 |       0.682792 |                      1.0 |                  3.539166 |               2.654375 |        2.442025 | 2.442025 | 2.654375 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.models.meteo import meteo_model


class Model(modeltools.AdHocModel):
    """Version 1 of the Meteo model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        meteo_model.Calc_EarthSunDistance_V1,
        meteo_model.Calc_SolarDeclination_V1,
        meteo_model.Calc_SunsetHourAngle_V1,
        meteo_model.Calc_SolarTimeAngle_V1,
        meteo_model.Calc_ExtraterrestrialRadiation_V1,
        meteo_model.Calc_PossibleSunshineDuration_V1,
        meteo_model.Calc_ClearSkySolarRadiation_V1,
        meteo_model.Calc_GlobalRadiation_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
