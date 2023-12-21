# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.wland import wland_constants
from hydpy.models.wland import wland_masks

if TYPE_CHECKING:
    from hydpy.core import variabletools


class SoilParameter(parametertools.Parameter):
    """Base class for parameters related to the soil character.

    Some parameters of *HydPy-W-Land* are strongly related to the soil character and
    come with default values. To apply these default values, use the `soil` keyword in
    combination with one of the available soil constants.

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

    You are free to ignore the default values and to set anything you like:

    >>> b.value = 3.0
    >>> b
    b(3.0)

    The string representation relies on the `soil` keyword only when used to define the
    value directly beforehand:

    >>> b(4.05)
    >>> b
    b(4.05)

    For a list of the available defaults, see the respective parameter's documentation
    or the error message that class |SoilParameter|  raises if one passes a wrong
    value:

    >>> b(soil=0)
    Traceback (most recent call last):
    ...
    ValueError: While trying the set the value of parameter `b` of element `?`, the \
following error occurred: The given soil constant `0` is not among the available \
ones.  Please use one of the following constants: SAND (1), LOAMY_SAND (2), \
SANDY_LOAM (3), SILT_LOAM (4), LOAM (5), SANDY_CLAY_LOAM (6), SILT_CLAY_LOAM (7), \
CLAY_LOAM (8), SANDY_CLAY (9), SILTY_CLAY (10), and CLAY (11).

    It is not allowed to combine the `soil` keyword with other keywords:

    >>> b(soil=SAND, landuse='acre')
    Traceback (most recent call last):
    ...
    TypeError: While trying the set the value of parameter `b` of element `?`, the \
following error occurred: It is not allowed to combine keyword `soil` with other \
keywords, but the following ones are also used: landuse.

    >>> b(landuse='acre')
    Traceback (most recent call last):
    ...
    NotImplementedError: While trying the set the value of parameter `b` of element \
`?`, the following error occurred: The value(s) of parameter `b` of element `?` could \
not be set based on the given keyword arguments.
    """

    _SOIL2VALUE: dict[int, float]
    _soil: Optional[int]

    def __init__(self, subvars: parametertools.SubParameters):
        super().__init__(subvars)
        self._soil = None

    def __call__(self, *args, **kwargs) -> None:
        self._soil = None
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError as exc:
            try:
                soil = kwargs.pop("soil", None)
                if soil is None:
                    raise exc
                if kwargs:
                    raise TypeError(
                        f"It is not allowed to combine keyword `soil` with other "
                        f"keywords, but the following ones are also used: "
                        f"{objecttools.enumeration(kwargs.keys())}."
                    ) from None
                try:
                    self(self._SOIL2VALUE[soil])
                    self._soil = soil
                except KeyError:
                    value2name = wland_constants.CONSTANTS.value2name
                    names = (
                        f"{value2name[value]} ({value})"
                        for value in self._SOIL2VALUE.keys()
                    )
                    raise ValueError(
                        f"The given soil constant `{soil}` is not among the available "
                        f"ones.  Please use one of the following constants: "
                        f"{objecttools.enumeration(names)}."
                    ) from None
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying the set the value of parameter "
                    f"{objecttools.elementphrase(self)}"
                )

    @classmethod
    def print_defaults(cls):
        """Print the soil-related default values of the parameter.

        See the documentation on class |B| for an example.
        """
        value2name = wland_constants.CONSTANTS.value2name
        for constant, value in cls._SOIL2VALUE.items():
            print(value2name[constant], end=": ")
            objecttools.round_(value)

    def __repr__(self) -> str:
        soil = self._soil
        value = self.value
        if soil and (self._SOIL2VALUE[soil] == value):
            name = wland_constants.SOIL_CONSTANTS.value2name[soil]
            return f"{self.name}(soil={name})"
        return f"{self.name}({objecttools.repr_(value)})"


class LanduseParameterLand(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters relevant for all land-related units.

    We take the parameter |DDT| as an example.  You can define its values by using the
    names of all land use-related constants in lower-case as keywords:

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
    >>> ddf.values
    array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10.,  0., nan])

    You can average the current values with regard to the hydrological response area
    fractions, defined via parameter |AUR|:

    >>> aur(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.22)
    >>> from hydpy import round_
    >>> round_(ddf.average_values())
    5.641026

    You can query or change the values related to specific land use types via attribute
    access:

    >>> ddf.sealed
    array([0., 0.])
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
    def refweights(self):
        """Alias for the associated instance of |AUR| for calculating areal mean
        values."""
        return self.subpars.aur


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    """Base class for parameters which values depend both on the actual month and
    land-use type."""

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
