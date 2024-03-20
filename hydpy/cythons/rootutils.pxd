# -*- coding: utf-8 -*-
"""This Cython module implements the performance-critical features of the
Python module |roottools|."""

cimport numpy

cdef class PegasusBase:

    cdef double apply_method0(self, double x) noexcept nogil

    cdef double find_x(
        self,
        double x0,
        double x1,
        double xmin,
        double xmax,
        double xtol,
        double ytol,
        int itermax,
    ) noexcept nogil
