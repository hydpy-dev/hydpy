# -*- coding: utf-8 -*-
"""This module implements classes that help to manage global HydPy options."""

# import...
# ...from standard library
import inspect
import itertools
from typing import *

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import timetools


TIn = TypeVar("TIn")
TOut = TypeVar("TOut")
TOrig = TypeVar("TOrig")
TOption = TypeVar("TOption", bound="_Option")


class _Context(Generic[TOrig, TOption]):

    _TYPE: Type
    _option: TOption
    _default: TOrig
    _old_value: TOrig

    def __new__(
        cls,
        *args,
        option: TOption,
        **kwargs,
    ):
        args_ = [cls, option._get_value()] + list(args)
        return cls._TYPE.__new__(*args_, **kwargs)

    def __init__(
        self,
        option: TOption,
    ):
        self._option = option
        self._old_value = option._value

    def __enter__(self):
        return self

    def __call__(
        self,
        value,
        optional=False,
    ):
        option = self._option
        if (value is not None) and ((option._get_value() is None) or not optional):
            option._value = option.ORIGTYPE(value)
        return self

    def __exit__(self, type_, value, traceback):
        self._option._value = self._old_value


class _IntContext(
    _Context[
        int,
        "_IntOption",
    ],
    int,
):

    _TYPE = int


class _PeriodContext(
    _Context[
        timetools.Period,
        "_PeriodOption",
    ],
    timetools.Period,
):

    _TYPE = timetools.Period


class _Option(Generic[TIn, TOut, TOrig]):

    ORIGTYPE: ClassVar[Type[TOrig]]
    CONTEXTTYPE: ClassVar[Type[TOut]]
    _default: TOrig
    _value: TOrig

    def __init__(self, default: TOrig):
        self._default = default
        self._value = default

    def __get__(self: TOption, options: "Options", type_=None) -> TOut:
        context = self.CONTEXTTYPE(option=self)
        context.__doc__ = self.__doc__
        context._default = self._default
        return context

    def __set__(self: TOption, options: "Options", value: TIn) -> None:
        self._value = self.ORIGTYPE(value)

    def __delete__(self, options: "Options") -> None:
        self._value = self._default

    def _get_value(self) -> TOrig:
        return self._value


class _IntOption(
    _Option[
        int,
        _IntContext,
        int,
    ],
):
    ORIGTYPE = int
    CONTEXTTYPE = _IntContext


class _BoolOption(
    _Option[
        bool,
        _IntContext,
        bool,
    ],
):

    ORIGTYPE = bool
    CONTEXTTYPE = _IntContext


class _PeriodOption(
    _Option[
        timetools.PeriodConstrArg,
        _PeriodContext,
        timetools.Period,
    ],
):

    ORIGTYPE = timetools.Period
    CONTEXTTYPE = _PeriodContext


class _Simulationstep(_PeriodOption):
    def _get_value(self):
        try:
            return hydpy.pub.timegrids.stepsize
        except RuntimeError:
            return super()._get_value()


class Options:
    """Singleton class for `global` options placed in module |pub|.

    Note that Most options are simple True/False or 0/1 flags.

    You can change all options in two ways.  By using the `with` statement,
    you make sure that the change is undone after leaving the corresponding
    code block (even if an error occurs):

    >>> from hydpy import pub
    >>> pub.options.printprogress = 0
    >>> pub.options.printprogress
    0
    >>> with pub.options.printprogress(True):
    ...     print(pub.options.printprogress)
    1
    >>> pub.options.printprogress
    0

    Alternatively, you can change all options via simple assignments:

    >>> pub.options.printprogress = True
    >>> pub.options.printprogress
    1

    But then you might have to keep in mind to undo the change later:

    >>> pub.options.printprogress
    1
    >>> pub.options.printprogress = False
    >>> pub.options.printprogress
    0

    When using the `with` statement, you can assign |None|, which does not
    change the original setting and resets it after leaving the `with` block:

    >>> with pub.options.printprogress(None):
    ...     print(pub.options.printprogress)
    ...     pub.options.printprogress = True
    ...     print(pub.options.printprogress)
    0
    1
    >>> pub.options.printprogress
    0

    The delete attribute restores the respective default setting:

    >>> del pub.options.printprogress
    >>> pub.options.printprogress
    1
    """

    autocompile = _BoolOption(True)
    """A True/False flag for enabling/disabling the automatic conversion of 
    pure Python models to computationally more efficient Cython models 
    whenever a existing Cython model may be outdated."""

    checkseries = _BoolOption(True)
    """True/False flag for raising an error when trying to load an input
    time series not spanning the whole initialisation period or containing
    |numpy.nan| values."""

    dirverbose = _BoolOption(False)
    """A True/False flag for letting the autocompletion textbox include
    all members of an object or only the most relevant ones.  So far, this
    option affects the behaviour of a few implemented classes only."""

    ellipsis = _IntOption(-999)
    """Ellipsis points are used to shorten the string representations of
    iterable HydPy objects containing many entries.  Set a value to define
    the maximum number of entries before and behind ellipsis points.  Set
    it to zero to avoid any ellipsis points.  Set it to -999 to rely on
    the default values of the respective iterable objects."""

    flattennetcdf = _BoolOption(False)
    """A True/False flag relevant when working with NetCDF files that 
    decides whether to handle multidimensional time series as a larger 
    number of 1-dimensional time series (True) or to keep the original 
    shape (False) (see the documentation on module |netcdftools| for 
    further information)."""

    forcecompiling = _BoolOption(False)
    """A True/False flag for enabling that each cythonizable model is
    cythonized when imported."""

    isolatenetcdf = _BoolOption(False)
    """A True/False flag relevant when working with NetCDF files that 
    decides whether to handle only the time series of a single sequence 
    type (True) or the time series of multiple sequence types (False)
    in individual NetCDF files (see the documentation on module 
    |netcdftools| for further information)."""

    parameterstep = _PeriodOption(timetools.Period("1d"))
    """The actual parameter time step size.  Change it by passing a |Period| 
    object or any valid |Period| constructor argument.  The default parameter 
    step is one day.
    
    >>> from hydpy import pub
    >>> pub.options.parameterstep
    Period("1d")
    """

    printprogress = _BoolOption(True)
    """A True/False flag for printing information about the progress of
    some processes to the standard output."""

    printincolor = _BoolOption(True)
    """A True/False flag for printing progress information in colour
    eventually."""

    reprcomments = _BoolOption(False)
    """A True/False flag for including comments into string representations.
    So far, this option affects the behaviour of a few implemented classes,
    only."""

    reprdigits = _IntOption(-1)
    """Required precision of string representations of floating point
    numbers, defined as the minimum number of digits to be reproduced
    by the string representation (see function |repr_|)."""

    simulationstep = _Simulationstep(timetools.Period())
    """The actual simulation time step size.  Change it by passing a |Period| 
    object or any valid |Period| constructor argument.  *HydPy* does not 
    define a default simulation step (indicated by an empty |Period| object).  
    
    Note that you cannot manually define the |Options.simulationstep| whenever 
    it is already available via attribute |Timegrids.stepsize| of the global  
    |Timegrids| object in module |pub| (`pub.timegrids`):
    
    >>> from hydpy import pub
    >>> pub.options.simulationstep
    Period()
    
    >>> pub.options.simulationstep = "1h"
    >>> pub.options.simulationstep
    Period("1h")
    
    >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
    >>> pub.options.simulationstep
    Period("1d")
 
    >>> pub.options.simulationstep = "1s"
    >>> pub.options.simulationstep
    Period("1d")
    
    >>> del pub.timegrids
    >>> pub.options.simulationstep
    Period("1s")
    
    >>> del pub.options.simulationstep
    >>> pub.options.simulationstep
    Period()
    """

    skipdoctests = _BoolOption(False)
    """A True/False flag for skipping the automatic execution of
    documentation tests."""

    timeaxisnetcdf = _IntOption(1)
    """An integer value relevant when working with NetCDF files that 
    determines the axis of the time variable (see the documentation on 
    module |netcdftools| for further information)."""

    trimvariables = _BoolOption(True)
    """A True/False flag for enabling/disabling function |trim|.  Set it
    to |False| only for good reasons."""

    usecython = _BoolOption(True)
    """TA True/False flag for applying cythonized models if possible,
    which are much faster than pure Python models. """

    usedefaultvalues = _BoolOption(False)
    """A True/False flag for initialising parameters with standard values."""

    utclongitude = _IntOption(15)
    """Longitude of the centre of the local time zone (see option
    |Options.utcoffset|).  Defaults to 15,  which corresponds to the 
    central meridian of UTC+01:00."""

    utcoffset = _IntOption(60)
    """Offset of your local time from UTC in minutes (see option 
    |Options.utclongitude|.  Defaults to 60, which corresponds to 
    UTC+01:00."""

    warnmissingcontrolfile = _BoolOption(False)
    """A True/False flag for only raising a warning instead of an exception
    when a necessary control file is missing."""

    warnmissingobsfile = _BoolOption(True)
    """A True/False flag for raising a warning when a requested observation
    sequence demanded by a node instance is missing."""

    warnmissingsimfile = _BoolOption(True)
    """A True/False flag for raising a warning when a requested simulation
    sequence demanded by a node instance is missing."""

    warnsimulationstep = _BoolOption(True)
    """A True/False flag for raising a warning when function |simulationstep|
    called for the first time directly by the user."""

    warntrim = _BoolOption(True)
    """A True/False flag for raising a warning when a |Variable| object
    trims its value(s) in order no not violate certain boundaries.
    To cope with the limited precision of floating-point numbers only
    those violations beyond a small tolerance value are reported
    (see function |trim|). """

    def __repr__(self):
        type_ = type(self)
        lines = ["Options("]
        for option in itertools.chain(vars(type_).keys(), vars(self).keys()):
            if not option.startswith("_"):
                value = getattr(self, option)
                lines.append(f"    {option} -> {repr(value)}")
        lines.append(")")
        return "\n".join(lines)


def _prepare_docstrings():
    """Assign docstrings to the corresponding attributes of class `Options`
    to make them available in the interactive mode of Python."""
    if config.USEAUTODOC:
        __test__ = {}
        source = inspect.getsource(Options)
        docstrings = source.split('"""')[3::2]
        attributes = [
            line.strip().split()[0]
            for line in source.split("\n")
            if (
                ("_IntOption(" in line)
                or ("_BoolOption(" in line)
                or ("_PeriodOption(" in line)
            )
        ]
        for attribute, docstring in zip(attributes, docstrings):
            Options.__dict__[attribute].__doc__ = docstring
            __test__[attribute] = docstring
        globals()["__test__"] = __test__


_prepare_docstrings()
