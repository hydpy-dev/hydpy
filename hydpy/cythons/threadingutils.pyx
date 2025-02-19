
from typing import Sequence, TYPE_CHECKING
if TYPE_CHECKING:
    from hydpy.core.modeltools import Model
    from hydpy.core.typingtools import BoundMethod

from cpython cimport PyObject
from libc.stdlib cimport free, malloc
cimport cython
from cython.parallel import prange
from hydpy.cythons.autogen.interfaceutils cimport BaseInterface

cdef class SimpleSimulator:

    def __init__(self, models: Sequence[Model]) -> None:
        self.nmb_models = len(models)
        free(self.models)
        size = self.nmb_models * cython.sizeof(cython.pointer(PyObject))
        self.models = <PyObject**>malloc(size)
        for i, model in enumerate(models):
            self.models[i] = <PyObject*>model.cymodel

    cpdef void simulate(self, int idx_start, int idx_end):
        cdef int nmb_models = self.nmb_models
        for i in range(idx_start, idx_end):
            for j in range(nmb_models):
                (<BaseInterface>self.models[j]).simulate(i)


cdef class Simulator:

    def __init__(
    self,
    premethods: Sequence[BoundMethod],
    models: Sequence[Model],
    breaks: Sequence[int],
    parallel_layers: int,
    postmethods: Sequence[BoundMethod],
    schedule: str,
    threads: int,
    chunksize: int,
    ) -> None:
        self.premethods = premethods
        free(self.models)
        size = len(models) * cython.sizeof(cython.pointer(PyObject))
        self.models = <PyObject**>malloc(size)
        for i, model in enumerate(models):
            self.models[i] = <PyObject*>model.cymodel
        self.breaks = breaks
        self.layers = len(breaks) - 1
        self.parallel_layers = min(max(parallel_layers, 0), self.layers)
        self.postmethods = postmethods
        self.schedule = schedule
        self.threads = threads
        self.chunksize = chunksize

    cpdef void simulate(self, int idx_start, int idx_end):
        if self.schedule == "dynamic":
            self._simulate_dynamic(idx_start, idx_end)
        else:
            self._simulate_static(idx_start, idx_end)

    cdef void _simulate_dynamic(self, int idx_start, int idx_end):

        cdef int threads = self.threads
        cdef int chunksize = self.chunksize
        cdef int layers = self.layers
        cdef int parallel_layers = self.parallel_layers
        cdef int i, j, l, b0, b1

        for i in range(idx_start, idx_end):
            for premethod in self.premethods:
                premethod(i)
            for l in range(parallel_layers):
                b0 = self.breaks[l]
                b1 = self.breaks[l + 1]
                for j in prange(
                    b0,
                    b1,
                    schedule="dynamic",
                    chunksize=chunksize,
                    num_threads=threads,
                    nogil=True,
                ):
                    (<BaseInterface>self.models[j]).simulate(i)
            b0 = self.breaks[parallel_layers]
            b1 = self.breaks[layers]
            for j in range(b0, b1):
                (<BaseInterface>self.models[j]).simulate(i)
            for postmethod in self.postmethods:
                postmethod(i)


    cdef void _simulate_static(self, int idx_start, int idx_end):

        cdef int threads = self.threads
        cdef int chunksize = self.chunksize
        cdef int layers = self.layers
        cdef int parallel_layers = self.parallel_layers
        cdef int i, j, l, b0, b1

        for i in range(idx_start, idx_end):
            for premethod in self.premethods:
                premethod(i)
            for l in range(parallel_layers):
                b0 = self.breaks[l]
                b1 = self.breaks[l + 1]
                for j in prange(
                    b0,
                    b1,
                    schedule="static",
                    chunksize=chunksize,
                    num_threads=threads,
                    nogil=True,
                ):
                    (<BaseInterface>self.models[j]).simulate(i)
            b0 = self.breaks[parallel_layers]
            b1 = self.breaks[layers]
            for j in range(b0, b1):
                (<BaseInterface>self.models[j]).simulate(i)
            for postmethod in self.postmethods:
                postmethod(i)

    def __dealloc__(self) -> None:
        free(self.models)
