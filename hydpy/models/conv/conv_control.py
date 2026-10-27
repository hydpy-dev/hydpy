# pylint: disable=missing-module-docstring

import abc

import numpy

from hydpy import config
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class Coordinates(parametertools.SpecialParameter):
    """Base class for |InputCoordinates| and |OutputCoordinates| [?].

    |Coordinates| is a special parameter (see |SpecialParameter|) that handles the
    names of the relevant input or output nodes together with their coordinates.  We
    use the derived class |InputCoordinates| as an example:

    >>> from hydpy.models.conv import *
    >>> parameterstep()

    Initially, neither the nodes nor their coordinates are known:

    >>> inputcoordinates
    inputcoordinates(?)
    >>> inputcoordinates.nodes
    ()
    >>> len(inputcoordinates)
    0
    >>> inputcoordinates.coordinates
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: The coordinates of parameter \
`inputcoordinates` of element `?` have not been defined so far.
    >>> inputcoordinates.verify()
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: The coordinates of parameter \
`inputcoordinates` of element `?` have not been defined so far.

    Use keyword arguments to define the names of the relevant input nodes as well as
    their coordinates:

    >>> inputcoordinates(in1=(1.0, 3.0))
    >>> inputcoordinates
    inputcoordinates(in1=(1.0, 3.0))
    >>> from hydpy import print_matrix
    >>> print_matrix(inputcoordinates.coordinates)
    | 1.0, 3.0 |
    >>> inputcoordinates.verify()

    Defining new coordinates removes the old ones:

    >>> inputcoordinates(in2=(2.0, 4.0),
    ...                  in0=(3.0, 5.0),
    ...                  in3=(4.0, 6.0))
    >>> inputcoordinates
    inputcoordinates(in2=(2.0, 4.0),
                     in0=(3.0, 5.0),
                     in3=(4.0, 6.0))
    >>> print_matrix(inputcoordinates.coordinates)
    | 2.0, 4.0 |
    | 3.0, 5.0 |
    | 4.0, 6.0 |
    >>> len(inputcoordinates)
    3

    You are free to change individual coordinate values (the rows of the matrix contain
    the different value pairs; the row order corresponds to the definition order when
    "calling" the parameter):

    >>> inputcoordinates.coordinates[1, 0] = 9.0
    >>> inputcoordinates
    inputcoordinates(in2=(2.0, 4.0),
                     in0=(9.0, 5.0),
                     in3=(4.0, 6.0))

    The attribute |Coordinates.nodes| stores the correctly ordered nodes:

    >>> inputcoordinates.nodes
    (Node("in2", variable="Q"), Node("in0", variable="Q"), \
Node("in3", variable="Q"))

    You must define the coordinates of at least one node, and each node requires exactly
    two coordinates.  In case of errors, the previous definitions remain unchanged:

    >>> inputcoordinates()
    Traceback (most recent call last):
    ...
    ValueError: Parameter `inputcoordinates` of element `?` requires the coordinates \
of at least one node, but none are given.

    >>> inputcoordinates(in1=(1.0, 3.0), in2=(1.0, 2.0, 3.0))
    Traceback (most recent call last):
    ...
    ValueError: Parameter `inputcoordinates` of element `?` requires exactly two \
coordinates for each node, but for node `in2`, `(1.0, 2.0, 3.0)` is given.

    >>> inputcoordinates(in1="wrong")
    Traceback (most recent call last):
    ...
    ValueError: Parameter `inputcoordinates` of element `?` requires exactly two \
coordinates for each node, but for node `in1`, `wrong` is given.

    >>> inputcoordinates
    inputcoordinates(in2=(2.0, 4.0),
                     in0=(9.0, 5.0),
                     in3=(4.0, 6.0))

    Positional arguments are not supported:

    >>> inputcoordinates((1.0, 3.0))
    Traceback (most recent call last):
    ...
    TypeError: Coordinates.__call__() takes 1 positional argument but 2 were given
    """

    nodes: tuple[devicetools.Node, ...]
    """The relevant input or output nodes."""

    _coordinates: MatrixFloat | None

    def __init__(self, subvars: parametertools.SubParameters[modeltools.Model]):
        super().__init__(subvars)
        self.nodes = ()
        self._coordinates = None

    def __call__(self, **coordinates: tuple[float, float]) -> None:
        if not coordinates:
            raise ValueError(
                f"Parameter {objecttools.elementphrase(self)} requires the coordinates "
                f"of at least one node, but none are given."
            )
        matrix = numpy.empty((len(coordinates), 2), dtype=config.NP_FLOAT)
        for idx, (name, values) in enumerate(coordinates.items()):
            try:
                matrix[idx, :] = values
            except (TypeError, ValueError):
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} requires exactly "
                    f"two coordinates for each node, but for node `{name}`, "
                    f"`{objecttools.repr_(values)}` is given."
                ) from None
        self.nodes = tuple(devicetools.Node(name) for name in coordinates)
        self._coordinates = matrix
        self._set_number_of_nodes()

    @abc.abstractmethod
    def _set_number_of_nodes(self) -> None:
        """Set the derived parameter that gives the number of nodes."""

    @property
    def coordinates(self) -> MatrixFloat:
        """The coordinates of all nodes (one row per node, in the order of
        |Coordinates.nodes|)."""
        if (coordinates := self._coordinates) is None:
            raise exceptiontools.AttributeNotReady(
                f"The coordinates of parameter {objecttools.elementphrase(self)} have "
                f"not been defined so far."
            )
        return coordinates

    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        prefix = f"{self.name}("
        if (coordinates := self._coordinates) is None:
            return f"{prefix}?)"
        blanks = " " * len(prefix)
        lines = []
        for idx, node in enumerate(self.nodes):
            entry = f"{node.name}={objecttools.repr_tuple(coordinates[idx, :])}"
            lines.append(f"{blanks if idx else prefix}{entry}")
            lines[-1] += "," if idx < len(self.nodes) - 1 else ")"
        return "\n".join(lines)

    def verify(self) -> None:
        """Raise an |AttributeNotReady| error if the coordinates are still undefined."""
        _ = self.coordinates


class InputCoordinates(Coordinates):
    """Coordinates of the inlet nodes [?]."""

    def _set_number_of_nodes(self) -> None:
        self.subpars.pars.derived.nmbinputs(len(self.nodes))


class OutputCoordinates(Coordinates):
    """Coordinates of the outlet nodes [?]."""

    def _set_number_of_nodes(self) -> None:
        self.subpars.pars.derived.nmboutputs(len(self.nodes))


class Heights(parametertools.Parameter):
    """Base class for |InputHeights| and |OutputHeights| [?].

    |Heights| subclasses are 1-dimensional parameters that provide one height value
    for each node defined by the corresponding |Coordinates| parameter.  We use the
    derived class |InputHeights| as an example:

    >>> from hydpy.models.conv import *
    >>> parameterstep()
    >>> inputheights
    inputheights(?)

    Defining the input coordinates also sets the derived parameter |NmbInputs| and
    thereby determines the shape of |InputHeights|:

    >>> inputcoordinates(in2=(2.0, 4.0),
    ...                  in0=(3.0, 5.0),
    ...                  in3=(4.0, 6.0))
    >>> derived.nmbinputs
    nmbinputs(3)
    >>> inputheights.shape
    (3,)

    You can pass the heights in the order of the coordinates' nodes, like the values
    of other 1-dimensional parameters:

    >>> inputheights(2.0, 3.0, 4.0)
    >>> from hydpy import print_vector
    >>> print_vector(inputheights.values)
    2.0, 3.0, 4.0

    However, the string representation relies on the node names:

    >>> inputheights
    inputheights(in2=2.0,
                 in0=3.0,
                 in3=4.0)

    Preferably, you should use the node names as keywords.  Then, the order does not
    matter:

    >>> inputheights(in3=6.0, in2=7.0, in0=8.0)
    >>> print_vector(inputheights.values)
    7.0, 8.0, 6.0

    The given node names must agree with the ones defined via |InputCoordinates|:

    >>> inputheights(in2=1.0, in0=2.0, in4=3.0)
    Traceback (most recent call last):
    ...
    ValueError: The keyword arguments of parameter `inputheights` of element `?` must \
agree with the node names defined by parameter `inputcoordinates`, but the name `in3` \
is missing and the name `in4` is unknown.

    >>> inputheights(in2=1.0)
    Traceback (most recent call last):
    ...
    ValueError: The keyword arguments of parameter `inputheights` of element `?` must \
agree with the node names defined by parameter `inputcoordinates`, but the names `in0` \
and `in3` are missing.

    >>> inputheights
    inputheights(in2=7.0,
                 in0=8.0,
                 in3=6.0)

    Mixing positional and keyword arguments is not allowed:

    >>> inputheights(1.0, in0=2.0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `inputheights` of element `?` both positional and \
keyword arguments are given, which is ambiguous.

    Reading the heights from auxiliary control files works as usual:

    >>> from hydpy import TestIO
    >>> with TestIO(clear_own=True):
    ...     with open("heights_aux.py", "w", encoding="utf-8") as file_:
    ...         for line in (
    ...             "from hydpy.models.conv import *",
    ...             "parameterstep()",
    ...             "inputheights(in3=1.0, in2=2.0, in0=3.0)",
    ...         ):
    ...             print(line, file=file_)
    ...     inputheights(auxfile="heights_aux")
    >>> inputheights
    inputheights(in2=2.0,
                 in0=3.0,
                 in3=1.0)
    >>> inputheights(in3=6.0, in2=7.0, in0=8.0)

    Redefining the coordinates of the same number of nodes keeps the heights, while
    changing the number of nodes discards them:

    >>> inputcoordinates(a=(2.0, 4.0), b=(3.0, 5.0), c=(4.0, 6.0))
    >>> inputheights
    inputheights(a=7.0,
                 b=8.0,
                 c=6.0)
    >>> inputcoordinates(a=(2.0, 4.0), b=(3.0, 5.0))
    >>> inputheights
    inputheights(?)

    The string representation falls back to the usual format if the numbers of heights
    and nodes differ:

    >>> inputheights.shape = 3
    >>> inputheights(1.0, 2.0, 3.0)
    >>> inputheights
    inputheights(1.0, 2.0, 3.0)
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float

    @property
    @abc.abstractmethod
    def coordinates(self) -> Coordinates:
        """The |Coordinates| parameter that defines the relevant nodes."""

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    @overload
    def __call__(self, **heights: float) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        if (not kwargs) or ("auxfile" in kwargs):
            super().__call__(*args, **kwargs)
            return
        if args:
            self._raise_args_and_kwargs_error()
        names = tuple(node.name for node in self.coordinates.nodes)
        missing = set(names) - set(kwargs)
        unknown = set(kwargs) - set(names)
        if missing or unknown:
            i = objecttools.Inflect
            problems = []
            if missing:
                problems.append(
                    f"the {i.listing('name', sorted(missing), 'is missing')}"
                )
            if unknown:
                problems.append(
                    f"the {i.listing('name', sorted(unknown), 'is unknown')}"
                )
            raise ValueError(
                f"The keyword arguments of parameter {objecttools.elementphrase(self)} "
                f"must agree with the node names defined by parameter "
                f"`{self.coordinates.name}`, but {' and '.join(problems)}."
            )
        super().__call__(*(kwargs[name] for name in names))

    def __repr__(self) -> str:
        nodes = self.coordinates.nodes
        values = exceptiontools.getattr_(self, "values", None)
        if (values is None) or (len(nodes) != len(values)):
            return super().__repr__()
        prefix = f"{self.name}("
        blanks = " " * len(prefix)
        lines = []
        for idx, (node, value) in enumerate(zip(nodes, values)):
            entry = f"{node.name}={objecttools.repr_(value)}"
            lines.append(f"{blanks if idx else prefix}{entry}")
            lines[-1] += "," if idx < len(nodes) - 1 else ")"
        return "\n".join(lines)


class InputHeights(Heights):
    """The height (above sea level or anything else) of the input nodes [?]."""

    @property
    def coordinates(self) -> InputCoordinates:
        """The |InputCoordinates| parameter."""
        return self.subpars.inputcoordinates

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.conv import conv_derived

        if isinstance(p, conv_derived.NmbInputs):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class OutputHeights(Heights):
    """The height (above sea level or anything else) of the output nodes [?]."""

    @property
    def coordinates(self) -> OutputCoordinates:
        """The |OutputCoordinates| parameter."""
        return self.subpars.outputcoordinates

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.conv import conv_derived

        if isinstance(p, conv_derived.NmbOutputs):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MaxNmbInputs(parametertools.Parameter):
    """The maximum number of input locations to be taken into account for
    interpolating the values of a specific output location [-].

    When passing no value, parameter |MaxNmbInputs| queries it from the shape
    of parameter |InputCoordinates|:

    >>> from hydpy.models.conv import *
    >>> parameterstep()
    >>> inputcoordinates(in2=(2.0, 4.0),
    ...                  in0=(3.0, 5.0),
    ...                  in3=(4.0, 6.0))
    >>> maxnmbinputs()
    >>> maxnmbinputs
    maxnmbinputs(3)

    You can define alternative values manually:

    >>> maxnmbinputs(2)
    >>> maxnmbinputs
    maxnmbinputs(2)
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        if not args and not kwargs:
            super().__call__(len(self.subpars.inputcoordinates.coordinates))
        else:
            super().__call__(*args, **kwargs)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        """Assure that the value of |MaxNmbInputs| does not exceed the
        number of available input locations.

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> inputcoordinates(in2=(2.0, 4.0),
        ...                  in0=(3.0, 5.0),
        ...                  in3=(4.0, 6.0))
        >>> maxnmbinputs(0)
        Traceback (most recent call last):
        ...
        ValueError: The value `0` of parameter `maxnmbinputs` of \
element `?` is not valid.
        >>> maxnmbinputs(4)
        Traceback (most recent call last):
        ...
        ValueError: The value `4` of parameter `maxnmbinputs` of \
element `?` is not valid.
        """
        if upper is None:
            upper = len(self.subpars.inputcoordinates.coordinates)
        return super().trim(lower, upper)


class MinNmbInputs(parametertools.Parameter):
    """The minimum number of inputs for performing a statistical analysis [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (2, None)


class DefaultConstant(parametertools.Parameter):
    """Default or fallback value for the constant of the linear regression model [?]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float


class DefaultFactor(parametertools.Parameter):
    """Default or fallback value for the factor of the linear regression model [?]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (-1.0, 1.0)


class Power(parametertools.Parameter):
    """Power parameter for calculating inverse distance weights [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0, None)
