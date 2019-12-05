# -*- coding: utf-8 -*-
"""This module implements classes that help to manage global HydPy options."""

# import...
# ...from standard library
import inspect
import itertools
# ...from HydPy
from hydpy import config


class _Context:

    _TYPE = None

    def __new__(cls, *args, option, **kwargs):
        args = [cls, option.value] + list(args)
        return cls._TYPE.__new__(*args, **kwargs)

    def __init__(self, option):
        self.option = option
        self.old_value = option.value

    def __enter__(self):
        return self

    def __call__(self, value, optional=False):
        if (self.option.value == self.option.nothing) or not optional:
            self.option.value = self.option.type_(value)
        return self

    def __exit__(self, type_, value, traceback):
        self.option.value = self.old_value


class _IntContext(_Context, int):

    _TYPE = int


class _FloatContext(_Context, float):

    _TYPE = float


class _StrContext(_Context, str):

    _TYPE = str


class _Option:

    TYPE2CONTEXT = {int: _IntContext,
                    bool: _IntContext,
                    float: _FloatContext,
                    str: _StrContext}

    def __init__(self, default, nothing=None):
        self.default = default
        self.nothing = nothing
        self.value = default
        self.type_ = type(default)
        self.context = self.TYPE2CONTEXT

    def __get__(self, options, type_=None):
        context = self.TYPE2CONTEXT[self.type_](option=self)
        context.__doc__ = self.__doc__
        context.default = self.default
        context.nothing = self.nothing
        return context

    def __set__(self, options, value):
        self.value = self.type_(value)

    def __delete__(self, options):
        self.value = self.default


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

    Alternatively, you can change all options via simple assignements:

    >>> pub.options.printprogress = True
    >>> pub.options.printprogress
    1

    But then you might have to keep in mind to undo the change later:

    >>> pub.options.printprogress
    1
    >>> pub.options.printprogress = False
    >>> pub.options.printprogress
    0

    The delete attribute restores the respective default setting:

    >>> del pub.options.printprogress
    >>> pub.options.printprogress
    1
    """

    autocompile = _Option(False, None)
    """A True/False flag for enabling/disabling the automatic conversion of 
    pure Python models to computationally more efficient Cython models 
    whenever a existing Cython model may be outdated."""

    checkseries = _Option(True, None)
    """True/False flag for raising an error when trying to load an input
    time series not spanning the whole initialisation period or containing
    |numpy.nan| values."""
    
    dirverbose = _Option(False, None)
    """A True/False flag for letting the autocompletion textbox include
    all members of an object or only the most relevant ones.  So far, this
    option affects the behaviour of a few implemented classes only."""

    ellipsis = _Option(-999, -999)
    """Ellipsis points are used to shorten the string representations of
    iterable HydPy objects containing many entries.  Set a value to define
    the maximum number of entries before and behind ellipsis points.  Set
    it to zero to avoid any ellipsis points.  Set it to -999 to rely on
    the default values of the respective iterable objects."""
    ellipsis.type_ = int

    flattennetcdf = _Option(False, None)
    """A True/False flag relevant when working with NetCDF files that 
    decides whether to handle multidimensional time series as a larger 
    number of 1-dimensional time series (True) or to keep the original 
    shape (False) (see the documentation on module |netcdftools| for 
    further information)."""

    forcecompiling = _Option(False, None)
    """A True/False flag for enabling that each cythonizable model is
    cythonized when imported."""

    isolatenetcdf = _Option(False, None)
    """A True/False flag relevant when working with NetCDF files that 
    decides whether to handle only the time series of a single sequence 
    type (True) or the time series of multiple sequence types (False)
    in individual NetCDF files (see the documentation on module 
    |netcdftools| for further information)."""

    printprogress = _Option(False, None)
    """A True/False flag for printing information about the progress of
    some processes to the standard output."""

    printincolor = _Option(True, None)
    """A True/False flag for printing progress information in colour
    eventually."""

    reprcomments = _Option(False, None)
    """A True/False flag for including comments into string representations.
    So far, this option affects the behaviour of a few implemented classes,
    only."""

    reprdigits = _Option(6, -1)
    """Required precision of string representations of floating point
    numbers, defined as the minimum number of digits to be reproduced
    by the string representation (see function |repr_|)."""

    skipdoctests = _Option(False, None)
    """A True/False flag for skipping the automatic execution of
    documentation tests."""

    timeaxisnetcdf = _Option(1, 1)
    """An integer value relevant when working with NetCDF files that 
    determines the axis of the time variable (see the documentation on 
    module |netcdftools| for further information)."""

    trimvariables = _Option(True, None)
    """A True/False flag for enabling/disabling function |trim|.  Set it
    to |False| only for good reasons."""

    usecython = _Option(False, None)
    """TA True/False flag for applying cythonized models if possible,
    which are much faster than pure Python models. """

    usedefaultvalues = _Option(False, None)
    """A True/False flag for initialising parameters with standard values."""

    utclongitude = _Option(15, None)
    """Longitude of the centre of the local time zone (see option
    |Options.utcoffset|).  Defaults to 15,  which corresponds to the 
    central meridian of UTC+01:00."""

    utcoffset = _Option(60, None)
    """Offset of your local time from UTC in minutes (see option 
    |Options.utclongitude|.  Defaults to 60, which corresponds to 
    UTC+01:00."""

    warnmissingcontrolfile = _Option(False, None)
    """A True/False flag for only raising a warning instead of an exception
    when a necessary control file is missing."""

    warnmissingobsfile = _Option(True, None)
    """A True/False flag for raising a warning when a requested observation
    sequence demanded by a node instance is missing."""

    warnmissingsimfile = _Option(True, None)
    """A True/False flag for raising a warning when a requested simulation
    sequence demanded by a node instance is missing."""

    warnsimulationstep = _Option(True, None)
    """A True/False flag for raising a warning when function |simulationstep|
    called for the first time directly by the user."""

    warntrim = _Option(True, None)
    """A True/False flag for raising a warning when a |Variable| object
    trims its value(s) in order no not violate certain boundaries.
    To cope with the limited precision of floating point numbers only
    those violations beyond a small tolerance value are reported
    (see function |trim|). """

    def __repr__(self):
        type_ = type(self)
        lines = ['Options(']
        for option in itertools.chain(vars(type_).keys(), vars(self).keys()):
            if not option.startswith('_'):
                value = getattr(self, option)
                lines.append(f'    {option} -> {value}')
        lines.append(')')
        return '\n'.join(lines)


def _prepare_docstrings():
    """Assign docstrings to the corresponding attributes of class `Options`
     to make them available in the interactive mode of Python."""
    if config.USEAUTODOC:
        source = inspect.getsource(Options)
        docstrings = source.split('"""')[3::2]
        attributes = [line.strip().split()[0] for line in source.split('\n')
                      if '_Option(' in line]
        for attribute, docstring in zip(attributes, docstrings):
            Options.__dict__[attribute].__doc__ = docstring


_prepare_docstrings()
