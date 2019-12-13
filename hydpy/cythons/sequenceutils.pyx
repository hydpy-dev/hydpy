# -*- coding: utf-8 -*-
#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This Cython module implements the performance-critical features of
the Python module |sequencetools| that are not covered by the usual
model cythonization.
"""
import cython
cimport cython
import numpy
cimport numpy
from libc.stdio cimport *
from libc.stdlib cimport *
from hydpy.cythons cimport pointerutils

@cython.final
cdef class FastAccessNodeSequence:
    """Cython implementation of class |sequencetools.FastAccessNodeSequence|
    of module |sequencetools|."""

    cpdef void open_files(self, int idx):
        """Open all files with an activated disk flag."""
        if self._sim_diskflag:
            self._sim_file = fopen(str(self._sim_path).encode(), "rb+")
            fseek(self._sim_file, idx*8, SEEK_SET)
        if self._obs_diskflag:
            self._obs_file = fopen(str(self._obs_path).encode(), "rb+")
            fseek(self._obs_file, idx*8, SEEK_SET)

    cpdef void close_files(self):
        """Close all files with an activated disk flag."""
        if self._sim_diskflag:
            fclose(self._sim_file)
        if self._obs_diskflag:
            fclose(self._obs_file)

    cpdef void load_simdata(self, int idx):
        """Load the next sim sequence value (of the given index)."""
        if self._sim_ramflag:
            self.sim.value = self._sim_array[idx]
        elif self._sim_diskflag:
            fread(&self.sim.value, 8, 1, self._sim_file)

    cpdef void save_simdata(self, idx: int):
        """Save the last sim sequence value (of the given index)."""
        if self._sim_ramflag:
            self._sim_array[idx] = self.sim.value
        elif self._sim_diskflag:
            fwrite(&self.sim.value, 8, 1, self._sim_file)

    cpdef void load_obsdata(self, int idx):
        """Load the next obs sequence value (of the given index)."""
        if self._obs_ramflag:
            self.obs.value = self._obs_array[idx]
        elif self._obs_diskflag:
            fread(&self.obs.value, 8, 1, self._obs_file)

    cpdef void reset(self, int idx):
        """Reset the actual value of the simulation sequence to zero."""
        self.sim.value = 0.
