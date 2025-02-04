
from typing import Sequence, TYPE_CHECKING
if TYPE_CHECKING:
    from hydpy.core.modeltools import Model
    from hydpy.core.typingtools import BoundMethod

from cpython cimport PyObject
from libc.stdlib cimport free, malloc
cimport cython
from cython.parallel import prange
from hydpy.cythons.autogen.interfaceutils cimport BaseInterface

cdef class Simulator:

    def __init__(
    self,
    premethods: Sequence[BoundMethod],
    models: Sequence[Model],
    breaks: Sequence[int],
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
        self.postmethods = postmethods
        self.schedule = schedule
        self.threads = threads
        self.chunksize = chunksize

    cpdef void simulate(self, int idx_start, int idx_end):

        cdef int threads = self.threads
        cdef int chunksize = self.chunksize
        cdef int layers = self.layers
        cdef int i, j, l, b0, b1

        if self.schedule == "dynamic":
            for i in range(idx_start, idx_end):
                for premethod in self.premethods:
                    premethod(i)
                with nogil:
                    for l in range(layers):
                        b0 = self.breaks[l]
                        b1 = self.breaks[l + 1]
                        for j in prange(
                            b0,
                            b1,
                            schedule="dynamic",
                            chunksize=chunksize,
                            num_threads=threads,
                        ):
                            (<BaseInterface>self.models[j]).simulate(i)
                for postmethod in self.postmethods:
                    postmethod(i)
        else:
            for i in range(idx_start, idx_end):
                for premethod in self.premethods:
                    premethod(i)
                with nogil:
                    for l in range(layers):
                        b0 = self.breaks[l]
                        b1 = self.breaks[l + 1]
                        for j in prange(
                            b0,
                            b1,
                            schedule="static",
                            chunksize=chunksize,
                            num_threads=threads,
                        ):
                            (<BaseInterface>self.models[j]).simulate(i)
                for postmethod in self.postmethods:
                    postmethod(i)

    def __dealloc__(self) -> None:
        free(self.models)
