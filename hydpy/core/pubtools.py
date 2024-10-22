"""This module provides features for handling public (global) project data."""

# import...
# ...from standard library
from __future__ import annotations
import types

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.core import propertytools
from hydpy.core import selectiontools
from hydpy.core import timetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.cythons import configutils


class _PubProperty(propertytools.DefaultProperty[T_contra, T_co]):
    def __init__(self) -> None:
        super().__init__(self._fget)

    def _fget(self, obj: Any) -> NoReturn:
        raise exceptiontools.AttributeNotReady(
            f"Attribute {self.name} of module `pub` is not defined at the moment."
        )


class _ProjectnameProperty(_PubProperty[str, str]):
    """The name of the current project and the project's root directory.

    One can manually set |Pub.projectname|:

    >>> from hydpy import create_projectstructure, HydPy, pub, TestIO
    >>> pub.projectname = "project_A"

    However, the usual way is to pass the project name to the constructor of class
    |HydPy|, which automatically sets |Pub.projectname|:

    >>> hp = HydPy("project_B")
    >>> pub.projectname
    'project_B'

    Changing |Pub.projectname| lets all file managers handled by the |pub| module
    forget their eventually previously memorised but now outdated working directories:

    >>> with TestIO(clear_all=True), pub.options.printprogress(True):
    ...     create_projectstructure("project_B")
    ...     for idx, filemanager in enumerate(pub.filemanagers):
    ...         filemanager.currentdir = f"dir_{idx}"  # doctest: +ELLIPSIS
    Directory ...project_B...dir_0 has been created.
    Directory ...project_B...dir_1 has been created.
    Directory ...project_B...dir_2 has been created.
    Directory ...project_B...dir_3 has been created.

    >>> pub.projectname = "project_C"
    >>> import os
    >>> with TestIO(clear_all=True), pub.options.printprogress(True):
    ...     create_projectstructure("project_C")
    ...     os.makedirs("project_C/conditions/test")
    ...     for filemanager in pub.filemanagers:
    ...         _ = filemanager.currentdir  # doctest: +ELLIPSIS
    The name of the network manager's current working directory has not been \
previously defined and is hence set to `default`.
    Directory ...project_C...default has been created.
    The name of the control manager's current working directory has not been \
previously defined and is hence set to `default`.
    Directory ...project_C...default has been created.
    The name of the condition manager's current working directory has not been \
previously defined and is hence set to `test`.
    The name of the sequence manager's current working directory has not been \
previously defined and is hence set to `default`.
    Directory ...project_C...default has been created.

    .. testsetup::

        >>> del pub.timegrids
    """

    def call_fset(self, obj: Any, value: str) -> None:
        try:
            for filemanager in hydpy.pub.filemanagers:
                filemanager.currentdir = None  # type: ignore[assignment]
        except exceptiontools.AttributeNotReady:
            pass
        super().call_fset(obj, value)


class TimegridsProperty(
    _PubProperty[
        Union[
            timetools.Timegrids,
            timetools.Timegrid,
            tuple[
                timetools.DateConstrArg,
                timetools.DateConstrArg,
                timetools.PeriodConstrArg,
            ],
        ],
        timetools.Timegrids,
    ]
):
    """|DefaultProperty| specialised for |Timegrids| objects.

    For convenience, property |TimegridsProperty| can create a |Timegrids| object from
    a combination of a first and last date (of type |str| or |Date|) and a step size
    (of type |str| or |Period|):

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = "2000-01-01", "2010-01-01", "1d"

    The given date and period information applies for the |Timegrids.init|, the
    |Timegrids.sim|, and the |Timegrids.eval_| attribute:

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
            timetools.Timegrid,
            tuple[
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
    """Base class of the singleton module instance |pub|.

    You can import |pub| like "normal" modules:

    >>> from hydpy import pub

    However, if you try to access unprepared attributes, |Pub| returns the following
    error message:

    >>> pub.timegrids
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute timegrids of module `pub` \
is not defined at the moment.

    After setting an attribute value successfully, it is accessible (we select the
    `timegrids` attribute here, as its setter supplies a little magic to make defining
    new |Timegrids| objects more convenient:

    >>> pub.timegrids = None
    Traceback (most recent call last):
    ...
    ValueError: While trying to define a new `Timegrids` object based on the \
arguments `None`, the following error occurred: Initialising a `Timegrids` object \
either requires one, two, or three `Timegrid` objects or two dates objects (of type \
`Date`, `datetime`, or `str`) and one period object (of type `Period`, `timedelta`, \
or `str`), but objects of the types `None, None, and None` are given.

    >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
    >>> pub.timegrids
    Timegrids("2000-01-01 00:00:00",
              "2001-01-01 00:00:00",
              "1d")

    After deleting it, the attribute is no longer accessible:

    >>> del pub.timegrids
    >>> pub.timegrids
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute timegrids of module `pub` \
is not defined at the moment.
    """

    options: optiontools.Options
    config: configutils.Config
    scriptfunctions: dict[str, Callable[..., Optional[int]]]

    projectname = _ProjectnameProperty()
    indexer = _PubProperty[indextools.Indexer, indextools.Indexer]()
    networkmanager = _PubProperty[filetools.NetworkManager, filetools.NetworkManager]()
    controlmanager = _PubProperty[filetools.ControlManager, filetools.ControlManager]()
    conditionmanager = _PubProperty[
        filetools.ConditionManager, filetools.ConditionManager
    ]()
    sequencemanager = _PubProperty[
        filetools.SequenceManager, filetools.SequenceManager
    ]()
    timegrids = TimegridsProperty()
    selections = _PubProperty[selectiontools.Selections, selectiontools.Selections]()

    def __init__(self, name: str, doc: Optional[str] = None) -> None:
        super().__init__(name=name, doc=doc)
        self.options = optiontools.Options()
        self.scriptfunctions = {}

    @property
    def filemanagers(self) -> Iterator[filetools.FileManager]:
        """Yield all file managers.

        >>> from hydpy import HydPy, pub
        >>> hp = HydPy("test")
        >>> for filemanager in pub.filemanagers:
        ...     type(filemanager).__name__
        'NetworkManager'
        'ControlManager'
        'ConditionManager'
        'SequenceManager'
        """
        yield self.networkmanager
        yield self.controlmanager
        yield self.conditionmanager
        yield self.sequencemanager
