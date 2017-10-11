#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This Cython module implements the performance-critical methods of the
Python module :mod:`~hydpy.auxs.anntools`.
"""

import cython
from libc.math cimport exp

cdef inline double logistic(double x) nogil:
    return 1./(1.+exp(-x))


@cython.final
cdef class ANN(object):

    cpdef inline void process_actual_input(self) nogil:
        cdef int idx_input, idx_neuron1, idx_neuron2, idx_output, idx_layer

        for idx_neuron1 in range(self.nmb_neurons[0]):
            self.neurons[0, idx_neuron1] = \
                    self.intercepts_hidden[0, idx_neuron1]
            for idx_input in range(self.nmb_inputs):
                self.neurons[0, idx_neuron1] = \
                        (self.neurons[0, idx_neuron1] +
                         (self.weights_input[idx_input, idx_neuron1] *
                          self.inputs[idx_input]))
            self.neurons[0, idx_neuron1] = logistic(self.neurons[0, idx_neuron1])

        for idx_layer in range(1, self.nmb_layers):
            for idx_neuron1 in range(self.nmb_neurons[idx_layer]):
                self.neurons[idx_layer, idx_neuron1] = \
                        self.intercepts_hidden[idx_layer, idx_neuron1]
                for idx_neuron2 in range(self.nmb_neurons[idx_layer-1]):
                    self.neurons[idx_layer, idx_neuron1] = \
                            (self.neurons[idx_layer, idx_neuron1] +
                             (self.weights_hidden[idx_layer-1, idx_neuron2, idx_neuron1] *
                              self.neurons[idx_layer-1, idx_neuron2]))
                self.neurons[idx_layer, idx_neuron1] = \
                        logistic(self.neurons[idx_layer, idx_neuron1])

        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = self.intercepts_output[idx_output]
            for idx_neuron2 in range(self.nmb_neurons[self.nmb_layers-1]):
                self.outputs[idx_output] = \
                        (self.outputs[idx_output] +
                         (self.weights_output[idx_neuron2, idx_output] *
                          self.neurons[self.nmb_layers-1, idx_neuron2]))