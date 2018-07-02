# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_masks


class ParameterComplete(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters relevant for all types
    of zones.

    Due to inheriting from |ZipParameter|, additional keyword zipping
    functionality is offered, which is configured by the handled mask
    |Complete|. The optional `kwargs` are checked for the keywords
    `field`, `forest`, `glacier`, `ilake,` and `default`.  If available,
    the respective values are used to define the values of those
    1-dimensional arrays, whose entries are related to the different
    zone types. Also the method |MultiParameter.compress_repr|
    tries to find compressed string representations based on the
    mentioned zone types.

    The following examples are based on parameter |PCorr|, which is
    directly derived from |ParameterComplete|.

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')

    Usually, one defines its shape through parameter |NmbZones|:

    >>> pcorr.shape
    Traceback (most recent call last):
    ...
    RuntimeError: Shape information for parameter `pcorr` can only be \
retrieved after it has been defined.  You can do this manually, but usually \
it is done automatically by defining the value of parameter `nmbzones` first \
in each parameter control file.

    >>> nmbzones(5)
    >>> pcorr.shape
    (5,)

    Now, principally, the five entries of the parameter |PCorr| can
    be filled with values via keyword arguments corresponding to
    the constants defined in module |hland_constants|:

    >>> pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to set the values of parameter `pcorr` \
of element `?` based on keyword arguments, the following error occured: \
The mask of parameter `pcorr` of element `?` cannot be determined, as \
long as parameter `zonetype` is not prepared properly.

    But, of course only after the reference parameter |ZoneType| has been
    properly prepared completely:

    >>> zonetype
    zonetype(-999999)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
    >>> pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> pcorr
    pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    >>> pcorr.values
    array([ 2.,  1.,  4.,  3.,  2.])

    One can specify a default value for all zone types not included in
    the keyword list:

    >>> pcorr(field=2.0, forest=1.0, default=9.0)
    >>> pcorr
    pcorr(field=2.0, forest=1.0, glacier=9.0, ilake=9.0)
    >>> pcorr.values
    array([ 2.,  1.,  9.,  9.,  2.])

    If no default value is given, numpys |nan| is applied:

    >>> pcorr(field=2.0, forest=1.0)
    >>> pcorr
    pcorr(field=2.0, forest=1.0, glacier=nan, ilake=nan)
    >>> pcorr.values
    array([  2.,   1.,  nan,  nan,   2.])

    Using wrong keyword arguments (that do not correspond to constants
    defined in module |hland_constants|) result in the following error:

    >>> pcorr(field=2.0, wood=1.0, glacier=4.0, ilake=3.0)
    Traceback (most recent call last):
    ...
    NotImplementedError: While trying to set the values of parameter \
`pcorr` of element `?` based on keyword arguments, the following error \
occured: Key `wood` is not an available model constant.

    The way positional arguments are understood remains unaffected:

    >>> pcorr(5.0)
    >>> pcorr
    pcorr(5.0)
    >>> pcorr.values
    array([ 5.,  5.,  5.,  5.,  5.])

    >>> pcorr(5.0, 4.0, 3.0, 2.0, 1.0)
    >>> pcorr
    pcorr(5.0, 4.0, 3.0, 2.0, 1.0)
    >>> pcorr.values
    array([ 5.,  4.,  3.,  2.,  1.])

    Parameter |ZoneArea| is used for calculating areal means (see
    |property| |ParameterComplete.refweights|).  When |ZoneArea| is
    propertly prepared, applying |Variable.average_values| returns
    the expected wheighted mean value:

    >>> pcorr.average_values()
    nan
    >>> zonearea(0.0, 1.0, 2.0, 3.0, 4.0)
    >>> from hydpy import round_
    >>> round_(pcorr.average_values())
    2.0

    One can pass other masks defined in module |hland_masks|, to take
    only certain types of zones into account:

    >>> round_(pcorr.average_values(model.masks.field))
    1.0
    >>> round_(pcorr.average_values('soil'))
    1.6
    >>> round_(pcorr.average_values(model.masks.field, 'forest'))
    1.6
    """
    MODEL_CONSTANTS = hland_constants.CONSTANTS
    mask = hland_masks.Complete()

    @property
    def shapeparameter(self):
        """Reference to the associated instance of |NmbZones|."""
        return self.subpars.pars.control.nmbzones

    @property
    def refweights(self):
        """Reference to the associated instance of |RelZoneArea| for
        calculating areal mean values."""
        return self.subpars.pars.control.zonearea


class ParameterSoil(ParameterComplete):
    """Base class for 1-dimensional parameters relevant for |FIELD|
    and |FOREST| zones.

    |ParameterSoil| works similar to |ParameterComplete|. Some examples
    based on parameter |ICMax|:

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
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
    >>> parameterstep('1d')
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
    >>> parameterstep('1d')
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
    >>> parameterstep('1d')
    >>> simulationstep('1d')
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
    >>> parameterstep('1d')
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
