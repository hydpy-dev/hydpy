# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import inflect

# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class X(sequencetools.ObserverSequence):
    """Arbitrary kind of input data [?]."""

    NDIM, NUMERIC = 1, False

    _observernodes: tuple[str, ...] | None = None

    @property
    def observernodes(self) -> tuple[str, ...]:
        """The relevant observer node's names.

        If necessary, the following error message tries to clarify the usual way of \
        specifying the relevant observer nodes:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> observers.x.observernodes
        Traceback (most recent call last):
        ...
        RuntimeError: The observer sequence `x` of element `?` does not know the \
names of the observer nodes it should be connected with.  Consider providing this \
information via the control parameter `observernodes`.

        >>> observernodes("gauge_1", "gauge_2")
        >>> observers.x.observernodes
        ('gauge_1', 'gauge_2')
        """
        if self._observernodes is None:
            observernodes = self.subseqs.seqs.model.parameters.control.observernodes
            raise RuntimeError(
                f"The observer sequence {objecttools.elementphrase(self)} does not "
                f"know the names of the observer nodes it should be connected with.  "
                f"Consider providing this information via the control parameter "
                f"`{observernodes.name}`."
            )
        return self._observernodes

    @observernodes.setter
    def observernodes(self, names: tuple[str, ...]) -> None:
        self._observernodes = names

    def connect_to_nodes(
        self,
        group: Literal[
            "inlets", "receivers", "inputs", "outlets", "senders", "observers"
        ],
        available_nodes: list[devicetools.Node],
        applied_nodes: list[devicetools.Node],
        report_noconnect: bool,
    ) -> None:
        """Establish pointer connections with the relevant observer nodes.

        The selection of the observer nodes relies on the nodes' names instead of their
        variable types.  We demonstrate this by using |dam_detention| as an example
        base model, which can handle an arbitrary number of |exch_interp| submodels:

        >>> from hydpy.models.dam_detention import *
        >>> parameterstep()

        We start with defining an element not connected to any observer nodes and a
        |dam_detention| model not handling any submodels and so not any observation
        series:

        >>> from hydpy import Element, PPoly, print_vector
        >>> basin = Element("basin", inlets="inflow", outlets="outflow")
        >>> nmbsafereleasemodels(0)
        >>> basin.model = model

        After adding a single submodel that wants to be connected to the still missing
        observer node `gauge_1`, |exch_observers.X.connect_to_nodes| raises the
        following error:

        >>> nmbsafereleasemodels(1)
        >>> with model.add_safereleasemodel("exch_interp", position=0):
        ...     observernodes("gauge_1")
        ...     x2y(PPoly.from_data(xs=[0.0], ys=[0.0]))
        >>> basin.model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `observer` \
sequences of the model handled by element `basin`, the following error occurred: The \
following node is unavailable: gauge_1.

        Adding a node named `gauge_1` as an inlet node makes no difference:

        >>> basin.inlets = "gauge_1"
        >>> basin.model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `observer` \
sequences of the model handled by element `basin`, the following error occurred: The \
following node is unavailable: gauge_1.

        After also adding `gauge_1` as an observer node,
        |exch_observers.X.connect_to_nodes| builds a proper connection to it without
        interfering with the general functionality, which also establishes a connection
        between this node and the main model's inlet sequence |dam_inlets.Q|:

        >>> basin.observers = "gauge_1"
        >>> basin.model.connect()
        >>> basin.observers.gauge_1.sequences.sim.value = 1.0
        >>> basin.model.update_inlets()
        >>> print_vector(basin.model.sequences.inlets.q.value)
        1.0, 0.0
        >>> safereleasemodel = basin.model.safereleasemodels[0]
        >>> safereleasemodel.update_observers()
        >>> print_vector(safereleasemodel.sequences.observers.x.value)
        1.0

        The following two examples demonstrate that both the error reporting and the
        connection mechanism work in more complex cases as well:

        >>> basin.observers = "gauge_3"
        >>> nmbsafereleasemodels(2)
        >>> with model.add_safereleasemodel("exch_interp", position=0):
        ...     observernodes("gauge_1")
        ...     x2y(PPoly.from_data(xs=[0.0], ys=[0.0]))
        >>> with model.add_safereleasemodel("exch_interp", position=1):
        ...     observernodes("gauge_2", "gauge_3", "gauge_4")
        ...     x2y(PPoly.from_data(xs=[0.0], ys=[0.0]))
        >>> basin.model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `observer` \
sequences of the model handled by element `basin`, the following error occurred: The \
following nodes are unavailable: gauge_2 and gauge_4.

        >>> from hydpy import print_vector
        >>> basin.observers = ("gauge_2", "gauge_4")
        >>> basin.model.connect()
        >>> basin.observers.gauge_1.sequences.sim.value = 1.0
        >>> basin.observers.gauge_2.sequences.sim.value = 4.0
        >>> basin.observers.gauge_3.sequences.sim.value = 3.0
        >>> basin.observers.gauge_4.sequences.sim.value = 2.0
        >>> safereleasemodel = basin.model.safereleasemodels[0]
        >>> safereleasemodel.update_observers()
        >>> print_vector(safereleasemodel.sequences.observers.x.value)
        1.0
        >>> safereleasemodel = basin.model.safereleasemodels[1]
        >>> safereleasemodel.update_observers()
        >>> print_vector(safereleasemodel.sequences.observers.x.values)
        4.0, 3.0, 2.0

        The error reporting on the existence of non-connectible nodes works as usual:

        >>> basin.observers = "gauge_5"
        >>> basin.model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `observer` \
sequences of the model handled by element `basin`, the following error occurred: The \
following nodes have not been connected to any sequences: gauge_5.
        """

        self.node2idx = {}
        self.shape = len(self.observernodes)
        remaining_idxs = set(range(self.shape[0]))
        for node in available_nodes:
            if node.name in self.observernodes:
                idx = self.observernodes.index(node.name)
                self.set_pointer(node.get_double(group), idx)
                self.node2idx[node] = idx
                applied_nodes.append(node)
                remaining_idxs.remove(idx)
        if nmb := len(remaining_idxs):
            p = inflect.engine()
            remaining_names = [self.observernodes[i] for i in sorted(remaining_idxs)]
            raise RuntimeError(
                f"The following {p.plural_noun('node', nmb)} "
                f"{p.plural_verb('is', nmb)} unavailable: {p.join(remaining_names)}."
            )
