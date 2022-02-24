# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Model for estimating sunshine duration based on global radiation following the FAO
reference evapotranspiration model.

|meteo_v002| is nearly identical with |meteo_v001|, except that it expects
|meteo_inputs.GlobalRadiation| as input and estimates |meteo_factors.SunshineDuration|,
while |meteo_v001| expects |meteo_inputs.SunshineDuration| as input and estimates
|meteo_fluxes.GlobalRadiation|.  Hence, please read the documentation on |meteo_v001|.
The following explanations focus only on the differences between both models.

Integration tests
=================

.. how_to_understand_integration_tests::

We design all integration tests as similar to those of |meteo_v001|.  This time, we
select |meteo_factors.SunshineDuration| and |meteo_factors.PossibleSunshineDuration| as
output sequences:

>>> from hydpy import Element, Node
>>> from hydpy.outputs import meteo_SunshineDuration, meteo_PossibleSunshineDuration
>>> node1 = Node("node1", variable=meteo_SunshineDuration)
>>> node2 = Node("node2", variable=meteo_PossibleSunshineDuration)

>>> from hydpy.models.meteo_v002 import *
>>> parameterstep()
>>> element = Element("element", outputs=(node1, node2))
>>> element.model = model

.. _meteo_v002_daily_simulation:

daily simulation
________________

We repeat the :ref:`meteo_v001_daily_simulation` example of |meteo_v001| but use its
global radiation result as input:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> latitude(50.8)
>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.globalradiation.series = 22.058369

|meteo_v002| calculates the same radiation terms and a sunshine duration of 9.25 h,
which is the input value used in the :ref:`meteo_v001_daily_simulation` example of
|meteo_v001|:

.. integration-test::

    >>> test(update_parameters=False)
    |       date | globalradiation | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | sunshineduration | extraterrestrialradiation | clearskysolarradiation | node1 |     node2 |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |       22.058369 |         0.967121 |         0.394547 |        2.106601 |            nan |                16.093247 |             9.25 |                 41.047408 |              30.785556 |  9.25 | 16.093247 |

.. _meteo_v002_hourly_simulation:

hourly simulation
_________________

We repeat the :ref:`meteo_v001_hourly_simulation` example of |meteo_v001| but use its
global radiation results as input:

>>> pub.options.utcoffset = -60
>>> pub.options.utclongitude = -15
>>> pub.timegrids = "2001-09-30 02:00", "2001-10-01 15:00", "1h"
>>> latitude(16.0 + 0.13 / 60 * 100)
>>> longitude(-16.25)

>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m %H:00"

>>> inputs.globalradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 0.4173717, 1.1815322, 1.8609122, 2.409213,
...     2.7890688, 2.9745931, 2.9531427, 2.7261795, 2.3091706, 1.7305344,
...     1.029704, 0.2889954, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.4238976, 1.2095048, 1.9152821, 2.4919982, 2.8987887,
...     3.1060457, 3.0975622, 2.8717768, 2.4420248)

Again, there is a good agreement with the results of |meteo_v001|:

.. integration-test::

    >>> test("meteo_v002_hourly", update_parameters=False,
    ...      axis1=(factors.sunshineduration, factors.possiblesunshineduration))
    |             date | globalradiation | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | sunshineduration | extraterrestrialradiation | clearskysolarradiation |    node1 |    node2 |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.460182 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 03:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.198383 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 04:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -1.936583 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 05:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -1.674784 |                   0.0248 |              0.0 |                       0.0 |                    0.0 |      0.0 |   0.0248 |
    | 2001-30-09 06:00 |        0.417372 |         0.999717 |        -0.070087 |        1.550377 |      -1.412985 |                      1.0 |              0.8 |                   0.64211 |               0.481583 |      0.8 |      1.0 |
    | 2001-30-09 07:00 |        1.181532 |         0.999717 |        -0.070087 |        1.550377 |      -1.151185 |                      1.0 |              0.8 |                  1.817742 |               1.363306 |      0.8 |      1.0 |
    | 2001-30-09 08:00 |        1.860912 |         0.999717 |        -0.070087 |        1.550377 |      -0.889386 |                      1.0 |              0.8 |                  2.862942 |               2.147206 |      0.8 |      1.0 |
    | 2001-30-09 09:00 |        2.409213 |         0.999717 |        -0.070087 |        1.550377 |      -0.627587 |                      1.0 |              0.8 |                  3.706481 |               2.779861 |      0.8 |      1.0 |
    | 2001-30-09 10:00 |        2.789069 |         0.999717 |        -0.070087 |        1.550377 |      -0.365787 |                      1.0 |              0.8 |                  4.290875 |               3.218156 |      0.8 |      1.0 |
    | 2001-30-09 11:00 |        2.974593 |         0.999717 |        -0.070087 |        1.550377 |      -0.103988 |                      1.0 |              0.8 |                  4.576297 |               3.432223 |      0.8 |      1.0 |
    | 2001-30-09 12:00 |        2.953143 |         0.999717 |        -0.070087 |        1.550377 |       0.157812 |                      1.0 |              0.8 |                  4.543297 |               3.407472 |      0.8 |      1.0 |
    | 2001-30-09 13:00 |         2.72618 |         0.999717 |        -0.070087 |        1.550377 |       0.419611 |                      1.0 |              0.8 |                  4.194122 |               3.145592 |      0.8 |      1.0 |
    | 2001-30-09 14:00 |        2.309171 |         0.999717 |        -0.070087 |        1.550377 |        0.68141 |                      1.0 |              0.8 |                   3.55257 |               2.664428 |      0.8 |      1.0 |
    | 2001-30-09 15:00 |        1.730534 |         0.999717 |        -0.070087 |        1.550377 |        0.94321 |                      1.0 |              0.8 |                  2.662361 |                1.99677 |      0.8 |      1.0 |
    | 2001-30-09 16:00 |        1.029704 |         0.999717 |        -0.070087 |        1.550377 |       1.205009 |                      1.0 |              0.8 |                   1.58416 |                1.18812 |      0.8 |      1.0 |
    | 2001-30-09 17:00 |        0.288995 |         0.999717 |        -0.070087 |        1.550377 |       1.466809 |                 0.819208 |              0.8 |                  0.391446 |               0.293585 |      0.8 | 0.819208 |
    | 2001-30-09 18:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |       1.728608 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 19:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |       1.990407 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 20:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.252207 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 21:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.514006 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 22:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.775806 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 23:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |       3.037605 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-01-10 00:00 |             0.0 |         1.000283 |        -0.076994 |        1.548357 |      -2.982399 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-01-10 01:00 |             0.0 |         1.000283 |        -0.076994 |        1.548357 |        -2.7206 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-01-10 02:00 |             0.0 |         1.000283 |        -0.076994 |        1.548357 |        -2.4588 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-01-10 03:00 |             0.0 |         1.000283 |        -0.076994 |        1.548357 |      -2.197001 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-01-10 04:00 |             0.0 |         1.000283 |        -0.076994 |        1.548357 |      -1.935202 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-01-10 05:00 |             0.0 |         1.000283 |        -0.076994 |        1.548357 |      -1.673402 |                 0.022362 |              0.0 |                       0.0 |                    0.0 |      0.0 | 0.022362 |
    | 2001-01-10 06:00 |        0.423898 |         1.000283 |        -0.076994 |        1.548357 |      -1.411603 |                      1.0 |         0.826667 |                  0.639042 |               0.479281 | 0.826667 |      1.0 |
    | 2001-01-10 07:00 |        1.209505 |         1.000283 |        -0.076994 |        1.548357 |      -1.149804 |                      1.0 |         0.833333 |                  1.814257 |               1.360693 | 0.833333 |      1.0 |
    | 2001-01-10 08:00 |        1.915282 |         1.000283 |        -0.076994 |        1.548357 |      -0.888004 |                      1.0 |             0.84 |                   2.85863 |               2.143972 |     0.84 |      1.0 |
    | 2001-01-10 09:00 |        2.491998 |         1.000283 |        -0.076994 |        1.548357 |      -0.626205 |                      1.0 |         0.846667 |                  3.700987 |               2.775741 | 0.846667 |      1.0 |
    | 2001-01-10 10:00 |        2.898789 |         1.000283 |        -0.076994 |        1.548357 |      -0.364405 |                      1.0 |         0.853333 |                  4.283924 |               3.212943 | 0.853333 |      1.0 |
    | 2001-01-10 11:00 |        3.106046 |         1.000283 |        -0.076994 |        1.548357 |      -0.102606 |                      1.0 |             0.86 |                  4.567714 |               3.425786 |     0.86 |      1.0 |
    | 2001-01-10 12:00 |        3.097562 |         1.000283 |        -0.076994 |        1.548357 |       0.159193 |                      1.0 |         0.866667 |                  4.533018 |               3.399763 | 0.866667 |      1.0 |
    | 2001-01-10 13:00 |        2.871777 |         1.000283 |        -0.076994 |        1.548357 |       0.420993 |                      1.0 |         0.873333 |                  4.182199 |               3.136649 | 0.873333 |      1.0 |
    | 2001-01-10 14:00 |        2.442025 |         1.000283 |        -0.076994 |        1.548357 |       0.682792 |                      1.0 |             0.88 |                  3.539166 |               2.654375 |     0.88 |      1.0 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.models.meteo import meteo_model


class Model(modeltools.AdHocModel):
    """Version 2 of the Meteo model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        meteo_model.Calc_EarthSunDistance_V1,
        meteo_model.Calc_SolarDeclination_V1,
        meteo_model.Calc_SunsetHourAngle_V1,
        meteo_model.Calc_SolarTimeAngle_V1,
        meteo_model.Calc_PossibleSunshineDuration_V1,
        meteo_model.Calc_ExtraterrestrialRadiation_V1,
        meteo_model.Calc_ClearSkySolarRadiation_V1,
        meteo_model.Calc_SunshineDuration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
