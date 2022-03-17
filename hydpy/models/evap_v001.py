# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the FAO reference evapotranspiration model.

Version 1 of the HydPy-E model (Evap) follows the guide-line provided by
:cite:t:`ref-Allen1998`.  However, there are some differences in input data assumptions
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
parameter values and input values from example 18 of :cite:t:`ref-Allen1998`:

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
recalculates example 18 of :cite:t:`ref-Allen1998`:

>>> inputs.globalradiation.series = 255.367464
>>> inputs.clearskysolarradiation.series = 356.40121

The calculated reference evapotranspiration is about 0.1 mm (3 %) smaller than the one
given by :cite:t:`ref-Allen1998`. This discrepancy is mainly due to different ways to
calculate |SaturationVapourPressure|.  :cite:t:`ref-Allen1998` estimates it both for the
minimum and maximum temperature and averages the results, while |evap_v001| directly
applies the corresponding formula on the average air temperature.  The first approach
results in higher pressure values due to the nonlinearity of the vapour pressure curve.
All other methodical differences show, at least in this example, less severe impacts:

.. integration-test::

    >>> test()
    |       date | airtemperature | relativehumidity | windspeed | atmosphericpressure | globalradiation | clearskysolarradiation | adjustedwindspeed | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | psychrometricconstant | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | referenceevapotranspiration |     node |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |             73.0 |  2.777778 |              1001.0 |      255.367464 |              356.40121 |          2.077091 |                19.254836 |                      1.221127 |             14.05603 |              0.665665 |            196.632947 |            43.150905 |   153.482043 |          0.0 |                    3.750015 | 3.750015 |

hourly simulation
_________________

The second example deals with an hourly simulation over multiple time steps.  We
calculate the reference evapotranspiration from 30 September to 1 October in N'Diaye
(Senegal) and take (or try to derive as good as possible) all parameter and input
values from example 19 of `FAO`:

>>> measuringheightwindspeed(2.0)

Example 19 of :t:ref-Allen1998` gives results for the intervals between 2 and 3
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
example 19 of :cite:t:`ref-Allen1998` in its :ref:`meteo_v001_hourly_simulation`
integration test:

>>> inputs.globalradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 115.964852, 328.283435, 517.046121, 669.389046, 774.930291,
...     826.477395, 820.517508, 757.456786, 641.592713, 480.821234, 286.098661,
...     80.296089, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     117.778042, 336.055513, 532.152561, 692.390544, 805.415479, 863.000911,
...     860.643794, 797.910345, 678.505661)
>>> inputs.clearskysolarradiation.series = (
...     0.0, 0.0, 0.0, 0.0, 133.805599, 378.788578, 596.591678, 772.371976, 894.150336,
...     953.627764, 946.75097, 873.988599, 740.299284, 554.793732, 330.113839,
...     81.571169, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     133.166127, 378.062452, 595.693165, 771.227092, 892.701885, 951.83924,
...     944.609042, 871.504018, 737.506154)

To avoid calculating |numpy.nan| values during the night periods within
the first 24 hours, we arbitrarily set the values of both log sequences
to one:

>>> logs.loggedclearskysolarradiation = 277.777778
>>> logs.loggedglobalradiation = 277.777778

Regarding reference evapotranspiration, the results match perfectly within the
specified accuracy.  The better agreement with the results reported by
:cite:t:`ref-Allen1998` compared with the above example is due to the more consistent
calculation of the saturation vapour pressure:

.. integration-test::

    >>> test("evap_v001_hourly", update_parameters=False,
    ...      axis1=fluxes.referenceevapotranspiration)
    |             date | airtemperature | relativehumidity | windspeed | atmosphericpressure | globalradiation | clearskysolarradiation | adjustedwindspeed | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | psychrometricconstant | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | referenceevapotranspiration |      node |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 | -0.000649 |
    | 2001-30-09 03:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 | -0.000649 |
    | 2001-30-09 04:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 | -0.000649 |
    | 2001-30-09 05:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 | -0.000649 |
    | 2001-30-09 06:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      115.964852 |             133.805599 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             89.292936 |            31.303588 |    57.989348 |     5.798935 |                    0.069246 |  0.069246 |
    | 2001-30-09 07:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      328.283435 |             378.788578 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            252.778245 |            31.303588 |   221.474657 |    22.147466 |                    0.213528 |  0.213528 |
    | 2001-30-09 08:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      517.046121 |             596.591678 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            398.125513 |            31.303588 |   366.821925 |    36.682193 |                    0.341803 |  0.341803 |
    | 2001-30-09 09:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      669.389046 |             772.371976 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            515.429565 |            31.303588 |   484.125978 |    48.412598 |                    0.445329 |  0.445329 |
    | 2001-30-09 10:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      774.930291 |             894.150336 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            596.696324 |            31.303588 |   565.392736 |    56.539274 |                     0.51705 |   0.51705 |
    | 2001-30-09 11:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      826.477395 |             953.627764 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            636.387594 |            31.303588 |   605.084006 |    60.508401 |                    0.552079 |  0.552079 |
    | 2001-30-09 12:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      820.517508 |              946.75097 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            631.798481 |            31.303588 |   600.494893 |    60.049489 |                    0.548029 |  0.548029 |
    | 2001-30-09 13:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      757.456786 |             873.988599 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            583.241725 |            31.303588 |   551.938137 |    55.193814 |                    0.505176 |  0.505176 |
    | 2001-30-09 14:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      641.592713 |             740.299284 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            494.026389 |            31.303588 |   462.722801 |     46.27228 |                     0.42644 |   0.42644 |
    | 2001-30-09 15:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      480.821234 |             554.793732 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             370.23235 |            31.303588 |   338.928762 |    33.892876 |                    0.317186 |  0.317186 |
    | 2001-30-09 16:00 |           28.0 |             90.0 |       1.9 |              1001.0 |      286.098661 |             330.113839 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |            220.295969 |            31.303588 |   188.992381 |    18.899238 |                    0.184861 |  0.184861 |
    | 2001-30-09 17:00 |           28.0 |             90.0 |       1.9 |              1001.0 |       80.296089 |              81.571169 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             61.827989 |            37.369516 |    24.458473 |     2.445847 |                    0.039653 |  0.039653 |
    | 2001-30-09 18:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            32.809472 |   -32.809472 |   -16.404736 |                    0.001981 |  0.001981 |
    | 2001-30-09 19:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            32.642447 |   -32.642447 |   -16.321224 |                    0.002063 |  0.002063 |
    | 2001-30-09 20:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            32.464689 |   -32.464689 |   -16.232345 |                     0.00215 |   0.00215 |
    | 2001-30-09 21:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             32.27513 |    -32.27513 |   -16.137565 |                    0.002243 |  0.002243 |
    | 2001-30-09 22:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            32.072553 |   -32.072553 |   -16.036276 |                    0.002343 |  0.002343 |
    | 2001-30-09 23:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            31.855571 |   -31.855571 |   -15.927785 |                    0.002449 |  0.002449 |
    | 2001-01-10 00:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |             31.62259 |    -31.62259 |   -15.811295 |                    0.002563 |  0.002563 |
    | 2001-01-10 01:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            31.371772 |   -31.371772 |   -15.685886 |                    0.002686 |  0.002686 |
    | 2001-01-10 02:00 |           28.0 |             90.0 |       1.9 |              1001.0 |             0.0 |                    0.0 |               1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |                   0.0 |            31.371772 |   -31.371772 |   -15.685886 |                    0.002686 |  0.002686 |
    | 2001-01-10 03:00 |      28.833333 |        86.833333 |  2.016667 |              1001.0 |             0.0 |                    0.0 |          2.016667 |                 39.67258 |                      2.295429 |            34.449023 |              0.665665 |                   0.0 |            31.089954 |   -31.089954 |   -15.544977 |                    0.010157 |  0.010157 |
    | 2001-01-10 04:00 |      29.666667 |        83.666667 |  2.133333 |              1001.0 |             0.0 |                    0.0 |          2.133333 |                41.626121 |                      2.393447 |            34.827188 |              0.665665 |                   0.0 |            30.876731 |   -30.876731 |   -15.438366 |                    0.018451 |  0.018451 |
    | 2001-01-10 05:00 |           30.5 |             80.5 |      2.25 |              1001.0 |             0.0 |                    0.0 |              2.25 |                43.662793 |                      2.494953 |            35.148549 |              0.665665 |                   0.0 |            30.741149 |   -30.741149 |   -15.370574 |                    0.027586 |  0.027586 |
    | 2001-01-10 06:00 |      31.333333 |        77.333333 |  2.366667 |              1001.0 |      117.778042 |             133.166127 |          2.366667 |                45.785544 |                      2.600043 |            35.407488 |              0.665665 |             90.689092 |            31.522798 |    59.166294 |     5.916629 |                    0.106493 |  0.106493 |
    | 2001-01-10 07:00 |      32.166667 |        74.166667 |  2.483333 |              1001.0 |      336.055513 |             378.062452 |          2.483333 |                47.997402 |                      2.708817 |            35.598073 |              0.665665 |            258.762745 |            31.799047 |   226.963698 |     22.69637 |                     0.27044 |   0.27044 |
    | 2001-01-10 08:00 |           33.0 |             71.0 |       2.6 |              1001.0 |      532.152561 |             595.693165 |               2.6 |                50.301478 |                      2.821374 |            35.714049 |              0.665665 |            409.757472 |            32.191063 |   377.566409 |    37.756641 |                    0.421442 |  0.421442 |
    | 2001-01-10 09:00 |      33.833333 |        67.833333 |  2.716667 |              1001.0 |      692.390544 |             771.227092 |          2.716667 |                52.700967 |                      2.937817 |            35.748823 |              0.665665 |            533.140719 |            32.715134 |   500.425585 |    50.042558 |                     0.54953 |   0.54953 |
    | 2001-01-10 10:00 |      34.666667 |        64.666667 |  2.833333 |              1001.0 |      805.415479 |             892.701885 |          2.833333 |                55.199152 |                       3.05825 |            35.695452 |              0.665665 |            620.169919 |            33.389426 |   586.780493 |    58.678049 |                    0.646153 |  0.646153 |
    | 2001-01-10 11:00 |           35.5 |             61.5 |      2.95 |              1001.0 |      863.000911 |              951.83924 |              2.95 |                57.799401 |                       3.18278 |            35.546632 |              0.665665 |            664.510701 |            34.234247 |   630.276454 |    63.027645 |                    0.704808 |  0.704808 |
    | 2001-01-10 12:00 |      36.333333 |        58.333333 |  3.066667 |              1001.0 |      860.643794 |             944.609042 |          3.066667 |                60.505174 |                      3.311513 |            35.294685 |              0.665665 |            662.695721 |            35.272376 |   627.423346 |    62.742335 |                    0.721536 |  0.721536 |
    | 2001-01-10 13:00 |      37.166667 |        55.166667 |  3.183333 |              1001.0 |      797.910345 |             871.504018 |          3.183333 |                63.320018 |                       3.44456 |            34.931543 |              0.665665 |            614.390966 |            36.529456 |   577.861509 |    57.786151 |                    0.695253 |  0.695253 |
    | 2001-01-10 14:00 |           38.0 |             52.0 |       3.3 |              1001.0 |      678.505661 |             737.506154 |               3.3 |                66.247576 |                      3.582033 |             34.44874 |              0.665665 |            522.449359 |            38.034488 |   484.414871 |    48.441487 |                    0.627892 |  0.627892 |
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
