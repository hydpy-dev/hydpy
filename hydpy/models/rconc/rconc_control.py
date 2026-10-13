# pylint: disable=missing-module-docstring

from __future__ import annotations
import math
from typing import Literal

import numpy

from hydpy import config
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class _AllowedKeywordArgsOfClassUH(TypedDict, total=False):
    """A |TypedDict| that holds the allowed keyword arguments of the `__call__` method
    of class |UH|."""

    tb: float
    tp: float | None
    x4: float
    beta: float
    auxfile: str


class UH(parametertools.Parameter):
    """Unit Hydrograph ordinates [-].

    The ordinates of the unit hydrograph can be set directly by calling the |UH|
    instance with a list of float values as one positional argument:

    >>> from hydpy.models.rconc import *
    >>> simulationstep("1d")
    >>> parameterstep("1d")
    >>> uh([0.1,0.2,0.4,0.2,0.1])
    >>> logs.quh = 0.0, 0.0, 0.0, 0.0, 0.0
    >>> uh
    uh(0.1, 0.2, 0.4, 0.2, 0.1)

    Like for other 1-dimensional parameters, passing the ordinates as separate
    positional arguments works as well:

    >>> uh(0.2, 0.6, 0.2)
    >>> uh
    uh(0.2, 0.6, 0.2)

    The number of the given ordinates determines the parameter's shape.  Hence, its
    string representation never combines identical ordinates into a single value:

    >>> uh(0.5, 0.5)
    >>> uh
    uh(0.5, 0.5)
    >>> uh(1.0)
    >>> uh
    uh(1.0)

    The ordinates must be given as a 1-dimensional sequence:

    >>> uh([[0.5], [0.5]])
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: The ordinates must be given as a 1-dimensional sequence, \
but the given values are 2-dimensional.

    >>> uh()
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Neither the ordinates, nor a predefined geometry, nor an \
auxiliary file is given.

    Alternatively, implemented geometries can be specified via a positional 'option'
    parameter and parameterised with the corresponding arguments.

    We generate the ordinates of a unit hydrograph in the form of an isosceles triangle
    with a base length of 10 days:

    >>> uh("triangle", tb=10.0)
    >>> uh
    uh("triangle", tb=10.0)
    >>> from hydpy import print_vector
    >>> print_vector(uh.values)
    0.02, 0.06, 0.1, 0.14, 0.18, 0.18, 0.14, 0.1, 0.06, 0.02

    The value of `tb` depends on the current parameter step size:

    >>> from hydpy import pub
    >>> with pub.options.parameterstep("2d"):
    ...     uh
    uh("triangle", tb=5.0)

    Omitting the option string or passing additional positional arguments results in
    an error:

    >>> uh(tb=10.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: When selecting a predefined geometry, you must pass the \
option string as the only positional argument and its parameters as keyword arguments.

    >>> uh([0.1,0.2,0.1], "triangle", tb=10.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: When selecting a predefined geometry, you must pass the \
option string as the only positional argument and its parameters as keyword arguments.

    If an unknown option is given, |UH| points to the supported ones:

    >>> uh("rectangle", tb=10.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Option `rectangle` is unknown.  Available options are \
`triangle`, `gr_uh1`, and `gr_uh2`.

    The optional argument 'tp' specifies the position of the peak:

    >>> uh("triangle", tb=10.0, tp=7.0)
    >>> uh
    uh("triangle", tb=10.0, tp=7.0)
    >>> print_vector(uh.values)
    0.014286, 0.042857, 0.071429, 0.1, 0.128571, 0.157143, 0.185714,
    0.166667, 0.1, 0.033333

    Any positive real numbers are allowed:

    >>> uh("triangle", tb=9.5, tp=6.7)
    >>> uh
    uh("triangle", tb=9.5, tp=6.7)
    >>> print_vector(uh.values)
    0.015711, 0.047133, 0.078555, 0.109976, 0.141398, 0.17282, 0.199445,
    0.150376, 0.075188, 0.009398

    Passing |None| for 'tp' is the same as omitting it:

    >>> uh("triangle", tb=10.0, tp=None)
    >>> uh
    uh("triangle", tb=10.0)

    Parameter 'tp' must not be greater than 'tb'.  After such a failed call, |UH|
    keeps its previous ordinates, and its string representation reports them instead
    of the rejected geometry:

    >>> uh("triangle", tb=2.0)
    >>> uh("triangle", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Parameter 'tp' must not be greater than 'tb'.
    >>> uh
    uh(0.5, 0.5)

    In addition to the HBV96-oriented triangular unit hydrograph (with the general
    purpose of damping the flood pulse; see :cite:t:`ref-Harlin1992`), the unit
    hydrographs used in the GR4J model (which reflect the outflow of the two
    conceptional storages used in this approach; see :cite:t:`ref-Perrin2007`) are also
    available:

    >>> uh("gr_uh1", x4=6.3)
    >>> uh
    uh("gr_uh1", x4=6.3)
    >>> print_vector(uh.values)
    0.010038, 0.046746, 0.099694, 0.16474, 0.239926, 0.324027, 0.11483

    >>> uh("gr_uh1", x4=0.8)
    >>> print_vector(uh.values)
    1.0

    >>> uh("gr_uh2", x4=2.8)
    >>> uh
    uh("gr_uh2", x4=2.8)
    >>> print_vector(uh.values)
    0.038113, 0.177487, 0.368959, 0.292023, 0.112789, 0.010628

    >>> uh("gr_uh2", x4=0.8)
    >>> print_vector(uh.values)
    0.75643, 0.24357

    According to :cite:t:`ref-Perrin2007`, the exponent 'beta' is 2.5 by default but can
    be changed:

    >>> uh("gr_uh1", x4=6.3, beta=1.5)
    >>> print_vector(uh.values)
    0.06324, 0.115629, 0.149734, 0.177314, 0.201123, 0.222388, 0.070571

    >>> uh("gr_uh2", x4=2.8, beta=1.5)
    >>> print_vector(uh.values)
    0.106717, 0.195124, 0.250762, 0.231417, 0.166382, 0.049598

    The triangle unit hydrograph must not be called with the parameters for the
    GR4J-like unit hydrograph:

    >>> uh("triangle", x4=2.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Wrong arguments for option `triangle`.

    The GR4J-based options cannot be mixed with the triangle parameters:

    >>> uh("gr_uh1", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Wrong arguments for option `gr_uh1`.

    >>> uh("gr_uh2", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Wrong arguments for option `gr_uh2`.

    The following tests examine the correct calculation of ordinates in edge cases:

    >>> uh("gr_uh2", x4=0.4)
    >>> print_vector(uh.values)
    1.0

    >>> uh("gr_uh2", x4=0.0)
    >>> print_vector(uh.values)
    1.0

    >>> uh("gr_uh2", x4=1.0)
    >>> print_vector(uh.values)
    0.5, 0.5

    >>> uh("gr_uh2", x4=1.5)
    >>> print_vector(uh.values)
    0.181444, 0.637113, 0.181444

    |UH| adjusts the shape of the log sequence |QUH| to the number of ordinates.  To
    prevent losing information, it does so only when necessary:

    >>> logs.quh = 1.0, 2.0, 0.0
    >>> uh([0.2, 0.5, 0.3])
    >>> logs.quh
    quh(1.0, 2.0, 0.0)
    >>> uh("triangle", tb=3.0)
    >>> logs.quh
    quh(1.0, 2.0, 0.0)
    >>> uh("gr_uh2", x4=1.5)
    >>> logs.quh
    quh(1.0, 2.0, 0.0)

    Changing the number of ordinates resets the logged values:

    >>> uh("gr_uh1", x4=0.8)
    >>> logs.quh
    quh(nan)

    Like other parameters, |UH| supports taking its ordinates from auxiliary control
    files.  The following example writes an auxiliary file, which defines a triangle
    unit hydrograph, and lets |UH| read it.  The string representation then reflects
    the definition given in the auxiliary file, and |QUH| is adjusted as usual:

    >>> from hydpy import TestIO
    >>> with TestIO(clear_own=True):
    ...     with open("uh_aux.py", "w", encoding="utf-8") as file_:
    ...         for line in (
    ...             "from hydpy.models.rconc import *",
    ...             "simulationstep('1d')",
    ...             "parameterstep('1d')",
    ...             "uh('triangle', tb=3.0)",
    ...         ):
    ...             print(line, file=file_)
    ...     uh(auxfile="uh_aux")
    >>> uh
    uh("triangle", tb=3.0)
    >>> print_vector(uh.values)
    0.222222, 0.555556, 0.222222
    >>> logs.quh
    quh(nan, nan, nan)

    As usual, you cannot combine the `auxfile` keyword with other arguments:

    >>> uh("triangle", auxfile="uh_aux")
    Traceback (most recent call last):
    ...
    ValueError: For parameter `uh` of element `?` both positional and keyword \
arguments are given, which is ambiguous.
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, 1.0)
    strict_valuehandling: bool = False

    KEYWORDS = {
        "tb": parametertools.Keyword(name="tb", time=False),
        "tp": parametertools.Keyword(name="tp", time=False),
        "x4": parametertools.Keyword(name="x4", time=False),
        "beta": parametertools.Keyword(name="beta", time=False),
    }

    @overload
    def __call__(self, value: VectorInputFloat, /) -> None: ...

    @overload
    def __call__(self, *values: float) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    @overload
    def __call__(
        self, option: Literal["triangle"], /, *, tb: float, tp: float | None = None
    ) -> None: ...

    @overload
    def __call__(
        self, option: Literal["gr_uh1", "gr_uh2"], /, *, x4: float, beta: float = 2.5
    ) -> None: ...

    def __call__(
        self,
        *args: VectorInputFloat | float | str,
        **kwargs: Unpack[_AllowedKeywordArgsOfClassUH],
    ) -> None:
        self._keywordarguments = parametertools.KeywordArguments(False)
        if "auxfile" in kwargs:
            super().__call__(*args, **kwargs)
            return
        try:
            if kwargs or any(isinstance(arg, str) for arg in args):
                if (len(args) != 1) or not isinstance(option := args[0], str):
                    raise ValueError(
                        "When selecting a predefined geometry, you must pass the "
                        "option string as the only positional argument and its "
                        "parameters as keyword arguments."
                    )
                self._set_geometry(option, kwargs)
            else:
                if not args:
                    raise ValueError(
                        "Neither the ordinates, nor a predefined geometry, nor an "
                        "auxiliary file is given."
                    )
                self._set_ordinates(args)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the values of parameter "
                f"{objecttools.elementphrase(self)}"
            )

    def _set_ordinates(self, args: tuple[VectorInputFloat | float | str, ...]) -> None:
        ordinates = numpy.array(
            args[0] if len(args) == 1 else args, dtype=config.NP_FLOAT, ndmin=1
        )
        if ordinates.ndim != 1:
            raise ValueError(
                f"The ordinates must be given as a 1-dimensional sequence, but the "
                f"given values are {ordinates.ndim}-dimensional."
            )
        self.shape = len(ordinates)
        self._adjust_quh_shape()
        self.values = ordinates

    def _set_geometry(self, option: str, kwargs: _AllowedKeywordArgsOfClassUH) -> None:
        if option not in ("triangle", "gr_uh1", "gr_uh2"):
            raise ValueError(
                f"Option `{option}` is unknown.  Available options are `triangle`, "
                f"`gr_uh1`, and `gr_uh2`."
            )
        idx = self._find_kwargscombination(
            (), dict(kwargs), ({"tb"}, {"tb", "tp"}, {"x4"}, {"x4", "beta"})
        )
        if idx not in ((0, 1) if option == "triangle" else (2, 3)):
            raise ValueError(f"Wrong arguments for option `{option}`.")
        if option == "triangle":
            self._set_triangle(kwargs)
        else:
            self._set_gr_uh(option, kwargs)

    def _set_triangle(self, kwargs: _AllowedKeywordArgsOfClassUH) -> None:
        tb = kwargs["tb"] / self.get_timefactor()
        if (tp := kwargs.get("tp")) is None:
            keywordarguments = parametertools.KeywordArguments(option="triangle", tb=tb)
        else:
            tp /= self.get_timefactor()
            keywordarguments = parametertools.KeywordArguments(
                option="triangle", tb=tb, tp=tp
            )
        self._set_triangle_uh(tb=tb, tp=tp)
        self._keywordarguments = keywordarguments

    def _set_gr_uh(self, option: str, kwargs: _AllowedKeywordArgsOfClassUH) -> None:
        x4 = kwargs["x4"] / self.get_timefactor()
        if (beta := kwargs.get("beta")) is None:
            beta = 2.5
            keywordarguments = parametertools.KeywordArguments(option=option, x4=x4)
        else:
            keywordarguments = parametertools.KeywordArguments(
                option=option, x4=x4, beta=beta
            )
        if option == "gr_uh1":
            self._set_gr_uh1(x4=x4, beta=beta)
        else:
            self._set_gr_uh2(x4=x4, beta=beta)
        self._keywordarguments = keywordarguments

    def _adjust_quh_shape(self) -> None:
        """Adjust the shape of log sequence |QUH| to the current shape of |UH| if
        necessary."""
        quh = self.subpars.pars.model.sequences.logs.quh
        quh.__hydpy__change_shape_if_necessary__(self.shape)

    def _set_triangle_uh(self, tb: float, tp: float | None = None) -> None:
        """Calculate and set the ordinates of a triangle unit hydrograph."""

        # Determine UH parameters...
        if tb <= 1.0:
            # ...when Tb smaller than or equal to the simulation time step.
            self.shape = 1
            self._adjust_quh_shape()
            self.values = 1.0
        else:
            full = tb
            # Now comes a terrible trick due to rounding problems coming from
            # the conversation of the SMHI parameter set to the HydPy
            # parameter set.  Time to get rid of it...
            if (full % 1.0) < 1e-4:
                full //= 1.0
            full_f = int(math.floor(full))
            full_c = int(math.ceil(full))
            if not tp:
                peak = full / 2.0
            else:
                if tp > tb:
                    raise ValueError("Parameter 'tp' must not be greater than 'tb'.")
                peak = tp
            peak_f = int(math.floor(peak))
            peak_c = int(math.ceil(peak))
            # Calculate the triangle ordinate(s)...
            self.shape = full_c
            uh = self.values.copy()
            self._adjust_quh_shape()
            slope1 = 1 / peak
            slope2 = -1 / (full - peak)
            # ...of the rising limb.
            points = numpy.arange(1, peak_f + 1)
            uh[:peak_f] = slope1 * (points - 0.5)
            # ...around the peak (if it exists).
            if numpy.mod(peak, 1.0) != 0.0:
                uh[peak_c - 1] = (
                    slope1 * (peak**2 - peak_f**2) / 2
                    + slope2 * (peak_c - peak) ** 2 / 2
                    + peak_c
                    - peak
                )
            # ...of the falling limb (eventually except the last one).
            points = numpy.arange(1, full_f - peak_c + 1)
            uh[peak_c:full_f] = slope2 * (points + peak_c - peak - 0.5) + 1
            # ...at the end (if not already done).
            if numpy.mod(full, 1.0) != 0.0:
                uh[full_c - 1] = (
                    slope2 * 0.5 * ((full - peak) ** 2 - (full_f - peak) ** 2)
                    + full
                    - full_f
                )
            # Normalize the ordinates.
            uh[:] = uh / numpy.sum(uh)
            self.values = uh

    def _set_gr_uh1(self, x4: float, beta: float = 2.5) -> None:
        """Calculate and set the ordinates of a unit hydrograph as done by GR4J for
        modifying base flow.
        """
        self.shape, self.values = self._det_gr_uh(x4=x4, beta=beta, left=True)
        self._adjust_quh_shape()

    def _set_gr_uh2(self, x4: float, beta: float = 2.5) -> None:
        """Calculate and set the ordinates of a unit hydrograph as done by GR4J for
        modifying direct runoff."""
        shape_left, values_left = self._det_gr_uh(x4=x4, beta=beta, left=True)
        shape_right, values_right = self._det_gr_uh(x4=x4, beta=beta, left=False)
        self.shape = shape_left + shape_right - 1
        self._adjust_quh_shape()
        self.values[:] = 0.0
        self.values[:shape_left] = values_left / 2.0
        self.values[-shape_right:] += values_right / 2.0

    def _det_gr_uh(self, x4: float, beta: float, left: bool) -> tuple[int, VectorFloat]:
        """Determine the shape and the ordinates of a GR4J-like (part of a) unit
        hydrograph.

        `left` means the rising limb and corresponds to "uh1" and the left part of
        "uh2".
        """
        if (x4 <= 0.5) or (left and x4 <= 1.0):
            return 1, numpy.ones(1, dtype=config.NP_FLOAT)

        if left:
            ts = numpy.arange(1.0, x4)
        else:
            ts = numpy.arange(2.0 * x4 - math.ceil(x4), 0.0, -1.0)[::-1]
        totals = numpy.empty(len(ts) + 2, dtype=config.NP_FLOAT)
        totals[1:-1] = (ts / x4) ** beta
        totals[0], totals[-1] = 0.0, 1.0
        deltas = numpy.diff(totals)
        if not left:
            deltas = deltas[::-1]
        return len(deltas), deltas / numpy.sum(deltas)

    def compress_repr(self) -> str | None:
        """Return `?` if the ordinates are not ready yet, `[]` if there are none, and
        |None| otherwise.

        The number of the ordinates defines the shape of |UH|.  Hence, combining
        identical ordinates into a single value (like |Parameter.compress_repr| does)
        would lose information:

        >>> from hydpy.models.rconc import *
        >>> parameterstep()
        >>> uh.compress_repr()
        '?'
        >>> uh(0.5, 0.5)
        >>> uh.compress_repr()
        """
        if (result := super().compress_repr()) in ("?", "[]"):
            return result
        return None

    def __repr__(self) -> str:
        if self._keywordarguments.valid:
            strings = []
            for name, value in self._keywordarguments:
                if name in ("tb", "tp", "x4"):
                    value *= self.get_timefactor()
                if name == "option":
                    strings.append(f'"{objecttools.repr_(value)}"')
                else:
                    strings.append(f"{name}={objecttools.repr_(value)}")
            return f"{self.name}({', '.join(strings)})"
        return super().__repr__()


class RetentionTime(parametertools.Parameter):
    """Retention time of the linear storage cascade [T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)


class NmbStorages(parametertools.NmbParameter):
    """Number of storages of the linear storage cascade [-]."""

    SPAN = (0, None)


class NmbSteps(parametertools.Parameter):
    """Number of internal computation steps per simulation time step [-].

    The default value of 1440 internal computation steps per day corresponds to 1
    computation step per minute.

    >>> from hydpy.models.rconc import *
    >>> parameterstep("1d")
    >>> simulationstep("12h")
    >>> nmbsteps(4.2)
    >>> nmbsteps
    nmbsteps(4.0)
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    TIME = True
    SPAN = (1, None)
    INIT = 1440.0
