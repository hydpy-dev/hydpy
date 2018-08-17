# -*- coding: utf-8 -*-
"""This module implements some exception classes and related features."""

# import...
# ...from standard library
import weakref
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools


class HydPyDeprecationWarning(DeprecationWarning):
    """Warning for deprecated HydPy features."""
    pass


class AttributeNotReady(AttributeError):
    """The attribute is principally defined, but must be prepared first."""


class ProtectedProperty(property):
    """|property| subclass which prevents getting an attribute
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

    >>> from hydpy.core.exceptiontools import ProtectedProperty
    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...
    ...     x = ProtectedProperty(name='x')
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

    Note that allowing for deep copying requires a specialized
    `__deepcopy__` method, which calls method |ProtectedProperty.copy|:

    >>> import copy
    >>> class Copyable(Test):
    ...
    ...     def __deepcopy__(self, memodict):
    ...         new = type(self)()
    ...         new.__dict__ = copy.deepcopy(self.__dict__, memodict)
    ...         Test.__dict__['x'].copy(self, new)
    ...         return new
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name='?'):
        self.name = name
        self.__obj2ready = weakref.WeakKeyDictionary()
        super().__init__(fget, fset, fdel, doc)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.isready(obj):
            return super().__get__(obj, objtype)
        raise AttributeNotReady(
            'Attribute `%s` of object %s has not been prepared so far.'
            % (self.name, objecttools.devicephrase(obj)))

    def __set__(self, obj, value):
        super().__set__(obj, value)
        self.__obj2ready[obj] = True

    def __delete__(self, obj):
        self.__obj2ready[obj] = False
        super().__delete__(obj)

    def getter(self, fget) -> 'ProtectedProperty':
        """Change the getter on a protected property."""
        new = type(self)(
            fget=fget, fset=self.fset, fdel=self.fdel, name=self.name)
        new.__doc__ = fget.__doc__
        return new

    def setter(self, fset) -> 'ProtectedProperty':
        """Change the setter on a protected property."""
        new = type(self)(
            fget=self.fget, fset=fset, fdel=self.fdel, name=self.name)
        new.__doc__ = self.__doc__
        return new

    def deleter(self, fdel) -> 'ProtectedProperty':
        """Change the deleter on a protected property."""
        new = type(self)(
            fget=self.fget, fset=self.fset, fdel=fdel, name=self.name)
        new.__doc__ = self.__doc__
        return new

    def isready(self, obj) -> bool:
        """Return |True| or |False| to indicate if the protected
        property is ready for the given object.  If the object is
        unknow, |ProtectedProperty| returns |False|."""
        return self.__obj2ready.get(obj, False)

    def copy(self, old_obj, new_obj):
        """Assume the same readiness of the old object than for tne
        new object.  If the old object is unknown, assume the new one
        is not ready."""
        self.__obj2ready[new_obj] = self.__obj2ready.get(old_obj, False)


class ProtectedProperties(object):
    """Iterable for |ProtectedProperty| objects.

    >>> from hydpy.core import exceptiontools as exct
    >>> class Test(object):
    ...
    ...     x = exct.ProtectedProperty(name='x')
    ...     @x.getter
    ...     def x(self):
    ...         return 'this is x'
    ...     @x.setter
    ...     def x(self, value):
    ...         pass
    ...
    ...     z = exct.ProtectedProperty(name='z')
    ...     @z.getter
    ...     def z(self):
    ...         return 'this is z'
    ...     @z.setter
    ...     def z(self, value):
    ...         pass
    ...
    ...     protectedproperties = exct.ProtectedProperties(x, z)

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

    def __init__(self, *properties):
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


class DependentProperty(property):
    """|property| subclass which prevents accessing a dependent attribute
    before other attributes have been prepared.

    The following explanations suppose first reading the documentation
    on function |ProtectedProperty|.  The following example builds on
    the one on class |ProtectedProperty|, but adds the dependent property,
    which requires the protected property `x` to be properly prepared:

    >>> from hydpy.core import exceptiontools as exct
    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._y = None
    ...
    ...     x = exct.ProtectedProperty(name='x')
    ...     @x.getter
    ...     def x(self):
    ...         return self._x
    ...     @x.setter
    ...     def x(self, value):
    ...         self._x = value
    ...     @x.deleter
    ...     def x(self):
    ...         self._x = None
    ...
    ...     y = exct.DependentProperty(name='y', protected=(x,))
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

    However, after assigning a vlaue to `y`, `x` behaves like a
    "normal" property:

    >>> test.x = 'anything'
    >>> test.y = 1
    >>> test.y
    1
    >>> del test.y
    >>> test.y
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None,
                 name='?', protected=()):
        self.name = name
        self.__protected = protected
        super().__init__(fget, fset, fdel, doc)

    def __check(self, obj):
        for req in self.__protected:
            if not req.isready(obj):
                raise AttributeNotReady(
                    'Attribute `%s` of object %s is not usable so far.  '
                    'At least, you have to prepare attribute `%s` first.'
                    % (self.name, objecttools.devicephrase(obj),
                       req.name))

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        self.__check(obj)
        return super().__get__(obj, objtype)

    def __set__(self, obj, value):
        self.__check(obj)
        return super().__set__(obj, value)

    def __delete__(self, obj):
        self.__check(obj)
        return super().__delete__(obj)

    def getter(self, fget):
        """Change the getter on a dependent property."""
        new = type(self)(
            fget=fget, fset=self.fset, fdel=self.fdel,
            name=self.name, protected=self.__protected)
        new.__doc__ = fget.__doc__
        return new

    def setter(self, fset):
        """Change the setter on a dependent property."""
        new = type(self)(
            fget=self.fget, fset=fset, fdel=self.fdel,
            name=self.name, protected=self.__protected)
        new.__doc__ = self.__doc__
        return new

    def deleter(self, fdel):
        """Change the deleter on a dependent property."""
        new = type(self)(
            fget=self.fget, fset=self.fset, fdel=fdel,
            name=self.name, protected=self.__protected)
        new.__doc__ = self.__doc__
        return new


class OptionalModuleNotAvailable(ImportError):
    """A `HydPy` function requiring an optional module is called, but this
    module is not available."""


class OptionalImport(object):
    """Exectutes the given import commands sequentially and returns the
    first importable module.  If no module could be imported at all, it
    returns a dummy object which raises a |OptionalModuleNotAvailable|
    each time a one tries to access a member of the original module.

    If a module is availabe:

    >>> from hydpy.core.exceptiontools import OptionalImport
    >>> numpy = OptionalImport(
    ...     'numpy',
    ...     ['import numpie', 'import numpy', 'import os'])
    >>> numpy.nan
    nan

    If no module is not available:

    >>> numpie = OptionalImport('numpie', ['import numpie'])
    >>> numpie.nan
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.OptionalModuleNotAvailable: HydPy could not \
load module `numpie`.  This module is no general requirement but \
necessary for some specific functionalities.

    If the module is available, but HydPy had been bundled to an
    executable:

    >>> from hydpy import pub
    >>> pub._is_hydpy_bundled = True
    >>> os = OptionalImport('os', 'import os')
    >>> os.getcwd()
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.OptionalModuleNotAvailable: HydPy could not \
load module `os`.  This module is no general requirement but necessary \
for some specific functionalities.

    The latter can be prevented by passing a `True` `bundle_module`
    argument:

    >>> textwrap = OptionalImport(
    ...     'textwrap', ['import textwrap'], bundle_module=True)
    >>> textwrap.wrap('')
    []

    >>> pub._is_hydpy_bundled = False
    """

    def __new__(cls, name, commands, bundle_module=False):
        if pub._is_hydpy_bundled and not bundle_module:
            return object.__new__(cls)
        for command in commands:
            try:
                exec(command)
                return eval(command.split()[-1])
            except BaseException:
                pass
        return object.__new__(cls)

    def __init__(self, name, commands, bundle_module=False):
        self.name = name

    def __getattr__(self, name):
        raise OptionalModuleNotAvailable(
            'HydPy could not load module `%s`.  This module is no '
            'general requirement but necessary for some specific '
            'functionalities.'
            % self.name)


autodoctools.autodoc_module()
