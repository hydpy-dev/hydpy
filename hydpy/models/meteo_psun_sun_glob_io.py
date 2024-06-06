# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""Submodel for reading possible sunshine duration, sunshine duration, and global
radiation data.

Use |meteo_psun_sun_glob_io| as a submodel for supplying (relative) main models like
|evap_pet_ambav1| with externally available clear-sky solar radiation and global
radiation time series.

Integration test
================

.. how_to_understand_integration_tests::

The only functionality of |meteo_psun_sun_glob_io| is to read the input time series of
possible sunshine duration, actual sunshine duration, and global radiation.  Hence,
configuring and testing it does not require additional explanations:

>>> from hydpy.models.meteo_psun_sun_glob_io import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.possiblesunshineduration.series = 10.0, 12.0
>>> inputs.sunshineduration.series = 5.0, 6.0
>>> inputs.globalradiation.series = 100.0, 200.0

.. integration-test::

    >>> test()
    |       date | possiblesunshineduration | sunshineduration | globalradiation |
    ------------------------------------------------------------------------------
    | 2000-01-01 |                     10.0 |              5.0 |           100.0 |
    | 2000-02-01 |                     12.0 |              6.0 |           200.0 |

>>> from hydpy import round_
>>> round_(model.get_possiblesunshineduration())
12.0
>>> round_(model.get_sunshineduration())
6.0
>>> round_(model.get_globalradiation())
200.0
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import radiationinterfaces
from hydpy.models.meteo import meteo_model


class Model(modeltools.AdHocModel, radiationinterfaces.RadiationModel_V4):
    """Possible sunshine duration, actual sunshine duration, and global radiation
    reader version of HydPy-Meteo."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        meteo_model.Get_PossibleSunshineDuration_V2,
        meteo_model.Get_SunshineDuration_V2,
        meteo_model.Get_GlobalRadiation_V2,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
