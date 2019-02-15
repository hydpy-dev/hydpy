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
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import autodoctools


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


class DeviceABC(abc.ABC):
    """See class |Device|."""

    name: str


class NodeABC(DeviceABC):
    """See class |Node|."""

    name: str
    entries: 'ElementsABC'
    exits: 'ElementsABC'


class ElementABC(DeviceABC):
    """See class |Element|."""

    inlets: 'NodesABC'
    outlets: 'NodesABC'
    receivers: 'NodesABC'
    senders: 'NodesABC'
    model: 'ModelABC'


class DevicesABC(abc.ABC):
    """See class |Devices|."""

    names: List[str]

    def __len__(self):
        ...


class NodesABC(DevicesABC):
    """See class |Nodes|."""

    ConstrArg = Union[None, NodeABC, str, Iterable[Union[NodeABC, str]]]

    def copy(self) -> 'NodesABC':
        ...

    def __getitem__(self, name: str) -> NodeABC:
        ...

    def __iter__(self) -> Iterator[NodeABC]:
        ...

    def __add__(self, values: 'NodesABC.ConstrArg') -> 'NodesABC':
        ...

    def __sub__(self, values: 'NodesABC.ConstrArg') -> 'NodesABC':
        ...

    def __lt__(self, other: DevicesABC) -> 'NodesABC':
        ...

    def __le__(self, other: DevicesABC) -> 'NodesABC':
        ...

    def __eq__(self, other: DevicesABC) -> 'NodesABC':
        ...

    def __ne__(self, other: DevicesABC) -> 'NodesABC':
        ...

    def __ge__(self, other: DevicesABC) -> 'NodesABC':
        ...

    def __gt__(self, other: DevicesABC) -> 'NodesABC':
        ...


class ElementsABC(DevicesABC):
    """See class |Elements|."""

    ConstrArg = Union[None, ElementABC, str, Iterable[Union[ElementABC, str]]]
    __init__: callable

    def copy(self) -> 'ElementsABC':
        ...

    def __getitem__(self, name: str) -> ElementABC:
        ...

    def __iter__(self) -> Iterator[ElementABC]:
        ...

    def __add__(self, values: 'ElementsABC.ConstrArg') -> 'ElementsABC':
        ...

    def __sub__(self, values: 'ElementsABC.ConstrArg') -> 'ElementsABC':
        ...

    def __lt__(self, other: DevicesABC) -> 'ElementsABC':
        ...

    def __le__(self, other: DevicesABC) -> 'ElementsABC':
        ...

    def __eq__(self, other: DevicesABC) -> 'ElementsABC':
        ...

    def __ne__(self, other: DevicesABC) -> 'ElementsABC':
        ...

    def __ge__(self, other: DevicesABC) -> 'ElementsABC':
        ...

    def __gt__(self, other: DevicesABC) -> 'ElementsABC':
        ...


class DevicesHandlerABC(abc.ABC):
    """Without concrete implementation."""

    nodes: NodesABC
    elements: ElementsABC


class SelectionABC(abc.ABC):
    """See class |Selection|."""

    name: str
    nodes: NodesABC
    elements: ElementsABC


class VariableABC(abc.ABC):
    """See class |Variable|."""
    value: Union[float, int, numpy.ndarray]
    values: Union[float, int, numpy.ndarray]
    initvalue: Union[float, int]
    fastaccess: Any


class ParameterABC(VariableABC):
    """See class |Parameter|."""


class ANNABC(abc.ABC):
    """See class |anntools.ANN|."""


class SeasonalANNABC(abc.ABC):
    """See class |anntools.SeasonalANN|."""


class IOSequencesABC(abc.ABC):
    """See class |IOSequences|."""


class InputSequencesABC(abc.ABC):
    """See class |InputSequences|."""


class OutputSequencesABC(abc.ABC):
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


class PeriodABC(abc.ABC):
    """See class |Period|."""

    ConstrArg = Union[None, 'PeriodABC', datetime.timedelta, str]
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

    @abc.abstractmethod
    def connect(self):
        ...

    @abc.abstractmethod
    def doit(self, idx):
        ...


__all__ = [
    'DeviceABC',
    'NodeABC',
    'ElementABC',
    'DevicesABC',
    'NodesABC',
    'ElementsABC',
    'DevicesHandlerABC',
    'SelectionABC',
    'VariableABC',
    'ParameterABC',
    'ANNABC',
    'SeasonalANNABC',
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
]

autodoctools.autodoc_module()
