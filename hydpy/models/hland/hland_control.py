# -*- coding: utf-8 -*-
"""
.. _`issue 67`: https://github.com/hydpy-dev/hydpy/issues/67
"""
# import...
# from standard library
import warnings

# from site-packages
import numpy

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from hland
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_fixed
from hydpy.models.hland import hland_parameters


class Area(parametertools.Parameter):
    """Subbasin area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NmbZones(parametertools.Parameter):
    """Number of zones (hydrological response units) in a subbasin [-].

    Note that |NmbZones| determines the length of most 1-dimensional parameters and
    sequences.  Usually, you should first prepare |NmbZones| and define the values of
    all 1-dimensional parameters and sequences afterwards:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> icmax.shape
    (5,)
    >>> states.ic.shape
    (5,)

    Changing the value of "N" later reshapes the affected parameters and sequences and
    makes it necessary the reset their values:

    >>> icmax(2.0)
    >>> icmax
    icmax(2.0)
    >>> nmbzones(3)
    >>> icmax
    icmax(?)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to |NmbZones| instances within
        parameter control files.  Sets the shape of most 1-dimensional
        parameter objects (except |UH|) and sequence objects (except |QUH|)
        additionally.
        """
        super().__call__(*args, **kwargs)
        for subpars in self.subpars.pars.model.parameters:
            for par in subpars:
                if (par.NDIM > 0) and (par.name != "uh"):
                    par.shape = self.value
        for subseqs in self.subpars.pars.model.sequences:
            for seq in subseqs:
                if (seq.NDIM > 0) and (seq.name not in ("quh", "sc")):
                    seq.shape = self.value


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

    Defining a value for parameter |NmbStorages| automatically sets the
    shape of state sequence |SC|:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbstorages(5)
    >>> states.sc.shape
    (5,)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.sequences.states.sc.shape = self


class Abstr(parametertools.Parameter):
    """Abstraction of water from computed outflow [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


K0.CONTROLPARAMETERS = (K1,)
K1.CONTROLPARAMETERS = (
    K0,
    K2,
)
K2.CONTROLPARAMETERS = (
    K1,
    K3,
)
