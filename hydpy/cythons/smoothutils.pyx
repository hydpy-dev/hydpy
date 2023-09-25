r"""This Cython module implements the performance-critical functions of the Python
module `smoothtools`.

MAX_LOG_FLOAT = 700
___________________

The natural logarithm of the highest possible float value.

The exact value depends on the actual system.  So, an automated estimation of this
value would be advisable.


smooth_logistic1
________________

Smoothing kernel based on the logistic function.

:math:`f_{log1}(x, c) = 1 - \frac{1}{1 + exp(x / c)}`

The following example shows the typical shape of the logistic function for four
different smoothing parameters:

>>> from hydpy.cythons import smoothutils
>>> from hydpy import round_
>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value, par=10.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([10.0, 1.0, 0.1, 0.0]):
...         round_(smoothutils.smooth_logistic1(value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
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

With the highest value of the smoothing parameter (10.0), the result approximates a
straight line.  With the lowest smoothing parameter (0.0), the result is identical with
a discontinuous first-order step function.

Function `smooth_logistic1` protects itself against numerical overflow.  Hence, even
extremely high `value/parameter` ratios are allowed:

>>> round_(smoothutils.smooth_logistic1(1000., .1))
1.0


smooth_logistic1_derivative2
____________________________

Calculate the derivative of the function `smooth_logistic1` with respect to the given
value.

:math:`\frac{d}{dx}f_{log1}(x, c) = \frac{exp(x/c)}{(exp(x/c)+1)^2}`

The following example shows the derivates for four different smoothing parameters:

>>> import numpy
>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         result = smoothutils.smooth_logistic1_derivative2(value, parameter)
...         if numpy.isinf(result):
...             print(result, end="")
...         else:
...             round_(result, width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
   -5, 0.044543, 0.006648, 0.000000, 0.000000
   -4, 0.055030, 0.017663, 0.000000, 0.000000
   -3, 0.065537, 0.045177, 0.000000, 0.000000
   -2, 0.074719, 0.104994, 0.000000, 0.000000
   -1, 0.081061, 0.196612, 0.000454, 0.000000
    0, 0.083333, 0.250000, 2.500000, inf
    1, 0.081061, 0.196612, 0.000454, 0.000000
    2, 0.074719, 0.104994, 0.000000, 0.000000
    3, 0.065537, 0.045177, 0.000000, 0.000000
    4, 0.055030, 0.017663, 0.000000, 0.000000
    5, 0.044543, 0.006648, 0.000000, 0.000000


We validate the calculated derivatives by comparing them with sufficiently accurate
numerical approximations:

>>> dx = 1e-7
>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         est = (smoothutils.smooth_logistic1(value+dx, parameter) -
...                smoothutils.smooth_logistic1(value, parameter))/dx
...         round_(est, width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
   -5, 0.044543, 0.006648, 0.000000, 0.000000
   -4, 0.055030, 0.017663, 0.000000, 0.000000
   -3, 0.065537, 0.045177, 0.000000, 0.000000
   -2, 0.074719, 0.104994, 0.000000, 0.000000
   -1, 0.081061, 0.196612, 0.000454, 0.000000
    0, 0.083333, 0.250000, 2.500000, 5000000.0
    1, 0.081061, 0.196612, 0.000454, 0.000000
    2, 0.074719, 0.104994, 0.000000, 0.000000
    3, 0.065537, 0.045177, 0.000000, 0.000000
    4, 0.055030, 0.017663, 0.000000, 0.000000
    5, 0.044543, 0.006648, 0.000000, 0.000000

Function `smooth_logistic2_derivative1` protects itself against numerical overflow.
Hence, even extremely high `value/parameter` ratios are allowed:

>>> round_(smoothutils.smooth_logistic1_derivative2(1000.0, 0.1))
0.0


smooth_logistic2
________________

Smoothing kernel based on the integral of the logistic function.

:math:`f_{log2}(x, c) = c \cdot ln(1+exp(x/c))`

The following example shows the shape of the integral of the logistic function for four
different smoothing parameters:

>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value, par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         round_(smoothutils.smooth_logistic2(value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
value, par=3.0,  par=1.0,  par=0.1,  par=0.0
   -5, 0.519024, 0.006715, 0.000000, 0.000000
   -4, 0.701888, 0.018150, 0.000000, 0.000000
   -3, 0.939785, 0.048587, 0.000000, 0.000000
   -2, 1.243110, 0.126928, 0.000000, 0.000000
   -1, 1.620917, 0.313262, 0.000005, 0.000000
    0, 2.079442, 0.693147, 0.069315, 0.000000
    1, 2.620917, 1.313262, 1.000005, 1.000000
    2, 3.243110, 2.126928, 2.000000, 2.000000
    3, 3.939785, 3.048587, 3.000000, 3.000000
    4, 4.701888, 4.018150, 4.000000, 4.000000
    5, 5.519024, 5.006715, 5.000000, 5.000000


With the highest value of the smoothing parameter (3.0), the resulting line is
relatively straight.  With the lowest smoothing parameter (0.0), the result is
identical to a second-order discontinuous step function.

Function `smooth_logistic2` protects itself against numerical overflow.  Hence, even
extremely high `value/parameter` ratios are allowed:

>>> round_(smoothutils.smooth_logistic2(1000.0, 0.1))
1000.0

smooth_logistic2_derivative1
____________________________

Calculate the derivative of the function `smooth_logistic2` with respect to its
smoothing parameter.

:math:`\frac{d}{dc}f_{log2}(x, c) = \frac{x}{c \cdot exp(x/c)+c} \cdot ln(exp(-x/c)+1)`

The following example shows the derivates for four different smoothing parameters:

>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         round_(smoothutils.smooth_logistic2_derivative1(value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
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

We validate the calculated derivatives by comparing them with sufficiently accurate
numerical approximations.

>>> dc = 1e-6
>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         est = (smoothutils.smooth_logistic2(value, parameter+dc) -
...                smoothutils.smooth_logistic2(value, parameter))/dc
...         round_(est, width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
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

Function `smooth_logistic2_derivative1` protects itself against numerical overflow.
Hence, even extremely high negative `value/parameter` ratios are allowed:

>>> round_(smoothutils.smooth_logistic2_derivative1(-1000.0, 0.1))
0.0


smooth_logistic2_derivative2
____________________________

Calculate the derivative of the function `smooth_logistic2` with respect to the given
value.

:math:`\frac{d}{dx}f_{log2}(x, c) = \frac{exp(x/c)}{exp(x/c)+1}`

The following example shows the derivates for four different smoothing parameters:

>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         round_(smoothutils.smooth_logistic2_derivative2(value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
   -5, 0.158869, 0.006693, 0.000000, 0.000000
   -4, 0.208609, 0.017986, 0.000000, 0.000000
   -3, 0.268941, 0.047426, 0.000000, 0.000000
   -2, 0.339244, 0.119203, 0.000000, 0.000000
   -1, 0.417430, 0.268941, 0.000045, 0.000000
    0, 0.500000, 0.500000, 0.500000, 1.000000
    1, 0.582570, 0.731059, 0.999955, 1.000000
    2, 0.660756, 0.880797, 1.000000, 1.000000
    3, 0.731059, 0.952574, 1.000000, 1.000000
    4, 0.791391, 0.982014, 1.000000, 1.000000
    5, 0.841131, 0.993307, 1.000000, 1.000000

We validate the calculated derivatives by comparing them with sufficiently accurate
numerical approximations.

>>> dx = 1e-7
>>> for value in range(-5, 6):
...     if value == -5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         est = (smoothutils.smooth_logistic2(value+dx, parameter) -
...                smoothutils.smooth_logistic2(value, parameter))/dx
...         round_(est, width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
   -5, 0.158869, 0.006693, 0.000000, 0.000000
   -4, 0.208609, 0.017986, 0.000000, 0.000000
   -3, 0.268941, 0.047426, 0.000000, 0.000000
   -2, 0.339244, 0.119203, 0.000000, 0.000000
   -1, 0.417430, 0.268941, 0.000045, 0.000000
    0, 0.500000, 0.500000, 0.500000, 1.000000
    1, 0.582570, 0.731059, 0.999955, 1.000000
    2, 0.660756, 0.880797, 1.000000, 1.000000
    3, 0.731059, 0.952574, 1.000000, 1.000000
    4, 0.791391, 0.982014, 1.000000, 1.000000
    5, 0.841131, 0.993307, 1.000000, 1.000000

Function `smooth_logistic2_derivative2` protects itself against numerical overflow.
Hence, even extremely high `value/parameter` ratios are allowed:

>>> round_(smoothutils.smooth_logistic2_derivative2(1000.0, 0.1))
1.0


smooth_logistic3
________________

Smoothing kernel that combines `smooth_logistic1` and `smooth_logistic2` for the
regularization of functions containing two second-order discontinuities.

:math:`f_{log3}(x, c) =
(1-w) \cdot f_{log2}(x, c) + w \cdot (1-f_{log2}(x, c))`

:math:`w = f_{log2}(x-1/2, d)`

:math:`d = max(0.54 \cdot c^{1.17}, 0.025)`

The following example shows the shape of this combined smoothing function for four
different smoothing parameters:

>>> from numpy import arange
>>> for value in arange(-5.5, 6):
...     if value == -5.5:
...         round_("value,  par=3.0,  par=1.0,  par=0.1,  par=0.0")
...     round_(value, width=5, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.1, 0.0]):
...         round_(smoothutils.smooth_logistic3(value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
value,  par=3.0,  par=1.0,  par=0.1,  par=0.0
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

With the highest value of the smoothing parameter (3.0), the resulting line is
relatively straight.  With the lowest smoothing parameter (0.0), the result is
identical to a function with two second-order discontinuities.

smooth_max1
___________

Smoothing kernel for approximating the maximum function for two values based on the
"LogSumExp" function.

:math:`f_{max}(x, y, c) = c \cdot ln(exp(x/c)+exp(y/c))`

The following example shows the different degree of approximation of the maximum
function for four different smoothing parameters:

>>> for value in range(11):
...     if value == 0:
...         round_("y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0")
...     round_(value, width=7, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.3, 0.0]):
...         round_(smoothutils.smooth_max1(5.0, value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
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

With the highest value of the smoothing parameter (3.0), the resulting line is
relatively straight.  With the lowest smoothing parameter (0.0), the result is
identical to the usual (discontinuous) maximum function.

Function `smooth_max1` protects itself against numerical underflow and overflow.  In
the following example, extreme values are added to both the `x` and the `y` value of 5
and 6, respectively.  The degree of smoothing is always identical:

>>> for test in ["-1e8", "0.0", "1e8"]:
...     round_(test, end=", ")
...     test = float(test)
...     round_(smoothutils.smooth_max1(test+5.0, test+6.0, 1.0)-test)
-1e8, 6.313262
0.0, 6.313262
1e8, 6.313262

smooth_min1
___________

Smoothing kernel for approximating the minimum function for two values based on the
LogSumExp function.

:math:`f_{max}(x, y, c) = -c \cdot ln(exp(x/-c)+exp(y/-c))`

The following example shows the different degree of approximation of the minimum
function for four different smoothing parameters:

>>> for value in range(11):
...     if value == 0:
...         round_("y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0")
...     round_(value, width=7, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.3, 0.0]):
...         round_(smoothutils.smooth_min1(5.0, value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
y_value, par=3.0,  par=1.0,  par=0.3,  par=0.0
      0, -0.519024, -0.006715, 0.000000, 0.000000
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

With the highest value of the smoothing parameter (3.0), the resulting line is
relatively straight.  With the lowest smoothing parameter (0.0), the result is
identical to the usual (discontinuous) minimum function.

Function `smooth_min1` protects itself against numerical underflow and overflow.  In
the following example, extreme values are added to both the `x` and the `y` value of 5
and 6, respectively.  The degree of smoothing is always identical:

>>> for test in ["-1e8", " 0.0", " 1e8"]:
...     round_(test, end=", ")
...     test = float(test)
...     round_(smoothutils.smooth_min1(test+5.0, test+6.0, 1.0)-test)
-1e8, 4.686738
 0.0, 4.686738
 1e8, 4.686738

smooth_max2
___________

Smoothing kernel for approximating the maximum function for three values based on the
"LogSumExp" function.

:math:`f_{max}(x, y, z, c) = c \cdot ln(exp(x/c)+exp(y/c)+exp(z/c))`

The following example shows the different degree of approximation of the maximum
function for four different smoothing parameters:

>>> for value in range(11):
...     if value == 0:
...         round_("z_value, par=3.0,  par=1.0,  par=0.3,  par=0.0")
...     round_(value, width=7, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.3, 0.0]):
...         round_(smoothutils.smooth_max2(-50.0, 5.0, value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
z_value, par=3.0,  par=1.0,  par=0.3,  par=0.0
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

With the highest value of the smoothing parameter (3.0), the resulting line is
relatively straight.  With the lowest smoothing parameter (0.0), the result is
identical to the usual (discontinuous) maximum function.

Function `smooth_max2` protects itself against numerical underflow and overflow.  In
the following example, extreme values are added to the `x`, the `y`, and the `z` value
of 5, 6, and 7, respectively.  The degree of smoothing is always identical:

>>> for test in ["-1e8", "0.0", "1e8"]:
...     round_(test, end=", ")
...     test = float(test)
...     round_(smoothutils.smooth_max2(test+5.0, test+6.0, test+7.0, 1.0)-test)
-1e8, 7.407606
0.0, 7.407606
1e8, 7.407606

smooth_min2
___________

Smoothing kernel for approximating the minimum function for two values based on the
LogSumExp function.

:math:`f_{max}(x, y, z, c) = -c \cdot ln(exp(x/-c)+exp(y/-c)+exp(z/-c))`

The following example shows the different degree of approximation of the minimum
function for four different smoothing parameters:

>>> for value in range(11):
...     if value == 0:
...         round_("z_value, par=3.0,  par=1.0,  par=0.3,  par=0.0")
...     round_(value, width=7, lfill=" ", end=", ")
...     for idx, parameter in enumerate([3.0, 1.0, 0.3, 0.0]):
...         round_(smoothutils.smooth_min2(60.0, 5.0, value, parameter),
...                width=8, rfill="0", end="")
...         if idx < 3:
...             round_("", end=", ")
...         else:
...             round_("")
z_value, par=3.0,  par=1.0,  par=0.3,  par=0.0
      0, -0.519024, -0.006715, 0.000000, 0.000000
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

With the highest value of the smoothing parameter (3.0), the resulting line is
relatively straight.  With the lowest smoothing parameter (0.0), the result is
identical to the usual (discontinuous) minimum function.

Function `smooth_min2` protects itself against numerical underflow and overflow.  In
the following example, extreme values are added to the `x`, the `y`, and the `z` value
of 5, 6, and 7, respectively.  The degree of smoothing is always identical:

>>> for test in ["-1e8", " 0.0", " 1e8"]:
...     round_(test, end=", ")
...     test = float(test)
...     round_(smoothutils.smooth_min2(test+5.0, test+6.0, test+7.0, 1.0)-test)
-1e8, 4.592394
 0.0, 4.592394
 1e8, 4.592394


filter_norm
___________

Filter kernel based on the normal distribution for smoothly turning additional function
terms around specific values on or off.

:math:`f_{norm}(x) =
exp \left( -\frac{1}{2} \cdot \left( \frac{x - \mu}{\sigma} \right)^2 \right)`

The higher the given sigma value, the wider is `filter_norm`'s radius of action.  In
contrast to the complete normal distribution, the highest value is always one (except
for a sigma value of zero, for which `filter_norm` should never impact any results):

>>> for value in range(11):
...     if value == 0:
...         print("      x,  sigma=2,  sigma=1,  sigma=0")
...     round_(value, width=7, lfill=" ", end=", ")
...     for i, sigma in enumerate([2.0, 1.0, 0.0]):
...         result = smoothutils.filter_norm(value, 5.0, sigma)
...         round_(result, width=8, rfill="0", end="")
...         if i < 2:
...             round_("", end=", ")
...         else:
...             round_("")
      x,  sigma=2,  sigma=1,  sigma=0
      0, 0.043937, 0.000004, 0.000000
      1, 0.135335, 0.000335, 0.000000
      2, 0.324652, 0.011109, 0.000000
      3, 0.606531, 0.135335, 0.000000
      4, 0.882497, 0.606531, 0.000000
      5, 1.000000, 1.000000, 0.000000
      6, 0.882497, 0.606531, 0.000000
      7, 0.606531, 0.135335, 0.000000
      8, 0.324652, 0.011109, 0.000000
      9, 0.135335, 0.000335, 0.000000
     10, 0.043937, 0.000004, 0.000000

"""

import cython
from libc.math cimport exp, log
from libc.math cimport INFINITY as inf

cdef double MAX_LOG_FLOAT = 700.0


cpdef inline double _max1(
    double x_value,
    double y_value,
) nogil:
    """The usual (discontinuous) maximum function for two values.

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils._max1(1.5, 2.5))
    2.5
    >>> round_(smoothutils._max1(-1.5, -2.5))
    -1.5
    >>> round_(smoothutils._max1(0.0, 0.0))
    0.0

    """
    if x_value > y_value:
        return x_value
    return y_value


cpdef inline double _max2(
    double x_value,
    double y_value,
    double z_value,
) nogil:
    """The usual (discontinuous) maximum function for three values.

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils._max2(1.5, 2.5, 2.0))
    2.5
    >>> round_(smoothutils._max2(-1.5, -2.5, -2.0))
    -1.5
    >>> round_(smoothutils._max2(-1.5, -2.5, 2.0))
    2.0
    >>> round_(smoothutils._max2(0.0, 0.0, 0.0))
    0.0

    """
    if x_value > y_value:
        if x_value > z_value:
            return x_value
        return z_value
    if y_value > z_value:
        return y_value
    return z_value


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
    return y_value


cpdef inline double smooth_logistic1(double value, double parameter) nogil:
    """Smoothing kernel based on the logistic function."""
    cdef double temp
    if parameter <= 0.0:
        if value < 0.0:
            return 0.0
        elif value == 0.0:
            return 0.5
        return 1.0
    temp = value/parameter
    if temp < MAX_LOG_FLOAT:
        return 1.0 - 1.0 / (1.0 + exp(temp))
    return 1.0


cpdef inline double smooth_logistic1_derivative2(
        double value, double parameter) nogil:
    """Derivative of the function `smooth_logistic1` with respect to its input value."""
    cdef double temp
    if parameter <= 0.0:
        if value == 0.0:
            return inf
        return 0.0
    temp = value / parameter
    if temp < MAX_LOG_FLOAT:
        return exp(temp) / (parameter * (exp(temp) + 1.0) ** 2)
    return 0.0


cpdef inline double smooth_logistic2(double value, double parameter) nogil:
    """Smoothing kernel based on the integral of the logistic function."""
    cdef double temp
    if parameter <= 0.0:
        if value < 0.0:
            return 0.0
        return value
    temp = value / parameter
    if temp < MAX_LOG_FLOAT:
        return parameter * log(1.0 + exp(temp))
    return value

cpdef inline double smooth_logistic2_derivative2(
        double value, double parameter) nogil:
    """Derivative of the function `smooth_logistic2` with respect to its input value."""
    cdef double temp
    if parameter <= 0.0:
        if value < 0.0:
            return 0.0
        return 1.0
    temp = value / parameter
    if temp < MAX_LOG_FLOAT:
        return exp(temp) / (exp(temp) + 1.0)
    return 1.0


cpdef inline double smooth_logistic2_derivative1(
        double value, double parameter) nogil:
    """Derivative of the function `smooth_logistic2` with respect to its smoothing 
    parameter."""
    cdef double temp
    if parameter <= 0.0:
        if value == 0.0:
            return log(2.0)
        return 0.0
    temp = -value / parameter
    if temp < MAX_LOG_FLOAT:
        return value/(parameter * exp(-temp) + parameter) + log(exp(temp) + 1.0)
    return 0.0


cpdef inline double smooth_logistic3(double value, double parameter) nogil:
    """Smoothing kernel which combines `smooth_logistic1` and `smooth_logistic2` for 
    the regularization of functions containing two second order discontinuities."""
    cdef double subtotal_1 = smooth_logistic2(value, parameter)
    cdef double subtotal_2 = 1.0 - smooth_logistic2(1.0 - value, parameter)
    cdef double meta_parameter = max(0.025, 0.54 * parameter**1.17)
    cdef double weight = smooth_logistic1(value - 0.5, meta_parameter)
    return  (1.0 - weight) * subtotal_1 + weight * subtotal_2


cpdef inline double smooth_max1(
    double x_value,
    double y_value,
    double parameter,
) nogil:
    """Smoothing kernel for approximating the maximum function for two values based on 
    the LogSumExp function."""
    cdef double m_temp, x_temp, y_temp
    m_temp = _max1(x_value, y_value)
    if parameter <= 0.:
        return m_temp
    x_temp = exp((x_value - m_temp) / parameter)
    y_temp = exp((y_value - m_temp) / parameter)
    return m_temp + parameter * log(x_temp + y_temp)


cpdef inline double smooth_min1(
    double x_value,
    double y_value,
    double parameter,
) nogil:
    """Smoothing kernel for approximating the minimum function for two values based on 
    the LogSumExp function."""
    return -smooth_max1(-x_value, -y_value, parameter)


cpdef inline double smooth_max2(
    double x_value,
    double y_value,
    double z_value,
    double parameter,
) nogil:
    """Smoothing kernel for approximating the maximum function for three values based 
    on the LogSumExp function."""
    cdef double m_temp, x_temp, y_temp, z_temp
    m_temp = _max2(x_value, y_value, z_value)
    if parameter <= 0.:
        return m_temp
    x_temp = exp((x_value - m_temp) / parameter)
    y_temp = exp((y_value - m_temp) / parameter)
    z_temp = exp((z_value - m_temp) / parameter)
    return m_temp + parameter * log(x_temp + y_temp + z_temp)


cpdef inline double smooth_min2(
    double x_value,
    double y_value,
    double z_value,
    double parameter,
) nogil:
    """Smoothing kernel for approximating the minimum function for three values based 
    on the LogSumExp function."""
    return -smooth_max2(-x_value, -y_value, -z_value, parameter)


cpdef double filter_norm(double value, double mean, double std) nogil:
    """Filter kernel based on the normal distribution for smoothly turning additional 
    function terms around specific values on or off."""
    if std > 0.0:
        return exp(-0.5 * ((value - mean) / std) ** 2)
    return 0.0