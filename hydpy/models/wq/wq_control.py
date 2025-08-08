# pylint: disable=missing-module-docstring
# import...
# ...from HydPy
from hydpy.core import parametertools

# ...from wq
from hydpy.models.wq import wq_variables


class NmbTrapezes(parametertools.NmbParameter):
    """Number of trapezes defining the cross section [-]."""

    SPAN = (1, None)


class NmbWidths(parametertools.NmbParameter):
    """Number of widths that define the cross section [-]."""

    SPAN = (2, None)


class NmbSectors(parametertools.NmbParameter):
    """Number of the separately calculated sectors of the cross section [-]."""

    SPAN = (1, None)


class Heights(wq_variables.MixinWidths, parametertools.Parameter):
    """The measurement heights of the widths defining the cross section [m].

    If water levels are essential, we encourage using the sea level as a reference.  If
    not (as for common hydrological routing approaches), one could also set the lowest
    tabulated level to zero.
    """

    TYPE, TIME, SPAN = float, None, (None, None)


class FlowWidths(wq_variables.MixinWidths, parametertools.Parameter):
    """The widths of those subareas of the cross section involved in water routing
    [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)


class TotalWidths(wq_variables.MixinWidths, parametertools.Parameter):
    """The widths of the total cross section [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)


class Transitions(parametertools.Parameter):
    """The measurement heights that mark the transitions between separately calculated
    cross section sectors [m]."""

    NDIM, TYPE, TIME, SPAN = 1, int, None, (0.0, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, NmbSectors):
            self.__hydpy__change_shape_if_necessary__((p.value - 1,))


class BottomLevels(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The bottom level for each trapeze [m].

    If water levels are essential, we encourage using the sea level as a reference.  If
    not (as for common hydrological routing approaches), one could also set the lowest
    trapeze's bottom level to zero.
    """

    TYPE, TIME, SPAN = float, None, (None, None)


class BottomWidths(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The bottom width for each trapeze [m].


    For example, when dealing with the second trapeze, the corresponding value of
    |BottomWidths| represents the sum of the trapeze's partial bottoms on the left and
    right sides of the first trapeze.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class SideSlopes(wq_variables.MixinTrapezes, parametertools.Parameter):
    """The side slope for each trapeze[-].

    A value of zero corresponds to a rectangular shape.  A value of two corresponds to
    a half-meter elevation increase for each additional meter distance from the
    trapeze's centre.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class StricklerCoefficients(
    wq_variables.MixinTrapezesOrSectors, parametertools.Parameter
):
    """Manning-Strickler coefficient for each trapeze [m^(1/3)/s].

    The higher the coefficient's value, the higher the calculated discharge.  Typical
    values range from 20 to 80.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class BottomSlope(parametertools.Parameter):
    r"""Bottom slope [-].

    :math:`BottomSlope = \frac{elevation_{start} - elevation_{end}}{length}`
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class ChannelDepth(parametertools.Parameter):
    """Channel depth [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestHeight(parametertools.Parameter):
    """The height of the weir's crest above the channel bottom [m].

    Set |CrestHeight| to zero for channels without weirs.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestHeightTolerance(parametertools.Parameter):
    """Smoothing parameter related to the difference between the water depth and the
    crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BankfullDischarge(parametertools.Parameter):
    """Bankfull discharge [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)


class DischargeExponent(parametertools.Parameter):
    """Exponent of the water depth-discharge relation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5
