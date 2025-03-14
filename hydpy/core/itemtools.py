"""This module implements so-called exchange items that simplify modifying the values
of |Parameter| and |Sequence_| objects."""

# import...
# ...from standard library
from __future__ import annotations
import itertools
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

Device2Target: TypeAlias = dict[
    devicetools.Node | devicetools.Element, variabletools.Variable
]
Selection2Targets: TypeAlias = dict[str, tuple[variabletools.Variable, ...]]
LevelType: TypeAlias = Literal["global", "selection", "device", "subunit"]


class ExchangeSpecification:
    """Specification of a concrete |Parameter| or |Sequence_| type.

    |ExchangeSpecification| is a helper class for |ExchangeItem| and its subclasses.
    Its constructor interprets two strings and one optional string (without any
    plausibility checks) and makes their information available as attributes.  The
    following tests list the expected cases:

    >>> from hydpy.core.itemtools import ExchangeSpecification
    >>> ExchangeSpecification(master="musk_classic", variable="control.nmbsequences",
    ...                       keyword="lag")
    ExchangeSpecification(master="musk_classic", variable="control.nmbsequences", \
keyword="lag")
    >>> ExchangeSpecification(master="hland_96", variable="fluxes.qt")
    ExchangeSpecification(master="hland_96", variable="fluxes.qt")
    >>> ExchangeSpecification(master="hland_96", variable="fluxes.qt.series")
    ExchangeSpecification(master="hland_96", variable="fluxes.qt.series")
    >>> ExchangeSpecification(master="node", variable="sim")
    ExchangeSpecification(master="node", variable="sim")
    >>> ExchangeSpecification(master="node", variable="sim.series")
    ExchangeSpecification(master="node", variable="sim.series")

    The following attributes are accessible:

    >>> spec = ExchangeSpecification(master="musk_classic",
    ...                              variable="control.nmbsequences", keyword="lag")
    >>> spec.master
    'musk_classic'
    >>> spec.subgroup
    'control'
    >>> spec.variable
    'nmbsequences'
    >>> spec.series
    False
    >>> spec.keyword
    'lag'
    """

    master: str
    """Either "node" or the name of the relevant base or application model (e. g. 
    "hland_96")."""
    variable: str
    """Name of the target or base variable."""
    keyword: str | None
    """(Optional) name of the target keyword argument of the target or base variable."""
    series: bool
    """Flag indicating whether to tackle the target variable's actual values (|False|)
    or complete time series (|True|)."""
    subgroup: str | None
    """For model variables, the name of the parameter or sequence subgroup of the
    target or base variable; for node sequences, |None|."""

    def __init__(
        self, *, master: str, variable: str, keyword: str | None = None
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
        self.keyword = keyword

    @property
    def specstring(self) -> str:
        """The string corresponding to the current values of `subgroup`, `state`, and
        `variable`.

        >>> from hydpy.core.itemtools import ExchangeSpecification
        >>> spec = ExchangeSpecification(master="hland_96", variable="fluxes.qt")
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
        keyword = "" if self.keyword is None else f', keyword="{self.keyword}"'
        return (
            f'ExchangeSpecification(master="{self.master}", '
            f'variable="{self.specstring}"{keyword})'
        )


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

        Property |ExchangeItem.ndim| needs to be overwritten by the concrete
        subclasses:

        >>> from hydpy.core.itemtools import ExchangeItem
        >>> ExchangeItem().ndim
        Traceback (most recent call last):
        ...
        NotImplementedError
        """
        raise NotImplementedError()

    def _iter_relevantelements(
        self, selection: selectiontools.Selection
    ) -> Iterator[devicetools.Element]:
        for element in selection.elements:
            for model in element.model.find_submodels(include_mainmodel=True).values():
                name1 = model.name
                name2 = name1.rpartition("_")[0]
                if self.targetspecs.master in (name1, name2):
                    yield element
                    break

    @staticmethod
    def _query_elementvariable(
        element: devicetools.Element, properties: ExchangeSpecification
    ) -> variabletools.Variable:
        # ToDo: Return more then one variable (possible for similar submodels).
        p = properties
        for model in element.model.find_submodels(include_mainmodel=True).values():
            for group in (model.parameters, model.sequences):
                if (
                    ((subgroupname := p.subgroup) is not None)
                    and ((subgroup := getattr(group, subgroupname, None)) is not None)
                    and ((variable := getattr(subgroup, p.variable, None)) is not None)
                ):
                    assert isinstance(variable, variabletools.Variable)
                    return variable
        raise RuntimeError(
            f"No model of element `{element.name}` handles a parameter or sequence "
            f"named `{p.variable}` in subgroup `{p.subgroup}`."
        )

    @staticmethod
    def _query_nodevariable(
        node: devicetools.Node, properties: ExchangeSpecification
    ) -> sequencetools.NodeSequence:
        sequence = getattr(node.sequences, properties.variable)
        assert isinstance(sequence, sequencetools.NodeSequence)
        return sequence

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        """Collect the relevant target variables handled by the devices of the given
        |Selections| object.

        We prepare the `HydPy-H-Lahn` example project to be able to use its
        |Selections| object:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        We change the type of a specific application model to the type of its base
        model for reasons explained later:

        >>> from hydpy.models.hland import Model
        >>> hp.elements.land_lahn_kalk.model.__class__ = Model

        We prepare an |ExchangeItem| as an example, handling all |hland_states.Ic|
        sequences corresponding to any application models derived from |hland|:

        >>> from hydpy.core.itemtools import ExchangeItem, ExchangeSpecification
        >>> item = ExchangeItem()

        |ExchangeItem| is only a base class.  Hence we need to prepare some missing
        attributes manually:

        >>> item.targetspecs = ExchangeSpecification(master="hland",
        ...                                          variable="states.ic")
        >>> item.level = "global"
        >>> item.device2target = {}
        >>> item.selection2targets = {}

        Applying method |ExchangeItem.collect_variables| connects the |ExchangeItem|
        object with all four relevant |hland_states.Ic| objects:

        >>> item.collect_variables(pub.selections)
        >>> land_dill_assl = hp.elements.land_dill_assl
        >>> for element in sorted(item.device2target, key=lambda x: x.name):
        ...     print(element)
        land_dill_assl
        land_lahn_kalk
        land_lahn_leun
        land_lahn_marb
        >>> ic_states = land_dill_assl.model.sequences.states.ic
        >>> item.device2target[land_dill_assl] is ic_states
        True

        Asking for |hland_states.Ic| objects corresponding to application model
        |hland_96| only results in skipping the |Element| `land_lahn_kalk` (handling
        the |hland| base model due to the hack above):

        >>> item.targetspecs.master = "hland_96"
        >>> item.device2target.clear()
        >>> item.collect_variables(pub.selections)
        >>> for element in sorted(item.device2target, key=lambda x: x.name):
        ...     print(element)
        land_dill_assl
        land_lahn_leun
        land_lahn_marb
        >>> ic_states = land_dill_assl.model.sequences.states.ic
        >>> item.device2target[land_dill_assl] is ic_states
        True

        The value of sub-attribute |ExchangeSpecification.series| of attribute
        |ExchangeItem.targetspecs| does not affect the results obtained with method
        |ExchangeItem.collect_variables|:

        >>> item.targetspecs.series = True
        >>> item.collect_variables(pub.selections)
        >>> ic_states = land_dill_assl.model.sequences.states.ic
        >>> item.device2target[land_dill_assl] is ic_states
        True

        An ill-defined subgroup name results in the following error:

        >>> item.targetspecs.subgroup = "wrong_group"
        >>> item.collect_variables(pub.selections)
        Traceback (most recent call last):
        ...
        RuntimeError: No model of element `land_dill_assl` handles a parameter or \
sequence named `ic` in subgroup `wrong_group`.

        Collecting the |Sim| or |Obs| sequences of |Node| objects works similarly:

        >>> item.targetspecs.master = "node"
        >>> item.targetspecs.variable = "sim"
        >>> item.targetspecs.subgroup = None
        >>> item.targetspecs.series = False
        >>> item.device2target.clear()
        >>> item.collect_variables(pub.selections)
        >>> dill_assl = hp.nodes.dill_assl
        >>> for node in sorted(item.device2target, key=lambda x: x.name):
        ...  print(node)
        dill_assl
        lahn_kalk
        lahn_leun
        lahn_marb
        >>> item.device2target[dill_assl] is dill_assl.sequences.sim
        True
        """
        variable: variabletools.Variable
        variables: list[variabletools.Variable]
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


def _make_subunit_name(
    device: devicetools.Device, target: variabletools.Variable
) -> Mayberable1[str]:
    """
    >>> from hydpy.core.itemtools import _make_subunit_name as make
    >>> device = type("D", (), {"name": "dev"})()
    >>> make(device, type("V", (), {"NDIM": 0, "shape": 0})())
    'dev'
    >>> print(*make(device, type("V", (), {"NDIM": 1, "shape": (2,)})()))
    dev_0 dev_1
    >>> print(*make(device, type("V", (), {"NDIM": 3, "shape": (1, 2, 3)})()))
    dev_0_0_0 dev_0_0_1 dev_0_0_2 dev_0_1_0 dev_0_1_1 dev_0_1_2
    """
    name = device.name
    if target.NDIM == 0:
        return name
    ranges = (range(length) for length in target.shape)
    return (
        f"{name}_{'_'.join(str(idx) for idx in idxs)}"
        for idxs in itertools.product(*ranges)
    )


class ChangeItem(ExchangeItem):
    """Base class for changing the values of multiple |Parameter| or |Sequence_|
    objects of a specific type."""

    level: LevelType
    """The level at which the values of the change item are valid."""
    _shape: tuple[()] | tuple[int] | None
    _value: NDArrayFloat | None

    @property
    def ndim(self) -> int:
        """The number of dimensions of the handled value vector."""
        return (self.level != "global") + self.targetspecs.series

    @property
    def shape(self) -> tuple[()] | tuple[int]:
        """The shape of the target variables.

        Trying to access property |ChangeItem.shape| before calling method
        |ChangeItem.collect_variables| results in the following error:

        >>> from hydpy import SetItem
        >>> SetItem(name="name", master="master", target="target", level="global").shape
        Traceback (most recent call last):
        ...
        RuntimeError: The shape of SetItem `name` has not been determined so far.

        See method |ChangeItem.collect_variables| for further information.
        """
        if self._shape is not None:
            return self._shape
        raise RuntimeError(
            f"The shape of {type(self).__name__} `{self.name}` has not been "
            f"determined so far."
        )

    @property
    def seriesshape(self) -> tuple[int] | tuple[int, int]:
        """The shape of the target variables' whole time series.

        |ChangeItem.seriesshape| extends the |ChangeItem.shape| tuple by the length of
        the current simulation period:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import SetItem
        >>> for level in ("global", "selection", "device",  "subunit"):
        ...     item = SetItem(name="t", master="hland", target="inputs.t.series",
        ...                    level=level)
        ...     item.collect_variables(pub.selections)
        ...     print(level, item.shape, item.seriesshape)
        global () (4,)
        selection (2,) (2, 4)
        device (4,) (4, 4)
        subunit (4,) (4, 4)
        """
        if self.shape:
            return self.shape[0], len(hydpy.pub.timegrids.sim)
        return (len(hydpy.pub.timegrids.sim),)

    @property
    def subnames(self) -> tuple[()] | tuple[str, ...] | None:
        """Artificial subnames of all values of all target variables.

        Property |ChangeItem.subnames| offers a way to identify specific entries of the
        vector returned by property |ChangeItem.value|.  See method
        |ChangeItem.collect_variables| for further information.
        """
        if self.level == "global":
            return None
        if self.level == "selection":
            return tuple(self.selection2targets)
        if self.level == "device":
            return tuple(device.name for device in self.device2target)
        if self.level == "subunit":
            subnames: list[str] = []
            for device, target in self.device2target.items():
                subsubnames = _make_subunit_name(device, target)
                if isinstance(subsubnames, str):
                    subnames.append(subsubnames)
                else:
                    subnames.extend(subsubnames)
            return tuple(subnames)
        assert_never(self.level)

    @property
    def value(self) -> NDArrayFloat:
        """The item value(s) changing the values of target variables through applying
        method |ChangeItem.update_variables| of class |ChangeItem|.

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        The first example deals with "global" state values:

        >>> from hydpy import print_matrix, round_, SetItem
        >>> item = SetItem(name="ic", master="hland", target="states.ic",
        ...                level="global")
        >>> item.collect_variables(pub.selections)
        >>> item.value
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem \
`ic` has/have not been prepared so far.

        >>> item.value = 1.0
        >>> round_(item.value)
        1.0

        >>> item.value = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: When trying to convert the value(s) `(1.0, 2.0)` assigned to \
SetItem `ic` to a numpy array of shape `()` and type `float`, the following error \
occurred: could not broadcast input array from shape (2,) into shape ()

        The second example deals with "selection-wide" input time series values:

        >>> item = SetItem(name="t", master="hland", target="inputs.t.series",
        ...                level="selection")
        >>> item.collect_variables(pub.selections)

        >>> item.value = [1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]
        >>> print_matrix(item.value)
        | 1.0, 2.0, 3.0, 4.0 |
        | 5.0, 6.0, 7.0, 8.0 |

        >>> item.value = 1.0, 2.0
        Traceback (most recent call last):
        ...
        ValueError: When trying to convert the value(s) `(1.0, 2.0)` assigned to \
SetItem `t` to a numpy array of shape `(2, 4)` and type `float`, the following error \
occurred: could not broadcast input array from shape (2,) into shape (2,4)
        """
        if self._value is None:
            raise exceptiontools.AttributeNotReady(
                f"The value(s) of the {type(self).__name__} `{self.name}` has/have "
                f"not been prepared so far."
            )
        return self._value

    @value.setter
    def value(self, value: NDArrayFloat) -> None:
        try:
            shape = self.seriesshape if self.targetspecs.series else self.shape
            self._value = numpy.full(shape, value, dtype=config.NP_FLOAT)
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to convert the value(s) `{value}` assigned to "
                f"{type(self).__name__} `{self.name}` to a numpy array of shape "
                f"`{shape}` and type `float`"
            )

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        """Apply method |ExchangeItem.collect_variables| of the base class
        |ExchangeItem| and determine the |ChangeItem.shape| of the current |ChangeItem|
        object afterwards.

        For the following examples, we prepare the `HydPy-H-Lahn` example project:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        After calling method |ChangeItem.collect_variables|, attribute
        |ExchangeItem.device2target| assigns all relevant devices to the chosen target
        variables:

        >>> from hydpy import SetItem
        >>> item = SetItem(name="ic", master="hland", target="states.ic",
        ...                level="global")
        >>> item.collect_variables(pub.selections)
        >>> for device, target in item.device2target.items():
        ...     print(device, target)  # doctest: +ELLIPSIS
        land_dill_assl ic(0.9694, ..., 1.47487)
        land_lahn_marb ic(0.96404, ..., 1.46719)
        land_lahn_kalk ic(0.96064, ..., 1.46444)
        land_lahn_leun ic(0.96159, ..., 1.46393)

        Similarly, attribute |ExchangeItem.selection2targets| maps all relevant
        selections to the chosen target variables:

        >>> for selection, targets in item.selection2targets.items():
        ...     print(selection, targets)  # doctest: +ELLIPSIS
        headwaters (ic(0.9694, ..., 1.47487), ic(0.96404, ..., 1.46719))
        nonheadwaters (ic(0.96064, ..., 1.46444), ic(0.96159, ..., 1.46393))

        The properties |ChangeItem.shape| and |ChangeItem.subnames| of a |ChangeItem|
        object depend on the intended aggregation |ChangeItem.level|.  For the "global"
        level, we need only one scalar value for all target variables.  Property
        |ChangeItem.shape| indicates this by returning an empty tuple and property
        |ChangeItem.subnames| by returning |None|:

        >>> item.shape
        ()
        >>> item.subnames

        For the "selection" level, we need one value for each relevant selection.
        Therefore, we use the plain selection names as sub-names:

        >>> item = SetItem(name="ic", master="hland", target="states.ic",
        ...                level="selection")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (2,)
        >>> item.subnames
        ('headwaters', 'nonheadwaters')

        For the "device" level, we need one value for each relevant device.  Therefore,
        we use the plain device names as sub-names:

        >>> item = SetItem(name="ic", master="hland", target="states.ic",
        ...                level="device")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (4,)
        >>> item.subnames
        ('land_dill_assl', 'land_lahn_marb', 'land_lahn_kalk', 'land_lahn_leun')

        For the "subunit" level, we need one value for each vector entry of all target
        variables. When using the 1-dimensional parameter |hland_states.IC| of the base
        model |hland| as an example, property |ChangeItem.shape| agrees with the total
        number of hydrological response units.  Property |ChangeItem.subnames| combines
        the device names with the zero-based index numbers of the vector entries of the
        respective target variables:

        >>> item = SetItem(name="ic", master="hland", target="states.ic",
        ...                level="subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (49,)
        >>> item.subnames  # doctest: +ELLIPSIS
        ('land_dill_assl_0', 'land_dill_assl_1', ..., 'land_lahn_leun_9')

        For 2-dimensional sequences, |ChangeItem.shape| returns the total number of
        matrix entries, and each sub-name indicates the row and the column of a specific
        matrix entry:

        >>> dill_assl = hp.elements.land_dill_assl.model
        >>> dill_assl.parameters.control.sclass(2)
        >>> item = SetItem(name="sp", master="hland", target="states.sp",
        ...                level="subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (61,)
        >>> item.subnames  # doctest: +ELLIPSIS
        ('land_dill_assl_0_0', 'land_dill_assl_0_1', ..., \
'land_dill_assl_1_10', 'land_dill_assl_1_11', ..., 'land_lahn_leun_0_9')

        For 0-dimensional sequences, |ChangeItem.shape| equals their number, and all
        sub-names are identical to the corresponding device names:

        >>> item = SetItem(name="lz", master="hland", target="states.lz",
        ...                level="subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (4,)
        >>> item.subnames  # doctest: +ELLIPSIS
        ('land_dill_assl', 'land_lahn_marb', 'land_lahn_kalk', 'land_lahn_leun')

        Everything works as explained above when specifying a keyword argument for
        defining values, except there is no support for the `subunit` level.  We show
        this for the parameter |musk_control.NmbSegments| of base model |musk|, which
        accepts a custom keyword argument named `lag`:

        >>> item = SetItem(name="lag", master="musk", target="control.nmbsegments",
        ...                keyword="lag", level="global")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        ()
        >>> item.subnames

        >>> item = SetItem(name="lag", master="musk", target="control.nmbsegments",
        ...                keyword="lag", level="selection")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (1,)
        >>> item.subnames
        ('streams',)

        >>> item = SetItem(name="lag", master="musk", target="control.nmbsegments",
        ...                keyword="lag", level="device")
        >>> item.collect_variables(pub.selections)
        >>> item.shape
        (3,)
        >>> item.subnames
        ('stream_dill_assl_lahn_leun', 'stream_lahn_leun_lahn_kalk', \
'stream_lahn_marb_lahn_leun')

        >>> item = SetItem(name="lag", master="musk", target="control.nmbsegments",
        ...                keyword="lag", level="subunit")
        >>> item.collect_variables(pub.selections)
        Traceback (most recent call last):
        ...
        ValueError: Incorrect configuration for exchange item `lag`: When defining a \
keyword for an exchange item, its aggregation level cannot be `subunit`.
        """
        super().collect_variables(selections)
        if self.level == "global":
            self._shape = ()
        elif self.level == "selection":
            self._shape = (len(self.selection2targets),)
        elif self.level == "device":
            self._shape = (len(self.device2target),)
        elif self.level == "subunit":
            if self.targetspecs.keyword is not None:
                raise ValueError(
                    f"Incorrect configuration for exchange item `{self.name}`: When "
                    f"defining a keyword for an exchange item, its aggregation level "
                    f"cannot be `subunit`."
                )
            self._shape = (
                sum(target.numberofvalues for target in self.device2target.values()),
            )
        else:
            assert_never(self.level)

    def update_variable(
        self, variable: variabletools.Variable, value: NDArrayFloat
    ) -> None:
        """Assign the given value(s) to the given target or base variable.

        If the assignment fails, |ChangeItem.update_variable| raises an error like the
        following:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import ChangeItem, ExchangeSpecification
        >>> item = ChangeItem()
        >>> item.name = "alpha"
        >>> item.targetspecs = ExchangeSpecification(master="hland_96",
        ...                                          variable="control.alpha")
        >>> item.level = "global"
        >>> item.device2target = {}
        >>> item.selection2targets = {}
        >>> item._value = "wrong"
        >>> item.collect_variables(pub.selections)
        >>> item.update_variables()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: When trying to update a target variable of ChangeItem `alpha` with \
the value(s) `wrong`, the following error occurred: While trying to set the value(s) \
of variable `alpha` of element `land_dill_assl`, the following error occurred: The \
given value `wrong` cannot be converted to type `float`.
        """
        try:
            if self.targetspecs.series:
                assert isinstance(variable, sequencetools.IOSequence)
                variable.simseries = value
            elif self.targetspecs.keyword is None:
                variable(value)
            else:
                assert isinstance(variable, parametertools.Parameter)
                keywordarguments = variable.keywordarguments
                keywordarguments.valid = True
                keywordarguments[self.targetspecs.keyword] = value.item()
                variable(**dict(keywordarguments))
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to update a target variable of {type(self).__name__} "
                f"`{self.name}` with the value(s) `{value}`"
            )

    def update_variables(self) -> None:
        """Assign the current |ChangeItem.value| to the values or time series of the
        target variables.

        For the following examples, we prepare the `HydPy-H-Lahn` example project:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        "Global" |SetItem| objects assign the same value to all chosen 0-dimensional
        target variables (we use parameter |hland_control.Alpha| as an example):

        >>> from hydpy import print_vector, round_, SetItem
        >>> item = SetItem(name="alpha", master="hland_96", target="control.alpha",
        ...                level="global")
        >>> item
        SetItem(name="alpha", master="hland_96", target="control.alpha", level="global")
        >>> item.collect_variables(pub.selections)
        >>> land_dill_assl = hp.elements.land_dill_assl
        >>> land_dill_assl.model.parameters.control.alpha
        alpha(1.0)
        >>> item.value = 2.0
        >>> round_(item.value)
        2.0
        >>> land_dill_assl.model.parameters.control.alpha
        alpha(1.0)
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, element.model.parameters.control.alpha)
        land_dill_assl alpha(2.0)
        land_lahn_kalk alpha(2.0)
        land_lahn_leun alpha(2.0)
        land_lahn_marb alpha(2.0)

        Similar holds for "Global" |SetItem| objects that modify the time series of
        their target variables, which we demonstrate for the input time series
        |hland_inputs.T|:

        >>> item = SetItem(name="t", master="hland_96", target="inputs.t.series",
        ...                level="global")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 0.5, 1.0, 1.5, 2.0
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, end=": ")
        ...     print_vector(element.model.sequences.inputs.t.series)
        land_dill_assl: 0.5, 1.0, 1.5, 2.0
        land_lahn_kalk: 0.5, 1.0, 1.5, 2.0
        land_lahn_leun: 0.5, 1.0, 1.5, 2.0
        land_lahn_marb: 0.5, 1.0, 1.5, 2.0

        Some |Parameter| subclasses support setting their values via custom keyword
        arguments.  "Global" |SetItem| objects can use such keyword arguments.  We show
        this for the parameter |musk_control.NmbSegments| of base model |musk|, which
        accepts a custom keyword argument named `lag`:

        >>> item = SetItem(name="lag", master="musk", target="control.nmbsegments",
        ...                keyword="lag", level="global")
        >>> item
        SetItem(name="lag", master="musk", target="control.nmbsegments", \
keyword="lag", level="global")
        >>> item.collect_variables(pub.selections)
        >>> stream_lahn_marb_lahn_leun = hp.elements.stream_lahn_marb_lahn_leun
        >>> stream_lahn_marb_lahn_leun.model.parameters.control.nmbsegments
        nmbsegments(lag=0.583)
        >>> item.value = 2.0
        >>> round_(item.value)
        2.0
        >>> stream_lahn_marb_lahn_leun.model.parameters.control.nmbsegments
        nmbsegments(lag=0.583)
        >>> item.update_variables()
        >>> for element in hp.elements.river:
        ...     print(element, element.model.parameters.control.nmbsegments)
        stream_dill_assl_lahn_leun nmbsegments(lag=2.0)
        stream_lahn_leun_lahn_kalk nmbsegments(lag=2.0)
        stream_lahn_marb_lahn_leun nmbsegments(lag=2.0)

        For 1-dimensional target variables like the parameter |hland_control.FC|, a
        "global" |SetItem| assigns the same value to each vector entry or the selected
        keyword argument:

        >>> item = SetItem(name="fc", master="hland_96", target="control.fc",
        ...                level="global")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 200.0
        >>> land_dill_assl.model.parameters.control.fc
        fc(278.0)
        >>> item.update_variables()
        >>> land_dill_assl.model.parameters.control.fc
        fc(200.0)

        >>> item = SetItem(name="fc", master="hland_96", target="control.fc",
        ...                keyword="forest", level="global")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 300.0
        >>> land_dill_assl.model.parameters.control.fc
        fc(200.0)
        >>> item.update_variables()
        >>> land_dill_assl.model.parameters.control.fc
        fc(field=200.0, forest=300.0)

        The same holds for 2-dimensional target variables like the sequence
        |hland_states.SP| (we increase the number of snow classes and thus the length
        of the first axis for demonstration purposes):

        >>> land_dill_assl.model.parameters.control.sclass(2)
        >>> item = SetItem(name="sp", master="hland_96", target="states.sp",
        ...                level="global")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 5.0
        >>> land_dill_assl.model.sequences.states.sp
        sp([[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan],
            [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]])
        >>> item.update_variables()
        >>> land_dill_assl.model.sequences.states.sp
        sp([[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]])

        When working on the "selection" level, a |SetItem| object assigns one specific
        value to the target variables of each relevant selection, regardless of target
        variable's dimensionality:

        >>> item = SetItem(name="ic", master="hland_96", target="states.ic",
        ...                level="selection")
        >>> item.collect_variables(pub.selections)
        >>> land_dill_assl.model.sequences.states.ic  # doctest: +ELLIPSIS
        ic(0.9694, ..., 1.47487)
        >>> item.value = 0.5, 1.0
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.ic)
        land_dill_assl ic(0.5, 0.5, ..., 0.5, 0.5)
        land_lahn_kalk ic(1.0, 1.0, ..., 1.0, 1.0)
        land_lahn_leun ic(1.0, 1.0, ..., 1.0, 1.0)
        land_lahn_marb ic(0.5, 0.5, ..., 0.5, 0.5)

        >>> item = SetItem(name="t", master="hland_96", target="inputs.t.series",
        ...                level="selection")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [0.5, 1.0, 1.5, 2.0], [2.5, 3.0, 3.5, 4.0]
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, end=": ")
        ...     print_vector(element.model.sequences.inputs.t.series)
        land_dill_assl: 0.5, 1.0, 1.5, 2.0
        land_lahn_kalk: 2.5, 3.0, 3.5, 4.0
        land_lahn_leun: 2.5, 3.0, 3.5, 4.0
        land_lahn_marb: 0.5, 1.0, 1.5, 2.0

        >>> item = SetItem(name="tt", master="hland_96", target="control.tt",
        ...                keyword="field", level="selection")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [0.0, 1.0]
        >>> land_dill_assl.model.parameters.control.tt
        tt(0.55824)
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
        ...     print(element, element.model.parameters.control.tt)
        land_dill_assl tt(field=0.0, forest=0.55824)
        land_lahn_kalk tt(field=1.0, forest=0.0)
        land_lahn_leun tt(field=1.0, forest=0.0)
        land_lahn_marb tt(field=0.0, forest=0.59365)

        In contrast, each device receives one specific value when working on the
        "device" level:

        >>> item = SetItem(name="ic", master="hland_96", target="states.ic",
        ...                level="device")
        >>> item.collect_variables(pub.selections)
        >>> item.value = 0.5, 1.0, 1.5, 2.0
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.ic)
        land_dill_assl ic(0.5, 0.5, ..., 0.5, 0.5)
        land_lahn_kalk ic(1.5, 1.5, ..., 1.5, 1.5)
        land_lahn_leun ic(2.0, 2.0, ..., 2.0, 2.0)
        land_lahn_marb ic(1.0, 1.0, ... 1.0, 1.0)

        >>> item = SetItem(name="t", master="hland_96", target="inputs.t.series",
        ...                level="device")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [[0.5, 1.0, 1.5, 2.0], [2.5, 3.0, 3.5, 4.0],
        ...               [4.5, 5.0, 5.5, 6.0], [6.5, 7.0, 7.5, 8.0]]
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:
        ...     print(element, end=": ")
        ...     print_vector(element.model.sequences.inputs.t.series)
        land_dill_assl: 0.5, 1.0, 1.5, 2.0
        land_lahn_kalk: 4.5, 5.0, 5.5, 6.0
        land_lahn_leun: 6.5, 7.0, 7.5, 8.0
        land_lahn_marb: 2.5, 3.0, 3.5, 4.0

        >>> item = SetItem(name="beta", master="hland_96", target="control.beta",
        ...                keyword="forest", level="device")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [1.0, 2.0, 3.0, 4.0]
        >>> land_dill_assl.model.parameters.control.beta
        beta(2.54011)
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
        ...     print(element, element.model.parameters.control.beta)
        land_dill_assl beta(field=2.54011, forest=1.0)
        land_lahn_kalk beta(field=1.51551, forest=3.0)
        land_lahn_leun beta(field=2.5118, forest=4.0)
        land_lahn_marb beta(field=1.45001, forest=2.0)

        For the most detailed "subunit" level and 1-dimensional variables as
        |hland_states.IC|, the |SetItem| object handles one value for each of the 49
        hydrological response units of the complete `Lahn` river basin:

        >>> item = SetItem(name="ic", master="hland_96", target="states.ic",
        ...                level="subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [value/100 for value in range(49)]
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.ic)
        land_dill_assl ic(0.0, 0.01, ..., 0.1, 0.11)
        land_lahn_kalk ic(0.25, 0.26, ..., 0.37, 0.38)
        land_lahn_leun ic(0.39, 0.4, ..., 0.47, 0.48)
        land_lahn_marb ic(0.12, 0.13, ... 0.23, 0.24)

        We increased the number of snow classes per zone to two for element
        `land_dill_assl`.  Hence, its snow-related |hland_states.SP| object handles 22
        instead of 11 values, and we need to assign 61 instead of 49 values to the
        |SetItem| object.  Each item value relates to a specific matrix entry of a
        specific target variable:

        >>> item = SetItem(name="sp", master="hland_96", target="states.sp",
        ...                level="subunit")
        >>> item.collect_variables(pub.selections)
        >>> item.value = [value/100 for value in range(61)]
        >>> item.update_variables()
        >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
        ...     print(element, element.model.sequences.states.sp)
        land_dill_assl sp([[0.0, ...0.11],
            [0.12, ...0.23]])
        land_lahn_kalk sp(0.37, ...0.5)
        land_lahn_leun sp(0.51, ...0.6)
        land_lahn_marb sp(0.24, ...0.36)
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
                idx1 = idx0 + variable.numberofvalues
                subvalues = values[idx0:idx1]
                if variable.NDIM > 1:
                    subvalues = subvalues.reshape(variable.shape)
                self.update_variable(variable, subvalues)
                idx0 = idx1
        else:
            assert_never(self.level)


class SetItem(ChangeItem):
    """Exchange item for assigning |ChangeItem.value| to multiple |Parameter| or
    |Sequence_| objects of a specific type."""

    def __init__(
        self,
        *,
        name: str,
        master: str,
        target: str,
        level: LevelType,
        keyword: str | None = None,
    ) -> None:
        self.name = Name(name)
        self.targetspecs = ExchangeSpecification(
            master=master, variable=target, keyword=keyword
        )
        self.level = level
        self._value = None
        self._shape = None
        self.device2target = {}
        self.selection2targets = {}

    def extract_values(self) -> None:
        """Extract the target variables' values.

        Method |SetItem.extract_values| implements the inverse functionality of method
        |ChangeItem.update_variables|.  It queries the values of the target variables,
        aggregates them when necessary, and assigns them to the current |SetItem|
        object.  Please read the documentation on method |ChangeItem.update_variables|
        first, explaining the "aggregation level" concept.

        For the following examples, we prepare the `HydPy-H-Lahn` example project:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, _ = prepare_full_example_2()

        We define three |SetItem| objects, which handle states of different
        dimensionality.  `lz` addresses the 0-dimensional sequence |hland_states.LZ|,
        `sm` the 1-dimensional sequence |hland_states.SM|, and `sp` the 2-dimensional
        sequence |hland_states.SP|:

        >>> from hydpy import print_vector, round_, SetItem
        >>> lz = SetItem(name="lz", master="hland_96", target="states.lz",
        ...              level="to be defined")
        >>> sm = SetItem(name="sm", master="hland_96", target="states.sm",
        ...              level="to be defined")
        >>> sp = SetItem(name="sp", master="hland_96", target="states.sp",
        ...              level="to be defined")

        The additional |SetItem| objects `uz`, `ic`, and `wc` address the time series
        of the 0-dimensional sequence |hland_states.UZ|, the 1-dimensional sequence
        |hland_states.Ic|, and the 2-dimensional sequence |hland_states.WC|:

        >>> uz = SetItem(name="uz", master="hland_96", target="states.uz.series",
        ...              level="to be defined")
        >>> ic = SetItem(name="ic", master="hland_96", target="states.ic.series",
        ...              level="to be defined")
        >>> wc = SetItem(name="wc", master="hland_96", target="states.wc.series",
        ...              level="to be defined")

        The following test function updates the aggregation level and calls
        |SetItem.extract_values| for all six items:

        >>> def test(level):
        ...     for item in (lz, sm, sp, uz, ic, wc):
        ...         item.level = level
        ...         item.collect_variables(pub.selections)
        ...         item.extract_values()

        We mainly focus on the sequences of the application model of element
        `land_dill_assl` when comparing results:

        >>> dill_assl = hp.elements.land_dill_assl.model

        For rigorous testing, we increase the number of snow classes of this model
        instance and, thus, the length of the first axis of its |hland_states.SP| and
        its |hland_states.WC| object:

        >>> import numpy
        >>> dill_assl.parameters.control.sclass(2)

        After this change, we must define new test data for the current state of the
        |hland_states.SP| object of element `land_dill_assl`:

        >>> dill_assl.sequences.states.sp = numpy.arange(2*12).reshape(2, 12)

        Also, we must prepare test data for all considered time series:

        >>> dill_assl.sequences.states.uz.series = numpy.arange(4).reshape(4)
        >>> dill_assl.sequences.states.ic.series = numpy.arange(4*12).reshape(4, 12)
        >>> dill_assl.sequences.states.wc.series = numpy.arange(4*2*12).reshape(4,
        ...                                                                     2, 12)

        For all aggregation levels except `subunit`, |SetItem.extract_values| relies on
        the (spatial) aggregation of data, which is not possible beyond the `device`
        level.  Therefore, until the implementation of a more general spatial data
        concept into *HydPy*, |SetItem.extract_values| raises the following error when
        being applied to items working on the `global` or `selection` level:

        >>> test("global")
        Traceback (most recent call last):
        ...
        NotImplementedError: HydPy does not support averaging values across different \
elements so far.  So, it is not possible to aggregate to the global level.

        >>> test("selection")
        Traceback (most recent call last):
        ...
        NotImplementedError: HydPy does not support averaging values across different \
elements so far.  So, it is not possible to aggregate to the selection level.

        For the `device` level and non-scalar variables, |SetItem.extract_values| uses
        the |Variable.average_values| method of class |Variable| or the
        |IOSequence.average_series| method of class |IOSequence| for calculating the
        individual exchange item values:

        >>> test("device")
        >>> print_vector(lz.value)
        8.70695, 8.18711, 7.52648, 10.14007
        >>> dill_assl.sequences.states.lz
        lz(8.70695)
        >>> print_vector(sm.value)
        211.47288, 115.77717, 114.733823, 147.057048
        >>> round_(dill_assl.sequences.states.sm.average_values())
        211.47288
        >>> print_vector(sp.value)
        11.103987, 0.0, 0.0, 0.0
        >>> round_(dill_assl.sequences.states.sp.average_values())
        11.103987
        >>> for series in uz.value:
        ...     print_vector(series)
        0.0, 1.0, 2.0, 3.0
        nan, nan, nan, nan
        nan, nan, nan, nan
        nan, nan, nan, nan
        >>> print_vector(dill_assl.sequences.states.uz.series)
        0.0, 1.0, 2.0, 3.0
        >>> for series in ic.value:
        ...     print_vector(series)
        5.103987, 17.103987, 29.103987, 41.103987
        nan, nan, nan, nan
        nan, nan, nan, nan
        nan, nan, nan, nan
        >>> print_vector(dill_assl.sequences.states.ic.average_series())
        5.103987, 17.103987, 29.103987, 41.103987
        >>> for series in wc.value:
        ...     print_vector(series)
        11.103987, 35.103987, 59.103987, 83.103987
        nan, nan, nan, nan
        nan, nan, nan, nan
        nan, nan, nan, nan
        >>> print_vector(dill_assl.sequences.states.wc.average_series())
        11.103987, 35.103987, 59.103987, 83.103987

        For the `subunit` level, no aggregation is necessary:

        >>> test("subunit")
        >>> print_vector(lz.value)
        8.70695, 8.18711, 7.52648, 10.14007
        >>> dill_assl.sequences.states.lz
        lz(8.70695)
        >>> print_vector(sm.value)  # doctest: +ELLIPSIS
        185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
        222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427,
        99.27505, 96.17726, 109.16576, 106.39745, 117.97304, 115.56252,
        125.81523, 123.73198, 132.80035, 130.91684, 138.95523, 137.25983,
        142.84148, 101.31248, 97.225, 111.3861, 107.64977, 120.59559,
        117.26499, 129.01711, 126.0465, 136.66663, 134.01408, 143.59799,
        141.24428, 147.75786, 153.54053, 138.31396, 135.71124, 147.54968,
        145.47142, 154.96405, 153.32805, 160.91917, 159.62434, 165.65575,
        164.63255
        >>> dill_assl.sequences.states.sm
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)
        >>> hp.elements.land_lahn_kalk.model.sequences.states.sm
        sm(101.31248, 97.225, 111.3861, 107.64977, 120.59559, 117.26499,
           129.01711, 126.0465, 136.66663, 134.01408, 143.59799, 141.24428,
           147.75786, 153.54053)
        >>> print_vector(sp.value)
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,
        13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> for series in uz.value:
        ...     print_vector(series)
        0.0, 1.0, 2.0, 3.0
        nan, nan, nan, nan
        nan, nan, nan, nan
        nan, nan, nan, nan
        >>> print_vector(dill_assl.sequences.states.uz.series)
        0.0, 1.0, 2.0, 3.0
        >>> for series in ic.value:  # doctest: +ELLIPSIS
        ...     print_vector(series)
        0.0, 12.0, 24.0, 36.0
        1.0, 13.0, 25.0, 37.0
        ...
        10.0, 22.0, 34.0, 46.0
        11.0, 23.0, 35.0, 47.0
        nan, nan, nan, nan
        ...
        >>> for idx in range(12):  # doctest: +ELLIPSIS
        ...     print_vector(dill_assl.sequences.states.ic.series[:, idx])
        0.0, 12.0, 24.0, 36.0
        1.0, 13.0, 25.0, 37.0
        ...
        10.0, 22.0, 34.0, 46.0
        11.0, 23.0, 35.0, 47.0
        >>> for series in wc.value:  # doctest: +ELLIPSIS
        ...     print_vector(series)
        0.0, 24.0, 48.0, 72.0
        12.0, 36.0, 60.0, 84.0
        1.0, 25.0, 49.0, 73.0
        13.0, 37.0, 61.0, 85.0
        ...
        10.0, 34.0, 58.0, 82.0
        22.0, 46.0, 70.0, 94.0
        11.0, 35.0, 59.0, 83.0
        23.0, 47.0, 71.0, 95.0
        nan, nan, nan, nan
        ...
        >>> for jdx in range(12):  # doctest: +ELLIPSIS
        ...     for idx in range(2):
        ...         print_vector(dill_assl.sequences.states.wc.series[:, idx, jdx])
        0.0, 24.0, 48.0, 72.0
        12.0, 36.0, 60.0, 84.0
        1.0, 25.0, 49.0, 73.0
        13.0, 37.0, 61.0, 85.0
        ...
        10.0, 34.0, 58.0, 82.0
        22.0, 46.0, 70.0, 94.0
        11.0, 35.0, 59.0, 83.0
        23.0, 47.0, 71.0, 95.0

        Due to the current limitation regarding the `global` and the `selection` level
        and the circumstance that parameter-specific keyword arguments hardly ever
        resolve the `subunit` level, extracting the values of keyword arguments works
        only for the `device` level:

        >>> cfmax = SetItem(name="lag", master="hland_96", target="control.cfmax",
        ...                 keyword="forest", level="device")
        >>> cfmax.collect_variables(pub.selections)
        >>> cfmax.extract_values()
        >>> dill_assl.parameters.control.cfmax
        cfmax(field=4.55853, forest=2.735118)
        >>> print_vector(cfmax.value)
        2.735118, 3.0, 2.1, 2.1

        Method |SetItem.extract_values| cannot extract its complete data if the time
        series of any relevant variable is missing.  We disable the |IOSequence.series|
        attribute of the considered sequences to show how things work then:

        >>> dill_assl.sequences.states.uz.prepare_series(False)
        >>> dill_assl.sequences.states.ic.prepare_series(False)
        >>> dill_assl.sequences.states.wc.prepare_series(False)

        Method |SetItem.extract_values| emits a warning when encountering the first
        unprepared |IOSequence.series| attribute and, if existing, deletes already
        available data:

        >>> from hydpy.core.testtools import warn_later
        >>> with warn_later():
        ...     test("device")
        AttributeNotReadyWarning: While trying to query the values of exchange item \
`uz`, the following error occured: While trying to calculate the mean value of the \
internal time series of sequence `uz` of element `land_dill_assl`, the following error \
occurred: Sequence `uz` of element `land_dill_assl` is not requested to make any time \
series data available.
        AttributeNotReadyWarning: While trying to query the values of exchange item \
`ic`, the following error occured: While trying to calculate the mean value of the \
internal time series of sequence `ic` of element `land_dill_assl`, the following error \
occurred: Sequence `ic` of element `land_dill_assl` is not requested to make any time \
series data available.
        AttributeNotReadyWarning: While trying to query the values of exchange item \
`wc`, the following error occured: While trying to calculate the mean value of the \
internal time series of sequence `wc` of element `land_dill_assl`, the following error \
occurred: Sequence `wc` of element `land_dill_assl` is not requested to make any time \
series data available.

        >>> for series in uz.value:
        ...     print_vector(series)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem `uz` \
has/have not been prepared so far.
        >>> for series in ic.value:
        ...     print_vector(series)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem `ic` \
has/have not been prepared so far.
        >>> for series in wc.value:
        ...     print_vector(series)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem `wc` \
has/have not been prepared so far.

        >>> with warn_later():
        ...     test("subunit")
        AttributeNotReadyWarning: While trying to query the values of exchange item \
`uz`, the following error occured: Sequence `uz` of element `land_dill_assl` is not \
requested to make any time series data available.
        AttributeNotReadyWarning: While trying to query the values of exchange item \
`ic`, the following error occured: Sequence `ic` of element `land_dill_assl` is not \
requested to make any time series data available.
        AttributeNotReadyWarning: While trying to query the values of exchange item \
`wc`, the following error occured: Sequence `wc` of element `land_dill_assl` is not \
requested to make any time series data available.

        >>> for series in uz.value:
        ...     print_vector(series)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem `uz` \
has/have not been prepared so far.
        >>> for series in ic.value:  # doctest: +ELLIPSIS
        ...     print_vector(series)
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem `ic` \
has/have not been prepared so far.
        >>> for series in wc.value:  # doctest: +ELLIPSIS
        ...     print_vector(series)
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The value(s) of the SetItem `wc` \
has/have not been prepared so far.
        """
        series = self.targetspecs.series
        shape = self.seriesshape if series else self.shape
        itemvalues: NDArrayFloat = numpy.empty(shape, dtype=config.NP_FLOAT)
        jdx0, jdx1 = hydpy.pub.timegrids.simindices
        if self.level == "device":
            for idx, variable in enumerate(self.device2target.values()):
                if series:
                    assert isinstance(variable, sequencetools.IOSequence)
                    try:
                        itemvalues[idx] = variable.average_series()[jdx0:jdx1]
                    except exceptiontools.AttributeNotReady as exc:
                        self._value = None
                        warnings.warn(
                            f"While trying to query the values of exchange item "
                            f"`{self.name}`, the following error occured: {exc}",
                            exceptiontools.AttributeNotReadyWarning,
                        )
                        return
                elif self.targetspecs.keyword is None:
                    itemvalues[idx] = variable.average_values()
                else:
                    assert isinstance(variable, parametertools.Parameter)
                    itemvalues[idx] = variable.keywordarguments[
                        self.targetspecs.keyword
                    ]
        elif self.level == "subunit":
            idx0 = 0
            for variable in self.device2target.values():
                idx1 = idx0 + variable.numberofvalues
                if series:
                    assert isinstance(variable, sequencetools.IOSequence)
                    try:
                        targetvalues = variable.simseries.T
                        if variable.NDIM > 0:
                            targetvalues = targetvalues.reshape(
                                -1, targetvalues.shape[-1]
                            )
                    except exceptiontools.AttributeNotReady as exc:
                        self._value = None
                        warnings.warn(
                            f"While trying to query the values of exchange item "
                            f"`{self.name}`, the following error occured: {exc}",
                            exceptiontools.AttributeNotReadyWarning,
                        )
                        return
                else:
                    targetvalues = variable.values
                    if variable.NDIM > 1:
                        targetvalues = targetvalues.flatten()
                itemvalues[idx0:idx1] = targetvalues
                idx0 = idx1
        # pylint: disable=consider-using-in
        elif (self.level == "selection") or (self.level == "global"):
            raise NotImplementedError(
                f"HydPy does not support averaging values across different elements so "
                f"far.  So, it is not possible to aggregate to the {self.level} level."
            )
        else:
            assert_never(self.level)
        self.value = itemvalues
        return

    def __repr__(self) -> str:
        ts = self.targetspecs
        keyword = "" if ts.keyword is None else f'keyword="{ts.keyword}", '
        return (
            f"{type(self).__name__}("
            f'name="{self.name}", '
            f'master="{ts.master}", '
            f'target="{ts.specstring}", '
            f"{keyword}"
            f'level="{self.level}")'
        )


class MathItem(ChangeItem):
    """This base class performs some mathematical operations on the given values before
    assigning them to the handled target variables.

    Subclasses of |MathItem| like |AddItem| handle not only target variables but also
    base variables:

    >>> from hydpy.core.itemtools import MathItem
    >>> item = MathItem(name="sfcf", master="hland_96", target="control.sfcf",
    ...                 base="control.rfcf", level="global")
    >>> item
    MathItem(name="sfcf", master="hland_96", target="control.sfcf", \
base="control.rfcf", level="global")
    >>> item.targetspecs
    ExchangeSpecification(master="hland_96", variable="control.sfcf")
    >>> item.basespecs
    ExchangeSpecification(master="hland_96", variable="control.rfcf")

    Generally, each |MathItem| object calculates the value of the target variable of
    a |Device| object by using its current |ChangeItem.value| and the value(s) of the
    base variable of the same |Device|.
    """

    basespecs: ExchangeSpecification
    """The exchange specification for the chosen base variable."""
    target2base: dict[variabletools.Variable, variabletools.Variable]
    """All target variable objects and their related base variable objects."""

    def __init__(
        self, *, name: str, master: str, target: str, base: str, level: LevelType
    ) -> None:
        self.name = Name(name)
        self.targetspecs = ExchangeSpecification(master=master, variable=target)
        self.basespecs = ExchangeSpecification(master=master, variable=base)
        self.level = level
        self._value = None
        self._shape = None
        self.device2target = {}
        self.selection2targets = {}
        self.target2base = {}

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        """Apply method |ChangeItem.collect_variables| of the base class |ChangeItem|
        and also prepare the dictionary |MathItem.target2base|, which maps each target
        variable object to its base variable object.

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import AddItem
        >>> item = AddItem(name="alpha", master="hland_96", target="control.sfcf",
        ...                base="control.rfcf", level="global")
        >>> item.collect_variables(pub.selections)
        >>> land_dill_assl = hp.elements.land_dill_assl
        >>> control = land_dill_assl.model.parameters.control
        >>> item.device2target[land_dill_assl] is control.sfcf
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
            f"{type(self).__name__}("
            f'name="{self.name}", '
            f'master="{self.targetspecs.master}", '
            f'target="{self.targetspecs.specstring}", '
            f'base="{self.basespecs.specstring}", '
            f'level="{self.level}")'
        )


class AddItem(MathItem):
    """|MathItem| subclass performing additions.

    The following examples relate closely to the ones explained in the documentation of
    the method |ChangeItem.update_variables| of class |ChangeItem|.  Therefore, we
    similarly repeat them all to show that our |AddItem| always uses the sum of its own
    value(s) and the value(s) of the related base variable to update the value(s) of
    the target variable.

    We prepare the `HydPy-H-Lahn` example project:

    >>> from hydpy.core.testtools import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    We use the rainfall correction parameter (|hland_control.RfCF|) of the application
    model |hland_96| as the base variable.  Defining a different correction factor for
    each of the 49 hydrological response units allows strict testing:

    >>> value = 0.8
    >>> for element in hp.elements.catchment:
    ...     rfcf = element.model.parameters.control.rfcf
    ...     for idx in range(len(rfcf)):
    ...         rfcf[idx] = value
    ...         value += 0.01
    ...     print(element, rfcf)  # doctest: +ELLIPSIS
    land_dill_assl rfcf(0.8, ... 0.91)
    land_lahn_kalk rfcf(0.92, ... 1.05)
    land_lahn_leun rfcf(1.06, ... 1.15)
    land_lahn_marb rfcf(1.16, ... 1.28)

    We choose the snowfall correction parameter (|hland_control.SfCF|) as the target
    variable.  The following test calculations show the expected results for all
    available aggregation levels:

    >>> from hydpy.core.itemtools import AddItem
    >>> item = AddItem(name="sfcf", master="hland_96", target="control.sfcf",
    ...                base="control.rfcf", level="global")
    >>> item.collect_variables(pub.selections)
    >>> item.value = 0.1
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill_assl sfcf(0.9, ... 1.01)
    land_lahn_kalk sfcf(1.02, ... 1.15)
    land_lahn_leun sfcf(1.16, ... 1.25)
    land_lahn_marb sfcf(1.26, ... 1.38)

    >>> item.level = "selection"
    >>> item.collect_variables(pub.selections)
    >>> item.value = -0.1, 0.0
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill_assl sfcf(0.7, ... 0.81)
    land_lahn_kalk sfcf(0.92, ... 1.05)
    land_lahn_leun sfcf(1.06, ... 1.15)
    land_lahn_marb sfcf(1.06, ... 1.18)

    >>> item = AddItem(name="sfcf", master="hland_96", target="control.sfcf",
    ...                base="control.rfcf", level="device")
    >>> item.collect_variables(pub.selections)
    >>> item.value = -0.1, 0.0, 0.1, 0.2
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill_assl sfcf(0.7, ... 0.81)
    land_lahn_kalk sfcf(1.02, ... 1.15)
    land_lahn_leun sfcf(1.26, ... 1.35)
    land_lahn_marb sfcf(1.16, ... 1.28)

    >>> item = AddItem(name="sfcf", master="hland_96", target="control.sfcf",
    ...                base="control.rfcf", level="subunit")
    >>> item.collect_variables(pub.selections)
    >>> item.value = [idx/100 for idx in range(-20, 29)]
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill_assl sfcf(0.6, ... 0.82)
    land_lahn_kalk sfcf(0.97, ... 1.23)
    land_lahn_leun sfcf(1.25, ... 1.43)
    land_lahn_marb sfcf(1.08, ... 1.32)
    """

    def update_variable(
        self, variable: variabletools.Variable, value: NDArrayFloat
    ) -> None:
        """Assign the sum of the given value(s) and the value(s) of the base variable
        to the given target variable.

        If the addition fails, |AddItem.update_variable| raises an error like the
        following:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import AddItem
        >>> item = AddItem(name="sfcf", master="hland_96", target="control.sfcf",
        ...                base="control.rfcf", level="global")
        >>> item.collect_variables(pub.selections)
        >>> item._value = 0.1, 0.2
        >>> item.update_variables()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: When trying to add the value(s) `(0.1, 0.2)` of AddItem `sfcf` \
and the value(s) `[1.04283 ... 1.04283]` of variable `rfcf` of element \
`land_dill_assl`, the following error occurred: operands could not be broadcast \
together with shapes (12,) (2,)...
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


class MultiplyItem(MathItem):
    """|MathItem| subclass performing multiplications.

    Besides performing a multiplication instead of an addition, class |MultiplyItem|
    behaves exactly like class |AddItem|.  We adopt a single example of the
    documentation on class |AddItem| to demonstrate this difference:

    >>> from hydpy.core.testtools import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    >>> value = 0.8
    >>> for element in hp.elements.catchment:
    ...     rfcf = element.model.parameters.control.rfcf
    ...     for idx in range(len(rfcf)):
    ...         rfcf[idx] = value
    ...         value += 0.01
    ...     print(element, rfcf)  # doctest: +ELLIPSIS
    land_dill_assl rfcf(0.8, ... 0.91)
    land_lahn_kalk rfcf(0.92, ... 1.05)
    land_lahn_leun rfcf(1.06, ... 1.15)
    land_lahn_marb rfcf(1.16, ... 1.28)

    >>> from hydpy.core.itemtools import MultiplyItem
    >>> item = MultiplyItem(name="sfcf", master="hland_96", target="control.sfcf",
    ...                     base="control.rfcf", level="global")
    >>> item.collect_variables(pub.selections)
    >>> item.value = 2.0
    >>> item.update_variables()
    >>> for element in hp.elements.catchment:  # doctest: +ELLIPSIS
    ...     print(element, element.model.parameters.control.sfcf)
    land_dill_assl sfcf(1.6, ... 1.82)
    land_lahn_kalk sfcf(1.84, ... 2.1)
    land_lahn_leun sfcf(2.12, ... 2.3)
    land_lahn_marb sfcf(2.32, ... 2.56)
    """

    def update_variable(
        self, variable: variabletools.Variable, value: NDArrayFloat
    ) -> None:
        """Assign the product of the given value(s) and the value(s) of the base
        variable to the given target variable.

        If the multiplication fails, |MultiplyItem.update_variable| raises an error
        like the following:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import MultiplyItem
        >>> item = MultiplyItem(name="sfcf", master="hland_96", target="control.sfcf",
        ...                     base="control.rfcf", level="global")
        >>> item.collect_variables(pub.selections)
        >>> item._value = 0.1, 0.2
        >>> item.update_variables()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: When trying to multiply the value(s) `(0.1, 0.2)` of AddItem \
`sfcf` and the value(s) `[1.04283 ... 1.04283]` of variable `rfcf` of element \
`land_dill_assl`, the following error occurred: operands could not be broadcast \
together with shapes (12,) (2,)...
        """
        base = self.target2base[variable]
        try:
            result = base.value * value
        except BaseException:
            objecttools.augment_excmessage(
                f"When trying to multiply the value(s) `{value}` of AddItem "
                f"`{self.name}` and the value(s) `{base.value}` of variable "
                f"{objecttools.devicephrase(base)}"
            )
        super().update_variable(variable, result)


class GetItem(ExchangeItem):
    """Base class for querying the values of multiple |Parameter| or |Sequence_|
    objects of a specific type."""

    _device2name: dict[devicetools.Node | devicetools.Element, Name]
    _ndim: int | None = None

    def __init__(self, *, name: Name, master: str, target: str) -> None:
        self.name = name
        self.target = target.replace(".", "_")
        self.targetspecs = ExchangeSpecification(master=master, variable=target)
        self.device2target = {}
        self.selection2targets = {}
        self._device2name = {}

    @property
    def ndim(self) -> int:
        """The number of dimensions of the handled value vector.

        Trying to access property |GetItem.ndim| before calling method
        |GetItem.collect_variables| results in the following error message:

        >>> from hydpy.core.itemtools import GetItem
        >>> GetItem(name="temp", master="hland_96", target="states.lz").ndim
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `ndim` of GetItem \
`temp` is not ready.

        See the documentation of the method |GetItem.collect_variables| for further
        information.
        """
        if self._ndim is None:
            raise exceptiontools.AttributeNotReady(
                f"Attribute `ndim` of {type(self).__name__} `{self.name}` is not ready."
            )
        return self._ndim

    def collect_variables(self, selections: selectiontools.Selections) -> None:
        """Apply method |ExchangeItem.collect_variables| of the base class
        |ExchangeItem| and determine the |GetItem.ndim| attribute of the current
        |GetItem| object afterwards.

        The value of |GetItem.ndim| depends on whether the target variable's values or
        time series are of interest:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy.core.itemtools import GetItem
        >>> for target in ("states.lz", "states.lz.series",
        ...                "states.sm", "states.sm.series"):
        ...     item = GetItem(name="temp", master="hland_96", target=target)
        ...     item.collect_variables(pub.selections)
        ...     print(item, item.ndim)
        GetItem(name="temp", master="hland_96", target="states.lz") 0
        GetItem(name="temp", master="hland_96", target="states.lz.series") 1
        GetItem(name="temp", master="hland_96", target="states.sm") 1
        GetItem(name="temp", master="hland_96", target="states.sm.series") 2
        """
        super().collect_variables(selections)
        for device in sorted(self.device2target.keys(), key=lambda x: x.name):
            self._device2name[device] = Name(f"{device.name}_{self.target}")
        for target in self.device2target.values():
            self._ndim = target.NDIM
            if self.targetspecs.series:
                self._ndim += 1
            break

    def yield_name2subnames(
        self,
    ) -> Iterator[tuple[Name, str | tuple[()] | tuple[str, ...]]]:
        """Sequentially return pairs of the item name and its artificial sub-names.

        The purpose and definition of the sub-names are similar to those returned by
        property |ChangeItem.subnames| of class |ChangeItem| described in the
        documentation on method |ChangeItem.collect_variables|.  However, class
        |GetItem| does not support different aggregation levels and each |GetItem|
        object operates on the device level.  Therefore, the returned sub-names rely on
        the device names; and, for non-scalar target variables, additionally on the
        individual vector or matrix indices.

        Each item name is automatically generated and contains the name of the
        respective |Variable| object's |Device| and the target description.

        For 0-dimensional variables, there is only one sub-name that is identical to
        the device name:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import SetItem
        >>> item = GetItem(name="lz", master="hland_96", target="states.lz")
        >>> item.collect_variables(pub.selections)
        >>> for name, subnames in item.yield_name2subnames():
        ...     print(name, subnames)
        land_dill_assl_states_lz land_dill_assl
        land_lahn_kalk_states_lz land_lahn_kalk
        land_lahn_leun_states_lz land_lahn_leun
        land_lahn_marb_states_lz land_lahn_marb

        >>> item = GetItem(name="sim", master="nodes", target="sim.series")
        >>> item.collect_variables(pub.selections)
        >>> for name, subnames in item.yield_name2subnames():
        ...     print(name, subnames)
        dill_assl_sim_series dill_assl
        lahn_kalk_sim_series lahn_kalk
        lahn_leun_sim_series lahn_leun
        lahn_marb_sim_series lahn_marb

        For non-scalar variables, the sub-names combine the device name and all
        possible index combinations for the current shape of the target variable:

        >>> item = GetItem(name="sm", master="hland_96", target="states.sm")
        >>> item.collect_variables(pub.selections)
        >>> for name, subnames in item.yield_name2subnames():
        ...     print(name, subnames)  # doctest: +ELLIPSIS
        land_dill_assl_states_sm ('land_dill_assl_0', ..., 'land_dill_assl_11')
        land_lahn_kalk_states_sm ('land_lahn_kalk_0', ..., 'land_lahn_kalk_13')
        land_lahn_leun_states_sm ('land_lahn_leun_0', ..., 'land_lahn_leun_9')
        land_lahn_marb_states_sm ('land_lahn_marb_0', ..., 'land_lahn_marb_12')

        >>> item = GetItem(name="sp", master="hland_96", target="states.sp")
        >>> item.collect_variables(pub.selections)
        >>> for name, subnames in item.yield_name2subnames():
        ...     print(name, subnames)  # doctest: +ELLIPSIS
        land_dill_assl_states_sp ('land_dill_assl_0_0', ..., 'land_dill_assl_0_11')
        land_lahn_kalk_states_sp ('land_lahn_kalk_0_0', ..., 'land_lahn_kalk_0_13')
        land_lahn_leun_states_sp ('land_lahn_leun_0_0', ..., 'land_lahn_leun_0_9')
        land_lahn_marb_states_sp ('land_lahn_marb_0_0', ..., 'land_lahn_marb_0_12')
        """
        for device, name in self._device2name.items():
            subnames = _make_subunit_name(device, self.device2target[device])
            if isinstance(subnames, str):
                yield name, subnames
            else:
                yield name, tuple(subnames)

    def yield_name2value(
        self, idx1: int | None = None, idx2: int | None = None
    ) -> Iterator[tuple[Name, str]]:
        """Sequentially return name-value pairs describing the current state of the
        target variables.

        The item names are automatically generated and contain both the name of the
        |Device| of the respective |Variable| object and the target description:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import SetItem
        >>> item = GetItem(name="lz", master="hland_96", target="states.lz")
        >>> item.collect_variables(pub.selections)
        >>> hp.elements.land_dill_assl.model.sequences.states.lz = 100.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)
        land_dill_assl_states_lz 100.0
        land_lahn_kalk_states_lz 7.52648
        land_lahn_leun_states_lz 10.14007
        land_lahn_marb_states_lz 8.18711
        >>> item = GetItem(name="sm", master="hland_96", target="states.sm")
        >>> item.collect_variables(pub.selections)
        >>> hp.elements.land_dill_assl.model.sequences.states.sm = 2.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)  # doctest: +ELLIPSIS
        land_dill_assl_states_sm [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, \
2.0, 2.0, 2.0, 2.0]
        land_lahn_kalk_states_sm [101.31248, ..., 153.54053]
        ...

        When querying time series, one can restrict the span of interest by passing
        index values:

        >>> item = GetItem(name="sim", master="nodes", target="sim.series")
        >>> item.collect_variables(pub.selections)
        >>> hp.nodes.dill_assl.sequences.sim.series = 1.0, 2.0, 3.0, 4.0
        >>> for name, value in item.yield_name2value():
        ...     print(name, value)  # doctest: +ELLIPSIS
        dill_assl_sim_series [1.0, 2.0, 3.0, 4.0]
        lahn_kalk_sim_series [nan, ...
        ...
        >>> for name, value in item.yield_name2value(2, 3):
        ...     print(name, value)  # doctest: +ELLIPSIS
        dill_assl_sim_series [3.0]
        lahn_kalk_sim_series [nan]
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
            f'name="{self.name}", '
            f'master="{self.targetspecs.master}", '
            f'target="{self.targetspecs.specstring}")'
        )
