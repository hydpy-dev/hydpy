"""This module defines the Cython declarations related to module |interptools|."""

from cpython cimport PyObject

cimport numpy


cdef class SimpleInterpolator:

    cdef public int nmb_inputs
    cdef public int nmb_outputs
    cdef PyObject *algorithm
    cdef public int algorithm_type
    cdef public double[:] inputs
    cdef public double[:] outputs
    cdef public double[:] output_derivatives

    cpdef inline void calculate_values(self) noexcept nogil
    cpdef inline void calculate_derivatives(self, int idx_input) noexcept nogil


cdef class SeasonalInterpolator(object):

    cdef public int nmb_inputs
    cdef public int nmb_outputs
    cdef public int nmb_algorithms
    cdef public int[:] algorithm_types
    cdef PyObject **algorithms
    cdef public double[:, :] ratios
    cdef public double[:] inputs
    cdef public double[:] outputs

    cpdef inline void calculate_values(self, int idx_season) noexcept nogil