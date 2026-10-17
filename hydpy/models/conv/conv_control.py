# pylint: disable=missing-module-docstring

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


class OutputCoordinates(Coordinates):
    """Coordinates of the outlet nodes [?]."""


class Heights(parametertools.Parameter):
    """Base class for |InputHeights| and |OutputHeights| [?].

    We use the derived class |InputHeights| as an example:

    >>> from hydpy.models.conv import *
    >>> parameterstep()

    |Heights| subclasses define 1-dimensional sequences.  Hence, we must define
    their shape first:

    >>> inputheights
    inputheights(?)
    >>> inputheights.values
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for \
variable `inputheights` can only be retrieved after it has been defined.

    However, you usually do this automatically when assigning new values.
    Use keyword arguments to define the names of the relevant input nodes
    as well as their heights:

    >>> from hydpy import print_vector
    >>> inputheights(in1=1.0)
    >>> inputheights
    inputheights(in1=1.0)
    >>> print_vector(inputheights.values)
    1.0

    Defining new heights removes the old ones:

    >>> inputheights(in2=2.0,
    ...              in0=3.0,
    ...              in3=4.0)
    >>> inputheights
    inputheights(in2=2.0,
                 in0=3.0,
                 in3=4.0)
    >>> print_vector(inputheights.values)
    2.0, 3.0, 4.0

    You are free to change individual height values (the row order corresponds
    to the definition order when "calling" the parameter):

    >>> inputheights.values[1] = 9.0
    >>> inputheights
    inputheights(in2=2.0,
                 in0=9.0,
                 in3=4.0)

    The attribute |Heights.nodes| stores the correctly ordered nodes:

    >>> inputheights.nodes
    (Node("in2", variable="Q"), Node("in0", variable="Q"), \
Node("in3", variable="Q"))
    """

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float

    nodes: tuple[devicetools.Node, ...]
    """The relevant input or output nodes."""

    def __init__(self, subvars: parametertools.SubParameters[modeltools.Model]):
        super().__init__(subvars)
        self.nodes = ()

    def __call__(self, *args, **kwargs) -> None:
        nodes = []
        heights = numpy.empty(len(kwargs), dtype=config.NP_FLOAT)
        for idx, (name, value) in enumerate(kwargs.items()):
            nodes.append(devicetools.Node(name))
            heights[idx] = value
        self.nodes = tuple(nodes)
        self.shape = len(nodes)
        self.value = heights

    def __repr__(self) -> str:
        prefix = f"{self.name}("
        blanks = " " * len(prefix)
        lines = []
        if self.nodes:
            for idx, node in enumerate(self.nodes):
                entry = f"{node.name}={self.values[idx]}"
                if not idx:
                    lines.append(f"{prefix}{entry}")
                else:
                    lines.append(f"{blanks}{entry}")
                if idx < len(self.nodes) - 1:
                    lines[-1] += ","
                else:
                    lines[-1] += ")"
            return "\n".join(lines)
        return f"{prefix}?)"


class InputHeights(Heights):
    """The height (above sea level or anything else) of the input nodes [?]."""


class OutputHeights(Heights):
    """The height (above sea level or anything else) of the output nodes [?]."""


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

    def __call__(self, *args, **kwargs) -> None:
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
