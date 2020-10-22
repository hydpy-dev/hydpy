"""This Cython module implements the performance-critical methods of the
Python module |anntools|.
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
from libc.math cimport NAN as nan
from libc.stdlib cimport malloc, free


@cython.final
cdef class ANN(object):

    cdef inline void apply_activationfunction(self, int idx_layer, int idx_neuron, double input_) nogil:
        if self.activation[idx_layer, idx_neuron] == 1:
            self.neurons[idx_layer, idx_neuron] = \
                smoothutils.smooth_logistic1(self.neurons[idx_layer, idx_neuron], 1.)
        elif self.activation[idx_layer, idx_neuron] == 2:
            self.neurons[idx_layer, idx_neuron] = \
                input_ * smoothutils.smooth_logistic1(self.neurons[idx_layer, idx_neuron], 1.)

    cdef inline double apply_derivativefunction(self, int idx_layer, int idx_neuron, double inner) nogil:
        if self.activation[idx_layer, idx_neuron] in (1, 2):
            return smoothutils.smooth_logistic1_derivative2(inner, 1.)
        return 1.

    cpdef inline void calculate_values(self) nogil:
        cdef int idx_input, idx_neuron1, idx_neuron2, idx_output, idx_layer
        cdef double input_

        for idx_neuron1 in range(self.nmb_neurons[0]):
            self.neurons[0, idx_neuron1] = \
                self.intercepts_hidden[0, idx_neuron1]
            for idx_input in range(self.nmb_inputs):
                self.neurons[0, idx_neuron1] += (
                    self.weights_input[idx_input, idx_neuron1] *
                    self.inputs[idx_input])
            if idx_neuron1 < self.nmb_inputs:
                input_ = self.inputs[idx_neuron1]
            else:
                input_ = nan
            self.apply_activationfunction(0, idx_neuron1, input_)

        for idx_layer in range(1, self.nmb_layers):
            for idx_neuron1 in range(self.nmb_neurons[idx_layer]):
                self.neurons[idx_layer, idx_neuron1] = \
                    self.intercepts_hidden[idx_layer, idx_neuron1]
                for idx_neuron2 in range(self.nmb_neurons[idx_layer-1]):
                    self.neurons[idx_layer, idx_neuron1] += (
                        self.weights_hidden[idx_layer-1, idx_neuron2, idx_neuron1] *
                        self.neurons[idx_layer-1, idx_neuron2]
                    )
                if idx_neuron1 < self.nmb_neurons[idx_layer-1]:
                    input_ = self.neurons[idx_layer-1, idx_neuron1]
                else:
                    input_ = nan
                self.apply_activationfunction(idx_layer, idx_neuron1, input_)

        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = self.intercepts_output[idx_output]
            for idx_neuron2 in range(self.nmb_neurons[self.nmb_layers-1]):
                self.outputs[idx_output] += (
                    self.weights_output[idx_neuron2, idx_output] *
                    self.neurons[self.nmb_layers-1, idx_neuron2]
                )


    cpdef inline void calculate_derivatives(self, int idx_input) nogil:
        cdef int idx_neuron1, idx_neuron2, idx_input_, idx_output, idx_layer
        cdef double weight, input_
        cdef double der1   # outer derivative
        cdef double der2   # inner derivative

        for idx_neuron1 in range(self.nmb_neurons[0]):
            input_ = self.intercepts_hidden[0, idx_neuron1]
            for idx_input_ in range(self.nmb_inputs):
                input_ += (self.weights_input[idx_input_, idx_neuron1] *
                         self.inputs[idx_input_])
            der1 = self.apply_derivativefunction(0, idx_neuron1, input_)
            der2 = self.weights_input[idx_input, idx_neuron1]
            self.neuron_derivatives[0, idx_neuron1] = der1 * der2
            if self.activation[0, idx_neuron1] == 2:
                if idx_neuron1 < self.nmb_inputs:
                    input_ = self.inputs[idx_neuron1]
                else:
                    input_ = nan
                self.neuron_derivatives[0, idx_neuron1] *= input_
                if idx_neuron1 == idx_input:
                    self.neuron_derivatives[0, idx_neuron1] += \
                        self.neurons[0, idx_neuron1] / input_

        for idx_layer in range(1, self.nmb_layers):
            for idx_neuron1 in range(self.nmb_neurons[idx_layer]):
                input_ = self.intercepts_hidden[idx_layer, idx_neuron1]
                der2 = 0.
                for idx_neuron2 in range(self.nmb_neurons[idx_layer-1]):
                    weight = self.weights_hidden[
                        idx_layer-1, idx_neuron2, idx_neuron1]
                    input_ += weight * self.neurons[idx_layer-1, idx_neuron2]
                    der2 += weight * self.neuron_derivatives[
                        idx_layer-1, idx_neuron2]
                der1 = self.apply_derivativefunction(idx_layer, idx_neuron1, input_)
                self.neuron_derivatives[idx_layer, idx_neuron1] = der1 * der2
                if self.activation[idx_layer, idx_neuron1] == 2:
                    if idx_neuron1 < self.nmb_neurons[idx_layer-1]:
                        input_ = self.neurons[idx_layer-1, idx_neuron1]
                    else:
                        input_ = nan
                    self.neuron_derivatives[idx_layer, idx_neuron1] *= input_
                    self.neuron_derivatives[idx_layer, idx_neuron1] += (
                        self.neurons[idx_layer, idx_neuron1] / input_ *
                        self.neuron_derivatives[idx_layer-1, idx_neuron1]
                    )

        for idx_output in range(self.nmb_outputs):
            der1 = 1.
            der2 = 0.
            for idx_neuron2 in range(self.nmb_neurons[self.nmb_layers-1]):
                der2 += (
                    self.weights_output[idx_neuron2, idx_output] *
                    self.neuron_derivatives[self.nmb_layers-1, idx_neuron2])
            self.output_derivatives[idx_output] = der1 * der2


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

    cpdef inline void calculate_values(self, int idx_season) nogil:
        cdef int idx_ann, idx_input, idx_output
        cdef double ratio, frac
        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = 0.
        for idx_ann in range(self.nmb_anns):
            ratio = self.ratios[idx_season, idx_ann]
            if ratio > 0.:
                for idx_input in range(self.nmb_inputs):
                     (<ANN>self.canns[idx_ann]).inputs[idx_input] = self.inputs[idx_input]
                (<ANN>self.canns[idx_ann]).calculate_values()
                for idx_output in range(self.nmb_outputs):
                    frac = ratio*(<ANN>self.canns[idx_ann]).outputs[idx_output]
                    self.outputs[idx_output] += frac


