# -*- coding: utf-8 -*-
"""This module implements some exception classes and related features."""

# import...
# ...from HydPy
from hydpy.core import autodoctools


class HydPyDeprecationWarning(DeprecationWarning):
    """Warning for deprecated HydPy features."""
    pass


class AttributeNotReady(AttributeError):
    """The attribute is principally defined, but must be prepared first."""


class OptionalModuleNotAvailable(ImportError):
    """A `HydPy` function requiring an optional module is called, but this
    module is not available."""


class OptionalImport(object):
    """Exectutes the given import commands sequentially and returns the
    first importable module.  If no module could be imported at all, it
    returns a dummy object which raises a |OptionalModuleNotAvailable|
    each time a one tries to access a member of the original module.

    If a module is availabe:

    >>> from hydpy.core.exceptiontools import OptionalImport
    >>> numpy = OptionalImport(
    ...     'numpy',
    ...     ['import numpie', 'import numpy', 'import os'])
    >>> numpy.nan
    nan

    If no module is not available:

    >>> numpie = OptionalImport('numpie', ['import numpie'])
    >>> numpie.nan
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.OptionalModuleNotAvailable: HydPy could not \
load module `numpie`.  This module is no general requirement but \
necessary for some specific functionalities.
    """
    def __new__(cls, name, commands):
        for command in commands:
            try:
                exec(command)
                return eval(command.split()[-1])
            except BaseException:
                pass
        return object.__new__(cls)

    def __init__(self, name, commands):
        self.name = name

    def __getattr__(self, name):
        raise OptionalModuleNotAvailable(
            'HydPy could not load module `%s`.  This module is no '
            'general requirement but necessary for some specific '
            'functionalities.'
            % self.name)


autodoctools.autodoc_module()
