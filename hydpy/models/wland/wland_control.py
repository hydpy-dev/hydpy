# pylint: disable=missing-module-docstring
# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.models.wland import wland_parameters
from hydpy.models.wland import wland_constants
from hydpy.models.wland.wland_constants import *


class AT(parametertools.Parameter):
    """Total area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class NU(parametertools.Parameter):
    """Number of hydrological response units [-].

    Parameter |NU| automatically sets the length of most 1-dimensional parameters and
    sequences of |wland.DOCNAME.long|:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(3)
    >>> lt.shape
    (3,)
    >>> states.ic.shape
    (3,)

    Changing the value of parameter |NU| reshapes the related parameters and sequences
    and eventually deletes predefined values:

    >>> states.ic = 1.0
    >>> states.ic
    ic(1.0, 1.0, 1.0)
    >>> nu(2)
    >>> states.ic
    ic(nan, nan)

    Redefining the same value for parameter |NU| does not affect any related parameter
    and sequence object:

    >>> states.ic = 1.0
    >>> states.ic
    ic(1.0, 1.0)
    >>> nu(2)
    >>> states.ic
    ic(1.0, 1.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs) -> None:
        old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new = self._get_value()
        if new != old:
            for subpars in self.subpars.pars.model.parameters:
                for par in subpars:
                    if (par.NDIM == 1) and (
                        not isinstance(par, parametertools.MonthParameter)
                    ):
                        par._set_shape(new)
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq._set_shape(new)


class LT(parametertools.NameParameter):
    """Landuse type [-].

    For better readability, use the land-use-related constants defined in module
    |wland_constants| to set the individual hydrological response units' land-use
    types:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(12)
    >>> lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE,
    ...    WETLAND, TREES, CONIFER, DECIDIOUS, MIXED, WATER)
    >>> lt
    lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE, WETLAND, TREES,
       CONIFER, DECIDIOUS, MIXED, WATER)

    Note that |wland| generally requires a single surface water storage unit, which
    must be placed at the last position.  Trying to set another land type causes the
    following error:

    >>> lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE,
    ...    WETLAND, TREES, CONIFER, DECIDIOUS, MIXED, MIXED)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the land use types via parameter `lt` of element \
`?`, the following error occurred: The last land use type must be `WATER`, but \
`MIXED` is given.

    Trying to define multiple such units results in the following error:

    >>> lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE,
    ...    WETLAND, TREES, CONIFER, DECIDIOUS, WATER, WATER)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the land use types via parameter `lt` of element \
`?`, the following error occurred: W-Land requires a single surface water storage \
unit, but 2 units are defined as such.
    """

    constants = wland_constants.LANDUSE_CONSTANTS

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        try:
            is_water = self.values == WATER
            if not is_water[-1]:
                lt = wland_constants.LANDUSE_CONSTANTS.value2name[self.values[-1]]
                raise ValueError(
                    f"The last land use type must be `WATER`, but `{lt}` is given."
                )
            if sum(is_water) > 1:
                raise ValueError(
                    f"W-Land requires a single surface water storage unit, but "
                    f"{sum(is_water)} units are defined as such."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the land use types via parameter "
                f"{objecttools.elementphrase(self)}"
            )


class ER(wland_parameters.LanduseParameterLand):
    """Elevated region [-]."""

    NDIM, TYPE, TIME, SPAN = 1, bool, None, (None, None)
    INIT = False


class AUR(parametertools.Parameter):
    """Relative area of each hydrological response unit [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class GL(parametertools.Parameter):
    """The lowland region's average ground level [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Ensure |GL| is above |BL|.

        >>> from hydpy.models.wland import *
        >>> parameterstep()

        >>> gl(2.0)
        >>> gl
        gl(2.0)

        >>> bl.value = 4.0
        >>> gl(3.0)
        >>> gl
        gl(4.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.bl, "value", None)
        return super().trim(lower, upper)


class BL(parametertools.Parameter):
    """Channel bottom level [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Ensure |BL| is below |GL|.

        >>> from hydpy.models.wland import *
        >>> parameterstep()

        >>> from hydpy.models.wland import *
        >>> parameterstep()

        >>> bl(4.0)
        >>> bl
        bl(4.0)

        >>> gl.value = 2.0
        >>> bl(3.0)
        >>> bl
        bl(2.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.gl, "value", None)
        return super().trim(lower, upper)


class CP(parametertools.Parameter):
    """Factor for correcting precipitation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class LAI(wland_parameters.LanduseMonthParameter):
    """Leaf area index [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)


class IH(parametertools.Parameter):
    """Interception capacity with respect to the leaf surface area [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class TT(parametertools.Parameter):
    """Threshold temperature for snow/rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class TI(parametertools.Parameter):
    """Temperature interval with a mixture of snow and rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class DDF(wland_parameters.LanduseParameterLand):
    """Day degree factor [mm/°C/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)


class DDT(parametertools.Parameter):
    """Day degree threshold temperature [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class CWE(parametertools.Parameter):
    """Wetness index parameter for the elevated region [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1.0, None)


class CW(parametertools.Parameter):
    """Wetness index parameter for the lowland region [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1.0, None)


class CV(parametertools.Parameter):
    """Vadose zone relaxation time constant for the lowland region [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class CGE(parametertools.Parameter):
    """Groundwater reservoir constant for the elevated region [mm T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class CG(parametertools.Parameter):
    """Groundwater reservoir constant for the lowland region [mm T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class RG(parametertools.Parameter):
    """Groundwater reservoir restriction [-]."""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (None, None)


class CGF(parametertools.Parameter):
    """Groundwater reservoir flood factor [1/mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class DGC(parametertools.Parameter):
    """Direct groundwater connect [-]."""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (None, None)


class CQ(parametertools.Parameter):
    """Quickflow reservoir relaxation time [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class B(wland_parameters.SoilParameter):
    """Pore size distribution parameter [-].

    Parameter |B| comes with the following default values:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> b.print_defaults()
    SAND: 4.05
    LOAMY_SAND: 4.38
    SANDY_LOAM: 4.9
    SILT_LOAM: 5.3
    LOAM: 5.39
    SANDY_CLAY_LOAM: 7.12
    SILT_CLAY_LOAM: 7.75
    CLAY_LOAM: 8.52
    SANDY_CLAY: 10.4
    SILTY_CLAY: 10.4
    CLAY: 11.4

    See the documentation on class |SoilParameter| for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    _SOIL2VALUE = {
        SAND: 4.05,
        LOAMY_SAND: 4.38,
        SANDY_LOAM: 4.9,
        SILT_LOAM: 5.3,
        LOAM: 5.39,
        SANDY_CLAY_LOAM: 7.12,
        SILT_CLAY_LOAM: 7.75,
        CLAY_LOAM: 8.52,
        SANDY_CLAY: 10.4,
        SILTY_CLAY: 10.4,
        CLAY: 11.4,
    }


class PsiAE(wland_parameters.SoilParameter):
    """Air entry pressure [mm].

    Parameter |PsiAE| comes with the following default values:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> psiae.print_defaults()
    SAND: 121.0
    LOAMY_SAND: 90.0
    SANDY_LOAM: 218.0
    SILT_LOAM: 786.0
    LOAM: 478.0
    SANDY_CLAY_LOAM: 299.0
    SILT_CLAY_LOAM: 356.0
    CLAY_LOAM: 630.0
    SANDY_CLAY: 153.0
    SILTY_CLAY: 490.0
    CLAY: 405.0

    See the documentation on class |SoilParameter| for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    _SOIL2VALUE = {
        SAND: 121.0,
        LOAMY_SAND: 90.0,
        SANDY_LOAM: 218.0,
        SILT_LOAM: 786.0,
        LOAM: 478.0,
        SANDY_CLAY_LOAM: 299.0,
        SILT_CLAY_LOAM: 356.0,
        CLAY_LOAM: 630.0,
        SANDY_CLAY: 153.0,
        SILTY_CLAY: 490.0,
        CLAY: 405.0,
    }


class ThetaS(wland_parameters.SoilParameter):
    """Soil moisture content at saturation [-].

    Parameter |ThetaS| comes with the following default values:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> thetas.print_defaults()
    SAND: 0.395
    LOAMY_SAND: 0.41
    SANDY_LOAM: 0.435
    SILT_LOAM: 0.485
    LOAM: 0.451
    SANDY_CLAY_LOAM: 0.42
    SILT_CLAY_LOAM: 0.477
    CLAY_LOAM: 0.476
    SANDY_CLAY: 0.426
    SILTY_CLAY: 0.492
    CLAY: 0.482

    See the documentation on class |SoilParameter| for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, 1.0)

    _SOIL2VALUE = {
        SAND: 0.395,
        LOAMY_SAND: 0.41,
        SANDY_LOAM: 0.435,
        SILT_LOAM: 0.485,
        LOAM: 0.451,
        SANDY_CLAY_LOAM: 0.42,
        SILT_CLAY_LOAM: 0.477,
        CLAY_LOAM: 0.476,
        SANDY_CLAY: 0.426,
        SILTY_CLAY: 0.492,
        CLAY: 0.482,
    }

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |ThetaS| following :math:`1e^{-6} \leq ThetaS \leq 1.0` and,
        if |ThetaR| exists for the relevant application model, also following
        :math:`ThetaR \leq ThetaS`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()

        >>> thetas(0.0)
        >>> thetas
        thetas(0.000001)

        >>> thetar.value = 0.5
        >>> thetas(0.4)
        >>> thetas
        thetas(0.5)

        >>> thetas(soil=SANDY_LOAM)
        >>> thetas
        thetas(0.5)

        >>> thetas(1.01)
        >>> thetas
        thetas(1.0)
        """
        if lower is None:
            if exceptiontools.hasattr_(self.subpars, "thetar"):
                lower = exceptiontools.getattr_(self.subpars.thetar, "value", 1e-6)
            else:
                lower = 1e-6
        return super().trim(lower, upper)


class ThetaR(parametertools.Parameter):
    """Residual soil moisture deficit at tension saturation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-6, None)
    INIT = 0.01

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |ThetaR| following :math:`1e^{-6} \leq ThetaR \leq ThetaS`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetar(0.0)
        >>> thetar
        thetar(0.000001)
        >>> thetas(0.41)
        >>> thetar(0.42)
        >>> thetar
        thetar(0.41)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.thetas, "value", None)
        return super().trim(lower, upper)


class AC(parametertools.Parameter):
    """Air capacity for the elevated region [mm].

    ToDo: We should principally derive |AC| from |SoilParameter|, but
          :cite:t:`ref-Brauer2014` provides no soil-specific default values for it
          because it is not part of the original WALRUS model.  Do we want to determine
          consistent ones by ourselves?
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 200.0


class Zeta1(parametertools.Parameter):
    """Curvature parameter of the evapotranspiration reduction function [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.02


class Zeta2(parametertools.Parameter):
    """Inflection point of the evapotranspiration reduction function [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 400.0


class SH(parametertools.Parameter):
    """General smoothing parameter related to the height of water columns [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class ST(parametertools.Parameter):
    """General smoothing parameter related to temperature [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
