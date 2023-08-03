# -*- coding: utf-8 -*-
"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

from cpython cimport PyObject
cimport numpy


cdef class BaseInterface:

    cdef public int typeid
    cdef public int idx_sim

    cdef void load_data(self, int idx) nogil
    cdef void save_data(self, int idx) nogil


cdef class SubmodelsProperty:

    cdef int number
    cdef int[:] typeids
    cdef PyObject **submodels
