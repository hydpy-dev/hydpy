# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Use |evap_pet_mlc| as a plug-in between a main model like |lland_dd| and another
submodel like |evap_ret_tw2002| to adjust the reference evapotranspiration given by
|evap_ret_tw2002| by month and land cover.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_pet_mlc| does not define any land cover types by itself but
takes the ones of the respective main model.  Here, we manually introduce the land
cover types of grass, trees, and water to apply |evap_pet_mlc| as a stand-alone model:

>>> from hydpy.core.parametertools import Constants
>>> GRASS, TREES, WATER = 0, 1, 2
>>> constants = Constants(GRASS=GRASS, TREES=TREES, WATER=WATER)
>>> from hydpy.models.evap.evap_control import HRUType, LandMonthFactor
>>> with HRUType.modify_constants(constants), LandMonthFactor.modify_rows(constants):
...     from hydpy.models.evap_pet_mlc import *
...     parameterstep()

Application model |evap_pet_mlc| requires no input from another model and does not
supply any outlet sequence.  Hence, assigning a model instance to a blank |Element|
instance is sufficient:

>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

In our simple test-setting, the submodel of type |evap_ret_io| supplies different
reference evapotranspiration values for two hydrological response units of type "trees"
and "water" for the last of January and the first of February 2000.  |evap_pet_mlc|
applies individual adjustment factors for both months and land cover types and "damps"
the second unit's result value:

>>> from hydpy import pub
>>> pub.timegrids = "2000-01-31", "2000-02-02", "1d"
>>> nmbhru(2)
>>> hrutype(TREES, WATER)
>>> hruarea(0.2, 0.8)
>>> landmonthfactor.trees_jan = 1.2
>>> landmonthfactor.trees_feb = 1.4
>>> landmonthfactor.water_jan = 1.6
>>> landmonthfactor.water_feb = 1.8
>>> dampingfactor(1.0, 0.5)
>>> with model.add_retmodel_v1("evap_ret_io"):
...     evapotranspirationfactor(0.8, 1.2)
>>>
>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> test.inits = ((model.sequences.logs.loggedpotentialevapotranspiration, 1.92),)
>>>
>>> model.retmodel.sequences.inputs.referenceevapotranspiration.series = 1.0, 2.0

.. integration-test::

    >>> test()
    |       date |      referenceevapotranspiration |       potentialevapotranspiration | meanpotentialevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------
    | 2000-31-01 | 0.8                          1.2 | 0.96                         1.92 |                           1.728 |
    | 2000-01-02 | 1.6                          2.4 | 2.24                         3.12 |                           2.944 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_RET_PETModel_V1, evap_model.Sub_ETModel, petinterfaces.PETModel_V1
):
    """|evap_pet_mlc.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-PET-M-LC",
        description="month-based land cover adjustment of reference evapotranspiration",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_ReferenceEvapotranspiration_V4,
        evap_model.Calc_PotentialEvapotranspiration_V2,
        evap_model.Update_PotentialEvapotranspiration_V1,
        evap_model.Calc_MeanPotentialEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V2,
        evap_model.Get_MeanPotentialEvapotranspiration_V2,
    )
    ADD_METHODS = (evap_model.Calc_ReferenceEvapotranspiration_PETModel_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMODELS = ()

    retmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)


tester = Tester()
cythonizer = Cythonizer()
