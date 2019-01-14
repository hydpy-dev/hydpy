# -*- coding: utf-8 -*-
"""This module implements so-called exchange items, simplifying the
modification of the values of |Parameter| and |Sequence| objects.
"""
# import...
# ...from standard library
import abc
from typing import Dict, Iterator, Tuple
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import selectiontools
from hydpy.core import variabletools


class ExchangeSpecification(object):
    """Specification of a specific |Parameter| or |Sequence| type.

    |ExchangeSpecification| is a helper class for |ExchangeItem| and its
    subclasses. Its constructor interprets two strings (without any checks
    on plausibility) and makes their information available as attributes.
    The following tests list the expected cases:

    >>> from hydpy.core.itemtools import ExchangeSpecification
    >>> spec = ExchangeSpecification('hland_v1', 'fluxes.qt')
    >>> spec
    ExchangeSpecification('hland_v1', 'fluxes.qt')
    >>> spec.master
    'hland_v1'
    >>> spec.subgroup
    'fluxes'
    >>> spec.variable
    'qt'
    >>> spec.series
    False

    >>> spec = ExchangeSpecification('hland_v1', 'fluxes.qt.series')
    >>> spec
    ExchangeSpecification('hland_v1', 'fluxes.qt.series')
    >>> spec.master
    'hland_v1'
    >>> spec.subgroup
    'fluxes'
    >>> spec.variable
    'qt'
    >>> spec.series
    True

    >>> spec = ExchangeSpecification('node', 'sim')
    >>> spec
    ExchangeSpecification('node', 'sim')
    >>> spec.master
    'node'
    >>> spec.subgroup
    >>> spec.variable
    'sim'
    >>> spec.series
    False

    >>> spec = ExchangeSpecification('node', 'sim.series')
    >>> spec
    ExchangeSpecification('node', 'sim.series')
    >>> spec.master
    'node'
    >>> spec.subgroup
    >>> spec.variable
    'sim'
    >>> spec.series
    True
    """
    def __init__(self, master, variable):
        self.master = master
        entries = variable.split('.')
        entries = variable.split('.')
        self.series = entries[-1] == 'series'
        if self.series:
            del entries[-1]
        try:
            self.subgroup, self.variable = entries
        except ValueError:
            self.subgroup, self.variable = None, entries[0]

    def __repr__(self):
        if self.subgroup is None:
            variable = self.variable
        else:
            variable = f'{self.subgroup}.{self.variable}'
        if self.series:
            variable = f'{variable}.series'
        return f"ExchangeSpecification('{self.master}', '{variable}')"


class ExchangeItem(abc.ABC):
    """Base class for exchanging values with multiple |Parameter| or |Sequence|
    objects of a certain type."""

    master: str
    targetspecs: ExchangeSpecification
    device2target: Dict

    def _iter_relevantelements(self, selections: selectiontools.Selections) -> \
            Iterator[devicetools.Element]:
        for element in selections.elements:
            name1 = element.model.name
            name2 = name1.rpartition('_')[0]
            if self.targetspecs.master in (name1, name2):
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

    def collect_variables(self, selections) -> None:
        """Apply method |ExchangeItem.insert_variables| to collect the
        relevant target variables handled by the devices of the given
        |Selections| object.
        """
        self.insert_variables(self.device2target, self.targetspecs, selections)

    def insert_variables(
            self, device2variable, exchangespec, selections) -> None:
        """Determine the relevant target or base variables (as defined by the
        given |ExchangeSpecification|) handled by the given |Selections|
        object and insert them into the given `device2variable` dictionary.

        First, we prepare the `LahnH` example project, to be able to use
        its |Selection| "complete":

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
        ...     hp.prepare_everything()

        Second, we change the type of a specific application model to
        its base model for reasons explained later:

        >>> from hydpy.models.hland import Model
        >>> hp.elements.land_lahn_3.model.__class__ = Model



        >>> from hydpy.core.itemtools import AddItem, SetItem
        >>> item = AddItem(
        ...     'alpha', 'hland_v1', 'control.alpha', 'control.beta', 0)
        >>> item.targetspecs
        ExchangeSpecification('hland_v1', 'control.alpha')
        >>> item.basespecs
        ExchangeSpecification('hland_v1', 'control.beta')
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

        >>> item = SetItem('ic', 'hland', 'states.ic', 0)
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
        >>> item = SetItem('t', 'hland', 'inputs.t.series', 0)
        >>> item.collect_variables(pub.selections)
        >>> item.device2target[land_lahn_3]
        t(nan)
        >>> item.targetspecs.series
        True

        >>> item = SetItem('sim', 'node', 'sim', 0)
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
        >>> item = SetItem('sim', 'node', 'sim.series', 0)
        >>> item.collect_variables(pub.selections)
        >>> dill = hp.nodes.dill
        >>> item.device2target[dill]
        sim(0.0)
        """
        if self.targetspecs.master in ('node', 'nodes'):
            for node in selections.nodes:
                variable = self._query_nodevariable(node, exchangespec)
                device2variable[node] = variable
        else:
            for element in self._iter_relevantelements(selections):
                variable = self._query_elementvariable(element, exchangespec)
                device2variable[element] = variable


class ChangeItem(ExchangeItem, metaclass=abc.ABCMeta):
    """Base class for changing the values of multiple |Parameter| or |Sequence|
    objects of a certain type."""

    name: str
    ndim: int
    shape: Tuple[int]
    _value: numpy.ndarray

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


class SetItem(ChangeItem):
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

    def __init__(self, name, master, target, ndim):
        self.name = str(name)
        self.targetspecs = ExchangeSpecification(master, target)
        self.ndim = int(ndim)
        self._value: numpy.ndarray = None
        self.shape: Tuple[int] = None
        self.device2target: \
            Dict[devicetools.Device, variabletools.Variable] = {}

    def update_variables(self) -> None:
        value = self.value
        for variable in self.device2target.values():
            try:
                variable(value)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While letting "set item" `{self.name}` '
                    f'assign the new value(s) `{value}` to variable '
                    f'{objecttools.devicephrase(variable)}')


class MathItem(ChangeItem, metaclass=abc.ABCMeta):

    basespecs: ExchangeSpecification
    device2base: Dict

    def __init__(self, name, master, target, base, ndim):
        self.name = str(name)
        self.targetspecs = ExchangeSpecification(master, target)
        self.basespecs = ExchangeSpecification(master, base)
        self.ndim = int(ndim)
        self._value = None
        self.shape = None
        self.device2target = {}
        self.device2base = {}

    def collect_variables(self, selections) -> None:
        super().collect_variables(selections)
        self.insert_variables(self.device2base, self.basespecs, selections)


class AddItem(MathItem):
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
                raise objecttools.augment_excmessage(
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
    """Base class for getting the values of multiple |Parameter| or |Sequence|
    objects of a certain type.

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
    >>> for name, value in item.yield_name2value():
    ...     print(f'{name} = {value}')
    land_dill_states_lz = 100.0
    land_lahn_1_states_lz = 8.18711
    land_lahn_2_states_lz = 10.14007
    land_lahn_3_states_lz = 7.52648

    >>> item = GetItem('hland_v1', 'states.sm')
    >>> item.collect_variables(pub.selections)
    >>> hp.elements.land_dill.model.sequences.states.sm = 2.0
    >>> for name, value in item.yield_name2value():
    ...     print(f'{name} = {value}')    # doctest: +ELLIPSIS
    land_dill_states_sm = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, \
2.0, 2.0]
    land_lahn_1_states_sm = [99.275...
    ...
    """

    def __init__(self, master: str, target: str):
        self.target = target.replace('.', '_')
        self.targetspecs = ExchangeSpecification(master, target)
        self.ndim = None
        self.device2target = {}
        self._device2name: Dict[devicetools.Device, str] = {}

    def collect_variables(self, selections: selectiontools.Selections):
        super().collect_variables(selections)
        for device in sorted(self.device2target.keys()):
            self._device2name[device] = f'{device.name}_{self.target}'
        for target in self.device2target.values():
            self.ndim = target.NDIM
            if self.targetspecs.series:
                self.ndim += 1
            break

    def yield_name2value(self, idx1=None, idx2=None):
        for device, name in self._device2name.items():
            target = self.device2target[device]
            if self.targetspecs.series:
                values = target.series[idx1:idx2]
            else:
                values = target.values
            if self.ndim == 0:
                values = float(values)
            else:
                values = values.tolist()
            yield name, str(values)


autodoctools.autodoc_module()
