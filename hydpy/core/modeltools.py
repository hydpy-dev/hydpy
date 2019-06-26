# -*- coding: utf-8 -*-
"""This module implements tools for the development of hydrological models."""
# import...
# ...from standard library
import os
import types
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import conf
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import typingtools
from hydpy.cythons import modelutils


class Model:
    """Base class for all hydrological models."""

    __name = None

    NUMERICAL = False

    RUN_METHODS = ()
    ADD_METHODS = ()
    INLET_METHODS = ()
    OUTLET_METHODS = ()
    RECEIVER_METHODS = ()
    SENDER_METHODS = ()
    PART_ODE_METHODS = ()
    FULL_ODE_METHODS = ()
    _METHOD_GROUPS = ('RUN_METHODS', 'ADD_METHODS',
                      'INLET_METHODS', 'OUTLET_METHODS',
                      'RECEIVER_METHODS', 'SENDER_METHODS',
                      'PART_ODE_METHODS', 'FULL_ODE_METHODS')

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None
        self._masks = None
        self.cymodel = parametertools.FastAccessParameter()   # ToDo ???
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

    @property
    def name(self):
        """Name of the model type.

        For base models, |Model.name| corresponds to the package name:

        >>> from hydpy import prepare_model
        >>> hland = prepare_model('hland')
        >>> hland.name
        'hland'

        For application models, |Model.name| corresponds the module name:

        >>> hland_v1 = prepare_model('hland_v1')
        >>> hland_v1.name
        'hland_v1'

        This last example has only technical reasons:

        >>> hland.name
        'hland'
        """
        name = self.__name
        if name:
            return name
        subs = self.__module__.split('.')
        if len(subs) == 2:
            type(self).__name = subs[1]
        else:
            type(self).__name = subs[2]
        return self.__name

    def connect(self):
        """Connect the link sequences of the actual model."""
        try:
            for group in ('inlets', 'receivers', 'outlets', 'senders'):
                self._connect_subgroup(group)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to build the node connection of the `%s` '
                'sequences of the model handled by element `%s`'
                % (group[:-1], objecttools.devicename(self)))

    def _connect_subgroup(self, group):
        available_nodes = getattr(self.element, group)
        links = getattr(self.sequences, group, ())
        applied_nodes = []
        for seq in links:
            selected_nodes = tuple(node for node in available_nodes
                                   if node.variable.lower() == seq.name)
            if seq.NDIM == 0:
                if len(selected_nodes) == 1:
                    applied_nodes.append(selected_nodes[0])
                    seq.set_pointer(selected_nodes[0].get_double(group))
                elif len(selected_nodes) == 0:
                    raise RuntimeError(
                        f'Sequence `{seq.name}` cannot be connected '
                        f'as no node is available which is handling '
                        f'the variable `{seq.name.upper()}`.')
                else:
                    raise RuntimeError(
                        f'Sequence `{seq.name}` cannot be connected as '
                        f'it is 0-dimensional but multiple nodes are '
                        f'available which are handling variable '
                        f'`{seq.name.upper()}`.')
            elif seq.NDIM == 1:
                seq.shape = len(selected_nodes)
                for idx, node in enumerate(selected_nodes):
                    applied_nodes.append(node)
                    seq.set_pointer(node.get_double(group), idx)
        if len(applied_nodes) < len(available_nodes):
            remaining_nodes = [node.name for node in available_nodes
                               if node not in applied_nodes]
            raise RuntimeError(
                f'The following nodes have not been connected '
                f'to any sequences: '
                f'`{objecttools.enumeration(remaining_nodes)}`.')

    @property
    def mask(self):
        if self._mask is None:
            raise AttributeError(
                'Model `%s` does not handle a group of masks.'
                % objecttools.modulename(self))
        return self._masks

    def simulate(self, idx):
        self.idx_sim = idx
        self.load_data()
        self.update_inlets()
        self.run()
        self.new2old()
        self.update_outlets()

    def run(self):
        for method in self.RUN_METHODS:
            method(self)

    def load_data(self):
        self.sequences.load_data(self.idx_sim)

    def save_data(self, idx):
        self.idx_sim = idx
        self.sequences.save_data(idx)

    def update_inlets(self):
        for method in self.INLET_METHODS:
            method(self)

    def update_outlets(self):
        for method in self.OUTLET_METHODS:
            method(self)

    def update_receivers(self, idx):
        self.idx_sim = idx
        for method in self.RECEIVER_METHODS:
            method(self)

    def update_senders(self, idx):
        self.idx_sim = idx
        for method in self.SENDER_METHODS:
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

    def __str__(self):
        return self.__module__.split('.')[2]

    def __dir__(self):
        return objecttools.dir_(self)


class NumConstsELS:

    def __init__(self):
        self.nmb_methods = 10
        self.nmb_stages = 11
        self.dt_increase = 2.
        self.dt_decrease = 10.
        path = os.path.join(conf.__path__[0],
                            'a_coefficients_explicit_lobatto_sequence.npy')
        self.a_coefs = numpy.load(path)


class NumVarsELS:

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
        Model.__init__(self)
        self.numconsts = NumConstsELS()
        self.numvars = NumVarsELS()

    def simulate(self, idx):
        self.idx_sim = idx
        self.load_data()
        self.update_inlets()
        self.solve()
        self.update_outlets()

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
        >>> from hydpy import round_
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

        >>> from hydpy import reverse_model_wildcard_import
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
        """Apply all methods stored in the hidden attribute
        `PART_ODE_METHODS`.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.25)
        >>> states.s = 1.0
        >>> model.calculate_single_terms()
        >>> fluxes.q
        q(0.25)
        """
        self.numvars.nmb_calls = self.numvars.nmb_calls+1
        for method in self.PART_ODE_METHODS:
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
        for method in self.FULL_ODE_METHODS:
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
        for state in states:
            temp = getattr(states.fastaccess, '_%s_%s' % (state.name, type_))
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
        >>> from hydpy import round_
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
        >>> from hydpy import round_
        >>> round_(results[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_states(self.numvars.idx_method, 'results')

    def _set_states(self, idx, type_):
        states = self.sequences.states
        for state in states:
            temp = getattr(states.fastaccess, '_%s_%s' % (state.name, type_))
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
        for flux in fluxes.numericsequences:
            flux(getattr(fluxes.fastaccess, '_%s_sum' % flux.name))

    def set_point_fluxes(self):
        """Save the fluxes corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:] = 0.
        >>> model.set_point_fluxes()
        >>> from hydpy import round_
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
        >>> from hydpy import round_
        >>> round_(results[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_method, 'results')

    def _set_fluxes(self, idx, type_):
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            temp = getattr(fluxes.fastaccess, '_%s_%s' % (flux.name, type_))
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
        >>> from hydpy import round_
        >>> from hydpy import pub
        >>> round_(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
        0.375, 0.125
        >>> fluxes.q
        q(2.9375)
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            points = getattr(fluxes.fastaccess, '_%s_points' % flux.name)
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
        for flux in fluxes.numericsequences:
            if flux.NDIM == 0:
                setattr(fluxes.fastaccess, '_%s_sum' % flux.name, 0.)
            else:
                getattr(fluxes.fastaccess, '_%s_sum' % flux.name)[:] = 0.

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
        for flux in fluxes.numericsequences:
            sum_ = getattr(fluxes.fastaccess, '_%s_sum' % flux.name)
            sum_ += flux
            if flux.NDIM == 0:
                setattr(fluxes.fastaccess, '_%s_sum' % flux.name, sum_)

    def calculate_error(self):
        """Estimate the numerical error based on the fluxes calculated
        by the current and the last method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:4] = 0., 3., 4., 0.
        >>> model.calculate_error()
        >>> from hydpy import round_
        >>> round_(model.numvars.error)
        1.0
        """
        self.numvars.error = 0.
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            results = getattr(fluxes.fastaccess, '_%s_results' % flux.name)
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
        >>> from hydpy import round_
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
