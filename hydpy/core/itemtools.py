# -*- coding: utf-8 -*-
"""This module implements so-called exchange items, simplifying the
modification of the values of |Parameter| and |Sequence_| objects."""
# import...
# ...from standard library
from typing import *

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *


Device2Target = Dict[
    Union[devicetools.Node, devicetools.Element],
    variabletools.Variable[Any, Any],
]


class ExchangeSpecification:
    """Specification of a specific |Parameter| or |Sequence_| type.

    |ExchangeSpecification| is a helper class for |ExchangeItem| and its
    subclasses. Its constructor interprets two strings (without any checks
    on plausibility) and makes their information available as attributes.
    The following tests list the expected cases:

    >>> from hydpy.core.itemtools import ExchangeSpecification
    >>> ExchangeSpecification("hland_v1", "fluxes.qt")
    ExchangeSpecification("hland_v1", "fluxes.qt")
    >>> ExchangeSpecification("hland_v1", "fluxes.qt.series")
    ExchangeSpecification("hland_v1", "fluxes.qt.series")
    >>> ExchangeSpecification("node", "sim")
    ExchangeSpecification("node", "sim")
    >>> ExchangeSpecification("node", "sim.series")
    ExchangeSpecification("node", "sim.series")

    The following attributes are accessible:

    >>> spec = ExchangeSpecification("hland_v1", "fluxes.qt")
    >>> spec
    ExchangeSpecification("hland_v1", "fluxes.qt")
    >>> spec.master
    'hland_v1'
    >>> spec.subgroup
    'fluxes'
    >>> spec.variable
    'qt'
    >>> spec.series
    False
    """

    master: str
    entries: List[str]
    series: bool
    subgroup: Optional[str]

    def __init__(
        self,
        master: str,
        variable: str,
    ) -> None:
        self.master = master
        entries = variable.split(".")
        self.series = entries[-1] == "series"
        if self.series:
            del entries[-1]
        try:
            self.subgroup, self.variable = entries
        except ValueError:
            self.subgroup, self.variable = None, entries[0]

    @property
    def specstring(self) -> str:
        """The string corresponding to the current values of `subgroup`,
        `state`, and `variable`.

        >>> from hydpy.core.itemtools import ExchangeSpecification
        >>> spec = ExchangeSpecification("hland_v1", "fluxes.qt")
        >>> spec.specstring
        'fluxes.qt'
        >>> spec.series = True
        >>> spec.specstring
        'fluxes.qt.series'
        >>> spec.subgroup = None
        >>> spec.specstring
        'qt.series'
        """
        if self.subgroup is None:
            variable = self.variable
        else:
            variable = f"{self.subgroup}.{self.variable}"
        if self.series:
            variable = f"{variable}.series"
        return variable

    def __repr__(self) -> str:
        return f'ExchangeSpecification("{self.master}", "{self.specstring}")'


class ExchangeItem:
    """Base class for exchanging values with multiple |Parameter| or
    |Sequence_| objects of a certain type."""

    master: str
    targetspecs: ExchangeSpecification
    device2target: Device2Target
    ndim: int

    def _iter_relevantelements(
        self,
        selections: selectiontools.Selections,
    ) -> Iterator[devicetools.Element]:
        for element in selections.elements:
            name1 = element.model.name
            name2 = name1.rpartition("_")[0]
            if self.targetspecs.master in (name1, name2):
                yield element

    @staticmethod
    def _query_elementvariable(
        element: devicetools.Element,
        properties: ExchangeSpecification,
    ) -> variabletools.Variable[Any, Any]:
        model = element.model
        for group in (model.parameters, model.sequences):
            if properties.subgroup is not None:
                subgroup = getattr(group, properties.subgroup, None)
                if subgroup is not None:
                    variable_ = subgroup[properties.variable]
                    assert isinstance(variable_, variabletools.Variable)
                    return variable_
        raise RuntimeError(
            f"Model {objecttools.elementphrase(model)} does neither handle "
            f"a parameter of sequence subgroup named `{properties.subgroup}."
        )

    @staticmethod
    def _query_nodevariable(
        node: devicetools.Node,
        properties: ExchangeSpecification,
    ) -> sequencetools.NodeSequence:
        sequence = getattr(node.sequences, properties.variable)
        assert isinstance(sequence, sequencetools.NodeSequence)
        return sequence

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ExchangeItem.insert_variables| to collect the
        relevant target variables handled by the devices of the given
        |Selections| object.

        We prepare the `LahnH` example project to be able to use its
        |Selections| object:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        We change the type of a specific application model to the type
        of its base model for reasons explained later:

        >>> from hydpy.models.hland import Model
        >>> hp.elements.land_lahn_3.model.__class__ = Model

        We prepare a |SetItem| as an example, handling all |hland_states.Ic|
        sequences corresponding to any application models derived from |hland|:

        >>> from hydpy import SetItem
        >>> item = SetItem("ic", "hland", "states.ic", 0)
        >>> item.targetspecs
        ExchangeSpecification("hland", "states.ic")

        Applying method |ExchangeItem.collect_variables| connects the |SetItem|
        object with all four relevant |hland_states.Ic| objects:

        >>> item.collect_variables(pub.selections)
        >>> land_dill = hp.elements.land_dill
        >>> sequence = land_dill.model.sequences.states.ic
        >>> item.device2target[land_dill] is sequence
        True
        >>> for element in sorted(item.device2target, key=lambda x: x.name):
        ...     print(element)
        land_dill
        land_lahn_1
        land_lahn_2
        land_lahn_3

        Asking for |hland_states.Ic| objects corresponding to application
        model |hland_v1| only, results in skipping the |Element| `land_lahn_3`
        (handling the |hland| base model due to the hack above):

        >>> item = SetItem("ic", "hland_v1", "states.ic", 0)
        >>> item.collect_variables(pub.selections)
        >>> for element in sorted(item.device2target, key=lambda x: x.name):
        ...     print(element)
        land_dill
        land_lahn_1
        land_lahn_2

        Selecting a series of a variable instead of the variable itself
        only affects the `targetspec` attribute:

        >>> item = SetItem("t", "hland_v1", "inputs.t.series", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.targetspecs
        ExchangeSpecification("hland_v1", "inputs.t.series")
        >>> sequence = land_dill.model.sequences.inputs.t
        >>> item.device2target[land_dill] is sequence
        True

        To pass an ill-defined subgroup name results in the following error:

        >>> from hydpy import SetItem
        >>> item = SetItem("ic", "hland", "wrong_group.wrong_variable", 0)
        >>> item.collect_variables(pub.selections)
        Traceback (most recent call last):
        ...
        RuntimeError: Model `hland_v1` of element `land_dill` does neither \
handle a parameter of sequence subgroup named `wrong_group.

        It is both possible to address sequences of |Node| objects, as well
        as their time series, by arguments "node" and "nodes":

        >>> item = SetItem("sim", "node", "sim", 0)
        >>> item.collect_variables(pub.selections)
        >>> dill = hp.nodes.dill
        >>> item.targetspecs
        ExchangeSpecification("node", "sim")
        >>> item.device2target[dill] is dill.sequences.sim
        True
        >>> for node in sorted(item.device2target, key=lambda x: x.name):
        ...  print(node)
        dill
        lahn_1
        lahn_2
        lahn_3
        >>> item = SetItem("sim", "nodes", "sim.series", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.targetspecs
        ExchangeSpecification("nodes", "sim.series")
        >>> for node in sorted(item.device2target, key=lambda x: x.name):
        ...  print(node)
        dill
        lahn_1
        lahn_2
        lahn_3
        """
        self.insert_variables(self.device2target, self.targetspecs, selections)

    def insert_variables(
        self,
        device2variable: Device2Target,
        exchangespec: ExchangeSpecification,
        selections: selectiontools.Selections,
    ) -> None:
        """Determine the relevant target or base variables (as defined by
        the given |ExchangeSpecification| object) handled by the given
        |Selections| object and insert them into the given `device2variable`
        dictionary."""
        variable: variabletools.Variable[Any, Any]
        if self.targetspecs.master in ("node", "nodes"):
            for node in selections.nodes:
                variable = self._query_nodevariable(node, exchangespec)
                device2variable[node] = variable
        else:
            for element in self._iter_relevantelements(selections):
                variable = self._query_elementvariable(element, exchangespec)
                device2variable[element] = variable


class ChangeItem(ExchangeItem):
    """Base class for changing the values of multiple |Parameter| or
    |Sequence_| objects of a specific type."""

    name: Name
    ndim: int
    _shape: Optional[Tuple[int, ...]]
    _value: numpy.ndarray
    device2target: Device2Target

    @property
    def shape(self) -> Tuple[int, ...]:
        """The shape of the target variables.

        Trying to access property |ChangeItem.shape| before calling method
        |ChangeItem.collect_variables| results in the following error:

        >>> from hydpy import SetItem
        >>> SetItem("name", "master", "target", 0).shape
        Traceback (most recent call last):
        ...
        RuntimeError: The shape of SetItem `name` has not been determined so far.

        See method |ChangeItem.collect_variables| for further information.
        """
        if self._shape is not None:
            return self._shape
        raise RuntimeError(
            f"The shape of {type(self).__name__} `{self.name}` "
            f"has not been determined so far."
        )

    @property
    def value(self) -> numpy.ndarray:
        """The value(s) that can be used to change the values of target
        variables through applying method |ChangeItem.update_variables|
        of class |ChangeItem|.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import SetItem
        >>> item = SetItem("ic", "hland", "states.ic", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.value = 1
        >>> item.value
        array(1.0)
        >>> item.value = 1, 2
        Traceback (most recent call last):
        ...
        ValueError: When trying to convert the value(s) `(1, 2)` assigned to \
SetItem `ic` to a numpy array of shape `()` and type `float`, the following error \
occurred: could not broadcast input array from shape (2,) into shape ()
        """
        return self._value

    @value.setter
    def value(self, value: numpy.ndarray) -> None:
        try:
            self._value = numpy.full(self.shape, value, dtype=float)
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to convert the value(s) `{value}` assigned "
                f"to {type(self).__name__} `{self.name}` to a "
                f"numpy array of shape `{self.shape}` and type `float`"
            )

    def update_variables(self) -> None:
        """Subclasses must define a mathematical operation for updating
        the values of target variables.

        >>> from hydpy.core.itemtools import ChangeItem
        >>> ChangeItem().update_variables()
        Traceback (most recent call last):
        ...
        NotImplementedError
        """
        raise NotImplementedError

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ExchangeItem.collect_variables| of the base class
        |ExchangeItem| and determine the |ChangeItem.shape| of the current
        |ChangeItem| object afterwards, depending on its dimensionality
        and eventually on the shape of its target variables.

        For the following examples, we prepare the `LahnH` example project:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        0-dimensional change-items do not have a variable shape, which is
        indicated by an empty tuple:

        >>> from hydpy import SetItem
        >>> item = SetItem("ic", "hland", "states.ic", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        ()

        1-dimensional change-items take the shape of their target variables,
        which must be equal for all instances:

        >>> item = SetItem("ic", "hland", "states.ic", 1)
        >>> item.collect_variables(pub.selections)
        Traceback (most recent call last):
        ...
        RuntimeError: SetItem `ic` cannot handle target variables of \
different shapes.

        >>> for element in hp.elements.catchment:
        ...     element.model.parameters.control.nmbzones(3)
        >>> item = SetItem("ic", "hland", "states.ic", 1)
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (3,)

        Passing a |Selections| object not containing any relevant target
        variables results in the following error:

        >>> item = SetItem("ic", "hland", "states.ic", 1)
        >>> from hydpy import Selections
        >>> item.collect_variables(Selections())
        Traceback (most recent call last):
        ...
        RuntimeError: Cannot determine the shape of the actual `SetItem` \
object, as the given `Selections` object does not handle any relevant \
target variables.
        """
        super().collect_variables(selections)
        self._determine_shape()

    def _determine_shape(self) -> None:
        if self.ndim == 0:
            self._shape = ()
        else:
            shape = None
            for variable in self.device2target.values():
                if shape is None:
                    shape = variable.shape
                else:
                    if shape != variable.shape:
                        raise RuntimeError(
                            f"{type(self).__name__} `{self.name}` cannot handle "
                            f"target variables of different shapes."
                        )
            if shape is None:
                raise RuntimeError(
                    f"Cannot determine the shape of the actual "
                    f"`{type(self).__name__}` object, as the given "
                    f"`Selections` object does not handle any "
                    f"relevant target variables."
                )
            self._shape = shape

    def update_variable(
        self,
        variable: variabletools.Variable[Any, Any],
        value: numpy.ndarray,
    ) -> None:
        """Assign the given value(s) to the given target or base variable.

        If the assignment fails, |ChangeItem.update_variable| raises an
        error like the following:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> item = SetItem("alpha", "hland_v1", "control.alpha", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.update_variables()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: When trying to update a target variable of SetItem `alpha` \
with the value(s) `None`, the following error occurred: While trying to set \
the value(s) of variable `alpha` of element `...`, the following error \
occurred: The given value `None` cannot be converted to type `float`.
        """
        try:
            variable(value)
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to update a target variable of {type(self).__name__} "
                f"`{self.name}` with the value(s) `{value}`"
            )


class SetItem(ChangeItem):
    """Item for assigning |ChangeItem.value| to multiple |Parameter| or
    |Sequence_| objects of a specific type."""

    def __init__(
        self,
        name: str,
        master: str,
        target: str,
        ndim: int,
    ) -> None:
        self.name = Name(name)
        self.targetspecs = ExchangeSpecification(master, target)
        self.ndim = int(ndim)
        self._value = None
        self._shape = None
        self.device2target = {}

    def update_variables(self) -> None:
        """Assign the current objects |ChangeItem.value| to the values
        of the target variables.

        We use the `LahnH` project in the following:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        In the first example, a 0-dimensional |SetItem| changes the value
        of the 0-dimensional parameter |hland_control.Alpha|:

        >>> from hydpy.core.itemtools import SetItem
        >>> item = SetItem("alpha", "hland_v1", "control.alpha", 0)
        >>> item
        SetItem("alpha", "hland_v1", "control.alpha", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.value is None
        True
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

        In the second example, a 0-dimensional |SetItem| changes the values
        of the 1-dimensional parameter |hland_control.FC|:


        >>> item = SetItem("fc", "hland_v1", "control.fc", 0)
        >>> item.collect_variables(pub.selections)
        >>> item.value = 200.0
        >>> land_dill.model.parameters.control.fc
        fc(278.0)
        >>> item.update_variables()
        >>> land_dill.model.parameters.control.fc
        fc(200.0)

        In the third example, a 1-dimensional |SetItem| changes the values
        of the 1-dimensional sequence |hland_states.Ic|:

        >>> for element in hp.elements.catchment:
        ...     element.model.parameters.control.nmbzones(5)
        ...     element.model.parameters.control.icmax(4.0)
        >>> item = SetItem("ic", "hland_v1", "states.ic", 1)
        >>> item.collect_variables(pub.selections)
        >>> land_dill.model.sequences.states.ic
        ic(nan, nan, nan, nan, nan)
        >>> item.value = 2.0
        >>> item.update_variables()
        >>> land_dill.model.sequences.states.ic
        ic(2.0, 2.0, 2.0, 2.0, 2.0)
        >>> item.value = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> item.update_variables()
        >>> land_dill.model.sequences.states.ic
        ic(1.0, 2.0, 3.0, 4.0, 4.0)
        """
        value = self.value
        for variable in self.device2target.values():
            self.update_variable(variable, value)

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}("{self.name}", '
            f'"{self.targetspecs.master}", "{self.targetspecs.specstring}", '
            f"{self.ndim})"
        )


class MathItem(ChangeItem):
    # pylint: disable=abstract-method
    # due to pylint issue https://github.com/PyCQA/pylint/issues/179
    """Base class for performing some mathematical operations on the given
    values before assigning them to the handled target variables.

    Subclasses of |MathItem| like |AddItem| handle not only target
    variables but also base variables:

    >>> from hydpy import AddItem
    >>> item = AddItem(
    ...     "sfcf", "hland_v1", "control.sfcf", "control.rfcf", 0)
    >>> item
    AddItem("sfcf", "hland_v1", "control.sfcf", "control.rfcf", 0)
    >>> item.targetspecs
    ExchangeSpecification("hland_v1", "control.sfcf")
    >>> item.basespecs
    ExchangeSpecification("hland_v1", "control.rfcf")

    Generally, a |MathItem| calculates the target variable of a specific
    |Device| object by using its current |ChangeItem.value| and the value(s)
    of the base variable of the same |Device|.
    """

    basespecs: ExchangeSpecification
    device2base: Device2Target

    def __init__(
        self,
        name: str,
        master: str,
        target: str,
        base: str,
        ndim: int,
    ) -> None:
        self.name = Name(name)
        self.targetspecs = ExchangeSpecification(master, target)
        self.basespecs = ExchangeSpecification(master, base)
        self.ndim = int(ndim)
        self._value = None
        self._shape = None
        self.device2target = {}
        self.device2base = {}

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ChangeItem.collect_variables| of the base class
        |ChangeItem| and also apply method |ExchangeItem.insert_variables|
        of class |ExchangeItem| to collect the relevant base variables
        handled by the devices of the given |Selections| object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import AddItem
        >>> item = AddItem("alpha", "hland_v1", "control.sfcf", "control.rfcf", 0)
        >>> item.collect_variables(pub.selections)
        >>> land_dill = hp.elements.land_dill
        >>> control = land_dill.model.parameters.control
        >>> item.device2target[land_dill] is control.sfcf
        True
        >>> item.device2base[land_dill] is control.rfcf
        True
        >>> for device in sorted(item.device2base, key=lambda x: x.name):
        ...     print(device)
        land_dill
        land_lahn_1
        land_lahn_2
        land_lahn_3
        """
        super().collect_variables(selections)
        self.insert_variables(self.device2base, self.basespecs, selections)

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}("{self.name}", '
            f'"{self.targetspecs.master}", "{self.targetspecs.specstring}", '
            f'"{self.basespecs.specstring}", {self.ndim})'
        )


class AddItem(MathItem):
    """|MathItem| subclass performing additions."""

    def update_variables(self) -> None:
        """Add the general |ChangeItem.value| with the |Device| specific base
        variable and assign the result to the respective target variable.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.models.hland_v1 import FIELD
        >>> for element in hp.elements.catchment:
        ...     control = element.model.parameters.control
        ...     control.nmbzones(3)
        ...     control.zonetype(FIELD)
        ...     control.rfcf(1.1)
        >>> from hydpy.core.itemtools import AddItem
        >>> item = AddItem(
        ...     "sfcf", "hland_v1", "control.sfcf", "control.rfcf", 1)
        >>> item.collect_variables(pub.selections)
        >>> land_dill = hp.elements.land_dill
        >>> land_dill.model.parameters.control.sfcf
        sfcf(?)
        >>> item.value = -0.1, 0.0, 0.1
        >>> item.update_variables()
        >>> land_dill.model.parameters.control.sfcf
        sfcf(1.0, 1.1, 1.2)

        >>> land_dill.model.parameters.control.rfcf.shape = 2
        >>> land_dill.model.parameters.control.rfcf = 1.1
        >>> item.update_variables()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: When trying to add the value(s) `[-0.1  0.   0.1]` of \
AddItem `sfcf` and the value(s) `[ 1.1  1.1]` of variable `rfcf` of element \
`land_dill`, the following error occurred: operands could not be broadcast \
together with shapes (2,) (3,)...
        """
        value = self.value
        for device, target in self.device2target.items():
            base = self.device2base[device]
            try:
                result = base.value + value
            except BaseException:
                objecttools.augment_excmessage(
                    f"When trying to add the value(s) `{value}` of "
                    f"AddItem `{self.name}` and the value(s) `{base.value}` "
                    f"of variable {objecttools.devicephrase(base)}"
                )
            self.update_variable(target, result)


class GetItem(ExchangeItem):
    """Base class for querying the values of multiple |Parameter| or
    |Sequence_| objects of a specific type."""

    _device2name: Dict[Union[devicetools.Node, devicetools.Element], Name]

    def __init__(self, master: str, target: str) -> None:
        self.target = target.replace(".", "_")
        self.targetspecs = ExchangeSpecification(master, target)
        self.ndim = 0
        self.device2target = {}
        self._device2name = {}

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ExchangeItem.collect_variables| of the base class
        |ExchangeItem| and determine the `ndim` attribute of the current
        |ChangeItem| object afterwards.

        The value of `ndim` depends on whether the values of the target
        variable or its time series are of interest:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import SetItem
        >>> for target in ("states.lz", "states.lz.series",
        ...                "states.sm", "states.sm.series"):
        ...     item = GetItem("hland_v1", target)
        ...     item.collect_variables(pub.selections)
        ...     print(item, item.ndim)
        GetItem("hland_v1", "states.lz") 0
        GetItem("hland_v1", "states.lz.series") 1
        GetItem("hland_v1", "states.sm") 1
        GetItem("hland_v1", "states.sm.series") 2
        """
        super().collect_variables(selections)
        for device in sorted(self.device2target.keys(), key=lambda x: x.name):
            self._device2name[device] = Name(f"{device.name}_{self.target}")
        for target in self.device2target.values():
            self.ndim = target.NDIM
            if self.targetspecs.series:
                self.ndim += 1
            break

    def yield_name2value(
        self,
        idx1: Optional[int] = None,
        idx2: Optional[int] = None,
    ) -> Iterator[Tuple[Name, str]]:
        """Sequentially return name-value-pairs describing the current state
        of the target variables.

        The names are automatically generated and contain both the name of
        the |Device| of the respective |Variable| object and the target
        description:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import SetItem
        >>> item = GetItem("hland_v1", "states.lz")
        >>> item.collect_variables(pub.selections)
        >>> hp.elements.land_dill.model.sequences.states.lz = 100.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)
        land_dill_states_lz 100.0
        land_lahn_1_states_lz 8.18711
        land_lahn_2_states_lz 10.14007
        land_lahn_3_states_lz 7.52648
        >>> item = GetItem("hland_v1", "states.sm")
        >>> item.collect_variables(pub.selections)
        >>> hp.elements.land_dill.model.sequences.states.sm = 2.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)    # doctest: +ELLIPSIS
        land_dill_states_sm [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, \
2.0, 2.0, 2.0, 2.0]
        land_lahn_1_states_sm [99.27505, ..., 142.84148]
        ...

        When querying time series, one can restrict the span of interest
        by passing index values:

        >>> item = GetItem("nodes", "sim.series")
        >>> item.collect_variables(pub.selections)
        >>> hp.nodes.dill.sequences.sim.series = 1.0, 2.0, 3.0, 4.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)    # doctest: +ELLIPSIS
        dill_sim_series [1.0, 2.0, 3.0, 4.0]
        lahn_1_sim_series [nan, ...
        ...
        >>> for name, value in item.yield_name2value(2, 3):
        ...     print(name, value)    # doctest: +ELLIPSIS
        dill_sim_series [3.0]
        lahn_1_sim_series [nan]
        ...
        """
        for device, name in self._device2name.items():
            target = self.device2target[device]
            if self.targetspecs.series:
                assert isinstance(target, sequencetools.IOSequence)
                values = target.series[idx1:idx2]
            else:
                values = target.values
            if self.ndim == 0:
                values = objecttools.repr_(float(values))
            else:
                values = objecttools.repr_list(values.tolist())
            yield name, values

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f'"{self.targetspecs.master}", "{self.targetspecs.specstring}")'
        )
