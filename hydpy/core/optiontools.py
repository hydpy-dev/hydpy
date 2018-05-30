# -*- coding: utf-8 -*-
"""This module implements classes that help to manage global HydPy options."""

# import...
# ...from the Python standard library
from __future__ import division, print_function
import inspect
# ...from HydPy
from hydpy.core import autodoctools


class _Context(object):

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

    def __new__(cls, option):
        return int.__new__(cls, option.value)


class _FloatContext(_Context, float):

    def __new__(cls, option):
        return float.__new__(cls, option.value)


class _StrContext(_Context, str):

    def __new__(cls, option):
        return str.__new__(cls, option.value)


class _Option(object):

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
        context = self.TYPE2CONTEXT[self.type_](self)
        context.__doc__ = self.__doc__
        context.default = self.default
        context.nothing = self.nothing
        return context

    def __set__(self, options, value):
        self.value = self.type_(value)

    def __delete__(self, options):
        self.value = self.default


class Options(object):
    """Singleton class for `global` options placed in module |pub|.

    Note that Most options are simple True/False or 0/1 flags.

    You can change all options in two ways.  By using the `with` statement,
    you make sure that the change is undone after leaving the corresponding
    code block (even if an error occurs):

    >>> from hydpy.pub import options
    >>> options.printprogress = 0
    >>> options.printprogress
    0
    >>> with options.printprogress(True):
    ...     print(options.printprogress)
    1
    >>> options.printprogress
    0

    Alternatively, you can change all options via simple assignements:

    >>> options.printprogress = True
    >>> options.printprogress
    1

    But then you might have to keep in mind to undo the change later:

    >>> options.printprogress
    1
    >>> options.printprogress = False
    >>> options.printprogress
    0
    """

    checkseries = _Option(True, None)
    """True/False flag indicating whether an error shall be raised
    when e.g. an incomplete input time series, not spanning the whole
    initialization time period, is loaded."""

    ellipsis = _Option(-999, -999)
    """Ellipsis points are used to shorten the string representations
    of iterable HydPy objects containing many entries.  Set a value
    to define the maximum number of entries before and behind ellipsis
    points.  Set it to zero, if no ellipsis points should be drawn at
    all.  Set it to -999 (the default value) to rely on the default
    values of the respective iterables."""
    ellipsis.type_ = int

    fastcython = _Option(True, None)
    """True/False flag indicating whether Cythonization shall be
    configured in a fast but unsafe (True) or in a slow but safe (False)
    mode.  The fast mode is the default.  Setting this flag to False
    can be helpful when the implementation of new models or other
    Cython related features introduces errors that do not result in
    informative error messages."""

    printprogress = _Option(True, None)
    """True/False flag indicating whether information about the progress
    of certain processes shall be printed to the standard output or not.
    The default is `True`."""

    printincolor = _Option(True, None)
    """True/False flag indicating whether information shall be printed
    in color eventually or not. The default is `True`."""

    reprcomments = _Option(False, None)
    """True/False flag indicationg whether comments shall be included
    in string representations of some classes of the HydPy framework or
    not.  The default is `False`."""

    reprdigits = _Option(-999, -999)
    """Required precision of string representations of floating point
    numbers, defined as the minimum number of digits to be reproduced
    by the string representation (see function |repr_|)."""

    skipdoctests = _Option(False, None)
    """True/False flag indicating whether documetation tests shall be
    performed under certain situations.  Applying tests increases
    reliabilty and is thus the default."""

    usecython = _Option(True, None)
    """True/False flag indicating whether Cython models (True) or pure
    Python models (False) shall be applied if possible.  Using Cython
    models is more time efficient and thus the default."""

    usedefaultvalues = _Option(False, None)
    """True/False flag indicating whether parameters values shall be
    initialized with standard values or not."""

    dirverbose = _Option(False, None)
    """True/False flag indicationg whether the listboxes for the member
    selection of the classes of the HydPy framework should be complete
    (True) or restrictive (False).  The latter is more viewable and hence
    the default."""

    warnmissingcontrolfile = _Option(False, None)
    """True/False flag indicating whether only a warning shall be raised
    when a required control file is missing, or an exception."""

    warnmissingobsfile = _Option(True, None)
    """True/False flag indicating whether a warning shall be raised
    when a requested observation sequence demanded by a node instance
    is missing."""

    warnmissingsimfile = _Option(True, None)
    """True/False flag indicating whether a warning shall be raised
    when a requested simulation sequence demanded by a node instance
    is missing."""

    warnsimulationstep = _Option(True, None)
    """True/False flag indicating whether a warning shall be raised
    when function |simulationstep| called for the first time."""

    warntrim = _Option(True, None)
    """True/False flag indicating whether a warning shall be raised
    whenever certain values needed to be trimmed due to violating
    certain boundaries. Such warnings increase safety and are thus
    the default is `True`.  However, to cope with the limited precision
    of floating point numbers only those violations beyond a small
    tolerance value are reported (see function |trim|).  Warnings
    with identical information are reported only once."""


@autodoctools.make_autodoc_optional
def _prepare_docstrings():
    """Assign docstrings to the corresponding attributes of class `Options`
     to make them available in the interactive mode of Python."""
    source = inspect.getsource(Options)
    docstrings = source.split('"""')[3::2]
    attributes = [line.strip().split()[0] for line in source.split('\n')
                  if '_Option(' in line]
    for attribute, docstring in zip(attributes, docstrings):
        Options.__dict__[attribute].__doc__ = docstring


_prepare_docstrings()

autodoctools.autodoc_module()
