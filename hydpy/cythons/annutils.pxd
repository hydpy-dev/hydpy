"""This module defines the Cython declarations related to module |anntools|."""

cimport numpy


cdef class ANN:

    # required for usage as an "algorithm" by interputils:

    cdef public int nmb_inputs
    cdef public int nmb_outputs
    cdef public double[:] inputs
    cdef public double[:] outputs
    cdef public double[:] output_derivatives

    cpdef inline void calculate_values(self) noexcept nogil
    cpdef inline void calculate_derivatives(self, int idx_input) noexcept nogil

    # algorithm-specific requirements:

    cdef public int nmb_layers
    cdef public int[:] nmb_neurons
    cdef public double[:, :] weights_input
    cdef public double[:, :] weights_output
    cdef public double[:, :, :] weights_hidden
    cdef public double[:, :] intercepts_hidden
    cdef public double[:] intercepts_output
    cdef public int[:, :] activation
    cdef public double[:, :] neurons
    cdef public double[:, :] neuron_derivatives

    cdef inline void apply_activationfunction(self, int idx_layer, int idx_neuron, double input_) noexcept nogil
    cdef inline double apply_derivativefunction(self, int idx_layer, int idx_neuron, double inner) noexcept nogil
