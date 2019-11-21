# -*- coding: utf-8 -*-
"""This module implements features which help to regularize discontinuous
process equations.

.. _Tyralla (2016): http://www.hydrology.ruhr-uni-bochum.de/hydrolgy/mam/\
download/schriftenreihe_29.pdf

Many hydrological models rely heavily on discontinuous equations describing
hydrological processes.  The related "if-else" blocks are often not
theoretically motivated.  Instead, they are thought to ease implementing
ad hoc solutions of different (parts of) process equations without taking
care of the entire set of process equations.

There are some reasons to ground new model concepts on mainly continuous
process descriptions. See e. g. `Tyralla (2016)`_ for more a more exhaustive
discussion of this topic.  Nevertheless, one might often want -- at least as
a starting point -- to pick single discontinuous but well-established
equations of old model concepts for a new model concept.  The tools
provided by this module can be used to regularize the discontinuities of
such equations.  More concrete, the tools are thought for replacing
discontinuous process equations by continuous approximations.

Some of the implemented features are to be applied during model simulations
or are in some other way performance-critical, which is why we implement
them computationally efficient by using Cython (see the extension module
|smoothutils|.
"""

# import...
# ...from standard-library
import os
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import conf
from hydpy.core import exceptiontools
from hydpy.cythons.autogen import smoothutils
interpolate = exceptiontools.OptionalImport(
    'interpolate', ['scipy.interpolate'], locals())
optimize = exceptiontools.OptionalImport(
    'optimize', ['scipy.optimize'], locals())


def calc_smoothpar_logistic1(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_logistic1|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_logistic1
    >>> smoothpar = calc_smoothpar_logistic1(2.5)

    When using this smoothing parameter value, the output of function
    |smooth_logistic1| differs by 1 % from the related "true" discontinuous
    step function for the input values -2.5 and 2.5 (located at a distance
    of 2.5 from the position of the discontinuity):

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_logistic1(-2.5, smoothpar))
    0.01
    >>> round_(smoothutils.smooth_logistic1(2.5, smoothpar))
    0.99

    For zero or negative meta parameter values, function
    |calc_smoothpar_logistic1| zero:

    >>> round_(calc_smoothpar_logistic1(0.0))
    0.0
    >>> round_(calc_smoothpar_logistic1(-1.0))
    0.0
    """
    return numpy.clip(metapar/numpy.log(99.), 0., numpy.inf)


def _error_smoothpar_logistic2(par, metapar):
    return smoothutils.smooth_logistic2(-metapar, par) - .01


def _smooth_logistic2_derivative1(par, metapar):
    return smoothutils.smooth_logistic2_derivative1(metapar, par)


def calc_smoothpar_logistic2(metapar, iterate: bool = False):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_logistic2|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_logistic2
    >>> smoothpar = calc_smoothpar_logistic2(2.5)

    When using this smoothing parameter value, the output of function
    |smooth_logistic2| differs by 1% from the related "true" discontinuous
    step function for the input values -2.5 and 2.5 (located at a distance
    of 2.5 from the position of the discontinuity):

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_logistic2(-2.5, smoothpar))
    0.01
    >>> round_(smoothutils.smooth_logistic2(2.5, smoothpar))
    2.51

    For zero or negative meta parameter values, function
    |calc_smoothpar_logistic2| returns zero:

    >>> round_(calc_smoothpar_logistic2(-1.0))
    0.0
    >>> round_(calc_smoothpar_logistic2(-1.0, iterate=True))
    0.0

    Note that function |calc_smoothpar_logistic2| returns approximations
    only.  By standard, it relies on linear interpolation between 10,000
    unevenly spaced supporting points in the interval [0.0, 1,000].  The
    achieved interpolation accuracy should suffice for the anticipated
    applications, but be aware of low accuracies in the extrapolation range:

    >>> metapars = 1000.0, 2000.0, 3000.0
    >>> smoothpars = calc_smoothpar_logistic2(metapars)
    >>> for metapar, smoothpar in zip(metapars, smoothpars):
    ...     round_(smoothutils.smooth_logistic2(-metapar, smoothpar))
    0.01
    0.010137
    0.011697

    Alternatively, you can gain higher accuracies through the iterative
    refinement of the results based on the Newton method:

    >>> for metapar, smoothpar in zip(metapars, smoothpars):
    ...     smoothpar = calc_smoothpar_logistic2(metapar, iterate=True)
    ...     round_(smoothutils.smooth_logistic2(-metapar, smoothpar))
    0.01
    0.01
    0.01

    However, this is possible for scalar values only and very time-consuming.
    Furthermore, there is no guarantee for success (in the extrapolation range):

    >>> calc_smoothpar_logistic2(1000000.0, iterate=True)   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: Failed to converge ...

    Hence, our advice to model developers is to restrict the allowed
    span of all smoothing parameters relying on function
    |calc_smoothpar_logistic2| to the mentioned interval and not to use
    the iterative refinement strategy.  Consider the refinement only in
    cases that require extremely high accuracies or where one needs to
    extrapolate a little (of course, the range of the supporting points,
    provided by file `support_points_for_smoothpar_logistic2.npy`, could
    also be extended).
    """
    if iterate:
        if metapar <= 0.:
            return 0.
        return optimize.newton(_error_smoothpar_logistic2,
                               .3 * metapar**.84,
                               _smooth_logistic2_derivative1,
                               args=(metapar,))
    return numpy.clip(
        _cubic_interpolator_for_smoothpar_logistic2(metapar), 0.0, numpy.inf)


def calc_smoothpar_logistic3(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_logistic3|.

    |smooth_logistic3| is only an alias for |smooth_logistic2|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_logistic3
    >>> smoothpar = calc_smoothpar_logistic3(2.5)

    When using this smoothing parameter value, the output of function
    |smooth_logistic3| would ideally differ by 1% from the related "true"
    discontinuous step function for the input values -2.5 and 3.5 (located
    at a distance of 2.5 from the position of the nearest discontinuity):

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_logistic3(-2.5, smoothpar))
    0.009876
    >>> round_(smoothutils.smooth_logistic3(3.5, smoothpar))
    0.990124

    In contrast to the examples shown for functions |smooth_logistic1| and
    |smooth_logistic2|, the smoothing parameter determined for function
    |smooth_logistic3| is not in perfect agreement with the given meta
    parameter.  For most purposes, the resulting error is negligible.
    If you strive for very high accuracy, ask us to implement some iterative
    refinement strategy or try it on your own.
    """
    return calc_smoothpar_logistic2(metapar)


def calc_smoothpar_max1(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_max1|.

    |smooth_max1| is only an alias for |smooth_logistic2|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_max1
    >>> smoothpar = calc_smoothpar_max1(2.5)

    When using this smoothing parameter value, the output of function
    |smooth_max1| is 0.01 above the discontinuous maximum function result, if
    the absolute value of the difference between the x and the y value is 2.5:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_max1(4.0, 1.5, smoothpar))
    4.01
    """
    return calc_smoothpar_logistic2(metapar)


def calc_smoothpar_min1(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_min1|.

    |smooth_min1| is only an alias for |smooth_logistic2|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_min1
    >>> smoothpar = calc_smoothpar_min1(2.5)

    When using this smoothing parameter value, the output of function
    |smooth_min1| is 0.01 below the discontinuous minimum function result, if
    the absolute value of the difference between the x and the y value is 2.5:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_min1(-4.0, -1.5, smoothpar))
    -4.01
    """
    return calc_smoothpar_logistic2(metapar)


# Calculate and save the supporting points required for method
# `calc_smoothpar_logistic2`:
# xys = numpy.zeros((2, 10000), dtype=float)
# xys[0, :] = numpy.linspace(0., 1000.**(1./3.), 10000)**3.
# xys[1, :] = [calc_smoothpar_logistic2(x, iterate=True) for x in xys[0]]
# numpy.save(os.path.join(
#     conf.__path__[0], 'support_points_for_smoothpar_logistic2.npy'), xys)


# Load the supporting points required for method `calc_smoothpar_logistic2`:
xys = numpy.load(os.path.join(
    conf.__path__[0], 'support_points_for_smoothpar_logistic2.npy'))
_cubic_interpolator_for_smoothpar_logistic2 = interpolate.interp1d(
    xys[0], xys[1], kind='cubic', fill_value="extrapolate")
del xys
