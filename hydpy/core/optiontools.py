# -*- coding: utf-8 -*-
"""This module implements classes that help to manage global HydPy options."""

# import...
# ...from standard library
import inspect
import itertools
# ...from HydPy
from hydpy.core import autodoctools


class _Context(object):

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
        context = self.TYPE2CONTEXT[self.type_](option=self)
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
    """True/False flag for raising an error when trying to load an input
    time series not spanning the whole initialisation period."""

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

    fastcython = _Option(True, None)
    """A True/False flag which indicates whether cythonizing should result
    in faster but more fragile models or slower but more robust models.
    Setting this flag to False can be helpful when the implementation of
    new models or other Cython related features introduces errors that do
    not result in informative error messages."""

    printprogress = _Option(True, None)
    """A True/False flag for printing information about the progress of
    some processes to the standard output."""

    printincolor = _Option(True, None)
    """A True/False flag for printing progress information in colour
    eventually."""

    reprcomments = _Option(False, None)
    """A True/False flag for including comments into string representations.
    So far, this option affects the behaviour of a few implemented classes,
    only."""

    reprdigits = _Option(-999, -999)
    """Required precision of string representations of floating point
    numbers, defined as the minimum number of digits to be reproduced
    by the string representation (see function |repr_|)."""

    skipdoctests = _Option(False, None)
    """A True/False flag for skipping the automatic execution of
    documentation tests. """

    usecython = _Option(True, None)
    """TA True/False flag for applying cythonized models if possible,
    which are much faster than pure Python models. """

    usedefaultvalues = _Option(False, None)
    """A True/False flag for initialising parameters with standard values."""

    utcoffset = _Option(60, None)
    """Offset of your local time from UTC in minutes.  Defaults to 60,
    which corresponds to UTC+01:00."""

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
