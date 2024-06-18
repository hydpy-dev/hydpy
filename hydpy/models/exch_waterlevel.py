# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""|exch_waterlevel| informs its main model about the current water level simulated by
another model or passed in as a time series by the user.  Use it, for example, to
couple |wland_wag| and |dam_pump| so that the water level at a pumping station
(modelled by |dam_pump|) can affect the upstream groundwater level (modelled by
|wland_wag|).

Integration test
================

.. how_to_understand_integration_tests::

The only functionality of |exch_waterlevel| is querying water levels from a remote
node.  Hence, we include such a node in the following simple test setting, which does
not require further explanation:

>>> from hydpy.models.exch_waterlevel import *
>>> parameterstep()
>>> from hydpy import Element, Node
>>> node = Node("node", variable="WaterLevel")
>>> element = Element("element", receivers=node)
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"


.. integration-test::

    >>> node.sequences.sim.series = [2.0, 4.0]
    >>> test()
    |       date | node |
    ---------------------
    | 2000-01-01 |  2.0 |
    | 2000-02-01 |  4.0 |

>>> from hydpy import round_
>>> round_(model.get_waterlevel_v1())
4.0
"""
# import...

# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import stateinterfaces
from hydpy.models.exch import exch_model


class Model(modeltools.AdHocModel, stateinterfaces.WaterLevelModel_V1):
    """|exch_waterlevel.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-WL",
        description="submodel for querying the water level from a remote node",
    )

    INLET_METHODS = ()
    RECEIVER_METHODS = (exch_model.Get_WaterLevel_V1,)
    RUN_METHODS = ()
    INTERFACE_METHODS = (exch_model.Get_WaterLevel_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
