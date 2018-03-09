# -*- coding: utf-8 -*-
"""This module defines the Cython declarations related to module
:mod:`~hydpy.cythons.configtools`.
"""

cdef class Config(object):

    cdef public double _abs_error_max
    cdef public double _rel_dt_min
