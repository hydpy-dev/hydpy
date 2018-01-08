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
import copy
import textwrap
import types
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
    elif type_ is int:
        if self.NDIM == 0:
            _trim_int_0d(self, lower, upper)
        else:
            _trim_int_nd(self, lower, upper)
    elif type_ is bool:
        pass
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
    if numpy.any(self.values < lower) or numpy.any(self.values > upper):
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
    idxs = numpy.where(self.values == _INT_NAN)
    self[idxs] = lower[idxs]
    if numpy.any(self.values < lower) or numpy.any(self.values > upper):
        raise ValueError(
            'At least one value of parameter `%s` of element `%s` is not '
            'valid.' % (self.name, objecttools.devicename(self)))
    self[idxs] = _INT_NAN


def _tolerance(values):
    """Returns some sort of "numerical accuracy" to be expected for the
    given floating point value, see method :func:`trim`."""
    return abs(values*1e-15)


def _compare_variables_function_generator(
        method_string, aggregation_func):
    """Return a function that can be used as a comparison method of class
    :class:`Variable`.

    Pass the specific method (e.g. '__eq__') and the corresponding operator
    (e.g. `==`) as strings.  Also pass either :func:`all` or :func:`any`
    for aggregating multiple boolean values.
    """
    def comparison_function(self, other):
        method = getattr(self.value, method_string)
        try:
            if isinstance(other, abctools.Variable):
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
            objecttools.augmentexcmessage(
                'While trying to compare variable `{0!r}` of '
                'element `{1}` with object `{2}` of type `{3}`'
                .format(self, objecttools.devicename(self),
                        other, objecttools.classname(other)))
    return comparison_function


class Variable(object):
    """Base class for :class:`~hydpy.core.parametertools.Parameter` and
    :class:`~hydpy.core.sequencetools.Sequence`.

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

    Note that comparisons on :class:`Variable` objects containg multiple
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

    >>> variable < 'text'
    Traceback (most recent call last):
    ...
    TypeError: '<' not supported between instances of 'Variable' and 'str'

    >>> variable < [1.0, 2.0, 3.0]   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: While trying to compare variable `variable(1.0, 3.0)` of \
element `?` with object `[1.0, 2.0, 3.0]` of type `list`, the following \
error occured: operands could not be broadcast together with shapes (2,) (3,)
    """
    # Subclasses need to define...
    NDIM = None    # ... e.g. as class attribute (int)
    value = None   # ... e.g. as property (float or ndarray of dtype float)
    shape = None   # ... e.g. as property (tuple of values of type int)
    # ...and optionally...
    INIT = None

    NOT_DEEPCOPYABLE_MEMBERS = ()

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

    def __deepcopy__(self, memo):
        new = type(self)()
        for (key, value) in vars(self).items():
            if key not in self.NOT_DEEPCOPYABLE_MEMBERS:
                setattr(new, key, copy.deepcopy(value, memo))
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
        return numpy.divmod(self.value, other)

    def __rdivmod__(self, other):
        return numpy.divmod(other, self.value)

    __lt__ = _compare_variables_function_generator('__lt__', all)
    __le__ = _compare_variables_function_generator('__le__', all)
    __eq__ = _compare_variables_function_generator('__eq__', all)
    __ne__ = _compare_variables_function_generator('__ne__', any)
    __ge__ = _compare_variables_function_generator('__ge__', all)
    __gt__ = _compare_variables_function_generator('__gt__', all)

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
        return []

    def repr_(self, values, islong):
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

    def __repr__(self):
        return self.repr_(self.value, False)


class Variable2Auxfile(object):
    """Map :class:`Variable` objects to names of auxiliary files.

    In HydPy, parameter values are usually not shared between different
    model objects handled by different elements, even if the model objects
    are of the same type (e.g. HBV).  This offers flexibility in applying
    different parameterization schemes.  But very often, modellers prefer
    to use a very limited amount of values for certain parameters (at least
    within hydrologically homogeneous regions).  Hence, the downside of
    this flexibility is that the same parameter values might be defined in
    hundreds or even thousands of parameter control files (one file for
    each model/element).

    To decrease this redundancy, HydPy allows for passing names of
    `auxiliary` control files to parameters defined within `normal`
    control files.  The actual parameter values are than read from the
    auxiliary files, each one possibly referenced within a large number
    of control files.

    Reading parameters from `normal` and `auxiliary` control files is
    straightforward.   But storing some parameters in a large number
    of `normal` control files and some other parameters in a small number
    of `auxiliary`files can be a little complicated.  Class
    :class:`Variable2Auxfile` is one a means to perform such actions
    in a semi-automated manner (another means would be the selection
    mechanism implemented in module :mod:`~hydpy.core.selectiontools`).

    To show how :class class:`Variable2Auxfile` works, we firstly
    initialize a HydPy-L-Land (version 1) model:

    >>> from hydpy import pub
    >>> pub.options.usedefaultvalues = True
    >>> from hydpy.models.lland_v1 import *
    >>> parameterstep('1d')

    Note that we made use of the `usedefaultvalues` option.
    Hence, all parameters used in the following examples have
    some predefined values, e.g.:

    >>> eqb
    eqb(5000.0)

    Next, we initialize a :class:`Variable2Auxfile` object, which is
    supposed to allocate some calibration parameters related to runoff
    concentration to two axiliary files named `file1` and `file2`:

    >>> from hydpy.core.variabletools import Variable2Auxfile
    >>> v2af = Variable2Auxfile()

    Auxiliary file `file1` shall contain the actual values of parameters
    `eqb`, `eqi1` and `eqi2`:

    >>> v2af.file1 = eqb
    >>> v2af.file1 = eqi1, eqi2
    >>> v2af.file1
    [eqb(5000.0), eqi1(2000.0), eqi2(1000.0)]

     Auxiliary file `file2` shall contain the actual values of parameters
    `eqd1`, `eqd2` and (also!) of parameter `eqb`:

    >>> v2af.file2 = eqd1, eqd2
    >>> v2af.file2 = eqb
    Traceback (most recent call last):
    ...
    ValueError: While trying to extend the range of variables handled by the \
actual Variable2AuxFile object, the following error occured: You tried to \
allocate variable `eqb(5000.0)` to filename `file2`, but an equal `EQB` \
object has already been allocated to filename `file1`.
    >>> v2af.file2
    [eqd1(100.0), eqd2(50.0)]

    As explained by the error message, allocating the same parameter type
    with equal values to two different auxiliary files is not allowed.
    (If you really want to store equal values of the same type of parameter
    whithin different auxiliary files, work with selections instead.)

    Nevertheless, after changing the value of parameter `eqb`, it can be
    allocated to file name `file2`:

    >>> eqb *= 2
    >>> v2af.file2 = eqb
    >>> v2af.file2
    [eqb(10000.0), eqd1(100.0), eqd2(50.0)]

    The following example shows that the value of parameter `eqb` already
    allocated to `file1` has not been changed (this safety mechanism is
    accomplished via deep copying), and that all registered parameters can
    be viewed by using their names as an attribute names:

    >>> v2af.eqb
    [eqb(5000.0), eqb(10000.0)]

    The :class:`Variable2Auxfile` object defined above is also used in the
    documentation of the following class members.  Hence it is stored in
    the `dummies` object:

    >>> from hydpy import dummies
    >>> dummies.v2af = v2af


    The explanations above focus on parameter objects only.
    :class:`Variable2Auxfile` could be used to handle sequence objects
    as well, but possibly without a big benefit as long as `auxiliary
    condition files` are not supported.
    """

    def __init__(self):
        self.__dict__['__setattr__'] = \
            types.MethodType(object.__setattr__, self)
        self.__dict__['_type2filename2variable'] = {}
        del self.__setattr__

    def __getattr__(self, name):
        variables = self._sort_variables(self._yield_variables(name))
        if variables:
            return variables
        else:
            raise AttributeError(
                '`{0}` is neither a filename nor a name of a variable '
                'handled by the actual Variable2AuxFile object.'
                .format(name))

    def __setattr__(self, filename, variables):
        try:
            objecttools.valid_variable_identifier(filename)
            new_vars = objecttools.extract(
                variables, (abctools.Parameter, abctools.ConditionSequence))
            for new_var in new_vars:
                _type = type(new_var)
                fn2var = self._type2filename2variable.get(_type, {})
                for (reg_fn, reg_var) in fn2var.items():
                    if (reg_fn != filename) and (reg_var == new_var):
                        raise ValueError(
                            'You tried to allocate variable `{0!r}` to '
                            'filename `{1}`, but an equal `{2}` object has '
                            'already been allocated to filename `{3}`.'
                            .format(new_var, filename,
                                    objecttools.classname(new_var), reg_fn))
                fn2var[filename] = copy.deepcopy(new_var)
                self._type2filename2variable[_type] = fn2var
        except BaseException:
            objecttools.augmentexcmessage(
                'While trying to extend the range of variables handled by '
                'the actual Variable2AuxFile object')

    def remove(self, *values):
        """Remove the defined variables.

        The variables to be removed can be selected in two ways.  But the
        first example shows that passing nothing or an empty iterable to
        method :func:`~Variable2Auxfile.remove` does not remove any variable:

        >>> from hydpy import dummies
        >>> v2af = dummies.v2af
        >>> v2af.remove()
        >>> v2af.remove([])
        >>> from hydpy.core.objecttools import print_values
        >>> print_values(v2af.filenames)
        file1, file2
        >>> print_values(v2af.variables, width=30)
        eqb(5000.0), eqb(10000.0),
        eqd1(100.0), eqd2(50.0),
        eqi1(2000.0), eqi2(1000.0)

        The first option is to pass auxiliary file names:

        >>> v2af.remove('file1')
        >>> print_values(v2af.filenames)
        file2
        >>> print_values(v2af.variables)
        eqb(10000.0), eqd1(100.0), eqd2(50.0)

        The second option is, to pass variables of the correct type
        and value:

        >>> v2af = dummies.v2af
        >>> v2af.remove(v2af.eqb[0])
        >>> print_values(v2af.filenames)
        file1, file2
        >>> print_values(v2af.variables)
        eqb(10000.0), eqd1(100.0), eqd2(50.0), eqi1(2000.0), eqi2(1000.0)

        One can pass multiple variables or iterables containing variables
        at once:

        >>> v2af = dummies.v2af
        >>> v2af.remove(v2af.eqb, v2af.eqd1, v2af.eqd2)
        >>> print_values(v2af.filenames)
        file1
        >>> print_values(v2af.variables)
        eqi1(2000.0), eqi2(1000.0)

        Passing an argument that equals neither a registered file name or a
        registered variable results in the following exception:

        >>> v2af.remove('test')
        Traceback (most recent call last):
        ...
        ValueError: While trying to remove the given object `test` of type \
`str` from the actual Variable2AuxFile object, the following error occured:  \
`'test'` is neither a registered filename nor a registered variable.
        """
        for value in objecttools.extract(values, (str, abctools.Variable)):
            try:
                deleted_something = False
                for fn2var in list(self._type2filename2variable.values()):
                    for fn, var in list(fn2var.items()):
                        if value in (fn, var):
                            del fn2var[fn]
                            deleted_something = True
                if not deleted_something:
                    raise ValueError(
                        ' `{0!r}` is neither a registered filename nor a '
                        'registered variable.'.format(value))
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to remove the given object `{0}` of type '
                    '`{1}` from the actual Variable2AuxFile object'
                    .format(value, objecttools.classname(value)))

    @property
    def types(self):
        """A list of all handled variable types.

        >>> from hydpy import dummies
        >>> from hydpy.core.objecttools import print_values
        >>> print_values(dummies.v2af.types, width=50)
        <class 'hydpy.models.lland.lland_control.EQB'>,
        <class 'hydpy.models.lland.lland_control.EQD1'>,
        <class 'hydpy.models.lland.lland_control.EQD2'>,
        <class 'hydpy.models.lland.lland_control.EQI1'>,
        <class 'hydpy.models.lland.lland_control.EQI2'>
        """
        return sorted(self._type2filename2variable.keys(), key=str)

    @property
    def filenames(self):
        """A list of all handled auxiliary file names.

        >>> from hydpy import dummies
        >>> dummies.v2af.filenames
        ['file1', 'file2']
        """
        fns = set()
        for fn2var in self._type2filename2variable.values():
            fns.update(fn2var.keys())
        return sorted(fns)

    @property
    def variables(self):
        """A list of all handled variable objects.

        >>> from hydpy import dummies
        >>> from hydpy.core.objecttools import print_values
        >>> print_values(dummies.v2af.variables, width=30)
        eqb(5000.0), eqb(10000.0),
        eqd1(100.0), eqd2(50.0),
        eqi1(2000.0), eqi2(1000.0)
        """
        return self._sort_variables(self._yield_variables())

    def _yield_variables(self, name=None):
        for fn2var in self._type2filename2variable.values():
            for fn, var in fn2var.items():
                if name in (None, fn, var.name):
                    yield var

    @staticmethod
    def _sort_variables(variables):
        return sorted(variables, key=lambda x: (x.name, sum(x)))

    def get_filename(self, variable):
        """Return the auxiliary file name the given variable is allocated to
        or :class:`None` if the given variable is not allocated to any
        auxiliary file name.

        >>> from hydpy import dummies
        >>> eqb = dummies.v2af.eqb[0]
        >>> dummies.v2af.get_filename(eqb)
        'file1'
        >>> eqb += 500.0
        >>> dummies.v2af.get_filename(eqb)
        """
        fn2var = self._type2filename2variable.get(type(variable), {})
        for (fn, var) in fn2var.items():
            if var == variable:
                return fn
        return None

    def __deepcopy__(self, memo):
        new = type(self)()
        for (key, value) in vars(self).items():
            new.__dict__[key] = copy.deepcopy(value)
        return new

    def __dir__(self):
        """
        >>> from hydpy import dummies
        >>> from hydpy.core.objecttools import print_values
        >>> print_values(dir(dummies.v2af))
        eqb, eqd1, eqd2, eqi1, eqi2, file1, file2, filenames, get_filename,
        remove, types, variables
        """
        return (objecttools.dir_(self) +
                self.filenames +
                [objecttools.instancename(type_) for type_ in self.types])


abctools.Variable.register(Variable)


autodoctools.autodoc_module()
