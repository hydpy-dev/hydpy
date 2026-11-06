# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.conv import conv_parameters


class InputCoordinates(conv_parameters.Coordinates):
    """Coordinates of the inlet nodes [?]."""

    def _set_number_of_nodes(self) -> None:
        self.subpars.pars.derived.nmbinputs(len(self.nodes))


class OutputCoordinates(conv_parameters.Coordinates):
    """Coordinates of the outlet nodes [?]."""

    def _set_number_of_nodes(self) -> None:
        self.subpars.pars.derived.nmboutputs(len(self.nodes))


class InputHeights(conv_parameters.Heights):
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


class OutputHeights(conv_parameters.Heights):
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


class InputAverages(conv_parameters.Averages):
    """The long-term averages of the input nodes for each month of the year [?]."""

    @property
    def coordinates(self) -> InputCoordinates:
        """The |InputCoordinates| parameter."""
        return self.subpars.inputcoordinates

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.conv import conv_derived

        if isinstance(p, conv_derived.NmbInputs):
            self.__hydpy__change_shape_if_necessary__((p.value, 12))


class OutputAverages(conv_parameters.Averages):
    """The long-term averages of the output nodes for each month of the year [?]."""

    @property
    def coordinates(self) -> OutputCoordinates:
        """The |OutputCoordinates| parameter."""
        return self.subpars.outputcoordinates

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        # pylint: disable=import-outside-toplevel
        from hydpy.models.conv import conv_derived

        if isinstance(p, conv_derived.NmbOutputs):
            self.__hydpy__change_shape_if_necessary__((p.value, 12))


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
