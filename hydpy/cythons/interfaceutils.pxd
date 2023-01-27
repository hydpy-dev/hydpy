# -*- coding: utf-8 -*-
"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

cimport numpy


cdef class BaseInterface:

    cdef public numpy.int32_t typeid
    cdef public numpy.int32_t idx_sim

    cdef void load_data(self) nogil
    cdef void save_data(self, int idx) nogil
