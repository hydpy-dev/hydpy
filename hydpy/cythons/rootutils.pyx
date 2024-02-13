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

    cdef double apply_method0(self, double x) noexcept nogil:
        return nan

    cdef double find_x(
            self,
            double x0,
            double x1,
            double xmin,
            double xmax,
            double xtol,
            double ytol,
            int itermax,
    ) noexcept nogil:
        cdef double x, y, y0, y1, dx
        if x0 > x1:
            x0, x1 = x1, x0
        if xmin > xmax:
            xmin, xmax = xmax, xmin
        x0 = max(x0, xmin)
        x1 = min(x1, xmax)
        while True:
            y0 = self.apply_method0(x0)
            y0_abs = fabs(y0)
            if y0_abs <= ytol:
                return x0
            y1 = self.apply_method0(x1)
            y1_abs = fabs(y1)
            if y1_abs <= ytol:
                return x1
            dx = x1 - x0
            if (y0 < 0 and y1 < 0) or (y0 > 0 and y1 > 0):
                if (x0 == xmin) and (x1 == xmax):
                    if y0_abs <= y1_abs:
                        self.apply_method0(x0)
                        return x0
                    return x1
                x0 = max(x0 - dx, xmin)
                x1 = min(x1 + dx, xmax)
            else:
                break
        if fabs(dx) < xtol:
            return (x0 + x1) / 2
        for iter_ in range(itermax):
            x = x0 - y0 * dx / (y1 - y0)
            if x < xmin:
                self.apply_method0(xmin)
                return xmin
            elif x > xmax:
                self.apply_method0(xmax)
                return xmax
            y = self.apply_method0(x)
            if fabs(y) < ytol:
                return x
            if ((y1 < 0) and (y < 0)) or ((y1 > 0) and (y > 0)):
                y0 *= y1 / (y1 + y)
            else:
                x0 = x1
                y0 = y1
            x1 = x
            y1 = y
            dx = x1 - x0
            if fabs(dx) < xtol:
                break
        return x


@cython.final
cdef class PegasusPython(PegasusBase):

    cdef public object method0

    cpdef double find_x(
            self,
            double x0,
            double x1,
            double xmin,
            double xmax,
            double xtol,
            double ytol,
            int itermax,
    ) noexcept nogil:
        return PegasusBase.find_x(self, x0, x1, xmin, xmax, xtol, ytol, itermax)

    cpdef double apply_method0(self, double x) noexcept nogil:
        with gil:
            return self.method0(x)
