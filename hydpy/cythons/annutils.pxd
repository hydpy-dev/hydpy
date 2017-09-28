# -*- coding: utf-8 -*-
"""This defines the Cython declarations related to module
:mod:`~hydpy.auxs.anntools`.
"""

cdef class ANN(object):

    cdef public int nmb_inputs
    cdef public int nmb_neurons
    cdef public int nmb_outputs
    cdef public double[:, :] weights_input
    cdef public double[:, :] weights_output
    cdef public double[:] intercepts_input
    cdef public double[:] intercepts_output
    cdef public double[:] inputs
    cdef public double[:] outputs