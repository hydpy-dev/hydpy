# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""This module provides some abstract base classes.

There are some type checks within the HydPy framework relying on the
build in  function |isinstance|.  In order to keep HydPy "pythonic",
the following abstract base classes are defined.  All calls to |isinstance|
should rely these abstract base classes instead of the respective
original classes.  This helps to build e.g. a new parameter class when
one wants to avoid to inherit from |Parameter|.

At the moment, the provided classes do not provide things like abstract
methods (should be added later).  Just use them to register new classes
that are not actual subclasses of the respective HydPy classes, but
should be handled as if they were.  See class |anntools.ANN| as an example.
"""
# import...
# ...from standard library
import abc
import datetime
from typing import *
from typing_extensions import Protocol
# ...from site-packages
import numpy
# ...from hydpy
if TYPE_CHECKING:
    from hydpy.core import devicetools

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


class IterableNonStringABC(abc.ABC):
    """Abstract base class for checking if an object is iterable but not a
    string."""

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is IterableNonStringABC:
            return (hasattr(subclass, '__iter__') and
                    not (isinstance(subclass, str) or
                         issubclass(subclass, str)))
        return NotImplemented


class NodeABC(abc.ABC):
    """See class |Node|."""


class ElementABC(abc.ABC):
    """See class |Element|."""


class NodesABC(abc.ABC):
    """See class |Nodes|."""


class ElementsABC(abc.ABC):
    """See class |Elements|."""


class DevicesHandlerProtocol(Protocol):
    """Without concrete implementation."""

    nodes: 'devicetools.Nodes'
    elements: 'devicetools.Elements'


class VariableABC(abc.ABC):
    """See class |Variable|."""
    value: Union[float, int, numpy.ndarray]
    values: Union[float, int, numpy.ndarray]
    initvalue: Union[float, int]
    fastaccess: Any


class ParametersABC(abc.ABC):
    """See class |Parameters|."""

    @abc.abstractmethod
    def update(self) -> None:
        ...


class ParameterABC(VariableABC):
    """See class |Parameter|."""


class ANNABC(abc.ABC):
    """See class |anntools.ANN|."""


class SeasonalANNABC(abc.ABC):
    """See class |anntools.SeasonalANN|."""


class SequencesABC(abc.ABC):
    """See class |Sequences|."""
    
    inputs: 'InputSequencesABC'
    fluxes: 'FluxSequencesABC'
    states: 'StateSequencesABC'

    @abc.abstractmethod
    def __iter__(self) -> Iterator['SequenceABC']:
        ...

    @abc.abstractmethod
    def open_files(self, idx: int) -> None:
        ...

    @abc.abstractmethod
    def close_files(self) -> None:
        ...

    @abc.abstractmethod
    def reset(self) -> None:
        ...

    @property
    @abc.abstractmethod
    def conditions(self) -> Dict[str, Dict[str, Union[float, numpy.ndarray]]]:
        pass

    @abc.abstractmethod
    def trim_conditions(self) -> None:
        ...


class IOSequencesABC(SequencesABC, metaclass=abc.ABCMeta):
    """See class |IOSequences|."""


class InputSequencesABC(IOSequencesABC, metaclass=abc.ABCMeta):
    """See class |InputSequences|."""


class OutputSequencesABC(IOSequencesABC, metaclass=abc.ABCMeta):
    """See class "OutputSequences" classes
    like |FluxSequences|."""


class SequenceABC(VariableABC):
    """See class |Sequence|."""


class IOSequenceABC(SequenceABC):
    """See class |IOSequence|."""


class ModelSequenceABC(IOSequenceABC):
    """See class |ModelSequence|."""


class InputSequenceABC(ModelSequenceABC):
    """See class |InputSequence|."""
    pass


class FluxSequenceABC(ModelSequenceABC):
    """See class |FluxSequence|."""
    pass


class ConditionSequenceABC(ModelSequenceABC):
    """See class |ConditionSequence| classes.
    """


class StateSequenceABC(ConditionSequenceABC):
    """See class |StateSequence|."""


class LogSequenceABC(ConditionSequenceABC):
    """See class |LogSequence|."""


class AideSequenceABC(SequenceABC):
    """See class |AideSequence|."""


class LinkSequenceABC(SequenceABC):
    """See class |LinkSequence|."""


class NodeSequenceABC(IOSequenceABC):
    """See class |NodeSequence|."""


class MaskABC(abc.ABC):
    """See class `Mask` classes."""


class DateABC(abc.ABC):
    """See class |Date|."""

    datetime: datetime.datetime


Union['PeriodABC', datetime.timedelta, str, None]


class PeriodABC(abc.ABC):
    """See class |Period|."""

    ConstrArg = Union['PeriodABC', datetime.timedelta, str, None]
    TimeDeltaArg = ConstrArg
    timedelta: 'PeriodABC'


class TimegridABC(abc.ABC):
    """See class |Timegrid|."""

    firstdate: DateABC
    lastdate: DateABC
    stepsize: PeriodABC


class TimegridsABC(abc.ABC):
    """See class |Timegrids|."""


class TOYABC(abc.ABC):
    """See class |TOY|."""

    month: int
    day: int
    hour: int
    minute: int
    second: int


class ModelABC(abc.ABC):
    """See class |Model|."""

    element: ElementABC
    parameters: ParametersABC
    sequences: SequencesABC

    def connect(self):
        ...

    def doit(self, idx):
        ...


class AuxfilerABC(abc.ABC):
    """See class |Auxfiler|."""

    @abc.abstractmethod
    def save(self, parameterstep: PeriodABC.ConstrArg,
             simulationstep: PeriodABC.ConstrArg):
        ...


__all__ = [
    'Mayberable1',
    'Mayberable2',
    'Mayberable3',
    'MayNonerable1',
    'MayNonerable2',
    'MayNonerable3',
    'NodeABC',
    'ElementABC',
    'NodesABC',
    'ElementsABC',
    'DevicesHandlerProtocol',
    'ParametersABC',
    'VariableABC',
    'ParameterABC',
    'ANNABC',
    'SeasonalANNABC',
    'SequencesABC',
    'IOSequencesABC',
    'OutputSequencesABC',
    'SequenceABC',
    'IOSequenceABC',
    'ModelSequenceABC',
    'InputSequenceABC',
    'FluxSequenceABC',
    'ConditionSequenceABC',
    'StateSequenceABC',
    'LogSequenceABC',
    'AideSequenceABC',
    'LinkSequenceABC',
    'NodeSequenceABC',
    'MaskABC',
    'DateABC',
    'PeriodABC',
    'TimegridABC',
    'TimegridsABC',
    'TOYABC',
    'ModelABC',
    'AuxfilerABC',
]
