# -*- coding: utf-8 -*-
"""This module defines the Cython declarations related to module
:mod:`~hydpy.auxs.smoothtools`.
"""

cpdef inline double smooth_logistic1(double value, double parameter) nogil
cpdef inline double smooth_logistic2(double value, double parameter) nogil
cpdef inline double smooth_logistic2_derivative(double value,
                                                double parameter) nogil
cpdef inline double smooth_logistic3(double value, double parameter) nogil