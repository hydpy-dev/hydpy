# -*- coding: utf-8 -*-
"""This module provides some abstract base classes.

There are some type checks within the HydPy framework relying on the
build in  function :func:`isinstance`.  In order to keep HydPy
"pythonic", the following abstract base classes are defined.  All
calls to :func:`isinstance` should rely these abstract base classes
instead of the respective original classes.  This helps to build e.g.
a new parameter class when one wants to avoid to inherit from
:class:`~hydpy.core.parametertools.Parameter`.

At the moment, the provided classes do not provide things like abstract
methods(should be added later).  Just use them to register new classes
that are not actual subclasses of the respective HydPy classes, but
should be handled as if they were.  See class
:class:`~hydpy.auxs.anntools.ANN` as an example.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import abc


class DocABC(abc.ABC):
    """ABC base class automatically documenting is registered subclasses."""

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
             * :class:`~ __main__.New2`
             * :class:`~ __main__.New1`

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
        if not cls._abc_registry:
            cls.__doc__ += \
                    '\n\nAt the moment, the following classes are registered:'
        if subclass not in cls._abc_registry:
            cls.__doc__ += ('\n     * :class:`~ %s`'
                            % str(subclass).split("'")[1])
            abc.ABCMeta.register(cls, subclass)


class IterableNonString(abc.ABC):
    """Abstract base class for checking if an object is iterable but not a
    string."""

    @classmethod
    def __subclasshook__(cls, C):
        if cls is IterableNonString:
            return (hasattr(C, '__iter__') and
                    not (isinstance(C, str) or
                         issubclass(C, str)))
        else:
            return NotImplemented


class Element(DocABC):
    """Abstract base class for registering custom element classes."""
    pass


class Node(DocABC):
    """Abstract base class for registering custom node classes."""
    pass


class Parameter(DocABC):
    """Abstract base class for registering custom parameter classes."""


class Sequence(DocABC):
    """Abstract base class for registering custom sequence classes."""
    pass


class InputSequence(Sequence):
    """Abstract base class for registering custom input sequence classes."""
    pass
