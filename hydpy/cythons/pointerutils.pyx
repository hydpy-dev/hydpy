# -*- coding: utf-8 -*-
#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This module gives Python objects pointer access to C variables of type
`double` via Cython.

Module |pointerutils| implements the following Cython extension types:
  * |DoubleBase|: Base class, only for inheritance.
  * |Double|: For C variables of type double.
  * |PDouble|: For C pointers referencing a single C variable of type double.
  * |PPDouble|: For C pointers referencing multiple C variables of type double.

Classes |Double| and |PDouble| support arithmetic operations in a similar
manner as the immutable standard data type for floating-point operations
(|float|). |Double| and |PDouble| should be preferred over |float| only
when their pointer functionality is required.  At the moment, the only usage
of |Double| and |PDouble| within *HydPy* is to directly share information
between |NodeSequence| objects of |Node| instances and |LinkSequence|
objects of |Model| instances handled by |Element| instances.

The following examples try to give an idea of the purpose of using pointers
in *HydPy*.

To use the |numpy| |numpy.ndarray| offers the advantage to be able to address
the same data with different Python and Cython objects:

>>> import numpy
>>> from hydpy.cythons.pointerutils import Double, PDouble
>>> xs = numpy.zeros(5)
>>> ys = xs[:]
>>> xs[1] = 1.0
>>> ys[3] = 3.0
>>> print(all(xs == ys), xs is ys)
True False

Both "names" `x` and `y` refer to the same data.  Hence data can
easily be shared between different objects, no matter if they are Python
or Cython types.  Unfortunately, |numpy.ndarray| is primarily
designed to handle at least 1-dimensional data.  Using it for scalar values
stored within a "0-dimensional array" is possible, but has some drawbacks.
Hence, one would usually use the Python build in |float| for scalar values:

>>> x = 0.0
>>> y = x
>>> x = 1.0
>>> print(x == y, x is y)
False False

Now `x` and `y` refer to different data. As an alternative, C implements
the concept of pointers.  Wrapped in Cython objects of the types |Double|
and |PDouble|, this concept provides the following benefit:

>>> dx = Double(0.0)
>>> dx
Double(0.0)
>>> px = PDouble(dx)
>>> px
PDouble(Double(0.0))
>>> dx.setvalue(1.0)
>>> dx
Double(1.0)
>>> px
PDouble(Double(1.0))
>>> px.setvalue(2.0)
>>> dx
Double(2.0)
>>> px
PDouble(Double(2.0))

|Double| and |PDouble| implement many convenience functions, allowing,
for example, to use them in numerical calculations as if they were |float|
objects.  For demonstration purposes, we prepare two objects with different v
alues of each type, respectively:

>>> fx, fy = 1.0, -2.3
>>> dx, dy = Double(fx), Double(fy)
>>> px, py = PDouble(dx), PDouble(dy)

You can combine |Double|, |PDouble| and |float| in any calculation.
The following example demonstrates all possible combinations using the
`add` operator:

>>> from hydpy import round_
>>> round_(dx + dy)
-1.3
>>> round_(px + py)
-1.3
>>> round_(dx + py)
-1.3
>>> round_(py + dx)
-1.3
>>> round_(dx + fy)
-1.3
>>> round_(fy + dx)
-1.3
>>> round_(py + fx)
-1.3
>>> round_(fx + py)
-1.3

The following other binary and unary operators are supported as well:

>>> round_((fx - fy) + (dx - dy) + (px - py))
9.9
>>> round_((fx * fy) + (dx * dy) + (px * py))
-6.9
>>> round_((fx / fy) + (dx / dy) + (px / py))
-1.304348
>>> round_((fx // fy) + (dx // dy) + (px // py))
-3.0
>>> round_((fx % fy) + (dx % dy) + (px % py))
-3.9
>>> round_((2.0**fy) + (Double(2.0)**dy) + (PDouble(Double(2.0))**py))
0.609189

>>> round_(+fy + +dy + +py)
-6.9
>>> round_(-fy + -dy + -py)
6.9
>>> round_(1.0/fy + ~dy + ~py)
-1.304348

We support the following type conversions:

>>> str(dx), int(px), float(py), bool(py)
('1.0', 1, -2.3, True)

All comparison operators are supported:

>>> (dx < dx, dx <= dx, dx==dx, dx!=dx, dx>=dx, dx>dx)
(False, True, True, False, True, False)
>>> (px < py, px <= py, px==py, px!=py, px>=py, px>py)
(False, False, False, True, True, True)
>>> (dy < px, dy <= px, dy==px, dy!=px, dy>=px, dy>px)
(True, True, False, True, False, False)

You can apply the familiar in-place operators:

>>> dx += 1.0
>>> round_(dx)
2.0
>>> px -= 1.0
>>> round_(dx)
1.0

>>> dx -= 1.0
>>> round_(dx)
0.0
>>> px += 1.0
>>> round_(dx)
1.0

>>> dx *= 2.0
>>> round_(dx)
2.0
>>> px /= 2.0
>>> round_(dx)
1.0

>>> dx /= 2.0
>>> round_(dx)
0.5
>>> px *= 2.0
>>> round_(dx)
1.0

>>> dx = Double(2.5)
>>> px = PDouble(dx)
>>> dx //= 2.0
>>> round_(dx)
1.0
>>> px //= 0.3
>>> round_(dx)
3.0

>>> dx %= 2.5
>>> round_(dx)
0.5
>>> px %= 0.2
>>> round_(dx)
0.1

To increase consistency between Python code and Cython code (Cython
uses `[0]` as dereferencing syntax) as well as between |PDouble| and
|numpy| arrays (supporting `[:]` slicing), you are allowed to use
arbitrary objects as indices (actually, |Double| and |PDouble| simply
ignore them).

>>> py[0] = -999.0
>>> py[:]
-999.0
>>> dx[:] = 123.
>>> dx[0]
123.0

To resemble 0-dimensional |numpy| arrays, |Double| and |PDouble| return
empty tuples as shape information.

>>> print(dx.shape, px.shape)
() ()

Always remember that, even if not immediately evident, you are working with
pointers.

You are allowed to initialise a |PDouble| object without giving a |Double|
instance to the constructor, but do not do this unless you have an idea
how to specify the proper memory address later:

>>> px = PDouble()

You can construct multiple pointers referencing the same double value:

>>> dx = Double(1.0)
>>> px1, px2 = PDouble(dx), PDouble(dx)
>>> print(dx, px1, px2)
1.0 1.0 1.0
>>> dx += 1.0
>>> print(dx, px1, px2)
2.0 2.0 2.0
>>> px1 -= 1.0
>>> print(dx, px1, px2)
1.0 1.0 1.0

After deleting the original |Double| object, continuing to
use the associated |PDouble| object(s) corrupts your program, as the
pointed position in memory is freed for other purposes:

>>> del dx
>>> px1 += 1.0 # Possibly corrupts your program.

Note:
    |Double| is used in Python mode only; in Cython mode, the usual
    C type `double` is applied.  |PDouble| is also used in Cython mode,
    where it primarily serves the purpose to  pass C pointers of type
    `double` from one Cython module to another one.

A |PDouble| object can point to the value of a single |Double| object.
Instead, |PPDouble| allows pointing to an arbitrary number of |Double|
objects.  After initialisation, one needs to specify their `shape`
first, defining the number of |Double| objects to be taken into account:

>>> from hydpy.cythons.pointerutils import PPDouble
>>> ppdouble = PPDouble()
>>> ppdouble.shape
(0,)
>>> ppdouble[0]
Traceback (most recent call last):
...
RuntimeError: The shape of the actual `PPDouble` instance has not been set yet, which is a necessary preparation before using it.
>>> ppdouble[0] = 1.0
Traceback (most recent call last):
...
RuntimeError: The shape of the actual `PPDouble` instance has not been set yet, which is a necessary preparation before using it.

>>> ppdouble.shape = 4
>>> ppdouble.shape
(4,)
>>> ppdouble.shape = 3
>>> ppdouble.shape
(3,)

Trying to access values via invalid indices does result in errors
like the following:

>>> ppdouble[-1]
Traceback (most recent call last):
...
IndexError: The actual `PPDouble` instance is of length `3`.  Only index values between 0 and 2 are allowed, but the given index is `-1`.
>>> ppdouble[3] = 1.0
Traceback (most recent call last):
...
IndexError: The actual `PPDouble` instance is of length `3`.  Only index values between 0 and 2 are allowed, but the given index is `3`.

>>> ppdouble[0]
Traceback (most recent call last):
...
RuntimeError: The pointer of the actual `PPDouble` instance at index `0` requested, but not prepared yet via `set_pointer`.
>>> ppdouble[0] = 1.0
Traceback (most recent call last):
...
RuntimeError: The pointer of the actual `PPDouble` instance at index `0` requested, but not prepared yet via `set_pointer`.

To finally prepare our |PPDouble| object, we need to assign |Double| objects
to it via method `set_pointer`:

>>> d1, d2, d3 = Double(1.0), Double(2.0), Double(3.0)
>>> ppdouble.set_pointer(d1, 0)
>>> ppdouble.set_pointer(d2, 1)
>>> ppdouble.set_pointer(d3, 2)

Now we can query and modify the current values of the |Double| objects
via our |PPDouble| object:

>>> print(ppdouble[:])
[PDouble(Double(1.0)) PDouble(Double(2.0)) PDouble(Double(3.0))]


>>> ppdouble[:2] = 8.0, 9.0
>>> d3[0] = -1.0
>>> print(ppdouble[0], d1)
8.0 8.0
>>> print(ppdouble[1], d2)
9.0 9.0
>>> print(ppdouble[2], d3)
-1.0 -1.0

"""

# import...
# ...from standard library
import numbers
import cython
# ...from site-packages
import numpy
# cimport...
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free


cdef inline double conv2double(value):
    """Convert `value` (`Double`, `PDouble`, `float`, `int` object) to a
    C variable of type double and return it."""
    cdef double _value
    try:
        value = value[0]
    except (TypeError, IndexError):
        pass
    if isinstance(value, Double):
        _value = value.value
    elif isinstance(value, PDouble):
        _value = value.value[0]
    else:
        try:
            _value = value
        except TypeError:
            print('Types `Douple` and `PDouble` perform arithmetic methods '
                  'only on objects of type `Double`, `PDouble`, `float` and '
                  '`int` (or similar).  The given objects type is `%s`.'
                  % str(type(value)).split("'")[1])
    return _value


cdef class DoubleBase:
    """Base class for |Double| and |PDouble| that implements operators
    which return builtin Python objects."""

    def __add__(x, y):
        return conv2double(x) + conv2double(y)

    def __sub__(x, y):
        return conv2double(x) - conv2double(y)

    def __mul__(x, y):
        return conv2double(x) * conv2double(y)

    def __floordiv__(x, y):
        return conv2double(x) // conv2double(y)

    def __truediv__(x, y):
        return conv2double(x) / conv2double(y)

    def __mod__(x, y):
        return conv2double(x) % conv2double(y)

    def __pow__(x, y, z):
        return conv2double(x)**conv2double(y)

    def __neg__(self):
        return -conv2double(self)

    def __pos__(self):
        return +conv2double(self)

    def __abs__(self,):
        return abs(conv2double(self))

    def __invert__(self):
        return 1./conv2double(self)

    def __int__(self):
        return int(conv2double(self))

    def __float__(self):
        return float(conv2double(self))

    def __str__(self):
        return str(conv2double(self))

    def __format__(self, digits):
        return format(float(self), digits)

    def __richcmp__(x, y, int z):
        cdef double _x = conv2double(x)
        cdef double _y = conv2double(y)
        if z == 0:
            return _x < _y
        if z == 1:
            return _x <= _y
        if z == 2:
            return _x == _y
        if z == 3:
            return _x != _y
        if z == 4:
            return _x > _y
        if z == 5:
            return _x >= _y

    @property
    def shape(self):
        return ()


numbers.Real.register(DoubleBase)


@cython.final
cdef class Double(DoubleBase):
    """Handle a variable of the C type `double` in Python.

    Attributes:
        value (double): C variable, directly accessible through Cython only.
    """

    def __init__(self, value):
        self.value = value

    def setvalue(self, value):
        """Set `value` according to the passed object."""
        self.value = conv2double(value)

    def __getitem__(self, key):
        return self.value

    def __setitem__(self, key, value):
        self.value =  conv2double(value)

    def __iadd__(self, x):
        self.value += conv2double(x)
        return self

    def __isub__(self, x):
        self.value -= conv2double(x)
        return self

    def __imul__(self, x):
        self.value *= conv2double(x)
        return self

    def __idiv__(self, x):
        self.value /= conv2double(x)
        return self

    def __ifloordiv__(self, x):
        self.value //= conv2double(x)
        return self

    def __itruediv__(self, x):
        self.value /= conv2double(x)
        return self

    def __imod__(self, x):
        self.value %= conv2double(x)
        return self

    def __repr__(self):
        return 'Double(%s)' % conv2double(self)


@cython.final
cdef class PDouble(DoubleBase):
    """Handle a pointer to a variable of the C type `double` in Python.

    Attributes:
        p_value (`*double`): C pointer, directly accessible through Cython
            only.
    """

    def __init__(self, Double value=None):
        self.p_value = &value.value

    def setvalue(self, value):
        """Set the value referenced by `p_value`.
        """
        self.p_value[0] = conv2double(value)

    def __getitem__(self, key):
        return self.p_value[0]

    def __setitem__(self, key, value):
        self.p_value[0] =  conv2double(value)

    def __iadd__(self, x):
        self.p_value[0] += conv2double(x)
        return self

    def __isub__(self, x):
        self.p_value[0] -= conv2double(x)
        return self

    def __imul__(self, x):
        self.p_value[0] *= conv2double(x)
        return self

    def __idiv__(self, x):
        self.p_value[0] /= conv2double(x)
        return self

    def __ifloordiv__(self, x):
        self.p_value[0] //= conv2double(x)
        return self

    def __itruediv__(self, x):
        self.p_value[0] /= conv2double(x)
        return self

    def __imod__(self, x):
        self.p_value[0] %= conv2double(x)
        return self

    def __repr__(self):
        return 'PDouble(Double(%s))' % conv2double(self)


@cython.final
cdef class PPDouble:
    """Handle pointers to multiple variables of the C type `double` in Python.

    Attributes:
      * pp_value (`**double`): Second-order C pointer, directly accessible
        through Cython only.
    """
    def __init__(self):
        self.length = 0
        self._allocated = False

    def set_pointer(self, value, idx):
        check0(self.length)
        check1(self.length, idx)
        cdef int _idx = idx
        cdef Double _value = value
        self.pp_value[_idx] = &_value.value
        self.ready[idx] = True

    def _prepare_indices(self, idxs):
        try:
            return list(range(*idxs.indices(self.length)))
        except AttributeError:
            return [idxs]

    def __getitem__(self, idxs):
        idxs_ = self._prepare_indices(idxs)
        values = numpy.empty(len(idxs_), dtype=PDouble)
        check0(self.length)
        for i, idx in enumerate(idxs_):
            check1(self.length, idx)
            check2(self.ready, idx)
            pdouble = PDouble(Double(0.))
            pdouble.p_value = self.pp_value[idx]
            values[i] = pdouble
        if isinstance(idxs, int):
            return values[0]
        return values

    def __setitem__(self, idxs, values):
        cdef float value
        idxs = self._prepare_indices(idxs)
        values = numpy.full(len(idxs), values, dtype=float)
        check0(self.length)
        for idx, value in zip(idxs, values):
            check1(self.length, idx)
            check2(self.ready, idx)
            self.pp_value[idx][0] = value

    def __dealloc__(self):
        PyMem_Free(self.pp_value)

    @property
    def shape(self):
        return (self.length,)

    @shape.setter
    def shape(self, int length):
        if self._allocated:
            PyMem_Free(self.pp_value)
        self._allocated = True
        self.length = length
        self.ready = numpy.full(length, False, dtype=bool)
        self.pp_value = <double**> PyMem_Malloc(length * sizeof(double*))
        self._allocated = True


def check0(length):
    if length == 0:
        raise RuntimeError(
            'The shape of the actual `PPDouble` instance '
            'has not been set yet, which is a necessary '
            'preparation before using it.')

def check1(length, idx):
    if not (0 <= idx < length):
        raise IndexError(
            f'The actual `PPDouble` instance is of length '
            f'`{length}`.  Only index values between 0 and '
            f'{length-1} are allowed, but the given '
            f'index is `{idx}`.')

def check2(ready, idx):
    if not ready[idx]:
        raise RuntimeError(
            f'The pointer of the actual `PPDouble` instance '
            f'at index `{idx}` requested, but not prepared yet '
            f'via `set_pointer`.')