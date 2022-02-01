# -*- coding: utf-8 -*-
"""This module implements |property| like classes with similar or additional
behaviour."""

# import...
# ...from standard-library
from __future__ import annotations
import abc
import inspect
import types
from typing import *
from typing import Optional, Type, Any

from typing_extensions import Protocol  # type: ignore[misc]

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools

InputType = TypeVar("InputType")
InputType_contra = TypeVar("InputType_contra", contravariant=True)
OutputType = TypeVar("OutputType")
OutputType_co = TypeVar("OutputType_co", covariant=True)


class BaseDescriptor:
    """Base class for defining descriptors."""

    objtype: Type[Any]
    module: Optional[types.ModuleType]
    name: str
    __doc__: Optional[str]

    def set_doc(self, doc: Optional[str]) -> None:
        """Assign the given docstring to the property instance and, if possible,
        to the `__test__` dictionary of the module of its owner class."""
        if doc is not None:
            self.__doc__ = doc
            if hasattr(self, "module"):
                ref = f"{self.objtype.__name__}.{self.name}"
                self.module.__dict__["__test__"][ref] = doc

    def __set_name__(
        self,
        objtype: Type[Any],
        name: str,
    ) -> None:
        self.objtype = objtype
        self.module = inspect.getmodule(objtype)
        if self.module is not None:
            if not hasattr(self.module, "__test__"):
                self.module.__dict__["__test__"] = {}
        self.name = name
        doc = getattr(self, "__doc__")
        if doc:
            self.set_doc(doc)


class FGet(Protocol[OutputType_co]):
    """Callback protocol for getter functions."""

    def __call__(self, __obj: Any) -> OutputType_co:
        ...


class FSet(Protocol[InputType_contra]):
    """Callback protocol for setter functions."""

    def __call__(self, __obj: Any, __value: InputType_contra) -> None:
        ...


class FDel(Protocol):
    """Callback protocol for deleter functions."""

    def __call__(self, __obj: Any) -> None:
        ...


class BaseProperty(Generic[InputType, OutputType], BaseDescriptor):
    """Abstract base class for deriving classes similar to |property|.

    |BaseProperty| provides the abstract methods |BaseProperty.call_fget|,
    |BaseProperty.call_fset|, and |BaseProperty.call_fdel|, which are the
    appropriate places to add custom functionalities (e.g. caching).  See
    subclass |Property| for an example, which mimics the behaviour of the
    built-in |property| function.

    |BaseProperty| property uses dummy getter, setter and deleter functions
    to indicate than at an actual getter, setter or deleter function is missing.
    In case they are called due to the wrong implementation of a |BaseProperty|
    subclass, they raise a |RuntimeError|:

    >>> from hydpy.core.propertytools import BaseProperty
    >>> BaseProperty._fgetdummy(None)
    Traceback (most recent call last):
    ...
    RuntimeError

    >>> BaseProperty._fsetdummy(None, None)
    Traceback (most recent call last):
    ...
    RuntimeError

    >>> BaseProperty._fdeldummy(None)
    Traceback (most recent call last):
    ...
    RuntimeError
    """

    fget: FGet[OutputType]
    fset: FSet[InputType]
    fdel: FDel

    @staticmethod
    def _fgetdummy(__obj: Any) -> OutputType:
        raise RuntimeError

    @staticmethod
    def _fsetdummy(__obj: Any, __value: InputType) -> None:
        raise RuntimeError

    @staticmethod
    def _fdeldummy(__obj: Any) -> None:
        raise RuntimeError

    @overload
    def __get__(
        self, obj: None, objtype: Type[Any]
    ) -> BaseProperty[InputType, OutputType]:
        ...

    @overload
    def __get__(self, obj: Any, objtype: Type[Any]) -> OutputType:
        ...

    def __get__(
        self, obj: Optional[Any], objtype: Type[Any]
    ) -> Union[BaseProperty[InputType, OutputType], OutputType]:
        if obj is None:
            return self
        if self.fget is self._fgetdummy:
            raise AttributeError(
                f"Attribute `{self.name}` of object "
                f"{objecttools.devicephrase(obj)} is not gettable."
            )
        return self.call_fget(obj)

    def __set__(self, obj: Any, value: InputType) -> None:
        if self.fset is self._fsetdummy:
            raise AttributeError(
                f"Attribute `{self.name}` of object "
                f"{objecttools.devicephrase(obj)} is not settable."
            )
        self.call_fset(obj, value)

    def __delete__(self, obj: Any) -> None:
        if self.fdel is self._fdeldummy:
            raise AttributeError(
                f"Attribute `{self.name}` of object "
                f"{objecttools.devicephrase(obj)} is not deletable."
            )
        self.call_fdel(obj)

    @abc.abstractmethod
    def call_fget(self, obj: Any) -> OutputType:
        """Method for implementing unique getter functionalities."""

    @abc.abstractmethod
    def call_fset(self, obj: Any, value: InputType) -> None:
        """Method for implementing unique setter functionalities."""

    @abc.abstractmethod
    def call_fdel(self, obj: Any) -> None:
        """Method for implementing unique deleter functionalities."""


class Property(BaseProperty[InputType, OutputType]):
    """Class |Property| mimics the behaviour of the built-in function |property|.

    The only advantage of |Property| over |property| is that it allows defining
    different input and output types statically.  If the input and output types
    are identical, prefer |property|, which is probably faster.

    The following test class implements its attribute `x` by defining
    all three "property methods" (`getter`/`fget`, `setter`/`fset`,
    `deleter`/`fdel`), but its attribute `y` by defining none of them:

    >>> from hydpy.core.propertytools import Property
    >>> class Test:
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._y = None
    ...
    ...     @Property
    ...     def x(self):
    ...         return self._x
    ...     @x.setter
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter
    ...     def x(self):
    ...         self._x = None
    ...
    ...     y = Property()

    After initialising a test object, you can use its attribute `x` as expected:

    >>> test = Test()
    >>> test.x
    >>> test.x = 2
    >>> test.x
    2
    >>> del test.x
    >>> test.x

    When trying to invoke attribute `y`, you get the following error messages:

    >>> test.y
    Traceback (most recent call last):
    ...
    AttributeError: Attribute `y` of object `test` is not gettable.

    >>> test.y = 1
    Traceback (most recent call last):
    ...
    AttributeError: Attribute `y` of object `test` is not settable.

    >>> del test.y
    Traceback (most recent call last):
    ...
    AttributeError: Attribute `y` of object `test` is not deletable.
    """

    def __init__(
        self,
        fget: FGet[OutputType] = BaseProperty._fgetdummy,
        fset: FSet[InputType] = BaseProperty._fsetdummy,
        fdel: FDel = BaseProperty._fdeldummy,
    ) -> None:
        self.fget = fget
        self.set_doc(fget.__doc__)
        self.fset = fset
        self.fdel = fdel

    def call_fget(self, obj: Any) -> OutputType:
        """Call `fget` without additional functionalities."""
        return self.fget(obj)

    def call_fset(self, obj: Any, value: InputType) -> None:
        """Call `fset` without additional functionalities."""
        self.fset(obj, value)

    def call_fdel(self, obj: Any) -> None:
        """Call `fdel` without additional functionalities."""
        self.fdel(obj)

    def getter(self, fget: FGet[OutputType]) -> Property[InputType, OutputType]:
        """Add the given getter function and its docstring to the property and
        return it."""
        self.fget = fget
        self.set_doc(fget.__doc__)
        return self

    def setter(self, fset: FSet[InputType]) -> Property[InputType, OutputType]:
        """Add the given setter function to the property and return it."""
        self.fset = fset
        return self

    def deleter(self, fdel: FDel) -> Property[InputType, OutputType]:
        """Add the given deleter function to the property and return it."""
        setattr(self, "fdel", fdel)
        return self


class ProtectedProperty(BaseProperty[InputType, OutputType]):
    """A |property|-like class which prevents getting an attribute before setting it.

    Some attributes need preparations before being accessible.  Consider the case
    where a property of a Python class (being part of the API) links to an attribute
    of a Cython extension class (not part of the API).  If the Cython attribute is,
    for example, a vector requiring memory allocation, trying to query this vector
    before it has been initialised results in a program crash.  Using
    |ProtectedProperty| is a means to prevent such problems.

    The following class `Test` defines most simple getter, setter, and deleter
    functions for its only property `x`:

    >>> from hydpy.core.propertytools import ProtectedProperty
    >>> class Test:
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...
    ...     x = ProtectedProperty()
    ...     @x.getter
    ...     def x(self):
    ...         "Test"
    ...         return self._x
    ...     @x.setter
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter
    ...     def x(self):
    ...         self._x = None

    Trying to query `x` directly after initialising a `Test` object results in an
    |AttributeNotReady| error:

    >>> test = Test()
    >>> test.x
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `x` of object `test` \
has not been prepared so far.

    After setting a value, you can query this value as expected:

    >>> test.x = 1
    >>> test.x
    1

    After deleting the value, the protection mechanism applies again:

    >>> del test.x
    >>> test.x
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `x` of object `test` \
has not been prepared so far.
    """

    def __init__(
        self,
        fget: FGet[OutputType] = BaseProperty._fgetdummy,
        fset: FSet[InputType] = BaseProperty._fsetdummy,
        fdel: FDel = BaseProperty._fdeldummy,
    ) -> None:
        self.fget = fget
        self.set_doc(fget.__doc__)
        self.fset = fset
        self.fdel = fdel

    def call_fget(self, obj: Any) -> OutputType:
        """When ready, call `fget`; otherwise, raise an |AttributeNotReady|
        exception."""
        if self.isready(obj):
            return self.fget(obj)
        raise exceptiontools.AttributeNotReady(
            f"Attribute `{self.name}` of object {objecttools.devicephrase(obj)} "
            f"has not been prepared so far."
        )

    def call_fset(self, obj: Any, value: InputType) -> None:
        """Call `fset` and mark the attribute as ready."""
        self.fset(obj, value)
        vars(obj)[self.name] = True

    def call_fdel(self, obj: Any) -> None:
        """Call `fdel` and mark the attribute as not ready."""
        vars(obj)[self.name] = False
        self.fdel(obj)

    def isready(self, obj: Any) -> bool:
        """Return |True| or |False| to indicate if the protected
        property is ready for the given object.  If the object is
        unknown, |ProtectedProperty.isready| returns |False|."""
        return vars(obj).get(self.name, False)

    def getter(
        self, fget: FGet[OutputType]
    ) -> "ProtectedProperty[InputType, OutputType]":
        """Add the given getter function and its docstring to the property
        and return it."""
        self.fget = fget
        self.set_doc(fget.__doc__)
        return self

    def setter(self, fset: FSet[InputType]) -> ProtectedProperty[InputType, OutputType]:
        """Add the given setter function to the property and return it."""
        self.fset = fset
        return self

    def deleter(self, fdel: FDel) -> ProtectedProperty[InputType, OutputType]:
        """Add the given deleter function to the property and return it."""
        self.fdel = fdel
        return self


ProtectedPropertyStr = ProtectedProperty[str, str]
"""|ProtectedProperty| for handling |str| objects."""


class ProtectedProperties:
    """Iterable for |ProtectedProperty| objects.

    You can collect an arbitrary number of |ProtectedProperty| objects within a
    |ProtectedProperties| object.  Its |ProtectedProperties.allready| method
    allows checking the status of all properties at ones:

    >>> from hydpy.core import propertytools as pt
    >>> class Test:
    ...
    ...     @pt.ProtectedProperty
    ...     def x(self):
    ...         return "this is x"
    ...     @x.setter
    ...     def x(self, value):
    ...         pass
    ...
    ...     @pt.ProtectedProperty
    ...     def z(self):
    ...         return "this is z"
    ...     @z.setter
    ...     def z(self, value):
    ...         pass
    ...
    ...     protectedproperties = pt.ProtectedProperties(x, z)

    >>> test1 = Test()
    >>> test1.x = None
    >>> test2 = Test()
    >>> test2.x = None
    >>> test2.z = None
    >>> Test.protectedproperties.allready(test1)
    False
    >>> Test.protectedproperties.allready(test2)
    True
    """

    __properties: Tuple[ProtectedProperty[Any, Any], ...]

    def __init__(self, *properties: ProtectedProperty[Any, Any]) -> None:
        self.__properties = properties

    def allready(self, obj: Any) -> bool:
        """Return |True| or |False| to indicate whether all protected
        properties are ready or not."""
        for prop in self.__properties:
            if not prop.isready(obj):
                return False
        return True

    def __iter__(self) -> Iterator[ProtectedProperty[Any, Any]]:
        return self.__properties.__iter__()


class DependentProperty(BaseProperty[InputType, OutputType]):
    """|property|-like class which prevents accessing a dependent attribute
    before preparing certain other attributes.

    Please read the documentation on class |ProtectedProperty|, from which we
    take the following example.  `x` is a simple |ProtectedProperty| again,
    but time we add the |DependentProperty| `y`:

    >>> from hydpy.core import propertytools as pt
    >>> class Test:
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._y = None
    ...
    ...     @pt.ProtectedProperty
    ...     def x(self):
    ...         return self._x
    ...     @x.setter
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter
    ...     def x(self):
    ...         self._x = None
    ...
    ...     y = pt.DependentProperty(protected=(x,))
    ...
    ...     @y.getter
    ...     def y(self):
    ...         return self._y
    ...     @y.setter
    ...     def y(self, value):
    ...         self._y = value
    ...     @y.deleter
    ...     def y(self):
    ...         self._y = None

    Initially, due to `x` not being prepared, there is no way to get, set, or
    delete attribute `y`:

    >>> test = Test()
    >>> test.y
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `y` of object `test` \
is not usable so far.  At least, you have to prepare attribute `x` first.
    >>> test.y = 1
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `y` of object `test` \
is not usable so far.  At least, you have to prepare attribute `x` first.
    >>> del test.y
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `y` of object `test` \
is not usable so far.  At least, you have to prepare attribute `x` first.

    After assigning a value to `x`, `y` behaves like a common property:

    >>> test.x = "anything"
    >>> test.y = 1
    >>> test.y
    1
    >>> del test.y
    >>> test.y
    """

    protected: ProtectedProperties

    def __init__(
        self,
        protected: ProtectedProperties,
        fget: FGet[OutputType] = BaseProperty._fgetdummy,
        fset: FSet[InputType] = BaseProperty._fsetdummy,
        fdel: FDel = BaseProperty._fdeldummy,
    ) -> None:
        self.protected = protected
        self.fget = fget
        self.set_doc(fget.__doc__)
        self.fset = fset
        self.fdel = fdel

    def __check(self, obj: Any) -> None:
        for req in self.protected:
            if not req.isready(obj):
                raise exceptiontools.AttributeNotReady(
                    f"Attribute `{self.name}` of object "
                    f"{objecttools.devicephrase(obj)} is not usable "
                    f"so far.  At least, you have to prepare attribute "
                    f"`{req.name}` first."
                )

    def call_fget(self, obj: Any) -> OutputType:
        """Call `fget` when all required attributes are ready; otherwise, raise
        an |AttributeNotReady| error."""
        self.__check(obj)
        return self.fget(obj)

    def call_fset(self, obj: Any, value: InputType) -> None:
        """Call `fset` when all required attributes are ready; otherwise, raise
        an |AttributeNotReady| error."""
        self.__check(obj)
        self.fset(obj, value)

    def call_fdel(self, obj: Any) -> None:
        """Call `fdel` when all required attributes are ready; otherwise, raise
        an |AttributeNotReady| error."""
        self.__check(obj)
        self.fdel(obj)

    def getter(
        self, fget: FGet[OutputType]
    ) -> DependentProperty[InputType, OutputType]:
        """Add the given getter function and its docstring to the property and
        return it."""
        self.fget = fget
        self.set_doc(fget.__doc__)
        return self

    def setter(self, fset: FSet[InputType]) -> DependentProperty[InputType, OutputType]:
        """Add the given setter function to the property and return it."""
        self.fset = fset
        return self

    def deleter(self, fdel: FDel) -> DependentProperty[InputType, OutputType]:
        """Add the given deleter function to the property and return it."""
        self.fdel = fdel
        return self


class DefaultProperty(BaseProperty[InputType, OutputType]):
    """|property|-like class which uses the getter function to return a default
    value unless a custom value is available.

    In the following example, the default value of property `x` is one:

    >>> from hydpy.core.propertytools import DefaultProperty
    >>> class Test:
    ...
    ...     @DefaultProperty
    ...     def x(self):
    ...         "Default property x."
    ...         return 1

    Initially, property `x` returns the default value defined by its getter function:

    >>> test = Test()
    >>> test.x
    1

    Assigned custom values override such default values:

    >>> test.x = 3
    >>> test.x
    3

    After removing the custom value, it is again up to the getter function to return
    the default value:

    >>> del test.x
    >>> test.x
    1

    Trying to delete a not existing custom value does not harm:

    >>> del test.x

    The documentation string of the getter functions serves as the documentation
    string of the default property:

    >>> Test.x.__doc__
    'Default property x.'
    """

    def __init__(self, fget: FGet[OutputType] = BaseProperty._fgetdummy) -> None:
        self.fget = fget
        self.set_doc(fget.__doc__)
        self.fset = self._fsetowndummy
        self.fdel = self._fdelowndummy

    def call_fget(self, obj: Any) -> OutputType:
        """If available, return the predefined custom value; otherwise, return
        the value defined by the getter function."""
        value = cast(Optional[OutputType], vars(obj).get(self.name))
        if value is None:
            return self.fget(obj)
        return value

    def call_fset(self, obj: Any, value: InputType) -> None:
        """Store the given custom value."""
        vars(obj)[self.name] = value

    def call_fdel(self, obj: Any) -> None:
        """Remove the predefined custom value."""
        try:
            del vars(obj)[self.name]
        except KeyError:
            pass

    @staticmethod
    def _fsetowndummy(__obj: Any, __value: InputType) -> None:
        """Do nothing."""

    @staticmethod
    def _fdelowndummy(__obj: Any) -> None:
        """Do nothing."""


DefaultPropertyStr = DefaultProperty[str, str]
"""|DefaultProperty| for handling |str| objects."""
