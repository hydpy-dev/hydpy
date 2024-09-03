# -*- coding: utf-8 -*-
"""This modules implements the fundamental features for structuring *HydPy* projects.

Module |devicetools| provides two |Device| subclasses, |Node| and |Element|.  In this
documentation, "node" stands for an object of class |Node|, "element" for an object of
class |Element|, and "device" for either of them (you cannot initialise objects of
class |Device| directly).  On the other hand, the term "nodes", for example, does not
necessarily mean an object of class |Nodes| but any other group of |Node| objects as
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

When working interactively in the Python interpreter, it might sometimes be helpful to
clear the registry entirely.  However, Do this with care because defining nodes with
already assigned names might result in surprises due to using their names for
identification:

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
import collections
import contextlib
import copy
import itertools
import operator
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import masktools
from hydpy.core import objecttools
from hydpy.core import printtools
from hydpy.core import propertytools
from hydpy.core import sequencetools
from hydpy.core import seriestools
from hydpy.core import timetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from matplotlib import pyplot
    import pandas
    from hydpy.core import auxfiletools
    from hydpy.core import hydpytools
    from hydpy.core import modeltools
    from hydpy.cythons import pointerutils
else:
    pandas = exceptiontools.OptionalImport("pandas", ["pandas"], locals())
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())
    from hydpy.cythons.autogen import pointerutils

TypeDevice = TypeVar("TypeDevice", bound="Device")
TypeDevices = TypeVar("TypeDevices", bound="Devices[Any]")
NodeOrElement = Union["Node", "Element"]
TypeNodeElement = TypeVar("TypeNodeElement", "Node", "Element", NodeOrElement)

NodesConstrArg = MayNonerable2["Node", str]
ElementsConstrArg = MayNonerable2["Element", str]
NodeConstrArg = Union["Node", str]
ElementConstrArg = Union["Element", str]
IOSequenceArg = Union[str, sequencetools.IOSequence, type[sequencetools.IOSequence]]

NodeVariableType = Union[str, sequencetools.InOutSequenceTypes, "FusedVariable"]

_default_variable: NodeVariableType = "Q"


class Keywords(set[str]):
    """Set of keyword arguments used to describe and search for |Element| and |Node|
    objects."""

    device: Optional[Device]

    def __init__(self, *names: str):
        self.device = None
        self._check_keywords(names)
        super().__init__(names)

    def startswith(self, name: str) -> list[str]:
        """Return a list of all keywords, starting with the given string.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.startswith("keyword")
        ['keyword_3', 'keyword_4']
        """
        return sorted(keyword for keyword in self if keyword.startswith(name))

    def endswith(self, name: str) -> list[str]:
        """Return a list of all keywords ending with the given string.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.endswith("keyword")
        ['first_keyword', 'second_keyword']
        """
        return sorted(keyword for keyword in self if keyword.endswith(name))

    def contains(self, name: str) -> list[str]:
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
                    f"While trying to add the keyword `{name}` to device "
                    f"{objecttools.devicename(self.device)}"
                )

    def update(self, *names: str) -> None:  # type: ignore[override]
        """Before updating, the given names are checked to be valid variable
        identifiers.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.update("test_1", "test 2")   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to add the keyword `test 2` to device ?, the \
following error occurred: The given name string `test 2` does not define a valid \
variable identifier.  ...

        Note that even the first string (`test1`) is not added due to the second one
        (`test 2`) being invalid.

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
        """Before adding a new name, it is checked to be a valid variable identifier.

        >>> from hydpy.core.devicetools import Keywords
        >>> keywords = Keywords("first_keyword", "second_keyword",
        ...                     "keyword_3", "keyword_4",
        ...                     "keyboard")
        >>> keywords.add("1_test")   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to add the keyword `1_test` to device ?, the \
following error occurred: The given name string `1_test` does not define a valid \
variable identifier.  ...

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


_registry_fusedvariable: dict[str, FusedVariable] = {}


class FusedVariable:
    """Combines |InputSequence|, |ReceiverSequence|, and |OutputSequence| subclasses of
    different models dealing with the same property in a single variable.

    Class |FusedVariable| is one possible type of property |Node.variable| of class
    |Node|.  We need it in some *HydPy* projects where the involved models not only
    pass runoff to each other but also share other types of data.  Each
    project-specific |FusedVariable| object serves as a "meta-type", indicating which
    input and output sequences of the different models correlate and are thus
    connectable.

    Using class |FusedVariable| is easiest to explain by a concrete example.  Assume we
    use |conv_nn| to interpolate the air temperature for a specific location.  We use
    this temperature as input to an |meteo_temp_io| model, which passes it to an
    |evap_ret_fao56| model, which requires this and other meteorological data to
    calculate potential evapotranspiration.  Further, we pass the estimated potential
    evapotranspiration as input to |lland_dd| for calculating the actual
    evapotranspiration, which receives it through a submodel instance of |evap_ret_io|.
    Hence, we need to connect the output sequence
    |evap_fluxes.MeanReferenceEvapotranspiration| of |evap_ret_fao56| with the input
    sequence |evap_inputs.ReferenceEvapotranspiration| of |evap_ret_io|.

    ToDo: This example needs to be updated.  Today one could directly use
          |evap_ret_fao56| as a submodel of |lland_dd|.  However, it still demonstrates
          the relevant connection mechanisms correctly.

    Additionally, |lland_dd| requires temperature data itself for modelling snow
    processes, introducing the problem that we need to use the same data (the output of
    |conv_nn|) as the input of two differently named input sequences
    (|meteo_inputs.Temperature| and |lland_inputs.TemL| for |meteo_temp_io| and
    |lland_dd|, respectively).

    We need to create two |FusedVariable| objects, for our concrete example.  `E`
    combines |evap_fluxes.MeanReferenceEvapotranspiration| and
    |evap_inputs.ReferenceEvapotranspiration| and `T` combines
    |meteo_inputs.Temperature| and |lland_inputs.TemL| (for convenience, we import
    their globally available aliases):

    >>> from hydpy import FusedVariable
    >>> from hydpy.aliases import (
    ...     evap_inputs_ReferenceEvapotranspiration, meteo_inputs_Temperature,
    ...     lland_inputs_TemL, evap_fluxes_MeanReferenceEvapotranspiration)
    >>> E = FusedVariable("E", evap_inputs_ReferenceEvapotranspiration,
    ...                        evap_fluxes_MeanReferenceEvapotranspiration)
    >>> T = FusedVariable("T", meteo_inputs_Temperature, lland_inputs_TemL)

    Now we can construct the network:

     * Node `t1` handles the original temperature data and serves as the input node to
       element `conv`. We define the (arbitrarily selected) string `Temp` to be its
       variable.
     * Node `e` receives the potential evapotranspiration calculated by element `evap`
       and passes it to element `lland`.  Node `e` thus receives the fused variable `E`.
     * Node `t2` handles the interpolated temperature and serves as the outlet node of
       element `conv` and the input node to elements `evap` and `lland`.  Node `t2`
       thus receives the fused variable `T`.

    >>> from hydpy import Node, Element
    >>> t1 = Node("t1", variable="Temp")
    >>> t2 = Node("t2", variable=T)
    >>> e = Node("e", variable=E)
    >>> conv = Element("element_conv", inlets=t1, outlets=t2)
    >>> evap = Element("element_evap", inputs=t2, outputs=e)
    >>> lland = Element("element_lland", inputs=(t2, e), outlets="node_q")

    Now we can prepare the different model objects and assign them to their
    corresponding elements (note that parameters |conv_control.InputCoordinates| and
    |conv_control.OutputCoordinates| of |conv_nn| first require information on the
    location of the relevant nodes):

    >>> from hydpy import prepare_model
    >>> model_conv = prepare_model("conv_nn")
    >>> model_conv.parameters.control.inputcoordinates(t1=(0, 0))
    >>> model_conv.parameters.control.outputcoordinates(t2=(1, 1))
    >>> model_conv.parameters.control.maxnmbinputs(1)
    >>> model_conv.parameters.update()
    >>> conv.model = model_conv
    >>> model = prepare_model("evap_ret_fao56")
    >>> model.tempmodel = prepare_model("meteo_temp_io")
    >>> evap.model = model
    >>> model = prepare_model("lland_dd")
    >>> model.aetmodel = prepare_model("evap_aet_minhas")
    >>> model.aetmodel.petmodel = prepare_model("evap_ret_io")
    >>> lland.model = model

    We assign a temperature value to node `t1`:

    >>> t1.sequences.sim = -273.15

    Model |conv_nn| can now perform a simulation step and pass its output to node `t2`:

    >>> conv.model.simulate(0)
    >>> t2.sequences.sim
    sim(-273.15)

    Without further configuration, |evap_ret_fao56| cannot perform any simulation
    steps.  Hence, we just call its |Model.load_data| method to show that the input
    sequence |meteo_inputs.Temperature| of its submodel is well connected to the |Sim|
    sequence of node `t2` and receives the correct data:

    >>> evap.model.load_data(0)
    >>> evap.model.tempmodel.sequences.inputs.temperature
    temperature(-273.15)

    The output sequence |evap_fluxes.MeanReferenceEvapotranspiration| is also well
    connected.  A call to method |Model.update_outputs| passes its (manually set) value
    to node `e`, respectively:

    >>> evap.model.sequences.fluxes.meanreferenceevapotranspiration = 999.9
    >>> evap.model.update_outputs()
    >>> e.sequences.sim
    sim(999.9)

    Finally, both input sequences |lland_inputs.TemL| and
    |evap_inputs.ReferenceEvapotranspiration| receive the current values of nodes `t2`
    and `e`:

    >>> lland.model.load_data(0)
    >>> lland.model.sequences.inputs.teml
    teml(-273.15)
    >>> lland.model.aetmodel.petmodel.sequences.inputs.referenceevapotranspiration
    referenceevapotranspiration(999.9)

    When defining fused variables, class |FusedVariable| performs some registration
    behind the scenes, similar to what classes |Node| and |Element| do.  Again, the
    name works as the identifier, and we force the same fused variable to exist only
    once, even when defined in different selection files repeatedly.  Hence, when we
    repeat the definition from above, we get the same object:

    >>> Test = FusedVariable("T", meteo_inputs_Temperature, lland_inputs_TemL)
    >>> T is Test
    True

    Changing the member sequences of an existing fused variable is not allowed:

    >>> from hydpy.aliases import hland_inputs_T
    >>> FusedVariable("T", hland_inputs_T, lland_inputs_TemL)
    Traceback (most recent call last):
    ...
    ValueError: The sequences combined by a FusedVariable object cannot be changed.  \
The already defined sequences of the fused variable `T` are `lland_inputs_TemL and \
meteo_inputs_Temperature` instead of `hland_inputs_T and lland_inputs_TemL`.  Keep in \
mind, that `name` is the unique identifier for fused variable instances.

    Defining additional fused variables with the same member sequences is not advisable
    but is allowed:

    >>> Temp = FusedVariable("Temp", meteo_inputs_Temperature, lland_inputs_TemL)
    >>> T is Temp
    False

    To get an overview of the existing fused variables, call method
    |FusedVariable.get_registry|:

    >>> len(FusedVariable.get_registry())
    3

    Principally, you can clear the registry via method |FusedVariable.clear_registry|,
    but remember it does not remove |FusedVariable| objects from the running process
    being otherwise referenced:

    >>> FusedVariable.clear_registry()
    >>> FusedVariable.get_registry()
    ()
    >>> t2.variable
    FusedVariable("T", lland_inputs_TemL, meteo_inputs_Temperature)

    .. testsetup::

        >>> Node.clear_all()
        >>> Element.clear_all()
    """

    _name: str
    _aliases: tuple[str, ...]
    _variables: tuple[sequencetools.InOutSequenceTypes, ...]
    _alias2variable: dict[str, sequencetools.InOutSequenceTypes]

    def __new__(
        cls, name: str, *sequences: sequencetools.InOutSequenceTypes
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
                f"The sequences combined by a {type(self).__name__} object cannot be "
                f"changed.  The already defined sequences of the fused variable "
                f"`{name}` are `{objecttools.enumeration(fusedvariable._aliases)}` "
                f"instead of `{objecttools.enumeration(aliases)}`.  Keep in mind, "
                f"that `name` is the unique identifier for fused variable instances."
            )
        self._name = name
        self._aliases = aliases
        self._variables = variables
        _registry_fusedvariable[name] = self
        self._alias2variable = dict(zip(self._aliases, self._variables))
        return self

    @classmethod
    def get_registry(cls) -> tuple[FusedVariable, ...]:
        """Get all |FusedVariable| objects initialised so far."""
        return tuple(_registry_fusedvariable.values())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the registry from all |FusedVariable| objects initialised so far.

        Use this method only for good reasons!
        """
        return _registry_fusedvariable.clear()

    def __iter__(self) -> Iterator[sequencetools.InOutSequenceTypes]:
        yield from self._variables

    def __contains__(self, item: object) -> bool:
        sqt = sequencetools
        if isinstance(item, (sqt.LinkSequence, sqt.InputSequence, sqt.OutputSequence)):
            item = type(item)
        return item in self._variables

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f'FusedVariable("{self._name}", {", ".join(self._aliases)})'


class Devices(Generic[TypeDevice]):
    """Base class for class |Elements| and class |Nodes|.

    The following features are common to class |Nodes| and class |Elements|.  We
    arbitrarily select class |Nodes| for all examples.

    To initialise a |Nodes| collection, pass a variable number of |str| or |Node|
    objects.  Strings are used to create new or query already existing nodes
    automatically:

    >>> from hydpy import Node, Nodes
    >>> nodes = Nodes("na",
    ...               Node("nb", variable="W"),
    ...               Node("nc", keywords=("group_a", "group_1")),
    ...               Node("nd", keywords=("group_a", "group_2")),
    ...               Node("ne", keywords=("group_b", "group_1")))

    |Nodes| instances are containers supporting attribute and item access. You can
    access each node directly by its name:

    >>> nodes.na
    Node("na", variable="Q")
    >>> nodes["na"]
    Node("na", variable="Q")

    In many situations, a |Nodes| instance contains a single node only.  One can query
    such a single node using zero as the index for convenience:

    >>> Nodes("na")[0]
    Node("na", variable="Q")

    Other number-based indexed are not allowed:

    >>> Nodes("na", "nb")[1]
    Traceback (most recent call last):
    ...
    KeyError: 'Indexing with other numbers than `0` is not supported but `1` is given.'

    An automatic check prevents unexpected results when applying zero-based indexing on
    |Nodes| instances containing multiple nodes:

    >>> Nodes("na", "nb")[0]
    Traceback (most recent call last):
    ...
    KeyError: 'Indexing with `0` is only safe for Node handlers containing a single \
Node.'

    Wrong node names result in the following error messages:

    >>> nodes.wrong
    Traceback (most recent call last):
    ...
    AttributeError: The selected Nodes object has neither a `wrong` attribute nor \
does it handle a Node object with name or keyword `wrong`, which could be returned.
    >>> nodes["wrong"]
    Traceback (most recent call last):
    ...
    KeyError: 'No node named `wrong` available.'

    As explained in more detail in the documentation on property |Device.keywords|, you
    can also use the keywords of the individual nodes to query the relevant ones:

    >>> nodes.group_a
    Nodes("nc", "nd")

    You can remove nodes both via the attribute and item syntax:

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

    >>> nodes.add_device("na")
    >>> del nodes["na"]
    >>> del nodes["na"]
    Traceback (most recent call last):
    ...
    KeyError: 'No node named `na` available.'

    However, as shown by the following example, setting devices via attribute
    assignment or item assignment could result in inconsistencies and is thus not
    allowed (see method |Devices.add_device| instead):

    >>> nodes.NF = Node("nf")
    Traceback (most recent call last):
    ...
    AttributeError: Setting attributes of Nodes objects could result in confusion \
whether a new attribute should be handled as a Node object or as a "normal" attribute \
and is thus not support, hence `NF` is rejected.
    >>> nodes["NF"] = Node("nf")
    Traceback (most recent call last):
    ...
    TypeError: 'Nodes' object does not support item assignment

    |Nodes| instances support iteration:

    >>> len(nodes)
    4
    >>> for node in nodes:
    ...     print(node.name, end=",")
    nb,nc,nd,ne,

    The binary operators `+`, `+=`, `-`, and `-=` support adding and removing single
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

    _mutable: bool
    _name2device: dict[str, TypeDevice]
    _shadowed_keywords: set[str]

    def __new__(
        cls, *values: MayNonerable2[TypeDevice, str], mutable: bool = True
    ) -> Devices[Any]:
        if len(values) == 1 and isinstance(values[0], Devices):
            return values[0]
        self = super().__new__(cls)
        setattr_ = super().__setattr__
        setattr_(self, "_mutable", mutable)
        setattr_(self, "_name2device", {})
        setattr_(self, "_shadowed_keywords", set())
        contentclass = self.get_contentclass()
        try:
            for value in objecttools.extract(
                values, types_=(contentclass, str), skip=True
            ):
                self.add_device(value, force=True)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise a `{type(self).__name__}` object"
            )
        return self

    @staticmethod
    @abc.abstractmethod
    def get_contentclass() -> type[TypeDevice]:
        """To be overridden."""

    def add_device(self, device: Union[TypeDevice, str], force: bool = False) -> None:
        """Add the given |Node| or |Element| object to the actual |Nodes| or |Elements|
        object.

        You can pass either a string or a device:

        >>> from hydpy import Nodes
        >>> nodes = Nodes()
        >>> nodes.add_device("old_node")
        >>> nodes
        Nodes("old_node")
        >>> nodes.add_device("new_node")
        >>> nodes
        Nodes("new_node", "old_node")

        Method |Devices.add_device| is disabled for immutable |Nodes| and |Elements|
        objects by default:

        >>> nodes._mutable = False
        >>> nodes.add_device("newest_node")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to add the device `newest_node` to a Nodes object, \
the following error occurred: Adding devices to immutable Nodes objects is not allowed.

        Use parameter `force` to override this safety mechanism if necessary:

        >>> nodes.add_device("newest_node", force=True)
        >>> nodes
        Nodes("new_node", "newest_node", "old_node")
        """
        try:
            if force or self._mutable:
                _device = self.get_contentclass()(device)
                self._name2device[_device.name] = _device
                _id2devices[_device][id(self)] = cast(Devices[Device], self)  # ToDo
            else:
                raise RuntimeError(
                    f"Adding devices to immutable {type(self).__name__} objects is "
                    f"not allowed."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to add the device `{device}` to a "
                f"{type(self).__name__} object"
            )

    def remove_device(
        self, device: Union[TypeDevice, str], force: bool = False
    ) -> None:
        """Remove the given |Node| or |Element| object from the actual |Nodes| or
        |Elements| object.

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
        ValueError: While trying to remove the device `node_z` from a Nodes object, \
the following error occurred: The actual Nodes object does not handle such a device.

        Method |Devices.remove_device| is disabled for immutable |Nodes| and |Elements|
        objects by default:

        >>> nodes.add_device(node_x)
        >>> nodes._mutable = False
        >>> nodes.remove_device("node_x")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to remove the device `node_x` from a Nodes object, \
the following error occurred: Removing devices from immutable Nodes objects is not \
allowed.
        >>> nodes
        Nodes("node_x")

        Use parameter `force` to override this safety mechanism if necessary:

        >>> nodes.remove_device("node_x", force=True)
        >>> nodes
        Nodes()
        """
        try:
            if force or self._mutable:
                _device = self.get_contentclass()(device)
                try:
                    del self._name2device[_device.name]
                except KeyError:
                    raise ValueError(
                        f"The actual {type(self).__name__} object does not handle "
                        f"such a device."
                    ) from None
                del _id2devices[_device][id(self)]
            else:
                raise RuntimeError(
                    f"Removing devices from immutable {type(self).__name__} objects "
                    f"is not allowed."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to remove the device `{device}` from a "
                f"{type(self).__name__} object"
            )

    @property
    def names(self) -> tuple[str, ...]:
        """A sorted tuple of the names of the handled devices.

        >>> from hydpy import Nodes
        >>> Nodes("a", "c", "b").names
        ('a', 'b', 'c')
        """
        return tuple(device.name for device in self)

    @property
    def devices(self) -> tuple[TypeDevice, ...]:
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
    def keywords(self) -> set[str]:
        """A set of all keywords of all handled devices.

        In addition to attribute access via device names, |Nodes| and |Elements|
        objects allow for attribute access via keywords, allowing for an efficient
        search of certain groups of devices.  Let us use the example from above, where
        the nodes `na` and `nb` have no keywords, but each of the other three nodes
        both belongs to either `group_a` or `group_b` and `group_1` or `group_2`:

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

        If you are interested in inspecting all devices belonging to `group_a`, select
        them via this keyword:

        >>> subgroup = nodes.group_1
        >>> subgroup
        Nodes("nc", "ne")

        You can further restrict the search by also selecting the devices belonging to
        `group_b`, which holds only for node "e", in the discussed example:

        >>> subsubgroup = subgroup.group_b
        >>> subsubgroup
        Node("ne", variable="Q",
             keywords=["group_1", "group_b"])

        Note that the keywords already used for building a device subgroup are not
        informative anymore (as they hold for each device) and are thus not shown
        anymore:

        >>> sorted(subgroup.keywords)
        ['group_a', 'group_b']

        The latter might be confusing if you intend to work with a device subgroup for
        a longer time.  After copying the subgroup, all keywords of the contained
        devices are available again:

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

    def search_keywords(self: TypeDevices, *keywords: str) -> TypeDevices:
        """Search for all devices handling at least one of the given keywords and
        return them.

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

    def copy(self: TypeDevices) -> TypeDevices:
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

        Changing the |Device.name| of a device is recognised both by the original and
        the copied collection objects:

        >>> new.x.name = "z"
        >>> old.z
        Node("z", variable="Q")
        >>> new.z
        Node("z", variable="Q")

        Deep copying is permitted due to the above reason:

        >>> copy.deepcopy(old)
        Traceback (most recent call last):
        ...
        NotImplementedError: Deep copying of Nodes objects is not supported, as it \
would require to make deep copies of the Node objects themselves, which is in \
conflict with using their names as identifiers.
        """
        # pylint: disable=protected-access
        new = type(self)()
        vars(new).update(vars(self))
        new._name2device = copy.copy(self._name2device)
        new._shadowed_keywords.clear()
        for device in self:
            _id2devices[device][id(new)] = new
        return new

    def intersection(self: TypeDevices, *other: TypeDevices) -> TypeDevices:
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

    def __deepcopy__(self, dict_: NoReturn) -> NoReturn:
        classname = type(self).__name__
        raise NotImplementedError(
            f"Deep copying of {classname} objects is not supported, as it would "
            f"require to make deep copies of the {classname[:-1]} objects themselves, "
            f"which is in conflict with using their names as identifiers."
        )

    def __select_devices_by_keyword(self: TypeDevices, name: str) -> TypeDevices:
        # pylint: disable=protected-access
        devices = type(self)(*(device for device in self if name in device.keywords))
        devices._shadowed_keywords = self._shadowed_keywords.copy()
        devices._shadowed_keywords.add(name)
        return devices

    def __getattr__(self: TypeDevices, name: str) -> Union[TypeDevice, TypeDevices]:
        if name in self._name2device:
            return cast(TypeDevice, self._name2device[name])  # ToDo
        _devices = self.__select_devices_by_keyword(name)
        if len(_devices) > 1:
            return _devices
        if len(_devices) == 1:
            return cast(TypeDevice, _devices.devices[0])  # ToDo
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

    def __getitem__(self, name: Union[Literal[0], str]) -> TypeDevice:
        if name == 0:
            devices = tuple(self._name2device.values())
            if len(devices) == 1:
                return tuple(devices)[0]
            device = self.get_contentclass().__name__
            raise KeyError(
                f"Indexing with `0` is only safe for {device} handlers containing "
                f"a single {device}."
            ) from None
        try:
            return self._name2device[name]
        except KeyError:
            if isinstance(name, int):  # type: ignore[unreachable]
                raise KeyError(
                    f"Indexing with other numbers than `0` is not supported but "
                    f"`{name}` is given."
                ) from None
            device = self.get_contentclass().__name__.lower()
            raise KeyError(f"No {device} named `{name}` available.") from None

    def __setitem__(self, name: str, value: TypeDevice) -> NoReturn:
        raise TypeError(
            f"'{type(self).__name__}' object does not support item assignment"
        )

    def __delitem__(self, name: str) -> None:
        try:
            del self._name2device[name]
        except KeyError:
            device = self.get_contentclass().__name__.lower()
            raise KeyError(f"No {device} named `{name}` available.") from None

    def __iter__(self) -> Iterator[TypeDevice]:
        for _, device in sorted(self._name2device.items()):
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

    def __add__(self: TypeDevices, other: Mayberable2[TypeDevice, str]) -> TypeDevices:
        new = copy.copy(self)
        new._mutable = True
        for device in type(self)(other):
            new.add_device(device)
        return new

    def __iadd__(self: TypeDevices, other: Mayberable2[TypeDevice, str]) -> TypeDevices:
        for device in type(self)(other):
            self.add_device(device)
        return self

    def __sub__(self: TypeDevices, other: Mayberable2[TypeDevice, str]) -> TypeDevices:
        new = copy.copy(self)
        new._mutable = True
        for device in type(self)(other):
            try:
                new.remove_device(device)
            except ValueError:
                pass
        return new

    def __isub__(self: TypeDevices, other: Mayberable2[TypeDevice, str]) -> TypeDevices:
        for device in type(self)(other):
            try:
                self.remove_device(device)
            except ValueError:
                pass
        return self

    def __compare(self, other: object, func: Callable[[Any, Any], bool]) -> bool:
        if isinstance(other, type(self)):
            return func(set(self), set(other))
        return NotImplemented

    def __lt__(self: TypeDevices, other: TypeDevices) -> bool:
        return self.__compare(other, operator.lt)

    def __le__(self: TypeDevices, other: TypeDevices) -> bool:
        return self.__compare(other, operator.le)

    def __eq__(self, other: object) -> bool:
        return self.__compare(other, operator.eq)

    def __ne__(self, other: object) -> bool:
        return self.__compare(other, operator.ne)

    def __ge__(self: TypeDevices, other: TypeDevices) -> bool:
        return self.__compare(other, operator.ge)

    def __gt__(self: TypeDevices, other: TypeDevices) -> bool:
        return self.__compare(other, operator.gt)

    def __repr__(self) -> str:
        return self.assignrepr("")

    def assignrepr(self, prefix: str = "") -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            options = hydpy.pub.options
            with options.ellipsis(2, optional=True):
                prefix += f"{type(self).__name__}("
                repr_ = objecttools.assignrepr_values(self.names, prefix, width=70)
                return repr_ + ")"

    def __dir__(self) -> list[str]:
        """
        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes(Node("name1", keywords="keyword1"),
        ...               Node("name2", keywords=("keyword2a", "keyword2a")))
        >>> sorted(set(dir(nodes)) - set(object.__dir__(nodes)))
        ['keyword1', 'keyword2a', 'name1', 'name2']
        """
        return (
            cast(list[str], super().__dir__()) + list(self.names) + list(self.keywords)
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
        *values: MayNonerable2[Node, str],
        mutable: bool = True,
        defaultvariable: NodeVariableType = "Q",
    ) -> Nodes:
        global _default_variable
        _default_variable_copy = _default_variable
        try:
            _default_variable = defaultvariable
            return super().__new__(  # type: ignore[return-value]
                cls, *values, mutable=mutable
            )
        finally:
            _default_variable = _default_variable_copy

    @staticmethod
    def get_contentclass() -> type[Node]:
        """Return class |Node|."""
        return Node

    @printtools.print_progress
    def prepare_allseries(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |Node.prepare_allseries| of all handled |Node| objects."""
        for node in printtools.progressbar(self):
            node.prepare_allseries(allocate_ram=allocate_ram, jit=jit)

    @printtools.print_progress
    def prepare_simseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |Node.prepare_simseries| of all handled |Node| objects."""
        for node in printtools.progressbar(self):
            node.prepare_simseries(
                allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
            )

    @printtools.print_progress
    def prepare_obsseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |Node.prepare_obsseries| of all handled |Node| objects."""
        for node in printtools.progressbar(self):
            node.prepare_obsseries(
                allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
            )

    @printtools.print_progress
    def load_allseries(self) -> None:
        """Call methods |Nodes.load_simseries| and |Nodes.load_obsseries|."""
        self.load_simseries()
        self.load_obsseries()

    @printtools.print_progress
    def load_simseries(self) -> None:
        """Call method |IOSequence.load_series| of all |Sim| objects with an activated
        |IOSequence.memoryflag|."""
        self.__load_nodeseries("sim")

    @printtools.print_progress
    def load_obsseries(self) -> None:
        """Call method |IOSequence.load_series| of all |Obs| objects with an activated
        |IOSequence.memoryflag|."""
        self.__load_nodeseries("obs")

    def __load_nodeseries(self, seqname: str) -> None:
        for node in printtools.progressbar(self):
            node.sequences[seqname].load_series()

    @printtools.print_progress
    def save_allseries(self) -> None:
        """Call methods |Nodes.save_simseries| and |Nodes.save_obsseries|."""
        self.save_simseries()
        self.save_obsseries()

    @printtools.print_progress
    def save_simseries(self) -> None:
        """Call method |IOSequence.save_series| of all |Sim| objects with an activated
        |IOSequence.memoryflag|."""
        self.__save_nodeseries("sim")

    @printtools.print_progress
    def save_obsseries(self) -> None:
        """Call method |IOSequence.save_series| of all |Obs| objects with an activated
        |IOSequence.memoryflag|."""
        self.__save_nodeseries("obs")

    def __save_nodeseries(self, seqname: str) -> None:
        for node in printtools.progressbar(self):
            seq = node.sequences[seqname]
            if seq.ramflag:
                seq.save_series()

    @property
    def variables(self) -> set[NodeVariableType]:
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

    For the general usage of |Elements| objects, please see the documentation on its
    base class |Devices|.
    """

    @staticmethod
    def get_contentclass() -> type[Element]:
        """Return class |Element|."""
        return Element

    @property
    def collectives(self) -> dict[Optional[str], tuple[Element, ...]]:
        """The names and members of all currently relevant collectives.

        Note that all |Element| instances not belonging to any |Element.collective| are
        returned as a separate group:

        >>> from hydpy import Element, Elements
        >>> Elements().collectives
        {}
        >>> for group, elements in Elements(
        ...     Element("a"), Element("b1", collective="b"), Element("c"),
        ...     Element("d1", collective="d"), Element("b2", collective="b")
        ... ).collectives.items():
        ...     print(group, [e.name for e in elements])
        None ['a', 'c']
        b ['b1', 'b2']
        d ['d1']
        """
        collectives = collections.defaultdict(lambda: [])
        for element in self:
            collectives[element.collective].append(element)
        return {c: tuple(e) for c, e in collectives.items()}

    def unite_collectives(self) -> Elements:
        """Create overarching elements for all original elements that belong to a
        collective.

        All elements of the same |Element.collective| must be handled as one entity
        during simulation.  A typical use case is that individual elements describe
        different channels of a large river network, and all of them must be handled
        simultaneously by a single routing model instance to account for backwater
        effects.  We create such an example by combining instances of |musk_classic|
        (for "hydrological" routing neglecting backwater effects) and |sw1d_channel|
        (for "hydrodynamic" routing considering backwater effects).

        First, we create a |FusedVariable| object for connecting the inlets and outlets
        of |musk_classic| and |sw1d_channel|:

        >>> from hydpy import FusedVariable
        >>> from hydpy.aliases import (musk_inlets_Q, sw1d_inlets_LongQ,
        ...                            musk_outlets_Q, sw1d_outlets_LongQ)
        >>> q = FusedVariable("Q", musk_inlets_Q, sw1d_inlets_LongQ,
        ...                   musk_outlets_Q, sw1d_outlets_LongQ)

        The spatial setting is more concise than realistic and consists of four
        channels.  Channel `A` discharges into channel `B`, which discharges into
        channel `C`, which discharges into channel `D`.  We neglect backwater effects
        within channels `A` and `D`.  Hence we do not need to associate them with a
        collective and |musk_classic| becomes an appropriate choice.  Channel `B` and
        `C` are represented by separate collectives.  Hence, the setting could account
        for backwater effects within both channels but not between them.  Channel `B`
        consists only of a single subchannel (represented by element `b`), while
        channel `C` consists of two subchannels (represented by elements `c1` and
        `c2`):

        >>> from hydpy import Element, Elements, Nodes
        >>> q_a, q_a_b, q_b_c1, q_c1_c2, q_c2_d, q_d = Nodes(
        ...     "q_a", "q_a_b", "q_b_c1", "q_c1_c2", "q_c2_d", "q_d",
        ...     defaultvariable=q)
        >>> e_a = Element("e_a", inlets=q_a, outlets=q_a_b)
        >>> e_b = Element("e_b", collective="B", inlets=q_a_b, outlets=q_b_c1)
        >>> e_c1 = Element("e_c1", collective="C", inlets=q_b_c1, outlets=q_c1_c2)
        >>> e_c2 = Element("e_c2", collective="C", inlets=q_c1_c2, outlets=q_c2_d)
        >>> e_d = Element("e_d", inlets=q_c2_d, outlets=q_d)
        >>> elements = Elements(e_a, e_b, e_c1, e_c2, e_d)

        Method |Elements.unite_collectives| expects only those elements belonging to a
        collective to come with a ready |Model| instance.  So we only need to prepare
        |sw1d_channel| instances for elements `b`, `c1`, and `c2`, including the
        required submodels:

        >>> from hydpy import prepare_model, pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> for element in (e_b, e_c1, e_c2):
        ...     channel = prepare_model("sw1d_channel")
        ...     channel.parameters.control.nmbsegments(1)
        ...     add_storage = channel.add_storagemodel_v1
        ...     with add_storage("sw1d_storage", position=0, update=False):
        ...         pass
        ...     if element in (e_b, e_c1):
        ...         with channel.add_routingmodel_v1("sw1d_q_in", position=0):
        ...             pass
        ...     if element is e_c1:
        ...         with channel.add_routingmodel_v2("sw1d_lias", position=1):
        ...             lengthupstream(1.0)
        ...             lengthdownstream(1.0)
        ...     if element in (e_b, e_c2):
        ...         with channel.add_routingmodel_v3("sw1d_weir_out", position=1):
        ...             pass
        ...     element.model = channel

        Based on the defined five elements, method |Elements.unite_collectives| returns
        four:

        >>> elements.unite_collectives()
        Elements("B", "C", "e_a", "e_d")

        The returned elements `a` and `d` are the same as those defined initially, as
        they do not belong to any collectives:

        >>> collectives = elements.unite_collectives()
        >>> collectives.e_a is e_a
        True

        However, the elements `B` and `C` are new.  `B` replaces element `b`, and `C`
        replaces elements `c1` and `c2`.  Both handle instances of |sw1d_network|,
        which is the suitable model for connecting and applying the submodels of
        |sw1d_channel| (see |ModelCoupler|):

        >>> e_b, e_c = collectives.B, collectives.C
        >>> e_b.model.name
        'sw1d_network'

        The new element `B` has the same inlet and outlet nodes as `b`:

        >>> e_b
        Element("B",
                inlets="q_a_b",
                outlets="q_b_c1")

        However, `C` adopts both outlet nodes of `c1` and `c2` but only the inlet node
        of `c1`, which is relevant for clarifying the |HydPy.deviceorder| during
        simulations:

        >>> e_c
        Element("C",
                inlets="q_b_c1",
                outlets=["q_c1_c2", "q_c2_d"])

        The following technical checks ensure the underlying coupling mechanisms
        actually worked:

        >>> assert e_b.model.storagemodels.number == 1
        >>> assert e_c.model.storagemodels.number == 2
        >>> assert e_b.model.routingmodels.number == 2
        >>> assert e_c.model.routingmodels.number == 3
        >>> assert e_c.model.routingmodels[1].routingmodelsdownstream[0] is \
e_c.model.routingmodels[2]

        |Elements.unite_collectives| raises the following error if an element belonging
        to a collective does not handle a |Model| instance:

        >>> e_d.collective = "D"
        >>> elements.unite_collectives()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to unite the \
elements belonging to collective `D`, the following error occurred: The model object \
of element `e_d` has been requested but not been prepared so far.

        |Elements.unite_collectives| raises the following error if an element belonging
        to a collective does handle an unsuitable |Model| instance:

        >>> e_d.model = prepare_model("musk_classic")
        >>> elements.unite_collectives()
        Traceback (most recent call last):
        ...
        TypeError: While trying to unite the elements belonging to collective `D`, \
the following error occurred: Model `musk_classic` of element `e_d` does not provide \
a function for coupling models that belong to the same collective.

        .. testsetup::

            >>> del pub.timegrids
            >>> FusedVariable.clear_registry()
        """
        elements: list[Element] = []
        for collective, subelements in self.collectives.items():
            if collective is None:
                elements.extend(subelements)
            else:
                try:
                    outlets = set(
                        outlet
                        for subelement in subelements
                        for outlet in subelement.outlets
                    )
                    inlets = set(
                        inlet
                        for subelement in subelements
                        for inlet in subelement.inlets
                        if inlet not in outlets
                    )
                    outputs = set(
                        output
                        for subelement in subelements
                        for output in subelement.outputs
                    )
                    inputs = set(
                        input_
                        for subelement in subelements
                        for input_ in subelement.inputs
                        if input_ not in outputs
                    )
                    _registry[Element].pop(collective, None)
                    newelement = Element(
                        collective,
                        inlets=inlets,
                        outlets=outlets,
                        inputs=inputs,
                        outputs=outputs,
                    )
                    del _selection[Element][collective]
                    elements.append(newelement)
                    if (couple_models := subelements[0].model.couple_models) is None:
                        raise TypeError(
                            f"Model {objecttools.elementphrase(subelements[0].model)} "
                            f"does not provide a function for coupling models that "
                            f"belong to the same collective."
                        )
                    nodes = outlets.union(inlets).union(inputs).union(outputs)
                    newelement.model = couple_models(
                        nodes=Nodes(nodes), elements=Elements(subelements)
                    )
                    newelement.model.update_parameters()
                except BaseException:
                    objecttools.augment_excmessage(
                        f"While trying to unite the elements belonging to collective "
                        f"`{collective}`"
                    )
        return Elements(elements)

    @printtools.print_progress
    def prepare_models(self) -> None:
        """Call method |Element.prepare_model| of all handle |Element| objects.

        We show, based on the `HydPy-H-Lahn` example project, that method
        |Element.init_model| prepares the |Model| objects of all elements, including
        building the required connections and updating the derived parameters:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import attrready, HydPy, pub, TestIO
        >>> with TestIO():
        ...     hp = HydPy("HydPy-H-Lahn")
        ...     pub.timegrids = "1996-01-01", "1996-02-01", "1d"
        ...     hp.prepare_network()
        ...     hp.prepare_models()
        >>> hp.elements.land_dill_assl.model.parameters.derived.dt
        dt(0.000833)

        Wrong control files result in error messages like the following:

        >>> with TestIO():
        ...     with open("HydPy-H-Lahn/control/default/land_dill_assl.py",
        ...               "a") as file_:
        ...         _ = file_.write("zonetype(-1)")
        ...     hp.prepare_models()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: While trying to initialise the model object of element \
`land_dill_assl`, the following error occurred: While trying to load the control file \
`...land_dill_assl.py`, the following error occurred: At least one value of parameter \
`zonetype` of element `?` is not valid.

        By default, missing control files result in exceptions:

        >>> del hp.elements.land_dill_assl.model
        >>> import os
        >>> with TestIO():
        ...     os.remove("HydPy-H-Lahn/control/default/land_dill_assl.py")
        ...     hp.prepare_models()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        FileNotFoundError: While trying to initialise the model object of element \
`land_dill_assl`, the following error occurred: While trying to load the control file \
`...land_dill_assl.py`, the following error occurred: ...
        >>> attrready(hp.elements.land_dill_assl, "model")
        False

        When building new, still incomplete *HydPy* projects, this behaviour can be
        annoying.  After setting the option |Options.warnmissingcontrolfile| to
        |False|, missing control files result in a warning only:

        >>> with TestIO():
        ...     with pub.options.warnmissingcontrolfile(True):
        ...         hp.prepare_models()
        Traceback (most recent call last):
        ...
        UserWarning: Due to a missing or no accessible control file, no model could \
be initialised for element `land_dill_assl`
        >>> attrready(hp.elements.land_dill_assl, "model")
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
        hydpy.core.exceptiontools.HydPyDeprecationWarning: Method `init_models` of \
class `Elements` is deprecated.  Use method `prepare_models` instead.
        >>> mocked.call_args_list
        [call()]
        """
        self.prepare_models()
        warnings.warn(
            "Method `init_models` of class `Elements` is deprecated.  Use method "
            "`prepare_models` instead.",
            exceptiontools.HydPyDeprecationWarning,
        )

    @printtools.print_progress
    def save_controls(
        self,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        simulationstep: Optional[timetools.PeriodConstrArg] = None,
        auxfiler: Optional[auxfiletools.Auxfiler] = None,
    ) -> None:
        """Save the control parameters of the |Model| object handled by each |Element|
        object and eventually the ones handled by the given |Auxfiler| object."""
        if auxfiler:
            auxfiler.write(parameterstep=parameterstep, simulationstep=simulationstep)
        for element in printtools.progressbar(self):
            element.model.save_controls(
                parameterstep=parameterstep,
                simulationstep=simulationstep,
                auxfiler=auxfiler,
            )

    @printtools.print_progress
    def load_conditions(self) -> None:
        """Save the initial conditions of the |Model| object handled by each |Element|
        object."""
        for element in printtools.progressbar(self):
            element.model.load_conditions()

    @printtools.print_progress
    def save_conditions(self) -> None:
        """Save the calculated conditions of the |Model| object handled by each
        |Element| object."""
        for element in printtools.progressbar(self):
            element.model.save_conditions()

    def trim_conditions(self) -> None:
        """Call method |Model.trim_conditions| of the |Model| object handled by each
        |Element| object."""
        for element in self:
            element.model.trim_conditions()

    def reset_conditions(self) -> None:
        """Call method |Model.reset_conditions| of the |Model| object handled by each
        |Element| object."""
        for element in self:
            element.model.reset_conditions()

    @property
    def conditions(self) -> Conditions:
        """A nested dictionary that contains the values of all |ConditionSequence|
        objects of all currently handled models.

        See the documentation on property |HydPy.conditions| for further information.
        """
        return {element.name: element.model.conditions for element in self}

    @conditions.setter
    def conditions(self, conditions: Conditions) -> None:
        for name, subconditions in conditions.items():
            element = getattr(self, name)
            element.model.conditions = subconditions

    @printtools.print_progress
    def prepare_allseries(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |Element.prepare_allseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.prepare_allseries(allocate_ram=allocate_ram, jit=jit)

    @printtools.print_progress
    def prepare_inputseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |Element.prepare_inputseries| of all handled |Element|
        objects."""
        for element in printtools.progressbar(self):
            element.prepare_inputseries(
                allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
            )

    @printtools.print_progress
    def prepare_factorseries(
        self, allocate_ram: bool = True, write_jit: bool = False
    ) -> None:
        """Call method |Element.prepare_factorseries| of all handled |Element|
        objects."""
        for element in printtools.progressbar(self):
            element.prepare_factorseries(allocate_ram=allocate_ram, write_jit=write_jit)

    @printtools.print_progress
    def prepare_fluxseries(
        self, allocate_ram: bool = True, write_jit: bool = False
    ) -> None:
        """Call method |Element.prepare_fluxseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.prepare_fluxseries(allocate_ram=allocate_ram, write_jit=write_jit)

    @printtools.print_progress
    def prepare_stateseries(
        self, allocate_ram: bool = True, write_jit: bool = False
    ) -> None:
        """Call method |Element.prepare_stateseries| of all handled |Element|
        objects."""
        for element in printtools.progressbar(self):
            element.prepare_stateseries(allocate_ram=allocate_ram, write_jit=write_jit)

    @printtools.print_progress
    def load_allseries(self) -> None:
        """Call method |Element.load_inputseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.load_allseries()

    @printtools.print_progress
    def load_inputseries(self) -> None:
        """Call method |Element.load_inputseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.load_inputseries()

    @printtools.print_progress
    def load_factorseries(self) -> None:
        """Call method |Element.load_factorseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.load_factorseries()

    @printtools.print_progress
    def load_fluxseries(self) -> None:
        """Call method |Element.load_fluxseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.load_fluxseries()

    @printtools.print_progress
    def load_stateseries(self) -> None:
        """Call method |Element.load_stateseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.load_stateseries()

    @printtools.print_progress
    def save_allseries(self) -> None:
        """Call method |Element.save_allseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.save_allseries()

    @printtools.print_progress
    def save_inputseries(self) -> None:
        """Call method |Element.save_inputseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.save_inputseries()

    @printtools.print_progress
    def save_factorseries(self) -> None:
        """Call method |Element.save_factorseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.save_factorseries()

    @printtools.print_progress
    def save_fluxseries(self) -> None:
        """Call method |Element.save_fluxseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.save_fluxseries()

    @printtools.print_progress
    def save_stateseries(self) -> None:
        """Call method |Element.save_stateseries| of all handled |Element| objects."""
        for element in printtools.progressbar(self):
            element.save_stateseries()


class Device:
    """Base class for class |Element| and class |Node|."""

    _name: str
    _keywords: Keywords

    def __new__(
        cls, value: Union[Device, str], *args: object, **kwargs: object
    ) -> Device:
        # pylint: disable=unused-argument
        # required for consistincy with __init__
        name = str(value)
        cls.__check_name(name)
        try:
            self = _registry[cls][name]
        except KeyError:
            self = object.__new__(cls)
            self._name = name
            setattr(self, "new_instance", True)
            self._keywords = Keywords()
            self._keywords.device = self
            _id2devices[self] = {}
            _registry[cls][name] = self
        _selection[cls][name] = _registry[cls][name]
        return self

    @classmethod
    @abc.abstractmethod
    def get_handlerclass(cls) -> type[Devices[Any]]:
        """To be overridden."""

    @classmethod
    def query_all(cls) -> Devices[Self]:
        """Get all |Node| or |Element| objects initialised so far.

        See the main documentation on module |devicetools| for further information.
        """
        return cls.get_handlerclass()(*_registry[cls].values())

    @classmethod
    def extract_new(cls) -> Devices[Self]:
        """Gather all "new" |Node| or |Element| objects.

        See the main documentation on module |devicetools| for further information.
        """
        devices = cls.get_handlerclass()(*_selection[cls])
        _selection[cls].clear()
        return devices

    @classmethod
    def clear_all(cls) -> None:
        """Clear the registry from all initialised |Node| or |Element| objects.

        See the main documentation on module |devicetools| for further information.
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
        ValueError: While trying to initialize a `Node` object with value `n 3` of \
type `str`, the following error occurred: The given name string `n 3` does not define \
a valid variable identifier.  ...

        When you change the name of a device (only do this for a good reason), the
        corresponding keys of all related |Nodes| and |Elements| objects (as well as of
        the internal registry) change automatically:

        >>> Node.query_all()
        Nodes("n1", "n2")
        >>> node1.name = "n1a"
        >>> nodes
        Nodes("n1a", "n2")
        >>> Node.query_all()
        Nodes("n1a", "n2")
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self.__check_name(name)
        for devices in tuple(_id2devices[self].values()):
            if hasattr(devices, self.name):
                del devices._name2device[self.name]  # pylint: disable=protected-access
        del _registry[type(self)][self.name]
        self._name = name
        _registry[type(self)][self.name] = self
        for devices in tuple(_id2devices[self].values()):
            devices._name2device[self.name] = self  # pylint: disable=protected-access

    @classmethod
    def __check_name(cls, name: str) -> None:
        try:
            objecttools.valid_variable_identifier(name)
        except ValueError:
            objecttools.augment_excmessage(
                f"While trying to initialize a `{cls.__name__}` object with value "
                f"`{name}` of type `{type(name).__name__}`"
            )

    def _get_keywords(self) -> Keywords:
        """Keywords describing the actual |Node| or |Element| object.

        The keywords are contained within a |Keywords| object:

        >>> from hydpy import Node
        >>> node = Node("n", keywords="word0")
        >>> node.keywords
        Keywords("word0")

        Assigning new words does not overwrite already existing ones.  You are allowed
        to add them individually or within iterable objects:

        >>> node.keywords = "word1"
        >>> node.keywords = "word2", "word3"
        >>> node.keywords
        Keywords("word0", "word1", "word2", "word3")

        Additionally, passing additional keywords to the constructor of class |Node| or
        |Element| works also fine:

        >>> Node("n", keywords=("word3", "word4", "word5"))
        Node("n", variable="Q",
             keywords=["word0", "word1", "word2", "word3", "word4", "word5"])

        You can delete all keywords at once:

        >>> del node.keywords
        >>> node.keywords
        Keywords()
        """
        return self._keywords

    def _set_keywords(self, keywords: MayNonerable1[str]) -> None:
        keywords = tuple(objecttools.extract(keywords, (str,), True))
        self._keywords.update(*keywords)

    def _del_keywords(self) -> None:
        self._keywords.clear()

    keywords = propertytools.Property(
        fget=_get_keywords, fset=_set_keywords, fdel=_del_keywords
    )

    def __str__(self) -> str:
        return self.name


class Node(Device):
    """Handles the data flow between |Element| objects.

    |Node| objects always handle two sequences, a |Sim| object for simulated values and
    an |Obs| object for measured values:

    >>> from hydpy import Node
    >>> node = Node("test")
    >>> for sequence in node.sequences:
    ...     print(sequence)
    sim(0.0)
    obs(0.0)

    Each node can handle an arbitrary number of "input" and "output" elements,
    available as instance attributes `entries` and `exits`, respectively:

    >>> node.entries
    Elements()
    >>> node.exits
    Elements()

    You cannot (or at least should not) add new elements manually:

    >>> node.entries = "element"  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    AttributeError: ...
    >>> node.exits.add_device("element")
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add the device `element` to a Elements object, the \
following error occurred: Adding devices to immutable Elements objects is not allowed.

    Instead, see the documentation on class |Element| on how to connect |Node| and
    |Element| objects properly.
    """

    masks = masktools.NodeMasks()
    sequences: sequencetools.NodeSequences

    _entries: Elements
    _exits: Elements
    _variable: NodeVariableType
    _deploymode: DeployMode

    def __init__(
        self,
        value: NodeConstrArg,
        variable: Optional[NodeVariableType] = None,
        keywords: MayNonerable1[str] = None,
    ) -> None:
        # pylint: disable=unused-argument
        # required for consistincy with Device.__new__
        if hasattr(self, "new_instance"):
            if variable is None:
                self._variable = _default_variable
            else:
                self._variable = variable
            self._entries = Elements(None, mutable=False)
            self._exits = Elements(None, mutable=False)
            self.sequences = sequencetools.NodeSequences(self)
            self._deploymode = "newsim"
            self.__blackhole = pointerutils.Double(0.0)
            delattr(self, "new_instance")
        if (variable is not None) and (variable != self.variable):
            raise ValueError(
                f"The variable to be represented by a {type(self).__name__} instance "
                f"cannot be changed.  The variable of node `{self.name}` is "
                f"`{self.variable}` instead of `{variable}`.  Keep in mind, that "
                f"`name` is the unique identifier of node objects."
            )
        if keywords is not None:
            self.keywords = keywords

    @classmethod
    def get_handlerclass(cls) -> type[Nodes]:
        """Return class |Nodes|."""
        return Nodes

    @property
    def entries(self) -> Elements:
        """Group of |Element| objects which set the the simulated value of the |Node|
        object."""
        return self._entries

    @property
    def exits(self) -> Elements:
        """Group of |Element| objects that query the simulated or observed value of
        the actual |Node| object."""
        return self._exits

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
        Node("test3", variable=hland_inputs_T)

        The last example above shows that the string representations of nodes handling
        "class variables" use the aliases importable from the top level of the *HydPy*
        package:

        >>> from hydpy.aliases import hland_inputs_P
        >>> Node("test4", variable=hland_inputs_P)
        Node("test4", variable=hland_inputs_P)

        For some complex *HydPy* projects, one may need to fall back on |FusedVariable|
        objects.  The string representation then relies on the name of the fused
        variable:

        >>> from hydpy import FusedVariable
        >>> from hydpy.aliases import lland_inputs_Nied
        >>> Precipitation = FusedVariable("Precip", hland_inputs_P, lland_inputs_Nied)
        >>> Node("test5", variable=Precipitation)
        Node("test5", variable=Precip)

        To avoid confusion, one cannot change |Node.variable|:

        >>> node.variable = "H"  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: ...
        >>> Node("test1", variable="H")
        Traceback (most recent call last):
        ...
        ValueError: The variable to be represented by a Node instance cannot be \
changed.  The variable of node `test1` is `Q` instead of `H`.  Keep in mind, that \
`name` is the unique identifier of node objects.
        """
        return self._variable

    @property
    def deploymode(self) -> DeployMode:
        """Defines the kind of information a node offers its exit elements, eventually,
        its entry elements.

        *HydPy* supports the following modes:

          * newsim: Deploy the simulated values calculated just recently.  `newsim` is
            the default mode, used, for example, when a node receives a discharge value
            from an upstream element and passes it to the downstream element directly.
          * obs: Deploy observed values instead of simulated values.  The node still
            receives the simulated values from its upstream element(s).  However, it
            deploys values to its downstream element(s), which are defined externally.
            Usually, these values are observations made available within a time series
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
          * obs_bi: Similar to the `obs` mode but triggers "bidirectional" deployment.
            All bidirectional modes only apply if the upstream element(s) do not
            calculate data for but expect from their downstream nodes.  A typical
            example is using discharge measurements as lower boundary conditions for a
            hydrodynamical flood routing method.
          * oldsim_bi: The bidirectional version of the `oldsim` mode.
          * obs_oldsim_bi: The bidirectional version of the `obs_oldsim` mode.

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
        >>> node.deploymode = "oldsim_bi"
        >>> node.deploymode
        'oldsim_bi'
        >>> node.deploymode = "obs_bi"
        >>> node.deploymode
        'obs_bi'
        >>> node.deploymode = "obs_oldsim_bi"
        >>> node.deploymode
        'obs_oldsim_bi'
        >>> node.deploymode = "newsim"
        >>> node.deploymode
        'newsim'
        >>> node.deploymode = "oldobs"
        Traceback (most recent call last):
        ...
        ValueError: When trying to set the routing mode of node `test`, the value \
`oldobs` was given, but only the following values are allowed: `newsim`, `oldsim`, \
`obs`, `obs_newsim`, `obs_oldsim`, `obs_bi.`, `oldsim_bi`, and `obs_oldsim_bi`.
        """
        return self._deploymode

    @deploymode.setter
    def deploymode(self, value: DeployMode) -> None:
        def _assert_never(v: Never) -> NoReturn:
            raise ValueError(
                f"When trying to set the routing mode of node `{self.name}`, the "
                f"value `{value}` was given, but only the following values are "
                f"allowed: `newsim`, `oldsim`, `obs`, `obs_newsim`, `obs_oldsim`, "
                f"`obs_bi.`, `oldsim_bi`, and `obs_oldsim_bi`."
            )

        # due to https://github.com/python/mypy/issues/9718:
        # pylint: disable=consider-using-in,too-many-boolean-expressions

        if (
            value == "newsim"
            or value == "obs"
            or value == "obs_newsim"
            or value == "obs_bi"
            or value == "oldsim_bi"
            or value == "obs_oldsim_bi"
        ):
            pass
        elif value == "oldsim" or value == "obs_oldsim":
            self.__blackhole = pointerutils.Double(0.0)
        else:
            _assert_never(value)
        self._deploymode = value
        for element in itertools.chain(self.entries, self.exits):
            model: Optional[modeltools.Model]
            model = exceptiontools.getattr_(element, "model", None)
            if model and not model.COMPOSITE:
                model.connect()

    def get_double(
        self,
        group: Literal[
            "inlets", "receivers", "inputs", "outlets", "senders", "outputs"
        ],
    ) -> pointerutils.Double:
        """Return the |Double| object appropriate for the given |Element| input or
        output group and the actual |Node.deploymode|.

        Method |Node.get_double| should interest framework developers only (and
        eventually model developers).

        Let |Node| object `node1` handle different simulation and observation values:

        >>> from hydpy import Node
        >>> node = Node("node1")
        >>> node.sequences.sim = 1.0
        >>> node.sequences.obs = 2.0

        The following `test` function shows for a given |Node.deploymode| if method
        |Node.get_double| either returns the |Double| object handling the simulated
        value (1.0) or the one handling the observed value (2.0):

        >>> def test(deploymode):
        ...     node.deploymode = deploymode
        ...     for group in ( "inlets", "receivers", "inputs"):
        ...         end = None if group == "inputs" else ", "
        ...         print(group, node.get_double(group), sep=": ", end=end)
        ...     for group in ("outlets", "senders", "outputs"):
        ...         end = None if group == "outputs" else ", "
        ...         print(group, node.get_double(group), sep=": ", end=end)

        In the default mode, nodes (passively) route simulated values by offering the
        |Double| object of sequence |Sim| to all |Element| input and output groups:

        >>> test("newsim")
        inlets: 1.0, receivers: 1.0, inputs: 1.0
        outlets: 1.0, senders: 1.0, outputs: 1.0

        Setting |Node.deploymode| to `obs` means that a node receives simulated values
        (from group `outlets` or `senders`) but provides observed values (to group
        `inlets` or `receivers`):

        >>> test("obs")
        inlets: 2.0, receivers: 2.0, inputs: 2.0
        outlets: 1.0, senders: 1.0, outputs: 1.0

        With |Node.deploymode| set to `oldsim`, the node provides (previously)
        simulated values (to group `inlets`, `receivers`, or `inputs`) but does not
        receive any.  Method |Node.get_double| returns a dummy |Double| object
        initialised to 0.0 in this case (for group `outlets`, `senders`, or `outputs`):

        >>> test("oldsim")
        inlets: 1.0, receivers: 1.0, inputs: 1.0
        outlets: 0.0, senders: 0.0, outputs: 0.0

        For `obs_newsim`, the result is like for `obs` because, for missing data,
        *HydPy* temporarily copies newly calculated values into the observation
        sequence during simulation:

        >>> test("obs_newsim")
        inlets: 2.0, receivers: 2.0, inputs: 2.0
        outlets: 1.0, senders: 1.0, outputs: 1.0

        Similar holds for the `obs_oldsim` mode, but here |Node.get_double| must ensure
        newly calculated values do not overwrite the "old" ones:

        >>> test("obs_oldsim")
        inlets: 2.0, receivers: 2.0, inputs: 2.0
        outlets: 0.0, senders: 0.0, outputs: 0.0

        All "bidirectional" modes require symmetrical connections, as they long for
        passing the same information in the downstream and the upstream direction:

        >>> test("obs_bi")
        inlets: 2.0, receivers: 2.0, inputs: 2.0
        outlets: 2.0, senders: 2.0, outputs: 2.0
        >>> test("oldsim_bi")
        inlets: 1.0, receivers: 1.0, inputs: 1.0
        outlets: 1.0, senders: 1.0, outputs: 1.0
        >>> test("obs_oldsim_bi")
        inlets: 2.0, receivers: 2.0, inputs: 2.0
        outlets: 2.0, senders: 2.0, outputs: 2.0

        Other |Element| input or output groups are not supported:

        >>> node.get_double("test")
        Traceback (most recent call last):
        ...
        ValueError: Function `get_double` of class `Node` does not support the given \
group name `test`.
        """
        # pylint: disable=consider-using-in

        dm = self.deploymode

        if group in ("inlets", "receivers", "inputs"):
            if dm == "newsim" or dm == "oldsim" or dm == "oldsim_bi":
                return self.sequences.fastaccess.sim
            if (
                dm == "obs"
                or dm == "obs_newsim"
                or dm == "obs_oldsim"
                or dm == "obs_bi"
                or dm == "obs_oldsim_bi"
            ):
                return self.sequences.fastaccess.obs
            assert_never(dm)

        if group in ("outlets", "senders", "outputs"):
            if dm == "newsim" or dm == "obs" or dm == "obs_newsim" or dm == "oldsim_bi":
                return self.sequences.fastaccess.sim
            if dm == "obs_bi" or dm == "obs_oldsim_bi":
                return self.sequences.fastaccess.obs
            if dm == "oldsim" or dm == "obs_oldsim":
                return self.__blackhole
            assert_never(dm)

        raise ValueError(
            f"Function `get_double` of class `Node` does not support the given group "
            f"name `{group}`."
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

    def prepare_allseries(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |Node.prepare_simseries| with `write_jit=jit` and method
        |Node.prepare_obsseries| with `read_jit=jit`."""
        self.prepare_simseries(allocate_ram=allocate_ram, write_jit=jit)
        self.prepare_obsseries(allocate_ram=allocate_ram, read_jit=jit)

    def prepare_simseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of the |Sim| sequence object."""
        self.sequences.sim.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def prepare_obsseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of the |Obs| sequence object."""
        self.sequences.obs.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def plot_allseries(
        self,
        *,
        labels: Optional[tuple[str, str]] = None,
        colors: Optional[Union[str, tuple[str, str]]] = None,
        linestyles: Optional[Union[LineStyle, tuple[LineStyle, LineStyle]]] = None,
        linewidths: Optional[Union[int, tuple[int, int]]] = None,
        focus: bool = False,
        stepsize: Optional[StepSize] = None,
    ) -> pyplot.Figure:
        """Plot the |IOSequence.series| data of both the |Sim| and the |Obs| sequence
        object.

        We demonstrate the functionalities of method |Node.plot_allseries| based on the
        `Lahn` example project:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2(lastdate="1997-01-01")

        We perform a simulation run and calculate "observed" values for node
        `dill_assl`:

        >>> hp.simulate()
        >>> dill_assl = hp.nodes.dill_assl
        >>> dill_assl.sequences.obs.series = dill_assl.sequences.sim.series + 10.0

        A call to method |Node.plot_allseries| prints the time series of both sequences
        to the screen immediately (if not, you need to activate the interactive mode of
        `matplotlib` first):

        >>> figure = dill_assl.plot_allseries()

        Subsequent calls to |Node.plot_allseries| or the related methods
        |Node.plot_simseries| and |Node.plot_obsseries| of nodes add further time
        series data to the existing plot:

        >>> lahn_marb = hp.nodes.lahn_marb
        >>> figure = lahn_marb.plot_simseries()

        You can modify the appearance of the lines by passing different arguments:

        >>> lahn_marb.sequences.obs.series = lahn_marb.sequences.sim.series + 10.0
        >>> figure = lahn_marb.plot_obsseries(color="black", linestyle="dashed")

        All mentioned plotting functions return a |matplotlib| |figure.Figure| object.
        Use it for further plot handling, e.g. adding a title and saving the current
        figure to disk:

        >>> from hydpy.core.testtools import save_autofig
        >>> text = figure.axes[0].set_title('daily')
        >>> save_autofig("Node_plot_allseries_1.png", figure)

        .. image:: Node_plot_allseries_1.png

        You can plot the data in an aggregated manner (see the documentation on the
        function |aggregate_series| for the supported step sizes and further details):

        >>> figure = dill_assl.plot_allseries(stepsize="monthly")
        >>> text = figure.axes[0].set_title('monthly')
        >>> save_autofig("Node_plot_allseries_2.png", figure)

        .. image:: Node_plot_allseries_2.png

        You can restrict the plotted period via the |Timegrids.eval_| |Timegrid| and
        overwrite the time series label and other defaults via keyword arguments.
        For tuples passed to method |Node.plot_allseries|, the first entry corresponds
        to the observation and the second one to the simulation results:

        >>> pub.timegrids.eval_.dates = "1996-10-01", "1996-11-01"
        >>> figure = lahn_marb.plot_allseries(labels=("measured", "calculated"),
        ...                                colors=("blue", "red"),
        ...                                linewidths=2,
        ...                                linestyles=("--", ":"),
        ...                                focus=True,)
        >>> save_autofig("Node_plot_allseries_3.png", figure)

        .. image:: Node_plot_allseries_3.png

        When necessary, all plotting methods raise errors like the following:

        >>> figure = lahn_marb.plot_allseries(stepsize="quaterly")
        Traceback (most recent call last):
        ...
        ValueError: While trying to plot the time series of sequence(s) obs and sim \
of node `lahn_marb` for the period `1996-10-01 00:00:00` to `1996-11-01 00:00:00`, the \
following error occurred: While trying to aggregate the given series, the following \
error occurred: Argument `stepsize` received value `quaterly`, but only the following \
ones are supported: `monthly` (default) and `daily`.

        >>> from hydpy import pub
        >>> del pub.timegrids
        >>> figure = lahn_marb.plot_allseries()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to plot the time \
series of sequence(s) obs and sim of node `lahn_marb` , the following error occurred: \
Attribute timegrids of module `pub` is not defined at the moment.
        """

        t = TypeVar("t", str, int)

        def _make_tuple(
            x: Union[Optional[t], tuple[Optional[t], Optional[t]]]
        ) -> tuple[Optional[t], Optional[t]]:
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
    ) -> pyplot.Figure:
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
    ) -> pyplot.Figure:
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
    ) -> pyplot.Figure:
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
                        series=sequence.series, stepsize=stepsize, aggregator=numpy.mean
                    )
                    period = "15d" if stepsize.startswith("m") else "12h"
                    ps.index += timetools.Period(period).timedelta
                    ps = ps.rename(columns={"series": label_})
                kwargs = {"label": label_, "ax": pyplot.gca()}
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
                if (variable := str(self.variable)) == "Q":
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
            variable = f"{variable.__module__.split('.')[-1]}_{variable.__name__}"
        lines = [f'{prefix}Node("{self.name}", variable={variable},']
        if self.keywords:
            subprefix = f'{" "*(len(prefix)+5)}keywords='
            with objecttools.repr_.preserve_strings(True):
                with objecttools.assignrepr_tuple.always_bracketed(False):
                    line = objecttools.assignrepr_list(
                        values=sorted(self.keywords), prefix=subprefix, width=70
                    )
            lines.append(line + ",")
        lines[-1] = lines[-1][:-1] + ")"
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.assignrepr()


class Element(Device):
    """Handles a |Model| object and connects it to other models via
    |Node| objects.

    When preparing |Element| objects, one links them to nodes of different "groups",
    each group of nodes implemented as an immutable |Nodes| object:

     * |Element.inlets| and |Element.outlets| nodes handle, for example, the inflow to
       and the outflow from the respective element.
     * |Element.receivers| and |Element.senders| nodes are thought for information flow
       between arbitrary elements, for example, to inform a |dam| model about the
       discharge at a gauge downstream.
     * |Element.inputs| nodes provide optional input information, for example,
       interpolated precipitation that could alternatively be read from files as well.
     * |Element.outputs| nodes query optional output information, for example, the
       water level of a dam.

    You can select the relevant nodes either by passing them explicitly or passing
    their name both as single objects or as objects contained within an iterable
    object:

    >>> from hydpy import Element, Node
    >>> Element("test",
    ...         inlets="inl1",
    ...         outlets=Node("outl1"),
    ...         receivers=("rec1", Node("rec2")))
    Element("test",
            inlets="inl1",
            outlets="outl1",
            receivers=["rec1", "rec2"])

    Repeating such a statement with different nodes adds them to the existing ones
    without any conflict in case of repeated specifications:

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

    The properties try to verify that all connections make sense.  For example, an
    element should never handle an `inlet` node that it also handles as an `outlet`,
    `input`, or `output` node:

    >>> test.inlets = "outl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `outl1` is already defined \
as a(n) outlet node, which is not allowed.

    >>> test.inlets = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `inp1` is already defined as \
a(n) input node, which is not allowed.

    >>> test.inlets = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `outp1` is already defined \
as a(n) output node, which is not allowed.

    Similar holds for the `outlet` nodes:

    >>> test.outlets = "inl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `inl1` is already defined \
as a(n) inlet node, which is not allowed.

    >>> test.outlets = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `inp1` is already defined \
as a(n) input node, which is not allowed.

    >>> test.outlets = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `outp1` is already defined \
as a(n) output node, which is not allowed.

    The following restrictions hold for the `sender` nodes:

    >>> test.senders = "rec1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `rec1` is already defined \
as a(n) receiver node, which is not allowed.

    >>> test.senders = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `inp1` is already defined \
as a(n) input node, which is not allowed.

    >>> test.senders = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `outp1` is already defined \
as a(n) output node, which is not allowed.

    The following restrictions hold for the `receiver` nodes:

    >>> test.receivers = "sen1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `sen1` is already defined \
as a(n) sender node, which is not allowed.

    >>> test.receivers = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `inp1` is already defined \
as a(n) input node, which is not allowed.

    >>> test.receivers = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `outp1` is already \
defined as a(n) output node, which is not allowed.

    The following restrictions hold for the `input` nodes:

    >>> test.inputs = "outp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `outp1` is already defined \
as a(n) output node, which is not allowed.

    >>> test.inputs = "inl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `inl1` is already defined as \
a(n) inlet node, which is not allowed.

    >>> test.inputs = "outl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `outl1` is already defined \
as a(n) outlet node, which is not allowed.

    >>> test.inputs = "sen1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `sen1` is already defined as \
a(n) sender node, which is not allowed.

    >>> test.inputs = "rec1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given input node `rec1` is already defined as \
a(n) receiver node, which is not allowed.

   The following restrictions hold for the `output` nodes:

    >>> test.outputs = "inp1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `inp1` is already defined \
as a(n) input node, which is not allowed.

    >>> test.outputs = "inl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `inl1` is already defined \
as a(n) inlet node, which is not allowed.

    >>> test.outputs = "outl1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `outl1` is already defined \
as a(n) outlet node, which is not allowed.

    >>> test.outputs = "sen1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `sen1` is already defined \
as a(n) sender node, which is not allowed.

    >>> test.outputs = "rec1"
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given output node `rec1` is already defined \
as a(n) receiver node, which is not allowed.

    Note that the discussed |Nodes| objects are immutable by default, disallowing to
    change them in other ways as described above:

    >>> test.inlets += "inl3"
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add the device `inl3` to a Nodes object, the \
following error occurred: Adding devices to immutable Nodes objects is not allowed.

    Use the parameter `force` to change this behaviour:

    >>> test.inlets.add_device("inl3", force=True)

    However, it is up to you to make sure that the added node also handles the relevant
    element in the suitable group.  In the discussed example, only node `inl2` has been
    added properly but not node `inl3`:

    >>> test.inlets.inl2.exits
    Elements("test")
    >>> test.inlets.inl3.exits
    Elements()

    Some elements might belong to a |Element.collective|, which is a group of elements
    requiring simultaneous handling during simulation (see method
    |Elements.unite_collectives|).  If needed, specify the collective's name by the
    corresponding argument:

    >>> Element("part_1", collective="NileRiver", inlets="inl1")
    Element("part_1",
            collective="NileRiver",
            inlets="inl1")

    The information persists when querying the same element from the internal registry,
    whether one specifies the collective's name again or not:

    >>> Element("part_1", collective="NileRiver")
    Element("part_1",
            collective="NileRiver",
            inlets="inl1")

    >>> Element("part_1")
    Element("part_1",
            collective="NileRiver",
            inlets="inl1")

    However, changing the collective via the constructor is forbidden as it might
    result in hard-to-find configuration errors:

    >>> Element("part_1", collective="AmazonRiver")
    Traceback (most recent call last):
    ...
    RuntimeError: The collective name `AmazonRiver` is given, but element `part_1` is \
already a collective `NileRiver` member.
    """

    collective: Optional[str] = None
    """The collective the actual |Element| instance belongs to."""

    _inlets: Nodes
    _outlets: Nodes
    _receivers: Nodes
    _senders: Nodes
    _inputs: Nodes
    _outputs: Nodes
    _model: Optional[modeltools.Model]

    def __init__(
        self,
        value: ElementConstrArg,
        *,
        inlets: NodesConstrArg = None,
        outlets: NodesConstrArg = None,
        receivers: NodesConstrArg = None,
        senders: NodesConstrArg = None,
        inputs: NodesConstrArg = None,
        outputs: NodesConstrArg = None,
        collective: Optional[str] = None,
        keywords: MayNonerable1[str] = None,
    ) -> None:
        # pylint: disable=unused-argument
        # required for consistincy with Device.__new__
        if collective is not None:
            if (col := self.collective) is None:
                self.collective = collective
            elif col != collective:
                raise RuntimeError(
                    f"The collective name `{collective}` is given, but element "
                    f"`{self.name}` is already a collective `{col}` member."
                )
        if hasattr(self, "new_instance"):
            self._inlets = Nodes(mutable=False)
            self._outlets = Nodes(mutable=False)
            self._receivers = Nodes(mutable=False)
            self._senders = Nodes(mutable=False)
            self._inputs = Nodes(mutable=False)
            self._outputs = Nodes(mutable=False)
            self.__connections = (
                self.inlets,
                self.outlets,
                self.receivers,
                self.senders,
                self.inputs,
                self.outputs,
            )
            self._model = None
            delattr(self, "new_instance")
        self.keywords = keywords
        if inlets is not None:
            self.inlets = inlets
        if outlets is not None:
            self.outlets = outlets
        if receivers is not None:
            self.receivers = receivers
        if senders is not None:
            self.senders = senders
        if inputs is not None:
            self.inputs = inputs
        if outputs is not None:
            self.outputs = outputs
        # due to internal type conversion
        # see issue https://github.com/python/mypy/issues/3004

    def __update_group(
        self,
        values: NodesConstrArg,
        targetnodes: str,
        targetelements: str,
        incompatiblenodes: tuple[str, ...],
    ) -> None:
        elementgroup: Nodes = getattr(self, targetnodes)
        for node in Nodes(values):
            for incomp in incompatiblenodes:
                if node in getattr(self, incomp):
                    raise ValueError(
                        f"For element `{self}`, the given {targetnodes[1:-1]} "
                        f"node `{node}` is already defined as a(n) {incomp[1:-1]} "
                        f"node, which is not allowed."
                    )
            elementgroup.add_device(node, force=True)
            nodegroup: Elements = getattr(node, targetelements)
            nodegroup.add_device(self, force=True)

    def _get_inlets(self) -> Nodes:
        """Group of |Node| objects from which the handled |Model| object queries its
        "upstream" input values (e.g. inflow)."""
        return self._inlets

    def _set_inlets(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="_inlets",
            targetelements="_exits",
            incompatiblenodes=("_outlets", "_inputs", "_outputs"),
        )

    inlets = propertytools.Property(fget=_get_inlets, fset=_set_inlets)

    def _get_outlets(self) -> Nodes:
        """Group of |Node| objects to which the handled |Model| object passes its
        "downstream" output values (e.g. outflow)."""
        return self._outlets

    def _set_outlets(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="_outlets",
            targetelements="_entries",
            incompatiblenodes=("_inlets", "_inputs", "_outputs"),
        )

    outlets = propertytools.Property(fget=_get_outlets, fset=_set_outlets)

    def _get_receivers(self) -> Nodes:
        """Group of |Node| objects from which the handled |Model| object queries its
        "remote" information values (e.g. discharge at a remote downstream)."""
        return self._receivers

    def _set_receivers(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="_receivers",
            targetelements="_exits",
            incompatiblenodes=("_senders", "_inputs", "_outputs"),
        )

    receivers = propertytools.Property(fget=_get_receivers, fset=_set_receivers)

    def _get_senders(self) -> Nodes:
        """Group of |Node| objects to which the handled |Model| object passes its
        "remote" information values (e.g. water level of a |dam| model)."""
        return self._senders

    def _set_senders(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="_senders",
            targetelements="_entries",
            incompatiblenodes=("_receivers", "_inputs", "_outputs"),
        )

    senders = propertytools.Property(fget=_get_senders, fset=_set_senders)

    def _get_inputs(self) -> Nodes:
        """Group of |Node| objects from which the handled |Model| object queries its
        "external" input values instead of reading them from files (e.g. interpolated
        precipitation)."""
        return self._inputs

    def _set_inputs(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="_inputs",
            targetelements="_exits",
            incompatiblenodes=(
                "_inlets",
                "_outlets",
                "_senders",
                "_receivers",
                "_outputs",
            ),
        )

    inputs = propertytools.Property(fget=_get_inputs, fset=_set_inputs)

    def _get_outputs(self) -> Nodes:
        """Group of |Node| objects to which the handled |Model| object passes its
        "internal" output values, available via sequences of type |FluxSequence| or
        |StateSequence| (e.g. potential evaporation)."""
        return self._outputs

    def _set_outputs(self, values: NodesConstrArg) -> None:
        self.__update_group(
            values,
            targetnodes="_outputs",
            targetelements="_entries",
            incompatiblenodes=(
                "_inlets",
                "_outlets",
                "_senders",
                "_receivers",
                "_inputs",
            ),
        )

    outputs = propertytools.Property(fget=_get_outputs, fset=_set_outputs)

    @classmethod
    def get_handlerclass(cls) -> type[Elements]:
        """Return class |Elements|."""
        return Elements

    @property
    def model(self) -> modeltools.Model:
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

        >>> from hydpy.models.hland_96 import *
        >>> parameterstep("1d")
        >>> hland.model = model
        >>> hland.model.name
        'hland_96'

        >>> del hland.model
        >>> attrready(hland, "model")
        False

        For the "usual" approach to preparing models, please see the method
        |Element.prepare_model|.

        The following examples show that assigning |Model| objects to property
        |Element.model| creates some connection required by the respective model type
        automatically.  These examples should be relevant for developers only.

        The following |exch_branch_hbv96| model branches a single input value (from to
        node `inp`) to multiple outputs (nodes `out1` and `out2`):

        >>> from hydpy import Element, Node, reverse_model_wildcard_import, pub
        >>> reverse_model_wildcard_import()
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> element = Element("a_branch",
        ...                   inlets="branch_input",
        ...                   outlets=("branch_output_1", "branch_output_2"))
        >>> inp = element.inlets.branch_input
        >>> out1, out2 = element.outlets
        >>> from hydpy.models.exch_branch_hbv96 import *
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
        model = self._model
        if model:
            return model
        raise exceptiontools.AttributeNotReady(
            f"The model object of element `{self.name}` has been requested but not "
            f"been prepared so far."
        )

    @model.setter
    def model(self, model: modeltools.Model) -> None:
        self._model = model
        if exceptiontools.getattr_(model, "element", None) is not self:
            model.element = self
        if not model.COMPOSITE:
            for submodel in model.find_submodels().values():
                submodel.__hydpy_element__ = self
            model.connect()

    @model.deleter
    def model(self) -> None:
        if (model := self._model) is not None:
            self._model = None
            if exceptiontools.getattr_(model, "element", None) is self:
                del model.element

    def prepare_model(self, clear_registry: bool = True) -> None:
        """Load the control file of the actual |Element| object, initialise its |Model|
        object, build the required connections via (an eventually overridden version
        of) method |Model.connect| of class |Model|, and update its  derived parameter
        values via calling (an eventually overridden version) of method
        |Parameters.update| of class |Parameters|.

        See method |HydPy.prepare_models| of class |HydPy| and property |model| of
        class |Element| fur further information.
        """
        options = hydpy.pub.options
        try:
            try:
                hydpy.pub.timegrids
            except exceptiontools.AttributeNotReady:
                raise exceptiontools.AttributeNotReady(
                    "The initialisation period has not been defined via attribute "
                    "`timegrids` of module `pub` yet but might be required to prepare "
                    "the model properly."
                ) from None
            with options.warnsimulationstep(False):
                info = hydpy.pub.controlmanager.load_file(
                    element=self, clear_registry=clear_registry
                )
                self.model = info["model"]
                self.model.parameters.update()
        except OSError:
            if options.warnmissingcontrolfile:
                warnings.warn(
                    f"Due to a missing or no accessible control file, no model could "
                    f"be initialised for element `{self.name}`"
                )
            else:
                objecttools.augment_excmessage(
                    f"While trying to initialise the model object of element "
                    f"`{self.name}`"
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise the model object of element `{self.name}`"
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
        hydpy.core.exceptiontools.HydPyDeprecationWarning: Method `init_model` of \
class `Element` is deprecated.  Use method `prepare_model` instead.
        >>> mocked.call_args_list
        [call(False)]
        """
        self.prepare_model(clear_registry)
        warnings.warn(
            "Method `init_model` of class `Element` is deprecated.  Use method "
            "`prepare_model` instead.",
            exceptiontools.HydPyDeprecationWarning,
        )

    @property
    def variables(self) -> set[NodeVariableType]:
        """A set of all different |Node.variable| values of the |Node| objects directly
        connected to the actual |Element| object.

        Suppose an element is connected to five nodes, which (partly) represent
        different variables:

        >>> from hydpy import Element, Node
        >>> element = Element("Test",
        ...                   inlets=(Node("N1", "X"), Node("N2", "Y1")),
        ...                   outlets=(Node("N3", "X"), Node("N4", "Y2")),
        ...                   receivers=(Node("N5", "X"), Node("N6", "Y3")),
        ...                   senders=(Node("N7", "X"), Node("N8", "Y4")))

        Property |Element.variables| puts all the different variables of these nodes
        together:

        >>> sorted(element.variables)
        ['X', 'Y1', 'Y2', 'Y3', 'Y4']
        """
        variables = set()
        for connection in self.__connections:
            variables.update(connection.variables)
        return variables

    def prepare_allseries(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |Model.prepare_allseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.prepare_allseries(allocate_ram=allocate_ram, jit=jit)

    def prepare_inputseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |Model.prepare_inputseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.prepare_inputseries(
                allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
            )

    def prepare_factorseries(
        self, allocate_ram: bool = True, write_jit: bool = False
    ) -> None:
        """Call method |Model.prepare_factorseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.prepare_factorseries(allocate_ram=allocate_ram, write_jit=write_jit)

    def prepare_fluxseries(
        self, allocate_ram: bool = True, write_jit: bool = False
    ) -> None:
        """Call method |Model.prepare_fluxseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.prepare_fluxseries(allocate_ram=allocate_ram, write_jit=write_jit)

    def prepare_stateseries(
        self, allocate_ram: bool = True, write_jit: bool = False
    ) -> None:
        """Call method |Model.prepare_stateseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.prepare_stateseries(allocate_ram=allocate_ram, write_jit=write_jit)

    def load_allseries(self) -> None:
        """Call method |Model.load_allseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.load_allseries()

    def load_inputseries(self) -> None:
        """Call method |Model.load_inputseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.load_inputseries()

    def load_factorseries(self) -> None:
        """Call method |Model.load_factorseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.load_factorseries()

    def load_fluxseries(self) -> None:
        """Call method |Model.load_fluxseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.load_fluxseries()

    def load_stateseries(self) -> None:
        """Call method |Model.load_stateseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.load_stateseries()

    def save_allseries(self) -> None:
        """Call method |Model.save_allseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.save_allseries()

    def save_inputseries(self) -> None:
        """Call method |Model.save_inputseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.save_inputseries()

    def save_factorseries(self) -> None:
        """Call method |Model.save_factorseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.save_factorseries()

    def save_fluxseries(self) -> None:
        """Call method |Model.save_fluxseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.save_fluxseries()

    def save_stateseries(self) -> None:
        """Call method |Model.save_stateseries| of the currently handled |Model|
        instance and its submodels."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            model.save_stateseries()

    def _plot_series(
        self,
        *,
        subseqs: sequencetools.IOSequences[
            sequencetools.Sequences,
            sequencetools.IOSequence,
            sequencetools.FastAccessIOSequence,
        ],
        sequences: tuple[IOSequenceArg, ...],
        average: bool,
        labels: Optional[tuple[str, ...]],
        colors: Optional[Union[str, tuple[str, ...]]],
        linestyles: Optional[Union[LineStyle, tuple[LineStyle, ...]]],
        linewidths: Optional[Union[int, tuple[int, ...]]],
        focus: bool,
    ) -> pyplot.Figure:
        def _prepare_tuple(
            input_: Optional[Union[T, tuple[T, ...]]], nmb_entries: int
        ) -> tuple[Optional[T], ...]:
            if isinstance(input_, tuple):
                return input_
            return nmb_entries * (input_,)

        def _make_vectors(array: NDArrayFloat) -> list[NDArrayFloat]:
            vectors = []
            for idxs in itertools.product(*(range(shp) for shp in array.shape[1:])):
                vector = array
                for idx in idxs:
                    vector = vector[:, idx]
                vectors.append(vector)
            return vectors

        idx0, idx1 = hydpy.pub.timegrids.evalindices
        index = _get_pandasindex()[idx0:idx1]
        selseqs = self._query_iosequences(subseqs, sequences)
        nmb_sequences = len(selseqs)
        labels_: tuple[Optional[str], ...]
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
            kwargs = {"label": label_, "ax": pyplot.gca()}
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

    def _query_iosequences(
        self,
        subseqs: sequencetools.IOSequences[
            sequencetools.Sequences,
            sequencetools.IOSequence,
            sequencetools.FastAccessIOSequence,
        ],
        sequences: tuple[IOSequenceArg, ...],
    ) -> list[sequencetools.IOSequence]:
        models = tuple(self.model.find_submodels(include_mainmodel=True).values())
        if sequences:
            selseqs = []
            for sequence in sequences:
                typ: Optional[type[sequencetools.IOSequence]]
                if isinstance(sequence, str):
                    name = sequence
                    typ = None
                else:
                    name = sequence.name
                    if isinstance(sequence, sequencetools.IOSequence):
                        typ = type(sequence)
                    else:
                        typ = sequence
                for model in models:
                    seq = getattr(model.sequences[subseqs.name], name, None)
                    if (seq is not None) and ((typ is None) or isinstance(seq, typ)):
                        selseqs.append(seq)
                        break
                else:
                    raise ValueError(
                        f"No (sub)model handled by element `{self.name}` has "
                        f"{'an' if subseqs.name == 'inputs' else 'a'} "
                        f"{'flux' if subseqs.name == 'fluxes' else subseqs.name[:-1]} "
                        f"sequence named `{name}`"
                        f"{'' if typ is None else f' of type `{typ.__name__}'}."
                    )
            return selseqs
        return list(
            itertools.chain(*(getattr(m.sequences, subseqs.name) for m in models))
        )

    def plot_inputseries(
        self,
        *sequences: IOSequenceArg,
        average: bool = False,
        labels: Optional[tuple[str, ...]] = None,
        colors: Optional[Union[str, tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> pyplot.Figure:
        """Plot (the selected) |InputSequence| |IOSequence.series| values.

        We demonstrate the functionalities of method |Element.plot_inputseries| based
        on the `Lahn` example project:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2(lastdate="1997-01-01")

        Without any arguments, |Element.plot_inputseries| prints the time series of all
        input sequences handled by its (sub)models directly to the screen (in our
        example, |hland_inputs.P| and |hland_inputs.T| of |hland_96| and
        |evap_inputs.NormalAirTemperature| and |evap_inputs.NormalEvapotranspiration|
        of |evap_pet_hbv96|):

        >>> land = hp.elements.land_dill_assl
        >>> figure = land.plot_inputseries()

        You can use the `pyplot` API of `matplotlib` to modify the returned figure or
        to save it to disk (or print it to the screen, in case the interactive mode of
        `matplotlib` is disabled):

        >>> from hydpy.core.testtools import save_autofig
        >>> save_autofig("Element_plot_inputseries_complete.png", figure)

        .. image:: Element_plot_inputseries_complete.png

        Select specific sequences by passing their names, types, or example objects:

        >>> from hydpy.models.hland.hland_inputs import T
        >>> net = land.model.aetmodel.petmodel.sequences.inputs.normalevapotranspiration
        >>> figure = land.plot_inputseries("p", T, net)
        >>> save_autofig("Element_plot_inputseries_selection.png", figure)

        .. image:: Element_plot_inputseries_selection.png

        Misleading sequence specifiers result in the following error:

        >>> figure = land.plot_inputseries("xy")
        Traceback (most recent call last):
        ...
        ValueError: No (sub)model handled by element `land_dill_assl` has an input \
sequence named `xy`.

        Methods |Element.plot_factorseries|, |Element.plot_fluxseries|, and
        |Element.plot_stateseries| work in the same manner.  Before applying them, one
        has to calculate the time series of the |FactorSequence|, |FluxSequence|, and
        |StateSequence| objects:

        >>> hp.simulate()

        The arguments "labels," "colours," "line styles," and "line widths" can accept
        general or individual values:

        >>> figure = land.plot_fluxseries(
        ...     "q0", "q1", labels=("direct runoff", "base flow"),
        ...     colors=("red", "green"), linestyles="--", linewidths=2)
        >>> save_autofig("Element_plot_fluxseries.png", figure)

        .. image:: Element_plot_fluxseries.png

        For 1- and 2-dimensional |IOSequence| objects, all three methods plot the
        individual time series in the same colour.  We demonstrate this for the frozen
        (|hland_states.SP|) and the liquid (|hland_states.WC|) water equivalent of the
        snow cover of different hydrological response units.  Therefore, we restrict
        the shown period to February and March via the |Timegrids.eval_| time grid:

        >>> with pub.timegrids.eval_(firstdate="1996-02-01", lastdate="1996-04-01"):
        ...     figure = land.plot_stateseries("sp", "wc")
        >>> save_autofig("Element_plot_stateseries.png", figure)

        .. image:: Element_plot_stateseries.png

        Alternatively, you can print the averaged time series by assigning |True| to the
        argument `average`.  We demonstrate this functionality for the factor sequence
        |hland_factors.TC| (this time, without focusing on the time-series y-extent):

        >>> figure = land.plot_factorseries("tc", colors=("grey",))
        >>> figure = land.plot_factorseries(
        ...     "tc", average=True, focus=False, colors="black", linewidths=3)
        >>> save_autofig("Element_plot_factorseries.png", figure)

        .. image:: Element_plot_factorseries.png
        """
        return self._plot_series(
            subseqs=self.model.sequences.inputs,
            sequences=sequences,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def plot_factorseries(
        self,
        *sequences: IOSequenceArg,
        average: bool = False,
        labels: Optional[tuple[str, ...]] = None,
        colors: Optional[Union[str, tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> pyplot.Figure:
        """Plot the `factor` series of the handled model.

        See the documentation on method |Element.plot_inputseries| for additional
        information.
        """
        return self._plot_series(
            subseqs=self.model.sequences.factors,
            sequences=sequences,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def plot_fluxseries(
        self,
        *sequences: IOSequenceArg,
        average: bool = False,
        labels: Optional[tuple[str, ...]] = None,
        colors: Optional[Union[str, tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> pyplot.Figure:
        """Plot the `flux` series of the handled model.

        See the documentation on method |Element.plot_inputseries| for additional
        information.
        """
        return self._plot_series(
            subseqs=self.model.sequences.fluxes,
            sequences=sequences,
            average=average,
            labels=labels,
            colors=colors,
            linestyles=linestyles,
            linewidths=linewidths,
            focus=focus,
        )

    def plot_stateseries(
        self,
        *sequences: IOSequenceArg,
        average: bool = False,
        labels: Optional[tuple[str, ...]] = None,
        colors: Optional[Union[str, tuple[str, ...]]] = None,
        linestyles: Optional[Union[LineStyle, tuple[LineStyle, ...]]] = None,
        linewidths: Optional[Union[int, tuple[int, ...]]] = None,
        focus: bool = True,
    ) -> pyplot.Figure:
        """Plot the `state` series of the handled model.

        See the documentation on method |Element.plot_inputseries| for additional
        information.
        """
        return self._plot_series(
            subseqs=self.model.sequences.states,
            sequences=sequences,
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
                if (collective := self.collective) is not None:
                    lines.append(f'{blanks}collective="{collective}",')
                for groupname in (
                    "inlets",
                    "outlets",
                    "receivers",
                    "senders",
                    "inputs",
                    "outputs",
                ):
                    group = getattr(self, groupname, None)
                    if group:
                        subprefix = f"{blanks}{groupname}="
                        nodes = [str(node) for node in group]
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


_id2devices: dict[Device, dict[int, Devices[Device]]] = {}
_registry: Mapping[type[Device], dict[str, Device]] = {Node: {}, Element: {}}
_selection: Mapping[type[Device], dict[str, Device]] = {Node: {}, Element: {}}


@contextlib.contextmanager
def clear_registries_temporarily() -> Generator[None, None, None]:
    """Context manager for clearing the current |Node|, |Element|, and |FusedVariable|
    registries.

    Function |clear_registries_temporarily| is only available for testing purposes.

    These are the relevant registries for the currently initialised |Node|, |Element|,
    and |FusedVariable| objects:

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

    Before leaving the `with` block, the |clear_registries_temporarily| method restores
    the contents of each dictionary:

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
    registries: tuple[dict[Any, Any], ...] = (
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


def _get_pandasindex() -> pandas.Index:
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
        int((tg.lastdate - tg.firstdate - tg.stepsize) / tg.stepsize) + 1,
    )
    return index
