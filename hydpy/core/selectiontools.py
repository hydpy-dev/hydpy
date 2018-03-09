# -*- coding: utf-8 -*-
"""This module implements tools for selecting certain models in large
HydPy projects.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import os
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import devicetools
from hydpy.core import autodoctools
from hydpy.core import magictools


class Selections(object):
    """Collects :class:`Selection` instances.

    Attributes:
        * ? (:class:`Selection`): An arbitrary number of :class:`Selection`
          objects, which can be added (and removed) on demand.  Choose
          attribute names that are meaningfull within your specific project.
    """

    def __init__(self, *selections):
        for selection in selections:
            self += selection

    @property
    def names(self):
        """Names of the actual selections."""
        return tuple(vars(self).keys())

    def save(self, path='', write_nodes=False):
        """Save all selections in seperate network files."""
        for selection in self:
            fullpath = os.path.join(path, selection.name+'.py')
            selection.save(fullpath, write_nodes)

    def _getselections(self):
        """The actual selections themselves."""
        return tuple(vars(self).values())

    selections = property(_getselections)

    @magictools.printprogress
    def prepare_shapes(self):
        """Prepare the shapes of all element and node objects."""
        self.complete.load_shapes()
        for (name, selection) in self:
            selection.norm_shapes()

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del(self.__dict__[key])

    def __contains__(self, value):
        if isinstance(value, Selection):
            return value in self.selections
        else:
            return value in self.names

    def __iter__(self):
        for (name, selection) in sorted(vars(self).items()):
            yield selection

    def __len__(self):
        return len(self.names)

    @staticmethod
    def _getiterable(value):
        """Tries to convert the given argument to a :class:`list` of
        :class:`Selection` objects and returns it.

        Argument:
            * value (:class:`Selection`, :class:`Selections` of a simple
            iterable containing :class:`Selection` objects): The second
            operand applied in an arithmetic operation.
        """
        if isinstance(value, Selection):
            return [value]
        elif isinstance(value, Selections):
            return value.selections
        else:
            try:
                for selection in value:
                    selection.name
                    break
                return list(value)
            except (KeyError, AttributeError):
                raise TypeError('Arithmetic operations on `Selections` '
                                'objects are defined for other `Selections` '
                                'objects, single `Selection` objects or '
                                'simple iterables (like `list` objects) '
                                'containing `Selection` objects only.  The '
                                'given arguments type is `%s`.'
                                % type(value))

    def __add__(self, value):
        selections = self._getiterable(value)
        new = self.copy()
        for selection in selections:
            new[selection.name] = selection
        return new

    def __iadd__(self, value):
        selections = self._getiterable(value)
        for selection in selections:
            self[selection.name] = selection
        return self

    def __sub__(self, value):
        selections = self._getiterable(value)
        new = self.copy()
        for selection in selections:
            try:
                del(new[selection.name])
            except KeyError:
                pass
        return new

    def __isub__(self, value):
        selections = self._getiterable(value)
        for selection in selections:
            try:
                del(self[selection.name])
            except KeyError:
                pass
        return self

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        """Return a :func:`repr` string with an prefixed assignement.

        Argument:
            * prefix(:class:`str`): Usually something like 'x = '.
        """
        with objecttools.repr_.preserve_strings(True):
            with pub.options.ellipsis(2, optional=True):
                prefix += '%s(' % objecttools.classname(self)
                repr_ = objecttools.assignrepr_values(self.names, prefix, 70)
                return repr_ + ')'

    def __dir__(self):
        return ['names', 'selections', 'assignrepr'] + list(self.names)


class Selection(object):
    """Defines a combination of :class:`~hydpy.core.node.Node` and
    :class:`~hydpy.core.element.Element` objects suitable for a
    specific task.

    Attributes:
        * name (:class:`str`): Name of the selection.
        * nodes (|Nodes|): Currently selected nodes.
        * elements (|Elements|): Currently selected elements.
    """

    def __init__(self, name, nodes=None, elements=None):
        self.name = name
        self.nodes = devicetools.Nodes(nodes)
        self.elements = devicetools.Elements(elements)
        self.shapes = {}

    def select_upstream(self, device):
        """Limit the current selection to the network upstream of the given
        starting point, including the starting point itself.

        Argument:
            * device (:class:`~hydpy.core.devicetools.Node` or
              :class:`~hydpy.core.devicetools.Element`): Lowest point
              to be selected.
        """
        self.nodes, self.elements = self.getby_upstream(device)
        return self

    def deselect_upstream(self, device):
        """Remove the network upstream of the given starting point from the
        current selection, including the starting point itself.

        Argument:
            * device (:class:`~hydpy.core.devicetools.Node` or
              :class:`~hydpy.core.devicetools.Element`): Highest point
              to be deselected.
        """
        nodes, elements = self.getby_upstream(device)
        self.nodes -= nodes
        self.elements -= elements
        return self

    def getby_upstream(self, device):
        """Returns the network upstream of the given starting point, including
        the starting point itself.

        Argument:
            * device (:class:`~hydpy.core.devicetools.Node` or
              :class:`~hydpy.core.devicetools.Element`): Lowest point
              to be selected.
        """
        nodes = devicetools.Nodes()
        elements = devicetools.Elements()
        if isinstance(device, devicetools.Node):
            nodes, elements = self._nextnode(device, nodes, elements)
        elif isinstance(device, devicetools.Element):
            nodes, elements = self._nextelement(device, nodes, elements)
        else:
            raise AttributeError('Pass either a `Node` or an `Element` '
                                 'instance to the function.  The given '
                                 '`device` value `%s` is of type `%s`.'
                                 % (device, type(device)))
        return nodes, elements

    def _nextnode(self, node, nodes, elements):
        """First recursion method for :func:`~Selection.getupstreamnetwork`.

        Arguments:
            * node (:class:`~hydpy.core.devicetools.Node`): The node which
              is selected currently.
            * nodes (:class:`~hydpy.core.devicetools.Nodes`): All nodes
            which have been selected so far.
            * elements (:class:`~hydpy.core.devicetools.Elements`): All
            elements which have been selected so far.
        """
        if (node not in nodes) and (node in self.nodes):
            nodes += node
            for element in node.entries:
                nodes, elements = self._nextelement(element, nodes, elements)
        return nodes, elements

    def _nextelement(self, element, nodes, elements):
        """Second recursion method for :func:`~Selection.getupstreamnetwork`.

        Arguments:
            * element (:class:`~hydpy.core.devicetools.Element`): The
              element which is selected currently.
            * nodes (:class:`~hydpy.core.devicetools.Nodes`): All nodes
            which have been selected so far.
            * elements (:class:`~hydpy.core.devicetools.Elements`): All
            elements which have been selected so far.
        """
        if (element not in elements) and (element in self.elements):
            elements += element
            for node in element.inlets:
                nodes, elements = self._nextnode(node, nodes, elements)
        return nodes, elements

    def select_modelclasses(self, *modelclass):
        """Limits the current selection to all elements containing the
        given modelclass(es).  (All nodes are removed.)

        Argument:
            * modelclass (subclass of :class:`~hydpy.core.models.Model`):
              Model type(s) as the selection criterion/criteria.
        """
        self.nodes = devicetools.Nodes()
        self.elements = self.getby_modelclasses(modelclass)
        return self

    def deselect_modelclasses(self, *modelclasses):
        """Limits the current selection to all elements not containing the
        given modelclass(es).  (All nodes are removed.)

        Argument:
            * modelclass (subclass of :class:`~hydpy.core.models.Model`):
              Model type(s) as the selection criterion/criteria.
        """
        self.nodes = devicetools.Nodes()
        self.elements -= self.getby_modelclasses(*modelclasses)
        return self

    def getby_modelclasses(self, *modelclasses):
        """Returns all elements of the current selection containing the given
        modelclass(es).

        Argument:
            * modelclass (subclass of :class:`~hydpy.core.models.Model`):
              Model type(s) as the selection criterion/criteria.
        """
        elements = devicetools.Elements()
        for element in self.elements:
            if element.model is None:
                raise RuntimeError('For element `%s` no model object has been '
                                   'initialized so far, which is a necessary '
                                   'condition to perform (de)selections based '
                                   'on model classes.' % element)
            if isinstance(element.model, modelclasses):
                elements += element
        return elements

    def select_nodenames(self, *substrings):
        """Limits the current selection to all nodes with a name
        containing the given substring(s).  (All elements are unaffected.)

        Argument:
            * substrings (:class:`str`): (Possible) Part(s) of the nodes
              name as the selection criterion/criteria.
        """
        self.nodes = self.getby_nodenames(*substrings)
        return self

    def deselect_nodenames(self, *substrings):
        """Limits the current selection to all nodes with a name
        not containing the given substring(s).  (All elements are unaffected.)

        Argument:
            * substrings (:class:`str`): (Possible) Part(s) of the nodes
              name as the selection criterion/criteria.
        """
        self.nodes -= self.getby_nodenames(*substrings)
        return self

    def getby_nodenames(self, *substrings):
        """Returns all nodes of the current selection with a name
        containing the given substrings(s).

        Argument:
            * substrings (:class:`str`): (Possible) Part(s) of the nodes
              name as the selection criterion/criteria.
        """
        nodes = devicetools.Nodes()
        for node in self.nodes:
            for substring in substrings:
                if substring in node.name:
                    nodes += node
                    break
        return nodes

    def select_elementnames(self, *substrings):
        """Limits the current selection to all elements with a name
        containing the given substring(s).  (All nodes are unaffected.)

        Argument:
            * substrings (:class:`str`): (Possible) Part(s) of the elements
              name as the selection criterion/criteria.
        """
        self.elements = self.getby_elementnames(*substrings)
        return self

    def deselect_elementnames(self, *substrings):
        """Limits the current selection to all elements with a name
        not containing the given substring(s).  (All nodes are unaffected.)

        Argument:
            * substrings (:class:`str`): (Possible) Part(s) of the elements
              name as the selection criterion/criteria.
        """
        self.elements -= self.getby_elementnames(*substrings)
        return self

    def getby_elementnames(self, *substrings):
        """Returns all elements of the current selection with a name
        containing the given substrings(s).

        Argument:
            * substrings (:class:`str`): (Possible) Part(s) of the elements
              name as the selection criterion/criteria.
        """
        elements = devicetools.Elements()
        for element in self.elements:
            for substring in substrings:
                if substring in element.name:
                    elements += element
                    break
        return elements

    def copy(self, name):
        """Returns a semi-deep copy of the current selection.

        Arguments:
            * name (:class:`str`): Name of the new :class:`Selection` instance.
        """
        return Selection(name, self.nodes.copy(), self.elements.copy())

    @property
    def devices(self):
        """A tuple of all elements and nodes contained by the selection
        object."""
        return tuple(list(self.elements.devices)+list(self.nodes.devices))

    @magictools.printprogress
    def prepare_shapes(self):
        """Prepare the shapes of all element and node objects."""
        self.load_shapes()
        self.norm_shapes()

    @magictools.printprogress
    def load_shapes(self):
        """Load the shapes of all element and node objects."""
        for device in magictools.progressbar(self.devices):
            device.load_shape()

    @property
    def shapebounds(self):
        """A tuple containing the total `xmin`, `ymin`, `xmax` and `ymax`
        values of all shapes associated with the different nodes and elements.
        """
        xmin, ymin = numpy.inf, numpy.inf
        xmax, ymax = -numpy.inf, -numpy.inf
        for device in self.devices:
            xmin = min(xmin, numpy.min(device.shape.xs_orig))
            xmax = max(xmax, numpy.max(device.shape.xs_orig))
            ymin = min(ymin, numpy.min(device.shape.ys_orig))
            ymax = max(ymax, numpy.max(device.shape.ys_orig))
        return xmin, ymin, xmax, ymax

    @magictools.printprogress
    def norm_shapes(self):
        """Load the shapes of all element and node objects."""
        shapebounds = self.shapebounds
        for device in magictools.progressbar(self.devices):
            self.shapes[device.name] = device.shape.normed_shape(*shapebounds)

    def save(self, path=None, write_nodes=False):
        """Save the selection as a network file."""
        if path is None:
            path = self.name + '.py'
        with open(path, 'w', encoding="utf-8") as file_:
            file_.write('# -*- coding: utf-8 -*-\n')
            file_.write('\nfrom hydpy import Node, Element\n\n')
            if write_nodes:
                for node in self.nodes:
                    file_.write('\n' + repr(node) + '\n')
                file_.write('\n')
            for element in self.elements:
                file_.write('\n' + repr(element) + '\n')

    def __len__(self):
        return len(self.nodes) + len(self.elements)

    def __iadd__(self, other):
        self.nodes += other.nodes
        self.elements += other.elements
        return self

    def __isub__(self, other):
        self.nodes -= other.nodes
        self.elements -= other.elements
        return self

    def __lt__(self, other):
        return ((self.nodes < other.nodes) and
                (self.elements < other.elements))

    def __le__(self, other):
        return ((self.nodes <= other.nodes) and
                (self.elements <= other.elements))

    def __eq__(self, other):
        return ((self.nodes == other.nodes) and
                (self.elements == other.elements))

    def __ne__(self, other):
        return ((self.nodes != other.nodes) or
                (self.elements != other.elements))

    def __ge__(self, other):
        return ((self.nodes >= other.nodes) and
                (self.elements >= other.elements))

    def __gt__(self, other):
        return ((self.nodes > other.nodes) and
                (self.elements >= other.elements))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        """Return a :func:`repr` string with an prefixed assignement.

        Argument:
            * prefix(:class:`str`): Usually something like 'x = '.
        """
        with objecttools.repr_.preserve_strings(True):
            with pub.options.ellipsis(2, optional=True):
                with objecttools.assignrepr_tuple.always_bracketed(False):
                    prefix = '%sSelection(' % prefix
                    blanks = ' ' * len(prefix)
                    lines = ['%s"%s",' % (prefix, self.name)]
                    lines.append(objecttools.assignrepr_tuple(
                            self.elements.names, blanks+'elements=', 70) + ',')
                    lines.append(objecttools.assignrepr_tuple(
                            self.nodes.names, blanks+'nodes=', 70) + ')')
                    return '\n'.join(lines)

    def __dir__(self):
        return ['copy', 'deselect_elementnames', 'deselect_modelclasses',
                'deselect_nodenames', 'deselect_upstream', 'elements',
                'getby_elementnames', 'getby_modelclasses', 'getby_nodenames',
                'getby_upstream', 'nodes', 'select_elementnames',
                'select_modelclasses', 'select_nodenames', 'select_upstream',
                'assignrepr']


autodoctools.autodoc_module()
