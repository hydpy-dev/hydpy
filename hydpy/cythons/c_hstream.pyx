#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
import numpy
cimport numpy
from libc.math cimport exp
from libc.stdio cimport *
from libc.stdlib cimport *
import cython
from cpython.mem cimport PyMem_Malloc
from cpython.mem cimport PyMem_Realloc
from cpython.mem cimport PyMem_Free
from hydpy.cythons cimport pointer
from hydpy.cythons import pointer

@cython.final
cdef class ControlParameters(object):
    cdef public double lag
    cdef public double damp
@cython.final
cdef class DerivedParameters(object):
    cdef public numpy.int32_t nmbsegments
    cdef public double c1
    cdef public double c2
    cdef public double c3
@cython.final
cdef class StateSequences(object):
    cdef public double[:] qjoints
    cdef public int _qjoints_ndim
    cdef public int _qjoints_length
    cdef public int _qjoints_length_0
    cdef public bint _qjoints_diskflag
    cdef public str _qjoints_path
    cdef FILE *_qjoints_file
    cdef public bint _qjoints_ramflag
    cdef public double[:,:] _qjoints_array
    cpdef openfiles(self, int idx):
        if self._qjoints_diskflag:
            self._qjoints_file = fopen(str(self._qjoints_path), "rb+")
            fseek(self._qjoints_file, idx*self._qjoints_length*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._qjoints_diskflag:
            fclose(self._qjoints_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._qjoints_diskflag:
            fwrite(&self.qjoints[0], 8, self._qjoints_length, self._qjoints_file)
        elif self._qjoints_ramflag:
            for jdx0 in range(self._qjoints_length_0):
                self._qjoints_array[idx,jdx0] = self.qjoints[jdx0]
@cython.final
cdef class OutletSequences(object):
    cdef double *q
    cdef public int _q_ndim
    cdef public int _q_length
    cpdef inline setpointer0d(self, str name, pointer.PDouble value):
        if name == "q":
            self.q = value.p_value
@cython.final
cdef class InletSequences(object):
    cdef double *q
    cdef public int _q_ndim
    cdef public int _q_length
    cpdef inline setpointer0d(self, str name, pointer.PDouble value):
        if name == "q":
            self.q = value.p_value
@cython.final
cdef class Model(object):
    cdef public ControlParameters control
    cdef public DerivedParameters derived
    cdef public StateSequences states
    cdef public OutletSequences outlets
    cdef public InletSequences inlets
    cdef public StateSequences old_states
    cdef public StateSequences new_states
    cpdef inline void doit(self, int idx):
        self.updateinlets(idx)
        self.run(idx)
        self.updateoutlets(idx)
        self.new2old()
        self.savedata(idx)
    cpdef inline void openfiles(self, int idx):
        self.states.openfiles(idx)
    cpdef inline void closefiles(self):
        self.states.closefiles()
    cpdef inline void savedata(self, int idx):
        self.states.savedata(idx)
    cpdef inline void new2old(self):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        for jdx0 in range(self.states._qjoints_length_0):
            self.old_states.qjoints[jdx0] = self.new_states.qjoints[jdx0]
    cpdef inline void updateinlets(self, int idx):
        self.states.qjoints[0] = self.inlets.q[0]
    cpdef inline void updateoutlets(self, int idx):
        self.outlets.q[0] += self.states.qjoints[self.derived.nmbsegments]
    cpdef inline void run(self, int idx):
        cdef int j
        for j in range(self.derived.nmbsegments):
            self.new_states.qjoints[j+1] = (self.derived.c1*self.new_states.qjoints[j] +
                                self.derived.c2*self.old_states.qjoints[j] +
                                self.derived.c3*self.old_states.qjoints[j+1])
