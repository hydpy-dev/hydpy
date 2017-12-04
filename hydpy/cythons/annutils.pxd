# -*- coding: utf-8 -*-
"""This module defines the Cython declarations related to module
:mod:`~hydpy.auxs.anntools`.
"""

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

    cpdef inline void process_actual_input(self) nogil