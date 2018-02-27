# -*- coding: utf-8 -*-
"""This module provides some abstract base classes.

There are some type checks within the HydPy framework relying on the
build in  function :func:`isinstance`.  In order to keep HydPy
"pythonic", the following abstract base classes are defined.  All
calls to :func:`isinstance` should rely these abstract base classes
instead of the respective original classes.  This helps to build e.g.
a new parameter class when one wants to avoid to inherit from |Parameter|.

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


if pub.pyversion > 2:
    _ABC = abc.ABC
else:
    class _ABC(object):
        __metaclass__ = abc.ABCMeta


class DocABC(_ABC):
    """ABC base class automatically documenting is registered subclasses."""

    _registry_empty = True

    @classmethod
    def register(cls, subclass):
        """Add information to the documentation of the given abstract base
        class and register the subclass afterwards.

        Subclass the new abstract base class `NewABC` and define some new
        concrete classes (`New1`, `New2`, `New3`) which do not inherit
        from `NewABC`:

        >>> from hydpy.core.abctools import DocABC
        >>> class NewABC(DocABC):
        ...    "A new base class."
        >>> class New1(object):
        ...     "First new class"
        >>> class New2(object):
        ...     "Second new class"
        >>> class New3(object):
        ...     "Third new class"

        The docstring `NewABC` is still the same as defined above:

        >>> print(NewABC.__doc__)
        A new base class.

        Now we register the concrete classes `New1` and `New2`:

        >>> NewABC.register(New2)
        >>> NewABC.register(New1)
        >>> NewABC.register(New2)

        Now the docstring of `NewABC` includes the information about
        the concrete classes already registered:

        >>> print(NewABC.__doc__)
        A new base class.
        <BLANKLINE>
        At the moment, the following classes are registered:
             * :class:`~hydpy.core.abctools.New2`
             * :class:`~hydpy.core.abctools.New1`

        Note that the docstring order is the registration order.
        Also note that the "accidental reregistration" of class
        `New2` does not modify the docstring.

        Now the concrete classes `New1` and `New2` are handled as
        if they were actual subclasses of `NewABC`, but class `New3`
        -- which had not been registered -- is not:

        >>> issubclass(New1, NewABC)
        True
        >>> isinstance(New1(), NewABC)
        True
        >>> issubclass(New2, NewABC)
        True
        >>> isinstance(New2(), NewABC)
        True
        >>> issubclass(New3, NewABC)
        False
        >>> isinstance(New3(), NewABC)
        False
        """
        if cls._registry_empty:
            cls._registry_empty = False
            cls.__doc__ += \
                '\n\nAt the moment, the following classes are registered:'
        if not issubclass(subclass, cls):
            cls.__doc__ += ('\n     * :class:`~%s`'
                            % str(subclass).split("'")[1])
            abc.ABCMeta.register(cls, subclass)


class IterableNonStringABC(_ABC):
    """Abstract base class for checking if an object is iterable but not a
    string."""

    @classmethod
    def __subclasshook__(cls, C):
        if cls is IterableNonStringABC:
            return (hasattr(C, '__iter__') and
                    not (isinstance(C, str) or
                         issubclass(C, str)))
        return NotImplemented


class ElementABC(DocABC):
    """Abstract base class for registering custom element classes."""
    pass


class NodeABC(DocABC):
    """Abstract base class for registering custom node classes."""
    pass


class VariableABC(DocABC):
    """Abstract base class for registering custom variable classes.

    Usually, new classes should either be registered as a parameter
    or a sequence.  Afterwards, they are automatically handled as
    :class:`Variable` subclasses:

    >>> from hydpy.core.abctools import VariableABC, ParameterABC
    >>> class New(object):
    ...     pass
    >>> issubclass(New, VariableABC)
    False
    >>> ParameterABC.register(New)
    >>> issubclass(New, VariableABC)
    True
    """


class ParameterABC(VariableABC):
    """Abstract base class for registering custom parameter classes."""


class ANNABC(DocABC):
    """Abstract base class for registering custom artificial neural network
    classes."""


class SequenceABC(VariableABC):
    """Abstract base class for registering custom sequence classes."""
    pass


class InputSequenceABC(SequenceABC):
    """Abstract base class for registering custom input sequence classes."""
    pass


class FluxSequenceABC(SequenceABC):
    """Abstract base class for registering custom flux sequence classes."""
    pass


class ConditionSequenceABC(SequenceABC):
    """Abstract base class for registering custom condition sequence classes.
    """
    pass


class StateSequenceABC(ConditionSequenceABC):
    """Abstract base class for registering custom state sequence classes."""
    pass


class LogSequenceABC(ConditionSequenceABC):
    """Abstract base class for registering custom log sequence classes."""
    pass


class AideSequenceABC(SequenceABC):
    """Abstract base class for registering custom aide sequence classes."""
    pass


class LinkSequenceABC(SequenceABC):
    """Abstract base class for registering custom link sequence classes."""
    pass


class NodeSequenceABC(SequenceABC):
    """Abstract base class for registering custom node sequence classes."""
    pass


class DateABC(SequenceABC):
    """Abstract base class for registering custom date classes."""
    pass


class PeriodABC(SequenceABC):
    """Abstract base class for registering custom period classes."""
    pass


class TimegridABC(SequenceABC):
    """Abstract base class for registering custom timegrid classes."""
    pass


class TimegridsABC(SequenceABC):
    """Abstract base class for registering custom timegrids classes."""
    pass


class TOYABC(SequenceABC):
    """Abstract base class for registering custom TOY classes."""
    pass


class ModelABC(SequenceABC):
    """Abstract base class for registering custom Model classes."""
    pass


autodoctools.autodoc_module()
