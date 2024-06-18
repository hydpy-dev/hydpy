# -*- coding: utf-8 -*-
"""This module provides tools for defining and handling different kinds of parameters
of hydrological models."""
# import...
# ...from standard library
from __future__ import annotations
import builtins
import contextlib
import copy
import inspect
import itertools
import textwrap
import types
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import masktools
from hydpy.core import objecttools
from hydpy.core import propertytools
from hydpy.core import timetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

# from hydpy.cythons import modelutils  # actual download below

if TYPE_CHECKING:
    from hydpy.core import auxfiletools
    from hydpy.core import devicetools
    from hydpy.core import modeltools


def trim_kwarg(
    parameter: Parameter,
    name: str,
    value: float,
    lower: float = -numpy.inf,
    upper: float = numpy.inf,
) -> float:
    """Helper function for model developers for trimming scalar keyword arguments of
    type |float|.

    Function |trim_kwarg| works similarly to function |trim| but targets defining
    parameter values via parameter-specific keyword arguments.  Due to the individual
    nature of calculating parameter values from keyword arguments, using |trim_kwarg|
    is less standardisable than using |trim|.  Hence, model developers must include it
    manually into the `__call__` methods of their |Parameter| subclasses when trimming
    keyword arguments is required.

    The following tests show that |trim_kwarg| returns the eventually trimmed value,
    and, like |trim|, emits warnings only in case of boundary violations beyond the
    size of pure precision-related artefacts:

    >>> from hydpy.core.parametertools import Parameter, trim_kwarg
    >>> parameter = Parameter(None)

    >>> trim_kwarg(parameter, "x", 1.0) == 1.0
    True

    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     trim_kwarg(parameter, "x", 0.0, lower=1.0) == 1.0
    True
    UserWarning: For parameter `parameter` of element `?` the keyword argument `x` \
with value `0.0` needed to be trimmed to `1.0`.

    >>> with warn_later():
    ...     trim_kwarg(parameter, "x", 2.0, upper=1.0) == 1.0
    True
    UserWarning: For parameter `parameter` of element `?` the keyword argument `x` \
with value `2.0` needed to be trimmed to `1.0`.

    >>> x = 1.0 - 1e-15
    >>> x == 1.0
    False
    >>> with warn_later():
    ...     trim_kwarg(parameter, "x", x, lower=1.0) == 1.0
    True

    >>> x = 1.0 + 1e-15
    >>> x == 1.0
    False
    >>> with warn_later():
    ...     trim_kwarg(parameter, "x", x, upper=1.0) == 1.0
    True
    """
    gt = variabletools.get_tolerance
    if value < lower:
        if (value + gt(value)) < (lower - gt(lower)):
            _warn_trim_kwarg(parameter, name, value, lower)
        return lower
    if value > upper:
        if (value - gt(value)) > (upper + gt(upper)):
            _warn_trim_kwarg(parameter, name, value, upper)
        return upper
    return value


def _warn_trim_kwarg(
    parameter: Parameter, name: str, oldvalue: float, newvalue: float
) -> None:
    warnings.warn(
        f"For parameter {objecttools.elementphrase(parameter)} the keyword argument "
        f"`{name}` with value `{objecttools.repr_(oldvalue)}` needed to be trimmed to "
        f"`{objecttools.repr_(newvalue)}`."
    )


class IntConstant(int):
    """Class for |int| objects with individual docstrings."""

    def __new__(cls, value):
        const = int.__new__(cls, value)
        const.__doc__ = None
        frame = inspect.currentframe().f_back
        const.__module__ = frame.f_locals.get("__name__")
        return const


class Constants(dict[str, int]):
    """Base class for defining integer constants for a specific model."""

    value2name: dict[int, str]
    """Mapping from the the values of the constants to their names."""

    def __init__(self, *args, **kwargs) -> None:
        if not (args or kwargs):
            assert ((frame1 := inspect.currentframe()) is not None) and (
                (frame := frame1.f_back) is not None
            )
            assert isinstance(modulename := frame.f_locals.get("__name__"), str)
            self.__module__ = modulename
            for key, value in frame.f_locals.items():
                if key.isupper() and isinstance(value, IntConstant):
                    kwargs[key] = value
            super().__init__(**kwargs)
            self._prepare_docstrings(frame)
        else:
            super().__init__(*args, **kwargs)
        self.value2name = {value: key for key, value in self.items()}

    def _prepare_docstrings(self, frame: types.FrameType) -> None:
        """Assign docstrings to the constants handled by |Constants| to make them
        available in the interactive mode of Python."""
        if config.USEAUTODOC:
            assert (filename := inspect.getsourcefile(frame)) is not None
            with open(filename, encoding=config.ENCODING) as file_:
                sources = file_.read().split('"""')
            for code, doc in zip(sources[::2], sources[1::2]):
                code = code.strip()
                key = code.split("\n")[-1].split()[0]
                value = self.get(key)
                if value:
                    value.__doc__ = doc

    @property
    def sortednames(self) -> tuple[str, ...]:
        """The lowercase constants' names, sorted by the constants' values.

        >>> from hydpy.core.parametertools import Constants
        >>> Constants(GRASS=2, TREES=0, WATER=1).sortednames
        ('trees', 'water', 'grass')
        """
        return tuple(key.lower() for value, key in sorted(self.value2name.items()))


class Parameters:
    """Base class for handling all parameters of a specific model.

    |Parameters| objects handle four subgroups as attributes: the `control`
    subparameters, the `derived` subparameters, the `fixed` subparameters and the
    `solver` subparameters:

    >>> from hydpy.models.meteo_glob_fao56 import *
    >>> parameterstep("1d")
    >>> assert model.parameters
    >>> assert model.parameters.control
    >>> assert not model.parameters.solver

    Iterations makes only the non-empty subgroups available, which are actually
    handling |Parameter| objects:

    >>> for subpars in model.parameters:
    ...     print(subpars.name)
    control
    derived
    fixed
    >>> len(model.parameters)
    3

    Keyword access provides a type-safe way to query a subgroup via a string:

    >>> type(model.parameters["control"]).__name__
    'ControlParameters'
    >>> type(model.parameters["wrong"])
    Traceback (most recent call last):
    ...
    TypeError: There is no parameter subgroup named `wrong`.
    >>> model.parameters["model"]
    Traceback (most recent call last):
    ...
    TypeError: Attribute `model` is of type `Model`, which is not a subtype of class \
`SubParameters`.
    """

    model: modeltools.Model
    control: SubParameters
    derived: SubParameters
    fixed: SubParameters
    solver: SubParameters

    def __init__(self, kwargs):
        self.model = kwargs.get("model")
        self.control = self._prepare_subpars("control", kwargs)
        self.derived = self._prepare_subpars("derived", kwargs)
        self.fixed = self._prepare_subpars("fixed", kwargs)
        self.solver = self._prepare_subpars("solver", kwargs)

    def _prepare_subpars(self, shortname, kwargs):
        fullname = f"{shortname.capitalize()}Parameters"
        cls = kwargs.get(fullname, type(fullname, (SubParameters,), {"CLASSES": ()}))
        return cls(
            self,
            getattr(kwargs.get("cythonmodule"), fullname, None),
            kwargs.get("cymodel"),
        )

    def update(self, ignore_errors: bool = False) -> None:
        """Call method |Parameter.update| of all "secondary" parameters.

        Directly after initialisation, neither the primary (`control`) parameters nor
        the secondary (`derived`)  parameters of application model |meteo_glob_fao56|
        are ready for usage:

        >>> from hydpy.models.meteo_glob_fao56 import *
        >>> parameterstep("1d")
        >>> simulationstep("1d")
        >>> derived
        doy(?)
        moy(?)
        hours(?)
        days(?)
        sct(?)
        utclongitude(?)
        latituderad(?)

        Trying to update the values of the secondary parameters while the primary ones
        are still not defined raises errors like the following:

        >>> model.parameters.update()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to update parameter \
`doy` of element `?`, the following error occurred: An Indexer object has been asked \
for an `dayofyear` array.  Such an array has neither been determined yet nor can it \
be determined automatically at the moment.   Either define an `dayofyear` array \
manually and pass it to the Indexer object, or make a proper Timegrids object \
available within the pub module.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-04", "1d"
        >>> model.parameters.update()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: While trying to update parameter \
`latituderad` of element `?`, the following error occurred: While trying to multiply \
variable `latitude` and `float` instance `0.017453`, the following error occurred: \
For variable `latitude`, no value has been defined so far.

        With a defined |Timegrids| object and proper values both for parameters
        |meteo_control.Latitude| and |meteo_control.Longitude|, updating the derived
        parameters succeeds:

        >>> latitude(50.0)
        >>> longitude(10.0)
        >>> model.parameters.update()
        >>> derived
        doy(29, 30, 31, 32, 33)
        moy(0, 0, 1, 1, 1)
        hours(24.0)
        days(1.0)
        sct(12.0)
        utclongitude(15)
        latituderad(0.872665)

        .. testsetup::

            >>> del pub.timegrids
        """
        for subpars in self.secondary_subpars:
            for par in subpars:
                try:
                    par.update()
                except BaseException:
                    if not ignore_errors:
                        objecttools.augment_excmessage(
                            f"While trying to update parameter "
                            f"{objecttools.elementphrase(par)}"
                        )

    def verify(self) -> None:
        """Call method |Variable.verify| of all |Parameter| objects handled by the
        actual model.

        When calling method |Parameters.verify| directly after initialising model
        |meteo_glob_fao56| (without using default values), it raises a |RuntimeError|
        due to the undefined value of control parameter |meteo_control.Latitude|:

        >>> from hydpy.models.meteo_glob_fao56 import *
        >>> parameterstep("1d")
        >>> simulationstep("1d")
        >>> model.parameters.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `latitude`, 1 required value has not been set yet: \
latitude(?).

        Assigning a value to |meteo_control.Latitude| is not sufficient:

        >>> model.parameters.control.latitude(50.0)
        >>> model.parameters.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: For variable `longitude`, 1 required value has not been set \
yet: longitude(?).

        After also defining suitable values for all remaining control parameters, the
        derived parameters are still not ready:

        >>> model.parameters.control.longitude(10.0)
        >>> model.parameters.control.angstromconstant(0.25)
        >>> model.parameters.control.angstromfactor(0.5)
        >>> model.parameters.verify()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable \
`doy` can only be retrieved after it has been defined.

        After updating the derived parameters (which requires preparing a |Timegrids|
        object first), method |Parameters.verify| has no reason to complain anymore:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-30", "2000-02-04", "1d"
        >>> model.parameters.update()
        >>> model.parameters.verify()

        .. testsetup::

            >>> del pub.timegrids
        """
        for subpars in self:
            for par in subpars:
                par.verify()

    @property
    def secondary_subpars(self) -> Iterator[SubParameters]:
        """Iterate through all subgroups of "secondary" parameters.

        These secondary parameter subgroups are the `derived` parameters and the
        `solver` parameters at the moment:

        >>> from hydpy.models.meteo_glob_fao56 import *
        >>> parameterstep("1d")
        >>> for subpars in model.parameters.secondary_subpars:
        ...     print(subpars.name)
        derived
        solver
        """
        yield self.derived
        yield self.solver

    def __getitem__(self, item: str) -> SubParameters:
        try:
            subpars = getattr(self, item)
        except AttributeError:
            raise TypeError(f"There is no parameter subgroup named `{item}`.") from None
        if isinstance(subpars, SubParameters):
            return subpars
        raise TypeError(
            f"Attribute `{item}` is of type `{type(subpars).__name__}`, which is not "
            f"a subtype of class `SubParameters`."
        )

    def __iter__(self) -> Iterator[SubParameters]:
        for subpars in (self.control, self.derived, self.fixed, self.solver):
            if subpars:
                yield subpars

    def __len__(self):
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        return any(pars for pars in self)


class FastAccessParameter(variabletools.FastAccess):
    """Used as a surrogate for typed Cython classes handling parameters
    when working in pure Python mode."""


class SubParameters(
    variabletools.SubVariables[Parameters, "Parameter", FastAccessParameter]
):
    '''Base class for handling subgroups of model parameters.

    When trying to implement a new model, one has to define its
    specific |Parameter| subclasses. Currently, the HydPy framework
    distinguishes between control parameters, derived parameters,
    fixed parameters, and solver parameters. Each |Parameter| subclass is
    a member of a collection class derived from |SubParameters|, called
    "ControlParameters", "DerivedParameters", "FixedParameters", or
    "SolverParameters", respectively.  Indicate membership by putting the
    parameter subclasses into the |tuple| "CLASSES":

    >>> from hydpy.core.parametertools import Parameter, SubParameters
    >>> class Par2(Parameter):
    ...     """Parameter 2 [-]."""
    ...     NDIM = 1
    ...     TYPE = float
    ...     TIME = None
    >>> class Par1(Parameter):
    ...     """Parameter 1 [-]."""
    ...     NDIM = 1
    ...     TYPE = float
    ...     TIME = None
    >>> class ControlParameters(SubParameters):
    ...     """Control Parameters."""
    ...     CLASSES = (Par2,
    ...                Par1)

    The order within the tuple determines the order of iteration:

    >>> control = ControlParameters(None)
    >>> control
    par2(?)
    par1(?)

    Each |SubParameters| object has a `fastaccess` attribute.  When
    working in pure Python mode, this is an instance of class
    |FastAccessParameter|:

    >>> from hydpy import classname, prepare_model, pub
    >>> with pub.options.usecython(False):
    ...     model = prepare_model("lland_dd")
    >>> classname(model.parameters.control.fastaccess)
    'FastAccessParameter'

    When working in Cython mode (which is the default mode and much
    faster), `fastaccess` is an object of a Cython extension class
    specialised for the respective model and sequence group:

    >>> with pub.options.usecython(True):
    ...     model = prepare_model("lland_dd")
    >>> classname(model.parameters.control.fastaccess)
    'ControlParameters'
    '''

    pars: Parameters
    _cymodel: Optional[CyModelProtocol]
    _CLS_FASTACCESS_PYTHON = FastAccessParameter

    def __init__(
        self,
        master: Parameters,
        cls_fastaccess: Optional[type[FastAccessParameter]] = None,
        cymodel: Optional[CyModelProtocol] = None,
    ):
        self.pars = master
        self._cymodel = cymodel
        super().__init__(master=master, cls_fastaccess=cls_fastaccess)

    def _init_fastaccess(self) -> None:
        super()._init_fastaccess()
        if self._cls_fastaccess and self._cymodel:
            setattr(self._cymodel.parameters, self.name, self.fastaccess)

    @property
    def name(self) -> str:
        """The class name in lowercase letters omitting the last ten characters
        ("parameters").

        >>> from hydpy.core.parametertools import SubParameters
        >>> class ControlParameters(SubParameters):
        ...     CLASSES = ()
        >>> ControlParameters(None).name
        'control'
        """
        return type(self).__name__[:-10].lower()


class Keyword(NamedTuple):
    """Helper class to describe parameter-specific keyword arguments for defining
    values by "calling" a parameter object."""

    name: str
    """The keyword argument's name."""
    type_: type[Union[float, int]] = float
    """The keyword argument's type (equivalent to the |Variable.TYPE| attribute of 
    class |Variable|)."""
    time: Optional[bool] = None
    """Type of the keyword argument's time dependency (equivalent to the 
    |Parameter.TIME| attribute of class |Parameter|).
    """
    span: tuple[Optional[float], Optional[float]] = (None, None)
    """The keyword argument's lower and upper boundary (equivalent to the 
    |Variable.SPAN| attribute of class |Variable|).
    """


class KeywordArgumentsError(RuntimeError):
    """A specialised |RuntimeError| raised by class |KeywordArguments|."""


class KeywordArguments(Generic[T]):
    """A handler for the keyword arguments of the instances of specific |Parameter|
    subclasses.

    Class |KeywordArguments| is a rather elaborate feature of *HydPy* primarily
    thought for framework developers.  One possible use-case for (advanced)
    *HydPy* users is writing polished auxiliary control files.  When dealing with
    such a problem, have a look on method |KeywordArguments.extend|.

    The purpose of class |KeywordArguments| is to simplify handling instances of
    |Parameter| subclasses which allow setting values by calling them with keyword
    arguments.  When useful, instances of |Parameter| subclasses should return a
    valid |KeywordArguments| object via property |Parameter.keywordarguments|.
    This object should contain the keyword arguments that, when passed to the same
    parameter instance or another parameter instance of the same type, sets it into
    an equal state.  This is best explained by the following example based on
    parameter |lland_control.TRefT| of application model |lland_dd| (see the
    documentation on property |ZipParameter.keywordarguments| of class |ZipParameter|
    for additional information):

    >>> from hydpy.models.lland_dd import *
    >>> parameterstep()
    >>> nhru(4)
    >>> lnk(ACKER, LAUBW, WASSER, ACKER)
    >>> treft(acker=2.0, laubw=1.0)
    >>> treft.keywordarguments
    KeywordArguments(acker=2.0, laubw=1.0)

    You can initialise a |KeywordArguments| object on your own:

    >>> from hydpy import KeywordArguments
    >>> kwargs1 = KeywordArguments(acker=3.0, laubw=2.0, nadelw=1.0)
    >>> kwargs1
    KeywordArguments(acker=3.0, laubw=2.0, nadelw=1.0)

    After preparing a |KeywordArguments| object, it is "valid" by default:

    >>> kwargs1.valid
    True

    Pass |False| as a positional argument to the constructor if you want your
    |KeywordArguments| object to be invalid at first:

    >>> kwargs2 = KeywordArguments(False)
    >>> kwargs2
    KeywordArguments()
    >>> kwargs2.valid
    False

    Flag |KeywordArguments.valid|, for example, helps to distinguish between empty
    objects that are okay to be empty and those that are not.  When we, for example,
    set all hydrological response units to land-use type |lland_constants.WASSER|
    (water), parameter |lland_control.TRefT| returns the following valid
    |KeywordArguments| object, as its values do not need to be defined for water areas:

    >>> lnk(WASSER)
    >>> treft
    treft(nan)
    >>> treft.keywordarguments
    KeywordArguments()
    >>> treft.keywordarguments.valid
    True

    Class |KeywordArguments| supports features like iteration but raises the
    exception |KeywordArgumentsError| when trying to iterate an invalid object:

    >>> for keyword, argument in kwargs1:
    ...     print(keyword, argument)
    acker 3.0
    laubw 2.0
    nadelw 1.0

    >>> for keyword, argument in kwargs2:
    ...     print(keyword, argument)
    Traceback (most recent call last):
    ...
    hydpy.core.parametertools.KeywordArgumentsError: Cannot iterate an invalid \
`KeywordArguments` object.

    The same holds when trying to check if a specific keyword-value item is available:

    >>> ("acker", 3.0) in kwargs1
    True
    >>> ("laubw", 3.0) in kwargs1
    False
    >>> ("?", "???") in kwargs1
    False
    >>> ("laubw", 3.0) in kwargs2
    Traceback (most recent call last):
    ...
    hydpy.core.parametertools.KeywordArgumentsError: Cannot check if an item is \
defined by an invalid `KeywordArguments` object.

    However, keyword access is always possible:

    >>> kwargs2["laubw"] = 3.0

    >>> kwargs2["laubw"]
    3.0

    >>> del kwargs2["laubw"]

    >>> kwargs2["laubw"]
    Traceback (most recent call last):
    ...
    KeyError: 'The current `KeywordArguments` object does not handle an argument \
under the keyword `laubw`.'

    >>> del kwargs2["laubw"]
    Traceback (most recent call last):
    ...
    KeyError: 'The current `KeywordArguments` object does not handle an argument \
under the keyword `laubw`.'

    Two |KeywordArguments| objects are considered equal if they have the same
    validity state, the same length, and if all items are equal:

    >>> KeywordArguments(True) == KeywordArguments(False)
    False
    >>> KeywordArguments(x=1) == KeywordArguments(x=1, y=2)
    False
    >>> KeywordArguments(x=1, y=2) == KeywordArguments(x=1, y=3)
    False
    >>> KeywordArguments(x=1, y=2) == KeywordArguments(x=1, y=2)
    True

    You can also compare with other objects (always |False|) and use the
    "!=" operator:

    >>> KeywordArguments() == "test"
    False
    >>> KeywordArguments(x=1, y=2) != KeywordArguments(x=1, y=2)
    False
    """

    valid: bool
    """Flag indicating whether the actual |KeywordArguments| object is valid or not."""
    _name2value: dict[str, T]

    def __init__(self, __valid: bool = True, **keywordarguments: T) -> None:
        self.valid = __valid
        self._name2value = copy.deepcopy(keywordarguments)

    def add(self, name: str, value: T) -> None:
        """Add a keyword argument.

        Method |KeywordArguments.add| works both for valid and invalid
        |KeywordArguments| objects without changing their validity status:

        >>> from hydpy import KeywordArguments
        >>> kwargs = KeywordArguments()
        >>> kwargs.add("one", 1)
        >>> kwargs.valid = False
        >>> kwargs.add("two", 2)
        >>> kwargs
        KeywordArguments(one=1, two=2)

        It raises the following error when (possibly accidentally) trying to
        overwrite an existing keyword argument:

        >>> kwargs.add("one", 3)
        Traceback (most recent call last):
        ...
        hydpy.core.parametertools.KeywordArgumentsError: Cannot add argument value \
`3` of type `int` to the current `KeywordArguments` object as it already handles \
the unequal argument `1` under the keyword `one`.

        On the other hand, redefining the save value causes no harm and thus
        does not trigger an exception:

        >>> kwargs.add("one", 1)
        >>> kwargs
        KeywordArguments(one=1, two=2)
        """
        if name in self._name2value:
            if self._name2value[name] != value:
                raise KeywordArgumentsError(
                    f"Cannot add argument {objecttools.value_of_type(value)} to the "
                    f"current `{type(self).__name__}` object as it already handles "
                    f"the unequal argument `{self._name2value[name]}` under the "
                    f"keyword `{name}`."
                )
        else:
            self._name2value[name] = value

    def subset_of(self, other: KeywordArguments[T]) -> bool:
        """Check if the actual |KeywordArguments| object is a subset of the given one.

        First, we define the following (valid) |KeywordArguments| objects:

        >>> from hydpy import KeywordArguments
        >>> kwargs1 = KeywordArguments(a=1, b=2)
        >>> kwargs2 = KeywordArguments(a= 1, b=2, c=3)
        >>> kwargs3 = KeywordArguments(a= 1, b=3)

        Method |KeywordArguments.subset_of| requires that the keywords handled by
        the left |KeywordArguments| object form a subset of the keywords of the
        right |KeywordArguments| object:

        >>> kwargs1.subset_of(kwargs2)
        True
        >>> kwargs2.subset_of(kwargs1)
        False

        Additionally, all values corresponding to the union of the relevant keywords
        must be equal:

        >>> kwargs1.subset_of(kwargs3)
        False

        If at least one of both |KeywordArguments| is invalid,  method
        |KeywordArguments.subset_of| generally returns |False|:

        >>> kwargs2.valid = False
        >>> kwargs1.subset_of(kwargs2)
        False
        >>> kwargs2.subset_of(kwargs1)
        False
        >>> kwargs2.subset_of(kwargs2)
        False
        """
        if self.valid and other.valid:
            for item in self._name2value.items():
                if item not in other:
                    return False
            return True
        return False

    def extend(
        self,
        parametertype: type[Parameter],
        elements: Iterable[devicetools.Element],
        raise_exception: bool = True,
    ) -> None:
        """Extend the currently available keyword arguments based on the parameters
        of the given type handled by the given elements.
        
        Sometimes (for example, when writing auxiliary control files) one is 
        interested in a superset of all keyword arguments related to a specific
        |Parameter| type relevant for certain |Element| objects.  To show how
        method |KeywordArguments.extend| can help in such cases, we make use of
        the `LahnH` example project:
        
        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        First, we prepare an empty |KeywordArguments| object:

        >>> from hydpy import KeywordArguments
        >>> kwargs = KeywordArguments()
        >>> kwargs
        KeywordArguments()

        When passing a |Parameter| subclass (in our example
        |hland_control.IcMax|) and some |Element| objects (at first the headwater
        elements, which handle instances of application model |hland_v1|), method
        |KeywordArguments.extend| collects their relevant keyword arguments:

        >>> from hydpy.models.hland.hland_control import IcMax
        >>> kwargs.extend(IcMax, pub.selections.headwaters.elements)
        >>> kwargs
        KeywordArguments(field=1.0, forest=1.5)

        Applying method |KeywordArguments.extend| also on the non-headwaters does
        not change anything, as the values of parameter |hland_control.IcMax| are
        consistent for the whole Lahn river basin:

        >>> kwargs.extend(IcMax, pub.selections.nonheadwaters.elements)
        >>> kwargs
        KeywordArguments(field=1.0, forest=1.5)

        Next, we change the interception capacity of forests in one subcatchment:

        >>> icmax = hp.elements.land_lahn_2.model.parameters.control.icmax
        >>> icmax(field=1.0, forest=2.0)

        Re-applying method |KeywordArguments.extend| now raises the following error:

        >>> kwargs.extend(IcMax, pub.selections.nonheadwaters.elements)
        Traceback (most recent call last):
        ...
        hydpy.core.parametertools.KeywordArgumentsError: While trying to extend the \
keyword arguments based on the available `IcMax` parameter objects, the following \
error occurred: While trying to add the keyword arguments for element `land_lahn_2`, \
the following error occurred: Cannot add argument value `2.0` of type `float64` to \
the current `KeywordArguments` object as it already handles the unequal argument \
`1.5` under the keyword `forest`.

        The old keywords arguments and the validity status remain unchanged:

        >>> kwargs
        KeywordArguments(field=1.0, forest=1.5)
        >>> kwargs.valid
        True

        When we modify the same |hland_control.IcMax| parameter object in a way
        that it cannot return a valid |KeywordArguments| object anymore, we get
        the following error message:

        >>> icmax(0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
        >>> kwargs.extend(IcMax, pub.selections.nonheadwaters.elements)
        Traceback (most recent call last):
        ...
        hydpy.core.parametertools.KeywordArgumentsError: While trying to extend the \
keyword arguments based on the available `IcMax` parameter objects, the following \
error occurred: While trying to add the keyword arguments for element `land_lahn_2`, \
the following error occurred: Cannot iterate an invalid `KeywordArguments` object.

        When setting the `raise_exception` argument to |False|, method
        |KeywordArguments.extend| handles such errors internally and, instead of
        raising an error invalidates the actual |KeywordArguments| object:

        >>> kwargs.extend(
        ...     IcMax, pub.selections.nonheadwaters.elements, raise_exception=False)
        >>> kwargs
        KeywordArguments()
        >>> kwargs.valid
        False

        Trying to extend an invalid |KeywordArguments| object by default also
        raises an exception of type |KeywordArgumentsError|:

        >>> kwargs.extend(IcMax, pub.selections.headwaters.elements)
        Traceback (most recent call last):
        ...
        hydpy.core.parametertools.KeywordArgumentsError: While trying to extend the \
keyword arguments based on the available `IcMax` parameter objects, the following \
error occurred: The `KeywordArguments` object is invalid.

        When setting `raise_exception` to |False| instead, nothing happens:

        >>> kwargs.extend(IcMax, pub.selections.headwaters.elements, \
raise_exception=False)
        >>> kwargs
        KeywordArguments()
        >>> kwargs.valid
        False
        """
        name_parameter = parametertype.name
        try:
            if not self.valid:
                if raise_exception:
                    raise KeywordArgumentsError(
                        f"The `{type(self).__name__}` object is invalid."
                    )
                return
            for element in elements:
                try:
                    control = element.model.parameters.control
                    other = control[name_parameter].keywordarguments
                    for name_keyword, value in other:
                        self.add(name_keyword, value)
                except KeywordArgumentsError:
                    if raise_exception:
                        objecttools.augment_excmessage(
                            f"While trying to add the keyword arguments for "
                            f"element `{objecttools.devicename(element)}`"
                        )
                    self.valid = False
                    self._name2value.clear()
                    return
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to extend the keyword arguments based on the "
                f"available `{parametertype.__name__}` parameter objects"
            )
        return

    def clear(self) -> None:
        """Clear the current object contents and set attribute |KeywordArguments.valid|
        to |False|.

        >>> from hydpy import KeywordArguments
        >>> kwa =KeywordArguments(x=1, y=2)
        >>> kwa
        KeywordArguments(x=1, y=2)
        >>> kwa.valid
        True
        >>> kwa.clear()
        >>> kwa
        KeywordArguments()
        >>> kwa.valid
        True
        """
        self._name2value.clear()

    def __getitem__(self, key: str) -> T:
        try:
            return self._name2value[key]
        except KeyError:
            raise KeyError(
                f"The current `{type(self).__name__}` object does not handle an "
                f"argument under the keyword `{key}`."
            ) from None

    def __setitem__(self, key: str, value: T) -> None:
        self._name2value[key] = value

    def __delitem__(self, key: str) -> None:
        try:
            del self._name2value[key]
        except KeyError:
            raise KeyError(
                f"The current `{type(self).__name__}` object does not handle an "
                f"argument under the keyword `{key}`."
            ) from None

    def __contains__(self, item: tuple[str, T]) -> bool:
        if not self.valid:
            raise KeywordArgumentsError(
                f"Cannot check if an item is defined by an invalid "
                f"`{type(self).__name__}` object."
            )
        if item[0] in self._name2value:
            return self._name2value[item[0]] == item[1]
        return False

    def __len__(self) -> int:
        return len(self._name2value)

    def __iter__(self) -> Iterator[tuple[str, T]]:
        if not self.valid:
            raise KeywordArgumentsError(
                f"Cannot iterate an invalid `{type(self).__name__}` object."
            )
        yield from self._name2value.items()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KeywordArguments):
            if self.valid != other.valid:
                return False
            if len(self) != len(other):
                return False
            for item in self:
                if item not in other:
                    return False
            return True
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return objecttools.apply_black(type(self).__name__, **self._name2value)


class Parameter(variabletools.Variable):
    """Base class for model parameters.

    In *HydPy*, each kind of model parameter is represented by a unique
    class.  In almost all cases, you should derive such a class,
    directly or indirectly, from class |Parameter|, which provides
    all necessary features that assure the new parameter class works
    well when applied in different contexts.

    In most cases, the functionalities of class |Parameter| are sufficient
    for deriving new classes without doing any real coding (writing
    new or extending existing methods).  However, one sometimes prefers
    to do some extensions to simplify the usage of the parameter class.
    Before doing so on your own, have a look at the specialised
    subclasses already available in module |parametertools|.  One
    example is class |SeasonalParameter|, which allows defining
    parameter values that vary seasonally (e.g. the leaf area index).

    Class |Parameter| itself extends class |Variable|.  Hence, all
    model-specific |Parameter| subclasses must define both a value
    dimensionality and a type via class constants `NDIM` and `TYPE`,
    respectively.  Additionally, one has to define the class constant
    `TIME`, telling how parameter values depend on the simulation
    step size (see methods |Parameter.get_timefactor| and
    |Parameter.apply_timefactor|). Also, model developers might find
    it useful to define initial default values via `INIT` or minimum
    and maximum values via `SPAN`:

    .. testsetup::

        >>> from hydpy import pub
        >>> del pub.options.simulationstep

    Let us first prepare a new parameter class without time-dependency
    (indicated by assigning |None|) and initialise it:

    >>> from hydpy.core.parametertools import Parameter
    >>> class Par(Parameter):
    ...     NDIM = 0
    ...     TYPE = float
    ...     TIME = None
    ...     SPAN = 0.0, 5.0
    >>> par = Par(None)

    As described in the documentation on base class |Variable|, one
    can directly assign values via property |Variable.value|:

    >>> par.value = 6.0
    >>> par
    par(6.0)

    For |Parameter| objects, there is an alternative way to define
    new values, which should be preferred in most cases (especially
    when writing control files), by "calling" the parameter with
    suitable arguments.  For example, this offers the advantage of
    automatical trimming.  In the example above, the assigned value
    (6.0) violates the upper bound (5.0) of our test parameter.  When
    using the "call" syntax, the wrong value is corrected immediately:

    >>> from hydpy import pub
    >>> from hydpy.core.testtools import warn_later
    >>> with pub.options.warntrim(True), warn_later():
    ...     par(7.0)
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `7.0` and `5.0`, respectively.
    >>> par
    par(5.0)

    .. testsetup::

        >>> try:
        ...     del model
        ... except NameError:
        ...     pass

    The "call" syntax provides some additional features and related
    error messages.  Use the `auxfile` keyword argument to tell that
    another control file defines the actual parameter value.  Note
    that you cannot use this feature in the interactive mode:

    >>> par(auxfile="test")
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to extract information for parameter `par` \
from file `test`, the following error occurred: Cannot determine the \
corresponding model.  Use the `auxfile` keyword in usual parameter \
control files only.

    Also, note that you cannot combine the `auxfile` keyword with any other keyword:

    >>> par(auxfile="test", x1=1, x2=2, x3=3)
    Traceback (most recent call last):
    ...
    ValueError: It is not allowed to combine keyword `auxfile` with other \
keywords, but for parameter `par` of element `?` also the following keywords \
are used: x1, x2, and x3.

    Some |Parameter| subclasses support other keyword arguments.
    The standard error message for unsupported arguments is the following:

    >>> par(wrong=1.0)
    Traceback (most recent call last):
    ...
    NotImplementedError: The value(s) of parameter `par` of element `?` \
could not be set based on the given keyword arguments.

    Passing a wrong number of positional arguments results in the
    following error:

    >>> par(1.0, 2.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the value(s) of variable `par`, the \
following error occurred: The given value `[1. 2.]` cannot be converted \
to type `float`.

    Passing no argument or both positional and keyword arguments are also
    disallowed:

    >>> par()
    Traceback (most recent call last):
    ...
    ValueError: For parameter `par` of element `?` neither a positional \
nor a keyword argument is given.

    >>> par(1.0, auxfile="test")
    Traceback (most recent call last):
    ...
    ValueError: For parameter `par` of element `?` both positional and \
keyword arguments are given, which is ambiguous.

    Our next |Parameter| test class is a little more complicated, as it
    handles a (1-dimensional) vector of time-dependent values (indicated
    by setting the class attribute `TIME` to |True|):

    >>> class Par(Parameter):
    ...     NDIM = 1
    ...     TYPE = float
    ...     TIME = True
    ...     SPAN = 0.0, None

    We prepare a shape of length 2 and set different simulation and
    parameter step sizes, to see that the required time-related
    adjustments work correctly:

    >>> par = Par(None)
    >>> par.shape = (2,)
    >>> pub.options.parameterstep = "1d"
    >>> pub.options.simulationstep = "2d"

    Now you can pass one single value, an iterable containing two
    values, or two separate values as positional arguments, to set
    both required values.  Note that the given values are assumed to
    agree with the actual parameter step size, and are converted
    internally to agree with the actual simulation step size.  The
    string representation shows values that agree with the parameter
    step size; the |Variable.values| property shows the values that
    agree with the simulation step size, relevant during simulation
    runs.  Also, the string representation shows only one value, in
    case all (relevant) values are identical:

    >>> par(3.0)
    >>> par
    par(3.0)
    >>> par.values
    array([6., 6.])

    >>> par([0.0, 4.0])
    >>> par
    par(0.0, 4.0)
    >>> par.values
    array([0., 8.])

    >>> par(1.0, 2.0)
    >>> par
    par(1.0, 2.0)
    >>> par.values
    array([2., 4.])

    Using the `call` syntax to set parameter values triggers method
    |trim| automatically:

    >>> with pub.options.warntrim(True), warn_later():
    ...     par(-1.0, 3.0)
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `-2.0, 6.0` and `0.0, 6.0`, respectively.
    >>> par
    par(0.0, 3.0)
    >>> par.values
    array([0., 6.])

    You are free to change the parameter step size (temporarily) to change
    the string representation of |Parameter| handling time-dependent values
    without a risk to change the actual values relevant for simulation:

    >>> with pub.options.parameterstep("2d"):
    ...     print(par)
    ...     print(repr(par.values))
    par(0.0, 6.0)
    array([0., 6.])
    >>> par
    par(0.0, 3.0)
    >>> par.values
    array([0., 6.])

    The highest number of dimensions of |Parameter| subclasses supported
    is currently two.  The following examples repeat some examples from
    above for a 2-dimensional parameter that handles that values inversely
    related to the simulation step size (indicated by setting the class
    attribute `TIME` to |False|):

    >>> class Par(Parameter):
    ...     NDIM = 2
    ...     TYPE = float
    ...     TIME = False
    ...     SPAN = 0.0, 5.0

    >>> par = Par(None)
    >>> par.shape = (2, 3)

    >>> par(9.0)
    >>> par
    par(9.0)
    >>> par.values
    array([[4.5, 4.5, 4.5],
           [4.5, 4.5, 4.5]])

    >>> par([[1.0, 2.0, 3.0],
    ...      [4.0, 5.0, 6.0]])
    >>> par
    par([[1.0, 2.0, 3.0],
         [4.0, 5.0, 6.0]])
    >>> par.values
    array([[0.5, 1. , 1.5],
           [2. , 2.5, 3. ]])

    >>> par(1.0, 2.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `par`, the following \
error occurred: While trying to convert the value(s) `[0.5 1. ]` to a numpy ndarray \
with shape `(2, 3)` and type `float`, the following error occurred: could not \
broadcast input array from shape (2,) into shape (2,3)
    """

    TIME: Optional[bool]
    KEYWORDS: Mapping[str, Keyword] = {}

    subvars: SubParameters
    """The subgroup to which the parameter belongs."""
    subpars: SubParameters
    """Alias for |Parameter.subvars|."""

    _CLS_FASTACCESS_PYTHON = FastAccessParameter

    _keywordarguments: KeywordArguments

    def __init__(self, subvars: SubParameters) -> None:
        super().__init__(subvars)
        self.subpars = subvars
        self._keywordarguments = KeywordArguments(False)

    def _raise_args_and_kwargs_error(self) -> NoReturn:
        raise ValueError(
            f"For parameter {objecttools.elementphrase(self)} both positional and "
            f"keyword arguments are given, which is ambiguous."
        )

    def _raise_no_args_and_no_kwargs_error(self) -> NoReturn:
        raise ValueError(
            f"For parameter {objecttools.elementphrase(self)} neither a positional "
            f"nor a keyword argument is given."
        )

    def _raise_kwargs_and_auxfile_error(self, kwargs: Mapping[str, object]) -> NoReturn:
        raise ValueError(
            f"It is not allowed to combine keyword `auxfile` with other keywords, but "
            f"for parameter {objecttools.elementphrase(self)} also the following "
            f"keywords are used: {objecttools.enumeration(kwargs.keys())}."
        )

    def _raise_wrong_kwargs_error(self) -> NoReturn:
        # ToDo: we should stop using `NotImplementedError` this way
        # To trick pylint:
        raise getattr(builtins, "NotImplementedError")(
            f"The value(s) of parameter {objecttools.elementphrase(self)} could not "
            f"be set based on the given keyword arguments."
        )

    def __call__(self, *args, **kwargs) -> None:
        if args and kwargs:
            self._raise_args_and_kwargs_error()
        if not args and not kwargs:
            self._raise_no_args_and_no_kwargs_error()
        auxfile = kwargs.pop("auxfile", None)
        if auxfile:
            if kwargs:
                self._raise_kwargs_and_auxfile_error(kwargs)
            self.values = self._get_values_from_auxiliaryfile(auxfile)
        elif args:
            if len(args) == 1:
                args = args[0]
            self.values = self.apply_timefactor(numpy.array(args))
        else:
            self._raise_wrong_kwargs_error()
        self.trim()

    def _get_values_from_auxiliaryfile(self, auxfile: str):
        """Try to return the parameter values from the auxiliary control file with the
        given name.

        Things are a little complicated here.  To understand this method, you should
        first take a look at the |parameterstep| function.
        """
        try:
            assert (
                ((frame1 := inspect.currentframe()) is not None)
                and ((frame2 := frame1.f_back) is not None)
                and ((frame := frame2.f_back) is not None)
            )
            while frame:
                namespace = frame.f_locals
                try:
                    subnamespace = {"model": namespace["model"], "focus": self}
                    break
                except KeyError:
                    frame = frame.f_back
            else:
                raise RuntimeError(
                    "Cannot determine the corresponding model.  Use the `auxfile` "
                    "keyword in usual parameter control files only."
                )
            filetools.ControlManager.read2dict(auxfile, subnamespace)
            subself = subnamespace[self.name]
            try:
                return subself.value
            except exceptiontools.AttributeNotReady:
                raise RuntimeError(
                    f"The selected auxiliary file does not define "
                    f"value(s) for parameter `{self.name}`."
                ) from None
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to extract information for parameter "
                f"`{self.name}` from file `{auxfile}`"
            )

    def _find_kwargscombination(
        self,
        given_args: Sequence[Any],
        given_kwargs: dict[str, Any],
        allowed_combinations: tuple[set[str], ...],
    ) -> Optional[int]:
        if given_kwargs and ("auxfile" not in given_kwargs):
            if given_args:
                self._raise_args_and_kwargs_error()
            try:
                return allowed_combinations.index(set(given_kwargs))
            except ValueError:
                return None
        return None

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        if self.NDIM:
            if exceptiontools.attrready(self, "shape"):
                return
            setattr(self.fastaccess, self.name, None)
            return
        initvalue, initflag = self.initinfo
        if initflag:
            setattr(self, "value", initvalue)
            return
        setattr(self.fastaccess, self.name, initvalue)
        return

    @property
    def initinfo(self) -> tuple[Union[float, int, bool], bool]:
        """A |tuple| containing the initial value and |True| or a missing
        value and |False|, depending on the actual |Parameter| subclass and
        the actual value of option |Options.usedefaultvalues|.

        In the following we show how method the effects of property
        |Parameter.initinfo| when initiasing new |Parameter| objects.
        Let's define a parameter test class and prepare a function for
        initialising it and connecting the resulting instance to a
        |SubParameters| object:

        >>> from hydpy.core.parametertools import Parameter, SubParameters
        >>> class Test(Parameter):
        ...     NDIM = 0
        ...     TYPE = float
        ...     TIME = None
        ...     INIT = 2.0
        >>> class SubGroup(SubParameters):
        ...     CLASSES = (Test,)
        >>> def prepare():
        ...     subpars = SubGroup(None)
        ...     test = Test(subpars)
        ...     test.__hydpy__connect_variable2subgroup__()
        ...     return test

        By default, making use of the `INIT` attribute is disabled:

        >>> test = prepare()
        >>> test
        test(?)

        Enable it through setting |Options.usedefaultvalues| to |True|:

        >>> from hydpy import pub
        >>> pub.options.usedefaultvalues = True
        >>> test = prepare()
        >>> test
        test(2.0)

        When no `INIT` attribute is defined (indicated by |None|), enabling
        |Options.usedefaultvalues| has no effect, of course:

        >>> Test.INIT = None
        >>> test = prepare()
        >>> test
        test(?)

        For time-dependent parameter values, the `INIT` attribute is assumed
        to be related to a |Parameterstep| of one day:

        >>> pub.options.parameterstep = "2d"
        >>> pub.options.simulationstep = "12h"
        >>> Test.INIT = 2.0
        >>> Test.TIME = True
        >>> test = prepare()
        >>> test
        test(4.0)
        >>> test.value
        1.0
        """
        init = self.INIT
        if (init is not None) and hydpy.pub.options.usedefaultvalues:
            with hydpy.pub.options.parameterstep("1d"):
                return self.apply_timefactor(init), True
        return variabletools.TYPE2MISSINGVALUE[self.TYPE], False

    @classmethod
    def get_timefactor(cls) -> float:
        """Factor to adjust a new value of a time-dependent parameter.

        For a time-dependent parameter, its effective value depends on the
        simulation step size.  Method |Parameter.get_timefactor| returns
        the fraction between the current simulation step size and the
        current parameter step size.

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.options.simulationstep
            >>> del pub.options.parameterstep

        Method |Parameter.get_timefactor| raises the following error
        when time information is not available:

        >>> from hydpy.core.parametertools import Parameter
        >>> Parameter.get_timefactor()
        Traceback (most recent call last):
        ...
        RuntimeError: To calculate the conversion factor for adapting the \
values of the time-dependent parameters, you need to define both a \
parameter and a simulation time step size first.

        One can define both time step sizes directly:

        >>> from hydpy import pub
        >>> pub.options.parameterstep = "1d"
        >>> pub.options.simulationstep = "6h"
        >>> Parameter.get_timefactor()
        0.25

        As usual, the "global" simulation step size of the |Timegrids|
        object of module |pub| is prefered:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "12h"
        >>> Parameter.get_timefactor()
        0.5

        .. testsetup::

            >>> del pub.timegrids
        """
        try:
            parameterstep = hydpy.pub.options.parameterstep
            parameterstep.check()
            parfactor = hydpy.pub.timegrids.parfactor
        except RuntimeError:
            options = hydpy.pub.options
            if not (options.parameterstep and options.simulationstep):
                raise RuntimeError(
                    "To calculate the conversion factor for adapting "
                    "the values of the time-dependent parameters, "
                    "you need to define both a parameter and a simulation "
                    "time step size first."
                ) from None
            date1 = timetools.Date("2000.01.01")
            date2 = date1 + options.simulationstep
            parfactor = timetools.Timegrids(
                timetools.Timegrid(
                    firstdate=date1, lastdate=date2, stepsize=options.simulationstep
                )
            ).parfactor
        return parfactor(parameterstep)

    def trim(self, lower=None, upper=None) -> bool:
        """Apply function |trim| of module |variabletools|."""
        return variabletools.trim(self, lower, upper)

    @classmethod
    def apply_timefactor(cls, values: ArrayFloat) -> ArrayFloat:
        """Change and return the given value(s) in accordance with
        |Parameter.get_timefactor| and the type of time-dependence
        of the actual parameter subclass.

        For the same conversion factor returned by method
        |Parameter.get_timefactor|, method |Parameter.apply_timefactor|
        behaves differently depending on the `TIME` attribute of the
        respective |Parameter| subclass.  We first prepare a parameter
        test class and define both the parameter and simulation step size:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     TIME = None
        >>> from hydpy import pub
        >>> pub.options.parameterstep = "1d"
        >>> pub.options.simulationstep = "6h"

        |None| means the value(s) of the parameter are not time-dependent
        (e.g. maximum storage capacity).  Hence, |Parameter.apply_timefactor|
        returns the original value(s):

        >>> Par.apply_timefactor(4.0)
        4.0

        |True| means the effective parameter value is proportional to
        the simulation step size (e.g. travel time). Hence,
        |Parameter.apply_timefactor| returns a reduced value in the
        next example (where the simulation step size is smaller than
        the parameter step size):

        >>> Par.TIME = True
        >>> Par.apply_timefactor(4.0)
        1.0

        |False| means the effective parameter value is inversely
        proportional to the simulation step size (e.g. storage
        coefficient). Hence, |Parameter.apply_timefactor| returns
        an increased value in the next example:

        >>> Par.TIME = False
        >>> Par.apply_timefactor(4.0)
        16.0
        """
        if cls.TIME is True:
            return values * cls.get_timefactor()
        if cls.TIME is False:
            return values / cls.get_timefactor()
        return values

    @classmethod
    def revert_timefactor(cls, values: ArrayFloat) -> ArrayFloat:
        """The inverse version of method |Parameter.apply_timefactor|.

        See the explanations on method Parameter.apply_timefactor| to
        understand the following examples:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     TIME = None
        >>> Par.parameterstep = "1d"
        >>> Par.simulationstep = "6h"
        >>> Par.revert_timefactor(4.0)
        4.0

        >>> Par.TIME = True
        >>> Par.revert_timefactor(4.0)
        16.0

        >>> Par.TIME = False
        >>> Par.revert_timefactor(4.0)
        1.0
        """
        if cls.TIME is True:
            return values / cls.get_timefactor()
        if cls.TIME is False:
            return values * cls.get_timefactor()
        return values

    def update(self) -> None:
        """To be overridden by all "secondary" parameters.

        |Parameter| subclasses to be used as "primary" parameters (control
        parameters) do not need to implement method |Parameter.update|.
        For such classes, invoking the method results in the following
        error message:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     pass
        >>> Par(None).update()
        Traceback (most recent call last):
        ...
        RuntimeError: Parameter `par` of element `?` does not \
implement method `update`.
        """
        raise RuntimeError(
            f"Parameter {objecttools.elementphrase(self)} does not "
            f"implement method `update`."
        )

    @property
    def keywordarguments(self) -> KeywordArguments:
        """A |KeywordArguments| object.

        By default, instances of |Parameter| subclasses return empty, invalid
        |KeywordArguments| objects:

        >>> from hydpy.core.parametertools import Keyword, KeywordArguments, Parameter
        >>> par = Parameter(None)
        >>> kwa = par.keywordarguments
        >>> kwa
        KeywordArguments()
        >>> kwa.valid
        False

        See class |ZipParameter| for an implementation example of a |Parameter|
        subclass overriding this behaviour.  Another example is class
        |musk_control.NmbSegments|, which relies on the following mechanism.

        Model developers can use the private `_keywordarguments` attribute.  Property
        |Parameter.keywordarguments| returns a deep copy of the |KeywordArguments|
        object stored here:

        >>> par._keywordarguments = KeywordArguments(x=1.0, y=2.0, z=3.0)
        >>> par.keywordarguments
        KeywordArguments(x=1.0, y=2.0, z=3.0)
        >>> par.keywordarguments is par._keywordarguments
        False

        We assume that the values of time-dependent keyword arguments stored under the
        private attribute refer to the simulation step size.  However, the values of
        the |KeywordArguments| object returned by |Parameter.keywordarguments| must
        refer to the current parameter step size.  If the relevant |Parameter| class
        provides |Keyword| instances that describe the individual keyword arguments,
        |Parameter.keywordarguments| can perform the necessary adjustments
        automatically:

        >>> par.KEYWORDS = {"x": Keyword(name="x", time=None),
        ...                 "y": Keyword(name="y", time=True),
        ...                 "z": Keyword(name="z", time=False)}
        >>> from hydpy import pub
        >>> with pub.options.simulationstep("1d"), pub.options.parameterstep("2d"):
        ...     par.keywordarguments
        KeywordArguments(x=1.0, y=4.0, z=1.5)
        """
        keywordarguments = copy.deepcopy(self._keywordarguments)
        for name, keyword in self.KEYWORDS.items():
            if keyword.time is not None:
                try:
                    value = keywordarguments[keyword.name]
                except KeyError:
                    continue
                if keyword.time is True:
                    keywordarguments[name] = value / self.get_timefactor()
                else:
                    keywordarguments[name] = value * self.get_timefactor()
        return keywordarguments

    def compress_repr(self) -> Optional[str]:
        """Try to find a compressed parameter value representation and return it.

        |Parameter.compress_repr| raises a |NotImplementedError| when failing to find a
        compressed representation.

        For the following examples, we define a 1-dimensional sequence handling
        time-dependent floating-point values:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Test(Parameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = True
        >>> test = Test(None)

        Before and directly after defining the parameter shape, `nan` is returned:

        >>> test.compress_repr()
        '?'
        >>> test
        test(?)
        >>> test.shape = 4
        >>> test
        test(?)

        Due to the time-dependence of the values of our test class, we need to specify
        a parameter and a simulation time step:

        >>> from hydpy import pub
        >>> pub.options.parameterstep = "1d"
        >>> pub.options.simulationstep = "8h"

        Compression succeeds when all required values are identical:

        >>> test(3.0, 3.0, 3.0, 3.0)
        >>> test.values
        array([1., 1., 1., 1.])
        >>> test.compress_repr()
        '3.0'
        >>> test
        test(3.0)

        Method |Parameter.compress_repr| returns |None| in case the required values are
        not identical:

        >>> test(1.0, 2.0, 3.0, 3.0)
        >>> test.compress_repr()
        >>> test
        test(1.0, 2.0, 3.0, 3.0)

        If some values are not required, indicate this by the `mask` descriptor:

        >>> import numpy
        >>> test(3.0, 3.0, 3.0, numpy.nan)
        >>> test
        test(3.0, 3.0, 3.0, nan)
        >>> Test.mask = numpy.array([True, True, True, False])
        >>> test
        test(3.0)

        If trying to access the mask results in an error, |Parameter.compress_repr|
        behaves as if no mask were available:

        >>> def getattribute(obj, name):
        ...     if name == 'mask':
        ...         raise BaseException
        ...     return object.__getattribute__(obj, name)
        >>> Test.__getattribute__ = getattribute
        >>> test
        test(3.0, 3.0, 3.0, nan)

        For a shape of zero, the string representing includes an empty list:

        >>> test.shape = 0
        >>> test.compress_repr()
        '[]'
        >>> test
        test([])

        Method |Parameter.compress_repr| works similarly for different |Parameter|
        subclasses.  The following examples focus on a 2-dimensional parameter handling
        integer values:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Test(Parameter):
        ...     NDIM = 2
        ...     TYPE = int
        ...     TIME = None
        >>> test = Test(None)

        >>> test.compress_repr()
        '?'
        >>> test
        test(?)
        >>> test.shape = (2, 3)
        >>> test
        test(?)

        >>> test([[3, 3, 3],
        ...       [3, 3, 3]])
        >>> test
        test(3)

        >>> test([[3, 3, -999999],
        ...       [3, 3, 3]])
        >>> test
        test([[3, 3, -999999],
              [3, 3, 3]])

        >>> Test.mask = numpy.array([
        ...     [True, True, False],
        ...     [True, True, True]])
        >>> test
        test(3)

        >>> test.shape = (0, 0)
        >>> test
        test([[]])
        """
        if not exceptiontools.attrready(self, "value"):
            return "?"
        if not self:
            return f"{self.NDIM * '['}{self.NDIM * ']'}"
        try:
            unique = numpy.unique(self[self.mask])
        except BaseException:
            unique = numpy.unique(self.values)
        if sum(numpy.isnan(unique)) == len(unique.flatten()):
            unique = numpy.array([numpy.nan])
        else:
            unique = self.revert_timefactor(unique)
        if len(unique) == 1:
            return objecttools.repr_(unique[0])
        return None

    def __repr__(self) -> str:
        if self.NDIM:
            values = self.compress_repr()
            if values is None:
                values = self.revert_timefactor(self.values)
            brackets = (isinstance(values, str) and (values == "?")) or (
                (self.NDIM == 2) and (self.shape[0] != 1)
            )
            return variabletools.to_repr(self, values, brackets)
        if exceptiontools.attrready(self, "value"):
            value = self.revert_timefactor(self.value)
        else:
            value = "?"
        return f"{self.name}({objecttools.repr_(value)})"


class _MixinModifiableParameter(Parameter):
    @classmethod
    def _reset_after_modification(cls, name: str, value: Optional[object]) -> None:
        if value is None:
            delattr(cls, name)
        else:
            setattr(cls, name, value)


class NameParameter(_MixinModifiableParameter, Parameter):
    """Parameter displaying the names of constants instead of their values.

    For demonstration, we define the test class `LandType`, covering three different
    types of land covering.  For this purpose, we need to prepare a dictionary of type
    |Constants| (class attribute `constants`), mapping the land type names to identity
    values.  The class attributes `NDIM`, `TYPE`, and `TIME` are already set to `1`,
    `int`, and `None` via base class |NameParameter|.  Furthermore, both `SPAN` tuple
    entries are `None` because |NameParameter| can perform checks against the available
    constants, which is more precise than only checking against the lowest and highest
    constant value:

    >>> from hydpy.core.parametertools import Constants, NameParameter
    >>> class LandType(NameParameter):
    ...     __name__ = "temp.py"
    ...     constants = Constants(SOIL=1, WATER=2, GLACIER=3)

    Additionally, we make the constants available within the local namespace (which is
    usually done by importing the constants from the selected application model
    automatically):

    >>> SOIL, WATER, GLACIER = 1, 2, 3

    For parameters of zero length, unprepared values, and identical required values,
    the string representations of |NameParameter| subclasses equal those of other
    |Parameter| subclasses:

    >>> landtype = LandType(None)
    >>> landtype.shape = 0
    >>> landtype
    landtype([])
    >>> landtype.shape = 5
    >>> landtype
    landtype(?)
    >>> landtype(SOIL)
    >>> landtype
    landtype(SOIL)

    For non-identical required values, class |NameParameter| replaces the identity
    values with their names:

    >>> landtype(SOIL, WATER, GLACIER, WATER, SOIL)
    >>> landtype
    landtype(SOIL, WATER, GLACIER, WATER, SOIL)

    For high numbers of entries, string representations are wrapped:

    >>> landtype.shape = 22
    >>> landtype(SOIL)
    >>> landtype.values[0] = WATER
    >>> landtype.values[-1] = GLACIER
    >>> landtype
    landtype(WATER, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL,
             SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL, SOIL,
             SOIL, GLACIER)
    """

    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (None, None)
    constants: Constants
    _possible_values: set[int]

    def __init__(self, subvars: SubParameters) -> None:
        super().__init__(subvars)
        self.constants = type(self).constants
        self._possible_values = set(self.constants.values())
        self._possible_values.add(variabletools.INT_NAN)

    @classmethod
    @contextlib.contextmanager
    def modify_constants(
        cls, constants: Optional[Constants]
    ) -> Generator[None, None, None]:
        """Modify the relevant constants temporarily.

        The constants for defining land-use types are fixed for typical "main models"
        like |hland|.  However, some submodels must take over the constants defined
        by their current main model, which are only known at runtime.  For example,
        consider the following simple `LandType` parameter that handles predefined
        constants as a class attribute:

        >>> from hydpy.core.parametertools import Constants, NameParameter
        >>> class LandType(NameParameter):
        ...     __name__ = "temp.py"
        ...     constants = Constants(SOIL=1, WATER=2, GLACIER=3)
        >>> SOIL, WATER, GLACIER = 1, 2, 3
        >>> landtype1 = LandType(None)
        >>> landtype1.shape = 3
        >>> landtype1(SOIL, WATER, SOIL)
        >>> landtype1
        landtype(SOIL, WATER, SOIL)

        We can use |NameParameter.modify_constants| to temporarily change these
        constants:

        >>> FIELD, FOREST = 1, 4
        >>> with LandType.modify_constants(Constants(FIELD=1, FOREST=4)):
        ...     landtype2 = LandType(None)
        ...     landtype2.shape = 4
        ...     landtype2(FOREST, FOREST, FIELD, FIELD)
        ...     landtype2
        landtype(FOREST, FOREST, FIELD, FIELD)

        During initialisation, these constants become an instance attribute, so the
        parameter instance does not forget them after leaving the `with` block (when
        the class attribute is reset to its previous value):

        >>> landtype1.constants
        {'SOIL': 1, 'WATER': 2, 'GLACIER': 3}
        >>> landtype2.constants
        {'FIELD': 1, 'FOREST': 4}
        >>> LandType.constants
        {'SOIL': 1, 'WATER': 2, 'GLACIER': 3}

        One can now use both parameter instances with their specific constants without
        the risk of impacting the other:

        >>> landtype1(SOIL, WATER, WATER)
        >>> landtype1
        landtype(SOIL, WATER, WATER)
        >>> landtype2
        landtype(FOREST, FOREST, FIELD, FIELD)

        >>> landtype2(FIELD, FOREST, FOREST, FIELD)
        >>> landtype2
        landtype(FIELD, FOREST, FOREST, FIELD)
        >>> landtype1
        landtype(SOIL, WATER, WATER)

        Passing |None| does not overwrite the default or the previously set references:

        >>> with LandType.modify_constants(None):
        ...     LandType.constants
        ...     landtype3 = LandType(None)
        ...     landtype3.shape = 4
        ...     landtype3(GLACIER, SOIL, GLACIER, WATER)
        ...     landtype3
        {'SOIL': 1, 'WATER': 2, 'GLACIER': 3}
        landtype(GLACIER, SOIL, GLACIER, WATER)
        >>> LandType.constants
        {'SOIL': 1, 'WATER': 2, 'GLACIER': 3}
        >>> landtype3
        landtype(GLACIER, SOIL, GLACIER, WATER)
        """
        if constants is None:
            yield
        else:
            old = vars(cls).get("constants")
            try:
                cls.constants = constants
                yield
            finally:
                cls._reset_after_modification("constants", old)

    def trim(self, lower=None, upper=None) -> bool:
        """Check if all previously set values comply with the supported constants.

        >>> from hydpy.core.parametertools import Constants, NameParameter
        >>> class LandType(NameParameter):
        ...     __name__ = "temp.py"
        ...     constants = Constants(SOIL=1, WATER=2, GLACIER=4)
        >>> SOIL, WATER, ROCK, GLACIER = 1, 2, 3, 4
        >>> landtype = LandType(None)
        >>> landtype.shape = 4
        >>> landtype(SOIL, WATER, ROCK, GLACIER)
        Traceback (most recent call last):
        ..
        ValueError: At least one value of parameter `landtype` of element `?` is not \
valid.
        >>> landtype
        landtype(SOIL, WATER, 3, GLACIER)
        """
        if hydpy.pub.options.trimvariables:
            if any(value not in self._possible_values for value in self._get_value()):
                raise ValueError(
                    f"At least one value of parameter "
                    f"{objecttools.elementphrase(self)} is not valid."
                )
        return False

    def __repr__(self) -> str:
        string = super().compress_repr()
        if string in ("?", "[]"):
            return f"{self.name}({string})"
        if string is None:
            values = self.values
        else:
            values = [int(string)]
        get = self.constants.value2name.get
        names = tuple(get(value, repr(value)) for value in values)
        string = objecttools.assignrepr_values(
            values=names, prefix=f"{self.name}(", width=70
        )
        return f"{string})"


class ZipParameter(_MixinModifiableParameter, Parameter):
    """Base class for 1-dimensional model parameters that offers an additional
    keyword-based zipping functionality.

    Many models implemented in the *HydPy* framework realise the concept of hydrological
    response units via 1-dimensional |Parameter| objects, each entry corresponding with
    an individual unit.  To allow for a maximum of flexibility, one can define their
    values independently, which allows, for example, for applying arbitrary
    relationships between the altitude of individual response units and a precipitation
    correction factor to be parameterised.

    However, very often, hydrological modellers set identical values for different
    hydrological response units of the same type. One could, for example, set the same
    leaf area index for all units of the same land-use type.  Class |ZipParameter|
    allows defining parameters, which conveniently support this parameterisation
    strategy.

    .. testsetup::

        >>> from hydpy import pub
        >>> del pub.options.simulationstep

    To see how base class |ZipParameter| works, we need to create some additional
    subclasses.  First, we need a parameter defining the type of the individual
    hydrological response units, which can be done by subclassing from |NameParameter|.
    We do so by taking the example from the documentation of the |NameParameter| class:

    >>> from hydpy.core.parametertools import NameParameter
    >>> SOIL, WATER, GLACIER = 1, 2, 3
    >>> class LandType(NameParameter):
    ...     SPAN = (1, 3)
    ...     constants = {"SOIL":  SOIL, "WATER": WATER, "GLACIER": GLACIER}
    >>> landtype = LandType(None)

    Second, we need an |IndexMask| subclass.  Our subclass `Land` references the
    respective `LandType` parameter object (we do this in a simplified manner, see class
    |hland_parameters.ParameterComplete| for a "real world" example) but is supposed to
    focus on the response units of type `soil` or `glacier` only:

    >>> from hydpy.core.masktools import IndexMask
    >>> class Land(IndexMask):
    ...     relevant = (SOIL, GLACIER)
    ...     @staticmethod
    ...     def get_refindices(variable):
    ...         return variable.landtype

    Third, we prepare the actual |ZipParameter| subclass, holding the same `constants`
    dictionary as the `LandType` parameter and the `Land` mask as attributes.  We assume
    that the values of our test class `Par` are time-dependent and set different
    parameter and simulation step sizes, to show that the related value adjustments
    work.  Also, we make the `LandType` object available via attribute access, which is
    a hack to make the above simplification work:

    >>> from hydpy.core.parametertools import ZipParameter
    >>> class Par(ZipParameter):
    ...     TYPE = float
    ...     TIME = True
    ...     SPAN = (0.0, None)
    ...     constants = LandType.constants
    ...     mask = Land()
    ...     landtype = landtype
    >>> par = Par(None)
    >>> from hydpy import pub
    >>> pub.options.parameterstep = "1d"
    >>> pub.options.simulationstep = "12h"

    For parameters with zero-length or with unprepared or identical parameter values,
    the string representation looks as usual:

    >>> landtype.shape = 0
    >>> par.shape = 0
    >>> par
    par([])
    >>> landtype.shape = 5
    >>> landtype(SOIL, WATER, GLACIER, WATER, SOIL)
    >>> par.shape = 5
    >>> par
    par(?)
    >>> par(2.0)
    >>> par
    par(2.0)
    >>> par.values
    array([1., 1., 1., 1., 1.])

    The extended feature of class |ZipParameter| is to allow passing values via
    keywords, each keyword corresponding to one of the relevant constants (in our
    example: `SOIL` and `GLACIER`) in lower case letters:

    >>> par(soil=4.0, glacier=6.0)
    >>> par
    par(glacier=6.0, soil=4.0)
    >>> par.values
    array([ 2., nan,  3., nan,  2.])

    Use the `default` argument if you want to assign the same value to entries with
    different constants:

    >>> par(soil=2.0, default=8.0)
    >>> par
    par(glacier=8.0, soil=2.0)
    >>> par.values
    array([ 1., nan,  4., nan,  1.])

    Using a keyword argument corresponding to an existing, but not relevant constant (in
    our example: `WATER`) is silently ignored:

    >>> par(soil=4.0, glacier=6.0, water=8.0)
    >>> par
    par(glacier=6.0, soil=4.0)
    >>> par.values
    array([ 2., nan,  3., nan,  2.])

    However, using a keyword not corresponding to any constant raises an exception:

    >>> par(soil=4.0, glacier=6.0, wrong=8.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `par` of element `?` based \
on keyword arguments `soil, glacier, and wrong`, the following error occurred: Keyword \
`wrong` is not among the available model constants.

    The same is true when passing incomplete information:

    >>> par(soil=4.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `par` of element `?` based \
on keyword arguments `soil`, the following error occurred: The given keywords are \
incomplete and no default value is available.

    Values exceeding the bounds defined by class attribute `SPAN` are trimmed as usual:

    >>> from hydpy import pub
    >>> with pub.options.warntrim(False):
    ...     par(soil=-10.0, glacier=10.0)
    >>> par
    par(glacier=10.0, soil=0.0)

    For convenience, you can get or set all values related to a specific constant via
    attribute access:

    >>> par.soil
    array([0., 0.])
    >>> par.soil = 2.5
    >>> par
    par(glacier=10.0, soil=5.0)

    Improper use of these "special attributes" results in errors like the following:

    >>> par.Soil  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    AttributeError: `Soil` is neither a normal attribute of parameter `par` of element \
`?` nor among the following special attributes: soil, water, and glacier...

    >>> par.soil = "test"
    Traceback (most recent call last):
    ...
    ValueError: While trying the set the value(s) of parameter `par` of element `?` \
related to the special attribute `soil`, the following error occurred: could not \
convert string to float: 'test'
    """

    NDIM = 1
    constants: dict[str, int]
    """Mapping of the constants' names and values."""
    refindices: Optional[NameParameter] = None
    """Optional reference to the relevant index parameter."""
    relevant: Optional[tuple[int, ...]] = None
    """The values of all (potentially) relevant constants."""
    mask: masktools.IndexMask

    @classmethod
    @contextlib.contextmanager
    def modify_refindices(
        cls, refindices: Optional[NameParameter]
    ) -> Generator[None, None, None]:
        """Eventually, set or modify the reference to the required index parameter.

        The following example demonstrates that changes affect the relevant class only
        temporarily, but its objects initialised within the "with" block persistently:


        >>> from hydpy.core.variabletools import FastAccess, Variable
        >>> GRASS, TREES, WATER = 0, 1, 2
        >>> class RefPar(Variable):
        ...     NDIM = 1
        ...     TYPE = int
        ...     TIME = None
        ...     initinfo = 0, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        ...     constants = {"GRASS": GRASS, "TREES": TREES, "WATER": WATER}
        ...     relevant = (0, 1, 2)
        >>> from hydpy.core.parametertools import ZipParameter
        >>> from hydpy.core.masktools import SubmodelIndexMask
        >>> class ZipPar(ZipParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        ...     initinfo = 0.0, True
        ...     _CLS_FASTACCESS_PYTHON = FastAccess
        ...     constants = {"FIELD": 1, "FOREST": 3}
        ...     relevant = (1, 3)
        ...     mask = SubmodelIndexMask()
        >>> refpar = RefPar(None)
        >>> refpar.shape = 3
        >>> refpar(1, 2, 1)
        >>> with ZipPar.modify_refindices(refpar):
        ...     ZipPar.refindices.name
        ...     ZipPar.constants
        ...     ZipPar.relevant
        ...     zippar1 = ZipPar(None)
        ...     zippar1.shape = 3
        ...     zippar1(water=1.0, default=2.)
        ...     zippar1
        'refpar'
        {'GRASS': 0, 'TREES': 1, 'WATER': 2}
        (0, 1, 2)
        zippar(trees=2.0, water=1.0)

        >>> ZipPar.refindices
        >>> ZipPar.constants
        {'FIELD': 1, 'FOREST': 3}
        >>> ZipPar.relevant
        (1, 3)
        >>> zippar1
        zippar(trees=2.0, water=1.0)

        Passing |None| does not overwrite previously set references:

        >>> with ZipPar.modify_refindices(None):
        ...     ZipPar.refindices
        ...     ZipPar.constants
        ...     ZipPar.relevant
        {'FIELD': 1, 'FOREST': 3}
        (1, 3)

        >>> with ZipPar.modify_refindices(None):
        ...     zippar2 = ZipPar(None)
        ...     zippar2.shape = 3
        ...     zippar2(water=1.0, default=2.)
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to set the values of parameter `zippar` of element \
`?` based on keyword arguments `water and default`, the following error occurred: \
Variable `zippar` of element `?` does currently not reference an instance-specific \
index parameter.

        >>> ZipPar.refindices
        >>> ZipPar.constants
        {'FIELD': 1, 'FOREST': 3}
        >>> ZipPar.relevant
        (1, 3)
        """
        if refindices is None:
            yield
        else:
            get = vars(cls).get
            old_refindices = get("refindices")
            old_constants = get("constants")
            old_relevant = get("relevant")
            try:
                cls.refindices = refindices
                cls.constants = refindices.constants
                cls.relevant = tuple(refindices.constants.values())
                yield
            finally:
                cls._reset_after_modification("refindices", old_refindices)
                cls._reset_after_modification("constants", old_constants)
                cls._reset_after_modification("relevant", old_relevant)

    def __init__(self, subvars: SubParameters) -> None:
        super().__init__(subvars)
        self.refindices = type(self).refindices
        self.constants = type(self).constants
        self.relevant = type(self).relevant

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            try:
                self._own_call(kwargs)
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to set the values of parameter "
                    f"{objecttools.elementphrase(self)} based on keyword arguments "
                    f"`{objecttools.enumeration(kwargs)}`"
                )

    def _own_call(self, kwargs: dict[str, Any]) -> None:
        mask = self.mask
        self._set_value(numpy.nan)
        values = self._get_value()
        allidxs = mask.refindices.values
        relidxs = mask.narrow_relevant(relevant=self.relevant)
        counter = 0
        if "default" in kwargs:
            check = False
            values[mask] = kwargs.pop("default")
        else:
            check = True
        for key, value in kwargs.items():
            try:
                selidx = self.constants[key.upper()]
                if selidx in relidxs:
                    values[allidxs == selidx] = value
                    counter += 1
            except KeyError:
                raise TypeError(
                    f"Keyword `{key}` is not among the " f"available model constants."
                ) from None
        if check and (counter < len(relidxs)):
            raise TypeError(
                "The given keywords are incomplete and no default value is available."
            )
        values[:] = self.apply_timefactor(values)
        self.trim()

    @property
    def keywordarguments(self) -> KeywordArguments[float]:
        """A |KeywordArguments| object providing the currently valid keyword arguments.

        We take parameter |lland_control.TRefT| of application model |lland_dd| as an
        example and set its shape (the number of hydrological response units defined by
        parameter |lland_control.NHRU|) to four and prepare the land use types
        |lland_constants.ACKER| (acre), |lland_constants.LAUBW| (deciduous forest), and
        |lland_constants.WASSER| (water) via parameter |lland_control.Lnk|:

        >>> from hydpy.models.lland_dd import *
        >>> parameterstep()
        >>> nhru(4)
        >>> lnk(ACKER, LAUBW, WASSER, ACKER)

        After defining all required values via keyword arguments (note that parameter
        |lland_control.TRefT| does not need any values for response units of type
        |lland_constants.WASSER|), property |ZipParameter.keywordarguments| makes
        exactly these keywords arguments available:

        >>> treft(acker=2.0, laubw=1.0)
        >>> treft.keywordarguments
        KeywordArguments(acker=2.0, laubw=1.0)
        >>> treft.keywordarguments.valid
        True

        In the following example, both the first and the fourth response unit are of
        type |lland_constants.ACKER| but have different |lland_control.TRefT| values,
        which cannot be the result of defining values via keyword arguments.  Hence, the
        returned |KeywordArguments| object is invalid:

        >>> treft(1.0, 2.0, 3.0, 4.0)
        >>> treft.keywordarguments
        KeywordArguments()
        >>> treft.keywordarguments.valid
        False

        This is different from the situation where all response units are of type
        |lland_constants.WASSER|, where one does not need to define any values for
        parameter |lland_control.TRefT|.  Thus, the returned |KeywordArguments| object
        is also empty but valid:

        >>> lnk(WASSER)
        >>> treft.keywordarguments
        KeywordArguments()
        >>> treft.keywordarguments.valid
        True

        ToDo: document "refinement" asa lland_dd uses the AETModel_V1 interface
        """
        try:
            mask = self.mask
        except BaseException:
            return KeywordArguments(False)
        if (refinement := mask.refinement) is None:
            refindices = mask.refindices.values
        else:
            refindices = mask.refindices.values.copy()
            refindices[~refinement.values] = variabletools.INT_NAN
        name2unique = KeywordArguments[Union[float]]()
        if (relevant := self.relevant) is None:
            relevant = mask.relevant
        for key, value in self.constants.items():
            if value in relevant:
                unique = numpy.unique(self.values[refindices == value])
                unique = self.revert_timefactor(unique)
                length = len(unique)
                if length == 1:
                    name2unique[key.lower()] = unique[0]
                elif length > 1:
                    return KeywordArguments(False)
        return name2unique

    def __getattr__(self, name: str):
        name_ = name.upper()
        if (not name.islower()) or (name_ not in self.constants):
            names = objecttools.enumeration(
                key.lower() for key in self.constants.keys()
            )
            raise AttributeError(
                f"`{name}` is neither a normal attribute of parameter "
                f"{objecttools.elementphrase(self)} nor among the following special "
                f"attributes: {names}."
            )
        sel_constant = self.constants[name_]
        used_constants = self.mask.refindices.values
        return self.values[used_constants == sel_constant]

    def __setattr__(self, name: str, value):
        name_ = name.upper()
        if name.islower() and (name_ in (constants := self.constants)):
            try:
                sel_constant = constants[name_]
                used_constants = self.mask.refindices.values
                self.values[used_constants == sel_constant] = value
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying the set the value(s) of parameter "
                    f"{objecttools.elementphrase(self)} related to the special "
                    f"attribute `{name}`"
                )
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        string = self.compress_repr()
        if string is not None:
            return f"{self.name}({string})"
        keywordarguments = self.keywordarguments
        if not keywordarguments.valid:
            return super().__repr__()
        results = [
            f"{name}={objecttools.repr_(value)}" for name, value in keywordarguments
        ]
        string = objecttools.assignrepr_values(
            values=sorted(results), prefix=f"{self.name}(", width=70
        )
        return f"{string})"

    def __dir__(self) -> list[str]:
        """
        >>> from hydpy.models.lland_dd import *
        >>> parameterstep()
        >>> sorted(set(dir(treft)) - set(object.__dir__(treft)))
        ['acker', 'baumb', 'boden', 'feucht', 'fluss', 'glets', 'grue_e', 'grue_i', \
'laubw', 'mischw', 'nadelw', 'obstb', 'see', 'sied_d', 'sied_l', 'vers', 'wasser', \
'weinb']
        """
        names = itertools.chain(
            cast(list[str], super().__dir__()),
            (key.lower() for key in self.constants.keys()),
        )
        return list(names)


class SeasonalParameter(Parameter):
    """Base class for parameters handling values showing a seasonal variation.

    Quite a lot of model parameter values change on an annual basis.  One example is
    the leaf area index.  For deciduous forests within temperate climatic regions, it
    shows a clear peak during the summer season.

    If you want to vary the parameter values on a fixed (for example, a monthly) basis,
    |KeywordParameter2D| might be the best starting point.  See the
    |lland_parameters.LanduseMonthParameter| class of the |lland| base model as an
    example, which is used to define parameter |lland_control.LAI|, handling monthly
    leaf area index values for different land-use classes.

    However, class |SeasonalParameter| offers more flexibility in defining seasonal
    patterns, which is often helpful for modelling technical control systems.  One
    example is the parameter |dam_control.TargetVolume| of base model |dam| for
    determining a dam's desired volume throughout the year.

    .. testsetup::

        >>> from hydpy import pub
        >>> del pub.options.simulationstep

    For the following examples, we assume a simulation step size of one day:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"

    Let us prepare an empty 1-dimensional |SeasonalParameter| instance:

    >>> from hydpy.core.parametertools import SeasonalParameter
    >>> class Par(SeasonalParameter):
    ...     NDIM = 1
    ...     TIME = None
    >>> par = Par(None)
    >>> par.NDIM = 1
    >>> par
    par()

    The shape is determined automatically, as described in the documentation on
    property |SeasonalParameter.shape| in more detail:

    >>> par.shape = (None,)
    >>> par.shape
    (366,)

    Pairs of |TOY| objects and |float| values define the seasonal pattern.  One can
    assign them all at once via keyword arguments:

    >>> par(_1=2., _7_1=4., _3_1_0_0_0=5.)

    Note that all keywords in the call above are proper |TOY| initialisation arguments.
    Misspelt keywords result in error messages like the following:

    >>> Par(None)(_a=1.)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the seasonal parameter value `par` of element \
`?` for time of year `_a`, the following error occurred: While trying to initialise a \
TOY object based on argument value `_a` of type `str`, the following error occurred: \
While trying to retrieve the month, the following error occurred: For TOY (time of \
year) objects, all properties must be of type `int`, but the value `a` of type `str` \
given for property `month` cannot be converted to `int`.

    As the following string representation shows are the pairs of each
    |SeasonalParameter| instance automatically sorted:

    >>> par
    par(toy_1_1_0_0_0=2.0,
        toy_3_1_0_0_0=5.0,
        toy_7_1_0_0_0=4.0)

    By default, `toy` is used as a prefix string.  Using this prefix string, one can
    change the toy-value pairs via attribute access:

    >>> par.toy_1_1_0_0_0
    2.0
    >>> del par.toy_1_1_0_0_0
    >>> par.toy_2_1_0_0_0 = 2.
    >>> par
    par(toy_2_1_0_0_0=2.0,
        toy_3_1_0_0_0=5.0,
        toy_7_1_0_0_0=4.0)

    For attribute access, zero hours, minutes, or seconds can be left out:

    >>> par.toy_2_1
    2.0

    When using functions |getattr| and |delattr|, one can also omit the "toy" prefix:

    >>> getattr(par, "2_1")
    2.0
    >>> delattr(par, "2_1")
    >>> getattr(par, "2_1")
    Traceback (most recent call last):
    ...
    AttributeError: Seasonal parameter `par` of element `?` has neither a normal \
attribute nor does it handle a "time of year" named `2_1`.
    >>> delattr(par, "2_1")
    Traceback (most recent call last):
    ...
    AttributeError: Seasonal parameter `par` of element `?` has neither a normal \
attribute nor does it handle a "time of year" named `2_1`.

    Applying the |len| operator on |SeasonalParameter| objects returns the number of
    toy-value pairs.

    >>> len(par)
    2

    New values are checked to be compatible with the predefined shape:

    >>> par.toy_1_1_0_0_0 = [1., 2.]   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: While trying to add a new or change an existing toy-value pair for the \
seasonal parameter `par` of element `?`, the following error occurred: float() \
argument must be a string or a... number...
    >>> par = Par(None)
    >>> par.NDIM = 2
    >>> par.shape = (None, 3)
    >>> par.toy_1_1_0_0_0 = [1., 2.]
    Traceback (most recent call last):
    ...
    ValueError: While trying to add a new or change an existing toy-value pair for \
the seasonal parameter `par` of element `?`, the following error occurred: could not \
broadcast input array from shape (2,) into shape (3,)

    If you do not require seasonally varying parameter values in a specific situation,
    you can pass a single positional argument:

    >>> par(5.0)
    >>> par
    par([5.0, 5.0, 5.0])

    Note that class |SeasonalParameter| associates the given value(s) to the "first"
    time of the year internally:

    >>> par.toys
    (TOY("1_1_0_0_0"),)

    Incompatible positional arguments result in errors like the following:

    >>> par(1.0, 2.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `par`, the following \
error occurred: While trying to convert the value(s) `[1. 2.]` to a numpy ndarray \
with shape `(366, 3)` and type `float`, the following error occurred: could not \
broadcast input array from shape (2,) into shape (366,3)

    .. testsetup::

        >>> del pub.timegrids
    """

    TYPE = float

    strict_valuehandling: bool = False

    _toy2values_unprotected: list[tuple[timetools.TOY, Union[float, NDArrayFloat]]]
    _trimmed_insufficiently: bool
    _trimming_disabled: bool

    def __init__(self, subvars) -> None:
        super().__init__(subvars)
        self._toy2values_unprotected = []
        self._trimming_disabled = False
        self._trimmed_insufficiently = False

    @property
    def _toy2values_protected(
        self,
    ) -> list[tuple[timetools.TOY, Union[float, NDArrayFloat]]]:
        if self._trimmed_insufficiently and hydpy.pub.options.warntrim:
            warnings.warn(
                f'The "background values" of parameter '
                f"{objecttools.elementphrase(self)} have been trimmed but not its "
                f"original time of year-specific values.  Using the latter without "
                f"modification might result in inconsistencies."
            )
        return self._toy2values_unprotected

    def __call__(self, *args, **kwargs) -> None:
        if self.NDIM == 1:
            self.shape = (-1,)
        try:
            try:
                self._trimming_disabled = True
                super().__call__(*args, **kwargs)
            finally:
                self._trimming_disabled = False
            self._toy2values_unprotected = [(timetools.TOY(), self.values[0])]
            self.trim()
        except BaseException as exc:
            self._toy2values_unprotected = []
            if args:
                raise exc
            for toystr, values in kwargs.items():
                try:
                    self._add_toyvaluepair(toystr, values)
                except BaseException:
                    objecttools.augment_excmessage(
                        f"While trying to define the seasonal parameter value "
                        f"{objecttools.elementphrase(self)} for time of year `{toystr}`"
                    )
            self.refresh()

    def _add_toyvaluepair(self, name: str, value: Union[float, NDArrayFloat]) -> None:
        if self.NDIM == 1:
            value = float(value)
        else:
            value = numpy.full(self.shape[1:], value)
        toy_new = timetools.TOY(name)
        toy2values = self._toy2values_unprotected
        if len(toy2values) == 0:
            toy2values.append((toy_new, value))
        secs_new = toy_new.seconds_passed
        if secs_new > toy2values[-1][0].seconds_passed:
            toy2values.append((toy_new, value))
        else:
            for idx, (toy_old, _) in enumerate(toy2values[:]):
                secs_old = toy_old.seconds_passed
                if secs_new == secs_old:
                    toy2values[idx] = toy_new, value
                    break
                if secs_new < secs_old:
                    toy2values.insert(idx, (toy_new, value))
                    break

    def refresh(self) -> None:
        """Update the actual simulation values based on the toy-value pairs.

        Usually, one does not need to call refresh explicitly.  The "magic" methods
        `__call__`, `__setattr__`, and `__delattr__` invoke it automatically, when
        required.

        Method |SeasonalParameter.refresh| calculates only those time variable
        parameter values required for the defined initialisation period.  We start with
        an initialisation period covering a full year, making a complete calculation
        necessary:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"

        Instantiate a 1-dimensional |SeasonalParameter| object:

        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        >>> par = Par(None)
        >>> par.shape = (None,)

        When a |SeasonalParameter| object does not contain any toy-value pairs yet, the
        method |SeasonalParameter.refresh| sets all actual simulation values to zero:

        >>> par.values = 1.0
        >>> par.refresh()
        >>> par.values[0]
        0.0

        When there is only one toy-value pair, its values are relevant for all actual
        simulation values:

        >>> par.toy_1 = 2.0  # calls refresh automatically
        >>> par.values[0]
        2.0

        Method |SeasonalParameter.refresh| performs a linear interpolation for the
        central time points of each simulation time step.  Hence, in the following
        example, the original values of the toy-value pairs do not show up:

        >>> par.toy_12_31 = 4.0
        >>> from hydpy import round_
        >>> round_(par.values[0])
        2.00274
        >>> round_(par.values[-2])
        3.99726
        >>> par.values[-1]
        3.0

        If one wants to preserve the original values in this example, one must set the
        corresponding toy instances in the middle of some simulation step intervals:

        >>> del par.toy_1
        >>> del par.toy_12_31
        >>> par.toy_1_1_12 = 2
        >>> par.toy_12_31_12 = 4.0
        >>> par.values[0]
        2.0
        >>> round_(par.values[1])
        2.005479
        >>> round_(par.values[-2])
        3.994521
        >>> par.values[-1]
        4.0

        For short initialisation periods, method |SeasonalParameter.refresh| performs
        only the required interpolations for efficiency:

        >>> pub.timegrids = "2000-01-02", "2000-01-05", "1d"
        >>> Par.NDIM = 2
        >>> par = Par(None)
        >>> par.shape = (None, 3)
        >>> par.toy_1_2_12 = 2.0
        >>> par.toy_1_6_12 = 0.0, 2.0, 4.0
        >>> par.values[:6]
        array([[nan, nan, nan],
               [2. , 2. , 2. ],
               [1.5, 2. , 2.5],
               [1. , 2. , 3. ],
               [nan, nan, nan],
               [nan, nan, nan]])

        .. testsetup::

            >>> del pub.timegrids
        """
        toy2values = self._toy2values_unprotected
        if not toy2values:
            self._set_value(0.0)
        elif len(self) == 1:
            self.values[:] = self.apply_timefactor(toy2values[0][1])
        else:
            centred = timetools.TOY.centred_timegrid()
            values = self._get_value()
            for idx, (date, rel) in enumerate(zip(*centred)):
                values[idx] = self.interp(date) if rel else numpy.nan
            values = self.apply_timefactor(values)
            self._set_value(values)
        self.trim()

    def interp(self, date: timetools.Date) -> float:
        """Perform a linear value interpolation for the given `date` and return the
        result.

        Instantiate a 1-dimensional |SeasonalParameter| object:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        >>> par = Par(None)
        >>> par.shape = (None,)

        Define three toy-value pairs:

        >>> par(_1=2.0, _2=5.0, _12_31=4.0)

        Passing a |Date| object matching a |TOY| object exactly returns the
        corresponding |float| value:

        >>> from hydpy import Date
        >>> par.interp(Date("2000.01.01"))
        2.0
        >>> par.interp(Date("2000.02.01"))
        5.0
        >>> par.interp(Date("2000.12.31"))
        4.0

        For all intermediate points, |SeasonalParameter.interp| performs a linear
        interpolation:

        >>> from hydpy import round_
        >>> round_(par.interp(Date("2000.01.02")))
        2.096774
        >>> round_(par.interp(Date("2000.01.31")))
        4.903226
        >>> round_(par.interp(Date("2000.02.02")))
        4.997006
        >>> round_(par.interp(Date("2000.12.30")))
        4.002994

        Linear interpolation is also allowed between the first and the last pair when
        they do not capture the endpoints of the year:

        >>> par(_1_2=2.0, _12_30=4.0)
        >>> round_(par.interp(Date("2000.12.29")))
        3.99449
        >>> par.interp(Date("2000.12.30"))
        4.0
        >>> round_(par.interp(Date("2000.12.31")))
        3.333333
        >>> round_(par.interp(Date("2000.01.01")))
        2.666667
        >>> par.interp(Date("2000.01.02"))
        2.0
        >>> round_(par.interp(Date("2000.01.03")))
        2.00551

        The following example briefly shows interpolation performed for a 2-dimensional
        parameter:

        >>> Par.NDIM = 2
        >>> par = Par(None)
        >>> par.shape = (None, 2)
        >>> par(_1_1=[1., 2.], _1_3=[-3, 0.])
        >>> result = par.interp(Date("2000.01.02"))
        >>> round_(result[0])
        -1.0
        >>> round_(result[1])
        1.0

        .. testsetup::

            >>> del pub.timegrids
        """
        xnew = timetools.TOY(date)
        xys = list(self)
        for idx, (x1, y1) in enumerate(xys):
            if x1 > xnew:
                x0, y0 = xys[idx - 1]
                break
        else:
            x0, y0 = xys[-1]
            x1, y1 = xys[0]
        return y0 + (y1 - y0) / (x1 - x0) * (xnew - x0)

    @property
    def toys(self) -> tuple[timetools.TOY, ...]:
        """A sorted |tuple| of all contained |TOY| objects."""
        return tuple(toy for toy, _ in self._toy2values_unprotected)

    def _get_shape(self) -> tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.options.simulationstep

        Setting the shape of |SeasonalParameter| objects differs from setting the shape
        of other |Variable| subclasses, due to handling time on the first axis.  The
        simulation step size determines the length of this axis.  Hence, trying to set
        the shape before the simulation step size is known does not work:

        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        >>> par = Par(None)
        >>> par.shape = (None,)
        Traceback (most recent call last):
        ...
        RuntimeError: It is not possible the set the shape of the seasonal parameter \
`par` of element `?` at the moment.  You need to define the simulation step size \
first.  However, in complete HydPy projects this stepsize is indirectly defined via \
`pub.timegrids.stepsize` automatically.

        After preparing the simulation step size, you can pass a tuple with a single
        entry of any value to define the shape of the defined 1-dimensional test class.
        Property |SeasonalParameter.shape| replaces this arbitrary value by the number
        of simulation steps fitting into a leap year:

        >>> from hydpy import pub
        >>> pub.options.simulationstep = "1d"
        >>> par.shape = (123,)
        >>> par.shape
        (366,)

        Assigning a single, arbitrary value also works well:

        >>> par.shape = None
        >>> par.shape
        (366,)

        For higher-dimensional parameters, property |SeasonalParameter.shape| replaces
        the first entry of the assigned iterable, accordingly:

        >>> Par.NDIM = 2
        >>> par.shape = (None, 3)
        >>> par.shape
        (366, 3)

        For simulation steps not cleanly fitting into a leap year, the ceil-operation
        determines the number of entries:

        >>> pub.options.simulationstep = "100d"
        >>> par.shape = (None, 3)
        >>> par.shape
        (4, 3)
        """
        return super()._get_shape()

    def _set_shape(self, shape: Union[int, tuple[int, ...]]) -> None:
        if isinstance(shape, tuple):
            shape_ = list(shape)
        else:
            shape_ = [-1]
        simulationstep = hydpy.pub.options.simulationstep
        if not simulationstep:
            raise RuntimeError(
                f"It is not possible the set the shape of the seasonal parameter "
                f"{objecttools.elementphrase(self)} at the moment.  You need to "
                f"define the simulation step size first.  However, in complete HydPy "
                f"projects this stepsize is indirectly defined via "
                f"`pub.timegrids.stepsize` automatically."
            )
        shape_[0] = int(numpy.ceil(timetools.Period("366d") / simulationstep))
        shape_[0] = int(numpy.ceil(round(shape_[0], 10)))
        super()._set_shape(tuple(shape_))

    shape = propertytools.Property(fget=_get_shape, fset=_set_shape)

    def trim(self, lower=None, upper=None) -> bool:
        """Extend the usual trim logic with a warning mechanism to account for that
        trimming only affects "background values" and not the "visible" time of year /
        value pairs.

        The usual trimming process affects the simulation-relevant "background values",
        not the "visible" original values supplied by the user.  Hence,
        |SeasonalParameter| tries to keep track of recent trimmings to warn if users
        try to used the unmodified "visible" values later:

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"
        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> upperlowwaterthreshold.shape = 1
        >>> upperlowwaterthreshold.values[:3] = 1.0, 2.0, 3.0
        >>> bottomlowwaterthreshold(2.0)
        >>> round_(bottomlowwaterthreshold.values[:3])
        1.0, 2.0, 2.0
        >>> from hydpy.core.testtools import warn_later
        >>> with pub.options.warntrim(True), warn_later():
        ...     bottomlowwaterthreshold
        bottomlowwaterthreshold(2.0)
        UserWarning: The "background values" of parameter `bottomlowwaterthreshold` \
of element `?` have been trimmed but not its original time of year-specific values.  \
Using the latter without modification might result in inconsistencies.

        In such cases, modify the values of the affected parameter or its boundaries
        and call |SeasonalParameter.refresh| manually.  If successful, the warning
        disappears:

        >>> upperlowwaterthreshold.values[0] = 2.0
        >>> bottomlowwaterthreshold.refresh()
        >>> with pub.options.warntrim(True):
        ...     bottomlowwaterthreshold
        bottomlowwaterthreshold(2.0)

        The explained mechanism equivalently works when defining seasonally varying
        parameter values and trying to access the unmodified "visible" values in other
        ways:

        >>> bottomlowwaterthreshold(_1_1_12=3.0, _1_3_12=1.0)
        >>> round_(bottomlowwaterthreshold.values[:3])
        2.0, 2.0, 1.0
        >>> with pub.options.warntrim(True), warn_later():
        ...     round_(bottomlowwaterthreshold.toy_1_1_12)  # doctest: +ELLIPSIS
        3.0
        UserWarning: The "background values"...result in inconsistencies.
        >>> with pub.options.warntrim(True), warn_later():
        ...     tuple(bottomlowwaterthreshold)  # doctest: +ELLIPSIS
        ((TOY("1_1_12_0_0"), 3.0), (TOY("1_3_12_0_0"), 1.0))
        UserWarning: The "background values"...result in inconsistencies.
        >>> with pub.options.warntrim(True), warn_later():
        ...     len(bottomlowwaterthreshold)  # doctest: +ELLIPSIS
        2
        UserWarning: The "background values"...result in inconsistencies.

        .. testsetup::

            >>> del pub.timegrids
        """
        if not self._trimming_disabled:
            self._trimmed_insufficiently = super().trim(lower, upper)
        return self._trimmed_insufficiently

    def __iter__(self) -> Iterator[tuple[timetools.TOY, Any]]:
        return iter(self._toy2values_protected)

    def __getattr__(self, name: str) -> Union[float, NDArrayFloat]:
        selected = timetools.TOY(name)
        for available, value in self._toy2values_protected:
            if selected == available:
                return value
        raise AttributeError(
            f"Seasonal parameter {objecttools.elementphrase(self)} has neither a "
            f'normal attribute nor does it handle a "time of year" named `{name}`.'
        )

    def __setattr__(self, name: str, value: Union[float, NDArrayFloat]) -> None:
        if name.startswith("toy_"):
            try:
                self._add_toyvaluepair(name, value)
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to add a new or change an existing toy-value pair "
                    f"for the seasonal parameter {objecttools.elementphrase(self)}"
                )
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        try:
            super().__delattr__(name)
        except AttributeError:
            selected = timetools.TOY(name)
            for idx, (available, _) in enumerate(self._toy2values_unprotected):
                if selected == available:
                    break
            else:
                raise AttributeError(
                    f"Seasonal parameter {objecttools.elementphrase(self)} has "
                    f'neither a normal attribute nor does it handle a "time of year" '
                    f"named `{name}`."
                ) from None
            del self._toy2values_unprotected[idx]
            self.refresh()

    def __repr__(self) -> str:
        def _assignrepr(value_, prefix_):
            if self.NDIM == 1:
                return objecttools.assignrepr_value(value_, prefix_)
            return objecttools.assignrepr_list(value_, prefix_, width=79)

        toy2values = self._toy2values_protected
        if not toy2values:
            return f"{self.name}()"
        toy0 = timetools.TOY0
        if (len(self) == 1) and (toy0 == toy2values[0][0]):
            return f'{_assignrepr(toy2values[0][1], f"{self.name}(")})'
        lines = []
        blanks = " " * (len(self.name) + 1)
        for idx, (toy, value) in enumerate(self):
            if idx == 0:
                lines.append(_assignrepr(value, f"{self.name}({toy}="))
            else:
                lines.append(_assignrepr(value, f"{blanks}{toy}="))
        lines[-1] += ")"
        return ",\n".join(lines)

    def __len__(self) -> int:
        return len(self._toy2values_protected)

    def __dir__(self) -> list[str]:
        """

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TIME = None
        >>> par = Par(None)
        >>> par.NDIM = 1
        >>> par.shape = (None,)
        >>> par(_1=2., _7_1=4., _3_1_0_0_0=5.)
        >>> sorted(set(dir(par)) - set(object.__dir__(par)))
        ['toy_1_1_0_0_0', 'toy_3_1_0_0_0', 'toy_7_1_0_0_0']

        .. testsetup::

            >>> del pub.timegrids
        """
        return cast(list[str], super().__dir__()) + [str(toy) for (toy, dummy) in self]


class KeywordParameter1D(_MixinModifiableParameter, Parameter):
    """Base class for 1-dimensional model parameters with values depending on one
    factor.

    When subclassing from |KeywordParameter1D|, one needs to define the class attribute
    `entrynames`.  A typical use case is that `entrynames` defines seasons like the
    months or, as in our example, half-years:

    >>> from hydpy.core.parametertools import KeywordParameter1D
    >>> class IsHot(KeywordParameter1D):
    ...     TYPE = bool
    ...     TIME = None
    ...     entrynames = ("winter", "summer")

    Usually, |KeywordParameter1D| objects prepare their shape automatically.  However,
    to simplify this test case, we define it manually:

    >>> ishot = IsHot(None)
    >>> ishot.shape = 2

    You can pass all parameter values both via positional or keyword arguments:

    >>> ishot(True)
    >>> ishot
    ishot(True)

    >>> ishot(False, True)
    >>> ishot
    ishot(winter=False, summer=True)

    >>> ishot(winter=True, summer=False)
    >>> ishot
    ishot(winter=True, summer=False)
    >>> ishot.values
    array([ True, False])

    We check the given keyword arguments for correctness and completeness:

    >>> ishot(winter=True)
    Traceback (most recent call last):
    ...
    ValueError: When setting parameter `ishot` of element `?` via keyword arguments, \
each string defined in `entrynames` must be used as a keyword, but the following \
keywords are not: `summer`.

    >>> ishot(winter=True, summer=False, spring=True, autumn=False)
    Traceback (most recent call last):
    ...
    ValueError: When setting parameter `ishot` of element `?` via keyword arguments, \
each keyword must be defined in `entrynames`, but the following keywords are not: \
`spring and autumn`.

    Class |KeywordParameter1D| implements attribute access, including specialised error
    messages:

    >>> ishot.winter, ishot.summer = ishot.summer, ishot.winter
    >>> ishot
    ishot(winter=False, summer=True)

    >>> ishot.spring
    Traceback (most recent call last):
    ...
    AttributeError: Parameter `ishot` of element `?` does not handle an attribute \
named `spring`.

    >>> ishot.shape = 1
    >>> ishot.summer
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve a value from parameter `ishot` of element \
`?` via the attribute `summer`, the following error occurred: index 1 is out of \
bounds for axis 0 with size 1

    >>> ishot.summer = True
    Traceback (most recent call last):
    ...
    IndexError: While trying to assign a new value to parameter `ishot` of element \
`?` via attribute `summer`, the following error occurred: index 1 is out of bounds \
for axis 0 with size 1
    """

    NDIM = 1
    entrynames: tuple[str, ...]
    entrymin: int = 0

    strict_valuehandling: bool = False

    def __init__(self, subvars: SubParameters) -> None:
        super().__init__(subvars)
        self.entrynames = type(self).entrynames
        self.entrymin = type(self).entrymin

    @classmethod
    @contextlib.contextmanager
    def modify_entries(
        cls, constants: Optional[Constants]
    ) -> Generator[None, None, None]:
        """Modify the relevant entry names temporarily.

        The entry names for defining properties like land-use types are fixed for
        typical "main models" like |hland|.  However, some submodels must take over the
        entry names defined by their current main model, which are only known at
        runtime.  For example, consider the following simple `LAI` parameter that
        handles predefined land use type names as a class attribute:

        >>> from hydpy.core.parametertools import KeywordParameter1D
        >>> class LAI(KeywordParameter1D):
        ...     TYPE = float
        ...     TIME = None
        ...     entrynames = ("field", "forest")
        >>> lai1 = LAI(None)
        >>> lai1.shape = 2
        >>> lai1(field=1.0, forest=2.0)
        >>> lai1
        lai(field=1.0, forest=2.0)

        We can use |KeywordParameter1D.modify_entries| to temporarily change these
        names:

        >>> from hydpy.core.parametertools import Constants
        >>> constants = Constants(GRASS=2, SOIL=1, TREES=3)
        >>> with LAI.modify_entries(constants):
        ...     lai2 = LAI(None)
        ...     lai2.shape = 3
        ...     lai2(soil=0.0, grass=1.0, trees=2.0)
        ...     lai2
        lai(soil=0.0, grass=1.0, trees=2.0)

        During initialisation, the names and the lowest value of the given constants
        become instance attributes, so the parameter instance does not forget them
        after leaving the `with` block (when the class attribute is reset to its
        previous value):

        >>> lai1.entrynames
        ('field', 'forest')
        >>> lai2.entrynames
        ('soil', 'grass', 'trees')
        >>> LAI.entrynames
        ('field', 'forest')

        >>> lai1.entrymin
        0
        >>> lai2.entrymin
        1
        >>> LAI.entrymin
        0

        Passing |None| does not overwrite the default or the previously set references:

        >>> LAI.entrymin = 3
        >>> with LAI.modify_entries(None):
        ...     LAI.entrynames
        ...     LAI.entrymin
        ...     lai3 = LAI(None)
        ...     lai3.shape = 2
        ...     lai3(field=2.0, forest=1.0)
        ...     lai3
        ('field', 'forest')
        3
        lai(field=2.0, forest=1.0)
        >>> LAI.entrynames
        ('field', 'forest')
        >>> LAI.entrymin
        3
        >>> lai3
        lai(field=2.0, forest=1.0)
        """
        if constants is None:
            yield
        else:
            get = vars(cls).get
            old_names = get("entrynames")
            old_min = get("entrymin")
            try:
                cls.entrynames = constants.sortednames
                cls.entrymin = min(constants.values())
                yield
            finally:
                cls._reset_after_modification("entrynames", old_names)
                cls._reset_after_modification("entrymin", old_min)

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self.shape = len(self.entrynames)
        setattr(self.fastaccess, f"_{self.name}_entrymin", self.entrymin)

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            for idx, key in enumerate(self.entrynames):
                try:
                    self.values[idx] = self.apply_timefactor(kwargs[key])
                except KeyError:
                    err = (key for key in self.entrynames if key not in kwargs)
                    raise ValueError(
                        f"When setting parameter {objecttools.elementphrase(self)} "
                        f"via keyword arguments, each string defined in `entrynames` "
                        f"must be used as a keyword, but the following keywords are "
                        f"not: `{objecttools.enumeration(err)}`."
                    ) from None
            if len(kwargs) != len(self.entrynames):
                err = (key for key in kwargs if key not in self.entrynames)
                raise ValueError(
                    f"When setting parameter {objecttools.elementphrase(self)} via "
                    f"keyword arguments, each keyword must be defined in "
                    f"`entrynames`, but the following keywords are not: "
                    f"`{objecttools.enumeration(err)}`."
                ) from None

    def __getattr__(self, key):
        if key in self.entrynames:
            try:
                return self.values[self.entrynames.index(key)]
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to retrieve a value from parameter "
                    f"{objecttools.elementphrase(self)} via the attribute `{key}`"
                )
        raise AttributeError(
            f"Parameter {objecttools.elementphrase(self)} does not handle an "
            f"attribute named `{key}`."
        )

    def __setattr__(self, key, values):
        if key in self.entrynames:
            try:
                self.values[self.entrynames.index(key)] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to assign a new value to parameter "
                    f"{objecttools.elementphrase(self)} via attribute `{key}`"
                )
        else:
            super().__setattr__(key, values)

    def __repr__(self):
        values = self.revert_timefactor(self.values)
        prefix = f"{self.name}("
        lines = []
        if len(numpy.unique(values)) == 1:
            lines.append(f"{prefix}{objecttools.repr_(values[0])})")
        else:
            blanks = " " * len(prefix)
            string = ", ".join(
                f"{key}={objecttools.repr_(value)}"
                for key, value in zip(self.entrynames, values)
            )
            for idx, substring in enumerate(
                textwrap.wrap(
                    text=string, width=max(70 - len(prefix), 30), break_long_words=False
                )
            ):
                if idx:
                    lines.append(f"{blanks}{substring}")
                else:
                    lines.append(f"{prefix}{substring}")
            lines[-1] += ")"
        return "\n".join(lines)

    def __dir__(self) -> list[str]:
        """
        >>> from hydpy.core.parametertools import KeywordParameter1D
        >>> class Season(KeywordParameter1D):
        ...     TYPE = bool
        ...     TIME = None
        ...     entrynames = ("winter", "summer")
        >>> season = Season(None)
        >>> sorted(set(dir(season)) - set(object.__dir__(season)))
        ['summer', 'winter']
        """
        return cast(list[str], super().__dir__()) + list(self.entrynames)


class MonthParameter(KeywordParameter1D):
    """Base class for parameters whose values depend on the actual month.

    Please see the documentation on class |KeywordParameter1D| on how to use
    |MonthParameter| objects and class |lland_control.WG2Z| of base model |lland| as an
    example implementation:

    >>> from hydpy.models.lland import *
    >>> simulationstep("12h")
    >>> parameterstep("1d")
    >>> wg2z(3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0)
    >>> wg2z
    wg2z(jan=3.0, feb=2.0, mar=1.0, apr=0.0, may=-1.0, jun=-2.0, jul=-3.0,
         aug=-2.0, sep=-1.0, oct=0.0, nov=1.0, dec=2.0)

    Note that attribute access provides access to the "real" values related to the
    current simulation time step:

    >>> wg2z.feb
    2.0
    >>> wg2z.feb = 4.0
    >>> wg2z
    wg2z(jan=3.0, feb=4.0, mar=1.0, apr=0.0, may=-1.0, jun=-2.0, jul=-3.0,
         aug=-2.0, sep=-1.0, oct=0.0, nov=1.0, dec=2.0)
    """

    entrynames = (
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    )


class KeywordParameter2D(_MixinModifiableParameter, Parameter):
    """Base class for 2-dimensional model parameters with values depending on two
    factors.

    When subclassing from |KeywordParameter2D| one needs to define the attributes
    `rownames` and `columnnames` (both of type |tuple|).  A typical use case is that
    `rownames` defines some land-use classes, and `columnnames` defines seasons,
    months, etc.  Here, we consider a simple corresponding example where the values of
    the boolean parameter `IsWarm` depend on the on the hemisphere and the half-year
    period:

    >>> from hydpy.core.parametertools import KeywordParameter2D
    >>> class IsWarm(KeywordParameter2D):
    ...     TYPE = bool
    ...     TIME = None
    ...     rownames = ("north", "south")
    ...     columnnames = ("apr2sep", "oct2mar")

    Instantiate the defined parameter class and define its shape:

    >>> iswarm = IsWarm(None)
    >>> iswarm.shape = (2, 2)

    |KeywordParameter2D| allows us to set the values of all rows via keyword arguments:

    >>> iswarm(north=[True, False],
    ...        south=[False, True])
    >>> iswarm
    iswarm(north=[True, False],
           south=[False, True])
    >>> iswarm.values
    array([[ True, False],
           [False,  True]])

    If a keyword is missing, it raises a |ValueError|:

    >>> iswarm(north=[True, False])
    Traceback (most recent call last):
    ...
    ValueError: While setting parameter `iswarm` of element `?` via row related \
keyword arguments, each string defined in `rownames` must be used as a keyword, but \
the following keywords are not: `south`.

    One can modify single rows via attribute access:

    >>> iswarm.north = False, False
    >>> iswarm.north
    array([False, False])

    The same holds for the columns:

    >>> iswarm.apr2sep = True, False
    >>> iswarm.apr2sep
    array([ True, False])

    Also, combined row-column access is possible:

    >>> iswarm.north_apr2sep
    True
    >>> iswarm.north_apr2sep = False
    >>> iswarm.north_apr2sep
    False

    All three forms of attribute access define augmented exception messages in case
    anything goes wrong:

    >>> iswarm.north = True, True, True
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign new values to parameter `iswarm` of element \
`?` via the row related attribute `north`, the following error occurred: could not \
broadcast input array from shape (3,) into shape (2,)
    >>> iswarm.apr2sep = True, True, True
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign new values to parameter `iswarm` of element \
`?` via the column related attribute `apr2sep`, the following error occurred: could \
not broadcast input array from shape (3,) into shape (2,)

    >>> iswarm.shape = (1, 1)

    >>> iswarm.south_apr2sep = False
    Traceback (most recent call last):
    ...
    IndexError: While trying to assign new values to parameter `iswarm` of element \
`?` via the row and column related attribute `south_apr2sep`, the following error \
occurred: index 1 is out of bounds for axis 0 with size 1

    >>> iswarm.south
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve values from parameter `iswarm` of element \
`?` via the row related attribute `south`, the following error occurred: index 1 is \
out of bounds for axis 0 with size 1
    >>> iswarm.oct2mar
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve values from parameter `iswarm` of element \
`?` via the column related attribute `oct2mar`, the following error occurred: index 1 \
is out of bounds for axis 1 with size 1
    >>> iswarm.south_oct2mar
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve values from parameter `iswarm` of element \
`?` via the row and column related attribute `south_oct2mar`, the following error \
occurred: index 1 is out of bounds for axis 0 with size 1

    >>> iswarm.shape = (2, 2)

    Unknown attribute names result in the following error:

    >>> iswarm.wrong
    Traceback (most recent call last):
    ...
    AttributeError: Parameter `iswarm` of element `?` does neither handle a normal \
attribute nor a row or column related attribute named `wrong`.

    One can still define the parameter values  via positional arguments:

    >>> iswarm(True)
    >>> iswarm
    iswarm(north=[True, True],
           south=[True, True])

    For parameters with many columns, string representations are adequately wrapped:

    >>> iswarm.shape = (2, 10)
    >>> iswarm
    iswarm(north=[False, False, False, False, False, False, False, False,
                  False, False],
           south=[False, False, False, False, False, False, False, False,
                  False, False])
    """

    NDIM = 2
    rownames: tuple[str, ...]
    columnnames: tuple[str, ...]
    rowmin: int = 0
    columnmin: int = 0

    strict_valuehandling: bool = False

    _rowcolumnmappings: dict[str, tuple[int, int]]

    def __init__(self, subvars: SubParameters) -> None:
        super().__init__(subvars)
        self.rownames = type(self).rownames
        self.columnnames = type(self).columnnames
        self._rowcolumnmappings = self._make_rowcolumnmappings(
            rownames=self.rownames, columnnames=self.columnnames
        )
        self.rowmin = type(self).rowmin
        self.columnmin = type(self).columnmin

    @classmethod
    @contextlib.contextmanager
    def modify_rows(cls, constants: Optional[Constants]) -> Generator[None, None, None]:
        """Modify the relevant row names temporarily.

        Methods |KeywordParameter2D.modify_rows| and |KeywordParameter2D.modify_columns|
        serve the same purpose and behave exactly on the respective axis
        |KeywordParameter2D| instances as method |KeywordParameter1D.modify_entries| on
        the single axis of |KeywordParameter1D| instances.  Hence, we only test their
        implementation here.  Please read the documentation on method
        |KeywordParameter1D.modify_entries| for more information:

        >>> from hydpy.core.parametertools import KeywordParameter2D
        >>> class IsWarm(KeywordParameter2D):
        ...     TYPE = bool
        ...     TIME = None
        ...     rownames = ("north", "south")
        ...     columnnames = ("apr2sep", "oct2mar")
        >>> iswarm1 = IsWarm(None)
        >>> iswarm1.shape = (2, 2)
        >>> iswarm1(north=[True, False],
        ...         south=[False, True])
        >>> iswarm1.north
        array([ True, False])
        >>> iswarm1.apr2sep
        array([ True, False])

        >>> from hydpy.core.parametertools import Constants
        >>> consts_row = Constants(N=1, S=2)
        >>> consts_column = Constants(APR2JUN=2, JUN2SEP=3, OCT2DEC=4, JAN2MAR=5)
        >>> with IsWarm.modify_rows(consts_row), IsWarm.modify_columns(consts_column):
        ...     iswarm2 = IsWarm(None)
        ...     iswarm2.shape = (2, 4)
        ...     iswarm2(n=[True, True, False, False],
        ...             s=[False, False, True, True])
        ...     iswarm2.n
        ...     iswarm2.apr2jun
        array([ True,  True, False, False])
        array([ True, False])

        >>> iswarm1.rownames
        ('north', 'south')
        >>> iswarm1.columnnames
        ('apr2sep', 'oct2mar')
        >>> iswarm1.rowmin
        0
        >>> iswarm1.columnmin
        0

        >>> iswarm2.rownames
        ('n', 's')
        >>> iswarm2.columnnames
        ('apr2jun', 'jun2sep', 'oct2dec', 'jan2mar')
        >>> iswarm2.rowmin
        1
        >>> iswarm2.columnmin
        2

        >>> IsWarm.rownames
        ('north', 'south')
        >>> IsWarm.columnnames
        ('apr2sep', 'oct2mar')
        >>> IsWarm.rowmin
        0
        >>> IsWarm.columnmin
        0

        >>> IsWarm.rowmin = 2
        >>> IsWarm.columnmin = 3
        >>> with IsWarm.modify_rows(None), IsWarm.modify_columns(None):
        ...     IsWarm.rownames
        ...     IsWarm.rowmin
        ...     IsWarm.columnnames
        ...     IsWarm.columnmin
        ...     iswarm3 = IsWarm(None)
        ...     iswarm3.shape = (2, 2)
        ...     iswarm3(north=[True, False],
        ...             south=[False, True])
        ...     iswarm3
        ...     iswarm1.north
        ('north', 'south')
        2
        ('apr2sep', 'oct2mar')
        3
        iswarm(north=[True, False],
               south=[False, True])
        array([ True, False])
        >>> IsWarm.rownames
        ('north', 'south')
        >>> IsWarm.columnnames
        ('apr2sep', 'oct2mar')
        >>> IsWarm.rowmin
        2
        >>> IsWarm.columnmin
        3
        >>> iswarm3
        iswarm(north=[True, False],
               south=[False, True])
        >>> iswarm1.north
        array([ True, False])
        """
        if constants is None:
            yield
        else:
            get = vars(cls).get
            old_names = get("rownames")
            old_min = get("rowmin")
            try:
                cls.rownames = constants.sortednames
                cls.rowmin = min(constants.values())
                yield
            finally:
                cls._reset_after_modification("rownames", old_names)
                cls._reset_after_modification("rowmin", old_min)

    @classmethod
    @contextlib.contextmanager
    def modify_columns(
        cls, constants: Optional[Constants]
    ) -> Generator[None, None, None]:
        """Modify the relevant column names temporarily.

        Please see the documentation on method |KeywordParameter2D.modify_rows| for
        further information.
        """
        if constants is None:
            yield
        else:
            get = vars(cls).get
            old_names = get("columnnames")
            old_min = get("columnmin")
            try:
                cls.columnnames = constants.sortednames
                cls.columnmin = min(constants.values())
                yield
            finally:
                cls._reset_after_modification("columnnames", old_names)
                cls._reset_after_modification("columnmin", old_min)

    @classmethod
    def _make_rowcolumnmappings(
        cls, rownames: tuple[str, ...], columnnames: tuple[str, ...]
    ) -> dict[str, tuple[int, int]]:
        rowcolmappings = {}
        for idx, rowname in enumerate(rownames):
            for jdx, colname in enumerate(columnnames):
                rowcolmappings["_".join((rowname, colname))] = (idx, jdx)
        return rowcolmappings

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls._rowcolumnmappings = cls._make_rowcolumnmappings(
            rownames=cls.rownames, columnnames=cls.columnnames
        )

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self.shape = (len(self.rownames), len(self.columnnames))
        setattr(self.fastaccess, f"_{self.name}_rowmin", self.rowmin)
        setattr(self.fastaccess, f"_{self.name}_columnmin", self.columnmin)

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            for idx, key in enumerate(self.rownames):
                try:
                    self.values[idx, :] = self.apply_timefactor(kwargs[key])
                except KeyError:
                    miss = [key for key in self.rownames if key not in kwargs]
                    raise ValueError(
                        f"While setting parameter "
                        f"{objecttools.elementphrase(self)} via row related keyword "
                        f"arguments, each string defined in `rownames` must be used "
                        f"as a keyword, but the following keywords are not: "
                        f"`{objecttools.enumeration(miss)}`."
                    ) from None

    def __getattr__(self, key: str):
        if key in self.rownames:
            try:
                return self.values[self.rownames.index(key), :]
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to retrieve values from parameter "
                    f"{objecttools.elementphrase(self)} via the row related attribute "
                    f"`{key}`"
                )
        if key in self.columnnames:
            try:
                return self.values[:, self.columnnames.index(key)]
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to retrieve values from parameter "
                    f"{objecttools.elementphrase(self)} via the column related "
                    f"attribute `{key}`"
                )
        if key in self._rowcolumnmappings:
            idx, jdx = self._rowcolumnmappings[key]
            try:
                return self.values[idx, jdx]
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to retrieve values from parameter "
                    f"{objecttools.elementphrase(self)} via the row and column "
                    f"related attribute `{key}`"
                )
        raise AttributeError(
            f"Parameter {objecttools.elementphrase(self)} does neither handle a "
            f"normal attribute nor a row or column related attribute named `{key}`."
        )

    def __setattr__(self, key: str, values) -> None:
        if key in self.rownames:
            try:
                self.values[self.rownames.index(key), :] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to assign new values to parameter "
                    f"{objecttools.elementphrase(self)} via the row related attribute "
                    f"`{key}`"
                )
        elif key in self.columnnames:
            try:
                self.values[:, self.columnnames.index(key)] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to assign new values to parameter "
                    f"{objecttools.elementphrase(self)} via the column related "
                    f"attribute `{key}`"
                )
        elif key in self._rowcolumnmappings:
            idx, jdx = self._rowcolumnmappings[key]
            try:
                self.values[idx, jdx] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to assign new values to parameter "
                    f"{objecttools.elementphrase(self)} via the row and column "
                    f"related attribute `{key}`"
                )
        else:
            super().__setattr__(key, values)

    def __repr__(self) -> str:
        values = self.revert_timefactor(self.values)
        prefix = f"{self.name}("
        blanks = " " * len(prefix)
        lines = []
        for idx, key in enumerate(self.rownames):
            subprefix = f"{prefix}{key}=" if idx == 0 else f"{blanks}{key}="
            lines.append(
                objecttools.assignrepr_list(values[idx, :], subprefix, 75) + ","
            )
        lines[-1] = lines[-1][:-1] + ")"
        return "\n".join(lines)

    def __dir__(self) -> list[str]:
        """
        >>> from hydpy.core.parametertools import KeywordParameter2D
        >>> class IsWarm(KeywordParameter2D):
        ...     TYPE = bool
        ...     TIME = None
        ...     rownames = ("north", "south")
        ...     columnnames = ("apr2sep", "oct2mar")
        >>> iswarm = IsWarm(None)
        >>> sorted(set(dir(iswarm)) - set(object.__dir__(iswarm)))
        ['apr2sep', 'north', 'north_apr2sep', 'north_oct2mar', 'oct2mar', 'south', \
'south_apr2sep', 'south_oct2mar']
        """
        assert (rowcolmappings := self._rowcolumnmappings) is not None
        return (
            cast(list[str], super().__dir__())
            + list(self.rownames)
            + list(self.columnnames)
            + list(rowcolmappings)
        )


class LeftRightParameter(variabletools.MixinFixedShape, Parameter):
    """Base class for handling two values, a left one and a right one.

    The original purpose of class |LeftRightParameter| is to make the
    handling of river channel related parameters with different values
    for both river banks a little more convenient.

    As an example, we define a parameter class describing the width
    both of the left and the right flood plain of a river segment:

    >>> from hydpy.core.parametertools import LeftRightParameter
    >>> class FloodPlainWidth(LeftRightParameter):
    ...     TYPE = float
    ...     TIME = None
    >>> floodplainwidth = FloodPlainWidth(None)

    Here, we need to set the shape of the parameter to 2, which is an
    automated procedure in full model setups:

    >>> floodplainwidth.shape = 2

    Parameter values can be defined as usual:

    >>> floodplainwidth(3.0)
    >>> floodplainwidth
    floodplainwidth(3.0)

    Alternatively, use the keywords `left` or `l` and `right` or
    `r` to define both values individually:

    >>> floodplainwidth(left=1.0, right=2.0)
    >>> floodplainwidth
    floodplainwidth(left=1.0, right=2.0)
    >>> floodplainwidth(l=2.0, r=1.0)
    >>> floodplainwidth
    floodplainwidth(left=2.0, right=1.0)

    Incomplete information results in the following errors:

    >>> floodplainwidth(left=2.0)
    Traceback (most recent call last):
    ...
    ValueError: When setting the values of parameter `floodplainwidth` of \
element `?` via keyword arguments, either `right` or `r` for the "right" \
parameter value must be given, but is not.
    >>> floodplainwidth(right=1.0)
    Traceback (most recent call last):
    ...
    ValueError: When setting the values of parameter `floodplainwidth` of \
element `?` via keyword arguments, either `left` or `l` for the "left" \
parameter value must be given, but is not.

    Additionally, one can query and modify the individual values via the
    attribute names `left` and `right`:

    >>> floodplainwidth.left
    2.0
    >>> floodplainwidth.left = 3.0
    >>> floodplainwidth.right
    1.0
    >>> floodplainwidth.right = 4.0
    >>> floodplainwidth
    floodplainwidth(left=3.0, right=4.0)
    """

    NDIM = 1
    SHAPE = (2,)
    strict_valuehandling: bool = False

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            left = kwargs.get("left", kwargs.get("l"))
            if left is None:
                raise ValueError(
                    f"When setting the values of parameter "
                    f"{objecttools.elementphrase(self)} via keyword "
                    f'arguments, either `left` or `l` for the "left" '
                    f"parameter value must be given, but is not."
                ) from None
            self.left = left
            right = kwargs.get("right", kwargs.get("r"))
            if right is None:
                raise ValueError(
                    f"When setting the values of parameter "
                    f"{objecttools.elementphrase(self)} via keyword "
                    f'arguments, either `right` or `r` for the "right" '
                    f"parameter value must be given, but is not."
                ) from None
            self.right = right

    @property
    def left(self) -> float:
        """The "left" value of the actual parameter object."""
        return self.values[0]

    @left.setter
    def left(self, value):
        self.values[0] = value

    @property
    def right(self) -> float:
        """The "right" value of the actual parameter object."""
        return self.values[1]

    @right.setter
    def right(self, value):
        self.values[1] = value

    def __repr__(self):
        values = [objecttools.repr_(value) for value in self.values]
        if values[0] == values[1]:
            return f"{self.name}({values[0]})"
        return f"{self.name}(left={values[0]}, right={values[1]})"


class FixedParameter(Parameter):
    """Base class for defining parameters with fixed values.

    Model model-users usually do not modify the values of |FixedParameter|
    objects.  Hence, such objects prepare their "initial" values automatically
    whenever possible, even when option |Options.usedefaultvalues| is disabled.
    """

    INIT: Union[int, float, bool]

    @property
    def initinfo(self) -> tuple[Union[float, int, bool], bool]:
        """A |tuple| always containing the fixed value and |True|, except
        for time-dependent parameters and incomplete time-information.

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.options.simulationstep

        >>> from hydpy.core.parametertools import FixedParameter
        >>> class Par(FixedParameter):
        ...   NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)
        ...   INIT = 100.0
        >>> par = Par(None)
        >>> par.initinfo
        (nan, False)
        >>> from hydpy import pub
        >>> pub.options.parameterstep = "1d"
        >>> pub.options.simulationstep = "12h"
        >>> par.initinfo
        (50.0, True)
        """
        try:
            with hydpy.pub.options.parameterstep("1d"):
                return self.apply_timefactor(self.INIT), True
        except (AttributeError, RuntimeError):
            return variabletools.TYPE2MISSINGVALUE[self.TYPE], False

    def restore(self) -> None:
        """Restore the original parameter value.

        Method |FixedParameter.restore| is relevant for testing mainly.  Note that it
        might be necessary to call it after changing the simulation step size, as shown
        in the following example using the parameter |evap_fixed.HeatOfCondensation| of
        base model |evap|:

        >>> from hydpy.models.evap import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> from hydpy import round_
        >>> fixed.heatofcondensation
        heatofcondensation(28.5)
        >>> round_(fixed.heatofcondensation.value)
        28.5
        >>> simulationstep("12h")
        >>> fixed.heatofcondensation
        heatofcondensation(14.25)
        >>> round_(fixed.heatofcondensation.value)
        28.5
        >>> fixed.heatofcondensation.restore()
        >>> fixed.heatofcondensation
        heatofcondensation(28.5)
        >>> round_(fixed.heatofcondensation.value)
        57.0
        """
        with hydpy.pub.options.parameterstep("1d"):
            self(self.INIT)


class SolverParameter(Parameter):
    """Base class for defining parameters controlling numerical algorithms
    for solving model equations.

    So far, the equation systems of most models implemented into *HydPy*
    are primarily coded as approximative solutions.  However, there are also
    some models stating the original equations only.  One example
    is the |dam| model. Its code consists of the original differential
    equations, which must be solved by a separate algorithm.  Such
    algorithms, like the Runge Kutta schema implemented in class
    |ELSModel|, often come with some degrees of freedom, for example,
    to control the striven numerical accuracy.

    On the one hand, the model developer should know best how to configure
    a numerical algorithm he selects for solving the model equations.  On the
    other hand, there might be situations when the model user has diverging
    preferences.  For example, he might favour higher numerical accuracies
    in one project and faster computation times in another one.  Therefore,
    the |SolverParameter.update| method of class |SolverParameter| relies
    on an `INIT` value defined by the model developer as long as the user
    does not define an alternative value in his control files.

    As an example, we derive the numerical tolerance parameter `Tol`:

    >>> from hydpy.core.parametertools import SolverParameter
    >>> class Tol(SolverParameter):
    ...     NDIM = 0
    ...     TYPE = float
    ...     TIME = None
    ...     SPAN = (0.0, None)
    ...     INIT = 0.1

    Initially, the method |SolverParameter.update| applies the value of the
    class constant `INIT`:

    >>> tol = Tol(None)
    >>> tol.update()
    >>> tol
    tol(0.1)

    One can define an alternative value via "calling" the parameter as usual:

    >>> tol(0.01)
    >>> tol
    tol(0.01)

    Afterwards, |SolverParameter.update| reuses the alternative value
    instead of the value of class constant `INIT`:

    >>> tol.update()
    >>> tol
    tol(0.01)

    This alternative value is accessible and changeable via property
    |SolverParameter.alternative_initvalue|:

    >>> tol.alternative_initvalue
    0.01

    >>> tol.alternative_initvalue = 0.001
    >>> tol.update()
    >>> tol
    tol(0.001)

    One must delete the alternative value to make `INIT` relevant again:

    >>> del tol.alternative_initvalue
    >>> tol.alternative_initvalue
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: No alternative initial value for \
solver parameter `tol` of element `?` has been defined so far.
    >>> tol.update()
    >>> tol
    tol(0.1)

    Very often, solver parameters depend on other model settings as the
    simulation step size or the catchment size, but `INIT` is always
    constant.  To allow for more flexibility, model developers can
    override the method |SolverParameter.modify_init|, which allows
    adapting the effective parameter value to the actual project settings.

    As a most simple example, we extend our class `Tol` with a
    |SolverParameter.modify_init| method that doubles the original
    `INIT` value:

    >>> class ModTol(Tol):
    ...     def modify_init(self):
    ...         return 2.0 * self.INIT
    >>> modtol = ModTol(None)
    >>> modtol.update()
    >>> modtol
    modtol(0.2)

    Note that |SolverParameter.modify_init| changes the value of `INIT`
    only, not the value of |SolverParameter.alternative_initvalue|:

    >>> modtol.alternative_initvalue = 0.01
    >>> modtol.update()
    >>> modtol
    modtol(0.01)
    """

    INIT: Union[int, float, bool]
    _alternative_initvalue: Optional[float]

    def __init__(self, subvars):
        super().__init__(subvars)
        self._alternative_initvalue = None

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        self.alternative_initvalue = self.value

    def update(self) -> None:
        """Update the actual parameter value based on `INIT` or, if
        available, on |SolverParameter.alternative_initvalue|.

        See the main documentation on class |SolverParameter| for more
        information.
        """
        if self._alternative_initvalue:
            self.value = self.alternative_initvalue
        else:
            self.value = self.modify_init()

    def modify_init(self) -> Union[bool, int, float]:
        """Return the value of class constant `INIT`.

        Override this method to support project-specific solver parameters.
        See the main documentation on class |SolverParameter| for more
        information.
        """
        return self.INIT

    @property
    def alternative_initvalue(self) -> Union[bool, int, float]:
        """A user-defined value to be used instead of the value of class
        constant `INIT`.

        See the main documentation on class |SolverParameter| for more
        information.
        """
        if self._alternative_initvalue is None:
            raise exceptiontools.AttributeNotReady(
                f"No alternative initial value for solver parameter "
                f"{objecttools.elementphrase(self)} has been defined so far."
            )
        return self._alternative_initvalue

    @alternative_initvalue.setter
    def alternative_initvalue(self, value):
        self._alternative_initvalue = value

    @alternative_initvalue.deleter
    def alternative_initvalue(self):
        self._alternative_initvalue = None


class SecondsParameter(Parameter):
    """The length of the actual simulation step size in seconds [s]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)

    def update(self) -> None:
        """Take the number of seconds from the current simulation time step.

        >>> from hydpy import pub
        >>> from hydpy.core.parametertools import SecondsParameter
        >>> secondsparameter = SecondsParameter(None)
        >>> with pub.options.parameterstep("1d"):
        ...     with pub.options.simulationstep("12h"):
        ...         secondsparameter.update()
        ...         secondsparameter
        secondsparameter(43200.0)
        """
        self.value = hydpy.pub.options.simulationstep.seconds


class HoursParameter(Parameter):
    """The length of the actual simulation step size in hours [h]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)

    def update(self) -> None:
        """Take the number of hours from the current simulation time step.

        >>> from hydpy import pub
        >>> from hydpy.core.parametertools import HoursParameter
        >>> hoursparameter = HoursParameter(None)
        >>> with pub.options.parameterstep("1d"):
        ...     with pub.options.simulationstep("12h"):
        ...         hoursparameter.update()
        >>> hoursparameter
        hoursparameter(12.0)
        """
        self.value = hydpy.pub.options.simulationstep.hours


class DaysParameter(Parameter):
    """The length of the actual simulation step size in days [d]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)

    def update(self) -> None:
        """Take the number of days from the current simulation time step.

        >>> from hydpy import pub
        >>> from hydpy.core.parametertools import DaysParameter
        >>> daysparameter = DaysParameter(None)
        >>> with pub.options.parameterstep("1d"):
        ...     with pub.options.simulationstep("12h"):
        ...         daysparameter.update()
        >>> daysparameter
        daysparameter(0.5)
        """
        self.value = hydpy.pub.options.simulationstep.days


class TOYParameter(Parameter):
    """References the |Indexer.timeofyear| index array provided by the
    instance of class |Indexer| available in module |pub|. [-]."""

    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (0, None)

    def update(self) -> None:
        """Reference the actual |Indexer.timeofyear| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
        >>> from hydpy.core.parametertools import TOYParameter
        >>> toyparameter = TOYParameter(None)
        >>> toyparameter.update()
        >>> toyparameter
        toyparameter(57, 58, 59, 60, 61)

        .. testsetup::

            >>> del pub.timegrids
        """
        indexarray = hydpy.pub.indexer.timeofyear
        self._set_shape(indexarray.shape)
        self._set_value(indexarray)


class MOYParameter(Parameter):
    """References the |Indexer.monthofyear| index array provided by the
    instance of class |Indexer| available in module |pub| [-]."""

    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (0, 11)

    def update(self) -> None:
        """Reference the actual |Indexer.monthofyear| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
        >>> from hydpy.core.parametertools import MOYParameter
        >>> moyparameter = MOYParameter(None)
        >>> moyparameter.update()
        >>> moyparameter
        moyparameter(1, 1, 1, 2, 2)

        .. testsetup::

            >>> del pub.timegrids
        """
        indexarray = hydpy.pub.indexer.monthofyear
        self._set_shape(indexarray.shape)
        self._set_value(indexarray)


class DOYParameter(Parameter):
    """References the |Indexer.dayofyear| index array provided by the
    instance of class |Indexer| available in module |pub| [-]."""

    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (0, 365)

    def update(self) -> None:
        """Reference the actual |Indexer.dayofyear| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = "27.02.2004", "3.03.2004", "1d"
        >>> from hydpy.core.parametertools import DOYParameter
        >>> doyparameter = DOYParameter(None)
        >>> doyparameter.update()
        >>> doyparameter
        doyparameter(57, 58, 59, 60, 61)

        .. testsetup::

            >>> del pub.timegrids
        """
        indexarray = hydpy.pub.indexer.dayofyear
        self._set_shape(indexarray.shape)
        self._set_value(indexarray)


class SCTParameter(Parameter):
    """References the |Indexer.standardclocktime| array provided by the
    instance of class |Indexer| available in module |pub| [h]."""

    NDIM = 1
    TYPE = float
    TIME = None
    SPAN = (0.0, 86400.0)

    def update(self) -> None:
        """Reference the actual |Indexer.standardclocktime| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = "27.02.2004 21:00", "28.02.2004 03:00", "1h"
        >>> from hydpy.core.parametertools import SCTParameter
        >>> sctparameter = SCTParameter(None)
        >>> sctparameter.update()
        >>> sctparameter
        sctparameter(21.5, 22.5, 23.5, 0.5, 1.5, 2.5)

        .. testsetup::

            >>> del pub.timegrids
        """
        array = hydpy.pub.indexer.standardclocktime
        self._set_shape(array.shape)
        self._set_value(array)


class UTCLongitudeParameter(Parameter):
    """References the current "UTC longitude" defined by option
    |Options.utclongitude|."""

    NDIM = 0
    TYPE = int
    TIME = None
    SPAN = (-180, 180)

    def update(self):
        """Apply the current value of option |Options.utclongitude|.

        >>> from hydpy import pub
        >>> pub.options.utclongitude
        15
        >>> from hydpy.core.parametertools import UTCLongitudeParameter
        >>> utclongitudeparameter = UTCLongitudeParameter(None)
        >>> utclongitudeparameter.update()
        >>> utclongitudeparameter
        utclongitudeparameter(15)

        Note that changing the value of option |Options.utclongitude|
        might makes re-calling method |UTCLongitudeParameter.update| necessary:

        >>> pub.options.utclongitude = 0
        >>> utclongitudeparameter
        utclongitudeparameter(15)
        >>> utclongitudeparameter.update()
        >>> utclongitudeparameter
        utclongitudeparameter(0)
        """
        self(hydpy.pub.options.utclongitude)


def do_nothing(model: modeltools.Model) -> None:  # pylint: disable=unused-argument
    """The default Python version of the |CallbackParameter|
    |CallbackParameter.callback| function, which does nothing."""


class CallbackParameter(Parameter):
    """Base class for parameters that support calculating their values via user-defined
    callback functions alternatively of sticking to the same values during a simulation
    run.

    We use the callback parameter |sw1d_control.GateHeight| of application model
    |sw1d_gate_out| for the following technical explanations (for a more
    application-oriented example, see the |sw1d_model.Calc_Discharge_V3|
    documentation):

    >>> from hydpy.models.sw1d_gate_out import *
    >>> parameterstep()

    You can define a fixed gate height as usual:

    >>> gateheight
    gateheight(?)
    >>> gateheight(3.0)
    >>> gateheight
    gateheight(3.0)

    Alternatively, you can write an individual callback function.  Its only argument
    accepts the model under consideration (here, |sw1d_gate_out|).  Principally, you
    are free to modify the model in any way you like, but the expected behaviour is
    to set the considered parameter's value only:

    >>> def adjust_gateheight(model) -> None:
    ...     con = model.parameters.control.fastaccess
    ...     my_gateheight: float = 2.0 + 3.0
    ...     con.gateheight = my_gateheight

    However, when working in Cython mode, *HydPy* converts the pure Python function to
    a Cython function and compiles it to C in the background, similar to how it handles
    "normal" model methods.  This background conversion is crucial for efficiency but
    restricts the allowed syntax and functionality.  Generally, you should work with
    the usual "fast access shortcuts", be explicit about the |None| return type, and
    cannot import any Python library, but are free to use Cython-functionalities
    implemented for and used by other model methods instead. A trivial example is using
    |fabs| for calculating absolute values.

    Next, we hand the callback function over to the parameter.  Here, we do this a
    little strangely between the creation of two tuples for hiding potential
    information printed by Cython or the used C compiler:

    >>> ();gateheight(callback=adjust_gateheight);()  # doctest: +ELLIPSIS
    (...)

    The string representation now includes the callback's source code:

    >>> gateheight
    def adjust_gateheight(model) -> None:
        con = model.parameters.control.fastaccess
        my_gateheight: float = 2.0 + 3.0
        con.gateheight = my_gateheight
    gateheight(callback=adjust_gateheight)

    When interested in the parameter's value, request it via the
    |CallbackParameter.value| property.  Note that this property applies the callback
    automatically before returning the (then updated) value:

    >>> from hydpy import round_
    >>> round_(gateheight.value)
    5.0

    You can return the parameter to "normal behaviour" by assigning a fixed value:

    >>> gateheight(7.0)
    >>> gateheight
    gateheight(7.0)

    Alternatively, one can assign a function via the |CallbackParameter.callback|
    property.  We do not need to hide potential compiler output this time because the
    Python function has already been converted to a reusable Cython function:

    >>> gateheight.callback = adjust_gateheight
    >>> gateheight
    def adjust_gateheight(model) -> None:
        con = model.parameters.control.fastaccess
        my_gateheight: float = 2.0 + 3.0
        con.gateheight = my_gateheight
    gateheight(callback=adjust_gateheight)
    >>> round_(gateheight.value)
    5.0

    Note that *HydPy* stores the Cython callbacks persistently on disk, using the
    Python function name as a part of the Cython module name. Hence, you cannot use
    two equally named callback functions for the same parameter of the same application
    model within one project.

    Use the `del` statement to remove the callback function:

    >>> assert gateheight.callback is not None
    >>> del gateheight.callback
    >>> assert gateheight.callback is None
    >>> gateheight
    gateheight(5.0)
    >>> round_(gateheight.value)
    5.0

    Failing attempts to pass a callback function might result in the following errors:

    >>> gateheight(Callback=adjust_gateheight)
    Traceback (most recent call last):
    ...
    ValueError: When trying to prepare parameter `gateheight` of element `?` via a \
keyword argument, it must be `callback`, and you need to pass a callback function.

    >>> gateheight(value=1.0, callback=adjust_gateheight)
    Traceback (most recent call last):
    ...
    ValueError: Parameter `gateheight` of element `?` does not allow to combine the \
`callback` argument with other arguments.

    The conversion from Python to Cython also works when defining the original function
    in an indentated block:

    >>> try:
    ...     def adjust_gateheight_indented(model) -> None:
    ...         con = model.parameters.control.fastaccess
    ...         my_gateheight: float = 2.0 * 3.0
    ...         con.gateheight = my_gateheight
    ... finally:
    ...     ();gateheight(callback=adjust_gateheight_indented);()  # doctest: +ELLIPSIS
    (...)
    >>> gateheight.callback = adjust_gateheight_indented
    >>> gateheight
    def adjust_gateheight_indented(model) -> None:
        con = model.parameters.control.fastaccess
        my_gateheight: float = 2.0 * 3.0
        con.gateheight = my_gateheight
    gateheight(callback=adjust_gateheight_indented)
    >>> round_(gateheight.value)
    6.0
    """

    _has_callback: bool = False

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError as exc:
            if (callback := kwargs.get("callback", None)) is None:
                raise ValueError(
                    f"When trying to prepare parameter "
                    f"{objecttools.elementphrase(self)} via a keyword argument, it "
                    f"must be `callback`, and you need to pass a callback function."
                ) from exc
            if (len(args) > 0) or (len(kwargs) > 1):
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} does not allow to "
                    f"combine the `callback` argument with other arguments."
                ) from exc
            self.callback = callback

    def _init_callback(self):
        if init := getattr(self.fastaccess, f"init_{self.name}_callback", None):
            init()
        else:
            setattr(self.fastaccess, f"{self.name}_callback", do_nothing)

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self._init_callback()

    @property
    def callback(self) -> Optional[Callable[[modeltools.Model], None]]:
        """The currently handled callback function for updating the parameter value."""
        if self._has_callback:
            if get := getattr(self.fastaccess, f"get_{self.name}_callback", None):
                return get()
            return getattr(self.fastaccess, f"{self.name}_callback")
        return None

    @callback.setter
    def callback(self, callback: Callable[[modeltools.Model], None]) -> None:
        from hydpy.cythons import modelutils  # pylint: disable=import-outside-toplevel

        if set_ := getattr(self.fastaccess, f"set_{self.name}_callback", None):
            cymodule = modelutils.get_callbackcymodule(
                model=self.subpars.pars.model, parameter=self, callback=callback
            )
            set_(cymodule.get_wrapper())
        else:
            setattr(self.fastaccess, f"{self.name}_callback", callback)
        self._has_callback = True

    @callback.deleter
    def callback(self) -> None:
        self._has_callback = False
        self._init_callback()

    def _get_value(self):
        """The fixed value or the value last updated by the callback function."""
        if self._has_callback:
            self.callback(self.subpars.pars.model)
            self._valueready = True
        return super()._get_value()

    def _set_value(self, value) -> None:
        self._init_callback()
        self._has_callback = False
        super()._set_value(value)

    value = property(fget=_get_value, fset=_set_value)

    def __repr__(self) -> str:
        if self._has_callback:
            callback: Any = self.callback
            if isinstance(callback, types.FunctionType):
                lines = inspect.getsource(callback).split("\n")
                indent = len(lines[0]) - len(lines[0].lstrip())
                pycode = "\n".join(line[indent:] for line in lines).rstrip()
                funcname = callback.__name__
            else:
                pycode = callback.get_sourcecode()
                funcname = callback.get_name()
            varrepr = f"{self.name}(callback={funcname})"
            return "\n".join((pycode, varrepr))
        return super().__repr__()
