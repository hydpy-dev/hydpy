# pylint: disable=missing-module-docstring

from __future__ import annotations

import abc

from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.wland import wland_constants

# from hydpy.models.wland import wland_model  # actual import below
from hydpy.models.wland import wland_masks
from hydpy.models.wland import wland_variables

if TYPE_CHECKING:
    from hydpy.core import variabletools
    from hydpy.models.wland import wland_control


class SoilParameter(parametertools.Parameter, abc.ABC):
    """Base class for parameters related to the soil character.

    Some parameters of |wland.DOCNAME.long| are strongly related to the soil character
    and come with default values. To apply these default values, use the `soil` keyword
    in combination with one of the available soil constants.

    We take parameter |B| and the soil character |SAND| as an example, which has the
    default value `4.05`:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> b(soil=SAND)
    >>> b
    b(soil=SAND)
    >>> from hydpy import round_
    >>> round_(b.value)
    4.05

    For a list of the available defaults, see the respective parameter's documentation
    or the error message that class |SoilParameter| raises if one passes a wrong value:

    >>> b(soil=0)
    Traceback (most recent call last):
    ...
    ValueError: Parameter `b` of element `?` received the soil constant `0`, which is \
not among the available ones.  Please use one of the following constants: `SAND` (1), \
`LOAMY_SAND` (2), `SANDY_LOAM` (3), `SILT_LOAM` (4), `LOAM` (5), `SANDY_CLAY_LOAM` \
(6), `SILT_CLAY_LOAM` (7), `CLAY_LOAM` (8), `SANDY_CLAY` (9), `SILTY_CLAY` (10), and \
`CLAY` (11).
    """

    _SOIL2VALUE: dict[int, float]

    def _set_soil(self, *, soil: int) -> dict[str, int]:
        if (value := self._SOIL2VALUE.get(soil)) is None:
            value2name = wland_constants.CONSTANTS.value2name
            names = (f"`{value2name[v]}` ({v})" for v in self._SOIL2VALUE)
            raise ValueError(
                f"Parameter {objecttools.elementphrase(self)} received the soil "
                f"constant `{soil}`, which is not among the available ones.  Please "
                f"use one of the following constants: {objecttools.enumeration(names)}."
            )
        self.value = value
        return {"soil": soil}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("soil", type_=int), setter=_set_soil
        )
    )

    @overload
    def __call__(self, *values: CallHook) -> None: ...

    @overload
    def __call__(self, *, auxfile: str) -> None: ...

    @overload
    def __call__(self, *, soil: int) -> None: ...

    def __call__(self, *args: CallHook, **kwargs: Any) -> None:
        super().__call__(*args, **kwargs)

    @classmethod
    def print_defaults(cls) -> None:
        """Print the soil-related default values of the parameter.

        See the documentation on class |B| for an example.
        """
        value2name = wland_constants.CONSTANTS.value2name
        for constant, value in cls._SOIL2VALUE.items():
            print(value2name[constant], end=": ")
            objecttools.round_(value)

    def __repr__(self) -> str:
        if (arguments := self.keywordhandler.arguments).valid:
            name = wland_constants.SOIL_CONSTANTS.value2name[arguments["soil"]]
            return f"{self.name}(soil={name})"
        return super().__repr__()


class LanduseParameterLand(
    wland_variables.MixinHRUs, parametertools.ZipParameter, abc.ABC
):
    """Base class for 1-dimensional parameters relevant for all land-related units.

    We take the parameter |DDT| as an example.  You can define its values by using the
    names of all land use-related constants in lower-case as keywords:

    >>> from hydpy import print_vector, round_
    >>> from hydpy.models.wland import *
    >>> simulationstep("1d")
    >>> parameterstep("1d")
    >>> nu(13)
    >>> lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE, WETLAND,
    ...    TREES, CONIFER, DECIDIOUS, MIXED, SEALED, WATER)
    >>> ddf(sealed=0.0, field=1.0, wine=2.0, orchard=3.0, soil=4.0, pasture=5.0,
    ...     wetland=6.0, trees=7.0, conifer=8.0, decidious=9.0, mixed=10.0)
    >>> ddf
    ddf(conifer=8.0, decidious=9.0, field=1.0, mixed=10.0, orchard=3.0,
        pasture=5.0, sealed=0.0, soil=4.0, trees=7.0, wetland=6.0,
        wine=2.0)
    >>> print_vector(ddf.values)
    0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 0.0, nan

    You can average the current values with regard to the hydrological response area
    fractions, defined via parameter |AUR|:

    >>> aur(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.22)
    >>> round_(ddf.average_values())
    5.641026

    You can query or change the values related to specific land use types via attribute
    access:

    >>> print_vector(ddf.sealed)
    0.0, 0.0
    >>> ddf.sealed = 11.0, 12.0
    >>> ddf
    ddf(11.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, nan)
    >>> ddf.sealed = 12.0
    >>> ddf
    ddf(conifer=8.0, decidious=9.0, field=1.0, mixed=10.0, orchard=3.0,
        pasture=5.0, sealed=12.0, soil=4.0, trees=7.0, wetland=6.0,
        wine=2.0)
    """

    constants = wland_constants.LANDUSE_CONSTANTS
    mask = wland_masks.Land()

    @property
    def refweights(self) -> wland_control.AUR:
        """Alias for the associated instance of |AUR| for calculating areal mean
        values."""
        # pylint: disable=import-outside-toplevel
        from hydpy.models.wland import wland_model

        model = cast(wland_model.Model, self.subpars.pars.model)
        return model.parameters.control.aur


class LanduseMonthParameter(parametertools.KeywordParameter2D, abc.ABC):
    """Base class for parameters which values depend on the actual month and land-use
    type."""

    columnnames = (
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
    rownames = tuple(
        key.lower()
        for value, key in sorted(wland_constants.LANDUSE_CONSTANTS.value2name.items())
    )
