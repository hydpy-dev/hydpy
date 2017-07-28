# -*- coding: utf-8 -*-
"""This modules implements tools for handling connections between
:class:`~hydpy.core.devicetools.Node` and
:class:`~hydpy.core.devicetools.Element` instances.
"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from Hydpy
from hydpy.core import objecttools
from hydpy.core import autodoctools


class Connections(object):
    """Connection between :class:`~hydpy.core.devicetools.Node` and
    :class:`~hydpy.core.devicetools.Element` instances.
    """

    def __init__(self, master, *slaves):
        self.master = master
        for slave in slaves:
            self += slave

    def __iadd__(self, slave):
        setattr(self, slave.name, slave)
        return self

    @property
    def names(self):
        return [name for (name, slave) in self]

    @property
    def slaves(self):
        return [slave for (name, slave) in self]

    @property
    def variables(self):
        variable = getattr(self.master, 'variable', None)
        if variable:
            return [variable]
        else:
            return sorted(set([slave.variable for (name, slave) in self]))

    def __contains__(self, value):
        return value in (self.names + self.slaves)

    def __setitem__(self, name, value):
        self.__dict__[name] = value

    def __getitem__(self, name):
        return self.__dict__[name]

    def __iter__(self):
        for (name, slave) in vars(self).items():
            if name != 'master':
                yield (name, slave)

    def __len__(self):
        return len(self.names)

    def __dir__(self):
        return objecttools.dir_(self)


autodoctools.autodoc_module()
