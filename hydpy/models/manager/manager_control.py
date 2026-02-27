# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import inflect

# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *

# ...from manager
from hydpy.models.manager import manager_parameters


class Commission(parametertools.DateParameter):
    """Commission date [-]."""


class DischargeThreshold(parametertools.Parameter):
    """Discharge threshold for estimating release requests [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class DischargeTolerance(parametertools.Parameter):
    """Discharge tolerance for estimating release requests [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class TimeDelay(parametertools.Parameter):
    """Time delay (in terms of simulation steps) between the release of additional
    water and its effect on the target cross-section [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    TIME = None
    SPAN = (0, None)


class TimeWindow(parametertools.Parameter):
    """Time window (in terms of simulation steps) used for calculating multiple "free
    discharge" estimates [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    TIME = None
    SPAN = (1, None)


class Sources(parametertools.NmbParameter):
    """The sources (e.g. dams) that are instructible to release additional water [-].

    >>> from hydpy.models.manager import *
    >>> parameterstep()
    >>> sources
    sources(?)

    |Sources| expects the names of the elements which handle the relevant source models
    and sorts them alphabetically, if necessary:

    >>> sources("c", "a", "b")
    >>> sources
    sources("a", "b", "c")

    |Sources| provides the number of sources as its property |Variable.value| and the
    names of the individual sources by its property |Sources.sourcenames|:

    >>> sources.value
    3
    >>> sources.sourcenames
    ('a', 'b', 'c')

    |Sources| raises the following errors if the user gives invalid element names or
    tries to pass information via keyword arguments:

    >>> sources(3)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the sources to be controlled by the model \
`manager` of element `?`, the following error occurred: Parameter `sources` requires \
a list of the names of the elements which handle the relevant source models, but the \
following argument is not a valid element name: `3`

    >>> sources("not valid", "valid", " invalid")
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the sources to be controlled by the model \
`manager` of element `?`, the following error occurred: Parameter `sources` requires \
a list of the names of the elements which handle the relevant source models, but the \
following arguments are not some valid element names: `not valid` and ` invalid`

    >>> sources("valid", invalid=1)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the sources to be controlled by the model \
`manager` of element `?`, the following error occurred: Parameter `sources` cannot \
handle keyword arguments.
    """

    SPAN = (1, None)

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

    def __call__(self, *args, **kwargs) -> None:
        try:
            ivvi = objecttools.is_valid_variable_identifier
            if wrong := tuple(a for a in args if not ivvi(a)):
                p = inflect.engine().plural
                n = len(wrong)
                wrong = tuple(f"`{w}`" for w in wrong)
                raise ValueError(
                    f"Parameter `{self.name}` requires a list of the names of the "
                    f"elements which handle the relevant source models, but the "
                    f"following {p('argument', n)} {p('is', n)} not {p('a', n)} valid "
                    f"element {p('name', n)}: {objecttools.enumeration(wrong)}"
                )
            if kwargs:
                raise ValueError(
                    f"Parameter `{self.name}` cannot handle keyword arguments."
                )
            sourcenames = tuple(sorted(args))
            super().__call__(len(sourcenames))
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


class VolumeThreshold(manager_parameters.ParameterSource):
    """Water volume below which the sources do not fulfil additional water release
    requests [million m³].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class VolumeTolerance(manager_parameters.ParameterSource):
    """Water volume tolerance for determining the water demand of the individual
    sources [million m³].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class ReleaseMax(manager_parameters.ParameterSource):
    """Maximum additional release of the individual sources [m³/s].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class Active(manager_parameters.ParameterSource):
    """Flag to activate/deactivate sending requests to individual sources [-].

    The documentation of the base class |ParameterSource| provides information on the
    different ways to set source-specific values.
    """

    TYPE: Final = bool
    TIME = None
    SPAN = (False, True)
