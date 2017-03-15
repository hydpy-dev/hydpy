# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools


class Model(object):
    """Base class for hydrological models."""

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None

    def connect(self):
        """Connect the link sequences of the actual model."""
        conname_isexit_pairs = (('inlets', True),
                                ('receivers', True),
                                ('outlets', False),
                                ('senders', False))
        for (conname, isexit) in conname_isexit_pairs:
            nodes = getattr(self.element, conname).slaves
            if len(nodes) == 1:
                node = nodes[0]
                links = getattr(self.sequences, conname)
                seq = getattr(links, node.variable.lower(), None)
                if seq is None:
                    RuntimeError('ToDo')
                elif isexit:
                    seq.setpointer(node.getdouble_via_exits())
                else:
                    seq.setpointer(node.getdouble_via_entries())
            else:
                NotImplementedError('ToDo')
#        nodes = self.element.inlets.slaves
#        if len(nodes) == 1:
#            node = nodes[0]
#            seq = getattr(self.sequences.inlets, node.variable.lower(), None)
#            if seq is None:
#                RuntimeError('ToDo')
#            else:
#                seq.setpointer(node.getdouble_via_exits())
#        else:
#            NotImplementedError('ToDo')
#        nodes = self.element.outlets.slaves
#        if not nodes:
#            RuntimeError('ToDo')
#        elif len(nodes) == 1:
#            node = nodes[0]
#            seq = getattr(self.sequences.outlets, node.variable.lower(), None)
#            if seq is None:
#                RuntimeError('ToDo')
#            else:
#                seq.setpointer(node.getdouble_via_entries())
#        else:
#            NotImplementedError('ToDo')

    def updatereceivers(self, idx):
        pass

    def updatesenders(self, idx):
        pass

    def doit(self, idx):
        self.loaddata(idx)
        self.updateinlets(idx)
        self.run(idx)
        self.updateoutlets(idx)
        self.updatesenders(idx)
        self.new2old()
        self.savedata(idx)

    def loaddata(self, idx):
        self.sequences.loaddata(idx)

    def savedata(self, idx):
        self.sequences.savedata(idx)

    def updateinlets(self, idx):
        """Maybe."""
        pass

    def updateoutlets(self, idx):
        """In any case."""
        pass

    def new2old(self):
        """Assign the new/final state values of the actual time step to the
        new/initial state values of the next time step.  Needs to be
        overwritten in Cython mode.
        """
        try:
            self.sequences.states.new2old()
        except AttributeError:
            pass

    def __dir__(self):
        return objecttools.dir_(self)

