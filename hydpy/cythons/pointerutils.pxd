# -*- coding: utf-8 -*-

cimport numpy

cdef class DoubleBase:
    pass


cdef class Double(DoubleBase):

    cdef double value


cdef class PDouble(DoubleBase):

    cdef double *p_value


cdef class PPDouble:

    cdef object ready
    cdef int length
    cdef double **pp_value
    cdef bint _allocated