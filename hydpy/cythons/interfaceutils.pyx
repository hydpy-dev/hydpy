# -*- coding: utf-8 -*-
"""This module implements only the interface base class required to support casting to
specific subclasses in Cython."""

import numpy

from cpython cimport Py_DECREF
from libc.stdlib cimport free, malloc, realloc
cimport cython


cdef class BaseInterface:

    cdef void load_data(self, int idx) nogil:
        pass

    cdef void save_data(self, int idx) nogil:
        pass


cdef class SubmodelsProperty:

    def __init__(self) -> None:
        self.set_number(0)

    def _get_number(self) -> int:
        return self.number

    def set_number(self, int number) -> None:
        assert number >= 0
        free(self.submodels)
        self.number = number
        self.typeids = numpy.zeros(number, dtype=int)
        self.submodels = <PyObject **>malloc(
            number * cython.sizeof(cython.pointer(PyObject))
        )
        for i in range(number):
            self.submodels[i] = <PyObject*>None

    def _get_typeid(self, int position) -> int:
        assert 0 <= position < self.number
        return self.typeids[position]

    def _get_submodel(self, int position):
        assert 0 <= position < self.number
        submodel = <object>self.submodels[position]
        Py_DECREF(submodel)
        return submodel

    def put_submodel(self, submodel, int typeid, int position) -> None:
        assert 0 <= position < self.number
        self.typeids[position] = typeid
        self.submodels[position] = <PyObject*>submodel

    def append_submodel(self, submodel, int typeid) -> None:
        self.number += 1
        if self.number > 1:
            typeids = numpy.asarray(self.typeids).copy()
        self.typeids = numpy.zeros(self.number, dtype=int)
        for i in range(self.number - 1):
            self.typeids[i] = typeids[i]
        self.typeids[self.number - 1] = typeid
        self.submodels = <PyObject **>realloc(
            self.submodels, self.number * cython.sizeof(cython.pointer(PyObject))
        )
        self.submodels[self.number - 1] = <PyObject*>submodel

    def __dealloc__(self) -> None:
        free(self.submodels)
