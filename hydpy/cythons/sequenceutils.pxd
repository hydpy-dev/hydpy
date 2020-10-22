# -*- coding: utf-8 -*-
# !python
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: cdivision=True
"""This module defines the Cython declarations related to module
|sequencetools|.
"""
# import...
import numpy
cimport numpy
from libc.stdio cimport *
from libc.stdlib cimport *
from hydpy.cythons.autogen cimport pointerutils

cdef class FastAccessNodeSequence:

    cdef public pointerutils.Double sim
    cdef public pointerutils.Double obs
    cdef public numpy.int32_t _sim_ndim
    cdef public numpy.int32_t _obs_ndim
    cdef public numpy.int32_t _sim_length
    cdef public numpy.int32_t _obs_length
    cdef public double[:] _sim_array
    cdef public double[:] _obs_array
    cdef public bint _sim_ramflag
    cdef public bint _obs_ramflag
    cdef public bint _sim_diskflag
    cdef public bint _obs_diskflag
    cdef public str _sim_path
    cdef public str _obs_path
    cdef FILE *_sim_file
    cdef FILE *_obs_file

    cpdef void open_files(self, numpy.int32_t idx)
    cpdef void close_files(self)
    cpdef void load_simdata(self, numpy.int32_t idx)
    cpdef void save_simdata(self, numpy.int32_t idx)
    cpdef void load_obsdata(self, numpy.int32_t idx)
    cpdef void load_data(self, numpy.int32_t idx)
    cpdef void save_data(self, numpy.int32_t idx)
    cpdef void reset(self, numpy.int32_t idx)
    cpdef void fill_obsdata(self, numpy.int32_t idx)
