# import...
"""This module implements features for the validation of (numerical) input
data.
"""
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import magictools


def test_equal_shape(**kwargs):
    """Raise a ValueError if the shapes of the objects given as keywords
    are not equal.

    If all shapes are equal, nothing happens:

    >>> from hydpy.auxs.validtools import test_equal_shape
    >>> test_equal_shape(arr1=numpy.array([1., 2.]),
    ...                  arr2=numpy.array([3., 4.]),
    ...                  arr3=numpy.array([5., 6.]))

    If at least one shape differs, the following error is raised:

    >>> test_equal_shape(arr1=numpy.array([1., 2.]),
    ...                  arr2=numpy.array([3.]),
    ...                  arr3=numpy.array([5., 6.]))
    Traceback (most recent call last):
    ...
    ValueError: The shapes of the following objects are not equal: arr1 (2,), arr2 (1,), arr3 (2,).

    For flexibility in the functions application, it is allowed to pass only
    one array or no arrays at all:

    >>> test_equal_shape(arr1=numpy.array([1., 2.]))
    >>> test_equal_shape()
    """
    names = list(kwargs.keys())
    shapes = numpy.array([numpy.array(array).shape
                          for array in kwargs.values()])
    if any(shapes[:-1] != shapes[1:]):
        raise ValueError(
            'The shapes of the following objects are not equal: %s.'
            % ', '.join('%s %s' % (name, tuple(shape)) for (name, shape)
                        in sorted(zip(names, shapes))))


def test_non_negative(**kwargs):
    """Raise a ValueError if at least one value of the objects given as
    keywords is negative.

    If all values are non negative, nothing happens:

    >>> from hydpy.auxs.validtools import test_non_negative
    >>> test_non_negative(arr1=numpy.array([1., 2.]),
    ...                   arr2=numpy.array([3., 4.]),
    ...                   arr3=numpy.array([5., 6.]))

    If at least one value is negative, the following error is raised:

    >>> test_non_negative(arr1=numpy.array([1., 2.]),
    ...                   arr2=numpy.array([-3., 4.]),
    ...                   arr3=numpy.array([5., 6.]))
    Traceback (most recent call last):
    ...
    ValueError: For the following objects, at least one value is negative: arr2.

    For flexibility in the functions application, it is allowed to pass
    no arrays at all:

    >>> test_non_negative()
    """
    names = list(kwargs.keys())
    negs = [numpy.nanmin(array) < 0. for array in kwargs.values()]
    if any(negs):
        raise ValueError(
            'For the following objects, at least one value is negative: %s.'
            % ', '.join(name for name, neg in sorted(zip(names, negs)) if neg))

magictools.autodoc_module()
