# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Submodel for reading reference evapotranspiration.

Use |evap_io| as a submodel for handing externally available time series of reference
evapotranspiration to main models like |lland_v1|.

Integration tests
=================

.. how_to_understand_integration_tests::

The only functionality of |evap_io| besides reading input time series is to adjust the
given values to multiple hydrological response units.  Hence, configuring and testing
it does not require additional explanations:

>>> from hydpy.models.evap_io import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> nmbhru(2)
>>> hruarea(0.2, 0.8)
>>> evapotranspirationfactor(0.8, 1.2)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.referenceevapotranspiration.series = 1.0, 2.0

.. integration-test::

    >>> test()
    |       date | referenceevapotranspiration |      referenceevapotranspiration | meanreferenceevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------
    | 2000-01-01 |                         1.0 | 0.8                          1.2 |                            1.12 |
    | 2000-02-01 |                         2.0 | 1.6                          2.4 |                            2.24 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.models.evap import evap_model
from hydpy.interfaces import petinterfaces


class Model(modeltools.AdHocModel, petinterfaces.PETModel_V1):
    """The input reader version of HydPy-Evap."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_ReferenceEvapotranspiration_V3,
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_MeanReferenceEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V1,
        evap_model.Get_MeanPotentialEvapotranspiration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
