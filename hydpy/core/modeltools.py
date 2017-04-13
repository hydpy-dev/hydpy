# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools


class MetaModel(type):

    def __new__(cls, name, parents, dict_):
        methods = dict_.get('_METHODS')
        if methods is None:
            raise NotImplementedError('Each Model class needs to know which '
                                      'calculation methods shall be '
                                      'performed.  These methods must be '
                                      'available in a tuple stored as a class '
                                      'attribute named `_METHODS`.  For class '
                                      '`%s`, such a attribute is not defined.'
                                      % name)
        omitversion = dict_.get('_OMITVERSION', True)
        for method in methods:
            if omitversion:
                dict_['_'.join(method.__name__.split('_')[:-1])] = method
            else:
                dict_[method.__name__] = method
        return type.__new__(cls, name, parents, dict_)


class Model(object):
    """Base class for hydrological models."""

    __metaclass__ = MetaModel
    _OMITVERSION = False
    _METHODS = ()

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None
        self.cymodel = type('dummy', (), {})
        self.cymodel.idx_sim = -999

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

    def run(self):
        for method in self._METHODS:
            method(self)

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

    def _getidx_sim(self):
        """Index of the actual simulation time step."""
        return self.cymodel.idx_sim
    def _setidx_sim(self, value):
        self.cymodel.idx_sim = int(value)
    idx_sim = property(_getidx_sim, _setidx_sim)

    def __dir__(self):
        return objecttools.dir_(self)

