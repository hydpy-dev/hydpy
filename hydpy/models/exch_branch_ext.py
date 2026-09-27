# pylint: disable=line-too-long, unused-wildcard-import
"""
|exch_branch_ext| allows branching the summed input from some inlet nodes to an
arbitrary number of outlet nodes. The original HBV96 implementation is supposed to
split inflowing discharge, but |exch_branch_ext| is suitable for splitting arbitrary
variables. Calculations are performed for each branch individually by linear
interpolation (or extrapolation) following tabulated supporting points.  Additionally,
|exch_branch_ext| allows adjusting the input data with differences that can vary
monthly.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 11:00", "1h"

|exch_branch_ext| has no parameter with values depending on the simulation step size,
which is why we can pass anything (or nothing) to function |parameterstep| without
changing the following results:

>>> from hydpy.models.exch_branch_ext import *
>>> parameterstep()

|exch_branch_ext| queries inflow from two inlet |Node| objects and passes the
branched outflow to three outlet |Node| objects.  Thus, In contrast to most other
application models, we need to define the parameter values before connecting the
model to its |Element| object, called `branch`:

>>> nodes = Nodes("inflow1", "inflow2", "river", "diversion")
>>> branch = Element(
...     "branch", inlets=["inflow1", "inflow2"], outlets=["river", "diversion"]
... )
>>> targets(main="river", branch="diversion")
>>> fixwaterbalance(ADJUST_NOTHING)
>>> fallbackrules(PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 2.0, 2.0]))
>>> branch.model = model

We do not have to define any initial values in the test settings because the
|exch_branch_ext| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%H:%M"

The (identical) values of the inlet nodes `inflow1` and `inflow2` define no realistic
inflow series.  Instead, they serve to show the behaviour of |exch_branch_ext| within
and outside the current range defined by parameter |XPoints|:

>>> import numpy
>>> nodes.inflow1.sequences.sim.series = numpy.arange(0.0, 11.0)
>>> nodes.inflow2.sequences.sim.series = -1.0

`output1` shows linear continuations below and above the current range of parameter
|XPoints|. `output2` points out that inverse relationships are allowed. `output3` shows
that |exch_branch_ext| does not enforce equality between the total sum of input and
output values:

.. integration-test::

    >>> test("exch_branch_ext_ex1")
    |  date | exchange | originalinput |       outputs | diversion | inflow1 | inflow2 | river |
    --------------------------------------------------------------------------------------------
    | 00:00 |      nan |          -1.0 | -1.0      0.0 |       0.0 |     0.0 |    -1.0 |  -1.0 |
    | 01:00 |      nan |           0.0 |  0.0      0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 02:00 |      nan |           1.0 |  1.0      0.0 |       0.0 |     2.0 |    -1.0 |   1.0 |
    | 03:00 |      nan |           2.0 |  2.0      0.0 |       0.0 |     3.0 |    -1.0 |   2.0 |
    | 04:00 |      nan |           3.0 |  2.0      1.0 |       1.0 |     4.0 |    -1.0 |   2.0 |
    | 05:00 |      nan |           4.0 |  2.0      2.0 |       2.0 |     5.0 |    -1.0 |   2.0 |
    | 06:00 |      nan |           5.0 |  3.0      2.0 |       2.0 |     6.0 |    -1.0 |   3.0 |
    | 07:00 |      nan |           6.0 |  4.0      2.0 |       2.0 |     7.0 |    -1.0 |   4.0 |
    | 08:00 |      nan |           7.0 |  5.0      2.0 |       2.0 |     8.0 |    -1.0 |   5.0 |
    | 09:00 |      nan |           8.0 |  6.0      2.0 |       2.0 |     9.0 |    -1.0 |   6.0 |
    | 10:00 |      nan |           9.0 |  7.0      2.0 |       2.0 |    10.0 |    -1.0 |   7.0 |


>>> fallbackrules(
...     toy_01_01_00_30=PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 1.0, 2.0, 2.0]),
...     toy_01_01_10_30=PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 2.0, 2.0]),
... )
>>> model.connect()

.. integration-test::

    >>> test("exch_branch_ext_ex1b")
    |  date | exchange | originalinput |       outputs | diversion | inflow1 | inflow2 | river |
    --------------------------------------------------------------------------------------------
    | 00:00 |      nan |          -1.0 | -0.5     -0.5 |      -0.5 |     0.0 |    -1.0 |  -0.5 |
    | 01:00 |      nan |           0.0 |  0.0      0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 02:00 |      nan |           1.0 |  0.6      0.4 |       0.4 |     2.0 |    -1.0 |   0.6 |
    | 03:00 |      nan |           2.0 |  1.3      0.7 |       0.7 |     3.0 |    -1.0 |   1.3 |
    | 04:00 |      nan |           3.0 |  1.7      1.3 |       1.3 |     4.0 |    -1.0 |   1.7 |
    | 05:00 |      nan |           4.0 |  2.0      2.0 |       2.0 |     5.0 |    -1.0 |   2.0 |
    | 06:00 |      nan |           5.0 |  3.0      2.0 |       2.0 |     6.0 |    -1.0 |   3.0 |
    | 07:00 |      nan |           6.0 |  4.0      2.0 |       2.0 |     7.0 |    -1.0 |   4.0 |
    | 08:00 |      nan |           7.0 |  5.0      2.0 |       2.0 |     8.0 |    -1.0 |   5.0 |
    | 09:00 |      nan |           8.0 |  6.0      2.0 |       2.0 |     9.0 |    -1.0 |   6.0 |
    | 10:00 |      nan |           9.0 |  7.0      2.0 |       2.0 |    10.0 |    -1.0 |   7.0 |

>>> with pub.options.checkseries(False):
...     inputs.exchange.series = [
...         -1.0, 0.0, 3.0, 2.0, 2.0, 2.0, 2.0, 2.0, nan, inf, -inf,
...     ]



.. integration-test::

    >>> test("exch_branch_ext_ex2")
    |  date | exchange | originalinput |       outputs | diversion | inflow1 | inflow2 | river |
    --------------------------------------------------------------------------------------------
    | 00:00 |     -1.0 |          -1.0 |  0.0     -1.0 |      -1.0 |     0.0 |    -1.0 |   0.0 |
    | 01:00 |      0.0 |           0.0 |  0.0      0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 02:00 |      3.0 |           1.0 | -2.0      3.0 |       3.0 |     2.0 |    -1.0 |  -2.0 |
    | 03:00 |      2.0 |           2.0 |  0.0      2.0 |       2.0 |     3.0 |    -1.0 |   0.0 |
    | 04:00 |      2.0 |           3.0 |  1.0      2.0 |       2.0 |     4.0 |    -1.0 |   1.0 |
    | 05:00 |      2.0 |           4.0 |  2.0      2.0 |       2.0 |     5.0 |    -1.0 |   2.0 |
    | 06:00 |      2.0 |           5.0 |  3.0      2.0 |       2.0 |     6.0 |    -1.0 |   3.0 |
    | 07:00 |      2.0 |           6.0 |  4.0      2.0 |       2.0 |     7.0 |    -1.0 |   4.0 |
    | 08:00 |      nan |           7.0 |  5.0      2.0 |       2.0 |     8.0 |    -1.0 |   5.0 |
    | 09:00 |      inf |           8.0 |  6.0      2.0 |       2.0 |     9.0 |    -1.0 |   6.0 |
    | 10:00 |     -inf |           9.0 |  7.0      2.0 |       2.0 |    10.0 |    -1.0 |   7.0 |

.. integration-test::

    >>> fixwaterbalance(ADJUST_BRANCH)
    >>> test("exch_branch_ext_ex3")
    |  date | exchange | originalinput |      outputs | diversion | inflow1 | inflow2 | river |
    -------------------------------------------------------------------------------------------
    | 00:00 |     -1.0 |          -1.0 | 0.0     -1.0 |      -1.0 |     0.0 |    -1.0 |   0.0 |
    | 01:00 |      0.0 |           0.0 | 0.0      0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 02:00 |      3.0 |           1.0 | 0.0      1.0 |       1.0 |     2.0 |    -1.0 |   0.0 |
    | 03:00 |      2.0 |           2.0 | 0.0      2.0 |       2.0 |     3.0 |    -1.0 |   0.0 |
    | 04:00 |      2.0 |           3.0 | 1.0      2.0 |       2.0 |     4.0 |    -1.0 |   1.0 |
    | 05:00 |      2.0 |           4.0 | 2.0      2.0 |       2.0 |     5.0 |    -1.0 |   2.0 |
    | 06:00 |      2.0 |           5.0 | 3.0      2.0 |       2.0 |     6.0 |    -1.0 |   3.0 |
    | 07:00 |      2.0 |           6.0 | 4.0      2.0 |       2.0 |     7.0 |    -1.0 |   4.0 |
    | 08:00 |      nan |           7.0 | 5.0      2.0 |       2.0 |     8.0 |    -1.0 |   5.0 |
    | 09:00 |      inf |           8.0 | 6.0      2.0 |       2.0 |     9.0 |    -1.0 |   6.0 |
    | 10:00 |     -inf |           9.0 | 7.0      2.0 |       2.0 |    10.0 |    -1.0 |   7.0 |



.. integration-test::

    >>> fixwaterbalance(ADJUST_RIVER)
    >>> test("exch_branch_ext_ex3")
    |  date | exchange | originalinput |      outputs | diversion | inflow1 | inflow2 | river |
    -------------------------------------------------------------------------------------------
    | 00:00 |     -1.0 |          -1.0 | 0.0     -1.0 |      -1.0 |     0.0 |    -1.0 |   0.0 |
    | 01:00 |      0.0 |           0.0 | 0.0      0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 02:00 |      3.0 |           1.0 | 0.0      3.0 |       3.0 |     2.0 |    -1.0 |   0.0 |
    | 03:00 |      2.0 |           2.0 | 0.0      2.0 |       2.0 |     3.0 |    -1.0 |   0.0 |
    | 04:00 |      2.0 |           3.0 | 1.0      2.0 |       2.0 |     4.0 |    -1.0 |   1.0 |
    | 05:00 |      2.0 |           4.0 | 2.0      2.0 |       2.0 |     5.0 |    -1.0 |   2.0 |
    | 06:00 |      2.0 |           5.0 | 3.0      2.0 |       2.0 |     6.0 |    -1.0 |   3.0 |
    | 07:00 |      2.0 |           6.0 | 4.0      2.0 |       2.0 |     7.0 |    -1.0 |   4.0 |
    | 08:00 |      nan |           7.0 | 5.0      2.0 |       2.0 |     8.0 |    -1.0 |   5.0 |
    | 09:00 |      inf |           8.0 | 6.0      2.0 |       2.0 |     9.0 |    -1.0 |   6.0 |
    | 10:00 |     -inf |           9.0 | 7.0      2.0 |       2.0 |    10.0 |    -1.0 |   7.0 |

"""

from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly, PPolys  # pylint: disable=unused-import
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.exe.modelimports import *
from hydpy.models.exch.exch_constants import *
from hydpy.models.exch import exch_control
from hydpy.models.exch import exch_model


ADDITIONAL_CONTROLPARAMETERS = (exch_control.Targets,)  # ToDo: remove?

class Model(modeltools.AdHocModel):
    """|exch_branch_ext.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Branch-LARSIM", description="branch model adopted from LARSIM"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (exch_model.Pick_OriginalInput_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (exch_model.Calc_Outputs_V2,)
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
