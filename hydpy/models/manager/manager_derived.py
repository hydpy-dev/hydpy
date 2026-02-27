# pylint: disable=missing-module-docstring

# import...

# ...from standard library
import itertools

# ...from site-package
import inflect
import networkx

# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.auxs import smoothtools

from hydpy.models.manager import manager_parameters
from hydpy.models.manager import manager_control

# from hydpy.models import manager_lwc   actual import below


class Seconds(parametertools.SecondsParameter):
    """Length of the actual simulation step size [s]."""


class DischargeSmoothPar(parametertools.Parameter):
    """Smoothing parameter related to |DischargeTolerance| [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (manager_control.DischargeTolerance,)

    def update(self) -> None:
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following example in
        detail:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_max1, smooth_min1
        >>> from hydpy import round_
        >>> round_(smooth_max1(4.0, 1.5, derived.dischargesmoothpar))
        4.0
        >>> round_(smooth_min1(4.0, 1.5, derived.dischargesmoothpar))
        1.5
        >>> dischargetolerance(2.5)
        >>> derived.dischargesmoothpar.update()
        >>> round_(smooth_max1(4.0, 1.5, derived.dischargesmoothpar))
        4.01
        >>> round_(smooth_min1(4.0, 1.5, derived.dischargesmoothpar))
        1.49
        """
        metapar = self.subpars.pars.control.dischargetolerance
        self(smoothtools.calc_smoothpar_max1(metapar.value))


class VolumeSmoothPar(manager_parameters.ParameterSource):
    """Smoothing parameter related to |VolumeTolerance| [m³/s]."""

    TYPE = float
    TIME = None
    SPAN = (0.0, None)

    CONTROLPARAMETERS = (manager_control.VolumeTolerance,)

    def update(self) -> None:
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following example in
        detail:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources("a", "b")
        >>> volumetolerance(0.0, 2.5)
        >>> derived.volumesmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_max1, smooth_min1
        >>> from hydpy import round_
        >>> round_(smooth_max1(4.0, 1.5, derived.volumesmoothpar.values[0]))
        4.0
        >>> round_(smooth_min1(4.0, 1.5, derived.volumesmoothpar.values[0]))
        1.5
        >>> round_(smooth_max1(4.0, 1.5, derived.volumesmoothpar.values[1]))
        4.01
        >>> round_(smooth_min1(4.0, 1.5, derived.volumesmoothpar.values[1]))
        1.49
        """
        self.values = 0.0
        values = self.values
        for i, value in enumerate(self.subpars.pars.control.volumetolerance.values):
            values[i] = smoothtools.calc_smoothpar_max1(value)


class MemoryLength(parametertools.NmbParameter):
    """Number of simulation steps to be covered by some log sequences [-]."""

    TYPE = int
    TIME = None
    SPAN = (0, None)

    CONTROLPARAMETERS = (manager_control.TimeDelay, manager_control.TimeWindow)

    def update(self) -> None:
        """Update the memory length according to
        :math:`MemoryLength = TimeDelay + TimeWindow`.

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> timedelay(2)
        >>> timewindow(3)
        >>> derived.memorylength.update()
        >>> derived.memorylength
        memorylength(5)
        """
        control = self.subpars.pars.control
        self(control.timedelay.value + control.timewindow.value)


class Adjacency(parametertools.Parameter):
    """An (incomplete) adjacency matrix of the target node and all source elements [-].

    See method |Adjacency.update| for more information.
    """

    NDIM: Final[Literal[2]] = 2
    TYPE = bool
    TIME = None
    SPAN = (False, True)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, manager_control.Sources):
            self.__hydpy__change_shape_if_necessary__((p.value, p.value + 1))

    def update(self) -> None:
        """Determine a directed subgraph that contains only the target node and all
        selected source elements.

        We create the following setting where the sources `d_1` and `d_2` release their
        water toward the target node `t`, `d_1a` releases its water to `d_1`, `d_2a`
        and `d_2b` release their water to `d_2`, and `d_2b1` releases its water to
        `d_2b`:

        >>> from hydpy import Element, FusedVariable, Node, Nodes
        >>> from hydpy.aliases import (
        ...     dam_observers_A,
        ...     dam_states_WaterVolume,
        ...     manager_senders_Request,
        ...     manager_receivers_WaterVolume,
        ... )
        >>> t = Node("t")
        >>> WaterVolume = FusedVariable(
        ...     "WaterVolume", dam_states_WaterVolume, manager_receivers_WaterVolume
        ... )
        >>> v_1, v_1a, v_2, v_2a, v_2b, v_2b1 = Nodes(
        ...     "v_1", "v_1a", "v_2", "v_2a", "v_2b", "v_2b1",
        ...     defaultvariable=WaterVolume,
        ... )
        >>> Request = FusedVariable("Request", dam_observers_A, manager_senders_Request)
        >>> r_1, r_1a, r_2, r_2a, r_2b, r_2b1 = Nodes(
        ...     "r_1", "r_1a", "r_2", "r_2a", "r_2b", "r_2b1", defaultvariable=Request,
        ... )
        >>> d_1 = Element("d_1", inlets="q_1a_1", outlets=t, observers=r_1, outputs=v_1)
        >>> d_1a = Element("d_1a", outlets="q_1a_1", observers=r_1a, outputs=v_1a)
        >>> d_2 = Element(
        ...     "d_2", inlets=("q_2a_2", "q_2b_2"),
        ...     outlets=t, observers=r_2, outputs=v_2,
        ... )
        >>> d_2a = Element("d_2a", outlets="q_2a_2", observers=r_2a, outputs=v_2a)
        >>> d_2b = Element(
        ...     "d_2b", inlets="q_2b1_2b",
        ...     outlets="q_2b_2", observers=r_2b, outputs=v_2b,
        ... )
        >>> d_2b1 = Element("d_2b1", outlets="q_2b1_2b", observers=r_2b1, outputs=v_2b1)

        >>> lwc = Element(
        ...     "lwc",
        ...     receivers=[t, v_1, v_1a, v_2, v_2a, v_2b, v_2b1],
        ...     senders=[r_1, r_1a, r_2, r_2a, r_2b, r_2b1],
        ... )

        Method |Adjacency.update| converts this setting into an adjacency matrix.  The
        first column marks those sources (`d1` and `d_2`) that release their water
        directly to the target node.  The second column marks those sources (`d_1a`)
        that release their water to the first source (`d1`); the third column marks
        those sources (none) that release their water to the second source (`d_1a`),
        and so on.  Note that the adjacency matrix is not square because we know that
        the target node does not release any water towards of the sources, which means
        we can omit the corresponding (first) row:

        >>> from hydpy.models.manager_lwc import *
        >>> parameterstep()
        >>> sources("d_1", "d_1a", "d_2", "d_2a", "d_2b", "d_2b1")
        >>> lwc.model = model
        >>> derived.adjacency.update()
        >>> derived.adjacency
        adjacency([[True, False, False, False, False, False, False],
                   [False, True, False, False, False, False, False],
                   [True, False, False, False, False, False, False],
                   [False, False, False, True, False, False, False],
                   [False, False, False, True, False, False, False],
                   [False, False, False, False, False, True, False]])

        The adjacency matrix only represents the subgraph of the relevant source
        elements:

        >>> sources("d_1a", "d_2", "d_2a", "d_2b1")
        >>> derived.adjacency.update()
        >>> derived.adjacency
        adjacency([[True, False, False, False, False],
                   [True, False, False, False, False],
                   [False, False, True, False, False],
                   [False, False, True, False, False]])

        All source elements must, of course, lie upstream of the target node:

        >>> d_3 = Element("d_3", outlets="q_3")
        >>> sources("d_1", "d_2", "d_3")
        >>> derived.adjacency.update()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to update parameter `adjacency` of element `lwc`, \
the following error occurred: There are zero paths between the source element `d_3` \
and the target node `t`, but there must be exactly one.

        A branching of the river network above the target node can mean trouble.
        |Adjacency.update| thus searches for multiple paths between the target node and
        all source elements (this strategy might not cover all problematic cases and
        might also complain about some unproblematic ones - we might improve the
        algorithm later):

        >>> sources("d_1", "d_1a", "d_2", "d_2a", "d_2b", "d_2b1")
        >>> d_1a.outlets.add_device("b", force=True)
        >>> d_2a.inlets.add_device("b", force=True)
        >>> derived.adjacency.update()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to update parameter `adjacency` of element `lwc`, \
the following error occurred: There are two paths between the source element `d_1a` \
and the target node `t`, but there must be exactly one.
        """

        try:

            registry = devicetools._registry  # pylint: disable=protected-access
            _nodes = tuple(registry[devicetools.Node].values())
            nodes = devicetools.Nodes(_nodes)  # type: ignore[arg-type]
            _elements = tuple(registry[devicetools.Element].values())
            elements = devicetools.Elements(_elements)  # type: ignore[arg-type]
            graph = hydpytools.create_directedgraph(nodes=nodes, elements=elements)

            sources = self.subpars.pars.control.sources
            assert isinstance(sources, manager_control.Sources)
            name2element = {n: elements[n] for n in sources.sourcenames}
            target = self._target

            subgraph = networkx.DiGraph()
            subgraph.add_node(target)
            subgraph.add_nodes_from(name2element.values())

            def _fill_subgraph(
                downstream: devicetools.NodeOrElement,
                upstream: devicetools.Element,
                check: bool,
            ) -> None:
                p = networkx.all_simple_paths(graph, target=downstream, source=upstream)
                paths = tuple(p)
                n = len(paths)
                if check:
                    if n != 1:
                        e = inflect.engine()
                        number = e.number_to_words(n)  # type: ignore[arg-type]
                        raise RuntimeError(
                            f"There {e.plural('is', n)} {number} "
                            f"{e.plural('path', n)} between the source element "
                            f"`{upstream}` and the target node `{target}`, but there "
                            f"must be exactly one."
                        )
                if n > 0:
                    if all(d.name not in name2element for d in paths[0][1:-1]):
                        subgraph.add_edge(upstream, downstream)

            for source in name2element.values():
                _fill_subgraph(upstream=source, downstream=target, check=True)
            for source, subtarget in itertools.permutations(name2element.values(), 2):
                _fill_subgraph(upstream=source, downstream=subtarget, check=False)

            self.value = networkx.to_numpy_array(
                subgraph, nodelist=(target,) + tuple(name2element.values()), dtype=bool
            )[1:, :]

        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to update parameter {objecttools.elementphrase(self)}"
            )

    @property
    def _target(self) -> devicetools.Node:
        receivers = self.subpars.pars.model.element.receivers
        potential_targets = [r for r in receivers if r.variable == "Q"]
        assert len(potential_targets) == 1
        return potential_targets[0]


class Order(parametertools.Parameter):
    """The processing order of all source elements [-].

    See method |Order.update| for more information.
    """

    NDIM: Final[Literal[1]] = 1
    TYPE = int
    TIME = None
    SPAN = (0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, manager_control.Sources):
            self.__hydpy__change_shape_if_necessary__((p.value,))

    def update(self) -> None:
        """Determine the processing order based on a (reversed) topological sort.

        The following order ensures we do not process a source element before we have
        processed its downstream source elements:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources("d_1", "d_1a", "d_2", "d_2a", "d_2b", "d_2b1")
        >>> derived.adjacency([[True, False, False, False, False, False, False],
        ...                    [False, True, False, False, False, False, False],
        ...                    [True, False, False, False, False, False, False],
        ...                    [False, False, False, True, False, False, False],
        ...                    [False, False, False, True, False, False, False],
        ...                    [False, False, False, False, False, True, False]])
        >>> derived.order.update()
        >>> derived.order
        order(2, 4, 0, 5, 3, 1)
        """
        subgraph = networkx.from_numpy_array(
            self.subpars.adjacency.values[:, 1:], create_using=networkx.DiGraph
        )
        self.values = tuple(networkx.topological_sort(subgraph))[::-1]
