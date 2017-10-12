#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This Cython module implements the performance-critical functions of the
Python module :mod:`~hydpy.auxs.smoothtools`.
"""

import cython
from libc.math cimport exp, log


cpdef double MAX_LOG_FLOAT = 700.0
"""The natural logarithm of the highest possible float value.

Values below and slightly above can be assigned to the exponential function:

>>> from numpy import exp, log
>>> from hydpy.core.objecttools import round_
>>> round_(log(exp(700.0)))
700.0

But values clearly exceeding `700` result in a numerical overflow:

>>> x = log(exp(720.0))
Traceback (most recent call last):
...
RuntimeWarning: overflow encountered in exp
>>> x
inf

The exact value of :const:`MAX_LOG_FLOAT` might differ between different
systems.  So an automated estimation of this value would be advisable.
(On Windows using 64 bit Python, even 709.0 works.  But a not too small
savety factor seemed preferable.)
"""


cpdef inline double smooth_logistic1(double value, double parameter) nogil:
    """Smoothing kernel based on the logistic function.

    :math:`f_{log1}(x, c) = 1-\\frac{1}{1+exp(x/c)}`

    The following example shows the typical shape of the logistic function
    for three different smoothing parameters:

    >>> from hydpy.cythons.smoothutils import smooth_logistic1
    >>> from hydpy.core.objecttools import round_
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value, par=10.0,  par=1.0,  par=0.1')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([10.0, 1.0, 0.1]):
    ...         round_(smooth_logistic1(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 2:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value, par=10.0,  par=1.0,  par=0.1
       -5, 0.377541, 0.006693, 0.000000
       -4, 0.401312, 0.017986, 0.000000
       -3, 0.425557, 0.047426, 0.000000
       -2, 0.450166, 0.119203, 0.000000
       -1, 0.475021, 0.268941, 0.000045
        0, 0.500000, 0.500000, 0.500000
        1, 0.524979, 0.731059, 0.999955
        2, 0.549834, 0.880797, 1.000000
        3, 0.574443, 0.952574, 1.000000
        4, 0.598688, 0.982014, 1.000000
        5, 0.622459, 0.993307, 1.000000

    With the highest value of the smoothing parameter (10.0), the result
    approximates a streight line.  With the lowest smoothing parameter (0.1),
    the result approximates a discontinous first order step function.

    Function :func:`smooth_logistic1` is protected against numerical overflow.
    Hence even extremely high `value/parameter` ratios are allowed:

    >>> round_(smooth_logistic1(1000., .1))
    1.0
    """
    cdef double temp = value/parameter
    if temp < MAX_LOG_FLOAT:
        return (1.-1./(1.+exp(temp)))
    else:
        return 1.


cpdef inline double smooth_logistic2(double value, double parameter) nogil:
    """Smoothing kernel based on the integral of the logistic function.

    :math:`f_{log2}(x, c) = c \\cdot ln(1+exp(x/c))`

    The following example shows the shape of the integral of the
    logistic function for three different smoothing parameters:

    >>> from hydpy.cythons.smoothutils import smooth_logistic2
    >>> from hydpy.core.objecttools import round_
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value, par=3.0,  par=1.0,  par=0.1')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1]):
    ...         round_(smooth_logistic2(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 2:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value, par=10.0,  par=1.0,  par=0.1
       -5, 4.740770, 0.006715, 0.000000
       -4, 5.130153, 0.018150, 0.000000
       -3, 5.543552, 0.048587, 0.000000
       -2, 5.981389, 0.126928, 0.000000
       -1, 6.443967, 0.313262, 0.000005
        0, 6.931472, 0.693147, 0.069315
        1, 7.443967, 1.313262, 1.000005
        2, 7.981389, 2.126928, 2.000000
        3, 8.543552, 3.048587, 3.000000
        4, 9.130153, 4.018150, 4.000000
        5, 9.740770, 5.006715, 5.000000

    With the highest value of the smoothing parameter (3.0), the resulting
    line is relatively straight.  With the lowest smoothing parameter (0.1),
    the result approximates a second order discontinous step function.

    Function :func:`smooth_logistic2` is protected against numerical overflow.
    Hence even extremely high `value/parameter` ratios are allowed:

    >>> round_(smooth_logistic2(1000., .1))
    1000.0
    """
    cdef double temp = value/parameter
    if temp < MAX_LOG_FLOAT:
        return parameter*log(1.+exp(temp))
    else:
        return value

cpdef inline double smooth_logistic2_derivative(double value,
                                                double parameter) nogil:
    """Derivative of the function :func:`smooth_logistic2` regarding its
    smoothing parameter.

    :math:`\\frac{d}{dc}f_{log2}(x, c) =
    \\frac{x}{c \\cdot exp(x/c)+c} \\cdot ln(exp(-x/c)+1)`

    The following example shows the derivates for three different smoothing
    parameters:

    >>> from hydpy.cythons.smoothutils import smooth_logistic2_derivative
    >>> from hydpy.core.objecttools import round_
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value,  par=3.0,  par=1.0,  par=0.1')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1]):
    ...         round_(smooth_logistic2_derivative(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 2:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value,  par=3.0,  par=1.0,  par=0.1
       -5, 0.437790, 0.040180, 0.000000
       -4, 0.512107, 0.090095, 0.000000
       -3, 0.582203, 0.190865, 0.000000
       -2, 0.640533, 0.365334, 0.000000
       -1, 0.679449, 0.582203, 0.000499
        0, 0.693147, 0.693147, 0.693147
        1, 0.679449, 0.582203, 0.000499
        2, 0.640533, 0.365334, 0.000000
        3, 0.582203, 0.190865, 0.000000
        4, 0.512107, 0.090095, 0.000000
        5, 0.437790, 0.040180, 0.000000

    The validity of the calculated derivatives can be inspected by comparing
    with sufficiently accurate numerical approximations:

    >>> dc = 1e-4
    >>> from hydpy.cythons.smoothutils import smooth_logistic2
    >>> for value in range(-5, 6):
    ...     if value == -5:
    ...         round_('value,  par=3.0,  par=1.0,  par=0.1')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1]):
    ...         est = (smooth_logistic2(value, parameter+dc/2) -
    ...                smooth_logistic2(value, parameter-dc/2))/dc
    ...         round_(est, width=8, rfill='0', end='')
    ...         if idx < 2:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value,  par=3.0,  par=1.0,  par=0.1
       -5, 0.437790, 0.040180, 0.000000
       -4, 0.512107, 0.090095, 0.000000
       -3, 0.582203, 0.190865, 0.000000
       -2, 0.640533, 0.365334, 0.000000
       -1, 0.679449, 0.582203, 0.000499
        0, 0.693147, 0.693147, 0.693147
        1, 0.679449, 0.582203, 0.000499
        2, 0.640533, 0.365334, 0.000000
        3, 0.582203, 0.190865, 0.000000
        4, 0.512107, 0.090095, 0.000000
        5, 0.437790, 0.040180, 0.000000


    Function :func:`smooth_logistic2_derivative` is protected against
    numerical overflow. Hence even extremely high negative`value/parameter`
    ratios are allowed:

    >>> round_(smooth_logistic2_derivative(-1000., .1))
    0.0
    """
    cdef double temp = -value/parameter
    if temp < MAX_LOG_FLOAT:
        return (value/(parameter*exp(value/parameter)+parameter) +
                log(exp(temp)+1.))
    else:
        return 0.


cpdef inline double smooth_logistic3(double value, double parameter) nogil:
    """Smoothing kernel which combines :func:`smooth_logistic1`  and
    :func:`smooth_logistic2` for the regularization of functions containing
    two second order discontinuities.

    :math:`f_{log3}(x, c) =
    (1-w) \\cdot f_{log2}(x, c) + w \\cdot (1-f_{log2}(x, c))`

    :math:`w = f_{log2}(x-1/2, d)`

    :math:`d = max(0.54 \\cdot c^{1.17}, 0.025)`

    The following example shows the shape of this combined smoothing
    function for three different smoothing parameters:

    >>> from hydpy.cythons.smoothutils import smooth_logistic3
    >>> from hydpy.core.objecttools import round_
    >>> from numpy import arange
    >>> for value in arange(-5.5, 6):
    ...     if value == -5.5:
    ...         round_('value, par=3.0,  par=1.0,  par=0.1')
    ...     round_(value, width=5, lfill=' ', end=', ')
    ...     for idx, parameter in enumerate([3.0, 1.0, 0.1]):
    ...         round_(smooth_logistic3(value, parameter),
    ...                width=8, rfill='0', end='')
    ...         if idx < 2:
    ...             round_('', end=', ')
    ...         else:
    ...             round_('')
    value, par=3.0,  par=1.0,  par=0.1
     -5.5, 0.167513, 0.003996, 0.000000
     -4.5, 0.206271, 0.010618, 0.000000
     -3.5, 0.251687, 0.027603, 0.000000
     -2.5, 0.304292, 0.068844, 0.000000
     -1.5, 0.364136, 0.158615, 0.000000
     -0.5, 0.430211, 0.314615, 0.000672
      0.5, 0.500000, 0.500000, 0.500000
      1.5, 0.569789, 0.685385, 0.999328
      2.5, 0.635864, 0.841385, 1.000000
      3.5, 0.695708, 0.931156, 1.000000
      4.5, 0.748313, 0.972397, 1.000000
      5.5, 0.793729, 0.989382, 1.000000

    With the highest value of the smoothing parameter (3.0), the resulting
    line is relatively straight.  With the lowest smoothing parameter (0.1),
    the result approximates a function with two second order discontinuities.
    """
    cdef double subtotal_1 = smooth_logistic2(value, parameter)
    cdef double subtotal_2 = 1.-smooth_logistic2(1.-value, parameter)
    cdef double meta_parameter = max(.025, .54*parameter**1.17)
    cdef double weight = smooth_logistic1(value-.5, meta_parameter)
    return  (1.-weight)*subtotal_1 + weight*subtotal_2
