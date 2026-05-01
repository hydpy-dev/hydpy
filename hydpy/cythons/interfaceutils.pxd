"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

from cpython cimport PyObject
cimport numpy


cdef class BaseInterface:

    cdef public int typeid
    cdef public int idx_sim

    cdef void reset_reuseflags(self) noexcept nogil
    cdef void load_data(self, int idx) noexcept nogil
    cdef void save_data(self, int idx) noexcept nogil
    cdef void update_inlets(self) noexcept nogil
    cdef void update_observers(self) noexcept nogil
    cdef void update_receivers(self, int idx) noexcept nogil
    cdef void update_outlets(self) noexcept nogil
    cdef void update_senders(self) noexcept nogil
    cdef void update_outputs(self) noexcept nogil


cdef class SubmodelsProperty:

    cdef int number
    cdef int[:] typeids
    cdef PyObject **submodels
