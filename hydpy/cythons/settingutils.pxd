"""This module defines the Cython declarations related to module |settingutils|."""

cimport numpy


cpdef enum:
    HISTORICAL = 0
    FORECAST = 1


cdef class RunSettings:

    cdef readonly int simulationmode
