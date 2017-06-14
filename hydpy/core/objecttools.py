# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import inspect
import sys
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.cythons import pointer
#from hydpy.pub import ... (actual import commands moved to
# different functions below to avoid circular dependencies)

def dir_(self):
    """The prefered way for HydPy objects to respond to :func:`dir`.

    Note thedepencence on the `pub.options.dirverbose`.  If this option is
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
    from hydpy.pub import options
    names = set()
    for thing in list(inspect.getmro(type(self))) + [self]:
        for name in vars(thing).keys():
            if options.dirverbose or not name.startswith('_'):
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

def modulename(self):
    """Return the module name of the given instance object.

    >>> from hydpy.core.objecttools import modulename
    >>> from hydpy.pub import options
    >>> print(modulename(options))
    objecttools

    """
    return self.__module__.split('.')[-1]

def devicename(self):
    """Try to return the name of the (indirect) master
    :class:`~hydpy.core.devicetools.Node` or
    :class:`~hydpy.core.devicetools.Element` instance,
    otherwise return `?`."""
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

def augmentexcmessage(prefix=None, suffix=None):
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
    ...         objecttools.augmentexcmessage(prefix, suffix)
    ...     except TypeError as exc:
    ...         for line in textwrap.wrap(exc.args[0], width=76):
    ...             print(line)
    While showing how prefixing works, the following error occured: unsupported
    operand type(s) for +: 'int' and 'str' (This is a final remark.)

    Note that the ancillary purpose of function :func:`augmentexcmessage` is
    to make re-raising exceptions compatible with both Python 2 and 3.
    """
    from hydpy.pub import pyversion
    exception, message, traceback_ = sys.exc_info()
    if prefix is not None:
        message = ('%s, the following error occured: %s'
                    % (prefix, message))
    if suffix is not None:
        message = ' '.join((message, suffix))
    if pyversion < 3:
        exec('raise exception, message, traceback_')
    else:
        raise exception(message).with_traceback(traceback_)

def repr_(value):
    """Modifies :func:`repr` for strings and floats, mainly for supporting
    clean float representations that are compatible with :mod:`doctest`.

    When value is a string, it is returned without any modification:

    >>> from hydpy.core.objecttools import repr_
    >>> repr('test')
    "'test'"
    >>> repr_('test')
    'test'

    When value is a float, the result depends on how the option
    :attr:`~Options.reprdigits` is set. If it is :class:`None`, :func:`repr`
    defines the number of digits in the usual, system dependend manner:

    >>> from hydpy.pub import options
    >>> options.reprdigits = None
    >>> repr(1./3.) == repr_(1./3.)
    True

    Through setting :attr:`~Options.reprdigits` to a positive integer value,
    one defines the maximum number of decimal places, which allows for
    doctesting across different systems and Python versions:

    >>> options.reprdigits = 6
    >>> repr_(1./3.)
    '0.333333'
    >>> repr_(2./3.)
    '0.666667'
    >>> repr_(1./2.)
    '0.5'

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
    from hydpy.pub import options
    if isinstance(value, (pointer.Double, pointer.PDouble)):
        value = float(value)
    if isinstance(value, str):
        return value
    elif ((options.reprdigits is not None) and
          isinstance(value,
                     (float, numpy.float64, numpy.float32, numpy.float16))):
        string = '{0:.{1}f}'.format(value, options.reprdigits)
        string = string.rstrip('0')
        if string.endswith('.'):
            string += '0'
        return string
    else:
        return repr(value)


def round_(value):
    """Shortcut for print(repr_(value)).

    See the documentation on function :func:`repr_` for any details.
    """
    print(repr_(value))


class Options(object):
    """Singleton class for `global` options."""

    def __init__(self):
        self._printprogress = True
        self._verbosedir = False
        self._reprcomments = True
        self._usecython = True
        self._skipdoctests = False
        self._refreshmodels = False
        self._reprdigits = None
        self._warntrim = True
        self._warnsimulationstep = True

    def _getprintprogress(self):
        """True/False flag indicating whether information about the progress
        of certain processes shall be printed to the standard output or not.
        The default is `True`.
        """
        return self._printprogress
    def _setprintprogress(self, value):
        self._printprogress = bool(value)
    printprogress = property(_getprintprogress, _setprintprogress)

    def _getdirverbose(self):
        """True/False flag indicationg whether the listboxes for the member
        selection of the classes of the HydPy framework should be complete
        (True) or restrictive (False).  The latter is more viewable and hence
        the default.
        """
        return self._verbosedir
    def _setdirverbose(self, value):
        self._verbosedir = bool(value)
    dirverbose = property(_getdirverbose, _setdirverbose)

    def _getreprcomments(self):
        """True/False flag indicationg whether comments shall be included
        in string representations of some classes of the HydPy framework or
        not.  The default is `True`.
        """
        return self._reprcomments
    def _setreprcomments(self, value):
        self._reprcomments = bool(value)
    reprcomments = property(_getreprcomments, _setreprcomments)

    def _getusecython(self):
        """True/False flag indicating whether Cython models (True) or pure
        Python models (False) shall be applied if possible.  Using Cython
        models is more time efficient and thus the default.
        """
        return self._usecython
    def _setusecython(self, value):
        self._usecython = bool(value)
    usecython = property(_getusecython, _setusecython)

    def _getskipdoctests(self):
        """True/False flag indicating whether documetation tests shall be
        performed under certain situations.  Applying tests increases
        reliabilty and is thus the default.
        """
        return self._skipdoctests
    def _setskipdoctests(self, value):
        self._skipdoctests = bool(value)
    skipdoctests = property(_getskipdoctests, _setskipdoctests)

    def _getreprdigits(self):
        """Required precision of string representations of floating point
        numbers, defined as the minimum number of digits to be reproduced
        by the string representation (see function :func:`repr_`).
        """
        return self._reprdigits
    def _setreprdigits(self, value):
        if value is None:
            self._reprdigits = value
        else:
            self._reprdigits = int(value)
    reprdigits = property(_getreprdigits, _setreprdigits)

    def _getwarntrim(self):
        """True/False flag indicating whether a warning shall be raised
        whenever certain values needed to be trimmed due to violating
        certain boundaries. Such warnings increase savety and are thus
        the default is `True`.  However, to cope with the limited precision
        of floating point numbers only those violations beyond a small
        tolerance value are reported (see :class:`Trimmer`).  Warnings
        with identical information are reported only once.
        """
        return self._warntrim
    def _setwarntrim(self, value):
        self._warntrim = bool(value)
    warntrim = property(_getwarntrim, _setwarntrim)

    def _getwarnsimulationstep(self):
        """True/False flag indicating whether a warning shall be raised
        when function :func:`~hydpy.core.magictools.simulationstep` is
        called for the first time.
        """
        return self._warnsimulationstep
    def _setwarnsimulationstep(self, value):
        self._warnsimulationstep = bool(value)
    warnsimulationstep = property(_getwarnsimulationstep,
                                  _setwarnsimulationstep)

    def __dir__(self):
        return dir_(self)


def trim(self, lower=None, upper=None):
    """ToDo"""
    from hydpy.pub import options
    if lower is None:
        lower = self.SPAN[0]
    if upper is None:
        upper = self.SPAN[1]
    if self.NDIM == 0:
        if (lower is not None) and (self < lower):
            if (self+tolerance(self)) < (lower-tolerance(lower)):
                if options.warntrim:
                    self.warntrim()
            self.value = lower
        elif (upper is not None) and (self > upper):
            if (self-tolerance(self)) > (upper+tolerance(upper)):
                if options.warntrim:
                    self.warntrim()
            self.value = upper
    else:
        if (((lower is not None) and numpy.any(self.values < lower)) or
            ((upper is not None) and numpy.any(self.values > upper))):
            if (numpy.any((self+tolerance(self)) <
                          (lower-tolerance(lower))) or
                numpy.any((self-tolerance(self)) >
                          (upper+tolerance(upper)))):
                    if options.warntrim:
                        self.warntrim()
            self.values = numpy.clip(self.values, lower, upper)

def tolerance(values):
    return abs(values*1e-15)


class ValueMath(object):
    """Base class for :class:`~hydpy.core.parametertools.Parameter` and
    :class:`~hydpy.core.sequencetools.Sequence`.  Implements special
    methods for arithmetic calculations, comparisons and type conversions.

    The subclasses are required to provide the members `NDIM` (usually a
    class attribute) and `value` (usually a property).  But for testing
    purposes, one can simply add them as instance attributes.

    A few examples for 0-dimensional objects:

    >>> from hydpy.core.objecttools import ValueMath
    >>> vm0 = ValueMath()
    >>> vm0.NDIM = 0
    >>> vm0.value = 2.
    >>> print(vm0 + vm0)
    4.0
    >>> print(3. - vm0)
    1.0
    >>> vm0 /= 2.
    >>> print(vm0.value)
    1.0
    >>> print(vm0 > vm0)
    False
    >>> print(vm0 != 1.5)
    True

    Similar examples for 1-dimensional objects:

    >>> import numpy
    >>> vm1 = ValueMath()
    >>> vm1.NDIM = 1
    >>> vm1.value = numpy.array([1.,2.,3.])
    >>> print(vm1 + vm1)
    [ 2.  4.  6.]
    >>> print(3. - vm1)
    [ 2.  1.  0.]
    >>> vm1 /= 2.
    >>> print(vm1.value)
    [ 0.5  1.   1.5]
    >>> print(vm1 > vm1)
    [False False False]
    >>> print(vm1 != 1.5)
    [ True  True False]
    """

    # Subclasses need to define...
    NDIM = None # ... e.g. as class attribute (int)
    name = None # ... e.g. as property (str)
    value = None # ... e.g. as property (float or ndarray of dtype float)

    @staticmethod
    def _arithmetic_conversion(other):
        try:
            return other.value
        except AttributeError:
            return other

    def _arithmetic_exception(self, verb, other):
        augmentexcmessage('While trying to %s %s instance `%s` and %s `%s`'
                          % (verb, classname(self), self.name,
                             classname(other), other))

    def __add__(self, other):
        try:
            return self.value + self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('add', other)
    def __radd__(self, other):
        return self.__add__(other)
    def __iadd__(self, other):
        self.value = self.__add__(other)
        return self

    def __sub__(self, other):
        try:
            return self.value  - self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('subtract', other)
    def __rsub__(self, other):
        try:
            return self._arithmetic_conversion(other) - self.value
        except BaseException:
            self._arithmetic_exception('subtract', other)
    def __isub__(self, other):
        self.value = self.__sub__(other)
        return self

    def __mul__(self, other):
        try:
            return self.value * self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('multiply', other)
    def __rmul__(self, other):
        return self.__mul__(other)
    def __imul__(self, other):
        self.value = self.__mul__(other)
        return self

    def __truediv__(self, other):
        try:
            return self.value / self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('divide', other)
    def __rtruediv__(self, other):
        try:
            return self._arithmetic_conversion(other) / self.value
        except BaseException:
            self._arithmetic_exception('divide', other)
    def __itruediv__(self, other):
        self.value = self.__truediv__(other)
        return self

    def __floordiv__(self, other):
        try:
            return self.value // self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('floor divide', other)
    def __rfloordiv__(self, other):
        try:
            return self._arithmetic_conversion(other) // self.value
        except BaseException:
            self._arithmetic_exception('floor divide', other)
    def __ifloordiv__(self, other):
        self.value = self.__floordiv__(other)
        return self

    def __mod__(self, other):
        try:
            return self.value % self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('mod divide', other)
    def __rmod__(self, other):
        try:
            return self._arithmetic_conversion(other) % self.value
        except BaseException:
            self._arithmetic_exception('mod divide', other)
    def __imod__(self, other):
        self.value = self.__mod__(other)
        return self

    def __pow__(self, other):
        try:
            return self.value**self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('exponentiate', other)
    def __rpow__(self, other):
        try:
            return self._arithmetic_conversion(other)**self.value
        except BaseException:
            self._arithmetic_exception('exponentiate', other)
    def __ipow__(self, other):
        self.value = self.__pow__(other)
        return self

    def __neg__(self):
        return -self.value

    def __pos__(self):
        return +self.value

    def __abs__(self):
        return abs(self.value)

    def __invert__(self):
        return 1./self.value

    def __lt__(self, other):
        try:
            return self.value < self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (<)', other)

    def __le__(self, other):
        try:
            return self.value <= self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (<=)', other)

    def __eq__(self, other):
        try:
            return self.value == self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (==)', other)

    def __ne__(self, other):
        try:
            return self.value != self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (!=)', other)

    def __ge__(self, other):
        try:
            return self.value >= self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (>=)', other)

    def __gt__(self, other):
        try:
            return self.value > self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (>)', other)

    def _typeconversion(self, type_):
        if not self.NDIM:
            return type_(self.value)
        else:
            raise TypeError('The %s instance `%s` is %d-dimensional and thus '
                            'cannot be converted to a scalar %s value.'
                            % (classname(self), self.name, self.NDIM,
                               classname(type_)))

    def __float__(self):
        return self._typeconversion(float)

    def __int__(self):
        return self._typeconversion(int)

    def __round__(self, ndigits=0):
        return numpy.round(self.value, ndigits)

