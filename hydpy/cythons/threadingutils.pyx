
from typing import Sequence, TYPE_CHECKING
if TYPE_CHECKING:
    from hydpy.core.modeltools import Model

from cpython cimport PyObject
from libc.stdlib cimport free, malloc
cimport cython
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

    def __dealloc__(self) -> None:
        free(self.models)
