# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Implementation of the FAO reference evapotranspiration model.

.. _`Allen`: http://www.fao.org/3/x0490e/x0490e00.htm

Version 1 of the HydPy-E model (Evap) follows the guide-line provided
by `Allen`_.  There are only a few differences related to different
input data assumptions (given averaged daily values of temperature and
relative humidity instead of maximum and minimum values) and the calculation
of the radiation terms.  However, at least for the following example
calculations, these differences seem to be of minor importance.

|evap_v001| is tested for daily and hourly simulation time steps.  We
are quite confident that it also works fine for steps shorter than one
hour.  Applying it on step sizes longer one day or between one hour and
one day is not advisable (your contributions the extent its applicability
are welcome, of course).  There is also a geographic restriction due to
the calculation of the longwave radiation, which fails during polar nights
(again, contributions are welcome).

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_v001| does not calculate runoff and thus does not
define an outlet sequence.  Hence, we need to manually select an output
sequence, which usually is |ReferenceEvapotranspiration|.  We import
its globally available alias and prepare the corresponding output node:

>>> from hydpy import Element, evap_ReferenceEvapotranspiration, Node
>>> node = Node('node', variable=evap_ReferenceEvapotranspiration)

Now we can prepare an instance of |evap_v001| and assign it to an element
connected to the prepared node:

>>> from hydpy.models.evap_v001 import *
>>> parameterstep()
>>> element = Element('element', outputs=node)
>>> element.model = model

daily simulation
________________

The first example deals with a daily simulation time step.  We calculate
the reference evapotranspiration on 6 July in Uccle (Brussels, Belgium)
and take all parameter and input values from example 18 of `Allen`_:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = '2000-07-06', '2000-07-07', '1d'
>>> latitude(50.8)
>>> measuringheightwindspeed(10.0)
>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = '%Y-%d-%m'

>>> inputs.airtemperature.series = 16.9
>>> inputs.relativehumidity.series = 73.0
>>> inputs.windspeed.series = 10.0*1000./60/60
>>> inputs.sunshineduration.series = 9.25
>>> inputs.atmosphericpressure.series = 100.1

The calculated reference evapotranspiration is about 0.1 mm (3 %) smaller
than the one given by `Allen`_ (This discrepancy is mainly due
to different ways to calculate |SaturationVapourPressure|.  `Allen`_
calculates it both for the minimum and the maximum temperature and average
the results, while |evap_v001| applies the corresponding formula on the
average air temperature directly.  The first approach results in higher
pressure values due to the nonlinearity of the vapour pressure curve.
All other methodical differences show, at least in this example, less
severe impacts.):

.. integration-test::

    >>> test(update_parameters=False)
    |       date | airtemperature | relativehumidity | windspeed | sunshineduration | atmosphericpressure | adjustedwindspeed | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | earthsundistance | solardeclination | sunsethourangle | solartimeangle | extraterrestrialradiation | possiblesunshineduration | clearskysolarradiation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | psychrometricconstant | referenceevapotranspiration |     node |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |             73.0 |  2.777778 |             9.25 |               100.1 |          2.077091 |                 1.925484 |                      0.122113 |             1.405603 |         0.967121 |         0.394547 |        2.106601 |            nan |                 41.047408 |                16.093247 |              30.785556 |       22.058369 |             16.984944 |             3.728238 |    13.256706 |          0.0 |              0.066567 |                    3.749139 | 3.749139 |

hourly simulation
_________________

The second example deals with an hourly simulation over multiple time
steps.  We calculate the reference evapotranspiration from 30 September
to 1 October in N'Diaye (Senegal) and take (or try to derive as good as
possible) all parameter and input values from example 19 of
`Allen`_.

Example 19 of `Allen`_ gives results for the intervals between
2 and 3 o'clock and between 14 and 15 o'clock only.  We assume these
clock times are referring to UTC-1:

>>> pub.options.utcoffset = -60
>>> pub.options.utclongitude = -15
>>> pub.timegrids = '2001-09-30 02:00', '2001-10-01 15:00', '1h'

We reuse the Ångström coefficients from the first example:

>>> latitude(16.0+0.13/60*100)
>>> longitude(-16.25)
>>> measuringheightwindspeed(2.0)
>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> IntegrationTest.plotting_options.activated = [
...     fluxes.referenceevapotranspiration]
>>> test.dateformat = '%Y-%d-%m %H:00'

We set constant input sequence values from the start of the simulation
period to the first interval and interpolate linearly between the first
and the second interval, which is also the end of the simulation period:

>>> import numpy
>>> def interpolate(sequence, value1, value2):
...     sequence.series[:-13] = value1
...     sequence.series[-13:] = numpy.linspace(value1, value2, 13)

>>> interpolate(inputs.airtemperature, 28.0, 38.0)
>>> interpolate(inputs.relativehumidity, 90.0, 52.0)
>>> interpolate(inputs.windspeed, 1.9, 3.3)
>>> interpolate(inputs.atmosphericpressure, 100.1, 100.1)

We define the end value of the sunshine duration in a way that the
relation between global radiation and clear sky radiation is
approximately 0.92, which is an intermediate result of `Allen`_:

>>> interpolate(inputs.sunshineduration, 0.8, 0.88)

To avoid calculating |numpy.nan| values during the night periods within
the first 24 hours, we arbitrarily set the values of both log sequences
to one:

>>> logs.loggedclearskysolarradiation = 1.0
>>> logs.loggedglobalradiation = 1.0

Regarding reference evapotranspiration, the calculated values agree
within the precision given by `Allen`_ (The stronger agreement
compared with the above example is due to the consistent calculation
of the saturation vapour pressure.):

.. integration-test::

    >>> test('evap_v001_hourly', update_parameters=False)
    |             date | airtemperature | relativehumidity | windspeed | sunshineduration | atmosphericpressure | adjustedwindspeed | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | earthsundistance | solardeclination | sunsethourangle | solartimeangle | extraterrestrialradiation | possiblesunshineduration | clearskysolarradiation | globalradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | psychrometricconstant | referenceevapotranspiration |      node |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -2.460182 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |              0.066567 |                   -0.000649 | -0.000649 |
    | 2001-30-09 03:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -2.198383 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |              0.066567 |                   -0.000649 | -0.000649 |
    | 2001-30-09 04:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -1.936583 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |              0.066567 |                   -0.000649 | -0.000649 |
    | 2001-30-09 05:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -1.674784 |                       0.0 |                   0.0248 |                    0.0 |             0.0 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |              0.066567 |                   -0.000649 | -0.000649 |
    | 2001-30-09 06:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -1.412985 |                   0.64211 |                      1.0 |               0.481583 |        0.417372 |              0.321376 |             0.112693 |     0.208683 |     0.020868 |              0.066567 |                    0.069227 |  0.069227 |
    | 2001-30-09 07:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -1.151185 |                  1.817742 |                      1.0 |               1.363306 |        1.181532 |               0.90978 |             0.112693 |     0.797087 |     0.079709 |              0.066567 |                    0.213474 |  0.213474 |
    | 2001-30-09 08:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -0.889386 |                  2.862942 |                      1.0 |               2.147206 |        1.860912 |              1.432902 |             0.112693 |     1.320209 |     0.132021 |              0.066567 |                    0.341718 |  0.341718 |
    | 2001-30-09 09:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -0.627587 |                  3.706481 |                      1.0 |               2.779861 |        2.409213 |              1.855094 |             0.112693 |     1.742401 |      0.17424 |              0.066567 |                    0.445218 |  0.445218 |
    | 2001-30-09 10:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -0.365787 |                  4.290875 |                      1.0 |               3.218156 |        2.789069 |              2.147583 |             0.112693 |      2.03489 |     0.203489 |              0.066567 |                    0.516922 |  0.516922 |
    | 2001-30-09 11:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |      -0.103988 |                  4.576297 |                      1.0 |               3.432223 |        2.974593 |              2.290437 |             0.112693 |     2.177744 |     0.217774 |              0.066567 |                    0.551942 |  0.551942 |
    | 2001-30-09 12:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       0.157812 |                  4.543297 |                      1.0 |               3.407472 |        2.953143 |               2.27392 |             0.112693 |     2.161227 |     0.216123 |              0.066567 |                    0.547893 |  0.547893 |
    | 2001-30-09 13:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       0.419611 |                  4.194122 |                      1.0 |               3.145592 |         2.72618 |              2.099158 |             0.112693 |     1.986465 |     0.198647 |              0.066567 |                     0.50505 |   0.50505 |
    | 2001-30-09 14:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |        0.68141 |                   3.55257 |                      1.0 |               2.664428 |        2.309171 |              1.778061 |             0.112693 |     1.665368 |     0.166537 |              0.066567 |                    0.426333 |  0.426333 |
    | 2001-30-09 15:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |        0.94321 |                  2.662361 |                      1.0 |                1.99677 |        1.730534 |              1.332511 |             0.112693 |     1.219819 |     0.121982 |              0.066567 |                    0.317107 |  0.317107 |
    | 2001-30-09 16:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       1.205009 |                   1.58416 |                      1.0 |                1.18812 |        1.029704 |              0.792872 |             0.112693 |     0.680179 |     0.068018 |              0.066567 |                    0.184814 |  0.184814 |
    | 2001-30-09 17:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       1.466809 |                  0.391446 |                 0.819208 |               0.293585 |        0.288995 |              0.222526 |              0.13453 |     0.087996 |       0.0088 |              0.066567 |                     0.03964 |   0.03964 |
    | 2001-30-09 18:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       1.728608 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.118115 |    -0.118115 |    -0.059058 |              0.066567 |                    0.001981 |  0.001981 |
    | 2001-30-09 19:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       1.990407 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.117514 |    -0.117514 |    -0.058757 |              0.066567 |                    0.002063 |  0.002063 |
    | 2001-30-09 20:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       2.252207 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.116874 |    -0.116874 |    -0.058437 |              0.066567 |                     0.00215 |   0.00215 |
    | 2001-30-09 21:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       2.514006 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.116191 |    -0.116191 |    -0.058096 |              0.066567 |                    0.002243 |  0.002243 |
    | 2001-30-09 22:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       2.775806 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.115462 |    -0.115462 |    -0.057731 |              0.066567 |                    0.002343 |  0.002343 |
    | 2001-30-09 23:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         0.999717 |        -0.070087 |        1.550377 |       3.037605 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |              0.11468 |     -0.11468 |     -0.05734 |              0.066567 |                    0.002449 |  0.002449 |
    | 2001-01-10 00:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         1.000283 |        -0.076994 |        1.548357 |      -2.982399 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.113842 |    -0.113842 |    -0.056921 |              0.066567 |                    0.002563 |  0.002563 |
    | 2001-01-10 01:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         1.000283 |        -0.076994 |        1.548357 |        -2.7206 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.112938 |    -0.112938 |    -0.056469 |              0.066567 |                    0.002686 |  0.002686 |
    | 2001-01-10 02:00 |           28.0 |             90.0 |       1.9 |              0.8 |               100.1 |               1.9 |                  3.77993 |                       0.22008 |             3.401937 |         1.000283 |        -0.076994 |        1.548357 |        -2.4588 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.112938 |    -0.112938 |    -0.056469 |              0.066567 |                    0.002686 |  0.002686 |
    | 2001-01-10 03:00 |      28.833333 |        86.833333 |  2.016667 |         0.806667 |               100.1 |          2.016667 |                 3.967258 |                      0.229543 |             3.444902 |         1.000283 |        -0.076994 |        1.548357 |      -2.197001 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.111924 |    -0.111924 |    -0.055962 |              0.066567 |                    0.010157 |  0.010157 |
    | 2001-01-10 04:00 |      29.666667 |        83.666667 |  2.133333 |         0.813333 |               100.1 |          2.133333 |                 4.162612 |                      0.239345 |             3.482719 |         1.000283 |        -0.076994 |        1.548357 |      -1.935202 |                       0.0 |                      0.0 |                    0.0 |             0.0 |                   0.0 |             0.111156 |    -0.111156 |    -0.055578 |              0.066567 |                    0.018451 |  0.018451 |
    | 2001-01-10 05:00 |           30.5 |             80.5 |      2.25 |             0.82 |               100.1 |              2.25 |                 4.366279 |                      0.249495 |             3.514855 |         1.000283 |        -0.076994 |        1.548357 |      -1.673402 |                       0.0 |                 0.022362 |                    0.0 |             0.0 |                   0.0 |             0.110668 |    -0.110668 |    -0.055334 |              0.066567 |                    0.027586 |  0.027586 |
    | 2001-01-10 06:00 |      31.333333 |        77.333333 |  2.366667 |         0.826667 |               100.1 |          2.366667 |                 4.578554 |                      0.260004 |             3.540749 |         1.000283 |        -0.076994 |        1.548357 |      -1.411603 |                  0.639042 |                      1.0 |               0.479281 |        0.423898 |              0.326401 |             0.113482 |     0.212919 |     0.021292 |              0.066567 |                    0.106473 |  0.106473 |
    | 2001-01-10 07:00 |      32.166667 |        74.166667 |  2.483333 |         0.833333 |               100.1 |          2.483333 |                  4.79974 |                      0.270882 |             3.559807 |         1.000283 |        -0.076994 |        1.548357 |      -1.149804 |                  1.814257 |                      1.0 |               1.360693 |        1.209505 |              0.931319 |             0.114477 |     0.816842 |     0.081684 |              0.066567 |                    0.270383 |  0.270383 |
    | 2001-01-10 08:00 |           33.0 |             71.0 |       2.6 |             0.84 |               100.1 |               2.6 |                 5.030148 |                      0.282137 |             3.571405 |         1.000283 |        -0.076994 |        1.548357 |      -0.888004 |                   2.85863 |                      1.0 |               2.143972 |        1.915282 |              1.474767 |             0.115888 |     1.358879 |     0.135888 |              0.066567 |                    0.421351 |  0.421351 |
    | 2001-01-10 09:00 |      33.833333 |        67.833333 |  2.716667 |         0.846667 |               100.1 |          2.716667 |                 5.270097 |                      0.293782 |             3.574882 |         1.000283 |        -0.076994 |        1.548357 |      -0.626205 |                  3.700987 |                      1.0 |               2.775741 |        2.491998 |              1.918839 |             0.117774 |     1.801064 |     0.180106 |              0.066567 |                     0.54941 |   0.54941 |
    | 2001-01-10 10:00 |      34.666667 |        64.666667 |  2.833333 |         0.853333 |               100.1 |          2.833333 |                 5.519915 |                      0.305825 |             3.569545 |         1.000283 |        -0.076994 |        1.548357 |      -0.364405 |                  4.283924 |                      1.0 |               3.212943 |        2.898789 |              2.232067 |             0.120202 |     2.111865 |     0.211187 |              0.066567 |                    0.646013 |  0.646013 |
    | 2001-01-10 11:00 |           35.5 |             61.5 |      2.95 |             0.86 |               100.1 |              2.95 |                  5.77994 |                      0.318278 |             3.554663 |         1.000283 |        -0.076994 |        1.548357 |      -0.102606 |                  4.567714 |                      1.0 |               3.425786 |        3.106046 |              2.391655 |             0.123243 |     2.268412 |     0.226841 |              0.066567 |                    0.704657 |  0.704657 |
    | 2001-01-10 12:00 |      36.333333 |        58.333333 |  3.066667 |         0.866667 |               100.1 |          3.066667 |                 6.050517 |                      0.331151 |             3.529468 |         1.000283 |        -0.076994 |        1.548357 |       0.159193 |                  4.533018 |                      1.0 |               3.399763 |        3.097562 |              2.385123 |             0.126981 |     2.258142 |     0.225814 |              0.066567 |                    0.721384 |  0.721384 |
    | 2001-01-10 13:00 |      37.166667 |        55.166667 |  3.183333 |         0.873333 |               100.1 |          3.183333 |                 6.332002 |                      0.344456 |             3.493154 |         1.000283 |        -0.076994 |        1.548357 |       0.420993 |                  4.182199 |                      1.0 |               3.136649 |        2.871777 |              2.211268 |             0.131506 |     2.079762 |     0.207976 |              0.066567 |                    0.695112 |  0.695112 |
    | 2001-01-10 14:00 |           38.0 |             52.0 |       3.3 |             0.88 |               100.1 |               3.3 |                 6.624758 |                      0.358203 |             3.444874 |         1.000283 |        -0.076994 |        1.548357 |       0.682792 |                  3.539166 |                      1.0 |               2.654375 |        2.442025 |              1.880359 |             0.136924 |     1.743435 |     0.174343 |              0.066567 |                    0.627771 |  0.627771 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.models.evap import evap_model


class Model(modeltools.AdHocModel):
    """Version 1 of the Evap model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_AdjustedWindSpeed_V1,
        evap_model.Calc_SaturationVapourPressure_V1,
        evap_model.Calc_SaturationVapourPressureSlope_V1,
        evap_model.Calc_ActualVapourPressure_V1,
        evap_model.Calc_EarthSunDistance_V1,
        evap_model.Calc_SolarDeclination_V1,
        evap_model.Calc_SunsetHourAngle_V1,
        evap_model.Calc_SolarTimeAngle_V1,
        evap_model.Calc_ExtraterrestrialRadiation_V1,
        evap_model.Calc_PossibleSunshineDuration_V1,
        evap_model.Calc_ClearSkySolarRadiation_V1,
        evap_model.Update_LoggedClearSkySolarRadiation_V1,
        evap_model.Calc_GlobalRadiation_V1,
        evap_model.Update_LoggedGlobalRadiation_V1,
        evap_model.Calc_NetShortwaveRadiation_V1,
        evap_model.Calc_NetLongwaveRadiation_V1,
        evap_model.Calc_NetRadiation_V1,
        evap_model.Calc_SoilHeatFlux_V1,
        evap_model.Calc_PsychrometricConstant_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
