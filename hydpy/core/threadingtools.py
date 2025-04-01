"""This module implements HydPy's fundamental features for performing multi-threaded
simulation runs."""

from __future__ import annotations
import itertools
import queue
import sys
import threading

import networkx
import numpy

import hydpy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *


class Parallelisability:
    """An analyser for the "parallelisability" of a network.

    We explain the meaning of the members of class |Parallelisability| based on the
    small example project created by function |prepare_receiver_example|:

    >>> from hydpy.core.testtools import prepare_receiver_example
    >>> hp, pub = prepare_receiver_example()

    You can initialise |Parallelisability| objects manually, but it usually is
    sufficient to access the object made available by property
    |HydPy.parallelisability| of class |HydPy|.

    >>> p = hp.parallelisability

    The members |Parallelisability.parallel_elements| and
    |Parallelisability.sequential_elements| divide those elements that can be simulated
    in parallel and those that must be simulated sequentially:

    >>> p.parallel_elements
    Elements("l1", "l2", "l3")
    >>> p.sequential_elements
    Elements("d", "s12", "s23", "s34")

    The members |Parallelisability.parallel_nodes| and
    |Parallelisability.sequential_nodes| list all nodes connected to at least one
    element that is an item of |Parallelisability.parallel_elements| or
    |Parallelisability.sequential_elements|, respectively:

    >>> p.parallel_nodes
    Nodes("n1a", "n2", "n3")
    >>> p.sequential_nodes
    Nodes("n1a", "n1b", "n2", "n3", "n4")

    Nodes that mark a transition between the "parallelisable" and "non-parallelisable"
    parts of a network, and are thus listed both in |Parallelisability.parallel_nodes|
    and |Parallelisability.sequential_nodes|, need special treatment during simulation
    runs and are hence separately available via the member
    |Parallelisability.transition_nodes|:

    >>> p.transition_nodes
    Nodes("n1a", "n2", "n3")

    The reason why the analysed network is not completely parallelisable is the usage
    of the receiver node mechanism.  The |dam_v001| model handled by element `d` tries
    to prevent low flow situations at a downstream location and therefore gets
    information from this place via the receiver node `n2`.  Hence, calculating the
    latest water release of `d` requires up-to-date discharge information from `n2`,
    which prevents applying the "temporal chunking" strategy, on which HydPy's
    multi-threading approach is grounded:

    >>> hp.elements.d
    Element("d",
            inlets="n1a",
            outlets="n1b",
            receivers="n2")

    However, if we tell node `n2` not to pass freshly simulated but already available
    discharge values to `d` by changing its |Node.deploymode|, the need for `d` to wait
    for other models to contribute to the total discharge at `n2` disappears, and the
    complete network becomes parallelisable:

    >>> hp.nodes.n2.deploymode
    'newsim'
    >>> hp.nodes.n2.deploymode = "oldsim"
    >>> p = hp.parallelisability
    >>> p.parallel_elements
    Elements("d", "l1", "l2", "l3", "s12", "s23", "s34")
    >>> p.sequential_elements
    Elements()
    >>> p.parallel_nodes
    Nodes("n1a", "n1b", "n2", "n3", "n4")
    >>> p.sequential_nodes
    Nodes()
    >>> p.transition_nodes
    Nodes()
    """

    parallel_elements: devicetools.Elements
    """All parallelisable elements."""

    sequential_elements: devicetools.Elements
    """All non-parallelisable elements."""

    parallel_nodes: devicetools.Nodes
    """All nodes with a connection to at least one parallelisable element."""

    sequential_nodes: devicetools.Nodes
    """All nodes with a connection to at least one non-parallelisable element."""

    transition_nodes: devicetools.Nodes
    """All nodes with a connection to at least one parallelisable and one 
    non-parallelisable element."""

    def __init__(
        self, nodes: devicetools.Nodes, elements: devicetools.Elements
    ) -> None:

        graph = hydpytools.create_directedgraph(nodes, elements)
        sequential_elements: set[devicetools.Element] = set()
        for element in elements:
            if any(n.deploymode in ("newsim", "obs_newsim") for n in element.receivers):
                if element not in sequential_elements:
                    sequential_elements.add(element)
                    descendants = networkx.descendants(graph, element)
                    sequential_elements.update(
                        e for e in descendants if isinstance(e, devicetools.Element)
                    )
        parallel_elements = set(elements) - sequential_elements

        def _select_nodes(
            relevant_elements: set[devicetools.Element], /
        ) -> set[devicetools.Node]:
            selected_nodes = set()
            remaining_nodes = set(nodes)
            for e in relevant_elements:
                candidates = set(
                    itertools.chain(
                        e.inlets, e.outlets, e.receivers, e.senders, e.inputs, e.outputs
                    )
                )
                intersection = remaining_nodes.intersection(candidates)
                selected_nodes.update(intersection)
                remaining_nodes.difference_update(intersection)
                if not remaining_nodes:
                    break
            return selected_nodes

        sequential_nodes = _select_nodes(sequential_elements)
        parallel_nodes = _select_nodes(parallel_elements)

        transition_nodes = sequential_nodes.intersection(parallel_nodes)

        remaining_nodes = set(nodes) - sequential_nodes - parallel_nodes
        sequential_nodes.update(remaining_nodes)

        self.sequential_elements = devicetools.Elements(sequential_elements)
        self.parallel_elements = devicetools.Elements(parallel_elements)
        self.sequential_nodes = devicetools.Nodes(sequential_nodes)
        self.parallel_nodes = devicetools.Nodes(parallel_nodes)
        self.transition_nodes = devicetools.Nodes(transition_nodes)


class Queue(queue.LifoQueue[devicetools.NodeOrElement]):
    """A "Last In - First Out" queue for executing the parallelisable parts of a
    network more efficiently via multi-threading.

    For most users, |Queue| is more of an implementation detail that is never directly
    used.  However, if you intend to quench the last bit of performance out of HydPy,
    you can create custom |Queue| instances that fit better to your network and model
    configurations at hand, and pass them to method |HydPy.simulate_multithreaded|.
    """

    starters: Final[Sequence[devicetools.NodeOrElement]]
    """All nodes and elements that do not have any dependencies.  These can be 
    processed right at the start of a multi-threaded simulation."""

    dependencies: Final[Mapping[devicetools.NodeOrElement, int]]
    """The number of dependencies of all nodes and elements.  An element with three
    dependencies is connected to three nodes that must be processed until itself has
    all information required simulation."""

    upstream2downstream: Final[
        Mapping[devicetools.NodeOrElement, Sequence[devicetools.NodeOrElement]]
    ]
    """A mapping that lists for all nodes and elements, which neighbouring elements or 
    nodes must wait for their processing completion.   In other words, each key 
    (node or element) represents one of the dependencies of the corresponding list's 
    items (elements or nodes)."""

    _waiting: dict[devicetools.NodeOrElement, int]
    _first_exception: BaseException | None

    def __init__(
        self,
        *,
        starters: Sequence[devicetools.NodeOrElement],
        dependencies: Mapping[devicetools.NodeOrElement, int],
        upstream2downstream: Mapping[
            devicetools.NodeOrElement, Sequence[devicetools.NodeOrElement]
        ],
    ) -> None:

        super().__init__()
        self._first_exception = None
        self.upstream2downstream = upstream2downstream
        self.starters = starters
        self.dependencies = dependencies

    @classmethod
    def from_devices(
        cls, *, nodes: devicetools.Nodes, elements: devicetools.Elements
    ) -> Self:
        """Create a new |Queue| instance and determine its members from the given
        (parallelisable) devices."""

        upstream2downstream: dict[
            devicetools.NodeOrElement, list[devicetools.NodeOrElement]
        ] = {}
        successors2starter: list[tuple[int, devicetools.NodeOrElement]] = []
        dependencies: dict[devicetools.NodeOrElement, int] = {}

        graph = hydpytools.create_directedgraph(nodes, elements)
        successors = networkx.dfs_successors

        forwards_newsim = "newsim", "obs_newsim"
        receives_newsim = "newsim", "obs", "obs_newsim", "obs_bi"

        for e in elements:
            nmb_in = sum(
                node.deploymode in forwards_newsim
                for node in itertools.chain(e.inlets, e.receivers, e.inputs)
            )
            if nmb_in:
                dependencies[e] = nmb_in
            else:
                successors2starter.append((len(successors(graph, e)), e))
            upstream2downstream[e] = [
                n
                for n in itertools.chain(e.outlets, e.senders, e.outputs)
                if n.deploymode in receives_newsim
            ]

        for n in nodes:
            if n.deploymode in receives_newsim:
                if nmb_in := sum(e in elements for e in n.entries):
                    dependencies[n] = nmb_in
                else:
                    successors2starter.append((len(successors(graph, n)), n))
                if n.deploymode in forwards_newsim:
                    upstream2downstream[n] = list(e for e in n.exits if e in elements)

        return cls(
            starters=[d for n, d in sorted(successors2starter, key=lambda t: t[0])],
            dependencies=dependencies,
            upstream2downstream=upstream2downstream,
        )

    @classmethod
    def from_queue(cls, *, queue_: Self) -> Self:
        """Create a new |Queue| instance and take its members from the given |Queue|
        instance.

        This copy-like mechanism makes the information contained by old |Queue|
        instances already used in a multi-threaded simulation run reusable.
        """

        return cls(
            starters=queue_.starters,
            dependencies=queue_.dependencies,
            upstream2downstream=queue_.upstream2downstream,
        )

    def register(self) -> None:
        """Put all |Queue.starters| into the queue."""

        self._first_exception = None
        self._waiting = dict(self.dependencies.items())
        for starter in self.starters:
            self.put(starter)

    # This incorrect override is on purpose (wrapping instead of sublassing `Queue`
    # seems like unnecessary overhead and we want `task_done` only used this way):
    def task_done(  # type: ignore[override]
        self, upstream: devicetools.NodeOrElement | BaseException
    ) -> None:
        """Take the given readily processed node or element, determine which elements
        or nodes become ready for processing, and put them into the queue."""

        if not isinstance(upstream, BaseException):
            for downstream in self.upstream2downstream.get(upstream, ()):
                nmb = self._waiting[downstream]
                if nmb == 1:
                    self.put(downstream)
                else:
                    self._waiting[downstream] -= 1
        elif self._first_exception is None:
            self._first_exception = upstream
        super().task_done()

    if sys.version_info < (3, 13):

        def shutdown(self) -> None:
            """For compatibility with Python 3.12 and earlier."""
            for _ in range(hydpy.pub.options.threads):
                self.put(None)  # type: ignore[arg-type]

    def join(self) -> None:
        """Block the queue until all nodes and elements have been processed.

        If something is wrong, method |Queue.join| tries (with the help of method
        |Worker.run| of class |Worker|) to report the first error that occurred in one
        of the threads:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> for element in hp.elements:
        ...     element.model.simulate_period = None
        >>> with pub.options.threads(4):
        ...     hp.simulate()
        Traceback (most recent call last):
        ...
        TypeError: 'NoneType' object is not callable
        """

        super().join()
        if (exception := self._first_exception) is not None:
            self._first_exception = None
            raise exception


class Worker(threading.Thread):
    """A worker that interacts with the current |Queue| instance and is responsible
    for processing nodes and elements in an individual thread."""

    _queue: Queue
    _elements: devicetools.Elements
    _idx_start: int
    _idx_end: int

    def __init__(self, queue_: Queue, elements: devicetools.Elements) -> None:

        super().__init__()
        self._queue = queue_
        self._elements = elements
        self._idx_start, self._idx_end = hydpy.pub.timegrids.simindices

    def run(self) -> None:
        """Query the next device from the current |Queue| instance, update the relevant
        time series data, and perform a simulation if the device is an element."""

        if sys.version_info < (3, 13):
            stop = AttributeError  # pragma: no cover
        else:  # pragma: no cover
            stop = queue.ShutDown  # pragma: no cover

        while True:
            try:

                try:
                    device = self._queue.get()
                    # Remove when we stop supporting Python 3.12:
                    device.name  # pylint: disable=pointless-statement
                except stop:
                    return

                if isinstance(device, devicetools.Node):
                    self._update_node_series(device)
                else:
                    model = device.model
                    self._update_all_model_series(model)
                    threading_ = model.threading
                    try:
                        model.threading = True
                        model.simulate_period(self._idx_start, self._idx_end)
                    finally:
                        model.threading = threading_

            except BaseException as exception:

                self._queue.task_done(exception)
                return

            self._queue.task_done(device)

    def _update_node_series(self, node: devicetools.Node) -> None:

        i0, i1 = self._idx_start, self._idx_end
        seq_node = node.sequences.sim
        seq_node.series[i0:i1] = 0.0
        for element in node.entries:
            if element not in self._elements:
                continue
            for submodel in element.model.find_submodels(
                include_mainmodel=True
            ).values():
                seqs = submodel.sequences
                for seq_model in itertools.chain(
                    seqs.outlets, seqs.senders, seqs.factors, seqs.fluxes, seqs.states
                ):
                    if (j := seq_model.node2idx.get(node, -1)) != -1:
                        if j is None:
                            seq_node.series[i0:i1] += seq_model.series[i0:i1]
                        else:
                            seq_node.series[i0:i1] += seq_model.series[i0:i1, j]

    def _update_all_model_series(self, model: modeltools.Model) -> None:
        for submodel in model.find_submodels(include_mainmodel=True).values():
            seqs = submodel.sequences
            for seq in itertools.chain(seqs.inputs, seqs.inlets, seqs.receivers):
                self._update_one_model_series(seq)

    def _update_one_model_series(self, sequence: sequencetools.ModelIOSequence) -> None:

        if not sequence.node2idx:
            return

        i0, i1 = self._idx_start, self._idx_end
        series_model = sequence.series
        series_model[i0:i1] = 0.0
        for node, j in sequence.node2idx.items():
            deploymode = node.deploymode
            if deploymode in ("newsim", "oldsim", "oldsim_bi"):
                series_node = node.sequences.sim.series[i0:i1].copy()
            else:
                series_node = node.sequences.obs.series[i0:i1].copy()
                if deploymode != "obs":
                    i_nan = numpy.isnan(series_node)
                    if numpy.any(i_nan):
                        series_node[i_nan] = node.sequences.sim.series[i0:i1][i_nan]
            if j is None:
                series_model[i0:i1] += series_node
            else:
                series_model[i0:i1, j] += series_node


def check_threading(
    hp: hydpytools.HydPy,
    sequence: sequencetools.IOSequence,
    pause: timetools.Date | None = None,
) -> None:
    """Execute on "sequential", then two "parallel", and finally another "sequential"
    simulation run, and check if time the series calculated for all nodes are identical
    in all cases.

    >>> from hydpy.core.threadingtools import check_threading

    Tests based on the HydPy-L-Land example project (with the primary goal of checking
    if all deploy modes are properly supported):

    >>> from hydpy.core.testtools import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> leun = hp.nodes.lahn_leun
    >>> kalk = hp.nodes.lahn_kalk

    >>> check_threading(hp, kalk.sequences.sim)
    54.019337, 37.257561, 31.865308, 28.359542

    >>> check_threading(hp, kalk.sequences.sim, "1996-01-03")
    54.019337, 37.257561, 31.865308, 28.359542

    >>> leun.deploymode = "oldsim"
    >>> leun.sequences.sim.series -= 10.0
    >>> check_threading(hp, kalk.sequences.sim)
    44.019337, 27.257561, 21.865308, 18.359542

    >>> leun.deploymode = "obs"
    >>> leun.sequences.obs.series = 0.0
    >>> check_threading(hp, kalk.sequences.sim)
    11.672862, 10.100089, 8.984317, 8.202706

    >>> leun.deploymode = "obs"
    >>> leun.sequences.obs.series = 0.0
    >>> check_threading(hp, kalk.sequences.sim)
    11.672862, 10.100089, 8.984317, 8.202706

    >>> from numpy import nan
    >>> with pub.options.checkseries(False):
    ...     leun.sequences.obs.series= 0.0, nan, 0.0, nan
    >>> check_threading(hp, kalk.sequences.sim)
    11.672862, nan, 8.984317, nan

    >>> leun.deploymode = "obs_newsim"
    >>> check_threading(hp, kalk.sequences.sim)
    11.672862, 37.257561, 8.984317, 28.359542

    >>> leun.deploymode = "obs_oldsim"
    >>> leun.sequences.sim.series = 32.3697, 17.210443, 12.930066, 10.20133
    >>> check_threading(hp, kalk.sequences.sim)
    11.672862, 27.310532, 8.984317, 18.404036

    >>> leun.deploymode = "newsim"
    >>> leun.sequences.sim.series = 32.3697, 17.210443, 12.930066, 10.20133
    >>> check_threading(hp, kalk.sequences.sim)
    54.019337, 37.257561, 31.865308, 28.359542

    Tests based on the interpolation example project (with the primary goal of checking
    if the input node mechanism is properly supported within the parallelisable part
    of a network):

    >>> from hydpy.core.testtools import prepare_interpolation_example
    >>> hp, pub = prepare_interpolation_example()

    >>> check_threading(hp, hp.nodes.q12.sequences.sim)
    0.853716, 0.864633, 1.037645

    >>> hp.nodes.in1.deploymode = "oldsim"
    >>> hp.nodes.in1.sequences.sim.series = hp.nodes.in1.sequences.obs.series
    >>> hp.nodes.in1.sequences.obs.series = 0.0
    >>> check_threading(hp, hp.nodes.q12.sequences.sim)
    0.853716, 0.864633, 1.037645

    Tests based on the receiver example project (with the primary goal of checking if
    all deploy modes are properly supported around the transitions between the
    parallelisable and the non-parallelisable parts of a network):

    >>> from hydpy.core.testtools import prepare_receiver_example
    >>> hp, pub = prepare_receiver_example()

    >>> check_threading(hp, hp.nodes.n4.sequences.sim)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707

    >>> from hydpy import print_vector
    >>> print_vector(hp.elements.d.model.sequences.receivers.q.series)
    2.324939, 2.0521, 1.834626, 1.822902, 1.853202, 1.876488

    >>> hp.nodes.n2.deploymode = "oldsim"
    >>> check_threading(hp, hp.nodes.n4.sequences.sim)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707

    >>> print_vector(hp.elements.d.model.sequences.receivers.q.series)
    2.324939, 2.0521, 1.834626, 1.822902, 1.853202, 1.876488

    >>> hp.nodes.n2.deploymode = "obs"
    >>> hp.nodes.n2.sequences.obs.series = hp.nodes.n2.sequences.sim.series
    >>> hp.nodes.n2.sequences.sim.series = 0.0
    >>> check_threading(hp, hp.nodes.n4.sequences.sim)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707

    >>> hp.nodes.n2.deploymode = "obs_oldsim"
    >>> hp.nodes.n2.sequences.obs.series[2] = nan
    >>> check_threading(hp, hp.nodes.n4.sequences.sim)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707

    >>> hp.nodes.n2.deploymode = "obs_newsim"
    >>> hp.nodes.n2.sequences.obs.series[2] = nan
    >>> check_threading(hp, hp.nodes.n4.sequences.sim)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707

    Tests based on the collective example project (with the primary goals of checking
    if collective elements and the output node mechanism are properly supported):

    >>> from hydpy.core.testtools import prepare_collective_example
    >>> hp, pub = prepare_collective_example()

    >>> check_threading(hp, hp.nodes.c3_out.sequences.sim)
    0.409196, 0.386017, 0.337494, 0.279784, 0.203433, 0.071322
    """
    experiments = []
    for threads in (0, 4, 4, 0):
        experiment = {}
        hp.reset_conditions()
        sequence.series[:] = 0.0
        with hydpy.pub.options.threads(threads):
            timegrids = hydpy.pub.timegrids
            if pause is not None:
                timegrids.sim.lastdate = pause
            hp.simulate()
            if pause is not None:
                timegrids.sim.firstdate = pause
                timegrids.sim.lastdate = timegrids.init.lastdate
                hp.simulate()
                timegrids.sim.firstdate = timegrids.init.firstdate
        for node in hp.nodes:
            experiment[node] = node.sequences.sim.series.copy()
        experiments.append(experiment)
    for i, experiment in enumerate(experiments[1:]):
        for node, series in experiment.items():
            assert numpy.array_equal(
                experiments[0][node], series, equal_nan=True
            ), f"experiment `1` vs `{i + 2}`, node {node.name}"
    objecttools.print_vector(sequence.series)
