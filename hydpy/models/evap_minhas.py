# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Model for converting potential evapotranspiration to different kinds of actual
evapotranspiration that essentially relies on the :cite:t:`ref-Minhas1974` equation.

|evap_minhas| serves as a submodel that supplies its main model with estimates of
evapotranspiration from soils and evaporation from interception storages and water
areas.  Therefore, it requires potential evapotranspiration data calculated by a
sub-submodel.  See, for example, the documentation of application model |lland_v1|,
where |evap_tw2002| calculates grass reference evapotranspiration values after
Turc-Wendling :cite:p:`ref-DVWK`, which |evap_mlc| converts to month- and land
type-specific potential evapotranspiration values.

Integration tests
=================

.. how_to_understand_integration_tests::

According to the intended usage as a submodel, |evap_minhas| requires no connections to
any nodes.  Hence, assigning a model instance to a blank |Element| instance is
sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_minhas import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

We perform the integration test for three simulation days:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

Besides the number of hydrological response units, which |evap_minhas| usually receives
from its main model in real applications, we only need to define values for the control
parameters |MaxSoilWater| and |DisseFactor|:

>>> nmbhru(1)
>>> maxsoilwater(200.0)
>>> dissefactor(5.0)

We add submodels of type |evap_io|, |dummy_interceptedwater|, and |dummy_soilwater| for
providing pre-defined values of potential evapotranspiration, intercepted water, and
soil water:

>>> with model.add_petmodel_v1("evap_io"):
...     hruarea(1.0)
...     evapotranspirationfactor(1.0)
>>> with model.add_intercmodel_v1("dummy_interceptedwater"):
...     pass
>>> with model.add_soilwatermodel_v1("dummy_soilwater"):
...     pass

Now we can initialise an |IntegrationTest| object:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m"

All of the following tests share the same input time series.  Reference
evapotranspiration (used as potential evapotranspiration) and the initial soil water
content are identical for all three days, while the initial amount of intercepted water
varies from 0 to 2 mm, of which the last value equals reference evaporation:

>>> model.petmodel.sequences.inputs.referenceevapotranspiration.series = 2.0
>>> model.intercmodel.sequences.inputs.interceptedwater.series = [[0.0], [1.0], [2.0]]
>>> model.soilwatermodel.sequences.inputs.soilwater.series = 100.0

.. _evap_minhas_vegetated_soil:

vegetated soil
______________

For "vegetated soils", interception evaporation and soil evapotranspiration are
relevant:

>>> interception(True)
>>> soil(True)
>>> water(False)

The results for the second day show that the sum of interception evaporation and soil
water evapotranspiration never exceeds the given potential evapotranspiration:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialevapotranspiration | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                         2.0 |              0.0 |                     0.0 |               1.717962 |
    | 02/01 |              1.0 |     100.0 |                         2.0 |              0.0 |                     1.0 |               0.858981 |
    | 03/01 |              2.0 |     100.0 |                         2.0 |              0.0 |                     2.0 |                    0.0 |


.. _evap_minhas_bare_soil:

bare soil
_________

Next, we assume a "bare soil" where interception processes are irrelevant:

>>> interception(False)
>>> soil(True)
>>> water(False)

Due to ignoring possible interception evaporation, soil water evapotranspiration is
identical for all three days:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialevapotranspiration | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                         2.0 |              0.0 |                     0.0 |               1.717962 |
    | 02/01 |              1.0 |     100.0 |                         2.0 |              0.0 |                     0.0 |               1.717962 |
    | 03/01 |              2.0 |     100.0 |                         2.0 |              0.0 |                     0.0 |               1.717962 |

.. _evap_minhas_sealed_soil:

sealed soil
___________

The following "sealed soil" can evaporate water from its surface but not from its body:

>>> interception(True)
>>> soil(False)
>>> water(False)

All results are as to be expected:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialevapotranspiration | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                         2.0 |              0.0 |                     0.0 |                    0.0 |
    | 02/01 |              1.0 |     100.0 |                         2.0 |              0.0 |                     1.0 |                    0.0 |
    | 03/01 |              2.0 |     100.0 |                         2.0 |              0.0 |                     2.0 |                    0.0 |

.. _evap_minhas_water_area:

water area
__________

A "water area" comes neither with a solid surface nor a soil body:

>>> interception(False)
>>> soil(False)
>>> water(True)

There is never any difference between potential and actual evaporation for water areas:

.. integration-test::

    >>> test()
    |  date | interceptedwater | soilwater | potentialevapotranspiration | waterevaporation | interceptionevaporation | soilevapotranspiration |
    --------------------------------------------------------------------------------------------------------------------------------------------
    | 01/01 |              0.0 |     100.0 |                         2.0 |              2.0 |                     0.0 |                    0.0 |
    | 02/01 |              1.0 |     100.0 |                         2.0 |              2.0 |                     0.0 |                    0.0 |
    | 03/01 |              2.0 |     100.0 |                         2.0 |              2.0 |                     0.0 |                    0.0 |
"""

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_PET_PETModel_V1,
    evap_model.Main_IntercModel_V1,
    evap_model.Main_SoilWaterModel_V1,
    evap_model.Sub_AETModel_V1,
):
    """The Minhas version of HydPy-Evap for calculating actual evapotranspiration."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Determine_InterceptionEvaporation_V1,
        evap_model.Determine_SoilEvapotranspiration_V2,
        evap_model.Determine_WaterEvaporation_V2,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_WaterEvaporation_V2,
        evap_model.Determine_InterceptionEvaporation_V1,
        evap_model.Determine_SoilEvapotranspiration_V2,
        evap_model.Get_WaterEvaporation_V1,
        evap_model.Get_InterceptionEvaporation_V1,
        evap_model.Get_SoilEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_PotentialEvapotranspiration_V4,
        evap_model.Calc_WaterEvaporation_V2,
        evap_model.Calc_InterceptedWater_V1,
        evap_model.Calc_InterceptionEvaporation_V1,
        evap_model.Calc_SoilWater_V1,
        evap_model.Calc_SoilEvapotranspiration_V2,
        evap_model.Calc_PotentialEvapotranspiration_PETModel_V1,
        evap_model.Calc_InterceptedWater_IntercModel_V1,
        evap_model.Calc_SoilWater_SoilWaterModel_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMODELS = ()

    petmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    intercmodel = modeltools.SubmodelProperty(stateinterfaces.IntercModel_V1)
    soilwatermodel = modeltools.SubmodelProperty(stateinterfaces.SoilWaterModel_V1)


tester = Tester()
cythonizer = Cythonizer()
