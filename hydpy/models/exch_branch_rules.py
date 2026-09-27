# pylint: disable=line-too-long, unused-wildcard-import
"""
|exch_branch_rules| allows branching the summed input from some inlet nodes to an
arbitrary number of outlet nodes. The original HBV96 implementation is supposed to
split inflowing discharge, but |exch_branch_rules| is suitable for splitting arbitrary
variables. Calculations are performed for each branch individually by linear
interpolation (or extrapolation) following tabulated supporting points.  Additionally,
|exch_branch_rules| allows adjusting the input data with differences that can vary
monthly.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 11:00", "1h"

|exch_branch_rules| has no parameter with values depending on the simulation step size,
which is why we can pass anything (or nothing) to function |parameterstep| without
changing the following results:

>>> from hydpy.models.exch_branch_rules import *
>>> parameterstep()

|exch_branch_rules| queries inflow from two inlet |Node| objects and passes the
branched outflow to three outlet |Node| objects.  Thus, In contrast to most other
application models, we need to define the parameter values before connecting the
model to its |Element| object, called `branch`:

>>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
>>> branch = Element("branch",
...                  inlets=["input1", "input2"],
...                  outlets=["output1", "output2", "output3"])
>>> rules(
...     PPolys(
...         output1=PPoly.from_data(xs=[0.0, 2.0], ys=[0.0, 1.0]),
...         output2=PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 1.0, 0.0, 0.0]),
...         output3=PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 2.0, 6.0]),
...     )
... )
>>> branch.model = model

We do not have to define any initial values in the test settings because the
|exch_branch_rules| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%H:%M"

The (identical) values of the inlet nodes `input1` and `input2` define no realistic
inflow series.  Instead, they serve to show the behaviour of |exch_branch_rules| within
and outside the current range defined by parameter |XPoints|:

>>> import numpy
>>> nodes.input1.sequences.sim.series = numpy.arange(-2.0, 9.0)
>>> nodes.input2.sequences.sim.series = 0.0
>>> nodes.input2.sequences.sim.series[0] = 1.0

`output1` shows linear continuations below and above the current range of parameter
|XPoints|. `output2` points out that inverse relationships are allowed. `output3` shows
that |exch_branch_rules| does not enforce equality between the total sum of input and
output values:

.. integration-test::

    >>> test("exch_branch_rules_ex1")
    |  date | originalinput |             outputs | input1 | input2 | output1 | output2 | output3 |
    -----------------------------------------------------------------------------------------------
    | 00:00 |          -1.0 | -0.5  -0.5      0.0 |   -2.0 |    1.0 |    -0.5 |    -0.5 |     0.0 |
    | 01:00 |          -1.0 | -0.5  -0.5      0.0 |   -1.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 02:00 |           0.0 |  0.0   0.0      0.0 |    0.0 |    0.0 |     0.0 |     0.0 |     0.0 |
    | 03:00 |           1.0 |  0.5   0.5      0.0 |    1.0 |    0.0 |     0.5 |     0.5 |     0.0 |
    | 04:00 |           2.0 |  1.0   1.0      0.0 |    2.0 |    0.0 |     1.0 |     1.0 |     0.0 |
    | 05:00 |           3.0 |  1.5   0.5      1.0 |    3.0 |    0.0 |     1.5 |     0.5 |     1.0 |
    | 06:00 |           4.0 |  2.0   0.0      2.0 |    4.0 |    0.0 |     2.0 |     0.0 |     2.0 |
    | 07:00 |           5.0 |  2.5   0.0      4.0 |    5.0 |    0.0 |     2.5 |     0.0 |     4.0 |
    | 08:00 |           6.0 |  3.0   0.0      6.0 |    6.0 |    0.0 |     3.0 |     0.0 |     6.0 |
    | 09:00 |           7.0 |  3.5   0.0      8.0 |    7.0 |    0.0 |     3.5 |     0.0 |     8.0 |
    | 10:00 |           8.0 |  4.0   0.0     10.0 |    8.0 |    0.0 |     4.0 |     0.0 |    10.0 |


>>> rules(
...     PPolys(
...         output1=1,
...         output2=PPoly.from_data(xs=[0.0, 6.0, 7.0], ys=[0.0, 0.0, 1.0]),
...         output3=PPoly.from_data(xs=[-1.0, 0.0, 4.0, 6.0], ys=[-1.0, -1.0, 0.0, 0.0]),
...     )
... )
>>> branch.model.connect()

.. integration-test::

    >>> test("exch_branch_rules_ex2")
    |  date | originalinput |            outputs | input1 | input2 | output1 | output2 | output3 |
    ----------------------------------------------------------------------------------------------
    | 00:00 |          -1.0 |  0.0  0.0     -1.0 |   -2.0 |    1.0 |     0.0 |     0.0 |    -1.0 |
    | 01:00 |          -1.0 |  0.0  0.0     -1.0 |   -1.0 |    0.0 |     0.0 |     0.0 |    -1.0 |
    | 02:00 |           0.0 |  1.0  0.0     -1.0 |    0.0 |    0.0 |     1.0 |     0.0 |    -1.0 |
    | 03:00 |           1.0 | 1.75  0.0    -0.75 |    1.0 |    0.0 |    1.75 |     0.0 |   -0.75 |
    | 04:00 |           2.0 |  2.5  0.0     -0.5 |    2.0 |    0.0 |     2.5 |     0.0 |    -0.5 |
    | 05:00 |           3.0 | 3.25  0.0    -0.25 |    3.0 |    0.0 |    3.25 |     0.0 |   -0.25 |
    | 06:00 |           4.0 |  4.0  0.0      0.0 |    4.0 |    0.0 |     4.0 |     0.0 |     0.0 |
    | 07:00 |           5.0 |  5.0  0.0      0.0 |    5.0 |    0.0 |     5.0 |     0.0 |     0.0 |
    | 08:00 |           6.0 |  6.0  0.0      0.0 |    6.0 |    0.0 |     6.0 |     0.0 |     0.0 |
    | 09:00 |           7.0 |  6.0  1.0      0.0 |    7.0 |    0.0 |     6.0 |     1.0 |     0.0 |
    | 10:00 |           8.0 |  6.0  2.0      0.0 |    8.0 |    0.0 |     6.0 |     2.0 |     0.0 |

>>> rule1 = PPolys(
...     output1=1,
...     output2=PPoly.from_data(xs=[-1.0, 0.0, 1.0], ys=[0.0, 0.0, 0.5]),
...     output3=PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.0]),
... )
>>> rule2 = PPolys(
...     output1=1,
...     output2=PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.0]),
...     output3=PPoly.from_data(xs=[-1.0, 0.0, 1.0], ys=[0.0, 0.0, 0.5]),
... )
>>> rules(
...     toy_01_01_00_30=rule1,
...     toy_01_01_04_30=rule1,
...     toy_01_01_09_30=rule2,
...     toy_12_31_23_30=rule2,
... )
>>> branch.model.connect()

.. integration-test::

    >>> test("exch_branch_rules_ex3")
    |  date | originalinput |            outputs | input1 | input2 | output1 | output2 | output3 |
    ----------------------------------------------------------------------------------------------
    | 00:00 |          -1.0 | -1.0  0.0      0.0 |   -2.0 |    1.0 |    -1.0 |     0.0 |     0.0 |
    | 01:00 |          -1.0 | -1.0  0.0      0.0 |   -1.0 |    0.0 |    -1.0 |     0.0 |     0.0 |
    | 02:00 |           0.0 |  0.0  0.0      0.0 |    0.0 |    0.0 |     0.0 |     0.0 |     0.0 |
    | 03:00 |           1.0 |  0.5  0.5      0.0 |    1.0 |    0.0 |     0.5 |     0.5 |     0.0 |
    | 04:00 |           2.0 |  1.0  1.0      0.0 |    2.0 |    0.0 |     1.0 |     1.0 |     0.0 |
    | 05:00 |           3.0 |  1.5  1.2      0.3 |    3.0 |    0.0 |     1.5 |     1.2 |     0.3 |
    | 06:00 |           4.0 |  2.0  1.2      0.8 |    4.0 |    0.0 |     2.0 |     1.2 |     0.8 |
    | 07:00 |           5.0 |  2.5  1.0      1.5 |    5.0 |    0.0 |     2.5 |     1.0 |     1.5 |
    | 08:00 |           6.0 |  3.0  0.6      2.4 |    6.0 |    0.0 |     3.0 |     0.6 |     2.4 |
    | 09:00 |           7.0 |  3.5  0.0      3.5 |    7.0 |    0.0 |     3.5 |     0.0 |     3.5 |
    | 10:00 |           8.0 |  4.0  0.0      4.0 |    8.0 |    0.0 |     4.0 |     0.0 |     4.0 |

"""

from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly, PPolys  # pylint: disable=unused-import
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.exe.modelimports import *
from hydpy.models.exch import exch_model


class Model(modeltools.AdHocModel):
    """|exch_branch_rules.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Branch-Rules", description="branching based on piecewise interpolation rules"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (exch_model.Pick_OriginalInput_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (exch_model.Calc_Outputs_V3,)
    ADD_METHODS = ()
    OUTLET_METHODS = (exch_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    nodenames: list[str]
    """Names of the output nodes."""

    def __init__(self) -> None:
        super().__init__()
        self.nodenames = []

    def connect(self) -> None:

        inlets = self.element.inlets
        total = self.sequences.inlets.total
        if exceptiontools.getattr_(total, "shape", None) != (len(inlets),):
            total.node2idx = {}
        total.shape = len(inlets)
        for idx, node in enumerate(inlets):
            double = node.get_double("inlets")
            total.set_pointer(double, idx)
            total.node2idx[node] = idx

        branched = self.sequences.outlets.branched
        branched.node2idx = {}
        for idx, name in enumerate(self.nodenames):
            try:
                outlet = getattr(self.element.outlets, name)
            except AttributeError:
                raise RuntimeError(
                    f"Model {objecttools.elementphrase(self)} tried to connect to an "
                    f"outlet node named `{name}`, which is not an available outlet "
                    f"node of element `{self.element.name}`."
                ) from None
            double = outlet.get_double("outlets")
            branched.set_pointer(double, idx)
            branched.node2idx[outlet] = idx


tester = Tester()
cythonizer = Cythonizer()
