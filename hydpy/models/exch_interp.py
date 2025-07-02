# pylint: disable=line-too-long, unused-wildcard-import
"""|exch_interp| transfers information from an arbitrary number of observer nodes to
its main model (when used as a submodel) or to an arbitrary number of server nodes
(when used as a main model).  The data can be of arbitrary type but must be scalar and
can be modified by an interpolation function.  In cases where multiple observer nodes
are involved, |exch_interp| sums it up before passing it to the interpolation function.
In cases where multiple sender nodes are involved, they all receive the results of the
interpolation function.

A typical use case for |exch_interp| is to pass discharge information from a river
segment to a controlled detention basin model and thereby to transform the original
discharge values into release values suitable for flood protection.  Due to relying on
the observer node mechanism, this information reaches the detention basin immediately
so that it can adjust its release in the same simulation time step.  But, in contrast
to using the "slower" receiver mechanism, it prevents from taking information from
downstream river segments.

Integration test
================

.. how_to_understand_integration_tests::

|exch_interp| is primarily designed to be used as a submodel, as demonstrated in some
integration tests of the application model |dam_detention|.  Here, we focus on its
usage as a main model.

The selection of the relevant observer nodes relies on their names, which allows one
main model to handle multiple |exch_interp| submodels connected with different observer
nodes.  Therefore, their |Node.variable| property can be set arbitrarily (a more
descriptive string than the following would be advisable, of course):

>>> from hydpy import Element, IntegrationTest, Nodes, PPoly, pub
>>> in1, in2 = Nodes("in1", "in2", defaultvariable="arbitrary")

In contrast, connections to the sender nodes are established with the standard
variable-based approach:

>>> out1, out2 = Nodes("out1", "out2", defaultvariable="Y")
>>> element = Element("element", observers=("in1", "in2"), senders=("out1", "out2"))

Due to the name-based approach, we must specify the relevant names building the
connections:

>>> from hydpy.models.exch_interp import *
>>> parameterstep()
>>> element.model = model
Traceback (most recent call last):
...
RuntimeError: While trying to build the node connection of the `observer` sequences of the model handled by element `element`, the following error occurred: The observer sequence `x` of element `element` does not know the names of the observer nodes it should be connected with.  Consider providing this information via the control parameter `observernodes`.

>>> observernodes("in2", "in1")
>>> element.model = model

You can use the helper classes |PPoly| or |ANN| to configure parameter |X2Y| so that
|exch_interp| performs stepwise linear, spline, or neural network-based interpolations:

>>> x2y(PPoly.from_data([0.0, 1.0], [2.0, 4.0]))

As |exch_interp| is quite simple, it needs no more special configuration.  Hence, we
can finally define the simulation period, prepare an |IntegrationTest| instance, and
assign input data to both observer nodes:

>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> in1.sequences.sim.series = [0.0, 0.4]
>>> in2.sequences.sim.series = [0.0, 0.6]

Due to the simplicity of the discussed model, the following test results should contain
no surprises:

.. integration-test::

    >>> test()
    |       date |   x |   y | in1 | in2 | out1 | out2 |
    ----------------------------------------------------
    | 2000-01-01 | 0.0 | 2.0 | 0.0 | 0.0 |  2.0 |  2.0 |
    | 2000-02-01 | 1.0 | 4.0 | 0.4 | 0.6 |  4.0 |  4.0 |

>>> from hydpy import round_
>>> round_(model.get_y_v1())
4.0
"""

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.models.exch import exch_model
from hydpy.interfaces import exchangeinterfaces


class Model(modeltools.AdHocModel, exchangeinterfaces.ExchangeModel_V1):
    """|exch_interp.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Interp",
        description=(
            "model for exchanging arbitrary scalar data and modifying it with an "
            "interpolation function"
        ),
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = ()
    OBSERVER_METHODS = (exch_model.Pick_X_V1,)
    RECEIVER_METHODS = ()
    INTERFACE_METHODS = (exch_model.Determine_Y_V1, exch_model.Get_Y_V1)
    RUN_METHODS = (exch_model.Calc_Y_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = (exch_model.Pass_Y_V1,)
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
