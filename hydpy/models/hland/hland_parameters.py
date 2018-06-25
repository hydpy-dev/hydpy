# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.hland.hland_constants import FIELD, FOREST, ILAKE, GLACIER
from hydpy.models.hland.hland_constants import CONSTANTS


class MultiParameter(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters relevant for all types
    of zones.

    Due to inheriting from |ZipParameter|, additional keyword zipping
    functionality is offered.  The optional `kwargs` are checked for
    the keywords `field`, `forest`, `glacier`, `ilake,` and `default`.
    If available, the respective values are used to define the values
    of those 1-dimensional arrays, whose entries are related to the
    different zone types. Also the method
    |parametertools.MultiParameter.compress_repr| tries to find compressed
    string representations based on the mentioned zone types.

    The following examples are based on parameter |PCorr|, which is
    directly derived from |hland_parameters.MultiParameter|.

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
    RuntimeError: Parameter zonetype does not seem to be prepared \
properly for `pcorr` of element `?`.  Hence, setting values for parameter \
pcorr via keyword arguments is not possible.

    But, of course only after the reference parameter |ZoneType| has been
    properly prepared completely:

    >>> zonetype(-999999)
    >>> pcorr(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
    Traceback (most recent call last):
    ...
    RuntimeError: Parameter zonetype does not seem to be prepared \
properly for `pcorr` of element `?`.  Hence, setting values for parameter \
pcorr via keyword arguments is not possible.

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

    As shown above |hland_parameters.MultiParameter| implements
    parameter |ZoneType| as its "reference parameter" (see |property|
    |hland_parameters.MultiParameter.refindices|).
    Additionally, due to the class attribute
    |hland_parameters.MultiParameter.RELEVANT_VALUES| containing all
    four zone types, the |property| |parametertools.MultiParameter.mask|
    is |True| for all entries:

    >>> pcorr.RELEVANT_VALUES
    (1, 2, 3, 4)
    >>> pcorr.mask
    array([ True,  True,  True,  True,  True], dtype=bool)

    Finally, |hland_parameters.MultiParameter| implements parameter
    |ZoneArea| for calculating areal mean values (see |property|
    |hland_parameters.MultiParameter.refweights|).

    >>> pcorr.meanvalue
    nan
    >>> zonearea(0.0, 1.0, 2.0, 3.0, 4.0)
    >>> pcorr.meanvalue
    2.0
    """
    RELEVANT_VALUES = (FIELD, FOREST, GLACIER, ILAKE)
    MODEL_CONSTANTS = CONSTANTS

    @property
    def refindices(self):
        """Reference to the associated instance of |ZoneType|."""
        return self.subpars.pars.control.zonetype

    @property
    def shapeparameter(self):
        """Reference to the associated instance of |NmbZones|."""
        return self.subpars.pars.control.nmbzones

    @property
    def refweights(self):
        """Reference to the associated instance of |RelZoneArea| for
        calculating areal mean values."""
        return self.subpars.pars.control.zonearea


class MultiParameterSoil(MultiParameter):
    """Base class for 1-dimensional parameters relevant |FIELD| and |FOREST|
    zones.

    |MultiParameterSoil| works similar to |hland_parameters.MultiParameter|.
    Some examples based on parameter |ICMax|:

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
    >>> icmax.meanvalue
    3.75
    """
    RELEVANT_VALUES = (FIELD, FOREST)


class MultiParameterLand(MultiParameter):
    """Base class for 1-dimensional parameters relevant |FIELD|, |FOREST|,
    and |GLACIER| zones.

    |MultiParameterSoil| works similar to |hland_parameters.MultiParameter|.
    Some examples based on parameter |WHC|:

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
    >>> whc.meanvalue
    5.5
    """
    RELEVANT_VALUES = (FIELD, FOREST, GLACIER)


class MultiParameterLake(MultiParameter):
    """Base class for 1-dimensional parameters relevant |ILAKE| zones.

    |MultiParameterLake| works similar to |hland_parameters.MultiParameter|.
    Some examples based on parameter |TTIce|:

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
    >>> ttice.meanvalue
    9.0
    """
    RELEVANT_VALUES = (ILAKE,)


class MultiParameterGlacier(MultiParameter):
    """Base class for 1-dimensional parameters relevant |GLACIER| zones.

    |MultiParameterLake| works similar to |hland_parameters.MultiParameter|.
    Some examples based on parameter |GMelt|:

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
    >>> gmelt.meanvalue
    8.0
    """
    RELEVANT_VALUES = (GLACIER,)


class MultiParameterNoGlacier(MultiParameter):
    """Base class for 1-dimensional parameters relevant |FIELD|, |FOREST|,
    and |ILAKE| zones.

    |MultiParameterSoil| works similar to |hland_parameters.MultiParameter|.
    Some examples based on parameter |ECorr|:

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
    >>> ecorr.meanvalue
    5.5
    """

class RelZoneAreaMixin(parametertools.RelSubvaluesMixin):
    """Mixin class to be combined with class |hland_parameters.MultiParameter|
    or the classes derived from it.

    The following example shows how |RelLandZoneArea| works, which mixes
    |MultiParameterLand| and |RelZoneArea|:

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
    >>> area(100.0)
    >>> zonearea(10.0, 20.0, 30.0, 40.0)
    >>> derived.rellandzonearea.update()
    >>> derived.rellandzonearea
    rellandzonearea(field=0.166667, forest=0.333333, glacier=0.5)
    >>> zonetype(ILAKE)
    >>> derived.rellandzonearea
    rellandzonearea(nan)
    """

    @property
    def refabsolutes(self):
        """Reference to the associated instance of |ZoneArea|."""
        return self.subpars.pars.control.zonearea
