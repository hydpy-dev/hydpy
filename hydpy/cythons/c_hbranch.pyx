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
cimport pointer
import pointer
from cpython.mem cimport PyMem_Malloc
from cpython.mem cimport PyMem_Realloc
from cpython.mem cimport PyMem_Free

@cython.final
cdef class ControlParameters(object):
    cdef public double[:] xpoints
    cdef public double[:,:] ypoints
@cython.final
cdef class DerivedParameters(object):
    cdef public int nmbbranches
    cdef public int nmbpoints
@cython.final
cdef class FluxSequences(object):
    cdef public double input
    cdef public int _input_ndim
    cdef public int _input_length
    cdef public bint _input_diskflag
    cdef public str _input_path
    cdef FILE *_input_file
    cdef public bint _input_ramflag
    cdef public double[:] _input_array
    cdef public double[:] outputs
    cdef public int _outputs_ndim
    cdef public int _outputs_length
    cdef public int _outputs_length_0
    cdef public bint _outputs_diskflag
    cdef public str _outputs_path
    cdef FILE *_outputs_file
    cdef public bint _outputs_ramflag
    cdef public double[:,:] _outputs_array
    cpdef openfiles(self, int idx):
        if self._input_diskflag:
            self._input_file = fopen(str(self._input_path), "rb+")
            fseek(self._input_file, idx*8, SEEK_SET)
        if self._outputs_diskflag:
            self._outputs_file = fopen(str(self._outputs_path), "rb+")
            fseek(self._outputs_file, idx*self._outputs_length*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._input_diskflag:
            fclose(self._input_file)
        if self._outputs_diskflag:
            fclose(self._outputs_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._input_diskflag:
            fwrite(&self.input, 8, 1, self._input_file)
        elif self._input_ramflag:
            self._input_array[idx] = self.input
        if self._outputs_diskflag:
            fwrite(&self.outputs[0], 8, self._outputs_length, self._outputs_file)
        elif self._outputs_ramflag:
            for jdx0 in range(self._outputs_length_0):
                self._outputs_array[idx,jdx0] = self.outputs[jdx0]
@cython.final
cdef class OutletSequences(object):
    cdef double **branched
    cdef public int _branched_ndim
    cdef public int _branched_length
    cdef public int _branched_length_0
    cpdef inline alloc(self, name, int length):
        if name == "branched":
            self._branched_length_0 = length
            self.branched = <double**> PyMem_Malloc(length * sizeof(double*))
    cpdef inline dealloc(self):
        PyMem_Free(self.branched)
    cpdef inline setpointer1d(self, str name, pointer.PDouble value, int idx):
        if name == "branched":
            self.branched[idx] = value.p_value
@cython.final
cdef class InletSequences(object):
    cdef double *total
    cdef public int _total_ndim
    cdef public int _total_length
    cpdef inline setpointer0d(self, str name, pointer.PDouble value):
        if name == "total":
            self.total = value.p_value
@cython.final
cdef class Model(object):
    cdef public ControlParameters control
    cdef public DerivedParameters derived
    cdef public FluxSequences fluxes
    cdef public OutletSequences outlets
    cdef public InletSequences inlets
    cpdef inline void doit(self, int idx):
        self.updateinlets(idx)
        self.run(idx)
        self.updateoutlets(idx)
        self.savedata(idx)
    cpdef inline void openfiles(self, int idx):
        self.fluxes.openfiles(idx)
    cpdef inline void closefiles(self):
        self.fluxes.closefiles()
    cpdef inline void savedata(self, int idx):
        self.fluxes.savedata(idx)
    cpdef inline void updateinlets(self, int idx):
        self.fluxes.input = self.inlets.total[0]
    cpdef inline void updateoutlets(self, int idx):
        cdef int bdx
        for bdx in range(self.derived.nmbbranches):
            self.outlets.branched[bdx][0] += self.fluxes.outputs[bdx]
    cpdef inline void run(self, int idx):
        cdef int pdx, bdx
        for pdx in range(1, self.derived.nmbpoints):
            if self.control.xpoints[pdx] > self.fluxes.input:
                break
        for bdx in range(self.derived.nmbbranches):
            self.fluxes.outputs[bdx] = (
                (self.fluxes.input-self.control.xpoints[pdx-1]) *
                (self.control.ypoints[bdx, pdx]-self.control.ypoints[bdx, pdx-1]) /
                (self.control.xpoints[pdx]-self.control.xpoints[pdx-1]) +
                self.control.ypoints[bdx, pdx-1])
