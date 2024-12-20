"""This module defines the Cython declarations related to module |ppolytools|."""

cimport numpy


cdef class PPoly:

    # required for usage as an "algorithm" by interputils:

    cdef public int nmb_inputs
    cdef public int nmb_outputs
    cdef public double[:] inputs
    cdef public double[:] outputs
    cdef public double[:] output_derivatives

    cpdef inline void calculate_values(self) noexcept nogil
    cpdef inline void calculate_derivatives(self, int idx_input) noexcept nogil

    # algorithm-specific requirements:

    cdef public int nmb_ps
    cdef public int[:] nmb_cs
    cdef public double[:] x0s
    cdef public double[:, :] cs

    cpdef inline int find_index(self) noexcept nogil
