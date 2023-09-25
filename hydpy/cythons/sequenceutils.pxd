"""This module defines the Cython declarations related to module |sequencetools|.
"""
# import...
import numpy
cimport numpy
from hydpy.cythons.autogen cimport pointerutils

cdef class FastAccessNodeSequence:

    cdef public pointerutils.Double sim
    cdef public pointerutils.Double obs
    cdef public numpy.int32_t _sim_ndim
    cdef public numpy.int32_t _obs_ndim
    cdef public numpy.int32_t _sim_length
    cdef public numpy.int32_t _obs_length
    cdef public bint _sim_ramflag
    cdef public bint _obs_ramflag
    cdef public double[:] _sim_array
    cdef public double[:] _obs_array
    cdef public bint _sim_diskflag_reading
    cdef public bint _sim_diskflag_writing
    cdef public bint _obs_diskflag_reading
    cdef public bint _obs_diskflag_writing
    cdef public double[:] _sim_ncarray
    cdef public double[:] _obs_ncarray
    cdef public bint _reset_obsdata

    cpdef void load_simdata(self, numpy.int32_t idx)
    cpdef void save_simdata(self, numpy.int32_t idx)
    cpdef void load_obsdata(self, numpy.int32_t idx)
    cpdef void save_obsdata(self, numpy.int32_t idx)
    cpdef void load_data(self, numpy.int32_t idx)
    cpdef void save_data(self, numpy.int32_t idx)
    cpdef void reset(self, numpy.int32_t idx)
    cpdef void fill_obsdata(self, numpy.int32_t idx)
    cpdef void reset_obsdata(self, numpy.int32_t idx)
