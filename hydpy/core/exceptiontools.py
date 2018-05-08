# -*- coding: utf-8 -*-
"""This module implements some exception classes and related features."""

from hydpy import pub


class ModuleNotAvailable(ImportError):
    """To be raised when a `HydPy` function requiring an optional module is
    called, but this module is not available."""


class OptionalImport(object):
    """Exectutes the given import command and returns the imported module.
    If the import is not possible, it returns and dummy object which raises
    a |ModuleNotAvailable| each time a function tries to access a member of
    the orignal module.

    When the module is availabe:

    >>> from hydpy.core.exceptiontools import OptionalImport
    >>> numpy = OptionalImport('import numpy')
    >>> numpy.nan
    nan

    When the module is not available:

    >>> numpie = OptionalImport('import numpie')
    >>> numpie.nan
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.ModuleNotAvailable: HydPy could not load \
module `numpie`.  This module is no general requirement but necessary \
for some specific functionalities.
    """

    def __new__(cls, command, do_not_freeze=True):
        try:
            if pub._am_i_an_exe and do_not_freeze:
                raise ImportError()
            exec(command)
            return eval(command.split()[-1])
        except BaseException:
            return object.__new__(cls)

    def __init__(self, command):
        self.name = command.split()[-1]

    def __getattr__(self, name):
        raise ModuleNotAvailable(
            'HydPy could not load module `%s`.  This module is no '
            'general requirement but necessary for some specific '
            'functionalities.'
            % self.name)
