# -*- coding: utf-8 -*-
"""This module implements tools for the development of hydrological models.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import os
import types
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy import conf
from hydpy.core import objecttools
from hydpy.core import autodoctools
from hydpy.cythons import modelutils


class MetaModel(type):
    def __new__(cls, cls_name, cls_parents, dict_):
        _METHOD_GROUPS = ('_RUN_METHODS', '_ADD_METHODS',
                          '_INLET_METHODS', '_OUTLET_METHODS',
                          '_RECEIVER_METHODS', '_SENDER_METHODS',
                          '_PART_ODE_METHODS', '_FULL_ODE_METHODS')
        dict_['_METHOD_GROUPS'] = _METHOD_GROUPS
        for method_name in _METHOD_GROUPS:
            methods = dict_.get(method_name, ())
            if methods:
                if method_name == '_RUN_METHODS':
                    lst = ['\n\n\n    The following "run methods" are called '
                           'each simulation step run in the given sequence:']
                elif method_name == '_ADD_METHODS':
                    lst = ['\n\n\n    The following "additional methods" are '
                           'called by at least one "run method":']
                elif method_name == '_INLET_METHODS':
                    lst = ['\n\n\n    The following "inlet update methods" '
                           'are called in the given sequence immediately  '
                           'before solving the differential equations '
                           'of the respective model:']
                elif method_name == '_OUTLET_METHODS':
                    lst = ['\n\n\n    The following "outlet update methods" '
                           'are called in the given sequence immediately  '
                           'after solving the differential equations '
                           'of the respective model:']
                elif method_name == '_RECEIVER_METHODS':
                    lst = ['\n\n\n    The following "receiver update methods" '
                           'are called in the given sequence before solving '
                           'the differential equations of any model:']
                elif method_name == '_SENDER_METHODS':
                    lst = ['\n\n\n    The following "sender update methods" '
                           'are called in the given sequence after solving '
                           'the differential equations of all models:']
                elif method_name == '_PART_ODE_METHODS':
                    lst = ['\n\n\n    The following methods define the '
                           'relevant components of a system of ODE '
                           'equations (e.g. direct runoff):']
                elif method_name == '_FULL_ODE_METHODS':
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

        return type.__new__(cls, cls_name, cls_parents, dict_)


_MetaModel = MetaModel('MetaModel', (), {})


class Model(_MetaModel):
    """Base class for all hydrological models."""

    NUMERICAL = False

    _RUN_METHODS = ()
    _ADD_METHODS = ()
    _INLET_METHODS = ()
    _OUTLET_METHODS = ()
    _RECEIVER_METHODS = ()
    _SENDER_METHODS = ()
    _PART_ODE_METHODS = ()
    _FULL_ODE_METHODS = ()

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None
        self.cymodel = objecttools.FastAccess()
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
                name_func = func.__name__
                method = types.MethodType(func, self)
                setattr(self, name_func, method)
                shortname = '_'.join(name_func.split('_')[:-1])
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
        self.new2old()
        self.update_outlets()
        self.savedata()

    def run(self):
        for method in self._RUN_METHODS:
            method(self)

    def loaddata(self):
        self.sequences.loaddata(self.idx_sim)

    def savedata(self):
        self.sequences.savedata(self.idx_sim)

    def update_inlets(self):
        for method in self._INLET_METHODS:
            method(self)

    def update_outlets(self):
        for method in self._OUTLET_METHODS:
            method(self)

    def update_receivers(self, idx):
        self.idx_sim = idx
        for method in self._RECEIVER_METHODS:
            method(self)

    def update_senders(self, idx):
        self.idx_sim = idx
        for method in self._SENDER_METHODS:
            method(self)

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


class NumPars(object):

    def __iter__(self):
        for (name, par) in vars(self).items():
            yield (name, par)


class NumConstsELS(NumPars):

    def __init__(self):
        self.nmb_methods = 10
        self.nmb_stages = 11
        self.dt_increase = 2.
        self.dt_decrease = 10.
        path = os.path.join(conf.__path__[0],
                            'a_coefficients_explicit_lobatto_sequence.npy')
        self.a_coefs = numpy.load(path)


class NumVarsELS(NumPars):

    def __init__(self):
        self.nmb_calls = 0
        self.t0 = 0.
        self.t1 = 0.
        self.dt_est = 1.
        self.dt = 1.
        self.idx_method = 0
        self.idx_stage = 0
        self.error = 0.
        self.last_error = 0.
        self.extrapolated_error = 0.
        self.f0_ready = False


class ModelELS(Model):

    NUMERICAL = True

    def __init__(self):
        super(ModelELS, self).__init__()
        self.numconsts = NumConstsELS()
        self.numvars = NumVarsELS()

    def doit(self, idx):
        self.idx_sim = idx
        self.loaddata()
        self.update_inlets()
        self.solve()
        self.update_outlets()
        self.savedata()

    def solve(self):
        """

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.0)
        >>> solver.abserrormax = 1e-2
        >>> solver.reldtmin = 1e-4
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(1.0)
        >>> fluxes.q
        q(0.0)
        >>> model.numvars.idx_method
        2
        >>> model.numvars.dt
        1.0
        >>> model.numvars.nmb_calls
        2

        >>> k(0.1)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.905)
        >>> fluxes.q
        q(0.095)
        >>> model.numvars.idx_method
        2
        >>> model.numvars.nmb_calls
        2

        >>> import numpy
        >>> from hydpy.core.objecttools import round_
        >>> round_(numpy.exp(-k))
        0.904837

        >>> solver.abserrormax = 1e-3

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904833)
        >>> fluxes.q
        q(0.095167)
        >>> model.numvars.idx_method
        3
        >>> model.numvars.nmb_calls
        4

        >>> solver.abserrormax = 1e-4

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904837)
        >>> fluxes.q
        q(0.095163)
        >>> model.numvars.idx_method
        4
        >>> model.numvars.nmb_calls
        7

        >>> solver.abserrormax = 1e-12

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904837)
        >>> fluxes.q
        q(0.095163)
        >>> model.numvars.idx_method
        8
        >>> model.numvars.nmb_calls
        29

        >>> solver.abserrormax = 1e-2

        >>> k(0.5)

        >>> round_(numpy.exp(-k))
        0.606531

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.606771)
        >>> fluxes.q
        q(0.393229)
        >>> model.numvars.idx_method
        4
        >>> model.numvars.nmb_calls
        7

        >>> k(2.0)

        >>> round_(numpy.exp(-k))
        0.135335

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.134658)
        >>> fluxes.q
        q(0.865342)
        >>> model.numvars.nmb_calls
        22

        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.018929)
        >>> fluxes.q
        q(0.115728)
        >>> model.numvars.nmb_calls
        13

        >>> k(4.0)

        >>> round_(numpy.exp(-k))
        0.018316

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.019774)
        >>> fluxes.q
        q(0.980226)
        >>> round_(model.numvars.dt)
        0.3
        >>> model.numvars.nmb_calls
        44

        >>> from hydpy.core.magictools import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()

        >>> from hydpy.models.test_v2 import *
        >>> parameterstep()
        >>> k(0.5)
        >>> solver.abserrormax = 1e-2
        >>> solver.reldtmin = 1e-4
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.5)
        >>> fluxes.q
        q(0.5)
        >>> model.numvars.idx_method
        2
        >>> model.numvars.dt
        1.0
        >>> model.numvars.nmb_calls
        2

        >>> k(2.0)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(-0.006827)
        >>> fluxes.q
        q(1.006827)
        >>> model.numvars.nmb_calls
        58

        >>> k(2.1)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(-0.00072)
        >>> fluxes.q
        q(1.00072)
        >>> model.numvars.nmb_calls
        50

        """
        self.numvars.t0, self.numvars.t1 = 0., 1.
        self.numvars.dt_est = 1.
        self.numvars.f0_ready = False
        self.reset_sum_fluxes()
        while self.numvars.t0 < self.numvars.t1-1e-14:
            self.numvars.last_error = 999999.
            self.numvars.dt = min(
                    self.numvars.t1-self.numvars.t0,
                    max(self.numvars.dt_est, self.parameters.solver.reldtmin))
            if not self.numvars.f0_ready:
                self.calculate_single_terms()
                self.numvars.idx_method = 0
                self.numvars.idx_stage = 0
                self.set_point_fluxes()
                self.set_point_states()
                self.set_result_states()
            for self.numvars.idx_method in range(
                                        1, self.numconsts.nmb_methods+1):
                for self.numvars.idx_stage in range(
                                            1, self.numvars.idx_method):
                    self.get_point_states()
                    self.calculate_single_terms()
                    self.set_point_fluxes()
                for self.numvars.idx_stage in range(
                                            1, self.numvars.idx_method+1):
                    self.integrate_fluxes()
                    self.calculate_full_terms()
                    self.set_point_states()
                self.set_result_fluxes()
                self.set_result_states()
                self.calculate_error()
                self.extrapolate_error()
                if self.numvars.idx_method == 1:
                    continue
                elif self.numvars.error <= self.parameters.solver.abserrormax:
                    self.numvars.dt_est = (self.numconsts.dt_increase *
                                           self.numvars.dt)
                    self.numvars.f0_ready = False
                    self.addup_fluxes()
                    self.numvars.t0 = self.numvars.t0+self.numvars.dt
                    self.new2old()
                    break
                elif ((self.numvars.extrapolated_error >
                       self.parameters.solver.abserrormax) and
                      (self.numvars.dt > self.parameters.solver.reldtmin)):
                    self.numvars.f0_ready = True
                    self.numvars.dt_est = (self.numvars.dt /
                                           self.numconsts.dt_decrease)
                    break
                else:
                    self.numvars.last_error = self.numvars.error
                    self.numvars.f0_ready = True
                    continue
            else:
                if self.numvars.dt <= self.parameters.solver.reldtmin:
                    self.numvars.f0_ready = False
                    self.addup_fluxes()
                    self.numvars.t0 = self.numvars.t0+self.numvars.dt
                    self.new2old()
                else:
                    self.numvars.f0_ready = True
                    self.numvars.dt_est = (self.numvars.dt /
                                           self.numconsts.dt_decrease)
        self.get_sum_fluxes()

    def calculate_single_terms(self):
        """Apply all methods stored in :attr:`_PART_ODE_METHODS`.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.25)
        >>> states.s = 1.0
        >>> model.calculate_single_terms()
        >>> fluxes.q
        q(0.25)
        """
        self.numvars.nmb_calls = self.numvars.nmb_calls+1
        for method in self._PART_ODE_METHODS:
            method(self)

    def calculate_full_terms(self):
        """
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.25)
        >>> states.s.old = 1.0
        >>> fluxes.q = 0.25
        >>> model.calculate_full_terms()
        >>> states.s.old
        1.0
        >>> states.s.new
        0.75
        """
        for method in self._FULL_ODE_METHODS:
            method(self)

    def get_point_states(self):
        """Load the states corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:4] = 0.0, 0.0, 1.0, 0.0
        >>> model.get_point_states()
        >>> states.s.old
        2.0
        >>> states.s.new
        1.0
        """
        self._get_states(self.numvars.idx_stage, 'points')

    def _get_states(self, idx, type_):
        states = self.sequences.states
        for (name, state) in states:
            temp = getattr(states.fastaccess, '_%s_%s' % (name, type_))
            state.new = temp[idx]

    def set_point_states(self):
        """Save the states corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:] = 0.
        >>> model.set_point_states()
        >>> from hydpy.core.objecttools import round_
        >>> round_(points[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_states(self.numvars.idx_stage, 'points')

    def set_result_states(self):
        """Save the final states of the actual method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(states.fastaccess._s_results)
        >>> results[:] = 0.0
        >>> model.set_result_states()
        >>> from hydpy.core.objecttools import round_
        >>> round_(results[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_states(self.numvars.idx_method, 'results')

    def _set_states(self, idx, type_):
        states = self.sequences.states
        for (name, state) in states:
            temp = getattr(states.fastaccess, '_%s_%s' % (name, type_))
            temp[idx] = state.new

    def get_sum_fluxes(self):
        """Get the sum of the fluxes calculated so far.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 0.0
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> model.get_sum_fluxes()
        >>> fluxes.q
        q(1.0)
        """
        fluxes = self.sequences.fluxes
        for (name, flux) in fluxes.numerics:
            flux(getattr(fluxes.fastaccess, '_%s_sum' % name))

    def set_point_fluxes(self):
        """Save the fluxes corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:] = 0.
        >>> model.set_point_fluxes()
        >>> from hydpy.core.objecttools import round_
        >>> round_(points[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_stage, 'points')

    def set_result_fluxes(self):
        """Save the final fluxes of the actual method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:] = 0.
        >>> model.set_result_fluxes()
        >>> from hydpy.core.objecttools import round_
        >>> round_(results[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_method, 'results')

    def _set_fluxes(self, idx, type_):
        fluxes = self.sequences.fluxes
        for (name, flux) in fluxes.numerics:
            temp = getattr(fluxes.fastaccess, '_%s_%s' % (name, type_))
            temp[idx] = flux

    def integrate_fluxes(self):
        """Perform a dot multiplication between the fluxes and the
        A coefficients associated with the different stages of the
        actual method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> model.numvars.idx_stage = 1
        >>> model.numvars.dt = 0.5
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:4] = 15., 2., -999., 0.
        >>> model.integrate_fluxes()
        >>> from hydpy.core.objecttools import round_
        >>> from hydpy import pub
        >>> round_(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
        0.375, 0.125
        >>> fluxes.q
        q(2.9375)
        """
        fluxes = self.sequences.fluxes
        for (name, flux) in fluxes.numerics:
            points = getattr(fluxes.fastaccess, '_%s_points' % name)
            coefs = self.numconsts.a_coefs[self.numvars.idx_method-1,
                                           self.numvars.idx_stage,
                                           :self.numvars.idx_method]
            flux(self.numvars.dt *
                 numpy.dot(coefs, points[:self.numvars.idx_method]))

    def reset_sum_fluxes(self):
        """Set the sum of the fluxes calculated so far to zero.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 5.
        >>> model.reset_sum_fluxes()
        >>> fluxes.fastaccess._q_sum
        0.0
        """
        fluxes = self.sequences.fluxes
        for (name, flux) in fluxes.numerics:
            if flux.NDIM == 0:
                setattr(fluxes.fastaccess, '_%s_sum' % name, 0.)
            else:
                getattr(fluxes.fastaccess, '_%s_sum' % name)[:] = 0.

    def addup_fluxes(self):
        """Add up the sum of the fluxes calculated so far.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> fluxes.q(2.0)
        >>> model.addup_fluxes()
        >>> fluxes.fastaccess._q_sum
        3.0
        """
        fluxes = self.sequences.fluxes
        for (name, flux) in fluxes.numerics:
            sum_ = getattr(fluxes.fastaccess, '_%s_sum' % name)
            sum_ += flux
            if flux.NDIM == 0:
                setattr(fluxes.fastaccess, '_%s_sum' % name, sum_)

    def calculate_error(self):
        """Estimate the numerical error based on the fluxes calculated
        by the current and the last method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:4] = 0., 3., 4., 0.
        >>> model.calculate_error()
        >>> from hydpy.core.objecttools import round_
        >>> round_(model.numvars.error)
        1.0
        """
        self.numvars.error = 0.
        fluxes = self.sequences.fluxes
        for (name, flux) in fluxes.numerics:
            results = getattr(fluxes.fastaccess, '_%s_results' % name)
            diff = (results[self.numvars.idx_method] -
                    results[self.numvars.idx_method-1])
            self.numvars.error = max(self.numvars.error,
                                     numpy.max(numpy.abs(diff)))

    def extrapolate_error(self):
        """Estimate the numerical error to be expected when applying all
        methods available based on the results of the current and the
        last method.

        Note that this expolation strategy cannot be applied on the first
        method.  If the current method is the first one, `-999.9` is returned.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.error = 1e-2
        >>> model.numvars.last_error = 1e-1
        >>> model.numvars.idx_method = 10
        >>> model.extrapolate_error()
        >>> from hydpy.core.objecttools import round_
        >>> round_(model.numvars.extrapolated_error)
        0.01
        >>> model.numvars.idx_method = 9
        >>> model.extrapolate_error()
        >>> round_(model.numvars.extrapolated_error)
        0.001
        """
        if self.numvars.idx_method > 2:
            self.numvars.extrapolated_error = modelutils.exp(
                modelutils.log(self.numvars.error) +
                (modelutils.log(self.numvars.error) -
                 modelutils.log(self.numvars.last_error)) *
                (self.numconsts.nmb_methods-self.numvars.idx_method))
        else:
            self.numvars.extrapolated_error = -999.9

autodoctools.autodoc_module()
