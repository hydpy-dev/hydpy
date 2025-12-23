# pylint: disable=line-too-long, unused-wildcard-import
"""|meteo_sun_fao56| is nearly identical to |meteo_glob_fao56|, except that it expects
|meteo_inputs.GlobalRadiation| as input and estimates |meteo_factors.SunshineDuration|,
while |meteo_glob_fao56| expects |meteo_inputs.SunshineDuration| as input and estimates
|meteo_fluxes.GlobalRadiation|.  Hence, please read the documentation on
|meteo_glob_fao56|.  The following explanations focus only on the differences between
both models.

Integration tests
=================

.. how_to_understand_integration_tests::

We design all integration tests similar to those of |meteo_glob_fao56|.  This time, we
select |meteo_factors.SunshineDuration| and |meteo_factors.PossibleSunshineDuration| as
output sequences:

>>> from hydpy import Element, Node
>>> from hydpy.aliases import meteo_factors_SunshineDuration, meteo_factors_PossibleSunshineDuration
>>> node1 = Node("node1", variable=meteo_factors_SunshineDuration)
>>> node2 = Node("node2", variable=meteo_factors_PossibleSunshineDuration)

>>> from hydpy.models.meteo_sun_fao56 import *
>>> parameterstep()
>>> element = Element("element", outputs=(node1, node2))
>>> element.model = model

.. _meteo_sun_fao56_daily_simulation:

daily simulation
________________

We repeat the :ref:`meteo_glob_fao56_daily_simulation` example of |meteo_glob_fao56|
but use its global radiation result as input:

>>> from hydpy import IntegrationTest, pub, round_
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> latitude(50.8)
>>> angstromconstant(0.25)
>>> angstromfactor(0.5)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.globalradiation.series = 255.367464

|meteo_sun_fao56| calculates the same radiation terms and a sunshine duration of
9.25 h, which is the input value used in the :ref:`meteo_glob_fao56_daily_simulation`
example of |meteo_glob_fao56|:

.. integration-test::

    >>> test()
    |       date | globalradiation | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | sunshineduration | extraterrestrialradiation | clearskysolarradiation | node1 |     node2 |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |      255.367464 |         0.967121 |         0.394547 |        2.106601 |            nan |                16.093247 |             9.25 |                475.201614 |              356.40121 |  9.25 | 16.093247 |

All getters specified by the |RadiationModel_V1| interface return the correct data.

>>> round_(model.get_possiblesunshineduration())
16.093247
>>> round_(model.get_sunshineduration())
9.25
>>> round_(model.get_clearskysolarradiation())
356.40121
>>> round_(model.get_globalradiation())
255.367464

.. _meteo_sun_fao56_hourly_simulation:

hourly simulation
_________________

We repeat the :ref:`meteo_glob_fao56_hourly_simulation` example of |meteo_glob_fao56|
but use its global radiation results as input:

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
...     0.0, 0.0, 0.0, 0.0, 115.964852, 328.283435, 517.046121, 669.389046, 774.930291,
...     826.477395, 820.517508, 757.456786, 641.592713, 480.821234, 286.098661,
...     80.296089, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     117.778042, 336.055513, 532.152561, 692.390544, 805.415479, 863.000911,
...     860.643794, 797.910345, 678.505661)

Again, there is a good agreement with the results of |meteo_glob_fao56|:

.. integration-test::

    >>> test("meteo_sun_fao56_hourly",
    ...      axis1=(factors.sunshineduration, factors.possiblesunshineduration))
    |             date | globalradiation | earthsundistance | solardeclination | sunsethourangle | solartimeangle | possiblesunshineduration | sunshineduration | extraterrestrialradiation | clearskysolarradiation |    node1 |    node2 |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2001-30-09 02:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.460182 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 03:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -2.198383 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 04:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -1.936583 |                      0.0 |              0.0 |                       0.0 |                    0.0 |      0.0 |      0.0 |
    | 2001-30-09 05:00 |             0.0 |         0.999717 |        -0.070087 |        1.550377 |      -1.674784 |                   0.0248 |              0.0 |                       0.0 |                    0.0 |      0.0 |   0.0248 |
    | 2001-30-09 06:00 |      115.964852 |         0.999717 |        -0.070087 |        1.550377 |      -1.412985 |                      1.0 |              0.8 |                178.407465 |             133.805599 |      0.8 |      1.0 |
    | 2001-30-09 07:00 |      328.283435 |         0.999717 |        -0.070087 |        1.550377 |      -1.151185 |                      1.0 |              0.8 |                505.051438 |             378.788578 |      0.8 |      1.0 |
    | 2001-30-09 08:00 |      517.046121 |         0.999717 |        -0.070087 |        1.550377 |      -0.889386 |                      1.0 |              0.8 |                795.455571 |             596.591678 |      0.8 |      1.0 |
    | 2001-30-09 09:00 |      669.389046 |         0.999717 |        -0.070087 |        1.550377 |      -0.627587 |                      1.0 |              0.8 |               1029.829301 |             772.371976 |      0.8 |      1.0 |
    | 2001-30-09 10:00 |      774.930291 |         0.999717 |        -0.070087 |        1.550377 |      -0.365787 |                      1.0 |              0.8 |               1192.200448 |             894.150336 |      0.8 |      1.0 |
    | 2001-30-09 11:00 |      826.477395 |         0.999717 |        -0.070087 |        1.550377 |      -0.103988 |                      1.0 |              0.8 |               1271.503685 |             953.627764 |      0.8 |      1.0 |
    | 2001-30-09 12:00 |      820.517508 |         0.999717 |        -0.070087 |        1.550377 |       0.157812 |                      1.0 |              0.8 |               1262.334627 |              946.75097 |      0.8 |      1.0 |
    | 2001-30-09 13:00 |      757.456786 |         0.999717 |        -0.070087 |        1.550377 |       0.419611 |                      1.0 |              0.8 |               1165.318132 |             873.988599 |      0.8 |      1.0 |
    | 2001-30-09 14:00 |      641.592713 |         0.999717 |        -0.070087 |        1.550377 |        0.68141 |                      1.0 |              0.8 |                987.065712 |             740.299284 |      0.8 |      1.0 |
    | 2001-30-09 15:00 |      480.821234 |         0.999717 |        -0.070087 |        1.550377 |        0.94321 |                      1.0 |              0.8 |                739.724976 |             554.793732 |      0.8 |      1.0 |
    | 2001-30-09 16:00 |      286.098661 |         0.999717 |        -0.070087 |        1.550377 |       1.205009 |                      1.0 |              0.8 |                440.151786 |             330.113839 |      0.8 |      1.0 |
    | 2001-30-09 17:00 |       80.296089 |         0.999717 |        -0.070087 |        1.550377 |       1.466809 |                 0.819208 |              0.8 |                108.761559 |              81.571169 |      0.8 | 0.819208 |
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
    | 2001-01-10 06:00 |      117.778042 |         1.000283 |        -0.076994 |        1.548357 |      -1.411603 |                      1.0 |         0.826667 |                177.554837 |             133.166127 | 0.826667 |      1.0 |
    | 2001-01-10 07:00 |      336.055513 |         1.000283 |        -0.076994 |        1.548357 |      -1.149804 |                      1.0 |         0.833333 |                 504.08327 |             378.062452 | 0.833333 |      1.0 |
    | 2001-01-10 08:00 |      532.152561 |         1.000283 |        -0.076994 |        1.548357 |      -0.888004 |                      1.0 |             0.84 |                794.257553 |             595.693165 |     0.84 |      1.0 |
    | 2001-01-10 09:00 |      692.390544 |         1.000283 |        -0.076994 |        1.548357 |      -0.626205 |                      1.0 |         0.846667 |               1028.302789 |             771.227092 | 0.846667 |      1.0 |
    | 2001-01-10 10:00 |      805.415479 |         1.000283 |        -0.076994 |        1.548357 |      -0.364405 |                      1.0 |         0.853333 |                1190.26918 |             892.701885 | 0.853333 |      1.0 |
    | 2001-01-10 11:00 |      863.000911 |         1.000283 |        -0.076994 |        1.548357 |      -0.102606 |                      1.0 |             0.86 |               1269.118986 |              951.83924 |     0.86 |      1.0 |
    | 2001-01-10 12:00 |      860.643794 |         1.000283 |        -0.076994 |        1.548357 |       0.159193 |                      1.0 |         0.866667 |               1259.478722 |             944.609042 | 0.866667 |      1.0 |
    | 2001-01-10 13:00 |      797.910345 |         1.000283 |        -0.076994 |        1.548357 |       0.420993 |                      1.0 |         0.873333 |               1162.005357 |             871.504018 | 0.873333 |      1.0 |
    | 2001-01-10 14:00 |      678.505661 |         1.000283 |        -0.076994 |        1.548357 |       0.682792 |                      1.0 |             0.88 |                983.341538 |             737.506154 |     0.88 |      1.0 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import radiationinterfaces
from hydpy.models.meteo import meteo_model


class Model(modeltools.AdHocModel, radiationinterfaces.RadiationModel_V1):
    """|meteo_sun_fao56.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Meteo-Sun-FAO56",
        description="sunshine duration estimation adopted from FAO56",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
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
    INTERFACE_METHODS = (
        meteo_model.Process_Radiation_V1,
        meteo_model.Get_PossibleSunshineDuration_V1,
        meteo_model.Get_SunshineDuration_V1,
        meteo_model.Get_ClearSkySolarRadiation_V1,
        meteo_model.Get_GlobalRadiation_V2,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
