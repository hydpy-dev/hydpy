# -*- coding: utf-8 -*-
"""This module implements features which help to regularize discontinuous
process equations.

.. _Tyralla (2016): http://www.hydrology.ruhr-uni-bochum.de/hydrolgy/mam/\
download/schriftenreihe_29.pdf

Many hydrological models rely heavily on discontinous equations describing
hydrological processes.  The related "if-else" blocks are often not
theoretically motivated.  Instead, they are thought to ease implementing
ad hoc solutions of different (parts of) process equations without taking
care of the total set of process equations.

There are some reasons to ground new model concepts on mainly continuous
process descriptions. See e.g. `Tyralla (2016)`_ for more a more exhaustive
discussion of this topic.  Nevertheless, one might often want -- least as
a starting point -- to pick single discontinuous but well-established
equations of old model concepts for a new model concept.  The tools
provided by this module can be used to regularize the discontinuities of
such equations.  More concrete, the tools are thought for replacing
discontinous process equations by continuous approximations.

Some of the implemented features are to be applied during model simulations
and are in some other way performance-critical.  These features are defined
in the Cython extension module |smoothutils|.
"""

# import...
# ...from site-packages
import numpy
from scipy import optimize
# ...from HydPy
from hydpy.cythons import smoothutils
from hydpy.core import autodoctools


def calc_smoothpar_logistic1(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_logistic1|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_logistic1
    >>> smoothpar = calc_smoothpar_logistic1(2.5)

    Using this smoothing parameter value, the output of function
    |smooth_logistic1| differs by 1 % from the related `true`
    discontinuous step function for the input values -2.5 and 2.5
    (which are located at a distance of 2.5 from the position of
    the discontinuity):

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_logistic1(-2.5, smoothpar))
    0.01
    >>> round_(smoothutils.smooth_logistic1(2.5, smoothpar))
    0.99

    For zero or negative meta parameter values, a zero smoothing parameter
    value is returned:

    >>> round_(calc_smoothpar_logistic1(0.0))
    0.0
    >>> round_(calc_smoothpar_logistic1(-1.0))
    0.0
    """
    return max(metapar/numpy.log(99.), 0.)


def _error_smoothpar_logistic2(par, metapar):
    return smoothutils.smooth_logistic2(-metapar, par) - .01


def _smooth_logistic2_derivative(par, metapar):
    return smoothutils.smooth_logistic2_derivative(metapar, par)


def calc_smoothpar_logistic2(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_logistic2|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_logistic2
    >>> smoothpar = calc_smoothpar_logistic2(2.5)

    Using this smoothing parameter value, the output of function
    |smooth_logistic2| differs by
    1 % from the related `true` discontinuous step function for the
    input values -2.5 and 2.5 (which are located at a distance of 2.5
    from the position of the discontinuity):

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_logistic2(-2.5, smoothpar))
    0.01
    >>> round_(smoothutils.smooth_logistic2(2.5, smoothpar))
    2.51

    For zero or negative meta parameter values, a zero smoothing parameter
    value is returned:

    >>> round_(calc_smoothpar_logistic2(0.0))
    0.0
    >>> round_(calc_smoothpar_logistic2(-1.0))
    0.0
    """
    if metapar <= 0.:
        return 0.
    return optimize.newton(_error_smoothpar_logistic2,
                           .3 * metapar**.84,
                           _smooth_logistic2_derivative,
                           args=(metapar,))


def calc_smoothpar_logistic3(metapar):
    """Return the smoothing parameter corresponding to the given meta
    parameter when using |smooth_logistic3|.

    |smooth_logistic3| is only an alias for |smooth_logistic2|.

    Calculate the smoothing parameter value corresponding the meta parameter
    value 2.5:

    >>> from hydpy.auxs.smoothtools import calc_smoothpar_logistic3
    >>> smoothpar = calc_smoothpar_logistic3(2.5)

    Using this smoothing parameter value, the output of function
    |smooth_logistic3| would ideally differs by 1 % from the related
    `true` discontinuous step function for the input values -2.5 and 3.5
    (which are located at a distance of 2.5 from the position of the
    nearest discontinuity):

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
    If one needs a higher accuracy, some iterative refinement should be
    implemented.
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

    Using this smoothing parameter value, the output of function
    |smooth_max1| is 0.01 above the usual discontinuous maximum
    function result, if the absolute value of the difference
    between the x and the y value is 2.5:

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

    Using this smoothing parameter value, the output of function
    |smooth_min1| is 0.01 below the usual discontinuous minimum
    function result, if the absolute value of the difference
    between the x and the y value is 2.5:

    >>> from hydpy.cythons import smoothutils
    >>> from hydpy import round_
    >>> round_(smoothutils.smooth_min1(-4.0, -1.5, smoothpar))
    -4.01
    """
    return calc_smoothpar_logistic2(metapar)


autodoctools.autodoc_module()
