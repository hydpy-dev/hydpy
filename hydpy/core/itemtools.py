# -*- coding: utf-8 -*-
"""This module implements so-called exchange items, simplifying the
modification of the values of |Parameter| and |Sequence_| objects."""
# import...
# ...from standard library
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

Device2Target = Dict[
    Union[devicetools.Node, devicetools.Element],
    variabletools.Variable[Any, Any],
]
Selection2Targets = Dict[str, Tuple[variabletools.Variable[Any, Any], ...]]
LevelType = Literal["global", "selection", "device", "subunit"]


class ExchangeSpecification:
    """Specification of a concrete |Parameter| or |Sequence_| type.

    |ExchangeSpecification| is a helper class for |ExchangeItem| and its subclasses.
    Its constructor interprets two strings (without any plausibility checks) and
    makes their information available as attributes.  The following tests list the
    expected cases:

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
    """Either "node" or the name of the relevant base or application model (e. g. 
    "hland_v1")."""
    variable: str
    """Name of the target or base variable."""
    series: bool
    """Flag indicating whether to tackle the target variable's actual values (|False|)
    or complete time-series (|True|)."""
    subgroup: Optional[str]
    """For model variables, the name of the parameter or sequence subgroup of the
    target or base variable; for node sequences |None|."""

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
        """The string corresponding to the current values of `subgroup`, `state`,
        and `variable`.

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
    """Base class for exchanging values with multiple |Parameter| or |Sequence_|
    objects of a concrete type."""

    name: Name
    """The name of the exchange item."""
    targetspecs: ExchangeSpecification
    """The exchange specification for the chosen target variable."""
    device2target: Device2Target
    """A target variable object for each device."""
    selection2targets: Selection2Targets
    """A tuple of target variable objects for each selection."""

    @property
    def ndim(self) -> int:
        """The number of dimensions of the handled value vector.

        Property |ExchangeItem.ndim| to be overwritten by the concrete subclasses:

        >>> from hydpy.core.itemtools import ExchangeItem
        >>> ExchangeItem().ndim
        Traceback (most recent call last):
        ...
        NotImplementedError
        """
        raise NotImplementedError()

    def _iter_relevantelements(
        self,
        selection: selectiontools.Selection,
    ) -> Iterator[devicetools.Element]:
        for element in selection.elements:
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
            f"a parameter or sequence subgroup named `{properties.subgroup}."
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
        """Collect the relevant target variables handled by the devices of the given
        |Selections| object.

        We prepare the `LahnH` example project to be able to use its |Selections|
        object:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        We change the type of a specific application model to the type of its base
        model for reasons explained later:

        >>> from hydpy.models.hland import Model
        >>> hp.elements.land_lahn_3.model.__class__ = Model

        We prepare an |ExchangeItem| as an example, handling all |hland_states.Ic|
        sequences corresponding to any application models derived from |hland|:

        >>> from hydpy.core.itemtools import ExchangeItem, ExchangeSpecification
        >>> item = ExchangeItem()

        |ExchangeItem| is only a base class.  Hence we need to prepare some missing
        attributes manually:

        >>> item.targetspecs = ExchangeSpecification("hland", "states.ic")
        >>> item.level = "global"
        >>> item.device2target = {}
        >>> item.selection2targets = {}

        Applying method |ExchangeItem.collect_variables| connects the |ExchangeItem|
        object with all four relevant |hland_states.Ic| objects:

        >>> item.collect_variables(pub.selections)
        >>> land_dill = hp.elements.land_dill
        >>> for element in sorted(item.device2target, key=lambda x: x.name):
        ...     print(element)
        land_dill
        land_lahn_1
        land_lahn_2
        land_lahn_3
        >>> item.device2target[land_dill] is land_dill.model.sequences.states.ic
        True

        Asking for |hland_states.Ic| objects corresponding to application model
        |hland_v1| only results in skipping the |Element| `land_lahn_3` (handling
        the |hland| base model due to the hack above):

        >>> item.targetspecs.master = "hland_v1"
        >>> item.device2target.clear()
        >>> item.collect_variables(pub.selections)
        >>> for element in sorted(item.device2target, key=lambda x: x.name):
        ...     print(element)
        land_dill
        land_lahn_1
        land_lahn_2
        >>> item.device2target[land_dill] is land_dill.model.sequences.states.ic
        True

        The value of sub-attribute |ExchangeSpecification.series| of attribute
        |ExchangeItem.targetspecs| does not affect the results obtained with method
        |ExchangeItem.collect_variables|:

        >>> item.targetspecs.series = True
        >>> item.collect_variables(pub.selections)
        >>> item.device2target[land_dill] is land_dill.model.sequences.states.ic
        True

        An ill-defined subgroup name results in the following error:

        >>> item.targetspecs.subgroup = "wrong_group"
        >>> item.collect_variables(pub.selections)
        Traceback (most recent call last):
        ...
        RuntimeError: Model `hland_v1` of element `land_dill` does neither \
handle a parameter or sequence subgroup named `wrong_group.

        Collecting the |Sim| or |Obs| sequences of |Node| objects works similarly:

        >>> item.targetspecs.master = "node"
        >>> item.targetspecs.variable = "sim"
        >>> item.targetspecs.subgroup = None
        >>> item.targetspecs.series = False
        >>> item.device2target.clear()
        >>> item.collect_variables(pub.selections)
        >>> dill = hp.nodes.dill
        >>> for node in sorted(item.device2target, key=lambda x: x.name):
        ...  print(node)
        dill
        lahn_1
        lahn_2
        lahn_3
        >>> item.device2target[dill] is dill.sequences.sim
        True
        """
        variable: variabletools.Variable[Any, Any]
        variables: List[variabletools.Variable[Any, Any]]
        if self.targetspecs.master in ("node", "nodes"):
            for selection in selections:
                variables = []
                for node in selection.nodes:
                    variable = self._query_nodevariable(node, self.targetspecs)
                    self.device2target[node] = variable
                    variables.append(variable)
                if variables:
                    self.selection2targets[selection.name] = tuple(variables)
        else:
            for selection in selections:
                variables = []
                for element in self._iter_relevantelements(selection):
                    variable = self._query_elementvariable(element, self.targetspecs)
                    self.device2target[element] = variable
                    variables.append(variable)
                if variables:
                    self.selection2targets[selection.name] = tuple(variables)


class ChangeItem(ExchangeItem):
    """Base class for changing the values of multiple |Parameter| or |Sequence_|
    objects of a specific type."""

    level: LevelType
    """The level at which the values of the change item are valid."""
    _shape: Optional[Union[Tuple[()], Tuple[(int, ...)]]]
    _value: Optional[numpy.ndarray]

    @property
    def ndim(self) -> int:
        """The number of dimensions of the handled value vector."""
        return (self.level != "global") + self.targetspecs.series

    @property
    def shape(self) -> Union[Tuple[()], Tuple[(int, ...)]]:
        """The shape of the target variables.

        Trying to access property |ChangeItem.shape| before calling method
        |ChangeItem.collect_variables| results in the following error:

        >>> from hydpy import SetItem
        >>> SetItem("name", "master", "target", "global").shape
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
        """The item value(s) used for changing the values of target variables through
        applying method |ChangeItem.update_variables| of class |ChangeItem|.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import SetItem
        >>> item = SetItem("ic", "hland", "states.ic", "global")
        >>> item.collect_variables(pub.selections)
        >>> item.value
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem \
`ic` has/have not been prepared so far.

        >>> item.value = 1.0
        >>> item.value
        array(1.)

        >>> item.value = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: When trying to convert the value(s) `(1.0, 2.0)` assigned to \
SetItem `ic` to a numpy array of shape `()` and type `float`, the following error \
occurred: could not broadcast input array from shape (2,) into shape ()
        """
        if self._value is None:
            raise exceptiontools.AttributeNotReady(
                f"The value(s) of the {type(self).__name__} `{self.name}` has/have "
                f"not been prepared so far."
            )
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

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ExchangeItem.collect_variables| of the base class
        |ExchangeItem| and determine the |ChangeItem.shape| of the current
        |ChangeItem| object afterwards.

        For the following examples, we prepare the `LahnH` example project and
        remove the "complete" selection from the |Selections| object available
        in module |pub|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> del pub.selections["complete"]

        After calling the method |ChangeItem.collect_variables|, attribute
        |ExchangeItem.device2target| maps all relevant devices to the chosen target
        variables:

        >>> from hydpy import SetItem
        >>> item = SetItem("ic", "hland", "states.ic", "global")
        >>> item.collect_variables(pub.selections)
        >>> for device, target in item.device2target.items():
        ...     print(device, target)   # doctest: +ELLIPSIS
        land_dill ic(0.9694, ..., 1.47487)
        land_lahn_1 ic(0.96404, ..., 1.46719)
        land_lahn_2 ic(0.96159, ..., 1.46393)
        land_lahn_3 ic(0.96064, ..., 1.46444)

        Similarly, attribute |ExchangeItem.selection2target| maps all relevant
        selections to the chosen target variables:

        >>> for selection, targets in item.selection2targets.items():
        ...     print(selection, targets)   # doctest: +ELLIPSIS
        headwaters (ic(0.9694, ..., 1.47487), ic(0.96404, ..., 1.46719))
        nonheadwaters (ic(0.96159, ..., 1.46393), ic(0.96064, ..., 1.46444))

        The |ChangeItem.shape| of a |ChangeItem| object depends on the intended
        aggregation |ChangeItem.level|.  For the "global" level, we need only one
        scalar value for all target variables.  Property |ChangeItem.shape| indicates
        this by returning an empty tuple:

        >>> item.shape
        ()

        For the "selection" level, we need one value for each relevant selection:

        >>> item = SetItem("ic", "hland", "states.ic", "selection")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (2,)

        For the "device" level, we need one value for each relevant device:

        >>> item = SetItem("ic", "hland", "states.ic", "device")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (4,)

        For the "subunit" level, we need one value for each vector entry of all
        target variables (for parameter |hland_states.IC| of base model |hland|,
        this agrees with the total number of hydrological response units):

        >>> item = SetItem("ic", "hland", "states.ic", "subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (49,)
        """
        super().collect_variables(selections)
        if self.level == "global":
            self._shape = ()
        elif self.level == "selection":
            self._shape = (len(self.selection2targets),)
        elif self.level == "device":
            self._shape = (len(self.device2target),)
        elif self.level == "subunit":
            self._shape = (sum(len(target) for target in self.device2target.values()),)

    def update_variable(
        self,
        variable: variabletools.Variable[Any, Any],
        value: numpy.ndarray,
    ) -> None:
        """Assign the given value(s) to the given target or base variable.

        If the assignment fails, |ChangeItem.update_variable| raises an error like
        the following:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import ChangeItem, ExchangeSpecification
        >>> item = ChangeItem()
        >>> item.name = "alpha"
        >>> item.targetspecs = ExchangeSpecification("hland_v1", "control.alpha")
        >>> item.level = "global"
        >>> item.device2target = {}
        >>> item.selection2targets = {}
        >>> item._value = "wrong"
        >>> item.collect_variables(pub.selections)
        >>> item.update_variables()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: When trying to update a target variable of ChangeItem `alpha` with \
the value(s) `wrong`, the following error occurred: While trying to set the value(s) \
of variable `alpha` of element `land_dill`, the following error occurred: The given \
value `wrong` cannot be converted to type `float`.
        """
        try:
            variable(value)
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to update a target variable of {type(self).__name__} "
                f"`{self.name}` with the value(s) `{value}`"
            )

    def update_variables(self) -> None:
        """Assign the current objects |ChangeItem.value| to the values of the target
        variables.

        For the following examples, we prepare the `LahnH` example project and
        remove the "complete" selection from the |Selections| object available
        in module |pub|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> del pub.selections["complete"]

        "Global" |SetItem| objects assign the same value to all chosen 0-dimensional
        target variables (we use parameter |hland_control.Alpha| as an example):

        >>> from hydpy.core.itemtools import SetItem
        >>> item = SetItem("alpha", "hland_v1", "control.alpha", "global")
        >>> item
        SetItem("alpha", "hland_v1", "control.alpha", "global")
        >>> item.collect_variables(pub.selections)
        >>> land_dill = hp.elements.land_dill
        >>> land_dill.model.parameters.control.alpha
        alpha(1.0)
        >>> item.value = 2.0
        >>> item.value
        array(2.)
        >>> land_dill.model.parameters.control.alpha
        alpha(1.0)
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, element.model.parameters.control.alpha)
        land_dill alpha(2.0)
        land_lahn_1 alpha(2.0)
        land_lahn_2 alpha(2.0)
        land_lahn_3 alpha(2.0)

        For 1-dimensional target variables like the parameter |hland_control.FC|,
        a "global" |SetItem| assigns the same value to each vector entry:

        >>> item = SetItem("fc", "hland_v1", "control.fc", "global")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 200.0
        >>> land_dill.model.parameters.control.fc
        fc(278.0)
        >>> item.update_variables()
        >>> land_dill.model.parameters.control.fc
        fc(200.0)

        When working on the "selection" level, a |SetItem| object assigns one
        specific value to the target variables of each relevant selection, regardless
        of whether these target variables are 0- or 1-dimensional:

        >>> item = SetItem("ic", "hland_v1", "states.ic", "selection")
        >>> item.collect_variables(pub.selections)
        >>> land_dill.model.sequences.states.ic    # doctest: +ELLIPSIS
        ic(0.9694, ..., 1.47487)
        >>> item.value = 0.5, 1.0
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.ic)
        land_dill ic(0.5, 0.5, ..., 0.5, 0.5)
        land_lahn_1 ic(0.5, 0.5, ..., 0.5, 0.5)
        land_lahn_2 ic(1.0, 1.0, ..., 1.0, 1.0)
        land_lahn_3 ic(1.0, 1.0, ..., 1.0, 1.0)

        In contrast, when working on the "device" level, each device receives one
        specific value (note that the final values of element `land_lahn_2` are partly
        affected and that those of element `land_lahn_3` are all affected by the
        |hland_states.IC.trim| method of sequence |hland_states.IC|):

        >>> item = SetItem("ic", "hland_v1", "states.ic", "device")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 0.5, 1.0, 1.5, 2.0
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.ic)
        land_dill ic(0.5, 0.5, ..., 0.5, 0.5)
        land_lahn_1 ic(1.0, 1.0, ... 1.0, 1.0)
        land_lahn_2 ic(1.0, 1.5, ..., 1.0, 1.5)
        land_lahn_3 ic(1.0, 1.5, ..., 1.5, 1.5)

        For the most detailed "subunit" level, the |SetItem| object handles one value
        for each of the 49 hydrological response units of the complete `Lahn` river
        basin:

        >>> item = SetItem("ic", "hland_v1", "states.ic", "subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [value/100 for value in range(49)]
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.ic)
        land_dill ic(0.0, 0.01, ..., 0.1, 0.11)
        land_lahn_1 ic(0.12, 0.13, ... 0.23, 0.24)
        land_lahn_2 ic(0.25, 0.26, ..., 0.33, 0.34)
        land_lahn_3 ic(0.35, 0.36, ..., 0.47, 0.48)
        """
        values = self.value
        if self.level == "global":
            for variable in self.device2target.values():
                self.update_variable(variable, values)
        elif self.level == "selection":
            for variables, value in zip(self.selection2targets.values(), values):
                for variable in variables:
                    self.update_variable(variable, value)
        elif self.level == "device":
            for variable, value in zip(self.device2target.values(), values):
                self.update_variable(variable, value)
        elif self.level == "subunit":
            idx0 = 0
            for variable in self.device2target.values():
                idx1 = idx0 + len(variable)
                self.update_variable(variable, values[idx0:idx1])
                idx0 = idx1


class SetItem(ChangeItem):
    """Exchange item for assigning |ChangeItem.value| to multiple |Parameter| or
    |Sequence_| objects of a specific type."""

    def __init__(
        self,
        name: str,
        master: str,
        target: str,
        level: LevelType,
    ) -> None:
        self.name = Name(name)
        self.targetspecs = ExchangeSpecification(master, target)
        self.level = level
        self._value = None
        self._shape = None
        self.device2target = {}
        self.selection2targets = {}

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}("{self.name}", '
            f'"{self.targetspecs.master}", "{self.targetspecs.specstring}", '
            f'"{self.level}")'
        )


class MathItem(ChangeItem):
    # pylint: disable=abstract-method
    # due to pylint issue https://github.com/PyCQA/pylint/issues/179
    """This base class performs some mathematical operations on the given values
    before assigning them to the handled target variables.

    Subclasses of |MathItem| like |AddItem| handle not only target variables but
    also base variables:

    >>> from hydpy.core.itemtools import MathItem
    >>> item = MathItem("sfcf", "hland_v1", "control.sfcf", "control.rfcf", "global")
    >>> item
    MathItem("sfcf", "hland_v1", "control.sfcf", "control.rfcf", "global")
    >>> item.targetspecs
    ExchangeSpecification("hland_v1", "control.sfcf")
    >>> item.basespecs
    ExchangeSpecification("hland_v1", "control.rfcf")

    Generally, each |MathItem| object calculates the value of the target variable of
    a |Device| object by using its current |ChangeItem.value| and the value(s) of the
    base variable of the same |Device|.
    """

    basespecs: ExchangeSpecification
    """The exchange specification for the chosen base variable."""
    target2base: Dict[
        variabletools.Variable[Any, Any],
        variabletools.Variable[Any, Any],
    ]
    """All target variable objects and their related base variable objects."""

    def __init__(
        self,
        name: str,
        master: str,
        target: str,
        base: str,
        level: LevelType,
    ) -> None:
        self.name = Name(name)
        self.targetspecs = ExchangeSpecification(master, target)
        self.basespecs = ExchangeSpecification(master, base)
        self.level = level
        self._value = None
        self._shape = None
        self.device2target = {}
        self.selection2targets = {}
        self.target2base = {}

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ChangeItem.collect_variables| of the base class |ChangeItem|
        and also prepare the dictionary |MathItem.target2base|, which maps each target
        variable object to its base variable object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import AddItem
        >>> item = AddItem(name="alpha", master="hland_v1", target="control.sfcf",
        ...                base="control.rfcf", level="global")
        >>> item.collect_variables(pub.selections)
        >>> land_dill = hp.elements.land_dill
        >>> control = land_dill.model.parameters.control
        >>> item.device2target[land_dill] is control.sfcf
        True
        >>> item.target2base[control.sfcf] is control.rfcf
        True
        >>> len(item.target2base)
        4
        """
        super().collect_variables(selections)
        basename = self.basespecs.variable
        basegroup = self.basespecs.subgroup
        assert basegroup is not None
        allowed_bases = (parametertools.Parameters, sequencetools.Sequences)
        for target in self.device2target.values():
            vars_ = target.subvars.vars
            assert isinstance(vars_, allowed_bases)
            self.target2base[target] = vars_[basegroup][basename]

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}("{self.name}", '
            f'"{self.targetspecs.master}", "{self.targetspecs.specstring}", '
            f'"{self.basespecs.specstring}", "{self.level}")'
        )


class AddItem(MathItem):
    """|MathItem| subclass performing additions.

    The following examples relate closely to the ones explained in the documentation on
    method |ChangeItem.update_variables| of class |ChangeItem|.  We similarly  repeat
    them all to show that our |AddItem| always uses the sum of its own value(s) and the
    value(s) of the related base variable to update the value(s) of the target variable.

    We prepare the `LahnH` example project and remove the "complete" selection from
    the |Selections| object available in module |pub|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> del pub.selections["complete"]

    We use the rainfall correction parameter (|hland_control.RFCF|) of application
    model |hland_v1| as the base variable.  To allow strict testing, we define a
    different correction factor for each of the 49 hydrological response units:

    >>> value = 0.8
    >>> for element in hp.elements.catchment:
    ...     rfcf = element.model.parameters.control.rfcf
    ...     for idx in range(len(rfcf)):
    ...         rfcf[idx] = value
    ...         value += 0.01
    ...     print(element, rfcf)    # doctest: +ELLIPSIS
    land_dill rfcf(0.8, ... 0.91)
    land_lahn_1 rfcf(0.92, ... 1.04)
    land_lahn_2 rfcf(1.05, ... 1.14)
    land_lahn_3 rfcf(1.15, ... 1.28)

    We choose the snowfall correction parameter (|hland_control.SFCF|) as the target
    variable.  The following test calculations show the expected results for all
    available aggregation levels:

    >>> from hydpy.core.itemtools import AddItem
    >>> item = AddItem(name="sfcf", master="hland_v1", target="control.sfcf",
    ...                base="control.rfcf", level="global")
    >>> item.collect_variables(pub.selections)
    >>> item.value = 0.1
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill sfcf(0.9, ... 1.01)
    land_lahn_1 sfcf(1.02, ... 1.14)
    land_lahn_2 sfcf(1.15, ... 1.24)
    land_lahn_3 sfcf(1.25, ... 1.38)

    >>> item.level = "selection"
    >>> item.collect_variables(pub.selections)
    >>> item.value = -0.1, 0.0
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill sfcf(0.7, ... 0.81)
    land_lahn_1 sfcf(0.82, ... 0.94)
    land_lahn_2 sfcf(1.05, ... 1.14)
    land_lahn_3 sfcf(1.15, ... 1.28)

    >>> item = AddItem(name="sfcf", master="hland_v1", target="control.sfcf",
    ...                base="control.rfcf", level="device")
    >>> item.collect_variables(pub.selections)
    >>> item.value = -0.1, 0.0, 0.1, 0.2
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill sfcf(0.7, ... 0.81)
    land_lahn_1 sfcf(0.92, ... 1.04)
    land_lahn_2 sfcf(1.15, ... 1.24)
    land_lahn_3 sfcf(1.35, ... 1.48)

    >>> item = AddItem(name="sfcf", master="hland_v1", target="control.sfcf",
    ...                base="control.rfcf", level="subunit")
    >>> item.collect_variables(pub.selections)
    >>> item.value = [idx/100 for idx in range(-20, 29)]
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:    # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill sfcf(0.6, ... 0.82)
    land_lahn_1 sfcf(0.84, ... 1.08)
    land_lahn_2 sfcf(1.1, ... 1.28)
    land_lahn_3 sfcf(1.3, ... 1.56)
    """

    def update_variable(
        self,
        variable: variabletools.Variable[Any, Any],
        value: numpy.ndarray,
    ) -> None:
        """Assign the sum of the given value(s) and the value(s) of the base variable
        to the given target variable.

        If the addition fails, |AddItem.update_variable| raises an error like the
        following:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import AddItem
        >>> item = AddItem(name="sfcf", master="hland_v1", target="control.sfcf",
        ...                base="control.rfcf", level="global")
        >>> item.collect_variables(pub.selections)
        >>> item._value = 0.1, 0.2
        >>> item.update_variables()    # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: When trying to add the value(s) `(0.1, 0.2)` of AddItem `sfcf` \
and the value(s) `[ 1.04283 ... 1.04283]` of variable `rfcf` of element `land_dill`, \
the following error occurred: operands could not be broadcast together with shapes \
(12,) (2,)...
        """
        base = self.target2base[variable]
        try:
            result = base.value + value
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to add the value(s) `{value}` of AddItem "
                f"`{self.name}` and the value(s) `{base.value}` of variable "
                f"{objecttools.devicephrase(base)}"
            )
        super().update_variable(variable, result)


class GetItem(ExchangeItem):
    """Base class for querying the values of multiple |Parameter| or |Sequence_|
    objects of a specific type."""

    _device2name: Dict[Union[devicetools.Node, devicetools.Element], Name]
    _ndim: Optional[int] = None

    def __init__(
        self,
        name: Name,
        master: str,
        target: str,
    ) -> None:
        self.name = name
        self.target = target.replace(".", "_")
        self.targetspecs = ExchangeSpecification(master, target)
        self.device2target = {}
        self.selection2targets = {}
        self._device2name = {}

    @property
    def ndim(self) -> int:
        """The number of dimensions of the handled value vector.

        Trying to access property |GetItem.ndim| before calling method
        |GetItem.collect_variables| results in the following error message:

        >>> from hydpy.core.itemtools import GetItem
        >>> GetItem("temp", "hland_v1", "states.lz").ndim
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `ndim` of GetItem \
`temp` is not ready.

        See the documentation on method |GetItem.collect_variables| for further
        information.
        """
        if self._ndim is None:
            raise exceptiontools.AttributeNotReady(
                f"Attribute `ndim` of {type(self).__name__} `{self.name}` is not ready."
            )
        return self._ndim

    def collect_variables(
        self,
        selections: selectiontools.Selections,
    ) -> None:
        """Apply method |ExchangeItem.collect_variables| of the base class
        |ExchangeItem| and determine the `ndim` attribute of the current |GetItem|
        object afterwards.

        The value of `ndim` depends on whether the target variable's values or time
        series are of interest:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import GetItem
        >>> for target in ("states.lz", "states.lz.series",
        ...                "states.sm", "states.sm.series"):
        ...     item = GetItem("temp", "hland_v1", target)
        ...     item.collect_variables(pub.selections)
        ...     print(item, item.ndim)
        GetItem("temp", "hland_v1", "states.lz") 0
        GetItem("temp", "hland_v1", "states.lz.series") 1
        GetItem("temp", "hland_v1", "states.sm") 1
        GetItem("temp", "hland_v1", "states.sm.series") 2
        """
        super().collect_variables(selections)
        for device in sorted(self.device2target.keys(), key=lambda x: x.name):
            self._device2name[device] = Name(f"{device.name}_{self.target}")
        for target in self.device2target.values():
            self._ndim = target.NDIM
            if self.targetspecs.series:
                self._ndim += 1
            break

    def yield_name2value(
        self,
        idx1: Optional[int] = None,
        idx2: Optional[int] = None,
    ) -> Iterator[Tuple[Name, str]]:
        """Sequentially return name-value-pairs describing the current state of the
        target variables.

        The names are automatically generated and contain both the name of the
        |Device| of the respective |Variable| object and the target description:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import SetItem
        >>> item = GetItem("lz", "hland_v1", "states.lz")
        >>> item.collect_variables(pub.selections)
        >>> hp.elements.land_dill.model.sequences.states.lz = 100.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)
        land_dill_states_lz 100.0
        land_lahn_1_states_lz 8.18711
        land_lahn_2_states_lz 10.14007
        land_lahn_3_states_lz 7.52648
        >>> item = GetItem("sm", "hland_v1", "states.sm")
        >>> item.collect_variables(pub.selections)
        >>> hp.elements.land_dill.model.sequences.states.sm = 2.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)    # doctest: +ELLIPSIS
        land_dill_states_sm [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, \
2.0, 2.0, 2.0, 2.0]
        land_lahn_1_states_sm [99.27505, ..., 142.84148]
        ...

        When querying time series, one can restrict the span of interest by passing
        index values:

        >>> item = GetItem("sim", "nodes", "sim.series")
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
            f'"{self.name}", '
            f'"{self.targetspecs.master}", '
            f'"{self.targetspecs.specstring}")'
        )
