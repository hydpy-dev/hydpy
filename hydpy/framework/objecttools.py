# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import inspect
import sys
# ...from site-packages
import numpy
# ...from HydPy
#from hydpy import pub
# (actual import moved to  dir_ method to avoid circular dependencies)

def dir_(self):
    """The prefered way for HydPy objects to respond to :func:`dir`.

    Note thedepencence on the `pub.options.dirverbose`.  If this option is
    set `True`, all attributes and methods of the given instance and its
    class (including those inherited from the parent classes) are returned:

    >>> from hydpy import pub
    >>> pub.options.dirverbose = True
    >>> from hydpy.framework.objecttools import dir_
    >>> class Test(object):
    ...     only_public_attribute =  None
    >>> print(len(dir_(Test())) > 1) # Long list, try it yourself...
    True

    If the option is set to `False`, only the `public` attributes and methods
    (which do need begin with `_`) are returned:

    >>> pub.options.dirverbose = False
    >>> print(dir_(Test())) # Short list with one single entry...
    ['only_public_attribute']

    """
    from hydpy import pub
    names = set()
    for thing in list(inspect.getmro(type(self))) + [self]:
        for name in vars(thing).iterkeys():
            if pub.options.dirverbose or not name.startswith('_'):
                names.add(name)
    return list(names)

def classname(self):
    """Return the class name of the given instance object or class.

    >>> from hydpy.framework.objecttools import classname
    >>> from hydpy import pub
    >>> print(classname(float))
    float
    >>> print(classname(pub.options))
    Options

    """
    if not inspect.isclass(self):
        self = type(self)
    return str(self).split("'")[1].split('.')[-1]

def instancename(self):
    """Return the class name of the given instance object or class in lower
    case letters.

    >>> from hydpy.framework.objecttools import instancename
    >>> from hydpy import pub
    >>> print(instancename(pub.options))
    options

    """
    return classname(self).lower()

def modulename(self):
    """Return the module name of the given instance object.

    >>> from hydpy.framework.objecttools import modulename
    >>> from hydpy import pub
    >>> print(modulename(pub.options))
    objecttools

    """
    return self.__module__.split('.')[-1]

def devicename(self):
    """Try to return the name of the (indirect) master 
    :class:`~hydpy.framework.devicetools.Node` or 
    :class:`~hydpy.framework.devicetools.Element` instance, 
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

class Options(object):
    
    def __init__(self):
        self._printprogress = True
        self._verbosedir = False
        self._reprcomments = True
        self._usecython = True
        self._refreshmodels = False

    def _getprintprogress(self):
        """ToDo"""
        return self._printprogress
    def _setprintprogress(self, value):
        self._printprogress = bool(value)
    printprogress = property(_getprintprogress, _setprintprogress)
    
    def _getdirverbose(self):
        """True/False flag that indicates, whether the listboxes for the member
        selection of the classes of the HydPy framework should be complete 
        (True) or restrictive (False).  The latter is more viewable and hence
        the default option."""
        return self._verbosedir
    def _setdirverbose(self, value):
        self._verbosedir = bool(value)
    dirverbose = property(_getdirverbose, _setdirverbose)
 
    def _getreprcomments(self):
        """True/False flag that indicates, whether comments shall be included
        in string representations of some classes of the HydPy framework or
        not.  The default is `True`."""
        return self._reprcomments
    def _setreprcomments(self, value):
        self._reprcomments = bool(value)
    reprcomments = property(_getreprcomments, _setreprcomments)

    def _getusecython(self):
        """..."""
        return self._usecython
    def _setusecython(self, value):
        self._usecython = bool(value)
    usecython = property(_getusecython, _setusecython)
    
    def _getrefreshmodels(self):
        """..."""
        return self._refreshmodels
    def _setrefreshmodels(self, value):
        self._refreshmodels = bool(value)
    refreshmodels = property(_getrefreshmodels, _setrefreshmodels)
        
    def __dir__(self):
        return dir_(self)


class Trimmer(object):

    def trim(self, lower=None, upper=None):
        if lower is None:
            lower = self.SPAN[0]
        if upper is None:
            upper = self.SPAN[1]
        if self.NDIM == 0:
            if (lower is not None) and (self < lower):
                if (self+self.tolerance(self)) < (lower-self.tolerance(lower)):
                    self.warntrim()
                self.value = lower
            elif (upper is not None) and (self > upper):
                if (self-self.tolerance(self)) > (upper+self.tolerance(upper)):
                    self.warntrim()                
                self.value = upper
        else:
            if (((lower is not None) and numpy.any(self.values < lower)) or 
                ((upper is not None) and numpy.any(self.values > upper))):
                if (numpy.any((self+self.tolerance(self)) < 
                              (lower-self.tolerance(lower))) or
                    numpy.any((self-self.tolerance(self)) > 
                              (upper+self.tolerance(upper)))):
                       self.warntrim() 
                self.values = numpy.clip(self.values, lower, upper)
    
    @staticmethod
    def tolerance(values):
        return abs(values*1e-15)

class ValueMath(object):
    """Base class for :class:`~hydpy.framework.parametertools.Parameter` and
    :class:`~hydpy.framework.sequencetools.Sequence`.  Implements special
    methods for arithmetic calculations, comparisons and type conversions.

    The subclasses are required to provide the members `NDIM` (usually a
    class attribute) and `value` (usually a property).  But for testing
    purposes, one can simply add them as instance attributes.

    A few examples for 0-dimensional objects:

    >>> from hydpy.framework.objecttools import ValueMath
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
        exc, message, traceback_ = sys.exc_info()
        message = ('While trying to %s %s instance `%s` and %s `%s`, the '
                   'following error occured:  %s'
                   % (verb, classname(self), self.name, classname(other),
                      other, message))
        raise exc, message, traceback_

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

    def __div__(self, other):
        try:
            return self.value / self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('divide', other)
    def __rdiv__(self, other):
        try:
            return self._arithmetic_conversion(other) / self.value
        except BaseException:
            self._arithmetic_exception('divide', other)
    def __idiv__(self, other):
        self.value = self.__div__(other)
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

    def __abs__(self,):
        return abs(self.value)

    def __nonzero__(self,):
        return self.value != 0.

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

    def __long__(self):
        return self._typeconversion(long)

    def __bool__(self):
        return self._typeconversion(bool)
