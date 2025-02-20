# -*- coding: utf-8 -*-
"""This module implements general features for defining and working with model
parameters and sequences.

Features more specific to either parameters or sequences are implemented in modules
|parametertools| and |sequencetools|, respectively.
"""
# import...
# ...from standard library
from __future__ import annotations
import abc
import contextlib
import copy
import functools
import inspect
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import masktools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.cythons import pointerutils
    from hydpy.cythons import sequenceutils


TypeGroup_co = TypeVar(
    "TypeGroup_co",
    "parametertools.Parameters",
    "sequencetools.Sequences",
    "devicetools.Node",
    covariant=True,
)
TypeVariable = TypeVar("TypeVariable", bound="Variable")
TypeVariable_co = TypeVar("TypeVariable_co", bound="Variable", covariant=True)
TypeFastAccess_co = TypeVar("TypeFastAccess_co", bound="FastAccess", covariant=True)

INT_NAN: int = -999999
"""Surrogate for `nan`, which is available for floating-point values but not for 
integer values."""

TYPE2MISSINGVALUE = {float: numpy.nan, int: INT_NAN, bool: False}


def trim(self: Variable, lower=None, upper=None) -> bool:
    """Trim the value(s) of a |Variable| instance.

    The returned boolean indicates whether at least one value has been trimmed.

    Usually, users do not need to apply the |trim| function directly. Instead, some
    |Variable| subclasses implement their own `trim` methods relying on function |trim|.
    Model developers should implement individual `trim` methods for their |Parameter|
    or |Sequence_| subclasses when their boundary values depend on the actual project
    configuration (one example is soil moisture; its lowest possible value should
    possibly be zero in all cases, but its highest possible value could depend on
    another parameter defining the maximum storage capacity).

    For the following examples, we prepare a simple (not fully functional) |Variable|
    subclass, making use of function |trim| without any modifications.  Function |trim|
    works slightly different for variables handling |float|, |int|, and |bool| values.
    We start with the most common content type, |float|:

    >>> from hydpy.core.variabletools import trim, Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     TYPE = float
    ...     SPAN = 1.0, 3.0
    ...     trim = trim
    ...     initinfo = 2.0, False
    ...     _CLS_FASTACCESS_PYTHON = FastAccess

    First, we enable the printing of warning messages raised by function |trim|:

    >>> from hydpy import pub
    >>> pub.options.warntrim = True

    When not passing boundary values, function |trim| extracts them from class
    attribute `SPAN` of the given |Variable| instance, if available:

    >>> var = Var(None)
    >>> var.value = 2.0
    >>> assert var.trim() is False
    >>> var
    var(2.0)

    >>> var.value = 0.0
    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     assert var.trim() is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `0.0` and `1.0`, respectively.
    >>> var
    var(1.0)

    >>> var.value = 4.0
    >>> with warn_later():
    ...     assert var.trim() is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `4.0` and `3.0`, respectively.
    >>> var
    var(3.0)

    In the examples above, outlier values are set to the respective boundary value,
    accompanied by suitable warning messages.  For minimal deviations (defined by
    function |get_tolerance|), which might be due to precision problems only, outliers
    are trimmed but not reported:

    >>> var.value = 1.0 - 1e-15
    >>> var == 1.0
    False
    >>> assert trim(var) is False
    >>> var == 1.0
    True

    >>> var.value = 3.0 + 1e-15
    >>> var == 3.0
    False
    >>> assert var.trim() is False
    >>> var == 3.0
    True

    Use arguments `lower` and `upper` to override the (eventually) available `SPAN`
    entries:

    >>> with warn_later():
    ...     assert var.trim(lower=4.0) is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `3.0` and `4.0`, respectively.

    >>> with warn_later():
    ...     assert var.trim(lower=3.0) is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `4.0` and `3.0`, respectively.

    Function |trim| interprets both |None| and |numpy.nan| values as if no boundary
    value exists:

    >>> import numpy
    >>> var.value = 0.0
    >>> assert var.trim(lower=numpy.nan) is False
    >>> var.value = 5.0
    >>> assert var.trim(upper=numpy.nan) is False

    You can disable function |trim| via option |Options.trimvariables|:

    >>> with pub.options.trimvariables(False):
    ...     var.value = 5.0
    ...     assert var.trim() is False
    >>> var
    var(5.0)

    Alternatively, you can omit the warning messages only without modifying the return
    value:

    >>> with pub.options.warntrim(False):
    ...     var.value = 5.0
    ...     assert var.trim() is True
    >>> var
    var(3.0)

    If a |Variable| subclass does not have (fixed) boundaries, give it either no `SPAN`
    attribute or a |tuple| containing |None| values:

    >>> del Var.SPAN
    >>> var.value = 5.0
    >>> assert var.trim() is False
    >>> var
    var(5.0)

    >>> Var.SPAN = (None, None)
    >>> assert var.trim() is False
    >>> var
    var(5.0)

    The above examples deal with a 0-dimensional |Variable| subclass.  The following
    examples repeat the most relevant examples for a 2-dimensional subclass:

    >>> Var.SPAN = 1.0, 3.0
    >>> Var.NDIM = 2
    >>> var.shape = 1, 3
    >>> var.values = 2.0
    >>> assert var.trim() is False

    >>> var.values = 0.0, 1.0, 2.0
    >>> with warn_later():
    ...     assert var.trim() is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `0.0, 1.0, 2.0` and `1.0, 1.0, 2.0`, respectively.
    >>> var
    var(1.0, 1.0, 2.0)

    >>> var.values = 2.0, 3.0, 4.0
    >>> with warn_later():
    ...     assert var.trim() is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `2.0, 3.0, 4.0` and `2.0, 3.0, 3.0`, respectively.
    >>> var
    var(2.0, 3.0, 3.0)

    >>> from hydpy import print_matrix
    >>> var.values = 1.0-1e-15, 2.0, 3.0+1e-15
    >>> print_matrix(var.values == (1.0, 2.0, 3.0))
    | False, True, False |
    >>> assert var.trim() is False
    >>> print_matrix(var.values == (1.0, 2.0, 3.0))
    | True, True, True |

    >>> var.values = 0.0, 2.0, 4.0
    >>> assert var.trim(lower=numpy.nan, upper=numpy.nan) is False
    >>> var
    var(0.0, 2.0, 4.0)

    >>> with warn_later():
    ...     assert var.trim(lower=[numpy.nan, 3.0, 3.0]) is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `0.0, 2.0, 4.0` and `0.0, 3.0, 3.0`, respectively.

    >>> var.values = 0.0, 2.0, 4.0
    >>> with warn_later():
    ...     assert var.trim(upper=[numpy.nan, 1.0, numpy.nan]) is True
    UserWarning: For variable `var` at least one value needed to be trimmed.  The old \
and the new value(s) are `0.0, 2.0, 4.0` and `1.0, 1.0, 4.0`, respectively.

    For |Variable| subclasses handling |float| values, setting outliers to the
    respective boundary value might often be an acceptable approach.  However, this is
    often not the case for subclasses handling |int| values, which often serve as
    option flags (e.g. to enable/disable a certain hydrological process for different
    land-use types). Hence, function |trim| raises an exception instead of a warning
    and does not modify the wrong |int| value:

    >>> Var.TYPE = int
    >>> Var.NDIM = 0
    >>> Var.SPAN = 1, 3

    >>> var.value = 2
    >>> assert var.trim() is False
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
    >>> assert var.trim(lower=0) is False
    >>> assert var.trim(lower=INT_NAN) is False

    >>> var.value = 4
    >>> assert var.trim(upper=4) is False
    >>> assert var.trim(upper=INT_NAN) is False

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
    >>> assert var.trim() is False
    >>> var.value = 4
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: The value `4` of parameter `var` of element `?` is not valid.

    >>> del Var.SPAN
    >>> var.value = 0
    >>> assert var.trim() is False
    >>> var.value = 4
    >>> assert var.trim() is False

    >>> Var.SPAN = 1, 3
    >>> Var.NDIM = 2
    >>> var.shape = (1, 3)
    >>> var.values = 2
    >>> assert var.trim() is False

    >>> var.values = 0, 1, 2
    >>> var.trim()
    Traceback (most recent call last):
    ...
    ValueError: At least one value of parameter `var` of element `?` is not valid.
    >>> var
    var(0, 1, 2)
    >>> var.values = 2, 3, 4
    >>> var.trim()
    Traceback (most recent call last):
     ...
    ValueError: At least one value of parameter `var` of element `?` is not valid.
    >>> var
    var(2, 3, 4)


    >>> var.values = 0, 0, 2
    >>> assert var.trim(lower=[0, INT_NAN, 2]) is False

    >>> var.values = 2, 4, 4
    >>> assert var.trim(upper=[2, INT_NAN, 4]) is False

    For |bool| values, defining outliers does not make much sense, which is why
    function |trim| does nothing when applied to variables handling |bool| values:

    >>> Var.TYPE = bool
    >>> assert var.trim() is False

    If function |trim| encounters an unmanageable type, it raises an exception like the
    following:

    >>> Var.TYPE = str
    >>> var.trim()
    Traceback (most recent call last):
    ...
    NotImplementedError: Method `trim` can only be applied on parameters handling \
floating-point, integer, or boolean values, but the "value type" of parameter `var` \
is `str`.

    >>> pub.options.warntrim = False
    """
    if hydpy.pub.options.trimvariables:
        if lower is None:
            lower = self.SPAN[0]
        if upper is None:
            upper = self.SPAN[1]
        type_ = getattr(self, "TYPE", float)
        if type_ is float:
            if self.NDIM == 0:
                return _trim_float_0d(self, lower, upper)
            return _trim_float_nd(self, lower, upper)
        if type_ is int:
            if self.NDIM == 0:
                return _trim_int_0d(self, lower, upper)
            return _trim_int_nd(self, lower, upper)
        if type_ is bool:
            return False
        raise NotImplementedError(
            f"Method `trim` can only be applied on parameters handling "
            f'floating-point, integer, or boolean values, but the "value type" of '
            f"parameter `{self.name}` is `{self.TYPE.__name__}`."
        )
    return False


def _trim_float_0d(self, lower, upper) -> bool:
    if numpy.isnan(self.value):
        return False
    if (lower is None) or numpy.isnan(lower):
        lower = -numpy.inf
    if (upper is None) or numpy.isnan(upper):
        upper = numpy.inf
    if self < lower:
        old = self.value
        self.value = lower
        if (old + get_tolerance(old)) < (lower - get_tolerance(lower)):
            _warn_trim(self, oldvalue=old, newvalue=lower)
            return True
    elif self > upper:
        old = self.value
        self.value = upper
        if (old - get_tolerance(old)) > (upper + get_tolerance(upper)):
            _warn_trim(self, oldvalue=old, newvalue=upper)
            return True
    return False


def _trim_float_nd(self, lower, upper) -> bool:
    values = self.values
    shape = values.shape
    if lower is None:
        lower = -numpy.inf
    lower = numpy.full(shape, lower, dtype=config.NP_FLOAT)
    lower[numpy.where(numpy.isnan(lower))] = -numpy.inf
    if upper is None:
        upper = numpy.inf
    upper = numpy.full(shape, upper, dtype=config.NP_FLOAT)
    upper[numpy.where(numpy.isnan(upper))] = numpy.inf
    idxs = numpy.isnan(values)
    try:
        values[idxs] = lower[idxs]
        if numpy.any(values < lower) or numpy.any(values > upper):
            old = values.copy()
            trimmed = numpy.clip(values, lower, upper)
            values[:] = trimmed
            if numpy.any(
                (old + get_tolerance(old)) < (lower - get_tolerance(lower))
            ) or numpy.any((old - get_tolerance(old)) > (upper + get_tolerance(upper))):
                _warn_trim(self, oldvalue=old, newvalue=trimmed)
                return True
        return False
    finally:
        values[idxs] = numpy.nan


def _trim_int_0d(self, lower, upper) -> bool:
    if lower is None:
        lower = INT_NAN
    if (upper is None) or (upper == INT_NAN):
        upper = -INT_NAN
    if (self != INT_NAN) and ((self < lower) or (self > upper)):
        raise ValueError(
            f"The value `{self.value}` of parameter "
            f"{objecttools.elementphrase(self)} is not valid."
        )
    return False


def _trim_int_nd(self, lower, upper) -> bool:
    if lower is None:
        lower = INT_NAN
    lower = numpy.full(self.shape, lower, dtype=config.NP_INT)
    if upper is None:
        upper = -INT_NAN
    upper = numpy.full(self.shape, upper, dtype=config.NP_INT)
    upper[upper == INT_NAN] = -INT_NAN
    idxs = numpy.where(self.values == INT_NAN)
    try:
        self[idxs] = lower[idxs]
        if numpy.any(self.values < lower) or numpy.any(self.values > upper):
            raise ValueError(
                f"At least one value of parameter {objecttools.elementphrase(self)} "
                f"is not valid."
            )
        return False
    finally:
        self[idxs] = INT_NAN


def get_tolerance(values):
    """Return some "numerical accuracy" to be expected for the given floating-point
    value(s).

    The documentation on function |trim| explains also function |get_tolerance|.
    However, note the special case of infinite input values, for which function
    |get_tolerance| returns zero:

    >>> from hydpy.core.variabletools import get_tolerance
    >>> import numpy
    >>> get_tolerance(numpy.inf)
    0.0
    >>> from hydpy import round_
    >>> round_(get_tolerance(
    ...     numpy.array([1.0, numpy.inf, 2.0, -numpy.inf])), 16)
    0.000000000000001, 0.0, 0.000000000000002, 0.0
    """
    tolerance = numpy.abs(values * 1e-15)
    if hasattr(tolerance, "__setitem__"):
        tolerance[numpy.isinf(tolerance)] = 0.0
    elif numpy.isinf(tolerance):
        tolerance = 0.0
    return tolerance


def _warn_trim(self, oldvalue, newvalue):
    if hydpy.pub.options.warntrim:
        warnings.warn(
            f"For variable {objecttools.devicephrase(self)} at least one value "
            f"needed to be trimmed.  The old and the new value(s) are "
            f"`{objecttools.repr_numbers(oldvalue)}` and "
            f"`{objecttools.repr_numbers(newvalue)}`, respectively."
        )


def combine_arrays_to_lower_or_upper_bound(
    *arrays: Optional[NDArrayFloat], lower: bool
) -> Optional[NDArrayFloat]:
    """Helper function for parameter-specific trimming functions that collects all
    available lower or upper bound values.

    See function |sw1d_control.BottomLowWaterThreshold.trim| of class
    |sw1d_control.BottomLowWaterThreshold| for an example.
    """
    result: Optional[NDArrayFloat] = None
    for array in arrays:
        if (array is not None) and (array.ndim > 0):
            if result is None:
                result = array
            elif lower:
                result = numpy.maximum(result, array)
            else:
                result = numpy.minimum(result, array)
    return result


class FastAccess:
    """Used as a surrogate for typed Cython classes handling parameters or sequences
    when working in pure Python mode."""

    def _get_attribute(self, name, suffix, default=None):
        return getattr(self, f"_{name}_{suffix}", default)

    def _set_attribute(self, name, suffix, value):
        return setattr(self, f"_{name}_{suffix}", value)

    def __iter__(self):
        """Iterate over all sequence names."""
        for key in vars(self).keys():
            if not key.startswith("_"):
                yield key

    # ToDo: Replace this hack with a Mypy plugin?
    def __getattr__(self, item: str) -> Any:
        assert False

    del __getattr__

    def __setattr__(self, key: str, value: Any) -> None:
        assert False

    del __setattr__


class Variable:
    """Base class for |Parameter| and |Sequence_|.

    The subclasses are required to provide the class attributes `NDIM`
    and `TYPE`, defining the dimensionality and the type of the values
    to be handled by the subclass, respectively.  Class attribute `INIT`
    is optional and should provide a suitable default value.

    Class |Variable| implements methods for arithmetic calculations,
    comparisons and type conversions.  See the  following examples on
    how to do math with HydPys |Parameter| and |Sequence_| objects.

    We start with demonstrating the supported mathematical operations
    on 0-dimensional |Variable| objects handling |float| values:

    >>> import numpy
    >>> from hydpy.core.variabletools import FastAccess, Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     TYPE = float
    ...     initinfo = 0.0, False
    ...     _CLS_FASTACCESS_PYTHON = FastAccess
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

    If something goes wrong, all math operations return errors like the following:

    >>> var = Var(None)
    >>> var + 1.0
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: While trying to add \
variable `var` and `float` instance `1.0`, the following error occurred: \
For variable `var`, no value has been defined so far.

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
    >>> from hydpy import round_
    >>> round_(var.value, 1)
    1.7

    You can apply all the operations discussed above (except |float| and
    |int|) on |Variable| objects of arbitrary dimensionality:

    >>> from hydpy import print_matrix, print_vector
    >>> Var.NDIM = 1
    >>> Var.TYPE = float
    >>> var.shape = (2,)
    >>> var.values = 2.0
    >>> print_vector(var + var)
    4.0, 4.0
    >>> print_vector(var + 3.0)
    5.0, 5.0
    >>> print_vector([4.0, 0.0] + var)
    6.0, 2.0
    >>> var += 1
    >>> var
    var(3.0, 3.0)

    >>> var.values = 3.0
    >>> print_vector(var - [1.0, 0.0])
    2.0, 3.0
    >>> print_vector([7.0, 0.0] - var)
    4.0, -3.0
    >>> var -= [2.0, 0.0]
    >>> var
    var(1.0, 3.0)

    >>> var.values = 2.0
    >>> print_vector(var * [3.0, 1.0])
    6.0, 2.0
    >>> print_vector([4.0, 1.0] * var)
    8.0, 2.0
    >>> var *= [0.5, 1.0]
    >>> var
    var(1.0, 2.0)

    >>> var.values = 3.0
    >>> print_vector(var / [2.0, 1.0])
    1.5, 3.0
    >>> print_vector([7.5, 3.0] / var)
    2.5, 1.0
    >>> var /= [6.0, 1.]
    >>> var
    var(0.5, 3.0)

    >>> var.values = 3.0
    >>> print_vector(var // [2.0, 1.0])
    1.0, 3.0
    >>> print_vector([7.5, 3.0] // var)
    2.0, 1.0
    >>> var //= [0.9, 1.0]
    >>> var
    var(3.0, 3.0)

    >>> var.values = 5.0
    >>> print_vector(var % [2.0, 5.0])
    1.0, 0.0
    >>> print_vector([7.5, 5.0] % var)
    2.5, 0.0
    >>> var %= [3.0, 5.0]
    >>> var
    var(2.0, 0.0)

    >>> var.values = 2.0
    >>> print_vector(var**[3.0, 1.0])
    8.0, 2.0
    >>> print_vector([3.0, 1.0]**var)
    9.0, 1.0
    >>> var **= [4.0, 1.0]
    >>> var
    var(16.0, 2.0)

    >>> var.value = 5.0
    >>> print_matrix(divmod(var, [3.0, 5.0]))
    | 1.0, 1.0 |
    | 2.0, 0.0 |
    >>> print_matrix(divmod([13.0, 5.0], var))
    | 2.0, 1.0 |
    | 3.0, 0.0 |

    >>> var.values = -5.0
    >>> print_vector(+var)
    -5.0, -5.0
    >>> print_vector(-var)
    5.0, 5.0
    >>> print_vector(abs(var))
    5.0, 5.0
    >>> print_vector(~var)
    -0.2, -0.2
    >>> var.value = 2.5
    >>> import math
    >>> print_vector(math.floor(var))
    2, 2
    >>> print_vector(math.ceil(var))
    3, 3
    >>> var.values = 1.67
    >>> print_vector(round(var, 1))
    1.7, 1.7
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
    >>> round_(var[0])
    2.0
    >>> round_(var[-1])
    10.0
    >>> var[1:-1:2] = 2.0 * var[1:-1:2]
    >>> var
    var(2.0, 8.0, 6.0, 16.0, 10.0)
    >>> var[:] = "test"
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `var` \
with key `slice(None, None, None)`, the following error occurred: \
could not convert string to float: 'test'

    Comparisons with |Variable| objects containing multiple values return a single
    boolean value.  Two objects are equal if all of their value pairs are equal, and
    they are unequal if at least one of their value pairs is unequal:

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

    >>> var < "text"
    Traceback (most recent call last):
    ...
    TypeError: While trying to compare variable `var` of element `?` with \
object `text` of type `str`, the following error occurred: ufunc 'isnan' \
not supported for the input types, and the inputs could not be safely \
coerced to any supported types according to the casting rule ''safe''

    Note that, in contrast to the usual |numpy| array comparison, we ignore
    all single comparison results between two |numpy.nan| values:

    >>> from numpy import nan
    >>> var.shape = (3,)
    >>> var.values = 1.0, 2.0, nan
    >>> var < [2.0, 3.0, nan], var < [1.0, 2.0, nan], var < [2.0, nan, nan], \
var < [2.0, 3.0, 4.0]
    (True, False, False, False)
    >>> var <= [1.0, 3.0, nan], var <= [1.0, 1.0, nan], var <= [1.0, nan, nan], \
var <= [1.0, 3.0, 5.0]
    (True, False, False, False)
    >>> var == [1.0, 2.0, nan], var == [1.0, 1.0, nan], var == [1.0, nan, nan], \
var == [1.0, 2.0, 3.0]
    (True, False, False, False)
    >>> var != [1.0, 1.0, nan], var != [1.0, 2.0, nan], var != [1.0, nan, nan], \
var != [1.0, 2.0, 3.0]
    (True, False, True, True)
    >>> var >= [1.0, 1.0, nan], var >= [1.0, 3.0, nan], var <= [1.0, nan, nan], \
var <= [1.0, 3.0, 5.0]
    (True, False, False, False)
    >>> var > [0.0, 1.0, nan], var > [0.0, 2.0, nan], var < [0.0, nan, nan], \
var < [0.0, 1.0, 2.0]
    (True, False, False, False)

    Hence, when all entries of two compared objects are |numpy.nan|, we
    consider these objects equal:

    >>> var.values = nan
    >>> var < [nan, nan, nan], var <= [nan, nan, nan], var == [nan, nan, nan], \
var != [nan, nan, nan], var >= [nan, nan, nan], var > [nan, nan, nan]
    (False, True, True, False, True, False)
    >>> Var.NDIM = 0
    >>> var = Var(None)
    >>> var.shape = ()
    >>> var.value = nan
    >>> var < nan, var <= nan, var == nan, var != nan, var >= nan, var > nan
    (False, True, True, False, True, False)

    The |len| operator does not work for 0-dimensional variables:

    >>> Var.NDIM = 0
    >>> var = Var(None)
    >>> var.shape = ()
    >>> len(var)
    Traceback (most recent call last):
    ...
    TypeError: The `len` operator was applied on `var`, but this variable is \
0-dimensional and thus unsized.  Consider using the `numberofvalues` property instead.

    For higher-dimensional variables, `len` always returns the length of the first
    dimension:

    >>> Var.NDIM = 1
    >>> var = Var(None)
    >>> var.shape = (5,)
    >>> len(var)
    5
    >>> Var.NDIM = 3
    >>> var = Var(None)
    >>> var.shape = (2, 1, 4)
    >>> len(var)
    2

    |Variable| objects are hashable based on their |id| value to avoid avoiding
    confusion when adding different but equal objects into one |set| or |dict| object.
    The following examples show this behaviour by making deep copies of existing
    |Variable| objects:

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

    During initialisation, each |Variable| subclass tries to extract its
    unit from its docstring:

    >>> type("Var", (Variable,), {"__doc__": "Discharge [m³/s]."}).unit
    'm³/s'

    For missing or poorly written docstrings, we set `unit` to "?":

    >>> type("Var", (Variable,), {}).unit
    '?'
    >>> type("Var", (Variable,), {"__doc__": "Discharge ]m³/s[."}).unit
    '?'
    >>> type("Var", (Variable,), {"__doc__": "Discharge m³/s]."}).unit
    '?'
    """

    # Subclasses need to define...
    NDIM: int
    TYPE: type[Union[float, int, bool]]  # ToDo: is still `str` in some cases
    # ...and optionally...
    SPAN: tuple[Union[int, float, bool, None], Union[int, float, bool, None]] = (
        None,
        None,
    )
    INIT: Union[int, float, bool, None] = None

    _NOT_DEEPCOPYABLE_MEMBERS: Final[frozenset[str]] = frozenset(
        (
            "subvars",
            "subpars",
            "subseqs",
            "fastaccess",
            "fastaccess_old",
            "fastaccess_new",
        )
    )
    _CLS_FASTACCESS_PYTHON: ClassVar[type[FastAccess]]

    strict_valuehandling: bool = True

    __hydpy__subclasscounter__ = 1

    name: str
    """Name of the variable in lowercase letters."""
    unit: str
    """Unit of the variable."""
    fastaccess: FastAccess
    """Object for accessing the variable's data with little overhead."""
    subvars: SubVariables
    """The subgroup to which the variable belongs."""

    _refweights: Optional[Union[parametertools.Parameter, VectorFloat]] = None

    mask = masktools.DefaultMask(
        doc="The standard mask used by all variables (if not overwritten)."
    )

    @classmethod
    @contextlib.contextmanager
    def modify_refweights(
        cls, refweights: Optional[parametertools.Parameter]
    ) -> Generator[None, None, None]:
        """Eventually, set or modify the reference to a parameter defining the
        weighting coefficients required for aggregating values.

        The following example demonstrates that changes affect the relevant class only
        temporarily, but its objects initialised within the "with" block persistently:

        >>> from hydpy.core.variabletools import FastAccess, Variable
        >>> class Var1(Variable):
        ...     initinfo = 0.0, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> class Var2(Variable):
        ...     NDIM = 1
        ...     TYPE = float
        ...     initinfo = 0.0, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> var2 = Var2(None)
        >>> var2.shape = 3
        >>> with Var1.modify_refweights(var2):
        ...     Var1._refweights
        ...     var1 = Var1(None)
        ...     var1.refweights
        var2(0.0, 0.0, 0.0)
        var2(0.0, 0.0, 0.0)
        >>> Var1._refweights
        >>> var1.refweights
        var2(0.0, 0.0, 0.0)

        Passing |None| does not overwrite previously set references:

        >>> Var1._refweights = var2
        >>> with Var1.modify_refweights(None):
        ...     Var1._refweights
        ...     var1 = Var1(None)
        ...     var1.refweights
        var2(0.0, 0.0, 0.0)
        var2(0.0, 0.0, 0.0)
        >>> Var1._refweights
        var2(0.0, 0.0, 0.0)
        >>> var1.refweights
        var2(0.0, 0.0, 0.0)
        """
        if refweights is None:
            yield
        else:
            old = cls._refweights
            try:
                cls._refweights = refweights
                yield
            finally:
                cls._refweights = old

    def __init__(self, subvars: SubVariables) -> None:
        self.subvars = subvars
        self.fastaccess = self._CLS_FASTACCESS_PYTHON()
        self._valueready = False
        self.__shapeready = False
        self._refweights = type(self)._refweights

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.name = cls.__name__.lower()
        cls.unit = cls._get_unit()
        subclasscounter = Variable.__hydpy__subclasscounter__ + 1
        Variable.__hydpy__subclasscounter__ = subclasscounter
        cls.__hydpy__subclasscounter__ = subclasscounter

    @classmethod
    def _get_unit(cls) -> str:
        descr = objecttools.description(cls)
        idx1 = descr.find("[") + 1
        idx2 = descr.find("]")
        if 0 < idx1 < idx2:
            return descr[idx1:idx2]
        return "?"

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """To be called by the |SubVariables| object when preparing a
        new |Variable| object."""
        self.fastaccess = self.subvars.fastaccess
        self._finalise_connections()

    def _finalise_connections(self) -> None:
        """A hook method, called at the end of method
        `__hydpy__connect_variable2subgroup__` for initialising
        values and some related attributes."""

    @property
    @abc.abstractmethod
    def initinfo(self) -> tuple[Union[float, int, bool, pointerutils.Double], bool]:
        """To be overridden."""

    def __call__(self, *args) -> None:
        if len(args) == 1:
            args = args[0]
        self.values = args

    def _get_value(self):
        """The actual parameter or sequence value(s).

        First, we prepare a simple (not fully functional) |Variable| subclass:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     initinfo = 3.0, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess

        Without making use of default values (see below), trying to
        query the actual value of a freshly initialised |Variable|
        object results in the following error:

        >>> var = Var(None)
        >>> var.value
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: For variable `var`, \
no value has been defined so far.

        Property |Variable.value| tries to normalise assigned values and
        raises an error, if not possible:

        >>> var.value = 3
        >>> var.value
        3.0

        >>> var.value = ["2.0"]
        >>> var.value
        2.0

        >>> var.value = 1.0, 1.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the value(s) of variable `var`, the \
following error occurred: 2 values are assigned to the scalar variable `var`.
        >>> var.value
        2.0

        >>> var.value = "O"
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
        hydpy.core.exceptiontools.AttributeNotReady: Shape information for \
variable `var` can only be retrieved after it has been defined.

        >>> var.value = 2
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to set the \
value(s) of variable `var`, the following error occurred: Shape information \
for variable `var` can only be retrieved after it has been defined.

        >>> var.shape = (2, 3)
        >>> var.value
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: For variable `var`, \
no values have been defined so far.

        >>> from hydpy import print_matrix
        >>> var.value = 2
        >>> print_matrix(var.value)
        | 2, 2, 2 |
        | 2, 2, 2 |

        >>> var.value = 1, 2
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the value(s) of variable `var`, \
the following error occurred: While trying to convert the value(s) `(1, 2)` \
to a numpy ndarray with shape `(2, 3)` and type `int`, the following error \
occurred: could not broadcast input array from shape (2,) into shape (2,3)
        >>> print_matrix(var.value)
        | 2, 2, 2 |
        | 2, 2, 2 |

        >>> var.shape = (0, 0)
        >>> var.shape
        (0, 0)
        >>> var.value   # doctest: +ELLIPSIS
        array([], shape=(0, 0), dtype=...)
        """
        if (self.NDIM > 0) and not self.__shapeready:
            self._get_shape()  # raise the proper error
        value = self._prepare_getvalue(
            self._valueready or not self.strict_valuehandling,
            getattr(self.fastaccess, self.name, None),
        )
        if value is None:
            substring = "values have" if self.NDIM else "value has"
            raise exceptiontools.AttributeNotReady(
                f"For variable {objecttools.devicephrase(self)}, no {substring} been "
                f"defined so far."
            )
        return value

    def _set_value(self, value) -> None:
        try:
            value = self._prepare_setvalue(value)
            setattr(self.fastaccess, self.name, value)
            self._valueready = True
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the value(s) of variable "
                f"{objecttools.devicephrase(self)}"
            )

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
            value = getattr(value, "value", value)
            try:
                value = numpy.full(
                    self.shape, value, dtype=config.TYPES_PY2NP[self.TYPE]
                )
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to convert the value(s) `{value}` to a numpy "
                    f"ndarray with shape `{self.shape}` and type `{self.TYPE.__name__}`"
                )
        else:
            if isinstance(value, Sequence):
                if len(value) > 1:
                    raise ValueError(
                        f"{len(value)} values are assigned to the scalar variable "
                        f"{objecttools.devicephrase(self)}."
                    )
                value = value[0]
            try:
                value = self.TYPE(value)
            except BaseException:
                raise TypeError(
                    f"The given value `{value}` cannot be converted to type "
                    f"`{self.TYPE.__name__}`."
                ) from None
        return value

    value = property(fget=_get_value, fset=_set_value)

    @property
    def values(self):
        """Alias for |Variable.value|."""
        return self._get_value()

    @values.setter
    def values(self, values):
        self._set_value(values)

    def _get_shape(self) -> tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        Note that setting a new |Variable.shape| results in a loss of
        the actual |Variable.values| of the respective |Variable| object.

        First, we prepare a simple (not fully functional) |Variable| subclass:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     NDIM = 1
        ...     TYPE = float
        ...     initinfo = 3.0, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess

        Initially, the shape of a new |Variable| object is unknown:

        >>> var = Var(None)
        >>> var.shape
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Shape information for \
variable `var` can only be retrieved after it has been defined.

        For multidimensional objects, assigning shape information (as a
        |tuple| of |int| values) prepares the required array automatically.
        Due to the |Variable.initinfo| surrogate of our test class,
        the entries of this array are `3.0`:

        >>> from hydpy import print_vector
        >>> var.shape = (3,)
        >>> var.shape
        (3,)
        >>> print_vector(var.values)
        3.0, 3.0, 3.0

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
        hydpy.core.exceptiontools.AttributeNotReady: For variable `var`, no \
values have been defined so far.

        >>> print_vector(var.fastaccess.var)
        nan, nan, nan

        Property |Variable.shape| tries to normalise assigned values and
        raises errors like the following, if not possible:

        >>> var.shape = "x"
        Traceback (most recent call last):
        ...
        TypeError: While trying create a new numpy ndarray for \
variable `var`, the following error occurred: 'str' object cannot \
be interpreted as an integer
        >>> from hydpy import attrready
        >>> attrready(var, "shape")
        False
        >>> var.fastaccess.var

        >>> var.shape = (1,)
        >>> attrready(var, "shape")
        True

        >>> var.shape = (2, 3)
        Traceback (most recent call last):
        ...
        ValueError: Variable `var` is 1-dimensional, but the given \
shape indicates `2` dimensions.
        >>> attrready(var, "shape")
        False
        >>> var.fastaccess.var


        0-dimensional |Variable| objects inform the user about their shape
        but do not allow to change it for obvious reasons:

        >>> class Var(Variable):
        ...     NDIM = 0
        ...     TYPE = int
        ...     initinfo = 3, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess

        >>> var = Var(None)
        >>> var.shape
        ()
        >>> var.value
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: For variable `var`, \
no value has been defined so far.

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
        >>> attrready(var, "value")
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
            raise exceptiontools.AttributeNotReady(
                f"Shape information for variable {objecttools.devicephrase(self)} can "
                f"only be retrieved after it has been defined."
            )
        return ()

    def _set_shape(self, shape: Union[int, tuple[int, ...]]) -> None:
        self._valueready = False
        self.__shapeready = False
        initvalue, initflag = self.initinfo
        if self.NDIM:
            try:
                array = numpy.full(
                    shape, initvalue, dtype=config.TYPES_PY2NP[self.TYPE]
                )
            except BaseException:
                setattr(self.fastaccess, self.name, None)
                objecttools.augment_excmessage(
                    f"While trying create a new numpy ndarray for variable "
                    f"{objecttools.devicephrase(self)}"
                )
            if array.ndim != self.NDIM:
                setattr(self.fastaccess, self.name, None)
                raise ValueError(
                    f"Variable {objecttools.devicephrase(self)} is "
                    f"{self.NDIM}-dimensional, but the given "
                    f"shape indicates `{array.ndim}` dimensions."
                )
            setattr(self.fastaccess, self.name, array)
            self.__shapeready = True
        else:
            if shape:
                setattr(self.fastaccess, self.name, TYPE2MISSINGVALUE[self.TYPE])
                self._raise_wrongshape(shape)
            setattr(self.fastaccess, self.name, initvalue)
        if initflag:
            self._valueready = True

    shape = propertytools.Property(fget=_get_shape, fset=_set_shape)

    def _raise_wrongshape(self, shape):
        raise ValueError(
            f"The shape information of 0-dimensional variables "
            f"as {objecttools.devicephrase(self)} can only be `()`, "
            f"but `{shape}` is given."
        )

    @property
    def numberofvalues(self) -> int:
        """The total number of values handled by the variable according to the current
        shape.

        We create an incomplete |Variable| subclass for testing:

        >>> from hydpy.core.variabletools import FastAccess, Variable
        >>> class Var(Variable):
        ...     TYPE = float
        ...     initinfo = 0.0, False
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> var = Var(None)

        0-dimensional variables always handle precisely one value:

        >>> Var.NDIM = 0
        >>> var = Var(None)
        >>> var.shape = ()
        >>> var.numberofvalues
        1

        For higher-dimensional variables, |Variable.numberofvalues| is the cumulative
        product of the individual dimensons lengths:

        >>> Var.NDIM = 1
        >>> var = Var(None)
        >>> var.shape = (5,)
        >>> var.numberofvalues
        5
        >>> Var.NDIM = 3
        >>> var = Var(None)
        >>> var.shape = (2, 1, 4)
        >>> var.numberofvalues
        8

        As long as the shape of a higher-dimensional variable is undefined,
        |Variable.numberofvalues| is zero:

        >>> var = Var(None)
        >>> var.numberofvalues
        0
        """
        if self.NDIM == 0:
            return 1
        if (shape := exceptiontools.getattr_(self, "shape", None)) is None:
            return 0
        return int(numpy.cumprod(shape)[-1])

    def verify(self) -> None:
        """Raise a |RuntimeError| if at least one of the required values of a |Variable|
        object is |None| or |numpy.nan|.

        The descriptor |Variable.mask| defines which values are considered necessary.
        For |Variable| subclasses defining |numpy.nan| as their |Variable.INIT| value,
        method |Variable.verify| assumes that |numpy.nan| are not problematic.

        Examples on a 0-dimensional |Variable|:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     initinfo = 0.0, False
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> var = Var(None)
        >>> import numpy
        >>> var.shape = ()
        >>> var.value = 1.0
        >>> var.verify()
        >>> var.value = numpy.nan
        >>> var.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `var`, 1 required value has not been set yet: \
var(nan).

        >>> var.INIT = numpy.nan
        >>> var.verify()

        Examples on a 2-dimensional |Variable|:

        >>> Var.NDIM = 2
        >>> var = Var(None)
        >>> var.shape = (2, 3)
        >>> var.value = numpy.ones((2,3))
        >>> var.value[:, 1] = numpy.nan
        >>> var.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `var`, 2 required values have not been set yet: \
var([[1.0, nan, 1.0], [1.0, nan, 1.0]]).

        >>> Var.mask = var.mask
        >>> Var.mask[0, 1] = False
        >>> var.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `var`, 1 required value has not been set yet: \
var([[1.0, nan, 1.0], [1.0, nan, 1.0]]).

        >>> Var.mask[1, 1] = False
        >>> var.verify()
        """
        valueready = self._valueready
        try:
            self._valueready = True
            nmbnan: int = numpy.sum(numpy.isnan(numpy.array(self.value)[self.mask]))
        finally:
            self._valueready = valueready
        if nmbnan and ((self.INIT is None) or ~numpy.isnan(self.INIT)):
            text = "value has" if nmbnan == 1 else "values have"
            raise RuntimeError(
                f"For variable {objecttools.devicephrase(self)}, {nmbnan} required "
                f"{text} not been set yet: {objecttools.flatten_repr(self)}."
            )

    @property
    def valuevector(self) -> Vector:
        """The values of the actual |Variable| object, arranged in a 1-dimensional
        vector.

        For a 1-dimensional variable object, property |Variable.valuevector| returns
        the original values without any modification:

        >>> from hydpy.models.hland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> sclass(2)
        >>> states.sm.values = 1.0, 2.0, 3.0
        >>> from hydpy import print_vector
        >>> print_vector(states.sm.valuevector)
        1.0, 2.0, 3.0

        For all other variables, |Variable.valuevector| raises the following error by
        default:

        >>> states.uz.valuevector
        Traceback (most recent call last):
        ...
        NotImplementedError: Variable `uz` does not implement a method for converting \
its values to a 1-dimensional vector.

        If considered appropriate, model developers should override
        |Variable.valuevector| for individual multidimensional variables, to support
        methods like |Variable.average_values|, which rely on 1-dimensional data.  One
        example is the state sequence |hland_states.SP| of base model |hland|, which
        handles values for individual zones (second axis) and snow classes (first axis).
        Here we decided to let |hland_sequences.State2DSequence.valuevector| return the
        sums of all snow classes for each zone so that the content of the returned
        vector agrees with the contents of most 1-dimensional sequences of |hland|:

        >>> states.sp = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        >>> print_vector(states.sp.valuevector)
        2.5, 3.5, 4.5
        """
        if self.NDIM == 1:
            return self.value
        raise NotImplementedError(
            f"Variable {objecttools.devicephrase(self)} does not implement a method "
            f"for converting its values to a 1-dimensional vector."
        )

    @property
    def refweights(self) -> Union[parametertools.Parameter, VectorFloat]:
        """Reference to a |Parameter| object or a simple vector that defines weighting
        coefficients (e.g. fractional areas) for applying function
        |Variable.average_values|.

        Must be overwritten by subclasses when required."""
        if (refweights := self._refweights) is not None:
            return refweights
        raise AttributeError(
            f"Variable {objecttools.devicephrase(self)} does not define any weighting "
            f"coefficients."
        )

    def average_values(self, *args, **kwargs) -> float:
        """Average the actual values of the |Variable| object.

        For 0-dimensional |Variable| objects, the result of method
        |Variable.average_values| equals |Variable.value|.  The following example shows
        this for the poorly defined class `SoilMoisture`:

        >>> from hydpy.core.variabletools import Variable
        >>> class SoilMoisture(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     refweigths = None
        ...     availablemasks = None
        ...     initinfo = None
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        ...     value = 200.0
        >>> sm = SoilMoisture(None)
        >>> sm.average_values()
        200.0

        When the dimensionality of this class is increased to one, applying method
        |Variable.average_values| results in the following error:

        >>> SoilMoisture.NDIM = 1
        >>> import numpy
        >>> SoilMoisture.shape = (3,)
        >>> SoilMoisture.value = numpy.array([200.0, 400.0, 500.0])
        >>> sm.average_values()
        Traceback (most recent call last):
        ...
        AttributeError: While trying to calculate the mean value of variable \
`soilmoisture`, the following error occurred: Variable `soilmoisture` does not define \
any weighting coefficients.

        So model developers have to define another (in this case 1-dimensional)
        |Variable| subclass (usually a |Parameter| subclass) and make the relevant
        object available via property |Variable.refweights|:

        >>> class Area(Variable):
        ...     NDIM = 1
        ...     shape = (3,)
        ...     value = numpy.array([1.0, 1.0, 2.0])
        ...     initinfo = None
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> area = Area(None)
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> sm.average_values()
        400.0

        In the examples above, all single entries of `values` are relevant, which is
        the default case.  However, subclasses of |Variable| can define an alternative
        mask, allowing to make some entries irrelevant. Assume, for example, that our
        `SoilMoisture` object contains three single values, each one associated with a
        specific hydrological response unit (hru).  To indicate that soil moisture is
        undefined for the third unit (maybe because it is a water area), we set the
        third entry of the verification mask to |False|:

        >>> from hydpy.core.masktools import DefaultMask
        >>> class Soil(DefaultMask):
        ...     @classmethod
        ...     def new(cls, variable, **kwargs):
        ...         return cls.array2mask([True, True, False])
        >>> SoilMoisture.mask = Soil()
        >>> sm.average_values()
        300.0

        Alternatively, method |Variable.average_values| accepts additional masking
        information as positional or keyword arguments.  Therefore, the corresponding
        model must implement some alternative masks, which are provided by property
        |Variable.availablemasks|.  We mock this property with a new |Masks| object,
        handling one mask for flat soils (only the first hru), one mask for deep soils
        (only the second hru), and one mask for water areas (only the third hru):

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
        >>> SoilMoisture.availablemasks = Masks()

        One can pass either the mask classes themselves or their names:

        >>> sm.average_values(sm.availablemasks.flatsoil)
        200.0
        >>> sm.average_values("deepsoil")
        400.0

        Both variants can be combined:

        >>> sm.average_values(sm.availablemasks.deepsoil, "flatsoil")
        300.0

        The following error happens if the general mask of the variable
        does not contain the given masks:

        >>> sm.average_values("flatsoil", "water")
        Traceback (most recent call last):
        ...
        ValueError: While trying to calculate the mean value of variable \
`soilmoisture`, the following error occurred: Based on the arguments \
`('flatsoil', 'water')` and `{}` the mask `CustomMask([ True, False,  True])` \
has been determined, which is not a submask of `Soil([ True,  True, False])`.

        Applying masks with custom options is also supported.  One can change the
        behaviour of the following mask via the argument `complete`:

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
        >>> SoilMoisture.availablemasks = Masks()

        Again, one can apply the mask class directly (but note that one has to pass the
        relevant variable as the first argument):

        >>> sm.average_values(   # doctest: +ELLIPSIS
        ...     sm.availablemasks.allornothing(sm, complete=True))
        Traceback (most recent call last):
        ...
        ValueError: While trying to...

        Alternatively, one can pass the mask name as a keyword and pack the mask's
        options into a |dict| object:

        >>> sm.average_values(allornothing={"complete": False})
        nan

        You can combine all variants explained above:

        >>> sm.average_values("deepsoil", flatsoil={}, allornothing={"complete": False})
        300.0
        """
        try:
            if self.NDIM == 0:
                return self.value
            mask = self.get_submask(*args, **kwargs)
            if numpy.any(mask):
                weights = self.refweights[mask]
                values = self.valuevector[mask]
                return float(numpy.sum(weights * values) / numpy.sum(weights))
            return numpy.nan
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to calculate the mean value of variable "
                f"{objecttools.devicephrase(self)}"
            )

    @property
    def availablemasks(self) -> masktools.Masks:
        """For |ModelSequence| objects, a |Masks| object provided by the corresponding
        |Model| object; for |NodeSequence| object, a suitable |DefaultMask|.

        >>> from hydpy.core.testtools import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        >>> hp.elements["land_dill_assl"].model.parameters.control.fc.availablemasks
        complete of module hydpy.models.hland.hland_masks
        land of module hydpy.models.hland.hland_masks
        upperzone of module hydpy.models.hland.hland_masks
        snow of module hydpy.models.hland.hland_masks
        soil of module hydpy.models.hland.hland_masks
        field of module hydpy.models.hland.hland_masks
        forest of module hydpy.models.hland.hland_masks
        ilake of module hydpy.models.hland.hland_masks
        glacier of module hydpy.models.hland.hland_masks
        sealed of module hydpy.models.hland.hland_masks
        noglacier of module hydpy.models.hland.hland_masks

        >>> hp.nodes.dill_assl.sequences.sim.availablemasks
        defaultmask of module hydpy.core.masktools
        """
        model = getattr(self.subvars.vars, "model", None)
        if model:
            return model.masks
        return self.subvars.vars.masks

    def get_submask(
        self, *args, **kwargs
    ) -> Union[masktools.CustomMask, masktools.DefaultMask]:
        """Get a sub-mask of the mask handled by the actual |Variable| object based on
        the given arguments.

        See the documentation on method |Variable.average_values| for further
        information.
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
                    f"Based on the arguments `{args}` and `{kwargs}` the mask "
                    f"`{repr(mask)}` has been determined, which is not a submask of "
                    f"`{repr(self.mask)}`."
                )
            return mask
        return self.mask

    def _prepare_mask(self, mask, masks, **kwargs):
        mask = masks[mask]
        if inspect.isclass(mask):
            return mask(self, **kwargs)
        return mask

    def __deepcopy__(self, memo):
        new = type(self)(None)
        for key, value in vars(self).items():
            if key not in self._NOT_DEEPCOPYABLE_MEMBERS:
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
                f"While trying to access the value(s) of variable "
                f"{objecttools.devicephrase(self)} with key `{key}`"
            )

    def __setitem__(self, key, value):
        try:
            if self.NDIM:
                self.value[key] = value
            else:
                self._check_key(key)
                self.value = value
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the value(s) of variable "
                f"{objecttools.devicephrase(self)} with key `{key}`"
            )

    @staticmethod
    def _check_key(key):
        if key not in (0, slice(None, None, None)):
            raise IndexError(
                "The only allowed keys for 0-dimensional variables are `0` and `:`."
            )

    def __len__(self) -> int:
        if self.NDIM == 0:
            raise TypeError(
                f"The `len` operator was applied on {objecttools.devicephrase(self)}, "
                f"but this variable is 0-dimensional and thus unsized.  Consider "
                f"using the `numberofvalues` property instead."
            )
        return self._get_shape()[0]

    def _do_math(self, other, methodname, description):
        try:
            if hasattr(type(other), "_get_value"):
                value = other.value
            else:
                value = other
            result = getattr(self.value, methodname)(value)
            if (result is NotImplemented) and (not self.NDIM) and (self.TYPE is int):
                result = getattr(float(self.value), methodname)(value)
            return result
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to {description} variable "
                f"{objecttools.devicephrase(self)} and `{type(other).__name__}` "
                f"instance `{objecttools.repr_(other)}`"
            )

    def __add__(self, other):
        return self._do_math(other, "__add__", "add")

    def __radd__(self, other):
        return self._do_math(other, "__radd__", "add")

    def __iadd__(self, other):
        self.value = self._do_math(other, "__add__", "add")
        return self

    def __sub__(self, other):
        return self._do_math(other, "__sub__", "subtract")

    def __rsub__(self, other):
        return self._do_math(other, "__rsub__", "subtract")

    def __isub__(self, other):
        self.value = self._do_math(other, "__sub__", "subtract")
        return self

    def __mul__(self, other):
        return self._do_math(other, "__mul__", "multiply")

    def __rmul__(self, other):
        return self._do_math(other, "__rmul__", "multiply")

    def __imul__(self, other):
        self.value = self._do_math(other, "__mul__", "multiply")
        return self

    def __truediv__(self, other):
        return self._do_math(other, "__truediv__", "divide")

    def __rtruediv__(self, other):
        return self._do_math(other, "__rtruediv__", "divide")

    def __itruediv__(self, other):
        self.value = self._do_math(other, "__truediv__", "divide")
        return self

    def __floordiv__(self, other):
        return self._do_math(other, "__floordiv__", "floor divide")

    def __rfloordiv__(self, other):
        return self._do_math(other, "__rfloordiv__", "floor divide")

    def __ifloordiv__(self, other):
        self.value = self._do_math(other, "__floordiv__", "floor divide")
        return self

    def __mod__(self, other):
        return self._do_math(other, "__mod__", "mod divide")

    def __rmod__(self, other):
        return self._do_math(other, "__rmod__", "mod divide")

    def __imod__(self, other):
        self.value = self._do_math(other, "__mod__", "mod divide")
        return self

    def __divmod__(self, other):
        return self.__floordiv__(other), self.__mod__(other)

    def __rdivmod__(self, other):
        return self.__rfloordiv__(other), self.__rmod__(other)

    def __pow__(self, other):
        return self._do_math(other, "__pow__", "exponentiate")

    def __rpow__(self, other):
        return self._do_math(other, "__rpow__", "exponentiate (reflectively)")

    def __ipow__(self, other):
        self.value = self._do_math(other, "__pow__", "exponentiate")
        return self

    def __pos__(self):
        return +self.value

    def __neg__(self):
        return -self.value

    def __abs__(self):
        return abs(self.value)

    def __invert__(self):
        return 1.0 / self.value

    def __floor__(self):
        result = self.value // 1.0
        try:
            return int(result)
        except TypeError:
            return numpy.array(result, dtype=config.NP_INT)

    def __ceil__(self):
        result = numpy.ceil(self.value)
        try:
            return int(result)
        except TypeError:
            return numpy.array(result, dtype=config.NP_INT)

    def _compare(
        self,
        other: object,
        comparefunc: Callable,
        callingfunc: Literal["lt", "le", "eq", "ne", "ge", "gt"],
    ) -> bool:
        try:
            vs1 = self._get_value()
            if isinstance(other, Variable):
                vs2 = other._get_value()  # pylint: disable=protected-access
            else:
                vs2 = numpy.asarray(other)
            if self.NDIM == 0:
                if numpy.isnan(vs1) and bool(numpy.isnan(vs2)):
                    if callingfunc in ("le", "eq", "ge"):
                        return True
                    return False
                return comparefunc(vs1, vs2)
            try:
                idxs = ~(numpy.isnan(vs1) * numpy.isnan(vs2))
            except BaseException as exc:
                if callingfunc == "eq":
                    return False
                if callingfunc == "ne":
                    return True
                raise exc
            if numpy.sum(idxs) == 0:
                if callingfunc in ("le", "eq", "ge"):
                    return True
                return False
            return comparefunc(vs1, vs2)[idxs]
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to compare variable {objecttools.elementphrase(self)} "
                f"with object `{other}` of type `{type(other).__name__}`"
            )

    def __lt__(self, other: Union[Variable, float]) -> bool:
        return bool(
            numpy.all(
                self._compare(
                    other=other,
                    comparefunc=lambda vs1, vs2: vs1 < vs2,
                    callingfunc="lt",
                )
            )
        )

    def __le__(self, other: Union[Variable, float]) -> bool:
        return bool(
            numpy.all(
                self._compare(
                    other=other,
                    comparefunc=lambda vs1, vs2: vs1 <= vs2,
                    callingfunc="le",
                )
            )
        )

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        return bool(
            numpy.all(
                self._compare(
                    other=other,
                    comparefunc=lambda vs1, vs2: vs1 == vs2,
                    callingfunc="eq",
                )
            )
        )

    def __ne__(self, other: object) -> bool:
        return bool(
            numpy.any(
                self._compare(
                    other=other,
                    comparefunc=lambda vs1, vs2: vs1 != vs2,
                    callingfunc="ne",
                )
            )
        )

    def __ge__(self, other: Union[Variable, float]) -> bool:
        return bool(
            numpy.all(
                self._compare(
                    other=other,
                    comparefunc=lambda vs1, vs2: vs1 >= vs2,
                    callingfunc="ge",
                )
            )
        )

    def __gt__(self, other: Union[Variable, float]) -> bool:
        return bool(
            numpy.all(
                self._compare(
                    other=other,
                    comparefunc=lambda vs1, vs2: vs1 > vs2,
                    callingfunc="gt",
                )
            )
        )

    def _typeconversion(self, type_):
        if self.NDIM:
            raise TypeError(
                f"The variable {objecttools.devicephrase(self)} is "
                f"{self.NDIM}-dimensional and thus cannot be converted "
                f"to a scalar {type_.__name__} value."
            )
        return type_(self.value)

    def __bool__(self) -> bool:
        if self.NDIM == 0:
            return bool(self.value)
        return self.numberofvalues > 0

    def __float__(self) -> float:
        return self._typeconversion(float)

    def __int__(self) -> int:
        return self._typeconversion(int)

    def __round__(self, ndigits: int = 0):
        return numpy.round(self.value, ndigits)

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        brackets = (self.NDIM == 2) and (self.shape[0] != 1)
        return to_repr(self, self.value, brackets)


class MixinFixedShape:
    """Mixin class for defining variables with a fixed shape."""

    SHAPE: Union[tuple[int, ...]]
    name: str

    def _finalise_connections(self) -> None:
        super()._finalise_connections()  # type: ignore[misc]
        self.shape = self.SHAPE

    def _get_shape(self) -> tuple[int, ...]:
        """Variables that mix in |MixinFixedShape| are generally initialised with a
        fixed shape.

        We take parameter |kinw_control.BV| of base model |kinw| and sequence
        |exch_factors.WaterLevels| of base model |exch| as examples:

        >>> from hydpy import prepare_model
        >>> prepare_model("kinw").parameters.control.bv.shape
        (2,)
        >>> waterlevels = prepare_model("exch").sequences.factors.waterlevels
        >>> waterlevels.shape
        (2,)

        If we try to set a new shape, |MixinFixedShape| responds with the following
        exceptions:

        >>> waterlevels.shape = 2
        Traceback (most recent call last):
        ...
        AttributeError: The shape of variable `waterlevels` cannot be changed but \
this was attempted for element `?`.

        See the documentation on property |Variable.shape| of class |Variable| for
        further information.
        """
        return super()._get_shape()  # type: ignore[misc]

    def _set_shape(self, shape: Union[int, tuple[int, ...]]) -> None:
        oldshape = exceptiontools.getattr_(self, "shape", None)
        if oldshape is None:
            super()._set_shape(shape)  # type: ignore[misc]
        elif shape != oldshape:
            raise AttributeError(
                f"The shape of variable `{self.name}` cannot be changed but this was "
                f"attempted for element `{objecttools.devicename(self)}`."
            )

    shape = propertytools.Property(fget=_get_shape, fset=_set_shape)


@overload
def sort_variables(
    values: Iterable[type[TypeVariable_co]],
) -> tuple[type[TypeVariable_co], ...]: ...


@overload
def sort_variables(
    values: Iterable[tuple[type[TypeVariable_co], T]],
) -> tuple[tuple[type[TypeVariable_co], T], ...]: ...


def sort_variables(
    values: Iterable[Union[type[TypeVariable], tuple[type[TypeVariable], T]]],
) -> tuple[Union[type[TypeVariable], tuple[type[TypeVariable], T]], ...]:
    """Sort the given |Variable| subclasses by their initialisation order.

    When defined in one module, the initialisation order corresponds to the order
    within the file:

    >>> from hydpy import classname, sort_variables
    >>> from hydpy.models.hland.hland_control import Area, NmbZones, ZoneType
    >>> from hydpy import classname
    >>> for var in sort_variables([NmbZones, ZoneType, Area]):
    ...     print(classname(var))
    Area
    NmbZones
    ZoneType

    When defined in multiple modules, alphabetical sorting of the modules' filepaths
    takes priority:

    >>> from hydpy.models.evap.evap_control import NmbHRU, ExcessReduction
    >>> for var in sort_variables([NmbZones, ZoneType, Area, NmbHRU, ExcessReduction]):
    ...     print(classname(var))
    NmbHRU
    ExcessReduction
    Area
    NmbZones
    ZoneType

    Function |sort_variables| also supports sorting tuples.  Each first entry must be
    a |Variable| subclass:

    >>> for var, i in sort_variables([(NmbZones, 1), (ZoneType, 2), (Area, 3)]):
    ...     print(classname(var), i)
    Area 3
    NmbZones 1
    ZoneType 2

    >>> for var, i in sort_variables([(NmbZones, 1), (ZoneType, 2), (Area, 3)]):
    ...     print(classname(var), i)
    Area 3
    NmbZones 1
    ZoneType 2

    |sort_variables| does not remove duplicates:

    >>> for var, i in sort_variables([(Area, 3), (ZoneType, 2), (Area, 1), (Area, 3)]):
    ...     print(classname(var), i)
    Area 1
    Area 3
    Area 3
    ZoneType 2
    """
    modulepath_position_value = []
    for value in values:
        variable = value[0] if isinstance(value, tuple) else value
        modulepath = variable.__module__
        position = variable.__hydpy__subclasscounter__
        modulepath_position_value.append((modulepath, position, value))
    return tuple(value for _, _, value in sorted(modulepath_position_value))


class SubVariables(Generic[TypeGroup_co, TypeVariable_co, TypeFastAccess_co]):
    """Base class for |SubParameters| and |SubSequences|.

    Each subclass of class |SubVariables| is thought for handling a certain group of
    |Parameter| or |Sequence_| objects.  One specific example is subclass
    |sequencetools.InputSequences|, collecting all |InputSequence| objects of a
    specific hydrological model.

    For the following examples, we first prepare a (not fully functional) |Variable|
    subclass:

    >>> from hydpy.core.variabletools import FastAccess, SubVariables, Variable
    >>> class TestVar(Variable):
    ...     NDIM = 0
    ...     TYPE = float
    ...     initinfo = 0.0, False
    ...     _CLS_FASTACCESS_PYTHON = FastAccess

    Out test |SubVariables| subclass is thought to handle only this
    single |Variable| subclass, indicated by putting it into the
    |tuple| class attribute `CLASSES`:

    >>> class SubVars(SubVariables):
    ...     CLASSES = (TestVar,)
    ...     name = "subvars"
    ...     _CLS_FASTACCESS_PYTHON = FastAccess


    After initialisation, |SubVariables| objects reference their master object (either
    a |Parameters| or a |Sequences| object), passed to their constructor. However, in
    our simple test example, we just passed a string instead:

    >>> subvars = SubVars("test")
    >>> subvars.vars
    'test'

    The string representation lists all available variables and uses question marks to
    indicate cases where their values are not readily available:

    >>> subvars
    testvar(?)

    Class |SubVariables| provides attribute access to the handled |Variable| objects
    and protects |Variable| objects from accidental overwriting:

    >>> subvars.testvar = 3.0
    >>> subvars.testvar
    testvar(3.0)

    Trying to query not available |Variable| objects (or other attributes) results in
    the following error message:

    >>> subvars.wrong
    Traceback (most recent call last):
    ...
    AttributeError: Collection object `subvars` does neither handle a \
variable nor another attribute named wrong.

    Class |SubVariables| protects only the handled |Variable| objects from overwriting
    with unplausible data:

    >>> subvars.vars = "wrong"
    >>> subvars.vars
    'wrong'

    >>> subvars.testvar = "wrong"
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `testvar`, the following \
error occurred: 5 values are assigned to the scalar variable `testvar`.

    Alternatively, you can item-access a variable:

    >>> subvars["testvar"]
    testvar(3.0)

    >>> subvars["wrong"]
    Traceback (most recent call last):
    ...
    AttributeError: Collection object `subvars` does not handle a variable named \
`wrong`.

    Class |SubVariables| supporte iteration and the application of the |len| operator:

    >>> for variable in subvars:
    ...     print(variable.name)
    testvar
    >>> len(subvars)
    1
    """

    CLASSES: tuple[type[TypeVariable_co], ...]
    vars: TypeGroup_co
    _name2variable: dict[str, TypeVariable_co] = {}
    fastaccess: TypeFastAccess_co
    _cls_fastaccess: Optional[type[TypeFastAccess_co]] = None
    _CLS_FASTACCESS_PYTHON: ClassVar[type[TypeFastAccess_co]]  # type: ignore[misc]

    def __init__(
        self,
        master: TypeGroup_co,
        cls_fastaccess: Optional[type[TypeFastAccess_co]] = None,
    ):
        self.vars = master
        if cls_fastaccess:
            self._cls_fastaccess = cls_fastaccess
        self._init_fastaccess()
        self._name2variable = {}
        for cls in self.CLASSES:
            variable = cls(self)
            self._name2variable[variable.name] = variable
            variable.__hydpy__connect_variable2subgroup__()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """To be overridden."""

    @functools.cached_property
    def names(self) -> frozenset:
        """The names of all handled variables."""
        return frozenset(self._name2variable)

    def _init_fastaccess(self) -> None:
        """Create a `fastaccess` attribute and build the required connections to the
        related cythonized model eventually."""
        if (self._cls_fastaccess is None) or (self._cymodel is None):
            self.fastaccess = self._CLS_FASTACCESS_PYTHON()
        else:
            self.fastaccess = self._cls_fastaccess()

    def __getitem__(self, item) -> TypeVariable_co:
        try:
            return self._name2variable[item]
        except KeyError:
            raise AttributeError(
                f"Collection object {objecttools.devicephrase(self)} does not handle "
                f"a variable named `{item}`."
            ) from None

    def __getattr__(self, name) -> TypeVariable_co:
        try:
            return self._name2variable[name]
        except KeyError:
            raise AttributeError(
                f"Collection object {objecttools.devicephrase(self)} does neither "
                f"handle a variable nor another attribute named {name}."
            ) from None

    def __setattr__(self, name, value):
        variable = self._name2variable.get(name)
        if variable is None:
            super().__setattr__(name, value)
        else:
            variable._set_value(value)

    def __iter__(self) -> Iterator[TypeVariable_co]:
        yield from self._name2variable.values()

    def __len__(self) -> int:
        return len(self.CLASSES)

    def __bool__(self) -> bool:
        return bool(self.CLASSES)

    def __repr__(self) -> str:
        lines = []
        for variable in self:
            try:
                lines.append(repr(variable))
            except BaseException:
                lines.append(f"{variable.name}(?)")
        return "\n".join(lines)

    def __dir__(self) -> list[str]:
        """
        >>> from hydpy.core.variabletools import SubVariables, Variable
        >>> class TestVar(Variable):
        ...     NDIM = 0
        ...     TYPE = float
        ...     initinfo = 0.0, False
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> class TestSubVars(SubVariables):
        ...     CLASSES = (TestVar,)
        ...     name = None
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        >>> testsubvars = TestSubVars(None)
        >>> sorted(set(dir(testsubvars)) - set(object.__dir__(testsubvars)))
        ['testvar']
        """
        return cast(list[str], super().__dir__()) + list(self._name2variable.keys())


def to_repr(self: Variable, values, brackets: bool = False) -> str:
    """Return a valid string representation for the given |Variable| object.

    Function |to_repr| is thought for internal purposes only, more specifically for
    defining string representations of subclasses of class |Variable| like the
    following:

    >>> from hydpy.core.variabletools import to_repr, Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     TYPE = int
    ...     initinfo = 1.0, False
    ...     _CLS_FASTACCESS_PYTHON = FastAccess
    >>> var = Var(None)
    >>> var.value = 2
    >>> var
    var(2)

    The following examples demonstrate all covered cases.  Note that option `brackets`
    allows choosing between a "vararg" and an "iterable" string representation for
    multidimensional variables:

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
    var(0, 1, 2,
        3, 4, 5)
    >>> print(to_repr(var, [range(3), range(3, 6)], True))
    var([[0, 1, 2],
         [3, 4, 5]])
    >>> print(to_repr(var, [range(30), range(30, 60)], True))
    var([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
          19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
         [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
          46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]])
    >>> print(to_repr(var, [range(30), range(30, 60)]))
    var(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
        30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,
        47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59)
    """
    prefix = f"{self.name}("
    if isinstance(values, str):
        return f"{self.name}({values})"
    if self.NDIM == 0:
        return f"{self.name}({objecttools.repr_(values)})"
    if self.NDIM == 1:
        if brackets:
            return objecttools.assignrepr_list(values, prefix, 72) + ")"
        return objecttools.assignrepr_values(values, prefix, 72) + ")"
    if brackets:
        return objecttools.assignrepr_list2(values, prefix, 72) + ")"
    return objecttools.assignrepr_values2(values, prefix, 72) + ")"
