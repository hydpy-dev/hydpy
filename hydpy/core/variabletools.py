# -*- coding: utf-8 -*-
"""This module implements general features for defining and working with
parameters and sequences.

Features more specific to either parameters or sequences are implemented
in modules |parametertools| and |sequencetools| respectively.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import copy
import textwrap
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import objecttools


_INT_NAN = -999999
"""Surrogate for `nan`, which is available for floating point values
but not for integer values."""


def trim(self, lower=None, upper=None):
    """Trim the value(s) of a |Variable| instance.

    One can pass the lower and/or the upper boundary as a function
    argument.  Otherwise, boundary values are taken from the class
    attribute `SPAN` of the given |Variable| instance, if available.

    Note that method |trim| works differently on |Variable| instances
    handling values of different types.  For floating point values,

    an actual trimming is performed.  Additionally, a warning message is
    raised if the trimming results in a change in value exceeding the
    threshold value defined by function |tolerance|.  (This warning
    message can be suppressed by setting the related option flag to False.)
    For integer values, instead of a warning an exception is raised.
    """
    span = getattr(self, 'SPAN', (None, None))
    if lower is None:
        lower = span[0]
    if upper is None:
        upper = span[1]
    type_ = getattr(self, 'TYPE', float)
    if type_ is float:
        if self.NDIM == 0:
            _trim_float_0d(self, lower, upper)
        else:
            _trim_float_nd(self, lower, upper)
    elif type_ is int:
        if self.NDIM == 0:
            _trim_int_0d(self, lower, upper)
        else:
            _trim_int_nd(self, lower, upper)
    elif type_ is bool:
        pass
    else:
        raise NotImplementedError(
            'Method `trim` can only be applied on parameters '
            'handling integer or floating point values, but '
            'value type of parameter `%s` is `%s`.'
            % (self.name, objecttools.classname(self.TYPE)))


def _trim_float_0d(self, lower, upper):
    if numpy.isnan(self.value):
        return
    if (lower is None) or numpy.isnan(lower):
        lower = -numpy.inf
    if (upper is None) or numpy.isnan(upper):
        upper = numpy.inf
    if self < lower:
        if (self+tolerance(self)) < (lower-tolerance(lower)):
            if pub.options.warntrim:
                self.warn_trim()
        self.value = lower
    elif self > upper:
        if (self-tolerance(self)) > (upper+tolerance(upper)):
            if pub.options.warntrim:
                self.warn_trim()
        self.value = upper


def _trim_float_nd(self, lower, upper):
    if lower is None:
        lower = -numpy.inf
    lower = numpy.full(self.shape, lower, dtype=float)
    lower[numpy.where(numpy.isnan(lower))] = -numpy.inf
    if upper is None:
        upper = numpy.inf
    upper = numpy.full(self.shape, upper, dtype=float)
    upper[numpy.where(numpy.isnan(upper))] = numpy.inf
    idxs = numpy.where(numpy.isnan(self.values))
    self[idxs] = lower[idxs]
    if numpy.any(self.values < lower) or numpy.any(self.values > upper):
        if (numpy.any((self+tolerance(self)) <
                      (lower-tolerance(lower))) or
                numpy.any((self-tolerance(self)) >
                          (upper+tolerance(upper)))):
            if pub.options.warntrim:
                self.warn_trim()
        self.values = numpy.clip(self.values, lower, upper)
    self[idxs] = numpy.nan


def _trim_int_0d(self, lower, upper):
    if lower is None:
        lower = _INT_NAN
    if upper is None:
        upper = -_INT_NAN
    if (self != _INT_NAN) and ((self < lower) or (self > upper)):
        raise ValueError(
            'The value `%d` of parameter `%s` of element `%s` is not valid.  '
            % (self.value, self.name, objecttools.devicename(self)))


def _trim_int_nd(self, lower, upper):
    if lower is None:
        lower = _INT_NAN
    lower = numpy.full(self.shape, lower, dtype=int)
    if upper is None:
        upper = -_INT_NAN
    upper = numpy.full(self.shape, upper, dtype=int)
    idxs = numpy.where(self.values == _INT_NAN)
    self[idxs] = lower[idxs]
    if numpy.any(self.values < lower) or numpy.any(self.values > upper):
        raise ValueError(
            'At least one value of parameter `%s` of element `%s` is not '
            'valid.' % (self.name, objecttools.devicename(self)))
    self[idxs] = _INT_NAN


def tolerance(values):
    """Return some sort of "numerical accuracy" to be expected for the
    given floating point value (see method |trim|)."""
    return abs(values*1e-15)


def _compare_variables_function_generator(
        method_string, aggregation_func):
    """Return a function that can be used as a comparison method of class
    |Variable|.

    Pass the specific method (e.g. '__eq__') and the corresponding
    operator (e.g. `==`) as strings.  Also pass either |all| or |any|
    for aggregating multiple boolean values.
    """
    def comparison_function(self, other):
        """Wrapper for comparison functions for class |Variable|."""
        try:
            method = getattr(self.value, method_string)
        except AttributeError:
            # in Python 2.7, `int` (but not `float`) defines
            # `__cmp__` instead of rich comparisons
            method = getattr(float(self.value), method_string)
        try:
            if isinstance(other, abctools.VariableABC):
                result = method(other.value)
            else:
                result = method(other)
            if result is NotImplemented:
                return result
            try:
                return aggregation_func(result)
            except TypeError:
                return result
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to compare variable `{0!r}` of '
                'element `{1}` with object `{2}` of type `{3}`'
                .format(self, objecttools.devicename(self),
                        other, objecttools.classname(other)))
    return comparison_function


class Variable(object):
    """Base class for |Parameter| and |Sequence|.

    This base class Implements special methods for arithmetic calculations,
    comparisons and type conversions.  See the  following exemples on how
    to do math with HydPys parameter and sequence objects.

    The subclasses are required to provide the members `NDIM` (usually a
    class attribute) and `value` (usually a property).  But for testing
    purposes, one can simply add them as instance attributes.

    A few examples for 0-dimensional objects:

    >>> from hydpy.core.variabletools import Variable
    >>> variable = Variable()
    >>> variable.NDIM = 0
    >>> variable.shape = ()
    >>> variable.value = 2.0
    >>> variable + variable
    4.0
    >>> 3.0 - variable
    1.0
    >>> variable /= 2.
    >>> variable
    variable(1.0)

    Similar examples for 1-dimensional objects:

    >>> import numpy
    >>> variable = Variable()
    >>> variable.NDIM = 1
    >>> variable.shape = (3,)
    >>> variable.value = numpy.array([1.0, 2.0, 3.0])
    >>> print(variable + variable)
    [ 2.  4.  6.]
    >>> print(3. - variable)
    [ 2.  1.  0.]
    >>> variable /= 2.
    >>> variable
    variable(0.5, 1.0, 1.5)

    Note that comparisons on |Variable| objects containg multiple
    values return a single boolean only:

    >>> variable.value = numpy.array([1.0, 3.0])
    >>> variable == [0.0, 2.0], variable == [1.0, 2.0], variable == [1.0, 3.0]
    (False, False, True)
    >>> variable != [0.0, 2.0], variable != [1.0, 2.0], variable != [1.0, 3.0]
    (True, True, False)

    While either the `==` or the `!=` operator returns `True` (but not both),
    this must not be the case for the operator pairs `<`and `>=` as well as
    `>` and `<=`:

    >>> variable < 2.0, variable < 3.0, variable < 4.0
    (False, False, True)
    >>> variable <= 2.0, variable <= 3.0, variable <= 4.0
    (False, True, True)
    >>> variable >= 0.0, variable >= 1.0, variable >= 2.0
    (True, True, False)
    >>> variable > 0.0, variable > 1.0, variable > 2.0
    (True, False, False)

    When asking for impossible comparisons, error messages like the following
    are returned:

    >>> variable < [1.0, 2.0, 3.0]   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: While trying to compare variable `variable(1.0, 3.0)` of \
element `?` with object `[1.0, 2.0, 3.0]` of type `list`, the following \
error occured: operands could not be broadcast together with shapes (2,) (3,)

    >>> variable.NDIM = 0
    >>> variable.value = 1.0
    >>> variable < 'text'   # doctest: +SKIP
    Traceback (most recent call last):
    ...
    TypeError: '<' not supported between instances of 'Variable' and 'str'

    .. testsetup::

        >>> from hydpy import pub
        >>> if pub.pyversion == 2:
        ...    assert variable < 'text'
        ... else:
        ...     try:
        ...         variable < 'text'
        ...     except TypeError:
        ...         pass

    """
    # Subclasses need to define...
    NDIM = None    # ... e.g. as class attribute (int)
    # ...and optionally...
    INIT = None

    @property
    def value(self):
        """Actual value or |ndarray| of the actual values, to be defined
        by the subclasses of |Variable|."""
        raise NotImplementedError

    @property
    def shape(self):
        """Shape information as |tuple| of |int| values, to be defined
        by the subclasses of |Variable|."""
        raise NotImplementedError

    NOT_DEEPCOPYABLE_MEMBERS = ()

    @staticmethod
    def _arithmetic_conversion(other):
        try:
            return other.value
        except AttributeError:
            return other

    def _arithmetic_exception(self, verb, other):
        objecttools.augment_excmessage(
            'While trying to %s %s instance `%s` and %s `%s`'
            % (verb, objecttools.classname(self), self.name,
               objecttools.classname(other), other))

    name = property(objecttools.name)

    @property
    def length(self):
        """Total number of all entries of the sequence.

        For 0-dimensional sequences, `length` is always one:

        >>> from hydpy.core.variabletools import Variable
        >>> variable = Variable()
        >>> Variable.NDIM = 0
        >>> variable.length
        1

        For 1-dimensional sequences, it is the vector length:

        >>> Variable.NDIM = 1
        >>> variable.shape = (5,)
        >>> variable.length
        5

        For higher dimensional sequences, the lenghts of the different axes
        of the matrix are multiplied:

        >>> Variable.NDIM = 3
        >>> variable.shape = (2, 1, 4)
        >>> variable.length
        8
        """
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
        return length

    @property
    def mask(self):
        """A |numpy.ndarray| with all entries being |True| of the same shape
        as the values handled by the respective |Variable| object.

        All entries being |True| indicates that method |Variable.verify|
        checks all entries of the |numpy.ndarray| storing the parameter
        values.  Overwrite |Variable.mask| for |Variable| subclasses,
        where certain entries do not need to be checked.

        >>> from hydpy.core.objecttools import copy_class
        >>> from hydpy.core.variabletools import Variable
        >>> Variable = copy_class(Variable)
        >>> Variable.shape = (2,3)
        >>> Variable().mask
        array([[ True,  True,  True],
               [ True,  True,  True]], dtype=bool)
        """
        return numpy.full(self.shape, True, dtype=bool)

    def verify(self):
        """Raises a |RuntimeError| if at least one of the required values
        of a |Variable| object is |None| or |numpy.nan|. Property
        |Variable.mask| defines, which values are considered to be
        necessary.

        Example on a 0-dimensional |Variable|:

        >>> from hydpy.core.objecttools import copy_class
        >>> from hydpy.core.variabletools import Variable
        >>> Variable = copy_class(Variable)
        >>> variable = Variable()
        >>> import numpy
        >>> Variable.shape = ()
        >>> Variable.value = 1.0
        >>> variable.verify()
        >>> Variable.value = numpy.nan
        >>> variable.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `variable`, 1 required value \
has not been set yet.

        Example on a 2-dimensional |Variable|:

        >>> Variable = copy_class(Variable)
        >>> variable = Variable()
        >>> Variable.shape = (2, 3)
        >>> Variable.value = numpy.ones((2,3))
        >>> Variable.value[:, 1] = numpy.nan
        >>> variable.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `variable`, 2 required values \
have not been set yet.

        >>> Variable.mask = variable.mask
        >>> Variable.mask[0, 1] = False
        >>> variable.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `variable`, 1 required value \
has not been set yet.

        >>> Variable.mask[1, 1] = False
        >>> variable.verify()
        """
        nmbnan = numpy.sum(numpy.isnan(
            numpy.array(self.value)[self.mask]))
        if nmbnan:
            if nmbnan == 1:
                text = 'value has'
            else:
                text = 'values have'
            raise RuntimeError(
                'For variable %s, %d required %s '
                'not been set yet.'
                % (objecttools.devicephrase(self), nmbnan, text))

    def __deepcopy__(self, memo):
        new = type(self)()
        for (key, value) in vars(self).items():
            if key not in self.NOT_DEEPCOPYABLE_MEMBERS:
                setattr(new, key, copy.deepcopy(value, memo))
        if self.NDIM:
            new.shape = self.shape
        new.value = self.value
        return new

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
            return self.value - self._arithmetic_conversion(other)
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

    def __floor__(self):
        return self.value // 1.

    def __ceil__(self):
        return numpy.ceil(self.value)

    def __trunc__(self):
        return numpy.trunc(self.value)

    def __divmod__(self, other):
        # pylint: disable=no-member
        return numpy.divmod(self.value, other)

    def __rdivmod__(self, other):
        # pylint: disable=no-member
        return numpy.divmod(other, self.value)

    __lt__ = _compare_variables_function_generator('__lt__', numpy.all)
    __le__ = _compare_variables_function_generator('__le__', numpy.all)
    __eq__ = _compare_variables_function_generator('__eq__', numpy.all)
    __ne__ = _compare_variables_function_generator('__ne__', numpy.any)
    __ge__ = _compare_variables_function_generator('__ge__', numpy.all)
    __gt__ = _compare_variables_function_generator('__gt__', numpy.all)

    def _typeconversion(self, type_):
        if not self.NDIM:
            if isinstance(type_, type):
                return type_(self.value)
            else:
                attr = getattr(self.value, type_)
                try:
                    return attr()
                except TypeError:
                    return attr
        else:
            raise TypeError(
                'The %s instance `%s` is %d-dimensional and thus '
                'cannot be converted to a scalar %s value.'
                % (objecttools.classname(self), self.name,
                   self.NDIM, objecttools.classname(type_)))

    def __bool__(self):
        return self._typeconversion(bool)

    def __nonzero__(self):
        return self.__bool__()

    def __float__(self):
        return self._typeconversion(float)

    def __int__(self):
        return self._typeconversion(int)

    def __complex__(self):
        return numpy.complex(self.value)

    def __round__(self, ndigits=0):
        return numpy.round(self.value, ndigits)

    def commentrepr(self):
        """Returns a list with comments, e.g. for making string
        representations more informative.  When `pub.options.reprcomments`
        is set to |False|, an empty list is returned.
        """
        if pub.options.reprcomments:
            return ['# %s' % line for line in
                    textwrap.wrap(autodoctools.description(self), 78)]
        return []

    def to_repr(self, values, islong):
        """Return a valid string representation of the actual |Variable|
        object."""
        prefix = '%s(' % self.name
        if self.NDIM == 0:
            string = '%s(%s)' % (self.name, objecttools.repr_(values))
        elif self.NDIM == 1:
            if islong:
                string = objecttools.assignrepr_list(values, prefix, 75) + ')'
            else:
                string = objecttools.assignrepr_values(
                    values, prefix, 75) + ')'
        elif self.NDIM == 2:
            string = objecttools.assignrepr_list2(values, prefix, 75) + ')'
        else:
            raise NotImplementedError(
                '`repr` does not yet support parameters or sequences like `%s`'
                'of element `%s` which handle %d-dimensional matrices.'
                % self.NDIM)
        return '\n'.join(self.commentrepr() + [string])

    def __repr__(self):
        return self.to_repr(self.value, False)


abctools.VariableABC.register(Variable)


autodoctools.autodoc_module()
