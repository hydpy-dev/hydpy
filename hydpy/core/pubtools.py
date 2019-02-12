# -*- coding: utf-8 -*-
"""This module provides features for handling public (global) project data."""
# import...
# ...from standard library
from typing import Dict, Callable
import types
# ...from HydPy
from hydpy.core import autodoctools
from hydpy.core import filetools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.core import propertytools
from hydpy.core import selectiontools
from hydpy.core import timetools


class _PubProperty(propertytools.DefaultProperty):

    def __init__(self):
        super().__init__(self._fget)

    def _fget(self, obj):
        raise RuntimeError(
            f'Attribute {self.name} of module `pub` '
            f'is not defined at the moment.')


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
    RuntimeError: Attribute timegrids of module `pub` \
is not defined at the moment.

    After setting an attribute value successfully, it is accessible (we
    select the `timegrids` attribute here, as its setter supplies a little
    magic to make defining new |Timegrids| objects more convenient:

    >>> pub.timegrids = None
    Traceback (most recent call last):
    ...
    AttributeError: While trying to define a new Timegrids object based \
on arguments `None`, the following error occurred: While trying to prepare \
a Trimegrid object based on the arguments `None , the following error \
occurred: 'NoneType' object has no attribute 'firstdate' Either pass one \
preprepared Timegrid object or three objects interpretable as dates and \
periods. Either pass one `Timegrids` object, one or two `Timegrid` objects, \
or three strings.


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
    RuntimeError: Attribute timegrids of module `pub` \
is not defined at the moment.
    """
    projectname: str = _PubProperty()
    indexer: indextools.Indexer = _PubProperty()
    networkmanager: filetools.NetworkManager = _PubProperty()
    controlmanager: filetools.ControlManager = _PubProperty()
    conditionmanager: filetools.ConditionManager = _PubProperty()
    sequencemanager: filetools.SequenceManager = _PubProperty()
    timegrids: timetools.Timegrids = _PubProperty()
    selections: selectiontools.Selections = _PubProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options: optiontools.Options = optiontools.Options()
        self.scriptfunctions: Dict[str, Callable] = {}

    @timegrids.setter_
    def timegrids(self, args):
        try:
            return timetools.Timegrids(*args)
        except TypeError:
            return timetools.Timegrids(args)

    def get(self, name, default=None):
        """Return |None| or the given default value, if the attribute
         defined by the given name is not accessible at the moment.

        >>> from hydpy import pub
        >>> pub.get('timegrids') is None
        True
        >>> pub.get('timegrids', 'test')
        'test'
        """
        try:
            return getattr(self, name)
        except RuntimeError:
            return default


autodoctools.autodoc_module()
