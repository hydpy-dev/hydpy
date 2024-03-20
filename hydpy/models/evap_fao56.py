# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the FAO reference evapotranspiration model.

|evap_fao56| follows the guideline provided by :cite:t:`ref-Allen1998`.  However, there
are some differences in input data assumptions (averaged daily temperature and relative
humidity values instead of maximum and minimum values).

The primary purpose of |evap_fao56| is to serve as a submodel that provides estimates
of potential grass reference evapotranspiration.  However, you can also use it as a
stand-alone model, as it does not require interaction with a main model.  The following
examples make use of this stand-alone functionality.

On the other hand, |evap_fao56| requires two submodels.  One must follow the
|RadiationModel_V1| or the |RadiationModel_V3| interface and provide clear-sky solar
radiation and global radiation data; the other must follow the |TempModel_V1| or the
|TempModel_V2| interface and provide temperature data.  Regarding radiation,
|meteo_v001| is an obvious choice, as it follows the FAO guideline, too.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_fao56| requires no input from an external model and does not
supply  any data to an outlet sequence.  Hence, assigning a model instance to a blank
|Element| instance is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_fao56 import *
>>> parameterstep()
>>> element = Element("element")
>>> element.model = model

.. _evap_fao56_daily_simulation:

daily simulation
________________

The first example deals with a daily simulation time step.  We calculate the reference
evapotranspiration on 6 July in Uccle (Brussels, Belgium) and take the following
parameter values and input values from example 18 of :cite:t:`ref-Allen1998`:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> nmbhru(1)
>>> hruarea(1.0)
>>> measuringheightwindspeed(10.0)
>>> evapotranspirationfactor(1.0)
>>> with model.add_radiationmodel_v3("meteo_clear_glob_io"):
...     pass
>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     temperatureaddend(0.0)

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> model.tempmodel.sequences.inputs.temperature.series = 16.9
>>> inputs.relativehumidity.series = 73.0
>>> inputs.windspeed.series = 10.0 * 1000.0 / 60.0 / 60.0
>>> inputs.atmosphericpressure.series = 1001.0

The following global and clear sky solar radiation values are the results of the
:ref:`meteo_v001_daily_simulation` integration test of |meteo_v001| that also
recalculates example 18 of :cite:t:`ref-Allen1998`:

>>> model.radiationmodel.sequences.inputs.clearskysolarradiation.series = 356.40121
>>> model.radiationmodel.sequences.inputs.globalradiation.series = 255.367464

The calculated reference evapotranspiration is about 0.1 mm (3 %) smaller than the one
given by :cite:t:`ref-Allen1998`. This discrepancy is mainly due to different ways to
calculate |SaturationVapourPressure|.  :cite:t:`ref-Allen1998` estimates it both for the
minimum and maximum temperature and averages the results, while |evap_fao56| directly
applies the corresponding formula to the average air temperature.  The first approach
results in higher pressure values due to the nonlinearity of the vapour pressure curve.
All other methodical differences show, at least in this example, less severe impacts:

.. integration-test::

    >>> test()
    |       date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed2m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | psychrometricconstant | globalradiation | clearskysolarradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | referenceevapotranspiration | meanreferenceevapotranspiration |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |             73.0 |  2.777778 |              1001.0 |           16.9 |    2.077091 |                19.254836 |                      1.221127 |             14.05603 |              0.665665 |      255.367464 |              356.40121 |            196.632947 |            43.150905 |   153.482043 |          0.0 |                    3.750015 |                        3.750015 |


.. _evap_fao56_hourly_simulation:

hourly simulation
_________________

The second example deals with an hourly simulation over multiple time steps.  We
calculate the reference evapotranspiration from 30 September to 1 October in N'Diaye
(Senegal) and take (or try to derive as well as possible) all parameter and input
values from example 19 of `FAO`:

>>> measuringheightwindspeed(2.0)

Example 19 of :t:`ref-Allen1998` gives results for the intervals between 2 and 3
o'clock and between 14 and 15 o'clock only.  We assume these clock times are referring
to UTC-1:

>>> pub.options.utcoffset = -60
>>> pub.options.utclongitude = -15
>>> pub.timegrids = "2001-09-30 02:00", "2001-10-01 15:00", "1h"

This time, we do not let |meteo_clear_glob_io| provide the precalculated clear-sky and
global radiation of the :ref:`meteo_v001_hourly_simulation` integration test, which
corresponds to example 19 of :cite:t:`ref-Allen1998`, but let |meteo_v001| calculate
it on the fly:

>>> with model.add_radiationmodel_v1("meteo_v001"):
...     latitude(16.0 + 0.13 / 60 * 100)
...     longitude(-16.25)
...     angstromconstant(0.25)
...     angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m %H:00"

>>> sunshineduration = model.radiationmodel.sequences.inputs.sunshineduration
>>> sunshineduration.series = 0.0
>>> sunshineduration.series[3:16] = 0.8
>>> sunshineduration.series[27:] = numpy.linspace(0.82, 0.88, 10)

We set constant input sequence values from the start of the simulation period to the
first interval and interpolate linearly between the first and the second interval,
which is also the end of the simulation period:

>>> import numpy
>>> def interpolate(sequence, value1, value2):
...     sequence.series[:-13] = value1
...     sequence.series[-13:] = numpy.linspace(value1, value2, 13)

>>> interpolate(model.tempmodel.sequences.inputs.temperature, 28.0, 38.0)
>>> interpolate(inputs.relativehumidity, 90.0, 52.0)
>>> interpolate(inputs.windspeed, 1.9, 3.3)
>>> interpolate(inputs.atmosphericpressure, 1001.0, 1001.0)

To avoid calculating |numpy.nan| values at night within the first 24 hours, we
arbitrarily set the values of both log sequences to one:

>>> logs.loggedclearskysolarradiation = 277.777778
>>> logs.loggedglobalradiation = 277.777778

Regarding reference evapotranspiration, the results match perfectly within the
specified accuracy.  Compared with the above example, the better agreement with the
results reported by :cite:t:`ref-Allen1998` is due to the more consistent calculation
of the saturation vapour pressure:

.. integration-test::

    >>> test("evap_fao56_hourly", update_parameters=False,
    ...      axis1=fluxes.referenceevapotranspiration)
    |             date | relativehumidity | windspeed | atmosphericpressure | airtemperature | windspeed2m | saturationvapourpressure | saturationvapourpressureslope | actualvapourpressure | psychrometricconstant | globalradiation | clearskysolarradiation | netshortwaveradiation | netlongwaveradiation | netradiation | soilheatflux | referenceevapotranspiration | meanreferenceevapotranspiration |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 |                       -0.000649 |
    | 2001-30-09 03:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 |                       -0.000649 |
    | 2001-30-09 04:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 |                       -0.000649 |
    | 2001-30-09 05:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            38.175107 |   -38.175107 |   -19.087554 |                   -0.000649 |                       -0.000649 |
    | 2001-30-09 06:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      115.964852 |             133.805599 |             89.292936 |            31.303588 |    57.989348 |     5.798935 |                    0.069246 |                        0.069246 |
    | 2001-30-09 07:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      328.283435 |             378.788578 |            252.778245 |            31.303588 |   221.474657 |    22.147466 |                    0.213528 |                        0.213528 |
    | 2001-30-09 08:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      517.046121 |             596.591678 |            398.125513 |            31.303588 |   366.821925 |    36.682193 |                    0.341803 |                        0.341803 |
    | 2001-30-09 09:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      669.389046 |             772.371976 |            515.429565 |            31.303588 |   484.125978 |    48.412598 |                    0.445329 |                        0.445329 |
    | 2001-30-09 10:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      774.930291 |             894.150336 |            596.696324 |            31.303588 |   565.392736 |    56.539274 |                     0.51705 |                         0.51705 |
    | 2001-30-09 11:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      826.477395 |             953.627764 |            636.387594 |            31.303588 |   605.084006 |    60.508401 |                    0.552079 |                        0.552079 |
    | 2001-30-09 12:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      820.517508 |              946.75097 |            631.798481 |            31.303588 |   600.494893 |    60.049489 |                    0.548029 |                        0.548029 |
    | 2001-30-09 13:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      757.456786 |             873.988599 |            583.241725 |            31.303588 |   551.938137 |    55.193814 |                    0.505176 |                        0.505176 |
    | 2001-30-09 14:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      641.592713 |             740.299284 |            494.026389 |            31.303588 |   462.722801 |     46.27228 |                     0.42644 |                         0.42644 |
    | 2001-30-09 15:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      480.821234 |             554.793732 |             370.23235 |            31.303588 |   338.928763 |    33.892876 |                    0.317186 |                        0.317186 |
    | 2001-30-09 16:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |      286.098661 |             330.113839 |            220.295969 |            31.303588 |   188.992381 |    18.899238 |                    0.184861 |                        0.184861 |
    | 2001-30-09 17:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |       80.296089 |              81.571169 |             61.827989 |            37.369516 |    24.458473 |     2.445847 |                    0.039653 |                        0.039653 |
    | 2001-30-09 18:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            32.809472 |   -32.809472 |   -16.404736 |                    0.001981 |                        0.001981 |
    | 2001-30-09 19:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            32.642447 |   -32.642447 |   -16.321224 |                    0.002063 |                        0.002063 |
    | 2001-30-09 20:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            32.464689 |   -32.464689 |   -16.232345 |                     0.00215 |                         0.00215 |
    | 2001-30-09 21:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |             32.27513 |    -32.27513 |   -16.137565 |                    0.002243 |                        0.002243 |
    | 2001-30-09 22:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            32.072553 |   -32.072553 |   -16.036276 |                    0.002343 |                        0.002343 |
    | 2001-30-09 23:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            31.855571 |   -31.855571 |   -15.927785 |                    0.002449 |                        0.002449 |
    | 2001-01-10 00:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |             31.62259 |    -31.62259 |   -15.811295 |                    0.002563 |                        0.002563 |
    | 2001-01-10 01:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            31.371772 |   -31.371772 |   -15.685886 |                    0.002686 |                        0.002686 |
    | 2001-01-10 02:00 |             90.0 |       1.9 |              1001.0 |           28.0 |         1.9 |                37.799304 |                      2.200803 |            34.019373 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            31.371772 |   -31.371772 |   -15.685886 |                    0.002686 |                        0.002686 |
    | 2001-01-10 03:00 |        86.833333 |  2.016667 |              1001.0 |      28.833333 |    2.016667 |                 39.67258 |                      2.295429 |            34.449023 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            31.089954 |   -31.089954 |   -15.544977 |                    0.010157 |                        0.010157 |
    | 2001-01-10 04:00 |        83.666667 |  2.133333 |              1001.0 |      29.666667 |    2.133333 |                41.626121 |                      2.393447 |            34.827188 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            30.876731 |   -30.876731 |   -15.438365 |                    0.018451 |                        0.018451 |
    | 2001-01-10 05:00 |             80.5 |      2.25 |              1001.0 |           30.5 |        2.25 |                43.662793 |                      2.494953 |            35.148549 |              0.665665 |             0.0 |                    0.0 |                   0.0 |            30.741149 |   -30.741149 |   -15.370574 |                    0.027586 |                        0.027586 |
    | 2001-01-10 06:00 |        77.333333 |  2.366667 |              1001.0 |      31.333333 |    2.366667 |                45.785544 |                      2.600043 |            35.407488 |              0.665665 |      117.778042 |             133.166127 |             90.689092 |            31.522798 |    59.166294 |     5.916629 |                    0.106493 |                        0.106493 |
    | 2001-01-10 07:00 |        74.166667 |  2.483333 |              1001.0 |      32.166667 |    2.483333 |                47.997402 |                      2.708817 |            35.598073 |              0.665665 |      336.055513 |             378.062452 |            258.762745 |            31.799047 |   226.963698 |     22.69637 |                     0.27044 |                         0.27044 |
    | 2001-01-10 08:00 |             71.0 |       2.6 |              1001.0 |           33.0 |         2.6 |                50.301478 |                      2.821374 |            35.714049 |              0.665665 |      532.152561 |             595.693165 |            409.757472 |            32.191063 |   377.566409 |    37.756641 |                    0.421442 |                        0.421442 |
    | 2001-01-10 09:00 |        67.833333 |  2.716667 |              1001.0 |      33.833333 |    2.716667 |                52.700967 |                      2.937817 |            35.748823 |              0.665665 |      692.390544 |             771.227092 |            533.140719 |            32.715134 |   500.425585 |    50.042558 |                     0.54953 |                         0.54953 |
    | 2001-01-10 10:00 |        64.666667 |  2.833333 |              1001.0 |      34.666667 |    2.833333 |                55.199152 |                       3.05825 |            35.695452 |              0.665665 |      805.415479 |             892.701885 |            620.169919 |            33.389426 |   586.780492 |    58.678049 |                    0.646153 |                        0.646153 |
    | 2001-01-10 11:00 |             61.5 |      2.95 |              1001.0 |           35.5 |        2.95 |                57.799401 |                       3.18278 |            35.546632 |              0.665665 |      863.000911 |              951.83924 |            664.510701 |            34.234247 |   630.276454 |    63.027645 |                    0.704808 |                        0.704808 |
    | 2001-01-10 12:00 |        58.333333 |  3.066667 |              1001.0 |      36.333333 |    3.066667 |                60.505174 |                      3.311513 |            35.294685 |              0.665665 |      860.643794 |             944.609042 |            662.695721 |            35.272376 |   627.423345 |    62.742335 |                    0.721536 |                        0.721536 |
    | 2001-01-10 13:00 |        55.166667 |  3.183333 |              1001.0 |      37.166667 |    3.183333 |                63.320018 |                       3.44456 |            34.931543 |              0.665665 |      797.910345 |             871.504018 |            614.390966 |            36.529456 |   577.861509 |    57.786151 |                    0.695253 |                        0.695253 |
    | 2001-01-10 14:00 |             52.0 |       3.3 |              1001.0 |           38.0 |         3.3 |                66.247576 |                      3.582033 |             34.44874 |              0.665665 |      678.505661 |             737.506154 |            522.449359 |            38.034488 |   484.414871 |    48.441487 |                    0.627892 |                        0.627892 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import radiationinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2A,
    evap_model.Main_RadiationModel_V1,
    evap_model.Main_RadiationModel_V3,
    evap_model.Sub_ETModel,
    petinterfaces.PETModel_V1,
):
    """The FAO-56 version of the HydPy-Evap."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Process_RadiationModel_V1,
        evap_model.Calc_ClearSkySolarRadiation_V1,
        evap_model.Calc_GlobalRadiation_V1,
        evap_model.Calc_WindSpeed2m_V1,
        evap_model.Calc_AirTemperature_V1,
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
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_MeanReferenceEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V1,
        evap_model.Get_MeanPotentialEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_AirTemperature_TempModel_V1,
        evap_model.Calc_AirTemperature_TempModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2)
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    radiationmodel = modeltools.SubmodelProperty(
        radiationinterfaces.RadiationModel_V1, radiationinterfaces.RadiationModel_V3
    )


tester = Tester()
cythonizer = Cythonizer()
