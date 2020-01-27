# -*- coding: utf-8 -*-
"""This Cython module implements the performance-critical features of the
Python module |roottools|."""

# import...
# ...from standard library
from typing import *
# ...from site-packages
cimport cython
from libc.math cimport fabs
from libc.math cimport NAN as nan


cdef class PegasusBase:

    cdef double apply_method0(self, double x) nogil:
        return nan

    cdef double find_x(
            self, double x0, double x1, double xtol, double ytol) nogil:
        cdef double x, y, y0, y1, dx
        if x0 > x1:
            x0, x1 = x1, x0
        while True:
            y0 = self.apply_method0(x0)
            if fabs(y0) < ytol:
                return x0
            y1 = self.apply_method0(x1)
            if fabs(y1) < ytol:
                return x1
            dx = x1-x0
            if (y0 < 0 and y1 < 0) or (y0 > 0 and y1 > 0):
                x0 =- dx
                x1 += dx
            else:
                break
        if fabs(dx) < xtol:
            return (x0+x1)/2
        while True:
            x = x0-y0*dx/(y1-y0)
            y = self.apply_method0(x)
            if fabs(y) < ytol:
                return x
            if ((y1 < 0) and (y < 0)) or ((y1 > 0) and (y > 0)):
                y0 *= y1/(y1+y)
            else:
                x0 = x1
                y0 = y1
            x1 = x
            y1 = y
            dx = x1-x0
            if fabs(dx) < xtol:
                return x


@cython.final
cdef class PegasusPython(PegasusBase):

    cdef public object method0

    cpdef double find_x(
            self, double x0, double x1, double xtol, double ytol) nogil:
        return PegasusBase.find_x(self, x0, x1, xtol, ytol)

    cpdef double apply_method0(self, double x) nogil:
        with gil:
            return self.method0(x)
