# pylint: disable=missing-module-docstring
# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import variabletools

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


class Heights(wq_variables.MixinWidths, parametertools.SortedParameter):
    """The measurement heights of the widths defining the cross section [m].

    If water levels are essential, we encourage using the sea level as a reference.  If
    not (as for common hydrological routing approaches), one could also set the lowest
    tabulated level to zero.
    """

    TYPE, TIME, SPAN = float, None, (None, None)


class FlowWidths(wq_variables.MixinWidths, parametertools.SortedParameter):
    """The widths of those subareas of the cross section involved in water routing
    [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)


class TotalWidths(wq_variables.MixinWidths, parametertools.SortedParameter):
    """The widths of the total cross section [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)


class Transitions(parametertools.Parameter):
    """Indexes that mark the transitions between separately calculated cross-section
    sectors [m].

    According to the Python convention, the index :math:`0` would mark the first, and
    the index :math:`n - 1` would mark the last height/width pair.  However, precisely
    these two values are disallowed for reasons we explain in the following.

    Parameter |Transitions| defines the transitions between all neighbouring sectors.
    Hence, one does not need to specify any value if there is only one sector:

    >>> from hydpy.models.wq import *
    >>> parameterstep()
    >>> nmbsectors(1)
    >>> transitions
    transitions()

    In such cases, it is okay to pass nothing when using the usual parameter value
    setting syntax:

    >>> transitions()
    >>> transitions
    transitions()

    The number of the required values depends on |NmbSectors|, while the range of the
    allowed values depends on |NmbWidths|:

    >>> nmbwidths(7)
    >>> nmbsectors(4)
    >>> transitions(1, 4, 5)
    >>> transitions
    transitions(1, 4, 5)

    The index value :math:`0` is not allowed because there is no sector below the
    "lowest" height/width pair:

    >>> transitions(0, 4, 6)
    Traceback (most recent call last):
    ...
    ValueError: The smallest possible index value of parameter `transitions` of \
element `?` is 1, but 0 is given.

    >>> transitions
    transitions(-999999)

    The same logic holds for the "highest" height/width pair:

    >>> transitions(1, 4, 6)
    Traceback (most recent call last):
    ...
    ValueError: The largest possible index value of parameter `transitions` of element \
`?` is 5 (NmbWidths - 2), but 6 is given.

    >>> transitions
    transitions(-999999)

    Besides this, one must ensure that the index values are correctly sorted:

    >>> transitions(1, 4, 4)
    Traceback (most recent call last):
    ...
    ValueError: The index values given to parameter `transitions` of element `?` are \
not strictly rising (1, 4, and 4).

    >>> transitions
    transitions(-999999)
    """

    NDIM, TYPE, TIME, SPAN = 1, int, None, (1, None)

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, NmbSectors):
            self.__hydpy__change_shape_if_necessary__((p.value - 1,))

    def __call__(self, *args, **kwargs) -> None:
        if (self.shape[0] > 0) or args or kwargs:
            super().__call__(*args, **kwargs)
            if self.shape[0] > 0:
                values = self.values
                if not numpy.all(values[:-1] < values[1:]):
                    self.values = variabletools.INT_NAN
                    raise ValueError(
                        f"The index values given to parameter "
                        f"{objecttools.elementphrase(self)} are not strictly rising "
                        f"({objecttools.enumeration(values)})."
                    )
                if values[0] < 1:
                    self.values = variabletools.INT_NAN
                    raise ValueError(
                        f"The smallest possible index value of parameter "
                        f"{objecttools.elementphrase(self)} is 1, but {values[0]} is "
                        f"given."
                    )
                if values[-1] > (max_ := self.subpars.nmbwidths.value - 2):
                    self.values = variabletools.INT_NAN
                    raise ValueError(
                        f"The largest possible index value of parameter "
                        f"{objecttools.elementphrase(self)} is {max_} (NmbWidths - 2), "
                        f"but {values[-1]} is given."
                    )

    def trim(self, lower=None, upper=None) -> bool:
        """Regular trimming is disabled in favour of the special checks described in the
        main documentation of parameter |Transitions|."""
        return False

    def __repr__(self) -> str:
        if (self.subpars.nmbsectors == 1) and (self.shape[0] == 0):
            return f"{self.name}()"
        return super().__repr__()


class BottomLevels(wq_variables.MixinTrapezes, parametertools.SortedParameter):
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
