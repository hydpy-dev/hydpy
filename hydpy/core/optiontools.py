"""This module implements features for defining local or global *HydPy* options."""

# import...
# ...from standard library
from __future__ import annotations
import itertools
import types

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import propertytools
from hydpy.core import timetools
from hydpy.core.typingtools import *

TypeOption = TypeVar(
    "TypeOption",
    bool,
    int,
    str,
    timetools.Period,
    SeriesFileType,
    SeriesAggregationType,
    SeriesConventionType,
)
TypeOptionContextBase = TypeVar("TypeOptionContextBase", bound="OptionContextBase[Any]")
TypeOptionPropertyBase = TypeVar(
    "TypeOptionPropertyBase", bound="OptionPropertyBase[Any, Any]"
)


class OptionContextBase(Generic[TypeOption]):
    """Base class for defining context managers required for the different
    |OptionPropertyBase| subclasses."""

    _old_value: TypeOption
    _new_value: Optional[TypeOption]
    _set_value: Optional[tuple[Callable[[Optional[TypeOption]], None]]]

    def __init__(
        self,
        value: TypeOption,
        set_value: Optional[Callable[[Optional[TypeOption]], None]] = None,
    ) -> None:
        self._old_value = value
        self._new_value = None
        if set_value is None:
            self._set_value = None
        else:
            self._set_value = (set_value,)

    def __call__(
        self: TypeOptionContextBase, new_value: Optional[TypeOption] = None
    ) -> TypeOptionContextBase:
        self._new_value = new_value
        return self

    def __enter__(self) -> None:
        if self._set_value is not None:
            self._set_value[0](self._new_value)

    def __exit__(
        self,
        exception_type: type[BaseException],
        exception_value: BaseException,
        traceback_: types.TracebackType,
    ) -> None:
        self._new_value = None
        if self._set_value is not None:
            self._set_value[0](self._old_value)


class OptionContextBool(int, OptionContextBase[bool]):
    """Context manager required by |OptionPropertyBool|."""

    def __new__(  # pylint: disable=unused-argument
        cls, value: bool, set_value: Optional[Callable[[bool], None]] = None
    ) -> OptionContextBool:
        return super().__new__(cls, value)

    def __repr__(self) -> str:
        return "TRUE" if self else "FALSE"


class OptionContextInt(int, OptionContextBase[int]):
    """Context manager required by |OptionPropertyInt|."""

    def __new__(  # pylint: disable=unused-argument
        cls, value: int, set_value: Optional[Callable[[int], None]] = None
    ) -> OptionContextInt:
        return super().__new__(cls, value)


class _OptionContextEllipsis(int, OptionContextBase[int]):
    def __new__(  # pylint: disable=unused-argument
        cls,
        value: int,
        set_value: Optional[Callable[[int], None]] = None,
        optional: bool = False,
    ) -> _OptionContextEllipsis:
        return super().__new__(cls, value)

    def __call__(
        self: TypeOptionContextBase,
        new_value: Optional[int] = None,
        optional: bool = False,
    ) -> TypeOptionContextBase:
        if optional and (self._old_value != -999):
            self._new_value = self._old_value
        else:
            self._new_value = new_value
        return self


class OptionContextStr(str, OptionContextBase[TypeOption]):
    """Context manager required by |OptionPropertyStr|."""

    def __new__(  # pylint: disable=unused-argument
        cls, value: TypeOption, set_value: Optional[Callable[[TypeOption], None]] = None
    ) -> Self:
        return super().__new__(cls, value)


class OptionContextPeriod(timetools.Period, OptionContextBase[timetools.Period]):
    """Context manager required by |OptionPropertyPeriod|."""

    _set_value: tuple[Callable[[Optional[timetools.PeriodConstrArg]], None]]

    def __new__(  # pylint: disable=unused-argument
        cls,
        value: timetools.PeriodConstrArg,
        set_value: Optional[
            Callable[[Optional[timetools.PeriodConstrArg]], None]
        ] = None,
    ) -> OptionContextPeriod:
        return super().__new__(cls, value)

    def __call__(
        self: TypeOptionContextBase,
        new_value: Optional[timetools.PeriodConstrArg] = None,
    ) -> TypeOptionContextBase:
        self._new_value = new_value
        return self


class OptionPropertyBase(
    propertytools.BaseDescriptor, Generic[TypeOption, TypeOptionContextBase]
):
    """Base class for defining descriptors that work like regular |property| instances
    and support the `with` statement to change the property's value temporarily."""

    _CONVERTER: tuple[Callable[[TypeOption], TypeOption]]
    _CONTEXT: type[TypeOptionContextBase]
    _default: TypeOption
    _obj2value: dict[Hashable, TypeOption]

    def __init__(self, default: TypeOption, doc: str) -> None:
        self._default = default
        self._obj2value = {}
        self.set_doc(doc)

    @overload
    def __get__(self, obj: None, typ: type[Hashable]) -> Self: ...

    @overload
    def __get__(self, obj: Hashable, typ: type[Hashable]) -> TypeOptionContextBase: ...

    def __get__(
        self, obj: Optional[Hashable], typ: type[Hashable]
    ) -> Union[Self, TypeOptionContextBase]:
        if obj is None:
            return self
        return self._CONTEXT(
            self._get_value(obj), lambda value: self._set_value(obj, value)
        )

    def __set__(self, obj: Hashable, value: TypeOption) -> None:
        self._obj2value[obj] = self._CONVERTER[0](value)

    def __delete__(self, obj: Hashable) -> None:
        if obj in self._obj2value:
            del self._obj2value[obj]

    def _get_value(self, obj: Hashable) -> TypeOption:
        return self._obj2value.get(obj, self._default)

    def _set_value(self, obj: Hashable, value: Optional[TypeOption] = None) -> None:
        if value is not None:
            self._obj2value[obj] = self._CONVERTER[0](value)


class OptionPropertyBool(OptionPropertyBase[bool, OptionContextBool]):
    """Descriptor for defining bool-like options.

    Framework developers should implement bool-like options as follows:

    >>> from hydpy.core.optiontools import OptionPropertyBool
    >>> class T:
    ...     v = OptionPropertyBool(True, "x")

    The given string serves as documentation:

    >>> T.v.__doc__
    'x'

    Users can change the current value "normally" by assignments:

    >>> t = T()
    >>> assert t.v
    >>> t.v = False
    >>> assert not t.v

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v

    In most cases, the preferred way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v(False):
    ...     assert not t.v
    ...     with t.v(True):
    ...         assert t.v
    ...         with t.v():
    ...             assert t.v
    ...             with t.v(None):
    ...                 assert t.v
    ...                 with t.v(False):
    ...                     assert not t.v
    ...                 with t.v():
    ...                     t.v = False
    ...                     assert not t.v
    ...                 assert t.v
    ...             assert t.v
    ...         assert t.v
    ...     assert not t.v
    >>> assert t.v

    >>> with t.v(False):
    ...     assert not t.v
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v
    """

    _CONVERTER = (bool,)
    _CONTEXT = OptionContextBool


class OptionPropertyInt(OptionPropertyBase[int, OptionContextInt]):
    """Descriptor for defining integer-like options.

    Framework developers should implement integer-like options as follows:

    >>> from hydpy.core.optiontools import OptionPropertyInt
    >>> class T:
    ...     v = OptionPropertyInt(1, "x")

    The given string serves as documentation:

    >>> T.v.__doc__
    'x'

    Users can change the current value "normally" by assignments:

    >>> t = T()
    >>> assert t.v == 1
    >>> t.v = 2
    >>> assert t.v == 2

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v == 1

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v(2):
    ...     assert t.v == 2
    ...     with t.v(3):
    ...         assert t.v == 3
    ...         with t.v():
    ...             assert t.v == 3
    ...             with t.v(None):
    ...                 assert t.v == 3
    ...                 with t.v(1):
    ...                     assert t.v == 1
    ...                 with t.v():
    ...                     t.v = 4
    ...                     assert t.v == 4
    ...                 assert t.v == 3
    ...             assert t.v == 3
    ...         assert t.v == 3
    ...     assert t.v == 2
    >>> assert t.v == 1

    >>> with t.v(2):
    ...     assert t.v == 2
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == 1
    """

    _CONVERTER = (int,)
    _CONTEXT = OptionContextInt


class _OptionPropertyEllipsis(OptionPropertyBase[int, _OptionContextEllipsis]):
    """
    >>> from hydpy.core.optiontools import _OptionPropertyEllipsis
    >>> class T:
    ...     v = _OptionPropertyEllipsis(1, "x")

    >>> T.v.__doc__
    'x'

    >>> t = T()
    >>> assert t.v == 1
    >>> t.v = 2
    >>> assert t.v == 2

    >>> del t.v
    >>> assert t.v == 1

    >>> with t.v(2):
    ...     assert t.v == 2
    ...     with t.v(3):
    ...         assert t.v == 3
    ...         with t.v():
    ...             assert t.v == 3
    ...             with t.v(None):
    ...                 assert t.v == 3
    ...                 with t.v(1):
    ...                     assert t.v == 1
    ...                 with t.v():
    ...                     t.v = 4
    ...                     assert t.v == 4
    ...                 assert t.v == 3
    ...             assert t.v == 3
    ...         assert t.v == 3
    ...     assert t.v == 2
    >>> assert t.v == 1

    >>> with t.v(2):
    ...     assert t.v == 2
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == 1

    >>> with t.v(2, optional=True):
    ...     assert t.v == 1
    >>> t.v = -999
    >>> with t.v(2, optional=True):
    ...     assert t.v == 2
    """

    _CONVERTER = (int,)
    _CONTEXT = _OptionContextEllipsis


class OptionPropertyStr(OptionPropertyBase[str, OptionContextStr]):
    """Descriptor for defining string-like options.

    Framework developers should implement string-like options as follows:

    >>> from hydpy.core.optiontools import OptionPropertyStr
    >>> class T:
    ...     v = OptionPropertyStr("1", "x")

    The given string serves as documentation:

    >>> T.v.__doc__
    'x'

    Users can change the current value "normally" by assignments:

    >>> t = T()
    >>> assert t.v == "1"
    >>> t.v = "2"
    >>> assert t.v == "2"

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v == "1"

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v("2"):
    ...     assert t.v == "2"
    ...     with t.v("3"):
    ...         assert t.v == "3"
    ...         with t.v():
    ...             assert t.v == "3"
    ...             with t.v(None):
    ...                 assert t.v == "3"
    ...                 with t.v("1"):
    ...                     assert t.v == "1"
    ...                 with t.v():
    ...                     t.v = "4"
    ...                     assert t.v == "4"
    ...                 assert t.v == "3"
    ...             assert t.v == "3"
    ...         assert t.v == "3"
    ...     assert t.v == "2"
    >>> assert t.v == "1"

    >>> with t.v("2"):
    ...     assert t.v == "2"
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == "1"
    """

    _CONVERTER = (str,)
    _CONTEXT = OptionContextStr


class OptionPropertyPeriod(OptionPropertyBase[timetools.Period, OptionContextPeriod]):
    """Descriptor for defining options of type |Period|.

    Framework or model developers should implement options of type |Period| as follows:

    >>> from hydpy.core.optiontools import OptionPropertyPeriod
    >>> class T:
    ...     v = OptionPropertyPeriod("1d", "x")

    The given string serves as documentation:

    >>> T.v.__doc__
    'x'

    Users can change the current value "normally" by assignments (note the automatic
    type conversion):

    >>> t = T()
    >>> assert t.v == "1d"
    >>> t.v = "2d"
    >>> from hydpy import Period
    >>> assert t.v == Period("2d")

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v == "1d"

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v("2d"):
    ...     assert t.v == "2d"
    ...     with t.v("3d"):
    ...         assert t.v == "3d"
    ...         with t.v():
    ...             assert t.v == "3d"
    ...             with t.v(None):
    ...                 assert t.v == "3d"
    ...                 with t.v("1d"):
    ...                     assert t.v == "1d"
    ...                 with t.v():
    ...                     t.v = "4d"
    ...                     assert t.v == "4d"
    ...                 assert t.v == "3d"
    ...             assert t.v == "3d"
    ...         assert t.v == "3d"
    ...     assert t.v == "2d"
    >>> assert t.v == "1d"

    >>> with t.v("2d"):
    ...     assert t.v == "2d"
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == "1d"
    """

    _CONVERTER = (timetools.Period,)
    _CONTEXT = OptionContextPeriod

    def __set__(self, obj: Hashable, value: timetools.PeriodConstrArg) -> None:
        self._obj2value[obj] = self._CONVERTER[0](value)

    def _set_value(
        self, obj: Hashable, value: Optional[timetools.PeriodConstrArg] = None
    ) -> None:
        if value is not None:
            self._obj2value[obj] = self._CONVERTER[0](value)


class _OptionPropertySimulationstep(OptionPropertyPeriod):
    def _get_value(self, obj: Hashable) -> timetools.Period:
        try:
            return hydpy.pub.timegrids.stepsize
        except exceptiontools.AttributeNotReady:
            return super()._get_value(obj)


def _check_seriesfiletype(value: SeriesFileType) -> SeriesFileType:
    try:
        if value == "nc":
            return "nc"
        if value == "npy":
            return "npy"
        if value == "asc":
            return "asc"
        assert_never(value)
    except AssertionError:
        raise ValueError(
            f"The given sequence file type `{value}` is not implemented.  Please "
            f"choose one of the following file types: npy, asc, and nc."
        ) from None
    assert False


class OptionPropertySeriesFileType(
    OptionPropertyBase[SeriesFileType, OptionContextStr[SeriesFileType]]
):
    """Descriptor for defining options of type |SeriesFileType|.

    *HydPy* currently supports a simple text format (`asc`), the numpy binary format
    (`npy`) and NetCDF files (`nc`).  Options based on |OptionPropertySeriesFileType|
    automatically check if the given string is a supported file-ending and raise errors
    if not:

    >>> from hydpy.core.optiontools import OptionPropertySeriesFileType
    >>> class T:
    ...     v = OptionPropertySeriesFileType("asc", "x")
    >>> T.v.__doc__
    'x'

    >>> t = T()
    >>> assert t.v == "asc"
    >>> t.v = "abc"
    Traceback (most recent call last):
    ...
    ValueError: The given sequence file type `abc` is not implemented.  Please choose \
one of the following file types: npy, asc, and nc.
    >>> assert t.v == "asc"
    >>> t.v = "npy"
    >>> assert t.v == "npy"
    >>> t.v = "nc"
    >>> assert t.v == "nc"
    >>> t.v = "asc"
    >>> assert t.v == "asc"

    >>> with t.v("abc"):
    ...     pass
    Traceback (most recent call last):
    ...
    ValueError: The given sequence file type `abc` is not implemented.  Please choose \
one of the following file types: npy, asc, and nc.
    >>> assert t.v == "asc"
    >>> with t.v("npy"):
    ...     assert t.v == "npy"
    ...     with t.v("nc"):
    ...         assert t.v == "nc"
    ...         with t.v():
    ...             assert t.v == "nc"
    ...         with t.v(None):
    ...             assert t.v == "nc"
    ...     assert t.v == "npy"
    >>> assert t.v == "asc"
    """

    _CONVERTER = (_check_seriesfiletype,)
    _CONTEXT = OptionContextStr[SeriesFileType]


def _check_seriesaggregationtype(value: SeriesAggregationType) -> SeriesAggregationType:
    try:
        if value == "none":
            return "none"
        if value == "mean":
            return "mean"
        assert_never(value)
    except AssertionError:
        raise ValueError(
            f"The given aggregation mode `{value}` is not implemented.  Please "
            f"choose one of the following modes: none and mean."
        ) from None
    assert False


class OptionPropertySeriesAggregation(
    OptionPropertyBase[SeriesAggregationType, OptionContextStr[SeriesAggregationType]]
):
    """Descriptor for defining options of type |SeriesAggregationType|.

    The only currently supported aggregation is averaging (`mean`).  Use `none` to
    avoid any aggregation.  Options based on |OptionPropertySeriesAggregation|
    automatically check if the given string meets one of these modes and raise errors
    if not:

    >>> from hydpy.core.optiontools import OptionPropertySeriesAggregation
    >>> class T:
    ...     v = OptionPropertySeriesAggregation("none", "x")
    >>> T.v.__doc__
    'x'

    >>> t = T()
    >>> assert t.v == "none"
    >>> t.v = "sum"
    Traceback (most recent call last):
    ...
    ValueError: The given aggregation mode `sum` is not implemented.  Please choose \
one of the following modes: none and mean.
    >>> assert t.v == "none"
    >>> t.v = "mean"
    >>> assert t.v == "mean"
    >>> t.v = "none"
    >>> assert t.v == "none"

    >>> with t.v("sum"):
    ...     pass
    Traceback (most recent call last):
    ...
    ValueError: The given aggregation mode `sum` is not implemented.  Please choose \
one of the following modes: none and mean.
    >>> assert t.v == "none"
    >>> with t.v("mean"):
    ...     assert t.v == "mean"
    ...     with t.v():
    ...         assert t.v == "mean"
    ...     with t.v(None):
    ...         assert t.v == "mean"
    ...     assert t.v == "mean"
    >>> assert t.v == "none"
    """

    _CONVERTER = (_check_seriesaggregationtype,)
    _CONTEXT = OptionContextStr[SeriesAggregationType]


def _check_seriesconventiontype(value: SeriesConventionType) -> SeriesConventionType:
    try:
        if value == "model-specific":
            return "model-specific"
        if value == "HydPy":
            return "HydPy"
        assert_never(value)
    except AssertionError:
        raise ValueError(
            f"The given time series naming convention `{value}` is not "
            f"implemented.  Please choose one of the following modes: "
            f"model-specific and HydPy."
        ) from None
    assert False


class OptionPropertySeriesConvention(
    OptionPropertyBase[SeriesConventionType, OptionContextStr[SeriesConventionType]]
):
    """Descriptor for defining options of type |SeriesConventionType|.

    *HydPy* currently follows two naming conventions when reading input time series.
    The original convention is to rely on the model-specific sequence names in
    lowercase letters ("model-specific").  The more convenient convention is to rely on
    the standard names defined by the enum |sequencetools.StandardInputNames|
    ("HydPy").  We will likely support more official naming conventions later and
    eventually allow writing time series following other conventions than the
    "model-specific" one:

    >>> from hydpy.core.optiontools import OptionPropertySeriesConvention
    >>> class T:
    ...     v = OptionPropertySeriesConvention("model-specific", "x")
    >>> T.v.__doc__
    'x'

    >>> t = T()
    >>> assert t.v == "model-specific"
    >>> t.v = "WMO"
    Traceback (most recent call last):
    ...
    ValueError: The given time series naming convention `WMO` is not implemented.  \
Please choose one of the following modes: model-specific and HydPy.
    >>> assert t.v == "model-specific"
    >>> t.v = "HydPy"
    >>> assert t.v == "HydPy"
    >>> t.v = "model-specific"
    >>> assert t.v == "model-specific"

    >>> with t.v("WMO"):
    ...     pass
    Traceback (most recent call last):
    ...
    ValueError: The given time series naming convention `WMO` is not implemented.  \
Please choose one of the following modes: model-specific and HydPy.

    >>> assert t.v == "model-specific"
    >>> with t.v("HydPy"):
    ...     assert t.v == "HydPy"
    ...     with t.v():
    ...         assert t.v == "HydPy"
    ...     with t.v(None):
    ...         assert t.v == "HydPy"
    ...     assert t.v == "HydPy"
    >>> assert t.v == "model-specific"
    """

    _CONVERTER = (_check_seriesconventiontype,)
    _CONTEXT = OptionContextStr[SeriesConventionType]


class Options:
    """Singleton class for the general options available in the global |pub| module.

    Most options are simple bool-like flags.

    You can change all options in two ways.  First, using the `with` statement makes
    sure the change is reverted after leaving the corresponding code block (even if an
    error occurs):

    >>> from hydpy import pub
    >>> pub.options.printprogress = 0
    >>> pub.options.printprogress
    FALSE
    >>> with pub.options.printprogress(True):
    ...     print(pub.options.printprogress)
    TRUE
    >>> pub.options.printprogress
    FALSE

    Alternatively, you can change all options via simple assignments:

    >>> pub.options.printprogress = True
    >>> assert pub.options.printprogress

    But then you might have to keep in mind to undo the change later:

    >>> assert pub.options.printprogress
    >>> pub.options.printprogress = False
    >>> assert not pub.options.printprogress

    When using the `with` statement, you can pass nothing or |None|, which does not
    change the original setting and resets it after leaving the `with` block:

    >>> with pub.options.printprogress(None):
    ...     assert not pub.options.printprogress
    ...     pub.options.printprogress = True
    ...     assert pub.options.printprogress
    >>> assert not pub.options.printprogress

    The delete statement restores the respective default setting:

    >>> del pub.options.printprogress
    >>> assert pub.options.printprogress

    >>> pub.options.printprogress = False
    """

    checkprojectstructure = OptionPropertyBool(
        True,
        """A bool-like flag for raising a warning when creating a |HydPy| instance for
        a project without the basic project structure on disk.

         Defaults usually to true but during testing to false:
         
        >>> from hydpy import HydPy, pub
        >>> assert not pub.options.checkprojectstructure
        >>> del pub.options.checkprojectstructure
        >>> assert pub.options.checkprojectstructure
        """,
    )

    checkseries = OptionPropertyBool(
        True,
        """A bool-like flag for raising an error when loading an input time series that 
        does not cover the whole initialisation period or contains |numpy.nan| 
        values.
        
        Defaults to true:
        
        >>> from hydpy import pub
        >>> assert pub.options.checkseries
        >>> del pub.options.checkseries
        >>> assert pub.options.checkseries
        """,
    )
    ellipsis = _OptionPropertyEllipsis(
        -999,
        """The maximum number of collection members shown in string representations 
        before and behind ellipsis points.
        
        Ellipsis points serve to shorten the string representations of iterable HydPy 
        objects that contain many entries.  Set this option to -999 to rely on the 
        default values of the respective iterable objects or zero to avoid any 
        ellipsis points.  -999 is the default value, but zero is the preferred value 
        during testing:
        
        >>> from hydpy import pub
        >>> assert pub.options.ellipsis == 0
        >>> del pub.options.ellipsis
        >>> assert pub.options.ellipsis == -999
        """,
    )
    parameterstep = OptionPropertyPeriod(
        timetools.Period("1d"),
        """The actual parameter time step size.  Change it by passing a |Period| object 
        or any valid |Period| constructor argument.  
        
        Defaults to one day:
        
        >>> from hydpy import pub
        >>> assert pub.options.parameterstep == "1d"
        >>> del pub.options.parameterstep
        >>> assert pub.options.parameterstep == "1d"
        """,
    )
    printprogress = OptionPropertyBool(
        True,
        """A bool-like flag for printing information about the progress of some 
        processes to the standard output.
        
        Defaults usually to true but during testing to false:
         
        >>> from hydpy import pub
        >>> assert not pub.options.printprogress
        >>> del pub.options.printprogress
        >>> assert pub.options.printprogress
        """,
    )
    reprdigits = OptionPropertyInt(
        -1,
        """The maximum number of decimal places for floating point numbers that are 
        part of HydPy's string representations (see function |repr_|).
        
        -1 means printing with the highest available precision.  Defaults usually to 
        -1 but during testing to 6:
        
        >>> from hydpy import pub
        >>> assert pub.options.reprdigits == 6   
        >>> del pub.options.reprdigits
        >>> assert pub.options.reprdigits == -1
        """,
    )
    simulationstep = _OptionPropertySimulationstep(
        timetools.Period(),
        """The actual simulation time step size.  
        
        HydPy does not define a default simulation step, which is indicated by an empty 
        |Period| object).  
        
        >>> from hydpy import pub
        >>> pub.options.simulationstep
        Period()
        
        Change it by passing a |Period| object or any valid |Period| constructor 
        argument, but note that you cannot manually define the |Options.simulationstep| 
        whenever it is already available via attribute |Timegrids.stepsize| of the 
        global |Timegrids| object in module |pub| (`pub.timegrids`):
        
        >>> pub.options.simulationstep = "1h"
        >>> pub.options.simulationstep
        Period("1h")
        
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> pub.options.simulationstep
        Period("1d")
     
        >>> pub.options.simulationstep = "1s"
        >>> pub.options.simulationstep
        Period("1d")
        
        >>> del pub.timegrids
        >>> pub.options.simulationstep
        Period("1s")
        
        >>> del pub.options.simulationstep
        >>> pub.options.simulationstep
        Period()
        """,
    )
    timestampleft = OptionPropertyBool(
        True,
        """A bool-like flag telling if assigning interval data (like hourly 
        precipitation) to single time points relies on the start (True, default) or the 
        end (False) of the respective interval.  

        HydPy-internally, we usually prevent such potentially problematic assignments 
        by using |Timegrid| objects that define grids of intervals instead of time 
        points.  However, exceptions cannot be avoided, such as when reading or writing 
        NetCDF files.
        
        Defaults to true:
        
        >>> from hydpy import pub
        >>> assert pub.options.timestampleft
        >>> del pub.options.timestampleft
        >>> assert pub.options.timestampleft
        """,
    )
    trimvariables = OptionPropertyBool(
        True,
        """A bool-like flag for enabling/disabling function |trim|.  Set it to |False| 
        only for good reasons.
        
        Defaults to true:
        
        >>> from hydpy import pub
        >>> assert pub.options.trimvariables
        >>> del pub.options.trimvariables
        >>> assert pub.options.trimvariables
        """,
    )
    usecython = OptionPropertyBool(
        True,
        """A bool-like flag for applying cythonized models, which are much faster than 
        pure Python models.
        
        The benefit of using pure Python models is they simplify debugging a lot.  
        Hence, setting this option to false makes sense when implementing a new model
        or when trying to discover why a model does not work as expected.
              
        Defaults to true, but note that all tests work with this flag being enabled and
        disabled.

        >>> from hydpy import pub
        >>> del pub.options.usecython
        >>> assert pub.options.usecython
        """,
    )
    usedefaultvalues = OptionPropertyBool(
        False,
        """A bool-like flag for initialising parameters with standard values.        
        
        Defaults to false:
        
        >>> from hydpy import pub
        >>> assert not pub.options.usedefaultvalues
        >>> del pub.options.usedefaultvalues
        >>> assert not pub.options.usedefaultvalues
        """,
    )
    utclongitude = OptionPropertyInt(
        15,
        """Longitude of the centre of the local time zone (see option
        |Options.utcoffset|).  
        
        Defaults to 15, which corresponds to the central meridian of UTC+01:00:
        
        >>> from hydpy import pub
        >>> assert pub.options.utclongitude == 15
        >>> del pub.options.utclongitude
        >>> assert pub.options.utclongitude == 15
        """,
    )
    utcoffset = OptionPropertyInt(
        60,
        """Local time offset from UTC in minutes s(see option |Options.utclongitude|.  
        
        Defaults to 60, which corresponds to UTC+01:00.

        >>> from hydpy import pub
        >>> assert pub.options.utcoffset == 60
        >>> del pub.options.utcoffset
        >>> assert pub.options.utcoffset == 60
        """,
    )
    warnmissingcontrolfile = OptionPropertyBool(
        False,
        """A bool-like flag for only raising a warning instead of an exception when a 
        necessary control file is missing.

        Defaults to false:
        
        >>> from hydpy import pub
        >>> assert not pub.options.warnmissingcontrolfile
        >>> del pub.options.warnmissingcontrolfile
        >>> assert not pub.options.warnmissingcontrolfile
        """,
    )
    warnmissingobsfile = OptionPropertyBool(
        True,
        """A bool-like flag for raising a warning when a requested observation sequence 
        demanded by a node instance is missing.

        Defaults to true:
        
        >>> from hydpy import pub
        >>> assert pub.options.warnmissingobsfile
        >>> del pub.options.warnmissingobsfile
        >>> assert pub.options.warnmissingobsfile
        """,
    )
    warnmissingsimfile = OptionPropertyBool(
        True,
        """A bool-like flag for raising a warning when a requested simulation sequence 
        demanded by a node instance is missing.

        Defaults to true:
        
        >>> from hydpy import pub
        >>> assert pub.options.warnmissingsimfile
        >>> del pub.options.warnmissingsimfile
        >>> assert pub.options.warnmissingsimfile
        """,
    )
    warnsimulationstep = OptionPropertyBool(
        True,
        """A bool-like flag for raising a warning when function |simulationstep| is
        called for the first time directly by the user.

        Defaults usually to true but during testing to false:
        
        >>> from hydpy import pub
        >>> assert not pub.options.warnsimulationstep
        >>> del pub.options.warnsimulationstep
        >>> assert pub.options.warnsimulationstep
        """,
    )
    warntrim = OptionPropertyBool(
        True,
        """A bool-like flag for raising a warning when a |Variable| object trims its
        value(s) not to violate certain boundaries.  
        
        To cope with the limited precision of floating-point numbers, only those 
        violations beyond a small tolerance value are reported (see function |trim|).

        Defaults usually to true but during testing to false:
        
        >>> from hydpy import pub
        >>> assert not pub.options.warntrim
        >>> del pub.options.warntrim
        >>> assert pub.options.warntrim
        """,
    )

    def __repr__(self) -> str:
        type_ = type(self)
        lines = ["Options("]
        for option in itertools.chain(vars(type_).keys(), vars(self).keys()):
            if not option.startswith("_"):
                value = getattr(self, option)
                lines.append(f"    {option} -> {repr(value)}")
        lines.append(")")
        return "\n".join(lines)
