"""
.. _`issue 67`: https://github.com/hydpy-dev/hydpy/issues/67
"""

from __future__ import annotations
import functools
import math
import warnings

import numpy

from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_fixed
from hydpy.models.hland import hland_parameters
from hydpy.models.hland import hland_variables
from hydpy.models.hland.hland_constants import ILAKE

if TYPE_CHECKING:
    from scipy import integrate
    from scipy import stats
else:
    integrate = exceptiontools.OptionalImport("scipy", ["scipy.integrate"], locals())
    stats = exceptiontools.OptionalImport("stats", ["scipy.stats"], locals())


class Area(parametertools.Parameter):
    """Subbasin area [km²]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (1e-10, None)


class NmbZones(parametertools.NmbParameter):
    """Number of zones (hydrological response units) in a subbasin [-]."""

    SPAN = (1, None)


class SClass(parametertools.NmbParameter):
    """Number of snow classes in each zone [-]."""

    SPAN = (1, None)
    INIT = 1


class ZoneType(hland_variables.MixinZones, parametertools.NameParameter):
    """Type of each zone [-].

    Parameter |ZoneType| relies on the integer constants defined in module
    |hland_constants| for representing zone types:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(6)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
    >>> from hydpy import print_vector
    >>> print_vector(zonetype.values)
    1, 2, 3, 4, 4, 1
    >>> zonetype
    zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
    """

    constants = hland_constants.CONSTANTS


class ZoneArea(hland_parameters.ParameterComplete):
    """Zone area [km²]."""

    TYPE: Final = float
    SPAN = (0.0, None)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
        return super().trim(lower, upper)


class Psi(parametertools.Parameter):
    """Fraction of the actual sealing of zones classified as |SEALED| [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.01, 1.0)
    INIT = 1.0


class ZoneZ(hland_parameters.ParameterComplete):
    """Zone elevation [100m]."""

    TYPE: Final = float


class PCorr(hland_parameters.ParameterComplete):
    """General precipitation correction factor [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0


class PCAlt(hland_parameters.ParameterComplete):
    """Elevation correction factor for precipitation [1/100m]."""

    TYPE: Final = float
    INIT = 0.1


class RfCF(hland_parameters.ParameterComplete):
    """Rainfall correction factor [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0


class SfCF(hland_parameters.ParameterComplete):
    """Snowfall correction factor [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0


class TCorr(hland_parameters.ParameterNoGlacier):
    """General temperature correction addend [-]."""

    TYPE: Final = float
    INIT = 0.0


class TCAlt(hland_parameters.ParameterComplete):
    """Elevation correction factor for temperature [-1°C/100m]."""

    TYPE: Final = float
    INIT = 0.6


class IcMax(hland_parameters.ParameterInterception):
    """Maximum interception storage [mm]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class SFDist(hland_variables.MixinSnowClasses, parametertools.Parameter):
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

    >>> from hydpy import print_vector
    >>> def test(**kwargs):
    ...     for nmb in range(1, 6):
    ...         sclass(nmb)
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
    while the last snow class receives twice the zone's average snowfall.  |SFDist|
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

    The second available keyword is `lognormal`.  Here, |SFDist| calculates factors
    resulting in a lognormal distribution of snowfall, similarly as implemented in
    the COSERO model :cite:p:`ref-Frey2015CoseroSnow`.  Again, the lowest possible
    value, 0.0, results in uniform snow distributions:

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

    Theoretically, higher scale factors are allowed.  However, 1.0 results in highly
    heterogeneous snow distributions already.

    The string representation reflects the given keyword argument:

    >>> sfdist
    sfdist(lognormal=1.0)
    >>> sclass(3)
    >>> sfdist
    sfdist(?)
    >>> sfdist(linear=0.2)
    >>> sfdist
    sfdist(linear=0.2)
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0

    def _set_linear(self, *, linear: float) -> dict[str, float]:
        self.values = self._linear(linear, self.shape[0])
        self._normalise()
        return {"linear": linear}

    def _set_lognormal(self, *, lognormal: float) -> dict[str, float]:
        self.values = self._lognormal(self.shape[0], lognormal)
        self._normalise()
        return {"lognormal": lognormal}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("linear"), setter=_set_linear
        ),
        parametertools.KeywordGroup(
            parametertools.Keyword("lognormal"), setter=_set_lognormal
        ),
    )

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    @overload
    def __call__(self, *, linear: float) -> None: ...

    @overload
    def __call__(self, *, lognormal: float) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        super().__call__(*args, **kwargs)
        if not self.keywordhandler.recorded.valid:
            self._normalise()

    def _normalise(self) -> None:
        self.values /= sum(self.values) / self.shape[0]

    @staticmethod
    @functools.lru_cache
    def _linear(factor: float, sclass: int) -> VectorInputFloat:
        if sclass == 1:
            return (1.0,)
        return (
            factor * 2.0 * numpy.arange(sclass) / (sclass - 1) + (1.0 - factor)
        ) / sclass

    @staticmethod
    @functools.lru_cache
    def _lognormal(sclass: int, scale: float) -> VectorFloat:
        values = numpy.ones(sclass, dtype=config.NP_FLOAT)
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

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = numpy.inf


class SRed(hland_variables.MixinZonesZones, parametertools.Parameter):
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
    RuntimeError: The sums of rows 3 and 4 of parameter `sred` of element `?` are \
neither `0.0` nor `1.0`.

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
the sums of all rows of parameter `sred` of element `?` corresponding to internal \
lake zones must be zero, which is not the case for row 3.

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
lake zones must be zero, which is not the case for columns 3 and 5.

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
least one cycle: `(1, 5)` and `(5, 1)`.

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
least one cycle: `(3, 5)` and `(5, 3)`.
    >>> derived.sredorder
    sredorder(0, 1)

    You can alternatively define the weighting factors via the keyword arguments
    `n_zones` and `d_height`.  The first option works by specifying the number of
    target zones.  If we set the number of target zones to one, |SRed| determines the
    next lower target for each zone that is not a dead-end:

    >>> zonetype(GLACIER, FIELD, FOREST, SEALED, ILAKE, FOREST)
    >>> zonez(6.0, 5.0, 4.0, 3.0, 2.0, 1.0)
    >>> zonearea.values = 1.0
    >>> sred(n_zones=1)
    >>> sred
    sred(n_zones=1)
    >>> from hydpy import print_matrix
    >>> print_matrix(sred.values)
    | 0.0, 1.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 1.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    For two target zones (and identical zone areas), the weights of the next two lower
    zones are 0.5:

    >>> sred(n_zones=2)
    >>> print_matrix(sred.values)
    | 0.0, 0.5, 0.5, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.5, 0.5, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.5, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    You can specify an arbitrarily high number of target zones.  Parameter |SRed|
    adjusts the given value to the number of actually available target zones:

    >>> sred(n_zones=999)
    >>> print_matrix(sred.values)
    | 0.0, 0.25, 0.25, 0.25, 0.0, 0.25 |
    | 0.0, 0.0, 0.333333, 0.333333, 0.0, 0.333333 |
    | 0.0, 0.0, 0.0, 0.5, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    After defining the same elevation for the second and the third zone, the first zone
    redistributes the same snow amount to both of them.  Additionally, both zones
    redistribute their own snow to the fourth zone:

    >>> zonez(6.0, 5.0, 5.0, 3.0, 2.0, 1.0)

    >>> sred(n_zones=1)
    >>> print_matrix(sred.values)
    | 0.0, 0.5, 0.5, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 1.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 1.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    >>> sred(n_zones=2)
    >>> print_matrix(sred.values)
    | 0.0, 0.5, 0.5, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.5, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.5, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    >>> sred(n_zones=999)
    >>> print_matrix(sred.values)
    | 0.0, 0.25, 0.25, 0.25, 0.0, 0.25 |
    | 0.0, 0.0, 0.0, 0.5, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.5, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    For all zones lying on the same elevation, no redistribution occurs, regardless of
    the number of target zones:

    >>> zonez(1.0)
    >>> sred(n_zones=999)
    >>> print_matrix(sred.values)
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |

    The following examples demonstrate that the weights' calculation works well for
    unsorted elevations:

    >>> zonetype(FIELD, FOREST, FOREST, ILAKE, GLACIER, SEALED)
    >>> zonez(5.0, 4.0, 1.0, 2.0, 6.0, 3.0)

    >>> sred(n_zones=1)
    >>> print_matrix(sred.values)
    | 0.0, 1.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 1.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    >>> sred(n_zones=2)
    >>> print_matrix(sred.values)
    | 0.0, 0.5, 0.0, 0.0, 0.0, 0.5 |
    | 0.0, 0.0, 0.5, 0.0, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.5, 0.5, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    >>> sred(n_zones=999)
    >>> print_matrix(sred.values)
    | 0.0, 0.333333, 0.333333, 0.0, 0.0, 0.333333 |
    | 0.0, 0.0, 0.5, 0.0, 0.0, 0.5 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.25, 0.25, 0.25, 0.0, 0.0, 0.25 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    For unequal zone areas, the calculated weights reflect the relations between the
    respective source and target zones.  The idea is that larger target zones have
    larger contact surfaces with their source zones than smaller ones.  This approach
    prevents building extreme snow towers in small target zones:

    >>> zonearea.values = 1.0, 2.0, 3.0, 4.0, 5.0, 6.0

    >>> sred(n_zones=1)
    >>> print_matrix(sred.values)
    | 0.0, 1.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 1.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    >>> sred(n_zones=2)
    >>> print_matrix(sred.values)
    | 0.0, 0.25, 0.0, 0.0, 0.0, 0.75 |
    | 0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    >>> sred(n_zones=999)
    >>> print_matrix(sred.values)
    | 0.0, 0.181818, 0.272727, 0.0, 0.0, 0.545455 |
    | 0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    Instead of supplying the number of target zones directly, one can define the maximum
    height of redistribution.  For a source zone at an elevation `x`, parameter |SRed|
    searches for zones that lie within the interval :math:`[x - d\\_height, x)`.  If it
    does not find one, it selects at least the next lower target zone(s), if existing:

    >>> zonez(5.0, 5.0, 1.0, 2.0, 6.0, 3.0)

    >>> sred(d_height=0.0)
    >>> sred
    sred(d_height=0.0)
    >>> print_matrix(sred.values)
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    >>> sred(d_height=2.0)
    >>> print_matrix(sred.values)
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.333333, 0.666667, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    >>> sred(d_height=10.0)
    >>> print_matrix(sred.values)
    | 0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667 |
    | 0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 |
    | 0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5 |
    | 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 |

    |SRed| does not update its values when the values of |NmbZones|, |ZoneArea|,
    |ZoneType|, or |ZoneZ| change later.  Then, its string representation shows the
    actual weighting factors instead of the outdated option:

    >>> sred
    sred(d_height=10.0)
    >>> zonearea.values[0] = 0.0
    >>> sred
    sred([[0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.333333, 0.0, 0.0, 0.666667],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          [0.083333, 0.166667, 0.25, 0.0, 0.0, 0.5],
          [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])
    """

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.0

    def _set_n_zones(self, *, n_zones: int) -> dict[str, int]:
        self(self._prepare_nzones(n_zones))
        return {"n_zones": n_zones}

    def _set_d_height(self, *, d_height: float) -> dict[str, float]:
        self(self._prepare_dheight(d_height))
        return {"d_height": d_height}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("n_zones", type_=int),
            dependencies=("nmbzones", "zonearea", "zonetype", "zonez"),
            setter=_set_n_zones,
        ),
        parametertools.KeywordGroup(
            parametertools.Keyword("d_height"),
            dependencies=("nmbzones", "zonearea", "zonetype", "zonez"),
            setter=_set_d_height,
        ),
    )

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    @overload
    def __call__(self, *, n_zones: int) -> None: ...

    @overload
    def __call__(self, *, d_height: float) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        super().__call__(*args, **kwargs)

    def _prepare_nzones(self, nzones: int) -> MatrixFloat:
        return self._prepare(self.subpars.nmbzones.value * (nzones,))

    def _prepare_dheight(self, dheight: float) -> MatrixFloat:
        zonez = self.subpars.zonez.values
        nzones = (numpy.sum([(z > zonez) * (zonez >= (z - dheight))]) for z in zonez)
        return self._prepare(tuple(max(n, 1) for n in nzones))

    def _prepare(self, nzones: tuple[int, ...]) -> MatrixFloat:
        nmbzones = self.subpars.nmbzones.value
        zonearea = self.subpars.zonearea.value
        types_ = self.subpars.zonetype.value
        zonez = self.subpars.zonez.value
        zonez_sorted = numpy.sort(numpy.unique(zonez))[::-1]
        values = numpy.zeros((nmbzones, nmbzones), dtype=config.NP_FLOAT)
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
            rows = numpy.where(errors)[0]
            inflect = objecttools.Inflect
            n = len(rows)
            raise RuntimeError(
                f"The {inflect.plural('sum', n)} of "
                f"{inflect.listing('row', rows, backticks=False)} of parameter "
                f"{objecttools.elementphrase(self)} {inflect.plural('is', n)} "
                f"neither `0.0` nor `1.0`."
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
                idxs = numpy.where(errors)[0]
                raise RuntimeError(
                    f"Internal lake zones cannot be involved in snow "
                    f"redistribution, so the sums of all {string}s of parameter "
                    f"{objecttools.elementphrase(self)} corresponding to internal "
                    f"lake zones must be zero, which is not the case for "
                    f"{objecttools.Inflect.listing(string, idxs, backticks=False)}."
                )


class TT(hland_parameters.ParameterComplete):
    """Temperature threshold for snow/rain [°C]."""

    TYPE: Final = float
    INIT = 0.0


class TTInt(hland_parameters.ParameterComplete):
    """Temperature interval with a mixture of snow and rain [°C]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.0


class DTTM(hland_parameters.ParameterLand):
    """Difference between |TTM| and |TT| [°C]."""

    TYPE: Final = float
    INIT = 0.0


class CFMax(hland_parameters.ParameterLand):
    """Average degree day factor for snow (on glaciers or not) [mm/°C/T]."""

    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)
    INIT = 3.5


class CFVar(hland_parameters.ParameterLand):
    """Annual variability of |CFMax| [mm/°C/T].

    Use positive values for the northern and negative values for the southern
    hemisphere.
    """

    TYPE: Final = float
    TIME = True
    INIT = 0.0


class GMelt(hland_parameters.ParameterGlacier):
    """Degree day factor for glacial ice [mm/°C/T]."""

    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)
    INIT = 3.5


class GVar(hland_parameters.ParameterGlacier):
    """Annual variability of |GMelt| [mm/°C/T].

    Use positive values for the northern and negative values for the southern
    hemisphere.
    """

    TYPE: Final = float
    TIME = True
    INIT = 0.0


class CFR(hland_parameters.ParameterLand):
    """Refreezing factor for water stored within the snow layer [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.05


class WHC(hland_parameters.ParameterLand):
    """Relative water holding capacity of the snow layer [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.1


class FC(hland_parameters.ParameterSoil):
    """Maximum soil moisture content (field capacity) [mm]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 200


class Beta(hland_parameters.ParameterSoil):
    """Nonlinearity parameter of the soil routine [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 2.0


class PercMax(parametertools.Parameter):
    """Maximum percolation rate [mm/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)


class CFlux(hland_parameters.ParameterSoil):
    """Capacity (maximum) of the capillary return flux [mm/T]."""

    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)
    INIT = 1.0


class RespArea(parametertools.Parameter):
    """Flag to enable the contributing area approach [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool


class RecStep(parametertools.Parameter):
    """Number of internal computation steps per simulation time step [-].

    The default value of 1440 internal computation steps per day corresponds to 1
    computation step per minute.

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> simulationstep("12h")
    >>> recstep(4.2)
    >>> recstep
    recstep(4.0)
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    TIME = True
    SPAN = (1, None)
    INIT = 1440


class Alpha(parametertools.Parameter):
    """Nonlinearity parameter of the upper zone layer [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0


class K(parametertools.Parameter):
    """Recession coefficient of the upper zone layer [1/T/mm^alpha].

    You can alternatively define |K| via the keyword arguments `khq`, `hq`, and
    (optionally) `alpha`:

        :math:`K = \\frac{HQ}{(HQ/KHQ)^{1+Alpha}}`

    Examples:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> k(hq=10.0, khq=2.0, alpha=1.0)
        >>> k
        k(khq=2.0, hq=10.0, alpha=1.0)
        >>> from hydpy import round_
        >>> round_(k.value)
        0.2

        If a value for keyword argument `alpha` is missing, parameter |K| tries to
        query it from parameter |Alpha|.  The string representation then includes
        the queried value so that it does not depend on later changes of |Alpha|:

        >>> alpha(2.0)
        >>> k(hq=10.0, khq=2.0)
        >>> k
        k(khq=2.0, hq=10.0, alpha=2.0)
        >>> round_(k.value)
        0.04

        >>> import numpy
        >>> alpha(numpy.nan)
        >>> k(hq=10.0, khq=2.0)
        Traceback (most recent call last):
        ...
        RuntimeError: For the alternative calculation of parameter `k` of element `?`, \
either the keyword argument `alpha` must be given or the value of parameter `alpha` \
must be defined beforehand.

        The default value for k of 0.009633 (for a parameter step of one day) results
        from the default values for `alpha`, `hq` and `khq` given in HBV96 (the actual
        value is half as large due to the simulation step of 12 hours):

        >>> k(hq=3.0, khq=0.17, alpha=1.0)
        >>> round_(k.value)
        0.004817
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)
    INIT = 0.009633

    def _set_khq_hq(
        self, *, khq: float, hq: float, alpha: float | None = None
    ) -> dict[str, float]:
        if alpha is None:
            alpha = exceptiontools.getattr_(self.subpars.alpha, "value", numpy.nan)
        alpha = float(alpha)
        if math.isnan(alpha):
            raise RuntimeError(
                f"For the alternative calculation of parameter "
                f"{objecttools.elementphrase(self)}, either the keyword argument "
                f"`alpha` must be given or the value of parameter `alpha` must be "
                f"defined beforehand."
            )
        khq, hq = float(khq), float(hq)
        self(hq / ((hq / khq) ** (alpha + 1.0)))
        return {"khq": khq, "hq": hq, "alpha": alpha}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("khq", time=True),
            parametertools.Keyword("hq", time=True),
            parametertools.Keyword("alpha", optional=True),
            setter=_set_khq_hq,
        )
    )

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    @overload
    def __call__(self, *, khq: float, hq: float, alpha: float = ...) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        super().__call__(*args, **kwargs)


class SGR(hland_parameters.ParameterUpperZone):
    """Threshold content of |SUZ| for the generation of surface runoff [mm]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class K0(hland_parameters.ParameterUpperZone):
    """Storage time for surface runoff [T]."""

    TYPE: Final = float
    TIME = False

    # defined at the bottom of the file:
    CONTROLPARAMETERS: tuple[type[K1]]

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
        return super().trim(lower, upper)


class H1(hland_parameters.ParameterUpperZone):
    """Outlet level of the reservoir for simulating surface flow [mm]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class TAb1(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating surface flow [T]."""

    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)


class TVs1(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating percolation from the surface flow module
    [T]."""

    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)


class K1(hland_parameters.ParameterUpperZone):
    """Storage time for interflow [T]."""

    TYPE: Final = float
    TIME = False

    # defined at the bottom of the file:
    CONTROLPARAMETERS: tuple[type[K0], type[K2]]
    FIXEDPARAMETERS = (hland_fixed.K1L,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
                    lower, -1.0 / numpy.log(1.0 - numpy.exp(-1.0 / lower)), numpy.inf
                )
                lower = numpy.clip(lower, k1l, numpy.inf)
                lower[numpy.isnan(lower)] = k1l
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.k2, "values", None)
        return super().trim(lower, upper)


class SG1Max(hland_parameters.ParameterUpperZone):
    """Maximum content of the fast response groundwater reservoir |SG1| [mm]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class H2(hland_parameters.ParameterUpperZone):
    """Outlet level of the reservoir for simulating interflow [mm]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class TAb2(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating interflow [T]."""

    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)


class TVs2(hland_parameters.ParameterUpperZone):
    """Recession coefficient for simulating percolation from the interflow module
    [T]."""

    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)


class K4(parametertools.Parameter):
    """Recession coefficient of the lower zone layer [1/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)
    INIT = 0.01


class K2(hland_parameters.ParameterUpperZone):
    """Storage time for quick response baseflow [T]."""

    TYPE: Final = float
    TIME = False

    # defined at the bottom of the file:
    CONTROLPARAMETERS: tuple[type[K1], type[K3]]
    FIXEDPARAMETERS = (hland_fixed.K1L,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
        return super().trim(lower, upper)


class K3(parametertools.Parameter):
    """Storage time for delayed baseflow [T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    SPAN = (1.0, None)

    CONTROLPARAMETERS = (K2,)
    FIXEDPARAMETERS = (hland_fixed.K1L,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
        return super().trim(lower, upper)


class Gamma(parametertools.Parameter):
    """Nonlinearity parameter of the lower zone layer [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
