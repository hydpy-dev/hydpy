# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""This module implements some "types" to be used for static (and
eventually dynamical) typing."""
# import...
# ...from standard library
import abc
from typing import *
from typing_extensions import Protocol
# ...from site-packages
import numpy
# ...from hydpy
if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.core import timetools
    from hydpy.core import variabletools
    from hydpy.cythons import pointerutils

T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')

Mayberable1 = Union[T, Iterable[T]]
Mayberable2 = Union[T1, T2, Iterable[Union[T1, T2]]]
Mayberable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]]]
MayNonerable1 = Union[T, Iterable[T], None]
MayNonerable2 = Union[T1, T2, Iterable[Union[T1, T2]], None]
MayNonerable3 = Union[T1, T2, T3, Iterable[Union[T1, T2, T3]], None]


class IterableNonString(abc.ABC):
    """Abstract base class for checking if an object is iterable but not a
    string.
    
    >>> from hydpy.core.typingtools import IterableNonString
    >>> isinstance('asdf', IterableNonString)
    False
    >>> isinstance(['asdf'], IterableNonString)
    True
    >>> issubclass(str, IterableNonString)
    False
    >>> issubclass(list, IterableNonString)
    True
    >>>
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, '__iter__') and
                not (isinstance(subclass, str) or
                     issubclass(subclass, str)))


class DevicesHandlerProtocol(Protocol):
    """Without concrete implementation."""

    nodes: 'devicetools.Nodes'
    elements: 'devicetools.Elements'


class VariableProtocol(Protocol):
    """Protocol to identify objects as "variables"."""

    name: str

    def __init__(self, subvars: 'variabletools.SubgroupType'):
        """See class |Parameter| and class |Sequence|."""

    @abc.abstractmethod
    def __hydpy__connect_variable2subgroup__(self):
        """To be called by the |SubVariables| object when preparing a
        new |Variable| object."""


class CyModelProtocol(Protocol):
    """The protocol of Cython extension classes for defining
    efficient model implementations.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """

    sequences: Any


class FastAccessModelSequenceProtocol(Protocol):
    """The protocol of Cython extension classes for replacing
    the Python surrogate class |FastAccessModelSequence|.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """

    def open_files(self, idx: int) -> None:
        """Open the internal data files of all handled sequences with
        an activated |IOSequence.diskflag| and seek the position
        indicated by the given index."""

    def close_files(self) -> None:
        """Close the internal data files of all handled sequences with
        an activated |IOSequence.diskflag|."""

    def load_data(self, idx: int) -> None:
        """Let all handled sequences with an activated |IOSequence.memoryflag|
        load the data corresponding to the given index either from RAM
        (with |IOSequence.ramflag| being |True|) or from disk (with
        |IOSequence.diskflag| being |True|)."""

    def save_data(self, idx: int) -> None:
        """Let all handled sequences with an activated |IOSequence.memoryflag|
        save their actual data either to RAM (with |IOSequence.ramflag| being
        |True|) or to disk (with |IOSequence.diskflag|)."""


class FastAccessLinkSequenceProtocol(FastAccessModelSequenceProtocol):
    """The protocol of Cython extension classes for replacing
    the Python surrogate class |FastAccessModelSequence| when
    working with |LinkSequence| subclasses.

    Class |Cythonizer| generates the actual, model specific
    implementations automatically.
    """

    def alloc(self, name: str, length: int) -> None:
        """Allocate enough memory for the given vector length for the
        |LinkSequence| with the given name.

        |FastAccessLinkSequenceProtocol.alloc| has be implemented in case
        of the existence of 1-dimensional |LinkSequence| subclasses only.
        """

    def dealloc(self, name: str) -> None:
        """Free the previously allocated memory of the |LinkSequence| with
        the given name.

        |FastAccessLinkSequenceProtocol.alloc| has be implemented in case
        of the existence of 1-dimensional |LinkSequence| subclasses only.
        """

    def set_pointer0d(self, name: str, value: 'pointerutils.PDouble'):
        """Use the given |PDouble| object as the pointer of the
        0-dimensional |LinkSequence| object with the given name.

        |FastAccessLinkSequenceProtocol.alloc| has be implemented in case
        of the existence of 0-dimensional |LinkSequence| subclasses only.
        """

    def set_pointer1d(self, name: str, value: 'pointerutils.PDouble', idx: int):
        """Use the given |PDouble| object as one of the pointers of the
        1-dimensional |LinkSequence| object with the given name.

        The given index defines the vector position of the pointer.

        |FastAccessLinkSequenceProtocol.alloc| has be implemented in case
        of the existence of 1-dimensional |LinkSequence| subclasses only.
        """

    def get_value(self, name: str) -> Union[float, numpy.ndarray]:
        """Return the actual value(s) the |LinkSequence| object with
        the given name is pointing to."""

    def set_value(self, name: str, value: Mayberable1[float]) -> None:
        """Change the actual value(s) the |LinkSequence| object with
        the given name is pointing to."""


__all__ = [
    'IterableNonString',
    'Mayberable1',
    'Mayberable2',
    'Mayberable3',
    'MayNonerable1',
    'MayNonerable2',
    'MayNonerable3',
    'DevicesHandlerProtocol',
    'VariableProtocol',
    'CyModelProtocol',
    'FastAccessModelSequenceProtocol',
    'FastAccessLinkSequenceProtocol',
]
