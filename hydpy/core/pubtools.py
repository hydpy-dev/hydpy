# -*- coding: utf-8 -*-
"""This module provides features for handling public (global) project data."""
# import...
# ...from standard library
import types
from typing import *
from typing import NoReturn

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.core import propertytools
from hydpy.core import selectiontools
from hydpy.core import timetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.cythons.autogen import configutils


class _PubProperty(
    propertytools.DefaultProperty[
        propertytools.TypeInput,
        propertytools.TypeOutput,
    ]
):
    def __init__(self) -> None:
        super().__init__(self._fget)

    def _fget(self, obj: Any) -> NoReturn:
        raise exceptiontools.AttributeNotReady(
            f"Attribute {self.name} of module `pub` is not defined at the moment.",
        )


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
    >>> pub.timegrids = "2000-01-01", "2010-01-01", "1d"

    The given date and period information applies for the |Timegrids.init|,
    the |Timegrids.sim|, and the |Timegrids.eval_| attribute, as well:

    >>> pub.timegrids.init
    Timegrid("2000-01-01 00:00:00",
             "2010-01-01 00:00:00",
             "1d")
    >>> pub.timegrids.sim
    Timegrid("2000-01-01 00:00:00",
             "2010-01-01 00:00:00",
             "1d")
    >>> pub.timegrids.eval_
    Timegrid("2000-01-01 00:00:00",
             "2010-01-01 00:00:00",
             "1d")

    Alternatively, you can assign a ready |Timegrids| object directly:

    >>> pub.timegrids = Timegrids(Timegrid("2000-01-01", "2010-01-01", "1d"),
    ...                           Timegrid("2000-01-01", "2001-01-01", "1d"))
    >>> pub.timegrids
    Timegrids(init=Timegrid("2000-01-01 00:00:00",
                            "2010-01-01 00:00:00",
                            "1d"),
              sim=Timegrid("2000-01-01 00:00:00",
                           "2001-01-01 00:00:00",
                           "1d"),
              eval_=Timegrid("2000-01-01 00:00:00",
                             "2001-01-01 00:00:00",
                             "1d"))
    """

    def call_fset(
        self,
        obj: Any,
        value: Union[
            timetools.Timegrids,
            Tuple[
                timetools.DateConstrArg,
                timetools.DateConstrArg,
                timetools.PeriodConstrArg,
            ],
        ],
    ) -> None:
        """Try to convert the given input value(s)."""
        try:
            timegrids = timetools.Timegrids(*value)
        except TypeError:
            timegrids = timetools.Timegrids(value)  # type: ignore
            # this will most likely fail, we just want to reuse
            # the standard error message
        super().call_fset(obj, timegrids)


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
    ValueError: While trying to define a new `Timegrids` object based on the \
arguments `None`, the following error occurred: Initialising a `Timegrids` \
object either requires one, two, or three `Timegrid` objects or two dates objects \
(of type `Date`, `datetime`, or `str`) and one period object (of type \
`Period`, `timedelta`, or `str`), but objects of the types `None, None, and \
None` are given.

    >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
    >>> pub.timegrids
    Timegrids("2000-01-01 00:00:00",
              "2001-01-01 00:00:00",
              "1d")

    After deleting, the attribute is not accessible anymore:

    >>> del pub.timegrids
    >>> pub.timegrids
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute timegrids of \
module `pub` is not defined at the moment.
    """

    options: optiontools.Options
    config: "configutils.Config"
    scriptfunctions: Dict[str, ScriptFunction]

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

    def __init__(self, name: str, doc: Optional[str] = None) -> None:
        super().__init__(
            name=name,
            doc=doc,
        )
        self.options = optiontools.Options()
        self.scriptfunctions = {}
