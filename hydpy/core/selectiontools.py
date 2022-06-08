# -*- coding: utf-8 -*-
"""This module implements tools for defining subsets of |Node| and |Element| objects of
large *HydPy* projects, called "selections"."""
# import...
# ...from standard library
from __future__ import annotations
import collections
import copy
import itertools
import types
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import networkx

# ...from HydPy
import hydpy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import typingtools

ModelTypesArg = Union[modeltools.Model, types.ModuleType, str]


class Selections:
    """Collection class for |Selection| objects.

    You can pass an arbitrary number of |Selection| objects to the constructor of class
    |Selections|:

    >>> sel1 = Selection("sel1", ["node1", "node2"], ["element1"])
    >>> sel2 = Selection("sel2", ["node1", "node3"], ["element2"])
    >>> selections = Selections(sel1, sel2)
    >>> selections
    Selections("sel1", "sel2")

    Also, you can query, add, and remove |Selection| objects via attribute access:

    >>> selections.sel3
    Traceback (most recent call last):
    ...
    AttributeError: The actual Selections object handles neither a normal attribute \
nor a Selection object called `sel3` that could be returned.
    >>> sel3 = Selection("sel3", ["node1", "node4"], ["element3"])
    >>> selections.sel3 = sel3
    >>> selections.sel3
    Selection("sel3",
              nodes=("node1", "node4"),
              elements="element3")
    >>> "sel3" in dir(selections)
    True
    >>> del selections.sel3
    >>> "sel3" in dir(selections)
    False
    >>> del selections.sel3
    Traceback (most recent call last):
    ...
    AttributeError: The actual Selections object handles neither a normal attribute \
nor a Selection object called `sel3` that could be deleted.

    Attribute names must be consistent with the `name` attribute of the respective
    |Selection| object:

    >>> selections.sel4 = sel3
    Traceback (most recent call last):
    ...
    ValueError: To avoid inconsistencies when handling Selection objects as \
attributes of a Selections object, attribute name and Selection name must be \
identical.  However,  for selection `sel3` the given attribute name is `sel4`.

    You can use item access alternatively:

    >>> selections["sel4"]
    Traceback (most recent call last):
    ...
    KeyError: 'The actual Selections object does not handle a Selection object called \
`sel4` that could be returned.'
    >>> selections["sel4"] = Selection("sel4")
    >>> selections["sel4"]
    Selection("sel4",
              nodes=(),
              elements=())
    >>> del selections["sel4"]
    >>> del selections["sel4"]
    Traceback (most recent call last):
    ...
    KeyError: 'The actual Selections object does not handle a Selection object called \
`sel4` that could be deleted.'

    You can ask for the existence of specific |Selection| objects within a |Selections|
    object both via its name and via the object itself:

    >>> sel1 in selections
    True
    >>> "sel1" in selections
    True
    >>> sel3 in selections
    False
    >>> "sel3" in selections
    False

    Class |Selections| supports both the |iter| and |len| operators:

    >>> for selection in selections:
    ...     print(selection.name)
    sel1
    sel2
    >>> len(selections)
    2

    For convenience, use the "+", "-", "+=", and "-=" operators to compare and modify
    |Selections| objects either based on single |Selection| objects or collections of
    |Selection| objects:

    >>> larger = selections + sel3
    >>> smaller = selections - sel2
    >>> sorted(selections.names)
    ['sel1', 'sel2']
    >>> sorted(larger.names)
    ['sel1', 'sel2', 'sel3']
    >>> smaller.names
    ('sel1',)

    >>> smaller += larger
    >>> sorted(smaller.names)
    ['sel1', 'sel2', 'sel3']
    >>> smaller -= sel1, sel2
    >>> smaller.names
    ('sel3',)

    Note that trying to remove non-existing |Selection| objects does not raise errors:

    >>> smaller -= sel2
    >>> smaller.names
    ('sel3',)
    >>> smaller - (sel1, sel2, sel3)
    Selections()

    The binary operators do not support other types than the mentioned ones:

    >>> smaller -= "sel3"
    Traceback (most recent call last):
    ...
    TypeError: Binary operations on Selections objects are defined for other \
Selections objects, single Selection objects, or iterables containing `Selection` \
objects, but the type of the given argument is `str`.
    >>> smaller -= 1   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: ... is `int`.

    Use the "==" operator to compare two |Selections| objects:

    >>> larger == smaller
    False
    >>> larger == (smaller + selections)
    True
    >>> larger == (sel1, sel2, sel3)
    False
    """

    def __init__(self, *selections: Selection) -> None:
        self.__selections: Dict[str, Selection] = {}
        self.add_selections(*selections)

    @property
    def names(self) -> Tuple[str, ...]:
        """The names of the actual |Selection| objects.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection("sel1", ["node1", "node2"], ["element1"]),
        ...     Selection("sel2", ["node1", "node3"], ["element2"]))
        >>> sorted(selections.names)
        ['sel1', 'sel2']
        """
        return tuple(self.__selections.keys())

    @property
    def nodes(self) -> devicetools.Nodes:
        """The |Node| objects of all handled |Selection| objects.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection("sel1", ["node1", "node2"], ["element1"]),
        ...     Selection("sel2", ["node1", "node3"], ["element2"]))
        >>> selections.nodes
        Nodes("node1", "node2", "node3")
        """
        nodes = devicetools.Nodes()
        for selection in self:
            nodes += selection.nodes
        return nodes

    @property
    def elements(self) -> devicetools.Elements:
        """The |Element| objects of all handled |Selection| objects.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection("sel1", ["node1"], ["element1"]),
        ...     Selection("sel2", ["node1"], ["element2", "element3"]))
        >>> selections.elements
        Elements("element1", "element2", "element3")
        """
        elements = devicetools.Elements()
        for selection in self:
            elements += selection.elements
        return elements

    def add_selections(self, *selections: Selection) -> None:
        """Add the given |Selection| object(s) to the current |Selections| object.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(Selection("sel1", ["node1"], ["element1"]))
        >>> selections.add_selections(
        ...     Selection("sel2", ["node1"], ["element2", "element3"]),
        ...     Selection("sel3", ["node2"], []))
        >>> selections
        Selections("sel1", "sel2", "sel3")
        >>> selections.nodes
        Nodes("node1", "node2")
        >>> selections.elements
        Elements("element1", "element2", "element3")
        """
        for selection in selections:
            self[selection.name] = selection

    def remove_selections(self, *selections: Selection) -> None:
        """Remove the given |Selection| object(s) from the current |Selections| object.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection("sel1", ["node1"], ["element1"]),
        ...     Selection("sel2", ["node1"], ["element2", "element3"]))
        >>> selections.remove_selections(
        ...     Selection("sel3", ["node2"], []), selections["sel1"])
        >>> selections
        Selections("sel2")
        >>> selections.nodes
        Nodes("node1")
        >>> selections.elements
        Elements("element2", "element3")
        """
        for selection in selections:
            try:
                del self[selection.name]
            except KeyError:
                pass

    def find(self, device: devicetools.TypeDevice) -> Selections:
        """Return all |Selection| objects containing the given |Node| or |Element|
        object.

        >>> from hydpy import Elements, Nodes, Selection, Selections
        >>> nodes = Nodes("n1", "n2", "n3")
        >>> elements = Elements("e1", "e2")
        >>> selections = Selections(
        ...     Selection("s1", ["n1", "n2"], ["e1"]),
        ...     Selection("s2", ["n1"]))
        >>> selections.find(nodes.n1)
        Selections("s1", "s2")
        >>> selections.find(nodes.n2)
        Selections("s1")
        >>> selections.find(nodes.n3)
        Selections()
        >>> selections.find(elements.e1)
        Selections("s1")
        >>> selections.find(elements.e2)
        Selections()
        """
        attr = "nodes" if isinstance(device, devicetools.Node) else "elements"
        selections = (
            selection for selection in self if device in getattr(selection, attr)
        )
        return Selections(*selections)

    @overload
    def query_intersections(
        self, selection2element: Literal[True] = ...
    ) -> Dict[Selection, Dict[Selection, devicetools.Elements]]:
        ...

    @overload
    def query_intersections(
        self, selection2element: Literal[False]
    ) -> Dict[devicetools.Element, Selections]:
        ...

    def query_intersections(
        self, selection2element: bool = True
    ) -> Union[
        Dict[Selection, Dict[Selection, devicetools.Elements]],
        Dict[devicetools.Element, Selections],
    ]:
        """A dictionary covering all cases where one |Element| object is a member of
        multiple |Selection| objects.

        The dictionary's structure depends on the value of the optional argument
        `selection2element`.  See method |Selections.print_intersections| for an
        example.
        """
        if selection2element:
            intersections: Dict[
                Selection,
                Dict[Selection, devicetools.Elements],
            ] = collections.defaultdict(dict)
            for selection1, selection2 in itertools.combinations(self, 2):
                intersection = selection1.elements.intersection(*selection2.elements)
                if intersection:
                    intersections[selection1][selection2] = intersection
                    intersections[selection2][selection1] = intersection
            return dict(intersections)
        intersections_: Dict[devicetools.Element, Selections] = {}
        for element in self.elements:
            selections = self.find(element)
            if len(selections) > 1:
                intersections_[element] = selections
        return intersections_

    def print_intersections(self, selection2element: bool = True) -> None:
        """Print the result of method |Selections.query_intersections|.

        We use method |Selections.print_intersections| to check if any combination of
        the following selections handles the same elements.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection("s1", nodes="n1",elements=("e1", "e2", "e3")),
        ...     Selection("s2", nodes="n1", elements=("e2", "e3", "e4")),
        ...     Selection("s3", nodes="n1", elements="e3"),
        ...     Selection("s4", nodes="n1", elements=("e5", "e6")),
        ... )

        If we call method |Selections.print_intersections| with argument
        `selection2element` |True|, we find out which selection intersects with which
        other and which elements are affected:

        >>> selections.print_intersections()
        selection s1 intersects with...
           ...selection s2 due to the following elements: e2 and e3
           ...selection s3 due to the following elements: e3
        selection s2 intersects with...
           ...selection s1 due to the following elements: e2 and e3
           ...selection s3 due to the following elements: e3
        selection s3 intersects with...
           ...selection s1 due to the following elements: e3
           ...selection s2 due to the following elements: e3

        If we call method |Selections.print_intersections| with argument
        `selection2element` |False|, we find out which element occurs multiple times in
        which selections:

        >>> selections.print_intersections(selection2element=False)
        element e2 is a member of multiple selections: s1 and s2
        element e3 is a member of multiple selections: s1, s2, and s3
        """
        if selection2element:
            intersections = self.query_intersections(True)
            for selection1, selection2elements in intersections.items():
                print("selection", selection1, "intersects with...")
                for selection2, elements in selection2elements.items():
                    print(
                        "   ...selection",
                        selection2,
                        "due to the following elements:",
                        objecttools.enumeration(elements.names),
                    )
        else:
            intersections_ = self.query_intersections(False)
            for element, selections in intersections_.items():
                print(
                    "element",
                    element.name,
                    "is a member of multiple selections:",
                    objecttools.enumeration(selections.names),
                )

    def __getattr__(self, key: str) -> Selection:
        try:
            return self.__selections[key]
        except KeyError:
            raise AttributeError(
                f"The actual Selections object handles neither a normal attribute nor "
                f"a Selection object called `{key}` that could be returned."
            ) from None

    def __setattr__(self, name: str, value: object) -> None:
        if isinstance(value, Selection):
            self[name] = value
        else:
            super().__setattr__(name, value)

    def __delattr__(self, key: str) -> None:
        try:
            del self.__selections[key]
        except KeyError:
            raise AttributeError(
                f"The actual Selections object handles neither a normal attribute nor "
                f"a Selection object called `{key}` that could be deleted."
            ) from None

    def __getitem__(self, key: str) -> Selection:
        try:
            return self.__selections[key]
        except KeyError:
            raise KeyError(
                f"The actual Selections object does not handle a Selection object "
                f"called `{key}` that could be returned."
            ) from None

    def __setitem__(self, key: str, value: Selection) -> None:
        if key != value.name:
            raise ValueError(
                f"To avoid inconsistencies when handling Selection objects as "
                f"attributes of a Selections object, attribute name and Selection "
                f"name must be identical.  However,  for selection `{value.name}` the "
                f"given attribute name is `{key}`."
            )
        self.__selections[key] = value

    def __delitem__(self, key: str) -> None:
        try:
            del self.__selections[key]
        except KeyError:
            raise KeyError(
                f"The actual Selections object does not handle a Selection object "
                f"called `{key}` that could be deleted."
            ) from None

    def __contains__(self, value: Union[str, Selection]) -> bool:
        if isinstance(value, str):
            return value in self.names
        return value in self.__selections.values()

    def __iter__(self) -> Iterator[Selection]:
        return iter(self.__selections.values())

    def __len__(self) -> int:
        return len(self.__selections)

    @staticmethod
    def __getiterable(
        value: typingtools.Mayberable1[Selection],
    ) -> List[Selection]:
        """Try to convert the given argument to a |list| of  |Selection| objects and
        return it."""
        try:
            return list(objecttools.extract(value, (Selection,)))
        except TypeError:
            raise TypeError(
                f"Binary operations on Selections objects are defined for other "
                f"Selections objects, single Selection objects, or iterables "
                f"containing `Selection` objects, but the type of the given argument "
                f"is `{type(value).__name__}`."
            ) from None

    def __add__(self, other: typingtools.Mayberable1[Selection]) -> Selections:
        selections = self.__getiterable(other)
        new = copy.copy(self)
        for selection in selections:
            new[selection.name] = selection
        return new

    def __iadd__(
        self,
        other: typingtools.Mayberable1[Selection],
    ) -> Selections:
        selections = self.__getiterable(other)
        for selection in selections:
            self[selection.name] = selection
        return self

    def __sub__(self, other: typingtools.Mayberable1[Selection]) -> Selections:
        selections = self.__getiterable(other)
        new = copy.copy(self)
        for selection in selections:
            try:
                del new[selection.name]
            except KeyError:
                pass
        return new

    def __isub__(
        self,
        other: typingtools.Mayberable1[Selection],
    ) -> Selections:
        selections = self.__getiterable(other)
        for selection in selections:
            try:
                del self[selection.name]
            except KeyError:
                pass
        return self

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (Selection, Selections, hydpytools.HydPy)):
            return (self.nodes == self.nodes) and (self.elements == other.elements)
        return False

    def __copy__(self) -> Selections:
        return type(self)(*self.__selections.values())

    def __repr__(self) -> str:
        return self.assignrepr("")

    def assignrepr(self, prefix: str = "") -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            options = hydpy.pub.options
            with options.ellipsis(2, optional=True):  # pylint: disable=not-callable
                prefix = f"{prefix}{type(self).__name__}("
                return (
                    f"{objecttools.assignrepr_values(sorted(self.names), prefix, 70)})"
                )

    def __dir__(self) -> List[str]:
        return cast(List[str], super().__dir__()) + list(self.names)


class Selection:
    """Handles and modifies combinations of |Node| and |Element| objects.

    In *HydPy*, |Node|, and |Element| objects are the fundamental means to structure
    projects.  However, keeping the overview of huge projects involving thousands of
    nodes and elements requires additional strategies.

    One such strategy is to define different instances of class |Selection| for
    different aspects of a project.  Often, a selection contains all nodes and elements
    of a certain subcatchment or all elements handling certain model types. Selections
    can be overlapping, meaning, for example, that an element can be part of a
    subcatchment selection and of model-type selection at the same time.

    Selections can be written to and read from individual network files, as explained
    in the documentation on class |NetworkManager|.  Read selections are available via
    the |pub| module.  In most application scripts (e.g. for parameter calibration),
    one performs different operations on the nodes and elements of the different
    selections (e.g. change parameter "a" and "b" for models of selection "x" and "y",
    respectively).  However, class |Selection| also provides features for creating
    combinations of |Node| and |Element| objects suitable for different tasks, as
    explained in the documentation of the respective methods.  Here we only show its
    basic usage with the help of the `LahnH` example project prepared by function
    |prepare_full_example_2|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> _, pub, _ = prepare_full_example_2()

    For example, `LahnH` defines a `headwaters` selection:

    >>> pub.selections.headwaters
    Selection("headwaters",
              nodes=("dill", "lahn_1"),
              elements=("land_dill", "land_lahn_1"))

    You can compare this selection with other new or already available selections, with
    "headwaters < complete" returning |True| meaning that all nodes and elements of the
    headwater catchments are also part of the entire catchment:

    >>> from hydpy import Selection
    >>> test = Selection("test",
    ...                  elements=("land_dill", "land_lahn_1"),
    ...                  nodes=("dill", "lahn_1"))
    >>> pub.selections.headwaters < test
    False
    >>> pub.selections.headwaters <= test
    True
    >>> pub.selections.headwaters == test
    True
    >>> pub.selections.headwaters != test
    False
    >>> pub.selections.headwaters >= test
    True
    >>> pub.selections.headwaters > test
    False
    >>> pub.selections.headwaters < pub.selections.complete
    True
    >>> pub.selections.headwaters <= pub.selections.complete
    True
    >>> pub.selections.headwaters == pub.selections.complete
    False
    >>> pub.selections.headwaters != pub.selections.complete
    True
    >>> pub.selections.headwaters >= pub.selections.complete
    False
    >>> pub.selections.headwaters > pub.selections.complete
    False

    The |len| operator returns the total number of handled node and element objects:

    >>> len(test)
    4

    Use the "+=" and "-=" operators to add or remove nodes and elements:

    >>> test += pub.selections.complete
    >>> len(test)
    11
    >>> test -= pub.selections.complete
    >>> len(test)
    0

    Passing a wrong argument to the binary operators results in errors like the
    following:

    >>> test += 1
    Traceback (most recent call last):
    ...
    AttributeError: While trying to add selection `test` with object `1` of type \
`int`, the following error occurred: 'int' object has no attribute 'nodes'
    >>> test -= pub.selections.complete.nodes.dill
    Traceback (most recent call last):
    ...
    AttributeError: While trying to subtract selection `test` with object `dill` of \
type `Node`, the following error occurred: 'Node' object has no attribute 'nodes'
    >>> test < "wrong"
    Traceback (most recent call last):
    ...
    AttributeError: While trying to compare selection `test` with object `wrong` of \
type `str`, the following error occurred: 'str' object has no attribute 'nodes'

    But as usual, checking for equality or inequality returns |False| and |True| for
    uncomparable objects:

    >>> test == "wrong"
    False
    >>> test != "wrong"
    True

    Applying the |str| function only returns the selection name:

    >>> str(test)
    'test'
    """

    name: str
    """The selection's name."""
    nodes: devicetools.Nodes
    """The explicitly handled |Node| objects (m).
    
    |Selection.nodes| does not necessarily contain all nodes to which the elements in 
    |Selection.elements| are linked.
    """
    elements: devicetools.Elements
    """The explicitly handled |Element| objects.
    
    |Selection.elements| does not necessarily contain all nodes to which the elements 
    in |Selection.nodes| are linked.
    """

    def __init__(
        self,
        name: str,
        nodes: devicetools.NodesConstrArg = None,
        elements: devicetools.ElementsConstrArg = None,
    ) -> None:
        self.name = str(name)
        self.nodes = devicetools.Nodes(nodes).copy()
        self.elements = devicetools.Elements(elements).copy()

    def _check_device(
        self, device: devicetools.TypeDevice, type_of_device: str
    ) -> devicetools.TypeDevice:
        if isinstance(device, devicetools.Node):
            device = self.nodes[device.name]
        elif isinstance(device, devicetools.Element):
            device = self.elements[device.name]
        else:
            raise TypeError(
                f"Either a `Node` or an `Element` object is required as the "
                f'"{type_of_device} device", but the given `device` value is of type '
                f"`{type(device).__name__}`."
            )
        return device

    def search_upstream(
        self,
        device: devicetools.TypeDevice,
        name: str = "upstream",
        inclusive: bool = True,
    ) -> Selection:
        """Return the network upstream of the given starting point, including the
        starting point itself.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        You can pass both |Node| and |Element| objects and, optionally, the name of the
        newly created |Selection| object:

        >>> test = pub.selections.complete.copy("test")
        >>> test.search_upstream(hp.nodes.lahn_2)
        Selection("upstream",
                  nodes=("dill", "lahn_1", "lahn_2"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "stream_dill_lahn_2", "stream_lahn_1_lahn_2"))
        >>> test.search_upstream(hp.elements.stream_lahn_1_lahn_2, "UPSTREAM")
        Selection("UPSTREAM",
                  nodes=("lahn_1", "lahn_2"),
                  elements=("land_lahn_1", "stream_lahn_1_lahn_2"))

        Method |Selection.search_upstream| generally selects all |Node| objects
        directly connected to any upstream |Element| object.  Set the `inclusive`
        argument to |False| to circumvent this:

        >>> test.search_upstream(hp.elements.stream_lahn_1_lahn_2, "UPSTREAM", False)
        Selection("UPSTREAM",
                  nodes="lahn_1",
                  elements=("land_lahn_1", "stream_lahn_1_lahn_2"))

        Wrong device specifications result in errors like the following:

        >>> test.search_upstream(1)
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine an upstream network of selection `test`, \
the following error occurred: Either a `Node` or an `Element` object is required as \
the "outlet device", but the given `device` value is of type `int`.

        >>> pub.selections.headwaters.search_upstream(hp.nodes.lahn_3)
        Traceback (most recent call last):
        ...
        KeyError: "While trying to determine an upstream network of selection \
`headwaters`, the following error occurred: 'No device named `lahn_3` available.'"

        Method |Selection.select_upstream| restricts the current selection to the one
        determined with the method |Selection.search_upstream|:

        >>> test.select_upstream(hp.nodes.lahn_2)
        Selection("test",
                  nodes=("dill", "lahn_1", "lahn_2"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "stream_dill_lahn_2", "stream_lahn_1_lahn_2"))

        On the contrary, the method |Selection.deselect_upstream| restricts the current
        selection to all devices not determined by method |Selection.search_upstream|:

        >>> complete = pub.selections.complete.deselect_upstream(hp.nodes.lahn_2)
        >>> complete
        Selection("complete",
                  nodes="lahn_3",
                  elements=("land_lahn_3", "stream_lahn_2_lahn_3"))

        If necessary, include the "outlet device" manually afterwards:

        >>> complete.nodes.add_device(hp.nodes.lahn_2)
        >>> complete
        Selection("complete",
                  nodes=("lahn_2", "lahn_3"),
                  elements=("land_lahn_3", "stream_lahn_2_lahn_3"))

        Method |Selection.search_downstream| generally selects all |Node| objects
        directly connected to any upstream |Element| object.  Set the `inclusive`
        argument to |False| to circumvent this:

        >>> from hydpy import Element, Nodes, Selection
        >>> nodes = Nodes(
        ...     "inlet", "outlet1", "outlet2", "input_", "output", "receiver", "sender")
        >>> upper = Element("upper",
        ...                 inlets=nodes.inlet, outlets=(nodes.outlet1, nodes.outlet2),
        ...                 inputs=nodes.input_, outputs=nodes.output,
        ...                 receivers=nodes.receiver, senders=nodes.sender)
        >>> test = Selection("test", nodes=nodes, elements=upper)
        >>> test.search_upstream(nodes.outlet1, inclusive=True)
        Selection("upstream",
                  nodes=("inlet", "input_", "outlet1", "outlet2", "output",
                         "receiver", "sender"),
                  elements="upper")
        >>> test.search_upstream(nodes.outlet1, inclusive=False)
        Selection("upstream",
                  nodes=("inlet", "input_", "outlet1"),
                  elements="upper")
        """
        try:
            device = self._check_device(device, "outlet")
            devices = networkx.ancestors(
                G=hydpytools.create_directedgraph(self), source=device
            )
            devices.add(device)
            selection = Selection(
                name=name,
                nodes=[d for d in devices if isinstance(d, devicetools.Node)],
                elements=[d for d in devices if isinstance(d, devicetools.Element)],
            )
            if inclusive:
                add_device = selection.nodes.add_device
                for element in selection.elements:
                    for nodes in (
                        element.outlets,
                        element.outputs,
                        element.receivers,
                        element.senders,
                    ):
                        for node in nodes:
                            add_device(node)
            return selection
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to determine an upstream network of selection "
                f"`{self.name}`"
            )

    def select_upstream(
        self, device: devicetools.TypeDevice, inclusive: bool = True
    ) -> Selection:
        """Restrict the current selection to the network upstream of the given starting
        point, including the starting point itself.

        See the documentation on method |Selection.search_upstream| for additional
        information.
        """
        upstream = self.search_upstream(device, inclusive=inclusive)
        self.nodes = upstream.nodes
        self.elements = upstream.elements
        return self

    def deselect_upstream(
        self, device: devicetools.TypeDevice, inclusive: bool = True
    ) -> Selection:
        """Remove the network upstream of the given starting point from the current
        selection, including the starting point itself.

        See the documentation on method |Selection.search_upstream| for additional
        information.
        """
        upstream = self.search_upstream(device, inclusive=inclusive)
        self.nodes -= upstream.nodes
        self.elements -= upstream.elements
        return self

    def search_downstream(
        self,
        device: devicetools.TypeDevice,
        name: str = "downstream",
        inclusive: bool = True,
    ) -> Selection:
        """Return the network downstream of the given starting point, including the
        starting point itself.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        You can pass both |Node| and |Element| objects and, optionally, the name of the
        newly created |Selection| object:

        >>> test = pub.selections.complete.copy("test")
        >>> test.search_downstream(hp.nodes.lahn_1)
        Selection("downstream",
                  nodes=("lahn_1", "lahn_2", "lahn_3"),
                  elements=("stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))
        >>> test.search_downstream(hp.elements.land_lahn_1, "DOWNSTREAM")
        Selection("DOWNSTREAM",
                  nodes=("lahn_1", "lahn_2", "lahn_3"),
                  elements=("land_lahn_1", "stream_lahn_1_lahn_2",
                            "stream_lahn_2_lahn_3"))

        Wrong device specifications result in errors like the following:

        >>> test.search_downstream(1)
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine a downstream network of selection \
`test`, the following error occurred: Either a `Node` or an `Element` object is \
required as the "inlet device", but the given `device` value is of type `int`.

        >>> pub.selections.headwaters.search_downstream(hp.nodes.lahn_3)
        Traceback (most recent call last):
        ...
        KeyError: "While trying to determine a downstream network of selection \
`headwaters`, the following error occurred: 'No device named `lahn_3` available.'"

        Method |Selection.select_downstream| restricts the current selection to the one
        determined with the method |Selection.search_upstream|:

        >>> test.select_downstream(hp.nodes.lahn_1)
        Selection("test",
                  nodes=("lahn_1", "lahn_2", "lahn_3"),
                  elements=("stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

        On the contrary, the method |Selection.deselect_downstream| restricts the
        current selection to all devices not determined by method
        |Selection.search_downstream|:

        >>> complete = pub.selections.complete.deselect_downstream(
        ...     hp.nodes.lahn_1)
        >>> complete
        Selection("complete",
                  nodes="dill",
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2"))

        If necessary, include the "inlet device" manually afterwards:

        >>> complete.nodes.add_device(hp.nodes.lahn_1)
        >>> complete
        Selection("complete",
                  nodes=("dill", "lahn_1"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2"))

        Method |Selection.search_downstream| generally selects all |Node| objects
        directly connected to any upstream |Element| object.  Set the `inclusive`
        argument to |False| to circumvent this:

        >>> from hydpy import Element, Nodes, Selection
        >>> nodes = Nodes(
        ...     "inlet1", "inlet2", "outlet", "input_", "output", "receiver", "sender")
        >>> lower = Element("lower",
        ...                 inlets=(nodes.inlet1, nodes.inlet2), outlets=nodes.outlet,
        ...                 inputs=nodes.input_, outputs=nodes.output,
        ...                 receivers=nodes.receiver, senders=nodes.sender)
        >>> test = Selection("test", nodes=nodes, elements=lower)
        >>> test.search_downstream(nodes.inlet1, inclusive=True)
        Selection("downstream",
                  nodes=("inlet1", "inlet2", "input_", "outlet", "output",
                         "receiver", "sender"),
                  elements="lower")
        >>> test.search_downstream(nodes.inlet1, inclusive=False)
        Selection("downstream",
                  nodes=("inlet1", "outlet", "output"),
                  elements="lower")
        """
        try:
            device = self._check_device(device, "inlet")
            devices = networkx.descendants(
                G=hydpytools.create_directedgraph(self),
                source=device,
            )
            devices.add(device)
            selection = Selection(
                name=name,
                nodes=[d for d in devices if isinstance(d, devicetools.Node)],
                elements=[d for d in devices if isinstance(d, devicetools.Element)],
            )
            if inclusive:
                add_device = selection.nodes.add_device
                for element in selection.elements:
                    for nodes in (
                        element.inlets,
                        element.inputs,
                        element.receivers,
                        element.senders,
                    ):
                        for node in nodes:
                            add_device(node)
            return selection
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to determine a downstream network of selection "
                f"`{self.name}`"
            )

    def select_downstream(
        self, device: devicetools.TypeDevice, inclusive: bool = True
    ) -> Selection:
        """Restrict the current selection to the network downstream of the given
        starting point, including the starting point itself.

        See the documentation on method |Selection.search_downstream| for additional
        information.
        """
        downstream = self.search_downstream(device, inclusive=inclusive)
        self.nodes = downstream.nodes
        self.elements = downstream.elements
        return self

    def deselect_downstream(
        self, device: devicetools.TypeDevice, inclusive: bool = True
    ) -> Selection:
        """Remove the network downstream of the given starting point from the current
        selection, including the starting point itself.

        See the documentation on method |Selection.search_downstream| for additional
        information.
        """
        downstream = self.search_downstream(device, inclusive=inclusive)
        self.nodes -= downstream.nodes
        self.elements -= downstream.elements
        return self

    def search_modeltypes(
        self, *models: ModelTypesArg, name: str = "modeltypes"
    ) -> Selection:
        """Return a |Selection| object containing only the elements currently handling
        models of the given types.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        You can pass both |Model| objects and names and, as a keyword argument, the
        name of the newly created |Selection| object:

        >>> test = pub.selections.complete.copy("test")
        >>> from hydpy import prepare_model
        >>> hland_v1 = prepare_model("hland_v1")

        >>> test.search_modeltypes(hland_v1)
        Selection("modeltypes",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3"))
        >>> test.search_modeltypes(
        ...     hland_v1, "musk_classic", "lland_v1", name="MODELTYPES")
        Selection("MODELTYPES",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

        Wrong model specifications result in errors like the following:

        >>> test.search_modeltypes("wrong")
        Traceback (most recent call last):
        ...
        ModuleNotFoundError: While trying to determine the elements of selection \
`test` handling the model defined by the argument(s) `wrong` of type(s) `str`, the \
following error occurred: No module named 'hydpy.models.wrong'

        Method |Selection.select_modeltypes| restricts the current selection to the one
        determined with the method the |Selection.search_modeltypes|:

        >>> test.select_modeltypes(hland_v1)
        Selection("test",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3"))

        On the contrary, the method |Selection.deselect_upstream| restricts the current
        selection to all devices not determined by method the
        |Selection.search_upstream|:

        >>> pub.selections.complete.deselect_modeltypes(hland_v1)
        Selection("complete",
                  nodes=(),
                  elements=("stream_dill_lahn_2", "stream_lahn_1_lahn_2",
                            "stream_lahn_2_lahn_3"))
        """
        try:
            typelist = []
            for model in models:
                if not isinstance(model, modeltools.Model):
                    model = importtools.prepare_model(model)
                typelist.append(type(model))
            typetuple = tuple(typelist)
            selection = Selection(name)
            for element in self.elements:
                if isinstance(element.model, typetuple):
                    selection.elements += element
        except BaseException:
            values = objecttools.enumeration(models)
            classes = objecttools.enumeration(type(model).__name__ for model in models)
            objecttools.augment_excmessage(
                f"While trying to determine the elements of selection `{self.name}` "
                f"handling the model defined by the argument(s) `{values}` of type(s) "
                f"`{classes}`"
            )
        return selection

    def select_modeltypes(self, *models: ModelTypesArg) -> Selection:
        """Restrict the current |Selection| object to all elements containing the given
        model types (removes all nodes).

        See the documentation on method |Selection.search_modeltypes| for additional
        information.
        """
        self.nodes = devicetools.Nodes()
        self.elements = self.search_modeltypes(*models).elements
        return self

    def deselect_modeltypes(self, *models: ModelTypesArg) -> Selection:
        """Restrict the current selection to all elements not containing the given
        model types (removes all nodes).

        See the documentation on method |Selection.search_modeltypes| for additional
        information.
        """
        self.nodes = devicetools.Nodes()
        self.elements -= self.search_modeltypes(*models).elements
        return self

    def search_nodenames(self, *substrings: str, name: str = "nodenames") -> Selection:
        """Return a new selection containing all nodes of the current selection with a
        name containing at least one of the given substrings.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        Pass the (sub)strings as positional arguments and, optionally, the name of the
        newly created |Selection| object as a keyword argument:

        >>> test = pub.selections.complete.copy("test")
        >>> from hydpy import prepare_model
        >>> test.search_nodenames("dill", "lahn_1")
        Selection("nodenames",
                  nodes=("dill", "lahn_1"),
                  elements=())

        Wrong string specifications result in errors like the following:

        >>> test.search_nodenames(["dill", "lahn_1"])
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine the nodes of selection `test` with names \
containing at least one of the given substrings `['dill', 'lahn_1']`, the following \
error occurred: 'in <string>' requires string as left operand, not list

        Method |Selection.select_nodenames| restricts the current selection to the one
        determined with the the method |Selection.search_nodenames|:

        >>> test.select_nodenames("dill", "lahn_1")
        Selection("test",
                  nodes=("dill", "lahn_1"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

        On the contrary, the method |Selection.deselect_nodenames| restricts the
        current selection to all devices not determined by the method
        |Selection.search_nodenames|:

        >>> pub.selections.complete.deselect_nodenames("dill", "lahn_1")
        Selection("complete",
                  nodes=("lahn_2", "lahn_3"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))
        """
        try:
            selection = Selection(name)
            for node in self.nodes:
                for substring in substrings:
                    if substring in node.name:
                        selection.nodes += node
                        break
        except BaseException:
            values = objecttools.enumeration(substrings)
            objecttools.augment_excmessage(
                f"While trying to determine the nodes of selection `{self.name}` with "
                f"names containing at least one of the given substrings `{values}`"
            )
        return selection

    def select_nodenames(self, *substrings: str) -> Selection:
        """Restrict the current selection to all nodes with a name containing at least
        one of the given substrings  (does not affect any elements).

        See the documentation on method |Selection.search_nodenames| for additional
        information.
        """
        self.nodes = self.search_nodenames(*substrings).nodes
        return self

    def deselect_nodenames(self, *substrings: str) -> Selection:
        """Restrict the current selection to all nodes with a name not containing at
        least one of the given substrings (does not affect any elements).

        See the documentation on method |Selection.search_nodenames| for additional
        information.
        """
        self.nodes -= self.search_nodenames(*substrings).nodes
        return self

    def search_elementnames(
        self, *substrings: str, name: str = "elementnames"
    ) -> Selection:
        """Return a new selection containing all elements of the current selection with
        a name containing at least one of the given substrings.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        Pass the (sub)strings as positional arguments and, optionally, the name of the
        newly created |Selection| object as a keyword argument:

        >>> test = pub.selections.complete.copy("test")
        >>> from hydpy import prepare_model
        >>> test.search_elementnames("dill", "lahn_1")
        Selection("elementnames",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2"))

        Wrong string specifications result in errors like the following:

        >>> test.search_elementnames(["dill", "lahn_1"])
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine the elements of selection `test` with \
names containing at least one of the given substrings `['dill', 'lahn_1']`, the \
following error occurred: 'in <string>' requires string as left operand, not list

        Method |Selection.select_elementnames| restricts the current selection to the
        one determined with the method |Selection.search_elementnames|:

        >>> test.select_elementnames("dill", "lahn_1")
        Selection("test",
                  nodes=("dill", "lahn_1", "lahn_2", "lahn_3"),
                  elements=("land_dill", "land_lahn_1", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2"))

        On the contrary, the method |Selection.deselect_elementnames| restricts the
        current selection to all devices not determined by the method
        |Selection.search_elementnames|:

        >>> pub.selections.complete.deselect_elementnames("dill", "lahn_1")
        Selection("complete",
                  nodes=("dill", "lahn_1", "lahn_2", "lahn_3"),
                  elements=("land_lahn_2", "land_lahn_3",
                            "stream_lahn_2_lahn_3"))
        """
        try:
            selection = Selection(name)
            for element in self.elements:
                for substring in substrings:
                    if substring in element.name:
                        selection.elements += element
                        break
        except BaseException:
            values = objecttools.enumeration(substrings)
            objecttools.augment_excmessage(
                f"While trying to determine the elements of selection `{self.name}` "
                f"with names containing at least one of the given substrings `{values}`"
            )
        return selection

    def select_elementnames(self, *substrings: str) -> Selection:
        """Restrict the current selection to all elements with a name containing at
        least one of the given substrings (does not affect any nodes).

        See the documentation on method |Selection.search_elementnames| for additional
        information.
        """
        self.elements = self.search_elementnames(*substrings).elements
        return self

    def deselect_elementnames(
        self,
        *substrings: str,
    ) -> Selection:
        """Restrict the current selection to all elements with a name not containing at
        least one of the given substrings.   (does not affect any nodes).

        See the documentation on method |Selection.search_elementnames| for additional
        information.
        """
        self.elements -= self.search_elementnames(*substrings).elements
        return self

    def copy(self, name: str) -> Selection:
        """Return a new |Selection| object with the given name and copies of the
        handled |Nodes| and |Elements| objects based on method |Devices.copy|."""
        return type(self)(name, copy.copy(self.nodes), copy.copy(self.elements))

    def add_remotes(self) -> None:
        """Add all remote nodes linked to at least one of the currently handled
        elements.

        One often encounters the situation (for example, after calling method
        |Selection.select_upstream|), when a selection does not explicitly include all
        relevant remote nodes, like in the following example:

        >>> from hydpy import Element, Selection
        >>> dam = Element("dam", inlets="inflow", outlets="outflow",
        ...               receivers="discharge_downstream", senders="water_level")
        >>> sel = Selection("Dam", elements=dam, nodes=("inflow", "outflow"))
        >>> sel
        Selection("Dam",
                  nodes=("inflow", "outflow"),
                  elements="dam")

        The method |Selection.add_remotes| is a small auxiliary function that takes
        care of this:

        >>> sel.add_remotes()
        >>> sel
        Selection("Dam",
                  nodes=("discharge_downstream", "inflow", "outflow",
                         "water_level"),
                  elements="dam")
        """
        nodes = self.nodes
        for element in self.elements:
            for node in itertools.chain(element.receivers, element.senders):
                nodes.add_device(node)

    def save_networkfile(
        self, filepath: Union[str, None] = None, write_defaultnodes: bool = True
    ) -> None:
        """Save the selection as a network file.

        >>> from hydpy.examples import prepare_full_example_2
        >>> _, pub, TestIO = prepare_full_example_2()

        In most cases, one should conveniently write network files via method
        |NetworkManager.save_files| of class |NetworkManager|.  However, using the
        method |Selection.save_networkfile| allows for additional configuration via the
        arguments `filepath` and `write_defaultnodes`:

        >>> with TestIO():
        ...     pub.selections.headwaters.save_networkfile()
        ...     with open("headwaters.py") as networkfile:
        ...         print(networkfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy import Element, Node
        <BLANKLINE>
        <BLANKLINE>
        Node("dill", variable="Q",
             keywords="gauge")
        <BLANKLINE>
        Node("lahn_1", variable="Q",
             keywords="gauge")
        <BLANKLINE>
        <BLANKLINE>
        Element("land_dill",
                outlets="dill",
                keywords="catchment")
        <BLANKLINE>
        Element("land_lahn_1",
                outlets="lahn_1",
                keywords="catchment")
        <BLANKLINE>

        >>> with TestIO():
        ...     pub.selections.headwaters.save_networkfile(
        ...         "test.py", write_defaultnodes=False)
        ...     with open("test.py") as networkfile:
        ...         print(networkfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy import Element, Node
        <BLANKLINE>
        <BLANKLINE>
        Element("land_dill",
                outlets="dill",
                keywords="catchment")
        <BLANKLINE>
        Element("land_lahn_1",
                outlets="lahn_1",
                keywords="catchment")
        <BLANKLINE>

        The `write_defaultnodes` argument does only affect nodes handling the default
        variable `Q`:

        >>> from hydpy import FusedVariable, Node
        >>> from hydpy.inputs import hland_P, hland_T, lland_Nied
        >>> from hydpy.outputs import hland_Perc, hland_Q0, hland_Q1
        >>> Precip = FusedVariable("Precip", hland_P, lland_Nied)
        >>> Runoff = FusedVariable("Runoff", hland_Q0, hland_Q1)
        >>> nodes = pub.selections.headwaters.nodes
        >>> nodes.add_device(Node("test1", variable="X"))
        >>> nodes.add_device(Node("test2", variable=hland_T))
        >>> nodes.add_device(Node("test3", variable=Precip))
        >>> nodes.add_device(Node("test4", variable=hland_Perc))
        >>> nodes.add_device(Node("test5", variable=Runoff))
        >>> with TestIO():
        ...     pub.selections.headwaters.save_networkfile(
        ...         "test.py", write_defaultnodes=False)
        ...     with open("test.py") as networkfile:
        ...         print(networkfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy import Element, FusedVariable, Node
        from hydpy.inputs import hland_P, hland_T, lland_Nied
        from hydpy.outputs import hland_Perc, hland_Q0, hland_Q1
        <BLANKLINE>
        Precip = FusedVariable("Precip", hland_P, lland_Nied)
        Runoff = FusedVariable("Runoff", hland_Q0, hland_Q1)
        <BLANKLINE>
        <BLANKLINE>
        Node("test1", variable="X")
        <BLANKLINE>
        Node("test2", variable=hland_T)
        <BLANKLINE>
        Node("test3", variable=Precip)
        <BLANKLINE>
        Node("test4", variable=hland_Perc)
        <BLANKLINE>
        Node("test5", variable=Runoff)
        <BLANKLINE>
        <BLANKLINE>
        Element("land_dill",
                outlets="dill",
                keywords="catchment")
        <BLANKLINE>
        Element("land_lahn_1",
                outlets="lahn_1",
                keywords="catchment")
        <BLANKLINE>
        """
        inputaliases: Set[str] = set()
        outputaliases: Set[str] = set()
        fusedvariables: Set[devicetools.FusedVariable] = set()
        for variable in self.nodes.variables:
            if isinstance(variable, str):
                continue
            if isinstance(variable, devicetools.FusedVariable):
                fusedvariables.add(variable)
            elif issubclass(variable, sequencetools.InputSequence):
                inputaliases.add(hydpy.sequence2alias[variable])
            else:
                outputaliases.add(hydpy.sequence2alias[variable])
        for fusedvariable in fusedvariables:
            for sequence in fusedvariable:
                if issubclass(sequence, sequencetools.InputSequence):
                    inputaliases.add(hydpy.sequence2alias[sequence])
                else:
                    outputaliases.add(hydpy.sequence2alias[sequence])
        if filepath is None:
            filepath = self.name + ".py"
        with open(filepath, "w", encoding="utf-8") as file_:
            file_.write("# -*- coding: utf-8 -*-\n")
            if fusedvariables:
                file_.write("\nfrom hydpy import Element, FusedVariable, Node")
            else:
                file_.write("\nfrom hydpy import Element, Node")
            if inputaliases:
                aliases = ", ".join(sorted(inputaliases))
                file_.write(f"\nfrom hydpy.inputs import {aliases}")
            if outputaliases:
                aliases = ", ".join(sorted(outputaliases))
                file_.write(f"\nfrom hydpy.outputs import {aliases}")
            file_.write("\n\n")
            for fusedvariable in sorted(fusedvariables, key=str):
                file_.write(f"{fusedvariable} = {repr(fusedvariable)}\n")
            if fusedvariables:
                file_.write("\n")
            written = False
            for node in self.nodes:
                if write_defaultnodes or (node.variable != "Q"):
                    file_.write("\n" + repr(node) + "\n")
                    written = True
            if written:
                file_.write("\n")
            for element in self.elements:
                file_.write("\n" + repr(element) + "\n")

    def __len__(self) -> int:
        return len(self.nodes) + len(self.elements)

    _ERRORMESSAGE = (
        "selection `{self.name}` with object `{other}` of type `{classname(other)}`"
    )

    @objecttools.excmessage_decorator(f"add {_ERRORMESSAGE}")
    def __iadd__(self, other: Selection) -> Selection:
        self.nodes += other.nodes
        self.elements += other.elements
        return self

    @objecttools.excmessage_decorator(f"subtract {_ERRORMESSAGE}")
    def __isub__(self, other: Selection) -> Selection:
        self.nodes -= other.nodes
        self.elements -= other.elements
        return self

    @objecttools.excmessage_decorator(f"compare {_ERRORMESSAGE}")
    def __lt__(self, other: Selection) -> bool:
        return (self.nodes < other.nodes) and (self.elements < other.elements)

    @objecttools.excmessage_decorator(f"compare {_ERRORMESSAGE}")
    def __le__(self, other: Selection) -> bool:
        return (self.nodes <= other.nodes) and (self.elements <= other.elements)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (hydpytools.HydPy, Selection)):
            return (self.nodes == other.nodes) and (self.elements == other.elements)
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, (hydpytools.HydPy, Selection)):
            return (self.nodes != other.nodes) or (self.elements != other.elements)
        return True

    @objecttools.excmessage_decorator(f"compare {_ERRORMESSAGE}")
    def __ge__(self, other: Selection) -> bool:
        return (self.nodes >= other.nodes) and (self.elements >= other.elements)

    @objecttools.excmessage_decorator(f"compare {_ERRORMESSAGE}")
    def __gt__(self, other: Selection) -> bool:
        return (self.nodes > other.nodes) and (self.elements >= other.elements)

    def __hash__(self) -> int:
        return id(self)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.assignrepr("")

    def assignrepr(self, prefix: str = "") -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            options = hydpy.pub.options
            with options.ellipsis(2, optional=True):  # pylint: disable=not-callable
                with objecttools.assignrepr_tuple.always_bracketed(False):
                    classname = type(self).__name__
                    blanks = " " * (len(prefix + classname) + 1)
                    nodestr = objecttools.assignrepr_tuple(
                        self.nodes.names, blanks + "nodes=", 70
                    )
                    elementstr = objecttools.assignrepr_tuple(
                        self.elements.names, blanks + "elements=", 70
                    )
                    return (
                        f'{prefix}{classname}("{self.name}",\n'
                        f"{nodestr},\n"
                        f"{elementstr})"
                    )
