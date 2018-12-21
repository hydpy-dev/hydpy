# -*- coding: utf-8 -*-

# import...
# ...from standard library
import importlib
from typing import Iterator
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import selectiontools


class ExchangeVariable(dict):
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

    >>> from hydpy.core.itemtools import ExchangeVariable
    >>> ev = ExchangeVariable('hland_v1', 'control.alpha')
    >>> ev.collect_variables(pub.selections)
    >>> land_dill = hp.elements.land_dill
    >>> ev[land_dill] is land_dill.model.parameters.control.alpha
    True
    >>> ev[hp.nodes.dill]   # ToDo
    Traceback (most recent call last):
    ...
    KeyError: Node("dill", variable="Q",
         keywords="gauge")

    >>> for device in sorted(ev):
    ...     print(device)
    land_dill
    land_lahn_1
    land_lahn_2

    >>> ev = ExchangeVariable('hland', 'states.ic')
    >>> ev.collect_variables(pub.selections)
    >>> land_lahn_3 = hp.elements.land_lahn_3
    >>> ev[land_lahn_3] is land_lahn_3.model.sequences.states.ic
    True
    >>> for element in sorted(ev):
    ...     print(element)
    land_dill
    land_lahn_1
    land_lahn_2
    land_lahn_3

    >>> land_lahn_3.model.sequences.inputs.t.series = range(4)
    >>> ev = ExchangeVariable('hland', 'inputs.t.series')
    >>> ev.collect_variables(pub.selections)
    >>> ev[land_lahn_3]
    InfoArray([ 0.,  1.,  2.,  3.])

    >>> ev = ExchangeVariable('node', 'sim')
    >>> ev.collect_variables(pub.selections)
    >>> dill = hp.nodes.dill
    >>> ev[dill] is dill.sequences.sim
    True
    >>> for node in sorted(ev):
    ...  print(node)
    dill
    lahn_1
    lahn_2
    lahn_3

    >>> dill.sequences.sim.series = range(4)
    >>> ev = ExchangeVariable('node', 'sim.series')
    >>> ev.collect_variables(pub.selections)
    >>> dill = hp.nodes.dill
    >>> ev[dill]
    InfoArray([ 0.,  1.,  2.,  3.])
    """

    def __init__(self, parent: str, child: str):
        self._parent = parent
        entries = child.split('.')
        self._series = entries[-1] == 'series'
        if self._series:
            del entries[-1]
        try:
            self._subgroup, self._variable = entries
        except ValueError:
            self._subgroup, self._variable = None, entries[0]
        self._memory = None

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        if self._parent == 'node':
            for node in selections.nodes:
                self[node] = self._query_nodevariable(node)
                if self._series:
                    self[node] = self[node].series
        else:
            for element in self._iter_relevantelements(selections):
                self[element] = self._query_elementvariable(element)
                if self._series:
                    self[element] = self[element].series

    @property
    def value(self):
        return self._memory

    @value.setter
    def value(self, value):
        self._memory = value
        for variable in self.values():
            variable(value)

    def _iter_relevantelements(self, selections: selectiontools.Selections) -> \
            Iterator[devicetools.Element]:
        for element in selections.elements:
            name1 = element.model.name
            name2 = name1.rpartition('_')[0]
            if self._parent in (name1, name2):
                yield element

    def _query_elementvariable(self, element: devicetools.Element):
        model = element.model
        for group in (model.parameters, model.sequences):
            subgroup = getattr(group, self._subgroup, None)
            if subgroup is not None:
                return getattr(subgroup, self._variable)

    def _query_nodevariable(self, node: devicetools.Node):
        return getattr(node.sequences, self._variable)


class ExchangeItem(object):
    pass


class SetItem(ExchangeItem):
    """

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> from hydpy import HydPy, pub, TestIO
    >>> with TestIO():
    ...     hp = HydPy('LahnH')
    ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
    ...     hp.prepare_everything()

    >>> from hydpy.core.itemtools import SetItem
    >>> item = SetItem('hland_v1', 'control.alpha', 0)
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


    >>> item = SetItem('hland_v1', 'control.fc', 0)
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

    >>> item = SetItem('hland_v1', 'control.fc', 1)
    >>> item.collect_variables(pub.selections)
    Traceback (most recent call last):
    ...
    RuntimeError: different shapes

    >>> from hydpy.models.hland_v1 import FIELD
    >>> for element in hp.elements.catchment:
    ...     control = element.model.parameters.control
    ...     control.nmbzones(5)
    ...     control.zonetype(FIELD)

    >>> item = SetItem('hland_v1', 'control.fc', 1)
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
    def __init__(self, master, variable, ndim):
        self.target = ExchangeVariable(master, variable)
        self.ndim = int(ndim)
        self._value = None
        self.shape = None

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        self.target.collect_variables(selections)
        if self.ndim == 0:
            self.shape = ()
        else:
            shape = None
            for variable in self.target.values():
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
        self.target.value = self.value


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
