# -*- coding: utf-8 -*-
"""This modules implements the fundamental features for structuring *HydPy* projects.

Module |devicetools| provides two |Device| subclasses, |Node| and |Element|.  In this
documentation, "node" stands for an object of class |Node|, "element" for an object of
class |Element|, and "device" for either of them (you cannot initialise objects of
class |Device| directly).  On the other hand, "nodes", for example, does not
necessarily mean an object of class |Nodes|, but any other group of |Node| objects as
well.

Each element handles a single |Model| object and represents, for example, a subbasin or
a channel segment.  The purpose of a node is to connect different elements and, for
example, to pass the discharge calculated for a subbasin outlet (from a first element)
to the top of a channel segment (to second element).  Class |Node| and |Element| come
with specialised container classes (|Nodes| and |Elements|).  The names of individual
nodes and elements serve as identity values, so duplicate names are not permitted.

Note that module |devicetools| implements a registry mechanism both for nodes and
elements, preventing instantiating an object with an already assigned name.  This
mechanism allows to address the same node or element in different network files (see
module |selectiontools|).

Let us take class |Node| as an example.  One can call its constructor with the same
name multiple times, but it returns already existing nodes when available:

>>> from hydpy import Node
>>> node1 = Node("test1")
>>> node2a = Node("test2")
>>> node2b = Node("test2")
>>> node1 is node2a
False
>>> node2a is node2b
True

To get information on all currently registered nodes, call method
|Device.extract_new|:

>>> Node.extract_new()
Nodes("test1", "test2")

Method |Device.extract_new| returns only those nodes prepared or
recovered after its last invocation:

>>> node1 = Node("test1")
>>> node3a = Node("test3")

>>> Node.extract_new()
Nodes("test1", "test3")

For a complete list of all available nodes, use the method |Device.query_all|:

>>> Node.query_all()
Nodes("test1", "test2", "test3")

When working interactively in the Python interpreter, it might be useful to clear the
registry completely, sometimes.  Do this with care because defining nodes with already
assigned names might result in surprises due to using their names for identification:

>>> nodes = Node.query_all()
>>> Node.clear_all()
>>> Node.query_all()
Nodes()
>>> node3b = Node("test3")
>>> node3b in nodes
True
>>> nodes.test3.name == node3b.name
True
>>> nodes.test3 is node3b
False
"""
# import...
# ...from standard library
from __future__ import annotations
import abc
import contextlib
import copy
import itertools
import operator
import warnings
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import masktools
from hydpy.core import objecttools
from hydpy.core import printtools
from hydpy.core import sequencetools
from hydpy.core import seriestools
from hydpy.core import timetools
from hydpy.core.typingtools import *
from hydpy.cythons.autogen import pointerutils

if TYPE_CHECKING:
    from matplotlib import pyplot
    import pandas
    from hydpy.core import auxfiletools
    from hydpy.core import hydpytools
    from hydpy.core import modeltools
else:
    pandas = exceptiontools.OptionalImport("pandas", ["pandas"], locals())
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())

_default_variable = "Q"

DeviceType = TypeVar("DeviceType", "Node", "Element")
DevicesTypeBound = TypeVar("DevicesTypeBound", bound="Devices")
DevicesTypeUnbound = TypeVar("DevicesTypeUnbound", "Nodes", "Elements")

NodesConstrArg = MayNonerable2["Node", str]
ElementsConstrArg = MayNonerable2["Element", str]
NodeConstrArg = Union["Node", str]
ElementConstrArg = Union["Element", str]

NodeVariableType = Union[
    str,
    sequencetools.TypesInOutSequence,
    "FusedVariable",
]

LineStyle = Literal["-", "--", "-.", ":", "solid", "dashed", "dashdot", "dotted"]
StepSize = Literal["daily", "d", "monthly", "m"]


class Keywords(Set[str]):
    """Set of keyword arguments used to describe and search for |Element| and
    |Node| objects."""

    device: Union[Node, Element, None]

    def __init__(self, *names: str):
        self.device = None
        self._check_keywords(names)
        super().__init__(names)

    def startswith(self, name: str) -> List[str]:
        """Return a list of all keywords, starting with the given string.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.startswith("keyword")
        ['keyword_3', 'keyword_4']
        """
        return sorted(keyword for keyword in self if keyword.startswith(name))

    def endswith(self, name: str) -> List[str]:
        """Return a list of all keywords ending with the given string.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.endswith("keyword")
        ['first_keyword', 'second_keyword']
        """
        return sorted(keyword for keyword in self if keyword.endswith(name))

    def contains(self, name: str) -> List[str]:
        """Return a list of all keywords containing the given string.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.contains("keyword")
        ['first_keyword', 'keyword_3', 'keyword_4', 'second_keyword']
        """
        return sorted(keyword for keyword in self if name in keyword)

    def _check_keywords(self, names: Iterable[str]) -> None:
        for name in names:
            try:
                objecttools.valid_variable_identifier(name)
            except ValueError:
                objecttools.augment_excmessage(
                    f"While trying to add the keyword `{name}` "
                    f"to device {objecttools.devicename(self.device)}"
                )

    def update(self, *names: Any) -> None:
        """Before updating, the given names are checked to be valid
        variable identifiers.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.update("test_1", "test 2")   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to add the keyword `test 2` to device ?, \
the following error occurred: The given name string `test 2` does not \
define a valid variable identifier.  ...

        Note that even the first string (`test1`) is not added due to the
        second one (`test 2`) being invalid.

        >>> keywords
        Keywords("first_keyword", "keyboard", "keyword_3", "keyword_4",
                 "second_keyword")

        After correcting the second string, everything works fine:

        >>> keywords.update("test_1", "test_2")
        >>> keywords
        Keywords("first_keyword", "keyboard", "keyword_3", "keyword_4",
                 "second_keyword", "test_1", "test_2")
        """
        _names = [str(name) for name in names]
        self._check_keywords(_names)
        super().update(_names)

    def add(self, name: Any) -> None:
        """Before adding a new name, it is checked to be valid variable
        identifiers.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.add("1_test")   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to add the keyword `1_test` to device ?, \
the following error occurred: The given name string `1_test` does not \
define a valid variable identifier.  ...

        >>> keywords
        Keywords("first_keyword", "keyboard", "keyword_3", "keyword_4",
                 "second_keyword")

        After correcting the string, everything works fine:

        >>> keywords.add("one_test")
        >>> keywords
        Keywords("first_keyword", "keyboard", "keyword_3", "keyword_4",
                 "one_test", "second_keyword")
        """
        self._check_keywords([str(name)])
        super().add(str(name))

    def __repr__(self) -> str:
        with objecttools.repr_.preserve_strings(True):
            return (
                objecttools.assignrepr_values(sorted(self), "Keywords(", width=70) + ")"
            )


_registry_fusedvariable: Dict[str, "FusedVariable"] = {}


class FusedVariable:
    """Combines |InputSequence| and |OutputSequence| subclasses of different models
    dealing with the same property into a single variable.

    Class |FusedVariable| is one possible type of the property |Node.variable|
    of class |Node|.  We need it in some *HydPy* projects where the involved
    models do not only pass runoff to each other but share other types of
    data as well.  Each project-specific |FusedVariable| object serves as a
    "meta-type", indicating which input and output sequences of the different
    models correlate and are thus connectable with each other.

    Using class |FusedVariable| is easiest to explain by a concrete example.
    Assume we use |conv_v001| to interpolate the air temperature for a
    specific location.  We use this temperature as input to the |evap_v001|
    model, which requires this and other meteorological data to calculate
    potential evapotranspiration.  Further, we pass the calculated potential
    evapotranspiration as input to |lland_v2| for calculating the actual
    evapotranspiration.  Hence, we need to connect the output sequence
    |evap_fluxes.ReferenceEvapotranspiration| of |evap_v001| with the input
    sequence |lland_inputs.PET| of |lland_v2|.

    Additionally, |lland_v2| requires temperature data itself for modelling
    snow processes, introducing the problem that we need to use the same data
    (the output of |conv_v001|) as the input of two differently named input
    sequences (|evap_inputs.AirTemperature| and |lland_inputs.TemL| for
    |evap_v001| and |lland_v2|, respectively).

    For our concrete example, we need to create two |FusedVariable| objects.
    `E` combines |evap_fluxes.ReferenceEvapotranspiration| and
    |lland_inputs.PET| and `T` combines |evap_inputs.AirTemperature| and
    |lland_inputs.TemL| (for convenience, we import their globally
    available aliases):

    >>> from hydpy import FusedVariable
    >>> from hydpy.inputs import lland_PET, evap_AirTemperature, lland_TemL
    >>> from hydpy.outputs import evap_ReferenceEvapotranspiration
    >>> E = FusedVariable("E", evap_ReferenceEvapotranspiration, lland_PET)
    >>> T = FusedVariable("T", evap_AirTemperature, lland_TemL)

    Now we can construct the network:

     * Node `t1` handles the original temperature and serves as the input
       node to element `conv`. We define the (arbitrarily selected) string
       `Temp` to be its variable.
     * Node `e` receives the potential evapotranspiration calculated by
       element `evap` and passes it to element `lland`.  Node `e` thus
       receives the fused variable `E`.
     * Node `t2` handles the interpolated temperature and serves as the
       outlet node of element `conv` and the input node to elements
       `evap` and `lland`.  Node `t2` thus receives the fused variable `T`.

    >>> from hydpy import Node, Element
    >>> t1 = Node("t1", variable="Temp")
    >>> t2 = Node("t2", variable=T)
    >>> e = Node("e", variable=E)
    >>> conv = Element("element_conv",
    ...                inlets=t1,
    ...                outlets=t2)
    >>> evap = Element("element_evap",
    ...                inputs=t2,
    ...                outputs=e)
    >>> lland = Element("element_lland",
    ...                 inputs=(t2, e),
    ...                 outlets="node_q")

    Now we can prepare the different model objects and assign them to their
    corresponding elements (note that parameters |conv_control.InputCoordinates|
    and |conv_control.OutputCoordinates| of |conv_v001| first require
    information on the location of the relevant nodes):

    >>> from hydpy import prepare_model
    >>> model_conv = prepare_model("conv_v001")
    >>> model_conv.parameters.control.inputcoordinates(t1=(0, 0))
    >>> model_conv.parameters.control.outputcoordinates(t2=(1, 1))
    >>> model_conv.parameters.control.maxnmbinputs(1)
    >>> model_conv.parameters.update()
    >>> conv.model = model_conv
    >>> evap.model = prepare_model("evap_v001")
    >>> lland.model = prepare_model("lland_v2")

    We assign a temperature value to node `t1`:

    >>> t1.sequences.sim = -273.15

    Model |conv_v001| now can perform a simulation step and pass its
    output to node `t2`:

    >>> conv.model.simulate(0)
    >>> t2.sequences.sim
    sim(-273.15)

    Without further configuration, |evap_v001| cannot perform any simulation
    steps.  Hence, we just call its |Model.load_data| method to show that
    its input sequence |evap_inputs.AirTemperature| is well connected to the
    |Sim| sequence of node `t2` and receives the correct data:

    >>> evap.model.load_data()
    >>> evap.model.sequences.inputs.airtemperature
    airtemperature(-273.15)

    The output sequence |evap_fluxes.ReferenceEvapotranspiration| is also well
    connected.  A call to method |Model.update_outputs| passes its (manually set) value
    to node `e`, respectively:

    >>> evap.model.sequences.fluxes.referenceevapotranspiration = 999.9
    >>> evap.model.update_outputs()
    >>> e.sequences.sim
    sim(999.9)

    Finally, both input sequences |lland_inputs.TemL| and |lland_inputs.PET|
    receive the current values of nodes `t2` and `e`:

    >>> lland.model.load_data()
    >>> lland.model.sequences.inputs.teml
    teml(-273.15)
    >>> lland.model.sequences.inputs.pet
    pet(999.9)

    When defining fused variables, class |FusedVariable| performs some registration
    behind the scenes, similar to classes |Node| and |Element| do.  Again, the name
    works as the identifier, and we force the same fused variable to exist only once,
    even when defined in different selection files repeatedly.  Hence, when we repeat
    the definition from above, we get the same object:

    >>> Test = FusedVariable("T", evap_AirTemperature, lland_TemL)
    >>> T is Test
    True

    Changing the member sequences of an existing fused variable is not allowed:

    >>> from hydpy.inputs import hland_T
    >>> FusedVariable("T", hland_T, lland_TemL)
    Traceback (most recent call last):
    ...
    ValueError: The sequences combined by a FusedVariable object cannot be \
changed.  The already defined sequences of the fused variable `T` are \
`evap_AirTemperature and lland_TemL` instead of `hland_T and lland_TemL`.  \
Keep in mind, that `name` is the unique identifier for fused variable instances.


    Defining additional fused variables with the same member sequences does
    not seem advisable but is allowed:

    >>> Temp = FusedVariable("Temp", evap_AirTemperature, lland_TemL)
    >>> T is Temp
    False

    To get an overview of the already existing fused variables, call
    method |FusedVariable.get_registry|:

    >>> len(FusedVariable.get_registry())
    3

    Principally, you can clear the registry via method
    |FusedVariable.clear_registry|, but remember it does not remove
    |FusedVariable| objects from the running process being otherwise
    referenced:

    >>> FusedVariable.clear_registry()
    >>> FusedVariable.get_registry()
    ()
    >>> t2.variable
    FusedVariable("T", evap_AirTemperature, lland_TemL)

    .. testsetup::

        >>> Node.clear_all()
        >>> Element.clear_all()
    """

    _name: str
    _aliases: Tuple[str]
    _variables: Tuple[sequencetools.TypesInOutSequence, ...]
    _alias2variable: Dict[str, sequencetools.TypesInOutSequence]

    def __new__(
        cls,
        name: str,
        *sequences: sequencetools.TypesInOutSequence,
    ) -> FusedVariable:
        self = super().__new__(cls)
        aliases = tuple(hydpy.sequence2alias[seq] for seq in sequences)
        idxs = numpy.argsort(aliases)
        aliases = tuple(aliases[idx] for idx in idxs)
        variables = tuple(sequences[idx] for idx in idxs)
        fusedvariable = _registry_fusedvariable.get(name)
        if fusedvariable:
            if variables == fusedvariable._variables:
                return fusedvariable
            raise ValueError(
                f"The sequences combined by a {type(self).__name__} "
                f"object cannot be changed.  The already defined sequences "
                f"of the fused variable `{name}` are "
                f"`{objecttools.enumeration(fusedvariable._aliases)}` "
                f"instead of `{objecttools.enumeration(aliases)}`.  Keep in "
                f"mind, that `name` is the unique identifier for fused "
                f"variable instances."
            )
        self._name = name
        self._aliases = aliases
        self._variables = variables
        _registry_fusedvariable[name] = self
        self._alias2variable = dict(zip(self._aliases, self._variables))
        return self

    @classmethod
    def get_registry(cls) -> Tuple["FusedVariable", ...]:
        """Get all |FusedVariable| objects initialised so far."""
        return tuple(_registry_fusedvariable.values())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the registry from all |FusedVariable| objects initialised
        so far.

        Use this method only for good reasons!
        """
        return _registry_fusedvariable.clear()

    def __iter__(self) -> Iterator[sequencetools.TypesInOutSequence]:
        for variable in self._variables:
            yield variable

    def __contains__(self, item: object) -> bool:
        if isinstance(
            item,
            (sequencetools.InputSequence, sequencetools.OutputSequence),
        ):
            item = type(item)
        return item in self._variables

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f'FusedVariable("{self._name}", {", ".join(self._aliases)})'


class Devices(Generic[DeviceType]):
    """Base class for class |Elements| and class |Nodes|.

    The following features are common to class |Nodes| and class |Elements|.
    We arbitrarily select class |Nodes| for all examples.

    To initialise a |Nodes| collection class, pass a variable number of |str| or |Node|
    objects.  Strings are used to create new or query already existing nodes
    automatically:

    >>> from hydpy import Node, Nodes
    >>> nodes = Nodes("na",
    ...               Node("nb", variable="W"),
    ...               Node("nc", keywords=("group_a", "group_1")),
    ...               Node("nd", keywords=("group_a", "group_2")),
    ...               Node("ne", keywords=("group_b", "group_1")))

    |Nodes| and |Elements| objects are containers supporting attribute access. You can
    access each node or element directly by its name:

    >>> nodes.na
    Node("na", variable="Q")

    Wrong node names result in the following error message:

    >>> nodes.wrong
    Traceback (most recent call last):
    ...
    AttributeError: The selected Nodes object has neither a `wrong` attribute nor \
does it handle a Node object with name or keyword `wrong`, which could be returned.

    As explained in more detail in the documentation on property |Device.keywords|, you
    can also use the keywords of the individual nodes to query the relevant ones:

    >>> nodes.group_a
    Nodes("nc", "nd")

    Especially in this context, you might find it useful to also get an iterable object
    in case no node or only a single node is available:

    >>> Nodes.forceiterable = True
    >>> nodes.wrong
    Nodes()
    >>> nodes.na
    Nodes("na")
    >>> Nodes.forceiterable = False

    Attribute deleting is supported:

    >>> "na" in nodes
    True
    >>> del nodes.na
    >>> "na" in nodes
    False
    >>> del nodes.na
    Traceback (most recent call last):
    ...
    AttributeError: The actual Nodes object does not handle a Node object named `na` \
which could be removed, and deleting other attributes is not supported.

    However, shown  by the next example, setting devices via attribute access could
    result in inconsistencies and is not allowed (see method |Devices.add_device|
    instead):

    >>> nodes.NF = Node("nf")
    Traceback (most recent call last):
    ...
    AttributeError: Setting attributes of Nodes objects could result in confusion \
whether a new attribute should be handled as a Node object or as a "normal" attribute \
and is thus not support, hence `NF` is rejected.

    |Nodes| and |Elements| instances support iteration:

    >>> len(nodes)
    4
    >>> for node in nodes:
    ...     print(node.name, end=",")
    nb,nc,nd,ne,

    The binary operators `+`, `+=`, `-` and `-=` support adding and removing single
    devices or groups of devices:

    >>> nodes
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes - Node("nc")
    Nodes("nb", "nd", "ne")

    Nodes("nb", "nc", "nd", "ne")
    >>> nodes -= Nodes("nc", "ne")
    >>> nodes
    Nodes("nb", "nd")

    >>> nodes + "nc"
    Nodes("nb", "nc", "nd")
    >>> nodes
    Nodes("nb", "nd")
    >>> nodes += ("nc", Node("ne"))
    >>> nodes
    Nodes("nb", "nc", "nd", "ne")

    Attempts to add already existing or to remove non-existing devices do no harm:

    >>> nodes
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes + ("nc", "ne")
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes - Node("na")
    Nodes("nb", "nc", "nd", "ne")

    Comparisons are supported, with "x < y" being |True| if "x" is a subset of "y":

    >>> subgroup = Nodes("nc", "ne")
    >>> subgroup < nodes, nodes < subgroup, nodes < nodes
    (True, False, False)
    >>> subgroup <= nodes, nodes <= subgroup, nodes <= nodes
    (True, False, True)
    >>> subgroup == nodes, nodes == subgroup, nodes == nodes, nodes == "nodes"
    (False, False, True, False)
    >>> subgroup != nodes, nodes != subgroup, nodes != nodes, nodes != "nodes"
    (True, True, False, True)
    >>> subgroup >= nodes, nodes >= subgroup, nodes >= nodes
    (False, True, True)
    >>> subgroup > nodes, nodes > subgroup, nodes > nodes
    (False, True, False)

    Class |Nodes| supports the `in` operator both for |str| and |Node| objects and
    generally returns |False| for other types:

    >>> "na" in nodes
    False
    >>> "nb" in nodes
    True
    >>> Node("na") in nodes
    False
    >>> Node("nb") in nodes
    True
    >>> 1 in nodes
    False

    Passing wrong arguments to the constructor of class |Node| results in errors like
    the following:

    >>> from hydpy import Element
    >>> Nodes("na", Element("ea"))
    Traceback (most recent call last):
    ...
    TypeError: While trying to initialise a `Nodes` object, the following error \
occurred: The given (sub)value `Element("ea")` is not an instance of the following \
classes: Node and str.
    """

    _name2device: Dict[str, DeviceType]
    mutable: bool
    _shadowed_keywords: Set[str]
    forceiterable: bool = False

    # We do not want to implement the signature of Generic.__new__ here:
    def __new__(  # pylint: disable=arguments-differ
        cls,
        *values: MayNonerable2[DeviceType, str],
        mutable: bool = True,
    ):
        if len(values) == 1 and isinstance(values[0], Devices):
            return values[0]
        self = super().__new__(cls)
        dict_ = vars(self)
        dict_["mutable"] = mutable
        dict_["_name2device"] = {}
        dict_["_shadowed_keywords"] = set()
        contentclass = self.get_contentclass()
        try:
            for value in objecttools.extract(
                values, types_=(contentclass, str), skip=True
            ):
                self.add_device(value)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise a `{type(self).__name__}` object"
            )
        return self

    @staticmethod
    @abc.abstractmethod
    def get_contentclass() -> Type[DeviceType]:
        """To be overridden."""

    def add_device(self, device: Union[DeviceType, str]) -> None:
        """Add the given |Node| or |Element| object to the actual
        |Nodes| or |Elements| object.

        You can pass either a string or a device:

        >>> from hydpy import Nodes
        >>> nodes = Nodes()
        >>> nodes.add_device("old_node")
        >>> nodes
        Nodes("old_node")
        >>> nodes.add_device("new_node")
        >>> nodes
        Nodes("new_node", "old_node")

        Method |Devices.add_device| is disabled for immutable |Nodes|
        and |Elements| objects:

        >>> nodes.mutable = False
        >>> nodes.add_device("newest_node")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to add the device `newest_node` to a \
Nodes object, the following error occurred: Adding devices to immutable \
Nodes objects is not allowed.
        """
        try:
            if self.mutable:
                _device = self.get_contentclass()(device)
                self._name2device[_device.name] = _device
                _id2devices[_device][id(self)] = self
            else:
                raise RuntimeError(
                    f"Adding devices to immutable "
                    f"{type(self).__name__} objects is not allowed."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to add the device `{device}` to a "
                f"{type(self).__name__} object"
            )

    def remove_device(self, device: Union[DeviceType, str]) -> None:
        """Remove the given |Node| or |Element| object from the actual
        |Nodes| or |Elements| object.

        You can pass either a string or a device:

        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes("node_x", "node_y")
        >>> node_x, node_y = nodes
        >>> nodes.remove_device(Node("node_y"))
        >>> nodes
        Nodes("node_x")
        >>> nodes.remove_device(Node("node_x"))
        >>> nodes
        Nodes()
        >>> nodes.remove_device(Node("node_z"))
        Traceback (most recent call last):
        ...
        ValueError: While trying to remove the device `node_z` from a \
Nodes object, the following error occurred: The actual Nodes object does \
not handle such a device.

        Method |Devices.remove_device| is disabled for immutable |Nodes|
        and |Elements| objects:

        >>> nodes.mutable = False
        >>> nodes.remove_device("node_z")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to remove the device `node_z` from a \
Nodes object, the following error occurred: Removing devices from \
immutable Nodes objects is not allowed.
        """
        try:
            if self.mutable:
                _device = self.get_contentclass()(device)
                try:
                    del self._name2device[_device.name]
                except KeyError:
                    raise ValueError(
                        f"The actual {type(self).__name__} "
                        f"object does not handle such a device."
                    ) from None
                del _id2devices[_device][id(self)]
            else:
                raise RuntimeError(
                    f"Removing devices from immutable "
                    f"{type(self).__name__} objects is not allowed."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to remove the device `{device}` from a "
                f"{type(self).__name__} object"
            )

    @property
    def names(self) -> Tuple[str, ...]:
        """A sorted tuple of the names of the handled devices.

        >>> from hydpy import Nodes
        >>> Nodes("a", "c", "b").names
        ('a', 'b', 'c')
        """
        return tuple(device.name for device in self)

    @property
    def devices(self) -> Tuple[DeviceType, ...]:
        """A tuple of the handled devices sorted by the device names.

        >>> from hydpy import Nodes
        >>> for node in Nodes("a", "c", "b").devices:
        ...     print(repr(node))
        Node("a", variable="Q")
        Node("b", variable="Q")
        Node("c", variable="Q")
        """
        return tuple(device for device in self)

    @property
    def keywords(self) -> Set[str]:
        """A set of all keywords of all handled devices.

        In addition to attribute access via device names, |Nodes| and
        |Elements| objects allow for attribute access via keywords,
        allowing for an efficient search of certain groups of devices.
        Let us use the example from above, where the nodes `na` and `nb`
        have no keywords, but each of the other three nodes both belongs
        to either `group_a` or `group_b` and `group_1` or `group_2`:

        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes("na",
        ...               Node("nb", variable="W"),
        ...               Node("nc", keywords=("group_a", "group_1")),
        ...               Node("nd", keywords=("group_a", "group_2")),
        ...               Node("ne", keywords=("group_b", "group_1")))
        >>> nodes
        Nodes("na", "nb", "nc", "nd", "ne")
        >>> sorted(nodes.keywords)
        ['group_1', 'group_2', 'group_a', 'group_b']

        If you are interested in inspecting all devices belonging to
        `group_a`, select them via this keyword:

        >>> subgroup = nodes.group_1
        >>> subgroup
        Nodes("nc", "ne")

        You can further restrict the search by also selecting the devices belonging to
        `group_b`, which holds only for node "e", in the discussed example:

        >>> subsubgroup = subgroup.group_b
        >>> subsubgroup
        Node("ne", variable="Q",
             keywords=["group_1", "group_b"])

        Note that the keywords already used for building a device subgroup
        are not informative anymore (as they hold for each device) and are
        thus not shown anymore:

        >>> sorted(subgroup.keywords)
        ['group_a', 'group_b']

        The latter might be confusing if you intend to work with a device
        subgroup for a longer time.  After copying the subgroup, all
        keywords of the contained devices are available again:

        >>> from copy import copy
        >>> newgroup = copy(subgroup)
        >>> sorted(newgroup.keywords)
        ['group_1', 'group_a', 'group_b']
        """
        return set(
            keyword
            for device in self
            for keyword in device.keywords
            if keyword not in self._shadowed_keywords
        )

    def search_keywords(
        self: DevicesTypeBound,
        *keywords: str,
    ) -> DevicesTypeBound:
        """Search for all devices handling at least one of the given
        keywords and return them.

        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes("na",
        ...               Node("nb", variable="W"),
        ...               Node("nc", keywords=("group_a", "group_1")),
        ...               Node("nd", keywords=("group_a", "group_2")),
        ...               Node("ne", keywords=("group_b", "group_1")))
        >>> nodes.search_keywords("group_c")
        Nodes()
        >>> nodes.search_keywords("group_a")
        Nodes("nc", "nd")
        >>> nodes.search_keywords("group_a", "group_1")
        Nodes("nc", "nd", "ne")

        .. testsetup::

            >>> Node.clear_all()
        """
        keywords_ = set(keywords)
        return type(self)(
            *(device for device in self if keywords_.intersection(device.keywords))
        )

    def open_files(self, idx: int = 0) -> None:
        """Call method |Node.open_files| or |Element.open_files| of all
        contained |Node| or |Element| objects."""
        for device in self:
            device.open_files(idx)

    def close_files(self) -> None:
        """Call method |Node.close_files| or |Element.close_files| of
        all contained |Node| or |Element| objects."""
        for device in self:
            device.close_files()

    def copy(self: DevicesTypeBound) -> DevicesTypeBound:
        """Return a shallow copy of the actual |Nodes| or |Elements| object.

        Method |Devices.copy| returns a semi-flat copy of |Nodes| or |Elements| objects
        due to their devices being not copyable:

        >>> from hydpy import Nodes
        >>> old = Nodes("x", "y")
        >>> import copy
        >>> new = copy.copy(old)
        >>> new == old
        True
        >>> new is old
        False
        >>> new.devices is old.devices
        False
        >>> new.x is new.x
        True

        Changing the |Device.name| of a device is recognised both by the
        original and the copied collection objects:

        >>> new.x.name = "z"
        >>> old.z
        Node("z", variable="Q")
        >>> new.z
        Node("z", variable="Q")

        Deep copying is permitted due to the above reason:

        >>> copy.deepcopy(old)
        Traceback (most recent call last):
        ...
        NotImplementedError: Deep copying of Nodes objects is not supported, \
as it would require to make deep copies of the Node objects themselves, \
which is in conflict with using their names as identifiers.
        """
        new = type(self)()
        vars(new).update(vars(self))
        vars(new)["_name2device"] = copy.copy(self._name2device)
        vars(new)["_shadowed_keywords"].clear()
        for device in self:
            _id2devices[device][id(new)] = new
        return new

    def intersection(
        self: DevicesTypeBound,
        *other: DeviceType,
    ) -> DevicesTypeBound:
        """Return the intersection with the given |Devices| object.

        >>> from hydpy import Node, Nodes
        >>> nodes1 = Nodes("na", "nb", "nc")
        >>> nodes2 = Nodes("na", "nc", "nd")
        >>> nodes1.intersection(*nodes2)
        Nodes("na", "nc")

        .. testsetup::

            >>> Node.clear_all()
        """
        return type(self)(*set(self).intersection(set(other)))

    __copy__ = copy

    def __deepcopy__(self, dict_):
        classname = type(self).__name__
        raise NotImplementedError(
            f"Deep copying of {classname} objects is not supported, as it "
            f"would require to make deep copies of the {classname[:-1]} "
            f"objects themselves, which is in conflict with using their "
            f"names as identifiers."
        )

    def __select_devices_by_keyword(self, name: str) -> DevicesTypeBound:
        devices = type(self)(*(device for device in self if name in device.keywords))
        vars(devices)["_shadowed_keywords"] = self._shadowed_keywords.copy()
        vars(devices)["_shadowed_keywords"].add(name)
        return devices

    def __getattr__(
        self: DevicesTypeBound,
        name: str,
    ) -> Union[DeviceType, DevicesTypeBound]:
        try:
            name2device = self._name2device
            device = name2device[name]
            if self.forceiterable:
                return type(self)(device)
            return device
        except KeyError:
            pass
        _devices = self.__select_devices_by_keyword(name)
        if self.forceiterable or len(_devices) > 1:
            return _devices
        if len(_devices) == 1:
            return _devices.devices[0]
        raise AttributeError(
            f"The selected {type(self).__name__} object has neither a `{name}` "
            f"attribute nor does it handle a {self.get_contentclass().__name__} "
            f"object with name or keyword `{name}`, which could be returned."
        )

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, name):
            super().__setattr__(name, value)
        else:
            classname = type(self).__name__
            raise AttributeError(
                f"Setting attributes of {classname} objects could result in confusion "
                f"whether a new attribute should be handled as a {classname[:-1]} "
                f'object or as a "normal" attribute and is thus not support, hence '
                f"`{name}` is rejected."
            )

    def __delattr__(self, name: str) -> None:
        try:
            self.remove_device(name)
        except ValueError:
            raise AttributeError(
                f"The actual {type(self).__name__} object does not handle a "
                f"{self.get_contentclass().__name__} object named `{name}` which "
                f"could be removed, and deleting other attributes is not supported."
            ) from None

    def __getitem__(self, name: str) -> DeviceType:
        try:
            return self._name2device[name]
        except KeyError:
            raise KeyError(f"No device named `{name}` available.") from None

    def __setitem__(self, name: str, value: DeviceType) -> None:
        self._name2device[name] = value

    def __delitem__(self, name: str) -> None:
        del self._name2device[name]

    def __iter__(self) -> Iterator[DeviceType]:
        for (_, device) in sorted(self._name2device.items()):
            yield device

    def __contains__(self, value: object) -> bool:
        cls = self.get_contentclass()
        if isinstance(value, cls):
            return value.name in self._name2device
        if isinstance(value, str):
            return value in self._name2device
        return False

    def __len__(self) -> int:
        return len(self._name2device)

    def __add__(
        self: DevicesTypeBound,
        other: Mayberable2[DeviceType, str],
    ) -> DevicesTypeBound:
        new = copy.copy(self)
        new.mutable = True
        for device in type(self)(other):
            new.add_device(device)
        return new

    def __iadd__(
        self: DevicesTypeBound,
        other: Mayberable2[DeviceType, str],
    ) -> DevicesTypeBound:
        for device in type(self)(other):
            self.add_device(device)
        return self

    def __sub__(
        self: DevicesTypeBound,
        other: Mayberable2[DeviceType, str],
    ) -> DevicesTypeBound:
        new = copy.copy(self)
        new.mutable = True
        for device in type(self)(other):
            try:
                new.remove_device(device)
            except ValueError:
                pass
        return new

    def __isub__(
        self: DevicesTypeBound,
        other: Mayberable2[DeviceType, str],
    ) -> DevicesTypeBound:
        for device in type(self)(other):
            try:
                self.remove_device(device)
            except ValueError:
                pass
        return self

    def __compare(self, other: object, func: Callable[[object, object], bool]) -> bool:
        if isinstance(other, type(self)):
            return func(set(self), set(other))
        return NotImplemented

    def __lt__(self, other: DevicesTypeBound) -> bool:
        return self.__compare(other, operator.lt)

    def __le__(self, other: DevicesTypeBound) -> bool:
        return self.__compare(other, operator.le)

    def __eq__(self, other: Any) -> bool:
        return self.__compare(other, operator.eq)

    def __ne__(self, other: Any) -> bool:
        return self.__compare(other, operator.ne)

    def __ge__(self, other: DevicesTypeBound) -> bool:
        return self.__compare(other, operator.ge)

    def __gt__(self, other: DevicesTypeBound) -> bool:
        return self.__compare(other, operator.gt)

    def __repr__(self) -> str:
        return self.assignrepr("")

    def assignrepr(self, prefix: str = "") -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            with hydpy.pub.options.ellipsis(2, optional=True):
                prefix += f"{type(self).__name__}("
                repr_ = objecttools.assignrepr_values(self.names, prefix, width=70)
                return repr_ + ")"

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes(Node("name1", keywords="keyword1"),
        ...               Node("name2", keywords=("keyword2a", "keyword2a")))
        >>> sorted(set(dir(nodes)) - set(object.__dir__(nodes)))
        ['keyword1', 'keyword2a', 'name1', 'name2']
        """
        return (
            cast(List[str], super().__dir__()) + list(self.names) + list(self.keywords)
        )


class Nodes(Devices["Node"]):
    """A container class for handling |Node| objects.

    For the general usage of |Nodes| objects, please see the documentation on its base
    class |Devices|.

    Class |Nodes| provides the additional keyword argument `defaultvariable`.  Use it
    to temporarily change the default variable "Q" to another value during the
    initialisation of new |Node| objects:

    >>> from hydpy import Nodes
    >>> a1, t2 = Nodes("a1", "a2", defaultvariable="A")
    >>> a1
    Node("a1", variable="A")

    Be aware that changing the default variable does not affect already existing nodes:

    >>> a1, b1 = Nodes("a1", "b1", defaultvariable="B")
    >>> a1
    Node("a1", variable="A")
    >>> b1
    Node("b1", variable="B")
    """

    def __new__(
        cls,
        *values: MayNonerable2[DeviceType, str],
        mutable: bool = True,
        defaultvariable: NodeVariableType = "Q",
    ):
        global _default_variable
        _default_variable_copy = _default_variable
        try:
            _default_variable = defaultvariable
            return super().__new__(cls, *values, mutable=mutable)
        finally:
            _default_variable = _default_variable_copy

    @staticmethod
    def get_contentclass() -> Type[Node]:
        """Return class |Node|."""
        return Node

    @printtools.print_progress
    def prepare_allseries(self, ramflag: bool = True) -> None:
        """Call methods |Node.prepare_simseries| and
        |Node.prepare_obsseries|."""
        for node in printtools.progressbar(self):
            node.prepare_allseries(ramflag)

    @printtools.print_progress
    def prepare_simseries(self, ramflag: bool = True) -> None:
        """Call method |Node.prepare_simseries| of all handled
        |Node| objects."""
        for node in printtools.progressbar(self):
            node.prepare_simseries(ramflag)

    @printtools.print_progress
    def prepare_obsseries(self, ramflag: bool = True) -> None:
        """Call method |Node.prepare_obsseries| of all handled
        |Node| objects."""
        for node in printtools.progressbar(self):
            node.prepare_obsseries(ramflag)

    @printtools.print_progress
    def load_allseries(self) -> None:
        """Call methods |Nodes.load_simseries| and |Nodes.load_obsseries|."""
        self.load_simseries()
        self.load_obsseries()

    @printtools.print_progress
    def load_simseries(self) -> None:
        """Call method |IOSequence.load_ext| of all |Sim| objects
        with an activated |IOSequence.memoryflag|."""
        self.__load_nodeseries("sim")

    @printtools.print_progress
    def load_obsseries(self) -> None:
        """Call method |IOSequence.load_ext| of all |Obs| objects
        with an activated |IOSequence.memoryflag|."""
        self.__load_nodeseries("obs")

    def __load_nodeseries(self, seqname: str) -> None:
        for node in printtools.progressbar(self):
            getattr(node.sequences, seqname).load_ext()

    @printtools.print_progress
    def save_allseries(self) -> None:
        """Call methods |Nodes.save_simseries| and |Nodes.save_obsseries|."""
        self.save_simseries()
        self.save_obsseries()

    @printtools.print_progress
    def save_simseries(self) -> None:
        """Call method |IOSequence.save_ext| of all |Sim| objects
        with an activated |IOSequence.memoryflag|."""
        self.__save_nodeseries("sim")

    @printtools.print_progress
    def save_obsseries(self) -> None:
        """Call method |IOSequence.save_ext| of all |Obs| objects
        with an activated |IOSequence.memoryflag|."""
        self.__save_nodeseries("obs")

    def __save_nodeseries(self, seqname: str) -> None:
        for node in printtools.progressbar(self):
            seq = getattr(node.sequences, seqname)
            if seq.memoryflag:
                seq.save_ext()

    @property
    def variables(self) -> Set[NodeVariableType]:
        """Return a set of the variables of all handled |Node| objects.

        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes(Node("x1"),
        ...               Node("x2", variable="Q"),
        ...               Node("x3", variable="H"))
        >>> sorted(nodes.variables)
        ['H', 'Q']
        """
        return {node.variable for node in self}


class Elements(Devices["Element"]):
    """A container for handling |Element| objects.

    For the general usage of |Elements| objects, please see the documentation
    on its base class |Devices|.
    """

    @staticmethod
    def get_contentclass() -> Type[Element]:
        """Return class |Element|."""
        return Element

    @printtools.print_progress
    def prepare_models(self) -> None:
        """Call method |Element.prepare_model| of all handle |Element| objects.

        We show, based on the `LahnH` example project, that method |Element.init_model|
        prepares the |Model| objects of all elements, including building the required
        connections and updating the derived parameters:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import attrready, HydPy, pub, TestIO
        >>> with TestIO():
        ...     hp = HydPy("LahnH")
        ...     pub.timegrids = "1996-01-01", "1996-02-01", "1d"
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        >>> hp.elements.land_dill.model.parameters.derived.dt
        dt(0.000833)

        Wrong control files result in error messages like the following:

        >>> with TestIO():
        ...     with open("LahnH/control/default/land_dill.py", "a") as file_:
        ...         _ = file_.write("zonetype(-1)")
        ...     hp.prepare_models()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to initialise the model object of element \
`land_dill`, the following error occurred: While trying to load the control \
file `...land_dill.py`, the following error occurred: At least one value of \
parameter `zonetype` of element `?` is not valid.

        By default, missing control files result in exceptions:

        >>> del hp.elements.land_dill.model
        >>> import os
        >>> with TestIO():
        ...     os.remove("LahnH/control/default/land_dill.py")
        ...     hp.prepare_models()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        FileNotFoundError: While trying to initialise the model object of element \
`land_dill`, the following error occurred: While trying to load the control file \
`...land_dill.py`, the following error occurred: ...
        >>> attrready(hp.elements.land_dill, "model")
        False

        When building new, still incomplete *HydPy* projects, this behaviour can be
        annoying.  After setting the option |Options.warnmissingcontrolfile| to |False|,
        missing control files result in a warning only:

        >>> with TestIO():
        ...     with pub.options.warnmissingcontrolfile(True):
        ...         hp.prepare_models()
        Traceback (most recent call last):
        ...
        UserWarning: Due to a missing or no accessible control file, no model could \
be initialised for element `land_dill`
        >>> attrready(hp.elements.land_dill, "model")
        False
        """
        try:
            for element in printtools.progressbar(self):
                element.prepare_model(clear_registry=False)
        finally:
            hydpy.pub.controlmanager.clear_registry()

    def init_models(self) -> None:
        """Deprecated: use method |Elements.prepare_models| instead.

        >>> from hydpy import Elements
        >>> from unittest import mock
        >>> with mock.patch.object(Elements, "prepare_models") as mocked:
        ...     elements = Elements()
        ...     elements.init_models()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.HydPyDeprecationWarning: \
Method `init_models` of class `Elements` is deprecated.  \
Use method `prepare_models` instead.
        >>> mocked.call_args_list
        [call()]
        """
        self.prepare_models()
        warnings.warn(
            "Method `init_models` of class `Elements` is deprecated.  "
            "Use method `prepare_models` instead.",
            exceptiontools.HydPyDeprecationWarning,
        )

    @printtools.print_progress
    def save_controls(
        self,
        parameterstep: Optional["timetools.PeriodConstrArg"] = None,
        simulationstep: Optional["timetools.PeriodConstrArg"] = None,
        auxfiler: "Optional[auxfiletools.Auxfiler]" = None,
    ) -> None:
        """Save the control parameters of the |Model| object handled by
        each |Element| object and eventually the ones handled by the
        given |Auxfiler| object."""
        if auxfiler:
            auxfiler.write(
                parameterstep=parameterstep,
                simulationstep=simulationstep,
            )
        for element in printtools.progressbar(self):
            element.model.parameters.save_controls(
                parameterstep=parameterstep,
                simulationstep=simulationstep,
                auxfiler=auxfiler,
            )

    @printtools.print_progress
    def load_conditions(self) -> None:
        """Save the initial conditions of the |Model| object handled by
        each |Element| object."""
        for element in printtools.progressbar(self):
            element.model.sequences.load_conditions()

    @printtools.print_progress
    def save_conditions(self) -> None:
        """Save the calculated conditions of the |Model| object handled by
        each |Element| object."""
        for element in printtools.progressbar(self):
            element.model.sequences.save_conditions()

    def trim_conditions(self) -> None:
        """Call method |Sequences.trim_conditions| of the |Sequences|
        object handled (indirectly) by each |Element| object."""
        for element in self:
            element.model.sequences.trim_conditions()

    def reset_conditions(self) -> None:
        """Call method |Sequences.reset| of the |Sequences| object
        handled (indirectly) by each |Element| object."""
        for element in self:
            element.model.sequences.reset()

    @property
    def conditions(self) -> hydpytools.ConditionsType:
        """A nested dictionary that contains the values of all |ConditionSequence|
        objects of all currently handled models.

        See the documentation on property |HydPy.conditions| for further information.
        """
        return {element.name: element.model.sequences.conditions for element in self}

    @conditions.setter
    def conditions(self, conditions: hydpytools.ConditionsType) -> None:
        for name, subconditions in conditions.items():
            element = getattr(self, name)
            element.model.sequences.conditions = subconditions

    @printtools.print_progress
    def prepare_allseries(self, ramflag: bool = True) -> None:
        """Call method |Element.prepare_allseries| of all handled
        |Element| objects."""
        for element in printtools.progressbar(self):
            element.prepare_allseries(ramflag)

    @printtools.print_progress
    def prepare_inputseries(self, ramflag: bool = True) -> None:
        """Call method |Element.prepare_inputseries| of all handled
        |Element| objects."""
        for element in printtools.progressbar(self):
            element.prepare_inputseries(ramflag)

    @printtools.print_progress
    def prepare_factorseries(self, ramflag: bool = True) -> None:
        """Call method |Element.prepare_factorseries| of all handled |Element|
        objects."""
        for element in printtools.progressbar(self):
            element.prepare_factorseries(ramflag)

    @printtools.print_progress
    def prepare_fluxseries(self, ramflag: bool = True) -> None:
        """Call method |Element.prepare_fluxseries| of all handled
        |Element| objects."""
        for element in printtools.progressbar(self):
            element.prepare_fluxseries(ramflag)

    @printtools.print_progress
    def prepare_stateseries(self, ramflag: bool = True) -> None:
        """Call method |Element.prepare_stateseries| of all handled
        |Element| objects."""
        for element in printtools.progressbar(self):
            element.prepare_stateseries(ramflag)

    @printtools.print_progress
    def load_allseries(self) -> None:
        """Call methods |Elements.load_inputseries|, |Elements.load_factorseries|,
        |Elements.load_fluxseries|, and |Elements.load_stateseries|."""
        self.load_inputseries()
        self.load_factorseries()
        self.load_fluxseries()
        self.load_stateseries()

    @printtools.print_progress
    def load_inputseries(self) -> None:
        """Call method |IOSequence.load_ext| of all |InputSequence| objects
        with an activated |IOSequence.memoryflag|."""
        self.__load_modelseries("inputs")

    @printtools.print_progress
    def load_factorseries(self) -> None:
        """Call method |IOSequence.load_ext| of all |FactorSequence| objects with an
        activated |IOSequence.memoryflag|."""
        self.__load_modelseries("factors")

    @printtools.print_progress
    def load_fluxseries(self) -> None:
        """Call method |IOSequence.load_ext| of all |FluxSequence| objects
        with an activated |IOSequence.memoryflag|."""
        self.__load_modelseries("fluxes")

    @printtools.print_progress
    def load_stateseries(self) -> None:
        """Call method |IOSequence.load_ext| of all |StateSequence| objects
        with an activated |IOSequence.memoryflag|."""
        self.__load_modelseries("states")

    def __load_modelseries(self, name_subseqs) -> None:
        for element in printtools.progressbar(self):
            sequences = element.model.sequences
            subseqs = getattr(sequences, name_subseqs, ())
            for seq in subseqs:
                seq.load_ext()

    @printtools.print_progress
    def save_allseries(self) -> None:
        """Call methods |Elements.save_inputseries|, |Elements.save_factorseries|,
        |Elements.save_fluxseries|, and |Elements.save_stateseries|."""
        self.save_inputseries()
        self.save_factorseries()
        self.save_fluxseries()
        self.save_stateseries()

    @printtools.print_progress
    def save_inputseries(self) -> None:
        """Call method |IOSequence.save_ext| of all |InputSequence| objects
        with an activated |IOSequence.memoryflag|."""
        self.__save_modelseries("inputs")

    @printtools.print_progress
    def save_factorseries(self) -> None:
        """Call method |IOSequence.save_ext| of all |FactorSequence| objects with an
        activated |IOSequence.memoryflag|."""
        self.__save_modelseries("factors")

    @printtools.print_progress
    def save_fluxseries(self) -> None:
        """Call method |IOSequence.save_ext| of all |FluxSequence| objects
        with an activated |IOSequence.memoryflag|."""
        self.__save_modelseries("fluxes")

    @printtools.print_progress
    def save_stateseries(self) -> None:
        """Call method |IOSequence.save_ext| of all |StateSequence| objects
        with an activated |IOSequence.memoryflag|."""
        self.__save_modelseries("states")

    def __save_modelseries(self, name_subseqs: str) -> None:
        for element in printtools.progressbar(self):
            sequences = element.model.sequences
            subseqs = getattr(sequences, name_subseqs, ())
            for seq in subseqs:
                if seq.memoryflag:
                    seq.save_ext()


class Device(Generic[DevicesTypeUnbound]):
    """Base class for class |Element| and class |Node|."""

    def __new__(cls, value, *args, **kwargs):
        # pylint: disable=unused-argument
        # required for consistincy with __init__
        name = str(value)
        cls.__check_name(name)
        try:
            self = _registry[cls][name]
        except KeyError:
            self = object.__new__(cls)
            vars(self)["name"] = name
            vars(self)["new_instance"] = True
            vars(self)["keywords"] = Keywords()
            vars(self)["keywords"].device = self
            _id2devices[self] = {}
            _registry[cls][name] = self
        _selection[cls][name] = _registry[cls][name]
        return self

    @classmethod
    @abc.abstractmethod
    def get_handlerclass(cls) -> Type:
        """To be overridden."""

    @classmethod
    def query_all(cls) -> DevicesTypeUnbound:
        """Get all |Node| or |Element| objects initialised so far.

        See the main documentation on module |devicetools| for further
        information.
        """
        return cls.get_handlerclass()(*_registry[cls].values())

    @classmethod
    def extract_new(cls) -> DevicesTypeUnbound:
        """Gather all "new" |Node| or |Element| objects.

        See the main documentation on module |devicetools| for further
        information.
        """
        devices = cls.get_handlerclass()(*_selection[cls])
        _selection[cls].clear()
        return devices

    @classmethod
    def clear_all(cls) -> None:
        """Clear the registry from all initialised |Node| or |Element| objects.

        See the main documentation on module |devicetools| for further
        information.
        """
        _selection[cls].clear()
        _registry[cls].clear()

    @property
    def name(self) -> str:
        """Name of the actual |Node| or |Element| object.

        Device names serve as identifiers, as explained in the main documentation on
        module |devicetools|. Hence, define them carefully:

        >>> from hydpy import Node
        >>> Node.clear_all()
        >>> node1, node2 = Node("n1"), Node("n2")
        >>> node1 is Node("n1")
        True
        >>> node1 is Node("n2")
        False

        Each device name must be a valid variable identifier (see function
        |valid_variable_identifier|) to allow for attribute access:

        >>> from hydpy import Nodes
        >>> nodes = Nodes(node1, "n2")
        >>> nodes.n1
        Node("n1", variable="Q")

        Invalid variable identifiers result in errors like the following:

        >>> node3 = Node("n 3")   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to initialize a `Node` object with value \
`n 3` of type `str`, the following error occurred: The given name string \
`n 3` does not define a valid variable identifier.  ...

        When you change the name of a device (only do this for a good reason),
        the corresponding keys of all related |Nodes| and |Elements| objects
        (as well as of the internal registry) change automatically:

        >>> Node.query_all()
        Nodes("n1", "n2")
        >>> node1.name = "n1a"
        >>> nodes
        Nodes("n1a", "n2")
        >>> Node.query_all()
        Nodes("n1a", "n2")
        """
        return vars(self)["name"]

    @name.setter
    def name(self, name: str) -> None:
        self.__check_name(name)
        for devices in _id2devices[self].values():
            if hasattr(devices, self.name):
                del devices[self.name]
        del _registry[type(self)][self.name]
        vars(self)["name"] = name
        _registry[type(self)][self.name] = self
        for devices in _id2devices[self].values():
            devices[self.name] = self

    @classmethod
    def __check_name(cls, name: str) -> None:
        try:
            objecttools.valid_variable_identifier(name)
        except ValueError:
            objecttools.augment_excmessage(
                f"While trying to initialize a `{cls.__name__}` object "
                f"with value `{name}` of type `{type(name).__name__}`"
            )

    @property
    def keywords(self) -> Keywords:
        """Keywords describing the actual |Node| or |Element| object.

        The keywords are contained within a |Keywords| object:

        >>> from hydpy import Node
        >>> node = Node("n", keywords="word0")
        >>> node.keywords
        Keywords("word0")

        Assigning new words does not overwrite already existing ones.
        You are allowed to add them individually or within iterable objects:

        >>> node.keywords = "word1"
        >>> node.keywords = "word2", "word3"
        >>> node.keywords
        Keywords("word0", "word1", "word2", "word3")

        Additionally, passing additional keywords to the constructor
        of class |Node| or |Element| works also fine:

        >>> Node("n", keywords=("word3", "word4", "word5"))
        Node("n", variable="Q",
             keywords=["word0", "word1", "word2", "word3", "word4", "word5"])

        You can delete all keywords at once:

        >>> del node.keywords
        >>> node.keywords
        Keywords()
        """
        return vars(self)["keywords"]

    @keywords.setter
    def keywords(self, keywords: Mayberable1[str]) -> None:
        keywords = tuple(objecttools.extract(keywords, (str,), True))
        vars(self)["keywords"].update(*keywords)

    @keywords.deleter
    def keywords(self) -> None:
        vars(self)["keywords"].clear()

    def __str__(self) -> str:
        return self.name


class Node(Device[Nodes]):
    """Handles the data flow between |Element| objects.

    |Node| objects always handle two sequences, a |Sim| object for
    simulated values and an |Obs| object for measured values:

    >>> from hydpy import Node
    >>> node = Node("test")
    >>> for sequence in node.sequences:
    ...     print(sequence)
    sim(0.0)
    obs(0.0)

    Each node can handle an arbitrary number of "input" and "output"
    elements, available as instance attributes `entries` and `exits`,
    respectively:

    >>> node.entries
    Elements()
    >>> node.exits
    Elements()

    You cannot (or at least should not) add new elements manually:

    >>> node.entries = "element"
    Traceback (most recent call last):
    ...
    AttributeError: can't set attribute
    >>> node.exits.add_device("element")
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add the device `element` to a \
Elements object, the following error occurred: Adding devices to \
immutable Elements objects is not allowed.

    Instead, see the documentation on class |Element| on how to connect
    |Node| and |Element| objects properly.
    """

    masks = masktools.NodeMasks()
    sequences: sequencetools.NodeSequences

    def __init__(
        self,
        value: NodeConstrArg,
        variable: Optional[NodeVariableType] = None,
        keywords: MayNonerable1[str] = None,
    ) -> None:
        # pylint: disable=unused-argument
        # required for consistincy with Device.__new__
        if "new_instance" in vars(self):
            if variable is None:
                vars(self)["variable"] = _default_variable
            else:
                vars(self)["variable"] = variable
            vars(self)["entries"] = Elements(None, mutable=False)
            vars(self)["exits"] = Elements(None, mutable=False)
            self.sequences = sequencetools.NodeSequences(self)
            vars(self)["deploymode"] = "newsim"
            self.__blackhole = pointerutils.Double(0.0)
            del vars(self)["new_instance"]
        if (variable is not None) and (variable != self.variable):
            raise ValueError(
                f"The variable to be represented by a "
                f"{type(self).__name__} instance cannot be changed.  "
                f"The variable of node `{self.name}` is `{self.variable}` "
                f"instead of `{variable}`.  Keep in mind, that `name` is "
                f"the unique identifier of node objects."
            )
        if keywords is not None:
            self.keywords = keywords  # type: ignore
            # due to internal type conversion
            # see issue https://github.com/python/mypy/issues/3004

    @classmethod
    def get_handlerclass(cls) -> Type[Nodes]:
        """Return class |Nodes|."""
        return Nodes

    @property
    def entries(self) -> Elements:
        """Group of |Element| objects which set the the simulated value
        of the |Node| object."""
        return vars(self)["entries"]

    @property
    def exits(self) -> Elements:
        """Group of |Element| objects which query the simulated or
        observed value of the actual |Node| object."""
        return vars(self)["exits"]

    @property
    def variable(self) -> NodeVariableType:
        """The variable handled by the actual |Node| object.

        By default, we suppose that nodes route discharge:

        >>> from hydpy import Node
        >>> node = Node("test1")
        >>> node.variable
        'Q'

        Each other string, as well as each |InputSequence| subclass, is acceptable (for
        further information, see the documentation on method |Model.connect|):

        >>> Node("test2", variable="H")
        Node("test2", variable="H")
        >>> from hydpy.models.hland.hland_inputs import T
        >>> Node("test3", variable=T)
        Node("test3", variable=hland_T)

        The last above example shows that the string representations of
        nodes handling "class variables" use the aliases importable from
        the top-level of the *HydPy* package:

        >>> from hydpy.inputs import hland_P
        >>> Node("test4", variable=hland_P)
        Node("test4", variable=hland_P)

        For some complex *HydPy* projects, one may need to fall back on
        |FusedVariable| objects.  The string representation then relies
        on the name of the fused variable:

        >>> from hydpy import FusedVariable
        >>> from hydpy.inputs import lland_Nied
        >>> Precipitation = FusedVariable("Precip", hland_P, lland_Nied)
        >>> Node("test5", variable=Precipitation)
        Node("test5", variable=Precip)

        To avoid confusion, one cannot change |Node.variable|:

        >>> node.variable = "H"
        Traceback (most recent call last):
        ...
        AttributeError: can't set attribute
        >>> Node("test1", variable="H")
        Traceback (most recent call last):
        ...
        ValueError: The variable to be represented by a Node instance \
cannot be changed.  The variable of node `test1` is `Q` instead of `H`.  \
Keep in mind, that `name` is the unique identifier of node objects.
        """
        return vars(self)["variable"]

    @property
    def deploymode(
        self,
    ) -> Literal["newsim", "oldsim", "obs", "obs_newsim", "obs_oldsim",]:
        """Defines the kind of information a node offers its exit elements.

        *HydPy* supports the following modes:

          * newsim: Deploy the simulated values calculated just recently.  `newsim` is
            the default mode, used, for example, when a node receives a discharge value
            from an upstream element and passes it to the downstream element directly.
          * obs: Deploy observed values instead of simulated values.  The node still
            receives the simulated values from its upstream element(s).  However, it
            deploys values to its downstream element(s), which are defined externally.
            Usually, these values are observations made available within a time-series
            file. See the documentation on module |sequencetools| for further
            information on file specifications.
          * oldsim: Similar to mode `obs`.  However, it is usually applied when a node
            is supposed to deploy simulated values that have been calculated in a
            previous simulation run and stored in a sequence file.
          * obs_newsim: Combination of mode `obs` and `newsim`.  Mode `obs_newsim`
            gives priority to the provision of observation values.  New simulation
            values serve as a replacement for missing observed values.
          * obs_oldsim: Combination of mode `obs` and `oldsim`.  Mode `obs_oldsim`
            gives priority to the provision of observation values.  Old simulation
            values serve as a replacement for missing observed values.

        One relevant difference between modes `obs` and `oldsim` is that the external
        values are either handled by the `obs` or the `sim` sequence object.  Hence,
        if you select the `oldsim` mode, the values of the upstream elements calculated
        within the current simulation are not available (e.g. for parameter calibration)
        after the simulation finishes.

        Please refer to the documentation on method |HydPy.simulate| of class |HydPy|,
        which provides some application examples.

        >>> from hydpy import Node
        >>> node = Node("test")
        >>> node.deploymode
        'newsim'
        >>> node.deploymode = "obs"
        >>> node.deploymode
        'obs'
        >>> node.deploymode = "oldsim"
        >>> node.deploymode
        'oldsim'
        >>> node.deploymode = "obs_newsim"
        >>> node.deploymode
        'obs_newsim'
        >>> node.deploymode = "obs_oldsim"
        >>> node.deploymode
        'obs_oldsim'
        >>> node.deploymode = "newsim"
        >>> node.deploymode
        'newsim'
        >>> node.deploymode = "oldobs"
        Traceback (most recent call last):
        ...
        ValueError: When trying to set the routing mode of node `test`, the value \
`oldobs` was given, but only the following values are allowed: `newsim`, `oldsim`, \
`obs`, `obs_newsim`, and `obs_oldsim`.
        """
        return vars(self)["deploymode"]

    @deploymode.setter
    def deploymode(self, value: str) -> None:
        if value in ("oldsim", "obs_oldsim"):
            self.__blackhole = pointerutils.Double(0.0)
        elif value not in ("newsim", "obs", "obs_newsim", "obs_oldsim"):
            raise ValueError(
                f"When trying to set the routing mode of node `{self.name}`, "
                f"the value `{value}` was given, but only the following "
                f"values are allowed: `newsim`, `oldsim`, `obs`, `obs_newsim`, "
                f"and `obs_oldsim`."
            )
        vars(self)["deploymode"] = value
        for element in itertools.chain(self.entries, self.exits):
            model = getattr(element, "model")
            if model:
                model.connect()

    def get_double(self, group: str) -> pointerutils.Double:
        """Return the |Double| object appropriate for the given |Element|
        input or output group and the actual |Node.deploymode|.

        Method |Node.get_double| should be of interest for framework
        developers only (and eventually for model developers).

        Let |Node| object `node1` handle different simulation and
        observation values:

        >>> from hydpy import Node
        >>> node = Node("node1")
        >>> node.sequences.sim = 1.0
        >>> node.sequences.obs = 2.0

        The following `test` function shows for a given |Node.deploymode|
        if method |Node.get_double| either returns the |Double| object
        handling the simulated value (1.0) or the |Double| object handling
        the observed value (2.0):

        >>> def test(deploymode):
        ...     node.deploymode = deploymode
        ...     for group in ("inlets", "receivers", "outlets", "senders"):
        ...         print(group, node.get_double(group))

        In the default mode, nodes (passively) route simulated values by offering the
        |Double| object of sequence |Sim| to all |Element| input and output groups:

        >>> test("newsim")
        inlets 1.0
        receivers 1.0
        outlets 1.0
        senders 1.0

        Setting |Node.deploymode| to `obs` means that a node receives simulated values
        (from group `outlets` or `senders`) but provides observed values (to group
        `inlets` or `receivers`):

        >>> test("obs")
        inlets 2.0
        receivers 2.0
        outlets 1.0
        senders 1.0

        With |Node.deploymode| set to `oldsim`, the node provides (previously)
        simulated values (to group `inlets` or `receivers`) but does not receive any
        values.  Method |Node.get_double| just returns a dummy |Double| object
        initialised to 0.0 in this case (for group `outlets` or `senders`):

        >>> test("oldsim")
        inlets 1.0
        receivers 1.0
        outlets 0.0
        senders 0.0

        Other |Element| input or output groups are not supported:

        >>> node.get_double("test")
        Traceback (most recent call last):
        ...
        ValueError: Function `get_double` of class `Node` does not support the given \
group name `test`.
        """
        if group in ("inlets", "receivers", "inputs"):
            if not self.deploymode.startswith("obs"):
                return self.sequences.fastaccess.sim
            return self.sequences.fastaccess.obs
        if group in ("outlets", "senders", "outputs"):
            if self.deploymode not in ("oldsim", "obs_oldsim"):
                return self.sequences.fastaccess.sim
            return self.__blackhole
        raise ValueError(
            f"Function `get_double` of class `Node` does not "
            f"support the given group name `{group}`."
        )

    def reset(self, idx: int = 0) -> None:
        """Reset the actual value of the simulation sequence to zero.

        >>> from hydpy import Node
        >>> node = Node("node1")
        >>> node.sequences.sim = 1.0
        >>> node.reset()
        >>> node.sequences.sim
        sim(0.0)
        """
        self.sequences.fastaccess.reset(idx)

    def open_files(self, idx: int = 0) -> None:
        """Call method |Sequences.open_files| of the |Sequences| object
        handled by the actual |Node| object."""
        self.sequences.open_files(idx)

    def close_files(self) -> None:
        """Call method |Sequences.close_files| of the |Sequences| object
        handled by the actual |Node| object."""
        self.sequences.close_files()

    def prepare_allseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| object both of the |Sim| and the |Obs|
        sequence.

        Call this method before a simulation run if you need access to the whole
        time-series of the simulated and the observed series after the simulation run
        is finished.

        By default, the time-series are kept in RAM, which is the faster option.  If
        your RAM is limited, pass |False| to function argument `ramflag` to store the
        series on disk.
        """
        self.prepare_simseries(ramflag)
        self.prepare_obsseries(ramflag)

    def prepare_simseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| object of the |Sim| sequence.

        See method |Node.prepare_allseries| for further information.
        """
        self.__prepare_nodeseries("sim", ramflag)

    def prepare_obsseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| object of the |Obs| sequence.

        See method |Node.prepare_allseries| for further information.
        """
        self.__prepare_nodeseries("obs", ramflag)

    def __prepare_nodeseries(self, seqname, ramflag) -> None:
        seq = getattr(self.sequences, seqname)
        if ramflag:
            seq.activate_ram()
        else:
            seq.activate_disk()

    def plot_allseries(
        self,
        *,
        labels: Optional[Tuple[str, str]] = None,
        colors: Optional[Union[str, Tuple[str, str]]] = None,
        linestyles: Optional[Union[LineStyle, Tuple[LineStyle, LineStyle]]] = None,
        linewidths: Optional[Union[int, Tuple[int, int]]] = None,
        focus: bool = False,
        stepsize: Optional[StepSize] = None,
    ) -> "pyplot.Figure":
        """Plot the |IOSequence.series| data of both the |Sim| and the |Obs| sequence
        object.

        We demonstrate the functionalities of method |Node.plot_allseries| based on the
        `Lahn` example project:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2(lastdate="1997-01-01")

        We perform a simulation run and calculate "observed" values for node `dill`:

        >>> hp.simulate()
        >>> dill = hp.nodes.dill
        >>> dill.sequences.obs.series = dill.sequences.sim.series + 10.0

        A call to method |Node.plot_allseries| prints the time-series of both sequences
        to the screen immediately (if not, you need to activate the interactive mode of
        `matplotlib` first):

        >>> figure = dill.plot_allseries()

        Subsequent calls to |Node.plot_allseries| or the related methods
        |Node.plot_simseries| and |Node.plot_obsseries| of nodes add further
        time-series data to the existing plot:

        >>> lahn_1 = hp.nodes.lahn_1
        >>> figure = lahn_1.plot_simseries()

        You can modify the appearance of the lines by passing different arguments:

        >>> lahn_1.sequences.obs.series = lahn_1.sequences.sim.series + 10.0
        >>> figure = lahn_1.plot_obsseries(color="black", linestyle="dashed")

        All mentioned plotting functions return a |matplotlib| |figure.Figure| object.
        Use it for further plot handling, e.g. adding a title and saving the current
        figure to disk:

        >>> from hydpy.core.testtools import save_autofig
        >>> text = figure.axes[0].set_title('daily')
        >>> save_autofig("Node_plot_allseries_1.png", figure)

        .. image:: Node_plot_allseries_1.png

        You can plot the data in an aggregated manner (see the documentation on the
        function |aggregate_series| for the supported step sizes and further details):

        >>> figure = dill.plot_allseries(stepsize="monthly")
        >>> text = figure.axes[0].set_title('monthly')
        >>> save_autofig("Node_plot_allseries_2.png", figure)

        .. image:: Node_plot_allseries_2.png

        You can restrict the plotted period via the |Timegrids.eval_| |Timegrid| and
        overwrite the time-series label and other defaults via keyword arguments.
        For tuples passed to method |Node.plot_allseries|, the first entry corresponds
        to the observation and the second one to the simulation results:

        >>> pub.timegrids.eval_.dates = "1996-10-01", "1996-11-01"
        >>> figure = lahn_1.plot_allseries(labels=("measured", "calculated"),
        ...                                colors=("blue", "red"),
        ...                                linewidths=2,
        ...                                linestyles=("--", ":"),
        ...                                focus=True,)
        >>> save_autofig("Node_plot_allseries_3.png", figure)

        .. image:: Node_plot_allseries_3.png

        When necessary, all plotting methods raise errors like the following:

        >>> figure = lahn_1.plot_allseries(stepsize="quaterly")
        Traceback (most recent call last):
        ...
        ValueError: While trying to plot the time series of sequence(s) obs and sim \
of node `lahn_1` for the period `1996-10-01 00:00:00` to `1996-11-01 00:00:00`, \
the following error occurred: While trying to aggregate the given series, the \
following error occurred: Argument `stepsize` received value `quaterly`, but only \
the following ones are supported: `monthly` (default) and `daily`.

        >>> from hydpy import pub
        >>> del pub.timegrids
        >>> figure = lahn_1.plot_allseries()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to plot the time \
series of sequence(s) obs and sim of node `lahn_1` , the following error occurred: \
Attribute timegrids of module `pub` is not defined at the moment.
        """

        t = TypeVar("t", str, int)

        def _make_tuple(
            x: Union[Optional[t], Tuple[Optional[t], Optional[t]]],
        ) -> Tuple[Optional[t], Optional[t]]:
            return (x, x) if ((x is None) or isinstance(x, (str, int))) else x

        return self._plot_series(
            sequences=(self.sequences.obs, self.sequences.sim),
            labels=_make_tuple(labels),
            colors=_make_tuple(colors),
            linestyles=_make_tuple(linestyles),
            linewidths=_make_tuple(linewidths),
            focus=focus,
            stepsize=stepsize,
        )

    def plot_simseries(
        self,
        *,
        label: Optional[str] = None,
        color: Optional[str] = None,
        linestyle: Optional[LineStyle] = None,
        linewidth: Optional[int] = None,
        focus: bool = False,
        stepsize: Optional[StepSize] = None,
    ) -> "pyplot.Figure":
        """Plot the |IOSequence.series| of the |Sim| sequence object.

        See method |Node.plot_allseries| for further information.
        """
        return self._plot_series(
            [self.sequences.sim],
            labels=(label,),
            colors=(color,),
            linestyles=(linestyle,),
            linewidths=(linewidth,),
            focus=focus,
            stepsize=stepsize,
        )

    def plot_obsseries(
        self,
        *,
        label: Optional[str] = None,
        color: Optional[str] = None,
        linestyle: Optional[LineStyle] = None,
        linewidth: Optional[int] = None,
        focus: bool = False,
        stepsize: Optional[StepSize] = None,
    ) -> "pyplot.Figure":
        """Plot the |IOSequence.series| of the |Obs| sequence object.

        See method |Node.plot_allseries| for further information.
        """
        return self._plot_series(
            [self.sequences.obs],
            labels=(label,),
            colors=(color,),
            linestyles=(linestyle,),
            linewidths=(linewidth,),
            focus=focus,
            stepsize=stepsize,
        )

    def _plot_series(
        self,
        sequences: Sequence[sequencetools.IOSequence],
        labels: Iterable[Optional[str]],
        colors: Iterable[Optional[str]],
        linestyles: Iterable[Optional[str]],
        linewidths: Iterable[Optional[int]],
        focus: bool = False,
        stepsize: Optional[StepSize] = None,
    ) -> "pyplot.Figure":
        try:
            idx0, idx1 = hydpy.pub.timegrids.evalindices
            for sequence, label, color, linestyle, linewidth in zip(
                sequences, labels, colors, linestyles, linewidths
            ):
                label_ = label if label else " ".join((self.name, sequence.name))
                if stepsize is None:
                    index = _get_pandasindex()
                    ps = pandas.Series(sequence.evalseries, index=index[idx0:idx1])
                else:
                    ps = seriestools.aggregate_series(
                        series=sequence.series,
                        stepsize=stepsize,
                        aggregator=numpy.mean,
                    )
                    period = "15d" if stepsize.startswith("m") else "12h"
                    ps.index += timetools.Period(period).timedelta
                    ps = ps.rename(columns=dict(series=label_))
                kwargs = dict(
                    label=label_,
                    ax=pyplot.gca(),
                )
                if color is not None:
                    kwargs["color"] = color
                if linestyle is not None:
                    kwargs["linestyle"] = linestyle
                if linewidth is not None:
                    kwargs["linewidth"] = linewidth
                ps.plot(**kwargs)
            pyplot.legend()
            if not focus:
                pyplot.ylim((0.0, None))
            if pyplot.get_fignums():
                variable = self.variable
                if variable == "Q":
                    variable = "Q [m³/s]"
                pyplot.ylabel(variable)
            return pyplot.gcf()
        except BaseException:
            if exceptiontools.attrready(hydpy.pub, "timegrids"):
                tg = hydpy.pub.timegrids.eval_
                periodstring = f"for the period `{tg.firstdate}` to `{tg.lastdate}`"
            else:
                periodstring = ""
            objecttools.augment_excmessage(
                f"While trying to plot the time series of sequence(s) "
                f"{objecttools.enumeration(sequence.name for sequence in sequences)} "
                f"of node `{objecttools.devicename(sequences[0])}` {periodstring}"
            )

    def assignrepr(self, prefix: str = "") -> str:
        """Return a |repr| string with a prefixed assignment."""
        variable = self.variable
        if isinstance(variable, str):
            variable = f'"{variable}"'
        elif isinstance(variable, FusedVariable):
            variable = str(variable)
        else:
            variable = f"{variable.__module__.split('.')[2]}_{variable.__name__}"
        lines = [f'{prefix}Node("{self.name}", variable={variable},']
        if self.keywords:
            subprefix = f'{" "*(len(prefix)+5)}keywords='
            with objecttools.repr_.preserve_strings(True):
                with objecttools.assignrepr_tuple.always_bracketed(False):
                    line = objecttools.assignrepr_list(
                        values=sorted(self.keywords),
                        prefix=subprefix,
                        width=70,
                    )
            lines.append(line + ",")
        lines[-1] = lines[-1][:-1] + ")"
        return "\n".join(lines)

    def __repr__(self):
        return self.assignrepr()


class Element(Device[Elements]):
    """Handles a |Model| object and connects it to other models via
    |Node| objects.

    When preparing |Element| objects, one links them to nodes of different "groups",
    each group of nodes implemented as an immutable |Nodes| object:

     * |Element.inlets| and |Element.outlets| nodes handle, for
       example, the inflow to and the outflow from the respective element.
     * |Element.receivers| and |Element.senders| nodes are thought for
       information flow between arbitrary elements, for example, to inform a
       |dam| model about the discharge at a gauge downstream.
     * |Element.inputs| nodes provide optional input information, for example,
       interpolated precipitation that could alternatively be read from files
       as well.
     * |Element.outputs| nodes query optional output information, for example,
       the water level of a dam.

    You can select the relevant nodes either by passing them explicitly or passing
    their name both as single objects or as objects contained within an iterable object:

    >>> from hydpy import Element, Node
    >>> Element("test",
    ...         inlets="inl1",
    ...         outlets=Node("outl1"),
    ...         receivers=("rec1", Node("rec2")))
    Element("test",
            inlets="inl1",
            outlets="outl1",
            receivers=["rec1", "rec2"])

    Repeating such a statement with different nodes adds them to the
    existing ones without any conflict in case of repeated specifications:

    >>> Element("test",
    ...         inlets="inl1",
    ...         receivers=("rec2", "rec3"),
    ...         senders="sen1",
    ...         inputs="inp1",
    ...         outputs="outp1")
    Element("test",
            inlets="inl1",
            outlets="outl1",
            receivers=["rec1", "rec2", "rec3"],
            senders="sen1",
            inputs="inp1",
            outputs="outp1")

    Subsequent adding of nodes also works via property access:

    >>> test = Element("test")
    >>> test.inlets = "inl2"
    >>> test.outlets = None
    >>> test.receivers = ()
    >>> test.senders = "sen2", Node("sen3")
    >>> test.inputs = []
    >>> test.outputs = Node("outp2")
    >>> test
    Element("test",
            inlets=["inl1", "inl2"],
            outlets="outl1",
            receivers=["rec1", "rec2", "rec3"],
            senders=["sen1", "sen2", "sen3"],
            inputs="inp1",
            outputs=["outp1", "outp2"])

    The properties try to verify that all connections make sense.  For example,
    an element should never handle an `inlet` node that it also handles as an
    `outlet`, `input`, or `output` node:

    >>> test.inlets = "outl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `outl1` is already \
defined as a(n) outlet node, which is not allowed.

    >>> test.inlets = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `inp1` is already \
defined as a(n) input node, which is not allowed.

    >>> test.inlets = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `outp1` is already \
defined as a(n) output node, which is not allowed.

    Similar holds for the `outlet` nodes:

    >>> test.outlets = "inl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `inl1` is already \
defined as a(n) inlet node, which is not allowed.

    >>> test.outlets = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `inp1` is already \
defined as a(n) input node, which is not allowed.

    >>> test.outlets = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `outp1` is already \
defined as a(n) output node, which is not allowed.

    The following restrictions hold for the `sender` nodes:

    >>> test.senders = "rec1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `rec1` is already \
defined as a(n) receiver node, which is not allowed.

    >>> test.senders = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `inp1` is already \
defined as a(n) input node, which is not allowed.

    >>> test.senders = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `outp1` is already \
defined as a(n) output node, which is not allowed.

    The following restrictions hold for the `receiver` nodes:

    >>> test.receivers = "sen1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `sen1` is already \
defined as a(n) sender node, which is not allowed.

    >>> test.receivers = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `inp1` is already \
defined as a(n) input node, which is not allowed.

    >>> test.receivers = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `outp1` is already \
defined as a(n) output node, which is not allowed.

    The following restrictions hold for the `input` nodes:

    >>> test.inputs = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `outp1` is already \
defined as a(n) output node, which is not allowed.

    >>> test.inputs = "inl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `inl1` is already \
defined as a(n) inlet node, which is not allowed.

    >>> test.inputs = "outl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `outl1` is already \
defined as a(n) outlet node, which is not allowed.

    >>> test.inputs = "sen1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `sen1` is already \
defined as a(n) sender node, which is not allowed.

    >>> test.inputs = "rec1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `rec1` is already \
defined as a(n) receiver node, which is not allowed.

   The following restrictions hold for the `output` nodes:

    >>> test.outputs = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `inp1` is already \
defined as a(n) input node, which is not allowed.

    >>> test.outputs = "inl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `inl1` is already \
defined as a(n) inlet node, which is not allowed.

    >>> test.outputs = "outl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `outl1` is already \
defined as a(n) outlet node, which is not allowed.

    >>> test.outputs = "sen1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `sen1` is already \
defined as a(n) sender node, which is not allowed.

    >>> test.outputs = "rec1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `rec1` is already \
defined as a(n) receiver node, which is not allowed.

    Note that the discussed |Nodes| objects are immutable by default,
    disallowing to change them in other ways as described above:

    >>> test.inlets += "inl3"
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add the device `inl3` to a Nodes object, \
the following error occurred: Adding devices to immutable Nodes objects \
is not allowed.

    Setting their `mutable` flag to |True| changes this behaviour:

    >>> test.inlets.mutable = True
    >>> test.inlets.add_device("inl3")

    However, it is up to you to make sure that the added node also handles the relevant
    element in the suitable group.  In the discussed example, only node `inl2` has been
    added properly but not node `inl3`:

    >>> test.inlets.inl2.exits
    Elements("test")
    >>> test.inlets.inl3.exits
    Elements()
    """

    def __init__(
        self,
        value: ElementConstrArg,
        inlets: NodesConstrArg = None,
        outlets: NodesConstrArg = None,
        receivers: NodesConstrArg = None,
        senders: NodesConstrArg = None,
        inputs: NodesConstrArg = None,
        outputs: NodesConstrArg = None,
        keywords: MayNonerable1[str] = None,
    ):
        # pylint: disable=unused-argument
        # required for consistincy with Device.__new__
        if hasattr(self, "new_instance"):
            vars(self)["inlets"] = Nodes(mutable=False)
            vars(self)["outlets"] = Nodes(mutable=False)
            vars(self)["receivers"] = Nodes(mutable=False)
            vars(self)["senders"] = Nodes(mutable=False)
            vars(self)["inputs"] = Nodes(mutable=False)
            vars(self)["outputs"] = Nodes(mutable=False)
            self.__connections = (
                self.inlets,
                self.outlets,
                self.receivers,
                self.senders,
                self.inputs,
                self.outputs,
            )
            del vars(self)["new_instance"]
        self.keywords = keywords  # type: ignore
        if inlets is not None:
            self.inlets = inlets  # type: ignore
        if outlets is not None:
            self.outlets = outlets  # type: ignore
        if receivers is not None:
            self.receivers = receivers  # type: ignore
        if senders is not None:
            self.senders = senders  # type: ignore
        if inputs is not None:
            self.inputs = inputs  # type: ignore
        if outputs is not None:
            self.outputs = outputs  # type: ignore
        # due to internal type conversion
        # see issue https://github.com/python/mypy/issues/3004

    def __update_group(
        self,
        values: NodesConstrArg,
        targetnodes: str,
        targetelements: str,
        incompatiblenodes: Tuple[str, ...],
    ) -> None:
        elementgroup: Nodes = getattr(self, targetnodes)
        elementtargetmutable = elementgroup.mutable
        try:
            elementgroup.mutable = True
            for node in Nodes(values):
                for incomp in incompatiblenodes:
                    if node in vars(self)[incomp]:
                        raise ValueError(
                            f"For element `{self}`, the given "
                            f"{targetnodes[:-1]} node `{node}` is already "
                            f"defined as a(n) {incomp[:-1]} node, which is "
                            f"not allowed."
                        )
                elementgroup.add_device(node)
                nodegroup: Elements = getattr(node, targetelements)
                nodegroupmutable = nodegroup.mutable
                try:
                    nodegroup.mutable = True
                    nodegroup.add_device(self)
                finally:
                    nodegroup.mutable = nodegroupmutable
        finally:
            elementgroup.mutable = elementtargetmutable

    @property
    def inlets(self) -> Nodes:
        """Group of |Node| objects from which the handled |Model| object
        queries its "upstream" input values (e.g. inflow)."""
        return vars(self)["inlets"]

    @inlets.setter
    def inlets(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="inlets",
            targetelements="exits",
            incompatiblenodes=(
                "outlets",
                "inputs",
                "outputs",
            ),
        )

    @property
    def outlets(self) -> Nodes:
        """Group of |Node| objects to which the handled |Model| object
        passes its "downstream" output values (e.g. outflow)."""
        return vars(self)["outlets"]

    @outlets.setter
    def outlets(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="outlets",
            targetelements="entries",
            incompatiblenodes=(
                "inlets",
                "inputs",
                "outputs",
            ),
        )

    @property
    def receivers(self) -> Nodes:
        """Group of |Node| objects from which the handled |Model| object
        queries its "remote" information values (e.g. discharge at a
        remote downstream)."""
        return vars(self)["receivers"]

    @receivers.setter
    def receivers(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="receivers",
            targetelements="exits",
            incompatiblenodes=(
                "senders",
                "inputs",
                "outputs",
            ),
        )

    @property
    def senders(self) -> Nodes:
        """Group of |Node| objects to which the handled |Model| object
        passes its "remote" information values (e.g. water level of
        a |dam| model)."""
        return vars(self)["senders"]

    @senders.setter
    def senders(self, values: NodesConstrArg):
        self.__update_group(
            values,
            targetnodes="senders",
            targetelements="entries",
            incompatiblenodes=(
                "receivers",
                "inputs",
                "outputs",
            ),
        )

    @property
    def inputs(self) -> Nodes:
        """Group of |Node| objects from which the handled |Model| object
        queries its "external" input values, instead of reading them from
        files (e.g. interpolated precipitation)."""
        return vars(self)["inputs"]

    @inputs.setter
    def inputs(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="inputs",
            targetelements="exits",
            incompatiblenodes=(
                "inlets",
                "outlets",
                "senders",
                "receivers",
                "outputs",
            ),
        )

    @property
    def outputs(self) -> Nodes:
        """Group of |Node| objects to which the handled |Model| object passes
        its "internal" output values, available via sequences of type
        |FluxSequence| or |StateSequence| (e.g. potential evaporation)."""
        return vars(self)["outputs"]

    @outputs.setter
    def outputs(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="outputs",
            targetelements="entries",
            incompatiblenodes=(
                "inlets",
                "outlets",
                "senders",
                "receivers",
                "inputs",
            ),
        )

    @classmethod
    def get_handlerclass(cls) -> Type[Elements]:
        """Return class |Elements|."""
        return Elements

    @property
    def model(self) -> "modeltools.Model":
        """The |Model| object handled by the actual |Element| object.

        Directly after their initialisation, elements do not know which model they
        require:

        >>> from hydpy import attrready, Element
        >>> hland = Element("hland", outlets="outlet")
        >>> hland.model
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The model object of element \
`hland` has been requested but not been prepared so far.

        During scripting and when working interactively in the Python shell, it is
        often convenient to assign a |model| directly.

        >>> from hydpy.models.hland_v1 import *
        >>> parameterstep("1d")
        >>> hland.model = model
        >>> hland.model.name
        'hland_v1'

        >>> del hland.model
        >>> attrready(hland, "model")
        False

        For the "usual" approach to prepare models, please see the method
        |Element.prepare_model|.

        The following examples show that assigning |Model| objects to property
        |Element.model| creates some connection required by the respective model type
        automatically.  These examples should be relevant for developers only.

        The following |hbranch| model branches a single input value (from to node
        `inp`) to multiple outputs (nodes `out1` and `out2`):

        >>> from hydpy import Element, Node, reverse_model_wildcard_import, pub
        >>> reverse_model_wildcard_import()
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> element = Element("a_branch",
        ...                   inlets="branch_input",
        ...                   outlets=("branch_output_1", "branch_output_2"))
        >>> inp = element.inlets.branch_input
        >>> out1, out2 = element.outlets
        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> delta(0.0)
        >>> minimum(0.0)
        >>> xpoints(0.0, 3.0)
        >>> ypoints(branch_output_1=[0.0, 1.0], branch_output_2=[0.0, 2.0])
        >>> parameters.update()
        >>> element.model = model

        To show that the inlet and outlet connections are built properly, we assign a
        new value to the inlet node `inp` and verify that the suitable fractions of
        this value are passed to the outlet nodes out1` and `out2` by calling the
        method |Model.simulate|:

        >>> inp.sequences.sim = 999.0
        >>> model.simulate(0)
        >>> fluxes.originalinput
        originalinput(999.0)
        >>> out1.sequences.sim
        sim(333.0)
        >>> out2.sequences.sim
        sim(666.0)

        .. testsetup::

            >>> del pub.timegrids
        """
        model = vars(self).get("model")
        if model:
            return model
        raise exceptiontools.AttributeNotReady(
            f"The model object of element `{self.name}` has "
            f"been requested but not been prepared so far."
        )

    @model.setter
    def model(self, model: "modeltools.Model") -> None:
        vars(self)["model"] = model
        model.element = self
        model.connect()

    @model.deleter
    def model(self) -> None:
        vars(self)["model"] = None

    def prepare_model(self, clear_registry: bool = True) -> None:
        """Load the control file of the actual |Element| object, initialise
        its |Model| object, build the required connections via (an eventually
        overridden version of) method |Model.connect| of class |Model|, and
        update its  derived parameter values via calling (an eventually
        overridden version) of method |Parameters.update| of class |Parameters|.

        See method |HydPy.prepare_models| of class |HydPy| and property
        |model| of class |Element| fur further information.
        """
        try:
            try:
                hydpy.pub.timegrids
            except exceptiontools.AttributeNotReady:
                raise exceptiontools.AttributeNotReady(
                    "The initialisation period has not been defined via "
                    "attribute `timegrids` of module `pub` yet but might "
                    "be required to prepare the model properly."
                ) from None
            with hydpy.pub.options.warnsimulationstep(False):
                info = hydpy.pub.controlmanager.load_file(
                    element=self, clear_registry=clear_registry
                )
                self.model = info["model"]
                self.model.parameters.update()
        except OSError:
            if hydpy.pub.options.warnmissingcontrolfile:
                warnings.warn(
                    f"Due to a missing or no accessible control file, no "
                    f"model could be initialised for element `{self.name}`"
                )
            else:
                objecttools.augment_excmessage(
                    f"While trying to initialise the model "
                    f"object of element `{self.name}`"
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise the model "
                f"object of element `{self.name}`"
            )

    def init_model(self, clear_registry: bool = True) -> None:
        """Deprecated: use method |Element.prepare_model| instead.

        >>> from hydpy import Element
        >>> from unittest import mock
        >>> with mock.patch.object(Element, "prepare_model") as mocked:
        ...     element = Element("test")
        ...     element.init_model(False)
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.HydPyDeprecationWarning: \
Method `init_model` of class `Element` is deprecated.  \
Use method `prepare_model` instead.
        >>> mocked.call_args_list
        [call(False)]
        """
        self.prepare_model(clear_registry)
        warnings.warn(
            "Method `init_model` of class `Element` is deprecated.  "
            "Use method `prepare_model` instead.",
            exceptiontools.HydPyDeprecationWarning,
        )

    @property
    def variables(self) -> Set[NodeVariableType]:
        """A set of all different |Node.variable| values of the |Node|
        objects directly connected to the actual |Element| object.

        Suppose there is an element connected to five nodes, which (partly)
        represent different variables:

        >>> from hydpy import Element, Node
        >>> element = Element("Test",
        ...                   inlets=(Node("N1", "X"), Node("N2", "Y1")),
        ...                   outlets=(Node("N3", "X"), Node("N4", "Y2")),
        ...                   receivers=(Node("N5", "X"), Node("N6", "Y3")),
        ...                   senders=(Node("N7", "X"), Node("N8", "Y4")))

        Property |Element.variables| puts all the different variables of
        these nodes together:

        >>> sorted(element.variables)
        ['X', 'Y1', 'Y2', 'Y3', 'Y4']
        """
        variables = set()
        for connection in self.__connections:
            variables.update(connection.variables)
        return variables

    def open_files(self, idx: int = 0) -> None:
        """Call method |Sequences.open_files| of the |Sequences| object
        handled (indirectly) by the actual |Element| object."""
        self.model.sequences.open_files(idx)

    def close_files(self) -> None:
        """Call method |Sequences.close_files| of the |Sequences| object
        handled (indirectly) by the actual |Element| object."""
        self.model.sequences.close_files()

    def prepare_allseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| objects of all `input`, `factor`, `flux`,
        and `state` sequences of the model handled by this element.

        Call this method before a simulation run, if you need access to (nearly) all
        simulated series of the handled model after the simulation run is finished.

        By default, the time-series are stored in RAM, which is the faster option.  If
        your RAM is limited, pass |False| to function argument `ramflag` to store the
        series on disk.
        """
        self.prepare_inputseries(ramflag)
        self.prepare_factorseries(ramflag)
        self.prepare_fluxseries(ramflag)
        self.prepare_stateseries(ramflag)

    def prepare_inputseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| objects of the `input` sequences
        of the model handled by this element.

        See method |Element.prepare_allseries| for further information.
        """
        self.__prepare_series("inputs", ramflag)

    def prepare_factorseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| objects of the `factor` sequences of the
        model handled by this element.

        See method |Element.prepare_allseries| for further information.
        """
        self.__prepare_series("factors", ramflag)

    def prepare_fluxseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| objects of the `flux` sequences
        of the model handled by this element.

        See method |Element.prepare_allseries| for further information.
        """
        self.__prepare_series("fluxes", ramflag)

    def prepare_stateseries(self, ramflag: bool = True) -> None:
        """Prepare the |IOSequence.series| objects of the `state` sequences
        of the model handled by this element.

        See method |Element.prepare_allseries| for further information.
        """
        self.__prepare_series("states", ramflag)

    def __prepare_series(self, name_subseqs: str, ramflag: bool) -> None:
        subseqs = getattr(self.model.sequences, name_subseqs, None)
        if subseqs:
            if ramflag:
                subseqs.activate_ram()
            else:
                subseqs.activate_disk()

    def _plot_series(
        self,
        *,
        subseqs: sequencetools.SubSequences,
        names: Optional[Sequence[str]],
        average: bool,
        labels: Optional[Tuple[str, ...]],
        colors: Optional[Union[str, Tuple[str, ...]]],
        linestyles: Optional[Union[LineStyle, Tuple[LineStyle, ...]]],
        linewidths: Optional[Union[int, Tuple[int, ...]]],
        focus: bool,
    ) -> "pyplot.Figure":
        def _prepare_tuple(
            input_: Optional[Union[T, Tuple[T, ...]]],
            nmb_entries: int,
        ) -> Tuple[Optional[T], ...]:
            if isinstance(input_, tuple):
                return input_
            return nmb_entries * (input_,)

        def _make_vectors(
            array: Union[Vector[float], Matrix[float]],
        ) -> List[Vector[float]]:
            vectors = []
            for idxs in itertools.product(*(range(shp) for shp in array.shape[1:])):
                vector = array
                for idx in idxs:
                    vector = vector[:, idx]
                vectors.append(vector)
            return vectors

        idx0, idx1 = hydpy.pub.timegrids.evalindices
        index = _get_pandasindex()[idx0:idx1]
        selseqs: Iterable[sequencetools.IOSequence[Any, Any]]
        if names:
            selseqs = (getattr(subseqs, name.lower()) for name in names)
        else:
            selseqs = subseqs
        nmb_sequences = len(subseqs)
        labels_: Tuple[Optional[str], ...]
        if isinstance(labels, tuple):
            labels_ = labels
        else:
            labels_ = nmb_sequences * (labels,)
        for sequence, label, color, linestyle, linewidth in zip(
            selseqs,
            labels_,
            _prepare_tuple(colors, nmb_sequences),
            _prepare_tuple(linestyles, nmb_sequences),
            _prepare_tuple(linewidths, nmb_sequences),
        ):
            label_ = label if label else " ".join((self.name, type(sequence).__name__))
            if average:
                series = sequence.average_series()[idx0:idx1]
                label_ = f"{label_}, averaged"
            else:
                series = sequence.evalseries
            kwargs = dict(
                label=label_,
                ax=pyplot.gca(),
            )
            if color is not None:
                kwargs["color"] = color
            if linestyle is not None:
                kwargs["linestyle"] = linestyle
            if linewidth is not None:
                kwargs["linewidth"] = linewidth
            if series.ndim == 1:
                ps = pandas.Series(series, index=index)
                ps.plot(**kwargs)
            elif all(length > 0 for length in series.shape[1:]):
                vectors = _make_vectors(series)
                ps = pandas.Series(vectors[0], index=index)
                axessubplot = ps.plot(**kwargs)
                kwargs["label"] = "None"
                kwargs["color"] = axessubplot.get_lines()[-1].get_color()
                for vector in vectors:
                    ps = pandas.Series(vector, index=index)
                    ps.plot(**kwargs)
                if color:
                    kwargs["color"] = color
                else:
                    del kwargs["color"]
        lines = [l for l in pyplot.legend().get_lines() if l.get_label() != "None"]
        pyplot.legend(handles=lines)
        if not focus:
            pyplot.ylim((0.0, None))
        return pyplot.gcf()

    def plot_inputseries(
        self,
        names: Optional[Sequence[str]] = None,
        *,
        average: bool = False,
        labels: Optional[Tuple[str, ...]] = None,
        colors: Optional[Union[str, Tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, Tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, Tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> "pyplot.Figure":
        """Plot (the selected) |InputSequence| |IOSequence.series| values.

        We demonstrate the functionalities of method |Element.plot_inputseries|
        based on the `Lahn` example project:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2(lastdate="1997-01-01")

        Without any arguments, |Element.plot_inputseries| prints the time-series of
        all input sequences handled by its |Model| object directly to the screen (in
        our example |hland_inputs.P|, |hland_inputs.T|, |hland_inputs.TN|, and
        |hland_inputs.EPN| of application model |hland_v1|):

        >>> land = hp.elements.land_dill
        >>> figure = land.plot_inputseries()

        You can use the `pyplot` API of `matplotlib` to modify the returned figure or
        to save it to disk (or print it to the screen, in case the interactive mode of
        `matplotlib` is disabled):

        >>> from hydpy.core.testtools import save_autofig
        >>> save_autofig("Element_plot_inputseries.png", figure)

        .. image:: Element_plot_inputseries.png

        Methods |Element.plot_factorseries|, |Element.plot_fluxseries|, and
        |Element.plot_stateseries| work in the same manner.  Before applying them, one
        has to calculate the time-series of the |FactorSequence|, |FluxSequence|, and
        |StateSequence| objects:

        >>> hp.simulate()

        All three methods allow selecting specific sequences by passing their names
        (here, flux sequences |hland_fluxes.Q0| and |hland_fluxes.Q1| of |hland_v1|).
        Additionally, you can pass general or individual values to the arguments
        `labels`, `colors`, `linestyles`, and `linewidths`:

        >>> figure = land.plot_fluxseries(
        ...     ["q0", "q1"], labels=("direct runoff", "base flow"),
        ...     colors=("red", "green"), linestyles="--", linewidths=2)
        >>> save_autofig("Element_plot_fluxseries.png", figure)

        .. image:: Element_plot_fluxseries.png

        For 1- and 2-dimensional |IOSequence| objects, all three methods plot the
        individual time-series in the same colour.  We demonstrate this for the frozen
        (|hland_states.SP|) and the liquid (|hland_states.WC|) water equivalent of the
        snow cover of different hydrological response units.  Therefore, we restrict
        the shown period to February and March via the |Timegrids.eval_| time-grid:

        >>> with pub.timegrids.eval_(firstdate="1996-02-01", lastdate="1996-04-01"):
        ...     figure = land.plot_stateseries(["sp", "wc"])
        >>> save_autofig("Element_plot_stateseries.png", figure)

        .. image:: Element_plot_stateseries.png

        Alternatively, you can print the averaged time-series by assigning |True| to the
        argument `average`.  We demonstrate this functionality for the factor sequence
        |hland_factors.TC| (this time, without focusing on the time-series y-extent):

        >>> figure = land.plot_factorseries(["tc"], colors=("grey",))
        >>> figure = land.plot_factorseries(
        ...     ["tc"], average=True, focus=False, colors="black", linewidths=3)
        >>> save_autofig("Element_plot_factorseries.png", figure)

        .. image:: Element_plot_factorseries.png
        """
        return self._plot_series(
            subseqs=self.model.sequences.inputs,
            names=names,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def plot_factorseries(
        self,
        names: Optional[Sequence[str]] = None,
        *,
        average: bool = False,
        labels: Optional[Tuple[str, ...]] = None,
        colors: Optional[Union[str, Tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, Tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, Tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> "pyplot.Figure":
        """Plot the `factor` series of the handled model.

        See the documentation on method |Element.plot_inputseries| for additional
        information.
        """
        return self._plot_series(
            subseqs=self.model.sequences.factors,
            names=names,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def plot_fluxseries(
        self,
        names: Optional[Sequence[str]] = None,
        *,
        average: bool = False,
        labels: Optional[Tuple[str, ...]] = None,
        colors: Optional[Union[str, Tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, Tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, Tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> "pyplot.Figure":
        """Plot the `flux` series of the handled model.

        See the documentation on method |Element.plot_inputseries| for
        additional information.
        """
        return self._plot_series(
            subseqs=self.model.sequences.fluxes,
            names=names,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def plot_stateseries(
        self,
        names: Optional[Sequence[str]] = None,
        *,
        average: bool = False,
        labels: Optional[Tuple[str, ...]] = None,
        colors: Optional[Union[str, Tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, Tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, Tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> "pyplot.Figure":
        """Plot the `state` series of the handled model.

        See the documentation on method |Element.plot_inputseries| for
        additional information.
        """
        return self._plot_series(
            subseqs=self.model.sequences.states,
            names=names,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def assignrepr(self, prefix: str) -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            with objecttools.assignrepr_tuple.always_bracketed(False):
                blanks = " " * (len(prefix) + 8)
                lines = [f'{prefix}Element("{self.name}",']
                for groupname in (
                    "inlets",
                    "outlets",
                    "receivers",
                    "senders",
                    "inputs",
                    "outputs",
                ):
                    group = getattr(self, groupname, Node)
                    if group:
                        subprefix = f"{blanks}{groupname}="
                        # pylint: disable=not-an-iterable
                        # because pylint is wrong
                        nodes = [str(node) for node in group]
                        # pylint: enable=not-an-iterable
                        line = objecttools.assignrepr_list(nodes, subprefix, width=70)
                        lines.append(line + ",")
                if self.keywords:
                    subprefix = f"{blanks}keywords="
                    line = objecttools.assignrepr_list(
                        sorted(self.keywords), subprefix, width=70
                    )
                    lines.append(line + ",")
                lines[-1] = lines[-1][:-1] + ")"
                return "\n".join(lines)

    def __repr__(self) -> str:
        return self.assignrepr("")


_id2devices: Dict[Device, Dict[int, Devices]] = {}
_registry: Mapping = {Node: {}, Element: {}}
_selection: Mapping = {Node: {}, Element: {}}


@contextlib.contextmanager
def clear_registries_temporarily() -> Generator[None, None, None]:
    """Context manager for clearing the current |Node|, |Element|, and
    |FusedVariable| registries .

    Function |clear_registries_temporarily| is only available for testing
    purposes.

    These are the relevant registries for the currently initialised |Node|,
    |Element|, and |FusedVariable| objects:

    >>> from hydpy.core import devicetools
    >>> registries = (devicetools._id2devices,
    ...               devicetools._registry[devicetools.Node],
    ...               devicetools._registry[devicetools.Element],
    ...               devicetools._selection[devicetools.Node],
    ...               devicetools._selection[devicetools.Element],
    ...               devicetools._registry_fusedvariable)

    We first clear them and, just for testing, insert some numbers:

    >>> for idx, registry in enumerate(registries):
    ...     registry.clear()
    ...     registry[idx] = idx+1

    Within the `with` block, all registries are empty:

    >>> with devicetools.clear_registries_temporarily():
    ...     for registry in registries:
    ...         print(registry)
    {}
    {}
    {}
    {}
    {}
    {}

    Before leaving the `with` block, the |clear_registries_temporarily|
    method restores the contents of each dictionary:

    >>> for registry in registries:
    ...     print(registry)
    ...     registry.clear()
    {0: 1}
    {1: 2}
    {2: 3}
    {3: 4}
    {4: 5}
    {5: 6}
    """
    registries = (
        _id2devices,
        _registry[Node],
        _registry[Element],
        _selection[Node],
        _selection[Element],
        _registry_fusedvariable,
    )
    copies = tuple(copy.copy(registry) for registry in registries)
    try:
        for registry in registries:
            registry.clear()
        yield
    finally:
        for registry, copy_ in zip(registries, copies):
            registry.update(copy_)


def _get_pandasindex() -> "pandas.Index":
    """
    >>> from hydpy import pub
    >>> pub.timegrids = "2004.01.01", "2005.01.01", "1d"
    >>> from hydpy.core.devicetools import _get_pandasindex
    >>> _get_pandasindex()   # doctest: +ELLIPSIS
    DatetimeIndex(['2004-01-01 12:00:00', '2004-01-02 12:00:00',
    ...
                   '2004-12-30 12:00:00', '2004-12-31 12:00:00'],
                  dtype='datetime64[ns]', length=366, freq=None)
    """
    tg = hydpy.pub.timegrids.init
    shift = tg.stepsize / 2
    index = pandas.date_range(
        (tg.firstdate + shift).datetime,
        (tg.lastdate - shift).datetime,
        (tg.lastdate - tg.firstdate - tg.stepsize) / tg.stepsize + 1,
    )
    return index
