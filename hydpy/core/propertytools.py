# -*- coding: utf-8 -*-
"""This module implements |property| like classes with similar or
additional behaviour."""

# import...
# ...from standard-library
from typing import *
import abc
import weakref
# ...from HydPy
from hydpy.core import autodoctools
from hydpy.core import exceptiontools
from hydpy.core import objecttools


class BaseProperty(object, metaclass=abc.ABCMeta):
    """Abstract base class for deriving classes similar to |property|.

    |BaseProperty| provides the abstract methods |BaseProperty.call_fget|,
    |BaseProperty.call_fset|, and |BaseProperty.call_fdel|, which allow
    to add custom functionalities (e.g. caching) besides the standard
    functionalities of properties:

    >>> from hydpy.core.propertytools import BaseProperty
    >>> BaseProperty()
    Traceback (most recent call last):
    ...
    TypeError: Can't instantiate abstract class BaseProperty with abstract \
methods call_fdel, call_fget, call_fset

    The following concrete class mimics the behaviour of class |property|:

    >>> class ConcreteProperty(BaseProperty):
    ...
    ...     def __init__(self, fget=None):
    ...         self.fget = fget
    ...         self.__doc__ = fget.__doc__
    ...         self.fset = None
    ...         self.fdel = None
    ...
    ...     def call_fget(self, obj):
    ...         return self.fget(obj)
    ...     def call_fset(self, obj, value):
    ...         self.fset(obj, value)
    ...     def call_fdel(self, obj):
    ...         self.fdel(obj)

    The following owner class implements its attribute `x` by defining
    all three "property methods" (`getter_`/`fget`, `setter_`/`fset`,
    `deleter_`/`fdel`), but its attribute `y` by defining none of them:

    >>> class Owner(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._y = None
    ...
    ...     @ConcreteProperty
    ...     def x(self):
    ...         return self._x
    ...     @x.setter_
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter_
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
    AttributeError: Attribute `y` of object `owner` is not deleteable.
    """

    fget: Callable
    fset: Callable
    fdel: Callable

    def __set_name__(self, objtype, name) -> None:
        self.objtype: Any = objtype
        self.name: str = name

    def __get__(self, obj, objtype=None) -> Any:
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError(
                'Attribute `%s` of object %s is not gettable.'
                % (self.name, objecttools.devicephrase(obj)))
        return self.call_fget(obj)

    def __set__(self, obj, value) -> None:
        if self.fset is None:
            raise AttributeError(
                'Attribute `%s` of object %s is not settable.'
                % (self.name, objecttools.devicephrase(obj)))
        self.call_fset(obj, value)

    def __delete__(self, obj) -> None:
        if self.fdel is None:
            raise AttributeError(
                'Attribute `%s` of object %s is not deleteable.'
                % (self.name, objecttools.devicephrase(obj)))
        self.call_fdel(obj)

    @abc.abstractmethod
    def call_fget(self, obj) -> Any:
        """Method for implementing special getter functionalities."""

    @abc.abstractmethod
    def call_fset(self, obj, value) -> None:
        """Method for implementing special setter functionalities."""

    @abc.abstractmethod
    def call_fdel(self, obj) -> None:
        """Method for implementing special deleter functionalities."""

    def getter_(self, fget) -> 'BaseProperty':
        """Add the given getter function and its docstring to the
         property and return it."""
        self.fget = fget
        self.__doc__ = fget.__doc__
        return self

    def setter_(self, fset) -> 'BaseProperty':
        """Add the given setter function to the property and return it."""
        self.fset = fset
        return self

    def deleter_(self, fdel) -> 'BaseProperty':
        """Add the given deleter function to the property and return it."""
        self.fdel = fdel
        return self


class ProtectedProperty(BaseProperty):
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
    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...
    ...     @ProtectedProperty
    ...     def x(self):
    ...         "Test"
    ...         return self._x
    ...     @x.setter_
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter_
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

    def __init__(self, fget=None):
        self.fget = fget
        self.__doc__ = fget.__doc__
        self.fset = None
        self.fdel = None
        self.__obj2ready = weakref.WeakKeyDictionary()

    def call_fget(self, obj) -> Any:
        if self.isready(obj):
            return self.fget(obj)
        raise exceptiontools.AttributeNotReady(
            'Attribute `%s` of object %s has not been prepared so far.'
            % (self.name, objecttools.devicephrase(obj)))

    def call_fset(self, obj, value) -> None:
        self.fset(obj, value)
        self.__obj2ready[obj] = True

    def call_fdel(self, obj) -> None:
        self.__obj2ready[obj] = False
        self.fdel(obj)

    def isready(self, obj) -> bool:
        """Return |True| or |False| to indicate if the protected
        property is ready for the given object.  If the object is
        unknow, |ProtectedProperty| returns |False|."""
        return self.__obj2ready.get(obj, False)

    def copy(self, old_obj, new_obj) -> None:   # ToDo remove?
        """Assume the same readiness of the old object than for tne
        new object.  If the old object is unknown, assume the new one
        is not ready."""
        self.__obj2ready[new_obj] = self.__obj2ready.get(old_obj, False)


class ProtectedProperties(object):
    """Iterable for |ProtectedProperty| objects.

    You can combine an arbitrary number of |ProtectedProperty| objects
    with a |ProtectedProperties| objects.  Its |ProtectedProperties.allready|
    allows to check if the status of all properties at ones:

    >>> from hydpy.core import propertytools as pt
    >>> class Test(object):
    ...
    ...     @pt.ProtectedProperty
    ...     def x(self):
    ...         return 'this is x'
    ...     @x.setter_
    ...     def x(self, value):
    ...         pass
    ...
    ...     @pt.ProtectedProperty
    ...     def z(self):
    ...         return 'this is z'
    ...     @z.setter_
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


class DependentProperty(BaseProperty):
    """|property| like class which prevents accessing a dependent
    attribute before other attributes have been prepared.

    The following explanations suppose first reading the documentation
    on function |ProtectedProperty|.  The following e^xample builds on
    the one on class |ProtectedProperty|, but adds the dependent property,
    which requires the protected property `x` to be properly prepared:

    >>> from hydpy.core import propertytools as pt
    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._y = None
    ...
    ...     @pt.ProtectedProperty
    ...     def x(self):
    ...         return self._x
    ...     @x.setter_
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter_
    ...     def x(self):
    ...         self._x = None
    ...
    ...     y = pt.DependentProperty(
    ...         name='y', protected=(x,))
    ...
    ...     @y.getter_
    ...     def y(self):
    ...         return self._y
    ...     @y.setter_
    ...     def y(self, value):
    ...         self._y = value
    ...     @y.deleter_
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

    def __init__(self, name, protected):
        self.name = name
        self.protected = protected
        self.fget = None
        self.fset = None
        self.fdel = None

    def __check(self, obj) -> None:
        for req in self.protected:
            if not req.isready(obj):
                raise exceptiontools.AttributeNotReady(
                    'Attribute `%s` of object %s is not usable so far.  '
                    'At least, you have to prepare attribute `%s` first.'
                    % (self.name, objecttools.devicephrase(obj), req.name))

    def call_fget(self, obj) -> Any:
        self.__check(obj)
        return self.fget(obj)

    def call_fset(self, obj, value) -> None:
        self.__check(obj)
        self.fset(obj, value)

    def call_fdel(self, obj) -> None:
        self.__check(obj)
        self.fdel(obj)


class DefaultProperty(BaseProperty):
    """|property| like class which uses the getter function to return
    a default value unless a custom value is available.

    The following example includes two default properties.  Default
    property `x` implements only the required default getter
    function, default property `y` additionally implements a setter
    and a delete function with value checks:

    >>> from hydpy.core.propertytools import DefaultProperty
    >>> class Test(object):
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
    ...     @y.setter_
    ...     def y(self, value):
    ...         return float(value)
    ...     @y.deleter_
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
        self.__doc__ = fget.__doc__

    def call_fget(self, obj) -> Any:
        """Return the predefined custom value when available, otherwise,
        the value defined by the getter function."""
        custom = vars(obj).get(self.name)
        if custom is None:
            return self.fget(obj)
        return custom

    def call_fset(self, obj, value) -> None:
        """Store the given custom value and call the setter function."""
        vars(obj)[self.name] = self.fset(obj, value)

    def call_fdel(self, obj) -> None:
        """Remove the predefined custom value and call the delete function."""
        self.fdel(obj)
        try:
            del vars(obj)[self.name]
        except KeyError:
            pass

    def _fset(self, obj, value) -> Any:
        """Just return the given value."""
        return value

    def _fdel(self, obj) -> None:
        """Do nothing."""


autodoctools.autodoc_module()
