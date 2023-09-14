# -*- coding: utf-8 -*-
"""
.. _`issue 67`: https://github.com/hydpy-dev/hydpy/issues/67
"""
# import...
# from standard library
import functools
import warnings
from typing import *

# from site-packages
import numpy

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *

# ...from hland
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_fixed
from hydpy.models.hland import hland_parameters
from hydpy.models.hland.hland_constants import ILAKE

if TYPE_CHECKING:
    from scipy import integrate
    from scipy import stats
else:
    integrate = exceptiontools.OptionalImport("scipy", ["scipy.integrate"], locals())
    stats = exceptiontools.OptionalImport("stats", ["scipy.stats"], locals())


class Area(parametertools.Parameter):
    """Subbasin area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NmbZones(parametertools.Parameter):
    """Number of zones (hydrological response units) in a subbasin [-].

    |NmbZones| determines the length of most 1-dimensional parameters and sequences.
    Usually, you should first prepare |NmbZones| and define the values of all
    1-dimensional parameters and sequences afterwards:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> icmax.shape
    (5,)
    >>> states.ic.shape
    (5,)

    Changing the value of |NmbZones| later reshapes the affected parameters and
    sequences and makes it necessary the reset their values:

    >>> icmax(2.0)
    >>> icmax
    icmax(2.0)
    >>> nmbzones(3)
    >>> icmax
    icmax(?)

    Re-defining the same value does not delete the already available data:

    >>> icmax(2.0)
    >>> nmbzones(3)
    >>> icmax
    icmax(2.0)

    The length of both axes of the 2-dimensional sequence |SRed| agree with |NmbZones|:

    >>> sred.shape
    (3, 3)

    Some 2-dimensional sequences reflect differences in snow accumulation within each
    zone. |NmbZones| prepares their shapes also, but therefore requires parameter
    |SClass| to provide the number of snow classes within each zone:

    >>> states.sp
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable `sp` \
can only be retrieved after it has been defined.

    >>> sclass.value = 2
    >>> nmbzones(4)
    >>> states.sp.shape
    (2, 4)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        old_value = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new_value = self.value
        if new_value != old_value:
            sclass = exceptiontools.getattr_(self.subpars.sclass, "value", None)
            for subpars in self.subpars.pars:
                for par in subpars:
                    if (par.NDIM == 1) and (par.name not in ("uh", "sfdist")):
                        par.shape = new_value
                    if par.NDIM == 2:
                        par.shape = new_value, new_value
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if (seq.NDIM == 1) and (seq.name not in ("quh", "sc")):
                        seq.shape = new_value
                    elif seq.NDIM == 2:
                        if sclass is not None:
                            seq.shape = sclass, new_value


class SClass(parametertools.Parameter):
    """Number of snow classes in each zone [-].

    |SClass| determines the length of the first axis of those 2-dimensional sequences
    reflecting differences in snow accumulation within each zone.  Therefore, it
    requires parameter |NmbZones| to provide the number of zones within the subbasin:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> sclass(1)
    >>> states.sp
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable `sp` \
can only be retrieved after it has been defined.

    >>> nmbzones.value = 2
    >>> sclass(3)
    >>> states.sp.shape
    (3, 2)

    Changing the value of |SClass| later reshapes the affected sequences and makes it
    necessary to reset their values:

    >>> states.sp = 2.0
    >>> states.sp
    sp([[2.0, 2.0],
        [2.0, 2.0],
        [2.0, 2.0]])
    >>> sclass(2)
    >>> states.sp
    sp([[nan, nan],
        [nan, nan]])

    Re-defining the same value does not delete the already available data:

    >>> states.sp = 2.0
    >>> sclass(2)
    >>> states.sp
    sp([[2.0, 2.0],
        [2.0, 2.0]])

    Additionally, |SClass| determines the shape of the control parameter |SFDist|:

    >>> sfdist.shape
    (2,)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)
    INIT = 1

    def __call__(self, *args, **kwargs):
        old_value = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new_value = self.value
        if new_value != old_value:
            self.subpars.sfdist.shape = new_value
            nmbzones = exceptiontools.getattr_(self.subpars.nmbzones, "value", None)
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 2:
                        if nmbzones is not None:
                            seq.shape = new_value, nmbzones


class ZoneType(parametertools.NameParameter):
    """Type of each zone [-].

    Parameter |ZoneType| relies on the integer constants defined in module
    |hland_constants| for representing zone types:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(6)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
    >>> zonetype.values
    array([1, 2, 3, 4, 4, 1])
    >>> zonetype
    zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
    """

    NDIM, TYPE, TIME = 1, int, None
    SPAN = (
        min(hland_constants.CONSTANTS.values()),
        max(hland_constants.CONSTANTS.values()),
    )
    CONSTANTS = hland_constants.CONSTANTS


class ZoneArea(hland_parameters.ParameterComplete):
    """Zone area [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    def trim(self, lower=None, upper=None):
        r"""Trim |ZoneArea| so that :math:`\Sigma ZoneArea = Area` holds and each zone
        area is non-negative.

        Our example basin is 6 km² large and consists of three zones:

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> area(6.0)
        >>> nmbzones(3)
        >>> zonetype(FIELD)

        First, an example with correct data:

        >>> zonearea(1.0, 2.0, 3.0)
        >>> zonearea
        zonearea(1.0, 2.0, 3.0)

        Second, an example with a single zone with a negative area:

        >>> zonearea(-1.0, 2.0, 4.0)
        >>> zonearea
        zonearea(0.0, 2.0, 4.0)

        Third, an example with too low zone areas:

        >>> zonearea(0.5, 1.0, 1.5)
        >>> zonearea
        zonearea(1.0, 2.0, 3.0)

        Fourth, an example with too high zone areas:

        >>> zonearea(2.0, 4.0, 6.0)
        >>> zonearea
        zonearea(1.0, 2.0, 3.0)

        Fifth, a combined example:

        >>> zonearea(-1.0, 1.0, 2.0)
        >>> zonearea
        zonearea(0.0, 2.0, 4.0)
        """
        area = self.subpars.area.value
        areas = numpy.clip(self.values, 0.0, numpy.inf)
        areas *= area / numpy.sum(areas)
        if lower is None:
            lower = areas
        if upper is None:
            upper = areas
        super().trim(lower, upper)


class Psi(parametertools.Parameter):
    """Fraction of the actual sealing of zones classified as |SEALED| [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.01, 1.0)
    INIT = 1.0


class ZoneZ(hland_parameters.ParameterComplete):
    """Zone elevation [100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ZRelP(parametertools.Parameter):
    """Subbasin-wide reference elevation level for precipitation [100m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class ZRelT(parametertools.Parameter):
    """Subbasin-wide reference elevation level for temperature [100m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class ZRelE(parametertools.Parameter):
    """Subbasin-wide reference elevation level for evaporation [100m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class PCorr(hland_parameters.ParameterComplete):
    """General precipitation correction factor [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class PCAlt(hland_parameters.ParameterComplete):
    """Elevation correction factor for precipitation [1/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class RfCF(hland_parameters.ParameterComplete):
    """Rainfall correction factor [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class SfCF(hland_parameters.ParameterComplete):
    """Snowfall correction factor [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class TCAlt(hland_parameters.ParameterComplete):
    """Elevation correction factor for temperature [-1°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ECorr(hland_parameters.ParameterNoGlacier):
    """General evaporation correction factor [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class ECAlt(hland_parameters.ParameterNoGlacier):
    """Elevation correction factor for evaporation [-1/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class EPF(hland_parameters.ParameterNoGlacier):
    """Decrease in potential evaporation due to precipitation [T/mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)


class ETF(hland_parameters.ParameterNoGlacier):
    """Temperature factor for evaporation [1/°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ERed(hland_parameters.ParameterSoil):
    """Factor for restricting actual to potential evaporation [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class TTIce(hland_parameters.ParameterLake):
    """Temperature threshold for lake evaporation [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class IcMax(hland_parameters.ParameterInterception):
    """Maximum interception storage [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class SFDist(parametertools.Parameter):
    """Distribution of snowfall [-].

    Parameter |SFDist| handles multiple adjustment factors for snowfall, one for each
    snow class, to introduce spatial heterogeneity to the snow depth within each zone.
    If we, for example, define three snow classes per zone but assign the neutral value
    1.0 to |SFDist|, all snow classes will receive the same amount of liquid and frozen
    snowfall (everything else will also be identical, so defining three snow classes
    instead of one is just a waste of computation time):

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> sclass(3)
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

    >>> from hydpy import print_values
    >>> def test(**kwargs):
    ...     for nmb in range(1, 6):
    ...         sclass(nmb)
    ...         sfdist(**kwargs)
    ...         print_values(sfdist.values)

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

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 1.0

    def __call__(self, *args, **kwargs) -> None:
        sclass = self.shape[0]
        idx = self._find_kwargscombination(
            args, kwargs, (set(("linear",)), set(("lognormal",)))
        )
        if idx is None:
            super().__call__(*args, **kwargs)
        elif idx == 0:
            super().__call__(self._linear(kwargs["linear"], sclass))
        else:
            super().__call__(self._lognormal(sclass, kwargs["lognormal"]))
        self.value /= sum(self.value) / sclass

    @staticmethod
    @functools.lru_cache()
    def _linear(factor, sclass):
        if sclass == 1:
            values = (1.0,)
        else:
            values = (
                factor * 2.0 * numpy.arange(sclass) / (sclass - 1) + (1.0 - factor)
            ) / sclass
        return values

    @staticmethod
    @functools.lru_cache()
    def _lognormal(sclass, scale: float) -> Vector[float]:
        values = numpy.ones(sclass, dtype=float)
        if scale > 0.0:
            for idx in range(sclass):
                values[idx] = integrate.quad(
                    lambda x: stats.lognorm.ppf(x, scale),
                    idx / sclass,
                    (idx + 1) / sclass,
                )[0]
        return values


class SMax(hland_parameters.ParameterLand):
    """Maximum snow water equivalent [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = numpy.inf


class SRed(parametertools.Parameter):
    """Snow redistribution paths [-].

    |SRed| is a 2-dimensional parameter that handles weighting factors for all possible
    zone connections.  The source zones vary on the rows and the target zones on the
    columns.  In the following example, zone one sends all snow available for
    redistribution to zone three.  Zone two sends 50 % to zone four and 50 % to zone
    five.  Zone six sends 40 % to zone two, 40 % to zone three, and 20 % to zone four:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(6)
    >>> zonetype(FIELD)
    >>> sred([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.5, 0.5, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
    >>> sred
    sred([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.5, 0.5, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])

    A zone can either redistribute no snow at all (we then call it a "dead end") or
    needs to send 100 % of the snow available for redistribution.  Hence, the sums of
    the individual rows must be either 0.0 or 1.0.  Method |SRed.verify| checks for
    possible violations of this requirement (by calling method |SRed.verify_sums|):

    >>> sred([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.4, 0.5],
    ...       [0.0, 0.1, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
    >>> sred.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: The sum(s) of the following row(s) of parameter `sred` of element \
`?` are neither 0.0 nor 1.0: 3 and 4.

    Zones of type |ILAKE| possess no snow module.  Hence, they never release any snow
    for redistribution and method |SRed.verify| checks for possible unused weighting
    factors in the relevant rows (by calling method |SRed.verify_lakes|):

    >>> zonetype(FIELD, FIELD, FIELD, ILAKE, FIELD, ILAKE)
    >>> sred([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    >>> sred.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: Internal lake zones cannot be involved in snow redistribution, so \
the sums of all rows of parameter `sred` of element `?` corresponding to internal lake \
zones must be zero, which is not the case for the row(s): 3.

    For the same reason, internal lakes cannot receive and accumulate any redistributed
    snow.  Therefore, method |SRed.verify| additionally checks for possible problematic
    weighting factors in the relevant columns (by calling method |SRed.verify_lakes|):

    >>> sred([[0.0, 0.5, 0.0, 0.0, 0.0, 0.5],
    ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    >>> sred.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: Internal lake zones cannot be involved in snow redistribution, so \
the sums of all columns of parameter `sred` of element `?` corresponding to internal \
lake zones must be zero, which is not the case for the column(s): 3 and 5.

    The snow redistribution routine of |hland| does not allow for any cycles.  Method
    |SRed.verify| checks for possible cycles by calling method |SRed.verify_order|:

    >>> zonetype(FIELD)
    >>> sred([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
    ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
    >>> sred.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: The weighting factors of parameter `sred` of element `?` define at \
least one cycle: (1, 5) and (5, 1).

    Note that method |SRed.verify_order| relies on the |SRedOrder.update| method of
    parameter |SRedOrder| but resets its values afterwards:

    >>> derived.sredorder.shape = (1, 2)
    >>> derived.sredorder.values = [[0, 1]]
    >>> old_values = derived.sredorder.values.copy()
    >>> sred.values[1, -2:] = 1.0, 0.0
    >>> sred.verify_order()
    Traceback (most recent call last):
    ...
    RuntimeError: The weighting factors of parameter `sred` of element `?` define at \
least one cycle: (3, 5) and (5, 3).
    >>> derived.sredorder
    sredorder(0, 1)

    Parameter |SRed| provides two options to define the weighting factors with little
    effort.  The first option works by specifying the number of target zones.  If we
    set the number of target zones to one, |SRed| determines the next lower target for
    each zone that is not a dead-end:

    >>> zonetype(GLACIER, FIELD, FOREST, SEALED, ILAKE, FOREST)
    >>> zonez(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
    >>> zonearea.values = 1.0
    >>> sred(n_zones=1)

    For brevity, parameter |SRed| returns string representations based on these options
    when possible:

    >>> sred
    sred(n_zones=1)

    Clear the contents of the |KeywordArguments| object returned by property
    |SRed.keywordarguments| to see the actual parameter values:

    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    For two target zones (and identical zone areas), the weights of the next two lower
    zones are 0.5:

    >>> sred(n_zones=2)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.5, 0.5, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.5, 0.5, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    You can specify an arbitrarily high numbes of target zones.  Parameter |SRed|
    adjusts the given value to the number of actually available target zones:

    >>> sred(n_zones=999)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.25, 0.25, 0.25, 0.0, 0.25],
          [0.0, 0.0, 0.333333, 0.333333, 0.0, 0.333333],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    After defining the same elevation for the second and the third zone, the first zone
    redistributes the same snow amount to both of them.  Additionally, both zones
    redistribute their own snow to the fourth zone:

    >>> zonez(6.0, 5.0, 5.0, 3.0, 2.0, 1.0)

    >>> sred(n_zones=1)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.5, 0.5, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    >>> sred(n_zones=2)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.5, 0.5, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    >>> sred(n_zones=999)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.25, 0.25, 0.25, 0.0, 0.25],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.5, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    For all zones lying on the same elevation, no redistribution occurs:

    >>> zonez(1.0)

    >>> sred(n_zones=1)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred(0.0)

    >>> sred(n_zones=2)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred(0.0)

    >>> sred(n_zones=999)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred(0.0)

    The following examples demonstrate that the weights' calculation works well for
    unsorted elevations:

    >>> zonetype(FIELD, FOREST, FOREST, ILAKE, GLACIER, SEALED)
    >>> zonez(5.0, 4.0, 1.0, 2.0, 6.0, 3.0)

    >>> sred(n_zones=1)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> sred(n_zones=2)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.5, 0.0, 0.0, 0.0, 0.5],
          [0.0, 0.0, 0.5, 0.0, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.5, 0.5, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> sred(n_zones=999)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.333333, 0.333333, 0.0, 0.0, 0.333333],
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

    >>> sred(n_zones=1)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> sred(n_zones=2)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.25, 0.0, 0.0, 0.0, 0.75],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> sred(n_zones=999)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.181818, 0.272727, 0.0, 0.0, 0.545455],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    Instead of supplying the number of target zones directly, on can define the maximum
    height of redistribution.  For a source zone at an elevation `x`, parameter |SRed|
    searches for zones that lie within the interval :math:`[x - d\\_height, x)`.  If it
    does not find one, it selects at least the next lower target zone(s), if existing:

    >>> zonez(5.0, 5.0, 1.0, 2.0, 6.0, 3.0)

    >>> sred(d_height=0.0)
    >>> sred
    sred(d_height=0.0)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> sred(d_height=2.0)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    >>> sred(d_height=10.0)
    >>> sred.keywordarguments.clear()
    >>> sred
    sred([[0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])

    Passing multiple keyword arguments or a positional and a keyword argument at once
    results in the following error messages:

    >>> sred(n_zones=1, d_height=0.0)
    Traceback (most recent call last):
    ...
    ValueError: Parameter `sred` of element `?` accepts at most a single keyword \
argument but 2 are given.

    >>> sred(0.0, d_height=0.0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `sred` of element `?` both positional and keyword \
arguments are given, which is ambiguous.
    """

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)
    INIT = 0.0

    _keywordarguments = parametertools.KeywordArguments(False)

    def __init__(self, subvars) -> None:
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
                args = [self._prepare_nzones(kwargs.pop("n_zones"))]
            elif "d_height" in kwargs:
                args = [self._prepare_dheight(kwargs.pop("d_height"))]
            super().__call__(*args, **kwargs)
        except BaseException as exc:
            self._keywordarguments.clear()
            raise exc

    def _prepare_nzones(self, nzones: int) -> Matrix[float]:
        return self._prepare(self.subpars.nmbzones.value * (nzones,))

    def _prepare_dheight(self, dheight: float) -> Matrix[float]:
        zonez = self.subpars.zonez.values
        nzones = (numpy.sum((z > zonez) * (zonez >= (z - dheight))) for z in zonez)
        return self._prepare(tuple(max(n, 1) for n in nzones))

    def _prepare(self, nzones: Tuple[int, ...]) -> Matrix[float]:
        nmbzones = self.subpars.nmbzones.value
        zonearea = self.subpars.zonearea.value
        types_ = self.subpars.zonetype.value
        zonez = self.subpars.zonez.value
        zonez_sorted = numpy.sort(numpy.unique(zonez))[::-1]
        values = numpy.zeros((nmbzones, nmbzones), dtype=float)
        zonez_min = numpy.min(zonez)
        for idx, (z_upper, type_, nzone) in enumerate(zip(zonez, types_, nzones)):
            if (type_ != ILAKE) and (z_upper > zonez_min):
                for z_lower in zonez_sorted:
                    if z_upper > z_lower:
                        sel = (types_ != ILAKE) * (z_upper > zonez) * (zonez >= z_lower)
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
        sredorder = self.subpars.pars.derived.sredorder
        values = exceptiontools.getattr_(sredorder, "values", None)
        try:
            sredorder.update()
        finally:
            if values is not None:
                sredorder.shape = values.shape
                sredorder.values = values

    def verify_lakes(self) -> None:
        """Check if any internal lake seems to be involved in snow redistribution.

        See the main documentation on class |SRed| for further information.
        """
        values = self.values
        is_lake = self.subpars.zonetype.values == ILAKE
        for axis, string in ((1, "row"), (0, "column")):
            errors = is_lake * (numpy.sum(values, axis=axis) > 0.0)
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

        >>> from hydpy.models.hland import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(GLACIER, FIELD, FOREST, SEALED, ILAKE, FOREST)
        >>> zonez(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
        >>> zonearea.values = 1.0

        After defining the values of parameter |SRed| via option `n_zones` or
        `d_height`, the returned |KeywordArguments| object contains the given
        name-value pair and indicates its validity by its |True|
        |KeywordArguments.valid| attribute:

        >>> sred(n_zones=1)
        >>> sred.keywordarguments
        KeywordArguments(n_zones=1)
        >>> sred.keywordarguments.valid
        True

        Property |SRed.keywordarguments| checks if the last passed option still results
        in the currently defined parameter values and sets the |KeywordArguments.valid|
        flag to |False| if this is not the case.  We show this by modifying the zone
        heights specified by parameter |ZoneZ|:

        >>> zonez(4.0, 5.0, 4.0, 3.0, 2.0, 1.0)
        >>> sred.keywordarguments
        KeywordArguments(n_zones=1)
        >>> sred.keywordarguments.valid
        False

        After resetting the original values of |ZoneZ|, the |KeywordArguments.valid|
        flag of the returned |KeywordArguments| object is |True| again:

        >>> zonez(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
        >>> sred.keywordarguments
        KeywordArguments(n_zones=1)
        >>> sred.keywordarguments.valid
        True

        After defining the parameter values directly, the |KeywordArguments| object is
        always empty and invalid:

        >>> sred(sred.values)
        >>> sred.keywordarguments
        KeywordArguments()
        >>> sred.keywordarguments.valid
        False

        The same holds for erroneous keyword arguments:

        >>> sred(n_zones=None)
        Traceback (most recent call last):
        ...
        TypeError: '>=' not supported between instances of 'int' and 'NoneType'
        >>> sred.keywordarguments
        KeywordArguments()
        >>> sred.keywordarguments.valid
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


class TT(hland_parameters.ParameterComplete):
    """Temperature threshold for snow/rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class TTInt(hland_parameters.ParameterComplete):
    """Temperature interval with a mixture of snow and rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class DTTM(hland_parameters.ParameterLand):
    """Difference between |TTM| and |TT| [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class CFMax(hland_parameters.ParameterLand):
    """Average degree day factor for snow (on glaciers or not) [mm/°C/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)


class CFVar(hland_parameters.ParameterLand):
    """Annual variability of |CFMax| [mm/°C/T].

    Use positive values for the northern and negative values for the southern
    hemisphere.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, True, (None, None)
    INIT = 0.0


class GMelt(hland_parameters.ParameterGlacier):
    """Degree day factor for glacial ice [mm/°C/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)


class GVar(hland_parameters.ParameterGlacier):
    """Annual variability of |GMelt| [mm/°C/T].

    Use positive values for the northern and negative values for the southern
    hemisphere.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, True, (None, None)
    INIT = 0.0


class CFR(hland_parameters.ParameterLand):
    """Refreezing factor for water stored within the snow layer [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class WHC(hland_parameters.ParameterLand):
    """Relative water holding capacity of the snow layer [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class FC(hland_parameters.ParameterSoil):
    """Maximum soil moisture content (field capacity) [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class LP(hland_parameters.ParameterSoil):
    """Relative limit for potential evaporation [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class Beta(hland_parameters.ParameterSoil):
    """Nonlinearity parameter of the soil routine [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class PercMax(parametertools.Parameter):
    """Maximum percolation rate [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)


class CFlux(hland_parameters.ParameterSoil):
    """Capacity (maximum) of the capillary return flux [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)


class RespArea(parametertools.Parameter):
    """Flag to enable the contributing area approach [-]."""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (None, None)


class RecStep(parametertools.Parameter):
    """Number of internal computation steps per simulation time step [-].

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> simulationstep("12h")
    >>> recstep(4.2)
    >>> recstep
    recstep(4.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, True, (1, None)


class Alpha(parametertools.Parameter):
    """Nonlinearity parameter of the upper zone layer [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class K(parametertools.Parameter):
    """Recession coefficient of the upper zone layer [1/T/mm^alpha].

    In addition to the |Parameter| call method, it is possible to
    set the value of parameter |K| in accordance to the keyword arguments
    `khq`, `hq` and (optionally) `alpha`:

    Parameter |K| allows defining its value via the keyword arguments `khq`, `hq` and
    (optionally) `alpha`:

        :math:`K = \\frac{HQ}{(HQ/KHQ)^{1+Alpha}}`

    Examples:

        When directly setting the value of parameter |K|, one should be be aware of
        its time dependence:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> k(2.0)
        >>> k
        k(2.0)
        >>> k.value
        1.0

        Alternatively, one can specify the mentioned three keyword arguments:

        >>> k(hq=10.0, khq=2.0, alpha=1.0)
        >>> k
        k(0.4)
        >>> k.value
        0.2

        If a value for keyword argument `alpha` is missing, parameter |K| tries to
        query it from parameter |Alpha|.

        >>> alpha(2.0)
        >>> k(hq=10.0, khq=2.0)
        >>> k
        k(0.08)
        >>> k.value
        0.04

        The following exceptions occur for wrong combinations of keyword arguments or
        when |Alpha| is not ready (still has the value |numpy.nan|):

        >>> k(wrong=1)
        Traceback (most recent call last):
        ...
        ValueError: For parameter `k` of element `?` a value can be set directly or \
indirectly by using the keyword arguments `khq` and `hq`.

        >>> k(hq=10.0)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `k` of element `?`, \
at least the keywords arguments `khq` and `hq` must be given.

        >>> import numpy
        >>> alpha(numpy.nan)
        >>> k(hq=10.0, khq=2.0)
        Traceback (most recent call last):
        ...
        RuntimeError: For the alternative calculation of parameter `k` of element `?`, \
either the keyword argument `alpha` must be given or the value of parameter `alpha` \
must be defined beforehand.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)

    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError as exc:
            counter = ("khq" in kwargs) + ("hq" in kwargs)
            if counter == 0:
                raise ValueError(
                    f"For parameter {objecttools.elementphrase(self)} a "
                    f"value can be set directly or indirectly by using "
                    f"the keyword arguments `khq` and `hq`."
                ) from exc
            if counter == 1:
                raise ValueError(
                    f"For the alternative calculation of parameter "
                    f"{objecttools.elementphrase(self)}, at least the "
                    f"keywords arguments `khq` and `hq` must be given."
                ) from exc
            alpha = float(
                kwargs.get(
                    "alpha",
                    exceptiontools.getattr_(self.subpars.alpha, "value", numpy.nan),
                )
            )
            if numpy.isnan(alpha):
                raise RuntimeError(
                    f"For the alternative calculation of parameter "
                    f"{objecttools.elementphrase(self)}, either the "
                    f"keyword argument `alpha` must be given or the value "
                    f"of parameter `alpha` must be defined beforehand."
                ) from exc
            khq = float(kwargs["khq"])
            hq = float(kwargs["hq"])
            self(hq / ((hq / khq) ** (alpha + 1.0)))


class SGR(hland_parameters.ParameterUpperZone):
    """Threshold content of |SUZ| for the generation of surface runoff [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class K0(hland_parameters.ParameterUpperZone):
    """Storage time for surface runoff [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (None, None)

    # CONTROLPARAMETERS = (K1,)   defined below

    def trim(self, lower=None, upper=None):
        r"""Trim |K0| following :math:`K^* \leq K0 \leq K1` with
        :math:`K^* = -1/ln \left( 1 - e^{-1 / k1} \right)`.

        The additional restriction :math:`K^*` serves to prevent the storage |SUZ|
        from taking on negative values (see `issue 67`_).

        >>> from hydpy.models.hland import *
        >>> simulationstep("1d")
        >>> parameterstep("1h")
        >>> nmbzones(5)
        >>> zonetype(FIELD)
        >>> k1(48.0, 48.0, 48.0, 48.0, nan)
        >>> k0(24.0, 36.0, 48.0, 72.0, 72.0)
        >>> k0
        k0(25.730308, 36.0, 48.0, 48.0, 72.0)
        """
        if lower is None:
            try:
                lower = -1.0 / numpy.log(1.0 - numpy.exp(-1.0 / self.subpars.k1.values))
            except exceptiontools.AttributeNotReady:
                lower = 0.0
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.k1, "value", None)
        super().trim(lower, upper)


class H1(hland_parameters.ParameterUpperZone):
    """Outlet level of the reservoir for simulating surface flow [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class TAb1(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating surface flow [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)


class TVs1(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating percolation from the surface flow module
    [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)


class K1(hland_parameters.ParameterUpperZone):
    """Storage time for interflow [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (None, None)

    # CONTROLPARAMETERS = (K0, K2,)   defined below
    FIXEDPARAMETERS = (hland_fixed.K1L,)

    def trim(self, lower=None, upper=None):
        r"""Trim |K1| following :math:`max (K0, K^*) \leq K1 \leq K2` with
        :math:`K^* = max \left( -1/ln \left( 1 - e^{-1 / k0} \right), K1L \right)`.

        The additional restriction :math:`K^*` serves to prevent the storage |SUZ|
        from taking on negative values (see `issue 67`_).

        >>> from hydpy.models.hland import *
        >>> simulationstep("1d")
        >>> parameterstep("1h")
        >>> nmbzones(9)
        >>> zonetype(FIELD)
        >>> k1(24.0, 24.0, 72.0, 120.0, 24.0, 24.0, 120.0, nan, nan)
        >>> k1
        k1(34.624681, 34.624681, 72.0, 120.0, 34.624681, 34.624681, 120.0, nan,
           nan)
        >>> k1.values = nan
        >>> k0(48.0, 24.0, 24.0, 24.0, nan, 24.0, nan, 24.0, nan)
        >>> k2(96.0, 96.0, 96.0, 96.0, nan, nan, 96.0, 96.0, nan)
        >>> k1(24.0, 24.0, 72.0, 120.0, 24.0, 24.0, 120.0, nan, nan)
        >>> k1
        k1(48.0, 52.324614, 72.0, 96.0, 34.624681, 52.324614, 96.0, nan, nan)
        """
        if lower is None:
            k1l = self.subpars.pars.fixed.k1l.value
            try:
                lower = self.subpars.k0.values
            except exceptiontools.AttributeNotReady:
                lower = k1l
            else:
                lower = numpy.clip(
                    lower,
                    -1.0 / numpy.log(1.0 - numpy.exp(-1.0 / lower)),
                    numpy.inf,
                )
                lower = numpy.clip(lower, k1l, numpy.inf)
                lower[numpy.isnan(lower)] = k1l
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.k2, "values", None)
        super().trim(lower, upper)


class SG1Max(hland_parameters.ParameterUpperZone):
    """Maximum content of the fast response groundwater reservoir |SG1| [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class H2(hland_parameters.ParameterUpperZone):
    """Outlet level of the reservoir for simulating interflow [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class TAb2(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating interflow [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)


class TVs2(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating percolation from the interflow module
    [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)


class K4(parametertools.Parameter):
    """Recession coefficient of the lower zone layer [1/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)


class K2(hland_parameters.ParameterUpperZone):
    """Storage time for quick response baseflow [T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, False, (None, None)

    # CONTROLPARAMETERS = (K1, K3,)   defined below
    FIXEDPARAMETERS = (hland_fixed.K1L,)

    def trim(self, lower=None, upper=None):
        r"""Trim |K2| following :math:`max(K1, K1L) \leq K2 \leq K3`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1d")
        >>> parameterstep("1h")
        >>> nmbzones(6)
        >>> zonetype(FIELD)
        >>> k2(12.0, 12.0, 12.0, nan, 96.0, 120.0)
        >>> k2
        k2(34.624681, 34.624681, 34.624681, nan, 96.0, 120.0)
        >>> k2.values = nan
        >>> k1(24.0, 72.0, nan, nan, nan, 72.0)
        >>> k3(96.0)
        >>> k2(12.0, 12.0, 12.0, nan, 96.0, 120.0)
        >>> k2
        k2(34.624681, 72.0, 34.624681, nan, 96.0, 96.0)
        """
        if lower is None:
            k1l = self.subpars.pars.fixed.k1l.value
            try:
                lower = self.subpars.k1.values
            except exceptiontools.AttributeNotReady:
                lower = k1l
            else:
                lower[numpy.isnan(lower)] = k1l
                lower = numpy.clip(lower, k1l, numpy.inf)
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.k3, "value", None)
        super().trim(lower, upper)


class K3(parametertools.Parameter):
    """Storage time for delayed baseflow [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (1.0, None)

    CONTROLPARAMETERS = (K2,)
    FIXEDPARAMETERS = (hland_fixed.K1L,)

    def trim(self, lower=None, upper=None):
        r"""Trim |K3| in accordance with :math:`max(K2, K1L) \leq K3`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1d")
        >>> parameterstep("1h")
        >>> nmbzones(3)
        >>> k3(12.0)
        >>> k3
        k3(34.624681)
        >>> k3.values = nan
        >>> k2(36.0, 36.0, nan)
        >>> k2.value[0] /= 3.0
        >>> k3(12.0)
        >>> k3
        k3(36.0)
        >>> k2.values[1] /= 3.0
        >>> k3(12.0)
        >>> k3
        k3(34.624681)
        """
        if lower is None:
            k1l = self.subpars.pars.fixed.k1l.value
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error")
                    lower = numpy.nanmax(self.subpars.k2.values)
            except (exceptiontools.AttributeNotReady, RuntimeWarning):
                lower = k1l
            else:
                if not k1l < lower:
                    lower = k1l
        super().trim(lower, upper)


class Gamma(parametertools.Parameter):
    """Nonlinearity parameter of the lower zone layer [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class MaxBaz(parametertools.Parameter):
    """Base length of the triangle unit hydrograph [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class NmbStorages(parametertools.Parameter):
    """Number of storages of the linear storage cascade [-].

    Defining a value for parameter |NmbStorages| automatically sets the shape of state
    sequence |SC|:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbstorages(5)
    >>> states.sc.shape
    (5,)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.sequences.states.sc.shape = self.value


K0.CONTROLPARAMETERS = (K1,)
K1.CONTROLPARAMETERS = (
    K0,
    K2,
)
K2.CONTROLPARAMETERS = (
    K1,
    K3,
)
