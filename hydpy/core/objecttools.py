# -*- coding: utf-8 -*-
"""This module implements tools to help to standardize the functionality
of the different objects defined by the HydPy framework.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import copy
import inspect
import numbers
import sys
import textwrap
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools


def dir_(self):
    """The prefered way for HydPy objects to respond to :func:`dir`.

    Note the depencence on the `pub.options.dirverbose`.  If this option is
    set `True`, all attributes and methods of the given instance and its
    class (including those inherited from the parent classes) are returned:

    >>> from hydpy.pub import options
    >>> options.dirverbose = True
    >>> from hydpy.core.objecttools import dir_
    >>> class Test(object):
    ...     only_public_attribute =  None
    >>> print(len(dir_(Test())) > 1) # Long list, try it yourself...
    True

    If the option is set to `False`, only the `public` attributes and methods
    (which do need begin with `_`) are returned:

    >>> options.dirverbose = False
    >>> print(dir_(Test())) # Short list with one single entry...
    ['only_public_attribute']
    """
    names = set()
    for thing in list(inspect.getmro(type(self))) + [self]:
        for name in vars(thing).keys():
            if pub.options.dirverbose or not name.startswith('_'):
                names.add(name)
    if names:
        names = list(names)
    else:
        names = [' ']
    return names


def classname(self):
    """Return the class name of the given instance object or class.

    >>> from hydpy.core.objecttools import classname
    >>> from hydpy.pub import options
    >>> print(classname(float))
    float
    >>> print(classname(options))
    Options
    """
    if not inspect.isclass(self):
        self = type(self)
    return str(self).split("'")[1].split('.')[-1]


def instancename(self):
    """Return the class name of the given instance object or class in lower
    case letters.

    >>> from hydpy.core.objecttools import instancename
    >>> from hydpy.pub import options
    >>> print(instancename(options))
    options
    """
    return classname(self).lower()


def value_of_type(value):
    """Returns a string containing both the informal string and the type
    of the given value.

    This function is intended to simplifying writing HydPy exceptions,
    which frequently contain the following phrase:

    >>> from hydpy.core.objecttools import value_of_type
    >>> value_of_type(999)
    'value `999` of type `int`'
    """
    return 'value `%s` of type `%s`' % (value, classname(value))


def name(self):
    """Name of the class of the given instance in lower case letters.

    This function is thought to be implemented as a property.  Otherwise
    it would violate the principle not to access or manipulate private
    attributes ("_name"):

    >>> from hydpy.core.objecttools import name
    >>> class Test(object):
    ...     name = property(name)
    >>> test1 = Test()
    >>> test1.name
    'test'
    >>> test1._name
    'test'

    The private attribute is added for performance reasons only.  Note that
    it is a class attribute:

    >>> test2 = Test()
    >>> test2._name
    'test'
    """
    try:
        return type(self).__dict__['_name']
    except KeyError:
        type(self)._name = instancename(self)
        return type(self).__dict__['_name']


def modulename(self):
    """Return the module name of the given instance object.

    >>> from hydpy.core.objecttools import modulename
    >>> from hydpy.pub import options
    >>> print(modulename(options))
    optiontools
    """
    return self.__module__.split('.')[-1]


def devicename(self):
    """Try to return the name of the (indirect) master
    :class:`~hydpy.core.devicetools.Node` or
    :class:`~hydpy.core.devicetools.Element` instance,
    otherwise return `?`.
    """
    while True:
        device = getattr(self, 'element', getattr(self, 'node', None))
        if device is not None:
            return device.name
        for test in ('model', 'seqs', 'subseqs', 'pars', 'subpars'):
            master = getattr(self, test, None)
            if master is not None:
                self = master
                break
        else:
            return '?'


def valid_variable_identifier(name):
    """Raises an :class:`~exceptions.ValueError` if the given name is not
    a valid Python identifier.

    For example, the string `test_1` (with underscore) is valid...

    >>> from hydpy.core.objecttools import valid_variable_identifier
    >>> valid_variable_identifier('test_1')

    ...but the string `test 1` (with white space) is not:

    >>> valid_variable_identifier('test 1')
    Traceback (most recent call last):
    ...
    ValueError: The given name string `test 1` does not define a valid \
variable identifier.  Valid identifiers do not contain characters like \
`-` or empty spaces, do not start with numbers, cannot be mistaken with \
Python built-ins like `for`...)

    Also, names of Python built ins are not allowed:

    >>> valid_variable_identifier('while')
    Traceback (most recent call last):
    ...
    ValueError: The given name string `while` does not define...
    """
    string = str(name)
    try:
        exec('%s = None' % string)
        if name in dir(__builtins__):
            raise SyntaxError()
    except SyntaxError:
        raise ValueError(
            'The given name string `%s` does not define a valid variable '
            'identifier.  Valid identifiers do not contain characters like '
            '`-` or empty spaces, do not start with numbers, cannot be '
            'mistaken with Python built-ins like `for`...)' % name)


def augment_excmessage(prefix=None, suffix=None):
    """Augment an exception message with additional information while keeping
    the original traceback.

    You can prefix and/or suffix text.  If you prefix something (which happens
    much more often in the HydPy framework), the sub-clause ', the following
    error occured:' is automatically included:

    >>> from hydpy.core import objecttools
    >>> import textwrap
    >>> try:
    ...     1 + '1'
    ... except TypeError:
    ...     try:
    ...         prefix = 'While showing how prefixing works'
    ...         suffix = '(This is a final remark.)'
    ...         objecttools.augment_excmessage(prefix, suffix)
    ...     except TypeError as exc:
    ...         for line in textwrap.wrap(exc.args[0], width=76):
    ...             print(line)
    While showing how prefixing works, the following error occured: unsupported
    operand type(s) for +: 'int' and 'str' (This is a final remark.)

    Note that the ancillary purpose of function :func:`augment_excmessage` is
    to make re-raising exceptions compatible with both Python 2 and 3.
    """
    exception, message, traceback_ = sys.exc_info()
    if prefix is not None:
        message = ('%s, the following error occured: %s'
                   % (prefix, message))
    if suffix is not None:
        message = ' '.join((message, suffix))
    if pub.pyversion < 3:
        exec('raise exception, message, traceback_')
    else:
        raise exception(message).with_traceback(traceback_)


class ResetAttrFuncs(object):
    """Reset all attribute related methods of the given class temporarily.

    The "related methods" are defined in class attribute
    :attr:`~ResetAttrFuncs.funcnames`.

    There are (at least) two use cases for  class :class:`ResetAttrFuncs`,
    initialization and copying, which are described below.

    In HydPy, some classes define a `__setattr__` method which raises
    exceptions when one tries to set "improper" instance attributes.
    The problem is, that such customized `setattr` methods often prevent
    from defining instance attributes within `__init__` methods in the
    usual manner.  Working on instance dictionaries instead can confuse
    some automatic tools (e.g. pylint).  Class :class:`ResetAttrFuncs`
    implements a trick to circumvent this problem.

    To show how :class:`ResetAttrFuncs` works, we first define a class
    with a `__setattr__` method that does not allow to set any attribute:

    >>> class Test(object):
    ...     def __setattr__(self, name, value):
    ...         raise AttributeError
    >>> test = Test()
    >>> test.var1 = 1
    Traceback (most recent call last):
    ...
    AttributeError

    Assigning this class to :class:`ResetAttrFuncs` allows for setting
    attributes to all its instances inside a `with` block in the
    usual manner:

    >>> from hydpy.core.objecttools import ResetAttrFuncs
    >>> with ResetAttrFuncs(test):
    ...     test.var1 = 1
    >>> test.var1
    1

    After the end of the `with` block, the custom `__setattr__` method
    of the test class works again and prevents from setting attributes:

    >>> test.var2 = 2
    Traceback (most recent call last):
    ...
    AttributeError

    The second use case is related to method `__getattr__` and copying.
    The following test class stores its attributes (for whatever reasons)
    in a special dictionary called "dic" (note that how
    :class:`ResetAttrFuncs` is used in the `__init__` method):

    >>> class Test(object):
    ...     def __init__(self):
    ...         with ResetAttrFuncs(self):
    ...             self.dic = {}
    ...     def __setattr__(self, name, value):
    ...         self.dic[name] = value
    ...     def __getattr__(self, name):
    ...         try:
    ...             return self.dic[name]
    ...         except KeyError:
    ...             raise AttributeError

    Principally, this simple implementation does its job but its
    instances are not easily copyable under all Python versions:

    >>> test = Test()
    >>> test.var1 = 1
    >>> test.var1
    1
    >>> import copy
    >>> copy.deepcopy(test)   # doctest: +SKIP
    Traceback (most recent call last):
    ...
    RecursionError: maximum recursion depth exceeded ...

    :class:`ResetAttrFuncs` can be used to implement specialized
    `__copy__` and `__deepcopy__` methods, which rely on the temporary
    disabling of `__getattr__`.  For simple cases, one can import the
    predefined functions :func:`~hydpy.core.objecttools.copy_` and
    :func:`~hydpy.core.objecttools.deepcopy_`:

    >>> from hydpy.core.objecttools import copy_, deepcopy_
    >>> Test.__copy__ = copy_
    >>> test2 = copy.copy(test)
    >>> test2.var1
    1
    >>> Test.__deepcopy__ = deepcopy_
    >>> test3 = copy.deepcopy(test)
    >>> test3.var1
    1

    Note that an infinite recursion is avoided by also disabling methods
    `__copy__` and `__deepcopy__` themselves.

    """
    __slots__ = ('cls', 'name2func')
    funcnames = ('__getattr__', '__setattr__', '__delattr__',
                 '__copy__', '__deepcopy__')

    def __init__(self, obj):
        self.cls = type(obj)
        self.name2func = {}
        for name in self.funcnames:
            if hasattr(self.cls, name):
                self.name2func[name] = self.cls.__dict__.get(name)

    def __enter__(self):
        for name in self.name2func.keys():
            if name in ('__setattr__', '__delattr__'):
                setattr(self.cls, name, getattr(object, name))
            elif name == '__getattr__':
                setattr(self.cls, name, object.__getattribute__)
            else:
                setattr(self.cls, name, None)
        return self

    def __exit__(self, exception, message, traceback_):
        for name, func in self.name2func.items():
            if func:
                setattr(self.cls, name, func)
            else:
                delattr(self.cls, name)


def copy_(self):
    """Copy function for classes with modified attribute functions.

    See the documentation on class :class:`ResetAttrFuncs` for
    further information.
    """
    with ResetAttrFuncs(self):
        return copy.copy(self)


def deepcopy_(self, memo):
    """Deepcopy function for classes with modified attribute functions.

    See the documentation on class :class:`ResetAttrFuncs` for
    further information.
    """
    with ResetAttrFuncs(self):
        return copy.deepcopy(self, memo)


class _PreserveStrings(object):
    """Helper class for :class:`_Repr_`."""

    def __init__(self, preserve_strings):
        self.new_value = preserve_strings
        self.old_value = repr_._preserve_strings

    def __enter__(self):
        repr_._preserve_strings = self.new_value
        return None

    def __exit__(self, type_, value, traceback):
        repr_._preserve_strings = self.old_value


class _Repr_(object):
    """Modifies :func:`repr` for strings and floats, mainly for supporting
    clean float representations that are compatible with :mod:`doctest`.

    When value is a string, it is returned without any modification:

    >>> from hydpy.core.objecttools import repr_
    >>> print('test')
    test
    >>> print(repr('test'))
    'test'
    >>> print(repr_('test'))
    test

    You can change this behaviour of function object :func:`repr_`,
    when necessary:

    >>> with repr_.preserve_strings(True):
    ...     print(repr_('test'))
    "test"

    Behind the with block, :func:`repr_` works as before
    (even in case of an error):

    >>> print(repr_('test'))
    test

    When value is a float, the result depends on how the option
    :attr:`~hydpy.core.optiontools.Options.reprdigits` is set. If it is
    to -999, :func:`repr` defines the number of digits in
    the usual, system dependent manner:

    >>> from hydpy.pub import options
    >>> options.reprdigits = -999
    >>> repr(1./3.) == repr_(1./3.)
    True

    Through setting :attr:`~hydpy.core.optiontools.Options.reprdigits` to a
    positive integer value, one defines the maximum number of decimal places,
    which allows for doctesting across different systems and Python versions:

    >>> options.reprdigits = 6
    >>> repr_(1./3.)
    '0.333333'
    >>> repr_(2./3.)
    '0.666667'
    >>> repr_(1./2.)
    '0.5'

    Changing the number of decimal places can be done via a with block:

    >>> with options.reprdigits(3):
    ...     print(repr_(1./3.))
    0.333

    Such a change is only temporary (even in case of an error):
    >>> repr_(1./3.)
    '0.333333'

    :func:`repr_` can also be applied on numpy's float types:

    >>> import numpy
    >>> repr_(numpy.float(1./3.))
    '0.333333'
    >>> repr_(numpy.float64(1./3.))
    '0.333333'
    >>> repr_(numpy.float32(1./3.))
    '0.333333'
    >>> repr_(numpy.float16(1./3.))
    '0.333252'

    Note that the deviation from the `true` result in the last example is due
    to the low precision of :class:`~numpy.float16`.

    On all types not mentioned above, the usual :func:`repr` function is
    applied, e.g.:

    >>> repr([1, 2, 3])
    '[1, 2, 3]'
    >>> repr_([1, 2, 3])
    '[1, 2, 3]'
    """

    def __init__(self):
        self._preserve_strings = False

    def __call__(self, value):
        decimals = pub.options.reprdigits
        if isinstance(value, str):
            if self._preserve_strings:
                return '"%s"' % value
            else:
                return value
        if ((decimals > -1) and
                isinstance(value, numbers.Real) and
                (not isinstance(value, numbers.Integral))):
            string = '{0:.{1}f}'.format(value, decimals)
            string = string.rstrip('0')
            if string.endswith('.'):
                string += '0'
            return string
        else:
            return repr(value)

    def preserve_strings(self, preserve_strings):
        """Change the `preserve_string` option inside a with block."""
        return _PreserveStrings(preserve_strings)


repr_ = _Repr_()


def repr_values(values):
    """Return comma separated representations of the given values using
    function :func:`repr_`.

    >>> from hydpy.core.objecttools import repr_values
    >>> repr_values([1./1., 1./2., 1./3.])
    '1.0, 0.5, 0.333333'

    Note that the returned string is not wrapped.
    """
    return '%s' % ', '.join(repr_(value) for value in values)


def print_values(values, width=70):
    """Print the given values in multiple lines with a certain maximum width.

    By default, each line contains at most 70 characters:

    >>> from hydpy import print_values
    >>> print_values(range(21))
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
    20

    You can change this default behaviour by passing an alternative
    number of characters:

    >>> print_values(range(21), width=30)
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    10, 11, 12, 13, 14, 15, 16,
    17, 18, 19, 20
    """
    for line in textwrap.wrap(repr_values(values), width=width):
        print(line)


def repr_tuple(values):
    """Return a tuple representation of the given values using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import repr_tuple
    >>> repr_tuple([1./1., 1./2., 1./3.])
    '(1.0, 0.5, 0.333333)'

    Note that the returned string is not wrapped.

    In the special case of an iterable with only one entry, the returned
    string is still a valid tuple:

    >>> repr_tuple([1.])
    '(1.0,)'
    """
    if len(values) == 1:
        return '(%s,)' % repr_values(values)
    else:
        return '(%s)' % repr_values(values)


def repr_list(values):
    """Return a list representation of the given values using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import repr_list
    >>> repr_list([1./1., 1./2., 1./3.])
    '[1.0, 0.5, 0.333333]'

    Note that the returned string is not wrapped.
    """
    return '[%s]' % repr_values(values)


def assignrepr_value(value, prefix, width=None):
    """Return a prefixed string representation of the given value using
    function :func:`repr_`.

    Note that the argument has no effect. It is thought for increasing
    usage compatibility with functions like :func:`assignrepr_list` only.

    >>> from hydpy.core.objecttools import assignrepr_value
    >>> print(assignrepr_value(1./3., 'test = '))
    test = 0.333333
    """
    return prefix + repr_(value)


def assignrepr_values(values, prefix, width=None, _fakeend=0):
    """Return a prefixed, wrapped and properly aligned string representation
    of the given values using function :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_values
    >>> print(assignrepr_values(range(1, 13), 'test(', 20) + ')')
    test(1, 2, 3, 4, 5,
         6, 7, 8, 9, 10,
         11, 12)

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_values(range(1, 13), 'test(') + ')')
    test(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)


    To circumvent defining too long string representations, make use of the
    ellipsis option:

    >>> from hydpy.pub import options
    >>> with options.ellipsis(1):
    ...     print(assignrepr_values(range(1, 13), 'test(', 20) + ')')
    test(1, ...,12)

    >>> with options.ellipsis(5):
    ...     print(assignrepr_values(range(1, 13), 'test(', 20) + ')')
    test(1, 2, 3, 4, 5,
         ...,8, 9, 10,
         11, 12)

    >>> with options.ellipsis(6):
    ...     print(assignrepr_values(range(1, 13), 'test(', 20) + ')')
    test(1, 2, 3, 4, 5,
         6, 7, 8, 9, 10,
         11, 12)
    """
    ellipsis = pub.options.ellipsis
    if (ellipsis > 0) and (len(values) > 2*ellipsis):
        string = (repr_values(values[:ellipsis]) +
                  ', ...,' +
                  repr_values(values[-ellipsis:]))
    else:
        string = repr_values(values)
    blanks = ' '*len(prefix)
    if width is None:
        wrapped = [string]
        _fakeend = 0
    else:
        width -= len(prefix)
        wrapped = textwrap.wrap(string+'_'*_fakeend, width)
    if not wrapped:
        wrapped = ['']
    lines = []
    for (idx, line) in enumerate(wrapped):
        if idx == 0:
            lines.append('%s%s' % (prefix, line))
        else:
            lines.append('%s%s' % (blanks, line))
    string = '\n'.join(lines)
    return string[:len(string)-_fakeend]


class _AlwaysBracketed(object):
    """Helper class for :class:`_AssignReprBracketed`."""

    def __init__(self, value):
        self.new_value = value
        self.old_value = _AssignReprBracketed._always_bracketed

    def __enter__(self):
        _AssignReprBracketed._always_bracketed = self.new_value

    def __exit__(self, type_, value, traceback):
        _AssignReprBracketed._always_bracketed = self.old_value


class _AssignReprBracketed(object):
    """"Double Singleton class", see the documentation on
    :func:`assignrepr_tuple` and :func:`assignrepr_list`."""

    _always_bracketed = True

    def __init__(self, brackets):
        self._brackets = brackets

    def __call__(self, values, prefix, width=None):
        if (len(values) == 1) and not self._always_bracketed:
            return assignrepr_value(values[0], prefix)
        elif len(values):
            string = assignrepr_values(
                values, prefix+self._brackets[0], width, 1) + self._brackets[1]
            if (len(values) == 1) and (self._brackets[1] == ')'):
                return string[:-1] + ',)'
            else:
                return string
        else:
            return prefix + self._brackets

    def always_bracketed(self, always_bracketed):
        """Change the `always_bracketed` option inside a with block."""
        return _AlwaysBracketed(always_bracketed)


assignrepr_tuple = _AssignReprBracketed('()')
"""Return a prefixed, wrapped and properly aligned tuple string
representation of the given values using function :func:`repr_`.

>>> from hydpy.core.objecttools import assignrepr_tuple
>>> print(assignrepr_tuple(range(10), 'test = ', 22))
test = (0, 1, 2, 3, 4,
        5, 6, 7, 8, 9)

If no width is given, no wrapping is performed:

>>> print(assignrepr_tuple(range(10), 'test = '))
test = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

Functions :func:`assignrepr_tuple` works also on empty iterables and
those which possess only one entry:

>>> print(assignrepr_tuple([], 'test = '))
test = ()
>>> print(assignrepr_tuple([10], 'test = '))
test = (10,)

Optionally, bracketing single values can be prevented:

>>> with assignrepr_tuple.always_bracketed(False):
...     print(assignrepr_tuple([], 'test = '))
...     print(assignrepr_tuple([10], 'test = '))
...     print(assignrepr_tuple([10, 10], 'test = '))
test = ()
test = 10
test = (10, 10)

Behind the with block, :func:`assignrepr_tuple` works as before
(even in case of an error):

>>> print(assignrepr_tuple([10], 'test = '))
test = (10,)
"""


assignrepr_list = _AssignReprBracketed('[]')
"""Return a prefixed, wrapped and properly aligned list string
representation of the given values using function :func:`repr_`.

>>> from hydpy.core.objecttools import assignrepr_list
>>> print(assignrepr_list(range(10), 'test = ', 22))
test = [0, 1, 2, 3, 4,
        5, 6, 7, 8, 9]

If no width is given, no wrapping is performed:

>>> print(assignrepr_list(range(10), 'test = '))
test = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

Functions :func:`assignrepr_list` works also on empty iterables:

>>> print(assignrepr_list((), 'test = '))
test = []

Optionally, bracketing single values can be prevented:

>>> with assignrepr_list.always_bracketed(False):
...     print(assignrepr_list([], 'test = '))
...     print(assignrepr_list([10], 'test = '))
...     print(assignrepr_list([10, 10], 'test = '))
test = []
test = 10
test = [10, 10]

Behind the with block, :func:`assignrepr_list` works as before
(even in case of an error):

>>> print(assignrepr_list([10], 'test = '))
test = [10,]
"""


def assignrepr_values2(values, prefix):
    """Return a prefixed and properly aligned string representation
    of the given 2-dimensional value matrix using function :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_values2
    >>> import numpy
    >>> print(assignrepr_values2(numpy.eye(3), 'test(') + ')')
    test(1.0, 0.0, 0.0,
         0.0, 1.0, 0.0,
         0.0, 0.0, 1.0)

    Functions :func:`assignrepr_values2` works also on empty iterables:

    >>> print(assignrepr_values2([[]], 'test(') + ')')
    test()
    """
    lines = []
    blanks = ' '*len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append('%s%s,' % (prefix, repr_values(subvalues)))
        else:
            lines.append('%s%s,' % (blanks, repr_values(subvalues)))
    lines[-1] = lines[-1][:-1]
    return '\n'.join(lines)


def _assignrepr_bracketed2(assignrepr_bracketed1, values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned bracketed string
    representation of the given 2-dimensional value matrix using function
    :func:`repr_`."""
    prefix += assignrepr_bracketed1._brackets[0]
    lines = []
    blanks = ' '*len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(assignrepr_bracketed1(subvalues, prefix, width))
        else:
            lines.append(assignrepr_bracketed1(subvalues, blanks, width))
        if (len(subvalues) == 1) and (lines[-1] == ')'):
            lines[-1] = lines[-1].replace(')', ',)')
        lines[-1] += ','
    lines[-1] = lines[-1][:-1] + assignrepr_bracketed1._brackets[1]
    return '\n'.join(lines)


def assignrepr_tuple2(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned tuple string
    representation of the given 2-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_tuple2
    >>> import numpy
    >>> print(assignrepr_tuple2(numpy.eye(3), 'test = ', 18))
    test = ((1.0, 0.0,
             0.0),
            (0.0, 1.0,
             0.0),
            (0.0, 0.0,
             1.0))

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_tuple2(numpy.eye(3), 'test = '))
    test = ((1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0))

    Functions :func:`assignrepr_tuple2` works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_tuple2([[]], 'test = '))
    test = (())
    >>> print(assignrepr_tuple2([[], [1]], 'test = '))
    test = ((),
            (1,))
    """
    return _assignrepr_bracketed2(assignrepr_tuple, values, prefix, width)


def assignrepr_list2(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned list string
    representation of the given 2-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_list2
    >>> import numpy
    >>> print(assignrepr_list2(numpy.eye(3), 'test = ', 18))
    test = [[1.0, 0.0,
             0.0],
            [0.0, 1.0,
             0.0],
            [0.0, 0.0,
             1.0]]

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_list2(numpy.eye(3), 'test = '))
    test = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]

    Functions :func:`assignrepr_list2` works also on empty iterables:

    >>> print(assignrepr_list2([[]], 'test = '))
    test = [[]]
    >>> print(assignrepr_list2([[], [1]], 'test = '))
    test = [[],
            [1]]
    """
    return _assignrepr_bracketed2(assignrepr_list, values, prefix, width)


def _assignrepr_bracketed3(assignrepr_bracketed1, values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned bracketed string
    representation of the given 3-dimensional value matrix using function
    :func:`repr_`."""
    prefix += assignrepr_bracketed1._brackets[0]
    lines = []
    blanks = ' '*len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(_assignrepr_bracketed2(
                            assignrepr_bracketed1, subvalues, prefix, width))
        else:
            lines.append(_assignrepr_bracketed2(
                            assignrepr_bracketed1, subvalues, blanks, width))
        if (len(subvalues) <= 1) and (lines[-1][-1] == ')'):
            lines[-1] = lines[-1][:-1] + ',)'
        lines[-1] += ','
    lines[-1] = lines[-1][:-1] + assignrepr_bracketed1._brackets[1]
    if (len(values) <= 1) and (lines[-1][-1] == ')'):
        lines[-1] = lines[-1][:-1] + ',)'
    return '\n'.join(lines)


def assignrepr_tuple3(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned tuple string
    representation of the given 3-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_tuple3
    >>> import numpy
    >>> values = [numpy.eye(3), numpy.ones((3, 3))]
    >>> print(assignrepr_tuple3(values, 'test = ', 18))
    test = (((1.0,
              0.0,
              0.0),
             (0.0,
              1.0,
              0.0),
             (0.0,
              0.0,
              1.0)),
            ((1.0,
              1.0,
              1.0),
             (1.0,
              1.0,
              1.0),
             (1.0,
              1.0,
              1.0)))

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_tuple3(values, 'test = '))
    test = (((1.0, 0.0, 0.0),
             (0.0, 1.0, 0.0),
             (0.0, 0.0, 1.0)),
            ((1.0, 1.0, 1.0),
             (1.0, 1.0, 1.0),
             (1.0, 1.0, 1.0)))

    Functions :func:`assignrepr_tuple3` works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_tuple3([[[]]], 'test = '))
    test = (((),),)
    >>> print(assignrepr_tuple3([[[], [1]]], 'test = '))
    test = (((),
             (1,)),)
    """
    return _assignrepr_bracketed3(assignrepr_tuple, values, prefix, width)


def assignrepr_list3(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned list string
    representation of the given 3-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_list3
    >>> import numpy
    >>> values = [numpy.eye(3), numpy.ones((3, 3))]
    >>> print(assignrepr_list3(values, 'test = ', 18))
    test = [[[1.0,
              0.0,
              0.0],
             [0.0,
              1.0,
              0.0],
             [0.0,
              0.0,
              1.0]],
            [[1.0,
              1.0,
              1.0],
             [1.0,
              1.0,
              1.0],
             [1.0,
              1.0,
              1.0]]]

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_list3(values, 'test = '))
    test = [[[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [0.0, 0.0, 1.0]],
            [[1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0]]]

    Functions :func:`assignrepr_list3` works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_list3([[[]]], 'test = '))
    test = [[[]]]
    >>> print(assignrepr_list3([[[], [1]]], 'test = '))
    test = [[[],
             [1]]]
    """
    return _assignrepr_bracketed3(assignrepr_list, values, prefix, width)


def round_(values, decimals=None, width=0,
           lfill=None, rfill=None, **kwargs):
    """Prints values with a maximum number of digits in doctests.

    See the documentation on function :func:`repr_` for more details.  And
    note thate the option keyword arguments are passed to the print function.

    Usually one would apply function :func:`round_` on a single or a vector
    of numbers:

    >>> from hydpy import round_
    >>> round_(1./3., decimals=6)
    0.333333
    >>> round_((1./2., 1./3., 1./4.), decimals=4)
    0.5, 0.3333, 0.25

    Additionally, one can supply a `width` and a `rfill` argument:
    >>> round_(1.0, width=6, rfill='0')
    1.0000

    Alternatively, one can use the `lfill` arguments, which
    might e.g. be usefull for aligning different strings:

    >>> round_('test', width=6, lfill='_')
    __test

    Using both the `lfill` and the `rfill` argument raises an error:

    >>> round_(1.0, lfill='_', rfill='0')
    Traceback (most recent call last):
    ...
    ValueError: For function `round_` values are passed for both \
arguments `lfill` and `rfill`.  This is not allowed.
    """
    if decimals is None:
        decimals = pub.options.reprdigits
    with pub.options.reprdigits(decimals):
        if isinstance(values, abctools.IterableNonStringABC):
            string = repr_values(values)
        else:
            string = repr_(values)
        if (lfill is not None) and (rfill is not None):
            raise ValueError(
                'For function `round_` values are passed for both arguments '
                '`lfill` and `rfill`.  This is not allowed.')
        if (lfill is not None) or (rfill is not None):
            width = max(width, len(string))
            if lfill is not None:
                string = string.rjust(width, lfill)
            else:
                string = string.ljust(width, rfill)
        print(string, **kwargs)


def extract(values, types, skip=False):
    """Return a generator that extracts certain objects from `values`.

    This function is thought for supporting the definition of functions
    with arguments, that can be objects of of contain types or that can
    be iterables containing these objects.

    The following examples show that function :func:`extract`
    basically implements a type specific flattening mechanism:

    >>> from hydpy.core.objecttools import extract
    >>> tuple(extract('str1', (str, int)))
    ('str1',)
    >>> tuple(extract(['str1', 'str2'], (str, int)))
    ('str1', 'str2')
    >>> tuple(extract((['str1', 'str2'], [1,]), (str, int)))
    ('str1', 'str2', 1)

    If an object is neither iterable nor of the required type, the
    following exception is raised:

    >>> tuple(extract((['str1', 'str2'], [None, 1]), (str, int)))
    Traceback (most recent call last):
    ...
    TypeError: The given value `'None'` is neither iterable nor \
an instance of the following classes: str and int.

    Optionally, :class:`None` values can be skipped:
    >>> tuple(extract(None, (str, int), True))
    ()
    >>> tuple(extract((['str1', 'str2'], [None, 1]), (str, int), True))
    ('str1', 'str2', 1)
    """
    if isinstance(values, types):
        yield values
    elif skip and (values is None):
        return
    else:
        try:
            for value in values:
                for subvalue in extract(value, types, skip):
                    yield subvalue
        except TypeError as exc:
            if exc.args[0].startswith('The given value'):
                raise exc
            else:
                raise TypeError(
                    'The given value `{0!r}` is neither iterable nor an '
                    'instance of the following classes: {1}.'
                    .format(repr(values),
                            enumeration(types, converter=instancename)))


def enumeration(values, converter=str, default=''):
    """Return an enumeration string based on the given values.

    The following four examples show the standard output of function
    :func:`enumeration`:

    >>> from hydpy.core.objecttools import enumeration
    >>> enumeration(('text', 3, []))
    'text, 3, and []'
    >>> enumeration(('text', 3))
    'text and 3'
    >>> enumeration(('text',))
    'text'
    >>> enumeration(())
    ''

    All given objects are converted to strings by function :func:`str`,
    as shown by the first two examples.  This behaviour can be changed
    by another function expecting a single argument and returning a string:

    >>> from hydpy.core.objecttools import classname
    >>> enumeration(('text', 3, []), converter=classname)
    'str, int, and list'

    Furthermore, you can define a default string that is returned
    in case an empty iterable is given:

    >>> enumeration((), default='nothing')
    'nothing'
    """
    values = tuple(converter(value) for value in values)
    if len(values) == 0:
        return default
    elif len(values) == 1:
        return values[0]
    elif len(values) == 2:
        return ' and '.join(values)
    else:
        return ', and '.join((', '.join(values[:-1]), values[-1]))


class FastAccess(object):
    """Used as a surrogate for typed Cython classes when working in
    pure Python mode."""


class HydPyDeprecationWarning(DeprecationWarning):
    pass


autodoctools.autodoc_module()
