# -*- coding: utf-8 -*-
"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

cimport numpy


cdef class BaseInterface:

    cdef numpy.int32_t typeid
