# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Submodel for month-based adjusting of reference evapotranspiration.

Use |evap_m| as a plug-in between a main model like |lland_v1| and another submodel
like |evap_tw2002| to adjust the reference evapotranspiration given by |evap_tw2002| by
month.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_m| requires no input from another model and does not supply any
outlet sequence.  Hence, assigning a model instance to a blank |Element| instance is
sufficient:

>>> from hydpy.models.evap_m import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

In our simple test-setting, the submodel of type |evap_io| supplies different
reference evapotranspiration values for two hydrological response units for the last
of January and the first of February 2000.  |evap_m| applies individual adjustment
factors for both months:

>>> from hydpy import pub
>>> pub.timegrids = "2000-01-31", "2000-02-02", "1d"
>>> nmbhru(2)
>>> hruarea(0.2, 0.8)
>>> monthfactor.jan = 0.5
>>> monthfactor.feb = 2.0
>>> with model.add_retmodel_v1("evap_io"):
...     evapotranspirationfactor(0.8, 1.2)
>>>
>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>>
>>> model.retmodel.sequences.inputs.referenceevapotranspiration.series = 1.0, 2.0

.. integration-test::

    >>> test()
    |       date |      referenceevapotranspiration |      potentialevapotranspiration | meanpotentialevapotranspiration |
    ----------------------------------------------------------------------------------------------------------------------
    | 2000-31-01 | 0.8                          1.2 | 0.4                          0.6 |                            0.56 |
    | 2000-01-02 | 1.6                          2.4 | 3.2                          4.8 |                            4.48 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.models.evap import evap_model


class Model(evap_model.Main_PETModel_V1, evap_model.Sub_PETModel_V1):
    """HydPy-Evap-M (month-based adjustment of reference evapotranspiration)."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_ReferenceEvapotranspiration_V4,
        evap_model.Calc_PotentialEvapotranspiration_V1,
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
