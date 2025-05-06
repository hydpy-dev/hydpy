"""

>>> from hydpy.core.threadingtools import check_threading

>>> from hydpy.core.testtools import prepare_full_example_2
>>> hp, pub, TestIO = prepare_full_example_2()
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
54.019337, 37.257561, 31.865308, 28.359542

>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim, "1996-01-03")
54.019337, 37.257561, 31.865308, 28.359542

>>> hp.nodes.lahn_leun.deploymode = "oldsim"
>>> hp.nodes.lahn_leun.sequences.sim.series -= 10.0
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
44.019337, 27.257561, 21.865308, 18.359542

>>> hp.nodes.lahn_leun.deploymode = "obs"
>>> hp.nodes.lahn_leun.sequences.obs.series = 0.0
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)  # asdf
11.672862, 10.100089, 8.984317, 8.202706

>>> hp.nodes.lahn_leun.deploymode = "obs"
>>> hp.nodes.lahn_leun.sequences.obs.series = 0.0
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
11.672862, 10.100089, 8.984317, 8.202706

>>> from numpy import nan
>>> with pub.options.checkseries(False):
...     hp.nodes.lahn_leun.sequences.obs.series= 0.0, nan, 0.0, nan
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
11.672862, nan, 8.984317, nan

>>> hp.nodes.lahn_leun.deploymode = "obs_newsim"
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
11.672862, 37.257561, 8.984317, 28.359542

>>> hp.nodes.lahn_leun.deploymode = "obs_oldsim"
>>> hp.nodes.lahn_leun.sequences.sim.series = 32.3697, 17.210443, 12.930066, 10.20133
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
11.672862, 27.310532, 8.984317, 18.404036

>>> hp.nodes.lahn_leun.deploymode = "newsim"
>>> hp.nodes.lahn_leun.sequences.sim.series = 32.3697, 17.210443, 12.930066, 10.20133
>>> check_threading(hp, hp.nodes.lahn_kalk.sequences.sim)
54.019337, 37.257561, 31.865308, 28.359542




>>> from hydpy.core.testtools import prepare_interpolation_example
>>> hp, pub = prepare_interpolation_example()

>>> check_threading(hp, hp.nodes.q12.sequences.sim)
0.853716, 0.864633, 1.037645

>>> hp.nodes.in1.deploymode = "oldsim"
>>> hp.nodes.in1.sequences.sim.series = hp.nodes.in1.sequences.obs.series
>>> hp.nodes.in1.sequences.obs.series = 0.0
>>> check_threading(hp, hp.nodes.q12.sequences.sim)
0.853716, 0.864633, 1.037645





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



>>> from hydpy.core.testtools import prepare_collective_example
>>> hp, pub = prepare_collective_example()

>>> check_threading(hp, hp.nodes.c3_out.sequences.sim)
0.409196, 0.386017, 0.337494, 0.279784, 0.203433, 0.071322
"""

from __future__ import annotations
import itertools
import queue
import sys
import threading

import networkx
import numpy
from networkx import descendants

import hydpy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *


class Parallelisability:

    parallel_nodes: devicetools.Nodes
    parallel_elements: devicetools.Elements
    sequential_nodes: devicetools.Nodes
    sequential_elements: devicetools.Elements
    transition_nodes: devicetools.Nodes

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

    upstream2downstream: dict[
        devicetools.NodeOrElement, list[devicetools.NodeOrElement]
    ]
    starters: list[devicetools.NodeOrElement]
    dependencies: dict[devicetools.NodeOrElement, int]
    waiting: dict[devicetools.NodeOrElement, int]
    _first_exception: Exception | None

    def __init__(
        self, nodes: devicetools.Nodes, elements: devicetools.Elements
    ) -> None:
        super().__init__()
        self._first_exception = None

        upstream2downstream: dict[
            devicetools.NodeOrElement, list[devicetools.NodeOrElement]
        ] = {}
        successors2starter: list[tuple[int, devicetools.NodeOrElement]] = []
        dependencies: dict[devicetools.NodeOrElement, int] = {}

        graph = hydpytools.create_directedgraph(nodes, elements)
        successors = networkx.dfs_successors

        for e in elements:
            nmb_in = sum(
                node.deploymode in ("newsim", "obs_newsim")
                for node in itertools.chain(e.inlets, e.receivers, e.inputs)
            )
            if nmb_in:
                dependencies[e] = nmb_in
            else:
                successors2starter.append((len(successors(graph, e)), e))
            upstream2downstream[e] = [
                n
                for n in itertools.chain(e.outlets, e.senders, e.outputs)
                if n.deploymode in ("newsim", "obs", "obs_newsim", "obs_bi")
            ]

        for n in nodes:
            if n.deploymode in ("newsim", "obs", "obs_newsim", "obs_bi"):
                if nmb_in := sum(e in elements for e in n.entries):
                    dependencies[n] = nmb_in
                else:
                    successors2starter.append((len(successors(graph, n)), n))
                if n.deploymode in ("newsim", "obs_newsim"):
                    upstream2downstream[n] = list(e for e in n.exits if e in elements)

        self.upstream2downstream = upstream2downstream
        self.starters = [d for n, d in sorted(successors2starter, key=lambda t: t[0])]
        self.dependencies = dependencies

    def register(self) -> None:
        self.waiting = self.dependencies.copy()
        for starter in self.starters:
            self.put(starter)

    # This incorrect override is on purpose (wrapping instead of sublassing `Queue`
    # seems like unnecessary overhead and we want `task_done` only used this way):
    def task_done(  # type: ignore[override]
        self, upstream: devicetools.NodeOrElement | BaseException
    ) -> None:
        if not isinstance(upstream, BaseException):
            for downstream in self.upstream2downstream.get(upstream, ()):
                nmb = self.waiting[downstream]
                if nmb == 1:
                    self.put(downstream)
                else:
                    self.waiting[downstream] -= 1
        elif self._first_exception is None:
            self._first_exception = upstream
        super().task_done()

    if sys.version_info < (3, 13):

        def shutdown(self) -> None:
            for _ in range(hydpy.pub.options.threads):
                self.put(None)  # type: ignore[arg-type]

    def join(self) -> None:
        super().join()
        if (exception := self._first_exception) is not None:
            self._first_exception = None
            raise exception


class Worker(threading.Thread):
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

        if sys.version_info < (3, 13):
            stop = AttributeError
        else:
            stop = queue.ShutDown

        while True:
            try:

                try:
                    device = self._queue.get()
                    # Remove when we stop supporting Python 3.12:
                    device.name  # pylint: disable=pointless-statement
                except stop:
                    return

                if isinstance(device, devicetools.Node):
                    self.update_node_series(device)
                else:
                    model = device.model
                    self.update_all_model_series(model)
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

    def update_node_series(self, node: devicetools.Node) -> None:

        if node.deploymode in ("oldsim", "obs_oldsim", "oldsim_bi", "obs_oldsim_bi"):
            return

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

    def update_all_model_series(self, model: modeltools.Model) -> None:
        for submodel in model.find_submodels(include_mainmodel=True).values():
            seqs = submodel.sequences
            for seq in itertools.chain(seqs.inputs, seqs.inlets, seqs.receivers):
                self.update_one_model_series(seq)

    def update_one_model_series(self, sequence) -> None:

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
            try:
                assert numpy.array_equal(
                    numpy.round(experiments[0][node], 12),
                    numpy.round(series, 12),
                    equal_nan=True,
                ), f"experiment `1` vs `{i + 2}`, node {node.name}"
            except:
                print("blöd")
    objecttools.print_vector(sequence.series)
