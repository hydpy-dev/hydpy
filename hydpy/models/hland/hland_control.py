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
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
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

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (1e-10, None)


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

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)

    def __call__(self, *args, **kwargs) -> None:
        old_value = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new_value = self.value
        if new_value != old_value:
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


class ZoneType(parametertools.NameParameter):
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

        The default value for k of 0.009633 results from the default
        values for `alpha`, `hq` and `khq` given in HBV96:

        >>> k(hq=3.0, khq=0.17, alpha=1.0)
        >>> k
        k(0.009633)
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)
    INIT = 0.009633

    def __call__(self, *args, **kwargs) -> None:
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
            if math.isnan(alpha):
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
                    lower, -1.0 / numpy.log(1.0 - numpy.exp(-1.0 / lower)), numpy.inf  # type: ignore[operator, type-var]
                )
                lower = numpy.clip(lower, k1l, numpy.inf)  # type: ignore[type-var]
                lower[numpy.isnan(lower)] = k1l  # type: ignore[arg-type, index]
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
                lower[numpy.isnan(lower)] = k1l  # type: ignore[arg-type, index]
                lower = numpy.clip(lower, k1l, numpy.inf)  # type: ignore[type-var]
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
