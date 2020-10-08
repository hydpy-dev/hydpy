# -*- coding: utf-8 -*-
"""This module provides features for handling public (global) project data."""
# import...
# ...from standard library
import types
from typing import *
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.core import propertytools
from hydpy.core import selectiontools
from hydpy.core import timetools
if TYPE_CHECKING:
    from hydpy.cythons.autogen import configutils


class _PubProperty(
    propertytools.DefaultProperty[
        propertytools.InputType,
        propertytools.OutputType,
    ]
):

    def __init__(self):
        super().__init__(self._fget)

    def _fget(self, obj):
        raise exceptiontools.AttributeNotReady(
            f'Attribute {self.name} of module `pub` '
            f'is not defined at the moment.')


class TimegridsProperty(
    _PubProperty[
        Union[
            timetools.Timegrids,
            Tuple[
                timetools.DateConstrArg,
                timetools.DateConstrArg,
                timetools.PeriodConstrArg,
            ],
        ],
        timetools.Timegrids,
    ]
):
    """|DefaultProperty| specialised for |Timegrids| objects.

    For convenience, property |TimegridsProperty| can create a |Timegrids|
    object from a combination of a first and a last date (of type |str| or
    |Date|) and a step size (of type |str| or |Period|):

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = '2000-01-01', '2010-01-01', '1d'

    The given date and period information applies both for the
    |Timegrids.init| and the |Timegrids.sim| |Timegrid| object:

    >>> pub.timegrids.init
    Timegrid('2000-01-01 00:00:00',
             '2010-01-01 00:00:00',
             '1d')
    >>> pub.timegrids.sim
    Timegrid('2000-01-01 00:00:00',
             '2010-01-01 00:00:00',
             '1d')

    Alternatively, you can assign a ready |Timegrids| object directly:

    >>> pub.timegrids = Timegrids(
    ...     Timegrid('2000-01-01', '2010-01-01', '1d'),
    ...     Timegrid('2000-01-01', '2001-01-01', '1d'))
    >>> pub.timegrids
    Timegrids(Timegrid('2000-01-01 00:00:00',
                       '2010-01-01 00:00:00',
                       '1d'),
              Timegrid('2000-01-01 00:00:00',
                       '2001-01-01 00:00:00',
                       '1d'))
    """

    @staticmethod
    def _fset(_, value):
        """Try to convert the given input value(s)."""
        try:
            return timetools.Timegrids(*value)
        except TypeError:
            return timetools.Timegrids(value)


class Pub(types.ModuleType):
    """Base class/module of module |pub|.

    After initialisation |pub| takes over |Pub| as its new base class.
    The reason for this complicated trick is that it makes the attribute
    handling of |pub| easier for users.

    You can import |pub| like other modules:

    >>> from hydpy import pub

    However, if you try to access unprepared attributes, |Pub| returns
    the following error message:

    >>> pub.timegrids
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute timegrids of \
module `pub` is not defined at the moment.

    After setting an attribute value successfully, it is accessible (we
    select the `timegrids` attribute here, as its setter supplies a little
    magic to make defining new |Timegrids| objects more convenient:

    >>> pub.timegrids = None
    Traceback (most recent call last):
    ...
    TypeError: While trying to define a new Timegrids object based on \
arguments `None`, the following error occurred: When passing a single \
argument to the constructor of class `Timegrids`, the argument must be \
a `Timegrid` or a `Timegrids` object, but a `NoneType` is given.


    >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'
    >>> pub.timegrids
    Timegrids(Timegrid('2000-01-01 00:00:00',
                       '2001-01-01 00:00:00',
                       '1d'))

    After deleting, the attribute is not accessible anymore:

    >>> del pub.timegrids
    >>> pub.timegrids
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute timegrids of \
module `pub` is not defined at the moment.
    """

    options: optiontools.Options
    config: 'configutils.Config'

    projectname = _PubProperty[
        str,
        str,
    ]()
    indexer = _PubProperty[
        indextools.Indexer,
        indextools.Indexer,
    ]()
    networkmanager = _PubProperty[
        filetools.NetworkManager,
        filetools.NetworkManager,
    ]()
    controlmanager = _PubProperty[
        filetools.ControlManager,
        filetools.ControlManager,
    ]()
    conditionmanager = _PubProperty[
        filetools.ConditionManager,
        filetools.ConditionManager,
    ]()
    sequencemanager = _PubProperty[
        filetools.SequenceManager,
        filetools.SequenceManager,
    ]()
    timegrids = TimegridsProperty()
    selections = _PubProperty[
        selectiontools.Selections,
        selectiontools.Selections,
    ]()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options: optiontools.Options = optiontools.Options()
        self.scriptfunctions: Dict[str, Callable] = {}
