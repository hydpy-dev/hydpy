# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the FAO reference evapotranspiration model.

Version 1 of the HydPy-E model (Evap) follows the guide-line provided by
:cite:`ref-Allen1998`.  However, there are some differences in input data assumptions
(averaged daily temperature and relative humidity values instead of maximum and minimum
values).  You can use the models of the `HydPy-Meteo` family to "pre-process" some of
the required input data.  A suitable choice for |GlobalRadiation| and
|ClearSkySolarRadiation| might be the application model |evap_v001|, which also follows
the FAO guide-line.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_v001| does not calculate runoff and thus does not define an
outlet sequence.  Hence, we must manually select an output sequence, which is usually
|ReferenceEvapotranspiration|.  We import its globally available alias and prepare the
corresponding output node:

>>> from hydpy import Element, Node
>>> from hydpy.outputs import evap_ReferenceEvapotranspiration
>>> node = Node("node", variable=evap_ReferenceEvapotranspiration)

Now we can prepare an instance of |evap_v001| and assign it to an element connected to
the prepared node:

>>> from hydpy.models.evap_v001 import *
>>> parameterstep()
>>> element = Element("element", outputs=node)
>>> element.model = model

daily simulation
________________

The first example deals with a daily simulation time step.  We calculate the reference
evapotranspiration on 6 July in Uccle (Brussels, Belgium) and take the following
parameter values and input values from example 18 of :cite:`ref-Allen1998`:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> measuringheightwindspeed(10.0)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.airtemperature.series = 16.9
>>> inputs.relativehumidity.series = 73.0
>>> inputs.windspeed.series = 10.0 * 1000.0 / 60 / 60
>>> inputs.atmosphericpressure.series = 1001.0

The following global and clear sky solar radiation values are results of the
:ref:`meteo_v001_daily_simulation` integration test of |meteo_v001| that also
recalculates example 18 of :cite:`ref-Allen1998`:

>>> inputs.globalradiation.series = 22.058369
>>> inputs.clearskysolarradiation.series = 30.785556

The calculated reference evapotranspiration is about 0.1 mm (3 %) smaller than the one
given by :cite:`ref-Allen1998`. This discrepancy is mainly due to different ways to
calculate |SaturationVapourPressure|.  :cite:`ref-Allen1998` estimates it both for the
minimum and maximum temperature and averages the results, while |evap_v001| directly
applies the corresponding formula on the average air temperature.  The first approach
results in higher pressure values due to the nonlinearity of the vapour pressure curve.
All other methodical differences show, at least in this example, less severe impacts:

.. integration-test::

    >>> test()
    |       date | airtemperature | relativehumidity | windspeed | atmosphericpressure | globalradiation | clearskysolarradiation | adjustedwindspeed | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | psychrometricconstant | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | referenceevapotranspiration |     node |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |             73.0 |  2.777778 |              1001.0 |       22.058369 |              30.785556 |          2.077091 |                19.254836 |                      1.221127 |             14.05603 |              0.665665 |             16.984944 |             3.728238 |    13.256706 |          0.0 |                    3.749139 | 3.749139 |

hourly simulation
_________________

The second example deals with an hourly simulation over multiple time steps.  We
calculate the reference evapotranspiration from 30 September to 1 October in N'Diaye
(Senegal) and take (or try to derive as good as possible) all parameter and input
values from example 19 of `FAO`:

>>> measuringheightwindspeed(2.0)

Example 19 of :cite:`ref-Allen1998` gives results for the intervals between 2 and 3
o'clock and between 14 and 15 o'clock only.  We assume these clock times are referring
to UTC-1:

>>> pub.options.utcoffset = -60
>>> pub.options.utclongitude = -15
>>> pub.timegrids = "2001-09-30 02:00", "2001-10-01 15:00", "1h"

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m %H:00"

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
>>> interpolate(inputs.atmosphericpressure, 1001.0, 1001.0)

We again take global and clear sky solar radiation from |meteo_v001|, that recalculates
example 19 of :cite:`ref-Allen1998` in its :ref:`meteo_v001_hourly_simulation`
integration test:

>>> inputs.globalradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 0.41737167, 1.18153219, 1.86091215, 2.40921295, 2.78906879,
...     2.97459311, 2.95314275, 2.72617951, 2.30917055, 1.73053436, 1.02970403,
...     0.28899543, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0,
...     0.42389756, 1.20950485, 1.91528208, 2.49199816, 2.8987887, 3.10604571,
...     3.09756215, 2.87177681, 2.44202477)
>>> inputs.clearskysolarradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 0.4815827, 1.36330637, 2.14720633, 2.7798611, 3.21815629,
...     3.43222282, 3.4074724, 3.14559174, 2.66442756, 1.99677042, 1.18812004,
...     0.2935846, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.47928116, 1.36069295, 2.14397247, 2.77574052, 3.21294314, 3.42578571,
...     3.39976334, 3.13664943, 2.65437475)

To avoid calculating |numpy.nan| values during the night periods within
the first 24 hours, we arbitrarily set the values of both log sequences
to one:

>>> logs.loggedclearskysolarradiation = 1.0
>>> logs.loggedglobalradiation = 1.0

Regarding reference evapotranspiration, the results match perfectly within the
specified accuracy.  The better agreement with the results reported by
:cite:`ref-Allen1998` compared with the above example is due to the more consistent
calculation of the saturation vapour pressure:

.. integration-test::

    >>> test("evap_v001_hourly", update_parameters=False,
    ...      axis1=fluxes.referenceevapotranspiration)
    |             date | airtemperature | relativehumidity | windspeed | atmosphericpressure | globalradiation | clearskysolarradiation | adjustedwindspeed | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | psychrometricconstant | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | referenceevapotranspiration |      node |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |                   -0.000649 | -0.000649 |
    | 2001-30-09 03:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |                   -0.000649 | -0.000649 |
    | 2001-30-09 04:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |                   -0.000649 | -0.000649 |
    | 2001-30-09 05:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |              0.13743 |     -0.13743 |    -0.068715 |                   -0.000649 | -0.000649 |
    | 2001-30-09 06:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        0.417372 |               0.481583 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              0.321376 |             0.112693 |     0.208683 |     0.020868 |                    0.069227 |  0.069227 |
    | 2001-30-09 07:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        1.181532 |               1.363306 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |               0.90978 |             0.112693 |     0.797087 |     0.079709 |                    0.213474 |  0.213474 |
    | 2001-30-09 08:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        1.860912 |               2.147206 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              1.432902 |             0.112693 |     1.320209 |     0.132021 |                    0.341718 |  0.341718 |
    | 2001-30-09 09:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        2.409213 |               2.779861 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              1.855094 |             0.112693 |     1.742401 |      0.17424 |                    0.445218 |  0.445218 |
    | 2001-30-09 10:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        2.789069 |               3.218156 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              2.147583 |             0.112693 |      2.03489 |     0.203489 |                    0.516922 |  0.516922 |
    | 2001-30-09 11:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        2.974593 |               3.432223 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              2.290437 |             0.112693 |     2.177744 |     0.217774 |                    0.551942 |  0.551942 |
    | 2001-30-09 12:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        2.953143 |               3.407472 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |               2.27392 |             0.112693 |     2.161227 |     0.216123 |                    0.547893 |  0.547893 |
    | 2001-30-09 13:00 |           28.0 |             90.0 |       1.9 |              1001.0 |         2.72618 |               3.145592 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              2.099158 |             0.112693 |     1.986465 |     0.198647 |                     0.50505 |   0.50505 |
    | 2001-30-09 14:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        2.309171 |               2.664428 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              1.778061 |             0.112693 |     1.665368 |     0.166537 |                    0.426333 |  0.426333 |
    | 2001-30-09 15:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        1.730534 |                1.99677 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              1.332511 |             0.112693 |     1.219819 |     0.121982 |                    0.317107 |  0.317107 |
    | 2001-30-09 16:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        1.029704 |                1.18812 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              0.792872 |             0.112693 |     0.680179 |     0.068018 |                    0.184814 |  0.184814 |
    | 2001-30-09 17:00 |           28.0 |             90.0 |       1.9 |              1001.0 |        0.288995 |               0.293585 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |              0.222526 |              0.13453 |     0.087996 |       0.0088 |                     0.03964 |   0.03964 |
    | 2001-30-09 18:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.118115 |    -0.118115 |    -0.059058 |                    0.001981 |  0.001981 |
    | 2001-30-09 19:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.117514 |    -0.117514 |    -0.058757 |                    0.002063 |  0.002063 |
    | 2001-30-09 20:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.116874 |    -0.116874 |    -0.058437 |                     0.00215 |   0.00215 |
    | 2001-30-09 21:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.116191 |    -0.116191 |    -0.058096 |                    0.002243 |  0.002243 |
    | 2001-30-09 22:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.115462 |    -0.115462 |    -0.057731 |                    0.002343 |  0.002343 |
    | 2001-30-09 23:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |              0.11468 |     -0.11468 |     -0.05734 |                    0.002449 |  0.002449 |
    | 2001-01-10 00:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.113842 |    -0.113842 |    -0.056921 |                    0.002563 |  0.002563 |
    | 2001-01-10 01:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.112938 |    -0.112938 |    -0.056469 |                    0.002686 |  0.002686 |
    | 2001-01-10 02:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             0.112938 |    -0.112938 |    -0.056469 |                    0.002686 |  0.002686 |
    | 2001-01-10 03:00 |      28.833333 |        86.833333 |  2.016667 |              1001.0 |             0.0 |                    0.0 |          2.016667 |                 39.67258 |                      2.295429 |            34.449023 |              0.665665 |                   0.0 |             0.111924 |    -0.111924 |    -0.055962 |                    0.010157 |  0.010157 |
    | 2001-01-10 04:00 |      29.666667 |        83.666667 |  2.133333 |              1001.0 |             0.0 |                    0.0 |          2.133333 |                41.626121 |                      2.393447 |            34.827188 |              0.665665 |                   0.0 |             0.111156 |    -0.111156 |    -0.055578 |                    0.018451 |  0.018451 |
    | 2001-01-10 05:00 |           30.5 |             80.5 |      2.25 |              1001.0 |             0.0 |                    0.0 |              2.25 |                43.662793 |                      2.494953 |            35.148549 |              0.665665 |                   0.0 |             0.110668 |    -0.110668 |    -0.055334 |                    0.027586 |  0.027586 |
    | 2001-01-10 06:00 |      31.333333 |        77.333333 |  2.366667 |              1001.0 |        0.423898 |               0.479281 |          2.366667 |                45.785544 |                      2.600043 |            35.407488 |              0.665665 |              0.326401 |             0.113482 |     0.212919 |     0.021292 |                    0.106473 |  0.106473 |
    | 2001-01-10 07:00 |      32.166667 |        74.166667 |  2.483333 |              1001.0 |        1.209505 |               1.360693 |          2.483333 |                47.997402 |                      2.708817 |            35.598073 |              0.665665 |              0.931319 |             0.114477 |     0.816842 |     0.081684 |                    0.270383 |  0.270383 |
    | 2001-01-10 08:00 |           33.0 |             71.0 |       2.6 |              1001.0 |        1.915282 |               2.143972 |               2.6 |                50.301478 |                      2.821374 |            35.714049 |              0.665665 |              1.474767 |             0.115888 |     1.358879 |     0.135888 |                    0.421351 |  0.421351 |
    | 2001-01-10 09:00 |      33.833333 |        67.833333 |  2.716667 |              1001.0 |        2.491998 |               2.775741 |          2.716667 |                52.700967 |                      2.937817 |            35.748823 |              0.665665 |              1.918839 |             0.117774 |     1.801064 |     0.180106 |                     0.54941 |   0.54941 |
    | 2001-01-10 10:00 |      34.666667 |        64.666667 |  2.833333 |              1001.0 |        2.898789 |               3.212943 |          2.833333 |                55.199152 |                       3.05825 |            35.695452 |              0.665665 |              2.232067 |             0.120202 |     2.111865 |     0.211187 |                    0.646013 |  0.646013 |
    | 2001-01-10 11:00 |           35.5 |             61.5 |      2.95 |              1001.0 |        3.106046 |               3.425786 |              2.95 |                57.799401 |                       3.18278 |            35.546632 |              0.665665 |              2.391655 |             0.123243 |     2.268412 |     0.226841 |                    0.704657 |  0.704657 |
    | 2001-01-10 12:00 |      36.333333 |        58.333333 |  3.066667 |              1001.0 |        3.097562 |               3.399763 |          3.066667 |                60.505174 |                      3.311513 |            35.294685 |              0.665665 |              2.385123 |             0.126981 |     2.258142 |     0.225814 |                    0.721384 |  0.721384 |
    | 2001-01-10 13:00 |      37.166667 |        55.166667 |  3.183333 |              1001.0 |        2.871777 |               3.136649 |          3.183333 |                63.320018 |                       3.44456 |            34.931543 |              0.665665 |              2.211268 |             0.131506 |     2.079762 |     0.207976 |                    0.695112 |  0.695112 |
    | 2001-01-10 14:00 |           38.0 |             52.0 |       3.3 |              1001.0 |        2.442025 |               2.654375 |               3.3 |                66.247576 |                      3.582033 |             34.44874 |              0.665665 |              1.880359 |             0.136924 |     1.743435 |     0.174343 |                    0.627771 |  0.627771 |
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
        evap_model.Update_LoggedClearSkySolarRadiation_V1,
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
