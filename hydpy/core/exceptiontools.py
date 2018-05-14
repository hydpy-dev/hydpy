# -*- coding: utf-8 -*-
"""This module implements some exception classes and related features."""

# import...
# ...from site-packages
import wrapt
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools


class AttributeNotReady(AttributeError):
    """The attribute is principally defined, but must be prepared first."""


class IsReady(object):
    """Container that informs, whether all variables required in a certain
    context are properly prepared or not.

    All variables can start with a `True` or `False` value:

    >>> from hydpy.core.exceptiontools import IsReady
    >>> isready = IsReady(true=['x', 'y'], false=['z'])
    >>> isready.x
    True
    >>> isready.z
    False

    If there is at least one `False` value, the |IsReady| object itself
    is considered to be `False`:

    >>> isready
    IsReady(true=['x', 'y'],
            false=['z'])
    >>> bool(isready)
    False

    Only in case all values are `True`, `isready` is considered to the
    `True`:

    >>> isready.z = True
    >>> isready
    IsReady(true=['x', 'y', 'z'],
            false=[])
    >>> bool(isready)
    True
    """

    def __init__(self, true=(), false=()):
        for name in true:
            setattr(self, name, True)
        for name in false:
            setattr(self, name, False)

    @property
    def true(self):
        """Sorted tuple of the names of all `True` variables.

        >>> from hydpy.core.exceptiontools import IsReady
        >>> isready = IsReady(true=['b', 'c', 'a'], false=['z'])
        >>> isready.true
        ('a', 'b', 'c')
        """
        return tuple(name for (name, value) in self if value)

    @property
    def false(self):
        """Sorted tuple of the names of all `False` variables.

        >>> from hydpy.core.exceptiontools import IsReady
        >>> isready = IsReady(false=['b', 'c', 'a'], true=['z'])
        >>> isready.false
        ('a', 'b', 'c')
        """
        return tuple(name for (name, value) in self if not value)

    def __bool__(self):
        return all(vars(self).values())

    def __iter__(self):
        for key, value in sorted(vars(self).items()):
            yield key, value

    def __repr__(self):
        true = ["'%s'" % name for name in self.true]
        false = ["'%s'" % name for name in self.false]
        arl = objecttools.assignrepr_list
        return (arl(true, 'IsReady(true=', width=70) + ',\n' +
                arl(false, '        false=', width=70) + ')')


def _objectname(self):
    return getattr(self, 'name', objecttools.instancename(self))


def protected_property(propname, fget, fset=None, fdel=None):
    """Return a :func:`property` which prevents getting an attribute
    before setting it.

    Under some circumstances, an attribute value needs to be prepared
    before one should be allowed to query it.  Consider the case where
    a property of a Python class (beeing part of the API) links to an
    attribute of a Cython extension class (not part of the API).  If
    the Cython attribute is e.g. some type of vector requiring memory
    allocation, trying to query this vector befor it has actually been
    prepared results in a programm crash.  Using |protected_property|
    is a means to prevent from such problems to occur.

    Consider the following class `Test`, which defines most simple
    `set`, `get`, and `del` methods for its only property `x`:

    >>> from hydpy.core.exceptiontools import IsReady, protected_property
    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._isready = IsReady(false=['x'])
    ...
    ...     def _get_x(self):
    ...         return self._x
    ...
    ...     def _set_x(self, value):
    ...         self._x = value
    ...
    ...     def _del_x(self):
    ...         self._x = None
    ...
    ...     x = protected_property(
    ...         'x', _get_x, _set_x, _del_x)

    Due to using |protected_property| instead of :func:`property`,
    trying to query `x` after initializing a `Test` object results
    in an |AttributeNotReady| error:

    >>> test = Test()
    >>> test.x
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `test` has not been \
prepared so far.

    After setting a value for property `x`, this value can be queried
    as expected:

    >>> test.x = 1
    >>> test.x
    1

    After deleting `x`, its valu is not accessible, again:

    >>> del test.x
    >>> test.x
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `test` has not been \
prepared so far.

    If the considered object defines a name (different from the class
    name in lower letters) and/or references a |Node| or |Element|
    object, the exception message includes this additional information:

    >>> from hydpy import Element
    >>> test.name = 'name_object'
    >>> test.element = Element('name_element')

    >>> test.x
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `name_object` of \
element `name_element` has not been prepared so far.

    As for :func:`property`, the `set` and `del` can be omitted.  As
    an example, we redefine class `Test` with a `get` method only:

    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._isready = IsReady(false=['x'])
    ...
    ...     def _get_x(self):
    ...         return self._x
    ...
    ...     x = protected_property(
    ...         'x', _get_x)
    >>> test = Test()

    Now trying to set a new value results in the usual error...

    >>> test.x = 1
    Traceback (most recent call last):
    ...
    AttributeError: cannot set attribute

    ...and does not change the value of attribute `x`:

    >>> test.x
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `test` has not been \
prepared so far.

    The same holds true for trying to delete the value of attribute `x`:

    >>> del test.x
    Traceback (most recent call last):
    ...
    AttributeError: cannot delete attribute

    .. note::

        The class making use of |protected_property| must implement
        an |IsReady| member as shown in the example.  The member name
        `_isready` is mandatory.
    """
    # pylint: disable=no-value-for-parameter, unused-argument, protected-access
    @wrapt.decorator
    def wrap_fget(wrapped, instance, args, kwargs):
        """Wrap the get function."""
        self = args[0]
        if getattr(self._isready, propname):
            return wrapped(*args, **kwargs)
        else:
            raise AttributeNotReady(
                'Attribute `%s` of object `%s`%shas not been prepared so far.'
                % (propname,
                   _objectname(self),
                   objecttools.devicephrase(self)))

    @wrapt.decorator
    def wrap_fset(wrapped, instance, args, kwargs):
        """Wrap the set function."""
        if wrapped:
            wrapped(*args, **kwargs)
            setattr(args[0]._isready, propname, True)
        else:
            raise AttributeError(
                'cannot set attribute')

    @wrapt.decorator
    def wrap_fdel(wrapped, instance, args, kwargs):
        """Wrap the del function."""
        if wrapped:
            wrapped(*args, **kwargs)
            setattr(args[0]._isready, propname, False)
        else:
            raise AttributeError(
                'cannot delete attribute')

    return property(wrap_fget(fget), wrap_fset(fset), wrap_fdel(fdel))


def dependent_property(propname, fget, fset=None, fdel=None):
    """Return a :func:`property` which prevents accessing a dependent
    attribute before other attributes have been prepared.

    The following explanations suppose first reading the documentation
    on function |protected_property|.  Here the example class `Test` is
    defined very similarly, but `x` is returned by |dependent_property|
    instead of |protected_property|, and the |IsReady| member knows
    another attribute `y` but not the dependent attribute `x` (usually
    but not mandatory, `y` itself would be implemented as a
    |protected_property|, which is left out for reasons of brevity):

    >>> from hydpy.core.exceptiontools import IsReady, protected_property
    >>> from hydpy.core.exceptiontools import dependent_property
    >>> class Test(object):
    ...
    ...     def __init__(self):
    ...         self._x = None
    ...         self._isready = IsReady(false=['y'])
    ...
    ...     def _get_x(self):
    ...         return self._x
    ...
    ...     def _set_x(self, value):
    ...         self._x = value
    ...
    ...     def _del_x(self):
    ...         self._x = None
    ...
    ...     x = dependent_property(
    ...         'x', _get_x, _set_x, _del_x)

    Initially, due to `y` beeing not prepared according to `_isready`,
    there is no way to get, set, or delete attribute `x`:

    >>> test = Test()
    >>> test.x
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `test` is not usable so far.

    >>> test.x = 1
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `test` is not usable so far.

    >>> del test.x
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `x` of object `test` is not usable so far.

    However, after setting the `y` flag to `True`, `x` behaves like a
    "normal" property:

    >>> test._isready.y = True
    >>> test.x = 1
    >>> test.x
    1
    >>> del test.x
    >>> test.x
    """
    # pylint: disable=no-value-for-parameter, unused-argument
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        """Wrap the get, set, or del method."""
        self = args[0]
        if not wrapped:
            raise AttributeError(
                'Attribute `%s` of object `%s`%scannot be used this way.'
                % (propname,
                   _objectname(self),
                   objecttools.devicephrase(self)))
        elif self._isready:
            return wrapped(*args, **kwargs)
        else:
            raise AttributeNotReady(
                'Attribute `%s` of object `%s`%sis not usable so far.'
                % (propname,
                   _objectname(self),
                   objecttools.devicephrase(self)))

    return property(wrapper(fget), wrapper(fset), wrapper(fdel))


class OptionalModuleNotAvailable(ImportError):
    """A `HydPy` function requiring an optional module is called, but this
    module is not available."""


class OptionalImport(object):
    """Exectutes the given import command and returns the imported module.
    If the import is not possible, it returns and dummy object which raises
    a |OptionalModuleNotAvailable| each time a function tries to access a
    member of the orignal module.

    When the module is availabe:

    >>> from hydpy.core.exceptiontools import OptionalImport
    >>> numpy = OptionalImport('import numpy')
    >>> numpy.nan
    nan

    When the module is not available:

    >>> numpie = OptionalImport('import numpie')
    >>> numpie.nan
    Traceback (most recent call last):
    ...
    OptionalModuleNotAvailable: HydPy could not load module `numpie`.  \
This module is no general requirement but necessary for some \
specific functionalities.
    """

    def __new__(cls, command, do_not_freeze=True):
        try:
            if pub._am_i_an_exe and do_not_freeze:
                raise ImportError()
            exec(command)
            return eval(command.split()[-1])
        except BaseException:
            return object.__new__(cls)

    def __init__(self, command):
        self.name = command.split()[-1]

    def __getattr__(self, name):
        raise OptionalModuleNotAvailable(
            'HydPy could not load module `%s`.  This module is no '
            'general requirement but necessary for some specific '
            'functionalities.'
            % self.name)


autodoctools.autodoc_module()
