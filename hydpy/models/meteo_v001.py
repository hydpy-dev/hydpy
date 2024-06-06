# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Model for calculating radiation terms based on sunshine duration following the FAO
reference evapotranspiration model.

Version 1 of `HydPy-Meteo` follows the guide-line provided by :cite:t:`ref-Allen1998`.
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
models could require.  Many require |meteo_fluxes.GlobalRadiation| for calculating net
shortwave radiation.  Some also require |meteo_factors.PossibleSunshineDuration| or
|meteo_fluxes.ClearSkySolarRadiation| to guess cloudiness for calculating net longwave
radiation.  Here, we select |meteo_fluxes.GlobalRadiation| and
|meteo_fluxes.ClearSkySolarRadiation| by importing their globally available aliases,
which we hand over to the |Node| instances `node1` and `node2`:

>>> from hydpy import Element, Node
>>> from hydpy.aliases import meteo_fluxes_GlobalRadiation, meteo_fluxes_ClearSkySolarRadiation
>>> node1 = Node("node1", variable=meteo_fluxes_GlobalRadiation)
>>> node2 = Node("node2", variable=meteo_fluxes_ClearSkySolarRadiation)

Now, we can prepare an instance of |meteo_v001| and assign it to an element connected
to the prepared nodes:

>>> from hydpy.models.meteo_v001 import *
>>> parameterstep()
>>> element = Element("element", outputs=(node1, node2))
>>> element.model = model

.. _meteo_v001_daily_simulation:

daily simulation
________________

The first example deals with a daily simulation time step.  We calculate the radiation 
terms on 6 July in Uccle (Brussels, Belgium) and take all input data from example 18 of 
:cite:t:`ref-Allen1998`:

>>> from hydpy import IntegrationTest, pub, round_
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> latitude(50.8)
>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.sunshineduration.series = 9.25

Both for |meteo_fluxes.GlobalRadiation| and |meteo_fluxes.ClearSkySolarRadiation|, the
differences to the results given by :cite:t:`ref-Allen1998` are significantly less than
1 %:

.. integration-test::

    >>> test()
    |       date | sunshineduration | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | extraterrestrialradiation | clearskysolarradiation | globalradiation |      node1 |     node2 |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |             9.25 |         0.967121 |         0.394547 |        2.106601 |            nan |                16.093247 |                475.201614 |              356.40121 |      255.367464 | 255.367464 | 356.40121 |

All getters specified by the |RadiationModel_V1| interface return the correct data:

>>> round_(model.get_possiblesunshineduration())
16.093247
>>> round_(model.get_sunshineduration())
9.25
>>> round_(model.get_clearskysolarradiation())
356.40121
>>> round_(model.get_globalradiation())
255.367464

.. _meteo_v001_hourly_simulation:

hourly simulation
_________________

The second example deals with an hourly simulation over multiple time steps.  We 
calculate the different radiation terms from 30 September to 1 October in N'Diaye 
(Senegal) and take (or try to derive as well as possible) all parameter and input
values from example 19 of :cite:t:`ref-Allen1998`.

Example 19 of :cite:t:`ref-Allen1998` gives results for the intervals between 2 and 3
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

We set the sunshine duration constant at 80 % during the first daytime period and let
it linearly increase from 82 % to 88 % in the (incomplete) second daytime period.  The
exceedance of the potential sunshine duration during both sunsets does not affect the
results negatively.  At the end of the simulation period, the given sunshine duration
of 88 % corresponds to a ratio of global radiation and clear sky radiation of
approximately 0.92, which is an intermediate result of :cite:t:`ref-Allen1998`:

>>> import numpy
>>> inputs.sunshineduration.series = 0.0
>>> inputs.sunshineduration.series[3:16] = 0.8
>>> inputs.sunshineduration.series[27:] = numpy.linspace(0.82, 0.88, 10)

Again, the calculated |meteo_fluxes.GlobalRadiation| and
|meteo_fluxes.ClearSkySolarRadiation| differ significantly less than 1 % from the
results given by :cite:t:`ref-Allen1998`:

.. integration-test::

    >>> test("meteo_v001_hourly",
    ...      axis1=(fluxes.globalradiation, fluxes.clearskysolarradiation))
    |             date | sunshineduration | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | extraterrestrialradiation | clearskysolarradiation | globalradiation |      node1 |      node2 |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.460182 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 03:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.198383 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 04:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |      -1.936583 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 05:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -1.674784 |                   0.0248 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 06:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -1.412985 |                      1.0 |                178.407465 |             133.805599 |      115.964852 | 115.964852 | 133.805599 |
    | 2001-30-09 07:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -1.151185 |                      1.0 |                505.051438 |             378.788578 |      328.283435 | 328.283435 | 378.788578 |
    | 2001-30-09 08:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.889386 |                      1.0 |                795.455571 |             596.591678 |      517.046121 | 517.046121 | 596.591678 |
    | 2001-30-09 09:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.627587 |                      1.0 |               1029.829301 |             772.371976 |      669.389046 | 669.389046 | 772.371976 |
    | 2001-30-09 10:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.365787 |                      1.0 |               1192.200448 |             894.150336 |      774.930291 | 774.930291 | 894.150336 |
    | 2001-30-09 11:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |      -0.103988 |                      1.0 |               1271.503685 |             953.627764 |      826.477395 | 826.477395 | 953.627764 |
    | 2001-30-09 12:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       0.157812 |                      1.0 |               1262.334627 |              946.75097 |      820.517508 | 820.517508 |  946.75097 |
    | 2001-30-09 13:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       0.419611 |                      1.0 |               1165.318132 |             873.988599 |      757.456786 | 757.456786 | 873.988599 |
    | 2001-30-09 14:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |        0.68141 |                      1.0 |                987.065712 |             740.299284 |      641.592713 | 641.592713 | 740.299284 |
    | 2001-30-09 15:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |        0.94321 |                      1.0 |                739.724976 |             554.793732 |      480.821234 | 480.821234 | 554.793732 |
    | 2001-30-09 16:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       1.205009 |                      1.0 |                440.151786 |             330.113839 |      286.098661 | 286.098661 | 330.113839 |
    | 2001-30-09 17:00 |              0.8 |         0.999717 |        -0.070087 |        1.550377 |       1.466809 |                 0.819208 |                108.761559 |              81.571169 |       80.296089 |  80.296089 |  81.571169 |
    | 2001-30-09 18:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       1.728608 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 19:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       1.990407 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 20:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.252207 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 21:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.514006 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 22:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       2.775806 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-30-09 23:00 |              0.0 |         0.999717 |        -0.070087 |        1.550377 |       3.037605 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 00:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |      -2.982399 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 01:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |        -2.7206 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 02:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |        -2.4588 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 03:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |      -2.197001 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 04:00 |              0.0 |         1.000283 |        -0.076994 |        1.548357 |      -1.935202 |                      0.0 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 05:00 |             0.82 |         1.000283 |        -0.076994 |        1.548357 |      -1.673402 |                 0.022362 |                       0.0 |                    0.0 |             0.0 |        0.0 |        0.0 |
    | 2001-01-10 06:00 |         0.826667 |         1.000283 |        -0.076994 |        1.548357 |      -1.411603 |                      1.0 |                177.554837 |             133.166127 |      117.778042 | 117.778042 | 133.166127 |
    | 2001-01-10 07:00 |         0.833333 |         1.000283 |        -0.076994 |        1.548357 |      -1.149804 |                      1.0 |                 504.08327 |             378.062452 |      336.055513 | 336.055513 | 378.062452 |
    | 2001-01-10 08:00 |             0.84 |         1.000283 |        -0.076994 |        1.548357 |      -0.888004 |                      1.0 |                794.257553 |             595.693165 |      532.152561 | 532.152561 | 595.693165 |
    | 2001-01-10 09:00 |         0.846667 |         1.000283 |        -0.076994 |        1.548357 |      -0.626205 |                      1.0 |               1028.302789 |             771.227092 |      692.390544 | 692.390544 | 771.227092 |
    | 2001-01-10 10:00 |         0.853333 |         1.000283 |        -0.076994 |        1.548357 |      -0.364405 |                      1.0 |                1190.26918 |             892.701885 |      805.415479 | 805.415479 | 892.701885 |
    | 2001-01-10 11:00 |             0.86 |         1.000283 |        -0.076994 |        1.548357 |      -0.102606 |                      1.0 |               1269.118986 |              951.83924 |      863.000911 | 863.000911 |  951.83924 |
    | 2001-01-10 12:00 |         0.866667 |         1.000283 |        -0.076994 |        1.548357 |       0.159193 |                      1.0 |               1259.478722 |             944.609042 |      860.643794 | 860.643794 | 944.609042 |
    | 2001-01-10 13:00 |         0.873333 |         1.000283 |        -0.076994 |        1.548357 |       0.420993 |                      1.0 |               1162.005357 |             871.504018 |      797.910345 | 797.910345 | 871.504018 |
    | 2001-01-10 14:00 |             0.88 |         1.000283 |        -0.076994 |        1.548357 |       0.682792 |                      1.0 |                983.341538 |             737.506154 |      678.505661 | 678.505661 | 737.506154 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import radiationinterfaces
from hydpy.models.meteo import meteo_model


class Model(modeltools.AdHocModel, radiationinterfaces.RadiationModel_V1):
    """Version 1 of the Meteo model."""

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
        meteo_model.Calc_GlobalRadiation_V1,
    )
    INTERFACE_METHODS = (
        meteo_model.Process_Radiation_V1,
        meteo_model.Get_PossibleSunshineDuration_V1,
        meteo_model.Get_SunshineDuration_V2,
        meteo_model.Get_ClearSkySolarRadiation_V1,
        meteo_model.Get_GlobalRadiation_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
