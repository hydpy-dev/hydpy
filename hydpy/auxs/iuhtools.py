# -*- coding: utf-8 -*-
"""This module supports modelling based on instantaneous unit hydrographs.

This module implements some abstract descriptor classes, metaclasses and base
classes.  If you are just interested in applying a certain instantaneous
unit hydrograph (iuh) function or if you want to implement an additional
iuh, see the examples or the source code of class
:class:`TranslationDiffusionEquation`.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import itertools
# ...from site-packages
import numpy
from scipy import special
from matplotlib import pyplot
# ...from Hydpy
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.auxs import statstools
from hydpy.auxs import armatools


class IUH_Parameter(object):
    """Descriptor base class for :class:`PrimaryParameter` and
    :class:`SecondaryParameter`.

    The first initialization argument is the parameters name.  Optionally,
    an alternative type (the default type is :class:`float`) and a
    documentation string can be passed.
    """

    def __init__(self, name, type_=float, doc=None):
        self.name = name
        self._name = '_'+name
        self.type_ = type_
        self.__doc__ = ('Instantaneous unit hydrograph parameter %s.' % name
                        if doc is None else str(doc))

    def __get__(self, obj, type_=None):
        return self if obj is None else getattr(obj, self._name, None)

    def _convert_type(self, value):
        try:
            return self.type_(value)
        except BaseException:
            raise TypeError(
                'The value `%s` of type `%s` could not be converted to type '
                '`%s` of the instantaneous unit hydrograph parameter `%s`.'
                % (value, objecttools.classname(value),
                   objecttools.classname(self.type_), self.name))


class PrimaryParameter(IUH_Parameter):
    """Descriptor base class for parameters of instantaneous unit hydrograph
    functions to be defined by the user.

    When a primary parameter value is set or deleted, the master instance is
    instructed to :func:`~IUH.update` all secondary parameter values.
    """

    def __set__(self, obj, value):
        value = self._convert_type(value)
        setattr(obj, self._name, value)
        obj.update()

    def __delete__(self, obj):
        setattr(obj, self._name, None)
        obj.update()


class SecondaryParameter(IUH_Parameter):
    """Descriptor base class for parameters of instantaneous unit hydrograph
    functions which can be determined automatically."""

    def __set__(self, obj, value):
        value = self._convert_type(value)
        setattr(obj, self._name, value)

    def __delete__(self, obj):
        setattr(obj, self._name, None)


class MetaIUH(type):
    """Metaclass for class :class:`IUH`.

    For storing :class:`PrimaryParameter` and :class:`SecondaryParameter` in
    separate dictionaries.
    """

    def __new__(cls, name, parents, dict_):
        primary_parameters = {}
        secondary_parameters = {}
        for key, value in dict_.items():
            if isinstance(value, PrimaryParameter):
                primary_parameters[key] = value
            elif isinstance(value, SecondaryParameter):
                secondary_parameters[key] = value
        dict_['_primary_parameters'] = primary_parameters
        dict_['_secondary_parameters'] = secondary_parameters
        return type.__new__(cls, name, parents, dict_)


# Just for making MetaIUH the type of class IUH both in Python 2 and 3:
_MetaIUH = MetaIUH('_MetaIUH', (), {})


class IUH(_MetaIUH):
    """Base class for instantaneous unit hydrograph function objects.

    See class :class:`TranslationDiffusionEquation` for explanations and
    application examples.

    For developers: The string representation does also work for
    parameter-free :class:`IUH` subclasses:

    >>> from hydpy.auxs.iuhtools import IUH
    >>> class Test(IUH):
    ...     pass
    >>> Test()
    Test()
    """

    dt_response = 1e-2
    """Relative stepsize for plotting and analyzing iuh functions."""

    smallest_response = 1e-9
    """Smallest value taken into account for plotting and analyzing iuh
    functions."""

    def __init__(self, **kwargs):
        self.ma = armatools.MA(self)
        self.arma = armatools.ARMA(ma_model=self.ma)
        if kwargs:
            self.set_primary_parameters(**kwargs)

    def set_primary_parameters(self, **kwargs):
        """Set all primary parameters at once."""
        given = sorted(kwargs.keys())
        required = sorted(self._primary_parameters)
        if given == required:
            for (key, value) in kwargs.items():
                setattr(self, key, value)
        else:
            raise ValueError(
                'When passing primary parameter values as initialization '
                'arguments of the instantaneous unit hydrograph class `%s`, '
                'or when using method `set_primary_parameters, one has to '
                'to define all values at once via keyword arguments.  '
                'But instead of the primary parameter names `%s` the '
                'following keywords were given: %s.'
                % (objecttools.classname(self),
                   ', '.join(required), ', '.join(given)))

    @property
    def are_primary_parameters_complete(self):
        """True/False flag that indicates wheter the values of all primary
        parameters are defined or not."""
        for primpar in self._primary_parameters.values():
            if primpar.__get__(self) is None:
                return False
        return True

    def update(self):
        """Delete the coefficients of the pure MA model and also all MA and
        AR coefficients of the ARMA model.  Also calculate or delete the values
        of all secondary iuh parameters, depending on the completeness of the
        values of the primary parameters.
        """
        del self.ma.coefs
        del self.arma.ma_coefs
        del self.arma.ar_coefs
        if self.are_primary_parameters_complete:
            self.calc_secondary_parameters()
        else:
            for secpar in self._secondary_parameters.values():
                secpar.__delete__(self)

    @property
    def delay_response_series(self):
        """A tuple of two numpy arrays, which hold the time delays and the
        associated iuh values respectively."""
        delays = []
        responses = []
        sum_responses = 0.
        for t in itertools.count(self.dt_response/2., self.dt_response):
            delays.append(t)
            response = self(t)
            responses.append(response)
            sum_responses += self.dt_response*response
            if (sum_responses > .9) and (response < self.smallest_response):
                break
        return numpy.array(delays), numpy.array(responses)

    def plot(self, threshold=None, **kwargs):
        """Plot the instanteneous unit hydrograph.

        The optional argument allows for defining a threshold of the cumulative
        sum uf the hydrograph, used to adjust the largest value of the x-axis.
        It must be a value between zero and one.
        """
        delays, responses = self.delay_response_series
        pyplot.plot(delays, responses, **kwargs)
        pyplot.xlabel('time')
        pyplot.ylabel('response')
        if threshold is not None:
            threshold = numpy.clip(threshold, 0., 1.)
            cumsum = numpy.cumsum(responses)
            idx = numpy.where(cumsum >= threshold*cumsum[-1])[0][0]
            pyplot.xlim(0., delays[idx])

    @property
    def moments(self):
        """The first two time delay weighted statistical moments of the
        instantaneous unit hydrograph."""
        delays, response = self.delay_response_series
        moment1 = statstools.calc_mean_time(delays, response)
        moment2 = statstools.calc_mean_time_deviation(delays, response,
                                                      moment1)
        return numpy.array([moment1, moment2])

    def __repr__(self):
        parts = [objecttools.classname(self), '(']
        for (name, primpar) in sorted(self._primary_parameters.items()):
            value = primpar.__get__(self)
            if value is not None:
                parts.extend([name, '=', objecttools.repr_(value), ', '])
        if parts[-1] == ', ':
            parts[-1] = ')'
        else:
            parts.append(')')
        return ''.join(parts)


class TranslationDiffusionEquation(IUH):
    """An instantaneous unit hydrograph based on the `translation diffusion
    equation`.

    The equation used is a linear approximation of the Saint-Venant
    equations for channel routing:

      :math:`h(t) = \\frac{a}{t \\cdot \\sqrt{\\pi \\cdot t}} \\cdot
      e^{-t \\cdot (a/t-b)^2}`

    with:
      :math:`a = \\frac{x}{2 \\cdot \\sqrt{d}}`

      :math:`b = \\frac{u}{2 \\cdot \\sqrt{d}}`

    There are three primary parameter whichs values need to be defined by
    the user:

    >>> from hydpy import TranslationDiffusionEquation
    >>> tde = TranslationDiffusionEquation(u=5., d=15., x=50.)
    >>> tde
    TranslationDiffusionEquation(d=15.0, u=5.0, x=50.0)

    The values of both secondary parameters are determined automatically:

    >>> from hydpy import round_
    >>> round_((tde.a, tde.b))
    6.454972, 0.645497

    The function can be evaluated for time delays larger zero, but not for
    zero time delay:

    >>> import numpy
    >>> round_(tde(numpy.array([5., 10., 15., 20.])))
    0.040559, 0.115165, 0.031303, 0.00507
    >>> tde(0.)
    Traceback (most recent call last):
    ...
    ZeroDivisionError: float division by zero

    The first delay weighted central moment of the translation diffusion
    equation corresponds to the time lag (`x`/`u`), the second one to
    wave diffusion:

    >>> round_(tde.moments)
    10.0, 3.464101

    You can also plot the graph corresponding to the actual parameterization:

    >>> tde.plot(threshold=0.9)

    You can close the plotting window manually or by writing:

    >>> from matplotlib import pyplot
    >>> pyplot.close()

    All instances of the subclasses of :class:`IUH` provide a pure
    Moving Average and an Autoregressive-Moving Average approximation to the
    dt standard impulse of the instantaneous unit hydrograph function.  In
    the given example, the MA approximation involves 57 coefficients, and the
    ARMA approximation invoves 17 coefficients:

    >>> tde.ma.order
    57
    >>> tde.arma.order
    (3, 14)

    The diffusion of the MA model deviates from the iuh function due to
    aggregation.  For the ARMA model, there is also a slight deviation in
    time delay, as the ARMA model itself is only a approximation of the
    MA model:

    >>> round_(tde.ma.moments)
    10.0, 3.488074
    >>> round_(tde.arma.moments)
    10.000091, 3.488377

    For further information on using MA and ARMA models, read the
    documentation on module :mod:`~hydpy.auxs.armatools`.

    Changing a primary parameter results in an updating of the secondary
    parameters as well as the MA and the ARMA model:

    >>> tde.x = 5.
    >>> round_((tde.a, tde.b))
    0.645497, 0.645497
    >>> tde.ma.order
    37
    >>> tde.arma.order
    (4, 5)

    As long as the primary parameter values are incomplete, no secondary
    parameter values are available:

    >>> del tde.x
    >>> round_((tde.a, tde.b))
    None, None

    Suitable type conversions are performed when new parameter values are set:

    >>> tde.x = '1.'
    >>> tde.x
    1.0

    It a new value cannot be converted, an error is raised:

    >>> tde.x = 'a'
    Traceback (most recent call last):
    ...
    TypeError: The value `a` of type `str` could not be converted to type \
`float` of the instantaneous unit hydrograph parameter `x`.

    When passing parameter values as initialization arguments or when using
    method `set_primary_parameters`, tests for completeness are performed:

    >>> TranslationDiffusionEquation(u=5.0, d=15.0)
    Traceback (most recent call last):
    ...
    ValueError: When passing primary parameter values as initialization \
arguments of the instantaneous unit hydrograph class \
`TranslationDiffusionEquation`, or when using method \
`set_primary_parameters, one has to to define all values at once via \
keyword arguments.  But instead of the primary parameter names `d, u, x` \
the following keywords were given: d, u.
    """
    u = PrimaryParameter('u', doc='Wave velocity.')
    d = PrimaryParameter('d', doc='Diffusion coefficient.')
    x = PrimaryParameter('x', doc='Routing distance.')
    a = SecondaryParameter('a', doc='Distance related coefficient.')
    b = SecondaryParameter('b', doc='Velocity related coefficient.')

    def calc_secondary_parameters(self):
        """Determine the values of the secondary parameters `a` and `b`."""
        self.a = self.x/(2.*self.d**.5)
        self.b = self.u/(2.*self.d**.5)

    def __call__(self, t):
        return self.a/(t*(numpy.pi*t)**.5)*numpy.exp(-t*(self.a/t-self.b)**2)


class LinearStorageCascade(IUH):
    """An instantaneous unit hydrograph based on the `linear storage cascade`.

    The equation involves the gamma function, allowing for a fractional number
    of storages:

      :math:`h(t) = c \\cdot (t/k)^{n-1} \\cdot e^{-t/k}`

    with:
      :math:`c = \\frac{1}{k \\cdot \\gamma(n)}`

    After defining the values of the two primary parameters, the function
    object can be applied:

    >>> from hydpy import LinearStorageCascade
    >>> lsc = LinearStorageCascade(n=2.5, k=2.)
    >>> from hydpy import round_
    >>> round_(lsc.c)
    0.376126
    >>> import numpy
    >>> round_(lsc(numpy.array([5., 10., 15., 20.])))
    0.122042, 0.028335, 0.004273, 0.00054

    """
    n = PrimaryParameter('n', doc='Number of linear storages.')
    k = PrimaryParameter(
        'k', doc='Time of concentration of each individual storage.')
    c = SecondaryParameter('c', doc='Proportionality factor.')

    def calc_secondary_parameters(self):
        """Determine the value of the secondary parameter `c`."""
        self.c = 1./(self.k*special.gamma(self.n))

    def __call__(self, t):
        return self.c*(t/self.k)**(self.n-1)*numpy.exp(-t/self.k)


autodoctools.autodoc_module()
