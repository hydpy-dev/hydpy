# -*- coding: utf-8 -*-
"""This Cython module implements the performance-critical methods of the
Python module :mod:`~hydpy.auxs.anntools`.
"""

from libc.math cimport exp


cdef class ANN(object):

    def process_actual_input(self):
        cdef int idx_input, idx_neuron, idx_output
        cdef double state
        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = self.intercepts_output[idx_output]
        for idx_neuron in range(self.nmb_neurons):
            state = self.intercepts_input[idx_neuron]
            for idx_input in range(self.nmb_inputs):
                state += (self.inputs[idx_input] *
                          self.weights_input[idx_neuron, idx_input])
            state = 1./(1.+exp(-state))
            for idx_output in range(self.nmb_outputs):
                self.outputs[idx_output] += (
                        state*self.weights_output[idx_neuron, idx_output])
