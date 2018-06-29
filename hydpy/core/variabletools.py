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
from hydpy.core import metatools
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

    This base class implements special methods for arithmetic calculations,
    comparisons and type conversions.  See the  following examples on how
    to do math with HydPys |Parameter| and |Sequence| objects.

    The subclasses are required to provide the members as `NDIM` (usually
    a class attribute) and `value` (usually a property).  For testing
    purposes, we simply add them as class attributes to a copy of class
    |Variable|.

    >>> from hydpy.core.objecttools import copy_class
    >>> from hydpy.core.variabletools import Variable
    >>> Variable = copy_class(Variable)
    >>> variable = Variable()

    A few examples for 0-dimensional objects:

    >>> Variable.NDIM = 0
    >>> Variable.shape = ()
    >>> Variable.value = 2.0
    >>> variable + variable
    4.0
    >>> 3.0 - variable
    1.0
    >>> variable /= 2.
    >>> variable
    variable(1.0)
    >>> variable[0] = 2.0 * variable[:]
    >>> variable[0]
    2.0
    >>> variable[1]
    Traceback (most recent call last):
    ...
    IndexError: While trying to access the value(s) of variable `variable` \
with key `1`, the following error occured: The only allowed keys for \
0-dimensional variables are `0` and `:`.


    Similar examples for 1-dimensional objects:

    >>> import numpy
    >>> Variable.NDIM = 1
    >>> Variable.shape = (3,)
    >>> variable.value = numpy.array([1.0, 2.0, 3.0])
    >>> print(variable + variable)
    [ 2.  4.  6.]
    >>> print(3. - variable)
    [ 2.  1.  0.]
    >>> variable /= 2.
    >>> variable
    variable(0.5, 1.0, 1.5)
    >>> variable[:] = variable[1]
    >>> variable[:2]
    array([ 1.,  1.])
    >>> variable[:] = 'test'
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `variable` \
with key `slice(None, None, None)`, the following error occured: \
could not convert string to float: 'test'

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

    >>> Variable.NDIM = 0
    >>> Variable.value = 1.0
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
        """Actual value or |numpy.ndarray| of the actual values, to be
        defined by the subclasses of |Variable|."""
        raise NotImplementedError

    def _get_values(self):
        """Alias for |Variable.value|."""
        return self.value

    def _set_values(self, values):
        self.value = values

    values = property(_get_values, _set_values)

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

        >>> from hydpy.core.objecttools import copy_class
        >>> from hydpy.core.variabletools import Variable
        >>> Variable = copy_class(Variable)
        >>> variable = Variable()
        >>> Variable.NDIM = 0
        >>> variable.length
        1

        For 1-dimensional sequences, it is the vector length:

        >>> Variable.NDIM = 1
        >>> Variable.shape = (5,)
        >>> variable.length
        5

        For higher dimensional sequences, the lenghts of the different axes
        of the matrix are multiplied:

        >>> Variable.NDIM = 3
        >>> Variable.shape = (2, 1, 4)
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

    @property
    def refweights(self):
        """Reference to a |Parameter| object that defines weighting
        coefficients (e.g. fractional areas) for calculating
        |Variable.meanvalue|.  Must be overwritten by subclasses,
        when required."""
        raise NotImplementedError(
            'Variable %s does not define any weighting coefficients.'
            % objecttools.devicephrase(self))

    @property
    def meanvalue(self):
        """Mean value.

        For 0-dimensional |Variable| objects, |Variable.meanvalue|
        equals |Variable.value|.  The following example showns this
        for the sloppily defined class `SoilMoisture`:

        >>> from hydpy.core.variabletools import Variable
        >>> class SoilMoisture(Variable):
        ...     NDIM = 0
        ...     value = 200.0
        >>> soilmoisture = SoilMoisture()
        >>> soilmoisture.meanvalue
        200.0

        When the dimensionality of this class is increased to one,
        querying |Variable.meanvalue| results in the following error:

        >>> SoilMoisture.NDIM = 1
        >>> import numpy
        >>> SoilMoisture.shape = (3,)
        >>> SoilMoisture.values = numpy.array([200.0, 400.0, 500.0])
        >>> soilmoisture.meanvalue
        Traceback (most recent call last):
        ...
        NotImplementedError: While trying to calculate the mean value \
of variable `soilmoisture` , the following error occured: Variable \
`soilmoisture` does not define any weighting coefficients.

        So model developers have to define another (in this case
        1-dimensional) |Variable| subclass (usually a |MultiParameter|
        subclass), and make the relevant object available via property
        |Variable.refweights|:

        >>> class Area(Variable):
        ...     shape = (3,)
        ...     values = numpy.array([1.0, 1.0, 2.0])
        >>> area = Area()
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> soilmoisture.meanvalue
        400.0

        In the examples above are all single entries of `values` relevant,
        which is the default case.  But subclasses of |Variable| can
        define an alternative |Variable.mask|, allowing to make some
        entries irrelevant. Assume for example, that our `SoilMoisture`
        object contains three single values, because each one is
        associated with a specific hydrological response unit.  To
        indicate that soil moisture is not defined for the third unit,
        (maybe because it is a water area), we set the third entry of
        the verification mask to |False|:

        >>> SoilMoisture.mask = numpy.array([True, True, False])
        >>> soilmoisture.meanvalue
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to calculate the mean value of \
variable `soilmoisture` based on weighting parameter `area`, the \
following error occured: The verification matrices of parameters \
`soilmoisture` and `area` are inconsistent.

        This error message tells us, that we have to adapt the
        verification mask of the `Area` object (and to make the
        result reasonable, also its `values` attribute.  Now the
        calculated mean valuereflects the area and the soil moisture
        of the first to hydrological response units only:

        >>> Area.mask = numpy.array([True, True, False])
        >>> Area.values = numpy.array([0.25, 0.75, numpy.nan])
        >>> soilmoisture.meanvalue
        350.0

        For verification mask containing |False| only, |numpy.nan| is
        returned:

        >>> SoilMoisture.mask[:] = False
        >>> Area.mask[:] = False
        >>> soilmoisture.meanvalue
        nan
        """
        if not self.NDIM:
            return self.value
        try:
            weights = self.refweights
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to calculate the mean value of variable %s '
                % objecttools.devicephrase(self))
        try:
            idxs_w = weights.mask
            idxs_v = self.mask
            if any(idxs_w != idxs_v):
                raise RuntimeError(
                    'The verification matrices of parameters '
                    '`%s` and `%s` are inconsistent.'
                    % (self.name, weights.name))
            if any(idxs_w):
                return (
                    numpy.sum(weights.values[idxs_w]*self.values[idxs_v]) /
                    numpy.sum(weights.values[idxs_w]))
            return numpy.nan
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to calculate the mean value of variable %s '
                'based on weighting parameter `%s`'
                % (objecttools.devicephrase(self), weights.name))

    def __deepcopy__(self, memo):
        new = type(self)()
        for (key, value) in vars(self).items():
            if key not in self.NOT_DEEPCOPYABLE_MEMBERS:
                setattr(new, key, copy.deepcopy(value, memo))
        if self.NDIM:
            new.shape = self.shape
        new.value = self.value
        return new

    def __getitem__(self, key):
        try:
            if self.NDIM:
                return self.value[key]
            self._check_key(key)
            return self.value
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to access the value(s) of '
                'variable %s with key `%s`'
                % (objecttools.devicephrase(self), key))

    def __setitem__(self, key, value):
        try:
            if self.NDIM:
                self.value[key] = value
            else:
                self._check_key(key)
                self.value = value
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to set the value(s) of variable %s '
                'with key `%s`'
                % (objecttools.devicephrase(self), key))

    @staticmethod
    def _check_key(key):
        if key not in (0, slice(None, None, None)):
            raise IndexError(
                'The only allowed keys for 0-dimensional variables '
                'are `0` and `:`.')

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
                    textwrap.wrap(metatools.description(self), 78)]
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


class SubVariables(metatools.MetaSubgroupClass):
    """Base class for |SubParameters| and |SubSequences|.

    See class |SubParameters| for further information.
    """
    CLASSES = ()
    VARTYPE = None

    def __init__(self, variables, cls_fastaccess=None, cymodel=None):
        self.vars = variables
        self._init_fastaccess(cls_fastaccess, cymodel)
        for cls in self.CLASSES:
            setattr(self, objecttools.instancename(cls), cls())

    @property
    def name(self):
        """Must be implemented by subclasses."""
        return NotImplementedError()

    def __setattr__(self, name, value):
        """Attributes and methods should usually not be replaced.  Existing
        |Variable| attributes are protected in a way, that only their
        values are changed through assignements.  For new |Variable|
        attributes, additional `fastaccess` references are defined.  If you
        actually want to replace a parameter, you have to delete it first.
        """
        try:
            attr = getattr(self, name)
        except AttributeError:
            object.__setattr__(self, name, value)
            if isinstance(value, self.VARTYPE):
                value.connect(self)
        else:
            try:
                attr.value = value
            except AttributeError:
                raise RuntimeError(
                    '`%s` instances do not allow the direct replacement of '
                    'their members.  After initialization you should usually '
                    'only change parameter values through assignements.  '
                    'If you really need to replace a object member, '
                    'delete it beforehand.'
                    % objecttools.classname(self))

    def __iter__(self):
        for cls in self.CLASSES:
            name = objecttools.instancename(cls)
            yield getattr(self, name)

    def __contains__(self, variable):
        if isinstance(variable, self.VARTYPE):
            variable = type(variable)
        if variable in self.CLASSES:
            return True
        try:
            if issubclass(variable, self.VARTYPE):
                return False
        except TypeError:
            pass
        name = objecttools.instancename(self.VARTYPE)[:-3]
        raise TypeError(
            'The given %s is neither a %s class nor a %s instance.'
            % (objecttools.value_of_type(variable), name, name))

    def __repr__(self):
        lines = []
        if pub.options.reprcomments:
            lines.append('# %s object defined in module %s.'
                         % (objecttools.classname(self),
                            objecttools.modulename(self)))
            lines.append('# The implemented variables with their actual '
                         'values are:')
        for variable in self:
            try:
                lines.append('%s' % repr(variable))
            except BaseException:
                lines.append('%s(?)' % variable.name)
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


autodoctools.autodoc_module()
