"""This module provides features for applying and implementing hydrological models."""

# import...
# ...from standard library
from __future__ import annotations
import abc
import collections
import contextlib
import copy
import functools
import importlib
import inspect
import itertools
import os
import runpy
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

# from hydpy.auxs import roottools  # actual import below

if TYPE_CHECKING:
    from hydpy.core import masktools
    from hydpy.core import selectiontools
    from hydpy.auxs import interptools
    from hydpy.cythons import interfaceutils


TypeModel_co = TypeVar("TypeModel_co", bound="Model", covariant=True)
TypeModel_contra = TypeVar("TypeModel_contra", bound="Model", contravariant=True)
TypeSubmodelInterface = TypeVar("TypeSubmodelInterface", bound="SubmodelInterface")


class _ModelModule(types.ModuleType):
    ControlParameters: type[parametertools.SubParameters]
    DerivedParameters: type[parametertools.SubParameters]
    FixedParameters: type[parametertools.SubParameters]
    SolverParameters: type[parametertools.SubParameters]


class Method:
    """Base class for defining (hydrological) calculation methods."""

    SUBMODELINTERFACES: ClassVar[tuple[type[SubmodelInterface], ...]]
    SUBMETHODS: tuple[type[Method], ...] = ()
    CONTROLPARAMETERS: tuple[
        type[parametertools.Parameter | interptools.BaseInterpolator], ...
    ] = ()
    DERIVEDPARAMETERS: tuple[type[parametertools.Parameter], ...] = ()
    FIXEDPARAMETERS: tuple[type[parametertools.Parameter], ...] = ()
    SOLVERPARAMETERS: tuple[type[parametertools.Parameter], ...] = ()
    REQUIREDSEQUENCES: tuple[type[sequencetools.Sequence_], ...] = ()
    UPDATEDSEQUENCES: tuple[type[sequencetools.Sequence_], ...] = ()
    RESULTSEQUENCES: tuple[type[sequencetools.Sequence_], ...] = ()

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


class SetAutoMethod(Method):
    """Base class for defining setter methods that also use the given data to calculate
    other properties.

    |SetAutoMethod| calls its submethods in the specified order.  If, for example, the
    first two submethods are setters, it requires precisely two parameter values.  It
    passes the first value to the first setter and the second value to the second
    setter. After that, it executes the remaining methods without exchanging any data.
    """

    @classmethod
    def __call__(cls, model: Model, *values) -> None:
        for method, value in zip(cls.SUBMETHODS, values):
            method.__call__(model, value)
        for method in cls.SUBMETHODS[len(values) :]:
            method.__call__(model)


class ReusableMethod(Method):
    """Base class for defining methods that need not or must not be called multiple
    times for the same simulation step.

    |ReusableMethod| helps to implement "sharable" submodels, of which single instances
    can be used by multiple main model instances.  See |SharableSubmodelInterface| for
    further information.
    """

    REUSEMARKER: str
    """Name of an additional model attribute for marking if the respective method has 
    already been called and should not be called again for the same simulation step and 
    its results can be reused."""

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.REUSEMARKER = f"__hydpy_reuse_{cls.__name__.lower()}__"

    @classmethod
    def call_reusablemethod(cls, model: Model, *args, **kwargs) -> None:
        """Execute the "normal" model-specific `__call__` method only when indicated by
        the |ReusableMethod.REUSEMARKER| attribute and update this attribute when
        necessary."""
        if not getattr(model, cls.REUSEMARKER):
            cls.__call__(model, *args, **kwargs)
            setattr(model, cls.REUSEMARKER, True)


abstractmodelmethods: set[Callable[..., Any]] = set()


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


class _SubmodelPropertyBase(Generic[TypeSubmodelInterface]):
    interfaces: tuple[type[TypeSubmodelInterface], ...]

    _CYTHON_PYTHON_SUBMODEL_ERROR_MESSAGE: Final = (
        "The main model is initialised in Cython mode, but the submodel is "
        "initialised in pure Python mode so that the main model's cythonized methods "
        "could apply the submodel's methods."
    )

    def _check_submodel_follows_interface(
        self, submodel: TypeSubmodelInterface
    ) -> None:
        if not isinstance(submodel, self.interfaces):
            interfacenames = (i.__name__ for i in self.interfaces)
            raise ValueError(
                f"The given submodel is not an instance of any of the following "
                f"supported interfaces: {objecttools.enumeration(interfacenames)}."
            )

    def _find_first_suitable_interface(
        self, submodel: TypeSubmodelInterface
    ) -> type[SubmodelInterface]:
        for interface in self.interfaces:
            if isinstance(submodel, interface):
                return interface
        interfacenames = (i.__name__ for i in self.interfaces)
        raise ValueError(
            f"The given submodel is not an instance of any of the following supported "
            f"interfaces: {objecttools.enumeration(interfacenames)}."
        )


class SubmodelProperty(_SubmodelPropertyBase[TypeSubmodelInterface]):
    """Descriptor for submodel attributes.

    |SubmodelProperty| instances link main models and their submodels.  They follow the
    attribute convention described in the documentation on class |SubmodelInterface|.
    Behind the scenes, they build the required connections both on the Python and the
    Cython level and perform some type-related tests (to avoid errors due to selecting
    submodels following the wrong interfaces).

    We prepare the main model and its submodel in Cython and pure Python mode to test
    that |SubmodelProperty| works for all possible combinations:

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
    RuntimeError: While trying to assign submodel `ga_garto_submodel1` to property \
`soilmodel` of the main model `lland`, the following error occurred: The main model \
is initialised in Cython mode, but the submodel is initialised in pure Python mode so \
that the main model's cythonized methods could apply the submodel's methods.

    Disconnecting a submodel from its main model works by assigning |None| as well as
    using the `del` statement:

    >>> mainmodel_python.soilmodel = None
    >>> mainmodel_python.soilmodel

    >>> del mainmodel_cython.soilmodel
    >>> mainmodel_cython.soilmodel
    >>> mainmodel_cython.cymodel.get_soilmodel()

    Trying to assign an unsuitable submodel results in the following error:

    >>> mainmodel_python.soilmodel = mainmodel_python
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign submodel `lland` to property `soilmodel` of \
the main model `lland`, the following error occurred: The given submodel is not an \
instance of any of the following supported interfaces: SoilModel_V1.

    The automatically generated docstrings list the supported interfaces:

    >>> print(type(mainmodel_python).soilmodel.__doc__)
    Optional submodel that complies with the following interface: SoilModel_V1.
    """

    name: str
    """The addressed submodels' group name."""
    interfaces: tuple[type[TypeSubmodelInterface], ...]
    """The supported interfaces."""
    optional: Final[bool]
    """Flag indicating whether a submodel is optional or strictly required."""
    sidemodel: Final[bool]
    """Flag indicating whether the handled submodel is more a "side model" than a 
    submodel.  Usually, two models consider each other as side models if they are 
    "real" submodels of a third model but need direct references."""

    __hydpy_modeltype2instance__: ClassVar[
        collections.defaultdict[type[Model], list[SubmodelProperty[Any]]]
    ] = collections.defaultdict(list)

    def __init__(
        self,
        *interfaces: type[TypeSubmodelInterface],
        optional: bool = False,
        sidemodel: bool = False,
    ) -> None:
        self.interfaces = tuple(interfaces)
        self.optional = optional
        self.sidemodel = sidemodel
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

    def __set_name__(self, owner: type[Model], name: str) -> None:
        self.name = name
        self.__hydpy_modeltype2instance__[owner].append(self)

    @overload
    def __get__(self, obj: None, objtype: type[Model] | None) -> Self: ...

    @overload
    def __get__(
        self, obj: Model, objtype: type[Model] | None
    ) -> TypeSubmodelInterface | None: ...

    def __get__(
        self, obj: Model | None, objtype: type[Model] | None = None
    ) -> Self | TypeSubmodelInterface | None:
        if obj is None:
            return self
        return vars(obj).get(self.name, None)

    def __set__(self, obj: Model, value: TypeSubmodelInterface | None) -> None:
        try:
            if value is None:
                self.__delete__(obj)
            else:
                self._check_submodel_follows_interface(value)
                vars(obj)[self.name] = value
                if obj.cymodel is not None:
                    if value.cymodel is None:
                        raise RuntimeError(self._CYTHON_PYTHON_SUBMODEL_ERROR_MESSAGE)
                    getattr(obj.cymodel, f"set_{self.name}")(value.cymodel)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to assign submodel `{value}` to property `{self.name}` "
                f"of the main model `{obj.name}`"
            )

    def __delete__(self, obj: Model) -> None:
        vars(obj)[self.name] = None
        if obj.cymodel is not None:
            getattr(obj.cymodel, f"set_{self.name}")(None)


class SubmodelsProperty(_SubmodelPropertyBase[TypeSubmodelInterface]):
    """Descriptor for handling multiple submodels that follow defined interfaces.

    |SubmodelsProperty| supports the `len` operator and is iterable and indexable:

    >>> from hydpy import prepare_model
    >>> main = prepare_model("sw1d_channel")
    >>> sub1 = prepare_model("sw1d_q_in")
    >>> sub2 = prepare_model("sw1d_lias")

    >>> from hydpy.core.modeltools import SubmodelsProperty
    >>> assert isinstance(type(main).routingmodels, SubmodelsProperty)

    >>> main.routingmodels.append_submodel(submodel=sub1, typeid=1)
    >>> main.routingmodels.append_submodel(submodel=sub2, typeid=1)
    >>> len(main.routingmodels)
    2
    >>> for submodel in main.routingmodels:
    ...     print(submodel.name)
    sw1d_q_in
    sw1d_lias
    >>> main.routingmodels[0] is sub1
    True
    >>> main.routingmodels[1] is sub2
    True
    """

    name: str
    """The addressed submodels' group name."""
    interfaces: tuple[type[TypeSubmodelInterface], ...]
    """The supported interfaces."""
    sidemodels: bool
    """Flag indicating whether the handled submodel is more a "side model" than a 
    submodel.  Usually, two models consider each other as side models if they are 
    "real" submodels of a third model but need direct references."""

    __hydpy_modeltype2instance__: ClassVar[
        collections.defaultdict[type[Model], list[SubmodelsProperty[Any]]]
    ] = collections.defaultdict(list)
    __hydpy_mainmodel2submodels__: collections.defaultdict[
        Model, list[TypeSubmodelInterface | None]
    ]

    _mainmodel: Model | None
    _mainmodel2numbersubmodels: collections.defaultdict[Model, int]
    _mainmodel2submodeltypeids: collections.defaultdict[Model, list[int]]

    def __set_name__(self, owner: type[Model], name: str) -> None:
        self.name = name
        self.__hydpy_modeltype2instance__[owner].append(self)

    def __init__(
        self, *interfaces: type[TypeSubmodelInterface], sidemodels: bool = False
    ) -> None:
        self.interfaces = tuple(interfaces)
        self.sidemodels = sidemodels
        self.__hydpy_mainmodel2submodels__ = collections.defaultdict(list)
        self._mainmodel2numbersubmodels = collections.defaultdict(int)
        self._mainmodel2submodeltypeids = collections.defaultdict(list)
        interfacenames = (i.__name__ for i in self.interfaces)
        suffix = "s" if len(interfaces) > 1 else ""
        self.__doc__ = (
            f"Vector of submodels that comply with the following interface{suffix}: "
            f"{objecttools.enumeration(interfacenames, conjunction='or')}."
        )

    def __get__(self, obj: Model | None, objtype: type[Model] | None = None) -> Self:
        if obj is None:
            return self
        try:
            self._mainmodel = obj
            return copy.copy(self)
        finally:
            self._mainmodel = None

    @property
    def number(self) -> int:
        """The maximum number of handled submodels.

        Initially, the maximum number of submodels is zero:

        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("sw1d_channel")
        >>> model.storagemodels.number
        0
        >>> model.storagemodels.submodels
        ()
        >>> model.storagemodels.typeids
        ()

        Setting it to another value automatically prepares |SubmodelsProperty.typeids|
        and |SubmodelsProperty.submodels|:

        >>> model.storagemodels.number = 2
        >>> model.storagemodels.number
        2
        >>> model.storagemodels.typeids
        (0, 0)
        >>> model.storagemodels.submodels
        (None, None)

        When working in Cython mode, property |SubmodelsProperty.number| also prepares
        the analogue vectors of the cythonized model:

        >>> with pub.options.usecython(True):
        ...     model = prepare_model("sw1d_channel")
        >>> model.storagemodels.number
        0
        >>> model.storagemodels.submodels
        ()
        >>> model.storagemodels.typeids
        ()

        >>> model.storagemodels.number = 2
        >>> model.storagemodels.number
        2
        >>> model.storagemodels.submodels
        (None, None)
        >>> model.storagemodels.typeids
        (0, 0)
        >>> model.cymodel.storagemodels._get_number()
        2
        >>> model.cymodel.storagemodels._get_typeid(0)
        0
        >>> model.cymodel.storagemodels._get_submodel(0)
        """
        assert (model := self._mainmodel) is not None
        return self._mainmodel2numbersubmodels[model]

    @number.setter
    def number(self, number: int) -> None:
        if number != self.number:
            assert (model := self._mainmodel) is not None
            self._mainmodel2numbersubmodels[model] = number
            self.__hydpy_mainmodel2submodels__[model] = [None for _ in range(number)]
            self._mainmodel2submodeltypeids[model] = number * [0]
            if (cymodel := model.cymodel) is not None:
                cyprop: interfaceutils.SubmodelsProperty = getattr(cymodel, self.name)
                cyprop.set_number(number)

    def put_submodel(
        self, submodel: TypeSubmodelInterface, typeid: int, position: int
    ) -> None:
        """Put a submodel and its relevant type ID to the given position.

        We prepare the main model and its submodel in Cython and pure Python mode to
        test that |SubmodelsProperty.put_submodel| works for all possible combinations:

        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     main_py = prepare_model("sw1d_channel")
        ...     sub_py = prepare_model("sw1d_storage")
        >>> with pub.options.usecython(True):
        ...     main_cy = prepare_model("sw1d_channel")
        ...     sub_cy = prepare_model("sw1d_storage")

        For two pure Python models, there is no need to bother with synchronising
        cythonized models:

        >>> main_py.storagemodels.number = 2
        >>> main_py.storagemodels.put_submodel(submodel=sub_py, typeid=1, position=0)
        >>> assert main_py.storagemodels.typeids[0] == 1
        >>> assert main_py.storagemodels.submodels[0] is sub_py
        >>> assert main_py.storagemodels.typeids[1] == 0
        >>> assert main_py.storagemodels.submodels[1] is None

        If both models are initialised in Cython mode, |SubmodelsProperty.put_submodel|
        updates |SubmodelsProperty.typeids| and |SubmodelsProperty.submodels| as well
        as the corresponding vectors of the cythonized models:

        >>> main_cy.storagemodels.number = 2
        >>> main_cy.storagemodels.put_submodel(submodel=sub_cy, typeid=1, position=0)
        >>> assert main_cy.storagemodels.typeids[0] == 1
        >>> assert main_cy.cymodel.storagemodels._get_typeid(0) == 1
        >>> assert main_cy.storagemodels.submodels[0] is sub_cy
        >>> assert main_cy.cymodel.storagemodels._get_submodel(0) is sub_cy.cymodel
        >>> assert main_cy.storagemodels.typeids[1] == 0
        >>> assert main_cy.cymodel.storagemodels._get_typeid(1) == 0
        >>> assert main_cy.storagemodels.submodels[1] is None
        >>> assert main_cy.cymodel.storagemodels._get_submodel(1) is None

        Connecting a pure Python mode main model with a Cython mode submodel causes no
        harm:

        >>> main_py.storagemodels.number = 0
        >>> main_py.storagemodels.number = 2
        >>> main_py.storagemodels.put_submodel(submodel=sub_cy, typeid=1, position=0)
        >>> assert main_py.storagemodels.typeids[0] == 1
        >>> assert main_py.storagemodels.submodels[0] is sub_cy
        >>> assert main_py.storagemodels.typeids[1] == 0
        >>> assert main_py.storagemodels.submodels[1] is None

        However, connecting a Cython mode main model with a pure Python mode submodel
        would result in erroneous calculations and thus raises the following error:

        >>> main_cy.storagemodels.number = 0
        >>> main_cy.storagemodels.number = 2
        >>> main_cy.storagemodels.put_submodel(submodel=sub_py, typeid=1, position=0)
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to put submodel `sw1d_storage` to position `0` of \
property `storagemodels` of the main model `sw1d_channel`, the following error \
occurred: The main model is initialised in Cython mode, but the submodel is \
initialised in pure Python mode so that the main model's cythonized methods could \
apply the submodel's methods.
        >>> assert main_cy.storagemodels.typeids[0] == 0
        >>> assert main_cy.cymodel.storagemodels._get_typeid(0) == 0
        >>> assert main_cy.storagemodels.submodels[0] is None
        >>> assert main_cy.cymodel.storagemodels._get_submodel(0) is None
        >>> assert main_cy.storagemodels.typeids[1] == 0
        >>> assert main_cy.cymodel.storagemodels._get_typeid(1) == 0
        >>> assert main_cy.storagemodels.submodels[1] is None
        >>> assert main_cy.cymodel.storagemodels._get_submodel(1) is None

        Method |SubmodelsProperty.put_submodel| checks if the given submodel follows
        at least one supported interface:

        >>> sub_py = prepare_model("sw1d_lias")
        >>> main_py.storagemodels.number = 0
        >>> main_py.storagemodels.number = 2
        >>> main_py.storagemodels.put_submodel(submodel=sub_py, typeid=1, position=0)
        Traceback (most recent call last):
        ...
        ValueError: While trying to put submodel `sw1d_lias` to position `0` of \
property `storagemodels` of the main model `sw1d_channel`, the following error \
occurred: The given submodel is not an instance of any of the following supported \
interfaces: StorageModel_V1.
        >>> assert main_py.storagemodels.typeids[0] == 0
        >>> assert main_py.storagemodels.submodels[0] is None
        >>> assert main_py.storagemodels.typeids[1] == 0
        >>> assert main_py.storagemodels.submodels[1] is None
        """
        assert (mainmodel := self._mainmodel) is not None
        try:
            self._check_submodel_follows_interface(submodel)
            if (cymain := mainmodel.cymodel) is not None:
                if (cysub := submodel.cymodel) is None:
                    raise RuntimeError(self._CYTHON_PYTHON_SUBMODEL_ERROR_MESSAGE)
                cyprop: interfaceutils.SubmodelsProperty = getattr(cymain, self.name)
                cyprop.put_submodel(submodel=cysub, typeid=typeid, position=position)
            self.__hydpy_mainmodel2submodels__[mainmodel][position] = submodel
            self._mainmodel2submodeltypeids[mainmodel][position] = typeid
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to put submodel `{submodel}` to position `{position}` "
                f"of property `{self.name}` of the main model `{mainmodel}`"
            )

    def delete_submodel(self, position: int) -> None:
        """Delete the submodel at the given position.

        We prepare the main model and its submodel in Cython and pure Python mode to
        test that |SubmodelsProperty.delete_submodel| works both in Cython and pure
        Python Cython mode:

        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     main_py = prepare_model("sw1d_channel")
        ...     sub_py = prepare_model("sw1d_storage")
        >>> with pub.options.usecython(True):
        ...     main_cy = prepare_model("sw1d_channel")
        ...     sub_cy = prepare_model("sw1d_storage")

        In pure Python mode, |SubmodelsProperty.delete_submodel| resets the entry in
        the submodel vector to |None| and the type ID to zero:

        >>> main_py.storagemodels.number = 3
        >>> main_py.storagemodels.put_submodel(submodel=sub_py, typeid=1, position=1)
        >>> assert main_py.storagemodels.typeids[1] == 1
        >>> assert main_py.storagemodels.submodels[1] is sub_py

        >>> main_py.storagemodels.delete_submodel(position=1)
        >>> assert main_py.storagemodels.typeids[1] == 0
        >>> assert main_py.storagemodels.submodels[1] is None

        In Cython mode, |SubmodelsProperty.delete_submodel| does the same for the
        analogue C vectors:

        >>> main_cy.storagemodels.number = 3
        >>> main_cy.storagemodels.put_submodel(submodel=sub_cy, typeid=1, position=1)
        >>> assert main_cy.storagemodels.typeids[1] == 1
        >>> assert main_cy.cymodel.storagemodels._get_typeid(1) == 1
        >>> assert main_cy.storagemodels.submodels[1] is sub_cy
        >>> assert main_cy.cymodel.storagemodels._get_submodel(1) is sub_cy.cymodel

        >>> main_cy.storagemodels.delete_submodel(position=1)
        >>> assert main_cy.storagemodels.typeids[1] == 0
        >>> assert main_cy.cymodel.storagemodels._get_typeid(1) == 0
        >>> assert main_cy.storagemodels.submodels[1] is None
        >>> assert main_cy.cymodel.storagemodels._get_submodel(1) is None

        Calling |SubmodelsProperty.delete_submodel| for a position with an existing
        submodel does not raise a warning or error:

        >>> main_cy.storagemodels.delete_submodel(position=1)

        Potential errors are reported like this:

        >>> main_cy.storagemodels.delete_submodel(position=3)
        Traceback (most recent call last):
        ...
        IndexError: While trying to delete a submodel at position `3` of property \
`storagemodels` of the main model `sw1d_channel`, the following error occurred: list \
assignment index out of range
        """
        assert (mainmodel := self._mainmodel) is not None
        try:
            self.__hydpy_mainmodel2submodels__[mainmodel][position] = None
            self._mainmodel2submodeltypeids[mainmodel][position] = 0
            if (cymain := mainmodel.cymodel) is not None:
                cyprop: interfaceutils.SubmodelsProperty = getattr(cymain, self.name)
                cyprop.put_submodel(submodel=None, typeid=0, position=position)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to delete a submodel at position `{position}` of "
                f"property `{self.name}` of the main model `{mainmodel}`"
            )

    def append_submodel(
        self, submodel: TypeSubmodelInterface, typeid: int | None = None
    ) -> None:
        """Append a submodel and its relevant type ID to the already available ones.

        We prepare the main model and its submodel in Cython and pure Python mode to
        test that |SubmodelsProperty.append_submodel| works for all possible
        combinations:

        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     main_py = prepare_model("sw1d_channel")
        ...     sub_py = prepare_model("sw1d_storage")
        >>> with pub.options.usecython(True):
        ...     main_cy = prepare_model("sw1d_channel")
        ...     sub_cy = prepare_model("sw1d_storage")

        For two pure Python models, there is no need to bother with synchronising
        cythonized models:

        >>> main_py.storagemodels.append_submodel(submodel=sub_py, typeid=1)
        >>> assert main_py.storagemodels.number == 1
        >>> assert main_py.storagemodels.typeids[0] == 1
        >>> assert main_py.storagemodels.submodels[0] is sub_py

        If both models are initialised in Cython mode,
        |SubmodelsProperty.append_submodel| updates |SubmodelsProperty.typeids| and
        |SubmodelsProperty.submodels| as well as the corresponding vectors of the
        cythonized models:

        >>> main_cy.storagemodels.append_submodel(submodel=sub_cy, typeid=1)
        >>> assert main_cy.storagemodels.number == 1
        >>> assert main_cy.storagemodels.typeids[0] == 1
        >>> assert main_cy.cymodel.storagemodels._get_typeid(0) == 1
        >>> assert main_cy.storagemodels.submodels[0] is sub_cy
        >>> assert main_cy.cymodel.storagemodels._get_submodel(0) is sub_cy.cymodel

        Connecting a pure Python mode main model with a Cython mode submodel causes no
        harm:

        >>> main_py.storagemodels.append_submodel(submodel=sub_cy, typeid=1)
        >>> assert main_py.storagemodels.number == 2
        >>> assert main_py.storagemodels.typeids[0] == 1
        >>> assert main_py.storagemodels.submodels[0] is sub_py
        >>> assert main_py.storagemodels.typeids[1] == 1
        >>> assert main_py.storagemodels.submodels[1] is sub_cy

        However, connecting a Cython mode main model with a pure Python mode submodel
        would result in erroneous calculations and thus raises the following error:

        >>> main_cy.storagemodels.append_submodel(submodel=sub_py, typeid=1)
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to append submodel `sw1d_storage` to property \
`storagemodels` of the main model `sw1d_channel`, the following error occurred: The \
main model is initialised in Cython mode, but the submodel is initialised in pure \
Python mode so that the main model's cythonized methods could apply the submodel's \
methods.

        >>> assert main_cy.storagemodels.number == 1
        >>> assert main_cy.storagemodels.typeids[0] == 1
        >>> assert main_cy.cymodel.storagemodels._get_typeid(0) == 1
        >>> assert main_cy.storagemodels.submodels[0] is sub_cy
        >>> assert main_cy.cymodel.storagemodels._get_submodel(0) is sub_cy.cymodel

        Method |SubmodelsProperty.append_submodel| checks if the given submodel follows
        at least one supported interface:

        >>> sub_wrong = prepare_model("sw1d_lias")
        >>> main_py.storagemodels.append_submodel(submodel=sub_wrong, typeid=1)
        Traceback (most recent call last):
        ...
        ValueError: While trying to append submodel `sw1d_lias` to property \
`storagemodels` of the main model `sw1d_channel`, the following error occurred: The \
given submodel is not an instance of any of the following supported interfaces: \
StorageModel_V1.

        >>> assert main_py.storagemodels.number == 2
        >>> assert main_py.storagemodels.typeids[0] == 1
        >>> assert main_py.storagemodels.submodels[0] is sub_py
        >>> assert main_py.storagemodels.typeids[1] == 1
        >>> assert main_py.storagemodels.submodels[1] is sub_cy

        For convenience, you can omit to pass the type ID.
        |SubmodelsProperty.append_submodel| then detects the first suitable ID
        automatically:

        >>> main_py.routingmodels.append_submodel(prepare_model("sw1d_weir_out"))
        >>> main_py.routingmodels.append_submodel(prepare_model("sw1d_q_in"))
        >>> main_py.routingmodels.append_submodel(prepare_model("sw1d_lias"))
        >>> assert main_py.routingmodels.number == 3
        >>> assert main_py.routingmodels.typeids == (3, 1, 2)

        Method |SubmodelsProperty.append_submodel| checks if the given submodel follows
        at least one supported interface:

        >>> main_py.routingmodels[0].routingmodelsupstream.append_submodel(
        ...     prepare_model("sw1d_q_out"))
        Traceback (most recent call last):
        ...
        ValueError: While trying to append submodel `sw1d_q_out` to property \
`routingmodelsupstream` of the main model `sw1d_weir_out`, the following error \
occurred: The given submodel is not an instance of any of the following supported \
interfaces: RoutingModel_V1 and RoutingModel_V2.
        """
        assert (mainmodel := self._mainmodel) is not None
        try:
            if typeid is None:
                typeid = self._find_first_suitable_interface(submodel).typeid
            else:
                self._check_submodel_follows_interface(submodel)
            if (cymain := mainmodel.cymodel) is not None:
                if (cysub := submodel.cymodel) is None:
                    raise RuntimeError(self._CYTHON_PYTHON_SUBMODEL_ERROR_MESSAGE)
                cyprop: interfaceutils.SubmodelsProperty = getattr(cymain, self.name)
                cyprop.append_submodel(submodel=cysub, typeid=typeid)
            self._mainmodel2numbersubmodels[mainmodel] += 1
            self.__hydpy_mainmodel2submodels__[mainmodel].append(submodel)
            self._mainmodel2submodeltypeids[mainmodel].append(typeid)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to append submodel `{submodel}` to property "
                f"`{self.name}` of the main model `{mainmodel}`"
            )

    @property
    def submodels(self) -> tuple[TypeSubmodelInterface | None, ...]:
        """The currently handled submodels.

        >>> from hydpy import prepare_model
        >>> main = prepare_model("sw1d_channel")
        >>> sub1 = prepare_model("sw1d_q_in")
        >>> sub2 = prepare_model("sw1d_lias")
        >>> main.routingmodels.append_submodel(submodel=sub1, typeid=1)
        >>> main.routingmodels.append_submodel(submodel=sub2, typeid=1)
        >>> assert main.routingmodels.submodels == (sub1, sub2)
        """
        assert (mainmodel := self._mainmodel) is not None
        return tuple(self.__hydpy_mainmodel2submodels__[mainmodel])

    @property
    def typeids(self) -> tuple[int, ...]:
        """The interface-specific type IDs of the currently handled submodels.

        >>> from hydpy import prepare_model
        >>> main = prepare_model("sw1d_channel")
        >>> sub1 = prepare_model("sw1d_q_in")
        >>> sub2 = prepare_model("sw1d_lias")
        >>> main.routingmodels.append_submodel(submodel=sub1, typeid=1)
        >>> main.routingmodels.append_submodel(submodel=sub2, typeid=1)
        >>> assert main.routingmodels.typeids == (1, 1)
        """
        assert (mainmodel := self._mainmodel) is not None
        return tuple(self._mainmodel2submodeltypeids[mainmodel])

    def __getitem__(self, value: int) -> TypeSubmodelInterface | None:
        assert (mainmodel := self._mainmodel) is not None
        return self.__hydpy_mainmodel2submodels__[mainmodel][value]

    def __iter__(self) -> Iterator[TypeSubmodelInterface | None]:
        assert (mainmodel := self._mainmodel) is not None
        yield from self.__hydpy_mainmodel2submodels__[mainmodel]

    def __len__(self) -> int:
        return self.number


class SubmodelIsMainmodelProperty:
    """Descriptor for boolean "submodel_is_mainmodel" attributes.

    |SubmodelIsMainmodelProperty| instances work like simple boolean attributes but
    silently synchronise the equally named boolean attributes of the corresponding
    cython model, if available:

    >>> from hydpy import prepare_model, pub
    >>> with pub.options.usecython(True):
    ...     model = prepare_model("hland_96")
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

    _owner2value: dict[Model, bool]
    _name: Final[str]  # type: ignore[misc]

    def __init__(self, doc: str | None = None) -> None:
        self._owner2value = {}
        self.__doc__ = doc

    def __set_name__(self, owner: type[Model], name: str) -> None:
        self._name = name  # type: ignore[misc]

    @overload
    def __get__(self, obj: None, objtype: type[Model] | None) -> Self: ...

    @overload
    def __get__(self, obj: Model, objtype: type[Model] | None) -> bool: ...

    def __get__(
        self, obj: Model | None, objtype: type[Model] | None = None
    ) -> Self | bool:
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
    ...     model = prepare_model("hland_96")
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

    _owner2value: dict[Model, int]
    _name: Final[str]  # type: ignore[misc]

    def __init__(self, doc: str | None = None) -> None:
        self._owner2value = {}
        self.__doc__ = doc

    def __set_name__(self, owner: type[Model], name: str) -> None:
        self._name = name  # type: ignore[misc]

    @overload
    def __get__(self, obj: None, objtype: type[Model] | None) -> Self: ...

    @overload
    def __get__(self, obj: Model, objtype: type[Model] | None) -> int: ...

    def __get__(
        self, obj: Model | None, objtype: type[Model] | None = None
    ) -> Self | int:
        if obj is None:
            return self
        return self._owner2value.get(obj, 0)

    def __set__(self, obj: Model, value: int) -> None:
        self._owner2value[obj] = value
        if (cymodel := obj.cymodel) is not None:
            setattr(cymodel, self._name, value)


class SharedProperty(Generic[T]):
    """Base class for descriptors that handle model properties which need
    synchronisation between the Python and the Cython world."""

    name: str

    def __set_name__(self, owner: Model, name: str) -> None:
        self.name = name.lower()

    @overload
    def __get__(self, obj: Model, objtype: type[Model]) -> T: ...

    @overload
    def __get__(self, obj: None, objtype: type[Model]) -> Self: ...

    def __get__(self, obj: Model | None, objtype: type[Model]) -> Self | T:
        if obj is None:
            return self
        if obj.cymodel:
            return getattr(obj.cymodel, self.name)
        return vars(obj).get(self.name, 0)

    def __set__(self, obj: Model, value: T) -> None:
        if obj.cymodel:
            setattr(obj.cymodel, self.name, value)
        else:
            vars(obj)[self.name] = value


class Idx_Sim(SharedProperty[int]):
    """The simulation step index."""

    def __init__(self) -> None:
        self.__doc__ = "The simulation step index."


class Idx_HRU(SharedProperty[int]):
    """The hydrological response unit index."""

    def __init__(self) -> None:
        self.__doc__ = "The hydrological response unit index."


class Idx_Segment(SharedProperty[int]):
    """The segment index."""

    def __init__(self) -> None:
        self.__doc__ = "The segment index."


class Idx_Run(SharedProperty[int]):
    """The run index."""

    def __init__(self) -> None:
        self.__doc__ = "The run index."


class Threading(SharedProperty[bool]):
    """Is multi-threading for this model (and its submodels) currently enabled?

    Change this flag only for testing purposes.
    """

    def __init__(self) -> None:
        self.__doc__ = "Is multi-threading for this model currently enabled?"

    def __set__(self, obj: Model, value: bool) -> None:
        super().__set__(obj, value)
        for input_ in obj.sequences.inputs:
            if input_.NDIM == 0:
                input_.__hydpy__set_fastaccessattribute__(
                    "inputflag", input_.node2idx and not value
                )
        for submodel in obj.find_submodels(include_subsubmodels=False).values():
            setattr(submodel, self.name, value)


class DocName(NamedTuple):
    """Definitions for the documentation names of specific base or application
    models."""

    short: str
    """Short name of a model, e.g. "W-Wag"."""

    description: str = "base model"
    """Description of a model, e.g. "extended version of the original Wageningen WALRUS 
    model"."""

    @property
    def long(self):
        """Long name of a model.

        >>> from hydpy.models.wland_wag import Model
        >>> Model.DOCNAME.long
        'HydPy-W-Wag'
        """
        return f"HydPy-{self.short}"

    @property
    def complete(self) -> str:
        """Complete presentation of a model.

        >>> from hydpy.models.wland_wag import Model
        >>> Model.DOCNAME.complete
        'HydPy-W-Wag (extended version of the original Wageningen WALRUS model)'
        """
        return f"{self.long} ({self.description})"

    @property
    def family(self) -> str:
        """Family name of a model.

        >>> from hydpy.models.wland_wag import Model
        >>> Model.DOCNAME.family
        'HydPy-W'
        """
        return "-".join(self.long.split("-")[:2])


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

    >>> from hydpy.models.hland_96 import *
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

    cymodel: CyModelProtocol | None
    parameters: parametertools.Parameters
    sequences: sequencetools.Sequences
    masks: masktools.Masks
    idx_sim = Idx_Sim()
    threading = Threading()

    __hydpy_element__: devicetools.Element | None
    __HYDPY_NAME__: ClassVar[str]

    INLET_METHODS: ClassVar[tuple[type[Method], ...]]
    OUTLET_METHODS: ClassVar[tuple[type[Method], ...]]
    OBSERVER_METHODS: ClassVar[tuple[type[Method], ...]]
    RECEIVER_METHODS: ClassVar[tuple[type[Method], ...]]
    SENDER_METHODS: ClassVar[tuple[type[Method], ...]]
    ADD_METHODS: ClassVar[tuple[Callable, ...]]
    METHOD_GROUPS: ClassVar[tuple[str, ...]]
    SUBMODELINTERFACES: ClassVar[tuple[type[SubmodelInterface], ...]]
    SUBMODELS: ClassVar[tuple[type[Submodel], ...]]

    SOLVERPARAMETERS: tuple[type[parametertools.Parameter], ...] = ()

    REUSABLE_METHODS: ClassVar[tuple[type[ReusableMethod], ...]]

    COMPOSITE: bool = False
    """Flag for informing whether the respective |Model| subclass is usually not 
    directly applied by model users but behind the scenes for compositing all models 
    owned by elements belonging to the same |Element.collective| (see method 
    |Elements.unite_collectives|)."""

    DOCNAME: DocName

    __HYDPY_ROOTMODEL__: bool | None
    """Flag telling whether a submodel should be considered as a submodel graph root.
    
    `None` is reserved for base and special-purpose models likely irrelevant to users. 
    """

    def __init__(self) -> None:
        self.cymodel = None
        self.__hydpy_element__ = None
        self._init_methods()

    def _init_methods(self) -> None:
        """Convert all pure Python calculation functions of the model class to methods
        and assign them to the model instance."""
        blacklist_shortnames: set[str] = set()
        shortname2method: dict[str, types.MethodType] = {}
        for cls_ in self.get_methods():
            longname = cls_.__name__.lower()
            if issubclass(cls_, ReusableMethod):
                setattr(self, cls_.REUSEMARKER, False)
                method = types.MethodType(cls_.call_reusablemethod, self)
            else:
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
        if (element := self.__hydpy_element__) is None:
            raise exceptiontools.AttributeNotReady(
                f"Model `{self.name}` is not connected to an `Element` so far."
            )
        return element

    @element.setter
    def element(self, element: devicetools.Element) -> None:
        self.__hydpy_element__ = element
        if not self.COMPOSITE:
            for model in self.find_submodels().values():
                model.__hydpy_element__ = element
        if exceptiontools.getattr_(element, "model", None) is not self:
            element.model = self

    @element.deleter
    def element(self) -> None:
        if (element := self.__hydpy_element__) is not None:
            if exceptiontools.getattr_(element, "model", None) is self:
                del element.model
        for model in self.find_submodels(include_mainmodel=True).values():
            model.__hydpy_element__ = None

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
        >>> element1.model.parameters.control.nmbsegments(0)

        Now all connections work as expected:

        >>> in1.sequences.sim = 1.0
        >>> in2.sequences.sim = 2.0
        >>> out1.sequences.sim = 3.0
        >>> element1.model.update_inlets()
        >>> element1.model.sequences.inlets.q
        q(1.0, 2.0)
        >>> element1.model.update_outlets()
        >>> element1.model.sequences.outlets.q
        q(3.0)

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
        and |hland_states.UZ| of application model |hland_96|.  |hland_inputs.T| uses
        its own data (which we define manually, but we could read it from a file as
        well), whereas |hland_inputs.P| gets its data from node `inp1`.  Flux sequence
        |hland_fluxes.Q0| and state sequence |hland_states.UZ| pass their data to two
        separate output nodes, whereas all other fluxes and states do not.  This
        functionality requires telling each node which sequence it should connect to,
        which we do by passing the sequence types (or the globally available aliases
        `hland_inputs_P`, `hland_fluxes_Q0`, and `hland_states_UZ`) to the `variable`
        keyword of different node objects:

        >>> from hydpy import pub
        >>> from hydpy.aliases import hland_inputs_P, hland_fluxes_Q0, hland_states_UZ
        >>> pub.timegrids = "2000-01-01", "2000-01-06", "1d"

        >>> inp1 = Node("inp1", variable=hland_inputs_P)
        >>> outp1 = Node("outp1", variable=hland_fluxes_Q0)
        >>> outp2 = Node("outp2", variable=hland_states_UZ)
        >>> element8 = Element("element8", outlets=out1, inputs=inp1,
        ...                    outputs=[outp1, outp2])
        >>> element8.model = prepare_model("hland_96")
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
        >>> from hydpy.aliases import lland_inputs_Nied, lland_fluxes_QDGZ
        >>> Precip = FusedVariable("Precip", hland_inputs_P, lland_inputs_Nied)
        >>> inp2 = Node("inp2", variable=Precip)
        >>> FastRunoff = FusedVariable("FastRunoff", hland_fluxes_Q0, lland_fluxes_QDGZ)
        >>> outp3 = Node("outp3", variable=FastRunoff)
        >>> element9 = Element("element9", outlets=out1, inputs=inp2, outputs=outp3)
        >>> element9.model = prepare_model("hland_96")
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

        >>> from hydpy.aliases import lland_inputs_TemL
        >>> Wrong = FusedVariable("Wrong", lland_inputs_Nied, lland_inputs_TemL)
        >>> inp3 = Node("inp3", variable=Wrong)
        >>> element10 = Element("element10", outlets=out1, inputs=inp3)
        >>> element10.model = prepare_model("hland_96")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `input` \
sequences of the model handled by element `element10`, the following error occurred: \
The following nodes have not been connected to any sequences: inp3.

        >>> outp4 = Node("outp4", variable=Wrong)
        >>> element11 = Element("element11", outlets=out1, outputs=outp4)
        >>> element11.model = prepare_model("hland_96")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `output` \
sequences of the model handled by element `element11`, the following error occurred: \
None of the output sequences of model `hland_96` is among the sequences of the fused \
variable `Wrong` of node `outp4`.

        Selecting the wrong sequences results in the following error messages:

        >>> outp5 = Node("outp5", variable=hland_fluxes_Q0)
        >>> element12 = Element("element12", outlets=out1, inputs=outp5)
        >>> element12.model = prepare_model("hland_96")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the `input` \
sequences of the model handled by element `element12`, the following error occurred: \
The following nodes have not been connected to any sequences: outp5.

        >>> inp5 = Node("inp5", variable="P")
        >>> element13 = Element("element13", outlets=out1, outputs=inp5)
        >>> element13.model = prepare_model("hland_96")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `output` sequences \
of the model handled by element `element13`, the following error occurred: No factor, \
flux, or state sequence of model `hland_96` is named `p`.

        So far, you can build connections to 0-dimensional output sequences only:

        >>> from hydpy.models.hland.hland_fluxes import PC
        >>> outp6 = Node("outp6", variable=PC)
        >>> element14 = Element("element14", outlets=out1, outputs=outp6)
        >>> element14.model = prepare_model("hland_96")
        Traceback (most recent call last):
        ...
        TypeError: While trying to build the node connection of the `output` sequences \
of the model handled by element `element14`, the following error occurred: Only \
connections with 0-dimensional output sequences are supported, but sequence `pc` is \
1-dimensional.

        |FusedVariable| also supports |ReceiverSequence| for passing information from
        output nodes to receiver sequences (instead of input sequences, which we
        demonstrated in the above examples).  We take the receiver sequences
        |dam_receivers.OWL| (outer water level) and |dam_receivers.RWL| (remote water
        level) used by the application model |dam_pump| as an example:

        >>> from hydpy.aliases import dam_receivers_OWL, dam_receivers_RWL

        One |dam_pump| instance (handled by element `dam1`) shall receive the water
        level (|dam_factors.WaterLevel|) of two independent |dam_pump| instances.
        `dam1` interprets the water level of `dam2` as its outer water level and the
        water level of `dam3` as its remote water level:

        >>> from hydpy.aliases import dam_factors_WaterLevel
        >>> owl = FusedVariable("OWL", dam_receivers_OWL, dam_factors_WaterLevel)
        >>> rwl = FusedVariable("RWL", dam_receivers_RWL, dam_factors_WaterLevel)
        >>> n21, n31 = Node("n21", variable=owl), Node("n31", variable=rwl)
        >>> x, y = Node("x", variable=owl), Node("y", variable=rwl)
        >>> dam1 = Element("dam1", inlets="n01", outlets="n12",
        ...                receivers=(n21, n31))
        >>> dam2 = Element("dam2", inlets="n12", outlets="n23",
        ...                receivers=(x,y), outputs=n21)
        >>> dam3 = Element("dam3", inlets="n23", outlets="n34",
        ...                receivers=(x, y), outputs=n31)
        >>> dam1.model = prepare_model("dam_pump")
        >>> dam2.model = prepare_model("dam_pump")
        >>> dam3.model = prepare_model("dam_pump")

        We confirm that all connections are correctly built by letting `dam2` and
        `dam3` send different water levels:

        >>> dam2.model.sequences.factors.waterlevel = 2.0
        >>> dam2.model.update_outputs()
        >>> dam3.model.sequences.factors.waterlevel = 3.0
        >>> dam3.model.update_outputs()
        >>> dam1.model.update_receivers(0)
        >>> dam1.model.sequences.receivers.owl
        owl(2.0)
        >>> dam1.model.sequences.receivers.rwl
        rwl(3.0)

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
            group = "observers"
            self._connect_observers()
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

    def _connect_inputs(self, report_noconnect: bool = True) -> None:
        self._connect_subgroup("inputs", report_noconnect)

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
                            sequence.node2idx[node] = None
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
                sequence_.node2idx[node] = None

    def _determine_name(self, var: str | sequencetools.InOutSequenceTypes) -> str:
        if isinstance(var, str):
            return var.lower()
        return var.__name__.lower()

    def _connect_inlets(self, report_noconnect: bool = True) -> None:
        self._connect_subgroup("inlets", report_noconnect)

    def _connect_observers(self, report_noconnect: bool = True) -> None:
        self._connect_subgroup("observers", report_noconnect)

    def _connect_receivers(self, report_noconnect: bool = True) -> None:
        self._connect_subgroup("receivers", report_noconnect)

    def _connect_outlets(self, report_noconnect: bool = True) -> None:
        self._connect_subgroup("outlets", report_noconnect)

    def _connect_senders(self, report_noconnect: bool = True) -> None:
        self._connect_subgroup("senders", report_noconnect)

    def _connect_subgroup(
        self, group: LinkInputSequenceGroup, report_noconnect: bool
    ) -> None:

        available_nodes = getattr(self.element, group)
        applied_nodes: list[devicetools.Node] = []
        sequences: list[sequencetools.InputSequence | sequencetools.LinkSequence] = []
        self.__hydpy__collect_sequences__(group, sequences)

        for sequence in sequences:
            sequence.connect_to_nodes(
                group=group,
                available_nodes=available_nodes,
                applied_nodes=applied_nodes,
                report_noconnect=report_noconnect,
            )

        if report_noconnect and (len(applied_nodes) < len(available_nodes)):
            remaining_nodes = [
                node.name for node in available_nodes if node not in applied_nodes
            ]
            raise RuntimeError(
                f"The following nodes have not been connected to any sequences: "
                f"{objecttools.enumeration(remaining_nodes)}."
            )

    def __hydpy__collect_sequences__(
        self,
        group: str,
        sequences: list[sequencetools.InputSequence | sequencetools.LinkSequence],
    ) -> None:
        sequences.extend(self.sequences[group])  # type: ignore[arg-type]
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.__hydpy__collect_sequences__(group, sequences)

    @property
    def name(self) -> str:
        """Name of the model type.

        For base models, |Model.name| corresponds to the package name:

        >>> from hydpy import prepare_model
        >>> hland = prepare_model("hland")
        >>> hland.name
        'hland'

        For application models, |Model.name| to corresponds the module name:

        >>> hland_96 = prepare_model("hland_96")
        >>> hland_96.name
        'hland_96'

        This last example has only technical reasons:

        >>> hland.name
        'hland'
        """
        return self.__HYDPY_NAME__

    def prepare_allseries(self, allocate_ram: bool = True, jit: bool = False) -> None:
        """Call method |Model.prepare_inputseries| with `read_jit=jit` and methods
        |Model.prepare_factorseries|, |Model.prepare_fluxseries|, and
        |Model.prepare_stateseries| with `write_jit=jit`."""
        self.prepare_inputseries(allocate_ram=allocate_ram, read_jit=jit)
        self.prepare_factorseries(allocate_ram=allocate_ram, write_jit=jit)
        self.prepare_fluxseries(allocate_ram=allocate_ram, write_jit=jit)
        self.prepare_stateseries(allocate_ram=allocate_ram, write_jit=jit)
        self.prepare_linkseries(allocate_ram=allocate_ram, write_jit=jit)

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
        |FluxSequence| objects."""
        self.sequences.fluxes.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def prepare_stateseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all directly handled
        |StateSequence| objects."""
        self.sequences.states.prepare_series(
            allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
        )

    def prepare_linkseries(
        self, allocate_ram: bool = True, read_jit: bool = False, write_jit: bool = False
    ) -> None:
        """Call method |IOSequence.prepare_series| of all directly handled
        |LinkSequence| objects."""
        for subseqs in self.sequences.linksubsequences:
            subseqs.prepare_series(
                allocate_ram=allocate_ram, read_jit=read_jit, write_jit=write_jit
            )

    def load_allseries(self) -> None:
        """Call method |Model.load_inputseries|, |Model.load_factorseries|,
        |Model.load_fluxseries|, |Model.load_stateseries|, and
        |Model.load_linkseries|."""
        self.load_inputseries()
        self.load_factorseries()
        self.load_fluxseries()
        self.load_stateseries()
        self.load_linkseries()

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

    def load_linkseries(self) -> None:
        """Call method |IOSequence.load_series| of all directly handled |LinkSequence|
        objects."""
        for subseqs in self.sequences.linksubsequences:
            subseqs.load_series()

    def save_allseries(self) -> None:
        """Call method |Model.save_inputseries|, |Model.save_factorseries|,
        |Model.save_fluxseries|, |Model.save_stateseries|, and
        |Model.save_linkseries|."""
        self.save_inputseries()
        self.save_factorseries()
        self.save_fluxseries()
        self.save_stateseries()
        self.save_linkseries()

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

    def save_linkseries(self) -> None:
        """Call method |IOSequence.save_series| of all directly handled |LinkSequence|
        objects."""
        for subseqs in self.sequences.linksubsequences:
            subseqs.save_series()

    def get_controlfileheader(
        self,
        import_submodels: bool = True,
        parameterstep: timetools.PeriodConstrArg | None = None,
        simulationstep: timetools.PeriodConstrArg | None = None,
    ) -> str:
        """Return the header of a parameter control file.

        The header contains the default coding information, the model import commands
        and the actual parameter and simulation step sizes:

        >>> from hydpy import prepare_model, pub
        >>> model = prepare_model("hland_96")
        >>> model.aetmodel = prepare_model("evap_aet_hbv96")
        >>> pub.timegrids = "2000.01.01", "2001.01.01", "1h"
        >>> print(model.get_controlfileheader())
        from hydpy.models.hland_96 import *
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
        from hydpy.models.hland_96 import *
        <BLANKLINE>
        simulationstep("3d")
        parameterstep("2d")
        <BLANKLINE>
        <BLANKLINE>

        .. testsetup::

            >>> del pub.timegrids
        """
        lines = [f"from hydpy.models.{self} import *"]
        if import_submodels:
            names = []
            for submodel in self.find_submodels().values():
                if (name := submodel.name) not in names:
                    names.append(name)
            for name in sorted(names):
                lines.append(f"from hydpy.models import {name}")
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
        *,
        parameterstep: timetools.PeriodConstrArg | None = None,
        simulationstep: timetools.PeriodConstrArg | None = None,
        auxfiler: auxfiletools.Auxfiler | None = None,
        sublevel: int = 0,
        ignore: tuple[type[parametertools.Parameter], ...] | None = None,
    ) -> list[str]:
        parameter2auxfile = None if auxfiler is None else auxfiler.get(self)
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
        parameterstep: timetools.PeriodConstrArg | None = None,
        simulationstep: timetools.PeriodConstrArg | None = None,
        auxfiler: auxfiletools.Auxfiler | None = None,
        filepath: str | None = None,
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

        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep("1d")
        >>> simulationstep("1h")
        >>> k(0.1)
        >>> n(3)

        >>> from hydpy import Open
        >>> with Open():
        ...     model.save_controls(filepath="otherdir/otherfile.py")
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        otherdir/otherfile.py
        ---------------------------------------
        from hydpy.models.test_stiff1d import *
        <BLANKLINE>
        simulationstep("1h")
        parameterstep("1d")
        <BLANKLINE>
        k(0.1)
        n(3)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Method |Model.save_controls| also writes the string representations of all
        |SolverParameter| objects with non-default values into the control file:

        >>> solver.abserrormax(1e-6)
        >>> with Open():
        ...     model.save_controls(filepath="otherdir/otherfile.py")
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        otherdir/otherfile.py
        ---------------------------------------
        from hydpy.models.test_stiff1d import *
        <BLANKLINE>
        simulationstep("1h")
        parameterstep("1d")
        <BLANKLINE>
        k(0.1)
        n(3)
        <BLANKLINE>
        solver.abserrormax(0.000001)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Without a given file path and a proper project configuration, method
        |Model.save_controls| raises the following error:

        >>> model.save_controls()
        Traceback (most recent call last):
        ...
        RuntimeError: To save the control parameters of a model to a file, its \
filename must be known.  This can be done, by passing a filename to function \
`save_controls` directly.  But in complete HydPy applications, it is usally assumed \
to be consistent with the name of the element handling the model.

        Submodels like |meteo_glob_fao56| allow using their instances by multiple main
        models.  We prepare such a case by selecting such an instance as the submodel
        of the absolute main model |lland_knauf| and the the relative submodel
        |evap_aet_morsim|:

        >>> from hydpy.core.importtools import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-02", "1d"
        >>> from hydpy.models.lland_knauf import *
        >>> parameterstep()
        >>> nhru(1)
        >>> ft(1.0)
        >>> fhru(1.0)
        >>> gh(100.0)
        >>> lnk(ACKER)
        >>> measuringheightwindspeed(10.0)
        >>> lai(3.0)
        >>> wmax(300.0)
        >>> with model.add_radiationmodel_v1("meteo_glob_fao56") as meteo_glob_fao56:
        ...     latitude(50.0)
        >>> with model.add_aetmodel_v1("evap_aet_morsim"):
        ...     measuringheightwindspeed(2.0)
        ...     model.add_radiationmodel_v1(meteo_glob_fao56)

        To avoid name collisions, |Model.save_controls| prefixes the string `submodel_`
        to the submodel name (which is identical to the submodel module's name) to
        create the name of the variable that references the shared model's instance:

        >>> with Open():  # doctest: +ELLIPSIS
        ...     model.save_controls(filepath="otherdir/otherfile.py")
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~...
        otherdir/otherfile.py
        ----------------------------------------------------------------------------...
        from hydpy.models.lland_knauf import *
        from hydpy.models import evap_aet_morsim
        from hydpy.models import meteo_glob_fao56
        ...
        simulationstep("1d")
        parameterstep("1d")
        ...
        ft(1.0)
        ...
        measuringheightwindspeed(10.0)
        ...
        with model.add_aetmodel_v1(evap_aet_morsim):
            measuringheightwindspeed(2.0)
            ...
            with model.add_radiationmodel_v1(meteo_glob_fao56) as \
submodel_meteo_glob_fao56:
                latitude(50.0)
                ...
        model.add_radiationmodel_v1(submodel_meteo_glob_fao56)
        ...
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~...
        """

        def _extend_lines_submodel(
            model: Model, sublevel: int, preparemethods: set[str]
        ) -> None:
            def _find_adder_and_position() -> (
                tuple[importtools.SubmodelAdder, str | None]
            ):
                mt2sn2as = importtools.SubmodelAdder.__hydpy_maintype2subname2adders__
                subname, position = name.rpartition(".")[2], None
                for modeltype in inspect.getmro(type(model)):
                    if (name2adders := mt2sn2as.get(modeltype)) is not None:
                        if subname.rsplit("_")[-1].isnumeric():
                            subname, position = subname.rsplit("_")
                        for adder in name2adders[subname]:
                            if isinstance(submodel, adder.submodelinterface):
                                return adder, position
                assert False

            sublevel += 1
            for name, submodel in model.find_submodels(
                include_subsubmodels=False, repeat_sharedmodels=True
            ).items():
                adder, position = _find_adder_and_position()
                importtools.TargetParameterUpdater.testmode = True
                try:
                    if position is None:
                        adder.update(model, submodel, refresh=False)
                    else:
                        adder.update(
                            model, submodel, position=int(position), refresh=False
                        )
                finally:
                    importtools.TargetParameterUpdater.testmode = False
                position = "" if position is None else f", position={position}"
                addername = adder.get_wrapped().__name__
                indent = (sublevel - 1) * "    "
                if submodel in visited_shared_submodels:
                    lines.append(
                        f"{indent}model.{addername}(submodel_{submodel}{position})\n"
                    )
                else:
                    line = f"{indent}with model.{addername}({submodel}{position})"
                    if submodel in shared_submodels:
                        assert isinstance(submodel, SharableSubmodelInterface)
                        visited_shared_submodels.add(submodel)
                        line = f"{line} as submodel_{submodel}:\n"
                    else:
                        line = f"{line}:\n"
                    lines.append(line)
                    preparemethods_ = preparemethods.copy()
                    for method in adder.methods:
                        preparemethods_.add(method.__name__)
                    targetparameters = set()
                    for methodname in preparemethods_:
                        updater = getattr(submodel, methodname, None)
                        if (
                            isinstance(updater, importtools.TargetParameterUpdater)
                            and ((old := updater.values_orig.get(submodel)) is not None)
                            and ((new := updater.values_test.get(submodel)) is not None)
                            and objecttools.is_equal(old, new)
                        ):
                            targetparameters.add(updater.targetparameter)
                    submodellines = (
                        submodel._get_controllines(  # pylint: disable=protected-access
                            parameterstep=parameterstep,
                            simulationstep=simulationstep,
                            auxfiler=auxfiler,
                            sublevel=sublevel,
                            ignore=tuple(targetparameters),
                        )
                    )
                    if submodellines:
                        lines.extend(submodellines)
                    else:
                        lines.append(f"{sublevel * '    '}pass\n")  # pragma: no cover
                    _extend_lines_submodel(
                        model=submodel,
                        sublevel=sublevel,
                        preparemethods=preparemethods_,
                    )

        header = self.get_controlfileheader(
            import_submodels=True,
            parameterstep=parameterstep,
            simulationstep=simulationstep,
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

        submodels = tuple(self.find_submodels(repeat_sharedmodels=True).values())
        sharable_submodels = {
            m for m in submodels if isinstance(m, SharableSubmodelInterface)
        }
        shared_submodels = {m for m in sharable_submodels if submodels.count(m) > 1}
        visited_shared_submodels: set[SharableSubmodelInterface] = set()

        # ToDo: needs refactoring
        for submodel in self.find_submodels().values():
            submodel.preparemethod2arguments.clear()
        try:
            _extend_lines_submodel(model=self, sublevel=0, preparemethods=set())
        finally:
            for submodel in self.find_submodels().values():
                submodel.preparemethod2arguments.clear()

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

    @contextlib.contextmanager
    def define_conditions(
        self, module: types.ModuleType | str | None = None
    ) -> Generator[None, None, None]:
        """Allow defining the values of condition sequences in condition files
        conveniently.

        |Model.define_conditions| works similar to the "add_submodel" methods wrapped
        by instances of class |SubmodelAdder| but is much simpler.  In combination with
        the `with` statement, it makes the all relevant state and log sequences
        temporarily directly available:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "6h"
        >>> from hydpy.models.lland_knauf import *
        >>> parameterstep()
        >>> nhru(2)
        >>> ft(10.0)
        >>> fhru(0.2, 0.8)
        >>> gh(100.0)
        >>> lnk(ACKER, MISCHW)
        >>> wmax(acker=100.0, mischw=200.0)
        >>> measuringheightwindspeed(10.0)
        >>> with model.add_aetmodel_v1("evap_aet_morsim"):
        ...     pass
        >>> with model.aetmodel.define_conditions():
        ...     loggedwindspeed2m(1.0, 3.0, 2.0, 4.0)
        >>> loggedwindspeed2m
        Traceback (most recent call last):
        ...
        NameError: name 'loggedwindspeed2m' is not defined
        >>> model.aetmodel.sequences.logs.loggedwindspeed2m
        loggedwindspeed2m(1.0, 3.0, 2.0, 4.0)

        One can pass the submodel's module or name for documentation purposes:

        >>> with model.aetmodel.define_conditions("evap_aet_morsim"):
        ...     loggedwindspeed2m(4.0, 2.0, 3.0, 1.0)
        >>> loggedwindspeed2m
        Traceback (most recent call last):
        ...
        NameError: name 'loggedwindspeed2m' is not defined
        >>> model.aetmodel.sequences.logs.loggedwindspeed2m
        loggedwindspeed2m(4.0, 2.0, 3.0, 1.0)

        For misleading input, |Model.define_conditions| raises the following error:

        >>> from hydpy.models import evap_aet_hbv96
        >>> with model.aetmodel.define_conditions(evap_aet_hbv96):
        ...     loggedwindspeed2m(1.0, 3.0, 2.0, 4.0)
        Traceback (most recent call last):
        ...
        TypeError: While trying to define the conditions of (sub)model \
`evap_aet_morsim`, the following error occurred: (Sub)model `evap_aet_morsim` is not \
of type `evap_aet_hbv96`.
        >>> loggedwindspeed2m
        Traceback (most recent call last):
        ...
        NameError: name 'loggedwindspeed2m' is not defined
        >>> model.aetmodel.sequences.logs.loggedwindspeed2m
        loggedwindspeed2m(4.0, 2.0, 3.0, 1.0)

        .. testsetup::

            >>> del pub.timegrids
        """
        try:
            if module is not None:
                module = importtools.load_modelmodule(module)
                if self.__module__ != module.__name__:
                    raise TypeError(
                        f"(Sub)model `{self.name}` is not of type "
                        f"`{module.__name__.rpartition('.')[2]}`."
                    )
            assert (
                ((frame1 := inspect.currentframe()) is not None)
                and ((frame2 := frame1.f_back) is not None)
                and ((frame3 := frame2.f_back) is not None)
            )
            namespace = frame3.f_locals
            old_locals = namespace.get(importtools.__HYDPY_MODEL_LOCALS__, {})
            new_locals = {}
            for seq in self.sequences.conditionsequences:
                new_locals[seq.name] = seq
            try:
                namespace[importtools.__HYDPY_MODEL_LOCALS__] = new_locals
                namespace.update(new_locals)
                yield
            finally:
                for name in new_locals:
                    namespace.pop(name, None)
                namespace.update(old_locals)
                namespace[importtools.__HYDPY_MODEL_LOCALS__] = old_locals
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to define the conditions of (sub)model `{self.name}`"
            )

    def __prepare_conditionfilename(self, filename: str | None) -> str:
        if filename is None:
            filename = objecttools.devicename(self)
            if filename == "?":
                raise RuntimeError(
                    "To load or save the conditions of a model from or to a file, its "
                    "filename must be known.  This can be done, by passing filename "
                    "to method `load_conditions` or `save_conditions` directly.  But "
                    "in complete HydPy applications, it is usally assumed to be "
                    "consistent with the name of the element handling the model.  "
                    "Actually, neither a filename is given nor does the model know "
                    "its master element."
                )
        if not filename.endswith(".py"):
            filename += ".py"
        return filename

    def load_conditions(self, filename: str | None = None) -> None:
        """Read the initial conditions from a file and assign them to the respective
        |StateSequence| and |LogSequence| objects.

        The documentation on method |HydPy.load_conditions| of class |HydPy| explains
        how to read and write condition values for complete *HydPy* projects in the
        most convenient manner.  However, using the underlying methods
        |Model.load_conditions| and |Model.save_conditions| directly offers the
        advantage of specifying alternative filenames.  We demonstrate this by using
        the state sequence |hland_states.SM| if the `land_dill_assl` |Element| object
        of the `HydPy-H-Lahn` example project:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> dill_assl = hp.elements.land_dill_assl.model
        >>> dill_assl.sequences.states.sm
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)

        We work in the freshly created condition directory `test`:

        >>> with TestIO():
        ...     pub.conditionmanager.currentdir = "test"

        We set all soil moisture values to zero and write the updated values to file
        `cold_start.py`:

        >>> dill_assl.sequences.states.sm(0.0)
        >>> with TestIO():
        ...     dill_assl.save_conditions("cold_start.py")

        Trying to reload from the written file (after changing the soil moisture values
        again) without passing the file name fails due to the wrong assumption that the
        element's name serves as the file name base:

        >>> dill_assl.sequences.states.sm(100.0)
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     dill_assl.load_conditions()
        Traceback (most recent call last):
        ...
        FileNotFoundError: While trying to load the initial conditions of element \
`land_dill_assl`, the following error occurred: [Errno 2] No such file or directory: \
'...land_dill_assl.py'

        One does not need to explicitly state the file extensions (`.py`):

        >>> with TestIO():
        ...     dill_assl.load_conditions("cold_start")
        >>> dill_assl.sequences.states.sm
        sm(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        Automatically determining the file name requires a proper reference to the
        related |Element| object:

        >>> del dill_assl.element
        >>> with TestIO():
        ...     dill_assl.save_conditions()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to save the actual conditions of element `?`, the \
following error occurred: To load or save the conditions of a model from or to a file, \
its filename must be known.  This can be done, by passing filename to method \
`load_conditions` or `save_conditions` directly.  But in complete HydPy applications, \
it is usally assumed to be consistent with the name of the element handling the \
model.  Actually, neither a filename is given nor does the model know its master \
element.

        The submodels selected in the `HydPy-H-Lahn` example project do not require any
        condition sequences.  Hence, we replace the combination of |evap_aet_hbv96| and
        |evap_pet_hbv96| with a plain |evap_aet_morsim| instance, which relies on some
        log sequences:

        >>> with dill_assl.add_aetmodel_v1("evap_aet_morsim"):
        ...     pass

        The following code demonstrates that reading and writing of condition sequences
        also works for submodels:

        >>> logs = dill_assl.aetmodel.sequences.logs
        >>> logs.loggedairtemperature = 20.0
        >>> logs.loggedwindspeed2m = 2.0
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     dill_assl.save_conditions("submodel_conditions.py")
        >>> logs.loggedairtemperature = 10.0
        >>> logs.loggedwindspeed2m = 1.0
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     dill_assl.load_conditions("submodel_conditions.py")
        >>> logs.loggedairtemperature
        loggedairtemperature(20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0,
                             20.0, 20.0, 20.0, 20.0)
        >>> logs.loggedwindspeed2m
        loggedwindspeed2m(2.0)

        Method |Model.save_conditions| writes lines that use function |controlcheck|.
        It, therefore, must know the control directory related to the written
        conditions, for which it relies on the |FileManager.currentdir| property of the
        control manager instance of module |pub|.  So, make sure this property points
        to the correct directory.  Otherwise, errors like the following might occur:

        >>> with TestIO():  # doctest: +ELLIPSIS
        ...     del pub.controlmanager.currentdir
        ...     pub.controlmanager.currentdir = "calib_1"
        ...     pub.controlmanager.currentdir = "calib_2"
        ...     pub.controlmanager.currentdir = None
        ...     dill_assl.save_conditions("submodel_conditions.py")
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to save the actual conditions of element `?`, the \
following error occurred: While trying to determine the related control file \
directory for configuring the `controlcheck` function, the following error occurred: \
The current working directory of the control manager has not been defined manually \
and cannot be determined automatically: The default directory (default) is not among \
the available directories (calib_1 and calib_2).

        .. testsetup::

            >>> from hydpy import Element, Node, pub
            >>> Element.clear_all()
            >>> Node.clear_all()
            >>> del pub.timegrids
        """
        hasconditions = any(
            model.sequences.states or model.sequences.logs
            for model in self.find_submodels(include_mainmodel=True).values()
        )
        if hasconditions:
            try:
                dict_ = locals()
                for seq in self.sequences.conditionsequences:
                    dict_[seq.name] = seq
                dict_["model"] = self
                filepath = os.path.join(
                    hydpy.pub.conditionmanager.inputpath,
                    self.__prepare_conditionfilename(filename),
                )
                with hydpy.pub.options.trimvariables(False):
                    runpy.run_path(filepath, init_globals=dict_)
                for model in self.find_submodels(include_mainmodel=True).values():
                    for seq in reversed(tuple(model.sequences.conditionsequences)):
                        seq.trim()
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to load the initial conditions of element "
                    f"`{objecttools.devicename(self)}`"
                )

    def save_conditions(self, filename: str | None = None) -> None:
        """Query the actual conditions of the |StateSequence| and |LogSequence| objects
        and write them into an initial condition file.

        See the documentation on method |Model.load_conditions| for further
        information.
        """
        try:
            model2hasconditions = {}
            for model in self.find_submodels(include_mainmodel=True).values():
                seqs = model.sequences
                model2hasconditions[model] = seqs.states or seqs.logs
            if any(model2hasconditions.values()):
                con = hydpy.pub.controlmanager
                lines = [f"from hydpy.models.{self} import *\n"]
                submodelnames = set()
                for model, hasconditions in model2hasconditions.items():
                    if hasconditions and (model is not self):
                        submodelnames.add(model.name)
                for submodelname in sorted(submodelnames):
                    lines.append(f"from hydpy.models import {submodelname}\n")
                try:
                    controldir = con.currentdir
                except BaseException:
                    objecttools.augment_excmessage(
                        "While trying to determine the related control file directory "
                        "for configuring the `controlcheck` function"
                    )
                lines.append(
                    f'\ncontrolcheck(projectdir=r"{con.projectdir}", '
                    f'controldir="{controldir}", '
                    f'stepsize="{hydpy.pub.timegrids.stepsize}")\n\n'
                )
                for seq in self.sequences.conditionsequences:
                    lines.append(f"{repr(seq)}\n")
                for fullname, model in self.find_submodels().items():
                    if model2hasconditions[model]:
                        if fullname.rsplit("_")[-1].isnumeric():
                            prefix, _, position = fullname.rpartition("_")
                            fullname = f"{prefix}[{position}]"
                        lines.append(f"with {fullname}.define_conditions({model}):\n")
                        for seq in model.sequences.conditionsequences:
                            lines.append(f"    {repr(seq)}\n")
                filepath = os.path.join(
                    hydpy.pub.conditionmanager.outputpath,
                    self.__prepare_conditionfilename(filename),
                )
                with open(filepath, "w", encoding="utf-8") as file_:
                    file_.writelines(lines)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to save the actual conditions of element "
                f"`{objecttools.devicename(self)}`"
            )

    def trim_conditions(self) -> None:
        """Call method |Sequences.trim_conditions| of the handled |Sequences| object."""
        for model in self.find_submodels(include_mainmodel=True).values():
            model.sequences.trim_conditions()

    def reset_conditions(self) -> None:
        """Call method |Sequences.reset| of the handled |Sequences| object."""
        for model in self.find_submodels(include_mainmodel=True).values():
            model.sequences.reset()

    @abc.abstractmethod
    def simulate(self, idx: int) -> None:
        """Perform a simulation run over a single simulation time step."""

    def simulate_period(self, i0: int, i1: int) -> None:
        """Perform a simulation run over a complete simulation period.

        The required arguments correspond to the first and last simulation step index.

        Method |Model.simulate_period| calls method |Model.simulate| repeatedly for the
        whole considered simulation period and is thought for the multi-threading mode.
        Hence, we repeat the example of method |Model.simulate| but set the
        |Model.threading| flag to |True|:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> model = hp.elements.land_dill_assl.model
        >>> model.threading = True

        Method |Model.simulate_period| also calls method |Model.save_data| so that the
        simulated outflow is readily available via the link sequence |hland_outlets.Q|:

        >>> model.simulate_period(0, 4)
        >>> from hydpy import print_vector
        >>> print_vector(model.sequences.outlets.q.series[:4])
        11.757526, 8.865079, 7.101815, 5.994195

        Be aware that models never exchange data with their connected nodes when in
        multi-threading mode:

        >>> hp.nodes.dill_assl.sequences.sim
        sim(0.0)

        .. testsetup::

            >>> from hydpy import Element, Node, pub
            >>> del pub.timegrids
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        for i in range(i0, i1):
            self.simulate(i)
            self.update_senders(i)
            self.update_receivers(i)
            self.save_data(i)

    def reset_reuseflags(self) -> None:
        """Reset all |ReusableMethod.REUSEMARKER| attributes of the current model
        instance and its submodels (usually at the beginning of a simulation step).

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for method in self.REUSABLE_METHODS:
            setattr(self, method.REUSEMARKER, False)
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.reset_reuseflags()

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

    def _update_pointers_in(
        self,
        subseqs: (
            sequencetools.InletSequences
            | sequencetools.ObserverSequences
            | sequencetools.ReceiverSequences
        ),
    ) -> None:
        if not self.threading:
            for seq in subseqs:
                pointer = seq.__hydpy__get_fastaccessattribute__("pointer")
                if (pointer is not None) and (seq.NDIM == 0):
                    setattr(seq.fastaccess, seq.name, pointer[0])
                else:
                    values = getattr(seq.fastaccess, seq.name, None)
                    if values is not None:
                        for i in range(getattr(seq.fastaccess, f"len_{seq.name}")):
                            values[i] = pointer[i]

    def _update_pointers_out(
        self, subseqs: sequencetools.OutletSequences | sequencetools.SenderSequences
    ) -> None:
        if not self.threading:
            for seq in subseqs:
                pointer = seq.__hydpy__get_fastaccessattribute__("pointer")
                if (pointer is not None) and (seq.NDIM == 0):
                    pointer[0] += getattr(seq.fastaccess, seq.name)
                else:
                    values = getattr(seq.fastaccess, seq.name, None)
                    if values is not None:
                        for i in range(getattr(seq.fastaccess, f"len_{seq.name}")):
                            pointer[i][0] += values[i]

    def update_inlets(self) -> None:
        """Update all link sequences and then call all methods defined as
        "INLET_METHODS" in the defined order.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.update_inlets()
        self._update_pointers_in(self.sequences.inlets)
        for method in self.INLET_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def update_outlets(self) -> None:
        """Call all methods defined as "OUTLET_METHODS" in the defined order and then
        update all outlet nodes.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.update_outlets()
        for method in self.OUTLET_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call
        self._update_pointers_out(self.sequences.outlets)

    def update_observers(self) -> None:
        """Update all observer sequences and then call all methods defined as
        "OBSERVER_METHODS" in the defined order.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.update_observers()
        self._update_pointers_in(self.sequences.observers)
        for method in self.OBSERVER_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def update_receivers(self, idx: int) -> None:
        """Update all receiver sequences and then call all methods defined as
        "RECEIVER_METHODS" in the defined order.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.update_receivers(idx)
        self._update_pointers_in(self.sequences.receivers)
        for method in self.RECEIVER_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call

    def update_senders(self, idx: int) -> None:
        """Call all methods defined as "SENDER_METHODS" in the defined order and then
        update all sender nodes.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            submodel.update_senders(idx)
        for method in self.SENDER_METHODS:
            method.__call__(self)  # pylint: disable=unnecessary-dunder-call
        self._update_pointers_out(self.sequences.senders)

    def new2old(self) -> None:
        """Call method |StateSequences.new2old| of subattribute `sequences.states`.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        if self.sequences:
            self.sequences.states.new2old()
        for submodel in self.find_submodels(include_subsubmodels=False).values():
            if submodel.sequences:
                submodel.new2old()

    def update_outputs(self) -> None:
        """Call method |Sequences.update_outputs| of attribute |Model.sequences|.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        if not self.threading:
            self.sequences.update_outputs()
            for submodel in self.find_submodels(include_subsubmodels=False).values():
                submodel.update_outputs()

    @classmethod
    def get_methods(cls, skip: tuple[MethodGroup, ...] = ()) -> Iterator[type[Method]]:
        """Convenience method for iterating through all methods selected by a |Model|
        subclass.

        >>> from hydpy.models import hland_96
        >>> for method in hland_96.Model.get_methods():
        ...     print(method.__name__)  # doctest: +ELLIPSIS
        Calc_TC_V1
        ...
        Get_SnowCover_V1

        One can skip all methods that belong to specific groups:

        >>> for method in hland_96.Model.get_methods(
        ...     skip=("OUTLET_METHODS", "INTERFACE_METHODS")
        ... ):
        ...     print(method.__name__)  # doctest: +ELLIPSIS
        Calc_TC_V1
        ...
        Calc_OutRC_RConcModel_V1

        Note that function |Model.get_methods| returns the "raw" |Method| objects
        instead of the modified Python or Cython functions used for performing
        calculations.
        """
        methods = set()
        if hasattr(cls, "METHOD_GROUPS"):
            for groupname in cls.METHOD_GROUPS:
                if groupname not in skip:
                    for method in getattr(cls, groupname, ()):
                        if method not in methods:
                            methods.add(method)
                            yield method
        if hasattr(cls, "INTERFACE_METHODS") and ("INTERFACE_METHODS" not in skip):
            for method in cls.INTERFACE_METHODS:
                if method not in methods:
                    methods.add(method)
                    yield method

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_sidemodels: Literal[False] = ...,
        include_optional: Literal[False] = ...,
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[False] = ...,
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_sidemodels: Literal[False] = ...,
        include_optional: Literal[True],
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[False] = ...,
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model | None]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_sidemodels: Literal[False] = ...,
        include_optional: Literal[False] = ...,
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[True],
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model | None]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_sidemodels: Literal[False] = ...,
        include_optional: Literal[True],
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[True],
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model | None]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: Literal[False],
        include_mainmodel: bool = False,
        include_sidemodels: Literal[True],
        include_optional: Literal[False] = ...,
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[False] = ...,
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: Literal[False],
        include_mainmodel: bool = False,
        include_sidemodels: Literal[True],
        include_optional: Literal[True],
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[False] = ...,
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model | None]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: Literal[False],
        include_mainmodel: bool = False,
        include_sidemodels: Literal[True],
        include_optional: Literal[False] = ...,
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[True],
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model | None]: ...

    @overload
    def find_submodels(
        self,
        *,
        include_subsubmodels: Literal[False],
        include_mainmodel: bool = False,
        include_sidemodels: Literal[True],
        include_optional: Literal[True],
        include_feedbacks: bool = False,
        aggregate_vectors: Literal[True],
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model | None]: ...

    def find_submodels(
        self,
        *,
        include_subsubmodels: bool = True,
        include_mainmodel: bool = False,
        include_sidemodels: bool = False,
        include_optional: bool = False,
        include_feedbacks: bool = False,
        aggregate_vectors: bool = False,
        repeat_sharedmodels: bool = False,
    ) -> dict[str, Model] | dict[str, Model | None]:
        """Find the (sub)submodel instances of the current main model instance.

        Method |Model.find_submodels| returns an empty dictionary by default if no
        submodel is available:

        >>> from hydpy import prepare_model
        >>> model = prepare_model("lland_knauf")
        >>> model.find_submodels()
        {}

        The `include_mainmodel` parameter allows the addition of the main model:

        >>> model.find_submodels(include_mainmodel=True)
        {'model': lland_knauf}

        The `include_optional` parameter allows considering prepared and unprepared
        submodels:

        >>> model.find_submodels(include_optional=True)
        {'model.aetmodel': None, 'model.radiationmodel': None, 'model.soilmodel': None}
        >>> model.aetmodel = prepare_model("evap_aet_minhas")
        >>> model.aetmodel.petmodel = prepare_model("evap_pet_mlc")
        >>> model.aetmodel.petmodel.retmodel = prepare_model("evap_ret_tw2002")
        >>> from pprint import pprint
        >>> pprint(model.find_submodels(include_optional=True))  # doctest: +ELLIPSIS
        {'model.aetmodel': evap_aet_minhas...,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.petmodel': evap_pet_mlc...,
         'model.aetmodel.petmodel.retmodel': evap_ret_tw2002,
         'model.aetmodel.petmodel.retmodel.radiationmodel': None,
         'model.aetmodel.petmodel.retmodel.tempmodel': None,
         'model.aetmodel.soilwatermodel': None,
         'model.radiationmodel': None,
         'model.soilmodel': None}

        By default, |Model.find_submodels| does not return an additional entry when a
        main model serves as a sub-submodel:

        >>> model.aetmodel.soilwatermodel = model
        >>> model.aetmodel.soilwatermodel_is_mainmodel = True
        >>> pprint(model.find_submodels(include_optional=True))  # doctest: +ELLIPSIS
        {'model.aetmodel': evap_aet_minhas...,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.petmodel': evap_pet_mlc...,
         'model.aetmodel.petmodel.retmodel': evap_ret_tw2002,
         'model.aetmodel.petmodel.retmodel.radiationmodel': None,
         'model.aetmodel.petmodel.retmodel.tempmodel': None,
         'model.radiationmodel': None,
         'model.soilmodel': None}

        Use the `include_feedbacks` parameter to make such feedback connections
        transparent:

        >>> pprint(model.find_submodels(include_mainmodel=True,
        ...     include_optional=True, include_feedbacks=True))  # doctest: +ELLIPSIS
        {'model': lland_knauf...,
         'model.aetmodel': evap_aet_minhas...,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.petmodel': evap_pet_mlc...,
         'model.aetmodel.petmodel.retmodel': evap_ret_tw2002,
         'model.aetmodel.petmodel.retmodel.radiationmodel': None,
         'model.aetmodel.petmodel.retmodel.tempmodel': None,
         'model.aetmodel.soilwatermodel': lland_knauf...,
         'model.radiationmodel': None,
         'model.soilmodel': None}

        |Model.find_submodels| includes only one reference to shared model instances by
        default:

        >>> model.radiationmodel = prepare_model("meteo_glob_fao56")
        >>> model.aetmodel = prepare_model("evap_aet_morsim")
        >>> model.aetmodel.radiationmodel = model.radiationmodel
        >>> pprint(model.find_submodels(include_optional=True))  # doctest: +ELLIPSIS
        {'model.aetmodel': evap_aet_morsim...,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.snowalbedomodel': None,
         'model.aetmodel.snowcovermodel': None,
         'model.aetmodel.snowycanopymodel': None,
         'model.aetmodel.soilwatermodel': None,
         'model.aetmodel.tempmodel': None,
         'model.radiationmodel': meteo_glob_fao56,
         'model.soilmodel': None}

        Use the `repeat_sharedmodels` parameter to change this behaviour:

        >>> pprint(model.find_submodels(
        ...     repeat_sharedmodels=True, include_optional=True))  # doctest: +ELLIPSIS
        {'model.aetmodel': evap_aet_morsim...,
         'model.aetmodel.intercmodel': None,
         'model.aetmodel.radiationmodel': meteo_glob_fao56,
         'model.aetmodel.snowalbedomodel': None,
         'model.aetmodel.snowcovermodel': None,
         'model.aetmodel.snowycanopymodel': None,
         'model.aetmodel.soilwatermodel': None,
         'model.aetmodel.tempmodel': None,
         'model.radiationmodel': meteo_glob_fao56,
         'model.soilmodel': None}

        All previous examples dealt with scalar submodel references handled by
        |SubmodelProperty|.  Now we will focus on vectors of submodel references
        handled by |SubmodelsProperty| and take |sw1d_channel| as an example:

        >>> channel = prepare_model("sw1d_channel")
        >>> channel.parameters.control.nmbsegments(2)

        Again, method |Model.find_submodels| returns by default an empty dictionary if
        no submodel is available:

        >>> channel.find_submodels()
        {}

        The `include_optional` parameter works as shown for the scalar case.  But for
        scalar cases, the names contain an additional suffix to indicate the position
        of the respective submodel:

        >>> pprint(channel.find_submodels(include_optional=True))
        {'model.routingmodels_0': None,
         'model.routingmodels_1': None,
         'model.routingmodels_2': None,
         'model.storagemodels_0': None,
         'model.storagemodels_1': None}

        We now add some possible submodels to the |sw1d_channel| main model:

        >>> with channel.add_routingmodel_v1("sw1d_q_in", position=0, update=False):
        ...     pass
        >>> with channel.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> with channel.add_routingmodel_v2("sw1d_lias", position=1, update=False):
        ...     pass
        >>> with channel.add_storagemodel_v1("sw1d_storage", position=1, update=False):
        ...     pass
        >>> with channel.add_routingmodel_v3("sw1d_weir_out", position=2, update=False):
        ...     pass

        Method |Model.find_submodels| associates them with the correct positions:

        >>> pprint(channel.find_submodels())
        {'model.routingmodels_0': sw1d_q_in,
         'model.routingmodels_1': sw1d_lias,
         'model.routingmodels_2': sw1d_weir_out,
         'model.storagemodels_0': sw1d_storage,
         'model.storagemodels_1': sw1d_storage}

        One can use the `aggregate_vectors` parameter to gain a better overview.
        Then, |Model.find_submodels| reports only the names of the respective
        |SubmodelsProperty| instances with a suffixed wildcard to distinguish them
        from |SubmodelProperty| instances:

        >>> channel.find_submodels(aggregate_vectors=True)
        {'model.routingmodels_*': None, 'model.storagemodels_*': None}

        Another option is to include side models.  However, this does not work in
        combination with including sub-submodels and thus cannot give further insight
        into the configuration of a |sw1d_channel| model:

        >>> pprint(channel.find_submodels(include_sidemodels=True))
        Traceback (most recent call last):
        ...
        ValueError: Including sub-submodels and side-models leads to ambiguous results.

        So, one needs to apply it to the respective submodels directly:

        >>> pprint(channel.storagemodels[0].find_submodels(
        ...     include_subsubmodels=False, include_sidemodels=True))
        {'model.routingmodelsdownstream_0': sw1d_lias,
         'model.routingmodelsupstream_0': sw1d_q_in}

        >>> pprint(channel.routingmodels[1].find_submodels(
        ...     include_subsubmodels=False, include_sidemodels=True))
        {'model.routingmodelsdownstream_0': sw1d_weir_out,
         'model.routingmodelsupstream_0': sw1d_q_in,
         'model.storagemodeldownstream': sw1d_storage,
         'model.storagemodelupstream': sw1d_storage}
        """

        if include_subsubmodels and include_sidemodels:
            raise ValueError(
                "Including sub-submodels and side-models leads to ambiguous results."
            )

        def _find_submodels(name: str, model: Model) -> None:
            name2submodel_new = {}

            if isinstance(model, SharableSubmodelInterface):
                sharables.add(model)

            for subprop in SubmodelProperty.__hydpy_modeltype2instance__[type(model)]:
                sub_is_main = getattr(model, f"{subprop.name}_is_mainmodel")
                if (include_sidemodels or not subprop.sidemodel) and (
                    include_feedbacks or not sub_is_main
                ):
                    submodel = getattr(model, subprop.name)
                    if (include_optional or (submodel is not None)) and (
                        repeat_sharedmodels or (submodel not in sharables)
                    ):
                        name2submodel_new[f"{name}.{subprop.name}"] = submodel

            for subsprop in SubmodelsProperty.__hydpy_modeltype2instance__[type(model)]:
                if include_sidemodels or not subsprop.sidemodels:
                    submodelsname = f"{name}.{subsprop.name}"
                    if aggregate_vectors:
                        name2submodel_new[f"{submodelsname}_*"] = None
                    elif submodels := subsprop.__hydpy_mainmodel2submodels__[model]:
                        for i, submodel in enumerate(submodels):
                            # implement when required:
                            assert not isinstance(submodel, SharableSubmodelInterface)
                            if include_optional or (submodel is not None):
                                name2submodel_new[f"{submodelsname}_{i}"] = submodel

            name2submodel.update(name2submodel_new)
            if include_subsubmodels:
                for subname, submodel in name2submodel_new.items():
                    if submodel not in seen:
                        seen.add(submodel)
                        _find_submodels(subname, submodel)

        seen: set[Model] = {self}
        sharables: set[SharableSubmodelInterface] = set()
        name2submodel = {"model": self} if include_mainmodel else {}
        _find_submodels("model", self)
        return dict(sorted(name2submodel.items()))

    def query_submodels(self, name: types.ModuleType | str, /) -> list[Model]:
        """Use |Model.find_submodels| to query all (sub)models of the given type.

        >>> from hydpy import prepare_model
        >>> model = prepare_model("lland_knauf")
        >>> model.query_submodels("meteo_glob_fao56")
        []

        >>> model.radiationmodel = prepare_model("meteo_glob_fao56")
        >>> model.query_submodels("meteo_glob_fao56")
        [meteo_glob_fao56]

        >>> model.aetmodel = prepare_model("evap_aet_morsim")
        >>> model.aetmodel.radiationmodel = model.radiationmodel
        >>> model.query_submodels("meteo_glob_fao56")
        [meteo_glob_fao56]

        >>> from hydpy.models import meteo_glob_fao56
        >>> model.aetmodel.radiationmodel = prepare_model(meteo_glob_fao56)
        >>> model.query_submodels(meteo_glob_fao56)
        [meteo_glob_fao56, meteo_glob_fao56]
        """
        if isinstance(name, types.ModuleType):
            name = importtools.load_modelmodule(name).Model.__HYDPY_NAME__
        submodels = self.find_submodels(include_mainmodel=True)
        return [s for s in submodels.values() if s.name == name]

    def update_parameters(self, ignore_errors: bool = False) -> None:
        """Use the control parameter values of the current model for updating its
        derived parameters and the control and derived parameters of all its submodels.

        We use the combination of |hland_96|, |evap_aet_hbv96|, and |evap_pet_hbv96|
        used by the `HydPy-H-Lahn` project for modelling the Dill catchment as an
        example:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp = prepare_full_example_2()[0]
        >>> model = hp.elements.land_dill_assl.model

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

        Second, |hland_96| requires definitions for the zones' altitude
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

        >>> from hydpy.models.hland_96 import ILAKE
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
        |hland_96| main model and |evap_derived.Altitude| of the |evap_pet_hbv96|
        submodel:

        >>> model.parameters.derived.z
        z(4.0)
        >>> model.aetmodel.petmodel.parameters.control.hrualtitude
        hrualtitude(400.0)
        >>> model.aetmodel.petmodel.parameters.derived.altitude
        altitude(400.0)
        """
        self.parameters.update(ignore_errors=ignore_errors)
        for name, submodel in self.find_submodels(include_subsubmodels=False).items():
            if isinstance(submodel, SubmodelInterface):
                adder = submodel._submodeladder  # pylint: disable=protected-access
                if adder is not None:
                    if adder.dimensionality == 0:
                        adder.update(self, submodel, refresh=True)
                    elif adder.dimensionality == 1:
                        position = int(name.rpartition("_")[2])
                        adder.update(self, submodel, position=position, refresh=True)
                    else:
                        assert_never(adder.dimensionality)
                    submodel.update_parameters(ignore_errors=ignore_errors)

    @property
    def conditions(self) -> ConditionsModel:
        """A nested dictionary that contains the values of all condition sequences of
        a model and its submodels.

        See the documentation on property |HydPy.conditions| for further information.
        """
        conditions = {}
        for name, model in self.find_submodels(include_mainmodel=True).items():
            conditions[name] = model.sequences.conditions
        return conditions

    @conditions.setter
    def conditions(self, conditions: ConditionsModel) -> None:
        for name, model in self.find_submodels(include_mainmodel=True).items():
            model.sequences.conditions = conditions[name]

    @property
    def couple_models(self) -> ModelCoupler | None:
        """If available, return a function object for coupling models to a composite
        model suitable at least for the actual model subclass (see method
        |Elements.unite_collectives|)."""
        return None

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
        if modulename.startswith("hydpy.interfaces."):
            cls.__HYDPY_NAME__ = cls.__name__
        if not modulename.startswith("hydpy.models."):
            return
        if modulename.count(".") > 2:
            modulename = modulename.rpartition(".")[0]
        module = cast(_ModelModule, importlib.import_module(modulename))
        modelname = modulename.split(".")[-1]
        cls.__HYDPY_NAME__ = modelname

        allsequences = set()
        st = sequencetools
        infos: tuple[tuple[type[Any], type[Any], set[Any]], ...] = (
            (st.InletSequences, st.InletSequence, set()),
            (st.ObserverSequences, st.ObserverSequence, set()),
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

        cls.REUSABLE_METHODS = tuple(
            method for method in cls.get_methods() if issubclass(method, ReusableMethod)
        )

    def __repr__(self) -> str:
        lines = [self.name]
        for port, model in self.find_submodels().items():
            prefix = port.count(".") * "    "
            lines.append(f"{prefix}{port.rsplit('.')[-1]}: {model.name}")
        return "\n".join(lines)


class RunModel(Model):
    """Base class for |AdHocModel| and |SegmentModel| that introduces so-called "run
    methods", which need to be executed in the order of their positions in the
    |RunModel.RUN_METHODS| tuple."""

    RUN_METHODS: ClassVar[tuple[type[Method], ...]]
    METHOD_GROUPS: ClassVar[tuple[str, ...]] = (
        "RECEIVER_METHODS",
        "INLET_METHODS",
        "OBSERVER_METHODS",
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

        The required argument `idx` corresponds to property `idx_sim` (see the main
        documentation on class |Model|).

        You can integrate method |Model.simulate| into your workflows for tailor-made
        simulation runs.  Method |Model.simulate| is complete enough to allow for
        consecutive calls.  However, note that it does neither call |Model.save_data|,
        |Model.update_receivers|, nor |Model.update_senders|.  Also, as done in the
        following example, one would have to reset the related node sequences:

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> model = hp.elements.land_dill_assl.model
        >>> for idx in range(4):
        ...     model.simulate(idx)
        ...     print(hp.nodes.dill_assl.sequences.sim)
        ...     hp.nodes.dill_assl.sequences.sim = 0.0
        sim(11.757526)
        sim(8.865079)
        sim(7.101815)
        sim(5.994195)
        >>> hp.nodes.dill_assl.sequences.sim.series
        InfoArray([nan, nan, nan, nan])

        The results above are identical to those of method |HydPy.simulate| of class
        |HydPy|, which is the standard method to perform simulation runs (except that
        method |HydPy.simulate| of class |HydPy| also performs the steps neglected by
        method |Model.simulate| of class |Model| mentioned above):

        >>> from hydpy import round_
        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> round_(hp.nodes.dill_assl.sequences.sim.series)
        11.757526, 8.865079, 7.101815, 5.994195

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.

        .. testsetup::

            >>> from hydpy import Element, Node, pub
            >>> del pub.timegrids
            >>> Node.clear_all()
            >>> Element.clear_all()
        """
        self.reset_reuseflags()
        self.load_data(idx)
        self.update_inlets()
        self.update_observers()
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


class SubstepModel(RunModel):
    """Base class for (routing) models that solve the underlying differential equations
    "substep-wise".

    "substep-wise" means method |SubstepModel.run| repeatedly calls all "run methods"
    in the usual order within each simulation step until the |SubstepModel.timeleft|
    attribute is not larger than zero anymore.  The concrete model subclass is up to
    reduce |SubstepModel.timeleft|.  This mechanism allows the concrete model to
    adjust the internal calculation time step depending on its current accuracy and
    stability requirements.
    """

    cymodel: CySubstepModelProtocol | None

    _timeleft: float = 0.0

    @property
    def timeleft(self) -> float:
        """The time left within the current simulation step [s]."""
        if (cymodel := self.cymodel) is None:
            return self._timeleft
        return cymodel.timeleft

    @timeleft.setter
    def timeleft(self, value: float) -> None:
        if (cymodel := self.cymodel) is None:
            self._timeleft = value
        else:
            cymodel.timeleft = value

    def run(self) -> None:
        """Call all methods defined as "run methods" repeatedly.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.timeleft = self.parameters.derived.seconds.value
        while True:
            for method in self.RUN_METHODS:
                method.__call__(self)  # pylint: disable=unnecessary-dunder-call
            if self.timeleft <= 0.0:
                break
            self.new2old()


class SolverModel(Model):
    """Base class for hydrological models, which solve ordinary differential equations
    with numerical integration algorithms."""

    PART_ODE_METHODS: ClassVar[tuple[type[Method], ...]]
    FULL_ODE_METHODS: ClassVar[tuple[type[Method], ...]]

    @abc.abstractmethod
    def solve(self) -> bool:
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

    SOLVERSEQUENCES: ClassVar[tuple[type[sequencetools.DependentSequence], ...]]
    PART_ODE_METHODS: ClassVar[tuple[type[Method], ...]]
    FULL_ODE_METHODS: ClassVar[tuple[type[Method], ...]]
    METHOD_GROUPS: ClassVar[tuple[str, ...]] = (
        "RECEIVER_METHODS",
        "INLET_METHODS",
        "OBSERVER_METHODS",
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
        self.reset_reuseflags()
        self.load_data(idx)
        self.update_inlets()
        self.update_observers()
        self.solve()
        self.update_outlets()
        self.update_outputs()

    def solve(self) -> bool:
        """Solve all `FULL_ODE_METHODS` in parallel.

        Implementing numerical integration algorithms that (hopefully) always work well
        in practice is a tricky task.  The following exhaustive examples show how well
        our "Explicit Lobatto Sequence" algorithm performs for the numerical test
        models |test_stiff0d| and |test_discontinous|.  We hope to cover all possible
        corner cases.  Please tell us if you find one we missed.

        First, we set the value of parameter |test_control.K| to zero, resulting in no
        changes at all and thus defining the simplest test case possible:

        >>> from hydpy.models.test_stiff0d import *
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
        >>> assert model.solve()
        >>> states.s
        s(1.0)
        >>> fluxes.q
        q(0.0)

        To achieve the above result, |ELSModel| requires two function calls, one for
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
        >>> assert model.solve()
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
        >>> assert model.solve()
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
        >>> assert model.solve()
        >>> states.s
        s(0.904837)
        >>> fluxes.q
        q(0.095163)
        >>> model.numvars.idx_method
        4
        >>> model.numvars.nmb_calls
        7

        |ELSModel| achieves even a very extreme numerical precision (just for testing,
        way beyond hydrological requirements) in one single step, but now requires 29
        method calls:

        >>> solver.abserrormax(1e-12)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> assert model.solve()
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

        With a more dynamic parameterisation, where the storage decreases by about 40 %
        per time step, |ELSModel| needs seven method calls to meet a "normal" error
        tolerance:

        >>> solver.abserrormax(0.01)
        >>> k(0.5)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> assert model.solve()
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
        >>> assert model.solve()
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
        >>> assert model.solve()
        >>> states.s
        s(0.019774)
        >>> fluxes.q
        q(0.980226)
        >>> round_(model.numvars.dt)
        0.3
        >>> model.numvars.nmb_calls
        44

        If we prevent |ELSModel| from compensatingf or its problems by disallowing it
        to reduce its integration step size, it does not achieve satisfactory results:

        >>> solver.reldtmin(1.0)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> assert model.solve()
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
        >>> assert model.solve()
        >>> states.s
        s(0.016806)
        >>> fluxes.q
        q(0.983194)
        >>> round_(model.numvars.dt)
        0.25
        >>> model.numvars.nmb_calls
        33

        Alternatively, you can restrict the available number of Lobatto methods.  Using
        two methods only is an inefficient choice for the given initial value problem,
        but it at least solves it with the required accuracy:

        >>> solver.reldtmax(1.0)
        >>> model.numconsts.nmb_methods = 2
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> assert model.solve()
        >>> states.s
        s(0.020284)
        >>> fluxes.q
        q(0.979716)
        >>> round_(model.numvars.dt)
        0.156698
        >>> model.numvars.nmb_calls
        74

        In the above examples, we control numerical accuracy based on absolute error
        estimates only via parameter |test_solver.AbsErrorMax|.  After assigning an
        actual value to parameter |test_solver.RelErrorMax|, |ELSModel| also takes
        relative errors into account.  We modify some of the above examples to show how
        this works.

        Generally, it is sufficient to meet one of the two criteria.  If we repeat the
        second example with a relaxed absolute but a strict relative tolerance, we
        reproduce the original result due to our absolute criteria being the relevant
        one:

        >>> solver.abserrormax(0.1)
        >>> solver.relerrormax(0.000001)
        >>> k(0.1)
        >>> states.s(1.0)
        >>> assert model.solve()
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
        >>> assert model.solve()
        >>> states.s
        s(0.905)
        >>> fluxes.q
        q(0.095)

        Reiterating the "more dynamic parameterisation" example results in slightly
        different but also correct results:

        >>> k(0.5)
        >>> states.s(1.0)
        >>> assert model.solve()
        >>> states.s
        s(0.607196)
        >>> fluxes.q
        q(0.392804)

        Reiterating the stiffest example with a relative instead of an absolute error
        tolerance of 0.1 achieves higher accuracy, as expected due to the value of
        |test_states.S| being far below 1.0 for some time:

        >>> k(4.0)
        >>> states.s(1.0)
        >>> assert model.solve()
        >>> states.s
        s(0.0185)
        >>> fluxes.q
        q(0.9815)

        Besides its weaknesses with stiff problems, |ELSModel| cannot solve
        discontinuous problems well.  We use the |test_stiff0d| example model to
        demonstrate how |ELSModel| behaves when confronted with such a problem.

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_discontinous import *
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
        >>> assert model.solve()
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
        >>> assert model.solve()
        >>> states.s
        s(-0.006827)
        >>> fluxes.q
        q(1.006827)
        >>> model.numvars.nmb_calls
        58

        >>> k(2.1)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> assert model.solve()
        >>> states.s
        s(-0.00072)
        >>> fluxes.q
        q(1.00072)
        >>> model.numvars.nmb_calls
        50

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        maxeval = 0
        if self.stop_els(maxeval):
            return False
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
                if self.stop_els(maxeval):
                    return False
                self.calculate_single_terms()
                maxeval += 1
                self.numvars.idx_method = 0
                self.numvars.idx_stage = 0
                self.set_point_fluxes()
                self.set_point_states()
                self.set_result_states()
            for self.numvars.idx_method in range(1, self.numconsts.nmb_methods + 1):
                for self.numvars.idx_stage in range(1, self.numvars.idx_method):
                    self.get_point_states()
                    if self.stop_els(maxeval):
                        return False
                    self.calculate_single_terms()
                    maxeval += 1
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
        return True

    def stop_els(self, nmbeval: int) -> bool:  # pylint: disable=unused-argument
        """Stop the Explicit Lobatto Sequence early.

        Always returns |False| but gives subclasses the chance to fall back to
        alternative methods in case the Explicit Lobatto Sequence does not converge
        fast enough.

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        return False

    def calculate_single_terms(self) -> None:
        """Apply all methods stored in the `PART_ODE_METHODS` tuple.

        >>> from hydpy.models.test_stiff0d import *
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

        >>> from hydpy.models.test_stiff0d import *
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
        >>> from hydpy.models.test_stiff0d import *
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

        >>> from hydpy import reverse_model_wildcard_import, print_vector
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> states.sv.old = 3.0, 3.0
        >>> states.sv.new = 3.0, 3.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._sv_points)
        >>> points[:4, 0] = 0.0, 0.0, 1.0, 0.0
        >>> points[:4, 1] = 0.0, 0.0, 2.0, 0.0
        >>> model.get_point_states()
        >>> print_vector(states.sv.old)
        3.0, 3.0
        >>> print_vector(states.sv.new)
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

        >>> from hydpy import print_vector
        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:] = 0.
        >>> model.set_point_states()
        >>> print_vector(points[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> states.sv.old = 3.0, 3.0
        >>> states.sv.new = 1.0, 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._sv_points)
        >>> points[:] = 0.
        >>> model.set_point_states()
        >>> print_vector(points[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_vector(points[:4, 1])
        0.0, 0.0, 2.0, 0.0
        """
        self._set_states(self.numvars.idx_stage, "points")

    def set_result_states(self) -> None:
        """Save the final states of the actual method.

        >>> from hydpy import print_vector
        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(states.fastaccess._s_results)
        >>> results[:] = 0.0
        >>> model.set_result_states()
        >>> print_vector(results[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> states.sv.old = 3.0, 3.0
        >>> states.sv.new = 1.0, 2.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(states.fastaccess._sv_results)
        >>> results[:] = 0.0
        >>> model.set_result_states()
        >>> print_vector(results[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_vector(results[:4, 1])
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

        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> fluxes.q = 0.0
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> model.get_sum_fluxes()
        >>> fluxes.q
        q(1.0)

        >>> from hydpy import reverse_model_wildcard_import, print_vector
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
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

        >>> from hydpy import print_vector
        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> fluxes.q = 1.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:] = 0.0
        >>> model.set_point_fluxes()
        >>> print_vector(points[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> fluxes.qv = 1.0, 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._qv_points)
        >>> points[:] = 0.0
        >>> model.set_point_fluxes()
        >>> print_vector(points[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_vector(points[:4, 1])
        0.0, 0.0, 2.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_stage, "points")

    def set_result_fluxes(self) -> None:
        """Save the final fluxes of the actual method.

        >>> from hydpy import print_vector
        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> fluxes.q = 1.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:] = 0.0
        >>> model.set_result_fluxes()
        >>> from hydpy import round_
        >>> print_vector(results[:4])
        0.0, 0.0, 1.0, 0.0

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> fluxes.qv = 1.0, 2.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._qv_results)
        >>> results[:] = 0.0
        >>> model.set_result_fluxes()
        >>> print_vector(results[:4, 0])
        0.0, 0.0, 1.0, 0.0
        >>> print_vector(results[:4, 1])
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

        >>> from hydpy import print_vector
        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> model.numvars.idx_stage = 1
        >>> model.numvars.dt = 0.5
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:4] = 15.0, 2.0, -999.0, 0.0
        >>> model.integrate_fluxes()
        >>> from hydpy import round_
        >>> from hydpy import pub
        >>> print_vector(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
        0.375, 0.125
        >>> fluxes.q
        q(2.9375)

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> model.numvars.idx_method = 2
        >>> model.numvars.idx_stage = 1
        >>> model.numvars.dt = 0.5
        >>> points = numpy.asarray(fluxes.fastaccess._qv_points)
        >>> points[:4, 0] = 1.0, 1.0, -999.0, 0.0
        >>> points[:4, 1] = 15.0, 2.0, -999.0, 0.0
        >>> model.integrate_fluxes()
        >>> print_vector(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
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

        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 5.0
        >>> model.reset_sum_fluxes()
        >>> fluxes.fastaccess._q_sum
        0.0

        >>> from hydpy import reverse_model_wildcard_import, print_vector
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> import numpy
        >>> sums = numpy.asarray(fluxes.fastaccess._qv_sum)
        >>> sums[:] = 5.0, 5.0
        >>> model.reset_sum_fluxes()
        >>> print_vector(fluxes.fastaccess._qv_sum)
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

        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> fluxes.q(2.0)
        >>> model.addup_fluxes()
        >>> fluxes.fastaccess._q_sum
        3.0

        >>> from hydpy import reverse_model_wildcard_import, print_vector
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
        >>> parameterstep()
        >>> n(2)
        >>> sums = numpy.asarray(fluxes.fastaccess._qv_sum)
        >>> sums[:] = 1.0, 2.0
        >>> fluxes.qv(3.0, 4.0)
        >>> model.addup_fluxes()
        >>> print_vector(sums)
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
        >>> from hydpy.models.test_stiff0d import *
        >>> parameterstep()
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:5] = 0.0, 0.0, 3.0, 4.0, 4.0
        >>> model.numvars.use_relerror = False
        >>> model.numvars.idx_method = 3
        >>> model.calculate_error()
        >>> round_(model.numvars.abserror)
        1.0
        >>> round_(model.numvars.relerror)
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
        >>> round_(model.numvars.relerror)
        inf

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_stiff1d import *
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
        >>> round_(model.numvars.relerror)
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

         >>> from hydpy.models.test_stiff0d import *
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


class ELSIEModel(ELSModel):
    """Extension of |ELSModel| that can fall back to the simple non-adaptive Implicit
    Euler method.


    As thoroughly explained in the documentation of |ELSModel|, the "Explicit Lobatto
    Sequence" can solve many non-stiff ordinary differential equations quite
    efficiently, but struggles with solving stiff ones.  If you develop a model that
    might be prone to stiffness, |ELSIEModel| could be a usable alternative.  It
    primarily works like |ELSModel| but falls back to using the simple non-adaptive
    Implicit Euler method as soon as the Explicit Lobatto Sequence is likely to fail
    because of stiffness.  See the examples :ref:`dam_v001_stiffness`,
    :ref:`dam_v001_optional_implicit_euler`, :ref:`dam_v001_enforced_implicit_euler`,
    and :ref:`dam_v001_mixed_approach` on application model |dam_v001| for how this
    works in practice.

    Note that, due to relying on the Pegasus iteration, |ELSIEModel| is currently
    restricted to models that require only a single, scalar state sequence.
    """

    def __init__(self) -> None:
        from hydpy.auxs import roottools  # pylint: disable=import-outside-toplevel

        super().__init__()
        pegasus = roottools.Pegasus(model=self)
        pegasus._cysubmodel.method0 = self.calculate_backwards_error
        self.pegasusimpleuler = pegasus

    def simulate(self, idx: int) -> None:
        """Similar to method |ELSModel.simulate| of class |ELSModel|, but can fall back
        to the Implicit Euler method by calling method
        |ELSIEModel.apply_implicit_euler_fallback| .

        When working in Cython mode, the standard model import overrides this generic
        Python version with a model-specific Cython version.
        """
        self.reset_reuseflags()
        self.load_data(idx)
        self.update_inlets()
        self.update_observers()
        state: float = self.get_state_old()
        if not self.solve():
            self.set_state_old(state)
            self.apply_implicit_euler_fallback()
            self.new2old()
        self.update_outlets()
        self.update_outputs()

    def apply_implicit_euler_fallback(self) -> None:
        """Solve the ordinary differential equation in a simple, non-adaptive manner by
        applying the Implicit Euler method in combination with the Pegasus root-finding
        method."""
        x: float = self.get_state_old()
        self.pegasusimpleuler.find_x(
            0.0,
            1.0 if x == 0.0 else 2.0 * x,
            self.get_state_min(),
            self.get_state_max(),
            0.0,
            self.determine_ytol(x),
            100,
        )
        self.calculate_full_terms()

    def determine_ytol(self, x: float) -> float:
        """Determine the absolute result error tolerance of the Pegasus iteration based
        on the user-defined absolute and relative tolerance values.

        >>> from hydpy.models.dam_v001 import *
        >>> parameterstep()
        >>> solver.abserrormax(1.0)
        >>> solver.relerrormax(nan)
        >>> from math import isclose
        >>> assert isclose(model.determine_ytol(0.0), 1.0)
        >>> assert isclose(model.determine_ytol(2.0), 1.0)
        >>> solver.relerrormax(0.1)
        >>> assert isclose(model.determine_ytol(0.0), 1.0)
        >>> assert isclose(model.determine_ytol(9.9), 0.99)
        >>> assert isclose(model.determine_ytol(10.1), 1.0)
        """
        sol = self.parameters.solver.fastaccess
        if (x == 0.0) or modelutils.isnan(sol.relerrormax):
            return sol.abserrormax
        return min(sol.abserrormax, sol.relerrormax * abs(x))

    def calculate_backwards_error(self, value: float) -> float:
        """Determine the "backwards error" of the current Pegasus iteration step."""
        self.set_state_new(value)
        self.calculate_single_terms()
        self.calculate_full_terms()
        return self.adjust_backwards_error(value - self.get_state_new())

    @abc.abstractmethod
    def stop_els(self, nmbeval: int) -> bool:
        """Stop the Explicit Lobatto Sequence early."""

    @abc.abstractmethod
    def adjust_backwards_error(self, value: float) -> float:
        """Adjust the given error of the Pegasus iteration, which is the difference
        between the estimated value and the calculated value of the single state
        variable, so that it is better comparable with the defined error tolerances."""

    @abc.abstractmethod
    def get_state_old(self) -> float:
        """Get the single state value that corresponds to the beginning of the
        current simulation step."""

    @abc.abstractmethod
    def set_state_old(self, value: float) -> None:
        """Set the single state value that corresponds to the beginning of the
        current simulation step."""

    @abc.abstractmethod
    def get_state_new(self) -> float:
        """Get the single state value that corresponds to the end of the current
        simulation step."""

    @abc.abstractmethod
    def set_state_new(self, value: float) -> None:
        """Set the single state value that corresponds to the end of the current
        simulation step."""

    @abc.abstractmethod
    def get_state_min(self) -> float:
        """Get the lowest allowed value of the single state variable."""

    @abc.abstractmethod
    def get_state_max(self) -> float:
        """Get the highest allowed value of the single state variable."""


class SubmodelInterface(Model, abc.ABC):
    """Base class for defining interfaces for submodels."""

    INTERFACE_METHODS: ClassVar[tuple[type[Method], ...]]
    _submodeladder: importtools.SubmodelAdder | None
    preparemethod2arguments: dict[str, tuple[tuple[Any, ...], dict[str, Any]]]

    typeid: ClassVar[int]
    """Type identifier that we use for differentiating submodels that target the same 
    process group (e.g. infiltration) but follow different interfaces.

    For `Submodel_V1`, |SubmodelInterface.typeid| is 1, for `Submodel_V2` 2, and so on.

    We prefer using |SubmodelInterface.typeid| over the standard |isinstance| checks in 
    model equations as it allows releasing Python's Globel Interpreter Lock in Cython.
    """

    def __init__(self) -> None:
        super().__init__()
        self._submodeladder = None
        self.preparemethod2arguments = {}

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


class SharableSubmodelInterface(SubmodelInterface, abc.ABC):
    """Base class for defining interfaces for submodels designed as "sharable".

    Currently, |SharableSubmodelInterface|  implements no functionality.  Its sole
    purpose is to allow model developers to mark a submodel as sharable, meaning
    multiple main model instances can share the same submodel instance.  It is more of
    a safety mechanism to prevent reusing submodels that are not designed for this
    purpose.
    """


class Submodel:
    """Base class for implementing "submodels" that serve to deal with (possibly
    complicated) general mathematical algorithms (e.g. root-finding algorithms) within
    hydrological model methods.


    You might find class |Submodel| useful when trying to implement algorithms
    requiring some interaction with the respective model without any Python overhead.
    See the modules |roottools| and `rootutils` as an example, implementing Python
    interfaces and Cython implementations of a root-finding algorithms, respectively.
    """

    METHODS: ClassVar[tuple[type[Method], ...]]
    CYTHONBASECLASS: ClassVar[type[object]]
    PYTHONCLASS: ClassVar[type[object]]
    name: ClassVar[str]
    _cysubmodel: object

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.lower()

    def __init__(self, model: Model) -> None:
        if model.cymodel:
            self._cysubmodel = getattr(model.cymodel, self.name)
        else:
            self._cysubmodel = self.PYTHONCLASS()
            for idx, methodtype in enumerate(getattr(self, "METHODS", ())):
                setattr(
                    self._cysubmodel,
                    f"method{idx}",
                    getattr(model, methodtype.__name__.lower()),
                )


class CoupleModels(Protocol[TypeModel_co]):
    """Specification for defining custom "couple_models" functions to be wrapped by
    function |define_modelcoupler|."""

    __name__: str

    def __call__(
        self, *, nodes: devicetools.Nodes, elements: devicetools.Elements
    ) -> TypeModel_co: ...


def define_modelcoupler(
    inputtypes: tuple[type[TypeModel_contra], ...], outputtype: type[TypeModel_co]
) -> Callable[
    [CoupleModels[TypeModel_co]], ModelCoupler[TypeModel_co, TypeModel_contra]
]:
    """Wrap a model-specific function for creating a composite model based given on
    |Node| and |Element| objects and their handled "normal" |Model| instances."""

    def _define_modelcoupler(
        wrapped: CoupleModels[TypeModel_co],
    ) -> ModelCoupler[TypeModel_co, TypeModel_contra]:
        return ModelCoupler(
            inputtypes=inputtypes, outputtype=outputtype, wrapped=wrapped
        )

    return _define_modelcoupler


class ModelCoupler(Generic[TypeModel_co, TypeModel_contra]):
    """Wrapper that extends the functionality of model-specific functions for coupling
    "normal" models to composite models.

    One benefit of using |ModelCoupler| over raw "couple_models" is that it
    alternatively accepts |Selection| objects instead of |Nodes| and |Elements|
    objects:

    >>> from hydpy import Element, Elements, Node, Nodes, prepare_model, Selection
    >>> n12 = Node("n12", variable="LongQ")
    >>> e1 = Element("e1", outlets=n12)
    >>> channel1 = prepare_model("sw1d_channel")
    >>> channel1.parameters.control.nmbsegments(1)
    >>> with channel1.add_storagemodel_v1("sw1d_storage", position=0, update=False):
    ...     pass
    >>> with channel1.add_routingmodel_v2("sw1d_lias", position=1, update=False):
    ...     pass
    >>> e1.model = channel1
    >>> e2 = Element("e2", inlets=n12)
    >>> channel2 = prepare_model("sw1d_channel")
    >>> channel2.parameters.control.nmbsegments(1)
    >>> with channel2.add_storagemodel_v1("sw1d_storage", position=0, update=False):
    ...     pass
    >>> e2.model = channel2

    >>> network1 = e1.model.couple_models(nodes=Nodes(n12), elements=Elements(e1, e2))
    >>> assert network1.storagemodels[0] is channel1.storagemodels[0]
    >>> assert network1.storagemodels[1] is channel2.storagemodels[0]
    >>> assert network1.routingmodels[0] is channel1.routingmodels[1]
    >>> assert network1.storagemodels[0].routingmodelsdownstream.number == 1
    >>> assert network1.storagemodels[1].routingmodelsupstream.number == 1

    >>> selection = Selection("test", nodes=n12, elements=[e1, e2])
    >>> network2 = e1.model.couple_models(selection=selection)
    >>> assert network2.storagemodels[0] is channel1.storagemodels[0]
    >>> assert network2.storagemodels[1] is channel2.storagemodels[0]
    >>> assert network2.routingmodels[0] is channel1.routingmodels[1]
    >>> assert network2.storagemodels[0].routingmodelsdownstream.number == 1
    >>> assert network2.storagemodels[1].routingmodelsupstream.number == 1

    It additionally checks if the wrapped "couple_models" function supports the types
    of all passed model instances:

    >>> e3 = Element("e3", inlets="n3_in", outlets="n3_out")
    >>> e3.model = prepare_model("musk_classic")
    >>> e1.model.couple_models(nodes=Nodes(n12), elements=Elements(e1, e2, e3))
    Traceback (most recent call last):
    ...
    TypeError: While trying to couple the given model instances to a composite model \
of type `sw1d_network` based on function `combine_channels`, the following error \
occurred: `musk_classic` of element `e3` is not among the supported model types: \
sw1d_channel.
    """

    _inputtypes: tuple[type[TypeModel_contra], ...]
    _outputtype: type[TypeModel_co]
    _wrapped: CoupleModels

    def __init__(
        self,
        inputtypes: tuple[type[TypeModel_contra], ...],
        outputtype: type[TypeModel_co],
        wrapped: CoupleModels[TypeModel_co],
    ) -> None:
        self._inputtypes = inputtypes
        self._outputtype = outputtype
        self._wrapped = wrapped
        functools.update_wrapper(wrapper=self, wrapped=wrapped)

    @overload
    def __call__(self, *, selection: selectiontools.Selection) -> TypeModel_co: ...

    @overload
    def __call__(
        self, *, nodes: devicetools.Nodes, elements: devicetools.Elements
    ) -> TypeModel_co: ...

    def __call__(
        self,
        *,
        nodes: devicetools.Nodes | None = None,
        elements: devicetools.Elements | None = None,
        selection: selectiontools.Selection | None = None,
    ) -> TypeModel_co:
        try:
            if selection is None:
                assert nodes is not None
                assert elements is not None
            else:
                nodes = selection.nodes
                elements = selection.elements
            for element in elements:
                if not isinstance(element.model, self._inputtypes):
                    modeltypes = (m.__HYDPY_NAME__ for m in self._inputtypes)
                    raise TypeError(
                        f"{objecttools.elementphrase(element.model)} is not among the "
                        f"supported model types: "
                        f"{objecttools.enumeration(modeltypes)}."
                    )
            return self._wrapped(nodes=nodes, elements=elements)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to couple the given model instances to a composite "
                f"model of type `{self._outputtype.__HYDPY_NAME__}` based on function "
                f"`{self._wrapped.__name__}`"
            )
