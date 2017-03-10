# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import copy
import struct
# ...from site-packages
from matplotlib import pyplot
# ...from HydPy
from hydpy import pub
from hydpy.core import connectiontools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.cythons import pointer


class Device(object):

    _registry = {}
    _selection = {}

    def _getname(self):
        """Name of the actual device (node or element)."""
        return self._name
    name = property(_getname)

    def _checkname(self, name):
        """Raises an :class:`~exceptions.ValueError` if the given name is not
        a valid Python identifier.
        """
        exc = ValueError('For initializing `%s` objects, `value` is a '
                         'necessary function argument.  Principally, any '
                         'object is allowed that supports the Python build-in '
                         'function `str`.  But note that `str(value)` must '
                         'return a valid Python identifier (that does '
                         'not start with a number, that does not contain `-`, '
                         'that is not a Python keyword like `for`...).  The '
                         'given object returned the string `%s`, which is not '
                         'a valid Python identifier.'
                         % (objecttools.classname(self), name))
        try:
            exec('%s = None' % name)
        except SyntaxError:
            raise exc
        if name in dir(__builtins__):
            raise exc

    @classmethod
    def clearregistry(cls):
        cls._selection.clear()
        cls._registry.clear()

    @classmethod
    def registerednames(cls):
        """Get all names of :class:`Device` objects initialized so far."""
        return cls._registry.keys()

    def __iter__(self):
        for (key, value) in vars(self).items():
            if isinstance(value, connectiontools.Connections):
                yield (key, value)

    def __eq__(self, other):
        return self is self.__class__(other)

    def __ne__(self, other):
        return self is not self.__class__(other)

    def __str__(self):
        return self.name

    def __dir__(self):
        return objecttools.dir_(self)


class Node(Device):
    """
    readobs = False
    readext = False
    passsim = True
    passobs = False
    passext = False
    """
    _registry = {}
    _selection = {}
    _predefinedvariable = 'Q'
    ROUTING_MODES = ('newsim', 'obs', 'oldsim')

    def __new__(cls, value, variable=None):
        """Returns an already existing :class:`Node` instance or, if such
        an instance does not exist yet, a new newly created one.
        """
        name = str(value)
        if name not in cls._registry:
            self = object.__new__(Node)
            self._checkname(name)
            self._name = name
            if variable is None:
                self._variable = self._predefinedvariable
            else:
                self._variable = variable
            self.entries = connectiontools.Connections(self)
            self.exits = connectiontools.Connections(self)
            self.sequences = sequencetools.NodeSequences(self)
            self.routingmode = 'newsim'
            self._blackhole = None
            cls._registry[name] = self
        cls._selection[name] = cls._registry[name]
        return cls._registry[name]

    def __init__(self, name, variable=None, route=None):
        if (variable is not None) and (variable != self.variable):
            raise ValueError('The variable to be represented by a `Node '
                             'instance cannot be changed.  The variable of '
                             'node `%s` is `%s` instead of `%s` or `None`.  '
                             'Keep in mind, that `name` is the unique '
                             'identifier of node objects.'
                             % (self.name, self.variable, variable))

    def _getvariable(self):
        """The variable handled by the respective node instance."""
        return self._variable
    variable = property(_getvariable)

    @classmethod
    def predefinevariable(cls, name):
        cls._predefinedvariable = str(name)

    @classmethod
    def registerednodes(cls):
        """Get all :class:`Node` objects initialized so far."""
        return Nodes(cls._registry.values())

    @classmethod
    def gathernewnodes(cls):
        """Gather all `new` :class:`Node` objects. :class:`Node` objects
        are deemed to be new if their constructor has been called since the
        last usage of this method.
        """
        nodes = Nodes(cls._selection.values())
        cls._selection.clear()
        return nodes

    def _getroutingmode(self):
        return self._routingmode
    def _setroutingmode(self, value):
        if value in self.ROUTING_MODES:
            self._routingmode = value
            if value == 'newsim':
                self.sequences.sim.use_ext = False
            elif value == 'obs':
                self.sequences.sim.use_ext = False
                self.sequences.obs.use_ext = True
            elif value == 'oldsim':
                self.sequences.sim.use_ext = True
                self._blackhole = pointer.Double(0.)
        else:
            raise ValueError('When trying to set the routing mode of node %s, '
                             'the value `%s` was given, but only the '
                             'following values are allowed: %s.'
                             % (self.name, value,
                             ', '.join(self.ROUTING_MODES)))
    routingmode = property(_getroutingmode, _setroutingmode)

    def getdouble_via_exits(self):
        if self.routingmode != 'obs':
            return self.sequences.fastaccess.sim
        else:
            return self.sequences.fastaccess.obs

    def getdouble_via_entries(self):
        if self.routingmode != 'oldsim':
            return self.sequences.fastaccess.sim
        else:
            return self._blackhole

    def reset(self, idx=None):
        self.sequences.fastaccess.sim[0] = 0.

    def _loaddata_sim(self, idx):
        fastaccess = self.sequences.fastaccess
        if fastaccess._sim_ramflag:
            fastaccess.sim[0] = fastaccess._sim_array[idx]
        elif fastaccess._sim_diskflag:
            raw = fastaccess._sim_file.read(8)
            fastaccess.sim[0] = struct.unpack('d', raw)

    def _savedata_sim(self, idx):
        fastaccess = self.sequences.fastaccess
        if fastaccess._sim_ramflag:
            fastaccess._sim_array[idx] = fastaccess.sim[0]
        elif fastaccess._sim_diskflag:
            raw = struct.pack('d', fastaccess.sim[0])
            fastaccess._sim_file.write(raw)

    def _loaddata_obs(self, idx):
        fastaccess = self.sequences.fastaccess
        if fastaccess._obs_ramflag:
            fastaccess.obs[0] = fastaccess._obs_array[idx]
        elif fastaccess._obs_diskflag:
            raw = fastaccess._obs_file.read(8)
            fastaccess.obs[0] = struct.unpack('d', raw)

    def comparisonplot(self, **kwargs):
        for (name, seq) in self.sequences:
            if pyplot.isinteractive():
                name = ' '.join((self.name, name))
            pyplot.plot(seq.series, label=name, **kwargs)
        pyplot.legend()
        variable = self.variable
        if variable == 'Q':
            variable = u'Q [m³/s]'
        pyplot.ylabel(variable)
        if not pyplot.isinteractive():
            pyplot.show()

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        return ('%sNode("%s", variable="%s")'
                % (prefix, self.name, self.variable))



class Element(Device):

    _registry = {}
    _selection = {}

    def __new__(cls, value, inlets=None, outlets=None,
                receivers=None,  senders=None
                ):
        """Returns an already existing :class:`Element` instance or, if such
        an instance does not exist yet, a new newly created one.
        """
        name = str(value)
        if name not in cls._registry:
            self = object.__new__(Element)
            self._checkname(name)
            self._name = name
            self.inlets = connectiontools.Connections(self)
            self.outlets = connectiontools.Connections(self)
            self.receivers = connectiontools.Connections(self)
            self.senders =connectiontools. Connections(self)
            self.model = None
            cls._registry[name] = self
        cls._selection[name] = cls._registry[name]
        return cls._registry[name]

    def __init__(self, name, inlets=None, outlets=None,
                 receivers=None, senders=None
                ):
        """Adds the given :class:`~connectiontools.Connections` instances to
        the (old or new) :class:`Element` instance."""
        if inlets is not None:
            for (name, inlet) in Nodes(inlets):
                if inlet in self.outlets:
                    raise ValueError('For element `%s`, the given inlet node '
                                     '`%s` is already defined as an outlet '
                                     'node, which is not allowed.'
                                     % (self, inlet))
                self.inlets += inlet
                inlet.exits += self
        if outlets is not None:
            for (name, outlet) in Nodes(outlets):
                if outlet in self.inlets:
                    raise ValueError('For element `%s`, the given outlet node '
                                     '`%s` is already defined as an inlet '
                                     'node, which is not allowed.'
                                     % (self, outlet))
                self.outlets += outlet
                outlet.entries += self
        if receivers is not None:
            for (name, receiver) in Nodes(receivers):
                if receiver in self.senders:
                    raise ValueError('For element `%s`, the given receiver '
                                     'node `%s` is already defined as an '
                                     'sender node, which is not allowed.'
                                     % (self, receiver))
                self.receivers += receiver
                receiver.exits += self
        if senders is not None:
            for (name, sender) in Nodes(self.senders):
                if sender in self.receivers:
                    raise ValueError('For element `%s`, the given sender node '
                                     '`%s` is already defined as an receiver, '
                                     'node which is not allowed.'
                                     % (self, sender))
                self.senders += sender
                sender.entries += self

    @classmethod
    def registeredelements(cls):
        """Get all :class:`Element` objects initialized so far."""
        return Elements(cls._registry.values())

    @classmethod
    def gathernewelements(cls):
        """Gather all `new` :class:`Element` objects. :class:`Element` objects
        are deemed to be new if their constructor has been called since the
        last usage of this method.
        """
        elements = Elements(cls._selection.values())
        cls._selection.clear()
        return elements

    def _getvariables(self):
        variables = set()
        for (name, connections) in self:
            variables.update(connections.variables)
        return variables
    variables = property(_getvariables)

    def initmodel(self):
        namespace = pub.controlmanager.loadfile(self.name)
        self.model = namespace['model']
        self.model.element = self

    def connect(self):
        try:
            self.model.connect()
        except AttributeError:
            raise RuntimeError('First init than build')

    def _plot(self, subseqs, selnames, kwargs):
        for name in selnames:
            seq = getattr(subseqs, name)
            if seq.NDIM == 0:
                label = kwargs.pop('label', ' '.join((self.name, name)))
                pyplot.plot(seq.series, label=label, **kwargs)
                pyplot.legend()
            else:
                color = kwargs.pop('color', kwargs.pop('c', 'red'))
                pyplot.plot(seq.series, color=color, **kwargs)
        if not pyplot.isinteractive():
            pyplot.show()

    def inputplot(self, *args, **kwargs):
        self._plot(self.model.sequences.inputs, args, kwargs)

    def fluxplot(self, *args, **kwargs):
        self._plot(self.model.sequences.fluxes, args, kwargs)

    def stateplot(self, *args, **kwargs):
        self._plot(self.model.sequences.states, args, kwargs)

    def assignrepr(self, prefix):
        """Return a :func:`repr` string with an prefixed assignement.

        Argument:
            * prefix(:class:`str`): Usually something like 'x = '.
        """
        blanks = ' ' * (len(prefix) + 8)
        lines = []
        lines.append('%sElement("%s",' % (prefix, self.name))
        for conname in ('inlets', 'outlets', 'receivers', 'senders'):
            connections = getattr(self, conname, None)
            if connections:
                subprefix = '%s%s=' % (blanks, conname)
                if len(connections) == 1:
                    line = connections.slaves[0].assignrepr(subprefix)
                else:
                    line = Nodes(connections.slaves).assignrepr(subprefix)
                lines.append(line + ',')
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)

    def __repr__(self):
        return self.assignrepr('')



class Devices(object):

    _contentclass = None

    def __init__(self, *values):
        self._extractvalues(values)

    def _extractvalues(self, values):
        if values is not None:

            if isinstance(values, (self._contentclass, str)):
                device = self._contentclass(values)
                self[device.name] = device
            else:
                try:
                    for value in values:
                        self._extractvalues(value)
                except TypeError:
                    raise TypeError('toDo')

    def _getnames(self):
        return vars(self).keys()
    names = property(_getnames)

    def _getdevices(self):
        return vars(self).values()
    devices = property(_getdevices)

    def copy(self):
        """Return a shallow copy of the actual :class:`Elements` instance."""
        return copy.copy(self)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del(self.__dict__[key])

    def __iter__(self):
        for (name, device) in vars(self).items():
            yield (name, device)

    def __contains__(self, device):
        device = self._contentclass(device)
        return device.name in self.__dict__

    def __len__(self):
        return len(self.names)

    def __add__(self, values):
        new = self.copy()
        for (name, device) in self.__class__(values):
            new[name] = device
        return new

    def __iadd__(self, values):
        for (name, device) in self.__class__(values):
            self[name] = device
        return self

    def __sub__(self, values):
        new = self.copy()
        for (name, device) in self.__class__(values):
            if name in self:
                del(new[name])
        return new

    def __isub__(self, values):
        for (name, device) in self.__class__(values):
            if name in self:
                del(self[name])
        return self

    def __lt__(self, other):
        return set(self.devices) < set(other.devices)

    def __le__(self, other):
        return set(self.devices) <= set(other.devices)

    def __eq__(self, other):
        return set(self.devices) == set(other.devices)

    def __ne__(self, other):
        return set(self.devices) != set(other.devices)

    def __ge__(self, other):
        return set(self.devices) >= set(other.devices)

    def __gt__(self, other):
        return set(self.devices) > set(other.devices)

    def __repr__(self):
        lines = []
        for (name, device) in sorted(zip(self.names, self.devices)):
            lines.append(repr(device))
        return '\n'.join(lines)

    def assignrepr(self, prefix):
        lines = []
        prefix += '%s(' % objecttools.classname(self)
        blanks = ' '*len(prefix)
        names = sorted(self.names)
        for (idx, name) in enumerate(names):
            device = self[name]
            if idx == 0:
                lines.append(device.assignrepr(prefix))
            else:
                lines.append(device.assignrepr(blanks))
            lines[-1] += ','
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)

class Nodes(Devices):

    _contentclass = Node


class Elements(Devices):

    _contentclass = Element