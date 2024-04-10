# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
from __future__ import annotations
from typing_extensions import Unpack

# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class TD(TypedDict, total=False):
    """A TypedDict that holds the allowed keyword arguments of the call function
    of class UH"""

    tb: float
    tp: Optional[float]
    x4: float
    auxfile: str


class UH(parametertools.Parameter):
    """The ordinates of the unit hydrograph can be set directly by calling uh with a
    list of float values as one positional argument:

    >>> from hydpy.models.rconc import *
    >>> simulationstep("12h")
    >>> parameterstep("1d")
    >>> uh([0.1,0.2,0.4,0.2,0.1])
    >>> uh
    uh(0.1, 0.2, 0.4, 0.2, 0.1)

    Alternatively, implemented geometries can be specified via a positional 'option'
    parameter and parameterized with the corresponding arguments.
    We generate the ordinates of a unit hydrograph in the form of an isosceles triangle
    with a base length of 10:

    >>> from hydpy import print_values
    >>> from hydpy.models.rconc import *
    >>> simulationstep("1d")
    >>> parameterstep("1d")
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
    ValueError: Positional argument expected in parameter `uh` of element `?`.

    Also, calling uh with more than one positional argument or with positional argument
    of wrong type is not allowed:

    >>> uh([0.1,0.2,0.1], "triangle", tb=10.0)
    Traceback (most recent call last):
    ...
    ValueError: Only one positional argument allowed for parameter `uh` of element `?`.

    >>> uh(True)
    Traceback (most recent call last):
    ...
    TypeError: Wrong type of positional argument in `uh` of element `?`.

    The optional parameter 'tp' specifies the position of the peak:

    >>> uh("triangle", tb=10.0, tp=7.0)
    >>> uh
    uh("triangle", tb=10.0, tp=7.0)
    >>> print_values(uh.values)
    0.014286, 0.042857, 0.071429, 0.1, 0.128571, 0.157143, 0.185714,
    0.166667, 0.1, 0.033333

    Both parameters can also be fractional:

    >>> uh("triangle", tb=9.5, tp=6.7)
    >>> uh
    uh("triangle", tb=9.5, tp=6.7)
    >>> print_values(uh.values)
    0.015711, 0.047133, 0.078555, 0.109976, 0.141398, 0.17282, 0.199445,
    0.150376, 0.075188, 0.009398

    Parameter tp must not be greater than tb:

    >>> uh("triangle", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: Parameter 'tp' must not be greater than 'tb'

    In addition to the triangular unit hydrograph, the UHs used in the GR model are also
    implemented:

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



    The triangle unit hydrograph must not be called with the parameters for the
    GR unit hydrograph:

    >>> uh("triangle", x4=2.0)
    Traceback (most recent call last):
    ...
    ValueError: Wrong arguments for option 'triangle'

    The GR unit hydrographs  must not be called with the parameters for the
    triangle unit hydrograph:
    >>> uh("gr_uh1", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: Wrong arguments for option 'gr_uh1'
    >>> uh("gr_uh2", tb=2.0, tp=3.0)
    Traceback (most recent call last):
    ...
    ValueError: Wrong arguments for option 'gr_uh2'
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling: bool = False

    KEYWORDS = {
        "tb": parametertools.Keyword(name="tb", time=False),
        "tp": parametertools.Keyword(name="tp", time=False),
        "x4": parametertools.Keyword(name="x4", time=False),
    }

    @overload
    def __call__(self, value: VectorInputFloat, /) -> None: ...

    @overload
    def __call__(self, option: Literal["triangle"], /, *, tb: float) -> None: ...

    @overload
    def __call__(
        self, option: Literal["triangle"], /, *, tb: float, tp: float
    ) -> None: ...

    @overload
    def __call__(
        self, option: Literal["gr_uh1", "gr_uh2"], /, *, x4: float
    ) -> None: ...

    @overload
    def __call__(self, /, *, auxfile: str) -> None: ...

    def __call__(
        self, *args: Union[VectorInputFloat, str], **kwargs: Unpack[TD]
    ) -> None:
        self._keywordarguments = parametertools.KeywordArguments(False)

        # TODO: testing for parameter auxfile here would lead to necessity of
        # TODO: complex doctests, otherwise we would have to change the super class
        # TODO: For now, we skip support of auxfile and need to find a general solution.
        # auxfile = kwargs.get("auxfile")
        # if auxfile is not None:
        #    super().__call__(*args, **kwargs)
        #    return None

        if len(args) < 1:
            raise ValueError(
                f"Positional argument expected in parameter "
                f"{objecttools.elementphrase(self)}."
            )
        if len(args) > 1:
            raise ValueError(
                f"Only one positional argument allowed for parameter "
                f"{objecttools.elementphrase(self)}."
            )

        if isinstance(args[0], str):
            option = args[0]
            args = ()
        else:
            try:
                self.shape = len(args[0])
            except TypeError:
                raise TypeError(
                    f"Wrong type of positional argument in "
                    f"{objecttools.elementphrase(self)}."
                ) from None
            self.values = args[0]
            return None

        idx = self._find_kwargscombination(
            args, dict(kwargs), (set(("tb",)), set(("tb", "tp")), set(("x4",)))
        )

        if option == "triangle":
            if idx in [0, 1]:
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
                self.set_triangle_uh(tb=tb, tp=tp)
            else:
                raise ValueError("Wrong arguments for option 'triangle'")
        elif option == "gr_uh1":
            if idx == 2:
                x4 = kwargs["x4"]
                x4 /= self.get_timefactor()
                self._keywordarguments = parametertools.KeywordArguments(
                    option=option, x4=x4
                )
                self.set_gr_uh1_uh(x4=x4)
            else:
                raise ValueError("Wrong arguments for option 'gr_uh1'")
        elif option == "gr_uh2":
            if idx == 2:
                x4 = kwargs["x4"]
                x4 /= self.get_timefactor()
                self._keywordarguments = parametertools.KeywordArguments(
                    option=option, x4=x4
                )
                self.set_gr_uh2_uh(x4=x4)
            else:
                raise ValueError("Wrong arguments for option 'gr_uh2'")
        return None

    def __repr__(self) -> str:
        if self._keywordarguments.valid:
            strings = []
            for name, value in self._keywordarguments:
                if name in ["tb", "tp", "x4"]:
                    value *= self.get_timefactor()
                if name == "option":
                    strings.append(f'"{objecttools.repr_(value)}"')
                else:
                    strings.append(f"{name}={objecttools.repr_(value)}")
            return f"{self.name}({', '.join(strings)})"
        return super().__repr__()

    def set_triangle_uh(self, tb: float, tp: Optional[float] = None) -> None:
        """Calculate and set the ordinates of a triangle unit hydrograph"""

        quh = self.subpars.pars.model.sequences.logs.quh
        # Determine UH parameters...
        if tb <= 1.0:
            # ...when Tb smaller than or equal to the simulation time step.
            self.shape = 1
            self.values = 1.0
            quh.shape = 1
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
                    raise ValueError("Parameter 'tp' must not be greater than 'tb'")
                peak = tp
            peak_f = int(numpy.floor(peak))
            peak_c = int(numpy.ceil(peak))
            # Calculate the triangle ordinate(s)...
            self.shape = full_c
            uh = self.values.copy()
            quh.shape = full_c
            slope1 = 1 / peak
            slope2 = -1 / (full - peak)
            # ...of the rising
            # limb.
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

    def set_gr_uh1_uh(self, x4: float) -> None:
        """Calculate and set the ordinates of a unit hydrograph as used in GR model
        (UH1)
        """

        quh = self.subpars.pars.model.sequences.logs.quh
        if x4 <= 1.0:
            # ...when x4 smaller than or equal to the simulation time step.
            self.shape = 1
            quh.shape = 1
            self.values = 1.0
        else:
            index = numpy.arange(1, numpy.ceil(x4) + 1)
            sh1j = (index / x4) ** 2.5
            sh1j_1 = ((index - 1) / x4) ** 2.5
            sh1j[index >= x4] = 1
            sh1j_1[index - 1 >= x4] = 1
            self.shape = len(sh1j)
            uh1 = self.values
            quh.shape = len(uh1)
            uh1[:] = sh1j - sh1j_1

            # sum should be equal to one but better normalize
            uh1[:] = uh1 / numpy.sum(uh1)

    def set_gr_uh2_uh(self, x4: float) -> None:
        """Calculate and set the ordinates of a unit hydrograph as used in GR model
        (UH2)
        """
        # TODO: refactor
        quh = self.subpars.pars.model.sequences.logs.quh
        if x4 <= 1.0:
            index = numpy.arange(1, 3)
        else:
            index = numpy.arange(1, numpy.ceil(x4 * 2) + 1)

        nmb_uhs = len(index)
        sh2j = numpy.zeros(shape=nmb_uhs)
        sh2j_1 = numpy.zeros(shape=nmb_uhs)

        for idx in range(nmb_uhs):
            if index[idx] <= x4:
                sh2j[idx] = 0.5 * (index[idx] / x4) ** 2.5
            elif x4 < index[idx] < 2.0 * x4:
                sh2j[idx] = 1.0 - 0.5 * (2.0 - index[idx] / x4) ** 2.5
            else:
                sh2j[idx] = 1

            if index[idx] - 1 <= x4:
                sh2j_1[idx] = 0.5 * ((index[idx] - 1) / x4) ** 2.5
            elif x4 < index[idx] - 1 < 2.0 * x4:
                sh2j_1[idx] = 1.0 - 0.5 * (2.0 - (index[idx] - 1) / x4) ** 2.5
            else:
                # sh2j_1[idx] = 1
                assert False, "Please check gr_uh2 algorithm, line has been removed"

        self.shape = len(index)
        quh.shape = len(index)
        uh2 = self.values
        uh2[:] = sh2j - sh2j_1
        uh2[:] = uh2 / numpy.sum(uh2)


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


class RecStep(parametertools.Parameter):
    """Number of internal computation steps per simulation time step [-].

    The default value of 1440 internal computation steps per day corresponds to 1
    computation step per minute.

    >>> from hydpy.models.rconc import *
    >>> parameterstep("1d")
    >>> simulationstep("12h")
    >>> recstep(4.2)
    >>> recstep
    recstep(4.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, True, (1, None)
    INIT = 1440
