# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *


class CatchmentArea(parametertools.Parameter):
    """Size of the catchment draining into the channel [km²]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class NmbSegments(parametertools.NmbParameter):
    """Number of channel segments [-].

    You can set the number of segments directly:

    >>> from hydpy.models.musk import *
    >>> simulationstep("12h")
    >>> parameterstep("1d")
    >>> nmbsegments(2)
    >>> nmbsegments
    nmbsegments(2)

    If you prefer to configure |musk| in the style of HBV96
    :cite:p:`ref-Lindstrom1997HBV96`, use the `lag` argument.  |NmbSegments|
    calculates the number of segments so that one simulation step lag corresponds to
    one segment:

    >>> nmbsegments(lag=2.5)
    >>> nmbsegments
    nmbsegments(lag=2.5)
    >>> nmbsegments.value
    5

    Negative `lag` values are trimmed to zero:

    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     nmbsegments(lag=-1.0)
    UserWarning: For parameter `nmbsegments` of element `?` the keyword argument \
`lag` with value `-1.0` needed to be trimmed to `0.0`.
    >>> nmbsegments
    nmbsegments(lag=0.0)
    >>> nmbsegments.value
    0

    Calculating an integer number of segments from a time lag defined as a
    floating-point number requires rounding:

    >>> nmbsegments(lag=0.9)
    >>> nmbsegments
    nmbsegments(lag=0.9)
    >>> nmbsegments.value
    2
    """

    SPAN = (0, None)

    def _set_lag(self, *, lag: float) -> dict[str, float]:
        lag = parametertools.trim_kwarg(self, "lag", lag, lower=0.0)
        self.value = int(round(lag / self.get_timefactor()))
        return {"lag": lag}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("lag", time=False), setter=_set_lag
        )
    )

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.nmb_segments = self.value


class Coefficients(variabletools.MixinFixedShape, parametertools.Parameter):
    """Coefficients of the Muskingum working formula [-].

    There are three options for defining the (fixed) coefficients of the Muskingum
    working formula.  First, you can define them manually (see the documentation on
    method |Calc_Discharge_V1| on how these coefficients are applied):

    >>> from hydpy.models.musk import *
    >>> simulationstep("12h")
    >>> parameterstep("1d")
    >>> coefficients(0.2, 0.5, 0.3)
    >>> coefficients
    coefficients(0.2, 0.5, 0.3)

    Second, you can let parameter |Coefficients| calculate the coefficients according
    to HBV96 :cite:p:`ref-Lindstrom1997HBV96`.  Therefore, use the `damp` argument.
    Its lowest possible value is zero and results in a pure translation process where a
    flood wave travels one segment per simulation step without modification of its
    shape:

    >>> from hydpy import print_vector
    >>> coefficients(damp=0.0)
    >>> coefficients
    coefficients(damp=0.0)
    >>> print_vector(coefficients.values)
    0.0, 1.0, 0.0

    Negative `damp` values are trimmed to zero:

    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     coefficients(damp=-1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument \
`damp` with value `-1.0` needed to be trimmed to `0.0`.
    >>> coefficients
    coefficients(damp=0.0)
    >>> print_vector(coefficients.values)
    0.0, 1.0, 0.0

    Higher values do not change the translation time but increase wave attenuation.
    The highest possible value with non-negative coefficients is one:

    >>> coefficients(damp=1.0)
    >>> coefficients
    coefficients(damp=1.0)
    >>> print_vector(coefficients.values)
    0.5, 0.0, 0.5

    Higher values are allowed but result in highly skewed responses that are usually
    not desirable:

    >>> coefficients(damp=3.0)
    >>> coefficients
    coefficients(damp=3.0)
    >>> print_vector(coefficients.values)
    0.75, -0.5, 0.75

    The third option follows the original Muskingum method :cite:p:`ref-McCarthy1940`
    and is more flexible as it offers two parameters.  `k` is the translation time
    (defined with respect to the current parameter step size), and `x` is a weighting
    factor.  Note that both parameters hold for a single channel segment, so that, for
    example, a `k` value of one day results in an effective translation time of two
    days for a channel divided into two segments.

    The calculation of the coefficients follows the classic Muskingum method:

      :math:`c_1 = \\frac{1 - 2 \\cdot k \\cdot x}{2 \\cdot k (1 - x) + 1}`

      :math:`c_2 = \\frac{1 + 2 \\cdot k \\cdot x}{2 \\cdot k (1 - x) + 1}`

      :math:`c_3 = \\frac{2 \\cdot k (1 - x) - 1}{2 \\cdot k (1 - x) + 1}`

    For a `k` value of zero, travel time and diffusion are zero.  Negative `k` values
    are trimmed to zero:

    >>> with warn_later():
    ...     coefficients(k=-1.0, x=0.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `k` \
with value `-1.0` needed to be trimmed to `0.0`.
    >>> coefficients
    coefficients(k=0.0, x=0.0)
    >>> print_vector(coefficients.values)
    1.0, 1.0, -1.0

    The usual lowest value for `x` is zero:

    >>> coefficients(k=0.5, x=0.0)
    >>> coefficients
    coefficients(k=0.5, x=0.0)
    >>> print_vector(coefficients.values)
    0.333333, 0.333333, 0.333333

    However, negative `x` values do not always result in problematic wave
    transformations, so we allow them:

    >>> coefficients(k=0.5, x=-1.0)
    >>> coefficients
    coefficients(k=0.5, x=-1.0)
    >>> print_vector(coefficients.values)
    0.6, -0.2, 0.6

    As mentioned above, the value of `k` depends on the current parameter step size:

    >>> from hydpy import pub
    >>> with pub.options.parameterstep("12h"):
    ...     coefficients
    coefficients(k=1.0, x=-1.0)

    The highest possible value for `x` depends on the current value of `k` (but can
    never exceed 0.5):

      :math:`x
      \\leq min \\left( \\frac{1}{2 \\cdot k}, 1 - \\frac{1}{2 \\cdot k} \\right)
      \\leq \\frac{1}{2}`

    The string representation shows the originally given value of `x`, which results
    in the same coefficients but also in the same warning when executed again:

    >>> with warn_later():
    ...     coefficients(k=0.5, x=1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `1.0` needed to be trimmed to `0.5`.
    >>> coefficients
    coefficients(k=0.5, x=1.0)
    >>> print_vector(coefficients.values)
    0.0, 1.0, 0.0

    >>> with warn_later():
    ...     coefficients(k=1.0, x=1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `1.0` needed to be trimmed to `0.25`.
    >>> print_vector(coefficients.values)
    0.0, 0.5, 0.5

    >>> with warn_later():
    ...     coefficients(k=0.25, x=1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `1.0` needed to be trimmed to `0.0`.
    >>> print_vector(coefficients.values)
    0.5, 0.5, 0.0

    Hence, when exchange items or calibration rules change `k` (see method
    |KeywordHandler.set_value|), |Coefficients| trims `x` based on its originally given
    value and not on the result of a previous trimming:

    >>> with warn_later():
    ...     coefficients(k=1.0, x=0.4)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `0.4` needed to be trimmed to `0.25`.
    >>> coefficients.keywordhandler.set_value("k", 0.5)
    >>> coefficients
    coefficients(k=0.5, x=0.4)
    """

    TYPE: Final = float
    SHAPE = (3,)

    def _set_damp(self, *, damp: float) -> dict[str, float]:
        damp = parametertools.trim_kwarg(self, "damp", damp, lower=0.0)
        c13 = damp / (1.0 + damp)
        c2 = 1.0 - 2.0 * c13
        self.values = c13, c2, c13
        return {"damp": damp}

    def _set_k_x(self, *, k: float, x: float) -> dict[str, float]:
        k = parametertools.trim_kwarg(self, "k", k, lower=0.0)
        k_sim = k / self.get_timefactor()
        x_given = float(x)
        if k_sim > 0.0:
            upper = min(1.0 / 2.0 / k_sim, 1.0 - 1.0 / 2.0 / k_sim)
            x = parametertools.trim_kwarg(self, "x", x, upper=upper)
        denom = 2.0 * k_sim * (1.0 - x) + 1.0
        c1 = (1.0 - 2.0 * k_sim * x) / denom
        c2 = (1.0 + 2.0 * k_sim * x) / denom
        c3 = (2.0 * k_sim * (1.0 - x) - 1.0) / denom
        self.values = c1, c2, c3
        return {"k": k, "x": x_given}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(parametertools.Keyword("damp"), setter=_set_damp),
        parametertools.KeywordGroup(
            parametertools.Keyword("k", time=False),
            parametertools.Keyword("x"),
            setter=_set_k_x,
        ),
    )


class Length(parametertools.Parameter):
    """The total length of channel [km]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class BottomSlope(parametertools.Parameter):
    r"""Bottom slope [-].

    :math:`BottomSlope = \frac{elevation_{start} - elevation_{end}}{Length}`
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
