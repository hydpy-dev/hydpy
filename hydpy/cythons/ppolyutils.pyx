"""This Cython module implements the performance-critical methods of the
Python module |anntools|.
"""

from typing import assert_never

import cython
import numpy

# from hydpy.auxs import ppolytools  actual import below
from hydpy.cythons.autogen cimport smoothutils

cimport cython
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from libc.math cimport NAN as nan
from libc.stdlib cimport malloc, free


@cython.final
cdef class PPoly:

    cpdef inline int find_index(self) noexcept nogil:
        """Return the index of the polynomial coefficients."""
        cdef int idx
        cdef double x = self.inputs[0]
        for idx in range(1, self.nmb_ps):
            if x < self.x0s[idx]:
                return idx - 1
        return self.nmb_ps - 1

    cpdef inline void calculate_values(self) noexcept nogil:
        cdef int i, j
        cdef double x0, x, y
        i = self.find_index()
        x0 = self.x0s[i]
        x = self.inputs[0]
        y = 0.0
        for j in range(self.nmb_cs[i]):
            y += self.cs[i, j] * (x - x0) ** j
        self.outputs[0] = y

    cpdef inline void calculate_derivatives(self, int idx_input) noexcept nogil:
        cdef int i, j
        cdef double x0, x, y
        i = self.find_index()
        x0 = self.x0s[i]
        x = self.inputs[0]
        y = 0.0
        for j in range(1, self.nmb_cs[i]):
            y += j * self.cs[i, j] * (x - x0) ** (j - 1)
        self.output_derivatives[0] = y


@cython.final
cdef class PPolys:

    def __init__(self, ppolys) -> None:
        from hydpy.auxs import ppolytools
        self.nmb_ppolys = len(ppolys)
        self.ppolys = <PyObject **>malloc(
            self.nmb_ppolys * cython.sizeof(cython.pointer(PyObject))
        )
        for i, ppoly in enumerate(ppolys):
            if isinstance(ppoly, ppolytools.PPoly):
                self.ppolys[i] = <PyObject*>ppoly._calgorithm
            elif (ppoly == 0) or (ppoly == 1):
                self.ppolys[i] = <PyObject*>None
            else:
                assert_never(ppoly)

    cpdef inline void calculate_values(self) noexcept nogil:
        cdef double output_rest = self.inputs[0]
        for i in range(self.nmb_ppolys):
            if self.options[i] == 0:
                (<PPoly>self.ppolys[i]).inputs[0] = self.inputs[0]
                (<PPoly>self.ppolys[i]).calculate_values()
                self.outputs[i] = (<PPoly>self.ppolys[i]).outputs[0]
                output_rest -= self.outputs[i]
        for i in range(self.nmb_ppolys):
            if self.options[i] == 1:
                self.outputs[i] = output_rest

    cpdef inline void calculate_derivatives(self, int idx_input) noexcept nogil:
        cdef double derivative_rest = 1.0
        for i in range(self.nmb_ppolys):
            if self.options[i] == 0:
                (<PPoly>self.ppolys[i]).calculate_derivatives(idx_input)
                self.output_derivatives[i] = (<PPoly>self.ppolys[i]).output_derivatives[0]
                derivative_rest -= self.output_derivatives[i]
        for i in range(self.nmb_ppolys):
            if self.options[i] == 1:
                self.output_derivatives[i] = derivative_rest
