# -*- coding: utf-8 -*-

# import...
# ...from standard library
from typing import Iterator, Tuple
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import selectiontools


class ExchangeItem(object):
    """

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> from hydpy import HydPy, pub, TestIO
    >>> with TestIO():
    ...     hp = HydPy('LahnH')
    ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
    ...     hp.prepare_everything()


    >>> from hydpy.models.hland import Model
    >>> hp.elements.land_lahn_3.model.__class__ = Model

    >>> from hydpy.core.itemtools import ExchangeItem
    >>> item = ExchangeItem('alpha', 'hland_v1', 'control.alpha', None, 0)
    >>> item.collect_variables(pub.selections)
    >>> land_dill = hp.elements.land_dill
    >>> item.device2target[land_dill] is land_dill.model.parameters.control.alpha
    True
    >>> item.device2target[hp.nodes.dill]   # ToDo
    Traceback (most recent call last):
    ...
    KeyError: Node("dill", variable="Q",
         keywords="gauge")

    >>> for device in sorted(item.device2target):
    ...     print(device)
    land_dill
    land_lahn_1
    land_lahn_2

    >>> item = ExchangeItem('ic', 'hland', 'states.ic')
    >>> item.collect_variables(pub.selections)
    >>> land_lahn_3 = hp.elements.land_lahn_3
    >>> item.device2target[land_lahn_3] is land_lahn_3.model.sequences.states.ic
    True
    >>> for element in sorted(item.device2target):
    ...     print(element)
    land_dill
    land_lahn_1
    land_lahn_2
    land_lahn_3

    >>> land_lahn_3.model.sequences.inputs.t.series = range(4)
    >>> item = ExchangeItem('t', 'hland', 'inputs.t.series')
    >>> item.collect_variables(pub.selections)
    >>> item.device2target[land_lahn_3]
    InfoArray([ 0.,  1.,  2.,  3.])

    >>> item = ExchangeItem('sim', 'node', 'sim')
    >>> item.collect_variables(pub.selections)
    >>> dill = hp.nodes.dill
    >>> item.device2target[dill] is dill.sequences.sim
    True
    >>> for node in sorted(item.device2target):
    ...  print(node)
    dill
    lahn_1
    lahn_2
    lahn_3

    >>> dill.sequences.sim.series = range(4)
    >>> item = ExchangeItem('sim', 'node', 'sim.series')
    >>> item.collect_variables(pub.selections)
    >>> dill = hp.nodes.dill
    >>> item.device2target[dill]
    InfoArray([ 0.,  1.,  2.,  3.])
    """

    def __init__(
            self, name: str, master: str, target: str,
            base: str=None, ndim: int=0):
        self.name = str(name)
        self._master = master
        self._series_target, self._subgroup_target, self._variable_target = (
            self._get_seriesflag_and_subgroup_and_variable(target))
        if base is None:
            self._series_base, self._subgroup_base, self._variable_base = (
                None, None, None)
        else:
            self._series_base, self._subgroup_base, self._variable_base = (
                self._get_seriesflag_and_subgroup_and_variable(base))
        self.ndim = int(ndim)
        self._value: numpy.ndarray = None
        self.shape: Tuple[int] = None
        self.device2target = {}
        self.device2base = {}

    @staticmethod
    def _get_seriesflag_and_subgroup_and_variable(string):
        entries = string.split('.')
        series = entries[-1] == 'series'
        if series:
            del entries[-1]
        try:
            subgroup_target, variable_target = entries
        except ValueError:
            subgroup_target, variable_target = None, entries[0]
        return series, subgroup_target, variable_target

    def _iter_relevantelements(self, selections: selectiontools.Selections) -> \
            Iterator[devicetools.Element]:
        for element in selections.elements:
            name1 = element.model.name
            name2 = name1.rpartition('_')[0]
            if self._master in (name1, name2):
                yield element

    def _query_elementvariable(self, element: devicetools.Element):
        model = element.model
        for group in (model.parameters, model.sequences):
            subgroup = getattr(group, self._subgroup_target, None)
            if subgroup is not None:
                return getattr(subgroup, self._variable_target)

    def _query_nodevariable(self, node: devicetools.Node):
        return getattr(node.sequences, self._variable_target)

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        if self._master == 'node':
            for node in selections.nodes:
                self.device2target[node] = self._query_nodevariable(node)
                if self._series_target:
                    self.device2target[node] = self.device2target[node].series
        else:
            for element in self._iter_relevantelements(selections):
                self.device2target[element] = self._query_elementvariable(
                    element)
                if self._series_target:
                    self.device2target[element] = self.device2target[
                        element].series
        self.determine_shape()

    def determine_shape(self):
        if self.ndim == 0:
            self.shape = ()
        else:
            shape = None
            for variable in self.device2target.values():
                if shape is None:
                    shape = variable.shape
                else:
                    if shape != variable.shape:
                        raise RuntimeError('different shapes')
            self.shape = shape

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = numpy.full(self.shape, value)

    def update_variables(self):
        value = self.value
        for variable in self.device2target.values():
            variable(value)


class SetItem(ExchangeItem):
    """

    >>> from hydpy import pub
    >>> pub.options.reprdigits = 6
    >>> pub.options.autocompile = False
    >>> pub.options.printprogress = False

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> from hydpy import HydPy, pub, TestIO
    >>> with TestIO():
    ...     hp = HydPy('LahnH')
    ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
    ...     hp.prepare_everything()

    >>> from hydpy.core.itemtools import SetItem
    >>> item = SetItem('alpha', 'hland_v1', 'control.alpha', ndim=0)
    >>> item.collect_variables(pub.selections)

    >>> item.shape
    ()
    >>> item.value

    >>> land_dill = hp.elements.land_dill
    >>> land_dill.model.parameters.control.alpha
    alpha(1.0)

    >>> item.value = 2.0
    >>> item.value
    array(2.0)
    >>> land_dill.model.parameters.control.alpha
    alpha(1.0)


    >>> item.update_variables()
    >>> land_dill.model.parameters.control.alpha
    alpha(2.0)


    >>> item = SetItem('fc', 'hland_v1', 'control.fc', ndim=0)
    >>> item.collect_variables(pub.selections)
    >>> item.shape
    ()
    >>> land_dill.model.parameters.control.fc
    fc(278.0)
    >>> item.value = 200.0
    >>> item.value
    array(200.0)
    >>> item.update_variables()
    >>> land_dill.model.parameters.control.fc
    fc(200.0)

    >>> item = SetItem('fc', 'hland_v1', 'control.fc', ndim=1)
    >>> item.collect_variables(pub.selections)
    Traceback (most recent call last):
    ...
    RuntimeError: different shapes

    >>> from hydpy.models.hland_v1 import FIELD
    >>> for element in hp.elements.catchment:
    ...     control = element.model.parameters.control
    ...     control.nmbzones(5)
    ...     control.zonetype(FIELD)

    >>> item = SetItem('fc', 'hland_v1', 'control.fc', ndim=1)
    >>> item.name
    'fc'
    >>> item.collect_variables(pub.selections)
    >>> item.shape
    (5,)
    >>> land_dill.model.parameters.control.fc
    fc(nan)
    >>> item.value = 200.0
    >>> item.value
    array([ 200.,  200.,  200.,  200.,  200.])
    >>> item.update_variables()
    >>> land_dill.model.parameters.control.fc
    fc(200.0)

    >>> item.value = 100.0, 200.0, 300.0, 400.0, 500.0
    >>> item.update_variables()
    >>> land_dill.model.parameters.control.fc
    fc(100.0, 200.0, 300.0, 400.0, 500.0)

    >>> item.value = 100.0, 200.0, 300.0, 400.0
    Traceback (most recent call last):
    ...
    ValueError: could not broadcast input array from shape (4) into shape (5)


    """

    def update_variables(self):
        super().update_variables()


class AddItem(ExchangeItem):
    """
    >>> from hydpy.core.itemtools import AddItem
    >>> # item = AddItem('hland_v1', 'control.alpha', 'control.alpha')
    """

    def __init__(self, target, base):
        self.target = self.__doc__
        self.base = eval(f'import hydpy.models.{base}')

    @staticmethod
    def get_variable(string):
        model, group, variable = string.split('.')
        module = importlib.import_module(f'hydpy.models.{model}')
