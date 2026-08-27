# pylint: disable=unused-wildcard-import
"""Use |meteo_throughfall_io| as a submodel to supply (relative) main models like
|snow_dd| with externally available throughfall time series.

Integration tests
=================

.. how_to_understand_integration_tests::

|meteo_throughfall_io| provides the data as given, without modification.  Hence,
configuring and testing it does not require additional explanations:

>>> from hydpy.models.meteo_throughfall_io import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> nmbhru(2)

>>> parameters.update()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.throughfall.series = [[1.0, 2.0], [4.0, 3.0]]

.. integration-test::

    >>> test()
    |       date |      throughfall |
    ---------------------------------
    | 2000-01-01 | 1.0          2.0 |
    | 2000-02-01 | 4.0          3.0 |
"""

from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.models.meteo import meteo_control
from hydpy.models.meteo import meteo_model
from hydpy.interfaces import throughfallinterfaces

ADDITIONAL_CONTROLPARAMETERS = (meteo_control.NmbHRU,)


class Model(meteo_model.Sub_BaseModel, throughfallinterfaces.ThroughfallModel_V2):
    """|meteo_throughfall_io.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Meteo-Throughfall-IO", description="external throughfall data"
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (meteo_model.Get_Throughfall_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
