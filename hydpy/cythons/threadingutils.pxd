"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

from cpython cimport PyObject
cimport numpy

cdef class Chunk:

    cdef int number
    cdef PyObject** models

    cpdef void simulate(self, int idx)
    cpdef void simulate_period(self, int idx_start, int idx_end)
    cpdef void simulate_period_stepwise(self, int idx_start, int idx_end)
