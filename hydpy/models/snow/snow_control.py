# pylint: disable=missing-module-docstring

import functools

import numpy
from scipy import integrate
from scipy import stats

from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_parameters


class NumberZones(parametertools.NmbParameter):
    """The number of separately modelled hydrological response units [-]."""

    SPAN = (0, None)


class NumberDivisions(parametertools.NmbParameter):
    """Number of snow classes in each zone [-]."""

    SPAN = (1, None)
    INIT = 1


class ZoneType(parametertools.NameParameter):
    """Hydrological response unit type [-]."""

    constants = parametertools.Constants(ANY=0)


class Land(snow_parameters.ZipParameterBool1D):
    """A flag that indicates whether the individual zones are land areas or not."""

    SPAN = (False, True)


class Water(snow_parameters.ZipParameterBool1D):
    """A flag that indicates whether the individual zones are water areas or not."""

    SPAN = (False, True)


class ZoneArea(snow_parameters.ZipParameterFloat1D):
    """The area of each hydrological response unit [km²]."""

    SPAN = (0.0, None)


class ZoneHeight(snow_parameters.ZipParameterFloat1D):
    """Zone elevation [100m]."""


class RainSnowThreshold(snow_parameters.ZipParameterFloat1D):
    """Temperature threshold for snow/rain [°C]."""

    INIT = 0.0


class RainSnowInterval(snow_parameters.ZipParameterFloat1D):
    """Temperature interval with a mixture of snow and rain [°C]."""

    SPAN = (0.0, None)
    INIT = 0.0


class ThroughfallDistribution(parametertools.Parameter):
    """Distribution of snowfall [-].

    Parameter |SFDist| handles multiple adjustment factors for snowfall, one for each
    snow class, to introduce spatial heterogeneity to the snow depth within each zone.
    If we, for example, define three snow classes per zone but assign the neutral value
    1.0 to |SFDist|, all snow classes will receive the same amount of liquid and frozen
    snowfall (everything else will also be identical, so defining three snow classes
    instead of one is just a waste of computation time):

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> numberdivisions(3)
    >>> sfdist(1.0)
    >>> sfdist
    sfdist(1.0)

    |SFDist| norms the given values. If we assign 0.1, 0.2, and 0.3, the snow classes
    receive 50 %, 100 %, and 150 % of the average snowfall of their respective zone:

    >>> sfdist(0.1, 0.2, 0.3)
    >>> sfdist
    sfdist(0.5, 1.0, 1.5)

    |SFDist| provides two convenient alternatives for defining multiple factors with
    single keyword arguments.  To illustrate how they work, we first define a test
    function that accepts a keyword argument, passes it to a |SFDist| instance for the
    cases of one to five snow classes, and prints the respective snow class-specific
    factors:

    >>> from hydpy import print_vector
    >>> def test(**kwargs):
    ...     for nmb in range(1, 6):
    ...         numberdivisions(nmb)
    ...         sfdist(**kwargs)
    ...         print_vector(sfdist.values)

    The first available keyword is `linear`.  Using it, |SFDist| calculates its factors
    in agreement with the original *HBV96* implementation.  For the lowest possible
    value, 0.0, all adjustment factors are one:

    >>> test(linear=0.0)
    1.0
    1.0, 1.0
    1.0, 1.0, 1.0
    1.0, 1.0, 1.0, 1.0
    1.0, 1.0, 1.0, 1.0, 1.0

    For the highest possible value, 1.0, the first snow class receives no snowfall,
    while the last snow receives twice the zone's average snowfall.  |SFDist|
    interpolates the factors of the other snow classes linearly:

    >>> test(linear=1.0)
    1.0
    0.0, 2.0
    0.0, 1.0, 2.0
    0.0, 0.666667, 1.333333, 2.0
    0.0, 0.5, 1.0, 1.5, 2.0

    For a value of 0.5, the first and the last snow class receive 50 % and 150 % of the
    zone's average snowfall:

    >>> test(linear=0.5)
    1.0
    0.5, 1.5
    0.5, 1.0, 1.5
    0.5, 0.833333, 1.166667, 1.5
    0.5, 0.75, 1.0, 1.25, 1.5

    The first available keyword is `lognormal`.  Here, |SFDist| calculates factors
    resulting in a lognormal distribution of snowfall, similarly as implemented in
    the COSERO model :cite:p:`ref-Frey2015CoseroSnow`.   Again, the lowest possible
    value,
    0.0, results in uniform snow distributions:

    >>> test(lognormal=0.0)
    1.0
    1.0, 1.0
    1.0, 1.0, 1.0
    1.0, 1.0, 1.0, 1.0
    1.0, 1.0, 1.0, 1.0, 1.0

    In the following examples, we increase the scale factor from 0.01 to 0.1 to 1.0.
    The higher the scale factor, the more snow concentrates in the last snow class:

    >>> test(lognormal=0.01)
    1.0
    0.992021, 1.007979
    0.989116, 0.999953, 1.010931
    0.987332, 0.996711, 1.003204, 1.012754
    0.986061, 0.994647, 0.999951, 1.005284, 1.014057

    >>> test(lognormal=0.1)
    1.0
    0.920344, 1.079656
    0.893412, 0.995313, 1.111276
    0.877282, 0.963406, 1.028038, 1.131273
    0.865966, 0.943604, 0.995118, 1.049519, 1.145792

    >>> test(lognormal=1.0)
    1.0
    0.317311, 1.682689
    0.228763, 0.624994, 2.146243
    0.188069, 0.446552, 0.854969, 2.51041
    0.163826, 0.361372, 0.612984, 1.047213, 2.814604

    Theoretically, higher scale factors are allowed. However, 1.0 results in highly
    heterogeneous snow distributions already.

    Wrong usage results in the usual error messages:

    >>> sfdist(normal=1.0)
    Traceback (most recent call last):
    ...
    NotImplementedError: The value(s) of parameter `sfdist` of element `?` could not \
be set based on the given keyword arguments.

    >>> sfdist(linear=1.0, lognormal=1.0)
    Traceback (most recent call last):
    ...
    NotImplementedError: The value(s) of parameter `sfdist` of element `?` could not \
be set based on the given keyword arguments.

    >>> sfdist(1.0, lognormal=1.0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `sfdist` of element `?` both positional and keyword \
arguments are given, which is ambiguous.
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, NumberDivisions):
            self.__hydpy__change_shape_if_necessary__((p.value,))

    def __call__(self, *args, **kwargs) -> None:
        numberdivisions = self.shape[0]
        idx = self._find_kwargscombination(args, kwargs, ({"linear"}, {"lognormal"}))
        if idx is None:
            super().__call__(*args, **kwargs)
        elif idx == 0:
            super().__call__(self._linear(kwargs["linear"], numberdivisions))
        else:
            super().__call__(self._lognormal(numberdivisions, kwargs["lognormal"]))
        self.value /= sum(self.value) / numberdivisions

    @staticmethod
    @functools.lru_cache
    def _linear(factor: float, numberdivisions: int) -> VectorInputFloat:
        if numberdivisions == 1:
            return (1.0,)
        return (
            factor * 2.0 * numpy.arange(numberdivisions) / (numberdivisions - 1)
            + (1.0 - factor)
        ) / numberdivisions

    @staticmethod
    @functools.lru_cache
    def _lognormal(numberdivisions: int, scale: float) -> VectorFloat:
        values = numpy.ones(numberdivisions, dtype=config.NP_FLOAT)
        if scale > 0.0:
            for idx in range(numberdivisions):
                values[idx] = integrate.quad(
                    lambda x: stats.lognorm.ppf(x, scale),
                    idx / numberdivisions,
                    (idx + 1) / numberdivisions,
                )[0]
        return values


class DegreeDayThreshold(snow_parameters.ZipParameterFloat1D):
    """Difference between |TTM| and |TT| [°C]."""

    INIT = 0.0


class DegreeDayFactor(snow_parameters.LandParameter1D):
    """Average degree day factor for snow melting [mm/T/K]."""

    TIME = True
    SPAN = (0.0, None)
    INIT = 3.5


class DegreeDayVariability(snow_parameters.ZipParameterFloat1D):
    """Annual variability of |CFMax| [mm/°C/T].

    Use positive values for the northern and negative values for the southern
    hemisphere.
    """

    TIME = True
    INIT = 0.0


class RefreezingFactor(snow_parameters.ZipParameterFloat1D):
    """Refreezing factor for water stored within the snow layer [-]."""

    SPAN = (0.0, None)
    INIT = 0.05


class WaterCapacity(snow_parameters.ZipParameterFloat1D):
    """Relative water holding capacity of the snow layer [-]."""

    SPAN = (0.0, None)
    INIT = 0.1


class SnowpackLimit(snow_parameters.LandParameter1D):
    """Maximum snow water equivalent [mm]."""

    SPAN = (0.0, None)
    INIT = numpy.inf


class RedistributionPaths(parametertools.Parameter):
    """Snow redistribution paths [-].

    |SRed| is a 2-dimensional parameter that handles weighting factors for all possible
    zone connections.  The source zones vary on the rows and the target zones on the
    columns.  In the following example, zone one sends all snow available for
    redistribution to zone three.  Zone two sends 50 % to zone four and 50 % to zone
    five.  Zone six sends 40 % to zone two, 40 % to zone three, and 20 % to zone four:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> numberzones(6)
    >>> land(True)
    >>> redistributionpaths([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.5, 0.5, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.5, 0.5, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])

    A zone can either redistribute no snow at all (we then call it a "dead end") or
    needs to send 100 % of the snow available for redistribution.  Hence, the sums of
    the individual rows must be either 0.0 or 1.0.  Method |SRed.verify| checks for
    possible violations of this requirement (by calling method |SRed.verify_sums|):

    >>> redistributionpaths([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.4, 0.5],
    ...       [0.0, 0.1, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
    >>> redistributionpaths.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: The sum(s) of the following row(s) of parameter `redistributionpaths` of element \
`?` are neither 0.0 nor 1.0: 3 and 4.

    Zones of type |ILAKE| possess no snow module.  Hence, they never release any snow
    for redistribution and method |SRed.verify| checks for possible unused weighting
    factors in the relevant rows (by calling method |SRed.verify_lakes|):

    >>> land(True, True, True, False, True, False)
    >>> redistributionpaths([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    >>> redistributionpaths.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: Internal lake zones cannot be involved in snow redistribution, so \
the sums of all rows of parameter `redistributionpaths` of element `?` corresponding to internal lake \
zones must be zero, which is not the case for the row(s): 3.

    For the same reason, internal lakes cannot receive and accumulate any redistributed
    snow.  Therefore, method |SRed.verify| additionally checks for possible problematic
    weighting factors in the relevant columns (by calling method |SRed.verify_lakes|):

    >>> redistributionpaths([[0.0, 0.5, 0.0, 0.0, 0.0, 0.5],
    ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    >>> redistributionpaths.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: Internal lake zones cannot be involved in snow redistribution, so \
the sums of all columns of parameter `redistributionpaths` of element `?` corresponding to internal \
lake zones must be zero, which is not the case for the column(s): 3 and 5.

    The snow redistribution routine of |snow| does not allow for any cycles.  Method
    |SRed.verify| checks for possible cycles by calling method |SRed.verify_order|:

    >>> zonetype(FIELD)
    >>> redistributionpaths([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
    >>> redistributionpaths.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: The weighting factors of parameter `redistributionpaths` of element `?` define at \
least one cycle: (1, 5) and (5, 1).

    Note that method |SRed.verify_order| relies on the |SRedOrder.update| method of
    parameter |SRedOrder| but resets its values afterwards:

    >>> derived.redistributionpathsorder.shape = (1, 2)
    >>> derived.redistributionpathsorder.values = [[0, 1]]
    >>> old_values = derived.redistributionpathsorder.values.copy()
    >>> redistributionpaths.values[1, -2:] = 1.0, 0.0
    >>> redistributionpaths.verify_order()
    Traceback (most recent call last):
    ...
    RuntimeError: The weighting factors of parameter `redistributionpaths` of element `?` define at \
least one cycle: (3, 5) and (5, 3).
    >>> derived.redistributionpathsorder
    redistributionpathsorder(0, 1)

    Parameter |SRed| provides two options to define the weighting factors with little
    effort.  The first option works by specifying the number of target zones.  If we
    set the number of target zones to one, |SRed| determines the next lower target for
    each zone that is not a dead-end:

    >>> land(True, True, True, True, False, True)
    >>> zoneheight(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
    >>> zonearea.values = 1.0
    >>> redistributionpaths(n_zones=1)

    For brevity, parameter |SRed| returns string representations based on these options
    when possible:

    >>> redistributionpaths
    redistributionpaths(n_zones=1)

    Clear the contents of the |KeywordArguments| object returned by property
    |SRed.keywordarguments| to see the actual parameter values:

    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    For two target zones (and identical zone areas), the weights of the next two lower
    zones are 0.5:

    >>> redistributionpaths(n_zones=2)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.5, 0.5, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.5, 0.5, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    You can specify an arbitrarily high numbes of target zones.  Parameter |SRed|
    adjusts the given value to the number of actually available target zones:

    >>> redistributionpaths(n_zones=999)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.25, 0.25, 0.25, 0.0, 0.25],
          [0.0, 0.0, 0.333333, 0.333333, 0.0, 0.333333],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    After defining the same elevation for the second and the third zone, the first zone
    redistributes the same snow amount to both of them.  Additionally, both zones
    redistribute their own snow to the fourth zone:

    >>> zoneheight(6.0, 5.0, 5.0, 3.0, 2.0, 1.0)

    >>> redistributionpaths(n_zones=1)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.5, 0.5, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(n_zones=2)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.5, 0.5, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(n_zones=999)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.25, 0.25, 0.25, 0.0, 0.25],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    For all zones lying on the same elevation, no redistribution occurs:

    >>> zoneheight(1.0)

    >>> redistributionpaths(n_zones=1)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths(0.0)

    >>> redistributionpaths(n_zones=2)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths(0.0)

    >>> redistributionpaths(n_zones=999)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths(0.0)

    The following examples demonstrate that the weights' calculation works well for
    unsorted elevations:

    >>> land(True, True, True, False, True, True)
    >>> zoneheight(5.0, 4.0, 1.0, 2.0, 6.0, 3.0)

    >>> redistributionpaths(n_zones=1)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(n_zones=2)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.5, 0.0, 0.0, 0.0, 0.5],
          [0.0, 0.0, 0.5, 0.0, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.5, 0.5, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(n_zones=999)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.333333, 0.333333, 0.0, 0.0, 0.333333],
          [0.0, 0.0, 0.5, 0.0, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.25, 0.25, 0.25, 0.0, 0.0, 0.25],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    For unequal zone areas, the calculated weights reflect the relations between the
    respective source and target zones.  The idea is that larger target zones have
    larger contact surfaces with their source zones than smaller ones.  This approach
    prevents building extreme snow towers in small target zones:

    >>> zonearea.values = 1.0, 2.0, 3.0, 4.0, 5.0, 6.0

    >>> redistributionpaths(n_zones=1)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(n_zones=2)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.25, 0.0, 0.0, 0.0, 0.75],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(n_zones=999)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.181818, 0.272727, 0.0, 0.0, 0.545455],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    Instead of supplying the number of target zones directly, on can define the maximum
    height of redistribution.  For a source zone at an elevation `x`, parameter |SRed|
    searches for zones that lie within the interval :math:`[x - d\\_height, x)`.  If it
    does not find one, it selects at least the next lower target zone(s), if existing:

    >>> zoneheight(5.0, 5.0, 1.0, 2.0, 6.0, 3.0)

    >>> redistributionpaths(d_height=0.0)
    >>> redistributionpaths
    redistributionpaths(d_height=0.0)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(d_height=2.0)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> redistributionpaths(d_height=10.0)
    >>> redistributionpaths.keywordarguments.clear()
    >>> redistributionpaths
    redistributionpaths([[0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    Passing multiple keyword arguments or a positional and a keyword argument at once
    results in the following error messages:

    >>> redistributionpaths(n_zones=1, d_height=0.0)
    Traceback (most recent call last):
    ...
    ValueError: Parameter `redistributionpaths` of element `?` accepts at most a single keyword \
argument but 2 are given.

    >>> redistributionpaths(0.0, d_height=0.0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `redistributionpaths` of element `?` both positional and keyword \
arguments are given, which is ambiguous.
    """

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.0

    _keywordarguments = parametertools.KeywordArguments(False)

    def __init__(self, subvars: parametertools.SubParameters[modeltools.Model]) -> None:
        super().__init__(subvars)
        self._keywordarguments = parametertools.KeywordArguments(False)

    def __call__(self, *args, **kwargs) -> None:
        self._keywordarguments.clear()
        if ("n_zones" in kwargs) or ("d_height" in kwargs):
            if args:
                super().__call__(*args, **kwargs)
            if len(kwargs) > 1:
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} accepts at most a "
                    f"single keyword argument but {len(kwargs)} are given."
                )
            self._keywordarguments.add(*tuple(kwargs.items())[0])
        try:
            if "n_zones" in kwargs:
                args = (self._prepare_nzones(kwargs.pop("n_zones")),)
            elif "d_height" in kwargs:
                args = (self._prepare_dheight(kwargs.pop("d_height")),)
            super().__call__(*args, **kwargs)
        except BaseException as exc:
            self._keywordarguments.clear()
            raise exc

    def _prepare_nzones(self, nzones: int) -> MatrixFloat:
        return self._prepare(self.subpars.numberzones.value * (nzones,))

    def _prepare_dheight(self, dheight: float) -> MatrixFloat:
        zoneheight = self.subpars.zoneheight.values
        nzones = (
            numpy.sum([(z > zoneheight) * (zoneheight >= (z - dheight))])
            for z in zoneheight
        )
        return self._prepare(tuple(max(n, 1) for n in nzones))

    def _prepare(self, nzones: tuple[int, ...]) -> MatrixFloat:
        control = self.subpars
        numberzones = control.numberzones.value
        zonearea = control.zonearea.values
        lands = control.land.values
        zoneheight = control.zoneheight.values
        zoneheight_sorted = numpy.sort(numpy.unique(zoneheight))[::-1]
        values = numpy.zeros((numberzones, numberzones), dtype=config.NP_FLOAT)
        zoneheight_min = numpy.min(zoneheight)
        for idx, (z_upper, land, nzone) in enumerate(zip(zoneheight, lands, nzones)):
            if land and (z_upper > zoneheight_min):
                for z_lower in zoneheight_sorted:
                    if z_upper > z_lower:
                        sel = lands * (z_upper > zoneheight) * (zoneheight >= z_lower)
                        jdxs = numpy.where(sel)[0]
                        if len(jdxs) >= nzone:
                            break
                values[idx, jdxs] = zonearea[jdxs] / numpy.sum(zonearea[jdxs])
        return values

    def verify(self) -> None:
        """Perform the usual parameter value verifications (implemented in method
        |Variable.verify|) and call methods |SRed.verify_sums|, |SRed.verify_lakes|,
        and |SRed.verify_order| for additional checks.

        See the main documentation on class |SRed| for further information.
        """
        super().verify()
        self.verify_sums()
        self.verify_lakes()
        self.verify_order()

    def verify_sums(self) -> None:
        """Check if the sums of all rows are either 0.0 (for dead-end zones) or 1.0
        (for redistributing zones).

        See the main documentation on class |SRed| for further information.
        """
        values = self.values
        sums = numpy.round(numpy.sum(values, axis=1), 12)
        errors = ~numpy.isin(sums, (0.0, 1.0))
        if numpy.any(errors):
            raise RuntimeError(
                f"The sum(s) of the following row(s) of parameter "
                f"{objecttools.elementphrase(self)} are neither 0.0 nor 1.0: "
                f"{objecttools.enumeration(numpy.where(errors)[0])}."
            )

    def verify_order(self) -> None:
        """Check if the weighting factors define any cycles.

        See the main documentation on class |SRed| for further information.
        """
        redistributionpathsorder = self.subpars.pars.derived.redistributionpathsorder
        values = exceptiontools.getattr_(redistributionpathsorder, "values", None)
        try:
            redistributionpathsorder.update()
        finally:
            if values is not None:
                redistributionpathsorder.shape = values.shape
                redistributionpathsorder.values = values

    def verify_lakes(self) -> None:
        """Check if any internal lake seems to be involved in snow redistribution.

        See the main documentation on class |SRed| for further information.
        """
        values = self.values
        for axis, string in ((1, "row"), (0, "column")):
            errors = self.subpars.water * (numpy.sum(values, axis=axis) > 0.0)
            if numpy.any(errors):
                raise RuntimeError(
                    f"Internal lake zones cannot be involved in snow "
                    f"redistribution, so the sums of all {string}s of parameter "
                    f"{objecttools.elementphrase(self)} corresponding to internal "
                    f"lake zones must be zero, which is not the case for the "
                    f"{string}(s): {objecttools.enumeration(numpy.where(errors)[0])}."
                )

    @property
    def keywordarguments(self) -> parametertools.KeywordArguments[float]:
        """A |KeywordArguments| object, providing the currently valid keyword argument.

        We reuse one of the example configurations of the main documentation on class
        |SRed|:

        >>> from hydpy.models.snow import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> numberzones(6)
        >>> land(True, True, True, True, False, True)
        >>> zoneheight(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
        >>> zonearea.values = 1.0

        After defining the values of parameter |SRed| via option `n_zones` or
        `d_height`, the returned |KeywordArguments| object contains the given
        name-value pair and indicates its validity by its |True|
        |KeywordArguments.valid| attribute:

        >>> redistributionpaths(n_zones=1)
        >>> redistributionpaths.keywordarguments
        KeywordArguments(n_zones=1)
        >>> redistributionpaths.keywordarguments.valid
        True

        Property |SRed.keywordarguments| checks if the last passed option still results
        in the currently defined parameter values and sets the |KeywordArguments.valid|
        flag to |False| if this is not the case.  We show this by modifying the zone
        heights specified by parameter |ZoneZ|:

        >>> zoneheight(4.0, 5.0, 4.0, 3.0, 2.0, 1.0)
        >>> redistributionpaths.keywordarguments
        KeywordArguments(n_zones=1)
        >>> redistributionpaths.keywordarguments.valid
        False

        After resetting the original values of |ZoneZ|, the |KeywordArguments.valid|
        flag of the returned |KeywordArguments| object is |True| again:

        >>> zoneheight(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
        >>> redistributionpaths.keywordarguments
        KeywordArguments(n_zones=1)
        >>> redistributionpaths.keywordarguments.valid
        True

        After defining the parameter values directly, the |KeywordArguments| object is
        always empty and invalid:

        >>> redistributionpaths(redistributionpaths.values)
        >>> redistributionpaths.keywordarguments
        KeywordArguments()
        >>> redistributionpaths.keywordarguments.valid
        False

        The same holds for erroneous keyword arguments:

        >>> redistributionpaths(n_zones=None)
        Traceback (most recent call last):
        ...
        TypeError: '>=' not supported between instances of 'int' and 'NoneType'
        >>> redistributionpaths.keywordarguments
        KeywordArguments()
        >>> redistributionpaths.keywordarguments.valid
        False
        """
        kwa = self._keywordarguments
        kwa.valid = True
        if len(kwa) != 1:
            kwa.valid = False
        else:
            for name, value in kwa:
                if name == "n_zones":
                    values = self._prepare_nzones(value)
                else:
                    values = self._prepare_dheight(value)
            if self != values:
                kwa.valid = False
        return kwa

    def __repr__(self) -> str:
        keywordarguments = self.keywordarguments
        if keywordarguments.valid:
            name, value = tuple(keywordarguments)[0]
            return f"{self.name}({name}={objecttools.repr_(value)})"
        return super().__repr__()


class NLayers(parametertools.NmbParameter):
    """Number of snow layers  [-]."""

    SPAN = (1, None)


class ZLayers(snow_parameters.Parameter1DLayers):
    """Height of each snow layer [m].

    You can use method |snow_model.BaseModel.prepare_layers| to determine the values of
    |ZLayers| based on the catchment's elevation distribution.
    """


class LayerArea(snow_parameters.Parameter1DLayers):
    """Area of snow layer as a percentage of total area [-].

    Calling method |snow_model.BaseModel.prepare_layers| to determine the values of
    parameter |ZLayers| also sets all entries of parameter |LayerArea| to the same
    average value.
    """

    SPAN = (0.0, 1.0)


class GradP(parametertools.Parameter):
    """Altitude gradient of precipitation [1/m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    INIT = 0.00041


class GradTMean(snow_parameters.Parameter1D366):
    """Altitude gradient of daily mean air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class GradTMin(snow_parameters.Parameter1D366):
    """Altitude gradient of daily minimum air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class GradTMax(snow_parameters.Parameter1D366):
    """Altitude gradient of daily maximum air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class MeanAnSolidPrecip(snow_parameters.Parameter1DLayers):
    """Mean annual solid precipitation [mm/a]."""

    SPAN = (0.0, None)


class CN1(parametertools.Parameter):
    """Temporal weighting coefficient for the snow pack's thermal state [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)


class CN2(parametertools.Parameter):
    """Degree-day melt coefficient [mm/°C/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class CN4(parametertools.Parameter):
    """Fraction of annual snowfall defining the melt threshold [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)


class Hysteresis(parametertools.Parameter):
    """Flag that indicates whether hysteresis of build-up and melting of the snow cover
    should be considered [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
    SPAN = (False, True)
    INIT = False
