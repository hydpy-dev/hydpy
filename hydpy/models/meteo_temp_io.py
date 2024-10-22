# pylint: disable=unused-wildcard-import
"""Use |meteo_temp_io| as a submodel tp supply (relative) main models like
|evap_pet_hbv96| with externally available temperature time series.

Integration tests
=================

.. how_to_understand_integration_tests::

The only functionality of |meteo_temp_io| besides reading input time series is to
adjust the given values to multiple hydrological response units.  Hence, configuring
and testing it does not require additional explanations:

>>> from hydpy.models.meteo_temp_io import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> nmbhru(2)
>>> hruarea(0.2, 0.8)
>>> temperatureaddend(-0.6, -1.2)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.temperature.series = 2.0, 4.0

.. integration-test::

    >>> test()
    |       date | temperature |      temperature | meantemperature |
    -----------------------------------------------------------------
    | 2000-01-01 |         2.0 | 1.4          0.8 |            0.92 |
    | 2000-02-01 |         4.0 | 3.4          2.8 |            2.92 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.models.meteo import meteo_model
from hydpy.interfaces import tempinterfaces


class Model(meteo_model.Sub_BaseModel, tempinterfaces.TempModel_V2):
    """|meteo_temp_io.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Meteo-Temp-IO", description="external temperature data"
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        meteo_model.Calc_Temperature_V1,
        meteo_model.Adjust_Temperature_V1,
        meteo_model.Calc_MeanTemperature_V1,
    )
    INTERFACE_METHODS = (
        meteo_model.Determine_Temperature_V1,
        meteo_model.Get_Temperature_V1,
        meteo_model.Get_MeanTemperature_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
