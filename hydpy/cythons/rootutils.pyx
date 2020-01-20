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
            self, double xmin, double xmax, double xtol, double ytol) nogil:
        cdef double x, y, ymin, ymax, dx
        dx = xmax-xmin
        if fabs(dx) < xtol:
            return (xmax+xmin)/2.
        while True:
            ymin = self.apply_method0(xmin)
            if fabs(ymin) < ytol:
                return xmin
            if ymin <= 0.:
                break
            xmin -= dx
        while True:
            ymax = self.apply_method0(xmax)
            if fabs(ymax) < ytol:
                return xmax
            if ymax >= 0.:
                break
            xmax += dx
        while True:
            x = xmin-ymin*(xmax-xmin)/(ymax-ymin)
            y = self.apply_method0(x)
            if fabs(y) < ytol:
                return x
            if ((ymax < 0.) and (y < 0.)) or ((ymax > 0.) and (y > 0.)):
                ymin *= ymax/(ymax+y)
            else:
                xmin = xmax
                ymin = ymax
            xmax = x
            ymax = y
            if fabs(xmax-xmin) < xtol:
                return x


@cython.final
cdef class PegasusPython(PegasusBase):

    cdef public object method0

    cpdef double find_x(
            self, double xmin, double xmax, double xtol, double ytol) nogil:
        return PegasusBase.find_x(self, xmin, xmax, xtol, ytol)

    cpdef double apply_method0(self, double x) nogil:
        with gil:
            return self.method0(x)
