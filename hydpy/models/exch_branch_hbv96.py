# pylint: disable=line-too-long, unused-wildcard-import
"""
|exch_branch_hbv96| allows branching the summed input from some inlet nodes to an
arbitrary number of outlet nodes. The original HBV96 implementation is supposed to
split inflowing discharge, but |exch_branch_hbv96| is suitable for splitting arbitrary
variables. Calculations are performed for each branch individually by linear
interpolation (or extrapolation) following tabulated supporting points.  Additionally,
|exch_branch_hbv96| allows adjusting the input data with differences that can vary
monthly.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "01.01.2000 00:00", "01.01.2000 11:00", "1h"

|exch_branch_hbv96| has no parameter with values depending on the simulation step size,
which is why we can pass anything (or nothing) to function |parameterstep| without
changing the following results:

>>> from hydpy.models.exch_branch_hbv96 import *
>>> parameterstep()

|exch_branch_hbv96| queries inflow from two inlet |Node| objects and passes the
branched outflow to three outlet |Node| objects.  Thus, In contrast to most other
application models, we need to define the parameter values before connecting the
model to its |Element| object, called `branch`:

>>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
>>> branch = Element("branch",
...                  inlets=["input1", "input2"],
...                  outlets=["output1", "output2", "output3"])
>>> delta(-1.0)
>>> minimum(-1.0)
>>> xpoints(0.0, 2.0, 4.0, 6.0)
>>> ypoints(output1=[0.0, 1.0, 2.0, 3.0],
...         output2=[0.0, 1.0, 0.0, 0.0],
...         output3=[0.0, 0.0, 2.0, 6.0])
>>> branch.model = model

We do not have to define any initial values in the test settings because the
|exch_branch_hbv96| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%H:%M"

The (identical) values of the inlet nodes `input1` and `input2` define no realistic
inflow series.  Instead, they serve to show the behaviour of |exch_branch_hbv96| within
and outside the current range defined by parameter |XPoints|:

>>> import numpy
>>> nodes.input1.sequences.sim.series = numpy.arange(-1.0, 10.0)/2
>>> nodes.input2.sequences.sim.series = numpy.arange(-1.0, 10.0)/2

`output1` shows linear continuations below and above the current range of parameter
|XPoints|. `output2` points out that inverse relationships are allowed. `output3` shows
that |exch_branch_hbv96| does not enforce equality between the total sum of input and
output values:

.. integration-test::

    >>> test("exch_branch_hbv96_ex1")
    |  date | originalinput | adjustedinput |             outputs | input1 | input2 | output1 | output2 | output3 |
    ---------------------------------------------------------------------------------------------------------------
    | 00:00 |          -1.0 |          -1.0 | -0.5  -0.5      0.0 |   -0.5 |   -0.5 |    -0.5 |    -0.5 |     0.0 |
    | 01:00 |           0.0 |          -1.0 | -0.5  -0.5      0.0 |    0.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 02:00 |           1.0 |           0.0 |  0.0   0.0      0.0 |    0.5 |    0.5 |     0.0 |     0.0 |     0.0 |
    | 03:00 |           2.0 |           1.0 |  0.5   0.5      0.0 |    1.0 |    1.0 |     0.5 |     0.5 |     0.0 |
    | 04:00 |           3.0 |           2.0 |  1.0   1.0      0.0 |    1.5 |    1.5 |     1.0 |     1.0 |     0.0 |
    | 05:00 |           4.0 |           3.0 |  1.5   0.5      1.0 |    2.0 |    2.0 |     1.5 |     0.5 |     1.0 |
    | 06:00 |           5.0 |           4.0 |  2.0   0.0      2.0 |    2.5 |    2.5 |     2.0 |     0.0 |     2.0 |
    | 07:00 |           6.0 |           5.0 |  2.5   0.0      4.0 |    3.0 |    3.0 |     2.5 |     0.0 |     4.0 |
    | 08:00 |           7.0 |           6.0 |  3.0   0.0      6.0 |    3.5 |    3.5 |     3.0 |     0.0 |     6.0 |
    | 09:00 |           8.0 |           7.0 |  3.5   0.0      8.0 |    4.0 |    4.0 |     3.5 |     0.0 |     8.0 |
    | 10:00 |           9.0 |           8.0 |  4.0   0.0     10.0 |    4.5 |    4.5 |     4.0 |     0.0 |    10.0 |
"""
# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.exe.modelimports import *

# ...from exch
from hydpy.models.exch import exch_model


class Model(modeltools.AdHocModel):
    """|exch_branch_hbv96.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Branch-HBV96", description="branch model adopted from IHMS-HBV96"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (exch_model.Pick_OriginalInput_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (exch_model.Calc_AdjustedInput_V1, exch_model.Calc_Outputs_V1)
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
        """Connect the |LinkSequence| instances handled by the actual model to the
        |NodeSequence| instances handled by one inlet node and multiple outlet nodes.

        |exch_branch_hbv96| passes multiple output values to different outlet nodes,
        which requires additional information regarding the "direction" of each output
        value.  Therefore, it uses node names as keywords.  Assume the discharge values
        of both nodes `inflow1` and `inflow2`  shall be  branched to nodes `outflow1`
        and `outflow2` via element `branch`:

        >>> from hydpy import Element, pub
        >>> branch = Element("mybranch",
        ...                  inlets=["inflow1", "inflow2"],
        ...                  outlets=["outflow1", "outflow2"])

        Then, parameter |YPoints| relates different supporting points via keyword
        arguments to the respective nodes:

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.exch_branch_hbv96 import *
        >>> parameterstep()
        >>> delta(0.0)
        >>> xpoints(0.0, 3.0)
        >>> ypoints(outflow1=[0.0, 1.0], outflow2=[0.0, 2.0])
        >>> parameters.update()

        After connecting the model with its element, the total discharge value of nodes
        `inflow1` and `inflow2` can be adequately divided:

        >>> branch.model = model
        >>> branch.inlets.inflow1.sequences.sim = 1.0
        >>> branch.inlets.inflow2.sequences.sim = 5.0
        >>> model.simulate(0)
        >>> branch.outlets.outflow1.sequences.sim
        sim(2.0)
        >>> branch.outlets.outflow2.sequences.sim
        sim(4.0)

        The following error is raised in case of missing (or misspelt) outlet nodes:

        >>> branch.outlets.remove_device(branch.outlets.outflow1, force=True)
        >>> parameters.update()
        >>> model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: Model `exch_branch_hbv96` of element `mybranch` tried to \
connect to an outlet node named `outflow1`, which is not an available outlet node of \
element `mybranch`.
        """

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
