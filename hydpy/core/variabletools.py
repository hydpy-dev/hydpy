# -*- coding: utf-8 -*-
"""This module implements general features for defining and working with
parameters and sequences.

Feature more specific to either parameters or sequences are implemented
in modules :mod:`~hydpy.core.parametertools` and
:mod:`~hydpy.core.sequencetools` respectively.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import textwrap
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import autodoctools


_INT_NAN = -999999
"""Surrogate for `nan`, which is available for floating point values
but not for integer values."""


def trim(self, lower=None, upper=None):
    """Trim the value(s) of  a :class:`Variable` instance.

    One can pass the lower and/or the upper boundary as a function argument.
    Otherwise, boundary values are taken from the class attribute `SPAN`
    of the given :class:`Variable` instance, if available.

    Note that method :func:`trim` works differently on :class:`Variable`
    instances handling values of different types.  For floating point values,
    an actual trimming is performed.  Additionally, a warning message is
    raised if the trimming results in a change in value exceeding the
    threshold value defined by function :func:`_tolerance`.  (This warning
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
    elif type_ in (int, bool):
        if self.NDIM == 0:
            _trim_int_0d(self, lower, upper)
        else:
            _trim_int_nd(self, lower, upper)
    else:
        raise NotImplementedError(
            'Method `trim` can only be applied on parameters handling '
            'integer or floating point values, but value type of parameter '
            '`%s` is `%s`.' % (self.name, objecttools.classname(self.TYPE)))


def _trim_float_0d(self, lower, upper):
    if numpy.isnan(self.value):
        return
    if (lower is None) or numpy.isnan(lower):
        lower = -numpy.inf
    if (upper is None) or numpy.isnan(upper):
        upper = numpy.inf
    if self < lower:
        if (self+_tolerance(self)) < (lower-_tolerance(lower)):
            if pub.options.warntrim:
                self.warntrim()
        self.value = lower
    elif self > upper:
        if (self-_tolerance(self)) > (upper+_tolerance(upper)):
            if pub.options.warntrim:
                self.warntrim()
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
    if numpy.any(self < lower) or numpy.any(self > upper):
        if (numpy.any((self+_tolerance(self)) <
                      (lower-_tolerance(lower))) or
                numpy.any((self-_tolerance(self)) >
                          (upper+_tolerance(upper)))):
            if pub.options.warntrim:
                self.warntrim()
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
    idxs = numpy.where(self == _INT_NAN)
    self[idxs] = lower[idxs]
    if numpy.any(self < lower) or numpy.any(self > upper):
        raise ValueError(
            'At least one value of parameter `%s` of element `%s` is not '
            'valid.' % (self.name, objecttools.devicename(self)))
    self[idxs] = _INT_NAN


def _tolerance(values):
    """Returns some sort of "numerical accuracy" to be expected for the
    given floating point value, see method :func:`trim`."""
    return abs(values*1e-15)


class Variable(object):
    """Base class for :class:`~hydpy.core.parametertools.Parameter` and
    :class:`~hydpy.core.sequencetools.Sequence`.  Implements special
    methods for arithmetic calculations, comparisons and type conversions.

    The subclasses are required to provide the members `NDIM` (usually a
    class attribute) and `value` (usually a property).  But for testing
    purposes, one can simply add them as instance attributes.

    A few examples for 0-dimensional objects:

    >>> from hydpy.core.variabletools import Variable
    >>> v0 = Variable()
    >>> v0.NDIM = 0
    >>> v0.shape = ()
    >>> v0.value = 2.
    >>> print(v0 + v0)
    4.0
    >>> print(3. - v0)
    1.0
    >>> v0 /= 2.
    >>> print(v0.value)
    1.0
    >>> print(v0 > v0)
    False
    >>> print(v0 != 1.5)
    True
    >>> v0.length
    1

    Similar examples for 1-dimensional objects:

    >>> import numpy
    >>> v1 = Variable()
    >>> v1.NDIM = 1
    >>> v1.shape = (5,)
    >>> v1.value = numpy.array([1.,2.,3.])
    >>> print(v1 + v1)
    [ 2.  4.  6.]
    >>> print(3. - v1)
    [ 2.  1.  0.]
    >>> v1 /= 2.
    >>> print(v1.value)
    [ 0.5  1.   1.5]
    >>> print(v1 > v1)
    [False False False]
    >>> print(v1 != 1.5)
    [ True  True False]
    >>>
    >>> v1.length
    5
    """
    # Subclasses need to define...
    NDIM = None    # ... e.g. as class attribute (int)
    name = None    # ... e.g. as property (str)
    value = None   # ... e.g. as property (float or ndarray of dtype float)
    shape = None   # ... e.gl as property (tuple of values of type int)
    # ...and optionally...
    INIT = None

    @staticmethod
    def _arithmetic_conversion(other):
        try:
            return other.value
        except AttributeError:
            return other

    def _arithmetic_exception(self, verb, other):
        objecttools.augmentexcmessage(
            'While trying to %s %s instance `%s` and %s `%s`'
            % (verb, objecttools.classname(self), self.name,
               objecttools.classname(other), other))

    @property
    def length(self):
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
        return length

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
        return numpy.divmod(self.value, other)

    def __rdivmod__(self, other):
        return numpy.divmod(other, self.value)

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

    def __float__(self):
        return self._typeconversion(float)

    def __int__(self):
        return self._typeconversion(int)

    @property
    def real(self):
        return self._typeconversion('real')

    @property
    def imag(self):
        return self._typeconversion('imag')

    def conjugate(self):
        return self._typeconversion('conjugate')

    def __complex__(self):
        return numpy.complex(self.value)

    def __round__(self, ndigits=0):
        return numpy.round(self.value, ndigits)

    def commentrepr(self):
        """Returns a list with comments, e.g. for making string representations
        more informative.  When :attr:`pub.options.reprcomments` is set to
        `False`, an empty list is returned.
        """
        if pub.options.reprcomments:
            return ['# %s' % line for line in
                    textwrap.wrap(autodoctools.description(self), 78)]
        else:
            return []

    def _repr(self, values, islong):
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
            if islong:
                string = objecttools.assignrepr_list2(values, prefix, 75) + ')'
            else:
                string = objecttools.assignrepr_values2(values, prefix) + ')'
        else:
            raise NotImplementedError(
                '`repr` does not yet support parameters or sequences like `%s`'
                'of element `%s` which handle %d-dimensional matrices.'
                % self.NDIM)
        return '\n'.join(self.commentrepr() + [string])


autodoctools.autodoc_module()
