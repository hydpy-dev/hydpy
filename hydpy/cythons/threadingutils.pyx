
from typing import Sequence, TYPE_CHECKING
if TYPE_CHECKING:
    from hydpy.core.modeltools import Model

from cpython cimport PyObject
from libc.stdlib cimport free, malloc
cimport cython
from cython.parallel import prange
from hydpy.cythons.autogen.interfaceutils cimport BaseInterface

cdef class Chunk:

    def __init__(self, models: Sequence[Model]) -> None:
        free(self.models)
        self.number = len(models)
        size = self.number * cython.sizeof(cython.pointer(PyObject))
        self.models = <PyObject**>malloc(size)
        for i, model in enumerate(models):
            self.models[i] = <PyObject*>model.cymodel

    cpdef void simulate(self, int idx):
        cdef int j
        with nogil:
            for j in range(self.number):
                (<BaseInterface>self.models[j]).simulate(idx)

    cpdef void simulate_period(self, int idx_start, int idx_end):
        cdef int j
        for j in prange(self.number, nogil=True):
            (<BaseInterface>self.models[j]).simulate_period(idx_start, idx_end)

    cpdef void simulate_period_stepwise(self, int idx_start, int idx_end):
        cdef int i, j
        with nogil:
            for i in range(idx_start, idx_end):
                for j in prange(self.number):
                    (<BaseInterface>self.models[j]).simulate(i)

    def __dealloc__(self) -> None:
        free(self.models)
