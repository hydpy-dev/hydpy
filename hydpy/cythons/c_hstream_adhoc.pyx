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

@cython.final
cdef class Control(object):

    cdef public double DAMP
    cdef public double LAG
    cdef public double[:] Qbranch
    cdef public double[:] Qtotal


@cython.final
cdef class Disagg(object):

    pass


@cython.final
cdef class Dynamic(object):

    cdef public double c1
    cdef public double c2
    cdef public double c3
    cdef public int intLAG
    cdef public int nInterp


@cython.final
cdef class Static_(object):

    pass


@cython.final
cdef class Solver(object):

    pass




@cython.final
cdef class InputQuickaccess(object):

    pass


    cdef inline openfiles(self, int idx):
        pass

    cdef inline closefiles(self):
        pass

    cdef inline loaddata(self, int idx):
        cdef int j


@cython.final
cdef class LogQuickaccess(object):

    pass


    cdef inline openfiles(self, int idx):
        pass

    cdef inline closefiles(self):
        pass

    cdef inline savedata(self, int idx):
        cdef int j


@cython.final
cdef class DownstreamQuickaccess(object):

    cdef double *Q
    cdef public bint _diskflag_Q
    cdef public str _path_Q
    cdef FILE *_file_Q
    cdef public bint _ramflag_Q
    cdef public double[:] _array_Q


    cpdef inline setpointer(self, str name, pointer.PDouble value):
        if name == "Q":
            self.Q = value.p_value


@cython.final
cdef class UpstreamQuickaccess(object):

    cdef double *Q
    cdef public bint _diskflag_Q
    cdef public str _path_Q
    cdef FILE *_file_Q
    cdef public bint _ramflag_Q
    cdef public double[:] _array_Q


    cpdef inline setpointer(self, str name, pointer.PDouble value):
        if name == "Q":
            self.Q = value.p_value


@cython.final
cdef class StateQuickaccess(object):

    cdef public double[:] Q
    cdef public bint _diskflag_Q
    cdef public str _path_Q
    cdef FILE *_file_Q
    cdef public bint _ramflag_Q
    cdef public double[:,:] _array_Q
    cdef public int _length_Q


    cdef inline openfiles(self, int idx):
        if self._diskflag_Q:
            self._file_Q = fopen(str(self._path_Q), "rb+")
            fseek(self._file_Q, 8*idx*self._length_Q, SEEK_SET)

    cdef inline closefiles(self):
        if self._diskflag_Q:
            fclose(self._file_Q)

    cdef inline savedata(self, int idx):
        cdef int j
        if self._diskflag_Q:
            fwrite(&self.Q[0], 8, self._length_Q, self._file_Q)
        elif self._ramflag_Q:
            for j in range(self._length_Q):
                self._array_Q[idx,j]= self.Q[j]


@cython.final
cdef class AideQuickaccess(object):

    pass


    cdef inline openfiles(self, int idx):
        pass

    cdef inline closefiles(self):
        pass

    cdef inline savedata(self, int idx):
        cdef int j


@cython.final
cdef class FluxeQuickaccess(object):

    cdef public double Qinput
    cdef public bint _diskflag_Qinput
    cdef public str _path_Qinput
    cdef FILE *_file_Qinput
    cdef public bint _ramflag_Qinput
    cdef public double[:] _array_Qinput


    cdef inline openfiles(self, int idx):
        if self._diskflag_Qinput:
            self._file_Qinput = fopen(str(self._path_Qinput), "rb+")
            fseek(self._file_Qinput, 8*idx, SEEK_SET)

    cdef inline closefiles(self):
        if self._diskflag_Qinput:
            fclose(self._file_Qinput)

    cdef inline savedata(self, int idx):
        cdef int j
        if self._diskflag_Qinput:
            fwrite(&self.Qinput, 8, 1, self._file_Qinput)
        elif self._ramflag_Qinput:
            self._array_Qinput[idx] = self.Qinput
@cython.final
cdef class Model:

    cdef public Control control
    cdef public Static_ static_
    cdef public Dynamic dynamic
    cdef public Solver solver
    cdef public Disagg disagg
    cdef public InputQuickaccess inputs
    cdef public FluxeQuickaccess fluxes
    cdef public StateQuickaccess new
    cdef public StateQuickaccess old
    cdef public AideQuickaccess aides
    cdef public LogQuickaccess logs
    cdef public DownstreamQuickaccess downstream
    cdef public UpstreamQuickaccess upstream


    cpdef inline void openfiles(self, int idx):
        self.fluxes.openfiles(idx)
        self.old.openfiles(idx)

    cpdef inline void closefiles(self):
        self.fluxes.closefiles()
        self.old.closefiles()

    cdef inline void loaddata(self, int idx):
        self.inputs.loaddata(idx)

    cdef inline void savedata(self, int idx):
        self.fluxes.savedata(idx)
        self.old.savedata(idx)

    cdef inline void new2old(self):
        cdef int i
        for i in range(self.old._length_Q):
            self.old.Q[i] = self.new.Q[i]

    cpdef inline void doit(self, int idx):
        self.loaddata(idx)
        self.getinputs(idx)
        self.run(idx)
        self.addoutputs(idx)
        self.new2old()
        self.savedata(idx)

    cdef inline void run(self, int idx):
        

        self.adhoc(idx)

    cdef inline void getinputs(self, int idx):
        self.fluxes.Qinput = self.upstream.Q[0] 

    cdef inline void addoutputs(self, int idx):
        self.downstream.Q[0] += self.new.Q[self.dynamic.intLAG] 

    cdef void adhoc(self, int i):
        cdef int j
        

        # If necessary, perform linear interpolation type of branching.
        if self.dynamic.nInterp == 0:
            self.new.Q[0] = self.fluxes.Qinput
        else:
            for j in range(1, self.dynamic.nInterp+1):
                if self.control.Qtotal[j] > self.fluxes.Qinput:
                    break
            self.new.Q[0] = ((self.fluxes.Qinput-self.control.Qtotal[j-1]) * 
                        (self.control.Qbranch[j]-self.control.Qbranch[j-1]) /
                        (self.control.Qtotal[j]-self.control.Qtotal[j-1])) + self.control.Qbranch[j-1]                      
        # go through all river segments
        for j in range(self.dynamic.intLAG):
            # apply muskingum formula
            self.new.Q[j+1] = self.dynamic.c1*self.new.Q[j] + self.dynamic.c2*self.old.Q[j] + self.dynamic.c3*self.old.Q[j+1]  
