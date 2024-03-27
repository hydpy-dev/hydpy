# -*- coding: utf-8 -*-
"""This module defines the Cython declarations related to module
|smoothtools|.
"""

cpdef double smooth_logistic1(double value, double parameter) noexcept nogil
cpdef double smooth_logistic2(double value, double parameter) noexcept nogil
cpdef double smooth_logistic1_derivative2(
    double value, double parameter) noexcept nogil
cpdef double smooth_logistic2_derivative1(
    double value, double parameter) noexcept nogil
cpdef double smooth_logistic2_derivative2(
    double value, double parameter) noexcept nogil
cpdef double smooth_logistic3(double value, double parameter) noexcept nogil
cpdef double smooth_max1(
    double x_value, double y_value, double parameter) noexcept nogil
cpdef double smooth_min1(
    double x_value, double y_value, double parameter) noexcept nogil
cpdef double smooth_max2(
    double x_value, double y_value, double z_value, double parameter) noexcept nogil
cpdef double smooth_min2(
    double x_value, double y_value, double z_value, double parameter) noexcept nogil
cpdef double filter_norm(double value, double mean, double std) noexcept nogil
