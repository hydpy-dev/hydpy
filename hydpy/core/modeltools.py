# -*- coding: utf-8 -*-
"""This module implements tools for the development of hydrological models.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import types
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import autodoctools


class MetaModel(type):
    def __new__(cls, name, parents, dict_):
        _METHOD_GROUPS = ('_RUNMETHODS', '_ADDMETHODS',
                          '_PART_ODE_METHODS', '_FULL_ODE_METHODS')
        dict_['_METHOD_GROUPS'] = _METHOD_GROUPS
        for name in _METHOD_GROUPS:
            methods = dict_.get(name, ())
            if methods:
                if name == '_RUNMETHODS':
                    lst = ['\n\n\n    The following "run methods" are called '
                           'each simulation step run in the given sequence:']
                elif name == '_ADDMETHODS':
                    lst = ['\n\n\n    The following "additional methods" are '
                           'called by at least one "run method":']
                elif name == '_PART_ODE_METHODS':
                    lst = ['\n\n\n    The following methods define the '
                           'relevant components of a system of ODE '
                           'equations (e.g. direct runoff):']
                elif name == '_FULL_ODE_METHODS':
                    lst = ['\n\n\n    The following methods define the '
                           'complete equations of an ODE system '
                           '(e.g. change in storage of `fast water` due to '
                           ' effective precipitation and direct runoff):']
                for method in methods:
                    lst.append('      * :func:`~%s` `%s`'
                               % ('.'.join((method.__module__,
                                            method.__name__)),
                                  autodoctools.description(method)))
                doc = dict_.get('__doc__', 'Undocumented model.')
                dict_['__doc__'] = doc + '\n'.join(l for l in lst)

        return type.__new__(cls, name, parents, dict_)


_MetaModel = MetaModel('MetaModel', (), {})


class Model(_MetaModel):
    """Base class for all hydrological models."""

    _RUNMETHODS = ()
    _ADDMETHODS = ()
    _PART_ODE_METHODS = ()
    _FULL_ODE_METHODS = ()

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None
        self.cymodel = type('dummy', (), {})
        self.cymodel.idx_sim = -999
        self._init_methods()

    def _init_methods(self):
        """Convert all pure Python calculation functions of the model class to
        methods and assign them to the model instance.
        """
        for name_group in self._METHOD_GROUPS:
            functions = getattr(self, name_group, ())
            uniques = {}
            for func in functions:
                name = func.__name__
                method = types.MethodType(func, self)
                setattr(self, name, method)
                shortname = '_'.join(name.split('_')[:-1])
                if shortname in uniques:
                    uniques[shortname] = None
                else:
                    uniques[shortname] = method
            for (shortname, method) in uniques.items():
                if method is not None:
                    setattr(self, shortname, method)

    def connect(self):
        """Connect the link sequences of the actual model."""
        try:
            for group in ('inlets', 'receivers', 'outlets', 'senders'):
                self._connect_subgroup(group)
        except BaseException:
            objecttools.augmentexcmessage(
                'While trying to build the node connection of the `%s` '
                'sequences of the model handled by element `%s`'
                % (group[:-1],  objecttools.devicename(self)))

    def _connect_subgroup(self, group):
        isentry = group in ('inlets', 'receivers')
        available_nodes = getattr(self.element, group).slaves
        links = getattr(self.sequences, group, ())
        applied_nodes = []
        for (name, seq) in links:
            selected_nodes = [node for node in available_nodes
                              if node.variable.lower() == name]
            if isentry:
                selected_doubles = [node.getdouble_via_exits()
                                    for node in selected_nodes]
            else:
                selected_doubles = [node.getdouble_via_entries()
                                    for node in selected_nodes]
            if seq.NDIM == 0:
                if len(selected_nodes) == 1:
                    applied_nodes.append(selected_nodes[0])
                    seq.setpointer(selected_doubles[0])
                elif len(selected_nodes) == 0:
                    raise RuntimeError('Sequence `%s` cannot be connected, '
                                       'as no node is available which is '
                                       'handling the variable `%s`.'
                                       % (name, seq.name.upper()))
                else:
                    raise RuntimeError('Sequence `%s` cannot be connected, '
                                       'as it is 0-dimensional but multiple '
                                       'nodes are available which are '
                                       'handling variable `%s`.'
                                       % (name, seq.name.upper()))
            elif seq.NDIM == 1:
                seq.shape = len(selected_nodes)
                zipped = zip(selected_nodes, selected_doubles)
                for idx, (node, double) in enumerate(zipped):
                    applied_nodes.append(node)
                    seq.setpointer(double, idx)
        if len(applied_nodes) < len(available_nodes):
            remaining_nodes = [node.name for node in available_nodes
                               if node not in applied_nodes]
            raise RuntimeError('The following nodes have not been connected '
                               'to any sequences: `%s`.'
                               % ', '.join(remaining_nodes))

    def doit(self, idx):
        self.idx_sim = idx
        self.loaddata()
        self.update_inlets()
        self.run()
        self.update_outlets()
        self.update_senders()
        self.new2old()
        self.savedata()

    def run(self):
        for method in self._RUNMETHODS:
            if not method.__name__.startswith('update_'):
                method(self)

    def loaddata(self):
        self.sequences.loaddata(self.idx_sim)

    def savedata(self):
        self.sequences.savedata(self.idx_sim)

    def update_inlets(self):
        """Maybe."""
        pass

    def update_outlets(self):
        """In any case."""
        pass

    def update_receivers(self):
        pass

    def update_senders(self):
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


autodoctools.autodoc_module()
