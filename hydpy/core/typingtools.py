# -*- coding: utf-8 -*-
"""This module implements some "types" to be used for static (and
eventually dynamical) typing."""
# import...
# ...from standard library
import abc
from typing import *
from typing_extensions import Protocol  # type: ignore[misc]

# ...from hydpy
if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import hydpytools
    from hydpy.cythons.autogen import pointerutils

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

Mayberable1 = Union[T, Iterable[T]]
Mayberable2 = Union[T1, T2, Iterable[Union[T1, T2]]]
Mayberable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]]]
MayNonerable1 = Union[T, Iterable[T], None]
MayNonerable2 = Union[T1, T2, Iterable[Union[T1, T2]], None]
MayNonerable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]], None]

Vector = MutableMapping[int, float]


class IterableNonString(abc.ABC):
    """Abstract base class for checking if an object is iterable but not a
    string.

    >>> from hydpy.core.typingtools import IterableNonString
    >>> isinstance("asdf", IterableNonString)
    False
    >>> isinstance(["asdf"], IterableNonString)
    True
    >>> issubclass(str, IterableNonString)
    False
    >>> issubclass(list, IterableNonString)
    True
    >>>
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "__iter__") and not (
            isinstance(subclass, str) or issubclass(subclass, str)
        )


class VariableProtocol(Protocol):
    """Protocol to identify objects as "variables"."""

    name: str

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """To be called by the |SubVariables| object when preparing a
        new |Variable| object."""


class CyParametersProtocol(Protocol):
    """The protocol for the `parameters` attribute of Cython extension classes.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """


class CySequencesProtocol(Protocol):
    """The protocol for the `sequences` attribute of Cython extension classes.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """


class CyModelProtocol(Protocol):
    """The protocol of Cython extension classes for defining
    efficient model implementations.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """

    idx_sim: int
    parameters: CyParametersProtocol
    sequences: CySequencesProtocol


__all__ = [
    "IterableNonString",
    "Mayberable1",
    "Mayberable2",
    "Mayberable3",
    "MayNonerable1",
    "MayNonerable2",
    "MayNonerable3",
    "Vector",
    "VariableProtocol",
    "CyModelProtocol",
]
