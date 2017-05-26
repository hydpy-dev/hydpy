# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class N(parametertools.SingleParameter):
    """Anzahl Interpolationsstützstellen (number of nodes for the
    interpolation between water state, volume and discharge) [-].

    Parameter :class:`N` determines the length of all 1- and 2-dimensional
    parameters of HydPy-L-Lake.  This requires that the value of
    the respective :class:`N` instance is set before any of the values
    of these 1- and 2-dimensional parameters are set.  Changing the
    value of the :class:`N` instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> n(5)

        For "simple" 1-dimensional parameters, the shape depends on the
        value of :class:`N` only:

        >>> w.shape
        (5,)

        For time varying parameters (derived from
        :class:`~hydpy.core.parametertools.SeasonalParameter), it also depends
        on the defined number of dates:

        >>> verzw.shape
        >>> (0, )
        >>> verzw..toy_7 = 3.
        >>> verzw.shape
        >>> (1, )
        >>> q.shape
        (0, 5)
        >>> q.toy_7 = 3.
        >>> q.shape
        (1, 5)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (0., None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to :class:`N` instances
        within parameter control files.  Sets the shape of the associated
        1- and 2-dimensional parameter objects additionally.
        """
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        for (_name, subpars) in self.subpars.pars.model.parameters:
            for (name, par) in subpars:
                if par.NDIM == 1:
                    if isinstance(par, parametertools.SeasonalParameter):
                        par.shape = (0,)
                    else:
                        par.shape = self.value
                elif ((par.NDIM == 2) and
                      isinstance(par, parametertools.SeasonalParameter)):
                    par.shape = (None, self.value)


class W(parametertools.MultiParameter):
    """Wasserstand (water stage) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class V(parametertools.MultiParameter):
    """Wasservolumen bei vorgegebenem Wasserstand (water volume for a
    given water stage) [m³]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class Q(parametertools.SeasonalParameter):
    """Üblicher Seeausfluss bei vorgegebenem Wasserstand (sea outlet discharge
    for a given water stage) [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)


class MaxDW(parametertools.SingleParameter):
    """Maximale Absenkgeschwindigkeit (maximum drop in water level) [m/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)


class Verzw(parametertools.SeasonalParameter):
    """Zu- oder Abschlag des Seeausflusses (addition to or abstraction from
    the seas outlet discharge) [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-L-Lake, directly defined by the user."""
    _PARCLASSES = (N, W, V, Q, MaxDW, Verzw)
