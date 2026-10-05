# pylint: disable=line-too-long, unused-wildcard-import
"""
|exch_branch_io| modifies the flow through a stream by transferring water based on
externally defined requests.  These are usually positive (withdrawals) but can also be
negative (supplies).  If external requests are missing, it estimates the water transfer
using season-dependent interpolation rules.

|exch_branch_io| is compatible with the LARSIM routines for modelling simple (VERZ) and
extended (ERWV) branching of river discharge, while offering some additional
functionalities:

 * Handling of negative inflow (reverse flow) is possible.
 * Water transfers can be positive (withdrawals) and negative (supplies).
 * Configuration of minimum and maximum flows that must not be violated by externally
   requested water transfers (including different modes of transfer adjustment).
 * Inflow-dependent piecewise interpolation (for the fallback calculations) can be
   linear or non-linear (spline interpolation).
 * The transition between season-dependent interpolation rules is usually smoothed by
   linear interpolation over time.

Before reading the following integration tests, it is advisable to review the
documentation for method |Pass_ActualTransfer_StreamOutflow_V1|, which is the core of
|exch_branch_io|.


Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 days:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "2000-01-01", "2000-01-12", "1d"

|exch_branch_io| has no parameter whose values depend on the simulation time step, so
we do not need to define the parameter time step size here:

>>> from hydpy.models.exch_branch_io import *
>>> parameterstep()

According to the following setting, |exch_branch_io| queries inflow from two inlet
nodes and passes the branched outflow to two outlet nodes:

>>> nodes = Nodes("inflow1", "inflow2", "river", "diversion")
>>> branch = Element(
...     "branch", inlets=["inflow1", "inflow2"], outlets=["river", "diversion"]
... )

There may be fewer or more inlet nodes, but the number of outlet nodes must be exactly
two.

The |Node.variable| types of the respective |Node| instances do not matter.  Instead,
|exch_branch_io| lumps all inlet nodes together as inflow providers and builds
different connections to the two outlet nodes, for which it uses the node names passed
to parameter |Targets|:

>>> targets(stream="river", transfer="diversion")
>>> branch.model = model

By assigning "river" to the keyword `stream` and "diversion" to the keyword `transfer`,
the roles of the two outlet nodes become clear.  The "transfer" node will receive the
calculated water transfer, while the "river" node will receive the remaining (or
enhanced) streamflow.

We do not have to define any initial values in the test settings because
|exch_branch_io| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%d Jan."

Instead of defining a realistic inflow series, the sum of the inlet nodes' values
increases linearly:

>>> import numpy
>>> nodes.inflow1.sequences.sim.series = numpy.arange(0.0, 11.0)
>>> nodes.inflow2.sequences.sim.series = -1.0

.. _exch_branch_io_requested_transfer:

requested transfer
__________________

|exch_branch_io|'s priority is to withdraw water from or supply water to the main
stream based on externally requested transfers, given as an input time series.  In this
example, these requests are positive (withdrawals) in the first half and negative
(supplies) in the second half of the simulation period:

>>> inputs.requestedtransfer.series = 6 * [2.0] + 5 * [-2.0]

Withdrawals could cause too-low (and even negative) flows.  To prevent this, we set
parameter |MinStream| to 1 m³/s:

>>> minstream(1.0)

Likewise, supplies could cause too-high flows, which we prevent by setting parameter
|MaxStream| to 8 m³/s:

>>> maxstream(8.0)

Parameter |KeepWaterBalance| configures the exact behaviour during possible violations
of |MinStream| and |MaxStream|, which is explained in detail in the documentation on
method |Pass_ActualTransfer_StreamOutflow_V1|.  Here, we set the more intuitive
behaviour of reducing transfers as strongly as necessary to maintain the water balance:

>>> keepwaterbalance(True)

As the simulation results show, the transfer is reduced to zero if necessary.  Still,
withdrawals are never turned into supplies for already too-low inflows and supplies are
never turned into withdrawals for already too-high inflows:

.. integration-test::

    >>> test("exch_branch_io_requested_transfer")
    |    date | requestedtransfer | inflow | diversion | inflow1 | inflow2 | river |
    --------------------------------------------------------------------------------
    | 01 Jan. |               2.0 |   -1.0 |       0.0 |     0.0 |    -1.0 |  -1.0 |
    | 02 Jan. |               2.0 |    0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 03 Jan. |               2.0 |    1.0 |       0.0 |     2.0 |    -1.0 |   1.0 |
    | 04 Jan. |               2.0 |    2.0 |       1.0 |     3.0 |    -1.0 |   1.0 |
    | 05 Jan. |               2.0 |    3.0 |       2.0 |     4.0 |    -1.0 |   1.0 |
    | 06 Jan. |               2.0 |    4.0 |       2.0 |     5.0 |    -1.0 |   2.0 |
    | 07 Jan. |              -2.0 |    5.0 |      -2.0 |     6.0 |    -1.0 |   7.0 |
    | 08 Jan. |              -2.0 |    6.0 |      -2.0 |     7.0 |    -1.0 |   8.0 |
    | 09 Jan. |              -2.0 |    7.0 |      -1.0 |     8.0 |    -1.0 |   8.0 |
    | 10 Jan. |              -2.0 |    8.0 |       0.0 |     9.0 |    -1.0 |   8.0 |
    | 11 Jan. |              -2.0 |    9.0 |       0.0 |    10.0 |    -1.0 |   9.0 |

.. _exch_branch_io_internal_estimates:

internal estimates
__________________

If external requests are unavailable (preferably indicated by |numpy.inf| or
alternatively by |numpy.nan|), |exch_branch_io| must fall back to its internal routine
for calculating requested transfers:

>>> inputs.requestedtransfer.series = numpy.inf

Configuring this internal routine means defining piecewise linear or polynomial
interpolation functions and passing them to parameter |FlowTransferRules|.  The
documentation for parameter |FlowTransferRules| explains the available degrees of
freedom for doing so. However, here we restrict ourselves to simple |PPoly| instances,
each interpolating the water transfer for a specific time of year:

>>> flowtransferrules(
...     toy_01_01_12=PPoly(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 1.0, 1.0]),
...     toy_01_09_12=PPoly(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 1.0, 1.0]),
...     toy_01_11_12=PPoly(xs=[0.0, 2.0, 4.0, 6.0], ys=[0.0, 0.0, 2.0, 2.0]),
... )

From 1 to 9 Jan, the first rule (defined twice) applies, which diverts up to 1 m³/s.
After that, there is a continuous transition from the first to the second rule, which
diverts up to 2 m³/s:

.. integration-test::

    >>> test("exch_branch_io_internal_estimates")
    |    date | requestedtransfer | inflow | diversion | inflow1 | inflow2 | river |
    --------------------------------------------------------------------------------
    | 01 Jan. |               inf |   -1.0 |       0.0 |     0.0 |    -1.0 |  -1.0 |
    | 02 Jan. |               inf |    0.0 |       0.0 |     1.0 |    -1.0 |   0.0 |
    | 03 Jan. |               inf |    1.0 |       0.0 |     2.0 |    -1.0 |   1.0 |
    | 04 Jan. |               inf |    2.0 |       0.0 |     3.0 |    -1.0 |   2.0 |
    | 05 Jan. |               inf |    3.0 |       0.5 |     4.0 |    -1.0 |   2.5 |
    | 06 Jan. |               inf |    4.0 |       1.0 |     5.0 |    -1.0 |   3.0 |
    | 07 Jan. |               inf |    5.0 |       1.0 |     6.0 |    -1.0 |   4.0 |
    | 08 Jan. |               inf |    6.0 |       1.0 |     7.0 |    -1.0 |   5.0 |
    | 09 Jan. |               inf |    7.0 |       1.0 |     8.0 |    -1.0 |   6.0 |
    | 10 Jan. |               inf |    8.0 |       1.5 |     9.0 |    -1.0 |   6.5 |
    | 11 Jan. |               inf |    9.0 |       2.0 |    10.0 |    -1.0 |   7.0 |

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
from hydpy.core.typingtools import *
from hydpy.exe.modelimports import *
from hydpy.models.exch import exch_control
from hydpy.models.exch import exch_model

ADDITIONAL_CONTROLPARAMETERS = (exch_control.Targets,)


class Model(modeltools.AdHocModel):
    """|exch_branch_io.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Exch-Branch-IO",
        description="branch model using external water transfer requests",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (exch_model.Pick_Inflow_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    ADD_METHODS = ()
    OUTLET_METHODS = (exch_model.Pass_ActualTransfer_StreamOutflow_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    __hydpy__targetnames__: tuple[str, str] | None

    def __init__(self) -> None:
        super().__init__()
        self.__hydpy__targetnames__ = None

    @property
    def targetnames(self) -> tuple[str, str]:
        """Names of the target nodes.

        The first and the second name belong to the mainstream node and the transfer
        node, respectively.  Note that this order can differ from the alphabetical
        order of the outputs of parameter |FlowTransferRules| (see |StreamIndex|).
        """
        if (targetnames := self.__hydpy__targetnames__) is None:
            raise RuntimeError(
                f"The names of the target nodes are still unknown.  Please define "
                f"them via parameter `{exch_control.Targets.__name__.lower()}` first."
            )
        return targetnames

    def connect(self) -> None:
        """Connect all available inlet nodes to the inlet sequence
        |exch_inlets.Inflow|, and connect correctly named target outlet nodes to the
        outlet sequences |ActualTransfer| and |StreamOutflow|.

        The following test configuration involves two inlet nodes (`inflow1` and
        `inflow2`) and two outlet nodes (`diversion` and `river`):

        >>> from hydpy import Element, Nodes, pub
        >>> pub.timegrids = "2000-01-01", "2000-01-12", "1d"
        >>> diversion, inflow1, inflow2, river = Nodes(
        ...     "diversion", "inflow1", "inflow2", "river"
        ... )
        >>> branch = Element(
        ...     "branch", inlets=[inflow1, inflow2], outlets=[diversion, river]
        ... )

        Without giving |exch_branch_io| more information about the outlet nodes' roles,
        you cannot build connections to them:

        >>> from hydpy.models.exch_branch_io import *
        >>> parameterstep()
        >>> branch.model = model
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to connect model `exch_branch_io` with element \
`branch`, the following error occurred: The names of the target nodes are still \
unknown.  Please define them via parameter `targets` first.

        Providing this information works via parameter |Targets|, which requires the
        (correct) target node names:

        >>> targets(stream="channel", transfer="diversion")
        >>> model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to connect model `exch_branch_io` with element \
`branch`, the following error occurred: The target node names `channel and diversion` \
do not agree with the available outlet nodes `diversion and river`.

        With consistent definitions, the transfer and the mainstream outflow reach the
        nodes `diversion` and `river` as intended:

        >>> targets(stream="river", transfer="diversion")
        >>> flowtransferrules(PPoly(xs=[0.0, 3.0], ys=[0.0, 2.0]))
        >>> derived.toy.update()
        >>> derived.streamindex.update()
        >>> model.connect()
        >>> fluxes.inflow = 3.0
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
            inflow = self.sequences.inlets.inflow
            inflow.node2idx = {}
            inflow.shape = len(inlets)
            for idx, inlet in enumerate(inlets):
                inflow.set_pointer(inlet.get_double("inlets"), idx)
                inflow.node2idx[inlet] = idx

            targetnames = self.targetnames
            outlets = self.element.outlets
            if sorted(targetnames) != sorted(outlets.names):
                raise RuntimeError(
                    f"The target node names `{objecttools.enumeration(targetnames)}` "
                    f"do not agree with the available outlet nodes "
                    f"`{objecttools.enumeration(outlets.names)}`."
                )
            sequences = self.sequences.outlets
            for targetname, sequence in zip(
                targetnames, (sequences.streamoutflow, sequences.actualtransfer)
            ):
                targetnode = getattr(outlets, targetname)
                sequence.set_pointer(targetnode.get_double("outlets"), 0)
                sequence.node2idx = {targetnode: 0}

        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to connect model `{self.name}` with element "
                f"`{self.element.name}`"
            )


tester = Tester()
cythonizer = Cythonizer()
