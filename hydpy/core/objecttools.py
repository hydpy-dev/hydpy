# -*- coding: utf-8 -*-
"""This module implements tools to help to standardize the functionality
of the different objects defined by the HydPy framework."""
# import...
# ...from standard library
import builtins
import contextlib
import copy
import inspect
import itertools
import numbers
import sys
import textwrap
import types
from typing import *
from typing import NoReturn
from typing import TextIO
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import black
import wrapt

# ...from HydPy
import hydpy
from hydpy.core import typingtools

if TYPE_CHECKING:
    from hydpy.core import devicetools


_builtinnames = set(dir(builtins))

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
ReprArg = Union[
    numbers.Number,
    Iterable[numbers.Number],
    Iterable[Iterable[numbers.Number]],
]


def dir_(self: object) -> List[str]:
    """The prefered way for HydPy objects to respond to |dir|.

    Note the depencence on the `pub.options.dirverbose`.  If this option is
    set `True`, all attributes and methods of the given instance and its
    class (including those inherited from the parent classes) are returned:

    >>> from hydpy import pub
    >>> pub.options.dirverbose = True
    >>> from hydpy.core.objecttools import dir_
    >>> class Test:
    ...     only_public_attribute =  None
    >>> print(len(dir_(Test())) > 1) # Long list, try it yourself...
    True

    If the option is set to `False`, only the `public` attributes and methods
    (which do need begin with `_`) are returned:

    >>> pub.options.dirverbose = False
    >>> print(dir_(Test())) # Short list with one single entry...
    ['only_public_attribute']

    If none of those does exists, |dir_| returns a list with a single string
    containing a single empty space (which seems to work better for most
    IDEs than returning an emtpy list):

    >>> del Test.only_public_attribute
    >>> print(dir_(Test()))
    [' ']
    """
    names = set()
    for thing in itertools.chain(inspect.getmro(type(self)), (self,)):
        for key in vars(thing).keys():
            if hydpy.pub.options.dirverbose or not key.startswith("_"):
                names.add(key)
    if names:
        return list(names)
    return [" "]


def classname(self: object) -> str:
    """Return the class name of the given instance object or class.

    >>> from hydpy import classname
    >>> from hydpy import pub
    >>> classname(float)
    'float'
    >>> classname(pub.options)
    'Options'
    """
    if inspect.isclass(self):
        return self.__name__  # type: ignore [attr-defined, no-any-return]
    return type(self).__name__


def value_of_type(value: object) -> str:
    """Returns a string containing both the informal string and the type
    of the given value.

    This function is intended to simplifying writing HydPy exceptions,
    which frequently contain the following phrase:

    >>> from hydpy.core.objecttools import value_of_type
    >>> value_of_type(999)
    'value `999` of type `int`'
    """
    return f"value `{value}` of type `{classname(value)}`"


def modulename(self: object) -> str:
    """Return the module name of the given instance object.

    >>> from hydpy.core.objecttools import modulename
    >>> from hydpy import pub
    >>> print(modulename(pub.options))
    optiontools
    """
    return self.__module__.split(".")[-1]


def _search_device(
    self: object,
) -> Optional[Union["devicetools.Node", "devicetools.Element"]]:
    from hydpy.core import devicetools  # pylint: disable=import-outside-toplevel

    while True:
        if self is None:
            return None
        device = vars(self).get("node", vars(self).get("element"))
        if isinstance(device, (devicetools.Node, devicetools.Element)):
            return device
        for test in ("model", "seqs", "pars", "subvars"):
            master = vars(self).get(test)
            if master is not None:
                self = master
                break
        else:
            return None


def devicename(self: object) -> str:
    """Try to return the name of the (indirect) master |Node| or
    |Element| instance, if not possible return `?`.

    >>> from hydpy import prepare_model
    >>> model = prepare_model("hland_v1")
    >>> from hydpy.core.objecttools import devicename
    >>> devicename(model)
    '?'

    >>> from hydpy import Element
    >>> e1 = Element("e1", outlets="n1")
    >>> e1.model = model
    >>> devicename(e1)
    'e1'
    >>> devicename(model)
    'e1'
    """
    device = _search_device(self)
    if device is None:
        return "?"
    return device.name


def _devicephrase(self: object, objname: Optional[str] = None) -> str:
    name_ = getattr(self, "name", type(self).__name__.lower())
    device = _search_device(self)
    if device and objname:
        return f"`{name_}` of {objname} `{device.name}`"
    if objname:
        return f"`{name_}` of {objname} `?`"
    if device:
        return f"`{name_}` of {type(device).__name__.lower()} `{device.name}`"
    return f"`{name_}`"


def elementphrase(self: object) -> str:
    """Return the phrase used in exception messages to indicate
    which |Element| is affected.

    >>> class Model:
    ...     pass
    >>> model = Model()
    >>> from hydpy.core.objecttools import elementphrase
    >>> elementphrase(model)
    '`model` of element `?`'

    >>> model.name = "test"
    >>> elementphrase(model)
    '`test` of element `?`'

    >>> from hydpy import Element
    >>> model.element = Element("e1")
    >>> elementphrase(model)
    '`test` of element `e1`'
    """
    return _devicephrase(self, "element")


def nodephrase(self: object) -> str:
    """Return the phrase used in exception messages to indicate
    which |Node| is affected.

    >>> from hydpy.core.sequencetools import Sequences
    >>> sequences = Sequences(None)
    >>> from hydpy.core.objecttools import nodephrase
    >>> nodephrase(sequences)
    '`sequences` of node `?`'

    >>> sequences.name = "test"
    >>> nodephrase(sequences)
    '`test` of node `?`'

    >>> from hydpy import Node
    >>> n1 = Node("n1")
    >>> nodephrase(n1.sequences.sim)
    '`sim` of node `n1`'
    """
    return _devicephrase(self, "node")


def devicephrase(self: object) -> str:
    """Try to return the phrase used in exception messages to
    indicate which |Element| or which |Node| is affected.
    If not possible, return just the name of the given object.

    >>> class Model:
    ...     name = "test"
    >>> model = Model()
    >>> from hydpy.core.objecttools import devicephrase
    >>> devicephrase(model)
    '`test`'

    >>> from hydpy import Element
    >>> model.element = Element("e1")
    >>> devicephrase(model)
    '`test` of element `e1`'

    >>> from hydpy import Node
    >>> n1 = Node("n1")
    >>> devicephrase(n1.sequences.sim)
    '`sim` of node `n1`'
    """
    return _devicephrase(self)


def valid_variable_identifier(string: str) -> None:
    """Raises an |ValueError| if the given name is not a valid Python
    identifier.

    For example, the string `test_1` (with underscore) is valid...

    >>> from hydpy.core.objecttools import valid_variable_identifier
    >>> valid_variable_identifier("test_1")

    ...but the string `test 1` (with white space) is not:

    >>> valid_variable_identifier("test 1")
    Traceback (most recent call last):
    ...
    ValueError: The given name string `test 1` does not define a valid \
variable identifier.  Valid identifiers do not contain characters like \
`-` or empty spaces, do not start with numbers, cannot be mistaken with \
Python built-ins like `for`...)

    Also, names of Python built ins are not allowed:

    >>> valid_variable_identifier("print")   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: The given name string `print` does not define...
    """
    if string in _builtinnames or not string.isidentifier():
        raise ValueError(
            f"The given name string `{string}` does not define a valid "
            f"variable identifier.  Valid identifiers do not contain "
            f"characters like `-` or empty spaces, do not start with "
            f"numbers, cannot be mistaken with Python built-ins like "
            f"`for`...)"
        )


def augment_excmessage(
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
) -> NoReturn:
    """Augment an exception message with additional information while keeping
    the original traceback.

    You can prefix and/or suffix text.  If you prefix something (which happens
    much more often in the HydPy framework), the sub-clause ', the following
    error occurred:' is automatically included:

    >>> from hydpy.core import objecttools
    >>> import textwrap
    >>> try:
    ...     1 + "1"
    ... except BaseException:
    ...     prefix = "While showing how prefixing works"
    ...     suffix = "(This is a final remark.)"
    ...     objecttools.augment_excmessage(prefix, suffix)
    Traceback (most recent call last):
    ...
    TypeError: While showing how prefixing works, the following error \
occurred: unsupported operand type(s) for +: 'int' and 'str' \
(This is a final remark.)

    Some exceptions derived by site-packages do not support exception
    chaining due to requiring multiple initialisation arguments.
    In such cases, |augment_excmessage| generates an exception with the
    same name on the fly and raises it afterwards:

    >>> class WrongError(BaseException):
    ...     def __init__(self, arg1, arg2):
    ...         pass
    >>> try:
    ...     raise WrongError("info 1", "info 2")
    ... except BaseException:
    ...     objecttools.augment_excmessage("While showing how prefixing works")
    Traceback (most recent call last):
    ...
    hydpy.core.objecttools.WrongError: While showing how prefixing works, \
the following error occurred: ('info 1', 'info 2')

    Never use function |augment_excmessage| outside except clauses:

    >>> objecttools.augment_excmessage("While trying to do something")
    Traceback (most recent call last):
    ...
    RuntimeError: No exception available.  (Call function `augment_excmessage` \
only inside except clauses.)
    """
    exc_old = sys.exc_info()[1]
    if exc_old is None:
        raise RuntimeError(
            "No exception available.  (Call function `augment_excmessage` "
            "only inside except clauses.)"
        )
    message = str(exc_old)
    if prefix is not None:
        message = f"{prefix}, the following error occurred: {message}"
    if suffix is not None:
        message = f"{message} {suffix}"
    try:
        exc_new = type(exc_old)(message)
    except BaseException:
        exc_name = str(type(exc_old)).split("'")[1].split(".")[-1]
        exc_type = type(exc_name, (BaseException,), {})
        exc_type.__module__ = exc_old.__module__
        raise exc_type(message) from exc_old
    raise exc_new from exc_old


F = TypeVar("F", bound=Callable[..., Any])


def decorator(wrapper: Callable[..., Any]) -> Callable[[F], F]:
    """Function |decorator| adds type hints to function `decorator` of the
    site-package `wrapt` without changing its functionality."""
    return cast(Callable[[F], F], wrapt.decorator(wrapper))


def excmessage_decorator(description_: str) -> Callable[[F], F]:
    """Wrap a function with |augment_excmessage|.

    Function |excmessage_decorator| is a means to apply function
    |augment_excmessage| more efficiently.  Suppose you would apply
    function |augment_excmessage| in a function that adds and returns
    to numbers:

    >>> from  hydpy.core import objecttools
    >>> def add(x, y):
    ...     try:
    ...         return x + y
    ...     except BaseException:
    ...         objecttools.augment_excmessage("While trying to add `x` and `y`")

    This works as excepted...

    >>> add(1, 2)
    3
    >>> add(1, [])
    Traceback (most recent call last):
    ...
    TypeError: While trying to add `x` and `y`, the following error \
occurred: unsupported operand type(s) for +: 'int' and 'list'

    ...but can be achieved with much less code using |excmessage_decorator|:

    >>> @objecttools.excmessage_decorator("add `x` and `y`")
    ... def add(x, y):
    ...     return x+y

    >>> add(1, 2)
    3

    >>> add(1, [])
    Traceback (most recent call last):
    ...
    TypeError: While trying to add `x` and `y`, the following error \
occurred: unsupported operand type(s) for +: 'int' and 'list'

    Additionally, exception messages related to wrong function calls
    are now also augmented:

    >>> add(1)
    Traceback (most recent call last):
    ...
    TypeError: While trying to add `x` and `y`, the following error \
occurred: add() missing 1 required positional argument: 'y'

    |excmessage_decorator| evaluates the given string like an f-string,
    allowing to mention the argument values of the called function and
    to make use of all string modification functions provided by modules
    |objecttools|:

    >>> @objecttools.excmessage_decorator(
    ...     "add `x` ({repr_(x, 2)}) and `y` ({repr_(y, 2)})")
    ... def add(x, y):
    ...     return x+y

    >>> add(1.1111, "wrong")
    Traceback (most recent call last):
    ...
    TypeError: While trying to add `x` (1.11) and `y` (wrong), the following \
error occurred: unsupported operand type(s) for +: 'float' and 'str'
    >>> add(1)
    Traceback (most recent call last):
    ...
    TypeError: While trying to add `x` (1) and `y` (?), the following error \
occurred: add() missing 1 required positional argument: 'y'
    >>> add(y=1)
    Traceback (most recent call last):
    ...
    TypeError: While trying to add `x` (?) and `y` (1), the following error \
occurred: add() missing 1 required positional argument: 'x'

    Apply |excmessage_decorator| on methods also works fine:

    >>> class Adder:
    ...     def __init__(self):
    ...         self.value = 0
    ...     @objecttools.excmessage_decorator(
    ...         "add an instance of class `{classname(self)}` with value "
    ...         "`{repr_(other, 2)}` of type `{classname(other)}`")
    ...     def __iadd__(self, other):
    ...         self.value += other
    ...         return self

    >>> adder = Adder()
    >>> adder += 1
    >>> adder.value
    1
    >>> adder += "wrong"
    Traceback (most recent call last):
    ...
    TypeError: While trying to add an instance of class `Adder` with value \
`wrong` of type `str`, the following error occurred: unsupported operand \
type(s) for +=: 'int' and 'str'

    It is made sure that no information of the decorated function is lost:

    >>> add.__name__
    'add'
    """

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):  # type: ignore[no-untyped-def]
        """Apply |augment_excmessage| when the wrapped function fails."""
        # pylint: disable=unused-argument
        try:
            return wrapped(*args, **kwargs)
        except BaseException:
            info = kwargs.copy()
            info["self"] = instance
            argnames = inspect.getfullargspec(wrapped).args
            if argnames and (argnames[0] == "self"):
                argnames = argnames[1:]
            for argname, arg in zip(argnames, args):
                info[argname] = arg
            for argname in argnames:
                if argname not in info:
                    info[argname] = "?"
            message = eval(f"f'While trying to {description_}'", globals(), info)
            augment_excmessage(message)

    return cast(Callable[[F], F], wrapper)


class ResetAttrFuncs:
    """Reset all attribute related methods of the given class temporarily.

    The "related methods" are defined in class attribute
    |ResetAttrFuncs.funcnames|.

    There are (at least) two use cases for  class |ResetAttrFuncs|,
    initialization and copying, which are described below.

    In HydPy, some classes define a `__setattr__` method which raises
    exceptions when one tries to set "improper" instance attributes.
    The problem is, that such customized `setattr` methods often prevent
    from defining instance attributes within `__init__` methods in the
    usual manner.  Working on instance dictionaries instead can confuse
    some automatic tools (e.g. pylint).  Class |ResetAttrFuncs|
    implements a trick to circumvent this problem.

    To show how |ResetAttrFuncs| works, we first define a class
    with a `__setattr__` method that does not allow to set any attribute:

    >>> class Test:
    ...     def __setattr__(self, name, value):
    ...         raise AttributeError
    >>> test = Test()
    >>> test.var1 = 1
    Traceback (most recent call last):
    ...
    AttributeError

    Assigning this class to |ResetAttrFuncs| allows for setting
    attributes to all its instances inside a `with` block in the
    usual manner:

    >>> from hydpy.core.objecttools import ResetAttrFuncs
    >>> with ResetAttrFuncs(test):
    ...     test.var1 = 1
    >>> test.var1
    1

    After the end of the `with` block, the custom `__setattr__` method
    of the test class works again and prevents from setting attributes:

    >>> test.var2 = 2
    Traceback (most recent call last):
    ...
    AttributeError

    The second use case is related to method `__getattr__` and copying.
    The following test class stores its attributes (for whatever reasons)
    in a special dictionary called "dic" (note that how
    |ResetAttrFuncs| is used in the `__init__` method):

    >>> class Test:
    ...     def __init__(self):
    ...         with ResetAttrFuncs(self):
    ...             self.dic = {}
    ...     def __setattr__(self, name, value):
    ...         self.dic[name] = value
    ...     def __getattr__(self, name):
    ...         try:
    ...             return self.dic[name]
    ...         except KeyError:
    ...             raise AttributeError

    Principally, this simple implementation does its job but its
    instances are not easily copyable under all Python versions:

    >>> test = Test()
    >>> test.var1 = 1
    >>> test.var1
    1
    >>> import copy
    >>> copy.deepcopy(test)   # doctest: +SKIP
    Traceback (most recent call last):
    ...
    RecursionError: maximum recursion depth exceeded ...

    |ResetAttrFuncs| can be used to implement specialized
    `__copy__` and `__deepcopy__` methods, which rely on the temporary
    disabling of `__getattr__`.  For simple cases, one can import the
    predefined functions |copy_| and |deepcopy_|:

    >>> from hydpy.core.objecttools import copy_, deepcopy_
    >>> Test.__copy__ = copy_
    >>> test2 = copy.copy(test)
    >>> test2.var1
    1
    >>> Test.__deepcopy__ = deepcopy_
    >>> test3 = copy.deepcopy(test)
    >>> test3.var1
    1

    Note that an infinite recursion is avoided by also disabling methods
    `__copy__` and `__deepcopy__` themselves.

    """

    __slots__ = ("cls", "name2func")
    funcnames = (
        "__getattr__",
        "__setattr__",
        "__delattr__",
        "__copy__",
        "__deepcopy__",
    )

    def __init__(self, obj: object) -> None:
        self.cls = type(obj)
        self.name2func = {}
        for name_ in self.funcnames:
            if hasattr(self.cls, name_):
                self.name2func[name_] = self.cls.__dict__.get(name_)

    def __enter__(self) -> "ResetAttrFuncs":
        for name_ in self.name2func:
            if name_ in ("__setattr__", "__delattr__"):
                setattr(self.cls, name_, getattr(object, name_))
            elif name_ == "__getattr__":
                setattr(self.cls, name_, object.__getattribute__)
            else:
                setattr(self.cls, name_, None)
        return self

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: BaseException,
        traceback_: types.TracebackType,
    ) -> None:
        for name_, func in self.name2func.items():
            if func:
                setattr(self.cls, name_, func)
            else:
                delattr(self.cls, name_)


def copy_(self: T) -> T:
    """Copy function for classes with modified attribute functions.

    See the documentation on class |ResetAttrFuncs| for further information.
    """
    with ResetAttrFuncs(self):
        return copy.copy(self)


def deepcopy_(self: T, memo: Optional[Dict[int, object]]) -> T:
    """Deepcopy function for classes with modified attribute functions.

    See the documentation on class |ResetAttrFuncs| for further information.
    """
    with ResetAttrFuncs(self):
        return copy.deepcopy(self, memo)  # type: ignore [return-value]  # ???


class _PreserveStrings:
    """Helper class for |_Repr_|."""

    newvalue: bool
    oldvalue: bool

    def __init__(self, preserve_strings: bool) -> None:
        self.newvalue = preserve_strings
        self.oldvalue = getattr(repr_, "_preserve_strings")

    def __enter__(self) -> None:
        setattr(repr_, "_preserve_strings", self.newvalue)

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: BaseException,
        traceback: types.TracebackType,
    ) -> None:
        setattr(repr_, "_preserve_strings", self.oldvalue)


class _Repr:
    """Modifies |repr| for strings and floats, mainly for supporting
    clean float and path representations that are compatible with |doctest|."""

    def __init__(self) -> None:
        self._preserve_strings = False

    def __call__(
        self,
        value: object,
        decimals: Optional[int] = None,
    ) -> str:
        if decimals is None:
            decimals = hydpy.pub.options.reprdigits
        if isinstance(value, str):
            string = value.replace("\\", "/")
            if self._preserve_strings:
                return f'"{string}"'
            return string
        if isinstance(value, numbers.Real) and (
            not isinstance(value, numbers.Integral)
        ):
            value = float(value)
            if decimals > -1:
                string = "{0:.{1}f}".format(value, decimals)
                string = string.rstrip("0")
                if string.endswith("."):
                    string += "0"
                if string == "-0.0":
                    return "0.0"
                return string
        return repr(value)

    @staticmethod
    def preserve_strings(preserve_strings: bool) -> _PreserveStrings:
        """Change the `preserve_string` option inside a with block."""
        return _PreserveStrings(preserve_strings)


repr_ = _Repr()
r"""Modifies |repr| for strings and floats, mainly for supporting
clean float and path representations that are compatible with |doctest|.

Use the already available instance `repr_` instead of initialising
a new |Repr_| object.

When value is a string, it is returned without any modification,
except that the path separator "\" (Windows) is replaced with "/"
(Linux):

>>> from hydpy.core.objecttools import repr_

>>> print(r"directory\file")
directory\file
>>> print(repr(r"directory\file"))
'directory\\file'
>>> print(repr_(r"directory\file"))
directory/file

You can change this behaviour of function object |repr|,
when necessary:

>>> with repr_.preserve_strings(True):
...     print(repr_(r"directory\file"))
"directory/file"

Behind the with block, |repr_| works as before
(even in case of an error):

>>> print(repr_(r"directory\file"))
directory/file

When value is a float, the result depends on how the option
|Options.reprdigits| is set.  Without defining a special value,
|repr| defines the number of digits in the usual, system dependent
manner:

>>> from hydpy import pub
>>> del pub.options.reprdigits
>>> repr(1./3.) == repr_(1./3.)
True

Through setting |Options.reprdigits| to a positive integer value,
one defines the maximum number of decimal places, which allows for
doctesting across different systems and Python versions:

>>> pub.options.reprdigits = 6
>>> repr_(1./3.)
'0.333333'
>>> repr_(2./3.)
'0.666667'
>>> repr_(1./2.)
'0.5'

Changing the number of decimal places can be done via a with block:

>>> with pub.options.reprdigits(3):
...     print(repr_(1./3.))
0.333

Such a change is only temporary (even in case of an error):
>>> repr_(1./3.)
'0.333333'

|repr| can also be applied on numpy's float types:

>>> import numpy
>>> repr_(numpy.float(1./3.))
'0.333333'
>>> repr_(numpy.float64(1./3.))
'0.333333'
>>> repr_(numpy.float32(1./3.))
'0.333333'
>>> repr_(numpy.float16(1./3.))
'0.333252'

Note that the deviation from the `true` result in the last example is due
to the low precision of |numpy.float16|.

On all types not mentioned above, the usual |repr| function is
applied, e.g.:

>>> repr([1, 2, 3])
'[1, 2, 3]'
>>> repr_([1, 2, 3])
'[1, 2, 3]'
"""


def repr_values(values: Iterable[object]) -> str:
    """Return comma separated representations of the given values using
    function |repr_|.

    >>> from hydpy.core.objecttools import repr_values
    >>> repr_values([1.0/1.0, 1.0/2.0, 1.0/3.0])
    '1.0, 0.5, 0.333333'

    Note that the returned string is not wrapped.
    """
    return ", ".join(repr_(value) for value in values)


def repr_numbers(values: ReprArg) -> str:
    """Return comma separated representations of the given numbers using
    function |repr_|.

    Currently, function |repr_numbers| can handle scalar values,
    1-dimensional vectors, and 2-dimensional matrices:

    >>> from hydpy.core.objecttools import repr_numbers
    >>> repr_numbers(1.0/3.0)
    '0.333333'
    >>> repr_numbers([1.0/1.0, 1.0/2.0, 1.0/3.0])
    '1.0, 0.5, 0.333333'
    >>> repr_numbers([[1.0/1.0, 1.0/2.0, 1.0/3.0], [1.0/4.0, 1.0/5.0, 1.0/6.0]])
    '1.0, 0.5, 0.333333; 0.25, 0.2, 0.166667'

    Note that the returned string is not wrapped.
    """
    if isinstance(values, numbers.Number):
        return repr_(values)
    result = []
    ndim = 1
    for value in values:
        if isinstance(value, numbers.Number):
            result.append(repr_(value))
        else:
            result.append(", ".join(repr_(v) for v in value))
            ndim = 2
    if ndim == 1:
        return ", ".join(result)
    return "; ".join(result)


def print_values(values: Iterable[object], width: int = 70) -> None:
    """Print the given values in multiple lines with a certain maximum width.

    By default, each line contains at most 70 characters:

    >>> from hydpy import print_values
    >>> print_values(range(21))
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
    20

    You can change this default behaviour by passing an alternative
    number of characters:

    >>> print_values(range(21), width=30)
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    10, 11, 12, 13, 14, 15, 16,
    17, 18, 19, 20
    """
    for line in textwrap.wrap(
        text=repr_values(values),
        width=width,
        break_long_words=False,
    ):
        print(line)


def repr_tuple(values: Iterable[object]) -> str:
    """Return a tuple representation of the given values using function
    |repr|.

    >>> from hydpy.core.objecttools import repr_tuple
    >>> repr_tuple([1./1., 1./2., 1./3.])
    '(1.0, 0.5, 0.333333)'

    Note that the returned string is not wrapped.

    In the special case of an iterable with only one entry, the returned
    string is still a valid tuple:

    >>> repr_tuple([1.])
    '(1.0,)'
    """
    if len(list(values)) == 1:
        return f"({repr_values(values)},)"
    return f"({repr_values(values)})"


def repr_list(values: Iterable[object]) -> str:
    """Return a list representation of the given values using function
    |repr|.

    >>> from hydpy.core.objecttools import repr_list
    >>> repr_list([1./1., 1./2., 1./3.])
    '[1.0, 0.5, 0.333333]'

    Note that the returned string is not wrapped.
    """
    return f"[{repr_values(values)}]"


def assignrepr_value(value: object, prefix: str) -> str:
    """Return a prefixed string representation of the given value using
    function |repr|.

    Note that the argument has no effect. It is thought for increasing
    usage compatibility with functions like |assignrepr_list| only.

    >>> from hydpy.core.objecttools import assignrepr_value
    >>> print(assignrepr_value(1./3., "test = "))
    test = 0.333333
    """
    return prefix + repr_(value)


def assignrepr_values(
    values: Sequence[object],
    prefix: str,
    width: Optional[int] = None,
    _fakeend: int = 0,
) -> str:
    """Return a prefixed, wrapped and properly aligned string representation
    of the given values using function |repr|.

    >>> from hydpy.core.objecttools import assignrepr_values
    >>> print(assignrepr_values(range(1, 13), "test(", 20) + ")")
    test(1, 2, 3, 4, 5,
         6, 7, 8, 9, 10,
         11, 12)

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_values(range(1, 13), "test(") + ")")
    test(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)


    To circumvent defining too long string representations, make use of the
    ellipsis option:

    >>> from hydpy import pub
    >>> with pub.options.ellipsis(1):
    ...     print(assignrepr_values(range(1, 13), "test(", 20) + ")")
    test(1, ...,12)

    >>> with pub.options.ellipsis(5):
    ...     print(assignrepr_values(range(1, 13), "test(", 20) + ")")
    test(1, 2, 3, 4, 5,
         ...,8, 9, 10,
         11, 12)

    >>> with pub.options.ellipsis(6):
    ...     print(assignrepr_values(range(1, 13), "test(", 20) + ")")
    test(1, 2, 3, 4, 5,
         6, 7, 8, 9, 10,
         11, 12)
    """
    ellipsis_ = int(hydpy.pub.options.ellipsis)
    if (ellipsis_ > 0) and (len(values) > 2 * ellipsis_):
        string = (
            f"{repr_values(values[:ellipsis_])}"
            f", ...,"
            f"{repr_values(values[-ellipsis_:])}"
        )
    else:
        string = repr_values(values)
    blanks = " " * len(prefix)
    if width is None:
        wrapped = [string]
        _fakeend = 0
    else:
        width -= len(prefix)
        wrapped = textwrap.wrap(
            text=string + "_" * _fakeend,
            width=width,
            break_long_words=False,
        )
    if not wrapped:
        wrapped = [""]
    lines = []
    for (idx, line) in enumerate(wrapped):
        if idx == 0:
            lines.append(f"{prefix}{line}")
        else:
            lines.append(f"{blanks}{line}")
    string = "\n".join(lines)
    return string[: len(string) - _fakeend]


class _AssignReprBracketed:
    """ "Double Singleton class", see the documentation on
    |assignrepr_tuple| and |assignrepr_list|."""

    class _AlwaysBracketed:

        _new_value: bool
        _old_value: bool

        def __init__(self, value: bool) -> None:
            self._new_value = value
            self._old_value = _AssignReprBracketed._always_bracketed

        def __enter__(self) -> None:
            _AssignReprBracketed._always_bracketed = self._new_value

        def __exit__(
            self,
            exception_type: Type[BaseException],
            exception_value: BaseException,
            traceback: types.TracebackType,
        ) -> None:
            _AssignReprBracketed._always_bracketed = self._old_value

    _always_bracketed: bool = True
    _brackets: Literal["()", "[]", "{}"]

    def __init__(self, brackets: Literal["()", "[]", "{}"]) -> None:
        self._brackets = brackets

    def __call__(
        self,
        values: Sequence[object],
        prefix: str,
        width: Optional[int] = None,
    ) -> str:
        nmb_values = len(values)
        if (nmb_values == 1) and not self._always_bracketed:
            return assignrepr_value(values[0], prefix)
        if nmb_values:
            string = (
                assignrepr_values(
                    values=values,
                    prefix=prefix + self._brackets[0],
                    width=width,
                    _fakeend=1,
                )
                + self._brackets[1]
            )
            if (len(values) == 1) and (self._brackets[1] == ")"):
                return string[:-1] + ",)"
            return string
        return prefix + self._brackets

    @classmethod
    def always_bracketed(cls, always_bracketed: bool) -> _AlwaysBracketed:
        """Change the `always_bracketed` option inside a with block."""
        return cls._AlwaysBracketed(always_bracketed)


assignrepr_tuple = _AssignReprBracketed("()")
"""Return a prefixed, wrapped and properly aligned tuple string
representation of the given values using function |repr|.

>>> from hydpy.core.objecttools import assignrepr_tuple
>>> print(assignrepr_tuple(range(10), "test = ", 22))
test = (0, 1, 2, 3, 4,
        5, 6, 7, 8, 9)

If no width is given, no wrapping is performed:

>>> print(assignrepr_tuple(range(10), "test = "))
test = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

Functions |assignrepr_tuple| works also on empty iterables and
those which possess only one entry:

>>> print(assignrepr_tuple([], "test = "))
test = ()
>>> print(assignrepr_tuple([10], "test = "))
test = (10,)

Optionally, bracketing single values can be prevented:

>>> with assignrepr_tuple.always_bracketed(False):
...     print(assignrepr_tuple([], "test = "))
...     print(assignrepr_tuple([10], "test = "))
...     print(assignrepr_tuple([10, 10], "test = "))
test = ()
test = 10
test = (10, 10)

Behind the with block, |assignrepr_tuple| works as before
(even in case of an error):

>>> print(assignrepr_tuple([10], "test = "))
test = (10,)
"""


assignrepr_list = _AssignReprBracketed("[]")
"""Return a prefixed, wrapped and properly aligned list string
representation of the given values using function |repr|.

>>> from hydpy.core.objecttools import assignrepr_list
>>> print(assignrepr_list(range(10), "test = ", 22))
test = [0, 1, 2, 3, 4,
        5, 6, 7, 8, 9]

If no width is given, no wrapping is performed:

>>> print(assignrepr_list(range(10), "test = "))
test = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

Functions |assignrepr_list| works also on empty iterables:

>>> print(assignrepr_list((), "test = "))
test = []

Optionally, bracketing single values can be prevented:

>>> with assignrepr_list.always_bracketed(False):
...     print(assignrepr_list([], "test = "))
...     print(assignrepr_list([10], "test = "))
...     print(assignrepr_list([10, 10], "test = "))
test = []
test = 10
test = [10, 10]

Behind the with block, |assignrepr_list| works as before
(even in case of an error):

>>> print(assignrepr_list([10], "test = "))
test = [10,]
"""


def assignrepr_values2(
    values: Iterable[Iterable[object]],
    prefix: str,
) -> str:
    """Return a prefixed and properly aligned string representation
    of the given 2-dimensional value matrix using function |repr|.

    >>> from hydpy.core.objecttools import assignrepr_values2
    >>> import numpy
    >>> print(assignrepr_values2(numpy.eye(3), "test(") + ")")
    test(1.0, 0.0, 0.0,
         0.0, 1.0, 0.0,
         0.0, 0.0, 1.0)

    Functions |assignrepr_values2| works also on empty iterables:

    >>> print(assignrepr_values2([[]], "test(") + ")")
    test()
    """
    lines = []
    blanks = " " * len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(f"{prefix}{repr_values(subvalues)},")
        else:
            lines.append(f"{blanks}{repr_values(subvalues)},")
    lines[-1] = lines[-1][:-1]
    return "\n".join(lines)


def _assignrepr_bracketed2(
    assignrepr_bracketed1: _AssignReprBracketed,
    values: Sequence[Sequence[object]],
    prefix: str,
    width: Optional[int] = None,
) -> str:
    """Return a prefixed, wrapped and properly aligned bracketed string
    representation of the given 2-dimensional value matrix using function
    |repr|."""
    brackets = getattr(assignrepr_bracketed1, "_brackets")
    prefix += brackets[0]
    lines = []
    blanks = " " * len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(assignrepr_bracketed1(subvalues, prefix, width))
        else:
            lines.append(assignrepr_bracketed1(subvalues, blanks, width))
        lines[-1] += ","
    if (len(values) > 1) or (brackets != "()"):
        lines[-1] = lines[-1][:-1]
    lines[-1] += brackets[1]
    return "\n".join(lines)


def assignrepr_tuple2(
    values: Sequence[Sequence[object]],
    prefix: str,
    width: Optional[int] = None,
) -> str:
    """Return a prefixed, wrapped and properly aligned tuple string
    representation of the given 2-dimensional value matrix using function
    |repr|.

    >>> from hydpy.core.objecttools import assignrepr_tuple2
    >>> import numpy
    >>> print(assignrepr_tuple2(numpy.eye(3), "test = ", 18))
    test = ((1.0, 0.0,
             0.0),
            (0.0, 1.0,
             0.0),
            (0.0, 0.0,
             1.0))

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_tuple2(numpy.eye(3), "test = "))
    test = ((1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0))

    Functions |assignrepr_tuple2| works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_tuple2([[]], "test = "))
    test = ((),)
    >>> print(assignrepr_tuple2([[], [1]], "test = "))
    test = ((),
            (1,))
    """
    return _assignrepr_bracketed2(assignrepr_tuple, values, prefix, width)


def assignrepr_list2(
    values: Sequence[Sequence[object]],
    prefix: str,
    width: Optional[int] = None,
) -> str:
    """Return a prefixed, wrapped and properly aligned list string
    representation of the given 2-dimensional value matrix using function
    |repr|.

    >>> from hydpy.core.objecttools import assignrepr_list2
    >>> import numpy
    >>> print(assignrepr_list2(numpy.eye(3), "test = ", 18))
    test = [[1.0, 0.0,
             0.0],
            [0.0, 1.0,
             0.0],
            [0.0, 0.0,
             1.0]]

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_list2(numpy.eye(3), "test = "))
    test = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]

    Functions |assignrepr_list2| works also on empty iterables:

    >>> print(assignrepr_list2([[]], "test = "))
    test = [[]]
    >>> print(assignrepr_list2([[], [1]], "test = "))
    test = [[],
            [1]]
    """
    return _assignrepr_bracketed2(assignrepr_list, values, prefix, width)


def _assignrepr_bracketed3(
    assignrepr_bracketed1: _AssignReprBracketed,
    values: Sequence[Sequence[Sequence[object]]],
    prefix: str,
    width: Optional[int] = None,
) -> str:
    """Return a prefixed, wrapped and properly aligned bracketed string
    representation of the given 3-dimensional value matrix using function
    |repr|."""
    brackets = getattr(assignrepr_bracketed1, "_brackets")
    prefix += brackets[0]
    lines = []
    blanks = " " * len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(
                _assignrepr_bracketed2(assignrepr_bracketed1, subvalues, prefix, width)
            )
        else:
            lines.append(
                _assignrepr_bracketed2(assignrepr_bracketed1, subvalues, blanks, width)
            )
        lines[-1] += ","
    if (len(values) > 1) or (brackets != "()"):
        lines[-1] = lines[-1][:-1]
    lines[-1] += brackets[1]
    return "\n".join(lines)


def assignrepr_tuple3(
    values: Sequence[Sequence[Sequence[object]]],
    prefix: str,
    width: Optional[int] = None,
) -> str:
    """Return a prefixed, wrapped and properly aligned tuple string
    representation of the given 3-dimensional value matrix using function
    |repr|.

    >>> from hydpy.core.objecttools import assignrepr_tuple3
    >>> import numpy
    >>> values = [numpy.eye(3), numpy.ones((3, 3))]
    >>> print(assignrepr_tuple3(values, "test = ", 18))
    test = (((1.0,
              0.0,
              0.0),
             (0.0,
              1.0,
              0.0),
             (0.0,
              0.0,
              1.0)),
            ((1.0,
              1.0,
              1.0),
             (1.0,
              1.0,
              1.0),
             (1.0,
              1.0,
              1.0)))

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_tuple3(values, "test = "))
    test = (((1.0, 0.0, 0.0),
             (0.0, 1.0, 0.0),
             (0.0, 0.0, 1.0)),
            ((1.0, 1.0, 1.0),
             (1.0, 1.0, 1.0),
             (1.0, 1.0, 1.0)))

    Functions |assignrepr_tuple3| works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_tuple3([[[]]], "test = "))
    test = (((),),)
    >>> print(assignrepr_tuple3([[[], [1]]], "test = "))
    test = (((),
             (1,)),)
    """
    return _assignrepr_bracketed3(assignrepr_tuple, values, prefix, width)


def assignrepr_list3(
    values: Sequence[Sequence[Sequence[object]]],
    prefix: str,
    width: Optional[int] = None,
) -> str:
    """Return a prefixed, wrapped and properly aligned list string
    representation of the given 3-dimensional value matrix using function
    |repr|.

    >>> from hydpy.core.objecttools import assignrepr_list3
    >>> import numpy
    >>> values = [numpy.eye(3), numpy.ones((3, 3))]
    >>> print(assignrepr_list3(values, "test = ", 18))
    test = [[[1.0,
              0.0,
              0.0],
             [0.0,
              1.0,
              0.0],
             [0.0,
              0.0,
              1.0]],
            [[1.0,
              1.0,
              1.0],
             [1.0,
              1.0,
              1.0],
             [1.0,
              1.0,
              1.0]]]

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_list3(values, "test = "))
    test = [[[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [0.0, 0.0, 1.0]],
            [[1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0]]]

    Functions |assignrepr_list3| works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_list3([[[]]], "test = "))
    test = [[[]]]
    >>> print(assignrepr_list3([[[], [1]]], "test = "))
    test = [[[],
             [1]]]
    """
    return _assignrepr_bracketed3(assignrepr_list, values, prefix, width)


def flatten_repr(self: object) -> str:
    """Remove the newline characters from the string representation of the
    given object and return it.

    Complex string representations like the following one are convenient
    when working interactively, but cause line breaks when included in
    strings like in exception messages:

    >>> from hydpy import Node
    >>> node = Node("name", keywords="test")
    >>> node
    Node("name", variable="Q",
         keywords="test")

    Use function |flatten_repr| to prevent any line breaks:

    >>> from hydpy.core.objecttools import flatten_repr
    >>> print(flatten_repr(node))
    Node("name", variable="Q", keywords="test")

    When implementing a new class into the HydPy framework requiring a complex
    "|repr| string", either customize an simpler "|str| string" manually (as
    already done for the class |Node| or use function |flatten_repr|:

    >>> print(f"We print {node}!")
    We print name!
    >>> __str__ = Node.__str__
    >>> Node.__str__ = flatten_repr
    >>> print(f"We print {node}!")
    We print Node("name", variable="Q", keywords="test")!

    >>> Node.__str__ = __str__

    The named tuple subclass |lstream_v001.Characteristics| of application
    model |lstream_v001| uses function |flatten_repr| in the expected manner:

    >>> from hydpy.models.lstream_v001 import Characteristics
    >>> characteristics = Characteristics(
    ...     waterstage=1.0,
    ...     discharge=5.0,
    ...     derivative=0.1,
    ...     length_orig=3.0,
    ...     nmb_subsections=4,
    ...     length_adj=2.0,
    ... )

    >>> characteristics
    Characteristics(
        waterstage=1.0,
        discharge=5.0,
        derivative=0.1,
        length_orig=3.0,
        nmb_subsections=4,
        length_adj=2.0,
    )

    >>> print(characteristics)
    Characteristics(waterstage=1.0, discharge=5.0, derivative=0.1, \
length_orig=3.0, nmb_subsections=4, length_adj=2.0)
    """
    string = " ".join(string.strip() for string in repr(self).split("\n"))
    idx = string.find("(")
    string = f"{string[:idx]}({string[idx+1:].strip()}"
    if string.endswith(", )"):
        string = f"{string[:-3]})"
    return string


@overload
def round_(
    values: Union[object, Iterable[object]],
    decimals: Optional[int] = None,
    *,
    sep: str = " ",
    end: str = "\n",
    file_: Optional[TextIO] = None,
) -> None:
    ...


@overload
def round_(
    values: Union[object, Iterable[object]],
    decimals: Optional[int] = None,
    *,
    width: int = 0,
    lfill: Optional[str] = None,
    sep: str = " ",
    end: str = "\n",
    file_: Optional[TextIO] = None,
) -> None:
    ...


@overload
def round_(
    values: Union[object, Iterable[object]],
    decimals: Optional[int] = None,
    *,
    width: int = 0,
    rfill: Optional[str] = None,
    sep: str = " ",
    end: str = "\n",
    file_: Optional[TextIO] = None,
) -> None:
    ...


def round_(
    values: Union[object, Iterable[object]],
    decimals: Optional[int] = None,
    *,
    width: int = 0,
    lfill: Optional[str] = None,
    rfill: Optional[str] = None,
    sep: str = " ",
    end: str = "\n",
    file_: Optional[TextIO] = None,
) -> None:
    """Prints values with a maximum number of digits in doctests.

    See the documentation on function |repr| for more details.  And
    note thate the option keyword arguments are passed to the print function.

    Usually one would apply function |round_| on a single or a vector
    of numbers:

    >>> from hydpy import round_
    >>> round_(1./3., decimals=6)
    0.333333
    >>> round_((1./2., 1./3., 1./4.), decimals=4)
    0.5, 0.3333, 0.25

    Additionally, one can supply a `width` and a `rfill` argument:
    >>> round_(1.0, width=6, rfill="0")
    1.0000

    Alternatively, one can use the `lfill` arguments, which
    might e.g. be usefull for aligning different strings:

    >>> round_("test", width=6, lfill="_")
    __test

    Using both the `lfill` and the `rfill` argument raises an error:

    >>> round_(1.0, lfill="_", rfill="0")
    Traceback (most recent call last):
    ...
    ValueError: For function `round_` values are passed for both \
arguments `lfill` and `rfill`.  This is not allowed.
    """
    if decimals is None:
        decimals = hydpy.pub.options.reprdigits
    with hydpy.pub.options.reprdigits(decimals):
        if isinstance(values, typingtools.IterableNonString):
            string = repr_values(values)
        else:
            string = repr_(values)
        if (lfill is not None) and (rfill is not None):
            raise ValueError(
                "For function `round_` values are passed for both arguments "
                "`lfill` and `rfill`.  This is not allowed."
            )
        width = max(width, len(string))
        if lfill is not None:
            string = string.rjust(width, lfill)
        if rfill is not None:
            string = string.ljust(width, rfill)
        print(string, sep=sep, end=end, file=file_)


@overload
def extract(
    values: Union[Iterable[object], object],
    types_: Tuple[Type[T1]],
    skip: bool = False,
) -> Iterator[T1]:
    """Extract all objects of one defined type."""


@overload
def extract(
    values: Union[Iterable[object], object],
    types_: Tuple[Type[T1], Type[T2]],
    skip: bool = False,
) -> Iterator[Union[T1, T2]]:
    """Extract all objects of two defined types."""


@overload
def extract(
    values: Union[Iterable[object], object],
    types_: Tuple[Type[T1], Type[T2], Type[T3]],
    skip: bool = False,
) -> Iterator[Union[T1, T2, T3]]:
    """Extract all objects of three defined types."""


def extract(
    values: Union[Iterable[object], object],
    types_: Union[
        Tuple[Type[T1]],
        Tuple[Type[T1], Type[T2]],
        Tuple[Type[T1], Type[T2], Type[T3]],
    ],
    skip: bool = False,
) -> Iterator[Union[T1, T2, T3]]:
    """Return a generator that extracts certain objects from `values`.

    This function is thought for supporting the definition of functions
    with arguments, that can be objects of certain types or that can
    be iterables containing these objects.

    The following examples show that function |extract|
    basically implements a type specific flattening mechanism:

    >>> from hydpy.core.objecttools import extract
    >>> tuple(extract("str1", (str, int)))
    ('str1',)
    >>> tuple(extract(["str1", "str2"], (str, int)))
    ('str1', 'str2')
    >>> tuple(extract((["str1", "str2"], [1,]), (str, int)))
    ('str1', 'str2', 1)

    If an object is neither iterable nor of the required type, the
    following exception is raised:

    >>> tuple(extract("str1", (int,)))
    Traceback (most recent call last):
    ...
    TypeError: The given (sub)value `'str1'` is not an instance of \
the following classes: int.

    >>> tuple(extract((["str1", "str2"], [None, 1]), (str, int)))
    Traceback (most recent call last):
    ...
    TypeError: The given (sub)value `None` is not an instance of \
the following classes: str and int.

    Optionally, |None| values can be skipped:

    >>> tuple(extract(None, (str, int), True))
    ()
    >>> tuple(extract((["str1", "str2"], [None, 1]), (str, int), True))
    ('str1', 'str2', 1)
    """
    if isinstance(values, types_):
        yield values  # type: ignore[misc]  # see issue 4949
    elif skip and (values is None):
        return
    else:
        try:
            if isinstance(values, str) or not isinstance(values, Iterable):
                raise TypeError("temp")
            for value in values:
                for subvalue in extract(value, types_, skip):
                    yield subvalue
        except TypeError as exc:
            if exc.args[0].startswith("The given (sub)value"):
                raise exc
            enum = enumeration(types_, converter=lambda x: x.__name__)
            raise TypeError(
                f"The given (sub)value `{repr(values)}` is not an "
                f"instance of the following classes: {enum}."
            ) from None


def enumeration(
    values: Iterable[T],
    converter: Callable[[T], str] = str,
    default: str = "",
) -> str:
    """Return an enumeration string based on the given values.

    The following four examples show the standard output of function
    |enumeration|:

    >>> from hydpy.core.objecttools import enumeration
    >>> enumeration(("text", 3, []))
    'text, 3, and []'
    >>> enumeration(('text', 3))
    'text and 3'
    >>> enumeration(('text',))
    'text'
    >>> enumeration(())
    ''

    All given objects are converted to strings by function |str|, as shown
    by the first two examples.  This behaviour can be changed by another
    function expecting a single argument and returning a string:

    >>> from hydpy import classname
    >>> enumeration(("text", 3, []), converter=classname)
    'str, int, and list'

    You can define a default string that is returned in case an empty
    iterable is given:

    >>> enumeration((), default="nothing")
    'nothing'

    Functin |enumeration| respects option |Options.ellipsis|:

    >>> from hydpy import pub
    >>> with pub.options.ellipsis(3):
    ...     enumeration(range(10))
    '0, 1, 2, ..., 7, 8, and 9'
    """
    values_ = list(converter(value) for value in values)
    if not values_:
        return default
    if len(values_) == 1:
        return values_[0]
    if len(values_) == 2:
        return " and ".join(values_)
    ellipsis_ = int(hydpy.pub.options.ellipsis)
    if (ellipsis_ > 0) and (len(values_) > 2 * ellipsis_):
        values_ = values_[:ellipsis_] + ["..."] + values_[-ellipsis_:]
    return ", and ".join((", ".join(values_[:-1]), values_[-1]))


def description(self: object) -> str:
    """Returns the first "paragraph" of the docstring of the given object.

    Note that ugly things like multiple whitespaces and newline characters
    are removed:

    >>> from hydpy.core.objecttools import description, augment_excmessage
    >>> description(augment_excmessage)
    'Augment an exception message with additional information while keeping \
the original traceback.'

    In case the given object does not define a docstring, the following
    is returned:
    >>> description(type("Test", (), {}))
    'no description available'
    """
    doc = self.__doc__
    if doc is None or doc == "":
        return "no description available"
    return " ".join(doc.split("\n\n")[0].split())


@contextlib.contextmanager
def get_printtarget(file_: Union[TextIO, str, None]) -> Generator[TextIO, None, None]:
    """Get a suitable file object reading for writing text useable as the `file`
    argument of the standard |print| function.

    Function |get_printtarget| supports three types of arguments.  For |None|,
    it returns |sys.stdout|:

    >>> from hydpy.core.objecttools import get_printtarget
    >>> import sys
    >>> with get_printtarget(None) as printtarget:
    ...     print("printtarget = stdout", file=printtarget)
    printtarget = stdout

    If passes already opened file objects, flushing but not closing them:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     with open("testfile1.txt", "w") as testfile1:
    ...         with get_printtarget(testfile1) as printtarget:
    ...             print("printtarget = testfile1", file=printtarget, end="")
    >>> with TestIO():
    ...     with open("testfile1.txt", "r") as testfile1:
    ...         print(testfile1.read())
    printtarget = testfile1

    When receiving a file name, it creates a new file and closes it after leaving
    the `with` block:

    >>> with TestIO():
    ...     with get_printtarget("testfile2.txt") as printtarget:
    ...         print("printtarget = testfile2", file=printtarget, end="")
    >>> with TestIO():
    ...     with open("testfile2.txt", "r") as testfile2:
    ...         print(testfile2.read())
    printtarget = testfile2
    """
    if file_ is None:
        yield sys.stdout
    elif isinstance(file_, str):
        with open(file_, "w") as printobject:
            yield printobject
    else:
        yield file_
        file_.flush()


_black_filemode = black.FileMode()


def apply_black(
    name: str,
    *args: object,
    **kwargs: object,
) -> str:
    """Return a string representation of an instance of a class based on the given
     name, positional arguments and keyword arguments.

    .. _`black`: https://black.readthedocs.io/en/stable/
    .. _`PEP 8`: https://www.python.org/dev/peps/pep-0008/

    |apply_black| helps to define `__repr__` methods that agree with `PEP 8` by
    using the code formatter `black`_:

    >>> from hydpy.core.objecttools import apply_black
    >>> print(apply_black("Tester"))
    Tester()
    >>> print(apply_black("Tester", 1, "test"))
    Tester(1, "test")
    >>> print(apply_black("Tester", number=1, string="test"))
    Tester(number=1, string="test")
    >>> print(apply_black("Tester", 1, "test", number=2, \
string=f"a {10*'very '}long test"))
    Tester(
        1,
        "test",
        number=2,
        string="a very very very very very very very very very very long test",
    )
    """
    arguments = ", ".join(
        itertools.chain(
            (repr(arg) for arg in args),
            (f"{name}={repr(value)}" for name, value in kwargs.items()),
        )
    )
    return black.format_str(
        f"{name}({arguments})",
        mode=_black_filemode,
    )[:-1]
