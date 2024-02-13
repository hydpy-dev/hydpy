"""This Cython module implements the performance-critical methods of the
Python module |interptools|.
"""

import numpy

cimport cython
from libc.math cimport NAN as nan
from libc.stdlib cimport malloc, free

from hydpy.cythons.autogen cimport annutils
from hydpy.cythons.autogen cimport ppolyutils

cdef int _ANN = 0
cdef int _PPOLY = 1


def _type2number():
    from hydpy.auxs.anntools import ANN
    from hydpy.auxs.ppolytools import PPoly
    return {ANN: _ANN, PPoly: _PPOLY}


@cython.final
cdef class SimpleInterpolator:

    def __init__(self, algorithm):
        self.nmb_inputs = algorithm.nmb_inputs
        self.nmb_outputs = algorithm.nmb_outputs
        self.inputs = numpy.zeros(self.nmb_inputs, dtype=float)
        self.outputs = numpy.zeros(self.nmb_outputs, dtype=float)
        self.output_derivatives = numpy.zeros(self.nmb_outputs, dtype=float)
        t2n = _type2number()
        self.algorithm_type = _type2number()[type(algorithm)]
        self.algorithm = <PyObject*>algorithm._calgorithm

    cpdef inline void calculate_values(self) noexcept nogil:
        cdef int idx
        if self.algorithm_type == _ANN:
            for idx in range(self.nmb_inputs):
                 (<annutils.ANN>self.algorithm).inputs[idx] = self.inputs[idx]
            (<annutils.ANN>self.algorithm).calculate_values()
            for idx in range(self.nmb_outputs):
                self.outputs[idx] = (<annutils.ANN>self.algorithm).outputs[idx]
        elif self.algorithm_type == _PPOLY:
            for idx in range(self.nmb_inputs):
                 (<ppolyutils.PPoly>self.algorithm).inputs[idx] = self.inputs[idx]
            (<ppolyutils.PPoly>self.algorithm).calculate_values()
            for idx in range(self.nmb_outputs):
                self.outputs[idx] = (<ppolyutils.PPoly>self.algorithm).outputs[idx]

    cpdef inline void calculate_derivatives(self, int idx_input) noexcept nogil:
        cdef int idx_output
        if self.algorithm_type == _ANN:
            (<annutils.ANN>self.algorithm).calculate_derivatives(idx_input)
            for idx_output in range(self.nmb_outputs):
                self.output_derivatives[idx_output] = (<annutils.ANN>self.algorithm).output_derivatives[idx_output]
        elif self.algorithm_type == _PPOLY:
            (<ppolyutils.PPoly>self.algorithm).calculate_derivatives(idx_input)
            for idx_output in range(self.nmb_outputs):
                self.output_derivatives[idx_output] = (<ppolyutils.PPoly>self.algorithm).output_derivatives[idx_output]


@cython.final
cdef class SeasonalInterpolator:

    def __init__(self, algorithms):
        self.nmb_inputs = len(algorithms[0].inputs)
        self.nmb_outputs = len(algorithms[0].outputs)
        self.nmb_algorithms = len(algorithms)
        self.inputs = numpy.zeros(self.nmb_inputs, dtype=float)
        self.outputs = numpy.zeros(self.nmb_outputs, dtype=float)
        t2n = _type2number()
        self.algorithm_types = numpy.array([t2n[type(alg)] for alg in algorithms])
        self.algorithms = <PyObject **>malloc(
            self.nmb_algorithms * cython.sizeof(cython.pointer(PyObject))
        )
        for idx, algorithm in enumerate(algorithms):
            self.algorithms[idx] = <PyObject*>algorithm._calgorithm

    def __dealloc__(self):
        free(self.algorithms)

    cpdef inline void calculate_values(self, int idx_season) noexcept nogil:
        cdef int idx_algorithm, idx_input, idx_output
        cdef double ratio, frac
        for idx_output in range(self.nmb_outputs):
            self.outputs[idx_output] = 0.0
        for idx_algorithm in range(self.nmb_algorithms):
            ratio = self.ratios[idx_season, idx_algorithm]
            if ratio > 0.0:
                if self.algorithm_types[idx_algorithm] == _ANN:
                    for idx_input in range(self.nmb_inputs):
                         (<annutils.ANN>self.algorithms[idx_algorithm]).inputs[idx_input] = self.inputs[idx_input]
                    (<annutils.ANN>self.algorithms[idx_algorithm]).calculate_values()
                    for idx_output in range(self.nmb_outputs):
                        frac = ratio*(<annutils.ANN>self.algorithms[idx_algorithm]).outputs[idx_output]
                        self.outputs[idx_output] += frac
                if self.algorithm_types[idx_algorithm] == _PPOLY:
                    for idx_input in range(self.nmb_inputs):
                         (<ppolyutils.PPoly>self.algorithms[idx_algorithm]).inputs[idx_input] = self.inputs[idx_input]
                    (<ppolyutils.PPoly>self.algorithms[idx_algorithm]).calculate_values()
                    for idx_output in range(self.nmb_outputs):
                        frac = ratio * (<ppolyutils.PPoly>self.algorithms[idx_algorithm]).outputs[idx_output]
                        self.outputs[idx_output] += frac