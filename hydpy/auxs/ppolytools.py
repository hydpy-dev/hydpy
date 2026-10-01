"""This module implements interpolation approaches based on piecewise polynomials
required for some models implemented in the *HydPy* framework.

The relevant models perform the interpolation during simulation runs, which is why we
implement the related methods in the Cython extension module |ppolyutils|.
"""

from __future__ import annotations
import inspect

import numpy

import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core.typingtools import *
from hydpy.auxs import interptools

if TYPE_CHECKING:
    from scipy import interpolate
    from hydpy.cythons import ppolyutils
else:
    interpolate = exceptiontools.OptionalImport(
        "interpolate", ["scipy.interpolate"], locals()
    )
    from hydpy.cythons.autogen import ppolyutils


MethodNames: TypeAlias = Literal["linear", "cubic", "akima", "pchip"]


class Poly(NamedTuple):
    r"""Parameter handler for a power series representation of a single polynomial
    function.

    The following |Poly| object corresponds to the polynomial function
    :math:`f(x) = 2 + 3 \cdot (x - 1) + 4 \cdot (x - 1)^2`:

    >>> from hydpy import Poly
    >>> p = Poly(x0=1.0, cs=(2.0, 3.0, 4.0))

    Proper application of the constant and all coefficients for :math:`x = 3` results
    in 24:

    >>> x = 3.0
    >>> p.cs[0] + p.cs[1] * (x - p.x0) + p.cs[2] * (x - p.x0) ** 2
    24.0
    """

    x0: float
    """Constant of the power series."""
    cs: tuple[float, ...]
    """Coefficients of the power series."""

    def assignrepr(self, prefix: str) -> str:
        """Return a string representation of the actual |ppolytools.Poly| object
        prefixed with the given string.

        >>> from hydpy import Poly
        >>> poly = Poly(x0=1.0/3.0, cs=(2.0, 3.0, 4.0/3.0))
        >>> poly
        Poly(x0=0.333333, cs=(2.0, 3.0, 1.333333))
        >>> print(poly.assignrepr(prefix="poly = "))
        poly = Poly(x0=0.333333, cs=(2.0, 3.0, 1.333333))
        """
        return (
            f"{prefix}{type(self).__name__}("
            f"x0={objecttools.repr_(self.x0)}, "
            f"cs={objecttools.repr_tuple(self.cs)})"
        )

    def __repr__(self) -> str:
        return self.assignrepr(prefix="")


class _OriginalData(NamedTuple):
    """The original x-y data and the interpolation method used for estimating the
    polynomials of a |PPoly| object."""

    xs: VectorFloat
    ys: VectorFloat
    method: MethodNames


def _get_splineclass(
    name: MethodNames, /
) -> type[interpolate.CubicHermiteSpline] | None:
    if name == "cubic":
        return interpolate.CubicSpline
    if name == "akima":
        return interpolate.Akima1DInterpolator
    if name == "pchip":
        return interpolate.PchipInterpolator
    return None


def _get_splinename(
    class_: type[interpolate.CubicHermiteSpline], /
) -> Literal["cubic", "akima", "pchip"] | None:
    if class_ is interpolate.CubicSpline:
        return "cubic"
    if class_ is interpolate.Akima1DInterpolator:
        return "akima"
    if class_ is interpolate.PchipInterpolator:
        return "pchip"
    return None


class PPoly(interptools.InterpAlgorithm):
    """Piecewise polynomial interpolator.

    Class |PPoly| supports univariate data interpolation via multiple polynomial
    functions.  Typical use cases are linear or spline interpolation.  The primary
    purpose of |PPoly| is to allow for such interpolation within model equations (for
    example, to represent the relationship between water volume and water stage as in
    the model |dam_v001|).  Then, the user selects |PPoly| as the interpolation
    algorithm employed by parameters derived from |SimpleInterpolator| (e.g.
    |dam_control.WaterVolume2WaterLevel|) or |SeasonalInterpolator| (e.g.
    |dam_control.WaterLevel2FloodDischarge|).  However, one can apply |PPoly| also
    directly, as shown in the following examples.

    You can prepare a |PPoly| object by handing multiple |Poly| objects to its
    constructor:

    >>> from hydpy import Poly, PPoly
    >>> ppoly = PPoly(
    ...     Poly(x0=1.0, cs=(1.0,)),
    ...     Poly(x0=2.0, cs=(1.0, 1.0)),
    ...     Poly(x0=3.0, cs=(2.0, 3.0)),
    ... )

    Note that each power series constant (|Poly.x0|) also serves as a breakpoint.  Each
    |Poly.x0| value defines the lower bound of the interval for which the polynomial is
    valid.  The only exception affects the first |Poly| object.  Here, |Poly.x0| also
    serves as the power series constant but not as a breakpoint.  Hence, |PPoly| uses
    the first polynomial for extrapolation into the negative range (as it uses the last
    polynomial for extrapolating into the positive range).  The following equation,
    which reflects the configuration of the prepared interpolator, should clarify this
    definition:

      .. math::
        f(x) = \\begin{cases}
        1
        &|\\
        x < 2
        \\\\
        1 + x - 2
        &|\\
        2 \\leq x < 3
        \\\\
        2 + 3 \\cdot (x - 3)
        &|\\
        3 \\leq x
        \\end{cases}

    For applying `ppoly`, we need to set the input value before calling
    |PPoly.calculate_values|:

    >>> ppoly.inputs[0] = 2.5
    >>> ppoly.calculate_values()
    >>> from hydpy import round_
    >>> round_(ppoly.outputs[0])
    1.5

    The same holds when calling method |PPoly.calculate_derivatives| for calculating
    first order derivatives:

    >>> ppoly.calculate_derivatives(0)
    >>> round_(ppoly.output_derivatives[0])
    1.0

    Use method |InterpAlgorithm.print_table| or method |InterpAlgorithm.plot| to
    inspect the results of `ppoly` within the relevant data range:

    >>> ppoly.print_table([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
    x    y    dy/dx
    0.5  1.0  0.0
    1.0  1.0  0.0
    1.5  1.0  0.0
    2.0  1.0  1.0
    2.5  1.5  1.0
    3.0  2.0  3.0
    3.5  3.5  3.0

    >>> figure = ppoly.plot(xmin=0.0, xmax=4.0)
    >>> from hydpy.core.testtools import save_autofig
    >>> save_autofig("PPoly_base_example.png", figure=figure)

        .. image:: PPoly_base_example.png

    |PPoly| collects all constants and coefficients and provides access to them via
    properties |PPoly.x0s| and |PPoly.cs| available:

    >>> from hydpy import print_matrix, print_vector
    >>> print_vector(ppoly.x0s)
    1.0, 2.0, 3.0
    >>> print_matrix(ppoly.cs)
    | 1.0, 0.0 |
    | 1.0, 1.0 |
    | 2.0, 3.0 |

    Property |PPoly.nmb_ps| reflects the total number of polynomials:

    >>> ppoly.nmb_ps
    3

    Property |PPoly.nmb_cs| informs about the number of relevant coefficients for each
    polynomial (the last non-negative coefficient is the last relevant one):

    >>> print_vector(ppoly.nmb_cs)
    1, 2, 2

    You are free to manipulate both the breakpoints and the coefficients:

    >>> ppoly.x0s = 1.0, 2.0, 2.5
    >>> ppoly.cs[1, 1] = 2.0

    >>> ppoly.polynomials
    (Poly(x0=1.0, cs=(1.0,)), Poly(x0=2.0, cs=(1.0, 2.0)), Poly(x0=2.5, cs=(2.0, 3.0)))

    >>> ppoly.print_table([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
    x    y    dy/dx
    0.5  1.0  0.0
    1.0  1.0  0.0
    1.5  1.0  0.0
    2.0  1.0  2.0
    2.5  2.0  3.0
    3.0  3.5  3.0
    3.5  5.0  3.0

    However, be aware that manipulating |PPoly.nmb_ps|, |PPoly.nmb_cs|, |PPoly.x0s|,
    |PPoly.nmb_cs| can cause severe problems, including program crashes.  Hence, you
    should always call the |PPoly.verify| method after manipulating these properties,
    which checks the integrity of the current configuration of |PPoly| objects:

    >>> ppoly.nmb_ps = 1
    >>> ppoly.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to verify parameter `ppoly` of element `?`, the \
following error occurred: The number of constants indicated by `nmb_ps` (1) does not \
agree with the actual number of constants held by vector `x0s` (3).

    To change an existing |PPoly| object more safely, you can "call" it with different
    |Poly| objects, which overwrites all current information, as shown by the following
    example, defining only a single polynomial:

    >>> ppoly(Poly(x0=-1.0, cs=(0.0, 0.0, 1.0)))
    >>> ppoly.print_table([-3.0, -2.0, -1.0, 0.0, 1.0])
    x     y    dy/dx
    -3.0  4.0  -4.0
    -2.0  1.0  -2.0
    -1.0  0.0  0.0
    0.0   1.0  2.0
    1.0   4.0  4.0

    Instead of defining the polynomials directly, you can let |PPoly| estimate them
    from x-y data.  Therefore, pass the data via the keyword arguments `xs` and `ys`
    and, optionally, select an interpolation approach via the keyword argument
    `method` (see method |PPoly.from_data| for more information).  This works when
    calling an existing |PPoly| object:

    >>> ppoly(xs=[0.0, 1.0, 3.0], ys=[2.0, 5.0, 6.0])
    >>> ppoly.polynomials
    (Poly(x0=0.0, cs=(2.0, 3.0)), Poly(x0=1.0, cs=(5.0, 0.5)))

    It also works when creating a new one:

    >>> PPoly(xs=[0.0, 1.0], ys=[2.0, 5.0]).polynomials
    (Poly(x0=0.0, cs=(2.0, 3.0)),)

    In such cases, the string representation of |PPoly| objects shows the original data
    instead of the estimated polynomials (see method |PPoly.assignrepr|):

    >>> ppoly
    PPoly(
        xs=[0.0, 1.0, 3.0],
        ys=[2.0, 5.0, 6.0],
    )

    Calling |PPoly| objects without any arguments results in the following error:

    >>> ppoly()
    Traceback (most recent call last):
    ...
    TypeError: You must either define the piecewise polynomials directly by passing \
`Poly` instances, or provide the data required for estimating them.

    You cannot pass |Poly| objects and x-y data at the same time:

    >>> ppoly(Poly(x0=0.0, cs=(1.0,)), xs=[0.0], ys=[1.0])
    Traceback (most recent call last):
    ...
    TypeError: You must either define the piecewise polynomials directly by passing \
`Poly` instances, or provide the data required for estimating them, but not both.

    Estimating polynomials requires both x and y data:

    >>> ppoly(xs=[0.0, 1.0])
    Traceback (most recent call last):
    ...
    TypeError: Estimating piecewise polynomials requires both x and y data.

    The constructor performs the same checks.  The only exception is that it allows
    creating |PPoly| objects without any arguments, which you must configure afterwards
    (for example, by calling them as shown above):

    >>> PPoly(xs=[0.0, 1.0])
    Traceback (most recent call last):
    ...
    TypeError: Estimating piecewise polynomials requires both x and y data.
    """

    _calgorithm: ppolyutils.PPoly
    _cready: bool
    _original_data: _OriginalData | None

    @overload
    def __new__(cls, *polynomials: Poly) -> Self: ...

    @overload
    def __new__(
        cls,
        *,
        xs: VectorInputFloat,
        ys: VectorInputFloat,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> Self: ...

    def __new__(
        cls,
        *polynomials: Poly,
        xs: VectorInputFloat | None = None,
        ys: VectorInputFloat | None = None,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> Self:
        self = cls._make_self()
        if polynomials or (xs is not None) or (ys is not None):
            self._call(*polynomials, xs=xs, ys=ys, method=method)
        return self

    @classmethod
    def _make_self(cls) -> Self:
        self = super().__new__(cls)
        self._original_data = None
        ca = ppolyutils.PPoly()
        self._calgorithm = ca
        ca.inputs = numpy.zeros((1,), dtype=config.NP_FLOAT)
        ca.outputs = numpy.zeros((1,), dtype=config.NP_FLOAT)
        ca.output_derivatives = numpy.zeros((1,), dtype=config.NP_FLOAT)
        return self

    @overload
    def __call__(self, *polynomials: Poly) -> None: ...

    @overload
    def __call__(
        self,
        *,
        xs: VectorInputFloat,
        ys: VectorInputFloat,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> None: ...

    def __call__(
        self,
        *polynomials: Poly,
        xs: VectorInputFloat | None = None,
        ys: VectorInputFloat | None = None,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> None:
        self._call(*polynomials, xs=xs, ys=ys, method=method)

    def _call(
        self,
        *polynomials: Poly,
        xs: VectorInputFloat | None = None,
        ys: VectorInputFloat | None = None,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> None:
        nmb_vectors = (xs is not None) + (ys is not None)
        if polynomials:
            if nmb_vectors > 0:
                raise TypeError(
                    f"You must either define the piecewise polynomials directly by "
                    f"passing `{Poly.__name__}` instances, or provide the data "
                    f"required for estimating them, but not both."
                )
            self._use_polynomials(*polynomials)
        elif nmb_vectors == 1:
            raise TypeError(
                "Estimating piecewise polynomials requires both x and y data."
            )
        elif nmb_vectors == 2:
            assert (xs is not None) and (ys is not None)
            self._use_data(xs=xs, ys=ys, method=method)
        else:
            raise TypeError(
                f"You must either define the piecewise polynomials directly by passing "
                f"`{Poly.__name__}` instances, or provide the data required for "
                f"estimating them."
            )

    @classmethod
    def from_polynomials(cls, *polynomials: Poly) -> Self:
        """Prepare a |PPoly| object based on the given |Poly| objects.

        Method |PPoly.from_polynomials| is an alternative to passing |Poly| objects to
        the constructor of class |PPoly|:

        >>> from hydpy import Poly, PPoly
        >>> PPoly.from_polynomials(
        ...     Poly(x0=1.0, cs=(1.0,)), Poly(x0=2.0, cs=(1.0, 1.0))
        ... )
        PPoly(
            Poly(x0=1.0, cs=(1.0,)),
            Poly(x0=2.0, cs=(1.0, 1.0)),
        )

        In contrast to the constructor, which also allows for creating not-configured
        |PPoly| objects, method |PPoly.from_polynomials| requires at least one |Poly|
        object:

        >>> PPoly.from_polynomials()
        Traceback (most recent call last):
        ...
        TypeError: You must provide at least one `Poly` instance.
        """
        if not polynomials:
            raise TypeError(
                f"You must provide at least one `{Poly.__name__}` instance."
            )
        self = cls._make_self()
        self._use_polynomials(*polynomials)
        return self

    def _use_polynomials(self, *polynomials: Poly) -> None:
        nmb_ps = len(polynomials)
        nmb_cs = numpy.asarray([len(p.cs) for p in polynomials], dtype=config.NP_INT)
        x0s = numpy.asarray([p.x0 for p in polynomials], dtype=config.NP_FLOAT)
        cs = numpy.zeros((nmb_ps, max(nmb_cs)))
        for idx, (nmb, polynomial) in enumerate(zip(nmb_cs, polynomials)):
            cs[idx, :nmb] = polynomial.cs
        self.nmb_ps, self.nmb_cs, self.x0s, self.cs = nmb_ps, nmb_cs, x0s, cs
        self._original_data = None

    @classmethod
    def from_data(
        cls,
        xs: VectorInputFloat,
        ys: VectorInputFloat,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> Self:
        """Prepare a |PPoly| object based on x-y data.

        As explained in the main documentation on class |PPoly|, you are free to define
        an arbitrary number of polynomials, each with arbitrary constants and
        coefficients.  However, one usually prefers functionally similar polynomials
        that standardised algorithms can compute. Method |PPoly.from_data| is a
        convenience function for following this route.  So far, it supports linear
        interpolation and some spline techniques.

        We start our explanations with a small and smooth x-y data set:

        >>> xs = [1.0, 2.0, 3.0]
        >>> ys = [1.0, 2.0, 3.5]

        By default, method |PPoly.from_data| prepares everything for a piecewise linear
        interpolation:

        >>> from hydpy import PPoly
        >>> ppoly = PPoly.from_data(xs=xs, ys=ys)
        >>> for poly in ppoly.polynomials:
        ...     print(poly)
        Poly(x0=1.0, cs=(1.0, 1.0))
        Poly(x0=2.0, cs=(2.0, 1.5))
        >>> ppoly.print_table(xs=[1.9, 2.0, 2.1])
        x    y     dy/dx
        1.9  1.9   1.0
        2.0  2.0   1.5
        2.1  2.15  1.5
        >>> figure = ppoly.plot(0.0, 4.0, label="linear")

        The string representation of `ppoly` does not list these polynomials but the
        original data (see method |PPoly.assignrepr|):

        >>> ppoly
        PPoly(
            xs=[1.0, 2.0, 3.0],
            ys=[1.0, 2.0, 3.5],
        )

        Alternatively, |PPoly| can use the |scipy| classes `CubicSpline`,
        `Akima1DInterpolator`, and `PchipInterpolator` for determining higher-order
        polynomials.  Select them via the strings "cubic", "akima", and "pchip".

        For sufficiently smooth data, cubic spline interpolation is often a good choice,
        as it preserves much smoothness around breakpoints (helpful for reaching
        required accuracies when applying numerical integration algorithms):

        >>> ppoly = PPoly.from_data(xs=xs, ys=ys, method="cubic")
        >>> for poly in ppoly.polynomials:
        ...     print(poly)
        Poly(x0=1.0, cs=(1.0, 0.75, 0.25))
        Poly(x0=2.0, cs=(2.0, 1.25, 0.25))
        >>> ppoly.print_table(xs=[1.9, 2.0, 2.1])
        x    y       dy/dx
        1.9  1.8775  1.2
        2.0  2.0     1.25
        2.1  2.1275  1.3
        >>> figure = ppoly.plot(0.0, 4.0, label="Cubic")

        For non-linear interpolation methods, the string representation also includes
        the method's name:

        >>> ppoly
        PPoly(
            xs=[1.0, 2.0, 3.0],
            ys=[1.0, 2.0, 3.5],
            method="cubic",
        )

        For the given data, the Akima spline results in the same coefficients as the
        cubic spline:

        >>> ppoly = PPoly.from_data(xs=xs, ys=ys, method="akima")
        >>> for poly in ppoly.polynomials:
        ...     print(poly)
        Poly(x0=1.0, cs=(1.0, 0.75, 0.25))
        Poly(x0=2.0, cs=(2.0, 1.25, 0.25))
        >>> figure = ppoly.plot(0.0, 4.0, label="Akima")

        The PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) algorithm
        generally tends to produce less smooth interpolations:

        >>> ppoly = PPoly.from_data(xs=xs, ys=ys, method="pchip")
        >>> for poly in ppoly.polynomials:
        ...     print(poly)
        Poly(x0=1.0, cs=(1.0, 0.75, 0.3, -0.05))
        Poly(x0=2.0, cs=(2.0, 1.2, 0.35, -0.05))
        >>> ppoly.print_table(xs=[1.9, 2.0, 2.1])
        x    y        dy/dx
        1.9  1.88155  1.1685
        2.0  2.0      1.2
        2.1  2.12345  1.2685
        >>> figure = ppoly.plot(0.0, 4.0, label="Pchip")

        The following figure compares the linear and all spline interpolation results.
        As expected, the most sensible differences show in the interpolation ranges:

        >>> _ = figure.gca().legend()
        >>> from hydpy.core.testtools import save_autofig
        >>> save_autofig("PPoly_data_smooth.png")

        .. image:: PPoly_data_smooth.png

        Next, we apply all four interpolation approaches to a non-smooth data set.
        Cubic interpolation is again the smoothest one but tends to overshoot, which
        can be problematic when violating physical constraints.  Besides the linear
        approach, only the PCHIP interpolation always preserves monotonicity in the
        original data. The Akima interpolation appears as a good compromise between
        these two approaches:

        >>> for method in ("linear", "cubic", "akima", "pchip"):
        ...     figure = PPoly.from_data(
        ...         xs=[1.0, 2.0, 3.0, 4.0], ys=[1.0, 1.0, 2.0, 2.0], method=method
        ...     ).plot(0.0, 5.0, label=method)
        >>> _ = figure.gca().legend()
        >>> _ = figure.gca().set_ylim((0.5, 2.5))
        >>> save_autofig("PPoly_data_not_smooth.png")

        .. image:: PPoly_data_not_smooth.png

        Instead of strings, you can also pass the mentioned |scipy| classes themselves.
        |PPoly| recognises them and handles them like the corresponding strings:

        >>> from scipy.interpolate import CubicSpline
        >>> PPoly.from_data(xs=xs, ys=ys, method=CubicSpline)
        PPoly(
            xs=[1.0, 2.0, 3.0],
            ys=[1.0, 2.0, 3.5],
            method="cubic",
        )

        You can even pass other subclasses of |scipy|'s `CubicHermiteSpline` class.
        However, the string representation then falls back to listing the estimated
        polynomials:

        >>> class MySpline(CubicSpline):
        ...     pass
        >>> PPoly.from_data(xs=xs, ys=ys, method=MySpline)
        PPoly(
            Poly(x0=1.0, cs=(1.0, 0.75, 0.25)),
            Poly(x0=2.0, cs=(2.0, 1.25, 0.25)),
        )

        Unknown method names and wrong classes result in the following error:

        >>> PPoly.from_data(xs=xs, ys=ys, method="spline")
        Traceback (most recent call last):
        ...
        ValueError: While trying to derive polynomials from the vectors `x` ([1.0, \
2.0, and 3.0]) and `y` ([1.0, 2.0, and 3.5]), the following error occurred: `spline` \
is not a supported interpolation method.  Please select "linear", "cubic", "akima", \
or "pchip" or pass a subclass of SciPy's `CubicHermiteSpline` class.

        |PPoly| also checks the type of the method argument, even if the given data
        set contains so few x-y pairs that it does not need a spline at all:

        >>> class MyOtherSpline:
        ...     pass
        >>> PPoly.from_data(xs=[0.0, 1.0], ys=[2.0, 5.0], method=MyOtherSpline)
        Traceback (most recent call last):
        ...
        TypeError: While trying to derive polynomials from the vectors `x` ([0.0 and \
1.0]) and `y` ([2.0 and 5.0]), the following error occurred: `MyOtherSpline` is not a \
supported interpolation method.  Please select "linear", "cubic", "akima", or \
"pchip" or pass a subclass of SciPy's `CubicHermiteSpline` class.

        Passing data sets with one or two x-y pairs works fine:

        >>> PPoly.from_data(xs=[0.0], ys=[1.0]).polynomials
        (Poly(x0=0.0, cs=(1.0,)),)

        >>> PPoly.from_data(xs=[0.0, 1.0], ys=[2.0, 5.0]).polynomials
        (Poly(x0=0.0, cs=(2.0, 3.0)),)

        Empty data sets or data sets of different lengths result in the following
        error messages:

        >>> PPoly.from_data(xs=[], ys=[])
        Traceback (most recent call last):
        ...
        ValueError: While trying to derive polynomials from the vectors `x` ([]) and \
`y` ([]), the following error occurred: Vectors `x` and `y` must not be empty.

        >>> PPoly.from_data(xs=[0.0, 1.0], ys=[1.0, 2.0, 3.0])
        Traceback (most recent call last):
        ...
        ValueError: While trying to derive polynomials from the vectors `x` ([0.0 and \
1.0]) and `y` ([1.0, 2.0, and 3.0]), the following error occurred: The lenghts of \
vectors `x` (2) and `y` (3) must be identical.
        """
        self = cls._make_self()
        self._use_data(xs=xs, ys=ys, method=method)
        return self

    def _use_data(
        self,
        xs: VectorInputFloat,
        ys: VectorInputFloat,
        method: MethodNames | type[interpolate.CubicHermiteSpline] = "linear",
    ) -> None:

        def _make_error_message(method: object, /) -> str:
            methodname = method.__name__ if inspect.isclass(method) else method
            return (
                f"`{methodname}` is not a supported interpolation method.  Please "
                f'select "linear", "cubic", "akima", or "pchip" or pass a subclass of '
                f"SciPy's `CubicHermiteSpline` class."
            )

        try:
            name: MethodNames | None
            spline: type[interpolate.CubicHermiteSpline] | None
            if isinstance(method, str):
                if method not in ("linear", "cubic", "akima", "pchip"):
                    raise ValueError(_make_error_message(method))
                name = method
                spline = _get_splineclass(name)
            else:
                if not (
                    inspect.isclass(method)
                    and issubclass(method, interpolate.CubicHermiteSpline)
                ):
                    raise TypeError(_make_error_message(method))
                name = _get_splinename(method)
                spline = method
            xs = numpy.asarray(xs, dtype=config.NP_FLOAT)
            ys = numpy.asarray(ys, dtype=config.NP_FLOAT)
            if len(xs) != len(ys):
                raise ValueError(
                    f"The lenghts of vectors `x` ({len(xs)}) and `y` ({len(ys)}) "
                    f"must be identical."
                )
            if len(xs) == 0:
                raise ValueError("Vectors `x` and `y` must not be empty.")
            if len(xs) == 1:
                nmb_ps = 1
                nmb_cs = numpy.full((nmb_ps,), 1, dtype=config.NP_INT)
                x0s = xs.copy()
                cs = ys.copy().reshape((1, 1))
            elif (len(xs) == 2) or (spline is None):
                nmb_ps = len(xs) - 1
                nmb_cs = numpy.full((nmb_ps,), 2, dtype=config.NP_INT)
                x0s = xs[:-1].copy()
                cs = numpy.zeros((nmb_ps, numpy.max(nmb_cs)), dtype=config.NP_FLOAT)
                cs[:, 0] = ys[:-1]
                cs[:, 1] = numpy.diff(ys) / numpy.diff(xs)
            else:
                # Mypy bug?
                interpolator = spline(x=xs, y=ys)  # type: ignore[call-arg]
                x0s = xs[:-1].copy()
                cs = interpolator.c[::-1].T  # type: ignore[union-attr]
                nmb_ps = len(x0s)
                nmb_cs = numpy.asarray(
                    [numpy.max(numpy.nonzero(cs_), initial=0) + 1 for cs_ in cs],
                    dtype=config.NP_INT,
                )
            self.nmb_ps, self.nmb_cs, self.x0s, self.cs = nmb_ps, nmb_cs, x0s, cs
            if name is None:
                self._original_data = None
            else:
                self._original_data = _OriginalData(
                    xs=xs.copy(), ys=ys.copy(), method=name
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to derive polynomials from the vectors `x` "
                f"([{objecttools.enumeration(xs, objecttools.repr_)}]) and `y` "
                f"([{objecttools.enumeration(ys, objecttools.repr_)}])"
            )

    def _get_nmb_inputs(self) -> Literal[1]:
        """The number of input values.

        |PPoly| is a univariate interpolator.  Hence, |PPoly.nmb_inputs| is always one:

        >>> from hydpy import PPoly
        >>> PPoly().nmb_inputs
        1
        """
        return 1

    nmb_inputs = propertytools.Property[Never, Literal[1]](fget=_get_nmb_inputs)

    def _get_inputs(self) -> VectorFloat:
        """The current input value.

        |PPoly| is a univariate interpolator.  Hence, |PPoly.inputs| always returns a
        vector with a single entry:

        >>> from hydpy import PPoly, print_vector
        >>> print_vector(PPoly().inputs)
        0.0
        """
        return numpy.asarray(self._calgorithm.inputs)

    inputs = propertytools.Property[Never, VectorFloat](fget=_get_inputs)

    def _get_nmb_outputs(self) -> Literal[1]:
        """The number of output values.

        |PPoly| is a univariate interpolator.  Hence, |PPoly.nmb_outputs| is always
        one:

        >>> from hydpy import PPoly
        >>> PPoly().nmb_inputs
        1
        """
        return 1

    nmb_outputs = propertytools.Property[Never, Literal[1]](fget=_get_nmb_outputs)

    def _get_outputs(self) -> VectorFloat:
        """The last calculated output value.

        |PPoly| is a univariate interpolator.  Hence, |PPoly.outputs| always returns a
        vector with a single entry:

        >>> from hydpy import PPoly, print_vector
        >>> print_vector(PPoly().outputs)
        0.0
        """
        return numpy.asarray(self._calgorithm.outputs)

    outputs = propertytools.Property[Never, VectorFloat](fget=_get_outputs)

    def _get_output_derivatives(self) -> VectorFloat:
        """The last calculated first-order derivative.

        |PPoly| is a univariate interpolator.  Hence, |PPoly.output_derivatives|
        always returns a vector with a single entry:

        >>> from hydpy import PPoly, print_vector
        >>> print_vector(PPoly().output_derivatives)
        0.0
        """
        return numpy.asarray(self._calgorithm.output_derivatives)

    output_derivatives = propertytools.Property[Never, VectorFloat](
        fget=_get_output_derivatives
    )

    def _get_nmb_ps(self) -> int:
        """The number of polynomials.

        |PPoly.nmb_ps| is "protected" (implemented by |ProtectedProperty|) for the sake
        of preventing segmentation faults when trying to access the related data from
        the underlying Cython extension class before allocation:

        >>> from hydpy import PPoly
        >>> ppoly = PPoly()
        >>> ppoly.nmb_ps = 1
        >>> ppoly.nmb_ps
        1
        >>> del ppoly.nmb_ps
        >>> ppoly.nmb_ps
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `nmb_ps` of object \
`ppoly` has not been prepared so far.
        """
        return self._calgorithm.nmb_ps

    def _set_nmb_ps(self, value: int) -> None:
        self._calgorithm.nmb_ps = int(value)

    def _del_nmb_ps(self) -> None:
        pass

    nmb_ps = propertytools.ProtectedProperty[int, int](
        fget=_get_nmb_ps, fset=_set_nmb_ps, fdel=_del_nmb_ps
    )

    def _get_nmb_cs(self) -> VectorInt:
        """The number of relevant coefficients for each polynomial.

        |PPoly.nmb_cs| is "protected" (implemented by |ProtectedProperty|) for the sake
        of preventing segmentation faults when trying to access the related data from
        the underlying Cython extension class before allocation:

        >>> from hydpy import PPoly, print_vector
        >>> ppoly = PPoly()
        >>> ppoly.nmb_cs = 1, 2
        >>> print_vector(ppoly.nmb_cs)
        1, 2
        >>> del ppoly.nmb_cs
        >>> ppoly.nmb_cs
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `nmb_cs` of object \
`ppoly` has not been prepared so far.
        """
        return numpy.asarray(self._calgorithm.nmb_cs)

    def _set_nmb_cs(self, value: VectorInputInt) -> None:
        self._calgorithm.nmb_cs = numpy.asarray(value, dtype=config.NP_INT)

    def _del_nmb_cs(self) -> None:
        pass

    nmb_cs = propertytools.ProtectedProperty[VectorInputInt, VectorInt](
        fget=_get_nmb_cs, fset=_set_nmb_cs, fdel=_del_nmb_cs
    )

    def _get_x0s(self) -> VectorFloat:
        """The power series constants of all polynomials.

        |PPoly.x0s| is "protected" (implemented by |ProtectedProperty|) for the sake of
        preventing segmentation faults when trying to access the related data from the
        underlying Cython extension class before allocation:

        >>> from hydpy import PPoly, print_vector
        >>> ppoly = PPoly()
        >>> ppoly.x0s = 1.0, 2.0
        >>> print_vector(ppoly.x0s)
        1.0, 2.0
        >>> del ppoly.x0s
        >>> ppoly.x0s
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `x0s` of object \
`ppoly` has not been prepared so far.
        """
        return numpy.asarray(self._calgorithm.x0s)

    def _set_x0s(self, value: VectorInputFloat) -> None:
        self._calgorithm.x0s = numpy.asarray(value, dtype=config.NP_FLOAT)

    def _del_x0s(self) -> None:
        pass

    x0s = propertytools.ProtectedProperty[VectorInputFloat, VectorFloat](
        fget=_get_x0s, fset=_set_x0s, fdel=_del_x0s
    )

    def _get_cs(self) -> MatrixFloat:
        """The power series coefficients of all polynomials.

        |PPoly.cs| is "protected" (implemented by |ProtectedProperty|) for the sake of
        preventing segmentation faults when trying to access the related data from the
        underlying Cython extension class before allocation:

        >>> from hydpy import PPoly, print_matrix
        >>> ppoly = PPoly()
        >>> ppoly.cs = [[1.0, 2.0], [3.0, 4.0]]
        >>> print_matrix(ppoly.cs)
        | 1.0, 2.0 |
        | 3.0, 4.0 |
        >>> del ppoly.cs
        >>> ppoly.cs
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `cs` of object `ppoly` \
has not been prepared so far.
        """
        return numpy.asarray(self._calgorithm.cs)

    def _set_cs(self, value: MatrixInputFloat) -> None:
        self._calgorithm.cs = numpy.asarray(value, dtype=config.NP_FLOAT)

    def _del_cs(self) -> None:
        pass

    cs = propertytools.ProtectedProperty[MatrixInputFloat, MatrixFloat](
        fget=_get_cs, fset=_set_cs, fdel=_del_cs
    )

    def calculate_values(self) -> None:
        """Calculate the output value based on the input values defined previously.

        For more information, see the documentation on class |ppolytools.PPoly|.
        """
        self._calgorithm.calculate_values()

    def calculate_derivatives(self, idx: int = 0, /) -> None:
        """Calculate the derivative of the output value with respect to the input value.

        For more information, see the documentation on class |ppolytools.PPoly|.
        """
        self._calgorithm.calculate_derivatives(idx)

    @property
    def polynomials(self) -> tuple[Poly, ...]:
        """The configuration of the current |ppolytools.PPoly| object, represented by a
        tuple of |Poly| objects.

        >>> from hydpy import Poly, PPoly
        >>> ppoly = PPoly(Poly(x0=1.0, cs=(1.0,)), Poly(x0=2.0, cs=(1.0, 1.0)))
        >>> ppoly.polynomials
        (Poly(x0=1.0, cs=(1.0,)), Poly(x0=2.0, cs=(1.0, 1.0)))
        """
        return tuple(
            Poly(x0=x0, cs=tuple(cs[:n]))
            for x0, cs, n in zip(self.x0s, self.cs, self.nmb_cs)
        )

    def sort(self) -> None:
        """Sort the currently handled polynomials.

        The power series constants held by array |ppolytools.PPoly.x0s| also
        serve as breakpoints, defining the lower bounds of the intervals for which the
        available polynomials are valid. The algorithm underlying |PPoly| expects them
        in sorted order.

        In the following example, we hand over two wrongly-ordered |Poly| objects:

        >>> from hydpy import Poly, PPoly, print_matrix, print_vector
        >>> ppoly = PPoly(Poly(x0=2.0, cs=(1.0, 1.0)), Poly(x0=1.0, cs=(1.0,)))
        >>> ppoly.polynomials
        (Poly(x0=2.0, cs=(1.0, 1.0)), Poly(x0=1.0, cs=(1.0,)))
        >>> print_vector(ppoly.x0s)
        2.0, 1.0
        >>> print_vector(ppoly.nmb_cs)
        2, 1
        >>> print_matrix(ppoly.cs)
        | 1.0, 1.0 |
        | 1.0, 0.0 |

        Method |ppolytools.PPoly.sort| sorts |ppolytools.PPoly.x0s| and the related
        arrays |ppolytools.PPoly.nmb_cs| and |ppolytools.PPoly.cs|:

        >>> ppoly.sort()
        >>> ppoly.polynomials
        (Poly(x0=1.0, cs=(1.0,)), Poly(x0=2.0, cs=(1.0, 1.0)))
        >>> print_vector(ppoly.x0s)
        1.0, 2.0
        >>> print_vector(ppoly.nmb_cs)
        1, 2
        >>> print_matrix(ppoly.cs)
        | 1.0, 0.0 |
        | 1.0, 1.0 |
        """
        idxs: VectorInt = numpy.argsort(self.x0s)
        self.x0s = self.x0s[idxs]
        self.nmb_cs = self.nmb_cs[idxs]
        self.cs = self.cs[idxs, :]

    def verify(self) -> None:
        """Raise a |RuntimeError| if the current |ppolytools.PPoly| object shows
        inconsistencies.

        Note that |ppolytools.PPoly| never calls |ppolytools.PPoly.verify|
        automatically.  Hence, we strongly advise applying it manually before using a
        new |ppolytools.PPoly| configuration the first time.

        So far, method |ppolytools.PPoly.verify| reports the following problems:

        >>> from hydpy import PPoly
        >>> ppoly = PPoly(Poly(x0=2.0, cs=(1.0, 1.0)), Poly(x0=1.0, cs=(1.0,)))
        >>> ppoly.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to verify parameter `ppoly` of element `?`, the \
following error occurred: The constants held in vector `x0s` are not strictly \
increasing, which is necessary as they also serve as breakpoints for selecting the \
relevant polynomials.

        >>> ppoly.sort()
        >>> ppoly.verify()

        >>> ppoly.nmb_cs[1] = 3
        >>> ppoly.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to verify parameter `ppoly` of element `?`, the \
following error occurred: The highest number of coefficients indicated by `nmb_cs` \
(3) is larger than the possible number of coefficients storable in the coefficient \
matrix `cs` (2).

        >>> ppoly.cs = ppoly.cs[:1, :]
        >>> ppoly.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to verify parameter `ppoly` of element `?`, the \
following error occurred: The number of polynomials indicated by `nmb_ps` (2) does \
not agree with the actual number of coefficient arrays held by matrix `cs` (1).

        >>> ppoly.x0s = ppoly.x0s[:1]
        >>> ppoly.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to verify parameter `ppoly` of element `?`, the \
following error occurred: The number of constants indicated by `nmb_ps` (2) does not \
agree with the actual number of constants held by vector `x0s` (1).
        """
        try:
            if self.nmb_ps != len(self.x0s):
                raise RuntimeError(
                    f"The number of constants indicated by `nmb_ps` ({self.nmb_ps}) "
                    f"does not agree with the actual number of constants held by "
                    f"vector `x0s` ({len(self.x0s)})."
                )
            if self.nmb_ps != len(self.cs):
                raise RuntimeError(
                    f"The number of polynomials indicated by `nmb_ps` ({self.nmb_ps}) "
                    f"does not agree with the actual number of coefficient arrays held "
                    f"by matrix `cs` ({len(self.cs)})."
                )
            if numpy.max(self.nmb_cs) > self.cs.shape[1]:
                raise RuntimeError(
                    f"The highest number of coefficients indicated by `nmb_cs` "
                    f"({numpy.max(self.nmb_cs)}) is larger than the possible number of "
                    f"coefficients storable in the coefficient matrix `cs` "
                    f"({self.cs.shape[1]})."
                )
            if (self.nmb_ps > 1) and (numpy.min(numpy.diff(self.x0s)) <= 0.0):
                raise RuntimeError(
                    "The constants held in vector `x0s` are not strictly increasing, "
                    "which is necessary as they also serve as breakpoints for "
                    "selecting the relevant polynomials."
                )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to verify parameter {objecttools.elementphrase(self)}"
            )

    def _data_agrees(self, data: _OriginalData, /) -> bool:
        """Tell whether the polynomials estimated from the given original x-y data
        agree with the current polynomials."""
        with numpy.errstate(divide="ignore", invalid="ignore"):
            other = type(self).from_data(*data)
        try:
            return (
                (self.nmb_ps == other.nmb_ps)
                and numpy.array_equal(self.nmb_cs, other.nmb_cs)
                and numpy.array_equal(self.x0s, other.x0s, equal_nan=True)
                and numpy.array_equal(self.cs, other.cs, equal_nan=True)
            )
        except exceptiontools.AttributeNotReady:
            return False

    def assignrepr(self, prefix: str, indent: int = 0) -> str:
        """Return a string representation of the actual |ppolytools.PPoly| object
        prefixed with the given string.

        If you define the polynomials directly, the string representation lists the
        corresponding |Poly| objects:

        >>> from hydpy import Poly, PPoly
        >>> ppoly = PPoly(Poly(x0=1.0, cs=(1.0,)), Poly(x0=2.0, cs=(1.0, 1.0)))
        >>> ppoly
        PPoly(
            Poly(x0=1.0, cs=(1.0,)),
            Poly(x0=2.0, cs=(1.0, 1.0)),
        )
        >>> print(ppoly.assignrepr(prefix="    ppoly = ", indent=4))
            ppoly = PPoly(
                Poly(x0=1.0, cs=(1.0,)),
                Poly(x0=2.0, cs=(1.0, 1.0)),
            )

        If you let |PPoly| estimate the polynomials from x-y data, the string
        representation shows this data instead, which is usually easier to
        understand.  It includes the selected interpolation method only if it is not
        the default one (linear):

        >>> ppoly = PPoly(xs=[1.0, 2.0, 3.0], ys=[1.0, 2.0, 3.5])
        >>> ppoly
        PPoly(
            xs=[1.0, 2.0, 3.0],
            ys=[1.0, 2.0, 3.5],
        )
        >>> ppoly(xs=[1.0, 2.0, 3.0], ys=[1.0, 2.0, 3.5], method="pchip")
        >>> print(ppoly.assignrepr(prefix="    ppoly = ", indent=4))
            ppoly = PPoly(
                xs=[1.0, 2.0, 3.0],
                ys=[1.0, 2.0, 3.5],
                method="pchip",
            )

        Long data vectors are wrapped:

        >>> PPoly(xs=range(30), ys=range(30))
        PPoly(
            xs=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,
                13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0,
                25.0, 26.0, 27.0, 28.0, 29.0],
            ys=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,
                13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0,
                25.0, 26.0, 27.0, 28.0, 29.0],
        )

        The string representation must allow for recreating |PPoly| objects (for
        example, when reading control files).  Hence, it ignores the |Options.ellipsis|
        option:

        >>> from hydpy import pub
        >>> with pub.options.ellipsis(1):
        ...     PPoly(xs=[0.0, 1.0, 2.0, 3.0], ys=[0.0, 1.0, 4.0, 9.0])
        PPoly(
            xs=[0.0, 1.0, 2.0, 3.0],
            ys=[0.0, 1.0, 4.0, 9.0],
        )

        |PPoly| converts the given data to 64-bit floating-point numbers before
        estimating the polynomials, so other data types produce consistent string
        representations, too:

        >>> import numpy
        >>> PPoly(
        ...     xs=numpy.array([0.0, 0.3, 1.0], dtype=numpy.float32),
        ...     ys=numpy.array([0.0, 0.7, 0.9], dtype=numpy.float32),
        ... )
        PPoly(
            xs=[0.0, 0.3, 1.0],
            ys=[0.0, 0.7, 0.9],
        )

        The same holds for data containing |numpy.nan| values or duplicate x values,
        which result in useless polynomials but, at least, consistent string
        representations:

        >>> from numpy import nan
        >>> PPoly(xs=[1.0, 2.0, 3.0], ys=[1.0, nan, 3.0])
        PPoly(
            xs=[1.0, 2.0, 3.0],
            ys=[1.0, nan, 3.0],
        )
        >>> import warnings
        >>> with warnings.catch_warnings():
        ...     warnings.simplefilter("ignore")
        ...     duplicates = PPoly(xs=[1.0, 1.0, 2.0], ys=[1.0, 2.0, 3.0])
        >>> duplicates
        PPoly(
            xs=[1.0, 1.0, 2.0],
            ys=[1.0, 2.0, 3.0],
        )

        |PPoly| remembers the original data but cannot reconstruct it from the
        polynomials.  Hence, if you modify the polynomials after their estimation, the
        string representation falls back to listing |Poly| objects:

        >>> ppoly.cs[1, 1] = 2.0
        >>> ppoly
        PPoly(
            Poly(x0=1.0, cs=(1.0, 0.75, 0.3, -0.05)),
            Poly(x0=2.0, cs=(2.0, 2.0, 0.35, -0.05)),
        )

        The same holds for incompletely configured |PPoly| objects:

        >>> ppoly = PPoly(xs=[1.0, 2.0], ys=[1.0, 2.0])
        >>> del ppoly.nmb_ps
        >>> ppoly
        PPoly(
            Poly(x0=1.0, cs=(1.0, 1.0)),
        )
        """
        blanks = (indent + 4) * " "
        lines = [f"{prefix}{type(self).__name__}("]
        data = self._original_data
        if (data is not None) and self._data_agrees(data):
            with hydpy.pub.options.ellipsis(0):
                for name, values in (("xs", data.xs), ("ys", data.ys)):
                    lines.append(
                        objecttools.assignrepr_list(
                            values, f"{blanks}{name}=", width=79
                        )
                        + ","
                    )
            if data.method != "linear":
                lines.append(f'{blanks}method="{data.method}",')
        else:
            lines.extend(f"{blanks}{poly}," for poly in self.polynomials)
        lines.append(f'{indent*" "})')
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.assignrepr(prefix="", indent=0)
