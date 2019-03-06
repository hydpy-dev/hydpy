# -*- coding: utf-8 -*-
"""This module implements general features for defining and working with
parameters and sequences.

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


ValuesType = Union[
    float, Iterable[float], Iterable[Iterable[float]],
    int, Iterable[int], Iterable[Iterable[int]],
    bool, Iterable[bool], Iterable[Iterable[bool]]]


INT_NAN: int = -999999
"""Surrogate for `nan`, which is available for floating point values
but not for integer values."""


def trim(self: abctools.VariableABC, lower: Optional[ValuesType] = None,
         upper: Optional[ValuesType] = None) -> None:
    """Trim the value(s) of a |Variable| instance.

    One can pass the lower and/or the upper boundary as a function
    argument.  Otherwise, boundary values are taken from the class
    attribute `SPAN` of the given |Variable| instance, if available.

    Note that method |trim| works differently on |Variable| instances
    handling values of different types.  For floating point values,
    an actual trimming is performed.  Additionally, a warning message is
    raised if the trimming results in a change in value exceeding the
    threshold value defined by function "tolerance" ToDo.  (This warning
    message can be suppressed by setting the related option flag to False.)
    For integer values, instead of a warning an exception is raised.

    >>> from hydpy import pub
    >>> pub.options.warntrim = True

    >>> from hydpy.core.parametertools import Parameter
    >>> class Par(Parameter):
    ...     NDIM = 0
    ...     TYPE = float
    ...     TIME = None
    ...     SPAN = 1.0, 3.0
    >>> par = Par()

    >>> from hydpy.core.variabletools import trim
    >>> par(2.0)
    >>> trim(par)

    >>> par(0.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `0.0` and `1.0`, respectively.
    >>> par
    par(1.0)

    >>> par(4.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `4.0` and `3.0`, respectively.
    >>> par
    par(3.0)

    >>> par.value = 1.0 - 1e-15
    >>> par == 1.0
    False
    >>> trim(par)
    >>> par == 1.0
    True

    >>> par.value = 3.0 + 1e-15
    >>> par == 3.0
    False
    >>> trim(par)
    >>> par == 3.0
    True

    >>> trim(par, lower=4.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `3.0` and `4.0`, respectively.

    >>> trim(par, upper=3.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `4.0` and `3.0`, respectively.

    >>> import numpy
    >>> par.value = 0.0
    >>> trim(par, lower=numpy.nan)
    >>> par.value = 5.0
    >>> trim(par, upper=numpy.nan)

    >>> with pub.options.trimvariables(False):
    ...     par(5.0)
    >>> par
    par(5.0)

    >>> with pub.options.warntrim(False):
    ...     par(5.0)
    >>> par
    par(3.0)

    >>> del Par.SPAN
    >>> par(5.0)
    >>> par
    par(5.0)

    >>> Par.SPAN = (None, None)
    >>> trim(par)
    >>> par
    par(5.0)


    >>> Par.SPAN = 1.0, 3.0
    >>> Par.NDIM = 2
    >>> par.shape = 1, 3
    >>> par(2.0)

    >>> par(0.0, 1.0, 2.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 0.  1.  2.]]` and `[[ 1.  1.  2.]]`, \
respectively.
    >>> par
    par([[1.0, 1.0, 2.0]])

    >>> par(2.0, 3.0, 4.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 2.  3.  4.]]` and `[[ 2.  3.  3.]]`, \
respectively.
    >>> par
    par([[2.0, 3.0, 3.0]])

    >>> par.value = 1.0-1e-15, 2.0, 3.0+1e-15
    >>> par.value == (1.0, 2.0, 3.0)
    array([[False,  True, False]], dtype=bool)
    >>> trim(par)
    >>> par.value == (1.0, 2.0, 3.0)
    array([[ True,  True,  True]], dtype=bool)

    >>> par.value = 0.0, 2.0, 4.0
    >>> trim(par, lower=numpy.nan, upper=numpy.nan)
    >>> par
    par([[0.0, 2.0, 4.0]])

    >>> trim(par, lower=[numpy.nan, 3.0, 3.0])
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 0.  2.  4.]]` and `[[ 0.  3.  3.]]`, \
respectively.

    >>> par.value = 0.0, 2.0, 4.0
    >>> trim(par, upper=[numpy.nan, 1.0, numpy.nan])
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `[[ 0.  2.  4.]]` and `[[ 1.  1.  4.]]`, \
respectively.

    >>> Par.TYPE = int
    >>> Par.NDIM = 0
    >>> Par.SPAN = 1, 3

    >>> par(2)
    >>> par
    par(2)

    >>> par(0)
    Traceback (most recent call last):
    ...
    ValueError: The value `0` of parameter `par` of element `?` is not valid.
    >>> par
    par(0)
    >>> par(4)
    Traceback (most recent call last):
    ...
    ValueError: The value `4` of parameter `par` of element `?` is not valid.

    >>> from hydpy import INT_NAN
    >>> par.value = 0
    >>> trim(par, lower=0)
    >>> trim(par, lower=INT_NAN)

    >>> par.value = 4
    >>> trim(par, upper=4)
    >>> trim(par, upper=INT_NAN)

    >>> Par.SPAN = 1, None
    >>> par(0)
    Traceback (most recent call last):
    ...
    ValueError: The value `0` of parameter `par` of element `?` is not valid.
    >>> par(4)

    >>> Par.SPAN = None, 3
    >>> par(0)
    >>> par(4)
    Traceback (most recent call last):
    ...
    ValueError: The value `4` of parameter `par` of element `?` is not valid.

    >>> del Par.SPAN
    >>> par(0)
    >>> par(4)

    >>> Par.SPAN = 1, 3
    >>> Par.NDIM = 2
    >>> par.shape = (1, 3)
    >>> par(2)

    >>> par(0, 1, 2)
    Traceback (most recent call last):
    ...
    ValueError: At least one value of parameter `par` of element `?` \
is not valid.
    >>> par
    par([[0, 1, 2]])
    >>> par(2, 3, 4)
    Traceback (most recent call last):
     ...
    ValueError: At least one value of parameter `par` of element `?` \
is not valid.
    >>> par
    par([[2, 3, 4]])


    >>> par.value = 0, 0, 2
    >>> trim(par, lower=[0, INT_NAN, 2])

    >>> par.value = 2, 4, 4
    >>> trim(par, upper=[2, INT_NAN, 4])

    >>> Par.TYPE = bool
    >>> par.trim()

    >>> Par.TYPE = str
    >>> par.trim()
    Traceback (most recent call last):
    ...
    NotImplementedError: Method `trim` can only be applied on parameters \
handling floating point, integer, or boolean values, but the "value type" \
of parameter `par` is `str`.

    >>> pub.options.warntrim = False
    """
    if hydpy.pub.options.trimvariables:
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
        if (old + _get_tolerance(old)) < (lower - _get_tolerance(lower)):
            _warn_trim(self, oldvalue=old, newvalue=lower)
    elif self > upper:
        old = self.value
        self.value = upper
        if (old - _get_tolerance(old)) > (upper + _get_tolerance(upper)):
            _warn_trim(self, oldvalue=old, newvalue=upper)


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
        old = self.values.copy()
        trimmed = numpy.clip(self.values, lower, upper)
        self.values = trimmed
        if (numpy.any((old + _get_tolerance(old)) <
                      (lower - _get_tolerance(lower))) or
                numpy.any((old - _get_tolerance(old)) >
                          (upper + _get_tolerance(upper)))):
            _warn_trim(self, oldvalue=old, newvalue=trimmed)
    self[idxs] = numpy.nan


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


def _get_tolerance(values):
    """Return some sort of "numerical accuracy" to be expected for the
    given floating point value (see method |trim|)."""
    return abs(values*1e-15)


def _warn_trim(self, oldvalue, newvalue):
    if hydpy.pub.options.warntrim:
        warnings.warn(
            f'For variable {objecttools.devicephrase(self)} at least one '
            f'value needed to be trimmed.  The old and the new value(s) '
            f'are `{oldvalue}` and `{newvalue}`, respectively.')


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
        if self is other:
            return method_string in ('__eq__', '__le__', '__ge__')
        method = getattr(self.value, method_string)
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
                f'While trying to compare variable '
                f'{objecttools.elementphrase(self)} with object '
                f'`{other}` of type `{objecttools.classname(other)}`')
    return comparison_function


class Variable(abctools.VariableABC):
    """Base class for |Parameter| and |Sequence|.

    This base class implements special methods for arithmetic calculations,
    comparisons and type conversions.  See the  following examples on how
    to do math with HydPys |Parameter| and |Sequence| objects.

    The subclasses are required to provide the members as `NDIM` (usually
    a class attribute) and `value` (usually a property).  For testing
    purposes, we simply add them as class attributes to a copy of class
    |Variable|.

    >>> from hydpy.core.variabletools import Variable
    >>> class Var(Variable):
    ...     NDIM = 0
    ...     shape = None
    ...     value = None
    ...     __call__ = None

    >>> var = Var()

    A few examples for 0-dimensional objects:

    >>> var.shape = ()
    >>> var.value = 2.0
    >>> var + var
    4.0
    >>> 3.0 - var
    1.0
    >>> var /= 2.0
    >>> var
    var(1.0)
    >>> var[0] = 2.0 * var[:]
    >>> var[0]
    2.0
    >>> var[1]
    Traceback (most recent call last):
    ...
    IndexError: While trying to access the value(s) of variable `var` \
with key `1`, the following error occurred: The only allowed keys for \
0-dimensional variables are `0` and `:`.


    Similar examples for 1-dimensional objects:

    >>> import numpy
    >>> var.NDIM = 1
    >>> var.shape = (3,)
    >>> var.value = numpy.array([1.0, 2.0, 3.0])
    >>> print(var + var)
    [ 2.  4.  6.]
    >>> print(3. - var)
    [ 2.  1.  0.]
    >>> var /= 2.
    >>> var
    var(0.5, 1.0, 1.5)
    >>> var[:] = var[1]
    >>> var[:2]
    array([ 1.,  1.])
    >>> var[:] = 'test'
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `var` \
with key `slice(None, None, None)`, the following error occurred: \
could not convert string to float: 'test'


    Note that comparisons on |Variable| objects containg multiple
    values return a single boolean only:

    >>> var.value = numpy.array([1.0, 3.0])
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

    When asking for impossible comparisons, error messages like the following
    are returned:

    >>> var < [1.0, 2.0, 3.0]   # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: While trying to compare variable `var(1.0, 3.0)` of \
element `?` with object `[1.0, 2.0, 3.0]` of type `list`, the following \
error occurred: operands could not be broadcast together with shapes (2,) (3,)

    >>> Var.NDIM = 0
    >>> Var.value = 1.0
    >>> var < 'text'
    Traceback (most recent call last):
    ...
    TypeError: '<' not supported between instances of 'Var' and 'str'

    The |len| operator always returns the total number of values handles
    by the variable according to the current shape:

    >>> var.shape = ()
    >>> len(var)
    1
    >>> var.shape = (5,)
    >>> len(var)
    5
    >>> var.shape = (2, 1, 4)
    >>> len(var)
    8
    """
    # Subclasses need to define...
    NDIM: ClassVar[int]
    TYPE: ClassVar[type]
    # ...and optionally...
    INIT: ClassVar[Union[int, float]]

    initvalue: Union[float, int]
    fastaccess: Any
    subvars: 'SubVariables'

    mask = masktools.DefaultMask()

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """To be overridden."""

    @property
    def value(self) -> Union[float, int, numpy.ndarray]:
        """Actual parameter or sequence value(s).

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     NDIM = 0
        ...     TIME = None
        ...     TYPE = float
        >>> par = Par()
        >>> par.value = 3
        >>> par.value
        3.0

        >>> par.value = [2.0]
        >>> par.value
        2.0

        >>> par.value = 1.0, 1.0
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the value(s) of variable `par`, the \
following error occurred: 2 values are assigned to the scalar variable `par`.

        >>> par.value = 'O'
        Traceback (most recent call last):
        ...
        TypeError: While trying to set the value(s) of variable `par`, \
the following error occurred: The given value `O` cannot be converted \
to type `float`.
        """
        value = getattr(self.fastaccess, self.name, None)
        if value is None:
            raise AttributeError(
                f'For variable {objecttools.devicephrase(self)}, no '
                f'value/values has/have been defined so far.')
        if self.NDIM:
            return numpy.asarray(value)
        return self.TYPE(value)

    @value.setter
    def value(self, value: ValuesType) -> None:
        try:
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
                try:
                    temp = value[0]
                except (TypeError, IndexError):
                    pass
                else:
                    if len(value) > 1:
                        raise ValueError(
                            f'{len(value)} values are assigned to the scalar '
                            f'variable {objecttools.devicephrase(self)}.')
                    value = temp
                try:
                    value = self.TYPE(value)
                except (ValueError, TypeError):
                    raise TypeError(
                        f'The given value `{value}` cannot be converted '
                        f'to type `{objecttools.classname(self.TYPE)}`.')
            setattr(self.fastaccess, self.name, value)
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to set the value(s) of variable '
                f'{objecttools.devicephrase(self)}')

    @property
    def values(self) -> Union[float, int, numpy.ndarray]:
        """Alias for |Variable.value|."""
        return self.value

    @values.setter
    def values(self, values: ValuesType) -> None:
        self.value = values   # type: ignore

    @property
    def shape(self) -> Tuple[int, ...]:
        """A tuple containing the lengths in all dimensions of the sequence
        values at a specific time point.  Note that setting a new shape
        results in a loss of the actual values of the respective sequence.
        For 0-dimensional sequences an empty tuple is returned.
        """
        if self.NDIM:
            try:
                value: numpy.ndarray = self.value
                return tuple(int(x) for x in value.shape)
            except AttributeError:
                raise RuntimeError(
                    f'Shape information for variable '
                    f'{objecttools.devicephrase(self)} can only '
                    f'be retrieved after it has been defined.')
        else:
            return ()

    @shape.setter
    def shape(self, shape: Iterable[int]):
        if self.NDIM:
            array: numpy.ndarray
            try:
                array = numpy.full(shape, self.initvalue, dtype=self.TYPE)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying create a new numpy ndarray` for variable '
                    f'{objecttools.devicephrase(self)}')
            if array.ndim == self.NDIM:
                setattr(self.fastaccess, self.name, array)
            else:
                raise ValueError(
                    f'Variable {objecttools.devicephrase(self)} is '
                    f'{self.NDIM}-dimensional, but the given '
                    f'shape indicates `{array.ndim}` dimensions.')
        else:
            if shape:
                raise ValueError(
                    f'The shape information of 0-dimensional variables '
                    f'as {objecttools.devicephrase(self)} can only be `()`, '
                    f'but `{shape}` is given.')
            # else:  ToDo
            #     self.value = self.initvalue

    NOT_DEEPCOPYABLE_MEMBERS = ()

    @staticmethod
    def _arithmetic_conversion(other):
        try:
            return other.value
        except AttributeError:
            return other

    def _arithmetic_exception(self, verb, other):
        objecttools.augment_excmessage(
            f'While trying to {verb} variable {objecttools.devicephrase(self)} '
            f'and `{objecttools.classname(other)}` instance `{other}`')

    name = property(objecttools.name)

    def verify(self) -> None:
        """Raises a |RuntimeError| if at least one of the required values
        of a |Variable| object is |None| or |numpy.nan|. Descripter
        `mask` defines, which values are considered to be necessary.

        Example on a 0-dimensional |Variable|:

        >>> from hydpy.core.variabletools import Variable
        >>> class Var(Variable):
        ...     shape = None
        ...     value = None
        ...     __call__ = None
        >>> var = Var()
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
    def refweights(self) -> 'Variable':   # ToDo
        """Reference to a |Parameter| object that defines weighting
        coefficients (e.g. fractional areas) for applying
        |Variable.average_values|.  Must be overwritten by subclasses,
        when required."""
        raise AttributeError(
            f'Variable {objecttools.devicephrase(self)} does '
            f'not define any weighting coefficients.')

    def average_values(self, *args, **kwargs) -> float:
        """Average the actual values of the |Variable| object.

        For 0-dimensional |Variable| objects, the result of
        |Variable.average_values| equals |Variable.value|.  The
        following example shows this for the sloppily defined class
        `SoilMoisture`:

        >>> from hydpy.core.variabletools import Variable
        >>> class SoilMoisture(Variable):
        ...     NDIM = 0
        ...     value = 200.0
        ...     refweigths = None
        ...     availablemasks = None
        ...     __call__ = None
        >>> sm = SoilMoisture()
        >>> sm.average_values()
        200.0

        When the dimensionality of this class is increased to one,
        applying |Variable.average_values| results in the following error:

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
        1-dimensional) |Variable| subclass (usually a |Parameter| ToDo
        subclass), and make the relevant object available via property
        |Variable.refweights|:

        >>> class Area(Variable):
        ...     NDIM = 1
        ...     shape = (3,)
        ...     value = numpy.array([1.0, 1.0, 2.0])
        ...     __call__ = None
        >>> area = Area()
        >>> SoilMoisture.refweights = property(lambda self: area)
        >>> sm.average_values()
        400.0

        In the examples above are all single entries of `values` relevant,
        which is the default case.  But subclasses of |Variable| can
        define an alternative mask, allowing to make some entries
        irrelevant. Assume for example, that our `SoilMoisture` object
        contains three single values, because each one is associated with
        a specific hydrological response unit (hru).  To indicate that
        soil moisture is not defined for the third unit, (maybe because
        it is a water area), we set the third entry of the verification
        mask to |False|:

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

        If the general mask of the variable does not contain the given
        masks, an error is raised:

        >>> sm.average_values('flatsoil', 'water')
        Traceback (most recent call last):
        ...
        ValueError: While trying to calculate the mean value of variable \
`soilmoisture`, the following error occurred: Based on the arguments \
`('flatsoil', 'water')` and `{}` the mask `CustomMask([ True, False,  True])` \
has been determined, which is not a submask of `Soil([ True,  True, False])`.

        Applying masks with own options is also supported.  One can change
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
        has to pass the variable relevant variable as the first argument.):

        >>> sm.average_values(   # doctest: +ELLIPSIS
        ...     sm.availablemasks.allornothing(sm, complete=True))
        Traceback (most recent call last):
        ...
        ValueError: While trying to...

        Alternatively, one can pass the mask name as a keyword and pack
        the mask's options into an |dict| object:

        >>> sm.average_values(allornothing={'complete': False})
        nan

        All variants explained above can be combined:

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
        """|Masks| object provided by the corresponding |Model| object."""
        return self.subvars.vars.model.masks

    def get_submask(self, *args, **kwargs) -> masktools.CustomMask:
        """Get a submask of the mask handled by the actual |Variable| object
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
            attr = getattr(self.value, type_)
            try:
                return attr()
            except TypeError:
                return attr
        else:
            raise TypeError(
                f'The variable {objecttools.devicephrase(self)} is '
                f'{self.NDIM}-dimensional and thus cannot be converted '
                f'to a scalar {objecttools.classname(type_)} value.')

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

    def __hash__(self):
        return id(self)

    def commentrepr(self) -> List[str]:
        """Returns a list with comments, e.g. for making string
        representations more informative.  When `pub.options.reprcomments`
        is set to |False|, an empty list is returned.
        """
        if hydpy.pub.options.reprcomments:
            return [f'# {line}' for line in
                    textwrap.wrap(objecttools.description(self), 78)]
        return []

    def to_repr(self, values: ValuesType, islong: bool) -> str:
        """Return a valid string representation of the actual |Variable|
        object."""
        prefix = f'{self.name}('
        if self.NDIM == 0:
            string = f'{self.name}({objecttools.repr_(values)})'
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
                f'`repr` does not yet support parameters or sequences '
                f'like {objecttools.devicephrase(self)} which handle '
                f'{self.NDIM}-dimensional matrices.')
        return '\n'.join(self.commentrepr() + [string])

    def __repr__(self):
        return self.to_repr(self.value, False)


class SubVariables:
    """Base class for |SubParameters| and |SubSequences|.

    See class |SubParameters| for further information.
    """
    CLASSES = ()
    VARTYPE = None

    def __init__(self, variables, cls_fastaccess=None, cymodel=None):   # ToDo
        self.vars = variables
        self.init_fastaccess(cls_fastaccess, cymodel)
        for cls in self.CLASSES:
            setattr(self, objecttools.instancename(cls), cls())

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Must be implemented by subclasses."""

    @abc.abstractmethod
    def init_fastaccess(self, cls_fastaccess, cymodel):
        """ToDo"""

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
            super().__setattr__(name, value)
            if isinstance(value, self.VARTYPE):
                value.connect(self)
        else:
            try:
                attr.value = value
            except AttributeError:
                raise RuntimeError(
                    f'`{objecttools.classname(self)}` instances do not '
                    f'allow the direct replacement of their members.  '
                    f'After initialization you should usually only '
                    f'change parameter values through assignements.  '
                    f'If you really need to replace a object member, '
                    f'delete it beforehand.')

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
            f'The given {objecttools.value_of_type(variable)} is '
            f'neither a {name} class nor a {name} instance.')

    def __repr__(self):
        lines = []
        if hydpy.pub.options.reprcomments:
            lines.append(f'# {objecttools.classname(self)} object defined '
                         f'in module {objecttools.modulename(self)}.')
            lines.append('# The implemented variables with their actual '
                         'values are:')
        for variable in self:
            try:
                lines.append(repr(variable))
            except BaseException:
                lines.append(f'{variable.name}(?)')
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)
