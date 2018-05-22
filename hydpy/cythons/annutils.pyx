#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This Cython module implements the performance-critical methods of the
Python module |anntools|`.
"""

# import...
# ...from standard library
import cython
from hydpy.cythons.autogen cimport smoothutils
# ...from site-packages
import numpy
# ...cimport
cimport cython
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from libc.stdlib cimport malloc, free


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
            self.neurons[0, idx_neuron1] = \
                    smoothutils.smooth_logistic1(
                            self.neurons[0, idx_neuron1], 1.)

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
                        smoothutils.smooth_logistic1(
                                self.neurons[idx_layer, idx_neuron1], 1.)

        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = self.intercepts_output[idx_output]
            for idx_neuron2 in range(self.nmb_neurons[self.nmb_layers-1]):
                self.outputs[idx_output] = \
                        (self.outputs[idx_output] +
                         (self.weights_output[idx_neuron2, idx_output] *
                          self.neurons[self.nmb_layers-1, idx_neuron2]))


@cython.final
cdef class SeasonalANN(object):

    def __init__(self, anns):
        self.nmb_anns = len(anns)
        self.nmb_inputs = len(anns[0].inputs)
        self.nmb_outputs = len(anns[0].outputs)
        self.inputs = numpy.zeros(self.nmb_inputs, dtype=float)
        self.outputs = numpy.zeros(self.nmb_outputs, dtype=float)
        self.canns = <PyObject **>malloc(
            self.nmb_anns*cython.sizeof(cython.pointer(PyObject)))
        for idx, ann in enumerate(anns):
            self.canns[idx] = <PyObject*>ann._cann

    def __dealloc__(self):
        free(self.canns)

    cpdef inline void process_actual_input(self, int idx_season) nogil:
        cdef int idx_ann, idx_input, idx_output
        cdef double ratio, frac
        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = 0.
        for idx_ann in range(self.nmb_anns):
            ratio = self.ratios[idx_season, idx_ann]
            if ratio > 0.:
                for idx_input in range(self.nmb_inputs):
                     (<ANN>self.canns[idx_ann]).inputs[idx_input] = self.inputs[idx_input]
                (<ANN>self.canns[idx_ann]).process_actual_input()
                for idx_output in range(self.nmb_outputs):
                    frac = ratio*(<ANN>self.canns[idx_ann]).outputs[idx_output]
                    self.outputs[idx_output] += frac


