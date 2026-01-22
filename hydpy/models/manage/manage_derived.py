# pylint: disable=missing-module-docstring

# from site-package
import networkx

# import...
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import parametertools

# from manage
# from hydpy.models import manage_lwc   actual import below


class Seconds(parametertools.SecondsParameter):
    """Length of the actual simulation step size [s]."""


class NmbActiveSources(parametertools.Parameter):
    """ToDo [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)


class Adjacency(parametertools.Parameter):
    """ToDo [-]."""

    NDIM, TYPE, TIME, SPAN = 2, bool, None, (False, True)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.shape = (p.value, p.value + 1)

    def update(self) -> None:
        """ToDo


        >>> from hydpy import Element, Node, Nodes
        >>> from hydpy.aliases import dam_states_WaterVolume as WV
        >>> required1, required2 = Nodes("required1", "required2")
        >>> t = Node("t")
        >>> v_1, v_1a, v_2, v_2a, v_2b, v_2b1 = Nodes(
        ...     "v_1", "v_1a", "v_2", "v_2a", "v_2b", "v_2b1", defaultvariable=WV
        ... )
        >>> d_1 = Element("d_1", inlets="q_1a_1", outlets=t, outputs=v_1)
        >>> d_1a = Element("d_1a", outlets="q_1a_1", outputs=v_1a)
        >>> d_2 = Element("d_2", inlets=("q_2a_2", "q_2b_2"), outlets=t, outputs=v_2)
        >>> d_2a = Element("d_2a", outlets="q_2a_2", outputs=v_2a)
        >>> d_2b = Element("d_2b", inlets="q_2b1_2b", outlets="q_2b_2", outputs=v_2b)
        >>> d_2b1 = Element("d_2b1", outlets="q_2b1_2b", outputs=v_2b1)

        >>> lwc = Element(
        ...     "lwc",
        ...     receivers=[t, v_1, v_1a, v_2, v_2a, v_2b, v_2b1],
        ... )

        >>> from hydpy.models.manage_lwc import *
        >>> parameterstep()
        >>> lwc.model = model
        >>> nmbsources(6)
        >>> active(d_1=True, d_1a=True, d_2=True, d_2a=True, d_2b=True, d_2b1=True)
        >>> derived.adjacency.update()
        >>> model.sourcenames
        ['d_1', 'd_1a', 'd_2', 'd_2a', 'd_2b', 'd_2b1']
        >>> derived.adjacency
        adjacency([[True, False, False, False, False, False, False],
                   [False, True, False, False, False, False, False],
                   [True, False, False, False, False, False, False],
                   [False, False, False, True, False, False, False],
                   [False, False, False, True, False, False, False],
                   [False, False, False, False, False, True, False]])

        ToDo: include routing models in testing
        """

        from hydpy.models import manage_lwc

        model = self.subpars.pars.model
        assert isinstance(model, manage_lwc.Model)

        nodes = devicetools.Nodes(
            tuple(devicetools._registry[devicetools.Node].values())
        )
        elements = devicetools.Elements(
            tuple(devicetools._registry[devicetools.Element].values())
        )
        graph = hydpytools.create_directedgraph(nodes=nodes, elements=elements)

        source_name2element = {n: elements[n] for n in model.sourcenames}
        target = self._target

        subgraph = networkx.DiGraph()
        subgraph.add_node(target)
        subgraph.add_nodes_from(source_name2element.values())

        for source in source_name2element.values():
            paths = tuple(
                networkx.all_simple_paths(graph, target=target, source=source)
            )
            assert len(paths) == 1
            path = paths[0]
            if all(d.name not in source_name2element for d in path[1:-1]):
                subgraph.add_edge(source, target)

        for source in source_name2element.values():
            for target_ in source_name2element.values():
                if source is not target_:
                    paths = tuple(
                        networkx.all_simple_paths(graph, target=target_, source=source)
                    )
                    assert len(paths) < 2
                    if len(paths) == 1:
                        path = paths[0]
                        if all(d.name not in source_name2element for d in path[1:-1]):
                            subgraph.add_edge(source, target_)

        self.value = networkx.to_numpy_array(
            subgraph,
            nodelist=(target,) + tuple(source_name2element.values()),
            dtype=bool,
        )[1:, :]

    @property
    def _target(self) -> devicetools.Node:
        potential_targets = [
            r
            for r in self.subpars.pars.model.element.receivers
            if str(r.variable) == "Q"
        ]
        assert len(potential_targets) == 1
        return potential_targets[0]


"t", "d_1", "d_1a", "d_2", "d_2a", "d_2b", "d_2b1"
