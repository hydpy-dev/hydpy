# pylint: disable=line-too-long, unused-wildcard-import
"""
|exch_branch_rules| allows branching the summed input from some inlet nodes to an
arbitrary number of outlet nodes.  It calculates the output of each branch based on
seasonally varying, piecewise polynomial interpolation rules (see parameter |Rules|).
Branching discharge is the typical use case, but |exch_branch_rules| is suitable for
splitting arbitrary variables.  These can be negative (e.g. representing reverse flow).


Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 days:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "2000-01-01", "2000-01-12", "1d"

|exch_branch_rules| has no parameter whose values depend on the simulation time step,
so we do not need to define the parameter time step size here:

>>> from hydpy.models.exch_branch_rules import *
>>> parameterstep()

In the following setup, |exch_branch_rules| queries input from two inlet nodes and
passes the branched output to three outlet nodes:

>>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
>>> branch = Element("branch",
...                  inlets=["input1", "input2"],
...                  outlets=["output1", "output2", "output3"])

The |Node.variable| types of the respective |Node| instances do not matter.  Instead,
|exch_branch_rules| treats all inlet nodes as input providers and builds separate
connections to its outlet nodes, relying on the outlet nodes' names.  Hence, these
names must be used as keyword arguments when passing the respective interpolation rules
to parameter |Rules|:

>>> rules(
...     PPolys(
...         output1=PPoly.from_data(xs=[0.0, 2.0], ys=[0.0, 1.0]),
...         output2=PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 1.0, 0.0, 0.0]),
...         output3=PPoly.from_data(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 2.0, 6.0]),
...     )
... )

Now, as |exch_branch_rules| knows which interpolation rule applies to which outlet
node, we can safely connect the model to these nodes:

>>> branch.model = model

We do not have to define any initial values in the test settings because
|exch_branch_rules| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%d Jan."

The values of the inlet nodes `input1` and `input2` define no realistic input series.
Instead, they show |exch_branch_rules|'s behaviour inside and outside the ranges
covered by the interpolation rules' supporting points:

>>> import numpy
>>> nodes.input1.sequences.sim.series = numpy.arange(-2.0, 9.0)
>>> nodes.input2.sequences.sim.series = 0.0
>>> nodes.input2.sequences.sim.series[0] = 1.0

.. _exch_branch_rules_independent_rules:

independent rules
_________________

In the first example, we configure the interpolation rules of all outlet nodes
independently.  `output1` shows linear continuations below and above the range of its
supporting points.  `output2` points out that inverse relationships are allowed.
`output3` shows that |exch_branch_rules| does not enforce equality between the total
sum of input and output values (for example, the sum of all outputs is 14 instead of 8
for 11 Jan):

.. integration-test::

    >>> test("exch_branch_rules_independent_rules")
    |    date | input_ | input1 | input2 | output1 | output2 | output3 |
    --------------------------------------------------------------------
    | 01 Jan. |   -1.0 |   -2.0 |    1.0 |    -0.5 |    -0.5 |     0.0 |
    | 02 Jan. |   -1.0 |   -1.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 03 Jan. |    0.0 |    0.0 |    0.0 |     0.0 |     0.0 |     0.0 |
    | 04 Jan. |    1.0 |    1.0 |    0.0 |     0.5 |     0.5 |     0.0 |
    | 05 Jan. |    2.0 |    2.0 |    0.0 |     1.0 |     1.0 |     0.0 |
    | 06 Jan. |    3.0 |    3.0 |    0.0 |     1.5 |     0.5 |     1.0 |
    | 07 Jan. |    4.0 |    4.0 |    0.0 |     2.0 |     0.0 |     2.0 |
    | 08 Jan. |    5.0 |    5.0 |    0.0 |     2.5 |     0.0 |     4.0 |
    | 09 Jan. |    6.0 |    6.0 |    0.0 |     3.0 |     0.0 |     6.0 |
    | 10 Jan. |    7.0 |    7.0 |    0.0 |     3.5 |     0.0 |     8.0 |
    | 11 Jan. |    8.0 |    8.0 |    0.0 |     4.0 |     0.0 |    10.0 |


.. _exch_branch_rules_coordinated_rules:

coordinated rules
_________________

Often, maintaining the balance between input and outputs is essential.  Instead of
carefully synchronising the interpolation rules of all outlet nodes, you can use the
|PPolys.REST| option for one of them.  This node then receives everything not
distributed to the other nodes.  In the following example, node `output2` starts
receiving input when it exceeds 6.  Node `output3` provides a constant output of -1 for
input values up to 0, which then changes linearly to zero for an input of 4
(demonstrating that negative outputs are allowed, which might, for example, represent
supplies).  Finally, node `output1` receives the rest:

>>> rules(
...     PPolys(
...         output1=PPolys.REST,
...         output2=PPoly(xs=[0.0, 6.0, 7.0], ys=[0.0, 0.0, 1.0]),
...         output3=PPoly(xs=[-1.0, 0.0, 4.0, 6.0], ys=[-1.0, -1.0, 0.0, 0.0]),
...     )
... )

Because we use |PPolys.REST|, the sum of all outputs equals the input at each time step
(note that `output1` receives more than the total input when `output3` is negative):

.. integration-test::

    >>> test("exch_branch_rules_coordinated_rules")
    |    date | input_ | input1 | input2 | output1 | output2 | output3 |
    --------------------------------------------------------------------
    | 01 Jan. |   -1.0 |   -2.0 |    1.0 |     0.0 |     0.0 |    -1.0 |
    | 02 Jan. |   -1.0 |   -1.0 |    0.0 |     0.0 |     0.0 |    -1.0 |
    | 03 Jan. |    0.0 |    0.0 |    0.0 |     1.0 |     0.0 |    -1.0 |
    | 04 Jan. |    1.0 |    1.0 |    0.0 |    1.75 |     0.0 |   -0.75 |
    | 05 Jan. |    2.0 |    2.0 |    0.0 |     2.5 |     0.0 |    -0.5 |
    | 06 Jan. |    3.0 |    3.0 |    0.0 |    3.25 |     0.0 |   -0.25 |
    | 07 Jan. |    4.0 |    4.0 |    0.0 |     4.0 |     0.0 |     0.0 |
    | 08 Jan. |    5.0 |    5.0 |    0.0 |     5.0 |     0.0 |     0.0 |
    | 09 Jan. |    6.0 |    6.0 |    0.0 |     6.0 |     0.0 |     0.0 |
    | 10 Jan. |    7.0 |    7.0 |    0.0 |     6.0 |     1.0 |     0.0 |
    | 11 Jan. |    8.0 |    8.0 |    0.0 |     6.0 |     2.0 |     0.0 |


.. _exch_branch_rules_season_seasonal_rules:

seasonal rules
______________

Parameter |Rules| is a |SeasonalInterpolator|, so that you can define different
interpolation rules for different times of the year.  In this example, we define two
rules: the first passes half of the positive input to node `output2` and passes nothing
to node `output3`.  The second rule does the opposite.  Node `output1` receives the
rest in both cases:

>>> rule1 = PPolys(
...     output1=PPolys.REST,
...     output2=PPoly(xs=[-1.0, 0.0, 1.0], ys=[0.0, 0.0, 0.5]),
...     output3=PPoly(xs=[0.0, 1.0], ys=[0.0, 0.0]),
... )
>>> rule2 = PPolys(
...     output1=PPolys.REST,
...     output2=PPoly(xs=[0.0, 1.0], ys=[0.0, 0.0]),
...     output3=PPoly(xs=[-1.0, 0.0, 1.0], ys=[0.0, 0.0, 0.5]),
... )

We apply both rules twice, letting each control its respective time span without
interference from the other:

>>> rules(
...     toy_01_01_12=rule1, toy_01_05_12=rule1, toy_01_10_12=rule2, toy_12_30_12=rule2,
... )

Between the two separate time spans of rule one (1 Jan to 5 Jan) and rule two (10 Jan
to 31 Dec), |exch_branch_rules| linearly interpolates the results of both rules:

.. integration-test::

    >>> test("exch_branch_rules_season_seasonal_rules")
    |    date | input_ | input1 | input2 | output1 | output2 | output3 |
    --------------------------------------------------------------------
    | 01 Jan. |   -1.0 |   -2.0 |    1.0 |    -1.0 |     0.0 |     0.0 |
    | 02 Jan. |   -1.0 |   -1.0 |    0.0 |    -1.0 |     0.0 |     0.0 |
    | 03 Jan. |    0.0 |    0.0 |    0.0 |     0.0 |     0.0 |     0.0 |
    | 04 Jan. |    1.0 |    1.0 |    0.0 |     0.5 |     0.5 |     0.0 |
    | 05 Jan. |    2.0 |    2.0 |    0.0 |     1.0 |     1.0 |     0.0 |
    | 06 Jan. |    3.0 |    3.0 |    0.0 |     1.5 |     1.2 |     0.3 |
    | 07 Jan. |    4.0 |    4.0 |    0.0 |     2.0 |     1.2 |     0.8 |
    | 08 Jan. |    5.0 |    5.0 |    0.0 |     2.5 |     1.0 |     1.5 |
    | 09 Jan. |    6.0 |    6.0 |    0.0 |     3.0 |     0.6 |     2.4 |
    | 10 Jan. |    7.0 |    7.0 |    0.0 |     3.5 |     0.0 |     3.5 |
    | 11 Jan. |    8.0 |    8.0 |    0.0 |     4.0 |     0.0 |     4.0 |


.. _exch_branch_rules_input_modifying_rules:

input-modifying rules
_____________________

|exch_branch_rules| replaced the deprecated model |exch_branch_hbv96|, which only
supported piecewise linear interpolation.  However, |exch_branch_hbv96| has additional
parameters |Delta| and |Minimum|.  |Delta| adds or subtracts seasonally varying values
from the input, and |Minimum| resets the result to an eventually violated threshold
value.  We decided against adding such parameters to |exch_branch_rules|, because one
can easily construct the interpolation rules to achieve the same behaviour.


To demonstrate this, we take the only integration test of |exch_branch_hbv96| as an
example.  It defines a |Delta| of -1 and a |Minimum| of -1.  For the |XPoints|
`[0.0, 2.0, 4.0, 6.0]`, the |YPoints| are `[0.0, 1.0, 2.0, 3.0]`,
`[0.0, 1.0, 0.0, 0.0]`, and `[0.0, 0.0, 2.0, 6.0]` for nodes `output1`, `output2`, and
`output3`, respectively. This translates into:

>>> rules(
...     PPolys(
...         output1=PPoly(xs=[-1.0, 0.0, 1.0], ys=[-0.5, -0.5, 0.0]),
...         output2=PPoly(xs=[-1.0, 0.0, 3.0, 5.0, 7.0], ys=[-0.5, -0.5, 1.0, 0.0, 0.0]),
...         output3=PPoly(xs=[1.0, 3.0, 5.0, 7.0], ys=[0.0, 0.0, 2.0, 6.0]),
...     )
... )

As expected, the following results are identical to those of the |exch_branch_hbv96|
example:

.. integration-test::

    >>> test("exch_branch_rules_input_modifying_rules")
    |    date | input_ | input1 | input2 | output1 | output2 | output3 |
    --------------------------------------------------------------------
    | 01 Jan. |   -1.0 |   -2.0 |    1.0 |    -0.5 |    -0.5 |     0.0 |
    | 02 Jan. |   -1.0 |   -1.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 03 Jan. |    0.0 |    0.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 04 Jan. |    1.0 |    1.0 |    0.0 |     0.0 |     0.0 |     0.0 |
    | 05 Jan. |    2.0 |    2.0 |    0.0 |     0.5 |     0.5 |     0.0 |
    | 06 Jan. |    3.0 |    3.0 |    0.0 |     1.0 |     1.0 |     0.0 |
    | 07 Jan. |    4.0 |    4.0 |    0.0 |     1.5 |     0.5 |     1.0 |
    | 08 Jan. |    5.0 |    5.0 |    0.0 |     2.0 |     0.0 |     2.0 |
    | 09 Jan. |    6.0 |    6.0 |    0.0 |     2.5 |     0.0 |     4.0 |
    | 10 Jan. |    7.0 |    7.0 |    0.0 |     3.0 |     0.0 |     6.0 |
    | 11 Jan. |    8.0 |    8.0 |    0.0 |     3.5 |     0.0 |     8.0 |

.. testsetup::

    >>> from hydpy import Node
    >>> del pub.timegrids
    >>> Node.clear_all()
    >>> Element.clear_all()
"""

from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly, PPolys  # pylint: disable=unused-import
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.exe.modelimports import *
from hydpy.models.exch import exch_control
from hydpy.models.exch import exch_model


class Model(modeltools.AdHocModel):
    """|exch_branch_rules.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Branch-Rules",
        description=(
            "branching based on piecewise linear or polynomial interpolation rules"
        ),
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (exch_model.Pick_Input_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    ADD_METHODS = ()
    OUTLET_METHODS = (exch_model.Pass_Branched_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    __hydpy__targetnames__: tuple[str, ...] | None

    def __init__(self) -> None:
        super().__init__()
        self.__hydpy__targetnames__ = None

    @property
    def targetnames(self) -> tuple[str, ...]:
        """Names of the target nodes.

        The names are sorted alphabetically, which agrees with the order of the
        outputs of parameter |Rules|.
        """
        if (targetnames := self.__hydpy__targetnames__) is None:
            raise RuntimeError(
                f"The names of the target nodes are still unknown.  Please define "
                f"them via parameter `{exch_control.Rules.__name__.lower()}` first."
            )
        return targetnames

    def connect(self) -> None:
        """Connect all available inlet nodes to the inlet sequence |Total| and all
        target outlet nodes to the outlet sequence |Branched|.

        The following test configuration involves two inlet nodes (`inflow1` and
        `inflow2`) and two outlet nodes (`diversion` and `river`):

        >>> from hydpy import Element, Nodes, pub
        >>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
        >>> diversion, inflow1, inflow2, river = Nodes(
        ...     "diversion", "inflow1", "inflow2", "river"
        ... )
        >>> branch = Element(
        ...     "branch", inlets=[inflow1, inflow2], outlets=[diversion, river]
        ... )

        |exch_branch_rules| takes the target node names from parameter |Rules|.
        Hence, you cannot build connections before defining the interpolation rules:

        >>> from hydpy.models.exch_branch_rules import *
        >>> parameterstep()
        >>> branch.model = model
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to connect model `exch_branch_rules` with element \
`branch`, the following error occurred: The names of the target nodes are still \
unknown.  Please define them via parameter `rules` first.

        The target node names must agree with the outlet nodes' names:

        >>> rules(
        ...     PPolys(
        ...         channel=PPolys.REST,
        ...         diversion=PPoly(xs=[0.0, 3.0], ys=[0.0, 2.0]),
        ...     )
        ... )
        >>> model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to connect model `exch_branch_rules` with element \
`branch`, the following error occurred: The target node names `channel and \
diversion` do not agree with the available outlet nodes `diversion and river`.

        With consistent definitions, the branched flows reach the nodes `diversion`
        and `river` as intended:

        >>> rules(
        ...     PPolys(
        ...         river=PPolys.REST,
        ...         diversion=PPoly(xs=[0.0, 3.0], ys=[0.0, 2.0]),
        ...     )
        ... )
        >>> model.connect()
        >>> inflow1.sequences.sim = 1.0
        >>> inflow2.sequences.sim = 2.0
        >>> derived.toy.update()
        >>> model.update_inlets()
        >>> model.update_outlets()
        >>> river.sequences.sim
        sim(1.0)
        >>> diversion.sequences.sim
        sim(2.0)

        .. testsetup::

            >>> from hydpy import Node
            >>> del pub.timegrids
            >>> Node.clear_all()
            >>> Element.clear_all()
        """

        try:

            inlets = self.element.inlets
            total = self.sequences.inlets.total
            total.node2idx = {}
            total.shape = len(inlets)
            for idx, inlet in enumerate(inlets):
                total.set_pointer(inlet.get_double("inlets"), idx)
                total.node2idx[inlet] = idx

            targetnames = self.targetnames
            outlets = self.element.outlets
            if targetnames != outlets.names:
                raise RuntimeError(
                    f"The target node names `{objecttools.enumeration(targetnames)}` "
                    f"do not agree with the available outlet nodes "
                    f"`{objecttools.enumeration(outlets.names)}`."
                )
            branched = self.sequences.outlets.branched
            branched.node2idx = {}
            branched.shape = len(targetnames)
            for idx, targetname in enumerate(targetnames):
                targetnode = getattr(outlets, targetname)
                branched.set_pointer(targetnode.get_double("outlets"), idx)
                branched.node2idx[targetnode] = idx

        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to connect model `{self.name}` with element "
                f"`{self.element.name}`"
            )


tester = Tester()
cythonizer = Cythonizer()
