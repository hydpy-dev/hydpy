# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class Area(parametertools.Parameter):
    """Subbasin area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class IMax(parametertools.Parameter):
    """Interception store capacity [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class X1(parametertools.Parameter):
    """Maximum capacity of the production storage [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class X2(parametertools.Parameter):
    """Groundwater exchange coefficient (positive for water imports, negative for
    exports) [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (None, None)

    @classmethod
    def get_timefactor(cls) -> float:
        r"""Factor to adjust values of |X2| to differences between |parameterstep| and
        |simulationstep|.

        Method |X2.get_timefactor| of class |X2| extends method
        |Parameter.get_timefactor| of class |Parameter| according to
        :math:`x2_{sim} = x2_{par} \cdot (sim/par)^{0.125}` :cite:p:`ref-Ficchí2017`:

        >>> from hydpy.models.gland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> x2(7.0)
        >>> x2
        x2(7.0)
        >>> from hydpy import round_
        >>> round_(x2.value)
        4.70513
        """
        return super().get_timefactor() ** 0.125


class X3(parametertools.Parameter):
    """One timestep ahead maximum capacity of the routing store [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)

    @classmethod
    def get_timefactor(cls) -> float:
        r"""Factor to adjust values of |X3| to differences between |parameterstep| and
        |simulationstep|.

        Method |X3.get_timefactor| of class |X3| extends method
        |Parameter.get_timefactor| of class |Parameter| according to
        :math:`x3_{sim} = x3_{par} \cdot (sim/par)^{-0.25}` :cite:p:`ref-Ficchí2017`:

        >>> from hydpy.models.gland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> x3(30.0)
        >>> x3
        x3(30.0)
        >>> from hydpy import round_
        >>> round_(x3.value)
        66.400915
        """
        return super().get_timefactor() ** -0.25


class X5(parametertools.Parameter):
    """Intercatchment exchange threshold [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class X6(parametertools.Parameter):
    """Coefficient for emptying the exponential store [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
