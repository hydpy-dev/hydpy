# -*- coding: utf-8 -*-
"""This module implements features for the validation of (numerical) input data."""
# import...
# ...from site-packages
import numpy

# ...from hydpy
from hydpy.core import objecttools


def test_equal_shape(**kwargs) -> None:
    """Raise a ValueError if the shapes of the objects given as keywords are not equal.

    If all shapes are equal, nothing happens:

    >>> from hydpy.auxs.validtools import test_equal_shape
    >>> test_equal_shape(arr1=numpy.array([1.0, 2.0]),
    ...                  arr2=numpy.array([3.0, 4.0]),
    ...                  arr3=numpy.array([5.0, 6.0]))

    If at least one shape differs, the following error is raised:

    >>> test_equal_shape(arr1=numpy.array([1.0, 2.0]),
    ...                  arr2=numpy.array([3.0]),
    ...                  arr3=numpy.array([5.0, 6.0]))
    Traceback (most recent call last):
    ...
    ValueError: The shapes of the following objects are not equal: \
arr1 (2,), arr2 (1,), and arr3 (2,).

    For flexibility in the functions application, it is allowed to pass only one array
    or no arrays at all:

    >>> test_equal_shape(arr1=numpy.array([1.0, 2.0]))
    >>> test_equal_shape()
    """
    names = list(kwargs.keys())
    shapes = numpy.array([numpy.array(array).shape for array in kwargs.values()])
    if any(shapes[:-1] != shapes[1:]):
        string = objecttools.enumeration(
            f"{name} {tuple(shape)}" for (name, shape) in sorted(zip(names, shapes))
        )
        raise ValueError(
            f"The shapes of the following objects are not equal: {string}."
        )


def test_non_negative(**kwargs) -> None:
    """Raise a ValueError if at least one value of the objects given as keywords is
    negative.

    If all values are non negative, nothing happens:

    >>> from hydpy.auxs.validtools import test_non_negative
    >>> test_non_negative(arr1=numpy.array([1.0, 2.0]),
    ...                   arr2=numpy.array([3.0, 4.0]),
    ...                   arr3=numpy.array([5.0, 6.0]))

    If at least one value is negative, the following error is raised:

    >>> test_non_negative(arr1=numpy.array([1.0, 2.0]),
    ...                   arr2=numpy.array([-3.0, 4.0]),
    ...                   arr3=numpy.array([5.0, 6.0]))
    Traceback (most recent call last):
    ...
    ValueError: For the following objects, at least one value is negative: arr2.

    For flexibility in the functions application, it is allowed to pass no array at all:

    >>> test_non_negative()
    """
    names = list(kwargs.keys())
    negs = [numpy.nanmin(array) < 0.0 for array in kwargs.values()]
    if any(negs):
        string = objecttools.enumeration(
            name for name, neg in sorted(zip(names, negs)) if neg
        )
        raise ValueError(
            f"For the following objects, at least one value is negative: {string}."
        )
