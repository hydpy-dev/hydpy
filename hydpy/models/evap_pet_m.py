# pylint: disable=line-too-long, unused-wildcard-import
"""
Use |evap_pet_m| as a plug-in between a main model like |lland_dd| and another submodel
like |evap_ret_tw2002| to adjust the reference evapotranspiration given by
|evap_ret_tw2002| by month.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_pet_m| requires no input from another model and does not supply
any outlet sequence.  Hence, assigning a model instance to a blank |Element| instance
is sufficient:

>>> from hydpy.models.evap_pet_m import *
>>> parameterstep("1d")
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

In our simple test-setting, the submodel of type |evap_ret_io| supplies different
reference evapotranspiration values for two hydrological response units for the last
of January and the first of February 2000.  |evap_pet_m| applies individual adjustment
factors for both months and "damps" the second unit's result value:

>>> from hydpy import pub
>>> pub.timegrids = "2000-01-31", "2000-02-02", "1d"
>>> nmbhru(2)
>>> hruarea(0.2, 0.8)
>>> monthfactor.jan = 0.5
>>> monthfactor.feb = 2.0
>>> dampingfactor(1.0, 0.5)
>>> with model.add_retmodel_v1("evap_ret_io"):
...     evapotranspirationfactor(0.8, 1.2)
>>>
>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> test.inits = ((model.sequences.logs.loggedpotentialevapotranspiration, 0.6),)
>>>
>>> model.retmodel.sequences.inputs.referenceevapotranspiration.series = 1.0, 2.0

.. integration-test::

    >>> test()
    |       date |      referenceevapotranspiration |      potentialevapotranspiration | meanpotentialevapotranspiration |
    ----------------------------------------------------------------------------------------------------------------------
    | 2000-31-01 | 0.8                          1.2 | 0.4                          0.6 |                            0.56 |
    | 2000-01-02 | 1.6                          2.4 | 3.2                          2.7 |                             2.8 |
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
    """|evap_pet_m.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-PET-M",
        description="month-based adjustment of reference evapotranspiration",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_ReferenceEvapotranspiration_V4,
        evap_model.Calc_PotentialEvapotranspiration_V1,
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
