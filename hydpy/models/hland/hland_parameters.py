# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools

# ...from hland
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_masks


class ParameterComplete(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters relevant for all types
    of zones.

    |ParameterComplete| applies the features of class |ZipParameter|
    on the land use types `field`, `forest`, `glacier`, and `ilake`
    and consideres them all as relevant (e.g. for calculating
    weighted averages).

    The following examples are based on parameter |PCorr|, which is
    directly derived from |ParameterComplete|.  After preparing
    the parameter |NmbZones|, parameter |PCorr| allows to set its
    values using the relevant land use types as keywords:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
    >>> pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> pcorr
    pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> pcorr.values
    array([ 2.,  1.,  4.,  3.,  2.])

    Parameter |ZoneArea| is used for calculating the areal means (see
    |property| |ParameterComplete.refweights|):

    >>> zonearea(0.0, 1.0, 2.0, 3.0, 4.0)
    >>> from hydpy import round_
    >>> round_(pcorr.average_values())
    2.6

    Alternatively, pass other masks defined in module |hland_masks|,
    to take only certain types of zones into account:

    >>> round_(pcorr.average_values(model.masks.field))
    2.0
    >>> round_(pcorr.average_values("soil"))
    1.8
    >>> round_(pcorr.average_values(model.masks.field, "forest"))
    1.8

    All other masks (e.g. |hland_masks.Soil| used by |ParameterSoil|
    subclasses as |hland_control.IcMax|) are subsets of mask
    |hland_masks.Complete|:

    >>> icmax.mask in pcorr.mask
    True
    >>> pcorr.mask in icmax.mask
    False
    """

    MODEL_CONSTANTS = hland_constants.CONSTANTS
    mask = hland_masks.Complete()

    @property
    def refweights(self):
        """Reference to the associated instance of |RelZoneArea| for
        calculating areal mean values."""
        return self.subpars.pars.control.zonearea


class ParameterSoil(ParameterComplete):
    """Base class for 1-dimensional parameters relevant for |FIELD|
    and |FOREST| zones.

    |ParameterSoil| works similar to |ParameterComplete|. Some examples
    based on parameter |IcMax|:

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
    >>> zonearea(0.0, 1.0, nan, nan, 3.0)
    >>> from hydpy import round_
    >>> round_(icmax.average_values())
    3.75
    """

    mask = hland_masks.Soil()


class ParameterLand(ParameterComplete):
    """Base class for 1-dimensional parameters relevant for |FIELD|,
    |FOREST|, and |GLACIER| zones.

    |ParameterLand| works similar to |ParameterComplete|.  Some examples
    based on parameter |WHC|:

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
    >>> zonearea(1.0, 1.0, 1.0, nan, 1.0)
    >>> from hydpy import round_
    >>> round_(whc.average_values())
    5.5
    """

    mask = hland_masks.Land()


class ParameterLake(ParameterComplete):
    """Base class for 1-dimensional parameters relevant for |ILAKE| zones.

    |ParameterLake| works similar to |ParameterComplete|.  Some examples
    based on parameter |TTIce|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(ILAKE, FOREST, GLACIER, ILAKE, FIELD)
    >>> ttice(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> ttice
    ttice(3.0)
    >>> ttice(field=2.0, forest=9.0, default=9.0)
    >>> ttice
    ttice(9.0)
    >>> zonearea(1.0, nan, nan, 1.0, nan)
    >>> from hydpy import round_
    >>> round_(ttice.average_values())
    9.0
    """

    mask = hland_masks.ILake()


class ParameterGlacier(ParameterComplete):
    """Base class for 1-dimensional parameters relevant for |GLACIER| zones.

    |ParameterLake| works similar to |ParameterComplete|.  Some examples
    based on parameter |GMelt|:

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
    >>> zonearea(1.0, nan, nan, 1.0, nan)
    >>> from hydpy import round_
    >>> round_(gmelt.average_values())
    8.0
    """

    mask = hland_masks.Glacier()


class ParameterNoGlacier(ParameterComplete):
    """Base class for 1-dimensional parameters relevant for |FIELD|,
    |FOREST|, and |ILAKE| zones.

    |ParameterSoil| works similar to |ParameterComplete|.  Some examples
    based on parameter |ECorr|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
    >>> ecorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> ecorr
    ecorr(field=2.0, forest=1.0, ilake=3.0)
    >>> ecorr(field=2.0, default=9.0)
    >>> ecorr
    ecorr(field=2.0, forest=9.0, ilake=9.0)
    >>> zonearea(1.0, 1.0, nan, 1.0, 1.0)
    >>> from hydpy import round_
    >>> round_(ecorr.average_values())
    5.5
    """

    mask = hland_masks.NoGlacier()
