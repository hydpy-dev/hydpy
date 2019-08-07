# -*- coding: utf-8 -*-
"""This module implements tools for defining subsets of |Node| and
|Element| objects of large *HydPy* projects, called "selections"."""
# import...
# ...from standard library
import copy
import types
from typing import *
# ...from HydPy
import hydpy
from hydpy.core import devicetools
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import typingtools

ModelTypesArg = Union[modeltools.Model, types.ModuleType, str]


class Selections:
    """Collection class for |Selection| objects.

    You can pass an arbitrary number of |Selection| objects to the
    constructor of class |Selections|:

    >>> sel1 = Selection('sel1', ['node1', 'node2'], ['element1'])
    >>> sel2 = Selection('sel2', ['node1', 'node3'], ['element2'])
    >>> selections = Selections(sel1, sel2)
    >>> selections
    Selections("sel1", "sel2")

    Also, you can query, add, and remove |Selection| objects via attribute
    access:

    >>> selections.sel3
    Traceback (most recent call last):
    ...
    AttributeError: The actual Selections object handles neither a normal \
attribute nor a Selection object called `sel3` that could be returned.
    >>> sel3 = Selection('sel3', ['node1', 'node4'], ['element3'])
    >>> selections.sel3 = sel3
    >>> selections.sel3
    Selection("sel3",
              nodes=("node1", "node4"),
              elements="element3")
    >>> 'sel3' in dir(selections)
    True
    >>> del selections.sel3
    >>> 'sel3' in dir(selections)
    False
    >>> del selections.sel3
    Traceback (most recent call last):
    ...
    AttributeError: The actual Selections object handles neither a normal \
attribute nor a Selection object called `sel3` that could be deleted.

    Attribute names must be consistent with the `name` attribute of the
    respective |Selection| object:

    >>> selections.sel4 = sel3
    Traceback (most recent call last):
    ...
    ValueError: To avoid inconsistencies when handling Selection objects as \
attributes of a Selections object, attribute name and Selection name must be \
identical.  However,  for selection `sel3` the given attribute name is `sel4`.

    You can use item access alternatively:

    >>> selections['sel4']
    Traceback (most recent call last):
    ...
    KeyError: 'The actual Selections object does not handle a Selection \
object called `sel4` that could be returned.'
    >>> selections['sel4'] = Selection('sel4')
    >>> selections['sel4']
    Selection("sel4",
              nodes=(),
              elements=())
    >>> del selections['sel4']
    >>> del selections['sel4']
    Traceback (most recent call last):
    ...
    KeyError: 'The actual Selections object does not handle a Selection \
object called `sel4` that could be deleted.'

    You can ask for the existence of a specific |Selection| objects within
    a |Selections| object both via its name and via the object itself:

    >>> sel1 in selections
    True
    >>> 'sel1' in selections
    True
    >>> sel3 in selections
    False
    >>> 'sel3' in selections
    False

    Class |Selections| supports both the |iter| and |len| operator:

    >>> for selection in selections:
    ...     print(selection.name)
    sel1
    sel2
    >>> len(selections)
    2

    For convenience, use the "+", "-", "+=", and "-=" operators to
    compare and modify |Selections| objects either based on single
    |Selection| objects or collections of |Selection| objects

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

    Note that trying to remove non-existing |Selection| objects does not
    raise errors:

    >>> smaller -= sel2
    >>> smaller.names
    ('sel3',)
    >>> smaller - (sel1, sel2, sel3)
    Selections()

    The binary operators do not support other types than the mentioned ones:

    >>> smaller -= 'sel3'
    Traceback (most recent call last):
    ...
    TypeError: Binary operations on Selections objects are defined for other \
Selections objects, single Selection objects, or iterables containing \
`Selection` objects, but the type of the given argument is `str`.
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

    def __init__(self, *selections: 'Selection'):
        self.__selections: Dict[str, 'Selection'] = {}
        for selection in selections:
            self += selection

    @property
    def names(self) -> Tuple[str, ...]:
        """A |tuple| containing the names of the actual |Selection| objects.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection('sel1', ['node1', 'node2'], ['element1']),
        ...     Selection('sel2', ['node1', 'node3'], ['element2']))
        >>> sorted(selections.names)
        ['sel1', 'sel2']
        """
        return tuple(self.__selections.keys())

    @property
    def nodes(self) -> devicetools.Nodes:
        """A |set| containing the |Node| objects of all handled
        |Selection| objects.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection('sel1', ['node1', 'node2'], ['element1']),
        ...     Selection('sel2', ['node1', 'node3'], ['element2']))
        >>> selections.nodes
        Nodes("node1", "node2", "node3")
        """
        nodes = devicetools.Nodes()
        for selection in self:
            nodes += selection.nodes
        return nodes

    @property
    def elements(self) -> devicetools.Elements:
        """A |set| containing the |Node| objects of all handled
        |Selection| objects.

        >>> from hydpy import Selection, Selections
        >>> selections = Selections(
        ...     Selection('sel1', ['node1'], ['element1']),
        ...     Selection('sel2', ['node1'], ['element2', 'element3']))
        >>> selections.elements
        Elements("element1", "element2", "element3")
        """
        elements = devicetools.Elements()
        for selection in self:
            elements += selection.elements
        return elements

    def __getattr__(self, key):
        try:
            return self.__selections[key]
        except KeyError:
            raise AttributeError(
                f'The actual Selections object handles neither a normal '
                f'attribute nor a Selection object called `{key}` that '
                f'could be returned.')

    def __setattr__(self, name, value):
        if isinstance(value, Selection):
            self[name] = value
        else:
            super().__setattr__(name, value)

    def __delattr__(self, key):
        try:
            del self.__selections[key]
        except KeyError:
            raise AttributeError(
                f'The actual Selections object handles neither a normal '
                f'attribute nor a Selection object called `{key}` that '
                f'could be deleted.')

    def __getitem__(self, key: str) -> 'Selection':
        try:
            return self.__selections[key]
        except KeyError:
            raise KeyError(
                f'The actual Selections object does not handle '
                f'a Selection object called `{key}` that could '
                f'be returned.')

    def __setitem__(self, key: 'str', value: 'Selection') -> None:
        if key != value.name:
            raise ValueError(
                f'To avoid inconsistencies when handling Selection '
                f'objects as attributes of a Selections object, '
                f'attribute name and Selection name must be identical.  '
                f'However,  for selection `{value.name}` the given '
                f'attribute name is `{key}`.')
        self.__selections[key] = value

    def __delitem__(self, key: str) -> None:
        try:
            del self.__selections[key]
        except KeyError:
            raise KeyError(
                f'The actual Selections object does not handle '
                f'a Selection object called `{key}` that could '
                f'be deleted.')

    def __contains__(self, value: Union[str, 'Selection']) -> bool:
        try:
            return value in self.__selections.values()
        except AttributeError:
            return value in self.names

    def __iter__(self) -> Iterator['Selection']:
        return iter(self.__selections.values())

    def __len__(self) -> int:
        return len(self.__selections)

    @staticmethod
    def __getiterable(value: typingtools.Mayberable1['Selection']) \
            -> List['Selection']:
        """Try to convert the given argument to a |list| of  |Selection|
        objects and return it.
        """
        try:
            return list(objecttools.extract(value, (Selection,)))
        except TypeError:
            raise TypeError(
                f'Binary operations on Selections objects are defined for '
                f'other Selections objects, single Selection objects, or '
                f'iterables containing `Selection` objects, but the type of '
                f'the given argument is `{objecttools.classname(value)}`.')

    def __add__(self, other: typingtools.Mayberable1['Selection']) \
            -> 'Selections':
        selections = self.__getiterable(other)
        new = copy.copy(self)
        for selection in selections:
            setattr(new, selection.name, selection)
        return new

    def __iadd__(self, other: typingtools.Mayberable1['Selection']) \
            -> 'Selections':
        selections = self.__getiterable(other)
        for selection in selections:
            setattr(self, selection.name, selection)
        return self

    def __sub__(self, other: typingtools.Mayberable1['Selection']) \
            -> 'Selections':
        selections = self.__getiterable(other)
        new = copy.copy(self)
        for selection in selections:
            try:
                delattr(new, selection.name)
            except AttributeError:
                pass
        return new

    def __isub__(self, other: typingtools.Mayberable1['Selection']) \
            -> 'Selections':
        selections = self.__getiterable(other)
        for selection in selections:
            try:
                delattr(self, selection.name)
            except AttributeError:
                pass
        return self

    def __eq__(self, other: Any) -> bool:
        try:
            return ((self.nodes == self.nodes) and
                    (self.elements == other.elements))
        except AttributeError:
            pass
        return False

    def __copy__(self) -> 'Selections':
        return type(self)(*self.__selections.values())

    def __repr__(self) -> str:
        return self.assignrepr('')

    def assignrepr(self, prefix='') -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            with hydpy.pub.options.ellipsis(2, optional=True):
                prefix += '%s(' % objecttools.classname(self)
                repr_ = objecttools.assignrepr_values(
                    sorted(self.names), prefix, 70)
                return repr_ + ')'

    def __dir__(self) -> List[str]:
        return objecttools.dir_(self) + list(self.names)


class Selection:
    """Handles and modifies combinations of |Node| and |Element| objects.

    In *HydPy* |Node| and |Element| objects are the fundamental means
    to structure projects.  However, to keep the overview of huge projects
    involving thousands of nodes and elements requires additional strategies.

    One such strategy is to define different instances of class |Selection|
    for different aspects of a project.  Often, a selection contains all
    nodes and elements of a certain subcatchment or all elements handling
    certain model types. Selections can be overlapping, meaning, for
    example, that an element can be part of a subcatchment selection and
    of model-type selection at the same time.

    Selections can be written to and read from individual network files,
    as explained in the documentation on class |NetworkManager|.  Read
    selections are available via the |pub| module.  In most application
    scripts (e.g. for parameter calibration), one performs different
    operations on the nodes and elements of the different selections
    (e.g. change parameter "a" and "b" for models of selection "x" and "y",
    respectively).  However, class |Selection| also provides features for
    creating combinations of |Node| and |Element| objects suitable for
    different tasks, as explained in the documentation of the respective
    methods.  Here we only show its basic usage with the help of the `LahnH`
    example project prepared by function |prepare_full_example_2|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> _, pub, _ = prepare_full_example_2()

    For example, `LahnH` defines a `headwaters` selection:

    >>> pub.selections.headwaters
    Selection("headwaters",
              nodes=("dill", "lahn_1"),
              elements=("land_dill", "land_lahn_1"))

    You can compare this selection with other new or already available
    selections, with "headwaters < complete" returning |True| meaning that
    all nodes and elements of the headwater catchments are also part of
    the entire catchment:

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

    The |len| operator returns the total number of handled node and
    element objects:

    >>> len(test)
    4

    Use the "+=" and "-=" operators to add or remove nodes and elements:

    >>> test += pub.selections.complete
    >>> len(test)
    11
    >>> test -= pub.selections.complete
    >>> len(test)
    0

    Passing a wrong argument to the binary operators results in errors
    like the following:

    >>> test += 1
    Traceback (most recent call last):
    ...
    AttributeError: While trying to add selection `test` with object `1` of \
type `int`, the following error occurred: 'int' object has no attribute 'nodes'
    >>> test -= pub.selections.complete.nodes.dill
    Traceback (most recent call last):
    ...
    AttributeError: While trying to subtract selection `test` with object \
`dill` of type `Node`, the following error occurred: 'Node' object has no \
attribute 'nodes'
    >>> test == 'wrong'
    Traceback (most recent call last):
    ...
    AttributeError: While trying to compare selection `test` with object \
`wrong` of type `str`, the following error occurred: 'str' object has no \
attribute 'nodes'

    Applying the |str| function only returns the selection name:

    >>> str(test)
    'test'
    """
    def __init__(self, name: str,
                 nodes: devicetools.NodesConstrArg = None,
                 elements: devicetools.ElementsConstrArg = None):
        self.name = str(name)
        self.nodes = devicetools.Nodes(nodes).copy()
        self.elements = devicetools.Elements(elements).copy()

    def search_upstream(self, device: devicetools.Device,
                        name: str = 'upstream') -> 'Selection':
        """Return the network upstream of the given starting point, including
        the starting point itself.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        You can pass both |Node| and |Element| objects and, optionally,
        the name of the newly created |Selection| object:

        >>> test = pub.selections.complete.copy('test')
        >>> test.search_upstream(hp.nodes.lahn_2)
        Selection("upstream",
                  nodes=("dill", "lahn_1", "lahn_2"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "stream_dill_lahn_2", "stream_lahn_1_lahn_2"))
        >>> test.search_upstream(
        ...     hp.elements.stream_lahn_1_lahn_2, 'UPSTREAM')
        Selection("UPSTREAM",
                  nodes="lahn_1",
                  elements=("land_lahn_1", "stream_lahn_1_lahn_2"))

        Wrong device specifications result in errors like the following:

        >>> test.search_upstream(1)
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine the upstream network of \
selection `test`, the following error occurred: Either a `Node` or \
an `Element` object is required as the "outlet device", but the given \
`device` value is of type `int`.

        >>> pub.selections.headwaters.search_upstream(hp.nodes.lahn_3)
        Traceback (most recent call last):
        ...
        KeyError: "While trying to determine the upstream network of \
selection `headwaters`, the following error occurred: 'No node named \
`lahn_3` available.'"

        Method |Selection.select_upstream| restricts the current selection
        to the one determined with the method |Selection.search_upstream|:

        >>> test.select_upstream(hp.nodes.lahn_2)
        Selection("test",
                  nodes=("dill", "lahn_1", "lahn_2"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "stream_dill_lahn_2", "stream_lahn_1_lahn_2"))

        On the contrary, the method |Selection.deselect_upstream| restricts
        the current selection to all devices not determined by method
        |Selection.search_upstream|:

        >>> complete = pub.selections.complete.deselect_upstream(
        ...     hp.nodes.lahn_2)
        >>> complete
        Selection("complete",
                  nodes="lahn_3",
                  elements=("land_lahn_3", "stream_lahn_2_lahn_3"))

        If necessary, include the "outlet device" manually afterwards:

        >>> complete.nodes += hp.nodes.lahn_2
        >>> complete
        Selection("complete",
                  nodes=("lahn_2", "lahn_3"),
                  elements=("land_lahn_3", "stream_lahn_2_lahn_3"))
        """
        try:
            selection = Selection(name)
            if isinstance(device, devicetools.Node):
                node = self.nodes[device.name]
                return self.__get_nextnode(node, selection)
            if isinstance(device, devicetools.Element):
                element = self.elements[device.name]
                return self.__get_nextelement(element, selection)
            raise TypeError(
                f'Either a `Node` or an `Element` object is required '
                f'as the "outlet device", but the given `device` value '
                f'is of type `{objecttools.classname(device)}`.')
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to determine the upstream network of '
                f'selection `{self.name}`')

    def __get_nextnode(self, node, selection):
        if (node not in selection.nodes) and (node in self.nodes):
            selection.nodes += node
            for element in node.entries:
                selection = self.__get_nextelement(element, selection)
        return selection

    def __get_nextelement(self, element, selection):
        if (element not in selection.elements) and (element in self.elements):
            selection.elements += element
            for node in element.inlets:
                selection = self.__get_nextnode(node, selection)
        return selection

    def select_upstream(self, device: devicetools.Device) -> 'Selection':
        """Restrict the current selection to the network upstream of the given
        starting point, including the starting point itself.

        See the documentation on method |Selection.search_upstream| for
        additional information.
        """
        upstream = self.search_upstream(device)
        self.nodes = upstream.nodes
        self.elements = upstream.elements
        return self

    def deselect_upstream(self, device: devicetools.Device) -> 'Selection':
        """Remove the network upstream of the given starting point from the
        current selection, including the starting point itself.

        See the documentation on method |Selection.search_upstream| for
        additional information.
        """
        upstream = self.search_upstream(device)
        self.nodes -= upstream.nodes
        self.elements -= upstream.elements
        return self

    def search_modeltypes(self, *models: ModelTypesArg,
                          name: str = 'modeltypes') -> 'Selection':
        """Return a |Selection| object containing only the elements
        currently handling models of the given types.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        You can pass both |Model| objects and names and, as a keyword
        argument, the name of the newly created |Selection| object:

        >>> test = pub.selections.complete.copy('test')
        >>> from hydpy import prepare_model
        >>> hland_v1 = prepare_model('hland_v1')

        >>> test.search_modeltypes(hland_v1)
        Selection("modeltypes",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3"))
        >>> test.search_modeltypes(
        ...     hland_v1, 'hstream_v1', 'lland_v1', name='MODELTYPES')
        Selection("MODELTYPES",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

        Wrong model specifications result in errors like the following:

        >>> test.search_modeltypes('wrong')
        Traceback (most recent call last):
        ...
        ModuleNotFoundError: While trying to determine the elements of \
selection `test` handling the model defined by the argument(s) `wrong` \
of type(s) `str`, the following error occurred: \
No module named 'hydpy.models.wrong'

        Method |Selection.select_modeltypes| restricts the current selection to
        the one determined with the method the |Selection.search_modeltypes|:

        >>> test.select_modeltypes(hland_v1)
        Selection("test",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3"))

        On the contrary, the method |Selection.deselect_upstream| restricts
        the current selection to all devices not determined by method the
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
            return selection
        except BaseException:
            values = objecttools.enumeration(models)
            classes = objecttools.enumeration(
                objecttools.classname(model) for model in models)
            objecttools.augment_excmessage(
                f'While trying to determine the elements of selection '
                f'`{self.name}` handling the model defined by the '
                f'argument(s) `{values}` of type(s) `{classes}`')

    def select_modeltypes(self, *models: ModelTypesArg) -> 'Selection':
        """Restrict the current |Selection| object to all elements
        containing the given model types (removes all nodes).

        See the documentation on method |Selection.search_modeltypes| for
        additional information.
        """
        self.nodes = devicetools.Nodes()
        self.elements = self.search_modeltypes(*models).elements
        return self

    def deselect_modeltypes(self, *models: ModelTypesArg) -> 'Selection':
        """Restrict the current selection to all elements not containing the
        given model types (removes all nodes).

        See the documentation on method |Selection.search_modeltypes| for
        additional information.
        """
        self.nodes = devicetools.Nodes()
        self.elements -= self.search_modeltypes(*models).elements
        return self

    def search_nodenames(self, *substrings: str, name: str = 'nodenames') -> \
            'Selection':
        """Return a new selection containing all nodes of the current
        selection with a name containing at least one of the given substrings.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        Pass the (sub)strings as positional arguments and, optionally, the
        name of the newly created |Selection| object as a keyword argument:

        >>> test = pub.selections.complete.copy('test')
        >>> from hydpy import prepare_model
        >>> test.search_nodenames('dill', 'lahn_1')
        Selection("nodenames",
                  nodes=("dill", "lahn_1"),
                  elements=())

        Wrong string specifications result in errors like the following:

        >>> test.search_nodenames(['dill', 'lahn_1'])
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine the nodes of selection \
`test` with names containing at least one of the given substrings \
`['dill', 'lahn_1']`, the following error occurred: 'in <string>' \
requires string as left operand, not list

        Method |Selection.select_nodenames| restricts the current selection
        to the one determined with the the method |Selection.search_nodenames|:

        >>> test.select_nodenames('dill', 'lahn_1')
        Selection("test",
                  nodes=("dill", "lahn_1"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

        On the contrary, the method |Selection.deselect_nodenames| restricts
        the current selection to all devices not determined by the method
        |Selection.search_nodenames|:

        >>> pub.selections.complete.deselect_nodenames('dill', 'lahn_1')
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
            return selection
        except BaseException:
            values = objecttools.enumeration(substrings)
            objecttools.augment_excmessage(
                f'While trying to determine the nodes of selection '
                f'`{self.name}` with names containing at least one '
                f'of the given substrings `{values}`')

    def select_nodenames(self, *substrings: str) -> 'Selection':
        """Restrict the current selection to all nodes with a name
        containing at least one of the given substrings  (does not
        affect any elements).

        See the documentation on method |Selection.search_nodenames| for
        additional information.
        """
        self.nodes = self.search_nodenames(*substrings).nodes
        return self

    def deselect_nodenames(self, *substrings: str) -> 'Selection':
        """Restrict the current selection to all nodes with a name
        not containing at least one of the given substrings (does not
        affect any elements).

        See the documentation on method |Selection.search_nodenames| for
        additional information.
        """
        self.nodes -= self.search_nodenames(*substrings).nodes
        return self

    def search_elementnames(self, *substrings: str,
                            name: str = 'elementnames') -> 'Selection':
        """Return a new selection containing all elements of the current
        selection with a name containing at least one of the given substrings.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        Pass the (sub)strings as positional arguments and, optionally, the
        name of the newly created |Selection| object as a keyword argument:

        >>> test = pub.selections.complete.copy('test')
        >>> from hydpy import prepare_model
        >>> test.search_elementnames('dill', 'lahn_1')
        Selection("elementnames",
                  nodes=(),
                  elements=("land_dill", "land_lahn_1", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2"))

        Wrong string specifications result in errors like the following:

        >>> test.search_elementnames(['dill', 'lahn_1'])
        Traceback (most recent call last):
        ...
        TypeError: While trying to determine the elements of selection \
`test` with names containing at least one of the given substrings \
`['dill', 'lahn_1']`, the following error occurred: 'in <string>' \
requires string as left operand, not list

        Method |Selection.select_elementnames| restricts the current selection
        to the one determined with the method |Selection.search_elementnames|:

        >>> test.select_elementnames('dill', 'lahn_1')
        Selection("test",
                  nodes=("dill", "lahn_1", "lahn_2", "lahn_3"),
                  elements=("land_dill", "land_lahn_1", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2"))

        On the contrary, the method |Selection.deselect_elementnames|
        restricts the current selection to all devices not determined
        by the method |Selection.search_elementnames|:

        >>> pub.selections.complete.deselect_elementnames('dill', 'lahn_1')
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
            return selection
        except BaseException:
            values = objecttools.enumeration(substrings)
            objecttools.augment_excmessage(
                f'While trying to determine the elements of selection '
                f'`{self.name}` with names containing at least one '
                f'of the given substrings `{values}`')

    def select_elementnames(self, *substrings: str) -> 'Selection':
        """Restrict the current selection to all elements with a name
        containing at least one of the given substrings (does not
        affect any nodes).

        See the documentation on method |Selection.search_elementnames| for
        additional information.
        """
        self.elements = self.search_elementnames(*substrings).elements
        return self

    def deselect_elementnames(self, *substrings: str) -> 'Selection':
        """Restrict the current selection to all elements with a name
        not containing at least one of the given substrings.   (does
        not affect any nodes).

        See the documentation on method |Selection.search_elementnames| for
        additional information.
        """
        self.elements -= self.search_elementnames(*substrings).elements
        return self

    def copy(self, name: str) -> 'Selection':
        """Return a new |Selection| object with the given name and copies
        of the handles |Nodes| and |Elements| objects based on method
        |Devices.copy|."""
        return type(self)(name, copy.copy(self.nodes), copy.copy(self.elements))

    def save_networkfile(self, filepath: Union[str, None] = None,
                         write_nodes: bool = True) -> None:
        """Save the selection as a network file.

        >>> from hydpy.examples import prepare_full_example_2
        >>> _, pub, TestIO = prepare_full_example_2()

        In most cases, one should conveniently write network files via method
        |NetworkManager.save_files| of class |NetworkManager|.  However,
        using the method |Selection.save_networkfile| allows for additional
        configuration via the arguments `filepath` and `write_nodes`:

        >>> with TestIO():
        ...     pub.selections.headwaters.save_networkfile()
        ...     with open('headwaters.py') as networkfile:
        ...         print(networkfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy import Node, Element
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
        ...     pub.selections.headwaters.save_networkfile('test.py', False)
        ...     with open('test.py') as networkfile:
        ...         print(networkfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy import Node, Element
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
        if filepath is None:
            filepath = self.name + '.py'
        with open(filepath, 'w', encoding="utf-8") as file_:
            file_.write('# -*- coding: utf-8 -*-\n')
            file_.write('\nfrom hydpy import Node, Element\n\n')
            if write_nodes:
                for node in self.nodes:
                    file_.write('\n' + repr(node) + '\n')
                file_.write('\n')
            for element in self.elements:
                file_.write('\n' + repr(element) + '\n')

    def __len__(self) -> int:
        return len(self.nodes) + len(self.elements)

    _ERRORMESSAGE = ('selection `{self.name}` with object `{other}` '
                     'of type `{classname(other)}`')

    @objecttools.excmessage_decorator('add '+_ERRORMESSAGE)
    def __iadd__(self, other: typingtools.DevicesHandlerProtocol) \
            -> 'Selection':
        self.nodes += other.nodes
        self.elements += other.elements
        return self

    @objecttools.excmessage_decorator('subtract ' + _ERRORMESSAGE)
    def __isub__(self, other: typingtools.DevicesHandlerProtocol) \
            -> 'Selection':
        self.nodes -= other.nodes
        self.elements -= other.elements
        return self

    @objecttools.excmessage_decorator('compare ' + _ERRORMESSAGE)
    def __lt__(self, other: typingtools.DevicesHandlerProtocol) -> bool:
        return ((self.nodes < other.nodes) and
                (self.elements < other.elements))

    @objecttools.excmessage_decorator('compare ' + _ERRORMESSAGE)
    def __le__(self, other: typingtools.DevicesHandlerProtocol) -> bool:
        return ((self.nodes <= other.nodes) and
                (self.elements <= other.elements))

    @objecttools.excmessage_decorator('compare ' + _ERRORMESSAGE)
    def __eq__(self, other: typingtools.DevicesHandlerProtocol) -> bool:
        return ((self.nodes == other.nodes) and
                (self.elements == other.elements))

    @objecttools.excmessage_decorator('compare ' + _ERRORMESSAGE)
    def __ne__(self, other: typingtools.DevicesHandlerProtocol) -> bool:
        return ((self.nodes != other.nodes) or
                (self.elements != other.elements))

    @objecttools.excmessage_decorator('compare ' + _ERRORMESSAGE)
    def __ge__(self, other: typingtools.DevicesHandlerProtocol) -> bool:
        return ((self.nodes >= other.nodes) and
                (self.elements >= other.elements))

    @objecttools.excmessage_decorator('compare ' + _ERRORMESSAGE)
    def __gt__(self, other: typingtools.DevicesHandlerProtocol) -> bool:
        return ((self.nodes > other.nodes) and
                (self.elements >= other.elements))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.assignrepr('')

    def assignrepr(self, prefix: str) -> str:
        """Return a |repr| string with a prefixed assignment."""
        with objecttools.repr_.preserve_strings(True):
            with hydpy.pub.options.ellipsis(2, optional=True):
                with objecttools.assignrepr_tuple.always_bracketed(False):
                    classname = objecttools.classname(self)
                    blanks = ' ' * (len(prefix+classname) + 1)
                    nodestr = objecttools.assignrepr_tuple(
                        self.nodes.names, blanks+'nodes=', 70)
                    elementstr = objecttools.assignrepr_tuple(
                        self.elements.names, blanks + 'elements=', 70)
                    return (f'{prefix}{classname}("{self.name}",\n'
                            f'{nodestr},\n'
                            f'{elementstr})')

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy import Selection
        >>> 'elements' in dir(Selection('test'))
        True
        """
        return objecttools.dir_(self)
