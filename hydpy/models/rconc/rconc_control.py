# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
from __future__ import annotations

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class _AllowedKeywordArgsOfClassUH(TypedDict, total=False):
    """A |TypedDict| that holds the allowed keyword arguments of the `__call__` method
    of class |UH|."""

    tb: float
    tp: Optional[float]
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
    >>> uh
    uh(0.1, 0.2, 0.4, 0.2, 0.1)

    Alternatively, implemented geometries can be specified via a positional 'option'
    parameter and parameterised with the corresponding arguments.

    We generate the ordinates of a unit hydrograph in the form of an isosceles triangle
    with a base length of 10 days:

    >>> from hydpy import print_values
    >>> from hydpy.models.rconc import *
    >>> uh("triangle", tb=10.0)
    >>> uh
    uh("triangle", tb=10.0)
    >>> print_values(uh.values)
    0.02, 0.06, 0.1, 0.14, 0.18, 0.18, 0.14, 0.1, 0.06, 0.02

    The value of `tb` depends on the current parameter step size:

    >>> from hydpy import pub
    >>> with pub.options.parameterstep("2d"):
    ...     uh
    uh("triangle", tb=5.0)

    Omitting the option string will result in an error:

    >>> uh(tb=10.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Exactly one positional argument is expected, but none or \
more than one is given.

    Also, calling uh with more than one positional argument or with a positional
    argument of the wrong type is not allowed:

    >>> uh([0.1,0.2,0.1], "triangle", tb=10.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Exactly one positional argument is expected, but none or \
more than one is given.

    >>> uh(True)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: The expected type of the positional argument is a sequence \
of floats but a value of `bool` is given.

    The optional argument 'tp' specifies the position of the peak:

    >>> uh("triangle", tb=10.0, tp=7.0)
    >>> uh
    uh("triangle", tb=10.0, tp=7.0)
    >>> print_values(uh.values)
    0.014286, 0.042857, 0.071429, 0.1, 0.128571, 0.157143, 0.185714,
    0.166667, 0.1, 0.033333

    Any positive real numbers are allowed:

    >>> uh("triangle", tb=9.5, tp=6.7)
    >>> uh
    uh("triangle", tb=9.5, tp=6.7)
    >>> print_values(uh.values)
    0.015711, 0.047133, 0.078555, 0.109976, 0.141398, 0.17282, 0.199445,
    0.150376, 0.075188, 0.009398

    Parameter 'tp' must not be greater than 'tb':

    >>> uh("triangle", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Parameter 'tp' must not be greater than 'tb'.

    In addition to the HBV96-oriented triangular unit hydrograph (with the general
    purpose of damping the flood pulse; see :cite:t:`ref-Harlin1992`), the unit
    hydrographs used in the GR4J model (which reflect the outflow of the two
    conceptional storages used in this approach; see :cite:t:`ref-Perrin2007`) are also
    available:

    >>> uh("gr_uh1", x4=6.3)
    >>> uh
    uh("gr_uh1", x4=6.3)
    >>> print_values(uh.values)
    0.010038, 0.046746, 0.099694, 0.16474, 0.239926, 0.324027, 0.11483

    >>> uh("gr_uh1", x4=0.8)
    >>> print_values(uh.values)
    1.0

    >>> uh("gr_uh2", x4=2.8)
    >>> uh
    uh("gr_uh2", x4=2.8)
    >>> print_values(uh.values)
    0.038113, 0.177487, 0.368959, 0.292023, 0.112789, 0.010628

    >>> uh("gr_uh2", x4=0.8)
    >>> print_values(uh.values)
    0.75643, 0.24357

    According to :cite:t:`ref-Perrin2007`, the exponent 'beta' is 2.5 by default but
    can be changed:

    >>> uh("gr_uh1", x4=6.3, beta=1.5)
    >>> print_values(uh.values)
    0.06324, 0.115629, 0.149734, 0.177314, 0.201123, 0.222388, 0.070571

    >>> uh("gr_uh2", x4=2.8, beta=1.5)
    >>> print_values(uh.values)
    0.106717, 0.195124, 0.250762, 0.231417, 0.166382, 0.049598

    The triangle unit hydrograph must not be called with the parameters for the
    GR4J-like unit hydrograph:

    >>> uh("triangle", x4=2.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Wrong arguments for option 'triangle'.

    The GR4J-based options cannot be mixed with the triangle parameters:

    >>> uh("gr_uh1", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Wrong arguments for option 'gr_uh1'.

    >>> uh("gr_uh2", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `uh` of element `?`, the \
following error occurred: Wrong arguments for option 'gr_uh2'.

    The following tests examine the correct calculation of ordinates in edge cases:

    >>> uh("gr_uh2", x4=0.4)
    >>> print_values(uh.values)
    1.0

    >>> uh("gr_uh2", x4=0.0)
    >>> print_values(uh.values)
    1.0

    >>> uh("gr_uh2", x4=1.0)
    >>> print_values(uh.values)
    0.5, 0.5

    >>> uh("gr_uh2", x4=1.5)
    >>> print_values(uh.values)
    0.181444, 0.637113, 0.181444
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
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
    def __call__(
        self, option: Literal["triangle"], /, *, tb: float, tp: Optional[float] = None
    ) -> None: ...

    @overload
    def __call__(
        self, option: Literal["gr_uh1", "gr_uh2"], /, *, x4: float, beta: float = 2.5
    ) -> None: ...

    def __call__(
        self,
        *args: Union[VectorInputFloat, str],
        **kwargs: Unpack[_AllowedKeywordArgsOfClassUH],
    ) -> None:
        self._keywordarguments = parametertools.KeywordArguments(False)

        # TODO: testing for parameter auxfile here would lead to necessity of
        # TODO: complex doctests, otherwise we would have to change the super class
        # TODO: For now, we skip support of auxfile and need to find a general solution.
        # auxfile = kwargs.get("auxfile")
        # if auxfile is not None:
        #    super().__call__(*args, **kwargs)
        #    return None
        try:
            self._validate_args(args)
            if isinstance(args[0], str):
                option = args[0]
                args = ()
            else:
                try:
                    self.shape = len(args[0])
                except TypeError:
                    raise TypeError(
                        f"The expected type of the positional argument is a "
                        f"sequence of floats but a value of `{type(args[0]).__name__}`"
                        f" is given."
                    ) from None
                self.values = args[0]
                return None

            idx = self._find_kwargscombination(
                args,
                dict(kwargs),
                (set(("tb",)), set(("tb", "tp")), set(("x4",)), set(("x4", "beta"))),
            )

            if option == "triangle":
                if idx in (0, 1):
                    tb = kwargs["tb"]
                    tb /= self.get_timefactor()
                    if idx == 1:
                        tp = kwargs["tp"]
                        if tp is not None:
                            tp /= self.get_timefactor()
                        self._keywordarguments = parametertools.KeywordArguments(
                            option=option, tb=tb, tp=tp
                        )
                    else:
                        tp = None
                        self._keywordarguments = parametertools.KeywordArguments(
                            option=option, tb=tb
                        )
                    self._set_triangle_uh(tb=tb, tp=tp)
                else:
                    raise ValueError("Wrong arguments for option 'triangle'.")
            elif option == "gr_uh1":
                if idx in (2, 3):
                    x4 = kwargs["x4"]
                    x4 /= self.get_timefactor()
                    if idx == 3 and kwargs["beta"] is not None:
                        beta = kwargs["beta"]
                        self._keywordarguments = parametertools.KeywordArguments(
                            option=option, x4=x4, beta=beta
                        )
                    else:
                        beta = 2.5
                        self._keywordarguments = parametertools.KeywordArguments(
                            option=option, x4=x4
                        )
                    self.set_gr_uh1(x4=x4, beta=beta)
                else:
                    raise ValueError("Wrong arguments for option 'gr_uh1'.")
            elif option == "gr_uh2":
                if idx in (2, 3):
                    x4 = kwargs["x4"]
                    x4 /= self.get_timefactor()
                    if idx == 3 and kwargs["beta"] is not None:
                        beta = kwargs["beta"]
                        self._keywordarguments = parametertools.KeywordArguments(
                            option=option, x4=x4, beta=beta
                        )
                    else:
                        beta = 2.5
                        self._keywordarguments = parametertools.KeywordArguments(
                            option=option, x4=x4
                        )
                    self.set_gr_uh2(x4=x4, beta=beta)
                else:
                    raise ValueError("Wrong arguments for option 'gr_uh2'.")
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the values of parameter "
                f"{objecttools.elementphrase(self)}"
            )

        return None

    def _validate_args(self, args: tuple[Union[VectorInputFloat, str], ...]) -> None:
        if len(args) != 1:
            raise ValueError(
                "Exactly one positional argument is expected, but none or more "
                "than one is given."
            )

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

    def _set_triangle_uh(self, tb: float, tp: Optional[float] = None) -> None:
        """Calculate and set the ordinates of a triangle unit hydrograph."""

        quh = self.subpars.pars.model.sequences.logs.quh
        # Determine UH parameters...
        if tb <= 1.0:
            # ...when Tb smaller than or equal to the simulation time step.
            self.shape = quh.shape = 1
            self.values = 1.0
        else:
            full = tb
            # Now comes a terrible trick due to rounding problems coming from
            # the conversation of the SMHI parameter set to the HydPy
            # parameter set.  Time to get rid of it...
            if (full % 1.0) < 1e-4:
                full //= 1.0
            full_f = int(numpy.floor(full))
            full_c = int(numpy.ceil(full))
            if not tp:
                peak = full / 2.0
            else:
                if tp > tb:
                    raise ValueError("Parameter 'tp' must not be greater than 'tb'.")
                peak = tp
            peak_f = int(numpy.floor(peak))
            peak_c = int(numpy.ceil(peak))
            # Calculate the triangle ordinate(s)...
            self.shape = full_c
            uh = self.values.copy()
            quh.shape = full_c
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

    def set_gr_uh1(self, x4: float, beta: float = 2.5) -> None:
        """Calculate and set the ordinates of a unit hydrograph as done by GR4J for
        modifying base flow.
        """
        self.shape, self.values = self._det_gr_uh(x4=x4, beta=beta, left=True)
        self.subpars.pars.model.sequences.logs.quh.shape = self.shape

    def set_gr_uh2(self, x4: float, beta: float = 2.5) -> None:
        """Calculate and set the ordinates of a unit hydrograph as done by GR4J for
        modifying direct runoff."""
        shape_left, values_left = self._det_gr_uh(x4=x4, beta=beta, left=True)
        shape_right, values_right = self._det_gr_uh(x4=x4, beta=beta, left=False)
        self.shape = shape_left + shape_right - 1
        self.subpars.pars.model.sequences.logs.quh.shape = self.shape
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
            return 1, numpy.ones(1, dtype=float)

        if left:
            ts = numpy.arange(1.0, x4)
        else:
            ts = numpy.arange(2.0 * x4 - numpy.ceil(x4), 0.0, -1.0)[::-1]
        totals = numpy.empty(len(ts) + 2, dtype=float)
        totals[1:-1] = (ts / x4) ** beta
        totals[0], totals[-1] = 0.0, 1.0
        deltas = numpy.diff(totals)
        if not left:
            deltas = deltas[::-1]
        return len(deltas), deltas / numpy.sum(deltas)


class RetentionTime(parametertools.Parameter):
    """Retention time of the linear storage cascade [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class NmbStorages(parametertools.Parameter):
    """Number of storages of the linear storage cascade [-].

    Defining a value for parameter |NmbStorages| automatically sets the shape of state
    sequence |SC|:

    >>> from hydpy.models.rconc import *
    >>> parameterstep()
    >>> nmbstorages(5)
    >>> states.sc.shape
    (5,)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.sequences.states.sc.shape = self.value


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

    NDIM, TYPE, TIME, SPAN = 0, int, True, (1, None)
    INIT = 1440.0
