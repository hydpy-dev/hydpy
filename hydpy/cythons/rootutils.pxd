# -*- coding: utf-8 -*-
"""This Cython module implements the performance-critical features of the
Python module |roottools|."""


cdef class PegasusBase:

    cdef double apply_method0(self, double x) nogil

    cdef double find_x(
        self, double x0, double x1, double xtol, double ytol) nogil
