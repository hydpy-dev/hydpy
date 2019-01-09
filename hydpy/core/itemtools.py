# -*- coding: utf-8 -*-

# import...
# ...from standard library
import abc
import collections
from typing import Dict, Iterator, Tuple
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import selectiontools


_Properties = collections.namedtuple(
    '_Properties', ('series', 'subgroup', 'variable'))


class ExchangeItem(abc.ABC):
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

    >>> from hydpy.core.itemtools import SetItem
    >>> item = SetItem(
    ...     'alpha', 'hland_v1', 'control.alpha', 'control.beta', 0)
    >>> item.targetseries
    False
    >>> item.baseseries
    False
    >>> item.collect_variables(pub.selections)
    >>> land_dill = hp.elements.land_dill
    >>> control = land_dill.model.parameters.control
    >>> item.device2target[land_dill] is control.alpha
    True
    >>> item.device2base[land_dill] is control.beta
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

    >>> item = SetItem('ic', 'hland', 'states.ic')
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
    >>> item = SetItem('t', 'hland', 'inputs.t.series')
    >>> item.collect_variables(pub.selections)
    >>> item.device2target[land_lahn_3]
    t(nan)
    >>> item.targetseries
    True

    >>> item = SetItem('sim', 'node', 'sim')
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
    >>> item = SetItem('sim', 'node', 'sim.series')
    >>> item.collect_variables(pub.selections)
    >>> dill = hp.nodes.dill
    >>> item.device2target[dill]
    sim(0.0)
    """

    _master: str
    _target: _Properties
    _base: _Properties
    device2target: Dict
    device2base: Dict

    @staticmethod
    def _get_seriesflag_and_subgroup_and_variable(string):
        if string is None:
            return None, None, None
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

    @staticmethod
    def _query_elementvariable(element: devicetools.Element, properties):
        model = element.model
        for group in (model.parameters, model.sequences):
            subgroup = getattr(group, properties.subgroup, None)
            if subgroup is not None:
                return getattr(subgroup, properties.variable)

    @staticmethod
    def _query_nodevariable(node: devicetools.Node, properties):
        return getattr(node.sequences, properties.variable)

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        properties_ = [self._target]
        if self._base.variable is not None:
            properties_.append(self._base)
        for properties, dict_ in zip(properties_, [self.device2target, self.device2base]):
            if self._master == 'node':
                for node in selections.nodes:
                    variable = self._query_nodevariable(node, properties)
                    dict_[node] = variable
            else:
                for element in self._iter_relevantelements(selections):
                    variable = self._query_elementvariable(element, properties)
                    dict_[element] = variable


class NonGetItem(ExchangeItem, metaclass=abc.ABCMeta):

    def __init__(
            self, name: str, master: str, target: str,
            base: str = None, ndim: int = 0):
        self.name = str(name)
        self._master = master
        self._target = _Properties(
            *self._get_seriesflag_and_subgroup_and_variable(target))
        self._base = _Properties(
            *self._get_seriesflag_and_subgroup_and_variable(base))
        self.targetseries = self._target.series
        self.baseseries = self._base.series
        self.ndim = int(ndim)
        self._value: numpy.ndarray = None
        self.shape: Tuple[int] = None
        self.device2target = {}
        self.device2base = {}

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
        try:
            self._value = numpy.full(self.shape, value, dtype=float)
        except BaseException:
            objecttools.augment_excmessage(
                f'When letting item `{self.name}` convert the given '
                f'value(s) `{value}` to a numpy array of shape '
                f'`{self.shape}` and type `float`')

    @abc.abstractmethod
    def update_variables(self):
        ...

    def collect_variables(self, selections: selectiontools.Selections):
        super().collect_variables(selections)
        self.determine_shape()


class SetItem(NonGetItem):
    """

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
    ValueError: When letting item `fc` convert the given value(s) \
`(100.0, 200.0, 300.0, 400.0)` to a numpy array of shape `(5,)` and type \
`float`, the following error occurred: could not broadcast input array \
from shape (4) into shape (5)
    """

    def update_variables(self):
        value = self.value
        for variable in self.device2target.values():
            try:
                variable(value)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While letting "set item" `{self.name}` '
                    f'assign the new value(s) `{value}` to variable '
                    f'{objecttools.devicephrase(variable)}')


class AddItem(NonGetItem):
    """

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> from hydpy import HydPy, pub, TestIO
    >>> with TestIO():
    ...     hp = HydPy('LahnH')
    ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
    ...     hp.prepare_everything()

    >>> from hydpy.core.itemtools import AddItem
    >>> item = AddItem(
    ...     'sfcf', 'hland_v1', 'control.sfcf', 'control.rfcf', ndim=0)
    >>> item.collect_variables(pub.selections)

    >>> item.shape
    ()
    >>> item.value

    >>> land_dill = hp.elements.land_dill
    >>> land_dill.model.parameters.control.rfcf
    rfcf(1.04283)
    >>> land_dill.model.parameters.control.sfcf
    sfcf(1.1)

    >>> item.value = 0.1
    >>> item.value
    array(0.1)
    >>> land_dill.model.parameters.control.sfcf
    sfcf(1.1)


    >>> item.update_variables()
    >>> land_dill.model.parameters.control.sfcf
    sfcf(1.14283)

    """

    def update_variables(self):
        value = self.value
        for device, target in self.device2target.items():
            base = self.device2base[device]
            try:
                result = base + value
            except BaseException:
                objecttools.augment_excmessage(
                    f'While letting "add item" `{self.name}` add up '
                    f'the new value(s) `{value}` and the current value(s) '
                    f'of variable {objecttools.devicephrase(base)}')
            try:
                target(result)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While letting "add item" `{self.name}` assign '
                    f'the calculated sum(s) `{result}` to variable '
                    f'{objecttools.devicephrase(target)}')


class GetItem(ExchangeItem):
    """

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    >>> from hydpy import HydPy, pub, TestIO
    >>> with TestIO():
    ...     hp = HydPy('LahnH')
    ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
    ...     hp.prepare_everything()

    >>> from hydpy.core.itemtools import SetItem
    >>> item = GetItem('hland_v1', 'states.lz')
    >>> item.collect_variables(pub.selections)
    >>> hp.elements.land_dill.model.sequences.states.lz = 100.0
    >>> for name, value in item:
    ...     print(f'{name} = {value}')
    land_dill_states_lz = 100.0
    land_lahn_1_states_lz = 8.18711
    land_lahn_2_states_lz = 10.14007
    land_lahn_3_states_lz = 7.52648

    >>> item = GetItem('hland_v1', 'states.sm')
    >>> item.collect_variables(pub.selections)
    >>> hp.elements.land_dill.model.sequences.states.sm = 2.0
    >>> for name, value in item:
    ...     print(f'{name} = {value}')    # doctest: +ELLIPSIS
    land_dill_states_sm = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, \
2.0, 2.0]
    land_lahn_1_states_sm = [99.275...
    ...
    """

    def __init__(self, master: str, target: str):
        self.target = target.replace('.', '_')
        self._master = master
        self._target = _Properties(
            *self._get_seriesflag_and_subgroup_and_variable(target))
        self._base = _Properties(None, None, None)
        self.targetseries = self._target.series
        self.baseseries = None
        self.ndim = None
        self.device2target = {}
        self.device2base = {}
        self.device2name = {}

    def collect_variables(self, selections: selectiontools.Selections):
        super().collect_variables(selections)
        self.determine_equations()
        for target in self.device2target.values():
            self.ndim = target.NDIM
            if self.targetseries:
                self.ndim += 1
            break

    def determine_equations(self):
        for device in sorted(self.device2target.keys()):
            self.device2name[device] = f'{device.name}_{self.target}'

    def __iter__(self):
        for device, name in self.device2name.items():
            target = self.device2target[device]
            values = target.series if self.targetseries else target.values
            if self.ndim == 0:
                values = float(values)
            else:
                values = values.tolist()
            yield name, str(values)
