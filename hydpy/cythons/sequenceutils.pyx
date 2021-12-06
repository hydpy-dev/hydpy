# -*- coding: utf-8 -*-
# !python
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: cdivision=True
"""This Cython module implements the performance-critical features of
the Python module |sequencetools| that are not covered by the usual
model cythonization.
"""
import cython
cimport cython
import numpy
cimport numpy
from libc.math cimport isnan
from libc.stdio cimport *
from libc.stdlib cimport *
from hydpy.cythons.autogen cimport pointerutils

@cython.final
cdef class FastAccessNodeSequence:
    """Cython implementation of class |sequencetools.FastAccessNodeSequence|
    of module |sequencetools|."""

    cpdef void load_simdata(self, numpy.int32_t idx):
        """Load the next sim sequence value (of the given index)."""
        if self._sim_diskflag_reading:
            self.sim.value = self._sim_ncarray[0]
        elif self._sim_ramflag:
            self.sim.value = self._sim_array[idx]

    cpdef void save_simdata(self, numpy.int32_t idx):
        """Save the last sim sequence value (of the given index)."""
        if self._sim_diskflag_writing:
            self._sim_ncarray[0] = self.sim.value
        if self._sim_ramflag:
            self._sim_array[idx] = self.sim.value

    cpdef void load_obsdata(self, numpy.int32_t idx):
        """Load the next obs sequence value (of the given index)."""
        if self._obs_diskflag_reading:
            self.obs.value = self._obs_ncarray[0]
        if self._obs_ramflag:
            self.obs.value = self._obs_array[idx]

    cpdef void save_obsdata(self, numpy.int32_t idx):
        """Save the last obs sequence value (of the given index)."""
        if self._obs_diskflag_writing:
            self._obs_ncarray[0] = self.obs.value
        if self._obs_ramflag:
            self._obs_array[idx] = self.obs.value

    cpdef void load_data(self, numpy.int32_t idx):
        """Call both method `load_simdata` and method `load_obsdata`."""
        if self._sim_diskflag_reading:
            self.sim.value = self._sim_ncarray[0]
        if self._sim_ramflag:
            self.sim.value = self._sim_array[idx]
        if self._obs_diskflag_reading:
            self.obs.value = self._obs_ncarray[0]
        if self._obs_ramflag:
            self.obs.value = self._obs_array[idx]

    cpdef void save_data(self, numpy.int32_t idx):
        """Alias for method `save_simdata`."""
        if self._sim_diskflag_writing:
            self._sim_ncarray[0] = self.sim.value
        if self._sim_ramflag:
            self._sim_array[idx] = self.sim.value
        if self._obs_diskflag_writing:
            self._obs_ncarray[0] = self.obs.value
        if self._obs_ramflag:
            self._obs_array[idx] = self.obs.value

    cpdef void reset(self, numpy.int32_t idx):
        """Reset the actual value of the simulation sequence to zero."""
        self.sim.value = 0.

    cpdef void fill_obsdata(self, numpy.int32_t idx):
        """Use the current sim value for the current obs value if obs is
        `nan`."""
        if isnan(self.obs.value):
            self.obs.value = self.sim.value
