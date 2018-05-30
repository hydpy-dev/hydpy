#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This Cython module implements the performance-critical functions of the
Python module |smoothtools|.
"""

import cython
from libc.math cimport exp, log


cpdef double MAX_LOG_FLOAT = 700.0
"""The natural logarithm of the highest possible float value.

Values below and slightly above can be assigned to the exponential function:

>>> from numpy import exp, log
>>> from hydpy import round_
>>> round_(log(exp(700.0)))
700.0

But values clearly exceeding `700` result in a numerical overflow:

>>> x = log(exp(720.0))
Traceback (most recent call last):
...
RuntimeWarning: overflow encountered in exp
>>> x
inf

The exact value of might differ between different systems.  So an automated
estimation of this value would be advisable.  (On Windows using 64 bit Python,
even 709.0 works.  But a not too small safety factor seemed preferable.)
"""

cpdef inline double _max(double x_value, double y_value) nogil:
    """The usual (discontinuous) maximum function.

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils._max(1.5, 2.5))
    2.5
    >>> round_(smoothutils._max(-1.5, -2.5))
    -1.5
    >>> round_(smoothutils._max(0.0, 0.0))
    0.0
    """
    if x_value > y_value:
        return x_value
    else:
        return y_value


cpdef inline double _min(double x_value, double y_value) nogil:
    """The usual (discontinuous) minimum function.

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils._min(1.5, 2.5))
    1.5
    >>> round_(smoothutils._min(-1.5, -2.5))
    -2.5
    >>> round_(smoothutils._min(0.0, 0.0))
    0.0
    """
    if x_value < y_value:
        return x_value
    else:
        return y_value


cpdef inline double smooth_logistic1(double value, double parameter) nogil:
    """Smoothing kernel based on the logistic function.

    :math:`f_{log1}(x, c) = 1-\\frac{1}{1+exp(x/c)}`

    The following example shows the typical shape of the logistic function
    for four different smoothing parameters:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value, par=10.0,  par=1.0,  par=0.1,  par=0.0')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([10.0, 1.0, 0.1, 0.0]):
    ...         round_(smoothutils.smooth_logistic1(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value, par=10.0,  par=1.0,  par=0.1,  par=0.0
       -5, 0.377541, 0.006693, 0.000000, 0.000000
       -4, 0.401312, 0.017986, 0.000000, 0.000000
       -3, 0.425557, 0.047426, 0.000000, 0.000000
       -2, 0.450166, 0.119203, 0.000000, 0.000000
       -1, 0.475021, 0.268941, 0.000045, 0.000000
        0, 0.500000, 0.500000, 0.500000, 0.500000
        1, 0.524979, 0.731059, 0.999955, 1.000000
        2, 0.549834, 0.880797, 1.000000, 1.000000
        3, 0.574443, 0.952574, 1.000000, 1.000000
        4, 0.598688, 0.982014, 1.000000, 1.000000
        5, 0.622459, 0.993307, 1.000000, 1.000000

    With the highest value of the smoothing parameter (10.0), the result
    approximates a streight line.  With the lowest smoothing parameter (0.0),
    the result is identical with a discontinous first order step function.

    Function |smooth_logistic1| is protected against numerical overflow.
    Hence even extremely high `value/parameter` ratios are allowed:

    >>> round_(smooth_logistic1(1000., .1))
    1.0
    """
    cdef double temp
    if parameter <= 0.:
        if value < 0.:
            return 0.
        elif value == 0.:
            return .5
        else:
            return 1.
    else:
        temp = value/parameter
        if temp < MAX_LOG_FLOAT:
            return (1.-1./(1.+exp(temp)))
        else:
            return 1.


cpdef inline double smooth_logistic2(double value, double parameter) nogil:
    """Smoothing kernel based on the integral of the logistic function.

    :math:`f_{log2}(x, c) = c \\cdot ln(1+exp(x/c))`

    The following example shows the shape of the integral of the
    logistic function for four different smoothing parameters:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value, par=3.0,  par=1.0,  par=0.1,  par=0.0')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
    ...         round_(smoothutils.smooth_logistic2(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value, par=10.0,  par=1.0,  par=0.1,  par=0.0
       -5, 4.740770, 0.006715, 0.000000, 0.000000
       -4, 5.130153, 0.018150, 0.000000, 0.000000
       -3, 5.543552, 0.048587, 0.000000, 0.000000
       -2, 5.981389, 0.126928, 0.000000, 0.000000
       -1, 6.443967, 0.313262, 0.000005, 0.000000
        0, 6.931472, 0.693147, 0.069315, 0.000000
        1, 7.443967, 1.313262, 1.000005, 1.000000
        2, 7.981389, 2.126928, 2.000000, 2.000000
        3, 8.543552, 3.048587, 3.000000, 3.000000
        4, 9.130153, 4.018150, 4.000000, 4.000000
        5, 9.740770, 5.006715, 5.000000, 5.000000

    With the highest value of the smoothing parameter (3.0), the resulting
    line is relatively straight.  With the lowest smoothing parameter (0.0),
    the result is identical with a second order discontinous step function.

    Function |smooth_logistic2| is protected against numerical overflow.
    Hence even extremely high `value/parameter` ratios are allowed:

    >>> round_(smooth_logistic2(1000., .1))
    1000.0
    """
    cdef double temp
    if parameter <= 0.:
        if value < 0.:
            return 0.
        else:
            return value
    else:
        temp = value/parameter
        if temp < MAX_LOG_FLOAT:
            return parameter*log(1.+exp(temp))
        else:
            return value

cpdef inline double smooth_logistic2_derivative(double value,
                                                double parameter) nogil:
    """Derivative of the function |smooth_logistic2| regarding its
    smoothing parameter.

    :math:`\\frac{d}{dc}f_{log2}(x, c) =
    \\frac{x}{c \\cdot exp(x/c)+c} \\cdot ln(exp(-x/c)+1)`

    The following example shows the derivates for four different smoothing
    parameters:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value,  par=3.0,  par=1.0,  par=0.1, par=0.0')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
    ...         round_(smoothutils.smooth_logistic2_derivative(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
       -5, 0.437790, 0.040180, 0.000000, 0.000000
       -4, 0.512107, 0.090095, 0.000000, 0.000000
       -3, 0.582203, 0.190865, 0.000000, 0.000000
       -2, 0.640533, 0.365334, 0.000000, 0.000000
       -1, 0.679449, 0.582203, 0.000499, 0.000000
        0, 0.693147, 0.693147, 0.693147, 0.693147
        1, 0.679449, 0.582203, 0.000499, 0.000000
        2, 0.640533, 0.365334, 0.000000, 0.000000
        3, 0.582203, 0.190865, 0.000000, 0.000000
        4, 0.512107, 0.090095, 0.000000, 0.000000
        5, 0.437790, 0.040180, 0.000000, 0.000000

    The validity of the calculated derivatives can be inspected by comparing
    with sufficiently accurate numerical approximations:

    >>> dc = 1e-6
    >>> from hydpy.cythons import smoothutils
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value,  par=3.0,  par=1.0,  par=0.1,  par=0.0')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
    ...         est = (smoothutils.smooth_logistic2(value, parameter+dc) -
    ...                smoothutils.smooth_logistic2(value, parameter))/dc
    ...         round_(est, width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
       -5, 0.437790, 0.040180, 0.000000, 0.000000
       -4, 0.512107, 0.090095, 0.000000, 0.000000
       -3, 0.582203, 0.190865, 0.000000, 0.000000
       -2, 0.640533, 0.365334, 0.000000, 0.000000
       -1, 0.679449, 0.582203, 0.000499, 0.000000
        0, 0.693147, 0.693147, 0.693147, 0.693147
        1, 0.679449, 0.582203, 0.000499, 0.000000
        2, 0.640533, 0.365334, 0.000000, 0.000000
        3, 0.582203, 0.190865, 0.000000, 0.000000
        4, 0.512107, 0.090095, 0.000000, 0.000000
        5, 0.437790, 0.040180, 0.000000, 0.000000

    Function |smooth_logistic2_derivative| is protected against numerical
    overflow. Hence even extremely high negative `value/parameter` ratios
    are allowed:

    >>> round_(smooth_logistic2_derivative(-1000., .1))
    0.0
    """
    cdef double temp
    if parameter <= 0.:
        if value == 0.:
            return log(2.)
        else:
            return 0.
    else:
        temp = -value/parameter
        if temp < MAX_LOG_FLOAT:
            return value/(parameter*exp(-temp)+parameter)+log(exp(temp)+1.)
        else:
            return 0.


cpdef inline double smooth_logistic3(double value, double parameter) nogil:
    """Smoothing kernel which combines |smooth_logistic1| and
    |smooth_logistic2| for the regularization of functions containing
    two second order discontinuities.

    :math:`f_{log3}(x, c) =
    (1-w) \\cdot f_{log2}(x, c) + w \\cdot (1-f_{log2}(x, c))`

    :math:`w = f_{log2}(x-1/2, d)`

    :math:`d = max(0.54 \\cdot c^{1.17}, 0.025)`

    The following example shows the shape of this combined smoothing
    function for three different smoothing parameters:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> from numpy import arange
    >>> for value in arange(-5.5, 6):
    ...     if value == -5.5:
    ...         round_('value,  par=3.0,  par=1.0,  par=0.1,  par=0.0')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
    ...         round_(smoothutils.smooth_logistic3(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value,  par=3.0,  par=1.0,  par=0.1,  par=0.1
     -5.5, 0.167513, 0.003996, 0.000000, 0.000000
     -4.5, 0.206271, 0.010618, 0.000000, 0.000000
     -3.5, 0.251687, 0.027603, 0.000000, 0.000000
     -2.5, 0.304292, 0.068844, 0.000000, 0.000000
     -1.5, 0.364136, 0.158615, 0.000000, 0.000000
     -0.5, 0.430211, 0.314615, 0.000672, 0.000000
      0.5, 0.500000, 0.500000, 0.500000, 0.500000
      1.5, 0.569789, 0.685385, 0.999328, 1.000000
      2.5, 0.635864, 0.841385, 1.000000, 1.000000
      3.5, 0.695708, 0.931156, 1.000000, 1.000000
      4.5, 0.748313, 0.972397, 1.000000, 1.000000
      5.5, 0.793729, 0.989382, 1.000000, 1.000000

    With the highest value of the smoothing parameter (3.0), the resulting
    line is relatively straight.  With the lowest smoothing parameter (0.0),
    the result is identical with a function with two second order
    discontinuities.
    """
    cdef double subtotal_1 = smooth_logistic2(value, parameter)
    cdef double subtotal_2 = 1.-smooth_logistic2(1.-value, parameter)
    cdef double meta_parameter = max(.025, .54*parameter**1.17)
    cdef double weight = smooth_logistic1(value-.5, meta_parameter)
    return  (1.-weight)*subtotal_1 + weight*subtotal_2


cpdef inline double smooth_max1(
                    double x_value, double y_value, double parameter) nogil:
    """Smoothing kernel for approximating the maximum function for two
    values based on the LogSumExp function.

    :math:`f_{max}(x, y, c) = c \\cdot ln(exp(x/c)+exp(y/c))`

    The following example shows the different degree of approximation of
    the maximum function for four different smoothing parameters.  Parameter
    x is constantly set to 5, parameter y is varied between 0 and 10:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> for value in range(11):
    ...     if value == 0:
    ...         round_('y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0')
    ...     round_(value, width=7, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.3, 0.0]):
    ...         round_(smoothutils.smooth_max1(5., value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0
          0, 5.519024, 5.006715, 5.000000, 5.000000
          1, 5.701888, 5.018150, 5.000000, 5.000000
          2, 5.939785, 5.048587, 5.000014, 5.000000
          3, 6.243110, 5.126928, 5.000382, 5.000000
          4, 6.620917, 5.313262, 5.010516, 5.000000
          5, 7.079442, 5.693147, 5.207944, 5.000000
          6, 7.620917, 6.313262, 6.010516, 6.000000
          7, 8.243110, 7.126928, 7.000382, 7.000000
          8, 8.939785, 8.048587, 8.000014, 8.000000
          9, 9.701888, 9.018150, 9.000000, 9.000000
         10, 10.519024, 10.006715, 10.00000, 10.00000

    With the highest value of the smoothing parameter (3.0), the resulting
    line is relatively straight.  With the lowest smoothing parameter (0.0),
    the result is identical with the usual (discontinuous) maximum function.

    Function |smooth_max1| is protected against numerical underflow and
    overflow.  In the following example, extreme values are added to both
    the x and the y value of 5 and 6 respectively.  The degree of smoothing
    is always identical:

    >>> for test in ['-1e8', '0.0', '1e8']:
    ...     round_(test, end=', ')
    ...     test = float(test)
    ...     round_(smoothutils.smooth_max1(test+5.0, test+6.0, 1.0)-test)
    -1e8, 6.313262
    0.0, 6.313262
    1e8, 6.313262
    """
    cdef double m_temp, x_temp, y_temp
    m_temp = _max(x_value, y_value)
    if parameter <= 0.:
        return m_temp
    else:
        x_temp = exp((x_value-m_temp)/parameter)
        y_temp = exp((y_value-m_temp)/parameter)
        return m_temp + parameter*log(x_temp+y_temp)


cpdef inline double smooth_min1(
                    double x_value, double y_value, double parameter) nogil:
    """Smoothing kernel for approximating the minimum function for two
    values based on the LogSumExp function.

    :math:`f_{max}(x, y, c) = -c \\cdot ln(exp(x/-c)+exp(y/-c))`

    The following example shows the different degree of approximation of
    the minimum function for four different smoothing parameters.  Parameter
    x is constantly set to 5, parameter y is varied between 0 and 10:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> for value in range(11):
    ...     if value == 0:
    ...         round_('y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0')
    ...     round_(value, width=7, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.3, 0.0]):
    ...         round_(smoothutils.smooth_min1(5., value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 3:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0
          0, -0.519024, -0.006715, -0.00000, 0.000000
          1, 0.298112, 0.981850, 1.000000, 1.000000
          2, 1.060215, 1.951413, 1.999986, 2.000000
          3, 1.756890, 2.873072, 2.999618, 3.000000
          4, 2.379083, 3.686738, 3.989484, 4.000000
          5, 2.920558, 4.306853, 4.792056, 5.000000
          6, 3.379083, 4.686738, 4.989484, 5.000000
          7, 3.756890, 4.873072, 4.999618, 5.000000
          8, 4.060215, 4.951413, 4.999986, 5.000000
          9, 4.298112, 4.981850, 5.000000, 5.000000
         10, 4.480976, 4.993285, 5.000000, 5.000000

    With the highest value of the smoothing parameter (3.0), the resulting
    line is relatively straight.  With the lowest smoothing parameter (0.0),
    the result is identical with the usual (discontinuous) minimum function.

    Function |smooth_min1| is protected against numerical underflow and
    overflow.  In the following example, extreme values are added to both
    the x and the y value of 5 and 6 respectively.  The degree of smoothing
    is always identical:

    >>> for test in ['-1e8', ' 0.0', ' 1e8']:
    ...     round_(test, end=', ')
    ...     test = float(test)
    ...     round_(smoothutils.smooth_min1(test+5.0, test+6.0, 1.0)-test)
    -1e8, 4.686738
     0.0, 4.686738
     1e8, 4.686738
    """
    return -smooth_max1(-x_value, -y_value, parameter)
