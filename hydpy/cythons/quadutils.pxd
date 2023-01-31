# -*- coding: utf-8 -*-
"""This Cython module implements the performance-critical features of the
Python module |quadtools|."""

cimport numpy

cdef class QuadBase:

    cdef double apply_method0(self, double x) nogil

    cdef double integrate(
        self,
        double x0,
        double x1,
        int nmin,
        int nmax,
        double tol,
    ) nogil
