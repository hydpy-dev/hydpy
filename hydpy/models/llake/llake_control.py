# -*- coding: utf-8 -*-

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import timetools
from hydpy.core import objecttools


class N(parametertools.SingleParameter):
    """Anzahl Interpolationsstützstellen (number of nodes for the
    interpolation between water state, volume and discharge) [-].

    Parameter |N| determines the length of all 1- and 2-dimensional
    parameters of HydPy-L-Lake.  This requires that the value of
    the respective |N| instance is set before any of the values
    of these 1- and 2-dimensional parameters are set.  Changing the
    value of the |N| instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> n(5)

        For "simple" 1-dimensional parameters, the shape depends on the
        value of |N| only:

        >>> w.shape
        (5,)

        For time varying parameters (derived from |SeasonalParameter|),
        it also depends on the defined number simulation steps per leap year:

        >>> verzw.shape
        (732,)
        >>> q.shape
        (732, 5)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (2, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to |N| instances
        within parameter control files.  Sets the shape of the associated
        1- and 2-dimensional parameter objects additionally.
        """
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        for subpars in self.subpars.pars.model.parameters:
            for par in subpars:
                if par.name == 'toy':
                    continue
                elif par.NDIM == 1:
                    if isinstance(par, parametertools.SeasonalParameter):
                        par.shape = (None,)
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


class MaxDT(parametertools.SingleParameter):
    """Maximale interne Rechenschrittweite (maximum of the internal step size)
    [T].

    Examples:

        Initialize a llake model and set different time step length for
        parameterstep, simulationstep and maxdt:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> maxdt('1h')

        Internally, the value of maxdt is stored in seconds, but in string
        representations it is shown as a |Period| string:

        >>> maxdt.value
        3600.0
        >>> maxdt
        maxdt('1h')

        Note that maxdt only defines the maximum internal step size, not the
        one actually used.  Hence, maxdt is e.g. allowed to be larger than the
        actual simulation step size:

        >>> maxdt('2d')
        >>> maxdt
        maxdt('2d')

        It is allowed the set the number of seconds directly or modify it
        by mathematical operations:

        >>> maxdt.value = 60.
        >>> maxdt
        maxdt('1m')
        >>> maxdt *= 120.
        >>> maxdt
        maxdt('2h')

        However, for the more secure way of calling the object trying to
        pass an argument which cannot be converted to a Period instance
        unambiguously results in an exception:

        >>> maxdt(60.)
        Traceback (most recent call last):
        ...
        TypeError: While trying the set the value of parameter `maxdt` of \
the lake model handled by element `?`, the following error occurred: \
The supplied argument must be either an instance of `datetime.timedelta` \
or `str`.  The given arguments type is float. (An example: set `max dt` to \
3600 seconds by writing `maxdt("1h"))
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def __call__(self, *args, **kwargs):
        try:
            args = [timetools.Period(args[0]).seconds]
        except BaseException:
            objecttools.augment_excmessage(
                'While trying the set the value of parameter `maxdt` '
                'of the lake model handled by element `%s`'
                % objecttools.devicename(self),
                '(An example: set `max dt` to 3600 seconds by writing '
                '`maxdt("1h"))')
        parametertools.SingleParameter.__call__(self, *args, **kwargs)

    def __repr__(self):
        try:
            return "%s('%s')" % (self.name,
                                 str(timetools.Period.fromseconds(self.value)))
        except BaseException:
            return '%s(?)' % self.name


class MaxDW(parametertools.SeasonalParameter):
    """Maximale Absenkgeschwindigkeit (maximum drop in water level) [m/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)


class Verzw(parametertools.SeasonalParameter):
    """Zu- oder Abschlag des Seeausflusses (addition to or abstraction from
    the seas outlet discharge) [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-L-Lake, directly defined by the user."""
    CLASSES = (N,
               W,
               V,
               Q,
               MaxDT,
               MaxDW,
               Verzw)
