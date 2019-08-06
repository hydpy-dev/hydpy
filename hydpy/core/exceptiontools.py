# -*- coding: utf-8 -*-
"""This module implements some exception classes and related features."""

# import...
# ...from standard-library
import importlib
from typing import *
# ...from HydPy
from hydpy.core import objecttools


class HydPyDeprecationWarning(DeprecationWarning):
    """Warning for deprecated HydPy features."""


class AttributeNotReady(AttributeError):
    """The attribute is principally defined, but must be prepared first."""


class OptionalModuleNotAvailable(ImportError):
    """A `HydPy` function requiring an optional module is called, but this
    module is not available."""


class OptionalImport:
    """Imports the first found module "lazily".

    >>> from hydpy.core.exceptiontools import OptionalImport
    >>> numpy = OptionalImport(
    ...     'numpy', ['numpie', 'numpy', 'os'], locals())
    >>> numpy.nan
    nan

    If no module could be imported at all, |OptionalImport| returns a
    dummy object which raises a |OptionalModuleNotAvailable| each time
    a one tries to access a member of the original module.

    >>> numpie = OptionalImport('numpie', ['numpie'], locals())
    >>> numpie.nan
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.OptionalModuleNotAvailable: HydPy could not \
load one of the following modules: `numpie`.  These modules are no general \
requirement but installing at least one of them is necessary for some \
specific functionalities.
    """

    def __init__(
            self,
            name: str,
            modules: List[str],
            namespace: Dict[str, Any],
            hooks: Tuple[str, ...] = ()) \
            -> None:
        self._name = name
        self._modules = modules
        self._namespace = namespace
        self._hooks = hooks

    def __getattr__(self, name: str) -> Any:
        module = None
        for modulename in self._modules:
            try:
                module = importlib.import_module(modulename)
                self._namespace[self._name] = module
                break
            except ImportError:
                pass
        for hook in self._hooks:
            exec(hook)
        if module:
            return getattr(module, name)
        raise OptionalModuleNotAvailable(
            f'HydPy could not load one of the following modules: '
            f'`{objecttools.enumeration(self._modules)}`.  These modules are '
            f'no general requirement but installing at least one of them '
            f'is necessary for some specific functionalities.')
