"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

from cpython cimport PyObject
cimport numpy

cdef class Simulator:

    cdef object[:] premethods
    cdef PyObject** models
    cdef int[:] breaks
    cdef int layers
    cdef int parallel_layers
    cdef object[:] postmethods
    cdef int threads
    cdef str schedule
    cdef int chunksize

    cpdef void simulate(self, int idx_start, int idx_end)
    cdef void _simulate_dynamic(self, int idx_start, int idx_end)
    cdef void _simulate_static(self, int idx_start, int idx_end)
