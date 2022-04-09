# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.musk import musk_parameters


class NmbSegments(parametertools.Parameter):
    """Number of channel segments [-].

    You can set the number of segments directly:

    >>> from hydpy.models.musk import *
    >>> simulationstep("12h")
    >>> parameterstep("1d")
    >>> nmbsegments(2)
    >>> nmbsegments
    nmbsegments(2)

    |NmbSegments| prepares the shape of most 1-dimensional parameters and sequences
    automatically:

    >>> length.shape
    (2,)
    >>> derived.perimeterincrease.shape
    (2,)
    >>> factors.referencewaterlevel.shape
    (2,)
    >>> fluxes.referencedischarge.shape
    (2,)
    >>> states.discharge.shape
    (3,)

    If you prefer to configure |musk| in the style of HBV96
    :cite:p:`ref-Lindstrom1997HBV96`, use the `lag` argument.  |NmbSegments|
    calculates the number of segments so that one simulation step lag corresponds to
    one segment:

    >>> nmbsegments(lag=2.5)
    >>> nmbsegments
    nmbsegments(lag=2.5)
    >>> states.discharge.shape
    (6,)

    Negative `lag` values are trimmed to zero:

    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     nmbsegments(lag=-1.0)
    UserWarning: For parameter `nmbsegments` of element `?` the keyword argument \
`lag` with value `-1.0` needed to be trimmed to `0.0`.
    >>> nmbsegments
    nmbsegments(lag=0.0)
    >>> states.discharge.shape
    (1,)

    Calculating an integer number of segments from a time lag defined as a
    floating-point number requires rounding:

    >>> nmbsegments(lag=0.9)
    >>> nmbsegments
    nmbsegments(lag=0.9)
    >>> states.discharge.shape
    (3,)

    |NmbSegments| preserves existing values if the number of segments does not change:

    >>> states.discharge = 1.0, 2.0, 3.0
    >>> nmbsegments(2)
    >>> nmbsegments
    nmbsegments(2)
    >>> states.discharge
    discharge(1.0, 2.0, 3.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)
    KEYWORDS = {"lag": parametertools.Keyword(name="lag", time=False)}

    def __call__(self, *args, **kwargs) -> None:
        self._keywordarguments = parametertools.KeywordArguments(False)
        idx = self._find_kwargscombination(args, kwargs, (set(("lag",)),))
        if idx is None:
            super().__call__(*args, **kwargs)
        else:
            lag = parametertools.trim_kwarg(self, "lag", kwargs["lag"], lower=0.0)
            lag /= self.get_timefactor()
            self.value = int(round(lag))
            self._keywordarguments = parametertools.KeywordArguments(lag=lag)

        shape = self.value
        model = self.subpars.pars.model
        model.nmb_segments = shape
        pars, seqs = model.parameters, model.sequences
        for subvars in (
            pars.control,
            pars.derived,
            seqs.factors,
            seqs.fluxes,
            seqs.states,
        ):
            for variable in (var for var in subvars if var.NDIM == 1):
                if variable.name == "coefficients":
                    continue
                oldshape = exceptiontools.getattr_(variable, "shape", None)
                if variable.name == "discharge":
                    if oldshape != (shape + 1,):
                        variable.shape = (shape + 1,)
                else:
                    if oldshape != (shape,):
                        variable.shape = (shape,)

    def __repr__(self) -> str:
        if self._keywordarguments.valid:
            lag = self.get_timefactor() * self._keywordarguments["lag"]
            return f"{self.name}(lag={objecttools.repr_(lag)})"
        return super().__repr__()


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

    >>> from hydpy import print_values
    >>> coefficients(damp=0.0)
    >>> coefficients
    coefficients(damp=0.0)
    >>> print_values(coefficients.values)
    0.0, 1.0, 0.0

    Negative `damp` values are trimmed to zero:

    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     coefficients(damp=-1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument \
`damp` with value `-1.0` needed to be trimmed to `0.0`.

    Higher values do not change the translation time but increase wave attenuation.
    The highest possible value with non-negative coefficients is one:

    >>> coefficients(damp=1.0)
    >>> coefficients
    coefficients(damp=1.0)
    >>> print_values(coefficients.values)
    0.5, 0.0, 0.5

    Higher values are allowed but result in highly skewed responses that are usually
    not desirable:

    >>> coefficients(damp=3.0)
    >>> coefficients
    coefficients(damp=3.0)
    >>> print_values(coefficients.values)
    0.75, -0.5, 0.75

    The third option follows the original Muskingum method :cite:p:`ref-McCarthy1940`
    and is more flexible as it offers two parameters.  `k` is the translation time
    (defined with respect to the current parameter step size), and `x` is a weighting
    factor.  Note that both parameters hold for a single channel segment, so that, for
    example, a `k` value of one day results in an efficient translation time of two
    days for a channel divided into two segments.

    The calculation of the coefficients follows the classic Muskingum method:

      :math:`c_1 = \\frac{1 - 2 \\cdot k \\cdot x}{2 \\cdot k (1 - x) + 1}`

      :math:`c_2 = \\frac{1 + 2 \\cdot k \\cdot x}{2 \\cdot k (1 - x) + 1}`

      :math:`c_3 = \\frac{2 \\cdot k (1 - x) - 1}{2 \\cdot k (1 - x) + 1}`

    For a `k` value of zero, travel time and diffusion are zero:

    >>> coefficients(k=0.0, x=0.0)
    >>> coefficients
    coefficients(k=0.0, x=0.0)
    >>> print_values(coefficients.values)
    1.0, 1.0, -1.0

    Negative `k` values are trimmed:

    >>> with warn_later():
    ...     coefficients(k=-1.0, x=0.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `k` \
with value `-1.0` needed to be trimmed to `0.0`.
    >>> coefficients
    coefficients(k=0.0, x=0.0)
    >>> print_values(coefficients.values)
    1.0, 1.0, -1.0

    The usual lowest value for `x` is zero:

    >>> coefficients(k=0.5, x=0.0)
    >>> coefficients
    coefficients(k=0.5, x=0.0)
    >>> print_values(coefficients.values)
    0.333333, 0.333333, 0.333333

    However, negative `x` values do not always result in problematic wave
    transformations, so we allow them:

    >>> coefficients(k=0.5, x=-1.0)
    >>> coefficients
    coefficients(k=0.5, x=-1.0)
    >>> print_values(coefficients.values)
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

    >>> with warn_later():
    ...     coefficients(k=0.5, x=1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `1.0` needed to be trimmed to `0.5`.
    >>> coefficients
    coefficients(k=0.5, x=0.5)
    >>> print_values(coefficients.values)
    0.0, 1.0, 0.0

    >>> with warn_later():
    ...     coefficients(k=1.0, x=1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `1.0` needed to be trimmed to `0.25`.
    >>> coefficients
    coefficients(k=1.0, x=0.25)
    >>> print_values(coefficients.values)
    0.0, 0.5, 0.5

    >>> with warn_later():
    ...     coefficients(k=0.25, x=1.0)
    UserWarning: For parameter `coefficients` of element `?` the keyword argument `x` \
with value `1.0` needed to be trimmed to `0.0`.
    >>> coefficients
    coefficients(k=0.25, x=0.0)
    >>> print_values(coefficients.values)
    0.5, 0.5, 0.0
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    SHAPE = (3,)
    KEYWORDS = {
        "damp": parametertools.Keyword(name="damp"),
        "k": parametertools.Keyword(name="k", time=False),
        "x": parametertools.Keyword(name="x"),
    }

    def __call__(self, *args, **kwargs) -> None:
        self._keywordarguments = parametertools.KeywordArguments(False)
        idx = self._find_kwargscombination(
            args, kwargs, (set(("damp",)), set(("k", "x")))
        )
        if idx is None:
            super().__call__(*args, **kwargs)
        elif idx == 0:
            damp = parametertools.trim_kwarg(self, "damp", kwargs["damp"], lower=0.0)
            c13 = damp / (1.0 + damp)
            c2 = 1.0 - 2.0 * c13
            self.values = c13, c2, c13
            self._keywordarguments = parametertools.KeywordArguments(damp=damp)
        else:
            k = parametertools.trim_kwarg(self, "k", kwargs["k"], lower=0.0)
            k /= self.get_timefactor()
            x = kwargs["x"]
            if k > 0.0:
                upper = min(1.0 / 2.0 / k, 1.0 - 1.0 / 2.0 / k)
                x = parametertools.trim_kwarg(self, "x", x, upper=upper)
            denom = 2.0 * k * (1.0 - x) + 1.0
            c1 = (1.0 - 2.0 * k * x) / denom
            c2 = (1.0 + 2.0 * k * x) / denom
            c3 = (2.0 * k * (1.0 - x) - 1.0) / denom
            self.values = c1, c2, c3
            self._keywordarguments = parametertools.KeywordArguments(k=k, x=x)

    def __repr__(self) -> str:
        if self._keywordarguments.valid:
            strings = []
            for name, value in self._keywordarguments:
                if name == "k":
                    value *= self.get_timefactor()
                strings.append(f"{name}={objecttools.repr_(value)}")
            return f"{self.name}({', '.join(strings)})"
        return super().__repr__()


class Length(parametertools.Parameter):
    """Segment length [km]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BottomSlope(musk_parameters.Parameter1D):
    r"""Bottom slope [-].

    :math:`BottomSlope = \frac{elevation_{start} - elevation_{end}}{Length}`
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class BottomWidth(musk_parameters.Parameter1D):
    """Bottom width [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)


class SideSlope(musk_parameters.Parameter1D):
    """Side slope [-].

    A value of zero corresponds to a rectangular channel shape.  A value of two
    corresponds to an increase of a half meter elevation for each additional meter
    distance from the channel.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)


class StricklerCoefficient(musk_parameters.Parameter1D):
    """Gauckler-Manning-Strickler coefficient [m^(1/3)/s].

    The higher the coefficient's value, the higher the calculated discharge.  Typical
    values range from 20 to 80.
    """

    TYPE, TIME, SPAN = float, None, (0.0, None)
