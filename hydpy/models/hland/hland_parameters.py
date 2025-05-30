# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools

# ...from hland
from hydpy.models.hland.hland_constants import CONSTANTS
from hydpy.models.hland import hland_masks


class ParameterBase(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters."""

    constants = CONSTANTS

    @property
    def refweights(self):
        """Reference to the associated instance of |RelZoneAreas| for calculating areal
        mean values."""
        return self.subpars.pars.control.zonearea


class ParameterComplete(ParameterBase):
    """Base class for 1-dimensional parameters relevant for all types of zones.

    |ParameterComplete| applies the features of class |ZipParameter| on the land use
    types |FIELD|, |FOREST|, |GLACIER|, |ILAKE|, and |SEALED| and considers them all as
    relevant (e.g., for calculating weighted averages).

    We use parameter |PCorr| as an example, which is a subclass of |ParameterComplete|.
    After preparing the parameter |ZoneType|, |PCorr| allows setting its values using
    the relevant land-use types as keywords:

    >>> from hydpy import print_vector, round_
    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(6)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD, SEALED)
    >>> pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0, sealed=5.0)
    >>> pcorr
    pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0, sealed=5.0)
    >>> print_vector(pcorr.values)
    2.0, 1.0, 4.0, 3.0, 2.0, 5.0

    Parameter |ZoneArea| serves for calculating areal means (see the documentation on
    |property| |ParameterBase.refweights|):

    >>> zonearea.values = 0.0, 1.0, 2.0, 3.0, 4.0, 5.0
    >>> round_(pcorr.average_values())
    3.4

    Alternatively, pass other masks defined in module |hland_masks| to take only
    certain types of zones into account:

    >>> round_(pcorr.average_values(model.masks.field))
    2.0
    >>> round_(pcorr.average_values("soil"))
    1.8
    >>> round_(pcorr.average_values(model.masks.field, "forest"))
    1.8

    All other masks (for example, |hland_masks.Soil|, being used by |ParameterSoil|
    subclasses as |hland_control.IcMax|) are subsets of mask |hland_masks.Complete|:

    >>> icmax.mask in pcorr.mask
    True
    >>> pcorr.mask in icmax.mask
    False
    """

    mask = hland_masks.Complete()


class ParameterLand(ParameterBase):
    """Base class for 1-dimensional parameters relevant for |FIELD|, |FOREST|,
    |GLACIER|, and |SEALED| zones.

    |ParameterLand| works similarly to |ParameterComplete|.  Some examples based on the
    parameter |WHC|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
    >>> whc(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> whc
    whc(field=2.0, forest=1.0, glacier=4.0)
    >>> whc(field=2.0, default=9.0)
    >>> whc
    whc(field=2.0, forest=9.0, glacier=9.0)
    >>> zonearea.values = 1.0, 1.0, 1.0, nan, 1.0
    >>> from hydpy import round_
    >>> round_(whc.average_values())
    5.5
    """

    mask = hland_masks.Land()


class ParameterInterception(ParameterBase):
    """Base class for 1-dimensional parameters relevant for |FIELD|, |FOREST|, and
    |SEALED| zones.

    |ParameterInterception| works similarly to |ParameterComplete|. Some examples based
    on the parameter |IcMax|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> icmax(field=2.0, forest=1.0, glacier=4.0, ilake=5.0, sealed=3.0)
    >>> icmax
    icmax(field=2.0, forest=1.0, sealed=3.0)
    >>> icmax(field=2.0, default=8.0, sealed=3.0)
    >>> icmax
    icmax(field=2.0, forest=8.0, sealed=3.0)
    >>> zonearea.values = 1.0, 2.0, nan, nan, 3.0
    >>> from hydpy import round_
    >>> round_(icmax.average_values())
    4.5
    """

    mask = hland_masks.Interception()


class ParameterSoil(ParameterBase):
    """Base class for 1-dimensional parameters relevant for |FIELD| and |FOREST| zones.

    |ParameterSoil| works similarly to |ParameterComplete|. Some examples based on the
    parameter |IcMax|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
    >>> icmax(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> icmax
    icmax(field=2.0, forest=1.0)
    >>> icmax(field=2.0, default=9.0)
    >>> icmax
    icmax(field=2.0, forest=9.0)
    >>> zonearea.values = 0.0, 1.0, nan, nan, 3.0
    >>> from hydpy import round_
    >>> round_(icmax.average_values())
    3.75
    """

    mask = hland_masks.Soil()


class ParameterUpperZone(ParameterBase):
    """Base class for 1-dimensional parameters relevant for |FIELD|, |FOREST|, and
    |GLACIER| zones.

    |ParameterLand| works similarly to |ParameterComplete|.  Some examples based on
    parameter |H1|:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(6)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD, SEALED)
    >>> h1(field=2.0, forest=1.0, glacier=4.0, ilake=3.0, sealed=5.0)
    >>> h1
    h1(field=2.0, forest=1.0, glacier=4.0)
    >>> h1(field=2.0, default=9.0)
    >>> h1
    h1(field=2.0, forest=9.0, glacier=9.0)
    >>> zonearea.values = 1.0, 1.0, 1.0, nan, 1.0, nan
    >>> from hydpy import round_
    >>> round_(h1.average_values())
    5.5
    """

    mask = hland_masks.UpperZone()


class ParameterGlacier(ParameterBase):
    """Base class for 1-dimensional parameters relevant for |GLACIER| zones.

    |ParameterGlacier| works similarly to |ParameterComplete|.  Some examples based on
    the parameter |GMelt|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> simulationstep("1d")
    >>> nmbzones(5)
    >>> zonetype(GLACIER, FOREST, ILAKE, GLACIER, FIELD)
    >>> gmelt(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> gmelt
    gmelt(4.0)
    >>> gmelt(field=2.0, forest=9.0, default=8.0)
    >>> gmelt
    gmelt(8.0)
    >>> zonearea.values = 1.0, nan, nan, 1.0, nan
    >>> from hydpy import round_
    >>> round_(gmelt.average_values())
    8.0
    """

    mask = hland_masks.Glacier()


class ParameterNoGlacier(ParameterBase):
    """Base class for 1-dimensional parameters relevant for |FIELD|, |FOREST|, and
    |ILAKE| zones.

    |ParameterNoGlacier| works similarly to |ParameterComplete|.  Some examples based
    on the parameter |TCorr|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
    >>> tcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> tcorr
    tcorr(field=2.0, forest=1.0, ilake=3.0)
    >>> tcorr(field=2.0, default=9.0)
    >>> tcorr
    tcorr(field=2.0, forest=9.0, ilake=9.0)
    >>> zonearea.values = 1.0, 1.0, nan, 1.0, 1.0
    >>> from hydpy import round_
    >>> round_(tcorr.average_values())
    5.5
    """

    mask = hland_masks.NoGlacier()
