# pylint: disable=missing-module-docstring


from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.manager import manager_parameters


class Commission(parametertools.DateParameter):
    """Commission date [-]."""


class DischargeThreshold(parametertools.Parameter):
    """Discharge threshold for estimating release requests [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class DischargeTolerance(parametertools.Parameter):
    """Discharge tolerance for estimating release requests [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class TimeDelay(parametertools.Parameter):
    """Time delay (in terms of simulation steps) between the release of additional
    water and its effect on the target cross-section [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (0, None)


class TimeWindow(parametertools.Parameter):
    """Time window (in terms of simulation steps) used for calculating multiple "free
    discharge" estimates [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)


class Sources(parametertools.SpecialParameter):
    """The sources (e.g. dams) that are instructible to release additional water.

    |Sources| is a special parameter (see |SpecialParameter|) that handles the names
    of the elements that handle the relevant source models:

    >>> from hydpy.models.manager import *
    >>> parameterstep()
    >>> sources
    sources(?)
    >>> sources.verify()
    Traceback (most recent call last):
    ...
    RuntimeError: Parameter `sources` of element `?` does not know the names of the \
relevant sources so far.

    |Sources| expects the names of the elements which handle the relevant source models
    and sorts them alphabetically, if necessary:

    >>> sources("c", "a", "b")
    >>> sources
    sources("a", "b", "c")
    >>> sources.verify()

    |Sources| provides the names of the individual sources by its property
    |Sources.sourcenames| and passes their number to the derived parameter |NmbSources|,
    which determines the shape of many other parameters and sequences:

    >>> sources.sourcenames
    ('a', 'b', 'c')
    >>> derived.nmbsources
    nmbsources(3)
    >>> active.shape
    (3,)

    |Sources| raises the following errors if the user gives no or invalid element
    names:

    >>> sources()
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the sources to be controlled by the model \
`manager` of element `?`, the following error occurred: Parameter `sources` requires \
the name of at least one element, but none is given.

    >>> sources(3)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the sources to be controlled by the model \
`manager` of element `?`, the following error occurred: Parameter `sources` requires a \
list of the names of the elements which handle the relevant source models, but the \
argument `3` is not a valid element name.

    >>> sources("not valid", "valid", " invalid")
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the sources to be controlled by the model \
`manager` of element `?`, the following error occurred: Parameter `sources` requires a \
list of the names of the elements which handle the relevant source models, but the \
arguments `not valid` and ` invalid` are not valid element names.

    In case of errors, the previous definitions remain unchanged:

    >>> sources
    sources("a", "b", "c")
    """

    _sourcenames: tuple[str, ...] | None = None

    @property
    def sourcenames(self) -> tuple[str, ...]:
        """The names of the elements which handle the relevant source models.

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources.sourcenames
        Traceback (most recent call last):
        ...
        RuntimeError: Parameter `sources` of element `?` does not know the names of \
the relevant sources so far.

        >>> sources("c", "a", "b")
        >>> sources.sourcenames
        ('a', 'b', 'c')
        """
        if self._sourcenames is None:
            raise RuntimeError(
                f"Parameter {objecttools.elementphrase(self)} does not know the names "
                f"of the relevant sources so far."
            )
        return self._sourcenames

    def __call__(self, *sourcenames: str) -> None:
        try:
            if not sourcenames:
                raise ValueError(
                    f"Parameter `{self.name}` requires the name of at least one "
                    f"element, but none is given."
                )
            ivvi = objecttools.is_valid_variable_identifier
            if wrong := tuple(a for a in sourcenames if not ivvi(a)):
                i = objecttools.Inflect
                n = len(wrong)
                raise ValueError(
                    f"Parameter `{self.name}` requires a list of the names of the "
                    f"elements which handle the relevant source models, but the "
                    f"{i.listing('argument', wrong, 'is')} not "
                    f"{i.a('valid element name', n)}."
                )
            sourcenames = tuple(sorted(sourcenames))
            self.subpars.pars.derived.nmbsources(len(sourcenames))
            self._sourcenames = sourcenames
        except BaseException:
            objecttools.augment_excmessage(
                "While trying to define the sources to be controlled by the model "
                f"{objecttools.elementphrase(self.subpars.pars.model)}"
            )

    def __repr__(self) -> str:
        if self._sourcenames is None:
            return f"{self.name}(?)"
        sourcenames = tuple(f'"{sn}"' for sn in self._sourcenames)
        return objecttools.assignrepr_values(sourcenames, f"{self.name}(") + ")"

    def verify(self) -> None:
        """Raise a |RuntimeError| if the names of the sources are unknown."""
        _ = self.sourcenames


class VolumeThreshold(manager_parameters.ParameterSource):
    """Water volume below which the sources do not fulfil additional water release
    requests [million m³].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = float
    SPAN = (0.0, None)


class VolumeTolerance(manager_parameters.ParameterSource):
    """Water volume tolerance for determining the water demand of the individual
    sources [million m³].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = float
    SPAN = (0.0, None)


class ReleaseMax(manager_parameters.ParameterSource):
    """Maximum additional release of the individual sources [m³/s].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = float
    SPAN = (0.0, None)


class Active(manager_parameters.ParameterSource):
    """Flag to activate/deactivate sending requests to individual sources [-].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = bool
    SPAN = (False, True)
