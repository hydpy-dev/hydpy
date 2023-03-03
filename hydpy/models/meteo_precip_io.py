# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""Submodel for reading precipitation data.

Use |meteo_precip_io| as a submodel for handing externally available precipitation time
series to main models like |evap_hbv96|.

Integration tests
=================

.. how_to_understand_integration_tests::

The only functionality of |meteo_precip_io| besides reading input time series is to
adjust the given values to multiple hydrological response units.  Hence, configuring
and testing it does not require additional explanations:

>>> from hydpy.models.meteo_precip_io import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> nmbhru(2)
>>> hruarea(0.2, 0.8)
>>> precipitationfactor(0.8, 1.2)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.precipitation.series = 1.0, 2.0

.. integration-test::

    >>> test()
    |       date | precipitation |      precipitation | meanprecipitation |
    -----------------------------------------------------------------------
    | 2000-01-01 |           1.0 | 0.8            1.2 |              1.12 |
    | 2000-02-01 |           2.0 | 1.6            2.4 |              2.24 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.meteo import meteo_model


class Model(meteo_model.Sub_PrecipModel_V2):
    """Precipitation reader version of HydPy-Meteo."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        meteo_model.Calc_Precipitation_V1,
        meteo_model.Adjust_Precipitation_V1,
        meteo_model.Calc_MeanPrecipitation_V1,
    )
    INTERFACE_METHODS = (
        meteo_model.Determine_Precipitation_V1,
        meteo_model.Get_Precipitation_V1,
        meteo_model.Get_MeanPrecipitation_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
