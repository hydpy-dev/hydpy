# -*- coding: utf-8 -*-
"""This module provides features for applying and implementing hydrological models."""
# import...
# ...from standard library
from __future__ import annotations
import abc
import collections
import contextlib
import importlib
import inspect
import itertools
import os
import types

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import conf
from hydpy.core import auxfiletools
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import importtools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils

if TYPE_CHECKING:
    from hydpy.core import masktools
    from hydpy.auxs import interptools


class _ModelModule(types.ModuleType):
    ControlParameters: Type[parametertools.SubParameters]
    DerivedParameters: Type[parametertools.SubParameters]
    FixedParameters: Type[parametertools.SubParameters]
    SolverParameters: Type[parametertools.SubParameters]


class Method:
    """Base class for defining (hydrological) calculation methods."""

    SUBMODELINTERFACES: ClassVar[Tuple[Type[SubmodelInterface], ...]]
    SUBMETHODS: Tuple[Type[Method], ...] = ()
    CONTROLPARAMETERS: Tuple[
        Type[Union[parametertools.Parameter, interptools.BaseInterpolator]], ...
    ] = ()
    DERIVEDPARAMETERS: Tuple[Type[parametertools.Parameter], ...] = ()
    FIXEDPARAMETERS: Tuple[Type[parametertools.Parameter], ...] = ()
    SOLVERPARAMETERS: Tuple[Type[parametertools.Parameter], ...] = ()
    REQUIREDSEQUENCES: Tuple[Type[sequencetools.Sequence_], ...] = ()
    UPDATEDSEQUENCES: Tuple[Type[sequencetools.Sequence_], ...] = ()
    RESULTSEQUENCES: Tuple[Type[sequencetools.Sequence_], ...] = ()

    __call__: Callable
    __name__: str

    def __init_subclass__(cls) -> None:
        if isinstance(call := cls.__call__, types.FunctionType):
            setattr(call, "__HYDPY_METHOD__", True)


class AutoMethod(Method):
    """Base class for defining methods that only call their submethods in the specified
    order without passing any arguments or other customisations."""

    @classmethod
    def __call__(cls, model: Model) -> None:
        for method in cls.SUBMETHODS:
            method.__call__(model)


abstractmodelmethods: Set[Callable[..., Any]] = set()


def abstractmodelmethod(method: Callable[P, T]) -> Callable[P, T]:
    """Alternative for Python's |abc.abstractmethod|.

    We currently use it to mark abstract methods in submodel interfaces that are not
    statically overridden by concrete implementations but dynamically added during
    model initialisation (either in a pure Python or a Cython version).

    So far, the only functionality of |abstractmodelmethod| is to collect all decorated
    functions in the set `abstractmodelmethods` so that one can find out which methods
    are "abstract model methods" and which are not. We might also use it later to
    extend our model consistency checks.
    """
    abstractmodelmethods.add(method)
    return method


class SubmodelProperty:
    """Descriptor for submodel attributes.

    |SubmodelProperty| instances link main models and their submodels.  They follow the
    attribute convention described in the documentation on class |SubmodelInterface|.
    Behind the scenes, they build the required connections both on the Python and the
    Cython level and perform some type-related tests (to avoid errors due to selecting
    submodels following the wrong interfaces).

    We prepare the main model and its submodel in the Cython and pure Python mode to
    test that |SubmodelProperty| works for all possible combinations:

    >>> from hydpy import prepare_model, pub
    >>> with pub.options.usecython(False):
    ...     mainmodel_python = prepare_model("lland")
    ...     submodel_python = prepare_model("ga_garto_submodel1")
    >>> with pub.options.usecython(True):
    ...     mainmodel_cython = prepare_model("lland")
    ...     submodel_cython = prepare_model("ga_garto_submodel1")

    By default, the main model handles no submodel:

    >>> mainmodel_python.soilmodel
    >>> mainmodel_cython.soilmodel

    For pure Python main models, it makes no difference how the submodel is
    initialised:

    >>> mainmodel_python.soilmodel = submodel_python
    >>> type(mainmodel_python.soilmodel)
    <class 'hydpy.models.ga_garto_submodel1.Model'>
    >>> mainmodel_python.cymodel

    >>> mainmodel_python.soilmodel = submodel_cython
    >>> type(mainmodel_python.soilmodel)
    <class 'hydpy.models.ga_garto_submodel1.Model'>
    >>> mainmodel_python.cymodel

    If both models are initialised in Cython mode, |SubmodelProperty| connects the
    instances of the Cython extension classes on the fly:

    >>> mainmodel_cython.soilmodel = submodel_cython
    >>> type(mainmodel_cython.soilmodel)
    <class 'hydpy.models.ga_garto_submodel1.Model'>
    >>> type(mainmodel_cython.cymodel.get_soilmodel())
    <class 'hydpy.cythons.autogen.c_ga_garto_submodel1.Model'>

    Combining a Cython main model with a pure Python submodel causes a |RuntimeError|,
    as using such a mix could result in hard-to-find errors:

    >>> mainmodel_cython.soilmodel = submodel_python
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to assign value `ga_garto_submodel1` of type `Model` \
to property `soilmodel`, the following error occurred: The main model `lland` is \
initialised in Cython mode, but the submodel `ga_garto_submodel1` in pure Python \
mode, so that the main model's cythonized methods cannot apply the submodel's methods.

    Disconnecting a submodel from its main model works by assigning |None| as well as
    using the `del` statement:

    >>> mainmodel_python.soilmodel = None
    >>> mainmodel_python.soilmodel

    >>> del mainmodel_cython.soilmodel
    >>> mainmodel_cython.soilmodel
    >>> mainmodel_cython.cymodel.get_soilmodel()

    >>> mainmodel_python.soilmodel = mainmodel_python
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign value `lland` of type `Model` to property \
`soilmodel`, the following error occurred: The given value is neither `None` nor an \
instance of any of the following types: `SoilModel_V1`.

    The automatically generated docstrings list the supported interfaces:

    >>> print(type(mainmodel_python).soilmodel.__doc__)
    Optional submodel that complies with the following interface: SoilModel_V1.
    """

    interfaces: Final[Tuple[Type[SubmodelInterface], ...]]
    optional: Final[bool]
    name: Final[str]  # type: ignore[misc]
    modeltype2instance: ClassVar[
        DefaultDict[Type[Model], List[SubmodelProperty]]
    ] = collections.defaultdict(lambda: [])

    def __init__(
        self, *interfaces: Type[SubmodelInterface], optional: bool = False
    ) -> None:
        self.interfaces = tuple(interfaces)
        self.optional = optional
        interfacenames = (i.__name__ for i in self.interfaces)
        prefix = "Optional submodel" if optional else "Required submodel"
        suffix = (
            "the following interface"
            if len(interfaces) == 1
            else "one of the following interfaces"
        )
        self.__doc__ = (
            f"{prefix} that complies with {suffix}: "
            f"{objecttools.enumeration(interfacenames, conjunction='or')}."
        )

    def __set_name__(self, owner: Type[Model], name: str) -> None:
        self.name = name  # type: ignore[misc]
        self.modeltype2instance[owner].append(self)

    @overload
    def __get__(self, obj: None, objtype: Optional[Type[Model]]) -> Self:
        ...

    @overload
    def __get__(self, obj: Model, objtype: Optional[Type[Model]]) -> Optional[Model]:
        ...

    def __get__(
        self, obj: Optional[Model], objtype: Optional[Type[Model]] = None
    ) -> Union[SubmodelProperty, Optional[Model]]:
        if obj is None:
            return self
        return vars(obj).get(self.name, None)

    def __set__(self, obj: Model, value: Optional[Model]) -> None:
        try:
            if value is None:
                self.__delete__(obj)
            elif isinstance(value, self.interfaces):
                vars(obj)[self.name] = value
                if obj.cymodel is not None:
                    if value.cymodel is None:
                        raise RuntimeError(
                            f"The main model `{obj.name}` is initialised in Cython "
                            f"mode, but the submodel `{value.name}` in pure Python "
                            f"mode, so that the main model's cythonized methods "
                            f"cannot apply the submodel's methods."
                        )
                    getattr(obj.cymodel, f"set_{self.name}")(value.cymodel)
            else:
                interfacenames = (i.__name__ for i in self.interfaces)
                raise ValueError(
                    f"The given value is neither `None` nor an instance of any of the "
                    f"following types: `{objecttools.enumeration(interfacenames)}`."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to assign {objecttools.value_of_type(value)} to "
                f"property `{self.name}`"
            )

    def __delete__(self, obj: Model) -> None:
        vars(obj)[self.name] = None
        if obj.cymodel is not None:
            getattr(obj.cymodel, f"set_{self.name}")(None)


class SubmodelIsMainmodelProperty:
    """Descriptor for boolean "submodel_is_mainmodel" attributes.

    |SubmodelIsMainmodelProperty| instances work like simple boolean attributes but
    silently synchronise the equally named boolean attributes of the corresponding
    cython model, if available:

    >>> from hydpy import prepare_model, pub
    >>> with pub.options.usecython(True):
    ...     model = prepare_model("hland_v1")
    >>> type(model).aetmodel_is_mainmodel._name
    'aetmodel_is_mainmodel'
    >>> model.aetmodel_is_mainmodel
    False
    >>> model.cymodel.aetmodel_is_mainmodel
    0
    >>> model.aetmodel_is_mainmodel = True
    >>> model.aetmodel_is_mainmodel
    True
    >>> model.cymodel.aetmodel_is_mainmodel
    1
    """

    _owner2value: Dict[Model, bool]
    _name: Final[str]  # type: ignore[misc]

    def __init__(self, doc: Optional[str] = None) -> None:
        self._owner2value = {}
        self.__doc__ = doc

    def __set_name__(self, owner: Type[Model], name: str) -> None:
        self._name = name  # type: ignore[misc]

    @overload
    def __get__(self, obj: None, objtype: Optional[Type[Model]]) -> Self:
        ...

    @overload
    def __get__(self, obj: Model, objtype: Optional[Type[Model]]) -> bool:
        ...

    def __get__(
        self, obj: Optional[Model], objtype: Optional[Type[Model]] = None
    ) -> Union[Self, bool]:
        if obj is None:
            return self
        return self._owner2value.get(obj, False)

    def __set__(self, obj: Model, value: bool) -> None:
        self._owner2value[obj] = value
        if (cymodel := obj.cymodel) is not None:
            setattr(cymodel, self._name, value)


class SubmodelTypeIDProperty:
    """Descriptor for integer "submodel_typeid" attributes.

    |SubmodelTypeIDProperty| instances work like simple integer attributes but silently
    synchronise the equally named integer attributes of the corresponding cython model,
    if available:

    >>> from hydpy import prepare_model, pub
    >>> with pub.options.usecython(True):
    ...     model = prepare_model("hland_v1")
    >>> type(model).aetmodel_typeid._name
    'aetmodel_typeid'
    >>> model.aetmodel_typeid
    0
    >>> model.cymodel.aetmodel_typeid
    0
    >>> model.aetmodel_typeid = 1
    >>> model.aetmodel_typeid
    1
    >>> model.cymodel.aetmodel_typeid
    1
    """

    _owner2value: Dict[Model, int]
    _name: Final[str]  # type: ignore[misc]

    def __init__(self, doc: Optional[str] = None) -> None:
        self._owner2value = {}
        self.__doc__ = doc

    def __set_name__(self, owner: Type[Model], name: str) -> None:
        self._name = name  # type: ignore[misc]

    @overload
    def __get__(self, obj: None, objtype: Optional[Type[Model]]) -> Self:
        ...

    @overload
    def __get__(self, obj: Model, objtype: Optional[Type[Model]]) -> int:
        ...

    def __get__(
        self, obj: Optional[Model], objtype: Optional[Type[Model]] = None
    ) -> Union[Self, int]:
        if obj is None:
            return self
        return self._owner2value.get(obj, 0)

    def __set__(self, obj: Model, value: int) -> None:
        self._owner2value[obj] = value
        if (cymodel := obj.cymodel) is not None:
            setattr(cymodel, self._name, value)


class IndexProperty:
    """Base class for index descriptors like |Idx_Sim|."""

    name: str

    def __set_name__(self, owner: Model, name: str) -> None:
        self.name = name.lower()

    @overload
    def __get__(self, obj: Model, objtype: Type[Model]) -> int:
        ...

    @overload
    def __get__(self, obj: None, objtype: Type[Model]) -> Self:
        ...

    def __get__(self, obj: Optional[Model], objtype: Type[Model]) -> Union[Self, int]:
        if obj is None:
            return self
        if obj.cymodel:
            return getattr(obj.cymodel, self.name)
        return vars(obj).get(self.name, 0)

    def __set__(self, obj: Model, value: int) -> None:
        if obj.cymodel:
            setattr(obj.cymodel, self.name, value)
        else:
            vars(obj)[self.name] = value


class Idx_Sim(IndexProperty):
    """The simulation step index.

    Some model methods require knowing the index of the current simulation step (with
    respect to the initialisation period), which one usually updates by passing it to
    |Model.simulate|.  However, you can change it manually via the |modeltools.Idx_Sim|
    descriptor, which is often beneficial during testing:

    >>> from hydpy.models.hland_v1 import *
    >>> parameterstep("1d")
    >>> model.idx_sim
    0
    >>> model.idx_sim = 1
    >>> model.idx_sim
    1

    Like other objects of |IndexProperty| subclasses, |Idx_Sim| objects are aware of
    their name:

    >>> Model.idx_sim.name
    'idx_sim'
    """

    def __init__(self) -> None:
        self.__doc__ = "The simulation step index."


class Idx_HRU(IndexProperty):
    """The hydrological response unit index.

    The documentation on class |Idx_Sim| explains the general purpose and handling of
    |IndexProperty| instances.
    """

    def __init__(self) -> None:
        self.__doc__ = "The hydrological response unit index."


class Idx_Segment(IndexProperty):
    """The segment index.

    The documentation on class |Idx_Sim| explains the general purpose and handling of
    |IndexProperty| instances.
    """

    def __init__(self) -> None:
        self.__doc__ = "The segment index."


class Idx_Run(IndexProperty):
    """The run index.

    The documentation on class |Idx_Sim| explains the general purpose and handling of
    |IndexProperty| instances.
    """

    def __init__(self) -> None:
        self.__doc__ = "The run index."


class Model:
    """Base class for all hydrological models.

    Class |Model| provides everything to create a usable application model, except
    method |Model.simulate|.  See classes |AdHocModel| and |ELSModel|, which implement
    this method.

    Class |Model| does not prepare the strongly required attributes `parameters` and
    `sequences` during initialisation.  You need to add them manually whenever you want
    to prepare a workable |Model| object on your own (see the factory functions
    |prepare_model| and |parameterstep|, which do this regularly).

    Similar to `parameters` and `sequences`, there is also the dynamic `masks`
    attribute, making all predefined masks of the actual model type available within a
    |Masks| object:

    >>> from hydpy.models.hland_v1 import *
    >>> parameterstep("1d")
    >>> model.masks
    complete of module hydpy.models.hland.hland_masks
    land of module hydpy.models.hland.hland_masks
    upperzone of module hydpy.models.hland.hland_masks
    snow of module hydpy.models.hland.hland_masks
    soil of module hydpy.models.hland.hland_masks
    field of module hydpy.models.hland.hland_masks
    forest of module hydpy.models.hland.hland_masks
    ilake of module hydpy.models.hland.hland_masks
    glacier of module hydpy.models.hland.hland_masks
    sealed of module hydpy.models.hland.hland_masks
    noglacier of module hydpy.models.hland.hland_masks

    You can use these masks, for example, to average the zone-specific precipitation
    values handled by sequence |hland_fluxes.PC|.  When passing no argument, method
    |Variable.average_values| applies the `complete` mask.  For example, pass mask
    `land` to average the values of all zones except those of type
    |hland_constants.ILAKE|:

    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
    >>> zonearea.values = 1.0
    >>> fluxes.pc = 1.0, 3.0, 5.0, 7.0
    >>> fluxes.pc.average_values()
    4.0
    >>> fluxes.pc.average_values(model.masks.land)
    3.0
    """

    cymodel: Optional[CyModelProtocol]
    parameters: parametertools.Parameters
    sequences: sequencetools.Sequences
    masks: masktools.Masks
    idx_sim = Idx_Sim()

    _element: Optional[devicetools.Element]
    _NAME: ClassVar[str]

    INLET_METHODS: ClassVar[Tuple[Type[Method], ...]]
    OUTLET_METHODS: ClassVar[Tuple[Type[Method], ...]]
    RECEIVER_METHODS: ClassVar[Tuple[Type[Method], ...]]
    SENDER_METHODS: ClassVar[Tuple[Type[Method], ...]]
    ADD_METHODS: ClassVar[Tuple[Callable, ...]]
    METHOD_GROUPS: ClassVar[Tuple[str, ...]]
    SUBMODELINTERFACES: ClassVar[Tuple[Type[SubmodelInterface], ...]]
    SUBMODELS: ClassVar[Tuple[Type[Submodel], ...]]

    SOLVERPARAMETERS: Tuple[Type[parametertools.Parameter], ...] = ()

    def __init__(self) -> None:
        self.cymodel = None
        self._element = None
        self._init_methods()

    def _init_methods(self) -> None:
        """Convert all pure Python calculation functions of the model class to methods
        and assign them to the model instance."""
        blacklist_shortnames: Set[str] = set()
        shortname2method: Dict[str, types.MethodType] = {}
        for cls_ in self.get_methods():
            longname = cls_.__name__.lower()
            method = types.MethodType(cls_.__call__, self)
            setattr(self, longname, method)
            shortname = longname.rpartition("_")[0]
            if shortname in blacklist_shortnames:
                continue
            if shortname in shortname2method:
                del shortname2method[shortname]
                blacklist_shortnames.add(shortname)
            else:
                shortname2method[shortname] = method
        for shortname, method in shortname2method.items():
            setattr(self, shortname, method)

    @property
    def element(self) -> devicetools.Element:
        """The model instance's master element.

        Usually, one assigns a |Model| instance to an |Element| instance, but the other
        way round works as well (for more information, see the documentation on
        property |Element.model| of class |Element|):

        >>> from hydpy import Element, prepare_model
        >>> from hydpy.core.modeltools import Model
        >>> model = prepare_model("musk_classic")
        >>> model.element
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Model `musk_classic` is not \
connected to an `Element` so far.

        >>> e = Element("e")
        >>> model.element = e
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `outlet` \
sequences of the model handled by element `e`, the following error occurred: Sequence \
`q` of element `e` cannot be connected due to no available node handling variable `Q`.
        >>> model.element
        Element("e")
        >>> e.model.name
        'musk_classic'

        >>> del model.element
        >>> model.element
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Model `musk_classic` is not \
connected to an `Element` so far.
        >>> e.model
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The model object of element `e` \
has been requested but not been prepared so far.
        """
        if (element := self._element) is None:
            raise exceptiontools.AttributeNotReady(
                f"Model `{self.name}` is not connected to an `Element` so far."
            )
        return element

    @element.setter
    def element(self, element: devicetools.Element) -> None:
        for model in self.find_submodels(include_mainmodel=True).values():
            model._element = element  # pylint: disable=protected-access
        if exceptiontools.getattr_(element, "model", None) is not self:
            element.model = self

    @element.deleter
    def element(self) -> None:
        if (element := self._element) is not None:
            if exceptiontools.getattr_(element, "model", None) is self:
                del element.model
        for model in self.find_submodels(include_mainmodel=True).values():
            model._element = None  # pylint: disable=protected-access

    def connect(self) -> None:
        """Connect all |LinkSequence| objects and the selected |InputSequence| and
        |OutputSequence| objects of the actual model to the corresponding
        |NodeSequence| objects.

        You cannot connect any sequences until the |Model| object itself is connected
        to an |Element| object referencing the required |Node| objects:

        >>> from hydpy import prepare_model
        >>> prepare_model("musk_classic").connect()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to build the node \
connection of the `input` sequences of the model handled by element `?`, the \
following error occurred: Model `musk_classic` is not connected to an `Element` so far.

        The application model |musk_classic| can receive inflow from an arbitrary
        number of upstream nodes and passes its outflow to a single downstream node
        (note that property |Element.model| of class |Element| calls method
        |Model.connect| automatically):

        >>> from hydpy import Element, Node
        >>> in1 = Node("in1", variable="Q")
        >>> in2 = Node("in2", variable="Q")
        >>> out1 = Node("out1", variable="Q")

        >>> element1 = Element("element1", inlets=(in1, in2), outlets=out1)
        >>> element1.model = prepare_model("musk_classic")

        Now all connections work as expected:

        >>> in1.sequences.sim = 1.0
        >>> in2.sequences.sim = 2.0
        >>> out1.sequences.sim = 3.0
        >>> element1.model.sequences.inlets.q
        q(1.0, 2.0)
        >>> element1.model.sequences.outlets.q
        q(3.0)
        >>> element1.model.sequences.inlets.q *= 2.0
        >>> element1.model.sequences.outlets.q *= 2.0
        >>> in1.sequences.sim
        sim(2.0)
        >>> in2.sequences.sim
        sim(4.0)
        >>> out1.sequences.sim
        sim(6.0)

        To show some possible errors and related error messages, we define three
        additional nodes, two handling variables different from discharge (`Q`):

        >>> in3 = Node("in3", variable="X")
        >>> out2 = Node("out2", variable="Q")
        >>> out3 = Node("out3", variable="X")

        Link sequence names must match the `variable` a node is handling:

        >>> element2 = Element("element2", inlets=(in1, in2), outlets=out3)
        >>> element2.model = prepare_model("musk_classic")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `outlet` \
sequences of the model handled by element `element2`, the following error occurred: \
Sequence `q` of element `element2` cannot be connected due to no available node \
handling variable `Q`.

        One can connect a 0-dimensional link sequence to a single node sequence only:

        >>> element3 = Element("element3", inlets=(in1, in2), outlets=(out1, out2))
        >>> element3.model = prepare_model("musk_classic")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `outlet` \
sequences of the model handled by element `element3`, the following error occurred: \
Sequence `q` cannot be connected as it is 0-dimensional but multiple nodes are \
available which are handling variable `Q`.

        Method |Model.connect| generally reports about unusable node sequences:

        >>> element4 = Element("element4", inlets=(in1, in2), outlets=(out1, out3))
        >>> element4.model = prepare_model("musk_classic")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `outlet` \
sequences of the model handled by element `element4`, the following error occurred: \
The following nodes have not been connected to any sequences: out3.

        >>> element5 = Element("element5", inlets=(in1, in2, in3), outlets=out1)
        >>> element5.model = prepare_model("musk_classic")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `inlet` \
sequences of the model handled by element `element5`, the following error occurred: \
The following nodes have not been connected to any sequences: in3.

        >>> element6 = Element("element6", inlets=in1, outlets=out1, receivers=in2)
        >>> element6.model = prepare_model("musk_classic")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `receiver` \
sequences of the model handled by element `element6`, the following error occurred: \
The following nodes have not been connected to any sequences: in2.

        >>> element7 = Element("element7", inlets=in1, outlets=out1, senders=in2)
        >>> element7.model = prepare_model("musk_classic")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `sender` \
sequences of the model handled by element `element7`, the following error occurred: \
The following nodes have not been connected to any sequences: in2.

        The above examples explain how to connect link sequences to their nodes.  Such
        connections are relatively hard requirements (|musk_classic| definitively needs
        inflow provided from a node, which the node itself typically receives from
        another model).  In contrast, connections between input or output sequences and
        nodes are optional.  If one defines such a connection for an input sequence, it
        receives data from the related node; otherwise, it uses its individually
        managed data, usually read from a file.  If one defines such a connection for
        an output sequence, it passes its internal data to the related node; otherwise,
        nothing happens.

        We demonstrate this functionality by focussing on the input sequences
        |hland_inputs.T| and |hland_inputs.P| and the output sequences |hland_fluxes.Q0|
        and |hland_states.UZ| of application model |hland_v1|.  |hland_inputs.T| uses
        its own data (which we define manually, but we could read it from a file as
        well), whereas |hland_inputs.P| gets its data from node `inp1`.  Flux sequence
        |hland_fluxes.Q0| and state sequence |hland_states.UZ| pass their data to two
        separate output nodes, whereas all other fluxes and states do not.  This
        functionality requires telling each node which sequence it should connect to,
        which we do by passing the sequence types (or the globally available aliases
        `hland_P`, `hland_Q0`, and `hland_UZ`) to the `variable` keyword of different
        node objects:

        >>> from hydpy import pub
        >>> from hydpy.inputs import hland_P
        >>> from hydpy.outputs import hland_Q0, hland_UZ
        >>> pub.timegrids = "2000-01-01", "2000-01-06", "1d"

        >>> inp1 = Node("inp1", variable=hland_P)
        >>> outp1 = Node("outp1", variable=hland_Q0)
        >>> outp2 = Node("outp2", variable=hland_UZ)
        >>> element8 = Element(
        ...     "element8", outlets=out1, inputs=inp1, outputs=[outp1, outp2])
        >>> element8.model = prepare_model("hland_v1")
        >>> element8.prepare_inputseries()
        >>> element8.model.sequences.inputs.t.series = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> inp1.sequences.sim(9.0)
        >>> element8.model.load_data(2)
        >>> element8.model.sequences.inputs.t
        t(3.0)
        >>> element8.model.sequences.inputs.p
        p(9.0)
        >>> element8.model.sequences.fluxes.q0 = 99.0
        >>> element8.model.sequences.states.uz = 999.0
        >>> element8.model.update_outputs()
        >>> outp1.sequences.sim
        sim(99.0)
        >>> outp2.sequences.sim
        sim(999.0)

        Instead of using single |InputSequence| and |OutputSequence| subclasses, one
        can create and apply fused variables, combining multiple subclasses (see the
        documentation on class |FusedVariable| for more information and a more
        realistic example):

        >>> from hydpy import FusedVariable
        >>> from hydpy.inputs import lland_Nied
        >>> from hydpy.outputs import lland_QDGZ
        >>> Precip = FusedVariable("Precip", hland_P, lland_Nied)
        >>> inp2 = Node("inp2", variable=Precip)
        >>> FastRunoff = FusedVariable("FastRunoff", hland_Q0, lland_QDGZ)
        >>> outp3 = Node("outp3", variable=FastRunoff)
        >>> element9 = Element("element9", outlets=out1, inputs=inp2, outputs=outp3)
        >>> element9.model = prepare_model("hland_v1")
        >>> inp2.sequences.sim(9.0)
        >>> element9.model.load_data(0)
        >>> element9.model.sequences.inputs.p
        p(9.0)
        >>> element9.model.sequences.fluxes.q0 = 99.0
        >>> element9.model.update_outputs()
        >>> outp3.sequences.sim
        sim(99.0)

        Method |Model.connect| reports if one of the given fused variables does not
        find a fitting sequence:

        >>> from hydpy.inputs import lland_TemL
        >>> Wrong = FusedVariable("Wrong", lland_Nied, lland_TemL)
        >>> inp3 = Node("inp3", variable=Wrong)
        >>> element10 = Element("element10", outlets=out1, inputs=inp3)
        >>> element10.model = prepare_model("hland_v1")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `input` sequences \
of the model handled by element `element10`, the following error occurred: None of \
the input sequences of model `hland_v1` is among the sequences of the fused variable \
`Wrong` of node `inp3`.

        >>> outp4 = Node("outp4", variable=Wrong)
        >>> element11 = Element("element11", outlets=out1, outputs=outp4)
        >>> element11.model = prepare_model("hland_v1")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `output` \
sequences of the model handled by element `element11`, the following error occurred: \
None of the output sequences of model `hland_v1` is among the sequences of the fused \
variable `Wrong` of node `outp4`.

        Selecting wrong sequences results in the following error messages:

        >>> outp5 = Node("outp5", variable=hland_Q0)
        >>> element12 = Element("element12", outlets=out1, inputs=outp5)
        >>> element12.model = prepare_model("hland_v1")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `input` sequences \
of the model handled by element `element12`, the following error occurred: No input \
sequence of model `hland_v1` is named `q0`.

        >>> inp5 = Node("inp5", variable="P")
        >>> element13 = Element("element13", outlets=out1, outputs=inp5)
        >>> element13.model = prepare_model("hland_v1")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `output` sequences \
of the model handled by element `element13`, the following error occurred: No factor, \
flux, or state sequence of model `hland_v1` is named `p`.

        So far, you can build connections to 0-dimensional output sequences only:

        >>> from hydpy.models.hland.hland_fluxes import PC
        >>> outp6 = Node("outp6", variable=PC)
        >>> element14 = Element("element14", outlets=out1, outputs=outp6)
        >>> element14.model = prepare_model("hland_v1")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `output` sequences \
of the model handled by element `element14`, the following error occurred: Only \
connections with 0-dimensional output sequences are supported, but sequence `pc` is \
1-dimensional.

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
            >>> FusedVariable.clear_registry()
        """
        group = "inputs"
        try:
            self._connect_inputs()
            group = "outputs"
            self._connect_outputs()
            group = "inlets"
            self._connect_inlets()
            group = "receivers"
            self._connect_receivers()
            group = "outlets"
            self._connect_outlets()
            group = "senders"
            self._connect_senders()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to build the node connection of the `{group[:-1]}` "
                f"sequences of the model handled by element "
                f"`{objecttools.devicename(self)}`"
            )

    def _connect_inputs(self) -> None:
        for node in self.element.inputs:
            if isinstance(node.variable, devicetools.FusedVariable):
                connected = False
                for submodel in self.find_submodels(include_mainmodel=True).values():
                    for sequence in submodel.sequences.inputs:
                        if sequence in node.variable:
                            sequence.set_pointer(node.get_double("inputs"))
                            connected = True
                            break
                if not connected:
                    submodelphrase = objecttools.submodelphrase(self)
                    raise TypeError(
                        f"None of the input sequences of {submodelphrase} is among "
                        f"the sequences of the fused variable `{node.variable}` of "
                        f"node `{node.name}`."
                    )
            else:
                name = self._determine_name(node.variable)
                sequence_ = getattr(self.sequences.inputs, name, None)
                if sequence_ is None:
                    raise TypeError(
                        f"No input sequence of model `{self}` is named `{name}`."
                    )
                sequence_.set_pointer(node.get_double("inputs"))

    def _connect_outputs(self) -> None:
        def _set_pointer(
            seq: sequencetools.OutputSequence, node_: devicetools.Node
        ) -> None:
            if seq.NDIM > 0:
                raise TypeError(
                    f"Only connections with 0-dimensional output sequences are "
                    f"supported, but sequence `{seq.name}` is {seq.NDIM}-dimensional."
                )
            seq.set_pointer(node_.get_double("outputs"))

        for node in self.element.outputs:
            if isinstance(node.variable, devicetools.FusedVariable):
                connected = False
                for submodel in self.find_submodels(include_mainmodel=True).values():
                    for sequence in itertools.chain(
                        submodel.sequences.factors,
                        submodel.sequences.fluxes,
                        submodel.sequences.states,
                    ):
                        if sequence in node.variable:
                            _set_pointer(sequence, node)
                            connected = True
                            break
                if not connected:
                    submodelphrase = objecttools.submodelphrase(self)
                    raise TypeError(
                        f"None of the output sequences of {submodelphrase} is among "
                        f"the sequences of the fused variable `{node.variable}` of "
                        f"node `{node.name}`."
                    )
            else:
                name = self._determine_name(node.variable)
                sequence_ = getattr(self.sequences.factors, name, None)
                if sequence_ is None:
                    sequence_ = getattr(self.sequences.fluxes, name, None)
                if sequence_ is None:
                    sequence_ = getattr(self.sequences.states, name, None)
                if sequence_ is None:
                    raise TypeError(
                        f"No factor, flux, or state sequence of model `{self}` is "
                        f"named `{name}`."
                    )
                _set_pointer(sequence_, node)

    def _determine_name(self, var: Union[str, sequencetools.InOutSequenceTypes]) -> str:
        if isinstance(var, str):
            return var.lower()
        return var.__name__.lower()

    def _connect_inlets(self) -> None:
        self._connect_subgroup("inlets")

    def _connect_receivers(self) -> None:
        self._connect_subgroup("receivers")

    def _connect_outlets(self) -> None:
        self._connect_subgroup("outlets")

    def _connect_senders(self) -> None:
        self._connect_subgroup("senders")

    def _connect_subgroup(self, group: str) -> None:
        available_nodes = getattr(self.element, group)
        links = getattr(self.sequences, group, ())
        applied_nodes = []
        for seq in links:
            selected_nodes = tuple(
                node
                for node in available_nodes
                if str(node.variable).lower() == seq.name
            )
            if seq.NDIM == 0:
                if not selected_nodes:
                    raise RuntimeError(
                        f"Sequence {objecttools.elementphrase(seq)} cannot be "
                        f"connected due to no available node handling variable "
                        f"`{seq.name.upper()}`."
                    )
                if len(selected_nodes) > 1:
                    raise RuntimeError(
                        f"Sequence `{seq.name}` cannot be connected as it is "
                        f"0-dimensional but multiple nodes are available which are "
                        f"handling variable `{seq.name.upper()}`."
                    )
                applied_nodes.append(selected_nodes[0])
                seq.set_pointer(selected_nodes[0].get_double(group))
            elif seq.NDIM == 1:
                seq.shape = len(selected_nodes)
                for idx, node in enumerate(selected_nodes):
                    applied_nodes.append(node)
                    seq.set_pointer(node.get_double(group), idx)
        if len(applied_nodes) < len(available_nodes):
            remaining_nodes = [
                node.name for node in available_nodes if node not in applied_nodes
            ]
            raise RuntimeError(
                f"The following nodes have not been connected to any sequences: "
                f"{objecttools.enumeration(remaining_nodes)}."
            )

    @property
    def name(self) -> str:
        """Name of the model type.

        For base models, |Model.name| corresponds to the package name:

        >>> from hydpy import prepare_model
        >>> hland = prepare_model("hland")
        >>> hland.name
        'hland'

        For application models, |Model.name| to corresponds the module name:

        >>> hland_v1 = prepare_model("hland_v1")
        >>> hland_v1.name
        'hland_v1'

        This last example has only technical reasons:

        >>> hland.name
        'hland'
        """
        return self._NAME

    def prepare_allseries(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |Model.prepare_inputseries| with `read_jit=jit` and methods
        |Model.prepare_factorseries|, |Model.prepare_fluxseries|, and
        |Model.prepare_stateseries| with `write_jit=jit`."""
        self.prepare_inputseries(allocate_ram=allocate_ram, read_jit=jit)
        self.prepare_factorseries(allocate_ram=allocate_ram, write_jit=jit)
        self.prepare_fluxseries(allocate_ram=allocate_ram, write_jit=jit)
        self.prepare_stateseries(allocate_ram=allocate_ram, write_jit=jit)

    def prepare_inputseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all directly handled
        |InputSequence| objects."""
        self.sequences.inputs.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def prepare_factorseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all directly handled
        |FactorSequence| objects."""
        self.sequences.factors.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def prepare_fluxseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all directly handled
        |FluxSequence|."""
        self.sequences.fluxes.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def prepare_stateseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all directly handled
        |StateSequence| objects and."""
        self.sequences.states.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def load_allseries(self) -> None:
        """Call method |Model.load_inputseries|, |Model.load_factorseries|,
        |Model.load_fluxseries|, and |Model.load_stateseries|."""
        self.load_inputseries()
        self.load_factorseries()
        self.load_fluxseries()
        self.load_stateseries()

    def load_inputseries(self) -> None:
        """Call method |IOSequence.load_series| of all directly handled |InputSequence|
        objects."""
        self.sequences.inputs.load_series()

    def load_factorseries(self) -> None:
        """Call method |IOSequence.load_series| of all directly handled
        |FactorSequence| objects."""
        self.sequences.factors.load_series()

    def load_fluxseries(self) -> None:
        """Call method |IOSequence.load_series| of all directly handled |FluxSequence|
        objects."""
        self.sequences.fluxes.load_series()

    def load_stateseries(self) -> None:
        """Call method |IOSequence.load_series| of all directly handled |StateSequence|
        objects."""
        self.sequences.states.load_series()

    def save_allseries(self) -> None:
        """Call method |Model.save_inputseries|, |Model.save_factorseries|,
        |Model.save_fluxseries|, and |Model.save_stateseries|."""
        self.save_inputseries()
        self.save_factorseries()
        self.save_fluxseries()
        self.save_stateseries()

    def save_inputseries(self) -> None:
        """Call method |IOSequence.save_series| of all directly handled |InputSequence|
        objects."""
        self.sequences.inputs.save_series()

    def save_factorseries(self) -> None:
        """Call method |IOSequence.save_series| of all directly handled
        |FactorSequence| objects."""
        self.sequences.factors.save_series()

    def save_fluxseries(self) -> None:
        """Call method |IOSequence.save_series| of all directly handled |FluxSequence|
        objects."""
        self.sequences.fluxes.save_series()

    def save_stateseries(self) -> None:
        """Call method |IOSequence.save_series| of all directly handled |StateSequence|
        objects."""
        self.sequences.states.save_series()

    def get_controlfileheader(
        self,
        import_submodels: bool = True,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        simulationstep: Optional[timetools.PeriodConstrArg] = None,
    ) -> str:
        """Return the header of a parameter control file.

        The header contains the default coding information, the model import commands
        and the actual parameter and simulation step sizes:

        >>> from hydpy import prepare_model, pub
        >>> model = prepare_model("hland_v1")
        >>> model.aetmodel = prepare_model("evap_aet_hbv96")
        >>> pub.timegrids = "2000.01.01", "2001.01.01", "1h"
        >>> print(model.get_controlfileheader())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hland_v1 import *
        from hydpy.models import evap_aet_hbv96
        <BLANKLINE>
        simulationstep("1h")
        parameterstep("1d")
        <BLANKLINE>
        <BLANKLINE>

        Optionally, you can omit the submodel import lines and define alternative
        parameter step and simulation step sizes:

        >>> print(model.get_controlfileheader(
        ...     import_submodels=False, parameterstep="2d", simulationstep="3d"))
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hland_v1 import *
        <BLANKLINE>
        simulationstep("3d")
        parameterstep("2d")
        <BLANKLINE>
        <BLANKLINE>

        .. testsetup::

            >>> del pub.timegrids
        """
        lines = ["# -*- coding: utf-8 -*-\n", f"from hydpy.models.{self} import *"]
        if import_submodels:
            for submodel in self.find_submodels(include_subsubmodels=True).values():
                lines.append(f"from hydpy.models import {submodel}")
        options = hydpy.pub.options
        with options.parameterstep(parameterstep):
            if simulationstep is None:
                simulationstep = options.simulationstep
            else:
                simulationstep = timetools.Period(simulationstep)
            lines.append(f'\nsimulationstep("{simulationstep}")')
            lines.append(f'parameterstep("{options.parameterstep}")\n\n')
        return "\n".join(lines)

    def _get_controllines(
        self,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        simulationstep: Optional[timetools.PeriodConstrArg] = None,
        auxfiler: Optional[auxfiletools.Auxfiler] = None,
        sublevel: int = 0,
        ignore: Optional[Tuple[Type[parametertools.Parameter], ...]] = None,
    ) -> List[str]:
        if auxfiler is None:
            parameter2auxfile = None
        else:
            parameter2auxfile = auxfiler.get(self)
        lines = []
        opts = hydpy.pub.options
        with opts.parameterstep(parameterstep), opts.simulationstep(simulationstep):
            for par in self.parameters.control:
                if (ignore is None) or not isinstance(par, ignore):
                    if parameter2auxfile is not None:
                        auxfilename = parameter2auxfile.get_filename(par)
                        if auxfilename:
                            lines.append(f'{par.name}(auxfile="{auxfilename}")')
                            continue
                    lines.extend(repr(par).split("\n"))
            solver_lines = tuple(
                f"solver.{repr(par)}"
                for par in self.parameters.solver
                if exceptiontools.attrready(par, "alternative_initvalue")
            )
            if solver_lines:
                lines.append("")
            lines.extend(solver_lines)
        indent = sublevel * "    "
        return [f"{indent}{line}\n" for line in lines]

    def save_controls(
        self,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        simulationstep: Optional[timetools.PeriodConstrArg] = None,
        auxfiler: Optional[auxfiletools.Auxfiler] = None,
        filepath: Optional[str] = None,
    ) -> None:
        """Write the control parameters (and eventually some solver parameters) to a
        control file.

        Usually, a control file consists of a header (see the documentation on the
        method |Model.get_controlfileheader|) and the string representations of the
        individual |Parameter| objects handled by the `control` |SubParameters| object.

        The main functionality of method |Model.save_controls| is demonstrated in the
        documentation on method |HydPy.save_controls| of class |HydPy|, which one
        should apply to write the parameter information of complete *HydPy* projects.
        However, calling |Model.save_controls| on individual |Model| objects offers the
        advantage of choosing an arbitrary file path, as shown in the following
        example:

        >>> from hydpy.models.test_v3 import *
        >>> parameterstep("1d")
        >>> simulationstep("1h")
        >>> k(0.1)
        >>> n(3)

        >>> from hydpy import Open
        >>> with Open():
        ...     model.save_controls(filepath="otherdir/otherfile.py")
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        otherdir/otherfile.py
        ----------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.test_v3 import *
        <BLANKLINE>
        simulationstep("1h")
        parameterstep("1d")
        <BLANKLINE>
        k(0.1)
        n(3)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Method |Model.save_controls| also writes the string representations of all
        |SolverParameter| objects with non-default values into the control file:

        >>> solver.abserrormax(1e-6)
        >>> with Open():
        ...     model.save_controls(filepath="otherdir/otherfile.py")
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        otherdir/otherfile.py
        ----------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.test_v3 import *
        <BLANKLINE>
        simulationstep("1h")
        parameterstep("1d")
        <BLANKLINE>
        k(0.1)
        n(3)
        <BLANKLINE>
        solver.abserrormax(0.000001)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Without a given file path and a proper project configuration, method
        |Model.save_controls| raises the following error:

        >>> model.save_controls()
        Traceback (most recent call last):
        ...
        RuntimeError: To save the control parameters of a model to a file, its \
filename must be known.  This can be done, by passing a filename to function \
`save_controls` directly.  But in complete HydPy applications, it is usally assumed \
to be consistent with the name of the element handling the model.
        """

        def _extend_lines_submodel(
            model: Model, sublevel: int, general_methods: Set[str]
        ) -> None:
            sublevel += 1
            for name, submodel in model.find_submodels(
                include_subsubmodels=False
            ).items():
                t2n2a = importtools.SubmodelAdder.modeltype2submodelname2submodeladder
                subname = name.rpartition(".")[2]
                for modeltype in inspect.getmro(type(model)):
                    if (name2adder := t2n2a.get(modeltype)) is not None:
                        if (adder := name2adder.get(subname)) is not None:
                            break
                else:
                    assert False
                lines.append(
                    f"{(sublevel - 1) * '    '}with "
                    f"model.{adder.wrapped.__name__}({submodel}):\n"
                )
                all_methods: Set[str] = general_methods.copy()
                for method in adder.methods:
                    methodname = method.__name__
                    all_methods.add(methodname)
                    if methodname in SubmodelInterface.GENERAL_METHODS:
                        general_methods.add(methodname)
                targetparameters = set()
                for methodname in all_methods:
                    updater = getattr(submodel, methodname)
                    if isinstance(updater, importtools.TargetParameterUpdater):
                        targetparameters.add(updater.targetparameter)
                lines.extend(
                    submodel._get_controllines(  # pylint: disable=protected-access
                        parameterstep=parameterstep,
                        simulationstep=simulationstep,
                        auxfiler=auxfiler,
                        sublevel=sublevel,
                        ignore=tuple(targetparameters),
                    )
                )
                _extend_lines_submodel(
                    model=submodel, sublevel=sublevel, general_methods=general_methods
                )

        header = self.get_controlfileheader(
            parameterstep=parameterstep, simulationstep=simulationstep
        )
        lines = [header]
        lines.extend(
            self._get_controllines(
                parameterstep=parameterstep,
                simulationstep=simulationstep,
                auxfiler=auxfiler,
                sublevel=0,
            )
        )
        _extend_lines_submodel(model=self, sublevel=0, general_methods=set())
        text = "".join(lines)
        if filepath:
            with open(filepath, mode="w", encoding="utf-8") as controlfile:
                controlfile.write(text)
        else:
            filename = objecttools.devicename(self)
            if filename == "?":
                raise RuntimeError(
                    "To save the control parameters of a model to a file, its "
                    "filename must be known.  This can be done, by passing a filename "
                    "to function `save_controls` directly.  But in complete HydPy "
                    "applications, it is usally assumed to be consistent with the "
                    "name of the element handling the model."
                )
            hydpy.pub.controlmanager.save_file(filename, text)

    @abc.abstractmethod
    def simulate(self, idx: int) -> None:
        """Perform a simulation run over a single simulation time step."""

    def load_data(self, idx: int) -> None:
        """Call method |Sequences.load_data| of the attribute `sequences` of the
        current model instance and its submodels.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        if self.sequences:
            self.sequences.load_data(idx)
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.load_data(idx)

    def save_data(self, idx: int) -> None:
        """Call method |Sequences.save_data| of the attribute `sequences` of the
        current model instance and its submodels.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        if self.sequences:
            self.sequences.save_data(idx)
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.save_data(idx)

    def update_inlets(self) -> None:
        """Call all methods defined as "INLET_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(2)
        >>> class Test(AdHocModel):
        ...     INLET_METHODS = print_1, print_2
        >>> Test().update_inlets()
        1
        2

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for method in self.INLET_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def update_outlets(self) -> None:
        """Call all methods defined as "OUTLET_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(2)
        >>> class Test(AdHocModel):
        ...     OUTLET_METHODS = print_1, print_2
        >>> Test().update_outlets()
        1
        2

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for method in self.OUTLET_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def update_receivers(self, idx: int) -> None:
        """Call all methods defined as "RECEIVER_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...        print(test.idx_sim+1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(test.idx_sim+2)
        >>> class Test(AdHocModel):
        ...     RECEIVER_METHODS = print_1, print_2
        >>> test = Test()
        >>> test.update_receivers(1)
        2
        3

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        for method in self.RECEIVER_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def update_senders(self, idx: int) -> None:
        """Call all methods defined as "SENDER_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...        print(test.idx_sim+1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(test.idx_sim+2)
        >>> class Test(AdHocModel):
        ...     SENDER_METHODS = print_1, print_2
        >>> test = Test()
        >>> test.update_senders(1)
        2
        3

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        for method in self.SENDER_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def new2old(self) -> None:
        """Call method |StateSequences.new2old| of subattribute `sequences.states`.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        if self.sequences:
            self.sequences.states.new2old()

    def update_outputs(self) -> None:
        """Call method |Sequences.update_outputs| of attribute |Model.sequences|.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.sequences.update_outputs()

    @classmethod
    def get_methods(cls) -> Iterator[Type[Method]]:
        """Convenience method for iterating through all methods selected by a |Model|
        subclass.

        >>> from hydpy.models import hland_v1, ga_garto_submodel1
        >>> for method in hland_v1.Model.get_methods():
        ...     print(method.__name__)   # doctest: +ELLIPSIS
        Calc_TC_V1
        ...
        Pass_Q_V1

        >>> for method in ga_garto_submodel1.Model.get_methods():
        ...     print(method.__name__)   # doctest: +ELLIPSIS
        Set_InitialSurfaceWater_V1
        ...
        Get_SoilWaterContent_V1
        Return_RelativeMoisture_V1
        ...
        Withdraw_AllBins_V1

        Note that function |Model.get_methods| returns the "raw" |Method| objects
        instead of the modified Python or Cython functions used for performing
        calculations.
        """
        methods = set()
        if hasattr(cls, "METHOD_GROUPS"):
            for groupname in cls.METHOD_GROUPS:
                if (groupname == "ADD_METHODS") and hasattr(cls, "INTERFACE_METHODS"):
                    for method in cls.INTERFACE_METHODS:
                        if method not in methods:
                            methods.add(method)
                            yield method
                for method in getattr(cls, groupname, ()):
                    if method not in methods:
                        methods.add(method)
                        yield method

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_optional: Literal[False] = ...,
    ) -> Dict[str, Model]:
        ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_optional: Literal[True],
    ) -> Dict[str, Optional[Model]]:
        ...

    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_optional: bool = False,
        include_feedbacks: bool = False,
    ) -> Union[Dict[str, Model], Dict[str, Optional[Model]]]:
        """Find the (sub)submodel instances of the current main model instance.

        Method |Model.find_submodels| returns by default an empty dictionary if no
        submodel is available:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("lland_v1")
        >>> model.find_submodels()
        {}

        The `include_mainmodel` parameter allows the addition of the main model:

        >>> model.find_submodels(include_mainmodel=True)  # doctest: +ELLIPSIS
        {'model': <hydpy.models.lland_v1.Model ...>}

        The `include_optional` parameter allows considering prepared and unprepared
        submodels:

        >>> model.find_submodels(include_optional=True)
        {'model.aetmodel': None, 'model.soilmodel': None}
        >>> model.aetmodel = prepare_model("evap_minhas")
        >>> model.aetmodel.petmodel = prepare_model("evap_mlc")
        >>> model.aetmodel.petmodel.retmodel = prepare_model("evap_tw2002")
        >>> from pprint import pprint
        >>> pprint(model.find_submodels(include_optional=True))  # doctest: +ELLIPSIS
        {'model.aetmodel': <hydpy.models.evap_minhas.Model ...>,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.petmodel': <hydpy.models.evap_mlc.Model ...>,
         'model.aetmodel.petmodel.retmodel': <hydpy.models.evap_tw2002.Model ...>,
         'model.aetmodel.petmodel.retmodel.tempmodel': None,
         'model.aetmodel.soilwatermodel': None,
         'model.soilmodel': None}

        By default, |Model.find_submodels| does not return an additional entry when a
        main model serves as a sub-submodel:

        >>> model.aetmodel.soilwatermodel = model
        >>> model.aetmodel.soilwatermodel_is_mainmodel = True
        >>> pprint(model.find_submodels(include_optional=True))  # doctest: +ELLIPSIS
        {'model.aetmodel': <hydpy.models.evap_minhas.Model object ...>,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.petmodel': <hydpy.models.evap_mlc.Model ...>,
         'model.aetmodel.petmodel.retmodel': <hydpy.models.evap_tw2002.Model ...>,
         'model.aetmodel.petmodel.retmodel.tempmodel': None,
         'model.soilmodel': None}

        Use the `include_feedbacks` parameter to make such feedback connections
        transparent:

        >>> pprint(model.find_submodels(include_mainmodel=True,
        ...     include_optional=True, include_feedbacks=True))  # doctest: +ELLIPSIS
        {'model': <hydpy.models.lland_v1.Model ...>,
         'model.aetmodel': <hydpy.models.evap_minhas.Model ...>,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.petmodel': <hydpy.models.evap_mlc.Model ...>,
         'model.aetmodel.petmodel.retmodel': <hydpy.models.evap_tw2002.Model ...>,
         'model.aetmodel.petmodel.retmodel.tempmodel': None,
         'model.aetmodel.soilwatermodel': <hydpy.models.lland_v1.Model object ...>,
         'model.soilmodel': None}
        """

        def _find_submodels(name: str, model: Model) -> None:
            name2submodel_new = {}
            for submodelproperty in SubmodelProperty.modeltype2instance[type(model)]:
                if include_feedbacks or (
                    not getattr(model, f"{submodelproperty.name}_is_mainmodel")
                ):
                    submodel = getattr(model, submodelproperty.name)
                    if include_optional or (submodel is not None):
                        name2submodel_new[f"{name}.{submodelproperty.name}"] = submodel
            name2submodel.update(name2submodel_new)
            if include_subsubmodels:
                for subname, submodel in name2submodel_new.items():
                    if submodel not in seen:
                        seen.add(submodel)
                        _find_submodels(subname, submodel)

        seen: Set[Model] = set([self])
        name2submodel = {"model": self} if include_mainmodel else {}
        _find_submodels("model", self)
        return dict(sorted(name2submodel.items()))

    def update_parameters(self) -> None:
        """Use the control parameter values of the current model for updating its
        derived parameters and the control and derived parameters of all its submodels.

        We use the combination of |hland_v1|, |evap_aet_hbv96|, and |evap_pet_hbv96|
        used by the `LahnH` project for modelling the Dill catchment as an example:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp = prepare_full_example_2()[0]
        >>> model = hp.elements.land_dill.model

        First, all zones of the Dill catchment are either of type
        |hland_constants.FIELD| or |hland_constants.FOREST|:

        >>> model.parameters.control.zonetype
        zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST,
                 FIELD, FOREST, FIELD, FOREST)

        Hence, the |evap_control.Soil| parameter of |evap_aet_hbv96| must be |True| for
        the entire basin, as both zone types possess a soil module which
        requires soil evapotranspiration estimates:

        >>> model.aetmodel.parameters.control.soil
        soil(True)

        Second, |hland_v1| requires definitions for the zones' altitude
        (|hland_control.ZoneZ|) and determines the average basin altitude
        (|hland_derived.Z|) automatically:

        >>> model.parameters.control.zonez
        zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0)
        >>> model.parameters.derived.z
        z(4.205345)

        |evap_aet_hbv96| handles its altitude data similarly but relies on the unit 1 m
        instead of 100 m:

        >>> model.aetmodel.petmodel.parameters.control.hrualtitude
        hrualtitude(200.0, 200.0, 300.0, 300.0, 400.0, 400.0, 500.0, 500.0,
                    600.0, 600.0, 700.0, 700.0)
        >>> model.aetmodel.petmodel.parameters.derived.altitude
        altitude(420.53445)

        We now set the first zone to type |hland_constants.ILAKE| and the altitude of
        all zones to 400 m:

        >>> from hydpy.models.hland_v1 import ILAKE
        >>> model.parameters.control.zonetype[0] = ILAKE
        >>> model.parameters.control.zonez(4.0)

        |Model.update_parameters| uses the appropriate interface methods to transfer
        the updated control parameter values from the main model to all its submodels.
        So, parameter |evap_control.Soil| parameter of |evap_aet_hbv96| becomes aware
        of the introduced internal lake zone, which does not include a soil module and
        hence needs no soil evapotranspiration estimates:

        >>> model.update_parameters()
        >>> model.aetmodel.parameters.control.soil
        soil(field=True, forest=True, ilake=False)

        Additionally, |Model.update_parameters| uses method |Parameters.update| of
        class |Parameters| for updating the derived parameters |hland_derived.Z| of the
        |hland_v1| main model and |evap_derived.Altitude| of the |evap_pet_hbv96|
        submodel:

        >>> model.parameters.derived.z
        z(4.0)
        >>> model.aetmodel.petmodel.parameters.control.hrualtitude
        hrualtitude(400.0)
        >>> model.aetmodel.petmodel.parameters.derived.altitude
        altitude(400.0)
        """
        self.parameters.update()
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            if isinstance(submodel, SubmodelInterface):
                adder = submodel._submodeladder  # pylint: disable=protected-access
                if adder is not None:
                    adder.update(self, submodel)
                    submodel.update_parameters()

    # ToDo: Replace this hack with a Mypy plugin?
    def __getattr__(self, item: str) -> Any:
        assert False

    del __getattr__

    def __setattr__(self, key: str, value: Any) -> None:
        assert False

    del __setattr__

    def __str__(self) -> str:
        return self.name

    def __init_subclass__(cls) -> None:
        modulename = cls.__module__
        if not modulename.startswith("hydpy.models."):
            return
        if modulename.count(".") > 2:
            modulename = modulename.rpartition(".")[0]
        module = cast(_ModelModule, importlib.import_module(modulename))
        modelname = modulename.split(".")[-1]
        cls._NAME = modelname

        allsequences = set()
        st = sequencetools
        infos: Tuple[Tuple[Type[Any], Type[Any], Set[Any]], ...] = (
            (st.InletSequences, st.InletSequence, set()),
            (st.ReceiverSequences, st.ReceiverSequence, set()),
            (st.InputSequences, st.InputSequence, set()),
            (st.FluxSequences, st.FluxSequence, set()),
            (st.FactorSequences, st.FactorSequence, set()),
            (st.StateSequences, st.StateSequence, set()),
            (st.LogSequences, st.LogSequence, set()),
            (st.AideSequences, st.AideSequence, set()),
            (st.OutletSequences, st.OutletSequence, set()),
            (st.SenderSequences, st.SenderSequence, set()),
        )
        for method in cls.get_methods():
            for sequence in itertools.chain(
                method.REQUIREDSEQUENCES,
                method.UPDATEDSEQUENCES,
                method.RESULTSEQUENCES,
            ):
                for _, typesequence, sequences in infos:
                    if issubclass(sequence, typesequence):
                        sequences.add(sequence)
        for typesequences, _, sequences in infos:
            allsequences.update(sequences)
            classname = typesequences.__name__
            if not hasattr(module, classname):
                members = {
                    "CLASSES": variabletools.sort_variables(sequences),
                    "__doc__": f"{classname[:-9]} sequences of model {modelname}.",
                    "__module__": modulename,
                }
                setattr(module, classname, type(classname, (typesequences,), members))

        fixedparameters = set(getattr(module, "ADDITIONAL_FIXEDPARAMETERS", ()))
        controlparameters = set(getattr(module, "ADDITIONAL_CONTROLPARAMETERS", ()))
        derivedparameters = set(getattr(module, "ADDITIONAL_DERIVEDPARAMETERS", ()))
        for host in itertools.chain(cls.get_methods(), allsequences):
            fixedparameters.update(getattr(host, "FIXEDPARAMETERS", ()))
            controlparameters.update(getattr(host, "CONTROLPARAMETERS", ()))
            derivedparameters.update(getattr(host, "DERIVEDPARAMETERS", ()))
        for par in itertools.chain(
            controlparameters.copy(), derivedparameters.copy(), cls.SOLVERPARAMETERS
        ):
            fixedparameters.update(getattr(par, "FIXEDPARAMETERS", ()))
            controlparameters.update(getattr(par, "CONTROLPARAMETERS", ()))
            derivedparameters.update(getattr(par, "DERIVEDPARAMETERS", ()))
        if controlparameters and not hasattr(module, "ControlParameters"):
            module.ControlParameters = type(
                "ControlParameters",
                (parametertools.SubParameters,),
                {
                    "CLASSES": variabletools.sort_variables(controlparameters),
                    "__doc__": f"Control parameters of model {modelname}.",
                    "__module__": modulename,
                },
            )
        if derivedparameters and not hasattr(module, "DerivedParameters"):
            module.DerivedParameters = type(
                "DerivedParameters",
                (parametertools.SubParameters,),
                {
                    "CLASSES": variabletools.sort_variables(derivedparameters),
                    "__doc__": f"Derived parameters of model {modelname}.",
                    "__module__": modulename,
                },
            )
        if fixedparameters and not hasattr(module, "FixedParameters"):
            module.FixedParameters = type(
                "FixedParameters",
                (parametertools.SubParameters,),
                {
                    "CLASSES": variabletools.sort_variables(fixedparameters),
                    "__doc__": f"Fixed parameters of model {modelname}.",
                    "__module__": modulename,
                },
            )
        if cls.SOLVERPARAMETERS and not hasattr(module, "SolverParameters"):
            module.SolverParameters = type(
                "SolverParameters",
                (parametertools.SubParameters,),
                {
                    "CLASSES": variabletools.sort_variables(cls.SOLVERPARAMETERS),
                    "__doc__": f"Solver parameters of model {modelname}.",
                    "__module__": modulename,
                },
            )


class RunModel(Model):
    """Base class for |AdHocModel| and |SegmentModel| that introduces so-called "run
    methods", which need to be executed in the order of their positions in the
    |RunModel.RUN_METHODS| tuple."""

    RUN_METHODS: ClassVar[Tuple[Type[Method], ...]]
    METHOD_GROUPS = (
        "RECEIVER_METHODS",
        "INLET_METHODS",
        "RUN_METHODS",
        "ADD_METHODS",
        "OUTLET_METHODS",
        "SENDER_METHODS",
    )

    @abc.abstractmethod
    def run(self) -> None:
        """Call all methods defined as "run methods" in the defined order."""

    def simulate(self, idx: int) -> None:
        """Perform a simulation run over a single simulation time step.

        The required argument `idx` corresponds to property `idx_sim`
        (see the main documentation on class |Model|).

        You can integrate method |Model.simulate| into your workflows for
        tailor-made simulation runs.  Method |Model.simulate| is complete
        enough to allow for consecutive calls.  However, note that it
        does neither call |Model.save_data|, |Model.update_receivers|,
        nor |Model.update_senders|.  Also, one would have to reset the
        related node sequences, as done in the following example:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> model = hp.elements.land_dill.model
        >>> for idx in range(4):
        ...     model.simulate(idx)
        ...     print(hp.nodes.dill.sequences.sim)
        ...     hp.nodes.dill.sequences.sim = 0.0
        sim(11.78144)
        sim(8.902735)
        sim(7.132279)
        sim(6.018681)
        >>> hp.nodes.dill.sequences.sim.series
        InfoArray([nan, nan, nan, nan])

        The results above are identical to those of method |HydPy.simulate|
        of class |HydPy|, which is the standard method to perform simulation
        runs (except that method |HydPy.simulate| of class |HydPy| also
        performs the steps neglected by method |Model.simulate| of class
        |Model| mentioned above):

        >>> from hydpy import round_
        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> round_(hp.nodes.dill.sequences.sim.series)
        11.78144, 8.902735, 7.132279, 6.018681

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.

        .. testsetup::

            >>> from hydpy import Node, Element
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        self.load_data(idx)
        self.update_inlets()
        self.run()
        self.new2old()
        self.update_outlets()
        self.update_outputs()


class AdHocModel(RunModel):
    """Base class for models solving the underlying differential equations in an "ad
    hoc manner".

    "Ad hoc" stands for the classical approaches in hydrology to calculate individual
    fluxes separately (often sequentially) and without error control
    :cite:p:`ref-Clark2010`.
    """

    def run(self) -> None:
        """Call all methods defined as "run methods" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(2)
        >>> class Test(AdHocModel):
        ...     RUN_METHODS = print_1, print_2
        >>> Test().run()
        1
        2

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for method in self.RUN_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call


class SegmentModel(RunModel):
    """Base class for (routing) models that solve the underlying differential equations
    "segment-wise".

    "segment-wise" means that |SegmentModel| first runs the "run methods" for the
    first segment (by setting |SegmentModel.idx_segment| to zero), then for the
    second segment (by setting |SegmentModel.idx_segment| to one), and so on.
    Therefore, it requires the concrete model subclass to provide a control
    parameter named "NmbSegments".  Additionally, it requires the concrete
    model to implement a solver parameter named "NmbRuns" that defines how many
    times the "run methods" need to be (repeatedly) executed for each segment.
    See |musk_classic| and |musk_mct| as examples.
    """

    idx_segment = Idx_Segment()
    idx_run = Idx_Run()
    nmb_segments: int = 0

    def run(self) -> None:
        """Call all methods defined as "run methods" "segment-wise".

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """

        for idx_segment in range(self.parameters.control.nmbsegments.value):
            self.idx_segment = idx_segment
            for idx_run in range(self.parameters.solver.nmbruns.value):
                self.idx_run = idx_run
                for method in self.RUN_METHODS:
                    method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def run_segments(self, method: Method) -> None:
        """Run the given methods for all segments.

        Method |SegmentModel.run_segments| is mainly thought for testing purposes.
        See the documentation on method |musk_model.Calc_Discharge_V1| on how to apply
        it.
        """
        try:
            for idx in range(self.nmb_segments):
                self.idx_segment = idx
                method()
        finally:
            self.idx_segment = 0


class SolverModel(Model):
    """Base class for hydrological models, which solve ordinary differential equations
    with numerical integration algorithms."""

    PART_ODE_METHODS: ClassVar[Tuple[Type[Method], ...]]
    FULL_ODE_METHODS: ClassVar[Tuple[Type[Method], ...]]

    @abc.abstractmethod
    def solve(self) -> None:
        """Solve all `FULL_ODE_METHODS` in parallel."""


class NumConstsELS:
    """Configuration options for using the "Explicit Lobatto Sequence" implemented by
    class |ELSModel|.

    You can change the following solver options at your own risk.

    >>> from hydpy.core.modeltools import NumConstsELS
    >>> consts = NumConstsELS()

    The maximum number of Runge Kutta submethods to be applied (the higher, the better
    the theoretical accuracy, but also the worse the time spent unsuccessful when the
    theory does not apply):

    >>> consts.nmb_methods
    10

    The number of entries to handle the stages of the highest order method (must agree
    with the maximum number of methods):

    >>> consts.nmb_stages
    11

    The maximum increase of the integration step size in case of success:

    >>> consts.dt_increase
    2.0

    The maximum decrease of the integration step size in case of failure:

    >>> consts.dt_decrease
    10.0

    The Runge Kutta coefficients, one matrix for each submethod:

    >>> consts.a_coefs.shape
    (11, 12, 11)
    """

    nmb_methods: int
    nmb_stages: int
    dt_increase: float
    dt_decrease: float
    a_coeffs: numpy.ndarray

    def __init__(self):
        self.nmb_methods = 10
        self.nmb_stages = 11
        self.dt_increase = 2.0
        self.dt_decrease = 10.0
        path = os.path.join(
            conf.__path__[0], "a_coefficients_explicit_lobatto_sequence.npy"
        )
        self.a_coefs = numpy.load(path)


class NumVarsELS:
    """Intermediate results of the "Explicit Lobatto Sequence" implemented by class
    |ELSModel|.

    Class |NumVarsELS| should be of relevance for model developers, as it helps to
    evaluate how efficient newly implemented models are solved (see the documentation
    on method |ELSModel.solve| of class |ELSModel| as an example).
    """

    use_relerror: bool
    nmb_calls: int
    t0: float
    t1: float
    dt_est: float
    dt: float
    idx_method: int
    idx_stage: int
    abserror: float
    relerror: float
    last_abserror: float
    last_relerror: float
    extrapolated_abserror: float
    extrapolated_relerror: float
    f0_ready: bool

    def __init__(self):
        self.use_relerror = False
        self.nmb_calls = 0
        self.t0 = 0.0
        self.t1 = 0.0
        self.dt_est = 1.0
        self.dt = 1.0
        self.idx_method = 0
        self.idx_stage = 0
        self.abserror = 0.0
        self.relerror = 0.0
        self.last_abserror = 0.0
        self.last_relerror = 0.0
        self.extrapolated_abserror = 0.0
        self.extrapolated_relerror = 0.0
        self.f0_ready = False


class ELSModel(SolverModel):
    """Base class for hydrological models using the "Explicit Lobatto Sequence" for
    solving ordinary differential equations.

    The "Explicit Lobatto Sequence" is a variable order Runge Kutta method combining
    different Lobatto methods.  Its main idea is to first calculate a solution with a
    lower order method, then use these results to apply the next higher-order method,
    and to compare both results.  If they are close enough, the latter results are
    accepted.  If not, the next higher-order method is applied (or, if no higher-order
    method is available, the step size is decreased, and the algorithm restarts with
    the method of the lowest order).  So far, a thorough description of the algorithm
    is available in German only :cite:p:`ref-Tyralla2016`.

    Note the strengths and weaknesses of class |ELSModel| discussed in the
    documentation on method |ELSModel.solve|.  Model developers should not derive from
    class |ELSModel| when trying to implement models with a high potential for stiff
    parameterisations.  Discontinuities should be regularised, for example, by the
    "smoothing functions" provided by module |smoothtools|.  Model users should be
    careful not to define two small smoothing factors, to avoid needlessly long
    simulation times.
    """

    SOLVERSEQUENCES: ClassVar[Tuple[Type[sequencetools.DependentSequence], ...]]
    PART_ODE_METHODS: ClassVar[Tuple[Type[Method], ...]]
    FULL_ODE_METHODS: ClassVar[Tuple[Type[Method], ...]]
    METHOD_GROUPS = (
        "RECEIVER_METHODS",
        "INLET_METHODS",
        "PART_ODE_METHODS",
        "FULL_ODE_METHODS",
        "ADD_METHODS",
        "OUTLET_METHODS",
        "SENDER_METHODS",
    )
    numconsts: NumConstsELS
    numvars: NumVarsELS

    def __init__(self) -> None:
        super().__init__()
        self.numconsts = NumConstsELS()
        self.numvars = NumVarsELS()

    def simulate(self, idx: int) -> None:
        """Similar to method |Model.simulate| of class |AdHocModel| but calls method
        |ELSModel.solve| instead of |AdHocModel.run|.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.load_data(idx)
        self.update_inlets()
        self.solve()
        self.update_outlets()
        self.update_outputs()

    def solve(self) -> None:
        """Solve all `FULL_ODE_METHODS` in parallel.

        Implementing numerical integration algorithms that (hopefully) always work well
        in practice is a tricky task.  The following exhaustive examples show how well
        our "Explicit Lobatto Sequence" algorithm performs for the numerical test
        models |test_v1| and |test_v2|.  We hope to cover all possible corner cases.
        Please tell us if you find one we missed.

        First, we set the value of parameter |test_control.K| to zero, resulting in no
        changes at all and thus defining the simplest test case possible:

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.0)

        Second, we assign values to the solver parameters |test_solver.AbsErrorMax|,
        |test_solver.RelDTMin|, and |test_solver.RelDTMax| to specify the required
        numerical accuracy and the smallest and largest internal integration step size
        allowed:

        >>> solver.abserrormax(0.1)
        >>> solver.reldtmin(0.001)
        >>> solver.reldtmax(1.0)

        Additionally, we set |test_solver.RelErrorMax| to |numpy.nan|, which disables
        taking relative errors into account:

        >>> solver.relerrormax(nan)

        Calling method |ELSModel.solve| correctly calculates zero discharge
        (|test_fluxes.Q|) and thus does not change the water storage (|test_states.S|):

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(1.0)
        >>> fluxes.q
        q(0.0)

        The achieve the above result, |ELSModel| requires two function calls, one for
        the initial guess (using the Explicit Euler Method) and the other one
        (extending the Explicit Euler method to the Explicit Heun method) to confirm
        the first guess meets the required accuracy:

        >>> model.numvars.idx_method
        2
        >>> model.numvars.dt
        1.0
        >>> model.numvars.nmb_calls
        2

        With moderate changes due to setting the value of parameter |test_control.K|
        to 0.1, two method calls are still sufficient:

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

        Calculating the analytical solution shows |ELSModel| did not exceed the given
        tolerance value:

        >>> import numpy
        >>> from hydpy import round_
        >>> round_(numpy.exp(-k))
        0.904837

        After decreasing the allowed error by one order of magnitude, |ELSModel|
        requires four method calls (again, one for the first order and one for the
        second-order method, and two additional calls for the third-order method):

        >>> solver.abserrormax(0.001)
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

        After decreasing |test_solver.AbsErrorMax| by ten again, |ELSModel| needs one
        further higher-order method, which requires three additional calls, making a
        sum of seven:

        >>> solver.abserrormax(0.0001)
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

        |ELSModel| achieves even a very extreme numerical precision (just for testing,
        way beyond hydrological requirements) in one single step but now requires 29
        method calls:

        >>> solver.abserrormax(1e-12)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904837)
        >>> fluxes.q
        q(0.095163)
        >>> model.numvars.dt
        1.0
        >>> model.numvars.idx_method
        8
        >>> model.numvars.nmb_calls
        29

        With a more dynamical parameterisation, where the storage decreases by about
        40 % per time step, |ELSModel| needs seven method calls to meet a "normal"
        error tolerance:

        >>> solver.abserrormax(0.01)
        >>> k(0.5)
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
        >>> round_(numpy.exp(-k))
        0.606531

        Being an explicit integration method, the "Explicit Lobatto Sequence" can be
        inefficient for solving stiff initial value problems.  Setting |test_control.K|
        to 2.0 forces |ELSModel| to solve the problem in two substeps, requiring a
        total of 22 method calls:

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
        >>> round_(model.numvars.dt)
        0.3
        >>> model.numvars.nmb_calls
        22

        Increasing the stiffness of the initial value problem further can increase
        computation times rapidly:

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

        If we prevent |ELSModel| from compensatingf or its problems by disallowing it
        to reduce its integration step size, it does not achieve satisfying results:

        >>> solver.reldtmin(1.0)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.09672)
        >>> fluxes.q
        q(0.90328)
        >>> round_(model.numvars.dt)
        1.0
        >>> model.numvars.nmb_calls
        46

        You can restrict the allowed maximum integration step size, which can help to
        prevent from loosing to much performance due to trying to solve too stiff
        problems, repeatedly:

        >>> solver.reldtmin(0.001)
        >>> solver.reldtmax(0.25)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.016806)
        >>> fluxes.q
        q(0.983194)
        >>> round_(model.numvars.dt)
        0.25
        >>> model.numvars.nmb_calls
        33

        Alternatively, you can restrict the available number of Lobatto methods.  Using
        two methods only is an inefficient choice for the given initial value problem
        but at least solves it with the required accuracy:

        >>> solver.reldtmax(1.0)
        >>> model.numconsts.nmb_methods = 2
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.020284)
        >>> fluxes.q
        q(0.979716)
        >>> round_(model.numvars.dt)
        0.156698
        >>> model.numvars.nmb_calls
        74

        In the above examples, we control numerical accuracies based on absolute error
        estimates only via parameter |test_solver.AbsErrorMax|.  After assigning an
        actual value to parameter |test_solver.RelErrorMax|, |ELSModel| also takes
        relative errors into account.  We modify some of the above examples to show how
        this works.

        Generally, it is sufficient to meet one of both criteria.  If we repeat the
        second example with a relaxed absolute but a strict relative tolerance, we
        reproduce the original result due to our absolute criteria being the relevant
        one:

        >>> solver.abserrormax(0.1)
        >>> solver.relerrormax(0.000001)
        >>> k(0.1)
        >>> states.s(1.0)
        >>> model.solve()
        >>> states.s
        s(0.905)
        >>> fluxes.q
        q(0.095)

        The same holds for the opposite case of a strict absolute but a relaxed
        relative tolerance:

        >>> solver.abserrormax(0.000001)
        >>> solver.relerrormax(0.1)
        >>> k(0.1)
        >>> states.s(1.0)
        >>> model.solve()
        >>> states.s
        s(0.905)
        >>> fluxes.q
        q(0.095)

        Reiterating the "more dynamical parameterisation" example results in slightly
        different but also correct results:

        >>> k(0.5)
        >>> states.s(1.0)
        >>> model.solve()
        >>> states.s
        s(0.607196)
        >>> fluxes.q
        q(0.392804)

        Reiterating the stiffest example with a relative instead of an absolute error
        tolerance of 0.1 achieves higher accuracy, as to be expected due to the value
        of |test_states.S| being far below 1.0 for some time:

        >>> k(4.0)
        >>> states.s(1.0)
        >>> model.solve()
        >>> states.s
        s(0.0185)
        >>> fluxes.q
        q(0.9815)

        Besides its weaknesses with stiff problems, |ELSModel| cannot solve
        discontinuous problems well.  We use the |test_v1| example model to demonstrate
        how |ELSModel| behaves when confronted with such a problem.

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v2 import *
        >>> parameterstep()

        Everything works fine as long as the discontinuity does not affect the
        considered simulation step:

        >>> k(0.5)
        >>> solver.abserrormax(0.01)
        >>> solver.reldtmin(0.001)
        >>> solver.reldtmax(1.0)
        >>> solver.relerrormax(nan)
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

        The occurrence of a discontinuity within the simulation step often increases
        computation times more than a stiff parameterisation:

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

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.numvars.use_relerror = not modelutils.isnan(
            self.parameters.solver.relerrormax.value
        )
        self.numvars.t0, self.numvars.t1 = 0.0, 1.0
        self.numvars.dt_est = 1.0 * self.parameters.solver.reldtmax
        self.numvars.f0_ready = False
        self.reset_sum_fluxes()
        while self.numvars.t0 < self.numvars.t1 - 1e-14:
            self.numvars.last_abserror = modelutils.inf
            self.numvars.last_relerror = modelutils.inf
            self.numvars.dt = min(
                self.numvars.t1 - self.numvars.t0,
                1.0 * self.parameters.solver.reldtmax.value,
                max(self.numvars.dt_est, self.parameters.solver.reldtmin.value),
            )
            if not self.numvars.f0_ready:
                self.calculate_single_terms()
                self.numvars.idx_method = 0
                self.numvars.idx_stage = 0
                self.set_point_fluxes()
                self.set_point_states()
                self.set_result_states()
            for self.numvars.idx_method in range(1, self.numconsts.nmb_methods + 1):
                for self.numvars.idx_stage in range(1, self.numvars.idx_method):
                    self.get_point_states()
                    self.calculate_single_terms()
                    self.set_point_fluxes()
                for self.numvars.idx_stage in range(1, self.numvars.idx_method + 1):
                    self.integrate_fluxes()
                    self.calculate_full_terms()
                    self.set_point_states()
                self.set_result_fluxes()
                self.set_result_states()
                self.calculate_error()
                self.extrapolate_error()
                if self.numvars.idx_method == 1:
                    continue
                if (self.numvars.abserror <= self.parameters.solver.abserrormax) or (
                    self.numvars.relerror <= self.parameters.solver.relerrormax
                ):
                    self.numvars.dt_est = self.numconsts.dt_increase * self.numvars.dt
                    self.numvars.f0_ready = False
                    self.addup_fluxes()
                    self.numvars.t0 = self.numvars.t0 + self.numvars.dt
                    self.new2old()
                    break
                decrease_dt = self.numvars.dt > self.parameters.solver.reldtmin
                decrease_dt = decrease_dt and (
                    self.numvars.extrapolated_abserror
                    > self.parameters.solver.abserrormax
                )
                if self.numvars.use_relerror:
                    decrease_dt = decrease_dt and (
                        self.numvars.extrapolated_relerror
                        > self.parameters.solver.relerrormax
                    )
                if decrease_dt:
                    self.numvars.f0_ready = True
                    self.numvars.dt_est = self.numvars.dt / self.numconsts.dt_decrease
                    break
                self.numvars.last_abserror = self.numvars.abserror
                self.numvars.last_relerror = self.numvars.relerror
                self.numvars.f0_ready = True
            else:
                if self.numvars.dt <= self.parameters.solver.reldtmin:
                    self.numvars.f0_ready = False
                    self.addup_fluxes()
                    self.numvars.t0 = self.numvars.t0 + self.numvars.dt
                    self.new2old()
                else:
                    self.numvars.f0_ready = True
                    self.numvars.dt_est = self.numvars.dt / self.numconsts.dt_decrease
        self.get_sum_fluxes()

    def calculate_single_terms(self) -> None:
        """Apply all methods stored in the `PART_ODE_METHODS` tuple.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.25)
        >>> states.s = 1.0
        >>> model.calculate_single_terms()
        >>> fluxes.q
        q(0.25)
        """
        self.numvars.nmb_calls = self.numvars.nmb_calls + 1
        for method in self.PART_ODE_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def calculate_full_terms(self) -> None:
        """Apply all methods stored in the `FULL_ODE_METHODS` tuple.

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
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def get_point_states(self) -> None:
        """Load the states corresponding to the actual stage.

        >>> from hydpy import round_
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:4] = 0.0, 0.0, 1.0, 0.0
        >>> model.get_point_states()
        >>> round_(states.s.old)
        2.0
        >>> round_(states.s.new)
        1.0

        >>> from hydpy import reverse_model_wildcard_import, print_values
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> states.sv.old = 3.0, 3.0
        >>> states.sv.new = 3.0, 3.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._sv_points)
        >>> points[:4, 0] = 0.0, 0.0, 1.0, 0.0
        >>> points[:4, 1] = 0.0, 0.0, 2.0, 0.0
        >>> model.get_point_states()
        >>> print_values(states.sv.old)
        3.0, 3.0
        >>> print_values(states.sv.new)
        1.0, 2.0
        """
        self._get_states(self.numvars.idx_stage, "points")

    def _get_states(self, idx: int, type_: str) -> None:
        states = self.sequences.states
        for state in states:
            temp = getattr(states.fastaccess, f"_{state.name}_{type_}")
            state.new = temp[idx]

    def set_point_states(self) -> None:
        """Save the states corresponding to the actual stage.

        >>> from hydpy import print_values
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:] = 0.
        >>> model.set_point_states()
        >>> print_values(points[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> states.sv.old = 3.0, 3.0
        >>> states.sv.new = 1.0, 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._sv_points)
        >>> points[:] = 0.
        >>> model.set_point_states()
        >>> print_values(points[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_values(points[:4, 1])
        0.0, 0.0, 2.0, 0.0
        """
        self._set_states(self.numvars.idx_stage, "points")

    def set_result_states(self) -> None:
        """Save the final states of the actual method.

        >>> from hydpy import print_values
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(states.fastaccess._s_results)
        >>> results[:] = 0.0
        >>> model.set_result_states()
        >>> print_values(results[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> states.sv.old = 3.0, 3.0
        >>> states.sv.new = 1.0, 2.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(states.fastaccess._sv_results)
        >>> results[:] = 0.0
        >>> model.set_result_states()
        >>> print_values(results[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_values(results[:4, 1])
        0.0, 0.0, 2.0, 0.0
        """
        self._set_states(self.numvars.idx_method, "results")

    def _set_states(self, idx: int, type_: str) -> None:
        states = self.sequences.states
        for state in states:
            temp = getattr(states.fastaccess, f"_{state.name}_{type_}")
            temp[idx] = state.new

    def get_sum_fluxes(self) -> None:
        """Get the sum of the fluxes calculated so far.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 0.0
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> model.get_sum_fluxes()
        >>> fluxes.q
        q(1.0)

        >>> from hydpy import reverse_model_wildcard_import, print_values
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> fluxes.qv = 0.0, 0.0
        >>> numpy.asarray(fluxes.fastaccess._qv_sum)[:] = 1.0, 2.0
        >>> model.get_sum_fluxes()
        >>> fluxes.qv
        qv(1.0, 2.0)
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            flux(getattr(fluxes.fastaccess, f"_{flux.name}_sum"))

    def set_point_fluxes(self) -> None:
        """Save the fluxes corresponding to the actual stage.

        >>> from hydpy import print_values
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:] = 0.0
        >>> model.set_point_fluxes()
        >>> print_values(points[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> fluxes.qv = 1.0, 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._qv_points)
        >>> points[:] = 0.0
        >>> model.set_point_fluxes()
        >>> print_values(points[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_values(points[:4, 1])
        0.0, 0.0, 2.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_stage, "points")

    def set_result_fluxes(self) -> None:
        """Save the final fluxes of the actual method.

        >>> from hydpy import print_values
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:] = 0.0
        >>> model.set_result_fluxes()
        >>> from hydpy import round_
        >>> print_values(results[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> fluxes.qv = 1.0, 2.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._qv_results)
        >>> results[:] = 0.0
        >>> model.set_result_fluxes()
        >>> print_values(results[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_values(results[:4, 1])
        0.0, 0.0, 2.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_method, "results")

    def _set_fluxes(self, idx: int, type_: str) -> None:
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            temp = getattr(fluxes.fastaccess, f"_{flux.name}_{type_}")
            temp[idx] = flux

    def integrate_fluxes(self) -> None:
        """Perform a dot multiplication between the fluxes and the A coefficients
        associated with the different stages of the actual method.

        >>> from hydpy import print_values
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> model.numvars.idx_stage = 1
        >>> model.numvars.dt = 0.5
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:4] = 15.0, 2.0, -999.0, 0.0
        >>> model.integrate_fluxes()
        >>> from hydpy import round_
        >>> from hydpy import pub
        >>> print_values(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
        0.375, 0.125
        >>> fluxes.q
        q(2.9375)

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> model.numvars.idx_method = 2
        >>> model.numvars.idx_stage = 1
        >>> model.numvars.dt = 0.5
        >>> points = numpy.asarray(fluxes.fastaccess._qv_points)
        >>> points[:4, 0] = 1.0, 1.0, -999.0, 0.0
        >>> points[:4, 1] = 15.0, 2.0, -999.0, 0.0
        >>> model.integrate_fluxes()
        >>> print_values(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
        0.375, 0.125
        >>> fluxes.qv
        qv(0.25, 2.9375)
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            points = getattr(fluxes.fastaccess, f"_{flux.name}_points")
            coefs = self.numconsts.a_coefs[
                self.numvars.idx_method - 1,
                self.numvars.idx_stage,
                : self.numvars.idx_method,
            ]
            flux(self.numvars.dt * numpy.dot(coefs, points[: self.numvars.idx_method]))

    def reset_sum_fluxes(self) -> None:
        """Set the sum of the fluxes calculated so far to zero.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 5.0
        >>> model.reset_sum_fluxes()
        >>> fluxes.fastaccess._q_sum
        0.0

        >>> from hydpy import reverse_model_wildcard_import, print_values
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> import numpy
        >>> sums = numpy.asarray(fluxes.fastaccess._qv_sum)
        >>> sums[:] = 5.0, 5.0
        >>> model.reset_sum_fluxes()
        >>> print_values(fluxes.fastaccess._qv_sum)
        0.0, 0.0
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            if flux.NDIM:
                getattr(fluxes.fastaccess, f"_{flux.name}_sum")[:] = 0.0
            else:
                setattr(fluxes.fastaccess, f"_{flux.name}_sum", 0.0)

    def addup_fluxes(self) -> None:
        """Add up the sum of the fluxes calculated so far.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> fluxes.q(2.0)
        >>> model.addup_fluxes()
        >>> fluxes.fastaccess._q_sum
        3.0

        >>> from hydpy import reverse_model_wildcard_import, print_values
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> sums = numpy.asarray(fluxes.fastaccess._qv_sum)
        >>> sums[:] = 1.0, 2.0
        >>> fluxes.qv(3.0, 4.0)
        >>> model.addup_fluxes()
        >>> print_values(sums)
        4.0, 6.0
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            sum_ = getattr(fluxes.fastaccess, f"_{flux.name}_sum")
            sum_ += flux
            setattr(fluxes.fastaccess, f"_{flux.name}_sum", sum_)

    def calculate_error(self) -> None:
        """Estimate the numerical error based on the relevant fluxes calculated by the
        current and the last method.

        "Relevant fluxes" are those contained within the `SOLVERSEQUENCES` tuple.  If
        this tuple is empty, method |ELSModel.calculate_error| selects all flux
        sequences of the respective model with a |True| `NUMERIC` attribute.

        >>> from hydpy import round_
        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:5] = 0.0, 0.0, 3.0, 4.0, 4.0
        >>> model.numvars.use_relerror = False
        >>> model.numvars.idx_method = 3
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        1.0
        >>> model.numvars.relerror
        inf

        >>> model.numvars.use_relerror = True
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        1.0
        >>> round_(model.numvars.relerror)
        0.25

        >>> model.numvars.idx_method = 4
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        0.0
        >>> round_(model.numvars.relerror)
        0.0

        >>> model.numvars.idx_method = 1
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        0.0
        >>> model.numvars.relerror
        inf

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v3 import *
        >>> parameterstep()
        >>> n(2)
        >>> model.numvars.use_relerror = True
        >>> model.numvars.idx_method = 3
        >>> results = numpy.asarray(fluxes.fastaccess._qv_results)
        >>> results[:5, 0] = 0.0, 0.0, -4.0, -2.0, -2.0
        >>> results[:5, 1] = 0.0, 0.0, -8.0, -4.0, -4.0
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        4.0
        >>> round_(model.numvars.relerror)
        1.0

        >>> model.numvars.idx_method = 4
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        0.0
        >>> round_(model.numvars.relerror)
        0.0

        >>> model.numvars.idx_method = 1
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        0.0
        >>> model.numvars.relerror
        inf
        """
        self.numvars.abserror = 0.0
        if self.numvars.use_relerror:
            self.numvars.relerror = 0.0
        else:
            self.numvars.relerror = numpy.inf
        fluxes = self.sequences.fluxes
        solversequences = self.SOLVERSEQUENCES
        for flux in fluxes.numericsequences:
            if solversequences and not isinstance(flux, solversequences):
                continue
            results = getattr(fluxes.fastaccess, f"_{flux.name}_results")
            absdiff = numpy.abs(
                results[self.numvars.idx_method] - results[self.numvars.idx_method - 1]
            )
            try:
                maxdiff = numpy.max(absdiff)
            except ValueError:
                continue
            self.numvars.abserror = max(self.numvars.abserror, maxdiff)
            if self.numvars.use_relerror:
                idxs = results[self.numvars.idx_method] != 0.0
                if numpy.any(idxs):
                    reldiff = absdiff[idxs] / results[self.numvars.idx_method][idxs]
                else:
                    reldiff = numpy.inf
                self.numvars.relerror = max(
                    self.numvars.relerror, numpy.max(numpy.abs(reldiff))
                )

    def extrapolate_error(self) -> None:
        """Estimate the numerical error expected when applying all methods available
        based on the results of the current and the last method.

        Note that you cannot apply this extrapolation strategy to the first method.  If
        the current method is the first one, method |ELSModel.extrapolate_error|
        returns `-999.9`:

         >>> from hydpy.models.test_v1 import *
         >>> parameterstep()
         >>> model.numvars.use_relerror = False
         >>> model.numvars.abserror = 0.01
         >>> model.numvars.last_abserror = 0.1
         >>> model.numvars.idx_method = 10
         >>> model.extrapolate_error()
         >>> from hydpy import round_
         >>> round_(model.numvars.extrapolated_abserror)
         0.01
         >>> model.numvars.extrapolated_relerror
         inf

         >>> model.numvars.use_relerror = True
         >>> model.numvars.relerror = 0.001
         >>> model.numvars.last_relerror = 0.01
         >>> model.extrapolate_error()
         >>> round_(model.numvars.extrapolated_abserror)
         0.01
         >>> round_(model.numvars.extrapolated_relerror)
         0.001

         >>> model.numvars.idx_method = 9
         >>> model.extrapolate_error()
         >>> round_(model.numvars.extrapolated_abserror)
         0.001
         >>> round_(model.numvars.extrapolated_relerror)
         0.0001

         >>> model.numvars.relerror = inf
         >>> model.extrapolate_error()
         >>> round_(model.numvars.extrapolated_relerror)
         inf

         >>> model.numvars.abserror = 0.0
         >>> model.extrapolate_error()
         >>> round_(model.numvars.extrapolated_abserror)
         0.0
         >>> round_(model.numvars.extrapolated_relerror)
         0.0
        """
        if self.numvars.abserror <= 0.0:
            self.numvars.extrapolated_abserror = 0.0
            self.numvars.extrapolated_relerror = 0.0
        else:
            if self.numvars.idx_method > 2:
                self.numvars.extrapolated_abserror = modelutils.exp(
                    modelutils.log(self.numvars.abserror)
                    + (
                        modelutils.log(self.numvars.abserror)
                        - modelutils.log(self.numvars.last_abserror)
                    )
                    * (self.numconsts.nmb_methods - self.numvars.idx_method)
                )
            else:
                self.numvars.extrapolated_abserror = -999.9
            if self.numvars.use_relerror:
                if self.numvars.idx_method > 2:
                    if modelutils.isinf(self.numvars.relerror):
                        self.numvars.extrapolated_relerror = modelutils.inf
                    else:
                        self.numvars.extrapolated_relerror = modelutils.exp(
                            modelutils.log(self.numvars.relerror)
                            + (
                                modelutils.log(self.numvars.relerror)
                                - modelutils.log(self.numvars.last_relerror)
                            )
                            * (self.numconsts.nmb_methods - self.numvars.idx_method)
                        )
                else:
                    self.numvars.extrapolated_relerror = -999.9
            else:
                self.numvars.extrapolated_relerror = modelutils.inf


class PredefinedMethod2Argument(TypedDict, total=False):
    """Dictionary for passing arguments from main models to sub-submodels if the
    submodel does not override the related "general" interface methods for transfering
    parameter values from main models to submodels."""

    prepare_nmbzones: int
    prepare_zonetypes: VectorInputInt
    prepare_subareas: VectorInputFloat
    prepare_elevations: VectorInputFloat


class SubmodelInterface(Model, abc.ABC):
    """Base class for defining interfaces for submodels."""

    INTERFACE_METHODS: ClassVar[Tuple[Type[Method], ...]]
    GENERAL_METHODS: Tuple[str, ...] = (
        "prepare_nmbzones",
        "prepare_zonetypes",
        "prepare_subareas",
        "prepare_elevations",
    )
    _submodeladder: Optional[importtools.SubmodelAdder]
    predefinedmethod2argument: PredefinedMethod2Argument

    def __init__(self) -> None:
        super().__init__()
        self._submodeladder = None
        self.predefinedmethod2argument = {}

    @property
    @abc.abstractmethod
    def typeid(self) -> int:
        """Type identifier that we use for differentiating submodels that target the
        same process group (e.g. infiltration) but follow different interfaces.

        For `Submodel_V1`, |SubmodelInterface.typeid| is 1, for `Submodel_V2` 2, and so
        on.

        We prefer using |SubmodelInterface.typeid| over the standard |isinstance|
        checks in model equations as it allows releasing Python's Globel Interpreter
        Lock in Cython.
        """

    @staticmethod
    @contextlib.contextmanager
    def share_configuration(  # pylint: disable=unused-argument
        sharable_configuration: SharableConfiguration,
    ) -> Generator[None, None, None]:
        """Share class-level configurations between a main model and a submodel
        temporarily.

        The default implementation of method |SubmodelInterface.share_configuration|
        does nothing.  Submodels can overwrite it to adjust their classes to the
        current main model during initialisation.
        """
        yield

    def add_mainmodel_as_subsubmodel(  # pylint: disable=unused-argument
        self, mainmodel: Model
    ) -> bool:
        """If appropriate, add the given main model as a sub-submodel of the current
        submodel.

        The default implementation of method
        |SubmodelInterface.add_mainmodel_as_subsubmodel| just returns |False|.
        Submodels can overwrite it to enable them to query data from their main models
        actively.  If a submodel accepts a main model as a sub-submodel, it must return
        |True|; otherwise, |False|.
        """
        return False

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place.

        If a submodel does not work with a variable number of zones, it probably must
        not override |SubmodelInterface.prepare_nmbzones|.  Then, the default behaviour
        applies, where |SubmodelInterface.prepare_nmbzones| stores the given number of
        zones in the |SubmodelInterface.predefinedmethod2argument| dictionary.  There,
        it is available to eventual sub-submodels:

        >>> from hydpy.core.modeltools import SubmodelInterface
        >>> from hydpy.core.testtools import make_abc_testable
        >>> si = make_abc_testable(SubmodelInterface)()
        >>> si.prepare_nmbzones(3)
        >>> si.predefinedmethod2argument
        {'prepare_nmbzones': 3}
        """
        self.predefinedmethod2argument["prepare_nmbzones"] = nmbzones

    def prepare_zonetypes(self, zonetypes: Sequence[int]) -> None:
        """Set the types (usually land cover types) of the individual zones.

        The explanation on method |SubmodelInterface.prepare_nmbzones| also holds for
        the default behaviour of method |SubmodelInterface.prepare_zonetypes|:

        >>> from hydpy.core.modeltools import SubmodelInterface
        >>> from hydpy.core.testtools import make_abc_testable
        >>> si = make_abc_testable(SubmodelInterface)()
        >>> si.prepare_zonetypes([1, 2])
        >>> si.predefinedmethod2argument
        {'prepare_zonetypes': [1, 2]}
        """
        self.predefinedmethod2argument["prepare_zonetypes"] = zonetypes

    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km².

        The explanation on method |SubmodelInterface.prepare_nmbzones| also holds for
        the default behaviour of method |SubmodelInterface.prepare_subareas|:

        >>> from hydpy.core.modeltools import SubmodelInterface
        >>> from hydpy.core.testtools import make_abc_testable
        >>> si = make_abc_testable(SubmodelInterface)()
        >>> si.prepare_subareas([1.0, 2.0])
        >>> si.predefinedmethod2argument
        {'prepare_subareas': [1.0, 2.0]}
        """
        self.predefinedmethod2argument["prepare_subareas"] = subareas

    def prepare_elevations(self, elevations: Sequence[float]) -> None:
        """Set the elevations of the individual zones in m.

        The explanation on method |SubmodelInterface.prepare_nmbzones| also holds for
        the default behaviour of method |SubmodelInterface.prepare_elevations|:

        >>> from hydpy.core.modeltools import SubmodelInterface
        >>> from hydpy.core.testtools import make_abc_testable
        >>> si = make_abc_testable(SubmodelInterface)()
        >>> si.prepare_elevations([1.0, 2.0])
        >>> si.predefinedmethod2argument
        {'prepare_elevations': [1.0, 2.0]}
        """
        self.predefinedmethod2argument["prepare_elevations"] = elevations


class Submodel:
    """Base class for implementing "submodels" that serve to deal with (possibly
    complicated) general mathematical algorithms (e.g. root-finding algorithms) within
    hydrological model methods.


    You might find class |Submodel| useful when trying to implement algorithms
    requiring some interaction with the respective model without any Python overhead.
    See the modules |roottools| and `rootutils` as an example, implementing Python
    interfaces and Cython implementations of a root-finding algorithms, respectively.
    """

    METHODS: ClassVar[Tuple[Type[Method], ...]]
    CYTHONBASECLASS: ClassVar[Type]
    PYTHONCLASS: ClassVar[Type]
    name: ClassVar[str]
    _cysubmodel: object

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.lower()

    def __init__(self, model: Model) -> None:
        if model.cymodel:
            self._cysubmodel = getattr(model.cymodel, self.name)
        else:
            self._cysubmodel = self.PYTHONCLASS()
            for idx, methodtype in enumerate(self.METHODS):
                setattr(
                    self._cysubmodel,
                    f"method{idx}",
                    getattr(model, methodtype.__name__.lower()),
                )
