# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""Submodel for reading global radiation data.

Use |meteo_glob_io| as a submodel for supplying (relative) main models like
|evap_ret_tw2002| with externally available global radiation time series.

Integration test
================

.. how_to_understand_integration_tests::

The only functionality of |meteo_glob_io| is to read the input time series of global
radiation.  Hence, configuring and testing it does not require additional explanations:

>>> from hydpy.models.meteo_glob_io import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.globalradiation.series = 200.0, 400.0

.. integration-test::

    >>> test()
    |       date | globalradiation |
    --------------------------------
    | 2000-01-01 |           200.0 |
    | 2000-02-01 |           400.0 |

>>> from hydpy import round_
>>> round_(model.get_globalradiation())
400.0
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import radiationinterfaces
from hydpy.models.meteo import meteo_model


class Model(modeltools.AdHocModel, radiationinterfaces.RadiationModel_V2):
    """Global radiation reader version of HydPy-Meteo."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (meteo_model.Get_GlobalRadiation_V2,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
