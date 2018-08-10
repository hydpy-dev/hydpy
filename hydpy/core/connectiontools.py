# -*- coding: utf-8 -*-
"""This modules implements tools for handling connections between |Node| and
|Element| instances.
"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from Hydpy
from hydpy.core import autodoctools


class Connections(object):
    """Connection between |Node| and |Element| instances."""

    __slots__ = ('master', 'name', '_slaves')

    def __init__(self, master, name):
        self.master = master
        self.name = name
        self._slaves = set()

    def __iadd__(self, slave):
        self._slaves.add(slave)
        return self

    @property
    def names(self):
        return tuple(slave.name for slave in sorted(self._slaves))

    @property
    def slaves(self):
        return tuple(slave for slave in sorted(self._slaves))

    @property
    def variables(self):
        variable = getattr(self.master, 'variable', None)
        if variable:
            return [variable]
        else:
            return sorted(set([slave.variable for slave in self]))

    def __getattr__(self, name):
        for slave in self._slaves:
            if name == slave.name:
                return slave
        else:
            raise AttributeError(
                'The selected connection neither has a attribute nor does '
                'it handle a slave named `%s`.' % name)

    def __delattr__(self, name):
        slave = getattr(self, name)
        self._slaves.remove(slave)

    def __contains__(self, value):
        try:
            value = value.name
        except AttributeError:
            pass
        return value in self.names

    def __iter__(self):
        for slave in sorted(self._slaves):
            yield slave

    def __len__(self):
        return len(self._slaves)

    def __dir__(self):
        return ['names', 'slaves', 'variables'] + list(self.names)


autodoctools.autodoc_module()
