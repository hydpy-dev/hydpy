# -*- coding: utf-8 -*-
"""This module implements general features for defining and working with
model parameters and sequences.

Features more specific to either parameters or sequences are implemented
in modules |parametertools| and |sequencetools| respectively.
"""
# import...
# ...from standard library
import abc
import copy
import inspect
import textwrap
import warnings
from typing import *
# ...from site-packages
import numpy
# ...from HydPy
import hydpy
from hydpy.core import abctools
from hydpy.core import masktools
from hydpy.core import objecttools
if TYPE_CHECKING:
    from hydpy.core import parametertools
    from hydpy.core import sequencetools


GroupType = TypeVar(
    'GroupType',
    'parametertools.Parameters', 'sequencetools.Sequences')


SubgroupType = TypeVar(
    'SubgroupType',
    'parametertools.SubParameters', 'sequencetools.SubSequences')


INT_NAN: int = -999999
"""Surrogate for `nan`, which is available for floating point values
but not for integer values."""

TYPE2MISSINGVALUE = {float: numpy.nan,
                     int: INT_NAN,
                     bool: False}


def trim(self: 'Variable', lower=None, upper=None) -> None:
    """Trim the value(s) of a |Variable| instance.

    Usually, users do not need to apply function |trim| directly.
    Instead, some |Variable| subclasses implement their own `trim`
    methods relying on function |trim|.  Model developers should
    implement individual `trim` methods for their |Parameter| or
    |Sequence| subclasses when their boundary values depend on the
    actual project configuration (one example is soil moisture;
    its lowest possible value should possibly be zero in all cases,
    but its highest possible value could depend on another parameter
    defining the maximum storage capacity).

    For the following examples, we prepare a simple (not fully
    functional) |Variable| subclass, making use of function |trim|
    without any modifications.  Function |trim| works slightly
    different for variables handling |float|, |int|, and |bool|
    values.  We start with the most common content type |float|:

    >>> from hydpy.core.variabletools import trim, Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     TYPE = float
    ...     SPAN = 1.0, 3.0
    ...     trim = trim
    ...     initinfo = 2.0, False
    ...     __hydpy__connect_variable2subgroup__ = None

    First, we enable the printing of warning messages raised by function
    |trim|:

    >>> from hydpy import pub
    >>> pub.options.warntrim = True

    When not passing boundary values, function |trim| extracts them from
    class attribute `SPAN` of the given |Variable| instance, if available:

    >>> var = Var(None)
    >>> var.value = 2.0
    >>> var.trim()
    >>> var
    var(2.0)

    >>> var.value = 0.0
    >>> var.trim()
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `0.0` and `1.0`, respectively.
    >>> var
    var(1.0)

    >>> var.value = 4.0
    >>> var.trim()
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `4.0` and `3.0`, respectively.
    >>> var
    var(3.0)

    In the examples above, outlier values are set to the respective
    boundary value, accompanied by suitable warning messages.  For
    minimal deviations (defined by function |get_tolerance|), which
    might be due to precision problems only, outliers are trimmed
    but not reported:

    >>> var.value = 1.0 - 1e-15
    >>> var == 1.0
    False
    >>> trim(var)
    >>> var == 1.0
    True

    >>> var.value = 3.0 + 1e-15
    >>> var == 3.0
    False
    >>> var.trim()
    >>> var == 3.0
    True

    Use arguments `lower` and `upper` to override the (eventually)
    available `SPAN` entries:

    >>> var.trim(lower=4.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `3.0` and `4.0`, respectively.

    >>> var.trim(upper=3.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `4.0` and `3.0`, respectively.

    Function |trim| interprets both |None| and |numpy.nan| values as if
    no boundary value exists:

    >>> import numpy
    >>> var.value = 0.0
    >>> var.trim(lower=numpy.nan)
    >>> var.value = 5.0
    >>> var.trim(upper=numpy.nan)

    You can disable function |trim| via option |Options.trimvariables|:

    >>> with pub.options.trimvariables(False):
    ...     var.value = 5.0
    ...     var.trim()
    >>> var
    var(5.0)

    Alternatively, you can omit the warning messages only:

    >>> with pub.options.warntrim(False):
    ...     var.value = 5.0
    ...     var.trim()
    >>> var
    var(3.0)

    If a |Variable| subclass does not have (fixed) boundaries, give it
    either no `SPAN` attribute or a |tuple| containing |None| values:

    >>> del Var.SPAN
    >>> var.value = 5.0
    >>> var.trim()
    >>> var
    var(5.0)

    >>> Var.SPAN = (None, None)
    >>> var.trim()
    >>> var
    var(5.0)

    The above examples deal with a 0-dimensional |Variable| subclass.
    The following examples repeat the most relevant examples for a
    2-dimensional subclass:

    >>> Var.SPAN = 1.0, 3.0
    >>> Var.NDIM = 2
    >>> var.shape = 1, 3
    >>> var.values = 2.0
    >>> var.trim()

    >>> var.values = 0.0, 1.0, 2.0
    >>> var.trim()
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 0.  1.  2.]]` and `[[ 1.  1.  2.]]`, \
respectively.
    >>> var
    var([[1.0, 1.0, 2.0]])

    >>> var.values = 2.0, 3.0, 4.0
    >>> var.trim()
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 2.  3.  4.]]` and `[[ 2.  3.  3.]]`, \
respectively.
    >>> var
    var([[2.0, 3.0, 3.0]])

    >>> var.values = 1.0-1e-15, 2.0, 3.0+1e-15
    >>> var.values == (1.0, 2.0, 3.0)
    array([[False,  True, False]], dtype=bool)
    >>> var.trim()
    >>> var.values == (1.0, 2.0, 3.0)
    array([[ True,  True,  True]], dtype=bool)

    >>> var.values = 0.0, 2.0, 4.0
    >>> var.trim(lower=numpy.nan, upper=numpy.nan)
    >>> var
    var([[0.0, 2.0, 4.0]])

    >>> var.trim(lower=[numpy.nan, 3.0, 3.0])
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 0.  2.  4.]]` and `[[ 0.  3.  3.]]`, \
respectively.

    >>> var.values = 0.0, 2.0, 4.0
    >>> var.trim(upper=[numpy.nan, 1.0, numpy.nan])
    Traceback (most recent call last):
    ...
    UserWarning: For variable `var` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 0.  2.  4.]]` and `[[ 1.  1.  4.]]`, \
respectively.

    For |Variable| subclasses handling |float| values, setting outliers
    to the respective boundary value might often be an acceptable approach.
    However, this is often not the case for subclasses handling |int|
    values, which often serve as option flags (e.g. to enable/disable
    a certain hydrological process for different land-use types). Hence,
    function |trim| raises an exception instead of a warning and does
    not modify the wrong |int| value:

    >>> Var.TYPE = int
    >>> Var.NDIM = 0
    >>> Var.SPAN = 1, 3

    >>> var.value = 2
    >>> var.trim()
    >>> var
    var(2)

    >>> var.value = 0
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: The value `0` of parameter `var` of element `?` is not valid.
    >>> var
    var(0)
    >>> var.value = 4
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: The value `4` of parameter `var` of element `?` is not valid.
    >>> var
    var(4)

    >>> from hydpy import INT_NAN
    >>> var.value = 0
    >>> var.trim(lower=0)
    >>> var.trim(lower=INT_NAN)

    >>> var.value = 4
    >>> var.trim(upper=4)
    >>> var.trim(upper=INT_NAN)

    >>> Var.SPAN = 1, None
    >>> var.value = 0
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: The value `0` of parameter `var` of element `?` is not valid.
    >>> var
    var(0)

    >>> Var.SPAN = None, 3
    >>> var.value = 0
    >>> var.trim()
    >>> var.value = 4
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: The value `4` of parameter `var` of element `?` is not valid.

    >>> del Var.SPAN
    >>> var.value = 0
    >>> var.trim()
    >>> var.value = 4
    >>> var.trim()

    >>> Var.SPAN = 1, 3
    >>> Var.NDIM = 2
    >>> var.shape = (1, 3)
    >>> var.values = 2
    >>> var.trim()

    >>> var.values = 0, 1, 2
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: At least one value of parameter `var` of element `?` \
is not valid.
    >>> var
    var([[0, 1, 2]])
    >>> var.values = 2, 3, 4
    >>> var.trim()
    Traceback (most recent call last):
     ...
    ValueError: At least one value of parameter `var` of element `?` \
is not valid.
    >>> var
    var([[2, 3, 4]])


    >>> var.values = 0, 0, 2
    >>> var.trim(lower=[0, INT_NAN, 2])

    >>> var.values = 2, 4, 4
    >>> var.trim(upper=[2, INT_NAN, 4])

    For |bool| values, defining outliers does not make much sense,
    which is why function |trim| does nothing when applied on
    variables handling |bool| values:

    >>> Var.TYPE = bool
    >>> var.trim()

    If function |trim| encounters an unmanageable type, it raises an
    exception like the following:

    >>> Var.TYPE = str
    >>> var.trim()
    Traceback (most recent call last):
    ...
    NotImplementedError: Method `trim` can only be applied on parameters \
handling floating point, integer, or boolean values, but the "value type" \
of parameter `var` is `str`.

    >>> pub.options.warntrim = False
    """
    if hydpy.pub.options.trimvariables:
        if lower is None:
            lower = self.SPAN[0]
        if upper is None:
            upper = self.SPAN[1]
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
                f'Method `trim` can only be applied on parameters '
                f'handling floating point, integer, or boolean values, '
                f'but the "value type" of parameter `{self.name}` is '
                f'`{objecttools.classname(self.TYPE)}`.')


def _trim_float_0d(self, lower, upper):
    if numpy.isnan(self.value):
        return
    if (lower is None) or numpy.isnan(lower):
        lower = -numpy.inf
    if (upper is None) or numpy.isnan(upper):
        upper = numpy.inf
    if self < lower:
        old = self.value
        self.value = lower
        if (old + get_tolerance(old)) < (lower - get_tolerance(lower)):
            _warn_trim(self, oldvalue=old, newvalue=lower)
    elif self > upper:
        old = self.value
        self.value = upper
        if (old - get_tolerance(old)) > (upper + get_tolerance(upper)):
            _warn_trim(self, oldvalue=old, newvalue=upper)


def _trim_float_nd(self, lower, upper):
    values = self.values
    shape = values.shape
    if lower is None:
        lower = -numpy.inf
    lower = numpy.full(shape, lower, dtype=float)
    lower[numpy.where(numpy.isnan(lower))] = -numpy.inf
    if upper is None:
        upper = numpy.inf
    upper = numpy.full(shape, upper, dtype=float)
    upper[numpy.where(numpy.isnan(upper))] = numpy.inf
    idxs = numpy.where(numpy.isnan(values))
    values[idxs] = lower[idxs]
    if numpy.any(values < lower) or numpy.any(values > upper):
        old = values.copy()
        trimmed = numpy.clip(values, lower, upper)
        self.values = trimmed
        if (numpy.any((old + get_tolerance(old)) <
                      (lower - get_tolerance(lower))) or
                numpy.any((old - get_tolerance(old)) >
                          (upper + get_tolerance(upper)))):
            _warn_trim(self, oldvalue=old, newvalue=trimmed)
    values[idxs] = numpy.nan


def _trim_int_0d(self, lower, upper):
    if lower is None:
        lower = INT_NAN
    if (upper is None) or (upper == INT_NAN):
        upper = -INT_NAN
    if (self != INT_NAN) and ((self < lower) or (self > upper)):
        raise ValueError(
            f'The value `{self.value}` of parameter '
            f'{objecttools.elementphrase(self)} is not valid.')


def _trim_int_nd(self, lower, upper):
    if lower is None:
        lower = INT_NAN
    lower = numpy.full(self.shape, lower, dtype=int)
    if upper is None:
        upper = -INT_NAN
    upper = numpy.full(self.shape, upper, dtype=int)
    upper[upper == INT_NAN] = -INT_NAN
    idxs = numpy.where(self.values == INT_NAN)
    self[idxs] = lower[idxs]
    if numpy.any(self.values < lower) or numpy.any(self.values > upper):
        raise ValueError(
            f'At least one value of parameter '
            f'{objecttools.elementphrase(self)} is not valid.')
    self[idxs] = INT_NAN


def get_tolerance(values):
    """Return some "numerical accuracy" to be expected for the
    given floating point value(s).

    The documentation on function |trim| explains also function
    |get_tolerance|.  However, note the special case of infinite
    input values, for which function |get_tolerance| returns zero:

    >>> from hydpy.core.variabletools import get_tolerance
    >>> import numpy
    >>> get_tolerance(numpy.inf)
    0.0
    >>> from hydpy import round_
    >>> round_(get_tolerance(
    ...     numpy.array([1.0, numpy.inf, 2.0, -numpy.inf])), 16)
    0.000000000000001, 0.0, 0.000000000000002, 0.0
    """
    tolerance = numpy.abs(values*1e-15)
    if hasattr(tolerance, '__setitem__'):
        tolerance[numpy.isinf(tolerance)] = 0.
    elif numpy.isinf(tolerance):
        tolerance = 0.
    return tolerance


def _warn_trim(self, oldvalue, newvalue):
    if hydpy.pub.options.warntrim:
        warnings.warn(
            f'For variable {objecttools.devicephrase(self)} at least one '
            f'value needed to be trimmed.  The old and the new value(s) '
            f'are `{oldvalue}` and `{newvalue}`, respectively.')


def _compare_variables_function_generator(
        method_string, aggregation_func):
    """Return a function to be used as a comparison method for class |Variable|.

    Pass the specific method (e.g. `__eq__`) and the corresponding
    operator (e.g. `==`) as strings.  Also pass either |numpy.all| or
    |numpy.any| for aggregating multiple boolean values.
    """
    def comparison_function(self, other):
        """Wrapper for comparison functions for class |Variable|."""
        if self is other:
            return method_string in ('__eq__', '__le__', '__ge__')
        method = getattr(self.value, method_string)
        try:
            if hasattr(type(other), '__hydpy__get_value__'):
                other = other.__hydpy__get_value__()
            result = method(other)
            if result is NotImplemented:
                return result
            return aggregation_func(result)
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to compare variable '
                f'{objecttools.elementphrase(self)} with object '
                f'`{other}` of type `{objecttools.classname(other)}`')
    return comparison_function


class Variable(Generic[SubgroupType]):
    """Base class for |Parameter| and |Sequence|.

    The subclasses are required to provide the class attributes `NDIM`
    and `TYPE`, defining the dimensionality and the type of the values
    to be handled by the subclass, respectively.  Class attribute `INIT`
    is optional and should provide a suitable default value.

    Class |Variable| implements methods for arithmetic calculations,
    comparisons and type conversions.  See the  following examples on
    how to do math with HydPys |Parameter| and |Sequence| objects.

    We start with demonstrating the supported mathematical operations
    on 0-dimensional |Variable| objects handling |float| values:

    >>> import numpy
    >>> from hydpy.core.variabletools import Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     TYPE = float
    ...     __hydpy__connect_variable2subgroup__ = None
    ...     initinfo = 0.0, False
    >>> var = Var(None)

    You can perform additions both with other |Variable| objects and
    with ordinary number objects:

    >>> var.value = 2.0
    >>> var + var
    4.0
    >>> var + 3.0
    5.0
    >>> 4.0 + var
    6.0
    >>> var += 1
    >>> var
    var(3.0)
    >>> var += -1.0
    >>> var
    var(2.0)

    In case something went wrong, all math operations return errors
    like the following:

    >>> var = Var(None)
    >>> var + 1.0
    Traceback (most recent call last):
    ...
    AttributeError: While trying to add variable `var` and `float` instance \
`1.0`, the following error occurred: For variable `var`, no value has been \
defined so far.

    In general, the examples above are valid for the following binary
    operations:

    >>> var.value = 3.0
    >>> var - 1
    2.0
    >>> 7.0 - var
    4.0
    >>> var -= 2.0
    >>> var
    var(1.0)

    >>> var.value = 2.0
    >>> var * 3
    6.0
    >>> 4.0 * var
    8.0
    >>> var *= 0.5
    >>> var
    var(1.0)

    >>> var.value = 3.0
    >>> var / 2
    1.5
    >>> 7.5 / var
    2.5
    >>> var /= 6.0
    >>> var
    var(0.5)

    >>> var.value = 3.0
    >>> var // 2
    1.0
    >>> 7.5 // var
    2.0
    >>> var //= 0.9
    >>> var
    var(3.0)

    >>> var.value = 5.0
    >>> var % 2
    1.0
    >>> 7.5 % var
    2.5
    >>> var %= 3.0
    >>> var
    var(2.0)

    >>> var.value = 2.0
    >>> var**3
    8.0
    >>> 3.0**var
    9.0
    >>> var **= 4.0
    >>> var
    var(16.0)

    >>> var.value = 5.0
    >>> divmod(var, 3)
    (1.0, 2.0)
    >>> divmod(13.0, var)
    (2.0, 3.0)

    Additionally, we support the following unary operations:

    >>> var.values = -5.0
    >>> +var
    -5.0
    >>> -var
    5.0
    >>> abs(var)
    5.0
    >>> ~var
    -0.2
    >>> var.value = 2.5
    >>> import math
    >>> math.floor(var)
    2
    >>> math.ceil(var)
    3
    >>> bool(var)
    True
    >>> int(var)
    2
    >>> float(var)
    2.5
    >>> var.value = 1.67
    >>> round(var, 1)
    1.7

    You can apply all the operations discussed above (except |float| and
    |int|) on |Variable| objects of arbitrary dimensionality:

    >>> Var.NDIM = 1
    >>> Var.TYPE = float
    >>> var.shape = (2,)
    >>> var.values = 2.0
    >>> var + var
    array([ 4.,  4.])
    >>> var + 3.0
    array([ 5.,  5.])
    >>> [4.0, 0.0] + var
    array([ 6.,  2.])
    >>> var += 1
    >>> var
    var(3.0, 3.0)

    >>> var.values = 3.0
    >>> var - [1.0, 0.0]
    array([ 2.,  3.])
    >>> [7.0, 0.0] - var
    array([ 4., -3.])
    >>> var -= [2.0, 0.0]
    >>> var
    var(1.0, 3.0)

    >>> var.values = 2.0
    >>> var * [3.0, 1.0]
    array([ 6.,  2.])
    >>> [4.0, 1.0] * var
    array([ 8.,  2.])
    >>> var *= [0.5, 1.0]
    >>> var
    var(1.0, 2.0)

    >>> var.values = 3.0
    >>> var / [2.0, 1.0]
    array([ 1.5,  3. ])
    >>> [7.5, 3.0] / var
    array([ 2.5,  1. ])
    >>> var /= [6.0, 1.]
    >>> var
    var(0.5, 3.0)

    >>> var.values = 3.0
    >>> var // [2.0, 1.0]
    array([ 1.,  3.])
    >>> [7.5, 3.0] // var
    array([ 2.,  1.])
    >>> var //= [0.9, 1.0]
    >>> var
    var(3.0, 3.0)

    >>> var.values = 5.0
    >>> var % [2.0, 5.0]
    array([ 1.,  0.])
    >>> [7.5, 5.0] % var
    array([ 2.5,  0. ])
    >>> var %= [3.0, 5.0]
    >>> var
    var(2.0, 0.0)

    >>> var.values = 2.0
    >>> var**[3.0, 1.0]
    array([ 8.,  2.])
    >>> [3.0, 1.0]**var
    array([ 9.,  1.])
    >>> var **= [4.0, 1.0]
    >>> var
    var(16.0, 2.0)

    >>> var.value = 5.0
    >>> divmod(var, [3.0, 5.0])
    (array([ 1.,  1.]), array([ 2.,  0.]))
    >>> divmod([13.0, 5.0], var)
    (array([ 2.,  1.]), array([ 3.,  0.]))

    >>> var.values = -5.0
    >>> +var
    array([-5., -5.])
    >>> -var
    array([ 5.,  5.])
    >>> abs(var)
    array([ 5.,  5.])
    >>> ~var
    array([-0.2, -0.2])
    >>> var.value = 2.5
    >>> import math
    >>> math.floor(var)
    array([2, 2])
    >>> math.ceil(var)
    array([3, 3])
    >>> var.values = 1.67
    >>> round(var, 1)
    array([ 1.7,  1.7])
    >>> bool(var)
    True
    >>> int(var)
    Traceback (most recent call last):
    ...
    TypeError: The variable `var` is 1-dimensional and thus cannot be \
converted to a scalar int value.
    >>> float(var)
    Traceback (most recent call last):
    ...
    TypeError: The variable `var` is 1-dimensional and thus cannot be \
converted to a scalar float value.

    Indexing is supported (for consistency reasons, even for
    0-dimensional variables):

    >>> Var.NDIM = 0
    >>> var.value = 5.0
    >>> var[0] += var[0]
    >>> var[:]
    10.0
    >>> var[1]
    Traceback (most recent call last):
    ...
    IndexError: While trying to access the value(s) of variable `var` \
with key `1`, the following error occurred: The only allowed keys for \
0-dimensional variables are `0` and `:`.

    >>> Var.NDIM = 1
    >>> var = Var(None)
    >>> var.shape = (5,)
    >>> var.value = 2.0, 4.0, 6.0, 8.0, 10.0
    >>> var[0]
    2.0
    >>> var[-1]
    10.0
    >>> var[1:-1:2] = 2.0 * var[1:-1:2]
    >>> var
    var(2.0, 8.0, 6.0, 16.0, 10.0)
    >>> var[:] = 'test'
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `var` \
with key `slice(None, None, None)`, the following error occurred: \
could not convert string to float: 'test'

    Comparisons with |Variable| objects containing multiple values
    return a single boolean value.  Two objects are equal if all of
    their value-pairs are equal, and they are unequal if at least
    one of their value-pairs is unequal:

    >>> var.shape = (2,)
    >>> var.values = 1.0, 3.0
    >>> var == [0.0, 2.0], var == [1.0, 2.0], var == [1.0, 3.0]
    (False, False, True)
    >>> var != [0.0, 2.0], var != [1.0, 2.0], var != [1.0, 3.0]
    (True, True, False)

    While either the `==` or the `!=` operator returns `True` (but not both),
    this must not be the case for the operator pairs `<`and `>=` as well as
    `>` and `<=`:

    >>> var < 2.0, var < 3.0, var < 4.0
    (False, False, True)
    >>> var <= 2.0, var <= 3.0, var <= 4.0
    (False, True, True)
    >>> var >= 0.0, var >= 1.0, var >= 2.0
    (True, True, False)
    >>> var > 0.0, var > 1.0, var > 2.0
    (True, False, False)

    Comparing wrongly shaped values does work for `==` and `!=` but
    results in errors for the other operations:

    >>> var.values = 2.0
    >>> var == [2.0], var != [2.0]
    (True, False)
    >>> var == [2.0, 2.0, 2.0], var != [2.0, 2.0, 2.0]
    (False, True)
    >>> var < [2.0], var <= [2.0], var >= [2.0], var > [2.0]
    (False, True, True, False)
    >>> var < [2.0, 2.0, 2.0]   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: While trying to compare variable `var` of element `?` \
with object `[2.0, 2.0, 2.0]` of type `list`, the following error occurred: \
operands could not be broadcast together with shapes (2,) (3,)...

    You can compare different |Variable| objects directly with each other:

    >>> from copy import deepcopy
    >>> var < var, var < deepcopy(var)
    (False, False)
    >>> var <= var, var <= deepcopy(var)
    (True, True)
    >>> var == var, var == deepcopy(var)
    (True, True)
    >>> var != var, var != deepcopy(var)
    (False, False)
    >>> var >= var, var >= deepcopy(var)
    (True, True)
    >>> var > var, var > deepcopy(var)
    (False, False)

    When asking for impossible comparisons, |trim| raises error
    like the following:

    >>> var < 'text'
    Traceback (most recent call last):
    ...
    TypeError: '<' not supported between instances of 'Var' and 'str'

    The |len| operator always returns the total number of values handles
    by the variable according to the current shape:

    >>> Var.NDIM = 0
    >>> var = Var(None)
    >>> var.shape = ()
    >>> len(var)
    1
    >>> Var.NDIM = 1
    >>> var = Var(None)
    >>> var.shape = (5,)
    >>> len(var)
    5
    >>> Var.NDIM = 3
    >>> var = Var(None)
    >>> var.shape = (2, 1, 4)
    >>> len(var)
    8

    |Variable| objects are hashable based on their |id| value for
    avoiding confusion when adding different but equal objects into
    one |set| or |dict| object.  The following examples show this
    behaviour by making deep copies of existing |Variable| objects:

    >>> Var.NDIM = 0
    >>> var1 = Var(None)
    >>> var1.value = 5.0
    >>> varset = set([var1])
    >>> var1 in varset
    True
    >>> var1.value = 7.0
    >>> var1 in varset
    True
    >>> var2 = deepcopy(var1)
    >>> var1 == var2
    True
    >>> var2 in varset
    False

    >>> Var.NDIM = 1
    >>> var1 = Var(None)
    >>> var1.shape = (2,)
    >>> var1.value = 3.0, 5.0
    >>> varset = set([var1])
    >>> var1 in varset
    True
    >>> var1[1] = 7.0
    >>> var1 in varset
    True
    >>> var2 = deepcopy(var1)
    >>> var1 == var2
    True
    >>> var2 in varset
    False

    Enabling option |Options.reprcomments| adds the respective docstring
    header to the string representation of a variable:

    >>> Var.NDIM = 0
    >>> Var.__doc__ = 'header.\\n\\nbody\\n'
    >>> var = Var(None)
    >>> var.value = 3.0
    >>> from hydpy import pub
    >>> pub.options.reprcomments = True
    >>> var
    # header.
    var(3.0)

    >>> pub.options.reprcomments = False
    >>> var
    var(3.0)
    """
    # Subclasses need to define...
    NDIM: ClassVar[int]
    TYPE: ClassVar[type]
    # ...and optionally...
    SPAN: ClassVar[Tuple[Union[int, float, bool, None],
                         Union[int, float, bool, None]]] = (None, None)
    INIT: ClassVar[Union[int, float, bool, None]] = None

    NOT_DEEPCOPYABLE_MEMBERS: Tuple[str, ...] = ('subvars', 'fastaccess')

    strict_valuehandling: ClassVar[bool] = True

    fastaccess: Union['FastAccess', abctools.FastAccessModelSequenceProtocol]
    subvars: SubgroupType

    mask = masktools.DefaultMask()

    def __init__(self, subvars: SubgroupType):
        self.subvars = subvars
        self.fastaccess = FastAccess()
        self.__valueready = False
        self.__shapeready = False

    @abc.abstractmethod
    def __hydpy__connect_variable2subgroup__(self) -> None:
        """To be called by the |SubVariables| object when preparing a
        new |Variable| object."""

    @property
    @abc.abstractmethod
    def initinfo(self) -> Tuple[Union[float, int, bool], bool]:
        """To be overridden."""

    def __hydpy__get_value__(self):
        """The actual parameter or sequence value(s).

        First, we prepare a simple (not fully functional) |Variable| subclass:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     __hydpy__connect_variable2subgroup__ = None
        ...     initinfo = 3.0, True

        Without making use of default values (see below), trying to
        query the actual value of a freshly initialised |Variable|
        object results in the following error:

        >>> var = Var(None)
        >>> var.value
        Traceback (most recent call last):
        ...
        AttributeError: For variable `var`, no value has been defined so far.

        Property |Variable.value| tries to normalise assigned values and
        raises an error, if not possible:

        >>> var.value = 3
        >>> var.value
        3.0

        >>> var.value = ['2.0']
        >>> var.value
        2.0

        >>> var.value = 1.0, 1.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the value(s) of variable `var`, the \
following error occurred: 2 values are assigned to the scalar variable `var`.
        >>> var.value
        2.0

        >>> var.value = 'O'
        Traceback (most recent call last):
        ...
        TypeError: While trying to set the value(s) of variable `var`, \
the following error occurred: The given value `O` cannot be converted \
to type `float`.
        >>> var.value
        2.0

        The above examples deal with a 0-dimensional variable handling
        |float| values.  The following examples focus on a 2-dimensional
        variable handling |int| values:

        >>> from hydpy import INT_NAN
        >>> Var.NDIM = 2
        >>> Var.TYPE = int
        >>> Var.initinfo = INT_NAN, False

        For multidimensional objects, assigning new values required
        defining their |Variable.shape| first:

        >>> var = Var(None)
        >>> var.value
        Traceback (most recent call last):
        ...
        AttributeError: Shape information for variable `var` can only be \
retrieved after it has been defined.

        >>> var.value = 2
        Traceback (most recent call last):
        ...
        AttributeError: While trying to set the value(s) of variable `var`, \
the following error occurred: Shape information for variable `var` can only \
be retrieved after it has been defined.

        >>> var.shape = (2, 3)
        >>> var.value
        Traceback (most recent call last):
        ...
        AttributeError: For variable `var`, no values have been defined so far.

        >>> var.value = 2
        >>> var.value
        array([[2, 2, 2],
               [2, 2, 2]])

        >>> var.value = 1, 2
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the value(s) of variable `var`, \
the following error occurred: While trying to convert the value(s) `(1, 2)` \
to a numpy ndarray with shape `(2, 3)` and type `int`, the following error \
occurred: could not broadcast input array from shape (2) into shape (2,3)
        >>> var.value
        array([[2, 2, 2],
               [2, 2, 2]])

        >>> var.shape = (0, 0)
        >>> var.shape
        (0, 0)
        >>> var.value   # doctest: +ELLIPSIS
        array([], shape=(0, 0), dtype=int...)
        """
        value = self._prepare_getvalue(
            self.__valueready or not self.strict_valuehandling,
            getattr(self.fastaccess, self.name, None))
        if value is None:
            substring = 'values have' if self.NDIM else 'value has'
            raise AttributeError(
                f'For variable {objecttools.devicephrase(self)}, '
                f'no {substring} been defined so far.')
        return value

    def __hydpy__set_value__(self, value) -> None:
        try:
            value = self._prepare_setvalue(value)
            setattr(self.fastaccess, self.name, value)
            self.__valueready = True
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to set the value(s) of variable '
                f'{objecttools.devicephrase(self)}')

    def _prepare_getvalue(self, readyflag: bool, value):
        if readyflag:
            if self.NDIM:
                return numpy.asarray(value)
            return self.TYPE(value)
        if self.NDIM and not sum(self.shape):
            return numpy.asarray(value)
        return None

    def _prepare_setvalue(self, value):
        if self.NDIM:
            value = getattr(value, 'value', value)
            try:
                value = numpy.full(self.shape, value, dtype=self.TYPE)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to convert the value(s) `{value}` '
                    f'to a numpy ndarray with shape `{self.shape}` '
                    f'and type `{objecttools.classname(self.TYPE)}`')
        else:
            if isinstance(value, Sequence):
                if len(value) > 1:
                    raise ValueError(
                        f'{len(value)} values are assigned to the scalar '
                        f'variable {objecttools.devicephrase(self)}.')
                value = value[0]
            try:
                value = self.TYPE(value)
            except BaseException:
                raise TypeError(
                    f'The given value `{value}` cannot be converted '
                    f'to type `{objecttools.classname(self.TYPE)}`.')
        return value

    value = property(fget=__hydpy__get_value__, fset=__hydpy__set_value__)

    @property
    def values(self):
        """Alias for |Variable.value|."""
        return self.__hydpy__get_value__()

    @values.setter
    def values(self, values):
        self.__hydpy__set_value__(values)

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        Note that setting a new |Variable.shape| results in a loss of
        the actual |Variable.values| of the respective |Variable| object.

        First, we prepare a simple (not fully functional) |Variable| subclass:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     NDIM = 1
        ...     TYPE = float
        ...     __hydpy__connect_variable2subgroup__ = None
        ...     initinfo = 3.0, True

        Initially, the shape of a new |Variable| object is unknown:

        >>> var = Var(None)
        >>> var.shape
        Traceback (most recent call last):
        ...
        AttributeError: Shape information for variable `var` can only be \
retrieved after it has been defined.

        For multidimensional objects, assigning shape information (as a
        |tuple| of |int| values) prepares the required array automatically.
        Due to the |Variable.initinfo| surrogate of our test class,
        the entries of this array are `3.0`:

        >>> var.shape = (3,)
        >>> var.shape
        (3,)
        >>> var.values
        array([ 3.,  3.,  3.])

        For the |Variable.initinfo| flag (second |tuple| entry) being
        |False|, the array is still prepared but not directly accessible
        to the user:

        >>> import numpy
        >>> Var.initinfo = numpy.nan, False
        >>> var = Var(None)

        >>> var.shape = (3,)
        >>> var.shape
        (3,)
        >>> var.values
        Traceback (most recent call last):
        ...
        AttributeError: For variable `var`, no values have been defined so far.
        >>> var.fastaccess.var
        array([ nan,  nan,  nan])

        Property |Variable.shape| tries to normalise assigned values and
        raises errors like the following, if not possible:

        >>> var.shape = 'x'
        Traceback (most recent call last):
        ...
        TypeError: While trying create a new numpy ndarray for \
variable `var`, the following error occurred: 'str' object cannot \
be interpreted as an integer
        >>> hasattr(var, 'shape')
        False
        >>> var.fastaccess.var

        >>> var.shape = (1,)
        >>> hasattr(var, 'shape')
        True

        >>> var.shape = (2, 3)
        Traceback (most recent call last):
        ...
        ValueError: Variable `var` is 1-dimensional, but the given \
shape indicates `2` dimensions.
        >>> hasattr(var, 'shape')
        False
        >>> var.fastaccess.var


        0-dimensional |Variable| objects inform the user about their shape
        but do not allow to change it for obvious reasons:

        >>> class Var(Variable):
        ...     NDIM = 0
        ...     TYPE = int
        ...     __hydpy__connect_variable2subgroup__ = None
        ...     initinfo = 3, True

        >>> var = Var(None)
        >>> var.shape
        ()
        >>> var.value
        Traceback (most recent call last):
        ...
        AttributeError: For variable `var`, no value has been defined so far.

        >>> var.shape = ()
        >>> var.shape
        ()
        >>> var.value
        3
        >>> var.shape = (2,)
        Traceback (most recent call last):
        ...
        ValueError: The shape information of 0-dimensional variables \
as `var` can only be `()`, but `(2,)` is given.

        With a |False| |Variable.initinfo| flag, the default value is
        still readily prepared after initialisation but not directly
        accessible to the user:

        >>> from hydpy import INT_NAN
        >>> Var.initinfo = INT_NAN, False
        >>> var = Var(None)
        >>> var.shape
        ()
        >>> var.shape = ()
        >>> hasattr(var, 'value')
        False
        >>> var.fastaccess.var
        -999999

        >>> var.value = 6
        >>> var.value
        6

        >>> var.shape = ()
        >>> var.fastaccess.var
        -999999
        """
        if self.NDIM:
            if self.__shapeready:
                shape = getattr(self.fastaccess, self.name).shape
                return tuple(int(x) for x in shape)
            raise AttributeError(
                f'Shape information for variable '
                f'{objecttools.devicephrase(self)} can only '
                f'be retrieved after it has been defined.')
        return ()

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]):
        self.__valueready = False
        self.__shapeready = False
        initvalue, initflag = self.initinfo
        if self.NDIM:
            try:
                array: numpy.ndarray = numpy.full(
                    shape, initvalue, dtype=self.TYPE)
            except BaseException:
                setattr(self.fastaccess, self.name, None)
                objecttools.augment_excmessage(
                    f'While trying create a new numpy ndarray for variable '
                    f'{objecttools.devicephrase(self)}')
            if array.ndim != self.NDIM:
                setattr(self.fastaccess, self.name, None)
                raise ValueError(
                    f'Variable {objecttools.devicephrase(self)} is '
                    f'{self.NDIM}-dimensional, but the given '
                    f'shape indicates `{array.ndim}` dimensions.')
            setattr(self.fastaccess, self.name, array)
            self.__shapeready = True
        else:
            if shape:
                setattr(self.fastaccess, self.name,
                        TYPE2MISSINGVALUE[self.TYPE])
                self._raise_wrongshape(shape)
            setattr(self.fastaccess, self.name, initvalue)
        if initflag:
            self.__valueready = True

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)

    def _raise_wrongshape(self, shape):
        raise ValueError(
            f'The shape information of 0-dimensional variables '
            f'as {objecttools.devicephrase(self)} can only be `()`, '
            f'but `{shape}` is given.')

    name = property(objecttools.name)

    def verify(self) -> None:
        """Raises a |RuntimeError| if at least one of the required values
        of a |Variable| object is |None| or |numpy.nan|. The descriptor
        `mask` defines, which values are considered to be necessary.

        Example on a 0-dimensional |Variable|:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     __hydpy__connect_variable2subgroup__ = None
        ...     initinfo = 0.0, False
        >>> var = Var(None)
        >>> import numpy
        >>> var.shape = ()
        >>> var.value = 1.0
        >>> var.verify()
        >>> var.value = numpy.nan
        >>> var.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `var`, 1 required value has not been set yet.

        Example on a 2-dimensional |Variable|:

        >>> Var.NDIM = 2
        >>> var = Var(None)
        >>> var.shape = (2, 3)
        >>> var.value = numpy.ones((2,3))
        >>> var.value[:, 1] = numpy.nan
        >>> var.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `var`, 2 required values \
have not been set yet.

        >>> Var.mask = var.mask
        >>> Var.mask[0, 1] = False
        >>> var.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `var`, 1 required value has not been set yet.

        >>> Var.mask[1, 1] = False
        >>> var.verify()
        """
        nmbnan: int = numpy.sum(numpy.isnan(
            numpy.array(self.value)[self.mask]))
        if nmbnan:
            if nmbnan == 1:
                text = 'value has'
            else:
                text = 'values have'
            raise RuntimeError(
                f'For variable {objecttools.devicephrase(self)}, '
                f'{nmbnan} required {text} not been set yet.')

    @property
    def refweights(self) -> 'Variable':
        """Reference to a |Parameter| object that defines weighting
        coefficients (e.g. fractional areas) for applying function
        |Variable.average_values|.  Must be overwritten by subclasses,
        when required."""
        raise AttributeError(
            f'Variable {objecttools.devicephrase(self)} does '
            f'not define any weighting coefficients.')

    def average_values(self, *args, **kwargs) -> float:
        """Average the actual values of the |Variable| object.

        For 0-dimensional |Variable| objects, the result of method
        |Variable.average_values| equals |Variable.value|.  The
        following example shows this for the sloppily defined class
        `SoilMoisture`:

        >>> from hydpy.core.variabletools import Variable
        >>> class SoilMoisture(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     refweigths = None
        ...     availablemasks = None
        ...     __hydpy__connect_variable2subgroup__ = None
        ...     initinfo = None
        >>> sm = SoilMoisture(None)
        >>> sm.value = 200.0
        >>> sm.average_values()
        200.0

        When the dimensionality of this class is increased to one,
        applying method |Variable.average_values| results in the
        following error:

        >>> SoilMoisture.NDIM = 1
        >>> import numpy
        >>> SoilMoisture.shape = (3,)
        >>> SoilMoisture.value = numpy.array([200.0, 400.0, 500.0])
        >>> sm.average_values()
        Traceback (most recent call last):
        ...
        AttributeError: While trying to calculate the mean value \
of variable `soilmoisture`, the following error occurred: Variable \
`soilmoisture` does not define any weighting coefficients.

        So model developers have to define another (in this case
        1-dimensional) |Variable| subclass (usually a |Parameter|
        subclass), and make the relevant object available via property
        |Variable.refweights|:

        >>> class Area(Variable):
        ...     NDIM = 1
        ...     shape = (3,)
        ...     value = numpy.array([1.0, 1.0, 2.0])
        ...     __hydpy__connect_variable2subgroup__ = None
        ...     initinfo = None
        >>> area = Area(None)
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> sm.average_values()
        400.0

        In the examples above, all single entries of `values` are relevant,
        which is the default case.  However, subclasses of |Variable| can
        define an alternative mask, allowing to make some entries
        irrelevant. Assume for example, that our `SoilMoisture` object
        contains three single values, each one associated with a specific
        hydrological response unit (hru).  To indicate that soil moisture
        is undefined for the third unit, (maybe because it is a water area),
        we set the third entry of the verification mask to |False|:

        >>> from hydpy.core.masktools import DefaultMask
        >>> class Soil(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask([True, True, False])
        >>> SoilMoisture.mask = Soil()
        >>> sm.average_values()
        300.0

        Alternatively, method |Variable.average_values| accepts additional
        masking information as positional or keyword arguments.  Therefore,
        the corresponding model must implement some alternative masks,
        which are provided by property |Variable.availablemasks|.
        We mock this property with a new |Masks| object, handling one
        mask for flat soils (only the first hru), one mask for deep soils
        (only the second hru), and one mask for water areas (only the
        third hru):

        >>> class FlatSoil(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask([True, False, False])
        >>> class DeepSoil(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask([False, True, False])
        >>> class Water(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask([False, False, True])
        >>> from hydpy.core import masktools
        >>> class Masks(masktools.Masks):
        ...     CLASSES = (FlatSoil,
        ...                DeepSoil,
        ...                Water)
        >>> SoilMoisture.availablemasks = Masks(None)

        One can pass either the mask classes themselves or their names:

        >>> sm.average_values(sm.availablemasks.flatsoil)
        200.0
        >>> sm.average_values('deepsoil')
        400.0

        Both variants can be combined:

        >>> sm.average_values(sm.availablemasks.deepsoil, 'flatsoil')
        300.0

        The following error happens if the general mask of the variable
        does not contain the given masks:

        >>> sm.average_values('flatsoil', 'water')
        Traceback (most recent call last):
        ...
        ValueError: While trying to calculate the mean value of variable \
`soilmoisture`, the following error occurred: Based on the arguments \
`('flatsoil', 'water')` and `{}` the mask `CustomMask([ True, False,  True])` \
has been determined, which is not a submask of `Soil([ True,  True, False])`.

        Applying masks with custom options is also supported.  One can change
        the behaviour of the following mask via the argument `complete`:

        >>> class AllOrNothing(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, complete):
        ...         if complete:
        ...             bools = [True, True, True]
        ...         else:
        ...             bools = [False, False, False]
        ...         return cls.array2mask(bools)
        >>> class Masks(Masks):
        ...     CLASSES = (FlatSoil,
        ...                DeepSoil,
        ...                Water,
        ...                AllOrNothing)
        >>> SoilMoisture.availablemasks = Masks(None)

        Again, one can apply the mask class directly (but note that one
        has to pass the relevant variable as the first argument.):

        >>> sm.average_values(   # doctest: +ELLIPSIS
        ...     sm.availablemasks.allornothing(sm, complete=True))
        Traceback (most recent call last):
        ...
        ValueError: While trying to...

        Alternatively, one can pass the mask name as a keyword and pack
        the mask's options into a |dict| object:

        >>> sm.average_values(allornothing={'complete': False})
        nan

        You can combine all variants explained above:

        >>> sm.average_values(
        ...     'deepsoil', flatsoil={}, allornothing={'complete': False})
        300.0
        """
        try:
            if not self.NDIM:
                return self.value
            mask = self.get_submask(*args, **kwargs)
            if numpy.any(mask):
                weights = self.refweights[mask]
                return numpy.sum(weights*self[mask])/numpy.sum(weights)
            return numpy.nan
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to calculate the mean value of variable '
                f'{objecttools.devicephrase(self)}')

    @property
    def availablemasks(self) -> masktools.Masks:
        """A |Masks| object provided by the corresponding |Model| object."""
        return self.subvars.vars.model.masks

    def get_submask(self, *args, **kwargs) -> masktools.CustomMask:
        """Get a sub-mask of the mask handled by the actual |Variable| object
        based on the given arguments.

        See the documentation on method |Variable.average_values| for
        further information.
        """
        if args or kwargs:
            masks = self.availablemasks
            mask = masktools.CustomMask(numpy.full(self.shape, False))
            for arg in args:
                mask = mask + self._prepare_mask(arg, masks)
            for key, value in kwargs.items():
                mask = mask + self._prepare_mask(key, masks, **value)
            if mask not in self.mask:
                raise ValueError(
                    f'Based on the arguments `{args}` and `{kwargs}` '
                    f'the mask `{repr(mask)}` has been determined, '
                    f'which is not a submask of `{repr(self.mask)}`.')
        else:
            mask = self.mask
        return mask

    def _prepare_mask(self, mask, masks, **kwargs):
        mask = masks[mask]
        if inspect.isclass(mask):
            return mask(self, **kwargs)
        return mask

    def __deepcopy__(self, memo):
        new = type(self)(None)
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
                f'While trying to access the value(s) of variable '
                f'{objecttools.devicephrase(self)} with key `{key}`')

    def __setitem__(self, key, value):
        try:
            if self.NDIM:
                self.value[key] = value
            else:
                self._check_key(key)
                self.value = value
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to set the value(s) of variable '
                f'{objecttools.devicephrase(self)} with key `{key}`')

    @staticmethod
    def _check_key(key):
        if key not in (0, slice(None, None, None)):
            raise IndexError(
                'The only allowed keys for 0-dimensional variables '
                'are `0` and `:`.')

    def __len__(self):
        try:
            return numpy.cumprod(self.shape)[-1]
        except IndexError:
            return 1

    def _do_math(self, other, methodname, description):
        try:
            if hasattr(type(other), '__hydpy__get_value__'):
                value = other.value
            else:
                value = other
            result = getattr(self.value, methodname)(value)
            if ((result is NotImplemented) and
                    (not self.NDIM) and (self.TYPE is int)):
                result = getattr(float(self.value), methodname)(value)
            return result
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to {description} variable '
                f'{objecttools.devicephrase(self)} and '
                f'`{objecttools.classname(other)}` instance `{other}`')

    def __add__(self, other):
        return self._do_math(other, '__add__', 'add')

    def __radd__(self, other):
        return self._do_math(other, '__radd__', 'add')

    def __iadd__(self, other):
        self.value = self._do_math(other, '__add__', 'add')
        return self

    def __sub__(self, other):
        return self._do_math(other, '__sub__', 'subtract')

    def __rsub__(self, other):
        return self._do_math(other, '__rsub__', 'subtract')

    def __isub__(self, other):
        self.value = self._do_math(other, '__sub__', 'subtract')
        return self

    def __mul__(self, other):
        return self._do_math(other, '__mul__', 'multiply')

    def __rmul__(self, other):
        return self._do_math(other, '__rmul__', 'multiply')

    def __imul__(self, other):
        self.value = self._do_math(other, '__mul__', 'multiply')
        return self

    def __truediv__(self, other):
        return self._do_math(other, '__truediv__', 'divide')

    def __rtruediv__(self, other):
        return self._do_math(other, '__rtruediv__', 'divide')

    def __itruediv__(self, other):
        self.value = self._do_math(other, '__truediv__', 'divide')
        return self

    def __floordiv__(self, other):
        return self._do_math(other, '__floordiv__', 'floor divide')

    def __rfloordiv__(self, other):
        return self._do_math(other, '__rfloordiv__', 'floor divide')

    def __ifloordiv__(self, other):
        self.value = self._do_math(other, '__floordiv__', 'floor divide')
        return self

    def __mod__(self, other):
        return self._do_math(other, '__mod__', 'mod divide')

    def __rmod__(self, other):
        return self._do_math(other, '__rmod__', 'mod divide')

    def __imod__(self, other):
        self.value = self._do_math(other, '__mod__', 'mod divide')
        return self

    def __divmod__(self, other):
        return self.__floordiv__(other), self.__mod__(other)

    def __rdivmod__(self, other):
        return self.__rfloordiv__(other), self.__rmod__(other)

    def __pow__(self, other):
        return self._do_math(other, '__pow__', 'exponentiate')

    def __rpow__(self, other):
        return self._do_math(other, '__rpow__', 'exponentiate (reflectively)')

    def __ipow__(self, other):
        self.value = self._do_math(other, '__pow__', 'exponentiate')
        return self

    def __pos__(self):
        return +self.value

    def __neg__(self):
        return -self.value

    def __abs__(self):
        return abs(self.value)

    def __invert__(self):
        return 1./self.value

    def __floor__(self):
        result = self.value // 1.
        try:
            return int(result)
        except TypeError:
            return numpy.array(result, dtype=int)

    def __ceil__(self):
        result = numpy.ceil(self.value)
        try:
            return int(result)
        except TypeError:
            return numpy.array(result, dtype=int)

    __lt__ = _compare_variables_function_generator('__lt__', numpy.all)
    __le__ = _compare_variables_function_generator('__le__', numpy.all)
    __eq__ = _compare_variables_function_generator('__eq__', numpy.all)
    __ne__ = _compare_variables_function_generator('__ne__', numpy.any)
    __ge__ = _compare_variables_function_generator('__ge__', numpy.all)
    __gt__ = _compare_variables_function_generator('__gt__', numpy.all)

    def _typeconversion(self, type_):
        if self.NDIM:
            raise TypeError(
                f'The variable {objecttools.devicephrase(self)} is '
                f'{self.NDIM}-dimensional and thus cannot be converted '
                f'to a scalar {objecttools.classname(type_)} value.')
        return type_(self.value)

    def __bool__(self):
        if self.NDIM:
            return bool(len(self))
        return bool(self.value)

    def __float__(self):
        return self._typeconversion(float)

    def __int__(self):
        return self._typeconversion(int)

    def __round__(self, ndigits=0):
        return numpy.round(self.value, ndigits)

    def __hash__(self):
        return id(self)

    @property
    def commentrepr(self) -> List[str]:
        """A list with comments for making string representations
        more informative.

        With option |Options.reprcomments| being disabled,
        |Variable.commentrepr| is empty.
        """
        if hydpy.pub.options.reprcomments:
            return [f'# {line}' for line in
                    textwrap.wrap(objecttools.description(self), 72)]
        return []

    def __repr__(self):
        return to_repr(self, self.value)


class SubVariables(Generic[GroupType]):
    """Base class for |SubParameters| and |SubSequences|.

    Each subclass of class |SubVariables| is thought for handling
    a certain group of |Parameter| or |Sequence| objects.  One
    specific example is subclass |InputSequences|, collecting all
    |InputSequence| objects of a specific hydrological model.

    For the following examples, we first prepare a (not fully
    functional) |Variable| subclass:

    >>> from hydpy.core.variabletools import SubVariables, Variable
    >>> class TestVar(Variable):
    ...     NDIM = 0
    ...     TYPE = float
    ...     __hydpy__connect_variable2subgroup__ = lambda self: None
    ...     initinfo = 0.0, False

    Out test |SubVariables| subclass is thought to handle only this
    single |Variable| subclass, indicated by putting it into the
    |tuple| class attribute `CLASSES`:

    >>> class SubVars(SubVariables):
    ...     CLASSES = (TestVar,)
    ...     def __hydpy__initialise_fastaccess__(self):
    ...         return None
    ...     name = 'subvars'

    After initialisation, |SubVariables| objects reference their master
    object (either a |Parameters| or a |Sequences| object), passed to their
    constructor. However, in our simple test example, we just passed
    a string instead:

    >>> subvars = SubVars('test')
    >>> subvars.vars
    'test'

    The string representation lists all available variables and,
    with the option |Options.reprcomments| enabled, an additional
    informative header:

    >>> subvars
    testvar(?)
    >>> from hydpy import pub
    >>> pub.options.reprcomments = True
    >>> subvars
    # SubVars object defined in module variabletools,
    # handling the following variables:
    testvar(?)
    >>> pub.options.reprcomments = False

    Class |SubVariables| provides attribute access to the handled
    |Variable| objects, and protects |Variable| objects from
    accidental overwriting:

    >>> subvars.testvar = 3.0
    >>> subvars.testvar
    testvar(3.0)

    Trying to query not available |Variable| objects (or other attributes)
    results in the following error message:

    >>> subvars.wrong
    Traceback (most recent call last):
    ...
    AttributeError: Collection object `subvars` does neither handle a \
variable nor another attribute named wrong.

    Class |SubVariables| protects only the handled |Variable| objects
    from overwriting with unplausible data:

    >>> subvars.vars = 'wrong'
    >>> subvars.vars
    'wrong'

    >>> subvars.testvar = 'wrong'
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `testvar`, \
the following error occurred: 5 values are assigned to the scalar \
variable `testvar`.

    Class |SubVariables| supporte iteration and the application of the
    |len| operator:

    >>> for variable in subvars:
    ...     print(variable.name)
    testvar
    >>> len(subvars)
    1
    """
    CLASSES: ClassVar[Tuple[Type[abctools.VariableProtocol], ...]]
    vars: GroupType
    _name2variable: Dict[str, abctools.VariableProtocol] = {}
    fastaccess: Union['FastAccess', abctools.FastAccessModelSequenceProtocol]
    _cls_fastaccess: Optional[Type[abctools.FastAccessModelSequenceProtocol]]

    def __init__(self, master: Any):
        self.vars = master
        self.__hydpy__initialise_fastaccess__()
        self._name2variable = {}
        for cls in self.CLASSES:
            variable = cls(self)
            self._name2variable[variable.name] = variable
            variable.__hydpy__connect_variable2subgroup__()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """To be overridden."""

    @abc.abstractmethod
    def __hydpy__initialise_fastaccess__(self) -> None:
        """To be overridden.  Must create a `fastaccess` attribute and build
        the required connections to the related cythonized model eventually."""

    def __getattr__(self, name):
        try:
            return self._name2variable[name]
        except KeyError:
            raise AttributeError(
                f'Collection object {objecttools.devicephrase(self)} '
                f'does neither handle a variable nor another attribute '
                f'named {name}.')

    def __setattr__(self, name, value):
        variable = self._name2variable.get(name)
        if variable is None:
            super().__setattr__(name, value)
        else:
            variable.__hydpy__set_value__(value)

    def __iter__(self):
        for variable in self._name2variable.values():
            yield variable

    def __len__(self):
        return len(self.CLASSES)

    def __repr__(self):
        lines = []
        if hydpy.pub.options.reprcomments:
            lines.append(f'# {objecttools.classname(self)} object defined '
                         f'in module {objecttools.modulename(self)},\n'
                         f'# handling the following variables:')
        for variable in self:
            try:
                lines.append(repr(variable))
            except BaseException:
                lines.append(f'{variable.name}(?)')
        return '\n'.join(lines)

    def __dir__(self):
        """
        >>> from hydpy.core.variabletools import SubVariables, Variable
        >>> class TestVar(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     __hydpy__connect_variable2subgroup__ = lambda self: None
        ...     initinfo = 0.0, False
        >>> class TestSubVars(SubVariables):
        ...     CLASSES = (TestVar,)
        ...     __hydpy__initialise_fastaccess__ = lambda self: None
        ...     name = None
        >>> dir(TestSubVars(None))
        ['CLASSES', 'name', 'testvar', 'vars']
        """
        return objecttools.dir_(self) + list(self._name2variable.keys())


def to_repr(self: Variable, values, brackets1d: Optional[bool] = False) \
        -> str:
    """Return a valid string representation for the given |Variable|
    object.

    Function |to_repr| is thought for internal purposes only, more
    specifically for defining string representations of subclasses
    of class |Variable| like the following:

    >>> from hydpy.core.variabletools import to_repr, Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     TYPE = int
    ...     __hydpy__connect_variable2subgroup__ = None
    ...     initinfo = 1.0, False
    >>> var = Var(None)
    >>> var.value = 2
    >>> var
    var(2)

    The following examples demonstrate all covered cases.  Note that
    option `brackets1d` allows choosing between a "vararg" and an
    "iterable" string representation for 1-dimensional variables
    (the first one being the default):

    >>> print(to_repr(var, 2))
    var(2)

    >>> Var.NDIM = 1
    >>> var = Var(None)
    >>> var.shape = 3
    >>> print(to_repr(var, range(3)))
    var(0, 1, 2)
    >>> print(to_repr(var, range(3), True))
    var([0, 1, 2])
    >>> print(to_repr(var, range(30)))
    var(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29)
    >>> print(to_repr(var, range(30), True))
    var([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
         19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29])

    >>> Var.NDIM = 2
    >>> var = Var(None)
    >>> var.shape = (2, 3)
    >>> print(to_repr(var, [range(3), range(3, 6)]))
    var([[0, 1, 2],
         [3, 4, 5]])
    >>> print(to_repr(var, [range(30), range(30, 60)]))
    var([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
          19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
         [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
          46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]])
    """
    prefix = f'{self.name}('
    if isinstance(values, str):
        string = f'{self.name}({values})'
    elif self.NDIM == 0:
        string = f'{self.name}({objecttools.repr_(values)})'
    elif self.NDIM == 1:
        if brackets1d:
            string = objecttools.assignrepr_list(values, prefix, 72) + ')'
        else:
            string = objecttools.assignrepr_values(
                values, prefix, 72) + ')'
    else:
        string = objecttools.assignrepr_list2(values, prefix, 72) + ')'
    return '\n'.join(self.commentrepr + [string])


class FastAccess:
    """Used as a surrogate for typed Cython classes handling parameters or
    sequences when working in pure Python mode."""
