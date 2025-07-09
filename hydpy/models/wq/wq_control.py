# pylint: disable=missing-module-docstring
# import...
# ...from HydPy
from hydpy.core import parametertools

# ...from wq
from hydpy.models.wq import wq_variables


class NmbTrapezes(parametertools.NmbParameter):
    """Number of trapezes defining the cross section [-]."""

    SPAN = (1, None)


class BottomLevels(wq_variables.MixinShape, parametertools.Parameter):
    """The bottom level for each trapeze [m].

    If water levels are essential, we encourage using the sea level as a reference.  If
    not (as for common hydrological routing approaches), one could also set the lowest
    trapeze's bottom level to zero.
    """

    TYPE, TIME, SPAN = float, None, (None, None)


class BottomWidths(wq_variables.MixinShape, parametertools.Parameter):
    """The bottom width for each trapeze [m].


    For example, when dealing with the second trapeze, the corresponding value of
    |BottomWidths| represents the sum of the trapeze's partial bottoms on the left and
    right sides of the first trapeze.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class SideSlopes(wq_variables.MixinShape, parametertools.Parameter):
    """The side slope for each trapeze[-].

    A value of zero corresponds to a rectangular shape.  A value of two corresponds to
    a half-meter elevation increase for each additional meter distance from the
    trapeze's centre.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class StricklerCoefficients(wq_variables.MixinShape, parametertools.Parameter):
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
