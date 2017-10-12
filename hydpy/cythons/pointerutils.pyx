# -*- coding: utf-8 -*-
"""This module gives Python objects pointer access to C variables of type
`double` via Cython.

The following `cdef classes` (Cython extension types) are implemented:
  * :class:`DoubleBase`: Base class, only for inheritance.
  * :class:`Double`: For C variables of type double.
  * :class:`PDouble`: For C pointers referencing C variables of type double.

Classes :class:`Double` and :class:`PDouble` support arithmetic operations in
a similar manner as the immutable standard data type for floating operations
:class:`float`.  :class:`Double` and :class:`PDouble` should be preferred
to :class:`float` only in cases, where their mutability and pointer
functionality is required.  At the moment, the only usage of :class:`Double`
and :class:`PDouble` within HydPy is to directly share information between
:class:`~hydpy.core.sequence.SimulationSequence` objects of
:class:`~hydpy.core.node.Node` instances and
:class:`~hydpy.core.sequence.LinkSequence` objects of
:class:`~hydpy.core.model.Model` instances.

The following examples try to give an idea of the purpose of using pointers
in HydPy::

    import numpy
    from hydpy.cythons.pointer import Double, PDouble

    # Using numpy's ndarray gives the great advantage to be able to adress
    # the same data with different Python and Cython objects.
    # A pure Python / numpy example:
    xs = numpy.zeros(5)
    ys = xs
    xs[1] = 1.
    ys[3] = 3.
    print id(xs), xs
    print id(ys), ys
    # Obviously, both `names` x and y refer to the same data.  Hence data can
    # easily be shared between different objects, no matter if they are Python
    # or Cython types.  However, unfortunately ndarray are primarily designed
    # to handle at least 1-dimensional data.  Using ndarray for scalar values
    # stored within a `0-dimesional array` is possible, but has some drawbacks.
    # Hence, one would usually use the Python build in `float` for scalar
    # values.
    # A pure Python example:
    x = 0.
    y = x
    x = 1.
    print id(x), x
    print id(y), y
    # Obviously, x and y refer to different data.  This behaviour is due to x
    # and y beeing not typed and Python float objects beeing immutable
    # (thoroughly explained in the official documentation of Python).
    # In C the result would be the same, but the reason were that both
    # variables x and y constantly address a different position in the working
    # memory and 'y = x' just passes information from one position to the
    # other.
    # As an alternative, C implements the concept of pointers.  Wrapped in
    # Cython objects of the types Double and PDouble, this concept provides
    # the following benefit:
    x = Double(0.)
    print id(x), x
    px = PDouble(x)
    print id(px), px
    x.setvalue(1.)
    print x, px
    px.setvalue(2.)
    print x, px

:class:`Double` and :class:`PDouble` implement many convenience functions
(Python's `special methods`). Accordingly, their instances can for example be
included into numerical calculations as one knows from :class:`float` objects.
In order to increase the compatibility with external modules, when new objects
are generated, these are of type :class:`float` (except for type conversions
and comparision which await :class:`bool` objects). Some examples::

    from hydpy.cythons.pointer import Double, PDouble

    x, y = Double(1.), Double(-2.3)
    px, py = PDouble(x), PDouble(y)

    # A simple arithmetic operation returning a new float object:
    z = x + py + 3.
    print type(z), z
    # A more fancy example:
    z = -x % ~py
    print type(z), z
    # Some type conversion:
    print str(x), int(px), float(py)
    # Some comparisions:
    print x > 1., x <= px, px == py
    # Some in-place operations:
    print x, py
    x += 1.
    py *= 2.
    print x, py
    # Assignments to to ndarrays.
    zs = numpy.zeros(5)
    print zs.dtype, zs
    zs[1:3] = x, py
    print zs.dtype, zs

    # To increase consistency between Python code and Cython code (Cython
    # uses '[0]' as dereferencing syntax) as well as between PDouble and numpy
    # arrays (numpy arrays support '[:]' slicing) arbitrary objects as can
    # be used as indices (actually, they are ignored).
    py[0] = -999.
    print py[:]
    x[:] = 123.
    print x[0]
    # To resemble 0-dimensional numpy arrays, Double and PDouble return empty
    # tuples as shape information.
    print x.shape, px.shape


Always remember that, even if not immediately evident, you are working with
pointers::

    from hydpy.cythons.pointer import Double, PDouble

    # You are allowed to initialize a PDouble object without giving an Double
    # instance to the constructor.  Do not do this unless you have an idea
    # how to specify the proper working memory memory adress later.
    px = PDouble()
    print px

    # You can construct multiple pointers.
    x = Double(1.)
    px1, px2 = PDouble(x), PDouble(x)
    print x, px1, px2
    x += 1.
    print x, px1, px2
    px1 -= 1.
    print x, px1, px2

    # But when you delete the original Double object, further using the
    # associated PDouble object(s) corrupts your program, as the pointed
    # position in working memory is freed for other purposes.
    del x
    print px1, px2 # Returns possibly useless results.
    px1 += 1. # Possibly corrupts your (or another) program.

    # Instead of C pointers, you can also build Python references, which might
    # also happen unintentional:
    x, y = Double(1.), Double(2.)
    z = min(x, y)
    x -= z
    print x, y, z
    print id(x), id(y), id(z)

Note:
    :class:`Double` is used in Python mode only; in Cython mode, the usual
    C type `double` is applied.  :class:`PDouble` is also used in Cython mode,
    where it essentially serves the purpose pass C a pointers of type
    'double' from Cython module to another.

------------------------------------------------------------------------------
"""

# import...
# ...from standard library
from __future__ import division, print_function
import numpy
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


cdef class DoubleBase(object):
    """Base class for :class:`Double` and :class:`PDouble` that implements
    operators which return builtin Python objects."""

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

    def __repr__(self):
        return repr(conv2double(self))

    def __str__(self):
        return str(conv2double(self))

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


cdef class PPDouble(object):
    """Handle pointers to multiple variables of the C type `double` in Python.

    Attributes:
      * pp_value (`**double`): Second order C pointer, directly accessible
        through Cython only.
    """
    def __init__(self):
        self.length = 0

    def check0(self):
        if self.length == 0:
            raise RuntimeError('The shape of the actual `PPDouble` instance '
                             'has not been set yet, which is a necessary '
                             'preparation for each of its uses.')

    def check1(self, idx):
        if not (0 <= idx < self.length):
            raise IndexError('The actual `PPDouble` instance is of shape %s. '
                             'Only index values between 0 and %d are allowed, '
                             'but the given index is %d.'
                             % (self.shape, self.length-1, idx))

    def check2(self, idx):
        if not self.ready[idx]:
            raise RuntimeError('The pointer of the acutal `PPDouble` instance '
                               'at index %s requested, but not prepared yet '
                               'via `setpointer`.' % idx)

    def setpointer(self, value, idx):
        self.check0()
        self.check1(idx)
        cdef int _idx = idx
        cdef Double _value = value
        self.pp_value[_idx] = &_value.value
        self.ready[idx] = True

    def __getitem__(self, idx):
        cdef PDouble value
        self.check0()
        self.check1(idx)
        self.check2(idx)
        value = PDouble(Double(0.))
        value.p_value = self.pp_value[idx]
        return value

    def __dealloc__(self):
        PyMem_Free(self.pp_value)

    def _getshape(self):
        return (self.length, )
    def _setshape(self, int length):
        if self.length != 0:
            raise RuntimeError('The shape of `PPDouble` of instances must not '
                               'be changed.')
        self.length = length
        self.ready = numpy.full(length, False, dtype=bool)
        self.pp_value = <double**> PyMem_Malloc(length * sizeof(double*))
    shape = property(_getshape, _setshape)
