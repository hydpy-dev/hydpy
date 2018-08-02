# -*- coding: utf-8 -*-
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
from __future__ import division, print_function
import abc
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import texttools


if pub.pyversion > 2:
    _ABC = abc.ABC
else:
    class _ABC(object):
        __metaclass__ = abc.ABCMeta


class IterableNonStringABC(_ABC):
    """Abstract base class for checking if an object is iterable but not a
    string."""

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is IterableNonStringABC:
            return (hasattr(subclass, '__iter__') and
                    not (isinstance(subclass, StringABC) or
                         issubclass(subclass, StringABC)))
        return NotImplemented


class StringABC(_ABC):
    """Abstract base class for registering string classes."""


if pub.pyversion == 2:
    # pylint: disable=undefined-variable
    StringABC.register(basestring)   # pragma: no cover
else:
    StringABC.register(str)


class HydPyABC(_ABC):
    """Abstract base class for registering custom |HydPy| classes."""


class KeywordsABC(_ABC):
    """Abstract base class for registering custom |Keywords| classes."""


class DeviceABC(_ABC):
    """Abstract base class for registering custom |Device| classes."""


class ElementABC(_ABC):
    """Abstract base class for registering custom |Element| classes."""


class NodeABC(_ABC):
    """Abstract base class for registering custom |Node| classes."""


class DevicesABC(_ABC):
    """Abstract base class for registering custom |Devices| classes."""


class ElementsABC(_ABC):
    """Abstract base class for registering custom |Elements| classes."""


class NodesABC(_ABC):
    """Abstract base class for registering custom |Nodes| classes."""


class ConnectionsABC(_ABC):
    """Abstract base class for registering custom |Connections| classes."""


class VariableABC(_ABC):
    """Abstract base class for registering custom |Variable| classes."""


class ParameterABC(VariableABC):
    """Abstract base class for registering custom |Parameter| classes."""


class ANNABC(ParameterABC):
    """Abstract base class for registering custom |anntools.ANN| classes."""


class SeasonalANNABC(ParameterABC):
    """Abstract base class for registering custom |anntools.SeasonalANN|
    classes."""


class _SubgroupABCMeta(abc.ABCMeta):
    """Type for generating subclasses of |SubParameters|, |SubSequences|,
    and |Masks|.

    See class |SubParameters| for the effects of applying |MetaSubgroupType|.
    """
    def __new__(mcs, name, parents, dict_):
        classes = dict_.get('CLASSES')
        if classes:
            lst = ['\n\n\n    The following classes are selected:']
            for cls in classes:
                lst.append('      * :class:`~%s` %s'
                           % ('.'.join((cls.__module__,
                                        cls.__name__)),
                              texttools.description(cls)))
            doc = dict_.get('__doc__', None)
            if doc is None:
                doc = ''
            dict_['__doc__'] = doc + '\n'.join(l for l in lst)
        return abc.ABCMeta.__new__(mcs, name, parents, dict_)


if pub.pyversion > 2:
    class _SubgroupABC(metaclass=_SubgroupABCMeta):
        pass
else:
    class _SubgroupABC(object):
        __metaclass__ = _SubgroupABCMeta


class SubgroupABC(_SubgroupABC):
    """Abstract base class for registering custom `Subgroup` classes."""


class IOSequencesABC(SubgroupABC):
    """Abstract base class for registering custom |IOSequences| classes."""


class InputSequencesABC(IOSequencesABC):
    """Abstract base class for registering custom |InputSequences| classes."""


class OutputSequencesABC(_ABC):
    """Abstract base class for registering custom "OutputSequences" classes
    like |FluxSequences|."""


class SequenceABC(VariableABC):
    """Abstract base class for registering custom |Sequence| classes."""


class IOSequenceABC(SequenceABC):
    """Abstract base class for registering custom |IOSequence| classes."""


class ModelIOSequenceABC(IOSequenceABC):
    """Abstract base class for registering custom |ModelIOSequence| classes."""


class InputSequenceABC(ModelIOSequenceABC):
    """Abstract base class for registering custom |InputSequence| classes."""


class FluxSequenceABC(ModelIOSequenceABC):
    """Abstract base class for registering custom |FluxSequence| classes."""
    pass


class ConditionSequenceABC(ModelIOSequenceABC):
    """Abstract base class for registering custom |ConditionSequence| classes.
    """


class StateSequenceABC(ConditionSequenceABC):
    """Abstract base class for registering custom |StateSequence| classes."""


class LogSequenceABC(ConditionSequenceABC):
    """Abstract base class for registering custom |LogSequence| classes."""


class AideSequenceABC(SequenceABC):
    """Abstract base class for registering custom |AideSequence| classes."""


class LinkSequenceABC(SequenceABC):
    """Abstract base class for registering custom |LinkSequence| classes."""


class NodeSequencesABC(IOSequencesABC):
    """Abstract base class for registering custom |NodeSequences| classes."""


class NodeSequenceABC(IOSequenceABC):
    """Abstract base class for registering custom |NodeSequence| classes."""


class MaskABC(_ABC):
    """Abstract base class for registering custom `Mask` classes."""


class DateABC(_ABC):
    """Abstract base class for registering custom |Date| classes."""


class PeriodABC(_ABC):
    """Abstract base class for registering custom |Period| classes."""


class TimegridABC(_ABC):
    """Abstract base class for registering custom |Timegrid| classes."""


class TimegridsABC(_ABC):
    """Abstract base class for registering custom |Timegrids| classes."""


class TOYABC(_ABC):
    """Abstract base class for registering custom |TOY| classes."""


class _ModelABCMeta(abc.ABCMeta):

    def __new__(mcs, cls_name, cls_parents, dict_):
        _METHOD_GROUPS = ('_RUN_METHODS', '_ADD_METHODS',
                          '_INLET_METHODS', '_OUTLET_METHODS',
                          '_RECEIVER_METHODS', '_SENDER_METHODS',
                          '_PART_ODE_METHODS', '_FULL_ODE_METHODS')
        dict_['_METHOD_GROUPS'] = _METHOD_GROUPS
        for method_name in _METHOD_GROUPS:
            methods = dict_.get(method_name, ())
            if methods:
                if method_name == '_RUN_METHODS':
                    lst = ['\n\n\n    The following "run methods" are called '
                           'each simulation step run in the given sequence:']
                elif method_name == '_ADD_METHODS':
                    lst = ['\n\n\n    The following "additional methods" are '
                           'called by at least one "run method":']
                elif method_name == '_INLET_METHODS':
                    lst = ['\n\n\n    The following "inlet update methods" '
                           'are called in the given sequence immediately  '
                           'before solving the differential equations '
                           'of the respective model:']
                elif method_name == '_OUTLET_METHODS':
                    lst = ['\n\n\n    The following "outlet update methods" '
                           'are called in the given sequence immediately  '
                           'after solving the differential equations '
                           'of the respective model:']
                elif method_name == '_RECEIVER_METHODS':
                    lst = ['\n\n\n    The following "receiver update methods" '
                           'are called in the given sequence before solving '
                           'the differential equations of any model:']
                elif method_name == '_SENDER_METHODS':
                    lst = ['\n\n\n    The following "sender update methods" '
                           'are called in the given sequence after solving '
                           'the differential equations of all models:']
                elif method_name == '_PART_ODE_METHODS':
                    lst = ['\n\n\n    The following methods define the '
                           'relevant components of a system of ODE '
                           'equations (e.g. direct runoff):']
                elif method_name == '_FULL_ODE_METHODS':
                    lst = ['\n\n\n    The following methods define the '
                           'complete equations of an ODE system '
                           '(e.g. change in storage of `fast water` due to '
                           ' effective precipitation and direct runoff):']
                else:
                    lst = []
                for method in methods:
                    lst.append('      * :func:`~%s` %s'
                               % ('.'.join((method.__module__,
                                            method.__name__)),
                                  texttools.description(method)))
                doc = dict_.get('__doc__', 'Undocumented model.')
                dict_['__doc__'] = doc + '\n'.join(l for l in lst)

        return abc.ABCMeta.__new__(mcs, cls_name, cls_parents, dict_)


if pub.pyversion > 2:
    class _ModelABC(metaclass=_ModelABCMeta):
        pass
else:
    class _ModelABC(object):
        __metaclass__ = _ModelABCMeta


class ModelABC(_ModelABC):

    """Abstract base class for registering custom |Model| classes."""

    @abc.abstractmethod
    def connect(self):
        ...

    @abc.abstractmethod
    def doit(self, idx):
        ...


autodoctools.autodoc_module()
