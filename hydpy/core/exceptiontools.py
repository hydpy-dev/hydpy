# -*- coding: utf-8 -*-
"""This module implements some exception classes and related features."""

# import...
# ...from standard-library
import enum
import importlib
import types

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core.typingtools import *


class HydPyDeprecationWarning(DeprecationWarning):
    """Warning for deprecated *HydPy* features."""


class AttributeNotReady(RuntimeError):
    """The attribute is principally defined but so far unprepared."""


class AttributeNotReadyWarning(Warning):
    """The attribute is principally defined but so far unprepared."""


def attrready(obj: Any, name: str) -> bool:
    """Return |False| when trying the access the attribute of the given object
    results in an |AttributeNotReady| error and otherwise return |True|.

    In *HydPy*, some properties raise an |AttributeNotReady| error when one
    tries to access them before they are correctly set.  You can use method
    |attrready| to find out the current state of such properties without
    doing the related exception handling on your own:

    >>> from hydpy import attrready
    >>> from hydpy.core.parametertools import Parameter
    >>> class Par(Parameter):
    ...     NDIM, TYPE = 1, float
    >>> par = Par(None)
    >>> attrready(par, "NDIM")
    True
    >>> attrready(par, "ndim")
    Traceback (most recent call last):
    ...
    AttributeError: 'Par' object has no attribute 'ndim'
    >>> attrready(par, "shape")
    False
    >>> par.shape = 2
    >>> attrready(par, "shape")
    True
    """
    try:
        getattr(obj, name)
    except AttributeNotReady:
        return False
    return True


def hasattr_(obj: Any, name: str) -> bool:
    """Return |True| or |False| whether the object has an attribute with the
    given name.

    In *HydPy*, some properties raise an |AttributeNotReady| error when one
    tries to access them before they are correctly set, which also happens
    when one applies function |hasattr| to find out if the related object
    handles the property at all.  Function |hasattr_| extends function
    |hasattr| by also catching |AttributeNotReady| errors:

    >>> from hydpy import hasattr_
    >>> from hydpy.core.parametertools import Parameter
    >>> class Par(Parameter):
    ...     NDIM, TYPE = 1, float
    >>> par = Par(None)
    >>> hasattr_(par, "NDIM")
    True
    >>> hasattr_(par, "ndim")
    False
    >>> hasattr_(par, "shape")
    True
    >>> par.shape = 2
    >>> attrready(par, "shape")
    True
    """
    try:
        return hasattr(obj, name)
    except AttributeNotReady:
        return True


class _Enum(enum.Enum):
    GETATTR_NO_DEFAULT = 1


@overload
def getattr_(obj: Any, name: str) -> Any: ...


@overload
def getattr_(obj: Any, name: str, default: None) -> Optional[Any]: ...


@overload
def getattr_(obj: Any, name: str, default: T) -> T: ...


@overload
def getattr_(obj: Any, name: str, *, type_: type[T]) -> T: ...


@overload
def getattr_(obj: Any, name: str, default: None, type_: type[T]) -> Optional[T]: ...


@overload
def getattr_(obj: Any, name: str, default: T1, type_: type[T2]) -> Union[T1, T2]: ...


def getattr_(
    obj: Any,
    name: str,
    default: Union[T, _Enum] = _Enum.GETATTR_NO_DEFAULT,
    type_: Optional[type[T]] = None,
) -> Any:
    """Return the attribute with the given name or, if it does not exist,
    the default value, if available.

    In *HydPy*, some properties raise an |AttributeNotReady| error when one
    tries to access them before they are correctly set, which also happens
    when one applies function |getattr| with default values.  Function
    |getattr_| extends function |getattr| by also returning the default
    value when an |AttributeNotReady| error occurs:

    >>> from hydpy import getattr_
    >>> from hydpy.core.parametertools import Parameter
    >>> class Par(Parameter):
    ...     NDIM, TYPE = 1, float
    >>> par = Par(None)
    >>> getattr_(par, "NDIM")
    1
    >>> getattr_(par, "NDIM", 2)
    1
    >>> getattr_(par, "ndim")
    Traceback (most recent call last):
    ...
    AttributeError: 'Par' object has no attribute 'ndim'
    >>> getattr_(par, "ndim", 2)
    2

    >>> getattr_(par, "shape")
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for \
variable `par` can only be retrieved after it has been defined.
    >>> getattr_(par, "shape", (4,))
    (4,)
    >>> par.shape = 2
    >>> getattr_(par, "shape")
    (2,)
    >>> getattr_(par, "shape", (4,))
    (2,)

    Function |getattr_| allows to specify the expected return type and raises
    an |AssertionError| if necessary:

    >>> getattr_(par, "NDIM", type_=int)
    1
    >>> getattr_(par, "NDIM", type_=str)
    Traceback (most recent call last):
    ...
    AssertionError: returned type: int, allowed type: str

    Additionally, it infers the expected return type from the default argument
    automatically:

    >>> getattr_(par, "NDIM", "wrong")
    Traceback (most recent call last):
    ...
    AssertionError: returned type: int, allowed type(s): str

    If the attribute type differs from the default value type, you need to define
    the attribute type explicitly:

    >>> getattr_(par, "NDIM", "wrong", int)
    1
    """
    if default is _Enum.GETATTR_NO_DEFAULT:
        value = getattr(obj, name)
        if type_ is not None and not isinstance(value, type_):
            raise AssertionError(
                f"returned type: {type(value).__name__}, "
                f"allowed type: {type_.__name__}"
            )
        return value
    try:
        value = getattr(obj, name, default)
    except AttributeNotReady:
        return default
    types_ = ((type_,) if type_ else ()) + ((type(default),) if default else ())
    if types_ and not isinstance(value, types_):
        raise AssertionError(
            f"returned type: {type(value).__name__}, allowed type(s): "
            f"{objecttools.enumeration(type_.__name__ for type_ in types_)}"
        )
    return value


class OptionalModuleNotAvailable(ImportError):
    """A `HydPy` function requiring an optional module is called, but this
    module is not available."""


class OptionalImport(types.ModuleType):
    """Imports the first found module "lazily".

    >>> from hydpy.core.exceptiontools import OptionalImport
    >>> numpy = OptionalImport(
    ...     "numpy", ["numpie", "numpy", "os"], locals())
    >>> numpy.nan
    nan

    If no module could be imported at all, |OptionalImport| returns a
    dummy object which raises a |OptionalModuleNotAvailable| each time
    a one tries to access a member of the original module.

    >>> numpie = OptionalImport("numpie", ["numpie"], locals())
    >>> numpie.nan
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.OptionalModuleNotAvailable: HydPy could not \
load one of the following modules: `numpie`.  These modules are no general \
requirement but installing at least one of them is necessary for some \
specific functionalities.

    Note the very special case that |OptionalImport| raises a plain
    |AttributeError| when asked for the attribute `__wrapped__` (to avoid
    trouble when applying function `wrapt` of module |inspect|):

    >>> numpie.__wrapped__
    Traceback (most recent call last):
    ...
    AttributeError
    """

    def __init__(
        self, name: str, modules: list[str], namespace: dict[str, Any]
    ) -> None:
        self._name = name
        self._modules = modules
        self._namespace = namespace

    def __getattr__(self, name: str) -> Any:
        if name == "__wrapped__":
            raise AttributeError
        module = None
        for modulename in self._modules:
            try:
                module = importlib.import_module(modulename)
                self._namespace[self._name] = module
                break
            except ImportError:
                pass
        if module:
            return getattr(module, name)
        raise OptionalModuleNotAvailable(
            f"HydPy could not load one of the following modules: "
            f"`{objecttools.enumeration(self._modules)}`.  These modules are "
            f"no general requirement but installing at least one of them "
            f"is necessary for some specific functionalities."
        )
