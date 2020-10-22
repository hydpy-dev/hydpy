# -*- coding: utf-8 -*-
"""This module implements |property| like classes with similar or
additional behaviour."""

# import...
# ...from standard-library
import abc
import inspect
import types
from typing import *
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools

InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')


def fgetdummy(*args):
    """The "unready" default `fget` function of class |BaseProperty| objects.

    If any, only framework developers should ever encounter the following
    error when implementing new costum properties:

    >>> from hydpy.core.propertytools import fgetdummy
    >>> fgetdummy('arg1')
    Traceback (most recent call last):
    ...
    NotImplementedError: The "unready" default `fget` function `fgetdummy` \
should never been called, but has been called with argument(s): arg1.
    """
    raise NotImplementedError(
        f'The "unready" default `fget` function `fgetdummy` should '
        f'never been called, but has been called with argument(s): '
        f'{objecttools.enumeration(args)}.')


def fsetdummy(*args):
    """The "unready" default `fget` function of class |BaseProperty| objects.

    If any, only framework developers should ever encounter the following
    error when implementing new costum properties:

    >>> from hydpy.core.propertytools import fsetdummy
    >>> fsetdummy('arg1', 'arg2')
    Traceback (most recent call last):
    ...
    NotImplementedError: The "unready" default `fset` function `fsetdummy` \
should never been called, but has been called with argument(s): arg1 and arg2.
    """
    raise NotImplementedError(
        f'The "unready" default `fset` function `fsetdummy` should '
        f'never been called, but has been called with argument(s): '
        f'{objecttools.enumeration(args)}.')


def fdeldummy(*args):
    """The "unready" default `fget` function of class |BaseProperty| objects.

    If any, only framework developers should ever encounter the following
    error when implementing new costum properties:

    >>> from hydpy.core.propertytools import fdeldummy
    >>> fdeldummy('arg1')
    Traceback (most recent call last):
    ...
    NotImplementedError: The "unready" default `fdel` function `fdeldummy` \
should never been called, but has been called with argument(s): arg1.
    """
    raise NotImplementedError(
        f'The "unready" default `fdel` function `fdeldummy` should '
        f'never been called, but has been called with argument(s): '
        f'{objecttools.enumeration(args)}.')


class BaseProperty(Generic[InputType, OutputType]):
    # noinspection PyUnresolvedReferences
    """Abstract base class for deriving classes similar to |property|.

    |BaseProperty| provides the abstract methods |BaseProperty.call_fget|,
    |BaseProperty.call_fset|, and |BaseProperty.call_fdel|, which allow
    to add custom functionalities (e.g. caching) besides the standard
    functionalities of properties.  The following concrete class mimics
    the behaviour of class |property|:

    >>> from hydpy.core.propertytools import fgetdummy, fsetdummy, fdeldummy
    >>> class ConcreteProperty(BaseProperty):
    ...
    ...     def __init__(self, fget=fgetdummy):
    ...         self.fget = fget
    ...         self.__doc__ = fget.__doc__
    ...         self.fset = fsetdummy
    ...         self.fdel = fdeldummy
    ...
    ...     def call_fget(self, obj):
    ...         return self.fget(obj)
    ...     def call_fset(self, obj, value):
    ...         self.fset(obj, value)
    ...     def call_fdel(self, obj):
    ...         self.fdel(obj)

    The following owner class implements its attribute `x` by defining
    all three "property methods" (`getter`/`fget`, `setter`/`fset`,
    `deleter`/`fdel`), but its attribute `y` by defining none of them:

    >>> class Owner:
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._y = None
    ...
    ...     @ConcreteProperty
    ...     def x(self):
    ...         return self._x
    ...     @x.setter
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter
    ...     def x(self):
    ...         self._x = None
    ...
    ...     y = ConcreteProperty()

    After initialising an owner object, you can use its attribute `x`
    as expected:

    >>> owner = Owner()
    >>> owner.x
    >>> owner.x = 2
    >>> owner.x
    2
    >>> del owner.x
    >>> owner.x

    Invoking attribute `y` results in the following error messages:

    >>> owner.y
    Traceback (most recent call last):
    ...
    AttributeError: Attribute `y` of object `owner` is not gettable.
    >>> owner.y = 1
    Traceback (most recent call last):
    ...
    AttributeError: Attribute `y` of object `owner` is not settable.
    >>> del owner.y
    Traceback (most recent call last):
    ...
    AttributeError: Attribute `y` of object `owner` is not deletable.
    """

    fget: Callable
    fset: Callable
    fdel: Callable
    objtype: Any
    module: Optional[types.ModuleType]
    name: str
    __doc__: str

    def __set_name__(self, objtype, name) -> None:
        self.objtype: Any = objtype
        self.module = inspect.getmodule(objtype)
        if self.module is not None:
            if not hasattr(self.module, '__test__'):
                self.module.__dict__['__test__'] = dict()
        self.name: str = name
        doc = getattr(self, '__doc__')
        if doc:
            self.set_doc(doc)

    @overload
    def __get__(self, obj: None, objtype) -> 'BaseProperty':
        """get the property"""

    @overload
    def __get__(self, obj, objtype) -> OutputType:
        """get the value"""

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is fgetdummy:
            raise AttributeError(
                f'Attribute `{self.name}` of object '
                f'{objecttools.devicephrase(obj)} is not gettable.')
        return self.call_fget(obj)

    def __set__(self, obj, value: InputType) -> None:
        if self.fset is fsetdummy:
            raise AttributeError(
                f'Attribute `{self.name}` of object '
                f'{objecttools.devicephrase(obj)} is not settable.')
        self.call_fset(obj, value)

    def __delete__(self, obj) -> None:
        if self.fdel is fdeldummy:
            raise AttributeError(
                f'Attribute `{self.name}` of object '
                f'{objecttools.devicephrase(obj)} is not deletable.')
        self.call_fdel(obj)

    def set_doc(self, doc: str):
        """Assign the given docstring to the property instance and, if
        possible, to the `__test__` dictionary of the module of its
        owner class."""
        self.__doc__ = doc
        if hasattr(self, 'module'):
            ref = f'{self.objtype.__name__}.{self.name}'
            self.module.__dict__['__test__'][ref] = doc

    @abc.abstractmethod
    def call_fget(self, obj) -> OutputType:
        """Method for implementing special getter functionalities."""

    @abc.abstractmethod
    def call_fset(self, obj, value: InputType) -> None:
        """Method for implementing special setter functionalities."""

    @abc.abstractmethod
    def call_fdel(self, obj) -> None:
        """Method for implementing special deleter functionalities."""

    def getter(self, fget: Callable) -> 'BaseProperty':
        """Add the given getter function and its docstring to the
         property and return it."""
        setattr(self, 'fget', fget)
        self.set_doc(getattr(fget, '__doc__'))
        return self

    def setter(self, fset: Callable) -> 'BaseProperty':
        """Add the given setter function to the property and return it."""
        setattr(self, 'fset', fset)
        return self

    def deleter(self, fdel: Callable) -> 'BaseProperty':
        """Add the given deleter function to the property and return it."""
        setattr(self, 'fdel', fdel)
        return self


class ProtectedProperty(BaseProperty[InputType, OutputType]):
    # noinspection PyUnresolvedReferences
    """|property| like class which prevents getting an attribute
    before setting it.

    Under some circumstances, an attribute value needs to be prepared
    before one should be allowed to query it.  Consider the case where
    a property of a Python class (beeing part of the API) links to an
    attribute of a Cython extension class (not part of the API).  If
    the Cython attribute is e.g. some type of vector requiring memory
    allocation, trying to query this vector befor it has actually been
    prepared results in a programm crash.  Using |ProtectedProperty|
    is a means to prevent from such problems to occur.

    Consider the following class `Test`, which defines most simple
    `set`, `get`, and `del` methods for its only property `x`:

    >>> from hydpy.core.propertytools import ProtectedProperty
    >>> class Test:
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...
    ...     @ProtectedProperty
    ...     def x(self):
    ...         "Test"
    ...         return self._x
    ...     @x.setter
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter
    ...     def x(self):
    ...         self._x = None

    Due to using |ProtectedProperty| instead of |property|, trying
    to query `x` after initializing a `Test` object results in an
    |AttributeNotReady| error:

    >>> test = Test()
    >>> test.x
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `x` of object \
`test` has not been prepared so far.

    After setting a value for property `x`, this value can be queried
    as expected:

    >>> test.x = 1
    >>> test.x
    1

    After deleting `x`, its value is not accessible, again:

    >>> del test.x
    >>> test.x
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `x` of object \
`test` has not been prepared so far.

    If the considered object defines a name (different from the class
    name in lower letters) and/or references a |Node| or |Element|
    object (directly or indirectly), the exception message includes this
    additional information:

    >>> from hydpy import Element
    >>> test.name = 'name_object'
    >>> test.element = Element('name_element')

    >>> test.x
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `x` of object \
`name_object` of element `name_element` has not been prepared so far.
    """

    def __init__(self, fget=fsetdummy):
        self.fget = fget
        self.set_doc(fget.__doc__)
        self.fset = fsetdummy
        self.fdel = fdeldummy

    def call_fget(self, obj) -> OutputType:
        """Call `fget` when ready, otherwise raise an exception."""
        if self.isready(obj):
            return self.fget(obj)
        raise exceptiontools.AttributeNotReady(
            f'Attribute `{self.name}` of object '
            f'{objecttools.devicephrase(obj)} has not been prepared so far.')

    def call_fset(self, obj, value: InputType) -> None:
        """Call `fset` and mark the attribute as ready."""
        self.fset(obj, value)
        vars(obj)[self.name] = True

    def call_fdel(self, obj) -> None:
        """Call `fdel` and mark the attribute as not ready."""
        vars(obj)[self.name] = False
        self.fdel(obj)

    def isready(self, obj) -> bool:
        """Return |True| or |False| to indicate if the protected
        property is ready for the given object.  If the object is
        unknow, |ProtectedProperty| returns |False|."""
        return vars(obj).get(self.name, False)


class ProtectedPropertyStr(ProtectedProperty[str, str]):
    """|ProtectedProperty| for handling |str| objects."""


class ProtectedProperties:
    # noinspection PyUnresolvedReferences
    """Iterable for |ProtectedProperty| objects.

    You can combine an arbitrary number of |ProtectedProperty| objects
    with a |ProtectedProperties| objects.  Its |ProtectedProperties.allready|
    allows to check if the status of all properties at ones:

    >>> from hydpy.core import propertytools as pt
    >>> class Test:
    ...
    ...     @pt.ProtectedProperty
    ...     def x(self):
    ...         return 'this is x'
    ...     @x.setter
    ...     def x(self, value):
    ...         pass
    ...
    ...     @pt.ProtectedProperty
    ...     def z(self):
    ...         return 'this is z'
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

    def __init__(self, *properties: ProtectedProperty):
        self.__properties = properties

    def allready(self, obj) -> bool:
        """Return |True| or |False| to indicate whether all protected
        properties are ready or not."""
        for prop in self.__properties:
            if not prop.isready(obj):
                return False
        return True

    def __iter__(self):
        return self.__properties.__iter__()


class DependentProperty(BaseProperty[InputType, OutputType]):
    # noinspection PyUnresolvedReferences
    """|property| like class which prevents accessing a dependent
    attribute before other attributes have been prepared.

    The following explanations suppose first reading the documentation
    on function |ProtectedProperty|.  The following example builds on
    the one on class |ProtectedProperty|, but adds the dependent property,
    which requires the protected property `x` to be properly prepared:

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

    Initially, due to `x` beeing not prepared, there is no way to get,
    set, or delete attribute `y`:

    >>> test = Test()
    >>> test.y
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `y` of \
object `test` is not usable so far.  At least, you have to prepare \
attribute `x` first.
    >>> test.y = 1
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `y` of \
object `test` is not usable so far.  At least, you have to prepare \
attribute `x` first.
    >>> del test.y
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `y` of \
object `test` is not usable so far.  At least, you have to prepare \
attribute `x` first.

    However, after assigning a value to `x`, `y` behaves like a
    "normal" property:

    >>> test.x = 'anything'
    >>> test.y = 1
    >>> test.y
    1
    >>> del test.y
    >>> test.y
    """

    def __init__(self, protected):
        self.protected = protected
        self.fget = fgetdummy
        self.fset = fsetdummy
        self.fdel = fdeldummy

    def __check(self, obj) -> None:
        for req in self.protected:
            if not req.isready(obj):
                raise exceptiontools.AttributeNotReady(
                    f'Attribute `{self.name}` of object '
                    f'{objecttools.devicephrase(obj)} is not usable '
                    f'so far.  At least, you have to prepare attribute '
                    f'`{req.name}` first.')

    def call_fget(self, obj) -> OutputType:
        """Call `fget` when all required attributes are ready,
        otherwise raise an |AttributeNotReady| error."""
        self.__check(obj)
        return self.fget(obj)

    def call_fset(self, obj, value: InputType) -> None:
        """Call `fset` when all required attributes are ready,
        otherwise raise an |AttributeNotReady| error."""
        self.__check(obj)
        self.fset(obj, value)

    def call_fdel(self, obj) -> None:
        """Call `fdel` when all required attributes are ready,
        otherwise raise an |AttributeNotReady| error."""
        self.__check(obj)
        self.fdel(obj)


class DefaultProperty(BaseProperty[InputType, OutputType]):
    # noinspection PyUnresolvedReferences
    """|property| like class which uses the getter function to return
    a default value unless a custom value is available.

    The following example includes two default properties.  Default
    property `x` implements only the required default getter
    function, default property `y` additionally implements a setter
    and a delete function with value checks:

    >>> from hydpy.core.propertytools import DefaultProperty
    >>> class Test:
    ...
    ...     @DefaultProperty
    ...     def x(self):
    ...         "Default property x."
    ...         return 1
    ...
    ...     @DefaultProperty
    ...     def y(self):
    ...         "Default property y."
    ...         return 2.0
    ...     @y.setter
    ...     def y(self, value):
    ...         return float(value)
    ...     @y.deleter
    ...     def y(self):
    ...         if self.y == 4.0:
    ...             raise RuntimeError

    Initially, both properties return the default values defined by
    their getter functions:

    >>> test = Test()
    >>> test.x
    1
    >>> test.y
    2.0

    After setting custom values successfully, default properties return them:

    >>> test.x = 3
    >>> test.y = 'five'
    Traceback (most recent call last):
    ...
    ValueError: could not convert string to float: 'five'
    >>> test.x
    3
    >>> test.y
    2.0
    >>> test.y = '4'
    >>> test.y
    4.0

    After deleting these custom values successfully, the getter functions
    are again used to return default values:

    >>> del test.x
    >>> del test.y
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> test.x
    1
    >>> test.y
    4.0
    >>> test.y = 5.0
    >>> del test.y
    >>> test.y
    2.0

    Trying to delete a not existing custom value does not harm:

    >>> del test.x
    >>> del test.y

    The documentation strings of the getter functions serve as documentation
    strings of the respective default properties:

    >>> Test.x.__doc__
    'Default property x.'
    >>> Test.y.__doc__
    'Default property y.'
    """

    def __init__(self, fget):
        self.fget = fget
        self.fset = self._fset
        self.fdel = self._fdel
        self.set_doc(fget.__doc__)

    def call_fget(self, obj) -> OutputType:
        """Return the predefined custom value when available, otherwise,
        the value defined by the getter function."""
        custom = vars(obj).get(self.name)
        if custom is None:
            return self.fget(obj)
        return custom

    def call_fset(self, obj, value: InputType) -> None:
        """Store the given custom value and call the setter function."""
        vars(obj)[self.name] = self.fset(obj, value)

    def call_fdel(self, obj) -> None:
        """Remove the predefined custom value and call the delete function."""
        self.fdel(obj)
        try:
            del vars(obj)[self.name]
        except KeyError:
            pass

    @staticmethod
    def _fset(_, value) -> Any:
        """Just return the given value."""
        return value

    def _fdel(self, obj) -> None:
        """Do nothing."""


class DefaultPropertyStr(DefaultProperty[str, str]):
    """|DefaultProperty| for handling |str| objects."""
