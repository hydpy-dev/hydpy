# pylint: disable=unused-wildcard-import
"""
.. _`LARSIM`: http://www.larsim.de/en/the-model/

|dummy_node2node| serves as a placeholder model.  In each simulation step, it simply
sums up its inputs and hands the resulting value to the downstream node without
modifications.

In *HydPy*, it is fairly easy to introduce additional |Element| objects and thus bring
new models of arbitrary types into existing network structures.  Hence, there is
typically no need to define dummy elements or models in anticipation of possible future
changes.  However, application model |dummy_node2node| can help to more closely reflect
the actual network structures of other model systems as `LARSIM`_, which are more
restrictive regarding future changes and network complexity.

Integration test
================

    .. how_to_understand_integration_tests::

    We prepare a simulation period of three days:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

    The model object does not require any parameter information:

    >>> from hydpy.models.dummy_node2node import *
    >>> parameterstep()

    We add the model object to an element connected to two inlet nodes and one outlet
    node and prepare a runnable test object:

    >>> from hydpy import Element, IntegrationTest
    >>> element = Element("element",
    ...                   inlets=("inlet1", "inlet2"),
    ...                   outlets="outlet")
    >>> element.model = model
    >>> test = IntegrationTest(element)

    After defining two input series, we can demonstrate that each pair of values of the
    inlet nodes is summed up and handed to the outlet node:

    >>> element.inlets.inlet1.sequences.sim.series = 0.0, 1.0, 2.0
    >>> element.inlets.inlet2.sequences.sim.series = 0.0, 2.0, -4.0
    >>> test()
    |                date |    q | inlet1 | inlet2 | outlet |
    ---------------------------------------------------------
    | 2000-01-01 00:00:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 2000-01-02 00:00:00 |  3.0 |    1.0 |    2.0 |    3.0 |
    | 2000-01-03 00:00:00 | -2.0 |    2.0 |   -4.0 |   -2.0 |
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from dummy
from hydpy.models.dummy import dummy_model


class Model(modeltools.AdHocModel):
    """|dummy_node2node.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Dummy-Node2Node",
        description="dummy model passing data from inlet to outlet nodes",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (dummy_model.Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    ADD_METHODS = ()
    OUTLET_METHODS = (dummy_model.Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
