# import...
# ...from standard library
from __future__ import annotations
import itertools
import queue
import sys
import threading

# ...from site-packages
import networkx
import numpy

# ...from HydPy
import hydpy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class Queue(queue.LifoQueue[devicetools.NodeOrElement]):

    upstream2downstream: dict[
        devicetools.NodeOrElement, list[devicetools.NodeOrElement]
    ]
    starters: list[devicetools.NodeOrElement]
    dependencies: dict[devicetools.NodeOrElement, int]
    waiting: dict[devicetools.NodeOrElement, int]

    def __init__(
        self, nodes: devicetools.Nodes, elements: devicetools.Elements
    ) -> None:
        super().__init__()

        upstream2downstream: dict[
            devicetools.NodeOrElement, list[devicetools.NodeOrElement]
        ] = {}
        starters: list[tuple[int, devicetools.NodeOrElement]] = []
        dependencies: dict[devicetools.NodeOrElement, int] = {}

        graph = hydpytools.create_directedgraph(nodes, elements)
        successors = networkx.dfs_successors

        for element in elements:
            if nmb_in := (
                len(element.inlets) + len(element.receivers) + len(element.inputs)
            ):
                dependencies[element] = nmb_in
            else:
                starters.append((len(successors(graph, element)), element))
            upstream2downstream[element] = list(element.outlets)

        for node in nodes:
            if nmb_in := len(node.entries):
                dependencies[node] = nmb_in
            else:
                starters.append((len(successors(graph, node)), node))
            upstream2downstream[node] = list(node.exits)

        self.upstream2downstream = upstream2downstream
        self.starters = [d for n, d in sorted(starters, key=lambda t: t[0])]
        self.dependencies = dependencies

    def register(self) -> None:
        self.waiting = self.dependencies.copy()
        for starter in self.starters:
            self.put(starter)

    # This incorrect override is on purpose (wrapping instead of sublassing `Queue`
    # seems like unnecessary overhead and we want `task_done` only used this way):
    def task_done(  # type: ignore[override]
        self, upstream: devicetools.NodeOrElement
    ) -> None:
        for downstream in self.upstream2downstream.get(upstream, ()):
            nmb = self.waiting[downstream]
            if nmb == 1:
                self.put(downstream)
            else:
                self.waiting[downstream] -= 1
        super().task_done()

    if sys.version_info < (3, 13):

        def shutdown(self) -> None:
            for _ in range(hydpy.pub.options.threads):
                self.put(None)  # type: ignore[arg-type]


class Worker(threading.Thread):
    _queue: Queue
    _idx_start: int
    _idx_end: int

    def __init__(self, queue_: Queue) -> None:
        super().__init__()
        self._queue = queue_
        self._idx_start, self._idx_end = hydpy.pub.timegrids.simindices

    def run(self) -> None:

        if sys.version_info < (3, 13):
            stop = AttributeError
        else:
            stop = queue.ShutDown

        while True:

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

            self._queue.task_done(device)

    def update_node_series(self, node: devicetools.Node) -> None:

        if node.deploymode in ("oldsim", "obs_oldsim", "oldsim_bi", "obs_oldsim_bi"):
            return

        i0, i1 = self._idx_start, self._idx_end
        seq_node = node.sequences.sim
        seq_node.series[i0:i1] = 0.0
        for element in node.entries:
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
