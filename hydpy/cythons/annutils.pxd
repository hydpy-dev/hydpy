# -*- coding: utf-8 -*-
"""This module defines the Cython declarations related to module |anntools|.
"""

from cpython cimport PyObject

cimport numpy

cdef class ANN(object):

    cdef public int nmb_inputs
    cdef public int nmb_outputs
    cdef public int nmb_layers
    cdef public int[:] nmb_neurons
    cdef public double[:, :] weights_input
    cdef public double[:, :] weights_output
    cdef public double[:, :, :] weights_hidden
    cdef public double[:, :] intercepts_hidden
    cdef public double[:] intercepts_output
    cdef public double[:] inputs
    cdef public double[:] outputs
    cdef public double[:, :] neurons
    cdef public double[:] output_derivatives
    cdef public double[:, :] neuron_derivatives

    cpdef inline void calculate_values(self) nogil
    cpdef inline void calculate_derivatives(self, int idx_input) nogil


cdef class SeasonalANN(object):

    cdef public int nmb_anns
    cdef public int nmb_inputs
    cdef public int nmb_outputs
    cdef PyObject **canns
    cdef public double[:, :] ratios
    cdef public double[:] inputs
    cdef public double[:] outputs

    cpdef inline void calculate_values(self, int idx_season) nogil
